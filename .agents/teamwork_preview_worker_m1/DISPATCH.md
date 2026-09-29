## 2026-09-13T17:02:50Z
You are Worker Milestone 1 for the Harness 9 Epistemic Verification Layer project.
Your working directory is: g:\Finding-new-code\harness9\.agents\teamwork_preview_worker_m1

MANDATORY FIRST STEP: Read the authoritative request file before starting any work:
g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (specifically entry ## 2026-09-13T16:44:00Z)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Input Context & Survey Findings (Read these thoroughly):
1. `g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7\PROJECT.md`
2. `g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_survey_1\handoff.md` (Contracts, Models, Evidence Graph spec, 13-Tier Taxonomy)
3. `g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_survey_2\handoff.md` (State Machine Gates, Publishing Invariant, 9 Hermes Model Tools, Security)
4. `g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_survey_3\handoff.md` (Verification Strategies, Historical Scholarship Policy, Visual/Numerical Pipeline, FactBench)

Exclusive Write Ownership for this Milestone:
- `docs/architecture/epistemic-verification-audit.md` (Comprehensive baseline pre-implementation audit report)
- `docs/epistemic/EPISTEMIC_ARCHITECTURE.md` (Overall epistemic architecture, decoupling verification from retrieval, component interaction)
- `docs/epistemic/FACT_CHECKING_SPEC.md` (Fact-checking specification, claim types, verification pipelines)
- `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md` (Strict rules: no sole web sources for historical facts/interpretations, 8 consensus states, event vs interpretation, non-averaging contradictions)
- `docs/epistemic/EVIDENCE_GRAPH.md` (Evidence graph DAG data model, nodes, edges, provenance, reconstruction)
- `docs/epistemic/CLAIM_VERIFICATION.md` (Verification strategies, NLI, corroboration, quote checking, numerical checking, temporal checking)
- `docs/epistemic/VISUAL_FACT_CHECKING.md` (Visual fact-checking specification, storyboard element verification, deterministic numerical pipeline)
- `docs/epistemic/FACTBENCH.md` (H9-FactBench benchmark specification across 9 categories, metrics, hybrid offline/live connectors)
- Updates to existing core docs:
  - `docs/DATA_MODEL.md` (Add ClaimRecord extensions, EvidenceGraph, SourceTier, ConsensusState, EpistemicStatus)
  - `docs/WORKFLOW_SPEC.md` (Add the 4 verification gates and publishing lock invariants)
  - `docs/SECURITY_MODEL.md` (Add untrusted web content sanitization and prompt injection defenses)
  - `docs/CONTENTBENCH.md` (Incorporate H9-FactBench into the evaluation architecture)
- `docs/adrs/ADR-006-epistemic-verification.md` (Architecture Decision Record ADR-006: Epistemic Verification Layer)

Task Requirements:
1. Author the baseline audit report `docs/architecture/epistemic-verification-audit.md` capturing all findings from the Survey Explorers (heuristic scoring flaws in `scoring.py`, missing epistemic statuses, lack of gates in `state_machine.py`, lack of factual QA, lack of dataset lineage for charts).
2. Create the directory `docs/epistemic/` and author all 7 formal specifications in full, rigorous detail (complete equations, schemas, states, flows, tables, and invariants).
3. Update existing docs (`DATA_MODEL.md`, `WORKFLOW_SPEC.md`, `SECURITY_MODEL.md`, `CONTENTBENCH.md`) to integrate the Epistemic Verification Layer cleanly without breaking existing references.
4. Author `docs/adrs/ADR-006-epistemic-verification.md` in standard ADR format (Status: Accepted, Context, Decision, Consequences, Compliance).
5. Verify all markdown files are well-formatted, consistent, and cite the actual code paths.
