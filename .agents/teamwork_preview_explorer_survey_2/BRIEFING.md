# BRIEFING — 2026-09-13T17:01:00Z

## Mission
Investigate the production lifecycle state machine, runtime bridge, Hermes tools, and security boundaries for the Harness 9 Epistemic Verification Layer.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: read-only investigation, survey explorer 2
- Working directory: g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_survey_2
- Original parent: 15528e12-b20e-4a6f-b0a1-c1e61282799e
- Milestone: Epistemic Verification Layer Architecture & Survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Do NOT modify codebase source files
- All findings written to handoff.md in working directory
- Message parent with concise completion notice

## Current Parent
- Conversation ID: 15528e12-b20e-4a6f-b0a1-c1e61282799e
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `src/orchestrator/state_machine.py`, `src/orchestrator/pipeline.py`, `src/orchestrator/__init__.py`
  - `src/h9_runtime/content.py`, `src/h9_runtime/bridge.py`, `src/h9_runtime/tools.py`, `src/h9_runtime/execution.py`, `src/h9_runtime/agent.py`
  - `tools/h9_content_tools.py`, `tools/registry.py`
  - `src/security/tokens.py`, `src/security/guard.py`
  - `src/research/engine.py`
  - `tests/test_state_machine.py`, `tests/test_h9_acceptance.py`, `tests/test_h9_m5_sandbox_permission_mcp.py`
- **Key findings**:
  1. 17-state machine operates deterministically via `VALID_TRANSITIONS` table; has 17 canonical sequential states and 3 control states (`PAUSED_FOR_HUMAN`, `FAILED`, `CANCELLED`).
  2. Four verification gates (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`) map naturally between lifecycle phases and must enforce deterministic verdicts (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`). `FINAL_EPISTEMIC_QA` must gate `h9.publish` and state `COMPLETED`.
  3. Native Hermes model tools in `tools/h9_content_tools.py` follow the Footprint Ladder (Rung 3 service-gated `check_fn=check_h9_available`), dual dotted/underscore registration (`h9.tool` + `h9_tool`), and pre-execution capability token enforcement. Concrete schemas designed for 9 new epistemic tools.
  4. Security model enforces least-privilege token derivation ($P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$), HMAC-SHA256 signatures, TTL expiration, and cascading lineage revocation. Untrusted web content requires strict data/instruction boundary encapsulation (`<untrusted_source>`), token-level isolation, and sanitization to prevent prompt injection and authority escalation.
  5. Empirical test verification: `test_h9_m5_sandbox_permission_mcp.py` (19/19 passed), `test_h9_acceptance.py` (44/44 passed), `test_state_machine.py` (10/10 passed). Identified a circular import cycle between `src.orchestrator` and `src.h9_runtime.content` triggered when `src.orchestrator` is imported first.
- **Unexplored areas**: None within assigned scope.

## Key Decisions Made
- Fully documented the 4 verification gates and their transition hooks.
- Defined complete parameter schemas and handler contracts for all 9 new epistemic model tools.
- Formulated untrusted content sanitization architecture and capability permission token additions.
- Diagnosed circular import root cause and recommended deferring `Pipeline` import in `content.py`.

## Artifact Index
- handoff.md — Final 5-component technical handoff report
- DISPATCH.md — Initial dispatch log
- progress.md — Liveness and step tracker
