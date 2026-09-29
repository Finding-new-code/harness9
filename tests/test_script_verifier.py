"""tests/test_script_verifier.py — Test Suite for Post-Script Claim Re-Verification Engine.

Tests sentence segmentation with abbreviation/quote protection, bipartite alignment,
forensic drift detection (strengthened claims, altered numbers, omitted uncertainty,
fabricated quotes with Paraphrase Mandate), script remediation, and EvidenceGraph sync.
"""

import pytest
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    QuoteExactness,
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
    ScriptClaimMapping,
    ScriptSentenceExtraction,
    ScriptSentenceSegmenter,
    ScriptVerificationReport,
    ScriptVerifier,
)


@pytest.fixture
def sample_source() -> SourceRecord:
    return SourceRecord(
        source_id="src_feynman_01",
        title="Plenty of Room at the Bottom",
        url="https://caltech.edu/feynman/room.html",
        tier=SourceTier.PRIMARY_SOURCE,
        publisher="Caltech",
        published_date="1959-12-29",
    )


@pytest.fixture
def sample_graph(sample_source) -> EvidenceGraph:
    graph = EvidenceGraph(graph_id="g_test_script")
    graph.add_source(
        title=sample_source.title,
        url=sample_source.url,
        node_id=sample_source.source_id,
        source_record=sample_source,
    )

    # Claim 1: Hedged claim (Modal 1)
    c1 = ClaimRecord(
        claim_id="claim_diet_longevity",
        claim_text="Recent findings suggest a potential link between diet and longevity.",
        epistemic_status=EpistemicStatus.SUPPORTED,
        consensus_state=ConsensusState.BROAD_CONSENSUS,
        confidence_score=0.65,
        primary_source=sample_source,
    )

    # Claim 2: Quantitative casualty claim
    c2 = ClaimRecord(
        claim_id="claim_battle_casualties",
        claim_text="Historical archives record 50,000 casualties during the siege.",
        epistemic_status=EpistemicStatus.VERIFIED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=0.95,
        primary_source=sample_source,
    )

    # Claim 3: Approximate production count
    c3 = ClaimRecord(
        claim_id="claim_production_count",
        claim_text="Bell Labs produced 4,980 prototype units in 1948.",
        epistemic_status=EpistemicStatus.SUPPORTED,
        consensus_state=ConsensusState.BROAD_CONSENSUS,
        confidence_score=0.85,
        primary_source=sample_source,
    )

    # Claim 4: Active debate consensus
    c4 = ClaimRecord(
        claim_id="claim_bronze_age",
        claim_text="Causes of the Bronze Age collapse include climatic shifts and Sea Peoples raids.",
        epistemic_status=EpistemicStatus.CONTESTED,
        consensus_state=ConsensusState.ACTIVE_DEBATE,
        confidence_score=0.55,
        primary_source=sample_source,
    )

    # Claim 5: Primary quote
    c5 = ClaimRecord(
        claim_id="claim_feynman_quote",
        claim_text="There is plenty of room at the bottom.",
        claim_type=ClaimType.DIRECT_QUOTE,
        epistemic_status=EpistemicStatus.VERIFIED,
        consensus_state=ConsensusState.STRONG_CONSENSUS,
        confidence_score=1.0,
        primary_source=sample_source,
    )

    for c in [c1, c2, c3, c4, c5]:
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


class TestSentenceSegmentation:
    """Tests abbreviation, quote, and decimal protection in sentence segmentation."""

    def test_segmentation_with_abbreviations_and_numbers(self):
        verifier = ScriptVerifier()
        text = "Dr. Shockley developed the junction transistor at Bell Labs in the U.S. for $3.5M."
        spans = verifier.segment_sentences(text)
        assert len(spans) == 1
        assert spans[0][0] == text

    def test_segmentation_with_quotation_boundaries(self):
        verifier = ScriptVerifier()
        text = "He shouted 'Stop!' and ran."
        spans = verifier.segment_sentences(text)
        assert len(spans) == 1
        assert spans[0][0] == text

    def test_segmentation_multi_sentence_dialogue(self):
        verifier = ScriptVerifier()
        text = "The prototype was tested. 'It works,' said Bardeen. Production began immediately."
        spans = verifier.segment_sentences(text)
        assert len(spans) == 3
        assert spans[0][0] == "The prototype was tested."
        assert spans[1][0] == "'It works,' said Bardeen."
        assert spans[2][0] == "Production began immediately."

    def test_script_sentence_segmenter_export_and_custom_abbreviations(self):
        segmenter = ScriptSentenceSegmenter(abbreviations={"prof."})
        text = "Prof. Turing arrived at the lab. He began work."
        spans = segmenter.segment_sentences(text)
        assert len(spans) == 2
        assert spans[0][0] == "Prof. Turing arrived at the lab."
        assert spans[1][0] == "He began work."


class TestStrengthenedClaimDetection:
    """Tests modal level escalation (Level 1/2 -> Level 3)."""

    def test_detect_modal_level_3_escalation_from_level_1(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = "Scientists have definitely proven that diet always cures aging."
        report = verifier.verify_script(script_text, sample_graph)

        assert report.passed is False
        assert report.gate_recommendation == "BLOCK"
        strengthened_drifts = [d for d in report.drifts if d.drift_type == DriftType.STRENGTHENED]
        assert len(strengthened_drifts) >= 1
        assert strengthened_drifts[0].severity in (DriftSeverity.HIGH, DriftSeverity.CRITICAL)
        assert "suggests" in strengthened_drifts[0].recommended_edit.lower()

    def test_detect_modal_escalation_level_1_to_2(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = "Recent findings generally confirm that diet typically extends longevity."
        report = verifier.verify_script(script_text, sample_graph)

        escalation_drifts = [d for d in report.drifts if d.observed_value == "Modal Level 2" and d.expected_value == "Modal Level 1"]
        assert len(escalation_drifts) >= 1
        assert escalation_drifts[0].severity == DriftSeverity.MEDIUM
        assert escalation_drifts[0].drift_type == DriftType.OMITTED_UNCERTAINTY
        assert "suggests" in escalation_drifts[0].recommended_edit.lower()

    def test_conserve_appropriate_modal_level_2(self, sample_source):
        graph = EvidenceGraph(graph_id="g_test_modal2")
        c = ClaimRecord(
            claim_id="claim_thermal",
            claim_text="Silicon transistors typically exhibit higher thermal stability.",
            confidence_score=0.85,
            primary_source=sample_source,
        )
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            confidence_score=c.confidence_score,
            claim_record=c,
        )
        verifier = ScriptVerifier()
        script_text = "Silicon transistors generally offer greater thermal stability."
        report = verifier.verify_script(script_text, graph)

        strengthened_drifts = [d for d in report.drifts if d.drift_type == DriftType.STRENGTHENED]
        assert len(strengthened_drifts) == 0


class TestAlteredNumberDetection:
    """Tests dual tolerance, order-of-magnitude 10x traps, and compound math."""

    def test_detect_tenfold_order_of_magnitude_drift(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = "During the siege, over 500,000 soldiers perished in the battle."
        report = verifier.verify_script(script_text, sample_graph)

        assert report.passed is False
        assert report.gate_recommendation == "BLOCK"
        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
        assert len(num_drifts) >= 1
        assert num_drifts[0].severity == DriftSeverity.CRITICAL
        assert "10x" in num_drifts[0].explanation or "order-of-magnitude" in num_drifts[0].explanation.lower()

    def test_approximate_qualifier_tolerance_window(self, sample_graph):
        verifier = ScriptVerifier()
        # Evidence is 4,980. Script is "approximately 5,000" -> 0.4% error <= 5.0% approx tolerance
        script_text = "Bell Labs produced approximately 5,000 units in 1948."
        report = verifier.verify_script(script_text, sample_graph)

        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
        assert len(num_drifts) == 0

    def test_exact_tolerance_window_violation(self, sample_graph):
        verifier = ScriptVerifier()
        # Evidence is 4,980. Script is "exactly 5,000" -> 0.4% error > 0.1% exact tolerance
        script_text = "Bell Labs produced exactly 5,000 units in 1948."
        report = verifier.verify_script(script_text, sample_graph)

        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
        assert len(num_drifts) >= 1

    def test_detect_compound_growth_calculation_error(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = "Revenue grew from 10 million to 30 million, a 300% increase."
        report = verifier.verify_script(script_text, sample_graph)

        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
        assert any(d.severity == DriftSeverity.CRITICAL for d in num_drifts)
        assert any("200" in d.recommended_edit for d in num_drifts)


class TestOmittedUncertaintyDetection:
    """Tests hedging enforcement for ACTIVE_DEBATE and CONTESTED consensus states."""

    def test_detect_omitted_uncertainty_in_active_debate(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = "The collapse of Bronze Age civilizations was solely caused by the Sea Peoples."
        report = verifier.verify_script(script_text, sample_graph)

        assert report.passed is False
        unc_drifts = [d for d in report.drifts if d.drift_type == DriftType.OMITTED_UNCERTAINTY]
        assert len(unc_drifts) >= 1
        assert unc_drifts[0].severity == DriftSeverity.CRITICAL

    def test_calibrated_uncertainty_passes(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = "While debated, historians remain divided over the multi-causal Bronze Age collapse."
        report = verifier.verify_script(script_text, sample_graph)

        unc_drifts = [d for d in report.drifts if d.drift_type == DriftType.OMITTED_UNCERTAINTY]
        assert len(unc_drifts) == 0


class TestFabricatedQuoteDetection:
    """Tests exact Levenshtein quote matching, ellipses, and the strict Paraphrase Mandate."""

    def test_exact_verbatim_quote_passes(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = 'Feynman famously said: "There is plenty of room at the bottom."'
        report = verifier.verify_script(script_text, sample_graph)

        quote_drifts = [d for d in report.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
        assert len(quote_drifts) == 0

    def test_fabricated_quote_triggers_paraphrase_mandate(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = 'Feynman famously proclaimed: "We can easily shrink machines to the atomic scale!"'
        report = verifier.verify_script(script_text, sample_graph)

        assert report.passed is False
        quote_drifts = [d for d in report.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
        assert len(quote_drifts) >= 1
        assert quote_drifts[0].severity == DriftSeverity.CRITICAL
        # Paraphrase mandate: quotation marks MUST be stripped in recommended edit
        assert '"' not in quote_drifts[0].recommended_edit
        assert "discussed" in quote_drifts[0].recommended_edit.lower()


class TestScriptRemediationAndGraphSync:
    """Tests auto-remediation and EvidenceGraph DAG synchronization."""

    def test_remediation_and_graph_synchronization(self, sample_graph):
        verifier = ScriptVerifier()
        script = Script(
            title="Physics Wonders",
            topic="Physics",
            total_duration=10.0,
            scenes=[
                ScriptScene(
                    scene_id="sc_1",
                    narration_text='Feynman famously proclaimed: "We can easily shrink machines to the atomic scale!"',
                    beats=[
                        ScriptBeat(
                            beat_id="sc_1_beat_1",
                            text='Feynman famously proclaimed: "We can easily shrink machines to the atomic scale!"',
                            start_time=0.0,
                            duration=5.0,
                        )
                    ],
                )
            ],
        )
        report = verifier.verify_script(script, sample_graph, auto_remediate=True)
        assert report.revised_script is not None

        # Check DAG node insertion
        sentence_nodes = [
            n for n in sample_graph._nodes.values() if n.node_type == GraphNodeType.SCRIPT_SENTENCE
        ]
        assert len(sentence_nodes) >= 1
        assert sentence_nodes[0].paraphrase_mandated is True


class TestRemediationIteration2Features:
    """Tests remediation enhancements from Iteration 2 (contractions, modal matrix, auxiliary numbers, segmenter export)."""

    def test_contraction_and_possessive_apostrophes_not_treated_as_quotes(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = "It's clear that the company's product was innovative in every way."
        report = verifier.verify_script(script_text, sample_graph)
        assert not any(d.drift_type == DriftType.FABRICATED_QUOTE for d in report.drifts)

    def test_detect_modal_escalation_level_2_to_level_3(self, sample_source):
        graph = EvidenceGraph(graph_id="g_modal_l2_l3")
        c = ClaimRecord(
            claim_id="c_modal_2",
            claim_text="Silicon transistors typically exhibit higher thermal stability.",
            confidence_score=0.85,
            primary_source=sample_source,
        )
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            claim_type=c.claim_type.value if hasattr(c.claim_type, "value") else str(c.claim_type),
            confidence_score=c.confidence_score,
            claim_record=c,
        )
        verifier = ScriptVerifier()
        report = verifier.verify_script("Silicon transistors undeniably prove higher thermal stability.", graph)
        assert report.passed is False
        strengthened = [d for d in report.drifts if d.drift_type == DriftType.STRENGTHENED]
        assert len(strengthened) >= 1
        assert strengthened[0].severity == DriftSeverity.HIGH

    def test_detect_modal_escalation_level_1_to_level_2(self, sample_source):
        graph = EvidenceGraph(graph_id="g_modal_l1_l2")
        c = ClaimRecord(
            claim_id="c_modal_1",
            claim_text="Initial evidence suggests a possible link between the compounds.",
            confidence_score=0.80,
            primary_source=sample_source,
        )
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            claim_type=c.claim_type.value if hasattr(c.claim_type, "value") else str(c.claim_type),
            confidence_score=c.confidence_score,
            claim_record=c,
        )
        verifier = ScriptVerifier()
        report = verifier.verify_script("Initial evidence generally shows a link between the compounds.", graph)
        escalation_drifts = [d for d in report.drifts if d.observed_value == "Modal Level 2" and d.expected_value == "Modal Level 1"]
        assert len(escalation_drifts) >= 1
        assert escalation_drifts[0].drift_type == DriftType.OMITTED_UNCERTAINTY
        assert escalation_drifts[0].severity == DriftSeverity.MEDIUM

    def test_no_duplicate_drifts_on_grounded_sentences(self, sample_graph):
        verifier = ScriptVerifier()
        script_text = 'Feynman said: "There is barely any room at the bottom."'
        report = verifier.verify_script(script_text, sample_graph)
        quote_drifts = [d for d in report.drifts if d.drift_type == DriftType.FABRICATED_QUOTE]
        assert len(quote_drifts) == 1

    def test_word_boundary_modal_matching_benign_words(self):
        verifier = ScriptVerifier()
        exts = verifier.extract_sentences("The factory produced goods in May without delay.")
        assert len(exts) >= 1
        assert exts[0].modal_level == 2

    def test_auxiliary_count_not_flagged_as_10x_distortion(self, sample_source):
        graph = EvidenceGraph(graph_id="g_aux_count")
        c = ClaimRecord(
            claim_id="c_bell_proto",
            claim_text="Bell Labs produced 4,980 prototype units in 1948.",
            confidence_score=0.85,
            primary_source=sample_source,
        )
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            claim_type=c.claim_type.value if hasattr(c.claim_type, "value") else str(c.claim_type),
            confidence_score=c.confidence_score,
            claim_record=c,
        )
        verifier = ScriptVerifier()
        report = verifier.verify_script("In 1948, 3 engineers at Bell Labs produced 4,980 prototype units.", graph)
        num_drifts = [d for d in report.drifts if d.drift_type == DriftType.ALTERED_NUMBER]
        assert len(num_drifts) == 0

    def test_script_sentence_segmenter_export(self):
        segmenter = ScriptSentenceSegmenter()
        text = "Dr. Shockley developed the transistor at Bell Labs. It was a breakthrough."
        spans = segmenter.segment_sentences(text)
        assert len(spans) == 2
        extractions = segmenter.extract_sentences(text)
        assert len(extractions) == 2

    def test_compound_growth_alternate_phrasings(self, sample_graph):
        verifier = ScriptVerifier()
        for phrase in [
            "Revenue grew from 10 million to 30 million, a 300% increase.",
            "Sales increased from 10 to 30, an increase of 300%.",
            "Output rose from 10 to 30 (a 300% increase).",
            "Volume surged from 10 to 30, up 300%.",
        ]:
            report = verifier.verify_script(phrase, sample_graph)
            assert any(
                d.drift_type == DriftType.ALTERED_NUMBER and "calculation error" in d.explanation.lower()
                for d in report.drifts
            ), f"Failed to detect compound math error for: {phrase}"

