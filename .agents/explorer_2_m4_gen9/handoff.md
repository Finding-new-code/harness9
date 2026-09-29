# Visual Fact-Checking Engine Specification Report (`src/epistemic/visual_verifier.py`)

**Document Version:** 1.0.0  
**Author:** `explorer_2_m4_gen9` (Teamwork Preview Explorer)  
**Date:** 2026-09-14T00:09:00Z  
**Target Milestone:** Milestone 4 (R4) — Script Re-Verification & Visual Integrity  
**Deliverable File:** `g:\Finding-new-code\harness9\.agents\explorer_2_m4_gen9\handoff.md`  
**Target Implementation Module:** `src/epistemic/visual_verifier.py`  

---

## 1. Observation

Direct code and architectural observations across the Harness 9 codebase and specifications:

### 1.1 Authoritative Requirements & State Machine Mandates
- **`ORIGINAL_REQUEST.md` (lines 230–234)**:
  > *"R4. Multi-Stage Pipeline & Visual/Numerical Integrity: Implement post-script claim extraction and re-verification comparing script claims against the evidence graph to detect strengthened claims, altered numbers, omitted uncertainty, or fabricated quotes (enforcing strict quote verification and paraphrase rules). Implement visual fact-checking verifying rendered storyboard elements, timelines, charts, and counts against script narration. Guarantee numerical/data visualization integrity through a deterministic pipeline from source dataset to chart rendering."*
- **`ORIGINAL_REQUEST.md` (line 257)**:
  > *"Visual fact-checker verifies rendered scene elements, metrics, and dates against narration claims."*
- **`ORIGINAL_REQUEST.md` (lines 234, 261)**:
  > Expose verification capabilities natively through the Hermes runtime via `h9.verify_visual_claims` and state machine gate `VISUAL_FACT_CHECK`.
- **`PROJECT.md` (lines 28–30, 97–99, 101–105)**:
  > Feature 11: *"Visual Fact-Checking Engine: Audit rendered storyboard elements, timelines, charts, counts against narration in src/epistemic/visual_verifier.py (Milestone M4 | R4)."*  
  > Contract: `VisualVerifier.verify_visuals(storyboard: Storyboard, graph: EvidenceGraph, script: ScriptDraft) -> VisualVerificationReport`.  
  > Invariant: `StateMachine.can_publish() -> bool` returns `False` if any mandatory gate is `BLOCK` or `HUMAN_REVIEW`.

### 1.2 Canonical Visual Fact-Checking Specification (`docs/epistemic/VISUAL_FACT_CHECKING.md`)
- **Visual Block Parameter Extraction (lines 57–74)**:
  - `STATISTIC_REVEAL`: Parameters include `target_number`, `metric_label`, `prefix`, `suffix`, `context_subtext`. Verified against `StatisticRecord` and spoken beat narration.
  - `TIMELINE_REVEAL`: Parameters include `milestones` list (`year`/`date`, `title`, `description`). Verified against `ClaimRecord.temporal_context` and chronological order.
  - `QUOTE_HIGHLIGHT`: Parameters include `quote_text`, `author_name`, `publication`, `date`. Verified against `ClaimType.DIRECT_QUOTE` primary archival text.
  - `COMPARISON_PANEL`: Parameters include `comparison_rows` (`metric`, `val_a`, `val_b`), `dataset_binding_id`. Verified against `NumericalDataset` coordinates.
  - `REFERENCE_COLLAGE_HOOK`: Parameters include `image_paths`, `panel_count`. Reconciled against count claims in narration (e.g. *"three innovations"*).
- **Audio-Visual Reconciliation Protocols (lines 77–98)**:
  - Numerical error formula:
    $$\text{Error} = \frac{|V_{\text{vis}} - V_{\text{audio}}|}{V_{\text{vis}}}$$
    Invariant: If $\text{Error} > 0.001$ ($0.1\%$) and audio lacks explicit approximation qualifiers, the engine raises `VISUAL_AUDIO_NUMERICAL_MISMATCH` with severity `BLOCK`.
  - Unit reconciliation: Mismatch between visual units (`"M"`, `"B"`, `"%"`, `"nm"`) and spoken units (*"million"*, *"billion"*, *"percent"*) raises an immediate `BLOCK`.
  - Chronological reconciliation: Visual milestone chronological inversion ($T(E_1) < T(E_2)$ but rendered $X(E_1) > X(E_2)$) raises `TIMELINE_CHRONOLOGY_INVERSION`. Discrepancy between visual date and audio date raises `VISUAL_AUDIO_TEMPORAL_MISMATCH`.
  - Visual entity counts: If narration asserts an integer quantity $N_{\text{audio}}$ (e.g. *"Three key breakthroughs"*), and on-screen collage/cards count $N_{\text{vis}} \ne N_{\text{audio}}$, the engine flags `VISUAL_COUNT_DISCREPANCY`.
- **Deterministic Numerical Data Pipeline (lines 101–156)**:
  - Backed by `NumericalDataset` with `data_points: List[NumericalDataPoint]`, `dataset_id`, `dataset_sha256`.
  - Enforces mathematical baseline zero bounds on bar charts ($Y_{\min} \le 0.0$) to eliminate misleading scaling.

### 1.3 Fact-Checking Typology & Epistemic Contracts (`docs/epistemic/FACT_CHECKING_SPEC.md` & `src/models/contracts.py`)
- **`ClaimType` (`contracts.py:273–283`)**:
  `EVENT_FACT`, `CAUSAL_INTERPRETATION`, `SCHOLARLY_INTERPRETATION`, `NUMERICAL_METRIC`, `DIRECT_QUOTE`, `SCIENTIFIC_LAW`, `CURRENT_EVENT`, `DEFINITIONAL`.
- **`EpistemicStatus` (`contracts.py:197–210`)**:
  `VERIFIED`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTESTED`, `CONTRADICTED`, `UNSUPPORTED`, `UNVERIFIABLE`, `OUTDATED`, `MISLEADING`, `OPINION`, `PREDICTION`.
- **`SourceTier` (`contracts.py:212–258`)**:
  13-tier taxonomy from `PRIMARY_SOURCE` (Tier 1) to `UNVERIFIED` (Tier 13).
- **`TemporalContext` (`contracts.py:306–314`)**:
  `valid_from`, `valid_until`, `as_of_date`, `is_time_sensitive`, `temporal_status`.
- **`ClaimRecord` (`contracts.py:353–420`)**:
  Carries `claim_text`, `epistemic_status`, `consensus_state`, `temporal_context`, `quote_exactness`, `evidence_node_ids`, `evidence_links`.
- **`Script` & `ScriptScene` (`contracts.py:604–675`)**:
  `ScriptScene` contains `scene_id`, `start_time`, `duration`, `narration_text`, `component_type`, `component_props`, `beats: List[ScriptBeat]`.
- **`Storyboard` & `Scene` (`src/models/script.py:46–118`)**:
  Alternate representation containing `scenes: List[Scene]`, with `beats: List[Beat]`.

### 1.4 Production IR AST Models (`src/models/ir.py`)
- **`IRBlockType` (`ir.py:33–42`)**:
  `REFERENCE_COLLAGE_HOOK`, `SPLIT_SCREEN_INTRO`, `QUOTE_HIGHLIGHT`, `TIMELINE_REVEAL`, `STATISTIC_REVEAL`, `COMPARISON_PANEL`, `CREATOR_BOTTOM_COLLAGE`.
- **`IRVisualBlockNode` (`ir.py:140–171`)**:
  `block_type`, `parameters: Dict[str, Any]`, `asset_bindings: Dict[str, str]`, `referenced_asset_ids`.
- **`IRSceneNode` (`ir.py:183–210`)**:
  `scene_id`, `start_time_sec`, `duration_sec`, `narration: IRNarrationBlock`, `visual_block: Optional[IRVisualBlockNode]`, `visual_blocks: List[IRVisualBlockNode]`.
- **`ProductionIRDocument` (`ir.py:246–385`)**:
  AST root with strict invariants (contiguity, audio alignment, asset binding integrity, beat temporal clamping).

### 1.5 Evidence Graph DAG Integration (`src/epistemic/graph.py`)
- **Visual Nodes & Edges (`graph.py:50–58, 224–235, 566–594`)**:
  - `EdgeRelation.VISUAL_DEPICTION`: Connects `ClaimNode -> VisualElementNode`.
  - `EdgeRelation.DERIVES_FROM`: Connects `SceneNode -> VisualElementNode`.
  - `VisualElementNode`: `scene_id`, `block_type`, `parameter_key`, `parameter_value`, `dataset_id`, `grounded_claim_ids`, `display_unit`.
  - `add_visual_element(...)`: Inserts node and establishes DAG edges while checking for cycles.

### 1.6 HyperFrames Component Blocks (`src/hyperframes/components/`)
- `statistic_reveal.py`: `target_number`, `prefix`, `suffix`, `metric_label`, `context_subtext`.
- `timeline_reveal.py`: `milestones: list[dict]` where each entry contains `year` or `date`, `title`, `description`.
- `quote_highlight.py`: `quote_text`, `author_name`, `author_title`, `publication`, `date`.
- `comparison_panel.py`: `entity_a_name`, `entity_b_name`, `comparison_rows: list[dict]` (`metric`, `val_a`, `val_b`, `winner`).
- `reference_collage_hook.py`: `image_paths`, `headline`, `subtext`.

---

## 2. Logic Chain

The architecture of `src/epistemic/visual_verifier.py` is derived step-by-step from the verified codebase invariants:

1. **Polymorphic Input Normalization**:
   - The production pipeline expresses visual scenes across three representations depending on lifecycle stage: `ProductionIRDocument` (compiled IR AST), `Script` (Pydantic contracts), or `Storyboard` (`src/models/script.py`).
   - *Inference*: `VisualVerifier` must expose a polymorphic entry point `verify_visuals(storyboard, graph, script=None)` that normalizes any input into a canonical internal audit representation (`AuditedSceneContext`) consisting of `scene_id`, `visual_blocks` (block type + parameters), and `speech_beats` (text + time bounds).

2. **Parameter Extraction by Component Block Archetype**:
   - Every on-screen component belongs to one of the 7 `IRBlockType` definitions or a chart/geospatial extension.
   - *Inference*: The extraction layer must be dispatched per `IRBlockType`:
     - `STATISTIC_REVEAL` $\to$ extracts numeric value, prefix/suffix, multiplier, metric label.
     - `TIMELINE_REVEAL` $\to$ extracts ordered milestone list with parsed years/dates and titles.
     - `QUOTE_HIGHLIGHT` $\to$ extracts quote string, author name, attribution source, date.
     - `COMPARISON_PANEL` $\to$ extracts dual entity metrics, row values, winner designations.
     - `REFERENCE_COLLAGE_HOOK` / `CREATOR_BOTTOM_COLLAGE` $\to$ extracts image/panel count, tags.
     - General chart / geospatial properties $\to$ extracts data points, dataset references, axes, territory labels.

3. **Cross-Modal Reconciliation Logic (Audio vs Visual)**:
   - Voiceover audio is broken into `ScriptBeat` / `IRSpeechBeat` instances aligned temporally with the scene.
   - *Inference*: The cross-modal engine must perform 5 targeted consistency audits:
     - **Numerical Audit**: Extract spoken quantities via regex/tokenization (handling word numerals like *"four million"* $\to 4,000,000$). Calculate relative error $\frac{|V_{\text{vis}} - V_{\text{audio}}|}{V_{\text{vis}}}$. If error $> 0.1\%$ without approximate framing, trigger `BLOCK`. Verify unit equivalence ($"\$4.2\text{M}"$ vs *"4.2 million dollars"*).
     - **Trend Audit**: Compute slope of visual chart points $\Delta y / \Delta x$. Classify spoken trend tokens (e.g. *"fell"*, *"plummeted"*, *"dropped"* $\to -1$; *"surged"*, *"grew"*, *"rose"* $\to +1$). If signs disagree, trigger `CHART_TREND_CONTRADICTION` (`BLOCK`).
     - **Chronological Audit**: Verify milestones are monotonically ordered on horizontal timelines ($T(E_i) \le T(E_{i+1})$). Flag inversions as `BLOCK`. Verify visual date matches spoken date.
     - **Entity Count Audit**: Detect explicit spoken counts (*"three distinct phases"*, *"two approaches"*) and assert $N_{\text{vis}} = N_{\text{audio}}$. Flag discrepancy as `WARN` (or `BLOCK` if strong assertion).
     - **Quote & Attribution Audit**: Compute normalized Levenshtein similarity between on-screen quote and primary text/audio. Verify attributed speaker matches audio.

4. **Evidence Graph Grounding Audit (Visual vs Evidence)**:
   - Visuals must not only match narration; they must be grounded in the `EvidenceGraph`.
   - *Inference*:
     - Visual milestone dates are validated against `ClaimRecord.temporal_context`.
     - Charts referencing `dataset_id` are validated against `NumericalDataset` in the evidence graph. Unreferenced or mutated datasets trigger `DANGLING_DATASET_BINDING` (`BLOCK`).
     - Bar chart baseline zero ($Y_{\min} \le 0$) is strictly enforced to prevent misleading visual truncation (`CHART_BASELINE_TRUNCATION`).
     - Map and geospatial territory labels are validated against the temporal validity period of historical political entities (e.g. flagging "Russia" when depicting 1950 borders).

5. **Deterministic Return Contract & Lifecycle Gate Integration**:
   - The State Machine (`src/orchestrator/state_machine.py`) evaluates the `VISUAL_FACT_CHECK` gate.
   - *Inference*: The verification outcome must return `VisualVerificationReport` containing structured `VisualInconsistencyRecord` items categorized by `VisualDiscrepancyType` and `VisualSeverity` (`BLOCK`, `WARN`). Any `BLOCK` inconsistency sets `passed=False` and `verdict="BLOCK"`, halting publication under the `can_publish()` invariant.

---

## 3. Caveats

1. **Dual Representation in Existing Codebase**:
   - The repository contains both `src/models/script.py` (`Storyboard` with dataclass `Scene`) and `src/models/contracts.py` (`Script` with Pydantic `ScriptScene`), as well as `src/models/ir.py` (`ProductionIRDocument`). The specification mandates that `VisualVerifier` polymorphically handles all three inputs without throwing type errors.
2. **Headless Canvas/SVG Pixel vs AST Property Auditing**:
   - True frame-level OCR of rendered MP4/video frames is computationally heavy and non-deterministic. In Harness 9, visual generation is deterministically driven by parameterized HyperFrames components and Production IR AST. Auditing the compiled AST parameters against the `EvidenceGraph` and audio script achieves 100% mathematical certainty with zero OCR hallucination. Post-render pixel verification is confined to layout boundaries in renderer tests.
3. **Geospatial Boundaries**:
   - Deep polygon GIS intersection is out of scope for the lightweight epistemic core. Instead, geospatial verification focuses on:
     a) Territory label anachronisms (matching historical country/region names to scene timestamps).
     b) Coordinate consistency against evidence dossiers.
     c) Boundary dispute status (ensuring disputed regions are not marked as uncontested if evidence marks them as `CONTESTED`).
4. **Hermes Native Model Tool Registration**:
   - Exposing `h9.verify_visual_claims` in `tools/h9_content_tools.py` and `src/h9_runtime/bridge.py` is a Milestone 5 requirement. Milestone 4 focuses strictly on implementing the core engine in `src/epistemic/visual_verifier.py`.

---

## 4. Conclusion & Complete Technical Specification

The visual fact-checking engine shall be implemented in `src/epistemic/visual_verifier.py` according to the following complete architectural and contract specification.

### 4.1 System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            INPUT ARTIFACTS                                  │
│  • Storyboard / ProductionIRDocument / Script                               │
│  • Spoken Narration ScriptBeats / Audio Timestamps                          │
│  • EvidenceGraph (ClaimNodes, TemporalContext, NumericalDatasets)           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 VISUAL VERIFIER ENGINE (VisualVerifier)                     │
│                                                                             │
│  1. Input Normalizer (AuditedSceneContext)                                  │
│  2. Parameter Extractor (Timelines, Stats, Quotes, Charts, Counts, Maps)    │
│  3. Cross-Modal Auditor (Audio vs Visual Semantics):                        │
│     ├─ Number & Multiplier Parser (|V_vis - V_audio| / V_vis <= 0.001)      │
│     ├─ Trend Polarity Matcher (sign(slope) == sign(spoken_trend))           │
│     ├─ Chronology Sequence Validator (t_{i} <= t_{i+1})                     │
│     ├─ Entity Count Reconciler (N_vis == N_audio)                           │
│     └─ Quote Exactness & Attribution Alignment                              │
│  4. Epistemic Grounding Auditor (Visual vs EvidenceGraph):                  │
│     ├─ Timeline Anachronism vs ClaimRecord.temporal_context                 │
│     ├─ Chart Data Point & Baseline Zero Lineage vs NumericalDataset         │
│     └─ Geospatial Territory Period Validity                                │
│  5. Evidence Graph Sync (inserts VisualElementNode & VerificationTraceNode) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       VisualVerificationReport                              │
│  • passed: bool (True iff zero BLOCK discrepancies)                         │
│  • verdict: "PASS" | "WARN" | "BLOCK"                                       │
│  • inconsistencies: List[VisualInconsistencyRecord]                         │
│  • scene_reports: List[SceneVisualReport]                                   │
│  • total_scenes_audited, total_elements_audited                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Data Models & Contract Definitions (`src/epistemic/visual_verifier.py`)

```python
"""src/epistemic/visual_verifier.py — Visual Fact-Checking & Storyboard Reconciliation Engine."""

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
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
    TemporalContext,
)
from src.epistemic.graph import (
    EdgeRelation,
    EvidenceGraph,
    GraphNodeType,
    VisualElementNode,
)


class VisualSeverity(str, Enum):
    """Severity of a detected visual inconsistency."""
    BLOCK = "BLOCK"  # Halts publishing pipeline; mandatory epistemic violation
    WARN = "WARN"    # Non-blocking advisory divergence for creator review


class VisualDiscrepancyType(str, Enum):
    """Categorical taxonomy of visual, numerical, and cross-modal factual errors."""
    # Numerical & Quantitative
    VISUAL_AUDIO_NUMERICAL_MISMATCH = "VISUAL_AUDIO_NUMERICAL_MISMATCH"
    VISUAL_AUDIO_UNIT_MISMATCH = "VISUAL_AUDIO_UNIT_MISMATCH"
    CHART_DATA_POINT_MISMATCH = "CHART_DATA_POINT_MISMATCH"
    CHART_TREND_CONTRADICTION = "CHART_TREND_CONTRADICTION"
    CHART_BASELINE_TRUNCATION = "CHART_BASELINE_TRUNCATION"
    CHART_AXIS_LABEL_MISMATCH = "CHART_AXIS_LABEL_MISMATCH"
    DANGLING_DATASET_BINDING = "DANGLING_DATASET_BINDING"

    # Chronology & Temporal
    VISUAL_AUDIO_TEMPORAL_MISMATCH = "VISUAL_AUDIO_TEMPORAL_MISMATCH"
    TIMELINE_CHRONOLOGY_INVERSION = "TIMELINE_CHRONOLOGY_INVERSION"
    TIMELINE_DATE_ANACHRONISM = "TIMELINE_DATE_ANACHRONISM"

    # Entity & Count
    VISUAL_COUNT_DISCREPANCY = "VISUAL_COUNT_DISCREPANCY"

    # Quote & Citation
    QUOTE_TEXT_DISTORTION = "QUOTE_TEXT_DISTORTION"
    QUOTE_ATTRIBUTION_MISMATCH = "QUOTE_ATTRIBUTION_MISMATCH"

    # Geospatial & Territorial
    GEOSPATIAL_BOUNDARY_MISMATCH = "GEOSPATIAL_BOUNDARY_MISMATCH"
    TERRITORY_LABEL_ANACHRONISM = "TERRITORY_LABEL_ANACHRONISM"


class VisualInconsistencyRecord(H9BaseModel):
    """Detailed forensic record of an identified visual factual error."""
    inconsistency_id: str = Field(default_factory=lambda: f"vdis_{uuid.uuid4().hex[:8]}")
    scene_id: str
    beat_id: Optional[str] = None
    block_type: str
    parameter_key: str
    discrepancy_type: VisualDiscrepancyType
    severity: VisualSeverity
    visual_value: Any
    expected_value: Any
    audio_text_snippet: Optional[str] = None
    evidence_claim_id: Optional[str] = None
    dataset_id: Optional[str] = None
    explanation: str
    remediation_suggestion: str
    detected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Backward-compatibility alias
VisualDiscrepancy = VisualInconsistencyRecord


class SceneVisualReport(H9BaseModel):
    """Per-scene visual verification summary."""
    scene_id: str
    scene_index: int = 1
    block_type: str
    passed: bool = True
    inconsistencies: List[VisualInconsistencyRecord] = Field(default_factory=list)


class VisualVerificationReport(H9BaseModel):
    """Master return contract for the Visual Fact-Checking Engine."""
    report_id: str = Field(default_factory=lambda: f"vrep_{uuid.uuid4().hex[:8]}")
    passed: bool = True
    verdict: str = "PASS"  # "PASS", "WARN", "BLOCK"
    total_scenes_audited: int = 0
    total_elements_audited: int = 0
    inconsistencies: List[VisualInconsistencyRecord] = Field(default_factory=list)
    scene_reports: List[SceneVisualReport] = Field(default_factory=list)
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def discrepancies(self) -> List[VisualInconsistencyRecord]:
        """Synonym for inconsistencies."""
        return self.inconsistencies

    @property
    def block_count(self) -> int:
        return sum(1 for i in self.inconsistencies if i.severity == VisualSeverity.BLOCK)

    @property
    def warn_count(self) -> int:
        return sum(1 for i in self.inconsistencies if i.severity == VisualSeverity.WARN)
```

---

### 4.3 Element Extraction & Verification Specifications

#### 1. Timelines (`_verify_timeline`)
- **Extracted Fields**:
  - `milestones`: List of objects containing `year` / `date`, `title`, `description`.
- **Chronological Sequencing**:
  - Parse every milestone date into an absolute numerical or timestamp representation (e.g. `1947`, `1954`, `1958`, `1971`).
  - **Invariant**: For consecutive visual milestones $M_i$ and $M_{i+1}$, $T(M_i) \le T(M_{i+1})$.
  - If $T(M_i) > T(M_{i+1})$:
    - Emit `VisualInconsistencyRecord` with `TIMELINE_CHRONOLOGY_INVERSION`, `severity=VisualSeverity.BLOCK`.
    - Explanation: *"Milestone '{title_i}' ({year_i}) precedes '{title_next}' ({year_next}) on the visual timeline track."*
- **Date Consistency vs Script Narration**:
  - Extract all years/dates mentioned in the concurrent speech beat text.
  - If beat mentions a distinct year $Y_{\text{audio}}$ that differs from all on-screen milestone years, and narration does not frame it as background context, emit `VISUAL_AUDIO_TEMPORAL_MISMATCH` (`severity=VisualSeverity.BLOCK`).
- **Anachronism vs Evidence Graph**:
  - For each milestone linked to a grounded claim, check `ClaimRecord.temporal_context`.
  - If the visual year falls outside $[T_{\text{valid\_from}}, T_{\text{valid\_until}}]$, emit `TIMELINE_DATE_ANACHRONISM` (`severity=VisualSeverity.BLOCK`).

#### 2. Charts & Numerical Visualizations (`_verify_chart`)
- **Data Points vs Backing Dataset**:
  - If block specifies `dataset_id`:
    - Retrieve `NumericalDataset` from evidence graph or dossier.
    - If `dataset_id` not found in evidence store: Emit `DANGLING_DATASET_BINDING` (`severity=VisualSeverity.BLOCK`).
    - Verify that visual points $(x_i, y_i)$ match dataset points within numerical tolerance ($<0.01\%$).
- **Trend Reconciliation vs Narration**:
  - Compute mathematical trend from visual points:
    $$\text{Trend}_{\text{vis}} = \begin{cases} +1 & \text{if } y_n > y_1 \\ -1 & \text{if } y_n < y_1 \\ 0 & \text{if } y_n = y_1 \end{cases}$$
  - Extract directional trend polarity from audio text:
    - Positive tokens: `["increase", "grew", "growth", "surged", "rose", "rising", "jumped", "upward"]` $\to +1$.
    - Negative tokens: `["fell", "decreased", "drop", "plummeted", "declined", "downturn", "loss", "falling"]` $\to -1$.
    - Neutral/Flat tokens: `["plateaued", "steady", "stable", "unchanged", "stagnant"]` $\to 0$.
  - **Cross-Modal Invariant**: If $\text{AudioTrend} \ne 0$ and $\text{Trend}_{\text{vis}} \ne 0$ and $\text{Trend}_{\text{vis}} \ne \text{AudioTrend}$:
    - Emit `CHART_TREND_CONTRADICTION` (`severity=VisualSeverity.BLOCK`).
    - Explanation: *"Narration asserts negative trend ('{snippet}'), but visual chart depicts upward trajectory ($y_1={y_1}, y_n={y_n}$)."*
- **Baseline Zero Invariant**:
  - For bar charts, column charts, or comparative histograms:
  - If all data values $y_i > 0$, the $y$-axis origin $Y_{\min}$ must be $\le 0.0$.
  - If $Y_{\min} > 0.0$ (e.g. axis truncated at $y=90$ to make a $92$ vs $95$ difference appear $5\times$ larger), emit `CHART_BASELINE_TRUNCATION` (`severity=VisualSeverity.BLOCK`).
- **Axis Labels & Units**:
  - Verify that visual axis labels or unit markers match the dataset unit ($x\_\text{unit}, y\_\text{unit}$) and narration units.

#### 3. Counts & Quantities (`_verify_counts`)
- **Entity Count Reconciliation**:
  - Blocks such as `reference_collage_hook`, `split_screen_intro`, or multi-card lists display a discrete integer quantity of panels/images ($N_{\text{vis}} = \text{len}(\text{image\_paths})$ or panel count).
  - Extract verbal entity count expressions from concurrent narration:
    - Regular expression: `(?:\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+))\s+(?:key\s+)?(?:breakthroughs|phases|pillars|factors|steps|innovations|models|principles|elements|founders)`
    - Convert number word to integer $N_{\text{audio}}$ (e.g. *"three"* $\to 3$).
  - If $N_{\text{audio}}$ is detected and $N_{\text{vis}} \ne N_{\text{audio}}$:
    - Emit `VISUAL_COUNT_DISCREPANCY`.
    - Severity: `BLOCK` if error $> 1$ or if narration specifically highlights the visual layout (*"these three items shown here"*); `WARN` if colloquial phrasing (*"a couple"*).

#### 4. Maps & Geospatial Elements (`_verify_geospatial`)
- **Territory Label Anachronisms**:
  - When visual parameters include geographic regions or map entity labels (e.g. `"territory"`, `"country"`, `"boundary_label"`, `"location"`):
  - Check the historical era corresponding to scene timestamp.
  - Era dictionary checks:
    - `"Soviet Union"` / `"USSR"` valid only in $[1922, 1991]$. Labeling 1995 as "Soviet Union" or labeling 1940 as "Russian Federation" emits `TERRITORY_LABEL_ANACHRONISM` (`severity=VisualSeverity.BLOCK`).
    - `"Ottoman Empire"` valid only in $[1299, 1922]$.
    - `"Prussia"` valid only until $1947$.
- **Geographic Boundary Consistency**:
  - Ensure map borders asserted as national territories match the geopolitical status asserted in evidence claims. Disputed borders marked as undisputed emit `GEOSPATIAL_BOUNDARY_MISMATCH` (`severity=VisualSeverity.WARN`).

#### 5. Statistics & Quotes (`_verify_statistic` & `_verify_quote`)
- **Statistic Reveal**:
  - Parse on-screen `target_number` (e.g. `"$4.2M"`, `"100 Billion"`, `"95%"`).
  - Parse audio text for corresponding numerical mentions.
  - Calculate relative error:
    $$\text{Error} = \frac{|V_{\text{vis}} - V_{\text{audio}}|}{V_{\text{vis}}}$$
  - If $\text{Error} > 0.001$ ($0.1\%$):
    - Emit `VISUAL_AUDIO_NUMERICAL_MISMATCH` (`severity=VisualSeverity.BLOCK`).
  - If visual unit is `"M"` ($10^6$) and audio narrates *"billion"* ($10^9$), emit `VISUAL_AUDIO_UNIT_MISMATCH` (`severity=VisualSeverity.BLOCK`).
- **Quote Highlight**:
  - Compare `quote_text` to primary quote text or spoken text using character-level Levenshtein similarity.
  - If similarity $< 0.98$ and not marked as paraphrase: emit `QUOTE_TEXT_DISTORTION` (`severity=VisualSeverity.BLOCK`).
  - If on-screen `author_name` differs from spoken author name: emit `QUOTE_ATTRIBUTION_MISMATCH` (`severity=VisualSeverity.BLOCK`).

---

### 4.4 Complete Implementation Architecture of `VisualVerifier`

Here is the exact code architecture for `src/epistemic/visual_verifier.py`:

```python
class VisualVerifier:
    """Production visual fact-checking engine auditing storyboards against audio & evidence."""

    def __init__(
        self,
        verifier_name: str = "H9VisualFactChecker",
        relative_numerical_tolerance: float = 0.001,  # 0.1% tolerance
        enforce_zero_baseline: bool = True,
        sync_to_graph: bool = True,
    ) -> None:
        self.verifier_name = verifier_name
        self.tolerance = relative_numerical_tolerance
        self.enforce_zero_baseline = enforce_zero_baseline
        self.sync_to_graph = sync_to_graph

    # -----------------------------------------------------------------------
    # Primary Public Verification Interface
    # -----------------------------------------------------------------------
    def verify_visuals(
        self,
        storyboard: Union[Script, Any, Dict[str, Any]],
        graph: Optional[EvidenceGraph] = None,
        script: Optional[Script] = None,
    ) -> VisualVerificationReport:
        """Executes full visual fact-checking audit across all scenes."""
        scenes = self._normalize_scenes(storyboard, script)
        all_inconsistencies: List[VisualInconsistencyRecord] = []
        scene_reports: List[SceneVisualReport] = []
        total_elements = 0

        for sc in scenes:
            sc_inconsistencies, elem_count = self.verify_scene(sc, graph)
            total_elements += elem_count
            all_inconsistencies.extend(sc_inconsistencies)
            scene_reports.append(
                SceneVisualReport(
                    scene_id=sc["scene_id"],
                    scene_index=sc["scene_index"],
                    block_type=sc["block_type"],
                    passed=not any(i.severity == VisualSeverity.BLOCK for i in sc_inconsistencies),
                    inconsistencies=sc_inconsistencies,
                )
            )

        # Verdict calculation
        has_blocks = any(i.severity == VisualSeverity.BLOCK for i in all_inconsistencies)
        has_warns = any(i.severity == VisualSeverity.WARN for i in all_inconsistencies)
        verdict = "BLOCK" if has_blocks else ("WARN" if has_warns else "PASS")
        passed = not has_blocks

        # Optional EvidenceGraph sync
        if self.sync_to_graph and graph is not None:
            self._sync_verification_to_graph(graph, all_inconsistencies, verdict)

        return VisualVerificationReport(
            passed=passed,
            verdict=verdict,
            total_scenes_audited=len(scenes),
            total_elements_audited=total_elements,
            inconsistencies=all_inconsistencies,
            scene_reports=scene_reports,
        )

    # -----------------------------------------------------------------------
    # Per-Scene Verification
    # -----------------------------------------------------------------------
    def verify_scene(
        self,
        scene_ctx: Dict[str, Any],
        graph: Optional[EvidenceGraph] = None,
    ) -> Tuple[List[VisualInconsistencyRecord], int]:
        """Audits an individual scene's visual parameters against audio and evidence."""
        btype = scene_ctx.get("block_type", "")
        props = scene_ctx.get("parameters", {})
        beat_text = scene_ctx.get("narration_text", "")
        scene_id = scene_ctx.get("scene_id", "scene_unknown")
        inconsistencies: List[VisualInconsistencyRecord] = []
        element_count = len(props)

        # 1. Timeline Reveal Audit
        if btype == "timeline_reveal" or "milestones" in props:
            self._audit_timeline(scene_id, props, beat_text, graph, inconsistencies)

        # 2. Statistic Reveal Audit
        elif btype == "statistic_reveal" or "target_number" in props:
            self._audit_statistic(scene_id, props, beat_text, graph, inconsistencies)

        # 3. Quote Highlight Audit
        elif btype == "quote_highlight" or "quote_text" in props:
            self._audit_quote(scene_id, props, beat_text, graph, inconsistencies)

        # 4. Comparison Panel & Chart Data Audit
        elif btype == "comparison_panel" or "comparison_rows" in props:
            self._audit_comparison_panel(scene_id, props, beat_text, graph, inconsistencies)

        # 5. Chart / Data Visualization Audit (generic or chart block)
        if "chart_data" in props or "data_points" in props or props.get("dataset_id"):
            self._audit_chart(scene_id, props, beat_text, graph, inconsistencies)

        # 6. Entity Count Audit (collages, grids, cards)
        if btype in ["reference_collage_hook", "creator_bottom_collage", "split_screen_intro"] or "image_paths" in props:
            self._audit_entity_counts(scene_id, btype, props, beat_text, inconsistencies)

        # 7. Geospatial & Territorial Audit
        if "territory" in props or "map_regions" in props or "country" in props:
            self._audit_geospatial(scene_id, props, beat_text, graph, inconsistencies)

        return inconsistencies, element_count
```

---

### 4.5 Helper Parsing & NLP Analysis Implementations

```python
    # -----------------------------------------------------------------------
    # Helper: Number & Multiplier Parsing
    # -----------------------------------------------------------------------
    @staticmethod
    def parse_number_with_multiplier(text: str) -> Optional[float]:
        """Parses strings like '$4.2B', '100 million', '50K', '95%' into raw floats."""
        if not text:
            return None
        cleaned = text.replace("$", "").replace(",", "").replace("+", "").strip().lower()
        multiplier = 1.0

        if cleaned.endswith("b") or "billion" in cleaned:
            multiplier = 1e9
            cleaned = re.sub(r"(billion|b)", "", cleaned).strip()
        elif cleaned.endswith("m") or "million" in cleaned:
            multiplier = 1e6
            cleaned = re.sub(r"(million|m)", "", cleaned).strip()
        elif cleaned.endswith("k") or "thousand" in cleaned:
            multiplier = 1e3
            cleaned = re.sub(r"(thousand|k)", "", cleaned).strip()
        elif cleaned.endswith("%") or "percent" in cleaned:
            multiplier = 1.0  # Keep base percentage value
            cleaned = re.sub(r"(percent|%)", "", cleaned).strip()

        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if match:
            try:
                return float(match.group(0)) * multiplier
            except ValueError:
                return None
        return None

    @staticmethod
    def extract_audio_numbers(text: str) -> List[Tuple[float, str]]:
        """Extracts numerical quantities and multipliers mentioned in spoken text."""
        results = []
        # Word number map
        word_nums = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "hundred": 100, "thousand": 1e3, "million": 1e6, "billion": 1e9,
        }
        # Regex for digits with optional multiplier
        pattern = r"(\b\d+(?:\.\d+)?)\s*(billion|million|thousand|k|m|b|%|percent)?"
        for m in re.finditer(pattern, text, re.IGNORECASE):
            val = float(m.group(1))
            mult = (m.group(2) or "").lower()
            if mult in ["billion", "b"]:
                val *= 1e9
            elif mult in ["million", "m"]:
                val *= 1e6
            elif mult in ["thousand", "k"]:
                val *= 1e3
            results.append((val, m.group(0)))
        return results

    @staticmethod
    def extract_trend_polarity(text: str) -> int:
        """Determines verbal trend direction (+1=rising, -1=falling, 0=neutral/none)."""
        lower = text.lower()
        up_words = ["increase", "increased", "growing", "grew", "surged", "rose", "rising", "jumped", "upward", "doubled", "tripled"]
        down_words = ["decrease", "decreased", "fell", "falling", "dropped", "drop", "plummeted", "declined", "downturn", "loss", "lower"]
        up_score = sum(1 for w in up_words if w in lower)
        down_score = sum(1 for w in down_words if w in lower)
        if up_score > down_score:
            return 1
        elif down_score > up_score:
            return -1
        return 0

    @staticmethod
    def extract_stated_entity_count(text: str) -> Optional[int]:
        """Extracts spoken count assertions like 'three breakthroughs'."""
        word_to_int = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        }
        pattern = r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:key\s+|distinct\s+|major\s+)?(phases|breakthroughs|steps|pillars|innovations|models|categories|types|panels|components)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_cnt = match.group(1).lower()
            if raw_cnt in word_to_int:
                return word_to_int[raw_cnt]
            try:
                return int(raw_cnt)
            except ValueError:
                return None
        return None
```

---

### 4.6 Concrete Audit Routine Implementations

```python
    # -----------------------------------------------------------------------
    # 1. Timeline Audit
    # -----------------------------------------------------------------------
    def _audit_timeline(
        self,
        scene_id: str,
        props: Dict[str, Any],
        beat_text: str,
        graph: Optional[EvidenceGraph],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        milestones = props.get("milestones", [])
        if not isinstance(milestones, list) or len(milestones) < 2:
            return

        parsed_years: List[Tuple[int, Dict[str, Any]]] = []
        for idx, m in enumerate(milestones):
            raw_year = m.get("year", m.get("date", ""))
            y_match = re.search(r"\b(1\d{3}|20\d{2})\b", str(raw_year))
            if y_match:
                parsed_years.append((int(y_match.group(1)), m))

        # A. Chronology Inversion Check
        for i in range(len(parsed_years) - 1):
            y_curr, m_curr = parsed_years[i]
            y_next, m_next = parsed_years[i + 1]
            if y_curr > y_next:
                inconsistencies.append(
                    VisualInconsistencyRecord(
                        scene_id=scene_id,
                        block_type="timeline_reveal",
                        parameter_key="milestones",
                        discrepancy_type=VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION,
                        severity=VisualSeverity.BLOCK,
                        visual_value=f"{y_curr} preceding {y_next}",
                        expected_value=f"{y_next} after {y_curr}",
                        explanation=(
                            f"Chronological inversion in scene '{scene_id}': Milestone '{m_curr.get('title')}' "
                            f"({y_curr}) is placed before '{m_next.get('title')}' ({y_next})."
                        ),
                        remediation_suggestion=f"Reorder timeline milestones so {y_curr} appears after {y_next}.",
                    )
                )

        # B. Spoken Audio Date Mismatch Check
        spoken_years = [int(y) for y in re.findall(r"\b(1\d{3}|20\d{2})\b", beat_text)]
        if spoken_years and parsed_years:
            vis_year_set = {py[0] for py in parsed_years}
            # If spoken year is completely unrepresented and distinct
            for sy in spoken_years:
                if sy not in vis_year_set and not any(abs(sy - vy) <= 1 for vy in vis_year_set):
                    inconsistencies.append(
                        VisualInconsistencyRecord(
                            scene_id=scene_id,
                            block_type="timeline_reveal",
                            parameter_key="year",
                            discrepancy_type=VisualDiscrepancyType.VISUAL_AUDIO_TEMPORAL_MISMATCH,
                            severity=VisualSeverity.BLOCK,
                            visual_value=list(vis_year_set),
                            expected_value=sy,
                            audio_text_snippet=beat_text[:100],
                            explanation=f"Audio speaks of year {sy}, but timeline milestones only display {list(vis_year_set)}.",
                            remediation_suggestion=f"Align visual timeline milestones to cover year {sy}.",
                        )
                    )

    # -----------------------------------------------------------------------
    # 2. Statistic Audit
    # -----------------------------------------------------------------------
    def _audit_statistic(
        self,
        scene_id: str,
        props: Dict[str, Any],
        beat_text: str,
        graph: Optional[EvidenceGraph],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        target_str = str(props.get("target_number", ""))
        vis_val = self.parse_number_with_multiplier(target_str)
        if vis_val is None:
            return

        audio_nums = self.extract_audio_numbers(beat_text)
        if not audio_nums:
            return

        # Find closest spoken number
        best_match = None
        best_rel_err = float("inf")
        for a_val, raw_snippet in audio_nums:
            if vis_val == 0.0:
                err = abs(a_val)
            else:
                err = abs(vis_val - a_val) / abs(vis_val)
            if err < best_rel_err:
                best_rel_err = err
                best_match = (a_val, raw_snippet)

        if best_match and best_rel_err > self.tolerance:
            # Check for unit order-of-magnitude inversion (e.g. million vs billion)
            is_unit_mismatch = (best_rel_err > 10.0 or best_rel_err < 0.1) and (
                ("million" in beat_text.lower() and ("b" in target_str.lower() or "billion" in target_str.lower()))
                or ("billion" in beat_text.lower() and ("m" in target_str.lower() or "million" in target_str.lower()))
            )
            disc_type = (
                VisualDiscrepancyType.VISUAL_AUDIO_UNIT_MISMATCH
                if is_unit_mismatch
                else VisualDiscrepancyType.VISUAL_AUDIO_NUMERICAL_MISMATCH
            )
            inconsistencies.append(
                VisualInconsistencyRecord(
                    scene_id=scene_id,
                    block_type="statistic_reveal",
                    parameter_key="target_number",
                    discrepancy_type=disc_type,
                    severity=VisualSeverity.BLOCK,
                    visual_value=target_str,
                    expected_value=best_match[1],
                    audio_text_snippet=beat_text[:120],
                    explanation=(
                        f"Numerical contradiction in scene '{scene_id}': Visual displays '{target_str}' ({vis_val:g}), "
                        f"while voiceover narrates '{best_match[1]}' ({best_match[0]:g}). Relative error: {best_rel_err:.2%}."
                    ),
                    remediation_suggestion=f"Synchronize visual stat target_number to match narration: '{best_match[1]}'.",
                )
            )

    # -----------------------------------------------------------------------
    # 3. Chart Audit (Trends & Baseline Zero)
    # -----------------------------------------------------------------------
    def _audit_chart(
        self,
        scene_id: str,
        props: Dict[str, Any],
        beat_text: str,
        graph: Optional[EvidenceGraph],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        points = props.get("data_points") or props.get("chart_data") or []
        if isinstance(points, list) and len(points) >= 2:
            # A. Trend polarity check
            y_vals = []
            for p in points:
                if isinstance(p, dict) and "y" in p:
                    y_vals.append(float(p["y"]))
                elif isinstance(p, (int, float)):
                    y_vals.append(float(p))

            if len(y_vals) >= 2:
                vis_trend = 1 if y_vals[-1] > y_vals[0] else (-1 if y_vals[-1] < y_vals[0] else 0)
                audio_trend = self.extract_trend_polarity(beat_text)

                if audio_trend != 0 and vis_trend != 0 and vis_trend != audio_trend:
                    inconsistencies.append(
                        VisualInconsistencyRecord(
                            scene_id=scene_id,
                            block_type="chart",
                            parameter_key="data_points",
                            discrepancy_type=VisualDiscrepancyType.CHART_TREND_CONTRADICTION,
                            severity=VisualSeverity.BLOCK,
                            visual_value="UPWARD" if vis_trend == 1 else "DOWNWARD",
                            expected_value="UPWARD" if audio_trend == 1 else "DOWNWARD",
                            audio_text_snippet=beat_text[:120],
                            explanation=(
                                f"Cross-modal trend conflict in scene '{scene_id}': Audio narrates "
                                f"{'growth/increase' if audio_trend==1 else 'decline/fall'}, but visual chart plots "
                                f"{'upward' if vis_trend==1 else 'downward'} progression ({y_vals[0]} -> {y_vals[-1]})."
                            ),
                            remediation_suggestion="Invert or update chart data points to reflect spoken narrative trend.",
                        )
                    )

            # B. Baseline Zero check for bar/column charts
            chart_type = str(props.get("chart_type", "bar")).lower()
            if self.enforce_zero_baseline and "bar" in chart_type and y_vals:
                min_y = min(y_vals)
                axis_y_min = float(props.get("y_axis_min", min_y))
                if all(y > 0 for y in y_vals) and axis_y_min > 0:
                    inconsistencies.append(
                        VisualInconsistencyRecord(
                            scene_id=scene_id,
                            block_type="chart",
                            parameter_key="y_axis_min",
                            discrepancy_type=VisualDiscrepancyType.CHART_BASELINE_TRUNCATION,
                            severity=VisualSeverity.BLOCK,
                            visual_value=axis_y_min,
                            expected_value=0.0,
                            explanation=(
                                f"Misleading chart baseline in scene '{scene_id}': Bar chart y-axis origin is truncated "
                                f"at {axis_y_min} instead of 0.0, visually exaggerating variations."
                            ),
                            remediation_suggestion="Set chart y-axis minimum to 0.0 to comply with data visualization integrity policy.",
                        )
                    )

    # -----------------------------------------------------------------------
    # 4. Entity Count Audit
    # -----------------------------------------------------------------------
    def _audit_entity_counts(
        self,
        scene_id: str,
        btype: str,
        props: Dict[str, Any],
        beat_text: str,
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        stated_cnt = self.extract_stated_entity_count(beat_text)
        if stated_cnt is None:
            return

        # Determine visual entity count
        vis_cnt = None
        if "image_paths" in props and isinstance(props["image_paths"], list):
            vis_cnt = len(props["image_paths"])
        elif "panel_count" in props:
            vis_cnt = int(props["panel_count"])
        elif btype == "split_screen_intro":
            vis_cnt = 2

        if vis_cnt is not None and vis_cnt != stated_cnt:
            inconsistencies.append(
                VisualInconsistencyRecord(
                    scene_id=scene_id,
                    block_type=btype,
                    parameter_key="image_paths",
                    discrepancy_type=VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY,
                    severity=VisualSeverity.WARN if abs(vis_cnt - stated_cnt) == 1 else VisualSeverity.BLOCK,
                    visual_value=vis_cnt,
                    expected_value=stated_cnt,
                    audio_text_snippet=beat_text[:120],
                    explanation=(
                        f"Count discrepancy in scene '{scene_id}': Voiceover asserts {stated_cnt} entities, "
                        f"but component '{btype}' renders {vis_cnt} visual panels."
                    ),
                    remediation_suggestion=f"Adjust on-screen panel count or images to match spoken quantity: {stated_cnt}.",
                )
            )

    # -----------------------------------------------------------------------
    # 5. Geospatial Audit
    # -----------------------------------------------------------------------
    def _audit_geospatial(
        self,
        scene_id: str,
        props: Dict[str, Any],
        beat_text: str,
        graph: Optional[EvidenceGraph],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        territory = str(props.get("territory", props.get("country", ""))).strip()
        if not territory:
            return

        # Extract year from beat or scene
        y_match = re.search(r"\b(1\d{3}|20\d{2})\b", beat_text)
        if not y_match:
            return
        year = int(y_match.group(1))

        # Check known historical entity periods
        HISTORICAL_BOUNDARIES = {
            "soviet union": (1922, 1991),
            "ussr": (1922, 1991),
            "ottoman empire": (1299, 1922),
            "austria-hungary": (1867, 1918),
            "prussia": (1525, 1947),
        }
        low_t = territory.lower()
        if low_t in HISTORICAL_BOUNDARIES:
            start_y, end_y = HISTORICAL_BOUNDARIES[low_t]
            if year < start_y or year > end_y:
                inconsistencies.append(
                    VisualInconsistencyRecord(
                        scene_id=scene_id,
                        block_type="map",
                        parameter_key="territory",
                        discrepancy_type=VisualDiscrepancyType.TERRITORY_LABEL_ANACHRONISM,
                        severity=VisualSeverity.BLOCK,
                        visual_value=f"{territory} in {year}",
                        expected_value=f"Valid period: {start_y}-{end_y}",
                        explanation=f"Geographical anachronism in scene '{scene_id}': '{territory}' did not exist in year {year}.",
                        remediation_suggestion=f"Update territorial label to match political entity in {year}.",
                    )
                )

    # -----------------------------------------------------------------------
    # EvidenceGraph Synchronization
    # -----------------------------------------------------------------------
    def _sync_verification_to_graph(
        self,
        graph: EvidenceGraph,
        inconsistencies: List[VisualInconsistencyRecord],
        verdict: str,
    ) -> None:
        """Registers visual verification trace node in the EvidenceGraph DAG."""
        trace_id = f"trace_vis_{uuid.uuid4().hex[:8]}"
        warnings = [i.explanation for i in inconsistencies]
        # Graph trace insertion
        try:
            graph.add_verification_trace(
                target_node_id=graph.graph_id,
                strategy_used="VISUAL_FACT_CHECK",
                entailment_score=1.0 if verdict == "PASS" else (0.5 if verdict == "WARN" else 0.0),
                status_assigned="verified" if verdict == "PASS" else ("partially_supported" if verdict == "WARN" else "contradicted"),
                verifier_name=self.verifier_name,
                audit_notes=f"Visual verification completed with verdict {verdict}. Total inconsistencies: {len(inconsistencies)}",
                warnings=warnings,
                node_id=trace_id,
            )
        except Exception:
            pass  # Fallback gracefully if graph target_node_id not bound
```

---

## 5. Verification Method

To independently test and verify the visual fact-checking engine:

### 5.1 Unit & Integration Test Suite (`tests/epistemic/test_visual_verifier.py`)
Implement the test suite verifying:
1. **Numerical Discrepancy Detection**:
   - Spoken narration: *"The project cost 4.2 million dollars"*.
   - Visual stat reveal: `target_number="$4.2B"`.
   - Assert: returns `passed=False`, `verdict="BLOCK"`, discrepancy type `VISUAL_AUDIO_UNIT_MISMATCH`.
2. **Timeline Inversion Detection**:
   - Visual milestones: `[{"year": "1954", "title": "B"}, {"year": "1947", "title": "A"}]`.
   - Assert: returns `passed=False`, discrepancy type `TIMELINE_CHRONOLOGY_INVERSION`.
3. **Chart Trend Contradiction**:
   - Spoken narration: *"Revenue fell precipitously over the next two quarters"*.
   - Visual chart data points: `[{"x": 1, "y": 10}, {"x": 2, "y": 50}, {"x": 3, "y": 120}]`.
   - Assert: returns `passed=False`, discrepancy type `CHART_TREND_CONTRADICTION`.
4. **Baseline Zero Enforcement**:
   - Visual bar chart points with $y \in [90, 100]$ and `y_axis_min=85`.
   - Assert: flags `CHART_BASELINE_TRUNCATION` with `VisualSeverity.BLOCK`.
5. **Entity Count Matching**:
   - Spoken narration: *"Three distinct innovations occurred"*.
   - Visual `image_paths`: 5 image paths.
   - Assert: flags `VISUAL_COUNT_DISCREPANCY`.
6. **State Machine Gate Integration**:
   - Verify `StateMachine.evaluate_gate("VISUAL_FACT_CHECK", context)` returns `GateOutcome.BLOCK` when report contains `BLOCK` severity records.

### 5.2 Test Execution Command
```bash
# Execute standalone epistemic visual verifier unit tests
pytest tests/epistemic/test_visual_verifier.py -v

# Run full epistemic verification regression suite
pytest tests/test_evidence_graph.py tests/test_historical_policy.py tests/test_verification_engine.py -v
```

### 5.3 Invalidation Conditions
- An error is reported if relative numerical error threshold is breached on true approximate phrasing (e.g. *"nearly four million"* paired with `"$3.9M"` should be accepted under `PARTIALLY_SUPPORTED` / `WARN`).
- Invalidation occurs if the verifier crashes on missing optional fields (`parameters`, `beats`) instead of using resilient schema normalization.
