"""
tests/test_media_gate.py — the measured media gate, pinned against synthetic controls.

Every control is generated with ffmpeg's lavfi sources, so each test states a known truth
("this video is a flat colour") and asserts the gate reaches the same conclusion by decoding it.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.h9_media_fixtures import FFMPEG, make_video, run_ffmpeg
from src.evaluation.media_gate import (
    ExpectedMedia,
    GateThresholds,
    MediaGate,
    MediaGateError,
    MediaGateReport,
)

SIZE, DURATION = "640x360", 6
_run = run_ffmpeg


@unittest.skipUnless(FFMPEG, "ffmpeg/ffprobe not installed")
class TestMediaGateControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="h9_gate_"))
        t = cls.tmp
        cls.rich = make_video(t / "rich.mp4", "testsrc2")
        cls.flat = make_video(t / "flat.mp4", "color=c=0x0a2a18")
        # a smooth static vertical gradient (this is what the old placeholder renderer produced)
        cls.gradient = make_video(t / "gradient.mp4", "gradients=speed=0.00001:nb_colors=2:c0=0x0a2a18:c1=0x1a0f45:x0=0:y0=0:x1=0:y1=360")
        cls.black = make_video(t / "black.mp4", "color=c=black")
        cls.silent = make_video(t / "silent.mp4", "testsrc2", audio_src="anullsrc=channel_layout=stereo:sample_rate=44100")
        cls.noaudio = make_video(t / "noaudio.mp4", "testsrc2", audio_src=None)
        # frozen: one rich frame held for the whole clip
        frame = t / "frame.png"
        _run(["-f", "lavfi", "-i", f"testsrc2=size={SIZE}:rate=1", "-frames:v", "1", str(frame)])
        cls.frozen = t / "frozen.mp4"
        _run(["-loop", "1", "-framerate", "30", "-i", str(frame), "-f", "lavfi",
              "-i", f"sine=frequency=440:sample_rate=44100:duration={DURATION}", "-t", str(DURATION),
              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", "-c:a", "aac", str(cls.frozen)])
        cls.gate = MediaGate()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def failed(self, report):
        return {c.name for c in report.failed_checks()}

    # -- the control that must pass -----------------------------------------
    def test_rich_video_passes_every_check(self):
        r = self.gate.evaluate(self.rich, ExpectedMedia(duration=DURATION, width=640, height=360, fps=30))
        self.assertTrue(r.passed, r.summary())
        self.assertEqual(r.failed_checks(), [])
        self.assertGreater(r.metrics["edge_density"], 0.01)
        self.assertEqual(r.metrics["flat_frame_ratio"], 0.0)

    # -- the controls that must fail, and for the right reason ---------------
    def test_flat_colour_video_is_rejected(self):
        r = self.gate.evaluate(self.flat, ExpectedMedia(duration=DURATION))
        self.assertFalse(r.passed)
        self.assertIn("not_flat", self.failed(r))
        self.assertIn("visual_detail", self.failed(r))
        self.assertEqual(r.metrics["flat_frame_ratio"], 1.0)

    def test_static_gradient_is_rejected(self):
        r = self.gate.evaluate(self.gradient, ExpectedMedia(duration=DURATION))
        self.assertFalse(r.passed)
        self.assertIn("visual_detail", self.failed(r))

    def test_black_video_is_rejected(self):
        r = self.gate.evaluate(self.black)
        self.assertFalse(r.passed)
        self.assertIn("not_black", self.failed(r))

    def test_frozen_picture_is_rejected(self):
        r = self.gate.evaluate(self.frozen)
        self.assertFalse(r.passed)
        self.assertIn("not_frozen", self.failed(r))
        self.assertIn("has_motion", self.failed(r))

    def test_silent_audio_track_is_rejected(self):
        r = self.gate.evaluate(self.silent)
        self.assertFalse(r.passed)
        self.assertIn("audio_not_silent", self.failed(r))

    def test_missing_audio_stream_is_rejected_only_when_audio_is_required(self):
        needed = self.gate.evaluate(self.noaudio, ExpectedMedia(require_audio=True))
        self.assertIn("container_streams", self.failed(needed))
        optional = self.gate.evaluate(self.noaudio, ExpectedMedia(require_audio=False))
        self.assertTrue(optional.passed, optional.summary())

    def test_duration_resolution_and_fps_mismatches_are_rejected(self):
        r = self.gate.evaluate(self.rich, ExpectedMedia(duration=20, width=1920, height=1080, fps=60))
        self.assertEqual({"duration_match", "resolution_match", "fps_match"} & self.failed(r),
                         {"duration_match", "resolution_match", "fps_match"})

    # -- hostile inputs never crash the gate -----------------------------------
    def test_corrupt_file_is_a_failed_gate_not_an_exception(self):
        bad = self.tmp / "corrupt.mp4"
        bad.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\xff" * 64)
        r = self.gate.evaluate(bad)
        self.assertFalse(r.passed)
        self.assertIn("container_readable", self.failed(r))

    def test_missing_and_empty_files_fail(self):
        self.assertIn("file_exists", self.failed(self.gate.evaluate(self.tmp / "nope.mp4")))
        empty = self.tmp / "empty.mp4"
        empty.write_bytes(b"")
        self.assertIn("file_exists", self.failed(self.gate.evaluate(empty)))

    # -- API behaviour -----------------------------------------------------------
    def test_enforce_raises_with_the_report_attached(self):
        with self.assertRaises(MediaGateError) as ctx:
            self.gate.enforce(self.flat)
        self.assertFalse(ctx.exception.report.passed)
        self.assertIn("MEDIA GATE FAILED", str(ctx.exception))

    def test_enforce_returns_the_report_when_passing(self):
        self.assertTrue(self.gate.enforce(self.rich).passed)

    def test_report_json_roundtrip_and_save(self):
        r = self.gate.evaluate(self.rich)
        saved = r.save(self.tmp / "out" / "gate.json")
        restored = MediaGateReport.from_dict(json.loads(saved.read_text(encoding="utf-8")))
        self.assertEqual(restored.passed, r.passed)
        self.assertEqual([c.name for c in restored.checks], [c.name for c in r.checks])
        self.assertEqual(restored.file_size_bytes, r.file_size_bytes)

    def test_thresholds_are_configurable(self):
        lenient = MediaGate(GateThresholds(min_edge_density=0.0, min_luma_range=0.0, max_flat_frame_ratio=1.0,
                                           min_motion_ratio=0.0, max_frozen_ratio=1.0))
        self.assertTrue(lenient.evaluate(self.flat, ExpectedMedia(duration=DURATION)).passed)

    def test_probe_summary_reports_container_facts(self):
        info = self.gate.probe_summary(self.rich)
        self.assertEqual((info["width"], info["height"]), (640, 360))
        self.assertTrue(info["has_audio"])
        self.assertAlmostEqual(info["duration"], DURATION, delta=0.5)
        self.assertEqual(self.gate.probe_summary(self.tmp / "nope.mp4"), {})


if __name__ == "__main__":
    unittest.main()
