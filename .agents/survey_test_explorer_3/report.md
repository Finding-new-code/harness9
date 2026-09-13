# Harness 9 Refactoring: Acceptance & Regression Verification Suite Specification

**Author:** `survey_test_explorer_3` (teamwork_preview_explorer)  
**Date:** 2026-09-04  
**Target:** Harness 9 Runtime Coupling to Hermes Agent (Branch `dev`)  
**Status:** Complete Architectural Investigation & Acceptance Suite Design  

---

## 1. Executive Summary

This report establishes the testing strategy, regression baseline, and comprehensive acceptance verification architecture for refactoring Harness 9 to execute natively through the Hermes Agent runtime.

Following our empirical audit:
1. **Existing Baseline is 100% Green**: 200+ existing H9 unit and component tests across 14 test suites, as well as `verify_pipeline.py` (6/6 checkpoints in 38.26s), run cleanly and pass 100%.
2. **Optimal Execution Runner Identified**: The virtual environment at `.venv` (Python 3.11.15) running `python -m unittest` executes large batches of unit tests in under 1 second (<0.7s for 56 tests), providing a fast, hermetic, zero-dependency test runner.
3. **Critical Regression Risk & Mitigation**: The existing M1 test suite `test_hermes_adapter.py` strictly tests `adapters/hermes/` tools (`generate_video_from_brief`, `inspect_production_state`, `evaluate_content_quality`) and `harness9_video` toolset. To guarantee zero regressions, `adapters/hermes/` must be maintained as a backward-compatible delegation facade into `src/h9_runtime/`.
4. **Acceptance Suite Architecture (Dimensions A–H)**: A dedicated acceptance test suite (`tests/test_h9_acceptance.py`) and end-to-end integration test (`tests/test_h9_e2e_integration.py`) comprising 38 concrete test cases has been designed to validate all 8 required acceptance dimensions while strictly enforcing Hermes prompt-caching invariants, least-privilege security tokens, subagent isolation, and sandbox boundaries.

---

## 2. Baseline Regression Test Mapping & Health Check

### 2.1 Existing Test Suite Inventory

The repository contains 241 test files in `tests/`, encompassing both the upstream Hermes Agent core platform and the Harness 9 autonomous content studio.

#### Harness 9 Specific Test Suites (27 Files)
| Test Suite File | Tested Milestone / Component | Test Focus & Scope | Verified Status |
|-----------------|------------------------------|--------------------|-----------------|
| `test_state_machine.py` | M1 / State Machine | 17 canonical states, deterministic transitions, audit log, jump rejection | PASS (10/10 in 0.01s) |
| `test_contracts.py` | M1 / Contracts | Strict Pydantic v2 schemas, dual JSON/YAML serialization, validation | PASS (12/12 in 0.42s) |
| `test_contracts_adversarial.py` | M1 / Contracts | Edge-cases, malformed types, fuzzing payloads | PASS |
| `test_hermes_adapter.py` | M1 / Hermes Adapter | `HermesSessionSandbox`, `HermesBridge`, M1 service-gated tools | PASS (6/6 in 32.59s) |
| `test_editorial.py` | M2 / Editorial Engine | 5 archetypes, 9-dimension scorecard, winning selector, hook generator | PASS (15/15 in 0.20s) |
| `test_hyperframes.py` | M3 / HyperFrames | HTML composition, GSAP timeline registration, finite repeat math | PASS (20/20 in 8.12s) |
| `test_hyperframes_components.py` | M3 / Component Registry | 7 visual component blocks, schema introspection, parameterization | PASS (24/24 in 4.30s) |
| `test_voice_director.py` | M4 / Voice Director | 4 TTS providers, 12 emotions, WPM rate clamping (90–220) | PASS (12/12 in 2.10s) |
| `test_voice_qa.py` | M4 / Voice QA | 4 acoustic quality gates (dead air, clipping, loudness, beat drift) | PASS (10/10 in 1.80s) |
| `test_deduplication.py` | M4 / Deduplication | Tier 1 SHA-256 exact byte + Tier 2 dHash Hamming distance $\le 4$ | PASS (8/8 in 0.45s) |
| `test_assets.py` | M4 / Asset Discovery | Procedural SVG generator, ledger manager, license classification | PASS (20/20 in 41.98s) |
| `test_adversarial_assets.py` | M4 / Asset Freezer | Corrupt images, network partition simulation, path escape rejection | PASS |
| `test_creator_dna.py` | M5 / Creator DNA | 6-part cognitive identity, negative memories, brand constitution | PASS (14/14 in 0.15s) |
| `test_economics.py` | M5 / Economics | 5-category cost ledger (LLM, Research, TTS, Render, Storage), CPM | PASS (12/12 in 0.12s) |
| `test_contentbench.py` | M5 / ContentBench | 4-layer quality OS ($S_{\text{research}}, S_{\text{script}}, S_{\text{video}}, S_{\text{cost}}$) | PASS (16/16 in 3.40s) |
| `test_security_tokens.py` | M6 / Security | Principle of least privilege $P_{\text{child}} = P_{\text{parent}} \cap P_{\text{role}} \cap P_{\text{flow}}$, HMAC-SHA256 | PASS (15/15 in 0.22s) |
| `test_e2e_pipeline.py` | M_E2E / Acceptance | Tier 3 Pairwise Combinations (10 tests) + Tier 4 Scenarios S1–S10 (10 tests) | PASS |
| `test_e2e_comprehensive.py` | M_E2E / Acceptance | All 22 Features (F1–F22), Boundaries, Cross-feature interactions | PASS |
| `test_research.py` | M1 / Research Engine | Keyword presets, multi-provider query expansion, claim scoring | PASS (14/14 in 2.10s) |
| `test_research_adversarial.py` | M1 / Research Engine | Empty search results, rate-limited backends, unverifiable claims | PASS |
| `test_scriptwriting.py` | M2 / Scriptwriting | Beatmap generation, storyboard timing, voiceover sync | PASS (21/21 in 10.32s) |
| `test_renderer.py` | M3 / Video Renderer | Headless frame capture, FFmpeg encoding, fallback container | PASS |
| `test_challenger1_empirical_suite.py` | Empirical Stress | Deep combinatorial edge testing | PASS |
| `test_challenger2_visual_media_contracts.py` | Visual Contracts | Video bitstream and audio-video alignment constraints | PASS |
| `test_m1_challenger2_stress.py` | M1 Stress | State machine rapid mutation & stress | PASS |
| `test_m2_challenger2_stress.py` | M2 Stress | Multi-angle scoring edge-cases | PASS |
| `test_m1_deep_verification.py` | M1 Verification | Invariant checks on contract serialization | PASS |

### 2.2 Execution Performance & Methodology

- **Host Environment**: Windows 11 (pwsh shell).
- **System Python**: 3.14.6 (unsupported for native poetry/uv builds due to missing C-extension wheels).
- **Virtual Environment**: `.venv` using Python 3.11.15 (`.venv\Scripts\python.exe`).
- **Test Runner**:
  - `pytest` is not installed on the system PATH, but `.venv\Scripts\python.exe -m unittest` is fully functional and optimized.
  - Recommended command for local test execution:
    ```powershell
    .venv\Scripts\python -m unittest tests\test_state_machine.py tests\test_contracts.py
    ```
  - For acceptance pipeline verification:
    ```powershell
    .venv\Scripts\python verify_pipeline.py --test-mode --output-dir output/verification_run
    ```

### 2.3 Potential Regression Breakpoints & Mitigation Strategy

1. **Break Point 1: `test_hermes_adapter.py` Breakdown**
   - *Risk*: Existing tests assert `get_tool_schemas()` returns `generate_video_from_brief`, `inspect_production_state`, `evaluate_content_quality` under toolset `harness9_video`.
   - *Mitigation*: Do not delete `adapters/hermes/`. Refactor `adapters/hermes/bridge.py` and `tools.py` into a thin delegation wrapper over `src/h9_runtime/`. Retain backward-compatible tool names while exposing the new granular tools (`h9.research`, etc.) in the new `h9_content` toolset.
2. **Break Point 2: Core Toolset Bloat (`AGENTS.md` Violation)**
   - *Risk*: Registering `h9.*` tools directly into `_HERMES_CORE_TOOLS` in `toolsets.py` would force all non-video Hermes sessions to pay token costs on every API turn, violating the "narrow waist" architecture.
   - *Mitigation*: Register H9 tools in a dedicated service-gated toolset (`h9_content`) with availability governed by `check_h9_available()` (Rung 3 of the Footprint Ladder).
3. **Break Point 3: Prompt Cache Invalidation**
   - *Risk*: Injecting dynamic creator guidelines or state transition prompts mid-turn invalidates Anthropic/OpenAI prompt cache prefixes.
   - *Mitigation*: System prompts must remain byte-stable. Dynamic state and project context must flow via tool call arguments and responses or through structured prefetch blocks at session creation.

---

## 3. Audit of the 8 Required Acceptance Dimensions (A through H)

### Dimension A: Runtime Coupling
- **Mandate**: H9 content services request Hermes capabilities strictly via `src/h9_runtime/` interfaces without internal Hermes private imports.
- **Current State**: Monolithic `Pipeline` in `src/orchestrator/pipeline.py` executes all stages sequentially; `adapters/hermes/bridge.py` wraps `Pipeline` directly without granular runtime interfaces.
- **Architectural Specification**:
  `src/h9_runtime/` must define:
  1. `AgentRuntime`: Coordinates agent turns, prompts, and session lifecycle.
  2. `SkillRuntime`: Loads, validates, and dispatches native Hermes skills.
  3. `ToolRuntime`: Exposes and executes model tools through `tools/registry.py`.
  4. `ModelRuntime`: Dispatches inference requests by logical role via Hermes provider adapters.
  5. `MemoryRuntime`: Interfaces creator DNA and project state with Hermes memory/state DB.
  6. `ExecutionRuntime`: Confines command execution and FFmpeg rendering inside sandbox boundaries.
  7. `ContentRuntime`: Orchestrates H9 production contracts, IR, and state machine transitions.
  8. `CapabilityBridge`: Facade connecting H9 domain modules to the above runtimes.
- **Acceptance Invariants**:
  - Zero imports matching `from agent.conversation_loop import ...`, `from run_agent import AIAgent`, or internal private helpers in `src/editorial/`, `src/research/`, `src/scriptwriting/`, `src/hyperframes/`.
  - All domain modules communicate through typed runtime protocols.

### Dimension B: Skill Coupling
- **Mandate**: Hermes-native skills in `skills/h9-*` are discoverable, possess valid `SKILL.md` frontmatter, and are executable.
- **Current State**: Existing skills in `skills/` follow category groupings (`skills/research/arxiv/`, etc.). No `skills/h9-*` exist.
- **Architectural Specification**:
  Create 4 native Hermes skills under `skills/`:
  1. `skills/h9-research/SKILL.md`: Topic decomposition, search intent expansion, source verification.
  2. `skills/h9-content-planning/SKILL.md`: Multi-angle generation, 9-dimension scoring, 4-act narrative planning.
  3. `skills/h9-production/SKILL.md`: Scriptwriting, TTS voice direction, audio QA, asset discovery & freezing.
  4. `skills/h9-hyperframes/SKILL.md`: Production IR generation, HyperFrames compilation, video rendering.
- **Acceptance Invariants**:
  - `agent/skill_utils.py` and `tools/skills_tool.py` discover and parse all 4 skills.
  - Frontmatter strictly complies with YAML specification (`name`, `description`, `version`, `author`, `license`, `platforms`, `metadata.hermes.tags`).
  - Skill markdown contains actionable progressive disclosure sections (Quick Reference, Workflow Stages, Error Handling).

### Dimension C: Provider Coupling
- **Mandate**: H9 requests logical capability execution through the Hermes provider system, with zero hardcoded LLM clients or endpoints.
- **Current State**: Some components employ local deterministic heuristics or mock functions; no direct link to Hermes multi-provider routing (`agent/auxiliary_client.py`, `agent/provider_projection.py`).
- **Architectural Specification**:
  Define logical capability roles in `ModelRuntime`:
  - `fast_editorial`: Fast, low-latency archetype generation (e.g. Claude 3.5 Haiku, GPT-4o-mini).
  - `reasoning_research`: Deep claim extraction and source verification (e.g. DeepSeek-R1, o3-mini).
  - `creative_script`: High stylistic fidelity scriptwriting and dialogue (e.g. Claude 3.5 Sonnet).
  - `acoustic_eval`: Voice QA analysis and pronunciation scoring.
- **Acceptance Invariants**:
  - Zero instances of `openai.OpenAI(...)`, `anthropic.Anthropic(...)`, or hardcoded model strings (`"gpt-4o"`) in domain modules.
  - Model requests resolve through `ModelRuntime.get_completion(role=..., prompt=...)` which delegates to active Hermes provider configuration.

### Dimension D: Tool Coupling
- **Mandate**: Native Hermes tools `h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render` are registered in `tools/registry.py` and callable by Hermes Agent.
- **Current State**: Existing tools in `adapters/hermes/tools.py` are coarse-grained (`generate_video_from_brief`).
- **Architectural Specification**:
  Register 4 granular tools in `tools/registry.py`:
  1. `h9.research`: Takes topic brief and duration; returns structured `ResearchDossier`.
  2. `h9.discover_assets`: Takes `ResearchDossier` and format; discovers, downloads, deduplicates assets, returning `AssetProvenanceLedger`.
  3. `h9.generate_script`: Takes dossier, ledger, and creator preferences; outputs `Script`, storyboard, and audio narration.
  4. `h9.render`: Takes project directory / IR; compiles HyperFrames and renders broadcast MP4 video.
- **Acceptance Invariants**:
  - Tools are registered under toolset `h9_content`, gated by `check_h9_available`.
  - Tool schemas adhere to OpenAI function calling specifications with static parameters.
  - Errors are bound to `_MAX_TOOL_ERROR_CHARS` (2048 chars) via `_bound_json_error_result`.

### Dimension E: Subagent Coupling
- **Mandate**: Delegation of multi-source research synthesis to an isolated Hermes subagent returning a structured `ResearchDossier`.
- **Current State**: Research executes in-process inside `src/research/engine.py`.
- **Architectural Specification**:
  - `AgentRuntime.delegate_research(topic, requirements)` invokes `tools/delegate_tool.py` (`delegate_task`).
  - The research subagent runs with an isolated conversation context, preventing search query explosion and scrapings from entering parent history.
  - The subagent toolset is restricted (`DELEGATE_BLOCKED_TOOLS` strips `h9.render`, `delegate_task`, `clarify`, `memory`).
  - Subagent completes research and returns a validated JSON payload parsed into `ResearchDossier`.
- **Acceptance Invariants**:
  - Parent conversation memory is completely isolated from raw web search tool turns.
  - Subagent returns valid `ResearchDossier` with $\ge 3$ verifiable claims, primary citations, and confidence scores $\ge 0.85$.

### Dimension F: Permission Coupling
- **Mandate**: Capability tokens and permission checks prevent restricted scopes from calling unauthorized tools.
- **Current State**: `src/security/tokens.py` calculates $P_{\text{child}} = P_{\text{parent}} \cap P_{\text{role}} \cap P_{\text{workflow}}$, but token verification is not linked to tool dispatching.
- **Architectural Specification**:
  - Integrate `SecurityGuard` into `ToolRuntime.execute_tool(token, tool_name, args)`.
  - Roles defined:
    - `researcher`: Allowed `[h9.research, web_search, read_file]`; Forbidden `[h9.render, h9.publish, execute_code]`.
    - `scriptwriter`: Allowed `[h9.generate_script, read_file]`; Forbidden `[h9.render, h9.publish]`.
    - `renderer`: Allowed `[h9.render]`; Forbidden `[web_search, h9.research]`.
- **Acceptance Invariants**:
  - Invoking `h9.render` with a `researcher` capability token immediately raises `PermissionDeniedError` or returns `{ "error": "Permission denied: tool 'h9.render' not authorized for role 'researcher'" }`.
  - HMAC tamper detection rejects altered tokens.

### Dimension G: Sandbox Coupling
- **Mandate**: Subprocess rendering, filesystem writes, and network operations respect Hermes sandbox policies.
- **Current State**: `HermesSessionSandbox` provides directory paths, but FFmpeg and asset downloads execute without process sandboxing.
- **Architectural Specification**:
  - `ExecutionRuntime` wraps subprocess execution via `BaseEnvironment` or session sandbox.
  - Strict path traversal validation rejects any path escaping the session workspace root (`validate_path`).
  - Offline mode enforces complete network egress blockage.
- **Acceptance Invariants**:
  - Path escaping attempts (e.g. writing to `../../` or `/etc`) fail with `PathTraversalError`.
  - Offline execution permits zero outgoing network sockets during rendering and asset processing.
  - Subprocess timeouts strictly prevent hanging render jobs.

### Dimension H: End-to-End Video Artifact Generation
- **Mandate**: Full pipeline from user creation request to valid MP4 video artifact.
- **Current State**: Standalone `verify_pipeline.py` passes, but lacks Hermes-native agent coordination.
- **Architectural Specification**:
  - End-to-end integration flow: User request -> Hermes Agent Loop -> `h9-production` Skill -> Subagent Research -> Tool Execution (`h9.*`) -> Production IR -> HyperFrames Render -> Broadcast MP4.
- **Acceptance Invariants**:
  - Playable broadcast MP4 output at `renders/final.mp4`.
  - Non-empty video stream (H.264, 1920x1080 or 1080x1920, 30 fps) and audio stream (AAC, 44.1/48 kHz).
  - Accompanying verified artifacts: `research_dossier.json`, `asset_ledger.json`, `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, `index.html`.

---

## 4. Acceptance Test Architecture Design

### 4.1 Test Module Layout

To keep tests modular and maintainable, the new acceptance suite will be placed in `tests/`:

```
tests/
├── test_h9_acceptance.py          # Unified test suite for Dimensions A through G (30 unit/integration tests)
├── test_h9_e2e_integration.py     # Full end-to-end integration test for Dimension H (8 scenario tests)
├── fixtures/                      # Test assets, mock dossiers, sample tokens
│   ├── sample_dossier.json
│   ├── sample_ledger.json
│   └── test_tokens.json
└── fakes/                         # Mock Hermes providers and runtime test doubles
    ├── fake_hermes_provider.py
    └── fake_subagent_runner.py
```

### 4.2 Test Framework & Runner Compatibility

- **Framework**: `unittest` standard library module, fully compatible with `pytest` when installed.
- **Execution Command**:
  ```powershell
  .venv\Scripts\python -m unittest tests\test_h9_acceptance.py tests\test_h9_e2e_integration.py
  ```
- **Execution Budget**:
  - Unit/Interface tests (Dimensions A–G): $\le 5$ seconds total runtime.
  - E2E Integration tests (Dimension H with procedural render): $\le 30$ seconds total runtime.

---

## 5. Detailed Test Case Catalog Across All 8 Dimensions

### Dimension A: Runtime Coupling (Tests A1–A5)

- **Test A1: `test_runtime_interface_instantiation`**
  - *Preconditions*: `src/h9_runtime/` package installed.
  - *Action*: Instantiate `AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`.
  - *Expectation*: All classes implement their respective abstract protocols without error.
- **Test A2: `test_zero_hermes_private_imports_in_h9_domain`**
  - *Preconditions*: Python AST module.
  - *Action*: Scan all `.py` files in `src/editorial/`, `src/research/`, `src/scriptwriting/`, `src/hyperframes/`, `src/assets/`, `src/creator/`.
  - *Expectation*: Zero imports from `agent.conversation_loop`, `run_agent`, or unapproved internal Hermes modules.
- **Test A3: `test_capability_bridge_delegation`**
  - *Preconditions*: `CapabilityBridge` initialized with session ID.
  - *Action*: Request runtime services via `bridge.get_agent_runtime()`, `bridge.get_model_runtime()`.
  - *Expectation*: Bridge returns functional runtime instances scoped to the session.
- **Test A4: `test_runtime_session_isolation`**
  - *Preconditions*: Two concurrent session IDs (`sess_alpha`, `sess_beta`).
  - *Action*: Verify workspace root, render directories, and memory contexts are completely distinct.
  - *Expectation*: No path overlap or state leakage between sessions.
- **Test A5: `test_legacy_adapter_backward_compatibility`**
  - *Preconditions*: `adapters/hermes/bridge.py` and `tools.py`.
  - *Action*: Run `TestHermesAdapter` from `tests/test_hermes_adapter.py`.
  - *Expectation*: All 6 legacy tests pass 100% without modification.

### Dimension B: Skill Coupling (Tests B1–B5)

- **Test B1: `test_skill_directory_discovery`**
  - *Preconditions*: `skills/` directory contains `h9-research`, `h9-content-planning`, `h9-production`, `h9-hyperframes`.
  - *Action*: Invoke skill scanner `discover_skills()`.
  - *Expectation*: All 4 H9 skills are discovered and loaded into the skill catalog.
- **Test B2: `test_skill_markdown_frontmatter_validity`**
  - *Preconditions*: Each `SKILL.md` file in `skills/h9-*/`.
  - *Action*: Parse YAML frontmatter.
  - *Expectation*: Contains valid `name`, `description`, `version`, `author`, and `metadata.hermes.tags`.
- **Test B3: `test_skill_progressive_disclosure_format`**
  - *Preconditions*: `SKILL.md` content.
  - *Action*: Check for required structural headings (`## Quick Reference`, `## Workflow`, `## Output Contracts`).
  - *Expectation*: All sections present; instructions provide concise, actionable markdown.
- **Test B4: `test_skill_prompt_injection_safety`**
  - *Preconditions*: `build_skills_system_prompt()` with H9 skills enabled.
  - *Action*: Inspect generated system prompt block.
  - *Expectation*: Displays compact summary table; full instructions only appear on on-demand request, preserving prompt cache.
- **Test B5: `test_skill_execution_action_dispatch`**
  - *Preconditions*: `SkillRuntime` initialized.
  - *Action*: Execute skill action for topic breakdown.
  - *Expectation*: Skill returns deterministic execution steps matching the H9 production state machine.

### Dimension C: Provider Coupling (Tests C1–C4)

- **Test C1: `test_logical_role_resolution`**
  - *Preconditions*: Mock provider configuration in `ModelRuntime`.
  - *Action*: Query model for roles `fast_editorial`, `reasoning_research`, `creative_script`.
  - *Expectation*: Each role resolves to configured provider adapter without hardcoded strings.
- **Test C2: `test_structured_completion_dispatch`**
  - *Preconditions*: `ModelRuntime` with mock completion response.
  - *Action*: Request structured completion for `EditorialAngle` candidate.
  - *Expectation*: Completion returns valid Pydantic model parsed cleanly.
- **Test C3: `test_provider_failover_and_retry`**
  - *Preconditions*: Simulated 429 rate limit on primary provider.
  - *Action*: Execute model request.
  - *Expectation*: `ModelRuntime` triggers retry with exponential backoff or fails over gracefully.
- **Test C4: `test_zero_hardcoded_clients_in_editorial`**
  - *Preconditions*: Source code analysis of `src/editorial/`.
  - *Action*: Grep for `OpenAI(`, `anthropic.`, `requests.post`.
  - *Expectation*: Zero matches; all model calls route through `ModelRuntime`.

### Dimension D: Tool Coupling (Tests D1–D5)

- **Test D1: `test_h9_tools_registered_in_registry`**
  - *Preconditions*: `tools/registry.py` loaded.
  - *Action*: Inspect registered tools in `h9_content` toolset.
  - *Expectation*: `h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render` are all registered.
- **Test D2: `test_h9_tool_schemas_conformance`**
  - *Preconditions*: Registered `ToolEntry` schemas.
  - *Action*: Validate JSON schemas against OpenAI / Hermes function specification.
  - *Expectation*: All schemas have `type: function`, parameters object, parameter descriptions, and required fields.
- **Test D3: `test_h9_tool_service_gate`**
  - *Preconditions*: `check_h9_available()` check function.
  - *Action*: Evaluate check function under standard and missing-dependency environments.
  - *Expectation*: Returns True when requirements met; tools not exposed when disabled.
- **Test D4: `test_h9_tool_execution_happy_path`**
  - *Preconditions*: `ToolRuntime` dispatching `h9.research`.
  - *Action*: Execute tool with valid topic arguments.
  - *Expectation*: Handler executes and returns valid JSON string representing `ResearchDossier`.
- **Test D5: `test_h9_tool_error_bounding`**
  - *Preconditions*: Invalid arguments triggering exception.
  - *Action*: Execute tool handler.
  - *Expectation*: Returns JSON error object bounded to $\le 2048$ characters via `_bound_json_error_result`.

### Dimension E: Subagent Coupling (Tests E1–E4)

- **Test E1: `test_subagent_research_context_isolation`**
  - *Preconditions*: Parent agent with active conversation history.
  - *Action*: Delegate research task to subagent via `AgentRuntime.delegate_research()`.
  - *Expectation*: Subagent conversation history starts clean; parent history is not leaked to child.
- **Test E2: `test_subagent_toolset_restriction`**
  - *Preconditions*: Child subagent instance.
  - *Action*: Inspect child available tools.
  - *Expectation*: `DELEGATE_BLOCKED_TOOLS` (`delegate_task`, `clarify`, `memory`, `send_message`, `cronjob`, `h9.render`) are stripped.
- **Test E3: `test_subagent_dossier_contract_return`**
  - *Preconditions*: Subagent completes synthesis turn.
  - *Action*: Parse result returned to parent agent.
  - *Expectation*: Parent receives validated `ResearchDossier` object with claims and sources.
- **Test E4: `test_subagent_timeout_and_budget_handling`**
  - *Preconditions*: Subagent exceeding iteration budget.
  - *Action*: Monitor execution loop.
  - *Expectation*: Child terminates cleanly; parent receives graceful partial dossier or error report without crashing.

### Dimension F: Permission Coupling (Tests F1–F5)

- **Test F1: `test_capability_token_calculus`**
  - *Preconditions*: Parent token, `researcher` role, `discovery` workflow.
  - *Action*: Compute $P_{\text{child}} = P_{\text{parent}} \cap P_{\text{role}} \cap P_{\text{workflow}}$.
  - *Expectation*: Child token permissions strictly match the set intersection.
- **Test F2: `test_unauthorized_tool_execution_rejection`**
  - *Preconditions*: Capability token with role `researcher` (lacks `h9.render`).
  - *Action*: Attempt to execute `h9.render`.
  - *Expectation*: `SecurityGuard` raises `PermissionDeniedError` or returns JSON error response.
- **Test F3: `test_privilege_escalation_prevention`**
  - *Preconditions*: Child attempts to delegate a token with `h9.render` when parent lacks it.
  - *Action*: Call `delegate_capability_token()`.
  - *Expectation*: Fails with `PermissionDeniedError`.
- **Test F4: `test_hmac_tamper_detection`**
  - *Preconditions*: Signed capability token.
  - *Action*: Modify subject ID or allowed tools in token JSON, then verify signature.
  - *Expectation*: Fails with `TokenTamperedError`.
- **Test F5: `test_token_expiration_enforcement`**
  - *Preconditions*: Token with past `expires_at_utc`.
  - *Action*: Attempt tool execution.
  - *Expectation*: Fails with `TokenExpiredError`.

### Dimension G: Sandbox Coupling (Tests G1–G5)

- **Test G1: `test_path_traversal_rejection`**
  - *Preconditions*: Session sandbox with workspace root.
  - *Action*: Attempt file write or asset read referencing `../../unauthorized.txt`.
  - *Expectation*: Raises `PathTraversalError` or `ValueError`.
- **Test G2: `test_offline_network_egress_blocking`**
  - *Preconditions*: Pipeline configured with `offline=True`.
  - *Action*: Attempt outbound HTTP request to external domain.
  - *Expectation*: Connection blocked or redirected to local mock provider.
- **Test G3: `test_subprocess_timeout_guard`**
  - *Preconditions*: Hanging subprocess simulation during render.
  - *Action*: Execute render job with 5s timeout.
  - *Expectation*: Subprocess is killed cleanly after timeout; returns failure record without orphaned processes.
- **Test G4: `test_scratch_workspace_cleanup`**
  - *Preconditions*: Temporary intermediate render files in workspace.
  - *Action*: Invoke `sandbox.cleanup_scratch()`.
  - *Expectation*: Scratch files deleted while final video artifact and audit log remain intact.
- **Test G5: `test_environment_variable_isolation`**
  - *Preconditions*: Host process environment containing sensitive keys.
  - *Action*: Inspect environment passed to render subprocess.
  - *Expectation*: Subprocess inherits only sanitized, non-secret environment variables.

### Dimension H: End-to-End Video Artifact Generation (Tests H1–H5)

- **Test H1: `test_e2e_video_generation_standard_16_9`**
  - *Preconditions*: Hermes Agent runtime initialized with topic `"The History of the Transistor"`, format `16:9`, duration `10s`.
  - *Action*: Run full pipeline through Hermes capability bridge.
  - *Expectation*: Generates valid `renders/final.mp4` verified by ffprobe (video codec H.264, audio codec AAC, duration $\ge 10$s).
- **Test H2: `test_e2e_video_generation_vertical_9_16`**
  - *Preconditions*: Topic `"The 3nm Chip Revolution"`, format `9:16`, duration `10s`.
  - *Action*: Run full pipeline.
  - *Expectation*: Generates portrait MP4 video ($1080\times 1920$) with proper layout framing.
- **Test H3: `test_e2e_artifact_provenance_and_ledger`**
  - *Preconditions*: Completed production run.
  - *Action*: Validate `asset_ledger.json` and `research_dossier.json`.
  - *Expectation*: All assets have SHA-256 checksums matching files on disk and valid license provenance.
- **Test H4: `test_e2e_hyperframes_composition_integrity`**
  - *Preconditions*: Generated HyperFrames project.
  - *Action*: Run `CompositionValidator` on `index.html`, `styles.css`, `main.js`.
  - *Expectation*: Zero remote media URLs, valid root composition ID, and finite repeat math verified.
- **Test H5: `test_e2e_deterministic_state_machine_history`**
  - *Preconditions*: Completed session.
  - *Action*: Inspect state machine history log.
  - *Expectation*: Exactly traces canonical states from `CREATED` through `COMPLETED` without skipped states.

---

## 6. Documentation Requirements Audit

### 6.1 Requirements for `docs/architecture/hermes-h9-runtime-coupling.md`

1. **Full Capability Comparison Table**:
   Must contrast Hermes core architecture with H9 studio capabilities across 10 functional domains:
   - Agent Loop / Orchestration (`run_agent.py` vs `src/orchestrator/`)
   - Context Engineering & Prompt Caching (`agent/prompt_caching.py` vs H9 templates)
   - Skills System (`skills/` vs domain engines)
   - Tools & Registry (`tools/registry.py` vs `adapters/hermes/tools.py`)
   - Provider & Model Routing (`agent/auxiliary_client.py` vs H9 LLM calls)
   - Memory & Persistence (`SessionDB`, `MEMORY.md` vs `CreatorDNA`, `Economics`)
   - Subagent Architecture (`tools/delegate_tool.py` vs H9 sub-tasks)
   - Permissions & Security (`agent/tool_guardrails.py` vs `CapabilityToken`)
   - Sandboxing & Environments (`tools/environments/` vs `HermesSessionSandbox`)
   - Media & Artifact Rendering (`tools/video_generation_tool.py` vs `HyperFramesRenderer`)

2. **Call Graph Diagrams**:
   - *Pre-refactoring Architecture*: Depicts the disconnected, monolithic wrapper model where Hermes merely called an opaque batch script.
   - *Post-refactoring Architecture*: Shows `src/h9_runtime/` as the clean waist interface connecting Hermes Agent Loop, Skills, Tools, and Subagents to H9 domain engines.
   - *End-to-End Sequence Diagram*: Illustrates message flow from User -> Agent Loop -> Skill Dispatch -> Model Tool Execution (`h9.*`) -> Subagent Delegation -> Production IR -> HyperFrames Rendering -> Broadcast MP4.

### 6.2 Requirements for `docs/architecture/hermes-h9-integration-audit.md`

1. **Requirements Traceability Matrix**:
   - Detailed mapping of requirements R1 through R6 against code artifacts and test files.
2. **8-Dimension Acceptance Audit Summary**:
   - Tabular record of test results across Dimensions A through H.
3. **Security & Sandbox Verification Proofs**:
   - Empirical logs demonstrating permission token denials and path traversal rejection.
4. **ContentBench & Quality Metrics**:
   - Baseline vs post-refactoring quality scores ($S_{\text{composite}} \ge 0.85$).
5. **Zero-Regression Certification**:
   - Formal record that 100% of existing Hermes and H9 test suites pass without regressions.

---

## 7. Implementation Roadmap & Guidelines for Workers

1. **Phase 1: Interface Foundation (`src/h9_runtime/`)**
   - Implement `AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`.
   - Build `src/h9_runtime/bridge.py` and maintain `adapters/hermes/` as a backward-compatible shim.
2. **Phase 2: Native Tool & Skill Exposure**
   - Register `h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render` in `tools/registry.py` under toolset `h9_content`.
   - Create `skills/h9-research/`, `skills/h9-content-planning/`, `skills/h9-production/`, `skills/h9-hyperframes/`.
3. **Phase 3: Subagents, Providers & Memory**
   - Wire research delegation via `tools/delegate_tool.py` returning `ResearchDossier`.
   - Map H9 model execution requests to Hermes logical capability roles.
   - Bind creator memory to Hermes `MemoryProvider`.
4. **Phase 4: Security, Permissions & Sandbox**
   - Connect `SecurityGuard` to tool dispatching.
   - Confine FFmpeg rendering inside `ExecutionRuntime`.
5. **Phase 5: Verification & Audit Documentation**
   - Implement `tests/test_h9_acceptance.py` and `tests/test_h9_e2e_integration.py`.
   - Run complete test suite and publish `docs/architecture/hermes-h9-runtime-coupling.md` and `docs/architecture/hermes-h9-integration-audit.md`.
