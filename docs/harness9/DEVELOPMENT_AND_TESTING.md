# Harness 9 — Development & Testing Guide

## 1. Development Environment

Harness 9 runs natively on Windows, macOS, and Linux with Python 3.10+ and Node.js.

### Dependencies
- **Python**: `httpx`, `pydantic`, `pyyaml`, `pytest`
- **System**: `ffmpeg` (for video/audio encoding)
- **Node.js (>= 18) + Chrome/Chromium/Edge**: required for real rendering (headless frame capture via puppeteer-core; installed once into `~/.harness9/render-toolchain`). There are **no automatic fallbacks**: if the renderer is unavailable the run fails with instructions. Use `--render-backend stub` (or `HARNESS9_RENDER_BACKEND=stub`) for an explicit, labelled dry run. Tests that only exercise pipeline stages select the stub backend via `tests/h9_render_env.py`; real-render tests skip when the toolchain is absent. See `RENDERING.md`.

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
python verify_pipeline.py --topic "How GPUs Work" --duration 15 --output-dir output/verify-gpu
```

To verify the configured model and real online assets as well, add `--online-assets --model-script`. For live research, replace the default `--offline` with `--no-offline`; unverified live claims correctly leave the run `PARTIAL` and the verifier exits non-zero.

### Checkpoints Evaluated:
1. **Checkpoint 1 (Research Dossier)**: Requires at least three claims, HTTPS sources, finite confidence scores in `[0, 1]`, and `VERIFIED` status.
2. **Checkpoint 2 (Asset Ledger & Rights)**: Requires frozen local assets, HTTPS source metadata, creator and license details, attribution text when required, an in-project path, and a matching SHA-256 hash.
3. **Checkpoint 3 (Audio Narration)**: Parses WAV headers and duration; other supported audio formats must pass `ffprobe` stream and duration checks.
4. **Checkpoint 4 (HyperFrames Project Contract)**: Requires `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, `index.html`, `styles.css`, and `main.js`.
5. **Checkpoint 5 (Composition Linter)**: Checks the root composition, local media references, and finite animation loops.
6. **Checkpoint 6 (Video File Validity)**: Requires `ffprobe` to confirm an H.264/AAC MP4 with video and audio streams and a positive duration. The production media gate separately measures resolution, frame rate, audio/video sync, and visual/audio quality.

The verifier runs the real production pipeline; it does not fabricate replacement
artifacts. It only applies these checks to a pipeline run whose status is
`SUCCESS`. A live-research result with unreviewed claims is expected to remain
`PARTIAL` and exit non-zero.
