# Agent Skills & Tool Specifications: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `adapters/hermes/`, `tools/`  
**Cross-References:** `docs/API_CONTRACTS.md`, `docs/SECURITY_MODEL.md`  

---

## 1. Skill & Tool Architecture

Harness 9 tools integrate into the Hermes Agent skill ecosystem via **service-gated toolsets**. In accordance with the Footprint Ladder (`AGENTS.md`), tools are not permanently injected into core agent prompts; they are conditionally activated when video generation tasks are requested.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Hermes Agent Core                               │
│                         (AIAgent / LLM Tool Loop)                           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Tool Call Dispatch
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Harness 9 Service-Gated Toolset                        │
│                                                                             │
│  ┌─────────────────────────┐ ┌─────────────────────────┐ ┌───────────────┐  │
│  │ generate_video_from_    │ │ inspect_production_     │ │ evaluate_     │  │
│  │ brief                   │ │ state                   │ │ content_      │  │
│  │ (Full Production Run)   │ │ (Lifecycle Query)       │ │ quality       │  │
│  └────────────┬────────────┘ └────────────┬────────────┘ └───────┬───────┘  │
└───────────────┼───────────────────────────┼──────────────────────┼──────────┘
                │                           │                      │
                ▼                           ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Capability Guard & Execution Sandbox                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Service-Gated Model Tools

### 2.1 `generate_video_from_brief`
- **Description**: Orchestrates the autonomous production lifecycle to generate a rendered MP4 video from a creative topic brief.
- **Service Gate**: `check_harness9_available()`
- **Required Capability**: `tool:generate_video`

#### Parameter Schema
| Parameter | Type | Required | Default | Description |
|---|---|:---:|---|---|
| `topic` | `string` | **Yes** | — | Core concept, technology, or topic to explain in the video. |
| `format` | `string` | No | `"16:9"` | Aspect ratio: `"16:9"` (horizontal) or `"9:16"` (vertical reels/shorts). |
| `duration` | `integer` | No | `30` | Target runtime in seconds ($5 \le \text{duration} \le 600$). |
| `offline` | `boolean` | No | `true` | When true, runs 100% deterministically offline using local synthesizers and procedural assets. |
| `creator_id`| `string` | No | `None` | Creator ID to apply Brand Constitution and Creator DNA preferences. |

#### Return Payload Schema
```json
{
  "status": "success",
  "project_id": "proj_transistor_001",
  "video_path": "renders/final.mp4",
  "duration_seconds": 30.0,
  "file_size_bytes": 5242880,
  "cost_usd": 0.165,
  "contentbench_score": 0.9125,
  "current_state": "COMPLETED"
}
```

---

### 2.2 `inspect_production_state`
- **Description**: Inspects the current 17-state lifecycle status, transition history, and generated artifact file paths.
- **Service Gate**: `check_harness9_available()`
- **Required Capability**: `tool:inspect_state`

#### Parameter Schema
| Parameter | Type | Required | Default | Description |
|---|---|:---:|---|---|
| `session_id` | `string` | No | `None` | Session or project ID to inspect. |
| `include_history` | `boolean` | No | `true` | When true, includes the full `TransitionRecord` audit array. |

#### Return Payload Schema
```json
{
  "project_id": "proj_transistor_001",
  "current_state": "ASSETS_FROZEN",
  "history_count": 13,
  "history": [
    {
      "from_state": "CREATED",
      "to_state": "RESEARCH_PLANNED",
      "timestamp": "2026-08-31T12:00:00Z",
      "duration_ms": 142.5
    }
  ],
  "artifacts": {
    "dossier": "output/research_dossier.json",
    "script": "output/script.json",
    "audio": "assets/audio/narration.wav"
  }
}
```

---

### 2.3 `evaluate_content_quality`
- **Description**: Executes the ContentBench 4-layer evaluation framework on an existing project workspace.
- **Service Gate**: `check_harness9_available()`
- **Required Capability**: `tool:evaluate_quality`

#### Parameter Schema
| Parameter | Type | Required | Default | Description |
|---|---|:---:|---|---|
| `project_dir` | `string` | **Yes** | — | Path to the project workspace directory. |
| `layer` | `string` | No | `"all"` | Target layer: `"all"`, `"research"`, `"script"`, `"video"`, or `"cost"`. |

#### Return Payload Schema
```json
{
  "passed": true,
  "composite_score": 0.915,
  "layers": {
    "layer_1_research": { "score": 0.94, "fact_density": 4.2, "passed": true },
    "layer_2_script": { "score": 0.90, "readability": "Grade 8", "passed": true },
    "layer_3_video": { "score": 0.92, "voice_qa": "PASSED", "passed": true },
    "layer_4_cost": { "score": 0.88, "cost_per_sec": 0.0055, "passed": true }
  }
}
```

---

## 3. Internal Sub-Stage Worker Tools

When child workers are delegated specific sub-tasks, they execute with dedicated fine-grained tool authorities:

| Worker Role | Allowed Tool | Purpose | Capability Token Boundary |
|---|---|---|---|
| `researcher` | `extract_verified_claims` | Parses web search results and validates source provenance. | `tools: [extract_verified_claims]`, `net: [whitelist]` |
| `editorial` | `score_editorial_angles` | Runs 9-dimension scoring matrix on candidate angles. | `tools: [score_editorial_angles]`, `net: []` |
| `scriptwriter` | `plan_narrative_outline` | Generates 4-act structure and scene script beats. | `tools: [plan_narrative_outline]`, `net: []` |
| `audio_eng` | `synthesize_narration` | Calls VoiceDirector with SSML and pacing constraints. | `tools: [synthesize_narration]`, `net: [elevenlabs]` |
| `audio_eng` | `analyze_voice_qa` | Performs DSP waveform inspection (dead air, clipping). | `tools: [analyze_voice_qa]`, `net: []` |
| `asset_mgr` | `deduplicate_asset` | Calculates SHA-256 and `dHash` perceptual distance. | `tools: [deduplicate_asset]`, `write: [assets/]` |
| `renderer` | `render_hyperframes` | Compiles HTML/CSS/GSAP and launches Playwright. | `tools: [render_hyperframes]`, `write: [renders/]` |
