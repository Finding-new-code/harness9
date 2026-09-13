# Plan — challenger_2_m4

## Objective
Adversarial stress and correctness verification for Milestone 4: Subagent Research Delegation & Isolation.

## Scope
1. Adversarially stress `AgentRuntime.delegate_subagent`: test deep subagent recursion attempts, forbidden tools injection (`delegate_task`, `clarify`, `memory`, `h9.render`, `send_message`), invalid session IDs, and timeouts.
2. Adversarially stress `ResearchDossier` JSON schema output validation: test malformed JSON candidates, missing required fields (`primary_source`, `claim_text`), boundary string lengths, and schema recovery.
3. Verify parent context immutability: verify that intermediate subagent messages never leak into parent session.
4. Write empirical stress harness and execute via pytest.

## Deliverable
Write findings and test results to `.agents/challenger_2_m4/handoff.md` with explicit verdict: `APPROVE` or `REJECT`.
