## 2026-09-04T10:41:04Z
You are worker_m2_dev_2, a teamwork_preview_worker subagent.
Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m2_dev_2

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP:
Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (under ## 2026-09-04T08:55:45Z) and survey reports:
- `g:\Finding-new-code\harness9\.agents\survey_explorer_2\report.md` (Section 3: Native Tool Conversion)
- `g:\Finding-new-code\harness9\.agents\survey_spec_miner_1\report.md` (Section 3: Tool Registration)
- `g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_2\PROJECT.md`

CRITICAL PERFORMANCE INSTRUCTION:
DO NOT run unconstrained grep_search or find_by_name across the workspace (ripgrep hangs on .venv). Use view_file directly on `tools/registry.py`, `src/h9_runtime/`, `adapters/hermes/bridge.py`.

MILESTONE 2 OBJECTIVE:
Implement Milestone 2: Hermes Capability Bridge & Native Tool Conversion (Requirement R2).

EXCLUSIVE FILE OWNERSHIP:
- src/h9_runtime/bridge.py
- tools/h9_content_tools.py
- tools/registry.py (registering h9_content toolset and tools)
- tests/test_h9_content_tools.py

SPECIFICATIONS & REQUIREMENTS:
1. Capability Bridge (`src/h9_runtime/bridge.py`):
   - Implement `HermesCapabilityBridge` allowing H9 domain modules to request Hermes services without importing internal Hermes implementation details.
   - Bridge provides clean methods: `research(topic, ...)`, `discover_assets(requirements, ...)`, `generate_script(outline, ...)`, `render(production_ir, ...)`.
   - Accesses runtime abstractions from `src/h9_runtime/` (`ContentRuntime`, `ToolRuntime`, `ExecutionRuntime`, etc.).
2. Native Tool Conversion (`tools/h9_content_tools.py`):
   - Expose 4 native Hermes model tools:
     * `h9.research` (alias `h9_research`): inputs topic (str), depth (str), constraints (dict) -> returns validated `ResearchDossier` JSON.
     * `h9.discover_assets` (alias `h9_discover_assets`): inputs requirements (list), scene_ids (list) -> returns list of `AssetRecord` JSON.
     * `h9.generate_script` (alias `h9_generate_script`): inputs outline (dict), dossier (dict), creator_id (str) -> returns validated `Script` JSON.
     * `h9.render` (alias `h9_render`): inputs production_ir (dict), output_dir (str), session_id (str) -> returns `RenderArtifact` JSON.
   - Schemas must be valid OpenAI function tool definitions.
   - Handlers must validate incoming arguments against schema and bound error messages to <= 2048 chars.
   - Provide `check_h9_available() -> bool`.
3. Hermes Tool Registry Integration:
   - In `tools/registry.py`, register the 4 tools under named toolset `h9_content` (or `harness9`), gated by `check_h9_available()` (Rung 3 of Footprint Ladder).
   - DO NOT modify `_HERMES_CORE_TOOLS` in `toolsets.py` (narrow waist constraint).
4. Tests (`tests/test_h9_content_tools.py`):
   - Test tool registration in `registry`.
   - Test schema validity for each tool.
   - Test tool dispatch with valid arguments and schema validation on invalid arguments.
   - Test error bounding.
5. VERIFICATION MANDATE:
   - Run tests using `.venv\Scripts\python.exe -m unittest tests\test_h9_content_tools.py tests\test_challenger_2_integration_stress.py tests\test_h9_runtime.py tests\test_hermes_adapter.py`.
   - Verify 100% tests pass.

Write your handoff report to `g:\Finding-new-code\harness9\.agents\worker_m2_dev_2\handoff.md` and message the parent when complete.
