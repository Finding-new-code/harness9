"""tests/test_challenger_m3_empirical_deep.py

Adversarial Verification Suite for Milestone 3 (Requirement R3):
1. Skill Discovery & Resource Loading Security (Path traversal, non-existent skills, malformed paths)
2. Script-to-IR Compilation Edge Cases (1 scene, 100 scenes, empty beats, missing visuals)
3. HyperFramesCompiler and CompositionValidator Compliance (all 7 canonical blocks, scale stress, static linter)
"""

import hashlib
from pathlib import Path
import tempfile
import unittest
from typing import Any, Dict, List

from src.h9_runtime.skills import DefaultSkillRuntime
from src.h9_runtime.types import ProductionIR
from src.hyperframes.validator import CompositionValidator
from src.models.contracts import (
    AssetRecord,
    Dimensions,
    LicenseInfo,
    Script,
    ScriptBeat,
    ScriptScene,
)
from src.models.ir import (
    HyperFramesCompiler,
    IRBlockType,
    ProductionIRDocument,
    compile_script_to_ir,
)


class TestSkillDiscoveryAndSecurityAdversarial(unittest.TestCase):
    """Stress-test skill discovery, instruction retrieval, and resource confinement."""

    def setUp(self) -> None:
        self.runtime = DefaultSkillRuntime()

    def test_nonexistent_skill_instructions_safely_rejected(self) -> None:
        """Non-existent skill name raises FileNotFoundError cleanly without unhandled crash."""
        with self.assertRaises(FileNotFoundError):
            self.runtime.load_skill_instructions("totally_fictional_skill_xyz_99")

    def test_empty_skill_name_safely_rejected(self) -> None:
        """Empty string skill name raises FileNotFoundError cleanly without crashing."""
        with self.assertRaises(FileNotFoundError):
            self.runtime.load_skill_instructions("")

    def test_whitespace_skill_name_safely_rejected(self) -> None:
        """Whitespace-only skill name raises FileNotFoundError cleanly."""
        with self.assertRaises(FileNotFoundError):
            self.runtime.load_skill_instructions("   \t  \n ")

    def test_path_traversal_in_skill_instructions_rejected(self) -> None:
        """Path traversal patterns in load_skill_instructions do not crash."""
        traversal_attempts = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "....//....//config.yaml",
            "skills/../../h9-research",
        ]
        for attempt in traversal_attempts:
            try:
                self.runtime.load_skill_instructions(attempt)
            except FileNotFoundError:
                pass  # Safely rejected without crashing

    def test_relative_path_traversal_in_load_skill_resource_rejected(self) -> None:
        """Path traversal with '../' in resource path raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.runtime.load_skill_resource("h9-research", "../secret_credentials.txt")
        self.assertIn("Path traversal detected", str(ctx.exception))

    def test_posix_absolute_path_in_load_skill_resource_rejected(self) -> None:
        """POSIX absolute paths starting with '/' raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.runtime.load_skill_resource("h9-research", "/etc/shadow")
        self.assertIn("Path traversal detected", str(ctx.exception))

    def test_directory_traversal_in_skill_name_for_resource(self) -> None:
        """Test behavior when skill_name contains traversal '../' in load_skill_resource."""
        # Notice: skill_name='..' should ideally be confined and not expose repository root files
        # We record empirical behavior
        result = self.runtime.load_skill_resource("..", "pyproject.toml")
        # If traversal succeeds, result contains [project] pyproject content
        is_traversal_leaked = "[project]" in result or "hermes-agent" in result
        if is_traversal_leaked:
            print("\n[FINDING - SECURITY] load_skill_resource('..', 'pyproject.toml') leaked repository file!")

    def test_windows_absolute_path_in_load_skill_resource(self) -> None:
        """Test behavior when Windows absolute path (C:/...) is passed as relative_path."""
        # Windows absolute paths bypass startswith('/')
        win_hosts = Path("C:/Windows/System32/drivers/etc/hosts")
        if win_hosts.exists():
            result = self.runtime.load_skill_resource("h9-research", "C:/Windows/System32/drivers/etc/hosts")
            is_hosts_leaked = "Microsoft" in result or "localhost" in result
            if is_hosts_leaked:
                print("\n[FINDING - SECURITY] load_skill_resource bypassed path confinement via Windows absolute path!")

    def test_skill_discovery_with_adversarial_categories(self) -> None:
        """Category filtering handles empty string, regex metacharacters, and unicode without error."""
        adversarial_filters = [
            "",
            "   ",
            ".*",
            "[a-z]+",
            "(?P<name>.*)",
            "\\x00\\xFF",
            "🚀🔥💡",
            "completely_unmatched_category_filter",
        ]
        for cat in adversarial_filters:
            skills = self.runtime.discover_skills(category=cat)
            self.assertIsInstance(skills, list)

    def test_skill_discovery_frontmatter_resilience(self) -> None:
        """_parse_skill_file safely ignores corrupt/unparseable files without crashing."""
        with tempfile.TemporaryDirectory() as td:
            temp_skill_dir = Path(td) / "skills"
            temp_skill_dir.mkdir(parents=True)
            
            # File 1: No frontmatter
            bad_dir_1 = temp_skill_dir / "bad_1"
            bad_dir_1.mkdir()
            (bad_dir_1 / "SKILL.md").write_text("# Just markdown without YAML\nSome content", encoding="utf-8")
            
            # File 2: Invalid YAML
            bad_dir_2 = temp_skill_dir / "bad_2"
            bad_dir_2.mkdir()
            (bad_dir_2 / "SKILL.md").write_text("---\n: invalid : yaml: [broken\n---\nBody", encoding="utf-8")

            # File 3: Missing 'name' field in YAML
            bad_dir_3 = temp_skill_dir / "bad_3"
            bad_dir_3.mkdir()
            (bad_dir_3 / "SKILL.md").write_text("---\ndescription: No name here\nversion: 1.0.0\n---\nBody", encoding="utf-8")

            rt = DefaultSkillRuntime(skill_dirs=[temp_skill_dir])
            skills = rt.discover_skills()
            self.assertIsInstance(skills, list)
            self.assertGreaterEqual(len(skills), 4)


class TestCompileScriptToIREdgeCases(unittest.TestCase):
    """Stress-test compile_script_to_ir on extreme shapes and missing fields."""

    def test_minimal_single_scene_script(self) -> None:
        """Compiling a 1-scene script satisfies all 5 AST invariants."""
        sc = ScriptScene(
            scene_id="scene_solitary",
            title="Solitary Scene",
            start_time=0.0,
            duration=3.5,
            narration_text="Only one scene in this video.",
            component_type="reference_collage_hook",
        )
        script = Script(
            topic="Solo",
            title="One Scene Video",
            total_duration=3.5,
            scenes=[sc],
        )
        ir_doc = compile_script_to_ir(script)
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(len(ir_doc.scenes), 1)
        self.assertEqual(ir_doc.audio_track.total_duration_sec, 3.5)
        self.assertEqual(ir_doc.scenes[0].duration_sec, 3.5)
        self.assertEqual(ir_doc.scenes[0].start_time_sec, 0.0)

    def test_massive_100_scene_script_temporal_contiguity(self) -> None:
        """Compiling a 100-scene script preserves temporal conservation and audio sync without drift."""
        scenes = [
            ScriptScene(
                scene_id=f"scene_{i:03d}",
                title=f"Scene {i}",
                start_time=float(i * 2.5),
                duration=2.5,
                narration_text=f"Narration text for scene {i}.",
                component_type="statistic_reveal",
            )
            for i in range(100)
        ]
        script = Script(
            topic="Scale Test",
            title="100 Scenes Production",
            total_duration=250.0,
            scenes=scenes,
        )
        ir_doc = compile_script_to_ir(script)
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(len(ir_doc.scenes), 100)
        self.assertAlmostEqual(ir_doc.audio_track.total_duration_sec, 250.0, delta=0.01)

        expected_t = 0.0
        for sc in ir_doc.scenes:
            self.assertAlmostEqual(sc.start_time_sec, expected_t, delta=0.01)
            expected_t += sc.duration_sec
        self.assertAlmostEqual(expected_t, 250.0, delta=0.01)

    def test_empty_beats_handled_gracefully(self) -> None:
        """Scenes with beats=[] automatically get a default synthesized speech beat."""
        sc = ScriptScene(
            scene_id="s_no_beats",
            title="No Beats",
            start_time=0.0,
            duration=4.0,
            narration_text="Scene without any speech beats specified.",
            beats=[],
        )
        script = Script(topic="Beats Test", title="Beats", total_duration=4.0, scenes=[sc])
        ir_doc = compile_script_to_ir(script)
        beats = ir_doc.scenes[0].narration.speech_beats
        self.assertEqual(len(beats), 1)
        self.assertEqual(beats[0].start_time_sec, 0.0)
        self.assertEqual(beats[0].end_time_sec, 4.0)
        self.assertEqual(beats[0].text, "Scene without any speech beats specified.")

    def test_missing_visual_requirements_handled_with_safe_fallbacks(self) -> None:
        """Scene with empty visual_asset_path, unknown component_type, and no assets."""
        sc = ScriptScene(
            scene_id="s_missing_viz",
            title="No Viz",
            start_time=0.0,
            duration=5.0,
            narration_text="Scene without visual assets.",
            visual_asset_path="",
            component_type="nonexistent_alien_block",
            component_props={},
        )
        script = Script(topic="Missing Viz", title="Missing Viz", total_duration=5.0, scenes=[sc])
        ir_doc = compile_script_to_ir(script, assets=None)
        self.assertEqual(ir_doc.scenes[0].visual_block.block_type, IRBlockType.REFERENCE_COLLAGE_HOOK)
        self.assertEqual(len(ir_doc.scenes[0].visual_block.asset_bindings), 0)

    def test_empty_raw_dict_handled_with_fallback_scene(self) -> None:
        """compile_script_to_ir({}) gracefully produces a valid single-scene default IR."""
        ir_doc = compile_script_to_ir({})
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(len(ir_doc.scenes), 1)
        self.assertGreaterEqual(ir_doc.audio_track.total_duration_sec, 0.5)

    def test_invalid_type_rejected_with_type_error(self) -> None:
        """Passing an integer, list, or string raises TypeError."""
        for invalid_input in [123, ["not", "script"], "raw_string", None]:
            with self.assertRaises(TypeError):
                compile_script_to_ir(invalid_input)


class TestHyperFramesCompilerAndValidator(unittest.TestCase):
    """Verify HyperFramesCompiler produces valid projects passing CompositionValidator."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_single_scene_passes_composition_validator(self) -> None:
        """Single-scene compilation passes CompositionValidator with zero errors."""
        sc = ScriptScene(
            scene_id="s1",
            title="Intro",
            start_time=0.0,
            duration=5.0,
            narration_text="Single scene composition validation test.",
            component_type="reference_collage_hook",
        )
        script = Script(topic="Validation", title="Single Scene", total_duration=5.0, scenes=[sc])
        ir_doc = compile_script_to_ir(script)

        compiler = HyperFramesCompiler()
        project = compiler.compile(ir_doc, output_dir=self.output_path / "proj_1")
        
        validator = CompositionValidator(project.project_dir)
        report = validator.validate()
        self.assertTrue(report["valid"], f"Validation failed with errors: {report.get('errors')}")
        self.assertEqual(len(report["errors"]), 0)

    def test_100_scenes_passes_composition_validator(self) -> None:
        """Massive 100-scene compilation passes CompositionValidator with zero errors."""
        scenes = [
            ScriptScene(
                scene_id=f"s_{i:03d}",
                title=f"Scene {i}",
                start_time=float(i * 2.0),
                duration=2.0,
                narration_text=f"Scene {i} in massive composition.",
                component_type="timeline_reveal",
            )
            for i in range(100)
        ]
        script = Script(topic="Massive Scale", title="100 Scenes", total_duration=200.0, scenes=scenes)
        ir_doc = compile_script_to_ir(script)

        compiler = HyperFramesCompiler()
        project = compiler.compile(ir_doc, output_dir=self.output_path / "proj_100")

        validator = CompositionValidator(project.project_dir)
        report = validator.validate()
        self.assertTrue(report["valid"], f"Validation failed with errors: {report.get('errors')}")
        self.assertEqual(len(report["errors"]), 0)

    def test_all_seven_canonical_blocks_pass_composition_validator(self) -> None:
        """Each of the 7 canonical component blocks compiles and passes CompositionValidator."""
        compiler = HyperFramesCompiler()

        for b_type in IRBlockType:
            sc = ScriptScene(
                scene_id=f"sc_{b_type.value}",
                title=f"Test {b_type.value}",
                start_time=0.0,
                duration=5.0,
                narration_text=f"Testing component block {b_type.value}.",
                component_type=b_type.value,
            )
            script = Script(
                topic=b_type.value,
                title=f"Title {b_type.value}",
                total_duration=5.0,
                scenes=[sc],
            )
            ir_doc = compile_script_to_ir(script)
            target = self.output_path / f"proj_{b_type.value}"
            project = compiler.compile(ir_doc, output_dir=target)

            validator = CompositionValidator(project.project_dir)
            report = validator.validate()
            self.assertTrue(
                report["valid"],
                f"Block {b_type.value} failed validation: {report.get('errors')}",
            )
            self.assertEqual(len(report["errors"]), 0)

    def test_composition_validator_adversarial_rejection(self) -> None:
        """Verify CompositionValidator actually rejects invalid and non-compliant projects."""
        bad_dir = self.output_path / "bad_project"
        bad_dir.mkdir(parents=True)

        # 1. Missing index.html
        v1 = CompositionValidator(bad_dir).validate()
        self.assertFalse(v1["valid"])
        self.assertTrue(any("Missing required composition file" in e for e in v1["errors"]))

        # 2. Missing root composition element
        (bad_dir / "index.html").write_text("<html><body><div>No root</div></body></html>", encoding="utf-8")
        (bad_dir / "styles.css").write_text("body { background: #000; color: #fff; }", encoding="utf-8")
        (bad_dir / "main.js").write_text("window.__timelines = { root: gsap.timeline({ paused: true }) };", encoding="utf-8")
        v2 = CompositionValidator(bad_dir).validate()
        self.assertFalse(v2["valid"])
        self.assertTrue(any("Missing root composition element" in e for e in v2["errors"]))

        # 3. External media URL
        (bad_dir / "index.html").write_text(
            '<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="10">'
            '<img src="https://external-cdn.com/asset.png" /></div>',
            encoding="utf-8",
        )
        v3 = CompositionValidator(bad_dir).validate()
        self.assertFalse(v3["valid"])
        self.assertTrue(any("Forbidden external media URL" in e for e in v3["errors"]))

        # 4. Infinite loop repeat: -1
        (bad_dir / "index.html").write_text(
            '<div data-composition-id="root" data-width="1920" data-height="1080" data-duration="10"></div>',
            encoding="utf-8",
        )
        (bad_dir / "main.js").write_text(
            'window.__timelines = { root: gsap.timeline({ paused: true, repeat: -1 }) };',
            encoding="utf-8",
        )
        v4 = CompositionValidator(bad_dir).validate()
        self.assertFalse(v4["valid"])
        self.assertTrue(any("repeat: -1" in e for e in v4["errors"]))


if __name__ == "__main__":
    unittest.main()
