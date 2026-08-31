# Handoff Report: HyperFrames Specification Mining

## 1. Observation
Authoritative sources inspected within project directory `g:\Finding-new-code\harness9`:
- `g:\Finding-new-code\harness9\ORIGINAL_REQUEST.md` (Lines 1–42)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\SKILL.md` (Lines 1–209)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\references\composition.md` (Lines 1–130)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\references\features.md` (Lines 1–290)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\references\gsap.md` (Lines 1–137)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\references\cli.md` (Lines 1–186)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\references\troubleshooting.md` (Lines 1–161)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\references\website-to-video.md` (Lines 1–146)
- `g:\Finding-new-code\harness9\optional-skills\creative\hyperframes\scripts\setup.sh` (Lines 1–136)

Direct verbatim observations from authoritative files:
1. **Composition Structure (`references/composition.md` lines 10–35):**
   Root `index.html` must define top-level `<div id="stage" data-composition-id="root" data-start="0" data-duration="10" data-width="1920" data-height="1080">`. Sub-compositions use `<template id="...">` while the root composition MUST NOT use `<template>`.
2. **Timeline Registration Contract (`references/composition.md` lines 29–33, 76–82):**
   `window.__timelines = window.__timelines || {}; const tl = gsap.timeline({ paused: true }); window.__timelines["root"] = tl;`. Duration is governed strictly by `data-duration`, not GSAP timeline internal length.
3. **Deterministic Constraint & Loop Rule (`references/composition.md` lines 85–88):**
   No `Math.random()` or `Date.now()`. `repeat: -1` is strictly forbidden because infinite tweens break the frame capture engine; finite repeats must be calculated via `Math.ceil(duration / cycleDuration) - 1`.
4. **Media Separation Rule (`references/composition.md` line 91, `references/troubleshooting.md` lines 118–124):**
   `<video>` elements must always be `muted playsinline`. Audio is always placed in a separate `<audio>` tag to satisfy browser autoplay security and ensure independent FFmpeg audio muxing.
5. **Layout Container Best Practice (`references/composition.md` lines 92–93, 101–103):**
   Content containers must use `.scene-content { width: 100%; height: 100%; padding: Npx; display: flex; flex-direction: column; gap: Npx; box-sizing: border-box; }` rather than absolute positioning to avoid layout clipping.
6. **Scene Transition Invariant (`references/composition.md` lines 97–102, `references/features.md` lines 219–290):**
   Every element animates in via `gsap.from()`. Never use exit animations (`gsap.to()`) on intermediate scenes because the transition itself owns the exit. The final scene alone may fade out.
7. **Caption Synchronization & Hard Exit Kill (`references/features.md` lines 58–64):**
   Every caption phrase group requires a hard visibility kill: `tl.set(groupEl, { opacity: 0, visibility: "hidden" }, group.end);` to prevent phrase ghosting into later scenes.
8. **Audio-Reactivity Loop (`references/features.md` lines 150–161):**
   Audio-reactivity requires per-frame sampling inside the timeline via a `for` loop executing `tl.call(drawCallback, [], f / fps)`, not a single long tween.
9. **Rendering & Tooling (`references/cli.md` lines 87–109, `references/troubleshooting.md` lines 3–42):**
   Rendering executes via headless Chromium (`chrome-headless-shell` or screenshot fallback `PRODUCER_FORCE_SCREENSHOT=true`) stepping GSAP frame-by-frame and muxing video/audio with FFmpeg into `.mp4` or `.webm`.

## 2. Logic Chain
1. *From Observation 1 & 2:* The rendering engine discovers scenes and timelines by scanning `index.html` for `data-composition-id="root"` and evaluating `window.__timelines["root"]`. If `index.html` is wrapped in `<template>` or the timeline is not registered with `{ paused: true }`, the engine fails or produces blank output.
2. *From Observation 3 & 8:* Frame-by-frame rendering relies on deterministic seeking (`tl.seek(t)`). Infinite repeats (`repeat: -1`) or continuous time calls (`Date.now()`, single interpolating tweens) corrupt frame synchronization. Therefore, finite repeat math and discrete `tl.call()` sampling loops are mandatory.
3. *From Observation 4 & 9:* Automated headless browsers enforce strict media policies (autoplay blocking unmuted video elements). Decoupling `<video muted playsinline>` and `<audio>` allows FFmpeg to independently extract and mux clean audio streams with exact track offsets (`data-start`, `data-track-index`).
4. *From Observation 6 & 7:* Visual continuity during transitions requires incoming elements to be positioned at their hero frame while outgoing elements remain visible until the transition overlay passes. Premature exit tweens or missing caption visibility kills create visual stutter and text overlap artifacts.
5. *From Observation 5 & `references/cli.md` validation rules:* Automated audits (`npx hyperframes lint`, `validate`, `inspect`) enforce structure, WCAG AA contrast (4.5:1 / 3:1), and layout safety prior to high-cost rendering passes.

## 3. Caveats
- The external npm package `hyperframes` CLI binary was probed; its full execution in local environments depends on Node.js >= 22, FFmpeg, and Puppeteer `chrome-headless-shell` caching.
- If the global or npx package resolution is running in an offline or sandboxed environment, a standalone mock or local node script matching the exact HyperFrames file structure and GSAP contracts can be validated and rendered using Puppeteer and FFmpeg directly.

## 4. Conclusion
HyperFrames provides a fully deterministic, code-first video composition specification built on standard Web technologies (HTML/CSS/GSAP) and media tools (Puppeteer + FFmpeg). The complete specification—including project directory layout, document gating (`BRIEF.md` -> `DESIGN.md` -> `SCRIPT.md` -> `STORYBOARD.md` -> `index.html`), GSAP timeline conventions, aspect ratio definitions (9:16 vertical and 16:9 landscape), audio/TTS synchronization, multi-tier validation (`lint`, `validate`, `inspect`), and headless frame capture rendering—has been thoroughly mined and documented in `g:\Finding-new-code\harness9\.agents\spec_miner_hyperframes_0\report.md`.

## 5. Verification Method
1. Inspect the generated report:
   ```bash
   view_file g:\Finding-new-code\harness9\.agents\spec_miner_hyperframes_0\report.md
   ```
2. Verify structural adherence of any generated HyperFrames project against the mined specification:
   - Check presence of `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, and `index.html`.
   - Validate that `index.html` root `<div>` has `data-composition-id="root"`, `data-width`, `data-height`, `data-duration`.
   - Validate that `window.__timelines["root"]` is assigned a `gsap.timeline({ paused: true })`.
   - Confirm all `<video>` tags are `muted playsinline` and all `<audio>` tags are separate.
   - Confirm all caption groups implement `tl.set(..., { opacity: 0, visibility: "hidden" }, group.end)`.
3. Verify rendering pipeline requirements:
   ```bash
   node --version      # Must be >= 22
   ffmpeg -version     # Must be present on PATH
   ```
