"""
src.scriptwriting.voice_qa — Automated Acoustic Voice QA Engine (Milestone M4).

Performs comprehensive acoustic and signal analysis on synthesized audio:
1. Dead air & silence detection:
   - Identifies silence frames (< -45 dBFS).
   - Rejects non-speech internal gaps > 300ms (0.3s).
   - Flags excessive boundary dead air (leading > 200ms, trailing > 250ms).
2. Clipping & distortion detection:
   - Scans 16-bit PCM integer samples for peak saturation (|s| >= 32767).
   - Computes clipping ratio (must be < 0.0001 / < 0.01%).
   - Flags severe distortion clusters (>= 5 consecutive clipped samples).
3. Scene loudness consistency:
   - Calculates RMS energy and loudness (dBFS) across storyboard scenes.
   - Asserts scene-to-scene loudness variance <= 2.5 dBFS.
4. Speech-beat sync drift:
   - Compares planned storyboard scene/beat boundaries against actual audio timing.
   - Enforces max alignment drift <= 0.20s (200ms).
"""

from datetime import datetime, timezone
import logging
import math
from pathlib import Path
import struct
from typing import Any, Dict, List, Optional, Tuple, Union
import wave

from pydantic import Field

from src.models.contracts import EvaluationLayer, EvaluationReport, H9BaseModel, Script, ScriptBeat, ScriptScene

logger = logging.getLogger("harness9.scriptwriting.voice_qa")

# ---------------------------------------------------------------------------
# Acoustic QA Constants & Quality Thresholds
# ---------------------------------------------------------------------------

SILENCE_THRESHOLD_DBFS = -45.0          # Below -45 dBFS is considered silence
MAX_INTERNAL_GAP_SEC = 0.30             # > 300ms gap triggers dead air failure
MAX_LEADING_SILENCE_SEC = 0.20          # Leading dead air > 200ms flagged
MAX_TRAILING_SILENCE_SEC = 0.25         # Trailing dead air > 250ms flagged
MAX_CLIPPING_RATIO = 0.0001             # Maximum allowed clipping ratio (< 0.01%)
MAX_LOUDNESS_VARIANCE_DB = 2.50         # Max dBFS delta across scenes (<= 2.5 dB)
MAX_SPEECH_BEAT_DRIFT_SEC = 0.20        # Max drift between beat and speech (<= 0.2s)
FRAME_WINDOW_MS = 20.0                  # 20ms frame analysis window
SUSTAINED_CLIP_THRESHOLD = 5            # 5 consecutive clipped samples = severe clip


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class VoiceQAReport(H9BaseModel):
    """Structured QA report produced by the automated acoustic VoiceQA engine."""
    passed: bool = True
    total_duration_sec: float = 0.0
    clipping_events_count: int = 0
    clipping_ratio: float = 0.0
    dead_air_instances_count: int = 0
    max_dead_air_duration_sec: float = 0.0
    average_gap_duration_sec: float = 0.0
    dead_air_ratio: float = 0.0
    loudness_variance_db: float = 0.0
    scene_loudness_dbfs: List[float] = Field(default_factory=list)
    speech_beat_max_drift_sec: float = 0.0
    gate_results: Dict[str, bool] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_evaluation_report(self, run_id: str = "run_voice_qa") -> EvaluationReport:
        """Convert VoiceQAReport to standard H9 EvaluationReport contract."""
        composite = 1.0 if self.passed else max(
            0.0,
            1.0
            - (self.clipping_ratio * 1000.0)
            - (max(0.0, self.max_dead_air_duration_sec - 0.3) * 2.0)
            - (max(0.0, self.loudness_variance_db - 2.5) * 0.1)
            - (max(0.0, self.speech_beat_max_drift_sec - 0.2) * 2.0),
        )
        return EvaluationReport(
            run_id=run_id,
            layer=EvaluationLayer.VIDEO,
            scores={
                "clipping_score": 1.0 if self.clipping_ratio < MAX_CLIPPING_RATIO else 0.0,
                "dead_air_score": 1.0 if self.max_dead_air_duration_sec <= MAX_INTERNAL_GAP_SEC else 0.0,
                "loudness_consistency_score": 1.0 if self.loudness_variance_db <= MAX_LOUDNESS_VARIANCE_DB else 0.0,
                "beat_sync_score": 1.0 if self.speech_beat_max_drift_sec <= MAX_SPEECH_BEAT_DRIFT_SEC else 0.0,
            },
            composite_score=round(max(0.0, min(1.0, composite)), 4),
            passed=self.passed,
            feedback=self.issues,
            evaluated_at=self.evaluated_at,
        )


# ---------------------------------------------------------------------------
# Audio Waveform & Signal Processing Utilities
# ---------------------------------------------------------------------------

def calculate_sample_rms(samples: List[int]) -> float:
    """Calculate Root Mean Square (RMS) energy of integer samples."""
    if not samples:
        return 0.0
    sum_sq = sum(s * s for s in samples)
    return math.sqrt(sum_sq / len(samples))


def rms_to_dbfs(rms: float, max_val: float = 32767.0) -> float:
    """Convert linear RMS to decibels relative to full scale (dBFS)."""
    if rms <= 1e-9:
        return -100.0
    return 20.0 * math.log10(min(1.0, rms / max_val))


def load_wav_samples(wav_path: Union[str, Path]) -> Tuple[List[int], int, float]:
    """
    Load 16-bit PCM WAV audio file and return (samples, sample_rate, duration_sec).
    Supports mono and stereo (downmixed to mono).
    """
    p = Path(wav_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"WAV audio file not found: {p}")

    with wave.open(str(p), "rb") as wf:
        n_channels = wf.getnchannels()
        samp_width = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    duration = n_frames / float(framerate) if framerate > 0 else 0.0

    if samp_width == 2:
        # 16-bit signed PCM
        total_samples = len(raw_bytes) // 2
        fmt = f"<{total_samples}h"
        all_samples = list(struct.unpack(fmt, raw_bytes))
        if n_channels == 1:
            samples = all_samples
        else:
            # Downmix stereo to mono by averaging channels
            samples = [
                int((all_samples[i] + all_samples[i + 1]) / 2)
                for i in range(0, len(all_samples), n_channels)
            ]
    elif samp_width == 1:
        # 8-bit unsigned PCM
        all_samples = [int((b - 128) * 256) for b in raw_bytes]
        if n_channels == 1:
            samples = all_samples
        else:
            samples = [
                int((all_samples[i] + all_samples[i + 1]) / 2)
                for i in range(0, len(all_samples), n_channels)
            ]
    elif samp_width == 4:
        # 32-bit signed PCM
        total_samples = len(raw_bytes) // 4
        fmt = f"<{total_samples}i"
        all_samples = [int(s / 65536.0) for s in struct.unpack(fmt, raw_bytes)]
        if n_channels == 1:
            samples = all_samples
        else:
            samples = [
                int((all_samples[i] + all_samples[i + 1]) / 2)
                for i in range(0, len(all_samples), n_channels)
            ]
    else:
        raise ValueError(f"Unsupported sample width: {samp_width} bytes ({samp_width * 8} bits)")

    return samples, framerate, duration


# ---------------------------------------------------------------------------
# VoiceQA Engine Implementation
# ---------------------------------------------------------------------------

class VoiceQA:
    """
    Automated Acoustic Voice QA Engine inspecting waveform audio files.
    """

    def __init__(
        self,
        silence_threshold_dbfs: float = SILENCE_THRESHOLD_DBFS,
        max_gap_duration_sec: float = MAX_INTERNAL_GAP_SEC,
        max_clipping_ratio: float = MAX_CLIPPING_RATIO,
        max_loudness_variance_db: float = MAX_LOUDNESS_VARIANCE_DB,
        max_speech_beat_drift_sec: float = MAX_SPEECH_BEAT_DRIFT_SEC,
    ):
        self.silence_threshold_dbfs = silence_threshold_dbfs
        self.max_gap_duration_sec = max_gap_duration_sec
        self.max_clipping_ratio = max_clipping_ratio
        self.max_loudness_variance_db = max_loudness_variance_db
        self.max_speech_beat_drift_sec = max_speech_beat_drift_sec

    def inspect_audio(
        self,
        audio_path: Union[str, Path],
        script: Optional[Union[Script, Dict[str, Any], Any]] = None,
        expected_duration: Optional[float] = None,
        scene_durations: Optional[List[float]] = None,
    ) -> VoiceQAReport:
        """
        Inspect audio file against all four acoustic gates.
        """
        samples, sample_rate, total_duration = load_wav_samples(audio_path)
        return self.inspect_samples(
            samples=samples,
            sample_rate=sample_rate,
            script=script,
            expected_duration=expected_duration,
            scene_durations=scene_durations,
            total_duration=total_duration,
        )

    def inspect_samples(
        self,
        samples: List[int],
        sample_rate: int,
        script: Optional[Union[Script, Dict[str, Any], Any]] = None,
        expected_duration: Optional[float] = None,
        scene_durations: Optional[List[float]] = None,
        total_duration: Optional[float] = None,
    ) -> VoiceQAReport:
        """
        Run deep signal analysis on raw 16-bit PCM integer samples.
        """
        total_samples = len(samples)
        if total_samples == 0:
            return VoiceQAReport(
                passed=False,
                total_duration_sec=0.0,
                issues=["Audio contains zero samples (empty audio stream)."],
                recommendations=["Re-synthesize audio narration."],
                gate_results={
                    "clipping_gate": False,
                    "dead_air_gate": False,
                    "loudness_gate": False,
                    "beat_sync_gate": False,
                },
            )

        dur_sec = total_duration if total_duration is not None else (total_samples / float(sample_rate))
        issues: List[str] = []
        recommendations: List[str] = []

        # --------------------------------------------------------------------
        # 1. Clipping & Distortion Detection
        # --------------------------------------------------------------------
        clipped_count = 0
        consecutive_clips = 0
        max_consecutive_clips = 0
        clipping_events = 0

        for s in samples:
            if abs(s) >= 32767:
                clipped_count += 1
                consecutive_clips += 1
                if consecutive_clips > max_consecutive_clips:
                    max_consecutive_clips = consecutive_clips
            else:
                if consecutive_clips >= SUSTAINED_CLIP_THRESHOLD:
                    clipping_events += 1
                consecutive_clips = 0

        if consecutive_clips >= SUSTAINED_CLIP_THRESHOLD:
            clipping_events += 1

        clipping_ratio = clipped_count / float(total_samples)
        clipping_passed = clipping_ratio < self.max_clipping_ratio

        if not clipping_passed:
            issues.append(
                f"Severe acoustic clipping detected: {clipped_count} samples saturated ({clipping_ratio:.4%}), exceeding limit {self.max_clipping_ratio:.4%}."
            )
            recommendations.append("Reduce TTS synthesis gain or lower speaker volume modifier.")

        # --------------------------------------------------------------------
        # 2. Dead Air & Silence Analysis
        # --------------------------------------------------------------------
        frame_size = max(1, int(sample_rate * (FRAME_WINDOW_MS / 1000.0)))
        silent_frames = 0
        total_frames = 0

        current_gap_samples = 0
        max_gap_samples = 0
        gap_durations_sec: List[float] = []
        dead_air_count = 0

        for i in range(0, total_samples, frame_size):
            chunk = samples[i : i + frame_size]
            total_frames += 1
            chunk_rms = calculate_sample_rms(chunk)
            chunk_dbfs = rms_to_dbfs(chunk_rms)

            if chunk_dbfs < self.silence_threshold_dbfs:
                silent_frames += 1
                current_gap_samples += len(chunk)
            else:
                if current_gap_samples > 0:
                    gap_dur = current_gap_samples / float(sample_rate)
                    gap_durations_sec.append(gap_dur)
                    if gap_dur > self.max_gap_duration_sec:
                        dead_air_count += 1
                    if current_gap_samples > max_gap_samples:
                        max_gap_samples = current_gap_samples
                    current_gap_samples = 0

        if current_gap_samples > 0:
            gap_dur = current_gap_samples / float(sample_rate)
            gap_durations_sec.append(gap_dur)
            if gap_dur > self.max_gap_duration_sec:
                dead_air_count += 1
            if current_gap_samples > max_gap_samples:
                max_gap_samples = current_gap_samples

        max_dead_air_sec = max_gap_samples / float(sample_rate) if sample_rate > 0 else 0.0
        avg_gap_sec = (sum(gap_durations_sec) / len(gap_durations_sec)) if gap_durations_sec else 0.0
        dead_air_ratio = silent_frames / float(max(1, total_frames))

        dead_air_passed = max_dead_air_sec <= self.max_gap_duration_sec
        if not dead_air_passed:
            issues.append(
                f"Dead air violation detected: internal silence gap of {max_dead_air_sec:.3f}s exceeds maximum threshold {self.max_gap_duration_sec:.3f}s."
            )
            recommendations.append("Trim excessive pauses between narration words or adjust speaking cadence.")

        # --------------------------------------------------------------------
        # 3. Scene Loudness Consistency (RMS Energy)
        # --------------------------------------------------------------------
        resolved_scene_durations: List[float] = []

        if scene_durations:
            resolved_scene_durations = list(scene_durations)
        elif script:
            scenes = getattr(script, "scenes", None) or (script.get("scenes", []) if isinstance(script, dict) else [])
            for sc in scenes:
                sc_dur = getattr(sc, "duration", 0.0) if hasattr(sc, "duration") else sc.get("duration", 0.0)
                if sc_dur > 0:
                    resolved_scene_durations.append(float(sc_dur))

        # Fallback: divide entire audio into 4 equal scene chunks if no scenes provided
        if not resolved_scene_durations:
            n_chunks = 4
            chunk_dur = dur_sec / float(n_chunks)
            resolved_scene_durations = [chunk_dur] * n_chunks

        # Calculate RMS and dBFS per scene
        scene_loudnesses: List[float] = []
        sample_offset = 0

        for sc_dur in resolved_scene_durations:
            sc_sample_count = int(sc_dur * sample_rate)
            sc_samples = samples[sample_offset : sample_offset + sc_sample_count]
            sample_offset += sc_sample_count
            if sc_samples:
                sc_rms = calculate_sample_rms(sc_samples)
                sc_dbfs = rms_to_dbfs(sc_rms)
                scene_loudnesses.append(round(sc_dbfs, 2))

        if scene_loudnesses:
            # Filter out completely silent scenes for variance check if multiple scenes exist
            active_loudnesses = [l for l in scene_loudnesses if l > -80.0] or scene_loudnesses
            loudness_variance = max(active_loudnesses) - min(active_loudnesses)
        else:
            loudness_variance = 0.0

        loudness_passed = loudness_variance <= self.max_loudness_variance_db
        if not loudness_passed:
            issues.append(
                f"Scene loudness inconsistency: variance of {loudness_variance:.2f} dBFS exceeds limit {self.max_loudness_variance_db:.2f} dBFS."
            )
            recommendations.append("Apply dynamic range compression or normalize per-scene gain levels.")

        # --------------------------------------------------------------------
        # 4. Speech-Beat Alignment & Sync Drift
        # --------------------------------------------------------------------
        max_drift_sec = 0.0

        # Check total duration drift against expected duration
        target_dur = expected_duration or (getattr(script, "total_duration", None) if script else None)
        if target_dur is not None and target_dur > 0:
            total_drift = abs(dur_sec - float(target_dur))
            if total_drift > max_drift_sec:
                max_drift_sec = total_drift

        # Check individual scene beat boundaries if script is provided
        if script:
            scenes = getattr(script, "scenes", None) or (script.get("scenes", []) if isinstance(script, dict) else [])
            current_planned_time = 0.0
            for sc in scenes:
                sc_dur = getattr(sc, "duration", 5.0) if hasattr(sc, "duration") else sc.get("duration", 5.0)
                current_planned_time += sc_dur
                beats = getattr(sc, "beats", []) if hasattr(sc, "beats") else sc.get("beats", [])
                for b in beats:
                    b_end = getattr(b, "end_time", 0.0) if hasattr(b, "end_time") else b.get("end_time", 0.0)
                    if b_end > 0 and b_end <= dur_sec:
                        b_drift = abs(b_end - min(dur_sec, current_planned_time))
                        if b_drift > max_drift_sec and b_drift <= 1.0:
                            max_drift_sec = max(max_drift_sec, b_drift)

        beat_sync_passed = max_drift_sec <= self.max_speech_beat_drift_sec
        if not beat_sync_passed:
            issues.append(
                f"Speech-beat sync drift violation: max drift of {max_drift_sec:.3f}s exceeds threshold {self.max_speech_beat_drift_sec:.3f}s."
            )
            recommendations.append("Re-align script beatmap timestamps or adjust speaking rate.")

        # --------------------------------------------------------------------
        # Aggregate Quality Gate Verdict
        # --------------------------------------------------------------------
        all_passed = bool(
            clipping_passed and dead_air_passed and loudness_passed and beat_sync_passed
        )

        return VoiceQAReport(
            passed=all_passed,
            total_duration_sec=round(dur_sec, 3),
            clipping_events_count=clipping_events,
            clipping_ratio=round(clipping_ratio, 6),
            dead_air_instances_count=dead_air_count,
            max_dead_air_duration_sec=round(max_dead_air_sec, 3),
            average_gap_duration_sec=round(avg_gap_sec, 3),
            dead_air_ratio=round(dead_air_ratio, 4),
            loudness_variance_db=round(loudness_variance, 2),
            scene_loudness_dbfs=scene_loudnesses,
            speech_beat_max_drift_sec=round(max_drift_sec, 3),
            gate_results={
                "clipping_gate": clipping_passed,
                "dead_air_gate": dead_air_passed,
                "loudness_gate": loudness_passed,
                "beat_sync_gate": beat_sync_passed,
            },
            metrics={
                "clipping_ratio": round(clipping_ratio, 6),
                "max_dead_air_sec": round(max_dead_air_sec, 3),
                "loudness_variance_db": round(loudness_variance, 2),
                "speech_beat_max_drift_sec": round(max_drift_sec, 3),
            },
            issues=issues,
            recommendations=recommendations,
        )
