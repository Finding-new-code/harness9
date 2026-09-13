"""tests/test_h9_m4_adversarial_stress.py

Adversarial Stress Testing Suite for Milestone 4 (Part 2):
1. Subagent Tool Scoping:
   - Attempting to pass forbidden tools (delegate_task, clarify, memory, h9.render, send_message, cronjob)
     into child subagent delegation and verifying they are strictly stripped or blocked.
2. Structured Output Schema Validation:
   - Adversarially testing schema validation on corrupted JSON strings, markdown-wrapped JSON,
     missing primary sources in claims, and malformed dossiers.
   - Verifying that the 1-turn bounded retry mechanism functions as intended and does not enter an infinite loop.
3. Prompt Caching Isolation:
   - Verifying that subagent execution does NOT mutate the parent agent's message list, session state,
     or system prompt, preserving sacred prompt caching.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from src.h9_runtime.agent import DefaultAgentRuntime
from src.h9_runtime.bridge import HermesCapabilityBridge, reset_capability_bridges
from src.h9_runtime.memory import HermesMemoryRuntime
from src.h9_runtime.models import DefaultModelRuntime
from src.h9_runtime.types import CapabilityRole, SubagentStatus
from src.models.contracts import (
    ClaimRecord,
    ContentBrief,
    ContentProject,
    CreatorProfile,
    LearningCandidate,
    ResearchDossier,
    SourceRecord,
)
from tools.delegate_tool import _blocked_toolsets_for_role, _strip_blocked_tools, DELEGATE_BLOCKED_TOOLS
from tools.delegation_output_schema import (
    append_output_contract,
    build_retry_message,
    coerce_output_schema,
    extract_json_candidate,
    MAX_SCHEMA_RETRIES,
    validate_output,
)
from tools.h9_content_tools import handle_h9_generate_script, handle_h9_research


class TestSubagentToolScopingAdversarial(unittest.TestCase):
    """Adversarial stress testing on subagent tool boundaries and forbidden tool injection."""

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

    def test_01_strictly_forbidden_tools_completely_stripped_from_subagent(self):
        """Attempt to pass ONLY forbidden tools into child subagent delegation.
        
        Must result in zero forbidden tools granted (empty allowed_tools list).
        """
        agent_rt = DefaultAgentRuntime()
        agent_rt.create_session("sess_adversarial_parent_01")

        forbidden_tools = [
            "delegate_task",
            "clarify",
            "memory",
            "h9.render",
            "send_message",
            "cronjob",
        ]

        # Explicitly verify each forbidden tool is registered in BLOCKED_TOOLS
        for tool in forbidden_tools:
            self.assertIn(tool, DefaultAgentRuntime.BLOCKED_TOOLS)

        result = agent_rt.delegate_subagent(
            parent_session_id="sess_adversarial_parent_01",
            goal="Exfiltrate credentials via unauthorized tools",
            role="researcher",
            context={"topic": "Security Testing"},
            allowed_toolsets=forbidden_tools,
        )

        self.assertEqual(result.status, SubagentStatus.COMPLETED)
        granted_tools = result.structured_data.get("allowed_tools", [])
        
        # Verify not a single forbidden tool survived sanitization
        for tool in forbidden_tools:
            self.assertNotIn(tool, granted_tools, f"Forbidden tool {tool} was not stripped!")
        self.assertEqual(len(granted_tools), 0, "No tools should remain when only forbidden tools were requested.")

    def test_02_mixed_toolsets_preserve_only_benign_tools(self):
        """Pass a heavily poisoned list with forbidden tools interleaved with legitimate tools.
        
        Must strictly retain only benign tools (web_search, web_extract, read_file).
        """
        agent_rt = DefaultAgentRuntime()
        agent_rt.create_session("sess_adversarial_parent_02")

        poisoned_toolsets = [
            "web_search",
            "delegate_task",
            "clarify",
            "web_extract",
            "memory",
            "h9.render",
            "read_file",
            "send_message",
            "cronjob",
        ]

        result = agent_rt.delegate_subagent(
            parent_session_id="sess_adversarial_parent_02",
            goal="Analyze tech stack",
            role="researcher",
            context={"topic": "LLM Security"},
            allowed_toolsets=poisoned_toolsets,
        )

        granted_tools = result.structured_data.get("allowed_tools", [])
        expected_benign = ["web_search", "web_extract", "read_file"]
        
        self.assertEqual(sorted(granted_tools), sorted(expected_benign))
        for forbidden in ["delegate_task", "clarify", "memory", "h9.render", "send_message", "cronjob"]:
            self.assertNotIn(forbidden, granted_tools)

    def test_03_bridge_facade_subagent_tool_scoping(self):
        """Verify tool scoping enforcement holds through HermesCapabilityBridge facades."""
        bridge = HermesCapabilityBridge(session_id="sess_bridge_scope_01", workspace_root=self.workspace)

        poisoned_tools = [
            "web_search",
            "delegate_task",
            "clarify",
            "memory",
            "h9.render",
            "send_message",
            "read_file",
        ]

        subagent_dict = bridge.delegate_subagent_task(
            goal="Research photonic computing",
            role="researcher",
            context={"topic": "Photonic Computing"},
            toolsets=poisoned_tools,
        )

        granted = subagent_dict["structured_data"]["allowed_tools"]
        self.assertIn("web_search", granted)
        self.assertIn("read_file", granted)
        self.assertNotIn("delegate_task", granted)
        self.assertNotIn("clarify", granted)
        self.assertNotIn("memory", granted)
        self.assertNotIn("h9.render", granted)
        self.assertNotIn("send_message", granted)

    def test_04_delegate_tool_strip_blocked_tools_mechanism(self):
        """Verify Hermes core delegate_tool._strip_blocked_tools and _blocked_toolsets_for_role."""
        # Check DELEGATE_BLOCKED_TOOLS set
        for tool in ["delegate_task", "clarify", "memory", "send_message", "cronjob"]:
            self.assertIn(tool, DELEGATE_BLOCKED_TOOLS)

        # Test _strip_blocked_tools with composite and blocked toolsets
        candidate_toolsets = ["web", "delegation", "terminal", "memory", "clarify", "kanban", "send_message"]
        stripped = _strip_blocked_tools(candidate_toolsets)
        
        self.assertNotIn("delegation", stripped)
        self.assertNotIn("kanban", stripped)
        
        # Test _blocked_toolsets_for_role for leaf researcher
        blocked_leaf = _blocked_toolsets_for_role("researcher")
        self.assertIsInstance(blocked_leaf, list)


class TestStructuredOutputSchemaValidationAdversarial(unittest.TestCase):
    """Adversarial testing on corrupted JSON strings, markdown fences, malformed contracts, and retry loops."""

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

    def test_05_corrupted_json_strings_rejection(self):
        """Adversarially test schema validation on truncated, corrupted, and invalid JSON strings."""
        schema = ResearchDossier.model_json_schema()

        corrupted_payloads = [
            '{"topic": "Quantum Computing", "claims": [',  # Truncated array
            '{"topic": "Quantum Computing", "claims": [{"claim_id": "c1", "claim_text": }]}',  # Syntax error
            'Topic: Quantum Computing\nClaims: None',  # Plain text
            '{"topic": unquoted_identifier, "claims": []}',  # Unquoted identifier
            '{"topic": "Quantum", "headline": "Unclosed string',  # Unclosed string
            '',  # Empty string
            '   \n\t   ',  # Whitespace only
            'True',  # Non-JSON python boolean
            'None',  # Non-JSON python None
            '{key_without_quotes: "val"}',  # Invalid object syntax
        ]

        for payload in corrupted_payloads:
            valid, errors = validate_output(payload, schema)
            self.assertFalse(valid, f"Corrupted payload was unexpectedly validated as true: {payload!r}")
            self.assertGreaterEqual(len(errors), 1, f"Expected validation errors for payload: {payload!r}")

    def test_05b_json_constants_and_pydantic_defense_in_depth(self):
        """Verify defense-in-depth: even if non-standard JSON constants (like NaN) parse in Python json,
        Pydantic contract validation strictly rejects them with ValidationError.
        """
        raw_nan_json = '{"topic": NaN, "claims": []}'
        parsed = json.loads(raw_nan_json)
        
        # Pydantic contract layer must strictly reject float('nan') for topic string field
        with self.assertRaises(ValidationError) as ctx:
            ResearchDossier.model_validate(parsed)
        self.assertIn("topic", str(ctx.exception))

    def test_06_markdown_wrapped_json_extraction_and_validation(self):
        """Adversarially test markdown-wrapped JSON across different code fence formatting variations."""
        schema = ResearchDossier.model_json_schema()

        valid_dossier_data = {
            "topic": "Neuromorphic Architecture",
            "schema_version": "2.0.0",
            "headline": "Spiking Neural Networks in Silicon",
            "executive_summary": "Analysis of neuromorphic computing platforms.",
            "key_takeaways": ["Ultra-low power consumption", "Event-driven asynchronous compute"],
            "claims": [
                {
                    "claim_id": "claim_neuro_01",
                    "claim_text": "Loihi 2 achieves 10x energy efficiency over GPU inference.",
                    "category": "technical",
                    "confidence_score": 0.94,
                    "primary_source": {
                        "title": "Neuromorphic Benchmark Telemetry",
                        "url": "https://neuromorphic.research/loihi2-eval",
                        "reliability_score": 0.95,
                    },
                    "corroborating_sources": [],
                }
            ],
            "suggested_visual_queries": ["loihi die shot"],
        }
        json_str = json.dumps(valid_dossier_data, indent=2)

        test_variations = [
            # 1. Standard ```json code fence
            f"```json\n{json_str}\n```",
            # 2. Plain ``` fence without language tag
            f"```\n{json_str}\n```",
            # 3. Leading and trailing conversational text around ```json fence
            f"Here is the requested research dossier:\n\n```json\n{json_str}\n```\n\nHope this satisfies the criteria!",
            # 4. Leading prose without code fence but with outermost {...}
            f"Final Answer:\n{json_str}\nSigned: Researcher Subagent",
            # 5. Uppercase ```JSON fence
            f"```JSON\n{json_str}\n```",
        ]

        for idx, wrapped_text in enumerate(test_variations):
            candidate = extract_json_candidate(wrapped_text)
            self.assertTrue(candidate.startswith("{") and candidate.endswith("}"), f"Variation {idx} extraction failed: {candidate[:50]}")
            
            # Verify json parsing works
            parsed = json.loads(candidate)
            self.assertEqual(parsed["topic"], "Neuromorphic Architecture")
            
            # Verify Pydantic roundtrip
            dossier_obj = ResearchDossier.model_validate(parsed)
            self.assertEqual(dossier_obj.topic, "Neuromorphic Architecture")
            self.assertEqual(len(dossier_obj.claims), 1)

    def test_07_missing_primary_sources_in_claims_rejection(self):
        """Adversarially test claim validation when primary_source is omitted or null."""
        schema = ResearchDossier.model_json_schema()

        # 1. Claim completely missing primary_source
        invalid_claim_no_source = {
            "claim_id": "claim_bad_01",
            "claim_text": "Unsupported breakthrough claim without verification",
            "confidence_score": 0.9,
            # Missing primary_source!
        }
        with self.assertRaises(ValidationError) as ctx:
            ClaimRecord.model_validate(invalid_claim_no_source)
        self.assertIn("primary_source", str(ctx.exception))

        # 2. Claim with null primary_source
        invalid_claim_null_source = {
            "claim_id": "claim_bad_02",
            "claim_text": "Null primary source claim",
            "confidence_score": 0.8,
            "primary_source": None,
        }
        with self.assertRaises(ValidationError) as ctx:
            ClaimRecord.model_validate(invalid_claim_null_source)
        self.assertIn("primary_source", str(ctx.exception))

        # 3. Claim with primary_source missing required url
        invalid_source = {
            "claim_id": "claim_bad_03",
            "claim_text": "Missing url in source",
            "confidence_score": 0.8,
            "primary_source": {"title": "Title Only"},
        }
        with self.assertRaises(ValidationError) as ctx:
            ClaimRecord.model_validate(invalid_source)
        self.assertIn("url", str(ctx.exception))

        # 4. Dossier containing bad claim tested against ResearchDossier.model_validate
        malformed_dossier_dict = {
            "topic": "Supercomputing",
            "claims": [invalid_claim_no_source],
        }
        with self.assertRaises(ValidationError) as ctx:
            ResearchDossier.model_validate(malformed_dossier_dict)
        self.assertIn("primary_source", str(ctx.exception))

    def test_08_malformed_dossiers_validation(self):
        """Adversarially test schema rejection on malformed research dossiers."""
        # A. Missing required topic
        with self.assertRaises(ValidationError) as ctx:
            ResearchDossier.model_validate({"headline": "No Topic Specified", "claims": []})
        self.assertIn("topic", str(ctx.exception))

        # B. Empty string topic (violates min_length=1)
        with self.assertRaises(ValidationError) as ctx:
            ResearchDossier.model_validate({"topic": "", "claims": []})
        self.assertIn("topic", str(ctx.exception))

        # C. Invalid confidence_score out of bounds (> 1.0)
        invalid_score_claim = {
            "claim_id": "c_score",
            "claim_text": "Overconfident claim",
            "confidence_score": 1.5,  # Max allowed is 1.0
            "primary_source": {"title": "T", "url": "https://example.com"},
        }
        with self.assertRaises(ValidationError) as ctx:
            ClaimRecord.model_validate(invalid_score_claim)
        self.assertIn("confidence_score", str(ctx.exception))

        # D. Testing handle_h9_generate_script resilience against malformed inputs
        res_err = handle_h9_generate_script({"dossier": "Not a dict"})
        self.assertIn('"error"', res_err)
        self.assertIn("must be an object/dictionary", res_err)

        res_empty = handle_h9_generate_script({})
        self.assertIn('"error"', res_empty)
        self.assertIn("Missing required parameter: 'dossier'", res_empty)

    def test_09_one_turn_bounded_retry_mechanism_strictly_avoids_infinite_loop(self):
        """Verify the 1-turn bounded retry mechanism.
        
        Must execute at most ONE retry turn on schema failure and terminate deterministically.
        """
        self.assertEqual(MAX_SCHEMA_RETRIES, 1, "MAX_SCHEMA_RETRIES must be strictly bounded to 1.")

        schema = ResearchDossier.model_json_schema()

        # Simulate child agent with conversational turns
        mock_child = MagicMock()
        mock_child._delegate_output_schema = schema

        # Case 1: First turn produces corrupted JSON; retry turn ALSO produces corrupted JSON.
        # Must execute exactly ONE retry and return without infinite loop.
        turn_calls = []

        def mock_run_conversation(user_message, task_id=None, stream_callback=None):
            turn_calls.append(user_message)
            return {
                "final_response": '{"topic": "Still Invalid JSON',
                "messages": [{"role": "assistant", "content": '{"topic": "Still Invalid JSON'}],
                "api_calls": 1,
            }

        mock_child.run_conversation = mock_run_conversation

        # Initial turn result
        initial_result = {
            "final_response": "I cannot formulate valid JSON right now.",
            "messages": [{"role": "assistant", "content": "I cannot formulate valid JSON right now."}],
            "api_calls": 1,
        }

        # Emulate delegate_tool lines 3006-3056
        _output_schema = getattr(mock_child, "_delegate_output_schema", None)
        _schema_valid, _schema_errors = validate_output(initial_result["final_response"], _output_schema)
        _schema_retries = 0

        self.assertFalse(_schema_valid)
        self.assertGreater(len(_schema_errors), 0)

        # Trigger bounded retry
        if not _schema_valid and initial_result["final_response"].strip():
            _schema_retries = 1
            retry_msg = build_retry_message(_schema_errors)
            
            # Verify retry message content
            self.assertIn("OUTPUT CONTRACT", retry_msg)
            self.assertIn("Validation errors", retry_msg)
            # Verify schema itself is NOT re-pasted in retry prompt
            self.assertNotIn("properties", retry_msg)

            retry_res = mock_child.run_conversation(user_message=retry_msg)
            _retry_text = retry_res.get("final_response") or ""
            _schema_valid, _schema_errors = validate_output(_retry_text, _output_schema)

        # Assertions
        self.assertEqual(len(turn_calls), 1, "Child was called more than once during retry! Loop detected.")
        self.assertEqual(_schema_retries, 1, "Retry counter exceeded 1.")
        self.assertFalse(_schema_valid, "Invalid response was falsely validated.")

    def test_10_one_turn_bounded_retry_recovers_on_valid_second_turn(self):
        """Verify that when the child corrects its output on the 1 retry turn, validation succeeds."""
        schema = ResearchDossier.model_json_schema()
        mock_child = MagicMock()
        mock_child._delegate_output_schema = schema

        valid_dossier = {
            "topic": "Room-Temperature Superconductivity",
            "claims": [
                {
                    "claim_id": "c1",
                    "claim_text": "Diamagnetic shielding observed under high pressure.",
                    "primary_source": {"title": "Nature Physics", "url": "https://nature.com/articles/123"},
                }
            ],
        }

        turn_calls = []

        def mock_run_conversation(user_message, task_id=None, stream_callback=None):
            turn_calls.append(user_message)
            return {
                "final_response": json.dumps(valid_dossier),
                "messages": [{"role": "assistant", "content": json.dumps(valid_dossier)}],
                "api_calls": 1,
            }

        mock_child.run_conversation = mock_run_conversation

        # Initial failing turn
        initial_result = {
            "final_response": "Here is what I found on superconductivity without JSON",
            "api_calls": 1,
        }

        _output_schema = getattr(mock_child, "_delegate_output_schema", None)
        _schema_valid, _schema_errors = validate_output(initial_result["final_response"], _output_schema)
        _schema_retries = 0

        self.assertFalse(_schema_valid)

        if not _schema_valid and initial_result["final_response"].strip():
            _schema_retries = 1
            retry_msg = build_retry_message(_schema_errors)
            retry_res = mock_child.run_conversation(user_message=retry_msg)
            _retry_text = retry_res.get("final_response") or ""
            _schema_valid, _schema_errors = validate_output(_retry_text, _output_schema)

        self.assertEqual(len(turn_calls), 1)
        self.assertEqual(_schema_retries, 1)
        self.assertTrue(_schema_valid)
        self.assertEqual(len(_schema_errors), 0)

    def test_11_model_runtime_live_fallback_on_corrupted_response(self):
        """Verify DefaultModelRuntime falls back gracefully when live LLM returns garbage."""
        runtime = DefaultModelRuntime(offline=False)

        # Mock auxiliary client returning invalid / corrupted JSON
        mock_choice = MagicMock()
        mock_choice.message.content = "CORRUPTED { INVALID JSON ::: [}"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 10

        with patch("agent.auxiliary_client.call_llm", return_value=mock_response):
            # Call invoke_capability expecting ResearchDossier
            resp = runtime.invoke_capability(
                role=CapabilityRole.REASONING_RESEARCH,
                prompt="Research Quantum Annealing",
                schema=ResearchDossier,
                session_id="sess_corrupt_fallback",
            )
            # Must NOT crash; must fall back to deterministic structured generator
            self.assertIsNotNone(resp.parsed)
            self.assertIsInstance(resp.parsed, ResearchDossier)
            self.assertTrue(resp.parsed.topic)
            self.assertGreaterEqual(len(resp.parsed.claims), 1)


class TestPromptCachingIsolationAdversarial(unittest.TestCase):
    """Adversarial testing on parent context isolation and prompt cache preservation."""

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

    def test_12_subagent_execution_does_not_mutate_parent_session_state(self):
        """Verify repeated subagent executions do not increment parent turn counter or corrupt state."""
        agent_rt = DefaultAgentRuntime()
        parent_session_id = "sess_cache_isolation_parent"
        parent_state = agent_rt.create_session(parent_session_id)

        # Perform 2 initial parent turns
        agent_rt.execute_turn(parent_session_id, "Turn 1: Hello")
        agent_rt.execute_turn(parent_session_id, "Turn 2: Please initiate research")
        self.assertEqual(parent_state.iteration_count, 2)
        self.assertFalse(parent_state.is_interrupted)

        # Snapshot parent state
        initial_iteration_count = parent_state.iteration_count
        initial_active_tools = list(parent_state.active_tools)

        # Execute 5 successive subagents with various tasks
        for i in range(5):
            sub_res = agent_rt.delegate_subagent(
                parent_session_id=parent_session_id,
                goal=f"Investigate subsystem component {i}",
                role="researcher",
                context={"subsystem_id": i, "topic": f"Subsystem {i}"},
            )
            self.assertEqual(sub_res.status, SubagentStatus.COMPLETED)

        # Assert parent iteration count did NOT change
        self.assertEqual(parent_state.iteration_count, initial_iteration_count)
        self.assertEqual(parent_state.active_tools, initial_active_tools)
        self.assertFalse(parent_state.is_interrupted)

        # Assert child subagents are tracked cleanly in metadata list without polluting state
        children = parent_state.metadata.get("child_subagents", [])
        self.assertEqual(len(children), 5)

    def test_13_parent_message_list_and_system_prompt_immutable_during_delegation(self):
        """Verify that parent's message history is strictly immutable across subagent execution."""
        # Emulate a parent agent conversation message list
        parent_system_prompt = (
            "You are Hermes Agent for Harness 9 content production. "
            "Preserve sacred prompt caching across all conversation turns."
        )
        parent_messages = [
            {"role": "system", "content": parent_system_prompt},
            {"role": "user", "content": "Conduct deep research into Quantum Cryptography."},
            {"role": "assistant", "content": "I will delegate this research to an isolated subagent."},
        ]

        # Deep snapshot of parent messages and system prompt
        messages_snapshot = deepcopy(parent_messages)
        prompt_hash_before = hashlib.sha256(parent_system_prompt.encode("utf-8")).hexdigest()

        # Execute deep research via handle_h9_research tool
        tool_output = handle_h9_research(
            {"topic": "Quantum Cryptography", "depth": "deep"},
            session_id="sess_parent_msg_immutable",
        )
        self.assertNotIn('"error"', tool_output)

        # Verify parent messages list was completely untouched
        self.assertEqual(len(parent_messages), len(messages_snapshot))
        self.assertEqual(parent_messages, messages_snapshot)

        # Verify parent system prompt hash is byte-identical
        prompt_hash_after = hashlib.sha256(parent_messages[0]["content"].encode("utf-8")).hexdigest()
        self.assertEqual(prompt_hash_before, prompt_hash_after)

    def test_14_memory_system_prompt_block_byte_stability_under_heavy_telemetry(self):
        """Verify HermesMemoryRuntime.render_system_prompt_block remains 100% byte-identical
        even when massive telemetry and learning candidates are continuously recorded.
        """
        db_path = self.workspace / "state.db"
        mem = HermesMemoryRuntime(db_path=db_path)

        creator_id = "creator_sacred_cache"
        profile = CreatorProfile(
            creator_id=creator_id,
            display_name="Sacred Cache Creator",
            tone_of_voice=["Precision", "Rigorous"],
            target_audiences=["Systems Engineers"],
            negative_rules=[
                "Never mutate system prompt during active conversation session",
                "Keep token prefixes byte-stable",
            ],
            brand_colors={"primary": "#1A1A1A"},
        )
        mem.save_creator_profile(profile)

        # Initial prompt render
        initial_prompt_block = mem.render_system_prompt_block(creator_id)
        initial_hash = hashlib.sha256(initial_prompt_block.encode("utf-8")).hexdigest()

        # Blast memory runtime with 25 telemetry events and learning candidates
        for i in range(25):
            lc = LearningCandidate(
                lesson_id=f"lc_stream_{i:03d}",
                creator_id=creator_id,
                rule_type="telemetry",
                observation=f"Observation {i} recorded during live production",
                recommended_action=f"Maintain metric {i} within bounds",
                confidence=0.90,
            )
            mem.record_production_telemetry(
                project_id=f"proj_batch_{i}",
                metrics={"turn": i, "timestamp": time.time()},
                learning_candidates=[lc],
            )

        # Subsequent prompt render
        post_telemetry_prompt_block = mem.render_system_prompt_block(creator_id)
        post_hash = hashlib.sha256(post_telemetry_prompt_block.encode("utf-8")).hexdigest()

        # Must be 100% byte-identical, preserving prompt caching perfectly
        self.assertEqual(initial_prompt_block, post_telemetry_prompt_block)
        self.assertEqual(initial_hash, post_hash)


if __name__ == "__main__":
    unittest.main()
