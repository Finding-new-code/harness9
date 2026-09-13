"""src.hyperframes.components.base — Abstract Base Component and Schema Contracts (Milestone M3).

Defines:
- ValidationResult: Model capturing component property validation status, errors, and warnings.
- ComponentSchema: Metadata specification describing block ID, supported aspect ratios, and parameters.
- BaseComponent: Abstract base class providing render_html(), render_css(), render_gsap(), and validate().
"""

from abc import ABC, abstractmethod
import html
import logging
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger("harness9.hyperframes.components.base")


class ValidationResult(BaseModel):
    """Validation report returned by component parameter checks."""
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    valid: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

    def add_error(self, message: str) -> None:
        """Append an error message and set valid to False."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Append a non-fatal warning message."""
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to standard dictionary."""
        return self.model_dump()


class ComponentSchema(BaseModel):
    """Metadata schema defining component capabilities and properties."""
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    block_id: str = Field(..., description="Unique slug for the component block")
    display_name: str = Field(..., description="Human-readable block name")
    description: str = Field(..., description="Technical and functional description")
    category: str = Field(default="motion_graphics", description="Component classification")
    supported_aspect_ratios: List[str] = Field(
        default_factory=lambda: ["16:9", "9:16"],
        description="Supported viewport aspect ratios",
    )
    required_props: List[str] = Field(
        default_factory=list,
        description="List of mandatory property keys",
    )
    default_props: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default property values applied when omitted",
    )
    property_types: Dict[str, str] = Field(
        default_factory=dict,
        description="Type mapping for runtime validation",
    )


class BaseComponent(ABC):
    """Abstract base class for all parameterized HyperFrames visual component blocks."""

    schema: ComponentSchema

    def __init__(self) -> None:
        if not hasattr(self, "schema") or self.schema is None:
            raise ValueError(f"{self.__class__.__name__} must define a 'schema' attribute")

    @property
    def block_id(self) -> str:
        """Return the unique block identifier from schema."""
        return self.schema.block_id

    # ---------------------------------------------------------------------------
    # Public Unified Interfaces
    # ---------------------------------------------------------------------------

    def validate(
        self,
        params_or_props: Optional[Dict[str, Any]] = None,
        format_aspect: Optional[str] = None,
        **kwargs: Any,
    ) -> ValidationResult:
        """
        Validate component parameters against schema and semantic constraints.
        Supports both validate(params_dict) and validate(props, format_aspect="16:9").
        """
        result = ValidationResult(valid=True)
        raw_props: Dict[str, Any] = {}
        target_format = "16:9"

        if isinstance(params_or_props, dict):
            # Check if passed a full params envelope {"scene_id": ..., "props": ..., "format": ...}
            if "props" in params_or_props and isinstance(params_or_props["props"], dict):
                raw_props = dict(params_or_props["props"])
                target_format = params_or_props.get("format_aspect", params_or_props.get("format", "16:9"))
            else:
                raw_props = dict(params_or_props)
                target_format = format_aspect or raw_props.get("format_aspect", raw_props.get("format", "16:9"))
        elif kwargs:
            raw_props = dict(kwargs)
            target_format = format_aspect or kwargs.get("format_aspect", kwargs.get("format", "16:9"))

        # 1. Aspect Ratio Validation
        if target_format not in self.schema.supported_aspect_ratios:
            result.add_error(
                f"Unsupported aspect ratio '{target_format}' for block '{self.block_id}'. "
                f"Supported: {self.schema.supported_aspect_ratios}"
            )

        # 2. Required Properties Check (must be explicitly present in raw_props)
        for req in self.schema.required_props:
            if req not in raw_props or raw_props[req] is None or raw_props[req] == "":
                result.add_error(f"Missing required property '{req}' for block '{self.block_id}'")

        # Merge with default props for downstream semantic validation and rendering
        merged_props = {**self.schema.default_props, **raw_props}

        # 3. Component-specific semantic validation hook
        self._validate_props(merged_props, target_format, result)

        return result

    def render_html(
        self,
        scene_id_or_params: Union[str, Dict[str, Any]],
        props: Optional[Dict[str, Any]] = None,
        format_aspect: str = "16:9",
        **kwargs: Any,
    ) -> str:
        """
        Render semantic HTML DOM elements for the component.
        Supports both render_html(scene_id, props, format_aspect) and render_html(params_dict).
        """
        scene_id, resolved_props, fmt = self._unpack_invocation_args(
            scene_id_or_params, props, format_aspect, kwargs
        )
        return self._render_html(scene_id=scene_id, props=resolved_props, format_aspect=fmt)

    def render_css(
        self,
        scene_id_or_params: Union[str, Dict[str, Any]],
        props: Optional[Dict[str, Any]] = None,
        format_aspect: str = "16:9",
        **kwargs: Any,
    ) -> str:
        """
        Render scoped CSS styles for the component.
        Supports both render_css(scene_id, props, format_aspect) and render_css(params_dict).
        """
        scene_id, resolved_props, fmt = self._unpack_invocation_args(
            scene_id_or_params, props, format_aspect, kwargs
        )
        return self._render_css(scene_id=scene_id, props=resolved_props, format_aspect=fmt)

    def render_gsap(
        self,
        scene_id_or_params: Union[str, Dict[str, Any]],
        props: Optional[Dict[str, Any]] = None,
        start_time: float = 0.0,
        duration: float = 5.0,
        format_aspect: str = "16:9",
        **kwargs: Any,
    ) -> str:
        """
        Render deterministic GSAP animation instructions for the component.
        Supports both render_gsap(scene_id, props, start_time, duration, format_aspect) and render_gsap(params_dict).
        """
        if isinstance(scene_id_or_params, dict):
            params = scene_id_or_params
            scene_id = params.get("scene_id", "scene_1")
            raw_props = params.get("props", params.get("component_props", params))
            st = float(params.get("start_time", params.get("start", start_time)))
            dur = float(params.get("duration", duration))
            fmt = params.get("format_aspect", params.get("format", format_aspect))
        else:
            scene_id = str(scene_id_or_params)
            raw_props = props or {}
            st = float(kwargs.get("start_time", start_time))
            dur = float(kwargs.get("duration", duration))
            fmt = kwargs.get("format_aspect", format_aspect)

        resolved_props = {**self.schema.default_props, **(raw_props if isinstance(raw_props, dict) else {})}
        return self._render_gsap(
            scene_id=scene_id,
            props=resolved_props,
            start_time=st,
            duration=dur,
            format_aspect=fmt,
        )

    # ---------------------------------------------------------------------------
    # Abstract Template Methods (Implemented by 7+ Component Blocks)
    # ---------------------------------------------------------------------------

    @abstractmethod
    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        """Generate component HTML snippet."""
        pass

    @abstractmethod
    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        """Generate component CSS rules scoped to scene_id."""
        pass

    @abstractmethod
    def _render_gsap(
        self,
        scene_id: str,
        props: Dict[str, Any],
        start_time: float,
        duration: float,
        format_aspect: str,
    ) -> str:
        """Generate component GSAP timeline code."""
        pass

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Optional hook for component-specific property validations."""
        pass

    # ---------------------------------------------------------------------------
    # Utility Helpers for Derived Components
    # ---------------------------------------------------------------------------

    def _unpack_invocation_args(
        self,
        scene_id_or_params: Union[str, Dict[str, Any]],
        props: Optional[Dict[str, Any]],
        format_aspect: str,
        kwargs: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any], str]:
        """Normalize argument patterns into (scene_id, props, format_aspect)."""
        if isinstance(scene_id_or_params, dict):
            params = scene_id_or_params
            scene_id = str(params.get("scene_id", kwargs.get("scene_id", "scene_1")))
            raw_props = params.get("props", params.get("component_props", params))
            fmt = str(params.get("format_aspect", params.get("format", format_aspect)))
        else:
            scene_id = str(scene_id_or_params)
            raw_props = props or kwargs.get("props", kwargs)
            fmt = str(kwargs.get("format_aspect", format_aspect))

        resolved_props = {**self.schema.default_props, **(raw_props if isinstance(raw_props, dict) else {})}
        return scene_id, resolved_props, fmt

    @staticmethod
    def escape(text: Any) -> str:
        """Escape text for safe HTML rendering."""
        if text is None:
            return ""
        return html.escape(str(text))

    @staticmethod
    def sanitize_color(color: Optional[str], default: str = "#00d2ff") -> str:
        """Sanitize and validate a CSS color string (hex, rgb, rgba)."""
        if not color or not isinstance(color, str):
            return default
        c = color.strip()
        if re.match(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", c):
            return c
        if re.match(r"^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+(?:\s*,\s*[\d.]+\s*)?\)$", c):
            return c
        return default

    @staticmethod
    def calculate_finite_repeats(duration: float, cycle_duration: float) -> int:
        """
        Enforce HyperFrames finite loop math: Math.ceil(duration / cycle) - 1.
        Prevents render hangs from infinite repeat: -1.
        """
        if cycle_duration <= 0 or duration <= 0:
            return 0
        import math
        return max(0, math.ceil(duration / cycle_duration) - 1)
