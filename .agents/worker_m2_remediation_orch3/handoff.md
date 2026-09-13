# Milestone 2 Remediation Handoff Report: Hermes Capability Bridge & Tool Surface

**Worker:** `worker_m2_remediation_orch3`  
**Parent:** `d832f8a0-ed17-43c0-91e0-f1ecca7ae126`  
**Milestone:** Milestone 2 Remediation (Iteration 2) — Hermes Capability Bridge & Native Tool Conversion  
**Status:** Complete & Verified  
**Date:** 2026-09-04  

---

## 1. Observation

### Initial Stress Suite Run & Repro Output
Ran empirical stress test suite `tests/test_challenger_m2_stress.py` with `.venv\Scripts\python.exe -m pytest tests/test_challenger_m2_stress.py -v`:

```text
=========================== short test summary info ===========================
FAILED tests/test_challenger_m2_stress.py::TestH9GenerateScriptBoundaryStress::test_14_unhandled_target_duration_type_error
FAILED tests/test_challenger_m2_stress.py::TestConcurrencyAndBridgeStress::test_25_bridge_discover_assets_none_queries_direct
FAILED tests/test_challenger_m2_stress.py::TestConcurrencyAndBridgeStress::test_26_bridge_generate_script_claims_direct
======================== 3 failed, 23 passed in 5.88s =========================
```

### Crash Site 1 — Leaked Unhandled `ValueError`/`TypeError` in `handle_h9_generate_script`
- **Location**: `tools/h9_content_tools.py:272`
- **Original Code**:
  ```python
  duration = float(args.get("target_duration", 30.0))
  format_aspect = str(args.get("format_aspect", "16:9"))

  session_id = kwargs.get("session_id") or "default_session"

  try:
      bridge = get_capability_bridge(session_id=session_id)
  ```
- **Verbatim Error**:
  ```text
  tools\h9_content_tools.py:272: in handle_h9_generate_script
      duration = float(args.get("target_duration", 30.0))
  E   ValueError: could not convert string to float: 'not-a-number'
  ```
- When `target_duration` is `"not-a-number"` or `None`, `float()` was executed outside the handler's `try:` block, bypassing `tool_error` and leaking an unhandled traceback.

### Crash Site 2 — Leaked `TypeError` in `bridge.discover_assets` on `suggested_visual_queries=None`
- **Location**: `src/h9_runtime/bridge.py:746`
- **Original Code**:
  ```python
  elif scene_ids or dossier:
      queries = []
      if dossier:
          if hasattr(dossier, "suggested_visual_queries"):
              queries = list(dossier.suggested_visual_queries)
          elif isinstance(dossier, dict):
              queries = list(dossier.get("suggested_visual_queries", []))
  ```
- **Verbatim Error**:
  ```text
  src\h9_runtime\bridge.py:746: in discover_assets
      queries = list(dossier.get("suggested_visual_queries", []))
  E   TypeError: 'NoneType' object is not iterable
  ```
- When `dossier` is a dictionary containing `{"suggested_visual_queries": None}`, `.get(..., [])` returns `None`. Calling `list(None)` crashes with `TypeError`.

### Crash Site 3 — Leaked `TypeError` in `bridge.generate_script` on `claims=None`
- **Location**: `src/h9_runtime/bridge.py:458`
- **Original Code**:
  ```python
  if isinstance(dossier, dict):
      claims = dossier.get("claims", [])
      for c in claims:
          if "claim_id" not in c and "id" in c:
  ```
- **Verbatim Error**:
  ```text
  src\h9_runtime\bridge.py:458: in generate_script
      for c in claims:
  E   TypeError: 'NoneType' object is not iterable
  ```
- When `dossier` contains `{"claims": None}`, `dossier.get("claims", [])` returns `None`. Iterating with `for c in claims:` triggers an uncaught `TypeError: 'NoneType' object is not iterable`.

---

## 2. Logic Chain

1. **Error Bounding & Input Validation Contract**:
   Model tools exposed to the agent must never leak unhandled exceptions. As demonstrated by Observation 1 and 2, parsing `target_duration` before entering `try:` allowed malformed inputs (non-numeric strings or explicit `None`) to escape unhandled. Moving `target_duration` conversion inside `try:` with explicit checks for booleans and `(ValueError, TypeError)` exception handling returning `tool_error("Parameter 'target_duration' must be a valid number of seconds.")` ensures strict error boundary compliance.

2. **Null-Safety on Dict Defaults in Runtime Bridge**:
   In runtime integration payloads, optional dictionary keys frequently arrive serialized as JSON `null` (evaluating to Python `None`). Using standard dict fallback syntax `d.get("key", [])` only falls back when the key is *missing*; when the key exists with value `None`, it returns `None`.
   - In `bridge.discover_assets`: changing to `queries = list(dossier.get("suggested_visual_queries") or [])` (and `dossier.suggested_visual_queries or []` for object attributes) guarantees an empty list when the field is `None`.
   - In `bridge.generate_script`: changing to `claims = dossier.get("claims") or []` (and guarding element type with `isinstance(c, dict)`) guarantees that `claims` is always an iterable list, preventing iteration crashes. Similarly, `key_takeaways` and `suggested_visual_queries` now fall back safely with `or []`.

3. **Verification via Regression and Stress Suites**:
   After applying these targeted, minimal modifications, the adversarial stress suite (`tests/test_challenger_m2_stress.py`) passed completely (26/26). All four existing suites (`test_h9_content_tools.py`, `test_adversarial_m2_tools.py`, `test_h9_runtime.py`, `test_registry.py`) also passed with 100% pass rate (105/105 tests), demonstrating zero regressions.

---

## 3. Caveats

No caveats. The fixes are surgical, fully compliant with the minimal change principle, and directly address the root causes identified by the challenger report without altering API contracts or tool semantics.

---

## 4. Conclusion

All 3 crash vulnerabilities identified in Milestone 2 have been remediated:
1. `handle_h9_generate_script` in `tools/h9_content_tools.py` now securely parses `target_duration` within the `try:` block, trapping invalid types and non-numeric inputs into clean `tool_error` responses.
2. `discover_assets` in `src/h9_runtime/bridge.py` safely handles `None` values for `suggested_visual_queries`.
3. `generate_script` in `src/h9_runtime/bridge.py` safely handles `None` values for `claims`, `key_takeaways`, and `suggested_visual_queries`.

The codebase is robust, thread-safe, and passes all 5 test suites (131 tests total).

---

## 5. Verification Method

### Test Commands and Results

1. **Adversarial Stress Test Suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_challenger_m2_stress.py -v
   ```
   *Result*: **26 passed in 5.86s** (100%)

2. **H9 Content Tools Suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py -v
   ```
   *Result*: **34 passed in 7.95s** (100%)

3. **Adversarial M2 Tools Suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_adversarial_m2_tools.py -v
   ```
   *Result*: **22 passed in 5.38s** (100%)

4. **H9 Runtime Protocol Suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_h9_runtime.py -v
   ```
   *Result*: **10 passed in 2.25s** (100%)

5. **Hermes Tool Registry Suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/tools/test_registry.py -v
   ```
   *Result*: **39 passed in 1.48s** (100%)

### Total Tests Verified: 131 passed, 0 failed.

### Files Modified and Inspected
- `g:\Finding-new-code\harness9\tools\h9_content_tools.py`
- `g:\Finding-new-code\harness9\src\h9_runtime\bridge.py`

### Invalidation Conditions
- Any test failure in `tests/test_challenger_m2_stress.py`.
- Any unhandled exception escaping `handle_h9_generate_script` when `target_duration` is invalid or `None`.
- Any unhandled `TypeError` in `bridge.discover_assets` or `bridge.generate_script` when list fields are `None`.
