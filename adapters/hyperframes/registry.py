"""adapters.hyperframes.registry — Reusable Component Block Registry (Milestone M3).

Provides registration, discovery, schema inspection, and instantiation for
all HyperFrames parameterized visual component blocks.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from src.hyperframes.components.base import BaseComponent, ComponentSchema
from src.hyperframes.components.reference_collage_hook import ReferenceCollageHook
from src.hyperframes.components.split_screen_intro import SplitScreenIntro
from src.hyperframes.components.quote_highlight import QuoteHighlight
from src.hyperframes.components.timeline_reveal import TimelineReveal
from src.hyperframes.components.statistic_reveal import StatisticReveal
from src.hyperframes.components.comparison_panel import ComparisonPanel
from src.hyperframes.components.creator_bottom_collage import CreatorBottomCollage

logger = logging.getLogger("harness9.adapters.hyperframes.registry")


class ComponentRegistry:
    """Registry maintaining available HyperFrames component blocks."""

    def __init__(self, register_builtins: bool = True) -> None:
        self._registry: Dict[str, Type[BaseComponent]] = {}
        self._instances: Dict[str, BaseComponent] = {}
        if register_builtins:
            self._register_default_blocks()

    def _register_default_blocks(self) -> None:
        """Register the 7 canonical HyperFrames component blocks."""
        defaults = [
            ("reference_collage_hook", ReferenceCollageHook),
            ("split_screen_intro", SplitScreenIntro),
            ("quote_highlight", QuoteHighlight),
            ("timeline_reveal", TimelineReveal),
            ("statistic_reveal", StatisticReveal),
            ("comparison_panel", ComparisonPanel),
            ("creator_bottom_collage", CreatorBottomCollage),
        ]
        for block_id, cls_obj in defaults:
            self.register(block_id, cls_obj, allow_overwrite=True)

    def register(
        self,
        block_id: str,
        component_cls: Type[BaseComponent],
        allow_overwrite: bool = False,
    ) -> None:
        """
        Register a component block class under a unique block_id.
        """
        if not isinstance(block_id, str) or not block_id.strip():
            raise ValueError("block_id must be a non-empty string")
        norm_id = block_id.strip().lower()

        if not isinstance(component_cls, type) or not issubclass(component_cls, BaseComponent):
            raise TypeError(f"component_cls must be a subclass of BaseComponent, got: {component_cls}")

        if norm_id in self._registry and not allow_overwrite:
            raise ValueError(f"Component '{norm_id}' is already registered in ComponentRegistry")

        self._registry[norm_id] = component_cls
        # Invalidate cached instance if any
        if norm_id in self._instances:
            del self._instances[norm_id]
        logger.debug(f"Registered HyperFrames component block: '{norm_id}' ({component_cls.__name__})")

    def get_class(self, block_id: str) -> Type[BaseComponent]:
        """Retrieve component class by block_id."""
        norm_id = block_id.strip().lower()
        if norm_id not in self._registry:
            raise KeyError(
                f"Component '{norm_id}' not found in registry. "
                f"Available: {list(self._registry.keys())}"
            )
        return self._registry[norm_id]

    def get(self, block_id: str) -> BaseComponent:
        """Retrieve a cached or new instance of the component by block_id."""
        norm_id = block_id.strip().lower()
        if norm_id not in self._instances:
            cls_obj = self.get_class(norm_id)
            self._instances[norm_id] = cls_obj()
        return self._instances[norm_id]

    def instantiate(self, block_id: str, **kwargs: Any) -> BaseComponent:
        """Create a fresh instance of the component by block_id."""
        cls_obj = self.get_class(block_id)
        return cls_obj(**kwargs)

    def has(self, block_id: str) -> bool:
        """Check if block_id is registered."""
        return block_id.strip().lower() in self._registry

    def list_components(self) -> List[str]:
        """Return list of all registered component block IDs."""
        return sorted(list(self._registry.keys()))

    def get_schema(self, block_id: str) -> ComponentSchema:
        """Return ComponentSchema metadata for block_id."""
        comp = self.get(block_id)
        return comp.schema

    def list_schemas(self) -> List[ComponentSchema]:
        """Return list of ComponentSchemas for all registered blocks."""
        return [self.get(b).schema for b in self.list_components()]

    def count(self) -> int:
        """Return number of registered components."""
        return len(self._registry)


# Global Default Singleton Instance
_GLOBAL_REGISTRY: Optional[ComponentRegistry] = None


def get_registry() -> ComponentRegistry:
    """Return the global default ComponentRegistry singleton."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ComponentRegistry(register_builtins=True)
    return _GLOBAL_REGISTRY


def register_component(
    block_id: str,
    component_cls: Type[BaseComponent],
    allow_overwrite: bool = False,
) -> None:
    """Convenience helper to register a component on the global registry."""
    get_registry().register(block_id, component_cls, allow_overwrite=allow_overwrite)


def get_component(block_id: str) -> BaseComponent:
    """Convenience helper to get a component instance from the global registry."""
    return get_registry().get(block_id)


def list_registered_components() -> List[str]:
    """Convenience helper to list all registered component block IDs."""
    return get_registry().list_components()
