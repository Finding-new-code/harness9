# Harness 9 Codebase Architecture & Survey Analysis

**Author**: `explorer_survey_1`  
**Date**: 2026-08-31  
**Scope**: Full Codebase Survey & Gap Analysis for Harness 9 Upgrade (R1–R6)

---

## 1. Executive Summary

Harness 9 is an AI-native content production operating system integrated into the Hermes Agent ecosystem. It transforms creator topic briefs into broadcast-ready rendered MP4 videos through typed production stages, deterministic gates, and an asset rights ledger.

Currently, the repository contains a fully working 5-stage POC pipeline in `src/` backed by a 6-checkpoint verification harness (`verify_pipeline.py`) and a comprehensive multi-tier test suite in `tests/`. All existing unit, integration, and E2E verification suites pass 100% in hermetic offline environments.

To fulfill the Head of Engineering's architecture and upgrade plan specified in `ORIGINAL_REQUEST.md`, Harness 9 must evolve from this linear 5-stage POC into a decoupled, 17-state production lifecycle architecture featuring:
1. **R1**: 17-state deterministic lifecycle state machine, comprehensive Pydantic production schemas (incorporating `CreatorProfile`, `ContentBrief`, `ResearchPlan`, `ResearchDossier`, `SourceRecord`, `ClaimRecord`, `EditorialAngle`, `ContentOutline`, `Script`, `ScriptBeat`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`), and isolated `adapters/hermes/` compatibility layer with `docs/HERMES_COMPATIBILITY.md`.
2. **R2**: Dedicated editorial intelligence engine (`src/editorial/` or `packages/editorial/`) featuring multi-angle generation, 9-dimension scorecard evaluation, hook generation, and narrative planning.
3. **R3**: Formal HyperFrames adapter (`adapters/hyperframes/`) and H9 reusable component registry with 7 parameterized blocks.
4. **R4**: Multi-provider `VoiceDirector`, automated `VoiceQA` (dead air, clipping, volume consistency, speech-beat alignment), and multi-tiered asset deduplication (SHA-256 + perceptual hashing).
5. **R5**: Creator DNA data model, Creator Economics cost/revenue ledger, and 4-layer evaluation framework (`ContentBench`).
6. **R6**: Principle-of-least-privilege capability tokens (`child_permission = parent ∩ role ∩ workflow`) and the complete 14-document engineering specification suite + ADR-001 through ADR-005.

---

## 2. Codebase Layout & File Tree Mapping

The repository root `g:\Finding-new-code\harness9` houses both the parent `hermes-agent` platform and the dedicated Harness 9 video production subsystem.

```
g:\Finding-new-code\harness9\
├── src\                               # Core Harness 9 production source code
│   ├── config.py                      # Global configuration, environment vars, defaults
│   ├── models\                        # Data schemas & serialization models
│   │   ├── dossier.py                 # ResearchDossier, Claim, Source, TalkingPoint, Statistic
│   │   ├── ledger.py                  # AssetProvenanceLedger, MediaAsset, LicenseInfo, Dimensions
│   │   ├── script.py                  # Script, Storyboard, Scene, Beat
│   │   └── summary.py                 # PipelineSummary, StageResult
│   ├── research\                      # Stage 1: Research & Fact Synthesis (M1)
│   │   ├── engine.py                  # ResearchEngine orchestrator & preset matcher
│   │   ├── providers.py               # Search provider dispatcher (Tavily/Exa/Mock)
│   │   ├── scoring.py                 # Fact extraction & confidence scoring formula
│   │   └── presets\                   # Curated offline benchmark YAML dossiers
│   │       ├── apollo_computer.yaml
│   │       ├── how_gpus_work.yaml
│   │       ├── quantum_computing.yaml
│   │       └── transistor_history.yaml
│   ├── assets\                        # Stage 2: Asset Discovery, Freezing & Rights Ledger (M2)
│   │   ├── discovery.py               # Media search (Wikimedia, Pexels, NASA, Mock)
│   │   ├── freezer.py                 # Media downloader, magic byte validator, SHA256 hashing
│   │   ├── ledger.py                  # Provenance ledger manager & validation rules
│   │   ├── pipeline.py                # AssetPipeline orchestrator
│   │   └── procedural.py              # Procedural SVG & typographic card generator
│   ├── scriptwriting\                 # Stage 3: Script, Storyboard, Design Gate & TTS (M3)
│   │   ├── generator.py               # BRIEF.md, DESIGN.md, SCRIPT.md, STORYBOARD.md generator
│   │   ├── tts.py                     # TTSEngine (ElevenLabs / SAPI / Harmonic WAV synth)
│   │   ├── aligner.py                 # Audio transcript & word-level beat alignment
│   │   └── pipeline.py                # ScriptwritingPipeline orchestrator
│   ├── hyperframes\                   # Stage 4: HyperFrames HTML/CSS/GSAP & Video Renderer (M4)
│   │   ├── generator.py               # HTML/CSS/GSAP composition compiler
│   │   ├── validator.py               # Static linter, asset auditor, repeat checker
│   │   └── renderer.py                # Headless frame capture & FFmpeg video/audio muxing
│   ├── orchestrator\                  # Stage 5: Master Pipeline & CLI Runner (M5)
│   │   ├── pipeline.py                # End-to-end Pipeline orchestrator (Stages 1-5)
│   │   └── cli.py                     # CLI entrypoint parser
│   └── utils\                         # Shared helpers
│       ├── ffmpeg.py                  # FFmpeg/ffprobe diagnostics & container fallback
│       └── filesystem.py              # Atomic file writes & path resolution
├── docs\harness9\                     # Existing POC documentation
│   ├── README.md                      # Architecture & overview
│   ├── CLI_REFERENCE.md               # CLI flags and programmatic usage
│   ├── DEVELOPMENT_AND_TESTING.md     # Testing matrix and offline fallback guide
│   ├── HYPERFRAMES_GUIDE.md           # HyperFrames structure and GSAP rules
│   └── PROVENANCE_AND_RIGHTS.md       # License classification and SHA256 freezing
├── tests\                             # Harness 9 Unit, Integration & E2E Test Suite
│   ├── test_research.py               # 20 tests (Tier 1 & 2)
│   ├── test_assets.py                 # 28 tests (Tier 1 & 2)
│   ├── test_scriptwriting.py          # 20 tests (Tier 1 & 2)
│   ├── test_hyperframes.py            # 20 tests (Tier 1 & 2)
│   ├── test_renderer.py               # 20 tests (Tier 1 & 2)
│   ├── test_cli.py                    # 20 tests (Tier 1 & 2)
│   ├── test_e2e_pipeline.py           # 20 tests (Tier 3 Pairwise + Tier 4 Scenarios S1-S10)
│   ├── test_adversarial_assets.py     # Adversarial M2 stress tests
│   ├── test_research_adversarial.py   # Adversarial M1 stress tests
│   ├── test_m1_challenger2_stress.py  # M1 stress testing
│   └── test_m2_challenger2_stress.py  # M2 stress testing
├── HARNESS9.md                        # Project quickstart & pipeline overview
├── PROJECT.md                         # Architecture specification & feature inventory
├── TEST_INFRA.md                      # Test infrastructure specification
├── TEST_READY.md                      # Test readiness checklist
├── run_harness9.py                    # Root CLI entrypoint script
└── verify_pipeline.py                 # 6-checkpoint automated acceptance verification harness
```

---

## 3. Subsystem Deep-Dive & Current Capabilities

### 3.1 Stage 1: Research & Fact Synthesis (`src/research/`)
- **Key Modules**:
  - `src/research/engine.py`: Manages the query expansion, preset matching, online dispatching, and fallback procedural generation.
  - `src/research/providers.py`: Multi-provider dispatcher supporting Tavily, Exa, DuckDuckGo/urllib, and `MockSearchProvider`.
  - `src/research/scoring.py`: Calculates factual confidence score:
    $$\text{Score} = (0.40 \times \text{Authority}) + (0.35 \times \text{Corroboration}) + (0.25 \times \text{Clarity}) - \text{ConflictPenalty}$$
  - `src/research/presets/`: 4 benchmark YAML dossiers (`transistor_history.yaml`, `how_gpus_work.yaml`, `apollo_computer.yaml`, `quantum_computing.yaml`).
- **Data Output**: `research_dossier.json` and `research_dossier.yaml`.

### 3.2 Stage 2: Asset Discovery, Freezing & Rights Ledger (`src/assets/`)
- **Key Modules**:
  - `src/assets/discovery.py`: Searches Wikimedia Commons, Pexels, and NASA open media APIs.
  - `src/assets/freezer.py`: Downloads streams, validates magic bytes (PNG, JPEG, SVG, WebP, MP4), verifies SHA-256 checksums, and freezes files to local disk under `assets/images/`.
  - `src/assets/procedural.py`: High-fidelity procedural SVG vector graphic and typographic card generator for 100% offline environments.
  - `src/assets/ledger.py`: Manages `AssetProvenanceLedger` with SPDX license tags, source URLs, author attribution, and checksums.
- **Data Output**: `asset_ledger.json`, `asset_ledger.yaml`, and `assets/images/*`.

### 3.3 Stage 3: Script, Storyboard, Design Gate & TTS (`src/scriptwriting/`)
- **Key Modules**:
  - `src/scriptwriting/generator.py`: Generates `BRIEF.md`, `DESIGN.md` (with brand, color palette, typography, motion rules), `SCRIPT.md`, `STORYBOARD.md`, and `script.json`/`script.yaml`.
  - `src/scriptwriting/tts.py`: Multi-backend voice synthesis supporting ElevenLabs API, Windows SAPI (`win32com.client`), and a pure Python `HarmonicWAVSynthesizer` generating valid standard WAV audio.
  - `src/scriptwriting/aligner.py`: Aligns spoken audio with scene beats, generating timestamped word groups in `assets/transcript.json`.
- **Data Output**: `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, `assets/audio/narration.wav`, `assets/transcript.json`.

### 3.4 Stage 4: HyperFrames Composition & Video Renderer (`src/hyperframes/`)
- **Key Modules**:
  - `src/hyperframes/generator.py`: Generates HTML5 (`index.html`), CSS3 (`styles.css`), and synchronous GSAP master timeline (`main.js` with `window.__timelines["root"] = gsap.timeline({ paused: true })`).
  - `src/hyperframes/validator.py`: Static linter enforcing:
    1. Root composition attribute `data-composition-id="root"`.
    2. Zero external remote media URLs (strict hermetic asset references).
    3. Absence of broken local asset paths.
    4. Finite repeat math (`Math.ceil(...) - 1`, strictly no `repeat: -1`).
  - `src/hyperframes/renderer.py`: Headless Chromium/Playwright capture or procedural frame sequence creation muxed via FFmpeg into a broadcast-ready H.264/AAC `renders/final.mp4`.
- **Data Output**: `index.html`, `styles.css`, `main.js`, `renders/final.mp4`.

### 3.5 Stage 5: Unified Pipeline Orchestrator & CLI (`src/orchestrator/`)
- **Key Modules**:
  - `src/orchestrator/pipeline.py`: Master `Pipeline` class executing Stages 1–5 sequentially, measuring stage execution time, collecting metrics, and emitting `pipeline_summary.json` and `pipeline_summary.yaml`.
  - `src/orchestrator/cli.py`: Typer/argparse CLI entrypoint with `--topic`, `--output-dir`, `--offline`, `--format`, `--duration`, `--voice`.
  - `verify_pipeline.py`: Acceptance verification runner executing 6 automated checkpoints.

---

## 4. Verification Harness & Test Suite Assessment

### 4.1 Automated Checkpoint Results (`verify_pipeline.py --test-mode`)
The 6 acceptance checkpoints verify end-to-end correctness:
1. **Research Dossier**: Verified $\ge 3$ claims with citations and confidence scores. [PASS]
2. **Asset Ledger**: Verified frozen media assets with SPDX licenses, URLs, and SHA-256 hashes. [PASS]
3. **Audio Narration**: Verified valid WAV audio track with duration aligned to storyboard. [PASS]
4. **HyperFrames Project Files**: Verified presence of `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, `index.html`. [PASS]
5. **HyperFrames Composition**: Verified zero remote URLs, local asset integrity, GSAP paused timeline, and finite repeat math. [PASS]
6. **Rendered Video**: Verified valid MP4 container with video and audio streams. [PASS]

### 4.2 Pytest / Unittest Execution Summary
- `tests/test_research.py`: 20/20 PASSED (1.31s)
- `tests/test_assets.py`: 28/28 PASSED (2.05s)
- `tests/test_scriptwriting.py`: 20/20 PASSED (10.14s)
- `tests/test_hyperframes.py`: 20/20 PASSED (9.01s)
- `tests/test_cli.py`: 20/20 PASSED (0.75s)
- `tests/test_renderer.py`: 20/20 PASSED (43.18s)
- `tests/test_e2e_pipeline.py`: 20/20 PASSED (163.16s)
- Total tests executed across surveyed modules: **148+ passing tests** (100% pass rate).

---

## 5. Architectural Gap Analysis: Current State vs. Target Requirements (R1–R6)

| Requirement | Target Specification (from ORIGINAL_REQUEST.md) | Current State in Codebase | Gap / Action Required |
|---|---|---|---|
| **R1: State Machine** | 17-state deterministic lifecycle (`CREATED` through `COMPLETED`), rejecting invalid transitions | Linear sequential execution in `src/orchestrator/pipeline.py` (5 stages) | Implement explicit 17-state StateMachine with transition graph, state history, and transition validation |
| **R1: Production Schemas** | 17 Pydantic schemas: `CreatorProfile`, `ContentBrief`, `ResearchPlan`, `ResearchDossier`, `SourceRecord`, `ClaimRecord`, `EditorialAngle`, `ContentOutline`, `Script`, `ScriptBeat`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate` | 4 dataclass modules in `src/models/` (`dossier.py`, `ledger.py`, `script.py`, `summary.py`) | Expand and formalize all 17 Pydantic schemas with strict validation, default values, and serialization |
| **R1: Hermes Adapter** | Isolated `adapters/hermes/` compatibility layer with `docs/HERMES_COMPATIBILITY.md` | Direct references to Hermes tools without dedicated isolation package | Create `adapters/hermes/` package and documentation `docs/HERMES_COMPATIBILITY.md` |
| **R2: Editorial Intelligence** | Multi-angle generation, 9-dimension scoring matrix, hook generation, and narrative planning before scriptwriting | Script generator directly expands talking points into scenes | Create `src/editorial/` (or `packages/editorial/`) implementing candidate angle generation and 9-dimension scoring |
| **R3: HyperFrames Adapter & Registry** | Formal `adapters/hyperframes/` interface + registry of 7 parameterized blocks (reference collage, split-screen, quote highlight, timeline reveal, statistic reveal, comparison panel, creator bottom collage) | Monolithic template generator in `src/hyperframes/generator.py` | Implement `adapters/hyperframes/` and modular block registry for the 7 standard components |
| **R4: Voice Director & Voice QA** | Multi-backend `VoiceDirector` + automated `VoiceQA` (dead air, gap duration, clipping, volume consistency, speech-beat alignment) | Basic `TTSEngine` with ElevenLabs / SAPI / Harmonic synthesizer fallbacks | Implement `VoiceDirector` and quantitative audio analysis `VoiceQA` metrics in summary reports |
| **R4: Asset Deduplication** | Multi-tiered deduplication using SHA-256 content hashing and perceptual hashing | SHA-256 hashing during download; no perceptual hashing | Add perceptual hashing (dHash/pHash) and deduplication ledger to asset engine |
| **R5: Creator DNA & Economics** | Brand Constitution, Preferences, Skills, Examples, Performance Memory, Negative Memory + itemized cost ledger | Basic `BrandGuidelines` (colors/typography/motion) and runtime timers | Implement full Creator DNA model and granular itemized cost/revenue ledger (LLM, research, TTS, render, storage) |
| **R5: Quality OS (ContentBench)** | 4-layer evaluation framework across Research, Script, Video, and Cost | Basic 6-checkpoint acceptance verification in `verify_pipeline.py` | Implement `ContentBench` evaluation suite with benchmark test cases and scoring rubrics |
| **R6: Security Capability Tokens** | Principle-of-least-privilege capability token engine (`child = parent ∩ role ∩ workflow`) | Process-level permission checks | Implement capability token engine and permission boundary test suite |
| **R6: Documentation Suite & ADRs** | 14 engineering specifications + ADR-001 through ADR-005 in `docs/` | `docs/harness9/` (5 files) + root markdown files | Author complete 14-spec documentation suite and ADR-001 through ADR-005 |

---

## 6. Environment, Dependencies & Toolchain

1. **Python Interpreter & Virtual Environment**:
   - Python 3.11 / 3.12 / 3.13 supported (capped `<3.14` in `pyproject.toml`).
   - Active virtual environment: `g:\Finding-new-code\harness9\.venv\Scripts\python.exe`.
2. **Key Dependencies**:
   - Core libraries: `pydantic` (2.13.4), `pyyaml` (6.0.3), `requests` (2.33.0), `jinja2` (3.1.6), `Pillow` (12.3.0).
   - Video & Audio Processing: `wave`, `struct`, `subprocess`, `ffmpeg` / `ffprobe` (with robust built-in procedural and WAV synthesis fallbacks when system binaries are absent).
3. **Execution Commands**:
   - `python run_harness9.py --topic "<Topic>" --format 16:9 --duration 30`
   - `python verify_pipeline.py --test-mode`
   - `python -m unittest tests/test_*.py`

---

## 7. Recommended Implementation Roadmap

1. **Phase 1: Schemas, State Machine & Hermes Adapter (R1)**:
   - Implement `src/models/` full Pydantic suite (all 17 models).
   - Implement 17-state `src/pipeline/state_machine.py`.
   - Implement `adapters/hermes/` and `docs/HERMES_COMPATIBILITY.md`.
2. **Phase 2: Editorial Intelligence & Multi-Angle Engine (R2)**:
   - Implement `src/editorial/` with angle generator, 9-dimension scoring matrix, and hook planner.
3. **Phase 3: HyperFrames Adapter & Component Registry (R3)**:
   - Implement `adapters/hyperframes/` and 7 reusable parameterized component blocks.
4. **Phase 4: Voice Director, VoiceQA & Deduplication (R4)**:
   - Implement `VoiceDirector`, `VoiceQA` audio analyzer, and perceptual hashing deduplication.
5. **Phase 5: Creator DNA, Economics Ledger & ContentBench (R5)**:
   - Implement Creator DNA, itemized cost ledger, and `ContentBench` evaluation suite.
6. **Phase 6: Capability Tokens & Engineering Documentation Suite (R6)**:
   - Implement Capability Token Engine with permission intersection logic.
   - Deliver all 14 markdown specifications and ADR-001 through ADR-005.
