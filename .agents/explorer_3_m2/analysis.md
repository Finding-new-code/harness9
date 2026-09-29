# Architectural Design & Specification: Dedicated Evidence Graph Abstraction (`src/epistemic/graph.py`)

**Author:** `explorer_3_m2`  
**Milestone:** M2 — Evidence Graph & Extended Contracts  
**Target Package:** `src/epistemic/graph.py`  
**Target Test Suite:** `tests/test_evidence_graph.py`  
**Related Documents:** `docs/epistemic/EVIDENCE_GRAPH.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/epistemic/FACT_CHECKING_SPEC.md`, `docs/DATA_MODEL.md`, `docs/adrs/ADR-006-epistemic-verification.md`  

---

## 1. Executive Summary & Architectural Purpose

In autonomous content and media creation pipelines, factual claims have historically been treated as ephemeral strings or ungrounded scalar metadata. When a scriptwriting engine embellishes a passage, or when a rendering compiler parameterizes a chart, the grounding connection to the original archival document, lab report, or statistical registry is broken.

The **Harness 9 Evidence Graph (`src/epistemic/graph.py`)** is a dedicated, machine-readable Directed Acyclic Graph (DAG) abstraction that maintains an unbroken, tamper-resistant chain of factual provenance across the entire content lifecycle:
1. **Decoupling Retrieval from Truth**: Epistemic validity is modeled independently of search engine rank or domain authority.
2. **End-to-End Grounding Lineage**: Connects external sources to extracted textual passages, atomic evidence units, consolidated claims, verification traces, spoken voiceover script sentences, video scenes, and rendered visual IR elements.
3. **Graph Invariants**: Strictly enforces acyclicity, tamper-resistance (SHA-256 cryptographic digests of source bodies), non-averaging of historical contradictions, and deterministic topological ordering.
4. **Prompt-Cache Stability**: All graph structures, serializations, and node traversals employ deterministic tie-breaking to ensure byte-stable representations that do not bust LLM prompt caches.

---

## 2. Complete Node Taxonomy & Pydantic Data Models

The Evidence Graph defines 8 distinct node types across 6 logical layers. Every node inherits from `GraphNode`, which extends `H9BaseModel` (Pydantic v2 with dictionary, JSON, and YAML serialization capabilities).

```
Layer 1: Source Layer          ──► [SourceNode]
                                        │
Layer 2: Passage Layer         ──► [PassageNode]
                                        │
Layer 3: Evidence Unit Layer   ──► [EvidenceUnitNode]
                                        │
Layer 4: Claim Layer           ──► [ClaimNode]
                                        │
Layer 5: Production Output     ──► [SceneNode] ──► [ScriptSentenceNode]
                                      └──► [VisualElementNode]
                                        │
Layer 6: Audit Layer           ──► [VerificationTraceNode]
```

### 2.1 Node Enums & Base Model

```python
class GraphNodeType(str, Enum):
    """The 8 canonical node types within the Evidence Graph."""
    SOURCE = "source"
    PASSAGE = "passage"
    EVIDENCE_UNIT = "evidence_unit"
    CLAIM = "claim"
    VERIFICATION_TRACE = "verification_trace"
    SCRIPT_SENTENCE = "script_sentence"
    SCENE = "scene"
    VISUAL_ELEMENT = "visual_element"


class ModalityType(str, Enum):
    """Epistemic modality of an extracted evidence proposition."""
    CERTAIN = "CERTAIN"
    PROBABILISTIC = "PROBABILISTIC"
    POSSIBLE = "POSSIBLE"
    COUNTERFACTUAL = "COUNTERFACTUAL"


class GraphNode(H9BaseModel):
    """Abstract base class for all nodes in the Evidence Graph."""
    node_id: str = Field(..., min_length=1, description="Globally unique identifier for the node")
    node_type: GraphNodeType = Field(..., description="Discriminator enum identifying node category")
    label: Optional[str] = Field(default=None, description="Human-readable display label")
    created_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary extensible attributes")

    model_config = ConfigDict(extra="allow", validate_assignment=True)
```

### 2.2 The 8 Concrete Node Classes

#### 1. `SourceNode` (External Document/Dataset)
Represents an external information document, archival record, peer-reviewed paper, or dataset.
```python
class SourceNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.SOURCE)
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    tier: int = Field(default=1, ge=1, le=13, description="13-tier source taxonomy (1=Primary, 13=Unverified)")
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    domain_authority: float = Field(default=0.5, ge=0.0, le=1.0)
    doi: Optional[str] = None
    peer_reviewed: bool = False
    content_sha256: str = Field(default="", description="SHA-256 hash of raw source text")
    retrieved_at_utc: Optional[str] = None
    is_sanitized: bool = True
    source_record: Optional[SourceRecord] = None
```

#### 2. `PassageNode` (Verbatim Textual Excerpt)
Represents an immutable, verbatim excerpt from a source document with exact character offsets.
```python
class PassageNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.PASSAGE)
    source_node_id: str = Field(..., min_length=1, description="ID of parent SourceNode")
    verbatim_text: str = Field(..., min_length=1, description="Exact text excerpt")
    char_offset_start: int = Field(ge=0, description="Character start offset in source document")
    char_offset_end: int = Field(ge=0, description="Character end offset in source document")
    section_or_page: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None

    @model_validator(mode="after")
    def validate_offsets(self) -> "PassageNode":
        if self.char_offset_end < self.char_offset_start:
            raise ValueError("char_offset_end must be >= char_offset_start")
        return self
```

#### 3. `EvidenceUnitNode` (Atomic Factual Proposition)
Represents a singular, atomic factual proposition extracted from a passage.
```python
class EvidenceUnitNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.EVIDENCE_UNIT)
    passage_node_id: str = Field(..., min_length=1, description="ID of parent PassageNode")
    atomic_statement: str = Field(..., min_length=1, description="Decomposed atomic fact")
    modality: ModalityType = Field(default=ModalityType.CERTAIN)
    polarity: bool = Field(default=True, description="True = affirmative statement, False = negation")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extracted_entities: List[str] = Field(default_factory=list)
```

#### 4. `ClaimNode` (Consolidated Editorial Factual Claim)
Represents an aggregated, editorialized claim tested against the evidence graph.
```python
class ClaimNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.CLAIM)
    claim_id: str = Field(..., min_length=1, description="Unique claim identifier")
    claim_text: str = Field(..., min_length=1, description="Claim proposition text")
    epistemic_status: str = Field(default="supported", description="One of 11 EpistemicStatus values")
    consensus_state: str = Field(default="STRONG_CONSENSUS", description="One of 8 ConsensusState values")
    claim_type: str = Field(default="event_fact", description="One of 8 ClaimType categories")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    category: str = Field(default="general")
    temporal_context: Dict[str, Any] = Field(default_factory=dict)
    verifier_metadata: Dict[str, Any] = Field(default_factory=dict)
    claim_record: Optional[ClaimRecord] = None
```

#### 5. `VerificationTraceNode` (Verification Audit Trail)
Records the deterministic execution details of a verification strategy on a claim or script element.
```python
class VerificationTraceNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.VERIFICATION_TRACE)
    target_node_id: str = Field(..., min_length=1, description="Target Claim or Script node")
    strategy_used: str = Field(..., min_length=1, description="e.g. SOURCE_ENTAILMENT, QUOTE_CHECK")
    entailment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    corroboration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status_assigned: str = Field(default="supported")
    consensus_state_assigned: Optional[str] = None
    verifier_name: str = Field(default="H9EpistemicVerificationEngine")
    audit_notes: str = Field(default="")
    execution_duration_ms: float = Field(default=0.0, ge=0.0)
    warnings: List[str] = Field(default_factory=list)
```

#### 6. `SceneNode` (Video Scene Timeline Container)
Represents a temporal video scene container in the script or Production IR.
```python
class SceneNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.SCENE)
    scene_id: str = Field(..., min_length=1)
    scene_index: int = Field(default=1, ge=1)
    act_index: int = Field(default=1, ge=1, le=4)
    title: str = Field(default="")
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    duration_seconds: float = Field(default=5.0, gt=0.0)
    narration_text: str = Field(default="")
    visual_theme: str = Field(default="hero_graphic")
```

#### 7. `ScriptSentenceNode` (Spoken Narration Sentence)
Represents an individual spoken sentence within a voiceover script beat.
```python
class ScriptSentenceNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.SCRIPT_SENTENCE)
    scene_id: str = Field(..., min_length=1)
    beat_id: str = Field(..., min_length=1)
    sentence_text: str = Field(..., min_length=1)
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    end_time_seconds: float = Field(default=0.0, ge=0.0)
    grounded_claim_ids: List[str] = Field(default_factory=list)
    hedging_applied: bool = False
    paraphrase_mandated: bool = False
```

#### 8. `VisualElementNode` (Rendered Visual Graphic/Parameter)
Represents an on-screen graphical block, chart, timeline, or statistic parameter in the Production IR.
```python
class VisualElementNode(GraphNode):
    node_type: GraphNodeType = Field(default=GraphNodeType.VISUAL_ELEMENT)
    scene_id: str = Field(..., min_length=1)
    block_type: str = Field(..., min_length=1, description="STATISTIC_REVEAL, TIMELINE_REVEAL, etc.")
    parameter_key: str = Field(..., min_length=1, description="stat_number, year, quote_text, etc.")
    parameter_value: Any = Field(...)
    dataset_id: Optional[str] = Field(default=None, description="Backing NumericalDataset ID")
    grounded_claim_ids: List[str] = Field(default_factory=list)
    display_unit: Optional[str] = None
```

---

## 3. Edge Taxonomy & Semantic Relations

The Evidence Graph defines 6 primary typed relations connecting nodes in the DAG:

```python
class EdgeRelation(str, Enum):
    """The 6 canonical semantic relations governing edges in the Evidence Graph."""
    ENTAILMENT = "entailment"          # Logical support (e.g. EU -> Claim, Claim -> Script)
    CONTRADICTION = "contradiction"    # Logical conflict/refutation (EU -> Claim, Claim -> Claim)
    CORROBORATION = "corroboration"    # Mutual independent confirmation (Source <-> Source, Claim <-> Claim)
    MENTIONS = "mentions"              # Script/Passage refers to a Claim/Entity without strict entailment
    DERIVES_FROM = "derives_from"      # Lineage provenance (Passage -> Source, EU -> Passage, Scene -> Beat)
    VISUAL_DEPICTION = "visual_depiction" # Visual element renders/charts a Claim or Script fact

    # Architectural provenance aliases for semantic backwards-compatibility:
    PROVIDES = "derives_from"          # Source -> Passage
    EXTRACTS_FROM = "derives_from"     # Passage -> EU
    GROUNDS = "entailment"             # Claim -> ScriptSentence
    BINDS_TO = "visual_depiction"      # Claim -> VisualElement
    TRACES_TO = "derives_from"         # Trace -> Claim
```

### 3.1 `GraphEdge` Model

```python
class GraphEdge(H9BaseModel):
    """Directed, typed, and weighted edge between two nodes."""
    edge_id: str = Field(
        default_factory=lambda: f"edge_{uuid.uuid4().hex[:12]}",
        description="Unique edge identifier"
    )
    source_id: str = Field(..., min_length=1, description="Origin node ID")
    target_id: str = Field(..., min_length=1, description="Destination node ID")
    relation: EdgeRelation = Field(..., description="Canonical edge relationship")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Strength or salience of the relationship")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Algorithmic confidence in this edge")
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 3.2 Canonical Edge Flow & Invariants

| Edge Relation | Source Node Type | Target Node Type | Description & Semantic Invariant |
|---|---|---|---|
| `DERIVES_FROM` | `SourceNode` | `PassageNode` | Ingestion: Passage is derived from raw source. |
| `DERIVES_FROM` | `PassageNode` | `EvidenceUnitNode` | Extraction: Atomic proposition extracted from passage. |
| `ENTAILMENT` | `EvidenceUnitNode` | `ClaimNode` | Support: Evidence logically entails the claim ($P \models C$). |
| `CONTRADICTION` | `EvidenceUnitNode` | `ClaimNode` | Refutation: Evidence contradicts the claim ($P \models \neg C$). Non-averaging invariant applies. |
| `CORROBORATION` | `SourceNode` / `ClaimNode` | `SourceNode` / `ClaimNode` | Cross-source corroboration between independent branches. |
| `MENTIONS` | `ScriptSentenceNode` | `ClaimNode` | Narrative reference: Script sentence mentions a claim. |
| `ENTAILMENT` | `ClaimNode` | `ScriptSentenceNode` | Grounding: Spoken voiceover directly asserts verified claim. |
| `VISUAL_DEPICTION` | `ClaimNode` / `ScriptSentenceNode` | `VisualElementNode` | Visual rendering: Graphic depicts claim/sentence data. |
| `DERIVES_FROM` | `SceneNode` | `ScriptSentenceNode` / `VisualElementNode` | Containment: Scene contains spoken sentences and visual blocks. |
| `DERIVES_FROM` | `ClaimNode` / `ScriptSentenceNode` | `VerificationTraceNode` | Audit trail: Trace records verification execution on target. |

---

## 4. DAG Algorithms & Graph Operations

### 4.1 Cycle Prevention and Detection
A core invariant of the Evidence Graph is that knowledge provenance flows forward in time and deduction without cycles: $G = (V, E)$ must be a Directed Acyclic Graph.

#### 1. Pre-Insertion Cycle Prevention (`would_create_cycle`)
Before any directed edge $(u, v)$ is added:
- If $u == v$: Adding a self-loop would create a trivial cycle of length 1. **Rejected immediately.**
- If a directed path already exists from $v$ to $u$: Adding $(u, v)$ would complete a cycle $u \to v \dots \to u$. **Rejected immediately with `CycleDetectedError`.**

```python
def would_create_cycle(self, source_id: str, target_id: str) -> bool:
    """Check if adding edge source_id -> target_id would introduce a directed cycle."""
    if source_id == target_id:
        return True
    # Fast BFS from target_id to see if source_id is reachable
    visited = set()
    queue = collections.deque([target_id])
    while queue:
        curr = queue.popleft()
        if curr == source_id:
            return True
        if curr not in visited:
            visited.add(curr)
            for neighbor in self._adjacency.get(curr, []):
                if neighbor not in visited:
                    queue.append(neighbor)
    return False
```

#### 2. Global Cycle Verification (`has_cycles`, `find_cycles`)
Uses 3-color DFS (0: White/Unvisited, 1: Gray/Visiting, 2: Black/Visited) to audit graph integrity and identify exact cycle paths for debugging.

### 4.2 Deterministic Topological Sorting
Topological sorting provides a linear ordering of vertices such that for every directed edge $(u, v)$, $u$ comes before $v$.

To preserve **prompt cache stability** and guarantee **hermetic determinism**, tie-breaking among nodes with in-degree 0 is resolved lexicographically by `node_id`.

```python
def topological_sort(self) -> List[str]:
    """Return deterministically sorted list of node IDs using Kahn's algorithm with alphanumeric tie-breaking."""
    in_degree = {nid: 0 for nid in self._nodes}
    for edge in self._edges:
        in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1

    # Deterministic priority queue: alphabetically sorted list
    ready = sorted([nid for nid, deg in in_degree.items() if deg == 0])
    ordered = []

    while ready:
        curr = ready.pop(0)
        ordered.append(curr)
        for neighbor in sorted(self._adjacency.get(curr, [])):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                # Insert keeping sorted order
                bisect.insort(ready, neighbor)

    if len(ordered) != len(self._nodes):
        raise CycleDetectedError("Graph contains a cycle; topological sort cannot be completed.")
    return ordered
```

### 4.3 Querying Claims by Status and Criteria
The Evidence Graph provides optimized indexing and query helpers for filtering claims during editorial synthesis and verification gating:

```python
def get_claims_by_status(self, status: Union[EpistemicStatus, str]) -> List[ClaimNode]:
    """Retrieve all ClaimNodes matching a specific epistemic status."""

def get_contested_claims(self) -> List[ClaimNode]:
    """Retrieve all claims flagged as 'contested'."""

def get_unsupported_claims(self) -> List[ClaimNode]:
    """Retrieve all claims flagged as 'unsupported'."""

def get_verified_claims(self) -> List[ClaimNode]:
    """Retrieve all claims verified by authoritative sources."""

def get_claims_by_consensus(self, consensus: Union[ConsensusState, str]) -> List[ClaimNode]:
    """Filter claims by historical consensus state (e.g. STRONG_CONSENSUS, ACTIVE_DEBATE)."""

def get_claims_by_type(self, claim_type: Union[ClaimType, str]) -> List[ClaimNode]:
    """Filter claims by typology (e.g. EVENT_FACT, NUMERICAL_METRIC, DIRECT_QUOTE)."""
```

### 4.4 Provenance Chain Reconstruction (Lineage Traversal)
The graph supports both backward lineage reconstruction (identifying all sources that ground a given sentence or visual chart) and forward impact analysis (identifying which scripts or charts are affected if a source is retracted or invalidated).

#### Backward Lineage (`trace_lineage`)
Traversing backwards from a target node (such as a `ScriptSentenceNode` or `VisualElementNode`) traverses upstream edges along `DERIVES_FROM`, `ENTAILMENT`, and `VISUAL_DEPICTION`:
$$\text{Target} \longleftarrow \text{ClaimNode} \longleftarrow \text{EvidenceUnitNode} \longleftarrow \text{PassageNode} \longleftarrow \text{SourceNode}$$

The result is returned as a structured `ProvenanceChain`:
```python
class ProvenanceChain(H9BaseModel):
    target_node_id: str
    target_node_type: GraphNodeType
    root_source_ids: List[str]
    root_sources: List[SourceNode]
    passages: List[PassageNode]
    evidence_units: List[EvidenceUnitNode]
    claims: List[ClaimNode]
    edges_traversed: List[GraphEdge]
    complete_paths: List[List[str]]
    is_grounded: bool
    calculated_confidence: float
```

### 4.5 Calculating Chain Confidence
Confidence calculation in the Evidence Graph reflects both serial decay along inference hops and parallel reinforcement from independent corroboration.

#### 1. Serial Chain Confidence (Conjunction along path)
For a single linear path $P = (S, P_{\text{as}}, EU, C, \dots, T)$ consisting of nodes $v_0 \dots v_k$ and edges $e_1 \dots e_k$:
$$C(P) = W_{\text{tier}}(v_0) \times \prod_{i=1}^k \left[ w(e_i) \times c(e_i) \times c(v_i) \right] \times \lambda^{k-1}$$
Where:
- $W_{\text{tier}}(v_0) \in [0.0, 1.0]$ is the source authority weight from the 13-Tier Taxonomy.
- $w(e_i), c(e_i)$ are edge weight and edge confidence.
- $c(v_i)$ is node confidence (e.g. EvidenceUnit confidence).
- $\lambda \in (0.0, 1.0]$ is the hop decay factor (default $\lambda = 0.98$).

#### 2. Bottleneck Confidence (Min-Cut Series)
$$C_{\text{bottleneck}}(P) = \min \left( W_{\text{tier}}(v_0), \min_{i=1}^k [w(e_i) \times c(e_i)], \min_{i=1}^k c(v_i) \right)$$

#### 3. Parallel Independent Corroboration (Disjunction)
When multiple independent paths $P_1, \dots, P_m$ anchor into the same claim $C$ from distinct root sources:
$$C_{\text{corrob}}(C) = 1.0 - \prod_{j=1}^m \left( 1.0 - C(P_j) \times I_{\text{indep}}(S_j, S_1) \right)$$

#### 4. Contradiction Penalty
If active incoming `CONTRADICTION` edges exist with maximum contradiction probability $P_{\text{contra}}$:
$$C_{\text{final}}(C) = \max\left(0.0, C_{\text{corrob}}(C) \times (1.0 - P_{\text{contra}})\right)$$

### 4.6 Serialization & Deserialization (Bidirectional Schema Fidelity)
The graph serializes cleanly to formatted JSON, dictionary structures, and W3C-compatible JSON-LD without external graph database dependencies:
- `to_dict() -> Dict[str, Any]`
- `from_dict(data: Dict[str, Any]) -> EvidenceGraph`
- `to_json(indent: int = 2) -> str`
- `from_json(json_str: str) -> EvidenceGraph`
- `to_jsonld() -> Dict[str, Any]` (with `@context`, `@type`, `@id`, and `@graph`)
- `from_dossier(dossier: ResearchDossier) -> EvidenceGraph` (automatic instantiation of SourceNodes, PassageNodes, EvidenceUnitNodes, and ClaimNodes from research contracts)

---

## 5. Clean Class Interfaces & Implementation Blueprint

Below is the complete, canonical implementation design for `src/epistemic/graph.py`.

```python
"""src/epistemic/graph.py — Dedicated Machine-Readable Evidence Graph Abstraction.

Implements the Directed Acyclic Graph (DAG) managing the end-to-end provenance
lineage connecting external sources, passages, atomic evidence units, consolidated
claims, verification traces, script sentences, scenes, and visual elements (Milestone M2).
"""

from __future__ import annotations

import bisect
import collections
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.contracts import (
    ClaimRecord,
    H9BaseModel,
    ResearchDossier,
    SourceRecord,
)


# ===========================================================================
# 1. Node & Edge Enums
# ===========================================================================

class GraphNodeType(str, Enum):
    """The 8 canonical node types within the Evidence Graph."""
    SOURCE = "source"
    PASSAGE = "passage"
    EVIDENCE_UNIT = "evidence_unit"
    CLAIM = "claim"
    VERIFICATION_TRACE = "verification_trace"
    SCRIPT_SENTENCE = "script_sentence"
    SCENE = "scene"
    VISUAL_ELEMENT = "visual_element"


class EdgeRelation(str, Enum):
    """The 6 canonical semantic relations governing edges in the Evidence Graph."""
    ENTAILMENT = "entailment"
    CONTRADICTION = "contradiction"
    CORROBORATION = "corroboration"
    MENTIONS = "mentions"
    DERIVES_FROM = "derives_from"
    VISUAL_DEPICTION = "visual_depiction"


class ModalityType(str, Enum):
    """Modality of an extracted evidence proposition."""
    CERTAIN = "CERTAIN"
    PROBABILISTIC = "PROBABILISTIC"
    POSSIBLE = "POSSIBLE"
    COUNTERFACTUAL = "COUNTERFACTUAL"


# ===========================================================================
# 2. Exceptions
# ===========================================================================

class EvidenceGraphError(Exception):
    """Base exception for Evidence Graph operations."""
    pass


class CycleDetectedError(EvidenceGraphError):
    """Raised when an operation would violate the DAG acyclicity invariant."""
    pass


class NodeNotFoundError(EvidenceGraphError):
    """Raised when a referenced node does not exist in the graph."""
    pass


class EdgeNotFoundError(EvidenceGraphError):
    """Raised when a referenced edge does not exist in the graph."""
    pass


class InvalidEdgeError(EvidenceGraphError):
    """Raised when edge parameters violate semantic typing or constraints."""
    pass


# ===========================================================================
# 3. Node Models
# ===========================================================================

class GraphNode(H9BaseModel):
    """Abstract base class for all nodes in the Evidence Graph."""
    node_id: str = Field(..., min_length=1, description="Globally unique identifier for the node")
    node_type: GraphNodeType = Field(..., description="Discriminator enum identifying node category")
    label: Optional[str] = Field(default=None, description="Human-readable display label")
    created_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary extensible attributes")

    model_config = ConfigDict(extra="allow", validate_assignment=True)


class SourceNode(GraphNode):
    """Represents an external information document, archival record, or dataset."""
    node_type: GraphNodeType = Field(default=GraphNodeType.SOURCE)
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    tier: int = Field(default=1, ge=1, le=13)
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    domain_authority: float = Field(default=0.5, ge=0.0, le=1.0)
    doi: Optional[str] = None
    peer_reviewed: bool = False
    content_sha256: str = Field(default="")
    retrieved_at_utc: Optional[str] = None
    is_sanitized: bool = True
    source_record: Optional[SourceRecord] = None


class PassageNode(GraphNode):
    """Represents an immutable, verbatim excerpt from a source document."""
    node_type: GraphNodeType = Field(default=GraphNodeType.PASSAGE)
    source_node_id: str = Field(..., min_length=1)
    verbatim_text: str = Field(..., min_length=1)
    char_offset_start: int = Field(default=0, ge=0)
    char_offset_end: int = Field(default=0, ge=0)
    section_or_page: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None

    @model_validator(mode="after")
    def validate_offsets(self) -> "PassageNode":
        if self.char_offset_end < self.char_offset_start:
            raise ValueError("char_offset_end must be >= char_offset_start")
        return self


class EvidenceUnitNode(GraphNode):
    """Represents an atomic, singular factual proposition extracted from a passage."""
    node_type: GraphNodeType = Field(default=GraphNodeType.EVIDENCE_UNIT)
    passage_node_id: str = Field(..., min_length=1)
    atomic_statement: str = Field(..., min_length=1)
    modality: ModalityType = Field(default=ModalityType.CERTAIN)
    polarity: bool = Field(default=True)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extracted_entities: List[str] = Field(default_factory=list)


class ClaimNode(GraphNode):
    """Represents an aggregated, editorialized claim tested against the evidence graph."""
    node_type: GraphNodeType = Field(default=GraphNodeType.CLAIM)
    claim_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    epistemic_status: str = Field(default="supported")
    consensus_state: str = Field(default="STRONG_CONSENSUS")
    claim_type: str = Field(default="event_fact")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    category: str = Field(default="general")
    temporal_context: Dict[str, Any] = Field(default_factory=dict)
    verifier_metadata: Dict[str, Any] = Field(default_factory=dict)
    claim_record: Optional[ClaimRecord] = None


class VerificationTraceNode(GraphNode):
    """Records the execution audit trail for a claim or script verification check."""
    node_type: GraphNodeType = Field(default=GraphNodeType.VERIFICATION_TRACE)
    target_node_id: str = Field(..., min_length=1)
    strategy_used: str = Field(..., min_length=1)
    entailment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    corroboration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status_assigned: str = Field(default="supported")
    consensus_state_assigned: Optional[str] = None
    verifier_name: str = Field(default="H9EpistemicVerificationEngine")
    audit_notes: str = Field(default="")
    execution_duration_ms: float = Field(default=0.0, ge=0.0)
    warnings: List[str] = Field(default_factory=list)


class SceneNode(GraphNode):
    """Represents a video scene container in the script or Production IR."""
    node_type: GraphNodeType = Field(default=GraphNodeType.SCENE)
    scene_id: str = Field(..., min_length=1)
    scene_index: int = Field(default=1, ge=1)
    act_index: int = Field(default=1, ge=1, le=4)
    title: str = Field(default="")
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    duration_seconds: float = Field(default=5.0, gt=0.0)
    narration_text: str = Field(default="")
    visual_theme: str = Field(default="hero_graphic")


class ScriptSentenceNode(GraphNode):
    """Represents an individual spoken sentence within a voiceover script beat."""
    node_type: GraphNodeType = Field(default=GraphNodeType.SCRIPT_SENTENCE)
    scene_id: str = Field(..., min_length=1)
    beat_id: str = Field(..., min_length=1)
    sentence_text: str = Field(..., min_length=1)
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    end_time_seconds: float = Field(default=0.0, ge=0.0)
    grounded_claim_ids: List[str] = Field(default_factory=list)
    hedging_applied: bool = False
    paraphrase_mandated: bool = False


class VisualElementNode(GraphNode):
    """Represents an on-screen graphical block, chart, timeline, or statistic parameter."""
    node_type: GraphNodeType = Field(default=GraphNodeType.VISUAL_ELEMENT)
    scene_id: str = Field(..., min_length=1)
    block_type: str = Field(..., min_length=1)
    parameter_key: str = Field(..., min_length=1)
    parameter_value: Any = Field(...)
    dataset_id: Optional[str] = Field(default=None)
    grounded_claim_ids: List[str] = Field(default_factory=list)
    display_unit: Optional[str] = None


# Node discriminator lookup
NODE_CLASS_MAP = {
    GraphNodeType.SOURCE: SourceNode,
    GraphNodeType.PASSAGE: PassageNode,
    GraphNodeType.EVIDENCE_UNIT: EvidenceUnitNode,
    GraphNodeType.CLAIM: ClaimNode,
    GraphNodeType.VERIFICATION_TRACE: VerificationTraceNode,
    GraphNodeType.SCENE: SceneNode,
    GraphNodeType.SCRIPT_SENTENCE: ScriptSentenceNode,
    GraphNodeType.VISUAL_ELEMENT: VisualElementNode,
}


# ===========================================================================
# 4. Edge Model
# ===========================================================================

class GraphEdge(H9BaseModel):
    """Directed, typed, and weighted edge between two nodes."""
    edge_id: str = Field(
        default_factory=lambda: f"edge_{uuid.uuid4().hex[:12]}",
        description="Unique edge identifier"
    )
    source_id: str = Field(..., min_length=1, description="Origin node ID")
    target_id: str = Field(..., min_length=1, description="Destination node ID")
    relation: EdgeRelation = Field(..., description="Canonical edge relationship")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Strength or salience of the relationship")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Algorithmic confidence in this edge")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 5. Provenance Chain Model
# ===========================================================================

class ProvenanceChain(H9BaseModel):
    """Result of a backward or forward lineage traversal."""
    target_node_id: str
    target_node_type: GraphNodeType
    root_source_ids: List[str] = Field(default_factory=list)
    root_sources: List[SourceNode] = Field(default_factory=list)
    passages: List[PassageNode] = Field(default_factory=list)
    evidence_units: List[EvidenceUnitNode] = Field(default_factory=list)
    claims: List[ClaimNode] = Field(default_factory=list)
    edges_traversed: List[GraphEdge] = Field(default_factory=list)
    complete_paths: List[List[str]] = Field(default_factory=list)
    is_grounded: bool = False
    calculated_confidence: float = 0.0


# ===========================================================================
# 6. EvidenceGraph Class
# ===========================================================================

class EvidenceGraph:
    """Directed Acyclic Graph managing grounding, evidence lineage, and verification."""

    TIER_WEIGHTS: Dict[int, float] = {
        1: 1.00,  # PRIMARY_SOURCE
        2: 0.98,  # PEER_REVIEWED_JOURNAL
        3: 0.95,  # ACADEMIC_PRESS_BOOK
        4: 0.95,  # HISTORICAL_DOCUMENT_CRITICAL_EDITION
        5: 0.92,  # GOVERNMENT_RECORD_STATISTICAL_AGENCY
        6: 0.85,  # PREPRINT_SCHOLARLY
        7: 0.88,  # SPECIALIZED_SCHOLARLY_DATABASE
        8: 0.80,  # REPUTABLE_NEWS_INVESTIGATIVE
        9: 0.65,  # GENERAL_ENCYCLOPEDIC
        10: 0.50, # CORPORATE_WHITE_PAPER
        11: 0.30, # BLOG_OPINION_COMMENTARY
        12: 0.20, # SOCIAL_MEDIA_FORUM
        13: 0.00, # UNVERIFIED
    }

    def __init__(self, graph_id: Optional[str] = None, project_id: Optional[str] = None):
        self.graph_id = graph_id or f"eg_{uuid.uuid4().hex[:12]}"
        self.project_id = project_id or ""
        self.version = "1.0.0"
        self.created_at_utc = datetime.now(timezone.utc).isoformat()
        self.metadata: Dict[str, Any] = {}

        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        self._adjacency: Dict[str, List[str]] = collections.defaultdict(list)       # source -> [targets]
        self._reverse_adjacency: Dict[str, List[str]] = collections.defaultdict(list) # target -> [sources]
        self._edge_lookup: Dict[Tuple[str, str], str] = {}                          # (source, target) -> edge_id

    # -----------------------------------------------------------------------
    # Node Management
    # -----------------------------------------------------------------------
    def add_node(self, node: GraphNode) -> str:
        """Add a validated GraphNode to the graph."""
        if node.node_id in self._nodes:
            raise ValueError(f"Node '{node.node_id}' already exists in EvidenceGraph.")
        self._nodes[node.node_id] = node
        return node.node_id

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieve a node by ID."""
        return self._nodes.get(node_id)

    def require_node(self, node_id: str) -> GraphNode:
        """Retrieve a node by ID or raise NodeNotFoundError."""
        node = self._nodes.get(node_id)
        if node is None:
            raise NodeNotFoundError(f"Node '{node_id}' not found in EvidenceGraph.")
        return node

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all incident edges."""
        if node_id not in self._nodes:
            raise NodeNotFoundError(f"Node '{node_id}' not found in EvidenceGraph.")

        # Find and remove all incident edges
        incident_edges = [
            eid for eid, edge in self._edges.items()
            if edge.source_id == node_id or edge.target_id == node_id
        ]
        for eid in incident_edges:
            self.remove_edge(eid)

        del self._nodes[node_id]

    # Specific Typed Node Adders
    def add_source(
        self,
        title: str,
        url: str,
        tier: int = 1,
        node_id: Optional[str] = None,
        publisher: Optional[str] = None,
        author: Optional[str] = None,
        published_date: Optional[str] = None,
        reliability_score: float = 0.8,
        domain_authority: float = 0.5,
        doi: Optional[str] = None,
        peer_reviewed: bool = False,
        content_sha256: str = "",
        is_sanitized: bool = True,
        source_record: Optional[SourceRecord] = None,
    ) -> str:
        nid = node_id or f"src_{uuid.uuid4().hex[:8]}"
        node = SourceNode(
            node_id=nid,
            title=title,
            url=url,
            tier=tier,
            publisher=publisher,
            author=author,
            published_date=published_date,
            reliability_score=reliability_score,
            domain_authority=domain_authority,
            doi=doi,
            peer_reviewed=peer_reviewed,
            content_sha256=content_sha256,
            is_sanitized=is_sanitized,
            source_record=source_record,
        )
        return self.add_node(node)

    def add_passage(
        self,
        source_node_id: str,
        verbatim_text: str,
        char_offset_start: int = 0,
        char_offset_end: int = 0,
        node_id: Optional[str] = None,
        section_or_page: Optional[str] = None,
    ) -> str:
        self.require_node(source_node_id)
        nid = node_id or f"pas_{uuid.uuid4().hex[:8]}"
        node = PassageNode(
            node_id=nid,
            source_node_id=source_node_id,
            verbatim_text=verbatim_text,
            char_offset_start=char_offset_start,
            char_offset_end=char_offset_end,
            section_or_page=section_or_page,
        )
        self.add_node(node)
        self.link(source_node_id, nid, EdgeRelation.DERIVES_FROM)
        return nid

    def add_evidence_unit(
        self,
        passage_node_id: str,
        atomic_statement: str,
        node_id: Optional[str] = None,
        modality: ModalityType = ModalityType.CERTAIN,
        polarity: bool = True,
        confidence: float = 1.0,
        extracted_entities: Optional[List[str]] = None,
    ) -> str:
        self.require_node(passage_node_id)
        nid = node_id or f"eu_{uuid.uuid4().hex[:8]}"
        node = EvidenceUnitNode(
            node_id=nid,
            passage_node_id=passage_node_id,
            atomic_statement=atomic_statement,
            modality=modality,
            polarity=polarity,
            confidence=confidence,
            extracted_entities=extracted_entities or [],
        )
        self.add_node(node)
        self.link(passage_node_id, nid, EdgeRelation.DERIVES_FROM)
        return nid

    def add_claim(
        self,
        claim_text: str,
        node_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        epistemic_status: str = "supported",
        consensus_state: str = "STRONG_CONSENSUS",
        claim_type: str = "event_fact",
        confidence_score: float = 0.7,
        category: str = "general",
        claim_record: Optional[ClaimRecord] = None,
    ) -> str:
        cid = claim_id or node_id or f"claim_{uuid.uuid4().hex[:8]}"
        node = ClaimNode(
            node_id=cid,
            claim_id=cid,
            claim_text=claim_text,
            epistemic_status=epistemic_status,
            consensus_state=consensus_state,
            claim_type=claim_type,
            confidence_score=confidence_score,
            category=category,
            claim_record=claim_record,
        )
        return self.add_node(node)

    # -----------------------------------------------------------------------
    # Edge Management & Cycle Prevention
    # -----------------------------------------------------------------------
    def would_create_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding edge source_id -> target_id would introduce a directed cycle."""
        if source_id == target_id:
            return True
        visited = set()
        queue = collections.deque([target_id])
        while queue:
            curr = queue.popleft()
            if curr == source_id:
                return True
            if curr not in visited:
                visited.add(curr)
                for neighbor in self._adjacency.get(curr, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
        return False

    def link(
        self,
        source_id: str,
        target_id: str,
        relation: Union[EdgeRelation, str],
        weight: float = 1.0,
        confidence: float = 1.0,
        edge_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Creates a directed, typed edge; asserts existence and acyclicity."""
        self.require_node(source_id)
        self.require_node(target_id)

        # Normalize relation enum
        if isinstance(relation, str):
            try:
                rel_enum = EdgeRelation(relation.lower())
            except ValueError:
                # Handle provenance aliases
                mapping = {
                    "provides": EdgeRelation.DERIVES_FROM,
                    "extracts_from": EdgeRelation.DERIVES_FROM,
                    "grounds": EdgeRelation.ENTAILMENT,
                    "binds_to": EdgeRelation.VISUAL_DEPICTION,
                    "traces_to": EdgeRelation.DERIVES_FROM,
                }
                rel_enum = mapping.get(relation.lower(), EdgeRelation.DERIVES_FROM)
        else:
            rel_enum = relation

        # Cycle detection
        if self.would_create_cycle(source_id, target_id):
            raise CycleDetectedError(
                f"Adding directed edge '{source_id}' -> '{target_id}' with relation '{rel_enum.value}' "
                f"creates a cycle in EvidenceGraph '{self.graph_id}'."
            )

        eid = edge_id or f"edge_{uuid.uuid4().hex[:12]}"
        edge = GraphEdge(
            edge_id=eid,
            source_id=source_id,
            target_id=target_id,
            relation=rel_enum,
            weight=weight,
            confidence=confidence,
            metadata=metadata or {},
        )

        self._edges[eid] = edge
        self._adjacency[source_id].append(target_id)
        self._reverse_adjacency[target_id].append(source_id)
        self._edge_lookup[(source_id, target_id)] = eid
        return eid

    def remove_edge(self, edge_id: str) -> None:
        """Remove an edge by ID."""
        edge = self._edges.get(edge_id)
        if not edge:
            raise EdgeNotFoundError(f"Edge '{edge_id}' not found in EvidenceGraph.")

        src, tgt = edge.source_id, edge.target_id
        if tgt in self._adjacency[src]:
            self._adjacency[src].remove(tgt)
        if src in self._reverse_adjacency[tgt]:
            self._reverse_adjacency[tgt].remove(src)
        self._edge_lookup.pop((src, tgt), None)
        del self._edges[edge_id]

    def get_edge(self, source_id: str, target_id: str) -> Optional[GraphEdge]:
        """Look up edge by source and target IDs."""
        eid = self._edge_lookup.get((source_id, target_id))
        return self._edges.get(eid) if eid else None

    # -----------------------------------------------------------------------
    # DAG Algorithms: Cycle Checking & Topological Sort
    # -----------------------------------------------------------------------
    def has_cycles(self) -> bool:
        """Global check for directed cycles in the graph."""
        visited: Dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=visited
        for nid in self._nodes:
            visited[nid] = 0

        def dfs(u: str) -> bool:
            visited[u] = 1
            for v in self._adjacency.get(u, []):
                if visited.get(v, 0) == 1:
                    return True
                if visited.get(v, 0) == 0 and dfs(v):
                    return True
            visited[u] = 2
            return False

        for nid in self._nodes:
            if visited[nid] == 0:
                if dfs(nid):
                    return True
        return False

    def topological_sort(self) -> List[str]:
        """Return deterministically sorted list of node IDs using Kahn's algorithm."""
        in_degree = {nid: 0 for nid in self._nodes}
        for edge in self._edges.values():
            in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1

        ready = sorted([nid for nid, deg in in_degree.items() if deg == 0])
        ordered = []

        while ready:
            curr = ready.pop(0)
            ordered.append(curr)
            for neighbor in sorted(self._adjacency.get(curr, [])):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    bisect.insort(ready, neighbor)

        if len(ordered) != len(self._nodes):
            raise CycleDetectedError("Graph contains a cycle; topological sort cannot be completed.")
        return ordered

    # -----------------------------------------------------------------------
    # Querying Operations
    # -----------------------------------------------------------------------
    def get_claims(
        self,
        status: Optional[Union[str, Any]] = None,
        consensus: Optional[Union[str, Any]] = None,
        claim_type: Optional[Union[str, Any]] = None,
    ) -> List[ClaimNode]:
        """Filter ClaimNodes by status, consensus, or claim type."""
        status_val = status.value if hasattr(status, "value") else status
        consensus_val = consensus.value if hasattr(consensus, "value") else consensus
        type_val = claim_type.value if hasattr(claim_type, "value") else claim_type

        claims = []
        for node in self._nodes.values():
            if isinstance(node, ClaimNode):
                if status_val and node.epistemic_status != status_val:
                    continue
                if consensus_val and node.consensus_state != consensus_val:
                    continue
                if type_val and node.claim_type != type_val:
                    continue
                claims.append(node)
        return claims

    def get_claims_by_status(self, status: Union[str, Any]) -> List[ClaimNode]:
        return self.get_claims(status=status)

    def get_contested_claims(self) -> List[ClaimNode]:
        return self.get_claims(status="contested")

    def get_unsupported_claims(self) -> List[ClaimNode]:
        return self.get_claims(status="unsupported")

    def get_verified_claims(self) -> List[ClaimNode]:
        return self.get_claims(status="verified")

    def get_claims_by_consensus(self, consensus: Union[str, Any]) -> List[ClaimNode]:
        return self.get_claims(consensus=consensus)

    def get_claims_by_type(self, claim_type: Union[str, Any]) -> List[ClaimNode]:
        return self.get_claims(claim_type=claim_type)

    # -----------------------------------------------------------------------
    # Provenance Lineage & Chain Reconstruction
    # -----------------------------------------------------------------------
    def trace_lineage(self, target_node_id: str) -> ProvenanceChain:
        """Traverses backward from target node to find all root SourceNodes and complete paths."""
        target = self.require_node(target_node_id)
        
        # Backward traversal finding all paths to root sources
        all_paths: List[List[str]] = []
        
        def find_paths(curr: str, current_path: List[str]):
            parents = self._reverse_adjacency.get(curr, [])
            if not parents:
                all_paths.append(list(reversed(current_path)))
                return
            for p in parents:
                find_paths(p, current_path + [p])

        find_paths(target_node_id, [target_node_id])

        # Collect unique nodes and edges in the lineage
        all_node_ids = set()
        for p in all_paths:
            all_node_ids.update(p)

        root_source_ids = []
        root_sources = []
        passages = []
        evidence_units = []
        claims = []

        for nid in all_node_ids:
            node = self._nodes[nid]
            if isinstance(node, SourceNode):
                root_source_ids.append(nid)
                root_sources.append(node)
            elif isinstance(node, PassageNode):
                passages.append(node)
            elif isinstance(node, EvidenceUnitNode):
                evidence_units.append(node)
            elif isinstance(node, ClaimNode):
                claims.append(node)

        # Collect edges traversed
        edges_traversed = []
        for p in all_paths:
            for i in range(len(p) - 1):
                edge = self.get_edge(p[i], p[i+1])
                if edge and edge not in edges_traversed:
                    edges_traversed.append(edge)

        is_grounded = len(root_sources) > 0
        calculated_conf = self.calculate_chain_confidence(target_node_id)

        return ProvenanceChain(
            target_node_id=target_node_id,
            target_node_type=target.node_type,
            root_source_ids=root_source_ids,
            root_sources=root_sources,
            passages=passages,
            evidence_units=evidence_units,
            claims=claims,
            edges_traversed=edges_traversed,
            complete_paths=all_paths,
            is_grounded=is_grounded,
            calculated_confidence=calculated_conf,
        )

    def get_root_sources(self, node_id: str) -> List[SourceNode]:
        """Return all ancestor SourceNodes for the given node."""
        chain = self.trace_lineage(node_id)
        return chain.root_sources

    def extract_subgraph(self, node_ids: Set[str]) -> "EvidenceGraph":
        """Extract an isolated sub-EvidenceGraph consisting of specified nodes and interconnecting edges."""
        sub = EvidenceGraph(
            graph_id=f"{self.graph_id}_sub_{uuid.uuid4().hex[:6]}",
            project_id=self.project_id
        )
        for nid in node_ids:
            if nid in self._nodes:
                sub.add_node(self._nodes[nid])
        for edge in self._edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                sub.link(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    relation=edge.relation,
                    weight=edge.weight,
                    confidence=edge.confidence,
                    edge_id=edge.edge_id,
                    metadata=edge.metadata,
                )
        return sub

    # -----------------------------------------------------------------------
    # Chain Confidence Calculation
    # -----------------------------------------------------------------------
    def calculate_chain_confidence(
        self,
        target_node_id: str,
        hop_decay: float = 0.98,
        method: str = "probabilistic",
    ) -> float:
        """Calculates epistemic confidence for a target node using multi-path corroboration and tier weights."""
        target = self.require_node(target_node_id)

        # If target itself is a SourceNode
        if isinstance(target, SourceNode):
            return self.TIER_WEIGHTS.get(target.tier, 0.5) * target.reliability_score

        # Find all paths leading from root sources to target
        paths: List[List[str]] = []
        def dfs_paths(curr: str, path: List[str]):
            parents = self._reverse_adjacency.get(curr, [])
            if not parents:
                paths.append(list(reversed(path)))
                return
            for p in parents:
                dfs_paths(p, path + [p])

        dfs_paths(target_node_id, [target_node_id])

        if not paths:
            return 0.0

        path_confidences: List[float] = []

        for p in paths:
            root_node = self._nodes[p[0]]
            if isinstance(root_node, SourceNode):
                root_weight = self.TIER_WEIGHTS.get(root_node.tier, 0.5) * root_node.reliability_score
            else:
                root_weight = 0.5

            if method == "bottleneck":
                b_conf = root_weight
                for i in range(len(p) - 1):
                    edge = self.get_edge(p[i], p[i+1])
                    if edge:
                        b_conf = min(b_conf, edge.weight * edge.confidence)
                    node = self._nodes[p[i+1]]
                    if hasattr(node, "confidence"):
                        b_conf = min(b_conf, getattr(node, "confidence"))
                path_confidences.append(b_conf)
            else:
                # Default: Probabilistic multiplicative chain with hop decay
                score = root_weight
                hops = len(p) - 1
                for i in range(hops):
                    edge = self.get_edge(p[i], p[i+1])
                    if edge:
                        score *= (edge.weight * edge.confidence)
                    node = self._nodes[p[i+1]]
                    if hasattr(node, "confidence"):
                        score *= getattr(node, "confidence")
                score *= (hop_decay ** max(0, hops - 1))
                path_confidences.append(score)

        # Parallel branches combination (Noisy-OR)
        # S_corrob = 1.0 - prod(1.0 - score_i)
        prod = 1.0
        for conf in path_confidences:
            prod *= (1.0 - max(0.0, min(1.0, conf)))
        combined_confidence = 1.0 - prod

        # Check for active contradiction penalties
        contradiction_penalty = 0.0
        for p in self._reverse_adjacency.get(target_node_id, []):
            edge = self.get_edge(p, target_node_id)
            if edge and edge.relation == EdgeRelation.CONTRADICTION:
                contradiction_penalty = max(contradiction_penalty, edge.weight * edge.confidence)

        final_confidence = max(0.0, combined_confidence - contradiction_penalty)
        return round(final_confidence, 4)

    # -----------------------------------------------------------------------
    # Serialization & Reconstruction
    # -----------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire graph to standardized dictionary representation."""
        nodes_grouped: Dict[str, List[Dict[str, Any]]] = {
            "sources": [],
            "passages": [],
            "evidence_units": [],
            "claims": [],
            "verification_traces": [],
            "script_sentences": [],
            "scenes": [],
            "visual_elements": [],
        }

        for node in self._nodes.values():
            key = f"{node.node_type.value}s"
            if key in nodes_grouped:
                nodes_grouped[key].append(node.to_dict())
            else:
                nodes_grouped.setdefault("other", []).append(node.to_dict())

        return {
            "graph_id": self.graph_id,
            "project_id": self.project_id,
            "version": self.version,
            "created_at_utc": self.created_at_utc,
            "metadata": self.metadata,
            "nodes": nodes_grouped,
            "edges": [e.to_dict() for e in self._edges.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceGraph":
        """Instantiate EvidenceGraph from dictionary."""
        graph = cls(
            graph_id=data.get("graph_id"),
            project_id=data.get("project_id"),
        )
        graph.version = data.get("version", "1.0.0")
        graph.created_at_utc = data.get("created_at_utc", datetime.now(timezone.utc).isoformat())
        graph.metadata = data.get("metadata", {})

        nodes_data = data.get("nodes", {})
        if isinstance(nodes_data, dict):
            for group_key, items in nodes_data.items():
                for item in items:
                    ntype_str = item.get("node_type")
                    if ntype_str:
                        ntype = GraphNodeType(ntype_str)
                        node_cls = NODE_CLASS_MAP.get(ntype, GraphNode)
                        graph.add_node(node_cls.from_dict(item))
        elif isinstance(nodes_data, list):
            for item in nodes_data:
                ntype_str = item.get("node_type")
                if ntype_str:
                    ntype = GraphNodeType(ntype_str)
                    node_cls = NODE_CLASS_MAP.get(ntype, GraphNode)
                    graph.add_node(node_cls.from_dict(item))

        for edge_data in data.get("edges", []):
            graph.link(
                source_id=edge_data["source_id"],
                target_id=edge_data["target_id"],
                relation=edge_data["relation"],
                weight=edge_data.get("weight", 1.0),
                confidence=edge_data.get("confidence", 1.0),
                edge_id=edge_data.get("edge_id"),
                metadata=edge_data.get("metadata", {}),
            )

        return graph

    def to_json(self, indent: int = 2) -> str:
        """Serialize graph to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "EvidenceGraph":
        """Deserialize model from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_jsonld(self) -> Dict[str, Any]:
        """Convert graph to W3C-compatible JSON-LD format."""
        doc = self.to_dict()
        doc["@context"] = {
            "@vocab": "https://harness9.io/ns/epistemic#",
            "SourceNode": "https://harness9.io/ns/epistemic#SourceNode",
            "ClaimNode": "https://harness9.io/ns/epistemic#ClaimNode",
            "derives_from": {"@type": "@id"},
            "entails": {"@type": "@id"},
            "contradicts": {"@type": "@id"},
        }
        doc["@type"] = "EvidenceGraph"
        doc["@id"] = f"urn:h9:graph:{self.graph_id}"
        return doc

    @classmethod
    def from_dossier(cls, dossier: ResearchDossier, graph_id: Optional[str] = None) -> "EvidenceGraph":
        """Construct a hermetic EvidenceGraph offline from a structured ResearchDossier."""
        graph = cls(
            graph_id=graph_id or f"eg_{dossier.run_id or uuid.uuid4().hex[:8]}",
            project_id=dossier.run_id,
        )
        source_cache: Dict[str, str] = {}

        for claim in dossier.claims:
            # Add or reuse primary source
            src_key = claim.primary_source.url or claim.primary_source.title
            if src_key not in source_cache:
                s_id = graph.add_source(
                    title=claim.primary_source.title,
                    url=claim.primary_source.url,
                    publisher=claim.primary_source.publisher,
                    author=claim.primary_source.author,
                    published_date=claim.primary_source.published_date,
                    reliability_score=claim.primary_source.reliability_score,
                    source_record=claim.primary_source,
                )
                source_cache[src_key] = s_id
            primary_src_id = source_cache[src_key]

            # Add Passage & Evidence Unit for primary source
            pas_id = graph.add_passage(
                source_node_id=primary_src_id,
                verbatim_text=claim.claim_text,
            )
            eu_id = graph.add_evidence_unit(
                passage_node_id=pas_id,
                atomic_statement=claim.claim_text,
                confidence=claim.confidence_score,
            )

            # Add Claim Node
            claim_node_id = graph.add_claim(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                category=claim.category,
                confidence_score=claim.confidence_score,
                claim_record=claim,
            )
            graph.link(eu_id, claim_node_id, EdgeRelation.ENTAILMENT, weight=1.0)

            # Add Corroborating sources
            for corrob_src in claim.corroborating_sources:
                c_key = corrob_src.url or corrob_src.title
                if c_key not in source_cache:
                    cs_id = graph.add_source(
                        title=corrob_src.title,
                        url=corrob_src.url,
                        publisher=corrob_src.publisher,
                        author=corrob_src.author,
                        published_date=corrob_src.published_date,
                        reliability_score=corrob_src.reliability_score,
                        source_record=corrob_src,
                    )
                    source_cache[c_key] = cs_id
                corrob_src_id = source_cache[c_key]

                cpas_id = graph.add_passage(
                    source_node_id=corrob_src_id,
                    verbatim_text=claim.claim_text,
                )
                ceu_id = graph.add_evidence_unit(
                    passage_node_id=cpas_id,
                    atomic_statement=claim.claim_text,
                    confidence=corrob_src.reliability_score,
                )
                graph.link(ceu_id, claim_node_id, EdgeRelation.ENTAILMENT, weight=corrob_src.reliability_score)
                # Link source corroboration edge
                graph.link(primary_src_id, corrob_src_id, EdgeRelation.CORROBORATION)

        return graph
```

---

## 6. Detailed Test Suite Design for `tests/test_evidence_graph.py`

The test suite is structured into 10 cohesive test classes verifying all invariants, algorithms, and integration contracts.

```
tests/test_evidence_graph.py
├── TestGraphNodeModels                  (Node validation, schemas, offsets)
├── TestGraphEdgeModels                  (Edge validation, relations, weights)
├── TestEvidenceGraphDAGInvariants       (Cycle detection, self-loops, diamond graphs)
├── TestTopologicalSort                  (Kahn's sort, deterministic tie-breaking)
├── TestGraphQuerying                    (Status filtering, consensus, type queries)
├── TestLineageReconstruction            (Backward traversal, ungrounded detection)
├── TestChainConfidenceCalculations      (Series decay, Noisy-OR parallel, contradiction penalty)
├── TestSerializationAndRoundtrip        (JSON/dict roundtrip, JSON-LD)
├── TestResearchDossierIntegration       (Reconstruction from ResearchDossier)
└── TestGraphMutationAndCascades         (Node deletion cascade, edge deletion)
```

### 6.1 Test Class 1: `TestGraphNodeModels`
- `test_source_node_creation_and_defaults()`:
  - Asserts `tier` defaults to 1, `reliability_score` bounded in [0.0, 1.0].
  - Tests invalid tiers (< 1 or > 13) raise `ValidationError`.
  - Verifies SHA-256 field and sanitization flag.
- `test_passage_node_char_offsets()`:
  - Verifies `char_offset_start <= char_offset_end`.
  - Tests that `char_offset_end < char_offset_start` raises `ValidationError`.
- `test_evidence_unit_node_modalities_and_polarity()`:
  - Verifies `ModalityType` values (`CERTAIN`, `PROBABILISTIC`, `POSSIBLE`, `COUNTERFACTUAL`).
  - Verifies `polarity` (boolean).
- `test_claim_node_attributes()`:
  - Verifies `epistemic_status`, `consensus_state`, `claim_type`.
- `test_verification_trace_node()`:
  - Verifies audit metrics: `entailment_score`, `contradiction_score`, `strategy_used`.
- `test_script_sentence_and_scene_nodes()`:
  - Verifies sentence timing: `start_time_seconds`, `end_time_seconds`.
  - Verifies scene indices: `scene_index`, `act_index` (bounded 1-4).
- `test_visual_element_node()`:
  - Verifies `block_type`, `parameter_key`, `parameter_value`, and optional `dataset_id`.

### 6.2 Test Class 2: `TestGraphEdgeModels`
- `test_edge_relation_enum_coverage()`:
  - Asserts all 6 relations exist: `ENTAILMENT`, `CONTRADICTION`, `CORROBORATION`, `MENTIONS`, `DERIVES_FROM`, `VISUAL_DEPICTION`.
- `test_edge_weights_and_confidence()`:
  - Verifies `weight` and `confidence` bounded in [0.0, 1.0].
- `test_edge_alias_normalization()`:
  - Asserts string inputs like `"provides"`, `"grounds"`, `"binds_to"` normalize to valid `EdgeRelation` enums.

### 6.3 Test Class 3: `TestEvidenceGraphDAGInvariants`
- `test_add_node_duplicate_rejection()`:
  - Adding a node with an existing `node_id` raises `ValueError`.
- `test_link_nonexistent_nodes_rejection()`:
  - Linking nodes where source or target does not exist raises `NodeNotFoundError`.
- `test_self_loop_rejection()`:
  - `graph.link("node_a", "node_a", EdgeRelation.DERIVES_FROM)` raises `CycleDetectedError`.
- `test_direct_2_node_cycle_rejection()`:
  - `A -> B` followed by `B -> A` raises `CycleDetectedError`.
- `test_multi_hop_cycle_rejection()`:
  - `A -> B -> C -> D` followed by `D -> A` raises `CycleDetectedError`.
- `test_diamond_dag_allowed()`:
  - A valid DAG with a diamond pattern:
    ```
        A
       / \
      B   C
       \ /
        D
    ```
  - Adding `B -> D` and `C -> D` must succeed and NOT be falsely flagged as a cycle.

### 6.4 Test Class 4: `TestTopologicalSort`
- `test_topological_sort_linear_chain()`:
  - For `A -> B -> C`, sort returns `["A", "B", "C"]`.
- `test_topological_sort_diamond()`:
  - For diamond DAG, `A` precedes `B` and `C`, and `B` and `C` precede `D`.
- `test_deterministic_tie_breaking()`:
  - Given independent nodes with equal in-degrees (`node_Z`, `node_A`, `node_M`), topological sort returns them in strictly alphabetical order `["node_A", "node_M", "node_Z"]`.
  - Adding nodes in different orders produces identical topological output.

### 6.5 Test Class 5: `TestGraphQuerying`
- `test_get_claims_by_status()`:
  - Adding claims with statuses `verified`, `contested`, `unsupported`, `supported`.
  - Verifies filtering by status returns exactly the matching claims.
- `test_get_contested_claims()`:
  - Returns all claims marked as contested.
- `test_get_claims_by_consensus()`:
  - Filter by `STRONG_CONSENSUS`, `ACTIVE_DEBATE`, `CONTESTED`.
- `test_get_claims_by_type()`:
  - Filter by `EVENT_FACT`, `NUMERICAL_METRIC`, `DIRECT_QUOTE`.

### 6.6 Test Class 6: `TestLineageReconstruction`
- `test_trace_lineage_complete_forward_flow()`:
  - Setup: `Source -> Passage -> EvidenceUnit -> Claim -> ScriptSentence`.
  - `chain = graph.trace_lineage(sent_id)`.
  - Asserts `chain.is_grounded is True`.
  - Asserts `chain.root_source_ids == [src_id]`.
  - Asserts `chain.complete_paths` contains the exact 5-hop path.
- `test_trace_lineage_visual_element()`:
  - Setup: `Source -> Passage -> EvidenceUnit -> Claim -> VisualElement`.
  - Verifies lineage back to source.
- `test_ungrounded_proposition_detection()`:
  - A `ScriptSentenceNode` added without any incoming edges has `chain.is_grounded is False`, `root_sources == []`.

### 6.7 Test Class 7: `TestChainConfidenceCalculations`
- `test_single_path_tier_weighted_confidence()`:
  - Path from Tier 1 Source ($W_{\text{tier}} = 1.0$) vs Tier 8 Source ($W_{\text{tier}} = 0.8$) vs Tier 13 Source ($W_{\text{tier}} = 0.0$).
  - Tier 13 source results in `confidence == 0.0`.
- `test_multi_path_parallel_corroboration()`:
  - Single path confidence = 0.70.
  - Two independent corroborating paths: combined confidence $> 0.70$ (via Noisy-OR: $1 - (1-0.7)^2 = 0.91$).
- `test_contradiction_penalty_degradation()`:
  - Claim with corroboration confidence = 0.85.
  - Add incoming `CONTRADICTION` edge with weight 0.80.
  - Final confidence degrades to $\approx 0.05$ (or drops significantly).
- `test_bottleneck_confidence_calculation()`:
  - Series path with weights [1.0, 0.9, 0.4, 0.95].
  - Bottleneck method returns `0.40`.

### 6.8 Test Class 8: `TestSerializationAndRoundtrip`
- `test_dictionary_roundtrip()`:
  - Create graph with all 8 node types and 6 edge relations.
  - `data = graph.to_dict()`
  - `restored = EvidenceGraph.from_dict(data)`
  - Asserts node count, edge count, node attributes, and edge relations are identical.
- `test_json_roundtrip()`:
  - `json_str = graph.to_json()`
  - `restored = EvidenceGraph.from_json(json_str)`
  - Asserts full structural equality.
- `test_jsonld_structure()`:
  - Asserts `@context`, `@type`, `@id` are present in `to_jsonld()`.

### 6.9 Test Class 9: `TestResearchDossierIntegration`
- `test_from_dossier_reconstruction()`:
  - Instantiate a realistic `ResearchDossier` with primary and corroborating sources.
  - Call `EvidenceGraph.from_dossier(dossier)`.
  - Verifies `SourceNode`, `PassageNode`, `EvidenceUnitNode`, and `ClaimNode` were automatically instantiated.
  - Verifies `ENTAILMENT` edges link EUs to claims.
  - Verifies `CORROBORATION` edges link primary and corroborating sources.

### 6.10 Test Class 10: `TestGraphMutationAndCascades`
- `test_remove_node_cascades_edges()`:
  - Setup: `A -> B -> C`.
  - Remove node `B`.
  - Node `B` is deleted; edge `A -> B` and edge `B -> C` are deleted.
  - `A` and `C` remain in the graph.
- `test_remove_edge()`:
  - Removing an edge updates `_adjacency` and `_reverse_adjacency`.

---

## 7. Integration Recommendation & Next Steps for Milestone M2

1. **Implement `src/epistemic/graph.py`**:
   The implementer should create `src/epistemic/graph.py` following the blueprint in Section 5. Ensure `src/epistemic/__init__.py` exposes `EvidenceGraph`, all 8 node models, `GraphEdge`, `EdgeRelation`, and `CycleDetectedError`.
2. **Implement `tests/test_evidence_graph.py`**:
   Write the complete test suite adhering to Section 6.
3. **Connect with `src/models/contracts.py`**:
   Ensure `ClaimRecord` and `SourceRecord` in `src/models/contracts.py` seamlessly convert to and from `ClaimNode` and `SourceNode`.
4. **Fix Circular Import in `src/h9_runtime/content.py`**:
   As noted in `PROJECT.md` M2 scope, make `from src.orchestrator.pipeline import Pipeline` a lazy import inside methods that use it, ensuring `tests/test_state_machine.py` passes cleanly in isolation.
