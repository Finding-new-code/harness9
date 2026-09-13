# Review & Adversarial Challenge Report — Milestone 3: Production IR Seam & Native Hermes Skills

**Reviewer**: `reviewer_2_m3_orch3` (teamwork_preview_reviewer)  
**Roles**: Reviewer, Adversarial Critic  
**Date**: 2026-09-04T18:53:00Z  
**Target Branch**: `dev`  
**Working Directory**: `g:\Finding-new-code\harness9\.agents\reviewer_2_m3_orch3`  
**Verdict**: **APPROVE**  
**Integrity Status**: **PASS** (Zero integrity violations, no hardcoding, no facades, no bypassed logic)

---

## 1. Observation

Direct observations from independent inspection and test execution:

1. **Source Code Implementation (`src/models/ir.py`)**:
   - Lines 33–42: `IRBlockType(str, Enum)` defines the 7 canonical visual blocks (`reference_collage_hook`, `split_screen_intro`, `quote_highlight`, `timeline_reveal`, `statistic_reveal`, `comparison_panel`, `creator_bottom_collage`).
   - Lines 47–171: Strict Pydantic v2 AST node hierarchy:
     - `IRAssetReference`: Pinned asset model with `asset_id`, `file_path`, `file_sha256`, `media_type`, dimensions, license.
     - `IRSpeechBeat`: Timestamped acoustic cadence beat with `beat_id`, `start_time_sec`, `end_time_sec`, `text`, `duration_sec` property.
     - `IRNarrationBlock`: Scene vocal delivery specification with `full_text`, `voice_profile`, `target_wpm` (clamped 90–220), `speech_beats`.
     - `IRAnimationTrack`: Parametric GSAP track with selector, property, from/to values, offset, duration, and easing.
     - `IRVisualBlockNode`: Parameterized visual component AST node binding visual slots to manifest assets.
     - `IRTransitionSpec`: Entrance/exit transition dynamics with duration bounds ($[0.0, 2.0]$s).
     - `IRSceneNode`: Scene timeline node with index, act ($1$ to $4$), start time, duration ($>0$), and `end_time_sec` property.
     - `IRAudioTrack`: Global audio master track ($>0$ duration, sample rate, channels).
     - `IRMetadata`: Resolution, aspect ratio (regex `^(16:9|9:16|1:1)$`), fps ($15$ to $60$), brand theme colors.
   - Lines 176–298: `ProductionIRDocument(ProductionIR, BaseModel)`:
     - Dual-inherits from `ProductionIR` (frozen dataclass from `src.h9_runtime.types`) and `BaseModel`.
     - `@model_validator(mode="after")` enforces 5 strict invariants:
       - Invariant 0: Non-empty scenes list.
       - Invariant 1: Temporal contiguity & conservation ($\Delta t \le 0.05$s).
       - Invariant 2: Audio track duration matching ($|\sum t_{\text{scenes}} - t_{\text{audio}}| \le 0.5$s).
       - Invariant 3: Asset binding integrity (`asset_id in self.asset_manifest`).
       - Invariant 4: Speech beat bounds clamping ($t_{\text{start}} \ge t_{\text{scene\_start}} - 0.05$s and $t_{\text{end}} \le t_{\text{scene\_end}} + 0.15$s).
     - Automatically synchronizes legacy `ProductionIR` fields (`project_id`, `aspect_ratio`, `fps`, `duration_seconds`, `timeline_blocks`, `audio_tracks`, `css_variables`).
     - Provides `to_dict()` and `to_script()` round-trip conversions.
   - Lines 367–625: `compile_script_to_ir(...)`:
     - Dynamically parses `Script` or `dict`, builds asset manifest, enforces cumulative start times, clamps speech beats within scenes, constructs audio track matching scene duration, and instantiates validated `ProductionIRDocument`.
   - Lines 630–704: `HyperFramesCompiler`:
     - Consumes `ProductionIRDocument`, stages asset files (writing valid SVG and WAV stubs where missing), maps manifest to `AssetRecord` list, and calls `HyperFramesAdapter.compile_composition(...)`.

2. **Package Exports (`src/models/__init__.py`)**:
   - Lines 73–88, 90–105: Re-exports all 12 AST models/classes, `compile_script_to_ir`, and `HyperFramesCompiler`.

3. **Runtime Wiring (`src/h9_runtime/content.py` & `src/h9_runtime/bridge.py`)**:
   - `src/h9_runtime/content.py` (lines 80–86, 242–280): `compile_production_ir` typed to return `ProductionIRDocument` and invokes `compile_script_to_ir`.
   - `src/h9_runtime/bridge.py` (lines 510–515): `HermesCapabilityBridge.compile_production_ir` wraps `content.compile_production_ir` returning `ProductionIRDocument`.

4. **Native Hermes Skills (`skills/h9-*/SKILL.md`)**:
   - `skills/h9-research/SKILL.md`: Frontmatter with tags `[Content, Research, FactChecking, Verification, H9]`, 5-axis orthogonal query expansion, $\ge 0.70$ claim confidence threshold, subagent delegation instructions.
   - `skills/h9-content-planning/SKILL.md`: Frontmatter with tags `[Content, Editorial, Scriptwriting, Planning, H9]`, 5-archetype ideation, 9-dimension scorecard evaluation, 4-act narrative planning.
   - `skills/h9-production/SKILL.md`: Frontmatter with tags `[Production, Audio, TTS, MediaAssets, Pipeline, H9]`, 17-state lifecycle machine, 90–220 WPM cadence, 4-gate Voice QA, 3-tier asset deduplication.
   - `skills/h9-hyperframes/SKILL.md`: Frontmatter with tags `[Video, HyperFrames, GSAP, Animation, Rendering, H9]`, 7 canonical visual blocks, AST seam specifications, and headless MP4 render lifecycle.

5. **Test Verification Execution**:
   - Targeted M3 Suite:
     ```
     .venv\Scripts\python.exe -m pytest tests/test_h9_skills_and_ir.py tests/test_h9_content_tools.py tests/test_h9_runtime.py -v
     ============================= 63 passed in 41.17s =============================
     ```
   - Full Regression Suite:
     ```
     .venv\Scripts\python.exe -m pytest tests/test_h9_skills_and_ir.py tests/test_h9_content_tools.py tests/test_challenger_m2_stress.py tests/test_h9_runtime.py tests/tools/test_registry.py
     ======================= 128 passed in 369.12s (0:06:09) =======================
     ```
   - Adversarial Boundary Stress Test:
     - Boundary at 0.05s scene gap passed; 0.06s gap raised `ValueError: Temporal Discontinuity`.
     - Boundary at 0.50s audio drift passed; 0.51s drift raised `ValueError: Audio Drift`.
     - All 7 canonical blocks compiled via `HyperFramesCompiler` passed `project.validate()` with 0 errors.
     - Dynamic script with randomized UUIDs and durations compiled cleanly without static hardcoding.
     - JSON round-trip (`model_dump_json` $\to$ `model_validate_json`) preserved full AST document structure.

---

## 2. Logic Chain

1. **Requirement Fulfillment**:
   - Requirement R3 specifies: *"Package H9 domain workflows into native Hermes skills (skills/h9-research/, skills/h9-content-planning/, skills/h9-production/, skills/h9-hyperframes/) using existing Hermes skill conventions (SKILL.md). Introduce the typed Production IR seam between narrative planning and HyperFrames compilation."*
   - Direct inspection confirms that all 4 skills exist on disk in the standard Hermes repository layout with valid YAML frontmatter, markdown instructions, and quick references.
   - Direct inspection confirms that `src/models/ir.py` introduces the typed `ProductionIRDocument` AST with complete node hierarchies and mathematical invariant validators.
2. **Robust Invariant Enforcement**:
   - The `@model_validator(mode="after")` in `ProductionIRDocument` rigorously prevents corrupt data from reaching the rendering layer:
     - Invariant 0 prevents degenerate empty documents.
     - Invariant 1 prevents timeline tearing or scene overlaps.
     - Invariant 2 prevents audio-visual desync.
     - Invariant 3 prevents missing asset references.
     - Invariant 4 prevents speech beats from firing outside scene boundaries.
3. **Dual Inheritance and Backward Compatibility**:
   - By inheriting from both `ProductionIR` (legacy frozen dataclass) and `BaseModel`, `ProductionIRDocument` satisfies `isinstance(doc, ProductionIR)` checks throughout existing codebase modules.
   - Synchronizing legacy fields (`timeline_blocks`, `audio_tracks`, `css_variables`) allows downstream callers relying on dictionary-based timeline blocks to execute without modification.
4. **Zero Regressions and System Stability**:
   - The test suite of 128 tests (including stress challenger tests from M2 and runtime protocol tests from M1) passed with 100% success (0 failures, 0 errors).
5. **Integrity Validation**:
   - No mock facades or hardcoded return strings were found in `src/models/ir.py` or the test files.
   - Dynamic tests with arbitrary random inputs proved the compilation logic executes dynamically and deterministically.

---

## 3. Caveats

1. **Headless Browser Rendering**:
   - In environments without installed Chromium/Playwright browser binaries, real frame-by-frame HTML canvas rendering is not invoked; instead, procedural SVG asset generation and media container header synthesis serve as hermetic fallback paths. This is consistent with CI/CD design and fully documented.
2. **Standalone IRSpeechBeat Instantiation**:
   - Direct standalone instantiation of `IRSpeechBeat(start_time_sec=5.0, end_time_sec=2.0)` does not raise a validation error at model construction because duration is computed via `max(0.0, end - start)`. However, `compile_script_to_ir(...)` explicitly enforces `clamped_et >= clamped_st + 0.05`, and Invariant 4 bounds-checks beats within scenes. This is flagged as a minor observation for future hardening, but does not affect pipeline execution.

---

## 4. Conclusion & Verdict

**Verdict**: **APPROVE**  
**Integrity Finding**: **PASS** (Zero integrity violations)

Milestone 3 successfully establishes a rock-solid, typed Production IR AST seam (`ProductionIRDocument`) and delivers all 4 native Hermes skills (`h9-research`, `h9-content-planning`, `h9-production`, `h9-hyperframes`). Invariant validation is strict and mathematically sound, backward compatibility with legacy `ProductionIR` is 100% preserved, and the entire test suite passes without regressions.

---

## 5. Verification Method

To independently reproduce and verify this review:

1. **Run Targeted M3 Test Suite**:
   ```pwsh
   .venv\Scripts\python.exe -m pytest tests/test_h9_skills_and_ir.py tests/test_h9_content_tools.py tests/test_h9_runtime.py -v
   ```
   *Expected*: 63 tests pass.

2. **Run Full Regression Test Suite**:
   ```pwsh
   .venv\Scripts\python.exe -m pytest tests/test_h9_skills_and_ir.py tests/test_h9_content_tools.py tests/test_challenger_m2_stress.py tests/test_h9_runtime.py tests/tools/test_registry.py
   ```
   *Expected*: 128 tests pass.

3. **Verify AST Invariant Enforcement (Adversarial Check)**:
   ```pwsh
   .venv\Scripts\python.exe -c "from src.models.ir import *; import pytest; doc = compile_script_to_ir({'topic': 'T', 'scenes': [{'scene_id': 's1', 'duration': 5.0}]}); print('AST Document Valid:', doc.ir_version)"
   ```
   *Expected*: Output shows `AST Document Valid: 1.0.0`.
