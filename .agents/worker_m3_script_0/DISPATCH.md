# Dispatch for Worker M3 Script & Voiceover Engine
Directory: g:\Finding-new-code\harness9\.agents\worker_m3_script_0

## 2026-08-31T05:28:01Z
You are the Worker for Milestone 3: Script, Storyboard, Design Gate & TTS Voiceover Engine (R3).
Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m3_script_0
Project root: g:\Finding-new-code\harness9
Original request: g:\Finding-new-code\harness9\ORIGINAL_REQUEST.md
Project architecture & specs: g:\Finding-new-code\harness9\PROJECT.md
HyperFrames Spec Miner Report: g:\Finding-new-code\harness9\.agents\spec_miner_hyperframes_0\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your exclusive write ownership: `src/scriptwriting/`, `tests/test_scriptwriting.py`

Your tasks:
1. Implement `src/scriptwriting/generator.py`:
   - `BRIEF.md` generator (topic, audience, target duration, format 16:9 or 9:16, narrative arc).
   - `DESIGN.md` generator (HARD GATE: brand name, 3-5 explicit colors with functional roles, display and body typography, motion mood and standard easings, and explicit anti-patterns).
   - `SCRIPT.md` generator (scene breakdown with timestamped voiceover beats, duration estimates, and visual cues).
   - `STORYBOARD.md` generator (hero frame descriptions, entrance animations `gsap.from()`, and seamless transitions).
2. Implement `src/scriptwriting/tts.py`:
   - Multi-provider TTS engine:
     a. ElevenLabs API adapter (when `ELEVENLABS_API_KEY` is provided).
     b. Windows SAPI PowerShell voice synthesizer (using System.Speech.Synthesis for crisp native offline speech on Windows).
     c. Pure Python modulated harmonic WAV synthesizer (100% deterministic fallback).
   - Outputs valid 16-bit PCM WAV (`assets/audio/narration.wav`) or MP3 with accurate duration.
3. Implement `src/scriptwriting/aligner.py`:
   - Audio beat & transcript alignment computing timestamped intervals `[start, end]` per scene and word group, generating `transcript.json`.
4. Implement `src/scriptwriting/pipeline.py`:
   - `ScriptwritingPipeline` connecting `ResearchDossier` and `AssetProvenanceLedger` to script documents and audio.
5. Implement comprehensive unit & boundary tests in `tests/test_scriptwriting.py` and verify all tests pass (`python -m unittest tests/test_scriptwriting.py -v`).

Write report to: g:\Finding-new-code\harness9\.agents\worker_m3_script_0\report.md
And handoff to: g:\Finding-new-code\harness9\.agents\worker_m3_script_0\handoff.md

Send message to parent when finished.
