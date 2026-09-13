# Security Model & Capability Calculus: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/security/`  
**Cross-References:** `docs/ARCHITECTURE.md`, `docs/SYSTEM_DESIGN.md`, `docs/adrs/ADR-005.md`  

---

## 1. Threat Model & Security Objectives

Autonomous AI agent execution environments face distinct attack vectors when executing multi-stage production pipelines:
1. **Privilege Escalation**: A subagent (e.g. researcher) attempting to invoke destructive administrative tools (e.g. deleting projects, accessing credentials).
2. **Path Traversal & Filesystem Escapes**: Crafted filenames or output paths using `../` sequences attempting to overwrite system files or read sensitive user secrets (`~/.hermes/.env`).
3. **Data Exfiltration via Network Egress**: Rogue or hallucinated tool calls transmitting private project briefs, scripts, or audio to unauthorized third-party servers.
4. **Token Tampering & Signature Forgery**: Altering permissions in serialized JSON payloads to grant unauthorized tool authority.
5. **Replay & Unbounded Delegation**: Using expired capability tokens or delegating unbounded child chains to circumvent execution limits.

Harness 9 addresses these threats using a **Principle-of-Least-Privilege Capability Token Engine** combined with an active **Runtime Security Guard**.

---

## 2. Mathematical Capability Calculus

Every subagent, worker, or tool execution requires an active `CapabilityToken`. A derived child token cannot possess authorities exceeding the intersection of its delegator, role, and workflow stage.

### 2.1 The Intersection Formula
$$\mathcal{P}_{\text{child}} = \mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$$

Where:
- $\mathcal{P}_{\text{parent}}$: Explicit permissions held by the delegating parent token.
- $\mathcal{P}_{\text{role}}$: Maximum permitted authorities for the functional role (e.g. `researcher`, `scriptwriter`, `audio_engineer`, `renderer`).
- $\mathcal{P}_{\text{workflow}}$: Authorities authorized for the active state machine lifecycle stage.

### 2.2 Proof of Monotonic Restriction
Let $A \subseteq B$ denote permission containment. By definition of set intersection:
$$\mathcal{P}_{\text{child}} \subseteq \mathcal{P}_{\text{parent}}, \quad \mathcal{P}_{\text{child}} \subseteq \mathcal{P}_{\text{role}}, \quad \mathcal{P}_{\text{child}} \subseteq \mathcal{P}_{\text{workflow}}$$
Therefore, no delegation operation can ever expand permissions beyond the parent's authority ($\mathcal{P}_{\text{child}} \le \mathcal{P}_{\text{parent}}$).

---

## 3. Cryptographic Token Specification

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CAPABILITY TOKEN                                 │
│  • token_id: "cap_7a9f82d1c0e3"                                             │
│  • parent_token_id: "root_001"                                              │
│  • subject_id: "worker_researcher_01"                                       │
│  • role: "researcher"                                                       │
│  • workflow_id: "proj_transistor_001"                                       │
│  • workflow_stage: "RESEARCH_IN_PROGRESS"                                   │
│  • allowed_tools: {"search_web", "fetch_url"}                               │
│  • allowed_write_paths: {"output/proj_transistor_001/research"}             │
│  • allowed_read_paths: {"output/proj_transistor_001"}                        │
│  • allowed_network_hosts: {"commons.wikimedia.org"}                         │
│  • created_at_utc: 1788196400.0                                             │
│  • expires_at_utc: 1788200000.0                                             │
│  • delegation_depth: 1                                                      │
│  • max_delegation_depth: 3                                                  │
│  • delegation_lineage: ["root_001"]                                         │
│  • signature: HMAC-SHA256(Secret, CanonicalPayload)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 HMAC-SHA256 Signing & Verification Protocol
1. **Canonical Serialization**:
   - The token payload (excluding `signature`) is converted to a canonical JSON string with sorted keys and compact separators: `json.dumps(payload, sort_keys=True, separators=(",", ":"))`.
2. **Signature Generation**:
   $$\text{Signature} = \text{HMAC-SHA256}(K_{\text{master}}, \text{CanonicalPayload})$$
3. **Timing-Safe Verification**:
   - Signature checks execute via constant-time comparison (`hmac.compare_digest`) to prevent timing side-channel attacks.

### 3.2 Delegation Rules & Lineage Tracking
1. **Lineage Array**: When token $T_B$ is derived from $T_A$, $T_B.\text{delegation\_lineage} = T_A.\text{delegation\_lineage} + [T_A.\text{token\_id}]$.
2. **Depth Limit**: If $T_A.\text{delegation\_depth} \ge T_A.\text{max\_delegation\_depth}$, derivation is rejected with `DelegationLimitExceededError`.
3. **Expiration Bound**: Child expiration is bounded by parent:
   $$t_{\text{child\_exp}} = \min(t_{\text{now}} + \text{TTL}_{\text{requested}}, t_{\text{parent\_exp}})$$
4. **Parent Validity Gate**: If $T_A$ is expired or has an invalid signature, child derivation is aborted immediately (`TokenExpiredError` / `TokenTamperedError`).

---

## 4. Runtime Sandboxing Guard (`SecurityGuard`)

### 4.1 Tool Execution Whitelisting
- Any model tool call intercepted by the runtime is checked against `token.allowed_tools`.
- If the requested tool name is not in `allowed_tools` (and `*` is not present), execution is blocked and `PermissionDeniedError` is raised.

### 4.2 Filesystem Path Confinement & Traversal Defense
- The guard normalizes and resolves all target paths to absolute filesystem locations using `Path(target).resolve()`.
- **Traversal Defense**:
  - Rejects paths containing null bytes (`\0`).
  - Verifies that `resolved_target` starts with at least one directory prefix in `allowed_write_paths` (for write operations) or `allowed_read_paths` (for read operations).
  - Attempts to escape sandbox root via `../../` trigger `PathTraversalError`.

### 4.3 Network Egress Filtering
- Network calls (HTTP/WebSocket/Socket) are checked against `allowed_network_hosts`.
- Supports exact host matching (`api.elevenlabs.io`) and wildcard domain suffixes (`*.pexels.com`).
- Stages with empty `allowed_network_hosts` operate under `OFFLINE_ONLY` mode; any outbound socket connection raises `NetworkEgressError`.

---

## 5. Security Invariant Matrix

| Security Layer | Invariant Property | Failure Behavior |
|---|---|---|
| **Tool Execution** | $t_{\text{call}} \in \text{Token}.\text{allowed\_tools}$ | Intercepted; raises `PermissionDeniedError` |
| **Filesystem Write** | $\text{Path}.\text{resolve}() \subseteq \text{Token}.\text{allowed\_write\_paths}$ | Intercepted; raises `PathTraversalError` |
| **Filesystem Read** | $\text{Path}.\text{resolve}() \subseteq \text{Token}.\text{allowed\_read\_paths}$ | Intercepted; raises `PathTraversalError` |
| **Network Egress** | $\text{TargetHost} \in \text{Token}.\text{allowed\_network\_hosts}$ | Intercepted; raises `NetworkEgressError` |
| **Token Validity** | $t_{\text{now}} \le \text{Token}.\text{expires\_at\_utc}$ | Intercepted; raises `TokenExpiredError` |
| **Payload Integrity**| $\text{HMAC}(\text{Payload}) == \text{Token}.\text{signature}$ | Intercepted; raises `TokenTamperedError` |
| **Delegation Limit** | $\text{Token}.\text{depth} \le \text{Token}.\text{max\_depth}$ | Intercepted; raises `DelegationLimitExceededError` |
