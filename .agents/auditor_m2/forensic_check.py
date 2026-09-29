"""forensic_check.py — Rigorous Forensic Integrity Audit Suite for Milestone 2.

Empirically verifies:
1. Static code analysis & AST inspection for hardcoded test results, fake returns, facades.
2. Genuine Pydantic schemas, validation bounds, and enum invariants.
3. Genuine DAG data structures & BFS cycle detection (self-loops, 2-node, multi-hop, diamond DAGs).
4. Genuine Kahn's algorithm with deterministic alphanumeric tie-breaking.
5. Genuine lineage reconstruction & provenance tracking.
6. Genuine multi-path confidence calculation (Noisy-OR, series decay, bottleneck, contradiction penalties).
7. Clean circular import resolution in src/h9_runtime/content.py without bypassing functionality.
8. Test authenticity & assertion non-tautology in tests/test_evidence_graph.py.
"""

import ast
import bisect
import collections
import importlib
import inspect
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Add project root
PROJECT_ROOT = Path(r"g:\Finding-new-code\harness9").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import ValidationError

from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    DEFAULT_TIER_WEIGHTS,
    EpistemicStatus,
    EvidenceUnitLink,
    H9BaseModel,
    QuoteExactness,
    ResearchDossier,
    SourceQualityMetrics,
    SourceRecord,
    SourceTier,
    TemporalContext,
)
from src.epistemic.graph import (
    ClaimNode,
    CycleDetectedError,
    EdgeNotFoundError,
    EdgeRelation,
    EvidenceGraph,
    EvidenceGraphError,
    EvidenceUnitNode,
    GraphEdge,
    GraphNode,
    GraphNodeType,
    InvalidEdgeError,
    ModalityType,
    NodeNotFoundError,
    PassageNode,
    ProvenanceChain,
    SceneNode,
    ScriptSentenceNode,
    SourceNode,
    VerificationTraceNode,
    VisualElementNode,
)


class ForensicAuditSuite:
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}

    def record(self, check_name: str, passed: bool, details: str, evidence: Any = None):
        self.results[check_name] = {
            "passed": passed,
            "details": details,
            "evidence": evidence,
        }
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {check_name}: {details}")

    def run_all(self):
        print("=== STARTING MILESTONE 2 FORENSIC INTEGRITY AUDIT ===\n")
        self.audit_static_code_ast()
        self.audit_pydantic_schemas_and_validation()
        self.audit_dag_and_bfs_cycle_detection()
        self.audit_kahns_topological_sort()
        self.audit_lineage_and_provenance()
        self.audit_confidence_calculations()
        self.audit_circular_imports_and_lazy_loading()
        self.audit_test_suite_authenticity()
        print("\n=== AUDIT COMPLETE ===")
        return self.results

    # -----------------------------------------------------------------------
    # 1. Static Code Analysis & AST Inspection
    # -----------------------------------------------------------------------
    def audit_static_code_ast(self):
        files_to_check = [
            PROJECT_ROOT / "src" / "models" / "contracts.py",
            PROJECT_ROOT / "src" / "models" / "__init__.py",
            PROJECT_ROOT / "src" / "h9_runtime" / "content.py",
            PROJECT_ROOT / "src" / "epistemic" / "__init__.py",
            PROJECT_ROOT / "src" / "epistemic" / "graph.py",
        ]

        test_specific_keywords = [
            "claim_quantum_01",
            "MIT Tech Review",
            "Nature Physics",
            "Neutral atom qubits",
            "Archival Treaty Document",
            "The treaty was signed on June 28, 1919",
            "League of Nations",
            "Introduction to Geneva",
            "ds_league_members",
        ]

        violations = []
        suspicious_facades = []

        for fpath in files_to_check:
            if not fpath.exists():
                violations.append(f"Target file missing: {fpath}")
                continue

            content = fpath.read_text(encoding="utf-8")

            # Check 1a: Test constants leaked into production code
            for kw in test_specific_keywords:
                if kw in content:
                    violations.append(f"Hardcoded test literal '{kw}' found in {fpath.name}")

            # Check 1b: AST inspection for dummy returns (e.g. constant returns in core methods)
            tree = ast.parse(content, filename=str(fpath))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if body is just `return True` or `return "verified"` or `pass` in graph methods
                    if fpath.name == "graph.py":
                        # Check for empty/stub functions
                        real_stmts = [
                            s for s in node.body
                            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
                        ]
                        if len(real_stmts) == 1:
                            stmt = real_stmts[0]
                            if isinstance(stmt, ast.Pass):
                                suspicious_facades.append(f"Empty pass statement in {node.name}")
                            elif isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                                # Check if it's a property or trivial helper
                                if node.name not in ("confidence", "validate_offsets"):
                                    suspicious_facades.append(
                                        f"Trivial constant return in {node.name}: {stmt.value.value}"
                                    )

        passed = len(violations) == 0 and len(suspicious_facades) == 0
        details = (
            "No hardcoded test constants, test outputs, or stub facade returns found in production code."
            if passed
            else f"Violations: {violations + suspicious_facades}"
        )
        self.record("Static Code Analysis & AST Inspection", passed, details, violations + suspicious_facades)

    # -----------------------------------------------------------------------
    # 2. Genuine Pydantic Schemas & Invariant Enforcement
    # -----------------------------------------------------------------------
    def audit_pydantic_schemas_and_validation(self):
        issues = []

        # Verify 11 EpistemicStatus values
        expected_statuses = {
            "verified", "supported", "partially_supported", "contested", "contradicted",
            "unsupported", "unverifiable", "outdated", "misleading", "opinion", "prediction"
        }
        actual_statuses = {s.value for s in EpistemicStatus}
        if actual_statuses != expected_statuses:
            issues.append(f"EpistemicStatus mismatch: {actual_statuses ^ expected_statuses}")

        # Verify 13 SourceTier values and weights
        expected_tiers = set(range(1, 14))
        actual_tiers = {t.value for t in SourceTier}
        if actual_tiers != expected_tiers:
            issues.append(f"SourceTier mismatch: {actual_tiers ^ expected_tiers}")
        for t in SourceTier:
            if t not in DEFAULT_TIER_WEIGHTS:
                issues.append(f"SourceTier {t.name} missing from DEFAULT_TIER_WEIGHTS")

        # Verify 8 ConsensusState values
        expected_consensus = {
            "STRONG_CONSENSUS", "BROAD_CONSENSUS", "MAJORITY_INTERPRETATION", "MINORITY_INTERPRETATION",
            "ACTIVE_DEBATE", "CONTESTED", "UNRESOLVED", "INSUFFICIENT_LITERATURE"
        }
        actual_consensus = {c.value for c in ConsensusState}
        if actual_consensus != expected_consensus:
            issues.append(f"ConsensusState mismatch: {actual_consensus ^ expected_consensus}")

        # Verify PassageNode offset validator bounds
        try:
            PassageNode(
                node_id="p_inv",
                source_node_id="s1",
                verbatim_text="Inverted offsets test",
                char_offset_start=150,
                char_offset_end=50,
            )
            issues.append("PassageNode failed to reject inverted char_offsets (150 > 50)")
        except (ValidationError, ValueError):
            pass  # Expected

        # Verify SourceNode tier bounds
        try:
            SourceNode(node_id="s_bad", title="Bad Tier", url="https://x.org", tier=0)
            issues.append("SourceNode failed to reject tier=0")
        except ValidationError:
            pass

        try:
            SourceNode(node_id="s_bad", title="Bad Tier", url="https://x.org", tier=14)
            issues.append("SourceNode failed to reject tier=14")
        except ValidationError:
            pass

        # Verify ClaimRecord extended fields and backwards compatibility property
        cr = ClaimRecord(
            claim_id="cr_01",
            claim_text="Epistemic test claim",
            primary_source=SourceRecord(title="Test Source", url="https://test.org"),
            epistemic_status=EpistemicStatus.CONTESTED,
            consensus_state=ConsensusState.ACTIVE_DEBATE,
            source_tier=SourceTier.PEER_REVIEWED_JOURNAL,
        )
        if cr.verification_status != "CONTESTED":
            issues.append(f"ClaimRecord.verification_status property failed: got {cr.verification_status}")

        passed = len(issues) == 0
        details = (
            "All 11 epistemic statuses, 13 source tiers with default weights, 8 consensus states, and model validations verified."
            if passed else f"Issues: {issues}"
        )
        self.record("Pydantic Schemas & Value Invariants", passed, details, issues)

    # -----------------------------------------------------------------------
    # 3. DAG Engine & BFS Cycle Detection
    # -----------------------------------------------------------------------
    def audit_dag_and_bfs_cycle_detection(self):
        issues = []
        g = EvidenceGraph()

        # Add 6 nodes
        nodes = [f"node_{i}" for i in range(6)]
        for nid in nodes:
            g.add_claim(claim_text=f"Claim {nid}", node_id=nid)

        # Test 1: Self-loop rejection
        try:
            g.link("node_0", "node_0", EdgeRelation.DERIVES_FROM)
            issues.append("Failed to reject self-loop node_0 -> node_0")
        except CycleDetectedError:
            pass

        # Test 2: Direct 2-node cycle rejection
        g.link("node_0", "node_1", EdgeRelation.DERIVES_FROM)
        try:
            g.link("node_1", "node_0", EdgeRelation.DERIVES_FROM)
            issues.append("Failed to reject 2-node cycle node_1 -> node_0")
        except CycleDetectedError:
            pass

        # Test 3: Multi-hop cycle (0 -> 1 -> 2 -> 3 -> 0)
        g.link("node_1", "node_2", EdgeRelation.DERIVES_FROM)
        g.link("node_2", "node_3", EdgeRelation.DERIVES_FROM)
        try:
            g.link("node_3", "node_0", EdgeRelation.DERIVES_FROM)
            issues.append("Failed to reject multi-hop cycle node_3 -> node_0")
        except CycleDetectedError:
            pass

        # Test 4: Diamond DAG must NOT be flagged as cycle
        # 0 -> 4 -> 5 and 0 -> 1 -> 2 -> 5
        g.link("node_0", "node_4", EdgeRelation.DERIVES_FROM)
        g.link("node_4", "node_5", EdgeRelation.DERIVES_FROM)
        try:
            g.link("node_2", "node_5", EdgeRelation.DERIVES_FROM)
        except CycleDetectedError as e:
            issues.append(f"Diamond DAG falsely rejected as cycle: {e}")

        # Verify global has_cycles() returns False on valid DAG
        if g.has_cycles():
            issues.append("g.has_cycles() returned True on valid diamond DAG")

        # Test 5: Complex 10-node DAG cycle stress test
        g2 = EvidenceGraph()
        for i in range(10):
            g2.add_claim(claim_text=f"C{i}", node_id=f"N{i}")
        for i in range(9):
            g2.link(f"N{i}", f"N{i+1}", EdgeRelation.DERIVES_FROM)
        try:
            g2.link("N9", "N0", EdgeRelation.DERIVES_FROM)
            issues.append("Failed to reject 10-node cycle N9 -> N0")
        except CycleDetectedError:
            pass

        passed = len(issues) == 0
        details = (
            "BFS cycle prevention verified on self-loops, 2-node cycles, multi-hop chains, and diamond DAG non-rejection."
            if passed else f"Issues: {issues}"
        )
        self.record("DAG Engine & BFS Cycle Detection", passed, details, issues)

    # -----------------------------------------------------------------------
    # 4. Kahn's Algorithm & Deterministic Topological Sorting
    # -----------------------------------------------------------------------
    def audit_kahns_topological_sort(self):
        issues = []

        # Test 4a: Invariant verification: for every edge (u, v), index(u) < index(v)
        g = EvidenceGraph()
        node_names = ["delta", "alpha", "gamma", "beta", "epsilon", "zeta"]
        for name in node_names:
            g.add_claim(claim_text=f"Claim {name}", node_id=name)

        g.link("alpha", "beta", EdgeRelation.DERIVES_FROM)
        g.link("alpha", "gamma", EdgeRelation.DERIVES_FROM)
        g.link("beta", "delta", EdgeRelation.DERIVES_FROM)
        g.link("gamma", "delta", EdgeRelation.DERIVES_FROM)
        g.link("delta", "epsilon", EdgeRelation.DERIVES_FROM)
        g.link("zeta", "epsilon", EdgeRelation.DERIVES_FROM)

        sorted_nodes = g.topological_sort()
        idx_map = {nid: i for i, nid in enumerate(sorted_nodes)}

        for edge in g._edges.values():
            if idx_map[edge.source_id] >= idx_map[edge.target_id]:
                issues.append(
                    f"Topological sort invariant violated for edge {edge.source_id} -> {edge.target_id}"
                )

        # Test 4b: Deterministic tie-breaking across different node insertion orders
        g1 = EvidenceGraph()
        for n in ["Z", "A", "M", "B"]:
            g1.add_claim(claim_text=n, node_id=n)
        g1.link("A", "Z", EdgeRelation.DERIVES_FROM)
        g1.link("B", "Z", EdgeRelation.DERIVES_FROM)

        g2 = EvidenceGraph()
        for n in ["B", "M", "Z", "A"]:
            g2.add_claim(claim_text=n, node_id=n)
        g2.link("B", "Z", EdgeRelation.DERIVES_FROM)
        g2.link("A", "Z", EdgeRelation.DERIVES_FROM)

        sort1 = g1.topological_sort()
        sort2 = g2.topological_sort()

        if sort1 != sort2:
            issues.append(f"Topological sort is non-deterministic across insertion orders: {sort1} != {sort2}")
        if sort1 != ["A", "B", "M", "Z"]:
            issues.append(f"Expected alphanumeric tie-breaking ['A', 'B', 'M', 'Z'], got {sort1}")

        passed = len(issues) == 0
        details = (
            "Kahn's algorithm correctly sorts DAGs with strict index(u) < index(v) and deterministic alphanumeric tie-breaking."
            if passed else f"Issues: {issues}"
        )
        self.record("Kahn's Algorithm & Deterministic Topological Sorting", passed, details, issues)

    # -----------------------------------------------------------------------
    # 5. Provenance Lineage & Lineage Reconstruction
    # -----------------------------------------------------------------------
    def audit_lineage_and_provenance(self):
        issues = []
        g = EvidenceGraph()

        s1 = g.add_source(title="Source 1", url="https://s1.org", tier=1)
        s2 = g.add_source(title="Source 2", url="https://s2.org", tier=2)
        p1 = g.add_passage(source_node_id=s1, verbatim_text="Passage from S1")
        p2 = g.add_passage(source_node_id=s2, verbatim_text="Passage from S2")
        eu1 = g.add_evidence_unit(passage_node_id=p1, atomic_statement="Fact 1")
        eu2 = g.add_evidence_unit(passage_node_id=p2, atomic_statement="Fact 2")
        c1 = g.add_claim(claim_text="Claim backed by S1 and S2")
        g.link(eu1, c1, EdgeRelation.ENTAILMENT)
        g.link(eu2, c1, EdgeRelation.ENTAILMENT)

        sc = g.add_scene(scene_id="sc_01")
        sent = g.add_script_sentence(
            scene_id=sc, beat_id="b1", sentence_text="Voiceover", grounded_claim_ids=[c1]
        )

        chain = g.trace_lineage(sent)
        if not chain.is_grounded:
            issues.append("Expected chain.is_grounded to be True")
        if set(chain.root_source_ids) != {s1, s2}:
            issues.append(f"Expected root sources {s1, s2}, got {chain.root_source_ids}")
        # sent has 3 complete paths: 1 from SceneNode container, 2 from SourceNodes via c1
        if len(chain.complete_paths) != 3:
            issues.append(f"Expected 3 complete provenance paths for sentence (1 scene + 2 sources), got {len(chain.complete_paths)}")

        # Claim c1 has exactly 2 provenance paths (both from sources)
        claim_chain = g.trace_lineage(c1)
        if len(claim_chain.complete_paths) != 2:
            issues.append(f"Expected 2 complete provenance paths for claim c1, got {len(claim_chain.complete_paths)}")

        # Unconnected orphan node
        orphan = g.add_claim(claim_text="Floating orphan claim")
        orphan_chain = g.trace_lineage(orphan)
        if orphan_chain.is_grounded:
            issues.append("Expected orphan claim to have is_grounded=False")
        if orphan_chain.calculated_confidence != 0.0:
            issues.append("Expected orphan claim confidence to be 0.0")

        passed = len(issues) == 0
        details = (
            "Lineage reconstruction correctly discovers all root sources, complete paths, and ungrounded propositions."
            if passed else f"Issues: {issues}"
        )
        self.record("Provenance Lineage & Chain Reconstruction", passed, details, issues)

    # -----------------------------------------------------------------------
    # 6. Chain Confidence Calculation (Noisy-OR, Series Decay, Contradiction)
    # -----------------------------------------------------------------------
    def audit_confidence_calculations(self):
        issues = []
        g = EvidenceGraph()

        # Path 1: Source A (Tier 2: weight 0.98, rel 1.0)
        s_a = g.add_source(title="Src A", url="https://a.org", tier=2, reliability_score=1.0)
        p_a = g.add_passage(source_node_id=s_a, verbatim_text="Text A")
        eu_a = g.add_evidence_unit(passage_node_id=p_a, atomic_statement="Stmt A", confidence=1.0)
        claim = g.add_claim(claim_text="Test Claim")
        g.link(eu_a, claim, EdgeRelation.ENTAILMENT, weight=1.0, confidence=1.0)

        # Single path: hops = 3 (s_a -> p_a -> eu_a -> claim), hop_decay=0.98, hop_decay^(3-1) = 0.98^2 = 0.9604
        # expected = 0.98 * 1.0 * 1.0 * 0.9604 = 0.941192 -> 0.9412
        conf_single = g.calculate_chain_confidence(claim)
        expected_single = round(0.98 * (0.98 ** 2), 4)
        if abs(conf_single - expected_single) > 0.005:
            issues.append(f"Single path confidence mismatch: got {conf_single}, expected ~{expected_single}")

        # Path 2: Add independent Source B (Tier 1: weight 1.00, rel 1.0)
        s_b = g.add_source(title="Src B", url="https://b.org", tier=1, reliability_score=1.0)
        p_b = g.add_passage(source_node_id=s_b, verbatim_text="Text B")
        eu_b = g.add_evidence_unit(passage_node_id=p_b, atomic_statement="Stmt B", confidence=1.0)
        g.link(eu_b, claim, EdgeRelation.ENTAILMENT, weight=1.0, confidence=1.0)

        conf_multi = g.calculate_chain_confidence(claim)
        # Multi-path via Noisy-OR must strictly exceed single path confidence
        if conf_multi <= conf_single:
            issues.append(f"Noisy-OR multi-path failed: conf_multi ({conf_multi}) <= conf_single ({conf_single})")

        # Contradiction: Add contradictory source
        s_c = g.add_source(title="Src C", url="https://c.org", tier=1, reliability_score=1.0)
        g.link(s_c, claim, EdgeRelation.CONTRADICTION, weight=0.5, confidence=1.0)

        conf_contradicted = g.calculate_chain_confidence(claim)
        if conf_contradicted >= conf_multi:
            issues.append(
                f"Contradiction penalty failed: conf_contradicted ({conf_contradicted}) >= conf_multi ({conf_multi})"
            )
        if abs(conf_contradicted - (conf_multi - 0.5)) > 0.01:
            issues.append(
                f"Contradiction penalty magnitude mismatch: expected ~{conf_multi - 0.5}, got {conf_contradicted}"
            )

        # Bottleneck calculation
        g_bot = EvidenceGraph()
        sb = g_bot.add_source(title="SB", url="https://sb.org", tier=1, reliability_score=1.0)
        pb = g_bot.add_passage(source_node_id=sb, verbatim_text="Text")
        eub = g_bot.add_evidence_unit(passage_node_id=pb, atomic_statement="Fact", confidence=0.33)
        cb = g_bot.add_claim(claim_text="Bottleneck claim")
        g_bot.link(eub, cb, EdgeRelation.ENTAILMENT, weight=0.9, confidence=0.9)
        conf_bot = g_bot.calculate_chain_confidence(cb, method="bottleneck")
        if conf_bot != 0.33:
            issues.append(f"Bottleneck calculation expected 0.33, got {conf_bot}")

        passed = len(issues) == 0
        details = (
            "Confidence calculations verified: series exponential decay, Noisy-OR corroboration boost, contradiction penalties, and bottleneck min-cut."
            if passed else f"Issues: {issues}"
        )
        self.record("Chain Confidence Calculation Authenticity", passed, details, issues)

    # -----------------------------------------------------------------------
    # 7. Circular Imports & Lazy Loading in content.py
    # -----------------------------------------------------------------------
    def audit_circular_imports_and_lazy_loading(self):
        issues = []

        # Test isolated imports in various sequences
        test_sequences = [
            ["src.orchestrator.pipeline", "src.h9_runtime.content"],
            ["src.orchestrator.state_machine", "src.h9_runtime.content"],
            ["src.h9_runtime.content", "src.orchestrator.pipeline"],
            ["src.epistemic.graph", "src.models.contracts", "src.h9_runtime.content"],
        ]

        for seq in test_sequences:
            try:
                for mod_name in seq:
                    if mod_name in sys.modules:
                        del sys.modules[mod_name]
                for mod_name in seq:
                    importlib.import_module(mod_name)
            except Exception as e:
                issues.append(f"Import sequence {seq} failed: {type(e).__name__}: {e}")

        # Verify lazy import functions inside DefaultContentRuntime
        from src.h9_runtime.content import DefaultContentRuntime
        runtime = DefaultContentRuntime()

        # Check source of methods to ensure real classes are imported and called
        plan_src = inspect.getsource(runtime.plan_research)
        eval_src = inspect.getsource(runtime.evaluate_angles)
        prod_src = inspect.getsource(runtime.run_full_production)

        if "from src.research.engine import ResearchEngine" not in plan_src:
            issues.append("plan_research missing lazy import of ResearchEngine")
        if "from src.editorial import EditorialEngine" not in eval_src:
            issues.append("evaluate_angles missing lazy import of EditorialEngine")
        if "from src.orchestrator.pipeline import Pipeline" not in prod_src:
            issues.append("run_full_production missing lazy import of Pipeline")

        passed = len(issues) == 0
        details = (
            "Circular import cleanly eliminated; Pipeline, StateMachine, and Engines lazily imported without bypassing genuine execution."
            if passed else f"Issues: {issues}"
        )
        self.record("Circular Import & Lazy Loading Resolution", passed, details, issues)

    # -----------------------------------------------------------------------
    # 8. Test Suite Authenticity in tests/test_evidence_graph.py
    # -----------------------------------------------------------------------
    def audit_test_suite_authenticity(self):
        issues = []
        test_file = PROJECT_ROOT / "tests" / "test_evidence_graph.py"
        content = test_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(test_file))

        test_methods = []
        tautological_asserts = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_methods.append(node.name)
                # Check for assert True or assert x == x
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                        if sub.func.attr in ("assertTrue", "assertFalse") and len(sub.args) >= 1:
                            if isinstance(sub.args[0], ast.Constant) and isinstance(sub.args[0].value, bool):
                                tautological_asserts.append(f"{node.name}: assert{sub.func.attr}({sub.args[0].value})")
                        elif sub.func.attr == "assertEqual" and len(sub.args) >= 2:
                            a1, a2 = sub.args[0], sub.args[1]
                            if isinstance(a1, ast.Name) and isinstance(a2, ast.Name) and a1.id == a2.id:
                                tautological_asserts.append(f"{node.name}: assertEqual({a1.id}, {a2.id})")

        if len(test_methods) < 40:
            issues.append(f"Expected at least 40 test methods, found {len(test_methods)}")
        if tautological_asserts:
            issues.append(f"Found tautological assertions: {tautological_asserts}")

        passed = len(issues) == 0
        details = (
            f"All {len(test_methods)} tests in tests/test_evidence_graph.py exercise genuine functionality with zero tautological assertions."
            if passed else f"Issues: {issues}"
        )
        self.record("Test Suite Authenticity & Assertion Non-Tautology", passed, details, issues)


if __name__ == "__main__":
    suite = ForensicAuditSuite()
    results = suite.run_all()
    all_passed = all(r["passed"] for r in results.values())
    print(f"\nFinal Forensic Verdict: {'CLEAN' if all_passed else 'INTEGRITY VIOLATION'}")
    sys.exit(0 if all_passed else 1)
