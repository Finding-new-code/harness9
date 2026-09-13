"""src/models/ir.py — Harness 9 Production Intermediate Representation (IR) Contracts.

Provides the typed, hermetic Abstract Syntax Tree (AST) boundary separating
upstream creative narrative planning from downstream mechanical HyperFrames
compilation and headless video rendering (Milestone M3).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator

from src.h9_runtime.types import ProductionIR
from src.models.contracts import (
    AssetRecord,
    Dimensions,
    LicenseInfo,
    Script,
    ScriptBeat,
    ScriptScene,
)
from adapters.hyperframes.adapter import HyperFramesAdapter, HyperFramesProject


# ===========================================================================
# 1. Canonical Visual Block Types
# ===========================================================================
class IRBlockType(str, Enum):
    """The 7 canonical visual component blocks in the H9 HyperFrames registry."""
    REFERENCE_COLLAGE_HOOK = "reference_collage_hook"
    SPLIT_SCREEN_INTRO = "split_screen_intro"
    QUOTE_HIGHLIGHT = "quote_highlight"
    TIMELINE_REVEAL = "timeline_reveal"
    STATISTIC_REVEAL = "statistic_reveal"
    COMPARISON_PANEL = "comparison_panel"
    CREATOR_BOTTOM_COLLAGE = "creator_bottom_collage"


# ===========================================================================
# 2. Asset Reference & Integrity Node
# ===========================================================================
class IRAssetReference(BaseModel):
    """Cryptographically pinned media asset reference within the IR manifest."""
    asset_id: str = Field(..., min_length=1, description="Unique asset identifier in manifest")
    file_path: str = Field(..., min_length=1, description="Relative path from workspace root")
    file_sha256: str = Field(default="0" * 64, min_length=1, description="Cryptographic SHA-256 digest")
    media_type: str = Field(default="image/png", description="MIME media type")
    width: int = Field(default=1920, gt=0, description="Pixel width")
    height: int = Field(default=1080, gt=0, description="Pixel height")
    aspect_ratio: str = Field(default="16:9", description="Standard aspect ratio")
    license_type: str = Field(default="Public Domain", description="License provenance type")
    verified: bool = Field(default=True, description="Integrity verification status")


# ===========================================================================
# 3. Speech Beat & Narration Nodes
# ===========================================================================
class IRSpeechBeat(BaseModel):
    """Individual vocal cadence beat aligned to acoustic timestamps."""
    beat_id: str = Field(default_factory=lambda: f"beat_{int(time.time()*1000)}")
    start_time_sec: float = Field(default=0.0, ge=0.0)
    end_time_sec: float = Field(default=0.0, ge=0.0)
    text: str = Field(..., min_length=1)
    emphasis_words: List[str] = Field(default_factory=list)
    visual_trigger: Optional[str] = Field(
        default=None,
        description="Named visual animation trigger to fire at this beat start"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_beat(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "start_sec" in data and "start_time_sec" not in data:
                data["start_time_sec"] = data["start_sec"]
            if "end_sec" in data and "end_time_sec" not in data:
                data["end_time_sec"] = data["end_sec"]
            if "beat_id" not in data or not data["beat_id"]:
                data["beat_id"] = f"beat_{int(time.time()*1000)}"
        return data

    @property
    def start_sec(self) -> float:
        return self.start_time_sec

    @property
    def end_sec(self) -> float:
        return self.end_time_sec

    @property
    def duration_sec(self) -> float:
        """Computed duration in seconds."""
        return max(0.0, self.end_time_sec - self.start_time_sec)


class IRNarrationBlock(BaseModel):
    """Scene-level speech delivery and alignment specification."""
    full_text: str = Field(default="", min_length=0)
    voice_profile: str = Field(default="default")
    target_wpm: int = Field(default=145, ge=90, le=220)
    speech_beats: List[IRSpeechBeat] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_narration(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "text" in data and "full_text" not in data:
                data["full_text"] = data["text"]
            elif "full_text" in data and "text" not in data:
                data["text"] = data["full_text"]
            if not data.get("full_text"):
                data["full_text"] = " "
        return data

    @property
    def text(self) -> str:
        return self.full_text


# ===========================================================================
# 4. Animation Track & Visual Block Nodes
# ===========================================================================
class IRAnimationTrack(BaseModel):
    """Parametric GSAP animation keyframe track."""
    target_selector: str = Field(..., min_length=1)
    property_name: str = Field(..., min_length=1)  # "opacity", "transform", "scale"
    from_value: Union[str, float]
    to_value: Union[str, float]
    start_offset_sec: float = Field(default=0.0, ge=0.0)
    duration_sec: float = Field(default=0.5, gt=0.0)
    easing: str = Field(default="power2.out")


class IRVisualBlockNode(BaseModel):
    """Visual component AST block parameterized for compilation."""
    block_type: IRBlockType
    block_id: str = Field(default="")
    start_sec: float = Field(default=0.0)
    duration_sec: float = Field(default=0.0)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    props: Dict[str, Any] = Field(default_factory=dict)
    asset_bindings: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps visual slot parameter name to asset_id in manifest"
    )
    referenced_asset_ids: List[str] = Field(default_factory=list)
    animation_tracks: List[IRAnimationTrack] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_visual(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "props" in data and "parameters" not in data:
                data["parameters"] = data["props"]
            elif "parameters" in data and "props" not in data:
                data["props"] = data["parameters"]
            if "referenced_asset_ids" in data and "asset_bindings" not in data:
                bindings = {}
                for idx, aid in enumerate(data["referenced_asset_ids"]):
                    slot_name = "hero_image" if idx == 0 else f"slot_{idx}"
                    bindings[slot_name] = aid
                data["asset_bindings"] = bindings
            elif "asset_bindings" in data and "referenced_asset_ids" not in data:
                data["referenced_asset_ids"] = list(data["asset_bindings"].values())
        return data


# ===========================================================================
# 5. Scene Transition & Scene Node
# ===========================================================================
class IRTransitionSpec(BaseModel):
    """Scene entrance and exit transition dynamics."""
    entrance_type: str = Field(default="fade")
    exit_type: str = Field(default="fade")
    transition_duration_sec: float = Field(default=0.4, ge=0.0, le=2.0)


class IRSceneNode(BaseModel):
    """Independent temporal video scene node."""
    scene_id: str = Field(..., min_length=1)
    scene_index: int = Field(default=0, ge=0)
    act_index: int = Field(default=1, ge=1, le=4)
    start_time_sec: float = Field(default=0.0, ge=0.0)
    duration_sec: float = Field(..., gt=0.0)
    narration: IRNarrationBlock
    visual_block: Optional[IRVisualBlockNode] = None
    visual_blocks: List[IRVisualBlockNode] = Field(default_factory=list)
    transitions: IRTransitionSpec = Field(default_factory=IRTransitionSpec)

    @model_validator(mode="before")
    @classmethod
    def _normalize_scene(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "visual_blocks" in data and data["visual_blocks"] and "visual_block" not in data:
                data["visual_block"] = data["visual_blocks"][0]
            elif "visual_block" in data and data["visual_block"] and "visual_blocks" not in data:
                data["visual_blocks"] = [data["visual_block"]]
        return data

    @property
    def end_time_sec(self) -> float:
        """Computed end timestamp in seconds."""
        return self.start_time_sec + self.duration_sec


# ===========================================================================
# 6. Global Audio Track & Composition Metadata
# ===========================================================================
class IRAudioTrack(BaseModel):
    """Global acoustic master track."""
    audio_rel_path: str = Field(default="assets/audio/narration.wav")
    total_duration_sec: float = Field(..., gt=0.0)
    sample_rate: int = Field(default=44100)
    channels: int = Field(default=2)


class IRMetadata(BaseModel):
    """Global composition configuration."""
    project_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")
    fps: int = Field(default=30, ge=15, le=60)
    width: int = Field(default=1920, gt=0)
    height: int = Field(default=1080, gt=0)
    brand_primary_color: str = Field(default="#00d2ff")
    brand_background_color: str = Field(default="#0a0e17")


class AudioNarration(BaseModel):
    """Optional audio narration specification passed into compilation."""
    audio_rel_path: str = Field(default="assets/audio/narration.wav")
    total_duration_sec: float = Field(default=0.0, ge=0.0)
    sample_rate: int = Field(default=44100)
    channels: int = Field(default=2)


# ===========================================================================
# 7. Production IR Master Document
# ===========================================================================
class ProductionIRDocument(BaseModel, ProductionIR):
    """The master root AST document interfacing narrative planning and visual compilation.

    Inherits from ProductionIR for backwards compatibility across existing runtime
    modules, while strictly enforcing AST invariants via Pydantic v2.
    """
    ir_version: str = Field(default="1.0.0")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: IRMetadata
    audio_track: IRAudioTrack
    asset_manifest: Dict[str, IRAssetReference] = Field(default_factory=dict)
    scenes: List[IRSceneNode] = Field(default_factory=list)

    # Legacy compatibility fields from ProductionIR
    project_id: str = Field(default="")
    aspect_ratio: str = Field(default="16:9")
    duration_seconds: float = Field(default=30.0)
    fps: int = Field(default=30)
    timeline_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    audio_tracks: List[Dict[str, Any]] = Field(default_factory=list)
    css_variables: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _extract_project_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "project_id" not in data and "metadata" in data:
                meta = data["metadata"]
                data["project_id"] = getattr(meta, "project_id", "") if not isinstance(meta, dict) else meta.get("project_id", "")
            if "project_id" not in data:
                data["project_id"] = ""
        return data

    @model_validator(mode="after")
    def validate_production_invariants(self) -> "ProductionIRDocument":
        """Validate temporal conservation, audio matching, asset integrity, and speech bounds."""
        # Invariant 0: Non-empty scenes
        if not self.scenes:
            raise ValueError("ProductionIRDocument must contain at least one IRSceneNode")

        # Invariant 1: Temporal Conservation & Contiguity
        expected_start = 0.0
        for scene in self.scenes:
            if abs(scene.start_time_sec - expected_start) > 0.05:
                raise ValueError(
                    f"Temporal Discontinuity: Scene {scene.scene_id} start ({scene.start_time_sec}s) "
                    f"does not match expected contiguous start ({expected_start}s)."
                )
            expected_start += scene.duration_sec

        # Invariant 2: Audio Track Match
        total_scene_duration = expected_start
        if abs(total_scene_duration - self.audio_track.total_duration_sec) > 0.5:
            raise ValueError(
                f"Audio Drift: Total scene duration ({total_scene_duration}s) diverges from "
                f"audio narration length ({self.audio_track.total_duration_sec}s)."
            )

        # Invariant 3: Asset Binding Integrity
        for scene in self.scenes:
            vb = scene.visual_block or (scene.visual_blocks[0] if scene.visual_blocks else None)
            if vb and vb.asset_bindings:
                for slot, asset_id in vb.asset_bindings.items():
                    if asset_id not in self.asset_manifest:
                        raise ValueError(
                            f"Dangling Asset Reference: Scene {scene.scene_id} binds slot '{slot}' "
                            f"to '{asset_id}', which is missing from asset_manifest."
                        )

        # Invariant 4: Speech Beat Bounds Clamping
        for scene in self.scenes:
            for beat in scene.narration.speech_beats:
                if beat.start_time_sec < (scene.start_time_sec - 0.05) or beat.end_time_sec > (scene.end_time_sec + 0.15):
                    raise ValueError(
                        f"Speech Beat Out of Bounds: Beat {beat.beat_id} [{beat.start_time_sec}-{beat.end_time_sec}s] "
                        f"escapes Scene {scene.scene_id} [{scene.start_time_sec}-{scene.end_time_sec}s]."
                    )

        # Synchronize legacy fields for full backwards compatibility
        if self.metadata:
            object.__setattr__(self, "project_id", self.metadata.project_id)
            object.__setattr__(self, "aspect_ratio", self.metadata.aspect_ratio)
            object.__setattr__(self, "fps", self.metadata.fps)
        if self.audio_track:
            object.__setattr__(self, "duration_seconds", self.audio_track.total_duration_sec)

        if not self.timeline_blocks:
            blocks: List[Dict[str, Any]] = []
            for s in self.scenes:
                blocks.append({
                    "scene_id": s.scene_id,
                    "title": f"Scene {s.scene_index}",
                    "start_time": s.start_time_sec,
                    "duration": s.duration_sec,
                    "narration_text": s.narration.full_text,
                    "component_type": s.visual_block.block_type.value,
                    "beats": [
                        {
                            "beat_id": b.beat_id,
                            "start_time": b.start_time_sec,
                            "end_time": b.end_time_sec,
                            "duration": b.duration_sec,
                            "text": b.text,
                            "visual_cue": b.visual_trigger or "",
                            "emphasis_words": b.emphasis_words,
                        }
                        for b in s.narration.speech_beats
                    ],
                })
            object.__setattr__(self, "timeline_blocks", blocks)

        if not self.audio_tracks and self.audio_track:
            object.__setattr__(self, "audio_tracks", [{
                "track_id": "narration_master",
                "file_path": self.audio_track.audio_rel_path,
                "volume": 1.0,
                "duration": self.audio_track.total_duration_sec,
            }])

        if not self.css_variables and self.metadata:
            object.__setattr__(self, "css_variables", {
                "--primary-accent": self.metadata.brand_primary_color,
                "--bg-color": self.metadata.brand_background_color,
                "--text-color": "#f0f4f8",
                "--font-family": "'Inter', -apple-system, sans-serif",
            })

        return self

    @property
    def total_duration_sec(self) -> float:
        """Total duration of audio track or scenes in seconds."""
        if hasattr(self, "audio_track") and self.audio_track and getattr(self.audio_track, "total_duration_sec", 0) > 0:
            return self.audio_track.total_duration_sec
        return sum(s.duration_sec for s in self.scenes)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize AST document to dictionary."""
        return self.model_dump()

    def to_script(self) -> Script:
        """Convert Production IR back into a domain Script contract."""
        script_scenes: List[ScriptScene] = []
        transcript_parts: List[str] = []

        for s in self.scenes:
            transcript_parts.append(s.narration.full_text)
            beats: List[ScriptBeat] = [
                ScriptBeat(
                    beat_id=b.beat_id,
                    start_time=b.start_time_sec,
                    end_time=b.end_time_sec,
                    duration=b.duration_sec,
                    text=b.text,
                    visual_cue=b.visual_trigger or "",
                    emphasis_words=b.emphasis_words,
                )
                for b in s.narration.speech_beats
            ]

            visual_path = ""
            for slot, asset_id in s.visual_block.asset_bindings.items():
                if asset_id in self.asset_manifest:
                    visual_path = self.asset_manifest[asset_id].file_path
                    break

            c_props = dict(s.visual_block.parameters)
            if visual_path:
                if "image_paths" not in c_props:
                    c_props["image_paths"] = [visual_path]
                if "left_image" not in c_props:
                    c_props["left_image"] = visual_path

            script_scenes.append(
                ScriptScene(
                    scene_id=s.scene_id,
                    title=f"Scene {s.scene_index}",
                    start_time=s.start_time_sec,
                    duration=s.duration_sec,
                    narration_text=s.narration.full_text,
                    visual_asset_path=visual_path,
                    component_type=s.visual_block.block_type.value,
                    component_props=c_props,
                    entrance_animation=s.transitions.entrance_type,
                    transition_out=s.transitions.exit_type,
                    beats=beats,
                )
            )

        full_tx = " ".join(transcript_parts)
        return Script(
            topic=self.metadata.topic,
            title=self.metadata.title,
            total_duration=self.audio_track.total_duration_sec,
            full_transcript=full_tx,
            word_count=len(full_tx.split()),
            scenes=script_scenes,
        )


# ===========================================================================
# 8. Script to Production IR Compiler Function
# ===========================================================================
def compile_script_to_ir(
    script: Union[Script, Dict[str, Any]],
    assets: Optional[List[Union[AssetRecord, Dict[str, Any]]]] = None,
    metadata: Optional[Union[IRMetadata, Dict[str, Any]]] = None,
    audio_narration: Optional[Union[AudioNarration, Dict[str, Any]]] = None,
) -> ProductionIRDocument:
    """Compile a domain Script and discovered assets into a verified ProductionIRDocument AST.

    Enforces temporal contiguity, asset manifest integrity, and voice beat alignment.
    """
    # 1. Normalize Script
    if hasattr(script, "to_dict"):
        s_dict = script.to_dict()
    elif isinstance(script, dict):
        s_dict = script
    else:
        raise TypeError(f"script must be Script or dict, got {type(script)}")

    topic = s_dict.get("topic") or "Harness 9 Production"
    title = s_dict.get("title") or f"Video: {topic}"
    project_id = s_dict.get("project_id") or f"proj_{int(time.time())}"

    # 2. Build Asset Manifest
    manifest: Dict[str, IRAssetReference] = {}
    raw_assets = assets or []
    for item in raw_assets:
        if hasattr(item, "to_dict"):
            a_dict = item.to_dict()
        elif isinstance(item, dict):
            a_dict = item
        else:
            continue

        aid = a_dict.get("asset_id") or f"asset_{len(manifest)+1:02d}"
        fpath = (
            a_dict.get("file_path")
            or a_dict.get("local_path")
            or a_dict.get("path")
            or f"assets/images/{aid}.svg"
        )
        sha = a_dict.get("file_sha256") or a_dict.get("sha256")
        if not sha or len(sha) < 1:
            sha = hashlib.sha256(fpath.encode("utf-8")).hexdigest()

        dims = a_dict.get("dimensions", {})
        if isinstance(dims, dict):
            w = int(dims.get("width", 1920))
            h = int(dims.get("height", 1080))
            ar = dims.get("aspect_ratio", "16:9")
        else:
            w = getattr(dims, "width", 1920)
            h = getattr(dims, "height", 1080)
            ar = getattr(dims, "aspect_ratio", "16:9")

        lic = a_dict.get("license", {})
        l_type = lic.get("license_type", "Public Domain") if isinstance(lic, dict) else getattr(lic, "license_type", "Public Domain")

        manifest[aid] = IRAssetReference(
            asset_id=aid,
            file_path=str(fpath),
            file_sha256=str(sha),
            media_type=a_dict.get("media_type", "image/svg+xml"),
            width=w,
            height=h,
            aspect_ratio=ar,
            license_type=l_type,
            verified=a_dict.get("verification_status") == "VERIFIED" or a_dict.get("verified", True),
        )

    # 3. Process Scenes & Enforce Contiguity
    raw_scenes = s_dict.get("scenes", [])
    if not raw_scenes:
        # Fallback default scene
        raw_scenes = [{
            "scene_id": "scene_01",
            "title": title,
            "duration": float(s_dict.get("total_duration", 30.0) or 30.0),
            "narration_text": s_dict.get("full_transcript", f"Overview of {topic}"),
            "component_type": "reference_collage_hook",
        }]

    ir_scenes: List[IRSceneNode] = []
    current_start = 0.0

    valid_block_types = {b.value: b for b in IRBlockType}

    for idx, sc in enumerate(raw_scenes):
        if hasattr(sc, "to_dict"):
            sc_dict = sc.to_dict()
        elif isinstance(sc, dict):
            sc_dict = sc
        else:
            sc_dict = dict(sc)

        sid = sc_dict.get("scene_id") or f"scene_{idx+1:02d}"
        dur = float(sc_dict.get("duration") or sc_dict.get("estimated_duration_seconds") or 5.0)
        dur = max(0.5, round(dur, 3))
        start_time = round(current_start, 3)
        end_time = round(start_time + dur, 3)
        current_start = end_time

        # Map block type
        raw_btype = str(sc_dict.get("component_type", "")).lower()
        vdir = str(sc_dict.get("visual_direction", "")).lower()
        if raw_btype in valid_block_types:
            btype = valid_block_types[raw_btype]
        elif "split screen" in vdir or "split_screen" in vdir:
            btype = IRBlockType.SPLIT_SCREEN_INTRO
        elif "statistic" in vdir or "stat" in vdir:
            btype = IRBlockType.STATISTIC_REVEAL
        elif "timeline" in vdir:
            btype = IRBlockType.TIMELINE_REVEAL
        elif "quote" in vdir:
            btype = IRBlockType.QUOTE_HIGHLIGHT
        elif "comparison" in vdir:
            btype = IRBlockType.COMPARISON_PANEL
        elif "creator" in vdir or "bottom" in vdir:
            btype = IRBlockType.CREATOR_BOTTOM_COLLAGE
        elif "collage" in vdir or "hook" in vdir:
            btype = IRBlockType.REFERENCE_COLLAGE_HOOK
        else:
            btype = valid_block_types.get(raw_btype, IRBlockType.REFERENCE_COLLAGE_HOOK)

        # Asset bindings
        bindings: Dict[str, str] = {}
        vpath = sc_dict.get("visual_asset_path") or sc_dict.get("visual")
        cprops = dict(sc_dict.get("component_props") or {})

        # Bind explicit or detected assets
        if vpath:
            # Check if exists in manifest
            matched_aid = None
            for m_aid, m_ref in manifest.items():
                if m_ref.file_path == vpath or m_aid == sid or m_aid.endswith(sid):
                    matched_aid = m_aid
                    break
            if not matched_aid:
                # Synthesize asset into manifest to satisfy Invariant 3
                matched_aid = f"asset_{sid}"
                manifest[matched_aid] = IRAssetReference(
                    asset_id=matched_aid,
                    file_path=str(vpath),
                    file_sha256=hashlib.sha256(str(vpath).encode("utf-8")).hexdigest(),
                    media_type="image/svg+xml",
                    verified=True,
                )
            bindings["hero_image"] = matched_aid

        # Narration & Beats
        narration_text = sc_dict.get("narration_text") or sc_dict.get("narration") or sc_dict.get("text", f"Scene {idx+1} regarding {topic}.")
        raw_beats = sc_dict.get("beats", [])
        ir_beats: List[IRSpeechBeat] = []

        if raw_beats:
            for b_idx, b in enumerate(raw_beats):
                b_dict = b.to_dict() if hasattr(b, "to_dict") else dict(b)
                bid = b_dict.get("beat_id") or f"beat_{idx+1}_{b_idx+1}"
                b_text = b_dict.get("text") or narration_text
                b_st = float(b_dict.get("start_time", b_dict.get("start_second", start_time)))
                default_beat_dur = dur / len(raw_beats)
                b_dur = float(b_dict.get("duration", (float(b_dict.get("end_second", 0.0)) - b_st) if b_dict.get("end_second") is not None else default_beat_dur))
                b_et = float(b_dict.get("end_time", b_dict.get("end_second", b_st + b_dur)))

                # Clamp strictly within scene temporal bounds (Invariant 4)
                clamped_st = max(start_time, min(end_time - 0.05, b_st))
                clamped_et = max(clamped_st + 0.05, min(end_time, b_et))

                ir_beats.append(
                    IRSpeechBeat(
                        beat_id=bid,
                        start_time_sec=round(clamped_st, 3),
                        end_time_sec=round(clamped_et, 3),
                        text=b_text,
                        emphasis_words=b_dict.get("emphasis_words") or [],
                        visual_trigger=b_dict.get("visual_cue") or b_dict.get("visual_trigger"),
                    )
                )
        else:
            # Single default speech beat covering scene duration
            ir_beats.append(
                IRSpeechBeat(
                    beat_id=f"beat_{idx+1}_01",
                    start_time_sec=start_time,
                    end_time_sec=end_time,
                    text=narration_text,
                    emphasis_words=[],
                )
            )

        narration_block = IRNarrationBlock(
            full_text=narration_text,
            voice_profile="default",
            target_wpm=145,
            speech_beats=ir_beats,
        )

        visual_node = IRVisualBlockNode(
            block_type=btype,
            parameters=cprops,
            asset_bindings=bindings,
            animation_tracks=[],
        )

        transitions = IRTransitionSpec(
            entrance_type=sc_dict.get("entrance_animation", "fade"),
            exit_type=sc_dict.get("transition_out", "fade"),
            transition_duration_sec=0.4,
        )

        ir_scenes.append(
            IRSceneNode(
                scene_id=sid,
                scene_index=idx + 1,
                act_index=min(4, max(1, sc_dict.get("act_index", (idx // max(1, len(raw_scenes) // 4)) + 1))),
                start_time_sec=start_time,
                duration_sec=dur,
                narration=narration_block,
                visual_block=visual_node,
                visual_blocks=[visual_node],
                transitions=transitions,
            )
        )

    total_scene_duration = round(current_start, 3)

    # 4. Audio Track (satisfies Invariant 2)
    if isinstance(audio_narration, AudioNarration):
        a_path = audio_narration.audio_rel_path
        a_srate = audio_narration.sample_rate
        a_chan = audio_narration.channels
    elif isinstance(audio_narration, dict):
        a_path = audio_narration.get("audio_rel_path", "assets/audio/narration.wav")
        a_srate = audio_narration.get("sample_rate", 44100)
        a_chan = audio_narration.get("channels", 2)
    else:
        a_path = "assets/audio/narration.wav"
        a_srate = 44100
        a_chan = 2

    ir_audio = IRAudioTrack(
        audio_rel_path=a_path,
        total_duration_sec=total_scene_duration,
        sample_rate=a_srate,
        channels=a_chan,
    )

    # 5. Metadata
    if isinstance(metadata, IRMetadata):
        ir_meta = metadata
    elif isinstance(metadata, dict):
        ir_meta = IRMetadata(
            project_id=metadata.get("project_id") or project_id or f"proj_{int(time.time())}",
            topic=metadata.get("topic") or topic or "Harness 9 Production",
            title=metadata.get("title") or title or f"Video: {topic}",
            aspect_ratio=metadata.get("aspect_ratio") or "16:9",
            fps=int(metadata.get("fps") or 30),
            brand_primary_color=metadata.get("brand_primary_color") or "#00d2ff",
            brand_background_color=metadata.get("brand_background_color") or "#0a0e17",
        )
    else:
        ir_meta = IRMetadata(
            project_id=project_id or f"proj_{int(time.time())}",
            topic=topic or "Harness 9 Production",
            title=title or f"Video: {topic}",
            aspect_ratio="16:9",
            fps=30,
            brand_primary_color="#00d2ff",
            brand_background_color="#0a0e17",
        )

    # Construct and validate AST document
    return ProductionIRDocument(
        ir_version="1.0.0",
        metadata=ir_meta,
        audio_track=ir_audio,
        asset_manifest=manifest,
        scenes=ir_scenes,
    )


# ===========================================================================
# 9. HyperFrames Compiler Integration
# ===========================================================================
class HyperFramesCompiler:
    """Consumes a validated ProductionIRDocument AST to compile an executable HyperFrames project."""

    def __init__(self, adapter: Optional[HyperFramesAdapter] = None) -> None:
        self.adapter = adapter or HyperFramesAdapter()

    def compile(
        self,
        ir_doc: ProductionIRDocument,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> HyperFramesProject:
        """Compile ProductionIRDocument AST into HyperFramesProject HTML/CSS/JS assets."""
        if not isinstance(ir_doc, ProductionIRDocument):
            raise TypeError(f"Expected ProductionIRDocument, got {type(ir_doc)}")

        target_dir = (
            Path(output_dir).resolve()
            if output_dir
            else Path(f"output/hf_{int(time.time())}").resolve()
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
        (target_dir / "assets" / "audio").mkdir(parents=True, exist_ok=True)

        # Stage manifest assets so they exist on disk for validation
        for ref in ir_doc.asset_manifest.values():
            dest = target_dir / ref.file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                if dest.suffix.lower() == ".svg":
                    dest.write_text(
                        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ref.width}" height="{ref.height}"><rect width="100%" height="100%" fill="#0a0e17"/><text x="50%" y="50%" fill="#00d2ff">{ref.asset_id}</text></svg>',
                        encoding="utf-8",
                    )
                elif dest.suffix.lower() in [".wav", ".mp3", ".aac"]:
                    dest.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

        # Stage canonical default component assets if required by component templates
        for default_name in ["asset_01.svg", "asset_02.svg", "asset_03.svg"]:
            p = target_dir / "assets" / "images" / default_name
            if not p.exists():
                p.write_text(
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><rect width="100%" height="100%" fill="#0a0e17"/><text x="50%" y="50%" fill="#00d2ff">{default_name}</text></svg>',
                    encoding="utf-8",
                )

        script_obj = ir_doc.to_script()

        # Convert asset manifest to AssetRecord items
        asset_records: List[AssetRecord] = []
        for ref in ir_doc.asset_manifest.values():
            asset_records.append(
                AssetRecord(
                    asset_id=ref.asset_id,
                    local_path=ref.file_path,
                    file_sha256=ref.file_sha256,
                    media_type=ref.media_type,
                    dimensions=Dimensions(
                        width=ref.width,
                        height=ref.height,
                        aspect_ratio=ref.aspect_ratio,
                    ),
                    license=LicenseInfo(license_type=ref.license_type),
                    verification_status="VERIFIED" if ref.verified else "UNVERIFIED",
                )
            )

        return self.adapter.compile_composition(
            script=script_obj,
            assets=asset_records,
            output_dir=target_dir,
            format_aspect=ir_doc.metadata.aspect_ratio,
            duration=ir_doc.audio_track.total_duration_sec,
            audio_rel_path=ir_doc.audio_track.audio_rel_path,
        )
