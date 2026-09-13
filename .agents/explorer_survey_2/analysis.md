# Technical Analysis: Requirements R1, R2, and R3

**Author:** explorer_survey_2  
**Date:** 2026-08-31  
**Target Scope:** Requirements R1 (State Machine, Production Contracts & Hermes Adapter), R2 (Editorial Intelligence & Multi-Angle Decision Engine), and R3 (HyperFrames Adapter, Extension Pack & Reusable Component Registry)  
**Codebase Root:** `g:\Finding-new-code\harness9`  

---

## 1. Executive Summary & Problem Scope

Harness 9 is an AI-native content production operating system that transforms topic briefs into broadcast-ready rendered MP4 videos. Currently, the codebase contains a functional, deterministic 5-stage procedural proof-of-concept (`src/research`, `src/assets`, `src/scriptwriting`, `src/hyperframes`, `src/orchestrator`), but lacks:
1. **R1**: A formal 17-state deterministic lifecycle state machine, typed Pydantic v2 production contracts, and an isolated `adapters/hermes/` compatibility bridge.
2. **R2**: An editorial intelligence engine (`src/editorial/`) that performs multi-angle candidate ideation, 9-dimension scorecard evaluation, winning angle selection, hook generation, and narrative planning.
3. **R3**: A formal `adapters/hyperframes/` interface and an extensible registry of 7+ parameterized HyperFrames visual component blocks.

This document presents a comprehensive audit of existing code, identifies exact gaps, defines production schemas and interface signatures, and outlines the precise implementation roadmap for R1, R2, and R3.

---

## 2. Requirement R1: State Machine, Production Contracts & Hermes Adapter

### 2.1 Current State Audit (R1)
- **State Management**: `src/orchestrator/pipeline.py` executes stages sequentially in a simple linear Python loop (`research` -> `assets` -> `script_voiceover` -> `hyperframes_render` -> `summary`). There is no discrete state representation, no transition table, no validation against invalid state jumps, and no state persistence.
- **Data Models**: Existing models in `src/models/` (`dossier.py`, `ledger.py`, `script.py`, `summary.py`) are implemented as standard Python `@dataclass` classes with manual `.to_dict()` and `.from_dict()` serialization. They lack Pydantic v2 strict type validation, field constraints, schema generation, and immutability options. Missing 13+ production contract models specified in the system design.
- **Hermes Integration**: There is no `adapters/hermes/` module or `docs/HERMES_COMPATIBILITY.md`. Harness 9 runs only as an isolated CLI command, without structured tool exposure, session isolation, or prompt caching guarantees for upstream Hermes Agent hosts.

---

### 2.2 The 17-State Lifecycle State Machine Specification

The production lifecycle progresses deterministically through 17 explicit states. Any attempt to skip required intermediary states or jump across the pipeline triggers an `InvalidStateTransitionError`.

```
 [1. CREATED] 
      │
      ▼
 [2. BRIEF_VALIDATED]
      │
      ▼
 [3. RESEARCH_PLANNED]
      │
      ▼
 [4. RESEARCH_COMPLETED]
      │
      ▼
 [5. ANGLES_GENERATED]
      │
      ▼
 [6. ANGLE_SELECTED]
      │
      ▼
 [7. OUTLINE_PLANNED]
      │
      ▼
 [8. SCRIPT_DRAFTED]
      │
      ▼
 [9. SCRIPT_EVALUATED]
      │
      ▼
 [10. VOICE_SYNTHESIZED]
      │
      ▼
 [11. VOICE_QA_PASSED]
      │
      ▼
 [12. ASSETS_DISCOVERED]
      │
      ▼
 [13. ASSETS_FROZEN]
      │
      ▼
 [14. COMPOSITION_COMPILED]
      │
      ▼
 [15. COMPOSITION_LINTED]
      │
      ▼
 [16. RENDER_COMPLETED]
      │
      ▼
 [17. COMPLETED]
```

#### State Definitions & Transition Matrix

| # | State Enum Name | Input Contract | Output Contract | Allowed Target Transitions |
|---|----------------|----------------|-----------------|----------------------------|
| 1 | `CREATED` | Topic / Initial Prompt | `ContentBrief` | `BRIEF_VALIDATED`, `FAILED`, `CANCELLED` |
| 2 | `BRIEF_VALIDATED` | `ContentBrief`, `CreatorProfile` | Validated `ContentBrief` | `RESEARCH_PLANNED`, `FAILED`, `CANCELLED` |
| 3 | `RESEARCH_PLANNED` | `ContentBrief` | `ResearchPlan` | `RESEARCH_COMPLETED`, `FAILED`, `CANCELLED` |
| 4 | `RESEARCH_COMPLETED` | `ResearchPlan` | `ResearchDossier` | `ANGLES_GENERATED`, `FAILED`, `CANCELLED` |
| 5 | `ANGLES_GENERATED` | `ResearchDossier`, `ContentBrief` | `List[EditorialAngle]` | `ANGLE_SELECTED`, `FAILED`, `CANCELLED` |
| 6 | `ANGLE_SELECTED` | `List[EditorialAngle]` | Selected `EditorialAngle` | `OUTLINE_PLANNED`, `FAILED`, `CANCELLED` |
| 7 | `OUTLINE_PLANNED` | `EditorialAngle`, `ResearchDossier` | `ContentOutline` | `SCRIPT_DRAFTED`, `FAILED`, `CANCELLED` |
| 8 | `SCRIPT_DRAFTED` | `ContentOutline`, `CreatorProfile` | `Script` | `SCRIPT_EVALUATED`, `FAILED`, `CANCELLED` |
| 9 | `SCRIPT_EVALUATED` | `Script` | `EvaluationReport` (Layer 2) | `VOICE_SYNTHESIZED`, `SCRIPT_DRAFTED` (retry), `FAILED` |
| 10 | `VOICE_SYNTHESIZED` | `Script` | `AudioMetadata` (`narration.wav`) | `VOICE_QA_PASSED`, `FAILED`, `CANCELLED` |
| 11 | `VOICE_QA_PASSED` | `AudioMetadata`, `Script` | `VoiceQAReport` | `ASSETS_DISCOVERED`, `VOICE_SYNTHESIZED` (retry), `FAILED` |
| 12 | `ASSETS_DISCOVERED` | `Script`, `ResearchDossier` | `List[AssetRequirement]` | `ASSETS_FROZEN`, `FAILED`, `CANCELLED` |
| 13 | `ASSETS_FROZEN` | `List[AssetRequirement]` | `AssetProvenanceLedger` | `COMPOSITION_COMPILED`, `FAILED`, `CANCELLED` |
| 14 | `COMPOSITION_COMPILED`| `Script`, `AssetLedger`, `Audio` | HyperFrames files (`index.html`, etc.) | `COMPOSITION_LINTED`, `FAILED`, `CANCELLED` |
| 15 | `COMPOSITION_LINTED` | HyperFrames Project | `ValidationReport` | `RENDER_COMPLETED`, `COMPOSITION_COMPILED` (retry), `FAILED` |
| 16 | `RENDER_COMPLETED` | HyperFrames Project, FFmpeg | `RenderArtifact` (`renders/final.mp4`) | `COMPLETED`, `FAILED`, `CANCELLED` |
| 17 | `COMPLETED` | `RenderArtifact`, Run Logs | `PublishPackage`, `PipelineSummary` | Terminal State |

*Non-linear / Exception States*:
- `FAILED`: Terminal error state, records `error_message`, `failed_at_state`, `traceback`.
- `PAUSED_FOR_HUMAN`: Allows human-in-the-loop review at `ANGLE_SELECTED` or `SCRIPT_EVALUATED`.
- `CANCELLED`: User/orchestrator abort.

#### State Machine Implementation Class

```python
# src/orchestrator/state_machine.py
from enum import Enum
from typing import Dict, Set, Optional, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ProductionState(str, Enum):
    CREATED = "CREATED"
    BRIEF_VALIDATED = "BRIEF_VALIDATED"
    RESEARCH_PLANNED = "RESEARCH_PLANNED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    ANGLES_GENERATED = "ANGLES_GENERATED"
    ANGLE_SELECTED = "ANGLE_SELECTED"
    OUTLINE_PLANNED = "OUTLINE_PLANNED"
    SCRIPT_DRAFTED = "SCRIPT_DRAFTED"
    SCRIPT_EVALUATED = "SCRIPT_EVALUATED"
    VOICE_SYNTHESIZED = "VOICE_SYNTHESIZED"
    VOICE_QA_PASSED = "VOICE_QA_PASSED"
    ASSETS_DISCOVERED = "ASSETS_DISCOVERED"
    ASSETS_FROZEN = "ASSETS_FROZEN"
    COMPOSITION_COMPILED = "COMPOSITION_COMPILED"
    COMPOSITION_LINTED = "COMPOSITION_LINTED"
    RENDER_COMPLETED = "RENDER_COMPLETED"
    COMPLETED = "COMPLETED"
    PAUSED_FOR_HUMAN = "PAUSED_FOR_HUMAN"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class StateTransitionRecord(BaseModel):
    from_state: ProductionState
    to_state: ProductionState
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload_summary: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0

class ProductionStateMachine:
    VALID_TRANSITIONS: Dict[ProductionState, Set[ProductionState]] = {
        ProductionState.CREATED: {ProductionState.BRIEF_VALIDATED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.BRIEF_VALIDATED: {ProductionState.RESEARCH_PLANNED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.RESEARCH_PLANNED: {ProductionState.RESEARCH_COMPLETED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.RESEARCH_COMPLETED: {ProductionState.ANGLES_GENERATED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.ANGLES_GENERATED: {ProductionState.ANGLE_SELECTED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.ANGLE_SELECTED: {ProductionState.OUTLINE_PLANNED, ProductionState.PAUSED_FOR_HUMAN, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.OUTLINE_PLANNED: {ProductionState.SCRIPT_DRAFTED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.SCRIPT_DRAFTED: {ProductionState.SCRIPT_EVALUATED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.SCRIPT_EVALUATED: {ProductionState.VOICE_SYNTHESIZED, ProductionState.SCRIPT_DRAFTED, ProductionState.PAUSED_FOR_HUMAN, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.VOICE_SYNTHESIZED: {ProductionState.VOICE_QA_PASSED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.VOICE_QA_PASSED: {ProductionState.ASSETS_DISCOVERED, ProductionState.VOICE_SYNTHESIZED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.ASSETS_DISCOVERED: {ProductionState.ASSETS_FROZEN, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.ASSETS_FROZEN: {ProductionState.COMPOSITION_COMPILED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.COMPOSITION_COMPILED: {ProductionState.COMPOSITION_LINTED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.COMPOSITION_LINTED: {ProductionState.RENDER_COMPLETED, ProductionState.COMPOSITION_COMPILED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.RENDER_COMPLETED: {ProductionState.COMPLETED, ProductionState.FAILED, ProductionState.CANCELLED},
        ProductionState.PAUSED_FOR_HUMAN: {ProductionState.OUTLINE_PLANNED, ProductionState.VOICE_SYNTHESIZED, ProductionState.CANCELLED, ProductionState.FAILED},
        ProductionState.COMPLETED: set(),
        ProductionState.FAILED: {ProductionState.CREATED},  # Allow full reset
        ProductionState.CANCELLED: set(),
    }

    def __init__(self, run_id: str, initial_state: ProductionState = ProductionState.CREATED):
        self.run_id = run_id
        self.current_state = initial_state
        self.history: List[StateTransitionRecord] = []

    def can_transition_to(self, target_state: ProductionState) -> bool:
        return target_state in self.VALID_TRANSITIONS.get(self.current_state, set())

    def transition_to(self, target_state: ProductionState, payload: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0) -> ProductionState:
        if not self.can_transition_to(target_state):
            raise ValueError(f"Invalid state transition: Cannot transition from {self.current_state.value} to {target_state.value}")
        
        record = StateTransitionRecord(
            from_state=self.current_state,
            to_state=target_state,
            payload_summary=payload or {},
            duration_ms=duration_ms,
        )
        self.history.append(record)
        self.current_state = target_state
        return self.current_state
```

---

### 2.3 Comprehensive Pydantic Production Schemas (17 Contracts)

All data exchange across the production pipeline must be validated using Pydantic v2 `BaseModel` schemas with strict type hints, defaults, and validators:

```python
# src/models/contracts.py
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator, ConfigDict

# ---------------------------------------------------------------------------
# 1. Creator Profile & DNA Contract
# ---------------------------------------------------------------------------
class CreatorProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    creator_id: str = Field(..., description="Unique slug for creator")
    display_name: str = Field(..., description="Creator public brand name")
    tone_of_voice: List[str] = Field(default_factory=lambda: ["authoritative", "engaging", "accessible"])
    target_audiences: List[str] = Field(default_factory=lambda: ["tech enthusiasts", "general learners"])
    brand_colors: Dict[str, str] = Field(default_factory=lambda: {
        "primary": "#00d2ff", "background": "#0a0e17", "text": "#ffffff", "accent": "#ff5252"
    })
    default_format: str = Field(default="16:9", pattern="^(16:9|9:16|1:1)$")
    negative_rules: List[str] = Field(default_factory=lambda: [
        "Never use buzzwords like 'game-changer' or 'revolutionize'",
        "Never use unverified hype statistics"
    ])
    voice_preference: str = Field(default="default")

# ---------------------------------------------------------------------------
# 2. Content Brief Contract
# ---------------------------------------------------------------------------
class ContentBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(..., description="Unique job execution identifier")
    topic: str = Field(..., min_length=3, max_length=200)
    target_duration_seconds: int = Field(default=30, ge=5, le=600)
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16|1:1)$")
    goal: str = Field(default="Educational Overview")
    audience: str = Field(default="General Tech Enthusiasts")
    offline_mode: bool = Field(default=True)
    custom_instructions: Optional[str] = None

# ---------------------------------------------------------------------------
# 3. Research Plan & Sources
# ---------------------------------------------------------------------------
class ResearchPlan(BaseModel):
    topic: str
    target_claim_count: int = Field(default=5, ge=3)
    search_queries: List[Tuple[str, str]] = Field(default_factory=list, description="(category, query_string)")
    intent_categories: List[str] = Field(default_factory=lambda: [
        "origin_history", "technical_mechanism", "quantitative_metric", "modern_impact"
    ])
    timeout_seconds: float = Field(default=15.0)

class SourceRecord(BaseModel):
    title: str = Field(..., min_length=1)
    url: str = Field(...)
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)

class ClaimRecord(BaseModel):
    claim_id: str = Field(..., pattern=r"^claim_\d+$")
    claim_text: str = Field(..., min_length=10)
    category: str = Field(default="general")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    primary_source: SourceRecord
    corroborating_sources: List[SourceRecord] = Field(default_factory=list)
    visual_cue_suggestion: str = ""
    verification_notes: str = ""

# ---------------------------------------------------------------------------
# 4. Research Dossier
# ---------------------------------------------------------------------------
class TalkingPointRecord(BaseModel):
    beat_index: int = Field(..., ge=1)
    title: str
    narrative_hook: str
    supported_claim_ids: List[str] = Field(default_factory=list)
    estimated_duration_sec: float = Field(default=5.0, ge=0.5)

class StatisticRecord(BaseModel):
    metric: str
    value: str
    context: str
    source_claim_id: str

class ResearchDossier(BaseModel):
    schema_version: str = "2.0.0"
    topic: str
    run_id: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    headline: str
    executive_summary: str
    key_takeaways: List[str] = Field(default_factory=list)
    claims: List[ClaimRecord] = Field(default_factory=list)
    talking_points: List[TalkingPointRecord] = Field(default_factory=list)
    statistics: List[StatisticRecord] = Field(default_factory=list)
    suggested_visual_queries: List[str] = Field(default_factory=list)

# ---------------------------------------------------------------------------
# 5. Editorial Angle & Scorecard (R2)
# ---------------------------------------------------------------------------
class AngleScorecard(BaseModel):
    audience_relevance: float = Field(..., ge=0.0, le=1.0)
    novelty: float = Field(..., ge=0.0, le=1.0)
    hook_potential: float = Field(..., ge=0.0, le=1.0)
    narrative_potential: float = Field(..., ge=0.0, le=1.0)
    creator_fit: float = Field(..., ge=0.0, le=1.0)
    evidence_availability: float = Field(..., ge=0.0, le=1.0)
    visual_potential: float = Field(..., ge=0.0, le=1.0)
    platform_fit: float = Field(..., ge=0.0, le=1.0)
    saturation_risk: float = Field(..., ge=0.0, le=1.0, description="Lower is better, or inverted in composite")
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)

class EditorialAngle(BaseModel):
    angle_id: str = Field(..., pattern=r"^angle_\d+$")
    title: str
    premise: str
    core_thesis: str
    target_audience: str
    narrative_style: str = "Cinematic Discovery"
    key_hooks: List[str] = Field(default_factory=list)
    scorecard: AngleScorecard
    selected: bool = False
    selection_rationale: Optional[str] = None

# ---------------------------------------------------------------------------
# 6. Content Outline & Narrative Plan (R2)
# ---------------------------------------------------------------------------
class OutlineAct(BaseModel):
    act_index: int = Field(..., ge=1)
    act_name: str  # e.g., "The Hook", "The Bottleneck", "The Discovery", "The Horizon"
    target_start_pct: float  # e.g., 0.0
    target_end_pct: float    # e.g., 0.2
    narrative_job: str
    talking_point_indices: List[int] = Field(default_factory=list)
    visual_theme: str = "hero_graphic"

class ContentOutline(BaseModel):
    project_id: str
    topic: str
    angle_id: str
    angle_title: str
    primary_hook: str
    acts: List[OutlineAct] = Field(default_factory=list)
    total_estimated_duration: float = 30.0

# ---------------------------------------------------------------------------
# 7. Script, Beats & Storyboard
# ---------------------------------------------------------------------------
class ScriptBeat(BaseModel):
    beat_id: str = Field(..., pattern=r"^beat_\d+$")
    start_time: float = Field(default=0.0, ge=0.0)
    end_time: float = Field(default=0.0, ge=0.0)
    duration: float = Field(default=0.0, ge=0.0)
    text: str = Field(..., min_length=1)
    visual_cue: str = ""
    tone_modifier: Optional[str] = None
    emphasis_words: List[str] = Field(default_factory=list)

class ScriptScene(BaseModel):
    scene_id: str = Field(..., pattern=r"^scene_\d+$")
    title: str
    start_time: float = Field(..., ge=0.0)
    duration: float = Field(..., gt=0.0)
    narration_text: str
    visual_asset_path: str = ""
    hero_frame_description: str = ""
    component_type: str = Field(default="reference_collage_hook", description="HyperFrames component block ID")
    component_props: Dict[str, Any] = Field(default_factory=dict)
    entrance_animation: str = "fade"
    transition_out: str = "fade"
    beats: List[ScriptBeat] = Field(default_factory=list)

class Script(BaseModel):
    topic: str
    title: str
    angle_id: str
    total_duration: float
    full_transcript: str
    word_count: int
    scenes: List[ScriptScene] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ---------------------------------------------------------------------------
# 8. Asset Requirements & Asset Records
# ---------------------------------------------------------------------------
class AssetRequirement(BaseModel):
    requirement_id: str
    scene_id: str
    visual_query: str
    media_type: str = "image/svg+xml"
    aspect_ratio: str = "16:9"
    style_notes: str = ""
    associated_claim_id: Optional[str] = None

class Dimensions(BaseModel):
    width: int = 1920
    height: int = 1080
    aspect_ratio: str = "16:9"

class LicenseInfo(BaseModel):
    license_type: str = "CC0-1.0 (Public Domain)"
    license_url: Optional[str] = None
    attribution_text: str = ""
    attribution_required: bool = False
    commercial_use_allowed: bool = True
    modification_allowed: bool = True

class AssetRecord(BaseModel):
    asset_id: str = Field(..., pattern=r"^asset_\d+$")
    local_path: str
    absolute_path: Optional[str] = None
    file_size_bytes: int = 0
    file_sha256: str = Field(..., min_length=64, max_length=64)
    perceptual_hash: Optional[str] = None
    media_type: str = "image/svg+xml"
    dimensions: Dimensions = Field(default_factory=Dimensions)
    source_provider: str = "procedural_generator"
    source_url: str = ""
    page_url: Optional[str] = None
    creator_name: str = "Harness 9 Procedural Generator"
    license: LicenseInfo = Field(default_factory=LicenseInfo)
    verification_status: str = "VERIFIED"
    scene_target: str = "scene_1"
    claim_id_refs: List[str] = Field(default_factory=list)

# ---------------------------------------------------------------------------
# 9. Quality Evaluation & QA Reports
# ---------------------------------------------------------------------------
class EvaluationLayer(str, Enum):
    RESEARCH = "layer_1_research"
    SCRIPT = "layer_2_script"
    VIDEO = "layer_3_video"
    COST = "layer_4_cost"

class EvaluationReport(BaseModel):
    run_id: str
    layer: EvaluationLayer
    scores: Dict[str, float] = Field(default_factory=dict)
    composite_score: float = Field(..., ge=0.0, le=1.0)
    passed: bool = True
    feedback: List[str] = Field(default_factory=list)
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ---------------------------------------------------------------------------
# 10. Render Artifact & Publish Package
# ---------------------------------------------------------------------------
class RenderArtifact(BaseModel):
    video_path: str
    duration_seconds: float
    file_size_bytes: int
    width: int
    height: int
    fps: int = 30
    video_codec: str = "h264"
    audio_codec: str = "aac"
    rendered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validation_status: str = "VERIFIED"

class PublishPackage(BaseModel):
    project_id: str
    title: str
    description: str
    tags: List[str] = Field(default_factory=list)
    video_path: str
    thumbnail_path: Optional[str] = None
    captions_vtt_path: Optional[str] = None
    total_cost_usd: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ---------------------------------------------------------------------------
# 11. Analytics & Creator Memory
# ---------------------------------------------------------------------------
class AnalyticsSnapshot(BaseModel):
    project_id: str
    views: int = 0
    average_watch_percentage: float = 0.0
    ctr: float = 0.0
    engagement_rate: float = 0.0
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LearningCandidate(BaseModel):
    lesson_id: str
    creator_id: str
    rule_type: str = "negative_constraint"  # e.g., "pacing_adjustment", "hook_preference"
    observation: str
    recommended_action: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

---

### 2.4 Upstream Hermes Agent Adapter (`adapters/hermes/`)

In compliance with the Hermes Development Guide (`AGENTS.md`), the Hermes Adapter must satisfy four inviolable design rules:
1. **Sacred Prompt Caching**: Zero runtime mutation of system prompt bytes mid-conversation.
2. **Narrow Core Waist**: Harness 9 tools must live as a service-gated toolset (`check_fn` / `enabled_toolsets`), not as hardcoded core tools.
3. **Session-Scoped State**: Availability of video generation is resolved from session context, and file outputs are written to profile-safe paths (`get_hermes_home()`).
4. **Hermetic Isolation**: Internal Harness 9 dependencies (GSAP, FFmpeg, Playwright) remain isolated behind the adapter interface.

```
adapters/hermes/
├── __init__.py           # Adapter package exports
├── bridge.py             # Direct Python API bridge for Hermes run_agent / AIAgent
├── tools.py              # Hermes-compliant model tool definitions and JSON schemas
├── session.py            # Profile-aware workspace and tempfile sandbox manager
└── toolset.py            # Toolset distribution registration (hermes_harness9_toolset)
```

#### Tool Schema Definition (`adapters/hermes/tools.py`)

```python
# adapters/hermes/tools.py
from typing import Any, Dict
from src.orchestrator.pipeline import Pipeline

def check_harness9_available() -> bool:
    """Check whether Harness 9 dependencies (Python 3.10+, FFmpeg) are present."""
    from src.utils.ffmpeg import is_ffmpeg_available
    return is_ffmpeg_available()

HARNESS9_TOOL_SCHEMA = {
    "name": "generate_video_from_brief",
    "description": "Generate a broadcast-ready MP4 video from a topic brief using the Harness 9 production pipeline.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic or subject matter of the video.",
            },
            "format": {
                "type": "string",
                "enum": ["16:9", "9:16"],
                "default": "16:9",
                "description": "Target aspect ratio (16:9 for landscape/YouTube, 9:16 for Shorts/TikTok).",
            },
            "duration": {
                "type": "integer",
                "default": 30,
                "description": "Target duration in seconds.",
            },
            "offline": {
                "type": "boolean",
                "default": True,
                "description": "Whether to run in 100% deterministic offline mode.",
            }
        },
        "required": ["topic"]
    }
}

def handle_generate_video(args: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    topic = args.get("topic", "")
    fmt = args.get("format", "16:9")
    dur = int(args.get("duration", 30))
    offline = bool(args.get("offline", True))
    
    out_dir = f"output/hermes_session_{session_id}"
    p = Pipeline(topic=topic, output_dir=out_dir, offline=offline, format=fmt, duration=dur)
    success = p.run()
    
    return {
        "success": success,
        "topic": topic,
        "video_path": f"{out_dir}/renders/final.mp4" if success else None,
        "output_directory": out_dir,
    }
```

---

## 3. Requirement R2: Editorial Intelligence & Multi-Angle Decision Engine

### 3.1 Current State Audit (R2)
- Currently, `src/scriptwriting/generator.py` ingests a `ResearchDossier` and converts its talking points directly into a single script with default scenes.
- There is **no angle ideation stage**: zero candidate angles generated, zero scoring, and zero narrative planning before scriptwriting.
- There is no package or module named `src/editorial/` or `packages/editorial/`.

---

### 3.2 Subsystem Architecture (`src/editorial/`)

The Editorial Intelligence engine introduces an intermediate creative decision layer between Stage 1 (Research) and Stage 3 (Scriptwriting):

```
[Stage 1: Research Dossier]
            │
            ▼
[Editorial: Angle Generator] ────► Generates 3-5 distinct orthogonal angles
            │
            ▼
[Editorial: 9-Dimension Scorer] ─► Evaluates all candidates across 9 dimensions
            │
            ▼
[Editorial: Top Angle Selector] ─► Selects winning angle based on weighted criteria
            │
            ▼
[Editorial: Hook Generator] ────► Synthesizes 3 hook variations for winner
            │
            ▼
[Editorial: Narrative Planner] ──► Produces 4-Act ContentOutline with beat-to-claim mapping
            │
            ▼
[Stage 3: Scriptwriting Pipeline]
```

#### Package Layout
```
src/editorial/
├── __init__.py          # Public exports (EditorialEngine, AngleGenerator, AngleScorer, etc.)
├── angles.py            # Multi-angle ideation & archetype definitions
├── scoring.py           # 9-dimension scorecard evaluator & composite math
├── hooks.py             # Hook generation & retention optimization
├── planner.py           # 4-Act ContentOutline synthesis
└── heuristics.py        # Deterministic offline scoring rules
```

---

### 3.3 The 9-Dimension Scorecard Specification

Each candidate angle is evaluated against 9 normalized dimensions (0.0 to 1.0):

1. **`audience_relevance`** ($w_1 = 0.15$): Alignment with broad human curiosity, daily utility, or universal wonder.
2. **`novelty`** ($w_2 = 0.15$): Surprise factor; how counterintuitive or fresh the angle is vs generic summaries.
3. **`hook_potential`** ($w_3 = 0.15$): Capability to stop the viewer scroll in the first 3.0 seconds.
4. **`narrative_potential`** ($w_4 = 0.10$): Clear presence of conflict, escalation, stakes, and satisfying resolution.
5. **`creator_fit`** ($w_5 = 0.10$): Alignment with creator brand DNA, subject expertise, and tone.
6. **`evidence_availability`** ($w_6 = 0.10$): Density of verifiable facts and citations in the `ResearchDossier`.
7. **`visual_potential`** ($w_7 = 0.10$): Visual dynamic range (opportunities for schematics, comparisons, collages).
8. **`platform_fit`** ($w_8 = 0.10$): Suitability for target aspect ratio and pacing (e.g. punchy for 9:16 vs deep for 16:9).
9. **`saturation_risk`** ($w_9 = 0.05$): Penalty metric for overused tropes (scored where 0.0 is completely fresh and 1.0 is heavily saturated; inverted as $1 - \text{saturation\_risk}$ in composite math).

$$\text{Composite Score} = \sum_{i=1}^{8} (w_i \cdot d_i) + w_9 \cdot (1 - \text{saturation\_risk})$$

---

### 3.4 Multi-Angle Ideation Archetypes (`src/editorial/angles.py`)

The `AngleGenerator` produces 3-5 distinct angles based on established story archetypes:

1. **The Counterintuitive Revelation** ("The Accidental Revolution"): Focuses on how mistakes, accidents, or paradoxes created the technology.
2. **The High-Stakes Race** ("The Secret Race Against Collapse"): Focuses on geopolitical, commercial, or existential deadlines.
3. **The Microscopic Architecture** ("The Nanometer Miracle"): Focuses on physical mechanisms, physics bottlenecks, and engineering marvels.
4. **The Modern Domino Effect** ("Why This Governs Your Future"): Focuses on modern global supply chain vulnerabilities and economic impact.
5. **The Unsung Heroes** ("The Forgotten Pioneers"): Focuses on human drama, rivalries, and unrecognized contributors.

#### Angle Generator Implementation Signature

```python
# src/editorial/angles.py
from typing import List, Optional
from src.models.contracts import ContentBrief, CreatorProfile, EditorialAngle, ResearchDossier
from src.editorial.scoring import EditorialScorer

class AngleGenerator:
    """Generates orthogonal candidate editorial angles from research dossiers."""

    def __init__(self, scorer: Optional[EditorialScorer] = None):
        self.scorer = scorer or EditorialScorer()

    def generate_candidate_angles(
        self,
        dossier: ResearchDossier,
        brief: ContentBrief,
        creator: Optional[CreatorProfile] = None,
    ) -> List[EditorialAngle]:
        """Generate 3-5 candidate angles and score them against the 9-dimension scorecard."""
        # Ideate candidates based on topic themes and claims
        candidates: List[EditorialAngle] = []
        # ... candidate generation logic across archetypes ...
        # Score each candidate
        for angle in candidates:
            angle.scorecard = self.scorer.score_angle(angle, dossier, brief, creator)
        
        # Select top candidate
        candidates.sort(key=lambda a: a.scorecard.composite_score, reverse=True)
        if candidates:
            candidates[0].selected = True
            candidates[0].selection_rationale = f"Highest composite score ({candidates[0].scorecard.composite_score:.2f}) with exceptional hook potential and evidence density."
        
        return candidates
```

---

### 3.5 Narrative Planning (`src/editorial/planner.py`)

The `NarrativePlanner` converts the winning angle and research dossier into a structured 4-Act `ContentOutline`:
- **Act 1: The Hook & Paradox (0-15% duration)**: Grabs attention, establishes the core question or stakes.
- **Act 2: The Physical/Historical Barrier (15-45% duration)**: Explains the bottleneck that seemed impossible to solve.
- **Act 3: The Breakthrough Mechanism (45-75% duration)**: Deep dive into how the technology actually works, referencing verified claim IDs.
- **Act 4: The Ripple Effect & Takeaway (75-100% duration)**: Concludes with broad implications, call-to-thought, and key summary.

---

## 4. Requirement R3: HyperFrames Adapter, Extension Pack & Reusable Component Registry

### 4.1 Current State Audit (R3)
- `src/hyperframes/generator.py` generates a single monolithic scene DOM structure: `<div class="scene">` containing `<div class="scene-background">`, `<div class="scene-content">` (badge, title, narration), and an absolute caption overlay.
- There are no modular, reusable components; every scene renders identical HTML cards and identical GSAP `tl.from()` animations.
- There is no formal adapter package in `adapters/hyperframes/`.

---

### 4.2 HyperFrames Integration Architecture

```
adapters/hyperframes/
├── __init__.py           # Adapter exports (HyperFramesAdapter, ComponentRegistry)
├── adapter.py            # Primary interface contract for pipeline stages
├── compiler.py           # Composition compiler assembling components into index.html / main.js
└── registry.py           # Component registry manager

src/hyperframes/components/
├── __init__.py
├── base.py               # HyperFramesComponent abstract base class
├── reference_collage.py  # Block 1: Reference collage hook
├── split_screen.py       # Block 2: Split-screen intro
├── quote_highlight.py    # Block 3: Quote highlight card
├── timeline_reveal.py    # Block 4: Timeline / milestone reveal
├── statistic_reveal.py   # Block 5: Statistic & numerical counter reveal
├── comparison_panel.py   # Block 6: Side-by-side comparison panel
└── creator_bottom.py     # Block 7: Creator bottom collage overlay
```

---

### 4.3 The 7+ Parameterized Component Blocks Specification

Every component block implements the `HyperFramesComponent` base class and must adhere strictly to HyperFrames runtime invariants:
1. **Synchronous paused timeline**: All animations append to the global `window.__timelines["root"]` timeline.
2. **Finite repeat math**: Loops must calculate finite repeats `Math.ceil(duration / cycle) - 1` (never `repeat: -1`).
3. **Guaranteed clean exit**: Elements must clean up or hide (`tl.set(..., { autoAlpha: 0 })`) before the next scene to prevent DOM occlusion.
4. **Local asset integrity**: Zero external HTTP/HTTPS media URLs.

#### 1. `reference_collage_hook` (Block 1)
- **Use Case**: Video opening hook; creates high visual density by displaying 3-4 images in a staggered asymmetric masonry grid with glowing borders.
- **Parameters**: `headline: str`, `badge: str`, `image_paths: List[str]`, `glow_color: str`, `stagger_delay: float`.
- **GSAP Animation**: Staggered zoom-in `gsap.from(".collage-item", { scale: 0.8, opacity: 0, stagger: 0.15 })`.

#### 2. `split_screen_intro` (Block 2)
- **Use Case**: Contrasts two eras, technologies, or rival concepts (e.g. Vacuum Tube vs Transistor; CPU vs GPU).
- **Parameters**: `left_title: str`, `left_image: str`, `right_title: str`, `right_image: str`, `divider_color: str`.
- **GSAP Animation**: Dual wipe from opposing screen edges with central divider drop-in.

#### 3. `quote_highlight` (Block 3)
- **Use Case**: Highlights an authoritative historical quote, key claim citation, or dramatic statement.
- **Parameters**: `quote_text: str`, `author_name: str`, `author_title: str`, `author_image: Optional[str]`, `accent_color: str`.
- **GSAP Animation**: Kinetic word-by-word reveal with glowing ambient backdrop pulse.

#### 4. `timeline_reveal` (Block 4)
- **Use Case**: Displays chronological progression across 3-4 milestones with year badges and connecting line draw.
- **Parameters**: `milestones: List[Dict[str, str]]` (`year`, `label`, `description`), `line_color: str`.
- **GSAP Animation**: Progressive draw of horizontal/vertical line with node pop-in `scale: [0 -> 1.2 -> 1.0]`.

#### 5. `statistic_reveal` (Block 5)
- **Use Case**: Dramatizes a massive numerical breakthrough (e.g., "100 Billion Transistors", "4,096 CUDA Cores", "2.048 MHz").
- **Parameters**: `target_number: float/int`, `prefix: str`, `suffix: str`, `metric_label: str`, `context_subtext: str`.
- **GSAP Animation**: Smooth counter animation via GSAP ticker / `roundProps`, expanding glow ring, and subtext fade-up.

#### 6. `comparison_panel` (Block 6)
- **Use Case**: Side-by-side feature comparison table or "Before vs After" metric breakdown.
- **Parameters**: `entity_a_name: str`, `entity_b_name: str`, `comparison_rows: List[Tuple[str, str, str]]`.
- **GSAP Animation**: Staggered row reveal with color-coded winner highlights.

#### 7. `creator_bottom_collage` (Block 7)
- **Use Case**: Picture-in-picture lower third displaying creator avatar, handle, brand logo, and supporting thumbnail.
- **Parameters**: `creator_name: str`, `creator_handle: str`, `avatar_path: str`, `brand_badge: str`.
- **GSAP Animation**: Slide-up from bottom screen margin with elastic overshoot and badge shimmer.

---

### 4.4 Component Base Class Contract (`src/hyperframes/components/base.py`)

```python
# src/hyperframes/components/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class ComponentSchema(BaseModel):
    block_id: str
    display_name: str
    description: str
    supported_aspect_ratios: List[str] = Field(default_factory=lambda: ["16:9", "9:16"])
    required_props: List[str] = Field(default_factory=list)

class HyperFramesComponent(ABC):
    """Abstract base class for all modular HyperFrames visual components."""

    schema: ComponentSchema

    @abstractmethod
    def render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str = "16:9") -> str:
        """Render semantic HTML DOM elements for the component."""
        pass

    @abstractmethod
    def render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str = "16:9") -> str:
        """Render scoped CSS styles for the component."""
        pass

    @abstractmethod
    def render_gsap(
        self,
        scene_id: str,
        props: Dict[str, Any],
        start_time: float,
        duration: float,
        format_aspect: str = "16:9",
    ) -> str:
        """Render deterministic GSAP animation instructions."""
        pass
```

---

## 5. Concrete Implementation Steps & File Migration Matrix

| Requirement | Action | Target Path | Description |
|---|---|---|---|
| **R1** | Create | `src/orchestrator/state_machine.py` | 17-state lifecycle machine, transition graph, and jump validator |
| **R1** | Create | `src/models/contracts.py` | 17 unified Pydantic v2 production schemas |
| **R1** | Update | `src/models/__init__.py` | Export new contracts while preserving backward compatibility |
| **R1** | Create | `adapters/hermes/__init__.py` | Hermes adapter package root |
| **R1** | Create | `adapters/hermes/bridge.py` | Hermes AIAgent / CLI programmatic execution bridge |
| **R1** | Create | `adapters/hermes/tools.py` | Service-gated tool definitions and schemas for Hermes |
| **R1** | Create | `adapters/hermes/session.py` | Profile-aware workspace and sandbox isolation |
| **R1** | Create | `docs/HERMES_COMPATIBILITY.md` | Hermes compatibility, prompt caching, and integration spec |
| **R2** | Create | `src/editorial/__init__.py` | Editorial intelligence package root |
| **R2** | Create | `src/editorial/angles.py` | Multi-angle ideation generator across 5 archetypes |
| **R2** | Create | `src/editorial/scoring.py` | 9-dimension scorecard evaluator & composite scoring |
| **R2** | Create | `src/editorial/hooks.py` | Hook generator & retention optimizer |
| **R2** | Create | `src/editorial/planner.py` | 4-Act ContentOutline narrative planning engine |
| **R3** | Create | `adapters/hyperframes/__init__.py` | HyperFrames adapter package root |
| **R3** | Create | `adapters/hyperframes/adapter.py` | High-level compiler and renderer adapter |
| **R3** | Create | `src/hyperframes/components/__init__.py` | Component registry package root |
| **R3** | Create | `src/hyperframes/components/base.py` | `HyperFramesComponent` abstract base class & schema |
| **R3** | Create | `src/hyperframes/components/reference_collage.py` | Parameterized Block 1: Reference collage hook |
| **R3** | Create | `src/hyperframes/components/split_screen.py` | Parameterized Block 2: Split-screen intro |
| **R3** | Create | `src/hyperframes/components/quote_highlight.py` | Parameterized Block 3: Quote highlight card |
| **R3** | Create | `src/hyperframes/components/timeline_reveal.py` | Parameterized Block 4: Timeline reveal |
| **R3** | Create | `src/hyperframes/components/statistic_reveal.py` | Parameterized Block 5: Statistic reveal & counter |
| **R3** | Create | `src/hyperframes/components/comparison_panel.py` | Parameterized Block 6: Side-by-side comparison |
| **R3** | Create | `src/hyperframes/components/creator_bottom.py` | Parameterized Block 7: Creator bottom collage |
| **Integration** | Update | `src/orchestrator/pipeline.py` | Wire StateMachine, EditorialEngine, and ComponentRegistry into pipeline |
| **Testing** | Create | `tests/test_state_machine.py` | Unit tests for all 17 states and transition boundary validation |
| **Testing** | Create | `tests/test_editorial.py` | Unit tests for angle generation, 9-dimension scoring, and narrative planning |
| **Testing** | Create | `tests/test_hyperframes_components.py` | Unit tests for the 7 component blocks, static linting, and GSAP compliance |

---

## 6. Verification and Acceptance Testing

To independently verify the implementation of R1, R2, and R3:
1. **State Machine Verification**:
   - Assert all 17 states transition sequentially.
   - Assert invalid state jumps (e.g., `CREATED` -> `RENDER_COMPLETED`) raise `ValueError` / `InvalidStateTransitionError`.
   - Assert state machine history records timestamps and durations for every transition.
2. **Production Contracts Verification**:
   - Assert all 17 Pydantic schemas validate clean payloads without data loss.
   - Assert `model_dump()` and `model_dump_json()` produce valid JSON/YAML.
   - Assert existing tests (`tests/test_research.py`, `tests/test_assets.py`, `tests/test_scriptwriting.py`) pass without regressions.
3. **Editorial Intelligence Verification**:
   - Assert `generate_candidate_angles()` returns $\ge 3$ candidate angles with distinct premises.
   - Assert `score_angle()` computes all 9 dimensions in $[0.0, 1.0]$ and produces a deterministic composite score.
   - Assert top angle selection correctly sets `selected = True` on the highest-scoring candidate.
   - Assert `ContentOutline` generates 4 distinct acts mapped to research claims.
4. **HyperFrames Components Verification**:
   - Assert all 7 component blocks render valid HTML, CSS, and GSAP timeline code.
   - Assert `validate_composition()` passes with zero errors across all 7 blocks in both 16:9 and 9:16 aspect ratios.
   - Assert no external HTTP/HTTPS URLs or infinite loop repeats (`repeat: -1`) exist in generated code.
5. **Full Pipeline Acceptance**:
   - Run `python verify_pipeline.py --test-mode` and verify all 6 checkpoints pass.
   - Run `pytest tests/ -v` and verify 100% test pass rate.
