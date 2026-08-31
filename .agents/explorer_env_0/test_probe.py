import sys
import os
import subprocess
import shutil
import json
import wave
import math
import struct
import time

results = {}

# 1. Python Environment
results["python"] = {
    "version": sys.version,
    "executable": sys.executable,
    "prefix": sys.prefix,
    "in_venv": sys.prefix != getattr(sys, "base_prefix", sys.prefix)
}

# 2. Package Availability
packages_to_check = [
    "requests", "urllib.request", "httpx", "aiohttp",
    "bs4", "yaml", "pydantic", "pytest",
    "edge_tts", "pyttsx3", "elevenlabs",
    "playwright", "puppeteer", "selenium",
    "soundfile", "numpy", "torch", "transformers",
    "PIL", "jinja2", "rich", "typer"
]
pkg_status = {}
for pkg in packages_to_check:
    try:
        mod = __import__(pkg)
        pkg_status[pkg] = {"available": True, "version": str(getattr(mod, "__version__", "builtin/unknown"))}
    except Exception as e:
        pkg_status[pkg] = {"available": False, "error": str(e)}
results["packages"] = pkg_status

# 3. CLI Tools Check
cli_tools = ["python", "node", "npm", "npx", "uv", "ffmpeg", "ffprobe", "git", "curl"]
cli_status = {}
for tool in cli_tools:
    path = shutil.which(tool)
    cli_status[tool] = {"found": path is not None, "path": path}
    if path:
        try:
            ver_cmd = [path, "--version"] if tool != "ffmpeg" and tool != "ffprobe" else [path, "-version"]
            out = subprocess.run(ver_cmd, capture_output=True, text=True, timeout=5)
            first_line = (out.stdout or out.stderr).splitlines()[0] if (out.stdout or out.stderr) else ""
            cli_status[tool]["version_output"] = first_line
        except Exception as e:
            cli_status[tool]["version_output"] = f"Error: {e}"
results["cli_tools"] = cli_status

# 4. FFmpeg / FFprobe Specific Test
ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")
results["ffmpeg_test"] = {
    "ffmpeg_path": ffmpeg_path,
    "ffprobe_path": ffprobe_path,
    "path_has_brackets": "[" in (ffmpeg_path or "")
}

# 5. Browser Executables Probe
browsers = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ],
    "chrome_headless_shell": [
        os.path.expandvars(r"%USERPROFILE%\.cache\puppeteer\chrome-headless-shell\win64-145.0.7632.46\chrome-headless-shell-win64\chrome-headless-shell.exe")
    ]
}
browser_status = {}
for name, paths in browsers.items():
    found_path = None
    for p in paths:
        if os.path.exists(p):
            found_path = p
            break
    browser_status[name] = {"found": found_path is not None, "path": found_path}
results["browsers"] = browser_status

# Write JSON intermediate results
with open(r"g:\Finding-new-code\harness9\.agents\explorer_env_0\env_probe_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("Environment probe completed. Results written to env_probe_results.json")
