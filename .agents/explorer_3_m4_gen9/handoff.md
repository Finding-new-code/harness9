# Handoff Report: Deterministic Numerical Data Pipeline & Milestone 4 (R4) Test Suite Strategy

**Author:** `explorer_3_m4_gen9` (Teamwork Preview Explorer)  
**Date:** 2026-09-14T00:12:00Z  
**Target Milestone:** Milestone 4 (R4: Multi-Stage Pipeline & Visual/Numerical Integrity)  
**Scope:** `src/epistemic/numerical_pipeline.py`, `tests/test_script_verifier.py`, `tests/test_visual_verifier.py`, `tests/test_numerical_pipeline.py`  

---

## 1. Observation

Direct empirical observations from inspecting the codebase, specifications, contracts, and test executions:

### 1.1 Documented Specifications & Contracts
- **`docs/epistemic/CLAIM_VERIFICATION.md`** (Lines 90–105):
  - Defines Strategy 5: `NUMERICAL_CHECK`. Mandates dimensional analysis `(scalar, prefix, unit)`, SI base normalization, tolerance window $|V_{\text{claim}} - V_{\text{ground\_truth}}| \le \epsilon \times V_{\text{ground\_truth}}$ where $\epsilon = 0.001$ ($0.1\%$) for exact metrics and $\epsilon = 0.05$ ($5\%$) for approximation qualifiers, and mathematical consistency checks for compound growth rates (e.g. flagging $(30 - 10)/10 = 200\% \ne 300\%$).
- **`docs/epistemic/VISUAL_FACT_CHECKING.md`** (Lines 101–158):
  - Defines the Deterministic Data Visualization Pipeline:
    $$\text{Primary Dataset (CSV/JSON)} \longrightarrow \text{NumericalDataset} \longrightarrow \text{NormalizedChartIR} \longrightarrow \text{HyperFrames SVG}$$
  - Lines 128–149 define the contract for `NumericalDataPoint` (`x_value`, `y_value`, `label`, `uncertainty_range`) and `NumericalDataset` (`dataset_id`, `title`, `x_label`, `y_label`, `x_unit`, `y_unit`, `data_points`, `source_record`, `retrieved_at`, `dataset_sha256`).
  - Lines 151–157 specify mathematical axis scaling invariants: $Y_{\min} = 0.0$ baseline enforcement on bar charts, and coordinate projection formula:
    $$y_{\text{screen}} = H \times \left(1.0 - \frac{y_i - Y_{\min}}{Y_{\max} - Y_{\min}}\right)$$
  - Lines 81–98 define Audio-Visual Reconciliation: error threshold $\le 0.001$ ($0.1\%$), unit reconciliation (`"$4.2M"` vs *"4.2 billion USD"* triggers `BLOCK`), date mismatch (`VISUAL_AUDIO_TEMPORAL_MISMATCH`), and count mismatch ($N_{\text{visual}} \ne N_{\text{spoken}}$).
- **`docs/epistemic/FACTBENCH.md`** (Lines 33–45, 52–55, 74–76):
  - Category 2 (`numerical_integrity`): dimensional checks, unit conversions, compound math.
  - Category 9 (`visual_script_sync`): render vs voice synchronization, dataset lineage.
  - Formula 4.6 (Line 137): $S_{\text{factbench}} = 0.25 P_{\text{verif}} + 0.20 R_{\text{contra}} + 0.20 S_{\text{hist}} + 0.20 S_{\text{vis}} + 0.15 S_{\text{num}}$.
- **`src/epistemic/strategies.py`** (Lines 630–772):
  - `NumericalCheckStrategy` parses scalar numbers and multipliers (`k`, `thousand`, `m`, `million`, `b`, `billion`, `t`, `trillion`), tests compound growth assertions, enforces order-of-magnitude mismatch trap ($|\Delta \log_{10}| \ge 0.99$), and evaluates dual tolerance ($0.1\%$ exact, $5\%$ approx).
- **`src/models/contracts.py`** (Lines 1–854):
  - Defines 17 core production contracts (`CreatorProfile`, `ContentBrief`, `SourceRecord`, `ClaimRecord`, `ResearchDossier`, `Script`, etc.).
  - `NumericalDataPoint` and `NumericalDataset` are referenced in `docs/epistemic/VISUAL_FACT_CHECKING.md` but are not yet implemented in `src/models/contracts.py`.
- **`src/models/ir.py`** (Lines 33–42, 139–171):
  - `IRBlockType` defines the 7 canonical visual components (`REFERENCE_COLLAGE_HOOK`, `SPLIT_SCREEN_INTRO`, `QUOTE_HIGHLIGHT`, `TIMELINE_REVEAL`, `STATISTIC_REVEAL`, `COMPARISON_PANEL`, `CREATOR_BOTTOM_COLLAGE`).
  - `IRVisualBlockNode` exposes `parameters` / `props` and `asset_bindings`.
- **`src/epistemic/graph.py`** (Lines 224–235, 566–595):
  - `VisualElementNode` and `ScriptSentenceNode` exist in `EvidenceGraph`.
  - `EvidenceGraph.add_visual_element` links visual parameters to grounded claims via `EdgeRelation.VISUAL_DEPICTION`.

### 1.2 Test Suite Execution Baseline
- Execution of the existing epistemic and core regression suite:
  ```powershell
  uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -v
  ```
- Tool Result:
  ```
  ======================= 144 passed in 94.18s (0:01:34) ========================
  ```
  - `tests/test_historical_policy.py`: 15 passed
  - `tests/test_verification_engine.py`: 21 passed
  - `tests/test_evidence_graph.py`: 42 passed
  - `tests/test_contracts.py`: 12 passed
  - `tests/test_state_machine.py`: 10 passed
  - `tests/test_h9_acceptance.py`: 44 passed
- Invariant confirmed: Zero test failures, zero errors across all 144 existing tests.

---

## 2. Logic Chain

From the direct observations above, the architecture for the Deterministic Numerical Pipeline and the Milestone 4 Test Suite is deduced step by step:

### 2.1 The Hallucination Vulnerability in Automated Video Generation
- In multi-modal video production, LLMs frequently invent chart heights, distort axes, compress time intervals, or alter numbers between narration and graphics (e.g., spoken "$4.2 million" vs visual "$4.2B", or an exponential line drawn for linear data).
- Natural language models cannot be trusted to generate SVG coordinates or coordinate arrays directly.
- **Deduction:** The visual representation must be generated by a 100% deterministic, non-LLM pipeline that ingests verified source data, computes exact mathematical coordinates, validates visual invariants, and renders SVG graphics with cryptographic checksumming.

### 2.2 Numerical Ingestion and Canonical Integrity
- Datasets originate as CSVs, JSON tables, or database query results.
- Minor floating-point discrepancies or row reordering can produce varying checksums or subtle rounding errors.
- **Deduction:** 
  1. Ingestion must parse numbers using Python's `decimal.Decimal` or strict typed floats, enforcing canonical normalization (e.g., standardizing scientific notation and removing comma separators).
  2. The dataset must compute a canonical SHA-256 checksum over a strictly ordered, serialized representation of its coordinates and source metadata (`dataset_sha256`). Any mutation of a coordinate point must invalidate the hash.

### 2.3 Exact Mathematical Transformations
- Downstream visual components frequently display aggregated metrics (sum, mean, median), percentage breakdowns (part-to-whole), or growth rates (delta percentage).
- **Deductions:**
  1. *Percentage Invariant:* Part-to-whole percentages must sum to exactly $100.00\%$. The pipeline must implement the Largest Remainder Method (Hare-Niemeyer) for rounded integer or fixed-decimal allocations to prevent rounding anomalies (e.g. $33.3\% + 33.3\% + 33.3\% = 99.9\%$).
  2. *Growth Rate Invariant:* Delta calculation $\frac{y_t - y_0}{|y_0|} \times 100$ must trap division by zero ($y_0 = 0$) and verify parity with `NumericalCheckStrategy.evaluate()`.
  3. *Unit Scaling Invariant:* Converting between scales (e.g., raw count to millions or billions) must be governed by an exact bidirectional multiplier table (`K=1e3, M=1e6, B=1e9, T=1e12`), updating both the numeric values and the unit label simultaneously.

### 2.4 Viewport Projection & Invariant Gating
- Viewport projection maps data domain $[X_{\min}, X_{\max}] \times [Y_{\min}, Y_{\max}]$ into screen pixel space $[W, H]$.
- *Misleading Visual Trap (Truncated Baseline):* When a bar chart axis does not start at 0, small differences appear monumental (e.g., 98% vs 99% rendered in a 1:2 height ratio).
- **Deductions:**
  1. For `BAR` and `COLUMN` charts, $Y_{\min} = 0.0$ is mandatory by default. If a non-zero baseline is requested, it must require explicit opt-in (`allow_truncated_baseline=True`) AND trigger a mandatory visual disclosure badge (`"AXIS TRUNCATED: BASELINE STARTS AT [Y]"`).
  2. For `LINE` and `SCATTER` charts, dynamic bounding with fixed padding (e.g., $5\% \Delta$) is mathematically valid for continuous physical phenomena.
  3. The rendered SVG must be generated purely deterministically without random DOM IDs or timestamps, producing an immutable `chart_sha256`.

### 2.5 Test Suite Architecture & Interoperability
- Milestone 4 introduces three new verification test suites:
  1. `tests/test_script_verifier.py`: 4 test clusters (strengthened claims, altered numbers, omitted uncertainty, fabricated quotes).
  2. `tests/test_visual_verifier.py`: 4 test clusters (timeline reconciliation, chart verification, count verification, cross-modal contradictions).
  3. `tests/test_numerical_pipeline.py`: 5 test clusters (ingestion/checksums, precision transformations, dataset-to-chart determinism, unit conversions, invariant enforcement).
- Because these files are additive and rely on clean Pydantic schemas inheriting from `H9BaseModel`, they do not alter existing contracts or runtime behaviors, guaranteeing that the 144 baseline tests continue to pass with 0 regressions.

---

## 3. Specification

### 3.1 Architecture of `src/epistemic/numerical_pipeline.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NUMERICAL DATA PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. INGESTION (NumericalDatasetIngestion)                                   │
│     • Ingest CSV / JSON / Dict / DataFrame                                  │
│     • Type validation & Decimal precision normalization                     │
│     • Compute immutable dataset_sha256                                      │
│                                                                             │
│  2. TRANSFORMATIONS (NumericalTransformer)                                  │
│     • Aggregations: sum, mean, median, min, max, std_dev                   │
│     • Percentage Shares: Largest Remainder 100.0% sum invariant             │
│     • Growth Rates: (V_t - V_0) / |V_0| * 100 with zero division guard      │
│     • Scaling: K (1e3), M (1e6), B (1e9), T (1e12), nano (1e-9)             │
│                                                                             │
│  3. INVARIANT CHECKING (NumericalInvariantChecker)                          │
│     • Zero-baseline enforcement on bar charts (anti-distortion)             │
│     • Value fidelity validation: |y_screen - y_expected| < 1e-4             │
│     • Unit scale alignment: label "B" matches 1e9 scale factor              │
│     • Monotonicity preservation on sorted timelines                         │
│     • Non-averaging contradiction enforcement (range rendering)             │
│                                                                             │
│  4. CHART RENDERER (DeterministicChartRenderer)                             │
│     • NormalizedChartIR coordinate calculation                              │
│     • Deterministic SVG generator (<rect>, <polyline>, <circle>, <text>)    │
│     • Zero LLM generation / 100% reproducible chart_sha256                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.1.1 Pydantic Contracts & Data Models

```python
# src/models/contracts.py or src/epistemic/numerical_pipeline.py

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import Field, field_validator, model_validator
from src.models.contracts import H9BaseModel, SourceRecord

class ChartType(str, Enum):
    BAR = "bar"
    COLUMN = "column"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"

class NumericalDataPoint(H9BaseModel):
    """Single verified coordinate point in an empirical dataset."""
    x_value: Union[float, int, str]              # Year (1947), scalar (12.5), or Category ("Silicon")
    y_value: float                              # Numerical value
    label: Optional[str] = None                 # Optional point annotation
    uncertainty_range: Optional[Tuple[float, float]] = None # Optional [min, max] error bound
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("y_value")
    @classmethod
    def validate_finite(cls, v: float) -> float:
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError("y_value must be a finite numerical value")
        return v

class NumericalDataset(H9BaseModel):
    """Immutable ground-truth dataset backing charts and visual metrics."""
    dataset_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    x_label: str = Field(default="X")
    y_label: str = Field(default="Y")
    x_unit: str = Field(default="")             # e.g., "year", "nm", "category"
    y_unit: str = Field(default="")             # e.g., "USD", "count", "%", "W"
    data_points: List[NumericalDataPoint] = Field(..., min_length=1)
    source_record: SourceRecord
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dataset_sha256: str = Field(default="", description="Canonical SHA-256 hash")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def compute_hash_if_missing(self) -> "NumericalDataset":
        if not self.dataset_sha256:
            import hashlib, json
            canonical_payload = {
                "dataset_id": self.dataset_id,
                "title": self.title,
                "x_label": self.x_label,
                "y_label": self.y_label,
                "x_unit": self.x_unit,
                "y_unit": self.y_unit,
                "points": [(str(p.x_value), f"{p.y_value:.8f}") for p in self.data_points],
                "source_url": self.source_record.url if self.source_record else "",
            }
            raw = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
            object.__setattr__(self, "dataset_sha256", hashlib.sha256(raw).hexdigest())
        return self

class ChartElement(H9BaseModel):
    """Calculated graphical element ready for SVG rendering."""
    element_id: str
    element_type: str                            # "rect", "polyline", "circle", "slice", "text"
    raw_point: NumericalDataPoint
    screen_coords: Dict[str, float]              # e.g. {"x": 100.0, "y": 200.0, "width": 40.0, "height": 300.0}
    normalized_coords: Dict[str, float]          # Coordinates in [0.0, 1.0] viewport space
    formatted_value: str                         # e.g. "$4.2M", "100 Billion"
    fill_color: str = "#00d2ff"

class ChartConfig(H9BaseModel):
    """Deterministic configuration and rendered manifest for a data visualization."""
    chart_id: str
    chart_type: ChartType
    title: str
    dataset_id: str
    width: int = 1920
    height: int = 1080
    x_axis_min: float
    x_axis_max: float
    y_axis_min: float
    y_axis_max: float
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

class NumericalVerificationResult(H9BaseModel):
    """Integrity audit result for a chart configuration against its backing dataset."""
    valid: bool
    dataset_id: str
    chart_id: Optional[str] = None
    fidelity_score: float = 1.0
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
```

#### 3.1.2 Class Specifications

1. **`NumericalDatasetIngestion`**:
   - `from_csv(csv_text: str, dataset_id: str, title: str, source_record: SourceRecord, x_col: str, y_col: str, x_unit: str = "", y_unit: str = "") -> NumericalDataset`:
     - Parses CSV header and rows.
     - Strips commas, currency signs (`$`, `€`), and percentage signs (`%`).
     - Rejects rows with missing or non-numeric y-values.
     - Automatically infers if x_value is numeric (float/int) or categorical (string).
     - Instantiates `NumericalDataset` and calculates `dataset_sha256`.
   - `from_json_records(records: List[Dict[str, Any]], dataset_id: str, title: str, source_record: SourceRecord, x_key: str, y_key: str, ...) -> NumericalDataset`.
   - `verify_checksum(dataset: NumericalDataset) -> bool`:
     - Recomputes SHA-256 from data points and compares with stored `dataset_sha256`.

2. **`NumericalTransformer`**:
   - `aggregate(dataset: NumericalDataset, operation: str) -> float`:
     - Supported operations: `"sum"`, `"mean"`, `"median"`, `"min"`, `"max"`, `"std_dev"`.
     - Uses Python's `decimal.Decimal` with `ROUND_HALF_EVEN` to avoid floating-point drift.
   - `calculate_percentage_shares(dataset: NumericalDataset, decimal_places: int = 2) -> List[Tuple[NumericalDataPoint, float]]`:
     - Computes part-to-whole percentage: $P_i = \frac{y_i}{\sum y} \times 100$.
     - Implements the Largest Remainder Method (Hare-Niemeyer) so that $\sum P_i = 100.0\%$ exactly.
   - `calculate_growth_rate(v_start: float, v_end: float) -> float`:
     - Evaluates $\Delta\% = \frac{v_{\text{end}} - v_{\text{start}}}{|v_{\text{start}}|} \times 100$.
     - If $v_{\text{start}} == 0.0$, raises `ValueError("Cannot calculate percentage growth from zero baseline")`.
   - `scale_units(dataset: NumericalDataset, target_prefix: str) -> NumericalDataset`:
     - Supported prefixes: `"K"` ($10^3$), `"M"` ($10^6$), `"B"` ($10^9$), `"T"` ($10^{12}$), `"nano"` ($10^{-9}$), `"micro"` ($10^{-6}$).
     - Scales all `y_value` coordinates and appends prefix to `y_unit`.

3. **`DeterministicChartRenderer`**:
   - `render_chart(dataset: NumericalDataset, chart_type: ChartType, viewport: Tuple[int, int] = (1920, 1080), allow_truncated_baseline: bool = False, brand_colors: Optional[Dict[str, str]] = None) -> ChartConfig`:
     - Determines plot area margins (Left: 160, Right: 80, Top: 120, Bottom: 120).
     - Bounds computation:
       - For `BAR` / `COLUMN`: Enforces $Y_{\min} = 0.0$ unless `allow_truncated_baseline=True`. If truncated, flags `baseline_warning_required = True`.
       - For `LINE` / `SCATTER`: Sets $Y_{\min} = \min(y) - 0.05 \Delta$, $Y_{\max} = \max(y) + 0.05 \Delta$.
     - Projection calculation:
       $$x_{\text{screen}} = X_{\text{margin}} + W_{\text{plot}} \times \left(\frac{x_i - X_{\min}}{X_{\max} - X_{\min}}\right)$$
       $$y_{\text{screen}} = Y_{\text{margin}} + H_{\text{plot}} \times \left(1.0 - \frac{y_i - Y_{\min}}{Y_{\max} - Y_{\min}}\right)$$
     - Generates pure SVG string with deterministic formatting (`.2f`), ordered elements, axis ticks, and optional warning banner.
     - Computes `chart_sha256 = hashlib.sha256(rendered_svg.encode('utf-8')).hexdigest()`.

4. **`NumericalInvariantChecker`**:
   - `verify_chart_data(dataset: NumericalDataset, chart_config: ChartConfig) -> NumericalVerificationResult`:
     - **Check 1 (Zero Baseline):** If `chart_type == BAR` and $Y_{\min} > 0.0$ without `allow_truncated_baseline=True`, records violation `"UNJUSTIFIED_NON_ZERO_BASELINE"`.
     - **Check 2 (Value Fidelity):** For every element $k$, checks that screen height represents the exact data point within tolerance:
       $$\left| \text{height}_k - H_{\text{plot}} \times \frac{y_k - Y_{\min}}{Y_{\max} - Y_{\min}} \right| < 10^{-4}$$
     - **Check 3 (Unit Scaling):** Verifies that if `display_unit` is `"M"`, the ratio between raw dataset values and displayed values is exactly $10^6$.
     - **Check 4 (Monotonicity):** Verifies that horizontal ordering of points matches chronological or sorted x-values.

---

### 3.2 Specification of Milestone 4 Test Suite Design

#### 3.2.1 `tests/test_script_verifier.py` (Script Claim Re-Verification)
1. **Strengthened Claims Detection**:
   - `test_detect_modal_level_3_escalation_from_level_1`:
     - Primary passage: *"Preliminary laboratory observations suggest a potential decrease in resistance."* (Modal Level 1)
     - Script narration: *"The experiment conclusively proved that resistance is always eliminated."* (Modal Level 3)
     - Expected assertion: `STRENGTHENED_ASSERTION_WARNING` flag, `EpistemicStatus.PARTIALLY_SUPPORTED`, entailment score capped at 0.70.
   - `test_conserve_appropriate_modal_level_2`:
     - Passage: *"Silicon transistors typically exhibit higher thermal stability."* (Level 2)
     - Script: *"Silicon transistors generally offer greater thermal stability."* (Level 2)
     - Expected assertion: `EpistemicStatus.SUPPORTED`, no strengthening warning.
2. **Altered Numbers Detection**:
   - `test_detect_tenfold_order_of_magnitude_drift`:
     - Backing claim: 12,500 transistors.
     - Script narration: *"The new design packed 125,000 transistors on a single board."*
     - Expected assertion: `ORDER_OF_MAGNITUDE_MISMATCH` flag, `EpistemicStatus.CONTRADICTED`, `BLOCK` gate outcome.
   - `test_detect_compound_growth_calculation_error`:
     - Script narration: *"Revenue grew from 10 million to 30 million, a 300% increase."*
     - Expected assertion: `MATHEMATICAL_CALCULATION_ERROR` flag, `EpistemicStatus.CONTRADICTED`.
   - `test_approximate_qualifier_tolerance_window`:
     - Ground truth: 10,000 units. Script narrates *"around 10,400 units"*.
     - Asserted deviation: $4.0\%$. Tolerance for approx: $5.0\%$.
     - Expected assertion: PASS, `EpistemicStatus.SUPPORTED`.
3. **Omitted Uncertainty & Hedging Rules**:
   - `test_detect_omitted_scholarly_debate`:
     - Claim consensus state: `ConsensusState.ACTIVE_DEBATE`.
     - Script narration: *"Historians agree that the industrial embargo single-handedly caused the economic collapse."*
     - Expected assertion: `UNHEDGED_CONSENSUS_VIOLATION`, `EpistemicStatus.CONTESTED`.
   - `test_enforce_calibrated_rhetoric_for_minority_interpretation`:
     - Consensus state: `ConsensusState.MINORITY_INTERPRETATION`.
     - Script narration without minority qualifier (*"Some scholars argue..."*).
     - Expected assertion: `RHETORICAL_CALIBRATION_WARNING`.
4. **Quote Veracity & Paraphrase Mandate**:
   - `test_verbatim_quote_exact_match`:
     - Archival text: *"There's plenty of room at the bottom."*
     - Script text: `'"There is plenty of room at the bottom," Richard Feynman declared.'`
     - Expected assertion: `QuoteExactness.EXACT`, normalized Levenshtein $\le 0.02$, PASS.
   - `test_fabricated_quote_triggers_paraphrase_mandate`:
     - Archival text: *"I have become death, the destroyer of worlds."*
     - Script text: `'"I am now death, conqueror of all galaxies," Oppenheimer said.'`
     - Levenshtein normalized distance $> 0.30$.
     - Expected assertion: `QUOTE_FABRICATION_DETECTED`, `QuoteExactness.DISTORTED`, strips quotation marks and generates indirect paraphrase.

#### 3.2.2 `tests/test_visual_verifier.py` (Visual Fact-Checking Engine)
1. **Timeline Date Reconciliation**:
   - `test_timeline_reveal_year_matches_spoken_voiceover`:
     - Spoken voiceover: *"In December 1947, the first transistor was demonstrated."*
     - Visual block: `TIMELINE_REVEAL` with `year: 1947`.
     - Expected assertion: Reconciliation status PASS.
   - `test_timeline_reveal_date_anachronism_detected`:
     - Spoken voiceover: *"In late 1947, researchers created the prototype."*
     - Visual block: `TIMELINE_REVEAL` with `year: 1956`.
     - Expected assertion: `VISUAL_AUDIO_TEMPORAL_MISMATCH`, `BLOCK` gate outcome.
   - `test_detect_timeline_chronological_inversion`:
     - Scene contains timeline nodes for 1947 and 1954 where $X(1954) < X(1947)$.
     - Expected assertion: `TIMELINE_CHRONOLOGY_INVERSION`.
2. **Chart Data & Slope Verification**:
   - `test_verify_chart_data_matches_underlying_numerical_dataset`:
     - `COMPARISON_PANEL` or `STATISTIC_REVEAL` references `dataset_id: "ds_transistors"`.
     - Values match coordinates within $0.001\%$.
     - Expected assertion: `NumericalVerificationResult.valid == True`.
   - `test_detect_hallucinated_chart_coordinates`:
     - Visual coordinate displays exponential jump $y=100 \to 10,000$, while dataset has linear $100 \to 200$.
     - Expected assertion: `VISUAL_CHART_COORDINATE_DIVERGENCE`, `BLOCK` gate.
3. **Entity Count Verification**:
   - `test_spoken_count_matches_rendered_collage_panels`:
     - Spoken audio: *"Three distinct breakthroughs paved the way."*
     - Visual block: `REFERENCE_COLLAGE_HOOK` with `panel_count: 3`.
     - Expected assertion: PASS.
   - `test_detect_spoken_vs_visual_count_discrepancy`:
     - Spoken audio: *"Three distinct breakthroughs paved the way."*
     - Visual block: 5 visual panel elements.
     - Expected assertion: `VISUAL_COUNT_DISCREPANCY` (asserted 3 vs rendered 5), `WARN` or `BLOCK`.
4. **Cross-Modal Contradictions**:
   - `test_cross_modal_unit_mismatch_blocks_publish`:
     - Spoken audio: *"over four million dollars"*
     - Visual `STATISTIC_REVEAL`: `target_number: "$4.2B"`, `suffix: "B"`.
     - Error: $\frac{|4.2 \times 10^9 - 4.2 \times 10^6|}{4.2 \times 10^9} = 99.9\% > 0.1\%$.
     - Expected assertion: `VISUAL_AUDIO_NUMERICAL_MISMATCH`, immediate `BLOCK` verdict.

#### 3.2.3 `tests/test_numerical_pipeline.py` (Numerical Pipeline Integrity)
1. **Dataset Ingestion & Checksum**:
   - `test_csv_ingestion_canonical_hashing`:
     - Ingest valid CSV string with years and transistor counts.
     - Verify `NumericalDataset` structure, data point counts, and deterministic `dataset_sha256`.
   - `test_corrupt_csv_rejection`:
     - Ingest CSV with `NaN`, `Inf`, and missing values; assert `ValueError` with clear field trace.
2. **Transformations & Decimal Precision**:
   - `test_part_to_whole_percentage_sum_100_percent_invariant`:
     - Categories with fractional values (e.g. 1/3, 1/3, 1/3); assert that percentage sum equals exactly $100.00\%$ via Largest Remainder Method.
   - `test_growth_rate_calculation_and_zero_division_guard`:
     - Verify normal growth $(10 \to 30 \implies +200.0\%)$. Verify zero division raises explicit error.
3. **Dataset-to-Chart Determinism**:
   - `test_chart_renderer_100x_determinism`:
     - Render same dataset 100 times; assert identical byte-level SVG output and identical `chart_sha256`.
4. **Scaling & Unit Conversions**:
   - `test_unit_scaling_k_m_b_t`:
     - Convert $150 \times 10^9$ to billions; assert $y=150.0$, unit=`"B"`.
5. **Invariant Checking (Anti-Misleading Visuals)**:
   - `test_bar_chart_zero_baseline_enforcement`:
     - Render bar chart with $y \in [90, 100]$. Default bounds must set $Y_{\min} = 0.0$.
   - `test_bar_chart_truncated_baseline_requires_explicit_opt_in_and_warning`:
     - Render bar chart with `y_min = 80.0` without `allow_truncated_baseline=True`; assert `MisleadingVisualError`.
     - When `allow_truncated_baseline=True`, assert `baseline_warning_required == True` and SVG includes warning banner.
   - `test_unit_scale_mismatch_detection`:
     - Chart axis claims `"Millions"` but data is in `"Billions"`; invariant checker flags `UNIT_SCALE_MISMATCH_ERROR`.

---

## 4. Caveats

1. **Read-Only Scope:** In accordance with the role constraints of `explorer_3_m4_gen9`, no production files (`src/epistemic/numerical_pipeline.py`, `src/models/contracts.py`) were modified or written during this investigation. All implementations will be performed by `worker_m4`.
2. **Rendering Engine Backends:** The deterministic chart renderer generates self-contained vector SVGs adhering to HyperFrames standards. In headless production rendering, these SVGs are ingested by Chromium/Puppeteer inside the sandboxed HyperFrames runner (`adapters/hyperframes/adapter.py`).
3. **Natural Language Parsing in Tests:** Script claim re-verification uses regex and modal keyword matching for offline deterministic CI/CD mode. When deployed in live production, semantic support will be enhanced by the Hermes capability bridge (`src/h9_runtime/bridge.py`).

---

## 5. Conclusion

1. The architectural gap in Milestone 4 has been completely mapped: `NumericalDataset` and `NumericalDataPoint` contracts must be formalized, backed by `src/epistemic/numerical_pipeline.py` providing exact Decimal transformations, deterministic SVG viewport projection, zero-baseline anti-distortion invariant checking, and cryptographic SHA-256 verification.
2. The Milestone 4 test strategy is fully specified across three complementary suites:
   - `tests/test_script_verifier.py` (Script drift, modal strengthening, altered numbers, omitted uncertainty, quote fabrication)
   - `tests/test_visual_verifier.py` (Audio-visual reconciliation, timeline inversions, count discrepancies, cross-modal unit contradictions)
   - `tests/test_numerical_pipeline.py` (Ingestion, Decimal precision, 100% percentage invariant, SVG coordinate projection determinism, zero-baseline enforcement)
3. Zero-regression interoperability is strictly preserved: the 144 existing baseline tests remain 100% passing.

---

## 6. Verification Method

To independently verify the facts and logic specified in this report:

1. **Verify Baseline Test Suite (144 Passing Tests):**
   ```powershell
   uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -v
   ```
   *Expected result: 144 passed (0 failures, 0 errors).*

2. **Verify Epistemic Specifications Conformance:**
   ```powershell
   uv run python scripts/verify_epistemic_specs.py
   ```
   *Expected result: All 5 specification verification suites report `True`.*

3. **Inspect Specification Sources:**
   - `docs/epistemic/CLAIM_VERIFICATION.md` (Strategy 5, Lines 90–105)
   - `docs/epistemic/VISUAL_FACT_CHECKING.md` (Deterministic Pipeline, Lines 101–158)
   - `docs/epistemic/FACTBENCH.md` (Categories 2 & 9, Lines 33–45, 52–55, 74–76)
   - `src/epistemic/strategies.py` (Lines 630–772)
   - `src/models/contracts.py` & `src/models/ir.py`

4. **Invalidation Conditions:**
   - Any floating-point drift allowing part-to-whole percentages to sum to $\ne 100.0\%$.
   - Any bar chart rendered with a non-zero baseline without explicit opt-in and warning disclaimers.
   - Any failure of the SVG renderer to produce identical SHA-256 digests on repeated runs.
   - Any regression in the 144 baseline tests upon integrating Milestone 4 contracts.
