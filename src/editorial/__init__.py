"""Editorial Intelligence & Multi-Angle Decision Engine (Milestone M2).

Public exports for:
- Angle generation across 5 archetypes
- 9-dimension editorial scorecard scoring
- Winning angle selection and audit rationale
- Hook variation generation
- 4-act narrative outline planning
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from src.models.contracts import (
    AngleScorecard,
    ContentBrief,
    ContentOutline,
    CreatorProfile,
    EditorialAngle,
    EditorialScorecard,
    OutlineAct,
    ResearchDossier,
)
from src.editorial.angle_generator import AngleArchetype, AngleGenerator
from src.editorial.hook_generator import HookGenerator, HookIdeator, HookOption
from src.editorial.narrative_planner import NarrativePlanner, OutlinePlanner
from src.editorial.scorecard import (
    EditorialScorer,
    SCORECARD_WEIGHTS,
    ScorecardEngine,
    calculate_scorecard_composite,
)
from src.editorial.selector import AngleSelector, WinningAngleSelector


class EditorialEngine:
    """Unified facade orchestrating the complete Editorial Intelligence workflow."""

    def __init__(
        self,
        scorer: Optional[EditorialScorer] = None,
        generator: Optional[AngleGenerator] = None,
        selector: Optional[AngleSelector] = None,
        hook_gen: Optional[HookGenerator] = None,
        planner: Optional[NarrativePlanner] = None,
    ):
        self.scorer = scorer or EditorialScorer()
        self.generator = generator or AngleGenerator(scorer=self.scorer)
        self.selector = selector or AngleSelector(scorer=self.scorer)
        self.hook_generator = hook_gen or HookGenerator()
        self.planner = planner or NarrativePlanner()

    def process_editorial(
        self,
        dossier: ResearchDossier,
        brief: Optional[ContentBrief] = None,
        creator: Optional[CreatorProfile] = None,
    ) -> Tuple[List[EditorialAngle], EditorialAngle, List[HookOption], ContentOutline]:
        """Execute complete editorial pipeline:
        1. Generate 5 candidate angles across archetypes
        2. Score candidates against 9-dimension scorecard
        3. Select top winning angle with audit rationale
        4. Generate 3+ hook options for winner
        5. Build structured 4-act ContentOutline
        """
        # Step 1 & 2: Generate and score candidate angles
        candidates = self.generator.generate_candidates(dossier=dossier, brief=brief, creator=creator)

        # Step 3: Select winning angle
        winner, _ = self.selector.select_winning_angle(candidates)

        # Step 4: Generate hook variations
        hooks = self.hook_generator.generate_hooks(angle=winner, dossier=dossier)
        primary_hook = hooks[0] if hooks else "The untold story."

        # Step 5: Build 4-act narrative outline
        outline = self.planner.build_outline(
            winning_angle=winner,
            hook=primary_hook,
            dossier=dossier,
            brief=brief,
        )

        return candidates, winner, hooks, outline


__all__ = [
    # Models & Enums
    "AngleArchetype",
    "EditorialAngle",
    "EditorialScorecard",
    "AngleScorecard",
    "ContentOutline",
    "OutlineAct",
    "HookOption",
    "SCORECARD_WEIGHTS",
    # Core Engines
    "AngleGenerator",
    "EditorialScorer",
    "ScorecardEngine",
    "calculate_scorecard_composite",
    "AngleSelector",
    "WinningAngleSelector",
    "HookGenerator",
    "HookIdeator",
    "NarrativePlanner",
    "OutlinePlanner",
    "EditorialEngine",
]
