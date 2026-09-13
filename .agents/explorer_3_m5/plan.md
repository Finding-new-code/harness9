# Plan — explorer_3_m5

## Objective
Investigate Hermes MCP integration and design native tool/runtime consumption of MCP capabilities for H9 (R5.3).

## Scope
1. Hermes MCP integration architecture: Inspect `tools/mcp_tool.py`, MCP catalog, MCP client in Hermes core, MCP server discovery, and tool registration into Hermes registry.
2. H9 capability consumption: How H9 domain operations (research, asset discovery, voice synthesis, hyperframes rendering) discover and invoke tools provided via Hermes MCP servers.
3. Runtime boundary interface: How `src/h9_runtime/tools.py` (`ToolRuntime`) and `src/h9_runtime/bridge.py` expose and delegate to Hermes MCP tools.
4. MCP integration design: Concrete patterns for registering, discovering, and executing MCP tools through the native Hermes tool layer from H9.

## Deliverable
Write findings to `.agents/explorer_3_m5/handoff.md`.
