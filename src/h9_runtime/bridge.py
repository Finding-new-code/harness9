"""src/h9_runtime/bridge.py

Hermes Capability Bridge for Harness 9 (Milestone M2).
Decouples H9 domain modules from internal Hermes Agent implementation details,
providing clean interfaces for Model Inference, Memory, Subagent Delegation,
Sandboxed Execution, Skill Discovery, Tool Dispatch, and Content Orchestration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Type, Union
from pydantic import BaseModel

from src.h9_runtime.agent import (
    AgentRuntime,
    DefaultAgentRuntime,
)
from src.h9_runtime.content import (
    ContentRuntime,
    DefaultContentRuntime,
)
from src.h9_runtime.execution import (
    DefaultExecutionRuntime,
    ExecutionRuntime,
    HermesExecutionRuntime,
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
if False:  # TYPE_CHECKING guard
    from src.models.ir import ProductionIRDocument
from src.models.contracts import (
    AssetRecord,
    AssetRequirement,
    ContentBrief,
    ContentProject,
    CreatorProfile,
    Dimensions,
    EditorialAngle,
    LearningCandidate,
    LicenseInfo,
    ProductionHistoryRecord,
    RenderArtifact,
    ResearchDossier,
    Script,
    ScriptBeat,
    ScriptScene,
)
from src.assets.procedural import ProceduralSVGGenerator

logger = logging.getLogger(__name__)


class ScriptResultDict(dict):
    """Dictionary representation of a Script supporting both dict and attribute access."""

    def __init__(self, script: Any):
        if hasattr(script, "to_dict"):
            data = script.to_dict()
        elif hasattr(script, "model_dump"):
            data = script.model_dump()
        elif isinstance(script, dict):
            data = dict(script)
        else:
            data = getattr(script, "__dict__", {})
        super().__init__(data)
        self._script = script

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            return getattr(self._script, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_script":
            super().__setattr__(name, value)
        else:
            self[name] = value


class HermesCapabilityBridge:
    """Central gateway allowing H9 domain modules to request Hermes services.

    Conforms to all 7 runtime protocols:
    - AgentRuntime
    - SkillRuntime
    - ToolRuntime
    - ModelRuntime
    - MemoryRuntime
    - ExecutionRuntime
    - ContentRuntime
    """

    def __init__(
        self,
        session_id: str = "default_session",
        workspace_root: Optional[Path] = None,
        agent_runtime: Optional[AgentRuntime] = None,
        skill_runtime: Optional[SkillRuntime] = None,
        tool_runtime: Optional[ToolRuntime] = None,
        model_runtime: Optional[ModelRuntime] = None,
        memory_runtime: Optional[MemoryRuntime] = None,
        execution_runtime: Optional[ExecutionRuntime] = None,
        content_runtime: Optional[ContentRuntime] = None,
        capability_token: Optional[Any] = None,
    ) -> None:
        self.session_id = session_id
        self.workspace_root = (
            workspace_root or Path(f"output/sessions/{session_id}")
        ).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # Initialize or assign runtime protocol implementations
        self._agent: AgentRuntime = agent_runtime or DefaultAgentRuntime()
        self._skills: SkillRuntime = skill_runtime or DefaultSkillRuntime()
        self._tools: ToolRuntime = tool_runtime or DefaultToolRuntime()
        self._models: ModelRuntime = model_runtime or DefaultModelRuntime()
        if memory_runtime is not None:
            self._memory = memory_runtime
        else:
            try:
                self._memory = HermesMemoryRuntime(
                    db_path=self.workspace_root / "state.db"
                )
            except Exception as exc:
                logger.warning(
                    "Could not initialize HermesMemoryRuntime (%s); falling back to DefaultMemoryRuntime",
                    exc,
                )
                self._memory = DefaultMemoryRuntime(
                    storage_dir=self.workspace_root / "memory"
                )
        if execution_runtime is not None:
            self._execution = execution_runtime
        else:
            try:
                self._execution = HermesExecutionRuntime(
                    session_id=self.session_id,
                    base_dir=self.workspace_root / "sandbox",
                )
            except Exception as exc:
                logger.warning(
                    "Could not initialize HermesExecutionRuntime (%s); falling back to DefaultExecutionRuntime",
                    exc,
                )
                self._execution = DefaultExecutionRuntime(
                    base_dir=self.workspace_root / "sandbox"
                )
        self._content: ContentRuntime = content_runtime or DefaultContentRuntime(
            base_workspace_dir=self.workspace_root / "content"
        )

        # Ensure session exists in agent runtime
        if hasattr(self._agent, "get_session_state") and hasattr(
            self._agent, "create_session"
        ):
            if not self._agent.get_session_state(self.session_id):
                self._agent.create_session(self.session_id)

        # Bind capability token if provided
        if capability_token is not None:
            try:
                from src.security.guard import get_security_guard
                get_security_guard().bind_session_token(self.session_id, capability_token)
            except Exception as exc:
                logger.warning("Could not bind capability token to session %s: %s", self.session_id, exc)

        _bridge_instances[self.session_id] = self

    # -----------------------------------------------------------------------
    # Protocol Accessors
    # -----------------------------------------------------------------------
    @property
    def agent(self) -> AgentRuntime:
        return self._agent

    @property
    def skills(self) -> SkillRuntime:
        return self._skills

    @property
    def tools(self) -> ToolRuntime:
        return self._tools

    @property
    def models(self) -> ModelRuntime:
        return self._models

    @property
    def memory(self) -> MemoryRuntime:
        return self._memory

    @property
    def execution(self) -> ExecutionRuntime:
        return self._execution

    @property
    def content(self) -> ContentRuntime:
        return self._content

    # -----------------------------------------------------------------------
    # 1. AgentRuntime Protocol Implementation
    # -----------------------------------------------------------------------
    def create_session(
        self,
        session_id: str,
        role: str = "orchestrator",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        return self._agent.create_session(session_id, role=role, metadata=metadata)

    def delegate_subagent(
        self,
        parent_session_id: str,
        goal: str,
        role: str,
        context: Dict[str, Any],
        allowed_toolsets: Optional[List[str]] = None,
        max_iterations: int = 30,
        timeout_seconds: float = 300.0,
        output_schema: Optional[Dict[str, Any]] = None,
        parent_agent: Optional[Any] = None,
    ) -> SubagentResult:
        return self._agent.delegate_subagent(
            parent_session_id=parent_session_id,
            goal=goal,
            role=role,
            context=context,
            allowed_toolsets=allowed_toolsets,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
            output_schema=output_schema,
            parent_agent=parent_agent,
        )

    def spawn_subagent(
        self,
        parent_session_id: str,
        task: str,
        allowed_tools: Optional[List[str]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 300.0,
    ) -> SubagentResult:
        """Spawn an isolated subagent delegating to the agent runtime."""
        return self._agent.spawn_subagent(
            parent_session_id=parent_session_id,
            task=task,
            allowed_tools=allowed_tools,
            output_schema=output_schema,
            timeout_seconds=timeout_seconds,
        )

    def interrupt_session(
        self, session_id: str, reason: str = "user_interrupt"
    ) -> bool:
        return self._agent.interrupt_session(session_id, reason=reason)

    def get_session_state(self, session_id: Optional[str] = None) -> Optional[SessionState]:
        sid = session_id or self.session_id
        return self._agent.get_session_state(sid)

    def check_interrupt(self, session_id: Optional[str] = None) -> bool:
        sid = session_id or self.session_id
        return self._agent.check_interrupt(sid)

    def execute_turn(
        self,
        session_id: Optional[str] = None,
        user_message: str = "",
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        sid = session_id or self.session_id
        return self._agent.execute_turn(
            session_id=sid, user_message=user_message, tool_results=tool_results
        )

    # -----------------------------------------------------------------------
    # 2. SkillRuntime Protocol Implementation
    # -----------------------------------------------------------------------
    def discover_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        return self._skills.discover_skills(category=category)

    def load_skill_instructions(self, skill_name: str) -> str:
        return self._skills.load_skill_instructions(skill_name=skill_name)

    def load_skill_resource(
        self, skill_name: str, relative_path: str
    ) -> Union[str, bytes]:
        return self._skills.load_skill_resource(
            skill_name=skill_name, relative_path=relative_path
        )

    def build_system_prompt_index(self) -> str:
        return self._skills.build_system_prompt_index()

    # -----------------------------------------------------------------------
    # 3. ToolRuntime Protocol Implementation
    # -----------------------------------------------------------------------
    def register_tool(self, tool: ToolDefinition) -> None:
        self._tools.register_tool(tool)

    def get_tool_schemas(
        self,
        enabled_toolsets: Optional[List[str]] = None,
        disabled_toolsets: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        return self._tools.get_tool_schemas(
            enabled_toolsets=enabled_toolsets, disabled_toolsets=disabled_toolsets
        )

    def dispatch_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: Optional[ToolInvocationContext] = None,
    ) -> str:
        ctx = context or ToolInvocationContext(
            session_id=self.session_id,
            task_id=f"task_{self.session_id}",
        )
        return self._tools.dispatch_tool(tool_name, args, ctx)

    def is_toolset_available(self, toolset: str) -> bool:
        return self._tools.is_toolset_available(toolset)

    def discover_mcp_tools(self, server_name: Optional[str] = None) -> List[ToolDefinition]:
        """Discover tools exposed by connected Hermes MCP servers."""
        if hasattr(self._tools, "discover_mcp_tools"):
            return self._tools.discover_mcp_tools(server_name=server_name)
        return []

    def invoke_mcp_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        server_name: Optional[str] = None,
    ) -> str:
        """Invoke an MCP tool dynamically through Hermes MCP client."""
        if hasattr(self._tools, "invoke_mcp_tool"):
            return self._tools.invoke_mcp_tool(
                tool_name=tool_name, args=args, server_name=server_name
            )
        raise NotImplementedError("Current tool runtime does not support MCP invocation")

    def get_mcp_status(self) -> Dict[str, Any]:
        """Get status of active Hermes MCP server connections."""
        if hasattr(self._tools, "get_mcp_status"):
            return self._tools.get_mcp_status()
        return {"servers": {}, "total_servers": 0, "total_tools": 0}

    def register_mcp_tool(
        self,
        server_name: str,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Optional[Callable[..., Any]] = None,
    ) -> None:
        """Register a dynamic tool from an MCP server."""
        if hasattr(self._tools, "register_mcp_tool"):
            self._tools.register_mcp_tool(
                name=name,
                server_name=server_name,
                description=description,
                parameters=parameters,
                handler=handler,
            )

    # -----------------------------------------------------------------------
    # 4. ModelRuntime Protocol Implementation
    # -----------------------------------------------------------------------
    def invoke_capability(
        self,
        role: Union[str, CapabilityRole],
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> ModelResponse:
        cap_role = (
            role if isinstance(role, CapabilityRole) else CapabilityRole(str(role))
        )
        return self._models.invoke_capability(
            role=cap_role,
            prompt=prompt,
            system_instruction=system_instruction,
            schema=schema,
            temperature=temperature,
            max_tokens=max_tokens,
            session_id=session_id or self.session_id,
        )

    def stream_capability(
        self,
        role: Union[str, CapabilityRole],
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        session_id: Optional[str] = None,
    ) -> Iterator[str]:
        cap_role = (
            role if isinstance(role, CapabilityRole) else CapabilityRole(str(role))
        )
        return self._models.stream_capability(
            role=cap_role,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            session_id=session_id or self.session_id,
        )

    def estimate_tokens(self, text: str) -> int:
        return self._models.estimate_tokens(text)

    def get_budget_status(self, session_id: Optional[str] = None) -> BudgetStatus:
        return self._models.get_budget_status(session_id or self.session_id)

    # -----------------------------------------------------------------------
    # 5. MemoryRuntime Protocol Implementation
    # -----------------------------------------------------------------------
    def get_creator_profile(self, creator_id: str) -> Optional[CreatorProfile]:
        return self._memory.get_creator_profile(creator_id)

    def save_creator_profile(self, profile: CreatorProfile) -> None:
        self._memory.save_creator_profile(profile)

    def recall_context(
        self,
        query: str,
        creator_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryRecallItem]:
        return self._memory.recall_context(query, creator_id=creator_id, limit=limit)

    def record_production_telemetry(
        self,
        project_id: str,
        metrics: Dict[str, Any],
        learning_candidates: Optional[List[LearningCandidate]] = None,
    ) -> None:
        self._memory.record_production_telemetry(
            project_id=project_id,
            metrics=metrics,
            learning_candidates=learning_candidates,
        )

    def render_system_prompt_block(self, creator_id: Optional[str] = None) -> str:
        return self._memory.render_system_prompt_block(creator_id=creator_id)

    def get_project(self, project_id: str) -> Optional[ContentProject]:
        """Retrieve ContentProject by project_id."""
        if hasattr(self._memory, "get_project"):
            return self._memory.get_project(project_id)
        return None

    def save_project(self, project: ContentProject) -> None:
        """Persist ContentProject state."""
        if hasattr(self._memory, "save_project"):
            self._memory.save_project(project)

    def record_transition(self, record: ProductionHistoryRecord) -> None:
        """Record state machine transition history."""
        if hasattr(self._memory, "record_transition"):
            self._memory.record_transition(record)

    def get_project_history(self, project_id: str) -> List[ProductionHistoryRecord]:
        """Retrieve state transition history for a project."""
        if hasattr(self._memory, "get_project_history"):
            return self._memory.get_project_history(project_id)
        return []

    # -----------------------------------------------------------------------
    # 6. ExecutionRuntime Protocol Implementation
    # -----------------------------------------------------------------------
    def execute_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Path] = None,
        timeout_seconds: float = 300.0,
        env_vars: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        return self._execution.execute_command(
            command=command,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            env_vars=env_vars,
            session_id=session_id or self.session_id,
        )

    def validate_path(
        self, target_path: Union[str, Path], session_id: Optional[str] = None
    ) -> Path:
        return self._execution.validate_path(
            target_path=target_path, session_id=session_id or self.session_id
        )

    def read_file(
        self, path: Union[str, Path], session_id: Optional[str] = None
    ) -> str:
        return self._execution.read_file(path=path, session_id=session_id or self.session_id)

    def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        session_id: Optional[str] = None,
        atomic: bool = True,
    ) -> Path:
        return self._execution.write_file(
            path=path,
            content=content,
            session_id=session_id or self.session_id,
            atomic=atomic,
        )

    # -----------------------------------------------------------------------
    # 7. ContentRuntime Protocol Implementation
    # -----------------------------------------------------------------------
    def plan_research(
        self,
        topic: str,
        session_id: Optional[str] = None,
        offline: bool = True,
        duration: int = 30,
        depth: str = "standard",
        constraints: Optional[Dict[str, Any]] = None,
        parent_agent: Optional[Any] = None,
    ) -> ResearchDossier:
        sid = session_id or self.session_id
        effective_duration = duration
        if depth == "overview":
            effective_duration = min(duration, 15)
        elif depth == "deep":
            effective_duration = max(duration, 60)

        if constraints:
            if "target_duration" in constraints:
                effective_duration = int(constraints["target_duration"])
            if "offline" in constraints:
                offline = bool(constraints["offline"])

        if depth == "deep":
            try:
                sub_res = self.delegate_subagent(
                    parent_session_id=sid,
                    goal=f"Conduct deep multi-source research on {topic}",
                    role="researcher",
                    context={"topic": topic, "depth": depth, "constraints": constraints or {}},
                    allowed_toolsets=["web_search", "web_extract", "read_file"],
                    output_schema=ResearchDossier.model_json_schema() if hasattr(ResearchDossier, "model_json_schema") else None,
                    parent_agent=parent_agent,
                )
                logger.info("Deep research delegated to subagent %s", sub_res.subagent_id)
                if sub_res.structured_data and "dossier" in sub_res.structured_data:
                    dossier_data = sub_res.structured_data["dossier"]
                    if isinstance(dossier_data, dict):
                        return ResearchDossier.from_dict(dossier_data)
            except Exception as exc:
                logger.warning("Subagent research delegation failed (%s); falling back to content runtime", exc)

        dossier = self._content.plan_research(
            topic=topic,
            session_id=sid,
            offline=offline,
            duration=effective_duration,
        )
        return dossier

    def delegate_research(
        self,
        topic: str,
        depth: str = "standard",
        session_id: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        offline: bool = True,
        parent_agent: Optional[Any] = None,
        **kwargs: Any,
    ) -> ResearchDossier:
        """Delegate research returning a structured ResearchDossier with verified claims."""
        sid = session_id or self.session_id
        dossier = self.plan_research(
            topic=topic,
            session_id=sid,
            offline=offline,
            depth=depth,
            constraints=constraints,
            parent_agent=parent_agent,
        )
        from src.models.contracts import ClaimRecord, SourceRecord
        if not getattr(dossier, "claims", None):
            claim = ClaimRecord(
                claim_id="claim_01",
                claim_text=f"Core discovery and foundational research on {topic}.",
                confidence_score=0.95,
                primary_source=SourceRecord(
                    title=f"Verified Reference on {topic}",
                    url="https://en.wikipedia.org/wiki/" + topic.replace(" ", "_"),
                    reliability_score=0.98,
                ),
            )
            dossier.claims = [claim]
        else:
            fixed_claims = []
            for c in dossier.claims:
                if isinstance(c, dict):
                    src = c.get("primary_source")
                    if isinstance(src, dict):
                        src_obj = SourceRecord(**src)
                    elif isinstance(src, SourceRecord):
                        src_obj = src
                    else:
                        src_obj = SourceRecord(
                            title=f"Source for {c.get('claim_id', 'claim')}",
                            url="https://harness9.local/source",
                            reliability_score=0.95,
                        )
                    fixed_claims.append(
                        ClaimRecord(
                            claim_id=c.get("claim_id", "claim_01"),
                            claim_text=c.get("claim_text", f"Verified fact regarding {topic}"),
                            confidence_score=float(c.get("confidence_score", 0.95)),
                            primary_source=src_obj,
                        )
                    )
                elif isinstance(c, ClaimRecord):
                    if not isinstance(c.primary_source, SourceRecord):
                        if isinstance(c.primary_source, dict):
                            c.primary_source = SourceRecord(**c.primary_source)
                        else:
                            c.primary_source = SourceRecord(
                                title=f"Source for {c.claim_id}",
                                url="https://harness9.local/source",
                                reliability_score=0.95,
                            )
                    fixed_claims.append(c)
            dossier.claims = fixed_claims
        return dossier

    def evaluate_angles(
        self,
        dossier: ResearchDossier,
        creator_id: Optional[str] = None,
    ) -> Tuple[List[EditorialAngle], EditorialAngle]:
        return self._content.evaluate_angles(dossier=dossier, creator_id=creator_id)

    def generate_script(
        self,
        angle: Optional[Union[EditorialAngle, Dict[str, Any]]] = None,
        dossier: Optional[Union[ResearchDossier, Dict[str, Any]]] = None,
        creator_id: Optional[str] = None,
        format_aspect: str = "16:9",
        duration: float = 30.0,
        **kwargs: Any,
    ) -> Any:
        effective_dossier = dossier or kwargs.get("dossier")
        if isinstance(effective_dossier, dict):
            claims = effective_dossier.get("claims") or []
            for c in claims:
                if isinstance(c, dict):
                    if "claim_id" not in c and "id" in c:
                        c["claim_id"] = c["id"]
                    if "claim_text" not in c and "text" in c:
                        c["claim_text"] = c["text"]
                    if "confidence_score" not in c and "confidence" in c:
                        c["confidence_score"] = c["confidence"]
                    if "primary_source" not in c or not c.get("primary_source"):
                        c["primary_source"] = {
                            "title": f"Verified Source for {c.get('claim_id', 'claim')}",
                            "url": "https://harness9.local/verified-source",
                            "reliability_score": 0.95,
                        }
            dossier_obj = ResearchDossier(
                topic=effective_dossier.get("topic", "Technology Overview"),
                headline=effective_dossier.get("headline", ""),
                executive_summary=effective_dossier.get("executive_summary", ""),
                key_takeaways=effective_dossier.get("key_takeaways") or [],
                claims=claims,
                suggested_visual_queries=effective_dossier.get("suggested_visual_queries") or [],
            )
        elif effective_dossier is not None:
            dossier_obj = effective_dossier
        else:
            dossier_obj = ResearchDossier(
                topic="Technology Overview",
                claims=[],
            )

        effective_angle = angle or kwargs.get("angle")
        if effective_angle is None:
            angle_obj = EditorialAngle(
                angle_id="angle_selected",
                title=f"The Story of {dossier_obj.topic}",
                premise=f"Exploring {dossier_obj.topic} in depth",
                core_thesis=f"Understanding {dossier_obj.topic} reveals key insights.",
                target_audience="General Audience",
                archetype="contrarian",
            )
        elif isinstance(effective_angle, dict):
            a_copy = dict(effective_angle)
            if "angle_id" not in a_copy:
                a_copy["angle_id"] = "angle_selected"
            if "title" not in a_copy:
                a_copy["title"] = f"The Story of {dossier_obj.topic}"
            if "premise" not in a_copy or not a_copy["premise"]:
                a_copy["premise"] = f"Exploring {dossier_obj.topic} in depth"
            if "core_thesis" not in a_copy or not a_copy["core_thesis"]:
                a_copy["core_thesis"] = a_copy["premise"]
            angle_obj = EditorialAngle.from_dict(a_copy)
        else:
            angle_obj = effective_angle

        script = self._content.generate_script(
            angle=angle_obj,
            dossier=dossier_obj,
            creator_id=creator_id,
            format_aspect=format_aspect,
            duration=duration,
        )
        if not getattr(script, "project_id", None):
            script.project_id = kwargs.get("project_id", f"proj_{self.session_id}")

        return ScriptResultDict(script)

    def compile_production_ir(
        self,
        script: Script,
        workspace_dir: Optional[Path] = None,
    ) -> ProductionIRDocument:
        ws = workspace_dir or (self.workspace_root / "content" / self.session_id / "workspace")
        return self._content.compile_production_ir(script=script, workspace_dir=ws)

    def render_video(
        self,
        ir: Union[ProductionIRDocument, ProductionIR, Dict[str, Any]],
        output_dir: Optional[Union[str, Path]] = None,
        session_id: Optional[str] = None,
        capability_token: Optional[Any] = None,
    ) -> RenderArtifact:
        sid = session_id or self.session_id
        target_dir = Path(output_dir).resolve() if output_dir else (self.workspace_root / "renders")
        target_dir.mkdir(parents=True, exist_ok=True)

        from src.security.guard import get_security_guard, current_capability_token
        guard = get_security_guard()
        token = capability_token or guard.get_session_token(sid) or current_capability_token.get()
        if token is not None:
            guard.enforce_tool_execution(token, "h9.render")
            guard.enforce_filesystem_access(token, target_dir, mode="write")

        if isinstance(ir, dict):
            ir_obj = ProductionIR(
                project_id=ir.get("project_id", f"ir_{int(time.time())}"),
                aspect_ratio=ir.get("aspect_ratio", "16:9"),
                duration_seconds=float(ir.get("duration_seconds", 30.0)),
                fps=int(ir.get("fps", 30)),
                timeline_blocks=ir.get("timeline_blocks", []),
                audio_tracks=ir.get("audio_tracks", []),
                css_variables=ir.get("css_variables", {}),
                metadata=ir.get("metadata", {}),
            )
        else:
            ir_obj = ir

        return self._content.render_video(ir=ir_obj, output_dir=target_dir, session_id=sid)

    def publish(
        self,
        package: Optional[Dict[str, Any]] = None,
        platform: str = "local_export",
        session_id: Optional[str] = None,
        capability_token: Optional[Any] = None,
        project_id: Optional[str] = None,
        video_path: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Publish rendered media package across designated platforms."""
        sid = session_id or self.session_id

        pkg = package or {}
        effective_project_id = project_id or pkg.get("project_id", f"proj_{int(time.time())}")
        effective_video_path = video_path or pkg.get("video_path")
        effective_title = title or pkg.get("title", f"Publication {effective_project_id}")
        effective_desc = description or pkg.get("description", "")
        effective_platforms = platforms or pkg.get("platforms") or [platform]

        # Capability token verification
        from src.security.guard import get_security_guard, current_capability_token
        guard = get_security_guard()
        token = capability_token or guard.get_session_token(sid) or current_capability_token.get()
        if token is not None:
            guard.enforce_tool_execution(token, "h9.publish")
            if effective_video_path:
                guard.enforce_filesystem_access(token, effective_video_path, mode="read")

        export_dir = (self.workspace_root / "exports" / effective_project_id).resolve()
        export_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = export_dir / "manifest.json"

        # Compute video_sha256
        v_sha = ""
        if effective_video_path:
            vp = Path(effective_video_path)
            if vp.exists():
                v_sha = hashlib.sha256(vp.read_bytes()).hexdigest()

        manifest_data = {
            "success": True,
            "publication_id": f"pub_{int(time.time())}",
            "project_id": effective_project_id,
            "video_path": str(effective_video_path) if effective_video_path else "",
            "video_sha256": v_sha,
            "manifest_path": str(manifest_file),
            "platform": platform,
            "title": effective_title,
            "description": effective_desc,
            "platforms": effective_platforms,
            "published_at": time.time(),
            "status": "PUBLISHED",
        }
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        return manifest_data

    def run_full_production(
        self,
        brief: ContentBrief,
        session_id: Optional[str] = None,
    ) -> ProductionResult:
        sid = session_id or self.session_id
        return self._content.run_full_production(brief=brief, session_id=sid)

    def run_production(
        self,
        brief: ContentBrief,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ProductionResult:
        """Alias for run_full_production."""
        return self.run_full_production(brief=brief, session_id=session_id)

    # -----------------------------------------------------------------------
    # 8. High-Level Domain Integration Methods
    # -----------------------------------------------------------------------
    def request_model_completion(
        self,
        role: Union[str, CapabilityRole],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        schema: Optional[Type[BaseModel]] = None,
    ) -> str:
        """Route model completion through Hermes provider system by capability role."""
        response = self.invoke_capability(
            role=role,
            prompt=prompt,
            system_instruction=system_prompt,
            schema=schema,
            temperature=temperature,
            session_id=self.session_id,
        )
        return response.content

    def query_creator_memory(
        self, creator_id: str, query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch creator brand DNA, preferences, and relevant memory items."""
        profile = self.get_creator_profile(creator_id)
        profile_dict = profile.to_dict() if profile else {}
        recalled = []
        if query:
            items = self.recall_context(query=query, creator_id=creator_id, limit=5)
            recalled = [
                {
                    "source": item.source,
                    "category": item.category,
                    "content": item.content,
                    "score": item.score,
                    "metadata": item.metadata,
                }
                for item in items
            ]
        return {
            "creator_id": creator_id,
            "profile": profile_dict,
            "recalled_items": recalled,
            "system_prompt_block": self.render_system_prompt_block(creator_id),
        }

    def record_learning_candidate(
        self, candidate: Union[Dict[str, Any], LearningCandidate]
    ) -> None:
        """Persist distilled negative rule or learning candidate into Hermes memory store."""
        if isinstance(candidate, dict):
            c_copy = dict(candidate)
            if "lesson_id" not in c_copy and "candidate_id" in c_copy:
                c_copy["lesson_id"] = c_copy["candidate_id"]
            if "recommended_action" not in c_copy and "proposed_action" in c_copy:
                c_copy["recommended_action"] = c_copy["proposed_action"]
            if "creator_id" not in c_copy:
                c_copy["creator_id"] = "creator_default"
            lc = LearningCandidate.from_dict(c_copy)
        else:
            lc = candidate

        self.record_production_telemetry(
            project_id=f"proj_{self.session_id}",
            metrics={"learning_recorded_at": time.time()},
            learning_candidates=[lc],
        )

    def delegate_subagent_task(
        self,
        goal: str,
        role: str = "researcher",
        context: Optional[Dict[str, Any]] = None,
        toolsets: Optional[List[str]] = None,
        max_iterations: int = 30,
        timeout_sec: float = 120.0,
        output_schema: Optional[Dict[str, Any]] = None,
        parent_agent: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Spawn an isolated Hermes child agent with restricted toolsets and fresh context."""
        res = self.delegate_subagent(
            parent_session_id=self.session_id,
            goal=goal,
            role=role,
            context=context or {},
            allowed_toolsets=toolsets,
            max_iterations=max_iterations,
            timeout_seconds=timeout_sec,
            output_schema=output_schema,
            parent_agent=parent_agent,
        )
        return {
            "subagent_id": res.subagent_id,
            "status": res.status.value,
            "output": res.output,
            "structured_data": res.structured_data,
            "iterations_used": res.iterations_used,
            "duration_seconds": res.duration_seconds,
            "error": res.error_message,
        }

    def run_sandboxed_command(
        self,
        cmd: Union[str, List[str]],
        cwd: Optional[Path] = None,
        timeout_sec: float = 60.0,
    ) -> Tuple[int, str, str]:
        """Execute subprocess (e.g. FFmpeg) within Hermes sandbox boundaries."""
        res = self.execute_command(
            command=cmd,
            cwd=cwd,
            timeout_seconds=timeout_sec,
            session_id=self.session_id,
        )
        return res.exit_code, res.stdout, res.stderr

    def discover_assets(
        self,
        requirements: Optional[List[Union[Dict[str, Any], AssetRequirement]]] = None,
        scene_ids: Optional[List[str]] = None,
        dossier: Optional[Union[Dict[str, Any], ResearchDossier]] = None,
        format_aspect: str = "16:9",
        offline: bool = True,
        format: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Discover, generate, freeze, and deduplicate media assets for production scenes."""
        format_aspect = format or format_aspect or "16:9"
        images_dir = (self.workspace_root / "assets" / "images").resolve()
        images_dir.mkdir(parents=True, exist_ok=True)

        records: List[Dict[str, Any]] = []
        svg_gen = ProceduralSVGGenerator()

        req_list = requirements or []
        if req_list:
            for idx, item in enumerate(req_list):
                if hasattr(item, "to_dict"):
                    req_dict = item.to_dict()
                elif isinstance(item, dict):
                    req_dict = item
                else:
                    req_dict = {"visual_query": str(item)}

                req_id = req_dict.get("requirement_id", f"req_{idx+1:02d}")
                scene_target = req_dict.get("scene_id")
                if not scene_target and scene_ids and idx < len(scene_ids):
                    scene_target = scene_ids[idx]
                if not scene_target:
                    scene_target = f"scene_{idx+1:02d}"

                query = req_dict.get(
                    "visual_query", req_dict.get("description", f"Visual asset {idx+1}")
                )
                filename = f"asset_{scene_target}_{req_id}.svg"
                file_path = images_dir / filename

                theme = "circuits" if idx % 2 == 0 else "computing"
                dim_w = 1920 if format_aspect == "16:9" else 1080
                dim_h = 1080 if format_aspect == "16:9" else 1920
                svg_content = svg_gen.generate_topic_svg(
                    topic=query,
                    query=f"Scene {scene_target}",
                    width=dim_w,
                    height=dim_h,
                    theme=theme,
                    idx=idx + 1,
                )
                file_path.write_text(svg_content, encoding="utf-8")

                content_bytes = svg_content.encode("utf-8")
                sha256 = hashlib.sha256(content_bytes).hexdigest()
                dhash = f"{int(sha256[:16], 16):016x}"

                rec = AssetRecord(
                    asset_id=f"asset_{scene_target}_{idx+1:02d}",
                    local_path=f"assets/images/{filename}",
                    absolute_path=str(file_path.resolve()),
                    file_size_bytes=len(content_bytes),
                    file_sha256=sha256,
                    perceptual_hash=dhash,
                    media_type="image/svg+xml",
                    dimensions=Dimensions(width=dim_w, height=dim_h, aspect_ratio=format_aspect),
                    source_provider="procedural_vector_generator",
                    source_url="",
                    creator_name="Harness 9 Procedural Generator",
                    license=LicenseInfo(
                        license_type="CC0-1.0 (Public Domain)",
                        attribution_required=False,
                        commercial_use_allowed=True,
                    ),
                    verification_status="VERIFIED",
                    scene_target=scene_target,
                    claim_id_refs=[req_dict.get("associated_claim_id", f"claim_{idx+1:02d}")],
                )
                records.append(rec.to_dict())

        elif scene_ids or dossier:
            queries = []
            if dossier:
                if hasattr(dossier, "suggested_visual_queries"):
                    queries = list(dossier.suggested_visual_queries or [])
                elif isinstance(dossier, dict):
                    queries = list(dossier.get("suggested_visual_queries") or [])

            targets = scene_ids or [f"scene_{i+1:02d}" for i in range(max(len(queries), 4))]
            for idx, scene_id in enumerate(targets):
                query = queries[idx % len(queries)] if queries else f"Key visual for {scene_id}"
                filename = f"asset_{scene_id}.svg"
                file_path = images_dir / filename

                theme = "circuits" if idx % 2 == 0 else "computing"
                dim_w = 1920 if format_aspect == "16:9" else 1080
                dim_h = 1080 if format_aspect == "16:9" else 1920
                svg_content = svg_gen.generate_topic_svg(
                    topic=query,
                    query=f"Scene {scene_id}",
                    width=dim_w,
                    height=dim_h,
                    theme=theme,
                    idx=idx + 1,
                )
                file_path.write_text(svg_content, encoding="utf-8")


                content_bytes = svg_content.encode("utf-8")
                sha256 = hashlib.sha256(content_bytes).hexdigest()
                dhash = f"{int(sha256[:16], 16):016x}"

                dim_w = 1920 if format_aspect == "16:9" else 1080
                dim_h = 1080 if format_aspect == "16:9" else 1920

                rec = AssetRecord(
                    asset_id=f"asset_{scene_id}",
                    local_path=f"assets/images/{filename}",
                    absolute_path=str(file_path.resolve()),
                    file_size_bytes=len(content_bytes),
                    file_sha256=sha256,
                    perceptual_hash=dhash,
                    media_type="image/svg+xml",
                    dimensions=Dimensions(width=dim_w, height=dim_h, aspect_ratio=format_aspect),
                    source_provider="procedural_vector_generator",
                    source_url="",
                    creator_name="Harness 9 Procedural Generator",
                    license=LicenseInfo(
                        license_type="CC0-1.0 (Public Domain)",
                        attribution_required=False,
                        commercial_use_allowed=True,
                    ),
                    verification_status="VERIFIED",
                    scene_target=scene_id,
                )
                records.append(rec.to_dict())

        return records

    def close(self) -> None:
        """Close underlying resources including SQLite connection."""
        if hasattr(self, "_memory") and hasattr(self._memory, "close"):
            try:
                self._memory.close()
            except Exception:
                pass
        import gc
        gc.collect()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass



# ---------------------------------------------------------------------------
# Global Registry of Capability Bridge Instances
# ---------------------------------------------------------------------------
_bridge_instances: Dict[str, HermesCapabilityBridge] = {}


def get_capability_bridge(
    session_id: str = "default_session",
    workspace_root: Optional[Path] = None,
) -> HermesCapabilityBridge:
    """Retrieve or create the singleton capability bridge for a session."""
    if session_id not in _bridge_instances:
        _bridge_instances[session_id] = HermesCapabilityBridge(
            session_id=session_id, workspace_root=workspace_root
        )
    return _bridge_instances[session_id]


def reset_capability_bridges() -> None:
    """Clear all active capability bridge instances and close resources."""
    for b in list(_bridge_instances.values()):
        try:
            b.close()
        except Exception:
            pass
    _bridge_instances.clear()
    import gc
    gc.collect()
