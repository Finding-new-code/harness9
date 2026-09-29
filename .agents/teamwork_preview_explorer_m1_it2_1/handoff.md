# Technical Investigation & Remediation Report: Circular Import in `src/h9_runtime/content.py`

**Agent:** Remediation Explorer 1 — Milestone 1 (Iteration 2)  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_m1_it2_1`  
**Date:** 2026-09-13T17:41:00Z  
**Target:** `src/h9_runtime/content.py:37` (`Pipeline` circular import)  
**Status:** Completed Investigation & Exact Patch Formulated  

---

## 1. Observation

### 1.1 Source Code and Exact Locations
Direct inspection of `src/h9_runtime/content.py` reveals:
- **Line 37** contains an eager module-level import:
  ```python
  37: from src.orchestrator.pipeline import Pipeline
  ```
- **Line 345** in `DefaultContentRuntime.run_full_production` contains the sole runtime invocation of `Pipeline`:
  ```python
  344:             # Execute pipeline
  345:             pipeline = Pipeline(
  346:                 topic=brief.topic,
  347:                 output_dir=ws,
  348:                 offline=brief.offline_mode,
  349:                 format=brief.aspect_ratio,
  350:                 duration=brief.target_duration_seconds,
  351:             )
  352: 
  353:             success = pipeline.run()
  ```
- No other line in `src/h9_runtime/content.py` references `Pipeline`. Specifically, `Pipeline` is **never** used in type annotations, function signatures, docstrings, or class definitions. The return type of `run_full_production` is `ProductionResult`.

### 1.2 Git Status and Working Tree Diff
Running `git status` shows `modified: src/h9_runtime/content.py`.  
Running `git diff src/h9_runtime/content.py` against HEAD (`origin/dev` commit `bbd496d67`) reveals:
```diff
diff --git a/src/h9_runtime/content.py b/src/h9_runtime/content.py
index 43ef7b880..539462633 100644
--- a/src/h9_runtime/content.py
+++ b/src/h9_runtime/content.py
@@ -34,6 +34,7 @@ from src.models.contracts import (
     ScriptScene,
     ScriptBeat,
 )
+from src.orchestrator.pipeline import Pipeline
 from src.orchestrator.state_machine import (
     ProductionState,
     ProductionStateMachine,
@@ -341,7 +342,6 @@ class DefaultContentRuntime:
             )
 
             # Execute pipeline
-            from src.orchestrator.pipeline import Pipeline
             pipeline = Pipeline(
                 topic=brief.topic,
                 output_dir=ws,
```
In `origin/dev` HEAD, `from src.orchestrator.pipeline import Pipeline` was already lazily imported inside `run_full_production()`. Moving it to line 37 was an uncommitted edit introduced during Milestone 1.

### 1.3 Verbatim Import Cycle and Stack Trace
When importing `src.orchestrator` or executing `tests/test_state_machine.py`:
```pwsh
.venv\Scripts\python.exe -c "import src.orchestrator.pipeline"
```
Output:
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "G:\Finding-new-code\harness9\src\orchestrator\__init__.py", line 10, in <module>
    from src.orchestrator.pipeline import (
  File "G:\Finding-new-code\harness9\src\orchestrator\pipeline.py", line 19, in <module>
    from src.assets.pipeline import AssetPipeline
  File "G:\Finding-new-code\harness9\src\assets\__init__.py", line 3, in <module>
    from src.assets.deduplication import (
  File "G:\Finding-new-code\harness9\src\assets\deduplication.py", line 23, in <module>
    from src.models.contracts import H9BaseModel
  File "G:\Finding-new-code\harness9\src\models\__init__.py", line 73, in <module>
    from src.models.ir import (
  File "G:\Finding-new-code\harness9\src\models\ir.py", line 18, in <module>
    from src.h9_runtime.types import ProductionIR
  File "G:\Finding-new-code\harness9\src\h9_runtime\__init__.py", line 18, in <module>
    from src.h9_runtime.bridge import (
  File "G:\Finding-new-code\harness9\src\h9_runtime\bridge.py", line 24, in <module>
    from src.h9_runtime.content import (
  File "G:\Finding-new-code\harness9\src\h9_runtime\content.py", line 37, in <module>
    from src.orchestrator.pipeline import Pipeline
ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline' (most likely due to a circular import) (G:\Finding-new-code\harness9\src\orchestrator\pipeline.py)
```

Running `pytest tests/test_state_machine.py`:
```
ERROR collecting tests/test_state_machine.py
ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline'
1 error in 11.93s
```

### 1.4 Empirical In-Memory Patch Validation
Without altering any working-tree source files, we evaluated restoring the lazy import in-memory using a Python `importlib` meta-path hook. The results were:
- `tests/test_state_machine.py`: **10/10 passed** in 6.35s.
- `tests/test_h9_acceptance.py`: **44/44 passed** in 79.84s.
- `tests/test_contracts.py`: **12/12 passed** in 5.18s.
- `tests/test_editorial.py`, `tests/test_deduplication.py`, `tests/test_security_tokens.py`: **38/38 passed** in 4.78s.
- Total passing tests across sampled suites: **104/104 (100%)**.

---

## 2. Logic Chain

1. **Root Cause Mechanism**:
   - `src/orchestrator/__init__.py:10` unconditionally imports `Pipeline` from `src.orchestrator.pipeline`.
   - `src/orchestrator/pipeline.py` begins executing. At line 19 (`from src.assets.pipeline import AssetPipeline`), module execution diverges into the asset pipeline before `class Pipeline` is defined at line 32.
   - The dependency chain cascades:
     $$\text{pipeline.py:19} \to \text{assets} \to \text{deduplication} \to \text{contracts} \to \text{ir} \to \text{h9\_runtime} \to \text{bridge} \to \text{content.py}$$
   - When `content.py` executes line 37 (`from src.orchestrator.pipeline import Pipeline`), it requests the symbol `Pipeline` from `src.orchestrator.pipeline`, which is already registered in `sys.modules` but has only reached line 19.
   - Because `Pipeline` does not yet exist in the partially initialized module namespace, Python raises `ImportError`.

2. **Order-Dependent Masking**:
   - In `tests/test_h9_acceptance.py`, `src.h9_runtime` is imported first. By the time `content.py:37` runs, `src.orchestrator.pipeline` has not yet begun importing, so Python enters `src.orchestrator.pipeline` from `content.py`. In that execution order, `src.h9_runtime` is already in `sys.modules`, which masks the cycle.
   - However, any test or entry point that imports `src.orchestrator` first (such as `tests/test_state_machine.py:7` or `python -m src.orchestrator`) triggers the fatal cycle 100% of the time.

3. **Evaluation of Fix Options**:
   - **Option 1: Lazy import inside `DefaultContentRuntime.run_full_production` (Recommended)**
     - In `src/h9_runtime/content.py`, remove top-level line 37 and place `from src.orchestrator.pipeline import Pipeline` inside `run_full_production()` immediately before `pipeline = Pipeline(...)`.
     - *Evaluation*: This was the exact code in `origin/dev` HEAD commit `bbd496d67`. When modules are loaded, `src.h9_runtime.content` finishes importing without needing `src.orchestrator.pipeline`. The cycle is completely eliminated.
   - **Option 2: `if TYPE_CHECKING:` guard**
     - Moving the import to an `if TYPE_CHECKING:` block would prevent the import at module load time, but because `Pipeline` is instantiated at runtime on line 345, calling `run_full_production` would fail with `NameError: name 'Pipeline' is not defined` unless an internal import is also used. Furthermore, `Pipeline` is never used in type annotations. Thus, `TYPE_CHECKING` provides zero utility and Option 1 is strictly superior.

4. **Safety & Zero Regression**:
   - The fix touches only `src/h9_runtime/content.py`.
   - Restoring the lazy import restores full compatibility with both `test_state_machine.py` (10/10 passing) and `test_h9_acceptance.py` (44/44 passing).

---

## 3. Caveats

1. **Read-Only Explorer Boundary**:
   In adherence to the Explorer role constraints, no modifications were made directly to `src/h9_runtime/content.py`. The Worker agent must apply the recommended diff.
2. **Pre-Existing Unrelated Test Flake**:
   `tests/test_research.py::test_07_talking_points_duration_scaling` has a pre-existing assertion delta (`30.0 != 45.0`) present on `dev` before Milestone 1. It is unrelated to `content.py` or the epistemic verification specifications.

---

## 4. Conclusion & Recommended Action

### Recommendation
Worker M1 should revert `src/h9_runtime/content.py` line 37 by removing the top-level import and re-inserting the lazy import inside `DefaultContentRuntime.run_full_production()`.

Alternatively, because `src/h9_runtime/content.py` has no other modifications compared to `origin/dev` HEAD, running:
```pwsh
git checkout src/h9_runtime/content.py
```
reverts the file cleanly to its proven working state.

### Exact Patch Diff for Worker
```diff
diff --git a/src/h9_runtime/content.py b/src/h9_runtime/content.py
index 539462633..43ef7b880 100644
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
@@ -342,6 +341,7 @@ class DefaultContentRuntime:
             )
 
             # Execute pipeline
+            from src.orchestrator.pipeline import Pipeline
             pipeline = Pipeline(
                 topic=brief.topic,
                 output_dir=ws,
```

---

## 5. Verification Method

Once the Worker applies the patch, the following commands independently verify the remediation:

1. **Verify Isolated Module Import**:
   ```pwsh
   .venv\Scripts\python.exe -c "import src.orchestrator.pipeline; print('ORCHESTRATOR IMPORT SUCCESS')"
   .venv\Scripts\python.exe -c "import src.orchestrator.state_machine; print('STATE MACHINE IMPORT SUCCESS')"
   .venv\Scripts\python.exe -c "import src.h9_runtime.content; print('CONTENT RUNTIME IMPORT SUCCESS')"
   ```
   *Expected Result*: All print statements execute cleanly with exit code 0.

2. **Verify State Machine Unit Test Suite**:
   ```pwsh
   .venv\Scripts\python.exe -m pytest tests/test_state_machine.py -v
   ```
   *Expected Result*: `10 passed in ~6.5s (100%)`.

3. **Verify Full Acceptance & Contracts Regression Suite**:
   ```pwsh
   .venv\Scripts\python.exe -m pytest tests/test_contracts.py tests/test_h9_acceptance.py -q
   ```
   *Expected Result*: `56 passed in ~75s (100%)`.
