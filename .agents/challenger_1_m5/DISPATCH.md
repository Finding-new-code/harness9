## 2026-09-05T04:43:30Z

You are challenger_1_m5, an adversarial challenger for Milestone 5 (Sandbox, Permission & MCP Integration) of the Hermes x Harness 9 Runtime Coupling.

Your working directory is: g:\Finding-new-code\harness9\.agents\challenger_1_m5 (write only metadata/handoff here).

MANDATORY FIRST STEPS:
1. Initialize DISPATCH.md, BRIEFING.md, and progress.md.
2. Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (MANDATORY: read before starting tests).
3. Read g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_5\PROJECT.md.
4. Read g:\Finding-new-code\harness9\.agents\worker_m5_2\handoff.md.

CHALLENGE FOCUS: Permission & Capability Tokens Adversarial Stress
- Write an adversarial test script tests/test_challenger_m5_permissions.py that rigorously attempts to break the permission and token boundaries:
  1. Token Tampering: Modifying token_id, allowed_tools, subject_id, role, or expires_at_utc and verifying HMAC-SHA256 detection rejects it.
  2. Expired Token Replay: Replaying expired tokens and verifying immediate rejection.
  3. Privilege Escalation: Child attempting to request permissions not granted to parent ($P_{child} \not\subseteq P_{parent}$).
  4. Deep Lineage Delegation: Creating chains exceeding max_delegation_depth and verifying rejection.
  5. Unauthorized Tool Invocations: Calling h9.render and h9.publish with restricted tokens (role="researcher", role="scriptwriter", stage="ideation") and verifying permission_denied error envelopes.
  6. Dynamic Lineage Revocation: Revoking an intermediate parent token in TokenRevocationRegistry and verifying that all descendant child/grandchild tokens are immediately invalidated.
- Run tests: .venv\Scripts\python.exe -m pytest tests/test_challenger_m5_permissions.py -v.
- Deliverable: Write handoff to g:\Finding-new-code\harness9\.agents\challenger_1_m5\handoff.md with Gate Verdict: APPROVE or REQUEST_CHANGES.
- Notify orchestrator with send_message.
