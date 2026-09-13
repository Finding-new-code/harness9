## 2026-09-04T08:59:24Z
You are survey_spec_miner_1, a teamwork_preview_spec_miner subagent.
Your working directory is: g:\Finding-new-code\harness9\.agents\survey_spec_miner_1
You are in READ-ONLY mode. Do NOT edit any source code or test files. Only write your metadata, progress, and final report into your working directory.

TASK:
Investigate the authoritative sources for the Hermes Agent runtime and the requirements for refactoring Harness 9 to run directly through the Hermes runtime.

READ FIRST:
1. g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (specifically the section under ## 2026-09-04T08:55:45Z).
2. g:\Finding-new-code\harness9\AGENTS.md
3. Hermes Agent core files: run_agent.py, model_tools.py, toolsets.py, tools/registry.py, agent/ directory (provider adapters, memory, caching, compression), cron/, plugins/, existing Hermes skills in skills/, MCP integration, and sandbox/environment backends in tools/environments/.
4. Existing H9 adapter: adapters/hermes/ and docs/HERMES_COMPATIBILITY.md.

INVESTIGATION OBJECTIVES (Requirements R1, R2, R5):
1. How does Hermes register and dispatch model tools? (tools/registry.py, model_tools.py, toolsets.py, _HERMES_CORE_TOOLS vs named toolsets, check_fn vs surface gates).
2. How does Hermes discover, load, and execute skills? (skills/*/SKILL.md format, YAML frontmatter, instructions, scripts, invocation patterns).
3. How does Hermes route provider and model inference requests? (agent/ provider adapters, base_url, api_mode, capability roles, prompt caching invariants, message role alternation).
4. How does Hermes handle memory and state persistence? (agent/memory/, session DB, SessionDB, how creator and project memory should integrate without duplicate persistence).
5. How does Hermes manage subagent delegation and isolation? (run_agent.py AIAgent subagent spawning, max_iterations, iteration budget).
6. How does Hermes enforce sandbox, permissions, and MCP integrations? (tools/environments/ sandboxing, subprocess execution, MCP server catalog and client).
7. Clean runtime interface abstractions required in src/h9_runtime/:
   - AgentRuntime
   - SkillRuntime
   - ToolRuntime
   - ModelRuntime
   - MemoryRuntime
   - ExecutionRuntime
   - ContentRuntime
   Define exact abstract classes / protocols, methods, type signatures, and decoupling rationale so H9 content services request Hermes capabilities without internal implementation coupling.

OUTPUT:
Write your comprehensive report to g:\Finding-new-code\harness9\.agents\survey_spec_miner_1\report.md.
Include:
- Executive Summary
- Full capability comparison matrix: Hermes Runtime vs H9 Requirements
- Exact Hermes extension points and APIs
- Formal interface specifications for src/h9_runtime/
- Critical architectural constraints (prompt caching, role alternation, session scoping, no env pollution)
Update your progress.md and send a message back with your executive summary when complete.
