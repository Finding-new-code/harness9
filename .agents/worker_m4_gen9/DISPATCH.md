## 2026-09-14T00:10:32Z
You are worker_m4_gen9, a teamwork_preview_worker subagent.
Working directory: g:\Finding-new-code\harness9\.agents\worker_m4_gen9

MANDATORY INSTRUCTION: You MUST read the authoritative request at g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work. Do NOT skip this.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

SCOPE & TASK DESCRIPTION:
Implement Milestone 4 (R4: Multi-Stage Pipeline & Visual/Numerical Integrity) for Harness 9 Epistemic Verification Layer.

READ THE 3 EXPLORER HANDOFF REPORTS CAREFULLY BEFORE IMPLEMENTING:
1. Explorer 1 Report: g:\Finding-new-code\harness9\.agents\explorer_1_m4_gen9\handoff.md (Script Re-Verification Specification)
2. Explorer 2 Report: g:\Finding-new-code\harness9\.agents\explorer_2_m4_gen9\handoff.md (Visual Fact-Checking Specification)
3. Explorer 3 Report: g:\Finding-new-code\harness9\.agents\explorer_3_m4_gen9\handoff.md (Deterministic Numerical Pipeline & Test Suite Strategy)
4. Scope Document: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_9\PROJECT.md

EXCLUSIVELY OWNED FILES (You own and write these files):
- src/epistemic/script_verifier.py
- src/epistemic/visual_verifier.py
- src/epistemic/numerical_pipeline.py
- src/epistemic/__init__.py
- src/models/contracts.py (if exposing or updating contract imports/models)
- tests/test_script_verifier.py
- tests/test_visual_verifier.py
- tests/test_numerical_pipeline.py

IMPLEMENTATION REQUIREMENTS:
Part A: Post-Script Claim Re-Verification (src/epistemic/script_verifier.py):
- Sentence segmentation with abbreviation, number, and quotation boundary protection.
- Bipartite alignment of script sentences against EvidenceGraph DAG nodes.
- Forensic drift detection across all 4 canonical classes:
  * Strengthened claims (modal level 1/2 vs 3, unearned confidence jumps).
  * Altered numbers (SI normalization, dual tolerances 0.1%/5.0%, compound growth, 10x order-of-magnitude traps).
  * Omitted uncertainty (hedging enforcement for UNVERIFIED, CONTESTED, and ACTIVE_DEBATE consensus states).
  * Fabricated quotes (normalized Levenshtein distance D_norm <= 0.02 and strict Paraphrase Mandate).
- Pydantic v2 return models: ScriptVerificationReport, ScriptClaimDriftRecord, DriftType, DriftSeverity, ScriptClaimMapping, and actionable recommended_edit.
- EvidenceGraph synchronization (sync_to_evidence_graph) inserting ScriptSentenceNode and VerificationTraceNode without violating acyclicity.

Part B: Visual Fact-Checking Engine (src/epistemic/visual_verifier.py):
- Ingestion of Storyboard / Scene elements and reconciliation against script narration & EvidenceGraph.
- Timeline verification: monotonic ordering (no chronology inversions), date consistency against voiceover and evidence.
- Chart verification: coordinates vs backing NumericalDataset, trend slope/polarity (+1, -1, 0) vs narration sentiment, strict zero-baseline enforcement on bar/column charts.
- Entity counts: voiceover quantities vs on-screen visual elements.
- Map/geospatial checks: territory label anachronisms (e.g., USSR date bounds).
- Return models: VisualVerificationReport, VisualInconsistencyRecord, VisualDiscrepancyType, VisualSeverity.

Part C: Deterministic Numerical Data Pipeline (src/epistemic/numerical_pipeline.py):
- Ingestion: CSV/JSON parsing into NumericalDataset with canonical SHA-256 hash.
- Exact Decimal-backed transformations: aggregations, percentage shares (100.0% sum invariant via Largest Remainder Method), period growth with division-by-zero guards, unit scaling.
- Deterministic SVG/chart generation: pure coordinate projection with reproducible cryptographic hashes and zero hallucination.
- Invariant checking: zero-baseline distortion guards, coordinate value fidelity (< 10^-4), unit alignment, non-averaging contradiction preservation.
- Models: NumericalDataPoint, NumericalDataset, ChartType, ChartElement, ChartConfig, NumericalTransformationRecord, NumericalVerificationResult.

Part D: Comprehensive Test Suites & Verification:
- Implement tests/test_script_verifier.py, tests/test_visual_verifier.py, tests/test_numerical_pipeline.py.
- Run your new tests:
  uv run pytest tests/test_script_verifier.py tests/test_visual_verifier.py tests/test_numerical_pipeline.py -v
- Run full regression suite to ensure ZERO regressions:
  uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -v
- All tests must pass (100% pass rate).

DELIVERABLE:
1. Complete, genuine, tested implementations in the owned files.
2. Run test commands and document results.
3. Write 5-component handoff report to g:\Finding-new-code\harness9\.agents\worker_m4_gen9\handoff.md (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
4. Send completion message to parent with summary and test results.
