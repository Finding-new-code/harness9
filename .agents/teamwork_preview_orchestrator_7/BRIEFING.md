# BRIEFING — 2026-09-13T16:46:00Z

## Mission
Design, implement, integrate, and verify the Harness 9 Epistemic Verification Layer across the research, claim, production contract, editorial, script, visual rendering, and lifecycle state machine systems on branch dev in g:\Finding-new-code\harness9.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7
- Original parent: parent (Sentinel)
- Original parent conversation ID: 4f0c2de1-191c-4b52-872a-cefbb21ffbb4

## 🔒 My Workflow
- **Pattern**: Project Pattern (Dual Track: Implementation Track + E2E Testing Track)
- **Scope document**: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7\PROJECT.md
1. **Decompose**: Survey full scope with 3 parallel Explorers. Decompose into 3-7 modular milestones linked by interface contracts. Spawn parallel E2E Testing Track Orchestrator for requirement-driven opaque-box testing.
2. **Dispatch & Execute**:
   - **Delegate (sub-orchestrator)**: Delegate milestones to sub-orchestrators for recursive execution; top-level orchestrator coordinates milestones and tracks.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: Project Orchestrator cannot escalate to parent; must redesign.
4. **Succession**: At 16 spawns, write handoff.md, cancel crons, spawn successor.
- **Work items**:
  1. Survey & Pre-Implementation Audit (R1) [in-progress: dispatching Worker M1]
  2. Evidence Graph & Extended Claim Contracts (R2) [pending]
  3. Multi-Strategy Verification Engine & Policy Dispatch (R3) [pending]
  4. Multi-Stage Pipeline & Visual/Numerical Integrity (R4) [pending]
  5. Lifecycle State Machine Gates, Hermes Runtime & Security Boundaries (R5) [pending]
  6. E2E Testing Track: H9-FactBench & Adversarial Suite (R6) [pending]
  7. Final Acceptance & Verification (R6) [pending]
- **Current phase**: 1 (Milestone 1 Implementation)
- **Current focus**: Milestone 1 (Author baseline audit report docs/architecture/epistemic-verification-audit.md, docs/epistemic/* specs, core docs update, and ADR-006).

## 🔒 Key Constraints
- Never write, modify, or create source code files directly (DISPATCH-ONLY orchestrator).
- Never run build/test commands directly — require workers to do so.
- Never investigate or explore the problem at the code level — dispatch Explorers.
- Use file-editing tools ONLY for metadata/state files (.md) in .agents/ folder.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Binary veto on forensic audit failure.
- Mandatory ORIGINAL_REQUEST.md path in all subagent prompts.

## Current Parent
- Conversation ID: 4f0c2de1-191c-4b52-872a-cefbb21ffbb4
- Updated: 2026-09-13T16:46:00Z

## Key Decisions Made
- Dual-track project structure initiated: Track 1 (Implementation), Track 2 (E2E Testing & FactBench).
- Initial Survey phase launched with 3 parallel Explorers to assess codebase baseline and requirements.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| survey_explorer_1 | teamwork_preview_explorer | Survey: Contracts & Models | completed | 69843281-8cc4-4c08-bbda-1694ae71799d |
| survey_explorer_2 | teamwork_preview_explorer | Survey: State Machine & Runtime | completed | 20d9f075-1224-498b-8f1c-8420fa98d76f |
| survey_explorer_3 | teamwork_preview_explorer | Survey: Verification & Benchmarks | completed | 0be02872-dc2c-45c8-ad8c-e34e1cff358f |
| worker_m1 | teamwork_preview_worker | Milestone 1: Specifications & Audit | completed | 4b882754-c0ab-4059-9749-540bea7b8c7c |
| reviewer_m1_1 | teamwork_preview_reviewer | M1 Review: Architecture & Specs | completed | 3bc3addf-3d7a-43b0-ba34-dad33fc92f58 |
| reviewer_m1_2 | teamwork_preview_reviewer | M1 Review: Policy & State Machine | completed | 4e28549f-7d33-4ca6-9848-718b613585e3 |
| challenger_m1_1 | teamwork_preview_challenger | M1 Challenge: Spec Integrity | completed | 76a6654c-ab31-4cf6-acc2-5f0269383d7e |
| challenger_m1_2 | teamwork_preview_challenger | M1 Challenge: Regression & Bounds | completed | 11615e7f-6ec2-453e-9e26-643f2f409b05 |
| auditor_m1 | teamwork_preview_auditor | M1 Forensic Integrity Audit | completed | 63895589-f51c-4438-85ea-caa3eaf5110a |
| rem_explorer_1 | teamwork_preview_explorer | M1 It2: Circular Import Analysis | in-progress | 2652e419-433d-4bd2-8a70-1ac43840e237 |
| rem_explorer_2 | teamwork_preview_explorer | M1 It2: Test Impact Analysis | in-progress | c238dda7-8d6a-45f8-8013-12303462513a |
| rem_explorer_3 | teamwork_preview_explorer | M1 It2: Documentation Alignment | in-progress | e79466a3-344a-4933-a5f7-09c89a3a9b11 |

## Succession Status
- Succession required: no
- Spawn count: 12 / 16
- Pending subagents: 2652e419-433d-4bd2-8a70-1ac43840e237, c238dda7-8d6a-45f8-8013-12303462513a, e79466a3-344a-4933-a5f7-09c89a3a9b11
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: 15528e12-b20e-4a6f-b0a1-c1e61282799e/task-14
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7\DISPATCH.md — Verbatim user dispatch
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7\BRIEFING.md — Working memory & configuration
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7\progress.md — Liveness & milestone progress
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7\plan.md — Orchestrator execution plan
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_7\PROJECT.md — Global architecture, feature inventory, milestones
