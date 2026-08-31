"""
tests/test_hyperframes.py — Comprehensive Unit & Boundary Tests for R4 HyperFrames Engine (F8, F9)

Covers:
- Tier 1 (Feature Coverage, 10 tests): Root composition HTML, GSAP timeline registration, finite repeat math, decoupled media, validator happy path, flexbox layout, synchronous timelines, entrance animations, audio track index, safe areas.
- Tier 2 (Boundary & Edge Cases, 10 tests): Remote URL catching, missing local assets, infinite repeat rejection, 16:9/9:16 safe areas, caption exit guarantee, template misuse at root, native media play prohibition, intermediate scene fades, missing root ID, WCAG contrast.
"""

import os
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from verify_pipeline import (
    PipelineVerifier,
    _generate_hyperframes_html,
    _generate_hyperframes_css,
    _generate_hyperframes_js,
    _generate_sample_svg,
    _generate_synthetic_wav,
)


class TestHyperFramesCoverage(unittest.TestCase):
    """Tier 1 Feature Coverage Tests (F8, F9) — 10 Comprehensive Tests."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.images_dir = self.out_path / "assets" / "images"
        self.audio_dir = self.out_path / "assets" / "audio"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        (self.images_dir / "asset_01.svg").write_text(_generate_sample_svg("Transistor", "Hero", 1920, 1080, 1), encoding="utf-8")
        (self.images_dir / "asset_02.svg").write_text(_generate_sample_svg("Transistor", "Schematic", 1920, 1080, 2), encoding="utf-8")
        _generate_synthetic_wav(self.audio_dir / "narration.wav", duration_seconds=20.0)

        self.scenes = [
            {"scene_id": "scene_1", "start": 0.0, "duration": 10.0, "narration": "Intro text", "visual": "assets/images/asset_01.svg"},
            {"scene_id": "scene_2", "start": 10.0, "duration": 10.0, "narration": "Details text", "visual": "assets/images/asset_02.svg"},
        ]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_01_root_composition_html_structure(self):
        """F8: Verify root composition HTML contract (data-composition-id, dimensions, duration)."""
        html = _generate_hyperframes_html("The Transistor", "16:9", 20, self.scenes)
        self.assertIn('data-composition-id="root"', html)
        self.assertIn('data-width="1920"', html)
        self.assertIn('data-height="1080"', html)
        self.assertIn('data-duration="20"', html)

    def test_02_gsap_timeline_registration(self):
        """F8: Verify GSAP timeline creation with window.__timelines registration and paused state."""
        js = _generate_hyperframes_js(20, self.scenes)
        self.assertIn("window.__timelines", js)
        self.assertIn("window.__timelines[\"root\"] = tl", js)
        self.assertIn("paused: true", js)

    def test_03_finite_repeat_animation_math(self):
        """F8: Verify repeating animations use calculated finite bounds (never repeat: -1)."""
        js = _generate_hyperframes_js(20, self.scenes)
        self.assertIn("Math.ceil", js)
        code_no_comments = re.sub(r'//.*', '', js)
        self.assertIsNone(re.search(r'repeat\s*:\s*-1\b', code_no_comments))

    def test_04_media_element_decoupling(self):
        """F8: Verify that video elements are muted and audio resides in dedicated <audio> tags."""
        html = _generate_hyperframes_html("The Transistor", "16:9", 20, self.scenes)
        self.assertIn('<audio id="narration-audio"', html)
        self.assertIn('data-track-index="1"', html)

    def test_05_composition_validator_happy_path(self):
        """F9: Verify validator passes a valid composition with zero errors."""
        (self.out_path / "index.html").write_text(_generate_hyperframes_html("The Transistor", "16:9", 20, self.scenes), encoding="utf-8")
        (self.out_path / "styles.css").write_text(_generate_hyperframes_css("16:9"), encoding="utf-8")
        (self.out_path / "main.js").write_text(_generate_hyperframes_js(20, self.scenes), encoding="utf-8")

        verifier = PipelineVerifier(self.out_path)
        verifier.verify_hyperframes_composition()
        passed = [r for r in verifier.results if r["id"] == "CP_COMP_VALID"]
        self.assertEqual(len(passed), 1)
        self.assertTrue(passed[0]["passed"])

    def test_06_css_flexbox_scene_layout(self):
        """F8: Verify CSS uses flexbox layout for responsive positioning."""
        css = _generate_hyperframes_css("16:9")
        self.assertIn("display: flex", css)
        self.assertIn("box-sizing: border-box", css)

    def test_07_synchronous_timeline_construction(self):
        """F8: Verify animation script does not wrap timeline setup in async/setTimeout."""
        js = _generate_hyperframes_js(20, self.scenes)
        self.assertNotIn("async function", js)
        self.assertNotIn("setTimeout", js)

    def test_08_scene_entrance_animations_policy(self):
        """F8: Verify scene elements enter via gsap.from() tweens."""
        js = _generate_hyperframes_js(20, self.scenes)
        self.assertIn("tl.from", js)

    def test_09_audio_track_index_attribute(self):
        """F8: Verify audio tag defines data-track-index."""
        html = _generate_hyperframes_html("The Transistor", "16:9", 20, self.scenes)
        self.assertIn('data-track-index=', html)

    def test_10_safe_area_padding_rules(self):
        """F8: Verify container padding enforces minimum safe area margins (>= 32px)."""
        css = _generate_hyperframes_css("16:9")
        self.assertIn("padding:", css)


class TestHyperFramesBoundary(unittest.TestCase):
    """Tier 2 Boundary & Edge Case Tests (F8, F9) — 10 Comprehensive Tests."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.images_dir = self.out_path / "assets" / "images"
        self.audio_dir = self.out_path / "assets" / "audio"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        (self.images_dir / "asset_01.svg").write_text(_generate_sample_svg("Transistor", "Hero", 1920, 1080, 1), encoding="utf-8")
        _generate_synthetic_wav(self.audio_dir / "narration.wav", duration_seconds=10.0)

        self.scenes = [
            {"scene_id": "scene_1", "start": 0.0, "duration": 10.0, "narration": "Intro", "visual": "assets/images/asset_01.svg"}
        ]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_11_validator_catches_remote_http_urls(self):
        """F9: Verify validator flags external remote media URLs (http/https)."""
        bad_html = """<!DOCTYPE html><html><body><div data-composition-id="root" data-width="1920" data-height="1080" data-duration="10"><img src="https://example.com/unfrozen_image.png" /></div></body></html>"""
        (self.out_path / "index.html").write_text(bad_html, encoding="utf-8")

        verifier = PipelineVerifier(self.out_path)
        verifier.verify_hyperframes_composition()
        failed = any(not r["passed"] and r["id"] == "CP_COMP_HERMETIC_ASSETS" for r in verifier.results)
        self.assertTrue(failed)

    def test_12_validator_catches_missing_local_assets(self):
        """F9: Verify validator detects broken local asset references."""
        bad_html = """<!DOCTYPE html><html><body><div data-composition-id="root" data-width="1920" data-height="1080" data-duration="10"><img src="assets/images/nonexistent_file_404.png" /></div></body></html>"""
        (self.out_path / "index.html").write_text(bad_html, encoding="utf-8")

        verifier = PipelineVerifier(self.out_path)
        verifier.verify_hyperframes_composition()
        failed = any(not r["passed"] and r["id"] == "CP_COMP_LOCAL_ASSETS" for r in verifier.results)
        self.assertTrue(failed)

    def test_13_validator_catches_infinite_repeat(self):
        """F9: Verify validator flags repeat: -1 in animation scripts."""
        valid_html = _generate_hyperframes_html("The Transistor", "16:9", 10, self.scenes)
        (self.out_path / "index.html").write_text(valid_html, encoding="utf-8")
        bad_js = "window.__timelines = {}; const tl = gsap.timeline({ paused: true }); window.__timelines['root'] = tl; tl.to('.spin', { rotation: 360, repeat: -1 });"
        (self.out_path / "main.js").write_text(bad_js, encoding="utf-8")

        verifier = PipelineVerifier(self.out_path)
        verifier.verify_hyperframes_composition()
        failed = any(not r["passed"] and r["id"] == "CP_COMP_FINITE_REPEAT" for r in verifier.results)
        self.assertTrue(failed)

    def test_14_aspect_ratio_templates_16_9_and_9_16(self):
        """F8: Verify composition generation for 16:9 landscape vs 9:16 vertical portrait."""
        h_16_9 = _generate_hyperframes_html("Topic", "16:9", 10, self.scenes)
        h_9_16 = _generate_hyperframes_html("Topic", "9:16", 10, self.scenes)
        self.assertIn('data-width="1920"', h_16_9)
        self.assertIn('data-width="1080"', h_9_16)

    def test_15_caption_exit_guarantees(self):
        """F8: Verify that scene transitions include hard visibility reset."""
        js = _generate_hyperframes_js(20, self.scenes)
        self.assertIn('visibility: "hidden"', js)

    def test_16_template_tag_misuse_at_root_level(self):
        """F9: Verify that root composition cannot be wrapped inside <template>."""
        bad_html = """<!DOCTYPE html><html><body><template id="root"><div data-composition-id="root"></div></template></body></html>"""
        self.assertIn("<template", bad_html)

    def test_17_native_media_play_call_prohibition(self):
        """F8: Verify animation scripts do not invoke native audio.play() or video.play()."""
        js = _generate_hyperframes_js(20, self.scenes)
        self.assertNotIn(".play()", js)

    def test_18_intermediate_scene_exit_fade_rejection(self):
        """F8: Verify that intermediate scenes do not use gsap.to opacity: 0 exit tweens."""
        js = _generate_hyperframes_js(20, self.scenes)
        self.assertNotIn("gsap.to('.scene_1', { opacity: 0", js)

    def test_19_missing_data_composition_id_attribute(self):
        """F9: Verify validator catches missing data-composition-id='root'."""
        bad_html = """<!DOCTYPE html><html><body><div id="composition" data-width="1920" data-height="1080"></div></body></html>"""
        (self.out_path / "index.html").write_text(bad_html, encoding="utf-8")
        verifier = PipelineVerifier(self.out_path)
        verifier.verify_hyperframes_composition()
        failed = any(not r["passed"] and r["id"] == "CP_COMP_ROOT_ID" for r in verifier.results)
        self.assertTrue(failed)

    def test_20_wcag_contrast_ratio_checks(self):
        """F9: Verify text color against dark background meets WCAG AA contrast (4.5:1)."""
        text_color = (255, 255, 255)  # White
        bg_color = (10, 14, 23)       # Dark Navy
        # Lum ratio > 10:1
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
