# Harness 9 — Roadmap to Beta and SOTA

Status date: 2026-09-30 · Baseline: `dev@c8c387b` + the render/media-gate patch.
"Verified" = measured or read in code on that baseline. "Proposed" = a target or design choice to confirm.
Executable task cards for a coding agent live in [`AGENT_TASKS.md`](AGENT_TASKS.md).

## 1. Positioning (what "SOTA" should mean here)

Harness 9 will not out-render frontier generative-video models, and it should not try. The defensible
position is **verifiable explainer video**: every factual sentence traces to a source span, every pixel and
audio sample is measured before the file is called "verified", and the output is an editable, deterministic
HTML composition rather than an opaque clip. Compete on **integrity, measured quality, and editability**.

## 2. Where it stands (verified)

| Area | Today | Evidence |
| --- | --- | --- |
| Rendering | **Real** after the patch (headless Chromium seeks GSAP timelines) | 5 real-Chromium tests; 1080p sample frames viewed |
| Output verification | Pixels, motion, audio level/silence, loudness, container are measured. Speech intelligibility, captions, facts are **not** | `src/evaluation/media_gate.py` |
| Research | Regex over search snippets; **fabricates** claims and citations when offline or when live search finds < 3 claims | `src/research/engine.py:274, 337 (confidence 0.91), 493, 506` |
| Script | f-string template: title + hook + claim | `src/scriptwriting/generator.py:399` |
| Models in the loop | None in research / script / editorial stages | grep for provider names finds only `h9_runtime/models.py`, `voice_director.py`, `creator/economics.py` |
| Narration | ElevenLabs → Windows SAPI → harmonic synthesizer. On a machine with neither, the "narration" is a synthetic waveform, not speech | `src/scriptwriting/tts.py` |
| Epistemic verifier, ContentBench | ~7k LOC that no pipeline calls. Entailment is word overlap + a negation list | `src/epistemic/strategies.py:135-186` |
| Orchestration | Three overlapping layers: `Pipeline`, `h9_runtime` (fast-forwards the state machine after the fact), `verify_pipeline.py` (a 1,033-line mini re-implementation the e2e tests drive) | `src/h9_runtime/content.py`, `verify_pipeline.py` |
| Tests | 1,213 pass without a browser toolchain (+48 new tests; 5 more real-Chromium tests run when it is installed). 19 were red at baseline, 5 of them named `*_bug`. `test_e2e_comprehensive.py` imports no project code; `test_renderer.py` has 4 `assertTrue(True)` | Appendix A in `AGENT_TASKS.md` |
| Repo | Product lives inside a 12,097-file Hermes fork. 1,147 scratch/output files (55 MB, 109 binaries/DBs) are tracked; `.gitignore` is upstream's | `git ls-files` |
| Speed | ~0.1–0.2 s per 1080p frame, sequential (60 s video ≈ 3–6 min) | measured in the sandbox |

Scorecard (author's judgment, 0–10): Vision 8 · Architecture 7 · Code hygiene 6 · Tests 5 ·
Factual integrity 2 · Output quality 1 → **4** after the patch (real visuals; narration/captions/assets still basic).

## 3. Phases

| Phase | Goal | Rough size* | Exit |
| --- | --- | --- | --- |
| **0 — Make it honest** | No fabricated claims, no tautological tests, clean repo, CI | 1–2 weeks | §4 items B0–B3 |
| **1 — Beta** | A stranger can install it and get a verified, watchable 60 s video reliably | 4–6 weeks | all of §4 |
| **2 — SOTA tracks** | Lead on integrity, audio, visuals, speed, evaluation, product | 3–6 months, parallel | §6 targets |

*One to two engineers or agents working in parallel lanes (see `AGENT_TASKS.md`). Sizes are rough estimates.

```
T0.1 patch ─┬─> T0.2 hygiene ─┐
            └─> T0.7 CI ──────┤
T0.3 no-fabrication ─> T0.4 span-verified claims ─> T1.2 research v2 ─> T1.3 script v2 ─┐
T1.1 LLM layer ───────────────────────────────────^                                      ├─> T1.11 beta run
T1.4 real TTS ─> T1.5 alignment/captions ─> T1.6 render speed + layout QA ───────────────┘
T0.5 red tests, T0.6 real tests ─> T1.7 one orchestrator ─> T1.9 extract from fork
```

## 4. Beta exit criteria (proposed; tune after the first baseline run)

| # | Criterion | How it is measured |
| --- | --- | --- |
| B0 | Zero fabricated sources: every claim carries a verbatim quote that is found in a cached source document | automated span check (T0.4) |
| B1 | ≥ 95% of runs on a 20-topic set produce a gate-passing 60 s video with no manual step | `scripts/run_benchmark.py`, nightly |
| B2 | Every numeric/proper-noun token in the narration appears in a cited claim | script validator (T1.3) |
| B3 | Narration ASR round-trip WER ≤ 10%; caption WER ≤ 5%; caption drift p95 ≤ 100 ms | gate checks (T1.4, T1.5) |
| B4 | Loudness −14 ± 1.5 LUFS, true peak ≤ −1 dBTP, zero layout overflow defects | gate (T1.4, T1.6) |
| B5 | 60 s 1080p30 renders in ≤ 1.5× real-time on 8 cores | benchmark timing |
| B6 | CI green on Linux and Windows; no red or unexplained skipped tests; tests import real code | `h9-ci.yml`, test-quality lint |
| B7 | Fresh machine to first verified video in ≤ 15 min; cost per video logged and budget-capped | install doc + `run.json` |

## 5. Decisions needed from you

1. **Fork or package?** Recommended: extract `harness9` into its own repo/package and keep Hermes as an integration target (only `tools.registry` is a static dependency).
2. **Primary platform.** Paths in the scratch probes suggest Windows development; confirm. CI must cover it.
3. **Providers and budget.** Which LLM(s), search API, and TTS you will pay for; the per-video budget cap.
4. **Asset policy.** Wikimedia/NASA/stock only, or also generated images? Affects the rights ledger and licensing review.
5. **Audience.** Long explainers (YouTube) or shorts (9:16)? Drives pacing, layout QA, and the first distribution connector.
6. **Human review.** Who rates videos (≥ 5 raters) for the pairwise evaluations in §6-B and §6-F?

## 6. SOTA tracks (run in parallel after Phase 1)

Each track: **target** → **gap** → **moves** → **metric**. Targets are proposals.

### A. Factual integrity and provenance (the moat)
* **Target:** unsupported-claim rate ≤ 1% on a human-labelled audit; ≥ 90% of planted falsehoods caught.
* **Gap:** heuristic verifier, unwired; fabricated fallbacks (§2).
* **Moves:** (1) replace word-overlap entailment with a calibrated NLI cross-encoder or LLM judge, tuned on a public set (e.g. FEVER/VitaminC) plus ~300 own labelled claims, threshold chosen for ≥ 95% precision; (2) structured numbers/dates with unit normalisation and arithmetic/temporal checks (fixes the red numeric tests); (3) source tiers, mirror/syndication detection, correction checks; (4) disagreement handling ("sources differ" or drop); (5) verify the final narration, not just the claims; (6) provenance sidecar plus signed **C2PA Content Credentials** on the MP4 and an auto-generated Sources end card; (7) adversarial suites: planted falsehoods and prompt-injection pages.
* **Metric:** claim-support precision/recall, planted-error catch rate, injection-suite pass rate.

### B. Script and storytelling
* **Target:** beats a strong baseline in ≥ 65% of blind pairwise comparisons on 50 topics.
* **Moves:** retention-aware structure as constraints (hook ≤ 3 s, open loops, pattern interrupt every 20–30 s); n=4 candidates + judge tournament; capped self-critique; **creator-style memory that is injected and ablation-tested** (with vs without); choose the most surprising *verified* claims (wire `src/editorial`, which is template-driven today).
* **Metric:** pairwise win-rate; judge↔human Spearman ≥ 0.6 on 100 scripts; speaking rate 140–170 wpm.

### C. Voice and audio
* **Target:** UTMOS ≥ 4.0 and human MOS ≥ 4.0 on 20 samples; ASR WER ≤ 3%; −14 LUFS; true peak ≤ −1 dBTP.
* **Moves:** neural TTS (local default, premium optional) with prosody hints and a pronunciation lexicon; sentence-level synthesis cache; music bed with sidechain ducking (≥ 10 dB) from a licensed library; SFX on cuts; mastering chain; mispronunciation detection (ASR + phoneme diff); gate additions: clipping, DC offset, spectral flatness (non-speech detection), VAD ratio.
* **Metric:** UTMOS, WER, LUFS/dBTP, A/V sync p95 ≤ 80 ms.

### D. Visual design and motion
* **Target:** human rating ≥ 4/5 on clarity and aesthetics; zero layout defects in 16:9, 9:16, 1:1; charts correct by construction.
* **Moves:** data-driven charts/timelines/maps generated from *verified numeric claims*; asset retrieval with license capture (Wikimedia/NASA/stock) + CLIP re-ranking, optional generated imagery with provenance; shot-variety rules (no layout repeated > 2×, a visual change every ≤ 3 s); brand kits; DOM QA (overflow, safe areas, WCAG contrast, missing glyphs, upscale blur); a VLM critic over keyframes as a soft gate.
* **Metric:** layout defects = 0; VLM relevance/legibility ≥ 4/5; license-ledger completeness 100%; blind pairwise vs baseline.

### E. Rendering performance and determinism
* **Target:** 60 s 1080p30 in ≤ 0.5× real-time on 8 cores; one-scene re-render ≤ 10 s; pixel-stable across machines in the pinned container.
* **Moves:** parallel capture workers; direct frame piping to ffmpeg; CDP `beginFrame` determinism; scene-level frame cache keyed by (HTML, assets, time); optional hardware encoders guarded by a quality check (SSIM ≥ 0.98 or VMAF ≥ 95 vs libx264); pinned render container with fixed fonts; golden-frame tests for components; 4K and 9:16 support.
* **Metric:** wall-clock ÷ duration; frame-hash equality across worker counts; SSIM vs goldens.

### F. Evaluation and benchmarking (ContentBench, for real)
* **Target:** ≥ 50 topics, ≥ 12 metrics, nightly trend, regression gates, published methodology.
* **Moves:** metric suite = claim-support precision, unsupported-claim rate, planted-error catch, ASR WER, caption WER/drift, loudness, layout defects, gate pass rate, VLM score, calibrated judge score, $/min, seconds/min. Wire `src/evaluation/contentbench.py` so it **reads artifacts** (today it takes self-reported inputs). Small tracked JSON results + static dashboard; PR comment with deltas; fail a PR on gate-pass −2 pts or cost +20%. Quarterly blind human eval (≥ 5 raters, κ ≥ 0.4).
* **Metric:** the suite itself, plus judge↔human correlation.

### G. Agentic orchestration
* **Target:** ≥ 80% of gate failures auto-repaired within 2 attempts; every agent action auditable.
* **Moves:** map each failing check to a bounded remedy (low detail → richer assets; overflow → shorter text or smaller type; silent audio → re-synthesise with the next provider; duration mismatch → re-pace beats); separate writer from critic (judge + VLM + gate); approval checkpoints (script, assets, publish) through the existing permission model; planner chooses research depth by topic; budgets and attempt caps everywhere.
* **Metric:** repair success rate, attempts per fix, cost per repair.

### H. Product, UX, distribution
* **Target:** first draft ≤ 5 min; one-scene edit → re-render ≤ 10 s; three aspect ratios from one script.
* **Moves:** local-first Studio UI using the same composition for live preview with a scrubber over `__timelines`; edit text/swap asset/regenerate a scene; brand kits and templates; exports (MP4, SRT/VTT, thumbnail, chapters, description with sources); publishing connectors that attach provenance; project versions. **Legal check before shipping a Studio:** verify the current GSAP license terms (they include restrictions for products that offer visual animation builders).
* **Metric:** time-to-first-draft, edit-to-rerender latency, task success in usability tests (5 users).

### I. Security, rights, compliance
* **Target:** external review with zero critical findings; 100% of assets license-recorded; AI-content disclosure on export.
* **Moves:** STRIDE threat model; SSRF/path-traversal/zip-slip suites (fix the red sandbox tests first); Chrome sandbox on outside containers; secret redaction; `pip-audit` + `npm audit` + CycloneDX SBOM per release; prompt-injection red team; licence table for every model, voice and font (some local TTS builds and voices carry GPL or per-voice licences: verify each); misuse policy ("verified-only" mode; refuse persuasive falsehoods).

### J. Reliability and operations
* **Target:** ≥ 99% job success on the benchmark; p95 duration ≤ 2× median; no data loss on `kill -9`.
* **Moves:** error taxonomy; retries with backoff only for idempotent stages; resumable content-addressed stages; job queue + containerised render workers with resource limits; OpenTelemetry traces and metrics, SLOs and alerts; artifact GC and disk quotas; chaos tests (kill mid-render → resume correctly); `schema_version` on every contract with a migration policy; semver releases and a changelog.

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Gate thresholds were calibrated on synthetic controls and one pipeline's renders, so they can mis-fire on new visual styles | Calibrate on the 20-topic set, keep `GateThresholds` per template, log every gate JSON, review false positives weekly |
| LLM cost and nondeterminism | Disk cache + record/replay fixtures in CI, budget caps, pinned prompt versions |
| Scope sprawl (10 tracks) | Finish Phase 1 first; pick two tracks per quarter (recommended: A and C) |
| Fork drift from upstream Hermes | Extract the product (T1.9); test against upstream releases in one CI job |
| Rights and licensing | License ledger enforced at render time; legal review of GSAP, TTS voices, music, fonts |
