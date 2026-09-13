# Handoff Report: Hermes Runtime Survey & H9 Integration Specification

**Subagent:** survey_spec_miner_1  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\survey_spec_miner_1`  
**Date:** 2026-09-04  
**Type:** Hard Handoff (Task Complete)  

---

## 1. Observation

1. **User Request & Mandate:**
   `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md`, lines 55-82 (`## 2026-09-04T08:55:45Z`):
   > "Refactor Harness 9 so that its content-production capabilities run directly through the full Hermes Agent runtime (agent loop, context engineering, skills, tools, MCP, provider/model routing, memory, subagents, permissions, sandbox, and cron) on branch dev, establishing a clean integration boundary (src/h9_runtime/) without duplicating or breaking either runtime."

2. **Core Invariants & Footprint Ladder:**
   `g:\Finding-new-code\harness9\AGENTS.md`, lines 18-24:
   > "- Per-conversation prompt caching is sacred. A long-lived conversation reuses a cached prefix every turn. Anything that mutates past context, swaps toolsets, or rebuilds the system prompt mid-conversation invalidates that cache and multiplies the user's cost...
   > - The core is a narrow waist; capability lives at the edges. Every model tool we add is sent on every API call... Most new capability should arrive as a CLI command + skill, a service-gated tool, or a plugin — not as core surface."

3. **Tool Registration & Availability Probing:**
   `g:\Finding-new-code\harness9\tools\registry.py`, lines 763-778:
   > `register(name, toolset, schema, handler, check_fn=None, requires_env=None, is_async=False, ...)`
   Lines 269-277:
   > `_CHECK_FN_TTL_SECONDS = 30.0`
   > `_CHECK_FN_FAILURE_GRACE_SECONDS = 60.0`
   > `_check_fn_cached(fn)` returns cached booleans with 60s failure grace to suppress transient probe flapping.

4. **Skill Progressive Disclosure & Prompt Injection:**
   `g:\Finding-new-code\harness9\tools\skills_tool.py`, lines 9-13:
   > "Inspired by Anthropic's Claude Skills system with progressive disclosure architecture:
   > - Metadata (name ≤64 chars, description ≤1024 chars) - shown in skills_list
   > - Full Instructions - loaded via skill_view when needed
   > - Linked Files (references, templates) - loaded on demand"
   `agent/prompt_builder.py`, lines 1763-1825:
   > `build_skills_system_prompt()` builds a compact index table from scanning `~/.hermes/skills/`, bundled `skills/`, and project-local `./.hermes/skills` or `./.agents/skills`.

5. **Prompt Caching Invariants & Alternation:**
   `g:\Finding-new-code\harness9\agent\prompt_caching.py`, lines 3-8:
   > "The default layout uses 4 cache_control breakpoints: the static system prefix, the end of the system prompt, and the last 2 non-system messages... This preserves intra-session caching while allowing new sessions to reuse the stable system-prompt prefix."

6. **Memory Provider Architecture:**
   `g:\Finding-new-code\harness9\agent\memory_manager.py`, lines 6-8:
   > "Only ONE external plugin provider is allowed at a time — attempting to register a second external provider is rejected with a warning. This prevents tool schema bloat and conflicting memory backends."
   `agent/memory_provider.py`, lines 110-150:
   > `MemoryProvider` ABC defines `initialize()`, `system_prompt_block()`, `prefetch()`, `sync_turn()`, `get_tool_schemas()`, and `handle_tool_call()`.

7. **Subagent Delegation & Safety:**
   `g:\Finding-new-code\harness9\tools\delegate_tool.py`, lines 10-18, 50-58, 78-90:
   > Each child agent receives a fresh conversation, isolated `task_id`, parent toolsets with `DELEGATE_BLOCKED_TOOLS` (`delegate_task`, `clarify`, `memory`, `send_message`, `cronjob`) stripped.
   > Dangerous shell commands run through `_subagent_auto_deny`, preventing deadlocking parent interactive stdin.

8. **Sandboxing & Environments:**
   `g:\Finding-new-code\harness9\tools\environments/base.py`, lines 1-7, 82-95:
   > `BaseEnvironment` ABC executes commands via fresh `bash -c` process with `_BoundedOutputCollector` capturing 40/60 head-tail window and spilling up to 5MB to disk.

9. **Existing M1 Adapter Limitation:**
   `adapters/hermes/bridge.py`, lines 89-98:
   > Invokes monolithic `Pipeline(topic=topic, output_dir=workspace_dir, ...).run()` all at once, bypassing Hermes's turn-by-turn agent loop, skill loading, and subagent delegation.

---

## 2. Logic Chain

1. **Step 1:** Observation 1 establishes the requirement to refactor H9 from an external monolithic pipeline into a direct Hermes Agent runtime execution.
2. **Step 2:** Observation 9 shows that the existing `adapters/hermes/bridge.py` executes the entire production pipeline synchronously inside a single tool call, which does not utilize the Hermes agent loop, native skills, or subagents.
3. **Step 3:** Observation 2 mandates that new capabilities must not bloat the narrow waist of `_HERMES_CORE_TOOLS` (Rung 6) and must preserve prompt caching. Therefore, H9 tools must be registered as a named service-gated toolset (`harness9`, Rung 3) per Observation 3.
4. **Step 4:** Observation 4 defines the exact skill structure (`SKILL.md` with YAML frontmatter) and progressive disclosure mechanism (`skills_list`, `skill_view`) that H9 domain workflows (`h9-research`, `h9-content-planning`, `h9-production`, `h9-hyperframes`) must adopt.
5. **Step 5:** Observation 6 shows that Hermes permits only one external memory provider at a time and integrates with SQLite `SessionDB`. To avoid duplicate persistence engines, H9's `CreatorProfile` and `PerformanceMemory` must be exposed via a `MemoryProvider` implementation that feeds `system_prompt_block()` and `prefetch()`.
6. **Step 6:** Observation 7 confirms that multi-source research can be cleanly isolated using `delegate_task`, ensuring web scraping traces do not flood the parent conversation history and respecting iteration budgets.
7. **Step 7:** Observation 8 establishes that subprocess rendering (FFmpeg, HyperFrames compilation) must execute via `BaseEnvironment` to ensure proper confinement in Docker/Modal/remote backends.
8. **Step 8:** To protect both runtimes from tight internal coupling, formal runtime protocols (`AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`) must be implemented in `src/h9_runtime/` as defined in `report.md`.

---

## 3. Caveats

- **No live code was altered:** The miner operated in strict READ-ONLY mode.
- **FFmpeg binary availability:** In offline development environments where `ffmpeg` is not installed on the host, `ExecutionRuntime` should utilize the procedural fallback video generator already present in `src/utils/ffmpeg.py`.
- **MCP configuration dependency:** MCP integration tests depend on either local mock MCP servers or active `mcp_servers` configuration in `~/.hermes/config.yaml`.

---

## 4. Conclusion

Refactoring Harness 9 to run directly through the Hermes runtime is fully architecturally viable and adheres to all core Hermes invariants. 

The complete survey, capability comparison matrix, exact APIs, formal interface definitions for `src/h9_runtime/`, and architectural constraints have been authored and published to:
`g:\Finding-new-code\harness9\.agents\survey_spec_miner_1\report.md`.

The implementation path for the downstream workers is well-defined:
1. Establish `src/h9_runtime/` protocols and capability bridge.
2. Register granular tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) in `tools/registry.py`.
3. Package workflows into native Hermes skills (`skills/h9-*/SKILL.md`).
4. Connect narrative planning to HyperFrames compilation via typed Production IR.
5. Wire memory via `H9CreatorMemoryProvider` and research via subagent `delegate_task`.
6. Confine rendering within `BaseEnvironment` and verify against the 8-dimension integration test suite.

---

## 5. Verification Method

To independently verify the observations, facts, and interface contracts:
1. **Tool Registry Verification:**
   Inspect `tools/registry.py` and run:
   ```bash
   pytest tests/test_hermes_adapter.py -v
   ```
2. **Skill Format Verification:**
   Inspect `skills/research/arxiv/SKILL.md` and verify YAML frontmatter parser in `tools/skills_tool.py`:
   ```bash
   python -c "from tools.skills_tool import skills_list, skill_view; print(skills_list()[:200])"
   ```
3. **Prompt Caching Invariants Verification:**
   Inspect `agent/prompt_caching.py` to confirm the 4-breakpoint layout and role alternation rules.
4. **H9 Runtime Protocols Verification:**
   Inspect `g:\Finding-new-code\harness9\.agents\survey_spec_miner_1\report.md` Section 5 to confirm all 7 runtime protocols (`AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`) match standard Python `typing.Protocol` and Pydantic v2 conventions.
