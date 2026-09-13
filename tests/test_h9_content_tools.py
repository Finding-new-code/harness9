"""Comprehensive test suite for Harness 9 Content Tools & HermesCapabilityBridge (Milestone M2).

Tests:
1. Tool registration & OpenAI schema validity for all 4 tools & aliases
2. Service gating via check_h9_available() (active vs inactive / Rung 3 Footprint Ladder)
3. Genuine execution & error handling for h9.research, h9.discover_assets, h9.generate_script, h9.render
4. Registry dispatch boundary & error encapsulation
5. HermesCapabilityBridge protocol conformance across all 7 runtime protocols
6. Bridge domain integration methods (subagents, model capability, memory, sandboxed commands)
"""

import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from typing import Dict, Any

from src.h9_runtime import (
    AgentRuntime,
    ContentRuntime,
    ExecutionRuntime,
    HermesCapabilityBridge,
    MemoryRuntime,
    ModelRuntime,
    SkillRuntime,
    ToolRuntime,
    get_capability_bridge,
    reset_capability_bridges,
)
from src.h9_runtime.types import (
    CapabilityRole,
    ProductionIR,
    SubagentStatus,
    ToolInvocationContext,
)
from src.models.contracts import (
    CreatorProfile,
    LearningCandidate,
    ResearchDossier,
    Script,
)
from tools.h9_content_tools import (
    H9_DISCOVER_ASSETS_SCHEMA,
    H9_GENERATE_SCRIPT_SCHEMA,
    H9_RENDER_SCHEMA,
    H9_RESEARCH_SCHEMA,
    handle_h9_discover_assets,
    handle_h9_generate_script,
    handle_h9_render,
    handle_h9_research,
)
from tools.registry import (
    check_h9_available,
    invalidate_check_fn_cache,
    registry,
    set_h9_available,
)


class TestH9ToolRegistrationAndSchemas(unittest.TestCase):
    """Verify tool registration into Hermes registry and schema compliance."""

    def test_01_tool_registration(self):
        """Verify all 4 canonical tools and snake_case aliases are registered in h9_content."""
        expected_tools = {
            "h9.research",
            "h9_research",
            "h9.discover_assets",
            "h9_discover_assets",
            "h9.generate_script",
            "h9_generate_script",
            "h9.render",
            "h9_render",
        }
        registered_tools = set(registry.get_tool_names_for_toolset("h9_content"))
        for tool in expected_tools:
            self.assertIn(
                tool,
                registered_tools,
                f"Expected tool '{tool}' to be registered under toolset 'h9_content'",
            )

    def test_02_schema_validity(self):
        """Verify parameter schemas follow standard OpenAI function schema contracts."""
        schemas = [
            ("h9.research", H9_RESEARCH_SCHEMA),
            ("h9.discover_assets", H9_DISCOVER_ASSETS_SCHEMA),
            ("h9.generate_script", H9_GENERATE_SCRIPT_SCHEMA),
            ("h9.render", H9_RENDER_SCHEMA),
        ]
        for name, schema in schemas:
            self.assertEqual(schema["name"], name)
            self.assertIn("description", schema)
            self.assertGreater(len(schema["description"]), 10)
            self.assertIn("parameters", schema)
            params = schema["parameters"]
            self.assertEqual(params["type"], "object")
            self.assertIn("properties", params)
            self.assertIsInstance(params["properties"], dict)
            self.assertIn("required", params)
            self.assertIsInstance(params["required"], list)

    def test_03_research_schema_properties(self):
        """Verify h9.research schema specifically requires topic and defines depth & constraints."""
        props = H9_RESEARCH_SCHEMA["parameters"]["properties"]
        self.assertIn("topic", props)
        self.assertIn("depth", props)
        self.assertIn("constraints", props)
        self.assertEqual(props["topic"]["type"], "string")
        self.assertEqual(props["depth"]["type"], "string")
        self.assertIn("overview", props["depth"]["enum"])
        self.assertIn("standard", props["depth"]["enum"])
        self.assertIn("deep", props["depth"]["enum"])
        self.assertIn("topic", H9_RESEARCH_SCHEMA["parameters"]["required"])

    def test_04_render_schema_properties(self):
        """Verify h9.render schema requires production_ir and output_dir."""
        props = H9_RENDER_SCHEMA["parameters"]["properties"]
        self.assertIn("production_ir", props)
        self.assertIn("output_dir", props)
        self.assertEqual(props["production_ir"]["type"], "object")
        self.assertEqual(props["output_dir"]["type"], "string")
        self.assertIn("production_ir", H9_RENDER_SCHEMA["parameters"]["required"])
        self.assertIn("output_dir", H9_RENDER_SCHEMA["parameters"]["required"])


class TestH9GatingBehavior(unittest.TestCase):
    """Verify service gating via check_h9_available() conforming to Footprint Ladder Rung 3."""

    def setUp(self):
        invalidate_check_fn_cache()
        set_h9_available(None)

    def tearDown(self):
        invalidate_check_fn_cache()
        set_h9_available(None)

    def test_05_check_h9_available_default(self):
        """Default environment with src.h9_runtime installed reports available."""
        self.assertTrue(check_h9_available())

    def test_06_gating_active_definitions(self):
        """When H9 is active, get_definitions returns full schemas."""
        set_h9_available(True)
        self.assertTrue(check_h9_available())
        tool_names = {"h9.research", "h9.discover_assets", "h9.generate_script", "h9.render"}
        defs = registry.get_definitions(tool_names)
        self.assertEqual(len(defs), 4)
        names = {d["function"]["name"] for d in defs}
        self.assertEqual(names, tool_names)

    def test_07_gating_inactive_zero_overhead(self):
        """When H9 is inactive, get_definitions returns 0 schemas (0 core token overhead)."""
        set_h9_available(False)
        self.assertFalse(check_h9_available())
        tool_names = {"h9.research", "h9.discover_assets", "h9.generate_script", "h9.render"}
        defs = registry.get_definitions(tool_names)
        self.assertEqual(
            len(defs),
            0,
            "Gated tools must yield 0 schemas when check_fn evaluates False (Rung 3 compliance)",
        )

    def test_08_gating_reactivation(self):
        """Toggling availability dynamically updates schema definitions correctly."""
        set_h9_available(False)
        defs_off = registry.get_definitions({"h9.research"})
        self.assertEqual(len(defs_off), 0)

        set_h9_available(True)
        defs_on = registry.get_definitions({"h9.research"})
        self.assertEqual(len(defs_on), 1)
        self.assertEqual(defs_on[0]["function"]["name"], "h9.research")

    def test_09_env_var_gating(self):
        """Environment variable H9_ENABLED controls check_h9_available when override is None."""
        set_h9_available(None)
        old_env = os.environ.get("H9_ENABLED")
        try:
            os.environ["H9_ENABLED"] = "0"
            invalidate_check_fn_cache()
            self.assertFalse(check_h9_available())

            os.environ["H9_ENABLED"] = "1"
            invalidate_check_fn_cache()
            self.assertTrue(check_h9_available())
        finally:
            if old_env is not None:
                os.environ["H9_ENABLED"] = old_env
            else:
                os.environ.pop("H9_ENABLED", None)
            invalidate_check_fn_cache()


class TestH9ResearchTool(unittest.TestCase):
    """Verify h9.research execution, claim extraction, and parameter handling."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_10_research_standard_happy_path(self):
        """Execute h9.research on a technical topic with standard depth."""
        args = {"topic": "The Invention of the Transistor", "depth": "standard"}
        result_str = handle_h9_research(args, session_id="test_res_01")
        self.assertIsInstance(result_str, str)
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertIn("topic", data)
        self.assertEqual(data["topic"], "The Invention of the Transistor")
        self.assertIn("claims", data)
        self.assertGreaterEqual(len(data["claims"]), 1)
        self.assertIn("key_takeaways", data)

    def test_11_research_overview_depth(self):
        """Execute h9.research with overview depth producing concise findings."""
        args = {"topic": "GPU Parallel Computing", "depth": "overview"}
        result_str = handle_h9_research(args, session_id="test_res_02")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertEqual(data["topic"], "GPU Parallel Computing")

    def test_12_research_deep_depth(self):
        """Execute h9.research with deep depth."""
        args = {
            "topic": "Quantum Computing",
            "depth": "deep",
            "constraints": {"target_duration": 60, "offline": True},
        }
        result_str = handle_h9_research(args, session_id="test_res_03")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertEqual(data["topic"], "Quantum Computing")

    def test_13_research_missing_topic_error(self):
        """Execute h9.research with missing topic returns error JSON."""
        result_str = handle_h9_research({})
        data = json.loads(result_str)
        self.assertIn("error", data)
        self.assertIn("topic", data["error"].lower())

    def test_14_research_invalid_args_error(self):
        """Execute h9.research with non-dict args returns error JSON."""
        result_str = handle_h9_research("not a dict")  # type: ignore
        data = json.loads(result_str)
        self.assertIn("error", data)

    def test_15_research_dispatch_via_registry(self):
        """Dispatch h9.research and alias h9_research through registry.dispatch."""
        res1 = registry.dispatch("h9.research", {"topic": "Transistors"})
        data1 = json.loads(res1)
        self.assertNotIn("error", data1)
        self.assertEqual(data1["topic"], "Transistors")

        res2 = registry.dispatch("h9_research", {"topic": "Microprocessors"})
        data2 = json.loads(res2)
        self.assertNotIn("error", data2)
        self.assertEqual(data2["topic"], "Microprocessors")


class TestH9DiscoverAssetsTool(unittest.TestCase):
    """Verify h9.discover_assets execution, procedural vector generation, and asset records."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_16_discover_assets_with_requirements(self):
        """Discover and generate genuine vector assets for explicit requirements."""
        reqs = [
            {
                "requirement_id": "req_01",
                "scene_id": "scene_01",
                "visual_query": "Germanium crystal semiconductor point contact",
            },
            {
                "requirement_id": "req_02",
                "scene_id": "scene_02",
                "visual_query": "Microprocessor circuit timeline evolution",
            },
        ]
        args = {"requirements": reqs, "format_aspect": "16:9"}
        result_str = handle_h9_discover_assets(args, session_id="test_assets_01")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertIn("assets", data)
        assets = data["assets"]
        self.assertEqual(len(assets), 2)

        for asset in assets:
            self.assertIn("asset_id", asset)
            self.assertIn("local_path", asset)
            self.assertIn("file_sha256", asset)
            self.assertIn("dimensions", asset)
            self.assertEqual(asset["verification_status"], "VERIFIED")
            self.assertEqual(asset["dimensions"]["aspect_ratio"], "16:9")

            # Check that physical asset was written to disk
            if "absolute_path" in asset and asset["absolute_path"]:
                asset_file = Path(asset["absolute_path"])
                self.assertTrue(
                    asset_file.exists(),
                    f"Asset file {asset_file} must exist on disk",
                )
                self.assertGreater(asset_file.stat().st_size, 0)

    def test_17_discover_assets_with_scene_ids(self):
        """Discover assets mapped to specific scene IDs."""
        args = {"scene_ids": ["scene_intro", "scene_mechanism", "scene_climax"]}
        result_str = handle_h9_discover_assets(args, session_id="test_assets_02")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        assets = data["assets"]
        self.assertEqual(len(assets), 3)
        scene_targets = {a["scene_target"] for a in assets}
        self.assertEqual(scene_targets, {"scene_intro", "scene_mechanism", "scene_climax"})

    def test_18_discover_assets_with_dossier(self):
        """Discover assets matching suggested visual queries in a ResearchDossier."""
        dossier = {
            "topic": "History of Silicon",
            "suggested_visual_queries": [
                "silicon crystal boule ingot",
                "wafer slicing semiconductor",
            ],
        }
        args = {"dossier": dossier}
        result_str = handle_h9_discover_assets(args, session_id="test_assets_03")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertGreaterEqual(len(data["assets"]), 2)

    def test_19_discover_assets_invalid_args_error(self):
        """Passing invalid parameter types returns error JSON."""
        result_str = handle_h9_discover_assets({"requirements": "not a list"})
        data = json.loads(result_str)
        self.assertIn("error", data)

    def test_20_discover_assets_dispatch_via_registry(self):
        """Dispatch h9.discover_assets and h9_discover_assets through registry."""
        res1 = registry.dispatch(
            "h9.discover_assets",
            {"scene_ids": ["scene_01"]},
        )
        data1 = json.loads(res1)
        self.assertNotIn("error", data1)
        self.assertEqual(len(data1["assets"]), 1)

        res2 = registry.dispatch(
            "h9_discover_assets",
            {"scene_ids": ["scene_01", "scene_02"]},
        )
        data2 = json.loads(res2)
        self.assertNotIn("error", data2)
        self.assertEqual(len(data2["assets"]), 2)


class TestH9GenerateScriptTool(unittest.TestCase):
    """Verify h9.generate_script execution, editorial processing, and script structure."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_21_generate_script_happy_path(self):
        """Generate structured script from verified dossier and outline."""
        dossier = {
            "topic": "The Transistor Revolution",
            "headline": "How Three Bell Labs Physicists Changed the World",
            "key_takeaways": [
                "Replaced fragile vacuum tubes with solid-state devices",
                "Enabled modern microelectronics and smartphones",
            ],
            "claims": [
                {
                    "claim_id": "c1",
                    "claim_text": "Demonstrated December 23, 1947.",
                    "confidence_score": 0.98,
                }
            ],
        }
        outline = {
            "angle_archetype": "deep_dive",
            "title": "Solid State: The Spark of Modern Computing",
        }
        args = {
            "dossier": dossier,
            "outline": outline,
            "target_duration": 30.0,
            "format_aspect": "16:9",
        }
        result_str = handle_h9_generate_script(args, session_id="test_script_01")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertEqual(data["topic"], "The Transistor Revolution")
        self.assertEqual(data["title"], "Solid State: The Spark of Modern Computing")
        self.assertIn("scenes", data)
        self.assertEqual(len(data["scenes"]), 4)
        for scene in data["scenes"]:
            self.assertIn("scene_id", scene)
            self.assertIn("duration", scene)
            self.assertIn("narration_text", scene)
            self.assertIn("beats", scene)

    def test_22_generate_script_with_creator_dna(self):
        """Generate script incorporating Creator DNA rules and tone."""
        dossier = {
            "topic": "Artificial Intelligence",
            "key_takeaways": ["Neural networks enable pattern recognition"],
        }
        creator = {
            "creator_id": "creator_tech_explainer",
            "tone": "authoritative",
            "negative_rules": ["No clickbait hyperbole", "No sensational claims"],
        }
        args = {"dossier": dossier, "creator": creator, "target_duration": 20.0}
        result_str = handle_h9_generate_script(args, session_id="test_script_02")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertEqual(data["total_duration"], 20.0)

    def test_23_generate_script_missing_dossier_error(self):
        """Generate script without dossier returns error JSON."""
        result_str = handle_h9_generate_script({})
        data = json.loads(result_str)
        self.assertIn("error", data)
        self.assertIn("dossier", data["error"].lower())

    def test_24_generate_script_dispatch_via_registry(self):
        """Dispatch h9.generate_script and h9_generate_script through registry."""
        dossier = {"topic": "Semiconductors", "key_takeaways": ["Silicon is a group 14 element"]}
        res1 = registry.dispatch("h9.generate_script", {"dossier": dossier})
        data1 = json.loads(res1)
        self.assertNotIn("error", data1)
        self.assertEqual(data1["topic"], "Semiconductors")

        res2 = registry.dispatch("h9_generate_script", {"dossier": dossier})
        data2 = json.loads(res2)
        self.assertNotIn("error", data2)
        self.assertEqual(data2["topic"], "Semiconductors")


class TestH9RenderTool(unittest.TestCase):
    """Verify h9.render execution, MP4 rendering, and artifact verification."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_25_render_happy_path(self):
        """Render broadcast MP4 from valid Production IR AST."""
        out_dir = self.base_dir / "renders_01"
        prod_ir = {
            "project_id": "test_render_proj",
            "aspect_ratio": "16:9",
            "duration_seconds": 15.0,
            "fps": 30,
            "timeline_blocks": [
                {"scene_id": "scene_01", "duration": 7.5, "component_type": "split_screen_intro"},
                {"scene_id": "scene_02", "duration": 7.5, "component_type": "timeline_reveal"},
            ],
            "audio_tracks": [{"track_id": "narration", "duration": 15.0}],
            "css_variables": {"--accent": "#00d2ff"},
        }
        args = {"production_ir": prod_ir, "output_dir": str(out_dir)}
        result_str = handle_h9_render(args, session_id="test_render_01")
        data = json.loads(result_str)
        self.assertNotIn("error", data)
        self.assertIn("video_path", data)
        self.assertEqual(data["duration_seconds"], 15.0)
        self.assertEqual(data["width"], 1920)
        self.assertEqual(data["height"], 1080)
        self.assertEqual(data["fps"], 30)

        # Confirm physical MP4 file was rendered to disk
        video_file = Path(data["video_path"])
        self.assertTrue(video_file.exists(), "Rendered MP4 file must exist on disk")
        self.assertGreater(video_file.stat().st_size, 0, "Rendered MP4 file must be non-empty")

    def test_26_render_missing_ir_error(self):
        """Render without production_ir returns error JSON."""
        result_str = handle_h9_render({"output_dir": "renders"})
        data = json.loads(result_str)
        self.assertIn("error", data)
        self.assertIn("production_ir", data["error"].lower())

    def test_27_render_missing_output_dir_error(self):
        """Render without output_dir returns error JSON."""
        result_str = handle_h9_render({"production_ir": {"project_id": "p1"}})
        data = json.loads(result_str)
        self.assertIn("error", data)
        self.assertIn("output_dir", data["error"].lower())

    def test_28_render_dispatch_via_registry(self):
        """Dispatch h9.render and h9_render through registry."""
        out_dir = self.base_dir / "renders_02"
        prod_ir = {"project_id": "p1", "duration_seconds": 10.0}
        res1 = registry.dispatch("h9.render", {"production_ir": prod_ir, "output_dir": str(out_dir)})
        data1 = json.loads(res1)
        self.assertNotIn("error", data1)
        self.assertTrue(Path(data1["video_path"]).exists())

        out_dir2 = self.base_dir / "renders_03"
        res2 = registry.dispatch("h9_render", {"production_ir": prod_ir, "output_dir": str(out_dir2)})
        data2 = json.loads(res2)
        self.assertNotIn("error", data2)
        self.assertTrue(Path(data2["video_path"]).exists())


class TestHermesCapabilityBridge(unittest.TestCase):
    """Verify HermesCapabilityBridge protocol conformance and domain methods."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_29_bridge_protocol_conformance(self):
        """Verify HermesCapabilityBridge satisfies all 7 runtime protocols."""
        bridge = HermesCapabilityBridge(session_id="test_proto_01", workspace_root=self.workspace)
        self.assertIsInstance(bridge, AgentRuntime)
        self.assertIsInstance(bridge, SkillRuntime)
        self.assertIsInstance(bridge, ToolRuntime)
        self.assertIsInstance(bridge, ModelRuntime)
        self.assertIsInstance(bridge, MemoryRuntime)
        self.assertIsInstance(bridge, ExecutionRuntime)
        self.assertIsInstance(bridge, ContentRuntime)

    def test_30_bridge_model_completion(self):
        """Request model completion through bridge by capability role."""
        bridge = HermesCapabilityBridge(session_id="test_model_01", workspace_root=self.workspace)
        resp = bridge.request_model_completion(
            role="fast_editorial",
            prompt="Outline candidate angles for quantum computing.",
        )
        self.assertIsInstance(resp, str)
        self.assertGreater(len(resp), 10)

    def test_31_bridge_creator_memory_flow(self):
        """Verify saving and querying creator brand DNA via bridge."""
        bridge = HermesCapabilityBridge(session_id="test_mem_01", workspace_root=self.workspace)
        profile = CreatorProfile(
            creator_id="creator_dr_nova",
            display_name="Dr. Nova Explains",
            tone_of_voice=["Authoritative", "Curious"],
            target_audiences=["Physicists", "Engineers"],
            negative_rules=["No pseudo-science", "Cite primary journals"],
        )
        bridge.save_creator_profile(profile)

        # Query creator memory
        mem = bridge.query_creator_memory("creator_dr_nova", query="rules")
        self.assertEqual(mem["creator_id"], "creator_dr_nova")
        self.assertEqual(mem["profile"]["display_name"], "Dr. Nova Explains")
        self.assertIn("Dr. Nova Explains", mem["system_prompt_block"])

        # Record learning candidate
        lc = LearningCandidate(
            lesson_id="lc_01",
            creator_id="creator_dr_nova",
            rule_type="negative_constraint",
            observation="Hook duration > 5s caused 20% drop-off",
            recommended_action="Keep reference collage hook under 3.5s",
        )
        bridge.record_learning_candidate(lc)


    def test_32_bridge_subagent_delegation(self):
        """Delegate subagent research task through bridge."""
        bridge = HermesCapabilityBridge(session_id="test_sub_01", workspace_root=self.workspace)
        sub_res = bridge.delegate_subagent_task(
            goal="Research point contact transistor origins",
            role="researcher",
            context={"topic": "Transistors"},
        )
        self.assertEqual(sub_res["status"], "COMPLETED")
        self.assertIn("subagent_id", sub_res)
        self.assertIn("dossier_summary", sub_res["structured_data"])

    def test_33_bridge_sandboxed_command(self):
        """Execute sandboxed command through bridge."""
        bridge = HermesCapabilityBridge(session_id="test_sand_01", workspace_root=self.workspace)
        exit_code, stdout, stderr = bridge.run_sandboxed_command("echo 'Hermes Sandbox Active'")
        self.assertEqual(exit_code, 0)
        self.assertIn("Hermes Sandbox Active", stdout)

    def test_34_bridge_factory_and_reset(self):
        """Verify singleton factory get_capability_bridge and reset_capability_bridges."""
        b1 = get_capability_bridge("session_alpha")
        b2 = get_capability_bridge("session_alpha")
        self.assertIs(b1, b2, "Same session ID must return identical bridge instance")

        b3 = get_capability_bridge("session_beta")
        self.assertIsNot(b1, b3, "Different session IDs must return separate bridge instances")

        reset_capability_bridges()
        b4 = get_capability_bridge("session_alpha")
        self.assertIsNot(b1, b4, "Factory must create fresh instance after reset")


if __name__ == "__main__":
    unittest.main()
