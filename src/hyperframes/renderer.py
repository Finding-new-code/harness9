"""
src.hyperframes.renderer — HyperFrames video renderer & FFmpeg encoder.

Pipeline (backend "chrome", the default):
1. Composition pre-validation (syntax, local assets, timing)
2. Real frame capture: headless Chromium seeks the composition's GSAP timelines frame by frame
   (src.hyperframes.browser_capture) — hermetic, deterministic, no placeholder frames
3. Strict FFmpeg encode + narration mux (H.264 / AAC, bt709). ffmpeg failures raise; nothing is faked
4. Measured media gate (src.evaluation.media_gate): decoded pixels, motion, audio and container are
   analysed, and only a video that passes is reported as VERIFIED. A video that fails is moved to
   ``*.rejected.mp4`` and the render raises MediaGateError.

Backend "stub" is an explicit dry-run for tests and demos: solid-colour placeholder frames,
status "STUB", never VERIFIED. It is never selected automatically.
"""

import html
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.evaluation.media_gate import ExpectedMedia, MediaGate, MediaGateError, MediaGateReport
from src.hyperframes.browser_capture import RenderUnavailableError, capture_frames
from src.hyperframes.validator import CompositionValidator, validate_composition
from src.utils.ffmpeg import (
    create_fallback_mp4,
    is_ffmpeg_available,
    is_ffprobe_available,
    probe_media_file,
    render_video_with_ffmpeg,
)
from src.utils.filesystem import ensure_dir

logger = logging.getLogger("harness9.hyperframes.renderer")


class CompositionValidationError(Exception):
    """Raised when composition validation fails critical integrity checks."""
    pass


@dataclass
class RenderResult:
    """Outcome and technical metadata of a video render operation.

    validation_status:
        VERIFIED     real render AND the measured media gate passed
        STUB         explicit dry-run placeholder (never a real video)
        GATE_FAILED  real render whose media gate failed (only when enforce_gate=False)
        UNVERIFIED   nothing has been measured
    """
    output_path: str
    duration_seconds: float
    file_size_bytes: int
    width: int
    height: int
    fps: int
    has_video: bool = True
    has_audio: bool = True
    video_codec: str = "h264"
    audio_codec: str = "aac"
    validation_status: str = "UNVERIFIED"
    backend: str = "chrome"
    frames_captured: int = 0
    warnings: List[str] = field(default_factory=list)
    gate: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_path": self.output_path,
            "duration_seconds": round(self.duration_seconds, 3),
            "file_size_bytes": self.file_size_bytes,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "has_video": self.has_video,
            "has_audio": self.has_audio,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "validation_status": self.validation_status,
            "backend": self.backend,
            "frames_captured": self.frames_captured,
            "warnings": list(self.warnings),
            "gate": self.gate,
        }


_QUALITY_PROFILES: Dict[str, Dict[str, Any]] = {
    "draft": {"format": "jpeg", "jpeg_quality": 80, "crf": 26, "preset": "veryfast"},
    "standard": {"format": "jpeg", "jpeg_quality": 95, "crf": 20, "preset": "fast"},
    "high": {"format": "png", "jpeg_quality": 100, "crf": 16, "preset": "slow"},
}
RENDER_BACKENDS = ("chrome", "stub")


class HyperFramesRenderer:
    """Deterministic video renderer transforming HyperFrames compositions into MP4."""

    def __init__(
        self,
        fps: int = 30,
        quality: str = "standard",
        strict_validation: bool = False,
        execution_runtime: Optional[Any] = None,
        backend: Optional[str] = None,
        enforce_gate: bool = True,
        gate: Optional[MediaGate] = None,
    ):
        self.fps = fps
        self.quality = quality
        self.strict_validation = strict_validation
        self.execution_runtime = execution_runtime
        chosen = (backend or os.environ.get("HARNESS9_RENDER_BACKEND") or "chrome").strip().lower()
        if chosen not in RENDER_BACKENDS:
            raise ValueError(f"Unknown render backend {chosen!r}; expected one of {RENDER_BACKENDS}")
        self.backend = chosen
        self.enforce_gate = enforce_gate
        self.gate = gate or MediaGate()

    def render(
        self,
        project_dir: Union[str, Path],
        output_mp4: Optional[Union[str, Path]] = None,
        duration: Optional[float] = None,
        audio_path: Optional[Union[str, Path]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[int] = None,
        execution_runtime: Optional[Any] = None,
    ) -> RenderResult:
        """
        Render the HyperFrames composition in project_dir to an MP4.

        Raises RenderUnavailableError when the real renderer cannot run (no browser / Node / ffmpeg),
        BrowserCaptureError / FFmpegError when a stage fails, and MediaGateError when the finished
        video fails the measured quality gate. It never returns a fake video as a success.
        """
        proj_path = Path(project_dir).resolve()
        renders_dir = proj_path / "renders"
        renders_dir.mkdir(parents=True, exist_ok=True)

        target_mp4 = Path(output_mp4).resolve() if output_mp4 else (renders_dir / "final.mp4")
        target_mp4.parent.mkdir(parents=True, exist_ok=True)

        render_fps = fps or self.fps

        # 1. Composition pre-validation
        validator = CompositionValidator(proj_path)
        val_result = validator.validate()
        if not val_result["valid"] and self.strict_validation:
            raise CompositionValidationError(f"Composition validation failed: {val_result['errors']}")

        # 2. Extract dimensions and duration from HTML if not provided
        html_file = proj_path / "index.html"
        extracted_w, extracted_h, extracted_dur = self._extract_composition_metadata(html_file)

        render_w = width or extracted_w or 1920
        render_h = height or extracted_h or 1080
        render_dur = duration or extracted_dur or 30.0

        # Resolve audio narration path
        resolved_audio: Optional[Path] = None
        if audio_path:
            p = Path(audio_path).resolve()
            if p.exists():
                resolved_audio = p
        if not resolved_audio:
            candidates = [
                proj_path / "assets" / "audio" / "narration.wav",
                proj_path / "assets" / "narration.wav",
                proj_path / "assets" / "audio" / "narration.mp3",
            ]
            for c in candidates:
                if c.exists():
                    resolved_audio = c
                    break

        runtime = execution_runtime or self.execution_runtime

        if self.backend == "chrome" and runtime is None and not is_ffmpeg_available():
            raise RenderUnavailableError(
                "FFmpeg is required to encode and measure the real video, but it is not available on PATH. "
                "Install FFmpeg, refresh the process PATH, and retry."
            )

        # A video left over from an earlier run must never be mistaken for this run's output.
        for stale in (target_mp4, self._rejected_path(target_mp4), self._gate_path(target_mp4)):
            try:
                stale.unlink()
            except FileNotFoundError:
                pass

        self._run_project_hook(proj_path, runtime)

        ctx = dict(
            proj_path=proj_path, renders_dir=renders_dir, target_mp4=target_mp4, audio=resolved_audio,
            width=render_w, height=render_h, duration=render_dur, fps=render_fps, runtime=runtime,
            composition_errors=[] if val_result["valid"] else list(val_result.get("errors", [])),
        )
        if self.backend == "stub":
            return self._render_stub(**ctx)
        return self._render_chrome(**ctx)

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _rejected_path(target_mp4: Path) -> Path:
        return target_mp4.with_name(target_mp4.stem + ".rejected" + target_mp4.suffix)

    @staticmethod
    def _gate_path(target_mp4: Path) -> Path:
        return target_mp4.with_name(target_mp4.stem + ".gate.json")

    @staticmethod
    def _run_project_hook(proj_path: Path, runtime: Optional[Any]) -> None:
        """Legacy hook: run <project>/render.js if the project ships one. Failures are logged, not swallowed."""
        node_script = proj_path / "render.js"
        if not node_script.exists():
            return
        try:
            if runtime is not None:
                runtime.execute_command(["node", str(node_script)], cwd=proj_path)
            else:
                subprocess.run(["node", str(node_script)], cwd=str(proj_path), timeout=60)
        except Exception as exc:  # noqa: BLE001 - hook is optional; make the failure visible
            logger.warning("Project render hook %s failed: %s", node_script, exc)

    def _render_chrome(
        self, *, proj_path: Path, renders_dir: Path, target_mp4: Path, audio: Optional[Path],
        width: int, height: int, duration: float, fps: int, runtime: Optional[Any],
        composition_errors: List[str],
    ) -> RenderResult:
        profile = _QUALITY_PROFILES.get(self.quality, _QUALITY_PROFILES["standard"])
        warnings: List[str] = [f"composition validator: {e}" for e in composition_errors]

        if audio is None:
            warnings.append("no narration audio found; the video was encoded without an audio track")
        else:
            audio_info = probe_media_file(audio, execution_runtime=runtime)
            audio_len = audio_info.get("duration_seconds") or 0.0
            if audio_len and audio_len > duration + 0.5:
                warnings.append(
                    f"narration ({audio_len:.1f}s) is longer than the video ({duration:.1f}s) and was truncated"
                )

        frames_tmp = Path(tempfile.mkdtemp(prefix=".frames_", dir=str(renders_dir)))
        try:
            cap = capture_frames(
                proj_path, frames_tmp, width=width, height=height, fps=fps, duration=duration,
                image_format=profile["format"], jpeg_quality=profile["jpeg_quality"], execution_runtime=runtime,
            )
            warnings.extend(cap.warnings())
            render_video_with_ffmpeg(
                frames_pattern_or_input=cap.frame_pattern,
                audio_path=audio,
                output_mp4=target_mp4,
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                crf=profile["crf"],
                preset=profile["preset"],
                execution_runtime=runtime,
                strict=True,
                silent_audio_if_missing=False,
            )
        finally:
            shutil.rmtree(frames_tmp, ignore_errors=True)

        # Measured verification of what was actually encoded.
        gate_report = self.gate.evaluate(
            target_mp4,
            ExpectedMedia(duration=duration, width=width, height=height, fps=fps, require_audio=audio is not None),
        )
        gate_report.save(self._gate_path(target_mp4))
        warnings.extend(f"media gate warning — {c.name}: {c.message}" for c in gate_report.warnings())

        output_path = target_mp4
        if gate_report.passed:
            status = "VERIFIED"
        else:
            output_path = self._rejected_path(target_mp4)
            target_mp4.replace(output_path)  # keep the evidence, but never at the canonical path
            if self.enforce_gate:
                raise MediaGateError(gate_report)
            status = "GATE_FAILED"

        media_info = probe_media_file(output_path, execution_runtime=runtime)
        return RenderResult(
            output_path=str(output_path),
            duration_seconds=media_info.get("duration_seconds") or duration,
            file_size_bytes=output_path.stat().st_size,
            width=width,
            height=height,
            fps=fps,
            has_video=bool(media_info.get("has_video")),
            has_audio=bool(media_info.get("has_audio")),
            video_codec=media_info.get("video_codec") or "h264",
            audio_codec=media_info.get("audio_codec") or "aac",
            validation_status=status,
            backend="chrome",
            frames_captured=cap.frames,
            warnings=warnings,
            gate=gate_report.to_dict(),
        )

    def _render_stub(
        self, *, proj_path: Path, renders_dir: Path, target_mp4: Path, audio: Optional[Path],
        width: int, height: int, duration: float, fps: int, runtime: Optional[Any],
        composition_errors: List[str],
    ) -> RenderResult:
        """Explicit dry-run: solid-colour placeholder frames. Labelled STUB; never VERIFIED."""
        warnings = [
            "STUB render: solid-colour placeholder frames — this is NOT a real video and is never marked VERIFIED",
            *(f"composition validator: {e}" for e in composition_errors),
        ]
        with tempfile.TemporaryDirectory() as temp_frames_dir:
            temp_path = Path(temp_frames_dir)
            self._generate_frame_sequence(
                proj_path=proj_path, frames_dir=temp_path, duration=duration, fps=fps, width=width, height=height,
            )
            render_video_with_ffmpeg(
                frames_pattern_or_input=str(temp_path / "frame_%04d.png"),
                audio_path=audio,
                output_mp4=target_mp4,
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                execution_runtime=runtime,
            )

        if not target_mp4.exists() or target_mp4.stat().st_size == 0:
            create_fallback_mp4(target_mp4, duration=duration, width=width, height=height)

        media_info = probe_media_file(target_mp4, execution_runtime=runtime)
        return RenderResult(
            output_path=str(target_mp4),
            duration_seconds=media_info.get("duration_seconds") or duration,
            file_size_bytes=target_mp4.stat().st_size,
            width=width,
            height=height,
            fps=fps,
            has_video=media_info.get("has_video", True),
            has_audio=media_info.get("has_audio", True),
            video_codec=media_info.get("video_codec") or "h264",
            audio_codec=media_info.get("audio_codec") or "aac",
            validation_status="STUB",
            backend="stub",
            frames_captured=0,
            warnings=warnings,
            gate=None,
        )

    def _extract_composition_metadata(self, html_file: Path) -> Tuple[int, int, float]:
        """Extract data-width, data-height, and data-duration from index.html."""
        if not html_file.exists():
            return (1920, 1080, 30.0)

        content = html_file.read_text(encoding="utf-8")
        w_m = re.search(r'data-width=["\'](\d+)["\']', content)
        h_m = re.search(r'data-height=["\'](\d+)["\']', content)
        d_m = re.search(r'data-duration=["\']([\d.]+)["\']', content)

        w = int(w_m.group(1)) if w_m else 1920
        h = int(h_m.group(1)) if h_m else 1080
        dur = float(d_m.group(1)) if d_m else 30.0
        return (w, h, dur)

    def _generate_frame_sequence(
        self,
        proj_path: Path,
        frames_dir: Path,
        duration: float,
        fps: int,
        width: int,
        height: int,
    ) -> None:
        """
        Generate deterministic PNG frame sequence for the timeline.
        Creates individual PNG frames stepping from t=0 to t=duration.
        """
        total_frames = max(1, int(round(duration * fps)))
        images_dir = proj_path / "assets" / "images"
        svg_assets = list(images_dir.glob("*.svg")) if images_dir.exists() else []

        # Create basic raw valid PNG bytes
        # 1x1 minimal PNG frame or rendered frames
        png_header = b"\x89PNG\r\n\x1a\n"
        # Generate minimal compliant PNG chunk structure
        for i in range(total_frames):
            frame_file = frames_dir / f"frame_{i:04d}.png"
            # Write a deterministic frame payload
            frame_bytes = self._build_frame_png(width, height, frame_idx=i, total_frames=total_frames)
            frame_file.write_bytes(frame_bytes)

    @staticmethod
    def _build_frame_png(width: int, height: int, frame_idx: int, total_frames: int) -> bytes:
        """
        Build a deterministic uncompressed PNG file for the given frame index.
        """
        import struct
        import zlib

        w = 64 if width >= height else 36
        h = 36 if width >= height else 64

        # Build raw pixel buffer: color gradient shifting over time
        progress = frame_idx / max(1, total_frames - 1)
        r = int(10 + progress * 20)
        g = int(15 + (1.0 - progress) * 30)
        b = int(25 + progress * 50)

        row = bytes([0]) + bytes([r, g, b]) * w
        raw_data = row * h
        compressed = zlib.compress(raw_data)

        # PNG Chunks
        def _chunk(chunk_type: bytes, data: bytes) -> bytes:
            length = struct.pack(">I", len(data))
            crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
            return length + chunk_type + data + crc

        ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", compressed) + _chunk(b"IEND", b"")
        return png
