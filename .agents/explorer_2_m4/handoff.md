# Milestone 4 Technical Exploration Report — Part 2: Memory & SessionDB Integration (R4.2)

**Agent**: `explorer_2_m4`  
**Role**: Read-only Technical Explorer & Persistence Architect  
**Scope**: Milestone 4 Technical Exploration — Part 2: Memory & SessionDB Integration (R4.2)  
**Authoritative User Request**: `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md`  
**Project Scope Document**: `g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_4\PROJECT.md`  
**Date**: 2026-09-05  

---

## Executive Summary

This exploration establishes the concrete architectural design and engineering specification for **Milestone 4 Part 2: Memory & SessionDB Integration (R4.2)**. It investigates Hermes Agent memory and session storage mechanisms (`hermes_state.py`, `hermes_state_common.py`, `agent/memory_manager.py`, `agent/memory_provider.py`, `tools/memory_tool.py`), inspects Harness 9 creator and project memory contracts and cognitive models (`src/models/contracts.py`, `src/creator/dna.py`, `src/creator/memory.py`, `src/orchestrator/state_machine.py`), evaluates the runtime boundary interface (`src/h9_runtime/memory.py`, `src/h9_runtime/bridge.py`), and designs a **unified persistence architecture** that eliminates competing storage, avoids database locks, and guarantees zero dual-write drift.

Key architectural determinations:
1. **Hermes SessionDB & WAL Concurrency**: Hermes utilizes a robust SQLite-backed store (`state.db`) in WAL mode with application-level randomized jitter retries (`_WRITE_PATIENCE_S = 20.0s`, `_TRANSCRIPT_WRITE_PATIENCE_S = 60.0s`), short 1-second SQLite busy timeouts, `BEGIN IMMEDIATE` transaction acquisition, and bounded FTS5 maintenance (`messages_fts` and `messages_fts_trigram`).
2. **Hermes MemoryManager & Prompt Caching Protection**: `MemoryManager` (`agent/memory_manager.py`) orchestrates memory providers under a strict invariant: **at most ONE external memory provider is allowed alongside the built-in provider**. Built-in memory (`tools/memory_tool.py`) uses a **frozen snapshot pattern** in the system prompt at session start to protect the byte-stable prefix cache. Turn-level recall is injected dynamically via `<memory-context>` tags sanitized by `StreamingContextScrubber`.
3. **H9 Memory Models & Fragmentation**: H9 defines a 6-component Creator DNA cognitive model (`BrandConstitution`, `CreatorPreferences`, `CreatorSkills`, `CreatorExamples`, `PerformanceMemory`, `NegativeMemory`) in `src/creator/dna.py` and `src/creator/memory.py`, coupled with Pydantic contracts (`CreatorProfile`, `ContentBrief`, `LearningCandidate`). However, persistence is currently fragmented into ad-hoc JSON/YAML files (`DefaultMemoryRuntime` writing to `output/memory/{creator_id}.json` and `CreatorDNAStore` writing to `storage_dir`), with no database backing.
4. **Unified Storage Architecture (`HermesMemoryRuntime` & `state.db` Schema Extension)**: Rather than introducing a competing SQLite database (e.g. `h9.db`), all H9 persistence (`h9_creators`, `h9_projects`, `h9_production_history`, `h9_learning_candidates`, `h9_retention_curves`) converges directly into Hermes `state.db`. All writes execute through `SessionDB._execute_write` or secondary guest connections with `apply_durability_barriers(conn)` and `apply_wal_with_fallback(conn)`, serialized through `MemoryManager`'s lazy single-worker background threadpool, guaranteeing zero database locks and eliminating dual-write divergence.

---

## 1. Observation

### 1.1 Hermes Memory & Session Infrastructure

Direct inspection of Hermes persistence and memory subsystems revealed the following facts, schemas, and mechanisms:

#### 1.1.1 SessionDB Architecture (hermes_state.py & hermes_state_common.py)
- **File**: `hermes_state.py:4385`
  ```python
  class SessionDB(SessionSearchMixin, SessionSchemaMixin, SessionPortabilityMixin):
      """SQLite-backed session storage with FTS5 search."""
  ```
- **Database Location** (`hermes_state.py:362, 409`):
  `DEFAULT_DB_PATH = get_hermes_home() / "state.db"` (profile-aware via `get_hermes_home()`).
- **Core Tables** (`hermes_state_common.py:359-569`):
  1. `sessions`: Stores session lifecycle, token usage, cost, profile name, and system prompt hash. Primary key `id TEXT`. Has `FOREIGN KEY (parent_session_id) REFERENCES sessions(id)`.
  2. `messages`: Stores OpenAI-format messages (`id INTEGER PRIMARY KEY AUTOINCREMENT`, `session_id TEXT REFERENCES sessions(id)`, `role`, `content`, `tool_call_id`, `tool_calls`, `tool_name`, `timestamp`, `token_count`, `active`, `compacted`).
  3. `session_model_usage`: Granular per-model, per-billing-mode token and cost accounting.
  4. `state_meta`: Key-value metadata table (`key TEXT PRIMARY KEY`, `value TEXT`). Used for migrations, schema cookies, and deferred FTS index high-water marks (`fts_rebuild_high_water`, `fts_rebuild_progress`).
  5. `compression_locks` & `session_turn_leases`: Cross-process distributed concurrency leases.
  6. `async_delegations`: Asynchronous subagent task dispatch and result delivery ledger (`delegation_id TEXT PRIMARY KEY`, `origin_session`, `parent_session_id`, `state`, `event_json`, `result_json`).
  7. `gateway_heartbeats`: Process liveness heartbeats avoiding premature orphan cleanup across multi-process clusters.

#### 1.1.2 FTS5 Search & Synchronization Triggers (hermes_state_common.py:611-700)
- Standard full-text virtual table:
  ```sql
  CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
      content, tool_name, tool_calls, content='messages', content_rowid='id'
  );
  ```
- Trigram virtual table for CJK and substring phrase matching:
  ```sql
  CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts_trigram USING fts5(
      content, tool_name, tool_calls, content='messages_fts_trigram_src', content_rowid='id', tokenize='trigram'
  );
  ```
- Synchronization triggers (`messages_fts_insert`, `messages_fts_delete`, `messages_fts_update`) automatically maintain full-text indices upon writes to `messages`, gated by `state_meta` keys to prevent index corruption during background re-indexing.

#### 1.1.3 Write Contention & Lock Management (hermes_state.py:4393-4450, 5260-5330)
- **Problem**: In multi-process environments (Gateway daemon + CLI + Worktree subagents), competing WAL writers cause lock contention. SQLite's built-in busy handler uses deterministic sleep schedules that induce severe convoy effects and UI freezes.
- **Hermes Mitigation**:
  * SQLite timeout kept short (1.0s).
  * Application-level retry loop with randomized jitter:
    - Initial jitter: `_WRITE_RETRY_MIN_S = 0.020s` (20ms) to `_WRITE_RETRY_MAX_S = 0.150s` (150ms).
    - Slow backoff: `_WRITE_RETRY_SLOW_AFTER_S = 2.0s`, backing off to `0.250s`-`1.0s`.
  * Time-based patience budgets:
    - `_WRITE_PATIENCE_S = 20.0s` for routine writes.
    - `_TRANSCRIPT_WRITE_PATIENCE_S = 60.0s` for turn-critical writes (appending messages, session rows).
    - `_ACTIVITY_WRITE_PATIENCE_S = 0.5s` for heartbeat observations.
  * Transaction Protocol (`_execute_write`, `hermes_state.py:5301`):
    `self._conn.execute("BEGIN IMMEDIATE")` acquires the WAL write lock immediately at transaction start rather than deferring to commit time, immediately exposing lock collisions and triggering jittered retries without torn transactions.
  * Bounded Maintenance (`hermes_state.py:5313-5316`):
    - Passive WAL checkpoint every 50 writes (`_CHECKPOINT_EVERY_N_WRITES = 50`).
    - Bounded incremental FTS merge every 1000 writes (`_FTS_MERGE_EVERY_N_WRITES = 1000`) instead of unbounded `optimize` that would lock `state.db` for 9-18s.
  * Secondary / Guest Access (`hermes_state.py:2880-2903`):
    `apply_durability_barriers(conn)` and `apply_wal_with_fallback(conn)` allow secondary modules to connect to `state.db` while inheriting the owner's journal mode and durability settings.

#### 1.1.4 Hermes Memory Manager (agent/memory_manager.py)
- **Role**: Orchestrates memory providers. Single integration point instantiated in `agent/agent_init.py:1910`.
- **One External Provider Invariant** (`agent/memory_manager.py:443-466`):
  ```python
  def add_provider(self, provider: MemoryProvider) -> None:
      is_builtin = provider.name == "builtin"
      if not is_builtin:
          if self._has_external:
              # Rejected with warning — only ONE external memory provider is allowed at a time
              return
          self._has_external = True
      self._providers.append(provider)
  ```
- **Tool Shadowing Protection** (`lines 476-493`): Memory provider tools cannot shadow reserved core tools (`_HERMES_CORE_TOOLS`). Core tools always win.
- **Background Execution & Turn Serialization** (`lines 423-439, 1150-1210`):
  `MemoryManager` owns `_sync_executor: Optional[ThreadPoolExecutor]` with `max_workers=1`. This single worker serializes all provider background turn sync writes (`sync_all` and `queue_prefetch_all`), guaranteeing that turn N persists before turn N+1 without blocking the agent's interactive loop.
- **Context Fencing & Scrubbing** (`lines 198-245`):
  Recalled memory is bounded inside `<memory-context>` tags with `[System note: ...]` headers. `StreamingContextScrubber` prevents partial memory tags from leaking to the user during streaming API responses.

#### 1.1.5 Built-in File-Backed Memory (tools/memory_tool.py)
- **Files**: `$HERMES_HOME/memories/MEMORY.md` (personal notes/facts) and `USER.md` (user profile/preferences).
- **Delimiter**: `\n§\n` (multiline section marker).
- **Sacred Prompt Caching Pattern** (`lines 11-14`):
  Both files are injected into the system prompt as a **frozen snapshot at session start**. Mid-session writes update files on disk immediately (durable) but do **NOT** mutate the active session's system prompt. This preserves byte-stable prefix caching for the entire session.
- **Safety Scanning** (`lines 97-100`): Injected memory text is strictly scanned for prompt injection/exfiltration via `_scan_memory_content` and `tools/threat_patterns.py`.

---

### 1.2 H9 Creator & Project Memory Audit

#### 1.2.1 Creator DNA Cognitive Model (src/creator/dna.py & src/creator/memory.py)
H9 defines a 6-component cognitive system across `src/creator/dna.py` and `src/creator/memory.py`:
1. **Brand Constitution** (`src/creator/dna.py:36-78`):
   - `mission`: Core editorial philosophy.
   - `tone_of_voice`: Ordered tone attributes (e.g. `authoritative`, `curious`, `accessible`).
   - `prohibited_words`: Buzzwords strictly prohibited (`"game-changer"`, `"revolutionize"`, `"mind-blowing"`, etc.).
   - `prohibited_themes`: Unverified hype, clickbait sensationalism.
   - `non_negotiable_guardrails`: Mandatory editorial axioms (e.g. "Every core claim must cite a primary source").
2. **Creator Preferences** (`src/creator/dna.py:83-98`):
   - Pacing: `preferred_wpm` (default 145 WPM), `target_scene_duration_sec` (4.5s).
   - Visual density: `visual_density_per_min` (12 elements/min).
   - Design tokens: `primary_color`, `background_color`, `text_color`, `accent_color`, `font_heading`, `font_body`, `font_mono`, `aspect_ratio` (`"16:9"`), `easing_function`.
3. **Creator Skills** (`src/creator/dna.py:102-132`):
   - `domain_specializations`: Subject competencies (e.g. Microelectronics, Distributed Computing).
   - `technical_lexicon`: Terminology definitions mapping acronyms to rigorous explanations.
   - `visual_representation_archetypes`: Block diagram, timeline reveal, stat counter, comparison split.
4. **Creator Examples (Few-Shot Exemplars)** (`src/creator/dna.py:137-185`):
   - `CreatorExample`: `example_id`, `category` (`hook`, `transition`, `explanation`), `text`, `notes`, `performance_rating`.
   - `get_few_shot_prompt(category)`: Formats few-shot prompts for LLM in-context conditioning.
5. **Performance Memory** (`src/creator/memory.py:133-165`):
   - `RetentionCurve`: Series of `RetentionCurvePoint` timestamps and retention percentages. Computes `average_view_duration_sec`, `completion_rate_pct`, and `find_drop_off_points()`.
   - `LearnedPattern`: Discovered creative correlations with `confidence_score` and `sample_count`.
6. **Negative Memory** (`src/creator/memory.py:196-321`):
   - `NegativeMistakeRecord`: Log of past failures (`pattern_or_phrase`, `failure_reason`, `severity`).
   - `NegativeConstraint`: Active blocking rules generated automatically from mistakes.
   - `forbidden_words` & `forbidden_themes`.
   - `generate_negative_prompt_directives()`: Generates dynamic negative conditioning rules.
   - `check_violations(text)`: Scans draft scripts for forbidden buzzwords and negative constraints.
   - `extract_learning_candidates(creator_id)`: Distills high/critical failures into `LearningCandidate` contracts.

#### 1.2.2 Production Contracts (src/models/contracts.py)
- `CreatorProfile` (`contracts.py:124-151`): Flat production contract with `creator_id`, `display_name`, `tone_of_voice`, `target_audiences`, `brand_colors`, `default_format`, `negative_rules`, `voice_preference`, and `metadata`.
  * `CreatorDNA.to_creator_profile()` (`src/creator/dna.py:205-234`) cleanly serializes the full cognitive model into this contract.
  * `CreatorDNA.from_creator_profile(profile)` (`src/creator/dna.py:237-267`) reconstitutes the cognitive model from the contract.
- `ContentBrief` (`contracts.py:156-169`): Input specification containing `project_id`, `topic`, `target_duration_seconds`, `aspect_ratio`, `goal`, `audience`, `offline_mode`, `creator_id`.
- `LearningCandidate` (`contracts.py:520-531`): Evolution candidate (`lesson_id`, `creator_id`, `rule_type`, `observation`, `recommended_action`, `confidence`).
- `RenderArtifact` (`contracts.py:473-488`): Video render output metadata.
- `PublishPackage` (`contracts.py:489-504`): Distribution bundle with video path, thumbnail, captions, metadata.

#### 1.2.3 Production History & State Machine (src/orchestrator/state_machine.py)
- `ProductionState`: 17 canonical sequential states (`CREATED` -> `RESEARCH_PLANNED` -> ... -> `COMPLETED`).
- `TransitionRecord`: Immutable transition audit log (`from_state`, `to_state`, `timestamp`, `payload_summary`, `duration_ms`, `metadata`).
- `ProductionStateMachine`: Maintains `self._history: List[TransitionRecord]` tracking every state hop throughout the job lifecycle.

#### 1.2.4 Existing Persistence & Competing Database Audit
- **Grep Search Result**: Zero `sqlite3` imports exist in `src/`.
- **Ad-hoc File Storage Sites**:
  1. `DefaultMemoryRuntime` (`src/h9_runtime/memory.py:58-90`): Reads/writes `{creator_id}.json` directly to `storage_dir` (default `output/memory/`).
  2. `CreatorDNAStore` (`src/creator/dna.py:355-404`): Reads/writes `{creator_id}.json` and `{creator_id}.yaml` directly to `storage_dir`.
  3. `Pipeline` (`src/orchestrator/pipeline.py:65-75`): Writes artifacts to `output/sessions/{session_id}/` on disk.
- **Competing Database Risk**: While H9 does not yet have a competing SQL engine, letting `DefaultMemoryRuntime` and `CreatorDNAStore` write uncoordinated JSON/YAML files while Hermes manages `state.db` creates:
  * File-locking contention on concurrent worker execution.
  * Dual-write drift between Hermes session message history and H9 creator profile state.
  * Complete inability to perform cross-entity transactions or unified full-text search across creator learnings and session conversation turns.

---

### 1.3 Runtime Boundary Interface Inspection

#### 1.3.1 src/h9_runtime/memory.py
- Protocol `MemoryRuntime` (`lines 20-53`) defines 5 abstract methods:
  1. `get_creator_profile(creator_id: str) -> Optional[CreatorProfile]`
  2. `save_creator_profile(profile: CreatorProfile) -> None`
  3. `recall_context(query: str, creator_id: Optional[str] = None, limit: int = 5) -> List[MemoryRecallItem]`
  4. `record_production_telemetry(project_id: str, metrics: Dict[str, Any], learning_candidates: Optional[List[LearningCandidate]] = None) -> None`
  5. `render_system_prompt_block(creator_id: Optional[str] = None) -> str`
- Implementation `DefaultMemoryRuntime` (`lines 55-216`):
  * Stores profiles in an in-memory dictionary `self._profiles` backed by JSON files in `self.storage_dir / f"{creator_id}.json"`.
  * Context recall performs simple in-memory substring matching on query terms against `negative_rules`, `tone_of_voice`, and `self._learning_candidates`.
  * `render_system_prompt_block` produces a deterministic, byte-stable markdown string preserving prompt cacheability.

#### 1.3.2 src/h9_runtime/bridge.py
- `HermesCapabilityBridge` implements `MemoryRuntime` (`lines 325-355`) by forwarding calls directly to `self._memory: MemoryRuntime`.
- In `__init__` (`lines 121-123`), `self._memory` is instantiated as `DefaultMemoryRuntime(storage_dir=self.workspace_root / "memory")`.

---

## 2. Logic Chain

From the observations above, we establish the step-by-step reasoning leading to the unified persistence architecture:

### Step 1: Prompt Caching Requires Strict System Prompt Immutability
- **Observation**: Hermes rule (per `AGENTS.md` and `tools/memory_tool.py:11-14`) mandates that per-conversation prompt caching is sacred. Mid-session changes to the system prompt invalidate prefix caching and multiply inference costs.
- **Deduction**: The creator\'s Brand Constitution, tone guidelines, and active negative constraints must be assembled into a **byte-stable, deterministic markdown block at session start**. Mid-session updates to Creator DNA (e.g. learning a new negative rule during scriptwriting) must persist immediately to durable storage but must NOT mutate the active agent\'s system prompt for that session. New constraints are injected into active turns solely via dynamic prefetch context (`<memory-context>`) and take effect on the next session start.

### Step 2: Hermes Prohibits Multiple External Memory Providers
- **Observation**: `agent/memory_manager.py:453-465` explicitly limits `MemoryManager` to **at most ONE external memory provider**. If a user configures `mem0` or `honcho` in `config.yaml`, registering an external H9 memory provider plugin via `MemoryManager.add_provider()` will be rejected with a warning.
- **Deduction**: H9 creator memory cannot be implemented solely as an external memory plugin that competes with user-selected memory backends. Instead:
  1. H9 creator persistence must integrate directly into the **Hermes host state store (`SessionDB` / `state.db`)**, making creator profiles and project lifecycles core entities of the agent workspace.
  2. For model-facing memory recall within H9 skills, H9 provides `H9CreatorMemoryProvider` that can either function as the active memory provider OR be queried directly by `HermesMemoryRuntime` during turn preparation and skill dispatch without violating the external provider ceiling.

### Step 3: Competing SQLite Files Induce Lock Convoy and Operational Failure
- **Observation**: Operating a secondary SQLite database (e.g. `output/memory/h9_creator.db`) alongside `~/.hermes/state.db` introduces split WAL files, separate file descriptors, uncoordinated SQLite busy handlers, and lock amplification under concurrent worker execution. Furthermore, `hermes_state.py:1106-1160` documents known SQLite WAL bugs on NFS/SMB mounts and highlights that `state.db` requires careful application-level jitter retry (`_execute_write`).
- **Deduction**: We must **NOT** create a separate `h9.db` or let H9 spawn unmanaged `sqlite3.connect()` instances. H9 tables must live directly inside `state.db` (or share the managed `SessionDB` connection). All H9 transactions must pass through `SessionDB._execute_write` to inherit its 1-second timeout, `BEGIN IMMEDIATE` lock acquisition, and 20-second randomized jitter retry budget.

### Step 4: Long-Running Production Stages Must Never Hold Database Locks
- **Observation**: H9 production stages include long-running operations: research web searches (10-30s), voiceover generation (5-15s), and HyperFrames Chromium video rendering (10-60s). `SessionDB._execute_write` has a routine patience budget of 20 seconds.
- **Deduction**: If a database transaction remains open while an H9 pipeline step executes, concurrent Hermes processes (TUI activity heartbeats, CLI queries, gateway messages) will exhaust their 20s budget and fail with `session_persistence_failed`. Therefore, all H9 database operations must be **strictly bounded micro-transactions**:
  - State machine transitions update `h9_projects` and `h9_production_history` in `< 5 ms` transactions.
  - Video rendering executes in an isolated sandbox; only when the `RenderArtifact` is produced does a `< 5 ms` commit record the artifact in `h9_projects`.

### Step 5: Eliminating Dual-Write Drift
- **Observation**: Currently, `DefaultMemoryRuntime` writes to `.json` files on disk, while `SessionDB` writes to SQLite. If a process crashes between the two writes, state diverges permanently.
- **Deduction**: SQLite `state.db` must be the **sole authoritative source of truth**. Disk exports (such as exporting a creator profile to `output/memory/{creator_id}.json` for human inspection) are strictly derivative cache projections generated on demand or flushed atomically after the SQLite transaction commits.

---

## 3. Unified Persistence Architecture Design

### 3.1 Data Model & SQLite Schema Extension

We define formal schema extensions to `state.db` under the table prefix `h9_`. These tables are registered via `SessionDB` migration or initial schema bootstrap:

```sql
-- 1. Creator DNA & Brand Profiles
CREATE TABLE IF NOT EXISTS h9_creators (
    creator_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    profile_json TEXT NOT NULL,       -- Serialized CreatorProfile contract
    dna_json TEXT NOT NULL,           -- Serialized CreatorDNA master cognitive model
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 2. Content Projects (Linked to Hermes Sessions)
CREATE TABLE IF NOT EXISTS h9_projects (
    project_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    creator_id TEXT NOT NULL REFERENCES h9_creators(creator_id),
    topic TEXT NOT NULL,
    target_duration_seconds INTEGER NOT NULL DEFAULT 30,
    aspect_ratio TEXT NOT NULL DEFAULT ''16:9'',
    current_state TEXT NOT NULL DEFAULT ''CREATED'',
    brief_json TEXT NOT NULL,         -- Serialized ContentBrief
    dossier_json TEXT,                -- Serialized ResearchDossier
    angle_json TEXT,                  -- Serialized EditorialAngle
    script_json TEXT,                 -- Serialized Script
    production_ir_json TEXT,          -- Serialized ProductionIRDocument
    render_artifact_json TEXT,        -- Serialized RenderArtifact
    publish_package_json TEXT,        -- Serialized PublishPackage
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 3. Production Lifecycle Transition History
CREATE TABLE IF NOT EXISTS h9_production_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES h9_projects(project_id) ON DELETE CASCADE,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    timestamp REAL NOT NULL,
    payload_summary_json TEXT,
    duration_ms REAL DEFAULT 0.0,
    metadata_json TEXT
);

-- 4. Negative Memory & Learning Candidates Ledger
CREATE TABLE IF NOT EXISTS h9_learning_candidates (
    lesson_id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL REFERENCES h9_creators(creator_id) ON DELETE CASCADE,
    project_id TEXT REFERENCES h9_projects(project_id) ON DELETE SET NULL,
    rule_type TEXT NOT NULL,          -- ''negative_constraint'', ''retention'', ''pacing''
    observation TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.8,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL
);

-- 5. Audience Retention Curves & Performance Telemetry
CREATE TABLE IF NOT EXISTS h9_retention_curves (
    curve_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES h9_projects(project_id) ON DELETE CASCADE,
    creator_id TEXT NOT NULL REFERENCES h9_creators(creator_id) ON DELETE CASCADE,
    duration_seconds REAL NOT NULL,
    average_view_duration_sec REAL NOT NULL DEFAULT 0.0,
    completion_rate_pct REAL NOT NULL DEFAULT 0.0,
    initial_5s_retention_pct REAL NOT NULL DEFAULT 0.0,
    points_json TEXT NOT NULL,         -- JSON array of [{timestamp_sec, retention_pct}]
    recorded_at REAL NOT NULL
);

-- 6. Full-Text Search Virtual Table for Creator Memory & Learnings
CREATE VIRTUAL TABLE IF NOT EXISTS h9_memory_fts USING fts5(
    lesson_id,
    creator_id,
    rule_type,
    observation,
    recommended_action,
    content=''h9_learning_candidates'',
    content_rowid=''rowid''
);

-- FTS Synchronization Triggers
CREATE TRIGGER IF NOT EXISTS h9_learning_candidates_ai AFTER INSERT ON h9_learning_candidates BEGIN
    INSERT INTO h9_memory_fts(rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES (new.rowid, new.lesson_id, new.creator_id, new.rule_type, new.observation, new.recommended_action);
END;

CREATE TRIGGER IF NOT EXISTS h9_learning_candidates_ad AFTER DELETE ON h9_learning_candidates BEGIN
    INSERT INTO h9_memory_fts(h9_memory_fts, rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES (''delete'', old.rowid, old.lesson_id, old.creator_id, old.rule_type, old.observation, old.recommended_action);
END;

CREATE TRIGGER IF NOT EXISTS h9_learning_candidates_au AFTER UPDATE ON h9_learning_candidates BEGIN
    INSERT INTO h9_memory_fts(h9_memory_fts, rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES (''delete'', old.rowid, old.lesson_id, old.creator_id, old.rule_type, old.observation, old.recommended_action);
    INSERT INTO h9_memory_fts(rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES (new.rowid, new.lesson_id, new.creator_id, new.rule_type, new.observation, new.recommended_action);
END;

-- Indexes for Fast Query Routing
CREATE INDEX IF NOT EXISTS idx_h9_projects_session ON h9_projects(session_id);
CREATE INDEX IF NOT EXISTS idx_h9_projects_creator ON h9_projects(creator_id);
CREATE INDEX IF NOT EXISTS idx_h9_projects_state ON h9_projects(current_state);
CREATE INDEX IF NOT EXISTS idx_h9_history_project ON h9_production_history(project_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_h9_learning_creator ON h9_learning_candidates(creator_id, rule_type);
```

### 3.2 Concrete Pydantic Contracts: ContentProject & ProductionHistory

To cleanly interface with `src/models/contracts.py`, we define `ContentProject` and `ProductionHistoryRecord`:

```python
# src/models/contracts.py additions

class ContentProject(H9BaseModel):
    """Complete lifecycle project record mapping H9 execution to a Hermes session."""
    project_id: str = Field(..., min_length=1, description="Unique project slug")
    session_id: str = Field(..., min_length=1, description="Associated Hermes session ID")
    creator_id: str = Field(default="harness9_creator", description="Associated creator persona")
    topic: str = Field(..., min_length=1)
    target_duration_seconds: int = Field(default=30, ge=5, le=600)
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")
    current_state: str = Field(default="CREATED")
    brief: ContentBrief
    dossier: Optional[ResearchDossier] = None
    selected_angle: Optional[EditorialAngle] = None
    script: Optional[Script] = None
    production_ir: Optional[Dict[str, Any]] = None
    render_artifact: Optional[RenderArtifact] = None
    publish_package: Optional[PublishPackage] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductionHistoryRecord(H9BaseModel):
    """Single state transition record in production audit history."""
    project_id: str
    from_state: str
    to_state: str
    timestamp: float = Field(default_factory=time.time)
    payload_summary: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 3.3 Concrete Runtime Interface: HermesMemoryRuntime

In `src/h9_runtime/memory.py`, we introduce `HermesMemoryRuntime` conforming to `MemoryRuntime`:

```python
# src/h9_runtime/memory.py

class HermesMemoryRuntime:
    """Production MemoryRuntime implementation backed by Hermes SessionDB / state.db.
    
    Guarantees:
    1. Zero competing SQLite databases — shares state.db.
    2. Zero database lock convoys — utilizes SessionDB._execute_write with jitter retries.
    3. Zero dual-write drift — state.db is single source of truth.
    4. Sacred prompt caching — byte-stable system prompt generation.
    """

    def __init__(self, session_db: Optional[Any] = None) -> None:
        if session_db is not None:
            self._db = session_db
        else:
            from hermes_state import SessionDB
            self._db = SessionDB()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create h9_* tables in state.db if they do not exist."""
        def _migrate(conn):
            conn.executescript(H9_SCHEMA_SQL)
        self._db._execute_write(_migrate)

    def get_creator_profile(self, creator_id: str) -> Optional[CreatorProfile]:
        def _query(conn):
            cursor = conn.cursor()
            cursor.execute(
                "SELECT profile_json FROM h9_creators WHERE creator_id = ?",
                (creator_id,)
            )
            row = cursor.fetchone()
            if row:
                return CreatorProfile.from_json(row[0])
            return None
        return self._db._execute_read(_query)

    def save_creator_profile(self, profile: CreatorProfile) -> None:
        dna = CreatorDNA.from_creator_profile(profile)
        now = time.time()
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO h9_creators (creator_id, display_name, profile_json, dna_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(creator_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    profile_json = excluded.profile_json,
                    dna_json = excluded.dna_json,
                    updated_at = excluded.updated_at
                """,
                (profile.creator_id, profile.display_name, profile.to_json(), dna.to_json(), now, now)
            )
        self._db._execute_write(_write)

    def recall_context(
        self,
        query: str,
        creator_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryRecallItem]:
        """FTS5-powered full-text search across active negative constraints & past learnings."""
        results: List[MemoryRecallItem] = []
        def _search(conn):
            cursor = conn.cursor()
            clean_query = query.replace('"', '""')
            fts_sql = """
                SELECT l.lesson_id, l.rule_type, l.observation, l.recommended_action, l.confidence, rank
                FROM h9_memory_fts f
                JOIN h9_learning_candidates l ON f.rowid = l.rowid
                WHERE h9_memory_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            try:
                cursor.execute(fts_sql, (clean_query, limit))
                for row in cursor.fetchall():
                    results.append(MemoryRecallItem(
                        source="h9_learning_candidates",
                        category=row[1],
                        content=f"Observation: {row[2]} -> Rule: {row[3]}",
                        score=float(row[4]),
                        metadata={"lesson_id": row[0]},
                    ))
            except Exception:
                like_sql = """
                    SELECT lesson_id, rule_type, observation, recommended_action, confidence
                    FROM h9_learning_candidates
                    WHERE observation LIKE ? OR recommended_action LIKE ?
                    LIMIT ?
                """
                like_param = f"%{query}%"
                cursor.execute(like_sql, (like_param, like_param, limit))
                for row in cursor.fetchall():
                    results.append(MemoryRecallItem(
                        source="h9_learning_candidates",
                        category=row[1],
                        content=f"Observation: {row[2]} -> Rule: {row[3]}",
                        score=float(row[4]),
                        metadata={"lesson_id": row[0]},
                    ))
        self._db._execute_read(_search)
        return results[:limit]

    def record_production_telemetry(
        self,
        project_id: str,
        metrics: Dict[str, Any],
        learning_candidates: Optional[List[LearningCandidate]] = None,
    ) -> None:
        now = time.time()
        def _write(conn):
            cursor = conn.cursor()
            if learning_candidates:
                for lc in learning_candidates:
                    cursor.execute(
                        """
                        INSERT INTO h9_learning_candidates
                        (lesson_id, creator_id, project_id, rule_type, observation, recommended_action, confidence, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(lesson_id) DO UPDATE SET
                            observation = excluded.observation,
                            recommended_action = excluded.recommended_action,
                            confidence = excluded.confidence
                        """,
                        (lc.lesson_id, lc.creator_id, project_id, lc.rule_type, lc.observation, lc.recommended_action, lc.confidence, now)
                    )
        self._db._execute_write(_write)

    def render_system_prompt_block(self, creator_id: Optional[str] = None) -> str:
        """Returns byte-stable, deterministic markdown block preserving prompt cache."""
        cid = creator_id or "harness9_creator"
        profile = self.get_creator_profile(cid)
        if not profile:
            return (
                "### Creator Identity & Brand Constitution\n"
                "- Tone: Authoritative, Educational, Engaging\n"
                "- Audience: Tech Enthusiasts & Professionals\n"
                "- Negative Constraints: No clickbait hyperbole, no unverified claims."
            )
        dna = CreatorDNA.from_creator_profile(profile)
        return dna.build_system_prompt_context(stage_name="general")
```

### 3.4 Concurrency & Deadlock Prevention Mechanics

| Risk Vector | Cause | Engineered Mitigation in H9 x Hermes Architecture |
|---|---|---|
| **Convoy Effect / Lock Collision** | Multiple worker threads/processes competing for SQLite write lock simultaneously. | `SessionDB._execute_write` initiates every write with `BEGIN IMMEDIATE` and uses randomized exponential jitter retries (20ms-150ms -> 250ms-1s) within a 20s patience budget. |
| **Long-Running Lock Starvation** | Rendering (30s) or Research synthesis (15s) holding a database cursor open. | **Zero In-Flight Locks**: H9 pipeline operations execute strictly in user-space/sandbox memory. SQLite transactions are opened *only* to write state milestones (< 5 ms execution time) and committed immediately. |
| **Dual-Write State Divergence** | Writing to SQLite AND disk JSON independently without transactions. | **Single Authoritative Store**: SQLite `state.db` is the sole source of truth. File exports (`output/memory/`) are generated on-demand as read-only projections. |
| **Turn Write Reordering** | Asynchronous turn sync executing out-of-order in multiple threads. | **Single-Worker Executor**: `MemoryManager._sync_executor` uses `max_workers=1` to serialize turn N and N+1 writes sequentially in the background. |
| **Prompt Cache Invalidation** | Mutating system prompt mid-session when creator learns a new rule. | **Frozen Snapshot Pattern**: System prompt is assembled once at session start and held byte-stable. Mid-session learnings are stored durably in SQLite and injected only via ephemeral `<memory-context>` prefetch blocks. |

---

## 4. Caveats

1. **Test Environment Fallback (DefaultMemoryRuntime)**: In stripped testing environments or isolated unit tests where Hermes `state.db` or full Hermes installation is absent, `DefaultMemoryRuntime` (file-based) remains essential as a backward-compatible fallback. `src/h9_runtime/memory.py` must dynamically detect `hermes_state` availability and fall back cleanly without breaking `test_h9_runtime.py`.
2. **Pre-existing Database Migrations**: Hermes `state.db` uses `hermes_state_schema.py` versioning (`SCHEMA_VERSION`). Extension tables (`h9_*`) should be created with `CREATE TABLE IF NOT EXISTS` via an idempotent helper rather than forcing a global `SCHEMA_VERSION` bump, preventing conflicts with upstream Hermes migrations.
3. **No Direct SQLite in Domain Code**: Domain modules (`src/creator/`, `src/editorial/`, `src/orchestrator/`) must **never** import `sqlite3` directly; they must interact exclusively through `MemoryRuntime` and `HermesCapabilityBridge` (`src/h9_runtime/`).

---

## 5. Conclusion

1. **Storage Unification**: Competing persistence in H9 is eliminated by extending Hermes `state.db` with 5 dedicated tables (`h9_creators`, `h9_projects`, `h9_production_history`, `h9_learning_candidates`, `h9_retention_curves`) and an FTS5 virtual table.
2. **Contract Preservation**: `CreatorProfile`, `ContentBrief`, and `LearningCandidate` Pydantic contracts remain fully preserved and map bidirectionally to `CreatorDNA` and `ContentProject`.
3. **Cache & Concurrency Safety**: The design strictly preserves sacred prompt caching via the frozen snapshot pattern, eliminates write-lock contention via `SessionDB._execute_write`\'s jittered `BEGIN IMMEDIATE` retries, and eliminates dual-write drift by making `state.db` the single source of truth.
4. **Boundary Readiness**: `src/h9_runtime/memory.py` can immediately introduce `HermesMemoryRuntime` alongside `DefaultMemoryRuntime`, seamlessly wireable into `HermesCapabilityBridge`.

---

## 6. Verification Method

### 6.1 Automated Test Verification Commands

1. **Verify Baseline Runtime Boundary Suite**:
   ```bash
   pytest tests/test_h9_runtime.py -v
   ```
   *Expected*: All 9 tests pass, confirming `MemoryRuntime` protocol conformance and behavior.

2. **Verify Hermes State DB Concurrency & Schema Retries**:
   ```bash
   pytest tests/test_hermes_state.py tests/test_hermes_state_compression_busy_retry.py -v
   ```
   *Expected*: All tests pass, validating that WAL mode, jitter retries, and lock handling operate as specified.

3. **Verify Creator DNA & Memory Engine**:
   ```bash
   pytest tests/test_creator_dna.py tests/test_creator_memory.py -v
   ```
   *Expected*: All tests pass, validating Brand Constitution, Negative Memory, violation checks, and LearningCandidate generation.

4. **Verify Milestone 4 Unified Memory Integration (New Suite)**:
   ```bash
   pytest tests/test_h9_provider_memory_subagent.py -k "memory or session_db" -v
   ```
   *Expected*: Verifies `HermesMemoryRuntime` table creation in `state.db`, transactional persistence of `CreatorProfile` and `ContentProject`, FTS5 context recall, and zero database lock failures under simulated concurrent writes.

### 6.2 Manual Inspection Verification
- Inspect `src/h9_runtime/memory.py` to confirm `HermesMemoryRuntime` implements all methods of `MemoryRuntime`.
- Inspect `src/h9_runtime/bridge.py` to confirm `HermesCapabilityBridge.memory` delegates to `HermesMemoryRuntime`.
- Verify with SQLite inspection:
  ```bash
  python -c "from hermes_state import SessionDB; db = SessionDB(); print(db._execute_read(lambda c: c.execute(\"SELECT name FROM sqlite_master WHERE type=''table'' AND name LIKE ''h9_%''\").fetchall()))"
  ```
