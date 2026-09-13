# Review & Adversarial Critic Report: Milestone 2 (Hermes x Harness 9 Runtime Coupling)

- **Reviewer**: reviewer_2_m2_orch3 (teamwork_preview_reviewer)
- **Roles**: reviewer, critic
- **Milestone**: Milestone 2 — Hermes Capability Bridge & Native Tool Conversion
- **Date**: 2026-09-04
- **Verdict**: **APPROVE**

---

## 1. Observation

1. **Integrity & Implementation Audit**:
   - `tools/h9_content_tools.py` (lines 42–167): Defines 4 canonical model tool schemas (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) adhering strictly to standard OpenAI function calling specifications (`name`, `description`, `parameters` with `type: "object"`, `properties`, and `required`).
   - `tools/h9_content_tools.py` (lines 174–374): Implements concrete execution handlers (`handle_h9_research`, `handle_h9_discover_assets`, `handle_h9_generate_script`, `handle_h9_render`). No dummy stubs, mocked static values, or facade bypasses exist.
     - `handle_h9_research` invokes `bridge.plan_research`, triggering factual synthesis and claim extraction via `ResearchEngine`.
     - `handle_h9_discover_assets` invokes `bridge.discover_assets`, executing procedural vector rendering via `ProceduralSVGGenerator`, writing real `.svg` files to disk, and computing SHA-256 and perceptual dHash digests.
     - `handle_h9_generate_script` normalizes LLM claim formats (lines 281–295) and coordinates 9-dimension angle evaluation (`EditorialEngine`) to emit multi-scene scripts with timestamped `ScriptBeat`s.
     - `handle_h9_render` executes `bridge.render_video` generating broadcast-standard container artifacts (`RenderArtifact`) with dimensions 1920x1080 / 1080x1920 and target frame rates.
   - All handlers wrap outputs with `tools.registry.tool_result` and catch exceptions via `tools.registry.tool_error`, preventing stack traces from corrupting model context.

2. **Footprint Ladder & Toolset Gating Audit**:
   - `tools/registry.py` (lines 1352–1373): `check_h9_available()` gates the `h9_content` toolset. It inspects `_h9_availability_override`, `H9_ENABLED` / `HERMES_H9_ENABLED` environment variables, and the presence of `src.h9_runtime`.
   - `tools/h9_content_tools.py` (lines 380–462): All 4 tools and their 4 snake_case aliases (`h9_research`, `h9_discover_assets`, `h9_generate_script`, `h9_render`) are registered in named toolset `h9_content` with `check_fn=check_h9_available`.
   - The tools are **NOT** added to `_HERMES_CORE_TOOLS`, ensuring Rung 3 compliance (0 token footprint when inactive).
   - Dynamic reactivation and deactivation were verified via `registry.get_definitions({"h9.research", ...})`: returns empty list when inactive, returns full definitions when active.

3. **Bridge Protocol Conformance**:
   - `src/h9_runtime/bridge.py` (lines 83–821): `HermesCapabilityBridge` implements all 7 runtime protocols (`AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`).
   - `src/h9_runtime/__init__.py` (lines 18–99): Cleanly exports `HermesCapabilityBridge`, `get_capability_bridge`, and `reset_capability_bridges`.

4. **Empirical Test Verification**:
   - Executed `.venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py tests/tools/test_registry.py -v`:
     - Result: `73 passed in 16.29s` (34 tests in `test_h9_content_tools.py`, 39 tests in `test_registry.py`).
   - Executed combined M1 + M2 + registry suite `.venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py tests/test_h9_runtime.py tests/tools/test_registry.py -v`:
     - Result: `83 passed in 121.38s` (34 tests in `test_h9_content_tools.py`, 10 tests in `test_h9_runtime.py`, 39 tests in `test_registry.py`).
   - Zero test failures, zero regressions.

---

## 2. Logic Chain

1. **Integrity Assurance**:
   - Code inspection of `tools/h9_content_tools.py` and `src/h9_runtime/bridge.py` verified that no hardcoded return values, test bypasses, dummy stubs, or fabricated artifacts exist.
   - Claims and assets undergo real computation (e.g. SHA-256 calculation `hashlib.sha256(content_bytes).hexdigest()`, procedural SVG generation, timeline beat slicing).
   - Therefore, the implementation is genuine and meets strict integrity standards.

2. **Footprint Ladder & Prompt Caching Invariant**:
   - The Hermes architecture states: *"A long-lived conversation reuses a cached prefix every turn. Anything that mutates past context, swaps toolsets, or rebuilds the system prompt mid-conversation invalidates that cache and multiplies the user's cost."*
   - Tools are grouped under the isolated named toolset `h9_content` and gated by `check_h9_available()`.
   - When H9 is inactive, `registry.get_definitions(...)` returns 0 tool definitions, adding exactly 0 tokens to the core model tool schema.
   - Tool schemas are static declarations with fixed parameter types, preventing runtime schema oscillation and protecting prefix caching.

3. **Error Bounding & Robustness**:
   - Handlers defensively validate inputs against non-dictionary arguments, empty string topics, missing dossiers, and invalid aspect ratios.
   - Handlers catch all exceptions and route through `tool_error`, which enforces a 2048-character bound (`_MAX_TOOL_ERROR_CHARS`) to prevent context overflow.
   - Loose LLM claim structures (`id`, `text`, `confidence`) are automatically converted into strict Pydantic `ResearchDossier` formats (`claim_id`, `claim_text`, `confidence_score`, `primary_source`), avoiding deserialization breakages.

4. **Protocol & Architectural Decoupling**:
   - `HermesCapabilityBridge` acts as a facade isolating H9 domain services from internal Hermes agent implementations, allowing bidirectional delegation (subagents, sandboxed execution, memory queries) without polluting either codebase.

---

## 3. Caveats

- **No caveats.** The implementation satisfies all acceptance criteria of Milestone 2, demonstrates robust error handling, passes all empirical tests, and exhibits zero regressions against the existing tool registry test suite.

---

## 4. Conclusion

- **Verdict**: **APPROVE**
- `tools/h9_content_tools.py` and `tools/registry.py` are robust, secure, and conformant with Hermes architectural principles (Footprint Ladder Rung 3, prompt caching preservation, and error bounding).
- Milestone 2 is fully complete and ready for Milestone 3 progression.

---

## 5. Verification Method

To independently reproduce and verify this review:

```bash
# 1. Run M2 content tools and Hermes tool registry regression tests
.venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py tests/tools/test_registry.py -v

# 2. Run combined M1 + M2 + registry suite
.venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py tests/test_h9_runtime.py tests/tools/test_registry.py -v
```

### Invalidation Conditions
- Any failure in the 34 tests of `tests/test_h9_content_tools.py`.
- Any regression in the 39 tests of `tests/tools/test_registry.py`.
- Any leakage of `h9_content` schemas into default core toolsets when `check_h9_available()` is False.
