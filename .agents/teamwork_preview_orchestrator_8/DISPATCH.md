# Dispatch Log

## 2026-09-14T00:31:00Z

You are the Project Orchestrator (Generation 8) for the Harness 9 Epistemic Verification Layer project.

Working directory: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8
Workspace root: g:\Finding-new-code\harness9
Target branch: dev
Authoritative Request: g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (entry timestamp ## 2026-09-13T16:44:00Z)

Prior Generation State Handover:
1. R1 Pre-Implementation Audit & Epistemic Architectural Specifications:
   - COMPLETED & COMMITTED: Baseline audit at docs/architecture/epistemic-verification-audit.md, 7 formal specs under docs/epistemic/ (EPISTEMIC_ARCHITECTURE.md, FACT_CHECKING_SPEC.md, HISTORICAL_SCHOLARSHIP_POLICY.md, EVIDENCE_GRAPH.md, CLAIM_VERIFICATION.md, VISUAL_FACT_CHECKING.md, FACTBENCH.md), core doc updates (docs/DATA_MODEL.md, docs/WORKFLOW_SPEC.md, docs/SECURITY_MODEL.md, docs/CONTENTBENCH.md), and docs/adrs/ADR-006-epistemic-verification.md.
   - Note on circular import remediation: In src/h9_runtime/content.py, make sure 'from src.orchestrator.pipeline import Pipeline' is imported lazily inside run_full_production() rather than at module top level, so tests/test_state_machine.py passes in isolation.

Remaining Scope to Execute & Verify (R2 through R6):
2. R2: Evidence Graph & Extended Claim Contracts:
   - Extend ClaimRecord in src/models/contracts.py with executable semantics (granular epistemic statuses: verified, supported, partially_supported, contested, contradicted, unsupported, unverifiable, outdated, misleading, opinion, prediction; structured source evidence links, source quality metrics, corroboration sets, temporal context, verifier metadata).
   - Implement dedicated machine-readable Evidence Graph abstraction connecting sources, passages, evidence units, claims, verification traces, script sentences, scenes, and visual elements.
   - Establish 13-tier source taxonomy (PRIMARY_SOURCE to UNVERIFIED).
3. R3: Multi-Strategy Verification Engine & Policy Dispatch:
   - Implement modular, explainable verification strategies (SOURCE_ENTAILMENT, CROSS_SOURCE_CORROBORATION, CONTRADICTION_CHECK, QUOTE_CHECK, NUMERICAL_CHECK, TEMPORAL_CHECK, HISTORIOGRAPHICAL_CHECK).
   - Claim-type-specific policy dispatch (scientific, numerical, quote, current-event, technical, historical).
   - Historical Scholarship Policy: forbid single-source or popular web summaries from establishing historical facts or interpretations; explicitly model 8 consensus states (STRONG_CONSENSUS to INSUFFICIENT_LITERATURE); differentiate documented events from scholarly/causal interpretations; calibrate consensus language in script generation without ever averaging contradictions away.
4. R4: Multi-Stage Pipeline & Visual/Numerical Integrity:
   - Post-script claim extraction and re-verification comparing script claims against evidence graph to detect strengthened claims, altered numbers, omitted uncertainty, fabricated quotes (strict quote matching or paraphrase mandate).
   - Visual fact-checking verifying rendered storyboard elements, timelines, charts, and counts against script narration.
   - Deterministic numerical data pipeline from dataset to chart rendering.
5. R5: Lifecycle State Machine Gates, Hermes Runtime & Security Boundaries:
   - Integrate hard verification gates into production lifecycle state machine (RESEARCH_VERIFICATION, SCRIPT_FACT_CHECK, VISUAL_FACT_CHECK, FINAL_EPISTEMIC_QA) supporting deterministic quality outcomes (PASS, WARN, HUMAN_REVIEW, BLOCK). Block publishing when mandatory factual gates fail.
   - Expose verification capabilities as native Hermes model tools (h9.extract_claims, h9.verify_claim, h9.verify_script, h9.verify_quote, h9.verify_numbers, h9.analyze_historical_consensus, h9.detect_contradictions, h9.verify_visual_claims, h9.epistemic_gate).
   - Sanitize retrieved web content as untrusted input to prevent prompt injection or authority escalation.
6. R6: Evaluation Benchmark (H9-FactBench), Adversarial Testing & Final Audit:
   - Build H9-FactBench evaluation suite across 9 distinct categories with hybrid hermetic offline fixtures + live scholarly API connectors.
   - Adversarial test suite tests/test_epistemic_adversarial.py (false consensus, citation laundering, authority spoofing, prompt injection).
   - Ensure zero regressions across existing test suites (tests/test_h9_acceptance.py 44/44, unit and integration suites).
   - Author final forensic audit report at docs/architecture/epistemic-verification-final-audit.md.

Protocol:
- Initialize BRIEFING.md, plan.md, and progress.md in your working directory.
- Update progress.md regularly with status and milestones.
- Dispatch to specialist subagents (workers, reviewers, challengers, auditors).
- When all requirements and acceptance criteria are satisfied and verified, report completion back to Sentinel with full evidence.
