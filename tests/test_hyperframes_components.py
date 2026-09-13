"""tests/test_hyperframes_components.py — Comprehensive Unit & Integration Tests for Milestone M3.

Covers:
1. BaseComponent ABC & ComponentSchema (validation, unpacking, finite repeat math, color sanitization).
2. ComponentRegistry (built-in discovery, registration, lookup, duplicate guards, error handling).
3. 7 Canonical Component Blocks Unit Tests (16:9 and 9:16 HTML/CSS/GSAP generation, validation, edge cases):
   - ReferenceCollageHook
   - SplitScreenIntro
   - QuoteHighlight
   - TimelineReveal
   - StatisticReveal
   - ComparisonPanel
   - CreatorBottomCollage
4. HyperFramesAdapter Composition Compilation (assembling all 7 blocks into root index.html, styles.css, main.js).
5. Static Linter & CompositionValidator Verification (16:9 landscape and 9:16 portrait).
6. HyperFramesAdapter Video Render Interface (RenderArtifact production).
"""

import re
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from adapters.hyperframes.adapter import HyperFramesAdapter, HyperFramesProject
from adapters.hyperframes.registry import (
    ComponentRegistry,
    get_component,
    get_registry,
    list_registered_components,
    register_component,
)
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
from src.hyperframes.validator import CompositionValidator
from src.models.contracts import AssetRecord, RenderArtifact, Script, ScriptScene


class TestBaseComponentAndSchema(unittest.TestCase):
    """Test BaseComponent abstract class, schema definitions, and utility methods."""

    def test_01_validation_result_methods(self):
        """Verify ValidationResult error and warning tracking."""
        res = ValidationResult(valid=True)
        self.assertTrue(res.valid)
        self.assertEqual(len(res.errors), 0)

        res.add_warning("Minor warning")
        self.assertTrue(res.valid)
        self.assertEqual(len(res.warnings), 1)

        res.add_error("Fatal error")
        self.assertFalse(res.valid)
        self.assertEqual(len(res.errors), 1)

        d = res.to_dict()
        self.assertFalse(d["valid"])
        self.assertEqual(d["errors"], ["Fatal error"])

    def test_02_finite_repeat_calculations(self):
        """Verify HyperFrames finite loop math prevents infinite loop hangs."""
        # Math.ceil(duration / cycle) - 1
        # duration = 10.0, cycle = 2.0 -> Math.ceil(5.0) - 1 = 4 repeats
        self.assertEqual(BaseComponent.calculate_finite_repeats(10.0, 2.0), 4)
        # duration = 5.0, cycle = 5.0 -> Math.ceil(1.0) - 1 = 0 repeats
        self.assertEqual(BaseComponent.calculate_finite_repeats(5.0, 5.0), 0)
        # duration = 5.0, cycle = 10.0 -> Math.ceil(0.5) - 1 = 0 repeats
        self.assertEqual(BaseComponent.calculate_finite_repeats(5.0, 10.0), 0)
        # Negative / zero bounds
        self.assertEqual(BaseComponent.calculate_finite_repeats(0.0, 2.0), 0)
        self.assertEqual(BaseComponent.calculate_finite_repeats(10.0, 0.0), 0)

    def test_03_color_sanitization(self):
        """Verify CSS color validator accepts valid colors and defaults invalid ones."""
        self.assertEqual(BaseComponent.sanitize_color("#00d2ff"), "#00d2ff")
        self.assertEqual(BaseComponent.sanitize_color("#fff"), "#fff")
        self.assertEqual(BaseComponent.sanitize_color("#12345678"), "#12345678")
        self.assertEqual(BaseComponent.sanitize_color("rgb(10, 20, 30)"), "rgb(10, 20, 30)")
        self.assertEqual(BaseComponent.sanitize_color("rgba(10, 20, 30, 0.5)"), "rgba(10, 20, 30, 0.5)")
        # Invalid / injection attempts default to #00d2ff
        self.assertEqual(BaseComponent.sanitize_color("red; font-size: 100px"), "#00d2ff")
        self.assertEqual(BaseComponent.sanitize_color(""), "#00d2ff")
        self.assertEqual(BaseComponent.sanitize_color(None), "#00d2ff")

    def test_04_html_escaping(self):
        """Verify HTML character escaping for security and valid DOM."""
        raw = '<script>alert("xss") & \'test\'</script>'
        escaped = BaseComponent.escape(raw)
        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;script&gt;", escaped)
        self.assertIn("&amp;", escaped)
        self.assertIn("&quot;", escaped)
        self.assertEqual(BaseComponent.escape(None), "")


class TestComponentRegistry(unittest.TestCase):
    """Test ComponentRegistry registration, discovery, and instantiation."""

    def setUp(self):
        self.registry = ComponentRegistry(register_builtins=True)

    def test_05_all_7_builtins_registered(self):
        """Verify all 7 canonical component blocks are discovered and registered."""
        blocks = self.registry.list_components()
        expected = [
            "comparison_panel",
            "creator_bottom_collage",
            "quote_highlight",
            "reference_collage_hook",
            "split_screen_intro",
            "statistic_reveal",
            "timeline_reveal",
        ]
        self.assertEqual(blocks, expected)
        self.assertEqual(self.registry.count(), 7)

    def test_06_get_and_instantiate(self):
        """Verify component lookup and instance caching."""
        comp1 = self.registry.get("reference_collage_hook")
        comp2 = self.registry.get("reference_collage_hook")
        self.assertIs(comp1, comp2)  # Cached singleton instance
        self.assertIsInstance(comp1, ReferenceCollageHook)

        fresh_comp = self.registry.instantiate("reference_collage_hook")
        self.assertIsNot(comp1, fresh_comp)  # Fresh instance
        self.assertIsInstance(fresh_comp, ReferenceCollageHook)

    def test_07_get_schema_inspection(self):
        """Verify schema metadata retrieval for blocks."""
        schema = self.registry.get_schema("statistic_reveal")
        self.assertEqual(schema.block_id, "statistic_reveal")
        self.assertEqual(schema.display_name, "Statistic Reveal")
        self.assertIn("target_number", schema.required_props)
        self.assertIn("16:9", schema.supported_aspect_ratios)
        self.assertIn("9:16", schema.supported_aspect_ratios)

    def test_08_custom_component_registration(self):
        """Verify registering a custom user-defined component block."""
        class CustomBlock(BaseComponent):
            schema = ComponentSchema(
                block_id="custom_block",
                display_name="Custom Block",
                description="Custom test block",
                supported_aspect_ratios=["16:9"],
                required_props=["custom_prop"],
            )

            def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
                return f'<div id="{scene_id}-custom">{props.get("custom_prop")}</div>'

            def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
                return f"#{scene_id}-custom {{ color: red; }}"

            def _render_gsap(self, scene_id: str, props: Dict[str, Any], start_time: float, duration: float, format_aspect: str) -> str:
                return f"tl.from('#{scene_id}-custom', {{ opacity: 0 }}, {start_time});"

        self.registry.register("custom_block", CustomBlock)
        self.assertTrue(self.registry.has("custom_block"))
        inst = self.registry.get("custom_block")
        self.assertIsInstance(inst, CustomBlock)

        # Duplicate registration guard
        with self.assertRaises(ValueError):
            self.registry.register("custom_block", CustomBlock, allow_overwrite=False)

    def test_09_invalid_registration_errors(self):
        """Verify error handling on invalid registration inputs."""
        with self.assertRaises(ValueError):
            self.registry.register("", ReferenceCollageHook)
        with self.assertRaises(TypeError):
            self.registry.register("bad_class", str)  # type: ignore

    def test_10_unknown_component_key_error(self):
        """Verify KeyError on unknown block lookup."""
        with self.assertRaises(KeyError):
            self.registry.get("non_existent_block_404")

    def test_11_global_helpers(self):
        """Verify global helper functions mirror registry actions."""
        comps = list_registered_components()
        self.assertEqual(len(comps), 7)
        comp = get_component("timeline_reveal")
        self.assertIsInstance(comp, TimelineReveal)


class TestComponentBlocksUnit(unittest.TestCase):
    """Unit tests for each of the 7 individual component blocks."""

    def test_12_block_1_reference_collage_hook(self):
        """Block 1: ReferenceCollageHook validation and rendering in 16:9 and 9:16."""
        comp = ReferenceCollageHook()
        self.assertEqual(comp.block_id, "reference_collage_hook")

        # Validation Happy Path
        v_ok = comp.validate({"headline": "Accidental Discovery", "image_paths": ["assets/images/img1.svg"]})
        self.assertTrue(v_ok.valid)

        # Validation Missing Required Props
        v_fail = comp.validate({"headline": ""})
        self.assertFalse(v_fail.valid)
        self.assertIn("headline", v_fail.errors[0])

        # Validation Remote URL Rejection
        v_remote = comp.validate({"headline": "Valid", "image_paths": ["https://example.com/bad.png"]})
        self.assertFalse(v_remote.valid)
        self.assertIn("Forbidden remote URL", v_remote.errors[0])

        # Render 16:9
        html_16_9 = comp.render_html("scene_1", {"headline": "Accidental Discovery", "image_paths": ["assets/images/img1.svg"]}, "16:9")
        css_16_9 = comp.render_css("scene_1", {}, "16:9")
        gsap_16_9 = comp.render_gsap("scene_1", {}, start_time=0.0, duration=5.0, format_aspect="16:9")

        self.assertIn('data-block-id="reference_collage_hook"', html_16_9)
        self.assertIn("Accidental Discovery", html_16_9)
        self.assertIn("#scene_1-collage", css_16_9)
        self.assertIn("tl.from", gsap_16_9)
        self.assertNotIn("repeat: -1", gsap_16_9)

        # Render 9:16
        html_9_16 = comp.render_html("scene_1", {"headline": "Portrait Hook"}, "9:16")
        css_9_16 = comp.render_css("scene_1", {}, "9:16")
        self.assertIn("padding-bottom: 620px", css_9_16)

    def test_13_block_2_split_screen_intro(self):
        """Block 2: SplitScreenIntro validation and rendering in 16:9 and 9:16."""
        comp = SplitScreenIntro()
        self.assertEqual(comp.block_id, "split_screen_intro")

        # Validation
        v_ok = comp.validate({"left_title": "Tubes", "right_title": "Transistors"})
        self.assertTrue(v_ok.valid)

        v_fail = comp.validate({"left_title": "Tubes"})  # missing right_title
        self.assertFalse(v_fail.valid)

        # Remote URL check
        v_remote = comp.validate({"left_title": "A", "right_title": "B", "left_image": "http://evil.com/img.png"})
        self.assertFalse(v_remote.valid)

        # Render 16:9 & 9:16
        html_16_9 = comp.render_html("scene_2", {"left_title": "Vacuum Tubes", "right_title": "Transistors"}, "16:9")
        css_16_9 = comp.render_css("scene_2", {}, "16:9")
        gsap_16_9 = comp.render_gsap("scene_2", {}, start_time=5.0, duration=5.0, format_aspect="16:9")

        self.assertIn('data-block-id="split_screen_intro"', html_16_9)
        self.assertIn("Vacuum Tubes", html_16_9)
        self.assertIn("Transistors", html_16_9)
        self.assertIn("#scene_2-splitscreen", css_16_9)
        self.assertIn("tl.from", gsap_16_9)
        self.assertNotIn("repeat: -1", gsap_16_9)

        css_9_16 = comp.render_css("scene_2", {}, "9:16")
        self.assertIn("flex-direction: column", css_9_16)

    def test_14_block_3_quote_highlight(self):
        """Block 3: QuoteHighlight validation and rendering in 16:9 and 9:16."""
        comp = QuoteHighlight()
        self.assertEqual(comp.block_id, "quote_highlight")

        # Validation
        v_ok = comp.validate({"quote_text": "Physics is mystery.", "author_name": "Feynman"})
        self.assertTrue(v_ok.valid)

        v_fail = comp.validate({"quote_text": "No author"})
        self.assertFalse(v_fail.valid)

        # Render
        html = comp.render_html("scene_3", {"quote_text": "Physics is mystery.", "author_name": "Feynman"}, "16:9")
        css = comp.render_css("scene_3", {}, "16:9")
        gsap = comp.render_gsap("scene_3", {}, start_time=10.0, duration=5.0, format_aspect="16:9")

        self.assertIn('data-block-id="quote_highlight"', html)
        self.assertIn("Physics is mystery.", html)
        self.assertIn("Feynman", html)
        self.assertIn("#scene_3-quote", css)
        self.assertIn("tl.from", gsap)
        self.assertNotIn("repeat: -1", gsap)

    def test_15_block_4_timeline_reveal(self):
        """Block 4: TimelineReveal validation and rendering in 16:9 and 9:16."""
        comp = TimelineReveal()
        self.assertEqual(comp.block_id, "timeline_reveal")

        # Validation
        v_ok = comp.validate({
            "milestones": [
                {"year": "1947", "title": "Point Contact"},
                {"year": "1954", "title": "Silicon"},
            ]
        })
        self.assertTrue(v_ok.valid)

        # Less than 2 milestones
        v_fail = comp.validate({"milestones": [{"year": "1947"}]})
        self.assertFalse(v_fail.valid)

        # Render
        html = comp.render_html("scene_4", {"title": "Timeline", "milestones": [{"year": "1947", "title": "Birth", "description": "Desc"}]}, "16:9")
        css = comp.render_css("scene_4", {}, "16:9")
        gsap = comp.render_gsap("scene_4", {}, start_time=15.0, duration=5.0, format_aspect="16:9")

        self.assertIn('data-block-id="timeline_reveal"', html)
        self.assertIn("1947", html)
        self.assertIn("#scene_4-timeline", css)
        self.assertIn("tl.from", gsap)
        self.assertNotIn("repeat: -1", gsap)

        css_9_16 = comp.render_css("scene_4", {}, "9:16")
        self.assertIn("flex-direction: column", css_9_16)

    def test_16_block_5_statistic_reveal(self):
        """Block 5: StatisticReveal validation and rendering in 16:9 and 9:16."""
        comp = StatisticReveal()
        self.assertEqual(comp.block_id, "statistic_reveal")

        # Validation
        v_ok = comp.validate({"target_number": "100 Billion", "metric_label": "Transistors"})
        self.assertTrue(v_ok.valid)

        v_fail = comp.validate({"target_number": ""})
        self.assertFalse(v_fail.valid)

        # Render
        html = comp.render_html("scene_5", {"target_number": "100 Billion", "metric_label": "Transistors"}, "16:9")
        css = comp.render_css("scene_5", {}, "16:9")
        gsap = comp.render_gsap("scene_5", {}, start_time=20.0, duration=5.0, format_aspect="16:9")

        self.assertIn('data-block-id="statistic_reveal"', html)
        self.assertIn("100 Billion", html)
        self.assertIn("Transistors", html)
        self.assertIn("#scene_5-stat", css)
        self.assertIn("tl.from", gsap)
        self.assertNotIn("repeat: -1", gsap)

    def test_17_block_6_comparison_panel(self):
        """Block 6: ComparisonPanel validation and rendering in 16:9 and 9:16."""
        comp = ComparisonPanel()
        self.assertEqual(comp.block_id, "comparison_panel")

        # Validation
        v_ok = comp.validate({
            "entity_a_name": "Tubes",
            "entity_b_name": "Transistors",
            "comparison_rows": [{"metric": "Power", "val_a": "50W", "val_b": "0.01W", "winner": "b"}]
        })
        self.assertTrue(v_ok.valid)

        v_fail = comp.validate({"entity_a_name": "Tubes", "entity_b_name": ""})
        self.assertFalse(v_fail.valid)

        # Render
        html = comp.render_html("scene_6", {
            "entity_a_name": "Tubes",
            "entity_b_name": "Transistors",
            "comparison_rows": [{"metric": "Power", "val_a": "50W", "val_b": "0.01W", "winner": "b"}]
        }, "16:9")
        css = comp.render_css("scene_6", {}, "16:9")
        gsap = comp.render_gsap("scene_6", {}, start_time=25.0, duration=5.0, format_aspect="16:9")

        self.assertIn('data-block-id="comparison_panel"', html)
        self.assertIn("Tubes", html)
        self.assertIn("Transistors", html)
        self.assertIn("#scene_6-comparison", css)
        self.assertIn("tl.from", gsap)
        self.assertNotIn("repeat: -1", gsap)

    def test_18_block_7_creator_bottom_collage(self):
        """Block 7: CreatorBottomCollage validation and rendering in 16:9 and 9:16."""
        comp = CreatorBottomCollage()
        self.assertEqual(comp.block_id, "creator_bottom_collage")

        # Validation
        v_ok = comp.validate({"creator_name": "Harness 9", "creator_handle": "@H9"})
        self.assertTrue(v_ok.valid)

        v_fail = comp.validate({"creator_name": ""})
        self.assertFalse(v_fail.valid)

        # Remote URL check
        v_remote = comp.validate({"creator_name": "H9", "creator_handle": "@H9", "avatar_path": "https://remote.com/a.jpg"})
        self.assertFalse(v_remote.valid)

        # Render
        html = comp.render_html("scene_7", {"creator_name": "Harness 9 Studio", "creator_handle": "@Harness9AI"}, "16:9")
        css = comp.render_css("scene_7", {}, "16:9")
        gsap = comp.render_gsap("scene_7", {}, start_time=30.0, duration=5.0, format_aspect="16:9")

        self.assertIn('data-block-id="creator_bottom_collage"', html)
        self.assertIn("Harness 9 Studio", html)
        self.assertIn("@Harness9AI", html)
        self.assertIn("#scene_7-creator", css)
        self.assertIn("tl.from", gsap)
        self.assertNotIn("repeat: -1", gsap)

        css_9_16 = comp.render_css("scene_7", {}, "9:16")
        self.assertIn("bottom: 580px", css_9_16)


class TestHyperFramesAdapterIntegration(unittest.TestCase):
    """Integration tests for HyperFramesAdapter compiling all 7 blocks in 16:9 and 9:16."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

        # Create mock frozen assets
        images_dir = self.out_path / "assets" / "images"
        audio_dir = self.out_path / "assets" / "audio"
        images_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, 8):
            (images_dir / f"asset_{i:02d}.svg").write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><rect width="100%" height="100%" fill="#0a0e17"/><text x="50%" y="50%" fill="#00d2ff">Asset {i}</text></svg>',
                encoding="utf-8",
            )
        (audio_dir / "narration.wav").write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

        self.adapter = HyperFramesAdapter()

        # Build a comprehensive 7-scene script utilizing all 7 component blocks
        self.script_data = {
            "topic": "The Transistor Revolution",
            "title": "How Solid State Physics Built Silicon Valley",
            "total_duration": 35.0,
            "scenes": [
                {
                    "scene_id": "scene_1",
                    "title": "The Breakthrough",
                    "start_time": 0.0,
                    "duration": 5.0,
                    "component_type": "reference_collage_hook",
                    "visual_asset_path": "assets/images/asset_01.svg",
                    "component_props": {
                        "headline": "The Accidental Revolution That Built Computing",
                        "badge": "BREAKTHROUGH",
                        "image_paths": ["assets/images/asset_01.svg", "assets/images/asset_02.svg"],
                    },
                },
                {
                    "scene_id": "scene_2",
                    "title": "The Paradigm Shift",
                    "start_time": 5.0,
                    "duration": 5.0,
                    "component_type": "split_screen_intro",
                    "visual_asset_path": "assets/images/asset_02.svg",
                    "component_props": {
                        "left_title": "Vacuum Tubes",
                        "left_image": "assets/images/asset_02.svg",
                        "right_title": "Point Contact",
                        "right_image": "assets/images/asset_03.svg",
                    },
                },
                {
                    "scene_id": "scene_3",
                    "title": "The Discovery Quote",
                    "start_time": 10.0,
                    "duration": 5.0,
                    "component_type": "quote_highlight",
                    "visual_asset_path": "assets/images/asset_03.svg",
                    "component_props": {
                        "quote_text": "We knew the world would not be the same.",
                        "author_name": "J. Robert Oppenheimer",
                        "author_image": "assets/images/asset_03.svg",
                    },
                },
                {
                    "scene_id": "scene_4",
                    "title": "Timeline of Progress",
                    "start_time": 15.0,
                    "duration": 5.0,
                    "component_type": "timeline_reveal",
                    "visual_asset_path": "assets/images/asset_04.svg",
                    "component_props": {
                        "title": "Milestones of Computing",
                        "milestones": [
                            {"year": "1947", "title": "Bell Labs Point Contact"},
                            {"year": "1954", "title": "Silicon Transistor"},
                            {"year": "1971", "title": "Microprocessor"},
                        ],
                    },
                },
                {
                    "scene_id": "scene_5",
                    "title": "Transistor Scale",
                    "start_time": 20.0,
                    "duration": 5.0,
                    "component_type": "statistic_reveal",
                    "visual_asset_path": "assets/images/asset_05.svg",
                    "component_props": {
                        "target_number": "100 Billion",
                        "metric_label": "Transistors Per Modern GPU",
                        "context_subtext": "Exponential scaling across five decades of Moore's Law.",
                    },
                },
                {
                    "scene_id": "scene_6",
                    "title": "Architectural Comparison",
                    "start_time": 25.0,
                    "duration": 5.0,
                    "component_type": "comparison_panel",
                    "visual_asset_path": "assets/images/asset_06.svg",
                    "component_props": {
                        "entity_a_name": "Vacuum Tubes",
                        "entity_b_name": "Silicon Transistors",
                        "comparison_rows": [
                            {"metric": "Power Efficiency", "val_a": "50W", "val_b": "0.001W", "winner": "b"},
                            {"metric": "Switching Speed", "val_a": "100 kHz", "val_b": "100 MHz", "winner": "b"},
                        ],
                    },
                },
                {
                    "scene_id": "scene_7",
                    "title": "Creator Sign-off",
                    "start_time": 30.0,
                    "duration": 5.0,
                    "component_type": "creator_bottom_collage",
                    "visual_asset_path": "assets/images/asset_07.svg",
                    "component_props": {
                        "creator_name": "Harness 9 Studio",
                        "creator_handle": "@Harness9AI",
                        "avatar_path": "assets/images/asset_07.svg",
                        "headline": "Autonomous Video Intelligence",
                    },
                },
            ],
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_19_compile_composition_16_9_landscape(self):
        """Verify compiling a 16:9 project assembling all 7 component blocks."""
        project = self.adapter.compile_composition(
            script=self.script_data,
            output_dir=self.out_path / "comp_16_9",
            format_aspect="16:9",
        )

        self.assertTrue(project.exists())
        self.assertEqual(project.width, 1920)
        self.assertEqual(project.height, 1080)
        self.assertEqual(project.duration, 35.0)
        self.assertEqual(project.scene_count, 7)

        html_content = project.index_html.read_text(encoding="utf-8")
        css_content = project.styles_css.read_text(encoding="utf-8")
        js_content = project.main_js.read_text(encoding="utf-8")

        # Assert all 7 blocks are present in HTML
        self.assertIn('data-block-id="reference_collage_hook"', html_content)
        self.assertIn('data-block-id="split_screen_intro"', html_content)
        self.assertIn('data-block-id="quote_highlight"', html_content)
        self.assertIn('data-block-id="timeline_reveal"', html_content)
        self.assertIn('data-block-id="statistic_reveal"', html_content)
        self.assertIn('data-block-id="comparison_panel"', html_content)
        self.assertIn('data-block-id="creator_bottom_collage"', html_content)

        # Assert GSAP controller contracts
        self.assertIn('window.__timelines["root"] = tl', js_content)
        self.assertIn("paused: true", js_content)
        self.assertNotIn("repeat: -1", js_content)

        # Run composition validator
        val = project.validate()
        self.assertTrue(val["valid"], f"Composition validation failed: {val.get('errors')}")
        self.assertEqual(len(val["errors"]), 0)

    def test_20_compile_composition_9_16_portrait(self):
        """Verify compiling a 9:16 vertical portrait project assembling all 7 component blocks."""
        project = self.adapter.compile_composition(
            script=self.script_data,
            output_dir=self.out_path / "comp_9_16",
            format_aspect="9:16",
        )

        self.assertTrue(project.exists())
        self.assertEqual(project.width, 1080)
        self.assertEqual(project.height, 1920)

        html_content = project.index_html.read_text(encoding="utf-8")
        self.assertIn('data-width="1080"', html_content)
        self.assertIn('data-height="1920"', html_content)

        val = project.validate()
        self.assertTrue(val["valid"], f"9:16 validation failed: {val.get('errors')}")

    def test_21_render_project_produces_render_artifact(self):
        """Verify render_project returns a valid RenderArtifact contract."""
        project = self.adapter.compile_composition(
            script=self.script_data,
            output_dir=self.out_path / "render_test",
            format_aspect="16:9",
        )

        artifact = self.adapter.render_project(
            project=project,
            output_path=self.out_path / "render_test" / "renders" / "final.mp4",
        )

        self.assertIsInstance(artifact, RenderArtifact)
        self.assertTrue(artifact.video_path.endswith(".mp4"))
        self.assertEqual(artifact.width, 1920)
        self.assertEqual(artifact.height, 1080)
        self.assertGreater(artifact.duration_seconds, 0)
        self.assertIn(artifact.validation_status, ["VERIFIED", "WARNINGS"])

    def test_22_linter_detects_tampered_remote_url(self):
        """Verify CompositionValidator catches tampered external media URL in component project."""
        project = self.adapter.compile_composition(
            script=self.script_data,
            output_dir=self.out_path / "tampered_remote",
            format_aspect="16:9",
        )

        # Tamper index.html by injecting a remote URL
        content = project.index_html.read_text(encoding="utf-8")
        tampered = content.replace("assets/images/asset_01.svg", "https://unfrozen.com/remote_image.png")
        project.index_html.write_text(tampered, encoding="utf-8")

        val = project.validate()
        self.assertFalse(val["valid"])
        self.assertTrue(any("Forbidden external media URL" in err for err in val["errors"]))


if __name__ == "__main__":
    unittest.main()
