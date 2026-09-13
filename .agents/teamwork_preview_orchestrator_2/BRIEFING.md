# BRIEFING — 2026-09-04T10:19:00Z

## Mission
Refactor Harness 9 content-production capabilities to run directly through the full Hermes Agent runtime with clean integration boundary (src/h9_runtime/), native tools, skills, subagents, provider routing, memory, sandbox, permissions, MCP, and comprehensive 8-dimension acceptance verification.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator_2
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2
- Original parent: parent (Sentinel)
- Original parent conversation ID: dfd552f5-9d64-4f93-8118-78de33aa97d0

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\PROJECT.md
1. **Decompose**: Survey codebase with 3 Explorers/Spec Miners -> Produce PROJECT.md -> Decompose into 6 Milestones (M1-M6)
2. **Dispatch & Execute**:
   - **Direct (iteration loop)**: Iterate Worker (1) -> Reviewer (2) -> Challenger (2) -> Auditor (1) -> Gate per milestone.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (last resort)
4. **Succession**: Self-succeed at 16 spawns
- **Work items**:
  1. Architecture Audit & Runtime Boundary Interface (M1) [DONE]
  2. Hermes Capability Bridge & Native Tool Conversion (M2) [in-progress]
  3. Native Hermes Skills & Production IR Seam (M3) [pending]
  4. Provider, Memory & Subagent Integration (M4) [pending]
  5. Sandbox, Permission & MCP Integration (M5) [pending]
  6. Acceptance Verification Suite & Audit Report (M6) [pending]
- **Current phase**: 2 (Milestone Execution)
- **Current focus**: Milestone 2 (worker_m2_dev executing)

## 🔒 Key Constraints
- Pure DISPATCH-ONLY orchestrator: NEVER write source code, NEVER run tests directly, NEVER investigate code directly.
- All technical investigation via Explorers/Spec Miners; all implementation via Workers; all verification via Reviewers/Challengers/Auditors.
- Audit is a hard veto (zero tolerance).
- Prompt caching is sacred. Preserve message role alternation and system prompt stability.
- Never reuse subagents after handoff. Always spawn fresh.

## Current Parent
- Conversation ID: dfd552f5-9d64-4f93-8118-78de33aa97d0
- Updated: not yet

## Key Decisions Made
- Milestone 1 certified CLEAN and Gate PASSED (docs/architecture/hermes-h9-runtime-coupling.md, src/h9_runtime/, adapters/hermes/, 52/52 tests passing).
- Dispatched worker_m2_dev for Milestone 2: Hermes Capability Bridge & Native Tool Conversion.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| survey_spec_miner_1 | teamwork_preview_spec_miner | Hermes Runtime Architecture & src/h9_runtime/ Spec | completed | 595b5c23-9156-4623-ba1b-5a347382a942 |
| survey_explorer_2 | teamwork_preview_explorer | H9 Content Architecture, Tools, Skills & IR Seam | completed | bb32691b-b76e-4bb3-8de7-502e90689608 |
| survey_test_explorer_3 | teamwork_preview_explorer | Test Suite, Acceptance Dims A-H & Regression Baseline | completed | 78f0b8d7-f79b-49ea-a086-e708ab438986 |
| worker_m1_dev | teamwork_preview_worker | Milestone 1 Implementation | completed | c4a88d71-1937-4977-b8e5-64db9574c9bc |
| reviewer_1_m1_dev | teamwork_preview_reviewer | M1 Code Review & Protocol Conformance | completed (APPROVE) | d8794bfa-197f-4e7a-9929-f4a667ade6c2 |
| challenger_2_m1_dev | teamwork_preview_challenger | M1 Integration & State Machine Stress Test | completed (APPROVE) | dd52c159-6b3e-4714-9e2b-ce3bce5e1bff |
| worker_m1_remediation | teamwork_preview_worker | M1 Remediation of memory.py | completed (52/52 passed) | a993318e-ea69-41a2-8ba7-98b7550677b9 |
| auditor_m1_dev_2 | teamwork_preview_auditor | M1 Forensic Integrity Audit | completed (CLEAN) | 596d9424-81dc-4a7e-ad16-cec8e83d087a |
| worker_m2_dev | teamwork_preview_worker | Milestone 2 Implementation (hung on ripgrep) | replaced | 0738c1aa-b265-4247-b1cf-cff3ff9948a1 |
| worker_m2_dev_2 | teamwork_preview_worker | Milestone 2 Capability Bridge & Native Tools | in-progress | 019a29a6-cc8c-4ac0-8d9b-83cc74396698 |

## Succession Status
- Succession required: no
- Spawn count: 13 / 16
- Pending subagents: 019a29a6-cc8c-4ac0-8d9b-83cc74396698
- Predecessor: teamwork_preview_orchestrator_1
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: dba72588-b963-4d76-af7f-a4dfb2b69d51/task-21
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run manage_task(Action="list") — re-create if missing

## Artifact Index
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\DISPATCH.md — User dispatch record
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\progress.md — Liveness & iteration progress
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\BRIEFING.md — Persistent memory index
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\PROJECT.md — Global project plan and feature inventory
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\plan.md — Master execution plan
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\GATE_STATUS.md — Milestone gate status log
- g:\Finding-new-code\harness9\.agents\auditor_m1_dev_2\handoff.md — Forensic audit report (CLEAN)
