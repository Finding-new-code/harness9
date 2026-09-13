# Dispatch Assignment — teamwork_preview_orchestrator_5

## 2026-09-05T03:47:08Z

### Sender
Parent Orchestrator (Conversation ID: b85af34b-4be1-4195-afa1-aae88a4efcda)

### Assignment
You are teamwork_preview_orchestrator_5, the successor Project Orchestrator for the Hermes x Harness 9 Runtime Coupling.

Your working directory is: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_5
Authoritative user request: g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md

Current Status of Completed Milestones:
- Milestone 1: COMPLETED & VERIFIED CLEAN (docs/architecture/hermes-h9-runtime-coupling.md, src/h9_runtime/, tests/test_h9_runtime.py).
- Milestone 2: COMPLETED & VERIFIED CLEAN (src/h9_runtime/bridge.py, tools/h9_content_tools.py, tools/registry.py, tests/test_h9_content_tools.py, tests/test_adversarial_m2_tools.py, tests/test_challenger_m2_stress.py — passed gate 131/131 tests).
- Milestone 3: COMPLETED & VERIFIED CLEAN (skills/h9-research/SKILL.md, skills/h9-content-planning/SKILL.md, skills/h9-production/SKILL.md, skills/h9-hyperframes/SKILL.md, src/models/ir.py, tests/test_h9_skills_and_ir.py, tests/test_challenger_m3_stress.py — 42/42 stress tests passed).
- Milestone 4: COMPLETED & VERIFIED PASS (src/models/contracts.py, src/h9_runtime/models.py, src/h9_runtime/memory.py, src/h9_runtime/agent.py, tests/test_h9_provider_memory_subagent.py, tests/test_h9_m4_adversarial_stress.py — passed gate 82/82 tests).

Active Milestone: Milestone 5: Sandbox, Permission & MCP Integration
- Explorations completed in .agents/explorer_1_m5/handoff.md, .agents/explorer_2_m5/handoff.md, and .agents/explorer_3_m5/.
- Your immediate tasks for Milestone 5:
  1. Dispatch implementation worker(s) to implement execution sandboxing (wrapping BaseEnvironment for HyperFrames rendering subprocesses, ffmpeg timeouts, CWD isolation), capability token permission guard (TokenGuard with least-privilege checks on unauthorized H9 tools like render or publish), and Hermes MCP integration.
  2. Dispatch dual reviewers, dual adversarial challengers (attempting permission bypass and sandbox escapes), and forensic integrity auditor.
  3. Ensure all M5 verification tests pass.

Next Milestone: Milestone 6: Acceptance & Regression Verification Suite & Final Audit Report
  1. Implement and run integration test suite covering all 8 required acceptance dimensions (A: Runtime Coupling, B: Skill Coupling, C: Provider Coupling, D: Tool Coupling, E: Subagent Coupling, F: Permission Coupling, G: Sandbox Coupling, H: End-to-End Video Artifact Generation).
  2. Run full regression suite across existing Hermes and H9 test suites to verify zero regressions.
  3. Publish the final comprehensive integration audit report at docs/architecture/hermes-h9-integration-audit.md.

Operational Requirements:
- Follow the Orchestrator workflow: maintain your own BRIEFING.md, plan.md, and progress.md in g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_5.
- Update progress.md regularly with timestamped progress so Sentinel crons can track your progress.
- Dispatch work items to dedicated subagents (workers, reviewers, challengers, auditors).
- Verify all 8 acceptance dimensions (A through H) and full regression suite before claiming completion.
- When all criteria are met and verified, report completion to parent.
