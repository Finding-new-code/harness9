"""
tests/test_render_backend.py — the renderer never fakes a success.

Three layers:
  1. Backend semantics with a *patched capture step* that writes known frames (rich / flat) — fast,
     needs only ffmpeg. Proves: VERIFIED only through the measured gate, rejected videos are
     quarantined, failures are loud, stale videos are removed.
  2. Pipeline semantics: a stub run is PARTIAL, an unavailable renderer or a gate rejection FAILS the run.
  3. A REAL headless-Chromium render of a tiny GSAP composition (skipped unless the capture toolchain is
     installed: `python run_harness9.py --check-render`, or set HARNESS9_TOOLCHAIN_DIR).
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.evaluation.media_gate import MediaGateError, MediaGateReport
from src.hyperframes import renderer as renderer_module
from src.hyperframes.browser_capture import (
    BrowserCaptureError,
    CaptureResult,
    RenderUnavailableError,
    availability,
)
from src.hyperframes.renderer import RENDER_BACKENDS, HyperFramesRenderer
from src.orchestrator.pipeline import Pipeline
from src.utils.ffmpeg import FFmpegError
from tests.h9_media_fixtures import FFMPEG, make_frames, make_wav

W, H, FPS, DUR = 640, 360, 30, 3

COMPOSITION = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><link rel="stylesheet" href="styles.css"></head>
<body><div id="root" data-composition-id="root" data-start="0" data-duration="{DUR}" data-width="{W}" data-height="{H}">
<h1 id="title">Harness 9 render test</h1><div id="box"></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="main.js"></script></body></html>"""
STYLES = ("html,body{margin:0;background:#0b1020;width:100%;height:100%;overflow:hidden}"
          "h1{position:absolute;left:30px;top:30px;color:#fff;font:700 44px sans-serif}"
          "#box{position:absolute;top:200px;left:0;width:120px;height:120px;background:#2dd4ff}")
MAIN_JS = ("window.__timelines = window.__timelines || {};"
           "const tl = gsap.timeline({paused:true});"
           f"tl.fromTo('#box',{{x:0}},{{x:{W - 150},duration:{DUR},ease:'none'}},0);"
           "window.__timelines['root'] = tl;")


def write_project(root: Path, main_js: str = MAIN_JS, extra_html: str = "", narration_seconds: float = DUR) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(COMPOSITION.replace("</div>\n<script", extra_html + "</div>\n<script", 1),
                                     encoding="utf-8")
    (root / "styles.css").write_text(STYLES, encoding="utf-8")
    (root / "main.js").write_text(main_js, encoding="utf-8")
    if FFMPEG:
        audio = root / "assets" / "audio"
        audio.mkdir(parents=True, exist_ok=True)
        make_wav(audio / "narration.wav", narration_seconds)
    return root


def patched_capture(kind: str, seen: dict = None):
    """A capture_frames stand-in that writes real PNG frames of the given kind ('rich' | 'flat')."""
    def _capture(project_dir, frames_dir, *, width, height, fps, duration, **kwargs):
        if seen is not None:
            seen.update(kwargs, width=width, height=height, fps=fps, duration=duration)
        n = round(duration * fps)
        make_frames(frames_dir, kind, n, size=f"{width}x{height}", fps=fps)
        return CaptureResult(frames=n, frames_dir=Path(frames_dir), frame_pattern=str(Path(frames_dir) / "frame_%06d.png"),
                             image_format="png")
    return _capture


class _TmpDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="h9_render_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)


class TestBackendSelection(unittest.TestCase):
    def test_default_backend_is_the_real_renderer(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HARNESS9_RENDER_BACKEND", None)
            self.assertEqual(HyperFramesRenderer().backend, "chrome")

    def test_env_var_and_argument_selection(self):
        with mock.patch.dict(os.environ, {"HARNESS9_RENDER_BACKEND": "stub"}):
            self.assertEqual(HyperFramesRenderer().backend, "stub")
            self.assertEqual(HyperFramesRenderer(backend="chrome").backend, "chrome")  # argument wins

    def test_unknown_backend_is_rejected(self):
        with self.assertRaises(ValueError):
            HyperFramesRenderer(backend="placeholder")
        self.assertEqual(set(RENDER_BACKENDS), {"chrome", "stub"})


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class TestStubBackend(_TmpDirTest):
    def test_stub_is_labelled_and_never_verified(self):
        proj = write_project(self.tmp / "p")
        res = HyperFramesRenderer(backend="stub").render(proj, duration=DUR, width=W, height=H)
        self.assertEqual(res.validation_status, "STUB")
        self.assertEqual(res.backend, "stub")
        self.assertIsNone(res.gate)
        self.assertTrue(any("NOT a real video" in w for w in res.warnings))
        self.assertTrue(Path(res.output_path).exists())


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class TestChromeBackendSemantics(_TmpDirTest):
    def render(self, kind, **kw):
        proj = write_project(self.tmp / "p")
        with mock.patch.object(renderer_module, "capture_frames", patched_capture(kind, kw.pop("seen", None))):
            return proj, HyperFramesRenderer(backend="chrome", **kw).render(proj, duration=DUR, width=W, height=H, fps=FPS)

    def test_rich_frames_pass_the_gate_and_are_verified(self):
        proj, res = self.render("rich")
        self.assertEqual(res.validation_status, "VERIFIED")
        self.assertTrue(res.gate["passed"])
        self.assertEqual(res.frames_captured, DUR * FPS)
        self.assertEqual(Path(res.output_path), proj / "renders" / "final.mp4")
        gate_json = json.loads((proj / "renders" / "final.gate.json").read_text(encoding="utf-8"))
        self.assertTrue(gate_json["passed"])
        self.assertEqual([p.name for p in (proj / "renders").glob(".frames_*")], [])  # temp frames cleaned up

    def test_flat_frames_are_rejected_and_quarantined(self):
        proj = write_project(self.tmp / "p")
        with mock.patch.object(renderer_module, "capture_frames", patched_capture("flat")):
            with self.assertRaises(MediaGateError) as ctx:
                HyperFramesRenderer(backend="chrome").render(proj, duration=DUR, width=W, height=H, fps=FPS)
        self.assertIn("not_flat", {c.name for c in ctx.exception.report.failed_checks()})
        self.assertFalse((proj / "renders" / "final.mp4").exists(), "a rejected video must never sit at final.mp4")
        self.assertTrue((proj / "renders" / "final.rejected.mp4").exists())
        self.assertFalse(json.loads((proj / "renders" / "final.gate.json").read_text(encoding="utf-8"))["passed"])

    def test_enforce_gate_false_reports_gate_failed_without_raising(self):
        proj, res = self.render("flat", enforce_gate=False)
        self.assertEqual(res.validation_status, "GATE_FAILED")
        self.assertTrue(res.output_path.endswith("final.rejected.mp4"))
        self.assertFalse(res.gate["passed"])

    def test_unavailable_renderer_raises_and_leaves_no_video(self):
        proj = write_project(self.tmp / "p")
        with mock.patch.object(renderer_module, "capture_frames", side_effect=RenderUnavailableError("no browser")):
            with self.assertRaises(RenderUnavailableError):
                HyperFramesRenderer(backend="chrome").render(proj, duration=DUR, width=W, height=H)
        self.assertEqual(list((proj / "renders").glob("*.mp4")), [])

    def test_stale_video_from_an_earlier_run_is_removed(self):
        proj = write_project(self.tmp / "p")
        stale = proj / "renders" / "final.mp4"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_bytes(b"stale video from an earlier, successful run")
        with mock.patch.object(renderer_module, "capture_frames", side_effect=BrowserCaptureError("boom")):
            with self.assertRaises(BrowserCaptureError):
                HyperFramesRenderer(backend="chrome").render(proj, duration=DUR, width=W, height=H)
        self.assertFalse(stale.exists())

    def test_ffmpeg_failure_is_loud_not_a_fallback_video(self):
        proj = write_project(self.tmp / "p")
        with mock.patch.object(renderer_module, "capture_frames", patched_capture("rich")), \
             mock.patch.object(renderer_module, "render_video_with_ffmpeg", side_effect=FFmpegError("encode failed")):
            with self.assertRaises(FFmpegError):
                HyperFramesRenderer(backend="chrome").render(proj, duration=DUR, width=W, height=H)
        self.assertEqual(list((proj / "renders").glob("*.mp4")), [])

    def test_execution_runtime_is_forwarded_to_capture_and_encode(self):
        seen, runtime = {}, mock.MagicMock()
        proj = write_project(self.tmp / "p")
        with mock.patch.object(renderer_module, "capture_frames", patched_capture("rich", seen)), \
             mock.patch.object(renderer_module, "render_video_with_ffmpeg", side_effect=FFmpegError("stop here")) as enc:
            with self.assertRaises(FFmpegError):
                HyperFramesRenderer(backend="chrome", execution_runtime=runtime).render(
                    proj, duration=DUR, width=W, height=H, fps=FPS)
        self.assertIs(seen["execution_runtime"], runtime)
        self.assertIs(enc.call_args.kwargs["execution_runtime"], runtime)
        self.assertTrue(enc.call_args.kwargs["strict"])  # the real path never uses the lenient fallbacks

    def test_narration_longer_than_video_is_flagged_and_shorter_is_padded(self):
        proj = write_project(self.tmp / "long", narration_seconds=DUR + 3)
        with mock.patch.object(renderer_module, "capture_frames", patched_capture("rich")):
            res = HyperFramesRenderer(backend="chrome").render(proj, duration=DUR, width=W, height=H, fps=FPS)
        self.assertTrue(any("truncated" in w for w in res.warnings), res.warnings)
        self.assertEqual(res.validation_status, "VERIFIED")
        self.assertAlmostEqual(res.duration_seconds, DUR, delta=0.2)

        short = write_project(self.tmp / "short", narration_seconds=1.0)
        with mock.patch.object(renderer_module, "capture_frames", patched_capture("rich")):
            res = HyperFramesRenderer(backend="chrome", enforce_gate=False).render(
                short, duration=DUR, width=W, height=H, fps=FPS)
        self.assertAlmostEqual(res.duration_seconds, DUR, delta=0.2)  # video keeps its length; audio is padded


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class TestPipelineSemantics(_TmpDirTest):
    def pipeline(self, **kw):
        return Pipeline(topic="How GPUs Work", output_dir=self.tmp / "run", offline=True, duration=15, **kw)

    def summary(self):
        return json.loads((self.tmp / "run" / "pipeline_summary.json").read_text(encoding="utf-8"))

    def test_stub_run_is_partial_and_labelled(self):
        self.assertFalse(self.pipeline(render_backend="stub").run())
        s = self.summary()
        self.assertEqual(s["status"], "PARTIAL")
        stage = next(x for x in s["stages"] if x["stage_name"] == "hyperframes_render")
        self.assertEqual(stage["metrics"]["validation_status"], "STUB")
        self.assertIsNone(stage["metrics"]["gate_passed"])
        self.assertTrue((self.tmp / "run" / "renders" / "final.mp4").is_file())

    def test_unavailable_renderer_fails_the_run_with_an_actionable_error(self):
        with mock.patch.object(HyperFramesRenderer, "render", side_effect=RenderUnavailableError("install Chrome")):
            self.assertFalse(self.pipeline().run())
        s = self.summary()
        self.assertEqual(s["status"], "FAILED")
        err = next(x for x in s["stages"] if x["stage_name"] == "hyperframes_render")["error"]
        self.assertIn("RenderUnavailableError", err)
        self.assertIn("install Chrome", err)
        self.assertFalse((self.tmp / "run" / "renders" / "final.mp4").exists())

    def test_gate_rejection_fails_the_run_and_points_at_the_evidence(self):
        report = MediaGateReport(path="x.mp4", passed=False)
        with mock.patch.object(HyperFramesRenderer, "render", side_effect=MediaGateError(report)):
            self.assertFalse(self.pipeline().run())
        stage = next(x for x in self.summary()["stages"] if x["stage_name"] == "hyperframes_render")
        self.assertFalse(stage["success"])
        self.assertIn("renders/final.rejected.mp4", stage["artifacts"])
        self.assertIn("renders/final.gate.json", stage["artifacts"])


_READY = availability()["ready_without_install"] and bool(FFMPEG)


@unittest.skipUnless(_READY, "real-render toolchain not installed (see `python run_harness9.py --check-render`)")
class TestRealBrowserRender(_TmpDirTest):
    """Drives a real headless Chromium over a tiny GSAP composition."""

    def render(self, proj, **kw):
        return HyperFramesRenderer(backend="chrome", **kw).render(proj, duration=DUR, width=W, height=H, fps=FPS)

    def test_real_composition_renders_verified_with_real_motion(self):
        res = self.render(write_project(self.tmp / "ok"))
        self.assertEqual(res.validation_status, "VERIFIED")
        self.assertEqual(res.frames_captured, DUR * FPS)
        m = res.gate["metrics"]
        self.assertEqual(m["flat_frame_ratio"], 0.0)
        self.assertGreater(m["edge_density"], 0.002)
        self.assertGreaterEqual(m["motion_ratio"], 0.5)  # the box really moves across the frame

    def test_frames_differ_over_time(self):
        res = self.render(write_project(self.tmp / "motion"))
        import subprocess
        first, last = self.tmp / "f0.png", self.tmp / "f1.png"
        for t, out in ((0.1, first), (DUR - 0.2, last)):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", res.output_path, "-frames:v", "1", str(out)],
                           check=True)
        self.assertNotEqual(first.read_bytes(), last.read_bytes())

    def test_external_requests_are_blocked_and_reported(self):
        proj = write_project(self.tmp / "ext", extra_html='<img src="https://example.invalid/tracker.png">')
        res = self.render(proj)
        self.assertTrue(any("external request" in w for w in res.warnings), res.warnings)

    def test_composition_without_a_timeline_fails_loudly(self):
        proj = write_project(self.tmp / "notl", main_js="/* forgot to register the timeline */")
        with self.assertRaises(BrowserCaptureError) as ctx:
            self.render(proj)
        self.assertIn("No timelines are registered", str(ctx.exception))
        self.assertEqual(list((proj / "renders").glob("*.mp4")), [])

    def test_missing_image_is_reported(self):
        proj = write_project(self.tmp / "broken", extra_html='<img src="assets/images/does_not_exist.png">')
        res = self.render(proj)
        self.assertTrue(any("failed to load" in w for w in res.warnings), res.warnings)


if __name__ == "__main__":
    unittest.main()
