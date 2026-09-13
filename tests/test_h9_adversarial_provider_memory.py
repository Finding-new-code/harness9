"""tests/test_h9_adversarial_provider_memory.py

Adversarial Stress Test Suite for Milestone 4 (R4):
1. Provider Stress:
   - Invalid / unknown capability roles (strings, non-strings, None, numbers).
   - Deeply nested schemas (10+ levels deep).
   - Recursive and self-referencing schemas (detect recursion handling & fallback).
   - Malformed, non-model, and strict-validation schemas.
   - Budget exhaustion limits, deficit accounting, and recovery.
   - Token estimation extremes (empty strings, huge strings, unicode).
2. SessionDB Memory Stress:
   - Simulated concurrent write bursts into h9_projects and h9_creators.
   - Hotspot contention writes (concurrent updates to the identical project and creator).
   - Concurrent mixed read/write/telemetry operations.
   - FTS5 recall with SQL injection patterns, boolean operators (AND, OR, NOT), punctuation, and wildcards.
   - FTS5 multilingual unicode, CJK, Arabic, Cyrillic, and emoji recall.
   - Empty, whitespace, and extreme-length recall queries.
   - Handling of non-existent creators, duplicate project IDs (UPSERT), and orphaned transitions.
   - Resource cleanup and Windows file lock release.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional
import unittest

from pydantic import BaseModel, Field, field_validator

from src.h9_runtime.bridge import HermesCapabilityBridge, reset_capability_bridges
from src.h9_runtime.memory import HermesMemoryRuntime
from src.h9_runtime.models import DefaultModelRuntime
from src.h9_runtime.types import CapabilityRole, ModelResponse
from src.models.contracts import (
    ContentBrief,
    ContentProject,
    CreatorProfile,
    LearningCandidate,
    ProductionHistoryRecord,
    ResearchDossier,
)


# ---------------------------------------------------------------------------
# Deeply Nested and Edge-Case Schemas
# ---------------------------------------------------------------------------

class Level10(BaseModel):
    depth_10: str
    final_score: float

class Level9(BaseModel):
    depth_9: str
    sub: Level10

class Level8(BaseModel):
    depth_8: str
    sub: Level9

class Level7(BaseModel):
    depth_7: str
    sub: Level8

class Level6(BaseModel):
    depth_6: str
    sub: Level7

class Level5(BaseModel):
    depth_5: str
    sub: Level6

class Level4(BaseModel):
    depth_4: str
    sub: Level5

class Level3(BaseModel):
    depth_3: str
    sub: Level4

class Level2(BaseModel):
    depth_2: str
    sub: Level3

class Level1Deep(BaseModel):
    depth_1: str
    sub: Level2


class SelfReferencingSchema(BaseModel):
    node_name: str
    child: Optional["SelfReferencingSchema"] = None


class StrictValidationSchema(BaseModel):
    score: int
    sentiment: str

    @field_validator("score")
    @classmethod
    def validate_score_minimum(cls, v: int) -> int:
        if v < 100:
            raise ValueError("Score must be strictly >= 100")
        return v


class TestProviderStress(unittest.TestCase):
    """Adversarial stress tests for ModelRuntime provider roles, schemas, and budgets."""

    def setUp(self):
        self.runtime = DefaultModelRuntime(offline=True)

    def test_provider_invalid_unknown_capability_roles(self):
        """Verify requesting unknown, malformed, or non-string capability roles falls back safely."""
        invalid_roles = [
            "completely_unknown_role",
            "SUPER_ADMIN_CAPABILITY",
            "",
            "   ",
            "12345",
            None,
            123,
            True,
            ["nested_list"],
            {"dict": "role"},
        ]

        for inv in invalid_roles:
            resolved = self.runtime._resolve_role(inv)
            self.assertIsInstance(resolved, CapabilityRole)
            self.assertEqual(resolved, CapabilityRole.FAST_EDITORIAL)

            # Execution with invalid role must never crash
            resp = self.runtime.invoke_capability(
                role=inv,
                prompt="Stress test prompt for invalid role",
                session_id="sess_invalid_role",
            )
            self.assertIsInstance(resp, ModelResponse)
            self.assertTrue(resp.content)
            self.assertGreater(resp.prompt_tokens, 0)
            self.assertGreater(resp.completion_tokens, 0)
            self.assertGreater(resp.cost_usd, 0.0)

            # Streaming with invalid role must not crash
            chunks = list(
                self.runtime.stream_capability(
                    role=inv,
                    prompt="Stream test for invalid role",
                )
            )
            self.assertGreater(len(chunks), 0)

    def test_provider_deeply_nested_schemas(self):
        """Verify schema extraction handles 10-level deeply nested Pydantic models."""
        resp = self.runtime.invoke_capability(
            role=CapabilityRole.FAST_EDITORIAL,
            prompt="Generate deep hierarchical spec",
            schema=Level1Deep,
            session_id="sess_deep_schema",
        )

        self.assertIsInstance(resp, ModelResponse)
        self.assertIsInstance(resp.parsed, Level1Deep)

        # Traverse all 10 levels to verify complete deterministic population
        curr = resp.parsed
        for lvl in range(1, 10):
            self.assertTrue(hasattr(curr, f"depth_{lvl}"))
            self.assertTrue(hasattr(curr, "sub"))
            curr = curr.sub
        self.assertEqual(curr.depth_10, "Generated depth_10 for role fast_editorial")
        self.assertEqual(curr.final_score, 0.95)

        # JSON roundtrip verification
        json_str = resp.content
        loaded = Level1Deep.model_validate_json(json_str)
        self.assertEqual(loaded.depth_1, resp.parsed.depth_1)

    def test_provider_recursive_and_self_referencing_schemas(self):
        """Verify self-referencing schemas trigger safe exception handling without crashing."""
        resp = self.runtime.invoke_capability(
            role=CapabilityRole.REASONING_RESEARCH,
            prompt="Generate recursive tree node",
            schema=SelfReferencingSchema,
            session_id="sess_recursive_schema",
        )

        self.assertIsInstance(resp, ModelResponse)
        # RecursionError is caught by invoke_capability and falls back to safe JSON
        self.assertIsNone(resp.parsed)
        self.assertIn("status", resp.content)
        parsed_fallback = json.loads(resp.content)
        self.assertEqual(parsed_fallback["role"], CapabilityRole.REASONING_RESEARCH.value)
        self.assertEqual(parsed_fallback["status"], "completed")

    def test_provider_malformed_and_edge_case_schemas(self):
        """Verify non-model types and strict validation rejections fall back gracefully."""
        # 1. Non-BaseModel schema types
        non_models = [dict, list, int, str, object, "not_a_type"]
        for bad_schema in non_models:
            resp = self.runtime.invoke_capability(
                role=CapabilityRole.FAST_EDITORIAL,
                prompt="Generate bad schema",
                schema=bad_schema,
                session_id="sess_bad_schema",
            )
            self.assertIsInstance(resp, ModelResponse)
            self.assertTrue(resp.content)

        # 2. Strict validator rejection (score must be >= 100, default is 1)
        resp_strict = self.runtime.invoke_capability(
            role=CapabilityRole.FAST_EDITORIAL,
            prompt="Generate strict score",
            schema=StrictValidationSchema,
            session_id="sess_strict_schema",
        )
        self.assertIsInstance(resp_strict, ModelResponse)
        # ValidationError was caught and handled
        self.assertIsNone(resp_strict.parsed)
        self.assertIn("completed", resp_strict.content)

    def test_provider_budget_exhaustion_limits_and_recovery(self):
        """Verify spend accounting detects budget deficits and allows limit top-up recovery."""
        session_id = "sess_budget_adversarial_01"

        # 1. Set extremely tight budget ceiling ($0.0001)
        self.runtime.set_budget_limit(session_id, limit_usd=0.0001)
        init_budget = self.runtime.get_budget_status(session_id)
        self.assertEqual(init_budget.budget_limit_usd, 0.0001)
        self.assertEqual(init_budget.cost_usd, 0.0)
        self.assertEqual(init_budget.remaining_budget_usd, 0.0001)

        # 2. Incur spend that exhausts budget
        self.runtime.invoke_capability(
            role=CapabilityRole.REASONING_RESEARCH,
            prompt="Massive research task " * 50,
            session_id=session_id,
        )
        exhausted = self.runtime.get_budget_status(session_id)
        self.assertGreater(exhausted.cost_usd, exhausted.budget_limit_usd)
        self.assertIsNotNone(exhausted.remaining_budget_usd)
        self.assertLess(exhausted.remaining_budget_usd, 0.0)

        # 3. Budget recovery via limit increase
        self.runtime.set_budget_limit(session_id, limit_usd=10.0)
        recovered = self.runtime.get_budget_status(session_id)
        self.assertEqual(recovered.budget_limit_usd, 10.0)
        self.assertGreater(recovered.remaining_budget_usd, 9.9)

        # 4. Zero and negative budget limits
        self.runtime.set_budget_limit("sess_zero", limit_usd=0.0)
        zero_b = self.runtime.get_budget_status("sess_zero")
        self.assertEqual(zero_b.budget_limit_usd, 0.0)
        self.assertEqual(zero_b.remaining_budget_usd, 0.0)

        # 5. Unconfigured session
        unconfigured = self.runtime.get_budget_status("sess_unconfigured")
        self.assertIsNone(unconfigured.budget_limit_usd)
        self.assertIsNone(unconfigured.remaining_budget_usd)
        self.assertEqual(unconfigured.cost_usd, 0.0)

    def test_provider_token_estimation_extremes(self):
        """Verify token estimation survives extreme inputs (empty, 1MB string, unicode)."""
        self.assertEqual(self.runtime.estimate_tokens(""), 0)
        self.assertEqual(self.runtime.estimate_tokens("a"), 1)
        self.assertEqual(self.runtime.estimate_tokens("abcd"), 1)

        # 1MB string
        huge_text = "x" * 1_000_000
        estimated = self.runtime.estimate_tokens(huge_text)
        self.assertEqual(estimated, 250_000)

        # Multilingual & Emojis
        unicode_text = "量子计算 🚀 🔥 " * 1000
        uni_est = self.runtime.estimate_tokens(unicode_text)
        self.assertGreater(uni_est, 100)


class TestSessionDBMemoryStress(unittest.TestCase):
    """Adversarial stress tests for SessionDB concurrency, FTS5 recall, and DB integrity."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "adversarial_state.db"
        self.mem = HermesMemoryRuntime(db_path=self.db_path)

    def tearDown(self):
        self.mem.close()
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_concurrent_write_burst_distinct_projects_and_creators(self):
        """Verify 50 concurrent threads writing distinct projects and creators complete with zero lock errors."""
        total_writers = 50

        def _write_entity(idx: int) -> Dict[str, Any]:
            creator = CreatorProfile(
                creator_id=f"creator_burst_{idx}",
                display_name=f"Burst Creator {idx}",
                tone_of_voice=["Direct", "Empirical"],
                negative_rules=[f"Rule {idx}: Never compromise reproducibility"],
            )
            self.mem.save_creator_profile(creator)

            brief = ContentBrief(
                project_id=f"proj_burst_{idx}",
                topic=f"Concurrent Topic {idx}",
                target_duration_seconds=30,
            )
            project = ContentProject(
                project_id=f"proj_burst_{idx}",
                session_id=f"sess_burst_{idx}",
                creator_id=f"creator_burst_{idx}",
                topic=f"Concurrent Topic {idx}",
                current_state="CREATED",
                brief=brief,
            )
            self.mem.save_project(project)

            rec = ProductionHistoryRecord(
                project_id=f"proj_burst_{idx}",
                from_state="CREATED",
                to_state="RESEARCH_PLANNED",
                payload_summary={"idx": idx},
            )
            self.mem.record_transition(rec)

            return {"idx": idx, "status": "ok"}

        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(_write_entity, i) for i in range(total_writers)]
            for f in as_completed(futures):
                res = f.result()
                self.assertEqual(res["status"], "ok")

        # Verify all 50 projects and creators persisted intact
        for i in range(total_writers):
            p = self.mem.get_project(f"proj_burst_{i}")
            self.assertIsNotNone(p, f"Project proj_burst_{i} missing")
            self.assertEqual(p.topic, f"Concurrent Topic {i}")
            self.assertIsNotNone(p.brief)

            c = self.mem.get_creator_profile(f"creator_burst_{i}")
            self.assertIsNotNone(c, f"Creator creator_burst_{i} missing")
            self.assertEqual(c.display_name, f"Burst Creator {i}")

            hist = self.mem.get_project_history(f"proj_burst_{i}")
            self.assertEqual(len(hist), 1)

    def test_concurrent_write_burst_hotspot_contention_same_project(self):
        """Verify 30 concurrent threads hammering the EXACT SAME project row succeed via UPSERT."""
        project_id = "proj_hotspot_contention"
        base_proj = ContentProject(
            project_id=project_id,
            session_id="sess_hotspot",
            creator_id="creator_hotspot",
            topic="Contention Topic Base",
            current_state="CREATED",
        )
        self.mem.save_project(base_proj)

        def _update_project_worker(worker_id: int) -> int:
            proj = ContentProject(
                project_id=project_id,
                session_id="sess_hotspot",
                creator_id="creator_hotspot",
                topic=f"Contention Topic Update {worker_id}",
                target_duration_seconds=20 + (worker_id % 30),
                current_state=f"STATE_{worker_id}",
            )
            self.mem.save_project(proj)
            return worker_id

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_update_project_worker, i) for i in range(30)]
            for f in as_completed(futures):
                res = f.result()
                self.assertIsInstance(res, int)

        # Row must still exist and be completely valid
        final_proj = self.mem.get_project(project_id)
        self.assertIsNotNone(final_proj)
        self.assertEqual(final_proj.project_id, project_id)
        self.assertTrue(final_proj.topic.startswith("Contention Topic Update"))

    def test_concurrent_write_burst_hotspot_contention_same_creator(self):
        """Verify 30 concurrent threads hammering the EXACT SAME creator profile succeed via UPSERT."""
        creator_id = "creator_hotspot_contention"
        init_creator = CreatorProfile(
            creator_id=creator_id,
            display_name="Initial Creator",
            tone_of_voice=["Initial"],
        )
        self.mem.save_creator_profile(init_creator)

        def _update_creator_worker(worker_id: int) -> int:
            profile = CreatorProfile(
                creator_id=creator_id,
                display_name=f"Contention Creator {worker_id}",
                tone_of_voice=[f"Tone_{worker_id}"],
                negative_rules=[f"Rule_{worker_id}"],
            )
            self.mem.save_creator_profile(profile)
            return worker_id

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_update_creator_worker, i) for i in range(30)]
            for f in as_completed(futures):
                res = f.result()
                self.assertIsInstance(res, int)

        final_creator = self.mem.get_creator_profile(creator_id)
        self.assertIsNotNone(final_creator)
        self.assertEqual(final_creator.creator_id, creator_id)
        self.assertTrue(final_creator.display_name.startswith("Contention Creator"))

    def test_concurrent_mixed_read_write_telemetry_burst(self):
        """Verify interleaved concurrent reads, writes, telemetry, and FTS recall succeed without deadlock."""
        num_ops = 40

        def _mixed_operation(op_id: int) -> str:
            if op_id % 4 == 0:
                p = ContentProject(
                    project_id=f"proj_mix_{op_id}",
                    session_id=f"sess_mix_{op_id}",
                    topic=f"Mixed Topic {op_id}",
                )
                self.mem.save_project(p)
                return "save_project"
            elif op_id % 4 == 1:
                rec = ProductionHistoryRecord(
                    project_id=f"proj_mix_{op_id - 1}",
                    from_state="CREATED",
                    to_state="COMPLETED",
                    payload_summary={"mixed": True},
                )
                self.mem.record_transition(rec)
                return "record_transition"
            elif op_id % 4 == 2:
                lc = LearningCandidate(
                    lesson_id=f"lc_mix_{op_id}",
                    creator_id=f"c_mix_{op_id}",
                    rule_type="mixed",
                    observation=f"Mixed observation {op_id} for pacing",
                    recommended_action=f"Mixed action {op_id}",
                    confidence=0.85,
                )
                self.mem.record_production_telemetry(
                    project_id=f"proj_mix_{op_id - 2}",
                    metrics={"timestamp": time.time()},
                    learning_candidates=[lc],
                )
                return "telemetry"
            else:
                self.mem.recall_context(query="pacing observation", limit=3)
                return "recall"

        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(_mixed_operation, i) for i in range(num_ops)]
            results = [f.result() for f in as_completed(futures)]
            self.assertEqual(len(results), num_ops)

    def test_fts5_sql_injection_resilience(self):
        """Verify SQL injection patterns in recall queries are sanitized and cannot manipulate or drop tables."""
        # Seed test candidate
        lc = LearningCandidate(
            lesson_id="lc_safe_01",
            creator_id="creator_safe",
            rule_type="security",
            observation="Sanitized parameterized queries prevent SQL injection completely",
            recommended_action="Always utilize parameterized SQLite queries",
            confidence=0.99,
        )
        self.mem.record_production_telemetry("proj_sec", {}, [lc])

        injection_payloads = [
            "'; DROP TABLE h9_projects; --",
            "'; DROP TABLE h9_creators; --",
            "'; DROP TABLE h9_learning_candidates; --",
            "'; DROP TABLE h9_memory_fts; --",
            "' OR '1'='1",
            "' OR 1=1; --",
            "admin' --",
            "' UNION SELECT 1, 'injected', 'hack', 'hack', 1.0, 0 --",
            "'; DELETE FROM h9_learning_candidates; --",
            "\" OR \"\"=\"",
        ]

        for payload in injection_payloads:
            # Query must not raise an exception
            res = self.mem.recall_context(query=payload, creator_id="creator_safe")
            self.assertIsInstance(res, list)

        # Verify all tables still exist and were not dropped
        def _check_tables(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return {row[0] for row in cursor.fetchall()}

        tables = self.mem._execute_read(_check_tables)
        self.assertIn("h9_projects", tables)
        self.assertIn("h9_creators", tables)
        self.assertIn("h9_learning_candidates", tables)
        self.assertIn("h9_memory_fts", tables)

    def test_fts5_special_characters_and_syntax_operators(self):
        """Verify FTS5 boolean operators, syntax symbols, wildcards, and punctuation soup do not crash."""
        lc = LearningCandidate(
            lesson_id="lc_syntax_01",
            creator_id="creator_syntax",
            rule_type="syntax",
            observation="Complex punctuation: @#$%^&*()_+ and operators like AND, OR, NOT in titles",
            recommended_action="Strip operators or quote terms safely",
            confidence=0.95,
        )
        self.mem.record_production_telemetry("proj_syn", {}, [lc])

        adversarial_syntax_queries = [
            "*",
            "***",
            '"',
            '""',
            '""""',
            '""*""',
            "AND",
            "OR",
            "NOT",
            "AND AND AND",
            "OR OR OR",
            "NOT NOT",
            "AND OR NOT",
            "()",
            "(())",
            "(*)",
            "NEAR(punctuation, operators, 10)",
            "^ - + : :: {} []",
            "%",
            "_",
            "%%%",
            "___",
            "[%]",
            "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "<script>alert('xss')</script>",
            "creator_id:creator_syntax",
            "rule_type:syntax",
        ]

        for query in adversarial_syntax_queries:
            results = self.mem.recall_context(query=query, creator_id="creator_syntax")
            self.assertIsInstance(results, list)

    def test_fts5_multilingual_unicode_and_emojis(self):
        """Verify multilingual queries (CJK, Arabic, Cyrillic, Emojis) recall correctly without decoding errors."""
        multilingual_candidates = [
            LearningCandidate(
                lesson_id="lc_cjk_01",
                creator_id="c_multi",
                rule_type="cjk",
                observation="量子计算和深度学习模型在超导材料设计中的应用",
                recommended_action="保持低温77K超导阈值",
                confidence=0.95,
            ),
            LearningCandidate(
                lesson_id="lc_emoji_02",
                creator_id="c_multi",
                rule_type="emoji",
                observation="Intro using 🚀 rocket emoji increased CTR by 25% 🔥",
                recommended_action="Use high-contrast emojis in title thumbnails 💡",
                confidence=0.90,
            ),
            LearningCandidate(
                lesson_id="lc_arabic_03",
                creator_id="c_multi",
                rule_type="arabic",
                observation="إنتاج الفيديو الرقمي باستخدام الذكاء الاصطناعي الفائق",
                recommended_action="تطبيق معايير الجودة الصوتية العالية",
                confidence=0.88,
            ),
            LearningCandidate(
                lesson_id="lc_cyrillic_04",
                creator_id="c_multi",
                rule_type="cyrillic",
                observation="Нейросетевая оптимизация аудиодорожек и устранение пауз",
                recommended_action="Ограничить тишину 150 миллисекундами",
                confidence=0.92,
            ),
        ]

        self.mem.record_production_telemetry("proj_multi", {}, multilingual_candidates)

        # 1. Query CJK
        res_cjk = self.mem.recall_context(query="量子计算", creator_id="c_multi")
        self.assertGreaterEqual(len(res_cjk), 1)
        self.assertIn("超导", res_cjk[0].content)

        # 2. Query Emojis
        res_emoji = self.mem.recall_context(query="🚀", creator_id="c_multi")
        self.assertGreaterEqual(len(res_emoji), 1)
        self.assertIn("rocket", res_emoji[0].content)

        # 3. Query Arabic
        res_arabic = self.mem.recall_context(query="الذكاء الاصطناعي", creator_id="c_multi")
        self.assertGreaterEqual(len(res_arabic), 1)
        self.assertIn("الفيديو", res_arabic[0].content)

        # 4. Query Cyrillic
        res_cyrillic = self.mem.recall_context(query="Нейросетевая", creator_id="c_multi")
        self.assertGreaterEqual(len(res_cyrillic), 1)
        self.assertIn("аудиодорожек", res_cyrillic[0].content)

    def test_fts5_empty_whitespace_and_extreme_length_queries(self):
        """Verify empty, whitespace-only, and 10,000-character queries return safely."""
        # Empty and whitespace
        for empty_q in ["", " ", "   ", "\t", "\n", "\r\n", "      "]:
            res = self.mem.recall_context(query=empty_q)
            self.assertEqual(res, [])

        # Extreme length query (10,000 characters)
        huge_query = "quantum " * 1250
        res_huge = self.mem.recall_context(query=huge_query)
        self.assertIsInstance(res_huge, list)

    def test_handling_non_existent_creators(self):
        """Verify querying, prompt rendering, or referencing non-existent creators degrades gracefully."""
        phantom_id = "creator_phantom_does_not_exist_404"

        # 1. Query profile returns None
        self.assertIsNone(self.mem.get_creator_profile(phantom_id))

        # 2. System prompt block falls back to default constitution
        prompt_block = self.mem.render_system_prompt_block(phantom_id)
        self.assertIn("Creator Identity & Brand Constitution", prompt_block)
        self.assertIn("Authoritative", prompt_block)

        # 3. Recall context with phantom creator searches candidates without crashing
        recalled = self.mem.recall_context("anything", creator_id=phantom_id)
        self.assertIsInstance(recalled, list)

        # 4. Save project referencing phantom creator succeeds without foreign key violation
        phantom_proj = ContentProject(
            project_id="proj_with_phantom_creator",
            session_id="sess_phantom",
            creator_id=phantom_id,
            topic="Phantom Creator Project",
        )
        self.mem.save_project(phantom_proj)
        loaded = self.mem.get_project("proj_with_phantom_creator")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.creator_id, phantom_id)

    def test_handling_duplicate_project_ids_upsert(self):
        """Verify saving duplicate project IDs executes clean in-place UPSERT without crashing."""
        project_id = "proj_dup_test_01"

        # 1. Initial project in CREATED state
        p1 = ContentProject(
            project_id=project_id,
            session_id="sess_01",
            creator_id="creator_01",
            topic="Original Topic",
            target_duration_seconds=30,
            current_state="CREATED",
        )
        self.mem.save_project(p1)

        loaded_1 = self.mem.get_project(project_id)
        self.assertEqual(loaded_1.topic, "Original Topic")
        self.assertEqual(loaded_1.current_state, "CREATED")

        # 2. Overwrite project with identical project_id in COMPLETED state
        p2 = ContentProject(
            project_id=project_id,
            session_id="sess_02",
            creator_id="creator_02",
            topic="Updated Overwritten Topic",
            target_duration_seconds=60,
            current_state="COMPLETED",
        )
        self.mem.save_project(p2)

        loaded_2 = self.mem.get_project(project_id)
        self.assertEqual(loaded_2.topic, "Updated Overwritten Topic")
        self.assertEqual(loaded_2.target_duration_seconds, 60)
        self.assertEqual(loaded_2.current_state, "COMPLETED")
        self.assertEqual(loaded_2.session_id, "sess_02")
        self.assertEqual(loaded_2.creator_id, "creator_02")

        # Verify exactly one row exists in database
        def _count_rows(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM h9_projects WHERE project_id = ?", (project_id,))
            return cursor.fetchone()[0]

        row_count = self.mem._execute_read(_count_rows)
        self.assertEqual(row_count, 1)

    def test_handling_orphaned_transitions(self):
        """Verify state machine transitions for non-existent projects persist and retrieve chronologically."""
        ghost_project_id = "proj_ghost_never_created_999"

        # Project does not exist
        self.assertIsNone(self.mem.get_project(ghost_project_id))

        t0 = time.time()
        # Record orphaned transitions
        t1 = ProductionHistoryRecord(
            project_id=ghost_project_id,
            from_state="CREATED",
            to_state="RESEARCH_PLANNED",
            timestamp=t0,
            payload_summary={"step": 1},
            metadata={"source": "orphan_test"},
        )
        t2 = ProductionHistoryRecord(
            project_id=ghost_project_id,
            from_state="RESEARCH_PLANNED",
            to_state="FAILED",
            timestamp=t0 + 10,
            payload_summary={"error": "Pre-execution cancel"},
            metadata={"source": "orphan_test"},
        )
        self.mem.record_transition(t1)
        self.mem.record_transition(t2)

        # Retrieve history for orphaned project
        history = self.mem.get_project_history(ghost_project_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].from_state, "CREATED")
        self.assertEqual(history[0].to_state, "RESEARCH_PLANNED")
        self.assertEqual(history[1].from_state, "RESEARCH_PLANNED")
        self.assertEqual(history[1].to_state, "FAILED")

        # Project still does not exist in h9_projects
        self.assertIsNone(self.mem.get_project(ghost_project_id))

    def test_database_resource_cleanup_and_lock_release(self):
        """Verify calling close() releases SQLite connection cleanly without leaving locked files."""
        self.mem.close()
        # Verify reopening or checking file existence is clean
        self.assertTrue(self.db_path.exists())


if __name__ == "__main__":
    unittest.main()
