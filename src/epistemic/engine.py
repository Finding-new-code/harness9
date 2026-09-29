"""src/epistemic/engine.py — Multi-Strategy Verification Engine & Policy Dispatch.

Orchestrates strategy execution, claim-type policy dispatch, graph DAG mutation,
deterministic status determination, and dossier verification gating.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from pydantic import Field

from src.epistemic.graph import (
    ClaimNode,
    EdgeRelation,
    EvidenceGraph,
    EvidenceUnitNode,
    GraphNodeType,
    PassageNode,
    SourceNode,
    VerificationTraceNode,
)
from src.epistemic.historical_policy import (
    ContradictionRecord,
    HistoricalPolicyChecker,
    HistoriographicalViolationType,
)
from src.epistemic.strategies import (
    BaseVerificationStrategy,
    ContradictionCheckStrategy,
    CrossSourceCorroborationStrategy,
    HistoriographicalCheckStrategy,
    NumericalCheckStrategy,
    QuoteCheckStrategy,
    SourceEntailmentStrategy,
    StrategyExecutionResult,
    TemporalCheckStrategy,
    VerificationStrategy,
)
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    DEFAULT_TIER_WEIGHTS,
    EpistemicStatus,
    H9BaseModel,
    QuoteExactness,
    ResearchDossier,
    SourceRecord,
    SourceTier,
)


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


class VerificationResult(H9BaseModel):
    """Composite verification verdict for a single ClaimRecord."""
    claim_id: str
    status: EpistemicStatus
    claim_type: ClaimType
    confidence: float
    entailment_score: float = 0.0
    corroboration_score: float = 0.0
    contradiction_score: float = 0.0
    highest_source_tier: SourceTier = SourceTier.PRIMARY_SOURCE
    consensus_state: Optional[ConsensusState] = None
    quote_exactness: Optional[QuoteExactness] = None
    numerical_valid: Optional[bool] = None
    temporal_valid: Optional[bool] = None
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    contradictions: List[ContradictionRecord] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    trace_id: Optional[str] = None
    explanation: str = ""


class DossierVerificationReport(H9BaseModel):
    """Aggregate verification report for an entire ResearchDossier."""
    topic: str
    run_id: str = ""
    total_claims: int = 0
    status_counts: Dict[str, int] = Field(default_factory=dict)
    gate_recommendation: str = "PASS"  # PASS | WARN | HUMAN_REVIEW | BLOCK
    results: List[VerificationResult] = Field(default_factory=list)
    unsupported_claim_ids: List[str] = Field(default_factory=list)
    contradicted_claim_ids: List[str] = Field(default_factory=list)
    contested_claim_ids: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    graph_id: str = ""
    duration_ms: float = 0.0
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary_explanation: str = ""


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

    def resolve_strategies(self, claim: ClaimRecord) -> List[str]:
        """Resolves mandatory strategies based on ClaimType and dynamically augments by claim facets."""
        base_strategies = list(STRATEGY_DISPATCH_MAP.get(claim.claim_type, ["SOURCE_ENTAILMENT"]))

        # Dynamic Quote Facet: if text has quotes and QUOTE_CHECK not present
        if any(q in claim.claim_text for q in ('"', '“', '”', '«', "'")):
            if "QUOTE_CHECK" not in base_strategies:
                base_strategies.append("QUOTE_CHECK")

        # Dynamic Numerical Facet: if text has numbers/metrics and NUMERICAL_CHECK not present
        if re.search(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", claim.claim_text):
            if "NUMERICAL_CHECK" not in base_strategies:
                base_strategies.append("NUMERICAL_CHECK")

        # Dynamic Historical Facet: historical category or era keywords
        lower = claim.claim_text.lower()
        cat = (claim.category or "").lower()
        if cat in ("history", "historical") or any(k in lower for k in ("century", "bc", "bce", "ad", "era", "treaty", "emperor", "dynasty")):
            if "HISTORIOGRAPHICAL_CHECK" not in base_strategies:
                base_strategies.append("HISTORIOGRAPHICAL_CHECK")

        return base_strategies

    def _determine_epistemic_status(
        self,
        claim: ClaimRecord,
        agg: Dict[str, Any],
    ) -> Tuple[EpistemicStatus, float, str]:
        """Applies the deterministic priority decision ladder for EpistemicStatus."""
        lower_text = claim.claim_text.lower()
        category = (claim.category or "").lower()
        notes = (claim.verification_notes or "").lower()
        flags = agg.get("flags", [])

        # 1. Unverifiable
        if category in ("unverifiable", "metaphysical") or "unfalsifiable" in notes:
            return EpistemicStatus.UNVERIFIABLE, 0.20, "Claim is non-empirical or lacks falsifiable criteria."

        # 2. Opinion
        opinion_markers = ["most beautiful", "greatest ever", "my favorite", "best", "worst", "unbelievably scenic"]
        if category == "opinion" or any(m in lower_text for m in opinion_markers):
            return EpistemicStatus.OPINION, 0.50, "Claim is a subjective aesthetic or evaluative opinion."

        # 3. Prediction
        if category == "prediction" or any(m in lower_text for m in ["will happen", "by 2030", "by 2040", "by 2050", "predicted to"]):
            return EpistemicStatus.PREDICTION, 0.40, "Claim describes a future prediction."

        # 4. Historical Policy Violation
        if HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE.value in flags:
            self.metrics["policy_violations_blocked"] += 1
            return EpistemicStatus.UNSUPPORTED, 0.0, "Sole web source forbidden for historical scholarship."

        if HistoriographicalViolationType.NUMERICAL_AVERAGING_DETECTED.value in flags:
            self.metrics["policy_violations_blocked"] += 1
            return EpistemicStatus.CONTRADICTED, 0.0, "Synthetic numerical averaging strictly prohibited."

        # 5. Quote Distortion
        if "QUOTE_FABRICATION_DETECTED" in flags or agg.get("quote_exactness") == QuoteExactness.DISTORTED:
            return EpistemicStatus.MISLEADING, 0.10, "Direct quote is distorted or fabricated; paraphrase mandated."

        # 6. Numerical Mismatch
        if "ORDER_OF_MAGNITUDE_MISMATCH" in flags:
            return EpistemicStatus.CONTRADICTED, 0.0, "Order of magnitude mismatch trap triggered."
        if "NUMERICAL_MISMATCH" in flags or "MATHEMATICAL_CALCULATION_ERROR" in flags:
            return EpistemicStatus.CONTRADICTED, 0.0, "Numerical value exceeds tolerance or compound math error."

        # 7. Temporal Obsolete
        if "OUTDATED_CLAIM" in flags or agg.get("temporal_status") == "outdated":
            return EpistemicStatus.OUTDATED, 0.30, "Time-sensitive claim is outdated or validity expired."

        # 8. Contradiction
        s_entail = agg.get("entailment_score", 0.0)
        p_contra = agg.get("contradiction_score", 0.0)
        s_corrob = agg.get("corroboration_score", 0.0)
        highest_tier = agg.get("highest_source_tier", SourceTier.PRIMARY_SOURCE)
        consensus_state = agg.get("consensus_state")

        if p_contra >= 0.80 and p_contra > s_entail:
            self.metrics["contradictions_detected"] += 1
            return EpistemicStatus.CONTRADICTED, 0.10, f"Strong contradiction detected (P_contra={p_contra:.2f})."

        # 9. Contested
        if (p_contra >= 0.60 and s_entail >= 0.60) or consensus_state in (
            ConsensusState.ACTIVE_DEBATE,
            ConsensusState.CONTESTED,
            ConsensusState.UNRESOLVED,
        ):
            return EpistemicStatus.CONTESTED, 0.65, f"Contested by evidence or literature state ({consensus_state})."

        # 10. Strengthened Assertion
        if "STRENGTHENED_ASSERTION_WARNING" in flags:
            return EpistemicStatus.PARTIALLY_SUPPORTED, 0.70, "Assertion strengthened beyond backing evidence."

        # 11. Verified
        if s_entail >= 0.90 and s_corrob >= 0.85 and p_contra < 0.20 and highest_tier.value <= 3:
            return EpistemicStatus.VERIFIED, 0.95, "Verified with high entailment, corroboration, and tier <= 3."

        # 12. Supported
        if s_entail >= 0.80 and p_contra < 0.30:
            return EpistemicStatus.SUPPORTED, 0.85, f"Supported by sources (S_entail={s_entail:.2f})."

        # 13. Partially Supported
        if 0.60 <= s_entail < 0.80 and p_contra < 0.30:
            return EpistemicStatus.PARTIALLY_SUPPORTED, 0.70, f"Partially supported (S_entail={s_entail:.2f})."

        # 14. Unsupported
        return EpistemicStatus.UNSUPPORTED, 0.30, f"Insufficient evidentiary support (S_entail={s_entail:.2f})."

    def verify_claim(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
    ) -> VerificationResult:
        """Executes verification strategies, creates VerificationTraceNode, and updates ClaimRecord/ClaimNode."""
        start_time = time.perf_counter()

        # 1. Ensure claim is registered in EvidenceGraph
        claim_node = graph.get_node(claim.claim_id)
        if claim_node is None:
            ep_status = claim.epistemic_status.value if hasattr(claim.epistemic_status, "value") else claim.epistemic_status
            con_state = claim.consensus_state.value if hasattr(claim.consensus_state, "value") else claim.consensus_state
            cl_type = claim.claim_type.value if hasattr(claim.claim_type, "value") else claim.claim_type
            graph.add_claim(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=cl_type,
                epistemic_status=ep_status,
                consensus_state=con_state,
                confidence_score=claim.confidence_score,
                category=claim.category,
                claim_record=claim,
            )
            claim_node = graph.require_node(claim.claim_id)

        # 2. Resolve strategies
        strategies_to_run = self.resolve_strategies(claim)

        # 3. Sequential Execution
        strategy_results: List[StrategyExecutionResult] = []
        all_warnings: List[str] = []
        all_flags: List[str] = []
        all_contradictions: List[ContradictionRecord] = []
        supporting_e_ids: List[str] = []
        contradicting_e_ids: List[str] = []

        entailment_score = 0.0
        corroboration_score = 0.0
        contradiction_score = 0.0
        consensus_state: Optional[ConsensusState] = None
        quote_exactness: Optional[QuoteExactness] = None
        numerical_valid: Optional[bool] = None
        temporal_valid: Optional[bool] = None

        for s_name in strategies_to_run:
            strat = self.strategies.get(s_name)
            if not strat:
                continue
            res = strat.evaluate(claim=claim, graph=graph, claim_node=claim_node)
            strategy_results.append(res)
            all_warnings.extend(res.warnings)
            all_flags.extend(res.flags)
            all_contradictions.extend(res.contradictions)
            supporting_e_ids.extend(res.supporting_evidence_ids)
            contradicting_e_ids.extend(res.contradicting_evidence_ids)

            if s_name == "SOURCE_ENTAILMENT":
                entailment_score = res.entailment_score
            elif s_name == "CROSS_SOURCE_CORROBORATION":
                corroboration_score = res.corroboration_score
            elif s_name == "CONTRADICTION_CHECK":
                contradiction_score = res.contradiction_score
            elif s_name == "QUOTE_CHECK":
                quote_exactness = res.quote_exactness
            elif s_name == "NUMERICAL_CHECK":
                numerical_valid = res.passed
            elif s_name == "TEMPORAL_CHECK":
                temporal_valid = res.passed
            elif s_name == "HISTORIOGRAPHICAL_CHECK":
                if res.consensus_state:
                    consensus_state = res.consensus_state

        # Find highest source tier
        highest_tier = SourceTier.UNVERIFIED
        sources = [claim.primary_source] + claim.corroborating_sources
        for s in sources:
            if s:
                t = s.tier if isinstance(s.tier, SourceTier) else SourceTier(int(s.tier))
                if t.value < highest_tier.value:
                    highest_tier = t

        agg = {
            "entailment_score": entailment_score,
            "corroboration_score": corroboration_score,
            "contradiction_score": contradiction_score,
            "highest_source_tier": highest_tier,
            "consensus_state": consensus_state,
            "quote_exactness": quote_exactness,
            "numerical_valid": numerical_valid,
            "temporal_valid": temporal_valid,
            "flags": all_flags,
            "warnings": all_warnings,
        }

        # 4. Status decision ladder
        final_status, confidence, explanation = self._determine_epistemic_status(claim, agg)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # 5. Insert VerificationTraceNode into DAG
        trace_id = graph.add_verification_trace(
            target_node_id=claim.claim_id,
            strategy_used=",".join(strategies_to_run),
            entailment_score=entailment_score,
            contradiction_score=contradiction_score,
            corroboration_score=corroboration_score,
            status_assigned=final_status.value,
            consensus_state_assigned=consensus_state.value if consensus_state else None,
            verifier_name=self.verifier_name,
            audit_notes=explanation,
            execution_duration_ms=duration_ms,
            warnings=all_warnings,
        )

        # 6. Link supporting and contradicting evidence
        for eu_id in supporting_e_ids:
            if graph.get_node(eu_id) and not graph.get_edge(eu_id, claim.claim_id):
                if not graph.would_create_cycle(eu_id, claim.claim_id):
                    graph.link(eu_id, claim.claim_id, EdgeRelation.ENTAILMENT, weight=entailment_score)

        for counter_id in contradicting_e_ids:
            if graph.get_node(counter_id) and not graph.get_edge(counter_id, claim.claim_id):
                if not graph.would_create_cycle(counter_id, claim.claim_id):
                    graph.link(counter_id, claim.claim_id, EdgeRelation.CONTRADICTION, weight=contradiction_score)

        # 7. Synchronize ClaimRecord & ClaimNode
        claim.epistemic_status = final_status
        if consensus_state:
            claim.consensus_state = consensus_state
        claim.confidence_score = confidence
        claim.source_tier = highest_tier
        if quote_exactness:
            claim.quote_exactness = quote_exactness
        claim.verifier_metadata = {
            "trace_id": trace_id,
            "verifier_name": self.verifier_name,
            "duration_ms": duration_ms,
            "strategies_run": strategies_to_run,
            "warnings": all_warnings,
            "flags": all_flags,
            "entailment_score": entailment_score,
            "corroboration_score": corroboration_score,
            "contradiction_score": contradiction_score,
        }

        claim_node.epistemic_status = final_status.value
        if consensus_state:
            claim_node.consensus_state = consensus_state.value
        claim_node.confidence_score = confidence
        claim_node.verifier_metadata = claim.verifier_metadata

        self.metrics["claims_verified"] += 1
        self.metrics["traces_created"] += 1

        return VerificationResult(
            claim_id=claim.claim_id,
            status=final_status,
            claim_type=claim.claim_type,
            confidence=confidence,
            entailment_score=entailment_score,
            corroboration_score=corroboration_score,
            contradiction_score=contradiction_score,
            highest_source_tier=highest_tier,
            consensus_state=consensus_state,
            quote_exactness=quote_exactness,
            numerical_valid=numerical_valid,
            temporal_valid=temporal_valid,
            supporting_evidence_ids=supporting_e_ids,
            contradicting_evidence_ids=contradicting_e_ids,
            contradictions=all_contradictions,
            warnings=all_warnings,
            flags=all_flags,
            trace_id=trace_id,
            explanation=explanation,
        )

    def verify_dossier(
        self,
        dossier: ResearchDossier,
        graph: Optional[EvidenceGraph] = None,
    ) -> DossierVerificationReport:
        """Verifies all claims in a ResearchDossier, performs cross-claim checks, evaluates gate outcomes, and embeds serialized graph."""
        start_time = time.perf_counter()

        # 1. Resolve or construct hermetic EvidenceGraph
        if graph is None:
            graph = EvidenceGraph.from_dossier(dossier)

        # 2. Verify all claims
        results: List[VerificationResult] = []
        status_counts: Dict[str, int] = {}
        unsupported_ids: List[str] = []
        contradicted_ids: List[str] = []
        contested_ids: List[str] = []
        all_warnings: List[str] = []

        for claim in dossier.claims:
            res = self.verify_claim(claim, graph)
            results.append(res)
            st_val = res.status.value
            status_counts[st_val] = status_counts.get(st_val, 0) + 1
            all_warnings.extend(res.warnings)

            if res.status == EpistemicStatus.UNSUPPORTED:
                unsupported_ids.append(claim.claim_id)
            elif res.status in (EpistemicStatus.CONTRADICTED, EpistemicStatus.MISLEADING):
                contradicted_ids.append(claim.claim_id)
            elif res.status == EpistemicStatus.CONTESTED:
                contested_ids.append(claim.claim_id)

        # 3. Cross-Claim Contradiction Check
        # Check pairs of claims for conflicting facts (e.g. conflicting dates or metrics)
        for i in range(len(dossier.claims)):
            for j in range(i + 1, len(dossier.claims)):
                c1 = dossier.claims[i]
                c2 = dossier.claims[j]
                # If both reference the same subject but assert different years or numbers
                if c1.category == c2.category and c1.category not in ("general", ""):
                    # Check for explicit contradiction in text
                    t1, t2 = c1.claim_text.lower(), c2.claim_text.lower()
                    if ("invented in" in t1 and "invented in" in t2) or ("founded in" in t1 and "founded in" in t2):
                        years1 = set(re.findall(r"\b(1\d{3}|20\d{2})\b", t1))
                        years2 = set(re.findall(r"\b(1\d{3}|20\d{2})\b", t2))
                        if years1 and years2 and years1 != years2:
                            c1.epistemic_status = EpistemicStatus.CONTESTED
                            c2.epistemic_status = EpistemicStatus.CONTESTED
                            c1.consensus_state = ConsensusState.CONTESTED
                            c2.consensus_state = ConsensusState.CONTESTED
                            if c1.claim_id not in contested_ids:
                                contested_ids.append(c1.claim_id)
                            if c2.claim_id not in contested_ids:
                                contested_ids.append(c2.claim_id)
                            if not graph.get_edge(c1.claim_id, c2.claim_id) and not graph.would_create_cycle(c1.claim_id, c2.claim_id):
                                graph.link(c1.claim_id, c2.claim_id, EdgeRelation.CONTRADICTION)

        # 4. Gate Outcome Evaluation: BLOCK | HUMAN_REVIEW | WARN | PASS
        if contradicted_ids or unsupported_ids:
            gate_rec = "BLOCK"
            summary = (
                f"Gate outcome BLOCK: {len(contradicted_ids)} contradicted/misleading and "
                f"{len(unsupported_ids)} unsupported claim(s) detected."
            )
        elif contested_ids or status_counts.get(EpistemicStatus.UNVERIFIABLE.value, 0) > 0:
            gate_rec = "HUMAN_REVIEW"
            summary = (
                f"Gate outcome HUMAN_REVIEW: {len(contested_ids)} contested or unverifiable claim(s) require review."
            )
        elif (
            status_counts.get(EpistemicStatus.PARTIALLY_SUPPORTED.value, 0) > 0
            or status_counts.get(EpistemicStatus.OUTDATED.value, 0) > 0
        ):
            gate_rec = "WARN"
            summary = "Gate outcome WARN: Some claims are partially supported or outdated; hedging required."
        else:
            gate_rec = "PASS"
            summary = f"Gate outcome PASS: All {len(dossier.claims)} claim(s) successfully verified or supported."

        # 5. Embed serialized graph into dossier
        dossier.evidence_graph = graph.to_dict()

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return DossierVerificationReport(
            topic=dossier.topic,
            run_id=dossier.run_id,
            total_claims=len(dossier.claims),
            status_counts=status_counts,
            gate_recommendation=gate_rec,
            results=results,
            unsupported_claim_ids=unsupported_ids,
            contradicted_claim_ids=contradicted_ids,
            contested_claim_ids=contested_ids,
            warnings=all_warnings,
            graph_id=graph.graph_id,
            duration_ms=duration_ms,
            summary_explanation=summary,
        )
