# Plan — explorer_3_m4

## Objective
Investigate Hermes subagent delegation mechanisms and H9 research synthesis to design isolated subagent research execution returning a structured ResearchDossier for Milestone 4 (R4.3).

## Scope
1. Hermes subagent patterns: `run_agent.py`, `batch_runner.py`, `delegate_task` / subagent spawning conventions, session isolation, and prompt caching preservation.
2. H9 research workflows: `src/research/`, `skills/h9-research/SKILL.md`, `tools/h9_content_tools.py` (`h9.research`), `ResearchDossier`, `SourceRecord`, `ClaimRecord`.
3. Runtime boundary: `src/h9_runtime/agent.py`, `src/h9_runtime/bridge.py`, `AgentRuntime` interface.
4. Delegation interface: Executing research via an isolated Hermes subagent session without mutating main context, returning validated Pydantic `ResearchDossier`.

## Deliverable
Write findings to `.agents/explorer_3_m4/handoff.md`.
