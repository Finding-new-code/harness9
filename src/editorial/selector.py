"""Winning Editorial Angle Selection Algorithm (Milestone M2).

Ranks candidate editorial angles based on 9-dimension scorecards with multi-tier
deterministic tie-breaking, sets audit rationale, and flags the winning angle.
"""

from typing import Any, Dict, List, Optional, Tuple

from src.models.contracts import EditorialAngle, EditorialScorecard
from src.editorial.scorecard import EditorialScorer


class AngleSelector:
    """Ranks candidate angles and selects the optimal angle with an audit rationale."""

    def __init__(self, scorer: Optional[EditorialScorer] = None):
        self.scorer = scorer or EditorialScorer()

    def rank_angles(
        self,
        angles: List[EditorialAngle],
        scorecards: Optional[List[EditorialScorecard]] = None,
    ) -> List[EditorialAngle]:
        """Rank candidate angles in descending order with deterministic tie-breaking."""
        if not angles:
            return []

        # If external scorecards are provided, map them to the angles
        if scorecards and len(scorecards) == len(angles):
            for a, sc in zip(angles, scorecards):
                a.scorecard = sc

        # Ensure all angles have a valid scorecard
        for a in angles:
            if a.scorecard is None:
                a.scorecard = self.scorer.score_angle(a)

        # Multi-factor deterministic sort key:
        # 1. composite_score (descending)
        # 2. hook_potential (descending)
        # 3. novelty (descending)
        # 4. evidence_availability (descending)
        # 5. angle_id (ascending for strict determinism)
        def sort_key(a: EditorialAngle) -> Tuple[float, float, float, float, str]:
            sc = a.scorecard
            comp = sc.composite_score if sc else 0.0
            hook = sc.hook_potential if sc else 0.0
            nov = sc.novelty if sc else 0.0
            evid = sc.evidence_availability if sc else 0.0
            # Note: For ascending angle_id, we can sort with custom comparator or inverse
            return (comp, hook, nov, evid, a.angle_id)

        # Sort using Python's stable sort with primary criteria
        # We sort by angle_id first (ascending), then by scores (descending)
        sorted_angles = sorted(angles, key=lambda a: a.angle_id)
        sorted_angles = sorted(
            sorted_angles,
            key=lambda a: (
                a.scorecard.composite_score if a.scorecard else 0.0,
                a.scorecard.hook_potential if a.scorecard else 0.0,
                a.scorecard.novelty if a.scorecard else 0.0,
                a.scorecard.evidence_availability if a.scorecard else 0.0,
            ),
            reverse=True,
        )

        return sorted_angles

    def select_winning_angle(
        self,
        angles: List[EditorialAngle],
        scorecards: Optional[List[EditorialScorecard]] = None,
    ) -> Tuple[EditorialAngle, EditorialScorecard]:
        """Rank candidates, mark the winning angle, generate audit rationale, and return (winner, scorecard)."""
        if not angles:
            raise ValueError("Cannot select winning angle from an empty candidate list.")

        ranked = self.rank_angles(angles=angles, scorecards=scorecards)
        winner = ranked[0]

        # Reset selection flags
        for a in angles:
            a.selected = (a.angle_id == winner.angle_id)
            if a.angle_id != winner.angle_id:
                a.selection_rationale = None

        # Build detailed audit rationale for the winner
        sc = winner.scorecard or EditorialScorecard()
        rationale = (
            f"Selected as winning editorial angle '{winner.title}' with top composite score of {sc.composite_score:.4f}. "
            f"Key differentiators: hook_potential={sc.hook_potential:.2f}, novelty={sc.novelty:.2f}, "
            f"audience_relevance={sc.audience_relevance:.2f}, evidence_availability={sc.evidence_availability:.2f}, "
            f"saturation_risk={sc.saturation_risk:.2f} (narrative style: '{winner.narrative_style}')."
        )
        winner.selected = True
        winner.selection_rationale = rationale

        return winner, sc

    def select(self, angles: List[EditorialAngle]) -> EditorialAngle:
        """Convenience method returning the winning EditorialAngle directly."""
        winner, _ = self.select_winning_angle(angles)
        return winner


WinningAngleSelector = AngleSelector
