# Dispatch Log

## 2026-09-13T16:45:00Z

You are the Project Orchestrator for the Harness 9 Epistemic Verification Layer project.

Working directory: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7
Workspace root: g:\Finding-new-code\harness9
Target branch: dev
Authoritative Request: g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (entry timestamp ## 2026-09-13T16:44:00Z)

Your Mission:
Design, implement, integrate, and verify the Harness 9 Epistemic Verification Layer across the research, claim, production contract, editorial, script, visual rendering, and lifecycle state machine systems on branch dev in g:\Finding-new-code\harness9. Enable Harness 9 to ground claims in machine-readable evidence graphs, enforce rigorous historical scholarship and consensus modeling, verify script and visual consistency, block publication of unsupported/contradicted claims, and expose verification capabilities natively through the Hermes runtime.

Key Requirements:
1. R1: Comprehensive baseline audit report at docs/architecture/epistemic-verification-audit.md before core modifications begin. Deliver formal specs under docs/epistemic/ (EPISTEMIC_ARCHITECTURE.md, FACT_CHECKING_SPEC.md, HISTORICAL_SCHOLARSHIP_POLICY.md, EVIDENCE_GRAPH.md, CLAIM_VERIFICATION.md, VISUAL_FACT_CHECKING.md, FACTBENCH.md), update core docs (DATA_MODEL.md, WORKFLOW_SPEC.md, SECURITY_MODEL.md, CONTENTBENCH.md), and record docs/adrs/ADR-006-epistemic-verification.md.
2. R2: Evidence Graph & Extended Claim Contracts: Extend ClaimRecord in src/models/contracts.py with executable semantics (granular epistemic statuses, structured source evidence links, source quality metrics, corroboration sets, temporal context, verifier metadata). Implement dedicated machine-readable Evidence Graph abstraction. Establish 13-tier source taxonomy (PRIMARY_SOURCE to UNVERIFIED).
3. R3: Multi-Strategy Verification Engine & Policy Dispatch: Modular explainable strategies (SOURCE_ENTAILMENT, CROSS_SOURCE_CORROBORATION, CONTRADICTION_CHECK, QUOTE_CHECK, NUMERICAL_CHECK, TEMPORAL_CHECK, HISTORIOGRAPHICAL_CHECK) with claim-type-specific dispatch. Enforce hard Historical Scholarship Policy (no sole/popular web sources for historical facts/interpretations, consensus states, event vs. scholarly interpretation, calibrated consensus language, no averaging contradictions).
4. R4: Multi-Stage Pipeline & Visual/Numerical Integrity: Post-script claim extraction and re-verification against evidence graph. Visual fact-checking verifying rendered storyboard elements, timelines, charts, counts against narration. Deterministic numerical data pipeline from dataset to chart rendering.
5. R5: Lifecycle State Machine Gates, Hermes Runtime & Security Boundaries: Integrate hard verification gates (RESEARCH_VERIFICATION, SCRIPT_FACT_CHECK, VISUAL_FACT_CHECK, FINAL_EPISTEMIC_QA) with deterministic outcomes (PASS, WARN, HUMAN_REVIEW, BLOCK). Block publishing when mandatory factual gates fail. Expose native Hermes model tools (h9.extract_claims, h9.verify_claim, h9.verify_script, h9.verify_quote, h9.verify_numbers, h9.analyze_historical_consensus, h9.detect_contradictions, h9.verify_visual_claims, h9.epistemic_gate). Treat retrieved web content as untrusted input.
6. R6: H9-FactBench across 9 categories (general, numerical, quotes, scientific, current-event, historical facts, contested historical interpretations, contradictory sources, visual consistency) with hybrid hermetic offline fixtures + live scholarly API connectors. Adversarial suite tests/test_epistemic_adversarial.py. Zero regressions across existing test suites (tests/test_h9_acceptance.py 44/44, unit & integration). Author final forensic audit report at docs/architecture/epistemic-verification-final-audit.md.

Protocol:
- Initialize BRIEFING.md, plan.md, and progress.md in your working directory.
- Maintain progress.md regularly with clear status and milestones.
- Decompose into parallel/sequential specialist milestones and subagents.
- Follow adversarial review and verification standards.
- When all requirements and acceptance criteria are satisfied and verified, report completion back to Sentinel with evidence.
