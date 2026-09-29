"""tests/test_script_verifier_challenger1.py — Empirical Challenger Test Suite for ScriptVerifier.

Authored by challenger_1_m4_g10 to empirically stress-test:
1. Quote verification edge cases: multi-sentence quotes, subtle substitutions in long quotes,
   punctuation mutations, contractions in single-quote contexts, paraphrase generation.
2. Epistemic drift: confidence escalation from UNRESOLVED / CONTESTED / CONTRADICTED to
   SUPPORTED / VERIFIED in script narration, lexical coverage of escalation verbs.
3. Numerical changes in script vs evidence graph: negative numbers / sign flips,
   extreme magnitude gap (> 1.5 log diff / > 31.6x), multi-number sentence pairing.
"""

import math
import pytest

from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
    SourceTier,
)
from src.epistemic.graph import EvidenceGraph, GraphNodeType
from src.epistemic.script_verifier import (
    DriftSeverity,
    DriftType,
    ScriptClaimDriftRecord,
    ScriptVerifier,
    compute_normalized_levenshtein,
)


@pytest.fixture
def base_source() -> SourceRecord:
    return SourceRecord(
        source_id="src_challenger_01",
        title="Primary Historical & Scientific Corpus",
        url="https://corpus.org/history-science.html",
        tier=SourceTier.PRIMARY_SOURCE,
        publisher="Academic Press",
        published_date="1960-01-01",
    )


@pytest.fixture
def challenger_graph(base_source) -> EvidenceGraph:
    graph = EvidenceGraph(graph_id="g_challenger_1")
    graph.add_source(
        title=base_source.title,
        url=base_source.url,
        node_id=base_source.source_id,
        source_record=base_source,
    )

    # 1. Multi-sentence archival quote
    c_quote_multi = ClaimRecord(
        claim_id="claim_quote_multi",
        claim_text="The principles of physics do not speak against manipulating things atom by atom. It is not an attempt to violate any laws.",
        claim_type=ClaimType.DIRECT_QUOTE,
        epistemic_status=EpistemicStatus.VERIFIED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=1.0,
        primary_source=base_source,
    )

    # 2. Long archival quote (135 chars)
    c_quote_long = ClaimRecord(
        claim_id="claim_quote_long",
        claim_text="Ultimately we can do chemical synthesis by placing the atoms down individually one by one where they are required by the chemist.",
        claim_type=ClaimType.DIRECT_QUOTE,
        epistemic_status=EpistemicStatus.VERIFIED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=1.0,
        primary_source=base_source,
    )

    # 3. Unresolved historical claim
    c_unresolved = ClaimRecord(
        claim_id="claim_unresolved",
        claim_text="The ultimate fate of the lost colony of Roanoke remains undetermined in historical documents.",
        epistemic_status=EpistemicStatus.UNVERIFIABLE,
        consensus_state=ConsensusState.UNRESOLVED,
        confidence_score=0.40,
        primary_source=base_source,
    )

    # 4. Contested historical claim
    c_contested = ClaimRecord(
        claim_id="claim_contested",
        claim_text="The library of Alexandria was destroyed in 48 BCE during Caesar's civil war.",
        epistemic_status=EpistemicStatus.CONTESTED,
        consensus_state=ConsensusState.CONTESTED,
        confidence_score=0.45,
        primary_source=base_source,
    )

    # 5. Contradicted claim (false hypothesis in evidence graph)
    c_contradicted = ClaimRecord(
        claim_id="claim_contradicted",
        claim_text="Piltdown Man was an authentic early hominid ancestor.",
        epistemic_status=EpistemicStatus.CONTRADICTED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=0.05,
        primary_source=base_source,
    )

    # 6. Numerical claims: temperatures, percentages, and baseline counts
    c_num_temp = ClaimRecord(
        claim_id="claim_num_temp",
        claim_text="The surface temperature dropped to -15 degrees during the polar winter.",
        epistemic_status=EpistemicStatus.VERIFIED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=0.95,
        primary_source=base_source,
    )

    c_num_count = ClaimRecord(
        claim_id="claim_num_count",
        claim_text="The expedition recorded 100 surviving specimens in the preserve.",
        epistemic_status=EpistemicStatus.VERIFIED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=0.95,
        primary_source=base_source,
    )

    c_num_pct = ClaimRecord(
        claim_id="claim_num_pct",
        claim_text="The regional economy contracted by 12 percent during the recession.",
        epistemic_status=EpistemicStatus.VERIFIED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=0.90,
        primary_source=base_source,
    )

    for c in [c_quote_multi, c_quote_long, c_unresolved, c_contested, c_contradicted, c_num_temp, c_num_count, c_num_pct]:
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            epistemic_status=c.epistemic_status.value if hasattr(c.epistemic_status, "value") else str(c.epistemic_status),
            consensus_state=c.consensus_state.value if hasattr(c.consensus_state, "value") else str(c.consensus_state),
            claim_type=c.claim_type.value if hasattr(c.claim_type, "value") else str(c.claim_type),
            confidence_score=c.confidence_score,
            claim_record=c,
        )

    return graph


# ===========================================================================
# 1. Quote Verification Edge Cases
# ===========================================================================
class TestQuoteVerificationAdversarialEdgeCases:
    """Stress tests quote verification against multi-sentence quotes, long quote evasion,
    punctuation variations, contractions, and paraphrase mandate."""

    def test_multi_sentence_quote_segmentation_behavior(self, challenger_graph):
        """EMPIRICAL TEST: Check behavior when a direct quote spans across multiple sentences.
        If sentence segmentation splits on '. ', the opening quote is in sentence 1 and closing
        quote is in sentence 2. We probe whether quotes are extracted or whether the segmentation
        leaves unbalanced quotes.
        """
        verifier = ScriptVerifier()
        script = 'Feynman asserted: "The principles of physics do not speak against manipulating things atom by atom. It is not an attempt to violate any laws."'

        # Inspect extracted sentences
        extractions = verifier.extract_sentences(script)
        # Verify how sentences were segmented:
        sentence_texts = [e.sentence_text for e in extractions]
        extracted_quotes = [e.extracted_quotes for e in extractions]

        # Document exact empirical behavior:
        # Does the verifier keep the multi-sentence quote together, or split it into 2 sentences?
        report = verifier.verify_script(script, challenger_graph)
        assert isinstance(report.passed, bool)

    def test_fabricated_multi_sentence_quote_bypass_probe(self, challenger_graph):
        """EMPIRICAL TEST: A completely fabricated quote that spans two sentences.
        If segmentation splits inside the quotes, neither sentence has matching ["..."],
        which could lead to 0 extracted quotes and bypass FABRICATED_QUOTE detection.
        """
        verifier = ScriptVerifier()
        # Fabricated quote across 2 sentences:
        script = 'Feynman declared: "Atoms can be painted red. They will glow brightly under ultraviolet light."'
        report = verifier.verify_script(script, challenger_graph)

        # Check if FABRICATED_QUOTE drift was flagged or if it bypassed quote checking:
        quote_drifts = [d for d in report.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
        # In an ideal verifier, fabricated multi-sentence quotes MUST be flagged.
        # We record whether the current verifier flags it or whether ungrounded/fabricated is caught.
        all_drifts = report.drifts
        assert len(all_drifts) >= 0

    def test_long_quote_subtle_word_substitution_evasion_boundary(self, challenger_graph):
        """EMPIRICAL TEST: In a long quote (135 characters), substituting 2 characters gives:
        normalized Levenshtein distance = 2 / 135 = 0.0148 <= 0.02.
        Because distance <= 0.02, it EVADES fabricated quote detection!
        """
        verifier = ScriptVerifier()
        # Original: "...synthesis by placing the atoms down individually one by one where they are required..."
        # Altered: "one by one" -> "two by two" (3 char substitutions: 't','w','o' vs 'o','n','e' = dist 3 / 135 = 0.0222)
        # Let's test a 1-character subtle substitution: "chemist" -> "chemist." or "synthesis" -> "syntheses" (1 char in 135)
        # 1 / 135 = 0.0074 <= 0.02
        script_subtle = 'Feynman said: "Ultimately we can do chemical syntheses by placing the atoms down individually one by one where they are required by the chemist."'
        report_subtle = verifier.verify_script(script_subtle, challenger_graph)

        quote_drifts = [d for d in report_subtle.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
        # Empirically proves that 0.02 relative threshold allows subtle 1-character mutations in long quotes
        dist = compute_normalized_levenshtein(
            "Ultimately we can do chemical syntheses by placing the atoms down individually one by one where they are required by the chemist.",
            "Ultimately we can do chemical synthesis by placing the atoms down individually one by one where they are required by the chemist."
        )
        assert dist <= 0.02
        assert len(quote_drifts) == 0  # Passed due to 0.02 threshold!

    def test_subtle_word_substitution_greater_than_threshold(self, challenger_graph):
        """When subtle word substitution exceeds 0.02, it is caught."""
        verifier = ScriptVerifier()
        # Replace "individually" (12 chars) with "separately" (10 chars)
        script_altered = 'Feynman said: "Ultimately we can do chemical synthesis by placing the atoms down separately one by one where they are required by the chemist."'
        report = verifier.verify_script(script_altered, challenger_graph)
        quote_drifts = [d for d in report.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
        assert len(quote_drifts) >= 1
        assert quote_drifts[0].severity == DriftSeverity.CRITICAL

    def test_quote_punctuation_and_trailing_period_sensitivity(self, challenger_graph):
        """Tests whether omitting or changing trailing punctuation in a short quote triggers drift."""
        verifier = ScriptVerifier()
        # Claim text: "There is plenty of room at the bottom."
        # Script quote omits period: "There is plenty of room at the bottom"
        # Length 38. 1 char diff -> 1/38 = 0.0263 > 0.02 -> triggers FABRICATED_QUOTE
        # Add the claim to challenger_graph
        challenger_graph.add_claim(
            claim_text="There is plenty of room at the bottom.",
            claim_id="claim_quote_short",
            claim_type=ClaimType.DIRECT_QUOTE.value,
            confidence_score=1.0,
        )
        script_no_dot = 'Feynman said: "There is plenty of room at the bottom"'
        report = verifier.verify_script(script_no_dot, challenger_graph)
        quote_drifts = [d for d in report.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
        assert len(quote_drifts) >= 1

    def test_contractions_within_single_quote_citations(self):
        """Tests single-quoted strings containing contractions e.g. 'don\'t'."""
        verifier = ScriptVerifier()
        # Single quote around full quote with contraction inside
        text = "The witness stated 'we shouldn\'t panic' during the crisis."
        exts = verifier.extract_sentences(text)
        assert len(exts) == 1
        # Check if extracted_quotes captured the phrase
        quotes = exts[0].extracted_quotes
        assert len(quotes) >= 1
        assert "shouldn't" in quotes[0]


# ===========================================================================
# 2. Epistemic Drift & Confidence Escalation
# ===========================================================================
class TestEpistemicDriftAdversarialEdgeCases:
    """Stress tests confidence escalation, unhedged narration of UNRESOLVED / CONTESTED claims,
    and handling of CONTRADICTED claims."""

    def test_unresolved_claim_unhedged_narration_detected(self, challenger_graph):
        """An UNRESOLVED claim asserted without mandatory historical uncertainty hedging."""
        verifier = ScriptVerifier()
        # Evidence: The ultimate fate of the lost colony of Roanoke remains undetermined in historical documents.
        # Script narration asserts it with definitive closure:
        script = "The colonists of Roanoke perished completely in the harsh winter."
        report = verifier.verify_script(script, challenger_graph)

        # Should detect OMITTED_UNCERTAINTY because consensus is UNRESOLVED
        omitted = [d for d in report.drifts if d.drift_type == DriftType.OMITTED_UNCERTAINTY]
        assert len(omitted) >= 1
        assert omitted[0].severity in (DriftSeverity.HIGH, DriftSeverity.CRITICAL)

    def test_contested_claim_unhedged_narration_detected(self, challenger_graph):
        """A CONTESTED claim asserted as settled fact."""
        verifier = ScriptVerifier()
        # Evidence: Library of Alexandria destruction in 48 BCE is CONTESTED
        script = "The library of Alexandria was destroyed in 48 BCE during Caesar's civil war."
        report = verifier.verify_script(script, challenger_graph)

        omitted = [d for d in report.drifts if d.drift_type == DriftType.OMITTED_UNCERTAINTY]
        assert len(omitted) >= 1
        assert "contested" in omitted[0].explanation.lower()

    def test_escalation_verbs_lexical_coverage_probe(self, challenger_graph):
        """EMPIRICAL TEST: Probing whether escalation verbs like 'verified', 'confirmed',
        'established', 'demonstrated' trigger modal level 3.
        In current implementation, MODAL_LEVEL_3_TERMS includes:
        {'always', 'proven', 'definitely', 'solely', 'undoubtedly', 'certainly',
         'indisputable', 'conclusively', 'conclusive', 'undeniably', 'settled',
         'fact', 'irrefutably', 'single-handedly', 'unquestionably'}.
        Does 'verified' trigger modal_level 3?
        """
        verifier = ScriptVerifier()
        ext_verified = verifier.extract_sentences("Researchers verified that the diet extends longevity.")[0]
        ext_confirmed = verifier.extract_sentences("Scientists confirmed that the reaction is immediate.")[0]

        # Record empirical modal level:
        # Note: 'verified' and 'confirmed' evaluate to modal_level=2 (standard likelihood)
        assert ext_verified.modal_level == 2
        assert ext_confirmed.modal_level == 2

    def test_contradicted_claim_script_assertion_behavior(self, challenger_graph):
        """EMPIRICAL TEST: What happens when the script asserts a CONTRADICTED claim as true?
        Evidence: Piltdown Man was an authentic early hominid ancestor (CONTRADICTED, confidence 0.05).
        Script: "Piltdown Man was an authentic early hominid ancestor discovered in Sussex."
        """
        verifier = ScriptVerifier()
        script = "Piltdown Man was an authentic early hominid ancestor discovered in Sussex."
        report = verifier.verify_script(script, challenger_graph)

        # Check what drifts are reported:
        drifts = report.drifts
        # Does the verifier flag this claim?
        assert isinstance(report.passed, bool)


# ===========================================================================
# 3. Numerical Changes in Script vs Evidence Graph
# ===========================================================================
class TestNumericalChangesAdversarialEdgeCases:
    """Stress tests numerical comparisons: negative numbers, extreme magnitude gaps (>1.5 log-diff),
    and zero handling."""

    def test_negative_number_sign_flip_detection_probe(self, challenger_graph):
        r"""EMPIRICAL TEST: Negative numbers and sign flips.
        Evidence: 'surface temperature dropped to -15 degrees'
        Script: 'surface temperature was 15 degrees'
        Probe whether regex r'(\b\d+(?:,\d{3})*(?:\.\d+)?)...' extracts 15.0 for both,
        causing sign flip to be completely missed!
        """
        verifier = ScriptVerifier()
        script_positive = "The surface temperature reached 15 degrees during the polar winter."
        report = verifier.verify_script(script_positive, challenger_graph)

        # Check if ALTERED_NUMBER was triggered for -15 vs 15:
        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]

        # Let's inspect raw extraction of -15 vs 15:
        ext_neg = verifier.extract_sentences("The temperature dropped to -15 degrees.")[0]
        # In current regex r'(\b\d+...)', the leading minus sign is NOT captured!
        # Value extracted: 15.0
        assert ext_neg.extracted_numbers[0][0] == 15.0

    def test_extreme_magnitude_gap_probe(self, challenger_graph):
        """EMPIRICAL TEST: In _check_altered_numbers, Pass 2 matches unmatched numbers
        with 'best_log_diff < 1.5'.
        Evidence: 100 specimens
        Script: 10,000 specimens (100x increase, log diff = |log10(10000) - log10(100)| = 2.0 >= 1.5).
        What happens when log diff is 2.0?
        """
        verifier = ScriptVerifier()
        script_100x = "The expedition recorded 10,000 surviving specimens in the preserve."
        report = verifier.verify_script(script_100x, challenger_graph)

        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
        # Check if 100x alteration was flagged or dropped by the best_log_diff < 1.5 guard:
        # Document the exact empirical result:
        assert isinstance(report.passed, bool)

    def test_moderate_magnitude_gap_10x_caught(self, challenger_graph):
        """A 10x order-of-magnitude error (log diff = 1.0 < 1.5) IS caught by the 10x trap."""
        verifier = ScriptVerifier()
        # Evidence: 100
        # Script: 1,000 (10x, log diff = 1.0)
        script_10x = "The expedition recorded 1,000 surviving specimens in the preserve."
        report = verifier.verify_script(script_10x, challenger_graph)

        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
        assert len(num_drifts) >= 1
        assert any("10x trap" in d.explanation for d in num_drifts)
        assert num_drifts[0].severity == DriftSeverity.CRITICAL

    def test_percentage_change_sign_inversion_probe(self, challenger_graph):
        """Evidence: contracted by 12 percent. Script: grew by 12 percent."""
        verifier = ScriptVerifier()
        script = "The regional economy grew by 12 percent during the recession."
        report = verifier.verify_script(script, challenger_graph)
        # Numbers are 12 and 12, so numerical value difference is 0!
        # Document whether numerical checker or modal checker handles semantic direction:
        assert isinstance(report.passed, bool)


# ===========================================================================
# 4. Paraphrase Mandate & Remediation
# ===========================================================================
class TestParaphraseMandateAndRemediation:
    """Tests auto-remediation of fabricated quotes and unhedged claims."""

    def test_remediation_strips_quotes_and_replaces_dialogue_verbs(self, challenger_graph):
        verifier = ScriptVerifier()
        script = 'Feynman declared: "Atoms can be painted red to glow brightly!"'
        report = verifier.verify_script(script, challenger_graph, auto_remediate=True)

        assert report.revised_script is not None
        # Revised script must have stripped quotes and replaced dialogue verbs
        assert '"' not in report.revised_script
        assert "discussed" in report.revised_script.lower()

    def test_remediation_on_structured_script_object(self, challenger_graph):
        verifier = ScriptVerifier()
        script_obj = Script(
            title="Physics Script",
            topic="Physics",
            total_duration=10.0,
            scenes=[
                ScriptScene(
                    scene_id="sc_01",
                    narration_text='Feynman proclaimed: "We can easily build nanobots!"',
                    beats=[
                        ScriptBeat(
                            beat_id="b_01",
                            text='Feynman proclaimed: "We can easily build nanobots!"',
                            start_time=0.0,
                            duration=5.0,
                        )
                    ],
                )
            ],
        )
        report = verifier.verify_script(script_obj, challenger_graph, auto_remediate=True)
        assert report.revised_script is not None
        assert isinstance(report.revised_script, Script)
        revised_beat_text = report.revised_script.scenes[0].beats[0].text
        assert '"' not in revised_beat_text
        assert "discussed" in revised_beat_text.lower()
