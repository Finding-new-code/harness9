# Visual Fact-Checking & Deterministic Data Visualization Pipeline: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/epistemic/`, `src/models/`, `adapters/hyperframes/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/HYPERFRAMES_INTEGRATION.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`  

---

## 1. Executive Summary & Purpose

The **Harness 9 Visual Fact-Checking Specification** defines the protocols for verifying the factual accuracy, numerical integrity, and audio-narrative consistency of rendered video frames, motion graphics, charts, and storyboard intermediate representations (Production IR).

In video production, factual errors frequently occur not in the spoken dialogue, but in the accompanying on-screen text and graphics:
- Spoken voiceover narrates *"over four million dollars"*, while the on-screen kinetic typography displays `"$4.2B"`.
- A voiceover discusses the late 1950s, while an animated timeline graphic highlights the year `1947`.
- An on-screen bar chart depicts an exponential curve where the underlying empirical dataset reflects linear growth.
- Voiceover states *"Three distinct phases occurred"*, while a visual collage component renders 5 panels.

This specification guarantees that:
1. Every on-screen graphic, date, quote, and statistic is audited against spoken narration and the Evidence Graph.
2. All charts, graphs, and quantitative visualizations derive deterministically from immutable, typed `NumericalDataset` schemas.

---

## 2. Visual Storyboard Block Auditing

The visual fact-checker inspects compiled `IRVisualBlockNode` elements across all 7 canonical HyperFrames blocks:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRODUCTION IR DOCUMENT (AST)                          │
│  [Scene 1] ──► [VisualBlockNode: STATISTIC_REVEAL]                          │
│  [Scene 2] ──► [VisualBlockNode: TIMELINE_REVEAL]                           │
│  [Scene 3] ──► [VisualBlockNode: QUOTE_HIGHLIGHT]                           │
│  [Scene 4] ──► [VisualBlockNode: COMPARISON_PANEL]                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Parameter Extraction)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VISUAL FACT CHECKER ENGINE                             │
│  1. Extract parameters: numbers, dates, quote strings, icon counts          │
│  2. Extract concurrent spoken voiceover from ScriptBeat                     │
│  3. Reconcile Visual vs Audio semantics and numerical values                │
│  4. Verify data points against backing NumericalDataset                     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VERIFICATION OUTCOME / VERDICT                         │
│  • PASS: Perfect audio-visual alignment & verified dataset lineage          │
│  • WARN: Minor formatting divergence (e.g. "$4.2M" vs "4.2 million USD")    │
│  • BLOCK: Numerical discrepancy, date anachronism, or fabricated quote       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Audited Visual Block Types & Parameter Extraction

1. **`STATISTIC_REVEAL`**:
   - **Extracted Parameters**: `stat_number` (string/float), `stat_label` (string), `unit` (string), `comparison_pct` (float).
   - **Audit Target**: Verified against `StatisticRecord` and spoken beat audio.
2. **`TIMELINE_REVEAL`**:
   - **Extracted Parameters**: `year` (int/string), `date` (ISO string), `event_title` (string).
   - **Audit Target**: Verified against `ClaimRecord.temporal_context` and chronological timeline.
3. **`QUOTE_HIGHLIGHT`**:
   - **Extracted Parameters**: `quote_text` (string), `author` (string), `source_title` (string).
   - **Audit Target**: Verified against `ClaimType.DIRECT_QUOTE` primary archival text.
4. **`COMPARISON_PANEL`**:
   - **Extracted Parameters**: `left_val`, `right_val`, `delta_metric`, `dataset_binding_id`.
   - **Audit Target**: Verified against `NumericalDataset` coordinates.
5. **`REFERENCE_COLLAGE_HOOK`**:
   - **Extracted Parameters**: `panel_count` (int), `asset_descriptors` (list).
   - **Audit Target**: Reconciled against count claims in narration (e.g. *"three innovations"*).

---

## 3. Audio-Visual Reconciliation Protocols

For every scene in `ProductionIRDocument`, the engine synchronizes `ScriptBeat.text` with `IRVisualBlockNode.parameters`:

### 3.1 Numerical Value Reconciliation
Let $V_{\text{vis}}$ denote the numerical value in visual parameters, and $V_{\text{audio}}$ denote the number parsed from concurrent spoken text.

$$\text{Error} = \frac{|V_{\text{vis}} - V_{\text{audio}}|}{V_{\text{vis}}}$$

- **Invariant**: If $\text{Error} > 0.001$ ($0.1\%$) and audio lacks explicit approximation words, the engine raises `VISUAL_AUDIO_NUMERICAL_MISMATCH` and triggers a `BLOCK` gate.
- **Unit Reconciliation**: The engine verifies that visual unit suffixes (`"M"`, `"B"`, `"%"`, `"nm"`) match spoken units (*"million"*, *"billion"*, *"percent"*, *"nanometers"*). A mismatch between `"$4.2M"` and *"4.2 billion dollars"* produces an immediate `BLOCK`.

### 3.2 Chronological & Date Reconciliation
Let $T_{\text{vis}}$ denote the date/year displayed on-screen, and $T_{\text{audio}}$ denote the date spoken in narration.
- If $T_{\text{vis}} \ne T_{\text{audio}}$: Raises `VISUAL_AUDIO_TEMPORAL_MISMATCH`.
- If on-screen timeline orders events $E_1$ and $E_2$ such that $X(E_1) > X(E_2)$ on a horizontal timeline where $T(E_1) < T(E_2)$, the engine flags a `TIMELINE_CHRONOLOGY_INVERSION`.

### 3.3 Visual Entity & Count Reconciliation
When narration asserts a finite integer quantity of items (e.g. *"Three key breakthroughs paved the way"*):
- The visual engine counts rendered icons, collage panels, or callout cards ($N_{\text{visual}}$).
- If $N_{\text{visual}} \ne 3$: Raises `VISUAL_COUNT_DISCREPANCY` (`WARN` or `BLOCK`).

---

## 4. Deterministic Numerical Data Pipeline

To eliminate "hallucinated charts" (where LLMs invent bar chart heights, line points, or pie percentages), Harness 9 mandates a **Deterministic Data Visualization Pipeline**:

```
[ Primary Source / Official Dataset ] (CSV / Tabular JSON / Census / BLS)
                  │
                  ▼
      [ NumericalDataset Contract ]
        • dataset_id, title, x_unit, y_unit
        • data_points: List[NumericalDataPoint]
        • source_record: SourceRecord
                  │
                  ▼
      [ NormalizedChartIR Node ]
        • Computes exact mathematical min/max, scales, ticks
        • Normalizes coordinates to [0.0, 1.0] viewport space
                  │
                  ▼
   [ HyperFrames SVG/Canvas Component ]
     • Renders polylines, bar heights, and scatter coordinates
     • Strictly deterministic compilation; zero LLM generation
```

### 4.1 Numerical Data Contracts (`src/models/contracts.py`)

```python
class NumericalDataPoint(H9BaseModel):
    """Single verified coordinate point in an empirical dataset."""
    x_value: Union[float, str]                   # e.g. Year (1947) or Category ("Germanium")
    y_value: float                               # e.g. 100.0
    label: Optional[str] = None
    uncertainty_range: Optional[Tuple[float, float]] = None

class NumericalDataset(H9BaseModel):
    """Immutable ground-truth dataset backing charts and visual metrics."""
    dataset_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    x_label: str
    y_label: str
    x_unit: str
    y_unit: str
    data_points: List[NumericalDataPoint] = Field(..., min_length=1)
    source_record: SourceRecord
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    dataset_sha256: str = Field(..., min_length=64, max_length=64)
```

### 4.2 Mathematical Normalization & Rendering Invariants
1. **Mathematical Axis Scaling**: Axis bounds $[Y_{\min}, Y_{\max}]$ are computed deterministically from data points. Zero truncation on bar charts is strictly enforced to prevent misleading visual scaling.
2. **Coordinate Determinism**: HyperFrames component generators compile chart SVGs (`<polyline>`, `<rect>`) by pure coordinate projection:
   $$y_{\text{screen}} = H \times \left( 1.0 - \frac{y_i - Y_{\min}}{Y_{\max} - Y_{\min}} \right)$$
   Models have zero latitude to alter coordinate points.

---

## 5. Visual Fact-Checking Engine Implementation (`VisualFactChecker`)

```python
class VisualFactChecker:
    """Audits Production IR documents against narration audio and datasets."""

    def verify_composition(
        self,
        ir_document: ProductionIRDocument,
        script: Script,
        evidence_graph: EvidenceGraph,
    ) -> VisualFactAuditReport:
        """Executes full visual fact-checking audit."""
        discrepancies: List[VisualDiscrepancy] = []

        for scene in ir_document.scenes:
            beat = script.get_beat_by_id(scene.scene_id)

            # 1. Audit visual statistics against narration
            for block in scene.visual_blocks:
                if block.block_type == IRBlockType.STATISTIC_REVEAL:
                    self._check_statistic_reveal(block, beat, discrepancies)
                elif block.block_type == IRBlockType.TIMELINE_REVEAL:
                    self._check_timeline_reveal(block, beat, discrepancies)
                elif block.block_type == IRBlockType.QUOTE_HIGHLIGHT:
                    self._check_quote_highlight(block, beat, evidence_graph, discrepancies)
                elif block.block_type == IRBlockType.COMPARISON_PANEL:
                    self._check_dataset_lineage(block, discrepancies)

        verdict = self._compute_verdict(discrepancies)
        return VisualFactAuditReport(
            passed=(verdict in ["PASS", "WARN"]),
            verdict=verdict,
            discrepancies=discrepancies,
        )
```
