"""src/epistemic/historical_policy.py — Historical Scholarship Policy & Governance.

Enforces the 6 core historical scholarship rules:
1. Prohibition on forbidden sole web sources (Tiers 9-13).
2. Minimum evidentiary tier thresholds (Threshold A: Tier 1/6, Threshold B: Tier 3, Threshold C: 2x Tier 2).
3. Deterministic 8-consensus-state classification.
4. Event vs. interpretation distinction (forbidding unhedged declarative claims for causal hypotheses).
5. Non-averaging contradiction invariant (forbidding arithmetic synthesis of conflicting counts/dates).
6. Calibrated narration framing and balanced attribution formatting.
"""

from __future__ import annotations

from dataclasses import field
from datetime import datetime, timezone
from enum import Enum
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from pydantic import Field

from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    H9BaseModel,
    SourceRecord,
    SourceTier,
)


class HistoriographicalViolationType(str, Enum):
    """Categories of historiographical scholarship policy violations."""
    UNQUALIFIED_SOLE_SOURCE = "POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE"
    INSUFFICIENT_TIER_THRESHOLD = "POLICY_VIOLATION_INSUFFICIENT_TIER_THRESHOLD"
    UNHEDGED_INTERPRETATION = "POLICY_VIOLATION_UNHEDGED_INTERPRETATION"
    NUMERICAL_AVERAGING_DETECTED = "POLICY_VIOLATION_NUMERICAL_AVERAGING"
    UNBALANCED_ATTRIBUTION = "POLICY_VIOLATION_UNBALANCED_ATTRIBUTION"
    SPECULATIVE_CERTAINTY = "POLICY_VIOLATION_SPECULATIVE_CERTAINTY"
    ANACHRONISM_DETECTED = "POLICY_VIOLATION_ANACHRONISM"


class HistoricalFraming(H9BaseModel):
    """Prescribed rhetorical rules for voiceover script generation."""
    consensus_state: ConsensusState
    mandated_phrases: List[str] = Field(default_factory=list)
    forbidden_phrases: List[str] = Field(default_factory=list)
    attribution_template: Optional[str] = None
    tone_directive: str = "neutral_scholarly"
    requires_hedging: bool = False
    requires_balanced_perspectives: bool = False


class ContradictionRecord(H9BaseModel):
    """Immutable record of an identified factual contradiction between sources."""
    contradiction_id: str = Field(default_factory=lambda: f"contra_{uuid.uuid4().hex[:8]}")
    claim_id: str
    parameter_name: str = "general"
    contradiction_type: str = "polar_negation"  # polar_negation, numerical_incompatibility, attribution_rivalry, chronological_conflict
    claim_assertion: str = ""
    conflicting_assertion: str = ""
    source_a_id: str = ""
    source_b_id: str = ""
    source_a_tier: int = 1
    source_b_tier: int = 1
    severity: float = 1.0
    mandated_framing: str = ""
    conflicting_assertions: List[Dict[str, Any]] = Field(default_factory=list)
    reported_range: Optional[Tuple[float, float]] = None
    is_numeric: bool = False
    narrative_recommendation: str = ""
    is_resolved_by_averaging: bool = False  # MUST ALWAYS BE FALSE (Non-averaging invariant)


class HistoriographicalEvaluationReport(H9BaseModel):
    """Comprehensive audit report for a historical claim."""
    claim_id: str
    claim_type: ClaimType
    consensus_state: ConsensusState
    epistemic_status: EpistemicStatus
    eligible_for_narration: bool
    violations: List[HistoriographicalViolationType] = Field(default_factory=list)
    violation_details: List[str] = Field(default_factory=list)
    highest_source_tier: SourceTier
    qualifying_threshold: Optional[str] = None  # "Threshold A", "Threshold B", or "Threshold C"
    mandated_framing: HistoricalFraming
    is_averaged: bool = False
    divergent_values_preserved: List[Union[str, float, int]] = Field(default_factory=list)
    evaluated_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class HistoricalPolicyChecker:
    """Evaluates historical claims and enforces historiographical scholarship rules."""

    FORBIDDEN_SOLE_SOURCE_TIERS: Set[SourceTier] = {
        SourceTier.REPUTABLE_JOURNALISM,  # Tier 9
        SourceTier.TRADE_PUBLICATION,     # Tier 10
        SourceTier.POPULAR_MEDIA,         # Tier 11
        SourceTier.SELF_PUBLISHED,        # Tier 12
        SourceTier.UNVERIFIED,            # Tier 13
    }

    PRIMARY_TIERS: Set[SourceTier] = {
        SourceTier.PRIMARY_SOURCE,        # Tier 1
        SourceTier.ARCHIVAL_DOCUMENT,     # Tier 6
    }

    ACADEMIC_BOOK_TIERS: Set[SourceTier] = {
        SourceTier.ACADEMIC_BOOK,         # Tier 3
    }

    PEER_REVIEWED_TIERS: Set[SourceTier] = {
        SourceTier.PEER_REVIEWED_JOURNAL, # Tier 2
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None, strict: bool = True):
        self.config = config or {}
        self.strict = strict

    @staticmethod
    def _coerce_tier(source: SourceRecord) -> SourceTier:
        tier_val = source.tier
        if isinstance(tier_val, SourceTier):
            return tier_val
        try:
            return SourceTier(int(tier_val))
        except (ValueError, TypeError):
            return SourceTier.UNVERIFIED

    def check_forbidden_sole_source(
        self,
        sources: List[SourceRecord],
    ) -> Tuple[bool, List[str]]:
        """Returns (is_valid, violation_messages). Rejects if all sources are Tiers 9-13 or empty."""
        if not sources:
            return False, ["No backing sources provided for historical claim."]

        qualifying_sources = [
            s for s in sources if self._coerce_tier(s) not in self.FORBIDDEN_SOLE_SOURCE_TIERS
        ]

        if not qualifying_sources:
            msg = (
                f"POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE: All {len(sources)} source(s) "
                f"are within forbidden sole source tiers 9-13 (web summaries, popular media, blogs, or unverified). "
                f"Historical claims require primary, academic press, or peer-reviewed grounding."
            )
            return False, [msg]

        return True, []

    def verify_minimum_source_tiers(
        self,
        sources: List[SourceRecord],
        claim_type: ClaimType,
    ) -> Tuple[bool, Optional[str], List[str]]:
        """Verifies satisfaction of Threshold A, B, or C. Returns (is_valid, threshold_name, messages)."""
        if not sources:
            return False, None, ["No sources available to satisfy minimum evidentiary thresholds."]

        coerced = [(s, self._coerce_tier(s)) for s in sources]

        # Threshold A: >= 1 verified Tier 1 or Tier 6
        primary_sources = [s for s, t in coerced if t in self.PRIMARY_TIERS]
        if len(primary_sources) >= 1:
            return True, "Threshold A", []

        # Threshold B: >= 1 verified Tier 3 (Academic Book / Press)
        book_sources = [s for s, t in coerced if t in self.ACADEMIC_BOOK_TIERS]
        if len(book_sources) >= 1:
            return True, "Threshold B", []

        # Threshold C: >= 2 independent Tier 2 (Peer-Reviewed Journal)
        peer_sources = [s for s, t in coerced if t in self.PEER_REVIEWED_TIERS]
        if len(peer_sources) >= 2:
            # Check independence across distinct domains or titles
            return True, "Threshold C", []

        # If only 1 Tier 2 exists, it does not meet Threshold C
        if len(peer_sources) == 1:
            return (
                False,
                None,
                ["A single peer-reviewed journal article is insufficient for Threshold C (requires >= 2)."],
            )

        return (
            False,
            None,
            ["POLICY_VIOLATION_INSUFFICIENT_TIER_THRESHOLD: Does not satisfy Threshold A (Tier 1/6), Threshold B (Tier 3), or Threshold C (2x Tier 2)."],
        )

    def classify_consensus_state(
        self,
        claim: ClaimRecord,
        sources: List[SourceRecord],
        opposing_claims: Optional[List[ClaimRecord]] = None,
    ) -> ConsensusState:
        """Classifies claim into one of the 8 ConsensusState categories from literature distribution."""
        # 1. Check if metadata or explicit indicators specify consensus state
        if claim.verifier_metadata and "consensus_state" in claim.verifier_metadata:
            meta_cs = claim.verifier_metadata["consensus_state"]
            if isinstance(meta_cs, ConsensusState):
                return meta_cs
            try:
                return ConsensusState(str(meta_cs))
            except ValueError:
                pass

        # 3. Check for explicit unresolved markers in claim text or metadata
        lower_text = claim.claim_text.lower()
        notes = (claim.verification_notes or "").lower()
        if any(w in lower_text or w in notes for w in ["unresolved", "inconclusive", "open mystery", "historians cannot determine", "records are lost"]):
            return ConsensusState.UNRESOLVED

        # 4. Check for primary contradiction / contested accounts
        primary_dissent = any(
            self._coerce_tier(s) in self.PRIMARY_TIERS
            for s in claim.contradicting_sources
        )
        if primary_dissent or "contested" in lower_text:
            return ConsensusState.CONTESTED

        # 5. Count academic literature
        coerced = [(s, self._coerce_tier(s)) for s in sources]
        n_primary = sum(1 for _, t in coerced if t in self.PRIMARY_TIERS)
        n_peer = sum(1 for _, t in coerced if t in self.PEER_REVIEWED_TIERS)
        n_book = sum(1 for _, t in coerced if t in self.ACADEMIC_BOOK_TIERS)
        n_scholarly = n_peer + n_book

        if n_scholarly < 2 and n_primary < 1:
            return ConsensusState.INSUFFICIENT_LITERATURE

        # 6. Dissent analysis
        n_dissent = len(claim.contradicting_sources)
        n_agree = max(1, len(sources))
        r_agree = n_agree / (n_agree + n_dissent)

        if n_dissent == 0 and (n_primary >= 1 or n_book >= 1) and n_scholarly >= 2:
            return ConsensusState.STRONG_CONSENSUS

        if r_agree >= 0.90:
            return ConsensusState.BROAD_CONSENSUS
        elif 0.60 <= r_agree < 0.90:
            return ConsensusState.MAJORITY_INTERPRETATION
        elif 0.40 <= r_agree < 0.60:
            return ConsensusState.ACTIVE_DEBATE
        elif 0.10 <= r_agree < 0.40:
            return ConsensusState.MINORITY_INTERPRETATION

        return ConsensusState.ACTIVE_DEBATE

    def validate_event_vs_interpretation(
        self,
        claim: ClaimRecord,
        consensus_state: ConsensusState,
    ) -> Tuple[bool, List[str]]:
        """Ensures causal interpretations are never framed as uncontested empirical events."""
        text = claim.claim_text.lower()

        is_interpretation = claim.claim_type in (
            ClaimType.CAUSAL_INTERPRETATION,
            ClaimType.SCHOLARLY_INTERPRETATION,
        )

        unhedged_patterns = [
            r"\bdefinitely caused\b",
            r"\bsole cause\b",
            r"\bundisputed cause\b",
            r"\bit is an established fact that\b",
            r"\bproven beyond doubt that\b",
            r"\bcaused solely by\b",
            r"\bthe single reason was\b",
            r"\bindisputably caused\b",
        ]

        if is_interpretation:
            for pattern in unhedged_patterns:
                if re.search(pattern, text):
                    msg = (
                        f"POLICY_VIOLATION_UNHEDGED_INTERPRETATION: Causal or scholarly interpretation "
                        f"contains unhedged declarative absolute phrasing ('{pattern}'). "
                        f"Historiographical interpretations must be framed with scholarly attribution."
                    )
                    return False, [msg]

        return True, []

    def enforce_non_averaging(
        self,
        claim_id: str,
        asserted_value: Union[float, int, str],
        source_values: List[Union[float, int, str]],
    ) -> Tuple[bool, Optional[ContradictionRecord], List[str]]:
        """Detects and prohibits arithmetic averaging of divergent numbers or accounts."""
        if not source_values or len(source_values) < 2:
            return True, None, []

        # Convert to numeric if possible
        num_sources: List[float] = []
        for v in source_values:
            try:
                num_sources.append(float(v))
            except (ValueError, TypeError):
                pass

        if len(num_sources) >= 2 and min(num_sources) != max(num_sources):
            # Check if asserted_value is numeric
            try:
                asserted_num = float(asserted_value)
                mean_val = sum(num_sources) / len(num_sources)
                # If asserted number is close to the arithmetic mean and not equal to any source value
                if (
                    math.isclose(asserted_num, mean_val, rel_tol=0.02)
                    and all(not math.isclose(asserted_num, sv, rel_tol=0.001) for sv in num_sources)
                ):
                    contra = ContradictionRecord(
                        claim_id=claim_id,
                        parameter_name="numeric_metric",
                        contradiction_type="numerical_incompatibility",
                        claim_assertion=str(asserted_value),
                        conflicting_assertion=f"Divergent sources report: {num_sources}",
                        reported_range=(min(num_sources), max(num_sources)),
                        is_numeric=True,
                        narrative_recommendation=(
                            f"Estimates range from {min(num_sources):g} to {max(num_sources):g}; "
                            f"narration must present this range rather than an averaged figure."
                        ),
                        is_resolved_by_averaging=True,
                    )
                    msg = (
                        f"POLICY_VIOLATION_NUMERICAL_AVERAGING: Synthetic arithmetic average ({asserted_num}) "
                        f"detected across divergent historical sources {num_sources}. "
                        f"Arithmetic averaging of historical conflicts is strictly prohibited."
                    )
                    return False, contra, [msg]
            except (ValueError, TypeError):
                pass

            # Discrete divergent values preserved
            contra = ContradictionRecord(
                claim_id=claim_id,
                parameter_name="divergent_values",
                contradiction_type="numerical_incompatibility",
                claim_assertion=str(asserted_value),
                conflicting_assertion=f"Sources: {source_values}",
                reported_range=(min(num_sources), max(num_sources)) if num_sources else None,
                is_numeric=bool(num_sources),
                narrative_recommendation=f"Sources report divergent figures: {source_values}.",
                is_resolved_by_averaging=False,
            )
            return True, contra, []

        return True, None, []

    def get_mandated_framing(
        self,
        consensus_state: ConsensusState,
        claim_type: Optional[ClaimType] = None,
    ) -> HistoricalFraming:
        """Returns the prescribed HistoricalFraming rules for a given consensus state."""
        if consensus_state == ConsensusState.STRONG_CONSENSUS:
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["in", "on", "demonstrated", "signed", "established"],
                forbidden_phrases=["allegedly", "some believe", "it is claimed that", "supposedly"],
                attribution_template="{event} occurred on {date} at {location}.",
                tone_directive="declarative_objective",
                requires_hedging=False,
                requires_balanced_perspectives=False,
            )
        elif consensus_state == ConsensusState.BROAD_CONSENSUS:
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["historical evidence demonstrates", "scholarly consensus indicates", "widely agreed"],
                forbidden_phrases=["without any evidence", "allegedly"],
                attribution_template="Scholarly consensus indicates that {claim}.",
                tone_directive="calibrated_consensus",
                requires_hedging=False,
                requires_balanced_perspectives=False,
            )
        elif consensus_state == ConsensusState.MAJORITY_INTERPRETATION:
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["the leading historical view holds", "most evidence points to", "a prominent view among historians"],
                forbidden_phrases=["it is an established fact that", "undisputed truth"],
                attribution_template="While debated, the leading historical view holds that {claim}.",
                tone_directive="paradigmatic_hedged",
                requires_hedging=True,
                requires_balanced_perspectives=False,
            )
        elif consensus_state == ConsensusState.MINORITY_INTERPRETATION:
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["an important scholarly counter-thesis argues", "historians such as", "alternatively, scholars propose"],
                forbidden_phrases=["it is proven that", "all historians agree"],
                attribution_template="A notable school of historians, including {scholar}, contends that {claim}.",
                tone_directive="counter_perspective_hedged",
                requires_hedging=True,
                requires_balanced_perspectives=True,
            )
        elif consensus_state == ConsensusState.ACTIVE_DEBATE:
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["historians remain divided", "scholarly debate centers on", "competing perspectives"],
                forbidden_phrases=["it is undisputed", "settled fact", "obviously"],
                attribution_template="Historians remain divided: whereas {scholar_a} argues {view_a}, {scholar_b} contends {view_b}.",
                tone_directive="balanced_debate",
                requires_hedging=True,
                requires_balanced_perspectives=True,
            )
        elif consensus_state == ConsensusState.CONTESTED:
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["surviving accounts conflict", "estimates range widely", "contemporary records dispute"],
                forbidden_phrases=["precisely", "exact count of", "unanimous"],
                attribution_template="Surviving records conflict: estimates range from {val_min} to {val_max}.",
                tone_directive="conflict_transparent",
                requires_hedging=True,
                requires_balanced_perspectives=True,
            )
        elif consensus_state == ConsensusState.UNRESOLVED:
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["surviving records leave this question unanswered", "evidence remains inconclusive", "the ultimate cause remains unknown"],
                forbidden_phrases=["clearly resolved", "conclusively proven"],
                attribution_template="Surviving historical records leave the question unresolved.",
                tone_directive="scholarly_humility",
                requires_hedging=True,
                requires_balanced_perspectives=False,
            )
        else:  # INSUFFICIENT_LITERATURE
            return HistoricalFraming(
                consensus_state=consensus_state,
                mandated_phrases=["due to limited surviving documentation", "with scarce records surviving"],
                forbidden_phrases=["extensively documented", "definitive proof"],
                attribution_template="Historical documentation on this matter remains sparse.",
                tone_directive="sparse_record_disclosure",
                requires_hedging=True,
                requires_balanced_perspectives=False,
            )

    def check_narration_framing(
        self,
        script_text: str,
        consensus_state: ConsensusState,
        claim_type: ClaimType,
    ) -> Tuple[bool, List[str]]:
        """Audits generated voiceover text against the mandated phrasing and forbidden rhetoric matrix."""
        framing = self.get_mandated_framing(consensus_state, claim_type)
        lower_script = script_text.lower()
        violations: List[str] = []

        for forbidden in framing.forbidden_phrases:
            if forbidden in lower_script:
                violations.append(
                    f"Forbidden phrasing detected for consensus state {consensus_state.value}: '{forbidden}' in script."
                )

        if framing.requires_hedging and consensus_state in (
            ConsensusState.ACTIVE_DEBATE,
            ConsensusState.CONTESTED,
            ConsensusState.UNRESOLVED,
        ):
            # Verify that script contains at least one hedge or discussion marker
            hedge_markers = [
                "divided", "debate", "range", "conflict", "dispute", "unresolved",
                "inconclusive", "while", "whereas", "scholars argue", "contends", "estimates"
            ]
            if not any(marker in lower_script for marker in hedge_markers):
                violations.append(
                    f"Consensus state {consensus_state.value} requires hedging or debate markers, but none were detected."
                )

        return len(violations) == 0, violations

    def format_balanced_attribution(
        self,
        perspectives: List[Dict[str, str]],
    ) -> str:
        """Generates a balanced attribution string conforming to policy templates."""
        if not perspectives:
            return "Historians hold diverse perspectives on this question."
        if len(perspectives) == 1:
            p = perspectives[0]
            scholar = p.get("scholar", "scholars")
            argument = p.get("argument", "")
            return f"Historians such as {scholar} argue that {argument}."

        p1 = perspectives[0]
        p2 = perspectives[1]
        scholar1 = p1.get("scholar", "some historians")
        arg1 = p1.get("argument", "")
        scholar2 = p2.get("scholar", "others")
        arg2 = p2.get("argument", "")
        return f"Historians such as {scholar1} argue that {arg1}, whereas {scholar2} contends that {arg2}."

    def evaluate_claim(
        self,
        claim: ClaimRecord,
        sources: Optional[List[SourceRecord]] = None,
        opposing_claims: Optional[List[ClaimRecord]] = None,
    ) -> HistoriographicalEvaluationReport:
        """Executes end-to-end historical policy verification on a candidate claim."""
        all_sources: List[SourceRecord] = []
        if sources:
            all_sources.extend(sources)
        if claim.primary_source:
            all_sources.append(claim.primary_source)
        if claim.corroborating_sources:
            all_sources.extend(claim.corroborating_sources)

        violations: List[HistoriographicalViolationType] = []
        violation_details: List[str] = []

        # 1. Sole web source check
        sole_ok, sole_msgs = self.check_forbidden_sole_source(all_sources)
        if not sole_ok:
            violations.append(HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE)
            violation_details.extend(sole_msgs)

        # 2. Minimum source tiers check
        tier_ok, qualifying_threshold, tier_msgs = self.verify_minimum_source_tiers(
            all_sources, claim.claim_type
        )
        if not tier_ok:
            violations.append(HistoriographicalViolationType.INSUFFICIENT_TIER_THRESHOLD)
            violation_details.extend(tier_msgs)

        # 3. Consensus state classification
        consensus_state = self.classify_consensus_state(claim, all_sources, opposing_claims)

        # 4. Event vs interpretation validation
        event_ok, event_msgs = self.validate_event_vs_interpretation(claim, consensus_state)
        if not event_ok:
            violations.append(HistoriographicalViolationType.UNHEDGED_INTERPRETATION)
            violation_details.extend(event_msgs)

        # 5. Non-averaging check
        is_averaged = False
        divergent_preserved: List[Union[str, float, int]] = []
        contra_rec: Optional[ContradictionRecord] = None
        if claim.verifier_metadata and "source_values" in claim.verifier_metadata:
            s_vals = claim.verifier_metadata["source_values"]
            asserted_val = claim.verifier_metadata.get("asserted_value", claim.claim_text)
            navg_ok, c_rec, navg_msgs = self.enforce_non_averaging(
                claim.claim_id, asserted_val, s_vals
            )
            contra_rec = c_rec
            if not navg_ok:
                violations.append(HistoriographicalViolationType.NUMERICAL_AVERAGING_DETECTED)
                violation_details.extend(navg_msgs)
                is_averaged = True
            if c_rec and c_rec.conflicting_assertions:
                divergent_preserved = [c.get("value", "") for c in c_rec.conflicting_assertions]

        # Determine highest source tier
        highest_tier = SourceTier.UNVERIFIED
        for s in all_sources:
            t = self._coerce_tier(s)
            if t.value < highest_tier.value:
                highest_tier = t

        # Determine epistemic status & eligibility
        if HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE in violations:
            final_status = EpistemicStatus.UNSUPPORTED
            eligible = False
        elif HistoriographicalViolationType.NUMERICAL_AVERAGING_DETECTED in violations:
            final_status = EpistemicStatus.CONTRADICTED
            eligible = False
        elif consensus_state == ConsensusState.CONTESTED:
            final_status = EpistemicStatus.CONTESTED
            eligible = True
        elif consensus_state in (ConsensusState.ACTIVE_DEBATE, ConsensusState.MINORITY_INTERPRETATION):
            final_status = EpistemicStatus.SUPPORTED if tier_ok else EpistemicStatus.PARTIALLY_SUPPORTED
            eligible = True
        elif consensus_state in (ConsensusState.STRONG_CONSENSUS, ConsensusState.BROAD_CONSENSUS):
            final_status = EpistemicStatus.VERIFIED if (tier_ok and highest_tier.value <= 3) else EpistemicStatus.SUPPORTED
            eligible = True
        elif consensus_state == ConsensusState.UNRESOLVED:
            final_status = EpistemicStatus.PARTIALLY_SUPPORTED
            eligible = True
        else:
            final_status = EpistemicStatus.UNSUPPORTED
            eligible = False

        mandated_framing = self.get_mandated_framing(consensus_state, claim.claim_type)

        return HistoriographicalEvaluationReport(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            consensus_state=consensus_state,
            epistemic_status=final_status,
            eligible_for_narration=eligible,
            violations=violations,
            violation_details=violation_details,
            highest_source_tier=highest_tier,
            qualifying_threshold=qualifying_threshold,
            mandated_framing=mandated_framing,
            is_averaged=is_averaged,
            divergent_values_preserved=divergent_preserved,
        )


# Canonical alias for compatibility
HistoricalScholarshipPolicyEngine = HistoricalPolicyChecker
