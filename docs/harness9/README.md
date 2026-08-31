# Harness 9 — Architecture & System Design

## 1. System Overview

Harness 9 is an AI-native content production operating system built upon **Hermes Agent** and **HyperFrames**. It decouples creative intelligence and high-level production reasoning from underlying rendering mechanics, enforcing strict determinism, rights provenance, and broadcast quality standards.

```
                    HARNESS 9
             "AI Creator Studio Brain"

 ┌────────────────────────────────────────────┐
 │              Studio Control Plane          │
 │                                            │
 │ Showrunner / Planning / Quality / Memory   │
 │ Production Contracts / Evaluators          │
 └────────────────────┬───────────────────────┘
                      │
              Production Workflow
                      │
        ┌─────────────▼─────────────┐
        │ Durable Workflow Engine   │
        │       (Orchestrator)      │
        └─────────────┬─────────────┘
                      │
       ┌──────────────┼────────────────┐
       │              │                │
       ▼              ▼                ▼
 Research Engine  Asset & Media     HyperFrames
 & Dossier        Rights Ledger     Renderer
       │              │                │
 Multi-intent     Wikimedia         HTML5/CSS/GSAP
 Web Search       Pexels            Headless Render
 Claim Scoring    SHA-256 Freezer   FFmpeg Muxer
 Presets          SPDX Tracking     H.264/AAC MP4
```

---

## 2. The 5 Production Stages

### Stage 1: Research Engine (`src/research/`)
- **Input**: Topic brief string, target duration, offline mode flag.
- **Process**:
  1. Decomposes the brief into search queries across factuality, chronology, key figures, and technical mechanisms.
  2. Queries search endpoints or retrieves curated domain benchmark dossiers.
  3. Extracts claims, computes a normalized confidence score based on citation diversity, and maps each claim to recommended visual cues.
- **Output**: `ResearchDossier` object, written to `research_dossier.json` and `research_dossier.yaml`.

### Stage 2: Asset Engine (`src/assets/`)
- **Input**: `ResearchDossier` visual queries and claim cues.
- **Process**:
  1. Queries open media providers (Wikimedia Commons API, Pexels API, Openverse).
  2. Downloads media payloads using streaming HTTP, validates MIME magic bytes, and computes SHA-256 hashes.
  3. Freezes media into `assets/images/` before any rendering occurs.
  4. Generates procedural SVG vector cards for zero-network/offline environments.
  5. Compiles an immutable `AssetLedger` recording license categories, source URLs, and author attributions.
- **Output**: `AssetLedger` object, written to `asset_ledger.json` and `asset_ledger.yaml`.

### Stage 3: Script & Voiceover Engine (`src/scriptwriting/`)
- **Input**: `ResearchDossier` and `AssetLedger`.
- **Process**:
  1. Constructs a beatmapped script with hook, body points, and narrative conclusion.
  2. Aligns spoken text durations with visual scene timings.
  3. Synthesizes voiceover audio using ElevenLabs API, Windows SAPI TTS, or pure-Python synthetic harmonic WAV generator.
  4. Formats standard HyperFrames story documents (`BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`).
- **Output**: `narration.wav`, `SCRIPT.md`, `STORYBOARD.md`, and scene cue maps.

### Stage 4: HyperFrames Composition & Video Renderer (`src/hyperframes/`)
- **Input**: `STORYBOARD.md`, `DESIGN.md`, local frozen assets, and `narration.wav`.
- **Process**:
  1. Compiles responsive HTML5 (`index.html`), CSS styling (`styles.css`), and synchronous GSAP master timeline code (`main.js`).
  2. Runs static linter and validation checks (verifying local file paths, no remote network URLs, finite loops, and track bounds).
  3. Executes headless frame capture (via Chromium/Puppeteer or local canvas snapshotting) and feeds frames into FFmpeg.
  4. Encodes and muxes audio/video into a standard H.264 / AAC `.mp4` file.
- **Output**: Validated composition workspace and `renders/final.mp4`.

### Stage 5: Orchestration & CLI (`src/orchestrator/`)
- **Input**: CLI arguments, configuration files, and environment variables.
- **Process**:
  1. Initializes output directory workspace and logging telemetry.
  2. Sequences Stages 1 through 4 with strict state isolation and error boundaries.
  3. Emits `pipeline_summary.json` and `pipeline_summary.yaml` capturing runtime benchmarks, asset counts, and stage status.
- **Output**: Complete project workspace and terminal summary output.

---

## 3. Directory Layout

```
src/
├── assets/             # Asset discovery, freezing, rights ledger, and procedural SVGs
├── config.py           # Global pipeline settings, paths, and environment defaults
├── hyperframes/        # HTML/CSS/GSAP composition generator, linter, and video renderer
├── models/             # Pydantic/dataclass schema contracts for dossiers, ledgers, and scripts
├── orchestrator/       # Pipeline lifecycle manager, CLI interface, and run summary generator
├── research/           # Search query expansion, claim extraction, and confidence scoring
├── scriptwriting/      # Script generation, beat timing alignment, and TTS synthesis
└── utils/              # FFmpeg wrappers, audio utilities, and file helpers
```
