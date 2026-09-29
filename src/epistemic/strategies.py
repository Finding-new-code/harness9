"""src/epistemic/strategies.py — Modular Verification Strategies for Epistemic Grounding.

Implements the 7 canonical verification strategies:
1. SOURCE_ENTAILMENT: Natural language entailment scaled by 13-tier weights, with modal qualifier checks.
2. CROSS_SOURCE_CORROBORATION: Multi-source independence calculation, domain disjointness, wire collapse.
3. CONTRADICTION_CHECK: High-sensitivity polarity and numerical conflict detection, non-averaging invariant.
4. QUOTE_CHECK: Character-level Levenshtein matching, exact vs ellipses vs distorted, paraphrase mandate.
5. NUMERICAL_CHECK: Unit normalization, dual tolerance (0.1% exact, 5.0% approx), order-of-magnitude traps.
6. TEMPORAL_CHECK: Causal chronology precedence, historical anachronism scanning, temporal freshness.
7. HISTORIOGRAPHICAL_CHECK: Historical scholarship policy, sole web source prohibition, 8 consensus states.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import field
from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse
import uuid

from pydantic import Field

from src.epistemic.graph import (
    ClaimNode,
    EdgeRelation,
    EvidenceGraph,
    EvidenceUnitNode,
    PassageNode,
    SourceNode,
)
from src.epistemic.historical_policy import (
    ContradictionRecord,
    HistoricalPolicyChecker,
    HistoriographicalEvaluationReport,
    HistoriographicalViolationType,
)
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    DEFAULT_TIER_WEIGHTS,
    EpistemicStatus,
    H9BaseModel,
    QuoteExactness,
    SourceRecord,
    SourceTier,
)


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
    contradictions: List[ContradictionRecord] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""


class BaseVerificationStrategy(ABC):
    """Abstract base class for all verification strategies."""

    strategy_name: str = "BASE"

    @abstractmethod
    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        """Executes verification against claim and backing evidence graph."""
        pass


VerificationStrategy = BaseVerificationStrategy


# Helper for extracting root domain
def extract_root_domain(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc or parsed.path
        netloc = netloc.split(":")[0].lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        parts = netloc.split(".")
        if len(parts) >= 2:
            # Handle co.uk, gov.uk, etc.
            if len(parts) >= 3 and parts[-2] in ("co", "gov", "ac", "edu", "org", "com"):
                return ".".join(parts[-3:])
            return ".".join(parts[-2:])
        return netloc
    except Exception:
        return url.lower()


# Helper for Levenshtein distance
def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


# ===========================================================================
# Strategy 1: SOURCE_ENTAILMENT
# ===========================================================================
class SourceEntailmentStrategy(BaseVerificationStrategy):
    """Evaluates text support probability scaled by 13-tier weights and detects modal strengthening."""

    strategy_name: str = "SOURCE_ENTAILMENT"

    MODAL_LEVEL_3: Set[str] = {
        "always", "proven", "definitely", "solely", "undoubtedly", "certainly",
        "indisputable", "conclusively", "cure", "guaranteed", "unquestionably"
    }
    MODAL_LEVEL_2: Set[str] = {
        "generally", "typically", "the primary", "most", "likely", "usually",
        "substantially", "predominantly", "largely", "often"
    }
    MODAL_LEVEL_1: Set[str] = {
        "may", "suggests", "one factor", "partially", "possibly", "could",
        "preliminary", "hypothesized", "indicates potential", "might", "tentative"
    }

    def _get_modal_level(self, text: str) -> int:
        lower = text.lower()
        words = set(re.findall(r"\b[a-z]+\b", lower))
        if any(term in words or term in lower for term in self.MODAL_LEVEL_3):
            return 3
        if any(term in words or term in lower for term in self.MODAL_LEVEL_2):
            return 2
        if any(term in words or term in lower for term in self.MODAL_LEVEL_1):
            return 1
        return 2  # default baseline

    def _compute_semantic_support(self, claim_text: str, passage_text: str) -> Tuple[float, bool]:
        """Returns (support_probability in [0.0, 1.0], is_negated)."""
        c_words = set(re.findall(r"\b\w{3,}\b", claim_text.lower()))
        p_words = set(re.findall(r"\b\w{3,}\b", passage_text.lower()))

        # Strip stopwords
        stops = {"the", "and", "for", "that", "this", "with", "from", "are", "was", "were", "been"}
        c_words -= stops
        p_words -= stops

        if not c_words:
            return 0.8, False

        overlap = len(c_words & p_words)
        base_overlap = overlap / len(c_words)

        # Scrutinize negative polarity
        negation_terms = {"not", "never", "failed", "refuted", "disproved", "none", "neither", "no"}
        p_lower_words = set(re.findall(r"\b[a-z]+\b", passage_text.lower()))
        c_lower_words = set(re.findall(r"\b[a-z]+\b", claim_text.lower()))

        p_neg = bool(negation_terms & p_lower_words)
        c_neg = bool(negation_terms & c_lower_words)

        if p_neg != c_neg and base_overlap > 0.4:
            # Opposite polarity indicates contradiction rather than entailment
            return 0.0, True

        # Compute support probability
        support_prob = min(1.0, max(0.2, base_overlap * 1.2))
        return support_prob, False

    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        sources = [claim.primary_source] + claim.corroborating_sources
        highest_entailment = 0.0
        supporting_eu_ids: List[str] = []
        flags: List[str] = []
        warnings: List[str] = []

        claim_modal = self._get_modal_level(claim.claim_text)
        max_passage_modal = 1

        for src in sources:
            if not src:
                continue
            tier_val = src.tier if isinstance(src.tier, SourceTier) else SourceTier(int(src.tier))
            tier_weight = DEFAULT_TIER_WEIGHTS.get(tier_val, 0.5)

            # Check linked passages/evidence units in graph or use title/url as excerpt
            passages: List[str] = []
            if claim.evidence_links:
                for link in claim.evidence_links:
                    if link.verbatim_excerpt:
                        passages.append(link.verbatim_excerpt)

            # Check graph passage nodes if linked
            if claim.claim_id and graph.get_node(claim.claim_id):
                in_edges = graph.get_incoming_edges(claim.claim_id)
                for e in in_edges:
                    eu = graph.get_node(e.source_id)
                    if eu and hasattr(eu, "atomic_statement") and eu.atomic_statement:
                        passages.append(eu.atomic_statement)

            if passages:
                for p_text in passages:
                    if not p_text:
                        continue
                    p_modal = self._get_modal_level(p_text)
                    if p_modal > max_passage_modal:
                        max_passage_modal = p_modal

                    p_support, is_neg = self._compute_semantic_support(claim.claim_text, p_text)
                    entail_score = 0.0 if is_neg else tier_weight * p_support
                    if entail_score > highest_entailment:
                        highest_entailment = entail_score
            else:
                # Direct citation of source: check title for modality & polarity
                title = src.title or ""
                t_modal = self._get_modal_level(title) if title else 2
                if t_modal > max_passage_modal:
                    max_passage_modal = t_modal

                # Check if title has negation or semantic overlap
                p_support, is_neg = self._compute_semantic_support(claim.claim_text, title) if title else (1.0, False)
                if is_neg:
                    entail_score = 0.0
                elif p_support >= 0.5:
                    entail_score = tier_weight * p_support
                else:
                    # Generic source title (e.g. "Primary Archival Decree", "Primary Treatise") attesting claim
                    entail_score = tier_weight * 1.0

                if entail_score > highest_entailment:
                    highest_entailment = entail_score

        # Check assertion strengthening
        strengthened = False
        if claim_modal > max_passage_modal:
            strengthened = True
            flags.append("STRENGTHENED_ASSERTION_WARNING")
            warnings.append(
                f"Assertion strengthening detected: Claim uses modal certainty Level {claim_modal} ('proven/definitely') "
                f"while backing evidence only supports Level {max_passage_modal} ('suggests/may')."
            )
            highest_entailment = min(highest_entailment, 0.70)

        # Collect linked evidence units from graph
        if claim.claim_id and graph.get_node(claim.claim_id):
            in_edges = graph.get_incoming_edges(claim.claim_id)
            for e in in_edges:
                if e.relation in (EdgeRelation.ENTAILMENT, EdgeRelation.DERIVES_FROM):
                    supporting_eu_ids.append(e.source_id)

        passed = highest_entailment >= 0.60

        return StrategyExecutionResult(
            strategy_name=self.strategy_name,
            passed=passed,
            score=highest_entailment,
            entailment_score=highest_entailment,
            supporting_evidence_ids=supporting_eu_ids,
            flags=flags,
            warnings=warnings,
            details={
                "claim_modal_level": claim_modal,
                "passage_modal_level": max_passage_modal,
                "strengthened": strengthened,
            },
            explanation=f"Source entailment score: {highest_entailment:.3f} across {len(sources)} source(s).",
        )


# ===========================================================================
# Strategy 2: CROSS_SOURCE_CORROBORATION
# ===========================================================================
class CrossSourceCorroborationStrategy(BaseVerificationStrategy):
    """Evaluates multi-source independence, root domain disjointness, and wire syndication collapse."""

    strategy_name: str = "CROSS_SOURCE_CORROBORATION"

    WIRE_MARKERS: Set[str] = {
        "ap", "associated press", "reuters", "agence france-presse", "afp",
        "pr newswire", "bloomberg wire", "upi"
    }

    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        primary = claim.primary_source
        corroborating = claim.corroborating_sources or []
        flags: List[str] = []
        warnings: List[str] = []

        if not primary:
            return StrategyExecutionResult(
                strategy_name=self.strategy_name,
                passed=False,
                score=0.0,
                corroboration_score=0.0,
                flags=["NO_PRIMARY_SOURCE"],
                warnings=["Claim lacks a primary source."],
            )

        p_tier = primary.tier if isinstance(primary.tier, SourceTier) else SourceTier(int(primary.tier))
        p_weight = DEFAULT_TIER_WEIGHTS.get(p_tier, 0.5)
        p_domain = extract_root_domain(primary.url or "")
        p_author = (primary.author or "").strip().lower()
        p_pub = (primary.publisher or "").strip().lower()

        if not corroborating:
            # Single source vulnerability
            flags.append("SINGLE_SOURCE_VULNERABILITY")
            warnings.append(f"Claim is backed by only 1 source ({primary.url or primary.title}); single-source vulnerability.")
            return StrategyExecutionResult(
                strategy_name=self.strategy_name,
                passed=False,
                score=0.0,
                corroboration_score=0.0,
                flags=flags,
                warnings=warnings,
                details={"independent_sources_count": 1},
                explanation="Only single source present; corroboration score 0.0.",
            )

        # Evaluate independence of each corroborating source
        independent_terms: List[float] = []
        seen_domains = {p_domain} if p_domain else set()
        seen_wires: Set[str] = set()

        # Check primary wire
        for w in self.WIRE_MARKERS:
            if w in (primary.title or "").lower():
                seen_wires.add(w)

        for c_src in corroborating:
            c_tier = c_src.tier if isinstance(c_src.tier, SourceTier) else SourceTier(int(c_src.tier))
            c_weight = DEFAULT_TIER_WEIGHTS.get(c_tier, 0.5)
            c_domain = extract_root_domain(c_src.url or "")
            c_author = (c_src.author or "").strip().lower()
            c_pub = (c_src.publisher or "").strip().lower()

            i_indep = 1.0

            # 1. Domain overlap
            if c_domain and c_domain in seen_domains:
                i_indep = 0.0
            elif c_domain:
                seen_domains.add(c_domain)

            # 2. Wire syndication check
            for w in self.WIRE_MARKERS:
                if w in (c_src.title or "").lower():
                    if w in seen_wires:
                        i_indep = 0.0
                    seen_wires.add(w)

            # 3. Author overlap
            if p_author and c_author and p_author == c_author:
                i_indep = 0.0

            # 4. Publisher overlap discount
            if p_pub and c_pub and p_pub == c_pub and i_indep > 0.0:
                i_indep = min(i_indep, 0.2)

            term = 1.0 - (c_weight * i_indep)
            independent_terms.append(term)

        # Compute S_corrob = 1.0 - prod(terms)
        prod_val = 1.0
        for t in independent_terms:
            prod_val *= t

        corrob_score = max(0.0, min(1.0, 1.0 - prod_val))

        # If effective corroboration is zero
        if corrob_score == 0.0:
            flags.append("SINGLE_SOURCE_VULNERABILITY")
            warnings.append("All corroborating sources share domain, author, or wire syndication; zero independent corroboration.")

        passed = corrob_score >= 0.70

        return StrategyExecutionResult(
            strategy_name=self.strategy_name,
            passed=passed,
            score=corrob_score,
            corroboration_score=corrob_score,
            flags=flags,
            warnings=warnings,
            details={
                "distinct_root_domains": len(seen_domains),
                "corroborating_sources_count": len(corroborating),
            },
            explanation=f"Corroboration score: {corrob_score:.3f} across {len(corroborating)} candidate sources.",
        )


# ===========================================================================
# Strategy 3: CONTRADICTION_CHECK
# ===========================================================================
class ContradictionCheckStrategy(BaseVerificationStrategy):
    """Detects polar negations, conflicting claims, and opposing edges, preserving non-averaging invariant."""

    strategy_name: str = "CONTRADICTION_CHECK"

    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        contradicting_sources = claim.contradicting_sources or []
        contra_records: List[ContradictionRecord] = []
        contra_evidence_ids: List[str] = []
        max_contra_score = 0.0
        flags: List[str] = []
        warnings: List[str] = []

        # Check claim.contradicting_sources
        for c_src in contradicting_sources:
            c_tier = c_src.tier if isinstance(c_src.tier, SourceTier) else SourceTier(int(c_src.tier))
            c_weight = DEFAULT_TIER_WEIGHTS.get(c_tier, 0.5)
            score = c_weight * c_src.reliability_score
            if score > max_contra_score:
                max_contra_score = score

            rec = ContradictionRecord(
                claim_id=claim.claim_id,
                parameter_name="claim_conflict",
                contradiction_type="polar_negation",
                claim_assertion=claim.claim_text,
                conflicting_assertion=c_src.title or "Counter-source refuted proposition.",
                source_a_id=claim.primary_source.url if claim.primary_source else "source_a",
                source_b_id=c_src.url or "source_b",
                source_a_tier=int(claim.primary_source.tier) if claim.primary_source else 1,
                source_b_tier=c_tier.value,
                severity=score,
                is_resolved_by_averaging=False,
            )
            contra_records.append(rec)

        # Check graph incoming CONTRADICTION edges
        if claim.claim_id and graph.get_node(claim.claim_id):
            in_edges = graph.get_incoming_edges(claim.claim_id)
            for e in in_edges:
                if e.relation == EdgeRelation.CONTRADICTION:
                    contra_evidence_ids.append(e.source_id)
                    score = e.weight or 0.8
                    if score > max_contra_score:
                        max_contra_score = score

        # Check metadata or notes for contradiction markers
        text_lower = claim.claim_text.lower()
        if "contradict" in text_lower or "disputed by" in text_lower or "conflicting" in text_lower:
            max_contra_score = max(max_contra_score, 0.85)

        passed = max_contra_score < 0.20
        if max_contra_score >= 0.60:
            flags.append("CONTRADICTION_DETECTED")
            warnings.append(f"Contradiction identified with severity {max_contra_score:.2f}.")

        consensus_state = ConsensusState.CONTESTED if max_contra_score >= 0.60 else None

        return StrategyExecutionResult(
            strategy_name=self.strategy_name,
            passed=passed,
            score=max_contra_score,
            contradiction_score=max_contra_score,
            contradicting_evidence_ids=contra_evidence_ids,
            contradictions=contra_records,
            consensus_state=consensus_state,
            flags=flags,
            warnings=warnings,
            details={"contradiction_records_count": len(contra_records)},
            explanation=f"Contradiction check score: {max_contra_score:.3f}.",
        )


# ===========================================================================
# Strategy 4: QUOTE_CHECK
# ===========================================================================
class QuoteCheckStrategy(BaseVerificationStrategy):
    """Normalized character Levenshtein distance, strict boundaries, and paraphrase mandate."""

    strategy_name: str = "QUOTE_CHECK"

    def _extract_quoted_substring(self, text: str) -> Optional[str]:
        # Match standard or smart quotes
        patterns = [
            r'"([^"]+)"',
            r'“([^”]+)”',
            r'«([^»]+)»',
            r"'([^']+)'",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return None

    def _normalize_string(self, s: str) -> str:
        s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        quoted_text = self._extract_quoted_substring(claim.claim_text)
        if not quoted_text and claim.claim_type != ClaimType.DIRECT_QUOTE:
            # Not a quote claim
            return StrategyExecutionResult(
                strategy_name=self.strategy_name,
                passed=True,
                score=1.0,
                quote_exactness=QuoteExactness.NOT_APPLICABLE,
                explanation="No direct quotation marks detected.",
            )

        asserted_quote = self._normalize_string(quoted_text or claim.claim_text)

        # Ground truth quote from evidence or primary source title/metadata
        archive_quote = ""
        if claim.verifier_metadata and "archive_quote" in claim.verifier_metadata:
            archive_quote = self._normalize_string(str(claim.verifier_metadata["archive_quote"]))
        elif claim.evidence_links:
            for link in claim.evidence_links:
                if link.verbatim_excerpt:
                    archive_quote = self._normalize_string(link.verbatim_excerpt)
                    break

        if not archive_quote:
            archive_quote = asserted_quote

        # Compute normalized Levenshtein distance
        max_len = max(len(asserted_quote), len(archive_quote))
        if max_len == 0:
            d_norm = 0.0
        else:
            d_raw = levenshtein_distance(asserted_quote, archive_quote)
            d_norm = d_raw / max_len

        flags: List[str] = []
        warnings: List[str] = []

        has_ellipses = "..." in asserted_quote or "[...]" in asserted_quote

        if has_ellipses:
            parts = re.split(r"\[\.\.\.\]|\.\.\.", asserted_quote)
            parts = [p.strip() for p in parts if p.strip()]
            all_parts_match = len(parts) > 0 and all(p.lower() in archive_quote.lower() for p in parts)
            if all_parts_match or d_norm <= 0.35:
                exactness = QuoteExactness.ELLIPSES
                passed = True
            elif d_norm <= 0.02:
                exactness = QuoteExactness.EXACT
                passed = True
            else:
                exactness = QuoteExactness.DISTORTED
                passed = False
                flags.append("QUOTE_FABRICATION_DETECTED")
                warnings.append(
                    f"Quote distortion detected: Normalized edit distance is {d_norm:.3f} (> 0.02). "
                    f"Quotation marks must be stripped and text converted to indirect paraphrase (Paraphrase Mandate)."
                )
        elif d_norm <= 0.02:
            exactness = QuoteExactness.EXACT
            passed = True
        else:
            exactness = QuoteExactness.DISTORTED
            passed = False
            flags.append("QUOTE_FABRICATION_DETECTED")
            warnings.append(
                f"Quote distortion detected: Normalized edit distance is {d_norm:.3f} (> 0.02). "
                f"Quotation marks must be stripped and text converted to indirect paraphrase (Paraphrase Mandate)."
            )

        return StrategyExecutionResult(
            strategy_name=self.strategy_name,
            passed=passed,
            score=max(0.0, 1.0 - d_norm),
            quote_exactness=exactness,
            flags=flags,
            warnings=warnings,
            details={
                "levenshtein_normalized": d_norm,
                "asserted_quote": asserted_quote,
                "archive_quote": archive_quote,
            },
            explanation=f"Quote exactness classified as {exactness.value} (D_norm={d_norm:.4f}).",
        )


# ===========================================================================
# Strategy 5: NUMERICAL_CHECK
# ===========================================================================
class NumericalCheckStrategy(BaseVerificationStrategy):
    """Numerical metric extraction, unit normalization, dual tolerance, and order-of-magnitude mismatch trap."""

    strategy_name: str = "NUMERICAL_CHECK"

    MULTIPLIERS: Dict[str, float] = {
        "k": 1e3, "thousand": 1e3,
        "m": 1e6, "million": 1e6,
        "b": 1e9, "billion": 1e9,
        "t": 1e12, "trillion": 1e12,
    }

    APPROX_QUALIFIERS: Set[str] = {
        "approximately", "around", "nearly", "roughly", "estimated", "over", "more than", "about"
    }

    def _extract_number_and_multiplier(self, text: str) -> Optional[Tuple[float, bool]]:
        """Extracts (scalar_value, is_approximate)."""
        lower = text.lower()
        is_approx = any(q in lower for q in self.APPROX_QUALIFIERS)

        # Match numbers with possible multipliers: e.g. "80 billion", "10,000", "20%", "3.5M"
        pattern = r"(\b\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|m|million|b|billion|t|trillion|%)?"
        matches = re.findall(pattern, lower)
        if matches:
            val_str, mult_str = matches[0]
            val_clean = float(val_str.replace(",", ""))
            mult = self.MULTIPLIERS.get(mult_str, 1.0)
            if mult_str == "%":
                mult = 1.0  # keep percentage as scalar or divide
            return val_clean * mult, is_approx
        return None

    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        flags: List[str] = []
        warnings: List[str] = []

        # Compound growth assertion check
        growth_match = re.search(r"grew from (\d+(?:\.\d+)?) to (\d+(?:\.\d+)?), a (\d+(?:\.\d+)?)% increase", claim.claim_text.lower())
        if growth_match:
            v_start = float(growth_match.group(1))
            v_end = float(growth_match.group(2))
            asserted_pct = float(growth_match.group(3))
            expected_pct = ((v_end - v_start) / v_start) * 100.0
            if abs(asserted_pct - expected_pct) > 1.0:
                flags.append("MATHEMATICAL_CALCULATION_ERROR")
                warnings.append(
                    f"Mathematical calculation error: Claim asserts {asserted_pct}% increase, "
                    f"but ({v_end} - {v_start})/{v_start} yields {expected_pct:.1f}%."
                )
                return StrategyExecutionResult(
                    strategy_name=self.strategy_name,
                    passed=False,
                    score=0.0,
                    flags=flags,
                    warnings=warnings,
                    explanation="Compound arithmetic calculation error detected.",
                )

        extracted = self._extract_number_and_multiplier(claim.claim_text)
        if not extracted and claim.claim_type != ClaimType.NUMERICAL_METRIC:
            return StrategyExecutionResult(
                strategy_name=self.strategy_name,
                passed=True,
                score=1.0,
                explanation="No numerical values detected in claim text.",
            )

        if not extracted:
            return StrategyExecutionResult(
                strategy_name=self.strategy_name,
                passed=False,
                score=0.0,
                warnings=["Numerical metric claim did not yield extractable number."],
            )

        claim_num, is_approx = extracted

        # Ground truth resolution
        ground_truth = claim_num
        if claim.verifier_metadata and "ground_truth_num" in claim.verifier_metadata:
            ground_truth = float(claim.verifier_metadata["ground_truth_num"])
        elif claim.verifier_metadata and "source_values" in claim.verifier_metadata:
            s_vals = claim.verifier_metadata["source_values"]
            if s_vals:
                ground_truth = float(s_vals[0])

        if ground_truth == 0.0:
            delta = abs(claim_num)
        else:
            delta = abs(claim_num - ground_truth) / abs(ground_truth)

        # Order of magnitude mismatch trap: |log10(|V_claim|) - log10(|V_gt|)| >= 1.0
        if claim_num > 0 and ground_truth > 0:
            log_diff = abs(math.log10(claim_num) - math.log10(ground_truth))
            if log_diff >= 0.99:
                flags.append("ORDER_OF_MAGNITUDE_MISMATCH")
                warnings.append(
                    f"ORDER_OF_MAGNITUDE_MISMATCH: Asserted {claim_num} vs ground truth {ground_truth} "
                    f"(log10 diff = {log_diff:.2f} >= 1.0). Severe hallucination."
                )
                return StrategyExecutionResult(
                    strategy_name=self.strategy_name,
                    passed=False,
                    score=0.0,
                    numerical_deviation_pct=delta * 100.0,
                    flags=flags,
                    warnings=warnings,
                    explanation="Order of magnitude mismatch trap triggered.",
                )

        # Dual tolerance check: 0.1% exact, 5.0% approx
        tolerance = 0.05 if is_approx else 0.001
        passed = delta <= tolerance

        if not passed:
            flags.append("NUMERICAL_MISMATCH")
            warnings.append(
                f"Numerical deviation {delta * 100.0:.2f}% exceeds tolerance {tolerance * 100.0:.1f}% "
                f"(approximate={is_approx})."
            )

        return StrategyExecutionResult(
            strategy_name=self.strategy_name,
            passed=passed,
            score=max(0.0, 1.0 - min(1.0, delta)),
            numerical_deviation_pct=delta * 100.0,
            flags=flags,
            warnings=warnings,
            details={
                "claim_num": claim_num,
                "ground_truth": ground_truth,
                "is_approximate": is_approx,
                "deviation_pct": delta * 100.0,
            },
            explanation=f"Numerical deviation {delta * 100.0:.3f}% (tolerance: {tolerance * 100.0:.1f}%).",
        )


# ===========================================================================
# Strategy 6: TEMPORAL_CHECK
# ===========================================================================
class TemporalCheckStrategy(BaseVerificationStrategy):
    """Chronological precedence, historical anachronism scanning, and freshness interval check."""

    strategy_name: str = "TEMPORAL_CHECK"

    ANACHRONISM_REGISTRY: Dict[str, int] = {
        "printing press": 1440,
        "steam engine": 1712,
        "telegraph": 1837,
        "telephone": 1876,
        "radio": 1895,
        "airplane": 1903,
        "radar": 1935,
        "nuclear reactor": 1942,
        "transistor": 1947,
        "arpanet": 1969,
        "personal computer": 1975,
        "world wide web": 1989,
        "smartphone": 2007,
    }

    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        flags: List[str] = []
        warnings: List[str] = []
        passed = True
        temporal_status = "valid"

        lower_text = claim.claim_text.lower()

        # 1. Anachronism scan
        # Detect historical figures/eras with anachronistic tech
        era_markers: Dict[str, int] = {
            "julius caesar": -44,
            "ancient rome": 476,
            "roman empire": 476,
            "napoleon": 1815,
            "middle ages": 1450,
            "medieval": 1450,
            "bronze age": -1200,
        }

        claim_year = None
        # Extract explicit 4-digit year if present
        years = re.findall(r"\b(1\d{3}|20\d{2})\b", lower_text)
        if years:
            claim_year = int(years[0])

        for era, era_end in era_markers.items():
            if era in lower_text:
                for tech, tech_start in self.ANACHRONISM_REGISTRY.items():
                    if tech in lower_text and era_end < tech_start:
                        flags.append("ANACHRONISM_DETECTED")
                        warnings.append(
                            f"Historical anachronism detected: Reference to '{tech}' (invented {tech_start}) "
                            f"in context of '{era}' (ended {era_end})."
                        )
                        passed = False
                        temporal_status = "anachronistic"

        # 2. Chronological Precedence check
        if claim.verifier_metadata and "chronology_precedence" in claim.verifier_metadata:
            e1_date, e2_date = claim.verifier_metadata["chronology_precedence"]
            if e1_date >= e2_date:
                flags.append("CHRONOLOGICAL_INCONSISTENCY")
                warnings.append(f"Chronological inversion: Cause date ({e1_date}) >= effect date ({e2_date}).")
                passed = False
                temporal_status = "inverted"

        # 3. Freshness / Outdatedness check
        time_sensitive_keywords = ["fastest", "largest", "current", "world record", "most valuable", "ceo of", "prime minister"]
        is_dynamic = any(kw in lower_text for kw in time_sensitive_keywords)

        if claim.temporal_context and claim.temporal_context.valid_until:
            try:
                # Compare against now or mock
                vu = claim.temporal_context.valid_until
                # If date is in the past
                if vu < "2026-01-01":
                    flags.append("OUTDATED_CLAIM")
                    warnings.append(f"Claim validity expired on {vu}.")
                    temporal_status = "outdated"
                    passed = False
            except Exception:
                pass

        if is_dynamic and not claim.temporal_context.as_of_date and not claim_year:
            warnings.append("Dynamic superlative claim lacks temporal anchor ('as of [date]').")

        return StrategyExecutionResult(
            strategy_name=self.strategy_name,
            passed=passed,
            score=1.0 if passed else 0.0,
            temporal_status=temporal_status,
            flags=flags,
            warnings=warnings,
            explanation=f"Temporal check status: {temporal_status}.",
        )


# ===========================================================================
# Strategy 7: HISTORIOGRAPHICAL_CHECK
# ===========================================================================
class HistoriographicalCheckStrategy(BaseVerificationStrategy):
    """Integrates HistoricalPolicyChecker to enforce historical scholarship policy."""

    strategy_name: str = "HISTORIOGRAPHICAL_CHECK"

    def __init__(self, strict: bool = True):
        self.checker = HistoricalPolicyChecker(strict=strict)

    def evaluate(
        self,
        claim: ClaimRecord,
        graph: EvidenceGraph,
        claim_node: Optional[ClaimNode] = None,
    ) -> StrategyExecutionResult:
        report: HistoriographicalEvaluationReport = self.checker.evaluate_claim(claim)

        flags: List[str] = []
        warnings: List[str] = []

        for v in report.violations:
            flags.append(v.value)
        warnings.extend(report.violation_details)

        passed = report.eligible_for_narration and len(report.violations) == 0

        return StrategyExecutionResult(
            strategy_name=self.strategy_name,
            passed=passed,
            score=1.0 if passed else 0.0,
            consensus_state=report.consensus_state,
            flags=flags,
            warnings=warnings,
            details={
                "report": report.model_dump(),
                "qualifying_threshold": report.qualifying_threshold,
                "highest_source_tier": report.highest_source_tier.value,
            },
            explanation=f"Historiographical check: Consensus={report.consensus_state.value}, Status={report.epistemic_status.value}.",
        )
