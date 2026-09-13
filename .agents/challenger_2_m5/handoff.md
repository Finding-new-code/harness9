# Milestone 5 Adversarial Challenger Report: Sandbox, Permission & MCP Integration

**Agent**: challenger_2_m5  
**Role**: critic / specialist (Empirical Challenger)  
**Date**: 2026-09-05  
**Parent Conversation ID**: d8ee0a9c-a772-41e0-acea-c4143b224122  
**Milestone**: M5 (Sandbox, Permission & MCP Integration)  
**Gate Verdict**: **APPROVE**  

---

## 1. Observation

Adversarial stress testing was conducted against the Milestone 5 implementation using a dedicated, standalone adversarial test suite authored at `tests/test_challenger_m5_sandbox_mcp.py`.

### 1.1 Test Execution Commands and Verbatim Results

```powershell
# Execution of Adversarial Stress Suite
.venv\Scripts\python.exe -m pytest tests/test_challenger_m5_sandbox_mcp.py -v
```

**Verbatim Output**:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- G:\Finding-new-code\harness9\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: G:\Finding-new-code\harness9
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 18 items

tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialPathTraversal::test_01_validate_path_relative_traversals PASSED [  5%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialPathTraversal::test_02_validate_path_absolute_root_escapes PASSED [ 11%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialPathTraversal::test_03_validate_path_null_byte_injection PASSED [ 16%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialPathTraversal::test_04_download_stream_sandboxed_traversal_rejection PASSED [ 22%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialPathTraversal::test_05_render_execution_path_traversal_gating PASSED [ 27%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialPathTraversal::test_06_publish_execution_path_traversal_gating PASSED [ 33%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialPathTraversal::test_07_runtime_file_io_traversal_rejection PASSED [ 38%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialSubprocessTimeoutStress::test_01_hanging_subprocess_timeout_and_exit_code_124 PASSED [ 44%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialSubprocessTimeoutStress::test_02_hanging_subprocess_tree_group_termination_no_orphans PASSED [ 50%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialSubprocessTimeoutStress::test_03_rapid_consecutive_timeouts_resilience PASSED [ 55%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialAssetStreamSizeLimit::test_01_declared_content_length_exceeded PASSED [ 61%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialAssetStreamSizeLimit::test_02_chunked_streaming_exceeded_before_oom PASSED [ 66%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialAssetStreamSizeLimit::test_03_sandboxed_download_enforces_size_cap PASSED [ 72%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialAssetStreamSizeLimit::test_04_asset_freezer_freeze_bytes_size_cap PASSED [ 77%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialMCPDiscoveryAndExecution::test_01_mcp_discovery_empty_and_unknown_servers PASSED [ 83%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialMCPDiscoveryAndExecution::test_02_mcp_edge_case_registrations PASSED [ 88%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialMCPDiscoveryAndExecution::test_03_mcp_malformed_arguments_through_bridge PASSED [ 94%]
tests/test_challenger_m5_sandbox_mcp.py::TestAdversarialMCPDiscoveryAndExecution::test_04_mcp_unregistered_tool_and_exception_containment PASSED [100%]

============== 18 passed, 23 subtests passed in 86.19s (0:01:26) ==============
```

```powershell
# Combined Regression Test Run (Adversarial + M5 Baseline + Security Tokens)
.venv\Scripts\python.exe -m pytest tests/test_challenger_m5_sandbox_mcp.py tests/test_h9_m5_sandbox_permission_mcp.py tests/test_security_tokens.py -v
```

**Verbatim Output**:
```text
============================= test session starts =============================
...
============== 53 passed, 23 subtests passed in 84.52s (0:01:24) ==============
```

```powershell
# H9 Content Tools Suite
.venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py -v
```

**Verbatim Output**:
```text
============================= test session starts =============================
...
======================== 34 passed in 71.35s (0:01:11) ========================
```

---

## 2. Logic Chain

The adversarial stress testing systematically targeted four potential failure surfaces:

### 2.1 Attack Surface 1: Path Traversal Attacks
- **Test Implementation**: `TestAdversarialPathTraversal` (`test_01` through `test_07`)
- **Reasoning**:
  1. In `src/h9_runtime/execution.py` (`HermesExecutionRuntime.validate_path`), path validation resolves paths against `session_root` and verifies containment using `resolved.relative_to(session_root)`. When passed relative upward paths (`../../sensitive_outside.txt`, `subdir/../../sensitive_outside.txt`, `nested/sub/../../../sensitive_outside.txt`, `..\\..\\`, `os.path.join("..", "..", "file")`), a `PathTraversalError` is consistently raised, preventing any filesystem escape.
  2. Absolute system roots (`C:\Windows\System32`, `C:\`, `/etc/passwd`, and parent directories outside the jail) are resolved and checked against `session_root`. Any path not strictly prefixed by the session directory raises `PathTraversalError`.
  3. Null byte injections (`normal_file.txt\0evil.py`, `\x00C:\sensitive.txt`) are explicitly trapped at lines 76-77 and 244-245 of `src/h9_runtime/execution.py`, raising `PathTraversalError("Null byte injection detected in filesystem path")`.
  4. In `download_stream_sandboxed` (`src/assets/freezer.py`), `validate_path` is executed upfront prior to network streaming or file creation, ensuring malicious destination paths fail before any network stream opens.
  5. In `handle_h9_render` and `handle_h9_publish` (`tools/h9_content_tools.py`), output and input path arguments (`output_dir`, `video_path`) are guarded against capability tokens via `guard.enforce_filesystem_access(token, path, mode="write"/"read")`. When scoped tokens without root access are supplied, paths escaping designated directories are rejected either with `SecurityError` (when `raise_on_error=True`) or standard error envelopes (`status="error", error_type="permission_denied"`).

### 2.2 Attack Surface 2: Subprocess Timeout Stress & Process Group Termination
- **Test Implementation**: `TestAdversarialSubprocessTimeoutStress` (`test_01` through `test_03`)
- **Reasoning**:
  1. In `HermesExecutionRuntime.execute_command`, long-running or hanging subprocesses are bounded by `timeout_seconds`. When executed with `timeout_seconds=1.0`, execution terminates and returns an `ExecutionResult` with `exit_code=124`, `timed_out=True`, and `stderr` populated with `f"Command timed out after {timeout_seconds}s"`.
  2. Process tree killing was tested by executing a Python script that spawned an independent background worker (`subprocess.Popen`) which also attempted an infinite sleep. Using `psutil` process tracking, both the parent process and the spawned child process were verified to be terminated upon timeout. No orphaned or zombie background processes survived.
  3. Rapid consecutive timeouts (3 back-to-back 1-second timeout cycles) executed without deadlocks, resource exhaustion, or state leakage across commands.

### 2.3 Attack Surface 3: Asset Stream Size Limits & OOM Defense
- **Test Implementation**: `TestAdversarialAssetStreamSizeLimit` (`test_01` through `test_04`)
- **Reasoning**:
  1. In `src/assets/freezer.py` (`download_stream`), incoming HTTP responses with a declared `Content-Length` header exceeding `max_size_bytes` immediately raise `AssetSizeExceededError` before reading any stream chunks, protecting against payload allocation.
  2. When handling unbounded chunked transfer encoding (streams without a Content-Length header or with spoofed headers), `download_stream` reads in 64 KB chunks and tracks accumulated bytes. The moment `total_bytes > max_size_bytes`, it raises `AssetSizeExceededError` immediately, capping chunk reads and preventing memory exhaustion.
  3. `AssetSizeExceededError` inherits from both `AssetDownloadError` and `ValueError`, satisfying callers expecting either exception hierarchy.
  4. In `AssetFreezer.freeze_bytes`, byte arrays exceeding `max_size_bytes` are rejected prior to any disk write.

### 2.4 Attack Surface 4: MCP Discovery & Execution Robustness
- **Test Implementation**: `TestAdversarialMCPDiscoveryAndExecution` (`test_01` through `test_04`)
- **Reasoning**:
  1. Empty MCP registries and queries for nonexistent servers return empty lists (`[]`) and structured status reports without throwing unexpected exceptions.
  2. Dynamic tool registration gracefully accommodates unconventional tool names (e.g. `mcp.tools_special-1.v2`), minimal parameter schemas, server-based filtering, and clean tool overrides.
  3. In `DefaultToolRuntime.validate_parameter_schema` and `dispatch_tool`, malformed arguments are trapped:
     - Missing required parameters return structured schema validation error envelopes.
     - Type mismatches (e.g. string passed where integer expected; list passed where string expected) return validation errors.
     - Boolean values passed for integer parameters are correctly caught (`isinstance(v, bool)` guard), avoiding Python's `bool` subclass-of-`int` coercion bug.
  4. Dynamic invocation of nonexistent tools raises `ValueError(f"MCP tool '{tool_name}' not found.")`.
  5. Unhandled exceptions raised by tool handlers (e.g. simulated database crash) are trapped by `dispatch_tool` and encapsulated into bounded JSON error messages (`MAX_TOOL_ERROR_CHARS = 2048`), preventing crashes from propagating into the bridge or agent loop.

---

## 3. Caveats

- **Docker/Modal Daemons in CI**: When Docker or Modal environments are unavailable in local development or CI runners without container daemons, `HermesExecutionRuntime` and `resolve_environment` fallback to `LocalEnvironment`. All sandbox boundaries, directory confinement, process group killing, and timeout bounds were validated on `LocalEnvironment`.
- **Operating System Specifics**: On Windows hosts, process tree termination leverages `taskkill.exe /F /T /PID` via `gateway.status.terminate_pid`, which was empirically verified to terminate process trees cleanly. On POSIX platforms, `os.killpg(pgid, signal.SIGTERM/SIGKILL)` is used.

---

## 4. Conclusion

Milestone 5 (Sandbox, Permission & MCP Integration) successfully withstands all adversarial attack vectors:
1. **Path Traversal Resistance**: 100% of relative traversal vectors, absolute root escapes, null-byte injections, and unauthorized render/publish destinations are blocked.
2. **Subprocess Timeout Enforcement**: Timed-out subprocesses are cleanly terminated with exit code 124, stderr diagnostics populated, and zero orphaned background processes remaining.
3. **Asset Stream Safety**: Byte limits are strictly enforced on both declared Content-Length headers and chunked streams, raising `AssetSizeExceededError` before memory exhaustion.
4. **MCP Resilience**: MCP tool discovery, schema reflection, type validation (including bool/int discrimination), and error containment are robust.

**Gate Verdict**: **APPROVE**

---

## 5. Verification Method

To independently reproduce and verify this challenge assessment:

```powershell
# 1. Run the adversarial stress test suite
.venv\Scripts\python.exe -m pytest tests/test_challenger_m5_sandbox_mcp.py -v

# 2. Run the baseline M5 test suite
.venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py -v

# 3. Run the security capability token suite
.venv\Scripts\python.exe -m pytest tests/test_security_tokens.py -v

# 4. Run the combined verification suite (53 tests)
.venv\Scripts\python.exe -m pytest tests/test_challenger_m5_sandbox_mcp.py tests/test_h9_m5_sandbox_permission_mcp.py tests/test_security_tokens.py -v
```

### Invalidation Conditions
- Any test in `tests/test_challenger_m5_sandbox_mcp.py` failing.
- Any path traversal escape accessing or modifying files outside session roots.
- Orphaned background processes surviving a timed-out subprocess execution.
- Large/infinite streams exceeding `max_size_bytes` without raising `AssetSizeExceededError`.
- Unhandled exceptions from MCP handlers crashing the agent or capability bridge.
