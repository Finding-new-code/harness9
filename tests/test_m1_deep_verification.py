"""Comprehensive deep verification tests for M1 models, filesystem, and research engine."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.config import AppConfig, DEFAULT_TARGET_DURATION_SEC, get_default_config
from src.models import (
    AssetProvenanceLedger,
    Beat,
    Claim,
    CreatorInfo,
    Dimensions,
    DossierMetadata,
    LicenseInfo,
    MediaAsset,
    PipelineSummary,
    ResearchDossier,
    Scene,
    Script,
    Source,
    StageResult,
    Statistic,
    Storyboard,
    Summary,
    TalkingPoint,
)
from src.research.engine import ResearchEngine
from src.research.providers import (
    DuckDuckGoProvider,
    MockSearchProvider,
    MultiProviderDispatcher,
    SearchResult,
    WikipediaProvider,
    clean_snippet,
    expand_topic_queries,
    extract_domain,
)
from src.research.scoring import (
    ScoringWeights,
    calculate_clarity_score,
    calculate_confidence_score,
    calculate_conflict_penalty,
    calculate_corroboration_score,
    get_domain_authority,
    score_claim,
)
from src.utils.filesystem import (
    atomic_write,
    ensure_dir,
    load_json,
    load_text,
    load_yaml,
    resolve_path,
    save_json,
    save_text,
    save_yaml,
    sha256_bytes,
    sha256_file,
)


class TestM1DeepVerification(unittest.TestCase):
    """Deep verification suite for M1 schemas, utilities, and engine."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_filesystem_atomic_and_helpers(self):
        txt_path = Path(self.temp_dir) / "test" / "file.txt"
        save_text(txt_path, "Deep Test")
        self.assertEqual(load_text(txt_path), "Deep Test")

        json_path = Path(self.temp_dir) / "test" / "file.json"
        save_json(json_path, {"a": 1, "b": [2, 3]})
        self.assertEqual(load_json(json_path)["b"], [2, 3])

        yaml_path = Path(self.temp_dir) / "test" / "file.yaml"
        save_yaml(yaml_path, {"key": "val"})
        self.assertEqual(load_yaml(yaml_path)["key"], "val")

        sha = sha256_file(txt_path)
        self.assertEqual(sha, sha256_bytes(b"Deep Test"))

    def test_all_schema_roundtrips(self):
        # 1. Dossier
        meta = DossierMetadata(run_id="run_1", target_duration_seconds=30)
        summ = Summary(headline="H", executive_summary="E", key_takeaways=["T1", "T2"])
        c = Claim(
            claim_id="claim_01",
            claim_text="Text 1",
            category="origin_history",
            confidence_score=0.95,
            primary_source=Source(title="S1", url="https://example.com"),
        )
        tp = TalkingPoint(beat_index=1, title="TP1", narrative_hook="Hook 1", estimated_duration_sec=10.0)
        st = Statistic(metric="M", value="V", context="C", source_claim_id="claim_01")
        dossier = ResearchDossier(topic="Test Topic", metadata=meta, summary=summ, claims=[c], talking_points=[tp], statistics=[st], suggested_visual_queries=["Q1"])
        
        jp, yp = dossier.save(self.temp_dir, base_name="test_dossier")
        self.assertEqual(ResearchDossier.load(jp).topic, "Test Topic")
        self.assertEqual(ResearchDossier.load(yp).topic, "Test Topic")

        # 2. Ledger
        asset = MediaAsset(
            asset_id="asset_01",
            local_path="assets/images/img.jpg",
            dimensions=Dimensions(width=1920, height=1080),
            creator=CreatorInfo(name="Author"),
            license=LicenseInfo(license_type="CC0"),
        )
        ledger = AssetProvenanceLedger(project_id="p1", total_assets=1, assets=[asset])
        jp, yp = ledger.save(self.temp_dir, base_name="test_ledger")
        self.assertEqual(AssetProvenanceLedger.load(jp).assets[0].asset_id, "asset_01")
        self.assertEqual(AssetProvenanceLedger.load(yp).assets[0].license.license_type, "CC0")

        # 3. Script
        beat = Beat(beat_id="b1", start_time=0.0, end_time=5.0, duration=5.0, text="Intro")
        scene = Scene(scene_id="s1", title="Scene 1", start_time=0.0, duration=5.0, narration_text="Intro", beats=[beat])
        storyboard = Storyboard(project_id="p1", target_duration=5.0, scenes=[scene])
        script = Script(topic="T", title="Title", total_duration=5.0, storyboard=storyboard)
        jp, yp = script.save(self.temp_dir, base_name="test_script")
        self.assertEqual(Script.load(jp).title, "Title")
        self.assertEqual(Script.load(yp).storyboard.scenes[0].beats[0].text, "Intro")

        # 4. Summary
        stage = StageResult(stage_name="Research", success=True, execution_time_seconds=1.2, artifacts=["research_dossier.json"])
        pipeline_sum = PipelineSummary(run_id="r1", topic="T", start_time="2026-08-31T00:00:00Z", end_time="2026-08-31T00:00:01Z", total_duration_seconds=1.0, stages=[stage])
        jp, yp = pipeline_sum.save(self.temp_dir, base_name="test_summary")
        self.assertEqual(PipelineSummary.load(jp).stages[0].stage_name, "Research")
        self.assertEqual(PipelineSummary.load(yp).status, "SUCCESS")

    def test_all_four_presets(self):
        engine = ResearchEngine()
        presets = [
            ("The History of the Transistor", "Transistor"),
            ("How GPUs Work", "GPU"),
            ("The Apollo Guidance Computer", "Apollo"),
            ("How Quantum Computers Work", "Quantum"),
        ]
        for topic, expected_kw in presets:
            d = engine.synthesize_research(topic, offline=True, target_duration=30)
            self.assertIn(expected_kw.lower(), d.topic.lower())
            self.assertGreaterEqual(len(d.claims), 4)
            self.assertEqual(len(d.talking_points), 3)
            self.assertGreaterEqual(len(d.statistics), 1)
            self.assertGreaterEqual(len(d.suggested_visual_queries), 3)

    def test_live_search_query_expansion_and_dispatch(self):
        disp = MultiProviderDispatcher()
        self.assertGreaterEqual(len(disp.providers), 2)
        queries = expand_topic_queries("Microprocessors")
        self.assertEqual(len(queries), 5)


if __name__ == "__main__":
    unittest.main()
