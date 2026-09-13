"""9-Dimension Editorial Scorecard Engine (Milestone M2).

Evaluates candidate editorial angles across 9 normalized dimensions:
1. audience_relevance (w=0.15): Alignment with broad human curiosity, everyday utility, or wonder.
2. novelty (w=0.15): Surprise factor; how counterintuitive or fresh the perspective is.
3. hook_potential (w=0.15): Capacity to stop scroll retention within the first 3.0 seconds.
4. narrative_potential (w=0.10): Structural presence of conflict, escalation, stakes, and resolution.
5. creator_fit (w=0.10): Alignment with creator brand DNA, voice, and negative constraints.
6. evidence_availability (w=0.10): Density and confidence of verifiable facts and citations.
7. visual_potential (w=0.10): Visual dynamic range for schematics, comparisons, and motion graphics.
8. platform_fit (w=0.10): Pacing and aspect ratio suitability (9:16 vertical vs 16:9 horizontal).
9. saturation_risk (w=0.05): Penalty metric for overused tropes (inverted in composite).
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from src.models.contracts import (
    AngleScorecard,
    ContentBrief,
    CreatorProfile,
    EditorialAngle,
    EditorialScorecard,
    ResearchDossier,
)


SCORECARD_WEIGHTS: Dict[str, float] = {
    "audience_relevance": 0.15,
    "novelty": 0.15,
    "hook_potential": 0.15,
    "narrative_potential": 0.10,
    "creator_fit": 0.10,
    "evidence_availability": 0.10,
    "visual_potential": 0.10,
    "platform_fit": 0.10,
    "saturation_risk": 0.05,
}


def calculate_scorecard_composite(
    audience_relevance: float,
    novelty: float,
    hook_potential: float,
    narrative_potential: float,
    creator_fit: float,
    evidence_availability: float,
    visual_potential: float,
    platform_fit: float,
    saturation_risk: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Compute weighted composite editorial score with normalized bounds [0.0, 1.0].
    
    Composite = Sum(w_i * d_i) + w_sat * (1.0 - saturation_risk)
    """
    w = weights or SCORECARD_WEIGHTS
    raw = (
        audience_relevance * w.get("audience_relevance", 0.15)
        + novelty * w.get("novelty", 0.15)
        + hook_potential * w.get("hook_potential", 0.15)
        + narrative_potential * w.get("narrative_potential", 0.10)
        + creator_fit * w.get("creator_fit", 0.10)
        + evidence_availability * w.get("evidence_availability", 0.10)
        + visual_potential * w.get("visual_potential", 0.10)
        + platform_fit * w.get("platform_fit", 0.10)
        + (1.0 - saturation_risk) * w.get("saturation_risk", 0.05)
    )
    return round(max(0.0, min(1.0, raw)), 4)


class EditorialScorer:
    """Evaluates candidate editorial angles using heuristic signals and domain evidence."""

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        self.weights = custom_weights or SCORECARD_WEIGHTS

    def score_angle(
        self,
        angle: EditorialAngle,
        dossier: Optional[ResearchDossier] = None,
        brief: Optional[ContentBrief] = None,
        creator: Optional[CreatorProfile] = None,
    ) -> EditorialScorecard:
        """Calculate full 9-dimension scorecard for an editorial angle candidate."""
        # 1. Evaluate Audience Relevance
        aud_score = self._eval_audience_relevance(angle, brief, creator)

        # 2. Evaluate Novelty
        nov_score = self._eval_novelty(angle, dossier)

        # 3. Evaluate Hook Potential
        hook_score = self._eval_hook_potential(angle)

        # 4. Evaluate Narrative Potential
        narr_score = self._eval_narrative_potential(angle)

        # 5. Evaluate Creator Fit
        creator_score = self._eval_creator_fit(angle, creator)

        # 6. Evaluate Evidence Availability
        evid_score = self._eval_evidence_availability(angle, dossier)

        # 7. Evaluate Visual Potential
        vis_score = self._eval_visual_potential(angle, dossier)

        # 8. Evaluate Platform Fit
        plat_score = self._eval_platform_fit(angle, brief)

        # 9. Evaluate Saturation Risk
        sat_score = self._eval_saturation_risk(angle)

        composite = calculate_scorecard_composite(
            audience_relevance=aud_score,
            novelty=nov_score,
            hook_potential=hook_score,
            narrative_potential=narr_score,
            creator_fit=creator_score,
            evidence_availability=evid_score,
            visual_potential=vis_score,
            platform_fit=plat_score,
            saturation_risk=sat_score,
            weights=self.weights,
        )

        return EditorialScorecard(
            audience_relevance=aud_score,
            novelty=nov_score,
            hook_potential=hook_score,
            narrative_potential=narr_score,
            creator_fit=creator_score,
            evidence_availability=evid_score,
            visual_potential=vis_score,
            platform_fit=plat_score,
            saturation_risk=sat_score,
            composite_score=composite,
        )

    # -----------------------------------------------------------------------
    # Dimension Evaluators
    # -----------------------------------------------------------------------
    def _eval_audience_relevance(
        self,
        angle: EditorialAngle,
        brief: Optional[ContentBrief],
        creator: Optional[CreatorProfile],
    ) -> float:
        """Score alignment with broad audience curiosity and daily relevance."""
        text = f"{angle.title} {angle.premise} {angle.core_thesis}".lower()
        score = 0.75

        # Universal curiosity triggers
        universal_triggers = [
            "why", "how", "secret", "hidden", "mistake", "everyone", "future",
            "money", "power", "war", "computer", "human", "history", "real reason",
            "what happens", "danger", "everyday", "life", "civilization"
        ]
        matches = sum(1 for word in universal_triggers if word in text)
        score += min(0.15, matches * 0.03)

        # Brief target audience alignment
        if brief and brief.audience:
            brief_aud_words = set(brief.audience.lower().split())
            if any(w in text for w in brief_aud_words if len(w) > 3):
                score += 0.05

        return round(max(0.1, min(1.0, score)), 4)

    def _eval_novelty(
        self,
        angle: EditorialAngle,
        dossier: Optional[ResearchDossier],
    ) -> float:
        """Score perspective freshness and counterintuitive surprise factor."""
        text = f"{angle.title} {angle.premise} {angle.core_thesis}".lower()
        style = (angle.narrative_style or "").lower()

        # Archetype base bonus
        if "contrarian" in style or "paradox" in text or "counterintuitive" in style:
            base = 0.88
        elif "future" in style or "domino" in text:
            base = 0.85
        elif "deep dive" in style or "mechanism" in text:
            base = 0.80
        elif "human" in style or "unsung" in text:
            base = 0.78
        elif "data" in style:
            base = 0.76
        else:
            base = 0.75

        # Surprise keywords bonus
        novelty_words = [
            "accidental", "flaw", "myth", "wrong", "overlooked", "bizarre",
            "forbidden", "paradox", "unseen", "miracle", "shocking", "untold"
        ]
        bonus = sum(0.02 for w in novelty_words if w in text)
        return round(max(0.1, min(1.0, base + min(0.10, bonus))), 4)

    def _eval_hook_potential(self, angle: EditorialAngle) -> float:
        """Score capability to grab attention in first 3 seconds."""
        score = 0.75
        hooks = angle.key_hooks or []

        if not hooks:
            text = f"{angle.title} {angle.premise}".lower()
            if "?" in angle.title or any(w in text for w in ["why", "how", "secret", "never"]):
                return 0.80
            return 0.70

        score += min(0.10, len(hooks) * 0.03)

        # Check for rhetorical punch across hooks
        hook_text = " ".join(hooks).lower()
        if "?" in hook_text:
            score += 0.04
        if any(c.isdigit() for c in hook_text):
            score += 0.04
        if any(w in hook_text for w in ["never", "stop", "secret", "mistake", "billion", "truth", "shocking", "ruined"]):
            score += 0.05

        return round(max(0.1, min(1.0, score)), 4)

    def _eval_narrative_potential(self, angle: EditorialAngle) -> float:
        """Score conflict, escalation, stakes, and resolution structure."""
        text = f"{angle.title} {angle.premise} {angle.core_thesis}".lower()
        score = 0.75

        narrative_markers = [
            "crisis", "battle", "race", "bottleneck", "obstacle", "solved",
            "breakthrough", "struggle", "rivalry", "collapse", "triumph",
            "catastrophe", "discovered", "transformed", "engineered", "threat"
        ]
        matches = sum(1 for m in narrative_markers if m in text)
        score += min(0.18, matches * 0.04)

        return round(max(0.1, min(1.0, score)), 4)

    def _eval_creator_fit(
        self,
        angle: EditorialAngle,
        creator: Optional[CreatorProfile],
    ) -> float:
        """Score creator DNA alignment and enforce negative rule compliance."""
        if not creator:
            return 0.85

        score = 0.85
        text = f"{angle.title} {angle.premise} {angle.core_thesis} {' '.join(angle.key_hooks)}".lower()

        # Check negative rules (severe penalty for violation)
        negative_rules = creator.negative_rules or []
        for rule in negative_rules:
            rule_lower = rule.lower()
            # Extract common forbidden tokens if formatted like 'Never use buzzwords like "X"'
            extracted_tokens = re.findall(r"['\"](.*?)['\"]", rule_lower)
            if not extracted_tokens:
                extracted_tokens = [w for w in rule_lower.split() if len(w) > 5 and w not in ["never", "avoid", "always", "should"]]

            for token in extracted_tokens:
                if token in text:
                    score -= 0.25

        # Check tone of voice alignment
        for tone in (creator.tone_of_voice or []):
            if tone.lower() in text or tone.lower() in (angle.narrative_style or "").lower():
                score += 0.03

        return round(max(0.1, min(1.0, score)), 4)

    def _eval_evidence_availability(
        self,
        angle: EditorialAngle,
        dossier: Optional[ResearchDossier],
    ) -> float:
        """Score density, reliability, and confidence of supporting research evidence."""
        if not dossier:
            return 0.70

        claims = dossier.claims or []
        if not claims:
            return 0.40

        score = 0.50
        # Claim count scaling
        score += min(0.30, len(claims) * 0.06)

        # Average confidence of claims
        confidences = [c.confidence_score for c in claims if hasattr(c, "confidence_score")]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            score += avg_conf * 0.15

        # Statistics bonus
        stats = dossier.statistics or []
        if stats:
            score += min(0.08, len(stats) * 0.02)

        return round(max(0.1, min(1.0, score)), 4)

    def _eval_visual_potential(
        self,
        angle: EditorialAngle,
        dossier: Optional[ResearchDossier],
    ) -> float:
        """Score potential for rich diagrams, collages, and dynamic visual components."""
        text = f"{angle.title} {angle.premise} {angle.core_thesis}".lower()
        score = 0.72

        visual_words = [
            "schematic", "blueprint", "microscopic", "architecture", "timeline",
            "comparison", "graphic", "layer", "scale", "circuit", "silicon",
            "exploded view", "map", "chart", "counter", "animation"
        ]
        matches = sum(1 for w in visual_words if w in text)
        score += min(0.15, matches * 0.03)

        if dossier and dossier.suggested_visual_queries:
            score += min(0.10, len(dossier.suggested_visual_queries) * 0.02)

        return round(max(0.1, min(1.0, score)), 4)

    def _eval_platform_fit(
        self,
        angle: EditorialAngle,
        brief: Optional[ContentBrief],
    ) -> float:
        """Score compatibility with target aspect ratio and production pacing."""
        score = 0.85
        if not brief:
            return score

        aspect = brief.aspect_ratio or "16:9"
        duration = brief.target_duration_seconds or 30

        # Vertical format (9:16) favors high-hook, punchy styles
        if aspect == "9:16":
            if angle.key_hooks and len(angle.key_hooks) >= 2:
                score += 0.05
            if duration <= 45:
                score += 0.05
            else:
                score -= 0.05
        # Horizontal format (16:9) favors structured, deep-dive or documentary narrative
        elif aspect == "16:9":
            if duration >= 30:
                score += 0.05
            if "deep dive" in (angle.narrative_style or "").lower() or "data" in (angle.narrative_style or "").lower():
                score += 0.05

        return round(max(0.1, min(1.0, score)), 4)

    def _eval_saturation_risk(self, angle: EditorialAngle) -> float:
        """Score saturation penalty (0.0 = completely fresh, 1.0 = overused generic cliché)."""
        text = f"{angle.title} {angle.premise}".lower()
        risk = 0.15

        cliches = [
            "the history of", "a brief history", "everything you need to know",
            "the ultimate guide", "what is", "simple explanation", "for beginners",
            "introduction to", "the complete story", "how it works in 5 minutes"
        ]
        for c in cliches:
            if c in text:
                risk += 0.20

        # Generic title penalty
        if len(angle.title.split()) <= 3 and not any(w in text for w in ["why", "how", "secret", "paradox"]):
            risk += 0.15

        return round(max(0.0, min(1.0, risk)), 4)


# Engine alias
ScorecardEngine = EditorialScorer
