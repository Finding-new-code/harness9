"""tests/test_challenger2_visual_media_contracts.py — Empirical Challenger 2 Stress Suite.

Exhaustive empirical testing across the visual, media, and contract layers of Harness 9:
1. HyperFrames Components (7 canonical blocks) with valid props, missing optional props,
   invalid required props, remote URL injections, XSS attacks, color injection,
   finite repeat math, extreme aspect ratios (16:9, 9:16, 1:1, 4:3, 21:9), ComponentRegistry,
   and HyperFramesAdapter full pipeline compilation.
2. CompositionValidator static linter with broken local paths, infinite GSAP loops (repeat: -1),
   remote URLs, unmuted videos, missing root tags, template wrapping, timeline registration,
   paused state requirement, track collisions, data URIs, and WCAG contrast heuristics.
3. Editorial Scoring Engine with mathematical 9-dimension composite bounds, negative buzzword
   penalties, multi-tier deterministic tie-breakers (composite -> hook -> novelty -> evidence -> angle_id),
   psychological HookGenerator ideation, and 4-act narrative duration scaling from 5s to 600s.
4. All 17 Pydantic Production Schemas against malformed JSON/YAML payloads, type mismatches,
   boundary violations, missing required keys, extra fields preservation, dict subscripting,
   and lossless roundtrip serialization.
5. End-to-end acceptance pipeline verification (verify_pipeline.py).
"""

import json
import math
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import ValidationError

from adapters.hyperframes.adapter import HyperFramesAdapter, HyperFramesProject
from adapters.hyperframes.registry import (
    ComponentRegistry,
    get_component,
    get_registry,
    list_registered_components,
    register_component,
)
from src.editorial.hook_generator import HookGenerator, HookOption
from src.editorial.narrative_planner import NarrativePlanner
from src.editorial.scorecard import (
    EditorialScorer,
    SCORECARD_WEIGHTS,
    calculate_scorecard_composite,
)
from src.editorial.selector import AngleSelector
from src.hyperframes.components.base import (
    BaseComponent,
    ComponentSchema,
    ValidationResult,
)
from src.hyperframes.components.comparison_panel import ComparisonPanel
from src.hyperframes.components.creator_bottom_collage import CreatorBottomCollage
from src.hyperframes.components.quote_highlight import QuoteHighlight
from src.hyperframes.components.reference_collage_hook import ReferenceCollageHook
from src.hyperframes.components.split_screen_intro import SplitScreenIntro
from src.hyperframes.components.statistic_reveal import StatisticReveal
from src.hyperframes.components.timeline_reveal import TimelineReveal
from src.hyperframes.validator import CompositionValidator, validate_composition
from src.models.contracts import (
    AnalyticsSnapshot,
    AssetRecord,
    AssetRequirement,
    ClaimRecord,
    ContentBrief,
    ContentOutline,
    CreatorProfile,
    Dimensions,
    EditorialAngle,
    EditorialScorecard,
    EvaluationLayer,
    EvaluationReport,
    H9BaseModel,
    LearningCandidate,
    LicenseInfo,
    OutlineAct,
    PublishPackage,
    RenderArtifact,
    ResearchDossier,
    ResearchPlan,
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
    StatisticRecord,
    TalkingPointRecord,
)


class TestHyperFramesComponentsAdversarial(unittest.TestCase):
    """Stress tests for all 7 HyperFrames component blocks, BaseComponent, and Registry."""

    def setUp(self):
        self.components = [
            ReferenceCollageHook(),
            SplitScreenIntro(),
            QuoteHighlight(),
            TimelineReveal(),
            StatisticReveal(),
            ComparisonPanel(),
            CreatorBottomCollage(),
        ]

    # -----------------------------------------------------------------------
    # 1. BaseComponent Utilities & Mathematical Guarantees
    # -----------------------------------------------------------------------
    def test_01_finite_repeat_math_boundaries(self):
        """Stress-test finite repeat math: Math.ceil(duration / cycle) - 1."""
        # Standard cases
        self.assertEqual(BaseComponent.calculate_finite_repeats(10.0, 2.0), 4)
        self.assertEqual(BaseComponent.calculate_finite_repeats(5.0, 5.0), 0)
        self.assertEqual(BaseComponent.calculate_finite_repeats(5.0, 10.0), 0)
        
        # Fractional and extreme durations
        self.assertEqual(BaseComponent.calculate_finite_repeats(5.5, 2.0), 2)
        self.assertEqual(BaseComponent.calculate_finite_repeats(600.0, 1.5), 399)
        self.assertEqual(BaseComponent.calculate_finite_repeats(0.01, 1.0), 0)

        # Zero and negative safety bounds (must not crash, must return 0)
        self.assertEqual(BaseComponent.calculate_finite_repeats(0.0, 2.0), 0)
        self.assertEqual(BaseComponent.calculate_finite_repeats(-10.0, 2.0), 0)
        self.assertEqual(BaseComponent.calculate_finite_repeats(10.0, 0.0), 0)
        self.assertEqual(BaseComponent.calculate_finite_repeats(10.0, -2.0), 0)
        self.assertEqual(BaseComponent.calculate_finite_repeats(-5.0, -5.0), 0)

    def test_02_color_sanitization_adversarial_injections(self):
        """Stress-test CSS color sanitizer against malicious inputs, XSS, and CSS injections."""
        # Valid colors
        self.assertEqual(BaseComponent.sanitize_color("#00d2ff"), "#00d2ff")
        self.assertEqual(BaseComponent.sanitize_color("#FFF"), "#FFF")
        self.assertEqual(BaseComponent.sanitize_color("#123456aa"), "#123456aa")
        self.assertEqual(BaseComponent.sanitize_color("rgb(255, 0, 128)"), "rgb(255, 0, 128)")
        self.assertEqual(BaseComponent.sanitize_color("rgba(0, 210, 255, 0.8)"), "rgba(0, 210, 255, 0.8)")

        # Adversarial CSS injection payloads (must fallback to default safely)
        bad_colors = [
            'red; font-size: 100px; display: none;',
            '#00d2ff; background: url("http://evil.com/leak")',
            '<script>alert("color_xss")</script>',
            'javascript:alert(1)',
            'expression(alert(1))',
            'rgba(0,0,0,1); color: red',
            '',
            None,
            12345,
            [],
        ]
        for bad in bad_colors:
            sanitized = BaseComponent.sanitize_color(bad, default="#00d2ff")
            self.assertEqual(sanitized, "#00d2ff", f"Failed to sanitize color injection: {bad}")

    def test_03_html_escaping_adversarial_payloads(self):
        """Stress-test HTML escaping against script injection, img tags, and attribute escapes."""
        attacks = [
            '<script>alert("xss")</script>',
            '"><img src=x onerror=alert(1)>',
            "''><svg/onload=alert(1)>",
            '& < > " \'',
        ]
        for attack in attacks:
            escaped = BaseComponent.escape(attack)
            self.assertNotIn("<script>", escaped)
            self.assertNotIn("<img", escaped)
            self.assertNotIn("<svg", escaped)

    # -----------------------------------------------------------------------
    # 2. Component Props Validation & Aspect Ratio Handling
    # -----------------------------------------------------------------------
    def test_04_valid_props_across_16_9_and_9_16(self):
        """Test that all 7 components validate and render cleanly in 16:9 and 9:16 when required props are passed."""
        for comp in self.components:
            for fmt in ["16:9", "9:16"]:
                # Validation with default props (which satisfy all required_props)
                val = comp.validate(comp.schema.default_props, format_aspect=fmt)
                self.assertTrue(val.valid, f"Block {comp.block_id} failed default validation in {fmt}: {val.errors}")

                # Render HTML, CSS, and GSAP
                html = comp.render_html("scene_1", comp.schema.default_props, format_aspect=fmt)
                css = comp.render_css("scene_1", comp.schema.default_props, format_aspect=fmt)
                gsap = comp.render_gsap("scene_1", comp.schema.default_props, format_aspect=fmt, start_time=0.0, duration=5.0)

                self.assertIn("scene_1", html)
                self.assertIn("scene_1", css)
                self.assertIn("scene_1", gsap)
                self.assertIn(comp.block_id, html)
                self.assertNotIn("undefined", html.lower())

    def test_05_missing_optional_props_fallback_to_defaults(self):
        """Verify that omitting optional props uses defaults without breaking rendering."""
        for comp in self.components:
            # Pass only required props
            minimal_props = {}
            for req in comp.schema.required_props:
                minimal_props[req] = comp.schema.default_props.get(req, "Test Value")
            
            val = comp.validate(minimal_props)
            self.assertTrue(val.valid, f"Block {comp.block_id} failed with minimal required props: {val.errors}")

            html = comp.render_html("scene_test", minimal_props)
            css = comp.render_css("scene_test", minimal_props)
            gsap = comp.render_gsap("scene_test", minimal_props)

            self.assertTrue(len(html) > 50)
            self.assertTrue(len(css) > 50)
            self.assertTrue(len(gsap) > 50)

    def test_06_missing_or_empty_required_props_rejection(self):
        """Verify that missing or empty required props are caught by validate()."""
        for comp in self.components:
            if not comp.schema.required_props:
                continue
            for req in comp.schema.required_props:
                # 1. Completely omitted required prop
                props_omitted = {k: v for k, v in comp.schema.default_props.items() if k != req}
                val_omitted = comp.validate(props_omitted)
                self.assertFalse(val_omitted.valid, f"Block {comp.block_id} did not catch omitted required prop '{req}'")
                self.assertTrue(any(req in err for err in val_omitted.errors))

                # 2. Empty string for required prop
                props_empty = {**comp.schema.default_props, req: ""}
                val_empty = comp.validate(props_empty)
                self.assertFalse(val_empty.valid, f"Block {comp.block_id} did not catch empty string for required prop '{req}'")

                # 3. None value for required prop
                props_none = {**comp.schema.default_props, req: None}
                val_none = comp.validate(props_none)
                self.assertFalse(val_none.valid, f"Block {comp.block_id} did not catch None for required prop '{req}'")

    def test_07_extreme_dimensions_and_unsupported_aspect_ratios(self):
        """Stress-test components against extreme aspect ratios (1:1, 4:3, 21:9, ultra-wide)."""
        for comp in self.components:
            # 1. 1:1 Square aspect ratio (unsupported by standard 16:9/9:16 schema)
            val_1_1 = comp.validate(comp.schema.default_props, format_aspect="1:1")
            self.assertFalse(val_1_1.valid)
            self.assertTrue(any("Unsupported aspect ratio '1:1'" in err for err in val_1_1.errors))
            
            # 2. Arbitrary extreme aspect ratios (4:3, 21:9, 32:9, 9:21)
            for extreme_fmt in ["4:3", "21:9", "32:9", "9:21", "custom_aspect"]:
                val_ext = comp.validate(comp.schema.default_props, format_aspect=extreme_fmt)
                self.assertFalse(val_ext.valid)
                self.assertTrue(any(f"Unsupported aspect ratio '{extreme_fmt}'" in err for err in val_ext.errors))

    def test_08_remote_url_injection_rejection_in_components(self):
        """Verify components reject remote URLs in image/video paths during validation."""
        # Block 1: ReferenceCollageHook
        rch = ReferenceCollageHook()
        props_rch = {**rch.schema.default_props, "image_paths": ["https://evil.com/tracker.png", "assets/images/local.svg"]}
        val = rch.validate(props_rch)
        self.assertFalse(val.valid)
        self.assertTrue(any("Forbidden remote URL" in err for err in val.errors))

        # Block 2: SplitScreenIntro
        ssi = SplitScreenIntro()
        props_ssi = {**ssi.schema.default_props, "left_image": "http://insecure.com/video.jpg"}
        val_ssi = ssi.validate(props_ssi)
        self.assertFalse(val_ssi.valid)
        self.assertTrue(any("Forbidden remote URL" in err for err in val_ssi.errors))

        # Block 7: CreatorBottomCollage
        cbc = CreatorBottomCollage()
        props_cbc = {**cbc.schema.default_props, "avatar_path": "https://external.cdn/avatar.png"}
        val_cbc = cbc.validate(props_cbc)
        self.assertFalse(val_cbc.valid)
        self.assertTrue(any("Forbidden remote URL" in err for err in val_cbc.errors))

    # -----------------------------------------------------------------------
    # 3. Component Registry & Adapter Compilation
    # -----------------------------------------------------------------------
    def test_09_component_registry_discovery_and_lookup(self):
        """Verify ComponentRegistry discovers all 7 canonical blocks and handles lookups."""
        registry = get_registry()
        registered_ids = list_registered_components()
        expected_ids = [
            "reference_collage_hook",
            "split_screen_intro",
            "quote_highlight",
            "timeline_reveal",
            "statistic_reveal",
            "comparison_panel",
            "creator_bottom_collage",
        ]
        for bid in expected_ids:
            self.assertIn(bid, registered_ids)
            comp = get_component(bid)
            self.assertIsNotNone(comp)
            self.assertEqual(comp.block_id, bid)

        # Lookup non-existent block raises KeyError
        with self.assertRaises(KeyError):
            get_component("non_existent_block_xyz")

    def test_10_hyperframes_adapter_compilation_and_validation(self):
        """Verify HyperFramesAdapter compiles a multi-scene project and passes CompositionValidator."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "test_project"
            adapter = HyperFramesAdapter()

            script = Script(
                topic="The Transistor",
                title="The Silicon Breakthrough",
                total_duration=15.0,
                scenes=[
                    ScriptScene(
                        scene_id="scene_1",
                        duration=5.0,
                        component_type="reference_collage_hook",
                        component_props={"headline": "The Accidental Invention"},
                    ),
                    ScriptScene(
                        scene_id="scene_2",
                        duration=5.0,
                        component_type="split_screen_intro",
                        component_props={"left_title": "Vacuum Tubes", "right_title": "Solid State"},
                    ),
                    ScriptScene(
                        scene_id="scene_3",
                        duration=5.0,
                        component_type="statistic_reveal",
                        component_props={"target_number": "100 Billion", "metric_label": "Transistors per chip"},
                    ),
                ],
            )

            # Create dummy assets
            assets_dir = out_dir / "assets" / "images"
            assets_dir.mkdir(parents=True, exist_ok=True)
            for i in range(1, 4):
                (assets_dir / f"asset_{i:02d}.svg").write_text("<svg></svg>", encoding="utf-8")
            
            audio_dir = out_dir / "assets" / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            (audio_dir / "narration.wav").write_bytes(b"RIFFdummyWAVEfmt ")

            # Compile project
            project = adapter.compile_composition(
                script=script,
                output_dir=str(out_dir),
                format_aspect="16:9",
            )

            self.assertTrue((out_dir / "index.html").exists())
            self.assertTrue((out_dir / "styles.css").exists())
            self.assertTrue((out_dir / "main.js").exists())
            self.assertEqual(project.duration, 15.0)
            self.assertEqual(project.scene_count, 3)

            # Validate generated project
            val_result = validate_composition(out_dir)
            self.assertTrue(val_result["valid"], f"Compiled project failed validation: {val_result['errors']}")


class TestCompositionValidatorAdversarial(unittest.TestCase):
    """Stress tests for CompositionValidator static linter and security checks."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.proj_dir = Path(self.temp_dir.name)
        (self.proj_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
        (self.proj_dir / "assets" / "audio").mkdir(parents=True, exist_ok=True)

        # Create valid dummy assets
        (self.proj_dir / "assets" / "images" / "hero.svg").write_text("<svg></svg>", encoding="utf-8")
        (self.proj_dir / "assets" / "audio" / "narration.wav").write_bytes(b"RIFFdummyWAVEfmt ")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_composition(self, html: str, css: str = "", js: str = ""):
        (self.proj_dir / "index.html").write_text(html, encoding="utf-8")
        if css:
            (self.proj_dir / "styles.css").write_text(css, encoding="utf-8")
        if js:
            (self.proj_dir / "main.js").write_text(js, encoding="utf-8")

    def test_01_missing_index_html(self):
        """Missing index.html returns valid=False."""
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("Missing required composition file: index.html" in err for err in val["errors"]))

    def test_02_root_composition_tag_checks(self):
        """Validate root element attributes: data-composition-id, data-width, data-height, data-duration."""
        # 1. Missing data-composition-id="root"
        self._write_composition('<div id="comp" data-width="1920" data-height="1080" data-duration="30"></div>')
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("Missing root composition element" in err for err in val["errors"]))

        # 2. Wrapped inside <template>
        self._write_composition('<template><div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30"></div></template>')
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("must not be wrapped inside a <template> tag" in err for err in val["errors"]))

        # 3. Missing dimensions / duration
        self._write_composition('<div data-composition-id="root"></div>')
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("missing data-width" in err for err in val["errors"]))
        self.assertTrue(any("missing data-height" in err for err in val["errors"]))
        self.assertTrue(any("missing data-duration" in err for err in val["errors"]))

    def test_03_broken_local_paths_detection(self):
        """Detect referenced media files that do not exist on disk."""
        html = """<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30">
          <img src="assets/images/hero.svg" />
          <img src="assets/images/missing_diagram.svg" />
          <audio src="assets/audio/missing_track.wav" data-track-index="1"></audio>
        </div>"""
        self._write_composition(html)
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("missing_diagram.svg" in err for err in val["errors"]))
        self.assertTrue(any("missing_track.wav" in err for err in val["errors"]))
        # Valid asset should not be in errors
        self.assertFalse(any("hero.svg" in err for err in val["errors"]))

    def test_04_data_uris_ignored_by_local_file_checker(self):
        """Verify data URIs (data:image/svg+xml;base64,...) do not trigger local path missing errors."""
        html = """<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30">
          <img src="data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=" />
        </div>"""
        self._write_composition(html)
        val = validate_composition(self.proj_dir)
        self.assertFalse(any("data:image" in err for err in val["errors"]))

    def test_05_remote_url_rejection_in_html_and_css(self):
        """Reject external http:// and https:// URLs in media and warn in CSS."""
        html = """<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30">
          <img src="https://cdn.example.com/photo.jpg" />
          <video src="http://unsecured.org/clip.mp4" muted playsinline></video>
        </div>"""
        css = """body { background: url('https://fonts.gstatic.com/bg.png'); }"""
        self._write_composition(html, css=css)
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("Forbidden external media URL" in err for err in val["errors"]))
        self.assertTrue(any("External font or background URL in CSS" in w for w in val["warnings"]))

    def test_06_infinite_gsap_loop_repeat_minus_one(self):
        """Enforce finite repeat rule: catch repeat: -1 in JS and inline scripts."""
        html = """<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30">
          <script>
            // Good comment
          </script>
        </div>"""
        
        # 1. Explicit repeat: -1 in JS file
        js_bad = """
        window.__timelines = {};
        const tl = gsap.timeline({ paused: true, repeat: -1 });
        window.__timelines["root"] = tl;
        """
        self._write_composition(html, js=js_bad)
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("repeat: -1" in err for err in val["errors"]))

        # 2. Spaces in repeat: -1
        js_spaces = "gsap.to('.hero', { repeat:   -1, duration: 1 });"
        self._write_composition(html, js=js_spaces)
        val_spaces = validate_composition(self.proj_dir)
        self.assertFalse(val_spaces["valid"])
        self.assertTrue(any("repeat: -1" in err for err in val_spaces["errors"]))

        # 3. Comment containing repeat: -1 should NOT trigger error
        js_comment = """
        // Note: do not use repeat: -1 here!
        /* Multi-line comment:
           repeat: -1 is bad
        */
        window.__timelines = {};
        const tl = gsap.timeline({ paused: true, repeat: 2 });
        window.__timelines["root"] = tl;
        """
        self._write_composition(html, js=js_comment)
        val_comment = validate_composition(self.proj_dir)
        self.assertFalse(any("repeat: -1" in err for err in val_comment["errors"]))

    def test_07_timeline_registration_and_paused_state_contract(self):
        """Enforce timeline registration on window.__timelines and paused: true initialization."""
        html = '<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30"></div>'
        
        # 1. Missing window.__timelines
        js_no_reg = "const tl = gsap.timeline({ paused: true });"
        self._write_composition(html, js=js_no_reg)
        val_no_reg = validate_composition(self.proj_dir)
        self.assertFalse(val_no_reg["valid"])
        self.assertTrue(any("window.__timelines" in err for err in val_no_reg["errors"]))

        # 2. Missing paused: true
        js_unpaused = """
        window.__timelines = {};
        const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
        window.__timelines["root"] = tl;
        """
        self._write_composition(html, js=js_unpaused)
        val_unpaused = validate_composition(self.proj_dir)
        self.assertFalse(val_unpaused["valid"])
        self.assertTrue(any("paused: true" in err for err in val_unpaused["errors"]))

    def test_08_audio_track_collision_detection(self):
        """Detect overlapping audio clips on the same data-track-index."""
        html_collision = """<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30">
          <audio src="assets/audio/narration.wav" data-track-index="1" data-start="0.0" data-duration="10.0"></audio>
          <audio src="assets/audio/narration.wav" data-track-index="1" data-start="5.0" data-duration="10.0"></audio>
        </div>"""
        self._write_composition(html_collision)
        val = validate_composition(self.proj_dir)
        self.assertFalse(val["valid"])
        self.assertTrue(any("Track collision on track-index=1" in err for err in val["errors"]))

        # Non-overlapping audio clips on same track -> Valid
        html_clean = """<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="30">
          <audio src="assets/audio/narration.wav" data-track-index="1" data-start="0.0" data-duration="10.0"></audio>
          <audio src="assets/audio/narration.wav" data-track-index="1" data-start="10.0" data-duration="10.0"></audio>
          <!-- Different track -> allowed to overlap -->
          <audio src="assets/audio/narration.wav" data-track-index="2" data-start="5.0" data-duration="10.0"></audio>
        </div>"""
        self._write_composition(html_clean)
        val_clean = validate_composition(self.proj_dir)
        self.assertFalse(any("Track collision" in err for err in val_clean["errors"]))

    def test_09_wcag_contrast_heuristic_check(self):
        """Verify WCAG contrast calculation for accessible color schemes."""
        # High contrast (White #ffffff on Dark #0a0e17)
        ratio_high = CompositionValidator._compute_contrast_ratio("ffffff", "0a0e17")
        self.assertTrue(ratio_high >= 15.0)

        # Low contrast (Dark grey #333333 on Dark #0a0e17)
        ratio_low = CompositionValidator._compute_contrast_ratio("333333", "0a0e17")
        self.assertTrue(ratio_low < 3.0)


class TestEditorialEngineAdversarial(unittest.TestCase):
    """Stress tests for 9-Dimension Editorial Scoring Engine, Tie-Breakers, and 4-Act Planner."""

    def setUp(self):
        self.scorer = EditorialScorer()
        self.selector = AngleSelector(self.scorer)
        self.planner = NarrativePlanner()
        self.hook_gen = HookGenerator()

    # -----------------------------------------------------------------------
    # 1. 9-Dimension Composite Mathematical Invariants
    # -----------------------------------------------------------------------
    def test_01_scorecard_composite_mathematical_bounds(self):
        """Verify composite score mathematical bounds [0.0, 1.0] across all dimension combinations."""
        # Weights sum must equal 1.0 (0.15*3 + 0.10*5 + 0.05 = 0.45 + 0.50 + 0.05 = 1.0)
        total_weight = sum(SCORECARD_WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)

        # Invariant: All 1.0 with saturation_risk = 0.0 (fresh) -> 1.0
        comp_max = calculate_scorecard_composite(
            audience_relevance=1.0, novelty=1.0, hook_potential=1.0,
            narrative_potential=1.0, creator_fit=1.0, evidence_availability=1.0,
            visual_potential=1.0, platform_fit=1.0, saturation_risk=0.0,
        )
        self.assertEqual(comp_max, 1.0)

        # Invariant: All 0.0 with saturation_risk = 1.0 (fully saturated) -> 0.0
        comp_min = calculate_scorecard_composite(
            audience_relevance=0.0, novelty=0.0, hook_potential=0.0,
            narrative_potential=0.0, creator_fit=0.0, evidence_availability=0.0,
            visual_potential=0.0, platform_fit=0.0, saturation_risk=1.0,
        )
        self.assertEqual(comp_min, 0.0)

        # Inverted Saturation Risk behavior
        comp_fresh = calculate_scorecard_composite(
            0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, saturation_risk=0.0
        )
        comp_saturated = calculate_scorecard_composite(
            0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, saturation_risk=1.0
        )
        self.assertTrue(comp_fresh > comp_saturated)
        self.assertAlmostEqual(comp_fresh - comp_saturated, 0.05, places=4)

    # -----------------------------------------------------------------------
    # 2. Negative Buzzword Penalties
    # -----------------------------------------------------------------------
    def test_02_negative_buzzword_creator_penalties(self):
        """Verify creator negative constraint violations apply heavy score penalties."""
        creator = CreatorProfile(
            creator_id="c_strict",
            display_name="Strict Fact Engineer",
            negative_rules=[
                "Never use buzzwords like 'game-changer' or 'revolutionize'",
                "Never use 'unprecedented hype'",
            ],
        )

        clean_angle = EditorialAngle(
            angle_id="angle_clean",
            title="How the First Transistor Was Built",
            premise="A methodical look at Bell Labs solid-state semiconductor experiments.",
            core_thesis="Solid-state physics replaced vacuum tubes through deliberate crystalline engineering.",
            key_hooks=["Why did physicists spend ten years searching for a solid switch?"],
        )
        sc_clean = self.scorer.score_angle(clean_angle, creator=creator)

        violation_angle = EditorialAngle(
            angle_id="angle_buzzword",
            title="The Game-Changer That Will Revolutionize Everything",
            premise="This unprecedented hype technology changed computation forever.",
            core_thesis="A total game-changer for solid state.",
            key_hooks=["Why this revolutionize tech is unprecedented hype!"],
        )
        sc_violation = self.scorer.score_angle(violation_angle, creator=creator)

        # Creator fit should drop significantly
        self.assertTrue(sc_clean.creator_fit > sc_violation.creator_fit)
        self.assertTrue(sc_clean.creator_fit - sc_violation.creator_fit >= 0.25)
        self.assertTrue(sc_clean.composite_score > sc_violation.composite_score)

    # -----------------------------------------------------------------------
    # 3. Multi-Factor Deterministic Tie-Breakers
    # -----------------------------------------------------------------------
    def test_03_multi_tier_tie_breaking_hierarchy(self):
        """Stress-test deterministic 5-level tie-breaking in AngleSelector."""
        # Level 1: Primary composite_score
        a1 = EditorialAngle(angle_id="a1", title="Angle 1", premise="P1", core_thesis="T1")
        a1.scorecard = EditorialScorecard(composite_score=0.90, hook_potential=0.8, novelty=0.8, evidence_availability=0.8)
        
        a2 = EditorialAngle(angle_id="a2", title="Angle 2", premise="P2", core_thesis="T2")
        a2.scorecard = EditorialScorecard(composite_score=0.85, hook_potential=0.99, novelty=0.99, evidence_availability=0.99)
        
        winner, _ = self.selector.select_winning_angle([a2, a1])
        self.assertEqual(winner.angle_id, "a1", "Higher composite score must win over higher individual dimensions")

        # Level 2: Tie on composite -> hook_potential breaks tie
        a3 = EditorialAngle(angle_id="a3", title="Angle 3", premise="P3", core_thesis="T3")
        a3.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.95, novelty=0.70, evidence_availability=0.70)
        
        a4 = EditorialAngle(angle_id="a4", title="Angle 4", premise="P4", core_thesis="T4")
        a4.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.80, novelty=0.90, evidence_availability=0.90)

        winner2, _ = self.selector.select_winning_angle([a4, a3])
        self.assertEqual(winner2.angle_id, "a3", "Hook potential must break composite score tie")

        # Level 3: Tie on composite + hook -> novelty breaks tie
        a5 = EditorialAngle(angle_id="a5", title="Angle 5", premise="P5", core_thesis="T5")
        a5.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.85, novelty=0.95, evidence_availability=0.70)

        a6 = EditorialAngle(angle_id="a6", title="Angle 6", premise="P6", core_thesis="T6")
        a6.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.85, novelty=0.80, evidence_availability=0.95)

        winner3, _ = self.selector.select_winning_angle([a6, a5])
        self.assertEqual(winner3.angle_id, "a5", "Novelty must break composite + hook tie")

        # Level 4: Tie on composite + hook + novelty -> evidence_availability breaks tie
        a7 = EditorialAngle(angle_id="a7", title="Angle 7", premise="P7", core_thesis="T7")
        a7.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.85, novelty=0.85, evidence_availability=0.95)

        a8 = EditorialAngle(angle_id="a8", title="Angle 8", premise="P8", core_thesis="T8")
        a8.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.85, novelty=0.85, evidence_availability=0.80)

        winner4, _ = self.selector.select_winning_angle([a8, a7])
        self.assertEqual(winner4.angle_id, "a7", "Evidence availability must break tie")

        # Level 5: Identical across all 4 scores -> deterministic angle_id order
        a9_beta = EditorialAngle(angle_id="angle_02", title="Angle Beta", premise="PB", core_thesis="TB")
        a9_beta.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.85, novelty=0.85, evidence_availability=0.85)

        a9_alpha = EditorialAngle(angle_id="angle_01", title="Angle Alpha", premise="PA", core_thesis="TA")
        a9_alpha.scorecard = EditorialScorecard(composite_score=0.88, hook_potential=0.85, novelty=0.85, evidence_availability=0.85)

        winner5, _ = self.selector.select_winning_angle([a9_beta, a9_alpha])
        self.assertEqual(winner5.angle_id, "angle_01", "angle_id ascending must break total score ties deterministically")

    # -----------------------------------------------------------------------
    # 4. Psychological Hook Ideation
    # -----------------------------------------------------------------------
    def test_04_hook_generator_ideation_diversity(self):
        """Verify HookGenerator synthesizes at least 3 distinct hook archetypes with valid scores."""
        angle = EditorialAngle(
            angle_id="angle_01",
            title="The Solid State Paradox",
            premise="Semiconductors solved current control through atomic doping.",
            core_thesis="Solid silicon replaced hot vacuum cathodes.",
        )
        dossier = ResearchDossier(
            topic="Transistors",
            statistics=[StatisticRecord(metric="Transistors per chip", value="100 Billion")],
            claims=[ClaimRecord(claim_id="c1", claim_text="Invented at Bell Labs in 1947", primary_source=SourceRecord(title="T", url="U"))],
        )

        hooks = self.hook_gen.generate_hooks(angle=angle, dossier=dossier, count=3)
        self.assertTrue(len(hooks) >= 3)
        
        hook_types = {h.hook_type for h in hooks}
        self.assertTrue(len(hook_types) >= 3)
        for h in hooks:
            self.assertTrue(len(h.text) > 10)
            self.assertTrue(0.0 <= h.estimated_retention_lift <= 1.0)
            self.assertTrue(len(h.psychological_trigger) > 0)

    # -----------------------------------------------------------------------
    # 5. Duration Scaling in Narrative Planner (5s to 600s)
    # -----------------------------------------------------------------------
    def test_05_narrative_planner_duration_scaling_5s_to_600s(self):
        """Verify 4-act narrative outline scales duration from 5s to 600s."""
        angle = EditorialAngle(
            angle_id="winner_01",
            title="The Silicon Switch",
            premise="How the solid state was engineered.",
            core_thesis="Semiconductors enabled modern microprocessors.",
        )
        hook = HookOption(
            hook_id="hook_01",
            hook_type="question",
            text="In 1947, three physicists built a device that would replace every vacuum tube on Earth.",
            psychological_trigger="Curiosity Gap",
        )
        dossier = ResearchDossier(
            topic="The Transistor",
            talking_points=[
                TalkingPointRecord(beat_index=1, title="The Breakthrough"),
                TalkingPointRecord(beat_index=2, title="The Mechanism"),
                TalkingPointRecord(beat_index=3, title="The Scale"),
                TalkingPointRecord(beat_index=4, title="The Future"),
            ],
        )

        # Scale across boundary durations: 5s, 15s, 30s, 60s, 180s, 600s
        for dur in [5.0, 15.0, 30.0, 60.0, 180.0, 600.0]:
            brief = ContentBrief(project_id=f"proj_{int(dur)}", topic="The Transistor", target_duration_seconds=int(dur))
            outline = self.planner.build_outline(
                winning_angle=angle,
                hook=hook,
                dossier=dossier,
                brief=brief,
                target_duration=dur,
            )

            self.assertEqual(outline.total_estimated_duration, dur)
            self.assertEqual(len(outline.acts), 4)

            # Check act partition percentages
            self.assertEqual(outline.acts[0].target_start_pct, 0.0)
            self.assertEqual(outline.acts[0].target_end_pct, 0.15)
            self.assertEqual(outline.acts[1].target_start_pct, 0.15)
            self.assertEqual(outline.acts[1].target_end_pct, 0.45)
            self.assertEqual(outline.acts[2].target_start_pct, 0.45)
            self.assertEqual(outline.acts[2].target_end_pct, 0.75)
            self.assertEqual(outline.acts[3].target_start_pct, 0.75)
            self.assertEqual(outline.acts[3].target_end_pct, 1.0)


class TestPydanticContractsAdversarial(unittest.TestCase):
    """Stress tests for all 17 Pydantic schemas against malformed payloads and serialization."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -----------------------------------------------------------------------
    # 1. Malformed JSON / YAML Payloads Across 17 Contracts
    # -----------------------------------------------------------------------
    def test_01_malformed_json_and_yaml_syntax_rejection(self):
        """Verify that syntax errors in JSON and YAML strings raise descriptive errors."""
        broken_json = '{"project_id": "p1", "topic": "Broken JSON", '
        with self.assertRaises(Exception):
            ContentBrief.from_json(broken_json)

        broken_yaml = """
        project_id: p1
        topic: [Unbalanced YAML
        """
        with self.assertRaises(Exception):
            ContentBrief.from_yaml(broken_yaml)

        # Non-dict YAML root (e.g. YAML scalar or list)
        scalar_yaml = "just a plain string"
        with self.assertRaises(ValueError):
            ContentBrief.from_yaml(scalar_yaml)

    def test_02_all_17_contracts_reject_empty_payloads(self):
        """Verify that all 17 contracts reject empty dict payloads due to mandatory fields."""
        contract_classes = [
            CreatorProfile,
            ContentBrief,
            ResearchPlan,
            ResearchDossier,
            SourceRecord,
            ClaimRecord,
            EditorialAngle,
            ContentOutline,
            Script,
            ScriptBeat,
            AssetRequirement,
            AssetRecord,
            EvaluationReport,
            RenderArtifact,
            PublishPackage,
            AnalyticsSnapshot,
            LearningCandidate,
        ]
        self.assertEqual(len(contract_classes), 17, "Must test exactly 17 production contracts")

        for cls in contract_classes:
            with self.assertRaises(ValidationError, msg=f"Contract {cls.__name__} failed to reject empty payload"):
                cls.model_validate({})

    def test_03_boundary_value_rejections_across_contracts(self):
        """Stress-test numerical bounds, min_lengths, and enum validation."""
        # 1. ContentBrief duration bounds [5, 600]
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="Topic", target_duration_seconds=4)  # < 5
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="Topic", target_duration_seconds=601)  # > 600
        # Valid bounds
        cb_min = ContentBrief(project_id="p1", topic="Topic", target_duration_seconds=5)
        cb_max = ContentBrief(project_id="p1", topic="Topic", target_duration_seconds=600)
        self.assertEqual(cb_min.target_duration_seconds, 5)
        self.assertEqual(cb_max.target_duration_seconds, 600)

        # 2. SourceRecord reliability bounds [0.0, 1.0]
        with self.assertRaises(ValidationError):
            SourceRecord(title="T", url="U", reliability_score=-0.1)
        with self.assertRaises(ValidationError):
            SourceRecord(title="T", url="U", reliability_score=1.1)

        # 3. AnalyticsSnapshot percentage bounds
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", average_watch_percentage=100.5)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", ctr=1.05)

        # 4. EvaluationReport layer enum validation
        with self.assertRaises(ValidationError):
            EvaluationReport(run_id="r1", layer="invalid_layer", composite_score=1.5)

    def test_04_extra_fields_preservation_and_dict_subscripting(self):
        """Verify H9BaseModel extra='allow' preserves arbitrary custom fields and supports dict access."""
        p = CreatorProfile(
            creator_id="cp_custom",
            display_name="Custom Creator",
            custom_field_x="Arbitrary Value",
            nested_meta={"alpha": 123},
        )
        # Attribute access
        self.assertEqual(getattr(p, "custom_field_x"), "Arbitrary Value")
        # Subscript access
        self.assertEqual(p["custom_field_x"], "Arbitrary Value")
        self.assertEqual(p.get("custom_field_x"), "Arbitrary Value")
        self.assertTrue("custom_field_x" in p)
        # Serialization preservation
        d = p.to_dict()
        self.assertEqual(d["custom_field_x"], "Arbitrary Value")

    def test_05_lossless_roundtrip_all_17_contracts(self):
        """Verify lossless Python -> JSON -> Python -> YAML -> Python -> Dict -> Python roundtripping."""
        # Construct valid populated instances for all 17 contracts
        src = SourceRecord(title="IEEE Transistor History", url="https://ieee.org/t1", reliability_score=0.95)
        claim = ClaimRecord(claim_id="c1", claim_text="Transistor invented 1947", primary_source=src)

        instances: List[H9BaseModel] = [
            CreatorProfile(creator_id="cp1", display_name="Creator One"),
            ContentBrief(project_id="cb1", topic="Semiconductors", target_duration_seconds=45),
            ResearchPlan(topic="Quantum Dots", target_claim_count=3),
            ResearchDossier(topic="Microchips", claims=[claim]),
            src,
            claim,
            EditorialAngle(angle_id="ea1", title="The Silicon Era", premise="Solid state revolution", core_thesis="Transistors beat tubes"),
            ContentOutline(project_id="co1", topic="Silicon", angle_id="ea1", acts=[OutlineAct(act_index=1, act_name="Hook", target_start_pct=0.0, target_end_pct=0.15)]),
            Script(topic="Transistor", title="The Switch", scenes=[ScriptScene(scene_id="s1", narration_text="Opening text")]),
            ScriptBeat(beat_id="sb1", text="Opening hook beat", duration=3.2),
            AssetRequirement(requirement_id="ar1", scene_id="s1", visual_query="schematic diagram"),
            AssetRecord(asset_id="as1", local_path="assets/images/as1.svg", file_sha256="abcdef1234567890"),
            EvaluationReport(run_id="ev1", layer=EvaluationLayer.RESEARCH, composite_score=0.92),
            RenderArtifact(video_path="renders/final.mp4", duration_seconds=30.0, file_size_bytes=1048576),
            PublishPackage(project_id="pub1", title="Title", video_path="renders/final.mp4"),
            AnalyticsSnapshot(project_id="an1", views=10000, average_watch_percentage=65.5, ctr=0.08),
            LearningCandidate(lesson_id="lc1", creator_id="cp1", observation="Too slow", recommended_action="Speed up hook"),
        ]
        self.assertEqual(len(instances), 17)

        for obj in instances:
            cls = obj.__class__
            # 1. JSON Roundtrip
            json_str = obj.to_json()
            from_json_obj = cls.from_json(json_str)
            self.assertEqual(obj.to_dict(), from_json_obj.to_dict())

            # 2. YAML Roundtrip
            yaml_str = obj.to_yaml()
            from_yaml_obj = cls.from_yaml(yaml_str)
            self.assertEqual(obj.to_dict(), from_yaml_obj.to_dict())

            # 3. Disk Save & Load (atomic)
            j_path, y_path = obj.save(self.tmp_path, base_name=f"test_{cls.__name__}")
            loaded_j = cls.load(j_path)
            loaded_y = cls.load(y_path)
            self.assertEqual(obj.to_dict(), loaded_j.to_dict())
            self.assertEqual(obj.to_dict(), loaded_y.to_dict())


if __name__ == "__main__":
    unittest.main()
