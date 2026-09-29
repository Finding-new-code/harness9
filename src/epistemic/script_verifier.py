"""src/epistemic/script_verifier.py — Post-Script Claim Re-Verification & Drift Detection Engine.

Extracts discrete timestamped sentences from generated scripts, aligns them to
EvidenceGraph DAG nodes, detects 4 canonical drift classes (strengthened claims,
altered numbers, omitted uncertainty, fabricated quotes), mandates paraphrasing,
and mutatively synchronizes verification traces into the EvidenceGraph DAG.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import math
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import uuid

from pydantic import Field, field_validator, model_validator

from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    H9BaseModel,
    QuoteExactness,
    ResearchDossier,
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
    SourceTier,
)
from src.epistemic.graph import (
    ClaimNode,
    EdgeRelation,
    EvidenceGraph,
    GraphNodeType,
    ScriptSentenceNode,
    VerificationTraceNode,
)


# ===========================================================================
# 1. Enums & Core Contracts
# ===========================================================================

class DriftType(str, Enum):
    """Categorical taxonomy of factual semantic drift in generated scripts."""
    STRENGTHENED = "strengthened"
    ALTERED_NUMBER = "altered_number"
    OMITTED_UNCERTAINTY = "omitted_uncertainty"
    FABRICATED_QUOTE = "fabricated_quote"
    UNGROUNDED_CLAIM = "ungrounded_claim"
    ANACHRONISM = "anachronism"


class DriftSeverity(str, Enum):
    """Impact level of a detected drift on publication gating."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScriptSentenceExtraction(H9BaseModel):
    """Timestamped grammatical sentence extracted from a script scene beat."""
    extraction_id: str = Field(default_factory=lambda: f"ext_{uuid.uuid4().hex[:8]}")
    scene_id: str
    scene_index: int = 1
    beat_id: Optional[str] = None
    beat_index: int = 1
    sentence_index: int = 1
    sentence_text: str
    start_time: float = 0.0
    end_time: float = 0.0
    modal_level: int = 2  # 1=hedged/preliminary, 2=standard/likely, 3=absolute/proven
    extracted_numbers: List[Tuple[float, str, bool]] = Field(
        default_factory=list,
        description="List of (numeric_value, raw_token, is_approximate)"
    )
    extracted_quotes: List[str] = Field(default_factory=list)
    temporal_anchors: List[str] = Field(default_factory=list)
    is_rhetorical: bool = False
    grounded_claim_ids: List[str] = Field(default_factory=list)


class ScriptClaimDriftRecord(H9BaseModel):
    """Detailed forensic record of an identified factual drift in a script beat."""
    drift_id: str = Field(default_factory=lambda: f"drift_{uuid.uuid4().hex[:8]}")
    drift_type: DriftType
    severity: DriftSeverity
    scene_id: str
    beat_id: Optional[str] = None
    script_sentence: str
    evidence_claim_id: Optional[str] = None
    evidence_text: Optional[str] = None
    observed_value: Any = None
    expected_value: Any = None
    explanation: str
    recommended_edit: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScriptClaimMapping(H9BaseModel):
    """Provenance mapping connecting a script sentence to an EvidenceGraph node."""
    mapping_id: str = Field(default_factory=lambda: f"map_{uuid.uuid4().hex[:8]}")
    scene_id: str
    beat_id: Optional[str] = None
    sentence_text: str
    start_time: float = 0.0
    end_time: float = 0.0
    aligned_claim_id: Optional[str] = None
    alignment_score: float = 0.0
    is_grounded: bool = False
    has_drift: bool = False
    drifts: List[ScriptClaimDriftRecord] = Field(default_factory=list)


class ScriptVerificationReport(H9BaseModel):
    """Canonical verification verdict emitted by ScriptVerifier."""
    report_id: str = Field(default_factory=lambda: f"svr_{uuid.uuid4().hex[:8]}")
    project_id: Optional[str] = None
    topic: str = ""
    total_scenes: int = 0
    total_beats: int = 0
    total_sentences: int = 0
    grounded_sentences_count: int = 0
    ungrounded_sentences_count: int = 0
    drifts: List[ScriptClaimDriftRecord] = Field(default_factory=list)
    drift_counts_by_type: Dict[str, int] = Field(default_factory=dict)
    drift_counts_by_severity: Dict[str, int] = Field(default_factory=dict)
    mappings: List[ScriptClaimMapping] = Field(default_factory=list)
    passed: bool = True
    gate_recommendation: str = "PASS"  # PASS | WARN | HUMAN_REVIEW | BLOCK
    summary: str = ""
    revised_script: Optional[Any] = None
    graph_id: str = ""
    duration_ms: float = 0.0
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ===========================================================================
# 2. Heuristic Lexicons & Text Utilities
# ===========================================================================

MODAL_LEVEL_3_TERMS = {
    "always", "proven", "definitely", "solely", "undoubtedly", "certainly",
    "indisputable", "conclusively", "conclusive", "undeniably", "settled",
    "fact", "irrefutably", "single-handedly", "unquestionably"
}

MODAL_LEVEL_2_TERMS = {
    "generally", "typically", "the primary", "most", "likely", "probably",
    "largely", "mainly", "usually", "standard"
}

MODAL_LEVEL_1_TERMS = {
    "may", "suggests", "suggest", "suggesting", "one factor", "partially",
    "possibly", "could", "preliminary", "hypothesized", "might", "potentially",
    "in some cases", "tentatively", "indicated"
}

APPROXIMATION_TERMS = {
    "approximately", "about", "around", "nearly", "roughly", "over", "under",
    "estimated", "approx", "almost", "close to", "in the range of"
}

ABBREVIATIONS = {
    "dr.", "mr.", "mrs.", "ms.", "prof.", "u.s.", "u.k.", "e.g.", "i.e.",
    "vs.", "etc.", "approx.", "fig.", "st.", "gen.", "col.", "dept.", "inc.",
    "ltd.", "co.", "jr.", "sr."
}

HISTORICAL_UNCERTAINTY_HEDGES = {
    ConsensusState.ACTIVE_DEBATE: [
        "historians remain divided", "debate continues", "scholars disagree",
        "contested", "divided", "differing views", "competing theories", "debate"
    ],
    ConsensusState.CONTESTED: [
        "disputed", "contradict", "range from", "conflicting sources",
        "contested", "debated", "uncertain", "unclear"
    ],
    ConsensusState.MINORITY_INTERPRETATION: [
        "alternative view", "counter-thesis", "minority of scholars",
        "some historians argue", "counter-argument", "some scholars", "others contend"
    ],
    ConsensusState.UNRESOLVED: [
        "unanswered", "unresolved", "unknown", "uncertain", "surviving records leave",
        "remains a mystery"
    ],
}

# Compiled word-boundary regex patterns for robust classification
MODAL_LEVEL_3_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_3_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
MODAL_LEVEL_2_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_2_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
MODAL_LEVEL_1_TERMS_NO_MAY = [t for t in MODAL_LEVEL_1_TERMS if t != "may"]
MODAL_LEVEL_1_PATTERN = re.compile(
    r'(?i:\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_1_TERMS_NO_MAY, key=len, reverse=True)) + r')\b)|\bmay\b|^May\b|(?<=\.\s)May\b'
)
APPROXIMATION_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(APPROXIMATION_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
COMPOUND_GROWTH_PATTERN = re.compile(
    r'(?:grew|increased|rose|surged|jumped|climbed)\s+from\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?\s+to\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?(?:,\s*|\s+)(?:a|an|\(a|\(an)?\s*(?:increase\s+of\s+|growth\s+of\s+|up\s+)?(\d+(?:\.\d+)?)%\s*(?:increase|growth)?\)?',
    re.IGNORECASE
)


def compute_normalized_levenshtein(s1: str, s2: str) -> float:
    """Computes normalized Levenshtein distance in [0.0, 1.0]."""
    str1 = s1.strip().lower()
    str2 = s2.strip().lower()
    if str1 == str2:
        return 0.0
    if not str1:
        return 1.0
    if not str2:
        return 1.0

    len1, len2 = len(str1), len(str2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        c1 = str1[i - 1]
        for j in range(1, len2 + 1):
            c2 = str2[j - 1]
            cost = 0 if c1 == c2 else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )

    raw_dist = dp[len1][len2]
    max_len = max(len1, len2)
    return raw_dist / max_len if max_len > 0 else 0.0


# ===========================================================================
# 3. Post-Script Claim Verifier Engine
# ===========================================================================

class ScriptVerifier:
    """Post-script claim extraction and re-verification engine."""

    def __init__(
        self,
        verifier_name: str = "H9ScriptClaimVerifier",
        tolerance_exact: float = 0.001,  # 0.1%
        tolerance_approx: float = 0.05,  # 5.0%
        strict: bool = True,
        abbreviations: Optional[Set[str]] = None,
    ) -> None:
        self.verifier_name = verifier_name
        self.tolerance_exact = tolerance_exact
        self.tolerance_approx = tolerance_approx
        self.strict = strict
        self.abbreviations = set(abbreviations) if abbreviations is not None else set(ABBREVIATIONS)

    # -----------------------------------------------------------------------
    # 1. Sentence Segmentation & Text Normalization
    # -----------------------------------------------------------------------
    def segment_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """Splits raw text into sentences while protecting abbreviations, numbers, and quotes."""
        if not text or not text.strip():
            return []

        # Mask abbreviations and decimal numbers temporarily
        working = text
        spans: List[Tuple[int, int]] = []
        active_abbrevs = self.abbreviations if hasattr(self, "abbreviations") and self.abbreviations is not None else ABBREVIATIONS

        # Find sentence boundaries: punctuation (.!?) followed by space and capital letter or end of string
        # Boundary pattern respects quotes after terminal punctuation e.g. 'Stop!' or "No."
        pattern = r'([.!?]+[\'"”’]?)(?:\s+(?=[A-Z0-9"\'“‘])|\s*$)'

        last_end = 0
        for m in re.finditer(pattern, working):
            punct_end = m.end(1)
            candidate_text = working[last_end:punct_end].strip()

            # Check if candidate ends with an abbreviation
            words = candidate_text.split()
            if words:
                last_word = words[-1].lower()
                if last_word in active_abbrevs:
                    # Do not split on abbreviation
                    continue
                # Also check decimal number like '$3.5M.' or '3.14'
                if re.search(r'\b\d+\.\d*$', candidate_text):
                    continue

            # Valid sentence boundary
            start_idx = working.find(candidate_text, last_end)
            if start_idx != -1:
                end_idx = start_idx + len(candidate_text)
                spans.append((candidate_text, start_idx, end_idx))
                last_end = m.end()

        # Catch trailing segment if any
        if last_end < len(working):
            trailing = working[last_end:].strip()
            if trailing:
                start_idx = working.find(trailing, last_end)
                spans.append((trailing, start_idx, start_idx + len(trailing)))

        if not spans:
            clean_full = text.strip()
            return [(clean_full, 0, len(clean_full))]

        return spans

    def extract_sentences(
        self,
        script: Union[Script, Dict[str, Any], str, Any],
    ) -> List[ScriptSentenceExtraction]:
        """Extracts and annotates discrete timestamped sentences across script scenes and beats."""
        extractions: List[ScriptSentenceExtraction] = []
        normalized_scenes = self._normalize_script_scenes(script)

        for sc_idx, sc in enumerate(normalized_scenes, start=1):
            scene_id = sc.get("scene_id", f"scene_{sc_idx}")
            beats = sc.get("beats", [])

            if not beats:
                # Scene has raw narration but no explicit beats
                raw_narration = sc.get("narration_text") or sc.get("narration") or ""
                dur = float(sc.get("duration", 5.0) or 5.0)
                st = float(sc.get("start_time", 0.0) or 0.0)
                sentence_spans = self.segment_sentences(raw_narration)
                total_chars = max(1, len(raw_narration))

                for s_idx, (stext, c_start, c_end) in enumerate(sentence_spans, start=1):
                    s_start = st + (c_start / total_chars) * dur
                    s_end = st + (c_end / total_chars) * dur
                    ext = self._annotate_sentence(
                        scene_id=scene_id,
                        scene_index=sc_idx,
                        beat_id=f"{scene_id}_beat_1",
                        beat_index=1,
                        sentence_index=s_idx,
                        sentence_text=stext,
                        start_time=s_start,
                        end_time=s_end,
                    )
                    extractions.append(ext)
                continue

            for b_idx, beat in enumerate(beats, start=1):
                beat_id = beat.get("beat_id", f"{scene_id}_beat_{b_idx}")
                b_text = beat.get("text", "")
                b_dur = float(beat.get("duration", 0.0) or 0.0)
                b_start = float(beat.get("start_time", 0.0) or 0.0)
                b_end = float(beat.get("end_time", b_start + b_dur) or (b_start + b_dur))
                if b_dur == 0.0 and b_end >= b_start:
                    b_dur = b_end - b_start

                sentence_spans = self.segment_sentences(b_text)
                total_chars = max(1, len(b_text))

                for s_idx, (stext, c_start, c_end) in enumerate(sentence_spans, start=1):
                    s_start = b_start + (c_start / total_chars) * b_dur
                    s_end = b_start + (c_end / total_chars) * b_dur
                    ext = self._annotate_sentence(
                        scene_id=scene_id,
                        scene_index=sc_idx,
                        beat_id=beat_id,
                        beat_index=b_idx,
                        sentence_index=s_idx,
                        sentence_text=stext,
                        start_time=s_start,
                        end_time=s_end,
                        grounded_claim_ids=beat.get("grounded_claim_ids", []),
                    )
                    extractions.append(ext)

        return extractions

    def _annotate_sentence(
        self,
        scene_id: str,
        scene_index: int,
        beat_id: str,
        beat_index: int,
        sentence_index: int,
        sentence_text: str,
        start_time: float,
        end_time: float,
        grounded_claim_ids: Optional[List[str]] = None,
    ) -> ScriptSentenceExtraction:
        """Annotates a sentence with modal level, numbers, quotes, and temporal anchors."""
        lower = sentence_text.lower()

        # Modal level classification using word boundaries
        modal_level = 2
        if MODAL_LEVEL_3_PATTERN.search(sentence_text):
            modal_level = 3
        elif MODAL_LEVEL_1_PATTERN.search(sentence_text):
            modal_level = 1

        # Number extraction
        has_approx = bool(APPROXIMATION_PATTERN.search(sentence_text))
        extracted_nums = self._extract_numbers_from_text(sentence_text, has_approx)

        # Quote extraction: double quotes or single quotes not part of contractions/possessives
        quotes = []
        for m in re.finditer(r'["“]([^"”\r\n]{3,})["”]', sentence_text):
            quotes.append(m.group(1))
        single_quote_pattern = r'(?:(?<=^)|(?<=[\s\(\[\{,:]))[\'‘]((?:[^\'’\r\n]|(?<=[a-zA-Z])[\'’](?=[a-zA-Z])){3,}?)[\'’](?=$|[\s.,!?;:\)\]\}])'
        for m in re.finditer(single_quote_pattern, sentence_text):
            quotes.append(m.group(1))

        # Temporal anchors (years)
        years = re.findall(r'\b(1\d{3}|20\d{2})\b', sentence_text)

        # Check rhetorical commentary
        rhetorical = bool(re.search(r'\b(welcome back|in this video|thanks for watching|subscribe|stay tuned)\b', lower))

        return ScriptSentenceExtraction(
            scene_id=scene_id,
            scene_index=scene_index,
            beat_id=beat_id,
            beat_index=beat_index,
            sentence_index=sentence_index,
            sentence_text=sentence_text,
            start_time=start_time,
            end_time=end_time,
            modal_level=modal_level,
            extracted_numbers=extracted_nums,
            extracted_quotes=quotes,
            temporal_anchors=years,
            is_rhetorical=rhetorical,
            grounded_claim_ids=grounded_claim_ids or [],
        )

    def _extract_numbers_from_text(self, text: str, default_approx: bool) -> List[Tuple[float, str, bool]]:
        """Extracts scalar numbers, multipliers (K, M, B), and percentages."""
        results = []
        pattern = r'(\b\d+(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|thousand|k|m|b|%|percent)?'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            raw_str = m.group(1).replace(",", "")
            mult_str = (m.group(2) or "").lower()
            try:
                val = float(raw_str)
            except ValueError:
                continue

            if mult_str in ("billion", "b"):
                val *= 1e9
            elif mult_str in ("million", "m"):
                val *= 1e6
            elif mult_str in ("thousand", "k"):
                val *= 1e3

            # Check local approximation around the number
            start_pos = max(0, m.start() - 20)
            end_pos = min(len(text), m.end() + 20)
            context = text[start_pos:end_pos].lower()
            local_approx = default_approx or any(term in context for term in APPROXIMATION_TERMS)

            results.append((val, m.group(0), local_approx))

        return results

    # -----------------------------------------------------------------------
    # 2. Bipartite Alignment against EvidenceGraph
    # -----------------------------------------------------------------------
    def align_sentences_to_graph(
        self,
        extractions: List[ScriptSentenceExtraction],
        graph: Optional[EvidenceGraph] = None,
    ) -> List[ScriptClaimMapping]:
        """Aligns extracted sentences to EvidenceGraph ClaimNodes or EvidenceUnits."""
        mappings: List[ScriptClaimMapping] = []
        if graph is None or not graph._nodes:
            # Fallback when graph is absent or empty
            for ext in extractions:
                mappings.append(
                    ScriptClaimMapping(
                        scene_id=ext.scene_id,
                        beat_id=ext.beat_id,
                        sentence_text=ext.sentence_text,
                        start_time=ext.start_time,
                        end_time=ext.end_time,
                        aligned_claim_id=None,
                        alignment_score=0.0,
                        is_grounded=ext.is_rhetorical,
                    )
                )
            return mappings

        # Gather claim nodes
        claim_nodes: List[ClaimNode] = [
            n for n in graph._nodes.values() if isinstance(n, ClaimNode)
        ]

        for ext in extractions:
            best_node_id: Optional[str] = None
            best_score: float = 0.0

            # 1. Direct explicit claim IDs
            if ext.grounded_claim_ids:
                for cid in ext.grounded_claim_ids:
                    if cid in graph._nodes:
                        best_node_id = cid
                        best_score = 1.0
                        break

            # 2. Semantic token overlap with ClaimNodes
            if best_score < 0.9 and claim_nodes:
                STOP_WORDS = {
                    "the", "and", "that", "have", "for", "with", "this", "from", "they",
                    "here", "were", "been", "their", "will", "would", "there", "about",
                    "which", "when", "what", "more", "some", "such", "only", "other",
                    "into", "than", "then", "also", "very", "said", "over", "under", "all",
                    "recent", "between", "include", "including", "has", "are", "was"
                }
                sent_words = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', ext.sentence_text.lower()))
                sent_content = {w for w in sent_words if w not in STOP_WORDS}
                for cn in claim_nodes:
                    claim_words = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', cn.claim_text.lower()))
                    claim_content = {w for w in claim_words if w not in STOP_WORDS}
                    if not sent_content or not claim_content:
                        continue
                    overlap = len(sent_content.intersection(claim_content))
                    score = (2.0 * overlap) / (len(sent_content) + len(claim_content))
                    if overlap >= 1 and score < 0.35:
                        score = max(score, 0.40)

                    # Boost if numbers or years match exactly
                    if ext.temporal_anchors:
                        for yr in ext.temporal_anchors:
                            if yr in cn.claim_text:
                                score += 0.25

                    # Boost if author name in sentence
                    if hasattr(cn, "claim_record") and cn.claim_record and cn.claim_record.primary_source:
                        author = getattr(cn.claim_record.primary_source, "author", "") or ""
                        if author and author.lower() in ext.sentence_text.lower():
                            score += 0.50

                    if score > best_score:
                        best_score = score
                        best_node_id = cn.claim_id

            is_grounded = best_score >= 0.35 or ext.is_rhetorical
            mappings.append(
                ScriptClaimMapping(
                    scene_id=ext.scene_id,
                    beat_id=ext.beat_id,
                    sentence_text=ext.sentence_text,
                    start_time=ext.start_time,
                    end_time=ext.end_time,
                    aligned_claim_id=best_node_id if is_grounded else None,
                    alignment_score=best_score,
                    is_grounded=is_grounded,
                )
            )

        return mappings

    # -----------------------------------------------------------------------
    # 3. 4-Fold Forensic Drift Detection
    # -----------------------------------------------------------------------
    def check_drift(
        self,
        ext: ScriptSentenceExtraction,
        mapping: ScriptClaimMapping,
        graph: Optional[EvidenceGraph] = None,
    ) -> List[ScriptClaimDriftRecord]:
        """Audits an aligned mapping for strengthened claims, altered numbers, omitted uncertainty, and quotes."""
        drifts: List[ScriptClaimDriftRecord] = []
        if ext.is_rhetorical:
            return drifts

        # Check compound growth rate arithmetic error in script sentence itself (runs unconditionally)
        self._check_compound_growth_error(ext, drifts)

        # Check quotes against all direct quote claims in graph (runs unconditionally)
        if ext.extracted_quotes and graph is not None:
            self._check_all_quotes_against_graph(ext, graph, drifts)

        # Unaligned claim check
        if not mapping.is_grounded or not mapping.aligned_claim_id:
            if not drifts:
                drifts.append(
                    ScriptClaimDriftRecord(
                        drift_type=DriftType.UNGROUNDED_CLAIM,
                        severity=DriftSeverity.HIGH,
                        scene_id=ext.scene_id,
                        beat_id=ext.beat_id,
                        script_sentence=ext.sentence_text,
                        explanation=(
                            f"Script sentence '{ext.sentence_text[:80]}...' cannot be grounded in any verified "
                            "EvidenceGraph claim node (similarity score below threshold 0.35)."
                        ),
                        recommended_edit=f"Ground assertion in evidence or remove from script: '{ext.sentence_text}'",
                    )
                )
            return drifts

        if graph is None or mapping.aligned_claim_id not in graph._nodes:
            return drifts

        claim_node = graph._nodes[mapping.aligned_claim_id]
        if not isinstance(claim_node, ClaimNode):
            return drifts

        claim_record = claim_node.claim_record

        # Check 1: Strengthened Claim
        self._check_strengthened_claim(ext, claim_node, claim_record, drifts)

        # Check 2: Altered Numbers & Compound Math
        self._check_altered_numbers(ext, claim_node, claim_record, drifts)

        # Check 3: Omitted Uncertainty & Hedging
        self._check_omitted_uncertainty(ext, claim_node, claim_record, drifts)

        # Check 4: Fabricated Quotes & Paraphrase Mandate
        self._check_fabricated_quotes(ext, claim_node, claim_record, graph, drifts)

        # Deduplicate drift records
        unique_drifts: List[ScriptClaimDriftRecord] = []
        seen_keys = set()
        for d in drifts:
            key = (d.drift_type, d.script_sentence, str(d.observed_value), str(d.expected_value))
            if key not in seen_keys:
                seen_keys.add(key)
                unique_drifts.append(d)
        return unique_drifts

    def _check_compound_growth_error(
        self,
        ext: ScriptSentenceExtraction,
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Checks for compound growth percentage arithmetic error in sentence text."""
        if any(d.drift_type == DriftType.ALTERED_NUMBER and "calculation error" in d.explanation.lower() for d in drifts):
            return

        growth_match = COMPOUND_GROWTH_PATTERN.search(ext.sentence_text)
        if growth_match:
            v_start = float(growth_match.group(1))
            v_end = float(growth_match.group(2))
            stated_pct = float(growth_match.group(3))
            if v_start > 0:
                calc_pct = ((v_end - v_start) / v_start) * 100.0
                if abs(stated_pct - calc_pct) > 0.5:
                    drifts.append(
                        ScriptClaimDriftRecord(
                            drift_type=DriftType.ALTERED_NUMBER,
                            severity=DriftSeverity.CRITICAL,
                            scene_id=ext.scene_id,
                            beat_id=ext.beat_id,
                            script_sentence=ext.sentence_text,
                            observed_value=f"{stated_pct}%",
                            expected_value=f"{calc_pct:.1f}%",
                            explanation=(
                                f"Mathematical calculation error: Growth from {v_start} to {v_end} is "
                                f"{calc_pct:.1f}%, but script asserts {stated_pct}%."
                            ),
                            recommended_edit=ext.sentence_text.replace(f"{stated_pct:.0f}%", f"{calc_pct:.0f}%").replace(f"{stated_pct}%", f"{calc_pct:.1f}%"),
                        )
                    )

    def _check_all_quotes_against_graph(
        self,
        ext: ScriptSentenceExtraction,
        graph: EvidenceGraph,
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Audits quotes in sentence against all direct quote claims in EvidenceGraph."""
        archival_candidates: List[str] = []
        for n in graph._nodes.values():
            if isinstance(n, ClaimNode):
                is_quote_claim = (
                    getattr(n, "claim_type", "") in ("direct_quote", ClaimType.DIRECT_QUOTE)
                    or "quote" in str(getattr(n, "category", "")).lower()
                    or (
                        hasattr(n, "claim_record")
                        and n.claim_record is not None
                        and getattr(n.claim_record, "claim_type", None) in ("direct_quote", ClaimType.DIRECT_QUOTE)
                    )
                )
                if is_quote_claim:
                    archival_candidates.append(n.claim_text)
            elif hasattr(n, "verbatim_text"):
                archival_candidates.append(getattr(n, "verbatim_text"))

        if not archival_candidates:
            return

        for q_script in ext.extracted_quotes:
            best_dist = float("inf")
            best_archive = ""
            for arch in archival_candidates:
                d = compute_normalized_levenshtein(q_script, arch)
                if d < best_dist:
                    best_dist = d
                    best_archive = arch

            has_ellipses = "..." in q_script or "…" in q_script
            if has_ellipses and best_dist <= 0.15:
                continue

            if best_dist > 0.02:
                # Strip quotation marks and replace dialogue verbs with indirect speech
                paraphrase = ext.sentence_text
                for q_mark in (f'"{q_script}"', f"'{q_script}'", f'“{q_script}”', f'‘{q_script}’'):
                    paraphrase = paraphrase.replace(q_mark, q_script)
                paraphrase = re.sub(r'\b(proclaimed|declared|said|shouted):\s*', "discussed ", paraphrase, flags=re.IGNORECASE)

                # Avoid duplicate drift record if already added
                if not any(d.drift_type == DriftType.FABRICATED_QUOTE for d in drifts):
                    drifts.append(
                        ScriptClaimDriftRecord(
                            drift_type=DriftType.FABRICATED_QUOTE,
                            severity=DriftSeverity.CRITICAL,
                            scene_id=ext.scene_id,
                            beat_id=ext.beat_id,
                            script_sentence=ext.sentence_text,
                            observed_value=q_script,
                            expected_value=best_archive[:120],
                            explanation=(
                                f"Quote fabrication/distortion: Quotation marks enclose '{q_script}', which diverges "
                                f"from archival evidence (normalized Levenshtein distance {best_dist:.3f} > 0.02). "
                                "Strict Paraphrase Mandate requires stripping quotation marks."
                            ),
                            recommended_edit=paraphrase,
                        )
                    )

    def _check_strengthened_claim(
        self,
        ext: ScriptSentenceExtraction,
        claim_node: ClaimNode,
        claim_record: Optional[ClaimRecord],
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Detects unearned modal escalation (Level 1/2 -> Level 3 or Level 1 -> Level 2)."""
        evidence_text = claim_node.claim_text
        ev_modal = 2
        if MODAL_LEVEL_1_PATTERN.search(evidence_text):
            ev_modal = 1
        elif MODAL_LEVEL_3_PATTERN.search(evidence_text):
            ev_modal = 3

        if ext.modal_level > ev_modal:
            if ev_modal == 1 and ext.modal_level == 3:
                severity = DriftSeverity.HIGH
                drift_type = DriftType.STRENGTHENED
                target_term = "suggests"
                desc = "hedged phrasing (Modal Level 1), but voiceover script asserts dogmatic certainty (Modal Level 3)"
            elif ev_modal == 2 and ext.modal_level == 3:
                severity = DriftSeverity.HIGH
                drift_type = DriftType.STRENGTHENED
                target_term = "typically"
                desc = "standard/moderate phrasing (Modal Level 2), but voiceover script asserts dogmatic certainty (Modal Level 3)"
            else:  # ev_modal == 1 and ext.modal_level == 2
                severity = DriftSeverity.MEDIUM
                drift_type = DriftType.OMITTED_UNCERTAINTY
                target_term = "suggests"
                desc = "hedged phrasing (Modal Level 1), but voiceover script asserts standard likelihood (Modal Level 2)"

            edit = ext.sentence_text
            terms_to_replace = MODAL_LEVEL_3_TERMS if ext.modal_level == 3 else MODAL_LEVEL_2_TERMS
            for term in terms_to_replace:
                edit = re.sub(rf'\b{re.escape(term)}\b', target_term, edit, flags=re.IGNORECASE)

            drifts.append(
                ScriptClaimDriftRecord(
                    drift_type=drift_type,
                    severity=severity,
                    scene_id=ext.scene_id,
                    beat_id=ext.beat_id,
                    script_sentence=ext.sentence_text,
                    evidence_claim_id=claim_node.claim_id,
                    evidence_text=claim_node.claim_text,
                    observed_value=f"Modal Level {ext.modal_level}",
                    expected_value=f"Modal Level {ev_modal}",
                    explanation=f"Unearned modal certainty jump: Evidence text uses {desc}.",
                    recommended_edit=edit,
                )
            )
        elif claim_node.confidence_score <= 0.70 and ext.modal_level == 3:
            if not any(d.drift_type == DriftType.STRENGTHENED for d in drifts):
                drifts.append(
                    ScriptClaimDriftRecord(
                        drift_type=DriftType.STRENGTHENED,
                        severity=DriftSeverity.MEDIUM,
                        scene_id=ext.scene_id,
                        beat_id=ext.beat_id,
                        script_sentence=ext.sentence_text,
                        evidence_claim_id=claim_node.claim_id,
                        evidence_text=claim_node.claim_text,
                        observed_value=f"Confidence {claim_node.confidence_score:.2f} asserted as absolute fact",
                        expected_value="Hedged framing (likely / preliminary)",
                        explanation="Low/moderate confidence claim (<=0.70) asserted with absolute certainty.",
                        recommended_edit=f"Calibrate sentence with qualifier: 'Evidence indicates {claim_node.claim_text.lower()}'.",
                    )
                )

    def _check_altered_numbers(
        self,
        ext: ScriptSentenceExtraction,
        claim_node: ClaimNode,
        claim_record: Optional[ClaimRecord],
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Audits numbers against dual tolerance (0.1% / 5.0%), compound growth, and 10x traps."""
        if not ext.extracted_numbers:
            return

        # Compare numbers to evidence text numbers
        ev_numbers = self._extract_numbers_from_text(claim_node.claim_text, False)
        if not ev_numbers:
            return

        matched_s_indices = set()
        matched_e_indices = set()

        # Pass 1: match identical or within-tolerance numbers
        for s_idx, (s_val, s_tok, is_approx) in enumerate(ext.extracted_numbers):
            tol = self.tolerance_approx if is_approx else self.tolerance_exact
            best_e_idx = None
            best_err = float("inf")
            for e_idx, (e_val, e_tok, _) in enumerate(ev_numbers):
                if e_idx in matched_e_indices:
                    continue
                err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)
                if err <= tol and err < best_err:
                    best_err = err
                    best_e_idx = e_idx
            if best_e_idx is not None:
                matched_s_indices.add(s_idx)
                matched_e_indices.add(best_e_idx)

        # Pass 2: match remaining numbers by log-distance (preventing auxiliary counts from matching years)
        unmatched_s = [i for i in range(len(ext.extracted_numbers)) if i not in matched_s_indices]
        unmatched_e = [j for j in range(len(ev_numbers)) if j not in matched_e_indices]

        for s_idx in unmatched_s:
            s_val, s_tok, is_approx = ext.extracted_numbers[s_idx]
            if not unmatched_e:
                break

            best_e_idx = None
            best_log_diff = float("inf")
            for e_idx in unmatched_e:
                e_val, e_tok, _ = ev_numbers[e_idx]
                if s_val > 0 and e_val > 0:
                    ld = abs(math.log10(s_val) - math.log10(e_val))
                else:
                    ld = abs(s_val - e_val)
                if ld < best_log_diff:
                    best_log_diff = ld
                    best_e_idx = e_idx

            # Only pair if magnitude gap is reasonably related (< 1.5 log-diff, i.e. <= ~30x)
            if best_e_idx is not None and best_log_diff < 1.5:
                e_val, e_tok, _ = ev_numbers[best_e_idx]
                matched_e_indices.add(best_e_idx)
                matched_s_indices.add(s_idx)
                unmatched_e.remove(best_e_idx)

                err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)

                # Order of magnitude check: 10x trap (log diff in [0.99, 1.49])
                if s_val > 0 and e_val > 0 and best_log_diff >= 0.99:
                    rec_edit = re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, ext.sentence_text)
                    drifts.append(
                        ScriptClaimDriftRecord(
                            drift_type=DriftType.ALTERED_NUMBER,
                            severity=DriftSeverity.CRITICAL,
                            scene_id=ext.scene_id,
                            beat_id=ext.beat_id,
                            script_sentence=ext.sentence_text,
                            evidence_claim_id=claim_node.claim_id,
                            evidence_text=claim_node.claim_text,
                            observed_value=s_val,
                            expected_value=e_val,
                            explanation=(
                                f"Order-of-magnitude numerical distortion (10x trap): Script states '{s_tok}' "
                                f"({s_val:g}), but evidence states '{e_tok}' ({e_val:g})."
                            ),
                            recommended_edit=rec_edit,
                        )
                    )
                    continue

                tol = self.tolerance_approx if is_approx else self.tolerance_exact
                if err > tol:
                    severity = DriftSeverity.HIGH if err > 0.10 else DriftSeverity.MEDIUM
                    rec_edit = re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, ext.sentence_text)
                    drifts.append(
                        ScriptClaimDriftRecord(
                            drift_type=DriftType.ALTERED_NUMBER,
                            severity=severity,
                            scene_id=ext.scene_id,
                            beat_id=ext.beat_id,
                            script_sentence=ext.sentence_text,
                            evidence_claim_id=claim_node.claim_id,
                            evidence_text=claim_node.claim_text,
                            observed_value=s_val,
                            expected_value=e_val,
                            explanation=(
                                f"Numerical value mutation: Script mentions '{s_tok}' ({s_val:g}), "
                                f"exceeding allowed tolerance ({tol:.1%}) from evidence '{e_tok}' ({e_val:g}). "
                                f"Relative delta: {err:.2%}."
                            ),
                            recommended_edit=rec_edit,
                        )
                    )

    def _check_omitted_uncertainty(
        self,
        ext: ScriptSentenceExtraction,
        claim_node: ClaimNode,
        claim_record: Optional[ClaimRecord],
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Enforces calibrated uncertainty hedging for contested or unverified claims."""
        consensus_raw = str(claim_node.consensus_state or "BROAD_CONSENSUS").upper()
        status_raw = str(claim_node.epistemic_status or "supported").lower()

        # Check if consensus requires hedging
        needs_hedging = False
        target_state: Optional[ConsensusState] = None

        if "ACTIVE_DEBATE" in consensus_raw:
            needs_hedging = True
            target_state = ConsensusState.ACTIVE_DEBATE
        elif "CONTESTED" in consensus_raw or status_raw == "contested":
            needs_hedging = True
            target_state = ConsensusState.CONTESTED
        elif "MINORITY_INTERPRETATION" in consensus_raw:
            needs_hedging = True
            target_state = ConsensusState.MINORITY_INTERPRETATION
        elif "UNRESOLVED" in consensus_raw or status_raw == "unresolved":
            needs_hedging = True
            target_state = ConsensusState.UNRESOLVED

        if needs_hedging and target_state in HISTORICAL_UNCERTAINTY_HEDGES:
            valid_hedges = HISTORICAL_UNCERTAINTY_HEDGES[target_state]
            lower_sentence = ext.sentence_text.lower()
            hedged = any(hedge in lower_sentence for hedge in valid_hedges)

            if not hedged:
                # Severity is CRITICAL if asserted as sole causal factor ("solely caused", "proves")
                is_dogmatic = any(d in lower_sentence for d in ["solely", "single-handedly", "only factor", "proven fact"])
                sev = DriftSeverity.CRITICAL if is_dogmatic else DriftSeverity.HIGH
                example_hedge = valid_hedges[0]

                drifts.append(
                    ScriptClaimDriftRecord(
                        drift_type=DriftType.OMITTED_UNCERTAINTY,
                        severity=sev,
                        scene_id=ext.scene_id,
                        beat_id=ext.beat_id,
                        script_sentence=ext.sentence_text,
                        evidence_claim_id=claim_node.claim_id,
                        evidence_text=claim_node.claim_text,
                        observed_value="Unhedged categorical statement",
                        expected_value=f"Calibrated framing for {target_state.value}",
                        explanation=(
                            f"Omitted historiographical/scientific uncertainty: Claim consensus state is "
                            f"'{target_state.value}', but script asserts the claim without mandatory hedging."
                        ),
                        recommended_edit=f"While debated, {example_hedge}: {ext.sentence_text}",
                    )
                )

    def _check_fabricated_quotes(
        self,
        ext: ScriptSentenceExtraction,
        claim_node: ClaimNode,
        claim_record: Optional[ClaimRecord],
        graph: EvidenceGraph,
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Enforces normalized Levenshtein <= 0.02 for verbatim quotes, triggering paraphrase mandate on failure."""
        if not ext.extracted_quotes:
            return
        if any(d.drift_type == DriftType.FABRICATED_QUOTE for d in drifts):
            return

        # Find archival text in claim or linked passage nodes
        archival_candidates: List[str] = [claim_node.claim_text]
        for edge in graph.get_incoming_edges(claim_node.node_id):
            source_n = graph._nodes.get(edge.source_id)
            if source_n and hasattr(source_n, "verbatim_text"):
                archival_candidates.append(getattr(source_n, "verbatim_text"))

        for q_script in ext.extracted_quotes:
            best_dist = float("inf")
            best_archive = ""
            for arch in archival_candidates:
                # Find best matching substring in archive
                d = compute_normalized_levenshtein(q_script, arch)
                if d < best_dist:
                    best_dist = d
                    best_archive = arch

            # Check ellipses exemption: d <= 0.15 with ellipses
            has_ellipses = "..." in q_script or "…" in q_script
            if has_ellipses and best_dist <= 0.15:
                continue

            if best_dist > 0.02:
                # Fabricated or distorted quote!
                # Generate paraphrase rewrite by stripping quotes and changing to indirect speech
                paraphrase = ext.sentence_text
                for q_mark in (f'"{q_script}"', f"'{q_script}'", f'“{q_script}”', f'‘{q_script}’'):
                    paraphrase = paraphrase.replace(q_mark, q_script)
                paraphrase = re.sub(r'\b(proclaimed|declared|said|shouted):\s*', "discussed ", paraphrase, flags=re.IGNORECASE)

                drifts.append(
                    ScriptClaimDriftRecord(
                        drift_type=DriftType.FABRICATED_QUOTE,
                        severity=DriftSeverity.CRITICAL,
                        scene_id=ext.scene_id,
                        beat_id=ext.beat_id,
                        script_sentence=ext.sentence_text,
                        evidence_claim_id=claim_node.claim_id,
                        observed_value=q_script,
                        expected_value=best_archive[:120],
                        explanation=(
                            f"Quote fabrication/distortion: Quotation marks enclose '{q_script}', which diverges "
                            f"from archival evidence (normalized Levenshtein distance {best_dist:.3f} > 0.02). "
                            "Strict Paraphrase Mandate requires stripping quotation marks."
                        ),
                        recommended_edit=paraphrase,
                    )
                )

    # -----------------------------------------------------------------------
    # 4. Primary Public Verification Entry Point
    # -----------------------------------------------------------------------
    def verify_script(
        self,
        script: Union[Script, Dict[str, Any], str, Any],
        graph: Optional[EvidenceGraph] = None,
        dossier: Optional[ResearchDossier] = None,
        auto_remediate: bool = True,
    ) -> ScriptVerificationReport:
        """End-to-end audit of script against EvidenceGraph, producing report and optional remediation."""
        start_time_ts = datetime.now(timezone.utc)
        extractions = self.extract_sentences(script)
        mappings = self.align_sentences_to_graph(extractions, graph)

        all_drifts: List[ScriptClaimDriftRecord] = []
        for ext, mapping in zip(extractions, mappings):
            drifts = self.check_drift(ext, mapping, graph)
            if drifts:
                mapping.has_drift = True
                mapping.drifts = drifts
                all_drifts.extend(drifts)

        # Tally counts
        drift_counts_by_type: Dict[str, int] = {}
        drift_counts_by_severity: Dict[str, int] = {}
        for d in all_drifts:
            drift_counts_by_type[d.drift_type.value] = drift_counts_by_type.get(d.drift_type.value, 0) + 1
            drift_counts_by_severity[d.severity.value] = drift_counts_by_severity.get(d.severity.value, 0) + 1

        # Gating recommendation
        has_critical = drift_counts_by_severity.get(DriftSeverity.CRITICAL.value, 0) > 0
        has_high = drift_counts_by_severity.get(DriftSeverity.HIGH.value, 0) > 0
        has_medium = drift_counts_by_severity.get(DriftSeverity.MEDIUM.value, 0) > 0
        has_low_or_info = (
            drift_counts_by_severity.get(DriftSeverity.LOW.value, 0) > 0 or
            drift_counts_by_severity.get(DriftSeverity.INFO.value, 0) > 0
        )

        if has_critical or has_high:
            verdict = "BLOCK"
            passed = False
        elif has_medium:
            verdict = "HUMAN_REVIEW"
            passed = False
        elif has_low_or_info:
            verdict = "WARN"
            passed = True
        else:
            verdict = "PASS"
            passed = True

        revised = self.remediate_script(script, all_drifts) if auto_remediate and all_drifts else None
        grounded_count = sum(1 for m in mappings if m.is_grounded)
        ungrounded_count = len(mappings) - grounded_count

        total_scenes = len(self._normalize_script_scenes(script))
        total_beats = sum(len(sc.get("beats", [])) for sc in self._normalize_script_scenes(script))

        elapsed_ms = (datetime.now(timezone.utc) - start_time_ts).total_seconds() * 1000.0

        report = ScriptVerificationReport(
            project_id=getattr(script, "project_id", None) if hasattr(script, "project_id") else None,
            topic=getattr(script, "topic", "") if hasattr(script, "topic") else "",
            total_scenes=total_scenes,
            total_beats=total_beats,
            total_sentences=len(extractions),
            grounded_sentences_count=grounded_count,
            ungrounded_sentences_count=ungrounded_count,
            drifts=all_drifts,
            drift_counts_by_type=drift_counts_by_type,
            drift_counts_by_severity=drift_counts_by_severity,
            mappings=mappings,
            passed=passed,
            gate_recommendation=verdict,
            summary=(
                f"Script verification verdict: {verdict}. Total sentences: {len(extractions)}. "
                f"Grounded: {grounded_count}, Ungrounded: {ungrounded_count}. Drifts identified: {len(all_drifts)}."
            ),
            revised_script=revised,
            graph_id=graph.graph_id if graph else "",
            duration_ms=elapsed_ms,
        )

        # Synchronize to EvidenceGraph if provided
        if graph is not None:
            self.sync_to_evidence_graph(report, graph)

        return report

    # -----------------------------------------------------------------------
    # 5. Auto-Remediation & EvidenceGraph Mutation
    # -----------------------------------------------------------------------
    def remediate_script(
        self,
        script: Union[Script, Dict[str, Any], str, Any],
        drifts: List[ScriptClaimDriftRecord],
    ) -> Any:
        """Applies recommended edits to script scenes and beats, returning a corrected copy."""
        if not drifts:
            return script

        # Build replacement mapping
        replacements: Dict[str, str] = {d.script_sentence: d.recommended_edit for d in drifts}

        # If string
        if isinstance(script, str):
            res = script
            for orig, rep in replacements.items():
                res = res.replace(orig, rep)
            return res

        # If Pydantic Script
        if isinstance(script, Script):
            new_scenes: List[ScriptScene] = []
            for sc in script.scenes:
                new_beats: List[ScriptBeat] = []
                for b in sc.beats:
                    cur_text = b.text
                    for orig, rep in replacements.items():
                        if orig in cur_text:
                            cur_text = cur_text.replace(orig, rep)
                    new_beats.append(b.model_copy(update={"text": cur_text}))
                new_sc_text = sc.narration_text
                for orig, rep in replacements.items():
                    if orig in new_sc_text:
                        new_sc_text = new_sc_text.replace(orig, rep)
                new_scenes.append(sc.model_copy(update={"beats": new_beats, "narration_text": new_sc_text}))
            return script.model_copy(update={"scenes": new_scenes})

        # Fallback for dicts or other script models
        return script

    def sync_to_evidence_graph(
        self,
        report: ScriptVerificationReport,
        graph: EvidenceGraph,
    ) -> None:
        """Mutatively inserts ScriptSentenceNode and VerificationTraceNode without creating cycles."""
        for m in report.mappings:
            hedging_applied = any(d.drift_type == DriftType.OMITTED_UNCERTAINTY for d in m.drifts)
            paraphrase_mandated = any(d.drift_type == DriftType.FABRICATED_QUOTE for d in m.drifts)

            grounded_cids = [m.aligned_claim_id] if m.aligned_claim_id else []

            # Add script sentence node
            try:
                sent_id = graph.add_script_sentence(
                    scene_id=m.scene_id,
                    beat_id=m.beat_id or f"{m.scene_id}_beat_1",
                    sentence_text=m.sentence_text,
                    start_time_seconds=m.start_time,
                    end_time_seconds=m.end_time,
                    grounded_claim_ids=grounded_cids,
                    hedging_applied=hedging_applied,
                    paraphrase_mandated=paraphrase_mandated,
                )

                # Add verification trace for this sentence
                graph.add_verification_trace(
                    target_node_id=sent_id,
                    strategy_used="SCRIPT_CLAIM_RE_VERIFICATION",
                    entailment_score=m.alignment_score if not m.has_drift else (m.alignment_score * 0.5),
                    status_assigned="verified" if not m.has_drift else "contested",
                    verifier_name=self.verifier_name,
                    audit_notes=f"Sentence audited. Drifts: {len(m.drifts)}",
                    warnings=[d.explanation for d in m.drifts],
                )
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Helper: Scene Normalization
    # -----------------------------------------------------------------------
    def _normalize_script_scenes(self, script: Any) -> List[Dict[str, Any]]:
        """Normalizes polymorphic script representations into standard dictionaries."""
        if isinstance(script, str):
            return [{
                "scene_id": "scene_1",
                "scene_index": 1,
                "narration_text": script,
                "beats": [{"beat_id": "scene_1_beat_1", "text": script, "start_time": 0.0, "duration": 10.0}]
            }]

        if hasattr(script, "scenes"):
            raw_scenes = script.scenes
        elif isinstance(script, dict) and "scenes" in script:
            raw_scenes = script["scenes"]
        else:
            raw_scenes = [script] if isinstance(script, dict) else []

        normalized = []
        for idx, sc in enumerate(raw_scenes, start=1):
            if isinstance(sc, dict):
                sc_id = sc.get("scene_id", f"scene_{idx}")
                beats = sc.get("beats", [])
                raw_beats = []
                for b_idx, b in enumerate(beats, start=1):
                    if isinstance(b, dict):
                        raw_beats.append(b)
                    elif hasattr(b, "text"):
                        raw_beats.append({
                            "beat_id": getattr(b, "beat_id", f"{sc_id}_beat_{b_idx}"),
                            "text": getattr(b, "text", ""),
                            "start_time": float(getattr(b, "start_time", 0.0) or 0.0),
                            "duration": float(getattr(b, "duration", 0.0) or 0.0),
                            "grounded_claim_ids": getattr(b, "grounded_claim_ids", []),
                        })
                normalized.append({
                    "scene_id": sc_id,
                    "scene_index": sc.get("scene_index", idx),
                    "narration_text": sc.get("narration_text") or sc.get("narration", ""),
                    "duration": sc.get("duration", 5.0),
                    "start_time": sc.get("start_time", 0.0),
                    "beats": raw_beats,
                })
            elif hasattr(sc, "scene_id"):
                sc_id = getattr(sc, "scene_id")
                beats = getattr(sc, "beats", [])
                raw_beats = []
                for b_idx, b in enumerate(beats, start=1):
                    raw_beats.append({
                        "beat_id": getattr(b, "beat_id", f"{sc_id}_beat_{b_idx}"),
                        "text": getattr(b, "text", ""),
                        "start_time": float(getattr(b, "start_time", 0.0) or 0.0),
                        "duration": float(getattr(b, "duration", 0.0) or 0.0),
                        "grounded_claim_ids": getattr(b, "grounded_claim_ids", []),
                    })
                normalized.append({
                    "scene_id": sc_id,
                    "scene_index": getattr(sc, "scene_index", idx),
                    "narration_text": getattr(sc, "narration_text", "") or getattr(sc, "narration", ""),
                    "duration": getattr(sc, "duration", 5.0),
                    "start_time": getattr(sc, "start_time", 0.0),
                    "beats": raw_beats,
                })
        return normalized


# ===========================================================================
# 4. Standalone Script Sentence Segmenter
# ===========================================================================

class ScriptSentenceSegmenter:
    """Dedicated sentence segmenter protecting abbreviations, decimals, and quotations."""

    def __init__(self, abbreviations: Optional[Set[str]] = None) -> None:
        self._verifier = ScriptVerifier(abbreviations=abbreviations)

    def segment_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """Segments text into discrete sentence spans while protecting abbreviations."""
        return self._verifier.segment_sentences(text)

    def extract_sentences(self, script: Any) -> List[ScriptSentenceExtraction]:
        """Extracts and annotates sentence units from raw text or Script objects."""
        return self._verifier.extract_sentences(script)


__all__ = [
    "DriftType",
    "DriftSeverity",
    "ScriptSentenceExtraction",
    "ScriptSentenceSegmenter",
    "ScriptClaimDriftRecord",
    "ScriptClaimMapping",
    "ScriptVerificationReport",
    "ScriptVerifier",
    "compute_normalized_levenshtein",
    "MODAL_LEVEL_3_TERMS",
    "MODAL_LEVEL_2_TERMS",
    "MODAL_LEVEL_1_TERMS",
    "APPROXIMATION_TERMS",
    "HISTORICAL_UNCERTAINTY_HEDGES",
]

