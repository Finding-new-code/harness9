"""tests/test_adversarial_m2_tools.py

Adversarial stress-testing suite for Harness 9 Milestone M2 (Hermes Capability Bridge & Tools).
Author: challenger_2_m2_orch3 (Empirical Challenger)

Stress Test Categories:
1. Dynamic toggling of set_h9_available(False) and set_h9_available(True) across threads/calls.
2. Zero leakage of H9 tools in get_definitions() and get_tool_definitions() when inactive.
3. Prompt cache preservation: Byte-identical schema generation across 1,000+ repeated calls.
4. Tool registry idempotent re-registration under concurrency and serial hammering.
5. Handler resilience, boundary defense, cross-toolset shadowing rejection, and session isolation.
"""

from __future__ import annotations

import concurrent.futures
import copy
import hashlib
import json
import logging
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock
from typing import Any, Dict, List, Set, Tuple

from model_tools import get_tool_definitions
from src.h9_runtime import (
    HermesCapabilityBridge,
    get_capability_bridge,
    reset_capability_bridges,
)
from src.h9_runtime.types import ProductionIR, ToolInvocationContext
from src.models.contracts import (
    CreatorProfile,
    EditorialAngle,
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
    register_tools,
)
from tools.registry import (
    ToolRegistry,
    check_h9_available,
    invalidate_check_fn_cache,
    registry,
    set_h9_available,
)

logger = logging.getLogger(__name__)

ALL_H9_TOOL_NAMES = {
    "h9.research",
    "h9_research",
    "h9.discover_assets",
    "h9_discover_assets",
    "h9.generate_script",
    "h9_generate_script",
    "h9.render",
    "h9_render",
}

CANONICAL_H9_TOOL_NAMES = {
    "h9.research",
    "h9.discover_assets",
    "h9.generate_script",
    "h9.render",
}


class TestAdversarialGatingDynamicToggling(unittest.TestCase):
    """Stress-test dynamic toggling of set_h9_available across threads and calls."""

    def setUp(self):
        set_h9_available(None)
        invalidate_check_fn_cache()

    def tearDown(self):
        set_h9_available(None)
        invalidate_check_fn_cache()

    def test_rapid_sequential_toggling_100_cycles(self):
        """Rapidly toggle set_h9_available across 100 cycles and verify strict gating."""
        for cycle in range(100):
            # Phase 1: Disable
            set_h9_available(False)
            self.assertFalse(check_h9_available(), f"Cycle {cycle}: check_h9_available must be False")
            defs_inactive = registry.get_definitions(ALL_H9_TOOL_NAMES)
            self.assertEqual(
                len(defs_inactive),
                0,
                f"Cycle {cycle}: get_definitions leaked tools when inactive! Count: {len(defs_inactive)}",
            )

            # Phase 2: Enable
            set_h9_available(True)
            self.assertTrue(check_h9_available(), f"Cycle {cycle}: check_h9_available must be True")
            defs_active = registry.get_definitions(ALL_H9_TOOL_NAMES)
            self.assertEqual(
                len(defs_active),
                8,
                f"Cycle {cycle}: get_definitions failed to return all 8 tools when active! Count: {len(defs_active)}",
            )

    def test_multithreaded_concurrent_toggling_and_queries(self):
        """Stress-test concurrent calls to get_definitions() during background toggle churn."""
        stop_event = threading.Event()
        errors: List[str] = []

        def toggler():
            state = False
            while not stop_event.is_set():
                state = not state
                set_h9_available(state)
                time.sleep(0.001)

        def reader(worker_id: int):
            for _ in range(50):
                if stop_event.is_set():
                    break
                try:
                    defs = registry.get_definitions(ALL_H9_TOOL_NAMES, quiet=True)
                    count = len(defs)
                    if count not in (0, 8):
                        errors.append(f"Reader {worker_id} saw illegal intermediate count: {count}")
                except Exception as exc:
                    errors.append(f"Reader {worker_id} encountered exception: {exc}")
                time.sleep(0.002)

        toggler_threads = [threading.Thread(target=toggler) for _ in range(2)]
        reader_threads = [threading.Thread(target=reader, args=(i,)) for i in range(8)]

        for t in toggler_threads + reader_threads:
            t.start()

        for r in reader_threads:
            r.join()

        stop_event.set()
        for t in toggler_threads:
            t.join()

        self.assertEqual(errors, [], f"Encountered concurrency errors during toggling: {errors}")

    def test_env_var_toggling_matrix(self):
        """Verify environment variable transitions immediately reflect without stale TTL lock-in."""
        truthy_values = ["1", "true", "True", "yes", "YES", "enabled", "ENABLED"]
        falsy_values = ["0", "false", "False", "no", "disabled", "DISABLED"]

        for val in truthy_values:
            with mock.patch.dict(os.environ, {"H9_ENABLED": val}):
                invalidate_check_fn_cache()
                self.assertTrue(
                    check_h9_available(),
                    f"Env H9_ENABLED='{val}' should evaluate to available",
                )
                defs = registry.get_definitions(CANONICAL_H9_TOOL_NAMES)
                self.assertEqual(len(defs), 4)

        for val in falsy_values:
            with mock.patch.dict(os.environ, {"H9_ENABLED": val}):
                invalidate_check_fn_cache()
                self.assertFalse(
                    check_h9_available(),
                    f"Env H9_ENABLED='{val}' should evaluate to unavailable",
                )
                defs = registry.get_definitions(CANONICAL_H9_TOOL_NAMES)
                self.assertEqual(len(defs), 0)

        # Empty string / unset falls back to package import auto-detection (True when src.h9_runtime present)
        with mock.patch.dict(os.environ, {"H9_ENABLED": ""}):
            invalidate_check_fn_cache()
            self.assertTrue(check_h9_available())

    def test_grace_period_bypassed_on_explicit_disable(self):
        """Verify _CHECK_FN_FAILURE_GRACE_SECONDS does not preserve tools when explicitly disabled."""
        set_h9_available(True)
        self.assertTrue(check_h9_available())
        defs_before = registry.get_definitions(ALL_H9_TOOL_NAMES)
        self.assertEqual(len(defs_before), 8)

        set_h9_available(False)
        self.assertFalse(check_h9_available())

        defs_after = registry.get_definitions(ALL_H9_TOOL_NAMES)
        self.assertEqual(
            len(defs_after),
            0,
            "Tools were retained after set_h9_available(False) — grace period cache leakage!",
        )


class TestAdversarialLeakageWhenInactive(unittest.TestCase):
    """Stress-test zero-leakage guarantee when H9 is inactive across all query paths."""

    def setUp(self):
        set_h9_available(False)
        invalidate_check_fn_cache()

    def tearDown(self):
        set_h9_available(None)
        invalidate_check_fn_cache()

    def test_get_definitions_explicit_h9_names_leakage(self):
        """Querying registry.get_definitions with explicit H9 names returns empty list."""
        defs = registry.get_definitions(ALL_H9_TOOL_NAMES)
        self.assertEqual(defs, [])

    def test_get_definitions_wildcard_all_tools_leakage(self):
        """Querying registry.get_definitions with ALL tool names in registry leaks NO H9 tools."""
        all_tools = set(registry.get_all_tool_names())
        defs = registry.get_definitions(all_tools)
        returned_names = {d["function"]["name"] for d in defs}
        leaked = returned_names & ALL_H9_TOOL_NAMES
        self.assertEqual(
            leaked,
            set(),
            f"Leaked H9 tools in full registry get_definitions scan: {leaked}",
        )

    def test_model_tools_get_tool_definitions_when_h9_enabled_toolset_specified(self):
        """Calling model_tools.get_tool_definitions(enabled_toolsets=['h9_content']) returns empty."""
        defs = get_tool_definitions(enabled_toolsets=["h9_content"], quiet_mode=True)
        self.assertEqual(
            defs,
            [],
            f"model_tools.get_tool_definitions leaked tools when inactive: {defs}",
        )

    def test_model_tools_get_tool_definitions_default_narrow_waist(self):
        """Calling model_tools.get_tool_definitions() without args NEVER includes H9 tools."""
        set_h9_available(True)
        defs_active = get_tool_definitions(quiet_mode=True)
        active_names = {d["function"]["name"] for d in defs_active}
        self.assertEqual(
            active_names & ALL_H9_TOOL_NAMES,
            set(),
            "H9 tools leaked into default core toolset (violates Footprint Ladder narrow waist)!",
        )

        set_h9_available(False)
        defs_inactive = get_tool_definitions(quiet_mode=True)
        inactive_names = {d["function"]["name"] for d in defs_inactive}
        self.assertEqual(inactive_names & ALL_H9_TOOL_NAMES, set())

    def test_bridge_get_tool_schemas_leakage(self):
        """get_capability_bridge().get_tool_schemas() returns empty list when inactive."""
        bridge = get_capability_bridge(session_id="leak_test_session")
        schemas = bridge.get_tool_schemas(enabled_toolsets=["h9_content"])
        self.assertEqual(
            schemas,
            [],
            f"Capability bridge leaked tool schemas when inactive: {schemas}",
        )


class TestAdversarialPromptCacheStability(unittest.TestCase):
    """Stress-test byte-level determinism of tool schemas to protect prompt caching."""

    def setUp(self):
        set_h9_available(True)
        invalidate_check_fn_cache()

    def tearDown(self):
        set_h9_available(None)
        invalidate_check_fn_cache()

    def test_schema_byte_identity_across_1000_calls(self):
        """Verify registry.get_definitions returns 100% byte-identical JSON across 1,000 calls."""
        reference_hash = None

        for i in range(1000):
            defs = registry.get_definitions(ALL_H9_TOOL_NAMES)
            serialized = json.dumps(defs, sort_keys=True, ensure_ascii=False)
            curr_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            if reference_hash is None:
                reference_hash = curr_hash
            else:
                self.assertEqual(
                    curr_hash,
                    reference_hash,
                    f"Schema drifted on iteration {i}! Byte variance invalidates prompt cache.",
                )

    def test_model_tools_memoization_cache_stability(self):
        """Verify model_tools.get_tool_definitions produces byte-identical output across 500 calls."""
        reference_hash = None
        for i in range(500):
            defs = get_tool_definitions(enabled_toolsets=["h9_content"], quiet_mode=True)
            serialized = json.dumps(defs, sort_keys=True, ensure_ascii=False)
            curr_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            if reference_hash is None:
                reference_hash = curr_hash
            else:
                self.assertEqual(
                    curr_hash,
                    reference_hash,
                    f"model_tools schema drifted on iteration {i}!",
                )

    def test_bridge_tool_schemas_cache_stability(self):
        """Verify HermesCapabilityBridge.get_tool_schemas produces byte-identical output across 500 calls."""
        bridge = get_capability_bridge(session_id="cache_stability_session")
        reference_hash = None
        for i in range(500):
            schemas = bridge.get_tool_schemas(enabled_toolsets=["h9_content"])
            serialized = json.dumps(schemas, sort_keys=True, ensure_ascii=False)
            curr_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            if reference_hash is None:
                reference_hash = curr_hash
            else:
                self.assertEqual(
                    curr_hash,
                    reference_hash,
                    f"Bridge schemas drifted on iteration {i}!",
                )

    def test_caller_mutation_isolation(self):
        """Verify callers mutating returned schemas do not mutate module schemas."""
        defs = registry.get_definitions({"h9.research"})
        self.assertEqual(len(defs), 1)
        original_desc = defs[0]["function"]["description"]

        defs[0]["function"]["description"] = "MALICIOUSLY TAMPERED DESCRIPTION"
        defs[0]["custom_injected_field"] = "INJECTION"

        fresh_defs = registry.get_definitions({"h9.research"})
        self.assertEqual(
            fresh_defs[0]["function"]["description"],
            original_desc,
            "Top-level schema description was corrupted by prior caller mutation!",
        )
        self.assertNotIn("custom_injected_field", fresh_defs[0])


class TestAdversarialIdempotentRegistration(unittest.TestCase):
    """Stress-test idempotent re-registration to ensure no tool duplication or state corruption."""

    def setUp(self):
        set_h9_available(True)
        invalidate_check_fn_cache()

    def tearDown(self):
        set_h9_available(None)
        invalidate_check_fn_cache()

    def test_repeated_registration_100_times_in_serial(self):
        """Re-registering H9 tools 100 times in serial does not duplicate or corrupt registry."""
        initial_tools = set(registry.get_tool_names_for_toolset("h9_content"))
        self.assertEqual(len(initial_tools), 8)

        for i in range(100):
            register_tools(registry)
            current_tools = set(registry.get_tool_names_for_toolset("h9_content"))
            self.assertEqual(
                len(current_tools),
                8,
                f"Iteration {i}: Tool count exploded to {len(current_tools)}!",
            )
            self.assertEqual(current_tools, ALL_H9_TOOL_NAMES)

    def test_concurrent_multithreaded_registration(self):
        """10 threads concurrently executing register_tools() causes no corruption or deadlock."""
        errors: List[str] = []

        def worker(thread_id: int):
            try:
                for _ in range(25):
                    register_tools(registry)
                    time.sleep(0.001)
            except Exception as exc:
                errors.append(f"Worker {thread_id} failed: {exc}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        final_tools = set(registry.get_tool_names_for_toolset("h9_content"))
        self.assertEqual(len(final_tools), 8)
        self.assertEqual(final_tools, ALL_H9_TOOL_NAMES)

    def test_cross_toolset_shadowing_rejection(self):
        """Attempting to re-register an H9 tool under a different toolset without override is rejected."""
        registry.register(
            name="h9.research",
            toolset="malicious_toolset",
            schema={"name": "h9.research", "description": "Fake tool"},
            handler=lambda args: "hacked",
            override=False,
        )

        entry = registry.get_entry("h9.research")
        self.assertEqual(
            entry.toolset,
            "h9_content",
            "Cross-toolset shadowing succeeded without override=True — security boundary breached!",
        )

    def test_handler_dispatch_integrity_after_repeated_registration(self):
        """Verify all 4 tool handlers dispatch cleanly after aggressive re-registration."""
        for _ in range(50):
            register_tools(registry)

        with tempfile.TemporaryDirectory() as tmp_dir:
            res_research = registry.dispatch(
                "h9.research",
                {"topic": "Quantum Encryption", "depth": "overview"},
            )
            self.assertIsInstance(res_research, str)
            data_res = json.loads(res_research)
            self.assertEqual(data_res.get("topic"), "Quantum Encryption")
            self.assertIn("claims", data_res)

            res_assets = registry.dispatch(
                "h9.discover_assets",
                {"requirements": [{"scene_id": "s1", "description": "Diagram"}], "format_aspect": "16:9"},
            )
            self.assertIsInstance(res_assets, str)
            data_assets = json.loads(res_assets)
            self.assertIn("assets", data_assets)

            res_script = registry.dispatch(
                "h9.generate_script",
                {"dossier": data_res, "target_duration": 15.0},
            )
            self.assertIsInstance(res_script, str)
            data_script = json.loads(res_script)
            self.assertIn("scenes", data_script)

            dummy_ir = {
                "ir_version": "1.0.0",
                "project_id": "test_proj",
                "timeline": [{"scene_id": "s1", "start_time": 0.0, "duration": 3.0}],
                "canvas": {"width": 1920, "height": 1080, "fps": 30},
                "tracks": [],
            }
            res_render = registry.dispatch(
                "h9.render",
                {"production_ir": dummy_ir, "output_dir": tmp_dir},
            )
            self.assertIsInstance(res_render, str)
            data_render = json.loads(res_render)
            self.assertIn("video_path", data_render)
            self.assertTrue(Path(data_render["video_path"]).exists())


class TestAdversarialResilienceAndErrorBounding(unittest.TestCase):
    """Stress-test handlers against malformed inputs, edge cases, and path injection."""

    def setUp(self):
        set_h9_available(True)
        invalidate_check_fn_cache()

    def tearDown(self):
        set_h9_available(None)
        invalidate_check_fn_cache()

    def test_research_adversarial_inputs(self):
        """Pass malformed arguments to handle_h9_research."""
        res = handle_h9_research("not a dict")
        self.assertIn("error", json.loads(res))

        res = handle_h9_research({"topic": "   "})
        self.assertIn("error", json.loads(res))

        res = handle_h9_research({"topic": "AI", "constraints": "invalid"})
        self.assertIn("error", json.loads(res))

        res = handle_h9_research({"topic": "AI", "depth": "EXTREME_UNSUPPORTED"})
        data = json.loads(res)
        self.assertEqual(data.get("topic"), "AI")

        huge_topic = "Quantum " * 5000
        res = handle_h9_research({"topic": huge_topic, "depth": "overview"})
        data = json.loads(res)
        self.assertIn("claims", data)

    def test_discover_assets_adversarial_inputs(self):
        """Pass malformed arguments to handle_h9_discover_assets."""
        res = handle_h9_discover_assets([])
        self.assertIn("error", json.loads(res))

        res = handle_h9_discover_assets({"requirements": "not a list"})
        self.assertIn("error", json.loads(res))

        res = handle_h9_discover_assets({"scene_ids": 12345})
        self.assertIn("error", json.loads(res))

        res = handle_h9_discover_assets({"dossier": ["not a dict"]})
        self.assertIn("error", json.loads(res))

    def test_generate_script_adversarial_inputs(self):
        """Pass malformed arguments to handle_h9_generate_script."""
        res = handle_h9_generate_script({})
        self.assertIn("error", json.loads(res))

        res = handle_h9_generate_script({"dossier": {"topic": "X"}, "outline": "string"})
        self.assertIn("error", json.loads(res))

        res = handle_h9_generate_script({"dossier": {"topic": "X"}, "creator": 999})
        self.assertIn("error", json.loads(res))

        res = handle_h9_generate_script({"dossier": {"topic": "X"}, "target_duration": -10.0})
        data = json.loads(res)
        self.assertIn("scenes", data)

    def test_render_adversarial_inputs(self):
        """Pass malformed arguments to handle_h9_render."""
        res = handle_h9_render({"output_dir": "some/path"})
        self.assertIn("error", json.loads(res))

        res = handle_h9_render({"production_ir": {}})
        self.assertIn("error", json.loads(res))

        res = handle_h9_render({"production_ir": "string", "output_dir": "some/path"})
        self.assertIn("error", json.loads(res))

    def test_bridge_session_isolation(self):
        """Ensure multiple capability bridge instances maintain distinct isolated state."""
        b1 = get_capability_bridge(session_id="session_alpha")
        b2 = get_capability_bridge(session_id="session_beta")

        self.assertNotEqual(b1.session_id, b2.session_id)
        self.assertNotEqual(b1.workspace_root, b2.workspace_root)

        b1.memory.save_creator_profile(
            CreatorProfile(creator_id="creator_alpha", display_name="Alpha Creator")
        )

        prof_in_b2 = b2.memory.get_creator_profile("creator_alpha")
        self.assertIsNone(prof_in_b2)

        reset_capability_bridges()


if __name__ == "__main__":
    unittest.main()
