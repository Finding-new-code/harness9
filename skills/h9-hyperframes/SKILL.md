---
name: h9-hyperframes
description: "HyperFrames visual composition compilation, 7 canonical visual component blocks, static linting, and headless MP4 video rendering."
version: 1.0.0
author: Harness 9, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Video, HyperFrames, GSAP, Animation, Rendering, H9]
    related_skills: [h9-production]
prerequisites:
  commands: [python, ffmpeg]
---

# H9 HyperFrames Video Composition & Rendering Skill

Visual composition compiler and video rendering specialist for Harness 9.
Bridges creative narrative planning with mechanical execution by translating
`Script` and `AssetRecord` contracts into the typed `ProductionIRDocument` AST,
assembling HTML/CSS/GSAP timelines, running static linter validation, and executing
headless frame-accurate MP4 video renders.

---

## When to Use

- Compiling narrative scripts and media assets into the typed `ProductionIRDocument` AST.
- Mapping scene nodes to the 7 canonical HyperFrames visual component blocks.
- Verifying composition integrity (0 remote URLs, finite GSAP repeats, responsive viewport units).
- Driving headless video rendering through Playwright and FFmpeg to output broadcast MP4 video.

## When NOT to Use

- Multi-source fact extraction (use `h9-research`).
- Story angle brainstorming and scorecard evaluation (use `h9-content-planning`).
- Voice narration synthesis and Voice QA (use `h9-production`).

---

## Quick Reference

- **Invocation Tool**: `h9.render(production_ir: dict, output_dir: str = None)`
- **AST Seam Interface**: `src/models/ir.py` (`ProductionIRDocument`, `compile_script_to_ir`, `HyperFramesCompiler`).
- **Headless Video Output**: H.264 video + AAC audio at 1920x1080 (16:9) or 1080x1920 (9:16), 30 fps.
- **Composition Linter Invariants**: 100% hermetic (0 external network requests), finite animations, strict temporal conservation.

---

## The 7 Canonical HyperFrames Component Blocks

Every visual scene in a Harness 9 production is powered by one of 7 canonical visual blocks:

1. **`reference_collage_hook`**:
   - Multi-asset floating montage with staggered entrance animations.
   - Ideal for Act 1 opening hooks and high-energy introductions.
2. **`split_screen_intro`**:
   - Two-column or dual-pane layout contrasting competing concepts, eras, or approaches.
   - Ideal for versus comparisons, before/after reveals, and technical trade-offs.
3. **`quote_highlight`**:
   - Bold typography treatment emphasizing an authoritative citation, claim, or testimonial.
   - Features animated quotation marks and highlighted emphasis words.
4. **`timeline_reveal`**:
   - Horizontal or vertical milestone progression tracking historical evolution.
   - Synchronized keyframe markers that illuminate as speech beats advance.
5. **`statistic_reveal`**:
   - Massive numeric metric callout with animated easing counter.
   - Displays label, percentage change or multiplier, and contextual citation badge.
6. **`comparison_panel`**:
   - Multi-row matrix comparing features, specifications, or architectural attributes.
   - Color-coded indicator pills (green/red/neutral) with animated row reveals.
7. **`creator_bottom_collage`**:
   - Lower-third host branding and avatar card overlaid on a scrolling background media carousel.
   - Ideal for Act 4 resolution, conclusion summaries, and call-to-action cards.

---

## Compilation & Rendering Lifecycle

```
┌────────────────────────────────────────────────────────┐
│     Domain Script + Frozen Media Assets + Audio        │
└───────────────────────────┬────────────────────────────┘
                            │
               compile_script_to_ir(...)
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             TYPED PRODUCTION IR SEAM (AST)             │
│  • ProductionIRDocument (Validated Invariants)         │
│    - Contiguity (Δt ≤ 0.05s)                          │
│    - Audio Length Matching (|Σt_scenes - t_audio|≤0.5s)│
│    - Asset Manifest Integrity (0 dangling bindings)    │
│    - Speech Beat Bounds Clamping                       │
└───────────────────────────┬────────────────────────────┘
                            │
              HyperFramesCompiler.compile()
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            HyperFrames Project Workspace               │
│  • index.html (Hermetic DOM container)                 │
│  • styles.css (CSS variables, typography, keyframes)   │
│  • main.js (GSAP timelines synchronized to audio)      │
└───────────────────────────┬────────────────────────────┘
                            │
                  CompositionValidator
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Headless Renderer (Playwright/FFmpeg)       │
│  • Frame capture at 30 fps                             │
│  • FFmpeg audio-video multiplexing                     │
│  • Output: renders/final.mp4 (RenderArtifact)          │
└────────────────────────────────────────────────────────┘
```
