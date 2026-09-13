"""src/h9_runtime/memory.py

MemoryRuntime protocol, DefaultMemoryRuntime, and HermesMemoryRuntime implementations.
Governs Creator DNA persistence, project lifecycle state, performance memory,
learning candidates, and byte-stable system prompt generation backed by Hermes SessionDB.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Protocol, Union, runtime_checkable

from src.h9_runtime.types import MemoryRecallItem
from src.models.contracts import (
    ContentBrief,
    ContentProject,
    CreatorProfile,
    EditorialAngle,
    LearningCandidate,
    ProductionHistoryRecord,
    PublishPackage,
    RenderArtifact,
    ResearchDossier,
    Script,
)

logger = logging.getLogger(__name__)

try:
    from src.creator.dna import CreatorDNA
except ImportError:
    CreatorDNA = None


# ===========================================================================
# SQLite Schema for Hermes State DB Extension (h9_* tables)
# ===========================================================================
H9_SCHEMA_SQL = """
-- 1. Creator DNA & Brand Profiles
CREATE TABLE IF NOT EXISTS h9_creators (
    creator_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    dna_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 2. Content Projects (Linked to Hermes Sessions)
CREATE TABLE IF NOT EXISTS h9_projects (
    project_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    target_duration_seconds INTEGER NOT NULL DEFAULT 30,
    aspect_ratio TEXT NOT NULL DEFAULT '16:9',
    current_state TEXT NOT NULL DEFAULT 'CREATED',
    brief_json TEXT,
    dossier_json TEXT,
    angle_json TEXT,
    script_json TEXT,
    production_ir_json TEXT,
    render_artifact_json TEXT,
    publish_package_json TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 3. Production Lifecycle Transition History
CREATE TABLE IF NOT EXISTS h9_production_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
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
    creator_id TEXT NOT NULL,
    project_id TEXT,
    rule_type TEXT NOT NULL,
    observation TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.8,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL
);

-- 5. Audience Retention Curves & Performance Telemetry
CREATE TABLE IF NOT EXISTS h9_retention_curves (
    curve_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    average_view_duration_sec REAL NOT NULL DEFAULT 0.0,
    completion_rate_pct REAL NOT NULL DEFAULT 0.0,
    initial_5s_retention_pct REAL NOT NULL DEFAULT 0.0,
    points_json TEXT NOT NULL,
    recorded_at REAL NOT NULL
);

-- Indexes for Fast Query Routing
CREATE INDEX IF NOT EXISTS idx_h9_projects_session ON h9_projects(session_id);
CREATE INDEX IF NOT EXISTS idx_h9_projects_creator ON h9_projects(creator_id);
CREATE INDEX IF NOT EXISTS idx_h9_projects_state ON h9_projects(current_state);
CREATE INDEX IF NOT EXISTS idx_h9_history_project ON h9_production_history(project_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_h9_learning_creator ON h9_learning_candidates(creator_id, rule_type);
"""

H9_FTS_SCHEMA_SQL = """
-- 6. Full-Text Search Virtual Table for Creator Memory & Learnings
CREATE VIRTUAL TABLE IF NOT EXISTS h9_memory_fts USING fts5(
    lesson_id,
    creator_id,
    rule_type,
    observation,
    recommended_action,
    content='h9_learning_candidates',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS h9_learning_candidates_ai AFTER INSERT ON h9_learning_candidates BEGIN
    INSERT INTO h9_memory_fts(rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES (new.rowid, new.lesson_id, new.creator_id, new.rule_type, new.observation, new.recommended_action);
END;

CREATE TRIGGER IF NOT EXISTS h9_learning_candidates_ad AFTER DELETE ON h9_learning_candidates BEGIN
    INSERT INTO h9_memory_fts(h9_memory_fts, rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES ('delete', old.rowid, old.lesson_id, old.creator_id, old.rule_type, old.observation, old.recommended_action);
END;

CREATE TRIGGER IF NOT EXISTS h9_learning_candidates_au AFTER UPDATE ON h9_learning_candidates BEGIN
    INSERT INTO h9_memory_fts(h9_memory_fts, rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES ('delete', old.rowid, old.lesson_id, old.creator_id, old.rule_type, old.observation, old.recommended_action);
    INSERT INTO h9_memory_fts(rowid, lesson_id, creator_id, rule_type, observation, recommended_action)
    VALUES (new.rowid, new.lesson_id, new.creator_id, new.rule_type, new.observation, new.recommended_action);
END;
"""


class _DummyLock:
    """Null lock when no concurrency lock is present."""

    def __enter__(self) -> "_DummyLock":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


# ===========================================================================
# MemoryRuntime Protocol
# ===========================================================================
@runtime_checkable
class MemoryRuntime(Protocol):
    """Runtime interface for Creator DNA, project memory, and persistence."""

    def get_creator_profile(self, creator_id: str) -> Optional[CreatorProfile]:
        """Retrieve Creator DNA profile (Brand Constitution, Preferences)."""
        ...

    def save_creator_profile(self, profile: CreatorProfile) -> None:
        """Persist updated Creator DNA profile."""
        ...

    def recall_context(
        self,
        query: str,
        creator_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryRecallItem]:
        """Perform semantic or keyword retrieval across creator memory."""
        ...

    def record_production_telemetry(
        self,
        project_id: str,
        metrics: Dict[str, Any],
        learning_candidates: Optional[List[LearningCandidate]] = None,
    ) -> None:
        """Record completed production metrics, retention curves, and learning candidates."""
        ...

    def render_system_prompt_block(self, creator_id: Optional[str] = None) -> str:
        """Generate static creator instructions for system prompt injection."""
        ...


# ===========================================================================
# HermesMemoryRuntime (Backed by SessionDB / state.db)
# ===========================================================================
class HermesMemoryRuntime:
    """Production MemoryRuntime implementation backed by Hermes SessionDB / state.db.

    Guarantees:
    1. Zero competing SQLite databases — shares state.db.
    2. Zero database lock convoys — utilizes SessionDB._execute_write with BEGIN IMMEDIATE and jitter retries.
    3. Zero dual-write drift — state.db is the single source of truth.
    4. Sacred prompt caching — byte-stable, deterministic system prompt generation.
    """

    def __init__(
        self,
        session_db: Optional[Any] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        if session_db is not None:
            self._db = session_db
        else:
            try:
                from hermes_state import SessionDB
                self._db = SessionDB(db_path=db_path) if db_path else SessionDB()
            except Exception as exc:
                logger.warning(
                    "Could not initialize Hermes SessionDB (%s); falling back to direct sqlite3 connection",
                    exc,
                )
                import sqlite3
                path = str(db_path or ":memory:")
                self._db = sqlite3.connect(path, check_same_thread=False)
                self._db.row_factory = sqlite3.Row

        self._ensure_schema()

    def _execute_write(self, fn: Callable[[Any], Any]) -> Any:
        """Execute a write transaction with BEGIN IMMEDIATE semantics and jitter retry."""
        if hasattr(self._db, "_execute_write"):
            return self._db._execute_write(fn)

        lock = getattr(self._db, "_lock", _DummyLock())
        with lock:
            if hasattr(self._db, "execute"):
                cursor = self._db.cursor()
                try:
                    cursor.execute("BEGIN IMMEDIATE")
                except Exception:
                    pass
                try:
                    res = fn(self._db)
                    self._db.commit()
                    return res
                except Exception:
                    try:
                        self._db.rollback()
                    except Exception:
                        pass
                    raise
            raise RuntimeError("Database object does not support write execution")

    def _execute_read(self, fn: Callable[[Any], Any]) -> Any:
        """Execute a read query using connection under read lock if present."""
        lock = getattr(self._db, "_lock", None)
        conn = getattr(self._db, "_conn", self._db)
        if lock is not None:
            with lock:
                return fn(conn)
        return fn(conn)

    def _ensure_schema(self) -> None:
        """Establish table definitions and schema bootstrap for h9_* and FTS5."""
        def _apply(conn: Any) -> None:
            conn.executescript(H9_SCHEMA_SQL)
            try:
                conn.executescript(H9_FTS_SCHEMA_SQL)
            except Exception as fts_exc:
                logger.debug("FTS5 table creation notice: %s", fts_exc)

        self._execute_write(_apply)

    # -----------------------------------------------------------------------
    # Creator DNA Persistence
    # -----------------------------------------------------------------------
    def get_creator_profile(self, creator_id: str) -> Optional[CreatorProfile]:
        """Retrieve Creator DNA profile by creator_id."""
        def _query(conn: Any) -> Optional[CreatorProfile]:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT profile_json FROM h9_creators WHERE creator_id = ?",
                (creator_id,),
            )
            row = cursor.fetchone()
            if row:
                raw_json = row[0] if not isinstance(row, dict) else row["profile_json"]
                try:
                    return CreatorProfile.from_json(raw_json)
                except Exception:
                    return CreatorProfile.from_dict(json.loads(raw_json))
            return None

        return self._execute_read(_query)

    def save_creator_profile(self, profile: CreatorProfile) -> None:
        """Persist CreatorProfile and associated CreatorDNA model into h9_creators."""
        dna_str = "{}"
        if CreatorDNA is not None:
            try:
                dna = CreatorDNA.from_creator_profile(profile)
                dna_str = dna.to_json() if hasattr(dna, "to_json") else json.dumps(dna.__dict__)
            except Exception as exc:
                logger.debug("CreatorDNA conversion note: %s", exc)
                dna_str = profile.to_json()
        else:
            dna_str = profile.to_json()

        now = time.time()
        name = getattr(profile, "display_name", getattr(profile, "brand_name", profile.creator_id))

        def _write(conn: Any) -> None:
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
                (profile.creator_id, name, profile.to_json(), dna_str, now, now),
            )

        self._execute_write(_write)

    # -----------------------------------------------------------------------
    # Project & State Machine Transition Persistence
    # -----------------------------------------------------------------------
    def get_project(self, project_id: str) -> Optional[ContentProject]:
        """Retrieve complete ContentProject state record."""
        def _query(conn: Any) -> Optional[ContentProject]:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT project_id, session_id, creator_id, topic, target_duration_seconds,
                       aspect_ratio, current_state, brief_json, dossier_json, angle_json,
                       script_json, production_ir_json, render_artifact_json, publish_package_json,
                       created_at, updated_at
                FROM h9_projects WHERE project_id = ?
                """,
                (project_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            data: Dict[str, Any] = {
                "project_id": row[0],
                "session_id": row[1],
                "creator_id": row[2],
                "topic": row[3],
                "target_duration_seconds": row[4],
                "aspect_ratio": row[5],
                "current_state": row[6],
                "brief": (
                    ContentBrief.from_json(row[7])
                    if (row[7] and row[7].strip() not in ("{}", ""))
                    else None
                ),
                "dossier": (
                    ResearchDossier.from_json(row[8])
                    if (row[8] and row[8].strip() not in ("{}", ""))
                    else None
                ),
                "selected_angle": json.loads(row[9]) if row[9] else None,
                "script": json.loads(row[10]) if row[10] else None,
                "production_ir": json.loads(row[11]) if row[11] else None,
                "render_artifact": json.loads(row[12]) if row[12] else None,
                "publish_package": json.loads(row[13]) if row[13] else None,
                "created_at": row[14],
                "updated_at": row[15],
            }
            return ContentProject.from_dict(data)

        return self._execute_read(_query)

    def save_project(self, project: ContentProject) -> None:
        """Persist ContentProject state record to h9_projects via micro-transaction."""
        now = time.time()

        def _write(conn: Any) -> None:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO h9_projects (
                    project_id, session_id, creator_id, topic, target_duration_seconds,
                    aspect_ratio, current_state, brief_json, dossier_json, angle_json,
                    script_json, production_ir_json, render_artifact_json, publish_package_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    session_id = excluded.session_id,
                    creator_id = excluded.creator_id,
                    topic = excluded.topic,
                    target_duration_seconds = excluded.target_duration_seconds,
                    aspect_ratio = excluded.aspect_ratio,
                    current_state = excluded.current_state,
                    brief_json = excluded.brief_json,
                    dossier_json = excluded.dossier_json,
                    angle_json = excluded.angle_json,
                    script_json = excluded.script_json,
                    production_ir_json = excluded.production_ir_json,
                    render_artifact_json = excluded.render_artifact_json,
                    publish_package_json = excluded.publish_package_json,
                    updated_at = excluded.updated_at
                """,
                (
                    project.project_id,
                    project.session_id,
                    project.creator_id,
                    project.topic,
                    project.target_duration_seconds,
                    project.aspect_ratio,
                    project.current_state,
                    project.brief.to_json() if project.brief else None,
                    project.dossier.to_json() if project.dossier else None,
                    project.selected_angle.to_json() if project.selected_angle else None,
                    project.script.to_json() if project.script else None,
                    json.dumps(project.production_ir) if project.production_ir else None,
                    project.render_artifact.to_json() if project.render_artifact else None,
                    project.publish_package.to_json() if project.publish_package else None,
                    project.created_at,
                    now,
                ),
            )

        self._execute_write(_write)

    def record_transition(self, record: ProductionHistoryRecord) -> None:
        """Record state machine transition into h9_production_history (< 5ms lock)."""
        def _write(conn: Any) -> None:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO h9_production_history (
                    project_id, from_state, to_state, timestamp, payload_summary_json, duration_ms, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.project_id,
                    record.from_state,
                    record.to_state,
                    record.timestamp,
                    json.dumps(record.payload_summary),
                    record.duration_ms,
                    json.dumps(record.metadata),
                ),
            )

        self._execute_write(_write)

    def get_project_history(self, project_id: str) -> List[ProductionHistoryRecord]:
        """Retrieve full immutable state transition history for a project."""
        def _query(conn: Any) -> List[ProductionHistoryRecord]:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT project_id, from_state, to_state, timestamp, payload_summary_json, duration_ms, metadata_json
                FROM h9_production_history
                WHERE project_id = ?
                ORDER BY timestamp ASC, id ASC
                """,
                (project_id,),
            )
            records = []
            for row in cursor.fetchall():
                records.append(
                    ProductionHistoryRecord(
                        project_id=row[0],
                        from_state=row[1],
                        to_state=row[2],
                        timestamp=row[3],
                        payload_summary=json.loads(row[4]) if row[4] else {},
                        duration_ms=row[5] or 0.0,
                        metadata=json.loads(row[6]) if row[6] else {},
                    )
                )
            return records

        return self._execute_read(_query)

    # -----------------------------------------------------------------------
    # FTS5 Context Recall & Telemetry
    # -----------------------------------------------------------------------
    def recall_context(
        self,
        query: str,
        creator_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryRecallItem]:
        """Recall relevant rules, brand guidelines, and past learnings using FTS5 with fallback."""
        results: List[MemoryRecallItem] = []
        q_lower = query.lower()

        # 1. Search creator negative rules and brand tone
        if creator_id:
            profile = self.get_creator_profile(creator_id)
            if profile:
                rules = getattr(profile, "negative_rules", []) or getattr(profile, "negative_constraints", [])
                for neg in rules:
                    score = 1.0 if any(t in neg.lower() for t in q_lower.split()) else 0.5
                    results.append(
                        MemoryRecallItem(
                            source="creator_profile.negative_rules",
                            category="negative_rule",
                            content=neg,
                            score=score,
                            metadata={"creator_id": profile.creator_id},
                        )
                    )

                tones = getattr(profile, "tone_of_voice", [])
                tone_str = ", ".join(tones) if isinstance(tones, list) else str(getattr(profile, "tone", "authoritative"))
                audiences = getattr(profile, "target_audiences", [])
                aud_str = ", ".join(audiences) if isinstance(audiences, list) else str(getattr(profile, "target_audience", "General"))
                tone_score = 0.8 if any(t in q_lower for t in ("tone", "brand", "voice", "audience")) else 0.3
                results.append(
                    MemoryRecallItem(
                        source="creator_profile.brand",
                        category="tone",
                        content=f"Tone: {tone_str}. Target Audience: {aud_str}",
                        score=tone_score,
                        metadata={"creator_id": profile.creator_id},
                    )
                )

        # 2. Search learning candidates via FTS5 with LIKE fallback
        def _search_candidates(conn: Any) -> None:
            import re
            cursor = conn.cursor()
            tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9]+", query) if len(t) >= 2]
            fts_worked = False

            if tokens:
                clean_query = " OR ".join(f'"{t}"*' for t in tokens)
                try:
                    fts_sql = """
                        SELECT l.lesson_id, l.rule_type, l.observation, l.recommended_action, l.confidence, rank
                        FROM h9_memory_fts f
                        JOIN h9_learning_candidates l ON f.rowid = l.rowid
                        WHERE h9_memory_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """
                    cursor.execute(fts_sql, (clean_query, limit))
                    for row in cursor.fetchall():
                        results.append(
                            MemoryRecallItem(
                                source="h9_learning_candidates",
                                category=row[1],
                                content=f"Observation: {row[2]} -> Rule: {row[3]}",
                                score=float(row[4]),
                                metadata={"lesson_id": row[0]},
                            )
                        )
                    fts_worked = True
                except Exception as exc:
                    logger.debug("FTS5 query fell back to LIKE search: %s", exc)

            if not fts_worked or not any(r.source == "h9_learning_candidates" for r in results):
                search_terms = tokens if tokens else [query.strip()]
                for token in search_terms:
                    if not token:
                        continue
                    like_sql = """
                        SELECT lesson_id, rule_type, observation, recommended_action, confidence
                        FROM h9_learning_candidates
                        WHERE observation LIKE ? OR recommended_action LIKE ? OR rule_type LIKE ?
                        LIMIT ?
                    """
                    like_param = f"%{token}%"
                    cursor.execute(like_sql, (like_param, like_param, like_param, limit))
                    for row in cursor.fetchall():
                        item = MemoryRecallItem(
                            source="h9_learning_candidates",
                            category=row[1],
                            content=f"Observation: {row[2]} -> Rule: {row[3]}",
                            score=float(row[4]),
                            metadata={"lesson_id": row[0]},
                        )
                        if not any(r.content == item.content for r in results):
                            results.append(item)

        self._execute_read(_search_candidates)

        # Sort by relevance score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def record_production_telemetry(
        self,
        project_id: str,
        metrics: Dict[str, Any],
        learning_candidates: Optional[List[LearningCandidate]] = None,
    ) -> None:
        """Record completed production metrics, retention curves, and learning candidates."""
        now = time.time()

        def _write(conn: Any) -> None:
            cursor = conn.cursor()
            if learning_candidates:
                for lc in learning_candidates:
                    cursor.execute(
                        """
                        INSERT INTO h9_learning_candidates (
                            lesson_id, creator_id, project_id, rule_type, observation, recommended_action, confidence, is_active, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                        ON CONFLICT(lesson_id) DO UPDATE SET
                            observation = excluded.observation,
                            recommended_action = excluded.recommended_action,
                            confidence = excluded.confidence
                        """,
                        (
                            lc.lesson_id,
                            lc.creator_id,
                            project_id,
                            lc.rule_type,
                            lc.observation,
                            lc.recommended_action,
                            lc.confidence,
                            now,
                        ),
                    )

            # Store retention curve if points provided
            retention_points = metrics.get("retention_points") or metrics.get("points")
            if retention_points:
                curve_id = f"rc_{project_id}_{int(now)}"
                creator_id = metrics.get("creator_id", "harness9_creator")
                duration = float(metrics.get("duration", 30.0))
                cursor.execute(
                    """
                    INSERT INTO h9_retention_curves (
                        curve_id, project_id, creator_id, duration_seconds,
                        average_view_duration_sec, completion_rate_pct, initial_5s_retention_pct,
                        points_json, recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(curve_id) DO NOTHING
                    """,
                    (
                        curve_id,
                        project_id,
                        creator_id,
                        duration,
                        float(metrics.get("average_view_duration_sec", duration * 0.7)),
                        float(metrics.get("completion_rate_pct", 75.0)),
                        float(metrics.get("initial_5s_retention_pct", 90.0)),
                        json.dumps(retention_points),
                        now,
                    ),
                )

        self._execute_write(_write)

    def render_system_prompt_block(self, creator_id: Optional[str] = None) -> str:
        """Generate static creator instructions for system prompt injection.

        Preserves sacred prompt caching by generating a byte-stable, deterministic block.
        """
        profile = self.get_creator_profile(creator_id) if creator_id else None
        if not profile:
            return (
                "### Creator Identity & Brand Constitution\n"
                "- Tone: Authoritative, Educational, Engaging\n"
                "- Audience: Tech Enthusiasts & Professionals\n"
                "- Negative Constraints: No clickbait hyperbole, no unverified claims."
            )

        name = getattr(profile, "display_name", getattr(profile, "brand_name", profile.creator_id))
        tones = getattr(profile, "tone_of_voice", [])
        tone_str = ", ".join(tones) if isinstance(tones, list) else str(getattr(profile, "tone", "authoritative"))
        audiences = getattr(profile, "target_audiences", [])
        aud_str = ", ".join(audiences) if isinstance(audiences, list) else str(getattr(profile, "target_audience", "General"))
        rules = getattr(profile, "negative_rules", []) or getattr(profile, "negative_constraints", [])
        constraints_str = "\n".join(f"  * {c}" for c in rules) or "  * None"
        return (
            f"### Creator Identity: {name}\n"
            f"- Tone: {tone_str}\n"
            f"- Target Audience: {aud_str}\n"
            f"- Brand Constraints:\n{constraints_str}"
        )

    def close(self) -> None:
        """Close SQLite database connection to release Windows file locks."""
        if hasattr(self, "_db") and self._db is not None:
            if hasattr(self._db, "close"):
                try:
                    self._db.close()
                except Exception:
                    pass
            elif hasattr(self._db, "_conn") and hasattr(self._db._conn, "close"):
                try:
                    self._db._conn.close()
                except Exception:
                    pass
            self._db = None
        import gc
        gc.collect()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass




# ===========================================================================
# DefaultMemoryRuntime (File & In-Memory Fallback)
# ===========================================================================
class DefaultMemoryRuntime:
    """Concrete implementation of MemoryRuntime with unified profile and telemetry store."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = storage_dir or Path("output/memory")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._profiles: Dict[str, CreatorProfile] = {}
        self._projects: Dict[str, ContentProject] = {}
        self._history: Dict[str, List[ProductionHistoryRecord]] = {}
        self._telemetry: Dict[str, Dict[str, Any]] = {}
        self._learning_candidates: List[LearningCandidate] = []

    def get_creator_profile(self, creator_id: str) -> Optional[CreatorProfile]:
        """Retrieve Creator DNA profile by ID."""
        if creator_id in self._profiles:
            return self._profiles[creator_id]

        profile_path = self.storage_dir / f"{creator_id}.json"
        if profile_path.exists():
            try:
                data = profile_path.read_text(encoding="utf-8")
                profile = CreatorProfile.from_json(data)
                self._profiles[creator_id] = profile
                return profile
            except Exception as exc:
                logger.warning(f"Failed to load creator profile from {profile_path}: {exc}")

        return None

    def save_creator_profile(self, profile: CreatorProfile) -> None:
        """Persist updated Creator DNA profile."""
        self._profiles[profile.creator_id] = profile
        profile_path = self.storage_dir / f"{profile.creator_id}.json"
        try:
            profile_path.write_text(profile.to_json(), encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to write creator profile to {profile_path}: {exc}")

    def get_project(self, project_id: str) -> Optional[ContentProject]:
        """Retrieve ContentProject from in-memory / file cache."""
        return self._projects.get(project_id)

    def save_project(self, project: ContentProject) -> None:
        """Persist ContentProject to in-memory / file cache."""
        self._projects[project.project_id] = project

    def record_transition(self, record: ProductionHistoryRecord) -> None:
        """Record state machine transition to in-memory history log."""
        self._history.setdefault(record.project_id, []).append(record)

    def get_project_history(self, project_id: str) -> List[ProductionHistoryRecord]:
        """Retrieve history records for a project."""
        return self._history.get(project_id, [])

    def recall_context(
        self,
        query: str,
        creator_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryRecallItem]:
        """Recall relevant rules, brand guidelines, and past learnings matching query."""
        results: List[MemoryRecallItem] = []
        q_lower = query.lower()

        # 1. Search creator brand constitution & negative constraints
        profile = self.get_creator_profile(creator_id) if creator_id else None
        if profile:
            rules = getattr(profile, "negative_rules", []) or getattr(profile, "negative_constraints", [])
            for neg in rules:
                score = 1.0 if any(term in neg.lower() for term in q_lower.split()) else 0.5
                results.append(
                    MemoryRecallItem(
                        source="creator_profile.negative_rules",
                        category="negative_rule",
                        content=neg,
                        score=score,
                        metadata={"creator_id": profile.creator_id},
                    )
                )
            tones = getattr(profile, "tone_of_voice", [])
            tone_str = ", ".join(tones) if isinstance(tones, list) else str(getattr(profile, "tone", "authoritative"))
            audiences = getattr(profile, "target_audiences", [])
            aud_str = ", ".join(audiences) if isinstance(audiences, list) else str(getattr(profile, "target_audience", "General"))
            results.append(
                MemoryRecallItem(
                    source="creator_profile.brand",
                    category="tone",
                    content=f"Tone: {tone_str}. Target Audience: {aud_str}",
                    score=0.8,
                    metadata={"creator_id": profile.creator_id},
                )
            )

        # 2. Search learning candidates
        for lc in self._learning_candidates:
            if isinstance(lc, dict):
                obs = str(lc.get("observation", "") or "")
                action = str(lc.get("recommended_action", lc.get("proposed_action", "")) or "")
                rule_type = str(lc.get("rule_type", lc.get("category", "learning")) or "learning")
                lesson_id = str(lc.get("lesson_id", lc.get("candidate_id", "lc_unknown")) or "lc_unknown")
                hyp = str(lc.get("hypothesis", "") or "")
            else:
                obs = str(getattr(lc, "observation", "") or "")
                action = str(getattr(lc, "recommended_action", getattr(lc, "proposed_action", "")) or "")
                rule_type = str(getattr(lc, "rule_type", getattr(lc, "category", "learning")) or "learning")
                lesson_id = str(getattr(lc, "lesson_id", getattr(lc, "candidate_id", "lc_unknown")) or "lc_unknown")
                hyp = str(getattr(lc, "hypothesis", "") or "")

            q_terms = [term for term in q_lower.split() if term]
            phrase_match = (
                q_lower in obs.lower()
                or q_lower in action.lower()
                or q_lower in rule_type.lower()
                or (bool(hyp) and q_lower in hyp.lower())
            )
            term_match = (
                any(
                    term in obs.lower()
                    or term in action.lower()
                    or term in rule_type.lower()
                    or (bool(hyp) and term in hyp.lower())
                    for term in q_terms
                )
                if q_terms
                else False
            )

            if phrase_match or term_match:
                results.append(
                    MemoryRecallItem(
                        source="learning_candidates",
                        category=rule_type,
                        content=f"Observation: {obs} -> Rule: {action}",
                        score=0.9,
                        metadata={"candidate_id": lesson_id, "lesson_id": lesson_id},
                    )
                )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def record_production_telemetry(
        self,
        project_id: str,
        metrics: Dict[str, Any],
        learning_candidates: Optional[List[LearningCandidate]] = None,
    ) -> None:
        """Record completed production metrics, retention curves, and learning candidates."""
        self._telemetry[project_id] = {
            "metrics": metrics,
            "recorded_at": metrics.get("timestamp"),
        }
        if learning_candidates:
            self._learning_candidates.extend(learning_candidates)

    def render_system_prompt_block(self, creator_id: Optional[str] = None) -> str:
        """Generate static creator instructions for system prompt injection.

        Preserves prompt caching by generating a byte-stable, deterministic block.
        """
        profile = self.get_creator_profile(creator_id) if creator_id else None
        if not profile:
            return (
                "### Creator Identity & Brand Constitution\n"
                "- Tone: Authoritative, Educational, Engaging\n"
                "- Audience: Tech Enthusiasts & Professionals\n"
                "- Negative Constraints: No clickbait hyperbole, no unverified claims."
            )

        name = getattr(profile, "display_name", getattr(profile, "brand_name", profile.creator_id))
        tones = getattr(profile, "tone_of_voice", [])
        tone_str = ", ".join(tones) if isinstance(tones, list) else str(getattr(profile, "tone", "authoritative"))
        audiences = getattr(profile, "target_audiences", [])
        aud_str = ", ".join(audiences) if isinstance(audiences, list) else str(getattr(profile, "target_audience", "General"))
        rules = getattr(profile, "negative_rules", []) or getattr(profile, "negative_constraints", [])
        constraints_str = "\n".join(f"  * {c}" for c in rules) or "  * None"
        return (
            f"### Creator Identity: {name}\n"
            f"- Tone: {tone_str}\n"
            f"- Target Audience: {aud_str}\n"
            f"- Brand Constraints:\n{constraints_str}"
        )

    def close(self) -> None:
        """Close resources."""
        pass
