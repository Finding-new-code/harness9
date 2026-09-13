# Plan — explorer_2_m4

## Objective
Investigate Hermes memory infrastructure and H9 creator/project memory to design unified persistence without competing storage for Milestone 4 (R4.2).

## Scope
1. Hermes memory infrastructure: `hermes_state.py` (`SessionDB`), `agent/memory/`, `MemoryManager`, profile storage.
2. H9 memory models & stores: `CreatorProfile`, `ContentProject`, `ProductionHistory`, Creator DNA (Brand Constitution, preferences, negative memory, performance memory).
3. Runtime boundary: `src/h9_runtime/memory.py`, `src/h9_runtime/bridge.py`, `MemoryRuntime` interface.
4. Storage convergence: Unified SQLite/FTS5/SessionDB schema design without conflicting database locks or dual-write drift.

## Deliverable
Write findings to `.agents/explorer_2_m4/handoff.md`.
