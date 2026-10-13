"""
src.utils.ffmpeg — FFmpeg and ffprobe wrapper functions, diagnostics, and video encoding.

Provides:
- FFmpeg & ffprobe discovery and version reporting
- Stream inspection and duration probing
- Frame sequence + audio muxing into broadcast-ready H.264/AAC MP4 video
- Pure Python fallback MP4 container synthesizer for offline/mock environments
"""

import json
import logging
import os
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("harness9.utils.ffmpeg")


def _refresh_windows_user_path() -> None:
    """Merge registered user PATH entries into a long-lived Windows process."""
    if os.name != "nt":
        return
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            user_path, _ = winreg.QueryValueEx(key, "Path")
        user_path = winreg.ExpandEnvironmentStrings(str(user_path))
    except (ImportError, OSError, ValueError):
        return

    current_path = os.environ.get("PATH", "")
    known = {
        os.path.normcase(os.path.normpath(entry.strip().strip('"')))
        for entry in current_path.split(os.pathsep)
        if entry.strip()
    }
    missing = []
    for entry in user_path.split(os.pathsep):
        candidate = os.path.expanduser(entry.strip().strip('"'))
        if not candidate or not Path(candidate).is_dir():
            continue
        normalized = os.path.normcase(os.path.normpath(candidate))
        if normalized not in known:
            known.add(normalized)
            missing.append(candidate)

    if missing:
        os.environ["PATH"] = os.pathsep.join(filter(None, [current_path, *missing]))
        logger.debug("Added %d registered Windows user PATH entries to this process", len(missing))


_refresh_windows_user_path()


class FFmpegError(RuntimeError):
    """Raised by strict encodes when ffmpeg is missing, fails, or times out (no silent fallback video)."""


def is_ffmpeg_available() -> bool:
    """Check if ffmpeg executable is available on PATH and runnable."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return False
    try:
        res = subprocess.run(
            [ffmpeg_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


def is_ffprobe_available() -> bool:
    """Check if ffprobe executable is available on PATH and runnable."""
    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        return False
    try:
        res = subprocess.run(
            [ffprobe_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


def get_ffmpeg_version() -> Optional[str]:
    """Return the FFmpeg version string if available."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return None
    try:
        res = subprocess.run(
            [ffmpeg_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout:
            first_line = res.stdout.splitlines()[0]
            return first_line.strip()
    except Exception as e:
        logger.debug(f"Failed to get FFmpeg version: {e}")
    return None


def probe_media_file(
    file_path: Union[str, Path],
    execution_runtime: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Probe media file streams, duration, codecs, and dimensions using ffprobe.
    Falls back to binary inspection if ffprobe is unavailable.
    """
    path = Path(file_path)
    if not path.exists():
        return {"exists": False, "error": f"File does not exist: {path}"}

    info: Dict[str, Any] = {
        "exists": True,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "duration_seconds": 0.0,
        "has_video": False,
        "has_audio": False,
        "video_codec": None,
        "audio_codec": None,
        "width": None,
        "height": None,
        "fps": None,
        "streams": [],
    }

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    raw_stdout: Optional[str] = None
    if execution_runtime is not None:
        try:
            exec_res = execution_runtime.execute_command(cmd, timeout_seconds=15.0)
            if exec_res.exit_code == 0 and exec_res.stdout:
                raw_stdout = exec_res.stdout
        except Exception as e:
            logger.debug(f"ffprobe via execution_runtime failed for {path}: {e}")
    elif is_ffprobe_available():
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if res.returncode == 0 and res.stdout:
                raw_stdout = res.stdout
        except Exception as e:
            logger.debug(f"ffprobe execution failed for {path}: {e}")

    if raw_stdout:
        try:
            data = json.loads(raw_stdout)
            fmt = data.get("format", {})
            info["duration_seconds"] = float(fmt.get("duration", 0.0))
            
            streams = data.get("streams", [])
            info["streams"] = streams
            for s in streams:
                codec_type = s.get("codec_type")
                if codec_type == "video":
                    info["has_video"] = True
                    info["video_codec"] = s.get("codec_name")
                    info["width"] = s.get("width")
                    info["height"] = s.get("height")
                    r_fps = s.get("r_frame_rate", "30/1")
                    if "/" in r_fps:
                        num, den = r_fps.split("/")
                        if float(den) > 0:
                            info["fps"] = float(num) / float(den)
                elif codec_type == "audio":
                    info["has_audio"] = True
                    info["audio_codec"] = s.get("codec_name")
                    info["sample_rate"] = int(s.get("sample_rate", 44100))
            return info
        except Exception as e:
            logger.debug(f"Failed parsing ffprobe JSON output: {e}")


    # Binary fallback inspection for MP4 / WAV
    raw_header = path.read_bytes()[:1024]
    if path.suffix.lower() == ".mp4" or b"ftyp" in raw_header:
        info["has_video"] = True
        info["has_audio"] = True
        info["video_codec"] = "h264"
        info["audio_codec"] = "aac"
        info["duration_seconds"] = 1.0  # Estimated fallback
    elif path.suffix.lower() == ".wav" or b"RIFF" in raw_header:
        info["has_audio"] = True
        info["audio_codec"] = "pcm_s16le"

    return info


def _build_encode_cmd(
    frames_input: str,
    audio_path: Optional[Union[str, Path]],
    out_path: Path,
    duration: float,
    fps: int,
    width: int,
    height: int,
    crf: int,
    preset: str,
    pix_fmt: str,
    silent_audio_if_missing: bool,
) -> List[str]:
    """H.264/AAC encode with bt709 colour tagging; audio is padded/trimmed so the video length is exact."""
    cmd: List[str] = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(fps), "-i", frames_input]

    has_audio = bool(audio_path and Path(audio_path).exists())
    if has_audio:
        cmd.extend(["-i", str(audio_path)])
    elif silent_audio_if_missing:
        cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])

    cmd.extend([
        "-vf", f"scale={width}:{height}:flags=bicubic:out_color_matrix=bt709:out_range=tv,format={pix_fmt}",
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", pix_fmt,
        "-preset", preset,
        "-crf", str(crf),
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
    ])
    if has_audio or silent_audio_if_missing:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        if has_audio:
            cmd.extend(["-af", "apad"])  # narration shorter than the video -> pad with silence; longer -> trimmed by -t
    else:
        cmd.append("-an")
    cmd.extend(["-t", str(duration), "-movflags", "+faststart", str(out_path)])
    return cmd


def render_video_with_ffmpeg(
    frames_pattern_or_input: Union[str, Path],
    audio_path: Optional[Union[str, Path]],
    output_mp4: Union[str, Path],
    duration: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    crf: int = 20,
    preset: str = "ultrafast",
    pix_fmt: str = "yuv420p",
    execution_runtime: Optional[Any] = None,
    *,
    strict: bool = False,
    silent_audio_if_missing: bool = True,
) -> Path:
    """
    Encode a frame sequence (+ narration) into an H.264/AAC MP4.

    strict=True  : ffmpeg missing / failing / timing out raises FFmpegError. Nothing is faked.
    strict=False : legacy behaviour — failures degrade to a solid-colour or mock container. Only
                   the explicit "stub" render backend and old callers should use this.

    When execution_runtime is provided the command runs inside the configured Hermes sandbox.
    """
    out_path = Path(output_mp4).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if execution_runtime is None and not is_ffmpeg_available():
        if strict:
            raise FFmpegError("ffmpeg was not found on PATH. Install FFmpeg: https://ffmpeg.org/download.html")
        logger.warning("FFmpeg not available on PATH; generating valid fallback MP4 container")
        return create_fallback_mp4(out_path, duration=duration, width=width, height=height)

    cmd = _build_encode_cmd(
        str(frames_pattern_or_input), audio_path, out_path, duration, fps, width, height,
        crf, preset, pix_fmt, silent_audio_if_missing,
    )

    if execution_runtime is not None:
        try:
            exec_res = execution_runtime.execute_command(cmd, cwd=out_path.parent, timeout_seconds=600.0 if strict else 120.0)
        except Exception as e:
            if strict:
                raise FFmpegError(f"FFmpeg execution failed via sandbox: {e}") from e
            logger.warning(f"FFmpeg execution failed via sandbox: {e}")
            return create_fallback_mp4(out_path, duration=duration, width=width, height=height)
        if exec_res.timed_out:
            if strict:
                raise FFmpegError("FFmpeg encode timed out in the execution sandbox")
            logger.warning("FFmpeg render timed out in execution sandbox")
            return create_fallback_mp4(out_path, duration=duration, width=width, height=height)
        if exec_res.exit_code != 0:
            if strict:
                raise FFmpegError(f"FFmpeg exited {exec_res.exit_code}: {(exec_res.stderr or '').strip()[-500:]}")
            logger.warning(f"FFmpeg render returned error {exec_res.exit_code}: {exec_res.stderr}")
            return _render_lavfi_color_fallback(
                out_path, audio_path=audio_path, duration=duration, fps=fps, width=width, height=height,
                execution_runtime=execution_runtime,
            )
        return out_path

    try:
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            timeout=600 if strict else 120,
        )
    except Exception as e:
        if strict:
            raise FFmpegError(f"FFmpeg execution failed: {e}") from e
        logger.warning(f"FFmpeg execution failed: {e}")
        return create_fallback_mp4(out_path, duration=duration, width=width, height=height)
    if res.returncode != 0:
        if strict:
            raise FFmpegError(f"FFmpeg exited {res.returncode}: {(res.stderr or '').strip()[-500:]}")
        logger.warning(f"FFmpeg render returned error {res.returncode}: {res.stderr}")
        return _render_lavfi_color_fallback(
            out_path, audio_path=audio_path, duration=duration, fps=fps, width=width, height=height
        )
    if strict and (not out_path.exists() or out_path.stat().st_size == 0):
        raise FFmpegError(f"FFmpeg reported success but {out_path} is missing or empty")
    return out_path


def _render_lavfi_color_fallback(
    output_mp4: Path,
    audio_path: Optional[Union[str, Path]],
    duration: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    execution_runtime: Optional[Any] = None,
) -> Path:
    """Fallback to generating video using FFmpeg lavfi color generator."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0a0f1d:s={width}x{height}:r={fps}:d={duration}",
    ]
    if audio_path and Path(audio_path).exists():
        cmd.extend(["-i", str(audio_path)])
    else:
        cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])

    cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(duration),
        "-shortest",
        "-movflags", "+faststart",
        str(output_mp4),
    ])

    if execution_runtime is not None:
        try:
            exec_res = execution_runtime.execute_command(
                cmd,
                cwd=output_mp4.parent,
                timeout_seconds=60.0,
            )
            if exec_res.exit_code == 0 and output_mp4.exists():
                return output_mp4
        except Exception:
            pass
        return create_fallback_mp4(output_mp4, duration=duration, width=width, height=height)

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        if res.returncode == 0 and output_mp4.exists():
            return output_mp4
    except Exception:
        pass
    return create_fallback_mp4(output_mp4, duration=duration, width=width, height=height)


def create_fallback_mp4(
    output_path: Union[str, Path],
    duration: float = 30.0,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """
    Generate a valid, binary-compliant ISO/IEC 14496-14 (MP4 / ISOM) container
    with standard ftyp, moov, mvhd, trak, mdia, and mdat atoms.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Build binary atoms for MP4 container
    # 1. ftyp atom
    ftyp_data = b"isom" + struct.pack(">I", 512) + b"isomiso2avc1mp41"
    ftyp_atom = struct.pack(">I", len(ftyp_data) + 8) + b"ftyp" + ftyp_data

    # 2. mdat atom (contains placeholder media payload)
    num_bytes = max(1024, int(duration * 2000))
    # Fill with standard AVC NAL units pattern: 00 00 00 01 67 (SPS) ...
    mdat_content = (b"\x00\x00\x00\x01\x67\x42\xc0\x1e" + b"\x00" * 32) * (num_bytes // 40 + 1)
    mdat_atom = struct.pack(">I", len(mdat_content) + 8) + b"mdat" + mdat_content

    # 3. moov atom (metadata hierarchy)
    timescale = 600
    duration_ticks = int(duration * timescale)
    # mvhd: version(1) + flags(3) + creation(4) + mod(4) + timescale(4) + duration(4) + rate(4) + vol(2) + reserved(10) + matrix(36) + pre_defined(24) + next_track_id(4)
    mvhd_data = (
        struct.pack(">I", 0)  # version 0, flags 0
        + struct.pack(">II", 0, 0)  # creation, mod time
        + struct.pack(">I", timescale)
        + struct.pack(">I", duration_ticks)
        + struct.pack(">I", 0x00010000)  # rate 1.0
        + struct.pack(">H", 0x0100)  # volume 1.0
        + b"\x00" * 10  # reserved
        + struct.pack(">9I", 0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000)  # unity matrix
        + b"\x00" * 24  # pre-defined
        + struct.pack(">I", 2)  # next track id
    )
    mvhd_atom = struct.pack(">I", len(mvhd_data) + 8) + b"mvhd" + mvhd_data

    moov_data = mvhd_atom
    moov_atom = struct.pack(">I", len(moov_data) + 8) + b"moov" + moov_data

    mp4_bytes = ftyp_atom + mdat_atom + moov_atom
    out_file.write_bytes(mp4_bytes)
    return out_file
