# BRIEFING — 2026-09-04T10:41:04Z

## Mission
Implement Milestone 2: Hermes Capability Bridge & Native Tool Conversion (Requirement R2).

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: g:\Finding-new-code\harness9\.agents\worker_m2_dev_2
- Original parent: dba72588-b963-4d76-af7f-a4dfb2b69d51
- Milestone: Milestone 2: Hermes Capability Bridge & Native Tool Conversion

## 🔒 Key Constraints
- EXCLUSIVE FILE OWNERSHIP:
  * src/h9_runtime/bridge.py
  * tools/h9_content_tools.py
  * tools/registry.py (registering h9_content toolset and tools)
  * tests/test_h9_content_tools.py
- DO NOT CHEAT. All implementations must be genuine.
- DO NOT run unconstrained grep_search or find_by_name across the workspace (ripgrep hangs on .venv). Use view_file directly.
- DO NOT modify _HERMES_CORE_TOOLS in toolsets.py (narrow waist constraint).
- Gate native tools with check_h9_available() (Rung 3 of Footprint Ladder).
- Bound handler error messages to <= 2048 chars.
- 100% tests must pass with .venv\Scripts\python.exe -m unittest tests\test_h9_content_tools.py tests\test_challenger_2_integration_stress.py tests\test_h9_runtime.py tests\test_hermes_adapter.py.

## Current Parent
- Conversation ID: dba72588-b963-4d76-af7f-a4dfb2b69d51
- Updated: 2026-09-04T10:41:04Z

## Task Summary
- **What to build**: HermesCapabilityBridge in src/h9_runtime/bridge.py, 4 native tools in tools/h9_content_tools.py, register tools in tools/registry.py under 'h9_content', and comprehensive tests in tests/test_h9_content_tools.py.
- **Success criteria**: All 4 tools registered in registry under h9_content, schemas valid OpenAI function specs, dispatch working with genuine validation and execution, error bounded, and test suites passing 100%.
- **Interface contracts**: PROJECT.md, survey reports.
- **Code layout**: src/h9_runtime/bridge.py, tools/h9_content_tools.py, tools/registry.py, tests/test_h9_content_tools.py.

## Key Decisions Made
- [TBD]

## Artifact Index
- DISPATCH.md — Assignment instructions
- BRIEFING.md — Working memory index
- progress.md — Liveness heartbeat and progress log
- handoff.md — Final handoff report

## Change Tracker
- **Files modified**: None yet
- **Build status**: Untested
- **Pending issues**: None

## Quality Status
- **Build/test result**: Untested
- **Lint status**: Clean
- **Tests added/modified**: None yet

## Loaded Skills
None
