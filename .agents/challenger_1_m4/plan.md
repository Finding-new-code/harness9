# Plan — challenger_1_m4

## Objective
Adversarial stress and correctness verification for Milestone 4: Provider & Memory Integration.

## Scope
1. Adversarially stress `DefaultModelRuntime`: test invalid roles, corrupted schemas, budget overflow limits, token estimation extremes, and fallback behavior.
2. Adversarially stress `HermesMemoryRuntime`: test concurrent transactions, SQL injection / special characters in FTS5 queries, non-existent creator IDs, missing project fields, and rapid state transitions.
3. Write empirical stress test harness and execute via pytest.

## Deliverable
Write findings and test results to `.agents/challenger_1_m4/handoff.md` with explicit verdict: `APPROVE` or `REJECT`.
