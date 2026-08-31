# Dispatch for E2E Test Writer
Directory: g:\Finding-new-code\harness9\.agents\test_writer_e2e_0

## 2026-08-31T05:11:07Z
Build the comprehensive test suite and automated acceptance verification harness:
1. Implement `verify_pipeline.py` at project root:
   - Command-line runner supporting flags `--test-mode`, `--topic`, `--output-dir`, `--offline`, `--format`.
   - Executes the end-to-end pipeline in test/offline mode.
   - Validates and asserts all stage artifacts:
     a. `research_dossier.json` or `.yaml` (contains >= 3 verifiable claims with sources and confidence scores).
     b. `asset_ledger.json` or `.yaml` (contains asset records with license types, source URLs, author attribution, SHA-256, local frozen paths).
     c. `assets/audio/narration.wav` (exists, non-empty audio, duration matches beatmap).
     d. HyperFrames project files (`BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, `index.html`, `styles.css`, `main.js`).
     e. HyperFrames validation (zero broken local asset paths, no remote `http://` URLs in HTML/CSS).
     f. `renders/final.mp4` (valid, non-empty, playable MP4 with video and audio streams).
   - Exits with returncode 0 on success and prints a structured verification summary.
2. Implement comprehensive test files in `tests/`:
   - `tests/test_research.py` (Tier 1 & 2 tests for F1, F2: schema validation, confidence calculation, offline fallback, procedural synthesis).
   - `tests/test_assets.py` (Tier 1 & 2 tests for F3, F4, F5: media discovery, magic byte checks, rights ledger, procedural SVG generation).
   - `tests/test_scriptwriting.py` (Tier 1 & 2 tests for F6, F7: storyboard beatmap, duration sync, TTS synthesis fallback).
   - `tests/test_hyperframes.py` (Tier 1 & 2 tests for F8, F9: HTML composition generation, GSAP window.__timelines registration, finite repeat math, validation).
   - `tests/test_renderer.py` (Tier 1 & 2 tests for F10: frame capture, FFmpeg muxing, MP4 validity and duration).
   - `tests/test_cli.py` (Tier 1 & 2 tests for F11: CLI argument parsing, stage flags, error handling).
   - `tests/test_e2e_pipeline.py` (Tier 3 pairwise & Tier 4 real-world scenarios S1-S6).
3. Ensure all tests use Python's built-in `unittest` runner (`python -m unittest discover -s tests -p "test_*.py"`).
4. When complete, create `TEST_READY.md` at project root following the format in `TEST_INFRA.md`.
