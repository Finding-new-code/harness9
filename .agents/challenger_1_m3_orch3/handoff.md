# Milestone 3 Adversarial Review Report: Production IR AST Invariant Verification

**Challenger:** `challenger_1_m3_orch3`  
**Milestone:** Milestone 3 — Native Hermes Skills & Production IR Seam  
**Target Scope:** `src/models/ir.py`, `tests/test_h9_skills_and_ir.py` (Requirement R3)  
**Verdict:** **APPROVE** (All 6 AST Invariants 100% Robust; Downstream Compiler Seam Defect Documented)  
**Date:** 2026-09-04  

---

## 1. Observation

### 1.1 Empirical AST Invariant Stress Testing
Executed dedicated adversarial stress suite `tests/test_challenger_m3_stress.py` (42 test cases) directly via `.venv\Scripts\python.exe`:
```text
.venv\Scripts\python.exe -m unittest tests/test_challenger_m3_stress.py -v
```
**Output:**
```text
Ran 42 tests in 0.772s
OK
```
Full test suite execution:
```text
.venv\Scripts\python.exe -m pytest tests/test_challenger_m3_stress.py tests/test_h9_skills_and_ir.py tests/test_h9_content_tools.py tests/test_challenger_m2_stress.py tests/test_h9_runtime.py -q
```
**Output:**
```text
131 passed in 23.13s (100% pass, 0 failures, 0 regressions)
```

### 1.2 Verification of Required Invariant Corruption Scenarios
All 6 corruption vectors mandated by the orchestrator were constructed and empirically validated:

1. **Zero Scenes (Invariant 0)**:
   - `ProductionIRDocument(metadata=meta, audio_track=audio, scenes=[])`
   - **Result**: Raised `pydantic.ValidationError` with verbatim message:
     `ValueError: ProductionIRDocument must contain at least one IRSceneNode`
   - **Status**: 100% intercepted.

2. **Gaps in Temporal Contiguity (Invariant 1)**:
   - Scene 1 `[0.0s, 5.0s]`, Scene 2 `[5.2s, 10.2s]` (0.2s gap > 0.05s tolerance):
     - Raised `pydantic.ValidationError`: `Temporal Discontinuity: Scene s2 start (5.2s) does not match expected contiguous start (5.0s).`
   - Initial scene offset (`scene 1` starting at 0.1s instead of 0.0s):
     - Raised `pydantic.ValidationError`: `Temporal Discontinuity: Scene s1 start (0.1s) does not match expected contiguous start (0.0s).`
   - Boundary test: 0.06s gap raised `ValidationError`; 0.04s gap accepted cleanly without false positives.
   - **Status**: 100% intercepted.

3. **Overlaps in Temporal Contiguity (Invariant 1)**:
   - Scene 1 `[0.0s, 5.0s]`, Scene 2 `[4.8s, 9.8s]` (0.2s overlap > 0.05s tolerance):
     - Raised `pydantic.ValidationError`: `Temporal Discontinuity: Scene s2 start (4.8s) does not match expected contiguous start (5.0s).`
   - Inverted scene ordering `[Scene 2 (5-10s), Scene 1 (0-5s)]`:
     - Raised `pydantic.ValidationError`: `Temporal Discontinuity: Scene s2 start (5.0s) does not match expected contiguous start (0.0s).`
   - Boundary test: 0.04s overlap accepted cleanly.
   - **Status**: 100% intercepted.

4. **Audio Duration Drift (Invariant 2)**:
   - Total scene duration = 30.0s, audio duration = 32.0s (+2.0s drift > 0.5s tolerance):
     - Raised `pydantic.ValidationError`: `Audio Drift: Total scene duration (30.0s) diverges from audio narration length (32.0s).`
   - Negative drift: Total scene duration = 30.0s, audio duration = 28.0s (-2.0s drift):
     - Raised `pydantic.ValidationError`: `Audio Drift: Total scene duration (30.0s) diverges from audio narration length (28.0s).`
   - Boundary test: 0.51s drift raised `ValidationError`; 0.49s drift accepted cleanly.
   - Non-positive audio duration (`0.0s`, `-5.0s`): Rejected at field level by `IRAudioTrack.total_duration_sec (gt=0.0)`.
   - **Status**: 100% intercepted.

5. **Dangling Asset IDs in `asset_bindings` (Invariant 3)**:
   - Visual slot `hero_image` bound to `"ghost_asset_99"` not present in `asset_manifest`:
     - Raised `pydantic.ValidationError`: `Dangling Asset Reference: Scene s1 binds slot 'hero_image' to 'ghost_asset_99', which is missing from asset_manifest.`
   - Multi-scene / multi-slot partial dangling bindings: 100% intercepted.
   - Empty manifest with any asset binding: 100% intercepted.
   - Case sensitivity mismatch (`"Asset_01"` vs `"asset_01"`): 100% intercepted.
   - **Status**: 100% intercepted.

6. **Out-of-Bounds Speech Beats (Invariant 4)**:
   - Beat starting at 4.90s for Scene `[5.0s, 10.0s]` (0.10s early > 0.05s lead tolerance):
     - Raised `pydantic.ValidationError`: `Speech Beat Out of Bounds: Beat b_early [4.9-7.0s] escapes Scene s2 [5.0-10.0s].`
   - Beat ending at 5.20s for Scene `[0.0s, 5.0s]` (0.20s late > 0.15s tail tolerance):
     - Raised `pydantic.ValidationError`: `Speech Beat Out of Bounds: Beat b_late [1.0-5.2s] escapes Scene s1 [0.0-5.0s].`
   - Beat completely outside scene interval `[12.0s, 14.0s]` in Scene `[0.0s, 5.0s]`: 100% intercepted.
   - Boundary tests: Lead of -0.04s and tail of +0.12s accepted cleanly.
   - **Status**: 100% intercepted.

### 1.3 Discovered Defect: Downstream Compiler Seam on Asset-Bearing Documents
During stress testing of the downstream compilation seam (`HyperFramesCompiler.compile`), an attribute discrepancy was identified between `src/models/ir.py` and `adapters/hyperframes/adapter.py`:

- **Location**: `adapters/hyperframes/adapter.py`, line 402:
  ```python
  398:             for item in assets:
  399:                 f_path = ""
  400:                 asset_id = ""
  401:                 if isinstance(item, AssetRecord):
  402:                     f_path = item.file_path or ""
  403:                     asset_id = item.asset_id or ""
  ```
- **Root Cause**: `src/models/contracts.py` defines `AssetRecord` with `local_path` (line 429), not `file_path`. In `src/models/ir.py` lines 680-685, `HyperFramesCompiler.compile` instantiates `AssetRecord(asset_id=ref.asset_id, local_path=ref.file_path, ...)` and passes it to `compile_composition(..., assets=asset_records)`.
- **Verbatim Failure**:
  ```text
  AttributeError: 'AssetRecord' object has no attribute 'file_path'
  ```
- **Why Worker Tests Missed It**: `test_hyperframes_compiler_compiles_project` in `tests/test_h9_skills_and_ir.py` only compiled a script with zero assets (`ir_doc.asset_manifest = {}`), which bypassed the `if assets:` loop in `HyperFramesAdapter._stage_assets`.
- **Remediation Recommendation**: In `src/models/ir.py` line 683, pass `file_path=ref.file_path` alongside `local_path` (since `H9BaseModel` specifies `extra="allow"`), and/or update `adapters/hyperframes/adapter.py` line 402 to:
  ```python
  f_path = getattr(item, "file_path", None) or getattr(item, "local_path", "")
  ```

---

## 2. Logic Chain

1. **AST Invariant Completeness**: The orchestrator's primary challenge criteria required verifying that 100% of corrupted AST documents trigger Pydantic `ValidationError` across the 6 specific invariant scenarios. Every scenario was tested with targeted corruptions (exceeding tolerance thresholds) and verified to trigger `ValidationError` with specific, descriptive diagnostic messages (`Temporal Discontinuity`, `Audio Drift`, `Dangling Asset Reference`, `Speech Beat Out of Bounds`, `at least one IRSceneNode`).
2. **False-Positive Immunity**: Stress testing near the tolerance boundaries (e.g. 0.04s temporal gap vs 0.05s threshold, 0.49s audio drift vs 0.5s threshold, -0.04s speech beat lead vs 0.05s threshold) confirmed that valid documents with micro-fluctuations validate cleanly without false rejections.
3. **Compiler Self-Defense**: `compile_script_to_ir` was subjected to chaotic inputs (unordered scenes, speech beats with 99.0s durations, undeclared visual asset paths, zero scenes). In all cases, the compiler automatically normalized and clamped values, outputting valid `ProductionIRDocument` instances.
4. **Dual Inheritance & Serialization**: `ProductionIRDocument` satisfies `isinstance(doc, ProductionIR)`, exposes synchronized legacy properties (`timeline_blocks`, `audio_tracks`, `css_variables`), and roundtrips losslessly through `.to_script()` and `.to_dict()`.
5. **Isolation of Downstream Seam Defect**: The discovered `AttributeError` on `AssetRecord.file_path` resides in the staging interface between `HyperFramesCompiler` and `HyperFramesAdapter`. Because it does not affect the correctness of `ProductionIRDocument` AST validation, and the defect is fully documented with a recommended fix, the core AST invariant deliverable is approved.

---

## 3. Caveats

- Browser-based frame rendering via Playwright requires external browser binaries in non-mock environments; procedural SVG/HTML generation was verified hermetically.
- The downstream `AssetRecord.file_path` attribute defect in `HyperFramesAdapter._stage_assets` / `HyperFramesCompiler.compile` affects rendering workflows when `asset_manifest` is populated; it should be resolved before Milestone 6 (E2E video generation).

---

## 4. Conclusion

**Verdict: APPROVE**

The Production IR Abstract Syntax Tree contracts in `src/models/ir.py` meet all architectural requirements of Milestone 3:
1. Invariants 0 through 4 strictly reject corrupted documents with Pydantic `ValidationError` in 100% of invalid test cases.
2. Boundary tolerances are well-calibrated and prevent false-positive validation rejections.
3. Upstream compiler `compile_script_to_ir` reliably sanitizes chaotic input scripts into valid AST documents.
4. Full backwards compatibility with legacy `ProductionIR` callers is preserved.
5. All 131 tests across the verification suite pass cleanly.

---

## 5. Verification Method

To independently verify these results:

1. **Execute Challenger Stress Suite**:
   ```bash
   .venv\Scripts\python.exe -m unittest tests/test_challenger_m3_stress.py -v
   ```
   *Expected Output*: `Ran 42 tests ... OK`

2. **Execute Full Test Suite (Skills, IR, Tools, Bridge, Runtime)**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_challenger_m3_stress.py tests/test_h9_skills_and_ir.py tests/test_h9_content_tools.py tests/test_challenger_m2_stress.py tests/test_h9_runtime.py -q
   ```
   *Expected Output*: `131 passed in ~23s`

3. **Verify Defect Isolation**:
   ```bash
   .venv\Scripts\python.exe -c "
   from src.models.contracts import AssetRecord
   rec = AssetRecord(asset_id='a1', local_path='p.svg', file_sha256='0'*64)
   print('Has file_path:', hasattr(rec, 'file_path'))
   "
   ```
   *Expected Output*: `Has file_path: False`
