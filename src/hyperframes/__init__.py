"""
src.hyperframes — HyperFrames Composition Generator, Validator & Video Renderer (Milestone 4).

Provides:
- HyperFramesGenerator: Compiles HTML5/CSS/GSAP composition source files
- CompositionValidator: Static linter and integrity validator
- HyperFramesRenderer: Frame capture and FFmpeg MP4 encoding pipeline
- validate_composition: Convenience validation function
"""

from src.hyperframes.generator import (
    HyperFramesGenerator,
)
from src.hyperframes.validator import (
    CompositionValidator,
    validate_composition,
)
from src.hyperframes.renderer import (
    HyperFramesRenderer,
    RenderResult,
    CompositionValidationError,
)

__all__ = [
    "HyperFramesGenerator",
    "CompositionValidator",
    "validate_composition",
    "HyperFramesRenderer",
    "RenderResult",
    "CompositionValidationError",
]
