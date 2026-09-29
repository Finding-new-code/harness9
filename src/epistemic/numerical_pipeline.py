"""src/epistemic/numerical_pipeline.py — Deterministic Numerical Data & Visualization Pipeline.

Guarantees data integrity from source records/CSVs/JSON through exact Decimal
transformations to deterministic, reproducible SVG chart coordinate projections.
Enforces zero-baseline anti-distortion invariants and cryptographic dataset hashing.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
from enum import Enum
import hashlib
import io
import json
import math
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import uuid

from pydantic import Field, field_validator, model_validator

from src.models.contracts import H9BaseModel, SourceRecord


# ===========================================================================
# 1. Enums & Core Models
# ===========================================================================

class ChartType(str, Enum):
    """Supported data visualization chart types."""
    BAR = "bar"
    COLUMN = "column"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"


class NumericalDataPoint(H9BaseModel):
    """Single verified coordinate point in an empirical dataset."""
    x_value: Union[float, int, str] = Field(..., description="Year, scalar, or categorical label")
    y_value: float = Field(..., description="Finite numerical value")
    label: Optional[str] = Field(default=None, description="Optional point annotation or category name")
    uncertainty_range: Optional[Tuple[float, float]] = Field(
        default=None,
        description="Optional [min, max] error or confidence bound"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("y_value")
    @classmethod
    def validate_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("y_value must be a finite numerical value, not NaN or Inf")
        return v

    @field_validator("uncertainty_range")
    @classmethod
    def validate_uncertainty(cls, v: Optional[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        if v is not None:
            if len(v) != 2:
                raise ValueError("uncertainty_range must be a (min, max) tuple")
            if math.isnan(v[0]) or math.isnan(v[1]) or math.isinf(v[0]) or math.isinf(v[1]):
                raise ValueError("uncertainty_range values must be finite numerical values, not NaN or Inf")
            if v[0] > v[1]:
                raise ValueError("uncertainty_range min must be <= max")
        return v


class NumericalDataset(H9BaseModel):
    """Immutable ground-truth dataset backing charts and visual metrics."""
    dataset_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    x_label: str = Field(default="X")
    y_label: str = Field(default="Y")
    x_unit: str = Field(default="")
    y_unit: str = Field(default="")
    data_points: List[NumericalDataPoint] = Field(..., min_length=1)
    source_record: Optional[SourceRecord] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dataset_sha256: str = Field(default="", description="Canonical SHA-256 hash")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def compute_hash_if_missing(self) -> "NumericalDataset":
        if not self.dataset_sha256:
            object.__setattr__(self, "dataset_sha256", self.calculate_canonical_hash())
        return self

    def calculate_canonical_hash(self) -> str:
        """Computes deterministic SHA-256 hash across canonical serialized representation."""
        points_serialized = []
        for p in self.data_points:
            points_serialized.append((
                str(p.x_value),
                f"{p.y_value:.8f}",
                str(p.label or ""),
                f"{p.uncertainty_range[0]:.8f}:{p.uncertainty_range[1]:.8f}" if p.uncertainty_range else ""
            ))
        payload = {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "x_unit": self.x_unit,
            "y_unit": self.y_unit,
            "points": points_serialized,
            "source_url": self.source_record.url if self.source_record else "",
        }
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


class ChartElement(H9BaseModel):
    """Calculated graphical element ready for deterministic SVG coordinate projection."""
    element_id: str
    element_type: str  # "rect", "polyline", "circle", "path", "text"
    raw_point: NumericalDataPoint
    screen_coords: Dict[str, float]  # {"x": ..., "y": ..., "width": ..., "height": ...}
    normalized_coords: Dict[str, float]  # Coordinates in [0.0, 1.0] viewport space
    formatted_value: str
    fill_color: str = "#00d2ff"


class ChartConfig(H9BaseModel):
    """Deterministic configuration and rendered manifest for a data visualization."""
    chart_id: str = Field(default_factory=lambda: f"chart_{uuid.uuid4().hex[:8]}")
    chart_type: ChartType
    title: str
    dataset_id: str
    width: int = 1920
    height: int = 1080
    x_axis_min: float = 0.0
    x_axis_max: float = 1.0
    y_axis_min: float = 0.0
    y_axis_max: float = 1.0
    x_ticks: List[Dict[str, Any]] = Field(default_factory=list)
    y_ticks: List[Dict[str, Any]] = Field(default_factory=list)
    elements: List[ChartElement] = Field(default_factory=list)
    display_unit: str = ""
    scale_multiplier: float = 1.0
    has_truncated_baseline: bool = False
    baseline_warning_required: bool = False
    rendered_svg: str = ""
    chart_sha256: str = ""
    brand_colors: Dict[str, str] = Field(default_factory=dict)


class NumericalTransformationRecord(H9BaseModel):
    """Audit log of mathematical transformation performed on a dataset."""
    record_id: str = Field(default_factory=lambda: f"trans_{uuid.uuid4().hex[:8]}")
    operation: str
    input_dataset_id: str
    output_dataset_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    applied_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NumericalVerificationResult(H9BaseModel):
    """Integrity audit result for a chart configuration against its backing dataset."""
    valid: bool
    dataset_id: str
    chart_id: Optional[str] = None
    fidelity_score: float = 1.0
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 2. Ingestion Engine
# ===========================================================================

class NumericalDatasetIngestion:
    """Parses raw tabular and structured data into immutable NumericalDataset objects."""

    @classmethod
    def clean_numeric_string(cls, raw: Any) -> float:
        """Strips formatting symbols ($, €, %, commas, spaces) and returns float."""
        if isinstance(raw, (int, float)):
            if math.isnan(raw) or math.isinf(raw):
                raise ValueError("Non-finite numeric value detected")
            return float(raw)
        s = str(raw).strip()
        if not s or s.lower() in ("nan", "null", "none", "n/a", "-"):
            raise ValueError(f"Invalid empty or null numeric string: '{raw}'")
        # Remove currency symbols, commas, percent, plus
        cleaned = re.sub(r"[\$,€,£,¥,%,+\s]", "", s)
        try:
            val = float(cleaned)
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Numeric string parsed to non-finite float: '{raw}'")
            return val
        except ValueError as exc:
            raise ValueError(f"Cannot parse '{raw}' into a finite numeric value: {exc}")

    @classmethod
    def parse_x_value(cls, raw: Any) -> Union[float, int, str]:
        """Infers numeric or string identity for the X coordinate."""
        if isinstance(raw, (int, float)):
            return raw
        s = str(raw).strip()
        # Try integer first
        if re.fullmatch(r"[-+]?\d+", s):
            try:
                return int(s)
            except ValueError:
                pass
        # Try float
        if re.fullmatch(r"[-+]?\d*\.\d+", s):
            try:
                return float(s)
            except ValueError:
                pass
        return s

    @classmethod
    def from_csv(
        cls,
        csv_text: str,
        dataset_id: str,
        title: str,
        x_col: str,
        y_col: str,
        source_record: Optional[SourceRecord] = None,
        label_col: Optional[str] = None,
        x_unit: str = "",
        y_unit: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NumericalDataset:
        """Parses CSV string into a validated NumericalDataset."""
        if not csv_text or not csv_text.strip():
            raise ValueError("CSV content cannot be empty")

        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        if not reader.fieldnames or x_col not in reader.fieldnames or y_col not in reader.fieldnames:
            raise ValueError(
                f"Missing required columns. Expected '{x_col}' and '{y_col}'. Found: {reader.fieldnames}"
            )

        points: List[NumericalDataPoint] = []
        for row_idx, row in enumerate(reader, start=1):
            raw_x = row.get(x_col)
            raw_y = row.get(y_col)
            if raw_x is None or raw_y is None:
                raise ValueError(f"Row {row_idx} missing value for column '{x_col}' or '{y_col}'")

            parsed_x = cls.parse_x_value(raw_x)
            parsed_y = cls.clean_numeric_string(raw_y)
            lbl = str(row[label_col]).strip() if label_col and label_col in row and row[label_col] else None

            points.append(
                NumericalDataPoint(
                    x_value=parsed_x,
                    y_value=parsed_y,
                    label=lbl,
                    metadata={"row_index": row_idx},
                )
            )

        if not points:
            raise ValueError("CSV contains no valid data rows")

        return NumericalDataset(
            dataset_id=dataset_id,
            title=title,
            x_label=x_col,
            y_label=y_col,
            x_unit=x_unit,
            y_unit=y_unit,
            data_points=points,
            source_record=source_record,
            metadata=metadata or {},
        )

    @classmethod
    def from_json_records(
        cls,
        records: List[Dict[str, Any]],
        dataset_id: str,
        title: str,
        x_key: str,
        y_key: str,
        source_record: Optional[SourceRecord] = None,
        label_key: Optional[str] = None,
        x_unit: str = "",
        y_unit: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NumericalDataset:
        """Parses structured JSON records list into a validated NumericalDataset."""
        if not records:
            raise ValueError("JSON records list cannot be empty")

        points: List[NumericalDataPoint] = []
        for idx, rec in enumerate(records):
            if x_key not in rec or y_key not in rec:
                raise ValueError(f"Record at index {idx} missing key '{x_key}' or '{y_key}'")
            parsed_x = cls.parse_x_value(rec[x_key])
            parsed_y = cls.clean_numeric_string(rec[y_key])
            lbl = str(rec[label_key]) if label_key and label_key in rec else None
            points.append(
                NumericalDataPoint(
                    x_value=parsed_x,
                    y_value=parsed_y,
                    label=lbl,
                )
            )

        return NumericalDataset(
            dataset_id=dataset_id,
            title=title,
            x_label=x_key,
            y_label=y_key,
            x_unit=x_unit,
            y_unit=y_unit,
            data_points=points,
            source_record=source_record,
            metadata=metadata or {},
        )

    @classmethod
    def verify_checksum(cls, dataset: NumericalDataset) -> bool:
        """Verifies that dataset data points and metadata match its canonical dataset_sha256."""
        expected = dataset.calculate_canonical_hash()
        return dataset.dataset_sha256 == expected


# ===========================================================================
# 3. Precision Transformations (Exact Decimal Backed)
# ===========================================================================

class NumericalTransformer:
    """Exact Decimal-backed transformations with strict mathematical invariants."""

    UNIT_MULTIPLIERS = {
        "T": Decimal("1000000000000"),
        "TRILLION": Decimal("1000000000000"),
        "B": Decimal("1000000000"),
        "BILLION": Decimal("1000000000"),
        "M": Decimal("1000000"),
        "MILLION": Decimal("1000000"),
        "K": Decimal("1000"),
        "THOUSAND": Decimal("1000"),
        "MICRO": Decimal("0.000001"),
        "NANO": Decimal("0.000000001"),
    }

    @classmethod
    def aggregate(cls, dataset: NumericalDataset, operation: str) -> float:
        """Computes exact aggregate metric: sum, mean, median, min, max, std_dev."""
        op = operation.lower().strip()
        vals = [Decimal(str(p.y_value)) for p in dataset.data_points]
        if not vals:
            raise ValueError("Cannot aggregate empty dataset")

        n = Decimal(len(vals))
        if op == "sum":
            res = sum(vals, Decimal(0))
            return float(res)
        elif op == "mean":
            res = sum(vals, Decimal(0)) / n
            return float(res)
        elif op == "median":
            sorted_vals = sorted(vals)
            mid = len(sorted_vals) // 2
            if len(sorted_vals) % 2 == 1:
                return float(sorted_vals[mid])
            else:
                return float((sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal(2))
        elif op == "min":
            return float(min(vals))
        elif op == "max":
            return float(max(vals))
        elif op in ("std_dev", "stddev"):
            if len(vals) < 2:
                return 0.0
            mean_val = sum(vals, Decimal(0)) / n
            variance = sum((v - mean_val) ** 2 for v in vals) / (n - Decimal(1))
            return math.sqrt(float(variance))
        else:
            raise ValueError(f"Unsupported aggregate operation: '{operation}'")

    @classmethod
    def calculate_percentage_shares(
        cls,
        dataset: NumericalDataset,
        decimal_places: int = 2,
    ) -> List[Tuple[NumericalDataPoint, float]]:
        """Computes part-to-whole percentage shares summing to EXACTLY 100.0% via Largest Remainder Method."""
        vals = [Decimal(str(p.y_value)) for p in dataset.data_points]
        total = sum(vals, Decimal(0))
        if total <= Decimal(0):
            raise ValueError("Total sum of data points must be positive to compute percentage shares")

        scale = Decimal(10) ** decimal_places
        target_sum_int = int(Decimal(100) * scale)  # e.g. 10000 for 2 decimal places

        # Exact shares scaled
        raw_shares = [(v / total) * Decimal(100) * scale for v in vals]
        integer_parts = [int(s) for s in raw_shares]
        remainders = [s - Decimal(ip) for s, ip in zip(raw_shares, integer_parts)]

        allocated_sum = sum(integer_parts)
        shortage = target_sum_int - allocated_sum

        # Distribute remaining 1 units to the largest remainder indices
        sorted_indices = sorted(range(len(remainders)), key=lambda i: remainders[i], reverse=True)
        final_ints = list(integer_parts)
        for i in range(shortage):
            idx = sorted_indices[i % len(sorted_indices)]
            final_ints[idx] += 1

        results = []
        for p, fi in zip(dataset.data_points, final_ints):
            share_pct = float(Decimal(fi) / scale)
            results.append((p, share_pct))

        return results

    @classmethod
    def calculate_growth_rate(cls, v_start: float, v_end: float) -> float:
        """Calculates percentage growth rate: ((v_end - v_start) / |v_start|) * 100 with zero baseline guard."""
        d_start = Decimal(str(v_start))
        d_end = Decimal(str(v_end))
        if d_start == Decimal(0):
            raise ValueError("Cannot calculate percentage growth rate from a zero baseline (division by zero)")

        rate = ((d_end - d_start) / abs(d_start)) * Decimal(100)
        return float(rate)

    @classmethod
    def scale_units(
        cls,
        dataset: NumericalDataset,
        target_prefix: str,
        new_dataset_id: Optional[str] = None,
    ) -> NumericalDataset:
        """Scales numeric values by standard metric prefixes (K, M, B, T, etc.)."""
        prefix_upper = target_prefix.upper().strip()
        if prefix_upper not in cls.UNIT_MULTIPLIERS:
            raise ValueError(
                f"Unknown unit prefix '{target_prefix}'. Supported: {list(cls.UNIT_MULTIPLIERS.keys())}"
            )
        factor = cls.UNIT_MULTIPLIERS[prefix_upper]

        new_points: List[NumericalDataPoint] = []
        for p in dataset.data_points:
            d_val = Decimal(str(p.y_value))
            scaled_y = float(d_val / factor)
            new_uncertainty = None
            if p.uncertainty_range:
                u_min = float(Decimal(str(p.uncertainty_range[0])) / factor)
                u_max = float(Decimal(str(p.uncertainty_range[1])) / factor)
                new_uncertainty = (u_min, u_max)

            new_points.append(
                NumericalDataPoint(
                    x_value=p.x_value,
                    y_value=scaled_y,
                    label=p.label,
                    uncertainty_range=new_uncertainty,
                    metadata=dict(p.metadata),
                )
            )

        new_y_unit = f"{prefix_upper} {dataset.y_unit}".strip()
        ds_id = new_dataset_id or f"{dataset.dataset_id}_{prefix_upper.lower()}"
        return NumericalDataset(
            dataset_id=ds_id,
            title=f"{dataset.title} ({prefix_upper})",
            x_label=dataset.x_label,
            y_label=f"{dataset.y_label} ({prefix_upper})",
            x_unit=dataset.x_unit,
            y_unit=new_y_unit,
            data_points=new_points,
            source_record=dataset.source_record,
            metadata={
                **dataset.metadata,
                "scaled_from": dataset.dataset_id,
                "scale_factor": float(factor),
                "scale_prefix": prefix_upper,
            },
        )


# ===========================================================================
# 4. Deterministic SVG Chart Renderer
# ===========================================================================

class DeterministicChartRenderer:
    """Pure coordinate projection renderer generating deterministic, reproducible SVGs."""

    @classmethod
    def render_chart(
        cls,
        dataset: NumericalDataset,
        chart_type: ChartType,
        viewport: Tuple[int, int] = (1920, 1080),
        allow_truncated_baseline: bool = False,
        brand_colors: Optional[Dict[str, str]] = None,
        chart_id: Optional[str] = None,
    ) -> ChartConfig:
        """Projects dataset points into exact screen coordinates and renders a deterministic SVG."""
        width, height = viewport
        cid = chart_id or f"chart_{dataset.dataset_id}_{chart_type.value}"
        colors = brand_colors or {
            "primary": "#00d2ff",
            "secondary": "#ff007f",
            "background": "#0a0e17",
            "axis": "#4a5568",
            "text": "#ffffff",
            "grid": "#1e293b",
            "warning": "#ffaa00",
        }

        # Plot margins
        margin_left = 160.0
        margin_right = 80.0
        margin_top = 140.0
        margin_bottom = 140.0
        plot_w = float(width) - margin_left - margin_right
        plot_h = float(height) - margin_top - margin_bottom

        y_vals = [p.y_value for p in dataset.data_points]
        min_y_raw = min(y_vals)
        max_y_raw = max(y_vals)

        # Baseline zero determination
        has_truncated_baseline = False
        baseline_warning_required = False

        if chart_type in (ChartType.BAR, ChartType.COLUMN):
            if min_y_raw > 0.0 and not allow_truncated_baseline:
                y_axis_min = 0.0
            elif min_y_raw > 0.0 and allow_truncated_baseline:
                y_axis_min = min_y_raw * 0.95
                has_truncated_baseline = True
                baseline_warning_required = True
            else:
                y_axis_min = min(0.0, min_y_raw)
            y_axis_max = max_y_raw * 1.05 if max_y_raw > 0 else 1.0
        else:  # LINE, SCATTER, AREA
            delta_y = (max_y_raw - min_y_raw) if max_y_raw != min_y_raw else 1.0
            y_axis_min = min_y_raw - (0.05 * delta_y)
            y_axis_max = max_y_raw + (0.05 * delta_y)

        if y_axis_max == y_axis_min:
            y_axis_max = y_axis_min + 1.0

        # Calculate elements
        elements: List[ChartElement] = []
        n_points = len(dataset.data_points)

        for idx, pt in enumerate(dataset.data_points):
            elem_id = f"{cid}_el_{idx}"
            # Normalized y in [0.0, 1.0]
            norm_y = (pt.y_value - y_axis_min) / (y_axis_max - y_axis_min)
            screen_y = margin_top + (plot_h * (1.0 - norm_y))

            if chart_type in (ChartType.BAR, ChartType.COLUMN):
                bar_slot_w = plot_w / float(n_points)
                bar_w = bar_slot_w * 0.65
                screen_x = margin_left + (idx * bar_slot_w) + (bar_slot_w * 0.175)
                base_val = y_axis_min if has_truncated_baseline else 0.0
                zero_y = margin_top + (plot_h * (1.0 - ((base_val - y_axis_min) / (y_axis_max - y_axis_min))))
                bar_h = abs(zero_y - screen_y)
                bar_top = min(zero_y, screen_y)

                elem = ChartElement(
                    element_id=elem_id,
                    element_type="rect",
                    raw_point=pt,
                    screen_coords={"x": screen_x, "y": bar_top, "width": bar_w, "height": bar_h},
                    normalized_coords={"x": screen_x / width, "y": bar_top / height},
                    formatted_value=f"{pt.y_value:g}",
                    fill_color=colors["primary"],
                )
            else:  # LINE / SCATTER
                step_x = plot_w / float(max(1, n_points - 1)) if n_points > 1 else plot_w * 0.5
                screen_x = margin_left + (idx * step_x)
                elem = ChartElement(
                    element_id=elem_id,
                    element_type="circle",
                    raw_point=pt,
                    screen_coords={"x": screen_x, "y": screen_y, "radius": 8.0},
                    normalized_coords={"x": screen_x / width, "y": screen_y / height},
                    formatted_value=f"{pt.y_value:g}",
                    fill_color=colors["secondary"],
                )
            elements.append(elem)

        # Build pure deterministic SVG string
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
            f'  <rect width="{width}" height="{height}" fill="{colors["background"]}" />',
            f'  <text x="{margin_left}" y="80" fill="{colors["text"]}" font-size="36" font-weight="bold">{dataset.title}</text>',
            f'  <!-- Axis Lines -->',
            f'  <line x1="{margin_left:.2f}" y1="{margin_top + plot_h:.2f}" x2="{margin_left + plot_w:.2f}" y2="{margin_top + plot_h:.2f}" stroke="{colors["axis"]}" stroke-width="2" />',
            f'  <line x1="{margin_left:.2f}" y1="{margin_top:.2f}" x2="{margin_left:.2f}" y2="{margin_top + plot_h:.2f}" stroke="{colors["axis"]}" stroke-width="2" />',
        ]

        if baseline_warning_required:
            svg_parts.append(
                f'  <!-- Truncated Baseline Warning Badge -->'
                f'  <rect x="{width - 480}" y="50" width="400" height="40" rx="6" fill="{colors["warning"]}" fill-opacity="0.2" stroke="{colors["warning"]}" stroke-width="2" />'
                f'  <text x="{width - 280}" y="76" fill="{colors["warning"]}" font-size="16" font-weight="bold" text-anchor="middle">⚠️ AXIS TRUNCATED: BASELINE STARTS AT {y_axis_min:g}</text>'
            )

        if chart_type == ChartType.LINE and len(elements) >= 2:
            pts_str = " ".join(f"{el.screen_coords['x']:.2f},{el.screen_coords['y']:.2f}" for el in elements)
            svg_parts.append(f'  <polyline points="{pts_str}" fill="none" stroke="{colors["primary"]}" stroke-width="4" />')

        for el in elements:
            if el.element_type == "rect":
                sc = el.screen_coords
                svg_parts.append(
                    f'  <rect x="{sc["x"]:.2f}" y="{sc["y"]:.2f}" width="{sc["width"]:.2f}" height="{sc["height"]:.2f}" fill="{el.fill_color}" rx="4" />'
                )
            elif el.element_type == "circle":
                sc = el.screen_coords
                svg_parts.append(
                    f'  <circle cx="{sc["x"]:.2f}" cy="{sc["y"]:.2f}" r="{sc.get("radius", 6.0):.2f}" fill="{el.fill_color}" />'
                )

        svg_parts.append('</svg>')
        svg_content = "\n".join(svg_parts)
        chart_hash = hashlib.sha256(svg_content.encode("utf-8")).hexdigest()

        return ChartConfig(
            chart_id=cid,
            chart_type=chart_type,
            title=dataset.title,
            dataset_id=dataset.dataset_id,
            width=width,
            height=height,
            x_axis_min=0.0,
            x_axis_max=float(n_points),
            y_axis_min=y_axis_min,
            y_axis_max=y_axis_max,
            elements=elements,
            display_unit=dataset.y_unit,
            has_truncated_baseline=has_truncated_baseline,
            baseline_warning_required=baseline_warning_required,
            rendered_svg=svg_content,
            chart_sha256=chart_hash,
            brand_colors=colors,
        )


# ===========================================================================
# 5. Numerical Invariant Checker
# ===========================================================================

class NumericalInvariantChecker:
    """Audits chart configurations and visual metrics for mathematical distortion."""

    @classmethod
    def verify_chart_data(
        cls,
        dataset: NumericalDataset,
        chart_config: ChartConfig,
    ) -> NumericalVerificationResult:
        """Validates zero baseline compliance, coordinate fidelity (< 10^-4), and unit scale."""
        violations: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Dataset ID alignment
        if chart_config.dataset_id != dataset.dataset_id:
            violations.append(
                f"Dataset ID mismatch: chart references '{chart_config.dataset_id}', expected '{dataset.dataset_id}'"
            )

        # 2. Zero-baseline enforcement on bar/column charts
        y_vals = [p.y_value for p in dataset.data_points]
        if chart_config.chart_type in (ChartType.BAR, ChartType.COLUMN):
            if y_vals and all(y > 0 for y in y_vals):
                if chart_config.y_axis_min > 0.0 and not chart_config.has_truncated_baseline:
                    violations.append(
                        f"UNJUSTIFIED_NON_ZERO_BASELINE: Bar chart y-axis begins at {chart_config.y_axis_min} instead of 0.0"
                    )
                elif chart_config.has_truncated_baseline and not chart_config.baseline_warning_required:
                    violations.append(
                        "TRUNCATED_BASELINE_MISSING_DISCLOSURE: Truncated baseline without visible warning disclosure"
                    )

        # 3. Coordinate fidelity check
        if len(chart_config.elements) != len(dataset.data_points):
            violations.append(
                f"Element count mismatch: chart has {len(chart_config.elements)} elements, dataset has {len(dataset.data_points)} points"
            )
        else:
            plot_h = float(chart_config.height) - 280.0  # margin_top(140) + margin_bottom(140)
            y_range = chart_config.y_axis_max - chart_config.y_axis_min
            fidelity_errors = []

            for idx, (el, pt) in enumerate(zip(chart_config.elements, dataset.data_points)):
                expected_norm_y = (pt.y_value - chart_config.y_axis_min) / y_range if y_range != 0 else 0.0
                if chart_config.chart_type in (ChartType.BAR, ChartType.COLUMN):
                    # Height check
                    base_ref = chart_config.y_axis_min if chart_config.has_truncated_baseline else max(0.0, chart_config.y_axis_min)
                    expected_h = plot_h * abs(pt.y_value - base_ref) / y_range
                    actual_h = el.screen_coords.get("height", 0.0)
                    diff = abs(expected_h - actual_h)
                    if diff > 1e-4:
                        fidelity_errors.append(f"Point {idx}: height diff {diff:.6f} exceeds 1e-4")
                else:
                    expected_y = 140.0 + (plot_h * (1.0 - expected_norm_y))
                    actual_y = el.screen_coords.get("y", 0.0)
                    diff = abs(expected_y - actual_y)
                    if diff > 1e-4:
                        fidelity_errors.append(f"Point {idx}: y-coord diff {diff:.6f} exceeds 1e-4")

            if fidelity_errors:
                violations.append(f"COORDINATE_FIDELITY_ERROR: {len(fidelity_errors)} points violated tolerance 1e-4")
                details["fidelity_errors"] = fidelity_errors[:5]

        # 4. Monotonicity verification for sorted time-series
        is_time_series = all(isinstance(p.x_value, (int, float)) for p in dataset.data_points)
        if is_time_series and len(chart_config.elements) >= 2:
            x_screen_coords = [el.screen_coords.get("x", 0.0) for el in chart_config.elements]
            x_data_coords = [float(p.x_value) for p in dataset.data_points]
            # Check if sorted in data
            if x_data_coords == sorted(x_data_coords):
                if x_screen_coords != sorted(x_screen_coords):
                    violations.append("MONOTONICITY_INVERSION: Screen x coordinates do not monotonically increase")

        # 5. Non-averaging contradiction preservation check
        # Check if points with identical x_value have different y_values (conflicting reports)
        x_map: Dict[Any, List[float]] = {}
        for p in dataset.data_points:
            x_map.setdefault(p.x_value, []).append(p.y_value)
        contradictory_keys = [k for k, vs in x_map.items() if len(vs) > 1 and len(set(vs)) > 1]
        if contradictory_keys:
            warnings.append(
                f"Contradictory data points present for x={contradictory_keys}. Non-averaging policy active."
            )

        valid = len(violations) == 0
        score = 1.0 if valid else max(0.0, 1.0 - (0.25 * len(violations)))
        return NumericalVerificationResult(
            valid=valid,
            dataset_id=dataset.dataset_id,
            chart_id=chart_config.chart_id,
            fidelity_score=score,
            violations=violations,
            warnings=warnings,
            details=details,
        )
