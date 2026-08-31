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
- **Animation Cue**: Slow zoom-in with kinetic headline reveal.
- **Narrative Job**: Hook the viewer by presenting the physical limitation of computing before 1947.
```

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

4. **Guaranteed Caption & Card Exits**:
   Every visual element entering the screen must have an explicit exit transition or opacity fadeout before the subsequent scene begins to prevent DOM visual collision.

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
[FFmpeg Pipe (H.264 / AAC Muxer)]
  • Ingests raw video frame stream via stdin
  • Ingests synchronized `narration.wav` audio track
  • Applies high-compatibility encoding flags:
    `-c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k`
              │
              ▼
[renders/final.mp4]
```
