"""Adversarial stress-test suite for Harness 9 Pydantic v2 Production Contracts.

Empirically tests:
1. Malformed data, boundary conditions, regex violations, type mismatches.
2. Missing required fields across all 17 contracts.
3. Extra fields preservation and dict-like subscripting behavior (H9BaseModel).
4. Lossless JSON, YAML, and Dict round-trip serialization for all 17 contracts.
5. Atomic save/load functionality and error handling for malformed files.
6. Scorecard calculation mathematical invariants and edge cases.
7. Backward compatibility and legacy model imports.
"""

from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError
import yaml

import src.models as models_pkg
from src.models.contracts import (
    H9BaseModel,
    CreatorProfile,
    ContentBrief,
    ResearchPlan,
    SourceRecord,
    ClaimRecord,
    TalkingPointRecord,
    StatisticRecord,
    ResearchDossier,
    EditorialScorecard,
    AngleScorecard,
    EditorialAngle,
    OutlineAct,
    ContentOutline,
    ScriptBeat,
    ScriptScene,
    Script,
    AssetRequirement,
    Dimensions,
    LicenseInfo,
    AssetRecord,
    EvaluationLayer,
    EvaluationReport,
    RenderArtifact,
    PublishPackage,
    AnalyticsSnapshot,
    LearningCandidate,
)


class TestContractsAdversarial(unittest.TestCase):
    """Rigorous empirical stress tests for all 17 Pydantic schemas."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # =======================================================================
    # SECTION 1: Malformed Data & Boundary Value Stress Tests
    # =======================================================================

    def test_01_creator_profile_boundaries_and_regex(self):
        """Stress-test CreatorProfile regex, empty strings, and color dictionary."""
        # 1. Valid instances across all allowed aspect ratio patterns
        for ratio in ["16:9", "9:16", "1:1"]:
            p = CreatorProfile(creator_id="id1", display_name="Name", default_format=ratio)
            self.assertEqual(p.default_format, ratio)

        # 2. Regex violations
        invalid_ratios = ["4:3", "21:9", "16:9 ", " 16:9", "16-9", "", "custom", "16:9\n"]
        for bad_ratio in invalid_ratios:
            with self.assertRaises(ValidationError, msg=f"Failed to reject invalid ratio: {bad_ratio}"):
                CreatorProfile(creator_id="id1", display_name="Name", default_format=bad_ratio)

        # 3. Empty string violations for min_length fields
        with self.assertRaises(ValidationError):
            CreatorProfile(creator_id="", display_name="Valid")
        with self.assertRaises(ValidationError):
            CreatorProfile(creator_id="valid", display_name="")

        # 4. Custom colors and metadata preservation
        p = CreatorProfile(
            creator_id="c_001",
            display_name="Creator Alpha",
            brand_colors={"primary": "#123456", "custom_glow": "rgba(255,0,0,0.5)"},
            metadata={"deep": {"nested": [1, 2, 3]}},
        )
        self.assertEqual(p.brand_colors["custom_glow"], "rgba(255,0,0,0.5)")
        self.assertEqual(p.metadata["deep"]["nested"], [1, 2, 3])

    def test_02_content_brief_boundaries_and_length(self):
        """Stress-test ContentBrief boundaries for duration, topic length, and aspect ratios."""
        # 1. Duration lower bound: 5 is valid, 4 is invalid
        b_min = ContentBrief(project_id="p1", topic="T", target_duration_seconds=5)
        self.assertEqual(b_min.target_duration_seconds, 5)
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="T", target_duration_seconds=4)
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="T", target_duration_seconds=0)
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="T", target_duration_seconds=-10)

        # 2. Duration upper bound: 600 is valid, 601 is invalid
        b_max = ContentBrief(project_id="p1", topic="T", target_duration_seconds=600)
        self.assertEqual(b_max.target_duration_seconds, 600)
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="T", target_duration_seconds=601)

        # 3. Topic length: min 1, max 500
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="", target_duration_seconds=30)

        topic_500 = "x" * 500
        b_500 = ContentBrief(project_id="p1", topic=topic_500, target_duration_seconds=30)
        self.assertEqual(len(b_500.topic), 500)

        topic_501 = "x" * 501
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic=topic_501, target_duration_seconds=30)

        # 4. Aspect ratios
        for ratio in ["16:9", "9:16", "1:1"]:
            b = ContentBrief(project_id="p1", topic="T", aspect_ratio=ratio)
            self.assertEqual(b.aspect_ratio, ratio)
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="T", aspect_ratio="4:3")

    def test_03_research_plan_boundaries(self):
        """Stress-test ResearchPlan claim counts, timeouts, and query tuples."""
        # 1. Target claim count ge=1
        rp = ResearchPlan(topic="Topic", target_claim_count=1)
        self.assertEqual(rp.target_claim_count, 1)
        with self.assertRaises(ValidationError):
            ResearchPlan(topic="Topic", target_claim_count=0)
        with self.assertRaises(ValidationError):
            ResearchPlan(topic="Topic", target_claim_count=-5)

        # 2. Timeout seconds ge=0.1
        rp_t = ResearchPlan(topic="Topic", timeout_seconds=0.1)
        self.assertEqual(rp_t.timeout_seconds, 0.1)
        with self.assertRaises(ValidationError):
            ResearchPlan(topic="Topic", timeout_seconds=0.0)
        with self.assertRaises(ValidationError):
            ResearchPlan(topic="Topic", timeout_seconds=-1.0)

        # 3. Empty topic
        with self.assertRaises(ValidationError):
            ResearchPlan(topic="")

        # 4. Search query format (List of Tuple[str, str])
        queries = [("cat1", "query 1"), ("cat2", "query 2")]
        rp_q = ResearchPlan(topic="Topic", search_queries=queries)
        self.assertEqual(rp_q.search_queries, queries)

    def test_04_source_and_claim_record_boundaries(self):
        """Stress-test SourceRecord and ClaimRecord confidence and reliability scores."""
        # 1. Reliability score boundaries [0.0, 1.0]
        s_0 = SourceRecord(title="T", url="http://a", reliability_score=0.0)
        s_1 = SourceRecord(title="T", url="http://a", reliability_score=1.0)
        self.assertEqual(s_0.reliability_score, 0.0)
        self.assertEqual(s_1.reliability_score, 1.0)

        with self.assertRaises(ValidationError):
            SourceRecord(title="T", url="http://a", reliability_score=-0.001)
        with self.assertRaises(ValidationError):
            SourceRecord(title="T", url="http://a", reliability_score=1.001)
        with self.assertRaises(ValidationError):
            SourceRecord(title="", url="http://a")
        with self.assertRaises(ValidationError):
            SourceRecord(title="T", url="")

        # 2. ClaimRecord confidence boundaries [0.0, 1.0]
        src = SourceRecord(title="Source", url="https://example.com")
        c_0 = ClaimRecord(claim_id="c1", claim_text="Text", confidence_score=0.0, primary_source=src)
        c_1 = ClaimRecord(claim_id="c1", claim_text="Text", confidence_score=1.0, primary_source=src)
        self.assertEqual(c_0.confidence_score, 0.0)
        self.assertEqual(c_1.confidence_score, 1.0)

        with self.assertRaises(ValidationError):
            ClaimRecord(claim_id="c1", claim_text="Text", confidence_score=-0.1, primary_source=src)
        with self.assertRaises(ValidationError):
            ClaimRecord(claim_id="c1", claim_text="Text", confidence_score=1.1, primary_source=src)
        with self.assertRaises(ValidationError):
            ClaimRecord(claim_id="", claim_text="Text", primary_source=src)
        with self.assertRaises(ValidationError):
            ClaimRecord(claim_id="c1", claim_text="", primary_source=src)

    def test_05_talking_point_and_statistic_boundaries(self):
        """Stress-test TalkingPointRecord and StatisticRecord fields."""
        # 1. beat_index ge=1, estimated_duration_sec ge=0.0
        tp = TalkingPointRecord(beat_index=1, estimated_duration_sec=0.0)
        self.assertEqual(tp.beat_index, 1)
        self.assertEqual(tp.estimated_duration_sec, 0.0)

        with self.assertRaises(ValidationError):
            TalkingPointRecord(beat_index=0)
        with self.assertRaises(ValidationError):
            TalkingPointRecord(beat_index=-1)
        with self.assertRaises(ValidationError):
            TalkingPointRecord(estimated_duration_sec=-0.5)

        # 2. StatisticRecord
        stat = StatisticRecord(metric="Clock Speed", value="2.048 MHz", context="AGC CPU", source_claim_id="c1")
        self.assertEqual(stat.metric, "Clock Speed")

    def test_06_editorial_scorecard_math_and_boundaries(self):
        """Stress-test EditorialScorecard 9-dimension scorecard calculation and bounds."""
        # All 9 dimensions must be bounded [0.0, 1.0]
        dimension_fields = [
            "audience_relevance",
            "novelty",
            "hook_potential",
            "narrative_potential",
            "creator_fit",
            "evidence_availability",
            "visual_potential",
            "platform_fit",
            "saturation_risk",
        ]
        for field in dimension_fields:
            kwargs_low = {field: -0.01}
            with self.assertRaises(ValidationError, msg=f"Allowed negative for {field}"):
                EditorialScorecard(**kwargs_low)
            kwargs_high = {field: 1.01}
            with self.assertRaises(ValidationError, msg=f"Allowed >1.0 for {field}"):
                EditorialScorecard(**kwargs_high)

        # Test positive composite score calculation
        card_perfect = EditorialScorecard(
            audience_relevance=1.0,
            novelty=1.0,
            hook_potential=1.0,
            narrative_potential=1.0,
            creator_fit=1.0,
            evidence_availability=1.0,
            visual_potential=1.0,
            platform_fit=1.0,
            saturation_risk=0.0,
        )
        self.assertAlmostEqual(card_perfect.composite_score, 1.0, places=4)

        # If explicitly passed non-zero composite_score, it should be preserved
        card_manual = EditorialScorecard(
            audience_relevance=0.5,
            composite_score=0.9999,
        )
        self.assertEqual(card_manual.composite_score, 0.9999)

    def test_06_scorecard_zero_recursion_fix(self):
        """Verify zero composite score does not trigger infinite recursion and computes cleanly."""
        card = EditorialScorecard(
            audience_relevance=0.0,
            novelty=0.0,
            hook_potential=0.0,
            narrative_potential=0.0,
            creator_fit=0.0,
            evidence_availability=0.0,
            visual_potential=0.0,
            platform_fit=0.0,
            saturation_risk=1.0,
        )
        self.assertEqual(card.composite_score, 0.0)

    def test_07_outline_act_and_content_outline_boundaries(self):
        """Stress-test OutlineAct percentages and ContentOutline fields."""
        # 1. OutlineAct target percentages [0.0, 1.0] and act_index ge=1
        act = OutlineAct(act_index=1, act_name="Intro", target_start_pct=0.0, target_end_pct=0.25)
        self.assertEqual(act.act_index, 1)

        with self.assertRaises(ValidationError):
            OutlineAct(act_index=0, act_name="Bad")
        with self.assertRaises(ValidationError):
            OutlineAct(act_index=1, act_name="")
        with self.assertRaises(ValidationError):
            OutlineAct(act_index=1, act_name="Bad", target_start_pct=-0.1)
        with self.assertRaises(ValidationError):
            OutlineAct(act_index=1, act_name="Bad", target_end_pct=1.1)

        # 2. ContentOutline
        co = ContentOutline(
            project_id="p1",
            topic="Topic",
            angle_id="a1",
            total_estimated_duration=45.0,
        )
        self.assertEqual(co.total_estimated_duration, 45.0)
        with self.assertRaises(ValidationError):
            ContentOutline(project_id="", topic="T", angle_id="a1")
        with self.assertRaises(ValidationError):
            ContentOutline(project_id="p1", topic="", angle_id="a1")
        with self.assertRaises(ValidationError):
            ContentOutline(project_id="p1", topic="T", angle_id="")
        with self.assertRaises(ValidationError):
            ContentOutline(project_id="p1", topic="T", angle_id="a1", total_estimated_duration=-1.0)

    def test_08_script_beat_scene_boundaries(self):
        """Stress-test ScriptBeat, ScriptScene (duration gt 0), and Script."""
        # 1. ScriptBeat timing ge=0.0 and text min_length=1
        beat = ScriptBeat(beat_id="b1", text="Hello world", start_time=0.0, end_time=2.0, duration=2.0)
        self.assertEqual(beat.duration, 2.0)

        with self.assertRaises(ValidationError):
            ScriptBeat(beat_id="", text="Hello")
        with self.assertRaises(ValidationError):
            ScriptBeat(beat_id="b1", text="")
        with self.assertRaises(ValidationError):
            ScriptBeat(beat_id="b1", text="Hello", start_time=-1.0)
        with self.assertRaises(ValidationError):
            ScriptBeat(beat_id="b1", text="Hello", duration=-0.5)

        # 2. ScriptScene duration gt=0.0 (strictly positive)
        scene = ScriptScene(scene_id="s1", duration=0.001)
        self.assertEqual(scene.duration, 0.001)

        with self.assertRaises(ValidationError, msg="Allowed 0.0 duration on ScriptScene"):
            ScriptScene(scene_id="s1", duration=0.0)
        with self.assertRaises(ValidationError):
            ScriptScene(scene_id="s1", duration=-5.0)
        with self.assertRaises(ValidationError):
            ScriptScene(scene_id="")

        # 3. Script validation
        script = Script(topic="T", title="Title", total_duration=0.0)
        self.assertEqual(script.total_duration, 0.0)
        with self.assertRaises(ValidationError):
            Script(topic="", title="Title")
        with self.assertRaises(ValidationError):
            Script(topic="T", title="")
        with self.assertRaises(ValidationError):
            Script(topic="T", title="Title", total_duration=-1.0)

    def test_09_asset_requirement_and_record_boundaries(self):
        """Stress-test AssetRequirement and AssetRecord fields and checksums."""
        # 1. AssetRequirement
        req = AssetRequirement(requirement_id="r1", scene_id="s1", visual_query="quantum computer chip")
        self.assertEqual(req.visual_query, "quantum computer chip")
        with self.assertRaises(ValidationError):
            AssetRequirement(requirement_id="", scene_id="s1", visual_query="query")
        with self.assertRaises(ValidationError):
            AssetRequirement(requirement_id="r1", scene_id="", visual_query="query")
        with self.assertRaises(ValidationError):
            AssetRequirement(requirement_id="r1", scene_id="s1", visual_query="")

        # 2. Dimensions
        dim = Dimensions(width=3840, height=2160, aspect_ratio="16:9")
        self.assertEqual(dim.width, 3840)

        # 3. LicenseInfo
        lic = LicenseInfo(license_type="MIT", attribution_required=True, commercial_use_allowed=True)
        self.assertTrue(lic.attribution_required)

        # 4. AssetRecord
        sha256_mock = "a" * 64
        rec = AssetRecord(
            asset_id="a1",
            local_path="assets/img.svg",
            file_sha256=sha256_mock,
            dimensions=dim,
            license=lic,
        )
        self.assertEqual(rec.file_sha256, sha256_mock)
        with self.assertRaises(ValidationError):
            AssetRecord(asset_id="", local_path="p", file_sha256=sha256_mock)
        with self.assertRaises(ValidationError):
            AssetRecord(asset_id="a1", local_path="", file_sha256=sha256_mock)
        with self.assertRaises(ValidationError):
            AssetRecord(asset_id="a1", local_path="p", file_sha256="")

    def test_10_evaluation_report_boundaries(self):
        """Stress-test EvaluationReport layer types, score ranges, and passed flag."""
        # 1. Composite score boundaries [0.0, 1.0]
        rep_0 = EvaluationReport(run_id="run1", layer=EvaluationLayer.RESEARCH, composite_score=0.0)
        rep_1 = EvaluationReport(run_id="run1", layer=EvaluationLayer.VIDEO, composite_score=1.0)
        self.assertEqual(rep_0.composite_score, 0.0)
        self.assertEqual(rep_1.composite_score, 1.0)

        with self.assertRaises(ValidationError):
            EvaluationReport(run_id="run1", layer=EvaluationLayer.RESEARCH, composite_score=-0.01)
        with self.assertRaises(ValidationError):
            EvaluationReport(run_id="run1", layer=EvaluationLayer.RESEARCH, composite_score=1.01)
        with self.assertRaises(ValidationError):
            EvaluationReport(run_id="", layer=EvaluationLayer.SCRIPT)

        # 2. Layer string vs Enum equivalence
        rep_str = EvaluationReport(run_id="run1", layer="layer_1_research")
        self.assertEqual(rep_str.layer, "layer_1_research")

    def test_10_evaluation_report_yaml_enum_support(self):
        """Verify EvaluationReport with EvaluationLayer enum serializes to YAML cleanly."""
        report = EvaluationReport(
            run_id="run_eval_01",
            layer=EvaluationLayer.RESEARCH,
            composite_score=0.95,
        )
        # JSON dump works
        self.assertIsInstance(report.to_json(), str)

        # YAML dump works without representer error
        y = report.to_yaml()
        self.assertIn("layer: layer_1_research", y)
        restored = EvaluationReport.from_yaml(y)
        self.assertEqual(restored.layer, EvaluationLayer.RESEARCH)

    def test_11_render_artifact_and_publish_package_boundaries(self):
        """Stress-test RenderArtifact duration/filesize and PublishPackage."""
        # 1. RenderArtifact duration ge=0.0, file_size_bytes ge=0
        art = RenderArtifact(video_path="v.mp4", duration_seconds=0.0, file_size_bytes=0)
        self.assertEqual(art.duration_seconds, 0.0)

        with self.assertRaises(ValidationError):
            RenderArtifact(video_path="", duration_seconds=10.0)
        with self.assertRaises(ValidationError):
            RenderArtifact(video_path="v.mp4", duration_seconds=-0.1)
        with self.assertRaises(ValidationError):
            RenderArtifact(video_path="v.mp4", duration_seconds=10.0, file_size_bytes=-1)

        # 2. PublishPackage
        pub = PublishPackage(project_id="p1", title="Title", video_path="v.mp4")
        self.assertEqual(pub.project_id, "p1")
        with self.assertRaises(ValidationError):
            PublishPackage(project_id="", title="T", video_path="v.mp4")
        with self.assertRaises(ValidationError):
            PublishPackage(project_id="p1", title="", video_path="v.mp4")
        with self.assertRaises(ValidationError):
            PublishPackage(project_id="p1", title="T", video_path="")

    def test_12_analytics_and_learning_candidate_boundaries(self):
        """Stress-test AnalyticsSnapshot percentage/rates bounds and LearningCandidate."""
        # 1. AnalyticsSnapshot
        # views ge=0, average_watch_percentage [0.0, 100.0], ctr [0.0, 1.0], engagement_rate [0.0, 1.0]
        snap = AnalyticsSnapshot(
            project_id="p1",
            views=0,
            average_watch_percentage=100.0,
            ctr=1.0,
            engagement_rate=0.0,
        )
        self.assertEqual(snap.views, 0)
        self.assertEqual(snap.average_watch_percentage, 100.0)

        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", views=-1)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", average_watch_percentage=-0.1)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", average_watch_percentage=100.1)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", ctr=-0.01)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", ctr=1.01)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", engagement_rate=-0.01)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="p1", engagement_rate=1.01)
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="")

        # 2. LearningCandidate confidence [0.0, 1.0]
        lc = LearningCandidate(
            lesson_id="l1",
            creator_id="c1",
            observation="Obs",
            recommended_action="Act",
            confidence=0.0,
        )
        self.assertEqual(lc.confidence, 0.0)
        with self.assertRaises(ValidationError):
            LearningCandidate(lesson_id="", creator_id="c1", observation="O", recommended_action="A")
        with self.assertRaises(ValidationError):
            LearningCandidate(lesson_id="l1", creator_id="", observation="O", recommended_action="A")
        with self.assertRaises(ValidationError):
            LearningCandidate(lesson_id="l1", creator_id="c1", observation="", recommended_action="A")
        with self.assertRaises(ValidationError):
            LearningCandidate(lesson_id="l1", creator_id="c1", observation="O", recommended_action="")
        with self.assertRaises(ValidationError):
            LearningCandidate(lesson_id="l1", creator_id="c1", observation="O", recommended_action="A", confidence=-0.1)
        with self.assertRaises(ValidationError):
            LearningCandidate(lesson_id="l1", creator_id="c1", observation="O", recommended_action="A", confidence=1.1)

    # =======================================================================
    # SECTION 2: H9BaseModel Extensibility, Subscripting & Extra Fields
    # =======================================================================

    def test_13_h9_base_model_extra_fields_and_subscripting(self):
        """Test extra field preservation and dictionary subscripting on H9BaseModel."""
        brief = ContentBrief(
            project_id="proj_ext",
            topic="Deep Sea Exploration",
            custom_extra_attr="arbitrary_value",
            numeric_flag=42,
        )
        # Extra fields preserved
        self.assertEqual(brief.custom_extra_attr, "arbitrary_value")
        self.assertEqual(brief.numeric_flag, 42)

        # Dictionary access support
        self.assertEqual(brief["project_id"], "proj_ext")
        self.assertEqual(brief["custom_extra_attr"], "arbitrary_value")
        self.assertEqual(brief.get("numeric_flag"), 42)
        self.assertEqual(brief.get("nonexistent", "fallback"), "fallback")
        self.assertTrue("topic" in brief)
        self.assertTrue("custom_extra_attr" in brief)
        self.assertFalse("nonexistent" in brief)

        # Serialization preserves extra fields
        d = brief.to_dict()
        self.assertEqual(d["custom_extra_attr"], "arbitrary_value")
        self.assertEqual(d["numeric_flag"], 42)

        j = json.loads(brief.to_json())
        self.assertEqual(j["custom_extra_attr"], "arbitrary_value")

        y = yaml.safe_load(brief.to_yaml())
        self.assertEqual(y["custom_extra_attr"], "arbitrary_value")

    # =======================================================================
    # SECTION 3: Lossless Round-Trip Serialization Across All 17 Contracts
    # =======================================================================

    def test_14_lossless_round_trip_all_17_models(self):
        """Empirically verify lossless Dict, JSON, and YAML round-tripping for all 17 models."""
        source = SourceRecord(
            title="Quantum Teleportation Review",
            url="https://nature.com/articles/12345",
            publisher="Nature Publishing Group",
            author="Dr. Alice Smith",
            published_date="2026-01-15",
            reliability_score=0.97,
        )

        claim = ClaimRecord(
            claim_id="claim_qt_01",
            claim_text="Quantum entanglement enables deterministic state transfer across arbitrary distances.",
            category="quantum_physics",
            confidence_score=0.99,
            primary_source=source,
            corroborating_sources=[source],
            visual_cue_suggestion="Entangled photon pair split-screen schematic",
            verification_notes="Verified against peer-reviewed benchmark datasets.",
        )

        talking_point = TalkingPointRecord(
            beat_index=1,
            title="The Quantum Handshake",
            narrative_hook="How two particles share one destiny across the universe.",
            supported_claim_ids=["claim_qt_01"],
            estimated_duration_sec=7.5,
        )

        statistic = StatisticRecord(
            metric="Teleportation Fidelity",
            value="99.98%",
            context="Fiber-optic benchmark in metropolitan network",
            source_claim_id="claim_qt_01",
        )

        scorecard = EditorialScorecard(
            audience_relevance=0.92,
            novelty=0.88,
            hook_potential=0.95,
            narrative_potential=0.85,
            creator_fit=0.90,
            evidence_availability=0.95,
            visual_potential=0.90,
            platform_fit=0.93,
            saturation_risk=0.15,
        )

        angle = EditorialAngle(
            angle_id="angle_qt_01",
            title="The Ghost in the Fiber",
            premise="How quantum entanglement is secretly upgrading modern internet cables.",
            core_thesis="The quantum internet is already here—it just needs photons.",
            target_audience="Engineers and Science Enthusiasts",
            narrative_style="Documentary Mystery",
            key_hooks=["What if distance ceased to exist for data?"],
            scorecard=scorecard,
            selected=True,
            selection_rationale="Unbeatable hook potential and pristine evidence.",
        )

        act = OutlineAct(
            act_index=1,
            act_name="The Entanglement Puzzle",
            target_start_pct=0.0,
            target_end_pct=0.25,
            narrative_job="Introduce Einstein's spooky action at a distance",
            talking_point_indices=[1],
            visual_theme="split_screen_lab",
        )

        outline = ContentOutline(
            project_id="proj_qt_001",
            topic="Quantum Teleportation",
            angle_id="angle_qt_01",
            angle_title="The Ghost in the Fiber",
            primary_hook="Could data travel faster than light without breaking physics?",
            acts=[act],
            total_estimated_duration=45.0,
        )

        beat = ScriptBeat(
            beat_id="beat_qt_01",
            start_time=0.0,
            end_time=3.5,
            duration=3.5,
            text="In 1935, Einstein called it spooky. Today, we call it the quantum internet.",
            visual_cue="Animated photon stream",
            tone_modifier="intrigued",
            emphasis_words=["spooky", "quantum internet"],
        )

        scene = ScriptScene(
            scene_id="scene_qt_01",
            title="Hook Scene",
            start_time=0.0,
            duration=5.0,
            narration_text="In 1935, Einstein called it spooky. Today, we call it the quantum internet.",
            visual_asset_path="renders/assets/photon_beam.svg",
            hero_frame_description="Photon beam splitting at prism",
            component_type="split_screen_intro",
            component_props={"left_label": "Einstein 1935", "right_label": "Quantum Lab 2026"},
            entrance_animation="zoom_in",
            transition_out="dissolve",
            beats=[beat],
        )

        script = Script(
            topic="Quantum Teleportation",
            title="The Quantum Leap",
            angle_id="angle_qt_01",
            total_duration=30.0,
            full_transcript="In 1935, Einstein called it spooky...",
            word_count=12,
            scenes=[scene],
        )

        asset_req = AssetRequirement(
            requirement_id="req_qt_01",
            scene_id="scene_qt_01",
            visual_query="Quantum entanglement photon splitter schematic",
            media_type="image/svg+xml",
            aspect_ratio="16:9",
            style_notes="Dark aesthetic with cyan glow accents",
            associated_claim_id="claim_qt_01",
        )

        dimensions = Dimensions(width=1920, height=1080, aspect_ratio="16:9")
        license_info = LicenseInfo(
            license_type="CC-BY-4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            attribution_text="Source: CERN Open Science",
            attribution_required=True,
            commercial_use_allowed=True,
            modification_allowed=True,
        )

        asset_record = AssetRecord(
            asset_id="asset_qt_01",
            local_path="assets/quantum_prism.svg",
            absolute_path="/opt/harness9/assets/quantum_prism.svg",
            file_size_bytes=48120,
            file_sha256="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
            perceptual_hash="1010101010101010",
            media_type="image/svg+xml",
            dimensions=dimensions,
            source_provider="harness9_procedural",
            source_url="https://cern.ch/data/prism.svg",
            page_url="https://cern.ch/data",
            creator_name="Dr. CERN",
            license=license_info,
            verification_status="VERIFIED",
            scene_target="scene_qt_01",
            claim_id_refs=["claim_qt_01"],
        )

        # Test Enum layer round trip
        eval_report = EvaluationReport(
            run_id="run_qt_001",
            layer=EvaluationLayer.RESEARCH,
            scores={"fact_density": 0.98, "citation_validity": 1.0},
            composite_score=0.99,
            passed=True,
            feedback=["Outstanding primary source backing."],
        )

        render_artifact = RenderArtifact(
            video_path="output/renders/quantum_teleportation.mp4",
            duration_seconds=30.0,
            file_size_bytes=15728640,
            width=1920,
            height=1080,
            fps=60,
            video_codec="h264",
            audio_codec="aac",
            validation_status="VERIFIED",
        )

        publish_package = PublishPackage(
            project_id="proj_qt_001",
            title="The Quantum Teleportation Breakthrough",
            description="Autonomous video production deep dive into quantum networks.",
            tags=["quantum", "physics", "technology", "documentary"],
            video_path="output/renders/quantum_teleportation.mp4",
            thumbnail_path="output/renders/thumb_qt.jpg",
            captions_vtt_path="output/renders/captions_qt.vtt",
            total_cost_usd=0.035,
        )

        analytics = AnalyticsSnapshot(
            project_id="proj_qt_001",
            views=45200,
            average_watch_percentage=84.2,
            ctr=0.092,
            engagement_rate=0.145,
        )

        learning = LearningCandidate(
            lesson_id="lesson_qt_01",
            creator_id="tech_explorer",
            rule_type="positive_pattern",
            observation="Viewer engagement spiked 24% during photon splitting animation.",
            recommended_action="Use high-contrast dynamic schematics during technical explainers.",
            confidence=0.96,
        )

        profile = CreatorProfile(
            creator_id="tech_explorer",
            display_name="Tech Explorer Alpha",
            tone_of_voice=["visionary", "analytical"],
            target_audiences=["physicists", "software engineers"],
            brand_colors={"primary": "#00f0ff", "background": "#050811"},
            default_format="16:9",
            negative_rules=["Avoid clickbait hyperbole"],
            voice_preference="en_us_male_deep",
        )

        brief = ContentBrief(
            project_id="proj_qt_001",
            topic="Quantum Teleportation Explained",
            target_duration_seconds=30,
            aspect_ratio="16:9",
            goal="Comprehensive technical documentary",
            audience="Engineers",
            offline_mode=True,
            creator_id="tech_explorer",
        )

        plan = ResearchPlan(
            topic="Quantum Teleportation",
            target_claim_count=5,
            search_queries=[("physics", "quantum teleportation fiber distance records")],
        )

        dossier = ResearchDossier(
            topic="Quantum Teleportation",
            run_id="run_qt_001",
            headline="Teleportation at Scale",
            executive_summary="State-of-the-art overview of quantum networks.",
            claims=[claim],
            talking_points=[talking_point],
            statistics=[statistic],
            suggested_visual_queries=["Quantum optics table setup"],
        )

        # Collect all 17 models
        all_models = [
            profile,
            brief,
            plan,
            dossier,
            source,
            claim,
            angle,
            outline,
            script,
            beat,
            asset_req,
            asset_record,
            eval_report,
            render_artifact,
            publish_package,
            analytics,
            learning,
        ]

        self.assertEqual(len(all_models), 17, "Must test exactly 17 distinct production models")

        for idx, model in enumerate(all_models, start=1):
            cls = type(model)
            model_name = cls.__name__

            # 1. Dict Round-Trip
            d = model.to_dict()
            self.assertIsInstance(d, dict, f"[{model_name}] to_dict() must return a dict")
            from_d = cls.from_dict(d)
            self.assertEqual(model.to_dict(), from_d.to_dict(), f"[{model_name}] Dict round-trip failed")

            # 2. JSON Round-Trip
            j_str = model.to_json(indent=2)
            self.assertIsInstance(j_str, str, f"[{model_name}] to_json() must return a str")
            from_j = cls.from_json(j_str)
            self.assertEqual(model.to_dict(), from_j.to_dict(), f"[{model_name}] JSON round-trip failed")

            # 3. YAML Round-Trip
            y_str = model.to_yaml()
            self.assertIsInstance(y_str, str, f"[{model_name}] to_yaml() must return a str")
            from_y = cls.from_yaml(y_str)
            self.assertEqual(model.to_dict(), from_y.to_dict(), f"[{model_name}] YAML round-trip failed")

            # 4. Atomic Save and Load (JSON + YAML)
            json_p, yaml_p = model.save(self.tmp_path, f"test_model_{idx}")
            self.assertTrue(json_p.exists(), f"[{model_name}] JSON file not created")
            self.assertTrue(yaml_p.exists(), f"[{model_name}] YAML file not created")

            loaded_from_json = cls.load(json_p)
            self.assertEqual(model.to_dict(), loaded_from_json.to_dict(), f"[{model_name}] Load from JSON failed")

            loaded_from_yaml = cls.load(yaml_p)
            self.assertEqual(model.to_dict(), loaded_from_yaml.to_dict(), f"[{model_name}] Load from YAML failed")

    # =======================================================================
    # SECTION 4: File I/O Error Handling & Malformed Files
    # =======================================================================

    def test_15_file_io_error_handling(self):
        """Test H9BaseModel error handling for nonexistent files, malformed JSON, and invalid YAML."""
        # 1. Nonexistent file
        with self.assertRaises(FileNotFoundError):
            ContentBrief.load(self.tmp_path / "does_not_exist.json")

        # 2. Malformed JSON
        bad_json_file = self.tmp_path / "bad.json"
        bad_json_file.write_text("{ unclosed json: ", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            ContentBrief.load(bad_json_file)

        # 3. Malformed YAML (valid YAML but not a dictionary, e.g. a list)
        bad_yaml_file = self.tmp_path / "bad.yaml"
        bad_yaml_file.write_text("- item 1\n- item 2\n", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            ContentBrief.load(bad_yaml_file)
        self.assertIn("YAML root must be a dictionary object", str(ctx.exception))

    # =======================================================================
    # SECTION 5: Backward Compatibility & Module Exports
    # =======================================================================

    def test_16_backward_compatibility_module_exports(self):
        """Verify that src.models re-exports all legacy models and all 17 new contracts."""
        # 1. Check all 17 new contracts in __all__
        new_contracts = [
            "CreatorProfile",
            "ContentBrief",
            "ResearchPlan",
            "ResearchDossier",
            "SourceRecord",
            "ClaimRecord",
            "TalkingPointRecord",
            "StatisticRecord",
            "EditorialAngle",
            "EditorialScorecard",
            "AngleScorecard",
            "ContentOutline",
            "OutlineAct",
            "Script",
            "ScriptBeat",
            "ScriptScene",
            "AssetRequirement",
            "AssetRecord",
            "Dimensions",
            "LicenseInfo",
            "EvaluationReport",
            "EvaluationLayer",
            "RenderArtifact",
            "PublishPackage",
            "AnalyticsSnapshot",
            "LearningCandidate",
            "H9BaseModel",
        ]
        for name in new_contracts:
            self.assertTrue(hasattr(models_pkg, name), f"src.models missing export: {name}")
            self.assertIn(name, models_pkg.__all__, f"src.models.__all__ missing: {name}")

        # 2. Check legacy models in __all__
        legacy_exports = [
            "Claim",
            "Source",
            "TalkingPoint",
            "Statistic",
            "Summary",
            "DossierMetadata",
            "LegacyResearchDossier",
            "AssetProvenanceLedger",
            "MediaAsset",
            "CreatorInfo",
            "LegacyLicenseInfo",
            "LegacyDimensions",
            "Storyboard",
            "Scene",
            "Beat",
            "LegacyScript",
            "PipelineSummary",
            "StageResult",
        ]
        for name in legacy_exports:
            self.assertTrue(hasattr(models_pkg, name), f"src.models missing legacy export: {name}")
            self.assertIn(name, models_pkg.__all__, f"src.models.__all__ missing: {name}")

        # 3. Instantiate legacy models to ensure zero regression
        legacy_claim = models_pkg.Claim(
            claim_id="legacy_c1",
            claim_text="Legacy claim text",
            category="history",
            confidence_score=0.9,
            primary_source=models_pkg.Source(title="Legacy Source", url="https://example.com"),
        )
        self.assertEqual(legacy_claim.claim_id, "legacy_c1")

        legacy_sb = models_pkg.Storyboard(project_id="legacy_proj", target_duration=30.0)
        legacy_script = models_pkg.LegacyScript(
            topic="Legacy Topic",
            title="Legacy Title",
            total_duration=30.0,
            storyboard=legacy_sb,
        )
        self.assertEqual(legacy_script.topic, "Legacy Topic")

        legacy_beat = models_pkg.Beat(beat_id="b1", start_time=0.0, end_time=3.0, duration=3.0, text="Legacy beat")
        self.assertEqual(legacy_beat.duration, 3.0)


if __name__ == "__main__":
    unittest.main()
