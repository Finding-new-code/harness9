# Milestone M1 Challenger Handoff Report: Empirical Stress-Testing & Adversarial Findings

**Author:** `challenger_m1_1` (Empirical Challenger / Critic / Specialist)  
**Date:** 2026-08-31  
**Milestone:** M1 (State Machine, Production Contracts & Hermes Adapter)  
**Verdict:** `REQUEST_CHANGES`  

---

## 1. Observation

An adversarial test suite with 14 comprehensive stress-testing attack vectors was constructed and executed in `tests/test_adversarial_m1.py`.

Execution Command:
```powershell
$env:PYTHONPATH="g:\Finding-new-code\harness9"; & "g:\Finding-new-code\harness9\.venv\Scripts\python.exe" -m unittest tests.test_adversarial_m1
```

Execution Result:
```
..F.FE........
======================================================================
ERROR: test_adv_11_state_machine_unusual_and_corrupt_payloads (tests.test_adversarial_m1.TestM1AdversarialPayloadsAndCorruption.test_adv_11_state_machine_unusual_and_corrupt_payloads)
Verify state machine gracefully handles non-serializable, complex, and unhashable payloads.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "G:\Finding-new-code\harness9\tests\test_adversarial_m1.py", line 407, in test_adv_11_state_machine_unusual_and_corrupt_payloads
    json_str = sm.to_json()
               ^^^^^^^^^^^^
  File "G:\Finding-new-code\harness9\src\orchestrator\state_machine.py", line 373, in to_json
    return json.dumps(self.to_dict(), indent=indent)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Object of type complex is not JSON serializable

======================================================================
FAIL: test_adv_08_save_audit_record_path_traversal (tests.test_adversarial_m1.TestM1AdversarialHermesSandbox.test_adv_08_save_audit_record_path_traversal)
Verify save_audit_record cannot write outside the audit directory via record_name traversal.
----------------------------------------------------------------------
AssertionError: save_audit_record wrote outside audit directory: C:\Users\User\AppData\Local\Temp\escape_audit.json

======================================================================
FAIL: test_adv_10_concurrent_or_multiple_session_sandboxes (tests.test_adversarial_m1.TestM1AdversarialHermesSandbox.test_adv_10_concurrent_or_multiple_session_sandboxes)
Verify multiple simultaneous session sandboxes maintain complete isolation.
----------------------------------------------------------------------
AssertionError: 5 != 1

----------------------------------------------------------------------
Ran 14 tests in 0.359s

FAILED (failures=2, errors=1)
```

### Detailed Observations by File and Line Number:

#### Finding 1: Path Traversal Escape in `HermesSessionSandbox.save_audit_record`
- **File:** `adapters/hermes/sandbox.py` (lines 84–89)
- **Code Snippet:**
  ```python
  84:     def save_audit_record(self, record_name: str, data: Dict[str, Any]) -> Path:
  85:         """Save a JSON audit record into the session audit directory."""
  86:         target = self.audit_dir / f"{record_name}.json"
  87:         target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
  88:         return target
  ```
- **Observed Behavior:** When `record_name` contains path traversal sequences like `../../escaped_file`, the path concatenation resolves to a location outside `self.audit_dir` and outside `self.session_root`. The file is written to arbitrary disk locations without triggering `validate_path`.

#### Finding 2: Session Directory Collision and Isolation Failure when `base_dir` is Provided
- **File:** `adapters/hermes/sandbox.py` (lines 30–40)
- **Code Snippet:**
  ```python
  30:         if base_dir is not None:
  31:             self.base_dir = Path(base_dir).resolve()
  32:         else:
  33:             # Check HERMES_HOME env var or default to output/hermes_sessions
  34:             hermes_home = os.environ.get("HERMES_HOME")
  35:             if hermes_home:
  36:                 self.base_dir = Path(hermes_home).resolve() / "sessions" / self.session_id / "harness9"
  37:             else:
  38:                 self.base_dir = Path("output/hermes_sessions").resolve() / self.session_id
  39: 
  40:         self.session_root = self.base_dir
  ```
- **Observed Behavior:** When a caller provides `base_dir` (e.g. `base_dir="/tmp/sessions"` or via `HermesBridge(base_output_dir=...)`), `self.session_root` is assigned directly to `self.base_dir` rather than `self.base_dir / self.session_id`. Consequently, multiple sandboxes created with different `session_id`s share the exact same root directory, corrupting and mixing audit records, renders, and workspace files across independent sessions.

#### Finding 3: Unhandled `TypeError` in `ProductionStateMachine.to_json()` for Non-Primitive Payload Values
- **File:** `src/orchestrator/state_machine.py` (lines 301–313, 371–374)
- **Code Snippet:**
  ```python
  371:     def to_json(self, indent: int = 2) -> str:
  372:         """Serialize state machine to JSON string."""
  373:         return json.dumps(self.to_dict(), indent=indent)
  ```
- **Observed Behavior:** When arbitrary dictionary payloads containing non-standard Python types (e.g., complex numbers, custom non-serializable objects, raw bytes, or non-ISO timestamp structures) are passed into `transition_to(target_state, payload=...)`, `self._context` stores the dict as-is. Calling `to_json()` crashes with `TypeError: Object of type <type> is not JSON serializable` instead of applying a fallback serializer (`default=str`).

---

## 2. Logic Chain

1. **State Machine Integrity & 400-Pair Matrix (Robust)**:
   - Probing all 400 possible pairs $(S_i, S_j)$ among all 20 states confirmed that `ProductionStateMachine` deterministically enforces `VALID_TRANSITIONS` and rejects invalid transitions and skips with `StateTransitionError`.
   - Terminal states `COMPLETED` and `CANCELLED` correctly lock out all further state transitions.
   - 100-iteration cycles (`RESEARCH_PLANNED <-> RESEARCH_IN_PROGRESS`, `SCRIPTING_IN_PROGRESS <-> SCRIPT_COMPLETED`) executed without state degradation.

2. **Security & Sandbox Isolation Invariant Breakdown**:
   - Invariant: `HermesSessionSandbox` must guarantee that all writes and filesystem operations are strictly confined within the session directory.
   - Observation 1 demonstrates that `save_audit_record` accepts un-sanitized relative names (`../../`), directly violating this boundary.
   - Observation 2 demonstrates that passing a custom `base_dir` eliminates session sub-directories, breaking multi-tenant isolation.
   - Therefore, the sandbox security model is currently vulnerable to path traversal and cross-session contamination.

3. **State Telemetry Serialization Invariant Breakdown**:
   - Invariant: State machine audit logs and context snapshots must be safely serializable to JSON at any point in the pipeline lifecycle.
   - Observation 3 demonstrates that `to_json()` raises an unhandled `TypeError` when complex/non-primitive objects are present in payload dicts.
   - Therefore, state machine telemetry can crash upstream hosts during error reporting or pipeline state export.

---

## 3. Caveats

- All 17 Pydantic schemas in `src/models/contracts.py` successfully passed all boundary, constraint, regex, and Unicode serialization tests without issues.
- `HermesBridge` and `handle_tool_call` schemas and dispatch logic passed standard and offline video generation checks.
- State transition graph topology is correct and robust against state jump attacks.

---

## 4. Conclusion

**Verdict: `REQUEST_CHANGES`**

Milestone M1 cannot be approved in its current state due to the three identified issues:
1. **[Security/High]** Path traversal in `HermesSessionSandbox.save_audit_record` allowing arbitrary file writes outside the audit directory.
2. **[Bug/Medium]** Missing `session_id` subpath in `HermesSessionSandbox.__init__` when `base_dir` is provided, causing cross-session data contamination.
3. **[Robustness/Low-Medium]** Missing default serializer in `ProductionStateMachine.to_json()` causing crashes on non-primitive payload fields.

### Required Remediations for `worker_m1`:
1. In `adapters/hermes/sandbox.py`:
   - In `__init__`, ensure `self.session_root` always includes `self.session_id`:
     `self.base_dir = Path(base_dir).resolve() / self.session_id` when `base_dir` is passed.
   - In `save_audit_record`, sanitize `record_name` (e.g. `Path(record_name).name`) or validate `self.validate_path(target)` to prevent path traversal outside `self.audit_dir`.
2. In `src/orchestrator/state_machine.py`:
   - In `to_json`, add `default=str` to `json.dumps(self.to_dict(), indent=indent, default=str)`.

---

## 5. Verification Method

To independently reproduce all adversarial findings:

```powershell
# Execute the M1 Adversarial Test Suite
$env:PYTHONPATH="g:\Finding-new-code\harness9"; & "g:\Finding-new-code\harness9\.venv\Scripts\python.exe" -m unittest tests.test_adversarial_m1
```

**Pass Condition for Invalidation of this Verdict:**
All 14 tests in `tests/test_adversarial_m1.py` must execute and pass with 0 failures and 0 errors:
```
Ran 14 tests in ...s
OK
```
