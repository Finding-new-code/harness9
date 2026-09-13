"""Adversarial stress-testing suite for Harness 9 Milestone M1 (State Machine, Contracts, Hermes Adapter).

Covers:
1. Out-of-order state transitions, 400-pair matrix probing, terminal state lockdown, illegal loopbacks.
2. HermesSessionSandbox path traversal attacks, session ID sanitization, audit record escapes.
3. Invalid payloads, un-serializable objects, state corruption, deserialization tampering, and schema boundary violations.
"""

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from pydantic import ValidationError

from src.orchestrator.state_machine import (
    ProductionState,
    ProductionStateMachine,
    StateTransitionError,
    TransitionRecord,
)
from src.models.contracts import (
    CreatorProfile,
    ContentBrief,
    ResearchPlan,
    SourceRecord,
    ClaimRecord,
    TalkingPointRecord,
    StatisticRecord,
    ResearchDossier,
    EditorialAngle,
    ContentOutline,
    ScriptBeat,
    ScriptScene,
    Script,
    AssetRequirement,
    AssetRecord,
    EvaluationLayer,
    EvaluationReport,
    RenderArtifact,
    PublishPackage,
    AnalyticsSnapshot,
    LearningCandidate,
)
from adapters.hermes.sandbox import HermesSessionSandbox
from adapters.hermes.bridge import HermesBridge
from adapters.hermes.tools import handle_tool_call, check_harness9_available


class TestM1AdversarialStateMachine(unittest.TestCase):
    """Adversarial challenge tests for the 17-state deterministic state machine."""

    def test_adv_01_exhaustive_400_transition_pairs(self):
        """Exhaustively probe all 20x20 = 400 state combinations to verify transition matrix enforcement."""
        all_states = list(ProductionState)
        self.assertEqual(len(all_states), 20)  # 17 canonical + 3 control states

        for from_state in all_states:
            for to_state in all_states:
                sm = ProductionStateMachine(
                    run_id=f"test_{from_state.value}_to_{to_state.value}",
                    initial_state=from_state,
                )
                allowed_targets = ProductionStateMachine.VALID_TRANSITIONS.get(from_state, set())
                is_allowed = to_state in allowed_targets

                self.assertEqual(
                    sm.can_transition(to_state),
                    is_allowed,
                    f"Mismatch in can_transition for {from_state.value} -> {to_state.value}",
                )

                if is_allowed:
                    result = sm.transition_to(to_state)
                    self.assertEqual(result, to_state)
                    self.assertEqual(sm.current_state, to_state)
                    self.assertEqual(len(sm.history), 1)
                else:
                    # Must raise StateTransitionError
                    with self.assertRaises(
                        StateTransitionError,
                        msg=f"Expected StateTransitionError for forbidden transition {from_state.value} -> {to_state.value}",
                    ):
                        sm.transition_to(to_state)
                    
                    # State and history must remain strictly pristine after rejected transition
                    self.assertEqual(sm.current_state, from_state)
                    self.assertEqual(len(sm.history), 0)

    def test_adv_02_terminal_state_lockdown(self):
        """Verify terminal states COMPLETED and CANCELLED cannot transition to ANY state."""
        terminal_states = [ProductionState.COMPLETED, ProductionState.CANCELLED]
        all_states = list(ProductionState)

        for term_state in terminal_states:
            sm = ProductionStateMachine(run_id="term_lockdown", initial_state=term_state)
            self.assertTrue(sm.is_terminal())

            for target in all_states:
                self.assertFalse(
                    sm.can_transition(target),
                    f"Terminal state {term_state.value} allowed transition to {target.value}",
                )
                with self.assertRaises(StateTransitionError):
                    sm.transition_to(target)
                self.assertEqual(sm.current_state, term_state)
                self.assertEqual(len(sm.history), 0)

    def test_adv_03_invalid_backward_and_skip_jumps(self):
        """Verify explicit illegal jump scenarios are rejected deterministically."""
        sm = ProductionStateMachine(run_id="jump_probe")

        # Skip jumps from CREATED
        illegal_from_created = [
            ProductionState.COMPLETED,
            ProductionState.RENDER_COMPLETED,
            ProductionState.SCRIPT_COMPLETED,
            ProductionState.EDITORIAL_ANALYSIS,
            ProductionState.ASSETS_FROZEN,
        ]
        for target in illegal_from_created:
            with self.assertRaises(StateTransitionError):
                sm.transition_to(target)
            self.assertEqual(sm.current_state, ProductionState.CREATED)

        # Advance to ASSETS_FROZEN
        sm.transition_to(ProductionState.RESEARCH_PLANNED)
        sm.transition_to(ProductionState.RESEARCH_IN_PROGRESS)
        sm.transition_to(ProductionState.RESEARCH_COMPLETED)
        sm.transition_to(ProductionState.EDITORIAL_ANALYSIS)
        sm.transition_to(ProductionState.ANGLE_SELECTED)
        sm.transition_to(ProductionState.OUTLINE_APPROVED)
        sm.transition_to(ProductionState.SCRIPTING_IN_PROGRESS)
        sm.transition_to(ProductionState.SCRIPT_COMPLETED)
        sm.transition_to(ProductionState.VOICE_GENERATED)
        sm.transition_to(ProductionState.VOICE_QA_PASSED)
        sm.transition_to(ProductionState.ASSETS_DISCOVERED)
        sm.transition_to(ProductionState.ASSETS_FROZEN)

        # Illegal backward jumps from ASSETS_FROZEN
        illegal_from_assets_frozen = [
            ProductionState.CREATED,
            ProductionState.RESEARCH_PLANNED,
            ProductionState.EDITORIAL_ANALYSIS,
            ProductionState.OUTLINE_APPROVED,
            ProductionState.SCRIPT_COMPLETED,
            ProductionState.COMPLETED,
        ]
        for target in illegal_from_assets_frozen:
            with self.assertRaises(StateTransitionError):
                sm.transition_to(target)
            self.assertEqual(sm.current_state, ProductionState.ASSETS_FROZEN)

    def test_adv_04_stress_legal_cycles_and_high_iteration_loop(self):
        """Stress-test legal loopback cycles across 100 iterations without memory degradation or corruption."""
        sm = ProductionStateMachine(run_id="cycle_stress_run")
        sm.transition_to(ProductionState.RESEARCH_PLANNED)

        # 50 cycles of RESEARCH_PLANNED <-> RESEARCH_IN_PROGRESS
        for i in range(50):
            sm.transition_to(
                ProductionState.RESEARCH_IN_PROGRESS,
                payload={"iteration": i, "attempt": "in_progress"},
            )
            sm.transition_to(
                ProductionState.RESEARCH_PLANNED,
                payload={"iteration": i, "attempt": "retry"},
            )

        self.assertEqual(sm.current_state, ProductionState.RESEARCH_PLANNED)
        self.assertEqual(len(sm.history), 1 + 100)

        # Advance to SCRIPTING_IN_PROGRESS
        sm.transition_to(ProductionState.RESEARCH_IN_PROGRESS)
        sm.transition_to(ProductionState.RESEARCH_COMPLETED)
        sm.transition_to(ProductionState.EDITORIAL_ANALYSIS)
        sm.transition_to(ProductionState.ANGLE_SELECTED)
        sm.transition_to(ProductionState.OUTLINE_APPROVED)
        sm.transition_to(ProductionState.SCRIPTING_IN_PROGRESS)

        # 50 cycles of SCRIPTING_IN_PROGRESS <-> SCRIPT_COMPLETED
        for i in range(50):
            sm.transition_to(ProductionState.SCRIPT_COMPLETED, payload={"draft_version": i})
            sm.transition_to(ProductionState.SCRIPTING_IN_PROGRESS, payload={"revision": i})

        self.assertEqual(sm.current_state, ProductionState.SCRIPTING_IN_PROGRESS)
        self.assertEqual(len(sm.history), 101 + 6 + 100)

        # Verify serialization and round-trip of high-iteration history
        dumped = sm.to_dict()
        self.assertEqual(len(dumped["history"]), len(sm.history))
        restored = ProductionStateMachine.from_dict(dumped)
        self.assertEqual(restored.current_state, ProductionState.SCRIPTING_IN_PROGRESS)
        self.assertEqual(len(restored.history), len(sm.history))

    def test_adv_05_malformed_state_types_and_injections(self):
        """Verify invalid data types and malicious strings raise StateTransitionError."""
        sm = ProductionStateMachine(run_id="injection_test")

        invalid_targets = [
            None,
            123,
            0,
            True,
            False,
            [],
            {},
            "NON_EXISTENT_STATE",
            "CREATED; DROP TABLE sessions; --",
            " created ",
            "CREATED\n",
            "\x00CREATED",
        ]

        for inv in invalid_targets:
            with self.assertRaises(
                StateTransitionError,
                msg=f"Expected StateTransitionError for invalid target: {inv!r}",
            ):
                sm.transition_to(inv)
            self.assertEqual(sm.current_state, ProductionState.CREATED)


class TestM1AdversarialHermesSandbox(unittest.TestCase):
    """Adversarial challenge tests for HermesSessionSandbox path traversal and isolation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_adv_06_session_id_path_traversal_sanitization(self):
        """Verify malicious session IDs cannot escape the base directory via path traversal characters."""
        malicious_session_ids = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "../../../secret_escape",
            "/root/escape",
            "C:\\Windows\\System32",
            "session/subfolder/test",
            "session\\subfolder\\test",
            "session\x00_null_byte",
            "   ",
            "",
            None,
        ]

        for mal_id in malicious_session_ids:
            sandbox = HermesSessionSandbox(session_id=mal_id, base_dir=self.base_dir)
            session_root = sandbox.get_session_root()

            # The resolved session root MUST be within base_dir
            try:
                session_root.resolve().relative_to(self.base_dir.resolve())
            except ValueError:
                self.fail(f"Sandbox escaped base_dir for session_id {mal_id!r}: {session_root}")

            # Directories must be created safely inside base_dir
            self.assertTrue(sandbox.get_workspace_dir().exists())
            self.assertTrue(sandbox.get_renders_dir().exists())
            self.assertTrue(sandbox.get_audit_dir().exists())

    def test_adv_07_validate_path_jail_escape_attempts(self):
        """Verify validate_path strictly rejects all sandbox escape attempts."""
        sandbox = HermesSessionSandbox(session_id="secure_session_01", base_dir=self.base_dir)

        # Valid subpaths
        valid_targets = [
            sandbox.get_workspace_dir() / "temp.txt",
            sandbox.get_renders_dir() / "final.mp4",
            sandbox.get_audit_dir() / "log.json",
            sandbox.get_session_root() / "custom_sub" / "file.dat",
        ]
        for vt in valid_targets:
            res = sandbox.validate_path(vt)
            self.assertEqual(res, vt.resolve())

        # Jail escape attempts
        outside_targets = [
            self.base_dir / ".." / "outside.txt",
            self.base_dir.parent,
            Path("C:/Windows/System32"),
            Path("/etc/passwd"),
            sandbox.get_workspace_dir() / ".." / ".." / "escape.txt",
            sandbox.get_session_root() / ".." / "other_session" / "secret.txt",
        ]
        for ot in outside_targets:
            with self.assertRaises(
                ValueError,
                msg=f"Expected ValueError for sandbox escape: {ot}",
            ):
                sandbox.validate_path(ot)

    def test_adv_08_save_audit_record_path_traversal(self):
        """Verify save_audit_record cannot write outside the audit directory via record_name traversal."""
        sandbox = HermesSessionSandbox(session_id="audit_sec_session", base_dir=self.base_dir)
        
        # Test path traversal in record_name
        evil_names = [
            "../../escape_audit",
            "..\\..\\escape_audit_win",
            "../../../evil",
        ]
        for name in evil_names:
            target = sandbox.audit_dir / f"{name}.json"
            resolved = target.resolve()
            # If save_audit_record allows writing, verify whether it writes inside audit_dir or escapes
            try:
                sandbox.save_audit_record(name, {"malicious": True})
                # Check if it escaped audit_dir
                try:
                    resolved.relative_to(sandbox.audit_dir.resolve())
                except ValueError:
                    self.fail(f"save_audit_record wrote outside audit directory: {resolved}")
            except (ValueError, OSError):
                # Raising error is also secure behavior
                pass

    def test_adv_09_cleanup_scratch_isolation(self):
        """Verify cleanup_scratch deletes workspace files only and preserves renders, audit, and sister files."""
        sandbox = HermesSessionSandbox(session_id="cleanup_test_session", base_dir=self.base_dir)

        # Create files in workspace, renders, and audit
        scratch_file = sandbox.get_workspace_dir() / "scratch.tmp"
        scratch_file.write_text("temp", encoding="utf-8")

        scratch_subdir = sandbox.get_workspace_dir() / "subdir"
        scratch_subdir.mkdir()
        (scratch_subdir / "subfile.tmp").write_text("sub temp", encoding="utf-8")

        render_file = sandbox.get_renders_dir() / "final.mp4"
        render_file.write_text("fake video bytes", encoding="utf-8")

        audit_file = sandbox.get_audit_dir() / "state.json"
        audit_file.write_text("{}", encoding="utf-8")

        # Cleanup scratch
        sandbox.cleanup_scratch()

        # Workspace items must be deleted
        self.assertFalse(scratch_file.exists())
        self.assertFalse(scratch_subdir.exists())
        self.assertTrue(sandbox.get_workspace_dir().exists())

        # Renders and audit MUST be preserved
        self.assertTrue(render_file.exists())
        self.assertTrue(audit_file.exists())

    def test_adv_10_concurrent_or_multiple_session_sandboxes(self):
        """Verify multiple simultaneous session sandboxes maintain complete isolation."""
        sessions = [f"session_iso_{i}" for i in range(5)]
        sandboxes = [HermesSessionSandbox(session_id=s, base_dir=self.base_dir) for s in sessions]

        # Write unique data in each session
        for i, sb in enumerate(sandboxes):
            sb.save_audit_record(f"log_{i}", {"session_index": i})
            (sb.get_renders_dir() / f"video_{i}.mp4").write_text(f"vid_{i}", encoding="utf-8")

        # Check each sandbox has strictly its own files
        for i, sb in enumerate(sandboxes):
            records = sb.get_audit_records()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["session_index"], i)

            renders = sb.list_render_artifacts()
            self.assertEqual(len(renders), 1)
            self.assertIn(f"video_{i}.mp4", renders[0].name)


class TestM1AdversarialPayloadsAndCorruption(unittest.TestCase):
    """Adversarial tests for payload resilience, serialization tampering, and schema boundary violations."""

    def test_adv_11_state_machine_unusual_and_corrupt_payloads(self):
        """Verify state machine gracefully handles non-serializable, complex, and unhashable payloads."""
        sm = ProductionStateMachine(run_id="payload_stress")

        # Payload 1: Function / callable
        sm.transition_to(
            ProductionState.RESEARCH_PLANNED,
            payload=lambda x: x ** 2,
        )
        self.assertEqual(sm.current_state, ProductionState.RESEARCH_PLANNED)

        # Payload 2: Module object
        sm.transition_to(
            ProductionState.RESEARCH_IN_PROGRESS,
            payload=unittest,
        )
        self.assertEqual(sm.current_state, ProductionState.RESEARCH_IN_PROGRESS)

        # Payload 3: Complex numbers and nested structures
        sm.transition_to(
            ProductionState.RESEARCH_COMPLETED,
            payload={"complex_val": complex(1, 2), "nested": {"list": [1, 2, 3]}},
        )
        self.assertEqual(sm.current_state, ProductionState.RESEARCH_COMPLETED)

        # State machine should still serialize cleanly to dict and JSON
        d = sm.to_dict()
        self.assertEqual(d["current_state"], "RESEARCH_COMPLETED")
        self.assertEqual(len(d["history"]), 3)

        json_str = sm.to_json()
        self.assertIsInstance(json_str, str)
        restored = ProductionStateMachine.from_json(json_str)
        self.assertEqual(restored.current_state, ProductionState.RESEARCH_COMPLETED)

    def test_adv_12_state_machine_deserialization_corruption(self):
        """Verify deserialization handles corrupted or tampered state payloads safely."""
        # 1. Missing current_state defaults to CREATED or raises gracefully
        sm1 = ProductionStateMachine.from_dict({"run_id": "r1"})
        self.assertEqual(sm1.current_state, ProductionState.CREATED)

        # 2. Unknown current_state raises ValueError
        with self.assertRaises((ValueError, KeyError)):
            ProductionStateMachine.from_dict({"current_state": "INVALID_BOGUS_STATE"})

        # 3. Invalid JSON string
        with self.assertRaises(json.JSONDecodeError):
            ProductionStateMachine.from_json("{broken json string...")

    def test_adv_13_pydantic_contracts_boundary_and_fuzzing(self):
        """Verify boundary conditions and invalid values across production schemas."""
        # ContentBrief boundary tests
        with self.assertRaises(ValidationError):
            # Duration below min (5)
            ContentBrief(project_id="p1", topic="T", target_duration_seconds=4)

        with self.assertRaises(ValidationError):
            # Duration above max (600)
            ContentBrief(project_id="p1", topic="T", target_duration_seconds=601)

        with self.assertRaises(ValidationError):
            # Invalid aspect ratio
            ContentBrief(project_id="p1", topic="T", aspect_ratio="4:3")

        with self.assertRaises(ValidationError):
            # Empty project_id
            ContentBrief(project_id="", topic="T")

        # SourceRecord reliability score boundary
        with self.assertRaises(ValidationError):
            SourceRecord(title="T", url="http://example.com", reliability_score=-0.1)

        with self.assertRaises(ValidationError):
            SourceRecord(title="T", url="http://example.com", reliability_score=1.01)

        # EvaluationReport score boundary
        with self.assertRaises(ValidationError):
            EvaluationReport(
                run_id="eval_01",
                layer=EvaluationLayer.RESEARCH,
                scores={"test": 1.05},
                composite_score=1.05,
            )

        # Unicode, emojis, and special characters serialization
        unicode_brief = ContentBrief(
            project_id="proj_unicode_🚀",
            topic="量子コンピューティング & 🤖 AI Revolution (Überblick)",
            target_duration_seconds=60,
            custom_instructions="✨ Special symbols: <script>alert('xss')</script> & ñ, é, ö, 語",
        )
        json_out = unicode_brief.to_json()
        restored = ContentBrief.from_json(json_out)
        self.assertEqual(restored.topic, "量子コンピューティング & 🤖 AI Revolution (Überblick)")
        self.assertIn("alert('xss')", restored.custom_instructions)

        yaml_out = unicode_brief.to_yaml()
        restored_yaml = ContentBrief.from_yaml(yaml_out)
        self.assertEqual(restored_yaml.topic, unicode_brief.topic)

    def test_adv_14_hermes_tool_dispatcher_malformed_arguments(self):
        """Verify handle_tool_call handles malformed, missing, and unexpected arguments without unhandled exceptions."""
        temp_dir = tempfile.TemporaryDirectory()
        bridge = HermesBridge(base_output_dir=temp_dir.name)

        # 1. Unknown tool
        res1 = handle_tool_call("malicious_tool_call", {}, "session_001", bridge=bridge)
        self.assertFalse(res1["success"])
        self.assertIn("Unknown tool", res1["error"])

        # 2. Inspect session that doesn't exist
        res2 = handle_tool_call(
            "inspect_production_state",
            {"session_id": "non_existent_session_xyz"},
            "session_001",
            bridge=bridge,
        )
        self.assertEqual(res2["current_state"], "UNKNOWN")
        self.assertEqual(res2["render_count"], 0)

        # 3. Evaluate session that has no renders
        res3 = handle_tool_call(
            "evaluate_content_quality",
            {"session_id": "empty_session_xyz"},
            "session_001",
            bridge=bridge,
        )
        self.assertFalse(res3["passed"])
        self.assertEqual(res3["composite_score"], 0.0)

        temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
