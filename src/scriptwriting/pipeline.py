"""
src.scriptwriting.pipeline — End-to-End Scriptwriting & Voiceover Pipeline (R3).

Coordinates:
1. ResearchDossier & AssetProvenanceLedger ingestion
2. Script, Storyboard, Design Gate & Brief document generation
3. Multi-provider TTS narration synthesis (assets/audio/narration.wav)
4. Transcript beat alignment (assets/transcript.json)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config import AppConfig, get_default_config
from src.models.dossier import ResearchDossier
from src.models.ledger import AssetProvenanceLedger
from src.models.script import Script
from src.scriptwriting.aligner import TranscriptAligner, TranscriptResult
from src.scriptwriting.generator import BrandGuidelines, DesignTheme, ScriptGenerator
from src.scriptwriting.tts import AudioMetadata, TTSEngine
from src.utils.filesystem import ensure_dir


@dataclass
class ScriptwritingResult:
    """Artifact bundle output from the scriptwriting and voiceover pipeline."""
    topic: str
    target_duration: float
    aspect_ratio: str
    output_dir: str
    brief_path: str
    design_path: str
    script_path: str
    storyboard_path: str
    script_json_path: str
    script_yaml_path: str
    audio_path: str
    transcript_path: str
    audio_metadata: AudioMetadata
    transcript_result: TranscriptResult
    script_model: Script
    status: str = "success"
    brand_guidelines: Optional[BrandGuidelines] = None

    @property
    def audio(self) -> AudioMetadata:
        return self.audio_metadata

    @property
    def transcript(self) -> TranscriptResult:
        return self.transcript_result

    @property
    def storyboard(self) -> Any:
        return self.script_model.storyboard.scenes

    @property
    def brand(self) -> Optional[BrandGuidelines]:
        return self.brand_guidelines

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "topic": self.topic,
            "target_duration": self.target_duration,
            "aspect_ratio": self.aspect_ratio,
            "output_dir": self.output_dir,
            "artifacts": {
                "brief_md": self.brief_path,
                "design_md": self.design_path,
                "script_md": self.script_path,
                "storyboard_md": self.storyboard_path,
                "script_json": self.script_json_path,
                "script_yaml": self.script_yaml_path,
                "narration_audio": self.audio_path,
                "transcript_json": self.transcript_path,
            },
            "audio_metadata": self.audio_metadata.to_dict(),
            "transcript": self.transcript_result.to_dict(),
        }


class ScriptwritingPipeline:
    """
    Main pipeline orchestrator for Milestone 3 (Script, Storyboard, Design Gate & TTS).
    """

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        theme_name: str = "tech_dark",
        brand_guidelines: Optional[BrandGuidelines] = None,
        tts_voice: str = "af_nova",
        prefer_tts_provider: Optional[str] = None,
    ):
        self.config = config or get_default_config()
        self.theme_name = theme_name
        self.brand_guidelines = brand_guidelines or DesignTheme.get_preset(theme_name)
        self.tts_voice = tts_voice
        self.prefer_tts_provider = prefer_tts_provider

        self.generator = ScriptGenerator(
            theme_name=self.theme_name,
            brand_guidelines=self.brand_guidelines,
        )
        self.tts_engine = TTSEngine(
            elevenlabs_api_key=self.config.elevenlabs_api_key,
            default_voice=self.tts_voice,
            prefer_provider=self.prefer_tts_provider,
        )
        self.aligner = TranscriptAligner(target_words_per_group=3)

    def _resolve_dossier(
        self,
        dossier_input: Union[ResearchDossier, Dict[str, Any], Path, str],
    ) -> ResearchDossier:
        """Resolve dossier from instance, dict, or file path."""
        if isinstance(dossier_input, ResearchDossier):
            return dossier_input
        if isinstance(dossier_input, dict):
            return ResearchDossier.from_dict(dossier_input)
        if isinstance(dossier_input, (str, Path)):
            return ResearchDossier.load(dossier_input)
        raise TypeError(f"Unsupported dossier input type: {type(dossier_input)}")

    def _resolve_ledger(
        self,
        ledger_input: Optional[Union[AssetProvenanceLedger, Dict[str, Any], Path, str]],
    ) -> Optional[AssetProvenanceLedger]:
        """Resolve ledger from instance, dict, or file path."""
        if ledger_input is None:
            return None
        if isinstance(ledger_input, AssetProvenanceLedger):
            return ledger_input
        if isinstance(ledger_input, dict):
            return AssetProvenanceLedger.from_dict(ledger_input)
        if isinstance(ledger_input, (str, Path)):
            p = Path(ledger_input).resolve()
            if p.exists():
                return AssetProvenanceLedger.load(p)
        return None

    def run(
        self,
        dossier: Union[ResearchDossier, Dict[str, Any], Path, str],
        ledger: Optional[Union[AssetProvenanceLedger, Dict[str, Any], Path, str]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        target_duration: Optional[float] = None,
        aspect_ratio: str = "16:9",
        voice: Optional[str] = None,
        format_aspect: Optional[str] = None,
        **kwargs: Any,
    ) -> ScriptwritingResult:
        """
        Execute the scriptwriting and voiceover pipeline end-to-end.
        """
        effective_aspect = format_aspect or aspect_ratio or "16:9"
        resolved_dossier = self._resolve_dossier(dossier)
        resolved_ledger = self._resolve_ledger(ledger)

        out_dir_path = Path(output_dir or self.config.output_dir).resolve()
        assets_audio_dir = out_dir_path / "assets" / "audio"
        ensure_dir(out_dir_path)
        ensure_dir(assets_audio_dir)

        duration = target_duration if target_duration is not None else float(self.config.target_duration)

        # 1. Generate BRIEF.md, DESIGN.md, SCRIPT.md, STORYBOARD.md, script.json/yaml
        gen_result = self.generator.generate_all_documents(
            topic=resolved_dossier.topic,
            dossier=resolved_dossier,
            ledger=resolved_ledger,
            target_duration=duration,
            aspect_ratio=effective_aspect,
            output_dir=out_dir_path,
        )

        script_model: Script = gen_result["script_model"]
        scenes = gen_result["scenes"]

        # 2. Synthesize Audio Narration
        audio_output_path = assets_audio_dir / "narration.wav"
        full_text = script_model.full_transcript or " ".join(s.narration_text for s in scenes)

        audio_meta = self.tts_engine.synthesize(
            text=full_text,
            output_path=audio_output_path,
            target_duration=duration,
            voice=voice or self.tts_voice,
            provider_name=self.prefer_tts_provider,
        )

        # 3. Compute Transcript and Word-level Alignment
        actual_audio_duration = audio_meta.duration_seconds
        transcript_result = self.aligner.align_scenes(
            scenes=scenes,
            total_duration=actual_audio_duration,
        )

        # Save transcript.json into both output_dir and assets/
        transcript_path_assets = out_dir_path / "assets" / "transcript.json"
        transcript_path_root = out_dir_path / "transcript.json"
        transcript_result.save(transcript_path_assets)
        transcript_result.save(transcript_path_root)

        return ScriptwritingResult(
            topic=resolved_dossier.topic,
            target_duration=duration,
            aspect_ratio=effective_aspect,
            output_dir=str(out_dir_path),
            brief_path=str(out_dir_path / "BRIEF.md"),
            design_path=str(out_dir_path / "DESIGN.md"),
            script_path=str(out_dir_path / "SCRIPT.md"),
            storyboard_path=str(out_dir_path / "STORYBOARD.md"),
            script_json_path=str(out_dir_path / "script.json"),
            script_yaml_path=str(out_dir_path / "script.yaml"),
            audio_path=str(audio_output_path),
            transcript_path=str(transcript_path_assets),
            audio_metadata=audio_meta,
            transcript_result=transcript_result,
            script_model=script_model,
            status="success",
            brand_guidelines=self.brand_guidelines,
        )
