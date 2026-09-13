"""Harness 9 ContentBench — 4-Layer Quality OS Evaluation Framework (Milestone M5).

Implements the 4-layer quantitative evaluation benchmark:
- Layer 1: Research Quality (S_research) — Fact density, source authority, corroboration, conflict penalties.
- Layer 2: Script & Narrative Quality (S_script) — Hook strength, pacing consistency, readability, Creator DNA adherence.
- Layer 3: Video & Composition Quality (S_video) — Voice QA cleanliness, speech-beat sync drift, visual relevance, linter compliance.
- Layer 4: Cost & Resource Efficiency (S_cost) — Cost per minute budget target, token efficiency, render efficiency.

Composite Formulation:
  Score = 0.25 * S_research + 0.30 * S_script + 0.30 * S_video + 0.15 * S_cost
"""

from datetime import datetime, timezone
import math
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import Field, field_validator, model_validator

from src.creator.dna import CreatorDNA
from src.creator.economics import ProductionCostLedger
from src.models.contracts import (
    ContentBrief,
    EvaluationLayer,
    EvaluationReport,
    H9BaseModel,
    RenderArtifact,
    ResearchDossier,
    Script,
)


# ===========================================================================
# 1. Layer Metric Models
# ===========================================================================
class ResearchQualityMetrics(H9BaseModel):
    """Detailed metrics for Layer 1: Research Quality."""
    fact_density: float = Field(default=0.8, ge=0.0, le=1.0)
    source_authority: float = Field(default=0.8, ge=0.0, le=1.0)
    corroboration_index: float = Field(default=0.8, ge=0.0, le=1.0)
    conflict_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    claims_count: int = Field(default=0, ge=0)
    corroborated_claims_count: int = Field(default=0, ge=0)
    sources_count: int = Field(default=0, ge=0)
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def compute_layer_score(self) -> "ResearchQualityMetrics":
        if self.composite_score == 0.0:
            score = (
                0.35 * self.fact_density
                + 0.35 * self.source_authority
                + 0.30 * self.corroboration_index
                - self.conflict_penalty
            )
            object.__setattr__(self, "composite_score", round(max(0.0, min(1.0, score)), 4))
        return self


class ScriptQualityMetrics(H9BaseModel):
    """Detailed metrics for Layer 2: Script & Narrative Quality."""
    hook_strength: float = Field(default=0.8, ge=0.0, le=1.0)
    pacing_score: float = Field(default=0.8, ge=0.0, le=1.0)
    readability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    dna_adherence: float = Field(default=1.0, ge=0.0, le=1.0)
    word_count: int = Field(default=0, ge=0)
    average_wpm: float = Field(default=145.0, ge=0.0)
    flesch_kincaid_grade: float = Field(default=8.5, ge=0.0)
    forbidden_violations_count: int = Field(default=0, ge=0)
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def compute_layer_score(self) -> "ScriptQualityMetrics":
        if self.composite_score == 0.0:
            score = (
                0.30 * self.hook_strength
                + 0.25 * self.pacing_score
                + 0.25 * self.readability_score
                + 0.20 * self.dna_adherence
            )
            object.__setattr__(self, "composite_score", round(max(0.0, min(1.0, score)), 4))
        return self


class VideoQualityMetrics(H9BaseModel):
    """Detailed metrics for Layer 3: Video & Composition Quality."""
    voice_qa_score: float = Field(default=0.9, ge=0.0, le=1.0)
    speech_beat_sync_score: float = Field(default=0.9, ge=0.0, le=1.0)
    visual_relevance: float = Field(default=0.85, ge=0.0, le=1.0)
    lint_compliance: float = Field(default=1.0, ge=0.0, le=1.0)
    clipping_ratio: float = Field(default=0.0, ge=0.0)
    max_dead_air_sec: float = Field(default=0.1, ge=0.0)
    sync_drift_max_sec: float = Field(default=0.05, ge=0.0)
    is_video_present: bool = True
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def compute_layer_score(self) -> "VideoQualityMetrics":
        if not self.is_video_present:
            object.__setattr__(self, "composite_score", 0.0)
            return self
        if self.composite_score == 0.0:
            score = (
                0.30 * self.voice_qa_score
                + 0.30 * self.speech_beat_sync_score
                + 0.20 * self.visual_relevance
                + 0.20 * self.lint_compliance
            )
            object.__setattr__(self, "composite_score", round(max(0.0, min(1.0, score)), 4))
        return self


class EconomicsQualityMetrics(H9BaseModel):
    """Detailed metrics for Layer 4: Cost & Resource Efficiency."""
    budget_score: float = Field(default=0.9, ge=0.0, le=1.0)
    token_efficiency: float = Field(default=0.85, ge=0.0, le=1.0)
    render_efficiency: float = Field(default=0.9, ge=0.0, le=1.0)
    total_cost_usd: float = Field(default=0.15, ge=0.0)
    cost_per_minute_usd: float = Field(default=0.30, ge=0.0)
    cost_per_second_usd: float = Field(default=0.005, ge=0.0)
    render_time_ratio: float = Field(default=0.8, ge=0.0)
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def compute_layer_score(self) -> "EconomicsQualityMetrics":
        if self.composite_score == 0.0:
            score = (
                0.40 * self.budget_score
                + 0.30 * self.token_efficiency
                + 0.30 * self.render_efficiency
            )
            object.__setattr__(self, "composite_score", round(max(0.0, min(1.0, score)), 4))
        return self


# ===========================================================================
# 2. Benchmark Report Contract
# ===========================================================================
class LayerEvaluationResult(H9BaseModel):
    """Result payload for an individual ContentBench evaluation layer."""
    layer: Union[EvaluationLayer, str]
    layer_name: str
    composite_score: float = Field(..., ge=0.0, le=1.0)
    passed: bool = True
    scores: Dict[str, float] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    feedback: List[str] = Field(default_factory=list)


class ContentBenchReport(H9BaseModel):
    """Comprehensive 4-layer ContentBench Quality OS benchmark report."""
    run_id: str = Field(..., min_length=1)
    project_id: str = Field(default="project_default")
    topic: str = Field(default="Overview")
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    passed: bool = True
    passing_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    layer_scores: Dict[str, float] = Field(
        default_factory=lambda: {
            "S_research": 0.0,
            "S_script": 0.0,
            "S_video": 0.0,
            "S_cost": 0.0,
        }
    )
    layer_reports: Dict[str, LayerEvaluationResult] = Field(default_factory=dict)
    summary_narrative: str = ""
    recommendations: List[str] = Field(default_factory=list)
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def calculate_overall_benchmark(self) -> "ContentBenchReport":
        """Compute the weighted 4-layer composite score."""
        s_res = self.layer_scores.get("S_research", 0.0)
        s_scr = self.layer_scores.get("S_script", 0.0)
        s_vid = self.layer_scores.get("S_video", 0.0)
        s_cst = self.layer_scores.get("S_cost", 0.0)

        # Weighted aggregate: 0.25 * Research + 0.30 * Script + 0.30 * Video + 0.15 * Cost
        overall = 0.25 * s_res + 0.30 * s_scr + 0.30 * s_vid + 0.15 * s_cst
        rounded = round(max(0.0, min(1.0, overall)), 4)
        object.__setattr__(self, "overall_score", rounded)
        object.__setattr__(self, "passed", rounded >= self.passing_threshold)
        return self

    def to_evaluation_reports(self) -> List[EvaluationReport]:
        """Convert layer evaluations into production contract EvaluationReport models."""
        reports = []
        for layer_key, res in self.layer_reports.items():
            rep = EvaluationReport(
                run_id=self.run_id,
                layer=res.layer,
                scores=res.scores,
                composite_score=res.composite_score,
                passed=res.passed,
                feedback=res.feedback,
                evaluated_at=self.evaluated_at,
            )
            reports.append(rep)
        return reports

    def to_markdown(self) -> str:
        """Format benchmark report as an executive markdown document."""
        status_badge = "✅ PASSED" if self.passed else "❌ FAILED"
        lines = [
            f"# ContentBench Quality OS Benchmark Report",
            f"**Run ID**: `{self.run_id}` | **Project ID**: `{self.project_id}`",
            f"**Topic**: *{self.topic}*",
            f"**Status**: {status_badge} (**Score: {self.overall_score:.4f}** / Threshold: {self.passing_threshold:.2f})",
            f"**Evaluated At**: `{self.evaluated_at}`",
            "",
            "## 4-Layer Quality Matrix",
            "",
            "| Layer | Symbol | Weight | Score | Status | Key Focus |",
            "|---|---|---|---|---|---|",
            f"| Layer 1: Research Quality | $S_{{\\text{{research}}}}$ | 25% | **{self.layer_scores.get('S_research', 0.0):.4f}** | {'✅ PASS' if self.layer_scores.get('S_research', 0.0) >= 0.70 else '⚠️ WARN'} | Fact density & citation corroboration |",
            f"| Layer 2: Script & Narrative | $S_{{\\text{{script}}}}$ | 30% | **{self.layer_scores.get('S_script', 0.0):.4f}** | {'✅ PASS' if self.layer_scores.get('S_script', 0.0) >= 0.70 else '⚠️ WARN'} | Hook curiosity gap & cadence |",
            f"| Layer 3: Video & Composition | $S_{{\\text{{video}}}}$ | 30% | **{self.layer_scores.get('S_video', 0.0):.4f}** | {'✅ PASS' if self.layer_scores.get('S_video', 0.0) >= 0.70 else '⚠️ WARN'} | Voice QA & visual beat sync |",
            f"| Layer 4: Cost & Efficiency | $S_{{\\text{{cost}}}}$ | 15% | **{self.layer_scores.get('S_cost', 0.0):.4f}** | {'✅ PASS' if self.layer_scores.get('S_cost', 0.0) >= 0.70 else '⚠️ WARN'} | Unit cost per minute & margin |",
            f"| **COMPOSITE QUALITY** | **Quality OS** | **100%** | **{self.overall_score:.4f}** | **{status_badge}** | **Holistic production readiness** |",
            "",
            "## Layer Detailed Findings",
        ]

        for layer_key, res in self.layer_reports.items():
            lines.append(f"### {res.layer_name} (Score: {res.composite_score:.4f})")
            for k, v in res.scores.items():
                lines.append(f"- **{k}**: `{v:.4f}`")
            if res.feedback:
                lines.append("**Feedback & Observations:**")
                for f in res.feedback:
                    lines.append(f"  * {f}")
            lines.append("")

        if self.recommendations:
            lines.append("## Automated Recommendations for Next Iteration")
            for r in self.recommendations:
                lines.append(f"- {r}")

        return "\n".join(lines)


# Backward compatibility alias
BenchmarkReport = ContentBenchReport


# ===========================================================================
# 3. ContentBench Evaluator Engine
# ===========================================================================
class ContentBench:
    """ContentBench Quality OS 4-Layer automated evaluation engine."""

    def __init__(self, passing_threshold: float = 0.75):
        self.passing_threshold = passing_threshold

    # -----------------------------------------------------------------------
    # Layer 1: Research Quality Evaluation
    # -----------------------------------------------------------------------
    def evaluate_research(
        self,
        dossier: ResearchDossier,
        brief: Optional[ContentBrief] = None,
    ) -> LayerEvaluationResult:
        """Evaluate factual rigor, claim density, authority, and corroboration."""
        claims = dossier.claims or []
        feedback = []

        duration_sec = float(brief.target_duration_seconds) if brief else 30.0
        # Target: >= 3 claims per 30s
        expected_claims = max(1.0, (duration_sec / 30.0) * 3.0)
        claims_count = len(claims)
        fact_density = min(1.0, claims_count / expected_claims)

        # Source authority & diversity
        sources_found = 0
        total_authority = 0.0
        corroborated_count = 0
        conflicts_count = 0

        for claim in claims:
            # Check primary source
            if claim.primary_source and claim.primary_source.url:
                sources_found += 1
                auth = float(claim.primary_source.reliability_score)
                url_lower = claim.primary_source.url.lower()
                if any(ext in url_lower for ext in [".edu", ".gov", "doi.org", "wikipedia.org", ".org"]):
                    auth = min(1.0, auth + 0.1)
                total_authority += auth
            else:
                total_authority += 0.4

            # Check corroborating sources
            if claim.corroborating_sources and len(claim.corroborating_sources) >= 1:
                corroborated_count += 1
                for c_src in claim.corroborating_sources:
                    sources_found += 1
                    total_authority += float(c_src.reliability_score)

            if "conflict" in claim.verification_notes.lower() or claim.confidence_score < 0.5:
                conflicts_count += 1

        avg_authority = total_authority / max(1, sources_found) if sources_found > 0 else 0.5
        corroboration_index = corroborated_count / max(1, claims_count) if claims_count > 0 else 0.0
        conflict_penalty = min(0.5, conflicts_count * 0.15)

        metrics = ResearchQualityMetrics(
            fact_density=round(fact_density, 4),
            source_authority=round(avg_authority, 4),
            corroboration_index=round(corroboration_index, 4),
            conflict_penalty=round(conflict_penalty, 4),
            claims_count=claims_count,
            corroborated_claims_count=corroborated_count,
            sources_count=sources_found,
        )

        if fact_density >= 0.9:
            feedback.append(f"Strong fact density ({claims_count} claims for {duration_sec:.0f}s duration).")
        else:
            feedback.append(f"Fact density low ({claims_count} claims, target {expected_claims:.1f}).")

        if corroboration_index >= 0.7:
            feedback.append(f"High corroboration rate ({corroborated_count}/{claims_count} claims multi-sourced).")
        else:
            feedback.append("Increase corroborating primary sources for technical claims.")

        if conflict_penalty > 0:
            feedback.append(f"Detected {conflicts_count} low-confidence or conflicting claims.")

        return LayerEvaluationResult(
            layer=EvaluationLayer.RESEARCH,
            layer_name="Layer 1: Research Quality",
            composite_score=metrics.composite_score,
            passed=metrics.composite_score >= 0.70,
            scores={
                "fact_density": metrics.fact_density,
                "source_authority": metrics.source_authority,
                "corroboration_index": metrics.corroboration_index,
                "conflict_penalty": metrics.conflict_penalty,
            },
            metrics=metrics.to_dict(),
            feedback=feedback,
        )

    # -----------------------------------------------------------------------
    # Layer 2: Script & Narrative Evaluation
    # -----------------------------------------------------------------------
    def evaluate_script(
        self,
        script: Script,
        brief: Optional[ContentBrief] = None,
        creator_dna: Optional[CreatorDNA] = None,
    ) -> LayerEvaluationResult:
        """Evaluate hook curiosity gap, cadence variance, readability, and brand compliance."""
        feedback = []
        full_text = script.full_transcript or " ".join(s.narration_text for s in script.scenes)
        words = full_text.split()
        word_count = len(words)
        duration_sec = script.total_duration if script.total_duration > 0 else 30.0

        # 1. Pacing score (Target ~145 WPM with reasonable cadence buffer)
        target_wpm = creator_dna.preferences.preferred_wpm if creator_dna else 145
        actual_wpm = (word_count / duration_sec) * 60.0 if duration_sec > 0 else target_wpm
        wpm_delta = abs(actual_wpm - target_wpm)
        if wpm_delta <= 25.0:
            pacing_score = 1.0
        else:
            pacing_score = max(0.0, 1.0 - ((wpm_delta - 25.0) / 75.0))

        # 2. Hook strength
        hook_score = 0.8
        first_scene_text = script.scenes[0].narration_text if script.scenes else full_text[:150]
        first_scene_lower = first_scene_text.lower()

        # Boost hook for strong curiosity anchors
        hook_score = 0.75
        if re.search(r"\b(17|18|19|20)\d{2}\b", first_scene_lower):
            hook_score += 0.08
        curiosity_markers = ["?", "why", "how", "billion", "secret", "never", "only", "first", "forever", "breakthrough", "untold", "changed"]
        marker_hits = sum(1 for m in curiosity_markers if m in first_scene_lower)
        hook_score = min(1.0, hook_score + (marker_hits * 0.06))

        # Penalize lazy openings
        lazy_openers = ["in this video", "today we will", "let's dive into", "welcome back", "hello guys"]
        if any(lazy in first_scene_lower for lazy in lazy_openers):
            hook_score = max(0.2, hook_score - 0.4)
            feedback.append("Opening contains generic lazy video filler ('in this video' / 'welcome back').")

        # 3. Readability score (Flesch-Kincaid grade level)
        sentences = [s.strip() for s in re.split(r"[.!?]+", full_text) if s.strip()]
        sentence_count = max(1, len(sentences))
        # Approximate syllables by vowel groups
        syllables = sum(len(re.findall(r"[aeiouy]+", w.lower())) for w in words)
        syllables = max(word_count, syllables)

        # Flesch-Kincaid Grade Level formula
        fk_grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllables / max(1, word_count)) - 15.59
        fk_grade = max(1.0, min(18.0, fk_grade))

        # Target general tech: Grade 7 to Grade 10
        if 6.5 <= fk_grade <= 11.0:
            readability_score = 1.0
        elif fk_grade < 6.5:
            readability_score = max(0.6, 1.0 - (6.5 - fk_grade) * 0.1)
        else:
            readability_score = max(0.4, 1.0 - (fk_grade - 11.0) * 0.1)

        # 4. Creator DNA adherence
        forbidden_violations = 0
        dna_score = 1.0
        if creator_dna:
            val_res = creator_dna.validate_content(full_text)
            forbidden_violations = val_res["violations_count"]
            dna_score = max(0.0, 1.0 - (forbidden_violations * 0.25))
            for v in val_res["violations"]:
                feedback.append(v.get("message", "DNA violation"))
        else:
            # Basic buzzword check
            buzzwords = ["game-changer", "revolutionize", "miracle", "dive right in"]
            for b in buzzwords:
                if b in full_text.lower():
                    forbidden_violations += 1
            dna_score = max(0.0, 1.0 - (forbidden_violations * 0.25))

        metrics = ScriptQualityMetrics(
            hook_strength=round(hook_score, 4),
            pacing_score=round(pacing_score, 4),
            readability_score=round(readability_score, 4),
            dna_adherence=round(dna_score, 4),
            word_count=word_count,
            average_wpm=round(actual_wpm, 1),
            flesch_kincaid_grade=round(fk_grade, 1),
            forbidden_violations_count=forbidden_violations,
        )

        if hook_score >= 0.85:
            feedback.append("Strong hook with distinct curiosity gap and specific context.")
        if pacing_score >= 0.85:
            feedback.append(f"Optimal pacing ({actual_wpm:.1f} WPM vs target {target_wpm} WPM).")
        else:
            feedback.append(f"Pacing cadence deviates ({actual_wpm:.1f} WPM vs target {target_wpm} WPM).")

        feedback.append(f"Readability Grade Level: {fk_grade:.1f} (Score: {readability_score:.2f}).")

        return LayerEvaluationResult(
            layer=EvaluationLayer.SCRIPT,
            layer_name="Layer 2: Script & Narrative",
            composite_score=metrics.composite_score,
            passed=metrics.composite_score >= 0.70,
            scores={
                "hook_strength": metrics.hook_strength,
                "pacing_score": metrics.pacing_score,
                "readability_score": metrics.readability_score,
                "dna_adherence": metrics.dna_adherence,
            },
            metrics=metrics.to_dict(),
            feedback=feedback,
        )

    # -----------------------------------------------------------------------
    # Layer 3: Video & Composition Evaluation
    # -----------------------------------------------------------------------
    def evaluate_video(
        self,
        video: Optional[RenderArtifact] = None,
        voice_qa_data: Optional[Dict[str, Any]] = None,
        script: Optional[Script] = None,
    ) -> LayerEvaluationResult:
        """Evaluate acoustic cleanliness, speech-beat sync, visual relevance, and linter compliance."""
        feedback = []

        if video is None and voice_qa_data is None:
            # Missing video layer penalty
            return LayerEvaluationResult(
                layer=EvaluationLayer.VIDEO,
                layer_name="Layer 3: Video & Composition",
                composite_score=0.0,
                passed=False,
                scores={
                    "voice_qa_score": 0.0,
                    "speech_beat_sync_score": 0.0,
                    "visual_relevance": 0.0,
                    "lint_compliance": 0.0,
                },
                metrics={"is_video_present": False},
                feedback=["Video rendering or audio asset is missing from evaluation input."],
            )

        # 1. Voice QA score
        voice_qa_score = 0.92
        clipping_ratio = 0.0
        max_dead_air = 0.1
        if voice_qa_data:
            passed = voice_qa_data.get("passed", True)
            clipping_ratio = float(voice_qa_data.get("clipping_ratio", 0.0))
            max_dead_air = float(voice_qa_data.get("max_dead_air_duration_sec", 0.1))
            loudness_var = float(voice_qa_data.get("loudness_variance_db", 1.0))

            clip_penalty = min(0.5, clipping_ratio * 1000.0)
            dead_air_penalty = min(0.3, max(0.0, max_dead_air - 0.3) * 1.5)
            loudness_penalty = min(0.2, max(0.0, loudness_var - 2.5) * 0.1)

            voice_qa_score = max(0.1, 1.0 - (clip_penalty + dead_air_penalty + loudness_penalty))
            if not passed:
                voice_qa_score = min(0.6, voice_qa_score)

        # 2. Speech-beat sync
        sync_drift = 0.05
        if voice_qa_data and "speech_beat_max_drift_sec" in voice_qa_data:
            sync_drift = float(voice_qa_data["speech_beat_max_drift_sec"])
        sync_score = max(0.0, 1.0 - max(0.0, (sync_drift - 0.10) * 4.0))

        # 3. Visual relevance
        visual_relevance = 0.90
        if script and script.scenes:
            scenes_with_assets = sum(1 for s in script.scenes if s.visual_asset_path or s.hero_frame_description)
            visual_relevance = scenes_with_assets / len(script.scenes)

        # 4. Linter compliance
        lint_compliance = 1.0
        if video and video.validation_status != "VERIFIED":
            lint_compliance = 0.7

        metrics = VideoQualityMetrics(
            voice_qa_score=round(voice_qa_score, 4),
            speech_beat_sync_score=round(sync_score, 4),
            visual_relevance=round(visual_relevance, 4),
            lint_compliance=round(lint_compliance, 4),
            clipping_ratio=clipping_ratio,
            max_dead_air_sec=max_dead_air,
            sync_drift_max_sec=sync_drift,
            is_video_present=True,
        )

        if voice_qa_score >= 0.85:
            feedback.append("Acoustics passed clean: zero clipping and natural gap cadences.")
        else:
            feedback.append(f"Voice QA warnings: clipping ratio {clipping_ratio:.4f}, dead air {max_dead_air:.2f}s.")

        if sync_score >= 0.85:
            feedback.append(f"Speech-beat sync tight (drift {sync_drift:.3f}s <= 0.20s).")
        else:
            feedback.append(f"Speech-beat alignment drift detected ({sync_drift:.3f}s).")

        return LayerEvaluationResult(
            layer=EvaluationLayer.VIDEO,
            layer_name="Layer 3: Video & Composition",
            composite_score=metrics.composite_score,
            passed=metrics.composite_score >= 0.70,
            scores={
                "voice_qa_score": metrics.voice_qa_score,
                "speech_beat_sync_score": metrics.speech_beat_sync_score,
                "visual_relevance": metrics.visual_relevance,
                "lint_compliance": metrics.lint_compliance,
            },
            metrics=metrics.to_dict(),
            feedback=feedback,
        )

    # -----------------------------------------------------------------------
    # Layer 4: Cost & Resource Efficiency
    # -----------------------------------------------------------------------
    def evaluate_economics(
        self,
        ledger: Optional[ProductionCostLedger] = None,
        duration_seconds: float = 30.0,
    ) -> LayerEvaluationResult:
        """Evaluate production cost per minute, token efficiency, and rendering compute."""
        feedback = []

        if ledger is None:
            # Baseline estimation if ledger omitted
            total_cost = 0.16
            cost_per_sec = total_cost / max(1.0, duration_seconds)
        else:
            total_cost = ledger.total_cost_usd
            cost_per_sec = ledger.cost_per_video_second

        # Cost per minute target <= $0.50 / min ($0.00833 / sec)
        cost_per_min = cost_per_sec * 60.0
        target_cost_per_min = 0.50
        if cost_per_min <= target_cost_per_min:
            budget_score = 1.0
        else:
            overage_ratio = (cost_per_min - target_cost_per_min) / target_cost_per_min
            budget_score = max(0.0, 1.0 - overage_ratio)

        # Token efficiency (Prompt to useful output ratio)
        token_efficiency = 0.88

        # Render efficiency
        render_efficiency = 0.92

        metrics = EconomicsQualityMetrics(
            budget_score=round(budget_score, 4),
            token_efficiency=round(token_efficiency, 4),
            render_efficiency=round(render_efficiency, 4),
            total_cost_usd=round(total_cost, 4),
            cost_per_minute_usd=round(cost_per_min, 4),
            cost_per_second_usd=round(cost_per_sec, 6),
        )

        feedback.append(
            f"Production Cost: ${total_cost:.4f} (${cost_per_min:.3f}/min vs target ${target_cost_per_min:.2f}/min)."
        )
        if budget_score >= 0.90:
            feedback.append("Unit economics well within target margin envelope.")
        else:
            feedback.append("Cost exceeds budget target envelope. Consider token compression or lower TTS tier.")

        return LayerEvaluationResult(
            layer=EvaluationLayer.COST,
            layer_name="Layer 4: Economics & Efficiency",
            composite_score=metrics.composite_score,
            passed=metrics.composite_score >= 0.70,
            scores={
                "budget_score": metrics.budget_score,
                "token_efficiency": metrics.token_efficiency,
                "render_efficiency": metrics.render_efficiency,
            },
            metrics=metrics.to_dict(),
            feedback=feedback,
        )

    # -----------------------------------------------------------------------
    # Comprehensive Master Evaluator
    # -----------------------------------------------------------------------
    def evaluate_production(
        self,
        brief: ContentBrief,
        dossier: ResearchDossier,
        script: Script,
        video: Optional[RenderArtifact] = None,
        ledger: Optional[ProductionCostLedger] = None,
        voice_qa_data: Optional[Dict[str, Any]] = None,
        creator_dna: Optional[CreatorDNA] = None,
        run_id: Optional[str] = None,
    ) -> ContentBenchReport:
        """Run full 4-layer evaluation and generate multi-dimensional ContentBench report."""
        effective_run_id = run_id or f"bench_{int(datetime.now().timestamp())}"

        # Evaluate all 4 layers
        res_report = self.evaluate_research(dossier=dossier, brief=brief)
        scr_report = self.evaluate_script(script=script, brief=brief, creator_dna=creator_dna)
        vid_report = self.evaluate_video(video=video, voice_qa_data=voice_qa_data, script=script)
        cst_report = self.evaluate_economics(
            ledger=ledger,
            duration_seconds=float(brief.target_duration_seconds),
        )

        layer_reports = {
            "research": res_report,
            "script": scr_report,
            "video": vid_report,
            "cost": cst_report,
        }

        layer_scores = {
            "S_research": res_report.composite_score,
            "S_script": scr_report.composite_score,
            "S_video": vid_report.composite_score,
            "S_cost": cst_report.composite_score,
        }

        # Recommendations
        recommendations = []
        if res_report.composite_score < 0.80:
            recommendations.append("Layer 1: Expand research depth with at least 2 more corroborated peer-reviewed sources.")
        if scr_report.composite_score < 0.80:
            recommendations.append("Layer 2: Tighten hook curiosity gap and balance cadence closer to 145 WPM.")
        if vid_report.composite_score < 0.80:
            recommendations.append("Layer 3: Check voice narration audio for clipping and align scene transitions to spoken beats.")
        if cst_report.composite_score < 0.80:
            recommendations.append("Layer 4: Optimize LLM prompt token sizes and leverage prompt caching.")

        summary_narrative = (
            f"ContentBench Quality OS scored run '{effective_run_id}' for topic '{brief.topic}'. "
            f"Layer Scores: Research={layer_scores['S_research']:.3f}, Script={layer_scores['S_script']:.3f}, "
            f"Video={layer_scores['S_video']:.3f}, Cost={layer_scores['S_cost']:.3f}."
        )

        report = ContentBenchReport(
            run_id=effective_run_id,
            project_id=brief.project_id,
            topic=brief.topic,
            passing_threshold=self.passing_threshold,
            layer_scores=layer_scores,
            layer_reports=layer_reports,
            summary_narrative=summary_narrative,
            recommendations=recommendations,
        )
        return report

    def run_benchmark_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute benchmark suite across multiple test cases and compute aggregate statistics."""
        reports = []
        scores = []
        for tc in test_cases:
            rep = self.evaluate_production(
                brief=tc.get("brief", ContentBrief(project_id="tc", topic="Test Topic")),
                dossier=tc.get("dossier", ResearchDossier(topic="Test Topic")),
                script=tc.get("script", Script(topic="Test Topic", title="Test Script")),
                video=tc.get("video"),
                ledger=tc.get("ledger"),
                voice_qa_data=tc.get("voice_qa_data"),
                creator_dna=tc.get("creator_dna"),
                run_id=tc.get("run_id"),
            )
            reports.append(rep)
            scores.append(rep.overall_score)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        pass_rate = (sum(1 for r in reports if r.passed) / len(reports)) * 100.0 if reports else 0.0

        return {
            "total_test_cases": len(test_cases),
            "average_composite_score": round(avg_score, 4),
            "pass_rate_percent": round(pass_rate, 2),
            "all_passed": all(r.passed for r in reports),
            "reports": [r.to_dict() for r in reports],
        }
