"""src.hyperframes.components — Reusable Parameterized HyperFrames Component Blocks (Milestone M3).

Exports:
- BaseComponent, ComponentSchema, ValidationResult
- ReferenceCollageHook (Block 1)
- SplitScreenIntro (Block 2)
- QuoteHighlight (Block 3)
- TimelineReveal (Block 4)
- StatisticReveal (Block 5)
- ComparisonPanel (Block 6)
- CreatorBottomCollage (Block 7)
"""

from src.hyperframes.components.base import (
    BaseComponent,
    ComponentSchema,
    ValidationResult,
)
from src.hyperframes.components.reference_collage_hook import ReferenceCollageHook
from src.hyperframes.components.split_screen_intro import SplitScreenIntro
from src.hyperframes.components.quote_highlight import QuoteHighlight
from src.hyperframes.components.timeline_reveal import TimelineReveal
from src.hyperframes.components.statistic_reveal import StatisticReveal
from src.hyperframes.components.comparison_panel import ComparisonPanel
from src.hyperframes.components.creator_bottom_collage import CreatorBottomCollage

__all__ = [
    "BaseComponent",
    "ComponentSchema",
    "ValidationResult",
    "ReferenceCollageHook",
    "SplitScreenIntro",
    "QuoteHighlight",
    "TimelineReveal",
    "StatisticReveal",
    "ComparisonPanel",
    "CreatorBottomCollage",
]
