"""src/h9_runtime — Harness 9 Runtime Boundary Interface Package.

Exposes clean runtime protocols and implementations decoupling H9 domain modules
from internal Hermes Agent implementation details:
- AgentRuntime: Session state, turn execution, subagent delegation
- SkillRuntime: Progressive disclosure skill discovery and instruction loading
- ToolRuntime: Tool registration, schema generation, parameter validation, dispatch
- ModelRuntime: Logical capability role routing, token and budget accounting
- MemoryRuntime: Creator DNA persistence, performance memory, SessionDB bridging
- ExecutionRuntime: Sandboxed command execution, path confinement, atomic file I/O
- ContentRuntime: High-level content orchestration, Production IR compilation, video rendering
"""

from src.h9_runtime.agent import (
    AgentRuntime,
    DefaultAgentRuntime,
)
from src.h9_runtime.bridge import (
    HermesCapabilityBridge,
    get_capability_bridge,
    reset_capability_bridges,
)
from src.h9_runtime.content import (
    ContentRuntime,
    DefaultContentRuntime,
)
from src.h9_runtime.execution import (
    DefaultExecutionRuntime,
    ExecutionRuntime,
    HermesExecutionRuntime,
    resolve_environment,
)
from src.h9_runtime.memory import (
    DefaultMemoryRuntime,
    HermesMemoryRuntime,
    MemoryRuntime,
)
from src.h9_runtime.models import (
    DefaultModelRuntime,
    ModelRuntime,
)
from src.h9_runtime.skills import (
    DefaultSkillRuntime,
    SkillRuntime,
)
from src.h9_runtime.tools import (
    DefaultToolRuntime,
    ToolRuntime,
)
from src.h9_runtime.types import (
    BudgetStatus,
    CapabilityRole,
    ExecutionResult,
    MemoryRecallItem,
    ModelResponse,
    ProductionIR,
    ProductionResult,
    SessionState,
    SkillMetadata,
    SubagentResult,
    SubagentStatus,
    ToolDefinition,
    ToolInvocationContext,
)

__all__ = [
    # Bridge
    "HermesCapabilityBridge",
    "get_capability_bridge",
    "reset_capability_bridges",
    # Protocols
    "AgentRuntime",
    "SkillRuntime",
    "ToolRuntime",
    "ModelRuntime",
    "MemoryRuntime",
    "ExecutionRuntime",
    "ContentRuntime",
    # Implementations
    "DefaultAgentRuntime",
    "DefaultSkillRuntime",
    "DefaultToolRuntime",
    "DefaultModelRuntime",
    "DefaultMemoryRuntime",
    "HermesMemoryRuntime",
    "DefaultExecutionRuntime",
    "HermesExecutionRuntime",
    "resolve_environment",
    "DefaultContentRuntime",
    # Types & Enums
    "CapabilityRole",
    "SubagentStatus",
    "SubagentResult",
    "SessionState",
    "SkillMetadata",
    "ToolDefinition",
    "ToolInvocationContext",
    "ModelResponse",
    "BudgetStatus",
    "MemoryRecallItem",
    "ExecutionResult",
    "ProductionIR",
    "ProductionResult",
]

