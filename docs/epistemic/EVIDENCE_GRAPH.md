# Evidence Graph Specification & Provenance DAG: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/epistemic/`, `src/models/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/epistemic/FACT_CHECKING_SPEC.md`  

---

## 1. Executive Summary & Graph-Grounded Knowledge

The **Harness 9 Evidence Graph** is a machine-readable, directed acyclic grounding graph (DAG) that models the end-to-end lineage of factual assertions across video production. It connects raw external sources to extracted textual passages, atomic evidence units, consolidated claims, verification traces, spoken script sentences, and rendered visual IR components.

In conventional pipelines, facts exist as flat, decoupled strings in JSON dictionaries. When a scriptwriter alters a phrase or a visual engine renders a chart, the connection to the original source document is severed. The Evidence Graph maintains an unbroken, cryptographically verifiable chain of provenance: from the exact character offsets in a primary archival document all the way to the individual pixels on screen and spoken words in the audio waveform.

---

## 2. Graph Topology & Node/Edge Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SOURCE LAYER                                    │
│  [SourceNode] (SourceRecord: Tier 1–13, URL, DOI, SHA-256, Sanitized)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (PROVIDES)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PASSAGE LAYER                                   │
│  [PassageNode] (Verbatim Text, Char Start/End Offsets, Page/Section)         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (EXTRACTS_FROM)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EVIDENCE UNIT LAYER                                │
│  [EvidenceUnitNode] (Atomic Proposition, Modality, Polarity, Confidence)    │
└───────────────────┬─────────────────────────────────────┬───────────────────┘
                    │ (ENTAILS)                           │ (CONTRADICTS)
                    ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLAIM LAYER                                    │
│  [ClaimNode] (ClaimRecord: EpistemicStatus, ConsensusState, ClaimType)      │
└───────────────────┬─────────────────────────────────────┬───────────────────┘
                    │                                     │
                    │ (GROUNDS)                           │ (BINDS_TO)
                    ▼                                     ▼
┌──────────────────────────────────────┐ ┌────────────────────────────────────┐
│          SCRIPT BEAT LAYER           │ │        VISUAL ELEMENT LAYER        │
│  [ScriptSentenceNode]                │ │  [VisualElementNode]               │
│  • Beat ID, Start/End Time           │ │  • IR Visual Block: STATISTIC, ... │
│  • Spoken Voiceover Text             │ │  • Parameters: stat_number, year   │
└───────────────────┬──────────────────┘ └─────────────────┬──────────────────┘
                    │                                      │
                    └───────────────────┬──────────────────┘
                                        │ (TRACES_TO)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERIFICATION TRACE LAYER                            │
│  [VerificationTraceNode] (Strategy, Entailment Score, Verifier, Timestamp) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Node Hierarchy & Schema Definitions

All nodes inherit from `EvidenceGraphNode` and enforce strict Pydantic v2 validation:

### 3.1 `SourceNode`
Represents an external information document, archival file, or dataset.
```python
class SourceNode(H9BaseModel):
    node_id: str = Field(..., min_length=1)      # e.g. "src_bell_labs_1947"
    source_record: SourceRecord
    content_sha256: str = Field(..., min_length=64, max_length=64)
    retrieved_at: str
    is_sanitized: bool = True
```

### 3.2 `PassageNode`
Represents an immutable, verbatim excerpt from a source document.
```python
class PassageNode(H9BaseModel):
    node_id: str = Field(..., min_length=1)      # e.g. "pas_bardeen_lab_p42"
    source_node_id: str = Field(..., min_length=1)
    verbatim_text: str = Field(..., min_length=1)
    char_offset_start: int = Field(ge=0)
    char_offset_end: int = Field(ge=0)
    section_or_page: Optional[str] = None
```

### 3.3 `EvidenceUnitNode`
Represents an atomic, singular factual proposition extracted from a passage.
```python
class ModalityType(str, Enum):
    CERTAIN = "CERTAIN"
    PROBABILISTIC = "PROBABILISTIC"
    POSSIBLE = "POSSIBLE"
    COUNTERFACTUAL = "COUNTERFACTUAL"

class EvidenceUnitNode(H9BaseModel):
    node_id: str = Field(..., min_length=1)      # e.g. "eu_transistor_invention_date"
    passage_node_id: str = Field(..., min_length=1)
    atomic_statement: str = Field(..., min_length=1)
    modality: ModalityType = ModalityType.CERTAIN
    polarity: bool = True                        # True = affirmative, False = negative
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
```

### 3.4 `ClaimNode`
Represents an aggregated factual claim used by editorial and scriptwriting engines.
```python
class ClaimNode(H9BaseModel):
    node_id: str = Field(..., min_length=1)      # e.g. "claim_001"
    claim_record: ClaimRecord
    epistemic_status: EpistemicStatus
    consensus_state: ConsensusState
    claim_type: ClaimType
```

### 3.5 `ScriptSentenceNode`
Represents an individual sentence within a generated voiceover script beat.
```python
class ScriptSentenceNode(H9BaseModel):
    node_id: str = Field(..., min_length=1)      # e.g. "sent_scene1_beat1"
    scene_id: str
    beat_id: str
    sentence_text: str
    start_time_seconds: float
    end_time_seconds: float
    grounded_claim_ids: List[str] = Field(default_factory=list)
```

### 3.6 `VisualElementNode`
Represents an on-screen graphical element, chart, or animation parameter in the Production IR.
```python
class VisualElementNode(H9BaseModel):
    node_id: str = Field(..., min_length=1)      # e.g. "vis_stat_reveal_01"
    scene_id: str
    block_type: str                              # STATISTIC_REVEAL, TIMELINE_REVEAL, etc.
    parameter_key: str                           # "stat_number", "year", "quote_text"
    parameter_value: Any
    dataset_id: Optional[str] = None
    grounded_claim_ids: List[str] = Field(default_factory=list)
```

### 3.7 `VerificationTraceNode`
Records the deterministic audit trail for a claim or script verification execution.
```python
class VerificationTraceNode(H9BaseModel):
    node_id: str = Field(..., min_length=1)
    target_node_id: str                          # ClaimNode ID or ScriptSentenceNode ID
    strategy_used: str                           # SOURCE_ENTAILMENT, QUOTE_CHECK, etc.
    entailment_score: float
    contradiction_score: float
    verifier_name: str
    timestamp_utc: str
    audit_notes: str
```

---

## 4. Edge Types & Formal Semantics

Edges in the Evidence Graph are directed and typed:

```python
class EdgeRelation(str, Enum):
    PROVIDES = "PROVIDES"              # SourceNode -> PassageNode
    EXTRACTS_FROM = "EXTRACTS_FROM"    # PassageNode -> EvidenceUnitNode
    ENTAILS = "ENTAILS"                # EvidenceUnitNode -> ClaimNode
    CONTRADICTS = "CONTRADICTS"        # EvidenceUnitNode -> ClaimNode
    HEDGES = "HEDGES"                  # EvidenceUnitNode -> ClaimNode
    GROUNDS = "GROUNDS"                # ClaimNode -> ScriptSentenceNode
    BINDS_TO = "BINDS_TO"              # ClaimNode -> VisualElementNode
    TRACES_TO = "TRACES_TO"            # VerificationTraceNode -> ClaimNode
```

### Formal Edge Invariants:
1. **Entailment Monotonicity**: If an edge $(EU, C)$ has type `ENTAILS` with weight $w \ge 0.90$ and no active `CONTRADICTS` edges exist, $C$ must transition to `SUPPORTED` or `VERIFIED`.
2. **Contradiction Preservation**: If an edge $(EU_1, C)$ has type `ENTAILS` and edge $(EU_2, C)$ has type `CONTRADICTS`, the graph forbids deleting either edge. The claim $C$ transitions to `CONTESTED` or `ACTIVE_DEBATE`.
3. **Traceability Closure**: For every `ScriptSentenceNode` asserting a factual proposition, there must exist a directed path:
   $$\text{SourceNode} \xrightarrow{\text{PROVIDES}} \text{PassageNode} \xrightarrow{\text{EXTRACTS}} \text{EvidenceUnitNode} \xrightarrow{\text{ENTAILS}} \text{ClaimNode} \xrightarrow{\text{GROUNDS}} \text{ScriptSentenceNode}$$
   If no such path exists, the sentence is flagged as `UNGROUNDED_PROPOSITION`.

---

## 5. Directed Acyclic Graph (DAG) Invariants & Integrity

1. **Acyclicity (No Directed Cycles)**: The graph is strictly a Directed Acyclic Graph ($G = (V, E)$). Any edge addition creating a directed cycle ($u \to \dots \to u$) is rejected with `CyclicEvidenceError`.
2. **No Orphan Verified Claims**: A `ClaimNode` cannot possess status `VERIFIED` without at least one path leading to a Tier 1–3 `SourceNode`.
3. **Cryptographic Tamper-Resistance**: Every `SourceNode` stores the SHA-256 hash of the ingested raw content. If the content on disk changes, the cryptographic digest invalidates all descendant `PassageNode` and `EvidenceUnitNode` instances.
4. **Hermetic Portability**: The graph does not depend on active network connections or database daemons. It serializes to a self-contained JSON/YAML document.

---

## 6. Serialization, Export & Offline Reconstruction

The Evidence Graph serializes to a portable, standardized structure (`EvidenceGraphDocument`):

```json
{
  "graph_id": "eg_proj_transistor_001",
  "project_id": "proj_transistor_001",
  "version": "1.0.0",
  "created_at_utc": "2026-09-13T17:20:00Z",
  "nodes": {
    "sources": [
      {
        "node_id": "src_bell_labs_1947",
        "title": "The Point-Contact Transistor",
        "url": "https://www.bell-labs.com/about/history/transistor/",
        "tier": 1,
        "content_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    ],
    "passages": [
      {
        "node_id": "pas_001",
        "source_node_id": "src_bell_labs_1947",
        "verbatim_text": "On December 23, 1947, John Bardeen and Walter Brattain succeeded in creating the first working point-contact transistor.",
        "char_offset_start": 1024,
        "char_offset_end": 1145
      }
    ],
    "evidence_units": [
      {
        "node_id": "eu_001",
        "passage_node_id": "pas_001",
        "atomic_statement": "Point-contact transistor created on December 23, 1947 by Bardeen and Brattain.",
        "modality": "CERTAIN"
      }
    ],
    "claims": [
      {
        "node_id": "claim_001",
        "claim_text": "In December 1947, Bell Labs physicists created the first working point-contact transistor.",
        "epistemic_status": "verified",
        "consensus_state": "STRONG_CONSENSUS",
        "claim_type": "event_fact"
      }
    ]
  },
  "edges": [
    {
      "source_id": "src_bell_labs_1947",
      "target_id": "pas_001",
      "relation": "PROVIDES"
    },
    {
      "source_id": "pas_001",
      "target_id": "eu_001",
      "relation": "EXTRACTS_FROM"
    },
    {
      "source_id": "eu_001",
      "target_id": "claim_001",
      "relation": "ENTAILS",
      "weight": 1.0
    }
  ]
}
```

---

## 7. Python Implementation API (`EvidenceGraph`)

```python
class EvidenceGraph:
    """Directed Acyclic Graph managing grounding and evidence provenance."""

    def __init__(self, graph_id: str, project_id: str):
        self.graph_id = graph_id
        self.project_id = project_id
        self._nodes: Dict[str, Any] = {}
        self._edges: List[Dict[str, Any]] = []

    def add_source(self, source: SourceRecord) -> str:
        """Adds a SourceNode and returns unique node_id."""

    def add_passage(self, source_node_id: str, excerpt: str, start: int, end: int) -> str:
        """Adds a PassageNode anchored to a SourceNode."""

    def add_evidence_unit(self, passage_node_id: str, statement: str, modality: str) -> str:
        """Adds an atomic EvidenceUnitNode."""

    def add_claim(self, claim: ClaimRecord) -> str:
        """Adds a ClaimNode."""

    def link(self, source_id: str, target_id: str, relation: EdgeRelation, weight: float = 1.0) -> None:
        """Creates a directed, typed edge; asserts acyclicity."""

    def trace_lineage(self, target_node_id: str) -> List[Dict[str, Any]]:
        """Traverses backward from target node to find all root SourceNodes."""

    def export_json(self) -> str:
        """Serializes graph to canonical JSON format."""

    @classmethod
    def from_dossier(cls, dossier: ResearchDossier) -> "EvidenceGraph":
        """Reconstructs hermetic EvidenceGraph offline from ResearchDossier."""
```
