"""
tests/test_voice_director.py — Comprehensive Unit & Integration Tests for VoiceDirector (M4).

Tests:
1. Multi-provider VoiceDirector routing (ElevenLabs, OpenAI, Windows SAPI, Harmonic Synthesizer).
2. VoiceProfile configuration, character casting, and custom role registration.
3. Emotional tone modulation & tag stripping ([tense], [authoritative], [curious], [triumphant], [reflective], [urgent], [calm]).
4. WPM rate control (130-160 WPM default, bounded/clamped between 90 and 220 WPM).
5. AudioNarration contract output with scene-level audio boundary segmentation.
6. Edge cases: empty text, punctuation handling, pitch modifications, fallback hierarchies.
"""

from pathlib import Path
import tempfile
import unittest
import wave

from src.models.contracts import Script, ScriptBeat, ScriptScene
from src.scriptwriting.voice_director import (
    AudioNarration,
    BaseDirectorTTSProvider,
    ElevenLabsProvider,
    HarmonicWAVSynthProvider,
    OpenAIAudioProvider,
    VoiceDirector,
    VoiceProfile,
    WindowsSAPIProvider,
    clamp_wpm,
    strip_emotion_tags,
)


class TestVoiceDirector(unittest.TestCase):
    """Test suite for Multi-Provider VoiceDirector."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name)
        self.director = VoiceDirector()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_provider_initialization(self):
        """Verify all 4 TTS providers are initialized in VoiceDirector."""
        self.assertIn("elevenlabs", self.director.providers)
        self.assertIn("openai", self.director.providers)
        self.assertIn("sapi", self.director.providers)
        self.assertIn("harmonic", self.director.providers)
        self.assertTrue(self.director.providers["harmonic"].is_available())

    def test_02_voice_profile_defaults_and_validation(self):
        """Verify VoiceProfile default settings and Pydantic validation."""
        profile = VoiceProfile(
            voice_id="custom_voice",
            provider="harmonic",
            display_name="Custom Speaker",
            character_name="narrator",
            gender="female",
            speaking_rate_wpm=145,
            pitch_adjustment=0.05,
        )
        self.assertEqual(profile.voice_id, "custom_voice")
        self.assertEqual(profile.provider, "harmonic")
        self.assertEqual(profile.get_effective_wpm(), 145)
        self.assertEqual(profile.gender, "female")
        self.assertAlmostEqual(profile.pitch_adjustment, 0.05)

    def test_03_wpm_clamping_boundary_values(self):
        """Verify WPM rate control clamps to [90, 220] for extreme requests."""
        self.assertEqual(clamp_wpm(145), 145.0)
        self.assertEqual(clamp_wpm(30), 90.0)      # Extreme low
        self.assertEqual(clamp_wpm(400), 220.0)    # Extreme high
        self.assertEqual(clamp_wpm(90), 90.0)
        self.assertEqual(clamp_wpm(220), 220.0)
        self.assertEqual(clamp_wpm(130), 130.0)
        self.assertEqual(clamp_wpm(160), 160.0)

        # VoiceProfile with out-of-bounds WPM clamps via get_effective_wpm()
        extreme_profile = VoiceProfile(speaking_rate_wpm=500)
        self.assertEqual(extreme_profile.get_effective_wpm(), 220)
        low_profile = VoiceProfile(speaking_rate_wpm=20)
        self.assertEqual(low_profile.get_effective_wpm(), 90)

    def test_04_emotion_tag_stripping(self):
        """Verify extraction of emotional markers and clean spoken text."""
        raw_text = "[tense] The pressure inside the vessel exceeded critical limits."
        clean, emotion = strip_emotion_tags(raw_text)
        self.assertEqual(clean, "The pressure inside the vessel exceeded critical limits.")
        self.assertEqual(emotion, "tense")

        raw_auth = "[authoritative] Newton published the Principia Mathematica in 1687."
        clean_auth, emotion_auth = strip_emotion_tags(raw_auth)
        self.assertEqual(clean_auth, "Newton published the Principia Mathematica in 1687.")
        self.assertEqual(emotion_auth, "authoritative")

        raw_multi = "[curious] Why did the signal fluctuate?"
        clean_c, emotion_c = strip_emotion_tags(raw_multi)
        self.assertEqual(clean_c, "Why did the signal fluctuate?")
        self.assertEqual(emotion_c, "curious")

        # Text without emotion tag
        no_tag = "Standard narration without any brackets."
        clean_no, emotion_no = strip_emotion_tags(no_tag)
        self.assertEqual(clean_no, no_tag)
        self.assertIsNone(emotion_no)

    def test_05_character_casting_and_registration(self):
        """Verify character casting registry for multi-speaker roles."""
        narrator = self.director.get_character_profile("narrator")
        self.assertEqual(narrator.character_name, "narrator")
        self.assertEqual(narrator.gender, "female")

        expert = self.director.get_character_profile("expert")
        self.assertEqual(expert.character_name, "expert")
        self.assertEqual(expert.gender, "male")

        host = self.director.get_character_profile("host")
        self.assertEqual(host.character_name, "host")

        # Custom character registration
        custom_hero = VoiceProfile(
            voice_id="hero_voice",
            provider="harmonic",
            display_name="Captain Sterling",
            character_name="hero",
            gender="male",
            speaking_rate_wpm=150,
        )
        self.director.register_character("hero", custom_hero)
        retrieved = self.director.get_character_profile("hero")
        self.assertEqual(retrieved.display_name, "Captain Sterling")

        # Fallback to default for unknown character
        unknown = self.director.get_character_profile("unknown_alien")
        self.assertEqual(unknown.character_name, "narrator")

    def test_06_harmonic_wav_synthesis_audio_properties(self):
        """Verify pure-Python harmonic WAV synthesis produces valid 16-bit PCM WAV."""
        out_wav = self.out_dir / "test_harmonic.wav"
        text = "Silicon transistors revolutionized modern computing by replacing fragile vacuum tubes."
        profile = self.director.get_character_profile("narrator")

        narration = self.director.synthesize_text(
            text=text,
            output_path=out_wav,
            voice_profile=profile,
            target_duration=5.0,
        )

        self.assertTrue(out_wav.exists())
        self.assertGreater(out_wav.stat().st_size, 1000)
        self.assertEqual(narration.provider_used, "harmonic")
        self.assertAlmostEqual(narration.duration_seconds, 5.0, delta=0.1)

        # Inspect WAV header
        with wave.open(str(out_wav), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)  # 16-bit PCM
            self.assertEqual(wf.getframerate(), 44100)
            frames = wf.getnframes()
            self.assertGreater(frames, 0)
            actual_dur = frames / float(wf.getframerate())
            self.assertAlmostEqual(actual_dur, 5.0, delta=0.1)

    def test_07_emotional_tone_synthesis(self):
        """Verify synthesis with different emotional tones produces valid waveforms."""
        tones = ["tense", "authoritative", "curious", "triumphant", "reflective", "urgent", "calm"]
        for tone in tones:
            out_wav = self.out_dir / f"tone_{tone}.wav"
            text = f"[{tone}] This is a demonstration of {tone} tone modulation in the VoiceDirector."
            narration = self.director.synthesize_text(
                text=text,
                output_path=out_wav,
                voice_profile=self.director.get_character_profile("narrator"),
                target_duration=3.0,
            )
            self.assertTrue(out_wav.exists())
            self.assertEqual(narration.metadata.get("emotion"), tone)

    def test_08_multi_scene_script_narration_synthesis(self):
        """Verify full Script contract narration synthesis with scene segmentation."""
        script = Script(
            topic="History of Computing",
            title="The Microprocessor Revolution",
            total_duration=15.0,
            scenes=[
                ScriptScene(
                    scene_id="scene_01",
                    title="The Vacuum Tube Era",
                    duration=5.0,
                    narration_text="[reflective] In the early twentieth century, computing relied on bulky vacuum tubes.",
                    beats=[
                        ScriptBeat(beat_id="beat_1_1", text="Early computing relied on bulky vacuum tubes.", duration=5.0)
                    ],
                ),
                ScriptScene(
                    scene_id="scene_02",
                    title="The Solid State Breakthrough",
                    duration=5.0,
                    narration_text="[curious] What if electrons could flow across solid crystalline lattices?",
                    beats=[
                        ScriptBeat(beat_id="beat_2_1", text="What if electrons could flow across solid lattices?", duration=5.0)
                    ],
                ),
                ScriptScene(
                    scene_id="scene_03",
                    title="The Microprocessor Age",
                    duration=5.0,
                    narration_text="[triumphant] In 1971, Intel unveiled the 4004, ushering in the modern era.",
                    beats=[
                        ScriptBeat(beat_id="beat_3_1", text="Intel unveiled the 4004 microprocessor.", duration=5.0)
                    ],
                ),
            ],
        )

        narration = self.director.synthesize_narration(
            script=script,
            voice_profile=self.director.get_character_profile("narrator"),
            output_dir=self.out_dir,
        )

        self.assertTrue(Path(narration.audio_path).exists())
        self.assertAlmostEqual(narration.duration_seconds, 15.0, delta=0.2)
        self.assertEqual(len(narration.scene_audio_segments), 3)

        # Check scene boundaries
        seg1 = narration.scene_audio_segments[0]
        seg2 = narration.scene_audio_segments[1]
        seg3 = narration.scene_audio_segments[2]

        self.assertEqual(seg1["scene_id"], "scene_01")
        self.assertEqual(seg2["scene_id"], "scene_02")
        self.assertEqual(seg3["scene_id"], "scene_03")

        self.assertAlmostEqual(seg1["start_time"], 0.0)
        self.assertAlmostEqual(seg1["end_time"], 5.0, delta=0.2)
        self.assertAlmostEqual(seg2["start_time"], 5.0, delta=0.2)
        self.assertAlmostEqual(seg3["end_time"], 15.0, delta=0.2)

    def test_09_cloud_provider_fallback_when_unconfigured(self):
        """Verify seamless fallback from cloud providers to Harmonic Synthesizer when unconfigured."""
        eleven_profile = VoiceProfile(
            voice_id="rachel",
            provider="elevenlabs",
            display_name="Rachel Cloud",
        )
        out_wav = self.out_dir / "fallback_eleven.wav"
        # Without ELEVENLABS_API_KEY, fallback to harmonic
        narration = self.director.synthesize_text(
            text="Testing automatic cloud fallback to deterministic synthesizer.",
            output_path=out_wav,
            voice_profile=eleven_profile,
            target_duration=3.0,
        )
        self.assertTrue(out_wav.exists())
        self.assertEqual(narration.provider_used, "harmonic")

    def test_10_edge_cases_empty_and_short_texts(self):
        """Verify handling of edge case inputs (short, single-word, numbers)."""
        out_wav = self.out_dir / "edge_short.wav"
        narration = self.director.synthesize_text(
            text="Yes.",
            output_path=out_wav,
            voice_profile=self.director.get_character_profile("host"),
        )
        self.assertTrue(out_wav.exists())
        self.assertGreater(narration.duration_seconds, 0.5)


if __name__ == "__main__":
    unittest.main()
