"""
src.scriptwriting.aligner — Audio Beat & Transcript Alignment Engine.

Computes timestamped intervals [start, end] per scene, beat, and word group,
producing structured transcript.json for HyperFrames synchronized captions.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.models.script import Beat, Scene, Script
from src.utils.filesystem import atomic_write, ensure_dir


@dataclass
class WordTimestamp:
    """Individual word with precise start and end timestamps."""
    word: str
    start: float
    end: float
    scene_id: str = "scene_1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "scene_id": self.scene_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WordTimestamp":
        return cls(
            word=str(data.get("word", "")),
            start=float(data.get("start", 0.0)),
            end=float(data.get("end", 0.0)),
            scene_id=str(data.get("scene_id", "scene_1")),
        )


@dataclass
class TranscriptGroup:
    """Group of 2-5 words for kinetic on-screen caption phrases."""
    text: str
    start: float
    end: float
    scene_id: str
    word_count: int
    words: List[WordTimestamp] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "scene_id": self.scene_id,
            "word_count": self.word_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptGroup":
        return cls(
            text=str(data.get("text", "")),
            start=float(data.get("start", 0.0)),
            end=float(data.get("end", 0.0)),
            scene_id=str(data.get("scene_id", "")),
            word_count=int(data.get("word_count", 0)),
        )


@dataclass
class TranscriptScene:
    """Scene-level transcript with timing boundaries and narration text."""
    scene_id: str
    start: float
    end: float
    duration: float
    text: str
    word_count: int
    groups: List[TranscriptGroup] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.duration, 3),
            "text": self.text,
            "word_count": self.word_count,
            "groups": [g.to_dict() for g in self.groups],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptScene":
        raw_groups = data.get("groups") or []
        groups = [TranscriptGroup.from_dict(g) for g in raw_groups if isinstance(g, dict)]
        return cls(
            scene_id=str(data.get("scene_id", "")),
            start=float(data.get("start", 0.0)),
            end=float(data.get("end", 0.0)),
            duration=float(data.get("duration", 0.0)),
            text=str(data.get("text", "")),
            word_count=int(data.get("word_count", 0)),
            groups=groups,
        )


@dataclass
class TranscriptResult:
    """Complete transcript alignment result containing words, groups, and scenes."""
    total_duration: float
    total_words: int
    words: List[WordTimestamp] = field(default_factory=list)
    groups: List[TranscriptGroup] = field(default_factory=list)
    scenes: List[TranscriptScene] = field(default_factory=list)
    schema_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "total_duration": round(self.total_duration, 3),
            "total_words": self.total_words,
            "scenes": [s.to_dict() for s in self.scenes],
            "groups": [g.to_dict() for g in self.groups],
            "words": [w.to_dict() for w in self.words],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptResult":
        raw_words = data.get("words") or []
        words = [WordTimestamp.from_dict(w) for w in raw_words if isinstance(w, dict)]

        raw_groups = data.get("groups") or []
        groups = [TranscriptGroup.from_dict(g) for g in raw_groups if isinstance(g, dict)]

        raw_scenes = data.get("scenes") or []
        scenes = [TranscriptScene.from_dict(s) for s in raw_scenes if isinstance(s, dict)]

        return cls(
            schema_version=str(data.get("schema_version", "1.0.0")),
            total_duration=float(data.get("total_duration", 0.0)),
            total_words=int(data.get("total_words", len(words))),
            words=words,
            groups=groups,
            scenes=scenes,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "TranscriptResult":
        return cls.from_dict(json.loads(json_str))

    def save(self, file_path: Union[str, Path]) -> Path:
        out_p = Path(file_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(out_p, self.to_json(indent=2), mode="w")
        return out_p


class TranscriptAligner:
    """
    Computes precise time offsets for words and caption phrase groups across scenes.
    """

    def __init__(self, target_words_per_group: int = 3):
        self.target_words_per_group = max(2, min(6, target_words_per_group))

    def align_scenes(
        self,
        scenes: List[Scene],
        total_duration: Optional[float] = None,
    ) -> TranscriptResult:
        """
        Compute timestamped word intervals and caption groups for a list of scenes.
        """
        all_words: List[WordTimestamp] = []
        all_groups: List[TranscriptGroup] = []
        scene_results: List[TranscriptScene] = []

        if not scenes:
            return TranscriptResult(
                total_duration=total_duration or 0.0,
                total_words=0,
                words=[],
                groups=[],
                scenes=[],
            )

        calc_total_duration = sum(s.duration for s in scenes)
        effective_total_duration = total_duration if (total_duration and total_duration > 0) else calc_total_duration

        # Scale scene durations if needed to match effective_total_duration
        scale_factor = (effective_total_duration / calc_total_duration) if calc_total_duration > 0 else 1.0

        current_time = 0.0

        for scene in scenes:
            scene_duration = scene.duration * scale_factor
            scene_start = current_time
            scene_end = scene_start + scene_duration

            words_raw = scene.narration_text.split()
            scene_words_count = len(words_raw)

            if scene_words_count == 0:
                scene_results.append(TranscriptScene(
                    scene_id=scene.scene_id,
                    start=scene_start,
                    end=scene_end,
                    duration=scene_duration,
                    text="",
                    word_count=0,
                    groups=[],
                ))
                current_time = scene_end
                continue

            # Calculate word weights (character count + syllable factor + punctuation pauses)
            word_weights = []
            for w in words_raw:
                clean_w = re.sub(r'[^\w]', '', w)
                length_weight = max(1, len(clean_w))
                syllable_count = max(1, len(re.findall(r'[aeiouy]', clean_w.lower())))
                base_weight = length_weight * 0.6 + syllable_count * 1.5

                if w.endswith((".", "!", "?")):
                    base_weight += 3.0
                elif w.endswith((",", ";", ":")):
                    base_weight += 1.5
                word_weights.append(base_weight)

            total_weight = sum(word_weights)
            # Allocate duration per word proportionally
            scene_word_timestamps: List[WordTimestamp] = []
            word_time_cursor = scene_start

            for idx, (word_str, weight) in enumerate(zip(words_raw, word_weights)):
                w_dur = (weight / total_weight) * scene_duration
                w_start = word_time_cursor
                w_end = min(scene_end, w_start + w_dur)
                # If last word in scene, ensure it spans up to scene_end
                if idx == len(words_raw) - 1:
                    w_end = scene_end

                wt = WordTimestamp(
                    word=word_str,
                    start=round(w_start, 3),
                    end=round(w_end, 3),
                    scene_id=scene.scene_id,
                )
                scene_word_timestamps.append(wt)
                all_words.append(wt)
                word_time_cursor = w_end

            # Group words into caption chunks (2-4 words each)
            scene_groups: List[TranscriptGroup] = []
            chunk_size = self.target_words_per_group
            
            for g_idx in range(0, len(scene_word_timestamps), chunk_size):
                chunk = scene_word_timestamps[g_idx: g_idx + chunk_size]
                if not chunk:
                    continue
                group_text = " ".join([w.word for w in chunk])
                g_start = chunk[0].start
                g_end = chunk[-1].end

                tg = TranscriptGroup(
                    text=group_text,
                    start=round(g_start, 3),
                    end=round(g_end, 3),
                    scene_id=scene.scene_id,
                    word_count=len(chunk),
                    words=chunk,
                )
                scene_groups.append(tg)
                all_groups.append(tg)

            scene_results.append(TranscriptScene(
                scene_id=scene.scene_id,
                start=round(scene_start, 3),
                end=round(scene_end, 3),
                duration=round(scene_duration, 3),
                text=scene.narration_text,
                word_count=len(scene_word_timestamps),
                groups=scene_groups,
            ))

            current_time = scene_end

        return TranscriptResult(
            total_duration=round(effective_total_duration, 3),
            total_words=len(all_words),
            words=all_words,
            groups=all_groups,
            scenes=scene_results,
        )

    def align_from_text(
        self,
        full_text: str,
        total_duration: float,
        scene_count: int = 3,
    ) -> TranscriptResult:
        """
        Helper method to align a single unbroken text string across multiple scenes.
        """
        words = full_text.split()
        if not words:
            return TranscriptResult(total_duration=total_duration, total_words=0)

        words_per_scene = max(1, len(words) // scene_count)
        scenes: List[Scene] = []
        dur_per_scene = total_duration / float(scene_count)

        for i in range(scene_count):
            start_idx = i * words_per_scene
            end_idx = (i + 1) * words_per_scene if i < scene_count - 1 else len(words)
            scene_text = " ".join(words[start_idx:end_idx])

            scenes.append(Scene(
                scene_id=f"scene_{i+1}",
                title=f"Section {i+1}",
                start_time=i * dur_per_scene,
                duration=dur_per_scene,
                narration_text=scene_text,
            ))

        return self.align_scenes(scenes, total_duration=total_duration)
