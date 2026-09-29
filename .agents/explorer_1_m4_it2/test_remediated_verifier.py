import sys
import os
import re
import math
from typing import List, Dict, Any, Tuple, Optional, Union

sys.path.insert(0, os.path.abspath("."))

from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    SourceRecord,
    SourceTier,
)
from src.epistemic.graph import (
    ClaimNode,
    EvidenceGraph,
)
from src.epistemic.script_verifier import (
    DriftSeverity,
    DriftType,
    ScriptClaimDriftRecord,
    ScriptClaimMapping,
    ScriptSentenceExtraction,
    ScriptVerificationReport,
    ScriptVerifier,
    MODAL_LEVEL_3_TERMS,
    MODAL_LEVEL_2_TERMS,
    MODAL_LEVEL_1_TERMS,
    APPROXIMATION_TERMS,
    HISTORICAL_UNCERTAINTY_HEDGES,
    compute_normalized_levenshtein,
)

# Compile regex patterns
MODAL_LEVEL_3_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_3_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
MODAL_LEVEL_2_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_2_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
MODAL_LEVEL_1_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_1_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
APPROXIMATION_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(APPROXIMATION_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
COMPOUND_GROWTH_PATTERN = re.compile(
    r'(?:grew|increased|rose|surged|jumped|climbed)\s+from\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?\s+to\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?(?:,\s*|\s+)(?:a|an|\(a|\(an)?\s*(?:increase\s+of\s+|growth\s+of\s+|up\s+)?(\d+(?:\.\d+)?)%\s*(?:increase|growth)?\)?',
    re.IGNORECASE
)

class RemediatedScriptVerifier(ScriptVerifier):
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

        # Rhetorical check
        lower = sentence_text.lower()
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

    def _check_compound_growth_error(
        self,
        ext: ScriptSentenceExtraction,
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
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
        archival_candidates: List[str] = []
        for n in graph._nodes.values():
            if isinstance(n, ClaimNode):
                is_quote = (
                    getattr(n, "claim_type", "") in ("direct_quote", ClaimType.DIRECT_QUOTE)
                    or "quote" in str(getattr(n, "category", "")).lower()
                    or (
                        hasattr(n, "claim_record")
                        and n.claim_record is not None
                        and getattr(n.claim_record, "claim_type", None) in ("direct_quote", ClaimType.DIRECT_QUOTE)
                    )
                )
                if is_quote:
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
                paraphrase = ext.sentence_text
                for q_mark in (f'"{q_script}"', f"'{q_script}'", f'“{q_script}”', f'‘{q_script}’'):
                    paraphrase = paraphrase.replace(q_mark, q_script)
                paraphrase = re.sub(r'\b(proclaimed|declared|said|shouted):\s*', "discussed ", paraphrase, flags=re.IGNORECASE)

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
        evidence_text = claim_node.claim_text
        ev_modal = 2
        if MODAL_LEVEL_1_PATTERN.search(evidence_text):
            ev_modal = 1
        elif MODAL_LEVEL_3_PATTERN.search(evidence_text):
            ev_modal = 3

        if ext.modal_level > ev_modal:
            if ev_modal == 1 and ext.modal_level == 3:
                severity = DriftSeverity.HIGH
                target_term = "suggests"
                desc = "hedged phrasing (Modal Level 1), but voiceover script asserts dogmatic certainty (Modal Level 3)"
            elif ev_modal == 2 and ext.modal_level == 3:
                severity = DriftSeverity.HIGH
                target_term = "typically"
                desc = "standard/moderate phrasing (Modal Level 2), but voiceover script asserts dogmatic certainty (Modal Level 3)"
            else:  # ev_modal == 1 and ext.modal_level == 2
                severity = DriftSeverity.MEDIUM
                target_term = "suggests"
                desc = "hedged phrasing (Modal Level 1), but voiceover script asserts standard likelihood (Modal Level 2)"

            edit = ext.sentence_text
            terms_to_replace = MODAL_LEVEL_3_TERMS if ext.modal_level == 3 else MODAL_LEVEL_2_TERMS
            for term in terms_to_replace:
                edit = re.sub(rf'\b{re.escape(term)}\b', target_term, edit, flags=re.IGNORECASE)

            drifts.append(
                ScriptClaimDriftRecord(
                    drift_type=DriftType.STRENGTHENED,
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
        if not ext.extracted_numbers:
            return

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

        # Pass 2: match remaining numbers by log-distance
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

            if best_e_idx is not None and best_log_diff < 1.5:
                e_val, e_tok, _ = ev_numbers[best_e_idx]
                matched_e_indices.add(best_e_idx)
                matched_s_indices.add(s_idx)
                unmatched_e.remove(best_e_idx)

                err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)

                # Order of magnitude check: 10x trap (log diff >= 0.99)
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

    def _check_fabricated_quotes(
        self,
        ext: ScriptSentenceExtraction,
        claim_node: ClaimNode,
        claim_record: Optional[ClaimRecord],
        graph: EvidenceGraph,
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        # If quote was already audited and added or matched against graph, do not duplicate
        if any(d.drift_type == DriftType.FABRICATED_QUOTE for d in drifts):
            return
        super()._check_fabricated_quotes(ext, claim_node, claim_record, graph, drifts)

    def check_drift(
        self,
        ext: ScriptSentenceExtraction,
        mapping: ScriptClaimMapping,
        graph: Optional[EvidenceGraph] = None,
    ) -> List[ScriptClaimDriftRecord]:
        raw_drifts = super().check_drift(ext, mapping, graph)
        # Deduplicate
        deduped = []
        seen = set()
        for d in raw_drifts:
            k = (d.drift_type, d.script_sentence, str(d.observed_value), str(d.expected_value))
            if k not in seen:
                seen.add(k)
                deduped.append(d)
        return deduped

# Let's run all tests against RemediatedScriptVerifier!
src = SourceRecord(source_id="s1", title="t", url="u", tier=SourceTier.PRIMARY_SOURCE)
g = EvidenceGraph(graph_id="g")

c_thermal = ClaimRecord(claim_id="c1", claim_text="Silicon transistors typically exhibit higher thermal stability.", confidence_score=0.85, primary_source=src)
g.add_claim(claim_text=c_thermal.claim_text, claim_id=c_thermal.claim_id, confidence_score=c_thermal.confidence_score, claim_record=c_thermal)

c_quote = ClaimRecord(claim_id="c_quote", claim_text="There is plenty of room at the bottom.", claim_type=ClaimType.DIRECT_QUOTE, primary_source=src)
g.add_claim(claim_text=c_quote.claim_text, claim_id=c_quote.claim_id, claim_type=c_quote.claim_type.value, claim_record=c_quote)

c_bell = ClaimRecord(claim_id="c_bell", claim_text="Bell Labs produced 4,980 prototype units in 1948.", confidence_score=0.85, primary_source=src)
g.add_claim(claim_text=c_bell.claim_text, claim_id=c_bell.claim_id, confidence_score=c_bell.confidence_score, claim_record=c_bell)

v = RemediatedScriptVerifier()

# 1. Contraction check
r1 = v.verify_script("It's clear that the company's product was innovative in every way.", g)
print("1. Contraction test drifts:", len(r1.drifts), "passed:", r1.passed)
assert not any(d.drift_type == DriftType.FABRICATED_QUOTE for d in r1.drifts)

# 2. Level 2 -> Level 3 escalation
r2 = v.verify_script("Silicon transistors undeniably prove higher thermal stability.", g)
print("2. Level 2 -> Level 3 test drifts:", [d.drift_type for d in r2.drifts], "passed:", r2.passed)
assert any(d.drift_type == DriftType.STRENGTHENED for d in r2.drifts)
assert r2.passed is False

# 3. Substring factory
exts = v.extract_sentences("The factory produced goods in June.")
print("3. Modal level of factory:", exts[0].modal_level)
assert exts[0].modal_level == 2

# 4. Fabricated quote duplicate check
q = chr(34)
r4 = v.verify_script(f"Feynman said: {q}There is barely any room at the bottom.{q}", g)
quote_drifts = [d for d in r4.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
print("4. Fabricated quote drifts count:", len(quote_drifts))
assert len(quote_drifts) == 1

# 5. Auxiliary count 3 engineers vs 1948
r5 = v.verify_script("In 1948, 3 engineers at Bell Labs produced 4,980 prototype units.", g)
num_drifts5 = [d for d in r5.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
print("5. 3 engineers number drifts count:", len(num_drifts5))
assert len(num_drifts5) == 0

# 6. Compound growth alternate phrasings
for phrase in [
    "Revenue grew from 10 million to 30 million, a 300% increase.",
    "Sales increased from 10 to 30, an increase of 300%.",
    "Output rose from 10 to 30 (a 300% increase).",
    "Volume surged from 10 to 30, up 300%."
]:
    r6 = v.verify_script(phrase, g)
    assert any(d.drift_type == DriftType.ALTERED_NUMBER and "calculation error" in d.explanation.lower() for d in r6.drifts), f"Failed for {phrase}"
print("6. All compound growth phrasings caught!")

# 7. Exact quote passes without "room"
c_lincoln = ClaimRecord(
    claim_id="c_lincoln",
    claim_text="Four score and seven years ago our fathers brought forth on this continent a new nation.",
    claim_type=ClaimType.DIRECT_QUOTE,
    primary_source=src
)
g.add_claim(claim_text=c_lincoln.claim_text, claim_id=c_lincoln.claim_id, claim_type=c_lincoln.claim_type.value, claim_record=c_lincoln)
r7 = v.verify_script('Lincoln said: "Four score and seven years ago our fathers brought forth on this continent a new nation."', g)
assert len([d for d in r7.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]) == 0
print("7. Lincoln quote without 'room' in claim text correctly identified as archival candidate and passes!")

print("\n>>> ALL 7 REMEDIATION VERIFICATION TESTS PASSED PERFECTLY! <<<")
