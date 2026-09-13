# Plan — reviewer_1_m4

## Objective
Independent review of Milestone 4: Provider, Memory & Subagent Integration (R4.1, R4.2, R4.3).

## Scope
Inspect:
1. `src/models/contracts.py` (`ContentProject`, `ProductionHistoryRecord`).
2. `src/h9_runtime/models.py` and `src/h9_runtime/bridge.py` (capability role routing, fallback, budgeting).
3. `src/h9_runtime/memory.py` and `src/h9_runtime/bridge.py` (`HermesMemoryRuntime`, `SessionDB` / `state.db` schema, micro-transactions, FTS5 context recall, prompt caching stability).
4. `src/h9_runtime/agent.py` and `tools/h9_content_tools.py` (subagent research delegation, tool scoping, output schema validation).
5. `tests/test_h9_provider_memory_subagent.py` (coverage, test authenticity).

## Deliverable
Write review to `.agents/reviewer_1_m4/handoff.md` with explicit verdict: `APPROVE` or `REQUEST_CHANGES`.
