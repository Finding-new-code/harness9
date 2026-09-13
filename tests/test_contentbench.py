"""Unit & Integration Tests for ContentBench 4-Layer Quality OS (Milestone M5).

Tests:
1. Layer 1 (S_research) fact density, source authority, corroboration, and conflict penalties.
2. Layer 2 (S_script) hook curiosity gap, cadence variance, readability, and Creator DNA adherence.
3. Layer 3 (S_video) VoiceQA acoustics, speech-beat sync drift, visual relevance, and missing-layer penalty.
4. Layer 4 (S_cost) budget compliance, token efficiency, and compute efficiency.
5. Composite 4-layer formulation weighting (0.25, 0.30, 0.30, 0.15) and report generation.
6. Benchmark test suite runner and Markdown / JSON report serialization.
"""

import shutil
import tempfile
import unittest

from src.creator.dna import CreatorDNA
from src.creator.economics import CostCategory, CostItem, ProductionCostLedger, UnitType
from src.evaluation.contentbench import (
    ContentBench,
    ContentBenchReport,
    EconomicsQualityMetrics,
    LayerEvaluationResult,
    ResearchQualityMetrics,
    ScriptQualityMetrics,
    VideoQualityMetrics,
)
from src.models.contracts import (
    ClaimRecord,
    ContentBrief,
    EvaluationLayer,
    EvaluationReport,
    RenderArtifact,
    ResearchDossier,
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
)


class TestContentBench(unittest.TestCase):
    """Test suite verifying ContentBench 4-Layer Quality OS."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.evaluator = ContentBench(passing_threshold=0.75)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 1. Layer 1: Research Quality Tests
    # -----------------------------------------------------------------------
    def test_layer_1_research_high_quality(self):
        claims = [
            ClaimRecord(
                claim_id="c1",
                claim_text="The point-contact transistor was invented at Bell Labs in December 1947.",
                confidence_score=0.95,
                primary_source=SourceRecord(
                    title="IEEE History",
                    url="https://ieee.org/history/transistor",
                    reliability_score=0.95,
                ),
                corroborating_sources=[
                    SourceRecord(
                        title="Nobel Prize Archives",
                        url="https://nobelprize.org/physics/1956",
                        reliability_score=0.98,
                    )
                ],
            ),
            ClaimRecord(
                claim_id="c2",
                claim_text="Shockley, Bardeen, and Brattain shared the 1956 Nobel Prize in Physics.",
                confidence_score=0.95,
                primary_source=SourceRecord(
                    title="Nobel Citation",
                    url="https://nobelprize.org/physics/1956",
                    reliability_score=0.98,
                ),
            ),
            ClaimRecord(
                claim_id="c3",
                claim_text="Silicon replaced germanium due to its wider bandgap and native oxide layer.",
                confidence_score=0.90,
                primary_source=SourceRecord(
                    title="MIT OpenCourseWare",
                    url="https://ocw.mit.edu/semiconductors",
                    reliability_score=0.95,
                ),
                corroborating_sources=[
                    SourceRecord(
                        title="Stanford Solid State",
                        url="https://stanford.edu/solidstate",
                        reliability_score=0.92,
                    )
                ],
            ),
        ]
        dossier = ResearchDossier(topic="The Invention of the Transistor", claims=claims)
        brief = ContentBrief(project_id="test_m5_res", topic="The Invention of the Transistor", target_duration_seconds=30)

        result = self.evaluator.evaluate_research(dossier=dossier, brief=brief)

        self.assertIsInstance(result, LayerEvaluationResult)
        self.assertEqual(result.layer, EvaluationLayer.RESEARCH)
        self.assertTrue(result.passed)
        self.assertGreaterEqual(result.composite_score, 0.80)
        self.assertEqual(result.scores["fact_density"], 1.0)
        self.assertGreater(result.scores["source_authority"], 0.90)

    def test_layer_1_research_conflict_penalty(self):
        claims = [
            ClaimRecord(
                claim_id="c1",
                claim_text="Unverified claim about alien technology.",
                confidence_score=0.3,
                primary_source=SourceRecord(title="Blog", url="http://randomblog.com/post", reliability_score=0.3),
                verification_notes="Uncorroborated conflict detected in literature",
            )
        ]
        dossier = ResearchDossier(topic="Aliens", claims=claims)
        brief = ContentBrief(project_id="test_pen", topic="Aliens", target_duration_seconds=30)

        result = self.evaluator.evaluate_research(dossier=dossier, brief=brief)
        self.assertLess(result.composite_score, 0.60)
        self.assertFalse(result.passed)
        self.assertGreater(result.scores["conflict_penalty"], 0.0)

    # -----------------------------------------------------------------------
    # 2. Layer 2: Script & Narrative Quality Tests
    # -----------------------------------------------------------------------
    def test_layer_2_script_evaluation_optimal(self):
        script = Script(
            topic="Transistors",
            title="The 1947 Miracle",
            total_duration=30.0,
            full_transcript=(
                "In 1947, three physicists at Bell Labs built a fragile sliver of germanium that changed "
                "civilization forever. Without this breakthrough, modern microprocessors, the internet, and "
                "global satellite navigation could never function. Today, billions of microscopic switches "
                "power every digital screen on Earth. Here is the remarkable engineering story of the transistor."
            ),
            scenes=[
                ScriptScene(
                    scene_id="s1",
                    title="Hook",
                    duration=10.0,
                    narration_text="In 1947, three physicists at Bell Labs built a fragile sliver of germanium that changed civilization forever.",
                ),
                ScriptScene(
                    scene_id="s2",
                    title="Impact",
                    duration=10.0,
                    narration_text="Without this breakthrough, modern microprocessors, the internet, and global satellite navigation could never function.",
                ),
                ScriptScene(
                    scene_id="s3",
                    title="Conclusion",
                    duration=10.0,
                    narration_text="Today, billions of microscopic switches power every digital screen on Earth. Here is the remarkable engineering story of the transistor.",
                ),
            ],
        )
        brief = ContentBrief(project_id="test_scr", topic="Transistors", target_duration_seconds=30)
        dna = CreatorDNA(creator_id="harness9_creator")

        result = self.evaluator.evaluate_script(script=script, brief=brief, creator_dna=dna)

        self.assertIsInstance(result, LayerEvaluationResult)
        self.assertEqual(result.layer, EvaluationLayer.SCRIPT)
        self.assertTrue(result.passed)
        self.assertGreaterEqual(result.composite_score, 0.80)
        self.assertGreaterEqual(result.scores["hook_strength"], 0.80)
        self.assertEqual(result.scores["dna_adherence"], 1.0)

    def test_layer_2_script_lazy_opener_and_buzzword_penalties(self):
        script = Script(
            topic="Bad Script",
            title="Lazy Hook",
            total_duration=30.0,
            full_transcript="In this video we will explore a revolutionary game-changer technology.",
            scenes=[
                ScriptScene(
                    scene_id="s1",
                    duration=30.0,
                    narration_text="In this video we will explore a revolutionary game-changer technology.",
                )
            ],
        )
        dna = CreatorDNA(creator_id="strict_creator")
        dna.brand_constitution.prohibited_words = ["game-changer", "revolutionary"]

        result = self.evaluator.evaluate_script(script=script, creator_dna=dna)
        self.assertLess(result.composite_score, 0.65)
        self.assertLess(result.scores["hook_strength"], 0.60)
        self.assertLess(result.scores["dna_adherence"], 0.80)

    # -----------------------------------------------------------------------
    # 3. Layer 3: Video & Composition Quality Tests
    # -----------------------------------------------------------------------
    def test_layer_3_video_evaluation_clean_acoustics(self):
        video = RenderArtifact(
            video_path="renders/final.mp4",
            duration_seconds=30.0,
            file_size_bytes=5_000_000,
            validation_status="VERIFIED",
        )
        voice_qa = {
            "passed": True,
            "clipping_ratio": 0.0,
            "max_dead_air_duration_sec": 0.12,
            "loudness_variance_db": 1.4,
            "speech_beat_max_drift_sec": 0.04,
        }
        script = Script(
            topic="Test",
            title="Test",
            scenes=[
                ScriptScene(
                    scene_id="s1",
                    duration=15.0,
                    visual_asset_path="assets/images/img1.png",
                    hero_frame_description="Historical Bell Labs lab",
                ),
                ScriptScene(
                    scene_id="s2",
                    duration=15.0,
                    visual_asset_path="assets/images/img2.png",
                    hero_frame_description="Modern microprocessor die",
                ),
            ],
        )

        result = self.evaluator.evaluate_video(video=video, voice_qa_data=voice_qa, script=script)

        self.assertEqual(result.layer, EvaluationLayer.VIDEO)
        self.assertTrue(result.passed)
        self.assertGreaterEqual(result.composite_score, 0.85)
        self.assertGreater(result.scores["voice_qa_score"], 0.90)
        self.assertEqual(result.scores["visual_relevance"], 1.0)

    def test_layer_3_video_missing_layer_penalty(self):
        """Boundary test: Missing video layer produces zero composite score."""
        result = self.evaluator.evaluate_video(video=None, voice_qa_data=None)
        self.assertEqual(result.composite_score, 0.0)
        self.assertFalse(result.passed)
        self.assertIn("missing", result.feedback[0].lower())

    # -----------------------------------------------------------------------
    # 4. Layer 4: Cost & Resource Efficiency Tests
    # -----------------------------------------------------------------------
    def test_layer_4_economics_within_budget(self):
        ledger = ProductionCostLedger(
            run_id="run_cost_01",
            items=[
                CostItem(
                    category=CostCategory.LLM.value,
                    item_name="LLM Total",
                    units_consumed=15000,
                    unit_type=UnitType.TOKENS.value,
                    unit_rate_usd=0.000005,
                    total_cost_usd=0.075,
                ),
                CostItem(
                    category=CostCategory.TTS.value,
                    item_name="TTS Total",
                    units_consumed=1200,
                    unit_type=UnitType.CHARACTERS.value,
                    unit_rate_usd=0.00003,
                    total_cost_usd=0.036,
                ),
            ],
            video_duration_seconds=30.0,
        )

        result = self.evaluator.evaluate_economics(ledger=ledger, duration_seconds=30.0)

        self.assertEqual(result.layer, EvaluationLayer.COST)
        self.assertTrue(result.passed)
        self.assertGreaterEqual(result.composite_score, 0.85)
        self.assertEqual(result.scores["budget_score"], 1.0)

    # -----------------------------------------------------------------------
    # 5. Composite ContentBench Evaluation & Report Tests
    # -----------------------------------------------------------------------
    def test_contentbench_full_production_evaluation(self):
        brief = ContentBrief(
            project_id="proj_full_bench",
            topic="Apollo Guidance Computer",
            target_duration_seconds=30,
        )
        claims = [
            ClaimRecord(
                claim_id="c1",
                claim_text="The AGC was one of the first computers to use integrated circuits.",
                confidence_score=0.95,
                primary_source=SourceRecord(title="NASA History", url="https://nasa.gov/history/agc", reliability_score=0.98),
                corroborating_sources=[SourceRecord(title="MIT Instrumentation", url="https://mit.edu/agc", reliability_score=0.95)],
            ),
            ClaimRecord(
                claim_id="c2",
                claim_text="It operated at a clock frequency of 2.048 MHz with 4KB of RAM.",
                confidence_score=0.92,
                primary_source=SourceRecord(title="Computer History Museum", url="https://computerhistory.org", reliability_score=0.94),
            ),
            ClaimRecord(
                claim_id="c3",
                claim_text="Margaret Hamilton led the team developing the onboard flight software.",
                confidence_score=0.98,
                primary_source=SourceRecord(title="Smithsonian", url="https://si.edu/hamilton", reliability_score=0.95),
            ),
        ]
        dossier = ResearchDossier(topic="Apollo Guidance Computer", claims=claims)
        script = Script(
            topic="Apollo Guidance Computer",
            title="The Code That Landed on the Moon",
            total_duration=30.0,
            full_transcript="In 1969, a 70-pound computer with just 4 kilobytes of RAM safely landed humans on the Moon.",
            scenes=[
                ScriptScene(
                    scene_id="s1",
                    duration=30.0,
                    narration_text="In 1969, a 70-pound computer with just 4 kilobytes of RAM safely landed humans on the Moon.",
                    visual_asset_path="assets/images/agc.png",
                    hero_frame_description="Apollo Guidance Computer DSKY interface",
                )
            ],
        )
        video = RenderArtifact(
            video_path="renders/final.mp4",
            duration_seconds=30.0,
            file_size_bytes=4_500_000,
        )
        ledger = ProductionCostLedger(
            run_id="run_apollo",
            items=[
                CostItem(category="llm", item_name="LLM", units_consumed=8000, unit_type="tokens", unit_rate_usd=0.000005, total_cost_usd=0.04),
                CostItem(category="tts", item_name="TTS", units_consumed=500, unit_type="characters", unit_rate_usd=0.00003, total_cost_usd=0.015),
            ],
            video_duration_seconds=30.0,
        )
        dna = CreatorDNA(creator_id="harness9_creator")

        report = self.evaluator.evaluate_production(
            brief=brief,
            dossier=dossier,
            script=script,
            video=video,
            ledger=ledger,
            creator_dna=dna,
            run_id="run_apollo_01",
        )

        self.assertIsInstance(report, ContentBenchReport)
        self.assertTrue(report.passed)
        self.assertGreater(report.overall_score, 0.80)
        self.assertIn("S_research", report.layer_scores)
        self.assertIn("S_script", report.layer_scores)
        self.assertIn("S_video", report.layer_scores)
        self.assertIn("S_cost", report.layer_scores)

        # Verify composite weight formulation: 0.25 S_res + 0.30 S_scr + 0.30 S_vid + 0.15 S_cst
        expected_composite = (
            0.25 * report.layer_scores["S_research"]
            + 0.30 * report.layer_scores["S_script"]
            + 0.30 * report.layer_scores["S_video"]
            + 0.15 * report.layer_scores["S_cost"]
        )
        self.assertAlmostEqual(report.overall_score, round(expected_composite, 4), places=3)

        # Convert to production contract EvaluationReports
        eval_reports = report.to_evaluation_reports()
        self.assertEqual(len(eval_reports), 4)
        self.assertTrue(all(isinstance(r, EvaluationReport) for r in eval_reports))

        # Test Markdown formatting
        md = report.to_markdown()
        self.assertIn("ContentBench Quality OS Benchmark Report", md)
        self.assertIn("4-Layer Quality Matrix", md)
        self.assertIn("PASSED", md)

    def test_run_benchmark_suite(self):
        suite_cases = [
            {
                "brief": ContentBrief(project_id="tc1", topic="Semiconductors", target_duration_seconds=30),
                "dossier": ResearchDossier(topic="Semiconductors"),
                "script": Script(topic="Semiconductors", title="Chips", total_duration=30.0),
                "video": RenderArtifact(video_path="v.mp4", duration_seconds=30.0),
                "ledger": ProductionCostLedger(run_id="tc1", video_duration_seconds=30.0),
            },
            {
                "brief": ContentBrief(project_id="tc2", topic="Quantum Computing", target_duration_seconds=30),
                "dossier": ResearchDossier(topic="Quantum Computing"),
                "script": Script(topic="Quantum Computing", title="Qubits", total_duration=30.0),
                "video": RenderArtifact(video_path="v.mp4", duration_seconds=30.0),
                "ledger": ProductionCostLedger(run_id="tc2", video_duration_seconds=30.0),
            },
        ]
        suite_results = self.evaluator.run_benchmark_suite(suite_cases)
        self.assertEqual(suite_results["total_test_cases"], 2)
        self.assertIn("average_composite_score", suite_results)
        self.assertIn("pass_rate_percent", suite_results)
        self.assertEqual(len(suite_results["reports"]), 2)

    # -----------------------------------------------------------------------
    # 6. Boundary & Persistence Tests
    # -----------------------------------------------------------------------
    def test_contentbench_corrupt_voice_qa_penalties(self):
        """Verify heavy acoustic penalties for severe clipping and dead air."""
        voice_qa_bad = {
            "passed": False,
            "clipping_ratio": 0.05,  # 5% severe clipping
            "max_dead_air_duration_sec": 1.2,  # 1.2s dead air gap
            "loudness_variance_db": 6.5,
            "speech_beat_max_drift_sec": 0.45,  # 450ms drift
        }
        res = self.evaluator.evaluate_video(
            video=RenderArtifact(video_path="bad.mp4", duration_seconds=30.0, validation_status="INVALID"),
            voice_qa_data=voice_qa_bad,
        )
        self.assertFalse(res.passed)
        self.assertLess(res.composite_score, 0.50)
        self.assertLess(res.scores["voice_qa_score"], 0.60)
        self.assertLess(res.scores["speech_beat_sync_score"], 0.50)

    def test_contentbench_report_json_and_yaml_persistence(self):
        """Verify report model saves and loads cleanly to both JSON and YAML."""
        report = ContentBenchReport(
            run_id="run_persist_01",
            project_id="p_persist",
            topic="Persistence Test",
            passing_threshold=0.80,
            layer_scores={
                "S_research": 0.90,
                "S_script": 0.85,
                "S_video": 0.88,
                "S_cost": 0.92,
            },
        )
        json_path, yaml_path = report.save(self.temp_dir, base_name="benchmark_report")
        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        loaded_json = ContentBenchReport.load(json_path)
        self.assertEqual(loaded_json.run_id, "run_persist_01")
        self.assertAlmostEqual(loaded_json.overall_score, report.overall_score)
        self.assertTrue(loaded_json.passed)

        loaded_yaml = ContentBenchReport.load(yaml_path)
        self.assertEqual(loaded_yaml.run_id, "run_persist_01")
        self.assertAlmostEqual(loaded_yaml.overall_score, report.overall_score)


if __name__ == "__main__":
    unittest.main()
