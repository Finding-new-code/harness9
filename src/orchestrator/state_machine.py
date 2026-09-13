"""Harness 9 Production Lifecycle State Machine.

Implements the 17-state deterministic lifecycle (CREATED through COMPLETED)
with transition validation, jump rejection, and comprehensive audit history logging.
"""

from datetime import datetime, timezone
from enum import Enum
import json
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, ConfigDict


class ProductionState(str, Enum):
    """The 17 canonical lifecycle production states and system control states."""
    # 17 Canonical Lifecycle States
    CREATED = "CREATED"
    RESEARCH_PLANNED = "RESEARCH_PLANNED"
    RESEARCH_IN_PROGRESS = "RESEARCH_IN_PROGRESS"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    EDITORIAL_ANALYSIS = "EDITORIAL_ANALYSIS"
    ANGLE_SELECTED = "ANGLE_SELECTED"
    OUTLINE_APPROVED = "OUTLINE_APPROVED"
    SCRIPTING_IN_PROGRESS = "SCRIPTING_IN_PROGRESS"
    SCRIPT_COMPLETED = "SCRIPT_COMPLETED"
    VOICE_GENERATED = "VOICE_GENERATED"
    VOICE_QA_PASSED = "VOICE_QA_PASSED"
    ASSETS_DISCOVERED = "ASSETS_DISCOVERED"
    ASSETS_FROZEN = "ASSETS_FROZEN"
    COMPOSITION_GENERATED = "COMPOSITION_GENERATED"
    RENDER_IN_PROGRESS = "RENDER_IN_PROGRESS"
    RENDER_COMPLETED = "RENDER_COMPLETED"
    COMPLETED = "COMPLETED"

    # Control & Error States
    PAUSED_FOR_HUMAN = "PAUSED_FOR_HUMAN"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @classmethod
    def canonical_states(cls) -> List["ProductionState"]:
        """Return the exact 17 canonical sequential lifecycle states in order."""
        return [
            cls.CREATED,
            cls.RESEARCH_PLANNED,
            cls.RESEARCH_IN_PROGRESS,
            cls.RESEARCH_COMPLETED,
            cls.EDITORIAL_ANALYSIS,
            cls.ANGLE_SELECTED,
            cls.OUTLINE_APPROVED,
            cls.SCRIPTING_IN_PROGRESS,
            cls.SCRIPT_COMPLETED,
            cls.VOICE_GENERATED,
            cls.VOICE_QA_PASSED,
            cls.ASSETS_DISCOVERED,
            cls.ASSETS_FROZEN,
            cls.COMPOSITION_GENERATED,
            cls.RENDER_IN_PROGRESS,
            cls.RENDER_COMPLETED,
            cls.COMPLETED,
        ]


class StateTransitionError(ValueError):
    """Raised when an invalid state transition or state jump is attempted."""
    pass


class TransitionRecord(BaseModel):
    """Audit log entry capturing a single state transition."""
    model_config = ConfigDict(extra="allow")

    from_state: ProductionState
    to_state: ProductionState
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    payload_summary: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "timestamp": self.timestamp,
            "payload_summary": self.payload_summary,
            "duration_ms": float(self.duration_ms),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionRecord":
        return cls(
            from_state=ProductionState(data["from_state"]),
            to_state=ProductionState(data["to_state"]),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            payload_summary=data.get("payload_summary", {}),
            duration_ms=float(data.get("duration_ms", 0.0)),
            metadata=data.get("metadata", {}),
        )


# Backward compatibility alias
StateTransitionRecord = TransitionRecord


class ProductionStateMachine:
    """Deterministic 17-state lifecycle state machine.
    
    Enforces sequential progression, validates transitions against the transition graph,
    rejects invalid state jumps, and maintains an immutable audit log of all transitions.
    """

    # Transition graph mapping current state to allowed target states
    VALID_TRANSITIONS: Dict[ProductionState, Set[ProductionState]] = {
        ProductionState.CREATED: {
            ProductionState.RESEARCH_PLANNED,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.RESEARCH_PLANNED: {
            ProductionState.RESEARCH_IN_PROGRESS,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.RESEARCH_IN_PROGRESS: {
            ProductionState.RESEARCH_COMPLETED,
            ProductionState.RESEARCH_PLANNED,  # Retry research
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.RESEARCH_COMPLETED: {
            ProductionState.EDITORIAL_ANALYSIS,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.EDITORIAL_ANALYSIS: {
            ProductionState.ANGLE_SELECTED,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.ANGLE_SELECTED: {
            ProductionState.OUTLINE_APPROVED,
            ProductionState.EDITORIAL_ANALYSIS,  # Re-evaluate angles
            ProductionState.PAUSED_FOR_HUMAN,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.OUTLINE_APPROVED: {
            ProductionState.SCRIPTING_IN_PROGRESS,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.SCRIPTING_IN_PROGRESS: {
            ProductionState.SCRIPT_COMPLETED,
            ProductionState.OUTLINE_APPROVED,  # Re-outline
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.SCRIPT_COMPLETED: {
            ProductionState.VOICE_GENERATED,
            ProductionState.SCRIPTING_IN_PROGRESS,  # Re-draft script
            ProductionState.PAUSED_FOR_HUMAN,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.VOICE_GENERATED: {
            ProductionState.VOICE_QA_PASSED,
            ProductionState.SCRIPT_COMPLETED,  # Regenerate voice from script
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.VOICE_QA_PASSED: {
            ProductionState.ASSETS_DISCOVERED,
            ProductionState.VOICE_GENERATED,  # Voice QA failed, re-synthesize
            ProductionState.SCRIPT_COMPLETED,  # Voice QA failed requiring script edit
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.ASSETS_DISCOVERED: {
            ProductionState.ASSETS_FROZEN,
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.ASSETS_FROZEN: {
            ProductionState.COMPOSITION_GENERATED,
            ProductionState.ASSETS_DISCOVERED,  # Re-discover missing assets
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.COMPOSITION_GENERATED: {
            ProductionState.RENDER_IN_PROGRESS,
            ProductionState.COMPOSITION_GENERATED,  # Recompile composition
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.RENDER_IN_PROGRESS: {
            ProductionState.RENDER_COMPLETED,
            ProductionState.COMPOSITION_GENERATED,  # Re-render retry
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.RENDER_COMPLETED: {
            ProductionState.COMPLETED,
            ProductionState.RENDER_IN_PROGRESS,  # Re-render
            ProductionState.FAILED,
            ProductionState.CANCELLED,
        },
        ProductionState.PAUSED_FOR_HUMAN: {
            ProductionState.OUTLINE_APPROVED,
            ProductionState.SCRIPTING_IN_PROGRESS,
            ProductionState.VOICE_GENERATED,
            ProductionState.ASSETS_DISCOVERED,
            ProductionState.COMPOSITION_GENERATED,
            ProductionState.RENDER_IN_PROGRESS,
            ProductionState.CANCELLED,
            ProductionState.FAILED,
        },
        ProductionState.COMPLETED: set(),  # Terminal state
        ProductionState.FAILED: {
            ProductionState.CREATED,  # Reset / retry from beginning
        },
        ProductionState.CANCELLED: set(),  # Terminal state
    }

    def __init__(
        self,
        run_id: str = "default_run",
        initial_state: Union[ProductionState, str] = ProductionState.CREATED,
        context: Optional[Dict[str, Any]] = None,
    ):
        self._run_id = str(run_id)
        self._current_state = (
            initial_state
            if isinstance(initial_state, ProductionState)
            else ProductionState(str(initial_state))
        )
        self._history: List[TransitionRecord] = []
        self._context: Dict[str, Any] = context or {}

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def current_state(self) -> ProductionState:
        return self._current_state

    @property
    def history(self) -> List[TransitionRecord]:
        return list(self._history)

    @property
    def context(self) -> Dict[str, Any]:
        return self._context

    def can_transition(self, target_state: Union[ProductionState, str]) -> bool:
        """Check if transitioning from current_state to target_state is permitted."""
        target = (
            target_state
            if isinstance(target_state, ProductionState)
            else ProductionState(str(target_state))
        )
        allowed = self.VALID_TRANSITIONS.get(self._current_state, set())
        return target in allowed

    def can_transition_to(self, target_state: Union[ProductionState, str]) -> bool:
        """Alias for can_transition."""
        return self.can_transition(target_state)

    def transition_to(
        self,
        target_state: Union[ProductionState, str],
        payload: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
    ) -> ProductionState:
        """Transition the state machine to target_state.
        
        Raises StateTransitionError if the transition is not allowed.
        """
        try:
            target = (
                target_state
                if isinstance(target_state, ProductionState)
                else ProductionState(str(target_state))
            )
        except (ValueError, KeyError) as exc:
            raise StateTransitionError(
                f"Unknown target state: {target_state}"
            ) from exc

        if not self.can_transition(target):
            raise StateTransitionError(
                f"Invalid state transition: Cannot transition from "
                f"{self._current_state.value} to {target.value}"
            )

        payload_summary: Dict[str, Any] = {}
        if payload is not None:
            if hasattr(payload, "model_dump"):
                payload_summary = payload.model_dump()
            elif hasattr(payload, "to_dict"):
                payload_summary = payload.to_dict()
            elif isinstance(payload, dict):
                payload_summary = payload
            else:
                payload_summary = {"payload_repr": str(payload)}
            
            # Store in context
            self._context[target.value.lower()] = payload_summary

        record = TransitionRecord(
            from_state=self._current_state,
            to_state=target,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload_summary=payload_summary,
            duration_ms=float(duration_ms),
            metadata=metadata or {},
        )

        self._history.append(record)
        self._current_state = target
        return self._current_state

    def get_history(self) -> List[TransitionRecord]:
        """Return the transition history."""
        return list(self._history)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return serialized list of transition audit records."""
        return [rec.to_dict() for rec in self._history]

    def is_terminal(self) -> bool:
        """Check whether the state machine has reached a terminal state."""
        return self._current_state in {
            ProductionState.COMPLETED,
            ProductionState.CANCELLED,
        }

    def is_completed(self) -> bool:
        """Check whether the state machine has successfully completed."""
        return self._current_state == ProductionState.COMPLETED

    def is_failed(self) -> bool:
        """Check whether the state machine is in a failed state."""
        return self._current_state == ProductionState.FAILED

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state machine state and history to dictionary."""
        return {
            "run_id": self._run_id,
            "current_state": self._current_state.value,
            "history": [rec.to_dict() for rec in self._history],
            "context": self._context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionStateMachine":
        """Reconstruct state machine from dictionary."""
        sm = cls(
            run_id=data.get("run_id", "default_run"),
            initial_state=ProductionState(data.get("current_state", ProductionState.CREATED.value)),
            context=data.get("context", {}),
        )
        raw_history = data.get("history", [])
        sm._history = [TransitionRecord.from_dict(rec) for rec in raw_history]
        return sm

    def to_json(self, indent: int = 2) -> str:
        """Serialize state machine to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "ProductionStateMachine":
        """Reconstruct state machine from JSON string."""
        return cls.from_dict(json.loads(json_str))
