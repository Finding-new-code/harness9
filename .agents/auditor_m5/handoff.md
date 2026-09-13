# Forensic Audit Report: Milestone 5 (Sandbox, Permission & MCP Integration)

**Work Product**: Milestone 5 Implementation (`src/h9_runtime/execution.py`, `src/security/tokens.py`, `src/security/guard.py`, `tools/h9_content_tools.py`, `src/assets/freezer.py`, `src/h9_runtime/bridge.py`, `src/h9_runtime/tools.py`, and test suites `tests/test_h9_m5_sandbox_permission_mcp.py`, `tests/test_h9_content_tools.py`, `tests/test_security_tokens.py`)  
**Profile**: General Project  
**Integrity Mode**: development (derived from `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

### Phase Results
- **Phase 1.1: Pre-Populated Artifact Detection**: PASS — No pre-populated mock result or fake log artifacts found in repository test and source directories.
- **Phase 1.2: Hardcoded Output / Constant Return Detection**: PASS — Handlers and runtime methods compute real subprocess, cryptographic, and permission outputs dynamically. Zero dummy `return True` or test-specific short-circuits.
- **Phase 1.3: Facade & Stub Detection**: PASS — `HermesExecutionRuntime` genuinely interfaces with Hermes `BaseEnvironment` (Docker, Modal, Local); `SecurityGuard` / `TokenGuard` strictly enforces token signatures, expiry, cascading revocation, and path confinement.
- **Phase 1.4: Cryptographic & Set Calculus Integrity**: PASS — HMAC-SHA256 signatures use constant-time `hmac.compare_digest` with deterministic JSON canonical payload representations; permission intersection ($P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$) adheres strictly to least privilege; revocation cascades down full lineage trees.
- **Phase 2.1: Tool Gating & Boundary Enforcement**: PASS — All 5 H9 content tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, `h9.publish` and snake_case aliases) are registered under toolset `h9_content`, gated by `check_h9_available()`, and strictly verify capability tokens before argument processing. Unauthorized callers (e.g. `researcher`) attempting to invoke `h9.render` or `h9.publish` are blocked with `status="error", error_type="permission_denied"`.
- **Phase 2.2: Subprocess & Sandbox Execution**: PASS — HyperFrames renderer and download streams route through `HermesExecutionRuntime`, enforcing process group timeout killing (exit code 124), `--shm-size 1g` for Docker, and path traversal rejection.
- **Phase 2.3: Independent Test Execution**: PASS — 69 out of 69 tests executed and passed cleanly in 286.72 seconds.

---

## 1. Observation

Direct code and behavioral observations gathered during forensic inspection:

1. **Hermes BaseEnvironment Integration in `src/h9_runtime/execution.py`**:
   - Lines 206–224: `HermesExecutionRuntime.__init__` configures `session_id`, `base_dir`, `environment`, `env_type`, and `docker_shm_size="1g"`.
   - Lines 262–300: `resolve_environment()` dynamically queries Hermes `get_active_env(self.session_id)`, falls back to `ensure_task_env`, or instantiates `DockerEnvironment` (with `shm_size=self.docker_shm_size`), `ModalEnvironment`, or `LocalEnvironment`.
   - Lines 301–383: `execute_command()` quotes arguments, binds environment variables, translates container paths (`container_cwd = str(effective_cwd) if is_local else "/workspace"`), and executes directly against `env.execute()`. On timeout, process termination is enforced, `exit_code=124` is returned, and `stderr` is populated with `Command timed out after {timeout_seconds}s`.
   - Lines 237–260: `validate_path()` detects null byte injection (`"\0" in path_str`) and enforces directory jail confinement via `resolved.relative_to(root)` raising `PathTraversalError`.

2. **Cryptographic Capability Tokens & Cascading Revocation in `src/security/tokens.py`**:
   - Lines 183–278: `CapabilityToken` model contains Pydantic-validated fields (`token_id`, `parent_token_id`, `subject_id`, `role`, `workflow_id`, `workflow_stage`, `allowed_tools`, `allowed_write_paths`, `allowed_read_paths`, `allowed_network_hosts`, `created_at_utc`, `expires_at_utc`, `delegation_depth`, `max_delegation_depth`, `delegation_lineage`, `signature`).
   - Lines 304–340: `to_canonical_payload()` produces a sorted, deterministic dictionary. `sign()` and `verify_signature()` use `hmac.new(key_bytes, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()` and `hmac.compare_digest`.
   - Lines 70–116: `TokenRevocationRegistry` provides thread-safe active token invalidation with cascading lineage tracking. In `is_revoked()`, lines 99–104:
     ```python
     if token_id in self._revoked_tokens:
         return True
     for ancestor_id in check_lineage:
         if ancestor_id in self._revoked_tokens:
             return True
     return False
     ```
   - Lines 446–459: `calculate_capability_token()` enforces set intersection:
     ```python
     if "*" in parent_perms:
         return role_perms.intersection(workflow_perms)
     return effective_parent.intersection(role_perms).intersection(workflow_perms)
     ```
   - Lines 524–681: `derive_child_token()` verifies parent expiration, checks revocation across lineage, validates cryptographic signatures, checks `delegation_depth < max_delegation_depth`, computes tool, path, and network host intersections, ensures $T_{expire}^{child} \le T_{expire}^{parent}$, and appends `parent_token.token_id` to `delegation_lineage`.

3. **Tool Gating & Boundary Enforcement in `tools/h9_content_tools.py`**:
   - Lines 602–705: All 5 tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, `h9.publish`) and their aliases are registered into toolset `h9_content`, service-gated by `check_h9_available` (Rung 3 of Footprint Ladder).
   - In each handler (`handle_h9_research` lines 271–280, `handle_h9_discover_assets` lines 326–335, `handle_h9_generate_script` lines 381–390, `handle_h9_render` lines 487–499, `handle_h9_publish` lines 541–553):
     `token = resolve_capability_token(args, kwargs, session_id)` is invoked at the very entry. `guard.enforce_tool_execution(token, ...)` is evaluated before inspecting or parsing arguments. Unauthorized callers receive `tool_error(..., status="error", error_type="permission_denied")` or raise `PermissionDeniedError`.
   - `handle_h9_render` and `handle_h9_publish` additionally enforce path confinement on `output_dir` (mode "write") and `video_path` (mode "read") using `guard.enforce_filesystem_access`.

4. **Hermes MCP Integration in `src/h9_runtime/tools.py` & `src/h9_runtime/bridge.py`**:
   - Lines 255–393 of `src/h9_runtime/tools.py`: Implements `register_mcp_tool`, `discover_mcp_tools` (filtering by server name or listing all), `invoke_mcp_tool` (dynamic invocation with parameter passing), and `get_mcp_status` (connectivity and tool counts).

5. **Empirical Test Suite Execution**:
   - Command: `.venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py tests/test_h9_content_tools.py tests/test_security_tokens.py -v`
   - Exit code: `0`
   - Summary: `69 passed in 286.72s (0:04:46)`
   - 19 of 19 M5-specific tests passed.
   - 34 of 34 Content Tools tests passed.
   - 16 of 16 Security Tokens tests passed.

---

## 2. Logic Chain

1. **Authenticity of Sandboxed Execution**:
   - Direct observation of `src/h9_runtime/execution.py` confirms that `HermesExecutionRuntime` delegates command execution to the active Hermes `BaseEnvironment` (or instantiates `DockerEnvironment` / `LocalEnvironment` with `--shm-size 1g` and timeout bounds).
   - The timeout kill logic relies on real return code inspection (`retcode == 124` or output markers) and sets a clear, non-empty error message in `stderr`.
   - Path confinement is enforced by canonical resolution and checking `resolved.relative_to(session_root)`. Traversal attempts (`../`, null bytes) trigger `PathTraversalError`.
   - Therefore, execution sandboxing is genuine and satisfies R5.1.

2. **Authenticity of Cryptographic Tokens & Least Privilege Calculus**:
   - In `src/security/tokens.py`, tokens use canonical deterministic JSON payloads with HMAC-SHA256 signatures verified via `hmac.compare_digest`. Tampering with any payload attribute immediately invalidates the signature.
   - `derive_child_token` mathematically enforces $P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$; no child can gain permissions not held by its parent, and monotonic expiry guarantees a child token cannot outlive its parent.
   - Active revocation registry checks the token and its complete ancestor lineage (`delegation_lineage`). Revoking a root or intermediary token instantly cascades invalidation to all descendants.
   - Therefore, cryptographic capability calculus is mathematically sound, robust against tampering, and satisfies R5.2.

3. **Authenticity of 4-Tier Tool Gating**:
   - In `tools/h9_content_tools.py` and `src/security/guard.py`, permission checks occur unconditionally at the entry point of every handler (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, `h9.publish`).
   - Testing empirically confirmed that an agent with a `researcher` role cannot invoke `h9.render` or `h9.publish`, returning `permission_denied`.
   - Authorized roles (`editor` for render, `publisher` for publish) execute successfully.
   - Therefore, tool-level permission gating is authentic and satisfies R5.2.

4. **Authenticity of Hermes MCP Integration**:
   - `DefaultToolRuntime` and `HermesCapabilityBridge` provide complete implementations for MCP status querying, dynamic tool registration, reflection into tool schemas, and invocation.
   - All tests in `TestR53HermesMCPIntegration` passed dynamically without mocked hardcoded returns.
   - Therefore, Hermes MCP integration satisfies R5.3.

---

## 3. Caveats

- **Docker Daemon Dependency**: When running in an environment without a running Docker daemon, `HermesExecutionRuntime` gracefully falls back to `LocalEnvironment` while maintaining path confinement and timeout enforcement. The Docker `--shm-size 1g` parameter is verified via configuration tests.
- **No Caveats on Implementation Completeness**: No facade implementations, test-only hardcoded returns, dummy shims, or shortcuts were found.

---

## 4. Conclusion

Milestone 5 (Sandbox, Permission & MCP Integration) is **100% authentic, robustly implemented, and compliant with all project standards and constraints**.

- **Final Audit Verdict**: **CLEAN**
- All 69 relevant unit, integration, and gating tests pass with zero failures.
- No integrity violations exist. The work product is approved for Milestone 6 acceptance verification.

---

## 5. Verification Method

To independently verify this forensic audit:

1. **Execute the complete test suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py tests/test_h9_content_tools.py tests/test_security_tokens.py -v
   ```
   *Expected Output*: `69 passed` with exit code `0`.

2. **Verify Permission Boundary Enforcement**:
   Inspect `tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_05_four_tier_tool_gating_researcher_blocked_from_render_and_publish` to confirm that unauthorized roles are blocked from `h9.render` and `h9.publish`.

3. **Verify Cryptographic Tamper Detection**:
   Inspect `tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_05_token_model_tamper_detection` to confirm that tampering with payload attributes invalidates HMAC-SHA256 signatures.

4. **Invalidation Conditions**:
   - Any test failure in `tests/test_h9_m5_sandbox_permission_mcp.py`.
   - A caller with role `researcher` succeeding in calling `h9.render` or `h9.publish`.
   - A tampered capability token payload passing signature verification.
   - A path escaping `session_root` without raising `PathTraversalError`.
