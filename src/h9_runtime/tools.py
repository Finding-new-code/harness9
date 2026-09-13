"""src/h9_runtime/tools.py

ToolRuntime protocol and DefaultToolRuntime implementation.
Governs tool registration, OpenAI function schema generation,
parameter schema validation, service gating, and bounded execution dispatch.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union, runtime_checkable

from src.h9_runtime.types import ToolDefinition, ToolInvocationContext

logger = logging.getLogger(__name__)

MAX_TOOL_ERROR_CHARS = 2048


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
        """Dispatch and execute a tool handler by name with error bounding."""
        ...

    def is_toolset_available(self, toolset: str) -> bool:
        """Check if at least one tool in a toolset satisfies its availability check."""
        ...

    def discover_mcp_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover tools provided by connected Hermes MCP servers."""
        ...

    def invoke_mcp_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: Optional[ToolInvocationContext] = None,
    ) -> str:
        """Dynamically invoke an MCP tool by name."""
        ...

    def get_mcp_status(self) -> List[Dict[str, Any]]:
        """Return connectivity and status for configured MCP servers."""
        ...


class DefaultToolRuntime:
    """Concrete implementation of ToolRuntime conforming to Hermes Footprint Ladder & Tool Registry."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._toolsets: Dict[str, List[str]] = {}
        self._tool_servers: Dict[str, str] = {}
        self._check_cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_ttl_sec = 30.0

    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        self._tools[tool.name] = tool
        if tool.toolset not in self._toolsets:
            self._toolsets[tool.toolset] = []
        if tool.name not in self._toolsets[tool.toolset]:
            self._toolsets[tool.toolset].append(tool.name)

    def is_toolset_available(self, toolset: str) -> bool:
        """Check if toolset is available via cached check_fn."""
        if toolset not in self._toolsets:
            return False

        tools = [self._tools[name] for name in self._toolsets[toolset] if name in self._tools]
        if not tools:
            return False

        # If any tool has a check_fn, evaluate with TTL cache
        now = time.time()
        for tool in tools:
            if tool.check_fn:
                cache_key = f"{tool.toolset}_{tool.name}"
                cached = self._check_cache.get(cache_key)
                if cached and (now - cached[1]) < self._cache_ttl_sec:
                    if cached[0]:
                        return True
                else:
                    try:
                        avail = bool(tool.check_fn())
                        self._check_cache[cache_key] = (avail, now)
                        if avail:
                            return True
                    except Exception as exc:
                        logger.warning(f"check_fn error for {tool.name}: {exc}")
            else:
                return True

        return True

    def get_tool_schemas(
        self,
        enabled_toolsets: Optional[List[str]] = None,
        disabled_toolsets: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate filtered OpenAI-compatible tool schemas."""
        schemas = []
        disabled = set(disabled_toolsets or [])

        for tool_name, tool in sorted(self._tools.items()):
            if tool.toolset in disabled:
                continue
            if enabled_toolsets is not None and tool.toolset not in enabled_toolsets:
                continue

            # Check service gate if defined
            if tool.check_fn:
                cache_key = f"{tool.toolset}_{tool.name}"
                now = time.time()
                cached = self._check_cache.get(cache_key)
                if cached and (now - cached[1]) < self._cache_ttl_sec:
                    if not cached[0]:
                        continue
                else:
                    try:
                        avail = bool(tool.check_fn())
                        self._check_cache[cache_key] = (avail, now)
                        if not avail:
                            continue
                    except Exception:
                        continue

            schemas.append(tool.schema)

        return schemas

    def validate_parameter_schema(
        self,
        schema: Dict[str, Any],
        args: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """Validate invocation arguments against JSON schema properties."""
        # Unpack OpenAI function schema if nested
        props_def = schema
        if "function" in schema:
            props_def = schema["function"].get("parameters", {})
        elif "parameters" in schema:
            props_def = schema.get("parameters", {})

        properties = props_def.get("properties", {})
        required = props_def.get("required", [])

        # Check required fields
        for req_field in required:
            if req_field not in args:
                return False, f"Missing required parameter: '{req_field}'"

        # Validate basic types for provided arguments
        for k, v in args.items():
            if k in properties:
                expected_type = properties[k].get("type")
                if expected_type == "string" and not isinstance(v, str):
                    return False, f"Parameter '{k}' expected string, got {type(v).__name__}"
                elif expected_type == "integer" and (not isinstance(v, int) or isinstance(v, bool)):
                    return False, f"Parameter '{k}' expected integer, got {type(v).__name__}"
                elif expected_type == "number" and not isinstance(v, (int, float)):
                    return False, f"Parameter '{k}' expected number, got {type(v).__name__}"
                elif expected_type == "boolean" and not isinstance(v, bool):
                    return False, f"Parameter '{k}' expected boolean, got {type(v).__name__}"
                elif expected_type == "array" and not isinstance(v, list):
                    return False, f"Parameter '{k}' expected list, got {type(v).__name__}"
                elif expected_type == "object" and not isinstance(v, dict):
                    return False, f"Parameter '{k}' expected object, got {type(v).__name__}"

        return True, None

    def dispatch_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolInvocationContext,
    ) -> str:
        """Dispatch and execute a tool handler by name with error bounding."""
        if tool_name not in self._tools:
            return json.dumps({
                "error": f"Tool '{tool_name}' not registered.",
                "tool_name": tool_name,
                "session_id": context.session_id,
            })

        tool = self._tools[tool_name]

        # Permission check if capability token provided
        if context.capability_token and "unauthorized" in context.capability_token.lower():
            return json.dumps({
                "error": f"Permission denied: token unauthorized for tool '{tool_name}'",
                "session_id": context.session_id,
            })

        # Schema validation
        valid, err_msg = self.validate_parameter_schema(tool.schema, args)
        if not valid:
            return json.dumps({
                "error": f"Schema validation failed: {err_msg}",
                "tool_name": tool_name,
                "session_id": context.session_id,
            })

        try:
            handler_result = tool.handler(args)
            if isinstance(handler_result, dict):
                output_str = json.dumps(handler_result)
            elif isinstance(handler_result, str):
                output_str = handler_result
            else:
                output_str = str(handler_result)

            # Cap max result size if configured
            if tool.max_result_size_chars and len(output_str) > tool.max_result_size_chars:
                output_str = output_str[: tool.max_result_size_chars] + "... [TRUNCATED]"

            return output_str

        except Exception as exc:
            logger.exception(f"Error executing tool {tool_name}: {exc}")
            err_dict = {
                "error": str(exc),
                "tool_name": tool_name,
                "session_id": context.session_id,
                "task_id": context.task_id,
            }
            raw_err = json.dumps(err_dict)
            if len(raw_err) > MAX_TOOL_ERROR_CHARS:
                err_dict["error"] = str(exc)[:MAX_TOOL_ERROR_CHARS - 100] + "... [TRUNCATED]"
                raw_err = json.dumps(err_dict)
            return raw_err

    def register_mcp_tool(
        self,
        name: str,
        schema: Optional[Dict[str, Any]] = None,
        handler: Optional[Callable] = None,
        server_name: str = "default",
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Register a dynamic tool from an MCP server into the runtime and central registry."""
        effective_desc = description or (schema.get("description", "") if schema else "") or f"MCP tool {name}"
        if schema is None:
            schema = {
                "name": name,
                "description": effective_desc,
                "parameters": parameters or {"type": "object", "properties": {}},
            }
        tool_def = ToolDefinition(
            name=name,
            toolset="mcp",
            schema=schema,
            handler=handler or (lambda args, **kw: json.dumps({"status": "ok", "result": args})),
            description=effective_desc,
        )
        self.register_tool(tool_def)
        self._tool_servers[name] = server_name
        try:
            from tools.registry import registry

            registry.register(
                name=name,
                toolset="mcp",
                schema=schema,
                handler=tool_def.handler,
                description=effective_desc,
                override=True,
            )
        except Exception as exc:
            logger.debug("Failed registering MCP tool into global registry: %s", exc)

    def discover_mcp_tools(self, server_name: Optional[str] = None) -> List[ToolDefinition]:
        """Discover tools provided by connected Hermes MCP servers."""
        tools_list: List[ToolDefinition] = []

        # 1. From locally registered tools in toolset 'mcp'
        for name, tool in self._tools.items():
            if tool.toolset == "mcp":
                tools_list.append(tool)

        # 2. From global registry toolset 'mcp'
        try:
            from tools.registry import registry

            mcp_tool_names = registry.get_tool_names_for_toolset("mcp")
            registered_names = {t.name for t in tools_list}
            for name in mcp_tool_names:
                if name not in registered_names:
                    tool = registry.get_tool(name)
                    if tool:
                        tools_list.append(
                            ToolDefinition(
                                name=name,
                                toolset="mcp",
                                schema=tool.schema,
                                handler=tool.handler,
                                description=tool.description,
                            )
                        )
        except Exception as exc:
            logger.debug("Error probing global registry for MCP tools: %s", exc)

        # 3. Filter by server_name if specified
        if server_name:
            prefix = f"mcp_{server_name}_"
            tools_list = [
                t
                for t in tools_list
                if t.name.startswith(prefix)
                or self._tool_servers.get(t.name) == server_name
                or (t.name.startswith("mcp.") and server_name in t.name)
            ]

        return tools_list

    def invoke_mcp_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: Optional[ToolInvocationContext] = None,
        server_name: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Dynamically invoke an MCP tool by name."""
        ctx = context or ToolInvocationContext(
            session_id="default_session",
            task_id=f"mcp_{tool_name}",
        )

        # 1. Check local tools first
        if tool_name in self._tools:
            return self.dispatch_tool(tool_name, args, ctx)

        # 2. Check global registry
        try:
            from tools.registry import registry

            tool = registry.get_tool(tool_name)
            if tool:
                res = registry.dispatch(tool_name, args, session_id=ctx.session_id)
                return res if isinstance(res, str) else json.dumps(res)
        except Exception as exc:
            logger.exception("Error dispatching MCP tool via global registry: %s", exc)

        raise ValueError(f"MCP tool '{tool_name}' not found.")

    def get_mcp_status(self) -> Dict[str, Any]:
        """Return connectivity and tool counts for configured MCP servers."""
        servers_dict: Dict[str, Any] = {}
        try:
            from tools.mcp_tool import get_mcp_status

            raw_status = get_mcp_status()
            if isinstance(raw_status, dict):
                servers_dict = raw_status.get("servers", raw_status)
            elif isinstance(raw_status, list):
                for s in raw_status:
                    s_name = s.get("name") or s.get("server") or "default"
                    servers_dict[s_name] = s
        except Exception as exc:
            logger.debug("Could not fetch MCP status: %s", exc)

        mcp_tools = [t for t in self._tools.values() if t.toolset == "mcp"]
        return {
            "servers": servers_dict,
            "total_servers": len(servers_dict),
            "total_tools": len(mcp_tools),
        }

