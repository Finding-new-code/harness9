## 2026-09-14T00:50:09Z

You are worker_m2. Your working directory is g:\Finding-new-code\harness9\.agents\worker_m2.
Update your progress.md regularly.

MANDATORY FIRST STEP: Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work.
Also read:
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\PROJECT.md
- g:\Finding-new-code\harness9\.agents\explorer_1_m2\analysis.md
- g:\Finding-new-code\harness9\.agents\explorer_1_m2\handoff.md
- g:\Finding-new-code\harness9\.agents\explorer_2_m2\analysis.md
- g:\Finding-new-code\harness9\.agents\explorer_2_m2\handoff.md
- g:\Finding-new-code\harness9\.agents\explorer_3_m2\analysis.md
- g:\Finding-new-code\harness9\.agents\explorer_3_m2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE FILE OWNERSHIP:
You have exclusive write access to:
- src/models/contracts.py
- src/models/__init__.py
- src/h9_runtime/content.py
- src/epistemic/__init__.py
- src/epistemic/graph.py
- tests/test_evidence_graph.py

TASKS TO EXECUTE:
1. Fix circular import in src/h9_runtime/content.py:
   Move imports of Pipeline, EditorialEngine, ResearchEngine, and ProductionStateMachine to be lazy inside their respective methods (run_full_production, create_editorial_angle, execute_research, etc.) as detailed in explorer_2_m2/analysis.md.
   Verify that running pytest tests/test_state_machine.py in isolation passes completely (10/10).

2. Implement Extended Epistemic Contracts in src/models/contracts.py and src/models/__init__.py:
   - EpistemicStatus (11 statuses: verified, supported, partially_supported, contested, contradicted, unsupported, unverifiable, outdated, misleading, opinion, prediction).
   - SourceTier (13 tiers: PRIMARY_SOURCE (1) to UNVERIFIED (13)) with DEFAULT_TIER_WEIGHTS (1.00 down to 0.00).
   - ConsensusState (8 consensus states: STRONG_CONSENSUS, BROAD_CONSENSUS, MAJORITY_INTERPRETATION, MINORITY_INTERPRETATION, ACTIVE_DEBATE, CONTESTED, UNRESOLVED, INSUFFICIENT_LITERATURE).
   - Supporting models: SourceQualityMetrics, TemporalContext, QuoteExactness, EvidenceUnitLink, ClaimType.
   - Extend ClaimRecord with: evidence_node_ids, epistemic_status, consensus_state, source_tier, source_quality, corroboration_set, temporal_context, verifier_metadata, quote_exactness, @property def verification_status. Ensure all new fields have safe defaults so existing callers and tests/test_contracts.py continue to pass 100%.
   - Extend SourceRecord and ResearchDossier per explorer_1_m2/analysis.md.
   - Re-export new symbols in src/models/__init__.py.

3. Implement Evidence Graph Abstraction in src/epistemic/graph.py:
   - Create package src/epistemic/__init__.py.
   - Implement GraphNode(H9BaseModel) and 8 node types: SourceNode, PassageNode, EvidenceUnitNode, ClaimNode, VerificationTraceNode, SceneNode, ScriptSentenceNode, VisualElementNode.
   - Implement EdgeRelation enum (6 canonical relations: ENTAILMENT, CONTRADICTION, CORROBORATION, MENTIONS, DERIVES_FROM, VISUAL_DEPICTION + aliases) and GraphEdge(H9BaseModel).
   - Implement EvidenceGraph(H9BaseModel) with:
     - Cycle prevention (would_create_cycle, CycleDetectedError).
     - Deterministic topological sort via Kahn's algorithm with alphanumeric tie-breaking.
     - Query methods (get_claims_by_status, get_contested_claims, get_claims_by_type, get_nodes_by_type, get_incoming_edges, get_outgoing_edges).
     - Lineage reconstruction (trace_lineage returning ProvenanceChain).
     - Multi-path confidence calculation with hop decay, source tier weights, and contradiction penalties.
     - Serialization (to_dict, from_dict, to_json, from_json, export_jsonld, from_dossier).

4. Implement Comprehensive Test Suite in tests/test_evidence_graph.py:
   - Implement 10 comprehensive test classes covering node models, edge relations, cycle prevention & DAG invariants, deterministic topological sort, queries, lineage traversal, confidence calculation, serialization roundtrips, dossier conversion, and graph mutations.

5. Verification:
   Run the following tests:
   - pytest tests/test_state_machine.py -v
   - pytest tests/test_contracts.py -v
   - pytest tests/test_evidence_graph.py -v
   - pytest tests/test_h9_acceptance.py -v
   Confirm all suites pass with 0 failures and 0 errors.

6. Documentation:
   Write handoff.md in your working directory following the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method) including exact test commands and outputs. Send completion message via send_message.
