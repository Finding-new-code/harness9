"""Harness 9 Production Contracts & Pydantic v2 Schemas (Milestone M1).

Defines the 17 core production contracts exchanged across all subsystem boundaries:
1. CreatorProfile
2. ContentBrief
3. ResearchPlan
4. ResearchDossier
5. SourceRecord
6. ClaimRecord
7. EditorialAngle
8. ContentOutline
9. Script
10. ScriptBeat
11. AssetRequirement
12. AssetRecord
13. EvaluationReport
14. RenderArtifact
15. PublishPackage
16. AnalyticsSnapshot
17. LearningCandidate
"""

from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)



# ===========================================================================
# Base Contract Helper
# ===========================================================================
class H9BaseModel(BaseModel):
    """Base Pydantic model providing dictionary and JSON/YAML serialization."""
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        populate_by_name=True,
    )

    def to_dict(self, mode: str = "json") -> Dict[str, Any]:
        """Convert model to standard Python dictionary."""
        return self.model_dump(mode=mode)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Instantiate model from dictionary."""
        return cls.model_validate(data)

    def to_json(self, indent: int = 2) -> str:
        """Serialize model to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> Any:
        """Deserialize model from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_yaml(self) -> str:
        """Serialize model to YAML formatted string."""
        return yaml.safe_dump(
            self.to_dict(),
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> Any:
        """Deserialize model from YAML string."""
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a dictionary object")
        return cls.from_dict(data)

    def save(
        self,
        output_dir: Union[str, Path],
        base_name: str,
    ) -> Tuple[Path, Path]:
        """Save model to both JSON and YAML atomically."""
        out = Path(output_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        json_path = out / f"{base_name}.json"
        yaml_path = out / f"{base_name}.yaml"
        json_path.write_text(self.to_json(indent=2), encoding="utf-8")
        yaml_path.write_text(self.to_yaml(), encoding="utf-8")
        return json_path, yaml_path

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> Any:
        """Load model from either a JSON or YAML file."""
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Contract file not found: {p}")
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in [".yaml", ".yml"]:
            return cls.from_yaml(text)
        return cls.from_json(text)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


# ===========================================================================
# 1. Creator Profile & Brand DNA Contract
# ===========================================================================
class CreatorProfile(H9BaseModel):
    """Creator persona, voice, brand guidelines, and negative constraints."""
    creator_id: str = Field(..., min_length=1, description="Unique slug for creator")
    display_name: str = Field(..., min_length=1, description="Creator public brand name")
    tone_of_voice: List[str] = Field(
        default_factory=lambda: ["authoritative", "engaging", "accessible"]
    )
    target_audiences: List[str] = Field(
        default_factory=lambda: ["tech enthusiasts", "general learners"]
    )
    brand_colors: Dict[str, str] = Field(
        default_factory=lambda: {
            "primary": "#00d2ff",
            "background": "#0a0e17",
            "text": "#ffffff",
            "accent": "#ff5252",
        }
    )
    default_format: str = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")
    negative_rules: List[str] = Field(
        default_factory=lambda: [
            "Never use buzzwords like 'game-changer' or 'revolutionize'",
            "Never use unverified hype statistics",
        ]
    )
    voice_preference: str = Field(default="default")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 2. Content Brief Contract
# ===========================================================================
class ContentBrief(H9BaseModel):
    """Initial input specification defining the content production goal."""
    project_id: str = Field(..., min_length=1, description="Unique job execution identifier")
    topic: str = Field(..., min_length=1, max_length=500)
    target_duration_seconds: int = Field(default=30, ge=5, le=600)
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")
    goal: str = Field(default="Educational Overview")
    audience: str = Field(default="General Tech Enthusiasts")
    offline_mode: bool = Field(default=True)
    custom_instructions: Optional[str] = None
    creator_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 3. Research Plan Contract
# ===========================================================================
class ResearchPlan(H9BaseModel):
    """Structured research search plan with target claims and query categories."""
    topic: str = Field(..., min_length=1)
    target_claim_count: int = Field(default=5, ge=1)
    search_queries: List[Tuple[str, str]] = Field(
        default_factory=list,
        description="List of (category, query_string) tuples",
    )
    intent_categories: List[str] = Field(
        default_factory=lambda: [
            "origin_history",
            "technical_mechanism",
            "quantitative_metric",
            "modern_impact",
        ]
    )
    timeout_seconds: float = Field(default=15.0, ge=0.1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 4. Source & Claim Records
# ===========================================================================
class SourceRecord(H9BaseModel):
    """Citation and provenance metadata for an external information source."""
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)


class ClaimRecord(H9BaseModel):
    """Factual claim backed by primary and corroborating source records."""
    claim_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    category: str = Field(default="general")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    primary_source: SourceRecord
    corroborating_sources: List[SourceRecord] = Field(default_factory=list)
    visual_cue_suggestion: str = ""
    verification_notes: str = ""


# ===========================================================================
# 5. Research Dossier Contract
# ===========================================================================
class TalkingPointRecord(H9BaseModel):
    """Script beat talking point blueprint."""
    beat_index: int = Field(default=1, ge=1)
    title: str = ""
    narrative_hook: str = ""
    supported_claim_ids: List[str] = Field(default_factory=list)
    estimated_duration_sec: float = Field(default=5.0, ge=0.0)


class StatisticRecord(H9BaseModel):
    """Key metric or numerical data point."""
    metric: str = ""
    value: str = ""
    context: str = ""
    source_claim_id: str = ""


class ResearchDossier(H9BaseModel):
    """Complete structured research dossier containing claims and talking points."""
    topic: str = Field(..., min_length=1)
    schema_version: str = "2.0.0"
    run_id: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    headline: str = ""
    executive_summary: str = ""
    key_takeaways: List[str] = Field(default_factory=list)
    claims: List[ClaimRecord] = Field(default_factory=list)
    talking_points: List[TalkingPointRecord] = Field(default_factory=list)
    statistics: List[StatisticRecord] = Field(default_factory=list)
    suggested_visual_queries: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 6. Editorial Angle & Scorecard Contracts (R2)
# ===========================================================================
class EditorialScorecard(H9BaseModel):
    """9-dimension evaluation scorecard for candidate editorial angles."""
    audience_relevance: float = Field(default=0.8, ge=0.0, le=1.0)
    novelty: float = Field(default=0.8, ge=0.0, le=1.0)
    hook_potential: float = Field(default=0.8, ge=0.0, le=1.0)
    narrative_potential: float = Field(default=0.8, ge=0.0, le=1.0)
    creator_fit: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence_availability: float = Field(default=0.8, ge=0.0, le=1.0)
    visual_potential: float = Field(default=0.8, ge=0.0, le=1.0)
    platform_fit: float = Field(default=0.8, ge=0.0, le=1.0)
    saturation_risk: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Lower indicates fresher content"
    )
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def calculate_composite_score(self) -> "EditorialScorecard":
        """Compute weighted composite score if not set."""
        if self.composite_score == 0.0:
            weights = {
                "audience_relevance": 0.15,
                "novelty": 0.15,
                "hook_potential": 0.15,
                "narrative_potential": 0.10,
                "creator_fit": 0.10,
                "evidence_availability": 0.10,
                "visual_potential": 0.10,
                "platform_fit": 0.10,
                "saturation_risk": 0.05,
            }
            score = (
                self.audience_relevance * weights["audience_relevance"]
                + self.novelty * weights["novelty"]
                + self.hook_potential * weights["hook_potential"]
                + self.narrative_potential * weights["narrative_potential"]
                + self.creator_fit * weights["creator_fit"]
                + self.evidence_availability * weights["evidence_availability"]
                + self.visual_potential * weights["visual_potential"]
                + self.platform_fit * weights["platform_fit"]
                + (1.0 - self.saturation_risk) * weights["saturation_risk"]
            )
            object.__setattr__(self, "composite_score", round(max(0.0, min(1.0, score)), 4))
        return self


# Backward compatibility alias
AngleScorecard = EditorialScorecard


class EditorialAngle(H9BaseModel):
    """Candidate or selected editorial perspective for video production."""
    angle_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    premise: str = Field(..., min_length=1)
    core_thesis: str = Field(..., min_length=1)
    target_audience: str = "General"
    narrative_style: str = "Cinematic Discovery"
    key_hooks: List[str] = Field(default_factory=list)
    scorecard: Optional[EditorialScorecard] = None
    selected: bool = False
    selection_rationale: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 7. Content Outline Contract (R2)
# ===========================================================================
class OutlineAct(H9BaseModel):
    """Individual narrative act within a 4-act production outline."""
    act_index: int = Field(..., ge=1)
    act_name: str = Field(..., min_length=1)
    target_start_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    target_end_pct: float = Field(default=0.25, ge=0.0, le=1.0)
    narrative_job: str = ""
    talking_point_indices: List[int] = Field(default_factory=list)
    visual_theme: str = "hero_graphic"


class ContentOutline(H9BaseModel):
    """Structured 4-act narrative blueprint for the scriptwriting engine."""
    project_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    angle_id: str = Field(..., min_length=1)
    angle_title: str = ""
    primary_hook: str = ""
    acts: List[OutlineAct] = Field(default_factory=list)
    total_estimated_duration: float = Field(default=30.0, ge=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 8. Script, Beat & Storyboard Contracts
# ===========================================================================
class ScriptBeat(H9BaseModel):
    """Timestamped speech beat with text, timing, and visual cue."""
    beat_id: str = Field(default_factory=lambda: f"beat_{int(time.time()*1000)}", min_length=1)
    beat_index: int = 1
    start_time: float = Field(default=0.0, ge=0.0)
    end_time: float = Field(default=0.0, ge=0.0)
    duration: float = Field(default=0.0, ge=0.0)
    text: str = Field(..., min_length=1)
    visual_cue: str = ""
    tone_modifier: Optional[str] = None
    emphasis_words: List[str] = Field(default_factory=list)
    start_second: Optional[float] = None
    end_second: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_beat_times(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "start_second" in data and "start_time" not in data:
                data["start_time"] = data["start_second"]
            elif "start_time" in data and "start_second" not in data:
                data["start_second"] = data["start_time"]
            if "end_second" in data and "end_time" not in data:
                data["end_time"] = data["end_second"]
            elif "end_time" in data and "end_second" not in data:
                data["end_second"] = data["end_time"]
            if "duration" not in data or data["duration"] == 0.0:
                st = data.get("start_time", 0.0) or 0.0
                et = data.get("end_time", 0.0) or 0.0
                if et >= st:
                    data["duration"] = et - st
        return data


class ScriptScene(H9BaseModel):
    """Individual video scene with narration, animation, and visual component properties."""
    scene_id: str = Field(..., min_length=1)
    scene_index: int = 1
    title: str = ""
    start_time: float = Field(default=0.0, ge=0.0)
    duration: float = Field(default=5.0, gt=0.0)
    narration_text: str = ""
    narration: str = ""
    visual_direction: str = ""
    estimated_duration_seconds: Optional[float] = None
    visual_asset_path: str = ""
    hero_frame_description: str = ""
    component_type: str = "reference_collage_hook"
    component_props: Dict[str, Any] = Field(default_factory=dict)
    entrance_animation: str = "fade"
    transition_out: str = "fade"
    beats: List[ScriptBeat] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_scene(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "narration" in data and "narration_text" not in data:
                data["narration_text"] = data["narration"]
            elif "narration_text" in data and "narration" not in data:
                data["narration"] = data["narration_text"]
            if "estimated_duration_seconds" in data:
                if "duration" not in data or data["duration"] == 5.0:
                    data["duration"] = data["estimated_duration_seconds"]
            elif "duration" in data and "estimated_duration_seconds" not in data:
                data["estimated_duration_seconds"] = data["duration"]
        return data


class Script(H9BaseModel):
    """Full script transcript with scene and beat timeline definitions."""
    topic: str = Field(default="Untitled", min_length=1)
    title: str = Field(default="Untitled", min_length=1)
    project_id: Optional[str] = None
    aspect_ratio: str = "16:9"
    estimated_duration_seconds: Optional[float] = None
    angle_id: Optional[str] = None
    total_duration: float = Field(default=30.0, ge=0.0)
    full_transcript: str = ""
    word_count: int = 0
    scenes: List[ScriptScene] = Field(default_factory=list)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _normalize_script(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "topic" not in data or data["topic"] is None:
                if data.get("title"):
                    data["topic"] = data["title"]
                elif data.get("project_id"):
                    data["topic"] = data["project_id"]
            if "title" not in data or data["title"] is None:
                if data.get("topic"):
                    data["title"] = data["topic"]
                elif data.get("project_id"):
                    data["title"] = data["project_id"]
            if "estimated_duration_seconds" in data and ("total_duration" not in data or data["total_duration"] == 30.0):
                data["total_duration"] = data["estimated_duration_seconds"]
            elif "total_duration" in data and "estimated_duration_seconds" not in data:
                data["estimated_duration_seconds"] = data["total_duration"]
        return data


# ===========================================================================
# 9. Asset Requirements & Asset Records
# ===========================================================================
class AssetRequirement(H9BaseModel):
    """Visual asset requirement derived from script scenes."""
    requirement_id: str = Field(..., min_length=1)
    scene_id: str = Field(..., min_length=1)
    visual_query: str = Field(..., min_length=1)
    media_type: str = "image/svg+xml"
    aspect_ratio: str = "16:9"
    style_notes: str = ""
    associated_claim_id: Optional[str] = None


class Dimensions(H9BaseModel):
    """Pixel resolution and aspect ratio for media assets."""
    width: int = 1920
    height: int = 1080
    aspect_ratio: str = "16:9"


class LicenseInfo(H9BaseModel):
    """Legal rights and license attribution metadata."""
    license_type: str = "CC0-1.0 (Public Domain)"
    license_url: Optional[str] = None
    attribution_text: str = ""
    attribution_required: bool = False
    commercial_use_allowed: bool = True
    modification_allowed: bool = True


class AssetRecord(H9BaseModel):
    """Individual frozen media asset record with cryptographic checksum and provenance."""
    asset_id: str = Field(..., min_length=1)
    local_path: str = Field(..., min_length=1)
    absolute_path: Optional[str] = None
    file_size_bytes: int = 0
    file_sha256: str = Field(..., min_length=1)
    perceptual_hash: Optional[str] = None
    media_type: str = "image/svg+xml"
    dimensions: Dimensions = Field(default_factory=Dimensions)
    source_provider: str = "procedural_generator"
    source_url: str = ""
    page_url: Optional[str] = None
    creator_name: Optional[str] = "Harness 9 Procedural Generator"
    license: LicenseInfo = Field(default_factory=LicenseInfo)
    verification_status: str = "VERIFIED"
    scene_target: str = "scene_1"
    claim_id_refs: List[str] = Field(default_factory=list)


# ===========================================================================
# 10. Evaluation & QA Contracts
# ===========================================================================
class EvaluationLayer(str, Enum):
    """4-layer evaluation stages in the ContentBench framework."""
    RESEARCH = "layer_1_research"
    SCRIPT = "layer_2_script"
    VIDEO = "layer_3_video"
    COST = "layer_4_cost"


class EvaluationReport(H9BaseModel):
    """Quality and compliance evaluation report for a production stage."""
    run_id: str = Field(..., min_length=1)
    layer: Union[EvaluationLayer, str]
    scores: Dict[str, float] = Field(default_factory=dict)
    composite_score: float = Field(default=1.0, ge=0.0, le=1.0)
    passed: bool = True
    feedback: List[str] = Field(default_factory=list)
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ===========================================================================
# 11. Render Artifact & Publish Package Contracts
# ===========================================================================
class RenderArtifact(H9BaseModel):
    """Technical and metadata specifications of a rendered video file."""
    video_path: str = Field(..., min_length=1)
    duration_seconds: float = Field(..., ge=0.0)
    file_size_bytes: int = Field(default=0, ge=0)
    width: int = 1920
    height: int = 1080
    fps: int = 30
    video_codec: str = "h264"
    audio_codec: str = "aac"
    rendered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    validation_status: str = "VERIFIED"


class PublishPackage(H9BaseModel):
    """Distribution package bundling video, captions, thumbnail, and metadata."""
    project_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    video_path: str = Field(..., min_length=1)
    thumbnail_path: Optional[str] = None
    captions_vtt_path: Optional[str] = None
    total_cost_usd: float = 0.0
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 12. Analytics & Learning Candidate Contracts (R5)
# ===========================================================================
class AnalyticsSnapshot(H9BaseModel):
    """Post-publish performance analytics metrics."""
    project_id: str = Field(..., min_length=1)
    views: int = Field(default=0, ge=0)
    average_watch_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    ctr: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    recorded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class LearningCandidate(H9BaseModel):
    """Distilled learning rule or negative constraint for creator DNA evolution."""
    lesson_id: str = Field(..., min_length=1)
    creator_id: str = Field(..., min_length=1)
    rule_type: str = "negative_constraint"
    observation: str = Field(..., min_length=1)
    recommended_action: str = Field(..., min_length=1)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ===========================================================================
# 13. Project & Production Lifecycle Contracts (M4)
# ===========================================================================
class ContentProject(H9BaseModel):
    """Complete lifecycle project record mapping H9 execution to a Hermes session."""
    project_id: str = Field(..., min_length=1, description="Unique project slug or ID")
    session_id: str = Field(..., min_length=1, description="Associated Hermes session ID")
    creator_id: str = Field(default="harness9_creator", description="Associated creator persona")
    topic: str = Field(default="", description="Core subject or headline topic")
    target_duration_seconds: int = Field(default=30, ge=5, le=600)
    aspect_ratio: str = Field(default="16:9")
    current_state: str = Field(default="CREATED", description="Current 17-state lifecycle state")
    brief: Optional[ContentBrief] = Field(default=None, description="Input production brief")
    dossier: Optional[ResearchDossier] = Field(default=None, description="Research findings and verified claims")
    selected_angle: Optional[EditorialAngle] = Field(default=None, description="Chosen editorial hook and angle")
    script: Optional[Script] = Field(default=None, description="Final multi-scene production script")
    production_ir: Optional[Dict[str, Any]] = Field(default=None, description="Compiled Production IR document")
    render_artifact: Optional[RenderArtifact] = Field(default=None, description="Rendered video artifact")
    publish_package: Optional[PublishPackage] = Field(default=None, description="Distribution publish package")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp (unix epoch)")
    updated_at: float = Field(default_factory=time.time, description="Last update timestamp (unix epoch)")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _sync_topic_from_brief(self) -> "ContentProject":
        if not self.topic and self.brief is not None:
            self.topic = self.brief.topic
        return self


class ProductionHistoryRecord(H9BaseModel):
    """Single state transition record in production audit history."""
    project_id: str = Field(..., min_length=1)
    from_state: str = Field(..., min_length=1)
    to_state: str = Field(..., min_length=1)
    timestamp: float = Field(default_factory=time.time)
    payload_summary: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
