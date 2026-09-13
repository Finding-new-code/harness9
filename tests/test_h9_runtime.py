"""Unit tests for src/h9_runtime/ protocols and implementations (Milestone M1)."""

import json
from pathlib import Path
import tempfile
import time
import unittest
from pydantic import BaseModel

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
    MemoryRuntime,
    ModelRuntime,
    SkillRuntime,
    ToolRuntime,
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
from src.models.contracts import (
    ContentBrief,
    CreatorProfile,
    EditorialAngle,
    LearningCandidate,
    ResearchDossier,
    Script,
)


class SampleSchema(BaseModel):
    title: str
    score: int
    active: bool


class TestH9Runtime(unittest.TestCase):
    """Comprehensive test suite for src/h9_runtime/ boundary interfaces."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -----------------------------------------------------------------------
    # 1. Protocols & Types Verification
    # -----------------------------------------------------------------------
    def test_01_runtime_protocol_conformance(self):
        """Verify that default runtime classes conform to runtime_checkable protocols."""
        agent_rt: AgentRuntime = DefaultAgentRuntime()
        skill_rt: SkillRuntime = DefaultSkillRuntime()
        tool_rt: ToolRuntime = DefaultToolRuntime()
        model_rt: ModelRuntime = DefaultModelRuntime()
        memory_rt: MemoryRuntime = DefaultMemoryRuntime(storage_dir=self.base_dir / "memory")
        exec_rt: ExecutionRuntime = DefaultExecutionRuntime(base_dir=self.base_dir / "sessions")
        content_rt: ContentRuntime = DefaultContentRuntime(base_workspace_dir=self.base_dir / "ws")

        self.assertIsInstance(agent_rt, AgentRuntime)
        self.assertIsInstance(skill_rt, SkillRuntime)
        self.assertIsInstance(tool_rt, ToolRuntime)
        self.assertIsInstance(model_rt, ModelRuntime)
        self.assertIsInstance(memory_rt, MemoryRuntime)
        self.assertIsInstance(exec_rt, ExecutionRuntime)
        self.assertIsInstance(content_rt, ContentRuntime)

    def test_02_types_serialization(self):
        """Verify serialization contracts on shared data structures."""
        ir = ProductionIR(
            project_id="proj_ir_01",
            aspect_ratio="16:9",
            duration_seconds=15.0,
            fps=30,
            timeline_blocks=[{"id": "b1", "duration": 15.0}],
            css_variables={"--accent": "#00d2ff"},
        )
        ir_dict = ir.to_dict()
        self.assertEqual(ir_dict["project_id"], "proj_ir_01")
        self.assertEqual(ir_dict["duration_seconds"], 15.0)

        prod_res = ProductionResult(
            success=True,
            project_id="proj_01",
            session_id="sess_01",
            video_path="/path/to/video.mp4",
            elapsed_seconds=12.5,
        )
        res_dict = prod_res.to_dict()
        self.assertTrue(res_dict["success"])
        self.assertEqual(res_dict["session_id"], "sess_01")

    # -----------------------------------------------------------------------
    # 2. AgentRuntime Tests
    # -----------------------------------------------------------------------
    def test_03_agent_runtime_session_lifecycle(self):
        """Verify session creation, turn execution, and interrupt handling."""
        rt = DefaultAgentRuntime()

        # Create session
        session = rt.create_session("session_agent_01", role="orchestrator", metadata={"channel": "cli"})
        self.assertEqual(session.session_id, "session_agent_01")
        self.assertEqual(session.current_state, "CREATED")
        self.assertFalse(session.is_interrupted)

        # Retrieve state
        retrieved = rt.get_session_state("session_agent_01")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.session_id, "session_agent_01")

        # Execute turn
        turn_res = rt.execute_turn("session_agent_01", "Create a video on AI")
        self.assertTrue(turn_res["turn_completed"])
        self.assertEqual(turn_res["iteration"], 1)

        # Interrupt session
        interrupted = rt.interrupt_session("session_agent_01", reason="operator_abort")
        self.assertTrue(interrupted)
        self.assertTrue(rt.check_interrupt("session_agent_01"))

        # Subsequent turn reflects interrupt
        turn_res_2 = rt.execute_turn("session_agent_01", "Continue")
        self.assertTrue(turn_res_2["interrupted"])
        self.assertFalse(turn_res_2["turn_completed"])

    def test_04_agent_runtime_subagent_delegation(self):
        """Verify subagent spawning, isolation, and sanitized toolsets."""
        rt = DefaultAgentRuntime()
        rt.create_session("parent_session_01")

        subagent_res = rt.delegate_subagent(
            parent_session_id="parent_session_01",
            goal="Synthesize research on microchips",
            role="researcher",
            context={"topic": "Microchips", "claims": ["c1", "c2"]},
            allowed_toolsets=["web_search", "delegate_task", "h9.render", "read_file"],
            max_iterations=10,
        )

        self.assertIsInstance(subagent_res, SubagentResult)
        self.assertEqual(subagent_res.status, SubagentStatus.COMPLETED)
        self.assertIn("microchips", subagent_res.output.lower())
        self.assertIsNotNone(subagent_res.structured_data)
        
        # Verify blocked tools were stripped
        allowed = subagent_res.structured_data["allowed_tools"]
        self.assertIn("web_search", allowed)
        self.assertIn("read_file", allowed)
        self.assertNotIn("delegate_task", allowed)
        self.assertNotIn("h9.render", allowed)

    # -----------------------------------------------------------------------
    # 3. SkillRuntime Tests
    # -----------------------------------------------------------------------
    def test_05_skill_runtime_progressive_disclosure(self):
        """Verify 3-tier progressive disclosure: Tier 1 index, Tier 2 instructions, Tier 3 resources."""
        rt = DefaultSkillRuntime()

        # Tier 1: Discovery
        skills = rt.discover_skills()
        self.assertGreaterEqual(len(skills), 4)
        names = [s.name for s in skills]
        self.assertIn("h9-research", names)
        self.assertIn("h9-content-planning", names)
        self.assertIn("h9-production", names)
        self.assertIn("h9-hyperframes", names)

        # Tier 2: Instruction loading
        instructions = rt.load_skill_instructions("h9-research")
        self.assertIn("# H9 Research & Fact Verification Skill", instructions)
        self.assertIn("Quick Reference", instructions)

        # Tier 3: Resource loading with path traversal rejection
        resource = rt.load_skill_resource("h9-research", "references/intent_categories.md")
        self.assertIsNotNone(resource)

        with self.assertRaises(ValueError):
            rt.load_skill_resource("h9-research", "../../../etc/passwd")

        # System prompt compact index
        prompt_index = rt.build_system_prompt_index()
        self.assertIn("### Available Skills", prompt_index)
        self.assertIn("`h9-research`", prompt_index)

    # -----------------------------------------------------------------------
    # 4. ToolRuntime Tests
    # -----------------------------------------------------------------------
    def test_06_tool_runtime_registration_validation_dispatch(self):
        """Verify tool registration, parameter validation, service gating, and dispatch."""
        rt = DefaultToolRuntime()

        schema = {
            "type": "function",
            "function": {
                "name": "calc_add",
                "description": "Add two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer"},
                        "tag": {"type": "string"},
                    },
                    "required": ["a", "b"],
                },
            },
        }

        def handler(args: dict) -> dict:
            return {"sum": args["a"] + args["b"], "tag": args.get("tag", "")}

        tool = ToolDefinition(
            name="calc_add",
            toolset="math_tools",
            schema=schema,
            handler=handler,
            check_fn=lambda: True,
        )

        rt.register_tool(tool)
        self.assertTrue(rt.is_toolset_available("math_tools"))

        schemas = rt.get_tool_schemas(enabled_toolsets=["math_tools"])
        self.assertEqual(len(schemas), 1)

        ctx = ToolInvocationContext(session_id="s1", task_id="t1")

        # Valid invocation
        res = rt.dispatch_tool("calc_add", {"a": 10, "b": 20}, ctx)
        parsed = json.loads(res)
        self.assertEqual(parsed["sum"], 30)

        # Missing required parameter validation
        err_res = rt.dispatch_tool("calc_add", {"a": 10}, ctx)
        err_parsed = json.loads(err_res)
        self.assertIn("error", err_parsed)
        self.assertIn("Missing required parameter: 'b'", err_parsed["error"])

        # Type mismatch validation
        err_type = rt.dispatch_tool("calc_add", {"a": "ten", "b": 20}, ctx)
        self.assertIn("expected integer", json.loads(err_type)["error"])

        # Unregistered tool dispatch
        err_unreg = rt.dispatch_tool("unknown_tool", {}, ctx)
        self.assertIn("not registered", json.loads(err_unreg)["error"])

    # -----------------------------------------------------------------------
    # 5. ModelRuntime Tests
    # -----------------------------------------------------------------------
    def test_07_model_runtime_roles_and_budgeting(self):
        """Verify logical capability role invocation, schema generation, and spend accounting."""
        rt = DefaultModelRuntime()

        # Configure custom role
        rt.configure_role(
            CapabilityRole.FAST_EDITORIAL,
            model_name="test-fast-model",
            provider="test-provider",
            cost_per_1k_tokens=0.002,
        )

        # Plain completion
        resp = rt.invoke_capability(
            role=CapabilityRole.FAST_EDITORIAL,
            prompt="Brainstorm 5 angles",
            session_id="sess_budget_01",
        )
        self.assertIsInstance(resp, ModelResponse)
        self.assertIn("fast_editorial", resp.content)
        self.assertGreater(resp.prompt_tokens, 0)
        self.assertGreater(resp.cost_usd, 0.0)

        # Structured schema completion
        resp_schema = rt.invoke_capability(
            role=CapabilityRole.FAST_EDITORIAL,
            prompt="Generate sample data",
            schema=SampleSchema,
            session_id="sess_budget_01",
        )
        self.assertIsInstance(resp_schema.parsed, SampleSchema)
        self.assertEqual(resp_schema.parsed.score, 1)

        # Budget tracking
        budget = rt.get_budget_status("sess_budget_01")
        self.assertIsInstance(budget, BudgetStatus)
        self.assertGreater(budget.tokens_consumed, 0)
        self.assertGreater(budget.cost_usd, 0.0)

    # -----------------------------------------------------------------------
    # 6. MemoryRuntime Tests
    # -----------------------------------------------------------------------
    def test_08_memory_runtime_profile_and_recalls(self):
        """Verify CreatorProfile persistence, context recall, and prompt block rendering."""
        rt = DefaultMemoryRuntime(storage_dir=self.base_dir / "memory")

        profile = CreatorProfile(
            creator_id="creator_tech_01",
            display_name="DeepTech Insights",
            tone_of_voice=["rigorous", "engaging"],
            target_audiences=["Engineers", "Researchers"],
            negative_rules=["Never use clickbait", "No unverified benchmarks"],
        )

        rt.save_creator_profile(profile)
        loaded = rt.get_creator_profile("creator_tech_01")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.display_name, "DeepTech Insights")

        # Context recall
        recalls = rt.recall_context(query="benchmarks and clickbait", creator_id="creator_tech_01")
        self.assertGreater(len(recalls), 0)
        self.assertIn("clickbait", recalls[0].content)

        # Telemetry & learning candidates recall
        cand = LearningCandidate(
            lesson_id="lc_retention_01",
            creator_id="creator_tech_01",
            rule_type="retention",
            observation="Viewer dropoff increases if intro exceeds 15 seconds",
            recommended_action="Keep cold open under 10 seconds",
            confidence=0.85,
        )
        rt.record_production_telemetry(
            project_id="proj_01",
            metrics={"watch_time": 120},
            learning_candidates=[cand],
        )
        recalls_cand = rt.recall_context(query="cold open dropoff", creator_id="creator_tech_01")
        self.assertGreater(len(recalls_cand), 0)
        retention_cand = next((r for r in recalls_cand if r.category == "retention"), None)
        self.assertIsNotNone(retention_cand)
        self.assertEqual(retention_cand.score, 0.9)
        self.assertIn("Keep cold open under 10 seconds", retention_cand.content)
        self.assertEqual(retention_cand.metadata["candidate_id"], "lc_retention_01")

        # System prompt block
        block = rt.render_system_prompt_block("creator_tech_01")
        self.assertIn("DeepTech Insights", block)
        self.assertIn("Never use clickbait", block)

    # -----------------------------------------------------------------------
    # 7. ExecutionRuntime Tests
    # -----------------------------------------------------------------------
    def test_09_execution_runtime_sandboxed_operations(self):
        """Verify path confinement, command execution, and atomic I/O."""
        rt = DefaultExecutionRuntime(base_dir=self.base_dir / "sessions")
        session_id = "sess_exec_01"

        # Valid path confinement
        valid_path = rt.validate_path("sub/test.txt", session_id)
        self.assertTrue(str(valid_path).startswith(str(self.base_dir.resolve())))

        # Path traversal rejection
        with self.assertRaises(ValueError):
            rt.validate_path("../../unauthorized.txt", session_id)

        # Atomic write and read
        written = rt.write_file("data/sample.json", json.dumps({"status": "ok"}), session_id=session_id)
        self.assertTrue(written.exists())
        content = rt.read_file("data/sample.json", session_id=session_id)
        self.assertEqual(json.loads(content)["status"], "ok")

        # Command execution
        cmd_res = rt.execute_command(
            ["python", "-c", "print('hello from sandbox')"],
            session_id=session_id,
        )
        self.assertEqual(cmd_res.exit_code, 0)
        self.assertIn("hello from sandbox", cmd_res.stdout)
        self.assertFalse(cmd_res.timed_out)

    # -----------------------------------------------------------------------
    # 8. ContentRuntime Tests
    # -----------------------------------------------------------------------
    def test_10_content_runtime_stages_and_production_ir(self):
        """Verify ContentRuntime domain orchestration and Production IR compilation."""
        rt = DefaultContentRuntime(base_workspace_dir=self.base_dir / "content_ws")
        session_id = "sess_content_01"

        # 1. Plan Research
        dossier = rt.plan_research("The History of the Transistor", session_id=session_id, offline=True, duration=5)
        self.assertIsInstance(dossier, ResearchDossier)
        self.assertEqual(dossier.topic, "The History of the Transistor")
        self.assertGreaterEqual(len(dossier.claims), 1)

        # 2. Evaluate Angles
        candidates, winner = rt.evaluate_angles(dossier)
        self.assertGreaterEqual(len(candidates), 1)
        self.assertIsInstance(winner, EditorialAngle)

        # 3. Generate Script
        script = rt.generate_script(winner, dossier, duration=5.0)
        self.assertIsInstance(script, Script)
        self.assertEqual(len(script.scenes), 4)

        # 4. Compile Production IR
        ws = rt._get_session_workspace(session_id)
        ir = rt.compile_production_ir(script, workspace_dir=ws)
        self.assertIsInstance(ir, ProductionIR)
        self.assertEqual(len(ir.timeline_blocks), 4)
        self.assertIn("--primary-accent", ir.css_variables)

        # 5. Render Video
        renders_dir = rt._get_session_renders(session_id)
        render_art = rt.render_video(ir, output_dir=renders_dir, session_id=session_id)
        self.assertTrue(Path(render_art.video_path).exists())
        self.assertEqual(render_art.width, 1920)


if __name__ == "__main__":
    unittest.main()
