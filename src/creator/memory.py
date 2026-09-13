"""Harness 9 Creator Memory Engine (Milestone M5).

Implements:
- Performance retention curves and analytics modeling.
- Learned patterns and correlation extraction.
- Negative memory failure log and negative constraint extraction.
- Dynamic negative prompt directives generation.
- Learning candidate distillation for system evolution.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import Field, field_validator, model_validator

from src.models.contracts import H9BaseModel, LearningCandidate


# ===========================================================================
# 1. Performance Retention Models
# ===========================================================================
class RetentionCurvePoint(H9BaseModel):
    """Timestamped retention observation point."""
    timestamp_sec: float = Field(..., ge=0.0, description="Time in seconds from video start")
    retention_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of viewers still watching")


class RetentionCurve(H9BaseModel):
    """Audience retention curve for a published video."""
    project_id: str = Field(..., min_length=1)
    duration_seconds: float = Field(..., gt=0.0)
    points: List[RetentionCurvePoint] = Field(default_factory=list)
    average_view_duration_sec: float = Field(default=0.0, ge=0.0)
    completion_rate_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    initial_5s_retention_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    recorded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @model_validator(mode="after")
    def calculate_derived_metrics(self) -> "RetentionCurve":
        """Compute average view duration and completion metrics from curve points."""
        if not self.points:
            return self

        # Sort points by timestamp
        sorted_points = sorted(self.points, key=lambda p: p.timestamp_sec)
        object.__setattr__(self, "points", sorted_points)

        # Calculate initial 5s retention
        for p in sorted_points:
            if p.timestamp_sec <= 5.0:
                object.__setattr__(self, "initial_5s_retention_pct", round(p.retention_pct, 2))
            else:
                break

        # Calculate completion rate (last point or retention at duration)
        if sorted_points:
            object.__setattr__(
                self, "completion_rate_pct", round(sorted_points[-1].retention_pct, 2)
            )

        # Approximate average view duration using trapezoidal integration
        if len(sorted_points) >= 2:
            total_area = 0.0
            for i in range(len(sorted_points) - 1):
                t0, r0 = sorted_points[i].timestamp_sec, sorted_points[i].retention_pct / 100.0
                t1, r1 = sorted_points[i + 1].timestamp_sec, sorted_points[i + 1].retention_pct / 100.0
                dt = max(0.0, t1 - t0)
                total_area += 0.5 * (r0 + r1) * dt
            object.__setattr__(self, "average_view_duration_sec", round(total_area, 2))
        elif len(sorted_points) == 1:
            object.__setattr__(
                self,
                "average_view_duration_sec",
                round((sorted_points[0].retention_pct / 100.0) * self.duration_seconds, 2),
            )

        return self

    def retention_at(self, timestamp_sec: float) -> float:
        """Get linearly interpolated retention percentage at a specific timestamp."""
        if not self.points:
            return 0.0
        if timestamp_sec <= self.points[0].timestamp_sec:
            return self.points[0].retention_pct
        if timestamp_sec >= self.points[-1].timestamp_sec:
            return self.points[-1].retention_pct

        for i in range(len(self.points) - 1):
            p0, p1 = self.points[i], self.points[i + 1]
            if p0.timestamp_sec <= timestamp_sec <= p1.timestamp_sec:
                dt = p1.timestamp_sec - p0.timestamp_sec
                if dt == 0:
                    return p0.retention_pct
                ratio = (timestamp_sec - p0.timestamp_sec) / dt
                return round(p0.retention_pct + ratio * (p1.retention_pct - p0.retention_pct), 2)
        return self.points[-1].retention_pct

    def find_drop_off_points(self, threshold_pct_drop: float = 10.0) -> List[Dict[str, Any]]:
        """Identify intervals where audience drop-off exceeds threshold."""
        drops = []
        if len(self.points) < 2:
            return drops

        for i in range(len(self.points) - 1):
            p0, p1 = self.points[i], self.points[i + 1]
            drop = p0.retention_pct - p1.retention_pct
            if drop >= threshold_pct_drop:
                severity = "critical" if drop >= 25.0 else ("high" if drop >= 15.0 else "medium")
                drops.append({
                    "start_time_sec": p0.timestamp_sec,
                    "end_time_sec": p1.timestamp_sec,
                    "drop_pct": round(drop, 2),
                    "severity": severity,
                })
        return drops


class LearnedPattern(H9BaseModel):
    """Empirical pattern discovered through production feedback."""
    pattern_id: str = Field(..., min_length=1)
    category: str = Field(default="hook_structure")  # hook_structure, pacing, visual_density, transition
    description: str = Field(..., min_length=1)
    positive_correlation: str = Field(..., min_length=1)
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    sample_count: int = Field(default=1, ge=1)
    discovered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PerformanceMemory(H9BaseModel):
    """Historical performance telemetry and learned creative patterns."""
    retention_curves: List[RetentionCurve] = Field(default_factory=list)
    learned_patterns: List[LearnedPattern] = Field(default_factory=list)
    average_view_duration_overall: float = 0.0
    average_retention_overall: float = 0.0
    top_hook_styles: List[str] = Field(default_factory=list)

    def add_retention_curve(self, curve: RetentionCurve) -> None:
        """Add new retention curve and recalculate aggregate benchmarks."""
        self.retention_curves.append(curve)
        if self.retention_curves:
            total_avd = sum(c.average_view_duration_sec for c in self.retention_curves)
            total_ret = sum(c.completion_rate_pct for c in self.retention_curves)
            self.average_view_duration_overall = round(total_avd / len(self.retention_curves), 2)
            self.average_retention_overall = round(total_ret / len(self.retention_curves), 2)

    def add_pattern(self, pattern: LearnedPattern) -> None:
        """Register or update a learned pattern."""
        for idx, existing in enumerate(self.learned_patterns):
            if existing.pattern_id == pattern.pattern_id:
                self.learned_patterns[idx] = pattern
                return
        self.learned_patterns.append(pattern)

    def get_top_learnings(self, min_confidence: float = 0.7) -> List[str]:
        """Extract high-confidence learning takeaways."""
        return [
            f"[{p.category.upper()}] {p.description} -> {p.positive_correlation} (confidence: {p.confidence_score:.2f})"
            for p in self.learned_patterns
            if p.confidence_score >= min_confidence
        ]


# ===========================================================================
# 2. Negative Memory Models
# ===========================================================================
class NegativeMistakeRecord(H9BaseModel):
    """Record of a creative failure, rejected angle, or review issue."""
    mistake_id: str = Field(..., min_length=1)
    project_id: str = Field(default="global")
    category: str = Field(default="editorial")  # editorial, script, visual, factual, voice, pacing
    pattern_or_phrase: str = Field(..., min_length=1)
    failure_reason: str = Field(..., min_length=1)
    severity: str = Field(default="medium")  # critical, high, medium, low
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class NegativeConstraint(H9BaseModel):
    """Active constraint blocking recurring errors."""
    constraint_id: str = Field(..., min_length=1)
    category: str = Field(default="general")
    prohibited_pattern: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    severity: str = Field(default="high")
    is_active: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class NegativeMemory(H9BaseModel):
    """Negative memory system storing failure logs and negative constraints."""
    mistake_log: List[NegativeMistakeRecord] = Field(default_factory=list)
    active_constraints: List[NegativeConstraint] = Field(default_factory=list)
    forbidden_words: List[str] = Field(
        default_factory=lambda: [
            "game-changer",
            "revolutionize",
            "miracle",
            "in this video we will explore",
            "buckle up",
            "dive right in",
        ]
    )
    forbidden_themes: List[str] = Field(
        default_factory=lambda: [
            "Unverified hype claims",
            "Clickbait hyperbole",
            "Uncited medical advice",
        ]
    )

    def record_mistake(self, mistake: NegativeMistakeRecord) -> None:
        """Log a mistake and automatically generate an active negative constraint."""
        self.mistake_log.append(mistake)
        # Create corresponding constraint
        constraint = NegativeConstraint(
            constraint_id=f"nc_{mistake.mistake_id}",
            category=mistake.category,
            prohibited_pattern=mistake.pattern_or_phrase,
            rationale=mistake.failure_reason,
            severity=mistake.severity,
            is_active=True,
        )
        self.add_constraint(constraint)

    def add_constraint(self, constraint: NegativeConstraint) -> None:
        """Add or update an active negative constraint."""
        for idx, existing in enumerate(self.active_constraints):
            if existing.constraint_id == constraint.constraint_id:
                self.active_constraints[idx] = constraint
                return
        self.active_constraints.append(constraint)

    def add_forbidden_word(self, word: str) -> None:
        """Register a prohibited word or phrase."""
        cleaned = word.strip()
        if cleaned and cleaned.lower() not in [w.lower() for w in self.forbidden_words]:
            self.forbidden_words.append(cleaned)

    def add_forbidden_theme(self, theme: str) -> None:
        """Register a prohibited theme."""
        cleaned = theme.strip()
        if cleaned and cleaned not in self.forbidden_themes:
            self.forbidden_themes.append(cleaned)

    def generate_negative_prompt_directives(self) -> List[str]:
        """Generate negative prompt constraints formatted for LLM system conditioning."""
        directives = []

        # 1. Prohibited words and phrases
        if self.forbidden_words:
            words_str = ", ".join(f'"{w}"' for w in self.forbidden_words)
            directives.append(f"Do NOT use any of the following prohibited buzzwords or filler phrases: {words_str}.")

        # 2. Prohibited themes
        if self.forbidden_themes:
            themes_str = "; ".join(self.forbidden_themes)
            directives.append(f"Strictly avoid the following forbidden themes: {themes_str}.")

        # 3. Active mistake-derived constraints
        for constraint in self.active_constraints:
            if constraint.is_active:
                directives.append(
                    f"Do NOT use [{constraint.prohibited_pattern}], which failed previously due to: {constraint.rationale}"
                )

        return directives

    def check_violations(self, text: str) -> List[Dict[str, Any]]:
        """Check text against forbidden words, phrases, and active negative constraints."""
        violations = []
        text_lower = text.lower()

        # Check forbidden words
        for word in self.forbidden_words:
            pattern = rf"\b{re.escape(word.lower())}\b"
            if re.search(pattern, text_lower):
                violations.append({
                    "type": "forbidden_word",
                    "pattern": word,
                    "severity": "high",
                    "message": f"Detected forbidden buzzword/phrase: '{word}'",
                })

        # Check active negative constraints
        for constraint in self.active_constraints:
            if not constraint.is_active:
                continue
            pat = constraint.prohibited_pattern.lower()
            if pat in text_lower:
                violations.append({
                    "type": "negative_constraint",
                    "pattern": constraint.prohibited_pattern,
                    "severity": constraint.severity,
                    "message": f"Violates negative constraint: '{constraint.prohibited_pattern}' ({constraint.rationale})",
                })

        return violations

    def extract_learning_candidates(self, creator_id: str) -> List[LearningCandidate]:
        """Distill severe mistakes into formal LearningCandidate production contracts."""
        candidates = []
        for mistake in self.mistake_log:
            if mistake.severity in ("critical", "high"):
                cand = LearningCandidate(
                    lesson_id=f"lesson_{mistake.mistake_id}",
                    creator_id=creator_id,
                    rule_type="negative_constraint",
                    observation=f"Past failure in {mistake.category}: {mistake.pattern_or_phrase}",
                    recommended_action=f"Avoid {mistake.pattern_or_phrase}. Rationale: {mistake.failure_reason}",
                    confidence=0.9 if mistake.severity == "critical" else 0.82,
                )
                candidates.append(cand)
        return candidates
