## 2026-09-04T23:16:18Z

You are worker_m4, an expert implementation worker.
Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m4
Authoritative user request file (MANDATORY: read this first): g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md
Scope document: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_4\PROJECT.md

Explorer handoff reports with complete architectural blueprints (MANDATORY: read all three):
- Explorer 1 (Provider Routing & Roles): g:\Finding-new-code\harness9\.agents\explorer_1_m4\handoff.md
- Explorer 2 (Memory & SessionDB): g:\Finding-new-code\harness9\.agents\explorer_2_m4\handoff.md
- Explorer 3 (Subagent Research Delegation): g:\Finding-new-code\harness9\.agents\explorer_3_m4\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusively Owned Files:
- src/h9_runtime/models.py
- src/h9_runtime/memory.py
- src/h9_runtime/agent.py
- src/h9_runtime/bridge.py
- src/models/contracts.py
- tools/h9_content_tools.py
- tests/test_h9_provider_memory_subagent.py

Tasks:
1. Contracts (src/models/contracts.py):
   - Add `ContentProject` (mapping project_id, session_id, creator_id, brief, dossier, selected_angle, script, production_ir, render_artifact, publish_package, timestamps) and `ProductionHistoryRecord` (project_id, from_state, to_state, timestamp, payload_summary, duration_ms, metadata) as Pydantic v2 `H9BaseModel` contracts.
2. Provider & Model Routing (src/h9_runtime/models.py, bridge.py):
   - Implement logical capability role execution for `fast_editorial`, `reasoning_research`, `creative_script`, and `acoustic_eval`.
   - Route `DefaultModelRuntime.invoke_capability()` through Hermes auxiliary client (`agent/auxiliary_client.py:call_llm` when available/configured), resolving per-role parameters (temperature, max_tokens, schema) and recording token spend in session `BudgetStatus`.
   - Ensure clean offline / fallback mode: when no live LLM credentials are provided or running in offline unit tests, generate deterministic structured outputs adhering to schemas without network failure.
   - Prevent any hardcoded vendor SDK instantiations.
3. Unified Memory & Persistence (src/h9_runtime/memory.py, bridge.py):
   - Implement `HermesMemoryRuntime` adhering to `MemoryRuntime`, backed by Hermes `SessionDB` (`hermes_state.py`) / `state.db`.
   - Establish table definitions and schema bootstrap for `h9_creators`, `h9_projects`, `h9_production_history`, `h9_learning_candidates`, `h9_retention_curves`, and FTS5 virtual table `h9_memory_fts`.
   - Store and retrieve `CreatorProfile`, `CreatorDNA`, `ContentProject`, and state machine transitions using `SessionDB._execute_write` with `BEGIN IMMEDIATE` and jitter retries.
   - Ensure zero long-running database locks (< 5 ms micro-transactions).
   - Implement FTS5-powered `recall_context` over past learnings and negative constraints.
   - Implement `render_system_prompt_block` returning a byte-stable, deterministic markdown block preserving sacred prompt caching.
   - Maintain `DefaultMemoryRuntime` as a robust fallback.
4. Isolated Subagent Research Delegation (src/h9_runtime/agent.py, bridge.py, tools/h9_content_tools.py):
   - Implement `AgentRuntime.delegate_subagent()` to spawn isolated child subagents.
   - Connect `h9.research` (with `depth="deep"`) and `HermesCapabilityBridge.plan_research` to delegate to an isolated subagent.
   - Restrict subagent tools: allow `web_search`, `web_extract`, `read_file`; block `delegate_task`, `clarify`, `memory`, `h9.render`, `send_message`.
   - Inject `ResearchDossier.model_json_schema()` as structured output contract with bounded retry.
   - Preserve prompt caching: parent context records only outer tool call and final dossier; no subagent intermediate turns enter parent message history.
   - Ensure graceful fallback to procedural/preset research synthesis if subagent or live search fails.
5. Verification & Tests:
   - Create comprehensive test suite in `tests/test_h9_provider_memory_subagent.py` covering:
     * Model capability role execution across all 4 roles and budget tracking.
     * HermesMemoryRuntime persistence, CreatorProfile/ContentProject storage, FTS5 context recall, and prompt block cache stability.
     * Subagent research delegation with tool scoping, schema validation, and prompt caching isolation.
     * Fallback and error resilience.
   - Run tests: `.venv\Scripts\python.exe -m pytest tests/test_h9_provider_memory_subagent.py -v`.
   - Run regression suite: `.venv\Scripts\python.exe -m pytest tests/test_h9_runtime.py tests/test_h9_content_tools.py tests/test_h9_skills_and_ir.py tests/test_h9_provider_memory_subagent.py -q`.
   - Document all commands, passing test outputs, and line counts in `handoff.md`.

## 2026-09-04T23:30:18Z
**Context**: Milestone 4 Implementation (R4.1, R4.2, R4.3)
**Content**: Heartbeat check 5. Checking in on implementation progress.
**Action**: Please report current status across tasks (contracts, provider routing, SessionDB memory runtime, subagent delegation, tests).
