# Project: Harness 9 Epistemic Verification Layer

## Architecture
The Epistemic Verification Layer introduces machine-readable evidence graphs, historical scholarship consensus modeling, multi-strategy verification, script & visual consistency checks, deterministic lifecycle state machine gates, and native Hermes runtime tools.

```
[ Research Dossier / Web Sources ]
               │ (untrusted input sanitization)
               ▼
   [ 13-Tier Source Taxonomy ]
               │
               ▼
     [ Evidence Graph DAG ] ◄────────┐ (evidence linking)
               │                     │
               ▼                     │
[ Multi-Strategy Verification Engine ]
  ├─ SOURCE_ENTAILMENT (NLI/Semantics)
  ├─ CROSS_SOURCE_CORROBORATION
  ├─ CONTRADICTION_CHECK
  ├─ QUOTE_CHECK
  ├─ NUMERICAL_CHECK
  ├─ TEMPORAL_CHECK
  └─ HISTORIOGRAPHICAL_CHECK (8 consensus states)
               │
               ▼
[ Post-Script Claim Re-Verification ] ──► Detect drift, quote fabrication, unhedged claims
               │
               ▼
[ Visual & Numerical Integrity ] ───────► Reconcile charts, timelines, counts vs script
               │
               ▼
[ State Machine Verification Gates ]
  ├─ RESEARCH_VERIFICATION Gate
  ├─ SCRIPT_FACT_CHECK Gate
  ├─ VISUAL_FACT_CHECK Gate
  └─ FINAL_EPISTEMIC_QA Gate ───────────► Deterministic BLOCK on publish if failed
               │
               ▼
[ Hermes Model Tools: h9.verify_* ]
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Baseline Epistemic Audit Report | Comprehensive audit of existing scoring and contract gaps at docs/architecture/epistemic-verification-audit.md | M1 | R1 (DONE) |
| 2 | Formal Epistemic Specifications | Deliver docs/epistemic/ specifications (7 docs), update core docs, record ADR-006 | M1 | R1 (DONE) |
| 3 | Extended ClaimRecord Semantics | 11 granular epistemic statuses, evidence links, temporal anchors, verifier metadata in contracts.py | M2 | R2 (DONE) |
| 4 | 13-Tier Source Taxonomy | Authoritative taxonomy from PRIMARY_SOURCE to UNVERIFIED with quality metrics in contracts.py | M2 | R2 (DONE) |
| 5 | Evidence Graph Abstraction | Machine-readable DAG connecting sources, passages, evidence units, claims, scripts, visual nodes in src/epistemic/graph.py | M2 | R2 (DONE) |
| 6 | Circular Import Fix | Lazy import of Pipeline in src/h9_runtime/content.py so tests/test_state_machine.py passes in isolation | M2 | R1 Handover (DONE) |
| 7 | Multi-Strategy Verification Engine | 7 modular verification strategies with claim-type policy dispatch in src/epistemic/engine.py | M3 | R3 (DONE) |
| 8 | Historical Scholarship Policy | Block sole web sources, 8 consensus states, event vs interpretation, preserve contradictions | M3 | R3 (DONE) |
| 9 | Quote & Numerical Verification | Exact quote matching/paraphrase mandate; deterministic numerical dataset to chart pipeline | M3/M4 | R3 (DONE), R4 |
| 10 | Post-Script Claim Re-Verification | Extract claims from script text, audit against Evidence Graph for strengthening/omission in src/epistemic/script_verifier.py | M4 | R4 |
| 11 | Visual Fact-Checking Engine | Audit rendered storyboard elements, timelines, charts, counts against narration in src/epistemic/visual_verifier.py | M4 | R4 |
| 12 | State Machine Verification Gates | 4 hard verification gates (RESEARCH, SCRIPT, VISUAL, FINAL) with PASS/WARN/REVIEW/BLOCK | M5 | R5 |
| 13 | Publication Lock Invariant | Deterministically block publishing when mandatory factual gates fail | M5 | R5 |
| 14 | Native Hermes Verification Tools | 9 registered model tools (h9.extract_claims, h9.verify_claim, etc.) in tools/h9_content_tools.py | M5 | R5 |
| 15 | Untrusted Content Sanitization | Sanitize retrieved web content to prevent prompt injection or authority escalation | M5 | R5 |
| 16 | H9-FactBench Evaluation Suite | 9 benchmark categories with hybrid hermetic offline fixtures + scholarly API connectors | E2E-Track | R6 |
| 17 | Adversarial Verification Suite | tests/test_epistemic_adversarial.py covering false consensus, citation laundering, spoofing | E2E-Track | R6 |
| 18 | Final Acceptance & Forensic Audit | Zero regressions on test_h9_acceptance.py (44/44); docs/architecture/epistemic-verification-final-audit.md | M_Final | R6 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Pre-Audit & Formal Specifications | docs/architecture/epistemic-verification-audit.md, docs/epistemic/*, ADR-006, core docs update | none | DONE |
| M2 | Evidence Graph & Extended Contracts | src/models/contracts.py, src/epistemic/graph.py, 13-tier taxonomy, 11 statuses, 8 consensus states, lazy import fix in content.py | M1 | DONE |
| M3 | Verification Engine & Historical Policy | src/epistemic/engine.py, strategies, policy dispatch, historical scholarship policy | M2 | DONE |
| M4 | Script Re-Verification & Visual Integrity | src/epistemic/script_verifier.py, visual_verifier.py, numerical dataset pipeline | M3 | IN_PROGRESS |
| M5 | State Machine Gates & Hermes Tools | src/orchestrator/state_machine.py, tools/h9_content_tools.py, src/h9_runtime/bridge.py, sanitization | M4 | PLANNED |
| E2E | E2E Testing Track (FactBench & Adversarial) | tests/epistemic/, H9-FactBench (9 categories), tests/test_epistemic_adversarial.py, TEST_READY.md | M1 | PLANNED |
| M_Final | Final Acceptance, Regression & Final Audit | 100% pass across all suites, zero regressions (44/44), docs/architecture/epistemic-verification-final-audit.md | M5, E2E | PLANNED |

## Interface Contracts
### Contracts ↔ Evidence Graph
- `ClaimRecord` references `evidence_node_ids: List[str]`, `epistemic_status: EpistemicStatus`, `consensus_state: ConsensusState`, `source_tier: SourceTier`, `source_quality: SourceQualityMetrics`, `corroboration_set: List[str]`, `temporal_context: TemporalContext`, `verifier_metadata: Dict[str, Any]`.
- `EvidenceGraph.add_source(source: SourceRecord) -> str`
- `EvidenceGraph.add_evidence_unit(unit: EvidenceUnit) -> str`
- `EvidenceGraph.link_claim_to_evidence(claim_id: str, evidence_id: str, relation: EntailmentRelation)`
- `EvidenceGraph.export_dag() -> Dict[str, Any]`
- `EvidenceGraph.from_dag(data: Dict[str, Any]) -> EvidenceGraph`

### Verification Engine ↔ Policy Dispatch
- `VerificationEngine.verify(claim: ClaimRecord, graph: EvidenceGraph) -> VerificationResult`
- `VerificationResult.status: EpistemicStatus`
- `VerificationResult.confidence: float`
- `VerificationResult.contradictions: List[ContradictionRecord]`
- `VerificationResult.explanation: str`

### Script & Visual Verifier ↔ Evidence Graph & Pipeline
- `ScriptVerifier.verify_script(script: ScriptDraft, graph: EvidenceGraph) -> ScriptVerificationReport`
  - Detect strengthened claims (confidence escalated beyond evidence support).
  - Detect altered numbers (numerical values differing from source evidence).
  - Detect omitted uncertainty (epistemic hedging removed in narration).
  - Detect fabricated quotes (strict quote matching or paraphrase mandate).
- `VisualVerifier.verify_visuals(storyboard: Storyboard, graph: EvidenceGraph, script: ScriptDraft) -> VisualVerificationReport`
  - Reconcile timeline dates, chart data points, entity counts against narration & evidence graph.
- `NumericalPipeline.verify_chart_data(dataset: NumericalDataset, chart_config: ChartConfig) -> NumericalVerificationResult`

### State Machine ↔ Verification Gates
- `StateMachine.evaluate_gate(gate_name: str, context: Dict[str, Any]) -> GateOutcome`
- `GateOutcome: PASS | WARN | HUMAN_REVIEW | BLOCK`
- `StateMachine.can_publish() -> bool` (returns False if any mandatory gate is BLOCK or HUMAN_REVIEW)

## Code Layout
- `docs/architecture/epistemic-verification-audit.md` (Baseline pre-audit - completed)
- `docs/architecture/epistemic-verification-final-audit.md` (Final audit)
- `docs/epistemic/` (EPISTEMIC_ARCHITECTURE.md, FACT_CHECKING_SPEC.md, HISTORICAL_SCHOLARSHIP_POLICY.md, EVIDENCE_GRAPH.md, CLAIM_VERIFICATION.md, VISUAL_FACT_CHECKING.md, FACTBENCH.md - completed)
- `docs/adrs/ADR-006-epistemic-verification.md` (completed)
- `src/models/contracts.py` (Extended ClaimRecord, SourceRecord, EpistemicStatus, ConsensusState, SourceTier, EvidenceUnit, etc. - completed)
- `src/h9_runtime/content.py` (Lazy import of Pipeline to avoid circular dependency - completed)
- `src/epistemic/graph.py` (EvidenceGraph abstraction - completed)
- `src/epistemic/historical_policy.py` (Historical scholarship policy - completed)
- `src/epistemic/strategies.py` (7 verification strategies - completed)
- `src/epistemic/engine.py` (VerificationEngine with policy dispatch - completed)
- `src/epistemic/script_verifier.py` (Post-script claim re-verification, quote checking, drift detection)
- `src/epistemic/visual_verifier.py` (Visual fact-checking engine, storyboard reconciliation)
- `src/epistemic/numerical_pipeline.py` (Deterministic numerical dataset to chart pipeline)
- `src/epistemic/sanitization.py` (Untrusted content sanitization)
- `src/orchestrator/state_machine.py` (4 verification gates, gate outcomes, publishing invariants)
- `tools/h9_content_tools.py` & `src/h9_runtime/bridge.py` (9 native Hermes tools)
- `tests/epistemic/` & `tests/test_epistemic_adversarial.py` (H9-FactBench & adversarial tests)
