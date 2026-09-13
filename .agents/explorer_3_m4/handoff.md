# Milestone 4 Technical Exploration Report — Part 3: Isolated Subagent Research Delegation (R4.3)

**Agent**: `explorer_3_m4`  
**Role**: Read-only Technical Explorer  
**Scope**: Milestone 4 Technical Exploration — Part 3: Isolated Subagent Research Delegation (R4.3)  
**Authoritative User Request**: `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md`  
**Project Scope Document**: `g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_4\PROJECT.md`  
**Date**: 2026-09-05  

---

## Executive Summary

This report establishes the complete architectural and engineering design for **Milestone 4 Part 3: Isolated Subagent Research Delegation (R4.3)**. It investigates how Hermes Agent coordinates subagents, evaluates the existing Harness 9 research synthesis pipeline (`src/research/`, `skills/h9-research/`, `tools/h9_content_tools.py`, `src/models/contracts.py`), examines the runtime boundary interface (`src/h9_runtime/`), and defines how `h9.research` delegates multi-source research synthesis to an isolated Hermes subagent returning a validated Pydantic `ResearchDossier`.

Key findings:
1. **Subagent Architecture**: Hermes implements subagents in `tools/delegate_tool.py` via `delegate_task(...)` and `_build_child_agent(...)`, executing child `AIAgent` instances inside `DaemonThreadPoolExecutor` with headless quiet mode, clean context, dedicated `SessionDB` handles, and non-interactive approval callbacks (`_subagent_auto_deny`).
2. **Structured Output Contract**: Hermes includes native JSON Schema enforcement in `tools/delegation_output_schema.py` (`coerce_output_schema`, `append_output_contract`, `validate_output`, `build_retry_message`), providing automated 1-turn bounded retry on schema validation failures.
3. **Sacred Prompt Caching**: The parent agent's context window is strictly protected. The child agent's internal reasoning, intermediate tool calls (`web_search`, `read_file`), and tool outputs never enter parent conversation history; only the outer `delegate_task` invocation and final summary/result message are recorded.
4. **Data Contract Alignment**: `src/models/contracts.py:238` defines `ResearchDossier` as a Pydantic v2 model (`H9BaseModel`) with `SourceRecord` and `ClaimRecord`. Its JSON schema (`ResearchDossier.model_json_schema()`) directly powers the subagent's structured output contract.
5. **Logical Capability Mapping**: In `src/h9_runtime/models.py`, `CapabilityRole.REASONING_RESEARCH` maps to reasoning models (e.g. `deepseek-r1` via OpenRouter), allowing research subagents to execute on deep reasoning models while the parent orchestrator operates on fast conversational models.

---

## 1. Observation

### 1.1 Hermes Subagent Spawning & Coordination Patterns

#### 1.1.1 Tool Definition and Entry Point
- **File**: `tools/delegate_tool.py`
- **Lines 3670–3703**: `delegate_task` function signature:
  ```python
  def delegate_task(
      goal: Optional[str] = None,
      context: Optional[str] = None,
      tasks: Optional[List[Dict[str, Any]]] = None,
      max_iterations: Optional[int] = None,
      role: Optional[str] = None,
      background: Optional[bool] = None,
      output_schema: Optional[Dict[str, Any]] = None,
      action: Optional[str] = None,
      subagent_id: Optional[str] = None,
      message: Optional[str] = None,
      parent_agent=None,
      credentials_cfg: Optional[Dict[str, Any]] = None,
  ) -> str:
  ```
  The tool supports single-task execution (`goal`, `context`, `output_schema`) and parallel batch execution (`tasks=[{goal, context, output_schema}, ...]`).

#### 1.1.2 Child Agent Construction & Context Isolation
- **File**: `tools/delegate_tool.py`
- **Lines 1630–2058**: `_build_child_agent(...)`:
  - **Quiet Mode**: `quiet_mode=True` (line 2015) disables terminal spinners and user-facing interactive prompts.
  - **Ephemeral System Prompt**: `ephemeral_system_prompt=child_prompt` (line 2016). Built by `_build_child_system_prompt` (lines 1173–1278) from `goal`, `context`, `workspace_path`, `role`, `max_spawn_depth`, `child_depth`. Per `agent/system_prompt.py:879`, `ephemeral_system_prompt` is injected at API-call time and is **not** persisted into trajectories or stored prompts.
  - **Platform Marker**: `platform="subagent"` (line 2018).
  - **Repository Context Suppression**: `skip_context_files=True` (line 2019) prevents subagents from loading repo context files (`AGENTS.md`, workspace notes) that would inflate the prompt.
  - **Shared Memory Suppression**: `skip_memory=True` (line 2020) prevents subagents from reading or mutating the shared `MEMORY.md` file, avoiding cross-agent memory race conditions.
  - **Clarify Suppression**: `clarify_callback=None` (line 2021) ensures child agents cannot block by attempting to ask clarification questions from the user.
  - **Dedicated Database Handle**: `session_db=child_session_db` (lines 1976–1994). Each subagent opens its own `SessionDB(db_path=_parent_db_path)` pointing to the parent profile's SQLite database file, preventing parent session teardown from closing the child's database connection prematurely (`child._owns_session_db = True`, line 2064).
  - **Parent Lineage**: `parent_session_id=parent_agent.session_id` (line 2024).
  - **Independent Iteration Budget**: `iteration_budget=None` (line 2046). Each subagent receives an independent budget capped at `delegation.max_iterations` (default 50), preventing child loops from exhausting the parent's turn budget (`agent/iteration_budget.py:20–25`).

#### 1.1.3 Tool Scoping & Principle of Least Privilege
- **File**: `tools/delegate_tool.py`
- **Lines 50–59**: Core blocked tools:
  ```python
  DELEGATE_BLOCKED_TOOLS = frozenset(
      [
          "delegate_task",  # no recursive delegation (unless role='orchestrator')
          "clarify",        # no user interaction
          "memory",         # no writes to shared MEMORY.md
          "send_message",   # no cross-platform side effects
          "cronjob",        # no scheduling more work in the parent's name
      ]
  )
  ```
- **Lines 1306–1324**: `_strip_blocked_tools(toolsets)` removes blocked toolsets.
- **Lines 1741–1745**: `child_disabled_toolsets` strips blocked tools and `"kanban"` after composite toolset expansion.

#### 1.1.4 Approval Safety in Worker Threads
- **File**: `tools/delegate_tool.py`
- **Lines 61–117**:
  - Worker threads in `ThreadPoolExecutor` do not inherit `prompt_toolkit` TUI handles. Unhandled interactive prompts would call `input()` and deadlock the parent TUI process.
  - Handled via `_set_subagent_approval_cb`: defaults to `_subagent_auto_deny` (line 78), which returns `"deny"` so dangerous commands fail safely with an audible warning rather than hanging.

#### 1.1.5 Structured Output Validation & Bounded Retries
- **File**: `tools/delegation_output_schema.py`
- **Lines 22–27, 63–78, 105–150**:
  - `append_output_contract(context, schema)`: Injects `OUTPUT CONTRACT (machine-validated)` informing the model that its final answer must be a single JSON object conforming to the schema.
  - `validate_output(text, schema)`: Strips markdown code fences (`extract_json_candidate`), parses JSON, and validates with `jsonschema.validators.validator_for(schema)`.
  - `build_retry_message(errors)`: When validation fails, sends exactly **one** bounded retry turn carrying the validation errors verbatim without re-pasting the schema.
- **File**: `tools/delegate_tool.py`
- **Lines 3002–3056**: In `_run_single_child`:
  ```python
  _output_schema = getattr(child, "_delegate_output_schema", None)
  if isinstance(_output_schema, dict):
      _first_text = result.get("final_response") or ""
      _schema_valid, _schema_errors = validate_output(_first_text, _output_schema)
      if not _schema_valid and _first_text.strip() and not result.get("interrupted", False):
          _schema_retries = 1
          _retry_result = child.run_conversation(
              user_message=build_retry_message(_schema_errors),
              task_id=child_task_id,
              stream_callback=_relay_child_text,
          )
          ...
          _schema_valid, _schema_errors = validate_output(_retry_text, _output_schema)
  ```

#### 1.1.6 Prompt Caching & Context Headroom Preservation
- **File**: `tools/delegate_tool.py`
- **Lines 16–17**: *"The parent's context only sees the delegation call and the summary result, never the child's intermediate tool calls or reasoning."*
- **Lines 2402–2495**: `_apply_summary_budget(results, parent_agent)` calculates the parent's remaining context headroom fraction (`_SUMMARY_HEADROOM_FRACTION = 0.20`, line 124). If subagent results exceed the char budget, `_trim_summary_with_footer` truncates the response in context and spills the full text to `cache/delegation/subagent-summary-*.txt` via `_spill_summary_to_file`.
- **File**: `agent/system_prompt.py`
- **Lines 879–880**: `ephemeral_system_prompt` is excluded from the cached system prompt prefix, ensuring byte stability of parent and child prefixes.

---

### 1.2 H9 Research Synthesis Subsystem

#### 1.2.1 Research Engine & Query Expansion
- **File**: `src/research/engine.py`
- **Lines 34–57**: `ResearchEngine` manages multi-provider search dispatch (`MultiProviderDispatcher`), curated presets (`src/research/presets/`), and procedural fallbacks.
- **Lines 96–104**: `_generate_queries(topic)` expands a topic into 5 orthogonal query axes:
  1. `origin_history`: `f"{topic} history"`
  2. `technical_mechanism`: `f"{topic} technology"`
  3. `quantitative_metric`: `f"{topic} specifications"`
  4. `modern_impact`: `f"{topic} impact"`
  5. `visual_queries`: `f"{topic} photo"`
- **Lines 127–177**: Extracts factual sentences from search snippets, filters sentences between 40 and 280 characters, pairs them with `primary_source` and `corroborating_sources`, and scores them using `score_claim(...)` (`src/research/scoring.py`).
- **Lines 274–458**: `_synthesize_procedural(topic, target_duration)`: Generates deterministic seed-based research dossiers when offline or when external search is unavailable.
- **Lines 460–518**: `synthesize_research(topic, offline, target_duration, output_dir)`: Orchestrates live search, preset lookup, procedural fallback, and atomic persistence.

#### 1.2.2 Native Hermes Skill: `h9-research`
- **File**: `skills/h9-research/SKILL.md`
- **Lines 1–14**: Skill YAML frontmatter (`name: h9-research`, `version: 1.0.0`, `tags: [Content, Research, FactChecking, Verification, H9]`).
- **Lines 41–50**: Quick Reference:
  - Invocation tool: `h9.research(topic: str, depth: str = "standard", constraints: dict = None)`.
  - Depths: `overview` (15s), `standard` (30s), `deep` (60s+ deep synthesis delegating to isolated subagents).
  - Confidence threshold: $\ge 0.70$ with primary source provenance.
- **Lines 69–75**: Subagent delegation specification:
  - When `depth="deep"`, delegate sub-tasks to isolated Hermes subagents.
  - Provide isolated context and restricted toolsets (`web_search`, scraping, calculator).
  - Output structured findings conforming to `ResearchDossier`.

#### 1.2.3 Native Hermes Model Tool: `h9.research`
- **File**: `tools/h9_content_tools.py`
- **Lines 42–71**: Tool definition `H9_RESEARCH_SCHEMA`:
  - `name`: `h9.research`
  - `parameters`: `topic` (string, required), `depth` (enum: `["overview", "standard", "deep"]`, default `standard`), `constraints` (object).
- **Lines 179–211**: `handle_h9_research(args, **kwargs)`:
  - Resolves `session_id`.
  - Retrieves `bridge = get_capability_bridge(session_id=session_id)`.
  - Calls `dossier = bridge.plan_research(topic=topic.strip(), depth=depth, constraints=constraints)`.
  - Serializes `dossier.to_dict()` and returns `tool_result(dossier_dict)`.

#### 1.2.4 Data Models: Pydantic Contracts vs Dataclasses
- **File**: `src/models/contracts.py` (Pydantic v2 Production Contracts):
  - **Lines 196–204**: `SourceRecord(H9BaseModel)`: `title: str`, `url: str`, `publisher: Optional[str]`, `author: Optional[str]`, `published_date: Optional[str]`, `reliability_score: float = 0.8`.
  - **Lines 206–216**: `ClaimRecord(H9BaseModel)`: `claim_id: str`, `claim_text: str`, `category: str = "general"`, `confidence_score: float = 0.7`, `primary_source: SourceRecord`, `corroborating_sources: List[SourceRecord] = []`, `visual_cue_suggestion: str = ""`, `verification_notes: str = ""`.
  - **Lines 221–228**: `TalkingPointRecord(H9BaseModel)`: `beat_index: int`, `title: str`, `narrative_hook: str`, `supported_claim_ids: List[str]`, `estimated_duration_sec: float = 5.0`.
  - **Lines 230–236**: `StatisticRecord(H9BaseModel)`: `metric: str`, `value: str`, `context: str`, `source_claim_id: str`.
  - **Lines 238–254**: `ResearchDossier(H9BaseModel)`:
    ```python
    class ResearchDossier(H9BaseModel):
        topic: str = Field(..., min_length=1)
        schema_version: str = "2.0.0"
        run_id: str = ""
        generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
        headline: str = ""
        executive_summary: str = ""
        key_takeaways: List[str] = Field(default_factory=list)
        claims: List[ClaimRecord] = Field(default_factory=list)
        talking_points: List[TalkingPointRecord] = Field(default_factory=list)
        statistics: List[StatisticRecord] = Field(default_factory=list)
        suggested_visual_queries: List[str] = Field(default_factory=list)
        metadata: Dict[str, Any] = Field(default_factory=dict)
    ```
- **File**: `src/models/dossier.py`:
  - Lines 14–270: Dataclass implementations of `Source`, `Claim`, `TalkingPoint`, `Statistic`, `Summary`, `DossierMetadata`, and `ResearchDossier`. Both dataclass and Pydantic implementations share identical field semantics and dictionary conversion methods (`to_dict()`, `from_dict()`).

---

### 1.3 Runtime Boundary Interface

#### 1.3.1 AgentRuntime Protocol
- **File**: `src/h9_runtime/agent.py`
- **Lines 24–70**: `AgentRuntime` protocol definition:
  - `create_session(session_id, role, metadata) -> SessionState`
  - `delegate_subagent(parent_session_id, goal, role, context, allowed_toolsets, max_iterations, timeout_seconds) -> SubagentResult`
  - `interrupt_session(session_id, reason) -> bool`
  - `get_session_state(session_id) -> Optional[SessionState]`
  - `check_interrupt(session_id) -> bool`
  - `execute_turn(session_id, user_message, tool_results) -> Dict[str, Any]`
- **Lines 123–189**: `DefaultAgentRuntime.delegate_subagent(...)`:
  - Enforces tool security: `forbidden = {"delegate_task", "clarify", "memory", "h9.render"}`.
  - Restricts tools to `allowed_toolsets` (defaulting to `["web_search", "read_file"]`).
  - Records child subagent ID into parent session metadata (`parent_state.metadata["child_subagents"]`).
  - Emits `SubagentResult` with `SubagentStatus.COMPLETED` and structured data.

#### 1.3.2 HermesCapabilityBridge & Research Delegation
- **File**: `src/h9_runtime/bridge.py`
- **Lines 180–198**: `HermesCapabilityBridge.delegate_subagent` calls `self._agent.delegate_subagent(...)`.
- **Lines 404–441**: `HermesCapabilityBridge.plan_research(...)`:
  ```python
  if depth == "deep" and not offline:
      sub_res = self.delegate_subagent(
          parent_session_id=sid,
          goal=f"Conduct deep research on {topic}",
          role="researcher",
          context={"topic": topic, "depth": depth, "constraints": constraints or {}},
      )
      logger.info("Deep research delegated to subagent %s", sub_res.subagent_id)
  ```
- **Lines 621–648**: `HermesCapabilityBridge.delegate_subagent_task(...)` provides a high-level facade returning serialized dictionary status.

#### 1.3.3 Logical Capability Role Routing
- **File**: `src/h9_runtime/models.py`
- **Lines 69–73**:
  ```python
  CapabilityRole.REASONING_RESEARCH: {
      "model_name": "deepseek-r1",
      "provider": "openrouter",
      "cost_per_1k_tokens": 0.002,
  }
  ```
  This logical role allows research synthesis to route specifically to high-reasoning inference models with mathematical/factual verification capabilities.

---

## 2. Logic Chain

```
[Observation: tools/delegate_tool.py]
 Hermes subagents run as isolated AIAgents with quiet_mode=True, skip_memory=True,
 skip_context_files=True, dedicated SessionDB, and thread approval auto-deny.
          │
          ▼
[Observation: tools/delegation_output_schema.py]
 delegate_task accepts output_schema (JSON Schema), appends an explicit output contract,
 validates child response with jsonschema, and performs 1 bounded retry on error.
          │
          ▼
[Observation: src/models/contracts.py]
 ResearchDossier is a Pydantic v2 BaseModel (H9BaseModel) containing ClaimRecord and
 SourceRecord, natively producing ResearchDossier.model_json_schema().
          │
          ▼
[Observation: agent/system_prompt.py & tools/delegate_tool.py]
 Parent conversation context never includes subagent turns or intermediate web searches;
 only the top-level tool call and final dossier enter the parent history.
 Prompt caching prefix is byte-stable.
          │
          ▼
[Deduction: Delegation Architecture Integration]
 When h9.research executes with depth="deep":
 1. HermesCapabilityBridge delegates to an isolated subagent via delegate_task.
 2. Subagent receives output_schema=ResearchDossier.model_json_schema().
 3. Subagent toolset is restricted to web_search, web_extract, and read_file (h9.render/memory stripped).
 4. Subagent executes orthogonal query research according to skills/h9-research/SKILL.md.
 5. Output is validated against ResearchDossier schema and parsed with zero data loss.
 6. If live search or provider times out, it gracefully degrades to procedural/preset synthesis.
```

1. **Isolation & Security Invariant**:
   - In `tools/delegate_tool.py:50–59`, `DELEGATE_BLOCKED_TOOLS` prevents child agents from recursively calling `delegate_task`, corrupting `MEMORY.md`, or interacting with the user via `clarify`.
   - In the H9 context, `h9.render` must be added to blocked tools for research subagents (`src/h9_runtime/agent.py:146`). A research subagent must only have access to information gathering tools: `web_search`, `web_extract`, and `read_file`.

2. **Output Contract Invariant**:
   - Free-form text research summaries risk parsing errors and missing fields in downstream editorial and scripting stages.
   - By feeding `ResearchDossier.model_json_schema()` directly to `delegate_task(output_schema=...)`, `tools/delegation_output_schema.py` automatically injects the machine-validation contract block and enforces validation.
   - If the LLM omits a required field (e.g. `primary_source` in a claim), `validate_output` catches the error and `build_retry_message` prompts the subagent with the exact field path (e.g. `$.claims[0].primary_source: 'primary_source' is a required property`), which is resolved in a single bounded retry.

3. **Prompt Caching Invariant**:
   - Prompt caching requires strict byte-level prefix stability across turns.
   - Because `AIAgent` in `tools/delegate_tool.py` runs subagents in separate conversation contexts (`skip_context_files=True`, `skip_memory=True`, `ephemeral_system_prompt=...`), the parent agent's message list is never altered during the subagent's execution.
   - The parent's context sees only:
     `{"role": "assistant", "tool_calls": [{"name": "h9.research", ...}]}` followed by
     `{"role": "tool", "content": "<json ResearchDossier>"}`.
   - Parent KV prompt caches remain 100% warm.

4. **Fault Tolerance & Fallback Invariant**:
   - If network connectivity is lost, search API keys are missing, or a subagent times out, the system must not crash.
   - In `src/research/engine.py:488–507`, resolution cascades: `_synthesize_live` -> `_match_preset` -> `_synthesize_procedural`.
   - The delegation bridge maintains this guarantee: if subagent delegation times out or fails schema validation after the retry turn, it falls back to the deterministic procedural synthesizer, always returning a valid, complete `ResearchDossier`.

---

## 3. Delegation Architecture Design

### 3.1 Architectural Component Topology

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      Parent AIAgent (Hermes / H9 Orchestrator)                  │
│                     Active Session: session_id = "sess_prod_001"                │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼ Tool Call: h9.research(topic, depth="deep")
┌─────────────────────────────────────────────────────────────────────────────────┐
│              tools/h9_content_tools.py (handle_h9_research)                     │
│                        Hermes Tool Registry (Rung 3)                            │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼ bridge.plan_research(...)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   HermesCapabilityBridge (src/h9_runtime/bridge.py)             │
│   Determines depth == "deep" -> calls delegate_subagent_task(...)               │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼ delegate_task(...)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       Hermes Subagent Orchestration Engine                      │
│                          (tools/delegate_tool.py)                               │
│                                                                                 │
│  1. Scopes tools: allowed = ["web_search", "web_extract", "read_file"]          │
│     Blocked: ["delegate_task", "clarify", "memory", "h9.render", "send_message"]│
│  2. Injects schema: output_schema = ResearchDossier.model_json_schema()         │
│  3. Model routing: CapabilityRole.REASONING_RESEARCH (deepseek-r1 / openrouter) │
│  4. Creates isolated child AIAgent:                                             │
│     - quiet_mode = True, platform = "subagent"                                  │
│     - skip_memory = True, skip_context_files = True                             │
│     - dedicated SessionDB connection (db_path = parent.db_path)                 │
│     - ephemeral_system_prompt = child_research_prompt                           │
│  5. Dispatches in DaemonThreadPoolExecutor worker thread                        │
│     - approval_callback = _subagent_auto_deny                                   │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼ Executes child.run_conversation(...)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      Isolated Research Child AIAgent                            │
│                                                                                 │
│  - Executes orthogonal query expansion (origin, technical, metrics, impact)    │
│  - Calls web_search / web_extract to gather authoritative citations             │
│  - Extracts atomic claims, verifies confidence >= 0.70                          │
│  - Formats final response conforming to OUTPUT CONTRACT JSON Schema             │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼ Validates with validate_output(text, schema)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       Output Schema Validation & Fallback                       │
│                                                                                 │
│  - Valid? -> Parse JSON into Pydantic ResearchDossier                           │
│  - Invalid? -> Send 1 bounded retry turn with build_retry_message(errors)       │
│  - Timeout / Error? -> Graceful fallback to procedural synthesis                │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼ Returns verified ResearchDossier
┌─────────────────────────────────────────────────────────────────────────────────┐
│      Parent AIAgent Context Appends Tool Result (Prompt Cache Preserved)        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Session Lifecycle

1. **Initialization**:
   - `handle_h9_research` receives tool arguments: `topic`, `depth`, `constraints`.
   - `HermesCapabilityBridge` retrieves or creates the caller's session state via `AgentRuntime.get_session_state(session_id)`.
   - If `depth == "deep"`, the bridge creates a child subagent delegation request.
2. **Subagent Spawning**:
   - Subagent ID is assigned: `subagent_id = f"sa-research-{uuid.uuid4().hex[:8]}"`.
   - A dedicated `SessionDB` instance is created pointing to the active profile's `state.db` file.
   - Child agent is configured with `parent_session_id = parent_session_id`.
   - Fresh `IterationBudget` is allocated (capped at 30 iterations for research).
3. **Execution & Supervision**:
   - Child runs inside a daemon thread worker.
   - Non-interactive approval callback `_subagent_auto_deny` protects against dangerous terminal operations.
   - A background heartbeat thread touches `parent_agent._touch_activity("h9.research subagent working")` every 15 seconds to prevent gateway connection drops.
   - Timeout protection: Configured at 180 seconds (`timeout_seconds = 180.0`). If the child stalls, `_dump_subagent_timeout_diagnostic` writes thread stacks and state to `~/.hermes/logs/` and terminates the child.
4. **Completion & Linearization**:
   - The child's final response text is extracted.
   - The output schema validator verifies conformance against `ResearchDossier.model_json_schema()`.
   - On success, `ResearchDossier.model_validate(json.loads(candidate))` instantiates the validated Pydantic object.
   - The child session terminates cleanly and releases its `SessionDB` connection (`child._owns_session_db = True`).

### 3.3 Scoped Toolset Configuration

| Tool Name | Status | Rationale |
|---|---|---|
| `web_search` | **Allowed** | Core discovery of external news, academic papers, and technical specifications. |
| `web_extract` | **Allowed** | Paged full-text reading of discovered primary source articles. |
| `read_file` | **Allowed** | Inspecting local reference documents, presets, or offline source files. |
| `delegate_task` | **BLOCKED** | Prevents uncontrolled recursive delegation trees. |
| `clarify` | **BLOCKED** | Subagents run headlessly; cannot prompt the user for input. |
| `memory` | **BLOCKED** | Subagents must not write to shared `MEMORY.md`. |
| `send_message` | **BLOCKED** | Subagents must not trigger cross-platform gateway message emissions. |
| `cronjob` | **BLOCKED** | Subagents must not schedule background jobs. |
| `h9.render` | **BLOCKED** | Video rendering is forbidden during research phase. |
| `h9.generate_script` | **BLOCKED** | Scriptwriting is forbidden during research phase. |
| `h9.discover_assets` | **BLOCKED** | Asset downloading is deferred to asset discovery phase. |

### 3.4 Prompt Caching Preservation Strategy

Prompt caching efficiency in Hermes depends on strict prefix immutability. The subagent delegation architecture preserves this through three architectural guarantees:

1. **Context Boundary Isolation**:
   - The parent conversation context holds only two messages related to research:
     - Message $N$: `assistant` with `tool_calls: [{"id": "call_1", "type": "function", "function": {"name": "h9.research", "arguments": "{\"topic\": \"...\", \"depth\": \"deep\"}"}}]`
     - Message $N+1$: `tool` with `tool_call_id: "call_1"`, `name": "h9.research"`, `content: "<serialized ResearchDossier JSON>"`
   - None of the subagent's intermediate turns, tool calls (`web_search`), raw HTML scrapes, or reasoning tokens enter the parent's message history.
2. **Ephemeral Prompt Tiering**:
   - The subagent's system prompt uses `ephemeral_system_prompt` (`tools/delegate_tool.py:2016`), which is injected at API call time and excluded from the stored base prompt (`agent/system_prompt.py:879`).
3. **Headroom Truncation & Disk Spill**:
   - If the synthesized research dossier is large (exceeding context headroom), `_apply_summary_budget` trims the in-context JSON payload to a head+tail window and saves the complete dossier to `cache/delegation/subagent-summary-*.txt` and `output/sessions/{session_id}/research_dossier.json`.

### 3.5 Schema Enforcement & Error Recovery Workflow

```
       Subagent Produces Final Output Text
                       │
                       ▼
          tools/delegation_output_schema.py
             extract_json_candidate(text)
                       │
                       ▼
             validate_output(candidate,
          ResearchDossier.model_json_schema())
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
      [Valid]                    [Invalid]
         │                           │
         │                Retry count == 0?
         │                  ┌────────┴────────┐
         │               [Yes]               [No]
         │                  │                  │
         │                  ▼                  ▼
         │           Send 1 Bounded      Fallback to
         │           Retry Turn with     Procedural /
         │         build_retry_message   Preset Synthesis
         │           (exact errors)            │
         │                  │                  │
         │                  ▼                  │
         │           Subagent Fixes            │
         │             JSON Output             │
         │                  │                  │
         │                  ▼                  │
         │           validate_output           │
         │                  │                  │
         └─────────┬────────┘                  │
                   ▼                           ▼
          ResearchDossier.             ResearchDossier
          model_validate(...)          Procedural Object
                   │                           │
                   └───────────┬───────────────┘
                               ▼
                   Return Verified Dossier
```

---

## 4. Caveats

1. **Direct `delegate_task` Dependency on `parent_agent`**:
   - In `tools/delegate_tool.py:3704`, `delegate_task` checks `if parent_agent is None: return tool_error(...)`.
   - When running inside Hermes CLI or Gateway, `parent_agent` is injected by the conversation loop (`agent/conversation_loop.py`).
   - In standalone H9 unit tests or headless batch execution where no Hermes `AIAgent` instance is running, `AgentRuntime` must provide an adapter shim (such as `DefaultAgentRuntime`) that either constructs a standalone `AIAgent` or falls back to `ResearchEngine.synthesize_research(...)`.
2. **Web Search API Rate Limits & Quotas**:
   - External search providers (Tavily, Exa, Brave Search) have strict rate limits and network latency.
   - The subagent must handle search HTTP 429 / timeouts by falling back through the provider chain, and ultimately falling back to procedural synthesis if external search is unavailable.
3. **Dual Model Representation (`contracts.py` vs `dossier.py`)**:
   - `src/models/contracts.py` defines Pydantic v2 schemas (`H9BaseModel`), whereas `src/models/dossier.py` defines `@dataclass` schemas used by `src/research/engine.py`.
   - `HermesCapabilityBridge` and `DefaultContentRuntime` must ensure seamless conversion between dataclass dictionaries and Pydantic models so that neither runtime breaks during serialization or deserialization.

---

## 5. Conclusion

Milestone 4 Part 3 (R4.3) Isolated Subagent Research Delegation can be cleanly achieved without architectural redesign or token bloat:
1. **Infrastructure Exists**: Hermes Agent already has an industrial-grade subagent delegation engine in `tools/delegate_tool.py` and `tools/delegation_output_schema.py` featuring thread isolation, non-interactive approval safety, JSON Schema contract enforcement, bounded retries, and prompt caching protection.
2. **Schema Alignment**: `ResearchDossier` in `src/models/contracts.py` is a Pydantic v2 contract that directly supplies `ResearchDossier.model_json_schema()`.
3. **Clean Runtime Seam**: `h9.research` routes through `HermesCapabilityBridge.plan_research`, which delegates deep research to `AgentRuntime.delegate_subagent` / `delegate_task` mapped to `CapabilityRole.REASONING_RESEARCH`.
4. **Complete Fallback Safety**: If external APIs fail or timeouts occur, the pipeline falls back gracefully to deterministic procedural synthesis, ensuring 100% liveness and zero pipeline halts.

---

## 6. Verification Method

### 6.1 Automated Test Execution Commands

Run the test suites covering runtime abstractions, content tools, skills, and delegation output schemas:

```bash
# 1. Verify H9 runtime boundary protocols and subagent delegation mock
pytest tests/test_h9_runtime.py -v -k "test_04_agent_runtime_subagent_delegation"

# 2. Verify H9 content tools (h9.research execution and bridge subagent delegation)
pytest tests/test_h9_content_tools.py -v -k "test_10_research_standard_happy_path or test_12_research_deep_depth or test_32_bridge_subagent_delegation"

# 3. Verify Hermes delegate output schema validation and retry mechanics
pytest tests/tools/test_delegate_output_schema.py -v

# 4. Run full H9 runtime and tools regression suite
pytest tests/test_h9_runtime.py tests/test_h9_content_tools.py tests/test_h9_skills_and_ir.py -v
```

### 6.2 Key Verification Assertions
- **Subagent Tool Scoping**: In `test_04_agent_runtime_subagent_delegation`, verify that `allowed_tools` contains `web_search` and `read_file`, and strictly excludes `delegate_task` and `h9.render`.
- **Dossier Schema Validation**: Verify that `handle_h9_research` outputs a dictionary validating against `ResearchDossier` with non-empty `topic`, `claims` (with `primary_source`), and `key_takeaways`.
- **Output Schema Retry**: Verify that `validate_output` catches schema violations and that `build_retry_message` formats the exact field path error for the model.
- **Prompt Cache Stability**: Verify that the parent conversation turn count increments by exactly 1 and that no subagent intermediate tool calls appear in parent message history.

### 6.3 Invalidation Conditions
- Any change that allows subagent tool calls (e.g. `web_search` or terminal operations) to leak directly into the parent conversation history invalidates the prompt cache design.
- Any change that removes the 1-turn bound on schema retries could lead to recursive failure loops and token depletion.
- Any change that prevents graceful fallback to procedural synthesis when network search is unavailable invalidates pipeline resilience.
