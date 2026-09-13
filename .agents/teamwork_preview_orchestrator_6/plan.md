# Execution Plan — teamwork_preview_orchestrator_6

## Mission
Remediate all 26 failing tests and 4 errors in `tests/test_h9_acceptance.py` across Dimensions A–H to achieve 44/44 passing tests, run full regression testing across the entire suite, author `docs/architecture/hermes-h9-integration-audit.md`, and achieve clean passing gates from dual reviewers, challengers, and forensic auditor.

## Milestones & Phased Execution

### Phase 1: Investigation & Root Cause Mapping (Milestone 1)
- Dispatch 3 Explorers across Dimensions A–H:
  - Explorer 1: Dimensions A, B, C (src/h9_runtime/bridge.py, src/models/contracts.py, src/models/ir.py, provider schemas and fallback chains)
  - Explorer 2: Dimensions D, E (tools/h9_content_tools.py OpenAI function schemas, handlers, subagent delegation, research dossier return)
  - Explorer 3: Dimensions F, G, H (src/security/tokens.py token derivation/revocation, sandbox isolation, E2E video rendering/publish manifest)
- Synthesize explorer findings into concrete bug catalogs and remediation plans.

### Phase 2: Implementation & Defect Remediation (Milestone 2)
- Dispatch Worker(s) with clear file ownership boundaries:
  - Worker 1 (Core Contracts & IR & Bridge): src/h9_runtime/bridge.py, src/models/contracts.py, src/models/ir.py
  - Worker 2 (Tools, Subagent & Security): tools/h9_content_tools.py, src/security/tokens.py, sandbox/E2E integration points
- Require workers to run `pytest tests/test_h9_acceptance.py` and verify all 44 tests pass cleanly.

### Phase 3: Regression Suite Execution (Milestone 3)
- Execute the full Hermes × H9 regression test suite across all 16+ test files:
  - `tests/test_h9_runtime.py`
  - `tests/test_h9_content_tools.py`
  - `tests/test_h9_skills_and_ir.py`
  - `tests/test_h9_provider_memory_subagent.py`
  - `tests/test_h9_m5_sandbox_permission_mcp.py`
  - `tests/test_state_machine.py`
  - `tests/test_contracts.py`
  - `tests/test_editorial.py`
  - `tests/test_deduplication.py`
  - `tests/test_economics.py`
  - `tests/test_security_tokens.py`
  - etc.
- Confirm 100% pass rate with zero regressions.

### Phase 4: Author Final Integration Audit Report (Milestone 4)
- Dispatch Worker to author `docs/architecture/hermes-h9-integration-audit.md`:
  - Full capability matrix comparing standalone H9 vs Hermes coupled H9.
  - Boundary interface architecture (`src/h9_runtime/`).
  - Native model tools and skill catalog (`tools/h9_content_tools.py`, `skills/h9-*/`).
  - Production IR specification and HyperFrames compilation seam.
  - Provider, memory, subagent, permission, and sandbox governance.
  - Empirical acceptance test results across all 8 dimensions (A–H) with zero-regression confirmation.

### Phase 5: Independent Verification & Gate Assessment (Milestone 5)
- Dispatch 2 independent Reviewers (`teamwork_preview_reviewer`).
- Dispatch 2 Challengers (`teamwork_preview_challenger`).
- Dispatch 1 Forensic Auditor (`teamwork_preview_auditor`).
- Compile `GATE_STATUS.md` and verify all criteria pass.
- Produce final report and notify Sentinel.
