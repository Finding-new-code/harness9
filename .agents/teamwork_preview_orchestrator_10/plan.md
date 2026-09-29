# Master Orchestration Plan — Epistemic Verification Layer (Generation 10)

## Mission
Drive the complete implementation, integration, verification, and forensic audit of the Harness 9 Epistemic Verification Layer on branch `dev` in `g:\Finding-new-code\harness9`, covering R4 gate verification, R5 (State Machine Gates, Hermes Runtime Tools & Security Boundaries), R6 (H9-FactBench Evaluation Suite & Adversarial Testing), and Final Forensic Audit.

## Work Breakdown & Phasing

### Phase 1: Milestone 4 (R4) Gate Review & Integrity Audit
- Current State: Over 107 M4 tests passing across `test_script_verifier.py`, `test_script_verifier_adversarial.py`, `test_visual_verifier.py`, `test_numerical_pipeline.py`, and `test_m4_adversarial_challenger2.py`.
- Action:
  1. Dispatch 2 Reviewers independently (`reviewer_1_m4_g10` for script verifier & graph sync; `reviewer_2_m4_g10` for visual verifier & numerical pipeline).
  2. Dispatch 2 Challengers (`challenger_1_m4_g10` for script drift stress testing; `challenger_2_m4_g10` for visual/numerical invariant verification).
  3. Dispatch 1 Forensic Auditor (`auditor_m4_g10`) to confirm zero hardcoded strings/facades/cheats and genuine implementation.
  4. Collect reports, evaluate Gate criteria in `GATE_STATUS.md`.
  5. Upon unanimous approval + CLEAN audit, mark Milestone 4 DONE.

### Phase 2: Milestone 5 (R5) — State Machine Gates, Hermes Runtime & Security Boundaries
- Scope:
  1. Hard verification gates in production lifecycle state machine (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`) supporting deterministic quality outcomes (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`).
  2. Invariant: Production cannot publish while mandatory factual gates fail (`BLOCK` or `HUMAN_REVIEW`).
  3. Native Hermes model tools in `tools/h9_content_tools.py` and bridge integration in `src/h9_runtime/bridge.py`:
     - `h9.extract_claims`
     - `h9.verify_claim`
     - `h9.verify_script`
     - `h9.verify_quote`
     - `h9.verify_numbers`
     - `h9.analyze_historical_consensus`
     - `h9.detect_contradictions`
     - `h9.verify_visual_claims`
     - `h9.epistemic_gate`
  4. Untrusted content sanitization in `src/epistemic/sanitization.py` preventing prompt injection and authority escalation.
- Action:
  1. Dispatch 3 Explorers (Spec Miner / Explorers) to analyze current state machine, bridge, and tools.
  2. Synthesize findings, dispatch Worker with clear write ownership and integrity warnings.
  3. Dispatch 2 Reviewers, 2 Challengers, and 1 Forensic Auditor.
  4. Gate check in `GATE_STATUS.md`. Upon passing, mark M5 DONE.

### Phase 3: Milestone 6 (R6) & E2E Testing Track — H9-FactBench & Adversarial Verification
- Scope:
  1. H9-FactBench benchmark suite across 9 distinct categories:
     - general, numerical, quotes, scientific, current-event, historical facts, contested historical interpretations, contradictory sources, visual consistency.
     - hybrid hermetic offline test fixtures for deterministic CI/CD + live scholarly API connectors.
  2. Adversarial test suite `tests/test_epistemic_adversarial.py` (false consensus, citation laundering, authority spoofing, prompt injection).
  3. Verification of zero regressions across all test suites, including `tests/test_h9_acceptance.py` (44/44).
- Action:
  1. Dispatch Test Writer / Workers to build FactBench and adversarial suites.
  2. Execute tests, collect multi-dimensional metrics, verify 100% pass rate.
  3. Gate review and forensic audit.

### Phase 4: Final Milestone & Comprehensive Final Audit
- Scope:
  1. Zero regressions across entire repository (`tests/test_h9_acceptance.py`, all unit, integration, and epistemic test suites).
  2. Author final forensic audit report at `docs/architecture/epistemic-verification-final-audit.md`.
  3. Verify code layout, documentation completeness, and ADR-006 alignment.
  4. Final synthesis and handoff report back to Sentinel.
