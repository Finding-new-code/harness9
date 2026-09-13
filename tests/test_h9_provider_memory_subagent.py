"""tests/test_h9_provider_memory_subagent.py

Comprehensive test suite for Milestone 4 (R4):
1. Provider & Model Routing across logical capability roles (fast_editorial, reasoning_research, creative_script, acoustic_eval)
2. Unified Memory & Persistence backed by Hermes SessionDB / state.db with FTS5 search and prompt cache stability
3. Isolated Subagent Research Delegation with tool scoping, schema validation, and prompt caching isolation
4. Fallback resilience and error handling
"""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from pydantic import BaseModel, Field

from src.h9_runtime.agent import DefaultAgentRuntime
from src.h9_runtime.bridge import HermesCapabilityBridge, get_capability_bridge, reset_capability_bridges
from src.h9_runtime.memory import DefaultMemoryRuntime, HermesMemoryRuntime
from src.h9_runtime.models import DefaultModelRuntime
from src.h9_runtime.types import (
    BudgetStatus,
    CapabilityRole,
    MemoryRecallItem,
    ModelResponse,
    SubagentResult,
    SubagentStatus,
)
from src.models.contracts import (
    ContentBrief,
    ContentProject,
    CreatorProfile,
    EditorialAngle,
    EvaluationReport,
    LearningCandidate,
    ProductionHistoryRecord,
    RenderArtifact,
    ResearchDossier,
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
)
from tools.h9_content_tools import handle_h9_research


class CustomEditorialSchema(BaseModel):
    headline: str
    angle_archetype: str = "contrarian"
    score: int = 1
    reasoning: str


class TestH9ProviderMemorySubagent(unittest.TestCase):
    """Milestone 4 comprehensive integration test suite."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        reset_capability_bridges()

    def tearDown(self):
        reset_capability_bridges()
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    # =======================================================================
    # 1. Provider & Model Routing Tests
    # =======================================================================

    def test_01_all_four_logical_roles_execution(self):
        """Verify execution across all 4 logical capability roles with budget accounting."""
        runtime = DefaultModelRuntime(offline=True)
        session_id = "sess_roles_01"

        roles_to_test = [
            CapabilityRole.FAST_EDITORIAL,
            CapabilityRole.REASONING_RESEARCH,
            CapabilityRole.CREATIVE_SCRIPT,
            CapabilityRole.ACOUSTIC_EVAL,
        ]

        for role in roles_to_test:
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
            self.assertTrue(resp.model_name)
            self.assertTrue(resp.provider_name)

        # Confirm accumulated budget
        budget = runtime.get_budget_status(session_id)
        self.assertGreater(budget.tokens_consumed, 0)
        self.assertGreater(budget.cost_usd, 0.0)

    def test_02_structured_schema_generation_across_roles(self):
        """Verify deterministic structured output generation adhering strictly to Pydantic schemas."""
        runtime = DefaultModelRuntime(offline=True)

        # 1. FAST_EDITORIAL with CustomEditorialSchema
        resp_edit = runtime.invoke_capability(
            role=CapabilityRole.FAST_EDITORIAL,
            prompt="Generate contrarian angle",
            schema=CustomEditorialSchema,
            session_id="sess_struct_01",
        )
        self.assertIsInstance(resp_edit.parsed, CustomEditorialSchema)
        self.assertEqual(resp_edit.parsed.score, 1)
        self.assertIn("headline", resp_edit.content)

        # 2. REASONING_RESEARCH with ResearchDossier
        resp_res = runtime.invoke_capability(
            role=CapabilityRole.REASONING_RESEARCH,
            prompt="Investigate Quantum Supremacy",
            schema=ResearchDossier,
            session_id="sess_struct_02",
        )
        self.assertIsInstance(resp_res.parsed, ResearchDossier)
        self.assertTrue(resp_res.parsed.topic)
        self.assertGreaterEqual(len(resp_res.parsed.claims), 1)
        self.assertIsInstance(resp_res.parsed.claims[0].primary_source, SourceRecord)

        # 3. CREATIVE_SCRIPT with Script
        resp_script = runtime.invoke_capability(
            role=CapabilityRole.CREATIVE_SCRIPT,
            prompt="Write multi-scene script",
            schema=Script,
            session_id="sess_struct_03",
        )
        self.assertIsInstance(resp_script.parsed, Script)

    def test_03_role_configuration_and_parameter_overrides(self):
        """Verify dynamic configuration of model, provider, temperature, and max_tokens."""
        runtime = DefaultModelRuntime(offline=True)

        runtime.configure_role(
            role=CapabilityRole.CREATIVE_SCRIPT,
            model_name="claude-3-7-sonnet-custom",
            provider="anthropic_custom",
            cost_per_1k_tokens=0.005,
            temperature=0.85,
            max_tokens=4000,
        )

        cfg = runtime.get_role_config(CapabilityRole.CREATIVE_SCRIPT)
        self.assertEqual(cfg["model_name"], "claude-3-7-sonnet-custom")
        self.assertEqual(cfg["provider"], "anthropic_custom")
        self.assertEqual(cfg["temperature"], 0.85)
        self.assertEqual(cfg["cost_per_1k_tokens"], 0.005)

        resp = runtime.invoke_capability(
            role=CapabilityRole.CREATIVE_SCRIPT,
            prompt="Compose opening narration",
            session_id="sess_cfg_01",
        )
        self.assertEqual(resp.model_name, "claude-3-7-sonnet-custom")
        self.assertEqual(resp.provider_name, "anthropic_custom")

    def test_04_session_budget_tracking_and_limit_enforcement(self):
        """Verify token spend accounting and budget limit tracking."""
        runtime = DefaultModelRuntime(offline=True)
        session_id = "sess_budget_ceiling_01"

        runtime.set_budget_limit(session_id, limit_usd=0.05)

        resp1 = runtime.invoke_capability(
            role=CapabilityRole.FAST_EDITORIAL,
            prompt="Brief brainstorm",
            session_id=session_id,
        )

        budget1 = runtime.get_budget_status(session_id)
        self.assertEqual(budget1.budget_limit_usd, 0.05)
        self.assertIsNotNone(budget1.remaining_budget_usd)
        self.assertLess(budget1.remaining_budget_usd, 0.05)

        # Additional consumption
        resp2 = runtime.invoke_capability(
            role=CapabilityRole.REASONING_RESEARCH,
            prompt="Dossier generation prompt with high token content " * 20,
            session_id=session_id,
        )

        budget2 = runtime.get_budget_status(session_id)
        self.assertGreater(budget2.tokens_consumed, budget1.tokens_consumed)
        self.assertGreater(budget2.cost_usd, budget1.cost_usd)
        self.assertLess(budget2.remaining_budget_usd, budget1.remaining_budget_usd)

    def test_05_auxiliary_client_mock_dispatch(self):
        """Verify that when auxiliary client is available and active, invoke_capability routes through it."""
        runtime = DefaultModelRuntime(offline=False)

        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "headline": "Live Discovered Breakthrough",
            "angle_archetype": "deep_dive",
            "score": 95,
            "reasoning": "Empirical evidence from live inference",
        })
        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 45
        mock_response.usage.completion_tokens = 80

        with patch("agent.auxiliary_client.call_llm", return_value=mock_response) as mock_call:
            resp = runtime.invoke_capability(
                role=CapabilityRole.FAST_EDITORIAL,
                prompt="Discover angle",
                schema=CustomEditorialSchema,
                session_id="sess_live_aux_01",
            )
            mock_call.assert_called_once()
            self.assertIsInstance(resp.parsed, CustomEditorialSchema)
            self.assertEqual(resp.parsed.headline, "Live Discovered Breakthrough")
            self.assertEqual(resp.parsed.score, 95)

    def test_06_streaming_capability_tokens(self):
        """Verify stream_capability yields word/token chunks."""
        runtime = DefaultModelRuntime(offline=True)
        chunks = list(
            runtime.stream_capability(
                role=CapabilityRole.FAST_EDITORIAL,
                prompt="Quick hook generator",
            )
        )
        self.assertGreater(len(chunks), 1)
        full_text = "".join(chunks)
        self.assertIn("fast_editorial", full_text)

    # =======================================================================
    # 2. HermesMemoryRuntime & Unified Persistence Tests
    # =======================================================================

    def test_07_hermes_memory_runtime_schema_bootstrap(self):
        """Verify schema bootstrap creates all h9_* tables and indices in SQLite."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        def _check_tables(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            return tables

        tables = mem._execute_read(_check_tables)
        expected_tables = {
            "h9_creators",
            "h9_projects",
            "h9_production_history",
            "h9_learning_candidates",
            "h9_retention_curves",
        }
        for t in expected_tables:
            self.assertIn(t, tables, f"Expected table {t} missing from state.db")

    def test_08_creator_profile_and_dna_roundtrip(self):
        """Verify saving, retrieving, and updating CreatorProfile in HermesMemoryRuntime."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        profile = CreatorProfile(
            creator_id="creator_quantum_lab",
            display_name="Quantum Computing Lab",
            tone_of_voice=["rigorous", "explanatory", "uncompromising"],
            target_audiences=["Quantum Physicists", "Hardware Engineers"],
            negative_rules=[
                "Never claim quantum computers replace classical computers universally",
                "Always specify qubit coherence times",
            ],
            brand_colors={"primary": "#00FFCC", "accent": "#330066"},
        )

        # 1. Save profile
        mem.save_creator_profile(profile)

        # 2. Retrieve profile
        loaded = mem.get_creator_profile("creator_quantum_lab")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.creator_id, "creator_quantum_lab")
        self.assertEqual(loaded.display_name, "Quantum Computing Lab")
        self.assertEqual(len(loaded.tone_of_voice), 3)
        self.assertEqual(len(loaded.negative_rules), 2)
        self.assertEqual(loaded.brand_colors.get("primary"), "#00FFCC")

        # 3. Update profile (upsert)
        profile.display_name = "Quantum Computing Lab (Official)"
        profile.negative_rules.append("Cite primary arXiv preprints")
        mem.save_creator_profile(profile)

        updated = mem.get_creator_profile("creator_quantum_lab")
        self.assertEqual(updated.display_name, "Quantum Computing Lab (Official)")
        self.assertEqual(len(updated.negative_rules), 3)

    def test_09_content_project_persistence_and_update(self):
        """Verify ContentProject persistence, nested contract retrieval, and state update."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        brief = ContentBrief(
            project_id="proj_superconductor_01",
            topic="High-Temperature Superconductivity",
            target_duration_seconds=45,
            aspect_ratio="16:9",
            goal="Explain Meissner effect and critical temperatures",
            audience="Materials Scientists",
        )

        project = ContentProject(
            project_id="proj_superconductor_01",
            session_id="sess_sc_01",
            creator_id="creator_quantum_lab",
            topic="High-Temperature Superconductivity",
            current_state="CREATED",
            brief=brief,
        )

        # 1. Save project
        mem.save_project(project)

        # 2. Retrieve project
        loaded = mem.get_project("proj_superconductor_01")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.project_id, "proj_superconductor_01")
        self.assertEqual(loaded.session_id, "sess_sc_01")
        self.assertEqual(loaded.current_state, "CREATED")
        self.assertIsNotNone(loaded.brief)
        self.assertEqual(loaded.brief.goal, "Explain Meissner effect and critical temperatures")

        # 3. Update state with ResearchDossier and Script
        dossier = ResearchDossier(
            topic="High-Temperature Superconductivity",
            headline="Cuprate and Nickelate Phase Diagrams",
            executive_summary="Critical temperature milestones from 1986 to present.",
            claims=[
                {
                    "claim_id": "c_01",
                    "claim_text": "YBCO exhibits zero electrical resistance above 77 Kelvin.",
                    "primary_source": {
                        "title": "Superconductivity in Y-Ba-Cu-O",
                        "url": "https://doi.org/10.1103/PhysRevLett.58.908",
                    },
                }
            ],
        )
        loaded.dossier = dossier
        loaded.current_state = "RESEARCH_COMPLETED"
        mem.save_project(loaded)

        updated = mem.get_project("proj_superconductor_01")
        self.assertEqual(updated.current_state, "RESEARCH_COMPLETED")
        self.assertIsNotNone(updated.dossier)
        self.assertEqual(len(updated.dossier.claims), 1)
        self.assertEqual(updated.dossier.claims[0].claim_id, "c_01")

    def test_10_production_history_state_transitions(self):
        """Verify micro-transaction logging and chronological retrieval of state machine transitions."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)
        project_id = "proj_audit_01"

        transitions = [
            ("CREATED", "RESEARCH_PLANNED", {"step": "plan"}),
            ("RESEARCH_PLANNED", "RESEARCH_SYNTHESIZED", {"claims_count": 8}),
            ("RESEARCH_SYNTHESIZED", "ANGLES_EVALUATED", {"winner": "contrarian"}),
            ("ANGLES_EVALUATED", "SCRIPT_GENERATED", {"scene_count": 4}),
        ]

        t0 = time.time()
        for i, (from_s, to_s, payload) in enumerate(transitions):
            rec = ProductionHistoryRecord(
                project_id=project_id,
                from_state=from_s,
                to_state=to_s,
                timestamp=t0 + i,
                payload_summary=payload,
                duration_ms=45.2,
                metadata={"worker": "worker_m4"},
            )
            mem.record_transition(rec)

        history = mem.get_project_history(project_id)
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0].from_state, "CREATED")
        self.assertEqual(history[0].to_state, "RESEARCH_PLANNED")
        self.assertEqual(history[-1].to_state, "SCRIPT_GENERATED")
        self.assertEqual(history[2].payload_summary["winner"], "contrarian")

    def test_11_fts5_context_recall_and_ranking(self):
        """Verify FTS5 full-text search across creator learning candidates and negative rules."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        profile = CreatorProfile(
            creator_id="creator_learn_01",
            display_name="Tech Documentarian",
            tone_of_voice=["Analytical"],
            negative_rules=["Avoid sensational clickbait phrases like mind-blowing"],
        )
        mem.save_creator_profile(profile)

        # Record learning candidates
        learnings = [
            LearningCandidate(
                lesson_id="lc_hook_01",
                creator_id="creator_learn_01",
                rule_type="retention",
                observation="Intro duration exceeding 4.5 seconds caused significant audience drop-off",
                recommended_action="Keep reference collage hook under 3.5 seconds",
                confidence=0.95,
            ),
            LearningCandidate(
                lesson_id="lc_code_02",
                creator_id="creator_learn_01",
                rule_type="visual",
                observation="Monospace code blocks with low syntax contrast reduced legibility",
                recommended_action="Apply Tokyo Night theme with 18pt font minimum",
                confidence=0.90,
            ),
            LearningCandidate(
                lesson_id="lc_audio_03",
                creator_id="creator_learn_01",
                rule_type="acoustic",
                observation="Dead air gaps greater than 0.4s interrupted speech cadence",
                recommended_action="Clamp inter-beat silence to 150ms maximum",
                confidence=0.88,
            ),
        ]
        mem.record_production_telemetry(
            project_id="proj_learn_01",
            metrics={"timestamp": time.time()},
            learning_candidates=learnings,
        )

        # 1. Search for hook retention rule
        recalled_hook = mem.recall_context(query="hook drop-off", creator_id="creator_learn_01", limit=3)
        self.assertGreaterEqual(len(recalled_hook), 1)
        top_hook = recalled_hook[0]
        self.assertIn("3.5", top_hook.content)

        # 2. Search for audio cadence rule
        recalled_audio = mem.recall_context(query="dead air speech", creator_id="creator_learn_01", limit=3)
        self.assertGreaterEqual(len(recalled_audio), 1)
        self.assertIn("150ms", recalled_audio[0].content)

    def test_12_fts5_fallback_to_like_on_special_characters(self):
        """Verify that FTS5 syntax errors gracefully fall back to LIKE search without crashing."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        lc = LearningCandidate(
            lesson_id="lc_spec_01",
            creator_id="creator_spec_01",
            rule_type="pacing",
            observation="WPM rate (180+ words/min) overwhelmed viewers!",
            recommended_action="Target 145 WPM pacing",
            confidence=0.92,
        )
        mem.record_production_telemetry(
            project_id="proj_spec_01",
            metrics={"timestamp": time.time()},
            learning_candidates=[lc],
        )

        # Query with punctuation and symbols that would error in standard FTS5
        recalled = mem.recall_context(query="180+ words/min!", creator_id="creator_spec_01", limit=2)
        self.assertGreaterEqual(len(recalled), 1)
        self.assertIn("145 WPM", recalled[0].content)

    def test_13_prompt_block_byte_stability_preserves_cache(self):
        """Verify render_system_prompt_block produces byte-stable strings preserving sacred prompt caching."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        profile = CreatorProfile(
            creator_id="creator_cache_01",
            display_name="Byte-Stable Science",
            tone_of_voice=["Objective", "Empirical"],
            target_audiences=["Physicists"],
            negative_rules=["No unsupported claims", "Explicitly state margins of error"],
        )
        mem.save_creator_profile(profile)

        # Session start snapshot
        prompt_1 = mem.render_system_prompt_block("creator_cache_01")
        prompt_2 = mem.render_system_prompt_block("creator_cache_01")
        self.assertEqual(prompt_1, prompt_2)
        self.assertEqual(hash(prompt_1), hash(prompt_2))
        self.assertIn("Byte-Stable Science", prompt_1)
        self.assertIn("Explicitly state margins of error", prompt_1)

        # Mid-session telemetry/learning candidate added
        lc = LearningCandidate(
            lesson_id="lc_new_01",
            creator_id="creator_cache_01",
            rule_type="negative_constraint",
            observation="Font size 12pt is unreadable",
            recommended_action="Use 18pt font minimum",
            confidence=0.85,
        )
        mem.record_production_telemetry("proj_test", {"timestamp": time.time()}, [lc])

        # Verify active prompt block remains 100% byte-identical
        prompt_3 = mem.render_system_prompt_block("creator_cache_01")
        self.assertEqual(prompt_1, prompt_3)

    def test_14_concurrent_micro_transactions_zero_locks(self):
        """Verify concurrent multi-threaded writes succeed without database lock timeouts."""
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        def _write_task(worker_id: int):
            proj = ContentProject(
                project_id=f"proj_worker_{worker_id}",
                session_id=f"sess_{worker_id}",
                topic=f"Concurrent Topic {worker_id}",
            )
            mem.save_project(proj)

            rec = ProductionHistoryRecord(
                project_id=f"proj_worker_{worker_id}",
                from_state="CREATED",
                to_state="COMPLETED",
                payload_summary={"worker": worker_id},
            )
            mem.record_transition(rec)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_write_task, i) for i in range(20)]
            for f in futures:
                f.result()

        # Verify all 20 projects were persisted
        for i in range(20):
            p = mem.get_project(f"proj_worker_{i}")
            self.assertIsNotNone(p)
            self.assertEqual(p.project_id, f"proj_worker_{i}")

    # =======================================================================
    # 3. Isolated Subagent Research Delegation Tests
    # =======================================================================

    def test_15_subagent_delegation_tool_scoping(self):
        """Verify principle-of-least-privilege tool scoping for subagents."""
        agent_rt = DefaultAgentRuntime()
        agent_rt.create_session("sess_parent_scope_01")

        # Request tools including blocked tools
        requested_tools = [
            "web_search",
            "read_file",
            "delegate_task",
            "clarify",
            "memory",
            "h9.render",
            "send_message",
        ]

        result = agent_rt.delegate_subagent(
            parent_session_id="sess_parent_scope_01",
            goal="Synthesize research on microchips",
            role="researcher",
            context={"topic": "Microchips"},
            allowed_toolsets=requested_tools,
        )

        self.assertEqual(result.status, SubagentStatus.COMPLETED)
        allowed = result.structured_data["allowed_tools"]
        self.assertIn("web_search", allowed)
        self.assertIn("read_file", allowed)

        # Assert ALL blocked tools are stripped
        blocked_expected = ["delegate_task", "clarify", "memory", "h9.render", "send_message"]
        for b in blocked_expected:
            self.assertNotIn(b, allowed, f"Tool {b} should be strictly blocked from subagent")

    def test_16_subagent_research_dossier_structured_output(self):
        """Verify deep research delegates to subagent and returns verified ResearchDossier."""
        bridge = HermesCapabilityBridge(session_id="sess_research_sub_01", workspace_root=self.workspace)

        dossier = bridge.plan_research(
            topic="Solid-State Battery Breakthroughs",
            depth="deep",
        )

        self.assertIsInstance(dossier, ResearchDossier)
        self.assertEqual(dossier.topic, "Solid-State Battery Breakthroughs")
        self.assertGreaterEqual(len(dossier.claims), 2)
        self.assertGreaterEqual(len(dossier.key_takeaways), 2)

        # Check claim source verification
        claim1 = dossier.claims[0]
        self.assertIsInstance(claim1.primary_source, SourceRecord)
        self.assertTrue(claim1.primary_source.url)
        self.assertGreaterEqual(claim1.confidence_score, 0.70)

    def test_17_prompt_caching_isolation_no_parent_leakage(self):
        """Verify parent context is isolated and subagent intermediate turns never enter parent history."""
        agent_rt = DefaultAgentRuntime()
        parent_state = agent_rt.create_session("sess_parent_caching_01")

        # Initial turn
        agent_rt.execute_turn("sess_parent_caching_01", "Start deep research")
        self.assertEqual(parent_state.iteration_count, 1)

        # Spawn subagent
        sub_res = agent_rt.delegate_subagent(
            parent_session_id="sess_parent_caching_01",
            goal="Investigate Graphene Conductivity",
            role="researcher",
            context={"topic": "Graphene"},
        )

        # Verify parent iteration count did not increment
        self.assertEqual(parent_state.iteration_count, 1)
        # Verify subagent ID is tracked in parent metadata
        self.assertIn("child_subagents", parent_state.metadata)
        self.assertIn(sub_res.subagent_id, parent_state.metadata["child_subagents"])

        # Tool dispatch through handle_h9_research records only top-level result
        tool_res = handle_h9_research(
            {"topic": "Graphene", "depth": "deep"},
            session_id="sess_parent_caching_01",
        )
        parsed_res = json.loads(tool_res)
        self.assertNotIn("error", parsed_res)
        self.assertEqual(parsed_res["topic"], "Graphene")

    def test_18_research_fallback_on_subagent_failure(self):
        """Verify graceful fallback to content runtime / procedural research if subagent raises error."""
        bridge = HermesCapabilityBridge(session_id="sess_fallback_01", workspace_root=self.workspace)

        # Mock delegate_subagent to raise exception
        with patch.object(bridge, "delegate_subagent", side_effect=RuntimeError("Subagent spawn timeout")):
            dossier = bridge.plan_research(
                topic="CRISPR Gene Editing",
                depth="deep",
            )
            self.assertIsInstance(dossier, ResearchDossier)
            self.assertEqual(dossier.topic, "CRISPR Gene Editing")
            self.assertGreaterEqual(len(dossier.claims), 1)

    def test_19_bridge_unified_facade_integration(self):
        """Verify end-to-end orchestration of models, memory, and subagent delegation through bridge."""
        bridge = HermesCapabilityBridge(session_id="sess_e2e_bridge_01", workspace_root=self.workspace)

        # 1. Save creator DNA
        creator = CreatorProfile(
            creator_id="creator_e2e",
            display_name="Future Tech Horizon",
            tone_of_voice=["Visionary", "Methodical"],
            negative_rules=["No unverified hype"],
        )
        bridge.save_creator_profile(creator)

        # 2. Plan deep research via subagent
        dossier = bridge.plan_research(
            topic="Room-Temperature Photonic Chips",
            depth="deep",
        )
        self.assertEqual(dossier.topic, "Room-Temperature Photonic Chips")

        # 3. Create and persist ContentProject
        proj = ContentProject(
            project_id="proj_e2e_01",
            session_id=bridge.session_id,
            creator_id="creator_e2e",
            topic="Room-Temperature Photonic Chips",
            dossier=dossier,
        )
        bridge.save_project(proj)

        # 4. Record transition
        rec = ProductionHistoryRecord(
            project_id="proj_e2e_01",
            from_state="CREATED",
            to_state="RESEARCH_COMPLETED",
            payload_summary={"claims": len(dossier.claims)},
        )
        bridge.record_transition(rec)

        # 5. Verify retrieval
        loaded_proj = bridge.get_project("proj_e2e_01")
        self.assertIsNotNone(loaded_proj)
        self.assertEqual(loaded_proj.topic, "Room-Temperature Photonic Chips")

        history = bridge.get_project_history("proj_e2e_01")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].to_state, "RESEARCH_COMPLETED")

        # 6. Check budget status
        budget = bridge.get_budget_status()
        self.assertIsInstance(budget, BudgetStatus)


if __name__ == "__main__":
    unittest.main()
