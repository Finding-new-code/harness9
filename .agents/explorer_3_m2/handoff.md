# Handoff Report: Evidence Graph Abstraction Design (`src/epistemic/graph.py`)

**Agent ID:** `explorer_3_m2`  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\explorer_3_m2`  
**Milestone:** M2 — Evidence Graph & Extended Contracts  
**Handoff Type:** Hard  

---

## 1. Observation

1. **Context & Requirement Files**:
   - `ORIGINAL_REQUEST.md` (Lines 224–226): Mandates implementing a *"dedicated, machine-readable Evidence Graph abstraction connecting sources, passages, evidence units, claims, verification traces, script sentences, scenes, and visual elements"*.
   - User Dispatch: Explicitly specifies the 8 node types (`Sources`, `Passages`, `Evidence Units`, `Claims`, `Verification Traces`, `Script Sentences`, `Scenes`, `Visual Elements`), the 6 edge relations (`Entailment`, `Contradiction`, `Corroboration`, `Mentions`, `DerivesFrom`, `VisualDepiction`), DAG algorithms (cycle prevention/detection, topological sort, serialization to/from dict/JSON, querying claims by status, reconstructing evidence chains, calculating chain confidence), and test case designs for `tests/test_evidence_graph.py`.
   - `docs/epistemic/EVIDENCE_GRAPH.md` (Lines 21–60, 68–177, 269–302): Defines the 6-layer architecture, edge relations, and `EvidenceGraph` interface.
   - `scripts/verify_epistemic_specs.py` (Lines 244–251): Noted a layer directionality nuance where `VerificationTraceNode` sits at Layer 6 receiving edges from verified target nodes, whereas comment listed `TRACES_TO` in reverse. Canonical forward direction requires either forward edges (`Claim -> Trace`) or typed provenance relation (`Trace -> Claim: DERIVES_FROM`).
   - `src/models/contracts.py` (Lines 197–218): Currently defines baseline `SourceRecord` and `ClaimRecord` using `H9BaseModel`.
   - `PROJECT.md` (Lines 68, 76–82): Identifies M2 deliverables: `src/models/contracts.py`, `src/epistemic/graph.py`, 13-tier taxonomy, 11 statuses, 8 consensus states, and lazy import fix in `src/h9_runtime/content.py`.

2. **Filesystem Status**:
   - Directory `src/epistemic/` does not yet exist.
   - No `src/epistemic/graph.py` or `tests/test_evidence_graph.py` has been created yet.

---

## 2. Logic Chain

1. **Node Modeling**:
   - The prompt explicitly requires 8 node types: `Sources`, `Passages`, `Evidence Units`, `Claims`, `Verification Traces`, `Script Sentences`, `Scenes`, `Visual Elements`.
   - Defining a common base model `GraphNode(H9BaseModel)` ensures consistent Pydantic v2 validation, dictionary, JSON, and YAML serialization across all nodes.
   - Each concrete node class (`SourceNode`, `PassageNode`, `EvidenceUnitNode`, `ClaimNode`, `VerificationTraceNode`, `SceneNode`, `ScriptSentenceNode`, `VisualElementNode`) provides strict typing, character-offset boundaries, modality/polarity enumerations, and metadata fields.

2. **Edge Modeling & Relations**:
   - The prompt requires 6 relations: `Entailment`, `Contradiction`, `Corroboration`, `Mentions`, `DerivesFrom`, `VisualDepiction`.
   - Mapping these relations into an `EdgeRelation` enum with support for architectural aliases (`PROVIDES`, `EXTRACTS_FROM`, `GROUNDS`, `BINDS_TO`, `TRACES_TO`) provides 100% conformance to both user requirements and existing specifications.

3. **DAG Algorithms**:
   - *Cycle Prevention*: Pre-insertion cycle detection (`would_create_cycle`) via BFS from target to source guarantees that cycles are caught at insertion time before corrupting graph state. Trivial self-loops ($u = v$) are rejected immediately.
   - *Topological Sort*: Kahn's algorithm with alphanumeric tie-breaking ensures deterministic, byte-stable node orderings, preserving LLM prompt caching.
   - *Lineage Traversal*: Backward DFS pathfinding from any target node (`ScriptSentenceNode` or `VisualElementNode`) traverses upstream edges to return a typed `ProvenanceChain` and identifies ungrounded claims.
   - *Chain Confidence Calculation*: Uses multi-path Noisy-OR combination across independent branches, multiplicative decay along series hops, source tier discounting (Tiers 1–13), and subtraction of contradiction penalties.

4. **Testing Architecture**:
   - Partitioning `tests/test_evidence_graph.py` into 10 focused test classes covers all node models, edge relations, DAG invariants (cycles, self-loops, diamond DAGs), deterministic sorting, querying, lineage reconstruction, confidence formulas, serialization round-trips, `ResearchDossier` conversion, and cascading mutations.

---

## 3. Caveats

1. **Read-Only Explorer Scope**: In accordance with the Explorer persona, no files were created or modified under `src/` or `tests/`. All designs, specifications, and code blueprints are delivered in `analysis.md`.
2. **M2 Contract Dependencies**: `src/epistemic/graph.py` interacts with `SourceRecord` and `ClaimRecord` from `src/models/contracts.py`. Backward-compatible defaults on any extended fields in `contracts.py` must be preserved to prevent regressions in `tests/test_contracts.py`.

---

## 4. Conclusion

A complete, production-ready design and specification for the Evidence Graph abstraction in `src/epistemic/graph.py` has been authored and documented in `g:\Finding-new-code\harness9\.agents\explorer_3_m2\analysis.md`. 
The design fulfills all 5 user requirements:
- 8 node types modeled as Pydantic v2 schemas inheriting from `H9BaseModel`.
- 6 canonical edge relations (`Entailment`, `Contradiction`, `Corroboration`, `Mentions`, `DerivesFrom`, `VisualDepiction`).
- Formal DAG algorithms: pre-insertion cycle prevention, Kahn's deterministic topological sort, status/consensus queries, backward lineage reconstruction, and multi-path confidence calculation.
- Complete class interfaces and methods for `EvidenceGraph`.
- Detailed specification of 10 test classes for `tests/test_evidence_graph.py`.

---

## 5. Verification Method

1. **Inspect Analysis Document**:
   Read `g:\Finding-new-code\harness9\.agents\explorer_3_m2\analysis.md` to verify that all 8 node types, 6 edge relations, DAG algorithms, confidence formulas, and class blueprints are completely specified.
2. **Implementation Verification (Post-Implementation)**:
   When implemented by the coder agent, execute:
   ```bash
   pytest tests/test_evidence_graph.py -v
   pytest tests/test_contracts.py -v
   pytest tests/test_h9_acceptance.py -v
   ```
3. **Invalidation Conditions**:
   - The design is invalidated if any cyclic edge addition fails to raise `CycleDetectedError`.
   - The design is invalidated if diamond DAGs (`A -> B -> D` and `A -> C -> D`) are incorrectly rejected as cycles.
   - The design is invalidated if topological sorting order is non-deterministic across executions with different node insertion orders.
