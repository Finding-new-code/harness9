# Handoff Report — explorer_2_m5

**Task**: Milestone 5 Technical Exploration — Part 2: Capability Tokens & Principle-of-Least-Privilege Permission Boundary (R5.2)  
**Author**: explorer_2_m5 (Read-Only Technical Explorer)  
**Date**: 2026-09-05T00:35:00Z  
**Target File**: `g:\Finding-new-code\harness9\.agents\explorer_2_m5\handoff.md`  

---

## Executive Summary
This investigation provides a comprehensive architectural and engineering analysis of the **Principle-of-Least-Privilege Capability Token Engine** and **Tool Permission Gating** for Milestone 5 (Requirement R5.2). 
The investigation revealed that:
1. `src/security/tokens.py` and `src/security/guard.py` already implement a robust HMAC-SHA256 signed `CapabilityToken` model with set-intersection calculus ($P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$), path confinement, and network egress controls (verified via 16 passing tests in `tests/test_security_tokens.py`).
2. However, token revocation is currently limited to passive TTL expiration; no active token revocation registry or cascading lineage invalidation exists.
3. In the Hermes runtime layer (`src/h9_runtime/`), tool restriction in subagents is currently handled via a static blacklist (`DefaultAgentRuntime.BLOCKED_TOOLS = frozenset([...])` in `src/h9_runtime/agent.py:78-87`), rather than dynamic capability token enforcement.
4. The H9 content tools suite in `tools/h9_content_tools.py` currently registers only 4 tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`); `h9.publish` is missing despite being mandated by R5/R6 requirements.
5. In `tools/h9_content_tools.py` and `src/h9_runtime/bridge.py`, capability tokens are not yet checked upon tool execution or bridge dispatch.
6. A concrete 4-tier defense-in-depth permission verification engine is designed to connect capability tokens across `tools/h9_content_tools.py`, `src/h9_runtime/bridge.py`, and `src/h9_runtime/agent.py`.

---

## 1. Observation

### 1.1 Capability Token Architecture in `src/security/`
Direct inspection of `src/security/tokens.py`, `src/security/guard.py`, and `src/security/__init__.py` reveals:

1. **Capability Token Data Model** (`src/security/tokens.py:64-142`):
   ```python
   class CapabilityToken(BaseModel):
       token_id: str = Field(default_factory=lambda: f"cap_{uuid.uuid4().hex[:16]}")
       parent_token_id: Optional[str] = Field(default=None)
       subject_id: str
       role: str = Field(default="worker")
       workflow_id: str
       workflow_stage: Optional[str] = Field(default=None)
       allowed_tools: Set[str] = Field(default_factory=set)
       allowed_write_paths: Set[str] = Field(default_factory=set)
       allowed_read_paths: Set[str] = Field(default_factory=set)
       allowed_network_hosts: Set[str] = Field(default_factory=set)
       created_at_utc: float = Field(default_factory=lambda: time.time())
       expires_at_utc: float = Field(default_factory=lambda: time.time() + 3600.0)
       delegation_depth: int = Field(default=0, ge=0)
       max_delegation_depth: int = Field(default=3, ge=0)
       delegation_lineage: List[str] = Field(default_factory=list)
       metadata: Dict[str, Any] = Field(default_factory=dict)
       signature: Optional[str] = Field(default=None)
   ```
2. **Intersection Calculus** (`src/security/tokens.py:271-284`):
   ```python
   def calculate_capability_token(
       parent_perms: Set[str],
       role_perms: Set[str],
       workflow_perms: Set[str],
   ) -> Set[str]:
       """Calculate child permission set via set intersection:
       P_child = P_parent ∩ P_role ∩ P_workflow
       """
       effective_parent = parent_perms
       if "*" in parent_perms:
           return role_perms.intersection(workflow_perms)
       return effective_parent.intersection(role_perms).intersection(workflow_perms)
   ```
   Furthermore, `derive_child_token` (`src/security/tokens.py:349-490`) enforces:
   - Parent expiration check (`if parent_token.is_expired(now): raise TokenExpiredError(...)`).
   - Parent signature verification (`if not parent_token.verify_signature(secret_key): raise TokenTamperedError(...)`).
   - Delegation depth check (`if parent_token.delegation_depth >= parent_token.max_delegation_depth: raise DelegationLimitExceededError(...)`).
   - Monotonic path confinement (`_intersect_paths`) and network egress host intersection (`_intersect_hosts`).
   - Expiration clamping (`child_expires_at = min(requested_expiry, parent_token.expires_at_utc)`).
   - Ancestor lineage chaining (`lineage = list(parent_token.delegation_lineage) + [parent_token.token_id]`).
3. **Cryptographic Signing and Tampering Detection** (`src/security/tokens.py:286-305`):
   - Canonical payload generation (`to_canonical_payload()`, lines 168-188) sorts sets/keys and rounds timestamps.
   - HMAC-SHA256 hex digest calculation (`sign_capability_token()`).
   - Constant-time verification (`verify_capability_token()` using `hmac.compare_digest`).
   - Confirmed by `tests/test_security_tokens.py:test_05_token_model_tamper_detection`, which verifies that altering `allowed_tools` or `subject_id` causes `verify_signature` to return `False`.
4. **Active Revocation Absence**:
   - `grep_search` for `revoc` in `src/security/` returned zero matches.
   - Tokens can only expire passively via `expires_at_utc`. There is no mechanism to invalidate a compromised token or cancel a child delegation tree mid-turn.
5. **Existing Verification Suite**:
   - Executing `.venv\Scripts\python.exe -m unittest tests/test_security_tokens.py` completed with:
     ```
     Ran 16 tests in 0.217s
     OK
     ```

---

### 1.2 Hermes Tool Permission & Security Gates
Inspection of Hermes core files revealed how permissions, toolsets, and execution gates operate:

1. **Tool Registry & Service Gating** (`tools/registry.py`):
   - `ToolRegistry.register(name, toolset, schema, handler, check_fn, ...)` (line 763).
   - In `get_definitions(tool_names)` (lines 1044-1091):
     - Only tools whose `check_fn()` returns `True` are returned. Results are memoized for ~30 seconds via `_check_fn_cached`.
     - Inactive tools contribute 0 prompt tokens to LLM context (Rung 3 of Footprint Ladder).
   - In `dispatch(name, args, ...)` (lines 1128-1169):
     - Handler is looked up and executed.
     - Results are normalized via `_normalize_handler_result` to a string or multimodal envelope.
     - Exceptions are caught and formatted as `{"error": "..."}` via `tool_error`.
2. **Session Scoping & Tool Search Bridge Gate** (`model_tools.py`):
   - In `handle_function_call(function_name, function_args, ...)`:
     - Lines 1321-1334: Scopes catalog to session's `enabled_toolsets` and `disabled_toolsets`.
     - Lines 1357-1370: Defense-in-depth bridge gate:
       ```python
       _scoped_deferrable = _ts_mod.scoped_deferrable_names(current_defs)
       if underlying_name not in _scoped_deferrable:
           return _return_bridge_result(
               tool_error(
                   f"'{underlying_name}' is not available in this session. "
                   "Use tool_search to find tools you can call."
               )
           )
       ```
     - Pre-tool call hooks (`_dispatch_pre_tool_call_hooks`, lines 1435-1467): If a hook returns a `block_message`, the tool execution is halted and returns `tool_error(block_message)` with `status="blocked"`.
     - ACP Edit Approval (`maybe_require_edit_approval`, lines 1472-1509): Blocks file edits without client approval.
3. **Agent Runtime Tool Invocation** (`agent/agent_runtime_helpers.py` & `run_agent.py`):
   - `AIAgent._invoke_tool` delegates to `agent.agent_runtime_helpers.invoke_tool` (lines 3437-3745).
   - Agent-level tools (`todo`, `memory`, `session_search`, `clarify`) are handled internally; all other tools are dispatched to `model_tools.handle_function_call()`.
4. **Current H9 Subagent Tool Isolation** (`src/h9_runtime/agent.py`):
   - Lines 78-88:
     ```python
     BLOCKED_TOOLS = frozenset(
         [
             "delegate_task",
             "clarify",
             "memory",
             "h9.render",
             "send_message",
             "cronjob",
         ]
     )
     ```
   - Lines 163-166:
     ```python
     if allowed_toolsets is not None:
         sanitized_tools = [t for t in allowed_toolsets if t not in self.BLOCKED_TOOLS]
     else:
         sanitized_tools = self.DEFAULT_ALLOWED_TOOLS.copy()
     ```
   - This relies on a hardcoded, static blocked list rather than dynamic, signed capability token calculus.

---

### 1.3 H9 Tool Permission Enforcement & Gap Analysis
Inspection of `tools/h9_content_tools.py`, `src/h9_runtime/bridge.py`, and `src/models/contracts.py` revealed:

1. **Current Tool Set in `tools/h9_content_tools.py`**:
   - `h9.research` (alias `h9_research`): lines 394-411
   - `h9.discover_assets` (alias `h9_discover_assets`): lines 413-431
   - `h9.generate_script` (alias `h9_generate_script`): lines 433-451
   - `h9.render` (alias `h9_render`): lines 453-471
   - **Missing Tool**: `h9.publish` (and `h9_publish`) is completely absent from `tools/h9_content_tools.py`, despite being explicitly specified in:
     - `ORIGINAL_REQUEST.md:99`: *"Permission tests verify that restricted agents or execution scopes cannot call unauthorized H9 tools (e.g., render or publish)."*
     - User prompt: *"How can capability tokens be checked on H9 tools (`h9.render`, `h9.publish`, `h9.generate_script`, `h9.research`, `h9.discover_assets`)?"*
     - Contract `PublishPackage` is already defined in `src/models/contracts.py:490-504`.
2. **Current Lack of Capability Token Checks in Handlers**:
   - `handle_h9_research`, `handle_h9_discover_assets`, `handle_h9_generate_script`, and `handle_h9_render` currently extract arguments and forward directly to `bridge = get_capability_bridge(session_id=session_id)`.
   - None of the handlers check a `CapabilityToken`, verify a cryptographic signature, or assert that the calling agent's `allowed_tools` contains the tool name.
   - Any agent that knows the tool name can invoke `h9.render` if `h9_content` toolset is reachable.

---

## 2. Logic Chain

1. **Premise 1**: Security requirement R5.2 / R6 dictates that principle-of-least-privilege capability tokens must govern tool execution, ensuring that child agents or restricted steps cannot execute unauthorized tools (e.g. `h9.render`, `h9.publish`).
2. **Premise 2**: `src/security/tokens.py` and `src/security/guard.py` provide mathematical and cryptographic primitives (`calculate_capability_token`, `derive_child_token`, `SecurityGuard.enforce_tool_execution`, `SecurityGuard.enforce_filesystem_access`), but they are currently disconnected from `tools/h9_content_tools.py` and `src/h9_runtime/bridge.py`.
3. **Premise 3**: In `src/h9_runtime/agent.py`, `DefaultAgentRuntime` uses a static `BLOCKED_TOOLS` set (`"h9.render"`, `"delegate_task"`, etc.) which does not scale, does not handle lifecycle stages, does not prevent path traversal, and does not check cryptographic signatures.
4. **Premise 4**: For an agent or subagent to be securely restricted:
   - When a session is created (`create_session`), a signed root or intermediate token must be bound to that session.
   - When a subagent is delegated (`delegate_subagent`), a child token must be derived using $P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$ and bound to the subagent session.
   - When a tool is invoked (e.g. `h9.render`), the handler and the bridge must inspect the active token. If `"h9.render"` is not in `token.allowed_tools`, execution must be blocked with `PermissionDeniedError` (returned as a standard JSON error).
   - If an unauthorized subagent (e.g. `role="researcher"`, whose role permissions are `{"web_search", "web_extract", "read_file", "h9.research"}`) attempts to invoke `h9.render` or `h9.publish`, the intersection calculus ensures `h9.render` is not in its `allowed_tools`, and the tool execution is rejected.
5. **Premise 5**: Token expiration (TTL) alone is insufficient for long-running workflows. If a session is interrupted or a security violation is flagged, an active Revocation Registry (`TokenRevocationRegistry`) must immediately invalidate the token and transitively invalidate all child tokens in its delegation lineage.
6. **Premise 6**: To satisfy the explicit requirements of R5.2, `h9.publish` must be added to `tools/h9_content_tools.py` with its schema, handler, and toolset registration, accompanied by corresponding capability checks.

---

## 3. Permission Guard Engine Design

The Permission Guard Engine connects `src/security/` to the H9 runtime and tools via a 4-tier defense-in-depth architecture:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     Hermes Agent Runtime                                        │
│  AIAgent Turn Loop  ───►  model_tools.py  ───►  tools/registry.py (dispatch)                    │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         Tier 1: Toolset & Schema Gating (Preventative)                          │
│  - AgentRuntime / delegate_subagent scopes enabled_toolsets to child token permissions           │
│  - Unavailable tools are omitted from LLM prompt schema                                         │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                     Tier 2: Tool Handler Permission Guard (Boundary Defense)                     │
│  tools/h9_content_tools.py: handle_h9_*                                                         │
│  - Resolve token via ContextVar / Session Registry / kwargs                                     │
│  - Validate signature & check token revocation (TokenRevocationRegistry)                        │
│  - Check tool permission: guard.enforce_tool_execution(token, "h9.<tool>")                       │
│  - Return JSON tool_error on failure; never unhandled exception                                 │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                     Tier 3: Runtime Bridge Security Guard (Internal Defense)                     │
│  src/h9_runtime/bridge.py: HermesCapabilityBridge                                               │
│  - Enforces tool authorization on programmatic bridge method calls                              │
│  - Enforces strict filesystem path confinement (output_dir within allowed_write_paths)           │
│  - Enforces network egress allowlist for research and external media downloads                  │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    Tier 4: Dynamic Calculus in Subagent Delegation (Least Privilege)             │
│  src/h9_runtime/agent.py: delegate_subagent                                                     │
│  - Derives child token: P_child = P_parent ∩ P_role ∩ P_workflow                                │
│  - Binds child token to subagent session context                                                │
│  - Enforces max delegation depth and appends to delegation_lineage                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Token Revocation Registry (`src/security/revocation.py` or extension to `guard.py`)
To solve the revocation gap, implement a centralized, thread-safe `TokenRevocationRegistry`:

```python
class TokenRevocationRegistry:
    """Thread-safe revocation registry tracking invalidated capability tokens."""

    def __init__(self) -> None:
        self._revoked_tokens: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def revoke(self, token_id: str, reason: str = "manual_revocation") -> None:
        """Revoke a token by ID."""
        with self._lock:
            self._revoked_tokens[token_id] = {
                "revoked_at_utc": time.time(),
                "reason": reason,
            }

    def is_revoked(self, token: CapabilityToken) -> bool:
        """Check if token itself OR any ancestor in its lineage has been revoked."""
        with self._lock:
            if token.token_id in self._revoked_tokens:
                return True
            for ancestor_id in token.delegation_lineage:
                if ancestor_id in self._revoked_tokens:
                    return True
        return False
```

### 3.2 Session Token Binding & Context Propagation
Use Python's `contextvars` and a session token map in `src/security/guard.py`:

```python
import contextvars

# Thread/task-local active capability token
current_capability_token: contextvars.ContextVar[Optional[CapabilityToken]] = contextvars.ContextVar(
    "current_capability_token", default=None
)

class SecurityGuard:
    def __init__(self, ...):
        ...
        self._session_tokens: Dict[str, CapabilityToken] = {}
        self._revocation_registry = TokenRevocationRegistry()

    def bind_session_token(self, session_id: str, token: CapabilityToken) -> None:
        self.verify_token(token)
        self._session_tokens[session_id] = token

    def get_session_token(self, session_id: str) -> Optional[CapabilityToken]:
        return self._session_tokens.get(session_id)

    def revoke_session_token(self, session_id: str, reason: str = "session_closed") -> None:
        token = self._session_tokens.pop(session_id, None)
        if token:
            self._revocation_registry.revoke(token.token_id, reason=reason)

    def verify_token(self, token: CapabilityToken) -> bool:
        # Existing expiration and signature checks ...
        if self._revocation_registry.is_revoked(token):
            raise PermissionDeniedError(
                f"Token {token.token_id} (or an ancestor in its lineage) has been revoked."
            )
        return True
```

### 3.3 Adding `h9.publish` to `tools/h9_content_tools.py`
Define `H9_PUBLISH_SCHEMA`, `handle_h9_publish`, and register under `h9_content`:

```python
H9_PUBLISH_SCHEMA: Dict[str, Any] = {
    "name": "h9.publish",
    "description": "Package, license, and distribute rendered video content to target platforms.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "Production project identifier."},
            "video_path": {"type": "string", "description": "Filesystem path to rendered MP4 video artifact."},
            "title": {"type": "string", "description": "Release title for broadcast."},
            "description": {"type": "string", "description": "Video description and show notes."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Metadata discovery tags."},
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["youtube", "tiktok", "instagram", "local_export"]},
                "default": ["local_export"],
                "description": "Target publishing platforms.",
            },
        },
        "required": ["project_id", "video_path", "title"],
    },
}

def handle_h9_publish(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handler for h9.publish / h9_publish tool."""
    # Capability token enforcement
    session_id = kwargs.get("session_id") or "default_session"
    token = resolve_capability_token(args, kwargs, session_id)
    
    guard = get_security_guard()
    try:
        if token is not None:
            guard.enforce_tool_execution(token, "h9.publish")
            guard.enforce_filesystem_access(token, args.get("video_path", ""), mode="read")
        elif is_strict_security_mode():
            return tool_error("Permission denied: CapabilityToken required for h9.publish in strict mode.")
    except SecurityError as sec_err:
        return tool_error(f"Permission denied: {sec_err}", error_type="permission_denied")

    # Domain publishing logic ...
```

### 3.4 Updating Handlers in `tools/h9_content_tools.py`
Wrap all 5 tools with capability token verification:
- `h9.research` $\to$ enforces `h9.research`
- `h9.discover_assets` $\to$ enforces `h9.discover_assets`
- `h9.generate_script` $\to$ enforces `h9.generate_script`
- `h9.render` $\to$ enforces `h9.render` AND `allowed_write_paths` on `output_dir`
- `h9.publish` $\to$ enforces `h9.publish` AND `allowed_read_paths` on `video_path`

### 3.5 Updating `src/h9_runtime/agent.py` (`delegate_subagent`)
Replace static `BLOCKED_TOOLS` with dynamic capability derivation:
1. Fetch parent token: `parent_token = self.get_session_token(parent_session_id) or create_root_token(...)`
2. Define role permission map:
   ```python
   ROLE_PERMISSIONS = {
       "researcher": {"web_search", "web_extract", "read_file", "h9.research"},
       "scriptwriter": {"read_file", "write_file", "h9.generate_script"},
       "asset_specialist": {"read_file", "write_file", "h9.discover_assets"},
       "video_editor": {"read_file", "write_file", "h9.render"},
       "publisher": {"read_file", "h9.publish"},
       "orchestrator": {"*"},
   }
   ```
3. Define workflow stage permission map:
   ```python
   WORKFLOW_STAGE_PERMISSIONS = {
       "RESEARCH_IN_PROGRESS": {"web_search", "web_extract", "read_file", "h9.research"},
       "SCRIPTING_IN_PROGRESS": {"read_file", "write_file", "h9.generate_script"},
       "ASSET_DISCOVERY_IN_PROGRESS": {"read_file", "write_file", "h9.discover_assets"},
       "RENDERING_IN_PROGRESS": {"read_file", "write_file", "h9.render"},
       "PUBLISHING_IN_PROGRESS": {"read_file", "h9.publish"},
   }
   ```
4. Derive child token via `derive_child_token`:
   ```python
   child_token = derive_child_token(
       parent_token=parent_token,
       child_subject_id=subagent_id,
       role_allowed_tools=ROLE_PERMISSIONS.get(role, {"read_file"}),
       workflow_allowed_tools=WORKFLOW_STAGE_PERMISSIONS.get(workflow_stage, {"*"}),
       child_role=role,
       workflow_stage=workflow_stage,
       secret_key=self.secret_key,
   )
   ```
5. Bind `child_token` to the subagent session. When the subagent runs, it receives `child_token.allowed_tools` as its enabled toolset. Even if the subagent tries to bypass and invoke `h9.render`, `h9.render` is not in `child_token.allowed_tools`, and the tool handler will reject it with a `PermissionDeniedError`!

---

## 4. Caveats

1. **Secret Key Distribution**: For HMAC-SHA256 signature verification to be effective across processes (e.g. CLI vs Gateway vs Subprocess), all components must share a master secret key (e.g., loaded from `config.yaml` or an internal secret provider, never hardcoded in repository code).
2. **Backward Compatibility**: Existing unit tests (e.g. `tests/test_h9_content_tools.py`) dispatch tools without an explicit token. The guard must support an optional/permissive fallback mode when `session_id` is `"default_session"` or when strict security mode is not enabled (`HERMES_STRICT_CAPABILITY_TOKENS=0`), ensuring zero regressions across the 34 existing tests.
3. **No Network Egress Interception in Python Standard Library**: `SecurityGuard.check_network_egress` checks hoststrings, but Python standard library sockets (`urllib`, `requests`, `httpx`) do not intercept raw sockets automatically without monkeypatching or an external egress proxy (as documented in `docs/security/network-egress-isolation.md`). In H9, network egress enforcement is applied at the tool boundary (validating URLs before HTTP requests).

---

## 5. Conclusion

1. **Foundations are Sound**: `src/security/tokens.py` and `src/security/guard.py` already implement the mathematical model ($P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$), cryptographic HMAC signing, delegation depth limits, and path confinement.
2. **Missing Links Identified**:
   - Explicit token revocation is missing and must be added via `TokenRevocationRegistry`.
   - `h9.publish` is missing from `tools/h9_content_tools.py` and must be implemented.
   - `src/h9_runtime/agent.py` must switch from static `BLOCKED_TOOLS` to dynamic capability token derivation.
   - `tools/h9_content_tools.py` and `src/h9_runtime/bridge.py` must enforce capability tokens on every invocation.
3. **Actionable Implementation Plan**:
   - **Step 1**: Add `TokenRevocationRegistry` and session token binding to `src/security/guard.py`.
   - **Step 2**: Add `h9.publish` and alias `h9_publish` to `tools/h9_content_tools.py`.
   - **Step 3**: Wire `SecurityGuard.enforce_tool_execution` and `enforce_filesystem_access` into all 5 tool handlers in `tools/h9_content_tools.py`.
   - **Step 4**: Update `src/h9_runtime/agent.py` to derive and bind signed child capability tokens in `delegate_subagent`.
   - **Step 5**: Implement comprehensive integration tests in `tests/test_h9_capability_boundary.py` covering unauthorized tool rejection, expired token rejection, tampered token rejection, path traversal rejection, and cascading token revocation.

---

## 6. Verification Method

To independently verify the investigation findings and the subsequent implementation:

1. **Verify Security Token Primitives**:
   ```bash
   .venv\Scripts\python.exe -m unittest tests/test_security_tokens.py
   ```
   *Expected*: All 16 tests pass, confirming HMAC-SHA256 signing, intersection calculus, and path confinement.

2. **Verify Existing H9 Content Tools Baseline**:
   ```bash
   .venv\Scripts\python.exe -m unittest tests/test_h9_content_tools.py
   ```
   *Expected*: All 34 tests pass, confirming zero regressions.

3. **Verify Milestone 4 Baseline (Provider, Memory, Subagent)**:
   ```bash
   .venv\Scripts\python.exe -m unittest tests/test_h9_provider_memory_subagent.py
   ```
   *Expected*: All tests pass.

4. **Verify Capability Boundary Tests (to be authored in Milestone 5)**:
   ```bash
   .venv\Scripts\python.exe -m unittest tests/test_h9_capability_boundary.py
   ```
   *Test Cases to Verify*:
   - Researcher subagent calling `h9.render` $\to$ raises `PermissionDeniedError` / returns error JSON.
   - Researcher subagent calling `h9.publish` $\to$ raises `PermissionDeniedError` / returns error JSON.
   - Video editor subagent calling `h9.render` with valid IR $\to$ succeeds.
   - Video editor subagent calling `h9.render` with `output_dir="../../etc"` $\to$ raises `PathTraversalError`.
   - Tampered token payload $\to$ raises `TokenTamperedError`.
   - Expired token $\to$ raises `TokenExpiredError`.
   - Revoked parent token $\to$ rejects child subagent execution.
