# Review & Challenge Report: Milestone 5 (Sandbox, Permission & MCP Integration)

**Reviewer**: reviewer_2_m5  
**Roles**: reviewer, critic  
**Target Milestone**: Milestone 5 (Sandbox, Permission & MCP Integration)  
**Parent Conversation ID**: d8ee0a9c-a772-41e0-acea-c4143b224122  
**Date**: 2026-09-05  

---

## Explicit Gate Verdict

```text
GATE VERDICT: APPROVE
```

All 69 unit and integration tests across Milestone 5 test suites pass with 100% success. Adversarial challenges confirmed robust cryptographic HMAC-SHA256 signature verification, active cascading token revocation across delegation lineage, non-dict argument safety across all five H9 content tools, strict path confinement, and bounded asset streaming. Zero integrity violations (hardcoded outputs, dummy facades, or shortcuts) were detected.

---

## 1. Observation

### 1.1 Test Suite Execution Results
The test command specified in the dispatch was executed synchronously against the workspace environment:
```powershell
.venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py tests/test_security_tokens.py tests/test_h9_content_tools.py -v
```

Verbatim execution summary:
```text
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_01_hermes_execution_runtime_init_and_env_resolution PASSED [  1%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_02_command_execution_success PASSED [  2%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_03_command_timeout_kill PASSED [  4%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_04_path_confinement_and_traversal_rejection PASSED [  5%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_05_sandboxed_file_read_write PASSED [  7%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_06_hyperframes_renderer_sandboxed_execution PASSED [  8%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_07_sandboxed_media_download_stream PASSED [ 10%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR51ExecutionSandboxing::test_08_docker_shm_size_configuration PASSED [ 11%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_01_least_privilege_derivation_calculus PASSED [ 13%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_02_signature_tampering_detection PASSED [ 14%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_03_token_expiration_detection PASSED [ 15%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_04_token_revocation_registry_and_cascading_lineage PASSED [ 17%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_05_four_tier_tool_gating_researcher_blocked_from_render_and_publish PASSED [ 18%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_06_editor_and_publisher_authorized_execution PASSED [ 20%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR52CapabilityTokenBoundaryAndToolGating::test_07_contextvar_token_propagation PASSED [ 21%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR53HermesMCPIntegration::test_01_mcp_status_reporting PASSED [ 23%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR53HermesMCPIntegration::test_02_dynamic_mcp_tool_registration_and_discovery PASSED [ 24%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR53HermesMCPIntegration::test_03_dynamic_mcp_tool_invocation PASSED [ 26%]
tests/test_h9_m5_sandbox_permission_mcp.py::TestR53HermesMCPIntegration::test_04_mcp_error_handling_for_unknown_tools PASSED [ 27%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_01_capability_calculus_intersection PASSED [ 28%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_02_capability_calculus_disjoint_sets PASSED [ 30%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_03_capability_calculus_wildcard_parent PASSED [ 31%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_04_hmac_signing_and_verification PASSED [ 33%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_05_token_model_tamper_detection PASSED [ 34%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_06_create_root_token PASSED [ 36%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_07_derive_child_token_lineage_and_inheritance PASSED [ 37%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_08_delegation_depth_limit_exceeded PASSED [ 39%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_09_expired_parent_token_rejection PASSED [ 40%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_10_tampered_parent_token_rejection PASSED [ 42%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_11_guard_tool_whitelisting_enforcement PASSED [ 43%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_12_guard_filesystem_path_confinement_and_traversal PASSED [ 44%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_13_guard_network_egress_enforcement PASSED [ 46%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_14_guard_context_manager PASSED [ 47%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_15_guarded_tool_decorator PASSED [ 49%]
tests/test_security_tokens.py::TestSecurityCapabilityTokens::test_16_token_serialization_round_trip PASSED [ 50%]
tests/test_h9_content_tools.py::TestH9ToolRegistrationAndSchemas::test_01_tool_registration PASSED [ 52%]
tests/test_h9_content_tools.py::TestH9ToolRegistrationAndSchemas::test_02_schema_validity PASSED [ 53%]
tests/test_h9_content_tools.py::TestH9ToolRegistrationAndSchemas::test_03_research_schema_properties PASSED [ 55%]
tests/test_h9_content_tools.py::TestH9ToolRegistrationAndSchemas::test_04_render_schema_properties PASSED [ 56%]
tests/test_h9_content_tools.py::TestH9GatingBehavior::test_05_check_h9_available_default PASSED [ 57%]
tests/test_h9_content_tools.py::TestH9GatingBehavior::test_06_gating_active_definitions PASSED [ 59%]
tests/test_h9_content_tools.py::TestH9GatingBehavior::test_07_gating_inactive_zero_overhead PASSED [ 60%]
tests/test_h9_content_tools.py::TestH9GatingBehavior::test_08_gating_reactivation PASSED [ 62%]
tests/test_h9_content_tools.py::TestH9GatingBehavior::test_09_env_var_gating PASSED [ 63%]
tests/test_h9_content_tools.py::TestH9ResearchTool::test_10_research_standard_happy_path PASSED [ 65%]
tests/test_h9_content_tools.py::TestH9ResearchTool::test_11_research_overview_depth PASSED [ 66%]
tests/test_h9_content_tools.py::TestH9ResearchTool::test_12_research_deep_depth PASSED [ 68%]
tests/test_h9_content_tools.py::TestH9ResearchTool::test_13_research_missing_topic_error PASSED [ 69%]
tests/test_h9_content_tools.py::TestH9ResearchTool::test_14_research_invalid_args_error PASSED [ 71%]
tests/test_h9_content_tools.py::TestH9ResearchTool::test_15_research_dispatch_via_registry PASSED [ 72%]
tests/test_h9_content_tools.py::TestH9DiscoverAssetsTool::test_16_discover_assets_with_requirements PASSED [ 73%]
tests/test_h9_content_tools.py::TestH9DiscoverAssetsTool::test_17_discover_assets_with_scene_ids PASSED [ 75%]
tests/test_h9_content_tools.py::TestH9DiscoverAssetsTool::test_18_discover_assets_with_dossier PASSED [ 76%]
tests/test_h9_content_tools.py::TestH9DiscoverAssetsTool::test_19_discover_assets_invalid_args_error PASSED [ 78%]
tests/test_h9_content_tools.py::TestH9DiscoverAssetsTool::test_20_discover_assets_dispatch_via_registry PASSED [ 79%]
tests/test_h9_content_tools.py::TestH9GenerateScriptTool::test_21_generate_script_happy_path PASSED [ 81%]
tests/test_h9_content_tools.py::TestH9GenerateScriptTool::test_22_generate_script_with_creator_dna PASSED [ 82%]
tests/test_h9_content_tools.py::TestH9GenerateScriptTool::test_23_generate_script_missing_dossier_error PASSED [ 84%]
tests/test_h9_content_tools.py::TestH9GenerateScriptTool::test_24_generate_script_dispatch_via_registry PASSED [ 85%]
tests/test_h9_content_tools.py::TestH9RenderTool::test_25_render_happy_path PASSED [ 86%]
tests/test_h9_content_tools.py::TestH9RenderTool::test_26_render_missing_ir_error PASSED [ 88%]
tests/test_h9_content_tools.py::TestH9RenderTool::test_27_render_missing_output_dir_error PASSED [ 89%]
tests/test_h9_content_tools.py::TestH9RenderTool::test_28_render_dispatch_via_registry PASSED [ 91%]
tests/test_h9_content_tools.py::TestHermesCapabilityBridge::test_29_bridge_protocol_conformance PASSED [ 92%]
tests/test_h9_content_tools.py::TestHermesCapabilityBridge::test_30_bridge_model_completion PASSED [ 94%]
tests/test_h9_content_tools.py::TestHermesCapabilityBridge::test_31_bridge_creator_memory_flow PASSED [ 95%]
tests/test_h9_content_tools.py::TestHermesCapabilityBridge::test_32_bridge_subagent_delegation PASSED [ 97%]
tests/test_h9_content_tools.py::TestHermesCapabilityBridge::test_33_bridge_sandboxed_command PASSED [ 98%]
tests/test_h9_content_tools.py::TestHermesCapabilityBridge::test_34_bridge_factory_and_reset PASSED [100%]

======================= 69 passed in 289.11s (0:04:49) ========================
```

### 1.2 Cryptographic HMAC-SHA256 Verification & Tamper Detection
- In `src/security/tokens.py`:
  * Lines 304–323: `to_canonical_payload()` canonicalizes the token into sorted, deterministic dictionary representations with fixed floating-point rounding.
  * Lines 461–469: `sign_capability_token` generates HMAC-SHA256 digests over `json.dumps(token_data, sort_keys=True, separators=(",", ":"))`.
  * Lines 471–482: `verify_capability_token` uses `hmac.compare_digest` for timing-attack resistance.
  * Line 348–368 in `tests/test_h9_m5_sandbox_permission_mcp.py` (`test_02_signature_tampering_detection`) and lines 89–110 in `tests/test_security_tokens.py` (`test_05_token_model_tamper_detection`) prove that any alteration to `allowed_tools`, `subject_id`, or other attributes immediately causes signature verification failure.

### 1.3 Active Cascading Lineage Revocation
- In `src/security/tokens.py`:
  * Lines 70–115: `TokenRevocationRegistry` is thread-safe (`self._lock = threading.Lock()`).
  * Lines 89–105: `is_revoked(token, lineage)` verifies whether the token itself OR any ancestor in its `delegation_lineage` exists in `_revoked_tokens`.
  * Lines 562–565: `derive_child_token` checks `get_token_revocation_registry().is_revoked(parent_token)` before child token creation.
  * Lines 101–104 in `src/security/guard.py`: `verify_token` asserts `revocation_registry.is_revoked(token)`.
  * Test `test_04_token_revocation_registry_and_cascading_lineage` confirms revoking an ancestor root token immediately revokes all child and grandchild tokens down the lineage tree.

### 1.4 Non-Dict and Invalid Argument Safety at Tool Boundaries
- In `tools/h9_content_tools.py`:
  * Lines 228–246: `resolve_capability_token` checks `if isinstance(args, dict)` and `if isinstance(kwargs, dict)` before performing `.get(...)`.
  * In handlers `handle_h9_research` (line 281), `handle_h9_discover_assets` (line 336), `handle_h9_generate_script` (line 391), `handle_h9_render` (line 500), and `handle_h9_publish` (line 554):
    Every handler validates `if not isinstance(args, dict): return tool_error(...)`.
  * In exception handlers, `args.get("raise_on_error") if isinstance(args, dict) else False` ensures no `AttributeError` can occur.
  * Direct invocation verification confirmed:
    `all('error' in json.loads(fn('invalid')) for fn in [handle_h9_discover_assets, handle_h9_generate_script, handle_h9_render, handle_h9_publish]) == True`.

### 1.5 Path Confinement & Asset Download Size Enforcement
- In `src/h9_runtime/execution.py`:
  * Lines 73–94 (`DefaultExecutionRuntime.validate_path`) and lines 237–261 (`HermesExecutionRuntime.validate_path`):
    Target paths are resolved and validated using `resolved.relative_to(root)`. Any escape raises `PathTraversalError`. Null bytes (`\0`) are intercepted and rejected.
- In `src/assets/freezer.py`:
  * Line 34: `AssetSizeExceededError(AssetDownloadError, ValueError)` inherits from both `AssetDownloadError` and `ValueError`.
  * Lines 137–156: `download_stream` checks `Content-Length` header upfront and monitors cumulative downloaded chunk size during streaming. Exceeding `max_size_bytes` immediately raises `AssetSizeExceededError`.
  * Lines 177–181: `download_stream_sandboxed` validates `execution_runtime.validate_path(target_path)` *before* any network connection is opened or data is written.
  * Verified: `issubclass(AssetSizeExceededError, ValueError) == True` and `issubclass(PathTraversalError, ValueError) == True`.

---

## 2. Logic Chain

1. **Premise**: Milestone 5 requires secure sandboxing, strict capability token boundaries, least-privilege calculus, and MCP integration without compromising the Hermes core or introducing security bypasses.
2. **Cryptographic Integrity**:
   - Observations 1.1, 1.2 demonstrate that tokens are canonicalized deterministically and signed with HMAC-SHA256.
   - Any modification to subject, role, or permissions alters the payload hash and triggers `TokenTamperedError` via constant-time verification (`hmac.compare_digest`), preventing timing-channel side attacks and payload tampering.
3. **Lineage Invalidation**:
   - Observation 1.3 proves that delegation records ancestor token IDs into `delegation_lineage`.
   - `TokenRevocationRegistry` checks both the token ID and each ancestor in the lineage list. When a parent or root is revoked, all descendants are automatically marked revoked, preventing orphaned or rogue subagent tokens from executing.
4. **Boundary Robustness**:
   - Observation 1.4 confirms that non-dict or malformed arguments passed to any of the five tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, `h9.publish`) are intercepted at the perimeter.
   - No unhandled `AttributeError` or interpreter crash occurs; standard JSON error envelopes with `status="error"` are returned.
5. **Sandbox & Download Confinement**:
   - Observation 1.5 shows path resolution strictly checks `relative_to(root)` and blocks null-byte injections.
   - Media streaming caps both upfront HTTP headers and streamed bytes, raising `AssetSizeExceededError` (which is also catchable as a standard `ValueError`).
   - `download_stream_sandboxed` enforces `validate_path` prior to initiating HTTP requests, neutralizing SSRF / arbitrary filesystem overwrite vectors.
6. **Zero Integrity Violations**:
   - Review of test implementations and production code revealed no mock shortcuts, hardcoded test assertions embedded in production methods, or dummy facades.
   - Actual processes and render artifacts are generated and validated on disk.
7. **Conclusion**: All acceptance criteria for Milestone 5 are fully met.

---

## 3. Caveats

- **External Network Dependency**: Unit and integration tests mock external web endpoints (`urllib.request.urlopen`) to ensure deterministic offline execution while testing the full streaming, chunking, and size capping logic.
- **Windows vs. POSIX Process Groups**: Subprocess killing uses `taskkill /F /T` or `proc.kill()` on Windows environments where `os.killpg` is unavailable. The runtime transparently abstracts this, and process timeout returns exit code 124 with stderr reporting across platforms.
- **No Unexplored Areas**: All four specified review focus areas were independently verified.

---

## 4. Conclusion

Milestone 5 (Sandbox, Permission & MCP Integration) is **sound, secure, and production-ready**.
- Subprocess sandboxing operates through `HermesExecutionRuntime` with process group isolation and timeout kill semantics.
- Capability token calculus enforces least privilege ($P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$).
- Active cascading revocation immediately invalidates delegated subagent lineage.
- Boundary handlers safely process malformed and non-dict inputs.
- Filesystem jails and asset downloads are bounded and safe against traversal and resource exhaustion.

---

## 5. Verification Method

To independently reproduce and verify this review:

```powershell
# 1. Run Milestone 5 test suites (69 tests total)
.venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py tests/test_security_tokens.py tests/test_h9_content_tools.py -v

# 2. Verify non-dict tool argument safety across all H9 content tools
.venv\Scripts\python.exe -c "from tools.h9_content_tools import handle_h9_render, handle_h9_publish, handle_h9_generate_script, handle_h9_discover_assets; import json; assert all('error' in json.loads(fn('invalid')) for fn in [handle_h9_discover_assets, handle_h9_generate_script, handle_h9_render, handle_h9_publish]); print('Tool boundary non-dict safe')"

# 3. Verify exception inheritance compliance
.venv\Scripts\python.exe -c "from src.assets.freezer import AssetSizeExceededError; from src.security.tokens import PathTraversalError; assert issubclass(AssetSizeExceededError, ValueError) and issubclass(PathTraversalError, ValueError); print('Exceptions subclass ValueError')"
```

### Invalidation Conditions
- Any of the 69 tests failing.
- Tampered token payload accepted by `SecurityGuard.verify_token`.
- Grandchild token usable after revoking its root delegator.
- A non-dict tool invocation raising an unhandled `AttributeError`.
- Path traversal outside session root succeeding.

---

## Review Summary

**Verdict**: APPROVE

### Findings
- None (all items adhere to architecture specifications and security requirements).

### Verified Claims
- `P_child = P_parent ∩ P_role ∩ P_workflow` calculus → verified via `test_01_capability_calculus_intersection` & `test_01_least_privilege_derivation_calculus` → PASS
- HMAC-SHA256 signature verification & payload tamper detection → verified via `test_02_signature_tampering_detection` & `test_05_token_model_tamper_detection` → PASS
- Active cascading revocation down lineage tree → verified via `test_04_token_revocation_registry_and_cascading_lineage` → PASS
- 4-tier tool gating preventing unauthorized roles from calling `h9.render` and `h9.publish` → verified via `test_05_four_tier_tool_gating_researcher_blocked_from_render_and_publish` → PASS
- Subprocess timeout kill returning exit code 124 with stderr message → verified via `test_03_command_timeout_kill` → PASS
- Path traversal rejection via `validate_path` → verified via `test_04_path_confinement_and_traversal_rejection` → PASS
- Dynamic MCP tool registration, discovery, invocation, and error handling → verified via `TestR53HermesMCPIntegration` (4 tests) → PASS
- Non-dict argument handling at tool boundaries → verified via test suite and independent inline assertion → PASS
- `AssetSizeExceededError` and `PathTraversalError` inheriting `ValueError` → verified via runtime inspection → PASS

### Coverage Gaps
- None.

### Unverified Items
- None.

---

## Challenge Report

**Overall Risk Assessment**: LOW

### Challenges

#### [Low] Challenge 1: Wildcard Set Intersection in Capability Calculus
- **Assumption challenged**: Root and orchestrator tokens with `{"*"}` might produce empty sets when intersected with concrete permission sets if only `{"*"}` is present in the role permissions.
- **Evaluation**: Verified that `ROLE_PERMISSIONS["orchestrator"]` and `STAGE_PERMISSIONS["ROOT"]` contain both `"*" ` and `*ALL_PERMISSIONS`. When intersected with concrete tool names, `{"*", *ALL_PERMISSIONS} & {"h9.research"}` yields `{"h9.research"}` as expected.
- **Blast radius**: Minimal.
- **Defense in place**: Robust union of wildcard and canonical permissions in role definitions.

#### [Low] Challenge 2: Non-Dict Parameter Passing to Tool Boundaries
- **Assumption challenged**: Invoking tool functions directly with strings or integers might cause `.get()` attribute errors in capability token extraction or error logging.
- **Evaluation**: Verified that `resolve_capability_token` guards argument inspection with `isinstance(args, dict)` and each tool handler immediately returns structured error JSON if `not isinstance(args, dict)`.
- **Blast radius**: None.
- **Defense in place**: Upfront type guards on all five tool entry points.

#### [Low] Challenge 3: Stream Download Resource Exhaustion
- **Assumption challenged**: A remote server omitting `Content-Length` or using chunked transfer encoding could stream arbitrary gigabytes before hitting disk checks.
- **Evaluation**: Verified that `download_stream` tracks `total_bytes` accumulated across chunks and raises `AssetSizeExceededError` as soon as `total_bytes > max_size_bytes`, terminating the stream immediately.
- **Blast radius**: None.
- **Defense in place**: Chunk-level byte accumulator and threshold abort.
