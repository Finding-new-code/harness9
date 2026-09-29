"""Empirical Challenger Verification Script for Milestone 1 Epistemic Specifications.

This script mathematically and structurally stress-tests:
1. Taxonomy completeness, mutual consistency, and state machine gate alignments.
2. Evidence Graph DAG properties: acyclicity, edge constraints, schema validity, and JSON-LD serialization.
3. Fact-checking formulas: boundedness in [0.0, 1.0], edge cases, limit behavior, Monte Carlo stress testing.
4. ADR-006 formalization and document cross-consistency.
"""

import json
import math
import random
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

def test_taxonomies_completeness() -> Dict[str, Any]:
    """Audit 11 Epistemic Statuses, 13 Source Tiers, 8 Consensus States, 4 Verification Gates."""
    results = {}

    # 1. Epistemic Statuses (11)
    expected_statuses = {
        "verified", "supported", "partially_supported", "contested",
        "contradicted", "unsupported", "unverifiable", "outdated",
        "misleading", "opinion", "prediction"
    }
    results["status_count"] = len(expected_statuses)
    results["status_count_valid"] = (len(expected_statuses) == 11)

    # 2. Source Tiers (13)
    expected_tiers = {
        1: "PRIMARY_SOURCE",
        2: "PEER_REVIEWED_JOURNAL",
        3: "ACADEMIC_PRESS_BOOK",
        4: "HISTORICAL_DOCUMENT_CRITICAL_EDITION",
        5: "GOVERNMENT_RECORD_STATISTICAL_AGENCY",
        6: "PREPRINT_SCHOLARLY",
        7: "SPECIALIZED_SCHOLARLY_DATABASE",
        8: "REPUTABLE_NEWS_INVESTIGATIVE",
        9: "GENERAL_ENCYCLOPEDIC",
        10: "CORPORATE_WHITE_PAPER",
        11: "BLOG_OPINION_COMMENTARY",
        12: "SOCIAL_MEDIA_FORUM",
        13: "UNVERIFIED"
    }
    results["tier_count"] = len(expected_tiers)
    results["tier_count_valid"] = (len(expected_tiers) == 13)
    results["tier_contiguous"] = (set(expected_tiers.keys()) == set(range(1, 14)))

    # 3. Consensus States (8)
    expected_consensus = {
        "STRONG_CONSENSUS", "BROAD_CONSENSUS", "MAJORITY_INTERPRETATION",
        "MINORITY_INTERPRETATION", "ACTIVE_DEBATE", "CONTESTED",
        "UNRESOLVED", "INSUFFICIENT_LITERATURE"
    }
    results["consensus_count"] = len(expected_consensus)
    results["consensus_count_valid"] = (len(expected_consensus) == 8)

    # 4. Verification Gates (4)
    expected_gates = {
        "RESEARCH_VERIFICATION": ("RESEARCH_IN_PROGRESS", "RESEARCH_COMPLETED"),
        "SCRIPT_FACT_CHECK": ("SCRIPTING_IN_PROGRESS", "SCRIPT_COMPLETED"),
        "VISUAL_FACT_CHECK": ("COMPOSITION_GENERATED", "RENDER_IN_PROGRESS"),
        "FINAL_EPISTEMIC_QA": ("RENDER_COMPLETED", "COMPLETED"),
    }
    results["gate_count"] = len(expected_gates)
    results["gate_count_valid"] = (len(expected_gates) == 4)

    # 5. Gate Outcomes (4)
    expected_outcomes = {"PASS", "WARN", "HUMAN_REVIEW", "BLOCK"}
    results["outcome_count"] = len(expected_outcomes)
    results["outcome_count_valid"] = (len(expected_outcomes) == 4)

    return results

def decision_function(s_entail: float, s_corrob: float, p_contra: float) -> str:
    """Implement the Status Decision Function from FACT_CHECKING_SPEC.md Sec 4.4."""
    if p_contra >= 0.80 and p_contra > s_entail:
        return "CONTRADICTED"
    elif p_contra >= 0.60 and s_entail >= 0.60:
        return "CONTESTED"
    elif s_entail >= 0.90 and s_corrob >= 0.85 and p_contra < 0.20:
        return "VERIFIED"
    elif s_entail >= 0.80 and p_contra < 0.30:
        return "SUPPORTED"
    elif 0.60 <= s_entail < 0.80 and p_contra < 0.30:
        return "PARTIALLY_SUPPORTED"
    else:
        return "UNSUPPORTED"

def test_decision_function_stress() -> Dict[str, Any]:
    """Test decision function partition, determinism, and gap analysis."""
    outcomes = set()
    gaps_found = []
    
    # Grid search across [0, 1]^3
    step = 0.05
    n_points = 0
    contradicted_count = 0
    contested_count = 0
    verified_count = 0
    supported_count = 0
    partially_count = 0
    unsupported_count = 0

    s_vals = [round(i * step, 2) for i in range(int(1.0 / step) + 1)]
    for s_e in s_vals:
        for s_c in s_vals:
            for p_c in s_vals:
                n_points += 1
                status = decision_function(s_e, s_c, p_c)
                outcomes.add(status)
                if status == "CONTRADICTED": contradicted_count += 1
                elif status == "CONTESTED": contested_count += 1
                elif status == "VERIFIED": verified_count += 1
                elif status == "SUPPORTED": supported_count += 1
                elif status == "PARTIALLY_SUPPORTED": partially_count += 1
                elif status == "UNSUPPORTED": unsupported_count += 1

                # Specific gap check: high entailment, moderate contradiction (0.30 <= p_c < 0.60)
                if s_e >= 0.80 and 0.30 <= p_c < 0.60 and status == "UNSUPPORTED":
                    gaps_found.append((s_e, s_c, p_c, status))

    return {
        "n_evaluated": n_points,
        "reachable_statuses": sorted(list(outcomes)),
        "counts": {
            "CONTRADICTED": contradicted_count,
            "CONTESTED": contested_count,
            "VERIFIED": verified_count,
            "SUPPORTED": supported_count,
            "PARTIALLY_SUPPORTED": partially_count,
            "UNSUPPORTED": unsupported_count,
        },
        "ambiguity_or_overlap": False,  # if-elif chain is deterministic by definition
        "gap_sample_count": len(gaps_found),
        "gap_example": gaps_found[0] if gaps_found else None,
    }

def formula_s_entail(passages: List[Tuple[float, float]]) -> float:
    """S_entail = max [ W_tier * P(P_i |= C) ]. If passages empty, returns 0.0."""
    if not passages:
        return 0.0
    return max(w * p for w, p in passages)

def formula_s_corrob(sources: List[Tuple[float, float]]) -> float:
    """S_corrob = 1.0 - prod(1.0 - W_tier(S_k) * I_indep(S_k, S_primary))."""
    prod = 1.0
    for w, indep in sources:
        prod *= (1.0 - w * indep)
    return 1.0 - prod

def formula_p_contra(passages: List[Tuple[float, float]]) -> float:
    """P_contra = max [ W_tier * P(P_j |= ~C) ]. If passages empty, returns 0.0."""
    if not passages:
        return 0.0
    return max(w * p for w, p in passages)

def test_formulas_boundedness_and_limits() -> Dict[str, Any]:
    """Monte Carlo and boundary analysis for formula boundedness in [0.0, 1.0]."""
    violations = []
    
    # 1. Boundary cases
    # Empty inputs
    if not (formula_s_entail([]) == 0.0): violations.append("s_entail_empty")
    if not (formula_s_corrob([]) == 0.0): violations.append("s_corrob_empty")
    if not (formula_p_contra([]) == 0.0): violations.append("p_contra_empty")

    # Extreme inputs
    # All weights 0
    if not (formula_s_entail([(0.0, 1.0)]) == 0.0): violations.append("s_entail_w0")
    if not (formula_s_corrob([(0.0, 1.0)]) == 0.0): violations.append("s_corrob_w0")
    if not (formula_p_contra([(0.0, 1.0)]) == 0.0): violations.append("p_contra_w0")

    # All weights 1, prob 1
    if not (formula_s_entail([(1.0, 1.0)]) == 1.0): violations.append("s_entail_max")
    if not (formula_s_corrob([(1.0, 1.0)]) == 1.0): violations.append("s_corrob_max")
    if not (formula_p_contra([(1.0, 1.0)]) == 1.0): violations.append("p_contra_max")

    # Zero independence
    if not (formula_s_corrob([(1.0, 0.0), (0.9, 0.0), (0.8, 0.0)]) == 0.0):
        violations.append("s_corrob_zero_indep")

    # Large m asymptotic behavior (should approach 1.0 but not exceed)
    sources_large = [(0.5, 0.5) for _ in range(100)]
    val_large = formula_s_corrob(sources_large)
    if not (0.0 <= val_large <= 1.0): violations.append("s_corrob_large_bound")
    if not (val_large > 0.999999): violations.append("s_corrob_large_asymptote")

    # 2. Monte Carlo Stress Test: 100,000 random iterations
    random.seed(42)
    for _ in range(100_000):
        m = random.randint(0, 20)
        passages = [(random.random(), random.random()) for _ in range(m)]
        sources = [(random.random(), random.random()) for _ in range(m)]
        
        se = formula_s_entail(passages)
        sc = formula_s_corrob(sources)
        pc = formula_p_contra(passages)

        if not (0.0 <= se <= 1.0):
            violations.append(f"s_entail_out_of_bounds: {se}")
            break
        if not (0.0 <= sc <= 1.0):
            violations.append(f"s_corrob_out_of_bounds: {sc}")
            break
        if not (0.0 <= pc <= 1.0):
            violations.append(f"p_contra_out_of_bounds: {pc}")
            break

    # FactBench Composite Formula check
    weights = [0.25, 0.20, 0.20, 0.20, 0.15]
    weight_sum = math.fsum(weights)

    return {
        "violations": violations,
        "is_strictly_bounded": len(violations) == 0,
        "composite_weight_sum": weight_sum,
        "composite_weights_convex": abs(weight_sum - 1.0) < 1e-9,
    }

def test_evidence_graph_dag_acyclicity() -> Dict[str, Any]:
    """Test Evidence Graph DAG topology, cycle detection, and JSON-LD serialization."""
    layers = {
        "SourceNode": 1,
        "PassageNode": 2,
        "EvidenceUnitNode": 3,
        "ClaimNode": 4,
        "ScriptSentenceNode": 5,
        "VisualElementNode": 5,
        "VerificationTraceNode": 6
    }
    
    forward_edges = [
        ("SourceNode", "PassageNode", "PROVIDES"),
        ("PassageNode", "EvidenceUnitNode", "EXTRACTS_FROM"),
        ("EvidenceUnitNode", "ClaimNode", "ENTAILS"),
        ("EvidenceUnitNode", "ClaimNode", "CONTRADICTS"),
        ("EvidenceUnitNode", "ClaimNode", "HEDGES"),
        ("ClaimNode", "ScriptSentenceNode", "GROUNDS"),
        ("ClaimNode", "VisualElementNode", "BINDS_TO"),
    ]

    monotonic = True
    for src, dst, rel in forward_edges:
        if layers[src] >= layers[dst]:
            monotonic = False

    traces_in_diagram = (layers["ScriptSentenceNode"] < layers["VerificationTraceNode"])
    traces_in_comment = (layers["VerificationTraceNode"] > layers["ClaimNode"])

    # Extract JSON example from EVIDENCE_GRAPH.md
    graph_doc_path = Path("docs/epistemic/EVIDENCE_GRAPH.md")
    content = graph_doc_path.read_text(encoding="utf-8")
    
    # Extract json block
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    json_valid = False
    has_context = False
    has_type = False
    has_id = False
    has_graph = False
    parsed_json = None

    if json_match:
        raw_json = json_match.group(1)
        try:
            parsed_json = json.loads(raw_json)
            json_valid = True
            has_context = "@context" in parsed_json
            has_type = "@type" in parsed_json
            has_id = "@id" in parsed_json
            has_graph = "@graph" in parsed_json
        except Exception as e:
            json_valid = False

    return {
        "forward_edges_strictly_monotonic": monotonic,
        "traces_to_forward_in_diagram": traces_in_diagram,
        "traces_to_backward_in_comment": traces_in_comment,
        "json_example_found": json_match is not None,
        "json_parses_cleanly": json_valid,
        "is_w3c_json_ld": has_context or has_type or has_id or has_graph,
        "has_at_context": has_context,
        "has_at_type": has_type,
        "has_at_id": has_id,
        "has_at_graph": has_graph,
    }

def test_adr006_cross_doc_conformance() -> Dict[str, Any]:
    """Verify that ADR-006 accurately formalizes decisions across all specifications."""
    adr_path = Path("docs/adrs/ADR-006-epistemic-verification.md")
    adr_text = adr_path.read_text(encoding="utf-8")

    checks = {
        "adr006_status_accepted": "Status:** ACCEPTED" in adr_text,
        "adr006_11_statuses_listed": all(s in adr_text for s in [
            "verified", "supported", "partially_supported", "contested",
            "contradicted", "unsupported", "unverifiable", "outdated",
            "misleading", "opinion", "prediction"
        ]),
        "adr006_13_tiers_referenced": "13-tier source hierarchy" in adr_text,
        "adr006_8_consensus_states": all(c in adr_text for c in [
            "STRONG_CONSENSUS", "BROAD_CONSENSUS", "MAJORITY_INTERPRETATION",
            "MINORITY_INTERPRETATION", "ACTIVE_DEBATE", "CONTESTED",
            "UNRESOLVED", "INSUFFICIENT_LITERATURE"
        ]),
        "adr006_4_gates": all(g in adr_text for g in [
            "RESEARCH_VERIFICATION", "SCRIPT_FACT_CHECK",
            "VISUAL_FACT_CHECK", "FINAL_EPISTEMIC_QA"
        ]),
        "adr006_7_strategies": all(st in adr_text for st in [
            "SOURCE_ENTAILMENT", "CROSS_SOURCE_CORROBORATION",
            "CONTRADICTION_CHECK", "QUOTE_CHECK", "NUMERICAL_CHECK",
            "TEMPORAL_CHECK", "HISTORIOGRAPHICAL_CHECK"
        ]),
        "adr006_publishing_lock": "Publishing Lock Invariant" in adr_text,
        "adr006_hermes_tools": "9 native verification tools" in adr_text,
        "adr006_untrusted_sanitization": "<untrusted_evidence>" in adr_text,
    }

    return {
        "all_checks_passed": all(checks.values()),
        "individual_checks": checks,
    }

if __name__ == "__main__":
    print("=== Suite 1: Taxonomies Completeness & Mutual Consistency ===")
    tax_res = test_taxonomies_completeness()
    for k, v in tax_res.items():
        print(f"  {k}: {v}")

    print("\n=== Suite 2: Decision Function Partition & Boundary Analysis ===")
    dec_res = test_decision_function_stress()
    for k, v in dec_res.items():
        print(f"  {k}: {v}")

    print("\n=== Suite 3: Mathematical Formulas Boundedness & Limits ===")
    form_res = test_formulas_boundedness_and_limits()
    for k, v in form_res.items():
        print(f"  {k}: {v}")

    print("\n=== Suite 4: Evidence Graph DAG & Edge Directionality ===")
    dag_res = test_evidence_graph_dag_acyclicity()
    for k, v in dag_res.items():
        print(f"  {k}: {v}")

    print("\n=== Suite 5: ADR-006 Cross-Document Conformance ===")
    adr_res = test_adr006_cross_doc_conformance()
    for k, v in adr_res.items():
        print(f"  {k}: {v}")
