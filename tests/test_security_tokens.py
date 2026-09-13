"""Unit tests for Harness 9 Security Capability Token Engine & Sandboxing (Milestone M6)."""

import json
from pathlib import Path
import tempfile
import time
import unittest

from src.security.tokens import (
    CapabilityToken,
    SecurityError,
    PermissionDeniedError,
    TokenExpiredError,
    TokenTamperedError,
    PathTraversalError,
    NetworkEgressError,
    DelegationLimitExceededError,
    calculate_capability_token,
    sign_capability_token,
    verify_capability_token,
    create_root_token,
    derive_child_token,
)
from src.security.guard import (
    SecurityGuard,
)


class TestSecurityCapabilityTokens(unittest.TestCase):
    """Exhaustive test suite for capability calculus, HMAC signing, child inheritance, and sandboxing."""

    def setUp(self):
        self.secret_key = "test_super_secret_master_key_9999"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name).resolve()
        self.guard = SecurityGuard(secret_key=self.secret_key)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -----------------------------------------------------------------------
    # 1. Capability Permission Calculus (Intersection Math)
    # -----------------------------------------------------------------------
    def test_01_capability_calculus_intersection(self):
        """Verify P_child = P_parent ∩ P_role ∩ P_workflow."""
        parent_perms = {"read:research", "write:assets", "exec:tts", "exec:render"}
        role_perms = {"read:research", "exec:tts", "exec:audio_qa"}
        workflow_perms = {"exec:tts", "exec:render"}

        child_perms = calculate_capability_token(parent_perms, role_perms, workflow_perms)
        
        self.assertEqual(child_perms, {"exec:tts"})
        self.assertTrue(child_perms.issubset(parent_perms))
        self.assertTrue(child_perms.issubset(role_perms))
        self.assertTrue(child_perms.issubset(workflow_perms))

    def test_02_capability_calculus_disjoint_sets(self):
        """Verify calculus yields empty set when there is zero overlap."""
        parent_perms = {"exec:tts"}
        role_perms = {"read:research"}
        workflow_perms = {"write:assets"}

        child_perms = calculate_capability_token(parent_perms, role_perms, workflow_perms)
        self.assertEqual(child_perms, set())

    def test_03_capability_calculus_wildcard_parent(self):
        """Verify parent wildcard authority inherits intersection of role and workflow."""
        parent_perms = {"*"}
        role_perms = {"tool_search", "tool_fetch", "tool_parse"}
        workflow_perms = {"tool_search", "tool_fetch"}

        child_perms = calculate_capability_token(parent_perms, role_perms, workflow_perms)
        self.assertEqual(child_perms, {"tool_search", "tool_fetch"})

    # -----------------------------------------------------------------------
    # 2. Cryptographic HMAC Signing & Tamper Detection
    # -----------------------------------------------------------------------
    def test_04_hmac_signing_and_verification(self):
        """Verify valid HMAC-SHA256 generation and verification."""
        payload = {"sub": "worker_01", "role": "researcher", "tools": ["search_web"]}
        sig = sign_capability_token(payload, self.secret_key)
        
        self.assertIsInstance(sig, str)
        self.assertEqual(len(sig), 64)
        self.assertTrue(verify_capability_token(payload, sig, self.secret_key))
        self.assertFalse(verify_capability_token(payload, "invalid_signature_hex", self.secret_key))
        self.assertFalse(verify_capability_token(payload, sig, "wrong_secret_key_888"))

    def test_05_token_model_tamper_detection(self):
        """Verify tampering with any token payload attribute invalidates cryptographic signature."""
        token = create_root_token(
            subject_id="agent_orchestrator",
            role="orchestrator",
            workflow_id="wf_1001",
            allowed_tools={"search_web", "synthesize_narration"},
            secret_key=self.secret_key,
        )

        self.assertTrue(token.verify_signature(self.secret_key))
        self.assertIsNotNone(token.signature)

        # Tamper with allowed_tools (privilege escalation attempt)
        token.allowed_tools.add("delete_database")
        self.assertFalse(token.verify_signature(self.secret_key))

        # Tamper with subject_id
        token.allowed_tools.remove("delete_database")
        token.subject_id = "agent_impersonator"
        self.assertFalse(token.verify_signature(self.secret_key))

    # -----------------------------------------------------------------------
    # 3. Root Token Creation & Delegation Hierarchy
    # -----------------------------------------------------------------------
    def test_06_create_root_token(self):
        """Verify creation of root capability token."""
        root = create_root_token(
            subject_id="root_orchestrator",
            workflow_id="wf_root_01",
            allowed_tools={"*"},
            secret_key=self.secret_key,
        )

        self.assertEqual(root.subject_id, "root_orchestrator")
        self.assertEqual(root.role, "orchestrator")
        self.assertEqual(root.delegation_depth, 0)
        self.assertEqual(root.delegation_lineage, [])
        self.assertFalse(root.is_expired())
        self.assertTrue(root.verify_signature(self.secret_key))

    def test_07_derive_child_token_lineage_and_inheritance(self):
        """Verify child token derivation preserves lineage, restricts tools, and increments depth."""
        root = create_root_token(
            subject_id="root_orchestrator",
            workflow_id="wf_prod_01",
            allowed_tools={"search_web", "fetch_url", "generate_tts", "render_video"},
            allowed_write_paths={str(self.base_dir)},
            allowed_network_hosts={"commons.wikimedia.org", "api.elevenlabs.io"},
            secret_key=self.secret_key,
        )

        research_dir = self.base_dir / "research"
        research_dir.mkdir(parents=True, exist_ok=True)

        # Derive Child 1 (Researcher)
        child_researcher = derive_child_token(
            parent_token=root,
            child_subject_id="worker_researcher_01",
            role_allowed_tools={"search_web", "fetch_url"},
            workflow_allowed_tools={"search_web", "fetch_url", "generate_tts"},
            role_allowed_write_paths={str(research_dir)},
            workflow_allowed_write_paths={str(research_dir)},
            role_allowed_network_hosts={"commons.wikimedia.org"},
            child_role="researcher",
            workflow_stage="RESEARCH_IN_PROGRESS",
            secret_key=self.secret_key,
        )

        self.assertEqual(child_researcher.parent_token_id, root.token_id)
        self.assertEqual(child_researcher.delegation_depth, 1)
        self.assertEqual(child_researcher.delegation_lineage, [root.token_id])
        self.assertEqual(child_researcher.allowed_tools, {"search_web", "fetch_url"})
        self.assertEqual(child_researcher.allowed_network_hosts, {"commons.wikimedia.org"})
        self.assertTrue(child_researcher.verify_signature(self.secret_key))

        # Derive Child 2 (Sub-fact-checker from Researcher)
        child_fact_checker = derive_child_token(
            parent_token=child_researcher,
            child_subject_id="worker_fact_check_sub",
            role_allowed_tools={"fetch_url"},
            workflow_allowed_tools={"search_web", "fetch_url"},
            child_role="fact_checker",
            secret_key=self.secret_key,
        )

        self.assertEqual(child_fact_checker.parent_token_id, child_researcher.token_id)
        self.assertEqual(child_fact_checker.delegation_depth, 2)
        self.assertEqual(child_fact_checker.delegation_lineage, [root.token_id, child_researcher.token_id])
        self.assertEqual(child_fact_checker.allowed_tools, {"fetch_url"})

    def test_08_delegation_depth_limit_exceeded(self):
        """Verify exceeding max_delegation_depth raises DelegationLimitExceededError."""
        root = create_root_token(
            subject_id="root",
            workflow_id="wf_depth",
            max_delegation_depth=2,
            secret_key=self.secret_key,
        )

        # Depth 1
        d1 = derive_child_token(root, "d1", {"tool1"}, {"tool1"}, secret_key=self.secret_key)
        self.assertEqual(d1.delegation_depth, 1)

        # Depth 2
        d2 = derive_child_token(d1, "d2", {"tool1"}, {"tool1"}, secret_key=self.secret_key)
        self.assertEqual(d2.delegation_depth, 2)

        # Depth 3 -> Should fail
        with self.assertRaises(DelegationLimitExceededError):
            derive_child_token(d2, "d3", {"tool1"}, {"tool1"}, secret_key=self.secret_key)

    def test_09_expired_parent_token_rejection(self):
        """Verify deriving a child token from an expired parent fails."""
        root = create_root_token(
            subject_id="root_old",
            workflow_id="wf_exp",
            ttl_seconds=0.01,
            secret_key=self.secret_key,
        )
        time.sleep(0.05)

        self.assertTrue(root.is_expired())
        with self.assertRaises(TokenExpiredError):
            derive_child_token(root, "child_late", {"tool1"}, {"tool1"}, secret_key=self.secret_key)

    def test_10_tampered_parent_token_rejection(self):
        """Verify deriving a child token from a tampered parent fails."""
        root = create_root_token(
            subject_id="root_clean",
            workflow_id="wf_tamp",
            secret_key=self.secret_key,
        )
        # Malicious modification
        root.role = "super_admin"

        with self.assertRaises(TokenTamperedError):
            derive_child_token(root, "child_evil", {"tool1"}, {"tool1"}, secret_key=self.secret_key)

    # -----------------------------------------------------------------------
    # 4. Security Guard & Sandbox Enforcement
    # -----------------------------------------------------------------------
    def test_11_guard_tool_whitelisting_enforcement(self):
        """Verify guard permits whitelisted tools and raises PermissionDeniedError for unauthorized tools."""
        token = create_root_token(
            subject_id="worker_tts",
            role="audio_engineer",
            workflow_id="wf_audio",
            allowed_tools={"generate_tts", "analyze_voice_qa"},
            secret_key=self.secret_key,
        )

        # Authorized tools
        self.assertTrue(self.guard.check_tool_execution(token, "generate_tts"))
        self.assertTrue(self.guard.check_tool_execution(token, "analyze_voice_qa"))
        self.guard.enforce_tool_execution(token, "generate_tts")

        # Unauthorized tools
        self.assertFalse(self.guard.check_tool_execution(token, "search_web"))
        self.assertFalse(self.guard.check_tool_execution(token, "delete_project"))
        with self.assertRaises(PermissionDeniedError):
            self.guard.enforce_tool_execution(token, "search_web")

    def test_12_guard_filesystem_path_confinement_and_traversal(self):
        """Verify guard confines file writes to sandbox directory and rejects traversal attacks."""
        sandbox_dir = self.base_dir / "projects" / "p101" / "assets"
        sandbox_dir.mkdir(parents=True, exist_ok=True)

        token = create_root_token(
            subject_id="worker_assets",
            role="asset_manager",
            workflow_id="wf_assets",
            allowed_write_paths={str(sandbox_dir)},
            allowed_read_paths={str(sandbox_dir)},
            secret_key=self.secret_key,
        )

        # Valid write inside sandbox
        valid_file = sandbox_dir / "image.svg"
        self.assertTrue(self.guard.check_filesystem_access(token, valid_file, mode="write"))
        resolved = self.guard.enforce_filesystem_access(token, valid_file, mode="write")
        self.assertEqual(resolved, str(valid_file.resolve()).replace("\\", "/").rstrip("/"))

        # Valid write to nested subfolder
        nested_file = sandbox_dir / "icons" / "icon.png"
        self.assertTrue(self.guard.check_filesystem_access(token, nested_file, mode="write"))

        # Path traversal attack (../ escape attempt)
        escaped_file = sandbox_dir / ".." / ".." / "secret.env"
        self.assertFalse(self.guard.check_filesystem_access(token, escaped_file, mode="write"))
        with self.assertRaises(PathTraversalError):
            self.guard.enforce_filesystem_access(token, escaped_file, mode="write")

        # Absolute unauthorized path
        unauthorized_path = Path("/etc/shadow") if Path("/etc").exists() else Path("C:/Windows/System32")
        self.assertFalse(self.guard.check_filesystem_access(token, unauthorized_path, mode="write"))
        with self.assertRaises(PathTraversalError):
            self.guard.enforce_filesystem_access(token, unauthorized_path, mode="write")

    def test_13_guard_network_egress_enforcement(self):
        """Verify guard enforces network host whitelist and wildcard domains."""
        token = create_root_token(
            subject_id="worker_fetch",
            role="researcher",
            workflow_id="wf_net",
            allowed_network_hosts={"commons.wikimedia.org", "*.pexels.com", "api.nasa.gov"},
            secret_key=self.secret_key,
        )

        # Whitelisted hosts
        self.assertTrue(self.guard.check_network_egress(token, "commons.wikimedia.org"))
        self.assertTrue(self.guard.check_network_egress(token, "api.pexels.com"))
        self.assertTrue(self.guard.check_network_egress(token, "images.pexels.com"))
        self.assertTrue(self.guard.check_network_egress(token, "api.nasa.gov"))
        self.guard.enforce_network_egress(token, "commons.wikimedia.org")

        # Blocked hosts
        self.assertFalse(self.guard.check_network_egress(token, "malicious-hacker.com"))
        self.assertFalse(self.guard.check_network_egress(token, "unauthorized-api.io"))
        with self.assertRaises(NetworkEgressError):
            self.guard.enforce_network_egress(token, "malicious-hacker.com")

    def test_14_guard_context_manager(self):
        """Verify guard_context validates tool, path, and network permissions simultaneously."""
        valid_dir = self.base_dir / "out"
        valid_dir.mkdir(parents=True, exist_ok=True)
        valid_file = valid_dir / "data.json"

        token = create_root_token(
            subject_id="worker_ctx",
            workflow_id="wf_ctx",
            allowed_tools={"query_db"},
            allowed_write_paths={str(valid_dir)},
            allowed_network_hosts={"internal.api"},
            secret_key=self.secret_key,
        )

        # Valid context entry
        with self.guard.guard_context(
            token,
            tool_name="query_db",
            write_paths=[valid_file],
            network_hosts=["internal.api"],
        ) as t:
            self.assertEqual(t.subject_id, "worker_ctx")

        # Invalid tool inside context
        with self.assertRaises(PermissionDeniedError):
            with self.guard.guard_context(token, tool_name="unauthorized_tool"):
                pass

        # Invalid path inside context
        with self.assertRaises(PathTraversalError):
            with self.guard.guard_context(token, write_paths=[self.base_dir / "outside.txt"]):
                pass

    def test_15_guarded_tool_decorator(self):
        """Verify guarded_tool decorator enforces capability token check on decorated function."""
        token = create_root_token(
            subject_id="worker_dec",
            workflow_id="wf_dec",
            allowed_tools={"my_guarded_fn"},
            secret_key=self.secret_key,
        )

        @self.guard.guarded_tool()
        def my_guarded_fn(data: str, token: CapabilityToken) -> str:
            return f"processed: {data}"

        # Valid call
        res = my_guarded_fn("test_input", token=token)
        self.assertEqual(res, "processed: test_input")

        # Disallowed token
        bad_token = create_root_token(
            subject_id="worker_bad",
            workflow_id="wf_dec",
            allowed_tools={"other_fn"},
            secret_key=self.secret_key,
        )
        with self.assertRaises(PermissionDeniedError):
            my_guarded_fn("test_input", token=bad_token)

        # Call without token
        with self.assertRaises(PermissionDeniedError):
            my_guarded_fn("test_input")

    def test_16_token_serialization_round_trip(self):
        """Verify capability token serializes to and from dict and JSON without data loss."""
        token = create_root_token(
            subject_id="worker_serial",
            role="scriptwriter",
            workflow_id="wf_serial_01",
            allowed_tools={"plan_outline", "write_script"},
            allowed_write_paths={str(self.base_dir / "scripts")},
            allowed_read_paths={str(self.base_dir / "dossier")},
            allowed_network_hosts={"api.openai.com"},
            secret_key=self.secret_key,
            metadata={"priority": "high", "tier": 1},
        )

        d = token.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["subject_id"], "worker_serial")
        self.assertEqual(d["metadata"]["priority"], "high")

        # Reconstruct from dict
        reconstructed = CapabilityToken.from_dict(d)
        self.assertEqual(reconstructed.token_id, token.token_id)
        self.assertEqual(reconstructed.allowed_tools, token.allowed_tools)
        self.assertTrue(reconstructed.verify_signature(self.secret_key))


if __name__ == "__main__":
    unittest.main()
