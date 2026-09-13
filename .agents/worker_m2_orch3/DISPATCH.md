## 2026-09-04T17:47:27Z

<USER_REQUEST>
You are worker_m2_orch3, a teamwork_preview_worker implementing Milestone 2 of the Hermes x Harness 9 Runtime Coupling.

Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m2_orch3\
Create and maintain your own BRIEFING.md, progress.md, and handoff.md in your working directory.
Always communicate updates and completion via send_message to your parent (Recipient: d832f8a0-ed17-43c0-91e0-f1ecca7ae126).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INPUTS — READ THESE FIRST:
1. g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (Authoritative requirements, read sections ## 2026-09-04T17:41:55Z and ## 2026-09-04T08:55:45Z)
2. g:\Finding-new-code\harness9\docs\architecture\hermes-h9-runtime-coupling.md (Milestone 1 architecture audit and call graphs)
3. Existing runtime interfaces: g:\Finding-new-code\harness9\src\h9_runtime\ (types.py, agent.py, tools.py, skills.py, models.py, memory.py, execution.py, content.py)
4. Existing Hermes tool registry: g:\Finding-new-code\harness9\tools\registry.py and g:\Finding-new-code\harness9\model_tools.py
5. Technical survey reports:
   - g:\Finding-new-code\harness9\.agents\survey_spec_miner_1\report.md (Hermes runtime specs, tool registration patterns, check_fn)
   - g:\Finding-new-code\harness9\.agents\survey_explorer_2\report.md (H9 domain architectures, tool schemas, bridge design)
6. g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_3\PROJECT.md
7. g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_3\plan.md

YOUR EXCLUSIVE WRITE OWNERSHIP:
- g:\Finding-new-code\harness9\src\h9_runtime\bridge.py
- g:\Finding-new-code\harness9\src\h9_runtime\__init__.py (if exporting bridge)
- g:\Finding-new-code\harness9\tools\h9_content_tools.py
- g:\Finding-new-code\harness9\tools\registry.py (modify to register h9_content toolset and check_h9_available)
- g:\Finding-new-code\harness9\tests\test_h9_content_tools.py

DELIVERABLES & TASKS:
1. Implement `src/h9_runtime/bridge.py`:
   - Define `HermesCapabilityBridge` allowing H9 domain modules to request Hermes services without importing Hermes internals.
   - Implement methods mapping to the runtime protocols (AgentRuntime, SkillRuntime, ToolRuntime, ModelRuntime, MemoryRuntime, ExecutionRuntime, ContentRuntime).
   - Provide clean integration for H9 domain pipeline steps to invoke Hermes capabilities.
2. Implement `tools/h9_content_tools.py`:
   - Expose the 4 native Hermes model tools:
     - `h9.research`: params: topic (str), depth (str), constraints (optional dict). Returns ResearchDossier or structured research summary.
     - `h9.discover_assets`: params: requirements (list of dicts/AssetRequirements), scene_ids (list of str). Returns list of AssetRecords.
     - `h9.generate_script`: params: outline (dict), dossier (dict), creator (optional dict). Returns Script.
     - `h9.render`: params: production_ir (dict), output_dir (str). Returns RenderArtifact.
   - Each tool must have complete, valid OpenAI/Hermes tool schemas and genuine handler functions interfacing with the bridge / H9 services.
3. Integrate into `tools/registry.py`:
   - Register the 4 tools into the Hermes tool registry under the named toolset `h9_content`.
   - Implement `check_h9_available()` as the `check_fn` so the tools follow Rung 3 of the Footprint Ladder (service-gated: 0 core schema overhead when H9 is not active).
4. Implement comprehensive tests in `tests/test_h9_content_tools.py`:
   - Test tool registration and schema validity.
   - Test `check_h9_available()` gating behavior (active vs inactive).
   - Test tool execution for all 4 tools (happy path and error handling).
   - Test bridge integration and protocol conformance.
5. Run test verification:
   - Use Python in virtual environment (`.venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py tests/test_h9_runtime.py -v`).
   - Verify all tests pass 100% and zero regressions.
6. Write a comprehensive `handoff.md` in your working directory and notify parent via `send_message`.
</USER_REQUEST>
