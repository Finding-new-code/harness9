"""tests/test_evidence_graph.py — Comprehensive Test Suite for Evidence Graph Abstraction (Milestone M2).

Verifies node models, edge relations, cycle prevention & DAG invariants, deterministic
topological sorting (Kahn's algorithm with alphanumeric tie-breaking), querying, lineage
traversal, confidence calculation, serialization roundtrips, dossier conversion, and mutations.
"""

from datetime import datetime, timezone
import json
import unittest

from pydantic import ValidationError

from src.epistemic.graph import (
    CycleDetectedError,
    EdgeNotFoundError,
    EdgeRelation,
    EvidenceGraph,
    EvidenceGraphError,
    EvidenceUnitNode,
    GraphEdge,
    GraphNode,
    GraphNodeType,
    ModalityType,
    NodeNotFoundError,
    PassageNode,
    ProvenanceChain,
    SceneNode,
    ScriptSentenceNode,
    SourceNode,
    VerificationTraceNode,
    VisualElementNode,
    ClaimNode,
)
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    ResearchDossier,
    SourceRecord,
    SourceTier,
)


class TestGraphNodeModels(unittest.TestCase):
    """Test Suite 1: Node model validation, bounds, offsets, and modalities."""

    def test_source_node_creation_and_defaults(self):
        node = SourceNode(
            node_id="src_01",
            title="Archival Treaty Document",
            url="https://archives.gov/treaty1",
            tier=1,
            reliability_score=0.95,
            content_sha256="abc123sha256",
            is_sanitized=True,
        )
        self.assertEqual(node.node_type, GraphNodeType.SOURCE)
        self.assertEqual(node.tier, 1)
        self.assertEqual(node.reliability_score, 0.95)
        self.assertTrue(node.is_sanitized)
        self.assertEqual(node.content_sha256, "abc123sha256")

        # Invalid tier < 1 or > 13 raises ValidationError
        with self.assertRaises(ValidationError):
            SourceNode(node_id="src_bad", title="Bad Tier", url="https://x.org", tier=0)
        with self.assertRaises(ValidationError):
            SourceNode(node_id="src_bad", title="Bad Tier", url="https://x.org", tier=14)

    def test_passage_node_char_offsets(self):
        valid_passage = PassageNode(
            node_id="pas_01",
            source_node_id="src_01",
            verbatim_text="The treaty was signed on June 28, 1919.",
            char_offset_start=100,
            char_offset_end=138,
        )
        self.assertEqual(valid_passage.node_type, GraphNodeType.PASSAGE)
        self.assertEqual(valid_passage.char_offset_start, 100)
        self.assertEqual(valid_passage.char_offset_end, 138)

        # Invalid offset end < start raises ValidationError
        with self.assertRaises(ValidationError):
            PassageNode(
                node_id="pas_bad",
                source_node_id="src_01",
                verbatim_text="Inverted offsets",
                char_offset_start=200,
                char_offset_end=100,
            )

    def test_evidence_unit_node_modalities_and_polarity(self):
        eu = EvidenceUnitNode(
            node_id="eu_01",
            passage_node_id="pas_01",
            atomic_statement="The treaty established the League of Nations.",
            modality=ModalityType.CERTAIN,
            polarity=True,
            confidence=0.98,
            extracted_entities=["League of Nations"],
        )
        self.assertEqual(eu.node_type, GraphNodeType.EVIDENCE_UNIT)
        self.assertEqual(eu.modality, ModalityType.CERTAIN)
        self.assertTrue(eu.polarity)
        self.assertEqual(eu.confidence, 0.98)
        self.assertEqual(eu.extracted_entities, ["League of Nations"])

    def test_claim_node_attributes(self):
        claim = ClaimNode(
            node_id="claim_01",
            claim_id="claim_01",
            claim_text="The League of Nations was founded in 1920.",
            epistemic_status="verified",
            consensus_state="STRONG_CONSENSUS",
            claim_type="event_fact",
            confidence_score=0.95,
        )
        self.assertEqual(claim.node_type, GraphNodeType.CLAIM)
        self.assertEqual(claim.epistemic_status, "verified")
        self.assertEqual(claim.consensus_state, "STRONG_CONSENSUS")
        self.assertEqual(claim.confidence, 0.95)

    def test_verification_trace_node(self):
        trace = VerificationTraceNode(
            node_id="trace_01",
            target_node_id="claim_01",
            strategy_used="SOURCE_ENTAILMENT",
            entailment_score=0.96,
            contradiction_score=0.01,
            corroboration_score=0.92,
            status_assigned="verified",
        )
        self.assertEqual(trace.node_type, GraphNodeType.VERIFICATION_TRACE)
        self.assertEqual(trace.strategy_used, "SOURCE_ENTAILMENT")
        self.assertEqual(trace.entailment_score, 0.96)
        self.assertEqual(trace.status_assigned, "verified")

    def test_script_sentence_and_scene_nodes(self):
        scene = SceneNode(
            node_id="scene_01",
            scene_id="scene_01",
            scene_index=1,
            act_index=1,
            title="Introduction to Geneva",
            duration_seconds=8.5,
        )
        self.assertEqual(scene.node_type, GraphNodeType.SCENE)
        self.assertEqual(scene.duration_seconds, 8.5)

        sent = ScriptSentenceNode(
            node_id="sent_01",
            scene_id="scene_01",
            beat_id="beat_01",
            sentence_text="Delegates arrived in Geneva to begin deliberations.",
            start_time_seconds=0.0,
            end_time_seconds=3.5,
            grounded_claim_ids=["claim_01"],
            hedging_applied=False,
        )
        self.assertEqual(sent.node_type, GraphNodeType.SCRIPT_SENTENCE)
        self.assertEqual(sent.end_time_seconds, 3.5)
        self.assertEqual(sent.grounded_claim_ids, ["claim_01"])

    def test_visual_element_node(self):
        vis = VisualElementNode(
            node_id="vis_01",
            scene_id="scene_01",
            block_type="STATISTIC_REVEAL",
            parameter_key="member_count",
            parameter_value=42,
            dataset_id="ds_league_members",
            display_unit="nations",
        )
        self.assertEqual(vis.node_type, GraphNodeType.VISUAL_ELEMENT)
        self.assertEqual(vis.parameter_key, "member_count")
        self.assertEqual(vis.parameter_value, 42)
        self.assertEqual(vis.display_unit, "nations")


class TestGraphEdgeModels(unittest.TestCase):
    """Test Suite 2: Edge relations, weights, confidence, and aliases."""

    def test_edge_relation_enum_coverage(self):
        expected_relations = {
            "entailment",
            "contradiction",
            "corroboration",
            "mentions",
            "derives_from",
            "visual_depiction",
        }
        actual_relations = {r.value for r in EdgeRelation}
        self.assertTrue(expected_relations.issubset(actual_relations))

    def test_edge_weights_and_confidence(self):
        edge = GraphEdge(
            edge_id="edge_01",
            source_id="eu_01",
            target_id="claim_01",
            relation=EdgeRelation.ENTAILMENT,
            weight=0.95,
            confidence=0.99,
        )
        self.assertEqual(edge.weight, 0.95)
        self.assertEqual(edge.confidence, 0.99)
        self.assertEqual(edge.relation, EdgeRelation.ENTAILMENT)

    def test_edge_alias_normalization(self):
        graph = EvidenceGraph()
        s_id = graph.add_source(title="Doc", url="https://doc.org")
        c_id = graph.add_claim(claim_text="Claim text")

        # Test aliases: grounds -> entailment, provides -> derives_from, binds_to -> visual_depiction
        e1 = graph.link(s_id, c_id, "grounds")
        self.assertEqual(graph._edges[e1].relation, EdgeRelation.ENTAILMENT)


class TestEvidenceGraphDAGInvariants(unittest.TestCase):
    """Test Suite 3: Cycle prevention, self-loops, and diamond DAG support."""

    def setUp(self):
        self.graph = EvidenceGraph()
        self.n_a = self.graph.add_claim(claim_text="Node A", node_id="A")
        self.n_b = self.graph.add_claim(claim_text="Node B", node_id="B")
        self.n_c = self.graph.add_claim(claim_text="Node C", node_id="C")
        self.n_d = self.graph.add_claim(claim_text="Node D", node_id="D")

    def test_add_node_duplicate_rejection(self):
        with self.assertRaises(ValueError):
            self.graph.add_claim(claim_text="Duplicate A", node_id="A")

    def test_link_nonexistent_nodes_rejection(self):
        with self.assertRaises(NodeNotFoundError):
            self.graph.link("A", "NON_EXISTENT", EdgeRelation.ENTAILMENT)
        with self.assertRaises(NodeNotFoundError):
            self.graph.link("NON_EXISTENT", "B", EdgeRelation.ENTAILMENT)

    def test_self_loop_rejection(self):
        with self.assertRaises(CycleDetectedError):
            self.graph.link("A", "A", EdgeRelation.DERIVES_FROM)

    def test_direct_2_node_cycle_rejection(self):
        self.graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        with self.assertRaises(CycleDetectedError):
            self.graph.link("B", "A", EdgeRelation.DERIVES_FROM)

    def test_multi_hop_cycle_rejection(self):
        self.graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        self.graph.link("B", "C", EdgeRelation.DERIVES_FROM)
        self.graph.link("C", "D", EdgeRelation.DERIVES_FROM)
        with self.assertRaises(CycleDetectedError):
            self.graph.link("D", "A", EdgeRelation.DERIVES_FROM)

    def test_diamond_dag_allowed(self):
        # A -> B -> D and A -> C -> D is a valid DAG (diamond)
        self.graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        self.graph.link("A", "C", EdgeRelation.DERIVES_FROM)
        self.graph.link("B", "D", EdgeRelation.DERIVES_FROM)
        # Adding C -> D must succeed and not be flagged as a cycle
        e_cd = self.graph.link("C", "D", EdgeRelation.DERIVES_FROM)
        self.assertIsNotNone(e_cd)
        self.assertFalse(self.graph.has_cycles())


class TestTopologicalSort(unittest.TestCase):
    """Test Suite 4: Deterministic topological sort with alphanumeric tie-breaking."""

    def test_topological_sort_linear_chain(self):
        graph = EvidenceGraph()
        graph.add_claim(claim_text="1", node_id="step1")
        graph.add_claim(claim_text="2", node_id="step2")
        graph.add_claim(claim_text="3", node_id="step3")
        graph.link("step1", "step2", EdgeRelation.DERIVES_FROM)
        graph.link("step2", "step3", EdgeRelation.DERIVES_FROM)

        order = graph.topological_sort()
        self.assertEqual(order, ["step1", "step2", "step3"])

    def test_topological_sort_diamond(self):
        graph = EvidenceGraph()
        graph.add_claim(claim_text="A", node_id="A")
        graph.add_claim(claim_text="B", node_id="B")
        graph.add_claim(claim_text="C", node_id="C")
        graph.add_claim(claim_text="D", node_id="D")
        graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        graph.link("A", "C", EdgeRelation.DERIVES_FROM)
        graph.link("B", "D", EdgeRelation.DERIVES_FROM)
        graph.link("C", "D", EdgeRelation.DERIVES_FROM)

        order = graph.topological_sort()
        self.assertEqual(order[0], "A")
        self.assertEqual(order[-1], "D")
        self.assertTrue(order.index("B") < order.index("D"))
        self.assertTrue(order.index("C") < order.index("D"))

    def test_deterministic_tie_breaking(self):
        graph1 = EvidenceGraph()
        for nid in ["node_Z", "node_A", "node_M"]:
            graph1.add_claim(claim_text=nid, node_id=nid)

        graph2 = EvidenceGraph()
        for nid in ["node_A", "node_M", "node_Z"]:
            graph2.add_claim(claim_text=nid, node_id=nid)

        sort1 = graph1.topological_sort()
        sort2 = graph2.topological_sort()

        self.assertEqual(sort1, ["node_A", "node_M", "node_Z"])
        self.assertEqual(sort1, sort2)


class TestGraphQuerying(unittest.TestCase):
    """Test Suite 5: Querying claims by status, consensus, type, and edge queries."""

    def setUp(self):
        self.graph = EvidenceGraph()
        self.graph.add_claim(claim_text="C1", node_id="c1", epistemic_status="verified", consensus_state="STRONG_CONSENSUS", claim_type="event_fact")
        self.graph.add_claim(claim_text="C2", node_id="c2", epistemic_status="contested", consensus_state="ACTIVE_DEBATE", claim_type="causal_interpretation")
        self.graph.add_claim(claim_text="C3", node_id="c3", epistemic_status="unsupported", consensus_state="UNRESOLVED", claim_type="numerical_metric")
        self.graph.add_claim(claim_text="C4", node_id="c4", epistemic_status="supported", consensus_state="BROAD_CONSENSUS", claim_type="direct_quote")
        self.graph.add_source(title="S1", url="https://s1.org", node_id="s1")
        self.graph.link("s1", "c1", EdgeRelation.CORROBORATION)

    def test_get_claims_by_status(self):
        verified = self.graph.get_claims_by_status("verified")
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0].node_id, "c1")

    def test_get_contested_claims(self):
        contested = self.graph.get_contested_claims()
        self.assertEqual(len(contested), 1)
        self.assertEqual(contested[0].node_id, "c2")

    def test_get_unsupported_claims(self):
        unsupported = self.graph.get_unsupported_claims()
        self.assertEqual(len(unsupported), 1)
        self.assertEqual(unsupported[0].node_id, "c3")

    def test_get_verified_claims(self):
        verified = self.graph.get_verified_claims()
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0].node_id, "c1")

    def test_get_claims_by_consensus(self):
        debated = self.graph.get_claims_by_consensus("ACTIVE_DEBATE")
        self.assertEqual(len(debated), 1)
        self.assertEqual(debated[0].node_id, "c2")

    def test_get_claims_by_type(self):
        quotes = self.graph.get_claims_by_type("direct_quote")
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0].node_id, "c4")

    def test_get_nodes_by_type(self):
        claims = self.graph.get_nodes_by_type(GraphNodeType.CLAIM)
        self.assertEqual(len(claims), 4)
        sources = self.graph.get_nodes_by_type(GraphNodeType.SOURCE)
        self.assertEqual(len(sources), 1)

    def test_get_incoming_and_outgoing_edges(self):
        incoming_c1 = self.graph.get_incoming_edges("c1")
        self.assertEqual(len(incoming_c1), 1)
        self.assertEqual(incoming_c1[0].source_id, "s1")

        outgoing_s1 = self.graph.get_outgoing_edges("s1")
        self.assertEqual(len(outgoing_s1), 1)
        self.assertEqual(outgoing_s1[0].target_id, "c1")


class TestLineageReconstruction(unittest.TestCase):
    """Test Suite 6: Backward lineage traversal and ungrounded detection."""

    def test_trace_lineage_complete_forward_flow(self):
        graph = EvidenceGraph()
        s_id = graph.add_source(title="Archival Record", url="https://archive.org/doc", tier=1, reliability_score=0.98)
        p_id = graph.add_passage(source_node_id=s_id, verbatim_text="Text of passage.")
        eu_id = graph.add_evidence_unit(passage_node_id=p_id, atomic_statement="Atomic statement.", confidence=1.0)
        c_id = graph.add_claim(claim_text="Editorial Claim.")
        graph.link(eu_id, c_id, EdgeRelation.ENTAILMENT)
        scene_id = graph.add_scene(scene_id="scene_01")
        sent_id = graph.add_script_sentence(scene_id=scene_id, beat_id="beat_01", sentence_text="Voiceover text.", grounded_claim_ids=[c_id])

        chain = graph.trace_lineage(sent_id)
        self.assertTrue(chain.is_grounded)
        self.assertEqual(chain.root_source_ids, [s_id])
        self.assertEqual(len(chain.root_sources), 1)
        self.assertEqual(len(chain.passages), 1)
        self.assertEqual(len(chain.evidence_units), 1)
        self.assertEqual(len(chain.claims), 1)
        self.assertGreater(chain.calculated_confidence, 0.5)

    def test_trace_lineage_visual_element(self):
        graph = EvidenceGraph()
        s_id = graph.add_source(title="Census Report", url="https://census.gov", tier=5, reliability_score=0.95)
        p_id = graph.add_passage(source_node_id=s_id, verbatim_text="Population was 3.9 million.")
        eu_id = graph.add_evidence_unit(passage_node_id=p_id, atomic_statement="Population 3.9M in 1790.", confidence=1.0)
        c_id = graph.add_claim(claim_text="US Population in 1790 was 3.9M.")
        graph.link(eu_id, c_id, EdgeRelation.ENTAILMENT)
        scene_id = graph.add_scene(scene_id="scene_01")
        vis_id = graph.add_visual_element(
            scene_id=scene_id,
            block_type="STATISTIC_REVEAL",
            parameter_key="population",
            parameter_value="3.9M",
            grounded_claim_ids=[c_id],
        )

        chain = graph.trace_lineage(vis_id)
        self.assertTrue(chain.is_grounded)
        self.assertEqual(chain.root_source_ids, [s_id])

    def test_ungrounded_proposition_detection(self):
        graph = EvidenceGraph()
        sent_id = graph.add_script_sentence(
            scene_id="scene_floating",
            beat_id="beat_floating",
            sentence_text="Completely invented assertion with no sources.",
        )
        chain = graph.trace_lineage(sent_id)
        self.assertFalse(chain.is_grounded)
        self.assertEqual(chain.root_source_ids, [])
        self.assertEqual(chain.calculated_confidence, 0.0)

    def test_get_root_sources(self):
        graph = EvidenceGraph()
        s_id = graph.add_source(title="Primary", url="https://prim.org", tier=1)
        p_id = graph.add_passage(source_node_id=s_id, verbatim_text="Passage text")
        eu_id = graph.add_evidence_unit(passage_node_id=p_id, atomic_statement="Statement")
        c_id = graph.add_claim(claim_text="Claim")
        graph.link(eu_id, c_id, EdgeRelation.ENTAILMENT)

        roots = graph.get_root_sources(c_id)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].node_id, s_id)


class TestChainConfidenceCalculations(unittest.TestCase):
    """Test Suite 7: Series decay, Noisy-OR corroboration, contradiction penalties."""

    def test_single_path_tier_weighted_confidence(self):
        graph = EvidenceGraph()
        s1 = graph.add_source(title="T1", url="https://t1.org", tier=1, reliability_score=1.0)
        p1 = graph.add_passage(source_node_id=s1, verbatim_text="Text")
        eu1 = graph.add_evidence_unit(passage_node_id=p1, atomic_statement="Fact", confidence=1.0)
        c1 = graph.add_claim(claim_text="Claim 1")
        graph.link(eu1, c1, EdgeRelation.ENTAILMENT, weight=1.0, confidence=1.0)

        # Tier 1 with weight 1.0, reliability 1.0, hop_decay=0.98 on 2 hops (hops-1=1)
        # hops = len([s1, p1, eu1, c1]) - 1 = 3 hops. hop_decay^(3-1) = 0.98^2 = 0.9604
        conf_t1 = graph.calculate_chain_confidence(c1)
        self.assertAlmostEqual(conf_t1, 0.9604, places=3)

        # Tier 13 (Unverified, weight 0.0)
        s13 = graph.add_source(title="T13", url="https://t13.org", tier=13, reliability_score=1.0)
        p13 = graph.add_passage(source_node_id=s13, verbatim_text="Rumor")
        eu13 = graph.add_evidence_unit(passage_node_id=p13, atomic_statement="Rumor fact", confidence=1.0)
        c13 = graph.add_claim(claim_text="Claim 13")
        graph.link(eu13, c13, EdgeRelation.ENTAILMENT, weight=1.0, confidence=1.0)

        conf_t13 = graph.calculate_chain_confidence(c13)
        self.assertEqual(conf_t13, 0.0)

    def test_multi_path_parallel_corroboration(self):
        graph = EvidenceGraph()
        # Path 1 from Source A
        s_a = graph.add_source(title="A", url="https://a.org", tier=2, reliability_score=0.9)
        p_a = graph.add_passage(source_node_id=s_a, verbatim_text="Text A")
        eu_a = graph.add_evidence_unit(passage_node_id=p_a, atomic_statement="Statement A", confidence=0.9)
        c = graph.add_claim(claim_text="Corroborated Claim")
        graph.link(eu_a, c, EdgeRelation.ENTAILMENT, weight=0.9, confidence=0.9)

        conf_single = graph.calculate_chain_confidence(c)

        # Path 2 from Source B
        s_b = graph.add_source(title="B", url="https://b.org", tier=2, reliability_score=0.9)
        p_b = graph.add_passage(source_node_id=s_b, verbatim_text="Text B")
        eu_b = graph.add_evidence_unit(passage_node_id=p_b, atomic_statement="Statement B", confidence=0.9)
        graph.link(eu_b, c, EdgeRelation.ENTAILMENT, weight=0.9, confidence=0.9)

        conf_multi = graph.calculate_chain_confidence(c)
        # Parallel corroboration via Noisy-OR must exceed single path confidence
        self.assertGreater(conf_multi, conf_single)

    def test_contradiction_penalty_degradation(self):
        graph = EvidenceGraph()
        s_pos = graph.add_source(title="Pos", url="https://pos.org", tier=1, reliability_score=0.95)
        p_pos = graph.add_passage(source_node_id=s_pos, verbatim_text="Affirmative text")
        eu_pos = graph.add_evidence_unit(passage_node_id=p_pos, atomic_statement="Affirmative fact")
        c = graph.add_claim(claim_text="Disputed Claim")
        graph.link(eu_pos, c, EdgeRelation.ENTAILMENT, weight=1.0, confidence=1.0)

        conf_before = graph.calculate_chain_confidence(c)

        # Add contradictory evidence
        s_neg = graph.add_source(title="Neg", url="https://neg.org", tier=1, reliability_score=0.95)
        graph.link(s_neg, c, EdgeRelation.CONTRADICTION, weight=0.8, confidence=1.0)

        conf_after = graph.calculate_chain_confidence(c)
        self.assertLess(conf_after, conf_before)

    def test_bottleneck_confidence_calculation(self):
        graph = EvidenceGraph()
        s = graph.add_source(title="Source", url="https://s.org", tier=1, reliability_score=1.0)
        p = graph.add_passage(source_node_id=s, verbatim_text="Text")
        eu = graph.add_evidence_unit(passage_node_id=p, atomic_statement="Fact", confidence=0.45)
        c = graph.add_claim(claim_text="Bottleneck claim")
        graph.link(eu, c, EdgeRelation.ENTAILMENT, weight=0.9, confidence=0.9)

        conf_bottle = graph.calculate_chain_confidence(c, method="bottleneck")
        self.assertEqual(conf_bottle, 0.45)


class TestSerializationAndRoundtrip(unittest.TestCase):
    """Test Suite 8: JSON, dictionary, and JSON-LD serialization."""

    def setUp(self):
        self.graph = EvidenceGraph(graph_id="eg_roundtrip_test", project_id="proj_alpha")
        self.s_id = self.graph.add_source(title="S1", url="https://s1.org", tier=1)
        self.p_id = self.graph.add_passage(source_node_id=self.s_id, verbatim_text="Passage")
        self.eu_id = self.graph.add_evidence_unit(passage_node_id=self.p_id, atomic_statement="Fact")
        self.c_id = self.graph.add_claim(claim_text="Claim")
        self.graph.link(self.eu_id, self.c_id, EdgeRelation.ENTAILMENT)
        self.sc_id = self.graph.add_scene(scene_id="scene_01")
        self.sent_id = self.graph.add_script_sentence(scene_id=self.sc_id, beat_id="b1", sentence_text="Sentence", grounded_claim_ids=[self.c_id])
        self.vis_id = self.graph.add_visual_element(scene_id=self.sc_id, block_type="CHART", parameter_key="k", parameter_value="v", grounded_claim_ids=[self.c_id])
        self.tr_id = self.graph.add_verification_trace(target_node_id=self.c_id, strategy_used="ENTAILMENT")

    def test_dictionary_roundtrip(self):
        d = self.graph.to_dict()
        self.assertEqual(d["graph_id"], "eg_roundtrip_test")
        self.assertEqual(d["project_id"], "proj_alpha")

        restored = EvidenceGraph.from_dict(d)
        self.assertEqual(len(restored._nodes), len(self.graph._nodes))
        self.assertEqual(len(restored._edges), len(self.graph._edges))
        self.assertEqual(restored.require_node(self.c_id).node_type, GraphNodeType.CLAIM)

    def test_json_roundtrip(self):
        json_str = self.graph.to_json()
        self.assertIn("eg_roundtrip_test", json_str)

        restored = EvidenceGraph.from_json(json_str)
        self.assertEqual(restored.graph_id, "eg_roundtrip_test")
        self.assertEqual(len(restored._nodes), len(self.graph._nodes))

    def test_jsonld_structure(self):
        ld = self.graph.export_jsonld()
        self.assertIn("@context", ld)
        self.assertIn("@type", ld)
        self.assertEqual(ld["@type"], "EvidenceGraph")
        self.assertEqual(ld["@id"], f"urn:h9:graph:{self.graph.graph_id}")

        # to_jsonld alias check
        ld2 = self.graph.to_jsonld()
        self.assertEqual(ld, ld2)


class TestResearchDossierIntegration(unittest.TestCase):
    """Test Suite 9: Building EvidenceGraph directly from ResearchDossier."""

    def test_from_dossier_reconstruction(self):
        prim_source = SourceRecord(
            title="MIT Tech Review",
            url="https://technologyreview.com/quantum",
            tier=SourceTier.PEER_REVIEWED_JOURNAL,
            reliability_score=0.96,
        )
        corrob_source = SourceRecord(
            title="Nature Physics",
            url="https://nature.com/articles/phys123",
            tier=SourceTier.PRIMARY_SOURCE,
            reliability_score=0.99,
        )
        claim = ClaimRecord(
            claim_id="claim_quantum_01",
            claim_text="Neutral atom qubits demonstrated coherence times exceeding 10 seconds.",
            category="quantum_computing",
            confidence_score=0.95,
            primary_source=prim_source,
            corroborating_sources=[corrob_source],
            epistemic_status=EpistemicStatus.VERIFIED,
            consensus_state=ConsensusState.STRONG_CONSENSUS,
            claim_type=ClaimType.SCIENTIFIC_LAW,
        )
        dossier = ResearchDossier(
            topic="Quantum Computing",
            run_id="run_quantum_01",
            claims=[claim],
        )

        graph = EvidenceGraph.from_dossier(dossier)
        self.assertGreaterEqual(len(graph._nodes), 4)

        # Find Claim Node
        claims = graph.get_claims_by_status("verified")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].claim_id, "claim_quantum_01")
        self.assertEqual(claims[0].consensus_state, "STRONG_CONSENSUS")

        # Verify lineage traces back to both sources
        chain = graph.trace_lineage(claims[0].node_id)
        self.assertTrue(chain.is_grounded)
        self.assertEqual(len(chain.root_sources), 2)


class TestGraphMutationAndCascades(unittest.TestCase):
    """Test Suite 10: Node removal cascading edges, edge removal, and subgraphs."""

    def test_remove_node_cascades_edges(self):
        graph = EvidenceGraph()
        n1 = graph.add_claim(claim_text="A", node_id="A")
        n2 = graph.add_claim(claim_text="B", node_id="B")
        n3 = graph.add_claim(claim_text="C", node_id="C")
        e1 = graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        e2 = graph.link("B", "C", EdgeRelation.DERIVES_FROM)

        self.assertEqual(len(graph._edges), 2)
        # Remove middle node B
        graph.remove_node("B")

        self.assertNotIn("B", graph._nodes)
        self.assertNotIn(e1, graph._edges)
        self.assertNotIn(e2, graph._edges)
        self.assertIn("A", graph._nodes)
        self.assertIn("C", graph._nodes)

    def test_remove_edge(self):
        graph = EvidenceGraph()
        graph.add_claim(claim_text="A", node_id="A")
        graph.add_claim(claim_text="B", node_id="B")
        e1 = graph.link("A", "B", EdgeRelation.DERIVES_FROM)

        self.assertIsNotNone(graph.get_edge("A", "B"))
        graph.remove_edge(e1)
        self.assertIsNone(graph.get_edge("A", "B"))

    def test_extract_subgraph(self):
        graph = EvidenceGraph()
        graph.add_claim(claim_text="A", node_id="A")
        graph.add_claim(claim_text="B", node_id="B")
        graph.add_claim(claim_text="C", node_id="C")
        graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        graph.link("B", "C", EdgeRelation.DERIVES_FROM)

        sub = graph.extract_subgraph({"A", "B"})
        self.assertEqual(len(sub._nodes), 2)
        self.assertEqual(len(sub._edges), 1)
        self.assertIsNotNone(sub.get_edge("A", "B"))
        self.assertIsNone(sub.get_edge("B", "C"))


if __name__ == "__main__":
    unittest.main()
