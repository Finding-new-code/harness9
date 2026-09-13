"""adapters.hyperframes — HyperFrames Adapter, Registry & Visual Components Interface (Milestone M3).

Provides:
- HyperFramesAdapter: Primary compilation and video rendering interface.
- HyperFramesProject: Workspace container for compiled HyperFrames compositions.
- ComponentRegistry: Registry for registration, discovery, and instantiation of visual component blocks.
- Registry convenience helpers: get_registry, register_component, get_component, list_registered_components.
"""

from adapters.hyperframes.adapter import (
    HyperFramesAdapter,
    HyperFramesProject,
)
from adapters.hyperframes.registry import (
    ComponentRegistry,
    get_registry,
    register_component,
    get_component,
    list_registered_components,
)

__all__ = [
    "HyperFramesAdapter",
    "HyperFramesProject",
    "ComponentRegistry",
    "get_registry",
    "register_component",
    "get_component",
    "list_registered_components",
]
