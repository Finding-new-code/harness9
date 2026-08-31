# Project: Harness 9 Automated Video Generation POC Pipeline

## Architecture
Harness 9 transforms creator topic briefs into broadcast-ready, rendered MP4 videos through a deterministic 5-stage pipeline:

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
[Stage 3: Script & Voiceover] ─────► SCRIPT.md, STORYBOARD.md + assets/audio/narration.wav
     │
     ▼
[Stage 4: HyperFrames & Render] ───► index.html, styles.css, main.js ──► renders/final.mp4
     │
     ▼
[Stage 5: Orchestrator & CLI] ─────► pipeline_summary.json / .yaml
```

### Core Design Principles:
1. **Zero External Breakage / Full Offline Capability**: Built-in deterministic fallbacks for research (curated presets + procedural topic synthesis), assets (procedural high-fidelity SVG graphics), and audio (Windows SAPI / harmonic wav synthesizer) guarantee 100% reliable execution in all environments without API keys or network access.
2. **Provenance & Rights Traceability**: Strict adherence to schema validation for Research Dossiers (claims, citations, confidence scores) and Asset Ledgers (license type, source URL, author attribution, SHA256 checksums).
3. **HyperFrames Compliance**: Synchronous GSAP timeline creation, `window.__timelines["root"] = gsap.timeline({ paused: true })`, finite repeat math (`Math.ceil(...) - 1`), decoupled audio/video elements, strict local asset references (`assets/...`), and caption exit guarantees.
4. **Broadcast Encoding**: Headless frame capture and FFmpeg audio/video muxing yielding valid, standard H.264/AAC playable `.mp4` video files.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Research & Fact Extraction | Multi-intent query expansion, claim extraction, confidence scoring, and structured dossier generation | M1 | R1 |
| F2 | Offline Research Fallback | Curated benchmark dossier presets and procedural deterministic synthesis for offline execution | M1 | R1 |
| F3 | Asset Discovery & Licensing | Wikimedia Commons, Pexels, and NASA open media search with license provenance extraction | M2 | R2 |
| F4 | Asset Freezing & Ledger | Streaming media download, magic byte sniffing, SHA256 hashing, local freezing, and asset ledger generation | M2 | R2 |
| F5 | Procedural Vector Asset Generator | Dynamic topic-tailored 1920x1080 SVG graphics and typographic card generator for zero-network environments | M2 | R2 |
| F6 | Structured Script & Storyboard | Scene beatmapping, timestamped voiceover beats, visual cue directives, BRIEF.md, DESIGN.md, SCRIPT.md, STORYBOARD.md | M3 | R3 |
| F7 | Voiceover & Speech Synthesis | ElevenLabs API integration + deterministic Windows SAPI / Pure Python TTS fallback producing synchronized audio | M3 | R3 |
| F8 | HyperFrames Composition Generator | HTML5/CSS/GSAP composition generator, window.__timelines binding, 16:9 & 9:16 templates, finite animation math | M4 | R4 |
| F9 | Composition Validator & Linter | Static linting, track collision checks, missing local asset verification, contrast/layout checks | M4 | R4 |
| F10 | Video Rendering & FFmpeg Muxing | Headless frame-by-frame capture and FFmpeg audio/video muxing into valid playable .mp4 | M4 | R4 |
| F11 | Unified CLI Runner & Orchestrator | Single command-line interface executing stages end-to-end, structured output structuring, summary reporting | M5 | R5 |
| F12 | Automated Verification Suite | Comprehensive verification script asserting generation of all stage artifacts and non-empty valid MP4 | M_FINAL | AC |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | `research_engine` | R1 Research & Fact Synthesis (F1, F2), dossier schemas, web search & offline fallback | none | **DONE** |
| M2 | `asset_pipeline` | R2 Asset Discovery, Provenance Ledger, Asset Freezing & SVG Generator (F3, F4, F5) | M1 | **DONE** |
| M3 | `script_voiceover` | R3 Script, Storyboard, Design Gate & TTS Voiceover Engine (F6, F7) | M1, M2 | **DONE** |
| M4 | `hyperframes_renderer` | R4 HyperFrames Generator, Validator & FFmpeg MP4 Video Renderer (F8, F9, F10) | M2, M3 | **DONE** |
| M5 | `orchestrator_cli` | R5 Unified Pipeline Orchestrator, CLI Runner & Summary Reporting (F11) | M1, M2, M3, M4 | **DONE** |
| M_FINAL | `e2e_verification_hardening` | Verification Suite (F12): 100% Tier 1-4 test pass, adversarial Tier 5 hardening & forensic audit | M1, M2, M3, M4, M5 | **DONE** |

---

## Interface Contracts

### 1. Topic Input ➔ M1 Research Engine
- **Input**: Topic string (`str`), optional `--offline` flag, optional target duration (`int`).
- **Output**: `ResearchDossier` object / `research_dossier.json` & `research_dossier.yaml`.
- **Key Fields**: `topic`, `summary` (headline, executive_summary, key_takeaways), `claims` (list of `{ claim_id, claim_text, category, confidence_score, primary_source, visual_cue_suggestion }`), `talking_points` (list of `{ beat_index, title, narrative_hook, supported_claim_ids, estimated_duration_sec }`), `statistics`, `suggested_visual_queries`.

### 2. M1 Research Engine ➔ M2 Asset Pipeline
- **Input**: `ResearchDossier` (or `suggested_visual_queries` + `claims`), target output directory, offline mode flag.
- **Output**: `AssetProvenanceLedger` object / `asset_ledger.json` & `asset_ledger.yaml` + local media files in `assets/images/*`.
- **Key Fields**: `project_id`, `total_assets`, `license_summary`, `assets` (list of `{ asset_id, claim_id_refs, scene_target, media_type, local_path, absolute_path, file_size_bytes, file_sha256, dimensions, source_provider, source_url, creator, license, verification_status }`).

### 3. M1 Dossier + M2 Asset Ledger ➔ M3 Script & Voiceover Engine
- **Input**: `ResearchDossier`, `AssetProvenanceLedger`, output directory, voice preferences, TTS mode.
- **Output**: `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md` + audio file `assets/audio/narration.wav` + `transcript.json` (timestamped beats).
- **Key Fields in Storyboard**: List of scenes with `{ scene_id, title, start_time, duration, narration_text, visual_asset_path, hero_frame_description, entrance_animation, transition_out }`.

### 4. M2 Assets + M3 Script/Audio ➔ M4 HyperFrames Generator & Video Renderer
- **Input**: Storyboard, design tokens, local frozen assets (`assets/images/*`), audio narration (`assets/audio/narration.wav`), output directory, resolution (1920x1080 or 1080x1920), fps (30).
- **Output**: HyperFrames composition files (`index.html`, `styles.css`, `main.js`), validation report, and rendered playable video `renders/final.mp4`.
- **Validation Contract**: `validate_composition()` checks syntax, absence of external URLs (`http://`), presence of all local `assets/*`, `window.__timelines["root"]` registration, and finite animation repeats.
- **Render Contract**: Headless frame capture + FFmpeg video/audio muxing -> produces non-empty `.mp4` matching target duration within ±0.2s with valid H.264 video and AAC audio streams.

### 5. Orchestrator Runner ➔ End-to-End Execution
- **Input**: CLI arguments (`--topic`, `--output-dir`, `--offline`, `--duration`, `--format`, `--voice`, `--test-mode`).
- **Output**: Complete project directory populated with all stage artifacts + `pipeline_summary.json` & `pipeline_summary.yaml` reporting status, execution time per stage, asset count, and render path.

---

## Code Layout
```
g:\Finding-new-code\harness9\
├── src\
│   ├── __init__.py
│   ├── config.py                 # Global configurations, paths, environment bindings
│   ├── models\                   # Pydantic / dataclass schemas
│   │   ├── __init__.py
│   │   ├── dossier.py            # ResearchDossier schema
│   │   ├── ledger.py             # AssetProvenanceLedger schema
│   │   ├── script.py             # Script, Storyboard, Beatmap schemas
│   │   └── summary.py            # PipelineSummary schema
│   ├── research\                 # M1: Research & Fact Synthesis
│   │   ├── __init__.py
│   │   ├── engine.py             # Main research engine orchestrator
│   │   ├── providers.py          # Web search adapters (Tavily/DuckDuckGo/Exa/urllib)
│   │   ├── scoring.py            # Fact extraction & confidence scoring
│   │   └── presets\              # Curated offline benchmark dossiers (YAML)
│   │       ├── transistor_history.yaml
│   │       ├── how_gpus_work.yaml
│   │       └── apollo_computer.yaml
│   ├── assets\                   # M2: Asset Discovery & Rights Ledger
│   │   ├── __init__.py
│   │   ├── discovery.py          # Media discovery (Wikimedia, Pexels, NASA)
│   │   ├── freezer.py            # Streaming downloader, magic byte validator, SHA256
│   │   ├── ledger.py             # Provenance ledger manager
│   │   └── procedural.py         # Dynamic SVG / typographic card generator
│   ├── scriptwriting\            # M3: Script & Voiceover Engine
│   │   ├── __init__.py
│   │   ├── generator.py          # Script, storyboard, and design generator
│   │   ├── tts.py                # TTS engine (Windows SAPI / Pure Python / ElevenLabs)
│   │   └── aligner.py            # Audio beat & timestamp alignment
│   ├── hyperframes\              # M4: HyperFrames Composition & Renderer
│   │   ├── __init__.py
│   │   ├── generator.py          # HTML/CSS/GSAP composition compiler
│   │   ├── validator.py          # Static linter & asset integrity validator
│   │   └── renderer.py           # Headless browser capture & FFmpeg MP4 encoder
│   ├── orchestrator\             # M5: Unified Orchestrator & CLI
│   │   ├── __init__.py
│   │   ├── pipeline.py           # Pipeline runner executing stages 1-5
│   │   └── cli.py                # CLI interface entrypoint (typer/argparse)
│   └── utils\                    # Shared utilities
│       ├── __init__.py
│       ├── ffmpeg.py             # FFmpeg/ffprobe wrappers and diagnostics
│       └── filesystem.py         # Safe path resolution and atomic file writes
├── tests\                        # Comprehensive E2E and Unit Test Suite
│   ├── test_e2e_pipeline.py      # End-to-end full pipeline verification
│   ├── test_research.py          # M1 research engine tests
│   ├── test_assets.py            # M2 asset discovery, freezing & ledger tests
│   ├── test_scriptwriting.py     # M3 script, storyboard & TTS tests
│   ├── test_hyperframes.py       # M4 composition & validator tests
│   ├── test_renderer.py          # M4 MP4 rendering & FFmpeg tests
│   └── test_cli.py               # M5 CLI runner tests
├── verify_pipeline.py            # Acceptance criteria automated verification runner
├── run_harness9.py               # Root CLI entrypoint
├── PROJECT.md                    # This project plan and architecture specification
└── TEST_INFRA.md                 # E2E test infrastructure specification
```
