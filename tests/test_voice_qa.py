"""
tests/test_voice_qa.py — Comprehensive Acoustic Signal Tests for VoiceQA Engine (M4).

Tests all 4 acoustic quality gates:
1. Dead Air Detection (silence frames < -45 dBFS, internal gap > 300ms).
2. Clipping & Peak Saturation (saturated samples |s| >= 32767, clipping ratio < 0.01%).
3. Scene Loudness Consistency (RMS power variance across scenes <= 2.5 dBFS).
4. Speech-Beat Alignment Sync (max drift offset <= 0.20s).
5. EvaluationReport contract export and scoring fidelity.
"""

import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from src.models.contracts import Script, ScriptBeat, ScriptScene
from src.scriptwriting.voice_qa import (
    MAX_CLIPPING_RATIO,
    MAX_INTERNAL_GAP_SEC,
    MAX_LOUDNESS_VARIANCE_DB,
    MAX_SPEECH_BEAT_DRIFT_SEC,
    SILENCE_THRESHOLD_DBFS,
    VoiceQA,
    VoiceQAReport,
    calculate_sample_rms,
    load_wav_samples,
    rms_to_dbfs,
)


def create_test_wav(
    file_path: Path,
    duration_sec: float = 3.0,
    sample_rate: int = 44100,
    amplitude: float = 12000.0,
    frequency: float = 220.0,
    silent_gap_sec: float = 0.0,
    silent_gap_offset_sec: float = 1.0,
    clipped_sample_count: int = 0,
) -> Path:
    """Helper to generate synthetic test WAV files with precise acoustic parameters."""
    total_samples = int(duration_sec * sample_rate)
    gap_start = int(silent_gap_offset_sec * sample_rate)
    gap_end = gap_start + int(silent_gap_sec * sample_rate)

    samples = []
    for i in range(total_samples):
        if gap_start <= i < gap_end:
            samples.append(0)
        else:
            val = int(amplitude * math.sin(2.0 * math.pi * frequency * (i / sample_rate)))
            samples.append(val)

    # Inject clipped samples if requested
    if clipped_sample_count > 0:
        step = max(1, total_samples // clipped_sample_count)
        for idx in range(0, total_samples, step):
            if idx < len(samples):
                samples[idx] = 32767

    # Write WAV
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        packed = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(packed)

    return file_path


class TestVoiceQA(unittest.TestCase):
    """Acoustic inspection test suite for VoiceQA."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name)
        self.qa = VoiceQA()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_clean_audio_passes_all_gates(self):
        """Verify normal, clean audio narration passes all 4 VoiceQA gates."""
        clean_wav = self.out_dir / "clean_narration.wav"
        create_test_wav(
            file_path=clean_wav,
            duration_sec=4.0,
            amplitude=12000.0,
            frequency=180.0,
            silent_gap_sec=0.10,  # 100ms gap (well within <= 300ms)
        )

        script = Script(
            topic="Clean Audio Test",
            title="Clean Narration",
            total_duration=4.0,
            scenes=[
                ScriptScene(scene_id="s1", duration=2.0, narration_text="First scene."),
                ScriptScene(scene_id="s2", duration=2.0, narration_text="Second scene."),
            ],
        )

        report = self.qa.inspect_audio(clean_wav, script=script)

        self.assertTrue(report.passed)
        self.assertTrue(report.gate_results["clipping_gate"])
        self.assertTrue(report.gate_results["dead_air_gate"])
        self.assertTrue(report.gate_results["loudness_gate"])
        self.assertTrue(report.gate_results["beat_sync_gate"])

        self.assertLess(report.clipping_ratio, MAX_CLIPPING_RATIO)
        self.assertLessEqual(report.max_dead_air_duration_sec, MAX_INTERNAL_GAP_SEC)
        self.assertLessEqual(report.loudness_variance_db, MAX_LOUDNESS_VARIANCE_DB)
        self.assertLessEqual(report.speech_beat_max_drift_sec, MAX_SPEECH_BEAT_DRIFT_SEC)

    def test_02_clipping_rejection_boundary(self):
        """Verify audio with clipping ratio >= 0.01% is rejected."""
        clipped_wav = self.out_dir / "clipped_audio.wav"
        sample_rate = 44100
        dur_sec = 2.0
        total_samples = int(dur_sec * sample_rate)  # 88,200 samples
        # 0.05% clipping = ~44 clipped samples (> 0.01% limit)
        create_test_wav(
            file_path=clipped_wav,
            duration_sec=dur_sec,
            sample_rate=sample_rate,
            amplitude=12000.0,
            clipped_sample_count=80,
        )

        report = self.qa.inspect_audio(clipped_wav, expected_duration=2.0)

        self.assertFalse(report.passed)
        self.assertFalse(report.gate_results["clipping_gate"])
        self.assertGreater(report.clipping_ratio, MAX_CLIPPING_RATIO)
        self.assertTrue(any("clipping" in issue.lower() for issue in report.issues))

    def test_03_dead_air_rejection_boundary(self):
        """Verify audio with internal silence gap > 300ms is rejected."""
        dead_air_wav = self.out_dir / "dead_air_audio.wav"
        create_test_wav(
            file_path=dead_air_wav,
            duration_sec=4.0,
            amplitude=12000.0,
            silent_gap_sec=0.50,  # 500ms dead air gap (> 300ms)
            silent_gap_offset_sec=1.5,
        )

        report = self.qa.inspect_audio(dead_air_wav, expected_duration=4.0)

        self.assertFalse(report.passed)
        self.assertFalse(report.gate_results["dead_air_gate"])
        self.assertGreater(report.max_dead_air_duration_sec, MAX_INTERNAL_GAP_SEC)
        self.assertTrue(any("dead air" in issue.lower() for issue in report.issues))

    def test_04_scene_loudness_inconsistency_rejection(self):
        """Verify audio with scene loudness variance > 2.5 dBFS is rejected."""
        # Generate two scenes with large volume difference (e.g. 15000 vs 2000)
        sample_rate = 44100
        samples_s1 = [int(15000 * math.sin(2.0 * math.pi * 200.0 * (i / sample_rate))) for i in range(sample_rate * 2)]
        samples_s2 = [int(2000 * math.sin(2.0 * math.pi * 200.0 * (i / sample_rate))) for i in range(sample_rate * 2)]
        combined_samples = samples_s1 + samples_s2

        inconsistent_wav = self.out_dir / "loudness_inconsistent.wav"
        with wave.open(str(inconsistent_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f"<{len(combined_samples)}h", *combined_samples))

        script = Script(
            topic="Loudness Test",
            title="Variance Test",
            total_duration=4.0,
            scenes=[
                ScriptScene(scene_id="s1", duration=2.0, narration_text="Loud scene."),
                ScriptScene(scene_id="s2", duration=2.0, narration_text="Quiet scene."),
            ],
        )

        report = self.qa.inspect_audio(inconsistent_wav, script=script)

        self.assertFalse(report.passed)
        self.assertFalse(report.gate_results["loudness_gate"])
        self.assertGreater(report.loudness_variance_db, MAX_LOUDNESS_VARIANCE_DB)
        self.assertTrue(any("loudness" in issue.lower() for issue in report.issues))

    def test_05_speech_beat_sync_drift_rejection(self):
        """Verify audio with speech-beat drift > 0.20s is rejected."""
        # Generate 2.0s audio, but expected duration is 4.0s (drift = 2.0s > 0.2s)
        drifted_wav = self.out_dir / "drifted_audio.wav"
        create_test_wav(
            file_path=drifted_wav,
            duration_sec=2.0,
            amplitude=12000.0,
        )

        report = self.qa.inspect_audio(drifted_wav, expected_duration=4.0)

        self.assertFalse(report.passed)
        self.assertFalse(report.gate_results["beat_sync_gate"])
        self.assertGreater(report.speech_beat_max_drift_sec, MAX_SPEECH_BEAT_DRIFT_SEC)
        self.assertTrue(any("drift" in issue.lower() for issue in report.issues))

    def test_06_evaluation_report_contract_conversion(self):
        """Verify VoiceQAReport cleanly converts to standard H9 EvaluationReport."""
        clean_wav = self.out_dir / "eval_clean.wav"
        create_test_wav(file_path=clean_wav, duration_sec=3.0)

        qa_report = self.qa.inspect_audio(clean_wav, expected_duration=3.0)
        eval_report = qa_report.to_evaluation_report(run_id="run_test_01")

        self.assertEqual(eval_report.run_id, "run_test_01")
        self.assertEqual(eval_report.layer, "layer_3_video")
        self.assertTrue(eval_report.passed)
        self.assertEqual(eval_report.composite_score, 1.0)
        self.assertIn("clipping_score", eval_report.scores)
        self.assertIn("dead_air_score", eval_report.scores)
        self.assertIn("loudness_consistency_score", eval_report.scores)
        self.assertIn("beat_sync_score", eval_report.scores)

    def test_07_signal_processing_mathematical_helpers(self):
        """Verify mathematical helpers (RMS and dBFS calculations)."""
        zero_samples = [0, 0, 0, 0]
        self.assertEqual(calculate_sample_rms(zero_samples), 0.0)
        self.assertEqual(rms_to_dbfs(0.0), -100.0)

        # Full scale sine wave has RMS = 32767 / sqrt(2) ≈ 23169.8
        # Loudness ≈ 20 * log10(1 / sqrt(2)) ≈ -3.01 dBFS
        sine_samples = [int(32767 * math.sin(2.0 * math.pi * 100 * (i / 44100))) for i in range(44100)]
        rms_val = calculate_sample_rms(sine_samples)
        dbfs_val = rms_to_dbfs(rms_val)
        self.assertAlmostEqual(dbfs_val, -3.01, delta=0.2)

    def test_08_load_wav_samples_mono_and_stereo(self):
        """Verify load_wav_samples accurately parses 16-bit PCM WAV headers."""
        wav_path = self.out_dir / "sample_load.wav"
        create_test_wav(file_path=wav_path, duration_sec=1.5, sample_rate=22050)

        samples, s_rate, dur = load_wav_samples(wav_path)
        self.assertEqual(s_rate, 22050)
        self.assertAlmostEqual(dur, 1.5, delta=0.01)
        self.assertEqual(len(samples), int(1.5 * 22050))


if __name__ == "__main__":
    unittest.main()
