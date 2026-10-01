"""
Shared ffmpeg-generated media fixtures for the Harness 9 render / gate / evaluator tests.

Everything is synthesised with lavfi sources, so each fixture states a known truth
(a picture with real detail, a flat colour, a held frame, silence ...).
"""

import shutil
import subprocess
from pathlib import Path

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def run_ffmpeg(args):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def make_video(path, video_src, audio_src="sine=frequency=440:sample_rate=44100", seconds=6, size="640x360", fps=30):
    """Encode `video_src` (+ optional `audio_src`) to H.264/AAC. audio_src=None -> no audio stream."""
    path = Path(path)
    vsrc = f"{video_src}:size={size}:rate={fps}:duration={seconds}" if "=" in video_src \
        else f"{video_src}=size={size}:rate={fps}:duration={seconds}"
    cmd = ["-f", "lavfi", "-i", vsrc]
    if audio_src:
        cmd += ["-f", "lavfi", "-i", audio_src if "duration" in audio_src else f"{audio_src}:duration={seconds}"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast"]
    cmd += ["-c:a", "aac", "-shortest"] if audio_src else ["-an"]
    run_ffmpeg([*cmd, str(path)])
    return path


def make_frames(frames_dir, kind, count, size="640x360", fps=30):
    """Write `count` PNG frames named frame_000000.png ... ; kind = "rich" | "flat"."""
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    src = f"testsrc2=size={size}:rate={fps}" if kind == "rich" else f"color=c=0x0a2a18:size={size}:rate={fps}"
    run_ffmpeg(["-f", "lavfi", "-i", src, "-frames:v", str(count), "-start_number", "0",
                str(frames_dir / "frame_%06d.png")])
    return count


def make_wav(path, seconds, freq=440):
    run_ffmpeg(["-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate=44100:duration={seconds}", str(path)])
    return Path(path)
