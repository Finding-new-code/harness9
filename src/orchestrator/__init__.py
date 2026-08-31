"""
src.orchestrator — Unified End-to-End Pipeline Orchestrator & CLI Runner (Milestone 5).

Provides:
- Pipeline: Master orchestrator linking Stages 1 to 5
- run_pipeline: Convenience function for pipeline execution
- main: CLI execution entrypoint
"""

from src.orchestrator.pipeline import (
    Pipeline,
    run_pipeline,
)
from src.orchestrator.cli import (
    main,
    build_parser,
)

__all__ = [
    "Pipeline",
    "run_pipeline",
    "main",
    "build_parser",
]
