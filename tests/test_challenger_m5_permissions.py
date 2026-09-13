"""Adversarial stress-test suite for Milestone 5 Permission & Capability Token architecture.

Authored by challenger_1_m5.
Tests rigorously challenge:
1. Token Tampering: Tampering with individual fields, payload mutations, corrupted/forged HMAC signatures.
2. Expired Token Replay: Immediate rejection of expired tokens across guard, child derivation, and tools.
3. Privilege Escalation: Enforcement of least-privilege calculus (P_child ⊆ P_parent) preventing tool, path, and host escalation.
4. Deep Lineage Delegation: Bounding by max_delegation_depth, non-delegable tokens, and ancestry tracking.
5. Unauthorized Tool Invocations: Strict 4-tier blocking on h9.render and h9.publish across restricted roles/stages.
6. Dynamic Lineage Revocation: Immediate cascading invalidation down multi-tier delegation trees upon intermediate revocation.
"""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

from src.security.tokens import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    STAGE_PERMISSIONS,
    CapabilityToken,
    SecurityError,
    PermissionDeniedError,
    TokenExpiredError,
    TokenTamperedError,
    TokenValidationError,
    PathTraversalError,
    NetworkEgressError,
    DelegationLimitExceededError,
    TokenRevocationRegistry,
    calculate_capability_token,
    sign_capability_token,
    verify_capability_token,
    create_root_token,
    derive_child_token,
    get_token_revocation_registry,
    reset_token_revocation_registry,
)
from src.security.guard import (
    SecurityGuard,
    current_capability_token,
    get_security_guard,
    reset_security_guard,
)
from tools.h9_content_tools import (
    handle_h9_publish,
    handle_h9_render,
    handle_h9_research,
    handle_h9_generate_script,
    handle_h9_discover_assets,
    resolve_capability_token,
)
from src.h9_runtime import (
    reset_capability_bridges,
)


class TestChallengerM5TokenTampering(unittest.TestCase):
    """Adversarial suite 1: Token Tampering & Cryptographic HMAC-SHA256 Integrity."""

    def setUp(self):
        self.secret_key = "challenger_super_secret_master_key_9999"
        self.attacker_key = "attacker_rogue_secret_key_6666"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            enforce_expiry=True,
            enforce_signatures=True,
            strict_path_confinement=True,
        )
        reset_token_revocation_registry()
        reset_security_guard()

    def tearDown(self):
        reset_token_revocation_registry()
        reset_security_guard()

    def _clone_and_tamper(self, token: CapabilityToken, **kwargs) -> CapabilityToken:
        """Create a new CapabilityToken instance keeping existing signature but altering fields."""
        data = token.to_dict()
        data.update(kwargs)
        return CapabilityToken.from_dict(data)

    def test_01_tamper_token_id_rejected(self):
        """Verify modifying token_id invalidates cryptographic HMAC verification."""
        token = CapabilityToken.create(
            subject_id="worker_research_01",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        self.assertTrue(token.verify_signature(self.secret_key))
        self.assertTrue(self.guard.verify_token(token))

        # Tamper token_id
        tampered = self._clone_and_tamper(token, token_id="root_forged_admin_id")
        self.assertFalse(tampered.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered)

    def test_02_tamper_allowed_tools_privilege_injection_rejected(self):
        """Verify injecting privileged tools (h9.render, h9.publish, *) into signed token fails."""
        token = CapabilityToken.create(
            subject_id="worker_script_01",
            role="scriptwriter",
            allowed_tools={"h9.generate_script"},
            secret_key=self.secret_key,
        )
        self.assertTrue(token.verify_signature(self.secret_key))

        # Attacker injects h9.render and h9.publish
        tampered_tools = set(token.allowed_tools) | {"h9.render", "h9.publish", "*"}
        tampered = self._clone_and_tamper(token, allowed_tools=tampered_tools)
        self.assertFalse(tampered.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered)

    def test_03_tamper_subject_id_impersonation_rejected(self):
        """Verify spoofing subject_id from worker to orchestrator fails signature verification."""
        token = CapabilityToken.create(
            subject_id="unprivileged_worker_7",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        tampered = self._clone_and_tamper(token, subject_id="orchestrator_root_admin")
        self.assertFalse(tampered.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered)

    def test_04_tamper_role_escalation_rejected(self):
        """Verify escalating role attribute from researcher to orchestrator is rejected."""
        token = CapabilityToken.create(
            subject_id="worker_research_02",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        tampered = self._clone_and_tamper(token, role="orchestrator")
        self.assertFalse(tampered.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered)

    def test_05_tamper_expires_at_utc_lifetime_extension_rejected(self):
        """Verify extending expiration timestamp into the far future is rejected."""
        token = CapabilityToken.create(
            subject_id="worker_temp",
            role="researcher",
            allowed_tools={"h9.research"},
            lifetime_seconds=30,
            secret_key=self.secret_key,
        )
        far_future = token.expires_at_utc + 86400.0 * 365
        tampered = self._clone_and_tamper(token, expires_at_utc=far_future)
        self.assertFalse(tampered.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered)

    def test_06_tamper_path_and_network_confinement_rejected(self):
        """Verify expanding allowed_write_paths or allowed_network_hosts is rejected."""
        token = CapabilityToken.create(
            subject_id="worker_confined",
            role="researcher",
            allowed_tools={"h9.research"},
            allowed_write_paths=["/workspace/sandboxed"],
            allowed_network_hosts=["api.harness9.io"],
            secret_key=self.secret_key,
        )
        # Attempt to escape path confinement
        tampered_paths = self._clone_and_tamper(token, allowed_write_paths=["/etc", "/root", "*"])
        self.assertFalse(tampered_paths.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered_paths)

        # Attempt to escape network egress confinement
        tampered_hosts = self._clone_and_tamper(token, allowed_network_hosts=["*", "evil-attacker.com"])
        self.assertFalse(tampered_hosts.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered_hosts)

    def test_07_tamper_delegation_depth_and_lineage_rejected(self):
        """Verify forging delegation_depth or delegation_lineage fails verification."""
        root = CapabilityToken.create(
            subject_id="root_orchestrator",
            role="orchestrator",
            secret_key=self.secret_key,
        )
        child = derive_child_token(
            parent_token=root,
            child_subject_id="child_worker_depth_1",
            secret_key=self.secret_key,
        )
        self.assertEqual(child.delegation_depth, 1)

        # Tamper depth: reset depth from 1 to 0
        tampered_depth = self._clone_and_tamper(child, delegation_depth=0)
        self.assertFalse(tampered_depth.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered_depth)

        # Tamper root depth to 99
        tampered_root_depth = self._clone_and_tamper(root, delegation_depth=99)
        self.assertFalse(tampered_root_depth.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered_root_depth)

        # Forge lineage
        tampered_lineage = self._clone_and_tamper(child, delegation_lineage=["root_fake_ancestor"])
        self.assertFalse(tampered_lineage.verify_signature(self.secret_key))
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered_lineage)

    def test_08_corrupted_signature_and_attacker_key_rejection(self):
        """Verify corrupted signature strings and signatures from unauthorized keys are rejected."""
        token = CapabilityToken.create(
            subject_id="worker_valid",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        original_sig = token.signature

        # Single bit flip in signature
        flipped_sig = ("0" if original_sig[0] != "0" else "1") + original_sig[1:]
        corrupted_token = self._clone_and_tamper(token, signature=flipped_sig)
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(corrupted_token)

        # Non-hex / malformed signature
        malformed_token = self._clone_and_tamper(token, signature="not_a_valid_hex_digest!!")
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(malformed_token)

        # Missing / None signature
        missing_token = self._clone_and_tamper(token, signature=None)
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(missing_token)

        # Signed by attacker key
        attacker_token = CapabilityToken.create(
            subject_id="worker_attacker",
            role="orchestrator",
            allowed_tools={"*"},
            secret_key=self.attacker_key,
        )
        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(attacker_token)

    def test_09_tampered_parent_rejected_during_child_derivation(self):
        """Verify derive_child_token detects and rejects tampered parent token."""
        parent = CapabilityToken.create(
            subject_id="parent_orchestrator",
            role="orchestrator",
            allowed_tools=ROLE_PERMISSIONS["orchestrator"],
            secret_key=self.secret_key,
        )
        # Attacker tampers parent token
        tampered_parent = self._clone_and_tamper(parent, role="researcher")
        with self.assertRaises(TokenTamperedError):
            derive_child_token(
                parent_token=tampered_parent,
                child_subject_id="child_worker",
                secret_key=self.secret_key,
            )


class TestChallengerM5ExpiredTokenReplay(unittest.TestCase):
    """Adversarial suite 2: Expired Token Replay & Lifetime Boundary Enforcement."""

    def setUp(self):
        self.secret_key = "challenger_secret_key_m5_replay"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            enforce_expiry=True,
            enforce_signatures=True,
        )
        reset_token_revocation_registry()
        reset_capability_bridges()

    def tearDown(self):
        reset_token_revocation_registry()
        reset_capability_bridges()

    def test_10_immediate_rejection_of_expired_token(self):
        """Verify tokens past their expiration are rejected immediately by verify_token."""
        now = time.time()
        expired_token = CapabilityToken.create(
            subject_id="expired_agent",
            role="researcher",
            allowed_tools={"h9.research"},
            lifetime_seconds=-10.0,
            secret_key=self.secret_key,
        )
        self.assertTrue(expired_token.is_expired())
        self.assertTrue(expired_token.is_expired(now))

        with self.assertRaises(TokenExpiredError):
            self.guard.verify_token(expired_token)

        with self.assertRaises(TokenExpiredError):
            self.guard.enforce_tool_execution(expired_token, "h9.research")

    def test_11_epsilon_boundary_expiration_checks(self):
        """Verify microsecond boundary sensitivity on token expiration checks."""
        now = time.time()
        # Just expired (0.001s in past)
        just_expired = CapabilityToken.create(
            subject_id="just_expired",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        just_expired.expires_at_utc = now - 0.001
        just_expired.sign(self.secret_key)
        self.assertTrue(just_expired.is_expired(now))

        with self.assertRaises(TokenExpiredError):
            self.guard.verify_token(just_expired)

        # Valid for next 5 seconds
        still_valid = CapabilityToken.create(
            subject_id="still_valid",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        still_valid.expires_at_utc = now + 5.0
        still_valid.sign(self.secret_key)
        self.assertFalse(still_valid.is_expired(now))
        self.assertTrue(self.guard.verify_token(still_valid))

    def test_12_derive_child_from_expired_parent_fails(self):
        """Verify delegating from an expired parent raises TokenExpiredError."""
        expired_parent = CapabilityToken.create(
            subject_id="expired_parent",
            role="orchestrator",
            allowed_tools={"*"},
            lifetime_seconds=-5.0,
            secret_key=self.secret_key,
        )
        with self.assertRaises(TokenExpiredError):
            derive_child_token(
                parent_token=expired_parent,
                child_subject_id="child_worker",
                secret_key=self.secret_key,
            )

    def test_13_replay_expired_token_in_h9_tools_returns_permission_denied(self):
        """Verify replaying an expired token in H9 content tools returns permission_denied."""
        expired_token = CapabilityToken.create(
            subject_id="replayed_expired_token",
            role="orchestrator",
            allowed_tools={"*"},
            lifetime_seconds=-20.0,
            secret_key=self.secret_key,
        )

        # 1. h9.research
        res_res = handle_h9_research(
            {"topic": "quantum computing"},
            capability_token=expired_token,
        )
        data_res = json.loads(res_res)
        self.assertEqual(data_res.get("status"), "error")
        self.assertEqual(data_res.get("error_type"), "permission_denied")

        # 2. h9.render
        res_ren = handle_h9_render(
            {"production_ir": {"scenes": []}, "output_dir": "/tmp"},
            capability_token=expired_token,
        )
        data_ren = json.loads(res_ren)
        self.assertEqual(data_ren.get("status"), "error")
        self.assertEqual(data_ren.get("error_type"), "permission_denied")

        # 3. h9.publish
        res_pub = handle_h9_publish(
            {"project_id": "proj_1", "video_path": "/tmp/v.mp4", "title": "Test"},
            capability_token=expired_token,
        )
        data_pub = json.loads(res_pub)
        self.assertEqual(data_pub.get("status"), "error")
        self.assertEqual(data_pub.get("error_type"), "permission_denied")

        # With raise_on_error=True
        with self.assertRaises(TokenExpiredError):
            handle_h9_research(
                {"topic": "quantum computing"},
                capability_token=expired_token,
                raise_on_error=True,
            )

    def test_14_child_token_lifetime_strictly_bounded_by_parent(self):
        """Verify child token expiration timestamp cannot exceed parent expiration timestamp."""
        now = time.time()
        parent = CapabilityToken.create(
            subject_id="parent_short_lived",
            role="orchestrator",
            allowed_tools={"*"},
            lifetime_seconds=30.0,
            secret_key=self.secret_key,
        )
        # Child requests 1 hour lifetime (3600s)
        child = derive_child_token(
            parent_token=parent,
            child_subject_id="child_long_lived",
            lifetime_seconds=3600.0,
            secret_key=self.secret_key,
        )
        self.assertLessEqual(child.expires_at_utc, parent.expires_at_utc)
        self.assertAlmostEqual(child.expires_at_utc, parent.expires_at_utc, delta=0.5)


class TestChallengerM5PrivilegeEscalation(unittest.TestCase):
    """Adversarial suite 3: Privilege Escalation Prevention (P_child ⊆ P_parent)."""

    def setUp(self):
        self.secret_key = "challenger_secret_privilege_escalation"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            enforce_expiry=True,
            enforce_signatures=True,
        )
        reset_token_revocation_registry()
        reset_capability_bridges()

    def tearDown(self):
        reset_token_revocation_registry()
        reset_capability_bridges()

    def test_15_tool_privilege_escalation_impossible(self):
        """Verify child cannot acquire tools outside parent's granted permissions."""
        parent = CapabilityToken.create(
            subject_id="researcher_parent",
            role="researcher",
            allowed_tools={"h9.research", "web_search"},
            secret_key=self.secret_key,
        )

        # Child tries to request h9.render and h9.publish in both role and workflow sets
        child = derive_child_token(
            parent_token=parent,
            child_subject_id="rogue_child_worker",
            role_allowed_tools={"h9.render", "h9.publish", "h9.research"},
            workflow_allowed_tools={"h9.render", "h9.publish"},
            secret_key=self.secret_key,
        )

        # Intersection: {"h9.research", "web_search"} & {"h9.render", "h9.publish", "h9.research"} & {"h9.render", "h9.publish"} = set()
        self.assertEqual(child.allowed_tools, set())
        self.assertFalse(child.has_tool_permission("h9.render"))
        self.assertFalse(child.has_tool_permission("h9.publish"))
        self.assertTrue(child.allowed_tools.issubset(parent.allowed_tools))

    def test_16_child_role_spoofing_cannot_escalate_beyond_parent(self):
        """Verify child specifying child_role='orchestrator' does not inherit wildcard if parent lacks it."""
        parent = CapabilityToken.create(
            subject_id="restricted_parent",
            role="researcher",
            allowed_tools={"h9.research", "web_search"},
            secret_key=self.secret_key,
        )

        # Child claims to be orchestrator
        child = derive_child_token(
            parent_token=parent,
            child_subject_id="child_claiming_orchestrator",
            child_role="orchestrator",
            secret_key=self.secret_key,
        )

        # Even though orchestrator role default has {"*", ...}, parent only has {"h9.research", "web_search"}
        self.assertTrue(child.allowed_tools.issubset(parent.allowed_tools))
        self.assertNotIn("*", child.allowed_tools)
        self.assertNotIn("h9.render", child.allowed_tools)
        self.assertNotIn("h9.publish", child.allowed_tools)

    def test_17_path_privilege_escalation_impossible(self):
        """Verify child cannot expand write paths beyond parent's path boundaries."""
        parent = CapabilityToken.create(
            subject_id="parent_isolated",
            role="scriptwriter",
            allowed_tools={"h9.generate_script"},
            allowed_write_paths=["/workspace/project_alpha/scripts"],
            secret_key=self.secret_key,
        )

        # Child tries to gain write access to /workspace, /etc, or /
        child = derive_child_token(
            parent_token=parent,
            child_subject_id="child_escaping_jail",
            role_allowed_write_paths=["/workspace", "/etc", "/"],
            secret_key=self.secret_key,
        )

        # Child candidates intersected with parent
        for p in child.allowed_write_paths:
            self.assertTrue(
                p.startswith("/workspace/project_alpha/scripts") or p == "/workspace/project_alpha/scripts",
                f"Path {p} escaped parent confinement!",
            )

    def test_18_network_egress_escalation_impossible(self):
        """Verify child cannot expand allowed_network_hosts beyond parent's whitelist."""
        parent = CapabilityToken.create(
            subject_id="parent_network_gated",
            role="researcher",
            allowed_tools={"h9.research"},
            allowed_network_hosts=["api.harness9.io"],
            secret_key=self.secret_key,
        )

        # Child requests wildcard or untrusted host
        child = derive_child_token(
            parent_token=parent,
            child_subject_id="child_network_escaped",
            role_allowed_network_hosts=["*", "evil.org", "api.harness9.io"],
            secret_key=self.secret_key,
        )

        self.assertNotIn("*", child.allowed_network_hosts)
        self.assertNotIn("evil.org", child.allowed_network_hosts)
        self.assertEqual(child.allowed_network_hosts, {"api.harness9.io"})


class TestChallengerM5DeepLineageDelegation(unittest.TestCase):
    """Adversarial suite 4: Deep Lineage Delegation & Depth Limit Enforcement."""

    def setUp(self):
        self.secret_key = "challenger_secret_deep_delegation"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            enforce_expiry=True,
            enforce_signatures=True,
        )
        reset_token_revocation_registry()

    def tearDown(self):
        reset_token_revocation_registry()

    def test_19_delegation_depth_limit_strictly_enforced(self):
        """Verify token delegation stops precisely at max_delegation_depth."""
        root = CapabilityToken.create(
            subject_id="root_pipeline",
            role="orchestrator",
            max_delegation_depth=2,
            secret_key=self.secret_key,
        )
        self.assertEqual(root.delegation_depth, 0)

        # Depth 1: OK
        child1 = derive_child_token(
            parent_token=root,
            child_subject_id="depth1_agent",
            secret_key=self.secret_key,
        )
        self.assertEqual(child1.delegation_depth, 1)

        # Depth 2: OK
        child2 = derive_child_token(
            parent_token=child1,
            child_subject_id="depth2_agent",
            secret_key=self.secret_key,
        )
        self.assertEqual(child2.delegation_depth, 2)

        # Depth 3: Must raise DelegationLimitExceededError
        with self.assertRaises(DelegationLimitExceededError):
            derive_child_token(
                parent_token=child2,
                child_subject_id="depth3_illegal_agent",
                secret_key=self.secret_key,
            )

    def test_20_zero_depth_root_token_is_non_delegable(self):
        """Verify root token with max_delegation_depth=0 strictly rejects any child derivation."""
        root_non_delegable = CapabilityToken.create(
            subject_id="root_sealed",
            role="orchestrator",
            max_delegation_depth=0,
            secret_key=self.secret_key,
        )
        self.assertEqual(root_non_delegable.delegation_depth, 0)

        with self.assertRaises(DelegationLimitExceededError):
            derive_child_token(
                parent_token=root_non_delegable,
                child_subject_id="child_attempt",
                secret_key=self.secret_key,
            )

    def test_21_lineage_ancestry_chain_integrity(self):
        """Verify 4-generation delegation chain maintains accurate ordered lineage array."""
        root = CapabilityToken.create(
            subject_id="root_gen0",
            role="orchestrator",
            max_delegation_depth=3,
            secret_key=self.secret_key,
        )
        gen1 = derive_child_token(
            parent_token=root,
            child_subject_id="worker_gen1",
            secret_key=self.secret_key,
        )
        gen2 = derive_child_token(
            parent_token=gen1,
            child_subject_id="worker_gen2",
            secret_key=self.secret_key,
        )
        gen3 = derive_child_token(
            parent_token=gen2,
            child_subject_id="worker_gen3",
            secret_key=self.secret_key,
        )

        self.assertEqual(root.delegation_lineage, [])
        self.assertEqual(gen1.delegation_lineage, [root.token_id])
        self.assertEqual(gen2.delegation_lineage, [root.token_id, gen1.token_id])
        self.assertEqual(gen3.delegation_lineage, [root.token_id, gen1.token_id, gen2.token_id])
        self.assertEqual(gen3.parent_token_id, gen2.token_id)
        self.assertEqual(gen3.delegation_depth, 3)

        # Verify all tokens in chain have valid signatures
        self.assertTrue(self.guard.verify_token(root))
        self.assertTrue(self.guard.verify_token(gen1))
        self.assertTrue(self.guard.verify_token(gen2))
        self.assertTrue(self.guard.verify_token(gen3))


class TestChallengerM5UnauthorizedToolInvocations(unittest.TestCase):
    """Adversarial suite 5: Unauthorized Tool Invocations (h9.render, h9.publish)."""

    def setUp(self):
        self.secret_key = "challenger_secret_unauthorized_tools"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            enforce_expiry=True,
            enforce_signatures=True,
        )
        reset_token_revocation_registry()
        reset_capability_bridges()
        reset_security_guard()
        get_security_guard(secret_key=self.secret_key)

    def tearDown(self):
        reset_token_revocation_registry()
        reset_capability_bridges()
        reset_security_guard()

    def test_22_role_researcher_blocked_from_render_and_publish(self):
        """Verify role='researcher' cannot execute h9.render or h9.publish."""
        researcher_token = CapabilityToken.create(
            subject_id="researcher_agent_42",
            role="researcher",
            workflow_stage="research",
            allowed_tools=ROLE_PERMISSIONS["researcher"] & STAGE_PERMISSIONS["research"],
            allowed_write_paths=["*"],
            allowed_read_paths=["*"],
            secret_key=self.secret_key,
        )

        # 1. Calling h9.render
        res_render = handle_h9_render(
            {"production_ir": {"scenes": []}, "output_dir": "/tmp/out"},
            capability_token=researcher_token,
        )
        data_render = json.loads(res_render)
        self.assertEqual(data_render.get("status"), "error")
        self.assertEqual(data_render.get("error_type"), "permission_denied")
        self.assertIn("Permission denied", data_render.get("error", ""))

        with self.assertRaises(PermissionDeniedError):
            handle_h9_render(
                {"production_ir": {"scenes": []}, "output_dir": "/tmp/out"},
                capability_token=researcher_token,
                raise_on_error=True,
            )

        # 2. Calling h9.publish
        res_publish = handle_h9_publish(
            {"project_id": "proj_1", "video_path": "/tmp/vid.mp4", "title": "Vid"},
            capability_token=researcher_token,
        )
        data_publish = json.loads(res_publish)
        self.assertEqual(data_publish.get("status"), "error")
        self.assertEqual(data_publish.get("error_type"), "permission_denied")
        self.assertIn("Permission denied", data_publish.get("error", ""))

        with self.assertRaises(PermissionDeniedError):
            handle_h9_publish(
                {"project_id": "proj_1", "video_path": "/tmp/vid.mp4", "title": "Vid"},
                capability_token=researcher_token,
                raise_on_error=True,
            )

    def test_23_role_scriptwriter_blocked_from_render_and_publish(self):
        """Verify role='scriptwriter' cannot execute h9.render or h9.publish."""
        scriptwriter_token = CapabilityToken.create(
            subject_id="scriptwriter_agent_10",
            role="scriptwriter",
            workflow_stage="scripting",
            allowed_tools=ROLE_PERMISSIONS["scriptwriter"] & STAGE_PERMISSIONS["scripting"],
            allowed_write_paths=["*"],
            allowed_read_paths=["*"],
            secret_key=self.secret_key,
        )

        # h9.render
        res_render = handle_h9_render(
            {"production_ir": {"scenes": []}, "output_dir": "/tmp/out"},
            capability_token=scriptwriter_token,
        )
        data_render = json.loads(res_render)
        self.assertEqual(data_render.get("status"), "error")
        self.assertEqual(data_render.get("error_type"), "permission_denied")

        # h9.publish
        res_publish = handle_h9_publish(
            {"project_id": "proj_1", "video_path": "/tmp/vid.mp4", "title": "Vid"},
            capability_token=scriptwriter_token,
        )
        data_publish = json.loads(res_publish)
        self.assertEqual(data_publish.get("status"), "error")
        self.assertEqual(data_publish.get("error_type"), "permission_denied")

    def test_24_role_video_editor_blocked_from_publish(self):
        """Verify role='video_editor' (has h9.render) is strictly blocked from h9.publish."""
        editor_token = CapabilityToken.create(
            subject_id="editor_agent_03",
            role="video_editor",
            workflow_stage="rendering",
            allowed_tools=ROLE_PERMISSIONS["video_editor"] & STAGE_PERMISSIONS["rendering"],
            allowed_write_paths=["*"],
            allowed_read_paths=["*"],
            secret_key=self.secret_key,
        )

        self.assertTrue(editor_token.has_tool_permission("h9.render"))
        self.assertFalse(editor_token.has_tool_permission("h9.publish"))

        res_publish = handle_h9_publish(
            {"project_id": "proj_1", "video_path": "/tmp/vid.mp4", "title": "Vid"},
            capability_token=editor_token,
        )
        data_publish = json.loads(res_publish)
        self.assertEqual(data_publish.get("status"), "error")
        self.assertEqual(data_publish.get("error_type"), "permission_denied")

    def test_25_stage_restricted_invocations_blocked(self):
        """Verify early lifecycle stages (ideation, research) block privileged tool calls."""
        early_stage_token = CapabilityToken.create(
            subject_id="early_stage_agent",
            role="researcher",
            workflow_stage="RESEARCH_IN_PROGRESS",
            allowed_tools=STAGE_PERMISSIONS["RESEARCH_IN_PROGRESS"],
            secret_key=self.secret_key,
        )

        # Blocked from render
        res_render = handle_h9_render(
            {"production_ir": {"scenes": []}, "output_dir": "/tmp/out"},
            capability_token=early_stage_token,
        )
        self.assertEqual(json.loads(res_render).get("error_type"), "permission_denied")

        # Blocked from publish
        res_publish = handle_h9_publish(
            {"project_id": "p", "video_path": "/tmp/v.mp4", "title": "T"},
            capability_token=early_stage_token,
        )
        self.assertEqual(json.loads(res_publish).get("error_type"), "permission_denied")

    def test_26_contextvar_and_session_binding_token_enforcement(self):
        """Verify ContextVar and session-bound tokens enforce tool execution policies."""
        restricted_token = CapabilityToken.create(
            subject_id="contextvar_researcher",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )

        # 1. Enforced via guard.use_token ContextVar
        guard = get_security_guard()
        with guard.use_token(restricted_token):
            # No explicit token in args, should resolve from ContextVar
            res_render = handle_h9_render(
                {"production_ir": {"scenes": []}, "output_dir": "/tmp/out"}
            )
            data_render = json.loads(res_render)
            self.assertEqual(data_render.get("status"), "error")
            self.assertEqual(data_render.get("error_type"), "permission_denied")

        # 2. Enforced via session token binding
        session_id = "session_adversarial_test_99"
        guard.bind_session_token(session_id, restricted_token)
        try:
            res_publish = handle_h9_publish(
                {"project_id": "p", "video_path": "/tmp/v.mp4", "title": "T"},
                session_id=session_id,
            )
            data_publish = json.loads(res_publish)
            self.assertEqual(data_publish.get("status"), "error")
            self.assertEqual(data_publish.get("error_type"), "permission_denied")
        finally:
            guard.revoke_session_token(session_id)


class TestChallengerM5DynamicLineageRevocation(unittest.TestCase):
    """Adversarial suite 6: Dynamic Lineage Revocation & Multi-Branch Cascading Invalidation."""

    def setUp(self):
        self.secret_key = "challenger_secret_revocation_cascades"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            enforce_expiry=True,
            enforce_signatures=True,
        )
        reset_token_revocation_registry()
        reset_capability_bridges()
        reset_security_guard()
        get_security_guard(secret_key=self.secret_key)

    def tearDown(self):
        reset_token_revocation_registry()
        reset_capability_bridges()
        reset_security_guard()

    def test_27_intermediate_parent_revocation_cascades_down_descendants(self):
        """Verify revoking an intermediate parent invalidates all its child and grandchild tokens."""
        registry = get_token_revocation_registry()

        # Build multi-branch hierarchy:
        # Root
        #  ├── Inter_A
        #  │    └── Child_A1
        #  │         └── Grandchild_A1_sub
        #  └── Inter_B
        #       └── Child_B1
        root = CapabilityToken.create(
            subject_id="root_corp",
            role="orchestrator",
            max_delegation_depth=3,
            secret_key=self.secret_key,
        )
        inter_a = derive_child_token(
            parent_token=root,
            child_subject_id="dept_a_manager",
            secret_key=self.secret_key,
        )
        child_a1 = derive_child_token(
            parent_token=inter_a,
            child_subject_id="team_a1_lead",
            secret_key=self.secret_key,
        )
        grandchild_a1_sub = derive_child_token(
            parent_token=child_a1,
            child_subject_id="worker_a1_leaf",
            secret_key=self.secret_key,
        )

        inter_b = derive_child_token(
            parent_token=root,
            child_subject_id="dept_b_manager",
            secret_key=self.secret_key,
        )
        child_b1 = derive_child_token(
            parent_token=inter_b,
            child_subject_id="worker_b1_leaf",
            secret_key=self.secret_key,
        )

        # Before revocation: all valid
        self.assertFalse(registry.is_revoked(root))
        self.assertFalse(registry.is_revoked(inter_a))
        self.assertFalse(registry.is_revoked(child_a1))
        self.assertFalse(registry.is_revoked(grandchild_a1_sub))
        self.assertFalse(registry.is_revoked(inter_b))
        self.assertFalse(registry.is_revoked(child_b1))

        self.assertTrue(self.guard.verify_token(grandchild_a1_sub))
        self.assertTrue(self.guard.verify_token(child_b1))

        # Revoke INTERMEDIATE parent Inter_A
        registry.revoke(inter_a.token_id, reason="Security audit breach in Dept A")

        # Lineage cascade checks:
        self.assertTrue(registry.is_revoked(inter_a), "Inter_A must be revoked directly")
        self.assertTrue(registry.is_revoked(child_a1), "Child_A1 must be revoked via lineage")
        self.assertTrue(registry.is_revoked(grandchild_a1_sub), "Grandchild_A1 must be revoked via lineage")

        # Root and Branch B must remain UNTOUCHED
        self.assertFalse(registry.is_revoked(root), "Root should not be revoked")
        self.assertFalse(registry.is_revoked(inter_b), "Sibling Branch Inter_B should not be revoked")
        self.assertFalse(registry.is_revoked(child_b1), "Sibling Descendant Child_B1 should not be revoked")

        # Guard enforcement
        with self.assertRaises(TokenValidationError):
            self.guard.verify_token(child_a1)

        with self.assertRaises(TokenValidationError):
            self.guard.verify_token(grandchild_a1_sub)

        # Sibling branch remains completely functional
        self.assertTrue(self.guard.verify_token(child_b1))

    def test_28_derivation_from_revoked_ancestor_rejected(self):
        """Verify attempting derive_child_token from a revoked token or its descendant fails."""
        registry = get_token_revocation_registry()
        root = CapabilityToken.create(
            subject_id="root_delegator",
            role="orchestrator",
            secret_key=self.secret_key,
        )
        child = derive_child_token(
            parent_token=root,
            child_subject_id="child_delegator",
            secret_key=self.secret_key,
        )

        registry.revoke(root.token_id, reason="Revoking root")

        # Derivation from root fails
        with self.assertRaises(TokenValidationError):
            derive_child_token(
                parent_token=root,
                child_subject_id="new_child_fail",
                secret_key=self.secret_key,
            )

        # Derivation from child fails because root ancestor is revoked
        with self.assertRaises(TokenValidationError):
            derive_child_token(
                parent_token=child,
                child_subject_id="grandchild_fail",
                secret_key=self.secret_key,
            )

    def test_29_tool_invocations_with_revoked_token_immediately_blocked(self):
        """Verify H9 content tools reject calls made with revoked capability tokens."""
        registry = get_token_revocation_registry()
        root = CapabilityToken.create(
            subject_id="root_active",
            role="orchestrator",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        researcher_token = derive_child_token(
            parent_token=root,
            child_subject_id="research_agent_active",
            child_role="researcher",
            secret_key=self.secret_key,
        )

        # Revoke root
        registry.revoke(root.token_id, reason="Emergency revocation")

        # Handler invocation should catch TokenValidationError and return permission_denied
        res = handle_h9_research(
            {"topic": "artificial intelligence safety"},
            capability_token=researcher_token,
        )
        data = json.loads(res)
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("error_type"), "permission_denied")
        self.assertIn("revoked", data.get("error", "").lower())

        with self.assertRaises(TokenValidationError):
            handle_h9_research(
                {"topic": "artificial intelligence safety"},
                capability_token=researcher_token,
                raise_on_error=True,
            )

    def test_30_revocation_registry_metadata_and_clear(self):
        """Verify revocation metadata retrieval and registry clearing semantics."""
        registry = get_token_revocation_registry()
        token_id = "cap_revocation_meta_test"

        registry.revoke(token_id, reason="compromised_private_key")
        info = registry.get_revocation_info(token_id)
        self.assertIsNotNone(info)
        self.assertEqual(info.get("reason"), "compromised_private_key")
        self.assertIn("revoked_at_utc", info)

        self.assertTrue(registry.is_revoked(token_id))

        # Clear
        registry.clear()
        self.assertFalse(registry.is_revoked(token_id))
        self.assertIsNone(registry.get_revocation_info(token_id))


if __name__ == "__main__":
    unittest.main()
