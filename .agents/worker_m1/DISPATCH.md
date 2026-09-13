## 2026-08-31T11:21:34Z
You are worker_m1.
Working directory: g:\Finding-new-code\harness9\.agents\worker_m1
Original request file: g:\Finding-new-code\harness9\ORIGINAL_REQUEST.md
Project plan: g:\Finding-new-code\harness9\PROJECT.md
Survey analysis references:
- g:\Finding-new-code\harness9\.agents\explorer_survey_1\analysis.md
- g:\Finding-new-code\harness9\.agents\explorer_survey_2\analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task is to implement Milestone M1: State Machine, Production Contracts & Hermes Adapter.

Files you own exclusively:
1. `src/orchestrator/state_machine.py`:
   - Implement `ProductionState` enum containing exactly the 17 canonical lifecycle states:
     `CREATED`, `RESEARCH_PLANNED`, `RESEARCH_IN_PROGRESS`, `RESEARCH_COMPLETED`, `EDITORIAL_ANALYSIS`, `ANGLE_SELECTED`, `OUTLINE_APPROVED`, `SCRIPTING_IN_PROGRESS`, `SCRIPT_COMPLETED`, `VOICE_GENERATED`, `VOICE_QA_PASSED`, `ASSETS_DISCOVERED`, `ASSETS_FROZEN`, `COMPOSITION_GENERATED`, `RENDER_IN_PROGRESS`, `RENDER_COMPLETED`, `COMPLETED`.
   - Implement `ProductionStateMachine` class with transition graph, `transition_to(target_state, payload=None)`, validation of valid transitions, rejection of invalid jumps (raising ValueError or StateTransitionError), and transition history audit log.
2. `src/models/contracts.py`:
   - Implement all 17 Pydantic v2 production schemas:
     `CreatorProfile`, `ContentBrief`, `ResearchPlan`, `ResearchDossier`, `SourceRecord`, `ClaimRecord`, `EditorialAngle`, `ContentOutline`, `Script`, `ScriptBeat`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`.
   - Maintain full backwards compatibility for existing code in `src/models/__init__.py` and re-export existing attributes/methods as needed.
3. `adapters/hermes/`:
   - Implement the Hermes adapter package (`adapters/hermes/__init__.py`, `adapters/hermes/bridge.py`, `adapters/hermes/tools.py`, `adapters/hermes/sandbox.py`).
   - Conforms strictly to Hermes Agent principles (session isolation, prompt cache preservation, service-gated tool definitions).
4. `docs/HERMES_COMPATIBILITY.md`:
   - Complete technical documentation of the Hermes adapter, tool interfaces, cache safety, and session bridge.
5. Unit tests:
   - `tests/test_state_machine.py`: Test all 17 states, all valid sequential transitions, and rejection of invalid state jumps.
   - `tests/test_contracts.py`: Test serialization, deserialization, validation, and field constraints of all 17 Pydantic schemas.
   - `tests/test_hermes_adapter.py`: Test Hermes adapter session sandbox, tool registration, and tool invocation without cache disruption.

Execution & Verification:
- Run unit tests using `.venv\Scripts\python.exe -m unittest ...` or `pytest` to ensure 100% pass.
- Write your complete handoff report to `g:\Finding-new-code\harness9\.agents\worker_m1\handoff.md`.
- Send a message to your parent with your summary and handoff path.
