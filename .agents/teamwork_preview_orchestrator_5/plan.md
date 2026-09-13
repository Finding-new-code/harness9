# Execution Plan — teamwork_preview_orchestrator_5

## Mission
Execute and complete Milestone 5 (Sandbox, Permission & MCP Integration) and Milestone 6 (Acceptance & Regression Verification Suite & Final Audit Report) for the Hermes x Harness 9 Runtime Coupling on branch `dev`.

## Step-by-Step Plan

### Milestone 5: Sandbox, Permission & MCP Integration
1. **Worker Dispatch (Phase B)**:
   - Worker (`worker_m5` / `teamwork_preview_worker`) implements:
     - **R5.1 Sandbox Execution Enforcement**:
       - Integrate Hermes `BaseEnvironment` (via `tools/environments/` / `tools/terminal_tool.py`) into `src/h9_runtime/execution.py`.
       - Wrap HyperFrames rendering subprocesses, ffmpeg compilation, and asset downloads through `BaseEnvironment`.
       - Enforce CWD isolation, timeouts (e.g. ffmpeg timeout), process group termination, and shared memory sizing (1G).
     - **R5.2 Capability Token Permission Boundary**:
       - Connect `src/security/tokens.py` and `src/security/guard.py` (`TokenGuard`).
       - Enforce principle-of-least-privilege capability token checks in `src/h9_runtime/bridge.py` and `tools/h9_content_tools.py`.
       - Ensure `h9.publish` exists in `tools/h9_content_tools.py` with proper schema and capability gating.
       - Ensure restricted agents/scopes attempting to invoke unauthorized tools (`h9.render`, `h9.publish`) are strictly blocked.
       - Implement active token revocation registry and lineage invalidation in `src/security/tokens.py`.
     - **R5.3 Hermes MCP Integration**:
       - Integrate Hermes MCP tool discovery (`tools/mcp_tool.py` / `tools/registry.py`) into H9 runtime boundary (`src/h9_runtime/tools.py` / `bridge.py`).
       - Enable H9 operations to discover, inspect, and invoke MCP tools seamlessly.
     - Implement comprehensive verification suite (`tests/test_h9_m5_sandbox_permission_mcp.py`) and run all M5 tests.

2. **Dual Reviewers (Phase C)**:
   - Reviewer 1 (`reviewer_1_m5`): Review code quality, architectural elegance, compliance with Hermes Footprint Ladder, and BaseEnvironment/TokenGuard/MCP contracts. Run unit tests.
   - Reviewer 2 (`reviewer_2_m5`): Review security boundaries, edge cases, error handling, and prompt cache preservation. Run unit tests.

3. **Dual Adversarial Challengers (Phase D)**:
   - Challenger 1 (`challenger_1_m5`): Adversarial security & permission testing — attempt capability token tampering, privilege escalation, expired token replay, lineage forgery, and calling unauthorized tools (`h9.render`, `h9.publish`).
   - Challenger 2 (`challenger_2_m5`): Adversarial sandbox & MCP stress testing — test subprocess timeouts, ffmpeg hung processes, directory traversal/escape outside sandbox CWD, malicious MCP server payloads, and concurrent execution.

4. **Forensic Integrity Auditor (Phase E)**:
   - Auditor (`auditor_m5` / `teamwork_preview_auditor`):
     - Static analysis and integrity verification against hardcoding, dummy mocks, or facade implementations.
     - Binary veto check.

5. **Gate Evaluation (Phase F)**:
   - Check all criteria (Worker tests pass, Reviewers APPROVE, Challengers confirm robustness, Auditor CLEAN).

---

### Milestone 6: Acceptance & Regression Verification Suite & Final Audit Report
6. **Integration & Acceptance Test Implementation**:
   - Worker / Test Writer implements integration test suite covering all 8 acceptance dimensions:
     - Dim A: Runtime Coupling
     - Dim B: Skill Coupling
     - Dim C: Provider Coupling
     - Dim D: Tool Coupling
     - Dim E: Subagent Coupling
     - Dim F: Permission Coupling
     - Dim G: Sandbox Coupling
     - Dim H: End-to-End Video Artifact Generation
7. **Regression Suite Execution**:
   - Execute full regression across existing Hermes and H9 test suites.
8. **Final Integration Audit Report**:
   - Author comprehensive final report at `docs/architecture/hermes-h9-integration-audit.md`.
9. **Verification, Review, and Parent Notification**:
   - Reviewers, Challengers, Auditor verify M6.
   - Present final results to parent.
