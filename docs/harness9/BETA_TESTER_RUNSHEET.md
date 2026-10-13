# Harness 9 Three Tester Beta Run Sheet

Use a fresh output directory for every run. Run these steps from the repository root in PowerShell. The pilot covers the Windows `run_harness9.py` production CLI; the separate `h9.render` Hermes tool is not part of this pilot because it cannot synthesize narration from Production IR by itself.

## Before Each Run

1. Confirm Python dependencies and the tester's Hermes model provider are configured outside the repository. Speech also needs a usable Windows SAPI voice or ElevenLabs credentials; model credentials alone do not provide TTS.
2. Run `.venv\Scripts\python.exe run_harness9.py --check-render`. Confirm `problems` is empty and `ready_without_install` is `true`.
3. Check SAPI from the same Windows account that will run the pipeline:

   ```powershell
   .venv\Scripts\python.exe -c "from src.scriptwriting.tts import WindowsSAPITTSProvider; print('usable_sapi', WindowsSAPITTSProvider().is_available())"
   ```

   If it prints `False`, configure ElevenLabs TTS outside the repository before the run.
4. Do not publish or upload generated videos from these runs. Keep all output directories unique.

## Tester Scenarios

### Tester 1: Landscape, curated research, model-assisted script

```powershell
.venv\Scripts\python.exe run_harness9.py `
  --topic "How GPUs Work" --duration 15 --format 16:9 `
  --output-dir output\beta-tester-1-landscape `
  --offline --online-assets --model-script --json
```

Expected: exit code `0`, `pipeline_summary.json` status `SUCCESS`, verified claims, three frozen assets, SAPI narration, 450 frames at 1920x1080/30 fps, and a passing media gate.

### Tester 2: Portrait, curated research, model-assisted script

```powershell
.venv\Scripts\python.exe run_harness9.py `
  --topic "How GPUs Work" --duration 15 --format 9:16 `
  --output-dir output\beta-tester-2-portrait `
  --offline --online-assets --model-script --json
```

Expected: exit code `0`, status `SUCCESS`, 450 frames at 1080x1920/30 fps, three frozen assets, SAPI narration, and a passing media gate.

### Tester 3: Live research and source review

```powershell
.venv\Scripts\python.exe run_harness9.py `
  --topic "Apollo 11" --duration 15 --format 16:9 `
  --output-dir output\beta-tester-3-live-research `
  --online --model-script --json
```

Expected: live search and asset discovery make network requests. With at least three usable claims, a real render and audio should complete; the run should report `PARTIAL` (CLI exit code `1`) while claims remain `UNVERIFIED`. This tests the source-integrity gate; do not relabel it `SUCCESS`. The `Apollo 11` topic produced five unverified claims in the readiness check. Live results vary, and fewer than three usable claims should stop research with `FAILED` before later artifacts are written. That is a valid fail-closed outcome; retry with a broader topic if the goal is to test the rendered `PARTIAL` path. If a run reports `SUCCESS`, review every cited source before treating the content as publishable.

## Return These Results

Send the output directory or an archive containing `pipeline_summary.json`, `research_dossier.json`, `asset_ledger.json`, `SCRIPT.md`, `STORYBOARD.md`, `assets/transcript.json`, `renders/final.mp4` when present, and `renders/final.gate.json` when present. Include the preflight JSON, exit code, Windows version, elapsed time, audio intelligibility notes, visual defects, and any claim/source concerns. Do not include `.env`, API keys, tokens, or other credentials.
