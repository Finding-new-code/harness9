# HyperFrames Comprehensive Specification Report

## Overview
HyperFrames is a deterministic, code-first video generation and motion graphics framework where HTML/CSS is the single source of truth for visual presentation, GSAP (GreenSock Animation Platform) drives precise timeline animations, and a headless Chromium engine paired with FFmpeg captures and renders frame-by-frame compositions into playable MP4/WebM video.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | CLI Tooling | `init` | Scaffolds a new HyperFrames video project with templates, assets, and config | Project name, flags (`--example <template>`, `--video <file>`, `--audio <file>`, `--non-interactive`) | Directory tree with `index.html`, config, assets, scripts | Fails if destination exists or invalid template | `references/cli.md`, `SKILL.md` |
| 2 | CLI Tooling | `capture` | Ingests a live website URL, extracting assets, computed design tokens, fonts, and screenshots | URL, flags (`-o <dir>`, `--json`, `--skip-assets`) | `capture/` folder containing `screenshots/`, `assets/`, `extracted/tokens.json`, `fonts.json`, `visible-text.txt`, `asset-descriptions.md` | Network/Puppeteer navigation failure | `references/cli.md`, `references/website-to-video.md` |
| 3 | CLI Tooling | `lint` | Static analysis of composition HTML and sub-compositions | File/directory path, flags (`--verbose`, `--json`, `--strict`, `--strict-all`) | Terminal report or JSON of errors, warnings, info notes | Exits non-zero with `--strict` on errors or `--strict-all` on warnings | `references/cli.md`, `SKILL.md` |
| 4 | CLI Tooling | `validate` | Multi-timestamp visual contrast audit checking text against rendered background pixels | Flags (`--no-contrast`) | WCAG AA compliance report (4.5:1 normal text, 3:1 large text) at 5 timestamps | Emits warnings detailing element selectors, measured contrast, and timestamp | `references/cli.md`, `SKILL.md` |
| 5 | CLI Tooling | `inspect` / `layout` | Deep visual layout audit for element clipping, overflow, occlusion, and safe area violations | Path, flags (`--samples <N>`, `--at <t1,t2>`, `--json`) | Per-timestamp layout analysis, bounding box collisions, overflow reports | Flags off-screen, overflowing, or occluded elements | `references/cli.md` |
| 6 | CLI Tooling | `preview` | Long-lived Next.js / Studio preview server on port 3002 with live hot-reload | Directory, flags (`--port <port>`) | Local HTTP preview server at `http://localhost:3002` | Fails if port is occupied; leaves background workers if unstopped | `references/cli.md`, `SKILL.md` |
| 7 | CLI Tooling | `render` | Deterministic frame-by-frame browser capture and FFmpeg audio/video muxing | Flags (`--output <file>`, `--quality <draft|standard|high>`, `--fps <24|30|60>`, `--format <mp4|webm>`, `--workers <N>`, `--docker`, `--gpu`, `--strict`) | Encoded video file (`.mp4` or `.webm`) | Exits non-zero on browser crash, timeout, or lint failure (if `--strict`) | `references/cli.md`, `SKILL.md` |
| 8 | CLI Tooling | `tts` | Local zero-credential speech synthesis using Kokoro-82M neural TTS model | Text string or file, flags (`--voice <voice_id>`, `--output <file>`, `--lang <code>`, `--speed <float>`) | Rendered audio file (`.wav` or `.mp3`) | Fails if `espeak-ng` is missing for non-English locales | `references/cli.md`, `references/features.md` |
| 9 | CLI Tooling | `transcribe` | Automatic speech recognition yielding word-level timestamped transcripts via Whisper | Media file (`.mp3`, `.wav`, `.mp4`, `.srt`, `.vtt`), flags (`--model <model>`, `--language <code>`) | JSON word-level transcript with `start`, `end`, and `word` keys | Model download error or unsupported file format | `references/cli.md`, `references/features.md` |
| 10 | CLI Tooling | `doctor` | Diagnostics for runtime environment (Node >= 22, FFmpeg, RAM, Chrome binary, CLI version) | None | Diagnostic status checks & system info | Warns/errors on missing dependencies or low RAM (<4GB) | `references/cli.md`, `SKILL.md` |
| 11 | CLI Tooling | `browser` | Manages Puppeteer bundled `chrome-headless-shell` binary | Flags (`--install`, `--path`, `--clean`) | Path output or binary download progress | Network error on download | `references/cli.md`, `references/troubleshooting.md` |
| 12 | CLI Tooling | `add` | Installs reusable visual blocks and WebGL shader transitions from catalog | Component/shader name (`flash-through-white`, `lower-third`, etc.), flags (`--list`) | Local component files installed to project | Error if package/block name not found in catalog | `references/cli.md`, `references/features.md` |
| 13 | Composition Core | Root Composition Contract | Top-level HTML structure defining canvas bounds, global duration, and track containers | `index.html` with root `<div>` having `data-composition-id="root"`, `data-start="0"`, `data-duration="N"`, `data-width="W"`, `data-height="H"` | Full-bleed video canvas evaluated by browser | Fails if wrapped in `<template>` or missing `data-composition-id` | `references/composition.md` |
| 14 | Composition Core | Sub-Composition Contract | Modular external HTML compositions loaded into parent tracks | `<template id="...">` wrapper containing `<div data-composition-id="...">` loaded via `data-composition-src` | Nested reusable visual scene | Must use `<template>` wrapper (unlike root) | `references/composition.md` |
| 15 | Composition Core | Track & Clip Timing Schema | Deterministic placement and duration metadata via HTML5 data-attributes | Attributes: `data-start`, `data-duration`, `data-track-index`, `data-media-start`, `data-volume` | Non-linear multitrack timeline layout | Overlapping clips on identical `data-track-index` cause lint error | `references/composition.md` |
| 16 | Animation Engine | Timeline Registration & State | GSAP timeline initialization and global window registry binding | `window.__timelines["<id>"] = gsap.timeline({ paused: true })` | Bound GSAP timeline controllable by frame capture player | Unregistered timeline causes frozen/blank render | `references/composition.md`, `references/gsap.md` |
| 17 | Animation Engine | Deterministic Animation Rules | Strict math and timing isolation ensuring frame reproducibility | Seeded PRNGs, pure math offsets, synchronous timeline construction | Identical visual output across arbitrary frame evaluation order | `Math.random()`, `Date.now()`, or `async` breaks reproducibility | `references/composition.md`, `references/gsap.md` |
| 18 | Animation Engine | Finite Loop Calculation | Required formula for looping tweens/effects | `repeat: Math.ceil(duration / cycleDuration) - 1` | Bounded repeating animation | `repeat: -1` breaks capture engine and causes render hang | `references/composition.md`, `references/gsap.md` |
| 19 | Animation Engine | Entrance / Exit Policy | Strict hierarchy preventing blank frame glitches across scene boundaries | `gsap.from()` on all scene elements; zero `gsap.to()` exit tweens (except final scene) | Seamless transition-driven scene changes | Adding exit tweens to intermediate scenes causes black/blank flash | `references/composition.md`, `references/features.md` |
| 20 | Audio & Narration | Media Element Decoupling | Muted video tag requirement paired with dedicated audio tags | `<video muted playsinline>` + separate `<audio data-track-index="...">` | Autoplay-compliant video with independent audio muxing | Unmuted video fails under browser autoplay security policies | `references/composition.md` |
| 21 | Audio & Narration | Word-Level Synchronized Captions | Kinetic text display synced to Whisper word timestamps | Transcript JSON, layout width, font styling, tone presets | Word-by-word highlighted text rendered to canvas | Overlapping or lingering captions if hard exit kill is omitted | `references/features.md` |
| 22 | Audio & Narration | Caption Exit Guarantee | Hard instant kill preventing text ghosting into subsequent phrases | `tl.set(groupEl, { opacity: 0, visibility: "hidden" }, group.end)` | Zero residual DOM visibility after phrase end | Ghosted captions visible behind subsequent scenes | `references/features.md` |
| 23 | Audio & Narration | Dynamic Font Fitting | Text auto-scaling utility avoiding multi-line clipping | `window.__hyperframes.fitTextFontSize(text, { maxWidth, fontFamily, fontWeight })` | Computed `{ fontSize }` fitting within safe pixel bounds | Text overflow outside stage safe area | `references/composition.md`, `references/features.md` |
| 24 | Audio & Narration | Audio-Reactive Visuals | Pre-computed frequency band amplitude modulation of CSS/GSAP properties | `AUDIO_DATA` JSON with per-frame frequency bands (bass, mid, treble) sampled via `tl.call()` loop | Scaled, pulsing, glowing elements synchronized to music | Single continuous tween fails to track dynamic audio peaks | `references/features.md` |
| 25 | Visual Effects | Marker-Style Highlighting | Deterministic CSS + SVG stroke animations for text emphasis | CSS transform `scaleX` on highlight bars, `stroke-dashoffset` on SVG circles, bursts, scribbles | Animated hand-drawn marker effect | Animated SVG filters cause non-deterministic seeking issues | `references/features.md` |
| 26 | Scene Transitions | CSS Transitions | Native DOM container transform and opacity transitions | GSAP tweens on `.scene` containers (`push slide`, `blur crossfade`, `zoom through`) | Smooth hardware-accelerated scene transitions | Inter-scene timing gaps if durations mismatch | `references/features.md` |
| 27 | Scene Transitions | WebGL Shader Transitions | Per-pixel texture compositing via html2canvas and GLSL shaders | `@hyperframes/shader-transitions` shaders (`flash-through-white`, `liquid-wipe`, `cross-warp-morph`, etc.) | Canvas-based shader morph between scene snapshots | Failing to set explicit `background-color` yields black textures | `references/features.md` |
| 28 | Quality Assurance | Animation Choreography Map | Offline AST/timeline analysis script inspecting tween pacing and dead zones | `node skills/hyperframes/scripts/animation-map.mjs <dir> --out <dir>/.hyperframes/anim-map` | `animation-map.json`, ASCII Gantt chart, dead zone (>1s) alerts, pacing warnings | Flags `offscreen`, `collision`, `invisible`, `paced-fast`, `paced-slow` | `SKILL.md` |

---

## Edge Cases

| # | Feature | Input / Trigger Condition | Observed & Expected Behavior |
|---|---------|---------------------------|------------------------------|
| 1 | GSAP Timeline | `repeat: -1` on tween or timeline | **Observed Failure:** Engine calculates infinite duration; Puppeteer frame capture loop never terminates and hangs indefinitely.<br>**Required Behavior:** Always compute finite repeat: `Math.ceil(duration / cycleDuration) - 1`. |
| 2 | Root Composition HTML | Wrapping top-level `index.html` body inside `<template id="...">` | **Observed Failure:** Browser parses template as inert fragment; DOM is empty; render outputs completely black/blank video.<br>**Required Behavior:** Root composition must place `<div data-composition-id="root">` directly in `<body>`. `<template>` is reserved exclusively for external sub-compositions. |
| 3 | Media Playback | Calling native `video.play()` or `audio.play()` in JavaScript | **Observed Failure:** Desynchronizes playback from the frame-stepping clock; causes race conditions during headless capture.<br>**Required Behavior:** Never call play/pause/seek methods. The HyperFrames capture harness controls time progression via GSAP seek. |
| 4 | Media Separation | Providing audio via an unmuted `<video>` element | **Observed Failure:** Browser autoplay security blocks unmuted playback; video renders muted with zero audio track.<br>**Required Behavior:** Video must be `<video muted playsinline>` and audio must reside in a separate `<audio>` tag. |
| 5 | Timeline Construction | Wrapping GSAP timeline setup in `async/await`, `setTimeout`, or `Promise.then` | **Observed Failure:** Headless capture inspects `window.__timelines` immediately upon page load event; async timelines are undefined at capture start.<br>**Required Behavior:** All timeline creation, tween definitions, and `window.__timelines` assignments must execute synchronously. |
| 6 | Caption Rendering | Omitting hard `tl.set()` kill at caption phrase boundary (`group.end`) | **Observed Failure:** CSS opacity tweens leave residual DOM elements visible when subsequent phrases render, causing overlapping text artifacts.<br>**Required Behavior:** Follow every caption exit tween with `tl.set(groupEl, { opacity: 0, visibility: "hidden" }, group.end)`. |
| 7 | Audio Reactivity | Creating a single long tween across the entire clip instead of frame sampling | **Observed Failure:** GSAP interpolates between start and end values linearly; animation fails to track instantaneous waveform amplitude peaks.<br>**Required Behavior:** Construct a synchronous `for` loop executing `tl.call(drawCallback, [], frameIndex / fps)`. |
| 8 | Multi-scene Transitions | Adding `gsap.to(el, { opacity: 0 })` exit animations to outgoing scenes | **Observed Failure:** Outgoing scene content vanishes before the transition completes, resulting in empty/black frames during transition playback.<br>**Required Behavior:** Use entrance animations (`gsap.from()`) on all scenes; never use exit tweens on intermediate scenes (the transition itself acts as the exit). Only the final scene may fade out. |
| 9 | Whisper Transcription | Passing `--model small.en` on audio containing non-English speech | **Observed Failure:** Whisper `.en` models translate speech into English instead of transcribing native language phonemes.<br>**Required Behavior:** Use multilingual models (`--model small`) and explicit language tags (`--language <code>`). |
| 10 | Headless Chrome Protocol | Running on Chromium 147+ without `chrome-headless-shell` or fallback | **Observed Failure:** `Protocol error (HeadlessExperimental.beginFrame): 'HeadlessExperimental.beginFrame' wasn't found`.<br>**Required Behavior:** Ensure `hyperframes >= 0.4.2` or set `export PRODUCER_FORCE_SCREENSHOT=true`. Pre-install `chrome-headless-shell`. |
| 11 | Preview Server Cleanup | Leaving `npx hyperframes preview` running in background on headless/WSL/CI | **Observed Failure:** SwiftShader software WebGL processes peg CPU cores at 300%+ indefinitely.<br>**Required Behavior:** Always issue `pkill -f "hyperframes.*preview"` and `pkill -f chrome-headless-shell` when preview sessions conclude. |
| 12 | Shader Transitions CSS | Using CSS `transparent` keyword inside linear/radial gradients | **Observed Failure:** html2canvas / WebGL texture capture interpolates `transparent` as `rgba(0,0,0,0)`, creating harsh dark/black fringing artifacts.<br>**Required Behavior:** Use explicit color with zero alpha: `rgba(R, G, B, 0)`. |
| 13 | Shader Transitions CSS | Using CSS custom properties (`var(--color)`) during shader texture capture | **Observed Failure:** html2canvas fails to resolve custom variables reliably, rendering elements as blank/black.<br>**Required Behavior:** Use literal hex or rgba values on elements visible during shader capture. |

---

## In-Depth Technical Specification

### 1. Exact File Structure & Project Conventions

A standard HyperFrames project adheres to a strict artifact pipeline and folder layout. Every creative project progresses through specific gated document stages before code generation:

```
my-video-project/
├── BRIEF.md                    # Core topic, audience, objective, and narrative arc
├── DESIGN.md                   # Brand guidelines, color palette, typography, motion rules, anti-patterns
├── SCRIPT.md                   # Timed voiceover script with scene breakdown & timestamped beats
├── STORYBOARD.md               # Text-based scene plans describing hero frames, entrances, transitions
├── REVIEW.md                   # Iterative feedback log from draft rendering passes
├── index.html                  # Root composition (single source of truth for video)
├── styles.css                  # Optional external stylesheet (or inline <style>)
├── main.js                     # Optional external animation script (or inline <script>)
├── assets/                     # Downloaded media, images, vector graphics, audio files
│   ├── narration.wav           # Voiceover audio generated by TTS
│   ├── background.png          # Visual hero assets
│   └── transcript.json         # Word-level timestamped transcription from Whisper
├── compositions/               # Optional sub-compositions loaded via data-composition-src
│   ├── intro.html              # Sub-composition wrapped in <template>
│   └── scene2.html             # Sub-composition wrapped in <template>
├── captures/                   # (If generated via website capture)
│   └── <hostname>/capture/     # Extracted screenshots, tokens.json, fonts.json
└── renders/                    # Output directory for rendered videos
    ├── draft.mp4               # Draft review render
    └── final.mp4               # High-quality delivery render
```

#### Document Gating Lifecycle:
1. **`BRIEF.md` (Topic & Goal):** Defines the narrative premise, target duration (e.g., 30s-60s), and format (9:16 portrait or 16:9 landscape).
2. **`DESIGN.md` (HARD GATE):** Must be established prior to writing any HTML. Must define:
   - `## Brand`: Name and core mission.
   - `## Colors`: 3-5 explicit hex codes with functional roles (Background, Primary Accent, Secondary Text, Base Text).
   - `## Typography`: Display font (e.g., Inter Tight 700) and Body font (e.g., Inter 400).
   - `## Motion`: Motion mood (cinematic, explosive, technical, fluid) and standard easing curves.
   - `## What NOT to Do`: Explicit anti-patterns (e.g., no default blue `#3b82f6`, no generic drop shadows, no unbranded fonts).
3. **`SCRIPT.md` (Timestamped Narration):** Scene-by-scene script. Scene durations MUST derive directly from audio/TTS duration rather than arbitrary estimates.
4. **`STORYBOARD.md` (Visual Plan):** For each scene, documents:
   - **Hero Frame:** The single moment when the maximum number of scene elements are simultaneously visible.
   - **Entrance Animation:** How each element enters the scene (`gsap.from()`).
   - **Transition Out:** How the scene transitions to the next (e.g., `push-slide`, `flash-through-white`).
5. **Composition HTML (`index.html`):** The executable code representation.

---

### 2. GSAP Timeline & Animation Conventions

#### Resolution & Aspect Ratio Rules
HyperFrames compositions are dimensionally fixed at the root element level:
- **Vertical Short-Form (9:16):** `data-width="1080"` and `data-height="1920"` (TikTok, Instagram Reels, YouTube Shorts).
  - *Safe Zone:* Captions positioned ~600-700px from the bottom to prevent obstruction by social platform UI overlays (likes, comments, audio labels).
  - *Typography:* Headlines 60px+, Body 24px+, Captions 56-80px.
- **Landscape Standard (16:9):** `data-width="1920"` and `data-height="1080"` (YouTube, Web, Desktop).
  - *Safe Zone:* Captions positioned 80-120px from bottom, centered.
  - *Typography:* Headlines 72-96px, Body 20px+, Data labels 16px+.

#### Framerate & Timing Standards
- Framerates supported: **24 fps**, **30 fps** (default standard), **60 fps** (high motion fidelity).
- Duration precedence: `data-duration` on the composition element dictates total render length, taking strict precedence over the GSAP timeline's internal duration.

#### GSAP Timeline Contract
1. **Global Registry:** Every composition must register its timeline on the global window object:
   ```javascript
   window.__timelines = window.__timelines || {};
   const tl = gsap.timeline({ paused: true, defaults: { duration: 0.6, ease: "power2.out" } });
   window.__timelines["root"] = tl;
   ```
2. **Paused Initialization:** Timelines MUST start with `{ paused: true }`. The HyperFrames headless capture engine controls seeking and time progression.
3. **Finite Repeat Calculations:** Infinite loops (`repeat: -1`) cause render hangs. All recurring animations must use calculated bounds:
   ```javascript
   const repeatCount = Math.ceil(totalDuration / cycleDuration) - 1;
   tl.to(element, { rotation: 360, repeat: repeatCount, ease: "none" }, 0);
   ```
4. **Deterministic Execution:**
   - No non-deterministic functions (`Math.random()`, `Date.now()`, `performance.now()`). Use seeded pseudo-random number generators (e.g., mulberry32) if variation is needed.
   - All timeline construction must occur synchronously at page evaluation time. Do not wrap in `async/await`, `setTimeout`, or `requestAnimationFrame`.
5. **DOM Layout & Hierarchy:**
   - Write static HTML/CSS for the **hero frame** first using flexbox containers with internal padding (`.scene-content { width: 100%; height: 100%; padding: 48px; display: flex; flex-direction: column; gap: 24px; box-sizing: border-box; }`).
   - Never use `position: absolute; top: Npx` on content containers (causes unrecoverable overflow). Absolute positioning is restricted to decorative layers and fixed overlay badges.
6. **Entrance vs Exit Invariants:**
   - **Always use entrance animations:** Every element must animate into view using `gsap.from(...)`.
   - **Never use exit animations on intermediate scenes:** The scene transition (CSS or WebGL shader) owns the outgoing dismissal. Calling `gsap.to(..., { opacity: 0 })` creates black/blank gaps during transitions.
   - **Final scene exception:** The final scene may fade out to black/brand color using `gsap.to()`.

---

### 3. Audio Synchronization Rules

#### Media Decoupling Contract
- Under browser security and autoplay policies, video elements cannot reliably trigger synchronized unmuted audio during automated evaluation.
- **Rule:** `<video>` elements must always specify `muted playsinline`.
- Audio tracks must reside in dedicated `<audio>` elements with timing attributes:
  ```html
  <audio id="narration" data-start="0" data-duration="28.5" data-track-index="10" data-volume="1.0" src="assets/narration.wav"></audio>
  <audio id="bgm" data-start="0" data-duration="28.5" data-track-index="11" data-volume="0.25" src="assets/music.mp3"></audio>
  ```
- **Track Collision Rule:** Clips sharing the same `data-track-index` must never overlap in their `[data-start, data-start + data-duration]` intervals.

#### Voice Synthesis (Kokoro-82M TTS)
- Synthesizes clean narration locally without API keys:
  ```bash
  npx hyperframes tts "Narration text" --voice af_nova --output assets/narration.wav
  ```
- **Voice Mapping Conventions:**
  - `af_heart` / `af_nova` (American Female): Warm, professional, ideal for product explainers and storytelling.
  - `am_adam` / `am_michael` (American Male): Authoritative, tutorial, technical.
  - `bf_emma` / `bm_george` (British English): Documentary, formal.
  - Language prefix auto-inferencing: `a`=en-US, `b`=en-GB, `e`=es, `f`=fr, `h`=hi, `i`=it, `j`=ja, `p`=pt-BR, `z`=zh.
- **Pacing / Speed:** `1.0` is standard conversational pace (~140-160 wpm); `0.7-0.8` for dense tutorials; `1.1-1.2` for dynamic short-form hooks.

#### Whisper Word-Level Transcription & Captions
- Audio files are transcribed using Whisper to extract word-level timestamps:
  ```bash
  npx hyperframes transcribe assets/narration.wav --model small
  ```
- **Whisper Language Rule:** Never use `.en` models (e.g. `small.en`) on non-English audio, as `.en` forces English translation rather than transcription.
- **Caption Structuring & Layout:**
  - Word groups: 2-3 words for high energy/hype; 3-5 words for conversational flow.
  - Safe Area Clamping: Use `window.__hyperframes.fitTextFontSize(text, { maxWidth, fontFamily, fontWeight })` to compute exact font sizes that guarantee zero text wrapping outside safe bounds.
  - **Caption Exit Guarantee:** To prevent visual leaking across phrase boundaries, every caption group MUST append an instantaneous hard visibility kill at its end timestamp:
    ```javascript
    tl.to(groupEl, { opacity: 0, scale: 0.95, duration: 0.12, ease: "power2.in" }, group.end - 0.12);
    tl.set(groupEl, { opacity: 0, visibility: "hidden" }, group.end); // Hard kill
    ```

#### Audio-Reactive Visual Modulation
- Real-time Web Audio API analysis is non-deterministic in headless renderers.
- Audio waveforms are pre-extracted into frame-indexed frequency buckets:
  ```javascript
  const AUDIO_DATA = {
    fps: 30,
    totalFrames: 900,
    frames: [
      { bands: [0.82, 0.45, 0.31, 0.12, 0.08, /* ... */] },
      // ... frame array normalized 0.0 to 1.0
    ]
  };
  ```
- Frequency Mapping:
  - `bands[0]` (Bass): Drives `scale` pulse on visual containers or cards (3-6% variation for text; 10-30% for background cards).
  - `bands[12-14]` (Treble): Drives `textShadow` and `boxShadow` glow intensity.
  - Mid-range bands: Drives `borderRadius` and border highlights.
- **Frame Sampling Loop:** Reactivity is wired via per-frame `tl.call()` invocations:
  ```javascript
  for (let f = 0; f < AUDIO_DATA.totalFrames; f++) {
    tl.call(
      ((frame) => () => renderAudioFrame(frame))(AUDIO_DATA.frames[f]),
      [],
      f / AUDIO_DATA.fps
    );
  }
  ```

---

### 4. Validation Rules & Quality Assurance

HyperFrames incorporates a multi-tier validation suite to verify compositions prior to rendering:

```
               ┌───────────────────────┐
               │    HTML Composition   │
               └───────────┬───────────┘
                           │
             ┌─────────────▼─────────────┐
             │   npx hyperframes lint    │ ───► Track overlaps, missing IDs, unpaused timelines
             └─────────────┬─────────────┘
                           │
             ┌─────────────▼─────────────┐
             │ npx hyperframes validate  │ ───► WCAG AA contrast sampling (4.5:1 / 3:1)
             └─────────────┬─────────────┘
                           │
             ┌─────────────▼─────────────┐
             │  npx hyperframes inspect  │ ───► Visual layout overflow & element occlusion
             └─────────────┬─────────────┘
                           │
             ┌─────────────▼─────────────┐
             │   animation-map.mjs       │ ───► Gantt dead zones (>1s), pacing violations
             └─────────────┬─────────────┘
                           │
                           ▼
                 Ready for Render
```

1. **Static Analysis (`npx hyperframes lint`):**
   - Asserts existence of `data-composition-id` on root and sub-compositions.
   - Verifies all media elements contain `data-start`, `data-duration`, and `data-track-index`.
   - Confirms that clips on the same track index do not overlap in time.
   - Asserts that `window.__timelines["<id>"]` is registered and initialized `{ paused: true }`.
   - Checks that no tweens specify forbidden `repeat: -1`.
   - Verifies that all local assets referenced in `src` attributes exist on disk.
2. **Contrast Validation (`npx hyperframes validate`):**
   - Automatically seeks the composition to 5 representative timestamps.
   - Captures rendered canvas frames and samples background pixels behind every text bounding box.
   - Flags WCAG AA contrast failures where contrast is `< 4.5:1` for standard text or `< 3:1` for large text (24px+ or 19px+ bold).
3. **Visual Layout Inspection (`npx hyperframes inspect` / `layout`):**
   - Inspects computed DOM layout bounds across sampled timestamps (e.g. `--samples 15` or `--at 1.5,4.0,7.25`).
   - Identifies text elements wrapping beyond safe canvas boundaries.
   - Detects visual collisions and z-index occlusion between foreground cards and background elements.
4. **Choreography & Pacing Verification (`animation-map.mjs`):**
   - Analyzes tween distribution across the timeline.
   - Flags dead zones (>1.0 second duration with zero active animations).
   - Identifies pacing anomalies: `paced-fast` (<0.2s duration) or `paced-slow` (>2.0s duration).
   - Generates ASCII Gantt timeline representations and structured JSON metrics (`animation-map.json`).

---

### 5. Rendering Process & MP4 Encoding Architecture

The rendering pipeline translates deterministic DOM/GSAP states into broadcast-ready video files:

```
┌───────────────────────────┐
│     index.html & GSAP     │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  Puppeteer / Chrome CDP   │  ◄── chrome-headless-shell (HeadlessExperimental.beginFrame)
│  (Timeline Frame Stepping)│      Fallback: PRODUCER_FORCE_SCREENSHOT=true
└─────────────┬─────────────┘
              │
              ▼ [Raw RGB/PNG Frame Stream]
┌───────────────────────────┐
│       FFmpeg Worker       │  ◄── Encodes H.264 (libx264) / AAC
│  (Mux Video + Audio Tracks)│      Muxes narration.wav + background audio
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│      output/final.mp4     │
└───────────────────────────┘
```

#### Step-by-Step Execution Flow:
1. **Engine Initialization:**
   - HyperFrames spawns a headless browser worker pool (`--workers <N>`, default auto-scaled to CPU cores).
   - Preferred binary: Puppeteer-managed `chrome-headless-shell`.
2. **Page Loading & Resource Binding:**
   - Navigates to local `index.html`.
   - Fonts declared via CSS `@font-face` or curated system stacks are embedded by the compiler.
   - Synchronously extracts registered timelines from `window.__timelines`.
3. **Deterministic Frame Stepping:**
   - For frame index $f \in [0, \text{fps} \times \text{duration} - 1]$, computes target timestamp $t = f / \text{fps}$.
   - Advances GSAP timeline via `tl.seek(t, false)`.
   - Dispatches CDP `HeadlessExperimental.beginFrame` (or screenshot capture) to render and extract the exact frame buffer at full display resolution (1080x1920 or 1920x1080).
4. **Audio Extraction & FFmpeg Muxing:**
   - Scans DOM for all `<audio>` elements with valid `data-start`, `data-duration`, `data-media-start`, and `data-volume` attributes.
   - Invokes FFmpeg to encode the incoming image stream via `libx264` (video) and muxes the audio streams with exact time-offset filters (`adelay`, `volume`, `amix`).
5. **Render Profiles & Quality Flags:**
   - `--quality draft`: Faster encode with higher CRF / faster preset for rapid iteration.
   - `--quality standard`: Balanced CRF and encoding speed for review passes.
   - `--quality high`: High bitrate, slow preset, optimal for final delivery.
   - `--fps 24|30|60`: Target output framerate.
   - `--format mp4|webm`: Output container (MP4 for broad social/video compatibility; WebM for transparent alpha channel rendering).
   - `--docker`: Runs the rendering pipeline inside a containerized sandbox for 100% byte-identical reproducible rendering across operating systems.
6. **Post-Render Integrity Assertions:**
   - File presence and non-zero byte size verification: `ls -lh final.mp4`.
   - Duration alignment check: `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 final.mp4` matching `data-duration` within ±0.1s.
   - Audio stream confirmation: `ffprobe -v error -show_streams -select_streams a final.mp4`.
   - Visual frame sanity check: `ffmpeg -i final.mp4 -ss 00:00:05 -vframes 1 preview.png`.

---

## Architectural Summary & Integration Guide for Harness 9

When constructing automated pipelines that generate HyperFrames compositions (such as in Harness 9):
1. **Asset Staging:** Download and freeze all visual assets and synthesized audio locally into `assets/` before generating HTML.
2. **Design Gating:** Synthesize `DESIGN.md`, `SCRIPT.md`, and `STORYBOARD.md` to establish visual rules, color palettes, and timestamped beats.
3. **HTML/GSAP Generation:** Generate `index.html` referencing local relative paths (`assets/...`), defining `data-start`, `data-duration`, `data-track-index`, and registering `window.__timelines["root"] = gsap.timeline({ paused: true })`.
4. **Validation Suite:** Run static structural checks (`lint`), contrast verification (`validate`), and layout collision checks (`inspect`).
5. **Render Execution:** Execute headless frame capture and FFmpeg audio muxing to produce the final playable `.mp4` file.
