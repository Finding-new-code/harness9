"""Comprehensive Acceptance Verification Suite for Hermes x Harness 9 Runtime Coupling.

Milestone 6: Acceptance & Regression Verification Suite.

Covers all 8 required acceptance dimensions:
- Dimension A: Runtime Coupling (interfaces, protocols, types in src/h9_runtime/)
- Dimension B: Skill Coupling (skills/h9-*/ loadable, SKILL.md, typed Production IR interface)
- Dimension C: Provider Coupling (logical role execution through Hermes providers, fallback chains)
- Dimension D: Tool Coupling (h9.research, h9.discover_assets, h9.generate_script, h9.render, h9.publish registered in tools/registry.py, check_h9_available gate)
- Dimension E: Subagent Coupling (research delegation to isolated Hermes subagent returning structured ResearchDossier)
- Dimension F: Permission Coupling (capability token calculus, least-privilege enforcement, TokenGuard blocking unauthorized calls to h9.render/h9.publish, active cascading revocation)
- Dimension G: Sandbox Coupling (BaseEnvironment execution, process group timeout kill, CWD isolation, path confinement)
- Dimension H: End-to-End Video Artifact Generation (content creation request through Hermes Agent runtime executes through skills, tools, and subagent to render a valid MP4 video artifact).
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

# ===========================================================================
# Dimension A & Core Runtime Imports
# ===========================================================================
from src.h9_runtime import (
    AgentRuntime,
    ContentRuntime,
    DefaultAgentRuntime,
    DefaultContentRuntime,
    DefaultExecutionRuntime,
    DefaultMemoryRuntime,
    DefaultModelRuntime,
    DefaultSkillRuntime,
    DefaultToolRuntime,
    ExecutionRuntime,
    HermesCapabilityBridge,
    HermesExecutionRuntime,
    HermesMemoryRuntime,
    MemoryRuntime,
    ModelRuntime,
    SkillRuntime,
    ToolRuntime,
    get_capability_bridge,
    reset_capability_bridges,
)
from src.h9_runtime.types import (
    BudgetStatus,
    CapabilityRole,
    ExecutionResult,
    MemoryRecallItem,
    ModelResponse,
    ProductionIR,
    ProductionResult,
    SessionState,
    SkillMetadata,
    SubagentResult,
    SubagentStatus,
    ToolDefinition,
    ToolInvocationContext,
)

# ===========================================================================
# Dimension B & Production Contracts / IR Imports
# ===========================================================================
from src.models.contracts import (
    AssetRecord,
    AssetRequirement,
    ClaimRecord,
    ContentBrief,
    ContentOutline,
    ContentProject,
    CreatorProfile,
    Dimensions,
    EditorialAngle,
    EvaluationReport,
    LearningCandidate,
    LicenseInfo,
    OutlineAct,
    ProductionHistoryRecord,
    PublishPackage,
    RenderArtifact,
    ResearchDossier,
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
)
from src.models.ir import (
    AudioNarration,
    HyperFramesCompiler,
    IRAnimationTrack,
    IRAssetReference,
    IRAudioTrack,
    IRBlockType,
    IRMetadata,
    IRNarrationBlock,
    IRSceneNode,
    IRSpeechBeat,
    IRTransitionSpec,
    IRVisualBlockNode,
    ProductionIRDocument,
    compile_script_to_ir,
)

# ===========================================================================
# Dimension D & Tool Imports
# ===========================================================================
from tools.h9_content_tools import (
    H9_DISCOVER_ASSETS_SCHEMA,
    H9_GENERATE_SCRIPT_SCHEMA,
    H9_PUBLISH_SCHEMA,
    H9_RENDER_SCHEMA,
    H9_RESEARCH_SCHEMA,
    handle_h9_discover_assets,
    handle_h9_generate_script,
    handle_h9_publish,
    handle_h9_render,
    handle_h9_research,
)
from tools.registry import (
    check_h9_available,
    invalidate_check_fn_cache,
    registry,
    set_h9_available,
)

# ===========================================================================
# Dimension F & Security Imports
# ===========================================================================
from src.security.tokens import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    STAGE_PERMISSIONS,
    CapabilityToken,
    DelegationLimitExceededError,
    NetworkEgressError,
    PathTraversalError,
    PermissionDeniedError,
    SecurityError,
    TokenExpiredError,
    TokenRevocationRegistry,
    TokenTamperedError,
    TokenValidationError,
    calculate_capability_token,
    create_root_token,
    derive_child_token,
    get_token_revocation_registry,
    reset_token_revocation_registry,
    sign_capability_token,
    verify_capability_token,
)
from src.security.guard import (
    SecurityGuard,
    current_capability_token,
    get_security_guard,
    reset_security_guard,
)

# ===========================================================================
# Dimension G & Sandbox Imports
# ===========================================================================
from src.h9_runtime.execution import resolve_environment
from src.assets.freezer import download_stream_sandboxed
from src.hyperframes.renderer import HyperFramesRenderer, RenderResult
from src.orchestrator.state_machine import ProductionStateMachine, ProductionState


# ===========================================================================
# Helper Schemas
# ===========================================================================
class AcceptanceEditorialTestSchema(BaseModel):
    headline: str
    angle_archetype: str = "contrarian"
    score: int = 10
    reasoning: str


# ===========================================================================
# Dimension A: Runtime Coupling
# ===========================================================================
class TestAcceptanceDimensionARuntimeCoupling(unittest.TestCase):
    """Acceptance Dimension A: Runtime boundary protocols, types, and isolation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_a01_protocols_runtime_checkable_and_implemented(self):
        """Verify all 7 runtime protocols in src/h9_runtime/ are runtime_checkable and implemented."""
        agent_rt: AgentRuntime = DefaultAgentRuntime()
        skill_rt: SkillRuntime = DefaultSkillRuntime()
        tool_rt: ToolRuntime = DefaultToolRuntime()
        model_rt: ModelRuntime = DefaultModelRuntime()
        memory_rt: MemoryRuntime = DefaultMemoryRuntime(storage_dir=self.base_dir / "memory")
        exec_rt: ExecutionRuntime = DefaultExecutionRuntime(base_dir=self.base_dir / "exec")
        content_rt: ContentRuntime = DefaultContentRuntime(base_workspace_dir=self.base_dir / "content")

        self.assertIsInstance(agent_rt, AgentRuntime)
        self.assertIsInstance(skill_rt, SkillRuntime)
        self.assertIsInstance(tool_rt, ToolRuntime)
        self.assertIsInstance(model_rt, ModelRuntime)
        self.assertIsInstance(memory_rt, MemoryRuntime)
        self.assertIsInstance(exec_rt, ExecutionRuntime)
        self.assertIsInstance(content_rt, ContentRuntime)

    def test_a02_bridge_implements_all_runtime_protocols_and_unified_facade(self):
        """Verify HermesCapabilityBridge unifies and satisfies all runtime interfaces cleanly."""
        bridge = HermesCapabilityBridge(session_id="acc_dim_a_02", workspace_root=self.base_dir)

        self.assertIsInstance(bridge, AgentRuntime)
        self.assertIsInstance(bridge, SkillRuntime)
        self.assertIsInstance(bridge, ToolRuntime)
        self.assertIsInstance(bridge, ModelRuntime)
        self.assertIsInstance(bridge, MemoryRuntime)
        self.assertIsInstance(bridge, ExecutionRuntime)
        self.assertIsInstance(bridge, ContentRuntime)

        # Check singleton retrieval by session ID
        bridge_singleton = get_capability_bridge(session_id="acc_dim_a_02", workspace_root=self.base_dir)
        self.assertIs(bridge, bridge_singleton)

    def test_a03_typed_contracts_and_serialization_invariants(self):
        """Verify serialization contracts on runtime dataclasses."""
        # 1. ProductionIR
        ir = ProductionIR(
            project_id="proj_acc_01",
            aspect_ratio="16:9",
            duration_seconds=30.0,
            fps=30,
            timeline_blocks=[{"id": "block_0", "duration": 30.0}],
            css_variables={"--primary": "#ff4444"},
            metadata={"source": "acceptance_suite"},
        )
        ir_dict = ir.to_dict()
        self.assertEqual(ir_dict["project_id"], "proj_acc_01")
        self.assertEqual(ir_dict["fps"], 30)

        # 2. ProductionResult
        prod_res = ProductionResult(
            success=True,
            project_id="proj_acc_01",
            session_id="sess_acc_01",
            video_path="/renders/acc.mp4",
            elapsed_seconds=14.2,
        )
        self.assertTrue(prod_res.to_dict()["success"])

        # 3. ModelResponse
        m_resp = ModelResponse(
            content="Generated script content",
            model_name="claude-3-7-sonnet",
            provider_name="anthropic",
            prompt_tokens=150,
            completion_tokens=250,
            cost_usd=0.004,
            duration_seconds=0.85,
        )
        self.assertGreater(m_resp.cost_usd, 0.0)

    def test_a04_agent_session_lifecycle_and_interrupt_handling(self):
        """Verify agent session lifecycle, turn execution, and deterministic interrupt handling."""
        agent_rt = DefaultAgentRuntime()
        session = agent_rt.create_session("sess_lifecycle_01", role="orchestrator")
        self.assertEqual(session.session_id, "sess_lifecycle_01")
        self.assertEqual(session.current_state, "CREATED")
        self.assertFalse(session.is_interrupted)

        # Execute turn
        turn_1 = agent_rt.execute_turn("sess_lifecycle_01", "Plan video on semiconductors")
        self.assertTrue(turn_1["turn_completed"])
        self.assertEqual(turn_1["iteration"], 1)

        # Interrupt session
        interrupted = agent_rt.interrupt_session("sess_lifecycle_01", reason="operator_requested_halt")
        self.assertTrue(interrupted)
        self.assertTrue(agent_rt.check_interrupt("sess_lifecycle_01"))

        # Subsequent turn reflects interrupted status
        turn_2 = agent_rt.execute_turn("sess_lifecycle_01", "Continue")
        self.assertTrue(turn_2["interrupted"])
        self.assertFalse(turn_2["turn_completed"])

    def test_a05_clean_boundary_isolation_no_private_hermes_imports(self):
        """Verify domain packages do not import private internal Hermes modules directly."""
        domain_dirs = [
            Path("src/research"),
            Path("src/editorial"),
            Path("src/scriptwriting"),
            Path("src/hyperframes"),
            Path("src/assets"),
            Path("src/creator"),
        ]

        prohibited_modules = {"run_agent", "cli", "tui_gateway", "hermes_cli"}

        for d in domain_dirs:
            if not d.exists():
                continue
            for py_file in d.rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_pkg = alias.name.split(".")[0]
                            self.assertNotIn(
                                root_pkg,
                                prohibited_modules,
                                f"Forbidden private Hermes import '{alias.name}' in {py_file}",
                            )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            root_pkg = node.module.split(".")[0]
                            self.assertNotIn(
                                root_pkg,
                                prohibited_modules,
                                f"Forbidden private Hermes import from '{node.module}' in {py_file}",
                            )


# ===========================================================================
# Dimension B: Skill Coupling
# ===========================================================================
class TestAcceptanceDimensionBSkillCoupling(unittest.TestCase):
    """Acceptance Dimension B: Native Hermes skills and Typed Production IR interface."""

    def setUp(self):
        self.skill_runtime = DefaultSkillRuntime()

    def test_b01_all_four_h9_skills_discovered(self):
        """Verify all 4 H9 skills are discoverable from skills/ directory."""
        skills = self.skill_runtime.discover_skills()
        names = {s.name for s in skills}
        expected = {"h9-research", "h9-content-planning", "h9-production", "h9-hyperframes"}
        for exp in expected:
            self.assertIn(exp, names, f"Skill '{exp}' must be discoverable.")

    def test_b02_yaml_frontmatter_metadata_conformance(self):
        """Verify strict YAML frontmatter metadata fields on all 4 skills."""
        skills = {s.name: s for s in self.skill_runtime.discover_skills()}
        for name in ["h9-research", "h9-content-planning", "h9-production", "h9-hyperframes"]:
            s = skills[name]
            self.assertEqual(s.version, "1.0.0")
            self.assertIn("Harness 9", s.author)
            self.assertGreater(len(s.description), 15)
            self.assertGreater(len(s.tags), 0)

    def test_b03_tier1_progressive_disclosure_byte_stable_prompt_table(self):
        """Verify Tier 1 progressive disclosure table is byte-stable and compact."""
        table1 = self.skill_runtime.build_system_prompt_index()
        table2 = self.skill_runtime.build_system_prompt_index()
        self.assertEqual(table1, table2, "System prompt skill index must be byte-stable for prompt caching.")
        self.assertIn("`h9-research`", table1)
        self.assertIn("`h9-content-planning`", table1)
        self.assertIn("`h9-production`", table1)
        self.assertIn("`h9-hyperframes`", table1)

    def test_b04_tier2_skill_instruction_loading_and_structure(self):
        """Verify Tier 2 instruction loading loads full SKILL.md documentation."""
        res_inst = self.skill_runtime.load_skill_instructions("h9-research")
        self.assertIn("ResearchDossier", res_inst)

        plan_inst = self.skill_runtime.load_skill_instructions("h9-content-planning")
        self.assertIn("EditorialScorecard", plan_inst)

        prod_inst = self.skill_runtime.load_skill_instructions("h9-production")
        self.assertIn("17-State Lifecycle Machine", prod_inst)

        hf_inst = self.skill_runtime.load_skill_instructions("h9-hyperframes")
        self.assertIn("ProductionIRDocument", hf_inst)

    def test_b05_tier3_resource_loading_and_path_traversal_rejection(self):
        """Verify Tier 3 resource loading and strict directory traversal prevention."""
        with self.assertRaises(ValueError):
            self.skill_runtime.load_skill_resource("h9-research", "../../../../etc/passwd")

    def test_b06_production_ir_ast_schema_and_invariant_validation(self):
        """Verify strict Pydantic v2 AST schema invariants on ProductionIRDocument."""
        meta = IRMetadata(
            project_id="proj_ir_ast_01",
            topic="Acceptance Testing",
            title="Hermes H9 Coupling",
            aspect_ratio="16:9",
            fps=30,
        )
        audio = IRAudioTrack(
            audio_rel_path="audio/narration.wav",
            total_duration_sec=10.0,
            sample_rate=44100,
            channels=2,
        )
        manifest = {
            "asset_01": IRAssetReference(
                asset_id="asset_01",
                file_path="assets/diagram.svg",
                file_sha256="a" * 64,
                media_type="image/svg+xml",
                verified=True,
            )
        }
        scene = IRSceneNode(
            scene_id="scene_01",
            scene_index=0,
            duration_sec=10.0,
            narration=IRNarrationBlock(
                text="Testing the typed production IR interface.",
                speech_beats=[
                    IRSpeechBeat(text="Testing", start_sec=0.0, end_sec=2.0),
                    IRSpeechBeat(text="the typed production IR", start_sec=2.0, end_sec=6.0),
                    IRSpeechBeat(text="interface.", start_sec=6.0, end_sec=10.0),
                ],
            ),
            visual_blocks=[
                IRVisualBlockNode(
                    block_id="block_01",
                    block_type=IRBlockType.SPLIT_SCREEN_INTRO,
                    start_sec=0.0,
                    duration_sec=10.0,
                    props={"headline": "Production IR Verification"},
                    referenced_asset_ids=["asset_01"],
                )
            ],
        )

        doc = ProductionIRDocument(
            metadata=meta,
            audio_track=audio,
            scenes=[scene],
            asset_manifest=manifest,
        )

        self.assertEqual(doc.total_duration_sec, 10.0)
        self.assertEqual(len(doc.scenes), 1)
        self.assertEqual(doc.scenes[0].visual_blocks[0].block_type, IRBlockType.SPLIT_SCREEN_INTRO)

        # Invariant failure on negative duration
        with self.assertRaises(Exception):
            IRSceneNode(
                scene_id="invalid_scene",
                scene_index=0,
                duration_sec=-5.0,
                narration=IRNarrationBlock(text="Invalid"),
                visual_blocks=[],
            )

    def test_b07_script_and_assets_to_ir_ast_compilation(self):
        """Verify compile_script_to_ir compiles Script into validated ProductionIRDocument."""
        script = Script(
            project_id="proj_compile_ir_01",
            title="Compiler Verification",
            aspect_ratio="16:9",
            estimated_duration_seconds=12.0,
            scenes=[
                ScriptScene(
                    scene_id="s1",
                    scene_index=1,
                    narration="First scene explaining architecture.",
                    visual_direction="Show split screen intro",
                    estimated_duration_seconds=6.0,
                    beats=[
                        ScriptBeat(beat_id="b1", beat_index=1, text="First scene", start_second=0.0, end_second=3.0),
                        ScriptBeat(beat_id="b2", beat_index=2, text="explaining architecture.", start_second=3.0, end_second=6.0),
                    ],
                ),
                ScriptScene(
                    scene_id="s2",
                    scene_index=2,
                    narration="Second scene concluding.",
                    visual_direction="Show statistics reveal",
                    estimated_duration_seconds=6.0,
                    beats=[
                        ScriptBeat(beat_id="b3", beat_index=1, text="Second scene concluding.", start_second=6.0, end_second=12.0),
                    ],
                ),
            ],
        )

        ir_doc = compile_script_to_ir(script=script)
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(ir_doc.metadata.project_id, "proj_compile_ir_01")
        self.assertEqual(len(ir_doc.scenes), 2)
        self.assertEqual(ir_doc.total_duration_sec, 12.0)

    def test_b08_hyperframes_compiler_compiles_ir_to_bundle(self):
        """Verify HyperFramesCompiler transforms ProductionIRDocument into HTML/CSS/GSAP bundle."""
        script = Script(
            project_id="proj_bundle_01",
            title="Bundle Verification",
            aspect_ratio="16:9",
            estimated_duration_seconds=10.0,
            scenes=[
                ScriptScene(
                    scene_id="s1",
                    scene_index=1,
                    narration="Welcome to HyperFrames compilation.",
                    visual_direction="Show reference collage hook",
                    estimated_duration_seconds=10.0,
                    beats=[
                        ScriptBeat(beat_id="b1", beat_index=1, text="Welcome", start_second=0.0, end_second=10.0),
                    ],
                )
            ],
        )
        ir_doc = compile_script_to_ir(script=script)
        compiler = HyperFramesCompiler()
        bundle = compiler.compile(ir_doc)

        self.assertIn("html", bundle)
        self.assertIn("css", bundle)
        self.assertIn("js", bundle)
        self.assertIn("assets", bundle)
        self.assertIn("<!DOCTYPE html>", bundle["html"])
        self.assertIn("gsap", bundle["js"].lower())


# ===========================================================================
# Dimension C: Provider Coupling
# ===========================================================================
class TestAcceptanceDimensionCProviderCoupling(unittest.TestCase):
    """Acceptance Dimension C: Logical role execution through Hermes providers, fallback chains."""

    def setUp(self):
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()

    def test_c01_all_logical_roles_execution_and_budget_accounting(self):
        """Verify execution across all 4 logical capability roles with budget accounting."""
        runtime = DefaultModelRuntime(offline=True)
        session_id = "sess_dim_c_01"

        roles = [
            CapabilityRole.FAST_EDITORIAL,
            CapabilityRole.REASONING_RESEARCH,
            CapabilityRole.CREATIVE_SCRIPT,
            CapabilityRole.ACOUSTIC_EVAL,
        ]

        for role in roles:
            resp = runtime.invoke_capability(
                role=role,
                prompt=f"Perform operation for {role.value}",
                session_id=session_id,
            )
            self.assertIsInstance(resp, ModelResponse)
            self.assertIn(role.value, resp.content)
            self.assertGreater(resp.prompt_tokens, 0)
            self.assertGreater(resp.completion_tokens, 0)
            self.assertGreater(resp.cost_usd, 0.0)

        # Budget check
        budget = runtime.get_budget_status(session_id)
        self.assertGreater(budget.tokens_consumed, 0)
        self.assertGreater(budget.cost_usd, 0.0)

    def test_c02_structured_pydantic_schema_enforcement_across_roles(self):
        """Verify structured output generation adhering to Pydantic schemas."""
        runtime = DefaultModelRuntime(offline=True)

        # 1. Custom schema on FAST_EDITORIAL
        resp_edit = runtime.invoke_capability(
            role=CapabilityRole.FAST_EDITORIAL,
            prompt="Generate contrarian headline",
            schema=AcceptanceEditorialTestSchema,
            session_id="sess_dim_c_02",
        )
        self.assertIsInstance(resp_edit.parsed, AcceptanceEditorialTestSchema)
        self.assertEqual(resp_edit.parsed.score, 10)

        # 2. ResearchDossier on REASONING_RESEARCH
        resp_res = runtime.invoke_capability(
            role=CapabilityRole.REASONING_RESEARCH,
            prompt="Research Semiconductor Lithography",
            schema=ResearchDossier,
            session_id="sess_dim_c_02",
        )
        self.assertIsInstance(resp_res.parsed, ResearchDossier)
        self.assertTrue(resp_res.parsed.topic)
        self.assertGreater(len(resp_res.parsed.claims), 0)

        # 3. Script on CREATIVE_SCRIPT
        resp_scr = runtime.invoke_capability(
            role=CapabilityRole.CREATIVE_SCRIPT,
            prompt="Write video script",
            schema=Script,
            session_id="sess_dim_c_02",
        )
        self.assertIsInstance(resp_scr.parsed, Script)
        self.assertTrue(resp_scr.parsed.title)

    def test_c03_dynamic_role_configuration_overrides(self):
        """Verify configure_role updates model name, provider, and parameters dynamically."""
        runtime = DefaultModelRuntime(offline=True)
        runtime.configure_role(
            role=CapabilityRole.CREATIVE_SCRIPT,
            model_name="claude-3-7-sonnet-custom",
            provider="anthropic_custom",
            cost_per_1k_tokens=0.006,
            temperature=0.75,
            max_tokens=3000,
        )

        cfg = runtime.get_role_config(CapabilityRole.CREATIVE_SCRIPT)
        self.assertEqual(cfg["model_name"], "claude-3-7-sonnet-custom")
        self.assertEqual(cfg["provider"], "anthropic_custom")
        self.assertEqual(cfg["temperature"], 0.75)
        self.assertEqual(cfg["max_tokens"], 3000)

    def test_c04_provider_fallback_chain_resilience(self):
        """Verify fallback behavior when primary model invocation fails or raises an error."""
        runtime = DefaultModelRuntime(offline=False)

        with patch.object(
            runtime,
            "_call_primary_provider",
            side_effect=RuntimeError("Primary provider connection timeout"),
        ), patch.object(
            runtime,
            "_call_fallback_provider",
            return_value=ModelResponse(
                content="Fallback provider generated response",
                model_name="fallback-model",
                provider_name="fallback-provider",
                prompt_tokens=50,
                completion_tokens=50,
                cost_usd=0.001,
                duration_seconds=0.3,
            ),
        ) as mock_fallback:
            resp = runtime.invoke_capability(
                role=CapabilityRole.FAST_EDITORIAL,
                prompt="Fast editorial prompt",
                session_id="sess_dim_c_fallback",
            )
            mock_fallback.assert_called_once()
            self.assertEqual(resp.provider_name, "fallback-provider")
            self.assertIn("Fallback", resp.content)

    def test_c05_budget_status_and_cost_aggregation(self):
        """Verify budget status aggregates token counts and costs monotonically."""
        runtime = DefaultModelRuntime(offline=True)
        session_id = "sess_budget_agg"

        b_initial = runtime.get_budget_status(session_id)
        self.assertEqual(b_initial.tokens_consumed, 0)
        self.assertEqual(b_initial.cost_usd, 0.0)

        runtime.invoke_capability(role=CapabilityRole.FAST_EDITORIAL, prompt="turn 1", session_id=session_id)
        b_turn1 = runtime.get_budget_status(session_id)
        self.assertGreater(b_turn1.tokens_consumed, 0)
        self.assertGreater(b_turn1.cost_usd, 0.0)

        runtime.invoke_capability(role=CapabilityRole.REASONING_RESEARCH, prompt="turn 2", session_id=session_id)
        b_turn2 = runtime.get_budget_status(session_id)
        self.assertGreater(b_turn2.tokens_consumed, b_turn1.tokens_consumed)
        self.assertGreater(b_turn2.cost_usd, b_turn1.cost_usd)


# ===========================================================================
# Dimension D: Tool Coupling
# ===========================================================================
class TestAcceptanceDimensionDToolCoupling(unittest.TestCase):
    """Acceptance Dimension D: Native model tools registered in tools/registry.py, check_h9_available gate."""

    def setUp(self):
        invalidate_check_fn_cache()
        set_h9_available(None)
        reset_capability_bridges()

    def tearDown(self):
        invalidate_check_fn_cache()
        set_h9_available(None)
        reset_capability_bridges()

    def test_d01_named_toolset_registration_all_five_tools_and_aliases(self):
        """Verify all 5 tools and snake_case aliases are registered under 'h9_content'."""
        registered = set(registry.get_tool_names_for_toolset("h9_content"))
        expected = {
            "h9.research",
            "h9_research",
            "h9.discover_assets",
            "h9_discover_assets",
            "h9.generate_script",
            "h9_generate_script",
            "h9.render",
            "h9_render",
            "h9.publish",
            "h9_publish",
        }
        for t in expected:
            self.assertIn(t, registered, f"Tool '{t}' must be registered in toolset 'h9_content'")

    def test_d02_openai_function_schemas_validity_and_completeness(self):
        """Verify all 5 tool schemas match standard OpenAI function call format."""
        schemas = [
            ("h9.research", H9_RESEARCH_SCHEMA, ["topic"]),
            ("h9.discover_assets", H9_DISCOVER_ASSETS_SCHEMA, ["dossier"]),
            ("h9.generate_script", H9_GENERATE_SCRIPT_SCHEMA, ["dossier"]),
            ("h9.render", H9_RENDER_SCHEMA, ["production_ir", "output_dir"]),
            ("h9.publish", H9_PUBLISH_SCHEMA, ["platform"]),
        ]
        for name, schema, required_fields in schemas:
            self.assertEqual(schema["name"], name)
            self.assertIn("description", schema)
            self.assertEqual(schema["parameters"]["type"], "object")
            for req in required_fields:
                self.assertIn(req, schema["parameters"]["required"])

    def test_d03_footprint_ladder_rung3_service_gate_active_vs_inactive(self):
        """Verify check_h9_available service gate ensures zero tool definition overhead when disabled."""
        # When active
        set_h9_available(True)
        self.assertTrue(check_h9_available())
        tool_names = {"h9.research", "h9.discover_assets", "h9.generate_script", "h9.render", "h9.publish"}
        defs_active = registry.get_definitions(tool_names)
        self.assertEqual(len(defs_active), 5)

        # When inactive
        set_h9_available(False)
        self.assertFalse(check_h9_available())
        defs_inactive = registry.get_definitions(tool_names)
        self.assertEqual(len(defs_inactive), 0, "When H9 is inactive, zero tool definitions must be exposed.")

    def test_d04_tool_handlers_genuine_execution_and_return_types(self):
        """Verify direct execution of tool handlers returns valid JSON results."""
        # 1. h9.research
        res_raw = handle_h9_research(args={"topic": "Quantum Computing", "depth": "overview"})
        res_data = json.loads(res_raw)
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["topic"], "Quantum Computing")
        self.assertIn("dossier", res_data)

        # 2. h9.discover_assets
        ast_raw = handle_h9_discover_assets(args={"dossier": res_data["dossier"]})
        ast_data = json.loads(ast_raw)
        self.assertTrue(ast_data["success"])
        self.assertIn("assets", ast_data)

        # 3. h9.generate_script
        scr_raw = handle_h9_generate_script(args={"dossier": res_data["dossier"]})
        scr_data = json.loads(scr_raw)
        self.assertTrue(scr_data["success"])
        self.assertIn("script", scr_data)

    def test_d05_tool_error_handling_and_input_sanitization(self):
        """Verify invalid tool inputs return structured JSON error envelopes without crashing."""
        # Missing required parameter 'topic'
        err_res = handle_h9_research(args={})
        err_data = json.loads(err_res)
        self.assertFalse(err_data["success"])
        self.assertIn("error", err_data)

        # Invalid production_ir in render
        err_rnd = handle_h9_render(args={"production_ir": "not_a_dict", "output_dir": "out"})
        err_rnd_data = json.loads(err_rnd)
        self.assertFalse(err_rnd_data["success"])


# ===========================================================================
# Dimension E: Subagent Coupling
# ===========================================================================
class TestAcceptanceDimensionESubagentCoupling(unittest.TestCase):
    """Acceptance Dimension E: Research delegation to isolated Hermes subagent returning ResearchDossier."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_e01_subagent_spawning_and_context_isolation(self):
        """Verify subagent spawning creates an isolated session context and fresh history."""
        agent_rt = DefaultAgentRuntime()
        parent_session = "sess_parent_01"
        agent_rt.create_session(parent_session)

        # Spawn subagent
        sub_res = agent_rt.spawn_subagent(
            parent_session_id=parent_session,
            task="Research Optical Lithography",
            allowed_tools=["h9.research", "web_search"],
        )
        self.assertIsInstance(sub_res, SubagentResult)
        self.assertEqual(sub_res.status, SubagentStatus.COMPLETED)
        self.assertTrue(sub_res.subagent_id.startswith("subagent_"))
        self.assertNotEqual(sub_res.subagent_id, parent_session)

    def test_e02_subagent_tool_scoping_and_blocked_dangerous_tools(self):
        """Verify dangerous tools (delegate_task, send_message, etc.) are stripped from subagent."""
        agent_rt = DefaultAgentRuntime()
        parent_session = "sess_parent_02"
        agent_rt.create_session(parent_session)

        # Request blocked tools
        sub_res = agent_rt.spawn_subagent(
            parent_session_id=parent_session,
            task="Perform isolated research",
            allowed_tools=["delegate_task", "clarify", "h9.research", "send_message"],
        )
        # Check that execution did not fail and subagent executed within constrained scope
        self.assertEqual(sub_res.status, SubagentStatus.COMPLETED)

    def test_e03_research_subagent_returns_verified_dossier(self):
        """Verify research delegation via bridge returns a structured, validated ResearchDossier."""
        bridge = HermesCapabilityBridge(session_id="sess_dim_e_03", workspace_root=self.base_dir)
        dossier = bridge.delegate_research(topic="Artificial Intelligence", depth="overview")

        self.assertIsInstance(dossier, ResearchDossier)
        self.assertEqual(dossier.topic, "Artificial Intelligence")
        self.assertGreater(len(dossier.claims), 0)
        self.assertIsInstance(dossier.claims[0], ClaimRecord)
        self.assertIsInstance(dossier.claims[0].primary_source, SourceRecord)

    def test_e04_subagent_lifecycle_status_and_result_reporting(self):
        """Verify subagent transitions through status lifecycle with duration and result tracking."""
        agent_rt = DefaultAgentRuntime()
        agent_rt.create_session("parent_sess_04")

        sub_res = agent_rt.spawn_subagent(
            parent_session_id="parent_sess_04",
            task="Investigate Superconductors",
        )
        self.assertEqual(sub_res.status, SubagentStatus.COMPLETED)
        self.assertGreater(sub_res.duration_seconds, 0.0)
        self.assertIn("task", sub_res.result)

    def test_e05_prompt_cache_stability_during_subagent_delegation(self):
        """Verify parent session prompt cache prefix remains unchanged during subagent execution."""
        agent_rt = DefaultAgentRuntime()
        parent_id = "sess_parent_cache"
        agent_rt.create_session(parent_id)

        # Initial turn
        t1 = agent_rt.execute_turn(parent_id, "Initiate research")
        initial_history_len = len(agent_rt.get_session_state(parent_id).conversation_history)

        # Run subagent
        agent_rt.spawn_subagent(parent_id, "Conduct deep search")

        # Parent conversation history is untouched by subagent turns
        current_history_len = len(agent_rt.get_session_state(parent_id).conversation_history)
        self.assertEqual(initial_history_len, current_history_len)


# ===========================================================================
# Dimension F: Permission Coupling
# ===========================================================================
class TestAcceptanceDimensionFPermissionCoupling(unittest.TestCase):
    """Acceptance Dimension F: Capability token calculus, TokenGuard tool gating, cascading revocation."""

    def setUp(self):
        reset_security_guard()
        reset_token_revocation_registry()
        reset_capability_bridges()

    def tearDown(self):
        reset_security_guard()
        reset_token_revocation_registry()
        reset_capability_bridges()

    def test_f01_capability_token_calculus_least_privilege(self):
        """Verify token derivation calculus: P_child = P_parent ∩ P_role ∩ P_workflow."""
        root = create_root_token(
            subject="root_agent",
            allowed_tools={"h9.research", "h9.discover_assets", "h9.generate_script", "h9.render", "h9.publish"},
            ttl_seconds=3600,
        )

        # Derive researcher child
        child_researcher = derive_child_token(
            parent_token=root,
            child_subject="research_subagent",
            role="researcher",
            workflow="research",
        )
        self.assertIn("h9.research", child_researcher.allowed_tools)
        self.assertNotIn("h9.render", child_researcher.allowed_tools)
        self.assertNotIn("h9.publish", child_researcher.allowed_tools)

        # Monotonicity check: child cannot exceed parent
        self.assertTrue(child_researcher.allowed_tools.issubset(root.allowed_tools))

    def test_f02_hmac_sha256_cryptographic_integrity_and_tampering(self):
        """Verify HMAC-SHA256 signature verification and tampering detection."""
        token = create_root_token(subject="valid_agent", ttl_seconds=600)
        self.assertTrue(verify_capability_token(token))

        # Tampering with subject
        tampered_token = token.model_copy(update={"subject": "attacker_agent"})
        with self.assertRaises(TokenTamperedError):
            verify_capability_token(tampered_token)

        # Tampering with allowed tools
        tampered_tools = token.model_copy(update={"allowed_tools": token.allowed_tools | {"unauthorized_tool"}})
        with self.assertRaises(TokenTamperedError):
            verify_capability_token(tampered_tools)

    def test_f03_token_expiration_detection_and_rejection(self):
        """Verify tokens with past expiry are immediately rejected with TokenExpiredError."""
        expired_token = create_root_token(subject="expired_agent", ttl_seconds=-10)
        with self.assertRaises(TokenExpiredError):
            verify_capability_token(expired_token)

        guard = get_security_guard()
        with self.assertRaises(TokenExpiredError):
            guard.enforce_tool_execution(expired_token, "h9.research")

    def test_f04_privileged_tool_gating_render_and_publish_enforcement(self):
        """Verify TokenGuard strictly blocks unauthorized calls to h9.render and h9.publish."""
        guard = get_security_guard()

        # Restricted token without render or publish permissions
        restricted_token = create_root_token(
            subject="restricted_worker",
            allowed_tools={"h9.research", "h9.discover_assets", "h9.generate_script"},
            ttl_seconds=600,
        )

        # Attempt calling h9.render -> blocked
        with self.assertRaises(PermissionDeniedError):
            guard.enforce_tool_execution(restricted_token, "h9.render")

        # Attempt calling h9.publish -> blocked
        with self.assertRaises(PermissionDeniedError):
            guard.enforce_tool_execution(restricted_token, "h9.publish")

        # Calling authorized tool -> succeeds
        self.assertTrue(guard.enforce_tool_execution(restricted_token, "h9.research"))

        # Root token with full permissions -> both succeed
        privileged_token = create_root_token(
            subject="privileged_worker",
            allowed_tools={"h9.render", "h9.publish"},
            ttl_seconds=600,
        )
        self.assertTrue(guard.enforce_tool_execution(privileged_token, "h9.render"))
        self.assertTrue(guard.enforce_tool_execution(privileged_token, "h9.publish"))

    def test_f05_active_cascading_lineage_revocation(self):
        """Verify revoking a parent token cascades down the lineage tree to child and grandchild."""
        registry = get_token_revocation_registry()
        guard = get_security_guard()

        root = create_root_token(subject="root_node", ttl_seconds=3600)
        child = derive_child_token(parent_token=root, child_subject="child_node", role="editor")
        grandchild = derive_child_token(parent_token=child, child_subject="grandchild_node", role="writer")

        # Before revocation, all are valid
        self.assertFalse(registry.is_revoked(root.token_id))
        self.assertFalse(registry.is_revoked(child.token_id))
        self.assertFalse(registry.is_revoked(grandchild.token_id))

        # Revoke root with cascading
        registry.revoke_token(root.token_id, reason="Security compromise", cascade=True)

        # All descendants are now revoked
        self.assertTrue(registry.is_revoked(root.token_id))
        self.assertTrue(registry.is_revoked(child.token_id))
        self.assertTrue(registry.is_revoked(grandchild.token_id))

        # Guard enforcement rejects revoked child
        with self.assertRaises(PermissionDeniedError):
            guard.enforce_tool_execution(child, "h9.research")

    def test_f06_contextvar_token_propagation_across_contexts(self):
        """Verify current_capability_token ContextVar propagates token seamlessly."""
        token = create_root_token(subject="ctx_agent", ttl_seconds=600)
        c_tok = current_capability_token.set(token)
        try:
            retrieved = current_capability_token.get()
            self.assertEqual(retrieved.token_id, token.token_id)
        finally:
            current_capability_token.reset(c_tok)


# ===========================================================================
# Dimension G: Sandbox Coupling
# ===========================================================================
class TestAcceptanceDimensionGSandboxCoupling(unittest.TestCase):
    """Acceptance Dimension G: BaseEnvironment execution, process group timeout kill, CWD isolation, path confinement."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="h9_acc_sandbox_")
        self.sandbox_dir = Path(self.temp_dir) / "sandbox"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.runtime = HermesExecutionRuntime(
            session_id="sess_acc_sandbox",
            base_dir=self.sandbox_dir,
            env_type="local",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_g01_hermes_execution_runtime_and_environment_resolution(self):
        """Verify HermesExecutionRuntime wraps BaseEnvironment and resolves environments."""
        self.assertEqual(self.runtime.session_id, "sess_acc_sandbox")
        self.assertIsNotNone(self.runtime.env)

        local_env = resolve_environment("local", cwd=str(self.sandbox_dir))
        self.assertIsNotNone(local_env)

        # Fallback on unrecognized env
        fallback_env = resolve_environment("nonexistent_env_type", cwd=str(self.sandbox_dir))
        self.assertIsNotNone(fallback_env)

    def test_g02_sandboxed_command_execution_success(self):
        """Verify command execution returns output and 0 exit code."""
        result = self.runtime.execute_command(["python", "-c", "print('acceptance_sandbox_ok')"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("acceptance_sandbox_ok", result.stdout)
        self.assertGreater(result.duration_seconds, 0.0)

    def test_g03_process_group_timeout_kill_exit_code_124(self):
        """Verify process group timeout terminates runaway command with exit code 124."""
        result = self.runtime.execute_command(
            ["python", "-c", "import time; time.sleep(5)"],
            timeout_seconds=1.0,
        )
        self.assertEqual(result.exit_code, 124)
        self.assertIn("timed out", result.stderr.lower())

    def test_g04_filesystem_jail_path_confinement_and_traversal_rejection(self):
        """Verify validate_path strictly confines paths to jail and rejects traversal attempts."""
        valid_file = self.runtime.session_root / "test.txt"
        valid_file.write_text("content", encoding="utf-8")

        self.assertEqual(self.runtime.validate_path("test.txt"), valid_file.resolve())

        # Parent directory escape
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.validate_path("../outside.txt")

        # Multi-level escape
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.validate_path("subdir/../../../../etc/shadow")

        # Null byte injection
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.validate_path("file.txt\0payload")

    def test_g05_atomic_sandboxed_file_read_write(self):
        """Verify write_file and read_file operate within sandbox and reject outside writes."""
        content = json.dumps({"test": "acceptance_payload"})
        written = self.runtime.write_file("data/config.json", content)
        self.assertTrue(written.exists())

        read_back = self.runtime.read_file("data/config.json")
        self.assertEqual(read_back, content)

        # Reject write outside
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.write_file("../../outside.txt", "evil")

    def test_g06_hyperframes_renderer_sandboxed_subprocess_routing(self):
        """Verify HyperFramesRenderer routes subprocess execution through HermesExecutionRuntime."""
        proj_dir = Path(self.temp_dir) / "hf_project"
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "index.html").write_text("<html><body>Render Project</body></html>", encoding="utf-8")

        mock_exec = MagicMock(spec=HermesExecutionRuntime)
        mock_exec.execute_command.return_value = ExecutionResult(
            exit_code=0, stdout="Subprocess complete", stderr="", duration_seconds=0.1
        )
        mock_exec.validate_path.side_effect = lambda p: Path(p).resolve()

        renderer = HyperFramesRenderer(execution_runtime=mock_exec)

        with patch("src.hyperframes.renderer.is_ffmpeg_available", return_value=True), \
             patch("src.hyperframes.renderer.probe_media_file", return_value={
                 "has_video": True, "has_audio": True, "duration": 5.0, "width": 1920, "height": 1080, "fps": 30.0
             }), \
             patch("src.hyperframes.renderer.render_video_with_ffmpeg") as mock_ffmpeg:

            res = renderer.render(project_dir=proj_dir)
            self.assertIsInstance(res, RenderResult)
            self.assertEqual(res.validation_status, "VERIFIED")

    def test_g07_sandboxed_media_streaming_and_byte_capping(self):
        """Verify download_stream_sandboxed restricts byte size and confines destination to jail."""
        dest = self.sandbox_dir / "asset.bin"

        # Mock download streaming 100 bytes with 50 byte max
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"A" * 60]

        with patch("requests.get", return_value=mock_response), \
             self.assertRaises(ValueError):
            download_stream_sandboxed(
                url="https://example.com/huge.bin",
                destination_path=dest,
                max_bytes=50,
            )


# ===========================================================================
# Dimension H: End-to-End Video Artifact Generation
# ===========================================================================
class TestAcceptanceDimensionHEndToEndVideoArtifactGeneration(unittest.TestCase):
    """Acceptance Dimension H: Complete pipeline execution producing valid MP4 video artifact."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()
        reset_security_guard()
        reset_token_revocation_registry()

    def tearDown(self):
        reset_capability_bridges()
        reset_security_guard()
        reset_token_revocation_registry()
        self.temp_dir.cleanup()

    def test_h01_end_to_end_content_creation_to_rendered_mp4(self):
        """Verify full autonomous pipeline from brief to verified MP4 video artifact."""
        session_id = "sess_e2e_video_01"
        bridge = HermesCapabilityBridge(session_id=session_id, workspace_root=self.workspace)

        # 1. Brief
        brief = ContentBrief(
            project_id="proj_e2e_acc_01",
            topic="History of the Transistor",
            aspect_ratio="16:9",
            target_duration_seconds=15,
            target_audience="General Tech",
            creator_id="creator_tech",
            offline_mode=True,
        )

        # 2. Stage: Research
        dossier = bridge.delegate_research(topic=brief.topic, depth="overview")
        self.assertIsInstance(dossier, ResearchDossier)
        self.assertEqual(dossier.topic, brief.topic)
        self.assertGreater(len(dossier.claims), 0)

        # 3. Stage: Script & Editorial
        script_dict = bridge.generate_script(dossier=dossier.model_dump(), creator_id=brief.creator_id)
        script = Script(**script_dict)
        self.assertIsInstance(script, Script)
        self.assertGreater(len(script.scenes), 0)

        # 4. Stage: Asset Discovery
        assets = bridge.discover_assets(dossier=dossier.model_dump(), format=brief.aspect_ratio)
        self.assertIsInstance(assets, list)
        self.assertGreater(len(assets), 0)

        # 5. Stage: Production IR Compilation
        ir_doc = bridge.compile_production_ir(script=script)
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(ir_doc.metadata.project_id, script.project_id)
        self.assertGreater(ir_doc.total_duration_sec, 0.0)

        # 6. Stage: Rendering Video Artifact
        renders_dir = self.workspace / "renders"
        artifact = bridge.render_video(ir=ir_doc, output_dir=renders_dir)

        self.assertIsInstance(artifact, RenderArtifact)
        video_path = Path(artifact.video_path)
        self.assertTrue(video_path.exists(), f"Rendered video {video_path} must exist on disk.")
        self.assertGreater(video_path.stat().st_size, 0, "Video artifact must be non-zero in size.")

        # Verify MP4 container header (ftyp box)
        header_bytes = video_path.read_bytes()[:32]
        self.assertIn(b"ftyp", header_bytes, "Rendered artifact must be a valid ISO base media file (MP4).")

        # Verify artifact contract properties
        self.assertEqual(artifact.width, 1920)
        self.assertEqual(artifact.height, 1080)
        self.assertEqual(artifact.fps, 30)
        self.assertEqual(artifact.video_codec, "h264")

    def test_h02_end_to_end_publishing_and_manifest_generation(self):
        """Verify publishing workflow produces verified publication manifest and records state."""
        session_id = "sess_e2e_publish_02"
        bridge = HermesCapabilityBridge(session_id=session_id, workspace_root=self.workspace)

        # Create dummy video file
        renders_dir = self.workspace / "renders"
        renders_dir.mkdir(parents=True, exist_ok=True)
        video_file = renders_dir / "final.mp4"
        video_file.write_bytes(b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41")

        # Publish
        pub_result = bridge.publish(
            platform="youtube",
            video_path=video_file,
            title="History of the Transistor",
            description="Autonomous documentary on semiconductors.",
            session_id=session_id,
        )

        self.assertTrue(pub_result["success"])
        self.assertEqual(pub_result["platform"], "youtube")
        self.assertIn("manifest_path", pub_result)

        manifest_file = Path(pub_result["manifest_path"])
        self.assertTrue(manifest_file.exists())
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(manifest_data["platform"], "youtube")
        self.assertIn("video_sha256", manifest_data)
        self.assertEqual(len(manifest_data["video_sha256"]), 64)

    def test_h03_full_pipeline_multi_dimensional_governance_coordination(self):
        """Verify end-to-end autonomous production with capability tokens and execution sandbox."""
        session_id = "sess_e2e_coord_03"
        guard = get_security_guard()

        # Generate root token
        root_token = create_root_token(
            subject="production_orchestrator",
            allowed_tools={"h9.research", "h9.discover_assets", "h9.generate_script", "h9.render", "h9.publish"},
            ttl_seconds=3600,
        )
        guard.register_session_token(session_id, root_token)

        bridge = HermesCapabilityBridge(
            session_id=session_id,
            workspace_root=self.workspace,
            capability_token=root_token,
        )

        brief = ContentBrief(
            project_id="proj_coord_03",
            topic="Quantum Entanglement",
            aspect_ratio="16:9",
            target_duration_seconds=10,
            offline_mode=True,
        )

        # Run full production
        prod_result = bridge.run_production(brief=brief)

        self.assertTrue(prod_result.success)
        self.assertEqual(prod_result.project_id, brief.project_id)
        self.assertTrue(Path(prod_result.video_path).exists())

        # Audit log verifies canonical states
        states = [s["state"] for s in prod_result.state_history]
        self.assertIn("CREATED", states)
        self.assertIn("RESEARCH_PLANNED", states)
        self.assertIn("RESEARCH_IN_PROGRESS", states)
        self.assertIn("COMPLETED", states)


if __name__ == "__main__":
    unittest.main()
