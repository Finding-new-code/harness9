# Handoff Report: Acceptance & Regression Verification Baseline (survey_test_explorer_3)

**Agent:** `survey_test_explorer_3` (teamwork_preview_explorer)  
**Parent Agent ID:** `dba72588-b963-4d76-af7f-a4dfb2b69d51`  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\survey_test_explorer_3`  
**Report Path:** `g:\Finding-new-code\harness9\.agents\survey_test_explorer_3\report.md`  
**Date:** 2026-09-04  
**Type:** Hard Handoff (Task Complete)  

---

## 1. Observation

1. **User Request & Objectives:**
   `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md`, lines 55–82 (`## 2026-09-04T08:55:45Z`):
   > "Refactor Harness 9 so that its content-production capabilities run directly through the full Hermes Agent runtime (agent loop, context engineering, skills, tools, MCP, provider/model routing, memory, subagents, permissions, sandbox, and cron) on branch dev, establishing a clean integration boundary (src/h9_runtime/) without duplicating or breaking either runtime."
   Requirement R6 mandates implementing an integration test suite covering the 8 required acceptance dimensions (A through H), ensuring zero regressions across existing Hermes and H9 test suites, and authoring `docs/architecture/hermes-h9-integration-audit.md`.

2. **Existing Baseline Test Health:**
   - Evaluated 200+ H9 unit/component tests in `tests/`:
     - `tests/test_state_machine.py`: 10 tests passed in 0.011s (`.venv\Scripts\python -m unittest tests\test_state_machine.py`).
     - `tests/test_contracts.py`: 12 tests passed in 0.419s.
     - `tests/test_hermes_adapter.py`: 6 tests passed in 32.590s.
     - Batch 1 (`test_editorial.py`, `test_security_tokens.py`, `test_creator_dna.py`, `test_economics.py`): 56 tests passed in 0.697s.
     - Batch 2 (`test_hyperframes.py`, `test_hyperframes_components.py`, `test_voice_director.py`, `test_voice_qa.py`, `test_deduplication.py`, `test_assets.py`): 94 tests passed in 58.753s.
     - Batch 3 (`test_research.py`, `test_scriptwriting.py`, `test_contentbench.py`): 51 tests passed in 15.820s.
     - Acceptance pipeline harness: `.venv\Scripts\python verify_pipeline.py --test-mode --output-dir output/test_run_survey` passed all 6 checkpoints in 38.26s.
   - Result: 100% pass rate across existing baseline tests.

3. **Execution Runtime & Environment:**
   - Host Python: 3.14.6 (no pytest on system PATH).
   - Virtual environment: `.venv` has Python 3.11.15 (`.venv\Scripts\python.exe`), satisfying `pyproject.toml`'s requirement `requires-python = ">=3.11,<3.14"`.
   - `.venv\Scripts\python -m unittest` executes tests reliably and with high speed.

4. **Critical Regression Risk in `test_hermes_adapter.py`:**
   `tests/test_hermes_adapter.py`, lines 82–108:
   > Explicitly asserts that `get_tool_schemas()` returns 3 tools (`generate_video_from_brief`, `inspect_production_state`, `evaluate_content_quality`) and `get_harness9_toolsets()` returns toolset `"harness9_video"`.
   Deleting or breaking `adapters/hermes/` will cause immediate regression failures in `test_hermes_adapter.py`.

5. **Tool Registration & Invariants:**
   `tools/registry.py`, lines 763–778:
   > `register(name, toolset, schema, handler, check_fn=None, ...)`
   `AGENTS.md`, lines 18–24:
   > "The core is a narrow waist; capability lives at the edges. Every model tool we add is sent on every API call... Most new capability should arrive as a CLI command + skill, a service-gated tool, or a plugin — not as core surface."

---

## 2. Logic Chain

1. **Step 1 (Baseline Integrity):** Observation 2 confirms that the current H9 codebase is in a pristine, 100% passing state across all 14 core unit test suites and the 6-checkpoint pipeline verifier. Any test failure introduced during refactoring will represent a true regression.
2. **Step 2 (Execution Infrastructure):** Observation 3 shows that `.venv\Scripts\python.exe -m unittest` is the verified, hermetic test execution command, bypassing system Python 3.14 version incompatibilities.
3. **Step 3 (Backward Compatibility Preservation):** Observation 4 shows that existing M1 tests require `adapters/hermes/` to remain functional. Therefore, `adapters/hermes/bridge.py` and `tools.py` must NOT be deleted, but refactored into a thin compatibility facade delegating to the new `src/h9_runtime/` protocols.
4. **Step 4 (Footprint Ladder Compliance):** Observation 5 dictates that the new granular tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) must not be placed in `_HERMES_CORE_TOOLS`, but in a dedicated service-gated toolset (`h9_content`) with availability check `check_h9_available()`.
5. **Step 5 (Acceptance Suite Design):** Synthesizing Observations 1, 4, and 5 leads directly to the 8-dimension acceptance suite design (`tests/test_h9_acceptance.py` and `tests/test_h9_e2e_integration.py` containing 38 test cases), verifying:
   - Dimension A (Runtime): `src/h9_runtime/` protocols and zero private imports.
   - Dimension B (Skills): `skills/h9-*/` discovery, frontmatter, and progressive disclosure.
   - Dimension C (Providers): Logical capability role routing without hardcoded LLM clients.
   - Dimension D (Tools): Native Hermes tool registration and bounded error handling.
   - Dimension E (Subagents): Isolated research delegation via `delegate_task` returning `ResearchDossier`.
   - Dimension F (Permissions): Principle-of-least-privilege capability token enforcement and HMAC tamper rejection.
   - Dimension G (Sandbox): Path traversal rejection and offline network egress blocking.
   - Dimension H (E2E Artifact): Full pipeline rendering a valid, broadcast-ready MP4 artifact.

---

## 3. Caveats

- **Read-Only Investigation:** No code or test files in `src/`, `tests/`, or `adapters/` were modified.
- **FFmpeg Host Binary:** Where system `ffmpeg` is absent, test harnesses fallback to pure-Python procedural WAV and MP4 container generation in `src/utils/ffmpeg.py`.
- **System Pytest Absence:** The test suite must be run via `.venv\Scripts\python.exe -m unittest` unless `pytest` is explicitly invoked within `.venv`.

---

## 4. Conclusion

The acceptance test architecture and regression verification baselines are fully established and documented in `g:\Finding-new-code\harness9\.agents\survey_test_explorer_3\report.md`. 

Downstream workers have a clear implementation and verification contract:
1. Use `.venv\Scripts\python -m unittest` for all verification.
2. Keep `adapters/hermes/` as a backward-compatible delegation shim to ensure zero regressions in existing tests.
3. Implement `tests/test_h9_acceptance.py` and `tests/test_h9_e2e_integration.py` covering all 38 test cases across Dimensions A through H.
4. Document findings in `docs/architecture/hermes-h9-runtime-coupling.md` and `docs/architecture/hermes-h9-integration-audit.md`.

---

## 5. Verification Method

To independently verify the baseline and execution findings:
1. Run existing H9 unit test batches:
   ```powershell
   .venv\Scripts\python -m unittest tests\test_state_machine.py tests\test_contracts.py tests\test_hermes_adapter.py
   ```
2. Run the acceptance pipeline verifier:
   ```powershell
   .venv\Scripts\python verify_pipeline.py --test-mode --output-dir output/test_run_verify
   ```
3. Inspect the comprehensive acceptance test specification:
   `g:\Finding-new-code\harness9\.agents\survey_test_explorer_3\report.md`
