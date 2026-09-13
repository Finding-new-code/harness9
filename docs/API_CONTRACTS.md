# API Contracts & Interface Definitions: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/`, `adapters/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/WORKFLOW_SPEC.md`, `docs/SECURITY_MODEL.md`  

---

## 1. Interface Layer Architecture

Harness 9 exposes three distinct integration surfaces:
1. **Python Programmatic SDK**: Direct object-oriented API for embedding Harness 9 inside Python pipelines, orchestrators, and automated test runners.
2. **Hermes Agent Service-Gated Toolset**: Structured JSON-RPC/OpenAI tool interfaces enabled via `check_harness9_available`.
3. **CLI Interface**: Command-line tools for manual runs, headless batch renders, state inspection, and benchmark auditing.

---

## 2. Python Programmatic SDK API

### 2.1 Studio Pipeline Runner (`src.orchestrator.pipeline.Harness9Pipeline`)
```python
class Harness9Pipeline:
    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        offline_mode: bool = True,
        security_token: Optional[CapabilityToken] = None,
    ): ...

    def execute_production(
        self,
        brief: Union[ContentBrief, Dict[str, Any]],
        creator: Optional[Union[CreatorProfile, Dict[str, Any]]] = None,
    ) -> Tuple[PublishPackage, ProductionCostLedger, BenchmarkReport]:
        """Execute the full 17-state autonomous production lifecycle."""

    def resume_from_state(
        self,
        project_id: str,
        target_state: ProductionState,
    ) -> bool:
        """Resume or advance a paused/failed production workflow."""
```

### 2.2 State Machine Controller (`src.orchestrator.state_machine.ProductionStateMachine`)
```python
class ProductionStateMachine:
    def __init__(self, run_id: str, initial_state: ProductionState = ProductionState.CREATED): ...

    def can_transition(self, target_state: ProductionState) -> bool:
        """Check if transition to target_state is permitted from current_state."""

    def transition_to(
        self,
        target_state: ProductionState,
        payload: Optional[BaseModel] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Advance state machine with contract payload validation and audit logging."""

    def get_history(self) -> List[TransitionRecord]:
        """Retrieve full immutable state transition history."""
```

### 2.3 Hermes Adapter Bridge (`adapters.hermes.bridge.HermesBridge`)
```python
class HermesBridge:
    def __init__(self, session_id: str, base_dir: Optional[Union[str, Path]] = None): ...

    def generate_video(
        self,
        topic: str,
        target_duration: int = 30,
        aspect_ratio: str = "16:9",
        offline_mode: bool = True,
    ) -> Dict[str, Any]:
        """High-level video generation endpoint for Hermes AIAgent."""

    def inspect_state(self) -> Dict[str, Any]:
        """Return current state, stage durations, and artifact index."""
```

### 2.4 Security Capability Engine (`src.security.tokens`, `src.security.guard`)
```python
def create_root_token(
    subject_id: str,
    role: str = "orchestrator",
    workflow_id: str = "wf_root",
    allowed_tools: Optional[Set[str]] = None,
    allowed_write_paths: Optional[Set[str]] = None,
    secret_key: Optional[Union[str, bytes]] = None,
) -> CapabilityToken: ...

def derive_child_token(
    parent_token: CapabilityToken,
    child_subject_id: str,
    role_allowed_tools: Set[str],
    workflow_allowed_tools: Set[str],
    secret_key: Optional[Union[str, bytes]] = None,
) -> CapabilityToken: ...

class SecurityGuard:
    def enforce_tool_execution(self, token: CapabilityToken, tool_name: str) -> None: ...
    def enforce_filesystem_access(self, token: CapabilityToken, target_path: Union[str, Path], mode: str = "write") -> str: ...
    def enforce_network_egress(self, token: CapabilityToken, host: str) -> None: ...
```

---

## 3. Hermes Agent Service-Gated Tool Schemas

When running inside the Hermes Agent platform, Harness 9 exposes three OpenAI-compatible function schemas:

### 3.1 Tool 1: `generate_video_from_brief`
```json
{
  "type": "function",
  "function": {
    "name": "generate_video_from_brief",
    "description": "Generate a broadcast-ready rendered MP4 video from a creative topic brief.",
    "parameters": {
      "type": "object",
      "properties": {
        "topic": {
          "type": "string",
          "description": "The subject matter or concept to explain in the video."
        },
        "format": {
          "type": "string",
          "enum": ["16:9", "9:16", "1:1"],
          "default": "16:9",
          "description": "Visual aspect ratio."
        },
        "duration": {
          "type": "integer",
          "default": 30,
          "minimum": 5,
          "maximum": 600,
          "description": "Target video duration in seconds."
        },
        "offline": {
          "type": "boolean",
          "default": true,
          "description": "Run in 100% deterministic offline mode without external API calls."
        }
      },
      "required": ["topic"]
    }
  }
}
```

### 3.2 Tool 2: `inspect_production_state`
```json
{
  "type": "function",
  "function": {
    "name": "inspect_production_state",
    "description": "Inspect the current 17-state lifecycle state and artifact paths for the active session.",
    "parameters": {
      "type": "object",
      "properties": {
        "include_history": {
          "type": "boolean",
          "default": true,
          "description": "Include full state transition audit trail."
        }
      }
    }
  }
}
```

### 3.3 Tool 3: `evaluate_content_quality`
```json
{
  "type": "function",
  "function": {
    "name": "evaluate_content_quality",
    "description": "Run ContentBench 4-layer evaluation and return quality scorecard.",
    "parameters": {
      "type": "object",
      "properties": {
        "layer": {
          "type": "string",
          "enum": ["all", "research", "script", "video", "cost"],
          "default": "all"
        }
      }
    }
  }
}
```

---

## 4. CLI Command Interface

```bash
# 1. Generate full video from brief
python -m src.orchestrator.cli generate \
    --topic "How GPUs Work: Parallel Computing" \
    --duration 30 \
    --format 16:9 \
    --offline \
    --output ./output/gpu_explainer

# 2. Inspect session lifecycle state
python -m src.orchestrator.cli inspect \
    --session-id "session_gpu_01" \
    --audit-log

# 3. Run ContentBench evaluation suite
python -m src.evaluation.contentbench evaluate \
    --project-dir ./output/gpu_explainer \
    --report-format json

# 4. Verify system pipeline integrity (6 Checkpoints)
python verify_pipeline.py --offline --verbose
```

---

## 5. Error Code & Exception Catalog

| Exception Class | Error Code | HTTP/RPC Status | Description |
|---|---|---|---|
| `StateTransitionError` | `ERR_INVALID_STATE_JUMP` | 400 Bad Request | Attempted an invalid lifecycle state transition. |
| `PermissionDeniedError` | `ERR_UNAUTHORIZED_TOOL` | 403 Forbidden | Capability token does not authorize execution of the requested tool. |
| `TokenExpiredError` | `ERR_TOKEN_EXPIRED` | 401 Unauthorized | Capability token TTL has elapsed. |
| `TokenTamperedError` | `ERR_TOKEN_TAMPERED` | 401 Unauthorized | Cryptographic HMAC signature verification failed. |
| `PathTraversalError` | `ERR_PATH_JAIL_VIOLATION` | 403 Forbidden | Target filesystem path attempts to escape sandbox jail. |
| `NetworkEgressError` | `ERR_EGRESS_BLOCKED` | 403 Forbidden | Host is not in the allowed network egress whitelist. |
| `VoiceQAError` | `ERR_AUDIO_ACOUSTIC_FAIL` | 422 Unprocessable | Audio waveform failed dead air, clipping, or beat drift checks. |
| `CompositionLintError` | `ERR_COMPOSITION_INVALID` | 422 Unprocessable | HTML/GSAP composition failed safe-zone or loop checks. |
