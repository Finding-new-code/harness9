"""Hook Ideation & Retention Optimization Engine (Milestone M2).

Generates at least 3 distinct psychological hook variations:
1. question (Curiosity Gap): Provocative open question challenging status quo.
2. paradox (Cognitive Dissonance): Two mutually conflicting truths creating cognitive tension.
3. dramatic_statement (High Stakes / Urgency): Bold declaration of existential scale or danger.
4. cold_open (Sensory Immersion): Visual in-media-res moment anchoring the listener in a specific scene.
5. statistic_shock (Scale Wonder): Shocking empirical metric demonstrating astronomical scale.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field

from src.models.contracts import (
    EditorialAngle,
    H9BaseModel,
    ResearchDossier,
)


class HookOption(H9BaseModel):
    """Structured hook variation with psychological retention targeting and visual cue."""
    hook_id: str = Field(..., min_length=1)
    hook_type: str = Field(..., min_length=1)  # "question", "paradox", "dramatic_statement", "cold_open", "statistic_shock"
    text: str = Field(..., min_length=1)
    estimated_retention_lift: float = Field(default=0.85, ge=0.0, le=1.0)
    visual_cue: str = Field(default="")
    psychological_trigger: str = Field(default="Curiosity Gap")

    def __str__(self) -> str:
        return self.text


class HookGenerator:
    """Synthesizes high-retention hook options for a selected editorial angle."""

    def generate_hooks(
        self,
        angle: EditorialAngle,
        dossier: Optional[ResearchDossier] = None,
        count: int = 3,
    ) -> List[HookOption]:
        """Generate at least `count` distinct hook options across different psychological archetypes."""
        topic = dossier.topic if dossier and hasattr(dossier, "topic") and dossier.topic else "this technology"
        angle_title = angle.title or f"The Story of {topic}"

        # Extract research signals
        stats = dossier.statistics if dossier and hasattr(dossier, "statistics") else []
        claims = dossier.claims if dossier and hasattr(dossier, "claims") else []
        stat_snippet = f"{stats[0].value} {stats[0].metric}" if stats else "billions of operations per second"
        claim_snippet = claims[0].claim_text if claims else f"{topic} completely altered the path of computing"

        hooks: List[HookOption] = []

        # 1. Question (Curiosity Gap)
        q_text = f"What if the biggest breakthrough in {topic} was actually a complete accident?"
        if "?" in (angle.key_hooks[0] if angle.key_hooks else ""):
            q_text = angle.key_hooks[0]
        hooks.append(
            HookOption(
                hook_id="hook_q1",
                hook_type="question",
                text=q_text,
                estimated_retention_lift=0.92,
                visual_cue="Macro close-up with pulsing question mark overlay and dark ambient lighting",
                psychological_trigger="Curiosity Gap",
            )
        )

        # 2. Paradox (Cognitive Dissonance)
        p_text = f"The technology behind {topic} was physically impossible—until a mistake proved the textbooks wrong."
        hooks.append(
            HookOption(
                hook_id="hook_p1",
                hook_type="paradox",
                text=p_text,
                estimated_retention_lift=0.94,
                visual_cue="Split-screen comparison: theoretical textbook formula vs glowing physical prototype",
                psychological_trigger="Cognitive Dissonance",
            )
        )

        # 3. Dramatic Statement (High Stakes / Urgent)
        d_text = f"If {topic} stopped working for just 5 seconds, the global digital economy would suffer catastrophic collapse."
        hooks.append(
            HookOption(
                hook_id="hook_d1",
                hook_type="dramatic_statement",
                text=d_text,
                estimated_retention_lift=0.89,
                visual_cue="High-contrast warning graphic with rapid world map telemetry zoom",
                psychological_trigger="High Stakes & Urgency",
            )
        )

        # 4. Cold Open (Sensory Immersion / In-Media-Res)
        c_text = f"Inside a dimly lit lab, two scientists stared at a needle and realized they had just invented {topic}."
        hooks.append(
            HookOption(
                hook_id="hook_c1",
                hook_type="cold_open",
                text=c_text,
                estimated_retention_lift=0.88,
                visual_cue="Cinematic archival film grain recreation with slow camera pan across vintage workbench",
                psychological_trigger="Sensory Immersion",
            )
        )

        # 5. Statistic Shock (Scale Wonder)
        s_text = f"{stat_snippet}. That is the single metric that separates {topic} from everything that came before it."
        hooks.append(
            HookOption(
                hook_id="hook_s1",
                hook_type="statistic_shock",
                text=s_text,
                estimated_retention_lift=0.91,
                visual_cue="Giant numeric counter spinning up rapidly with particle burst effect",
                psychological_trigger="Scale Wonder",
            )
        )

        # Ensure we return at least `count` options, default 3
        requested_count = max(3, count)
        return hooks[:requested_count]


# Generator alias
HookIdeator = HookGenerator
