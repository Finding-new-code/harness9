# Harness 9 — HyperFrames Composition & Rendering Guide

## 1. The HyperFrames Specification

Harness 9 uses **HyperFrames** as its primary visual animation and rendering runtime. Rather than generating video frame-by-frame via pixel-level AI models, HyperFrames composes animated scenes using deterministic **HTML5, modern CSS layout, and GSAP (GreenSock Animation Platform)** timelines, rendered via headless browser frame capture and encoded using FFmpeg.

---

## 2. Project Contract Files

Every generated video project contains standard HyperFrames planning and specification documents:

```
my_project/
├── BRIEF.md                 # Creative intent, format specifications, and narrative goals
├── DESIGN.md                # Typography, palette, layer structure, and visual hierarchy
├── SCRIPT.md                # Spoken audio lines with precise beat timestamps
├── STORYBOARD.md            # Scene breakdown, visual cards, and entrance/exit cues
└── composition/
    ├── index.html           # HTML5 structure with decoupled scene containers
    ├── styles.css           # Responsive styling (16:9 / 9:16) with safe-zone margins
    └── main.js              # Deterministic GSAP master timeline
```

### `BRIEF.md` Example
```markdown
# Video Production Brief: The History of the Transistor

- **Format**: 16:9 (1920x1080)
- **Target Duration**: 30.0s
- **Audience**: General Tech & Science Enthusiasts
- **Core Value**: Explaining how the invention of the solid-state transistor replaced fragile vacuum tubes and sparked the modern computing revolution.
```

### `STORYBOARD.md` Example
```markdown
# Storyboard

### Scene 1: The Vacuum Tube Dilemma (0.0s - 7.5s)
- **Visual Goal**: Establish the bottleneck of early computing (massive, fragile, power-hungry tubes).
- **Media Asset**: `assets/images/asset_001.svg` (Vacuum tube schematic)
- **Animation Cue**: `zoom` for a verified detail; use a hard cut when the next image carries the beat.
- **Narrative Job**: Hook the viewer by presenting the physical limitation of computing before 1947.
```

### Motion Direction

Each scene's `entrance_animation` is a label, not executable JavaScript. The renderer maps it to a bounded preset:

- `rise`: 10-frame upward landing.
- `slide_left`: 10-frame horizontal entrance for a comparison or change of side.
- `zoom`: 12-frame scale landing for a sourced detail.
- `reveal`: 12-frame clip reveal for ordered processes or timelines.
- `fade`: 6-frame opacity transition, when explicitly chosen.
- `cut`: no title entrance; the new image carries the beat.

`transition_out` accepts `cut`, `fade`, or `hold`. Intermediate scenes cut by default; the final scene holds its resolved frame. Unknown entrance strings fall back to `rise` and are never evaluated as code. Keep timed captions for accessibility, and avoid separately rendering the full narration as a static card. Review contact sheets and key frames by eye: the media gate checks technical properties, not taste or clarity.

---

## 3. Determinism & Timing Rules

To ensure 100% reproducible frame rendering, Harness 9 adheres to the following rules:

1. **Synchronous Master Timeline Binding**:
   The GSAP master timeline must be created paused and bound to the global window:
   ```javascript
   window.__timelines = window.__timelines || {};
   const master = gsap.timeline({ paused: true });
   window.__timelines["root"] = master;
   ```

2. **Finite Repeat Math**:
   Infinite loops (`repeat: -1`) cause renderer hangs. Always use bounded loops calculated from scene duration:
   ```javascript
   const cycleDuration = 2.0;
   const sceneDuration = 7.5;
   const repeatCount = Math.max(0, Math.ceil(sceneDuration / cycleDuration) - 1);
   master.to(".pulse-element", { scale: 1.05, repeat: repeatCount, yoyo: true, duration: 1.0 }, 0);
   ```

3. **No External Network Dependencies**:
   All `<img>`, `<video>`, `<audio>`, and `@font-face` resources must resolve to local relative file paths (e.g. `../assets/images/asset_001.png`). Remote HTTP/HTTPS URLs are strictly forbidden inside the composition during rendering.

4. **Deterministic Scene Boundaries**:
   Entrances and fades are finite. Scenes cut at their authored boundary by default; timed captions are explicitly hidden at the end of each speech group. Only an intentional fade is allowed to change that behavior.

---

## 4. Headless Rendering Architecture

The rendering pipeline converts web compositions to broadcast `.mp4` video:

```
[HTML5 + CSS + GSAP Composition]
              │
              ▼
[Headless Browser (Chromium / Puppeteer)]
  • Sets viewport to target resolution (1920x1080 or 1080x1920)
  • Advances GSAP master timeline: `window.__timelines.root.seek(t)`
  • Captures raw frame buffer (PNG/JPEG) for frame t = 0 .. N
              │
              ▼
[FFmpeg encode (H.264 / AAC Muxer)]
  • Reads the captured frame sequence from a temp directory (piping via stdin is on the roadmap)
  • Ingests synchronized `narration.wav` audio track
  • Applies high-compatibility encoding flags:
    `-c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k`
              │
              ▼
[Media gate: decodes the file; flat/black/frozen picture, edge detail, motion,
 audio level, A/V sync, duration, resolution, fps]
              │ pass                      │ fail
              ▼                           ▼
[renders/final.mp4 + final.gate.json]   [renders/final.rejected.mp4 + final.gate.json; run FAILED]
```
