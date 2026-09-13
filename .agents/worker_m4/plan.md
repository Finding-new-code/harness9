# Plan — worker_m4

## Objective
Implement Milestone 4: Provider, Memory & Subagent Integration (R4.1, R4.2, R4.3).

## Owned Files
- `src/h9_runtime/models.py` (Enhance DefaultModelRuntime with Hermes auxiliary provider routing, fallback profiles, role configs)
- `src/h9_runtime/memory.py` (Implement HermesMemoryRuntime with SessionDB / state.db integration, FTS5 recall, prompt block generation)
- `src/h9_runtime/agent.py` (Enhance DefaultAgentRuntime with subagent delegation, tool scoping, output schema validation)
- `src/h9_runtime/bridge.py` (Wire HermesMemoryRuntime, subagent research delegation, and model capability routing)
- `src/models/contracts.py` (Add ContentProject, ProductionHistoryRecord, ensuring full Pydantic v2 compatibility)
- `tools/h9_content_tools.py` (Ensure h9.research integrates with deep subagent delegation and ResearchDossier schema)
- `tests/test_h9_provider_memory_subagent.py` (Create comprehensive Milestone 4 test suite)

## Implementation Steps
1. Update `src/models/contracts.py` to add `ContentProject` and `ProductionHistoryRecord`.
2. Enhance `src/h9_runtime/models.py` to route `invoke_capability` through Hermes provider system (`agent.auxiliary_client.call_llm` when available, with deterministic offline fallback and token spend accounting).
3. Implement `HermesMemoryRuntime` in `src/h9_runtime/memory.py` backed by `SessionDB` / `state.db` with `h9_creators`, `h9_projects`, `h9_production_history`, `h9_learning_candidates`, `h9_retention_curves`, FTS5 search, and byte-stable system prompt generation.
4. Enhance `src/h9_runtime/agent.py` and `src/h9_runtime/bridge.py` to connect isolated subagent delegation with tool scoping and `ResearchDossier` JSON schema validation.
5. Author comprehensive test suite `tests/test_h9_provider_memory_subagent.py`.
6. Run full pytest suite across new tests and all existing regression tests (`tests/test_h9_runtime.py`, `tests/test_h9_content_tools.py`, `tests/test_h9_skills_and_ir.py`, etc.).
7. Author handoff report in `.agents/worker_m4/handoff.md`.
