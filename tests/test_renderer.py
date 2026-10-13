"""Production renderer behavior checks for Harness 9."""

import shutil
import tempfile
import unittest
from pathlib import Path

from src.hyperframes.generator import HyperFramesGenerator
from src.hyperframes.renderer import HyperFramesRenderer


class TestRendererConfiguration(unittest.TestCase):
    def test_default_backend_is_real_chrome_and_unknown_backends_are_rejected(self):
        self.assertEqual(HyperFramesRenderer().backend, "chrome")
        with self.assertRaises(ValueError):
            HyperFramesRenderer(backend="placeholder")


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for the explicit stub render test")
class TestExplicitStubRender(unittest.TestCase):
    def test_stub_output_is_marked_non_verified_and_has_no_passed_gate(self):
        with tempfile.TemporaryDirectory(prefix="h9_stub_render_") as temp_dir:
            project_dir = Path(temp_dir)
            HyperFramesGenerator().generate_composition(
                topic="Renderer stub test",
                storyboard=[{
                    "scene_id": "scene_1",
                    "start_time": 0,
                    "duration": 1,
                    "title": "Explicit test frame",
                    "narration_text": "This placeholder is an explicitly labelled test render.",
                    "visual_asset_path": "assets/images/missing-test-fixture.svg",
                }],
                output_dir=project_dir,
                duration=1,
            )

            result = HyperFramesRenderer(backend="stub", fps=5).render(
                project_dir=project_dir,
                duration=1,
                width=160,
                height=90,
                fps=5,
            )

            self.assertEqual(result.validation_status, "STUB")
            self.assertIsNone(result.gate)
            self.assertTrue(any("NOT a real video" in warning for warning in result.warnings))
            self.assertTrue(Path(result.output_path).is_file())


if __name__ == "__main__":
    unittest.main()
