# Execution Plan — Epistemic Verification Layer

## Strategy Overview
Dual-track architecture:
- Track 1 (Implementation): Iterative milestone delivery (M2 -> M3 -> M4 -> M5) with rigorous Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate cycle.
- Track 2 (E2E Testing Track): Requirement-driven H9-FactBench across 9 categories + adversarial test suite -> publishes TEST_READY.md.
- Convergence (Final Milestone): Phase 1 (100% pass across all tests) + Phase 2 (Adversarial hardening) + Final forensic audit report.

## Step-by-Step Milestones

### Milestone 2: Evidence Graph & Extended Claim Contracts (R2)
1. Dispatch 3 Explorers:
   - Explorer 1: Examine existing `src/models/contracts.py`, existing tests (`tests/test_contracts.py`), and spec `docs/epistemic/EVIDENCE_GRAPH.md`.
   - Explorer 2: Examine `src/h9_runtime/content.py:37` circular import issue and its resolution (lazy import in `run_full_production`), testing isolated execution of `tests/test_state_machine.py`.
   - Explorer 3: Design concrete class structures for `EvidenceGraph` in `src/epistemic/graph.py`, 13-tier `SourceTier` taxonomy, 11 `EpistemicStatus` values, 8 `ConsensusState` values, and serialization/deserialization.
2. Aggregate Explorer reports into unified implementation prompt for Worker M2.
3. Dispatch Worker M2 to implement extended `ClaimRecord`, `EvidenceGraph`, enums, and fix the lazy import in `content.py`. Worker runs unit tests (`test_contracts.py`, `test_state_machine.py`, `test_h9_acceptance.py`).
4. Dispatch 2 Reviewers, 2 Challengers, and 1 Forensic Auditor.
5. Gate Check: Strict AND evaluation in `GATE_STATUS.md`.

### Milestone 3: Multi-Strategy Verification Engine & Policy Dispatch (R3)
1. Dispatch Explorers for `src/epistemic/engine.py`, 7 verification strategies, historical scholarship policy (blocking sole web sources, 8 consensus states, event vs interpretation, preserving contradictions), quote verifier, and numerical checks.
2. Worker M3 implements verification engine, strategies, and policy dispatch.
3. Reviewers, Challengers, Auditor, Gate.

### Milestone 4: Multi-Stage Pipeline & Visual/Numerical Integrity (R4)
1. Dispatch Explorers for post-script claim re-verification (`src/epistemic/script_verifier.py`), visual fact-checking (`src/epistemic/visual_verifier.py`), and deterministic numerical pipeline (`src/epistemic/numerical_pipeline.py`).
2. Worker M4 implements script & visual verifiers.
3. Reviewers, Challengers, Auditor, Gate.

### Milestone 5: Lifecycle State Machine Gates & Hermes Native Tools (R5)
1. Dispatch Explorers for state machine gates (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`), publication blocking, untrusted web sanitization, and 9 Hermes tools (`tools/h9_content_tools.py`, `src/h9_runtime/bridge.py`).
2. Worker M5 implements state machine gates, Hermes tools, and sanitization.
3. Reviewers, Challengers, Auditor, Gate.

### Parallel Track: E2E Testing Track (R6)
1. Dispatch Test Writer to build H9-FactBench across 9 categories + `tests/test_epistemic_adversarial.py`.
2. Publish `TEST_READY.md`.

### Final Milestone: 100% Verification, Zero Regression & Final Audit (R6)
1. Run full test suite including `tests/test_h9_acceptance.py` (44/44) and new epistemic tests.
2. Author `docs/architecture/epistemic-verification-final-audit.md`.
3. Gate check and final reporting back to Sentinel.
