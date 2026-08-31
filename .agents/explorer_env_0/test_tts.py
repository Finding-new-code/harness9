import subprocess
import os
import wave
import math
import struct
import shutil
import json

tts_results = {}

# Method 1: PowerShell System.Speech.Synthesis
ps_code = """
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$wavPath = "g:\\Finding-new-code\\harness9\\.agents\\explorer_env_0\\test_sapi.wav"
$synth.SetOutputToWaveFile($wavPath)
$synth.Speak("This is a deterministic voice narration test for Harness 9 pipeline.")
$synth.Dispose()
"""
ps_file = r"g:\Finding-new-code\harness9\.agents\explorer_env_0\test_sapi.ps1"
with open(ps_file, "w", encoding="utf-8") as f:
    f.write(ps_code)

try:
    res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file], capture_output=True, text=True, timeout=10)
    wav_out = r"g:\Finding-new-code\harness9\.agents\explorer_env_0\test_sapi.wav"
    exists = os.path.exists(wav_out)
    size = os.path.getsize(wav_out) if exists else 0
    tts_results["windows_sapi_powershell"] = {
        "success": exists and size > 0,
        "wav_path": wav_out,
        "size_bytes": size,
        "stderr": res.stderr
    }
except Exception as e:
    tts_results["windows_sapi_powershell"] = {"success": False, "error": str(e)}

# Method 2: Pure Python Deterministic Audio Synthesizer (Zero External Dependencies)
# Generates speech-like/rhythmic tones with envelope and word beats
def synthesize_deterministic_synthetic_audio(text, output_wav_path, sample_rate=24000):
    words = text.split()
    total_duration = max(1.5, len(words) * 0.4) # ~0.4s per word
    num_samples = int(total_duration * sample_rate)
    
    with wave.open(output_wav_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            word_idx = int(t / 0.4) % max(1, len(words))
            # Base harmonic pitch modulated by word index
            freq1 = 180 + (word_idx * 17) % 120
            freq2 = freq1 * 1.5
            freq3 = freq1 * 2.0
            
            # Envelope within each word beat
            beat_t = (t % 0.4) / 0.4
            envelope = math.sin(math.pi * min(1.0, beat_t * 1.2)) * (1.0 - 0.3 * beat_t)
            
            val = (0.5 * math.sin(2 * math.pi * freq1 * t) +
                   0.3 * math.sin(2 * math.pi * freq2 * t) +
                   0.2 * math.sin(2 * math.pi * freq3 * t)) * envelope
            
            sample = int(max(-32767, min(32767, val * 20000)))
            frames.extend(struct.pack('<h', sample))
            
        wav_file.writeframes(frames)
    return total_duration

synth_wav_out = r"g:\Finding-new-code\harness9\.agents\explorer_env_0\test_synth.wav"
try:
    dur = synthesize_deterministic_synthetic_audio("Welcome to the Harness 9 video pipeline demonstration.", synth_wav_out)
    tts_results["pure_python_synth"] = {
        "success": os.path.exists(synth_wav_out) and os.path.getsize(synth_wav_out) > 0,
        "path": synth_wav_out,
        "duration_seconds": dur,
        "size_bytes": os.path.getsize(synth_wav_out)
    }
except Exception as e:
    tts_results["pure_python_synth"] = {"success": False, "error": str(e)}

# Method 3: ElevenLabs API Key Check
eleven_key = os.environ.get("ELEVENLABS_API_KEY")
tts_results["elevenlabs"] = {
    "api_key_present": bool(eleven_key),
    "key_preview": (eleven_key[:4] + "..." + eleven_key[-4:]) if eleven_key else None
}

with open(r"g:\Finding-new-code\harness9\.agents\explorer_env_0\tts_probe_results.json", "w", encoding="utf-8") as f:
    json.dump(tts_results, f, indent=2)

print("TTS Probe completed.")
