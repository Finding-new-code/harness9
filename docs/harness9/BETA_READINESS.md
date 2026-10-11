# Harness 9 limited beta readiness: Windows

**Assessment date:** 2026-10-11  
**Disposition:** Ready for a small, supervised Windows pilot using curated research.  
**Tested scope:** 15-second 16:9 and 9:16 videos; 30-second 16:9 video; Windows SAPI; real Chrome/FFmpeg rendering; optional configured Hermes model.

The cleanest tester path keeps the curated, source-reviewed research while discovering real images online. Add `--model-script` to exercise the configured model in the production pipeline:

```powershell
.venv\Scripts\python.exe run_harness9.py `
  --topic "How GPUs Work" `
  --duration 15 `
  --format 16:9 `
  --output-dir output\beta-gpu `
  --offline --online-assets --model-script --json
```

`--online-assets` is an explicit network opt-in. In this combination, `--offline` means curated research; the effective asset mode and model use are recorded separately in `pipeline_summary.json`. Each tester must configure their own Hermes provider credentials. The Azure credential used for these checks is kept in the local Hermes profile, outside this repository.

## Real production-path evidence

| Run | Result | Measured evidence |
|---|---|---|
| `output/h9-beta-curated-final-20261011` — GPU, 30s, 16:9 | `SUCCESS` | 900 Chrome frames at 1920×1080/30 fps; three frozen Wikimedia assets; SAPI audio 29.58s; media gate passed. |
| `output/h9-beta-curated-15s-final-20261011` — GPU, 15s, 16:9 | `SUCCESS` | 450 Chrome frames; three frozen Wikimedia assets; SAPI audio 14.19s; media gate passed. |
| `output/h9-beta-quantum-15s-live-20261011` — Quantum, 15s, 16:9 | `SUCCESS` | Three frozen Wikimedia assets, including a real GIF; SAPI audio 14.94s; 450 Chrome frames; media gate passed. |
| `output/h9-beta-curated-model-15s-20261011` — GPU, 15s, model-assisted 16:9 | `SUCCESS` | Actual `azure-foundry:gpt-6-luna` request; verified curated claims; three licensed Wikimedia assets; SAPI audio 14.52s; media gate passed. |
| `output/h9-beta-curated-model-15s-9x16-final-20261011` — GPU, 15s, model-assisted 9:16 | `SUCCESS` | Actual Azure model request; 1080×1920/30 fps; three real assets with correct per-scene claim links; SAPI audio 14.88s; zero fallbacks; media gate passed. |
| `output/h9-beta-model-assisted-15s-live-retry1-20261011` — Apollo, 15s, live research/model | `PARTIAL` (expected) | Azure model and render succeeded; three real Wikimedia assets; SAPI audio 14.02s; 450 frames and media gate passed. All four live claims remain `UNVERIFIED`, so the pipeline did not report `SUCCESS`. |

The saved Hermes model configuration was exercised through actual Responses API requests; the model-assisted production runs report `azure-foundry:gpt-6-luna`. The 15-second GPU model script uses three scenes and passed the measured audio-duration gate in both aspect ratios.

The portrait contact sheet is at `output/h9-beta-visual-review-20261011/portrait_final_contact_sheet.jpg`. It was reviewed after the final asset-query update. The SIMT scene now uses a Wikimedia microarchitecture diagram, with its creator and Apache 2.0 license recorded in the asset ledger.

## Reliability and content gates

- Stage 3 measures the generated WAV and refuses audio that would be clipped or leave a material silent tail.
- A run can be `SUCCESS` only when the real render is `VERIFIED`, every research claim is verified, and no asset is a generated fallback. Live research is intentionally `PARTIAL` until its claims receive human/source review.
- Model-written narration must use each scene's allowed claim IDs, meet per-scene and total word budgets, and fit the selected target. The writer makes at most two bounded revision calls, then fails closed.
- Asset ledgers link each scene's visual to that scene's `supported_claim_ids`, including scenes backed by multiple claims. Unknown claims are not invented to fill gaps.
- Live search/download failures remain visible as generated fallbacks; those outputs cannot be mistaken for a fully successful run.
- The focused regression suite passed **98 tests** on this checkout: assets, adversarial assets, scriptwriting, research integrity, and CLI.
- `run_harness9.py --check-render` found Node, Chrome, FFmpeg, ffprobe, and the render toolchain without a PATH override; `ready_without_install` was `true`.

## Pilot limits

- The full render checks cover GPU and quantum curated topics. Windows SAPI duration checks also cover the transistor and Apollo curated presets, but those two do not yet have a clean full production render recorded here.
- The real model-assisted live Apollo run is a content-review sample, not a publishable success. Its `PARTIAL` result is correct until its four claims are checked against reliable sources.
- The checks use one Windows host. They do not establish compatibility with other Windows versions or other operating systems.
- 15-second rendering took about two minutes on this host. Longer jobs and other durations were not characterized.
- `FROZEN_LOCAL` records downloaded media and rights metadata; testers should preserve the asset ledger when sharing videos that use attribution-required licenses.

This is a limited pilot disposition, not a public-release or broadcast-certification claim.
