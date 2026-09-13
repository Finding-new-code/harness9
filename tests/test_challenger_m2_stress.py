"""tests/test_challenger_m2_stress.py

Adversarial Stress and Boundary Verification Suite for Milestone 2
(HermesCapabilityBridge and H9 Content Production Model Tools).

Empirical challenger harness designed to test:
1. Missing, empty, and malformed payloads for all 4 H9 tools
2. Type corruptions, NoneType injections, and invalid boundaries
3. Exception containment: ensuring tool handlers return tool_error JSON rather than leaking tracebacks
4. Concurrency and thread safety under simultaneous multi-session access
5. Extreme data sizes, unicode/control chars, and non-existent/invalid filesystem paths
"""

import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from typing import Any, Dict, List

from src.h9_runtime import (
    HermesCapabilityBridge,
    get_capability_bridge,
    reset_capability_bridges,
)
from src.h9_runtime.types import ProductionIR
from src.models.contracts import (
    CreatorProfile,
    EditorialAngle,
    LearningCandidate,
    ResearchDossier,
    Script,
)
from tools.h9_content_tools import (
    handle_h9_discover_assets,
    handle_h9_generate_script,
    handle_h9_render,
    handle_h9_research,
)
from tools.registry import registry, set_h9_available


class TestH9ResearchBoundaryStress(unittest.TestCase):
    """Stress tests and boundary condition validation for h9.research."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()
        set_h9_available(True)

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_01_missing_and_empty_topic(self):
        """Verify error encapsulation when topic is missing, None, empty, or whitespace."""
        test_cases = [
            {},
            {"topic": None},
            {"topic": ""},
            {"topic": "   "},
            {"topic": "\t\n  "},
        ]
        for payload in test_cases:
            res = handle_h9_research(payload)
            data = json.loads(res)
            self.assertIn("error", data, f"Expected error for payload {payload}")
            self.assertIn("topic", data["error"].lower())

    def test_02_non_dict_and_non_string_topic(self):
        """Verify non-dict payload and non-string topic types return clean tool_error."""
        for invalid in [None, "string", 12345, [1, 2, 3], True]:
            res = handle_h9_research(invalid)  # type: ignore
            data = json.loads(res)
            self.assertIn("error", data)

        for non_str_topic in [12345, [1, 2], {"key": "val"}, True]:
            res = handle_h9_research({"topic": non_str_topic})
            data = json.loads(res)
            self.assertIn("error", data)

    def test_03_invalid_and_corrupted_depths(self):
        """Verify arbitrary or invalid depth values safely fall back to standard without crashing."""
        for bad_depth in ["extreme", "shallow", "UNKNOWN", "", 1234, None, [], {}]:
            res = handle_h9_research({"topic": "Quantum Computing", "depth": bad_depth})
            data = json.loads(res)
            self.assertNotIn("error", data)
            self.assertIn("claims", data)

    def test_04_malformed_constraints(self):
        """Verify malformed constraints types are caught cleanly."""
        res = handle_h9_research({"topic": "Transistors", "constraints": "not-a-dict"})
        data = json.loads(res)
        self.assertIn("error", data)

        res = handle_h9_research({"topic": "Transistors", "constraints": [1, 2, 3]})
        data = json.loads(res)
        self.assertIn("error", data)

    def test_05_corrupted_constraints_fields(self):
        """Verify non-numeric target_duration in constraints returns tool_error instead of crashing."""
        res = handle_h9_research(
            {"topic": "Transistors", "constraints": {"target_duration": "not-a-number"}}
        )
        data = json.loads(res)
        self.assertIn("error", data)

    def test_06_extreme_topic_payload(self):
        """Verify research handles large strings, unicode, and control characters gracefully."""
        huge_topic = "Superconducting Qubits " * 200
        res = handle_h9_research({"topic": huge_topic})
        data = json.loads(res)
        self.assertNotIn("error", data)
        self.assertIn("claims", data)

        special_topic = "Transistor History: <script>alert('xss')</script> \u2603 \U0001F680"
        res = handle_h9_research({"topic": special_topic})
        data = json.loads(res)
        self.assertNotIn("error", data)


class TestH9DiscoverAssetsBoundaryStress(unittest.TestCase):
    """Stress tests and boundary condition validation for h9.discover_assets."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()
        set_h9_available(True)

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_07_empty_payload(self):
        """Verify empty payload yields 0 assets without crashing."""
        res = handle_h9_discover_assets({})
        data = json.loads(res)
        self.assertNotIn("error", data)
        self.assertEqual(data["total_assets"], 0)
        self.assertEqual(data["assets"], [])

    def test_08_invalid_argument_types(self):
        """Verify non-dict payload or invalid field types return tool_error."""
        for invalid in ["not a dict", 123, None, [1, 2]]:
            res = handle_h9_discover_assets(invalid)  # type: ignore
            data = json.loads(res)
            self.assertIn("error", data)

        res = handle_h9_discover_assets({"requirements": "not a list"})
        data = json.loads(res)
        self.assertIn("error", data)

        res = handle_h9_discover_assets({"scene_ids": "not a list"})
        data = json.loads(res)
        self.assertIn("error", data)

        res = handle_h9_discover_assets({"dossier": "not a dict"})
        data = json.loads(res)
        self.assertIn("error", data)

    def test_09_corrupted_requirements_elements(self):
        """Verify requirements list containing non-dict or empty elements is handled safely."""
        reqs = [
            None,
            {},
            "raw string query",
            123,
            {"visual_query": "Valid query"},
        ]
        res = handle_h9_discover_assets({"requirements": reqs})
        data = json.loads(res)
        self.assertNotIn("error", data)
        self.assertEqual(data["total_assets"], 5)

    def test_10_dossier_with_none_queries(self):
        """Verify dossier with suggested_visual_queries=None does not crash."""
        res = handle_h9_discover_assets(
            {"dossier": {"topic": "AI", "suggested_visual_queries": None}}
        )
        data = json.loads(res)
        # Should either produce assets or handle error cleanly without unhandled crash
        self.assertIsInstance(data, dict)

    def test_11_unusual_aspect_ratios(self):
        """Verify unusual aspect ratio values still produce valid dimension calculations."""
        for aspect in ["9:16", "1:1", "4:3", "invalid_aspect"]:
            res = handle_h9_discover_assets(
                {"scene_ids": ["scene_01"], "format_aspect": aspect}
            )
            data = json.loads(res)
            self.assertNotIn("error", data)
            self.assertEqual(len(data["assets"]), 1)


class TestH9GenerateScriptBoundaryStress(unittest.TestCase):
    """Stress tests and boundary condition validation for h9.generate_script."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()
        set_h9_available(True)

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_12_missing_or_empty_dossier(self):
        """Verify missing or non-dict dossier returns tool_error."""
        test_cases = [
            {},
            {"dossier": None},
            {"dossier": ""},
            {"dossier": []},
            {"dossier": 123},
        ]
        for payload in test_cases:
            res = handle_h9_generate_script(payload)
            data = json.loads(res)
            self.assertIn("error", data)

    def test_13_corrupted_outline_and_creator_types(self):
        """Verify invalid outline or creator types return tool_error."""
        dossier = {"topic": "Semiconductors"}
        res = handle_h9_generate_script({"dossier": dossier, "outline": "not a dict"})
        data = json.loads(res)
        self.assertIn("error", data)

        res = handle_h9_generate_script({"dossier": dossier, "creator": [1, 2]})
        data = json.loads(res)
        self.assertIn("error", data)

    def test_14_unhandled_target_duration_type_error(self):
        """Test whether target_duration handles invalid types cleanly or raises an unhandled exception."""
        dossier = {"topic": "Computing"}
        
        # Test string value for target_duration
        try:
            res = handle_h9_generate_script({"dossier": dossier, "target_duration": "not-a-number"})
            data = json.loads(res)
            # If handled cleanly, error should be returned in JSON
            self.assertIn("error", data)
        except (ValueError, TypeError) as exc:
            # If this exception is unhandled, we record it as an empirical finding
            self.fail(f"CRITICAL: Unhandled exception leaked in handle_h9_generate_script: {type(exc).__name__}: {exc}")

        # Test None value for target_duration
        try:
            res = handle_h9_generate_script({"dossier": dossier, "target_duration": None})
            data = json.loads(res)
            self.assertIn("error", data)
        except (ValueError, TypeError) as exc:
            self.fail(f"CRITICAL: Unhandled exception leaked in handle_h9_generate_script: {type(exc).__name__}: {exc}")

    def test_15_corrupted_claims_in_dossier(self):
        """Verify dossier with malformed claims returns tool_error cleanly."""
        dossier_with_bad_claims = {
            "topic": "AI",
            "claims": ["string claim", None, 123],
        }
        res = handle_h9_generate_script({"dossier": dossier_with_bad_claims})
        data = json.loads(res)
        # Should return an error dict, not raise uncaught exception
        self.assertIn("error", data)

    def test_16_empty_topic_in_dossier(self):
        """Verify dossier with missing or empty topic returns tool_error cleanly."""
        dossier_empty_topic = {"topic": "", "claims": []}
        res = handle_h9_generate_script({"dossier": dossier_empty_topic})
        data = json.loads(res)
        self.assertIn("error", data)


class TestH9RenderBoundaryStress(unittest.TestCase):
    """Stress tests and boundary condition validation for h9.render."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()
        set_h9_available(True)

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_17_missing_required_render_parameters(self):
        """Verify missing production_ir or output_dir returns tool_error."""
        for payload in [
            {},
            {"production_ir": None, "output_dir": str(self.workspace)},
            {"production_ir": {}, "output_dir": str(self.workspace)},
            {"production_ir": {"project_id": "p1"}},
            {"production_ir": {"project_id": "p1"}, "output_dir": None},
            {"production_ir": {"project_id": "p1"}, "output_dir": ""},
            {"production_ir": {"project_id": "p1"}, "output_dir": "   "},
        ]:
            res = handle_h9_render(payload)
            data = json.loads(res)
            self.assertIn("error", data)

    def test_18_corrupted_production_ir_types(self):
        """Verify malformed duration_seconds or fps in production_ir is handled cleanly."""
        out_dir = self.workspace / "renders"
        
        # Test non-float duration_seconds
        res = handle_h9_render(
            {
                "production_ir": {
                    "project_id": "p1",
                    "duration_seconds": "not-a-float",
                },
                "output_dir": str(out_dir),
            }
        )
        data = json.loads(res)
        self.assertIn("error", data)

        # Test non-int fps
        res = handle_h9_render(
            {
                "production_ir": {
                    "project_id": "p1",
                    "fps": "not-an-int",
                },
                "output_dir": str(out_dir),
            }
        )
        data = json.loads(res)
        self.assertIn("error", data)

    def test_19_nonexistent_and_nested_output_dir(self):
        """Verify rendering into deeply nested non-existent directory succeeds."""
        deep_dir = self.workspace / "a" / "b" / "c" / "deep_renders"
        prod_ir = {"project_id": "deep_p", "duration_seconds": 10.0}
        res = handle_h9_render(
            {"production_ir": prod_ir, "output_dir": str(deep_dir)}
        )
        data = json.loads(res)
        self.assertNotIn("error", data)
        self.assertTrue(Path(data["video_path"]).exists())

    def test_20_output_dir_is_existing_file(self):
        """Verify rendering where output_dir points to an existing file returns tool_error."""
        file_path = self.workspace / "some_file.txt"
        file_path.write_text("dummy", encoding="utf-8")
        prod_ir = {"project_id": "collision_test", "duration_seconds": 5.0}
        res = handle_h9_render(
            {"production_ir": prod_ir, "output_dir": str(file_path)}
        )
        data = json.loads(res)
        self.assertIn("error", data)


class TestConcurrencyAndBridgeStress(unittest.TestCase):
    """Concurrency, thread-safety, and repeated invocation stress tests."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()
        set_h9_available(True)

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_21_concurrent_bridge_instantiation(self):
        """Verify concurrent threads requesting bridge instances for same and distinct sessions."""
        def get_bridge(sid: str):
            b = get_capability_bridge(sid, workspace_root=self.workspace / sid)
            return b.session_id

        session_ids = [f"session_{i % 5}" for i in range(30)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(get_bridge, session_ids))

        self.assertEqual(len(results), 30)
        for i, sid in enumerate(session_ids):
            self.assertEqual(results[i], sid)

    def test_22_concurrent_tool_dispatch(self):
        """Verify concurrent registry dispatches across multiple threads."""
        def run_research(idx: int):
            topic = f"Concurrency Test Topic {idx}"
            return registry.dispatch("h9.research", {"topic": topic, "depth": "overview"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(run_research, i) for i in range(12)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), 12)
        for r in results:
            data = json.loads(r)
            self.assertNotIn("error", data)
            self.assertIn("claims", data)

    def test_23_repeated_rapid_dispatches(self):
        """Verify rapid repeated dispatches do not exhaust handles or fail state."""
        for i in range(15):
            res = registry.dispatch(
                "h9.discover_assets",
                {"scene_ids": [f"rapid_scene_{i:02d}"], "format_aspect": "16:9"},
            )
            data = json.loads(res)
            self.assertNotIn("error", data)
            self.assertEqual(len(data["assets"]), 1)

    def test_24_bridge_direct_boundary_resilience(self):
        """Verify direct bridge method calls with boundary parameters."""
        bridge = HermesCapabilityBridge(
            session_id="boundary_bridge", workspace_root=self.workspace
        )

        # Sandboxed command with timeout and empty command
        code, stdout, stderr = bridge.run_sandboxed_command("echo Hello")
        self.assertEqual(code, 0)
        self.assertIn("Hello", stdout)

        # Creator memory with non-existent creator
        mem = bridge.query_creator_memory("non_existent_creator_999", query="test")
        self.assertEqual(mem["creator_id"], "non_existent_creator_999")
        self.assertEqual(mem["profile"], {})

        # Subagent delegation with zero iterations
        sub = bridge.delegate_subagent_task(
            goal="Test subagent", role="researcher", max_iterations=1, timeout_sec=10.0
        )
        self.assertEqual(sub["status"], "COMPLETED")

    def test_25_bridge_discover_assets_none_queries_direct(self):
        """Verify whether bridge.discover_assets directly crashes on suggested_visual_queries=None."""
        bridge = HermesCapabilityBridge(session_id="bridge_assets_test", workspace_root=self.workspace)
        try:
            records = bridge.discover_assets(dossier={"suggested_visual_queries": None})
            self.assertIsInstance(records, list)
        except TypeError as exc:
            self.fail(f"CRITICAL: bridge.discover_assets crashed with unhandled TypeError: {exc}")

    def test_26_bridge_generate_script_claims_direct(self):
        """Verify whether bridge.generate_script directly crashes when claims is None or corrupted."""
        bridge = HermesCapabilityBridge(session_id="bridge_script_test", workspace_root=self.workspace)
        try:
            script = bridge.generate_script(
                angle={},
                dossier={"topic": "Direct Bridge Test", "claims": None},
            )
            self.assertIsInstance(script, Script)
        except (TypeError, AttributeError) as exc:
            self.fail(f"CRITICAL: bridge.generate_script crashed with unhandled exception: {exc}")



if __name__ == "__main__":
    unittest.main()
