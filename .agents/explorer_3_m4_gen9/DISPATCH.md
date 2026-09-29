## 2026-09-14T00:03:10Z
You are explorer_3_m4_gen9, a teamwork_preview_explorer subagent.
Working directory: g:\Finding-new-code\harness9\.agents\explorer_3_m4_gen9

MANDATORY INSTRUCTION: You MUST read the authoritative request at g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work. Do NOT skip this.

Scope Document: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_9\PROJECT.md

OBJECTIVE:
Investigate and specify the deterministic numerical data pipeline (src/epistemic/numerical_pipeline.py) and test suite strategy for Milestone 4 (R4).

KEY SOURCES TO INVESTIGATE:
1. docs/epistemic/CLAIM_VERIFICATION.md
2. docs/epistemic/VISUAL_FACT_CHECKING.md
3. docs/epistemic/FACTBENCH.md
4. src/epistemic/strategies.py (check NumericalVerificationStrategy)
5. src/models/contracts.py

YOU MUST SPECIFY:
1. Deterministic numerical data pipeline:
   - Ingestion: raw dataset / CSV / table parsing into NumericalDataset.
   - Transformations: aggregation, percentage calculation, scaling with exact precision.
   - Chart rendering pipeline: deterministic chart configuration generation from dataset.
   - Invariant checking: ensuring chart rendering preserves exact values, prevents truncation misleading visuals (e.g. non-zero baselines without explicit warning), unit mismatches (e.g. thousands vs millions).
2. Comprehensive test suite design for R4:
   - tests/test_script_verifier.py: test cases for strengthened claims, altered numbers, omitted uncertainty, fabricated quotes.
   - tests/test_visual_verifier.py: test cases for timeline reconciliation, chart verification, count verification, cross-modal contradictions.
   - tests/test_numerical_pipeline.py: test cases for dataset-to-chart determinism, precision, unit conversions.
3. Ensure seamless interoperability with existing 144 passing tests.

SCOPE BOUNDARIES:
- Read-only exploration. DO NOT write or edit source code files.
- Maintain progress.md in your working directory with 'Last visited: [timestamp]' for liveness.

DELIVERABLE:
Write a complete 5-part handoff report to g:\Finding-new-code\harness9\.agents\explorer_3_m4_gen9\handoff.md (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
When done, notify parent using send_message with your handoff summary.
