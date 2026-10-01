"""
tests/test_render_evaluation.py — evaluators report measurements, never invented numbers.

Regression guard for the old evaluators that returned audio_speech_alignment=0.95,
scene_pacing=0.92 and factual_grounding=0.96 and passed whenever an MP4 file existed.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from adapters.hermes.bridge import HermesBridge
from src.evaluation.media_gate import ExpectedMedia, MediaGate, MediaGateReport
from src.evaluation.render_evaluation import (
    NOT_MEASURED,
    evaluate_render,
    pick_video_to_evaluate,
    report_from_gate,
)
from src.models.contracts import EvaluationLayer, RenderArtifact
from tests.h9_media_fixtures import FFMPEG, make_video

INVENTED = ("factual_grounding", "audio_speech_alignment", "scene_pacing", "video_integrity")


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class TestEvaluateRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="h9_eval_"))
        cls.rich = make_video(cls.tmp / "rich.mp4", "testsrc2")
        cls.flat = make_video(cls.tmp / "flat.mp4", "color=c=0x0a2a18")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_real_picture_passes_with_measured_scores_only(self):
        r = evaluate_render(self.rich, run_id="e1")
        self.assertTrue(r.passed)
        self.assertEqual(r.layer, EvaluationLayer.VIDEO)
        self.assertEqual(r.composite_score, 1.0)
        for key in INVENTED:
            self.assertNotIn(key, r.scores)
        self.assertIn("picture_not_flat", r.scores)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in r.scores.values()))

    def test_unmeasured_dimensions_are_declared_not_scored(self):
        r = evaluate_render(self.rich, run_id="e2")
        line = next(f for f in r.feedback if f.startswith("NOT MEASURED"))
        for dimension in NOT_MEASURED:
            self.assertIn(dimension, line)

    def test_flat_video_fails_and_says_why(self):
        r = evaluate_render(self.flat, run_id="e3")
        self.assertFalse(r.passed)
        self.assertLess(r.composite_score, 1.0)
        self.assertTrue(any(f.startswith("FAIL not_flat") for f in r.feedback), r.feedback)
        self.assertEqual(r.scores["picture_not_flat"], 0.0)

    def test_missing_video_is_a_failed_evaluation_with_no_scores(self):
        for missing in (None, self.tmp / "nope.mp4"):
            r = evaluate_render(missing, run_id="e4")
            self.assertFalse(r.passed)
            self.assertEqual(r.scores, {})
            self.assertEqual(r.composite_score, 0.0)

    def test_unmeasurable_video_cannot_pass(self):
        with mock.patch("src.evaluation.media_gate.shutil.which", return_value=None):
            r = evaluate_render(self.rich, run_id="e5")
        self.assertFalse(r.passed)
        self.assertTrue(any("could not be measured" in f for f in r.feedback))

    def test_expected_duration_is_enforced(self):
        r = evaluate_render(self.rich, run_id="e6", expected=ExpectedMedia(duration=60.0))
        self.assertFalse(r.passed)
        self.assertTrue(any("duration_match" in f for f in r.feedback))

    def test_notes_are_prepended(self):
        r = evaluate_render(self.flat, run_id="e7", notes=["Render backend was 'stub'."])
        self.assertEqual(r.feedback[0], "Render backend was 'stub'.")

    def test_composite_is_the_fraction_of_passed_checks(self):
        gate_report = MediaGate().evaluate(self.flat)
        fail = [c for c in gate_report.checks if c.severity == "fail"]
        expected = round(sum(c.passed for c in fail) / len(fail), 4)
        self.assertEqual(report_from_gate(gate_report, "e8").composite_score, expected)


class TestPickVideo(unittest.TestCase):
    def test_preference_order(self):
        tmp = Path(tempfile.mkdtemp(prefix="h9_pick_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        names = ["a.mp4", "final.mp4", "final.rejected.mp4"]
        for n in names:
            (tmp / n).write_bytes(b"x")
        self.assertEqual(pick_video_to_evaluate(tmp / n for n in names).name, "final.mp4")
        self.assertEqual(pick_video_to_evaluate([tmp / "final.rejected.mp4", tmp / "a.mp4"]).name, "a.mp4")
        self.assertEqual(pick_video_to_evaluate([tmp / "final.rejected.mp4"]).name, "final.rejected.mp4")
        self.assertIsNone(pick_video_to_evaluate([tmp / "ghost.mp4"]))
        self.assertIsNone(pick_video_to_evaluate([]))


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class TestBridgeEvaluateSession(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="h9_bridge_"))
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.bridge = HermesBridge(base_output_dir=self.base)

    def _session_with(self, session_id, video_src):
        sandbox = self.bridge.get_sandbox(session_id)
        sandbox.renders_dir.mkdir(parents=True, exist_ok=True)
        make_video(sandbox.renders_dir / "final.mp4", video_src)
        return sandbox

    def test_real_picture_passes_and_is_audited(self):
        sandbox = self._session_with("s_rich", "testsrc2")
        report = self.bridge.evaluate_session("s_rich")
        self.assertTrue(report["passed"])
        for key in INVENTED:
            self.assertNotIn(key, report["scores"])
        self.assertTrue(any(f.startswith("NOT MEASURED") for f in report["feedback"]))
        audited = json.loads((sandbox.audit_dir / "evaluation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(audited["passed"], report["passed"])
        self.assertEqual(audited["scores"], report["scores"])

    def test_flat_video_no_longer_passes_just_because_the_file_exists(self):
        self._session_with("s_flat", "color=c=0x0a2a18")
        report = self.bridge.evaluate_session("s_flat")
        self.assertFalse(report["passed"])
        self.assertTrue(any(f.startswith("FAIL not_flat") for f in report["feedback"]), report["feedback"])

    def test_session_without_a_video_fails(self):
        report = self.bridge.evaluate_session("s_none")
        self.assertFalse(report["passed"])
        self.assertEqual(report["scores"], {})


class TestRenderArtifactDefault(unittest.TestCase):
    def test_a_render_artifact_is_not_verified_unless_someone_says_so(self):
        self.assertEqual(RenderArtifact(video_path="x.mp4", duration_seconds=1.0).validation_status, "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
