"""tests/test_h9_skills_and_ir.py

Comprehensive test suite verifying Milestone 3:
1. Native Hermes Skills Discovery & Progressive Disclosure
2. Typed Production IR AST Schema & Strict Invariant Validation
3. Script & Asset Record to Production IR AST Compilation
4. Production IR to HyperFrames Compilation & Rendering Seam Integration
"""

import hashlib
from pathlib import Path
import tempfile
import unittest

from src.h9_runtime.bridge import HermesCapabilityBridge
from src.h9_runtime.content import DefaultContentRuntime
from src.h9_runtime.skills import DefaultSkillRuntime
from src.h9_runtime.types import ProductionIR
from src.models.contracts import (
    AssetRecord,
    Dimensions,
    LicenseInfo,
    Script,
    ScriptBeat,
    ScriptScene,
)
from src.models.ir import (
    AudioNarration,
    HyperFramesCompiler,
    IRAnimationTrack,
    IRAssetReference,
    IRBlockType,
    IRMetadata,
    IRNarrationBlock,
    IRSceneNode,
    IRSpeechBeat,
    IRTransitionSpec,
    IRVisualBlockNode,
    IRAudioTrack,
    ProductionIRDocument,
    compile_script_to_ir,
)


class TestH9SkillsDiscovery(unittest.TestCase):
    """Verify native Hermes skill discovery, frontmatter parsing, and progressive disclosure."""

    def setUp(self) -> None:
        self.skill_runtime = DefaultSkillRuntime()

    def test_all_four_h9_skills_discovered(self) -> None:
        """Ensure all 4 H9 skills are discovered from the repository skills/ directory."""
        skills = self.skill_runtime.discover_skills()
        skill_names = [s.name for s in skills]

        expected_skills = [
            "h9-research",
            "h9-content-planning",
            "h9-production",
            "h9-hyperframes",
        ]
        for expected in expected_skills:
            self.assertIn(expected, skill_names, f"Skill '{expected}' was not discovered.")

    def test_skill_metadata_integrity(self) -> None:
        """Verify YAML frontmatter fields: name, description, version, author, and tags."""
        skills = {s.name: s for s in self.skill_runtime.discover_skills()}

        # 1. h9-research
        s_res = skills["h9-research"]
        self.assertEqual(s_res.version, "1.0.0")
        self.assertIn("Harness 9", s_res.author)
        self.assertIn("Research", s_res.tags)
        self.assertTrue(len(s_res.description) > 20)

        # 2. h9-content-planning
        s_plan = skills["h9-content-planning"]
        self.assertEqual(s_plan.version, "1.0.0")
        self.assertIn("Editorial", s_plan.tags)

        # 3. h9-production
        s_prod = skills["h9-production"]
        self.assertEqual(s_prod.version, "1.0.0")
        self.assertIn("Production", s_prod.tags)

        # 4. h9-hyperframes
        s_hf = skills["h9-hyperframes"]
        self.assertEqual(s_hf.version, "1.0.0")
        self.assertIn("HyperFrames", s_hf.tags)

    def test_skill_instructions_retrieval(self) -> None:
        """Ensure full instruction content (SKILL.md) is loaded cleanly."""
        res_text = self.skill_runtime.load_skill_instructions("h9-research")
        self.assertIn("ResearchDossier", res_text)
        self.assertIn("Orthogonal Query Expansion", res_text)

        plan_text = self.skill_runtime.load_skill_instructions("h9-content-planning")
        self.assertIn("9-Dimension Editorial Scorecard", plan_text)
        self.assertIn("contrarian", plan_text)

        prod_text = self.skill_runtime.load_skill_instructions("h9-production")
        self.assertIn("17-State Lifecycle Machine", prod_text)
        self.assertIn("Voice QA", prod_text)

        hf_text = self.skill_runtime.load_skill_instructions("h9-hyperframes")
        self.assertIn("reference_collage_hook", hf_text)
        self.assertIn("ProductionIRDocument", hf_text)

    def test_progressive_disclosure_system_prompt_index(self) -> None:
        """Verify system prompt index renders compact byte-stable table."""
        index_table = self.skill_runtime.build_system_prompt_index()
        self.assertIn("### Available Skills", index_table)
        self.assertIn("`h9-research`", index_table)
        self.assertIn("`h9-content-planning`", index_table)
        self.assertIn("`h9-production`", index_table)
        self.assertIn("`h9-hyperframes`", index_table)

    def test_skill_resource_traversal_confinement(self) -> None:
        """Ensure path traversal attacks on skill resources are strictly blocked."""
        with self.assertRaises(ValueError):
            self.skill_runtime.load_skill_resource("h9-research", "../../../etc/passwd")


class TestProductionIRAST(unittest.TestCase):
    """Verify strict Pydantic v2 AST schema invariants on ProductionIRDocument."""

    def _create_valid_document(self) -> ProductionIRDocument:
        """Construct a baseline valid ProductionIRDocument with 2 scenes."""
        metadata = IRMetadata(
            project_id="proj_test_01",
            topic="Quantum Computing",
            title="Qubits and Superposition",
            aspect_ratio="16:9",
            fps=30,
        )
        audio = IRAudioTrack(
            audio_rel_path="assets/audio/narration.wav",
            total_duration_sec=10.0,
            sample_rate=44100,
            channels=2,
        )
        manifest = {
            "asset_01": IRAssetReference(
                asset_id="asset_01",
                file_path="assets/images/qubit.svg",
                file_sha256="0" * 64,
                media_type="image/svg+xml",
                verified=True,
            ),
            "asset_02": IRAssetReference(
                asset_id="asset_02",
                file_path="assets/images/bloch_sphere.svg",
                file_sha256="1" * 64,
                media_type="image/svg+xml",
                verified=True,
            ),
        }
        scenes = [
            IRSceneNode(
                scene_id="scene_01",
                scene_index=1,
                act_index=1,
                start_time_sec=0.0,
                duration_sec=5.0,
                narration=IRNarrationBlock(
                    full_text="Introduction to quantum computing principles.",
                    speech_beats=[
                        IRSpeechBeat(
                            beat_id="beat_01",
                            start_time_sec=0.0,
                            end_time_sec=5.0,
                            text="Introduction to quantum computing principles.",
                        )
                    ],
                ),
                visual_block=IRVisualBlockNode(
                    block_type=IRBlockType.REFERENCE_COLLAGE_HOOK,
                    parameters={"theme": "circuits"},
                    asset_bindings={"hero_image": "asset_01"},
                ),
            ),
            IRSceneNode(
                scene_id="scene_02",
                scene_index=2,
                act_index=2,
                start_time_sec=5.0,
                duration_sec=5.0,
                narration=IRNarrationBlock(
                    full_text="Understanding the Bloch sphere representation.",
                    speech_beats=[
                        IRSpeechBeat(
                            beat_id="beat_02",
                            start_time_sec=5.0,
                            end_time_sec=10.0,
                            text="Understanding the Bloch sphere representation.",
                        )
                    ],
                ),
                visual_block=IRVisualBlockNode(
                    block_type=IRBlockType.SPLIT_SCREEN_INTRO,
                    parameters={"left_header": "Classical", "right_header": "Quantum"},
                    asset_bindings={"hero_image": "asset_02"},
                ),
            ),
        ]
        return ProductionIRDocument(
            ir_version="1.0.0",
            metadata=metadata,
            audio_track=audio,
            asset_manifest=manifest,
            scenes=scenes,
        )

    def test_valid_document_instantiation(self) -> None:
        """Valid AST document instantiates cleanly and satisfies all model validators."""
        doc = self._create_valid_document()
        self.assertEqual(doc.ir_version, "1.0.0")
        self.assertEqual(len(doc.scenes), 2)
        self.assertEqual(doc.scenes[0].end_time_sec, 5.0)
        self.assertEqual(doc.scenes[1].end_time_sec, 10.0)
        self.assertIn("asset_01", doc.asset_manifest)

    def test_empty_scenes_rejected(self) -> None:
        """Invariant 0: ProductionIRDocument must contain at least one IRSceneNode."""
        doc = self._create_valid_document()
        with self.assertRaises(ValueError):
            ProductionIRDocument(
                ir_version="1.0.0",
                metadata=doc.metadata,
                audio_track=doc.audio_track,
                asset_manifest=doc.asset_manifest,
                scenes=[],
            )

    def test_temporal_discontinuity_rejected(self) -> None:
        """Invariant 1: Gap or overlap between scenes (> 0.05s) raises ValueError."""
        doc = self._create_valid_document()
        # Create a gap: scene 1 ends at 5.0s, scene 2 starts at 6.0s (1.0s gap)
        broken_scene_2 = doc.scenes[1].model_copy(update={"start_time_sec": 6.0})
        with self.assertRaises(ValueError) as ctx:
            ProductionIRDocument(
                ir_version="1.0.0",
                metadata=doc.metadata,
                audio_track=doc.audio_track,
                asset_manifest=doc.asset_manifest,
                scenes=[doc.scenes[0], broken_scene_2],
            )
        self.assertIn("Temporal Discontinuity", str(ctx.exception))

    def test_audio_drift_rejected(self) -> None:
        """Invariant 2: Divergence between total scene duration and audio length raises ValueError."""
        doc = self._create_valid_document()
        # Audio track is 10.0s, scenes total 10.0s. Change audio track to 12.0s (> 0.5s divergence)
        broken_audio = doc.audio_track.model_copy(update={"total_duration_sec": 12.0})
        with self.assertRaises(ValueError) as ctx:
            ProductionIRDocument(
                ir_version="1.0.0",
                metadata=doc.metadata,
                audio_track=broken_audio,
                asset_manifest=doc.asset_manifest,
                scenes=doc.scenes,
            )
        self.assertIn("Audio Drift", str(ctx.exception))

    def test_dangling_asset_reference_rejected(self) -> None:
        """Invariant 3: Binding a visual slot to a non-existent asset_id raises ValueError."""
        doc = self._create_valid_document()
        # Bind slot to "asset_999" which is not in asset_manifest
        broken_visual = doc.scenes[0].visual_block.model_copy(
            update={"asset_bindings": {"hero_image": "asset_999"}}
        )
        broken_scene_1 = doc.scenes[0].model_copy(update={"visual_block": broken_visual})
        with self.assertRaises(ValueError) as ctx:
            ProductionIRDocument(
                ir_version="1.0.0",
                metadata=doc.metadata,
                audio_track=doc.audio_track,
                asset_manifest=doc.asset_manifest,
                scenes=[broken_scene_1, doc.scenes[1]],
            )
        self.assertIn("Dangling Asset Reference", str(ctx.exception))

    def test_speech_beat_out_of_bounds_rejected(self) -> None:
        """Invariant 4: Speech beat escaping scene bounds raises ValueError."""
        doc = self._create_valid_document()
        # Scene 1 is [0.0, 5.0]. Beat ends at 7.0s (> 5.15s)
        broken_beat = doc.scenes[0].narration.speech_beats[0].model_copy(update={"end_time_sec": 7.0})
        broken_narration = doc.scenes[0].narration.model_copy(update={"speech_beats": [broken_beat]})
        broken_scene_1 = doc.scenes[0].model_copy(update={"narration": broken_narration})
        with self.assertRaises(ValueError) as ctx:
            ProductionIRDocument(
                ir_version="1.0.0",
                metadata=doc.metadata,
                audio_track=doc.audio_track,
                asset_manifest=doc.asset_manifest,
                scenes=[broken_scene_1, doc.scenes[1]],
            )
        self.assertIn("Speech Beat Out of Bounds", str(ctx.exception))

    def test_dual_inheritance_and_backward_compatibility(self) -> None:
        """Verify ProductionIRDocument satisfies isinstance(doc, ProductionIR) and exposes legacy properties."""
        doc = self._create_valid_document()
        self.assertIsInstance(doc, ProductionIR)
        self.assertEqual(doc.project_id, "proj_test_01")
        self.assertEqual(doc.aspect_ratio, "16:9")
        self.assertEqual(doc.duration_seconds, 10.0)
        self.assertEqual(len(doc.timeline_blocks), 2)
        self.assertIn("--primary-accent", doc.css_variables)
        self.assertEqual(len(doc.audio_tracks), 1)

    def test_to_script_conversion(self) -> None:
        """Verify AST document cleanly round-trips into a domain Script contract."""
        doc = self._create_valid_document()
        script = doc.to_script()
        self.assertIsInstance(script, Script)
        self.assertEqual(script.topic, "Quantum Computing")
        self.assertEqual(len(script.scenes), 2)
        self.assertEqual(script.scenes[0].scene_id, "scene_01")
        self.assertEqual(script.scenes[1].component_type, "split_screen_intro")


class TestScriptToIRCompilation(unittest.TestCase):
    """Verify genuine compilation from Script and AssetRecords to ProductionIRDocument."""

    def test_compile_script_to_ir_basic(self) -> None:
        """Compile a 4-scene script into a fully validated ProductionIRDocument."""
        scenes = [
            ScriptScene(
                scene_id="scene_01",
                title="Hook",
                start_time=0.0,
                duration=7.5,
                narration_text="The revolution of computing.",
                component_type="reference_collage_hook",
                beats=[
                    ScriptBeat(
                        beat_id="b1",
                        start_time=0.0,
                        end_time=7.5,
                        duration=7.5,
                        text="The revolution of computing.",
                    )
                ],
            ),
            ScriptScene(
                scene_id="scene_02",
                title="Context",
                start_time=7.5,
                duration=7.5,
                narration_text="From vacuum tubes to silicon wafers.",
                component_type="timeline_reveal",
                beats=[
                    ScriptBeat(
                        beat_id="b2",
                        start_time=7.5,
                        end_time=15.0,
                        duration=7.5,
                        text="From vacuum tubes to silicon wafers.",
                    )
                ],
            ),
            ScriptScene(
                scene_id="scene_03",
                title="Breakdown",
                start_time=15.0,
                duration=7.5,
                narration_text="Photolithography reaches the physical limit.",
                component_type="statistic_reveal",
                beats=[
                    ScriptBeat(
                        beat_id="b3",
                        start_time=15.0,
                        end_time=22.5,
                        duration=7.5,
                        text="Photolithography reaches the physical limit.",
                    )
                ],
            ),
            ScriptScene(
                scene_id="scene_04",
                title="Conclusion",
                start_time=22.5,
                duration=7.5,
                narration_text="The future of nanoscale manufacturing.",
                component_type="creator_bottom_collage",
                beats=[
                    ScriptBeat(
                        beat_id="b4",
                        start_time=22.5,
                        end_time=30.0,
                        duration=7.5,
                        text="The future of nanoscale manufacturing.",
                    )
                ],
            ),
        ]
        script = Script(
            topic="Semiconductors",
            title="The Chip Making Revolution",
            total_duration=30.0,
            full_transcript="The revolution of computing...",
            scenes=scenes,
        )

        ir_doc = compile_script_to_ir(script)
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(len(ir_doc.scenes), 4)
        self.assertEqual(ir_doc.audio_track.total_duration_sec, 30.0)
        self.assertEqual(ir_doc.metadata.topic, "Semiconductors")

        # Verify contiguity across all 4 scenes
        expected_t = 0.0
        for s in ir_doc.scenes:
            self.assertAlmostEqual(s.start_time_sec, expected_t, delta=0.01)
            expected_t += s.duration_sec
        self.assertAlmostEqual(expected_t, 30.0, delta=0.01)

    def test_compile_script_with_assets(self) -> None:
        """Verify AssetRecords are correctly integrated into asset_manifest and bindings."""
        asset_record = AssetRecord(
            asset_id="asset_euv_laser",
            local_path="assets/images/euv_laser.svg",
            file_sha256=hashlib.sha256(b"euv_laser_content").hexdigest(),
            media_type="image/svg+xml",
            dimensions=Dimensions(width=1920, height=1080),
            verification_status="VERIFIED",
            scene_target="scene_01",
        )
        scene = ScriptScene(
            scene_id="scene_01",
            title="EUV Core",
            start_time=0.0,
            duration=10.0,
            narration_text="Laser produced plasma generation.",
            visual_asset_path="assets/images/euv_laser.svg",
            component_type="reference_collage_hook",
        )
        script = Script(
            topic="EUV Lithography",
            title="Laser Produced Plasma",
            total_duration=10.0,
            scenes=[scene],
        )

        ir_doc = compile_script_to_ir(script, assets=[asset_record])
        self.assertIn("asset_euv_laser", ir_doc.asset_manifest)
        self.assertEqual(
            ir_doc.scenes[0].visual_block.asset_bindings.get("hero_image"),
            "asset_euv_laser",
        )

    def test_compile_script_auto_clamps_unbounded_beats(self) -> None:
        """Verify compiler auto-clamps out-of-bounds beats so resulting document is valid."""
        scene = ScriptScene(
            scene_id="scene_01",
            start_time=0.0,
            duration=5.0,
            narration_text="Clamped beat test.",
            beats=[
                ScriptBeat(
                    beat_id="b_unclamped",
                    start_time=0.0,
                    end_time=15.0,  # Far exceeds 5.0s scene
                    duration=15.0,
                    text="Clamped beat test.",
                )
            ],
        )
        script = Script(topic="Clamping", title="Clamping Test", total_duration=5.0, scenes=[scene])
        ir_doc = compile_script_to_ir(script)
        # Verify compiled beat was clamped to scene duration
        clamped_beat = ir_doc.scenes[0].narration.speech_beats[0]
        self.assertLessEqual(clamped_beat.end_time_sec, 5.0)


class TestHyperFramesIRIntegration(unittest.TestCase):
    """Verify HyperFrames compiler, composition generation, and runtime integration."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        from src.h9_runtime.bridge import reset_capability_bridges
        reset_capability_bridges()
        self.temp_dir.cleanup()

    def test_hyperframes_compiler_compiles_project(self) -> None:
        """HyperFramesCompiler compiles ProductionIRDocument into valid HTML/CSS/JS project."""
        scene = ScriptScene(
            scene_id="scene_01",
            title="Intro",
            start_time=0.0,
            duration=5.0,
            narration_text="Testing HyperFrames compilation.",
            component_type="reference_collage_hook",
        )
        script = Script(topic="Compiler Test", title="Compiler", total_duration=5.0, scenes=[scene])
        ir_doc = compile_script_to_ir(script)

        compiler = HyperFramesCompiler()
        project = compiler.compile(ir_doc, output_dir=self.output_path / "hf_project")

        self.assertTrue(project.exists())
        self.assertTrue(project.index_html.exists())
        self.assertTrue(project.styles_css.exists())
        self.assertTrue(project.main_js.exists())

        # Check composition validation
        val_result = project.validate()
        self.assertTrue(val_result.get("valid", False))

    def test_content_runtime_compile_production_ir(self) -> None:
        """DefaultContentRuntime.compile_production_ir returns ProductionIRDocument."""
        rt = DefaultContentRuntime(base_workspace_dir=self.output_path / "sessions")
        scene = ScriptScene(
            scene_id="scene_01",
            title="S1",
            start_time=0.0,
            duration=5.0,
            narration_text="Content runtime test.",
        )
        script = Script(topic="Runtime Test", title="Runtime", total_duration=5.0, scenes=[scene])
        ws = self.output_path / "sessions" / "test_sess" / "workspace"
        ws.mkdir(parents=True, exist_ok=True)

        ir_doc = rt.compile_production_ir(script, workspace_dir=ws)
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(len(ir_doc.scenes), 1)

    def test_capability_bridge_ir_seam_and_render(self) -> None:
        """HermesCapabilityBridge compiles ProductionIRDocument and renders video artifact."""
        bridge = HermesCapabilityBridge(
            session_id="test_bridge_ir",
            workspace_root=self.output_path / "bridge_ws",
        )
        try:
            scene = ScriptScene(
                scene_id="scene_01",
                title="Bridge Scene",
                start_time=0.0,
                duration=5.0,
                narration_text="Bridge integration scene.",
            )
            script = Script(topic="Bridge Seam", title="Bridge Title", total_duration=5.0, scenes=[scene])

            ir_doc = bridge.compile_production_ir(script)
            self.assertIsInstance(ir_doc, ProductionIRDocument)

            artifact = bridge.render_video(ir_doc)
            self.assertTrue(Path(artifact.video_path).exists())
            self.assertGreater(artifact.duration_seconds, 0.0)
        finally:
            bridge.close()


if __name__ == "__main__":
    unittest.main()
