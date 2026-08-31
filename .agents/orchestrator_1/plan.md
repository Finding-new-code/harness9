# Master Plan: Harness 9 Automated Video Generation POC Pipeline

## Objective
Deliver a production-grade, automated, well-tested Proof of Concept (POC) pipeline for Harness 9 taking creator topics/briefs to rendered MP4 video with full research, licensing provenance, synchronized TTS voiceover, and HyperFrames composition.

## Pipeline Requirements
- **R1: Research & Fact Synthesis Engine**: Web querying, fact/stat extraction, claim confidence, structured research dossier JSON/YAML.
- **R2: Asset Discovery, Rights Ledger & Local Freezing**: Wikimedia Commons/Pexels/open web media search, license metadata recording, local asset freezing.
- **R3: Script & Voiceover Generation**: Structured script with timestamped beats, voiceover transcript, visual cues; ElevenLabs API + deterministic synthetic TTS fallback (e.g. edge-tts / pyttsx3 / synthetic wav generator).
- **R4: HyperFrames Composition & Video Rendering**: HTML/CSS/GSAP HyperFrames project (BRIEF.md, STORYBOARD.md, SCRIPT.md, composition files, GSAP timeline), validation suite, automated browser/headless video rendering to playable MP4 (e.g., Playwright/Puppeteer/remotion/ffmpeg screen capture or canvas frames to MP4).
- **R5: End-to-End Orchestrator & CLI Runner**: Unified runner command, stage execution, output directory structuring, run summary report.

## Orchestration Phases
1. **Phase 0: Survey & Discovery**
   - Explorer 1 (Spec Miner): Mine HyperFrames conventions, schemas, templates, validation rules in `optional-skills/creative/hyperframes/`.
   - Explorer 2 (System Architecture): Survey repository structure, environment capabilities, Python/Node tools, ffmpeg availability, web search APIs, TTS options.
   - Explorer 3 (Pipeline & Asset Pipeline): Survey open web asset APIs (Wikimedia Commons, Pexels), license schemas, research synthesis formats, and fallback strategies.
2. **Phase 1: Architecture & Decomposition**
   - Synthesize survey findings into `PROJECT.md` and `TEST_INFRA.md`.
   - Define exact interface contracts, data schemas (Dossier, Asset Ledger, Script/Beatmap, HyperFrames spec), and file layout.
3. **Phase 2: Dual Track Execution**
   - **Track A (E2E Testing)**: Test infra, test runners, Tier 1-4 test suites.
   - **Track B (Implementation)**:
     - M1: Research & Fact Synthesis Engine (R1)
     - M2: Asset Discovery, Rights Ledger & Local Freezing (R2)
     - M3: Script & Voiceover Engine with deterministic fallback (R3)
     - M4: HyperFrames Generator, Validator & MP4 Renderer (R4)
     - M5: Unified CLI Runner, Orchestrator & Reporting (R5)
4. **Phase 3: Integration & E2E Validation**
   - Phase 1: Pass 100% of E2E test suite (Tiers 1-4).
   - Phase 2: Adversarial coverage hardening (Tier 5) with Challengers and Forensic Auditor verification.
5. **Phase 4: Synthesis & Human Reporting**
   - Compile final verification evidence and report to parent/user.
