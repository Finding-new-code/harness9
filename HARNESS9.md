# Harness 9 — AI-Native Content Production OS

> **A durable AI studio operating system built on Hermes Agent and HyperFrames that converts a creator topic brief into a broadcast-ready, rendered MP4 video through typed production stages, deterministic gates, and an asset rights ledger.**

---

## Quickstart

### 1. Generate a Video
```bash
# Standard 16:9 widescreen video (1920x1080)
python run_harness9.py --topic "The History of the Transistor" --format 16:9 --duration 30

# Vertical 9:16 short-form video (Shorts / Reels / TikTok - 1080x1920)
python run_harness9.py --topic "How GPUs Work" --format 9:16 --duration 20 --output-dir output/gpu_video

# Fully deterministic offline run (no external API keys or network required)
python run_harness9.py --topic "Quantum Computing Breakthroughs" --offline
```

### 2. Run Acceptance Verification
```bash
# Run the 6-checkpoint verification harness
python verify_pipeline.py --test-mode

# Run the complete test suite (186+ unit, integration & boundary tests)
pytest tests/ -v
```

---

## 5-Stage Production Pipeline

```
[Topic Brief]
     │
     ▼
[Stage 1: Research Engine] ────────► research_dossier.json / .yaml
     │
     ▼
[Stage 2: Asset Engine] ───────────► asset_ledger.json / .yaml + assets/images/*
     │
     ▼
[Stage 3: Script & Voiceover] ─────► SCRIPT.md, STORYBOARD.md + narration.wav
     │
     ▼
[Stage 4: HyperFrames & Render] ───► index.html, styles.css, main.js ──► renders/final.mp4
     │
     ▼
[Stage 5: Orchestrator & CLI] ─────► pipeline_summary.json / .yaml
```

---

## Documentation Index

Comprehensive documentation for all subsystems is available in [`docs/harness9/`](docs/harness9/):

1. [**Architecture & Overview**](docs/harness9/README.md) — System design, contracts, data flow, and design principles.
2. [**CLI Reference**](docs/harness9/CLI_REFERENCE.md) — All command-line arguments, environment variables, flags, and programmatic API usage.
3. [**HyperFrames Composition Guide**](docs/harness9/HYPERFRAMES_GUIDE.md) — HyperFrames project structure (`BRIEF.md`, `STORYBOARD.md`, `SCRIPT.md`), GSAP timeline rules, caption exit rules, and headless render architecture.
4. [**Provenance & Rights Ledger**](docs/harness9/PROVENANCE_AND_RIGHTS.md) — Asset discovery (Wikimedia, Pexels), SHA-256 local freezing, SPDX/CC license classification, and credit package generation.
5. [**Developer & Testing Guide**](docs/harness9/DEVELOPMENT_AND_TESTING.md) — Multi-tier test matrix, adversarial review gates, running CI verification, and offline fallback mechanics.

---

## Output Workspace Structure

Each run produces a standalone, reproducible project workspace:

```
output/my_project/
├── BRIEF.md                 # Topic summary, creative direction, target duration & aspect ratio
├── DESIGN.md                # Visual hierarchy, color palette, typography & motion guidelines
├── SCRIPT.md                # Spoken narration text, timestamps, and emotional cues
├── STORYBOARD.md            # Frame-by-frame visual descriptions, visual cues & assets
├── research_dossier.json    # Machine-readable claims, sources & confidence scores
├── research_dossier.yaml    # Human-readable YAML dossier
├── asset_ledger.json        # Provenance ledger with SPDX licenses, SHA-256 hashes & URLs
├── asset_ledger.yaml        # Human-readable YAML asset ledger
├── pipeline_summary.json    # Run telemetry, execution durations, stage status & costs
├── pipeline_summary.yaml    # Human-readable YAML summary
├── assets/
│   ├── audio/
│   │   └── narration.wav    # Synchronized voiceover audio track
│   └── images/
│       ├── asset_001.png    # Frozen local media asset (SHA-256 verified)
│       └── asset_002.svg    # Procedurally generated vector asset
├── composition/
│   ├── index.html           # HyperFrames HTML5 entrypoint
│   ├── styles.css           # Responsive composition styles & layout rules
│   └── main.js              # Synchronous GSAP master timeline (`window.__timelines["root"]`)
└── renders/
    └── final.mp4            # Broadcast-ready H.264/AAC rendered MP4 video
```
