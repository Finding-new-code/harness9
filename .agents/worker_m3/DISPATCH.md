## 2026-09-13T19:51:03Z
You are worker_m3. Your working directory is g:\Finding-new-code\harness9\.agents\worker_m3.
Update your progress.md regularly.

MANDATORY FIRST STEP: Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work.
Also read:
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\PROJECT.md
- g:\Finding-new-code\harness9\.agents\explorer_1_m3\analysis.md
- g:\Finding-new-code\harness9\.agents\explorer_1_m3\handoff.md
- g:\Finding-new-code\harness9\.agents\explorer_2_m3\analysis.md
- g:\Finding-new-code\harness9\.agents\explorer_2_m3\handoff.md
- g:\Finding-new-code\harness9\.agents\explorer_3_m3\analysis.md
- g:\Finding-new-code\harness9\.agents\explorer_3_m3\handoff.md
- src/models/contracts.py
- src/epistemic/graph.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE FILE OWNERSHIP:
You have exclusive write access to:
- src/epistemic/strategies.py
- src/epistemic/historical_policy.py
- src/epistemic/engine.py
- src/epistemic/__init__.py
- tests/test_verification_engine.py
- tests/test_historical_policy.py

TASKS TO EXECUTE:
1. Implement the 7 modular verification strategies in src/epistemic/strategies.py per explorer_1_m3/analysis.md and explorer_3_m3/analysis.md:
   - Base VerificationStrategy protocol / class and StrategyExecutionResult.
   - SourceEntailmentStrategy: semantic scoring with 13-tier source weights, modal qualifier checks (detecting unearned assertion strengthening).
   - CrossSourceCorroborationStrategy: multi-source independence calculation, publisher diversity, detecting single-source vulnerabilities.
   - ContradictionCheckStrategy: detecting conflicting claims, opposing polarity, registering ContradictionRecords, preserving opposing edges in EvidenceGraph without arithmetic averaging.
   - QuoteCheckStrategy: normalized character Levenshtein distance, strict boundaries (exact vs ellipses vs distorted), mandate paraphrase when distorted or unverified.
   - NumericalCheckStrategy: numerical metric extraction, unit normalization, dual tolerance (0.1% exact, 5.0% approximate), order-of-magnitude mismatch trap (|delta log10| >= 1.0).
   - TemporalCheckStrategy: chronological precedence, historical anachronisms, freshness interval check.
   - HistoriographicalCheckStrategy: integrates HistoricalPolicyChecker.

2. Implement the Historical Scholarship Policy in src/epistemic/historical_policy.py per explorer_2_m3/analysis.md:
   - HistoricalPolicyChecker class.
   - Prohibition on forbidden sole web sources (Tiers 9-13: Wikipedia, blogs, popular web summaries) for establishing historical facts or interpretations.
   - Minimum evidentiary tier thresholds (Threshold A: Tier 1/6 primary/archival; Threshold B: Tier 3 academic monograph; Threshold C: 2x Tier 2 peer-reviewed articles).
   - Deterministic 8-consensus-state classification (STRONG_CONSENSUS, BROAD_CONSENSUS, MAJORITY_INTERPRETATION, MINORITY_INTERPRETATION, ACTIVE_DEBATE, CONTESTED, UNRESOLVED, INSUFFICIENT_LITERATURE).
   - Event vs. interpretation distinction (EVENT_FACT vs CAUSAL_INTERPRETATION / SCHOLARLY_INTERPRETATION), forbidding unhedged declarative narration for causal models.
   - Non-averaging contradiction invariant (strict prohibition of arithmetic averaging of conflicting counts/dates; preserve discrete nodes with CONTESTED status).
   - Calibrated framing and balanced attribution formatter ("Historians such as X argue A, whereas Y contends B").

3. Implement VerificationEngine in src/epistemic/engine.py per explorer_3_m3/analysis.md:
   - VerificationEngine class with strategy registry and claim-type policy dispatch mapping ClaimType to mandatory strategies plus dynamic facet detection.
   - verify_claim(claim: ClaimRecord, graph: EvidenceGraph) -> VerificationResult: executes strategies, creates VerificationTraceNode, inserts into EvidenceGraph with EdgeRelation.DERIVES_FROM, links evidence units, and updates ClaimRecord and ClaimNode epistemic_status using the priority decision ladder.
   - verify_dossier(dossier: ResearchDossier, graph: Optional[EvidenceGraph] = None) -> DossierVerificationReport: verifies all claims, cross-claim contradiction checks, evaluates gate outcomes (PASS, WARN, HUMAN_REVIEW, BLOCK), and embeds serialized graph into dossier.evidence_graph.
   - Re-export symbols in src/epistemic/__init__.py.

4. Implement Comprehensive Test Suites:
   - tests/test_verification_engine.py: testing engine initialization, policy dispatch, all 7 strategies, trace nodes in DAG, and verify_dossier.
   - tests/test_historical_policy.py: testing sole web source prohibition, thresholds A/B/C, 8 consensus states classification, event vs interpretation, non-averaging invariant, calibrated framing.

5. Verification:
   Run:
   - pytest tests/test_historical_policy.py -v
   - pytest tests/test_verification_engine.py -v
   - pytest tests/test_evidence_graph.py -v
   - pytest tests/test_contracts.py -v
   - pytest tests/test_state_machine.py -v
   - pytest tests/test_h9_acceptance.py -v
   Confirm 100% pass across all suites with 0 failures, 0 errors, and zero regressions.

6. Documentation:
   Write handoff.md in your working directory following the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method) with full test commands and output logs. Send completion message via send_message.
