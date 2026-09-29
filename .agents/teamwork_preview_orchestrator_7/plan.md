# Epistemic Verification Layer — Project Execution Plan

## 1. Overview & Objective
Design, implement, integrate, and verify the Harness 9 Epistemic Verification Layer across the research, claim, production contract, editorial, script, visual rendering, and lifecycle state machine systems on branch `dev` in `g:\Finding-new-code\harness9`.

## 2. Phase 0: Survey & Pre-Implementation Audit (R1)
- **Explorer 1 (Contracts, Research & Editorial)**: Investigate `src/models/contracts.py`, `src/models/ir.py`, `src/research/`, `src/editorial/`, and current claim modeling.
- **Explorer 2 (State Machine, Gates, Runtime & Security)**: Investigate `src/orchestrator/state_machine.py`, `src/h9_runtime/`, `tools/h9_content_tools.py`, `src/security/tokens.py`, and sandbox execution.
- **Explorer 3 (Tests, Acceptance Suite & ContentBench)**: Investigate `tests/test_h9_acceptance.py`, `tests/test_state_machine.py`, `tests/test_editorial.py`, `ContentBench`, and existing test harnesses.
- **Synthesis & Baseline Deliverables**:
  - Synthesize Feature Inventory in `PROJECT.md`.
  - Author baseline audit report at `docs/architecture/epistemic-verification-audit.md`.
  - Author formal specifications under `docs/epistemic/` (`EPISTEMIC_ARCHITECTURE.md`, `FACT_CHECKING_SPEC.md`, `HISTORICAL_SCHOLARSHIP_POLICY.md`, `EVIDENCE_GRAPH.md`, `CLAIM_VERIFICATION.md`, `VISUAL_FACT_CHECKING.md`, `FACTBENCH.md`).
  - Update core documentation (`DATA_MODEL.md`, `WORKFLOW_SPEC.md`, `SECURITY_MODEL.md`, `CONTENTBENCH.md`).
  - Record Architecture Decision Record `docs/adrs/ADR-006-epistemic-verification.md`.

## 3. Parallel Tracks Execution

### Track 1: Implementation Track
- **Milestone 1: Evidence Graph & Extended Claim Contracts (R2)**
  - Extend `ClaimRecord` in `src/models/contracts.py` with granular epistemic statuses, source evidence links, source quality metrics, corroboration sets, temporal context, verifier metadata.
  - Implement dedicated machine-readable Evidence Graph abstraction connecting sources, passages, evidence units, claims, verification traces, script sentences, scenes, and visual elements.
  - Establish 13-tier source taxonomy from `PRIMARY_SOURCE` to `UNVERIFIED`.
- **Milestone 2: Multi-Strategy Verification Engine & Policy Dispatch (R3)**
  - Modular explainable strategies: `SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK`, `QUOTE_CHECK`, `NUMERICAL_CHECK`, `TEMPORAL_CHECK`, `HISTORIOGRAPHICAL_CHECK`.
  - Claim-type-specific policy dispatch.
  - Historical Scholarship Policy: forbid sole/popular web sources for historical facts/interpretations; explicit consensus states (`STRONG_CONSENSUS` to `INSUFFICIENT_LITERATURE`); differentiate documented events from interpretations; calibrate consensus language without averaging contradictions.
- **Milestone 3: Multi-Stage Pipeline & Visual/Numerical Integrity (R4)**
  - Post-script claim extraction and re-verification against evidence graph (strengthened claims, altered numbers, omitted uncertainty, quote verification/paraphrase enforcement).
  - Visual fact-checking verifying rendered storyboard elements, timelines, charts, counts against script narration.
  - Deterministic numerical data pipeline from dataset to chart rendering.
- **Milestone 4: Lifecycle State Machine Gates, Hermes Runtime & Security Boundaries (R5)**
  - Hard verification gates in production lifecycle state machine (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`) with outcomes `PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`.
  - Mandatory publishing invariant: block publishing when factual gates fail.
  - Expose native Hermes model tools: `h9.extract_claims`, `h9.verify_claim`, `h9.verify_script`, `h9.verify_quote`, `h9.verify_numbers`, `h9.analyze_historical_consensus`, `h9.detect_contradictions`, `h9.verify_visual_claims`, `h9.epistemic_gate`.
  - Untrusted content sanitization (prevent prompt injection or authority escalation).

### Track 2: E2E Testing Track (R6)
- **E2E Testing Track Orchestrator**:
  - Establish `TEST_INFRA.md`.
  - Build `H9-FactBench` across 9 categories (general, numerical, quotes, scientific, current-event, historical facts, contested historical interpretations, contradictory sources, visual consistency).
  - Provision hybrid hermetic offline fixtures + live scholarly API connectors.
  - Implement adversarial test suite `tests/test_epistemic_adversarial.py`.
  - Publish `TEST_READY.md`.

## 4. Final Milestone & Acceptance Verification (R6)
- Phase 1: 100% pass across all FactBench, adversarial, acceptance (`tests/test_h9_acceptance.py` 44/44), unit, and integration suites.
- Phase 2: Adversarial coverage hardening (Tier 5).
- Final forensic audit report at `docs/architecture/epistemic-verification-final-audit.md`.
- Comprehensive handoff to Sentinel.
