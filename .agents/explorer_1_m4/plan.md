# Plan — explorer_1_m4

## Objective
Investigate Hermes provider abstraction and H9 model execution paths to design the logical capability role routing architecture for Milestone 4 (R4.1).

## Scope
1. Hermes provider system: `run_agent.py`, `agent/`, provider adapters, model registries, fallback handling, configuration resolution.
2. H9 model call sites: `src/editorial/`, `src/production/`, `src/research/`, `src/models/`, `adapters/`.
3. Runtime boundary: `src/h9_runtime/models.py`, `src/h9_runtime/bridge.py`, `ModelRuntime` interface.
4. Logical roles: `fast_editorial`, `reasoning_research`, `creative_script`, `acoustic_eval`.

## Deliverable
Write findings to `.agents/explorer_1_m4/handoff.md`.
