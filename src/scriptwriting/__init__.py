"""
src.scriptwriting — Script, Storyboard, Design Gate & TTS Voiceover Engine (Milestone 3).

Provides:
- Document Generators: BRIEF.md, DESIGN.md, SCRIPT.md, STORYBOARD.md
- Multi-Provider TTS: ElevenLabs API, Windows SAPI PowerShell, Pure Python Harmonic WAV
- Transcript & Audio Alignment: Word-level and group-level timestamp alignment
- End-to-End Scriptwriting Pipeline: Connecting ResearchDossier & AssetProvenanceLedger to audio & script
"""

from src.scriptwriting.generator import (
    ScriptGenerator,
    generate_brief,
    generate_design,
    generate_script,
    generate_storyboard,
    DesignTheme,
    BrandGuidelines,
)
from src.scriptwriting.tts import (
    TTSEngine,
    TTSProvider,
    ElevenLabsTTSProvider,
    WindowsSAPITTSProvider,
    HarmonicWAVSynthesizer,
    AudioMetadata,
)
from src.scriptwriting.aligner import (
    TranscriptAligner,
    WordTimestamp,
    TranscriptGroup,
    TranscriptScene,
    TranscriptResult,
)
from src.scriptwriting.pipeline import (
    ScriptwritingPipeline,
    ScriptwritingResult,
)

__all__ = [
    "ScriptGenerator",
    "generate_brief",
    "generate_design",
    "generate_script",
    "generate_storyboard",
    "DesignTheme",
    "BrandGuidelines",
    "TTSEngine",
    "TTSProvider",
    "ElevenLabsTTSProvider",
    "WindowsSAPITTSProvider",
    "HarmonicWAVSynthesizer",
    "AudioMetadata",
    "TranscriptAligner",
    "WordTimestamp",
    "TranscriptGroup",
    "TranscriptScene",
    "TranscriptResult",
    "ScriptwritingPipeline",
    "ScriptwritingResult",
]
