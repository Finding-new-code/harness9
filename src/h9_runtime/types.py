"""src/h9_runtime/types.py

Shared type definitions, dataclasses, enums, and structured contracts
for the Harness 9 Runtime Boundary Interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class CapabilityRole(str, Enum):
    """Logical capability roles routing model inference requests."""

    FAST_EDITORIAL = "fast_editorial"
    REASONING_RESEARCH = "reasoning_research"
    CREATIVE_SCRIPT = "creative_script"
    ACOUSTIC_EVAL = "acoustic_eval"

    # Aliases for cross-specification compatibility
    FAST_INFERENCE = "fast_inference"
    REASONING_DEEP = "reasoning_deep"
    CREATIVE_SYNTHESIS = "creative_synthesis"
    VOICE_SYNTHESIS = "voice_synthesis"
    VISION_ANALYSIS = "vision_analysis"


class SubagentStatus(str, Enum):
    """Execution status of a delegated subagent task."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class SubagentResult:
    """Outcome and telemetry of a delegated subagent execution."""

    subagent_id: str
    status: SubagentStatus
    output: str
    structured_data: Optional[Dict[str, Any]] = None
    iterations_used: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None

    @property
    def result(self) -> Dict[str, Any]:
        """Convenience accessor for structured subagent result data."""
        res = dict(self.structured_data) if self.structured_data else {}
        if "task" not in res:
            res["task"] = res.get("goal", self.output)
        return res


@dataclass
class SessionState:
    """Live state, active tools, and telemetry of an agent execution session."""

    session_id: str
    current_state: str
    active_tools: List[str] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 50
    is_interrupted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class SkillMetadata:
    """Tier 1 metadata for progressive disclosure skill discovery."""

    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Harness 9"
    platforms: List[str] = field(default_factory=lambda: ["linux", "macos", "windows"])
    tags: List[str] = field(default_factory=list)
    skill_dir: Optional[Path] = None


@dataclass(frozen=True)
class ToolDefinition:
    """Specification and registration bundle for a model tool."""

    name: str
    toolset: str
    schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Union[str, Dict[str, Any]]]
    description: str = ""
    emoji: str = "⚡"
    is_async: bool = False
    check_fn: Optional[Callable[[], bool]] = None
    max_result_size_chars: Optional[int] = None


@dataclass(frozen=True)
class ToolInvocationContext:
    """Contextual metadata provided during tool dispatch."""

    session_id: str
    task_id: str
    tool_call_id: Optional[str] = None
    turn_id: Optional[str] = None
    capability_token: Optional[str] = None


@dataclass(frozen=True)
class ModelResponse:
    """Structured response from a model capability invocation."""

    content: str
    parsed: Optional[Any] = None
    model_name: str = ""
    provider_name: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "parsed": (
                self.parsed.to_dict()
                if hasattr(self.parsed, "to_dict")
                else (self.parsed.model_dump() if hasattr(self.parsed, "model_dump") else self.parsed)
            ),
            "model_name": self.model_name,
            "provider_name": self.provider_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cached_tokens": self.cached_tokens,
            "cost_usd": self.cost_usd,
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True)
class BudgetStatus:
    """Token consumption, cost tracking, and spend ceilings."""

    session_id: str
    tokens_consumed: int = 0
    cost_usd: float = 0.0
    budget_limit_usd: Optional[float] = None
    remaining_budget_usd: Optional[float] = None


@dataclass(frozen=True)
class MemoryRecallItem:
    """Retrieved memory item matching a contextual or semantic query."""

    source: str
    category: str
    content: str
    score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    """Outcome of a sandboxed command or subprocess execution."""

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float = 0.0
    timed_out: bool = False


@dataclass(frozen=True)
class ProductionIR:
    """Typed Intermediate Representation AST between scriptwriting and HyperFrames."""

    project_id: str
    aspect_ratio: str = "16:9"
    duration_seconds: float = 30.0
    fps: int = 30
    timeline_blocks: List[Dict[str, Any]] = field(default_factory=list)
    audio_tracks: List[Dict[str, Any]] = field(default_factory=list)
    css_variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "aspect_ratio": self.aspect_ratio,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "timeline_blocks": self.timeline_blocks,
            "audio_tracks": self.audio_tracks,
            "css_variables": self.css_variables,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ProductionResult:
    """Final output artifact bundle of an autonomous production run."""

    success: bool
    project_id: str
    session_id: str
    video_path: Optional[str] = None
    render_artifact: Optional[Any] = None
    publish_package: Optional[Any] = None
    evaluation_report: Optional[Any] = None
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "video_path": self.video_path,
            "render_artifact": (
                self.render_artifact.to_dict()
                if hasattr(self.render_artifact, "to_dict")
                else self.render_artifact
            ),
            "publish_package": (
                self.publish_package.to_dict()
                if hasattr(self.publish_package, "to_dict")
                else self.publish_package
            ),
            "evaluation_report": (
                self.evaluation_report.to_dict()
                if hasattr(self.evaluation_report, "to_dict")
                else self.evaluation_report
            ),
            "state_history": self.state_history,
            "elapsed_seconds": self.elapsed_seconds,
            "error_message": self.error_message,
        }
