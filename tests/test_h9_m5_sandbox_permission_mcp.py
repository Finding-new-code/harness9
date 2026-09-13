"""Comprehensive test suite for Milestone 5 (Sandbox, Permission & MCP Integration).

Validates:
- R5.1 Execution Sandboxing:
  - HermesExecutionRuntime wrapping Hermes BaseEnvironment (Local, Docker, Modal)
  - Dynamic environment resolution (resolve_environment)
  - Subprocess execution, exit code capture, process group timeout kill (exit code 124)
  - Filesystem jail path confinement & traversal rejection
  - HyperFrames rendering subprocesses routed through Hermes sandbox
  - Sandboxed media downloads (download_stream_sandboxed) with byte capping
  - Docker shm-size=1g container configuration

- R5.2 Capability Token Boundary & Tool Gating:
  - Principle of least privilege token derivation calculus:
    P_child = P_parent ∩ P_role ∩ P_workflow
  - Monotonic path restriction and token lifetime bounding
  - Cryptographic HMAC-SHA256 signature verification & tampering detection
  - Token expiration detection
  - Thread-safe TokenRevocationRegistry with real-time cascading lineage invalidation
  - 4-Tier tool gating on h9.render and h9.publish across handlers, bridge, and roles
  - h9.publish tool execution & publication manifest export
  - ContextVar token propagation

- R5.3 Hermes MCP Integration:
  - MCP tool discovery across connected servers
  - Dynamic MCP tool registration & schema reflection
  - Dynamic tool invocation with parameter passing
  - Connection status reporting (get_mcp_status)
"""

import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from src.h9_runtime import (
    HermesCapabilityBridge,
    get_capability_bridge,
    reset_capability_bridges,
)
from src.h9_runtime.execution import (
    DefaultExecutionRuntime,
    HermesExecutionRuntime,
    resolve_environment,
)
from src.h9_runtime.tools import (
    DefaultToolRuntime,
    ToolDefinition,
    ToolInvocationContext,
)
from src.h9_runtime.types import ExecutionResult
from src.hyperframes.renderer import HyperFramesRenderer, RenderResult
from src.assets.freezer import download_stream_sandboxed
from src.security.tokens import (
    CapabilityToken,
    DelegationLimitExceededError,
    NetworkEgressError,
    PathTraversalError,
    PermissionDeniedError,
    ROLE_PERMISSIONS,
    STAGE_PERMISSIONS,
    SecurityError,
    TokenExpiredError,
    TokenRevocationRegistry,
    TokenTamperedError,
    TokenValidationError,
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
    H9_PUBLISH_SCHEMA,
    handle_h9_publish,
    handle_h9_render,
    handle_h9_research,
)
from tools.registry import registry


class TestR51ExecutionSandboxing(unittest.TestCase):
    """Verify HermesExecutionRuntime, BaseEnvironment integration, and subprocess routing."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="h9_test_m5_sandbox_")
        self.sandbox_dir = Path(self.temp_dir) / "sandbox"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.runtime = HermesExecutionRuntime(
            session_id="test_m5_session",
            base_dir=self.sandbox_dir,
            env_type="local",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_hermes_execution_runtime_init_and_env_resolution(self):
        """Verify HermesExecutionRuntime initializes BaseEnvironment cleanly and resolves environments."""
        self.assertEqual(self.runtime.session_id, "test_m5_session")
        self.assertEqual(self.runtime.base_dir, self.sandbox_dir.resolve())
        self.assertIsNotNone(self.runtime.env)

        # resolve_environment for local
        local_env = resolve_environment("local", cwd=str(self.sandbox_dir))
        self.assertIsNotNone(local_env)

        # Fallback to local on unknown environment
        fallback_env = resolve_environment("unsupported_backend_xyz", cwd=str(self.sandbox_dir))
        self.assertIsNotNone(fallback_env)

    def test_02_command_execution_success(self):
        """Verify command execution returns output and zero exit code."""
        # Run standard python command
        result = self.runtime.execute_command(["python", "-c", "print('hello_sandbox_m5')"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello_sandbox_m5", result.stdout)
        self.assertGreater(result.duration_seconds, 0.0)

    def test_03_command_timeout_kill(self):
        """Verify process group timeout terminates long running command with exit code 124."""
        # Execute a command that sleeps longer than timeout_seconds
        result = self.runtime.execute_command(
            ["python", "-c", "import time; time.sleep(5)"],
            timeout_seconds=1.0,
        )
        self.assertEqual(result.exit_code, 124)
        self.assertIn("timed out", result.stderr.lower())

    def test_04_path_confinement_and_traversal_rejection(self):
        """Verify validate_path strictly rejects directory escape and traversal."""
        valid_file = self.runtime.session_root / "data.txt"
        valid_file.write_text("ok", encoding="utf-8")

        resolved = self.runtime.validate_path("data.txt")
        self.assertEqual(resolved, valid_file.resolve())

        # Attempt directory escape via ../
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.validate_path("../outside.txt")

        # Attempt escape via deep relative traversal
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.validate_path("subdir/../../../../etc/passwd")

        # Attempt null byte injection
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.validate_path("data.txt\0evil.py")

    def test_05_sandboxed_file_read_write(self):
        """Verify write_file and read_file operate atomically within jail and reject outside writes."""
        target_rel = "output/test.json"
        content = json.dumps({"key": "value_m5"})
        written_path = self.runtime.write_file(target_rel, content)
        self.assertTrue(written_path.exists())

        read_content = self.runtime.read_file(target_rel)
        self.assertEqual(read_content, content)

        # Attempt write outside sandbox
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.write_file("../outside.json", "illegal")

        # Attempt read outside sandbox
        with self.assertRaises((PathTraversalError, ValueError)):
            self.runtime.read_file("../../outside.json")

    def test_06_hyperframes_renderer_sandboxed_execution(self):
        """Verify HyperFramesRenderer routes subprocess execution through HermesExecutionRuntime."""
        proj_dir = Path(self.temp_dir) / "hyperframes_proj"
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "index.html").write_text(
            "<html><head><meta name='viewport' content='width=1920,height=1080'/></head><body>Render Test</body></html>",
            encoding="utf-8",
        )

        mock_execution = MagicMock(spec=HermesExecutionRuntime)
        mock_execution.execute_command.return_value = ExecutionResult(
            exit_code=0, stdout="Mocked node render", stderr="", duration_seconds=0.1
        )
        mock_execution.validate_path.side_effect = lambda p: Path(p).resolve()

        renderer = HyperFramesRenderer(
            fps=30,
            quality="standard",
            execution_runtime=mock_execution,
        )

        with patch("src.hyperframes.renderer.is_ffmpeg_available", return_value=True), \
             patch("src.hyperframes.renderer.probe_media_file", return_value={"has_video": True, "has_audio": True, "duration": 5.0, "width": 1920, "height": 1080, "fps": 30.0}), \
             patch("src.hyperframes.renderer.render_video_with_ffmpeg") as mock_ffmpeg_render:
            
            # Setup output file for render mock
            final_mp4 = proj_dir / "renders" / "final.mp4"
            final_mp4.parent.mkdir(parents=True, exist_ok=True)
            final_mp4.write_bytes(b"\x00\x00\x00\x1cftypisom")
            mock_ffmpeg_render.return_value = (True, str(final_mp4), "OK")

            res = renderer.render(
                project_dir=proj_dir,
                output_mp4=final_mp4,
                duration=5.0,
            )

            self.assertIsInstance(res, RenderResult)
            self.assertIn(res.validation_status, ("VERIFIED", "WARNINGS"))
            # Verify that mock_execution was passed to render_video_with_ffmpeg
            mock_ffmpeg_render.assert_called_once()
            _, kwargs = mock_ffmpeg_render.call_args
            self.assertEqual(kwargs.get("execution_runtime"), mock_execution)

    def test_07_sandboxed_media_download_stream(self):
        """Verify download_stream_sandboxed enforces size caps and rejects path traversal."""
        dest_inside = self.runtime.session_root / "assets" / "downloaded.svg"
        
        # Test download inside sandbox
        mock_content = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [mock_content, b""]
            mock_url.return_value.__enter__.return_value = mock_resp

            written, sha, size, mtype = download_stream_sandboxed(
                url="https://example.com/asset.svg",
                target_path=dest_inside,
                execution_runtime=self.runtime,
                max_size_bytes=1024 * 1024,
            )
            self.assertEqual(written, dest_inside)
            self.assertTrue(dest_inside.exists())

        # Test download outside sandbox raises PathTraversalError
        dest_outside = Path(self.temp_dir) / "outside.svg"
        with self.assertRaises((PathTraversalError, ValueError)):
            download_stream_sandboxed(
                url="https://example.com/asset.svg",
                target_path=dest_outside,
                execution_runtime=self.runtime,
            )

        # Test exceeding max_bytes
        large_content = b"x" * 1000
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [large_content, b""]
            mock_url.return_value.__enter__.return_value = mock_resp

            with self.assertRaises(ValueError):
                download_stream_sandboxed(
                    url="https://example.com/asset.svg",
                    target_path=self.runtime.session_root / "too_large.bin",
                    execution_runtime=self.runtime,
                    max_size_bytes=500,
                )

    def test_08_docker_shm_size_configuration(self):
        """Verify DockerEnvironment is configured with shm_size='1g' for video rendering."""
        with patch("tools.environments.docker.DockerEnvironment") as mock_docker_cls:
            mock_instance = MagicMock()
            mock_docker_cls.return_value = mock_instance

            env = resolve_environment("docker", cwd=str(self.sandbox_dir))
            mock_docker_cls.assert_called_once()
            _, kwargs = mock_docker_cls.call_args
            self.assertEqual(kwargs.get("shm_size"), "1g")


class TestR52CapabilityTokenBoundaryAndToolGating(unittest.TestCase):
    """Verify CapabilityToken least-privilege derivation, revocation, and 4-tier tool gating."""

    def setUp(self):
        self.secret_key = "test_m5_secret_key_super_secure"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            enforce_expiry=True,
            enforce_signatures=True,
            strict_path_confinement=True,
        )
        reset_token_revocation_registry()
        reset_capability_bridges()

    def tearDown(self):
        reset_token_revocation_registry()
        reset_capability_bridges()

    def test_01_least_privilege_derivation_calculus(self):
        """Verify P_child = P_parent ∩ P_role ∩ P_workflow with monotonic path restrictions."""
        parent_token = CapabilityToken.create(
            subject_id="orchestrator_root",
            role="orchestrator",
            workflow_stage="full_production",
            allowed_tools=ROLE_PERMISSIONS["orchestrator"],
            allowed_read_paths=["/workspace"],
            allowed_write_paths=["/workspace/output"],
            secret_key=self.secret_key,
            lifetime_seconds=3600,
        )

        # Derive child token for researcher
        child_token = derive_child_token(
            parent_token=parent_token,
            child_subject_id="researcher_subagent_01",
            child_role="researcher",
            child_workflow_stage="research",
            secret_key=self.secret_key,
            lifetime_seconds=1800,
        )

        # Invariant 1: Permissions intersection
        expected_perms = (
            parent_token.allowed_tools
            & ROLE_PERMISSIONS["researcher"]
            & STAGE_PERMISSIONS["research"]
        )
        self.assertEqual(child_token.allowed_tools, expected_perms)

        # Researcher must NOT have render or publish tools
        self.assertFalse(child_token.has_tool_permission("h9.render"))
        self.assertFalse(child_token.has_tool_permission("h9.publish"))
        self.assertTrue(child_token.has_tool_permission("h9.research"))

        # Invariant 2: Monotonic path restriction
        self.assertTrue(child_token.allowed_write_paths.issubset(parent_token.allowed_write_paths))

        # Invariant 3: Expiration monotonicity
        self.assertLessEqual(child_token.expires_at_utc, parent_token.expires_at_utc)

        # Invariant 4: Lineage tracking
        self.assertEqual(child_token.parent_token_id, parent_token.token_id)
        self.assertIn(parent_token.token_id, child_token.delegation_lineage)

    def test_02_signature_tampering_detection(self):
        """Verify token signature verification rejects payload alterations."""
        token = CapabilityToken.create(
            subject_id="worker_01",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
        )
        self.assertTrue(self.guard.verify_token(token))

        # Tamper with allowed_tools to illicitly add h9.render
        tampered_tools = set(token.allowed_tools) | {"h9.render"}
        tampered_token = CapabilityToken(
            token_id=token.token_id,
            subject_id=token.subject_id,
            role=token.role,
            workflow_stage=token.workflow_stage,
            allowed_tools=tampered_tools,
            allowed_read_paths=token.allowed_read_paths,
            allowed_write_paths=token.allowed_write_paths,
            allowed_network_hosts=token.allowed_network_hosts,
            issued_at_utc=token.issued_at_utc,
            expires_at_utc=token.expires_at_utc,
            signature=token.signature,  # Stale signature over old payload
        )

        with self.assertRaises(TokenTamperedError):
            self.guard.verify_token(tampered_token)

    def test_03_token_expiration_detection(self):
        """Verify expired tokens are rejected by SecurityGuard."""
        expired_token = CapabilityToken.create(
            subject_id="expired_worker",
            role="researcher",
            allowed_tools={"h9.research"},
            secret_key=self.secret_key,
            lifetime_seconds=-10,  # Already expired
        )
        with self.assertRaises(TokenExpiredError):
            self.guard.verify_token(expired_token)

    def test_04_token_revocation_registry_and_cascading_lineage(self):
        """Verify revoking an ancestor token invalidates all derived descendant tokens."""
        registry = get_token_revocation_registry()

        root_token = CapabilityToken.create(
            subject_id="root_pipeline",
            role="orchestrator",
            allowed_tools=ROLE_PERMISSIONS["orchestrator"],
            secret_key=self.secret_key,
        )
        child_token = derive_child_token(
            parent_token=root_token,
            child_subject_id="editor_subagent",
            child_role="editor",
            secret_key=self.secret_key,
        )
        grandchild_token = derive_child_token(
            parent_token=child_token,
            child_subject_id="render_worker",
            child_role="editor",
            secret_key=self.secret_key,
        )

        # Before revocation, all tokens valid
        self.assertFalse(registry.is_revoked(root_token))
        self.assertFalse(registry.is_revoked(child_token))
        self.assertFalse(registry.is_revoked(grandchild_token))
        self.assertTrue(self.guard.verify_token(grandchild_token))

        # Revoke the root token
        registry.revoke(root_token.token_id, reason="Security compromise")

        # Immediate cascading invalidation across lineage
        self.assertTrue(registry.is_revoked(root_token))
        self.assertTrue(registry.is_revoked(child_token))
        self.assertTrue(registry.is_revoked(grandchild_token))

        with self.assertRaises(TokenValidationError):
            self.guard.verify_token(grandchild_token)

        # Attempting to derive a child from a revoked parent must fail
        with self.assertRaises(TokenValidationError):
            derive_child_token(
                parent_token=root_token,
                child_subject_id="new_child",
                child_role="researcher",
                secret_key=self.secret_key,
            )

    def test_05_four_tier_tool_gating_researcher_blocked_from_render_and_publish(self):
        """Verify Researcher role is strictly blocked from calling h9.render and h9.publish."""
        researcher_token = CapabilityToken.create(
            subject_id="researcher_agent",
            role="researcher",
            workflow_stage="research",
            allowed_tools=ROLE_PERMISSIONS["researcher"] & STAGE_PERMISSIONS["research"],
            allowed_write_paths=["*"],
            allowed_read_paths=["*"],
            secret_key=self.secret_key,
        )

        # 1. Tier 3 Handler check on h9.render
        res_render = handle_h9_render(
            {"project_id": "test_proj"},
            capability_token=researcher_token,
        )
        data_render = json.loads(res_render)
        self.assertEqual(data_render.get("status"), "error")
        self.assertEqual(data_render.get("error_type"), "permission_denied")

        with self.assertRaises(PermissionDeniedError):
            handle_h9_render(
                {"project_id": "test_proj"},
                capability_token=researcher_token,
                raise_on_error=True,
            )

        # 2. Tier 3 Handler check on h9.publish
        res_publish = handle_h9_publish(
            {
                "project_id": "test_proj",
                "video_path": "final.mp4",
                "title": "Blocked Publication",
            },
            capability_token=researcher_token,
        )
        data_publish = json.loads(res_publish)
        self.assertEqual(data_publish.get("status"), "error")
        self.assertEqual(data_publish.get("error_type"), "permission_denied")

        with self.assertRaises(PermissionDeniedError):
            handle_h9_publish(
                {
                    "project_id": "test_proj",
                    "video_path": "final.mp4",
                    "title": "Blocked Publication",
                },
                capability_token=researcher_token,
                raise_on_error=True,
            )

        # 3. Tier 4 Bridge check on render_video & publish
        bridge = get_capability_bridge(session_id="researcher_sess")
        with self.assertRaises(PermissionDeniedError):
            bridge.render_video(
                ir={"project_id": "test_proj"},
                capability_token=researcher_token,
            )

        with self.assertRaises(PermissionDeniedError):
            bridge.publish(
                project_id="test_proj",
                video_path="final.mp4",
                capability_token=researcher_token,
            )

    def test_06_editor_and_publisher_authorized_execution(self):
        """Verify Editor can render and Publisher can publish when granted appropriate tokens."""
        editor_token = CapabilityToken.create(
            subject_id="editor_agent",
            role="editor",
            workflow_stage="assembly",
            allowed_tools=ROLE_PERMISSIONS["editor"] & STAGE_PERMISSIONS["assembly"],
            allowed_write_paths=["*"],
            allowed_read_paths=["*"],
            secret_key=self.secret_key,
        )
        publisher_token = CapabilityToken.create(
            subject_id="publisher_agent",
            role="publisher",
            workflow_stage="distribution",
            allowed_tools=ROLE_PERMISSIONS["publisher"] & STAGE_PERMISSIONS["distribution"],
            allowed_write_paths=["*"],
            allowed_read_paths=["*"],
            secret_key=self.secret_key,
        )

        # Editor has h9.render but NOT h9.publish
        self.assertTrue(editor_token.has_tool_permission("h9.render"))
        self.assertFalse(editor_token.has_tool_permission("h9.publish"))

        # Publisher has h9.publish but NOT h9.render
        self.assertTrue(publisher_token.has_tool_permission("h9.publish"))
        self.assertFalse(publisher_token.has_tool_permission("h9.render"))

        # Publisher executes publish
        bridge = get_capability_bridge(session_id="publisher_sess")
        pub_result = bridge.publish(
            project_id="proj_m5_published",
            video_path="renders/final.mp4",
            title="Milestone 5 Broadcast",
            platforms=["youtube", "local_export"],
            capability_token=publisher_token,
        )
        self.assertEqual(pub_result["status"], "PUBLISHED")
        self.assertEqual(pub_result["project_id"], "proj_m5_published")
        self.assertIn("youtube", pub_result["platforms"])

    def test_07_contextvar_token_propagation(self):
        """Verify ContextVar current_capability_token propagates automatically through SecurityGuard."""
        token = CapabilityToken.create(
            subject_id="scoped_session_worker",
            role="publisher",
            allowed_tools={"h9.publish"},
            allowed_read_paths=["*"],
            allowed_write_paths=["*"],
            secret_key=self.secret_key,
        )

        self.assertIsNone(current_capability_token.get())

        with self.guard.use_token(token):
            self.assertEqual(current_capability_token.get(), token)
            # Bridge calls without explicit token pick up the active context token
            bridge = get_capability_bridge(session_id="context_sess")
            res = bridge.publish(
                project_id="context_proj",
                video_path="vid.mp4",
                title="Context Var Publication",
            )
            self.assertEqual(res["status"], "PUBLISHED")

        # Context reverts cleanly upon exit
        self.assertIsNone(current_capability_token.get())


class TestR53HermesMCPIntegration(unittest.TestCase):
    """Verify Hermes MCP tool discovery, dynamic registration, status, and invocation."""

    def setUp(self):
        self.tool_runtime = DefaultToolRuntime()
        self.bridge = HermesCapabilityBridge(
            session_id="test_mcp_session",
            tool_runtime=self.tool_runtime,
        )

    def test_01_mcp_status_reporting(self):
        """Verify get_mcp_status returns structured server registry information."""
        status = self.bridge.get_mcp_status()
        self.assertIn("servers", status)
        self.assertIn("total_servers", status)
        self.assertIn("total_tools", status)
        self.assertIsInstance(status["servers"], dict)

    def test_02_dynamic_mcp_tool_registration_and_discovery(self):
        """Verify registering dynamic MCP tools allows discovery and schema exposure."""
        def mock_query_handler(args: dict, **kwargs) -> str:
            return f"Processed query: {args.get('q')}"

        self.bridge.register_mcp_tool(
            server_name="literature_server",
            name="mcp.query_papers",
            description="Query academic research papers via MCP",
            parameters={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Search query"},
                },
                "required": ["q"],
            },
            handler=mock_query_handler,
        )

        # Discover tools
        tools = self.bridge.discover_mcp_tools()
        mcp_names = [t.name for t in tools]
        self.assertIn("mcp.query_papers", mcp_names)

        # Verify server filtering
        lit_tools = self.bridge.discover_mcp_tools(server_name="literature_server")
        self.assertEqual(len(lit_tools), 1)
        self.assertEqual(lit_tools[0].name, "mcp.query_papers")

        other_tools = self.bridge.discover_mcp_tools(server_name="nonexistent_server")
        self.assertEqual(len(other_tools), 0)

        # Verify tool schemas reflect registered MCP tool
        schemas = self.bridge.get_tool_schemas()
        schema_names = [s.get("name") for s in schemas]
        self.assertIn("mcp.query_papers", schema_names)

    def test_03_dynamic_mcp_tool_invocation(self):
        """Verify dynamic MCP tool invocation passes arguments and returns results."""
        def mock_echo(args: dict, **kwargs) -> str:
            val = args.get("val", "")
            return f"ECHO:{val}"

        self.bridge.register_mcp_tool(
            server_name="echo_server",
            name="mcp.echo",
            description="Echo back input",
            parameters={"type": "object", "properties": {"val": {"type": "string"}}},
            handler=mock_echo,
        )

        res = self.bridge.invoke_mcp_tool("mcp.echo", {"val": "Hermes_Harness9_M5"})
        self.assertEqual(res, "ECHO:Hermes_Harness9_M5")

    def test_04_mcp_error_handling_for_unknown_tools(self):
        """Verify calling unregistered MCP tools raises ValueError."""
        with self.assertRaises(ValueError):
            self.bridge.invoke_mcp_tool("mcp.nonexistent_tool", {})


if __name__ == "__main__":
    unittest.main()
