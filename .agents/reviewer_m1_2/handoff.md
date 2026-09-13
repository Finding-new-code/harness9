# Review & Adversarial Critic Report: Milestone M1 (State Machine, Production Contracts & Hermes Adapter)

**Author:** `reviewer_m1_2` (Reviewer & Adversarial Critic)  
**Date:** 2026-08-31  
**Milestone:** M1 (State Machine, Production Contracts & Hermes Adapter)  
**Verdict:** **REQUEST_CHANGES**  

---

## 1. Observation

### Codebase & Implementation Inspection
1. **17-State Lifecycle State Machine (`src/orchestrator/state_machine.py`)**:
   - `ProductionState` enum defines the exact 17 canonical states: `CREATED`, `RESEARCH_PLANNED`, `RESEARCH_IN_PROGRESS`, `RESEARCH_COMPLETED`, `EDITORIAL_ANALYSIS`, `ANGLE_SELECTED`, `OUTLINE_APPROVED`, `SCRIPTING_IN_PROGRESS`, `SCRIPT_COMPLETED`, `VOICE_GENERATED`, `VOICE_QA_PASSED`, `ASSETS_DISCOVERED`, `ASSETS_FROZEN`, `COMPOSITION_GENERATED`, `RENDER_IN_PROGRESS`, `RENDER_COMPLETED`, `COMPLETED` and control states (`PAUSED_FOR_HUMAN`, `FAILED`, `CANCELLED`).
   - `ProductionStateMachine` implements `can_transition()`, `transition_to()`, `get_history()`, `get_audit_log()`, `to_dict()`, `from_dict()`, `to_json()`, `from_json()`.
   - Verified that transition graph validation strictly enforces valid transitions and raises `StateTransitionError` (subclass of `ValueError`) on invalid jumps.
   - Verified that `sm.history` returns a copy of the list, preventing external mutation of internal audit records.

2. **17 Pydantic v2 Production Contracts (`src/models/contracts.py`)**:
   - Implemented all 17 requested contract schemas: `CreatorProfile`, `ContentBrief`, `ResearchPlan`, `ResearchDossier`, `SourceRecord`, `ClaimRecord`, `EditorialAngle`, `ContentOutline`, `Script`, `ScriptBeat`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`.
   - Re-exported via `src/models/__init__.py` alongside all legacy pipeline schemas (`Claim`, `Source`, `TalkingPoint`, `Statistic`, `Summary`, `DossierMetadata`, `LegacyResearchDossier`, `AssetProvenanceLedger`, `MediaAsset`, `LegacyLicenseInfo`, `CreatorInfo`, `LegacyDimensions`, `Storyboard`, `Scene`, `Beat`, `LegacyScript`, `PipelineSummary`, `StageResult`).
   - Models inherit from `H9BaseModel` providing dual `.save()` / `.load()` (JSON and YAML), `.to_dict()` / `.from_dict()`, `.to_json()` / `.from_json()`, `.to_yaml()` / `.from_yaml()`, and dictionary access operators (`__getitem__`, `get`, `__contains__`).

3. **Hermes Adapter (`adapters/hermes/`)**:
   - `adapters/hermes/sandbox.py`: `HermesSessionSandbox` creates directory structures (`workspace/`, `renders/`, `audit/`), provides `validate_path()` guards against path traversal, and manages scratch cleanup.
   - `adapters/hermes/bridge.py`: `HermesBridge` manages production execution, state tracking, and summary generation.
   - `adapters/hermes/tools.py`: Service-gated tool definitions (`generate_video_from_brief`, `inspect_production_state`, `evaluate_content_quality`) and dispatcher `handle_tool_call()`.
   - `docs/HERMES_COMPATIBILITY.md`: Full specification documenting prompt caching preservation and interface contracts.

### Verification Runs Observed
- Standard M1 unit tests (`tests/test_state_machine.py`, `tests/test_contracts.py`, `tests/test_hermes_adapter.py`): **28/28 passed** in 133.1s.
- Backwards compatibility suite (`tests/test_research.py`, `tests/test_scriptwriting.py`, `tests/test_cli.py`): **60/60 passed** in 22.8s.
- Acceptance Verification Runner (`verify_pipeline.py --test-mode`): **6/6 checkpoints passed** in 219.8s.
- Exhaustive 400-pair state transition matrix: **All 400 pairs validated successfully**.

---

## 2. Findings & Adversarial Stress Test Results

During deep adversarial edge-case stress testing, two defects were identified:

### [Critical] Finding 1: Infinite Recursion (`RecursionError`) on Zero/Boundary Scores in `EditorialScorecard`
- **Location**: `src/models/contracts.py:274-301`
- **Symptom**:
  ```python
  from src.models.contracts import EditorialScorecard
  card = EditorialScorecard(
      audience_relevance=0.0, novelty=0.0, hook_potential=0.0,
      narrative_potential=0.0, creator_fit=0.0, evidence_availability=0.0,
      visual_potential=0.0, platform_fit=0.0, saturation_risk=1.0
  )
  # -> RecursionError: maximum recursion depth exceeded
  ```
- **Root Cause Analysis**:
  In `EditorialScorecard`, `calculate_composite_score` is decorated with `@model_validator(mode="after")`. Inside this method:
  ```python
  if self.composite_score == 0.0:
      ...
      self.composite_score = round(max(0.0, min(1.0, score)), 4)
  return self
  ```
  Because `H9BaseModel` has `validate_assignment=True` in its `ConfigDict`, setting `self.composite_score = 0.0` triggers Pydantic's `validate_assignment`, which re-invokes the `model_validator` (`calculate_composite_score`). Since the computed score is `0.0`, `self.composite_score == 0.0` is still True, which re-assigns `self.composite_score = 0.0`, triggering an infinite recursion loop and crashing Python with `RecursionError`.
- **Impact**: Any candidate angle scoring 0.0 or any boundary initialization with zero metrics will crash the entire pipeline with a stack overflow.
- **Required Fix**:
  Use `object.__setattr__(self, "composite_score", ...)` or `self.__dict__["composite_score"] = ...` to bypass triggering `__setattr__` / `validate_assignment` inside the model validator, or initialize `composite_score: Optional[float] = None` and check `if self.composite_score is None:`.

---

### [Major] Finding 2: `HermesSessionSandbox` Session ID Sanitization Allows Path Escape via Dot Sequences
- **Location**: `adapters/hermes/sandbox.py:28`
- **Symptom**:
  ```python
  from adapters.hermes.sandbox import HermesSessionSandbox
  sb = HermesSessionSandbox(session_id="..")
  # sb.get_session_root() resolves to G:\Finding-new-code\harness9\output\hermes_sessions\..
  # which equals G:\Finding-new-code\harness9\output (escaping hermes_sessions/)
  ```
- **Root Cause Analysis**:
  In `HermesSessionSandbox.__init__`:
  ```python
  self.session_id = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", str(session_id).strip())
  ```
  The regex permits `.` (period) in the session ID. Consequently, inputs like `".."` or `"../../something"` have slashes replaced with underscores (e.g. `".._.._something"` or `".."`), leaving `..` intact. When joined with `Path("output/hermes_sessions") / self.session_id`, `..` causes the path to traverse up into the parent directory, bypassing the intended session root confinement.
- **Impact**: Malicious or malformed session IDs can place session workspaces outside `output/hermes_sessions/`, violating the security boundary.
- **Required Fix**:
  Sanitize dots from session IDs, e.g. `re.sub(r"[^a-zA-Z0-9_\-]", "_", str(session_id).strip())` or strip leading/consecutive dots and assert that `(self.base_dir / self.session_id).resolve()` is strictly within the intended base directory.

---

## 3. Logic Chain

1. **State Machine Correctness**: The 17-state lifecycle transition graph and jump rejection logic in `ProductionStateMachine` was tested across all $20 \times 20 = 400$ state pairs and proved 100% sound. Jump rejections, terminal states (`COMPLETED`, `CANCELLED`), error transitions, audit logging, and payload serialization are fully compliant.
2. **Schema Completeness & Serialization**: All 17 Pydantic v2 schemas and sub-models support dual JSON/YAML file I/O, dict interface, and unknown extra field preservation via `H9BaseModel`.
3. **Backwards Compatibility**: All legacy imports and existing pipeline test suites run with 100% pass rates without breaking changes.
4. **Integrity Verification**: No hardcoded mock outputs, dummy facades, or skipped validations were found.
5. **Necessity of Changes**: Despite strong overall implementation quality, Finding 1 represents a reproducible crash (`RecursionError`) on valid boundary inputs, and Finding 2 represents a sandbox escape vulnerability. Therefore, the implementation requires remediation before approval.

---

## 4. Caveats

- Finding 1 only manifests when the calculated composite score evaluates to exactly `0.0` or when `self.composite_score` is reassigned during assignment validation; standard test cases with positive scores (e.g. >0.8) passed silently because the score was non-zero.
- Finding 2 requires specific dot-containing session IDs; standard alphanumeric session IDs did not trigger the escape.

---

## 5. Conclusion

**Verdict: REQUEST_CHANGES**

Milestone M1 is well-structured and 90% complete, but requires two targeted fixes:
1. Fix `EditorialScorecard.calculate_composite_score` in `src/models/contracts.py` to prevent `RecursionError` on zero/boundary scores (use `object.__setattr__` or `composite_score: Optional[float] = None`).
2. Fix session ID sanitization in `adapters/hermes/sandbox.py` to prevent directory traversal via `..`.

Once these two items are corrected, Milestone M1 will be ready for final approval.

---

## 6. Verification Method

To reproduce and verify the findings and fixes, execute:

```bash
# 1. Reproduce Finding 1 (RecursionError on zero score)
.venv\Scripts\python.exe -c "from src.models.contracts import EditorialScorecard; card = EditorialScorecard(audience_relevance=0.0, novelty=0.0, hook_potential=0.0, narrative_potential=0.0, creator_fit=0.0, evidence_availability=0.0, visual_potential=0.0, platform_fit=0.0, saturation_risk=1.0)"

# 2. Reproduce Finding 2 (Session ID path escape)
.venv\Scripts\python.exe -c "from adapters.hermes.sandbox import HermesSessionSandbox; from pathlib import Path; sb = HermesSessionSandbox(session_id='..'); print(sb.get_session_root().resolve())"

# 3. Run official M1 test suites
.venv\Scripts\python.exe -m unittest tests/test_state_machine.py tests/test_contracts.py tests/test_hermes_adapter.py

# 4. Run backwards compatibility test suites
.venv\Scripts\python.exe -m unittest tests/test_research.py tests/test_scriptwriting.py tests/test_cli.py
```
