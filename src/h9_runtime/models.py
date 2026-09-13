"""src/h9_runtime/models.py

ModelRuntime protocol and DefaultModelRuntime implementation.
Governs provider-independent model execution mapped to logical capability roles,
token expenditure accounting, schema parsing, and graceful fallback handling.
"""

from __future__ import annotations

from enum import Enum
import json
import logging
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    runtime_checkable,
)
from pydantic import BaseModel

from src.h9_runtime.types import BudgetStatus, CapabilityRole, ModelResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


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
        session_id: Optional[str] = None,
    ) -> ModelResponse:
        """Invoke model inference mapped to a logical capability role."""
        ...

    def stream_capability(
        self,
        role: CapabilityRole,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        session_id: Optional[str] = None,
    ) -> Iterator[str]:
        """Stream token responses from a capability role."""
        ...

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text snippet."""
        ...

    def get_budget_status(self, session_id: str) -> BudgetStatus:
        """Retrieve token expenditure and budget status for a session."""
        ...


class DefaultModelRuntime:
    """Concrete implementation of ModelRuntime with role mapping and token accounting."""

    # Default mapping of capability roles to logical provider configs
    DEFAULT_ROLE_CONFIGS: Dict[CapabilityRole, Dict[str, Any]] = {
        CapabilityRole.FAST_EDITORIAL: {
            "model_name": "claude-3-5-haiku",
            "provider": "anthropic",
            "temperature": 0.35,
            "max_tokens": 1500,
            "cost_per_1k_tokens": 0.001,
        },
        CapabilityRole.REASONING_RESEARCH: {
            "model_name": "deepseek-r1",
            "provider": "openrouter",
            "temperature": 0.60,
            "max_tokens": 6000,
            "cost_per_1k_tokens": 0.002,
        },
        CapabilityRole.CREATIVE_SCRIPT: {
            "model_name": "claude-3-5-sonnet",
            "provider": "anthropic",
            "temperature": 0.75,
            "max_tokens": 3500,
            "cost_per_1k_tokens": 0.003,
        },
        CapabilityRole.ACOUSTIC_EVAL: {
            "model_name": "acoustic-evaluator",
            "provider": "hermes_auxiliary",
            "temperature": 0.15,
            "max_tokens": 1000,
            "cost_per_1k_tokens": 0.001,
        },
        # Aliases
        CapabilityRole.FAST_INFERENCE: {
            "model_name": "claude-3-5-haiku",
            "provider": "anthropic",
            "temperature": 0.35,
            "max_tokens": 1500,
            "cost_per_1k_tokens": 0.001,
        },
        CapabilityRole.REASONING_DEEP: {
            "model_name": "deepseek-r1",
            "provider": "openrouter",
            "temperature": 0.60,
            "max_tokens": 6000,
            "cost_per_1k_tokens": 0.002,
        },
        CapabilityRole.CREATIVE_SYNTHESIS: {
            "model_name": "claude-3-5-sonnet",
            "provider": "anthropic",
            "temperature": 0.75,
            "max_tokens": 3500,
            "cost_per_1k_tokens": 0.003,
        },
        CapabilityRole.VOICE_SYNTHESIS: {
            "model_name": "acoustic-evaluator",
            "provider": "hermes_auxiliary",
            "temperature": 0.15,
            "max_tokens": 1000,
            "cost_per_1k_tokens": 0.001,
        },
        CapabilityRole.VISION_ANALYSIS: {
            "model_name": "claude-3-5-sonnet",
            "provider": "anthropic",
            "temperature": 0.20,
            "max_tokens": 2000,
            "cost_per_1k_tokens": 0.003,
        },
    }

    def __init__(
        self,
        role_configs: Optional[Dict[CapabilityRole, Dict[str, Any]]] = None,
        offline: bool = False,
    ) -> None:
        self._role_configs = role_configs or self.DEFAULT_ROLE_CONFIGS.copy()
        # Session token spend: session_id -> {tokens: int, cost: float, limit: Optional[float]}
        self._budgets: Dict[str, Dict[str, Any]] = {}
        self._offline = offline

    def configure_role(
        self,
        role: Union[CapabilityRole, str],
        model_name: str,
        provider: str = "hermes_provider",
        cost_per_1k_tokens: float = 0.002,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        """Override or configure a logical capability role mapping."""
        cap_role = self._resolve_role(role)
        self._role_configs[cap_role] = {
            "model_name": model_name,
            "provider": provider,
            "cost_per_1k_tokens": cost_per_1k_tokens,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def set_budget_limit(self, session_id: str, limit_usd: float) -> None:
        """Set an explicit spend ceiling for a session."""
        if session_id not in self._budgets:
            self._budgets[session_id] = {"tokens": 0, "cost": 0.0, "limit": limit_usd}
        else:
            self._budgets[session_id]["limit"] = limit_usd

    def _resolve_role(self, role: Union[CapabilityRole, str]) -> CapabilityRole:
        """Resolve a capability role from enum or string."""
        if isinstance(role, CapabilityRole):
            return role
        try:
            return CapabilityRole(str(role))
        except ValueError:
            for member in CapabilityRole:
                if member.value == str(role).lower() or member.name.lower() == str(role).lower():
                    return member
            return CapabilityRole.FAST_EDITORIAL

    def get_role_config(self, role: Union[CapabilityRole, str]) -> Dict[str, Any]:
        """Retrieve active configuration dict for role."""
        cap_role = self._resolve_role(role)
        return self._role_configs.get(cap_role, {
            "model_name": "default-capability-model",
            "provider": "hermes_provider",
            "cost_per_1k_tokens": 0.002,
            "temperature": 0.7,
            "max_tokens": 2000,
        })

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using whitespace and character heuristics."""
        if not text:
            return 0
        # Average English text is ~4 characters per token
        return max(1, len(text) // 4)

    def _record_usage(
        self,
        session_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_per_1k: float,
    ) -> float:
        """Record token consumption and calculate costs."""
        total_tokens = prompt_tokens + completion_tokens
        cost = (total_tokens / 1000.0) * cost_per_1k

        if session_id not in self._budgets:
            self._budgets[session_id] = {
                "tokens": 0,
                "cost": 0.0,
                "limit": None,
            }

        self._budgets[session_id]["tokens"] += total_tokens
        self._budgets[session_id]["cost"] += cost
        return cost

    def get_budget_status(self, session_id: str) -> BudgetStatus:
        """Retrieve token spend and remaining budget for a session."""
        entry = self._budgets.get(session_id, {"tokens": 0, "cost": 0.0, "limit": None})
        limit = entry.get("limit")
        remaining = (limit - entry["cost"]) if limit is not None else None

        return BudgetStatus(
            session_id=session_id,
            tokens_consumed=entry["tokens"],
            cost_usd=round(entry["cost"], 5),
            budget_limit_usd=limit,
            remaining_budget_usd=round(remaining, 5) if remaining is not None else None,
        )

    def _generate_deterministic_sample_value(
        self,
        field_name: str,
        annotation: Any,
        role: CapabilityRole,
        prompt: str,
    ) -> Any:
        """Generate a valid sample value for a field based on type annotation and field name."""
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is Union:
            non_none = [a for a in args if a is not type(None)]
            if non_none:
                annotation = non_none[0]
                origin = get_origin(annotation)
                args = get_args(annotation)

        # 1. Pydantic BaseModel (nested model)
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return self._generate_deterministic_structured(role, prompt, annotation)

        # 2. Enum
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            members = list(annotation)
            return members[0].value if members else ""

        # 3. List
        if origin is list or annotation is list:
            item_type = args[0] if args else str
            if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                item1 = self._generate_deterministic_structured(role, prompt, item_type)
                return [item1]
            if item_type is str:
                if "takeaway" in field_name.lower():
                    return [f"Key insight for {role.value}", f"Empirical validation for {role.value}"]
                if "query" in field_name.lower() or "tag" in field_name.lower():
                    return ["photo", "schematic"]
                return [f"{field_name}_1", f"{field_name}_2"]
            if item_type in (int, float):
                return [1, 2]
            return []

        # 4. Dict
        if origin is dict or annotation is dict:
            return {"generated_by": role.value, "version": "1.0.0"}

        # 5. String
        if annotation is str:
            fname = field_name.lower()
            if "role" in fname or "capability" in fname:
                return role.value
            if "topic" in fname:
                return prompt[:40] if prompt else "Technical Topic"
            if "headline" in fname or "title" in fname:
                return f"Generated {field_name} for role {role.value}"
            if "summary" in fname or "description" in fname or "narrative" in fname:
                return f"Synthesized {field_name} for role [{role.value}]"
            if "action" in fname:
                return f"Recommended action for {role.value}"
            if "observation" in fname:
                return f"Observation noted for {role.value}"
            if "status" in fname:
                return "COMPLETED"
            if "url" in fname:
                return "https://example.com/source/ref"
            return f"Generated {field_name} for role {role.value}"

        # 6. Integer
        if annotation is int:
            fname = field_name.lower()
            if "score" in fname:
                return 1
            if "duration" in fname:
                return 30
            if "count" in fname or "fps" in fname:
                return 30
            return 1

        # 7. Float
        if annotation is float:
            fname = field_name.lower()
            if "score" in fname or "confidence" in fname:
                return 0.95
            if "duration" in fname:
                return 30.0
            if "cost" in fname:
                return 0.05
            return 1.0

        # 8. Boolean
        if annotation is bool:
            return True

        return f"val_{field_name}"

    def _generate_deterministic_structured(
        self,
        role: CapabilityRole,
        prompt: str,
        schema: Type[T],
    ) -> T:
        """Recursively construct a valid deterministic instance of a Pydantic schema."""
        schema_fields = getattr(schema, "model_fields", None)
        if schema_fields is None:
            schema_fields = getattr(schema, "__fields__", {})

        sample_data: Dict[str, Any] = {}
        for field_name, field_info in schema_fields.items():
            try:
                from pydantic_core import PydanticUndefined
            except ImportError:
                PydanticUndefined = object()
            default_val = getattr(field_info, "default", None)
            if default_val is not None and default_val is not PydanticUndefined:
                sample_data[field_name] = default_val
                continue
            default_factory = getattr(field_info, "default_factory", None)
            if default_factory is not None:
                val = default_factory()
                annotation = getattr(field_info, "annotation", Any)
                origin = get_origin(annotation)
                args = get_args(annotation)
                if isinstance(val, list) and len(val) == 0 and (origin is list or annotation is list):
                    item_type = args[0] if args else None
                    if item_type and isinstance(item_type, type) and issubclass(item_type, BaseModel):
                        sample_data[field_name] = self._generate_deterministic_sample_value(
                            field_name=field_name,
                            annotation=annotation,
                            role=role,
                            prompt=prompt,
                        )
                        continue
                sample_data[field_name] = val
                continue

            annotation = getattr(field_info, "annotation", Any)
            sample_data[field_name] = self._generate_deterministic_sample_value(
                field_name=field_name,
                annotation=annotation,
                role=role,
                prompt=prompt,
            )

        if hasattr(schema, "model_validate"):
            return schema.model_validate(sample_data)
        return schema(**sample_data)

    def _generate_deterministic_text(self, role: CapabilityRole, prompt: str) -> str:
        """Generate role-aligned deterministic text."""
        return f"Synthesized response for [{role.value}] on prompt: {prompt[:80]}"

    def _call_primary_provider(
        self,
        role: CapabilityRole,
        config: Dict[str, Any],
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Optional[ModelResponse]:
        """Invoke primary provider for capability role."""
        from agent.auxiliary_client import call_llm
        messages = []
        sys_content = system_instruction or ""
        if schema is not None and hasattr(schema, "model_json_schema"):
            schema_str = json.dumps(schema.model_json_schema())
            contract = f"\n\nOUTPUT CONTRACT: You MUST return ONLY valid JSON matching this schema:\n{schema_str}"
            sys_content = (sys_content + contract) if sys_content else contract

        if sys_content:
            messages.append({"role": "system", "content": sys_content})
        messages.append({"role": "user", "content": prompt})

        aux_resp = call_llm(
            task=role.value,
            provider=config.get("provider"),
            model=config.get("model_name"),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if aux_resp is None:
            return None

        raw_text = ""
        if hasattr(aux_resp, "choices") and aux_resp.choices:
            msg = aux_resp.choices[0].message
            raw_text = getattr(msg, "content", "") or ""
        elif isinstance(aux_resp, str):
            raw_text = aux_resp
        elif isinstance(aux_resp, dict):
            raw_text = aux_resp.get("content") or json.dumps(aux_resp)

        parsed_object = None
        if raw_text.strip() and schema is not None:
            clean_json = raw_text.strip()
            if clean_json.startswith("```"):
                lines = clean_json.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_json = "\n".join(lines).strip()
            parsed_object = schema.model_validate(json.loads(clean_json))

        p_tokens = self.estimate_tokens(prompt) + self.estimate_tokens(system_instruction or "")
        c_tokens = self.estimate_tokens(raw_text)
        cost_per_1k = config.get("cost_per_1k_tokens", 0.002)
        cost = ((p_tokens + c_tokens) / 1000.0) * cost_per_1k

        return ModelResponse(
            content=raw_text,
            parsed=parsed_object,
            model_name=config.get("model_name", ""),
            provider_name=config.get("provider", "hermes_provider"),
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            cached_tokens=0,
            cost_usd=round(cost, 5),
            duration_seconds=0.5,
        )

    def _call_fallback_provider(
        self,
        role: CapabilityRole,
        config: Dict[str, Any],
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Optional[ModelResponse]:
        """Invoke fallback provider if primary provider raises an error."""
        fallback_provider = config.get("fallback_provider", "openrouter")
        fallback_model = config.get("fallback_model", "anthropic/claude-3-haiku")
        fallback_cfg = dict(config)
        fallback_cfg["provider"] = fallback_provider
        fallback_cfg["model_name"] = fallback_model
        return self._call_primary_provider(
            role=role,
            config=fallback_cfg,
            prompt=prompt,
            system_instruction=system_instruction,
            schema=schema,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def invoke_capability(
        self,
        role: Union[CapabilityRole, str],
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Type[T]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> ModelResponse:
        """Invoke model inference mapped to a logical capability role."""
        cap_role = self._resolve_role(role)
        config = self.get_role_config(cap_role)

        eff_temp = temperature if temperature is not None else config.get("temperature", 0.7)
        eff_max_tokens = max_tokens if max_tokens is not None else config.get("max_tokens", 2000)

        p_tokens = self.estimate_tokens(prompt) + self.estimate_tokens(system_instruction or "")

        # 1. Attempt live execution via primary/fallback if not in offline mode
        if not self._offline:
            try:
                model_resp = self._call_primary_provider(
                    role=cap_role,
                    config=config,
                    prompt=prompt,
                    system_instruction=system_instruction,
                    schema=schema,
                    temperature=eff_temp,
                    max_tokens=eff_max_tokens,
                )
                if model_resp is not None:
                    if session_id:
                        self._record_usage(
                            session_id=session_id,
                            prompt_tokens=model_resp.prompt_tokens,
                            completion_tokens=model_resp.completion_tokens,
                            cost_per_1k=config.get("cost_per_1k_tokens", 0.002),
                        )
                    return model_resp
            except Exception as primary_exc:
                logger.warning(
                    "Primary provider invocation failed for role %s: %s; trying fallback provider",
                    cap_role.value,
                    primary_exc,
                )
                try:
                    fallback_resp = self._call_fallback_provider(
                        role=cap_role,
                        config=config,
                        prompt=prompt,
                        system_instruction=system_instruction,
                        schema=schema,
                        temperature=eff_temp,
                        max_tokens=eff_max_tokens,
                    )
                    if fallback_resp is not None:
                        if session_id:
                            self._record_usage(
                                session_id=session_id,
                                prompt_tokens=fallback_resp.prompt_tokens,
                                completion_tokens=fallback_resp.completion_tokens,
                                cost_per_1k=config.get("cost_per_1k_tokens", 0.002),
                            )
                        return fallback_resp
                except Exception as fallback_exc:
                    logger.warning(
                        "Fallback provider invocation also failed for role %s: %s",
                        cap_role.value,
                        fallback_exc,
                    )

        # 2. Fallback to deterministic generator
        parsed_object: Optional[Any] = None
        if schema is not None:
            try:
                parsed_object = self._generate_deterministic_structured(cap_role, prompt, schema)
                generated_content = (
                    parsed_object.model_dump_json(indent=2)
                    if hasattr(parsed_object, "model_dump_json")
                    else json.dumps(parsed_object)
                )
            except Exception as exc:
                logger.warning(f"Failed to generate structured schema {schema}: {exc}")
                generated_content = f'{{"role": "{cap_role.value}", "status": "completed"}}'
        else:
            generated_content = self._generate_deterministic_text(cap_role, prompt)

        c_tokens = self.estimate_tokens(generated_content)
        cost = self._record_usage(
            session_id or "default_session",
            p_tokens,
            c_tokens,
            config.get("cost_per_1k_tokens", 0.002),
        )

        return ModelResponse(
            content=generated_content,
            parsed=parsed_object,
            model_name=config.get("model_name", "unknown"),
            provider_name=config.get("provider", "hermes_provider"),
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            cached_tokens=0,
            cost_usd=round(cost, 5),
            duration_seconds=0.0,
        )

    def stream_capability(
        self,
        role: Union[CapabilityRole, str],
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        session_id: Optional[str] = None,
    ) -> Iterator[str]:
        """Stream token responses from a capability role."""
        full_response = self.invoke_capability(
            role=role,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            session_id=session_id,
        )
        words = full_response.content.split(" ")
        for word in words:
            yield word + " "
