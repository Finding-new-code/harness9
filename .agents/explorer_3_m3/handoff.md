# Handoff Report — explorer_3_m3
**Task:** Design VerificationEngine architecture, policy dispatch, DAG trace node integration, status matrix, and test case specs for Milestone 3 (Requirement R3).  
**Author:** explorer_3_m3  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\explorer_3_m3`  
**Handoff Type:** Hard (Task complete)  

---

## 1. Observation

1. **Production Contracts (`src/models/contracts.py`)**:
   - Lines 197–209: `EpistemicStatus` enum defines 11 statuses (`VERIFIED`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTESTED`, `CONTRADICTED`, `UNSUPPORTED`, `UNVERIFIABLE`, `OUTDATED`, `MISLEADING`, `OPINION`, `PREDICTION`).
   - Lines 212–258: `SourceTier` enum defines a 13-tier taxonomy from `PRIMARY_SOURCE = 1` to `UNVERIFIED = 13`, with `DEFAULT_TIER_WEIGHTS` from 1.00 down to 0.00.
   - Lines 261–271: `ConsensusState` enum defines 8 states (`STRONG_CONSENSUS`, `BROAD_CONSENSUS`, `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `INSUFFICIENT_LITERATURE`).
   - Lines 273–283: `ClaimType` enum defines 8 claim typologies (`EVENT_FACT`, `CAUSAL_INTERPRETATION`, `SCHOLARLY_INTERPRETATION`, `NUMERICAL_METRIC`, `DIRECT_QUOTE`, `SCIENTIFIC_LAW`, `CURRENT_EVENT`, `DEFINITIONAL`).
   - Lines 353–420: `ClaimRecord` has fields `epistemic_status`, `consensus_state`, `source_tier`, `source_quality`, `corroboration_set`, `temporal_context`, `verifier_metadata`, `quote_exactness`, `claim_type`, `contradicting_sources`, and `evidence_links`.
   - Lines 442–472: `ResearchDossier` includes `evidence_graph: Optional[Dict[str, Any]]` and `sources: List[SourceRecord]`.

2. **Evidence Graph Abstraction (`src/epistemic/graph.py`)**:
   - Lines 38–48: `GraphNodeType` defines 8 node types including `CLAIM` and `VERIFICATION_TRACE`.
   - Lines 50–58: `EdgeRelation` defines 6 edge relations: `ENTAILMENT`, `CONTRADICTION`, `CORROBORATION`, `MENTIONS`, `DERIVES_FROM`, `VISUAL_DEPICTION`.
   - Lines 182–196: `VerificationTraceNode` has attributes `target_node_id`, `strategy_used`, `entailment_score`, `contradiction_score`, `corroboration_score`, `status_assigned`, `consensus_state_assigned`, `verifier_name`, `audit_notes`, `execution_duration_ms`, `warnings`.
   - Lines 473–507: Method `add_verification_trace()` creates a `VerificationTraceNode` and links `target_node_id -> trace_node_id` via `EdgeRelation.DERIVES_FROM`.
   - Lines 1080–1179: Method `EvidenceGraph.from_dossier(dossier)` constructs an `EvidenceGraph` offline from a `ResearchDossier`.

3. **Formal Epistemic Specifications (`docs/epistemic/`)**:
   - `FACT_CHECKING_SPEC.md` Lines 90–133: Defines mathematical formulations for $S_{\text{entail}}$, $S_{\text{corrob}}$, $P_{\text{contra}}$, and the deterministic status decision function. Lines 201–220 define the `VerificationResult` schema.
   - `CLAIM_VERIFICATION.md` Lines 25–128: Specifies the 7 verification strategies in detail (`SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK`, `QUOTE_CHECK`, `NUMERICAL_CHECK`, `TEMPORAL_CHECK`, `HISTORIOGRAPHICAL_CHECK`). Lines 133–176 define the `STRATEGY_DISPATCH_MAP`.
   - `HISTORICAL_SCHOLARSHIP_POLICY.md` Lines 26–160: Enforces 6 inviolable rules: (1) sole web source prohibition, (2) minimum evidentiary thresholds, (3) 8 consensus states, (4) event vs. interpretation distinction, (5) non-averaging contradiction invariant, (6) calibrated script language framing.

4. **Execution & Test Environment**:
   - Python runner: `uv run pytest` under Python 3.11.15.
   - Verified that `uv run pytest tests/test_contracts.py` passes 12/12 tests in 6.54s.
   - Verified that `uv run pytest tests/test_evidence_graph.py` passes 42/42 tests in 9.06s.

---

## 2. Logic Chain

1. **Strategy Orchestration & Dispatch**:
   - Observation 1 & 3 show that claims are categorized into 8 `ClaimType`s and require different evidentiary checks.
   - Observation 3 shows the dispatch mapping in `CLAIM_VERIFICATION.md` mapping each `ClaimType` to a subset of the 7 strategies.
   - Therefore, `VerificationEngine` must implement a strategy registry and a dispatch resolver (`_resolve_strategies(claim)`) that selects mandatory strategies by `ClaimType` and dynamically augments them when text contains quotes, numbers, or historical dates.

2. **Graph Trace Node Integration & DAG Invariant**:
   - Observation 2 shows `VerificationTraceNode` and `add_verification_trace()` in `src/epistemic/graph.py`.
   - In Kahn's topological sort and DFS cycle checks in `graph.py` (lines 600–755), adding a directed edge from `claim_node_id` to `trace_node_id` with `DERIVES_FROM` never introduces a cycle because trace nodes are terminal sink nodes with no outgoing edges.
   - Therefore, calling `add_verification_trace()` inside `verify_claim()` is strictly cycle-safe and preserves DAG invariants.

3. **Status Decision Matrix**:
   - Observation 3 shows the piecewise decision function in `FACT_CHECKING_SPEC.md` §4.4 and the 11 statuses in `src/models/contracts.py`.
   - To prevent ambiguity, the status decision logic must follow a strict priority ladder: Unverifiable $\to$ Opinion $\to$ Prediction $\to$ Historical Policy Violation $\to$ Quote Distortion $\to$ Numerical Incompatibility $\to$ Temporal Obsolete $\to$ Contradicted $\to$ Contested $\to$ Partially Supported (strengthened/hedged) $\to$ Verified $\to$ Supported $\to$ Unsupported.

4. **Synchronous Contract & Graph Mutation**:
   - Observation 1 & 2 show that `ClaimRecord` and `ClaimNode` represent the same entity at the contract and graph layer.
   - Updating `claim.epistemic_status`, `claim.confidence_score`, `claim.consensus_state`, and `claim.verifier_metadata` alongside `claim_node` ensures consistency across downstream scriptwriting, editorial, and state machine gates.

5. **Dossier Verification (`verify_dossier`)**:
   - Observation 2 shows that `EvidenceGraph.from_dossier` exists.
   - Therefore, `verify_dossier` can process dossiers with or without an existing graph, verify all claims, execute cross-claim contradiction checks, compute status distribution counts, recommend gate verdicts (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`), and embed the serialized DAG into `dossier.evidence_graph`.

---

## 3. Caveats

- **Hermetic vs. Model-Assisted NLP**: In production, `SOURCE_ENTAILMENT` can optionally hook into an LLM or transformer NLI model via the Hermes provider bridge (`src/h9_runtime/bridge.py`). However, for hermetic offline test suites (`tests/test_verification_engine.py`), the strategy must provide a fully deterministic rule-based implementation (token overlap, negation detection, modal qualifier checking) to guarantee 100% offline reproducibility without API keys.
- **Scope Limit**: Script re-verification (`src/epistemic/script_verifier.py`) and visual fact-checking (`src/epistemic/visual_verifier.py`) belong to Milestone 4 and were not designed here, though their graph node interfaces (`ScriptSentenceNode`, `VisualElementNode`) were validated for downstream compatibility.

---

## 4. Conclusion

The architectural design for `VerificationEngine` in `src/epistemic/engine.py` is fully specified, mathematically grounded, and aligned with all project contracts. The design includes:
1. Complete class structure and lifecycle for `VerificationEngine`.
2. Detailed algorithms for `verify_claim(claim, graph)` and `verify_dossier(dossier, graph)`.
3. Complete aggregation logic into `VerificationResult` and `DossierVerificationReport`.
4. Strict, cycle-safe insertion of `VerificationTraceNode` into `EvidenceGraph`.
5. 11-status deterministic rule matrix.
6. Exhaustive test case designs for `tests/test_verification_engine.py` (7 test suites, 26 tests) and `tests/test_historical_policy.py` (6 test suites, 18 tests).

Full documentation is written to `g:\Finding-new-code\harness9\.agents\explorer_3_m3\analysis.md`.

---

## 5. Verification Method

To verify the findings and specifications independently:
1. **Inspect Analysis Document**:
   Read `g:\Finding-new-code\harness9\.agents\explorer_3_m3\analysis.md` to review the architecture, schemas, and test specs.
2. **Verify Contract & Graph Baseline**:
   Run the project tests to confirm current baseline stability:
   ```bash
   uv run pytest tests/test_contracts.py
   uv run pytest tests/test_evidence_graph.py
   ```
   Both commands must pass 100% (12/12 and 42/42 tests).
3. **Invalidation Conditions**:
   - Any strategy that mutates previous conversation prompts (violating Hermes prompt caching).
   - Any strategy that performs arithmetic averaging of conflicting numbers (violating the non-averaging invariant).
   - Any DAG edge insertion that creates directed cycles.
   - Any claim status transition that lacks deterministic rule grounding.
