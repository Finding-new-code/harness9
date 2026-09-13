# DISPATCH — 2026-09-05T09:50:36Z

## 2026-09-05T09:50:36Z
You are worker_m5_2, the replacement implementation worker for Milestone 5 (Sandbox, Permission & MCP Integration) of the Hermes x Harness 9 Runtime Coupling.
Predecessor worker_m5 became unresponsive after creating tests/test_h9_m5_sandbox_permission_mcp.py and making core edits.

Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m5_2 (initialize DISPATCH.md, BRIEFING.md, and progress.md here; only metadata in .agents/).
Source code files to review/finalize are in project root: src/, tools/, adapters/, tests/.

MANDATORY FIRST STEPS:
1. Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (MANDATORY).
2. Read g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_5\PROJECT.md.
3. Read g:\Finding-new-code\harness9\.agents\explorer_1_m5\handoff.md (sandboxing design) and explorer_2_m5\handoff.md (capability tokens & permission calculus).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

TASK OBJECTIVES:
1. Inspect the state left by worker_m5:
   - Check tests/test_h9_m5_sandbox_permission_mcp.py and run it using .venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py.
   - Inspect changes in src/h9_runtime/execution.py, src/security/tokens.py, src/security/guard.py, src/h9_runtime/bridge.py, tools/h9_content_tools.py, tools/registry.py, tools/mcp_tool.py, src/h9_runtime/tools.py.
2. Complete and finalize:
   - R5.1 (Execution Sandboxing): Subprocess execution via Hermes BaseEnvironment, ffmpeg process group timeout killing, CWD isolation, shared memory sizing (--shm-size 1g for Docker).
   - R5.2 (Capability Token Guard & Tool Gating): Principle-of-least-privilege permission calculus (P_child = P_parent ∩ P_role ∩ P_workflow), active TokenRevocationRegistry with cascading lineage invalidation, h9.publish registered in tools/h9_content_tools.py under h9_content toolset, and TokenGuard strictly blocking unauthorized scopes from invoking h9.render or h9.publish.
   - R5.3 (Hermes MCP Integration): Seamless MCP tool discovery, schema translation, and dynamic execution via H9 runtime/bridge.
3. Run the complete test suite:
   .venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py tests/test_h9_runtime.py tests/test_h9_content_tools.py tests/test_h9_provider_memory_subagent.py
   Verify 100% passing tests with zero regressions.
4. Document all changes and test outputs in g:\Finding-new-code\harness9\.agents\worker_m5_2\handoff.md following standard Handoff format (Observation, Logic Chain, Files Modified, Test Commands & Verbatim Output, Verification Method).
5. Send completion message to orchestrator via send_message.
