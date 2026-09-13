# BRIEFING — 2026-09-05T04:55:00Z

## Mission
Independent review and adversarial criticism of Milestone 5 (Sandbox, Permission & MCP Integration) for Hermes x Harness 9 Runtime Coupling.

## 🔒 My Identity
- Archetype: reviewer
- Roles: reviewer, critic
- Working directory: g:\Finding-new-code\harness9\.agents\reviewer_1_m5
- Original parent: d8ee0a9c-a772-41e0-acea-c4143b224122
- Milestone: Milestone 5 (Sandbox, Permission & MCP Integration)
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code
- Write only metadata/handoff in .agents/reviewer_1_m5/
- Objective review and adversarial challenge: check for integrity violations, edge cases, failure modes, hardcoded test results, bypasses, facade implementations

## Current Parent
- Conversation ID: d8ee0a9c-a772-41e0-acea-c4143b224122
- Updated: 2026-09-05T04:55:00Z

## Review Scope
- **Files to review**:
  - R5.1 Execution Sandboxing: src/h9_runtime/execution.py, adapters/hyperframes/adapter.py, src/hyperframes/renderer.py, src/assets/freezer.py
  - R5.2 Capability Token Boundary: src/security/tokens.py, src/security/guard.py, tools/h9_content_tools.py
  - R5.3 Hermes MCP Integration: src/h9_runtime/tools.py, src/h9_runtime/bridge.py
- **Interface contracts**: g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md, g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_5\PROJECT.md
- **Review criteria**: correctness, logical completeness, quality, risk assessment, adversarial robustness, integrity checks

## Review Checklist
- **Items reviewed**:
  - R5.1 Execution Sandboxing (BaseEnvironment, timeout, confinement, --shm-size 1g, freezer) [VERIFIED]
  - R5.2 Capability Token Boundary (calculus, HMAC-SHA256, revocation registry, h9.publish, TokenGuard) [VERIFIED]
  - R5.3 Hermes MCP Integration (tools.py, bridge.py, discovery, registration, invocation) [VERIFIED]
  - Milestone 5 test suites (63 tests passed across M5, content tools, runtime) [VERIFIED]
  - Regression test suites (35 tests passed across M4 and security tokens) [VERIFIED]
- **Verdict**: APPROVE (with Major finding on wildcard calculus for custom stages and Minor finding on guarded_tool ContextVar)
- **Unverified claims**: none remaining (all verified independently)

## Attack Surface
- **Hypotheses tested**:
  1. Custom workflow stages with wildcard intersection: confirmed that `calculate_capability_token` collapses dynamic/unregistered stages to empty sets (`set()`).
  2. ContextVar propagation in `@guard.guarded_tool`: confirmed that decorator does not inspect `current_capability_token.get()`.
  3. Integrity checks: verified absence of test cheats, hardcoded responses, or facade stubs across codebase.
- **Vulnerabilities found**:
  - Major: Wildcard calculus asymmetry in `calculate_capability_token` causes dynamic stages to fail-closed with 0 permissions.
  - Minor: `@guard.guarded_tool` decorator ignores ContextVar token.
- **Untested angles**: All primary angles stress-tested and verified.

## Key Decisions Made
- Confirmed zero integrity violations (no cheating, no facades, no hardcodes).
- Confirmed full test suite pass (98/98 tests across M1-M5).
- Issued Gate Verdict: APPROVE with recommendations.

## Artifact Index
- g:\Finding-new-code\harness9\.agents\reviewer_1_m5\DISPATCH.md
- g:\Finding-new-code\harness9\.agents\reviewer_1_m5\BRIEFING.md
- g:\Finding-new-code\harness9\.agents\reviewer_1_m5\progress.md
- g:\Finding-new-code\harness9\.agents\reviewer_1_m5\handoff.md
