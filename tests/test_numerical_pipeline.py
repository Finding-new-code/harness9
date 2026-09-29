"""tests/test_numerical_pipeline.py — Test Suite for Deterministic Numerical Pipeline.

Verifies CSV/JSON ingestion, canonical cryptographic hashing, exact Decimal
transformations (aggregations, 100% percentage invariant via Largest Remainder Method,
growth rate zero-division trap, unit scaling), deterministic SVG chart generation,
and anti-distortion invariant checks.
"""

import math
import pytest
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from src.models.contracts import SourceRecord, SourceTier
from src.epistemic.numerical_pipeline import (
    ChartConfig,
    ChartElement,
    ChartType,
    DeterministicChartRenderer,
    NumericalDataPoint,
    NumericalDataset,
    NumericalDatasetIngestion,
    NumericalInvariantChecker,
    NumericalTransformer,
    NumericalVerificationResult,
)


@pytest.fixture
def sample_source_record() -> SourceRecord:
    return SourceRecord(
        source_id="src_bls_01",
        title="Bureau of Labor Statistics Annual Survey",
        url="https://www.bls.gov/data/survey_2025.csv",
        tier=SourceTier.PRIMARY_SOURCE,
        reliability_score=0.98,
        domain_authority=0.95,
        publisher="U.S. Bureau of Labor Statistics",
    )


@pytest.fixture
def sample_csv_text() -> str:
    return """year,revenue,category
2020,"$10,000,000",Software
2021,"$15,500,000",Software
2022,"$22,000,000",Software
2023,"$35,000,000",Hardware
2024,"$50,000,000",Services
"""


class TestNumericalDatasetIngestion:
    """Tests CSV, JSON parsing, validation, and SHA-256 canonical integrity."""

    def test_from_csv_parsing_and_canonical_hash(self, sample_csv_text, sample_source_record):
        dataset = NumericalDatasetIngestion.from_csv(
            csv_text=sample_csv_text,
            dataset_id="ds_revenue_annual",
            title="Annual Tech Revenue",
            x_col="year",
            y_col="revenue",
            source_record=sample_source_record,
            label_col="category",
            y_unit="USD",
        )

        assert dataset.dataset_id == "ds_revenue_annual"
        assert len(dataset.data_points) == 5
        assert dataset.data_points[0].x_value == 2020
        assert dataset.data_points[0].y_value == 10000000.0
        assert dataset.data_points[0].label == "Software"
        assert dataset.data_points[4].x_value == 2024
        assert dataset.data_points[4].y_value == 50000000.0
        assert len(dataset.dataset_sha256) == 64
        assert NumericalDatasetIngestion.verify_checksum(dataset) is True

    def test_checksum_fails_on_tampered_data(self, sample_csv_text, sample_source_record):
        dataset = NumericalDatasetIngestion.from_csv(
            csv_text=sample_csv_text,
            dataset_id="ds_revenue_annual",
            title="Annual Tech Revenue",
            x_col="year",
            y_col="revenue",
            source_record=sample_source_record,
        )
        assert NumericalDatasetIngestion.verify_checksum(dataset) is True

        # Mutate point
        dataset.data_points[0].y_value = 99999999.0
        assert NumericalDatasetIngestion.verify_checksum(dataset) is False

    def test_from_json_records(self, sample_source_record):
        records = [
            {"node": "Alpha", "latency_ms": 12.4},
            {"node": "Beta", "latency_ms": 18.2},
            {"node": "Gamma", "latency_ms": "9.8%"},
        ]
        dataset = NumericalDatasetIngestion.from_json_records(
            records=records,
            dataset_id="ds_latency",
            title="Cluster Latency",
            x_key="node",
            y_key="latency_ms",
            source_record=sample_source_record,
            y_unit="ms",
        )
        assert len(dataset.data_points) == 3
        assert dataset.data_points[0].x_value == "Alpha"
        assert dataset.data_points[0].y_value == 12.4
        assert dataset.data_points[2].y_value == 9.8

    def test_rejection_of_non_finite_values(self):
        with pytest.raises(ValueError, match="finite numerical value"):
            NumericalDataPoint(x_value="Test", y_value=float("nan"))

        with pytest.raises(ValueError, match="finite numerical value"):
            NumericalDataPoint(x_value="Test", y_value=float("inf"))

    def test_rejection_of_missing_columns(self, sample_source_record):
        csv_missing = "year,val\n2020,100"
        with pytest.raises(ValueError, match="Missing required columns"):
            NumericalDatasetIngestion.from_csv(
                csv_text=csv_missing,
                dataset_id="ds_err",
                title="Err",
                x_col="date",
                y_col="revenue",
                source_record=sample_source_record,
            )


class TestNumericalTransformer:
    """Tests exact Decimal transformations, aggregations, 100% share invariant, and growth."""

    @pytest.fixture
    def test_dataset(self, sample_source_record) -> NumericalDataset:
        points = [
            NumericalDataPoint(x_value=1, y_value=10.0),
            NumericalDataPoint(x_value=2, y_value=20.0),
            NumericalDataPoint(x_value=3, y_value=30.0),
            NumericalDataPoint(x_value=4, y_value=40.0),
        ]
        return NumericalDataset(
            dataset_id="ds_math",
            title="Math Test",
            data_points=points,
            source_record=sample_source_record,
        )

    def test_aggregations(self, test_dataset):
        assert NumericalTransformer.aggregate(test_dataset, "sum") == 100.0
        assert NumericalTransformer.aggregate(test_dataset, "mean") == 25.0
        assert NumericalTransformer.aggregate(test_dataset, "min") == 10.0
        assert NumericalTransformer.aggregate(test_dataset, "max") == 40.0
        # Median of [10, 20, 30, 40] is (20 + 30) / 2 = 25.0
        assert NumericalTransformer.aggregate(test_dataset, "median") == 25.0

    def test_percentage_shares_largest_remainder_100_percent_invariant(self, sample_source_record):
        # 3 items of equal size: 10, 10, 10 -> each is 1/3 (33.333...%)
        # Standard round(2) gives 33.33 + 33.33 + 33.33 = 99.99% (violation!)
        # Largest Remainder Method MUST guarantee exactly 100.00%
        pts = [
            NumericalDataPoint(x_value="A", y_value=10.0),
            NumericalDataPoint(x_value="B", y_value=10.0),
            NumericalDataPoint(x_value="C", y_value=10.0),
        ]
        ds = NumericalDataset(
            dataset_id="ds_equal_thirds",
            title="Thirds",
            data_points=pts,
            source_record=sample_source_record,
        )

        shares = NumericalTransformer.calculate_percentage_shares(ds, decimal_places=2)
        assert len(shares) == 3

        total_percentage = sum(s[1] for s in shares)
        assert total_percentage == pytest.approx(100.00, abs=1e-6)
        # One share will be 33.34, others 33.33
        assert sorted([s[1] for s in shares]) == [33.33, 33.33, 33.34]

    def test_growth_rate_calculation(self):
        # 10 to 30 -> +200.0%
        assert NumericalTransformer.calculate_growth_rate(10.0, 30.0) == 200.0
        # 40 to 10 -> -75.0%
        assert NumericalTransformer.calculate_growth_rate(40.0, 10.0) == -75.0

    def test_growth_rate_zero_baseline_division_guard(self):
        with pytest.raises(ValueError, match="Cannot calculate percentage growth rate from a zero baseline"):
            NumericalTransformer.calculate_growth_rate(0.0, 50.0)

    def test_unit_scaling(self, test_dataset):
        # Scale 10, 20, 30, 40 to K (factor 1000)
        scaled_ds = NumericalTransformer.scale_units(test_dataset, "K")
        assert scaled_ds.data_points[0].y_value == 0.01
        assert scaled_ds.data_points[3].y_value == 0.04
        assert "K" in scaled_ds.y_unit


class TestDeterministicChartRenderer:
    """Tests coordinate projection, reproducible cryptographic hashing, and baseline zero."""

    @pytest.fixture
    def chart_dataset(self, sample_source_record) -> NumericalDataset:
        pts = [
            NumericalDataPoint(x_value=1950, y_value=92.0),
            NumericalDataPoint(x_value=1960, y_value=95.0),
            NumericalDataPoint(x_value=1970, y_value=98.0),
        ]
        return NumericalDataset(
            dataset_id="ds_perf",
            title="System Performance",
            data_points=pts,
            source_record=sample_source_record,
        )

    def test_renderer_100x_determinism(self, chart_dataset):
        c1 = DeterministicChartRenderer.render_chart(chart_dataset, ChartType.BAR)
        c2 = DeterministicChartRenderer.render_chart(chart_dataset, ChartType.BAR)
        assert c1.chart_sha256 == c2.chart_sha256
        assert c1.rendered_svg == c2.rendered_svg

    def test_bar_chart_zero_baseline_enforcement(self, chart_dataset):
        # Dataset has min=92.0. By default, bar chart must enforce Y_min = 0.0
        cfg = DeterministicChartRenderer.render_chart(
            chart_dataset,
            ChartType.BAR,
            allow_truncated_baseline=False,
        )
        assert cfg.y_axis_min == 0.0
        assert cfg.has_truncated_baseline is False
        assert cfg.baseline_warning_required is False

    def test_bar_chart_truncated_baseline_with_disclosure(self, chart_dataset):
        cfg = DeterministicChartRenderer.render_chart(
            chart_dataset,
            ChartType.BAR,
            allow_truncated_baseline=True,
        )
        assert cfg.y_axis_min > 0.0
        assert cfg.has_truncated_baseline is True
        assert cfg.baseline_warning_required is True
        assert "AXIS TRUNCATED" in cfg.rendered_svg


class TestNumericalInvariantChecker:
    """Tests anti-distortion validation, coordinate fidelity, and non-averaging checks."""

    @pytest.fixture
    def valid_chart_setup(self, sample_source_record) -> Tuple[NumericalDataset, ChartConfig]:
        pts = [
            NumericalDataPoint(x_value=1, y_value=10.0),
            NumericalDataPoint(x_value=2, y_value=20.0),
            NumericalDataPoint(x_value=3, y_value=30.0),
        ]
        ds = NumericalDataset(
            dataset_id="ds_inv",
            title="Integrity Test",
            data_points=pts,
            source_record=sample_source_record,
        )
        cfg = DeterministicChartRenderer.render_chart(ds, ChartType.BAR)
        return ds, cfg

    def test_valid_chart_passes_all_invariants(self, valid_chart_setup):
        ds, cfg = valid_chart_setup
        res = NumericalInvariantChecker.verify_chart_data(ds, cfg)
        assert res.valid is True
        assert res.fidelity_score == 1.0
        assert len(res.violations) == 0

    def test_detect_unjustified_non_zero_baseline(self, valid_chart_setup):
        ds, cfg = valid_chart_setup
        # Tamper cfg to non-zero baseline without setting has_truncated_baseline
        bad_cfg = cfg.model_copy(update={"y_axis_min": 5.0, "has_truncated_baseline": False})
        res = NumericalInvariantChecker.verify_chart_data(ds, bad_cfg)
        assert res.valid is False
        assert any("UNJUSTIFIED_NON_ZERO_BASELINE" in v for v in res.violations)

    def test_detect_coordinate_fidelity_distortion(self, valid_chart_setup):
        ds, cfg = valid_chart_setup
        # Distort element screen height
        mutated_elements = list(cfg.elements)
        orig_sc = dict(mutated_elements[0].screen_coords)
        orig_sc["height"] = orig_sc["height"] + 50.0  # Big distortion
        mutated_elements[0] = mutated_elements[0].model_copy(update={"screen_coords": orig_sc})

        bad_cfg = cfg.model_copy(update={"elements": mutated_elements})
        res = NumericalInvariantChecker.verify_chart_data(ds, bad_cfg)
        assert res.valid is False
        assert any("COORDINATE_FIDELITY_ERROR" in v for v in res.violations)

    def test_contradiction_preservation_warning(self, sample_source_record):
        # Two different conflicting reports for x=1947
        pts = [
            NumericalDataPoint(x_value=1947, y_value=12500.0, label="Report A"),
            NumericalDataPoint(x_value=1947, y_value=15000.0, label="Report B"),
        ]
        ds = NumericalDataset(
            dataset_id="ds_contra",
            title="Contradictory Estimates",
            data_points=pts,
            source_record=sample_source_record,
        )
        cfg = DeterministicChartRenderer.render_chart(ds, ChartType.SCATTER)
        res = NumericalInvariantChecker.verify_chart_data(ds, cfg)
        assert res.valid is True
        assert any("Non-averaging policy active" in w for w in res.warnings)
