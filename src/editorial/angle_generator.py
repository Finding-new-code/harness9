"""Multi-Angle Ideation Generator across 5 Archetypes (Milestone M2).

Generates candidate editorial angles for a topic across 5 canonical archetypes:
1. contrarian: The Counterintuitive Revelation / Accidental Revolution
2. deep_dive: The Microscopic Architecture / Nanometer Miracle
3. data_led: The Quantitative Reality / Exponential Curve
4. human_narrative: The Unsung Pioneers / High-Stakes Race
5. future_impact: The Modern Domino Effect / Horizon Collapse
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.models.contracts import (
    ContentBrief,
    CreatorProfile,
    EditorialAngle,
    EditorialScorecard,
    ResearchDossier,
)
from src.editorial.scorecard import EditorialScorer


class AngleArchetype(str, Enum):
    CONTRARIAN = "contrarian"
    DEEP_DIVE = "deep_dive"
    DATA_LED = "data_led"
    HUMAN_NARRATIVE = "human_narrative"
    FUTURE_IMPACT = "future_impact"


ARCHETYPE_STYLES: Dict[AngleArchetype, str] = {
    AngleArchetype.CONTRARIAN: "Contrarian Revelation",
    AngleArchetype.DEEP_DIVE: "Technical Deep Dive",
    AngleArchetype.DATA_LED: "Data-Driven Analysis",
    AngleArchetype.HUMAN_NARRATIVE: "Human-Centric Drama",
    AngleArchetype.FUTURE_IMPACT: "Futurist Speculation",
}


class AngleGenerator:
    """Generates orthogonal candidate editorial angles from research dossiers."""

    def __init__(self, scorer: Optional[EditorialScorer] = None):
        self.scorer = scorer or EditorialScorer()

    def generate_candidates(
        self,
        dossier: ResearchDossier,
        brief: Optional[ContentBrief] = None,
        creator: Optional[CreatorProfile] = None,
        archetypes: Optional[List[AngleArchetype]] = None,
    ) -> List[EditorialAngle]:
        """Generate candidate editorial angles across all 5 archetypes with calculated scorecards."""
        target_archetypes = archetypes or [
            AngleArchetype.CONTRARIAN,
            AngleArchetype.DEEP_DIVE,
            AngleArchetype.DATA_LED,
            AngleArchetype.HUMAN_NARRATIVE,
            AngleArchetype.FUTURE_IMPACT,
        ]

        topic = dossier.topic if hasattr(dossier, "topic") and dossier.topic else "Advanced Technology"
        candidates: List[EditorialAngle] = []

        # Extract dossier signals
        claims_text = " ".join([c.claim_text for c in (dossier.claims or []) if hasattr(c, "claim_text")])
        headline = getattr(dossier, "headline", "") or ""
        statistics = getattr(dossier, "statistics", []) or []
        stat_summary = f"{statistics[0].metric}: {statistics[0].value}" if statistics else ""

        for idx, archetype in enumerate(target_archetypes, start=1):
            angle = self._build_angle_for_archetype(
                archetype=archetype,
                angle_id=f"angle_{idx}",
                topic=topic,
                headline=headline,
                claims_text=claims_text,
                stat_summary=stat_summary,
                brief=brief,
                creator=creator,
            )
            # Evaluate 9-dimension scorecard
            angle.scorecard = self.scorer.score_angle(
                angle=angle,
                dossier=dossier,
                brief=brief,
                creator=creator,
            )
            candidates.append(angle)

        return candidates

    def generate_candidate_angles(
        self,
        dossier: ResearchDossier,
        brief: Optional[ContentBrief] = None,
        creator: Optional[CreatorProfile] = None,
    ) -> List[EditorialAngle]:
        """Alias for generate_candidates."""
        return self.generate_candidates(dossier=dossier, brief=brief, creator=creator)

    # -----------------------------------------------------------------------
    # Archetype Builder Implementations
    # -----------------------------------------------------------------------
    def _build_angle_for_archetype(
        self,
        archetype: AngleArchetype,
        angle_id: str,
        topic: str,
        headline: str,
        claims_text: str,
        stat_summary: str,
        brief: Optional[ContentBrief],
        creator: Optional[CreatorProfile],
    ) -> EditorialAngle:
        """Construct structured EditorialAngle for a specific archetype."""
        style = ARCHETYPE_STYLES.get(archetype, "Cinematic Discovery")
        target_aud = brief.audience if brief and brief.audience else "General Tech Enthusiasts"

        if archetype == AngleArchetype.CONTRARIAN:
            title = f"The Accidental Paradox: Why Everyone Misunderstands {topic}"
            premise = (
                f"Most explanations of {topic} portray it as a deliberate, linear breakthrough. "
                f"In reality, it was triggered by a counterintuitive flaw and accidental discoveries that "
                f"conventional experts initially rejected."
            )
            core_thesis = (
                f"The core breakthrough of {topic} succeeded specifically because its pioneers ignored "
                f"established dogma and exploited a physical paradox everyone else dismissed."
            )
            hooks = [
                f"What if the most important breakthrough in {topic} was actually a complete accident?",
                f"99% of people misunderstand how {topic} actually works—and the truth is far stranger.",
                f"The machine that powers {topic} was originally built to do something completely different.",
            ]

        elif archetype == AngleArchetype.DEEP_DIVE:
            title = f"The Nanometer Miracle: How {topic} Actually Works Under the Hood"
            premise = (
                f"Stripping away the high-level buzzwords to examine the microscopic physics, architecture, "
                f"and engineering bottlenecks that make {topic} physically possible at scale."
            )
            core_thesis = (
                f"The true marvel of {topic} lies in microscopic engineering tolerances where quantum physics "
                f"and mechanical limits are conquered through ingenious architectural design."
            )
            hooks = [
                f"Under a microscope, {topic} looks less like technology and more like science fiction.",
                f"How do engineers force nature to obey rules that shouldn't physically be possible in {topic}?",
                f"This is the exact microscopic mechanism inside {topic} that modern civilization relies on.",
            ]

        elif archetype == AngleArchetype.DATA_LED:
            metric_snippet = f" (such as {stat_summary})" if stat_summary else ""
            title = f"The Exponential Reality: The Hard Math and Metrics of {topic}"
            premise = (
                f"A rigorous, metric-first breakdown of {topic}{metric_snippet}, tracking scaling curves, "
                f"efficiency multipliers, and the astronomical figures governing modern performance."
            )
            core_thesis = (
                f"When evaluated through raw quantitative data, the trajectory of {topic} proves that "
                f"we have crossed an irreversible threshold in computational and technical efficiency."
            )
            hooks = [
                f"The single number behind {topic} that proves our entire world has quietly changed.",
                f"When you look at the raw data for {topic}, the exponential curve is almost terrifying.",
                f"Behind every unit of {topic} is a mathematical equation that took 50 years to balance.",
            ]

        elif archetype == AngleArchetype.HUMAN_NARRATIVE:
            title = f"The Secret Race: The Unsung Pioneers Who Risked Everything for {topic}"
            premise = (
                f"Behind the technical specifications of {topic} lies a high-stakes human drama of rival labs, "
                f"desperate sleepless deadlines, and forgotten researchers who bet their careers on an impossible idea."
            )
            core_thesis = (
                f"Technology is never just equations—{topic} was forged through fierce human rivalry, "
                f"stubborn obsession, and the courage to pursue what every peer deemed impossible."
            )
            hooks = [
                f"In a dimly lit laboratory, two researchers made a bet that would accidentally change the world.",
                f"The forgotten engineers behind {topic} never got the credit, but you use their invention every day.",
                f"They were given 6 months to solve {topic} or face total project cancellation.",
            ]

        elif archetype == AngleArchetype.FUTURE_IMPACT:
            title = f"The Modern Domino Effect: Why {topic} Governs the Next 20 Years"
            premise = (
                f"Tracing the global geopolitical, economic, and societal supply chain dependencies that make "
                f"{topic} the single most critical chokepoint of the 21st century."
            )
            core_thesis = (
                f"{topic} is no longer just a technical tool—it is the foundational keystone upon which global "
                f"economic power, sovereignty, and future security are now decided."
            )
            hooks = [
                f"If {topic} stopped functioning tomorrow, global infrastructure would grind to a halt in 48 hours.",
                f"The hidden geopolitical battle for {topic} that will determine the next century.",
                f"Why the future of world economics depends entirely on a technology few people truly understand.",
            ]

        return EditorialAngle(
            angle_id=angle_id,
            title=title,
            premise=premise,
            core_thesis=core_thesis,
            target_audience=target_aud,
            narrative_style=style,
            key_hooks=hooks,
            selected=False,
        )
