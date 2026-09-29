"""tests/test_m4_adversarial_challenger2.py — Adversarial Challenge Test Suite for Milestone 4.

Author: challenger_2_m4_gen9 (teamwork_preview_challenger)
Purpose: Adversarially challenge and stress-test the Visual Fact-Checking Engine
         (src/epistemic/visual_verifier.py) and Deterministic Numerical Data Pipeline
         (src/epistemic/numerical_pipeline.py).

Challenge Dimensions:
1. Timeline & chronology stress: negative/BCE years, cross-scene inversions, conflicting voiceover vs visual dates.
2. Visual chart trend inversion: positive slope with negative voiceover ("crashed", "plummeted"), non-zero baseline without disclosure.
3. Numerical pipeline precision & determinism: 100x bit-identical SVG rendering, NaN/Inf injection, Hare-Niemeyer pathological splits.
4. Entity count mismatch boundaries: voiceover "dozens" vs visual count 5, exact singular vs plural noun counts.
"""

import math
from decimal import Decimal
import pytest

from src.models.contracts import SourceRecord, SourceTier
from src.epistemic.visual_verifier import (
    VisualVerifier,
    VisualSeverity,
    VisualDiscrepancyType,
    VisualVerificationReport,
)
from src.epistemic.numerical_pipeline import (
    ChartType,
    DeterministicChartRenderer,
    NumericalDataPoint,
    NumericalDataset,
    NumericalDatasetIngestion,
    NumericalInvariantChecker,
    NumericalTransformer,
)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def sample_source() -> SourceRecord:
    return SourceRecord(
        source_id="src_adv_m4",
        title="Historical and Economic Statistics Archive",
        url="https://archive.org/stats",
        tier=SourceTier.PRIMARY_SOURCE,
        publisher="Global Historical Archive",
    )


# ===========================================================================
# 1. Timeline & Chronology Stress
# ===========================================================================

class TestTimelineAndChronologyStress:
    """Stress-tests timeline ordering, negative/BCE year handling, and cross-scene chronology."""

    def test_timeline_chronology_inversion_positive_ce_detected(self):
        """Baseline: verifies standard 4-digit CE chronological inversion is caught."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_ce_inv",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1980", "title": "Microprocessor Era"},
                    {"year": "1960", "title": "Integrated Circuit"},
                ]
            },
            "narration_text": "From 1960 to 1980, computing accelerated.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION
            for i in report.inconsistencies
        )

    def test_timeline_chronology_bce_string_inversion(self):
        """Adversarial: Inverted BCE years (e.g., 44 BCE preceding 500 BCE).
        In history, 500 BCE happened before 44 BCE. Putting 44 BCE first is an inversion.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_bce_inv",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "44 BCE", "title": "Assassination of Julius Caesar"},
                    {"year": "500 BCE", "title": "Roman Republic Established"},
                ]
            },
            "narration_text": "The Roman Republic began in 500 BCE and Caesar fell in 44 BCE.",
        }
        report = verifier.verify_visuals([scene])
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION
            for i in report.inconsistencies
        ), "Expected TIMELINE_CHRONOLOGY_INVERSION for 44 BCE placed before 500 BCE"

    def test_timeline_negative_integer_year_inversion(self):
        """Adversarial: Negative integer astronomical year numbering (-44 preceding -500)."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_neg_inv",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": -44, "title": "Event Later"},
                    {"year": -500, "title": "Event Earlier"},
                ]
            },
            "narration_text": "Ancient historical milestones.",
        }
        report = verifier.verify_visuals([scene])
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION
            for i in report.inconsistencies
        ), "Expected TIMELINE_CHRONOLOGY_INVERSION for -44 placed before -500"

    def test_cross_scene_out_of_order_chronology(self):
        """Adversarial: Scene 1 depicts 1995, Scene 2 depicts 1970.
        Tests whether the verifier audits cross-scene chronology or only intra-scene milestones.
        """
        verifier = VisualVerifier()
        scenes = [
            {
                "scene_id": "sc_scene_1",
                "scene_index": 1,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [
                        {"year": "1990", "title": "World Wide Web"},
                        {"year": "1995", "title": "Dot Com Boom"},
                    ]
                },
                "narration_text": "In 1990 the web arrived, followed by 1995.",
            },
            {
                "scene_id": "sc_scene_2",
                "scene_index": 2,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [
                        {"year": "1970", "title": "ARPANET Expansion"},
                        {"year": "1975", "title": "Altair 8800"},
                    ]
                },
                "narration_text": "Back in 1970, networks were rudimentary.",
            },
        ]
        report = verifier.verify_visuals(scenes)
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION
            for i in report.inconsistencies
        ), "Expected cross-scene chronological inversion to be detected"

    def test_conflicting_voiceover_vs_visual_dates(self):
        """Conflicting voiceover date (1985) vs visual milestone dates (1947, 1954)."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_voiceover_mismatch",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1947", "title": "Invention"},
                    {"year": "1954", "title": "Production"},
                ]
            },
            "narration_text": "In 1985, personal computing transformed the entire economic landscape.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.VISUAL_AUDIO_TEMPORAL_MISMATCH
            for i in report.inconsistencies
        )


# ===========================================================================
# 2. Visual Chart Trend Inversion
# ===========================================================================

class TestVisualChartTrendInversionStress:
    """Stress-tests trend slope polarities vs narrative sentiments, and zero baseline invariants."""

    def test_trend_inversion_plummeted_detected(self):
        """Positive slope visual ([10, 50, 100]) vs voiceover with 'plummeted'."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_chart_plummet",
            "block_type": "chart",
            "parameters": {
                "chart_data": [{"x": 1, "y": 10}, {"x": 2, "y": 50}, {"x": 3, "y": 100}],
            },
            "narration_text": "Sales plummeted dramatically over the quarter.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
            for i in report.inconsistencies
        )

    def test_trend_inversion_crashed_sentiment_detection(self):
        """Adversarial: Positive slope visual ([10, 50, 100]) vs voiceover stating 'crashed'."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_chart_crashed",
            "block_type": "chart",
            "parameters": {
                "chart_data": [{"x": 1, "y": 10}, {"x": 2, "y": 50}, {"x": 3, "y": 100}],
            },
            "narration_text": "The market crashed to historic lows amidst the panic.",
        }
        report = verifier.verify_visuals([scene])
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
            for i in report.inconsistencies
        ), "Expected CHART_TREND_CONTRADICTION when audio says 'crashed' but chart rises"

    def test_bar_chart_non_zero_baseline_lacking_disclosure_blocked(self):
        """Bar chart starting at y=80 with values [90, 95, 100] lacking explicit disclosure."""
        verifier = VisualVerifier(enforce_zero_baseline=True)
        scene = {
            "scene_id": "sc_bar_nonzero",
            "block_type": "bar_chart",
            "parameters": {
                "chart_type": "bar",
                "data_points": [{"x": 1, "y": 90.0}, {"x": 2, "y": 95.0}, {"x": 3, "y": 100.0}],
                "y_axis_min": 80.0,
                "allow_truncated_baseline": False,
            },
            "narration_text": "Consistent output recorded.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.CHART_BASELINE_TRUNCATION
            for i in report.inconsistencies
        )

    def test_numerical_invariant_checker_non_zero_baseline_violation(self, sample_source):
        """Verifies NumericalInvariantChecker rejects non-zero baseline without disclosure."""
        pts = [
            NumericalDataPoint(x_value=1, y_value=90.0),
            NumericalDataPoint(x_value=2, y_value=95.0),
        ]
        ds = NumericalDataset(
            dataset_id="ds_nz_test",
            title="Non-Zero Baseline Test",
            data_points=pts,
            source_record=sample_source,
        )
        cfg = DeterministicChartRenderer.render_chart(ds, ChartType.BAR)
        bad_cfg = cfg.model_copy(update={"y_axis_min": 50.0, "has_truncated_baseline": False})
        res = NumericalInvariantChecker.verify_chart_data(ds, bad_cfg)
        assert res.valid is False
        assert any("UNJUSTIFIED_NON_ZERO_BASELINE" in v for v in res.violations)


# ===========================================================================
# 3. Numerical Pipeline Precision & Determinism
# ===========================================================================

class TestNumericalPipelinePrecisionAndDeterminism:
    """Stress-tests 100x bit-identical SVG rendering, NaN/Inf injection, and Hare-Niemeyer splits."""

    def test_100x_bit_identical_svg_rendering_stress(self, sample_source):
        """Renders 100 times across BAR, LINE, and SCATTER charts; verifies 100% bit-identical hash."""
        pts = [
            NumericalDataPoint(x_value=1950, y_value=10.5, label="A"),
            NumericalDataPoint(x_value=1960, y_value=25.25, label="B"),
            NumericalDataPoint(x_value=1970, y_value=60.125, label="C"),
            NumericalDataPoint(x_value=1980, y_value=120.75, label="D"),
        ]
        ds = NumericalDataset(
            dataset_id="ds_100x_test",
            title="Determinism Test",
            data_points=pts,
            source_record=sample_source,
        )

        for chart_type in [ChartType.BAR, ChartType.LINE, ChartType.SCATTER]:
            first_cfg = DeterministicChartRenderer.render_chart(ds, chart_type)
            first_hash = first_cfg.chart_sha256
            first_svg = first_cfg.rendered_svg

            for i in range(100):
                rendered = DeterministicChartRenderer.render_chart(ds, chart_type)
                assert rendered.chart_sha256 == first_hash, f"Hash divergence at run {i} for {chart_type}"
                assert rendered.rendered_svg == first_svg, f"SVG divergence at run {i} for {chart_type}"

    def test_nan_and_inf_input_injection_rejection(self):
        """Injects NaN, +Inf, and -Inf into NumericalDataPoint and ingestion functions."""
        # 1. Direct NumericalDataPoint y_value validation
        with pytest.raises(ValueError, match="finite numerical value"):
            NumericalDataPoint(x_value="2020", y_value=float("nan"))

        with pytest.raises(ValueError, match="finite numerical value"):
            NumericalDataPoint(x_value="2020", y_value=float("inf"))

        with pytest.raises(ValueError, match="finite numerical value"):
            NumericalDataPoint(x_value="2020", y_value=float("-inf"))

        # 2. Ingestion clean_numeric_string validation
        for bad_val in ["NaN", "nan", "Inf", "-inf", "Infinity", "-Infinity", "null", "none", "n/a", ""]:
            with pytest.raises(ValueError):
                NumericalDatasetIngestion.clean_numeric_string(bad_val)

        # 3. CSV injection with NaN
        csv_nan = "year,val\n2020,NaN\n2021,50"
        with pytest.raises(ValueError):
            NumericalDatasetIngestion.from_csv(csv_nan, "ds_nan", "Title", "year", "val")

        # 4. JSON records injection with Inf
        json_inf = [{"year": 2020, "val": float("inf")}]
        with pytest.raises(ValueError):
            NumericalDatasetIngestion.from_json_records(json_inf, "ds_inf", "Title", "year", "val")

    def test_nan_injection_in_uncertainty_range(self):
        """Adversarial: Injects NaN into uncertainty_range tuple."""
        with pytest.raises(ValueError, match="finite"):
            NumericalDataPoint(
                x_value="2020",
                y_value=10.0,
                uncertainty_range=(float("nan"), 12.0),
            )

    def test_hare_niemeyer_pathological_splits(self, sample_source):
        """Tests Hare-Niemeyer Largest Remainder Method across pathological splits."""
        # Case A: 3 equal thirds (10, 10, 10)
        pts_3 = [
            NumericalDataPoint(x_value="A", y_value=10.0),
            NumericalDataPoint(x_value="B", y_value=10.0),
            NumericalDataPoint(x_value="C", y_value=10.0),
        ]
        ds_3 = NumericalDataset(dataset_id="ds_3", title="Thirds", data_points=pts_3, source_record=sample_source)
        shares_3 = NumericalTransformer.calculate_percentage_shares(ds_3, decimal_places=2)
        total_3 = sum(s[1] for s in shares_3)
        assert round(total_3, 6) == 100.00, f"Thirds sum: {total_3}"

        # Case B: 7 equal sevenths (1, 1, 1, 1, 1, 1, 1) -> 1/7 = 14.285714%
        pts_7 = [NumericalDataPoint(x_value=f"Item_{i}", y_value=1.0) for i in range(7)]
        ds_7 = NumericalDataset(dataset_id="ds_7", title="Sevenths", data_points=pts_7, source_record=sample_source)
        shares_7 = NumericalTransformer.calculate_percentage_shares(ds_7, decimal_places=2)
        total_7 = sum(s[1] for s in shares_7)
        assert round(total_7, 6) == 100.00, f"Sevenths sum: {total_7}"
        vals_7 = sorted(s[1] for s in shares_7)
        assert vals_7 == [14.28, 14.28, 14.28, 14.29, 14.29, 14.29, 14.29]

        # Case C: Zero value items present (100, 0, 0)
        pts_zero = [
            NumericalDataPoint(x_value="Main", y_value=100.0),
            NumericalDataPoint(x_value="Zero1", y_value=0.0),
            NumericalDataPoint(x_value="Zero2", y_value=0.0),
        ]
        ds_zero = NumericalDataset(dataset_id="ds_zero", title="Zero", data_points=pts_zero, source_record=sample_source)
        shares_zero = NumericalTransformer.calculate_percentage_shares(ds_zero, decimal_places=2)
        total_zero = sum(s[1] for s in shares_zero)
        assert round(total_zero, 6) == 100.00
        assert [s[1] for s in shares_zero] == [100.00, 0.00, 0.00]


# ===========================================================================
# 4. Entity Count Mismatch Boundaries
# ===========================================================================

class TestEntityCountMismatchBoundaries:
    """Stress-tests entity count mismatch boundaries, 'dozens' voiceover, and singular vs plural counts."""

    def test_voiceover_dozens_vs_visual_five(self):
        """Adversarial: Voiceover states 'Dozens of breakthroughs' vs visual component containing 5 images."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_cnt_dozens",
            "block_type": "reference_collage_hook",
            "parameters": {
                "image_paths": ["img1.png", "img2.png", "img3.png", "img4.png", "img5.png"],
            },
            "narration_text": "Dozens of breakthroughs transformed the entire scientific world.",
        }
        report = verifier.verify_visuals([scene])
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY
            for i in report.inconsistencies
        ), "Expected VISUAL_COUNT_DISCREPANCY when voiceover states 'Dozens' but visual displays 5"

    def test_singular_noun_count_boundary(self):
        """Adversarial: Spoken singular noun 'one breakthrough' vs visual containing 5 images."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_cnt_singular",
            "block_type": "reference_collage_hook",
            "parameters": {
                "image_paths": ["img1.png", "img2.png", "img3.png", "img4.png", "img5.png"],
            },
            "narration_text": "One breakthrough transformed the entire field of solid state physics.",
        }
        report = verifier.verify_visuals([scene])
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY
            for i in report.inconsistencies
        ), "Expected VISUAL_COUNT_DISCREPANCY when voiceover asserts 1 entity but visual has 5"

    def test_exact_singular_plural_delta_one_severity(self):
        """Tests delta=1 discrepancy produces WARN severity, while delta>1 produces BLOCK severity."""
        verifier = VisualVerifier()

        # Delta = 1 (spoken: 3, visual: 2) -> Should be WARN
        scene_delta1 = {
            "scene_id": "sc_delta1",
            "block_type": "reference_collage_hook",
            "parameters": {
                "image_paths": ["img1.png", "img2.png"],
            },
            "narration_text": "Three key breakthroughs revolutionized computing.",
        }
        report1 = verifier.verify_visuals([scene_delta1])
        cnt_inc1 = [i for i in report1.inconsistencies if i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY]
        assert len(cnt_inc1) == 1
        assert cnt_inc1[0].severity == VisualSeverity.WARN

        # Delta = 2 (spoken: 3, visual: 5) -> Should be BLOCK
        scene_delta2 = {
            "scene_id": "sc_delta2",
            "block_type": "reference_collage_hook",
            "parameters": {
                "image_paths": ["img1.png", "img2.png", "img3.png", "img4.png", "img5.png"],
            },
            "narration_text": "Three key breakthroughs revolutionized computing.",
        }
        report2 = verifier.verify_visuals([scene_delta2])
        cnt_inc2 = [i for i in report2.inconsistencies if i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY]
        assert len(cnt_inc2) == 1
        assert cnt_inc2[0].severity == VisualSeverity.BLOCK

# ===========================================================================
# 5. Multi-Predicate Comparison Panel Stress
# ===========================================================================

class TestMultiPredicateComparisonPanelStress:
    """Stress-tests multi-attribute comparison panels against multi-clause narration.
    Focus: Verify whether multi-attribute comparisons are handled dynamically without
    failing or reverting to single-predicate shortcuts.
    """

    def test_multi_predicate_unidirectional_consistent_passes(self):
        """Control: When all attributes in a multi-attribute panel point in the same
        direction (Entity A > Entity B) and voiceover uses 'higher than' / 'greater than',
        verification passes.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_unidir",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Throughput", "val_a": 100, "val_b": 50},
                    {"metric": "Efficiency", "val_a": 95, "val_b": 80},
                ]
            },
            "narration_text": "Entity A delivered throughput higher than Entity B, and efficiency greater than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
        assert report.verdict == "PASS"
        assert len(report.inconsistencies) == 0

    def test_multi_predicate_mixed_attributes_empirical_failure_reproduction(self):
        """Adversarial & Empirical Bug Reproduction:
        Row 0: Throughput 100 vs 50 (Entity A > Entity B).
        Row 1: Latency 10 vs 50 (Entity A < Entity B).
        Voiceover: 'Entity A achieved throughput higher than Entity B, with latency lower than Entity B.'
        
        VULNERABILITY: VisualVerifier._audit_comparison_panel executes a naive global search
        across the entire narration text for lower_synonyms and higher_synonyms.
        Both 'higher than' and 'lower than' match globally.
        Then, for Row 0 (A > B), it checks 'if num_a > num_b and matched_lower:', which triggers
        because 'lower than' was matched from the Latency clause!
        For Row 1 (A < B), it checks 'elif num_a < num_b and matched_higher:', which triggers
        because 'higher than' was matched from the Throughput clause!
        Both rows are falsely flagged as blocking contradictions.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_multi_pred_fail",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Throughput", "val_a": 100, "val_b": 50},
                    {"metric": "Latency", "val_a": 10, "val_b": 50},
                ]
            },
            "narration_text": "Entity A achieved throughput higher than Entity B, with latency lower than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        # Empirically verify the failure mode
        assert report.passed is False
        assert report.verdict == "BLOCK"
        contradictions = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
        ]
        assert len(contradictions) == 2
        assert any("Throughput" in c.explanation and "lower than" in c.explanation for c in contradictions)
        assert any("Latency" in c.explanation and "higher than" in c.explanation for c in contradictions)

    @pytest.mark.xfail(
        reason="Defect: VisualVerifier._audit_comparison_panel uses a single-predicate global search shortcut instead of per-metric clause binding",
        strict=False,
    )
    def test_multi_predicate_mixed_attributes_ideal_contract(self):
        """Specification Contract:
        A fact-checking engine MUST dynamically reconcile multi-attribute comparisons
        without falsely flagging valid visual-audio pairs.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_multi_pred_contract",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Throughput", "val_a": 100, "val_b": 50},
                    {"metric": "Latency", "val_a": 10, "val_b": 50},
                ]
            },
            "narration_text": "Entity A achieved throughput higher than Entity B, with latency lower than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
        assert report.verdict == "PASS"
        assert len(report.inconsistencies) == 0

    def test_multi_predicate_metric_decoupling_vulnerability(self):
        """Adversarial: Metric names in comparison_rows are never checked in narration text.
        Even when narration explicitly names the metrics ('throughput', 'latency'), the engine
        does not associate metrics with their respective clauses.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_decoupled",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Cost", "val_a": 50, "val_b": 100},
                    {"metric": "Reliability", "val_a": 99, "val_b": 85},
                ]
            },
            "narration_text": "Entity A had cost lower than Entity B, while reliability was higher than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        # The engine flags contradictions on both rows because it lacks per-metric clause binding
        assert len(report.inconsistencies) == 2


# ===========================================================================
# 6. Timeline Span & Partial Date Reconciliation Stress
# ===========================================================================

class TestTimelineSpanAndPartialDateReconciliationStress:
    """Stress-tests timeline reconciliation across partial dates, year spans, and inverted sequences."""

    def test_intra_year_partial_date_chronology_inversion_empirical_blindspot(self):
        """Adversarial & Empirical Blindspot:
        Milestone 1: '1947-12-23' (Point-contact transistor invented).
        Milestone 2: '1947-06-15' (Initial field-effect experiments).
        Chronologically, December 1947 happens AFTER June 1947. Placing December first is an inversion.
        
        VULNERABILITY: parse_year_value() truncates ISO dates ('1947-12-23' -> 1947).
        Therefore, y_curr > y_next evaluates to 1947 > 1947 (False).
        The intra-year chronology inversion is completely missed!
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_intra_year_inv",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"date": "1947-12-23", "title": "Point Contact Transistor"},
                    {"date": "1947-06-15", "title": "Field Effect Experiments"},
                ]
            },
            "narration_text": "Experiments in June 1947 led to the December 1947 breakthrough.",
        }
        report = verifier.verify_visuals([scene])
        # Empirically: The engine passes this inversion because it only compares integer years
        assert report.passed is True
        assert report.verdict == "PASS"
        assert not any(
            i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION
            for i in report.inconsistencies
        )

    @pytest.mark.xfail(
        reason="Defect: parse_year_value truncates ISO partial dates to 4-digit years, blinding the engine to intra-year chronological inversions",
        strict=False,
    )
    def test_intra_year_partial_date_inversion_ideal_contract(self):
        """Specification Contract:
        The engine MUST detect chronological inversions when partial dates (ISO YYYY-MM-DD)
        occur out of order within the same calendar year.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_intra_year_contract",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"date": "1947-12-23", "title": "Point Contact Transistor"},
                    {"date": "1947-06-15", "title": "Field Effect Experiments"},
                ]
            },
            "narration_text": "Experiments in June 1947 led to the December 1947 breakthrough.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION
            for i in report.inconsistencies
        )

    def test_year_span_end_year_dropped_empirical_false_alarm(self):
        """Adversarial & Empirical False Alarm:
        Visual Milestone 1: '1939-1945' (World War II).
        Visual Milestone 2: '1949' (NATO Founded).
        Voiceover: 'The conflict ended in 1945, leading to NATO in 1949.'
        
        VULNERABILITY: parse_year_value('1939-1945') uses regex r'\b(1\d{3}|20\d{2})\b',
        which returns only 1939. The end year 1945 is completely discarded.
        When spoken_years contains 1945, it checks if 1945 is in {1939, 1949}.
        It is not (and abs diff is 4 and 6, exceeding tolerance 1).
        The engine raises a false BLOCK discrepancy VISUAL_AUDIO_TEMPORAL_MISMATCH.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_span_drop_test",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1939-1945", "title": "World War II"},
                    {"year": "1949", "title": "NATO Founded"},
                ]
            },
            "narration_text": "The conflict ended in 1945, leading to NATO in 1949.",
        }
        report = verifier.verify_visuals([scene])
        # Empirically: The engine halts production due to dropping the end year
        assert report.passed is False
        assert report.verdict == "BLOCK"
        temporal_errors = [
            i for i in report.inconsistencies
            if i.discrepancy_type == VisualDiscrepancyType.VISUAL_AUDIO_TEMPORAL_MISMATCH
        ]
        assert len(temporal_errors) == 1
        assert "1945" in temporal_errors[0].explanation

    @pytest.mark.xfail(
        reason="Defect: parse_year_value discards the end year of range spans ('1939-1945' -> 1939), triggering false temporal mismatches",
        strict=False,
    )
    def test_year_span_end_year_ideal_contract(self):
        """Specification Contract:
        When a visual timeline milestone displays a year span (e.g. '1939-1945'),
        audio narration referencing the concluding year (1945) MUST NOT be flagged as a mismatch.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_span_contract",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1939-1945", "title": "World War II"},
                    {"year": "1949", "title": "NATO Founded"},
                ]
            },
            "narration_text": "The conflict ended in 1945, leading to NATO in 1949.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
        assert report.verdict == "PASS"
        assert len(report.inconsistencies) == 0

    def test_single_milestone_timeline_audio_check_bypassed(self):
        """Empirical: When a timeline component has fewer than 2 milestones (e.g., 1 featured milestone),
        _audit_timeline returns immediately, completely bypassing date reconciliation.
        """
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_single_mile",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "1947", "title": "Transistor Discovery"},
                ]
            },
            "narration_text": "In 1999, the team celebrated a massive new breakthrough.",
        }
        report = verifier.verify_visuals([scene])
        # Returns PASS because len(milestones) < 2 aborts the audit
        assert report.passed is True
        assert len(report.inconsistencies) == 0


# ===========================================================================
# 7. Chart Data Distortion, Negatives & Unit Anomalies Stress
# ===========================================================================

class TestChartDataDistortionNegativesAndUnitAnomaliesStress:
    """Stress-tests negative numbers in audio/visual pipelines, unit conversion multipliers,
    division by zero guards, and Decimal float precision.
    """

    def test_unit_multiplier_mb_kb_gb_inflated_to_billions_empirical_vulnerability(self):
        """Adversarial & Empirical Unit Anomaly:
        VisualVerifier.parse_number_with_multiplier() checks cleaned.endswith('b').
        Any data rate or storage string ending in 'B' (e.g., '500MB', '500KB', '500GB')
        triggers the 'billion' multiplier (1e9)!
        
        Empirically:
        - 500MB (500 million bytes) becomes 500,000,000,000 (500 Billion) -> 1,000x inflation!
        - 500KB (500 thousand bytes) becomes 500,000,000,000 (500 Billion) -> 1,000,000x inflation!
        """
        val_mb = VisualVerifier.parse_number_with_multiplier("500MB")
        val_kb = VisualVerifier.parse_number_with_multiplier("500KB")
        val_gb = VisualVerifier.parse_number_with_multiplier("500GB")

        # Empirically demonstrate the inflation anomaly
        assert val_mb == 500_000_000_000.0, f"Expected 500e9 due to bug, got {val_mb}"
        assert val_kb == 500_000_000_000.0, f"Expected 500e9 due to bug, got {val_kb}"
        assert val_gb == 500_000_000_000.0

    @pytest.mark.xfail(
        reason="Defect: parse_number_with_multiplier misidentifies MB and KB as Billions due to endswith('b')",
        strict=False,
    )
    def test_unit_multiplier_mb_kb_gb_ideal_contract(self):
        """Specification Contract:
        '500MB' must parse to 500,000,000.0 and '500KB' must parse to 500,000.0.
        """
        val_mb = VisualVerifier.parse_number_with_multiplier("500MB")
        val_kb = VisualVerifier.parse_number_with_multiplier("500KB")
        assert val_mb == pytest.approx(500_000_000.0)
        assert val_kb == pytest.approx(500_000.0)

    def test_negative_audio_number_drops_minus_sign_empirical_vulnerability(self):
        """Adversarial & Empirical Negative Number Extraction Bug:
        VisualVerifier.extract_audio_numbers() uses regex r'(\b\d+(?:\.\d+)?)\s*(...)?'.
        Because \b is a word boundary between non-word and word characters, the leading
        negative sign '-' is completely stripped!
        
        Voiceover: 'The company reported -50 million in losses.'
        Visual target_number: '-50M'.
        Spoken extraction yields: (50000000.0, '50 million').
        Relative error: |-50M - 50M| / |-50M| = 2.0 (200% error), causing a false BLOCK.
        """
        extracted = VisualVerifier.extract_audio_numbers("The company reported -50 million in losses.")
        assert len(extracted) == 1
        # Empirically: The negative sign is dropped, yielding positive 50M
        assert extracted[0][0] == 50_000_000.0

        # When verified in a scene:
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_neg_num_test",
            "block_type": "statistic_reveal",
            "parameters": {"target_number": "-50M"},
            "narration_text": "The company reported -50 million in losses.",
        }
        report = verifier.verify_visuals([scene])
        # Empirically: Halts pipeline on false numerical mismatch
        assert report.passed is False
        assert report.verdict == "BLOCK"

    @pytest.mark.xfail(
        reason="Defect: extract_audio_numbers regex drops leading negative sign, causing false numerical mismatch on negative numbers",
        strict=False,
    )
    def test_negative_audio_number_ideal_contract(self):
        """Specification Contract:
        Spoken negative numbers ('-50 million') must extract with sign intact (-50,000,000.0),
        and match visual '-50M' with PASS verdict.
        """
        extracted = VisualVerifier.extract_audio_numbers("The company reported -50 million in losses.")
        assert extracted[0][0] == -50_000_000.0

        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_neg_num_contract",
            "block_type": "statistic_reveal",
            "parameters": {"target_number": "-50M"},
            "narration_text": "The company reported -50 million in losses.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
        assert report.verdict == "PASS"

    def test_division_by_zero_guards_in_growth_rate_and_shares(self, sample_source):
        """Stress: Confirms division by zero guards prevent crashes on zero baselines."""
        # 1. Growth rate zero baseline guard
        with pytest.raises(ValueError, match="Cannot calculate percentage growth rate from a zero baseline"):
            NumericalTransformer.calculate_growth_rate(0.0, 100.0)

        with pytest.raises(ValueError, match="Cannot calculate percentage growth rate from a zero baseline"):
            NumericalTransformer.calculate_growth_rate(0.0, 0.0)

        # 2. Percentage shares zero total sum guard
        pts_zero = [
            NumericalDataPoint(x_value="A", y_value=0.0),
            NumericalDataPoint(x_value="B", y_value=0.0),
        ]
        ds_zero = NumericalDataset(dataset_id="ds_all_zero", title="Zero", data_points=pts_zero, source_record=sample_source)
        with pytest.raises(ValueError, match="Total sum of data points must be positive"):
            NumericalTransformer.calculate_percentage_shares(ds_zero)

    def test_bar_chart_negative_numbers_coordinate_projection(self, sample_source):
        """Stress: Deterministic coordinate projection for bar charts with negative values."""
        # Mixed values: [-20.0, 0.0, 30.0]
        pts_mixed = [
            NumericalDataPoint(x_value="2021", y_value=-20.0),
            NumericalDataPoint(x_value="2022", y_value=0.0),
            NumericalDataPoint(x_value="2023", y_value=30.0),
        ]
        ds_mixed = NumericalDataset(dataset_id="ds_bar_neg_mixed", title="Mixed", data_points=pts_mixed, source_record=sample_source)
        cfg_mixed = DeterministicChartRenderer.render_chart(ds_mixed, ChartType.BAR)
        res_mixed = NumericalInvariantChecker.verify_chart_data(ds_mixed, cfg_mixed)
        assert res_mixed.valid is True
        assert res_mixed.fidelity_score == 1.0

        # All negative values: [-50.0, -20.0, -10.0]
        pts_all_neg = [
            NumericalDataPoint(x_value="2021", y_value=-50.0),
            NumericalDataPoint(x_value="2022", y_value=-20.0),
            NumericalDataPoint(x_value="2023", y_value=-10.0),
        ]
        ds_all_neg = NumericalDataset(dataset_id="ds_bar_all_neg", title="All Neg", data_points=pts_all_neg, source_record=sample_source)
        cfg_all_neg = DeterministicChartRenderer.render_chart(ds_all_neg, ChartType.BAR)
        res_all_neg = NumericalInvariantChecker.verify_chart_data(ds_all_neg, cfg_all_neg)
        assert res_all_neg.valid is True
        assert res_all_neg.fidelity_score == 1.0

    def test_extreme_float_precision_scale_units_and_aggregations(self, sample_source):
        """Stress: Verifies Decimal precision preservation across extreme float scales."""
        # Very small values: 1e-9, 2e-9, 3e-9
        pts_micro = [
            NumericalDataPoint(x_value="Point_1", y_value=1e-9),
            NumericalDataPoint(x_value="Point_2", y_value=2e-9),
            NumericalDataPoint(x_value="Point_3", y_value=3e-9),
        ]
        ds_micro = NumericalDataset(dataset_id="ds_micro", title="Nanoscale", data_points=pts_micro, source_record=sample_source)
        # Sum must be 6e-9
        agg_sum = NumericalTransformer.aggregate(ds_micro, "sum")
        assert agg_sum == pytest.approx(6e-9, rel=1e-6)

        # Scale by NANO (multiplier 1e-9) -> points become [1.0, 2.0, 3.0]
        scaled = NumericalTransformer.scale_units(ds_micro, "NANO")
        assert scaled.data_points[0].y_value == pytest.approx(1.0, rel=1e-6)
        assert scaled.data_points[1].y_value == pytest.approx(2.0, rel=1e-6)
        assert scaled.data_points[2].y_value == pytest.approx(3.0, rel=1e-6)
        assert "NANO" in scaled.y_unit
