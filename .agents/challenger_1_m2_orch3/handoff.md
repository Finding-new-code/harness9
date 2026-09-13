# Milestone 2 Adversarial Review Report: Hermes Capability Bridge & Tool Surface

**Challenger:** `challenger_1_m2_orch3`  
**Milestone:** Milestone 2 — Hermes Capability Bridge & Native Tool Conversion  
**Verdict:** **REJECT** (3 Unhandled Crash Vulnerabilities Confirmed)  
**Date:** 2026-09-04  

---

## 1. Observation

1. **Test Execution & Repro Output**:
   Ran empirical stress test suite `tests/test_challenger_m2_stress.py` containing 26 adversarial test cases against `HermesCapabilityBridge` and the H9 model tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`):
   ```text
   .venv\Scripts\python.exe -m pytest tests/test_challenger_m2_stress.py -v
   ```
   **Output:**
   ```text
   =========================== short test summary info ===========================
   FAILED tests/test_challenger_m2_stress.py::TestH9GenerateScriptBoundaryStress::test_14_unhandled_target_duration_type_error
   FAILED tests/test_challenger_m2_stress.py::TestConcurrencyAndBridgeStress::test_25_bridge_discover_assets_none_queries_direct
   FAILED tests/test_challenger_m2_stress.py::TestConcurrencyAndBridgeStress::test_26_bridge_generate_script_claims_direct
   ======================== 3 failed, 23 passed in 16.50s ========================
   ```

2. **Vulnerability 1 — Unhandled Exception Leaked in `handle_h9_generate_script`**:
   - **Location**: `tools/h9_content_tools.py`, line 272:
     ```python
     270:     creator = args.get("creator") or {}
     271:     if not isinstance(creator, dict):
     272:         return tool_error("Parameter 'creator' must be an object/dictionary.")
     273:
     274:     duration = float(args.get("target_duration", 30.0))
     275:     format_aspect = str(args.get("format_aspect", "16:9"))
     276:
     277:     session_id = kwargs.get("session_id") or "default_session"
     278:
     279:     try:
     280:         bridge = get_capability_bridge(session_id=session_id)
     ```
   - **Verbatim Error**:
     ```text
     tools\h9_content_tools.py:272: in handle_h9_generate_script
         duration = float(args.get("target_duration", 30.0))
     E   ValueError: could not convert string to float: 'not-a-number'
     ```
   - When `target_duration` is provided as a non-numeric string (e.g. `"not-a-number"`, `"30s"`, `"approx 1 min"`) or explicit `None` (where `args.get("target_duration", 30.0)` evaluates to `None`), line 272 executes **before** the `try:` block at line 278.
   - This bypasses `tool_error` and allows a raw `ValueError` or `TypeError` to escape the handler, crashing direct callers.

3. **Vulnerability 2 — Unhandled `TypeError` in `bridge.discover_assets` on `suggested_visual_queries=None`**:
   - **Location**: `src/h9_runtime/bridge.py`, line 746:
     ```python
     741:         elif scene_ids or dossier:
     742:             queries = []
     743:             if dossier:
     744:                 if hasattr(dossier, "suggested_visual_queries"):
     745:                     queries = list(dossier.suggested_visual_queries)
     746:                 elif isinstance(dossier, dict):
     747:                     queries = list(dossier.get("suggested_visual_queries", []))
     ```
   - **Verbatim Error**:
     ```text
     src\h9_runtime\bridge.py:746: in discover_assets
         queries = list(dossier.get("suggested_visual_queries", []))
     E   TypeError: 'NoneType' object is not iterable
     ```
   - When a caller passes `dossier={"suggested_visual_queries": None}`, `dict.get("suggested_visual_queries", [])` returns `None` rather than the fallback empty list. Calling `list(None)` crashes with `TypeError`.

4. **Vulnerability 3 — Unhandled `TypeError` in `bridge.generate_script` on `claims=None`**:
   - **Location**: `src/h9_runtime/bridge.py`, line 458:
     ```python
     456:         if isinstance(dossier, dict):
     457:             claims = dossier.get("claims", [])
     458:             for c in claims:
     459:                 if "claim_id" not in c and "id" in c:
     ```
   - **Verbatim Error**:
     ```text
     src\h9_runtime\bridge.py:458: in generate_script
         for c in claims:
     E   TypeError: 'NoneType' object is not iterable
     ```
   - When `dossier={"claims": None}` is passed to `bridge.generate_script`, `dossier.get("claims", [])` returns `None`. The subsequent `for c in claims:` attempts iteration over `None`, immediately raising `TypeError`.

---

## 2. Logic Chain

1. **Claimed vs Observed Invariant**:
   - The worker claimed in `worker_m2_orch3/handoff.md`:
     > "4. Error Bounding: All handlers serialize responses using `tool_result` and catch exceptions via `tool_error`, preventing unbounded tracebacks from contaminating conversation history."
   - Observation 2 directly falsifies this invariant: `duration = float(args.get("target_duration", 30.0))` was placed outside the `try:` block in `handle_h9_generate_script`. Passing `target_duration="not-a-number"` or `target_duration=None` immediately raises an uncaught `ValueError`/`TypeError`.

2. **Domain Contract Fragility**:
   - `HermesCapabilityBridge` serves as the central integration boundary across all 7 runtime protocols.
   - Observations 3 and 4 demonstrate that `bridge.discover_assets` and `bridge.generate_script` assume dictionary fields with default lookups cannot evaluate to `None`.
   - In real Hermes agent interactions, model responses or upstream tool JSON payloads frequently contain explicit `null`/`None` values for optional fields like `"claims": null` or `"suggested_visual_queries": null`.
   - When these payloads reach the bridge, they trigger uncaught `TypeError: 'NoneType' object is not iterable` crashes.

3. **Required Remediations**:
   - **In `tools/h9_content_tools.py`**:
     Move the `target_duration` parsing inside the `try:` block or guard it explicitly:
     ```python
     target_duration_raw = args.get("target_duration", 30.0)
     try:
         duration = float(target_duration_raw) if target_duration_raw is not None else 30.0
     except (ValueError, TypeError):
         return tool_error("Parameter 'target_duration' must be a valid number.")
     ```
   - **In `src/h9_runtime/bridge.py` line 746 (`discover_assets`)**:
     Ensure queries fallback handles `None`:
     ```python
     queries_raw = dossier.get("suggested_visual_queries") if isinstance(dossier, dict) else None
     queries = list(queries_raw) if queries_raw is not None else []
     ```
   - **In `src/h9_runtime/bridge.py` line 457 (`generate_script`)**:
     Ensure claims fallback handles `None`:
     ```python
     claims_raw = dossier.get("claims")
     claims = claims_raw if isinstance(claims_raw, list) else []
     ```

---

## 3. Caveats

- 23 of 26 stress tests passed, demonstrating good architectural foundations:
  - Multi-threaded concurrency (`TestConcurrencyAndBridgeStress`) passed cleanly with 30 concurrent bridge instantiations and 12 parallel tool dispatches without deadlock or race conditions.
  - Procedural SVG asset generation and filesystem path collision handling (`test_19`, `test_20`) proved resilient.
  - `h9.research`, `h9.render`, and service gating (`check_h9_available`) cleanly reject missing and invalid payloads.
- The rejection is scoped specifically to the three unhandled exception crash sites identified.

---

## 4. Conclusion

**Verdict: REJECT**

Milestone 2 cannot be approved in its current state because:
1. `handle_h9_generate_script` violates the error-bounding contract by leaking unhandled `ValueError` and `TypeError` exceptions outside `tool_error`.
2. `HermesCapabilityBridge.discover_assets` and `HermesCapabilityBridge.generate_script` crash with `TypeError` when standard dictionary payloads contain `None` values for list fields.

Once the worker patches these 3 crash sites, all 26 tests in `tests/test_challenger_m2_stress.py` should pass alongside existing test suites.

---

## 5. Verification Method

To verify these findings independently:

```bash
# Execute the adversarial challenger stress suite:
.venv\Scripts\python.exe -m pytest tests/test_challenger_m2_stress.py -v
```

**Invalidation Conditions**:
- If all 26 tests in `tests/test_challenger_m2_stress.py` pass with 0 failures, the rejection is invalidated and Milestone 2 may be approved.
