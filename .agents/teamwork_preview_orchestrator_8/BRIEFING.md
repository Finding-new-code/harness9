# BRIEFING — 2026-09-14T00:32:00Z

## Mission
Design, implement, integrate, and verify the Harness 9 Epistemic Verification Layer across the research, claim, production contract, editorial, script, visual rendering, and lifecycle state machine systems on branch dev in g:\Finding-new-code\harness9 (R2 through R6).

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8
- Original parent: parent (Sentinel)
- Original parent conversation ID: 4f0c2de1-191c-4b52-872a-cefbb21ffbb4

## 🔒 My Workflow
- **Pattern**: Project Pattern (Dual Track: Implementation Track + E2E Testing Track)
- **Scope document**: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\PROJECT.md
1. **Decompose**:
   - Track 1 (Implementation):
     - Milestone 1: Pre-Audit & Formal Specifications (COMPLETED by Gen 7)
     - Milestone 2: Evidence Graph & Extended Claim Contracts (R2) + lazy import fix in content.py
     - Milestone 3: Multi-Strategy Verification Engine & Policy Dispatch (R3)
     - Milestone 4: Multi-Stage Pipeline & Visual/Numerical Integrity (R4)
     - Milestone 5: State Machine Gates, Hermes Runtime & Security Boundaries (R5)
   - Track 2 (E2E Testing Track):
     - E2E Milestone: H9-FactBench (9 categories) & Adversarial Suite (R6) -> TEST_READY.md
   - Final Milestone: Pass 100% test suite, zero regressions (44/44 test_h9_acceptance.py), author final audit report
2. **Dispatch & Execute**:
   - For each milestone: 3 Explorers -> 1 Worker -> 2 Reviewers -> 2 Challengers -> 1 Forensic Auditor -> Gate evaluation.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: Project Orchestrator cannot escalate to parent; must redesign.
4. **Succession**: At 16 spawns, write handoff.md, cancel crons, spawn successor.
- **Work items**:
  1. Milestone 1: Pre-Audit & Specifications [DONE in Gen 7]
  2. Milestone 2: Evidence Graph & Extended Claim Contracts (R2) + lazy import [pending]
  3. Milestone 3: Multi-Strategy Verification Engine & Policy Dispatch (R3) [pending]
  4. Milestone 4: Multi-Stage Pipeline & Visual/Numerical Integrity (R4) [pending]
  5. Milestone 5: State Machine Gates & Hermes Tools (R5) [pending]
  6. E2E Track: H9-FactBench & Adversarial Testing Suite (R6) [pending]
  7. Final Milestone: 100% Verification, Zero Regression & Final Audit [pending]
- **Current phase**: 2 (Milestone 2 & E2E Track Dispatch)
- **Current focus**: Milestone 2 (Evidence Graph, Extended ClaimRecord, 13-Tier Taxonomy, lazy import in content.py)

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
- Updated: 2026-09-14T00:32:00Z

## Key Decisions Made
- Inherited Gen 7 completed M1 baseline audit and specifications.
- Will execute Milestone 2 (Evidence Graph & Extended Claim Contracts) and E2E Test Suite design in parallel.
- Ensure Worker M2 fixes lazy import of Pipeline in src/h9_runtime/content.py to ensure tests/test_state_machine.py passes in isolation.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_1_m2 | teamwork_preview_explorer | M2 Contracts & Taxonomy Explorer | completed | 71796b94-4147-42e5-b29a-78a3b76823e0 |
| explorer_2_m2 | teamwork_preview_explorer | M2 Circular Import & State Machine Explorer | completed | 56ab1561-8540-4150-b9d0-10dd887b94f5 |
| explorer_3_m2 | teamwork_preview_explorer | M2 Evidence Graph Architecture Explorer | completed | ee1215ac-215c-4e3d-8e23-49b72e9eefde |
| worker_m2 | teamwork_preview_worker | M2 Implementation Worker | completed | 5ce7cdb1-c574-41fc-a2b7-5ae30faa72bd |
| reviewer_1_m2 | teamwork_preview_reviewer | M2 Schema & Contracts Reviewer | completed | f9170a7c-078f-4c9b-bfec-1b6319d86d84 |
| reviewer_2_m2 | teamwork_preview_reviewer | M2 Evidence Graph Reviewer | completed | 6fbcadd8-d4d8-4656-b714-67fbb9dfa8cb |
| challenger_1_m2 | teamwork_preview_challenger | M2 DAG Invariants Challenger | completed | f0935b12-212c-4854-8eb1-4bf2a24be8b3 |
| challenger_2_m2 | teamwork_preview_challenger | M2 Contract Compatibility Challenger | completed | 30a5a2c8-6fec-4348-90e8-55c29747e346 |
| auditor_m2 | teamwork_preview_auditor | M2 Forensic Integrity Auditor | completed | 0e0fbf36-8892-472c-9345-d585f614eb37 |
| explorer_1_m3 | teamwork_preview_explorer | M3 Strategies & Dispatch Explorer | completed | 87782e70-dc5e-45bf-9358-54e75d586754 |
| explorer_2_m3 | teamwork_preview_explorer | M3 Historical Policy Explorer | completed | 6a348093-99e5-4729-8245-db6ff113d4f5 |
| explorer_3_m3 | teamwork_preview_explorer | M3 Engine Architecture Explorer | completed | 0d6e3480-3b05-4604-99a8-ce1a9063408c |
| worker_m3 | teamwork_preview_worker | M3 Implementation Worker | completed | c815b2d8-ba8a-4ec6-a94a-0082a415296b |
| reviewer_1_m3 | teamwork_preview_reviewer | M3 Historical Policy Reviewer | in-progress | c4a45ce8-e8d8-45af-aa31-3bb582313a5e |
| reviewer_2_m3 | teamwork_preview_reviewer | M3 Engine & Strategies Reviewer | in-progress | 4db970ca-86ee-4928-9654-f28fa6539343 |
| challenger_1_m3 | teamwork_preview_challenger | M3 Strategies Stress Challenger | in-progress | b706e3b6-a0f0-470f-9e3e-e804fc714141 |
| challenger_2_m3 | teamwork_preview_challenger | M3 Historical Policy Challenger | in-progress | daca4d02-224e-49d0-a5fe-e09e115faf28 |
| auditor_m3 | teamwork_preview_auditor | M3 Forensic Integrity Auditor | in-progress | 4dff1cd8-821e-49da-8cca-1db213b5d0a5 |

## Succession Status
- Succession required: pending subagent completion (spawn threshold reached: 18 >= 16)
- Spawn count: 18 / 16
- Pending subagents: c4a45ce8-e8d8-45af-aa31-3bb582313a5e, 4db970ca-86ee-4928-9654-f28fa6539343, b706e3b6-a0f0-470f-9e3e-e804fc714141, daca4d02-224e-49d0-a5fe-e09e115faf28, 4dff1cd8-821e-49da-8cca-1db213b5d0a5
- Predecessor: teamwork_preview_orchestrator_7
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: ba190775-5480-43b0-a934-7fd1b7ba9b5b/task-32
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\DISPATCH.md — Verbatim user dispatch
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\BRIEFING.md — Working memory & configuration
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\progress.md — Liveness & milestone progress
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\plan.md — Orchestrator execution plan
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\PROJECT.md — Global architecture, feature inventory, milestones
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\GATE_STATUS.md — Gate status tracking
