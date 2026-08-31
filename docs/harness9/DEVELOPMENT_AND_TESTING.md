# Harness 9 — Development & Testing Guide

## 1. Development Environment

Harness 9 runs natively on Windows, macOS, and Linux with Python 3.10+ and Node.js.

### Dependencies
- **Python**: `httpx`, `pydantic`, `pyyaml`, `pytest`
- **System**: `ffmpeg` (for video/audio encoding)
- **Node.js**: Chromium / Puppeteer for headless browser frame extraction (optional; automated pure-canvas/snapshot fallbacks included).

---

## 2. Testing Hierarchy

Harness 9 uses a 5-tier test matrix:

```
Tier 1: Unit Tests (Isolated functions, schemas, hashing, math)
Tier 2: Component Tests (Research parser, TTS backends, SVG builder)
Tier 3: Property & Invariant Tests (GSAP timeline bounds, loop finiteness)
Tier 4: End-to-End Integration (Topic brief -> Full rendered MP4)
Tier 5: Adversarial Hardening (Corrupted assets, dead network, timeout stress)
```

---

## 3. Running the Test Suite

### Full Pytest Suite
Run all unit and integration tests across the codebase:
```bash
pytest tests/ -v
```

### Run Stage-Specific Tests
```bash
# Research engine tests
pytest tests/test_research.py -v

# Asset discovery & rights ledger tests
pytest tests/test_assets.py -v

# Scriptwriting & voiceover tests
pytest tests/test_scriptwriting.py -v

# HyperFrames generator & renderer tests
pytest tests/test_hyperframes.py -v

# Full E2E pipeline integration tests
pytest tests/test_e2e_pipeline.py -v
```

---

## 4. Acceptance Verification Harness

The `verify_pipeline.py` script is the automated acceptance validator. It evaluates the 6 fundamental production checkpoints:

```bash
python verify_pipeline.py --test-mode
```

### Checkpoints Evaluated:
1. **Checkpoint 1 (Research Dossier)**: Validates JSON/YAML structure, at least 3 verifiable claims with sources, category mappings, and confidence scores $\ge 0.70$.
2. **Checkpoint 2 (Asset Ledger & Rights)**: Validates local frozen assets, valid SPDX/CC licenses, SHA-256 hash matching, and attribution metadata.
3. **Checkpoint 3 (Audio Narration & Beat Alignment)**: Validates non-empty audio files (`.wav`/`.mp3`), header format validity, and duration alignment with scene beats ($\pm 2.0\text{s}$).
4. **Checkpoint 4 (HyperFrames Project Contract)**: Verifies presence and structure of `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, and `STORYBOARD.md`.
5. **Checkpoint 5 (Composition Linter)**: Statically parses `index.html` and `main.js` to ensure zero remote URL links, synchronous `window.__timelines["root"]` binding, and bounded animation loops.
6. **Checkpoint 6 (Video File Validity)**: Uses FFprobe/FFmpeg to inspect `renders/final.mp4` for valid H.264 video streams, AAC audio streams, positive duration, and correct pixel dimensions (1920x1080 or 1080x1920).
