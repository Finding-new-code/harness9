"""tests/test_challenger_m5_sandbox_mcp.py

Adversarial Stress Test Suite for Milestone 5 (Sandbox, Permission & MCP Integration).
Authored by challenger_2_m5 to empirically stress-test:
1. Path Traversal Attacks:
   - Relative upward traversals (../../sensitive_file, sub/../../etc)
   - Absolute system root escapes (C:\\Windows\\System32, /etc/passwd)
   - Null-byte injection and unquoted URL-encoded traversals
   - Path confinement enforcement across validate_path, download_stream_sandboxed,
     read_file, write_file, handle_h9_render, and handle_h9_publish.
2. Subprocess Timeout Stress:
   - Hanging infinite sleep commands terminating with exit code 124
   - Stderr populated with timeout diagnostics
   - Process tree termination ensuring zero orphaned background processes
   - Rapid back-to-back timeout cycles without resource leakage
3. Asset Stream Size Limits:
   - Premature termination on oversized Content-Length header
   - Chunked streaming exceeding max_bytes raising AssetSizeExceededError before OOM
   - Sandboxed streaming download enforcing byte bounds
   - AssetFreezer atomic freezing size cap verification
4. MCP Discovery & Execution Robustness:
   - Empty and unknown server discovery
   - Edge-case tool naming, minimal schemas, and server filtering
   - Malformed argument validation (missing required, type mismatches including bool/int)
   - Unregistered tool invocation and exception containment without crashing
"""

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
import urllib.parse
from unittest.mock import MagicMock, patch
import psutil

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
from src.assets.freezer import (
    AssetDownloadError,
    AssetFreezer,
    AssetSizeExceededError,
    download_stream,
    download_stream_sandboxed,
)
from src.security.tokens import (
    CapabilityToken,
    PathTraversalError,
    PermissionDeniedError,
    SecurityError,
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
)


class TestAdversarialPathTraversal(unittest.TestCase):
    """Adversarial stress testing against filesystem boundaries and path traversal."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="h9_challenger_m5_traversal_")
        self.sandbox_dir = Path(self.temp_dir) / "jail"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.secret_file = Path(self.temp_dir) / "sensitive_outside.txt"
        self.secret_file.write_text("SUPER_SECRET_CREDENTIALS", encoding="utf-8")

        self.runtime = HermesExecutionRuntime(
            session_id="traversal_session",
            base_dir=self.sandbox_dir,
            env_type="local",
        )
        self.secret_key = "adversarial_test_secret_key"
        self.guard = SecurityGuard(
            secret_key=self.secret_key,
            strict_path_confinement=True,
        )
        reset_token_revocation_registry()
        reset_capability_bridges()

    def tearDown(self):
        reset_token_revocation_registry()
        reset_capability_bridges()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_validate_path_relative_traversals(self):
        """Verify relative traversal variants escaping sandbox root are rejected with PathTraversalError."""
        attack_paths = [
            "../../sensitive_outside.txt",
            "subdir/../../sensitive_outside.txt",
            "nested/sub/../../../sensitive_outside.txt",
            "..\\..\\sensitive_outside.txt",
            "subdir/..\\../sensitive_outside.txt",
            urllib.parse.unquote("%2e%2e%2f%2e%2e%2fsensitive_outside.txt"),
            os.path.join("..", "..", "sensitive_outside.txt"),
        ]
        for bad_path in attack_paths:
            with self.subTest(bad_path=bad_path):
                with self.assertRaises(PathTraversalError, msg=f"Should reject traversal: {bad_path}"):
                    self.runtime.validate_path(bad_path)

    def test_02_validate_path_absolute_root_escapes(self):
        """Verify absolute root paths outside sandbox session root are rejected."""
        if os.name == "nt":
            bad_roots = [
                "C:\\Windows\\System32\\cmd.exe",
                "C:\\Windows",
                str(Path(self.temp_dir).resolve()),  # Parent dir outside jail
                "\\\\network_share\\payload",
            ]
        else:
            bad_roots = [
                "/etc/passwd",
                "/var/log",
                str(Path(self.temp_dir).resolve()),
            ]

        for bad_root in bad_roots:
            with self.subTest(bad_root=bad_root):
                with self.assertRaises(PathTraversalError, msg=f"Should reject absolute root: {bad_root}"):
                    self.runtime.validate_path(bad_root)

    def test_03_validate_path_null_byte_injection(self):
        """Verify null byte injection attempts are detected and rejected."""
        null_byte_vectors = [
            "normal_file.txt\0evil.py",
            "safe_asset.svg\x00/../../etc/passwd",
            "\x00C:\\sensitive.txt",
        ]
        for vector in null_byte_vectors:
            with self.subTest(vector=vector):
                with self.assertRaises(PathTraversalError, msg=f"Should reject null byte: {vector}"):
                    self.runtime.validate_path(vector)

    def test_04_download_stream_sandboxed_traversal_rejection(self):
        """Verify download_stream_sandboxed rejects target paths escaping sandbox."""
        malicious_targets = [
            Path(self.temp_dir) / "escaped_download.bin",
            "../../sensitive_download.svg",
            "safe_dir/../../../outside.svg",
        ]
        mock_data = b"<svg>Mock payload</svg>"

        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [mock_data, b""]
            mock_url.return_value.__enter__.return_value = mock_resp

            for target in malicious_targets:
                with self.subTest(target=str(target)):
                    with self.assertRaises((PathTraversalError, ValueError)):
                        download_stream_sandboxed(
                            url="https://example.com/asset.svg",
                            target_path=target,
                            execution_runtime=self.runtime,
                        )

        # Confirm secret file outside was not modified/overwritten
        self.assertEqual(self.secret_file.read_text(encoding="utf-8"), "SUPER_SECRET_CREDENTIALS")

    def test_05_render_execution_path_traversal_gating(self):
        """Verify handle_h9_render and bridge.render_video reject output_dir traversal."""
        allowed_dir = (self.sandbox_dir / "traversal_session" / "renders").resolve()
        allowed_dir.mkdir(parents=True, exist_ok=True)

        token = CapabilityToken.create(
            subject_id="editor_subagent",
            role="editor",
            workflow_stage="assembly",
            allowed_tools={"h9.render"},
            allowed_write_paths=[str(allowed_dir)],
            allowed_read_paths=[str(self.sandbox_dir)],
            secret_key=self.secret_key,
        )

        escaped_dirs = [
            str(self.secret_file.parent),
            "../../escaped_renders",
            "C:\\Windows\\Temp" if os.name == "nt" else "/tmp/escaped",
        ]

        dummy_ir = {
            "project_id": "test_adversarial_render",
            "aspect_ratio": "16:9",
            "duration_seconds": 5.0,
            "timeline_blocks": [],
        }

        bridge = get_capability_bridge(session_id="traversal_session")

        for bad_dir in escaped_dirs:
            with self.subTest(bad_dir=bad_dir):
                # 1. Test handle_h9_render with raise_on_error=True
                with self.assertRaises(SecurityError):
                    handle_h9_render(
                        {"production_ir": dummy_ir, "output_dir": bad_dir},
                        capability_token=token,
                        raise_on_error=True,
                    )

                # 2. Test handle_h9_render returning JSON error
                raw_json = handle_h9_render(
                    {"production_ir": dummy_ir, "output_dir": bad_dir},
                    capability_token=token,
                    raise_on_error=False,
                )
                res = json.loads(raw_json)
                self.assertEqual(res.get("status"), "error")
                self.assertIn(res.get("error_type"), ("permission_denied", "security_error", "error"))

                # 3. Test bridge.render_video
                with self.assertRaises(SecurityError):
                    bridge.render_video(
                        ir=dummy_ir,
                        output_dir=bad_dir,
                        session_id="traversal_session",
                        capability_token=token,
                    )

    def test_06_publish_execution_path_traversal_gating(self):
        """Verify handle_h9_publish rejects video_path read escapes."""
        allowed_render_dir = (self.sandbox_dir / "traversal_session" / "renders").resolve()
        token = CapabilityToken.create(
            subject_id="publisher_subagent",
            role="publisher",
            workflow_stage="distribution",
            allowed_tools={"h9.publish"},
            allowed_write_paths=[str(self.sandbox_dir)],
            allowed_read_paths=[str(allowed_render_dir)],
            secret_key=self.secret_key,
        )

        escaped_video_paths = [
            str(self.secret_file),
            "../../sensitive_outside.txt",
            "C:\\Windows\\explorer.exe" if os.name == "nt" else "/bin/bash",
        ]

        for bad_video in escaped_video_paths:
            with self.subTest(bad_video=bad_video):
                with self.assertRaises(SecurityError):
                    handle_h9_publish(
                        {
                            "project_id": "test_proj",
                            "video_path": bad_video,
                            "title": "Adversarial Video",
                        },
                        capability_token=token,
                        raise_on_error=True,
                    )

    def test_07_runtime_file_io_traversal_rejection(self):
        """Verify read_file and write_file atomically reject traversal escapes."""
        # write_file outside session root
        with self.assertRaises(PathTraversalError):
            self.runtime.write_file("../../pwned.txt", "injected")

        # read_file outside session root
        with self.assertRaises(PathTraversalError):
            self.runtime.read_file("../../sensitive_outside.txt")


class TestAdversarialSubprocessTimeoutStress(unittest.TestCase):
    """Stress testing subprocess timeout kills and process tree cleanup."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="h9_challenger_m5_timeout_")
        self.runtime = HermesExecutionRuntime(
            session_id="timeout_stress_session",
            base_dir=Path(self.temp_dir),
            env_type="local",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_hanging_subprocess_timeout_and_exit_code_124(self):
        """Verify hanging sleep subprocess is killed at timeout with exit code 124 and populated stderr."""
        start = time.time()
        # Sleep for 100 seconds with timeout of 1.0s
        result = self.runtime.execute_command(
            [sys.executable, "-c", "import time; time.sleep(100)"],
            timeout_seconds=1.0,
        )
        elapsed = time.time() - start

        # Assert bounded duration (allowing for Windows cold login-shell startup)
        self.assertLess(elapsed, 30.0, "Command should terminate promptly after timeout")
        self.assertEqual(result.exit_code, 124, f"Exit code should be 124 on timeout, got {result.exit_code}")
        self.assertTrue(result.timed_out)
        self.assertIn("timed out", result.stderr.lower())
        self.assertIn("1.0", result.stderr)

    def test_02_hanging_subprocess_tree_group_termination_no_orphans(self):
        """Verify process tree spawning a child worker is terminated without orphaned processes."""
        spawn_script = (
            "import subprocess, sys, time\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(100)'])\n"
            "print(f'CHILD_PID:{child.pid}', flush=True)\n"
            "time.sleep(100)\n"
        )
        script_file = Path(self.temp_dir) / "spawner.py"
        script_file.write_text(spawn_script, encoding="utf-8")

        result = self.runtime.execute_command(
            [sys.executable, str(script_file)],
            timeout_seconds=2.0,
        )

        self.assertEqual(result.exit_code, 124)
        self.assertTrue(result.timed_out)

        child_pid = None
        for line in result.stdout.splitlines():
            if line.startswith("CHILD_PID:"):
                try:
                    child_pid = int(line.split(":")[1].strip())
                except ValueError:
                    pass

        if child_pid:
            time.sleep(0.5)
            self.assertFalse(
                psutil.pid_exists(child_pid) and psutil.Process(child_pid).is_running(),
                f"Orphaned child process {child_pid} detected still running!",
            )

    def test_03_rapid_consecutive_timeouts_resilience(self):
        """Verify multiple rapid timeout cycles do not exhaust resources or deadlock."""
        for cycle in range(3):
            res = self.runtime.execute_command(
                [sys.executable, "-c", "import time; time.sleep(50)"],
                timeout_seconds=1.0,
            )
            self.assertEqual(res.exit_code, 124, f"Failed at timeout cycle {cycle}")
            self.assertTrue(res.timed_out)
            self.assertIn("timed out", res.stderr.lower())


class TestAdversarialAssetStreamSizeLimit(unittest.TestCase):
    """Stress testing stream downloads against memory exhaustion and size limits."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="h9_challenger_m5_asset_size_")
        self.freezer = AssetFreezer(
            base_output_dir=self.temp_dir,
            max_size_bytes=1024 * 1024,  # 1 MB cap
        )
        self.runtime = HermesExecutionRuntime(
            session_id="asset_size_session",
            base_dir=Path(self.temp_dir),
            env_type="local",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_declared_content_length_exceeded(self):
        """Verify download_stream raises AssetSizeExceededError on Content-Length header exceeding cap."""
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.headers = {"Content-Length": "104857600"}  # 100 MB declared
            mock_url.return_value.__enter__.return_value = mock_resp

            with self.assertRaises(AssetSizeExceededError):
                download_stream("https://example.com/huge.bin", max_size_bytes=1024 * 1024)

            # Assert read was never called
            mock_resp.read.assert_not_called()

    def test_02_chunked_streaming_exceeded_before_oom(self):
        """Verify infinite/unbounded chunk stream aborts immediately upon exceeding limit."""
        chunk = b"X" * 65536  # 64 KB chunk
        call_count = 0

        def infinite_chunks(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return chunk

        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.headers = {}  # No Content-Length
            mock_resp.read.side_effect = infinite_chunks
            mock_url.return_value.__enter__.return_value = mock_resp

            # Max size is 128 KB (2 chunks)
            with self.assertRaises(AssetSizeExceededError):
                download_stream("https://example.com/infinite.bin", max_size_bytes=131072)

            # Verify it aborted quickly without reading more than 3 chunks
            self.assertLessEqual(call_count, 3, "Stream should abort immediately without reading unbounded chunks")

    def test_03_sandboxed_download_enforces_size_cap(self):
        """Verify download_stream_sandboxed enforces max_size_bytes cap when stream exceeds limit."""
        dest_path = self.runtime.session_root / "too_large_sandboxed.bin"
        large_chunk = b"Y" * 65536

        # Test fallback to download_stream when curl fails or size exceeded
        with patch.object(self.runtime, "execute_command") as mock_exec, \
             patch("urllib.request.urlopen") as mock_url:
            # Mock curl execution returning non-zero (e.g. curl exit code 63 for max-filesize exceeded)
            mock_exec.return_value = ExecutionResult(
                exit_code=63,
                stdout="",
                stderr="curl: (63) Maximum file size exceeded",
                duration_seconds=0.1,
                timed_out=False,
            )
            mock_resp = MagicMock()
            mock_resp.headers = {}
            mock_resp.read.side_effect = [large_chunk, large_chunk, b""]
            mock_url.return_value.__enter__.return_value = mock_resp

            with self.assertRaises((AssetSizeExceededError, ValueError)):
                download_stream_sandboxed(
                    url="https://example.com/toobig.bin",
                    target_path=dest_path,
                    execution_runtime=self.runtime,
                    max_size_bytes=50000,
                )

    def test_04_asset_freezer_freeze_bytes_size_cap(self):
        """Verify AssetFreezer.freeze_bytes raises AssetSizeExceededError."""
        target_file = Path(self.temp_dir) / "test_freeze.bin"
        oversized_data = b"A" * 2000

        freezer_small = AssetFreezer(max_size_bytes=1000)
        with self.assertRaises(AssetSizeExceededError):
            freezer_small.freeze_bytes(oversized_data, target_path=target_file)

        # AssetSizeExceededError must also be catchable as ValueError
        with self.assertRaises(ValueError):
            freezer_small.freeze_bytes(oversized_data, target_path=target_file)


class TestAdversarialMCPDiscoveryAndExecution(unittest.TestCase):
    """Stress testing MCP discovery, schema validation, and malformed invocation."""

    def setUp(self):
        self.tool_runtime = DefaultToolRuntime()
        self.bridge = HermesCapabilityBridge(
            session_id="mcp_adversarial_session",
            tool_runtime=self.tool_runtime,
        )

    def test_01_mcp_discovery_empty_and_unknown_servers(self):
        """Verify empty discovery returns empty lists and zero server counts."""
        empty_tools = self.bridge.discover_mcp_tools()
        self.assertEqual(empty_tools, [])

        unknown_server_tools = self.bridge.discover_mcp_tools(server_name="nonexistent_server_xyz")
        self.assertEqual(unknown_server_tools, [])

        status = self.bridge.get_mcp_status()
        self.assertEqual(status.get("total_tools"), 0)
        self.assertIsInstance(status.get("servers"), dict)

    def test_02_mcp_edge_case_registrations(self):
        """Verify MCP tools with unconventional names and minimal schemas register cleanly."""
        # 1. Complex naming
        self.bridge.register_mcp_tool(
            server_name="srv_special",
            name="mcp.tools_special-1.v2",
            description="Special tool naming",
            parameters={"type": "object", "properties": {}},
            handler=lambda args, **kw: "OK_SPECIAL",
        )

        tools = self.bridge.discover_mcp_tools(server_name="srv_special")
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].name, "mcp.tools_special-1.v2")

        res = self.bridge.invoke_mcp_tool("mcp.tools_special-1.v2", {})
        self.assertEqual(res, "OK_SPECIAL")

        # 2. Server filtering isolation
        self.bridge.register_mcp_tool(
            server_name="srv_other",
            name="mcp.tool_other",
            description="Other server tool",
            parameters={"type": "object", "properties": {}},
            handler=lambda args, **kw: "OK_OTHER",
        )
        srv_other_tools = self.bridge.discover_mcp_tools(server_name="srv_other")
        self.assertEqual(len(srv_other_tools), 1)
        self.assertEqual(srv_other_tools[0].name, "mcp.tool_other")

        srv_special_tools = self.bridge.discover_mcp_tools(server_name="srv_special")
        self.assertEqual(len(srv_special_tools), 1)
        self.assertEqual(srv_special_tools[0].name, "mcp.tools_special-1.v2")

        # 3. Clean override with same name
        self.bridge.register_mcp_tool(
            server_name="srv_special",
            name="mcp.tools_special-1.v2",
            description="Special tool override",
            parameters={"type": "object", "properties": {}},
            handler=lambda args, **kw: "OK_OVERRIDDEN",
        )
        res_override = self.bridge.invoke_mcp_tool("mcp.tools_special-1.v2", {})
        self.assertEqual(res_override, "OK_OVERRIDDEN")

    def test_03_mcp_malformed_arguments_through_bridge(self):
        """Verify parameter validation handles missing required args and type mismatches."""
        self.bridge.register_mcp_tool(
            server_name="validation_server",
            name="mcp.strict_calculator",
            description="Strict type validation tester",
            parameters={
                "type": "object",
                "properties": {
                    "count": {"type": "integer"},
                    "ratio": {"type": "number"},
                    "tags": {"type": "array"},
                    "meta": {"type": "object"},
                    "flag": {"type": "boolean"},
                },
                "required": ["count", "ratio"],
            },
            handler=lambda args, **kw: json.dumps({"status": "success", "result": args}),
        )

        # Case A: Missing required parameter 'ratio'
        res_missing = self.bridge.invoke_mcp_tool("mcp.strict_calculator", {"count": 10})
        data_missing = json.loads(res_missing)
        self.assertIn("error", data_missing)
        self.assertIn("Missing required parameter: 'ratio'", data_missing["error"])

        # Case B: Type mismatch - count passed as string
        res_str = self.bridge.invoke_mcp_tool("mcp.strict_calculator", {"count": "10", "ratio": 1.5})
        data_str = json.loads(res_str)
        self.assertIn("error", data_str)
        self.assertIn("expected integer", data_str["error"])

        # Case C: Type mismatch - count passed as boolean (Python bool is subclass of int)
        res_bool = self.bridge.invoke_mcp_tool("mcp.strict_calculator", {"count": True, "ratio": 1.5})
        data_bool = json.loads(res_bool)
        self.assertIn("error", data_bool)
        self.assertIn("expected integer", data_bool["error"])

        # Case D: Type mismatch - tags passed as string instead of array
        res_array = self.bridge.invoke_mcp_tool(
            "mcp.strict_calculator", {"count": 5, "ratio": 2.0, "tags": "not-a-list"}
        )
        data_array = json.loads(res_array)
        self.assertIn("error", data_array)
        self.assertIn("expected list", data_array["error"])

        # Case E: Valid execution
        res_valid = self.bridge.invoke_mcp_tool(
            "mcp.strict_calculator",
            {"count": 5, "ratio": 2.5, "tags": ["alpha", "beta"], "flag": False, "meta": {"k": "v"}},
        )
        data_valid = json.loads(res_valid)
        self.assertEqual(data_valid.get("status"), "success")
        self.assertEqual(data_valid["result"]["count"], 5)

    def test_04_mcp_unregistered_tool_and_exception_containment(self):
        """Verify calling unregistered tool raises ValueError and handler crash is contained."""
        # Unregistered tool invocation
        with self.assertRaises(ValueError):
            self.bridge.invoke_mcp_tool("mcp.does_not_exist", {})

        # Handler throwing an exception is cleanly trapped and returned as bounded JSON error
        def exploding_handler(args: dict, **kw) -> str:
            raise RuntimeError("Database connection suddenly dropped!")

        self.bridge.register_mcp_tool(
            server_name="crash_server",
            name="mcp.exploding_tool",
            description="Tool that throws",
            parameters={"type": "object", "properties": {}},
            handler=exploding_handler,
        )

        res_err = self.bridge.invoke_mcp_tool("mcp.exploding_tool", {})
        data_err = json.loads(res_err)
        self.assertIn("error", data_err)
        self.assertIn("Database connection suddenly dropped!", data_err["error"])
        self.assertEqual(data_err.get("tool_name"), "mcp.exploding_tool")


if __name__ == "__main__":
    unittest.main()
