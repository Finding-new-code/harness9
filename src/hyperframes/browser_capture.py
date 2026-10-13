"""
src.hyperframes.browser_capture — real frame capture for HyperFrames compositions.

Drives ``capture/capture_frames.mjs`` (Node + puppeteer-core + a headless Chromium) to seek the
composition's GSAP timelines frame by frame and write real screenshots. This replaces the old
placeholder-frame path: if the browser toolchain is not usable, the caller gets a
``RenderUnavailableError`` that says exactly what to install — never a fake video.

Environment variables
    HARNESS9_CHROME_PATH            explicit Chrome / Chromium / Edge executable
    HARNESS9_TOOLCHAIN_DIR          where puppeteer-core + gsap are installed (default ~/.harness9/render-toolchain)
    HARNESS9_AUTO_INSTALL_RENDER_DEPS   "0" disables the one-time `npm install` (default: enabled)
    HARNESS9_BUNDLED_CHROMIUM       "1" force / "0" forbid the self-contained @sparticuz/chromium (Linux only)
    HARNESS9_CHROME_NO_SANDBOX      "1" adds --no-sandbox (automatic when running as root, e.g. in containers)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("harness9.hyperframes.capture")

CAPTURE_SRC_DIR = Path(__file__).resolve().parent / "capture"
BUNDLED_CHROMIUM_SPEC = ("@sparticuz/chromium", "153.0.0")

_CHROME_ENV_VARS = ("HARNESS9_CHROME_PATH", "CHROME_PATH", "PUPPETEER_EXECUTABLE_PATH", "CHROME_BIN")
_CHROME_PATH_NAMES = (
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge", "microsoft-edge",
)
_CHROME_WINDOWS = (
    r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
    r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe",
    r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe",
)
_CHROME_MAC = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


class RenderUnavailableError(RuntimeError):
    """The real renderer cannot run on this machine. Callers must NOT substitute a fake video."""


class BrowserCaptureError(RuntimeError):
    """The browser started but frame capture failed."""


@dataclass
class CaptureResult:
    frames: int
    frames_dir: Path
    frame_pattern: str
    image_format: str
    timelines: List[str] = field(default_factory=list)
    blocked_requests: List[str] = field(default_factory=list)
    broken_images: List[str] = field(default_factory=list)
    page_errors: List[str] = field(default_factory=list)
    browser: str = ""
    seconds: float = 0.0

    def warnings(self) -> List[str]:
        out: List[str] = []
        if self.broken_images:
            out.append(f"{len(self.broken_images)} image(s) failed to load: {', '.join(self.broken_images[:5])}")
        if self.page_errors:
            out.append(f"{len(self.page_errors)} JavaScript error(s) in the composition: {self.page_errors[0][:160]}")
        if self.blocked_requests:
            out.append(f"{len(self.blocked_requests)} external request(s) blocked (renders are hermetic): "
                       f"{', '.join(self.blocked_requests[:3])}")
        return out


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def find_chrome() -> Optional[str]:
    """Locate a Chrome / Chromium / Edge executable, or None."""
    for var in _CHROME_ENV_VARS:
        value = os.environ.get(var)
        if value and Path(value).exists():
            return str(value)
    for name in _CHROME_PATH_NAMES:
        found = shutil.which(name)
        if found:
            return found
    system = platform.system()
    if system == "Windows":
        for template in _CHROME_WINDOWS:
            candidate = os.path.expandvars(template)
            if "%" not in candidate and Path(candidate).exists():
                return candidate
    elif system == "Darwin":
        for candidate in _CHROME_MAC:
            if Path(candidate).exists():
                return candidate
    return None


def toolchain_dir() -> Path:
    override = os.environ.get("HARNESS9_TOOLCHAIN_DIR")
    return Path(override).expanduser() if override else Path.home() / ".harness9" / "render-toolchain"


def _env_flag(name: str, default: Optional[bool]) -> Optional[bool]:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _bundled_chromium_wanted(system_chrome: Optional[str]) -> bool:
    if platform.system() != "Linux":
        return False
    forced = _env_flag("HARNESS9_BUNDLED_CHROMIUM", None)
    if forced is not None:
        return forced
    return system_chrome is None  # Linux with no system browser: use the self-contained one


def _package_json_for(bundled: bool) -> Dict[str, Any]:
    data = json.loads((CAPTURE_SRC_DIR / "package.json").read_text(encoding="utf-8"))
    if bundled:
        name, version = BUNDLED_CHROMIUM_SPEC
        data.setdefault("dependencies", {})[name] = version
    return data


def _signature(pkg: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(pkg, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def availability() -> Dict[str, Any]:
    """Non-installing readiness report (used by the CLI doctor and by error messages)."""
    node, npm, ffmpeg = shutil.which("node"), shutil.which("npm"), shutil.which("ffmpeg")
    chrome = find_chrome()
    tdir = toolchain_dir()
    marker = tdir / "node_modules" / ".h9-installed"
    installed = marker.exists()
    problems: List[str] = []
    if not node:
        problems.append("Node.js (>= 18) is not on PATH — install from https://nodejs.org")
    if not ffmpeg:
        problems.append("FFmpeg is not on PATH — install from https://ffmpeg.org/download.html")
    if not chrome and platform.system() != "Linux":
        problems.append("No Chrome / Chromium / Edge found — install Chrome or set HARNESS9_CHROME_PATH")
    return {
        "node": node, "npm": npm, "ffmpeg": ffmpeg, "chrome": chrome,
        "toolchain_dir": str(tdir), "toolchain_installed": installed,
        "bundled_chromium_would_be_used": _bundled_chromium_wanted(chrome),
        "ready_without_install": bool(node and ffmpeg and (chrome or _bundled_chromium_wanted(chrome)) and installed),
        "problems": problems,
    }


# ---------------------------------------------------------------------------
# Toolchain installation (one-time, app-owned directory)
# ---------------------------------------------------------------------------
def ensure_toolchain(*, auto_install: Optional[bool] = None, timeout: float = 900.0) -> Path:
    """Make sure puppeteer-core + GSAP (+ optional bundled Chromium) are installed; return the toolchain dir."""
    node = shutil.which("node")
    if not node:
        raise RenderUnavailableError(
            "Node.js is required for real video rendering but was not found on PATH. "
            "Install Node >= 18 from https://nodejs.org (or use --render-backend stub for a labelled dry run)."
        )
    if auto_install is None:
        auto_install = bool(_env_flag("HARNESS9_AUTO_INSTALL_RENDER_DEPS", True))

    system_chrome = find_chrome()
    bundled = _bundled_chromium_wanted(system_chrome)
    if not system_chrome and not bundled:
        raise RenderUnavailableError(
            "No Chrome / Chromium / Edge executable was found. Install Google Chrome, or set HARNESS9_CHROME_PATH "
            "to a browser executable (on Linux, HARNESS9_BUNDLED_CHROMIUM=1 installs a self-contained Chromium via npm)."
        )

    tdir = toolchain_dir()
    tdir.mkdir(parents=True, exist_ok=True)
    pkg = _package_json_for(bundled)
    sig = _signature(pkg)

    script_src = CAPTURE_SRC_DIR / "capture_frames.mjs"
    script_dst = tdir / "capture_frames.mjs"
    if not script_dst.exists() or script_dst.read_bytes() != script_src.read_bytes():
        shutil.copyfile(script_src, script_dst)
    pkg_text = json.dumps(pkg, indent=2) + "\n"
    pkg_dst = tdir / "package.json"
    if not pkg_dst.exists() or pkg_dst.read_text(encoding="utf-8") != pkg_text:
        pkg_dst.write_text(pkg_text, encoding="utf-8")

    marker = tdir / "node_modules" / ".h9-installed"
    if marker.exists() and marker.read_text(encoding="utf-8").strip() == sig:
        return tdir

    npm = shutil.which("npm")
    if not npm:
        raise RenderUnavailableError("npm was not found on PATH; it is needed once to install the render toolchain.")
    if not auto_install:
        raise RenderUnavailableError(
            f"The render toolchain is not installed in {tdir}. Run:  cd \"{tdir}\" && npm install --omit=dev  "
            f"(or unset HARNESS9_AUTO_INSTALL_RENDER_DEPS=0 to let Harness 9 do it)."
        )

    logger.info("Installing the render toolchain into %s (one-time; puppeteer-core, gsap%s)…",
                tdir, ", bundled Chromium" if bundled else "")
    try:
        res = subprocess.run(
            [npm, "install", "--omit=dev", "--no-audit", "--no-fund", "--loglevel=error"],
            cwd=str(tdir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderUnavailableError(f"`npm install` timed out after {timeout:.0f}s in {tdir}.") from exc
    if res.returncode != 0:
        raise RenderUnavailableError(
            f"`npm install` failed in {tdir} (exit {res.returncode}): {(res.stderr or res.stdout).strip()[-600:]}"
        )
    (tdir / "node_modules").mkdir(exist_ok=True)
    marker.write_text(sig, encoding="utf-8")
    return tdir


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------
def _needs_no_sandbox() -> bool:
    forced = _env_flag("HARNESS9_CHROME_NO_SANDBOX", None)
    if forced is not None:
        return forced
    geteuid = getattr(os, "geteuid", None)
    return bool(geteuid and geteuid() == 0)


def _parse_events(stdout: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def capture_frames(
    project_dir: Path,
    frames_dir: Path,
    *,
    width: int,
    height: int,
    fps: float,
    duration: float,
    image_format: str = "jpeg",
    jpeg_quality: int = 95,
    timeout: Optional[float] = None,
    execution_runtime: Optional[Any] = None,
    auto_install: Optional[bool] = None,
) -> CaptureResult:
    """Capture ``round(duration * fps)`` real frames of the composition in ``project_dir``."""
    tdir = ensure_toolchain(auto_install=auto_install)
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    total = max(1, round(duration * fps))
    ext = "png" if image_format == "png" else "jpg"

    cmd: List[str] = [
        shutil.which("node") or "node", str(tdir / "capture_frames.mjs"),
        "--project", str(Path(project_dir).resolve()), "--out", str(frames_dir.resolve()),
        "--width", str(int(width)), "--height", str(int(height)),
        "--fps", str(fps), "--duration", str(duration),
        "--format", "png" if image_format == "png" else "jpeg", "--quality", str(int(jpeg_quality)),
    ]
    chrome = find_chrome()
    if chrome:
        cmd += ["--chrome", chrome]
    if _needs_no_sandbox():
        cmd.append("--no-sandbox")

    limit = timeout if timeout is not None else max(180.0, total * 1.0)
    logger.info("Capturing %d frames (%dx%d @ %s fps) with %s", total, width, height, fps, chrome or "bundled Chromium")

    if execution_runtime is not None:
        res = execution_runtime.execute_command(cmd, cwd=Path(project_dir), timeout_seconds=limit)
        exit_code, stdout, stderr = res.exit_code, res.stdout or "", res.stderr or ""
        timed_out = bool(getattr(res, "timed_out", False))
    else:
        try:
            proc = subprocess.run(
                cmd, cwd=str(tdir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                encoding="utf-8", errors="replace", timeout=limit,
            )
            exit_code, stdout, stderr, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as exc:
            exit_code, stdout, stderr, timed_out = -1, (exc.stdout or ""), (exc.stderr or ""), True

    events = _parse_events(stdout if isinstance(stdout, str) else stdout.decode("utf-8", "replace"))
    if timed_out:
        raise BrowserCaptureError(f"Frame capture timed out after {limit:.0f}s ({total} frames requested).")
    if exit_code != 0:
        err = next((e for e in reversed(events) if e.get("event") == "error"), None)
        message = (err or {}).get("message") or (stderr or "").strip()[-500:] or f"exit code {exit_code}"
        if exit_code == 3 or (err or {}).get("code") == 3:
            raise RenderUnavailableError(f"No usable browser for rendering: {message}")
        raise BrowserCaptureError(f"Frame capture failed: {message}")

    done = next((e for e in reversed(events) if e.get("event") == "done"), None)
    if done is None:
        raise BrowserCaptureError("Frame capture exited cleanly but reported no completion event.")
    written = len(list(frames_dir.glob(f"frame_*.{ext}")))
    if written != total:
        raise BrowserCaptureError(f"Expected {total} frames but found {written} in {frames_dir}.")

    return CaptureResult(
        frames=written,
        frames_dir=frames_dir,
        frame_pattern=str(frames_dir / f"frame_%06d.{ext}"),
        image_format="png" if image_format == "png" else "jpeg",
        timelines=list(done.get("timelines", [])),
        blocked_requests=list(done.get("blocked_requests", [])),
        broken_images=list(done.get("broken_images", [])),
        page_errors=list(done.get("page_errors", [])),
        browser=str(done.get("browser", "")),
        seconds=float(done.get("seconds", 0.0)),
    )
