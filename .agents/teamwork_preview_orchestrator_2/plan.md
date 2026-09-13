# Master Execution Plan: Harness 9 Hermes Runtime Integration

## Phase 0: Survey & Scope Mapping [COMPLETED]
- survey_spec_miner_1: Completed Hermes runtime specification and src/h9_runtime/ abstractions.
- survey_explorer_2: Completed H9 content architecture, native tools, skills, and Production IR design.
- survey_test_explorer_3: Completed baseline verification (200+ tests green) and 8-dimension acceptance suite design.

## Phase 1: Milestone Decomposition & Architecture Finalization [COMPLETED]
- Master PROJECT.md established with 17 inventoried features mapped to Milestones M1-M6.
- Interface contracts and code layout established.

## Phase 2: Implementation & Verification Track (M1 through M6)
Each milestone executes via the formal iteration loop:
- Worker implements the milestone deliverables following survey specifications.
- Reviewer 1 & Reviewer 2 objectively review code correctness, completeness, and interface conformance.
- Challenger 1 & Challenger 2 adversarially test boundaries, edge cases, and runtime behavior.
- Forensic Auditor (teamwork_preview_auditor) conducts integrity analysis (anti-cheat, anti-facade, true logic).
- Gate check: All criteria must pass before advancing.

### Milestone Schedule:
- **Milestone 1**: Architecture Audit & Runtime Boundary Interface
  - Deliverables: `docs/architecture/hermes-h9-runtime-coupling.md`, `src/h9_runtime/` protocols & types, `adapters/hermes/` backward-compatibility shim.
- **Milestone 2**: Hermes Capability Bridge & Native Tool Conversion
  - Deliverables: `src/h9_runtime/bridge.py`, `tools/h9_content_tools.py`, tool registry registration (`tools/registry.py`) under `h9_content` toolset, `check_h9_available()`.
- **Milestone 3**: Native Hermes Skills & Production IR Seam
  - Deliverables: `skills/h9-*/SKILL.md` (research, content-planning, production, hyperframes), `src/models/ir.py` AST schemas and validators.
- **Milestone 4**: Provider, Memory & Subagent Integration
  - Deliverables: Logical role-based provider routing, `H9CreatorMemoryProvider` / SessionDB integration, research subagent delegation via `delegate_task`.
- **Milestone 5**: Sandbox, Permission & MCP Integration
  - Deliverables: `BaseEnvironment` subprocess rendering, capability token security guard, MCP tool discovery & consumption.
- **Milestone 6**: 8-Dimension Acceptance Suite & Final Integration Audit
  - Deliverables: `tests/test_h9_acceptance.py`, `tests/test_h9_e2e_integration.py` (Dimensions A-H), zero regression verification, `docs/architecture/hermes-h9-integration-audit.md`.

## Phase 3: Final Acceptance & Sentinel Reporting
- Full verification of all acceptance criteria.
- Complete handoff.md authoring.
- Sentinel notification.
