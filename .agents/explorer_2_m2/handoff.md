# Handoff Report: Circular Import Investigation (M2)

**Agent:** explorer_2_m2  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\explorer_2_m2`  
**Date:** 2026-09-13  
**Target:** Circular Import in `src/h9_runtime/content.py:37`  
**Deliverable:** `analysis.md`, `handoff.md`  
**Handoff Type:** Hard (Task complete)  

---

## 1. Observation

1. **Test Failure in Isolation**:
   Running `.venv\Scripts\pytest.exe tests/test_state_machine.py` produces:
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
   E   ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline' (most likely due to a circular import) (G:\Finding-new-code\harness9\src\orchestrator\pipeline.py)
   =========================== short test summary info ===========================
   ERROR tests/test_state_machine.py
   !!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
   ============================== 1 error in 2.24s ===============================
   ```

2. **Source Code Inspection (`src/h9_runtime/content.py`)**:
   - Line 37: `from src.orchestrator.pipeline import Pipeline`
   - Line 345: `pipeline = Pipeline(` inside `DefaultContentRuntime.run_full_production()`
   - `Pipeline` is not referenced in the `ContentRuntime` Protocol (lines 48–105), not in any type annotations, and not in any other class method.
   - Precedent: Line 275 already uses lazy import: `from src.models.ir import compile_script_to_ir`.

3. **In-Memory Fix Verification**:
   - Executing `python -u .agents/explorer_2_m2/test_fix_in_memory.py` with in-memory patched `content.py`:
     ```
     Testing isolated import of src.orchestrator.state_machine...
     Successfully imported state_machine! Initial state: ProductionState.CREATED
     Testing isolated import of src.orchestrator.pipeline...
     Successfully imported Pipeline! Class: <class 'src.orchestrator.pipeline.Pipeline'>
     Running test_state_machine suite with patched in-memory content.py...
     Ran 10 tests in 0.003s
     OK
     ALL TESTS PASSED IN ISOLATION!
     ```
   - Executing `python -u .agents/explorer_2_m2/test_acceptance_with_fix.py`:
     ```
     Ran 44 tests in 37.325s
     OK
     ALL 44 ACCEPTANCE TESTS PASSED (0 REGRESSIONS)!
     ```

4. **Codebase-Wide Module Isolation Scan**:
   - An automated scan of all 72 modules under `src/` revealed that top-level eager imports in `content.py` caused circular dependencies across:
     - `src.orchestrator.*` (4 modules)
     - `src.editorial.*` (6 modules)
     - `src.research.*` (4 modules)
   - Applying lazy imports in `content.py` to `Pipeline`, `ProductionStateMachine`, `EditorialEngine`, and `ResearchEngine` resolved 52/72 modules.
   - The remaining 20 modules failed due to a secondary circular dependency between `adapters/hyperframes/adapter.py:17` and `src/hyperframes/generator.py:25`.

---

## 2. Logic Chain

1. *From Observation 1*: Importing `src.orchestrator.state_machine` in `tests/test_state_machine.py` requires Python to load `src.orchestrator.__init__.py` first.
2. *From Observation 1*: `src/orchestrator/__init__.py:10` imports `src.orchestrator.pipeline`, making `src.orchestrator.pipeline` partially initialized.
3. *From Observation 1*: `src.orchestrator.pipeline` imports `src.assets.pipeline`, which transitively loads `src.models.ir` and `src.h9_runtime.content`.
4. *From Observation 1 & 2*: At `content.py:37`, `from src.orchestrator.pipeline import Pipeline` attempts to fetch `Pipeline` from `sys.modules['src.orchestrator.pipeline']`, which is incomplete and does not yet have the `Pipeline` class defined, raising an `ImportError`.
5. *From Observation 2*: Because `Pipeline` is only needed at runtime when `run_full_production()` is invoked, top-level binding at module load time is unnecessary and harmful.
6. *From Observation 3*: Moving the import inside `run_full_production()` completely removes `src.orchestrator.pipeline` from the module initialization chain of `content.py`.
7. *From Observation 3*: Test isolation is achieved: `tests/test_state_machine.py` runs and passes 100% in isolation with zero errors, and `tests/test_h9_acceptance.py` passes 44/44 without regression.

---

## 3. Caveats

1. **Secondary Circular Dependency**: A separate, orthogonal circular import exists between `adapters/hyperframes/adapter.py` and `src/hyperframes/generator.py` (caused by `adapters/hyperframes/adapter.py:17` eagerly importing `HyperFramesGenerator` and `src/hyperframes/generator.py:25` importing `BrandGuidelines` from `src.scriptwriting.generator`). This does not impact `tests/test_state_machine.py` or `tests/test_h9_acceptance.py`, but was documented in `analysis.md` for future cleanup.
2. **Read-Only Exploration**: Under the assigned explorer persona, source files in `src/` were not directly modified on disk. All verification was conducted through non-destructive in-memory AST/importlib hooks.

---

## 4. Conclusion

1. The circular import error during isolated execution of `tests/test_state_machine.py` is definitively diagnosed to `src/h9_runtime/content.py:37`.
2. The fix is strictly localized to `src/h9_runtime/content.py`:
   - Delete line 37 (`from src.orchestrator.pipeline import Pipeline`).
   - Add `from src.orchestrator.pipeline import Pipeline` inside `DefaultContentRuntime.run_full_production()` at line 345 right before `pipeline = Pipeline(...)`.
3. (Recommended Hardening): Also move `from src.research.engine import ResearchEngine` into `plan_research()`, `from src.editorial import EditorialEngine` into `evaluate_angles()`, and `from src.orchestrator.state_machine import ProductionState, ProductionStateMachine` into `run_full_production()`.

---

## 5. Verification Method

To independently verify the fix once implemented on disk by a worker:

1. **Execute isolated state machine tests**:
   ```bash
   .venv\Scripts\pytest.exe tests/test_state_machine.py -v
   ```
   *Expected outcome:* 10 passed, 0 failed, 0 errors.

2. **Execute regression acceptance suite**:
   ```bash
   .venv\Scripts\pytest.exe tests/test_h9_acceptance.py -v
   ```
   *Expected outcome:* 44 passed, 0 failed, 0 errors.

3. **Verify isolated module imports**:
   ```bash
   .venv\Scripts\python.exe -c "import src.orchestrator.state_machine; print('state_machine OK')"
   .venv\Scripts\python.exe -c "import src.orchestrator.pipeline; print('pipeline OK')"
   .venv\Scripts\python.exe -c "import src.h9_runtime.content; print('content OK')"
   ```
   *Expected outcome:* All exit with code 0 and print OK.

4. **Invalidation Condition**:
   If any import of `src.orchestrator.state_machine` raises `ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline'`, the import was not successfully moved inside `run_full_production()`.
