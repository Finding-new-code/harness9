"""Unit tests for Harness 9 17-State Lifecycle State Machine (Milestone M1)."""

import json
import unittest
from datetime import datetime

from src.orchestrator.state_machine import (
    ProductionState,
    ProductionStateMachine,
    StateTransitionError,
    TransitionRecord,
    StateTransitionRecord,
)


class TestProductionStateMachine(unittest.TestCase):
    """Test suite covering the 17 canonical states, transition graph, jump rejections, and audit history."""

    def test_01_canonical_17_states_exist(self):
        """Verify that all 17 canonical lifecycle states are defined with exact names."""
        canonical_states = ProductionState.canonical_states()
        self.assertEqual(len(canonical_states), 17)

        expected_names = [
            "CREATED",
            "RESEARCH_PLANNED",
            "RESEARCH_IN_PROGRESS",
            "RESEARCH_COMPLETED",
            "EDITORIAL_ANALYSIS",
            "ANGLE_SELECTED",
            "OUTLINE_APPROVED",
            "SCRIPTING_IN_PROGRESS",
            "SCRIPT_COMPLETED",
            "VOICE_GENERATED",
            "VOICE_QA_PASSED",
            "ASSETS_DISCOVERED",
            "ASSETS_FROZEN",
            "COMPOSITION_GENERATED",
            "RENDER_IN_PROGRESS",
            "RENDER_COMPLETED",
            "COMPLETED",
        ]

        for idx, expected in enumerate(expected_names):
            state = canonical_states[idx]
            self.assertEqual(state.value, expected)
            self.assertEqual(state.name, expected)

    def test_02_initial_state_and_properties(self):
        """Verify initial state machine properties and defaults."""
        sm = ProductionStateMachine(run_id="run_test_001")
        self.assertEqual(sm.run_id, "run_test_001")
        self.assertEqual(sm.current_state, ProductionState.CREATED)
        self.assertEqual(len(sm.history), 0)
        self.assertFalse(sm.is_terminal())
        self.assertFalse(sm.is_completed())
        self.assertFalse(sm.is_failed())

    def test_03_valid_sequential_lifecycle_transitions(self):
        """Verify complete, deterministic sequential traversal across all 17 states."""
        sm = ProductionStateMachine(run_id="run_seq_001")
        canonical = ProductionState.canonical_states()

        for next_state in canonical[1:]:
            self.assertTrue(
                sm.can_transition(next_state),
                f"Expected to be able to transition from {sm.current_state} to {next_state}",
            )
            self.assertTrue(
                sm.can_transition_to(next_state.value),
                f"Expected can_transition_to string alias to work for {next_state}",
            )
            result = sm.transition_to(
                next_state,
                payload={"step": next_state.value},
                duration_ms=10.5,
            )
            self.assertEqual(result, next_state)
            self.assertEqual(sm.current_state, next_state)

        self.assertEqual(sm.current_state, ProductionState.COMPLETED)
        self.assertTrue(sm.is_completed())
        self.assertTrue(sm.is_terminal())
        self.assertEqual(len(sm.history), 16)

    def test_04_rejection_of_invalid_state_jumps(self):
        """Verify that skipping intermediary states raises StateTransitionError (subclass of ValueError)."""
        sm = ProductionStateMachine(run_id="run_jump_test")

        # Attempt to jump from CREATED directly to COMPLETED
        self.assertFalse(sm.can_transition(ProductionState.COMPLETED))
        with self.assertRaises(StateTransitionError):
            sm.transition_to(ProductionState.COMPLETED)
        
        # Verify ValueError is also caught since StateTransitionError is a ValueError
        with self.assertRaises(ValueError):
            sm.transition_to(ProductionState.RENDER_COMPLETED)

        # Advance to RESEARCH_PLANNED
        sm.transition_to(ProductionState.RESEARCH_PLANNED)

        # Attempt to jump to SCRIPT_COMPLETED
        self.assertFalse(sm.can_transition(ProductionState.SCRIPT_COMPLETED))
        with self.assertRaises(StateTransitionError):
            sm.transition_to(ProductionState.SCRIPT_COMPLETED)

    def test_05_unknown_state_transition_rejection(self):
        """Verify attempting to transition to an invalid/non-existent state raises StateTransitionError."""
        sm = ProductionStateMachine(run_id="run_unknown_test")
        with self.assertRaises(StateTransitionError):
            sm.transition_to("NON_EXISTENT_STATE_XYZ")

    def test_06_error_and_cancellation_states(self):
        """Verify transitioning to FAILED and CANCELLED states and reset recovery."""
        sm = ProductionStateMachine(run_id="run_fail_test")
        sm.transition_to(ProductionState.RESEARCH_PLANNED)
        sm.transition_to(ProductionState.RESEARCH_IN_PROGRESS)

        # Fail during research
        sm.transition_to(
            ProductionState.FAILED,
            payload={"error": "Network timeout connecting to provider"},
        )
        self.assertEqual(sm.current_state, ProductionState.FAILED)
        self.assertTrue(sm.is_failed())

        # FAILED allows reset back to CREATED
        self.assertTrue(sm.can_transition(ProductionState.CREATED))
        sm.transition_to(ProductionState.CREATED)
        self.assertEqual(sm.current_state, ProductionState.CREATED)

    def test_07_pause_for_human_review_and_resume(self):
        """Verify PAUSED_FOR_HUMAN state transitions at editorial checkpoints."""
        sm = ProductionStateMachine(run_id="run_pause_test")
        sm.transition_to(ProductionState.RESEARCH_PLANNED)
        sm.transition_to(ProductionState.RESEARCH_IN_PROGRESS)
        sm.transition_to(ProductionState.RESEARCH_COMPLETED)
        sm.transition_to(ProductionState.EDITORIAL_ANALYSIS)
        sm.transition_to(ProductionState.ANGLE_SELECTED)

        # Pause for human angle approval
        self.assertTrue(sm.can_transition(ProductionState.PAUSED_FOR_HUMAN))
        sm.transition_to(
            ProductionState.PAUSED_FOR_HUMAN,
            payload={"review_type": "editorial_angle_approval"},
        )
        self.assertEqual(sm.current_state, ProductionState.PAUSED_FOR_HUMAN)

        # Human approves -> proceed to OUTLINE_APPROVED
        self.assertTrue(sm.can_transition(ProductionState.OUTLINE_APPROVED))
        sm.transition_to(ProductionState.OUTLINE_APPROVED)
        self.assertEqual(sm.current_state, ProductionState.OUTLINE_APPROVED)

    def test_08_loopback_and_retry_transitions(self):
        """Verify valid loop-back transitions when QA gates or re-evaluations occur."""
        sm = ProductionStateMachine(run_id="run_retry_test")
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

        # Suppose asset discovery fails, retry voice or script
        self.assertTrue(sm.can_transition(ProductionState.VOICE_GENERATED))
        sm.transition_to(
            ProductionState.VOICE_GENERATED,
            payload={"reason": "Regenerating narration with modified pacing"},
        )
        self.assertEqual(sm.current_state, ProductionState.VOICE_GENERATED)

    def test_09_audit_log_and_transition_records(self):
        """Verify transition history and audit log structure."""
        sm = ProductionStateMachine(run_id="run_audit_test")
        sm.transition_to(
            ProductionState.RESEARCH_PLANNED,
            payload={"query_count": 5},
            metadata={"operator": "worker_m1"},
            duration_ms=45.2,
        )

        history = sm.get_history()
        self.assertEqual(len(history), 1)
        record = history[0]
        self.assertEqual(record.from_state, ProductionState.CREATED)
        self.assertEqual(record.to_state, ProductionState.RESEARCH_PLANNED)
        self.assertEqual(record.duration_ms, 45.2)
        self.assertEqual(record.metadata["operator"], "worker_m1")
        self.assertEqual(record.payload_summary["query_count"], 5)

        audit_log = sm.get_audit_log()
        self.assertEqual(len(audit_log), 1)
        self.assertIn("from_state", audit_log[0])
        self.assertEqual(audit_log[0]["from_state"], "CREATED")
        self.assertEqual(audit_log[0]["to_state"], "RESEARCH_PLANNED")

    def test_10_serialization_and_restoration(self):
        """Verify serialization to and from dictionary and JSON."""
        sm = ProductionStateMachine(run_id="run_serial_test")
        sm.transition_to(ProductionState.RESEARCH_PLANNED, payload={"test": 123})
        sm.transition_to(ProductionState.RESEARCH_IN_PROGRESS, payload={"progress": 50})

        data = sm.to_dict()
        self.assertEqual(data["run_id"], "run_serial_test")
        self.assertEqual(data["current_state"], "RESEARCH_IN_PROGRESS")
        self.assertEqual(len(data["history"]), 2)

        # Restore from dict
        restored = ProductionStateMachine.from_dict(data)
        self.assertEqual(restored.run_id, "run_serial_test")
        self.assertEqual(restored.current_state, ProductionState.RESEARCH_IN_PROGRESS)
        self.assertEqual(len(restored.history), 2)

        # JSON serialization
        json_str = sm.to_json()
        restored_json = ProductionStateMachine.from_json(json_str)
        self.assertEqual(restored_json.current_state, ProductionState.RESEARCH_IN_PROGRESS)
        self.assertEqual(restored_json.run_id, "run_serial_test")


if __name__ == "__main__":
    unittest.main()
