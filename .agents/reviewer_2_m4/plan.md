# Plan — reviewer_2_m4

## Objective
Independent review of Milestone 4: Provider, Memory & Subagent Integration (R4.1, R4.2, R4.3).

## Scope
Inspect:
1. Interface conformance: Protocol compliance across `ModelRuntime`, `MemoryRuntime`, `AgentRuntime`, `HermesCapabilityBridge`.
2. Concurrency & locking: Verify `HermesMemoryRuntime` uses `< 5 ms` micro-transactions with `BEGIN IMMEDIATE` and jitter retries; verify absence of competing databases or file locks.
3. Prompt caching preservation: Verify byte stability of `render_system_prompt_block` and isolation of subagent reasoning from parent context.
4. Test execution: Run full test suite and verify zero regressions.

## Deliverable
Write review to `.agents/reviewer_2_m4/handoff.md` with explicit verdict: `APPROVE` or `REQUEST_CHANGES`.
