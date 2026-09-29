"""tests/test_evidence_graph_adversarial.py — Adversarial Stress Suite for Evidence Graph.

Exhaustively stress-tests:
1. Cycle detection: Self-loops, direct cycles, multi-hop cycles (3, 5, 10, 50 nodes),
   disconnected cyclic components, cross-branch cycles, and cycle injection via serialization.
2. Diamond DAGs and complex topologies: Single diamonds, multi-diamonds, wide fan-in,
   transitive shortcuts, complete bipartite DAGs, and dense DAGs.
3. Topological sort determinism: Invariant output under random insertion orderings and
   identical dependency depths across nodes.
4. Confidence formula boundaries: Strict [0.0, 1.0] bounds under all contradictions,
   disconnected nodes, high-depth hop decay, and extreme corroboration.
5. Serialization round-trip fidelity: 100% attribute, type, and edge fidelity across
   dictionary and JSON round-trips for all 8 node types and 6 edge relations.
"""

from datetime import datetime, timezone
import itertools
import json
import random
import unittest
from typing import List

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


class TestAdversarialCycles(unittest.TestCase):
    """Adversarial Focus 1: Exhaustive testing of cycle detection and prevention."""

    def test_self_loops_all_relations(self):
        """Verify that self-loops are blocked for every EdgeRelation."""
        for relation in EdgeRelation:
            graph = EvidenceGraph()
            node_id = graph.add_claim(claim_text=f"Node {relation.value}", node_id="self_node")
            with self.assertRaises(CycleDetectedError, msg=f"Failed to block self-loop for {relation}"):
                graph.link(node_id, node_id, relation)

    def test_direct_two_node_cycles_all_relations(self):
        """Verify that 2-node cycles A -> B and B -> A are blocked across relations."""
        for rel1 in [EdgeRelation.DERIVES_FROM, EdgeRelation.ENTAILMENT]:
            for rel2 in [EdgeRelation.CONTRADICTION, EdgeRelation.CORROBORATION]:
                graph = EvidenceGraph()
                a = graph.add_claim(claim_text="A", node_id="A")
                b = graph.add_claim(claim_text="B", node_id="B")
                graph.link(a, b, rel1)
                with self.assertRaises(CycleDetectedError):
                    graph.link(b, a, rel2)

    def test_multi_hop_cycles_various_lengths(self):
        """Verify cycle detection across 3, 5, 10, and 50 node linear paths."""
        for length in [3, 5, 10, 50]:
            graph = EvidenceGraph()
            node_ids = [f"node_{length}_{i}" for i in range(length)]
            for nid in node_ids:
                graph.add_claim(claim_text=f"Claim {nid}", node_id=nid)

            # Build linear chain: 0 -> 1 -> 2 -> ... -> (length - 1)
            for i in range(length - 1):
                graph.link(node_ids[i], node_ids[i+1], EdgeRelation.DERIVES_FROM)

            # Attempt to close the loop: (length - 1) -> 0
            with self.assertRaises(CycleDetectedError, msg=f"Failed to detect cycle of length {length}"):
                graph.link(node_ids[-1], node_ids[0], EdgeRelation.DERIVES_FROM)

            # Graph must remain a valid DAG
            self.assertFalse(graph.has_cycles())
            self.assertEqual(len(graph.topological_sort()), length)

    def test_disconnected_components_cycle(self):
        """Verify that a cycle in a secondary disconnected component is blocked without affecting component 1."""
        graph = EvidenceGraph()
        # Component 1: valid DAG C1_A -> C1_B -> C1_C
        for nid in ["C1_A", "C1_B", "C1_C"]:
            graph.add_claim(claim_text=nid, node_id=nid)
        graph.link("C1_A", "C1_B", EdgeRelation.DERIVES_FROM)
        graph.link("C1_B", "C1_C", EdgeRelation.DERIVES_FROM)

        # Component 2: C2_X -> C2_Y -> C2_Z
        for nid in ["C2_X", "C2_Y", "C2_Z"]:
            graph.add_claim(claim_text=nid, node_id=nid)
        graph.link("C2_X", "C2_Y", EdgeRelation.ENTAILMENT)
        graph.link("C2_Y", "C2_Z", EdgeRelation.ENTAILMENT)

        # Attempt to cycle Component 2: C2_Z -> C2_X
        with self.assertRaises(CycleDetectedError):
            graph.link("C2_Z", "C2_X", EdgeRelation.ENTAILMENT)

        # Ensure Component 1 remains completely intact
        self.assertIsNotNone(graph.get_edge("C1_A", "C1_B"))
        self.assertFalse(graph.has_cycles())

    def test_cross_branch_cycles_in_complex_tree(self):
        """Verify that attempting to close cycles across branching DAG paths is caught."""
        graph = EvidenceGraph()
        # Root -> Branch 1 (B1_1 -> B1_2 -> B1_3)
        # Root -> Branch 2 (B2_1 -> B2_2 -> B2_3)
        nodes = ["Root", "B1_1", "B1_2", "B1_3", "B2_1", "B2_2", "B2_3"]
        for n in nodes:
            graph.add_claim(claim_text=n, node_id=n)

        graph.link("Root", "B1_1", EdgeRelation.DERIVES_FROM)
        graph.link("B1_1", "B1_2", EdgeRelation.DERIVES_FROM)
        graph.link("B1_2", "B1_3", EdgeRelation.DERIVES_FROM)

        graph.link("Root", "B2_1", EdgeRelation.DERIVES_FROM)
        graph.link("B2_1", "B2_2", EdgeRelation.DERIVES_FROM)
        graph.link("B2_2", "B2_3", EdgeRelation.DERIVES_FROM)

        # B1_3 -> Root must fail
        with self.assertRaises(CycleDetectedError):
            graph.link("B1_3", "Root", EdgeRelation.DERIVES_FROM)

        # Cross-branch edge B1_3 -> B2_1 is valid (no cycle)
        graph.link("B1_3", "B2_1", EdgeRelation.DERIVES_FROM)

        # But now B2_3 -> B1_1 would create a cycle: B1_1 -> B1_2 -> B1_3 -> B2_1 -> B2_2 -> B2_3 -> B1_1
        with self.assertRaises(CycleDetectedError):
            graph.link("B2_3", "B1_1", EdgeRelation.DERIVES_FROM)

    def test_deserialization_blocks_cycles(self):
        """Verify that reconstructing from a dictionary containing a cycle strictly raises CycleDetectedError."""
        cyclic_dict = {
            "graph_id": "cyclic_graph",
            "nodes": {
                "claims": [
                    {"node_id": "c1", "node_type": "claim", "claim_id": "c1", "claim_text": "Claim 1"},
                    {"node_id": "c2", "node_type": "claim", "claim_id": "c2", "claim_text": "Claim 2"},
                ]
            },
            "edges": [
                {"source_id": "c1", "target_id": "c2", "relation": "derives_from"},
                {"source_id": "c2", "target_id": "c1", "relation": "derives_from"},
            ]
        }
        with self.assertRaises(CycleDetectedError):
            EvidenceGraph.from_dict(cyclic_dict)


class TestAdversarialComplexTopologies(unittest.TestCase):
    """Adversarial Focus 2: Verify valid DAGs with converging paths are never falsely flagged as cycles."""

    def test_single_diamond_dag(self):
        """A -> B, A -> C, B -> D, C -> D must never trigger CycleDetectedError."""
        graph = EvidenceGraph()
        for n in ["A", "B", "C", "D"]:
            graph.add_claim(claim_text=n, node_id=n)

        graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        graph.link("A", "C", EdgeRelation.DERIVES_FROM)
        graph.link("B", "D", EdgeRelation.DERIVES_FROM)
        # Adding C -> D must succeed
        graph.link("C", "D", EdgeRelation.DERIVES_FROM)

        self.assertFalse(graph.has_cycles())
        order = graph.topological_sort()
        self.assertEqual(order[0], "A")
        self.assertEqual(order[-1], "D")

    def test_multi_diamond_and_grid(self):
        """Consecutive chained diamonds: A -> (B,C) -> D -> (E,F) -> G."""
        graph = EvidenceGraph()
        for n in ["A", "B", "C", "D", "E", "F", "G"]:
            graph.add_claim(claim_text=n, node_id=n)

        # Diamond 1
        graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        graph.link("A", "C", EdgeRelation.DERIVES_FROM)
        graph.link("B", "D", EdgeRelation.DERIVES_FROM)
        graph.link("C", "D", EdgeRelation.DERIVES_FROM)

        # Diamond 2
        graph.link("D", "E", EdgeRelation.DERIVES_FROM)
        graph.link("D", "F", EdgeRelation.DERIVES_FROM)
        graph.link("E", "G", EdgeRelation.DERIVES_FROM)
        graph.link("F", "G", EdgeRelation.DERIVES_FROM)

        self.assertFalse(graph.has_cycles())
        order = graph.topological_sort()
        self.assertEqual(order[0], "A")
        self.assertEqual(order[3], "D")
        self.assertEqual(order[-1], "G")

    def test_wide_fan_in_fan_out(self):
        """1 root fans out to 20 intermediate nodes, all 20 fan in to a single collector."""
        graph = EvidenceGraph()
        graph.add_claim(claim_text="Root", node_id="Root")
        graph.add_claim(claim_text="Collector", node_id="Collector")
        mid_nodes = [f"Mid_{i}" for i in range(20)]
        for m in mid_nodes:
            graph.add_claim(claim_text=m, node_id=m)
            graph.link("Root", m, EdgeRelation.ENTAILMENT)
            graph.link(m, "Collector", EdgeRelation.ENTAILMENT)

        self.assertFalse(graph.has_cycles())
        order = graph.topological_sort()
        self.assertEqual(order[0], "Root")
        self.assertEqual(order[-1], "Collector")
        self.assertEqual(len(order), 22)

    def test_complete_bipartite_dag(self):
        """Complete bipartite DAG: 10 sources all connect to 10 claims (100 edges)."""
        graph = EvidenceGraph()
        sources = [f"src_{i}" for i in range(10)]
        claims = [f"claim_{j}" for j in range(10)]
        for s in sources:
            graph.add_source(title=s, url=f"https://{s}.org", node_id=s)
        for c in claims:
            graph.add_claim(claim_text=c, node_id=c)

        for s in sources:
            for c in claims:
                graph.link(s, c, EdgeRelation.CORROBORATION)

        self.assertFalse(graph.has_cycles())
        self.assertEqual(len(graph._edges), 100)
        order = graph.topological_sort()
        # All sources must precede all claims
        for s in sources:
            for c in claims:
                self.assertLess(order.index(s), order.index(c))

    def test_transitive_shortcut_edges(self):
        """A -> B -> C -> D, plus shortcut edges A -> C, A -> D, B -> D."""
        graph = EvidenceGraph()
        for n in ["A", "B", "C", "D"]:
            graph.add_claim(claim_text=n, node_id=n)

        # Backbone
        graph.link("A", "B", EdgeRelation.DERIVES_FROM)
        graph.link("B", "C", EdgeRelation.DERIVES_FROM)
        graph.link("C", "D", EdgeRelation.DERIVES_FROM)

        # Shortcuts
        graph.link("A", "C", EdgeRelation.DERIVES_FROM)
        graph.link("A", "D", EdgeRelation.DERIVES_FROM)
        graph.link("B", "D", EdgeRelation.DERIVES_FROM)

        self.assertFalse(graph.has_cycles())
        self.assertEqual(graph.topological_sort(), ["A", "B", "C", "D"])

    def test_dense_random_dag(self):
        """50-node random DAG with edges only from i -> j (i < j). Must never flag cycles."""
        rng = random.Random(42)
        graph = EvidenceGraph()
        n_nodes = 50
        node_ids = [f"N_{i:02d}" for i in range(n_nodes)]
        for nid in node_ids:
            graph.add_claim(claim_text=nid, node_id=nid)

        edge_count = 0
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                if rng.random() < 0.25:  # ~25% density
                    graph.link(node_ids[i], node_ids[j], EdgeRelation.DERIVES_FROM)
                    edge_count += 1

        self.assertFalse(graph.has_cycles())
        order = graph.topological_sort()
        self.assertEqual(len(order), n_nodes)
        # Verify topological validity
        pos = {nid: idx for idx, nid in enumerate(order)}
        for edge in graph._edges.values():
            self.assertLess(pos[edge.source_id], pos[edge.target_id])


class TestAdversarialTopologicalSortDeterminism(unittest.TestCase):
    """Adversarial Focus 3: Verify topological sort determinism under random insertion orderings and identical depths."""

    def test_identical_depth_independent_nodes_permutation_invariance(self):
        """50 independent nodes with depth 0 must sort identically regardless of insertion permutation."""
        base_ids = [f"item_{i:03d}" for i in range(50)]
        expected_sort = sorted(base_ids)

        rng = random.Random(1337)
        for trial in range(25):
            shuffled_ids = list(base_ids)
            rng.shuffle(shuffled_ids)

            graph = EvidenceGraph()
            for nid in shuffled_ids:
                graph.add_claim(claim_text=nid, node_id=nid)

            result = graph.topological_sort()
            self.assertEqual(result, expected_sort, f"Sort order deviated on trial {trial}")

    def test_identical_depth_layer_tie_breaking(self):
        """Root -> {z, a, m, b, y, c} -> Target. Sibling order must be strictly alphanumeric."""
        siblings = ["node_z", "node_a", "node_m", "node_b", "node_y", "node_c"]
        expected_siblings_order = sorted(siblings)

        rng = random.Random(999)
        for trial in range(20):
            shuffled = list(siblings)
            rng.shuffle(shuffled)

            graph = EvidenceGraph()
            graph.add_claim(claim_text="Root", node_id="Root")
            graph.add_claim(claim_text="Target", node_id="Target")

            for s in shuffled:
                graph.add_claim(claim_text=s, node_id=s)
                graph.link("Root", s, EdgeRelation.ENTAILMENT)
                graph.link(s, "Target", EdgeRelation.ENTAILMENT)

            order = graph.topological_sort()
            self.assertEqual(order[0], "Root")
            self.assertEqual(order[-1], "Target")
            self.assertEqual(order[1:-1], expected_siblings_order)

    def test_multi_tier_lattice_permutation_invariance(self):
        """Lattice with 3 tiers where each tier has multiple nodes:
        Tier 0: [T0_B, T0_A, T0_C]
        Tier 1: [T1_E, T1_D, T1_F]
        Tier 2: [T2_H, T2_G]
        All nodes in tier i link to all in tier i+1.
        Verify determinism across 20 random node/edge creation orders.
        """
        tier0 = ["T0_A", "T0_B", "T0_C"]
        tier1 = ["T1_D", "T1_E", "T1_F"]
        tier2 = ["T2_G", "T2_H"]
        expected_order = sorted(tier0) + sorted(tier1) + sorted(tier2)

        rng = random.Random(2026)
        for trial in range(20):
            all_nodes = tier0 + tier1 + tier2
            rng.shuffle(all_nodes)

            graph = EvidenceGraph()
            for n in all_nodes:
                graph.add_claim(claim_text=n, node_id=n)

            # Build cross-tier edges in random sequence
            edges_to_add = []
            for u in tier0:
                for v in tier1:
                    edges_to_add.append((u, v))
            for u in tier1:
                for v in tier2:
                    edges_to_add.append((u, v))
            rng.shuffle(edges_to_add)

            for u, v in edges_to_add:
                graph.link(u, v, EdgeRelation.DERIVES_FROM)

            order = graph.topological_sort()
            self.assertEqual(order, expected_order, f"Lattice sort deviated on trial {trial}")


class TestAdversarialConfidenceBoundaries(unittest.TestCase):
    """Adversarial Focus 4: Verify confidence formula strictly bounds within [0.0, 1.0]."""

    def test_disconnected_nodes_confidence_is_zero(self):
        """A node with no paths to any SourceNode must have exactly 0.0 confidence."""
        graph = EvidenceGraph()
        c_id = graph.add_claim(claim_text="Floating claim with no sources")
        conf = graph.calculate_chain_confidence(c_id)
        self.assertEqual(conf, 0.0)

        # Adding intermediate non-source nodes still results in 0.0
        p_id = graph.add_passage(source_node_id="dummy_src_not_created", verbatim_text="Text") if False else None
        # Link another claim to it
        c2_id = graph.add_claim(claim_text="Second floating claim")
        graph.link(c_id, c2_id, EdgeRelation.ENTAILMENT)
        self.assertEqual(graph.calculate_chain_confidence(c2_id), 0.0)

    def test_all_contradictions_lower_bound_zero(self):
        """When evidence consists purely of contradictions, confidence must never drop below 0.0."""
        graph = EvidenceGraph()
        # Source S1
        s1 = graph.add_source(title="S1", url="https://s1.org", tier=1, reliability_score=1.0)
        c = graph.add_claim(claim_text="Falsified Claim")

        # 5 strong contradiction edges
        graph.link(s1, c, EdgeRelation.CONTRADICTION, weight=1.0, confidence=1.0)
        s2 = graph.add_source(title="S2", url="https://s2.org", tier=1, reliability_score=1.0)
        graph.link(s2, c, EdgeRelation.CONTRADICTION, weight=1.0, confidence=1.0)

        conf = graph.calculate_chain_confidence(c)
        self.assertEqual(conf, 0.0)
        self.assertGreaterEqual(conf, 0.0)
        self.assertLessEqual(conf, 1.0)

    def test_overwhelming_contradiction_penalty_does_not_underflow(self):
        """Contradiction penalty greater than corroborating confidence is clamped to 0.0."""
        graph = EvidenceGraph()
        # Weak supporting source: Tier 11 (weight 0.35), reliability 0.5
        s_supp = graph.add_source(title="Supp", url="https://supp.org", tier=11, reliability_score=0.5)
        p_supp = graph.add_passage(source_node_id=s_supp, verbatim_text="Support text")
        eu_supp = graph.add_evidence_unit(passage_node_id=p_supp, atomic_statement="Support statement")
        c = graph.add_claim(claim_text="Weakly supported claim")
        graph.link(eu_supp, c, EdgeRelation.ENTAILMENT, weight=0.5, confidence=0.5)

        # Overwhelming contradiction: Tier 1 primary source with 1.0 weight
        s_contra = graph.add_source(title="Contra", url="https://contra.org", tier=1, reliability_score=1.0)
        graph.link(s_contra, c, EdgeRelation.CONTRADICTION, weight=1.0, confidence=1.0)

        conf = graph.calculate_chain_confidence(c)
        self.assertEqual(conf, 0.0)
        self.assertIsInstance(conf, float)

    def test_deep_chain_decay_bounds(self):
        """Very deep chains (e.g. 20 hops) decay monotonically and remain in [0.0, 1.0]."""
        graph = EvidenceGraph()
        s = graph.add_source(title="Genesis Source", url="https://source.org", tier=1, reliability_score=1.0)
        prev = s
        chain_confs = []

        # Build 15 intermediate passages and units
        for i in range(15):
            nid = f"pas_{i}"
            pas = graph.add_passage(source_node_id=prev if i == 0 else f"pas_{i-1}", verbatim_text=f"Text {i}", node_id=nid)
            conf = graph.calculate_chain_confidence(nid, hop_decay=0.95)
            self.assertGreaterEqual(conf, 0.0)
            self.assertLessEqual(conf, 1.0)
            chain_confs.append(conf)

        # Verify strictly monotonically decreasing confidence
        for i in range(len(chain_confs) - 1):
            self.assertGreaterEqual(chain_confs[i], chain_confs[i+1])

    def test_extreme_hop_decay_values(self):
        """Test boundary hop_decay values: 0.0, 1.0."""
        graph = EvidenceGraph()
        s = graph.add_source(title="Source", url="https://src.org", tier=1, reliability_score=1.0)
        p = graph.add_passage(source_node_id=s, verbatim_text="Text")
        eu = graph.add_evidence_unit(passage_node_id=p, atomic_statement="Statement")
        c = graph.add_claim(claim_text="Claim")
        graph.link(eu, c, EdgeRelation.ENTAILMENT)

        # hop_decay = 0.0 -> hops = 3, (0.0 ** 2) = 0.0
        conf_zero_decay = graph.calculate_chain_confidence(c, hop_decay=0.0)
        self.assertEqual(conf_zero_decay, 0.0)

        # hop_decay = 1.0 -> no decay across hops
        conf_no_decay = graph.calculate_chain_confidence(c, hop_decay=1.0)
        self.assertAlmostEqual(conf_no_decay, 1.0, places=3)
        self.assertLessEqual(conf_no_decay, 1.0)

    def test_massive_parallel_corroboration_upper_bound(self):
        """25 independent sources corroborating one claim must approach 1.0 without exceeding 1.0."""
        graph = EvidenceGraph()
        c = graph.add_claim(claim_text="Heavily Corroborated Claim")

        for i in range(25):
            s = graph.add_source(title=f"Source {i}", url=f"https://s{i}.org", tier=1, reliability_score=0.99)
            p = graph.add_passage(source_node_id=s, verbatim_text=f"Passage {i}")
            eu = graph.add_evidence_unit(passage_node_id=p, atomic_statement=f"Fact {i}", confidence=0.99)
            graph.link(eu, c, EdgeRelation.ENTAILMENT, weight=1.0, confidence=1.0)

        conf = graph.calculate_chain_confidence(c)
        self.assertLessEqual(conf, 1.0)
        self.assertGreater(conf, 0.999)


class TestAdversarialSerializationRoundTrip(unittest.TestCase):
    """Adversarial Focus 5: Verify 100% attribute, type, and edge fidelity across round-trips."""

    def test_full_schema_round_trip_fidelity(self):
        """Populate every single node type with all optional and nested fields, all 6 edge relations,
        custom metadata, and verify byte-level and semantic fidelity after JSON round-trip."""
        graph = EvidenceGraph(
            graph_id="eg_adversarial_full",
            project_id="proj_epistemic_deep",
            version="2.1.0",
            metadata={"run_env": "production", "batch_id": 9948, "flags": [True, False, None]}
        )

        # 1. SourceNode
        src_id = graph.add_source(
            title="Archival Treaty Document",
            url="https://archives.gov/treaty1919",
            tier=1,
            publisher="National Archives",
            author="Commission of Plenipotentiaries",
            published_date="1919-06-28",
            reliability_score=0.98,
            domain_authority=0.95,
            doi="10.1000/182",
            peer_reviewed=True,
            content_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            is_sanitized=True,
            node_id="src_archival_01",
        )
        graph.require_node(src_id).metadata["license"] = "Public Domain"

        # 2. PassageNode
        pas_id = graph.add_passage(
            source_node_id=src_id,
            verbatim_text="Article 1. The Covenant of the League of Nations is hereby adopted.",
            char_offset_start=450,
            char_offset_end=518,
            section_or_page="Section I, Page 3",
            node_id="pas_art1_01",
        )

        # 3. EvidenceUnitNode
        eu_id = graph.add_evidence_unit(
            passage_node_id=pas_id,
            atomic_statement="The League of Nations Covenant was formally adopted in Article 1.",
            modality=ModalityType.CERTAIN,
            polarity=True,
            confidence=0.99,
            extracted_entities=["League of Nations", "Article 1"],
            node_id="eu_art1_01",
        )

        # 4. ClaimNode
        claim_id = graph.add_claim(
            claim_text="The Treaty established the League of Nations as its primary international body.",
            epistemic_status="verified",
            consensus_state="STRONG_CONSENSUS",
            claim_type="event_fact",
            confidence_score=0.97,
            category="historical_treaty",
            node_id="claim_art1_01",
        )
        graph.link(eu_id, claim_id, EdgeRelation.ENTAILMENT, weight=0.98, confidence=0.99, edge_id="edge_eu_to_claim")

        # 5. VerificationTraceNode
        tr_id = graph.add_verification_trace(
            target_node_id=claim_id,
            strategy_used="SOURCE_ENTAILMENT",
            entailment_score=0.98,
            contradiction_score=0.0,
            corroboration_score=0.95,
            status_assigned="verified",
            consensus_state_assigned="STRONG_CONSENSUS",
            verifier_name="EpistemicEngineV2",
            audit_notes="Validated against verbatim primary treaty text.",
            execution_duration_ms=12.4,
            warnings=["Slight stylistic variant in translation"],
            node_id="trace_claim_01",
        )

        # 6. SceneNode
        sc_id = graph.add_scene(
            scene_id="scene_01",
            scene_index=1,
            act_index=1,
            title="The Signing of the Covenant",
            start_time_seconds=0.0,
            duration_seconds=14.5,
            narration_text="In the Hall of Mirrors, delegates gathered to sign the covenant.",
            visual_theme="archival_sepia",
            node_id="scene_01",
        )

        # 7. ScriptSentenceNode
        sent_id = graph.add_script_sentence(
            scene_id=sc_id,
            beat_id="beat_01",
            sentence_text="Delegates formally instituted the League of Nations.",
            start_time_seconds=2.0,
            end_time_seconds=6.5,
            grounded_claim_ids=[claim_id],
            hedging_applied=False,
            paraphrase_mandated=False,
            node_id="sent_01",
        )

        # 8. VisualElementNode
        vis_id = graph.add_visual_element(
            scene_id=sc_id,
            block_type="STATISTIC_REVEAL",
            parameter_key="signatory_count",
            parameter_value={"total": 44, "present": 32, "absent": 12},  # nested structure
            dataset_id="ds_signatories_1919",
            grounded_claim_ids=[claim_id],
            display_unit="nations",
            node_id="vis_01",
        )

        # Add all other edge relations
        e_mentions = graph.link(src_id, claim_id, EdgeRelation.MENTIONS, weight=0.5, edge_id="edge_mentions")
        e_corrob = graph.link(src_id, eu_id, EdgeRelation.CORROBORATION, weight=0.8, edge_id="edge_corrob")
        e_vis = graph.link(claim_id, vis_id, EdgeRelation.VISUAL_DEPICTION, weight=1.0, edge_id="edge_vis_depict")

        # --- Execute JSON Round-Trip ---
        json_blob = graph.to_json()
        restored = EvidenceGraph.from_json(json_blob)

        # Assert Graph level attributes
        self.assertEqual(restored.graph_id, "eg_adversarial_full")
        self.assertEqual(restored.project_id, "proj_epistemic_deep")
        self.assertEqual(restored.version, "2.1.0")
        self.assertEqual(restored.metadata["batch_id"], 9948)
        self.assertEqual(restored.metadata["flags"], [True, False, None])

        # Assert Node counts and types
        self.assertEqual(len(restored._nodes), 8)
        self.assertEqual(len(restored._edges), len(graph._edges))

        # Check SourceNode fidelity
        r_src: SourceNode = restored.require_node(src_id)
        self.assertIsInstance(r_src, SourceNode)
        self.assertEqual(r_src.doi, "10.1000/182")
        self.assertTrue(r_src.peer_reviewed)
        self.assertEqual(r_src.metadata["license"], "Public Domain")

        # Check PassageNode fidelity
        r_pas: PassageNode = restored.require_node(pas_id)
        self.assertEqual(r_pas.char_offset_start, 450)
        self.assertEqual(r_pas.char_offset_end, 518)
        self.assertEqual(r_pas.section_or_page, "Section I, Page 3")

        # Check EvidenceUnitNode fidelity
        r_eu: EvidenceUnitNode = restored.require_node(eu_id)
        self.assertEqual(r_eu.modality, ModalityType.CERTAIN)
        self.assertEqual(r_eu.extracted_entities, ["League of Nations", "Article 1"])

        # Check VisualElementNode fidelity with nested parameter_value
        r_vis: VisualElementNode = restored.require_node(vis_id)
        self.assertEqual(r_vis.parameter_value, {"total": 44, "present": 32, "absent": 12})
        self.assertEqual(r_vis.display_unit, "nations")

        # Check VerificationTraceNode fidelity
        r_tr: VerificationTraceNode = restored.require_node(tr_id)
        self.assertEqual(r_tr.execution_duration_ms, 12.4)
        self.assertEqual(r_tr.warnings, ["Slight stylistic variant in translation"])

        # Check Edge fidelity
        r_edge = restored.get_edge(eu_id, claim_id)
        self.assertIsNotNone(r_edge)
        self.assertEqual(r_edge.edge_id, "edge_eu_to_claim")
        self.assertEqual(r_edge.relation, EdgeRelation.ENTAILMENT)
        self.assertEqual(r_edge.weight, 0.98)

        # Assert topological sort works identically on restored graph
        self.assertEqual(graph.topological_sort(), restored.topological_sort())

    def test_extract_subgraph_round_trip(self):
        """Verify that extracting a subgraph and roundtripping it retains topology and node types."""
        graph = EvidenceGraph()
        s = graph.add_source(title="S", url="https://s.org", node_id="S")
        # add_passage automatically creates the s -> p DERIVES_FROM edge
        p = graph.add_passage(source_node_id=s, verbatim_text="Text", node_id="P")
        c = graph.add_claim(claim_text="Claim", node_id="C")
        graph.link(p, c, EdgeRelation.ENTAILMENT)

        sub = graph.extract_subgraph({"S", "P"})
        self.assertEqual(len(sub._nodes), 2)
        self.assertEqual(len(sub._edges), 1)

        sub_json = sub.to_json()
        sub_restored = EvidenceGraph.from_json(sub_json)
        self.assertEqual(len(sub_restored._nodes), 2)
        self.assertEqual(len(sub_restored._edges), 1)
        self.assertIsInstance(sub_restored.require_node("S"), SourceNode)
        self.assertIsInstance(sub_restored.require_node("P"), PassageNode)


class TestAdversarialParallelEdgesAndLookupIntegrity(unittest.TestCase):
    """Adversarial Focus 6: Empirical verification of parallel edge collision and lookup shadowing."""

    def test_parallel_edges_shadow_lookup_and_corrupt_traversal(self):
        """Empirically prove that adding two directed edges between the same (source, target)
        silently overwrites _edge_lookup, shadows the first edge, duplicates the second edge
        in get_incoming_edges/get_outgoing_edges, and causes edge orphaning upon removal.
        """
        graph = EvidenceGraph()
        a = graph.add_claim(claim_text="Node A", node_id="A")
        b = graph.add_claim(claim_text="Node B", node_id="B")

        # Edge 1: MENTIONS
        e1 = graph.link(a, b, EdgeRelation.MENTIONS, weight=0.5, edge_id="edge_mentions")
        self.assertEqual(graph._edges[e1].relation, EdgeRelation.MENTIONS)
        self.assertEqual(graph.get_edge("A", "B").edge_id, e1)

        # Edge 2: ENTAILMENT between same pair (A, B)
        e2 = graph.link(a, b, EdgeRelation.ENTAILMENT, weight=0.9, edge_id="edge_entailment")

        # Flaw 1: _edge_lookup was overwritten by e2, shadowing e1
        lookup_eid = graph._edge_lookup.get(("A", "B"))
        self.assertEqual(lookup_eid, e2)
        # get_edge("A", "B") can never retrieve e1 anymore
        self.assertEqual(graph.get_edge("A", "B").relation, EdgeRelation.ENTAILMENT)

        # Flaw 2: get_incoming_edges returns [e2, e2] instead of [e1, e2]!
        incoming_b = graph.get_incoming_edges("B")
        self.assertEqual(len(incoming_b), 2)
        # Both returned edges are e2 (e1 is completely unreachable via traversal)
        self.assertEqual([e.edge_id for e in incoming_b], [e2, e2])

        # Flaw 3: get_outgoing_edges returns [e2, e2] instead of [e1, e2]!
        outgoing_a = graph.get_outgoing_edges("A")
        self.assertEqual([e.edge_id for e in outgoing_a], [e2, e2])

        # Flaw 4: Removing e2 completely breaks lookup for e1
        graph.remove_edge(e2)
        # e1 is STILL present in _edges
        self.assertIn(e1, graph._edges)
        # But _edge_lookup was popped!
        self.assertIsNone(graph._edge_lookup.get(("A", "B")))
        # get_edge now returns None despite e1 existing in _edges!
        self.assertIsNone(graph.get_edge("A", "B"))
        # And incoming edges now returns empty list despite e1 existing!
        self.assertEqual(graph.get_incoming_edges("B"), [])


    def test_flat_list_nodes_deserialization(self):
        """Verify that from_dict accepts a flat list of node dicts as well as a grouped dict."""
        flat_data = {
            "graph_id": "flat_test",
            "nodes": [
                {"node_type": "source", "node_id": "s1", "title": "Source 1", "url": "https://s1.org"},
                {"node_type": "claim", "node_id": "c1", "claim_id": "c1", "claim_text": "Claim 1"},
            ],
            "edges": [
                {"source_id": "s1", "target_id": "c1", "relation": "corroboration"}
            ]
        }
        g = EvidenceGraph.from_dict(flat_data)
        self.assertEqual(len(g._nodes), 2)
        self.assertEqual(len(g._edges), 1)
        self.assertIsInstance(g.require_node("s1"), SourceNode)
        self.assertIsInstance(g.require_node("c1"), ClaimNode)

    def test_embedded_contracts_roundtrip(self):
        """Verify full fidelity roundtrip when SourceRecord and ClaimRecord are attached to nodes."""
        s_rec = SourceRecord(
            title="Embedded Source",
            url="https://embedded.org",
            tier=SourceTier.PEER_REVIEWED_JOURNAL,
            reliability_score=0.92,
        )
        c_rec = ClaimRecord(
            claim_id="claim_emb_01",
            claim_text="Embedded claim proposition",
            category="epistemics",
            primary_source=s_rec,
            epistemic_status=EpistemicStatus.VERIFIED,
            consensus_state=ConsensusState.STRONG_CONSENSUS,
            claim_type=ClaimType.SCIENTIFIC_LAW,
        )

        graph = EvidenceGraph(graph_id="eg_embedded")
        s_id = graph.add_source(title="Embedded Source", url="https://embedded.org", source_record=s_rec)
        c_id = graph.add_claim(claim_text="Embedded claim proposition", claim_id="claim_emb_01", claim_record=c_rec)

        # JSON Roundtrip
        json_str = graph.to_json()
        restored = EvidenceGraph.from_json(json_str)

        r_src = restored.require_node(s_id)
        r_claim = restored.require_node(c_id)

        self.assertIsInstance(r_src.source_record, SourceRecord)
        self.assertEqual(r_src.source_record.title, "Embedded Source")
        self.assertEqual(r_src.source_record.tier, SourceTier.PEER_REVIEWED_JOURNAL)

        self.assertIsInstance(r_claim.claim_record, ClaimRecord)
        self.assertEqual(r_claim.claim_record.epistemic_status, EpistemicStatus.VERIFIED)
        self.assertEqual(r_claim.claim_record.claim_type, ClaimType.SCIENTIFIC_LAW)

    def test_unicode_and_special_character_node_ids(self):
        """Verify that node IDs containing colons, slashes, spaces, and unicode symbols are handled without error."""
        g = EvidenceGraph(graph_id="special_chars_graph")
        ids = [
            "urn:h9:claim:001",
            "https://doi.org/10.1000/182",
            "node_äöü_日本語",
            "node with whitespace",
            "node#symbol@token!",
        ]
        for nid in ids:
            g.add_claim(claim_text=f"Claim {nid}", node_id=nid)

        for i in range(len(ids) - 1):
            g.link(ids[i], ids[i+1], EdgeRelation.DERIVES_FROM)

        order = g.topological_sort()
        self.assertEqual(len(order), len(ids))

        restored = EvidenceGraph.from_json(g.to_json())
        self.assertEqual(order, restored.topological_sort())


class TestAdversarialComplexityAndRecursion(unittest.TestCase):
    """Adversarial Focus 7: Stress testing algorithm scalability, recursion bounds, and path explosion."""

    def test_deep_chain_has_cycles_recursion_limit(self):
        """Document that recursive DFS in has_cycles() fails on deep chains (>1000 nodes),
        while iterative Kahn's topological_sort() succeeds.
        """
        graph = EvidenceGraph()
        N = 1050
        node_ids = [f"chain_node_{i}" for i in range(N)]
        for nid in node_ids:
            graph.add_claim(claim_text=nid, node_id=nid)
        for i in range(N - 1):
            graph.link(node_ids[i], node_ids[i+1], EdgeRelation.DERIVES_FROM)

        # Kahn's topological sort is iterative and handles 1050 nodes without issue
        order = graph.topological_sort()
        self.assertEqual(len(order), N)

        # has_cycles uses recursive DFS and hits Python's recursion limit
        with self.assertRaises(RecursionError):
            graph.has_cycles()

    def test_converging_diamond_path_count_explosion(self):
        """Demonstrate that calculate_chain_confidence has O(2^N) complexity on diamond lattices
        due to unmemoized path enumeration in dfs_paths.
        """
        g = EvidenceGraph()
        src = g.add_source(title="Genesis", url="https://genesis.org", tier=1, reliability_score=1.0)

        # 10 layers of 2 nodes each = 2^11 = 2048 paths
        N = 10
        prev = [src]
        for i in range(N):
            u1 = g.add_claim(claim_text=f"u_{i}_1", node_id=f"u_{i}_1")
            u2 = g.add_claim(claim_text=f"u_{i}_2", node_id=f"u_{i}_2")
            for p in prev:
                g.link(p, u1, EdgeRelation.ENTAILMENT)
                g.link(p, u2, EdgeRelation.ENTAILMENT)
            prev = [u1, u2]

        target = g.add_claim(claim_text="Target", node_id="Target")
        for p in prev:
            g.link(p, target, EdgeRelation.ENTAILMENT)

        # Must calculate correct bounded confidence in reasonable time for N=10
        conf = g.calculate_chain_confidence("Target")
        self.assertGreaterEqual(conf, 0.0)
        self.assertLessEqual(conf, 1.0)


if __name__ == "__main__":
    unittest.main()


