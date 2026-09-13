"""tests/test_challenger_m3_stress.py

Adversarial Stress, Fuzzing, and Invariant Boundary Harness for Milestone 3
(Production IR AST and Native Hermes Skills Seam).

Empirical challenger harness designed to test:
1. Temporal Contiguity & Conservation Invariants:
   - Gaps between scenes (tiny > 0.05s, medium, large, initial scene offset)
   - Overlaps between scenes (tiny > 0.05s, medium, complete overlap, inverted order)
   - Boundary tolerance tests (within tolerance vs exceeding tolerance)
2. Audio Track Duration Drift Invariants:
   - Positive drift (+0.51s, +2.0s, +10.0s)
   - Negative drift (-0.51s, -2.0s, -10.0s)
   - Boundary tolerance tests (0.49s passes, 0.51s fails)
   - Non-positive audio duration (0.0s, negative)
3. Asset Manifest Integrity & Binding Invariants:
   - Dangling asset references in visual blocks
   - Multi-scene / multi-slot partial dangling references
   - Empty manifests with bound slots
   - Case sensitivity and whitespace corruptions
4. Speech Beat Bounds Clamping Invariants:
   - Beats starting before scene start (beyond 0.05s lead tolerance)
   - Beats ending after scene end (beyond 0.15s tail tolerance)
   - Beats completely outside scene intervals
   - Boundary tolerance verification (within tolerance passes, outside fails)
5. Structural & Schema Boundaries:
   - Zero scenes list rejection
   - Field-level constraint violations (negative durations, out-of-range WPM, invalid fps, etc.)
   - Invalid block types
6. Script-to-IR Compiler Defense & Normalization:
   - Normalization of unordered, non-contiguous, or missing script properties
   - Auto-clamping of out-of-bounds beats
   - Auto-synthesis of missing visual assets
7. HyperFrames Compilation & Legacy ProductionIR Compatibility:
   - Roundtrip script conversion
   - Dual inheritance contract verification
   - HyperFrames composition generation without assets (passes)
   - Empirical defect reproduction: HyperFramesCompiler crash when asset manifest is non-empty
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile
import unittest
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

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
    IRAudioTrack,
    IRBlockType,
    IRMetadata,
    IRNarrationBlock,
    IRSceneNode,
    IRSpeechBeat,
    IRTransitionSpec,
    IRVisualBlockNode,
    ProductionIRDocument,
    compile_script_to_ir,
)


def create_base_metadata(
    project_id: str = "proj_adversarial_m3",
    topic: str = "Adversarial Stress",
    title: str = "AST Invariant Hardening",
    aspect_ratio: str = "16:9",
    fps: int = 30,
) -> IRMetadata:
    """Helper to create valid metadata."""
    return IRMetadata(
        project_id=project_id,
        topic=topic,
        title=title,
        aspect_ratio=aspect_ratio,
        fps=fps,
        brand_primary_color="#00d2ff",
        brand_background_color="#0a0e17",
    )


def create_base_manifest(asset_ids: Optional[List[str]] = None) -> Dict[str, IRAssetReference]:
    """Helper to create valid asset manifest."""
    ids = asset_ids or ["asset_01", "asset_02"]
    manifest = {}
    for aid in ids:
        manifest[aid] = IRAssetReference(
            asset_id=aid,
            file_path=f"assets/images/{aid}.svg",
            file_sha256=hashlib.sha256(aid.encode("utf-8")).hexdigest(),
            media_type="image/svg+xml",
            width=1920,
            height=1080,
            aspect_ratio="16:9",
            license_type="Public Domain",
            verified=True,
        )
    return manifest


def create_scene_node(
    scene_id: str,
    scene_index: int,
    start_time_sec: float,
    duration_sec: float,
    asset_bindings: Optional[Dict[str, str]] = None,
    speech_beats: Optional[List[IRSpeechBeat]] = None,
    block_type: IRBlockType = IRBlockType.REFERENCE_COLLAGE_HOOK,
) -> IRSceneNode:
    """Helper to create a well-formed IRSceneNode."""
    end_time_sec = start_time_sec + duration_sec
    if speech_beats is None:
        speech_beats = [
            IRSpeechBeat(
                beat_id=f"beat_{scene_id}_1",
                start_time_sec=start_time_sec,
                end_time_sec=end_time_sec,
                text=f"Narration for {scene_id}",
                emphasis_words=[],
            )
        ]
    return IRSceneNode(
        scene_id=scene_id,
        scene_index=scene_index,
        act_index=1,
        start_time_sec=start_time_sec,
        duration_sec=duration_sec,
        narration=IRNarrationBlock(
            full_text=f"Narration for {scene_id}",
            voice_profile="default",
            target_wpm=145,
            speech_beats=speech_beats,
        ),
        visual_block=IRVisualBlockNode(
            block_type=block_type,
            parameters={"headline": f"Header {scene_id}"},
            asset_bindings=asset_bindings or {},
        ),
        transitions=IRTransitionSpec(
            entrance_type="fade",
            exit_type="fade",
            transition_duration_sec=0.4,
        ),
    )


class TestTemporalContiguityAdversarial(unittest.TestCase):
    """Stress testing Invariant 1: Temporal Conservation & Contiguity."""

    def setUp(self) -> None:
        self.meta = create_base_metadata()
        self.manifest = create_base_manifest(["asset_01", "asset_02", "asset_03"])

    def test_initial_scene_start_offset_rejected(self) -> None:
        """Scene 1 starting at > 0.05s violates expected initial start of 0.0s."""
        s1 = create_scene_node("s1", 1, start_time_sec=0.1, duration_sec=5.0)
        audio = IRAudioTrack(total_duration_sec=5.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[s1],
            )
        self.assertIn("Temporal Discontinuity", str(ctx.exception))
        self.assertIn("Scene s1", str(ctx.exception))

    def test_gap_between_scenes_rejected(self) -> None:
        """Gap of 0.2s between scene 1 (0-5s) and scene 2 (5.2-10.2s) must raise ValidationError."""
        s1 = create_scene_node("s1", 1, start_time_sec=0.0, duration_sec=5.0)
        s2 = create_scene_node("s2", 2, start_time_sec=5.2, duration_sec=5.0)
        audio = IRAudioTrack(total_duration_sec=10.2)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Temporal Discontinuity", str(ctx.exception))
        self.assertIn("Scene s2", str(ctx.exception))

    def test_overlap_between_scenes_rejected(self) -> None:
        """Overlap of 0.2s (scene 1 ends at 5.0s, scene 2 starts at 4.8s) must raise ValidationError."""
        s1 = create_scene_node("s1", 1, start_time_sec=0.0, duration_sec=5.0)
        s2 = create_scene_node("s2", 2, start_time_sec=4.8, duration_sec=5.0)
        audio = IRAudioTrack(total_duration_sec=9.8)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Temporal Discontinuity", str(ctx.exception))

    def test_tiny_gap_beyond_tolerance_rejected(self) -> None:
        """Gap of 0.06s exceeds 0.05s tolerance and must raise ValidationError."""
        s1 = create_scene_node("s1", 1, start_time_sec=0.0, duration_sec=5.0)
        s2 = create_scene_node("s2", 2, start_time_sec=5.06, duration_sec=5.0)
        audio = IRAudioTrack(total_duration_sec=10.06)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Temporal Discontinuity", str(ctx.exception))

    def test_tiny_gap_within_tolerance_accepted(self) -> None:
        """Gap of 0.04s is within 0.05s tolerance and must validate cleanly."""
        s1 = create_scene_node("s1", 1, start_time_sec=0.0, duration_sec=5.0)
        s2 = create_scene_node("s2", 2, start_time_sec=5.04, duration_sec=5.0)
        # Total expected_start = 5.0 + 5.0 = 10.0. Audio track matched to expected duration
        audio = IRAudioTrack(total_duration_sec=10.0)
        doc = ProductionIRDocument(
            metadata=self.meta,
            audio_track=audio,
            asset_manifest=self.manifest,
            scenes=[s1, s2],
        )
        self.assertEqual(len(doc.scenes), 2)

    def test_tiny_overlap_within_tolerance_accepted(self) -> None:
        """Overlap of 0.04s (scene 2 starts at 4.96s) is within 0.05s tolerance and must validate."""
        s1 = create_scene_node("s1", 1, start_time_sec=0.0, duration_sec=5.0)
        s2 = create_scene_node("s2", 2, start_time_sec=4.96, duration_sec=5.0)
        audio = IRAudioTrack(total_duration_sec=10.0)
        doc = ProductionIRDocument(
            metadata=self.meta,
            audio_track=audio,
            asset_manifest=self.manifest,
            scenes=[s1, s2],
        )
        self.assertEqual(len(doc.scenes), 2)

    def test_multi_scene_middle_gap_rejected(self) -> None:
        """In a 4-scene timeline, gap between scene 3 and scene 4 must be intercepted."""
        s1 = create_scene_node("s1", 1, 0.0, 5.0)
        s2 = create_scene_node("s2", 2, 5.0, 5.0)
        s3 = create_scene_node("s3", 3, 10.0, 5.0)
        s4 = create_scene_node("s4", 4, 16.0, 5.0)  # Gap of 1.0s
        audio = IRAudioTrack(total_duration_sec=21.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[s1, s2, s3, s4],
            )
        self.assertIn("Temporal Discontinuity", str(ctx.exception))
        self.assertIn("Scene s4", str(ctx.exception))

    def test_inverted_scene_order_rejected(self) -> None:
        """Scenes supplied out of order [scene 2 (5-10), scene 1 (0-5)] must be rejected."""
        s1 = create_scene_node("s1", 1, 0.0, 5.0)
        s2 = create_scene_node("s2", 2, 5.0, 5.0)
        audio = IRAudioTrack(total_duration_sec=10.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[s2, s1],
            )
        self.assertIn("Temporal Discontinuity", str(ctx.exception))


class TestAudioDurationDriftAdversarial(unittest.TestCase):
    """Stress testing Invariant 2: Audio Track Match and Drift Tolerance."""

    def setUp(self) -> None:
        self.meta = create_base_metadata()
        self.manifest = create_base_manifest(["asset_01"])
        # Baseline: 2 scenes of 15.0s each = 30.0s total scene duration
        self.s1 = create_scene_node("s1", 1, 0.0, 15.0)
        self.s2 = create_scene_node("s2", 2, 15.0, 15.0)

    def test_audio_drift_positive_2s_rejected(self) -> None:
        """Total scenes = 30.0s, audio = 32.0s (+2.0s drift) must raise ValidationError."""
        audio = IRAudioTrack(total_duration_sec=32.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[self.s1, self.s2],
            )
        self.assertIn("Audio Drift", str(ctx.exception))
        self.assertIn("30.0s", str(ctx.exception))
        self.assertIn("32.0s", str(ctx.exception))

    def test_audio_drift_negative_2s_rejected(self) -> None:
        """Total scenes = 30.0s, audio = 28.0s (-2.0s drift) must raise ValidationError."""
        audio = IRAudioTrack(total_duration_sec=28.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[self.s1, self.s2],
            )
        self.assertIn("Audio Drift", str(ctx.exception))

    def test_audio_drift_threshold_0_51s_rejected(self) -> None:
        """Drift of 0.51s (> 0.5s tolerance) must raise ValidationError."""
        audio = IRAudioTrack(total_duration_sec=30.51)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=audio,
                asset_manifest=self.manifest,
                scenes=[self.s1, self.s2],
            )
        self.assertIn("Audio Drift", str(ctx.exception))

    def test_audio_drift_threshold_0_49s_accepted(self) -> None:
        """Drift of 0.49s (<= 0.5s tolerance) must pass cleanly."""
        audio = IRAudioTrack(total_duration_sec=30.49)
        doc = ProductionIRDocument(
            metadata=self.meta,
            audio_track=audio,
            asset_manifest=self.manifest,
            scenes=[self.s1, self.s2],
        )
        self.assertEqual(doc.audio_track.total_duration_sec, 30.49)

    def test_non_positive_audio_duration_rejected_by_field(self) -> None:
        """IRAudioTrack total_duration_sec <= 0.0 must raise field-level ValidationError."""
        with self.assertRaises(ValidationError):
            IRAudioTrack(total_duration_sec=0.0)
        with self.assertRaises(ValidationError):
            IRAudioTrack(total_duration_sec=-5.0)


class TestAssetManifestIntegrityAdversarial(unittest.TestCase):
    """Stress testing Invariant 3: Asset Binding Integrity."""

    def setUp(self) -> None:
        self.meta = create_base_metadata()
        self.audio = IRAudioTrack(total_duration_sec=10.0)

    def test_dangling_asset_in_first_scene_rejected(self) -> None:
        """Binding 'hero_image' to undeclared 'ghost_asset_99' must raise ValidationError."""
        manifest = create_base_manifest(["asset_01"])
        s1 = create_scene_node(
            "s1", 1, 0.0, 5.0,
            asset_bindings={"hero_image": "ghost_asset_99"},
        )
        s2 = create_scene_node("s2", 2, 5.0, 5.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Dangling Asset Reference", str(ctx.exception))
        self.assertIn("ghost_asset_99", str(ctx.exception))
        self.assertIn("hero_image", str(ctx.exception))

    def test_dangling_asset_in_subsequent_scene_rejected(self) -> None:
        """Scene 1 is valid, Scene 2 contains dangling binding -> must raise ValidationError."""
        manifest = create_base_manifest(["asset_01", "asset_02"])
        s1 = create_scene_node("s1", 1, 0.0, 5.0, asset_bindings={"hero": "asset_01"})
        s2 = create_scene_node("s2", 2, 5.0, 5.0, asset_bindings={"chart": "missing_chart_asset"})
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Dangling Asset Reference", str(ctx.exception))
        self.assertIn("missing_chart_asset", str(ctx.exception))

    def test_partial_dangling_multiple_bindings_rejected(self) -> None:
        """Visual block has 2 bindings: one valid, one missing -> must raise ValidationError."""
        manifest = create_base_manifest(["asset_01"])
        s1 = create_scene_node(
            "s1", 1, 0.0, 10.0,
            asset_bindings={"left_img": "asset_01", "right_img": "dangling_right"},
        )
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=manifest,
                scenes=[s1],
            )
        self.assertIn("Dangling Asset Reference", str(ctx.exception))
        self.assertIn("dangling_right", str(ctx.exception))

    def test_case_sensitive_mismatch_rejected(self) -> None:
        """Asset IDs are strictly case sensitive: 'Asset_01' != 'asset_01'."""
        manifest = create_base_manifest(["Asset_01"])
        s1 = create_scene_node("s1", 1, 0.0, 10.0, asset_bindings={"hero": "asset_01"})
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=manifest,
                scenes=[s1],
            )
        self.assertIn("Dangling Asset Reference", str(ctx.exception))

    def test_empty_manifest_with_bindings_rejected(self) -> None:
        """Empty manifest with any asset binding must raise ValidationError."""
        s1 = create_scene_node("s1", 1, 0.0, 10.0, asset_bindings={"slot": "a1"})
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest={},
                scenes=[s1],
            )
        self.assertIn("Dangling Asset Reference", str(ctx.exception))


class TestSpeechBeatBoundsClampingAdversarial(unittest.TestCase):
    """Stress testing Invariant 4: Speech Beat Bounds Clamping."""

    def setUp(self) -> None:
        self.meta = create_base_metadata()
        self.manifest = create_base_manifest(["asset_01"])
        self.audio = IRAudioTrack(total_duration_sec=10.0)

    def test_beat_starts_before_scene_start_beyond_lead_tolerance(self) -> None:
        """Beat starts at 4.90s for Scene 2 [5.0s, 10.0s] (0.10s early > 0.05s tolerance)."""
        s1 = create_scene_node("s1", 1, 0.0, 5.0)
        bad_beat = IRSpeechBeat(
            beat_id="b_early",
            start_time_sec=4.90,  # 0.10s before scene start (limit is -0.05s -> 4.95s)
            end_time_sec=7.0,
            text="Early beat text.",
        )
        s2 = create_scene_node("s2", 2, 5.0, 5.0, speech_beats=[bad_beat])
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=self.manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Speech Beat Out of Bounds", str(ctx.exception))
        self.assertIn("b_early", str(ctx.exception))

    def test_beat_starts_before_scene_start_within_lead_tolerance(self) -> None:
        """Beat starts at 4.96s for Scene 2 [5.0s, 10.0s] (0.04s early <= 0.05s tolerance)."""
        s1 = create_scene_node("s1", 1, 0.0, 5.0)
        ok_beat = IRSpeechBeat(
            beat_id="b_ok_early",
            start_time_sec=4.96,
            end_time_sec=7.0,
            text="Acceptable early beat text.",
        )
        s2 = create_scene_node("s2", 2, 5.0, 5.0, speech_beats=[ok_beat])
        doc = ProductionIRDocument(
            metadata=self.meta,
            audio_track=self.audio,
            asset_manifest=self.manifest,
            scenes=[s1, s2],
        )
        self.assertEqual(len(doc.scenes), 2)

    def test_beat_ends_after_scene_end_beyond_tail_tolerance(self) -> None:
        """Beat ends at 5.20s for Scene 1 [0.0s, 5.0s] (0.20s late > 0.15s tolerance)."""
        bad_beat = IRSpeechBeat(
            beat_id="b_late",
            start_time_sec=1.0,
            end_time_sec=5.20,  # Limit is +0.15s -> 5.15s
            text="Late trailing beat.",
        )
        s1 = create_scene_node("s1", 1, 0.0, 5.0, speech_beats=[bad_beat])
        s2 = create_scene_node("s2", 2, 5.0, 5.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=self.manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Speech Beat Out of Bounds", str(ctx.exception))
        self.assertIn("b_late", str(ctx.exception))

    def test_beat_ends_after_scene_end_within_tail_tolerance(self) -> None:
        """Beat ends at 5.12s for Scene 1 [0.0s, 5.0s] (0.12s late <= 0.15s tolerance)."""
        ok_beat = IRSpeechBeat(
            beat_id="b_ok_late",
            start_time_sec=1.0,
            end_time_sec=5.12,
            text="Acceptable trailing beat.",
        )
        s1 = create_scene_node("s1", 1, 0.0, 5.0, speech_beats=[ok_beat])
        s2 = create_scene_node("s2", 2, 5.0, 5.0)
        doc = ProductionIRDocument(
            metadata=self.meta,
            audio_track=self.audio,
            asset_manifest=self.manifest,
            scenes=[s1, s2],
        )
        self.assertEqual(len(doc.scenes), 2)

    def test_beat_completely_outside_scene_interval(self) -> None:
        """Beat [12.0s, 14.0s] placed inside Scene 1 [0.0s, 5.0s] must be rejected."""
        wild_beat = IRSpeechBeat(
            beat_id="b_wild",
            start_time_sec=12.0,
            end_time_sec=14.0,
            text="Wild beat completely misplaced.",
        )
        s1 = create_scene_node("s1", 1, 0.0, 5.0, speech_beats=[wild_beat])
        s2 = create_scene_node("s2", 2, 5.0, 5.0)
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=self.manifest,
                scenes=[s1, s2],
            )
        self.assertIn("Speech Beat Out of Bounds", str(ctx.exception))


class TestEmptyAndCorruptDocumentStructures(unittest.TestCase):
    """Stress testing Invariant 0 and low-level schema boundaries."""

    def setUp(self) -> None:
        self.meta = create_base_metadata()
        self.manifest = create_base_manifest(["asset_01"])
        self.audio = IRAudioTrack(total_duration_sec=10.0)

    def test_zero_scenes_rejected(self) -> None:
        """Invariant 0: Empty scenes list must raise ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            ProductionIRDocument(
                metadata=self.meta,
                audio_track=self.audio,
                asset_manifest=self.manifest,
                scenes=[],
            )
        self.assertIn("at least one IRSceneNode", str(ctx.exception))

    def test_negative_scene_duration_rejected(self) -> None:
        """IRSceneNode duration_sec <= 0 must fail field validation."""
        with self.assertRaises(ValidationError):
            create_scene_node("s1", 1, 0.0, duration_sec=-1.0)
        with self.assertRaises(ValidationError):
            create_scene_node("s1", 1, 0.0, duration_sec=0.0)

    def test_negative_scene_start_time_rejected(self) -> None:
        """IRSceneNode start_time_sec < 0 must fail field validation."""
        with self.assertRaises(ValidationError):
            create_scene_node("s1", 1, start_time_sec=-0.5, duration_sec=5.0)

    def test_invalid_aspect_ratio_metadata_rejected(self) -> None:
        """IRMetadata aspect_ratio not matching regex (16:9|9:16|1:1) must fail."""
        with self.assertRaises(ValidationError):
            create_base_metadata(aspect_ratio="4:3")
        with self.assertRaises(ValidationError):
            create_base_metadata(aspect_ratio="21:9")

    def test_invalid_fps_metadata_rejected(self) -> None:
        """IRMetadata fps outside [15, 60] must fail."""
        with self.assertRaises(ValidationError):
            create_base_metadata(fps=10)
        with self.assertRaises(ValidationError):
            create_base_metadata(fps=120)

    def test_invalid_target_wpm_rejected(self) -> None:
        """IRNarrationBlock target_wpm outside [90, 220] must fail."""
        with self.assertRaises(ValidationError):
            IRNarrationBlock(full_text="test", target_wpm=50)
        with self.assertRaises(ValidationError):
            IRNarrationBlock(full_text="test", target_wpm=300)

    def test_invalid_transition_duration_rejected(self) -> None:
        """IRTransitionSpec transition_duration_sec outside [0.0, 2.0] must fail."""
        with self.assertRaises(ValidationError):
            IRTransitionSpec(transition_duration_sec=-0.5)
        with self.assertRaises(ValidationError):
            IRTransitionSpec(transition_duration_sec=3.5)

    def test_empty_string_identifiers_rejected(self) -> None:
        """Empty string identifiers for scene_id, beat_id, project_id must fail min_length=1."""
        with self.assertRaises(ValidationError):
            create_scene_node("", 1, 0.0, 5.0)
        with self.assertRaises(ValidationError):
            IRSpeechBeat(beat_id="", start_time_sec=0.0, end_time_sec=1.0, text="hi")
        with self.assertRaises(ValidationError):
            create_base_metadata(project_id="")

    def test_invalid_block_type_enum_rejected(self) -> None:
        """Visual block with non-existent block type must fail Enum validation."""
        with self.assertRaises(ValidationError):
            IRVisualBlockNode(block_type="unsupported_quantum_viz")


class TestCompilerAdversarialDefense(unittest.TestCase):
    """Verify compile_script_to_ir normalizes corrupt or messy input data without crashing."""

    def test_compiler_normalizes_unordered_scenes(self) -> None:
        """Script with erratic start times is sanitized into strictly contiguous scenes."""
        sc1 = ScriptScene(
            scene_id="s1",
            title="S1",
            start_time=100.0,  # Wild start time
            duration=6.0,
            narration_text="Scene one.",
        )
        sc2 = ScriptScene(
            scene_id="s2",
            title="S2",
            start_time=2.0,  # Out of sequence
            duration=4.0,
            narration_text="Scene two.",
        )
        script = Script(
            topic="Sanitization",
            title="Sanitization Test",
            total_duration=10.0,
            scenes=[sc1, sc2],
        )
        ir_doc = compile_script_to_ir(script)
        self.assertIsInstance(ir_doc, ProductionIRDocument)
        self.assertEqual(ir_doc.scenes[0].start_time_sec, 0.0)
        self.assertEqual(ir_doc.scenes[0].duration_sec, 6.0)
        self.assertEqual(ir_doc.scenes[1].start_time_sec, 6.0)
        self.assertEqual(ir_doc.scenes[1].duration_sec, 4.0)
        self.assertEqual(ir_doc.audio_track.total_duration_sec, 10.0)

    def test_compiler_auto_clamps_wild_speech_beats(self) -> None:
        """Script with speech beats extending far past scene duration are clamped."""
        sc = ScriptScene(
            scene_id="s1",
            title="S1",
            start_time=0.0,
            duration=5.0,
            narration_text="Clamping beat test.",
            beats=[
                ScriptBeat(
                    beat_id="b1",
                    start_time=0.0,
                    end_time=99.0,  # Far beyond 5.0s
                    duration=99.0,
                    text="Clamping beat test.",
                )
            ],
        )
        script = Script(topic="Clamping", title="Clamping", total_duration=5.0, scenes=[sc])
        ir_doc = compile_script_to_ir(script)
        clamped_beat = ir_doc.scenes[0].narration.speech_beats[0]
        self.assertLessEqual(clamped_beat.end_time_sec, 5.0)

    def test_compiler_auto_synthesizes_missing_manifest_assets(self) -> None:
        """Script with visual_asset_path not in asset list gets auto-synthesized in manifest."""
        sc = ScriptScene(
            scene_id="s1",
            title="S1",
            start_time=0.0,
            duration=5.0,
            narration_text="Asset test.",
            visual_asset_path="assets/images/unlisted_diagram.svg",
        )
        script = Script(topic="Asset Synthesis", title="Synthesis", total_duration=5.0, scenes=[sc])
        # Pass empty assets list
        ir_doc = compile_script_to_ir(script, assets=[])
        # Manifest should contain auto-synthesized entry
        self.assertTrue(len(ir_doc.asset_manifest) >= 1)
        hero_aid = ir_doc.scenes[0].visual_block.asset_bindings.get("hero_image")
        self.assertIsNotNone(hero_aid)
        self.assertIn(hero_aid, ir_doc.asset_manifest)
        self.assertEqual(
            ir_doc.asset_manifest[hero_aid].file_path,
            "assets/images/unlisted_diagram.svg",
        )

    def test_compiler_handles_empty_scenes_with_fallback(self) -> None:
        """Script with scenes=[] gets a valid default fallback scene instead of failing."""
        script = Script(
            topic="Empty Test",
            title="Empty Test Title",
            total_duration=10.0,
            scenes=[],
        )
        ir_doc = compile_script_to_ir(script)
        self.assertEqual(len(ir_doc.scenes), 1)
        self.assertEqual(ir_doc.scenes[0].start_time_sec, 0.0)
        self.assertEqual(ir_doc.scenes[0].duration_sec, 10.0)

    def test_compiler_enforces_minimum_scene_duration(self) -> None:
        """Scene with duration=0.0s or tiny duration is enforced to minimum 0.5s."""
        sc = ScriptScene(
            scene_id="s1",
            title="S1",
            start_time=0.0,
            duration=0.01,
            narration_text="Tiny duration scene.",
        )
        script = Script(topic="Min Duration", title="Min Dur", total_duration=0.5, scenes=[sc])
        ir_doc = compile_script_to_ir(script)
        self.assertGreaterEqual(ir_doc.scenes[0].duration_sec, 0.5)


class TestHyperFramesCompilationAndLegacyCompatibility(unittest.TestCase):
    """Verify AST serialization, dual inheritance compatibility, and HyperFrames compilation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_roundtrip_script_to_ir_to_script(self) -> None:
        """Compile Script -> ProductionIRDocument -> to_script() preserves structure and data."""
        scenes = [
            ScriptScene(
                scene_id="s1",
                title="Scene 1",
                start_time=0.0,
                duration=5.0,
                narration_text="First scene narrative.",
                component_type="reference_collage_hook",
            ),
            ScriptScene(
                scene_id="s2",
                title="Scene 2",
                start_time=5.0,
                duration=5.0,
                narration_text="Second scene narrative.",
                component_type="statistic_reveal",
            ),
        ]
        script = Script(
            topic="Roundtrip",
            title="Roundtrip Verification",
            total_duration=10.0,
            full_transcript="First scene narrative. Second scene narrative.",
            scenes=scenes,
        )
        ir_doc = compile_script_to_ir(script)
        reconstituted_script = ir_doc.to_script()

        self.assertEqual(reconstituted_script.topic, "Roundtrip")
        self.assertEqual(reconstituted_script.total_duration, 10.0)
        self.assertEqual(len(reconstituted_script.scenes), 2)
        self.assertEqual(reconstituted_script.scenes[0].scene_id, "s1")
        self.assertEqual(reconstituted_script.scenes[1].scene_id, "s2")
        self.assertEqual(reconstituted_script.scenes[1].component_type, "statistic_reveal")

    def test_pydantic_model_dump_and_validate_roundtrip(self) -> None:
        """ProductionIRDocument.to_dict() and model_validate roundtrip cleanly."""
        meta = create_base_metadata()
        manifest = create_base_manifest(["asset_01"])
        audio = IRAudioTrack(total_duration_sec=5.0)
        s1 = create_scene_node("s1", 1, 0.0, 5.0, asset_bindings={"hero": "asset_01"})
        doc = ProductionIRDocument(
            metadata=meta,
            audio_track=audio,
            asset_manifest=manifest,
            scenes=[s1],
        )

        dumped = doc.to_dict()
        self.assertIsInstance(dumped, dict)
        re_validated = ProductionIRDocument.model_validate(dumped)
        self.assertEqual(re_validated.metadata.project_id, meta.project_id)
        self.assertEqual(len(re_validated.scenes), 1)

    def test_legacy_production_ir_duck_typing_and_inheritance(self) -> None:
        """Verify backwards compatibility contract: isinstance(ProductionIR) and legacy attributes."""
        meta = create_base_metadata(project_id="proj_legacy_compat")
        manifest = create_base_manifest(["asset_01"])
        audio = IRAudioTrack(total_duration_sec=5.0)
        s1 = create_scene_node("s1", 1, 0.0, 5.0, asset_bindings={"hero": "asset_01"})
        doc = ProductionIRDocument(
            metadata=meta,
            audio_track=audio,
            asset_manifest=manifest,
            scenes=[s1],
        )

        # Dual inheritance check
        self.assertIsInstance(doc, ProductionIR)
        # Check synchronized legacy fields
        self.assertEqual(doc.project_id, "proj_legacy_compat")
        self.assertEqual(doc.duration_seconds, 5.0)
        self.assertEqual(doc.aspect_ratio, "16:9")
        self.assertEqual(doc.fps, 30)
        self.assertTrue(len(doc.timeline_blocks) == 1)
        self.assertTrue(len(doc.audio_tracks) == 1)
        self.assertIn("--primary-accent", doc.css_variables)

    def test_hyperframes_compiler_compiles_project_without_assets(self) -> None:
        """HyperFramesCompiler compiles AST without assets into valid project and passes linter."""
        meta = create_base_metadata()
        audio = IRAudioTrack(total_duration_sec=5.0)
        s1 = create_scene_node("s1", 1, 0.0, 5.0)
        doc = ProductionIRDocument(
            metadata=meta,
            audio_track=audio,
            asset_manifest={},
            scenes=[s1],
        )

        compiler = HyperFramesCompiler()
        target_dir = self.output_path / "test_no_assets_hf"
        project = compiler.compile(doc, output_dir=target_dir)

        self.assertTrue(project.exists())
        self.assertTrue(project.index_html.exists())
        self.assertTrue(project.styles_css.exists())
        self.assertTrue(project.main_js.exists())

        val_result = project.validate()
        self.assertTrue(val_result.get("valid", False))

    def test_hyperframes_compiler_asset_record_attribute_defect_reproduction(self) -> None:
        """Empirical Defect Reproduction:
        When an AST document has non-empty asset_manifest, HyperFramesCompiler converts
        manifest entries into AssetRecord(local_path=ref.file_path, ...).
        However, HyperFramesAdapter._stage_assets line 402 accesses item.file_path,
        which does not exist on AssetRecord (which defines local_path), causing
        AttributeError: 'AssetRecord' object has no attribute 'file_path'.
        """
        meta = create_base_metadata()
        manifest = create_base_manifest(["asset_01", "asset_02"])
        audio = IRAudioTrack(total_duration_sec=10.0)
        s1 = create_scene_node("s1", 1, 0.0, 5.0, asset_bindings={"hero_image": "asset_01"})
        s2 = create_scene_node(
            "s2", 2, 5.0, 5.0,
            asset_bindings={"hero_image": "asset_02"},
            block_type=IRBlockType.SPLIT_SCREEN_INTRO,
        )
        doc = ProductionIRDocument(
            metadata=meta,
            audio_track=audio,
            asset_manifest=manifest,
            scenes=[s1, s2],
        )

        compiler = HyperFramesCompiler()
        target_dir = self.output_path / "test_adversarial_hf"

        # Empirically verify that this raises AttributeError on AssetRecord.file_path
        with self.assertRaises(AttributeError) as ctx:
            compiler.compile(doc, output_dir=target_dir)
        self.assertIn("file_path", str(ctx.exception))
        self.assertIn("AssetRecord", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
