# Harness 9 limited beta readiness: Windows

**Assessment date:** 2026-10-12
**Disposition:** Ready for a supervised beta with three Windows testers.
**Scope:** 15-second model-assisted videos in landscape and portrait, curated research with live licensed assets, and one live-research source-integrity scenario.

## Current production-path evidence

Both curated runs used the configured `azure-foundry:gpt-6-luna` model, real Windows SAPI narration, online Wikimedia asset discovery, Chrome capture, and FFmpeg. Each run returned `SUCCESS`, passed all six verifier checkpoints, and passed the media gate.

| Run | Result | Measured evidence |
|---|---|---|
| `output/h9-beta-verified-model-15s-20261012-rerun3` | `SUCCESS` | Four cited research claims; three frozen, licensed assets; SAPI audio 14.32s; 450 frames at 1920x1080/30 fps; verified H.264/AAC render. |
| `output/h9-beta-verified-model-15s-9x16-20261012` | `SUCCESS` | Four cited claims; three frozen, licensed assets; SAPI audio 13.93s; 450 frames at 1080x1920/30 fps; verified H.264/AAC render. |
| `output/h9-beta-live-integrity-apollo11-20261012` | `PARTIAL` (expected) | Five live claims remain unverified; three frozen, licensed assets; SAPI audio 14.12s; verified 450-frame Chrome render; no generated fallback visuals. The CLI returned 1 and correctly marked the output non-publishable. |
| `output/h9-beta-curated-final-20261011` | `SUCCESS` (prior host run) | 30-second 16:9 render with 900 Chrome frames and SAPI audio 29.58s. |

The live Apollo 11 scenario is the third tester's source-review exercise. A separate attempt with `The Apollo Guidance Computer` found only one usable claim and stopped at research; live mode intentionally requires at least three and does not invent replacement claims.

## Readiness checks

- `run_harness9.py --check-render` found Node, npm, Chrome, FFmpeg, and the installed render toolchain; `problems` was empty and `ready_without_install` was `true`.
- The focused component suite passed **247 tests and 3 subtests** across acceptance, content tools, runtime, provider/subagent behavior, skills, HyperFrames, rendering, research, CLI, scriptwriting, end-to-end pipeline, and verifier suites.
- Full repository collection was not completed: unrelated ACP tests require the optional `acp` package, which is absent in this environment. Do not treat the scoped suite as a full-repository pass.
- The suite includes two duration-fitting regression tests. Small WAV overruns receive at most 5% pitch-preserving FFmpeg time compression and are remeasured; larger overruns remain subject to the pipeline's fail-closed duration gate.
- Landscape and portrait contact sheets were spot-checked for visible assets, titles, and captions within the frame.

## Tester requirements and limits

Each tester needs the configured Hermes model provider plus a usable Windows SAPI voice or an ElevenLabs TTS credential. Run the SAPI check in the run sheet from the account that will run H9; model credentials alone do not supply speech synthesis. Keep outputs local during the pilot. The live scenario must stay `PARTIAL` until a person checks every claim against its linked source; fewer than three usable live claims should stop early with `FAILED`.

These checks use one Windows host and do not establish compatibility with other Windows releases. A 15-second render took about two minutes here. Testers should record speech intelligibility, visual defects, Windows version, elapsed time, and any source concerns. Preserve each asset ledger when sharing attribution-required media. This disposition covers a supervised beta only, not public release or broadcast certification.
