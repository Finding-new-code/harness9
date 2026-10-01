# Rendering & the media gate

Harness 9 renders a HyperFrames composition (`index.html` + a paused GSAP timeline on
`window.__timelines`) to an MP4, then **measures the result before calling it verified**.

## What changed

| Before | Now |
| --- | --- |
| `renderer.py` ignored the HTML and encoded 64×36 solid-colour PNGs | Headless Chromium seeks the real GSAP timelines frame by frame |
| ffmpeg missing/failing silently produced a solid-colour or mock MP4 | `FFmpegError`; no fallback video |
| "VERIFIED" = the file has a video stream | "VERIFIED" = the **media gate** decoded it and every check passed |
| `evaluate_session` returned hard-coded 0.92–0.96 scores | Scores are measured ratios; unmeasured dimensions are listed as NOT MEASURED |

## Requirements

* Node.js ≥ 18, FFmpeg + ffprobe on `PATH`
* Chrome / Chromium / Edge (set `HARNESS9_CHROME_PATH` if it is not auto-detected). On Linux with no
  system browser, a self-contained Chromium is installed via npm (`HARNESS9_BUNDLED_CHROMIUM=1` forces it).
* First render installs `puppeteer-core` + `gsap@3.12.5` once into `~/.harness9/render-toolchain`.

```bash
python run_harness9.py --check-render        # is the real renderer usable here? (exit 1 + reasons if not)
python run_harness9.py --topic "How GPUs Work" --duration 30
python -m src.evaluation renders/final.mp4 --duration 30 --size 1920x1080 --json   # exit 0 = pass, 1 = fail
```

## Backends and statuses

| `--render-backend` | Meaning | `RenderResult.validation_status` | Run status |
| --- | --- | --- | --- |
| `chrome` (default) | Real render + media gate | `VERIFIED` | `SUCCESS` |
| `chrome`, gate fails | Video moved to `renders/final.rejected.mp4`, `MediaGateError` | — (run fails) | `FAILED` |
| `chrome`, no browser/Node/ffmpeg | `RenderUnavailableError` with install instructions | — (run fails) | `FAILED` |
| `stub` | Explicit dry run: placeholder frames, **never** selected automatically | `STUB` | `PARTIAL` |

Evidence is kept next to the video: `renders/final.gate.json` (every check, value and threshold).

## The media gate (`src/evaluation/media_gate.py`)

Everything is measured by decoding the file with ffmpeg/ffprobe (stdlib only):

`container_streams` · `duration_match` · `av_duration_sync` · `resolution_match` · `fps_match` ·
`not_flat` (luma range per sampled frame) · `visual_detail` (edge density) · `not_black` ·
`has_motion` · `not_frozen` · `audio_not_silent` · `audio_silence_ratio` · `audio_loudness` (warning only).

Thresholds live in `GateThresholds` and were calibrated against synthetic controls
(`tests/test_media_gate.py`: flat, gradient, black, frozen, silent, no-audio, corrupt) and real
Chromium renders. A real 1080p render measured edge density ≈ 0.012 vs a 0.002 floor; the old
placeholder videos measured 0.0.

## Hermetic, deterministic capture

* Frames come from absolute timeline seeks (`tl.time(frame / fps)`), never wall-clock playback.
* The page may only load `file://` and `data:` URLs. CDN GSAP requests are answered from the pinned
  local copy; every other request is blocked and reported as a render warning.
* A composition with no registered timeline, no GSAP, or a frame that fails to capture is an error.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `HARNESS9_RENDER_BACKEND` | `chrome` (default) or `stub` |
| `HARNESS9_CHROME_PATH` | Explicit browser executable |
| `HARNESS9_TOOLCHAIN_DIR` | Where the Node toolchain lives |
| `HARNESS9_AUTO_INSTALL_RENDER_DEPS=0` | Never run `npm install` automatically |
| `HARNESS9_BUNDLED_CHROMIUM` | `1` force / `0` forbid the npm-installed Chromium (Linux) |
| `HARNESS9_CHROME_NO_SANDBOX=1` | Add `--no-sandbox` (automatic when running as root) |

## Known limits

* Capture is sequential: roughly 0.2 s per 1080p frame (a 30 s video takes ~2 minutes).
* Only GSAP timelines are seeked. `<video>`/`<audio>` elements and pure-CSS animations are not.
* Not measured yet (listed as NOT MEASURED in evaluation reports): factual grounding of the narration,
  speech/caption alignment, editorial quality.
* Verified on Linux (Chromium 153, Node 22, FFmpeg 6.1). Windows/macOS paths are implemented but
  not exercised by the author of this change — please run `--check-render` and a draft render there.
