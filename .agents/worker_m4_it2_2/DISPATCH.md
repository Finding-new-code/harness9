## 2026-09-14T05:01:00Z
You are worker_m4_it2_2, a teamwork_preview_worker subagent (replacement worker for worker_m4_it2 resuming from interruption point).
Working directory: g:\Finding-new-code\harness9\.agents\worker_m4_it2_2

MANDATORY INSTRUCTION: You MUST read the authoritative request at g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work. Do NOT skip this.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

SCOPE & TASK DESCRIPTION:
Resume and complete Milestone 4 (Iteration 2 Remediation) for Harness 9 Epistemic Verification Layer.

PRIOR WORK COMPLETED BY PREDECESSOR:
Predecessor worker_m4_it2 completed Part A before being interrupted by a quota error:
- Part A (src/epistemic/script_verifier.py): Hardcoded "room" removed, contract inspection implemented, contraction protection added, modal escalation matrix implemented, duplicate drifts deduplicated, ScriptSentenceSegmenter exported. Verify this via `uv run pytest tests/test_script_verifier.py tests/test_script_verifier_adversarial.py -v` (47 tests).

YOUR TASKS TO COMPLETE (RESUMING FROM PART B):
1. Part B: Visual Verifier Remediation (src/epistemic/visual_verifier.py, tests/test_visual_verifier.py):
   Reference: g:\Finding-new-code\harness9\.agents\explorer_2_m4_it2\handoff.md
   - Generalize entity count regex to support arbitrary entity nouns ("battalions", "vessels", etc.) without hardcoded 11-noun lists.
   - Generalize comparison panel validation for bidirectional relations ("higher than", "greater than", "less than", etc.).
   - Parse BCE/BC dates into negative years (-44, -500) for monotonic chronology checks.
   - Add global cross-scene timeline sequence auditing across scene boundaries.
   - Expand trend polarity lexicon ("crashed", "collapsed", "tanked", "plunged", "skyrocketed").
   - Support entity count quantifier ("dozens" -> 24) and singular noun boundaries.
   - Add dataset ID fallback extracting data_points directly from verified NumericalDataset in datasets.

2. Part C: Numerical Pipeline & Adversarial Remediation (src/epistemic/numerical_pipeline.py, tests/test_m4_adversarial_challenger2.py):
   Reference: g:\Finding-new-code\harness9\.agents\explorer_3_m4_it2\handoff.md
   - Reject NaN/Inf tuples in NumericalDataPoint.validate_uncertainty.
   - Anchor base_val to y_axis_min when has_truncated_baseline=True in both DeterministicChartRenderer.render_chart and NumericalInvariantChecker.verify_chart_data.
   - Remove all 7 @pytest.mark.xfail markers from tests/test_m4_adversarial_challenger2.py so all 16 tests pass.

3. Part D: Verification & Full Regression:
   - Run all M4 unit and adversarial tests:
     uv run pytest tests/test_script_verifier.py tests/test_visual_verifier.py tests/test_numerical_pipeline.py tests/test_script_verifier_adversarial.py tests/test_m4_adversarial_challenger2.py -v
   - Run full baseline regression suite:
     uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -v
   - Verify all 228 tests pass with 0 regressions.
