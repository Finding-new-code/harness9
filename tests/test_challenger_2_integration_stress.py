"""Adversarial Integration Stress & Backward-Compatibility Test Suite.

Empirical Challenger 2 Suite for Milestone M1 (adapters/hermes/ and src/h9_runtime/).
Tests:
1. HermesBridge.run_production() parameter fuzzing, valid/invalid inputs, sandbox audit records.
2. ContentRuntime 17-state machine graph strict compliance, jump rejection, failure handling.
3. CreatorProfile and DefaultMemoryRuntime persistence, recall accuracy, and prompt caching determinism.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from adapters.hermes.bridge import HermesBridge
from adapters.hermes.sandbox import HermesSessionSandbox
from src.h9_runtime.content import ContentRuntime, DefaultContentRuntime
from src.h9_runtime.execution import DefaultExecutionRuntime
from src.h9_runtime.memory import DefaultMemoryRuntime, MemoryRuntime
from src.h9_runtime.types import ProductionResult
from src.models.contracts import (
    ContentBrief,
    CreatorProfile,
    LearningCandidate,
)
from src.orchestrator.state_machine import (
    ProductionState,
    ProductionStateMachine,
    StateTransitionError,
)


class TestHermesBridgeIntegrationStress(unittest.TestCase):
    """Adversarial stress testing for HermesBridge and HermesSessionSandbox."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.bridge = HermesBridge(base_output_dir=self.base_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_run_production_valid_parameters_contract_compliance(self):
        """Verify HermesBridge.run_production returns exact previous contract dictionary and produces sandbox audit records."""
        session_id = "stress_valid_sess_01"
        topic = "Semiconductor Lithography"

        result = self.bridge.run_production(
            session_id=session_id,
            topic=topic,
            format="16:9",
            duration=5,
            offline=True,
        )

        # 1. Verify contract dictionary keys
        expected_keys = {
            "success",
            "session_id",
            "project_id",
            "topic",
            "video_path",
            "duration_seconds",
            "aspect_ratio",
            "elapsed_seconds",
            "state",
            "state_history",
            "render_artifact",
            "publish_package",
        }
        self.assertTrue(expected_keys.issubset(result.keys()))
        self.assertTrue(result["success"])
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["topic"], topic)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["duration_seconds"], 5)
        self.assertEqual(result["aspect_ratio"], "16:9")
        self.assertGreater(result["elapsed_seconds"], 0.0)

        # 2. Verify video artifact
        video_path = Path(result["video_path"])
        self.assertTrue(video_path.exists())
        self.assertGreater(video_path.stat().st_size, 0)
        self.assertEqual(result["render_artifact"]["width"], 1920)
        self.assertEqual(result["render_artifact"]["height"], 1080)

        # 3. Verify sandbox audit records
        sandbox = self.bridge.get_sandbox(session_id)
        audit_dir = sandbox.get_audit_dir()
        self.assertTrue((audit_dir / "state_machine.json").exists())
        self.assertTrue((audit_dir / "publish_package.json").exists())
        self.assertTrue((audit_dir / "evaluation_report.json").exists())

        audit_records = sandbox.get_audit_records()
        self.assertGreaterEqual(len(audit_records), 3)

        sm_record = next(r for r in audit_records if "current_state" in r)
        self.assertEqual(sm_record["current_state"], "COMPLETED")
        self.assertEqual(len(sm_record["history"]), 16)

        # 4. Verify sandbox inspection
        inspection = self.bridge.inspect_session(session_id)
        self.assertEqual(inspection["session_id"], session_id)
        self.assertEqual(inspection["current_state"], "COMPLETED")
        self.assertGreaterEqual(inspection["render_count"], 1)
        self.assertEqual(len(inspection["history"]), 16)

        # 5. Verify sandbox evaluation
        eval_report = self.bridge.evaluate_session(session_id)
        self.assertTrue(eval_report["passed"])
        self.assertGreater(eval_report["composite_score"], 0.8)

    def test_02_run_production_vertical_format_and_creator_id(self):
        """Verify format 9:16 vertical video and creator metadata pass through correctly."""
        session_id = "stress_vert_sess_02"
        result = self.bridge.run_production(
            session_id=session_id,
            topic="Quantum Dots in Displays",
            format="9:16",
            duration=5,
            offline=True,
            custom_instructions="Focus on QLED quantum dot efficiency",
            creator_id="creator_tech_reviewer",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["aspect_ratio"], "9:16")
        self.assertEqual(result["render_artifact"]["width"], 1080)
        self.assertEqual(result["render_artifact"]["height"], 1920)

    def test_03_run_production_invalid_parameters_rejection(self):
        """Verify invalid parameters (empty topic, out-of-range duration, invalid format) are rejected via ValidationError."""
        # Empty topic
        with self.assertRaises(ValidationError):
            self.bridge.run_production(
                session_id="err_sess_01",
                topic="",
                duration=5,
            )

        # Duration below minimum (< 5)
        with self.assertRaises(ValidationError):
            self.bridge.run_production(
                session_id="err_sess_02",
                topic="Nanotechnology",
                duration=2,
            )

        # Duration above maximum (> 600)
        with self.assertRaises(ValidationError):
            self.bridge.run_production(
                session_id="err_sess_03",
                topic="Nanotechnology",
                duration=700,
            )

        # Invalid aspect ratio
        with self.assertRaises(ValidationError):
            self.bridge.run_production(
                session_id="err_sess_04",
                topic="Nanotechnology",
                format="4:3",
            )

    def test_04_session_id_path_traversal_confinement(self):
        """Verify malicious path traversal in session_id is sanitized and confined within base_dir."""
        evil_session = "../../escape_attack_session"
        result = self.bridge.run_production(
            session_id=evil_session,
            topic="Silicon Photonics",
            duration=5,
            offline=True,
        )

        self.assertTrue(result["success"])
        sandbox = self.bridge.get_sandbox(evil_session)
        # Sandbox must reside strictly inside self.base_dir
        self.assertTrue(str(sandbox.get_session_root().resolve()).startswith(str(self.base_dir.resolve())))
        self.assertNotIn("..", str(sandbox.get_session_root()))

    def test_05_failed_pipeline_audit_generation(self):
        """Verify that when pipeline execution fails, HermesBridge returns success=False and saves failure audit log."""
        mock_runtime = MagicMock(spec=ContentRuntime)
        mock_runtime.run_full_production.return_value = ProductionResult(
            success=False,
            project_id="proj_fail_test",
            session_id="fail_session_01",
            error_message="Simulated rendering engine timeout",
            state_history=[
                {"from_state": "CREATED", "to_state": "RESEARCH_PLANNED"},
                {"from_state": "RESEARCH_PLANNED", "to_state": "RESEARCH_IN_PROGRESS"},
                {"from_state": "RESEARCH_IN_PROGRESS", "to_state": "FAILED"},
            ],
            elapsed_seconds=1.23,
        )

        fail_bridge = HermesBridge(
            base_output_dir=self.base_dir,
            content_runtime=mock_runtime,
        )

        res = fail_bridge.run_production(
            session_id="fail_session_01",
            topic="Failed Topic",
            duration=5,
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["state"], "FAILED")
        self.assertEqual(res["error"], "Simulated rendering engine timeout")
        self.assertEqual(len(res["state_history"]), 3)

        # Verify failure audit record was persisted to sandbox
        sandbox = fail_bridge.get_sandbox("fail_session_01")
        records = sandbox.get_audit_records()
        sm_record = next(r for r in records if "current_state" in r)
        self.assertEqual(sm_record["current_state"], "FAILED")

    def test_06_inspect_and_evaluate_non_existent_session(self):
        """Verify inspect_session and evaluate_session handle un-run sessions gracefully."""
        res_inspect = self.bridge.inspect_session("unrun_session_xyz")
        self.assertEqual(res_inspect["current_state"], "UNKNOWN")
        self.assertEqual(res_inspect["render_count"], 0)
        self.assertEqual(res_inspect["renders"], [])
        self.assertEqual(res_inspect["audit_records_count"], 0)
        self.assertEqual(res_inspect["history"], [])

        res_eval = self.bridge.evaluate_session("unrun_session_xyz")
        self.assertFalse(res_eval["passed"])
        self.assertEqual(res_eval["composite_score"], 0.0)
        self.assertIn("Video file not found.", res_eval["feedback"])


class TestContentRuntimeStateMachineAdherence(unittest.TestCase):
    """Adversarial testing for 17-state machine graph enforcement in ContentRuntime."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.content_rt = DefaultContentRuntime(base_workspace_dir=self.base_dir / "ws")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_07_canonical_17_state_sequential_execution(self):
        """Verify DefaultContentRuntime traverses all 17 canonical states in exact order with 16 transitions."""
        brief = ContentBrief(
            project_id="proj_canon_17",
            topic="Solid State Batteries",
            target_duration_seconds=5,
            aspect_ratio="16:9",
            offline_mode=True,
        )

        result = self.content_rt.run_full_production(brief=brief, session_id="canon_sess_17")

        self.assertTrue(result.success)
        self.assertEqual(len(result.state_history), 16)

        canonical_names = [s.value for s in ProductionState.canonical_states()]

        for i, transition in enumerate(result.state_history):
            self.assertEqual(
                transition["from_state"],
                canonical_names[i],
                f"Transition {i} from_state mismatch: expected {canonical_names[i]}, got {transition['from_state']}",
            )
            self.assertEqual(
                transition["to_state"],
                canonical_names[i + 1],
                f"Transition {i} to_state mismatch: expected {canonical_names[i + 1]}, got {transition['to_state']}",
            )

    def test_08_illegal_state_jumps_rejected(self):
        """Verify arbitrary illegal jumps across the state graph raise StateTransitionError."""
        sm = ProductionStateMachine(run_id="jump_adversary")

        # 1. Cannot jump from CREATED to COMPLETED
        self.assertFalse(sm.can_transition(ProductionState.COMPLETED))
        with self.assertRaises(StateTransitionError):
            sm.transition_to(ProductionState.COMPLETED)

        # 2. Cannot jump from CREATED to SCRIPT_COMPLETED
        self.assertFalse(sm.can_transition(ProductionState.SCRIPT_COMPLETED))
        with self.assertRaises(StateTransitionError):
            sm.transition_to(ProductionState.SCRIPT_COMPLETED)

        # 3. Step to RESEARCH_PLANNED, attempt jump to RENDER_IN_PROGRESS
        sm.transition_to(ProductionState.RESEARCH_PLANNED)
        self.assertFalse(sm.can_transition(ProductionState.RENDER_IN_PROGRESS))
        with self.assertRaises(StateTransitionError):
            sm.transition_to(ProductionState.RENDER_IN_PROGRESS)

        # 4. Step to RESEARCH_IN_PROGRESS, attempt backward jump to CREATED
        sm.transition_to(ProductionState.RESEARCH_IN_PROGRESS)
        self.assertFalse(sm.can_transition(ProductionState.CREATED))
        with self.assertRaises(StateTransitionError):
            sm.transition_to(ProductionState.CREATED)

    def test_09_pipeline_exception_handling_and_state_failed(self):
        """Verify pipeline exceptions are caught and transition cleanly to FAILED state."""
        brief = ContentBrief(
            project_id="proj_exc_test",
            topic="Quantum Cryptography",
            target_duration_seconds=5,
            offline_mode=True,
        )

        with patch("src.h9_runtime.content.Pipeline.run", side_effect=RuntimeError("GPU kernel memory exhausted")):
            result = self.content_rt.run_full_production(brief=brief, session_id="exc_sess_01")

        self.assertFalse(result.success)
        self.assertIn("GPU kernel memory exhausted", result.error_message)
        self.assertGreaterEqual(len(result.state_history), 2)
        last_transition = result.state_history[-1]
        self.assertEqual(last_transition["to_state"], "FAILED")


class TestCreatorProfileAndMemoryRuntimeStress(unittest.TestCase):
    """Adversarial testing for CreatorProfile persistence, context recall, and cache determinism."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name) / "memory"
        self.memory_rt = DefaultMemoryRuntime(storage_dir=self.storage_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_10_creator_profile_full_persistence_across_instances(self):
        """Verify deep CreatorProfile fields persist across completely separate runtime instances."""
        profile = CreatorProfile(
            creator_id="creator_quantum_007",
            display_name="Quantum Horizon",
            tone_of_voice=["rigorous", "visionary", "concise"],
            target_audiences=["Physicists", "Semiconductor Engineers"],
            brand_colors={
                "primary": "#00ffcc",
                "background": "#050811",
                "text": "#ffffff",
                "accent": "#ff007f",
            },
            default_format="9:16",
            negative_rules=[
                "Never mention hype buzzwords like revolutionary",
                "No unverified quantum advantage claims",
                "Never cite paywalled unverified preprints",
            ],
            voice_preference="en-US-Neural2-F",
            metadata={"tier": "enterprise", "created_by": "challenger_2"},
        )

        self.memory_rt.save_creator_profile(profile)

        # Verify file exists on disk
        target_file = self.storage_dir / "creator_quantum_007.json"
        self.assertTrue(target_file.exists())

        # Instantiate a FRESH runtime instance with empty memory cache
        fresh_rt = DefaultMemoryRuntime(storage_dir=self.storage_dir)
        loaded = fresh_rt.get_creator_profile("creator_quantum_007")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.creator_id, "creator_quantum_007")
        self.assertEqual(loaded.display_name, "Quantum Horizon")
        self.assertEqual(loaded.tone_of_voice, ["rigorous", "visionary", "concise"])
        self.assertEqual(loaded.target_audiences, ["Physicists", "Semiconductor Engineers"])
        self.assertEqual(loaded.default_format, "9:16")
        self.assertEqual(len(loaded.negative_rules), 3)
        self.assertEqual(loaded.brand_colors["primary"], "#00ffcc")
        self.assertEqual(loaded.voice_preference, "en-US-Neural2-F")
        self.assertEqual(loaded.metadata["tier"], "enterprise")

    def test_11_creator_profile_mutation_and_updates(self):
        """Verify updating CreatorProfile fields overwrites cleanly and persists across instances."""
        profile = CreatorProfile(
            creator_id="mut_creator",
            display_name="Old Name",
            negative_rules=["Rule 1"],
        )
        self.memory_rt.save_creator_profile(profile)

        # Update profile
        profile.display_name = "New Updated Name"
        profile.negative_rules.append("Rule 2: No clickbait")
        self.memory_rt.save_creator_profile(profile)

        fresh_rt = DefaultMemoryRuntime(storage_dir=self.storage_dir)
        loaded = fresh_rt.get_creator_profile("mut_creator")
        self.assertEqual(loaded.display_name, "New Updated Name")
        self.assertEqual(len(loaded.negative_rules), 2)
        self.assertIn("Rule 2: No clickbait", loaded.negative_rules)

    def test_12_context_recall_scoring_and_learning_candidates(self):
        """Verify context recall scores negative rules and learning candidates accurately."""
        profile = CreatorProfile(
            creator_id="recall_creator",
            display_name="DeepTech",
            negative_rules=[
                "Never use sensational clickbait or hyperbole",
                "No fake benchmark comparisons",
            ],
            tone_of_voice=["analytical"],
            target_audiences=["Developers"],
        )
        self.memory_rt.save_creator_profile(profile)

        # Record production telemetry with learning candidates
        cand1 = LearningCandidate(
            lesson_id="lc_pacing_01",
            creator_id="recall_creator",
            rule_type="pacing",
            observation="Viewers drop off after 10 seconds of static narration",
            recommended_action="Limit static narration scenes to 6 seconds",
            confidence=0.88,
        )
        self.memory_rt.record_production_telemetry(
            project_id="proj_recall_01",
            metrics={"retention_rate": 0.72},
            learning_candidates=[cand1],
        )

        # Recall 1: Query matching negative rule
        recalls_neg = self.memory_rt.recall_context(
            query="clickbait hyperbole",
            creator_id="recall_creator",
            limit=5,
        )
        self.assertGreater(len(recalls_neg), 0)
        self.assertEqual(recalls_neg[0].category, "negative_rule")
        self.assertEqual(recalls_neg[0].score, 1.0)
        self.assertIn("clickbait", recalls_neg[0].content)

        # Recall 2: Query matching learning candidate
        recalls_learn = self.memory_rt.recall_context(
            query="static narration pacing",
            creator_id="recall_creator",
            limit=5,
        )
        cand_recall = next((r for r in recalls_learn if r.category == "pacing"), None)
        self.assertIsNotNone(cand_recall)
        self.assertEqual(cand_recall.score, 0.9)
        self.assertIn("Limit static narration scenes to 6 seconds", cand_recall.content)

        # Limit parameter enforcement
        recalls_limited = self.memory_rt.recall_context(
            query="narration",
            creator_id="recall_creator",
            limit=1,
        )
        self.assertEqual(len(recalls_limited), 1)

    def test_13_byte_stable_prompt_block_determinism(self):
        """Verify render_system_prompt_block produces 100% byte-identical output across calls and instances."""
        profile = CreatorProfile(
            creator_id="stable_creator",
            display_name="Deterministic Labs",
            tone_of_voice=["objective", "concise"],
            target_audiences=["Engineers"],
            negative_rules=["Rule A", "Rule B"],
        )
        self.memory_rt.save_creator_profile(profile)

        rt1 = DefaultMemoryRuntime(storage_dir=self.storage_dir)
        rt2 = DefaultMemoryRuntime(storage_dir=self.storage_dir)

        block1 = rt1.render_system_prompt_block("stable_creator")
        block2 = rt2.render_system_prompt_block("stable_creator")

        # 1. Byte-for-byte identity
        self.assertEqual(block1, block2)

        # 2. Repeated calls identity
        for _ in range(25):
            self.assertEqual(rt1.render_system_prompt_block("stable_creator"), block1)

        # 3. Verify absence of volatile timestamps or dynamic counters
        self.assertNotIn("2026-", block1)
        self.assertNotIn("timestamp", block1.lower())
        self.assertIn("Deterministic Labs", block1)
        self.assertIn("Rule A", block1)

        # 4. Fallback block determinism
        fallback1 = rt1.render_system_prompt_block(None)
        fallback2 = rt2.render_system_prompt_block(None)
        self.assertEqual(fallback1, fallback2)

    def test_14_memory_error_resilience_and_corrupted_files(self):
        """Verify memory runtime gracefully handles missing creators and corrupted JSON files."""
        # Missing creator returns None
        self.assertIsNone(self.memory_rt.get_creator_profile("non_existent_creator"))

        # Write corrupted JSON to disk
        corrupt_file = self.storage_dir / "corrupt_creator.json"
        corrupt_file.write_text("{ this is malformed json : [unclosed", encoding="utf-8")

        # Should log warning and return None without raising exception
        res = self.memory_rt.get_creator_profile("corrupt_creator")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
