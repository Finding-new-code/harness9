"""Unit tests for Harness 9 Hermes Adapter & Session Sandbox (Milestone M1)."""

import json
from pathlib import Path
import tempfile
import unittest

from adapters.hermes.sandbox import HermesSessionSandbox
from adapters.hermes.bridge import HermesBridge
from adapters.hermes.tools import (
    check_harness9_available,
    get_tool_schemas,
    get_harness9_toolsets,
    handle_tool_call,
    TOOL_GENERATE_VIDEO,
    TOOL_INSPECT_STATE,
    TOOL_EVALUATE_QUALITY,
)


class TestHermesAdapter(unittest.TestCase):
    """Test suite for Hermes adapter sandbox, bridge, tool schemas, and tool execution."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -----------------------------------------------------------------------
    # 1. HermesSessionSandbox Tests
    # -----------------------------------------------------------------------
    def test_01_sandbox_directory_creation_and_isolation(self):
        """Verify session sandbox creates isolated workspace, renders, and audit dirs."""
        sandbox = HermesSessionSandbox(session_id="session_alpha_01", base_dir=self.base_dir)
        
        self.assertEqual(sandbox.session_id, "session_alpha_01")
        self.assertTrue(sandbox.get_workspace_dir().exists())
        self.assertTrue(sandbox.get_renders_dir().exists())
        self.assertTrue(sandbox.get_audit_dir().exists())

    def test_02_sandbox_path_traversal_guard(self):
        """Verify validate_path rejects paths outside the session root."""
        sandbox = HermesSessionSandbox(session_id="session_sec_01", base_dir=self.base_dir)
        
        # Valid path within sandbox
        valid_path = sandbox.get_workspace_dir() / "test.txt"
        validated = sandbox.validate_path(valid_path)
        self.assertEqual(validated, valid_path.resolve())

        # Path escaping sandbox
        outside_path = self.base_dir / ".." / "unauthorized.txt"
        with self.assertRaises(ValueError):
            sandbox.validate_path(outside_path)

    def test_03_sandbox_audit_records_and_scratch_cleanup(self):
        """Verify saving audit records and cleaning up workspace scratch files."""
        sandbox = HermesSessionSandbox(session_id="session_clean_01", base_dir=self.base_dir)
        
        # Create a scratch file in workspace
        scratch = sandbox.get_workspace_dir() / "scratch.tmp"
        scratch.write_text("temporary data", encoding="utf-8")
        
        # Save audit record
        saved = sandbox.save_audit_record("test_log", {"key": "val"})
        self.assertTrue(saved.exists())
        
        records = sandbox.get_audit_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["key"], "val")

        # Cleanup scratch
        sandbox.cleanup_scratch()
        self.assertFalse(scratch.exists())
        self.assertTrue(sandbox.get_workspace_dir().exists())
        self.assertTrue(saved.exists())

    # -----------------------------------------------------------------------
    # 2. Tool Schemas & Service Gates
    # -----------------------------------------------------------------------
    def test_04_tool_schemas_and_service_gate(self):
        """Verify service-gated tool definitions conform to OpenAI / Hermes tool specs."""
        self.assertTrue(check_harness9_available())
        
        schemas = get_tool_schemas()
        self.assertEqual(len(schemas), 3)

        tool_names = [s["function"]["name"] for s in schemas]
        self.assertIn("generate_video_from_brief", tool_names)
        self.assertIn("inspect_production_state", tool_names)
        self.assertIn("evaluate_content_quality", tool_names)

        # Check required fields for generate_video_from_brief
        gen_tool = next(s for s in schemas if s["function"]["name"] == "generate_video_from_brief")
        props = gen_tool["function"]["parameters"]["properties"]
        self.assertIn("topic", props)
        self.assertIn("format", props)
        self.assertIn("duration", props)
        self.assertIn("offline", props)
        self.assertEqual(gen_tool["function"]["parameters"]["required"], ["topic"])

        # Check toolset definition
        toolset = get_harness9_toolsets()
        self.assertEqual(toolset["name"], "harness9_video")
        self.assertTrue(toolset["check_fn"]())
        self.assertEqual(len(toolset["tools"]), 3)

    # -----------------------------------------------------------------------
    # 3. HermesBridge & Tool Dispatching
    # -----------------------------------------------------------------------
    def test_05_bridge_run_production_and_state_machine(self):
        """Verify end-to-end bridge execution with 17-state lifecycle tracking."""
        bridge = HermesBridge(base_output_dir=self.base_dir)
        
        result = bridge.run_production(
            session_id="bridge_session_01",
            topic="The History of the Transistor",
            format="16:9",
            duration=5,
            offline=True,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["session_id"], "bridge_session_01")
        self.assertEqual(result["state"], "COMPLETED")
        self.assertIn("video_path", result)
        self.assertGreater(len(result["state_history"]), 10)

        # Verify inspection
        inspection = bridge.inspect_session("bridge_session_01")
        self.assertEqual(inspection["current_state"], "COMPLETED")
        self.assertGreaterEqual(inspection["render_count"], 1)

        # Verify evaluation
        evaluation = bridge.evaluate_session("bridge_session_01")
        self.assertTrue(evaluation["passed"])
        self.assertGreater(evaluation["composite_score"], 0.8)

    def test_06_handle_tool_call_dispatcher(self):
        """Verify handle_tool_call routes tool calls and returns structured responses."""
        bridge = HermesBridge(base_output_dir=self.base_dir)
        
        # 1. generate_video_from_brief
        res = handle_tool_call(
            tool_name="generate_video_from_brief",
            arguments={
                "topic": "The History of the Transistor",
                "format": "16:9",
                "duration": 5,
                "offline": True,
            },
            session_id="dispatcher_session_01",
            bridge=bridge,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], "COMPLETED")

        # 2. inspect_production_state
        res_inspect = handle_tool_call(
            tool_name="inspect_production_state",
            arguments={"session_id": "dispatcher_session_01"},
            session_id="dispatcher_session_01",
            bridge=bridge,
        )
        self.assertEqual(res_inspect["current_state"], "COMPLETED")

        # 3. evaluate_content_quality
        res_eval = handle_tool_call(
            tool_name="evaluate_content_quality",
            arguments={"session_id": "dispatcher_session_01"},
            session_id="dispatcher_session_01",
            bridge=bridge,
        )
        self.assertTrue(res_eval["passed"])

        # 4. Unknown tool call handling
        res_unknown = handle_tool_call(
            tool_name="non_existent_tool",
            arguments={},
            session_id="dispatcher_session_01",
            bridge=bridge,
        )
        self.assertFalse(res_unknown["success"])
        self.assertIn("Unknown tool", res_unknown["error"])


if __name__ == "__main__":
    unittest.main()
