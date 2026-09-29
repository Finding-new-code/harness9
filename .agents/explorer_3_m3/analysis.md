# Technical Architecture & Specification: VerificationEngine & Strategy Orchestration
**Component:** `src/epistemic/engine.py` & `src/epistemic/historical.py`  
**Author:** explorer_3_m3  
**Milestone:** Milestone 3 (Requirement R3) — Epistemic Verification Layer  
**Target Date:** 2026-09-14  

---

## 1. Executive Summary & Architectural Overview

The **Harness 9 Epistemic Verification Engine** (`VerificationEngine`) is the operational core of Milestone 3. It orchestrates multi-strategy truth evaluation, enforces domain-specific verification policies, maintains cryptographic and provenance lineage within the directed acyclic **Evidence Graph** (`EvidenceGraph`), and outputs deterministic, explainable verdicts across all 11 epistemic states.

### Core Architectural Mandates
1. **Decoupled Verification**: Epistemic truth is evaluated independently of search retrieval confidence. High domain authority or page ranking cannot substitute for logical entailment, independent corroboration, and scholarly consensus.
2. **Modular Strategy Dispatch**: Rather than applying a monolithic text similarity check, the engine dispatches claims to specialized verification strategies tailored to their structural typology (`ClaimType`).
3. **Graph-Grounded Lineage (`VerificationTraceNode`)**: Every execution writes an immutable trace node into the `EvidenceGraph` DAG, linking target claims, supporting evidence units, and counter-assertions while strictly maintaining DAG acyclicity.
4. **Historical Scholarship Invariant**: Historical facts and interpretations are subject to non-negotiable scholarship rules: sole web summaries are forbidden from establishing history, consensus states are classified across 8 discrete states, events are rigorously decoupled from causal interpretations, and conflicting numbers are never averaged away.
5. **Contract Synchronization**: In-memory `ClaimRecord` instances and graph `ClaimNode` entities are updated synchronously to guarantee zero data loss and 100% backward compatibility with existing H9 production contracts.

---

## 2. VerificationEngine Class Architecture & Lifecycle (`src/epistemic/engine.py`)

### 2.1 Class Structure & Imports
The `VerificationEngine` integrates directly with existing Pydantic contracts and graph abstractions:

```python
# Imports from src.models.contracts
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    H9BaseModel,
    QuoteExactness,
    ResearchDossier,
    SourceQualityMetrics,
    SourceRecord,
    SourceTier,
    TemporalContext,
)

# Imports from src.epistemic.graph
from src.epistemic.graph import (
    CycleDetectedError,
    EdgeRelation,
    EvidenceGraph,
    EvidenceUnitNode,
    GraphNodeType,
    PassageNode,
    SourceNode,
    ClaimNode,
    VerificationTraceNode,
)
```

### 2.2 Strategy Protocol & Execution Result Schema
Each verification strategy adheres to a common execution contract returning a strongly-typed `StrategyExecutionResult`:

```python
class StrategyExecutionResult(H9BaseModel):
    """Execution output from an individual verification strategy."""
    strategy_name: str
    passed: bool
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    entailment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    corroboration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    consensus_state: Optional[ConsensusState] = None
    quote_exactness: Optional[QuoteExactness] = None
    numerical_deviation_pct: Optional[float] = None
    temporal_status: Optional[str] = None
    flags: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
```

### 2.3 VerificationEngine Class Definition & Lifecycle

```python
class VerificationEngine:
    """Orchestrates strategy execution, policy dispatch, graph DAG mutation, and status determination."""

    DEFAULT_VERIFIER_NAME = "H9EpistemicVerificationEngine"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        verifier_name: Optional[str] = None,
        enable_strict_historical_policy: bool = True,
    ):
        self.config = config or {}
        self.verifier_name = verifier_name or self.DEFAULT_VERIFIER_NAME
        self.enable_strict_historical_policy = enable_strict_historical_policy
        
        # Strategy Registry
        self.strategies: Dict[str, VerificationStrategy] = {
            "SOURCE_ENTAILMENT": SourceEntailmentStrategy(),
            "CROSS_SOURCE_CORROBORATION": CrossSourceCorroborationStrategy(),
            "CONTRADICTION_CHECK": ContradictionCheckStrategy(),
            "QUOTE_CHECK": QuoteCheckStrategy(),
            "NUMERICAL_CHECK": NumericalCheckStrategy(),
            "TEMPORAL_CHECK": TemporalCheckStrategy(),
            "HISTORIOGRAPHICAL_CHECK": HistoriographicalCheckStrategy(
                strict=self.enable_strict_historical_policy
            ),
        }

        # Telemetry & Diagnostics
        self.metrics = {
            "claims_verified": 0,
            "traces_created": 0,
            "contradictions_detected": 0,
            "policy_violations_blocked": 0,
        }
```

---

## 3. The 7 Modular Verification Strategies

### 3.1 Strategy 1: `SOURCE_ENTAILMENT`
- **Objective**: Evaluates whether cited passages logically entail the claim, calculating $P(\text{Passage} \models C)$ weighted by source authority $W_{\text{tier}}$.
- **Mathematical Formulation**:
  $$S_{\text{entail}}(C) = \max_{P_i \in \text{Passages}} \left[ W_{\text{tier}}(P_i) \times P(P_i \models C) \right]$$
  Where $W_{\text{tier}}$ maps Tier 1 (1.00) down to Tier 13 (0.00).
- **Assertion Strengthening & Hedging Detection**:
  - Compares modal qualifier strength:
    - Strength 3: `"always"`, `"proven"`, `"definitely"`, `"solely"`, `"undoubtedly"`, `"certainly"`
    - Strength 2: `"generally"`, `"typically"`, `"the primary"`, `"most"`, `"substantially"`
    - Strength 1: `"may"`, `"suggests"`, `"one factor"`, `"partially"`, `"possibly"`, `"preliminary"`
  - **Invariant**: If $M(C) > M(P)$ (e.g., passage says *"evidence suggests"* but claim states *"definitely caused"*), the strategy flags `STRENGTHENED_ASSERTION_WARNING` and caps effective entailment at 0.70, forcing downstream script hedging.

### 3.2 Strategy 2: `CROSS_SOURCE_CORROBORATION`
- **Objective**: Evaluates independent confirmation across non-syndicated primary publishers.
- **Independence Calculus**:
  1. **Domain Disjointness**: Compares root domains (e.g., `archives.gov` vs `nytimes.com`). Identical root domains are assigned $I_{\text{indep}} = 0.0$.
  2. **Syndication Wire Check**: Excerpts containing syndicated wire markers (`"AP"`, `"Associated Press"`, `"Reuters"`, `"PR Newswire"`, `"Bloomberg Wire"`) are collapsed to single source provenance.
  3. **Publisher / Author Overlap**: Identical author or institutional publisher collapses independence.
- **Corroboration Score Formulation**:
  $$S_{\text{corrob}}(C) = 1.0 - \prod_{k=1}^{m} \left( 1.0 - W_{\text{tier}}(S_k) \times I_{\text{indep}}(S_k, S_{\text{primary}}) \right)$$
- If only 1 source exists for a claim requiring multi-source backing, flags `SINGLE_SOURCE_VULNERABILITY`.

### 3.3 Strategy 3: `CONTRADICTION_CHECK`
- **Objective**: Detects mutually exclusive assertions, opposing polarities, or numerical incompatibilities.
- **Contradiction Penalty**:
  $$P_{\text{contra}}(C) = \max_{P_j \in \text{Passages}} \left[ W_{\text{tier}}(P_j) \times P(P_j \models \neg C) \right]$$
- **The Non-Averaging Invariant**:
  - When contradiction is identified (e.g. Source A asserts 20,000 casualties, Source B asserts 100,000), the system is strictly forbidden from synthesizing a mid-point (60,000).
  - Both assertions are preserved in the DAG linked via `EdgeRelation.CONTRADICTION`.
  - Sets `ConsensusState = CONTESTED` and sets status `CONTESTED`.

### 3.4 Strategy 4: `QUOTE_CHECK`
- **Objective**: Enforces character-level verbatim fidelity for direct speech and primary textual quotations.
- **Levenshtein Matching Protocol**:
  1. Strip quotation marks (`"`, `”`, `“`, `'`), normalize whitespace, collapse internal punctuation.
  2. Compute normalized Levenshtein distance:
     $$D_{\text{norm}}(Q_{\text{asserted}}, Q_{\text{archive}}) = \frac{\text{Levenshtein}(Q_{\text{asserted}}, Q_{\text{archive}})}{\max(|Q_{\text{asserted}}|, |Q_{\text{archive}}|)}$$
  3. Decision Thresholds:
     - $D_{\text{norm}} \le 0.02 \implies$ `QuoteExactness.EXACT`.
     - $0.02 < D_{\text{norm}} \le 0.15$ with standard ellipses (`...` or `[...]`) $\implies$ `QuoteExactness.ELLIPSES`.
     - $D_{\text{norm}} > 0.02$ without ellipses $\implies$ `QuoteExactness.DISTORTED`.
  4. **The Paraphrase Mandate**: If quote is distorted, the strategy mandates conversion to indirect attributed paraphrase and flags `QUOTE_FABRICATION_DETECTED`.

### 3.5 Strategy 5: `NUMERICAL_CHECK`
- **Objective**: Validates numerical quantities, dimensions, metric scales, and arithmetic calculations.
- **Verification Protocol**:
  1. Extract `(scalar, prefix, unit)` from claim text (e.g. `"80 billion transistors"` $\to (80 \times 10^9, \text{count})$).
  2. Normalize to SI base units.
  3. Relative deviation calculation against ground truth:
     $$\delta = \frac{|V_{\text{claim}} - V_{\text{ground\_truth}}|}{V_{\text{ground\_truth}}}$$
  4. Tolerance evaluation:
     - $\delta \le 0.001$ ($0.1\%$): Validated exact metric.
     - $\delta \le 0.05$ ($5.0\%$): Permitted ONLY if explicit approximation qualifiers are present (`"approximately"`, `"around"`, `"roughly"`).
     - $\delta > \text{tolerance}$: Flags `NUMERICAL_MISMATCH` and triggers `BLOCK`.
  5. Arithmetic consistency check: Computes compound statements (e.g., "grew from 10 to 30, a 300% increase" $\implies$ detects calculation error because $(30-10)/10 = 200\% \ne 300\%$).

### 3.6 Strategy 6: `TEMPORAL_CHECK`
- **Objective**: Evaluates chronological precedence, historical anachronisms, and temporal freshness.
- **Verification Protocol**:
  1. **Causal Precedence**: If claim asserts event $A$ caused event $B$, verifies $\text{Date}(A) < \text{Date}(B)$. If $\text{Date}(A) \ge \text{Date}(B)$, flags `CHRONOLOGICAL_INVERSION`.
  2. **Anachronism Scanner**: Evaluates named entities and technologies against historical era boundaries $[T_{\text{origin}}, T_{\text{extinction}}]$. Any technology referenced before its inception date (e.g., radar in 1812) triggers `ANACHRONISM_DETECTED`.
  3. **Temporal Freshness**: If claim asserts time-sensitive status ("fastest computer", "world record holder", "current CEO") without an `as_of_date` or when `valid_until < now()`, flags `OUTDATED_CLAIM` and assigns status `OUTDATED`.

### 3.7 Strategy 7: `HISTORIOGRAPHICAL_CHECK`
- **Objective**: Enforces the 6 rules of the Historical Scholarship Policy (`HISTORICAL_SCHOLARSHIP_POLICY.md`).
- **Verification Protocol**:
  1. **Rule 1 (Sole Web Source Prohibition)**: Blocks any historical fact (`EVENT_FACT`) or interpretation (`SCHOLARLY_INTERPRETATION`) backed solely by Tiers 9–13 (Wikipedia, blogs, pop articles, forums). Raises `POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE`.
  2. **Rule 2 (Minimum Evidentiary Thresholds)**: Requires either Threshold A (Tier 1 Primary), Threshold B (Tier 3 University Press), or Threshold C (2x Tier 2 Peer-Reviewed Journals).
  3. **Rule 3 (Consensus State Classification)**: Maps scholarship into one of the 8 canonical consensus states:
     - `STRONG_CONSENSUS`, `BROAD_CONSENSUS`, `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `INSUFFICIENT_LITERATURE`.
  4. **Rule 4 (Event vs Interpretation)**: Ensures causal theories are never narrated as undisputed empirical events.
  5. **Rule 5 (Non-Averaging Contradiction)**: Preserves opposing estimates in the graph.
  6. **Rule 6 (Calibrated Narration Framing)**: Mandates consensus-aligned phrasing templates.

---

## 4. Policy Dispatch Matrix & Execution Routing

The `VerificationEngine` routes claims based on their `ClaimType` and dynamically augments the strategy pipeline when specific textual facets are detected:

```python
STRATEGY_DISPATCH_MAP: Dict[ClaimType, List[str]] = {
    ClaimType.EVENT_FACT: [
        "SOURCE_ENTAILMENT",
        "CROSS_SOURCE_CORROBORATION",
        "TEMPORAL_CHECK",
        "HISTORIOGRAPHICAL_CHECK",
    ],
    ClaimType.CAUSAL_INTERPRETATION: [
        "HISTORIOGRAPHICAL_CHECK",
        "CONTRADICTION_CHECK",
        "CROSS_SOURCE_CORROBORATION",
    ],
    ClaimType.SCHOLARLY_INTERPRETATION: [
        "HISTORIOGRAPHICAL_CHECK",
        "CONTRADICTION_CHECK",
    ],
    ClaimType.NUMERICAL_METRIC: [
        "NUMERICAL_CHECK",
        "SOURCE_ENTAILMENT",
        "CROSS_SOURCE_CORROBORATION",
    ],
    ClaimType.DIRECT_QUOTE: [
        "QUOTE_CHECK",
        "SOURCE_ENTAILMENT",
    ],
    ClaimType.SCIENTIFIC_LAW: [
        "SOURCE_ENTAILMENT",
        "CROSS_SOURCE_CORROBORATION",
        "CONTRADICTION_CHECK",
    ],
    ClaimType.CURRENT_EVENT: [
        "SOURCE_ENTAILMENT",
        "TEMPORAL_CHECK",
        "CROSS_SOURCE_CORROBORATION",
        "CONTRADICTION_CHECK",
    ],
    ClaimType.DEFINITIONAL: [
        "SOURCE_ENTAILMENT",
    ],
}
```

### Dynamic Strategy Augmentation
Before execution, `resolve_strategies(claim)` dynamically expands the required strategy list:
1. **Quote Facet**: If `claim.claim_text` contains quotation marks (`"` or `“`) and `"QUOTE_CHECK"` is not present, `"QUOTE_CHECK"` is added.
2. **Numerical Facet**: If regex detects numbers/percentages/metrics and `"NUMERICAL_CHECK"` is not present, `"NUMERICAL_CHECK"` is added.
3. **Historical Facet**: If claim topic, category, or temporal date references historical context ($T < 1950$) and `"HISTORIOGRAPHICAL_CHECK"` is not present, it is added.

---

## 5. Method Specifications

### 5.1 Method: `verify_claim(claim, graph) -> VerificationResult`

#### Execution Workflow
1. **Node Resolution**:
   - Checks if `claim.claim_id` exists in `graph`. If absent, registers a `ClaimNode` via `graph.add_claim(...)`.
   - Ensures backing `SourceNode`, `PassageNode`, and `EvidenceUnitNode` exist in `graph` (ingesting from `claim.primary_source` and `claim.corroborating_sources` if needed).
2. **Strategy Dispatch**:
   - Resolves mandatory and augmented strategies for `claim.claim_type`.
3. **Sequential Execution**:
   - Runs each strategy against the claim and graph context.
   - Collects intermediate metrics: entailment score, corroboration score, contradiction penalty, quote exactness, numerical deviation, temporal freshness, consensus state, and flags.
4. **Deterministic Rule Matrix Evaluation**:
   - Applies the decision hierarchy to determine the final `EpistemicStatus` and composite confidence score.
5. **DAG Mutation (`VerificationTraceNode`)**:
   - Instantiates `VerificationTraceNode` and inserts it via `graph.add_verification_trace(...)`.
   - Automatically establishes the directed edge: `target_claim_id -> trace_node_id` with `relation = DERIVES_FROM`.
   - Links supporting `EvidenceUnitNode`s via `relation = ENTAILMENT`.
   - Links contradicting `EvidenceUnitNode`s via `relation = CONTRADICTION`.
   - Guarantees DAG acyclicity (traces are sink nodes).
6. **Contract & Graph Synchronization**:
   - Updates `claim.epistemic_status = result.status`.
   - Updates `claim.consensus_state = result.consensus_state`.
   - Updates `claim.source_tier = result.highest_source_tier`.
   - Updates `claim.confidence_score = result.confidence`.
   - Updates `claim.verifier_metadata` with trace ID, execution duration, and audit notes.
   - Synchronously updates the corresponding `ClaimNode` attributes in `graph`.
7. **Return**: Returns the populated `VerificationResult`.

```python
def verify_claim(
    self,
    claim: ClaimRecord,
    graph: EvidenceGraph,
) -> VerificationResult:
    start_time = time.perf_counter()
    
    # 1. Ensure claim is registered in EvidenceGraph
    claim_node = graph.get_node(claim.claim_id)
    if claim_node is None:
        graph.add_claim(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            claim_type=claim.claim_type.value,
            epistemic_status=claim.epistemic_status.value,
            consensus_state=claim.consensus_state.value,
            confidence_score=claim.confidence_score,
            category=claim.category,
            claim_record=claim,
        )
        claim_node = graph.require_node(claim.claim_id)

    # 2. Resolve strategies
    strategies_to_run = self._resolve_strategies(claim)
    
    # 3. Execute strategies
    strategy_results: List[StrategyExecutionResult] = []
    for s_name in strategies_to_run:
        strategy = self.strategies[s_name]
        res = strategy.evaluate(claim=claim, graph=graph, claim_node=claim_node)
        strategy_results.append(res)

    # 4. Aggregate metrics & apply decision matrix
    agg = self._aggregate_strategy_results(claim, strategy_results)
    final_status, confidence, explanation = self._determine_epistemic_status(claim, agg)
    
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    # 5. Insert VerificationTraceNode into DAG
    trace_id = graph.add_verification_trace(
        target_node_id=claim.claim_id,
        strategy_used=",".join(strategies_to_run),
        entailment_score=agg["entailment_score"],
        contradiction_score=agg["contradiction_score"],
        corroboration_score=agg["corroboration_score"],
        status_assigned=final_status.value,
        consensus_state_assigned=agg["consensus_state"].value if agg.get("consensus_state") else None,
        verifier_name=self.verifier_name,
        audit_notes=explanation,
        execution_duration_ms=duration_ms,
        warnings=agg["warnings"],
    )

    # 6. Link supporting and contradicting evidence
    for eu_id in agg["supporting_evidence_ids"]:
        if not graph.get_edge(eu_id, claim.claim_id) and not graph.would_create_cycle(eu_id, claim.claim_id):
            graph.link(eu_id, claim.claim_id, EdgeRelation.ENTAILMENT, weight=agg["entailment_score"])
            
    for counter_id in agg["contradicting_evidence_ids"]:
        if not graph.get_edge(counter_id, claim.claim_id) and not graph.would_create_cycle(counter_id, claim.claim_id):
            graph.link(counter_id, claim.claim_id, EdgeRelation.CONTRADICTION, weight=agg["contradiction_score"])

    # 7. Synchronize ClaimRecord & ClaimNode
    claim.epistemic_status = final_status
    if agg.get("consensus_state"):
        claim.consensus_state = agg["consensus_state"]
    claim.confidence_score = confidence
    claim.source_tier = agg["highest_source_tier"]
    claim.verifier_metadata = {
        "trace_id": trace_id,
        "verifier_name": self.verifier_name,
        "duration_ms": duration_ms,
        "strategies_run": strategies_to_run,
        "warnings": agg["warnings"],
        "flags": agg["flags"],
    }
    
    claim_node.epistemic_status = final_status.value
    if agg.get("consensus_state"):
        claim_node.consensus_state = agg["consensus_state"].value
    claim_node.confidence_score = confidence
    claim_node.verifier_metadata = claim.verifier_metadata

    return VerificationResult(
        claim_id=claim.claim_id,
        status=final_status,
        claim_type=claim.claim_type,
        confidence=confidence,
        entailment_score=agg["entailment_score"],
        corroboration_score=agg["corroboration_score"],
        contradiction_score=agg["contradiction_score"],
        highest_source_tier=agg["highest_source_tier"],
        consensus_state=agg.get("consensus_state"),
        supporting_evidence_ids=agg["supporting_evidence_ids"],
        contradicting_evidence_ids=agg["contradicting_evidence_ids"],
        flags=agg["flags"],
        explanation=explanation,
    )
```

---

### 5.2 Method: `verify_dossier(dossier, graph) -> DossierVerificationReport`

#### Execution Workflow
1. **Graph Resolution**:
   - If `graph` is provided: uses the active graph instance.
   - If `graph` is None: builds a fresh hermetic `EvidenceGraph` from `dossier` via `EvidenceGraph.from_dossier(dossier)`.
2. **Claim Verification**:
   - Loops over all claims in `dossier.claims`, calling `verify_claim(claim, graph)`.
3. **Cross-Claim Contradiction Audit**:
   - Traverses all pairs of claims in the dossier. If two claims assert contradictory facts (e.g. claim 1: "invented in 1947", claim 2: "invented in 1952"), both are flagged and their status set to `CONTESTED`.
4. **Talking Point & Statistic Validation**:
   - Verifies that all `dossier.talking_points` reference valid, non-blocked claims.
   - Verifies that all `dossier.statistics` align with verified claims.
5. **Gate Recommendation Evaluation**:
   - `BLOCK`: If any claim is `CONTRADICTED` or `UNSUPPORTED`, or if `policy_violation` exists.
   - `HUMAN_REVIEW`: If any claim is `CONTESTED` or `UNVERIFIABLE`.
   - `WARN`: If any claim is `PARTIALLY_SUPPORTED` or `OUTDATED`.
   - `PASS`: If all claims are `VERIFIED` or `SUPPORTED`.
6. **Graph Serialization**:
   - Stores the updated Evidence Graph back into `dossier.evidence_graph = graph.to_dict()`.
7. **Return**: Returns structured `DossierVerificationReport`.

```python
class DossierVerificationReport(H9BaseModel):
    """Aggregate verification report for an entire ResearchDossier."""
    topic: str
    run_id: str
    total_claims: int
    status_counts: Dict[str, int]
    gate_recommendation: str  # PASS | WARN | HUMAN_REVIEW | BLOCK
    results: List[VerificationResult]
    unsupported_claim_ids: List[str] = Field(default_factory=list)
    contradicted_claim_ids: List[str] = Field(default_factory=list)
    contested_claim_ids: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    graph_id: str
    duration_ms: float
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

---

## 6. Deterministic Epistemic Status Rule Matrix

The assignment of `EpistemicStatus` follows a deterministic decision hierarchy:

```
                                  EVALUATION PIPELINE
                                          │
                    [Is claim empirically testable / falsifiable?]
                                   ┌──────┴──────┐
                                   NO           YES
                                   │             │
                             UNVERIFIABLE   [Is subjective evaluative judgment?]
                                                 ┌──────┴──────┐
                                                YES            NO
                                                 │              │
                                              OPINION     [Is forward-looking forecast (T > now)?]
                                                               ┌──────┴──────┐
                                                              YES            NO
                                                               │              │
                                                           PREDICTION   [Policy Violation (Sole Web Source)?]
                                                                             ┌──────┴──────┐
                                                                            YES            NO
                                                                             │              │
                                                                        UNSUPPORTED   [Quote Distortion / Distorted?]
                                                                                           ┌──────┴──────┐
                                                                                          YES            NO
                                                                                           │              │
                                                                                      CONTRADICTED  [Numerical Mismatch > Tol?]
                                                                                                         ┌──────┴──────┐
                                                                                                        YES            NO
                                                                                                         │              │
                                                                                                    CONTRADICTED  [Temporal Check Obsolete?]
                                                                                                                       ┌──────┴──────┐
                                                                                                                      YES            NO
                                                                                                                       │              │
                                                                                                                    OUTDATED     [P_contra >= 0.80 & P_contra > S_entail?]
                                                                                                                                      ┌──────┴──────┐
                                                                                                                                     YES            NO
                                                                                                                                      │              │
                                                                                                                                CONTRADICTED    [P_contra >= 0.60 & S_entail >= 0.60, or Debate?]
                                                                                                                                                     ┌──────┴──────┐
                                                                                                                                                    YES            NO
                                                                                                                                                     │              │
                                                                                                                                                 CONTESTED     [Assertion Strengthened?]
                                                                                                                                                                    ┌──────┴──────┐
                                                                                                                                                                   YES            NO
                                                                                                                                                                    │              │
                                                                                                                                                           PARTIALLY_SUPP  [S_entail >= 0.90 & S_corrob >= 0.85 & Tier <= 3?]
                                                                                                                                                                                ┌──────┴──────┐
                                                                                                                                                                               YES            NO
                                                                                                                                                                                │              │
                                                                                                                                                                             VERIFIED     [S_entail >= 0.80 & P_contra < 0.30?]
                                                                                                                                                                                               ┌──────┴──────┐
                                                                                                                                                                                              YES            NO
                                                                                                                                                                                               │              │
                                                                                                                                                                                           SUPPORTED      [0.60 <= S_entail < 0.80?]
                                                                                                                                                                                                               ┌──────┴──────┐
                                                                                                                                                                                                              YES            NO
                                                                                                                                                                                                               │              │
                                                                                                                                                                                                       PARTIALLY_SUPP    UNSUPPORTED
```

### Complete Decision Matrix Specification

| Status | Triggering Conditions | Required Action | Gate Impact |
|---|---|---|---|
| `UNVERIFIABLE` | Assertion lacks empirical/falsifiable criteria | Strip factual claims; reclassify | `HUMAN_REVIEW` |
| `OPINION` | Subjective/aesthetic judgment ("greatest", "beautiful") | Permitted as commentary | Ignored |
| `PREDICTION` | Future event date $T > T_{\text{current}}$ | Mandate speculative framing | `WARN` |
| `CONTRADICTED` | $P_{\text{contra}} \ge 0.80$, or distorted quote, or numerical mismatch $> \text{tol}$ | Strip claim from synthesis | `BLOCK` |
| `CONTESTED` | $P_{\text{contra}} \ge 0.60 \land S_{\text{entail}} \ge 0.60$, or `ConsensusState` in (`ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`) | Mandate calibrated range narration | `HUMAN_REVIEW` |
| `OUTDATED` | Time-sensitive assertion missing anchor or superseded | Require temporal anchor ("as of 2024") | `WARN` / `BLOCK` |
| `PARTIALLY_SUPPORTED` | $0.60 \le S_{\text{entail}} < 0.80$, or assertion strengthening detected | Inject epistemic qualifiers/hedging | `WARN` |
| `VERIFIED` | $S_{\text{entail}} \ge 0.90 \land S_{\text{corrob}} \ge 0.85 \land P_{\text{contra}} < 0.20 \land \text{Tier} \le 3$ | Allowed unconditionally | `PASS` |
| `SUPPORTED` | $S_{\text{entail}} \ge 0.80 \land P_{\text{contra}} < 0.30$ | Allowed | `PASS` |
| `UNSUPPORTED` | Sole web source for historical claim, or $S_{\text{entail}} < 0.60$ | Strip claim; require new research | `BLOCK` |

---

## 7. Test Case Specifications: `tests/test_verification_engine.py`

File: `tests/test_verification_engine.py`  
Test Runner: `uv run pytest tests/test_verification_engine.py`  
Framework: `unittest.TestCase` / `pytest`

### Test Suite 1: Initialization, Verifier Identity & Strategy Registry
- `test_engine_initialization_defaults()`: Verifies that engine initializes with default verifier name `"H9EpistemicVerificationEngine"`, strict historical policy enabled, and all 7 strategies registered.
- `test_engine_initialization_custom_config()`: Verifies custom verifier name, strategy configuration overrides, and telemetry counters initialized to zero.

### Test Suite 2: Policy Dispatch by ClaimType & Dynamic Facets
- `test_dispatch_event_fact()`: Asserts dispatched strategies include `SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`, `TEMPORAL_CHECK`, `HISTORIOGRAPHICAL_CHECK`.
- `test_dispatch_numerical_metric()`: Asserts dispatched strategies include `NUMERICAL_CHECK`, `SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`.
- `test_dispatch_direct_quote()`: Asserts dispatched strategies include `QUOTE_CHECK`, `SOURCE_ENTAILMENT`.
- `test_dispatch_causal_interpretation()`: Asserts dispatched strategies include `HISTORIOGRAPHICAL_CHECK`, `CONTRADICTION_CHECK`, `CROSS_SOURCE_CORROBORATION`.
- `test_dispatch_dynamic_quote_augmentation()`: Passes a `ClaimType.EVENT_FACT` whose claim text contains `"He said 'eureka'"`. Asserts `"QUOTE_CHECK"` is dynamically added.
- `test_dispatch_dynamic_numerical_augmentation()`: Passes a `ClaimType.EVENT_FACT` with `"80,000 troops"`. Asserts `"NUMERICAL_CHECK"` is dynamically added.

### Test Suite 3: Strategy Execution Units
- `test_strategy_source_entailment_tier_weighting()`: Tests claim backed by Tier 1 (weight 1.0) vs Tier 11 (weight 0.35). Verifies calculated $S_{\text{entail}}$ correctly reflects tier weight.
- `test_strategy_source_entailment_strengthening_detection()`: Passage has "preliminary data suggests", claim has "definitely proven". Verifies `STRENGTHENED_ASSERTION_WARNING` is raised and status is downgraded to `PARTIALLY_SUPPORTED`.
- `test_strategy_cross_corroboration_independent_sources()`: Two distinct domains (`nih.gov`, `nature.com`) yield high $S_{\text{corrob}} > 0.90$.
- `test_strategy_cross_corroboration_syndicated_discounting()`: Two sources from `reuters.com` and `apnews.com` containing `"AP Wire"` are discounted as non-independent.
- `test_strategy_contradiction_detection()`: Source asserts "Entity was founded in 1990", counter-source asserts "Entity was never founded". Detects polar contradiction, calculates $P_{\text{contra}} > 0.85$, assigns `CONTRADICTED`.
- `test_strategy_quote_check_exact_match()`: Verbatim match with $D_{\text{norm}} = 0.0$ returns `QuoteExactness.EXACT`.
- `test_strategy_quote_check_ellipses_match()`: Text with standard omission `[...]` returns `QuoteExactness.ELLIPSES`.
- `test_strategy_quote_check_distortion_mandates_paraphrase()`: Distorted quote with $D_{\text{norm}} = 0.30$ returns `QuoteExactness.DISTORTED`, raises `QUOTE_FABRICATION_DETECTED`, and mandates paraphrase.
- `test_strategy_numerical_check_exact_and_tolerance()`: 80B transistors vs 80.0B passes exact. 82B with "approximately" passes within $5\%$. 120B fails tolerance with `NUMERICAL_MISMATCH`.
- `test_strategy_numerical_check_compound_arithmetic_error()`: Sentence asserting "grew from 10 to 30, a 300% increase" flags arithmetic error.
- `test_strategy_temporal_check_anachronism()`: Roman empire communicating via "telegraph" flags anachronism.
- `test_strategy_temporal_check_outdated_status()`: "World's fastest supercomputer" with `valid_until = "2020-01-01"` assigns `OUTDATED`.

### Test Suite 4: Deterministic Epistemic Status Matrix
- `test_status_verified()`: High entailment ($0.95$), high corroboration ($0.92$), low contradiction ($0.05$), Tier 1 $\implies$ `VERIFIED`.
- `test_status_supported()`: Entailment $0.85$, contradiction $0.10$ $\implies$ `SUPPORTED`.
- `test_status_partially_supported()`: Entailment $0.72$ $\implies$ `PARTIALLY_SUPPORTED`.
- `test_status_contested()`: Entailment $0.85$, contradiction $0.80$ $\implies$ `CONTESTED`.
- `test_status_contradicted()`: Contradiction $0.90 > \text{Entailment}$ $\implies$ `CONTRADICTED`.
- `test_status_unsupported()`: Entailment $0.40$ $\implies$ `UNSUPPORTED`.
- `test_status_opinion()`: "The sunset was the most beautiful in history" $\implies$ `OPINION`.
- `test_status_prediction()`: "By 2050, AI will exceed..." $\implies$ `PREDICTION`.
- `test_status_unverifiable()`: Unfalsifiable metaphysical statement $\implies$ `UNVERIFIABLE`.

### Test Suite 5: DAG Trace Node & Graph Integration
- `test_verification_trace_node_insertion()`: Verifies `VerificationTraceNode` is added to `EvidenceGraph`.
- `test_graph_edge_link_derives_from()`: Verifies directed edge `claim_id -> trace_id` with `EdgeRelation.DERIVES_FROM`.
- `test_graph_acyclicity_preserved()`: Traverses graph with Kahn's topological sort; asserts 0 cycles after trace insertion.
- `test_synchronous_claim_record_and_node_update()`: Asserts `claim.epistemic_status == claim_node.epistemic_status` and metadata matches.

### Test Suite 6: Dossier Verification (`verify_dossier`)
- `test_verify_dossier_all_valid_pass_gate()`: Dossier with 3 verified claims yields `gate_recommendation == "PASS"`.
- `test_verify_dossier_contested_claim_human_review_gate()`: Dossier with 1 contested claim yields `gate_recommendation == "HUMAN_REVIEW"`.
- `test_verify_dossier_contradicted_claim_block_gate()`: Dossier with 1 contradicted claim yields `gate_recommendation == "BLOCK"`.
- `test_verify_dossier_cross_claim_contradiction()`: Dossier with two claims contradicting each other sets both to `CONTESTED` and recommends `HUMAN_REVIEW`.
- `test_verify_dossier_stores_graph_in_dossier()`: Verifies `dossier.evidence_graph` contains serialized DAG dictionary.

---

## 8. Test Case Specifications: `tests/test_historical_policy.py`

File: `tests/test_historical_policy.py`  
Test Runner: `uv run pytest tests/test_historical_policy.py`  
Framework: `unittest.TestCase` / `pytest`

### Test Suite 1: Rule 1 — Prohibition of Sole Web Sources
- `test_sole_source_wikipedia_rejected()`: Historical claim with sole source Tier 9 (Wikipedia / General Encyclopedia) is blocked with `POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE` and assigned `UNSUPPORTED`.
- `test_sole_source_blog_rejected()`: Historical claim with sole source Tier 11/12 (Commercial blog) is rejected.
- `test_web_source_corroborated_by_archive_allowed()`: Web encyclopedia cross-referenced with Tier 1 (Archival Document) or Tier 3 (Academic Press Book) satisfies Rule 1 and succeeds.

### Test Suite 2: Rule 2 — Minimum Evidentiary Thresholds
- `test_threshold_a_primary_source_pass()`: Single Tier 1 Primary Source satisfies Threshold A $\implies$ `SUPPORTED`.
- `test_threshold_b_academic_press_pass()`: Single Tier 3 University Press Book (e.g. Oxford University Press) satisfies Threshold B $\implies$ `SUPPORTED`.
- `test_threshold_c_two_peer_reviewed_journals_pass()`: Two independent Tier 2 Peer-Reviewed Journals satisfy Threshold C $\implies$ `SUPPORTED`.
- `test_single_peer_reviewed_journal_insufficient_for_threshold_c()`: A single Tier 2 journal without primary backing flags insufficient literature.

### Test Suite 3: Rule 3 — 8-State Consensus Model Classification
- `test_consensus_strong_consensus()`: Unanimous agreement with 0 dissent across 50 years $\implies$ `STRONG_CONSENSUS`.
- `test_consensus_broad_consensus()`: $>90\%$ academic agreement with minor fringe dissent $\implies$ `BROAD_CONSENSUS`.
- `test_consensus_majority_interpretation()`: Dominant paradigm with established academic counter-hypothesis $\implies$ `MAJORITY_INTERPRETATION`.
- `test_consensus_minority_interpretation()`: Peer-reviewed counter-thesis $\implies$ `MINORITY_INTERPRETATION`.
- `test_consensus_active_debate()`: Competing scholarly schools with substantial peer-reviewed division $\implies$ `ACTIVE_DEBATE`.
- `test_consensus_contested()`: Mutually exclusive primary accounts $\implies$ `CONTESTED`.
- `test_consensus_unresolved()`: Inconclusive documentary evidence $\implies$ `UNRESOLVED`.
- `test_consensus_insufficient_literature()`: $<2$ scholarly references $\implies$ `INSUFFICIENT_LITERATURE`.

### Test Suite 4: Rule 4 — Event vs. Interpretation Distinction
- `test_event_fact_requires_empirical_date_and_place()`: `ClaimType.EVENT_FACT` validates presence of verified temporal date and location.
- `test_causal_interpretation_requires_attribution()`: `ClaimType.CAUSAL_INTERPRETATION` stated as absolute empirical certainty is flagged; requires attribution to historical scholarship.

### Test Suite 5: Rule 5 — The Non-Averaging Contradiction Invariant
- `test_divergent_casualty_counts_non_averaging()`: Source A says 20,000 casualties; Source B says 100,000 casualties.
  - Verifies engine DOES NOT average to 60,000.
  - Verifies both records are stored in graph with `EdgeRelation.CONTRADICTION`.
  - Verifies `claim.epistemic_status == EpistemicStatus.CONTESTED`.
  - Verifies `claim.consensus_state == ConsensusState.CONTESTED`.
- `test_divergent_battle_dates_preserved()`: Divergent historical dates preserved as opposing assertions.

### Test Suite 6: Rule 6 — Calibrated Script Language Framing & Adversarial Myth Defense
- `test_strong_consensus_framing()`: Mandates direct affirmative statements; forbids ungrounded speculation words ("allegedly").
- `test_active_debate_framing()`: Mandates "Historians remain divided over whether X or Y..."; forbids dogmatic assertion of one side.
- `test_adversarial_false_consensus_myth_neutralization()`: Historical myth (e.g. "horned Viking helmets") repeated on 100 blogs is demoted due to zero-weighting of Tier 11–13 sources, preventing false consensus attack.

---

## 9. Implementation File Structure & Module Exports

When Milestone 3 is implemented by worker agents, the codebase layout will be:

```
src/epistemic/
├── __init__.py               # Exports VerificationEngine, VerificationResult, DossierVerificationReport, etc.
├── graph.py                  # EvidenceGraph DAG abstraction (Milestone M2 - completed)
├── engine.py                 # VerificationEngine, strategies, and policy dispatch
├── historical.py             # HistoricalScholarshipPolicyEngine and consensus classifier
├── rules.py                  # Deterministic EpistemicStatus decision matrix
└── strategies/               # Individual strategy implementations
    ├── __init__.py
    ├── entailment.py         # SourceEntailmentStrategy
    ├── corroboration.py      # CrossSourceCorroborationStrategy
    ├── contradiction.py      # ContradictionCheckStrategy
    ├── quote.py              # QuoteCheckStrategy
    ├── numerical.py          # NumericalCheckStrategy
    ├── temporal.py           # TemporalCheckStrategy
    └── historiographical.py  # HistoriographicalCheckStrategy
```

### Module `src/epistemic/__init__.py` Extension
```python
from src.epistemic.engine import (
    VerificationEngine,
    VerificationResult,
    DossierVerificationReport,
    StrategyExecutionResult,
)
from src.epistemic.historical import (
    HistoricalScholarshipPolicyEngine,
    HistoriographicalEvaluationReport,
)
```

---

## 10. Conclusion & Worker Handoff Directives

1. **Clean Separation of Concerns**: Keep each verification strategy in a modular class or function with isolated unit testing.
2. **Hermetic Offline Testing**: Strategies must execute deterministically without requiring live internet access during test runs.
3. **Pydantic Validation**: All outputs (`VerificationResult`, `DossierVerificationReport`, `StrategyExecutionResult`) must inherit from `H9BaseModel` and validate strict field constraints.
4. **Zero Regressions**: Ensure `tests/test_contracts.py` (12/12) and `tests/test_evidence_graph.py` (42/42) continue to pass 100%.
