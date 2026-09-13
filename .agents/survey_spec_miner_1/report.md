# Comprehensive Specification Miner Report: Hermes Runtime & Harness 9 Direct Integration

**Document Version:** 1.0.0  
**Author:** survey_spec_miner_1 (Teamwork Preview Spec Miner)  
**Target Path:** `docs/architecture/hermes-h9-runtime-coupling.md` / `src/h9_runtime/`  
**Date:** 2026-09-04  

---

## 1. Executive Summary

This report establishes the authoritative specification and architectural bridge for refactoring **Harness 9 (H9)** to execute natively and directly through the **Hermes Agent runtime**. 

In the initial Milestone 1 architecture, Harness 9 operated as an external execution monolith invoked solely through high-level tool wrappers (`generate_video_from_brief`, `inspect_production_state`, `evaluate_content_quality`). Under the 2026-09-04 mandate, Harness 9's content-production capabilities are refactored to run directly through the full Hermes Agent runtime:
1. **Core Agent Loop & Multi-Turn Reasoning:** Replacing monolithic one-shot pipeline execution with native step-by-step agent tool calling, streaming progress, and human/gateway interruptability.
2. **First-Class Hermes Tools:** Exposing granular H9 capabilities (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) as registered Hermes tools under a dedicated `harness9` toolset.
3. **Hermes Skills Standard:** Packaging domain workflows into native Hermes skills (`skills/h9-research/`, `skills/h9-content-planning/`, `skills/h9-production/`, `skills/h9-hyperframes/`) adhering strictly to the `SKILL.md` progressive disclosure standard.
4. **Logical Capability Provider Routing:** Eliminating hardcoded LLM endpoints by routing model inference through Hermes provider adapters via capability roles (`fast_inference`, `reasoning_deep`, `creative_synthesis`, `voice_synthesis`).
5. **Unified Memory & State Persistence:** Interfacing Creator DNA (`CreatorProfile`, `PerformanceMemory`, `NegativeMemory`) directly with Hermes's `MemoryManager` / `MemoryProvider` architecture and SQLite `SessionDB`, eliminating duplicate persistence engines.
6. **Subagent Research Delegation:** Delegating multi-source fact synthesis to an isolated Hermes child agent (`delegate_task`) that executes with bounded iterations and returns a structured `ResearchDossier` without leaking scraping scrapings into the parent conversation history.
7. **Sandbox & Permission Enforcement:** Unifying H9 capability tokens with Hermes environments (`BaseEnvironment`, Docker/Modal/local) and approval mechanics to enforce strict least-privilege boundaries.
8. **Decoupled Boundary Abstraction (`src/h9_runtime/`):** Establishing a canonical, typed runtime boundary (`AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`) ensuring H9 content services never import or depend on internal Hermes implementation details.

---

## 2. Features Discovered & Edge Cases

### Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Tool Registration | `ToolRegistry.register` | Module-level tool declaration with schema, handler, check_fn, and dynamic overrides | `name`, `toolset`, `schema`, `handler`, `check_fn`, etc. | None (registers in registry) | Rejects cross-toolset shadowing unless `override=True` | `tools/registry.py` |
| 2 | Tool Availability | `_check_fn_cached` | 30s TTL caching of tool availability probes with 60s transient failure grace | `fn: Callable` | `bool` | Serves last-good True on flake; logs warning | `tools/registry.py` |
| 3 | Tool Dispatch | `ToolRegistry.dispatch` | Executes tool handler, bridging async coroutines via persistent worker event loops | `name`, `args`, `scope`, `**kwargs` | JSON string or multimodal dict | Sanitized `{"error": ...}` JSON string | `tools/registry.py`, `model_tools.py` |
| 4 | Tool Search Bridge | `tool_search`, `tool_describe`, `tool_call` | Dynamic tool discovery bridge for large tool catalogs, deferring tool schemas | Search query, tool name, invocation args | Tool descriptions or unwrapped execution | Restricts calls strictly to session's granted toolsets | `model_tools.py`, `tools/tool_search.py` |
| 5 | Skill Progressive Disclosure | `skills_list` & `skill_view` | Two-tier disclosure: Tier 1 metadata in index; Tier 2/3 full SKILL.md & references on demand | `skill_name`, optional `subpath` | Markdown text / file content | `tool_error("Skill not found")` / path traversal blocked | `tools/skills_tool.py` |
| 6 | Skill Prompt Index | `build_skills_system_prompt` | Builds byte-stable compact skill index table for LLM system prompt | Available tools, toolsets, categories | System prompt text block | Omits unavailable or platform-mismatched skills | `agent/prompt_builder.py` |
| 7 | Prompt Caching | `PromptCachePlan` | Applies 4 cache breakpoints (system prefix, system end, last 2 turns) for Anthropic/OpenRouter | `messages`, `tools`, `provider` | Modified message list with `cache_control` | Bypasses part-level markers on LiteLLM routes (#89886) | `agent/prompt_caching.py` |
| 8 | Memory Management | `MemoryManager` & `MemoryProvider` | Single-external-provider memory orchestration with prefetch, post-turn sync, and compression checkpoints | User prompt, turn messages | Injected context, background persistence | Rejects secondary external memory plugins | `agent/memory_manager.py`, `agent/memory_provider.py` |
| 9 | Subagent Delegation | `delegate_task` | Spawns isolated child `AIAgent` with fresh history, dedicated `task_id`, and stripped blocked tools | `task`, `goal`, `context`, `tools` | Final summary string result | Auto-denies dangerous commands; budget enforcement | `tools/delegate_tool.py` |
| 10 | Execution Environments | `BaseEnvironment` | Spawns processes in isolated local, Docker, Modal, Singularity, or SSH sandboxes | `command`, `timeout`, `cwd` | `(stdout, stderr, exit_code)` | Raises `EnvironmentConnectionError`; bounded spillover | `tools/environments/base.py` |
| 11 | Command Approvals | `detect_dangerous_command` | Interactive CLI & async gateway approval gating for shell commands | `command`, `session_key` | Approval status (`allow`, `deny`, `once`) | Blocks unapproved dangerous commands | `tools/approval.py` |
| 12 | MCP Client | `mcp_servers` stdio/SSE/HTTP | Connects to external Model Context Protocol servers and registers tools dynamically | Config dict, server transport | Dynamic `mcp-*` toolsets in registry | Recycles idle stdio; caps output at 2,000,000 chars | `tools/mcp_tool.py` |

### Edge Cases Observed
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | `ToolRegistry.register` | Plugin attempts to register existing tool name without `override=True` | Registration is rejected with error log; existing tool preserved. |
| 2 | `ToolRegistry.register` | Scoped plugin attempts to override global tool without config opt-in | Raises `PermissionError` (requires `allow_tool_override: true`). |
| 3 | `check_fn` probing | Docker daemon times out during `check_terminal_requirements` | `_check_fn_cached` serves last-known True for 60s grace period to avoid flapping. |
| 4 | Tool Dispatch | Handler returns arbitrary Python object (e.g. integer or custom class) | `_normalize_handler_result` intercepts and returns structured `tool_result_contract` error. |
| 5 | Tool Dispatch | Tool handler raises unhandled exception with stack trace | Catches exception, sanitizes CDATA/fences, and wraps into `{"error": ...}` JSON. |
| 6 | Subagent Spawning | Child agent attempts to call `delegate_task`, `clarify`, or `memory` | Stripped from schema via `DELEGATE_BLOCKED_TOOLS`; execution blocked. |
| 7 | Subagent Execution | Child agent runs dangerous bash command | `_subagent_auto_deny` returns "deny" immediately, avoiding deadlock on parent TUI stdin. |
| 8 | Prompt Caching | Mid-conversation tool set mutation or system prompt edit | Invalidates cache prefix, multiplying prompt token costs; strictly prohibited. |
| 9 | Prompt Caching | LiteLLM OpenAI-wire proxy route | Part-level `cache_control` markers on `role: tool` are stripped to prevent HTTP 400. |
| 10 | Skill View | `skill_view("arxiv", "../../../etc/passwd")` | Path traversal guard intercepts and rejects with `tool_error`. |
| 11 | Environment Execution | Command produces 50MB of raw continuous stdout | `_BoundedOutputCollector` keeps 40/60 head-tail window and spills to disk up to 5MB cap. |
| 12 | Surface Gating | Electron desktop tool enabled via process env var `HERMES_DESKTOP=1` | Silent failure when connecting over SSH or web URL; must be gated on session source. |

---

## 3. Full Capability Comparison Matrix: Hermes Runtime vs H9 Requirements

| Architectural Dimension | Harness 9 Current (Milestone 1 Adapter) | Hermes Agent Native Runtime | Target H9 Refactored Direct Integration |
|---|---|---|---|
| **Execution Model** | Monolithic batch execution (`Pipeline.run()`) inside a single blocking tool call (`generate_video_from_brief`). | Reactive agent loop (`AIAgent.run_conversation()`), streaming turn-by-turn with model tool calling. | Native Hermes Agent loop drives the 17-state lifecycle turn-by-turn using modular tools and skills. |
| **Tool Surface** | 3 coarse service-gated tools (`generate_video_from_brief`, `inspect_production_state`, `evaluate_content_quality`). | Fine-grained, granular tool registry with dynamic discovery, validation, and middleware hooks. | 4 native H9 domain tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) registered in Hermes registry. |
| **Skill Framework** | Static internal stage modules; no runtime skill abstraction. | Progressive disclosure (`skills_list`, `skill_view`), YAML frontmatter, `SKILL.md` format. | Native Hermes skills: `skills/h9-research/`, `skills/h9-content-planning/`, `skills/h9-production/`, `skills/h9-hyperframes/`. |
| **Model & Provider Routing** | Direct LLM client instantiation or offline procedural mock; no runtime provider abstraction. | Pluggable provider adapters (Anthropic, Gemini, OpenAI, Bedrock, Vertex, Codex) with auxiliary clients. | Logical capability roles (`fast_inference`, `reasoning_deep`, `creative_synthesis`, `voice_synthesis`) routed via Hermes providers. |
| **Prompt Caching** | Fixed tool schema; no token-level cache coordination. | Sacred 4-breakpoint prompt caching with stable system prefix and strict message role alternation. | Byte-stable system prompt, immutable past messages, static tool schemas, and zero mid-loop injections. |
| **Memory Architecture** | Independent `src/creator/memory.py` models with standalone retention curves & negative memory. | `MemoryManager` orchestrating `MemoryProvider` plugins, plus SQLite `SessionDB` with FTS5 search. | Integrated `H9CreatorMemoryProvider` providing system prompt blocks, prefetch, and sync without parallel DB. |
| **Subagent Delegation** | Monolithic in-process multi-threading or sequential execution. | Isolated child `AIAgent` instances (`delegate_task`) with bounded iterations, fresh history, and auto-deny safety. | Multi-source research synthesis delegated to isolated Hermes subagent returning a typed `ResearchDossier`. |
| **Sandboxing & Subprocess** | Local subprocess calls to `ffmpeg` and local filesystem sandbox (`HermesSessionSandbox`). | Pluggable execution environments (`BaseEnvironment`: Local, Docker, Modal, Singularity, SSH, Daytona). | Subprocess execution (HyperFrames compiler, FFmpeg) routed through Hermes `BaseEnvironment` abstraction. |
| **Permissions & Security** | Cryptographic capability tokens (`CapabilityToken`) with HMAC-SHA256 signatures. | Interactive & async dangerous command approvals, session allowlists, and execution middleware. | Unified security boundary: capability tokens checked by Hermes tool handlers and execution middleware. |
| **MCP Integration** | No MCP client or server capabilities in H9 core. | Full MCP client (`tools/mcp_tool.py`) supporting stdio, SSE, and Streamable HTTP transports. | H9 operations can discover, bind, and execute external tools exposed through Hermes MCP catalog. |

---

## 4. Exact Hermes Extension Points and APIs

### 4.1 Tool Registration & Dispatch APIs (`tools/registry.py`, `model_tools.py`)
Hermes registers tools at module import time into the singleton `tools.registry.registry`:

```python
from tools.registry import registry, tool_error, tool_result

# Tool Handler Signature
def handle_h9_research(args: dict, **kwargs) -> str:
    task_id = kwargs.get("task_id")
    session_id = kwargs.get("session_id")
    topic = args.get("topic")
    # Execute research operation...
    return tool_result(dossier_data)

# Schema Definition (OpenAI-compatible)
H9_RESEARCH_SCHEMA = {
    "name": "h9_research",
    "description": "Synthesize multi-source research into a structured ResearchDossier.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Subject of research"},
            "focus_areas": {"type": "array", "items": {"type": "string"}},
            "offline": {"type": "boolean", "default": True}
        },
        "required": ["topic"]
    }
}

# Registration Call
registry.register(
    name="h9_research",
    toolset="harness9",
    schema=H9_RESEARCH_SCHEMA,
    handler=handle_h9_research,
    check_fn=check_harness9_available,  # TTL-cached 30s availability probe
    description="Synthesize multi-source research into a structured ResearchDossier.",
    emoji="🔬",
    is_async=False
)
```

**Key Invariants:**
- `name` must be unique across toolsets unless `override=True` with operator authorization.
- `handler` must return a string (JSON formatted) or a dictionary with `_multimodal: True`.
- `check_fn` must be a zero-argument callable returning `bool`. Results are TTL-cached for 30s with a 60s failure grace window.
- Surface gating must be handled via toolset inclusion (`enabled_toolsets`), never via global process environment variables.

### 4.2 Skill Discovery and Progressive Disclosure APIs (`tools/skills_tool.py`)
Hermes discovers skills by scanning:
1. `~/.hermes/skills/` (user active profile skills)
2. Bundled `skills/` directory (shipped with repo)
3. Project-local `.hermes/skills/` or `.agents/skills/`
4. Configured `skills.external_dirs` in `config.yaml`

**SKILL.md Specification:**
```yaml
---
name: h9-research
description: "Autonomous multi-source research and fact synthesis for video production."
version: 1.0.0
author: Harness 9
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [curl]
metadata:
  hermes:
    tags: [video, research, fact-checking, harness9]
    related_skills: [h9-content-planning, h9-production]
---

# H9 Research Skill
Instructions for conducting multi-source research...
```

**Progressive Disclosure API:**
- `skills_list()`: Returns metadata (`name`, `description`, `platforms`) for system prompt index.
- `skill_view(skill_name: str, subpath: Optional[str] = None)`: Retrieves the full `SKILL.md` or a supporting reference/template file.

### 4.3 Provider & Model Routing APIs (`agent/`, `agent/prompt_caching.py`)
Hermes routes model calls through `agent_runtime_helpers.py` and `chat_completion_helpers.py`:
- Supported providers: `anthropic`, `gemini`, `bedrock`, `vertex`, `codex_responses`, and standard OpenAI-compatible endpoints (`openrouter`, `ollama`, `vllm`, `deepseek`, etc.).
- Auxiliary calls (summarization, reflection, review) use `agent.auxiliary_client.AuxiliaryClient`, avoiding polluting main conversation state.
- Prompt caching is governed by `agent.prompt_caching.PromptCachePlan`:
  - Breakpoint 1: Stable system prompt prefix (`DEFAULT_AGENT_IDENTITY`).
  - Breakpoint 2: End of system prompt and tool definitions.
  - Breakpoints 3 & 4: Last two non-system messages in conversation history.

### 4.4 Memory & Persistence APIs (`agent/memory_manager.py`, `agent/memory_provider.py`)
To integrate creator memory without parallel persistence, H9 implements `MemoryProvider`:

```python
from agent.memory_provider import MemoryProvider, RecallStatus

class H9CreatorMemoryProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return "h9_creator_memory"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        self.session_id = session_id
        self.hermes_home = kwargs.get("hermes_home")

    def system_prompt_block(self) -> str:
        # Returns formatted Creator DNA / Brand Constitution
        return "# Creator DNA & Preferences\n..."

    def prefetch(self, query: str) -> Optional[str]:
        # Semantic search over past retention curves / negative memories
        return "Relevant creator guidelines for this topic..."

    def sync_turn(self, user_msg: str, assistant_msg: str) -> None:
        # Asynchronously capture learning candidates or negative signals
        pass

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    def handle_tool_call(self, name: str, args: Dict[str, Any], **kwargs) -> Any:
        raise NotImplementedError

    def shutdown(self) -> None:
        pass
```

### 4.5 Subagent Delegation APIs (`tools/delegate_tool.py`)
Hermes executes subagents via `tools.delegate_tool.delegate_task`:
- Single subagent: `delegate_task(task="Research quantum computing", goal="Generate ResearchDossier", ...)`
- Batch parallel subagents: `delegate_task(tasks=[{"task": "Source A", "goal": "..."}, {"task": "Source B", "goal": "..."}])`
- Execution guarantees:
  - Child runs in a fresh `AIAgent` instance with empty conversation history.
  - Child runs under isolated `child_task_id = f"subagent_{uuid.uuid4().hex[:8]}"`.
  - Dangerous commands are automatically denied via `_subagent_auto_deny` unless explicitly configured.
  - Intermediate scratchpad turns are discarded; only the final summary string is returned to parent context.

### 4.6 Sandbox & Environment Execution APIs (`tools/environments/base.py`)
Hermes abstracts command execution behind `BaseEnvironment`:
- `BaseEnvironment.execute_command(cmd, timeout=300, cwd=None)`
- Captures streaming output via `_BoundedOutputCollector` (retains 40/60 head-tail window; spills to disk up to 5MB).
- Backends: `LocalEnvironment`, `DockerEnvironment`, `ModalEnvironment`, `SingularityEnvironment`, `SSHEnvironment`.
- HyperFrames rendering subprocesses must be invoked via `BaseEnvironment.execute_command()` rather than direct `subprocess.run()`.

---

## 5. Formal Interface Specifications for `src/h9_runtime/`

To completely decouple Harness 9 domain services from Hermes internal implementation details, the following clean runtime interface abstractions are formally specified in `src/h9_runtime/`.

### 5.1 Architecture Overview of `src/h9_runtime/`

```
src/h9_runtime/
├── __init__.py           # Unified exports of runtime interfaces and contracts
├── agent.py              # AgentRuntime (agent lifecycle, subagent delegation, session state)
├── skill.py              # SkillRuntime (discovery, loading, instruction management)
├── tool.py               # ToolRuntime (tool registration, schema generation, dispatch)
├── model.py              # ModelRuntime (logical capability roles, provider inference)
├── memory.py             # MemoryRuntime (creator DNA, project memory, prefetch & sync)
├── execution.py          # ExecutionRuntime (sandboxed command execution, filesystem, timeouts)
├── content.py            # ContentRuntime (end-to-end production, IR compilation, rendering)
└── bridge.py             # HermesCapabilityBridge (concrete implementation binding to Hermes)
```

---

### 5.2 `AgentRuntime` (`src/h9_runtime/agent.py`)

```python
"""AgentRuntime protocol defining agent lifecycle, session management, and subagent delegation."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class SubagentStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class SubagentResult:
    """Outcome of a delegated subagent execution."""
    subagent_id: str
    status: SubagentStatus
    output: str
    structured_data: Optional[Dict[str, Any]] = None
    iterations_used: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


@dataclass(frozen=True)
class SessionState:
    """Current state of an agent execution session."""
    session_id: str
    current_state: str
    active_tools: List[str]
    iteration_count: int
    max_iterations: int
    is_interrupted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class AgentRuntime(Protocol):
    """Core runtime interface for agent conversation loops and subagent delegation."""

    def create_session(
        self,
        session_id: str,
        role: str = "orchestrator",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        """Initialize and configure an agent session context."""
        ...

    def delegate_subagent(
        self,
        parent_session_id: str,
        goal: str,
        role: str,
        context: Dict[str, Any],
        allowed_toolsets: Optional[List[str]] = None,
        max_iterations: int = 30,
        timeout_seconds: float = 300.0,
    ) -> SubagentResult:
        """Spawn an isolated child agent to complete a focused subtask."""
        ...

    def interrupt_session(self, session_id: str, reason: str = "user_interrupt") -> bool:
        """Request immediate interruption of a running agent session."""
        ...

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Retrieve live state and telemetry for a session."""
        ...
```

---

### 5.3 `SkillRuntime` (`src/h9_runtime/skill.py`)

```python
"""SkillRuntime protocol defining skill discovery, metadata extraction, and instruction loading."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable


@dataclass(frozen=True)
class SkillMetadata:
    """Progressive disclosure Tier 1 skill metadata."""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Harness 9"
    platforms: List[str] = field(default_factory=lambda: ["linux", "macos", "windows"])
    tags: List[str] = field(default_factory=list)
    skill_dir: Optional[Path] = None


@runtime_checkable
class SkillRuntime(Protocol):
    """Runtime interface for managing and loading agent skills."""

    def discover_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """Discover available skills matching category or platform."""
        ...

    def load_skill_instructions(self, skill_name: str) -> str:
        """Retrieve full Tier 2 instruction content (SKILL.md) for a skill."""
        ...

    def load_skill_resource(
        self,
        skill_name: str,
        relative_path: str,
    ) -> Union[str, bytes]:
        """Retrieve Tier 3 supporting reference, template, or script."""
        ...

    def build_system_prompt_index(self) -> str:
        """Render a byte-stable compact skills index table for system prompt injection."""
        ...
```

---

### 5.4 `ToolRuntime` (`src/h9_runtime/tool.py`)

```python
"""ToolRuntime protocol defining tool registration, OpenAI schema generation, and invocation."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Union, runtime_checkable


@dataclass(frozen=True)
class ToolDefinition:
    """Registration specification for a runtime tool."""
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
    """Execution context supplied during tool dispatch."""
    session_id: str
    task_id: str
    tool_call_id: Optional[str] = None
    turn_id: Optional[str] = None
    capability_token: Optional[str] = None


@runtime_checkable
class ToolRuntime(Protocol):
    """Runtime interface for tool registration, schemas, and execution dispatch."""

    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a model tool into the central registry."""
        ...

    def get_tool_schemas(
        self,
        enabled_toolsets: Optional[List[str]] = None,
        disabled_toolsets: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate filtered OpenAI-compatible tool schemas for LLM inference."""
        ...

    def dispatch_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolInvocationContext,
    ) -> str:
        """Dispatch and execute a tool handler by name."""
        ...

    def is_toolset_available(self, toolset: str) -> bool:
        """Check if at least one tool in a toolset satisfies its availability check."""
        ...
```

---

### 5.5 `ModelRuntime` (`src/h9_runtime/model.py`)

```python
"""ModelRuntime protocol defining logical capability routing, provider dispatch, and budgeting."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Protocol, Type, TypeVar, runtime_checkable
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class CapabilityRole(str, Enum):
    FAST_INFERENCE = "fast_inference"          # Research queries, classification, filtering
    REASONING_DEEP = "reasoning_deep"          # Multi-angle editorial analysis, verification
    CREATIVE_SYNTHESIS = "creative_synthesis"  # Scriptwriting, hook generation, storyboarding
    VOICE_SYNTHESIS = "voice_synthesis"        # Text-to-speech narration generation
    VISION_ANALYSIS = "vision_analysis"        # Visual asset quality verification, framing


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


@dataclass(frozen=True)
class BudgetStatus:
    """Current iteration and token spend tracking."""
    session_id: str
    tokens_consumed: int
    cost_usd: float
    budget_limit_usd: Optional[float] = None
    remaining_budget_usd: Optional[float] = None


@runtime_checkable
class ModelRuntime(Protocol):
    """Runtime interface for provider-independent model execution by capability role."""

    def invoke_capability(
        self,
        role: CapabilityRole,
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """Invoke model inference mapped to a logical capability role."""
        ...

    def stream_capability(
        self,
        role: CapabilityRole,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """Stream token responses from a capability role."""
        ...

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text snippet."""
        ...

    def get_budget_status(self, session_id: str) -> BudgetStatus:
        """Retrieve token expenditure and budget status for a session."""
        ...
```

---

### 5.6 `MemoryRuntime` (`src/h9_runtime/memory.py`)

```python
"""MemoryRuntime protocol defining Creator DNA, project persistence, and memory sync."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from src.models.contracts import CreatorProfile, ContentBrief, LearningCandidate


@dataclass(frozen=True)
class MemoryRecallItem:
    """Retrieved memory item matching a semantic query."""
    source: str
    category: str
    content: str
    score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class MemoryRuntime(Protocol):
    """Runtime interface for Creator DNA, project memory, and persistence."""

    def get_creator_profile(self, creator_id: str) -> Optional[CreatorProfile]:
        """Retrieve Creator DNA profile (Brand Constitution, Preferences)."""
        ...

    def save_creator_profile(self, profile: CreatorProfile) -> None:
        """Persist updated Creator DNA profile."""
        ...

    def recall_context(
        self,
        query: str,
        creator_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryRecallItem]:
        """Perform semantic retrieval across creator memory and historical production patterns."""
        ...

    def record_production_telemetry(
        self,
        project_id: str,
        metrics: Dict[str, Any],
        learning_candidates: Optional[List[LearningCandidate]] = None,
    ) -> None:
        """Record completed production metrics, retention curves, and learning candidates."""
        ...

    def render_system_prompt_block(self, creator_id: Optional[str] = None) -> str:
        """Generate static creator instructions for system prompt injection."""
        ...
```

---

### 5.7 `ExecutionRuntime` (`src/h9_runtime/execution.py`)

```python
"""ExecutionRuntime protocol defining sandboxed command execution, path confinement, and file I/O."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable


@dataclass(frozen=True)
class ExecutionResult:
    """Outcome of a sandboxed command execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


@runtime_checkable
class ExecutionRuntime(Protocol):
    """Runtime interface for sandbox-isolated shell and filesystem operations."""

    def execute_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        timeout_seconds: float = 300.0,
        env_vars: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a shell command within the configured sandbox environment."""
        ...

    def validate_path(self, target_path: Union[str, Path], session_id: str) -> Path:
        """Validate and resolve a path against session sandbox confinement boundaries."""
        ...

    def read_file(self, path: Union[str, Path], session_id: Optional[str] = None) -> str:
        """Read text content from a confined file."""
        ...

    def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        session_id: Optional[str] = None,
        atomic: bool = True,
    ) -> Path:
        """Write content to a confined file atomically."""
        ...
```

---

### 5.8 `ContentRuntime` (`src/h9_runtime/content.py`)

```python
"""ContentRuntime protocol defining high-level production operations and Production IR compilation."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable
from src.models.contracts import (
    ContentBrief,
    ContentOutline,
    EditorialAngle,
    EvaluationReport,
    PublishPackage,
    RenderArtifact,
    ResearchDossier,
    Script,
)


@dataclass(frozen=True)
class ProductionIR:
    """Typed Intermediate Representation connecting narrative planning to HyperFrames compiler."""
    project_id: str
    aspect_ratio: str
    duration_seconds: float
    fps: int
    timeline_blocks: List[Dict[str, Any]]
    audio_tracks: List[Dict[str, Any]]
    css_variables: Dict[str, str]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class ProductionResult:
    """Final output package of an end-to-end production run."""
    success: bool
    project_id: str
    session_id: str
    video_path: Optional[str]
    render_artifact: Optional[RenderArtifact]
    publish_package: Optional[PublishPackage]
    evaluation_report: Optional[EvaluationReport]
    state_history: List[Dict[str, Any]]
    elapsed_seconds: float
    error_message: Optional[str] = None


@runtime_checkable
class ContentRuntime(Protocol):
    """High-level content production interface connecting H9 domain logic with Hermes."""

    def plan_research(self, topic: str, session_id: str) -> ResearchDossier:
        """Execute multi-source research synthesis returning a validated dossier."""
        ...

    def evaluate_angles(self, dossier: ResearchDossier, creator_id: str) -> Tuple[List[EditorialAngle], EditorialAngle]:
        """Generate candidate angles and select winning angle via 9-dimension evaluation."""
        ...

    def generate_script(self, angle: EditorialAngle, dossier: ResearchDossier, creator_id: str) -> Script:
        """Generate structured script and storyboard beats."""
        ...

    def compile_production_ir(self, script: Script, workspace_dir: Path) -> ProductionIR:
        """Compile script and discovered assets into typed Production IR."""
        ...

    def render_video(self, ir: ProductionIR, output_dir: Path, session_id: str) -> RenderArtifact:
        """Render broadcast MP4 from Production IR using sandboxed execution."""
        ...

    def run_full_production(self, brief: ContentBrief, session_id: str) -> ProductionResult:
        """Execute full 17-state autonomous production pipeline."""
        ...
```

---

## 6. Critical Architectural Constraints

In accordance with `AGENTS.md`, any refactoring of Harness 9 to run through the Hermes runtime MUST uphold the following inviolable design constraints:

### 6.1 Sacred Per-Conversation Prompt Caching
1. **Byte-Stable System Prompt:** The system prompt (including the skills index and creator brand constitution) must remain identical from turn 0 to turn N within a session. Dynamic per-turn state (like current timestamp or live CPU usage) must NEVER be appended to the system prompt.
2. **Immutable History:** Past conversation messages must never be edited, pruned (except during explicit context compression), or swapped.
3. **Static Tool Schemas:** The JSON schemas of all registered tools must be static and immutable throughout the conversation. Mid-turn tool addition or schema mutation invalidates provider cache prefixes and multiplies token costs by up to 10x.
4. **Strict Role Alternation:** Conversation turns must strictly alternate:
   $$\text{user} \longrightarrow \text{assistant (tool\_calls)} \longrightarrow \text{tool (tool\_results)} \longrightarrow \text{assistant}$$
   Never insert consecutive assistant turns, never inject synthetic user messages mid-turn loop, and never skip tool result messages.

### 6.2 Narrow Core Waist & The Footprint Ladder
- Every tool added to `_HERMES_CORE_TOOLS` is sent to the LLM on **every single API call** across CLI, messaging platforms, and gateways.
- Harness 9 tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) must live on **Rung 3** of the Footprint Ladder: **Service-Gated Named Toolset** (`harness9`).
- They are enabled explicitly when requested (`enabled_toolsets=["harness9"]`), ensuring zero token overhead for general-purpose users who do not produce video.

### 6.3 Surface Capability vs Process Environment Gating
- Capabilities that depend on client rendering (e.g. preview windows, interactive timeline scrubbing) must be gated on **Session Source**, never on process environment variables like `HERMES_DESKTOP=1`.
- The backend process may be running in the cloud or over SSH while the client Electron GUI connects remotely. Environment variable checks are blind to this topology.
- Availability must resolve from the session's platform hint (`session.platform == "desktop_gui"`), handled via `_load_enabled_toolsets()`.

### 6.4 Non-Secret Configuration Hygiene
- `.env` files are reserved strictly for secret credentials (e.g., API keys, auth tokens).
- All behavioral settings, timeouts, quality presets, and feature flags must be placed in `config.yaml` (under a dedicated `harness9:` namespace). No new `HERMES_*` environment variables may be introduced for non-secret configuration.

---

## 7. Next Implementation Steps for Teamwork Orchestrator

1. **Step 1 (Branch Initialization):** Verify work is isolated on branch `dev`.
2. **Step 2 (Runtime Boundary Interfaces):** Implement `src/h9_runtime/` protocols (`agent.py`, `skill.py`, `tool.py`, `model.py`, `memory.py`, `execution.py`, `content.py`) and concrete adapter bridge `src/h9_runtime/bridge.py`.
3. **Step 3 (Native Model Tools):** Create `tools/h9_tools.py` registering `h9.research`, `h9.discover_assets`, `h9.generate_script`, and `h9.render` into `tools/registry.py` under toolset `harness9`.
4. **Step 4 (Native Hermes Skills):** Create `skills/h9-research/`, `skills/h9-content-planning/`, `skills/h9-production/`, and `skills/h9-hyperframes/` containing compliant `SKILL.md` documents.
5. **Step 5 (Production IR Seam):** Introduce `src/models/ir.py` defining `ProductionIR` and connecting `ScriptwritingPipeline` to `HyperFramesGenerator`.
6. **Step 6 (Subagent Research & Memory):** Wire `h9.research` to invoke `delegate_task` with isolated subagent parameters, and implement `H9CreatorMemoryProvider` registered with `MemoryManager`.
7. **Step 7 (Sandbox & Subprocess):** Refactor `HyperFramesRenderer` to execute `ffmpeg` and capture pipelines via `ExecutionRuntime` (`BaseEnvironment`).
8. **Step 8 (Verification Suite):** Implement integration test suite verifying the 8 acceptance dimensions (`tests/test_h9_hermes_runtime_integration.py`).
9. **Step 9 (Audit Documentation):** Author final integration audit report in `docs/architecture/hermes-h9-integration-audit.md`.
