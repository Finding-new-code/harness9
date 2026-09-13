# Hermes Agent Compatibility & Adapter Specification

**Document Version:** 1.0.0  
**Target Milestone:** M1 (State Machine, Production Contracts & Hermes Adapter)  
**Package Path:** `adapters/hermes/`  
**Status:** Canonical Engineering Specification  

---

## 1. Executive Summary & Architectural Role

The Harness 9 **Hermes Adapter** (`adapters/hermes/`) provides a clean, decoupled integration layer enabling the Hermes Agent platform (including its CLI, TUI, messaging gateways, and Desktop GUI) to orchestrate autonomous video production workflows without polluting the core agent waist or disrupting per-conversation prompt caching.

Harness 9 acts as an external specialized execution subsystem. Through the adapter, Hermes agents can invoke structured tools to generate broadcast-ready rendered MP4 videos, inspect the 17-state deterministic lifecycle progress, and run multi-layer quality evaluation benchmarks.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Hermes Agent Host                             │
│     (AIAgent / CLI / Gateway Platforms / Electron Desktop App)          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                 Service-Gated Tool Calling & JSON Schemas
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    adapters/hermes/ (Adapter Layer)                     │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐  │
│  │   HermesBridge        │ │   HermesSession   │ │   Service-Gated   │  │
│  │   (Execution API)     │ │   Sandbox         │ │   Tool Definitions│  │
│  └───────────┬───────────┘ └─────────┬─────────┘ └─────────┬─────────┘  │
└──────────────┼───────────────────────┼─────────────────────┼────────────┘
               │                       │                     │
               ▼                       ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Harness 9 Core Production OS                          │
│  • 17-State Deterministic Lifecycle State Machine (src/orchestrator/)   │
│  • 17 Pydantic v2 Production Contracts (src/models/)                    │
│  • Domain Engines (Research, Editorial, Scripts, Assets, HyperFrames)   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hermes Invariants & Core Design Principles

In accordance with the Hermes Development Guide (`AGENTS.md`), the Harness 9 adapter adheres strictly to the four core design invariants:

### 2.1 Sacred Per-Conversation Prompt Caching
- **Invariant:** Long-lived conversations rely on deterministic prompt caching. Mid-conversation mutations of past context, dynamic tool swapping, or system prompt alterations invalidate cache prefixes and multiply API costs.
- **Implementation:** The Harness 9 adapter provides **static, byte-stable tool schemas** and fixed system boundaries. Invoking a Harness 9 tool never mutates system prompts, never injects synthetic user turns into conversation history, and maintains strict role alternation (`user` -> `assistant` (tool_call) -> `tool` -> `assistant`).

### 2.2 Narrow Core Waist & The Footprint Ladder
- **Invariant:** Every model tool added to core is sent on every API call, incurring permanent token overhead. Tools must live at the appropriate rung of the Footprint Ladder.
- **Implementation:** Harness 9 tools are exposed as a **Service-Gated Toolset** (`check_fn: check_harness9_available`) under the toolset name `harness9_video`. Tools only appear when enabled for the session, adding zero permanent footprint to standard general-purpose conversations.

### 2.3 Session-Scoped Isolation & State Independence
- **Invariant:** Capability and state are properties of the individual conversation session, never shared process-wide environment state.
- **Implementation:** Every execution is isolated to a `HermesSessionSandbox` keyed by `session_id`. Workspaces, render directories, and audit logs are partitioned per session, preventing cross-session pollution or race conditions.

### 2.4 Hermetic Dependency Isolation
- **Invariant:** Internal production toolchains (GSAP timelines, Playwright headful/headless capture, FFmpeg pipelines) must remain strictly isolated behind clean adapter interfaces.
- **Implementation:** The Hermes Agent core requires zero direct knowledge of video synthesis libraries. All interactions occur via typed Pydantic payloads and JSON-serializable tool responses.

---

## 3. Adapter Package Layout (`adapters/hermes/`)

```
adapters/hermes/
├── __init__.py           # Package exports (HermesBridge, HermesSessionSandbox, tools)
├── sandbox.py            # Session sandbox, directory management & path traversal guards
├── bridge.py             # High-level programmatic API for Hermes AIAgent / CLI
└── tools.py              # OpenAI-compatible function schemas & tool execution handler
```

### Module Responsibilities

| Module | Class / Functions | Description |
|---|---|---|
| `sandbox.py` | `HermesSessionSandbox` | Manages isolated filesystem paths (`workspace/`, `renders/`, `audit/`) per session and enforces path security. |
| `bridge.py` | `HermesBridge` | Orchestrates the 17-state lifecycle state machine, runs the pipeline, and generates `PublishPackage` and `RenderArtifact`. |
| `tools.py` | `get_tool_schemas()`, `handle_tool_call()`, `check_harness9_available()` | Defines JSON schemas for model tool calling and routes tool execution requests. |

---

## 4. Tool Schemas & Interface Specifications

The adapter registers three service-gated tools:

### 4.1 `generate_video_from_brief`

Generates a broadcast-ready rendered MP4 video from a creator topic brief.

#### JSON Schema
```json
{
  "type": "function",
  "function": {
    "name": "generate_video_from_brief",
    "description": "Generate a broadcast-ready rendered MP4 video from a topic brief using the Harness 9 production operating system.",
    "parameters": {
      "type": "object",
      "properties": {
        "topic": {
          "type": "string",
          "description": "The topic, technology, or narrative subject of the video."
        },
        "format": {
          "type": "string",
          "enum": ["16:9", "9:16"],
          "default": "16:9",
          "description": "Target video aspect ratio (16:9 for YouTube/Desktop, 9:16 for Shorts/Reels/TikTok)."
        },
        "duration": {
          "type": "integer",
          "default": 30,
          "description": "Target duration in seconds (between 5 and 300)."
        },
        "offline": {
          "type": "boolean",
          "default": true,
          "description": "Whether to run in 100% deterministic offline mode using curated benchmarks and procedural generation."
        },
        "custom_instructions": {
          "type": "string",
          "description": "Optional custom creator instructions, specific angles, or narrative constraints."
        }
      },
      "required": ["topic"]
    }
  }
}
```

#### Return Value
```json
{
  "success": true,
  "session_id": "cli_session_01",
  "project_id": "proj_cli_session_01_1725100000",
  "topic": "How GPUs Work",
  "video_path": "output/hermes_sessions/cli_session_01/renders/final.mp4",
  "duration_seconds": 30,
  "aspect_ratio": "16:9",
  "elapsed_seconds": 4.12,
  "state": "COMPLETED",
  "state_history": [ ... ],
  "render_artifact": { ... },
  "publish_package": { ... }
}
```

---

### 4.2 `inspect_production_state`

Retrieves real-time or historical telemetry, 17-state lifecycle progress, and audit logs for a given session.

#### JSON Schema
```json
{
  "type": "function",
  "function": {
    "name": "inspect_production_state",
    "description": "Inspect the 17-state lifecycle progress, transition audit logs, and generated artifacts for a video production session.",
    "parameters": {
      "type": "object",
      "properties": {
        "session_id": {
          "type": "string",
          "description": "The session ID of the production run to inspect."
        }
      },
      "required": ["session_id"]
    }
  }
}
```

---

### 4.3 `evaluate_content_quality`

Executes the ContentBench 4-layer quality evaluation suite across research, script, video, and acoustic dimensions.

#### JSON Schema
```json
{
  "type": "function",
  "function": {
    "name": "evaluate_content_quality",
    "description": "Run the 4-layer quality evaluation (ContentBench) on the research, script, video, and acoustic integrity of a production session.",
    "parameters": {
      "type": "object",
      "properties": {
        "session_id": {
          "type": "string",
          "description": "The session ID of the production run to evaluate."
        }
      },
      "required": ["session_id"]
    }
  }
}
```

---

## 5. Session Sandbox & Security Model

To prevent cross-session collision and ensure hermetic execution, every run is sandboxed:

### 5.1 Directory Layout
```
output/hermes_sessions/<session_id>/
├── workspace/                  # Scratch space for raw downloads, transcript JSON, and HTML
│   ├── assets/
│   │   ├── audio/
│   │   │   └── narration.wav
│   │   ├── images/
│   │   │   └── asset_01.svg
│   │   └── transcript.json
│   ├── index.html
│   ├── styles.css
│   └── main.js
├── renders/                    # Final rendered broadcast MP4s
│   └── final.mp4
└── audit/                      # Immutable JSON state machine and evaluation audit records
    ├── state_machine.json
    ├── publish_package.json
    └── evaluation_report.json
```

### 5.2 Security & Path Traversal Guards
- The `HermesSessionSandbox.validate_path(target_path)` method validates that any file accessed or written by the pipeline resolves strictly within the session sandbox root.
- Any attempt to reference files outside the sandbox raises a `ValueError("Path traversal detected")`.
- `HermesSessionSandbox.cleanup_scratch()` cleans up temporary working files after rendering while preserving the finalized MP4 artifact and audit logs.

---

## 6. State Machine Telemetry & Audit Trails

The adapter integrates directly with the 17-state lifecycle machine (`ProductionStateMachine`), transitioning deterministically through:

1. `CREATED`
2. `RESEARCH_PLANNED`
3. `RESEARCH_IN_PROGRESS`
4. `RESEARCH_COMPLETED`
5. `EDITORIAL_ANALYSIS`
6. `ANGLE_SELECTED`
7. `OUTLINE_APPROVED`
8. `SCRIPTING_IN_PROGRESS`
9. `SCRIPT_COMPLETED`
10. `VOICE_GENERATED`
11. `VOICE_QA_PASSED`
12. `ASSETS_DISCOVERED`
13. `ASSETS_FROZEN`
14. `COMPOSITION_GENERATED`
15. `RENDER_IN_PROGRESS`
16. `RENDER_COMPLETED`
17. `COMPLETED`

Every state transition records a timestamped `TransitionRecord` with duration and payload summaries, which is serialized to `audit/state_machine.json`.

---

## 7. Offline Resilience & System Requirements

- **Python Runtime:** Python 3.10, 3.11, 3.12, 3.13.
- **Offline Mode:** When `--offline` is enabled (default), research uses curated benchmark dossiers or procedural synthesis, and assets use deterministic SVG vectors and pure Python WAV synthesis.
- **FFmpeg Integration:** Uses system FFmpeg when available; falls back gracefully to containerized or procedural simulation in test environments.

---

## 8. Verification & Test Attestation

The Hermes Adapter is thoroughly verified by the test suite:
- `tests/test_hermes_adapter.py`: Tests tool registration, schema validity, sandbox creation, path traversal guards, tool call dispatching, and cache preservation.
- `tests/test_state_machine.py`: Tests full 17-state lifecycle transitions and invalid jump rejection.
- `tests/test_contracts.py`: Tests all 17 Pydantic v2 schemas and validation constraints.
