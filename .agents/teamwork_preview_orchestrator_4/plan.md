# Milestone Execution Plan — teamwork_preview_orchestrator_4

## Overview
Successor orchestrator continuing the Hermes x Harness 9 Runtime Coupling.
Milestones 1, 2, and 3 are completed and verified CLEAN.
Active target: Milestone 4 (Provider, Memory & Subagent Integration), followed by Milestone 5 (Sandbox, Permissions & MCP) and Milestone 6 (Acceptance & Regression Suite, Final Audit Report).

## Milestone 4: Provider, Memory & Subagent Integration
### Objectives
1. **Logical Capability Provider Routing (R4.1)**:
   - Route H9 model execution requests through Hermes' provider abstraction by logical capability roles (`fast_editorial`, `reasoning_research`, `creative_script`, `acoustic_eval`).
   - Prevent hardcoded LLM backends or direct un-gated SDK client instantiations.
   - Implement graceful fallback, temperature/sampling profiles per role, and connection via `ModelRuntime` / `CapabilityBridge`.
2. **Unified Creator & Project Memory (R4.2)**:
   - Interface `CreatorProfile`, `ContentProject`, and `ProductionHistory` with Hermes memory infrastructure (`MemoryManager`, `SessionDB`, SQLite/vector memory providers) without competing persistence.
   - Avoid dual-write drift or conflicting database lockups.
3. **Isolated Research Delegation to Subagents (R4.3)**:
   - Enable delegation of multi-source research synthesis to an isolated Hermes subagent returning a structured `ResearchDossier`.
   - Preserve per-conversation prompt caching: subagent runs in its own context session without bloating or mutating the primary agent's context.

### Execution Cycle for Milestone 4:
- **Phase A: Investigation & Exploration**:
  - Dispatch 3 Explorers (`explorer_1_m4`, `explorer_2_m4`, `explorer_3_m4`) to investigate existing provider, memory, and subagent systems in Hermes and H9 (`src/h9_runtime/`, `agent/`, `hermes_state.py`, `batch_runner.py`, `src/editorial/`, `src/research/`, etc.).
  - Synthesize findings into concrete architectural specifications and file ownership boundaries for the Worker.
- **Phase B: Implementation**:
  - Dispatch Worker (`worker_m4`) with strict write ownership, implementation guide, and the MANDATORY INTEGRITY WARNING.
  - Implement provider role router, memory bridge/provider, and subagent research delegator.
  - Worker runs tests and reports verified passes.
- **Phase C: Independent Review**:
  - Dispatch 2 Reviewers (`reviewer_1_m4`, `reviewer_2_m4`) independently verifying code correctness, interfaces, memory consistency, and test coverage.
- **Phase D: Adversarial Stress & Correctness Verification**:
  - Dispatch 2 Challengers (`challenger_1_m4`, `challenger_2_m4`) to write empirical stress harnesses, mock failure scenarios, test concurrency, fallback chains, and subagent isolation.
- **Phase E: Forensic Integrity Audit**:
  - Dispatch Forensic Auditor (`auditor_m4`) to run full static, behavioral, and anti-facade integrity checks.
- **Phase F: Gate Decision**:
  - Evaluate verdicts in `GATE_STATUS.md`. Require 100% clean passes across build/test, both Reviewers, both Challengers, and Auditor.

## Milestone 5: Sandbox, Permission & MCP Integration
- Plan prepared upon Milestone 4 gate pass.

## Milestone 6: Acceptance & Regression Suite & Final Audit Report
- Plan prepared upon Milestone 5 gate pass.
