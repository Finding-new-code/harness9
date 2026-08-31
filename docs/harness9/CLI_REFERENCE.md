# Harness 9 — CLI Reference & Configuration

## 1. Command-Line Entrypoints

Harness 9 provides two primary CLI interfaces:

1. **`run_harness9.py`** — Top-level runner for generating videos from topic briefs.
2. **`verify_pipeline.py`** — Verification harness for testing and validating the entire pipeline.

---

## 2. `run_harness9.py` Options

### Syntax
```bash
python run_harness9.py [OPTIONS]
```

### Options Table

| Flag | Type | Default | Description |
|---|---|---|---|
| `--topic` | `str` | `"The History of the Transistor"` | The topic, concept, or brief to research and produce. |
| `--format` | `str` | `16:9` | Video aspect ratio. Supported values: `16:9` (1920x1080) or `9:16` (1080x1920). |
| `--duration` | `int` | `30` | Target video duration in seconds (10 to 180 seconds). |
| `--output-dir` | `str` | `output/<topic_slug>` | Directory where project files, assets, and renders will be stored. |
| `--offline` | `flag` | `False` | Force offline mode using built-in curated presets, procedural SVGs, and local TTS. |
| `--voice` | `str` | `"default"` | Voice profile identifier (`"default"`, `"elevenlabs"`, `"sapi"`, `"synthetic"`). |
| `--fps` | `int` | `30` | Render frame rate for the final MP4 video. |
| `--verbose` | `flag` | `False` | Enable detailed debug logging to stdout. |

### Examples

```bash
# Generate a 30s widescreen 16:9 video
python run_harness9.py --topic "The Discovery of Penicillin" --format 16:9 --duration 30

# Generate a 15s vertical 9:16 video for YouTube Shorts
python run_harness9.py --topic "How Neural Networks Learn" --format 9:16 --duration 15 --output-dir output/neural_short

# Run in an isolated offline environment
python run_harness9.py --topic "The Apollo 11 Moon Landing" --offline
```

---

## 3. Environment Variables

Configure optional API credentials in your `.env` or system environment:

| Variable | Required | Description |
|---|---|---|
| `ELEVENLABS_API_KEY` | Optional | API key for high-fidelity ElevenLabs voice synthesis. (Falls back to SAPI/harmonic WAV if unset). |
| `ELEVENLABS_VOICE_ID` | Optional | Custom ElevenLabs voice ID to use for narration. |
| `PEXELS_API_KEY` | Optional | API key for searching Pexels photo & video catalog. |
| `OPENAI_API_KEY` | Optional | API key for LLM-based creative synthesis (when running in LLM mode). |
| `HARNESS_OFFLINE` | Optional | Set to `1` or `true` to force global offline fallback mode. |

---

## 4. `verify_pipeline.py` Options

### Syntax
```bash
python verify_pipeline.py [OPTIONS]
```

### Options Table

| Flag | Type | Default | Description |
|---|---|---|---|
| `--test-mode` | `flag` | `False` | Run acceptance verification against all 6 production checkpoints. |
| `--topic` | `str` | `"The History of the Transistor"` | Test topic to execute and verify. |
| `--output-dir` | `str` | `output/test_verification_run` | Target output directory for the verification run. |
| `--offline` | `flag` | `True` | Run verification in hermetic offline mode. |
| `--format` | `str` | `16:9` | Aspect ratio for test rendering. |

### Example
```bash
python verify_pipeline.py --test-mode
```

Output:
```
================================================================================
HARNESS 9 — AUTOMATED ACCEPTANCE VERIFICATION
================================================================================
[CHECKPOINT 1/6] Research Dossier Integrity: PASSED
[CHECKPOINT 2/6] Asset Ledger & Rights Provenance: PASSED
[CHECKPOINT 3/6] Audio Narration & Alignment: PASSED
[CHECKPOINT 4/6] HyperFrames Project Files: PASSED
[CHECKPOINT 5/6] HyperFrames Composition Linter: PASSED
[CHECKPOINT 6/6] Video File Validity & Streams: PASSED
================================================================================
VERIFICATION SUMMARY: 6/6 PASSED (100%) — VICTORY CONFIRMED
================================================================================
```
