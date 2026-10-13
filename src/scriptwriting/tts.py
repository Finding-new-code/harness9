"""
src.scriptwriting.tts — Multi-Provider Text-to-Speech (TTS) Engine.

Supports:
1. ElevenLabs API Adapter (when ELEVENLABS_API_KEY is available)
2. Windows SAPI Voice Synthesizer (System.Speech.Synthesis via PowerShell on Windows)
3. Pure Python Modulated Harmonic WAV Synthesizer (100% deterministic fallback)

Outputs valid 16-bit PCM WAV (e.g. assets/audio/narration.wav) or MP3 with accurate duration.
"""

import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.config import DEFAULT_AUDIO_SAMPLE_RATE, get_env_var
from src.utils.filesystem import atomic_write, ensure_dir


@dataclass
class AudioMetadata:
    """Technical metadata for synthesized audio narration."""
    file_path: str
    duration_seconds: float
    sample_rate: int
    channels: int = 1
    sample_width_bytes: int = 2
    file_size_bytes: int = 0
    provider_used: str = "harmonic_synthesizer"
    format: str = "wav"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "duration_seconds": round(self.duration_seconds, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width_bytes": self.sample_width_bytes,
            "file_size_bytes": self.file_size_bytes,
            "provider_used": self.provider_used,
            "format": self.format,
        }


def fit_audio_duration(
    metadata: AudioMetadata,
    target_duration: float,
    *,
    max_speedup: float = 1.05,
) -> AudioMetadata:
    """Gently time-compress a WAV that barely exceeds its target.

    The narration remains complete; small provider timing overruns are handled
    with FFmpeg's pitch-preserving ``atempo`` filter. Larger overruns are left
    untouched so the pipeline's duration gate can reject them.
    """
    target = float(target_duration)
    if target <= 0 or metadata.duration_seconds <= target + 0.01:
        return metadata
    if metadata.format.lower() != "wav" or metadata.sample_width_bytes != 2:
        return metadata

    safety_margin = min(0.05, target * 0.005)
    adjusted_target = target - safety_margin
    speedup = metadata.duration_seconds / adjusted_target
    if speedup > max_speedup:
        return metadata

    ffmpeg = shutil.which("ffmpeg")
    audio_path = Path(metadata.file_path).resolve()
    if not ffmpeg or not audio_path.is_file():
        return metadata

    with tempfile.TemporaryDirectory(prefix="h9-audio-fit-", dir=str(audio_path.parent)) as temp_dir:
        fitted_path = Path(temp_dir) / audio_path.name
        try:
            subprocess.run(
                [
                    ffmpeg,
                    "-nostdin",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(audio_path),
                    "-filter:a",
                    f"atempo={speedup:.8f}",
                    "-ac",
                    str(metadata.channels),
                    "-ar",
                    str(metadata.sample_rate),
                    "-c:a",
                    "pcm_s16le",
                    str(fitted_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            with wave.open(str(fitted_path), "rb") as fitted_wav:
                sample_rate = fitted_wav.getframerate()
                frames = fitted_wav.getnframes()
                channels = fitted_wav.getnchannels()
                sample_width = fitted_wav.getsampwidth()
                if sample_rate <= 0 or frames <= 0 or sample_width != 2:
                    raise ValueError("FFmpeg produced an invalid narration WAV")
                actual_duration = frames / float(sample_rate)
                if actual_duration > target + 0.01:
                    raise ValueError(
                        f"FFmpeg narration remains over target ({actual_duration:.3f}s > {target:.3f}s)"
                    )
            os.replace(fitted_path, audio_path)
        except (OSError, ValueError, wave.Error, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"Could not fit narration WAV to its target duration: {exc}") from exc

    return AudioMetadata(
        file_path=str(audio_path),
        duration_seconds=actual_duration,
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bytes=sample_width,
        file_size_bytes=audio_path.stat().st_size,
        provider_used=metadata.provider_used,
        format="wav",
    )


class TTSProvider(ABC):
    """Abstract Base Class for TTS Providers."""

    name: str = "base_tts"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available in the current environment."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_path: Union[str, Path],
        target_duration: Optional[float] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioMetadata:
        """Synthesize text to audio and return metadata."""
        pass


class ElevenLabsTTSProvider(TTSProvider):
    """
    Cloud TTS Provider utilizing ElevenLabs API.
    """
    name = "elevenlabs"
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    DEFAULT_MODEL_ID = "eleven_monolingual_v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_env_var("ELEVENLABS_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def synthesize(
        self,
        text: str,
        output_path: Union[str, Path],
        target_duration: Optional[float] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioMetadata:
        if not self.is_available():
            raise RuntimeError("ElevenLabs API key is missing or invalid.")

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        voice_id = (
            voice
            if voice and voice.lower() not in {"default", "af_nova"}
            else self.DEFAULT_VOICE_ID
        )

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        payload = {
            "text": text,
            "model_id": kwargs.get("model_id", self.DEFAULT_MODEL_ID),
            "voice_settings": {
                "stability": kwargs.get("stability", 0.5),
                "similarity_boost": kwargs.get("similarity_boost", 0.75),
            }
        }

        import json
        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key.strip(),
            "User-Agent": "Harness9-VideoEngine/1.0",
        }

        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                audio_bytes = resp.read()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"ElevenLabs API HTTP error {e.code}: {err_body}")
        except Exception as e:
            raise RuntimeError(f"ElevenLabs API request failed: {e}")

        if len(audio_bytes) < 100:
            raise ValueError("ElevenLabs returned empty or invalid audio payload.")

        if out_file.suffix.lower() == ".wav":
            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                raise RuntimeError("ElevenLabs returned MP3 audio, but FFmpeg is required to create the WAV narration track.")
            with tempfile.TemporaryDirectory(prefix="h9-elevenlabs-") as temp_dir:
                mp3_path = Path(temp_dir) / "response.mp3"
                mp3_path.write_bytes(audio_bytes)
                try:
                    subprocess.run(
                        [
                            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                            "-i", str(mp3_path), "-ac", "1", "-ar", "44100",
                            "-c:a", "pcm_s16le", str(out_file),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        check=True,
                    )
                except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                    raise RuntimeError(f"Could not convert ElevenLabs MP3 to WAV: {exc}") from exc
            try:
                with wave.open(str(out_file), "rb") as wav_file:
                    sample_rate = wav_file.getframerate()
                    duration = wav_file.getnframes() / float(sample_rate)
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
            except (OSError, wave.Error, ZeroDivisionError) as exc:
                raise RuntimeError("Converted ElevenLabs narration WAV could not be measured.") from exc
            if duration <= 0 or channels < 1 or sample_width != 2:
                raise RuntimeError("Converted ElevenLabs narration WAV has invalid audio metadata.")
            file_size = out_file.stat().st_size
            audio_format = "wav"
        elif out_file.suffix.lower() == ".mp3":
            out_file.write_bytes(audio_bytes)
            ffprobe = shutil.which("ffprobe")
            if not ffprobe:
                raise RuntimeError("FFprobe is required to measure ElevenLabs MP3 duration.")
            try:
                measured = subprocess.run(
                    [
                        ffprobe, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(out_file),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=True,
                )
                duration = float(measured.stdout.strip())
            except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise RuntimeError(f"Could not measure ElevenLabs MP3 duration: {exc}") from exc
            sample_rate, channels, sample_width = 44100, 1, 2
            file_size = out_file.stat().st_size
            audio_format = "mp3"
        else:
            raise ValueError("ElevenLabs output path must end in .wav or .mp3.")

        return AudioMetadata(
            file_path=str(out_file),
            duration_seconds=duration,
            sample_rate=sample_rate,
            channels=channels,
            sample_width_bytes=sample_width,
            file_size_bytes=file_size,
            provider_used="elevenlabs",
            format=audio_format,
        )


class WindowsSAPITTSProvider(TTSProvider):
    """
    Crisp Native Offline Speech Synthesizer on Windows via PowerShell / System.Speech.Synthesis.
    """
    name = "windows_sapi"

    def is_available(self) -> bool:
        if os.name != "nt":
            return False
        # Verify that SAPI can actually render audio in this process. Listing
        # installed voices alone is insufficient: service or locked-down
        # Windows sessions can enumerate voices but cannot select or use them.
        probe_script = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$stream = New-Object System.IO.MemoryStream
try {
    $voices = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled })
    if ($voices.Count -eq 0) { throw 'No enabled SAPI voice is installed.' }
    $synth.SelectVoice($voices[0].VoiceInfo.Name)
    $synth.SetOutputToWaveStream($stream)
    $synth.Speak('Test.')
    if ($stream.Length -le 44) { throw 'SAPI returned an empty WAV stream.' }
    Write-Output 'ok'
} catch {
    exit 1
} finally {
    $synth.Dispose()
    $stream.Dispose()
}
"""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", probe_script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return res.returncode == 0 and "ok" in res.stdout.strip().lower()
        except Exception:
            return False

    def synthesize(
        self,
        text: str,
        output_path: Union[str, Path],
        target_duration: Optional[float] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioMetadata:
        if not self.is_available():
            raise RuntimeError("Windows SAPI TTS is not available on this platform.")

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        # Escape single quotes for PowerShell
        clean_text = text.replace("'", "''").replace('"', '`"').replace("\n", " ").replace("\r", " ")
        out_wav_str = str(out_file).replace("'", "''")

        rate_val = int(kwargs.get("rate", 0))  # System.Speech range: -10 to 10
        if not -10 <= rate_val <= 10:
            raise ValueError("Windows SAPI rate must be between -10 and 10.")
        volume_val = kwargs.get("volume", 100)

        def synthesize_at_rate(speech_rate: int) -> AudioMetadata:
            out_file.unlink(missing_ok=True)
            ps_script = f"""
$ErrorActionPreference = 'Stop';
Add-Type -AssemblyName System.Speech;
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
$synth.Rate = {speech_rate};
$synth.Volume = {volume_val};
"""
            if voice:
                clean_voice = voice.replace("'", "''")
                ps_script += f"""
try {{
    $synth.SelectVoice('{clean_voice}');
}} catch {{}}
"""

            ps_script += f"""
$synth.SetOutputToWaveFile('{out_wav_str}');
$synth.Speak('{clean_text}');
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
                    raise RuntimeError(
                        f"PowerShell SAPI execution returned {res.returncode}: {res.stderr.strip()}"
                    )
            except Exception as e:
                raise RuntimeError(f"Windows SAPI generation failed: {e}") from e

            if not out_file.exists() or out_file.stat().st_size < 100:
                raise RuntimeError(f"SAPI output WAV was not created or too small ({out_file}).")

            # Inspect the generated WAV using its actual frame count. If the file
            # is malformed, fail rather than estimating duration from its text.
            try:
                with wave.open(str(out_file), "rb") as wf:
                    channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    sample_rate = wf.getframerate()
                    frames = wf.getnframes()
                    if sample_rate <= 0 or frames <= 0:
                        raise RuntimeError("Windows SAPI produced WAV audio with no measurable samples.")
                    actual_duration = frames / float(sample_rate)
            except (OSError, wave.Error, EOFError) as exc:
                raise RuntimeError("Windows SAPI produced WAV audio that could not be measured.") from exc

            if channels < 1 or sample_width != 2 or actual_duration <= 0:
                raise RuntimeError("Windows SAPI produced invalid WAV audio metadata.")

            return AudioMetadata(
                file_path=str(out_file),
                duration_seconds=actual_duration,
                sample_rate=sample_rate,
                channels=channels,
                sample_width_bytes=sample_width,
                file_size_bytes=out_file.stat().st_size,
                provider_used="windows_sapi",
                format="wav",
            )

        if not target_duration or target_duration <= 0:
            return synthesize_at_rate(rate_val)

        target = float(target_duration)
        tolerance = max(1.0, target * 0.10)
        low_rate, high_rate = -10, 10
        checked_rates = set()
        measurements: List[Tuple[int, AudioMetadata]] = []
        candidate_rate = rate_val

        # SAPI expands numbers and abbreviations differently across voices.
        # Search real measured WAV durations across its supported rate range;
        # never stretch metadata or accept a synthetic duration estimate.
        for _ in range(7):
            if candidate_rate in checked_rates or candidate_rate < low_rate or candidate_rate > high_rate:
                break
            checked_rates.add(candidate_rate)
            measured = synthesize_at_rate(candidate_rate)
            measurements.append((candidate_rate, measured))

            if measured.duration_seconds > target + 0.01:
                low_rate = max(low_rate, candidate_rate + 1)
            else:
                if target - measured.duration_seconds <= tolerance:
                    # This rate fits. Try a slower rate to use more of the target
                    # duration without crossing into narration truncation.
                    high_rate = min(high_rate, candidate_rate - 1)
                else:
                    high_rate = min(high_rate, candidate_rate - 1)

            if low_rate > high_rate:
                break
            candidate_rate = (low_rate + high_rate) // 2

        feasible = [
            (speech_rate, meta)
            for speech_rate, meta in measurements
            if meta.duration_seconds <= target + 0.01
            and target - meta.duration_seconds <= tolerance
        ]
        if feasible:
            best_rate, best_meta = max(feasible, key=lambda item: item[1].duration_seconds)
        else:
            best_rate, best_meta = min(
                measurements,
                key=lambda item: abs(target - item[1].duration_seconds),
            )

        if measurements[-1][0] != best_rate:
            best_meta = synthesize_at_rate(best_rate)
        return best_meta


class HarmonicWAVSynthesizer(TTSProvider):
    """
    Pure Python Modulated Harmonic WAV Synthesizer (100% Deterministic Fallback).
    Zero external dependencies, works offline anywhere.
    Produces valid 16-bit PCM WAV audio with realistic speech-cadence amplitude envelopes.
    """
    name = "harmonic_synthesizer"

    def is_available(self) -> bool:
        return True

    def synthesize(
        self,
        text: str,
        output_path: Union[str, Path],
        target_duration: Optional[float] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioMetadata:
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        sample_rate = int(kwargs.get("sample_rate", DEFAULT_AUDIO_SAMPLE_RATE))
        words = text.split()
        num_words = max(1, len(words))

        # Determine duration: if target_duration provided use it; else calculate from words (~2.5 wps)
        if target_duration is not None and target_duration > 0:
            total_duration = float(target_duration)
        else:
            total_duration = max(2.0, num_words / 2.5)

        total_samples = int(total_duration * sample_rate)

        # Voice pitch profile
        voice_str = (voice or "default").lower()
        if "female" in voice_str or "nova" in voice_str or "heart" in voice_str:
            base_f0 = 220.0  # A3 (Female speaking pitch)
        elif "deep" in voice_str or "male" in voice_str or "michael" in voice_str:
            base_f0 = 120.0  # B2 (Deep male pitch)
        else:
            base_f0 = 160.0  # E3 (Neutral narrative pitch)

        # Build word intervals with micro-pauses
        pause_ratio = 0.15
        active_time = total_duration * (1.0 - pause_ratio)
        word_dur = active_time / float(num_words)
        pause_dur = (total_duration * pause_ratio) / float(num_words)

        frames = bytearray()
        sample_idx = 0

        # Formant frequencies for natural speech harmonics (F1, F2, F3)
        formants = [
            (base_f0 * 1.0, 0.40),    # Fundamental F0
            (base_f0 * 2.0, 0.25),    # Second harmonic
            (base_f0 * 3.5, 0.15),    # Formant F1
            (base_f0 * 5.0, 0.10),    # Formant F2
            (base_f0 * 8.0, 0.05),    # Formant F3 (clarity)
        ]

        # Precompute a base harmonic wave cycle for maximum generation speed
        cycle_length = max(10, int(sample_rate / base_f0))
        base_cycle = []
        for i in range(cycle_length):
            val = 0.0
            for freq_mult, amp_weight in formants:
                val += amp_weight * math.sin(2.0 * math.pi * (freq_mult / base_f0) * (i / cycle_length))
            base_cycle.append(val)

        # Generate audio buffer
        for w_idx, word in enumerate(words):
            vowels = len(re.findall(r'[aeiouy]', word.lower()))
            syllables = max(1, vowels)

            word_samples = int(word_dur * sample_rate)
            pause_samples = int(pause_dur * sample_rate)
            if word.endswith((".", "!", "?", ":", ";")):
                pause_samples = int(pause_samples * 2.0)

            # Attack / decay envelope parameters
            attack_len = int(word_samples * 0.15)
            decay_len = int(word_samples * 0.15)
            sustain_len = max(0, word_samples - attack_len - decay_len)

            # Generate word samples using precomputed cycle
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
                amplitude = 12000.0 * env
                final_val = int(cycle_val * amplitude)
                clamped_val = max(-32767, min(32767, final_val))
                frames.extend(struct.pack("<h", clamped_val))
                sample_idx += 1

            # Inter-word pause
            for s in range(pause_samples):
                if sample_idx >= total_samples:
                    break
                frames.extend(struct.pack("<h", 0))
                sample_idx += 1

        # Pad remaining samples to match total_duration precisely
        while sample_idx < total_samples:
            frames.extend(struct.pack("<h", 0))
            sample_idx += 1

        # Write WAV file atomically
        with wave.open(str(out_file), "wb") as wf:
            wf.setnchannels(1)      # Mono
            wf.setsampwidth(2)      # 16-bit PCM
            wf.setframerate(sample_rate)
            wf.writeframes(frames)

        file_size = out_file.stat().st_size
        return AudioMetadata(
            file_path=str(out_file),
            duration_seconds=total_duration,
            sample_rate=sample_rate,
            channels=1,
            sample_width_bytes=2,
            file_size_bytes=file_size,
            provider_used="harmonic_synthesizer",
            format="wav",
        )


class TTSEngine:
    """
    Main Text-to-Speech Engine managing provider fallback chain:
    ElevenLabs API -> Windows SAPI -> Pure Python Harmonic Synthesizer.
    """

    def __init__(
        self,
        elevenlabs_api_key: Optional[str] = None,
        default_voice: str = "af_nova",
        prefer_provider: Optional[str] = None,
    ):
        self.providers: Dict[str, TTSProvider] = {
            "elevenlabs": ElevenLabsTTSProvider(api_key=elevenlabs_api_key),
            "windows_sapi": WindowsSAPITTSProvider(),
            "harmonic_synthesizer": HarmonicWAVSynthesizer(),
        }
        self.default_voice = default_voice
        self.prefer_provider = prefer_provider

    def synthesize(
        self,
        text: str,
        output_path: Union[str, Path],
        target_duration: Optional[float] = None,
        voice: Optional[str] = None,
        provider_name: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioMetadata:
        """
        Synthesize text to audio using the best available provider or requested provider.
        """
        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        chosen_voice = voice or self.default_voice

        # Provider priority order
        provider_key = provider_name or self.prefer_provider
        if provider_key and provider_key in self.providers:
            provider = self.providers[provider_key]
            if provider.is_available():
                try:
                    return provider.synthesize(
                        text=text,
                        output_path=out_path,
                        target_duration=target_duration,
                        voice=chosen_voice,
                        **kwargs,
                    )
                except Exception as e:
                    # Fallback to standard chain
                    pass

        # Standard Fallback Chain: ElevenLabs -> Windows SAPI -> Harmonic Synthesizer
        chain = ["elevenlabs", "windows_sapi", "harmonic_synthesizer"]
        last_error = None

        for p_name in chain:
            prov = self.providers[p_name]
            if prov.is_available():
                try:
                    meta = prov.synthesize(
                        text=text,
                        output_path=out_path,
                        target_duration=target_duration,
                        voice=chosen_voice,
                        **kwargs,
                    )
                    return meta
                except Exception as e:
                    last_error = e
                    continue

        # If all else failed, guarantee pure python synthesis
        fallback = self.providers["harmonic_synthesizer"]
        return fallback.synthesize(
            text=text,
            output_path=out_path,
            target_duration=target_duration,
            voice=chosen_voice,
            **kwargs,
        )

    def get_audio_duration(self, audio_file: Union[str, Path]) -> float:
        """Inspect duration of an audio file in seconds."""
        p = Path(audio_file).resolve()
        if not p.exists():
            return 0.0
        if p.suffix.lower() == ".wav":
            try:
                with wave.open(str(p), "rb") as wf:
                    return wf.getnframes() / float(wf.getframerate())
            except Exception:
                pass
        return 0.0
