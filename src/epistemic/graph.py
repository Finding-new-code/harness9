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

from pydantic import ConfigDict, Field, PrivateAttr, model_validator

from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    H9BaseModel,
    ResearchDossier,
    SourceRecord,
    SourceTier,
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
    """Epistemic modality of an extracted evidence proposition."""
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

    @property
    def confidence(self) -> float:
        return self.confidence_score


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

class EvidenceGraph(H9BaseModel):
    """Directed Acyclic Graph managing grounding, evidence lineage, and verification."""

    graph_id: str = Field(default_factory=lambda: f"eg_{uuid.uuid4().hex[:12]}")
    project_id: str = Field(default="")
    version: str = Field(default="1.0.0")
    created_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    _nodes: Dict[str, GraphNode] = PrivateAttr(default_factory=dict)
    _edges: Dict[str, GraphEdge] = PrivateAttr(default_factory=dict)
    _adjacency: Dict[str, List[str]] = PrivateAttr(default_factory=lambda: collections.defaultdict(list))
    _reverse_adjacency: Dict[str, List[str]] = PrivateAttr(default_factory=lambda: collections.defaultdict(list))
    _edge_lookup: Dict[Tuple[str, str], str] = PrivateAttr(default_factory=dict)

    TIER_WEIGHTS: Dict[int, float] = {
        1: 1.00,  # PRIMARY_SOURCE
        2: 0.98,  # PEER_REVIEWED_JOURNAL
        3: 0.95,  # ACADEMIC_BOOK
        4: 0.90,  # SCHOLARLY_CONFERENCE
        5: 0.88,  # INSTITUTIONAL_REPORT
        6: 0.92,  # ARCHIVAL_DOCUMENT
        7: 0.80,  # REFERENCE_WORK
        8: 0.75,  # EXPERT_ANALYSIS
        9: 0.70,  # REPUTABLE_JOURNALISM
        10: 0.55, # TRADE_PUBLICATION
        11: 0.35, # POPULAR_MEDIA
        12: 0.20, # SELF_PUBLISHED
        13: 0.00, # UNVERIFIED
    }

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

        incident_edges = [
            eid for eid, edge in self._edges.items()
            if edge.source_id == node_id or edge.target_id == node_id
        ]
        for eid in incident_edges:
            self.remove_edge(eid)

        del self._nodes[node_id]

    def get_nodes_by_type(self, node_type: Union[GraphNodeType, str]) -> List[GraphNode]:
        """Retrieve all GraphNodes matching the specified node type."""
        type_val = node_type.value if hasattr(node_type, "value") else node_type
        return [n for n in self._nodes.values() if n.node_type.value == type_val or n.node_type == type_val]

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

    def add_verification_trace(
        self,
        target_node_id: str,
        strategy_used: str,
        entailment_score: float = 0.0,
        contradiction_score: float = 0.0,
        corroboration_score: float = 0.0,
        status_assigned: str = "supported",
        consensus_state_assigned: Optional[str] = None,
        verifier_name: str = "H9EpistemicVerificationEngine",
        audit_notes: str = "",
        execution_duration_ms: float = 0.0,
        warnings: Optional[List[str]] = None,
        node_id: Optional[str] = None,
    ) -> str:
        self.require_node(target_node_id)
        nid = node_id or f"trace_{uuid.uuid4().hex[:8]}"
        node = VerificationTraceNode(
            node_id=nid,
            target_node_id=target_node_id,
            strategy_used=strategy_used,
            entailment_score=entailment_score,
            contradiction_score=contradiction_score,
            corroboration_score=corroboration_score,
            status_assigned=status_assigned,
            consensus_state_assigned=consensus_state_assigned,
            verifier_name=verifier_name,
            audit_notes=audit_notes,
            execution_duration_ms=execution_duration_ms,
            warnings=warnings or [],
        )
        self.add_node(node)
        self.link(target_node_id, nid, EdgeRelation.DERIVES_FROM)
        return nid

    def add_scene(
        self,
        scene_id: str,
        scene_index: int = 1,
        act_index: int = 1,
        title: str = "",
        start_time_seconds: float = 0.0,
        duration_seconds: float = 5.0,
        narration_text: str = "",
        visual_theme: str = "hero_graphic",
        node_id: Optional[str] = None,
    ) -> str:
        nid = node_id or scene_id
        node = SceneNode(
            node_id=nid,
            scene_id=scene_id,
            scene_index=scene_index,
            act_index=act_index,
            title=title,
            start_time_seconds=start_time_seconds,
            duration_seconds=duration_seconds,
            narration_text=narration_text,
            visual_theme=visual_theme,
        )
        return self.add_node(node)

    def add_script_sentence(
        self,
        scene_id: str,
        beat_id: str,
        sentence_text: str,
        start_time_seconds: float = 0.0,
        end_time_seconds: float = 0.0,
        grounded_claim_ids: Optional[List[str]] = None,
        hedging_applied: bool = False,
        paraphrase_mandated: bool = False,
        node_id: Optional[str] = None,
    ) -> str:
        nid = node_id or f"sent_{uuid.uuid4().hex[:8]}"
        node = ScriptSentenceNode(
            node_id=nid,
            scene_id=scene_id,
            beat_id=beat_id,
            sentence_text=sentence_text,
            start_time_seconds=start_time_seconds,
            end_time_seconds=end_time_seconds,
            grounded_claim_ids=grounded_claim_ids or [],
            hedging_applied=hedging_applied,
            paraphrase_mandated=paraphrase_mandated,
        )
        self.add_node(node)
        if scene_id in self._nodes:
            self.link(scene_id, nid, EdgeRelation.DERIVES_FROM)
        for cid in (grounded_claim_ids or []):
            if cid in self._nodes:
                self.link(cid, nid, EdgeRelation.ENTAILMENT)
        return nid

    def add_visual_element(
        self,
        scene_id: str,
        block_type: str,
        parameter_key: str,
        parameter_value: Any,
        dataset_id: Optional[str] = None,
        grounded_claim_ids: Optional[List[str]] = None,
        display_unit: Optional[str] = None,
        node_id: Optional[str] = None,
    ) -> str:
        nid = node_id or f"vis_{uuid.uuid4().hex[:8]}"
        node = VisualElementNode(
            node_id=nid,
            scene_id=scene_id,
            block_type=block_type,
            parameter_key=parameter_key,
            parameter_value=parameter_value,
            dataset_id=dataset_id,
            grounded_claim_ids=grounded_claim_ids or [],
            display_unit=display_unit,
        )
        self.add_node(node)
        if scene_id in self._nodes:
            self.link(scene_id, nid, EdgeRelation.DERIVES_FROM)
        for cid in (grounded_claim_ids or []):
            if cid in self._nodes:
                self.link(cid, nid, EdgeRelation.VISUAL_DEPICTION)
        return nid

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

    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        """Retrieve all incoming GraphEdges targeting node_id."""
        self.require_node(node_id)
        edges = []
        for parent in self._reverse_adjacency.get(node_id, []):
            eid = self._edge_lookup.get((parent, node_id))
            if eid and eid in self._edges:
                edges.append(self._edges[eid])
        return edges

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        """Retrieve all outgoing GraphEdges originating from node_id."""
        self.require_node(node_id)
        edges = []
        for child in self._adjacency.get(node_id, []):
            eid = self._edge_lookup.get((node_id, child))
            if eid and eid in self._edges:
                edges.append(self._edges[eid])
        return edges

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

        all_paths: List[List[str]] = []

        def find_paths(curr: str, current_path: List[str]):
            parents = self._reverse_adjacency.get(curr, [])
            if not parents:
                all_paths.append(list(reversed(current_path)))
                return
            for p in parents:
                find_paths(p, current_path + [p])

        find_paths(target_node_id, [target_node_id])

        all_node_ids: Set[str] = set()
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

        if isinstance(target, SourceNode):
            tier_weight = self.TIER_WEIGHTS.get(target.tier, 0.5)
            return round(tier_weight * target.reliability_score, 4)

        paths: List[List[str]] = []
        def dfs_paths(curr: str, path: List[str]):
            parents = self._reverse_adjacency.get(curr, [])
            if not parents:
                paths.append(list(reversed(path)))
                return
            for p in parents:
                dfs_paths(p, path + [p])

        dfs_paths(target_node_id, [target_node_id])

        # Filter to paths originating from an actual SourceNode
        valid_paths = [p for p in paths if isinstance(self._nodes.get(p[0]), SourceNode)]
        if not valid_paths:
            return 0.0

        path_confidences: List[float] = []

        for p in valid_paths:
            root_node = self._nodes[p[0]]
            root_weight = self.TIER_WEIGHTS.get(root_node.tier, 0.5) * root_node.reliability_score

            if method == "bottleneck":
                b_conf = root_weight
                for i in range(len(p) - 1):
                    edge = self.get_edge(p[i], p[i+1])
                    if edge:
                        b_conf = min(b_conf, edge.weight * edge.confidence)
                    if i + 1 < len(p) - 1:
                        node = self._nodes[p[i+1]]
                        node_conf = getattr(node, "confidence", None)
                        if node_conf is None:
                            node_conf = getattr(node, "confidence_score", None)
                        if node_conf is not None:
                            b_conf = min(b_conf, node_conf)
                path_confidences.append(b_conf)
            else:
                score = root_weight
                hops = len(p) - 1
                for i in range(hops):
                    edge = self.get_edge(p[i], p[i+1])
                    if edge:
                        score *= (edge.weight * edge.confidence)
                    if i + 1 < len(p) - 1:
                        node = self._nodes[p[i+1]]
                        node_conf = getattr(node, "confidence", None)
                        if node_conf is None:
                            node_conf = getattr(node, "confidence_score", None)
                        if node_conf is not None:
                            score *= node_conf
                score *= (hop_decay ** max(0, hops - 1))
                path_confidences.append(score)

        # Noisy-OR combination across independent source paths
        prod = 1.0
        for conf in path_confidences:
            prod *= (1.0 - max(0.0, min(1.0, conf)))
        combined_confidence = 1.0 - prod

        # Active contradiction penalties
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
    def to_dict(self, mode: str = "json") -> Dict[str, Any]:
        """Convert entire graph to standardized dictionary representation."""
        nodes_grouped: Dict[str, List[Dict[str, Any]]] = {
            "sources": [],
            "passages": [],
            "evidence_units": [],
            "claims": [],
            "verification_traces": [],
            "scenes": [],
            "script_sentences": [],
            "visual_elements": [],
        }

        for node in self._nodes.values():
            key = f"{node.node_type.value}s"
            if key in nodes_grouped:
                nodes_grouped[key].append(node.to_dict(mode=mode))
            else:
                nodes_grouped.setdefault("other", []).append(node.to_dict(mode=mode))

        return {
            "graph_id": self.graph_id,
            "project_id": self.project_id,
            "version": self.version,
            "created_at_utc": self.created_at_utc,
            "metadata": self.metadata,
            "nodes": nodes_grouped,
            "edges": [e.to_dict(mode=mode) for e in self._edges.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceGraph":
        """Instantiate EvidenceGraph from dictionary."""
        graph = cls(
            graph_id=data.get("graph_id"),
            project_id=data.get("project_id", ""),
            version=data.get("version", "1.0.0"),
            created_at_utc=data.get("created_at_utc", datetime.now(timezone.utc).isoformat()),
            metadata=data.get("metadata", {}),
        )

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

    def export_jsonld(self) -> Dict[str, Any]:
        """Convert graph to W3C-compatible JSON-LD format."""
        doc = self.to_dict()
        doc["@context"] = {
            "@vocab": "https://harness9.io/ns/epistemic#",
            "SourceNode": "https://harness9.io/ns/epistemic#SourceNode",
            "PassageNode": "https://harness9.io/ns/epistemic#PassageNode",
            "EvidenceUnitNode": "https://harness9.io/ns/epistemic#EvidenceUnitNode",
            "ClaimNode": "https://harness9.io/ns/epistemic#ClaimNode",
            "VerificationTraceNode": "https://harness9.io/ns/epistemic#VerificationTraceNode",
            "SceneNode": "https://harness9.io/ns/epistemic#SceneNode",
            "ScriptSentenceNode": "https://harness9.io/ns/epistemic#ScriptSentenceNode",
            "VisualElementNode": "https://harness9.io/ns/epistemic#VisualElementNode",
            "derives_from": {"@type": "@id"},
            "entailment": {"@type": "@id"},
            "contradiction": {"@type": "@id"},
            "corroboration": {"@type": "@id"},
            "mentions": {"@type": "@id"},
            "visual_depiction": {"@type": "@id"},
        }
        doc["@type"] = "EvidenceGraph"
        doc["@id"] = f"urn:h9:graph:{self.graph_id}"
        return doc

    def to_jsonld(self) -> Dict[str, Any]:
        """Alias for export_jsonld."""
        return self.export_jsonld()

    @classmethod
    def from_dossier(cls, dossier: ResearchDossier, graph_id: Optional[str] = None) -> "EvidenceGraph":
        """Construct a hermetic EvidenceGraph offline from a structured ResearchDossier."""
        graph = cls(
            graph_id=graph_id or f"eg_{dossier.run_id or uuid.uuid4().hex[:8]}",
            project_id=dossier.run_id,
        )
        source_cache: Dict[str, str] = {}

        for claim in dossier.claims:
            # Primary Source
            src = claim.primary_source
            src_key = src.url or src.title or f"src_{uuid.uuid4().hex[:8]}"
            if src_key not in source_cache:
                tier_val = src.tier.value if hasattr(src.tier, "value") else int(src.tier)
                s_id = graph.add_source(
                    title=src.title,
                    url=src.url,
                    tier=tier_val,
                    publisher=src.publisher,
                    author=src.author,
                    published_date=src.published_date,
                    reliability_score=src.reliability_score,
                    domain_authority=src.domain_authority,
                    doi=src.doi,
                    peer_reviewed=src.peer_reviewed,
                    content_sha256=src.content_sha256 or "",
                    is_sanitized=src.is_sanitized,
                    source_record=src,
                )
                source_cache[src_key] = s_id
            primary_src_id = source_cache[src_key]

            # Passage & Evidence Unit for primary source
            pas_id = graph.add_passage(
                source_node_id=primary_src_id,
                verbatim_text=claim.claim_text,
            )
            eu_id = graph.add_evidence_unit(
                passage_node_id=pas_id,
                atomic_statement=claim.claim_text,
                confidence=claim.confidence_score,
            )

            # Claim Node
            ep_status = claim.epistemic_status.value if hasattr(claim.epistemic_status, "value") else claim.epistemic_status
            con_state = claim.consensus_state.value if hasattr(claim.consensus_state, "value") else claim.consensus_state
            cl_type = claim.claim_type.value if hasattr(claim.claim_type, "value") else claim.claim_type

            claim_node_id = graph.add_claim(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                epistemic_status=ep_status,
                consensus_state=con_state,
                claim_type=cl_type,
                confidence_score=claim.confidence_score,
                category=claim.category,
                claim_record=claim,
            )
            graph.link(eu_id, claim_node_id, EdgeRelation.ENTAILMENT, weight=1.0, confidence=claim.confidence_score)

            # Corroborating sources
            for corrob_src in claim.corroborating_sources:
                c_key = corrob_src.url or corrob_src.title or f"csrc_{uuid.uuid4().hex[:8]}"
                if c_key not in source_cache:
                    c_tier = corrob_src.tier.value if hasattr(corrob_src.tier, "value") else int(corrob_src.tier)
                    cs_id = graph.add_source(
                        title=corrob_src.title,
                        url=corrob_src.url,
                        tier=c_tier,
                        publisher=corrob_src.publisher,
                        author=corrob_src.author,
                        published_date=corrob_src.published_date,
                        reliability_score=corrob_src.reliability_score,
                        domain_authority=corrob_src.domain_authority,
                        doi=corrob_src.doi,
                        peer_reviewed=corrob_src.peer_reviewed,
                        content_sha256=corrob_src.content_sha256 or "",
                        is_sanitized=corrob_src.is_sanitized,
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
                graph.link(ceu_id, claim_node_id, EdgeRelation.ENTAILMENT, weight=corrob_src.reliability_score, confidence=corrob_src.reliability_score)

                # Link source corroboration edge if acyclic
                if not graph.get_edge(primary_src_id, corrob_src_id) and not graph.would_create_cycle(primary_src_id, corrob_src_id):
                    graph.link(primary_src_id, corrob_src_id, EdgeRelation.CORROBORATION)

        return graph
