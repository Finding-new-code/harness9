# Master Execution Plan: Harness 9 Hermes Runtime Integration

## Status Summary
- **Milestone 1**: Architecture Audit & Runtime Boundary Interface — COMPLETED & VERIFIED CLEAN.
- **Milestone 2**: Hermes Capability Bridge & Native Tool Conversion — ACTIVE / READY FOR WORKER.
- **Milestone 3**: Native Hermes Skills & Production IR Seam — PENDING.
- **Milestone 4**: Provider, Memory & Subagent Integration — PENDING.
- **Milestone 5**: Sandbox, Permission & MCP Integration — PENDING.
- **Milestone 6**: Acceptance & Regression Verification Suite & Final Audit — PENDING.

## Execution Sequence & Methodology

Each milestone follows the standard strict verification cycle:
1. **Worker**: Implement deliverables according to architectural specifications, run build and tests, produce handoff report.
2. **Reviewers (2)**: Independent objective code reviews covering completeness, interface conformance, and quality.
3. **Challengers (2)**: Empirical adversarial verification, boundary stress-testing, edge cases.
4. **Forensic Auditor (1)**: Integrity analysis (anti-cheat, anti-facade, genuine business logic). Hard veto.
5. **Gate**: Collect all verdicts in `GATE_STATUS.md`. All criteria must pass before moving to the next milestone.

---

### Milestone 2: Hermes Capability Bridge & Native Tool Conversion
- **Goal**: Implement `src/h9_runtime/bridge.py`, `tools/h9_content_tools.py`, integrate into `tools/registry.py` under `h9_content` toolset with `check_h9_available()`.
- **Worker Deliverables**:
  - `src/h9_runtime/bridge.py`: HermesCapabilityBridge implementing bidirectional communication.
  - `tools/h9_content_tools.py`: 4 native Hermes model tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`).
  - `tools/registry.py`: Service-gated toolset `h9_content` with zero core footprint when inactive.
  - `tests/test_h9_content_tools.py`: Comprehensive test suite verifying tool schemas, execution, error handling, and registry integration.
- **Verification**: 2 Reviewers, 2 Challengers, 1 Forensic Auditor.

---

### Milestone 3: Native Hermes Skills & Production IR Seam
- **Goal**: Package H9 domain workflows into native Hermes skills (`skills/h9-*/SKILL.md`) and implement typed Production IR seam (`src/models/ir.py`).
- **Worker Deliverables**:
  - `skills/h9-research/SKILL.md`
  - `skills/h9-content-planning/SKILL.md`
  - `skills/h9-production/SKILL.md`
  - `skills/h9-hyperframes/SKILL.md`
  - `src/models/ir.py`: Typed Production IR AST (`ProductionIRDocument`, `IRSceneNode`, `IRVisualBlockNode`, `IRSpeechBeatNode`, etc.) with validation.
  - Integration with HyperFrames compiler.
  - Unit and integration tests.
- **Verification**: 2 Reviewers, 2 Challengers, 1 Forensic Auditor.

---

### Milestone 4: Provider, Memory & Subagent Integration
- **Goal**: Route H9 model requests through Hermes provider abstraction by logical capability roles; interface creator/project memory with Hermes memory without competing persistence; delegate multi-source research synthesis to an isolated Hermes subagent returning `ResearchDossier`.
- **Worker Deliverables**:
  - Logical capability provider routing (`src/h9_runtime/models.py`).
  - Unified creator & project memory (`src/h9_runtime/memory.py` / Hermes MemoryManager / SessionDB).
  - Research subagent delegation via `delegate_task` (`src/h9_runtime/agent.py`).
  - Unit and integration tests.
- **Verification**: 2 Reviewers, 2 Challengers, 1 Forensic Auditor.

---

### Milestone 5: Sandbox, Permission & MCP Integration
- **Goal**: Enforce Hermes permission and sandbox execution boundaries on all H9 operations; enable H9 to consume Hermes MCP capabilities via native Hermes tool/runtime layer.
- **Worker Deliverables**:
  - Subprocess execution via `BaseEnvironment` (`src/h9_runtime/execution.py`).
  - Capability token permission enforcement.
  - MCP tool discovery and invocation integration.
  - Unit and integration tests.
- **Verification**: 2 Reviewers, 2 Challengers, 1 Forensic Auditor.

---

### Milestone 6: Acceptance & Regression Verification Suite & Final Audit
- **Goal**: Implement 8-dimension acceptance suite (Dimensions A-H), verify zero regressions across existing Hermes and H9 test suites, and publish final integration audit report.
- **Worker Deliverables**:
  - `tests/test_h9_acceptance.py` and `tests/test_h9_e2e_integration.py` covering all 8 dimensions.
  - Zero regressions across existing test suites (`pytest tests/`).
  - `docs/architecture/hermes-h9-integration-audit.md`.
- **Verification**: 2 Reviewers, 2 Challengers, 1 Forensic Auditor.
- **Final Completion Report** to parent.
