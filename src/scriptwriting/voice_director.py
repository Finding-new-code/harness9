"""
src.scriptwriting.voice_director — Multi-Provider Voice Director & Audio Orchestrator (Milestone M4).

Features:
1. Multi-provider VoiceDirector routing:
   - ElevenLabs API v2 (Cloud TTS with voice stability & similarity boost)
   - OpenAI Audio API (Cloud TTS tts-1 / tts-1-hd models)
   - Windows SAPI (Native offline speech synthesis via PowerShell / System.Speech)
   - Harmonic WAV Synthesizer (100% deterministic pure-Python formant synthesis)
2. Character Casting & Voice Profile mapping:
   - Maps speaker roles (narrator, host, expert, historian, interviewer) to distinct voices, pitches, and rates.
3. Emotional Tone Modulation:
   - Parses script emotional tags ([tense], [authoritative], [curious], [triumphant], [reflective], [urgent], [calm])
   - Adjusts acoustic synthesis parameters (pitch, rate, stability, volume, SSML).
4. Dynamic WPM Rate Control:
   - Standard range: 130 to 160 WPM (default 145 WPM).
   - Bounds clamping: clamped between 90 and 220 WPM for extreme requests.
   - Conforms audio timing to scene and beat constraints.
"""

import json
import logging
import math
import os
import re
import struct
import subprocess
import time
import urllib.error
import urllib.request
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.config import DEFAULT_AUDIO_SAMPLE_RATE, get_env_var
from src.models.contracts import H9BaseModel, Script, ScriptBeat, ScriptScene
from src.utils.filesystem import atomic_write, ensure_dir

logger = logging.getLogger("harness9.scriptwriting.voice_director")

# ---------------------------------------------------------------------------
# Tone & Emotion Modulation Profiles
# ---------------------------------------------------------------------------

EMOTION_PATTERNS = re.compile(
    r"\[(tense|authoritative|curious|triumphant|reflective|urgent|calm|enthusiastic|whispering|somber|dramatic|inquisitive)\]",
    re.IGNORECASE,
)

EMOTION_MODIFIERS: Dict[str, Dict[str, float]] = {
    "tense": {
        "pitch_mult": 1.10,
        "rate_mult": 1.12,
        "stability": 0.35,
        "similarity_boost": 0.85,
        "volume_mult": 1.05,
    },
    "authoritative": {
        "pitch_mult": 0.90,
        "rate_mult": 0.95,
        "stability": 0.75,
        "similarity_boost": 0.80,
        "volume_mult": 1.10,
    },
    "curious": {
        "pitch_mult": 1.05,
        "rate_mult": 1.02,
        "stability": 0.50,
        "similarity_boost": 0.70,
        "volume_mult": 1.00,
    },
    "triumphant": {
        "pitch_mult": 1.08,
        "rate_mult": 1.06,
        "stability": 0.60,
        "similarity_boost": 0.80,
        "volume_mult": 1.15,
    },
    "reflective": {
        "pitch_mult": 0.92,
        "rate_mult": 0.88,
        "stability": 0.70,
        "similarity_boost": 0.75,
        "volume_mult": 0.90,
    },
    "urgent": {
        "pitch_mult": 1.12,
        "rate_mult": 1.20,
        "stability": 0.40,
        "similarity_boost": 0.85,
        "volume_mult": 1.10,
    },
    "calm": {
        "pitch_mult": 0.98,
        "rate_mult": 0.92,
        "stability": 0.80,
        "similarity_boost": 0.75,
        "volume_mult": 0.95,
    },
    "enthusiastic": {
        "pitch_mult": 1.10,
        "rate_mult": 1.10,
        "stability": 0.50,
        "similarity_boost": 0.80,
        "volume_mult": 1.10,
    },
    "whispering": {
        "pitch_mult": 0.95,
        "rate_mult": 0.85,
        "stability": 0.60,
        "similarity_boost": 0.60,
        "volume_mult": 0.65,
    },
    "somber": {
        "pitch_mult": 0.88,
        "rate_mult": 0.82,
        "stability": 0.75,
        "similarity_boost": 0.80,
        "volume_mult": 0.85,
    },
    "dramatic": {
        "pitch_mult": 0.95,
        "rate_mult": 0.90,
        "stability": 0.65,
        "similarity_boost": 0.85,
        "volume_mult": 1.15,
    },
    "inquisitive": {
        "pitch_mult": 1.06,
        "rate_mult": 1.00,
        "stability": 0.55,
        "similarity_boost": 0.70,
        "volume_mult": 1.00,
    },
}


def strip_emotion_tags(text: str) -> Tuple[str, Optional[str]]:
    """
    Extract first emotional marker from text and return clean spoken text.
    
    Example:
        "[tense] The reactor core temperature began to rise rapidly."
        -> ("The reactor core temperature began to rise rapidly.", "tense")
    """
    if not text:
        return "", None
    match = EMOTION_PATTERNS.search(text)
    emotion = match.group(1).lower() if match else None
    cleaned_text = EMOTION_PATTERNS.sub("", text).strip()
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    return cleaned_text, emotion


def clamp_wpm(requested_wpm: float, min_wpm: float = 90.0, max_wpm: float = 220.0) -> float:
    """Clamp requested words per minute within strict production bounds [90, 220]."""
    return min(max(float(requested_wpm), min_wpm), max_wpm)


# ---------------------------------------------------------------------------
# Voice Profile Data Model
# ---------------------------------------------------------------------------

class VoiceProfile(H9BaseModel):
    """Configuration for a specific character voice in the VoiceDirector."""
    voice_id: str = "af_nova"
    provider: str = "harmonic"  # elevenlabs, openai, sapi, harmonic
    display_name: str = "Nova"
    character_name: str = "narrator"
    gender: str = "neutral"  # male, female, neutral
    pitch_adjustment: float = 0.0  # Semitones or normalized delta [-1.0, 1.0]
    speaking_rate_wpm: int = 145  # Standard: 130 - 160 WPM
    stability: float = 0.50
    similarity_boost: float = 0.75
    style: float = 0.00
    model: Optional[str] = None
    extra_settings: Dict[str, Any] = field(default_factory=dict)  # type: ignore

    def get_effective_wpm(self) -> int:
        """Return WPM clamped within bounds [90, 220]."""
        return int(clamp_wpm(self.speaking_rate_wpm))


@dataclass
class AudioNarration:
    """Technical metadata for synthesized narration output."""
    audio_path: str
    duration_seconds: float
    sample_rate: int = 44100
    channels: int = 1
    sample_width_bytes: int = 2
    file_size_bytes: int = 0
    provider_used: str = "harmonic"
    voice_id: str = "af_nova"
    wpm: float = 145.0
    scene_audio_segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audio_path": self.audio_path,
            "duration_seconds": round(self.duration_seconds, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width_bytes": self.sample_width_bytes,
            "file_size_bytes": self.file_size_bytes,
            "provider_used": self.provider_used,
            "voice_id": self.voice_id,
            "wpm": round(self.wpm, 1),
            "scene_audio_segments": self.scene_audio_segments,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# TTS Provider Abstract Interface & Implementations
# ---------------------------------------------------------------------------

class BaseDirectorTTSProvider(ABC):
    """Abstract Base Class for Director TTS Providers."""

    provider_id: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available in current environment."""
        pass

    @abstractmethod
    def synthesize_speech(
        self,
        text: str,
        output_path: Union[str, Path],
        voice_profile: VoiceProfile,
        target_duration: Optional[float] = None,
        emotion: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioNarration:
        """Synthesize text into WAV audio file."""
        pass


class ElevenLabsProvider(BaseDirectorTTSProvider):
    """ElevenLabs Cloud TTS integration."""
    provider_id = "elevenlabs"
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_env_var("ELEVENLABS_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def synthesize_speech(
        self,
        text: str,
        output_path: Union[str, Path],
        voice_profile: VoiceProfile,
        target_duration: Optional[float] = None,
        emotion: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioNarration:
        if not self.is_available():
            raise RuntimeError("ElevenLabs API key is missing or invalid.")

        clean_text, detected_emotion = strip_emotion_tags(text)
        eff_emotion = emotion or detected_emotion

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        voice_id = voice_profile.voice_id if voice_profile.voice_id and len(voice_profile.voice_id) > 5 else self.DEFAULT_VOICE_ID
        stability = voice_profile.stability
        similarity_boost = voice_profile.similarity_boost

        if eff_emotion and eff_emotion in EMOTION_MODIFIERS:
            mods = EMOTION_MODIFIERS[eff_emotion]
            stability = mods.get("stability", stability)
            similarity_boost = mods.get("similarity_boost", similarity_boost)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        payload = {
            "text": clean_text,
            "model_id": voice_profile.model or "eleven_monolingual_v1",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": voice_profile.style,
            },
        }

        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key.strip(),  # type: ignore
            "User-Agent": "Harness9-VoiceDirector/1.0",
        }

        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                audio_bytes = resp.read()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"ElevenLabs API HTTP {e.code}: {err_body}")
        except Exception as e:
            raise RuntimeError(f"ElevenLabs request failed: {e}")

        with open(out_file, "wb") as f:
            f.write(audio_bytes)

        words = len(clean_text.split())
        wpm = voice_profile.get_effective_wpm()
        estimated_duration = target_duration or max(1.0, (words / wpm) * 60.0)

        return AudioNarration(
            audio_path=str(out_file),
            duration_seconds=estimated_duration,
            sample_rate=44100,
            channels=1,
            sample_width_bytes=2,
            file_size_bytes=len(audio_bytes),
            provider_used="elevenlabs",
            voice_id=voice_id,
            wpm=float(wpm),
            metadata={"emotion": eff_emotion, "model": voice_profile.model},
        )


class OpenAIAudioProvider(BaseDirectorTTSProvider):
    """OpenAI Audio TTS integration (tts-1, tts-1-hd)."""
    provider_id = "openai"
    DEFAULT_VOICE = "alloy"
    DEFAULT_MODEL = "tts-1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_env_var("OPENAI_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def synthesize_speech(
        self,
        text: str,
        output_path: Union[str, Path],
        voice_profile: VoiceProfile,
        target_duration: Optional[float] = None,
        emotion: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioNarration:
        if not self.is_available():
            raise RuntimeError("OpenAI API key is missing or invalid.")

        clean_text, detected_emotion = strip_emotion_tags(text)
        eff_emotion = emotion or detected_emotion

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        voice = voice_profile.voice_id.lower() if voice_profile.voice_id in [
            "alloy", "echo", "fable", "onyx", "nova", "shimmer"
        ] else self.DEFAULT_VOICE

        model = voice_profile.model or self.DEFAULT_MODEL
        speed = clamp_wpm(voice_profile.speaking_rate_wpm) / 145.0
        speed = min(max(speed, 0.25), 4.0)

        if eff_emotion and eff_emotion in EMOTION_MODIFIERS:
            speed *= EMOTION_MODIFIERS[eff_emotion].get("rate_mult", 1.0)
            speed = min(max(speed, 0.25), 4.0)

        url = "https://api.openai.com/v1/audio/speech"
        payload = {
            "model": model,
            "input": clean_text,
            "voice": voice,
            "response_format": "wav" if out_file.suffix.lower() == ".wav" else "mp3",
            "speed": round(speed, 2),
        }

        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",  # type: ignore
            "Content-Type": "application/json",
            "User-Agent": "Harness9-VoiceDirector/1.0",
        }

        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                audio_bytes = resp.read()
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS synthesis failed: {e}")

        with open(out_file, "wb") as f:
            f.write(audio_bytes)

        words = len(clean_text.split())
        wpm = voice_profile.get_effective_wpm()
        dur = target_duration or max(1.0, (words / (wpm * (speed / (wpm / 145.0)))) * 60.0)

        return AudioNarration(
            audio_path=str(out_file),
            duration_seconds=dur,
            sample_rate=24000,
            channels=1,
            sample_width_bytes=2,
            file_size_bytes=len(audio_bytes),
            provider_used="openai",
            voice_id=voice,
            wpm=float(wpm),
            metadata={"emotion": eff_emotion, "model": model, "speed": speed},
        )


class WindowsSAPIProvider(BaseDirectorTTSProvider):
    """Windows System.Speech.Synthesis offline TTS."""
    provider_id = "sapi"

    def is_available(self) -> bool:
        if os.name != "nt":
            return False
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Write-Output 'ok'"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return "ok" in res.stdout.strip().lower()
        except Exception:
            return False

    def synthesize_speech(
        self,
        text: str,
        output_path: Union[str, Path],
        voice_profile: VoiceProfile,
        target_duration: Optional[float] = None,
        emotion: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioNarration:
        if not self.is_available():
            raise RuntimeError("Windows SAPI is not available on this system.")

        clean_text, detected_emotion = strip_emotion_tags(text)
        eff_emotion = emotion or detected_emotion

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        wpm = voice_profile.get_effective_wpm()
        # Convert WPM [90-220] to SAPI Rate [-10 to 10]
        # 145 WPM -> 0
        rate_val = int(round((wpm - 145.0) / 10.0))
        rate_val = min(max(rate_val, -10), 10)

        volume_val = 100
        if eff_emotion and eff_emotion in EMOTION_MODIFIERS:
            mods = EMOTION_MODIFIERS[eff_emotion]
            rate_val = int(round(rate_val * mods.get("rate_mult", 1.0)))
            volume_val = int(min(max(volume_val * mods.get("volume_mult", 1.0), 20), 100))

        clean_ps_text = clean_text.replace("'", "''").replace('"', '`"').replace("\n", " ")
        out_wav_str = str(out_file).replace("'", "''")

        ps_script = f"""
Add-Type -AssemblyName System.Speech;
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
$synth.Rate = {rate_val};
$synth.Volume = {volume_val};
"""
        if voice_profile.voice_id and voice_profile.voice_id not in ["default", "af_nova"]:
            v_name = voice_profile.voice_id.replace("'", "''")
            ps_script += f"""
try {{ $synth.SelectVoice('{v_name}'); }} catch {{}}
"""

        ps_script += f"""
$synth.SetOutputToWaveFile('{out_wav_str}');
$synth.Speak('{clean_ps_text}');
$synth.Dispose();
"""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if res.returncode != 0:
                raise RuntimeError(f"PowerShell SAPI returned {res.returncode}: {res.stderr.strip()}")
        except Exception as e:
            raise RuntimeError(f"Windows SAPI generation failed: {e}")

        if not out_file.exists() or out_file.stat().st_size < 100:
            raise RuntimeError(f"SAPI WAV was not created: {out_file}")

        try:
            with wave.open(str(out_file), "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                frames = wf.getnframes()
                actual_duration = frames / float(sample_rate) if sample_rate > 0 else 1.0
        except Exception:
            actual_duration = target_duration or (len(clean_text.split()) / (wpm / 60.0))
            channels = 1
            sample_width = 2
            sample_rate = 22050

        return AudioNarration(
            audio_path=str(out_file),
            duration_seconds=actual_duration,
            sample_rate=sample_rate,
            channels=channels,
            sample_width_bytes=sample_width,
            file_size_bytes=out_file.stat().st_size,
            provider_used="sapi",
            voice_id=voice_profile.voice_id,
            wpm=float(wpm),
            metadata={"emotion": eff_emotion, "rate_val": rate_val, "volume_val": volume_val},
        )


class HarmonicWAVSynthProvider(BaseDirectorTTSProvider):
    """
    Pure Python Modulated Harmonic Wave Synthesizer (100% Offline & Deterministic).
    Generates 16-bit PCM WAV audio with pitch, formant resonance, and cadence envelopes.
    """
    provider_id = "harmonic"

    def is_available(self) -> bool:
        return True

    def synthesize_speech(
        self,
        text: str,
        output_path: Union[str, Path],
        voice_profile: VoiceProfile,
        target_duration: Optional[float] = None,
        emotion: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioNarration:
        clean_text, detected_emotion = strip_emotion_tags(text)
        eff_emotion = emotion or detected_emotion

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        sample_rate = int(kwargs.get("sample_rate", DEFAULT_AUDIO_SAMPLE_RATE))
        words = clean_text.split()
        num_words = max(1, len(words))

        wpm = voice_profile.get_effective_wpm()
        # Compute baseline duration from WPM
        wpm_duration = (num_words / wpm) * 60.0

        if target_duration is not None and target_duration > 0:
            total_duration = float(target_duration)
        else:
            total_duration = max(1.5, wpm_duration)

        # Base pitch selection by gender / profile
        gender = voice_profile.gender.lower()
        if gender == "female" or "female" in voice_profile.voice_id.lower() or "nova" in voice_profile.voice_id.lower():
            base_f0 = 220.0  # A3 (Female speaking pitch)
        elif gender == "male" or "male" in voice_profile.voice_id.lower() or "deep" in voice_profile.voice_id.lower():
            base_f0 = 120.0  # B2 (Deep male pitch)
        else:
            base_f0 = 160.0  # E3 (Neutral narrative pitch)

        # Pitch adjustment
        base_f0 *= (1.0 + max(-0.5, min(0.5, voice_profile.pitch_adjustment)))

        # Emotion modulation
        amplitude_scale = 12000.0
        pause_ratio = 0.15
        if eff_emotion and eff_emotion in EMOTION_MODIFIERS:
            mods = EMOTION_MODIFIERS[eff_emotion]
            base_f0 *= mods.get("pitch_mult", 1.0)
            amplitude_scale *= mods.get("volume_mult", 1.0)

        total_samples = int(total_duration * sample_rate)
        active_time = total_duration * (1.0 - pause_ratio)
        word_dur = active_time / float(num_words)
        pause_dur = (total_duration * pause_ratio) / float(num_words)

        formants = [
            (base_f0 * 1.0, 0.40),
            (base_f0 * 2.0, 0.25),
            (base_f0 * 3.5, 0.15),
            (base_f0 * 5.0, 0.10),
            (base_f0 * 8.0, 0.05),
        ]

        cycle_length = max(10, int(sample_rate / max(50.0, base_f0)))
        base_cycle = []
        for i in range(cycle_length):
            val = 0.0
            for freq_mult, amp_weight in formants:
                val += amp_weight * math.sin(2.0 * math.pi * (freq_mult / base_f0) * (i / cycle_length))
            base_cycle.append(val)

        frames = bytearray()
        sample_idx = 0

        for w_idx, word in enumerate(words):
            word_samples = int(word_dur * sample_rate)
            pause_samples = int(pause_dur * sample_rate)
            if word.endswith((".", "!", "?", ":", ";")):
                pause_samples = int(pause_samples * 2.0)

            attack_len = int(word_samples * 0.15)
            decay_len = int(word_samples * 0.15)

            for s in range(word_samples):
                if sample_idx >= total_samples:
                    break
                if s < attack_len and attack_len > 0:
                    env = 0.5 * (1.0 - math.cos(math.pi * (s / attack_len)))
                elif s >= (word_samples - decay_len) and decay_len > 0:
                    rem = word_samples - s
                    env = 0.5 * (1.0 - math.cos(math.pi * (rem / decay_len)))
                else:
                    env = 1.0

                cycle_val = base_cycle[s % cycle_length]
                final_val = int(cycle_val * amplitude_scale * env)
                clamped_val = max(-32767, min(32767, final_val))
                frames.extend(struct.pack("<h", clamped_val))
                sample_idx += 1

            for s in range(pause_samples):
                if sample_idx >= total_samples:
                    break
                frames.extend(struct.pack("<h", 0))
                sample_idx += 1

        while sample_idx < total_samples:
            frames.extend(struct.pack("<h", 0))
            sample_idx += 1

        with wave.open(str(out_file), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(frames)

        return AudioNarration(
            audio_path=str(out_file),
            duration_seconds=total_duration,
            sample_rate=sample_rate,
            channels=1,
            sample_width_bytes=2,
            file_size_bytes=out_file.stat().st_size,
            provider_used="harmonic",
            voice_id=voice_profile.voice_id,
            wpm=float(wpm),
            metadata={"emotion": eff_emotion, "base_f0": base_f0},
        )


# ---------------------------------------------------------------------------
# VoiceDirector Master Engine
# ---------------------------------------------------------------------------

class VoiceDirector:
    """
    Master Audio Director orchestrating character casting, emotion modulation,
    dynamic WPM pacing, and multi-provider audio synthesis.
    """

    DEFAULT_PROFILES: Dict[str, VoiceProfile] = {
        "narrator": VoiceProfile(
            voice_id="af_nova",
            provider="harmonic",
            display_name="Nova Narrator",
            character_name="narrator",
            gender="female",
            speaking_rate_wpm=145,
            pitch_adjustment=0.0,
        ),
        "expert": VoiceProfile(
            voice_id="deep_expert",
            provider="harmonic",
            display_name="Dr. Vance",
            character_name="expert",
            gender="male",
            speaking_rate_wpm=135,
            pitch_adjustment=-0.1,
        ),
        "host": VoiceProfile(
            voice_id="upbeat_host",
            provider="harmonic",
            display_name="Alex Host",
            character_name="host",
            gender="neutral",
            speaking_rate_wpm=155,
            pitch_adjustment=0.05,
        ),
        "historian": VoiceProfile(
            voice_id="calm_historian",
            provider="harmonic",
            display_name="Historian Sage",
            character_name="historian",
            gender="neutral",
            speaking_rate_wpm=130,
            pitch_adjustment=-0.05,
        ),
        "interviewer": VoiceProfile(
            voice_id="interviewer_curious",
            provider="harmonic",
            display_name="Sam Interviewer",
            character_name="interviewer",
            gender="female",
            speaking_rate_wpm=150,
            pitch_adjustment=0.02,
        ),
    }

    def __init__(
        self,
        default_voice_profile: Optional[VoiceProfile] = None,
        elevenlabs_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        preferred_provider: Optional[str] = None,
    ):
        self.providers: Dict[str, BaseDirectorTTSProvider] = {
            "elevenlabs": ElevenLabsProvider(api_key=elevenlabs_api_key),
            "openai": OpenAIAudioProvider(api_key=openai_api_key),
            "sapi": WindowsSAPIProvider(),
            "harmonic": HarmonicWAVSynthProvider(),
        }
        self.cast_map: Dict[str, VoiceProfile] = dict(self.DEFAULT_PROFILES)
        self.default_profile = default_voice_profile or self.cast_map["narrator"]
        self.preferred_provider = preferred_provider

    def register_character(self, character_role: str, profile: VoiceProfile) -> None:
        """Register or override a character voice profile."""
        self.cast_map[character_role.lower()] = profile

    def get_character_profile(self, character_role: Optional[str] = None) -> VoiceProfile:
        """Retrieve voice profile for character role with fallback to default."""
        if character_role and character_role.lower() in self.cast_map:
            return self.cast_map[character_role.lower()]
        return self.default_profile

    def synthesize_text(
        self,
        text: str,
        output_path: Union[str, Path],
        voice_profile: Optional[VoiceProfile] = None,
        target_duration: Optional[float] = None,
        emotion: Optional[str] = None,
        provider_name: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioNarration:
        """
        Synthesize text to audio using specified or fallback provider chain.
        Fallback order: Requested/Preferred -> ElevenLabs -> OpenAI -> Windows SAPI -> Harmonic Synthesizer.
        """
        profile = voice_profile or self.default_profile
        target_file = Path(output_path).resolve()
        target_file.parent.mkdir(parents=True, exist_ok=True)

        req_prov = provider_name or self.preferred_provider or profile.provider
        if req_prov in self.providers and self.providers[req_prov].is_available():
            try:
                return self.providers[req_prov].synthesize_speech(
                    text=text,
                    output_path=target_file,
                    voice_profile=profile,
                    target_duration=target_duration,
                    emotion=emotion,
                    **kwargs,
                )
            except Exception as e:
                logger.warning(f"Preferred TTS provider '{req_prov}' failed: {e}. Falling back.")

        # Standard Fallback Chain
        fallback_order = ["elevenlabs", "openai", "harmonic", "sapi"]
        for p_id in fallback_order:
            prov = self.providers[p_id]
            if prov.is_available():
                try:
                    return prov.synthesize_speech(
                        text=text,
                        output_path=target_file,
                        voice_profile=profile,
                        target_duration=target_duration,
                        emotion=emotion,
                        **kwargs,
                    )
                except Exception as e:
                    logger.debug(f"Provider '{p_id}' failed: {e}")
                    continue

        # Guaranteed pure-python fallback
        return self.providers["harmonic"].synthesize_speech(
            text=text,
            output_path=target_file,
            voice_profile=profile,
            target_duration=target_duration,
            emotion=emotion,
            **kwargs,
        )

    def synthesize_narration(
        self,
        script: Union[Script, Dict[str, Any], str],
        voice_profile: Optional[VoiceProfile] = None,
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> AudioNarration:
        """
        Director-level narration synthesis of a full Script or text transcript.
        Generates master narration WAV along with scene-level audio tracking.
        """
        target_dir = Path(output_dir or "output").resolve()
        audio_dir = target_dir / "assets" / "audio" if not str(target_dir).endswith("audio") else target_dir
        audio_dir.mkdir(parents=True, exist_ok=True)
        master_audio_path = audio_dir / "narration.wav"

        profile = voice_profile or self.default_profile
        scene_segments: List[Dict[str, Any]] = []

        # Handle simple string input
        if isinstance(script, str):
            clean_text, detected_emotion = strip_emotion_tags(script)
            target_duration = kwargs.get("target_duration")
            return self.synthesize_text(
                text=clean_text,
                output_path=master_audio_path,
                voice_profile=profile,
                target_duration=target_duration,
                emotion=detected_emotion or kwargs.get("emotion"),
                **kwargs,
            )

        # Handle Script model or dict
        if isinstance(script, dict):
            script_data = script
            scenes = script_data.get("scenes", [])
            full_transcript = script_data.get("full_transcript", "")
            target_duration = script_data.get("total_duration")
        else:
            scenes = getattr(script, "scenes", [])
            full_transcript = getattr(script, "full_transcript", "")
            target_duration = getattr(script, "total_duration", None)

        if not full_transcript and scenes:
            full_transcript = " ".join(
                getattr(s, "narration_text", "") if hasattr(s, "narration_text") else s.get("narration_text", "")
                for s in scenes
            )

        clean_full_text, overall_emotion = strip_emotion_tags(full_transcript)

        # Synthesize full master audio
        master_audio = self.synthesize_text(
            text=clean_full_text,
            output_path=master_audio_path,
            voice_profile=profile,
            target_duration=target_duration,
            emotion=overall_emotion or kwargs.get("emotion"),
            **kwargs,
        )

        # Compute scene audio boundaries
        total_audio_dur = master_audio.duration_seconds
        total_script_dur = sum(
            getattr(s, "duration", 5.0) if hasattr(s, "duration") else s.get("duration", 5.0) for s in scenes
        ) or total_audio_dur

        current_offset = 0.0
        for idx, scene in enumerate(scenes):
            scene_id = getattr(scene, "scene_id", f"scene_{idx+1}") if hasattr(scene, "scene_id") else scene.get("scene_id", f"scene_{idx+1}")
            scene_dur = getattr(scene, "duration", 5.0) if hasattr(scene, "duration") else scene.get("duration", 5.0)
            
            # Proportionally scale scene duration to actual audio duration
            scaled_dur = (scene_dur / total_script_dur) * total_audio_dur if total_script_dur > 0 else (total_audio_dur / max(1, len(scenes)))
            
            scene_text = getattr(scene, "narration_text", "") if hasattr(scene, "narration_text") else scene.get("narration_text", "")
            _, s_emotion = strip_emotion_tags(scene_text)

            scene_segments.append({
                "scene_id": scene_id,
                "start_time": round(current_offset, 3),
                "end_time": round(current_offset + scaled_dur, 3),
                "duration": round(scaled_dur, 3),
                "emotion": s_emotion or overall_emotion,
            })
            current_offset += scaled_dur

        master_audio.scene_audio_segments = scene_segments
        return master_audio
