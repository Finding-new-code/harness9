# BRIEFING — 2026-09-13T19:06:30Z

## Mission
Design the dedicated machine-readable Evidence Graph abstraction in src/epistemic/graph.py and test specifications for tests/test_evidence_graph.py.

## 🔒 My Identity
- Archetype: explorer
- Roles: read-only investigation, architectural design, synthesis
- Working directory: g:\Finding-new-code\harness9\.agents\explorer_3_m2
- Original parent: ba190775-5480-43b0-a934-7fd1b7ba9b5b
- Milestone: M2 - Evidence Graph Abstraction

## 🔒 Key Constraints
- Read-only investigation — do NOT implement or modify source code directly
- Output findings and implementation recommendation to analysis.md and handoff.md in working directory
- Communicate via send_message to caller agent

## Current Parent
- Conversation ID: ba190775-5480-43b0-a934-7fd1b7ba9b5b
- Updated: 2026-09-13T19:06:30Z

## Investigation State
- **Explored paths**: `ORIGINAL_REQUEST.md`, `PROJECT.md`, `docs/epistemic/EVIDENCE_GRAPH.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/epistemic/FACT_CHECKING_SPEC.md`, `docs/DATA_MODEL.md`, `src/models/contracts.py`, `src/models/ir.py`, `src/h9_runtime/content.py`, `scripts/verify_epistemic_specs.py`, `tests/test_contracts.py`.
- **Key findings**:
  - Node taxonomy encompasses 8 distinct types across 6 layers: SourceNode, PassageNode, EvidenceUnitNode, ClaimNode, VerificationTraceNode, SceneNode, ScriptSentenceNode, VisualElementNode.
  - Edge taxonomy encompasses 6 canonical relations: Entailment, Contradiction, Corroboration, Mentions, DerivesFrom, VisualDepiction (with architectural aliases for backward compatibility).
  - DAG invariants require pre-insertion cycle prevention (`would_create_cycle`), self-loop rejection, deterministic topological sort with alphanumeric tie-breaking for prompt caching stability, and non-averaging contradiction handling.
  - Lineage reconstruction provides end-to-end provenance traces (`ProvenanceChain`) from script sentences/visual charts back to root sources.
  - Confidence calculation integrates series chain decay, bottleneck min-cut, parallel independent corroboration (Noisy-OR), 13-tier source weighting, and contradiction penalty degradation.
  - Serialization supports dict, formatted JSON, and W3C JSON-LD.
- **Unexplored areas**: None. Design and test case specifications are complete.

## Key Decisions Made
- Designed Pydantic v2 `GraphNode` base class inheriting from `H9BaseModel` for all 8 node types.
- Designed `GraphEdge` model with `EdgeRelation` enum and explicit support for both canonical relations and architectural aliases.
- Formulated deterministic Kahn's topological sort with sorted tie-breaking.
- Formulated rigorous multi-path Noisy-OR confidence calculation algorithm.
- Specified 10 comprehensive test classes for `tests/test_evidence_graph.py`.

## Artifact Index
- g:\Finding-new-code\harness9\.agents\explorer_3_m2\analysis.md — Comprehensive architectural analysis, Python class blueprints, and test suite design
- g:\Finding-new-code\harness9\.agents\explorer_3_m2\handoff.md — 5-component handoff report
- g:\Finding-new-code\harness9\.agents\explorer_3_m2\progress.md — Liveness heartbeat and task checklist
- g:\Finding-new-code\harness9\.agents\explorer_3_m2\DISPATCH.md — Stored dispatch instruction
