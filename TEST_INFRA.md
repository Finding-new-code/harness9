# E2E Test Infra: Harness 9 Automated Video Generation Pipeline

## Test Philosophy
- **Requirement-Driven**: All test cases are derived strictly from `ORIGINAL_REQUEST.md` (R1-R5 and Acceptance Criteria).
- **Opaque-Box & Deterministic**: Tests exercise the pipeline via public entrypoints (`verify_pipeline.py`, CLI commands, and public API interfaces) with zero dependency on internal private implementations.
- **Hermetic & Flake-Free**: Provides deterministic mock/offline fixtures alongside live adapters so test execution never flakes on network partitions or missing API keys.
- **Methodology**: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.

---

## Feature Inventory & Test Mapping
| # | Feature | Requirement Source | Tier 1 (Coverage) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Real-World) |
|---|---------|-------------------|:-----------------:|:-----------------:|:-----------------:|:-------------------:|
| F1 | Research & Fact Extraction | R1 §13 | 5 | 5 | ✓ | ✓ |
| F2 | Offline Research Fallback | R1 §13 | 5 | 5 | ✓ | ✓ |
| F3 | Asset Discovery & Licensing | R2 §16 | 5 | 5 | ✓ | ✓ |
| F4 | Asset Freezing & Ledger | R2 §16 | 5 | 5 | ✓ | ✓ |
| F5 | Procedural Vector Asset Gen | R2 §16 | 5 | 5 | ✓ | ✓ |
| F6 | Structured Script & Storyboard | R3 §19 | 5 | 5 | ✓ | ✓ |
| F7 | Voiceover & Speech Synthesis | R3 §19 | 5 | 5 | ✓ | ✓ |
| F8 | HyperFrames Composition Gen | R4 §22 | 5 | 5 | ✓ | ✓ |
| F9 | Composition Validator & Lint | R4 §22 | 5 | 5 | ✓ | ✓ |
| F10 | Video Rendering & FFmpeg | R4 §22 | 5 | 5 | ✓ | ✓ |
| F11 | Unified CLI & Orchestrator | R5 §25 | 5 | 5 | ✓ | ✓ |
| F12 | Automated Verification Suite | AC §41 | 5 | 5 | ✓ | ✓ |

---

## Test Architecture

### 1. Test Runner & Invocation
- **Full Test Suite Execution**:
  ```bash
  python -m unittest discover -s tests -p "test_*.py" -v
  ```
- **Automated Verification Script (Acceptance Gate)**:
  ```bash
  python verify_pipeline.py --test-mode --output-dir output/test_verification_run
  ```
  Expected: Exits with status `0` and generates full verification report.

### 2. Output Format & Assertions
All test runners output structured JUnit/TAP/Text test reports and assert:
1. Research Dossier (`research_dossier.json`/`.yaml`) contains $\ge 3$ verifiable claims with valid sources, confidence scores $\in [0.0, 1.0]$, and summary.
2. Asset Ledger (`asset_ledger.json`/`.yaml`) records all local assets, license types, source URLs, author attributions, SHA256 checksums, and verification statuses.
3. Audio Narration (`assets/audio/narration.wav` or `.mp3`) exists, is non-empty, and has duration aligned with storyboard beatmap within $\pm 0.2\text{s}$.
4. HyperFrames project contains `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, `index.html`, and assets directory.
5. HyperFrames composition validates with zero broken paths and no external URLs (`http://`).
6. Video file (`renders/final.mp4`) exists, is non-empty, has valid H.264 video and AAC audio streams, and is playable.

---

## Real-World Application Scenarios (Tier 4)

| # | Scenario | Features Exercised | Topic / Premise | Complexity |
|---|----------|--------------------|-----------------|------------|
| S1 | The History of the Transistor | F1, F2, F3, F4, F6, F7, F8, F9, F10, F11 | Invention of point-contact transistor at Bell Labs in 1947 | Standard Benchmark |
| S2 | How GPUs Work: Parallel Computing | F1, F2, F3, F5, F6, F7, F8, F9, F10, F11 | CPU vs GPU architecture, matrix cores, parallel compute | High Data Density |
| S3 | The Apollo Guidance Computer | F1, F2, F4, F5, F6, F7, F8, F9, F10, F11 | 1969 Apollo 11 AGC, core rope memory, real-time OS | Historical Deep Dive |
| S4 | Vertical Short-Form Video (9:16) | F1, F6, F7, F8, F9, F10, F11 | 1080x1920 portrait format for TikTok / Reels with safe area captions | Aspect Ratio & Layout |
| S5 | Pure Offline Execution Mode | F2, F4, F5, F6, F7, F8, F9, F10, F11 | Full pipeline execution with network disabled / zero API keys | Resilience & Isolation |
| S6 | Dynamic Procedural Custom Topic | F1, F2, F5, F6, F7, F8, F9, F10, F11 | Arbitrary user brief (e.g. "Quantum Cryptography Explained") | Dynamic Synthesis |

---

## Coverage Thresholds
- **Tier 1 (Feature Coverage)**: $\ge 60$ unit tests ($5 \times 12$ features).
- **Tier 2 (Boundary & Corner Cases)**: $\ge 60$ edge case tests covering missing keys, empty inputs, network errors, malformed assets, and long durations.
- **Tier 3 (Cross-Feature Combinations)**: $\ge 12$ pairwise integration tests.
- **Tier 4 (Real-World Scenarios)**: $\ge 6$ application-level end-to-end runs.
- **Total Minimum Test Count**: $\ge 138$ tests across all tiers.
