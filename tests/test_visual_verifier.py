"""tests/test_visual_verifier.py — Test Suite for Visual Fact-Checking & Storyboard Reconciliation Engine.

Tests audio-visual numerical reconciliation, timeline chronology and date consistency,
chart trend polarity matching, baseline zero anti-distortion enforcement, entity count
matching, territory label anachronisms, and EvidenceGraph DAG synchronization.
"""

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
    TemporalContext,
)
from src.models.script import Beat, Scene, Storyboard
from src.epistemic.graph import EvidenceGraph, GraphNodeType
from src.epistemic.visual_verifier import (
    SceneVisualReport,
    VisualDiscrepancyType,
    VisualInconsistencyRecord,
    VisualSeverity,
    VisualVerificationReport,
    VisualVerifier,
)
from src.epistemic.numerical_pipeline import NumericalDataPoint, NumericalDataset


@pytest.fixture
def sample_source() -> SourceRecord:
    return SourceRecord(
        source_id="src_tech_hist",
        title="Solid State Technology History",
        url="https://ieee.org/transistor.html",
        tier=SourceTier.PRIMARY_SOURCE,
        publisher="IEEE",
    )


class TestNumericalAndUnitVerification:
    """Tests numerical and unit alignment between visual statistic reveals and spoken audio."""

    def test_unit_mismatch_blocks_publishing(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_stat_1",
            "block_type": "statistic_reveal",
            "parameters": {
                "target_number": "$4.2B",
                "metric_label": "Development Budget",
            },
            "narration_text": "The entire development effort cost approximately 4.2 million dollars.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        assert report.verdict == "BLOCK"
        unit_mismatches = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.VISUAL_AUDIO_UNIT_MISMATCH
        ]
        assert len(unit_mismatches) == 1
        assert unit_mismatches[0].severity == VisualSeverity.BLOCK

    def test_numerical_mismatch_blocks_publishing(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_stat_2",
            "block_type": "statistic_reveal",
            "parameters": {
                "target_number": "$5.5M",
                "metric_label": "Revenue",
            },
            "narration_text": "The division generated 4.2 million in its first quarter.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        num_mismatches = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.VISUAL_AUDIO_NUMERICAL_MISMATCH
        ]
        assert len(num_mismatches) == 1

    def test_exact_numerical_match_passes(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_stat_3",
            "block_type": "statistic_reveal",
            "parameters": {
                "target_number": "$4.2M",
                "metric_label": "Revenue",
            },
            "narration_text": "The team secured 4.2 million dollars in venture funding.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
        assert report.verdict == "PASS"


class TestTimelineReconciliation:
    """Tests chronological ordering, date consistency, and evidence anachronisms."""

    def test_detect_timeline_chronology_inversion(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_time_inv",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1954", "title": "Silicon Transistor Commercialized"},
                    {"year": "1947", "title": "Point-Contact Transistor Invented"},
                ]
            },
            "narration_text": "First discovered in 1947, silicon models followed in 1954.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        inversions = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION
        ]
        assert len(inversions) == 1
        assert inversions[0].severity == VisualSeverity.BLOCK

    def test_detect_audio_visual_temporal_mismatch(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_time_mismatch",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1947", "title": "Invention"},
                    {"year": "1948", "title": "Announcement"},
                ]
            },
            "narration_text": "In 1956, the Nobel Prize recognized their groundbreaking discovery.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        date_mismatches = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.VISUAL_AUDIO_TEMPORAL_MISMATCH
        ]
        assert len(date_mismatches) == 1

    def test_detect_timeline_date_anachronism_against_evidence(self, sample_source):
        graph = EvidenceGraph(graph_id="g_time_anach")
        c = ClaimRecord(
            claim_id="claim_proto",
            claim_text="The prototype transistor was built in 1947.",
            temporal_context=TemporalContext(valid_from="1947", valid_until="1950"),
            primary_source=sample_source,
        )
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            claim_record=c,
        )

        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_anach",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1935", "title": "Early Prototype"},
                    {"year": "1948", "title": "Public Debut"},
                ],
                "grounded_claim_ids": ["claim_proto"],
            },
            "narration_text": "Work began early in 1935 before the debut in 1948.",
        }
        report = verifier.verify_visuals([scene], graph=graph)
        assert any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_DATE_ANACHRONISM for i in report.inconsistencies)


class TestChartAndTrendVerification:
    """Tests trend slope polarity, zero-baseline anti-distortion, and dataset bindings."""

    def test_detect_chart_trend_contradiction(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_chart_trend",
            "block_type": "chart",
            "parameters": {
                "chart_data": [{"x": 1, "y": 10}, {"x": 2, "y": 50}, {"x": 3, "y": 120}],
            },
            "narration_text": "Revenues fell precipitously and dropped sharply over the year.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        trend_contradictions = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
        ]
        assert len(trend_contradictions) == 1
        assert trend_contradictions[0].severity == VisualSeverity.BLOCK

    def test_enforce_zero_baseline_on_bar_chart(self):
        verifier = VisualVerifier(enforce_zero_baseline=True)
        scene = {
            "scene_id": "sc_bar_baseline",
            "block_type": "bar_chart",
            "parameters": {
                "chart_type": "bar",
                "data_points": [{"x": 1, "y": 92.0}, {"x": 2, "y": 95.0}, {"x": 3, "y": 98.0}],
                "y_axis_min": 85.0,  # Truncated baseline without opt-in
            },
            "narration_text": "Performance rose steadily over the decade.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        baseline_errors = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.CHART_BASELINE_TRUNCATION
        ]
        assert len(baseline_errors) == 1
        assert baseline_errors[0].severity == VisualSeverity.BLOCK

    def test_detect_dangling_dataset_binding(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_dangling",
            "block_type": "chart",
            "parameters": {
                "dataset_id": "ds_unregistered_999",
                "chart_data": [{"x": 1, "y": 10}],
            },
            "narration_text": "Here is the official empirical dataset.",
        }
        report = verifier.verify_visuals([scene], datasets={})

        assert report.passed is False
        dangling = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.DANGLING_DATASET_BINDING
        ]
        assert len(dangling) == 1


class TestEntityCountVerification:
    """Tests alignment between spoken quantities and on-screen panels/cards."""

    def test_detect_spoken_vs_visual_count_discrepancy(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_collage_cnt",
            "block_type": "reference_collage_hook",
            "parameters": {
                "image_paths": ["img1.png", "img2.png", "img3.png", "img4.png", "img5.png"],
            },
            "narration_text": "Three distinct breakthroughs transformed the industry.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        count_errors = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY
        ]
        assert len(count_errors) == 1
        assert count_errors[0].visual_value == 5
        assert count_errors[0].expected_value == 3

    def test_matching_entity_count_passes(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_collage_ok",
            "block_type": "reference_collage_hook",
            "parameters": {
                "panel_count": 3,
                "image_paths": ["img1.png", "img2.png", "img3.png"],
            },
            "narration_text": "Three key innovations paved the way.",
        }
        report = verifier.verify_visuals([scene])
        assert not any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report.inconsistencies)


class TestGeospatialVerification:
    """Tests territory label anachronisms against historical eras."""

    def test_detect_territory_label_anachronism(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_ussr_anach",
            "block_type": "map",
            "parameters": {
                "territory": "Soviet Union",
            },
            "narration_text": "By late 1995, diplomatic tensions had escalated across the region.",
        }
        report = verifier.verify_visuals([scene])

        assert report.passed is False
        anach = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.TERRITORY_LABEL_ANACHRONISM
        ]
        assert len(anach) == 1
        assert anach[0].severity == VisualSeverity.BLOCK


class TestPolymorphicInputAndGraphSync:
    """Tests handling of Storyboard dataclass and EvidenceGraph trace synchronization."""

    def test_storyboard_dataclass_input(self):
        verifier = VisualVerifier()
        sb = Storyboard(
            project_id="proj_sb_test",
            target_duration=10.0,
            scenes=[
                Scene(
                    scene_id="sc_sb_1",
                    title="Introduction",
                    start_time=0.0,
                    duration=5.0,
                    narration_text="The company raised 4.2 million dollars.",
                    beats=[
                        Beat(
                            beat_id="b_1",
                            text="The company raised 4.2 million dollars.",
                            start_time=0.0,
                            end_time=5.0,
                            duration=5.0,
                        )
                    ],
                )
            ],
        )
        report = verifier.verify_visuals(sb)
        assert report.total_scenes_audited == 1

    def test_evidence_graph_sync(self):
        graph = EvidenceGraph(graph_id="g_vis_sync")
        graph.add_source(title="Source", url="https://example.com")
        verifier = VisualVerifier(sync_to_graph=True)
        scene = {
            "scene_id": "sc_clean",
            "block_type": "statistic_reveal",
            "parameters": {"target_number": "$4.2M"},
            "narration_text": "Funding reached 4.2 million dollars.",
        }
        report = verifier.verify_visuals([scene], graph=graph)
        assert report.passed is True

        traces = [
            n for n in graph._nodes.values() if n.node_type == GraphNodeType.VERIFICATION_TRACE
        ]
        assert len(traces) >= 1
        assert traces[0].strategy_used == "VISUAL_FACT_CHECK"


class TestComparisonPanelVerification:
    """Tests comparison panel order relations and synonym consistency."""

    def test_comparison_panel_lower_than_conflict_blocks(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_1",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Cost", "val_a": 100, "val_b": 50},
                ]
            },
            "narration_text": "Entity A cost significantly lower than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
            and i.severity == VisualSeverity.BLOCK
            for i in report.inconsistencies
        )

    def test_comparison_panel_higher_than_inverse_conflict_blocks(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_2",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Latency", "val_a": 10, "val_b": 50},
                ]
            },
            "narration_text": "Entity A latency was higher than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
            and i.severity == VisualSeverity.BLOCK
            for i in report.inconsistencies
        )

    def test_comparison_panel_synonyms_detected(self):
        verifier = VisualVerifier()
        # "worse than"
        scene = {
            "scene_id": "sc_comp_syn",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [{"metric": "Score", "val_a": 95, "val_b": 70}]
            },
            "narration_text": "Entity A scored worse than Entity B across tests.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False

    def test_comparison_panel_consistent_passes(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_ok",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [{"metric": "Speed", "val_a": 100, "val_b": 50}]
            },
            "narration_text": "Entity A operated faster and higher than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True


class TestAncientTimelineAndCrossSceneVerification:
    """Tests BCE timeline parsing and cross-scene sequence continuity."""

    def test_detect_bce_timeline_inversion(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_bce",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "44 BCE", "title": "Caesar"},
                    {"year": "500 BCE", "title": "Republic"},
                ]
            },
            "narration_text": "From 500 BCE to 44 BCE, Rome evolved.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)

    def test_detect_negative_integer_timeline_inversion(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_neg",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": -44, "title": "Later"},
                    {"year": -500, "title": "Earlier"},
                ]
            },
            "narration_text": "Ancient timeline.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)

    def test_detect_cross_scene_timeline_inversion(self):
        verifier = VisualVerifier()
        scenes = [
            {
                "scene_id": "sc_1",
                "scene_index": 1,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [{"year": "1990", "title": "A"}, {"year": "1995", "title": "B"}]
                },
                "narration_text": "1990 to 1995.",
            },
            {
                "scene_id": "sc_2",
                "scene_index": 2,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [{"year": "1970", "title": "C"}, {"year": "1975", "title": "D"}]
                },
                "narration_text": "1970 to 1975.",
            },
        ]
        report = verifier.verify_visuals(scenes)
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)

    def test_cross_scene_flashback_allowed(self):
        verifier = VisualVerifier()
        scenes = [
            {
                "scene_id": "sc_1",
                "scene_index": 1,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [{"year": "1990", "title": "A"}, {"year": "1995", "title": "B"}]
                },
                "narration_text": "1990 to 1995.",
            },
            {
                "scene_id": "sc_2",
                "scene_index": 2,
                "block_type": "timeline_reveal",
                "parameters": {
                    "flashback": True,
                    "milestones": [{"year": "1970", "title": "C"}, {"year": "1975", "title": "D"}]
                },
                "narration_text": "Flashback to 1970.",
            },
        ]
        report = verifier.verify_visuals(scenes)
        assert not any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)


class TestEntityCountGeneralizationAndBoundaries:
    """Tests general entity nouns, 'dozens', and singular noun counts."""

    def test_general_entity_nouns_battalions_and_vessels(self):
        verifier = VisualVerifier()
        # Voiceover says "three battalions" vs 5 images -> discrepancy
        scene_discrepancy = {
            "scene_id": "sc_bat_bad",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "Three battalions defended the mountain pass.",
        }
        report = verifier.verify_visuals([scene_discrepancy])
        assert any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report.inconsistencies)

        # Voiceover says "5 vessels" vs 5 images -> passes
        scene_ok = {
            "scene_id": "sc_ves_ok",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "5 vessels sailed across the Atlantic.",
        }
        report_ok = verifier.verify_visuals([scene_ok])
        assert not any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report_ok.inconsistencies)

    def test_dozens_quantifier_boundary(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_dozens",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "Dozens of breakthroughs transformed the entire scientific world.",
        }
        report = verifier.verify_visuals([scene])
        assert any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report.inconsistencies)

    def test_singular_noun_boundary(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_sing",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "One breakthrough transformed the field of solid state physics.",
        }
        report = verifier.verify_visuals([scene])
        assert any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report.inconsistencies)


class TestChartTrendVocabularyAndDatasetFallback:
    """Tests 'crashed' sentiment detection and dataset_id fallback."""

    def test_trend_inversion_crashed_detected(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_crash",
            "block_type": "chart",
            "parameters": {
                "chart_data": [{"x": 1, "y": 10}, {"x": 2, "y": 50}, {"x": 3, "y": 100}],
            },
            "narration_text": "The market crashed to historic lows amidst the panic.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION for i in report.inconsistencies)

    def test_dataset_id_fallback_when_data_points_omitted(self, sample_source):
        verifier = VisualVerifier()
        ds = NumericalDataset(
            dataset_id="ds_sales_trend",
            title="Sales",
            data_points=[
                NumericalDataPoint(x_value=1, y_value=10.0),
                NumericalDataPoint(x_value=2, y_value=50.0),
                NumericalDataPoint(x_value=3, y_value=100.0),
            ],
            source_record=sample_source,
        )
        scene = {
            "scene_id": "sc_ds_fallback",
            "block_type": "chart",
            "parameters": {
                "dataset_id": "ds_sales_trend",
                # Note: data_points omitted
            },
            "narration_text": "Revenues fell precipitously and dropped sharply over the year.",
        }
        report = verifier.verify_visuals([scene], datasets={"ds_sales_trend": ds})
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION for i in report.inconsistencies)
