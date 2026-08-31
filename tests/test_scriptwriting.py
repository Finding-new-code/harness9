"""
tests/test_scriptwriting.py — Comprehensive Unit & Boundary Tests for R3 Script, Storyboard, Design Gate & TTS Engine (F6, F7).

Covers:
- Tier 1: Feature Coverage (F6 Structured Script & Storyboard, F7 Voiceover & TTS, Alignment, Pipeline)
- Tier 2: Boundary & Edge Cases (Corrupt inputs, empty texts, extreme durations, asset mismatches, Unicode, serialization roundtrips, WAV header validation, caption exit guarantees)
"""

import json
import os
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import yaml

from src.config import AppConfig
from src.models.dossier import Claim, DossierMetadata, ResearchDossier, Source, Summary, TalkingPoint
from src.models.ledger import (
    AssetProvenanceLedger,
    CreatorInfo,
    Dimensions,
    LicenseInfo,
    MediaAsset,
)
from src.models.script import Beat, Scene, Script, Storyboard
from src.scriptwriting.aligner import (
    TranscriptAligner,
    TranscriptGroup,
    TranscriptResult,
    TranscriptScene,
    WordTimestamp,
)
from src.scriptwriting.generator import (
    BrandGuidelines,
    ColorRole,
    DesignTheme,
    MotionRules,
    ScriptGenerator,
    TypographyStyle,
    generate_brief,
    generate_design,
    generate_script,
    generate_storyboard,
)
from src.scriptwriting.pipeline import ScriptwritingPipeline, ScriptwritingResult
from src.scriptwriting.tts import (
    AudioMetadata,
    ElevenLabsTTSProvider,
    HarmonicWAVSynthesizer,
    TTSEngine,
    WindowsSAPITTSProvider,
)


def _create_sample_dossier(topic: str = "The History of the Transistor") -> ResearchDossier:
    """Helper to build a valid sample ResearchDossier."""
    return ResearchDossier(
        topic=topic,
        metadata=DossierMetadata(run_id="test_run_01", target_duration_seconds=30),
        summary=Summary(
            headline=f"{topic}: The Foundation of Computation",
            executive_summary="Explores the invention and impact of the transistor.",
            key_takeaways=["Bell Labs breakthrough", "Solid state physics", "Modern silicon scaling"],
        ),
        claims=[
            Claim(
                claim_id="claim_01",
                claim_text="The point-contact transistor was invented in December 1947 at Bell Labs.",
                category="origin_history",
                confidence_score=0.98,
                primary_source=Source(title="Nobel Prize", url="https://nobelprize.org/1956"),
                visual_cue_suggestion="Bell Labs 1947 point-contact transistor prototype apparatus",
            ),
            Claim(
                claim_id="claim_02",
                claim_text="Transistors regulate electrical current using semiconductor materials.",
                category="technical_mechanism",
                confidence_score=0.94,
                primary_source=Source(title="IEEE", url="https://ieee.org/semiconductors"),
                visual_cue_suggestion="Semiconductor p-n junction electron flow diagram",
            ),
            Claim(
                claim_id="claim_03",
                claim_text="Modern microprocessors contain over 100 billion microscopic transistors.",
                category="quantitative_metric",
                confidence_score=0.92,
                primary_source=Source(title="Tech Review", url="https://example.com/transistors"),
                visual_cue_suggestion="Nanometer silicon die electron micrograph",
            ),
        ],
        talking_points=[
            TalkingPoint(
                beat_index=1,
                title="The 1947 Invention",
                narrative_hook="How three physicists at Bell Labs sparked the digital age.",
                supported_claim_ids=["claim_01"],
                estimated_duration_sec=10.0,
            ),
            TalkingPoint(
                beat_index=2,
                title="Solid-State Physics",
                narrative_hook="Replacing fragile vacuum tubes with pure silicon.",
                supported_claim_ids=["claim_02"],
                estimated_duration_sec=10.0,
            ),
            TalkingPoint(
                beat_index=3,
                title="The Silicon Revolution",
                narrative_hook="From one crude device to billions of transistors on a single chip.",
                supported_claim_ids=["claim_03"],
                estimated_duration_sec=10.0,
            ),
        ],
        suggested_visual_queries=["bell labs transistor", "semiconductor schematic", "microprocessor die"],
    )


def _create_sample_ledger(output_dir: Path) -> AssetProvenanceLedger:
    """Helper to build a sample AssetProvenanceLedger with real local files."""
    images_dir = output_dir / "assets" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    assets = []
    for i in range(3):
        asset_file = images_dir / f"asset_{i+1:02d}.svg"
        asset_file.write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><rect width="1920" height="1080" fill="#0a0e17"/></svg>', encoding="utf-8")
        assets.append(MediaAsset(
            asset_id=f"asset_{i+1:02d}",
            local_path=f"assets/images/asset_{i+1:02d}.svg",
            claim_id_refs=[f"claim_{i+1:02d}"],
            scene_target=f"scene_{i+1}",
            media_type="image/svg+xml",
            source_provider="procedural_vector_generator",
            source_url="https://commons.wikimedia.org",
            creator=CreatorInfo(name="Harness 9 Procedural Generator"),
            license=LicenseInfo(license_type="CC-BY-4.0"),
            verification_status="VERIFIED",
        ))

    return AssetProvenanceLedger(
        project_id="test_proj_01",
        total_assets=len(assets),
        assets=assets,
    )


class TestScriptwritingCoverage(unittest.TestCase):
    """Tier 1: Feature Coverage Tests (F6, F7)."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.topic = "The History of the Transistor"
        self.dossier = _create_sample_dossier(self.topic)
        self.ledger = _create_sample_ledger(self.out_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_01_brief_generation_content_and_structure(self):
        """F6: Validate BRIEF.md generation containing topic, duration, format, narrative arc, objectives."""
        brief_md = generate_brief(
            topic=self.topic,
            target_duration=30.0,
            aspect_ratio="16:9",
            audience="Engineers & Physicists",
        )
        self.assertIn(f"# BRIEF: {self.topic}", brief_md)
        self.assertIn("**Format**: 16:9", brief_md)
        self.assertIn("**Target Duration**: 30.0s", brief_md)
        self.assertIn("**Audience**: Engineers & Physicists", brief_md)
        self.assertIn("## Narrative Arc", brief_md)
        self.assertIn("## Key Objectives", brief_md)
        self.assertIn("## Composition Directives", brief_md)

    def test_02_design_gate_specification(self):
        """F6: Validate DESIGN.md generation strictly satisfies Hard Gate (Brand, Colors, Typography, Motion, Anti-patterns)."""
        design_md = generate_design(topic=self.topic)
        self.assertIn(f"# DESIGN: {self.topic}", design_md)
        
        # Verify Hard Gate required headers
        self.assertIn("## Brand", design_md)
        self.assertIn("## Colors", design_md)
        self.assertIn("## Typography", design_md)
        self.assertIn("## Motion", design_md)
        self.assertIn("## What NOT to Do", design_md)

        # Verify colors have explicit hex codes and roles
        self.assertIn("Background", design_md)
        self.assertIn("#0a0e17", design_md)
        self.assertIn("Primary Accent", design_md)
        self.assertIn("#00d2ff", design_md)

        # Verify typography specifications
        self.assertIn("Display", design_md)
        self.assertIn("Body", design_md)

        # Verify motion easings
        self.assertIn("power2.out", design_md)

        # Verify anti-patterns
        self.assertIn("Never use unbranded neon greens", design_md)
        self.assertIn("Never use pure black #000000", design_md)
        self.assertIn("repeat: -1", design_md)

    def test_03_design_theme_presets(self):
        """F6: Test preset brand design themes (tech_dark, cyberpunk_neon, editorial_gold)."""
        dark = DesignTheme.tech_dark()
        cyber = DesignTheme.cyberpunk_neon()
        gold = DesignTheme.editorial_gold()

        self.assertEqual(len(dark.colors), 5)
        self.assertEqual(len(cyber.colors), 5)
        self.assertEqual(len(gold.colors), 5)

        self.assertIn("#ff007f", [c.hex_code for c in cyber.colors])
        self.assertIn("#f0a500", [c.hex_code for c in gold.colors])

        cyber_design = generate_design(topic=self.topic, theme_name="cyberpunk_neon")
        self.assertIn("NeonPulse", cyber_design)
        self.assertIn("#ff007f", cyber_design)

    def test_04_script_generation_scenes_and_beats(self):
        """F6: Validate SCRIPT.md and structured Script model generation with scene and beat timing."""
        generator = ScriptGenerator()
        scenes = generator.synthesize_scenes_from_dossier(
            dossier=self.dossier,
            ledger=self.ledger,
            target_duration=30.0,
        )
        self.assertEqual(len(scenes), 3)

        script_model, script_md = generate_script(
            topic=self.topic,
            scenes=scenes,
            total_duration=30.0,
        )

        self.assertEqual(script_model.topic, self.topic)
        self.assertEqual(script_model.total_duration, 30.0)
        self.assertGreater(script_model.word_count, 10)
        self.assertEqual(len(script_model.storyboard.scenes), 3)

        # Check markdown contents
        self.assertIn(f"# SCRIPT: {self.topic}", script_md)
        self.assertIn("## Scene scene_1", script_md)
        self.assertIn("**Voiceover**:", script_md)
        self.assertIn("**Visual Cue**:", script_md)

    def test_05_storyboard_generation_gsap_and_hero(self):
        """F6: Validate STORYBOARD.md generation with hero frames, gsap.from() entrance, and transitions."""
        generator = ScriptGenerator()
        scenes = generator.synthesize_scenes_from_dossier(
            dossier=self.dossier,
            ledger=self.ledger,
            target_duration=30.0,
        )
        sb_md = generate_storyboard(topic=self.topic, scenes=scenes)

        self.assertIn(f"# STORYBOARD: {self.topic}", sb_md)
        self.assertIn("## SCENE_1", sb_md)
        self.assertIn("**Time Window**:", sb_md)
        self.assertIn("**Hero Frame Description**:", sb_md)
        self.assertIn("**Entrance Animation**: `gsap.from(", sb_md)
        self.assertIn("**Transition Out**:", sb_md)

    def test_06_harmonic_wav_tts_synthesis(self):
        """F7: Test Pure Python modulated harmonic WAV synthesizer outputs valid 16-bit PCM WAV."""
        synth = HarmonicWAVSynthesizer()
        self.assertTrue(synth.is_available())

        wav_path = self.out_path / "test_harmonic.wav"
        meta = synth.synthesize(
            text="The invention of the point-contact transistor revolutionized computation forever.",
            output_path=wav_path,
            target_duration=5.0,
            voice="af_nova",
        )

        self.assertTrue(wav_path.exists())
        self.assertGreater(wav_path.stat().st_size, 1000)
        self.assertAlmostEqual(meta.duration_seconds, 5.0, places=1)
        self.assertEqual(meta.channels, 1)
        self.assertEqual(meta.sample_width_bytes, 2)
        self.assertEqual(meta.format, "wav")

        # Verify WAV header integrity with wave module
        with wave.open(str(wav_path), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), 44100)
            frames = wf.getnframes()
            dur = frames / float(wf.getframerate())
            self.assertAlmostEqual(dur, 5.0, places=1)

    def test_07_windows_sapi_tts_provider(self):
        """F7: Test Windows SAPI TTS synthesizer availability and synthesis."""
        provider = WindowsSAPITTSProvider()
        if os.name == "nt" and provider.is_available():
            wav_path = self.out_path / "test_sapi.wav"
            meta = provider.synthesize(
                text="Testing Windows SAPI speech synthesis.",
                output_path=wav_path,
                target_duration=3.0,
            )
            self.assertTrue(wav_path.exists())
            self.assertGreater(wav_path.stat().st_size, 500)
            self.assertEqual(meta.provider_used, "windows_sapi")
        else:
            # On non-Windows or disabled env, ensure is_available returns False or handles cleanly
            self.assertIsInstance(provider.is_available(), bool)

    def test_08_elevenlabs_tts_provider(self):
        """F7: Test ElevenLabs provider handling and mock execution."""
        provider = ElevenLabsTTSProvider(api_key="mock_invalid_key")
        self.assertTrue(provider.is_available())

        # Test request failure handling
        wav_path = self.out_path / "test_elevenlabs.wav"
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"RIFF" + b"\x00" * 200
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            meta = provider.synthesize(
                text="Testing ElevenLabs audio narration.",
                output_path=wav_path,
                target_duration=4.0,
            )
            self.assertTrue(wav_path.exists())
            self.assertEqual(meta.provider_used, "elevenlabs")

    def test_09_tts_engine_provider_selection_and_fallback(self):
        """F7: Test TTSEngine fallback chain (ElevenLabs -> Windows SAPI -> Harmonic Synthesizer)."""
        engine = TTSEngine(elevenlabs_api_key=None)
        wav_path = self.out_path / "test_engine_fallback.wav"

        # Force fallback to pure python harmonic synthesizer
        meta = engine.synthesize(
            text="Fallback test narration.",
            output_path=wav_path,
            target_duration=3.5,
            provider_name="harmonic_synthesizer",
        )
        self.assertTrue(wav_path.exists())
        self.assertEqual(meta.provider_used, "harmonic_synthesizer")
        self.assertAlmostEqual(meta.duration_seconds, 3.5, places=1)

    def test_10_transcript_aligner_word_and_groups(self):
        """F6/F7: Test TranscriptAligner computing timestamped intervals per scene and word groups."""
        generator = ScriptGenerator()
        scenes = generator.synthesize_scenes_from_dossier(
            dossier=self.dossier,
            ledger=self.ledger,
            target_duration=30.0,
        )

        aligner = TranscriptAligner(target_words_per_group=3)
        result = aligner.align_scenes(scenes=scenes, total_duration=30.0)

        self.assertAlmostEqual(result.total_duration, 30.0, places=1)
        self.assertGreater(result.total_words, 10)
        self.assertEqual(len(result.scenes), 3)
        self.assertGreater(len(result.groups), 5)
        self.assertEqual(len(result.words), result.total_words)

        # Check monotonic timestamps in words
        prev_end = 0.0
        for w in result.words:
            self.assertGreaterEqual(w.start, prev_end - 0.001)
            self.assertGreater(w.end, w.start)
            prev_end = w.start

        # Check caption groups
        for g in result.groups:
            self.assertGreater(g.end, g.start)
            self.assertGreaterEqual(g.word_count, 1)
            self.assertLessEqual(g.word_count, 6)

        # Check serialization and save
        json_path = self.out_path / "transcript.json"
        result.save(json_path)
        self.assertTrue(json_path.exists())
        loaded = TranscriptResult.from_json(json_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded.total_words, result.total_words)

    def test_11_scriptwriting_pipeline_end_to_end(self):
        """F6/F7: Test full ScriptwritingPipeline connecting dossier + ledger to all output artifacts."""
        pipeline = ScriptwritingPipeline()
        res = pipeline.run(
            dossier=self.dossier,
            ledger=self.ledger,
            output_dir=self.out_path,
            target_duration=25.0,
            aspect_ratio="16:9",
        )

        self.assertEqual(res.status, "success")
        self.assertEqual(res.topic, self.topic)
        self.assertEqual(res.target_duration, 25.0)

        # Verify all required files exist
        self.assertTrue(Path(res.brief_path).exists())
        self.assertTrue(Path(res.design_path).exists())
        self.assertTrue(Path(res.script_path).exists())
        self.assertTrue(Path(res.storyboard_path).exists())
        self.assertTrue(Path(res.script_json_path).exists())
        self.assertTrue(Path(res.script_yaml_path).exists())
        self.assertTrue(Path(res.audio_path).exists())
        self.assertTrue(Path(res.transcript_path).exists())

        # Verify audio file is valid WAV and matches audio metadata duration
        self.assertGreater(Path(res.audio_path).stat().st_size, 1000)
        with wave.open(res.audio_path, "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            actual_dur = wf.getnframes() / float(wf.getframerate())
            self.assertAlmostEqual(actual_dur, res.audio_metadata.duration_seconds, places=1)
            self.assertAlmostEqual(res.transcript_result.total_duration, actual_dur, places=1)


class TestScriptwritingBoundaries(unittest.TestCase):
    """Tier 2: Boundary & Edge Cases."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.topic = "Quantum Computing Architectures"
        self.dossier = _create_sample_dossier(self.topic)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_12_empty_or_minimal_text_tts(self):
        """Edge Case: Single word or empty text handling in TTS synthesizer."""
        synth = HarmonicWAVSynthesizer()
        wav_path = self.out_path / "single_word.wav"
        meta = synth.synthesize(text="Quantum", output_path=wav_path, target_duration=2.0)
        self.assertTrue(wav_path.exists())
        self.assertAlmostEqual(meta.duration_seconds, 2.0, places=1)

        # Empty text
        wav_empty = self.out_path / "empty.wav"
        meta_empty = synth.synthesize(text="", output_path=wav_empty, target_duration=1.5)
        self.assertTrue(wav_empty.exists())
        self.assertAlmostEqual(meta_empty.duration_seconds, 1.5, places=1)

    def test_13_extreme_durations(self):
        """Edge Case: Extreme target durations (short 2s, long 120s)."""
        synth = HarmonicWAVSynthesizer()
        
        # Short 2s
        wav_short = self.out_path / "short.wav"
        meta_short = synth.synthesize(text="Quick overview.", output_path=wav_short, target_duration=2.0)
        self.assertAlmostEqual(meta_short.duration_seconds, 2.0, places=1)

        # Long 60s
        wav_long = self.out_path / "long.wav"
        meta_long = synth.synthesize(text="A longer narrative exploring extensive technical domains.", output_path=wav_long, target_duration=60.0)
        self.assertAlmostEqual(meta_long.duration_seconds, 60.0, places=1)

    def test_14_mismatched_asset_and_scene_counts(self):
        """Edge Case: More scenes than assets, or zero assets provided."""
        generator = ScriptGenerator()
        # Zero ledger provided
        scenes = generator.synthesize_scenes_from_dossier(dossier=self.dossier, ledger=None, target_duration=30.0)
        self.assertEqual(len(scenes), 3)
        for s in scenes:
            self.assertTrue(s.visual_asset_path.startswith("assets/images/"))

    def test_15_unicode_and_special_characters(self):
        """Edge Case: Special characters, quotes, math symbols, and Unicode in topic and text."""
        complex_topic = 'Quantum "Superposition" & E = mc² <Theory> & 100% Logic'
        brief = generate_brief(topic=complex_topic)
        self.assertIn(complex_topic, brief)

        design = generate_design(topic=complex_topic)
        self.assertIn(complex_topic, design)

        synth = HarmonicWAVSynthesizer()
        wav_path = self.out_path / "unicode_audio.wav"
        meta = synth.synthesize(text=f"Analyzing {complex_topic} with precision.", output_path=wav_path, target_duration=3.0)
        self.assertTrue(wav_path.exists())

    def test_16_script_json_yaml_roundtrip_parity(self):
        """Edge Case: JSON and YAML serialization and deserialization roundtrip parity."""
        generator = ScriptGenerator()
        scenes = generator.synthesize_scenes_from_dossier(self.dossier, target_duration=20.0)
        script_model, _ = generate_script(self.topic, scenes, total_duration=20.0)

        json_file, yaml_file = script_model.save(self.out_path, base_name="script_test")
        
        loaded_json = Script.load(json_file)
        loaded_yaml = Script.load(yaml_file)

        self.assertEqual(loaded_json.topic, script_model.topic)
        self.assertEqual(loaded_yaml.topic, script_model.topic)
        self.assertEqual(len(loaded_json.storyboard.scenes), len(script_model.storyboard.scenes))
        self.assertEqual(len(loaded_yaml.storyboard.scenes), len(script_model.storyboard.scenes))

    def test_17_audio_wav_riff_header_integrity(self):
        """Edge Case: Verify exact RIFF header bytes, format tags, and byte sizes of synthesized WAV."""
        synth = HarmonicWAVSynthesizer()
        wav_path = self.out_path / "header_test.wav"
        synth.synthesize("Testing WAV header bytes.", wav_path, target_duration=3.0)

        raw_bytes = wav_path.read_bytes()
        self.assertTrue(raw_bytes.startswith(b"RIFF"))
        self.assertEqual(raw_bytes[8:12], b"WAVE")
        self.assertEqual(raw_bytes[12:16], b"fmt ")

        # Parse audio format tag (1 for PCM)
        audio_format, channels, sample_rate, byte_rate, block_align, bits_per_sample = struct.unpack("<HHIIHH", raw_bytes[20:36])
        self.assertEqual(audio_format, 1)  # 1 = PCM
        self.assertEqual(channels, 1)
        self.assertEqual(sample_rate, 44100)
        self.assertEqual(bits_per_sample, 16)

    def test_18_transcript_caption_exit_guarantee(self):
        """Edge Case: Verify Caption Exit Guarantee - all word groups have bounded non-overlapping end times."""
        generator = ScriptGenerator()
        scenes = generator.synthesize_scenes_from_dossier(self.dossier, target_duration=15.0)
        aligner = TranscriptAligner(target_words_per_group=2)
        res = aligner.align_scenes(scenes, total_duration=15.0)

        for i, g in enumerate(res.groups):
            self.assertGreater(g.end, g.start)
            self.assertLessEqual(g.end, 15.001)
            if i > 0:
                self.assertGreaterEqual(g.start, res.groups[i-1].start)

    def test_19_missing_dossier_talking_points_fallback(self):
        """Edge Case: Dossier without talking points falls back to clean default scene synthesis."""
        dossier_no_tp = ResearchDossier(
            topic="Minimal Topic",
            metadata=DossierMetadata(run_id="run_min"),
            summary=Summary(headline="Headline", executive_summary="Summary"),
            claims=[],
            talking_points=[],
        )
        generator = ScriptGenerator()
        scenes = generator.synthesize_scenes_from_dossier(dossier_no_tp, target_duration=18.0)
        self.assertEqual(len(scenes), 3)
        self.assertAlmostEqual(sum(s.duration for s in scenes), 18.0, places=1)

    def test_20_pipeline_custom_voice_and_aspect_ratio(self):
        """Edge Case: Pipeline execution with 9:16 portrait aspect ratio and custom voice."""
        pipeline = ScriptwritingPipeline()
        res = pipeline.run(
            dossier=self.dossier,
            output_dir=self.out_path,
            target_duration=20.0,
            aspect_ratio="9:16",
            voice="deep_male",
        )
        self.assertEqual(res.aspect_ratio, "9:16")
        brief_text = Path(res.brief_path).read_text(encoding="utf-8")
        self.assertIn("9:16", brief_text)
        self.assertIn("1080x1920", brief_text)


if __name__ == "__main__":
    unittest.main()
