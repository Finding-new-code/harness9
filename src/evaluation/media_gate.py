"""
src.evaluation.media_gate — Measured quality gate for rendered videos.

Every number in a MediaGateReport comes from *decoding the file* with ffmpeg /
ffprobe. Nothing is inferred from file names, flags, or "the render call
returned". The gate exists so that a flat-colour video, a frozen video, a
silent video or a truncated video can never be reported as VERIFIED.

Checks (severity "fail" unless noted):

  container_streams   video stream present (+ audio stream when expected)
  duration_match      video duration within tolerance of the expected duration
  av_duration_sync    audio and video stream durations agree
  resolution_match    width x height equals the expected size
  fps_match           frame rate equals the expected fps
  not_flat            share of sampled frames with (almost) no luma range
  visual_detail       edge density (text / imagery actually present)
  not_black           share of the timeline that is black
  has_motion          share of sampled intervals in which pixels change
  not_frozen          share of the timeline that is a frozen picture
  audio_not_silent    mean volume above the silence floor
  audio_silence_ratio share of the timeline that is silent
  audio_loudness      integrated loudness in a sane range        (warn only)

Only ffmpeg/ffprobe and the standard library are required.

CLI:
    python -m src.evaluation renders/final.mp4 --duration 30 --size 1920x1080
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

logger = logging.getLogger("harness9.evaluation.media_gate")

__all__ = [
    "ExpectedMedia",
    "GateCheck",
    "GateThresholds",
    "MediaGate",
    "MediaGateError",
    "MediaGateReport",
    "MediaGateUnavailable",
    "main",
]


class MediaGateUnavailable(RuntimeError):
    """ffmpeg / ffprobe is missing, so nothing can be measured. Never treated as a pass."""


class MediaGateError(RuntimeError):
    """Raised by MediaGate.enforce() when a video fails the gate."""

    def __init__(self, report: "MediaGateReport"):
        self.report = report
        super().__init__(report.summary())


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GateThresholds:
    """Tunable limits. Defaults were calibrated on real Chromium renders and on synthetic
    controls (flat colour, gradient, frozen frame, black, silence) — see tests/test_media_gate.py."""

    sample_fps: float = 2.0            # analysis sampling rate (raised automatically for short clips)
    analysis_width: int = 640          # frames are scaled to this width before analysis

    # container / stream sanity
    duration_abs_tolerance: float = 0.75   # seconds
    duration_rel_tolerance: float = 0.03   # 3 %
    max_av_duration_delta: float = 0.75    # seconds between audio and video stream durations
    fps_tolerance: float = 0.5

    # picture content
    min_luma_range: float = 40.0       # YMAX - YMIN below this => frame is "flat"
    max_flat_frame_ratio: float = 0.10
    min_edge_density: float = 0.002    # mean share of pixels that are edges (text/imagery)
    max_black_ratio: float = 0.15
    motion_ydif: float = 0.05          # mean |dY| between sampled frames that counts as "changed"
    min_motion_ratio: float = 0.25
    max_frozen_ratio: float = 0.60
    freeze_noise_db: float = -60.0
    freeze_min_seconds: float = 2.0

    # audio content
    silence_noise_db: float = -45.0
    silence_min_seconds: float = 1.0
    min_mean_volume_db: float = -50.0
    max_silence_ratio: float = 0.60
    loudness_range_lufs: Tuple[float, float] = (-26.0, -8.0)


@dataclass(frozen=True)
class ExpectedMedia:
    """What the caller *asked for*. Anything left as None is not checked."""

    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    require_audio: bool = True


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
@dataclass
class GateCheck:
    name: str
    passed: bool
    value: Any
    threshold: Any
    message: str
    severity: str = "fail"  # "fail" | "warn"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MediaGateReport:
    path: str
    passed: bool
    checks: List[GateCheck] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    analysis_seconds: float = 0.0
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file_size_bytes: int = 0
    file_mtime_ns: int = 0

    def failed_checks(self) -> List[GateCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "fail"]

    def warnings(self) -> List[GateCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "warn"]

    def check(self, name: str) -> Optional[GateCheck]:
        return next((c for c in self.checks if c.name == name), None)

    def summary(self) -> str:
        if self.passed:
            warn = f" ({len(self.warnings())} warning(s))" if self.warnings() else ""
            return f"MEDIA GATE PASSED{warn}: {self.path}"
        reasons = "; ".join(f"{c.name}: {c.message}" for c in self.failed_checks())
        return f"MEDIA GATE FAILED: {self.path} — {reasons}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "passed": self.passed,
            "summary": self.summary(),
            "checks": [c.to_dict() for c in self.checks],
            "metrics": self.metrics,
            "analysis_seconds": round(self.analysis_seconds, 3),
            "evaluated_at": self.evaluated_at,
            "file_size_bytes": self.file_size_bytes,
            "file_mtime_ns": self.file_mtime_ns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MediaGateReport":
        return cls(
            path=data["path"],
            passed=bool(data["passed"]),
            checks=[GateCheck(**c) for c in data.get("checks", [])],
            metrics=dict(data.get("metrics", {})),
            analysis_seconds=float(data.get("analysis_seconds", 0.0)),
            evaluated_at=data.get("evaluated_at", ""),
            file_size_bytes=int(data.get("file_size_bytes", 0)),
            file_mtime_ns=int(data.get("file_mtime_ns", 0)),
        )

    def save(self, path: Union[str, Path]) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        tmp.replace(out)
        return out


# ---------------------------------------------------------------------------
# ffmpeg plumbing
# ---------------------------------------------------------------------------
_META_FRAME = re.compile(r"^frame:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:\s*(-?[\d.eE+-]+)")
_META_STAT = re.compile(r"^lavfi\.signalstats\.([A-Z]+)=(-?[\d.eE+-]+)")


def _tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise MediaGateUnavailable(
            f"'{name}' was not found on PATH. The media gate measures decoded frames and audio, "
            f"so it cannot pass without ffmpeg/ffprobe. Install FFmpeg (https://ffmpeg.org/download.html)."
        )
    return found


def _run(cmd: Sequence[str], timeout: float) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            list(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"ffmpeg analysis timed out after {timeout:.0f}s: {' '.join(cmd[:6])} …") from exc


def _f(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_ratio(text: Optional[str]) -> Optional[float]:
    if not text or text in ("0/0", "N/A"):
        return None
    if "/" in text:
        num, _, den = text.partition("/")
        n, d = _f(num), _f(den)
        return (n / d) if n is not None and d else None
    return _f(text)


def _parse_signalstats(stdout: str) -> List[Dict[str, float]]:
    frames: List[Dict[str, float]] = []
    current: Optional[Dict[str, float]] = None
    for line in stdout.splitlines():
        m = _META_FRAME.match(line)
        if m:
            current = {"t": float(m.group(3))}
            frames.append(current)
            continue
        m = _META_STAT.match(line)
        if m and current is not None:
            current[m.group(1)] = float(m.group(2))
    return frames


def _parse_intervals(stderr: str, start_key: str, dur_key: str, total: float) -> float:
    """Sum of interval durations for `<start_key>: x` / `<dur_key>: y` log lines (handles an unterminated tail)."""
    starts = [float(x) for x in re.findall(rf"{start_key}:\s*(-?[\d.]+)", stderr)]
    durs = [float(x) for x in re.findall(rf"{dur_key}:\s*(-?[\d.]+)", stderr)]
    covered = sum(max(0.0, d) for d in durs)
    if len(starts) > len(durs):  # last interval ran to the end of the file
        covered += max(0.0, total - starts[-1])
    return covered


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
class MediaGate:
    """Measure a rendered video and decide whether it is a real video."""

    def __init__(self, thresholds: Optional[GateThresholds] = None, timeout_seconds: float = 300.0):
        self.t = thresholds or GateThresholds()
        self.timeout = timeout_seconds

    # -- public API ---------------------------------------------------------
    def evaluate(self, video_path: Union[str, Path], expected: Optional[ExpectedMedia] = None) -> MediaGateReport:
        started = time.time()
        path = Path(video_path)
        exp = expected or ExpectedMedia()
        report = MediaGateReport(path=str(path), passed=False)

        if not path.exists() or not path.is_file():
            report.checks.append(GateCheck("file_exists", False, str(path), "exists", f"File does not exist: {path}"))
            return report
        stat = path.stat()
        report.file_size_bytes, report.file_mtime_ns = stat.st_size, stat.st_mtime_ns
        if stat.st_size == 0:
            report.checks.append(GateCheck("file_exists", False, 0, "> 0 bytes", "File is empty"))
            return report

        ffmpeg, ffprobe = _tool("ffmpeg"), _tool("ffprobe")
        try:
            probe = self._probe(ffprobe, path)
        except (RuntimeError, ValueError) as exc:
            # A corrupt / truncated / non-media file is a *failed gate*, not a crash.
            report.checks.append(GateCheck("container_readable", False, str(exc)[:300], "decodable media file",
                                           f"file is not a decodable video: {str(exc)[:160]}"))
            report.analysis_seconds = time.time() - started
            return report
        v, a, fmt = probe["video"], probe["audio"], probe["format"]
        report.metrics["container"] = {
            "format": fmt.get("format_name"),
            "size_bytes": stat.st_size,
            "video": v and {k: v.get(k) for k in ("codec_name", "width", "height", "pix_fmt")},
            "audio": a and {k: a.get(k) for k in ("codec_name", "sample_rate", "channels")},
        }

        vdur = _f((v or {}).get("duration")) or _f(fmt.get("duration"), 0.0) or 0.0
        adur = _f((a or {}).get("duration")) if a else None
        fps = _parse_ratio((v or {}).get("avg_frame_rate")) or _parse_ratio((v or {}).get("r_frame_rate"))
        width, height = (v or {}).get("width"), (v or {}).get("height")
        report.metrics.update(video_duration=vdur, audio_duration=adur, fps=fps, width=width, height=height)

        self._check_container(report, v, a, exp)
        if v is None:
            report.passed = False
            report.analysis_seconds = time.time() - started
            return report
        self._check_timing_and_size(report, exp, vdur, adur, fps, width, height)

        sample_fps = min(max(self.t.sample_fps, 8.0 / max(vdur, 0.1)), max(fps or 30.0, 1.0))
        report.metrics["sample_fps"] = round(sample_fps, 3)
        self._check_visual(report, ffmpeg, path, vdur, sample_fps)
        if a is not None or exp.require_audio:
            self._check_audio(report, ffmpeg, path, vdur, has_audio=a is not None)

        report.passed = not report.failed_checks()
        report.analysis_seconds = time.time() - started
        logger.info(report.summary())
        return report

    def enforce(self, video_path: Union[str, Path], expected: Optional[ExpectedMedia] = None) -> MediaGateReport:
        report = self.evaluate(video_path, expected)
        if not report.passed:
            raise MediaGateError(report)
        return report

    def probe_summary(self, video_path: Union[str, Path]) -> Dict[str, Any]:
        """Fast ffprobe-only facts about a file (no frame analysis). Returns {} if it cannot be probed."""
        try:
            probe = self._probe(_tool("ffprobe"), Path(video_path))
        except (RuntimeError, ValueError, MediaGateUnavailable):
            return {}
        v, a, fmt = probe["video"], probe["audio"], probe["format"]
        if v is None:
            return {"has_video": False, "has_audio": a is not None}
        return {
            "has_video": True,
            "has_audio": a is not None,
            "duration": _f(v.get("duration")) or _f(fmt.get("duration")),
            "width": v.get("width"),
            "height": v.get("height"),
            "fps": _parse_ratio(v.get("avg_frame_rate")) or _parse_ratio(v.get("r_frame_rate")),
        }

    # -- probing ------------------------------------------------------------
    def _probe(self, ffprobe: str, path: Path) -> Dict[str, Any]:
        res = _run([ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], 60)
        if res.returncode != 0:
            raise RuntimeError(f"ffprobe could not read {path}: {res.stderr.strip()[:300]}")
        data = json.loads(res.stdout or "{}")
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        return {"video": video, "audio": audio, "format": data.get("format", {})}

    # -- checks -------------------------------------------------------------
    def _add(self, report: MediaGateReport, name: str, passed: bool, value: Any, threshold: Any,
             ok_msg: str, bad_msg: str, severity: str = "fail") -> None:
        report.checks.append(GateCheck(name, passed, value, threshold, ok_msg if passed else bad_msg, severity))

    def _check_container(self, report, v, a, exp: ExpectedMedia) -> None:
        ok = v is not None and (a is not None or not exp.require_audio)
        missing = [n for n, s, req in (("video", v, True), ("audio", a, exp.require_audio)) if req and s is None]
        self._add(report, "container_streams", ok, {"video": v is not None, "audio": a is not None},
                  {"video": True, "audio": exp.require_audio},
                  "video and audio streams present" if exp.require_audio else "video stream present",
                  f"missing stream(s): {', '.join(missing)}")

    def _check_timing_and_size(self, report, exp: ExpectedMedia, vdur, adur, fps, width, height) -> None:
        t = self.t
        if exp.duration is not None:
            tol = max(t.duration_abs_tolerance, t.duration_rel_tolerance * exp.duration)
            self._add(report, "duration_match", abs(vdur - exp.duration) <= tol, round(vdur, 3),
                      f"{exp.duration}s ±{tol:.2f}s",
                      f"duration {vdur:.2f}s matches expected {exp.duration}s",
                      f"duration {vdur:.2f}s differs from expected {exp.duration}s by more than {tol:.2f}s")
        elif vdur <= 0:
            self._add(report, "duration_match", False, vdur, "> 0s", "", "video duration is zero")
        if adur is not None:
            delta = abs(vdur - adur)
            self._add(report, "av_duration_sync", delta <= t.max_av_duration_delta, round(delta, 3),
                      f"<= {t.max_av_duration_delta}s",
                      f"audio/video duration delta {delta:.2f}s",
                      f"audio ({adur:.2f}s) and video ({vdur:.2f}s) durations differ by {delta:.2f}s")
        if exp.width and exp.height:
            self._add(report, "resolution_match", (width, height) == (exp.width, exp.height), f"{width}x{height}",
                      f"{exp.width}x{exp.height}", f"resolution {width}x{height}",
                      f"resolution is {width}x{height}, expected {exp.width}x{exp.height}")
        if exp.fps:
            ok = fps is not None and abs(fps - exp.fps) <= t.fps_tolerance
            self._add(report, "fps_match", ok, fps, f"{exp.fps}±{t.fps_tolerance}", f"{fps} fps",
                      f"frame rate is {fps}, expected {exp.fps}")

    def _video_filter(self, sample_fps: float, extra: str) -> str:
        return f"fps={sample_fps:.4f},scale={self.t.analysis_width}:-2:flags=area{extra}"

    def _signalstats(self, ffmpeg: str, path: Path, vf: str) -> List[Dict[str, float]]:
        res = _run([ffmpeg, "-hide_banner", "-nostats", "-v", "error", "-i", str(path), "-an", "-vf",
                    vf + ",signalstats,metadata=mode=print:file=-", "-f", "null", "-"], self.timeout)
        if res.returncode != 0:
            raise RuntimeError(f"ffmpeg video analysis failed: {res.stderr.strip()[:300]}")
        return _parse_signalstats(res.stdout)

    def _check_visual(self, report, ffmpeg, path: Path, vdur: float, sample_fps: float) -> None:
        t = self.t
        stats = self._signalstats(ffmpeg, path, self._video_filter(sample_fps, ""))
        if len(stats) < 3:
            self._add(report, "not_flat", False, len(stats), ">= 3 frames", "",
                      f"only {len(stats)} frame(s) could be decoded for analysis")
            return
        ranges = [s.get("YMAX", 0.0) - s.get("YMIN", 0.0) for s in stats]
        flat = sum(1 for r in ranges if r < t.min_luma_range) / len(ranges)
        report.metrics.update(frames_analyzed=len(stats), flat_frame_ratio=round(flat, 4),
                              median_luma_range=sorted(ranges)[len(ranges) // 2])
        self._add(report, "not_flat", flat <= t.max_flat_frame_ratio, round(flat, 4), f"<= {t.max_flat_frame_ratio}",
                  f"{flat:.0%} of sampled frames are flat",
                  f"{flat:.0%} of sampled frames are flat (luma range < {t.min_luma_range:.0f}); the video has no real picture content")

        # edge density: how much text / imagery detail exists at all
        edge_stats = self._signalstats(ffmpeg, path, self._video_filter(sample_fps, ",edgedetect=low=0.08:high=0.24"))
        # edgedetect paints edges bright on black; (YAVG - black level) / (white - black) = edge share
        dens = []
        for s in edge_stats:
            lo, hi = s.get("YMIN", 0.0), max(s.get("YMAX", 0.0), 1.0)
            span = max(hi - lo, 1.0) if hi > lo else 0.0
            dens.append(((s.get("YAVG", 0.0) - lo) / span) if span else 0.0)
        edge_density = sum(dens) / len(dens) if dens else 0.0
        report.metrics["edge_density"] = round(edge_density, 5)
        self._add(report, "visual_detail", edge_density >= t.min_edge_density, round(edge_density, 5),
                  f">= {t.min_edge_density}", f"edge density {edge_density:.4f}",
                  f"edge density {edge_density:.5f} is below {t.min_edge_density}: no text or imagery detail found")

        # motion between consecutive sampled frames
        ydifs = [s.get("YDIF", 0.0) for s in stats[1:]]
        moving = sum(1 for d in ydifs if d > t.motion_ydif) / max(len(ydifs), 1)
        report.metrics["motion_ratio"] = round(moving, 4)
        self._add(report, "has_motion", moving >= t.min_motion_ratio, round(moving, 4), f">= {t.min_motion_ratio}",
                  f"{moving:.0%} of sampled intervals show motion",
                  f"only {moving:.0%} of sampled intervals change; the picture is (almost) static")

        # frozen / black spans
        det = _run([ffmpeg, "-hide_banner", "-nostats", "-v", "info", "-i", str(path), "-an", "-vf",
                    f"fps=4,scale=320:-2:flags=area,freezedetect=n={t.freeze_noise_db}dB:d={t.freeze_min_seconds},"
                    f"blackdetect=d=0.5:pix_th=0.10", "-f", "null", "-"], self.timeout)
        log = det.stderr
        frozen = _parse_intervals(log, r"lavfi\.freezedetect\.freeze_start", r"lavfi\.freezedetect\.freeze_duration", vdur)
        black = _parse_intervals(log, r"black_start", r"black_duration", vdur)
        frozen_ratio = min(1.0, frozen / vdur) if vdur else 0.0
        black_ratio = min(1.0, black / vdur) if vdur else 0.0
        report.metrics.update(frozen_ratio=round(frozen_ratio, 4), black_ratio=round(black_ratio, 4))
        self._add(report, "not_black", black_ratio <= t.max_black_ratio, round(black_ratio, 4),
                  f"<= {t.max_black_ratio}", f"{black_ratio:.0%} black",
                  f"{black_ratio:.0%} of the timeline is black")
        self._add(report, "not_frozen", frozen_ratio <= t.max_frozen_ratio, round(frozen_ratio, 4),
                  f"<= {t.max_frozen_ratio}", f"{frozen_ratio:.0%} frozen",
                  f"{frozen_ratio:.0%} of the timeline is a frozen picture")

    def _check_audio(self, report, ffmpeg, path: Path, vdur: float, has_audio: bool) -> None:
        t = self.t
        if not has_audio:
            return  # the missing stream is already reported by container_streams
        res = _run([ffmpeg, "-hide_banner", "-nostats", "-v", "info", "-i", str(path), "-vn", "-af",
                    f"volumedetect,silencedetect=n={t.silence_noise_db}dB:d={t.silence_min_seconds},"
                    f"ebur128=peak=true:framelog=quiet", "-f", "null", "-"], self.timeout)
        log = res.stderr
        mean = _f((re.findall(r"mean_volume:\s*(-?[\d.]+|-inf)\s*dB", log) or [None])[-1], -120.0)
        peak = _f((re.findall(r"max_volume:\s*(-?[\d.]+|-inf)\s*dB", log) or [None])[-1], -120.0)
        lufs = _f((re.findall(r"\bI:\s+(-?[\d.]+|-inf)\s+LUFS", log) or [None])[-1])
        sil_total = _parse_intervals(log, r"silence_start", r"silence_duration", vdur)
        sil_ratio = min(1.0, sil_total / vdur) if vdur else 0.0
        report.metrics.update(mean_volume_db=mean, max_volume_db=peak, integrated_lufs=lufs,
                              silence_ratio=round(sil_ratio, 4))
        self._add(report, "audio_not_silent", mean is not None and mean >= t.min_mean_volume_db, mean,
                  f">= {t.min_mean_volume_db} dB", f"mean volume {mean} dB",
                  f"audio is effectively silent (mean volume {mean} dB)")
        self._add(report, "audio_silence_ratio", sil_ratio <= t.max_silence_ratio, round(sil_ratio, 4),
                  f"<= {t.max_silence_ratio}", f"{sil_ratio:.0%} silent",
                  f"{sil_ratio:.0%} of the audio track is silence")
        lo, hi = t.loudness_range_lufs
        if lufs is not None:
            self._add(report, "audio_loudness", lo <= lufs <= hi, lufs, f"{lo}..{hi} LUFS", f"{lufs} LUFS",
                      f"integrated loudness {lufs} LUFS is outside {lo}..{hi} LUFS", severity="warn")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Measure a rendered video and decide whether it is a real video.")
    p.add_argument("video", nargs="+", help="MP4 file(s) to analyse")
    p.add_argument("--duration", type=float, help="expected duration in seconds")
    p.add_argument("--size", help="expected size, e.g. 1920x1080")
    p.add_argument("--fps", type=float, help="expected frame rate")
    p.add_argument("--no-audio", action="store_true", help="audio is not required")
    p.add_argument("--json", action="store_true", help="print full JSON reports")
    args = p.parse_args(argv)

    w = h = None
    if args.size:
        w, h = (int(x) for x in args.size.lower().split("x"))
    expected = ExpectedMedia(duration=args.duration, width=w, height=h, fps=args.fps, require_audio=not args.no_audio)
    gate, worst = MediaGate(), 0
    for video in args.video:
        report = gate.evaluate(video, expected)
        worst = max(worst, 0 if report.passed else 1)
        print(json.dumps(report.to_dict(), indent=2) if args.json else report.summary())
    return worst


if __name__ == "__main__":
    sys.exit(main())
