"""Unit tests for Harness 9 Pydantic v2 Production Contracts (Milestone M1)."""

import json
from pathlib import Path
import tempfile
import unittest
from pydantic import ValidationError

from src.models.contracts import (
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


class TestProductionContracts(unittest.TestCase):
    """Test suite verifying validation, serialization, and constraints for all 17 Pydantic v2 schemas."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -----------------------------------------------------------------------
    # 1. CreatorProfile
    # -----------------------------------------------------------------------
    def test_01_creator_profile_schema(self):
        """Verify CreatorProfile validation, defaults, and format constraints."""
        profile = CreatorProfile(
            creator_id="tech_explorer",
            display_name="Tech Explorer",
        )
        self.assertEqual(profile.creator_id, "tech_explorer")
        self.assertEqual(profile.display_name, "Tech Explorer")
        self.assertIn("authoritative", profile.tone_of_voice)
        self.assertEqual(profile.default_format, "16:9")
        self.assertGreaterEqual(len(profile.negative_rules), 1)

        # Invalid format pattern
        with self.assertRaises(ValidationError):
            CreatorProfile(
                creator_id="bad",
                display_name="Bad",
                default_format="invalid_ratio",
            )

    # -----------------------------------------------------------------------
    # 2. ContentBrief
    # -----------------------------------------------------------------------
    def test_02_content_brief_schema(self):
        """Verify ContentBrief validation, duration bounds, and serialization."""
        brief = ContentBrief(
            project_id="proj_001",
            topic="How Superconductors Work",
            target_duration_seconds=45,
            aspect_ratio="9:16",
        )
        self.assertEqual(brief.project_id, "proj_001")
        self.assertEqual(brief.target_duration_seconds, 45)
        self.assertEqual(brief.aspect_ratio, "9:16")

        # Invalid duration bounds (duration < 5 or > 600)
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p1", topic="Test", target_duration_seconds=2)
        with self.assertRaises(ValidationError):
            ContentBrief(project_id="p2", topic="Test", target_duration_seconds=1000)

        # Serialization to JSON and YAML
        json_path, yaml_path = brief.save(self.out_path, "brief")
        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        loaded = ContentBrief.load(json_path)
        self.assertEqual(loaded.topic, "How Superconductors Work")

    # -----------------------------------------------------------------------
    # 3. ResearchPlan
    # -----------------------------------------------------------------------
    def test_03_research_plan_schema(self):
        """Verify ResearchPlan search queries and target claim bounds."""
        plan = ResearchPlan(
            topic="Quantum Cryptography",
            target_claim_count=6,
            search_queries=[
                ("origin_history", "Quantum key distribution early history"),
                ("technical_mechanism", "BB84 protocol mechanics"),
            ],
            timeout_seconds=20.0,
        )
        self.assertEqual(plan.target_claim_count, 6)
        self.assertEqual(len(plan.search_queries), 2)
        self.assertEqual(len(plan.intent_categories), 4)

    # -----------------------------------------------------------------------
    # 4. SourceRecord & ClaimRecord
    # -----------------------------------------------------------------------
    def test_04_source_and_claim_records(self):
        """Verify SourceRecord reliability scores and ClaimRecord structure."""
        source = SourceRecord(
            title="Bell Labs Physical Review",
            url="https://example.org/transistor",
            reliability_score=0.95,
        )
        self.assertEqual(source.reliability_score, 0.95)

        # Invalid reliability score > 1.0
        with self.assertRaises(ValidationError):
            SourceRecord(title="Bad", url="https://bad.org", reliability_score=1.5)

        claim = ClaimRecord(
            claim_id="claim_01",
            claim_text="The first point-contact transistor was demonstrated on December 23, 1947.",
            category="origin_history",
            confidence_score=0.98,
            primary_source=source,
            corroborating_sources=[source],
            visual_cue_suggestion="Point-contact replica photo",
        )
        self.assertEqual(claim.claim_id, "claim_01")
        self.assertEqual(claim.primary_source.title, "Bell Labs Physical Review")
        self.assertEqual(len(claim.corroborating_sources), 1)

    # -----------------------------------------------------------------------
    # 5. ResearchDossier
    # -----------------------------------------------------------------------
    def test_05_research_dossier_contract(self):
        """Verify ResearchDossier schema versioning, talking points, and saving/loading."""
        source = SourceRecord(title="Source 1", url="https://example.com/1")
        claim = ClaimRecord(
            claim_id="claim_01",
            claim_text="Test claim with sufficient character length.",
            confidence_score=0.9,
            primary_source=source,
        )
        dossier = ResearchDossier(
            topic="Apollo Guidance Computer",
            run_id="run_apollo_01",
            headline="How Apollo Made It to the Moon with 4KB of RAM",
            executive_summary="The AGC was a seminal leap in real-time embedded computing.",
            claims=[claim],
            talking_points=[
                TalkingPointRecord(
                    beat_index=1,
                    title="The Core Memory",
                    narrative_hook="Hand-woven rope memory powered the moon landing.",
                    supported_claim_ids=["claim_01"],
                    estimated_duration_sec=8.0,
                )
            ],
            statistics=[
                StatisticRecord(
                    metric="ROM Capacity",
                    value="36,864 words",
                    context="Rope core ROM storage",
                    source_claim_id="claim_01",
                )
            ],
            suggested_visual_queries=["Apollo DSKY interface", "Rope core memory weaving"],
        )
        self.assertEqual(dossier.schema_version, "2.0.0")
        self.assertEqual(len(dossier.claims), 1)
        self.assertEqual(len(dossier.talking_points), 1)
        self.assertEqual(len(dossier.statistics), 1)

        # Save and reload
        json_p, yaml_p = dossier.save(self.out_path, "test_dossier")
        loaded_dossier = ResearchDossier.load(yaml_p)
        self.assertEqual(loaded_dossier.topic, "Apollo Guidance Computer")
        self.assertEqual(loaded_dossier.talking_points[0].title, "The Core Memory")

    # -----------------------------------------------------------------------
    # 6. EditorialScorecard & EditorialAngle
    # -----------------------------------------------------------------------
    def test_06_editorial_scorecard_and_angle(self):
        """Verify 9-dimension scorecard calculation and EditorialAngle structure."""
        scorecard = EditorialScorecard(
            audience_relevance=0.9,
            novelty=0.85,
            hook_potential=0.95,
            narrative_potential=0.8,
            creator_fit=0.85,
            evidence_availability=0.9,
            visual_potential=0.8,
            platform_fit=0.9,
            saturation_risk=0.1,
        )
        self.assertGreater(scorecard.composite_score, 0.8)
        self.assertLessEqual(scorecard.composite_score, 1.0)

        # Boundary score tests: all 0.0 with saturation_risk=1.0 -> composite_score == 0.0
        zero_card = EditorialScorecard(
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
        self.assertEqual(zero_card.composite_score, 0.0)

        # Boundary score tests: all 1.0 with saturation_risk=0.0 -> composite_score == 1.0
        max_card = EditorialScorecard(
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
        self.assertEqual(max_card.composite_score, 1.0)

        angle = EditorialAngle(
            angle_id="angle_01",
            title="The Forgotten Women Who Wove the Moon Landing",
            premise="Focuses on the rope core memory workers known as 'Little Old Ladies'.",
            core_thesis="Human precision made the Apollo guidance computer possible.",
            scorecard=scorecard,
            selected=True,
            selection_rationale="Highest composite score and exceptional novelty.",
        )
        self.assertEqual(angle.angle_id, "angle_01")
        self.assertTrue(angle.selected)
        self.assertEqual(angle.scorecard.composite_score, scorecard.composite_score)

        # Verify alias AngleScorecard works identically
        alias_card = AngleScorecard(audience_relevance=0.7)
        self.assertIsInstance(alias_card, EditorialScorecard)

    # -----------------------------------------------------------------------
    # 7. ContentOutline & OutlineAct
    # -----------------------------------------------------------------------
    def test_07_content_outline_contract(self):
        """Verify 4-act ContentOutline structure."""
        acts = [
            OutlineAct(
                act_index=1,
                act_name="The Hand-Woven Miracle",
                target_start_pct=0.0,
                target_end_pct=0.25,
                narrative_job="Establish stakes and introduce rope memory",
                talking_point_indices=[1],
            ),
            OutlineAct(
                act_index=2,
                act_name="The Memory Bottleneck",
                target_start_pct=0.25,
                target_end_pct=0.50,
                narrative_job="Explain the 4KB limit",
                talking_point_indices=[2],
            ),
        ]
        outline = ContentOutline(
            project_id="proj_agc_01",
            topic="Apollo Guidance Computer",
            angle_id="angle_01",
            angle_title="The Rope Memory Miracle",
            primary_hook="How do you fly to the moon with less memory than a single emoji?",
            acts=acts,
            total_estimated_duration=30.0,
        )
        self.assertEqual(len(outline.acts), 2)
        self.assertEqual(outline.primary_hook.startswith("How do you fly"), True)

    # -----------------------------------------------------------------------
    # 8. ScriptBeat, ScriptScene & Script
    # -----------------------------------------------------------------------
    def test_08_script_beats_and_scenes(self):
        """Verify Script, ScriptScene, and ScriptBeat schemas."""
        beats = [
            ScriptBeat(
                beat_id="beat_01",
                start_time=0.0,
                end_time=3.2,
                duration=3.2,
                text="In 1969, navigating to the moon required a computer.",
                visual_cue="Saturn V rocket launch",
                emphasis_words=["navigating", "moon"],
            )
        ]
        scene = ScriptScene(
            scene_id="scene_01",
            title="Introduction",
            start_time=0.0,
            duration=5.0,
            narration_text="In 1969, navigating to the moon required a computer.",
            component_type="reference_collage_hook",
            component_props={"headline": "Moon Mission Computer", "glow_color": "#00d2ff"},
            beats=beats,
        )
        script = Script(
            topic="Apollo Guidance Computer",
            title="The AGC Story",
            angle_id="angle_01",
            total_duration=30.0,
            full_transcript="In 1969, navigating to the moon required a computer.",
            word_count=9,
            scenes=[scene],
        )
        self.assertEqual(len(script.scenes), 1)
        self.assertEqual(script.scenes[0].beats[0].emphasis_words, ["navigating", "moon"])

    # -----------------------------------------------------------------------
    # 9. AssetRequirement & AssetRecord
    # -----------------------------------------------------------------------
    def test_09_asset_requirement_and_record(self):
        """Verify AssetRequirement and AssetRecord with SHA-256 and dimensions."""
        req = AssetRequirement(
            requirement_id="req_01",
            scene_id="scene_01",
            visual_query="Apollo DSKY display unit",
            media_type="image/svg+xml",
        )
        self.assertEqual(req.aspect_ratio, "16:9")

        record = AssetRecord(
            asset_id="asset_01",
            local_path="assets/images/dsky.svg",
            file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            dimensions=Dimensions(width=1920, height=1080, aspect_ratio="16:9"),
            license=LicenseInfo(
                license_type="CC0-1.0",
                commercial_use_allowed=True,
            ),
            scene_target="scene_01",
        )
        self.assertEqual(record.dimensions.width, 1920)
        self.assertTrue(record.license.commercial_use_allowed)

    # -----------------------------------------------------------------------
    # 10. EvaluationReport
    # -----------------------------------------------------------------------
    def test_10_evaluation_report(self):
        """Verify EvaluationReport across 4 layers and ensure YAML/JSON round-trip with Enum instances."""
        report = EvaluationReport(
            run_id="run_eval_01",
            layer=EvaluationLayer.RESEARCH,
            scores={"fact_density": 0.95, "source_diversity": 0.9},
            composite_score=0.92,
            passed=True,
            feedback=["Strong citation coverage."],
        )
        self.assertEqual(report.layer, EvaluationLayer.RESEARCH)
        self.assertTrue(report.passed)

        # YAML serialization must succeed without RepresenterError
        yaml_str = report.to_yaml()
        self.assertIn("layer: layer_1_research", yaml_str)
        restored = EvaluationReport.from_yaml(yaml_str)
        self.assertEqual(restored.layer, EvaluationLayer.RESEARCH)
        self.assertEqual(restored.composite_score, 0.92)

        # JSON round-trip
        json_str = report.to_json()
        restored_json = EvaluationReport.from_json(json_str)
        self.assertEqual(restored_json.layer, EvaluationLayer.RESEARCH)

    # -----------------------------------------------------------------------
    # 11. RenderArtifact & PublishPackage
    # -----------------------------------------------------------------------
    def test_11_render_artifact_and_publish_package(self):
        """Verify RenderArtifact and PublishPackage metadata."""
        artifact = RenderArtifact(
            video_path="renders/final.mp4",
            duration_seconds=30.0,
            file_size_bytes=10485760,
            width=1920,
            height=1080,
            fps=30,
        )
        self.assertEqual(artifact.video_codec, "h264")

        package = PublishPackage(
            project_id="proj_01",
            title="The AGC Story",
            description="Autonomous video production",
            tags=["tech", "history", "space"],
            video_path=artifact.video_path,
            total_cost_usd=0.04,
        )
        self.assertEqual(len(package.tags), 3)
        self.assertEqual(package.total_cost_usd, 0.04)

    # -----------------------------------------------------------------------
    # 12. AnalyticsSnapshot & LearningCandidate
    # -----------------------------------------------------------------------
    def test_12_analytics_and_learning_candidate(self):
        """Verify AnalyticsSnapshot and LearningCandidate models."""
        snapshot = AnalyticsSnapshot(
            project_id="proj_01",
            views=15000,
            average_watch_percentage=78.5,
            ctr=0.085,
            engagement_rate=0.12,
        )
        self.assertEqual(snapshot.views, 15000)

        # Invalid watch percentage > 100
        with self.assertRaises(ValidationError):
            AnalyticsSnapshot(project_id="bad", average_watch_percentage=120.0)

        learning = LearningCandidate(
            lesson_id="lesson_001",
            creator_id="tech_explorer",
            rule_type="negative_constraint",
            observation="Viewer dropoff increased when scenes exceeded 7 seconds.",
            recommended_action="Keep max scene duration below 6.5 seconds.",
            confidence=0.92,
        )
        self.assertEqual(learning.rule_type, "negative_constraint")
        self.assertEqual(learning.confidence, 0.92)


if __name__ == "__main__":
    unittest.main()
