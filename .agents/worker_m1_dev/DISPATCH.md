## 2026-09-04T09:12:17Z
You are worker_m1_dev, a teamwork_preview_worker subagent.
Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m1_dev

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP:
Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (under ## 2026-09-04T08:55:45Z) and the survey reports:
1. g:\Finding-new-code\harness9\.agents\survey_spec_miner_1\report.md (contains exact protocol definitions, method signatures, capability matrix)
2. g:\Finding-new-code\harness9\.agents\survey_explorer_2\report.md
3. g:\Finding-new-code\harness9\.agents\survey_test_explorer_3\report.md

MILESTONE 1 OBJECTIVE:
Implement Milestone 1: Architecture Audit & Runtime Boundary Interface (Requirement R1).

EXCLUSIVE FILE OWNERSHIP:
- docs/architecture/hermes-h9-runtime-coupling.md
- src/h9_runtime/__init__.py
- src/h9_runtime/types.py
- src/h9_runtime/agent.py
- src/h9_runtime/skills.py
- src/h9_runtime/tools.py
- src/h9_runtime/models.py
- src/h9_runtime/memory.py
- src/h9_runtime/execution.py
- src/h9_runtime/content.py
- adapters/hermes/bridge.py (refactor as delegation shim into src/h9_runtime/ while preserving backwards compatibility)
- adapters/hermes/tools.py (preserve backwards compatibility)

SPECIFICATIONS & REQUIREMENTS:
1. docs/architecture/hermes-h9-runtime-coupling.md:
   - Must contain an in-depth audit of current Hermes vs. H9 execution paths.
   - Must contain a complete capability comparison matrix across all 10 core capabilities (Agent loop, Skills, Tools, MCP, Model routing, Memory, Subagents, Permissions, Sandbox, Cron).
   - Must include clear ASCII / Mermaid call graph diagrams showing:
     a) Legacy M1 Coupling (monolithic synchronous black-box call).
     b) New Decoupled Runtime Coupling via src/h9_runtime/ protocols and capability bridge.
2. src/h9_runtime/ package:
   - Create package src/h9_runtime/ with proper __init__.py exposing all public interfaces.
   - Implement clean runtime interface abstractions (using typing.Protocol / ABCs with strong typing):
     * AgentRuntime: session management, turn execution, context inspection, interrupt checks.
     * SkillRuntime: skill discovery (YAML frontmatter parsing), skill loading, instruction progressive disclosure.
     * ToolRuntime: tool registry interface, parameter schema validation, service-gated toolset management.
     * ModelRuntime: logical capability role routing (fast_editorial, reasoning_research, creative_script, acoustic_eval), prompt execution, fallback handling.
     * MemoryRuntime: CreatorProfile retrieval/updating, PerformanceMemory, SessionDB access without duplicate databases.
     * ExecutionRuntime: sandboxed subprocess execution (FFmpeg, rendering, shell commands) with bounded output capture and timeout handling.
     * ContentRuntime: high-level content orchestration interface mapping domain operations to runtime abstractions.
   - Ensure H9 content services can request Hermes capabilities without importing private internal implementation details.
3. Backward Compatibility Preservation:
   - Preserve adapters/hermes/ as a compatibility delegation facade so existing tests (especially tests/test_hermes_adapter.py) continue to pass 100%.
4. VERIFICATION MANDATE:
   - Run tests using `.venv\Scripts\python.exe -m unittest tests\test_state_machine.py tests\test_contracts.py tests\test_hermes_adapter.py` and any new unit tests for src/h9_runtime/.
   - Ensure 100% tests pass with zero regressions.
   - Document verification commands and output in your handoff.md.

Write your handoff report to g:\Finding-new-code\harness9\.agents\worker_m1_dev\handoff.md and send a message to parent when complete.
