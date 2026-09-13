# BRIEFING — 2026-09-04T10:20:00Z

## Mission
Implement Milestone 2: Hermes Capability Bridge & Native Tool Conversion (Requirement R2) for Harness9.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: g:\Finding-new-code\harness9\.agents\worker_m2_dev
- Original parent: dba72588-b963-4d76-af7f-a4dfb2b69d51
- Milestone: Milestone 2 (Bridge & Native Tool Conversion)

## 🔒 Key Constraints
- Exclusive file ownership:
  * src/h9_runtime/bridge.py
  * tools/h9_content_tools.py
  * tools/registry.py (registering h9_content toolset and tools)
  * tests/test_h9_content_tools.py
- DO NOT modify `_HERMES_CORE_TOOLS` in `toolsets.py` (narrow waist constraint).
- Service-gated tool: tools in `h9_content` toolset gated by `check_h9_available()` (Rung 3 of Footprint Ladder).
- Bound tool error messages to <= 2048 chars.
- Valid OpenAI function tool definitions.
- Genuine implementations, no cheating/facades.
- Verify 100% tests pass on test suite including M1 tests.

## Current Parent
- Conversation ID: dba72588-b963-4d76-af7f-a4dfb2b69d51
- Updated: 2026-09-04T10:20:00Z

## Task Summary
- **What to build**: HermesCapabilityBridge in `src/h9_runtime/bridge.py`, 4 native Hermes tools in `tools/h9_content_tools.py`, tool registry updates in `tools/registry.py`, comprehensive test suite in `tests/test_h9_content_tools.py`.
- **Success criteria**: Clean capability bridge methods (`research`, `discover_assets`, `generate_script`, `render`), 4 valid OpenAI schema tools with handler validation and <=2048 char error bounding, `check_h9_available` registration, 100% passing test suite.
- **Interface contracts**: `PROJECT.md`, `src/h9_runtime/` (contracts, hermes_adapter, state_machine).
- **Code layout**: Runtime bridge in `src/h9_runtime/`, tools in `tools/`, tests in `tests/`.

## Key Decisions Made
- [Initial turn - reading surveys and specs]

## Artifact Index
- `src/h9_runtime/bridge.py`
- `tools/h9_content_tools.py`
- `tools/registry.py`
- `tests/test_h9_content_tools.py`
- `handoff.md`

## Change Tracker
- **Files modified**: none yet
- **Build status**: pending initial run
- **Pending issues**: none

## Quality Status
- **Build/test result**: pending
- **Lint status**: pending
- **Tests added/modified**: pending

## Loaded Skills
- None specified
