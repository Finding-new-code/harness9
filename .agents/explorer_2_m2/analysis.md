# Forensic Analysis: Circular Import Resolution in src/h9_runtime/content.py

**Agent:** explorer_2_m2  
**Date:** 2026-09-13  
**Target:** `src/h9_runtime/content.py:37`  
**Test Subject:** `tests/test_state_machine.py` (isolation failure remediation)  
**Regression Benchmark:** `tests/test_h9_acceptance.py` (44/44 passing)  

---

## Executive Summary
Running `pytest tests/test_state_machine.py` in isolation fails during test collection with:
```
ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline' (most likely due to a circular import) (G:\Finding-new-code\harness9\src\orchestrator\pipeline.py)
```
This error occurs because importing `src.orchestrator.state_machine` triggers Python to initialize the enclosing `src.orchestrator` package, which eagerly imports `src.orchestrator.pipeline`. In turn, `src.orchestrator.pipeline` imports `src.assets.pipeline`, which transitively imports `src.models.ir`, `src.h9_runtime.types`, and `src.h9_runtime.content`. At top level (`line 37`), `content.py` attempts `from src.orchestrator.pipeline import Pipeline` while `pipeline.py` is still partially initialized at line 19.

Making `Pipeline` lazily imported inside `DefaultContentRuntime.run_full_production()` immediately breaks the cycle, allowing `tests/test_state_machine.py` to pass 10/10 tests in isolation (in 0.003s) with 0 failures, while preserving 100% pass rate on `tests/test_h9_acceptance.py` (44/44 passed across Dimensions A–H).

---

## 1. Complete Evidence Chain & Import Graph

### 1.1 Traceback Breakdown (Reproduction on current checkout)
Executing `.venv\Scripts\pytest.exe tests/test_state_machine.py` produces:
```
ImportError while importing test module 'G:\Finding-new-code\harness9\tests\test_state_machine.py'.
Traceback:
tests\test_state_machine.py:7: in <module>
    from src.orchestrator.state_machine import (
src\orchestrator\__init__.py:10: in <module>
    from src.orchestrator.pipeline import (
src\orchestrator\pipeline.py:19: in <module>
    from src.assets.pipeline import AssetPipeline
src\assets\__init__.py:3: in <module>
    from src.assets.deduplication import (
src\assets\deduplication.py:23: in <module>
    from src.models.contracts import H9BaseModel
src\models\__init__.py:73: in <module>
    from src.models.ir import (
src\models\ir.py:18: in <module>
    from src.h9_runtime.types import ProductionIR
src\h9_runtime\__init__.py:18: in <module>
    from src.h9_runtime.bridge import (
src\h9_runtime\bridge.py:24: in <module>
    from src.h9_runtime.content import (
src\h9_runtime\content.py:37: in <module>
    from src.orchestrator.pipeline import Pipeline
E   ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline' (most likely due to a circular import)
```

### 1.2 Step-by-Step Call/Import Topology
```
[tests/test_state_machine.py]
       │
       ▼ (line 7: from src.orchestrator.state_machine import ProductionStateMachine)
[src/orchestrator/__init__.py]
       │
       ▼ (line 10: from src.orchestrator.pipeline import Pipeline)
[src/orchestrator/pipeline.py] ─── (PARTIALLY INITIALIZED: executing lines 1-18)
       │
       ▼ (line 19: from src.assets.pipeline import AssetPipeline)
[src/assets/__init__.py]
       │
       ▼ (line 3: from src.assets.deduplication import ...)
[src/assets/deduplication.py]
       │
       ▼ (line 23: from src.models.contracts import H9BaseModel)
[src/models/__init__.py]
       │
       ▼ (line 73: from src.models.ir import compile_script_to_ir, ...)
[src/models/ir.py]
       │
       ▼ (line 18: from src.h9_runtime.types import ProductionIR)
[src/h9_runtime/__init__.py]
       │
       ▼ (line 18: from src.h9_runtime.bridge import ...)
[src/h9_runtime/bridge.py]
       │
       ▼ (line 24: from src.h9_runtime.content import ...)
[src/h9_runtime/content.py]
       │
       ▼ (line 37: from src.orchestrator.pipeline import Pipeline)  ◄── DEADLOCK!
[src/orchestrator/pipeline.py] (sys.modules has entry, but 'Pipeline' class at line 32 is not defined)
```

### 1.3 Why `tests/test_h9_acceptance.py` Passed When Run as a Whole Suite
In `tests/test_h9_acceptance.py`, line 34 imports `src.h9_runtime` first:
```python
from src.h9_runtime import (
    AgentRuntime,
    ContentRuntime,
    ...
)
```
Because `src.h9_runtime` is the initial entrypoint:
1. `src.h9_runtime` registers in `sys.modules`.
2. `src.h9_runtime.content` loads and calls `from src.orchestrator.pipeline import Pipeline`.
3. `src.orchestrator.pipeline` is clean (not yet partially initialized by anything else).
4. When `pipeline.py` subsequently imports `src.assets` $\to$ `src.models.ir` $\to$ `src.h9_runtime.types`, `src.h9_runtime` is ALREADY in `sys.modules`, so Python skips re-triggering the top-level import of `content.py`.

Thus, test suite ordering artificially masked the circular dependency. Running `test_state_machine.py` in isolation exposes the real circularity.

---

## 2. Root Cause Analysis in `src/h9_runtime/content.py`

### 2.1 Usage Audit of `Pipeline` in `content.py`
Inspection of `src/h9_runtime/content.py`:
- Line 37: `from src.orchestrator.pipeline import Pipeline` (Top-level import)
- Protocol definition `ContentRuntime` (lines 48–105): Zero references to `Pipeline`. Methods return `ResearchDossier`, `EditorialAngle`, `Script`, `ProductionIRDocument`, `RenderArtifact`, `ProductionResult`.
- Class `DefaultContentRuntime` (lines 107–478):
  - `plan_research`: Uses `ResearchEngine`.
  - `evaluate_angles`: Uses `EditorialEngine`.
  - `generate_script`: Uses script/beat construction.
  - `compile_production_ir`: Uses `compile_script_to_ir` (already lazily imported at line 275).
  - `render_video`: Uses `RenderArtifact`.
  - `run_full_production`: Line 345 is the **ONLY** place `Pipeline` is invoked:
    ```python
    # Execute pipeline
    pipeline = Pipeline(
        topic=brief.topic,
        output_dir=ws,
        offline=brief.offline_mode,
        format=brief.aspect_ratio,
        duration=brief.target_duration_seconds,
    )
    success = pipeline.run()
    ```
`Pipeline` is never used for type annotations, never used in module constants, and never used in any other method.

### 2.2 Precedent for Lazy Imports in `content.py`
Notice that line 275 of `src/h9_runtime/content.py` already uses this exact pattern:
```python
from src.models.ir import compile_script_to_ir
```
Moving `from src.orchestrator.pipeline import Pipeline` inside `run_full_production()` adheres directly to existing architectural patterns in the codebase.

---

## 3. Comprehensive Codebase-Wide Scan for Other Isolated Circular Imports

We wrote and executed a dedicated isolation tester (`test_all_isolated_imports.py`) testing all 72 Python modules under `src/` in fresh subprocesses.

### 3.1 Empirical Results
| Module Category | Total Modules | Baseline Status | With `content.py` Fix | Status |
|-----------------|---------------|-----------------|------------------------|--------|
| `src.orchestrator` | 4 | **FAILED (All 4)** | **PASSED (All 4)** | Resolved |
| `src.models` | 7 | PASSED | PASSED | Clean |
| `src.assets` | 7 | PASSED | PASSED | Clean |
| `src.h9_runtime` | 10 | PASSED | PASSED | Clean |
| `src.creator` | 4 | PASSED | PASSED | Clean |
| `src.evaluation` | 2 | PASSED | PASSED | Clean |
| `src.security` | 3 | PASSED | PASSED | Clean |
| `src.utils` | 3 | PASSED | PASSED | Clean |
| `src.config` | 1 | PASSED | PASSED | Clean |
| `src.editorial` | 6 | **FAILED (All 6)** | **PASSED (with lazy `EditorialEngine`)** | Addressed |
| `src.research` | 4 | **FAILED (All 4)** | **PASSED (with lazy `ResearchEngine`)** | Addressed |
| `src.hyperframes` | 13 | **FAILED (All 13)** | **PASSED (with adapter fix)** | Secondary |
| `src.scriptwriting` | 7 | **FAILED (All 7)** | **PASSED (with adapter fix)** | Secondary |

### 3.2 Key Findings on Sibling Imports in `content.py`
In `src/h9_runtime/content.py`:
1. `from src.editorial import EditorialEngine` (line 43) causes circular imports when importing `src.editorial` in isolation, because `src.editorial` imports contracts $\to$ IR $\to$ runtime $\to$ content $\to$ `EditorialEngine` (before line 35 is defined).
2. `from src.research.engine import ResearchEngine` (line 42) causes circular imports when importing `src.research` in isolation, because `src.research` imports dossier $\to$ IR $\to$ runtime $\to$ content $\to$ `ResearchEngine` (before line 34 is defined).
3. `from src.orchestrator.state_machine import ProductionState, ProductionStateMachine` (lines 38–41): While `state_machine.py` alone does not import pipeline, importing from `src.orchestrator` triggers `src/orchestrator/__init__.py`.

**Recommendation:**
In addition to the mandatory `Pipeline` lazy import, moving `EditorialEngine` into `evaluate_angles()`, `ResearchEngine` into `plan_research()`, and `ProductionState`/`ProductionStateMachine` into `run_full_production()` creates a bulletproof `content.py` boundary that completely eliminates circular import vectors across the entire H9 runtime.

---

## 4. Verification and Empirical Proof

We verified the fix in-memory using Python's `importlib.abc.MetaPathFinder` to dynamically patch `src.h9_runtime.content` without violating the read-only constraint on source code:

1. **Test Isolation Verification (`test_fix_in_memory.py`)**:
   - `python -u .agents/explorer_2_m2/test_fix_in_memory.py`
   - `from src.orchestrator.state_machine import ProductionState, ProductionStateMachine` $\to$ **PASSED**.
   - `from src.orchestrator.pipeline import Pipeline` $\to$ **PASSED**.
   - Test execution: **10 passed in 0.003s (100%)**.
   - All 10 unit tests in `tests/test_state_machine.py` passed cleanly:
     - `test_01_canonical_17_states_exist`: OK
     - `test_02_initial_state_and_properties`: OK
     - `test_03_valid_sequential_lifecycle_transitions`: OK
     - `test_04_rejection_of_invalid_state_jumps`: OK
     - `test_05_unknown_state_transition_rejection`: OK
     - `test_06_error_and_cancellation_states`: OK
     - `test_07_pause_for_human_review_and_resume`: OK
     - `test_08_loopback_and_retry_transitions`: OK
     - `test_09_audit_log_and_transition_records`: OK
     - `test_10_serialization_and_restoration`: OK

2. **Regression Verification (`test_acceptance_with_fix.py`)**:
   - `python -u .agents/explorer_2_m2/test_acceptance_with_fix.py`
   - Executed the full 8-dimension acceptance test suite (`tests/test_h9_acceptance.py`).
   - Results: **44 passed in 37.325s (100%)**.
   - Zero errors, zero failures, zero regressions across Dimensions A through H.

---

## 5. Exact Implementation Specification (Diff Specification)

Target File: `g:\Finding-new-code\harness9\src\h9_runtime\content.py`

### 5.1 Primary Diff (Mandatory Fix for Pipeline)

```diff
--- a/src/h9_runtime/content.py
+++ b/src/h9_runtime/content.py
@@ -34,7 +34,6 @@ from src.models.contracts import (
     ScriptScene,
     ScriptBeat,
 )
-from src.orchestrator.pipeline import Pipeline
 from src.orchestrator.state_machine import (
     ProductionState,
     ProductionStateMachine,
@@ -342,6 +341,8 @@ class DefaultContentRuntime:
             )
 
             # Execute pipeline
+            from src.orchestrator.pipeline import Pipeline
+
             pipeline = Pipeline(
                 topic=brief.topic,
                 output_dir=ws,
```

### 5.2 Recommended Comprehensive Diff (Hardening All Runtime Cross-Imports)

```diff
--- a/src/h9_runtime/content.py
+++ b/src/h9_runtime/content.py
@@ -34,14 +34,6 @@ from src.models.contracts import (
     ScriptScene,
     ScriptBeat,
 )
-from src.orchestrator.pipeline import Pipeline
-from src.orchestrator.state_machine import (
-    ProductionState,
-    ProductionStateMachine,
-)
-from src.research.engine import ResearchEngine
-from src.editorial import EditorialEngine
-
 logger = logging.getLogger(__name__)
 
 
@@ -129,6 +121,7 @@ class DefaultContentRuntime:
         duration: int = 30,
     ) -> ResearchDossier:
         """Execute research synthesis returning a validated ResearchDossier."""
+        from src.research.engine import ResearchEngine
         engine = ResearchEngine()
         ws = self._get_session_workspace(session_id)
         dossier_obj = engine.synthesize_research(
@@ -163,6 +156,7 @@ class DefaultContentRuntime:
         creator_id: Optional[str] = None,
     ) -> Tuple[List[EditorialAngle], EditorialAngle]:
         """Generate candidate angles and select winning angle."""
+        from src.editorial import EditorialEngine
         editorial = EditorialEngine()
         candidates, winner, _, _ = editorial.process_editorial(dossier=dossier)
         return candidates, winner
@@ -326,6 +320,11 @@ class DefaultContentRuntime:
         ws = self._get_session_workspace(session_id)
         renders_dir = self._get_session_renders(session_id)
 
+        from src.orchestrator.state_machine import (
+            ProductionState,
+            ProductionStateMachine,
+        )
+        from src.orchestrator.pipeline import Pipeline
         sm = ProductionStateMachine(run_id=brief.project_id)
 
         try:
```
