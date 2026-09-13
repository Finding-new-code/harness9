"""4-Act Narrative Planning Engine (Milestone M2).

Transforms the winning editorial angle, primary hook, and research dossier
into a structured 4-act ContentOutline:
- Act 1: The Hook & Paradox (0% - 15% duration)
- Act 2: The Bottleneck & Context (15% - 45% duration)
- Act 3: The Core Insight & Mechanism (45% - 75% duration)
- Act 4: The Payoff & Horizon (75% - 100% duration)
"""

from typing import Any, Dict, List, Optional, Union

from src.models.contracts import (
    ContentBrief,
    ContentOutline,
    EditorialAngle,
    OutlineAct,
    ResearchDossier,
)
from src.editorial.hook_generator import HookOption


class NarrativePlanner:
    """Synthesizes structured 4-act narrative blueprints for the scriptwriting engine."""

    def build_outline(
        self,
        winning_angle: EditorialAngle,
        hook: Union[str, HookOption],
        dossier: Optional[ResearchDossier] = None,
        brief: Optional[ContentBrief] = None,
        target_duration: Optional[float] = None,
    ) -> ContentOutline:
        """Construct a validated 4-act ContentOutline from winning angle and selected hook."""
        topic = dossier.topic if dossier and hasattr(dossier, "topic") and dossier.topic else "Autonomous Tech"
        project_id = brief.project_id if brief and hasattr(brief, "project_id") else "proj_default"

        # Resolve duration: explicit arg -> brief -> default 30.0
        duration = 30.0
        if target_duration is not None and target_duration > 0:
            duration = float(target_duration)
        elif brief and hasattr(brief, "target_duration_seconds") and brief.target_duration_seconds:
            duration = float(brief.target_duration_seconds)

        # Extract primary hook text
        hook_text = str(hook.text if isinstance(hook, HookOption) else hook)

        # Extract available talking points from dossier
        talking_points = dossier.talking_points if dossier and hasattr(dossier, "talking_points") else []
        tp_indices = [tp.beat_index for tp in talking_points if hasattr(tp, "beat_index")]
        if not tp_indices:
            tp_indices = [1, 2, 3, 4]

        # Partition talking point indices across the 4 acts
        act1_tps = [tp_indices[0]] if len(tp_indices) >= 1 else [1]
        act2_tps = [tp_indices[1]] if len(tp_indices) >= 2 else act1_tps
        act3_tps = [tp_indices[2]] if len(tp_indices) >= 3 else [tp_indices[-1]]
        act4_tps = [tp_indices[3]] if len(tp_indices) >= 4 else [tp_indices[-1]]

        # Construct the canonical 4 Acts
        acts: List[OutlineAct] = [
            OutlineAct(
                act_index=1,
                act_name="The Hook & Paradox",
                target_start_pct=0.0,
                target_end_pct=0.15,
                narrative_job=(
                    f"Stop the viewer within 3.0 seconds with the primary hook: '{hook_text[:60]}...'. "
                    f"Establish the central paradox or high-stakes premise."
                ),
                talking_point_indices=act1_tps,
                visual_theme="reference_collage_hook",
            ),
            OutlineAct(
                act_index=2,
                act_name="The Bottleneck & Context",
                target_start_pct=0.15,
                target_end_pct=0.45,
                narrative_job=(
                    f"Contextualize the status quo and the seemingly insurmountable technical or historical barrier "
                    f"before {topic} was solved."
                ),
                talking_point_indices=act2_tps,
                visual_theme="split_screen_intro",
            ),
            OutlineAct(
                act_index=3,
                act_name="The Core Insight & Mechanism",
                target_start_pct=0.45,
                target_end_pct=0.75,
                narrative_job=(
                    f"Deep dive into the core architectural breakthrough and verifiable evidence: {winning_angle.core_thesis[:80]}..."
                ),
                talking_point_indices=act3_tps,
                visual_theme="statistic_reveal",
            ),
            OutlineAct(
                act_index=4,
                act_name="The Payoff & Horizon",
                target_start_pct=0.75,
                target_end_pct=1.0,
                narrative_job=(
                    f"Deliver the ultimate payoff, broad future domino effect, and lasting call-to-thought for {topic}."
                ),
                talking_point_indices=act4_tps,
                visual_theme="creator_bottom_collage",
            ),
        ]

        return ContentOutline(
            project_id=project_id,
            topic=topic,
            angle_id=winning_angle.angle_id,
            angle_title=winning_angle.title,
            primary_hook=hook_text,
            acts=acts,
            total_estimated_duration=duration,
        )


# Planner alias
OutlinePlanner = NarrativePlanner
