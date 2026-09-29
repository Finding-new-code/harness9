# Plan — Harness 9 Epistemic Verification Layer (Generation 9)

## Overview
Generation 9 executes the remaining scope (R4, R5, R6) building upon the completed M1 (Specs & Pre-Audit), M2 (Contracts & Evidence Graph), and M3 (Verification Engine & Historical Policy).

## Milestones & Execution Stages

### Stage 1: Milestone 4 (R4) — Multi-Stage Pipeline & Visual/Numerical Integrity
- **Objective**:
  1. Post-script claim extraction and re-verification comparing script claims against evidence graph to detect:
     - Strengthened claims (confidence escalated beyond evidence support)
     - Altered numbers (numerical drift)
     - Omitted uncertainty (loss of epistemic hedging)
     - Fabricated quotes (strict quote matching or paraphrase mandate)
  2. Visual fact-checking engine verifying rendered storyboard elements, timelines, charts, and counts against script narration.
  3. Deterministic numerical data pipeline from dataset to chart rendering.
- **Workflow**:
  - Step 1: Dispatch 3 parallel Explorers (`explorer_1_m4`, `explorer_2_m4`, `explorer_3_m4`) to investigate existing script/visual structures, specs in `docs/epistemic/`, and design architecture for `src/epistemic/script_verifier.py`, `src/epistemic/visual_verifier.py`, and `src/epistemic/numerical_pipeline.py`.
  - Step 2: Synthesize findings and dispatch `worker_m4` to implement.
  - Step 3: Dispatch Reviewers (`reviewer_1_m4`, `reviewer_2_m4`), Challengers (`challenger_1_m4`, `challenger_2_m4`), and Forensic Auditor (`auditor_m4`).
  - Step 4: Gate evaluation -> Milestone 4 completion.

### Stage 2: Milestone 5 (R5) — Lifecycle State Machine Gates, Hermes Runtime & Security Boundaries
- **Objective**:
  1. Integrate 4 hard verification gates into production lifecycle state machine (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`) supporting deterministic quality outcomes (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`). Block publishing when mandatory factual gates fail.
  2. Expose verification capabilities as native Hermes model tools (`h9.extract_claims`, `h9.verify_claim`, `h9.verify_script`, `h9.verify_quote`, `h9.verify_numbers`, `h9.analyze_historical_consensus`, `h9.detect_contradictions`, `h9.verify_visual_claims`, `h9.epistemic_gate`).
  3. Untrusted content sanitization (`src/epistemic/sanitization.py`) protecting against prompt injection and authority escalation.
- **Workflow**:
  - Explorers -> Worker -> Reviewers + Challengers + Auditor -> Gate evaluation.

### Stage 3: Milestone 6 / E2E Track (R6) — Evaluation Benchmark (H9-FactBench), Adversarial Testing & Final Audit
- **Objective**:
  1. Build H9-FactBench evaluation suite across 9 distinct categories with hybrid hermetic offline fixtures + live scholarly API connectors.
  2. Adversarial test suite `tests/test_epistemic_adversarial.py` (false consensus, citation laundering, authority spoofing, prompt injection).
  3. Ensure 100% test pass and zero regressions across existing test suites (`tests/test_h9_acceptance.py` 44/44, unit & integration suites).
  4. Author final forensic audit report at `docs/architecture/epistemic-verification-final-audit.md`.
- **Workflow**:
  - E2E Test Writers / Workers -> Reviewers + Challengers + Victory Auditor -> Gate evaluation -> Final completion report to Sentinel.
