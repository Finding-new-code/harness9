"""Script, Storyboard, and Beat schema models for R3."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from src.utils.filesystem import atomic_write, ensure_dir


@dataclass
class Beat:
    """Timestamped audio narration beat."""
    beat_id: str
    start_time: float
    end_time: float
    duration: float
    text: str
    visual_cue: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beat_id": self.beat_id,
            "start_time": float(self.start_time),
            "end_time": float(self.end_time),
            "duration": float(self.duration),
            "text": self.text,
            "visual_cue": self.visual_cue,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Beat":
        return cls(
            beat_id=str(data.get("beat_id", "")),
            start_time=float(data.get("start_time", 0.0)),
            end_time=float(data.get("end_time", 0.0)),
            duration=float(data.get("duration", 0.0)),
            text=str(data.get("text", "")),
            visual_cue=str(data.get("visual_cue", "")),
        )


@dataclass
class Scene:
    """Individual visual scene and narration unit."""
    scene_id: str
    title: str
    start_time: float
    duration: float
    narration_text: str
    visual_asset_path: str = ""
    hero_frame_description: str = ""
    entrance_animation: str = "fade"
    transition_out: str = "fade"
    beats: List[Beat] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "start_time": float(self.start_time),
            "duration": float(self.duration),
            "narration_text": self.narration_text,
            "visual_asset_path": self.visual_asset_path,
            "hero_frame_description": self.hero_frame_description,
            "entrance_animation": self.entrance_animation,
            "transition_out": self.transition_out,
            "beats": [b.to_dict() for b in self.beats],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scene":
        raw_beats = data.get("beats") or []
        beats = [Beat.from_dict(b) for b in raw_beats if isinstance(b, dict)]

        return cls(
            scene_id=str(data.get("scene_id", "")),
            title=str(data.get("title", "")),
            start_time=float(data.get("start_time", 0.0)),
            duration=float(data.get("duration", 0.0)),
            narration_text=str(data.get("narration_text", "")),
            visual_asset_path=str(data.get("visual_asset_path", "")),
            hero_frame_description=str(data.get("hero_frame_description", "")),
            entrance_animation=str(data.get("entrance_animation", "fade")),
            transition_out=str(data.get("transition_out", "fade")),
            beats=beats,
        )


@dataclass
class Storyboard:
    """Complete video scene timeline structure."""
    project_id: str
    target_duration: float
    scenes: List[Scene] = field(default_factory=list)
    aspect_ratio: str = "16:9"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "target_duration": float(self.target_duration),
            "aspect_ratio": self.aspect_ratio,
            "scenes": [s.to_dict() for s in self.scenes],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Storyboard":
        raw_scenes = data.get("scenes") or []
        scenes = [Scene.from_dict(s) for s in raw_scenes if isinstance(s, dict)]
        return cls(
            project_id=str(data.get("project_id", "")),
            target_duration=float(data.get("target_duration", 0.0)),
            scenes=scenes,
            aspect_ratio=str(data.get("aspect_ratio", "16:9")),
        )


@dataclass
class Script:
    """Generated script with narration transcript and storyboard."""
    topic: str
    title: str
    total_duration: float
    storyboard: Storyboard
    full_transcript: str = ""
    word_count: int = 0
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def scenes(self) -> List[Scene]:
        return self.storyboard.scenes if self.storyboard else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "title": self.title,
            "total_duration": float(self.total_duration),
            "full_transcript": self.full_transcript,
            "word_count": int(self.word_count),
            "generated_at": self.generated_at,
            "storyboard": self.storyboard.to_dict(),
        }

    def model_dump(self) -> Dict[str, Any]:
        return self.to_dict()

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Script":
        sb_data = data.get("storyboard") or {}
        storyboard = Storyboard.from_dict(sb_data)
        return cls(
            topic=str(data.get("topic", "")),
            title=str(data.get("title", "")),
            total_duration=float(data.get("total_duration", 0.0)),
            storyboard=storyboard,
            full_transcript=str(data.get("full_transcript", "")),
            word_count=int(data.get("word_count", 0)),
            generated_at=str(data.get("generated_at", datetime.now(timezone.utc).isoformat())),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Script":
        return cls.from_dict(json.loads(json_str))

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "Script":
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a dictionary")
        return cls.from_dict(data)

    def save(
        self,
        output_dir: Union[str, Path],
        base_name: str = "script",
    ) -> Tuple[Path, Path]:
        out_dir = ensure_dir(output_dir)
        json_path = out_dir / f"{base_name}.json"
        yaml_path = out_dir / f"{base_name}.yaml"

        atomic_write(json_path, self.to_json(indent=2), mode="w")
        atomic_write(yaml_path, self.to_yaml(), mode="w")

        return json_path, yaml_path

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "Script":
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Script file not found: {p}")
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in [".yaml", ".yml"]:
            return cls.from_yaml(text)
        return cls.from_json(text)
