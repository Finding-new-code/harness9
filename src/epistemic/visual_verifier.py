"""src/epistemic/visual_verifier.py — Visual Fact-Checking & Storyboard Reconciliation Engine.

Audits rendered storyboard elements, timelines, charts, entity counts, quotes,
and geospatial territory maps against spoken narration and the EvidenceGraph DAG.
Enforces zero-baseline anti-distortion on bar charts, chronology monotonicity,
and audio-visual numerical unit alignment.
"""

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
from src.epistemic.numerical_pipeline import NumericalDataset, NumericalInvariantChecker


# ===========================================================================
# 1. Enums & Core Contracts
# ===========================================================================

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
    visual_value: Any = None
    expected_value: Any = None
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
    block_type: str = ""
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


# Historical political entities and their recognized historical eras
HISTORICAL_BOUNDARIES: Dict[str, Tuple[int, int]] = {
    "soviet union": (1922, 1991),
    "ussr": (1922, 1991),
    "ottoman empire": (1299, 1922),
    "austria-hungary": (1867, 1918),
    "prussia": (1525, 1947),
    "russian empire": (1721, 1917),
    "weimar republic": (1918, 1933),
}


# ===========================================================================
# 2. Visual Fact-Checking Engine
# ===========================================================================

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
        script: Optional[Any] = None,
        datasets: Optional[Dict[str, NumericalDataset]] = None,
    ) -> VisualVerificationReport:
        """Executes full visual fact-checking audit across all scenes."""
        scenes = self._normalize_scenes(storyboard, script)
        all_inconsistencies: List[VisualInconsistencyRecord] = []
        scene_reports: List[SceneVisualReport] = []
        total_elements = 0

        last_timeline_scene_id: Optional[str] = None
        last_timeline_max_year: Optional[int] = None

        for sc in scenes:
            sc_inconsistencies, elem_count = self.verify_scene(sc, graph, datasets)
            total_elements += elem_count

            # Cross-scene timeline sequence audit
            sc_props = sc.get("parameters", {})
            sc_btype = sc.get("block_type", "")
            if sc_btype in ("timeline_reveal", "timeline") or "milestones" in sc_props:
                milestones = sc_props.get("milestones", [])
                if isinstance(milestones, list) and milestones:
                    sc_years = []
                    for m in milestones:
                        if isinstance(m, dict):
                            y_val = self.parse_year_value(m.get("year", m.get("date", "")))
                            if y_val is not None:
                                sc_years.append(y_val)
                    if sc_years:
                        sc_min_yr = min(sc_years)
                        sc_max_yr = max(sc_years)
                        is_flashback = bool(sc_props.get("flashback", False) or sc_props.get("non_linear", False))
                        if last_timeline_max_year is not None and sc_min_yr < last_timeline_max_year and not is_flashback:
                            cross_inversion = VisualInconsistencyRecord(
                                scene_id=sc["scene_id"],
                                block_type=sc_btype or "timeline_reveal",
                                parameter_key="milestones",
                                discrepancy_type=VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION,
                                severity=VisualSeverity.BLOCK,
                                visual_value=f"Scene '{last_timeline_scene_id}' ({last_timeline_max_year}) preceding Scene '{sc['scene_id']}' ({sc_min_yr})",
                                expected_value=f"Chronological continuity across scenes (year >= {last_timeline_max_year})",
                                explanation=(
                                    f"Cross-scene chronological inversion: Scene '{sc['scene_id']}' displays year {sc_min_yr}, "
                                    f"which is earlier than previous scene '{last_timeline_scene_id}' year {last_timeline_max_year}."
                                ),
                                remediation_suggestion="Reorder scenes or set 'flashback: True' to denote non-linear chronology.",
                            )
                            sc_inconsistencies.append(cross_inversion)
                        last_timeline_scene_id = sc["scene_id"]
                        last_timeline_max_year = sc_max_yr

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
        datasets: Optional[Dict[str, NumericalDataset]] = None,
    ) -> Tuple[List[VisualInconsistencyRecord], int]:
        """Audits an individual scene's visual parameters against audio and evidence."""
        btype = scene_ctx.get("block_type", "")
        props = scene_ctx.get("parameters", {})
        beat_text = scene_ctx.get("narration_text", "")
        scene_id = scene_ctx.get("scene_id", "scene_unknown")
        inconsistencies: List[VisualInconsistencyRecord] = []
        element_count = max(1, len(props))

        # 1. Timeline Reveal Audit
        if btype in ("timeline_reveal", "timeline") or "milestones" in props:
            self._audit_timeline(scene_id, props, beat_text, graph, inconsistencies)

        # 2. Statistic Reveal Audit
        elif btype in ("statistic_reveal", "statistic") or "target_number" in props:
            self._audit_statistic(scene_id, props, beat_text, graph, inconsistencies)

        # 3. Quote Highlight Audit
        elif btype in ("quote_highlight", "quote") or "quote_text" in props:
            self._audit_quote(scene_id, props, beat_text, graph, inconsistencies)

        # 4. Comparison Panel Audit
        elif btype in ("comparison_panel", "comparison") or "comparison_rows" in props:
            self._audit_comparison_panel(scene_id, props, beat_text, graph, inconsistencies)

        # 5. Chart / Data Visualization Audit
        if "chart_data" in props or "data_points" in props or props.get("dataset_id") or "bar" in btype or "chart" in btype:
            self._audit_chart(scene_id, props, beat_text, graph, datasets, inconsistencies)

        # 6. Entity Count Audit (collages, grids, cards)
        if btype in ("reference_collage_hook", "creator_bottom_collage", "split_screen_intro", "collage") or "image_paths" in props:
            self._audit_entity_counts(scene_id, btype, props, beat_text, inconsistencies)

        # 7. Geospatial & Territorial Audit
        if "territory" in props or "map_regions" in props or "country" in props:
            self._audit_geospatial(scene_id, props, beat_text, graph, inconsistencies)

        return inconsistencies, element_count

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
            if isinstance(m, dict):
                raw_year = m.get("year", m.get("date", ""))
                y_val = self.parse_year_value(raw_year)
                if y_val is not None:
                    parsed_years.append((y_val, m))

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
        spoken_years = self.extract_audio_years(beat_text)
        if spoken_years and parsed_years:
            vis_year_set = {py[0] for py in parsed_years}
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
                            audio_text_snippet=beat_text[:120],
                            explanation=f"Audio speaks of year {sy}, but timeline milestones only display {list(vis_year_set)}.",
                            remediation_suggestion=f"Align visual timeline milestones to cover year {sy}.",
                        )
                    )

        # C. Evidence Graph Temporal Bounds Check (Anachronism)
        if graph is not None and props.get("grounded_claim_ids"):
            for cid in props["grounded_claim_ids"]:
                node = graph._nodes.get(cid)
                if node:
                    tc = getattr(node, "temporal_context", None)
                    if (not tc or tc == {}) and hasattr(node, "claim_record") and node.claim_record:
                        tc = getattr(node.claim_record, "temporal_context", None)
                    if tc:
                        v_from = tc.get("valid_from") if isinstance(tc, dict) else getattr(tc, "valid_from", None)
                        v_until = tc.get("valid_until") if isinstance(tc, dict) else getattr(tc, "valid_until", None)
                        for py, m in parsed_years:
                            if v_from and py < int(v_from):
                                inconsistencies.append(
                                    VisualInconsistencyRecord(
                                        scene_id=scene_id,
                                        block_type="timeline_reveal",
                                        parameter_key="temporal_context",
                                        discrepancy_type=VisualDiscrepancyType.TIMELINE_DATE_ANACHRONISM,
                                        severity=VisualSeverity.BLOCK,
                                        visual_value=py,
                                        expected_value=f">={v_from}",
                                        explanation=f"Milestone date {py} precedes claim validity lower bound {v_from}.",
                                        remediation_suggestion=f"Update milestone year to fall within [{v_from}, {v_until or 'present'}].",
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
            is_unit_mismatch = (
                ("million" in beat_text.lower() and ("b" in target_str.lower() or "billion" in target_str.lower())) or
                ("billion" in beat_text.lower() and ("m" in target_str.lower() or "million" in target_str.lower())) or
                ("thousand" in beat_text.lower() and ("m" in target_str.lower() or "million" in target_str.lower()))
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
        datasets: Optional[Dict[str, NumericalDataset]],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        # Check dataset binding if dataset_id provided
        ds_id = props.get("dataset_id")
        ds = None
        if ds_id:
            if datasets and ds_id in datasets:
                ds = datasets[ds_id]
            if ds is None:
                # Dangling binding
                inconsistencies.append(
                    VisualInconsistencyRecord(
                        scene_id=scene_id,
                        block_type="chart",
                        parameter_key="dataset_id",
                        discrepancy_type=VisualDiscrepancyType.DANGLING_DATASET_BINDING,
                        severity=VisualSeverity.BLOCK,
                        visual_value=ds_id,
                        expected_value="Verified NumericalDataset",
                        explanation=f"Chart references dataset_id '{ds_id}' which does not exist in the evidence store.",
                        remediation_suggestion=f"Bind chart to an existing verified NumericalDataset.",
                    )
                )

        points = props.get("data_points") or props.get("chart_data") or []
        # Fallback to extracting data_points from referenced verified NumericalDataset
        if not points and ds is not None and hasattr(ds, "data_points") and ds.data_points:
            points = [{"x": p.x_value, "y": p.y_value, "label": getattr(p, "label", "")} for p in ds.data_points]
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
            allow_trunc = bool(props.get("allow_truncated_baseline", False))
            if self.enforce_zero_baseline and ("bar" in chart_type or "column" in chart_type) and y_vals:
                min_y = min(y_vals)
                axis_y_min = float(props.get("y_axis_min", min_y))
                if all(y > 0 for y in y_vals) and axis_y_min > 0 and not allow_trunc:
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
    # 4. Comparison Panel Audit
    # -----------------------------------------------------------------------
    def _audit_comparison_panel(
        self,
        scene_id: str,
        props: Dict[str, Any],
        beat_text: str,
        graph: Optional[EvidenceGraph],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        rows = props.get("comparison_rows", [])
        if not isinstance(rows, list):
            return

        lower_text = beat_text.lower()
        lower_synonyms = ["lower than", "less than", "smaller than", "below", "under", "worse than", "inferior to"]
        higher_synonyms = ["higher than", "greater than", "more than", "above", "better than", "superior to", "exceeded"]

        matched_lower = next((p for p in lower_synonyms if p in lower_text), None)
        matched_higher = next((p for p in higher_synonyms if p in lower_text), None)

        for r_idx, row in enumerate(rows):
            if isinstance(row, dict):
                metric = row.get("metric", "")
                val_a = row.get("val_a")
                val_b = row.get("val_b")
                num_a = val_a if isinstance(val_a, (int, float)) else self.parse_number_with_multiplier(str(val_a))
                num_b = val_b if isinstance(val_b, (int, float)) else self.parse_number_with_multiplier(str(val_b))

                if num_a is not None and num_b is not None:
                    # Case 1: val_a > val_b visually, but audio asserts lower relation
                    if num_a > num_b and matched_lower:
                        inconsistencies.append(
                            VisualInconsistencyRecord(
                                scene_id=scene_id,
                                block_type="comparison_panel",
                                parameter_key=f"comparison_rows[{r_idx}]",
                                discrepancy_type=VisualDiscrepancyType.CHART_TREND_CONTRADICTION,
                                severity=VisualSeverity.BLOCK,
                                visual_value=f"{val_a} > {val_b}",
                                expected_value=f"{val_a} < {val_b}",
                                audio_text_snippet=beat_text[:120],
                                explanation=f"Comparison row '{metric}' shows Entity A higher than B ({val_a} > {val_b}), but audio asserts '{matched_lower}'.",
                                remediation_suggestion="Align comparison row values to match voiceover narrative.",
                            )
                        )
                    # Case 2: val_a < val_b visually, but audio asserts higher relation
                    elif num_a < num_b and matched_higher:
                        inconsistencies.append(
                            VisualInconsistencyRecord(
                                scene_id=scene_id,
                                block_type="comparison_panel",
                                parameter_key=f"comparison_rows[{r_idx}]",
                                discrepancy_type=VisualDiscrepancyType.CHART_TREND_CONTRADICTION,
                                severity=VisualSeverity.BLOCK,
                                visual_value=f"{val_a} < {val_b}",
                                expected_value=f"{val_a} > {val_b}",
                                audio_text_snippet=beat_text[:120],
                                explanation=f"Comparison row '{metric}' shows Entity A lower than B ({val_a} < {val_b}), but audio asserts '{matched_higher}'.",
                                remediation_suggestion="Align comparison row values to match voiceover narrative.",
                            )
                        )

    # -----------------------------------------------------------------------
    # 5. Entity Count Audit
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
    # 6. Geospatial Audit
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

        y_match = re.search(r"\b(1\d{3}|20\d{2})\b", beat_text)
        if not y_match:
            return
        year = int(y_match.group(1))

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
    # 7. Quote Audit
    # -----------------------------------------------------------------------
    def _audit_quote(
        self,
        scene_id: str,
        props: Dict[str, Any],
        beat_text: str,
        graph: Optional[EvidenceGraph],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        vis_quote = str(props.get("quote_text", "")).strip()
        if not vis_quote:
            return

        author = str(props.get("author_name", "")).strip()
        if author and author.lower() not in beat_text.lower() and len(author) > 3:
            # Check if narration mentions a different author
            other_authors = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', beat_text)
            if other_authors and author not in other_authors:
                inconsistencies.append(
                    VisualInconsistencyRecord(
                        scene_id=scene_id,
                        block_type="quote_highlight",
                        parameter_key="author_name",
                        discrepancy_type=VisualDiscrepancyType.QUOTE_ATTRIBUTION_MISMATCH,
                        severity=VisualSeverity.BLOCK,
                        visual_value=author,
                        expected_value=other_authors[0],
                        audio_text_snippet=beat_text[:120],
                        explanation=f"Quote attribution mismatch: Visual displays '{author}', while voiceover names '{other_authors[0]}'.",
                        remediation_suggestion=f"Synchronize quote author to match audio voiceover: '{other_authors[0]}'.",
                    )
                )

    # -----------------------------------------------------------------------
    # Parsing Helpers
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
            multiplier = 1.0
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
        pattern = r'(\b\d+(?:\.\d+)?)\s*(billion|million|thousand|k|m|b|%|percent)?'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            val = float(m.group(1))
            mult = (m.group(2) or "").lower()
            if mult in ("billion", "b"):
                val *= 1e9
            elif mult in ("million", "m"):
                val *= 1e6
            elif mult in ("thousand", "k"):
                val *= 1e3
            results.append((val, m.group(0)))
        return results

    @staticmethod
    def parse_year_value(val: Any) -> Optional[int]:
        """Parses BCE/BC, CE/AD, signed integers, and standard years into signed integers.
        BCE/BC years are mapped to negative integers (e.g., '44 BCE' -> -44, '500 BCE' -> -500).
        """
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return int(val)
        s = str(val).strip()
        if not s:
            return None

        # 1. Negative integer string, e.g. "-44", "-500"
        if re.match(r'^-\d+$', s):
            return int(s)

        # 2. Year with BCE or BC suffix (e.g., "44 BCE", "500 BC", "44 B.C.E.")
        bce_match = re.search(r'\b(\d+)\s*(?:bce|bc|b\.c\.e\.|b\.c\.)\b', s, re.IGNORECASE)
        if bce_match:
            return -int(bce_match.group(1))

        # 3. Year with CE or AD prefix/suffix (e.g., "476 AD", "1995 CE")
        ce_match = re.search(r'\b(\d+)\s*(?:ce|ad|c\.e\.|a\.d\.)\b', s, re.IGNORECASE)
        if ce_match:
            return int(ce_match.group(1))

        # 4. Pure integer digits string
        if s.isdigit():
            return int(s)

        # 5. Embedded 4-digit year in date string (e.g. "1947-06-15", "October 1954")
        m4 = re.search(r'\b(1\d{3}|20\d{2})\b', s)
        if m4:
            return int(m4.group(1))

        return None

    @staticmethod
    def extract_audio_years(text: str) -> List[int]:
        """Extracts spoken years including BCE/BC and CE into signed integers."""
        years: List[int] = []
        # 1. Look for BCE/BC years
        for m in re.finditer(r'\b(\d+)\s*(?:bce|bc|b\.c\.e\.|b\.c\.)\b', text, re.IGNORECASE):
            years.append(-int(m.group(1)))
        # 2. Look for CE/AD years
        for m in re.finditer(r'\b(\d+)\s*(?:ce|ad|c\.e\.|a\.d\.)\b', text, re.IGNORECASE):
            years.append(int(m.group(1)))
        # 3. Look for 4-digit years (not part of BCE/BC/CE/AD)
        for m in re.finditer(r'\b(1\d{3}|20\d{2})\b', text):
            val = int(m.group(1))
            if val not in years and -val not in years:
                years.append(val)
        return years

    @staticmethod
    def extract_trend_polarity(text: str) -> int:
        """Determines verbal trend direction (+1=rising, -1=falling, 0=neutral/none)."""
        lower = text.lower()
        words_in_text = set(re.findall(r'\b[a-z]+\b', lower))

        up_words = {
            "increase", "increased", "increasing",
            "growing", "grew", "grow", "growth",
            "surged", "surging", "surge",
            "rose", "rising", "rise",
            "jumped", "jumping", "jump",
            "upward", "doubled", "tripled",
            "skyrocketed", "skyrocketing", "skyrocket",
            "exploded", "exploding",
            "boomed", "booming", "boom",
            "rallied", "rallying", "rally",
            "gained", "gaining", "gain", "gains",
        }
        down_words = {
            "decrease", "decreased", "decreasing",
            "fell", "falling", "fall",
            "dropped", "dropping", "drop",
            "plummeted", "plummeting", "plummet",
            "declined", "declining", "decline",
            "downturn", "loss", "losses", "lost", "lower",
            "crashed", "crashing", "crash",
            "collapsed", "collapsing", "collapse",
            "tanked", "tanking",
            "plunged", "plunging", "plunge",
            "slumped", "slumping", "slump",
            "nosedived", "nosediving", "nosedive",
        }

        up_score = len(up_words.intersection(words_in_text))
        down_score = len(down_words.intersection(words_in_text))
        if up_score > down_score:
            return 1
        elif down_score > up_score:
            return -1
        return 0

    @staticmethod
    def extract_stated_entity_count(text: str) -> Optional[int]:
        """Extracts spoken count assertions like 'three breakthroughs', 'three battalions',
        '5 vessels', 'one breakthrough', or 'dozens of breakthroughs'.
        """
        word_to_int = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "dozen": 12, "dozens": 24,
        }
        excluded_nouns = {
            "year", "years", "decade", "decades", "century", "centuries",
            "month", "months", "week", "weeks", "day", "days", "hour", "hours",
            "minute", "minutes", "second", "seconds", "percent", "percentage",
            "dollar", "dollars", "cent", "cents", "euro", "euros",
            "bce", "bc", "ce", "ad", "million", "billion", "trillion", "thousand",
            "times", "fold", "points", "point",
        }

        pattern = re.compile(
            r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|dozens|\d{1,3})\s+(?:of\s+)?(?:[a-zA-Z]{3,}\s+)?([a-zA-Z]{3,})\b',
            re.IGNORECASE
        )

        for m in pattern.finditer(text):
            raw_cnt = m.group(1).lower()
            noun = m.group(2).lower()
            if noun in excluded_nouns:
                continue
            if raw_cnt in word_to_int:
                return word_to_int[raw_cnt]
            if raw_cnt.isdigit():
                return int(raw_cnt)

        return None

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
        if not graph._nodes:
            return
        target_id = next(iter(graph._nodes.keys()))
        try:
            graph.add_verification_trace(
                target_node_id=target_id,
                strategy_used="VISUAL_FACT_CHECK",
                entailment_score=1.0 if verdict == "PASS" else (0.5 if verdict == "WARN" else 0.0),
                status_assigned="verified" if verdict == "PASS" else ("partially_supported" if verdict == "WARN" else "contradicted"),
                verifier_name=self.verifier_name,
                audit_notes=f"Visual verification completed with verdict {verdict}. Total inconsistencies: {len(inconsistencies)}",
                warnings=warnings,
                node_id=trace_id,
            )
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Normalization Helper
    # -----------------------------------------------------------------------
    def _normalize_scenes(self, storyboard: Any, script: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Polymorphically extracts scene context dictionaries from various H9 models."""
        scenes: List[Dict[str, Any]] = []

        # Case 1: Raw list of scenes
        if isinstance(storyboard, list):
            raw_scenes = storyboard
        # Case 2: Storyboard from script.py (scenes list)
        elif hasattr(storyboard, "scenes"):
            raw_scenes = storyboard.scenes
        elif isinstance(storyboard, dict) and "scenes" in storyboard:
            raw_scenes = storyboard["scenes"]
        else:
            raw_scenes = [storyboard] if isinstance(storyboard, dict) else []

        # If script provided separately, build narration lookup by scene_id or index
        narration_by_id: Dict[str, str] = {}
        if script is not None:
            if hasattr(script, "scenes"):
                for sc in script.scenes:
                    sid = getattr(sc, "scene_id", "")
                    ntext = getattr(sc, "narration_text", "") or getattr(sc, "narration", "")
                    if not ntext and hasattr(sc, "beats"):
                        ntext = " ".join(getattr(b, "text", "") for b in sc.beats)
                    narration_by_id[sid] = ntext

        for idx, sc in enumerate(raw_scenes, start=1):
            if isinstance(sc, dict):
                sc_id = sc.get("scene_id", f"scene_{idx}")
                btype = sc.get("component_type") or sc.get("block_type") or ""
                props = sc.get("component_props") or sc.get("parameters") or sc.get("props") or {}
                # Narration text fallback
                ntext = sc.get("narration_text") or sc.get("narration") or narration_by_id.get(sc_id, "")
                if not ntext and "beats" in sc:
                    ntext = " ".join(b.get("text", "") for b in sc["beats"] if isinstance(b, dict))
                scenes.append({
                    "scene_id": sc_id,
                    "scene_index": sc.get("scene_index", idx),
                    "block_type": btype,
                    "parameters": props,
                    "narration_text": ntext,
                })
            elif hasattr(sc, "scene_id"):
                sc_id = getattr(sc, "scene_id")
                btype = getattr(sc, "component_type", "") or getattr(sc, "block_type", "")
                props = getattr(sc, "component_props", {}) or getattr(sc, "parameters", {})
                ntext = getattr(sc, "narration_text", "") or getattr(sc, "narration", "") or narration_by_id.get(sc_id, "")
                if not ntext and hasattr(sc, "beats"):
                    ntext = " ".join(getattr(b, "text", "") for b in getattr(sc, "beats", []))
                scenes.append({
                    "scene_id": sc_id,
                    "scene_index": getattr(sc, "scene_index", idx),
                    "block_type": btype,
                    "parameters": props,
                    "narration_text": ntext,
                })

        return scenes
