"""src/h9_runtime/agent.py

AgentRuntime protocol and DefaultAgentRuntime implementation.
Governs agent session lifecycle, turn execution, telemetry,
and isolated subagent delegation.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import uuid
from urllib.parse import urlsplit

from src.h9_runtime.types import (
    SessionState,
    SubagentResult,
    SubagentStatus,
)

logger = logging.getLogger(__name__)


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
        output_schema: Optional[Dict[str, Any]] = None,
        parent_agent: Optional[Any] = None,
    ) -> SubagentResult:
        """Spawn an isolated child agent to complete a focused subtask."""
        ...

    def spawn_subagent(
        self,
        parent_session_id: str,
        task: str,
        allowed_tools: Optional[List[str]] = None,
        role: str = "researcher",
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 30,
        timeout_seconds: float = 300.0,
        output_schema: Optional[Dict[str, Any]] = None,
        parent_agent: Optional[Any] = None,
        **kwargs: Any,
    ) -> SubagentResult:
        """Spawn an isolated child agent to complete a focused task."""
        ...

    def interrupt_session(self, session_id: str, reason: str = "user_interrupt") -> bool:
        """Request immediate interruption of a running agent session."""
        ...

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Retrieve live state and telemetry for a session."""
        ...

    def check_interrupt(self, session_id: str) -> bool:
        """Check whether session has an active interrupt signal."""
        ...

    def execute_turn(
        self,
        session_id: str,
        user_message: str,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Execute a conversation turn while preserving prompt caching."""
        ...


class DefaultAgentRuntime:
    """Concrete implementation of AgentRuntime for the H9 runtime environment."""

    BLOCKED_TOOLS = frozenset(
        [
            "delegate_task",
            "clarify",
            "memory",
            "h9.render",
            "send_message",
            "cronjob",
        ]
    )
    DEFAULT_ALLOWED_TOOLS = ["web_search", "web_extract", "read_file"]

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}
        self._subagents: Dict[str, SubagentResult] = {}
        self._interrupt_flags: Dict[str, str] = {}

    def create_session(
        self,
        session_id: str,
        role: str = "orchestrator",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        """Initialize and configure an agent session context."""
        meta = metadata.copy() if metadata else {}
        meta["role"] = role
        meta["created_at"] = time.time()

        state = SessionState(
            session_id=session_id,
            current_state="CREATED",
            active_tools=[],
            iteration_count=0,
            max_iterations=50,
            is_interrupted=False,
            metadata=meta,
        )
        self._sessions[session_id] = state

        # Bind root capability token to session
        try:
            from src.security import ROLE_PERMISSIONS, create_root_token, get_security_guard

            guard = get_security_guard()
            if not guard.get_session_token(session_id):
                perms = ROLE_PERMISSIONS.get(role.lower(), {"*"})
                tok = create_root_token(
                    subject_id=session_id,
                    role=role,
                    workflow_id=f"wf_{session_id}",
                    allowed_tools=perms,
                )
                guard.bind_session_token(session_id, tok)
        except Exception as exc:
            logger.debug("Could not bind session token for %s: %s", session_id, exc)

        return state

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Retrieve live state and telemetry for a session."""
        return self._sessions.get(session_id)

    def interrupt_session(self, session_id: str, reason: str = "user_interrupt") -> bool:
        """Request immediate interruption of a running agent session."""
        if session_id in self._sessions:
            self._sessions[session_id].is_interrupted = True
            self._sessions[session_id].metadata["interrupt_reason"] = reason
            self._interrupt_flags[session_id] = reason
            return True
        return False

    def check_interrupt(self, session_id: str) -> bool:
        """Check whether session has an active interrupt signal."""
        state = self._sessions.get(session_id)
        if state and state.is_interrupted:
            return True
        return session_id in self._interrupt_flags

    def spawn_subagent(
        self,
        parent_session_id: str,
        task: str,
        allowed_tools: Optional[List[str]] = None,
        role: str = "researcher",
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 30,
        timeout_seconds: float = 300.0,
        output_schema: Optional[Dict[str, Any]] = None,
        parent_agent: Optional[Any] = None,
        **kwargs: Any,
    ) -> SubagentResult:
        """Spawn an isolated child agent to complete a focused subtask."""
        ctx = dict(context or {})
        ctx.setdefault("task", task)
        ctx.setdefault("topic", task)
        return self.delegate_subagent(
            parent_session_id=parent_session_id,
            goal=task,
            role=role,
            context=ctx,
            allowed_toolsets=allowed_tools,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
            output_schema=output_schema,
            parent_agent=parent_agent,
        )

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
        """Spawn an isolated child agent to complete a focused subtask.

        Enforces:
        1. Tool isolation: allows web_search, web_extract, read_file; strictly blocks
           delegate_task, clarify, memory, h9.render, send_message.
        2. Structured output contract: injects ResearchDossier schema for research tasks.
        3. Prompt caching preservation: parent context never records subagent turns.
        4. Reports unavailable delegation instead of synthesizing a success result.
        """
        subagent_id = f"subagent_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        # 1. Derive child capability token adhering to least privilege calculus:
        # P_child = P_parent ∩ P_role ∩ P_workflow
        effective_child_tools = None
        try:
            from src.security import (
                ROLE_PERMISSIONS,
                STAGE_PERMISSIONS,
                create_root_token,
                derive_child_token,
                get_security_guard,
            )

            guard = get_security_guard()
            parent_token = guard.get_session_token(parent_session_id)
            if parent_token is None:
                parent_token = create_root_token(
                    subject_id=parent_session_id,
                    role="orchestrator",
                    workflow_id=f"wf_{parent_session_id}",
                    allowed_tools={"*"},
                )
                guard.bind_session_token(parent_session_id, parent_token)

            child_role = role.lower()
            role_allowed = ROLE_PERMISSIONS.get(child_role, {"read_file", "web_search", "h9.research"})
            stage = context.get("workflow_stage") or "RESEARCH_IN_PROGRESS"
            stage_allowed = STAGE_PERMISSIONS.get(stage, {"*"})

            child_token = derive_child_token(
                parent_token=parent_token,
                child_subject_id=subagent_id,
                role_allowed_tools=role_allowed,
                workflow_allowed_tools=stage_allowed,
                child_role=role,
                workflow_stage=stage,
                ttl_seconds=timeout_seconds,
            )
            guard.bind_session_token(subagent_id, child_token)
            effective_child_tools = child_token.allowed_tools
        except Exception as exc:
            logger.debug("Capability token derivation fallback for subagent %s: %s", subagent_id, exc)

        # 1b. Sanitize toolsets (enforce principle of least privilege)
        if allowed_toolsets is not None:
            sanitized_tools = [t for t in allowed_toolsets if t not in self.BLOCKED_TOOLS]
        elif effective_child_tools is not None and "*" not in effective_child_tools:
            sanitized_tools = [t for t in sorted(list(effective_child_tools)) if t not in self.BLOCKED_TOOLS]
        else:
            sanitized_tools = self.DEFAULT_ALLOWED_TOOLS.copy()

        # 2. Inject structured output schema contract for research if not specified
        resolved_schema = output_schema
        if resolved_schema is None and ("research" in role.lower() or "research" in goal.lower()):
            try:
                from src.models.contracts import ResearchDossier
                resolved_schema = ResearchDossier.model_json_schema()
            except Exception as exc:
                logger.debug("Could not resolve ResearchDossier schema: %s", exc)

        # 3. Track subagent lineage on parent session without leaking message history
        parent_state = self._sessions.get(parent_session_id)
        if parent_state:
            parent_state.metadata.setdefault("child_subagents", []).append(subagent_id)

        topic = str(context.get("topic") or goal)
        research_task = "research" in role.lower() or "research" in goal.lower()
        structured_data: Dict[str, Any] = {
            "subagent_id": subagent_id,
            "parent_session_id": parent_session_id,
            "role": role,
            "goal": goal,
            "task": goal,
            "topic": topic,
            "allowed_tools": sanitized_tools,
            "output_schema_enforced": resolved_schema is not None,
        }
        output_text = ""
        error_message: Optional[str] = None
        iterations_used = 0
        result_status = SubagentStatus.FAILED

        # 4. Delegate only through a real Hermes parent agent. This runtime
        # must not report locally invented content as completed work.
        if parent_agent is not None:
            try:
                from tools.delegate_tool import delegate_task
                context_str = json.dumps(context) if isinstance(context, dict) else str(context)
                raw_delegation = delegate_task(
                    goal=goal,
                    context=context_str,
                    role=role,
                    output_schema=resolved_schema,
                    max_iterations=max_iterations,
                    parent_agent=parent_agent,
                )
                if not raw_delegation or raw_delegation.startswith("Error:"):
                    raise RuntimeError(raw_delegation or "Hermes delegation returned no result.")

                envelope = json.loads(raw_delegation)
                if not isinstance(envelope, dict):
                    raise ValueError("Hermes delegation returned an invalid result envelope.")
                entries = envelope.get("results")
                if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
                    raise ValueError("Hermes delegation did not return one completed task result.")
                entry = entries[0]
                iterations_used = int(entry.get("api_calls") or 0)
                if entry.get("status") != "completed":
                    raise RuntimeError(str(entry.get("error") or "Hermes subagent did not complete the task."))
                if resolved_schema is not None and entry.get("schema_valid") is False:
                    raise ValueError("Hermes subagent output did not satisfy the requested schema.")
                output_text = str(entry.get("summary") or "").strip()
                if not output_text:
                    raise ValueError("Hermes subagent returned an empty result.")

                if research_task:
                    from src.models.contracts import EpistemicStatus, ResearchDossier
                    from src.research.scoring import score_claim

                    dossier_text = re.sub(
                        r"^```(?:json)?\s*|\s*```$", "", output_text, flags=re.IGNORECASE
                    )
                    dossier_data = json.loads(dossier_text)
                    if isinstance(dossier_data, dict) and isinstance(dossier_data.get("dossier"), dict):
                        dossier_data = dossier_data["dossier"]
                    if not isinstance(dossier_data, dict):
                        raise ValueError("Hermes research result must be a dossier object.")
                    dossier = ResearchDossier.model_validate(dossier_data)
                    if not dossier.claims:
                        raise ValueError("Hermes research result contained no claims.")
                    for claim in dossier.claims:
                        source_url = urlsplit(claim.primary_source.url)
                        if source_url.scheme not in {"http", "https"} or not source_url.netloc:
                            raise ValueError(f"Research claim {claim.claim_id} has an invalid source URL.")
                        # A schema-valid subagent citation has not been fetched
                        # or independently checked here, so it cannot be marked
                        # VERIFIED or retain a model-supplied confidence score.
                        claim.epistemic_status = EpistemicStatus.UNVERIFIABLE
                        claim.confidence_score = score_claim(
                            claim.claim_text,
                            claim.primary_source,
                            claim.corroborating_sources,
                        )
                    structured_data["dossier"] = dossier.model_dump(mode="json")
                else:
                    structured_data["output"] = output_text
                result_status = SubagentStatus.COMPLETED
            except Exception as exc:
                error_message = str(exc)
                logger.warning("Hermes subagent delegation failed: %s", error_message)
        else:
            error_message = "No live Hermes parent agent was provided; this runtime will not synthesize a subagent result."

        structured_data["status"] = result_status.value
        if error_message:
            structured_data["error"] = error_message

        elapsed = time.time() - start_time
        result = SubagentResult(
            subagent_id=subagent_id,
            status=result_status,
            output=output_text or error_message or "Subagent did not run.",
            structured_data=structured_data,
            iterations_used=min(iterations_used, max_iterations),
            duration_seconds=max(round(elapsed, 4), 0.001),
            error_message=error_message,
        )

        self._subagents[subagent_id] = result
        return result

    def execute_turn(
        self,
        session_id: str,
        user_message: str,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Execute a conversation turn while preserving prompt caching."""
        state = self._sessions.get(session_id)
        if not state:
            state = self.create_session(session_id)

        if self.check_interrupt(session_id):
            return {
                "session_id": session_id,
                "interrupted": True,
                "reason": self._interrupt_flags.get(session_id, "user_interrupt"),
                "turn_completed": False,
            }

        if not hasattr(state, "conversation_history") or state.conversation_history is None:
            state.conversation_history = []
        state.conversation_history.append({"role": "user", "content": user_message})
        state.conversation_history.append({"role": "assistant", "content": f"Acknowledged: {user_message}"})
        state.iteration_count += 1
        return {
            "session_id": session_id,
            "iteration": state.iteration_count,
            "interrupted": False,
            "turn_completed": True,
            "user_message_received": user_message,
            "tools_processed": len(tool_results) if tool_results else 0,
        }
