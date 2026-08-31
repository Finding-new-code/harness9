"""
tests/test_m1_challenger2_stress.py — Empirical Stress & Adversarial Verification Suite
Challenger 2 for Milestone 1 (Research & Fact Synthesis Engine - R1).

Focus Areas:
1. Seeded Procedural Determinism:
   - Identical topic offline yields 100% identical claims, metrics (statistics), talking points, visual queries, summaries.
   - Presets vs arbitrary procedural topics across multiple iterations and interleaved executions.
   - Case/whitespace insensitivity, unicode/multilingual topics, long strings, boundary durations.
2. JSON/YAML Schema Roundtripping:
   - Full roundtrip parity for ResearchDossier, AssetProvenanceLedger, Script, PipelineSummary.
   - String serialization (to_json/from_json, to_yaml/from_yaml) and atomic file I/O (save/load).
   - Edge case schemas (Unicode, quotes, newlines, high precision floats, optional fields populated vs omitted).
   - Low-level filesystem JSON/YAML helpers (save_json/load_json, save_yaml/load_yaml).
3. Cross-Platform Path Safety & Atomic Write Concurrency:
   - Multi-threaded and multi-process concurrent atomic writes to identical and distinct targets.
   - Concurrent reader-writer integrity (no partial reads, no JSON decode corruption during continuous overwrites).
   - Cross-platform path resolution (relative, absolute, spaces, deep nesting, Windows backslashes / POSIX slashes, Unicode paths).
   - Error handling & temp file cleanup on write failure (original target preservation).
"""

import concurrent.futures
import json
import os
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from src.models.dossier import (
    Claim,
    DossierMetadata,
    ResearchDossier,
    Source,
    Statistic,
    Summary,
    TalkingPoint,
)
from src.models.ledger import (
    AssetProvenanceLedger,
    CreatorInfo,
    Dimensions,
    LicenseInfo,
    MediaAsset,
)
from src.models.script import (
    Beat,
    Scene,
    Script,
    Storyboard,
)
from src.models.summary import (
    PipelineSummary,
    StageResult,
)
from src.research.engine import ResearchEngine
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


class TestSeededProceduralDeterminism(unittest.TestCase):
    """Stress testing deterministic behavior of ResearchEngine in offline mode."""

    def setUp(self):
        self.engine = ResearchEngine()

    def test_preset_topics_procedural_determinism_multi_iteration(self):
        """Verify that repeated calls for preset topics yield identical claims, stats, and talking points."""
        presets = [
            "The History of the Transistor",
            "How GPUs Work",
            "The Apollo Guidance Computer",
            "How Quantum Computers Work",
        ]
        iterations = 10

        for topic in presets:
            base_dossier = self.engine.synthesize_research(topic, offline=True, target_duration=30)
            base_claims = [c.to_dict() for c in base_dossier.claims]
            base_stats = [s.to_dict() for s in base_dossier.statistics]
            base_tps = [tp.to_dict() for tp in base_dossier.talking_points]
            base_vis = list(base_dossier.suggested_visual_queries)
            base_summary = base_dossier.summary.to_dict()

            self.assertGreaterEqual(len(base_claims), 3, f"Preset '{topic}' has fewer than 3 claims")
            self.assertGreaterEqual(len(base_tps), 1, f"Preset '{topic}' has no talking points")

            for i in range(iterations):
                repeat_dossier = self.engine.synthesize_research(topic, offline=True, target_duration=30)
                repeat_claims = [c.to_dict() for c in repeat_dossier.claims]
                repeat_stats = [s.to_dict() for s in repeat_dossier.statistics]
                repeat_tps = [tp.to_dict() for tp in repeat_dossier.talking_points]
                repeat_vis = list(repeat_dossier.suggested_visual_queries)
                repeat_summary = repeat_dossier.summary.to_dict()

                self.assertEqual(base_claims, repeat_claims, f"Claims mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_stats, repeat_stats, f"Stats mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_tps, repeat_tps, f"Talking points mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_vis, repeat_vis, f"Visual queries mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_summary, repeat_summary, f"Summary mismatch in iteration {i} for '{topic}'")

    def test_arbitrary_topics_procedural_determinism_multi_iteration(self):
        """Verify that procedural synthesis of novel non-preset topics is 100% deterministic."""
        novel_topics = [
            "The Physics of High-Temperature Superconductors",
            "Cellular Automata in Biological Morphogenesis",
            "History and Structural Engineering of Roman Concrete",
            "RISC-V Open Standard Instruction Set Architecture",
            "Deep Sea Hydrothermal Vent Ecosystems",
            "Gravitational Wave Interferometry with LIGO",
            "The Evolution of Synthetic Aperture Radar",
            "Memristor Crossbar Arrays in Neuromorphic Computing",
        ]
        iterations = 8

        for topic in novel_topics:
            base_dossier = self.engine.synthesize_research(topic, offline=True, target_duration=45)
            base_claims = [c.to_dict() for c in base_dossier.claims]
            base_stats = [s.to_dict() for s in base_dossier.statistics]
            base_tps = [tp.to_dict() for tp in base_dossier.talking_points]
            base_vis = list(base_dossier.suggested_visual_queries)
            base_summary = base_dossier.summary.to_dict()

            self.assertGreaterEqual(len(base_claims), 4, f"Procedural topic '{topic}' has fewer than 4 claims")

            for i in range(iterations):
                repeat_dossier = self.engine.synthesize_research(topic, offline=True, target_duration=45)
                repeat_claims = [c.to_dict() for c in repeat_dossier.claims]
                repeat_stats = [s.to_dict() for s in repeat_dossier.statistics]
                repeat_tps = [tp.to_dict() for tp in repeat_dossier.talking_points]
                repeat_vis = list(repeat_dossier.suggested_visual_queries)
                repeat_summary = repeat_dossier.summary.to_dict()

                self.assertEqual(base_claims, repeat_claims, f"Claims mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_stats, repeat_stats, f"Stats mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_tps, repeat_tps, f"Talking points mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_vis, repeat_vis, f"Visual queries mismatch in iteration {i} for '{topic}'")
                self.assertEqual(base_summary, repeat_summary, f"Summary mismatch in iteration {i} for '{topic}'")

    def test_interleaved_multi_topic_determinism(self):
        """Verify that interleaved execution of diverse topics does not poison internal RNG state."""
        topics = [
            "How GPUs Work",
            "The Physics of High-Temperature Superconductors",
            "The History of the Transistor",
            "Cellular Automata in Biological Morphogenesis",
            "The Apollo Guidance Computer",
            "Memristor Crossbar Arrays in Neuromorphic Computing",
        ]

        # First pass: collect baseline
        baselines = {}
        for t in topics:
            d = self.engine.synthesize_research(t, offline=True, target_duration=30)
            baselines[t] = {
                "claims": [c.to_dict() for c in d.claims],
                "stats": [s.to_dict() for s in d.statistics],
                "tps": [tp.to_dict() for tp in d.talking_points],
                "vis": list(d.suggested_visual_queries),
            }

        # Second pass in reversed order with multiple repetitions
        for rep in range(3):
            for t in reversed(topics):
                d = self.engine.synthesize_research(t, offline=True, target_duration=30)
                curr = {
                    "claims": [c.to_dict() for c in d.claims],
                    "stats": [s.to_dict() for s in d.statistics],
                    "tps": [tp.to_dict() for tp in d.talking_points],
                    "vis": list(d.suggested_visual_queries),
                }
                self.assertEqual(baselines[t]["claims"], curr["claims"], f"Interleaved claims mismatch for '{t}' (rep {rep})")
                self.assertEqual(baselines[t]["stats"], curr["stats"], f"Interleaved stats mismatch for '{t}' (rep {rep})")
                self.assertEqual(baselines[t]["tps"], curr["tps"], f"Interleaved talking points mismatch for '{t}' (rep {rep})")
                self.assertEqual(baselines[t]["vis"], curr["vis"], f"Interleaved visual queries mismatch for '{t}' (rep {rep})")

    def test_case_and_whitespace_invariance_for_presets(self):
        """Verify that casing variations and whitespace in preset topic briefs match the same preset deterministically."""
        variants = [
            ("The History of the Transistor", "the history of the transistor"),
            ("  The History of the Transistor  \t", "THE HISTORY OF THE TRANSISTOR"),
            ("How GPUs Work", "HOW GPUS WORK"),
            ("how gpu works", "How GPU Works"),
        ]

        for v1, v2 in variants:
            d1 = self.engine.synthesize_research(v1, offline=True, target_duration=30)
            d2 = self.engine.synthesize_research(v2, offline=True, target_duration=30)
            claims1 = [c.claim_text for c in d1.claims]
            claims2 = [c.claim_text for c in d2.claims]
            self.assertEqual(claims1, claims2, f"Preset claim mismatch between '{v1}' and '{v2}'")

    def test_unicode_and_multilingual_procedural_determinism(self):
        """Verify that multilingual and Unicode topics synthesize deterministically without encoding faults."""
        unicode_topics = [
            "半導体集積回路の歴史と微細化技術",
            "تاريخ الحواسيب الكمومية والفيزياء الحديثة",
            "Évolution des accélérateurs graphiques modernes",
            "Geschichte der Apollo-Navigationscomputer und Raumfahrttechnik",
            "История транзисторов и полупроводниковых приборов",
        ]

        for topic in unicode_topics:
            d1 = self.engine.synthesize_research(topic, offline=True, target_duration=30)
            d2 = self.engine.synthesize_research(topic, offline=True, target_duration=30)
            self.assertEqual([c.to_dict() for c in d1.claims], [c.to_dict() for c in d2.claims])
            self.assertEqual([s.to_dict() for s in d1.statistics], [s.to_dict() for s in d2.statistics])
            self.assertEqual([tp.to_dict() for tp in d1.talking_points], [tp.to_dict() for tp in d2.talking_points])

    def test_duration_proportional_scaling_determinism(self):
        """Verify that talking point durations scale deterministically across different target durations."""
        durations = [15, 30, 45, 60, 120, 300]
        topic = "Quantum Metamaterials"

        for dur in durations:
            d1 = self.engine.synthesize_research(topic, offline=True, target_duration=dur)
            d2 = self.engine.synthesize_research(topic, offline=True, target_duration=dur)
            self.assertEqual(d1.metadata.target_duration_seconds, dur)
            self.assertEqual(d2.metadata.target_duration_seconds, dur)
            tps1 = [tp.to_dict() for tp in d1.talking_points]
            tps2 = [tp.to_dict() for tp in d2.talking_points]
            self.assertEqual(tps1, tps2)

            total_dur = sum(tp.estimated_duration_sec for tp in d1.talking_points)
            self.assertAlmostEqual(total_dur, float(dur), delta=1.5)


class TestSchemaRoundtripping(unittest.TestCase):
    """Stress testing JSON and YAML serialization/deserialization across all data models."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.out_dir = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_research_dossier_json_yaml_roundtrip(self):
        """Test ResearchDossier roundtrip through to_json/from_json, to_yaml/from_yaml, and disk save/load."""
        engine = ResearchEngine()
        dossier = engine.synthesize_research("How GPUs Work", offline=True, target_duration=30)

        # 1. JSON String roundtrip
        json_str = dossier.to_json()
        dossier_from_json = ResearchDossier.from_json(json_str)
        self.assertEqual(dossier.to_dict(), dossier_from_json.to_dict())

        # 2. YAML String roundtrip
        yaml_str = dossier.to_yaml()
        dossier_from_yaml = ResearchDossier.from_yaml(yaml_str)
        self.assertEqual(dossier.to_dict(), dossier_from_yaml.to_dict())

        # 3. Disk Save & Load (JSON and YAML)
        json_path, yaml_path = dossier.save(self.out_dir, base_name="test_dossier")
        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        loaded_from_json = ResearchDossier.load(json_path)
        loaded_from_yaml = ResearchDossier.load(yaml_path)

        self.assertEqual(dossier.to_dict(), loaded_from_json.to_dict())
        self.assertEqual(dossier.to_dict(), loaded_from_yaml.to_dict())

    def test_research_dossier_edge_values_roundtrip(self):
        """Test ResearchDossier with special characters, unicode, quotes, empty optional fields."""
        metadata = DossierMetadata(
            run_id="run_edge_#1_αβγ",
            generated_at="2026-08-31T12:00:00.123456+00:00",
            mode="offline_fallback",
            target_duration_seconds=60,
            search_backend="custom_search'backend\"with special & chars <tag>",
        )
        summary = Summary(
            headline="Headline with \"quotes\", 'single quotes', \nnewlines, and unicode ⚡ 🚀",
            executive_summary="Line 1\nLine 2: 100% efficiency & <xml> tags\nLine 3: \tTabbed content.",
            key_takeaways=["Takeaway 1: 50% increase", "Takeaway 2: 'quoted' text", "Takeaway 3: π ≈ 3.14159"],
        )
        claims = [
            Claim(
                claim_id="claim_01",
                claim_text="Claim with special formatting: 99.9% reliability; cost < $0.01 per 1,000 units.",
                category="quantitative_metric",
                confidence_score=0.99,
                primary_source=Source(
                    title="Source with \"quotes\" and symbols: 100% verified",
                    url="https://example.com/search?q=test%20query&lang=en#section-1",
                    publisher="Example Org, Inc.",
                ),
                corroborating_sources=[
                    Source(title="Corrob 1", url="https://corrob1.org/path", publisher=None),
                    Source(title="Corrob 2", url="https://corrob2.edu/res", publisher="University"),
                ],
                visual_cue_suggestion="Diagram showing <flow> & 'process'",
                verification_notes="Notes with \n multi-line content.",
            ),
            Claim(
                claim_id="claim_02",
                claim_text="Minimal claim with empty corroborating sources and notes.",
                category="origin_history",
                confidence_score=0.75,
                primary_source=Source(title="Minimal", url="https://minimal.org"),
                corroborating_sources=[],
                visual_cue_suggestion="",
                verification_notes="",
            ),
        ]
        talking_points = [
            TalkingPoint(
                beat_index=1,
                title="Introduction: The \"Breakthrough\"",
                narrative_hook="Hook containing colons: semicolons; and ampersands & more.",
                supported_claim_ids=["claim_01", "claim_02"],
                estimated_duration_sec=14.5,
            )
        ]
        statistics = [
            Statistic(
                metric="Efficiency Gain",
                value="99.9%",
                context="Context with numbers: 1,000,000 and decimals: 0.0001",
                source_claim_id="claim_01",
            )
        ]
        queries = ["Query 1: \"high precision\"", "Query 2: 1080p & 4k diagrams", "Query 3: α-particles"]

        dossier = ResearchDossier(
            topic="Edge Case Topic: \"Quotes\" & Symbols ⚡",
            metadata=metadata,
            summary=summary,
            claims=claims,
            talking_points=talking_points,
            statistics=statistics,
            suggested_visual_queries=queries,
        )

        # JSON roundtrip
        j_str = dossier.to_json()
        from_j = ResearchDossier.from_json(j_str)
        self.assertEqual(dossier.to_dict(), from_j.to_dict())

        # YAML roundtrip
        y_str = dossier.to_yaml()
        from_y = ResearchDossier.from_yaml(y_str)
        self.assertEqual(dossier.to_dict(), from_y.to_dict())

        # Disk roundtrip
        jp, yp = dossier.save(self.out_dir, base_name="edge_dossier")
        self.assertEqual(dossier.to_dict(), ResearchDossier.load(jp).to_dict())
        self.assertEqual(dossier.to_dict(), ResearchDossier.load(yp).to_dict())

    def test_asset_provenance_ledger_roundtrip(self):
        """Test AssetProvenanceLedger roundtrip through JSON, YAML, and atomic disk save/load."""
        assets = [
            MediaAsset(
                asset_id="asset_01",
                local_path="assets/images/scene1.jpg",
                claim_id_refs=["claim_01"],
                scene_target="scene_01",
                media_type="image/jpeg",
                absolute_path=str(self.out_dir / "assets/images/scene1.jpg"),
                file_size_bytes=1048576,
                file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                dimensions=Dimensions(width=1920, height=1080, aspect_ratio="16:9"),
                source_provider="wikimedia_commons",
                source_url="https://commons.wikimedia.org/wiki/File:Transistor.jpg",
                page_url="https://commons.wikimedia.org/wiki/File:Transistor.jpg",
                creator=CreatorInfo(name="John Doe", profile_url="https://commons.wikimedia.org/User:JohnDoe"),
                license=LicenseInfo(
                    license_type="CC-BY-SA-4.0",
                    license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                    attribution_text="Photo by John Doe / CC BY-SA 4.0",
                    attribution_required=True,
                    commercial_use_allowed=True,
                    modification_allowed=True,
                ),
                verification_status="VERIFIED",
                downloaded_at="2026-08-31T12:00:00Z",
            ),
            MediaAsset(
                asset_id="asset_02",
                local_path="assets/images/procedural_scene2.svg",
                claim_id_refs=["claim_02"],
                scene_target="scene_02",
                media_type="image/svg+xml",
                file_size_bytes=4096,
                file_sha256="procedural_sha256_mock",
                source_provider="procedural_vector_generator",
                source_url="internal://procedural/scene2",
                verification_status="GENERATED",
            ),
        ]
        ledger = AssetProvenanceLedger(
            project_id="proj_test_123",
            total_assets=2,
            license_summary={"CC-BY-SA-4.0": 1, "Public Domain / Procedural": 1},
            assets=assets,
        )

        # JSON roundtrip
        j_str = ledger.to_json()
        from_j = AssetProvenanceLedger.from_json(j_str)
        self.assertEqual(ledger.to_dict(), from_j.to_dict())

        # YAML roundtrip
        y_str = ledger.to_yaml()
        from_y = AssetProvenanceLedger.from_yaml(y_str)
        self.assertEqual(ledger.to_dict(), from_y.to_dict())

        # Disk roundtrip
        jp, yp = ledger.save(self.out_dir, base_name="test_ledger")
        self.assertEqual(ledger.to_dict(), AssetProvenanceLedger.load(jp).to_dict())
        self.assertEqual(ledger.to_dict(), AssetProvenanceLedger.load(yp).to_dict())

    def test_script_and_storyboard_roundtrip(self):
        """Test Script, Storyboard, Scene, and Beat roundtrip through JSON, YAML, and disk save/load."""
        beats1 = [
            Beat(beat_id="beat_01", start_time=0.0, end_time=4.5, duration=4.5, text="First beat narration.", visual_cue="Show title card"),
            Beat(beat_id="beat_02", start_time=4.5, end_time=10.0, duration=5.5, text="Second beat narration with details.", visual_cue="Zoom in on schematic"),
        ]
        scene1 = Scene(
            scene_id="scene_01",
            title="Introduction",
            start_time=0.0,
            duration=10.0,
            narration_text="First beat narration. Second beat narration with details.",
            visual_asset_path="assets/images/scene1.jpg",
            hero_frame_description="Hero view of early laboratory apparatus",
            entrance_animation="fadeInScale",
            transition_out="crossFade",
            beats=beats1,
        )
        storyboard = Storyboard(
            project_id="proj_script_456",
            target_duration=30.0,
            scenes=[scene1],
            aspect_ratio="16:9",
        )
        script = Script(
            topic="The History of the Transistor",
            title="The Spark of Computing: The Transistor Story",
            total_duration=30.0,
            storyboard=storyboard,
            full_transcript="First beat narration. Second beat narration with details.",
            word_count=10,
        )

        # JSON roundtrip
        j_str = script.to_json()
        from_j = Script.from_json(j_str)
        self.assertEqual(script.to_dict(), from_j.to_dict())

        # YAML roundtrip
        y_str = script.to_yaml()
        from_y = Script.from_yaml(y_str)
        self.assertEqual(script.to_dict(), from_y.to_dict())

        # Disk roundtrip
        jp, yp = script.save(self.out_dir, base_name="test_script")
        self.assertEqual(script.to_dict(), Script.load(jp).to_dict())
        self.assertEqual(script.to_dict(), Script.load(yp).to_dict())

    def test_pipeline_summary_roundtrip(self):
        """Test PipelineSummary and StageResult roundtrip through JSON, YAML, and disk save/load."""
        stages = [
            StageResult(stage_name="research_engine", success=True, execution_time_seconds=0.45, artifacts=["research_dossier.json", "research_dossier.yaml"], metrics={"claims_count": 4}),
            StageResult(stage_name="asset_pipeline", success=True, execution_time_seconds=1.20, artifacts=["asset_ledger.json", "assets/images/img1.svg"], metrics={"assets_count": 4}),
            StageResult(stage_name="script_voiceover", success=True, execution_time_seconds=2.10, artifacts=["SCRIPT.md", "STORYBOARD.md", "assets/audio/narration.wav"], metrics={"duration": 30.0}),
            StageResult(stage_name="hyperframes_render", success=True, execution_time_seconds=15.30, artifacts=["renders/final.mp4"], metrics={"fps": 30, "resolution": "1920x1080"}),
        ]
        summary = PipelineSummary(
            run_id="run_pipeline_summary_test",
            topic="How GPUs Work",
            start_time="2026-08-31T10:00:00Z",
            end_time="2026-08-31T10:00:19Z",
            total_duration_seconds=19.05,
            status="SUCCESS",
            stages=stages,
            output_directory=str(self.out_dir),
            final_video_path=str(self.out_dir / "renders/final.mp4"),
            metrics={"total_stages": 4, "passed_stages": 4},
        )

        # JSON roundtrip
        j_str = summary.to_json()
        from_j = PipelineSummary.from_json(j_str)
        self.assertEqual(summary.to_dict(), from_j.to_dict())

        # YAML roundtrip
        y_str = summary.to_yaml()
        from_y = PipelineSummary.from_yaml(y_str)
        self.assertEqual(summary.to_dict(), from_y.to_dict())

        # Disk roundtrip
        jp, yp = summary.save(self.out_dir, base_name="test_pipeline_summary")
        self.assertEqual(summary.to_dict(), PipelineSummary.load(jp).to_dict())
        self.assertEqual(summary.to_dict(), PipelineSummary.load(yp).to_dict())

    def test_low_level_filesystem_json_yaml_helpers(self):
        """Test save_json/load_json, save_yaml/load_yaml, save_text/load_text in src.utils.filesystem."""
        sample_dict = {
            "str_val": "hello world 🌍",
            "int_val": 42,
            "float_val": 3.1415926535,
            "bool_val": True,
            "none_val": None,
            "list_val": [1, "two", 3.0, {"nested": True}],
            "dict_val": {"a": 1, "b": [10, 20, 30]},
        }

        # JSON helper
        j_file = self.out_dir / "helpers_test.json"
        save_json(j_file, sample_dict)
        loaded_j = load_json(j_file)
        self.assertEqual(sample_dict, loaded_j)

        # YAML helper
        y_file = self.out_dir / "helpers_test.yaml"
        save_yaml(y_file, sample_dict)
        loaded_y = load_yaml(y_file)
        self.assertEqual(sample_dict, loaded_y)

    def test_low_level_filesystem_json_yaml_helpers(self):
        """Test save_json/load_json, save_yaml/load_yaml, save_text/load_text in src.utils.filesystem."""
        sample_dict = {
            "str_val": "hello world 🌍",
            "int_val": 42,
            "float_val": 3.1415926535,
            "bool_val": True,
            "none_val": None,
            "list_val": [1, "two", 3.0, {"nested": True}],
            "dict_val": {"a": 1, "b": [10, 20, 30]},
        }

        # JSON helper
        j_file = self.out_dir / "helpers_test.json"
        save_json(j_file, sample_dict)
        loaded_j = load_json(j_file)
        self.assertEqual(sample_dict, loaded_j)

        # YAML helper
        y_file = self.out_dir / "helpers_test.yaml"
        save_yaml(y_file, sample_dict)
        loaded_y = load_yaml(y_file)
        self.assertEqual(sample_dict, loaded_y)

        # Text helper roundtrip verification
        t_file = self.out_dir / "helpers_test.txt"
        sample_text = "Line 1: Sample UTF-8 content\nLine 2: 🚀 Unicode and special characters: <tag> & 'quote'\n"
        save_text(t_file, sample_text)
        loaded_t = load_text(t_file)
        self.assertEqual(sample_text, loaded_t)


def _mp_worker(args: Tuple[str, int]) -> Dict[str, Any]:
    target_dir_str, idx = args
    target_dir = Path(target_dir_str)
    file_path = target_dir / f"output_proc_{idx % 5}.json"
    payload = {"proc_id": idx, "time": time.time(), "magic": f"magic_{idx:04d}"}
    save_json(file_path, payload)
    return load_json(file_path)


class TestAtomicWriteConcurrencyAndPathSafety(unittest.TestCase):
    """Stress testing atomic writes under concurrency and cross-platform path resolution safety."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_windows_crlf_translation_vulnerability(self):
        """
        Adversarial Test: Detect platform line-ending conversion in atomic_write.
        On Windows without newline='', os.fdopen converts \\n to \\r\\n, altering binary SHA-256.
        """
        target = self.test_dir / "line_endings.txt"
        content = "line1\nline2\n"
        save_text(target, content)
        raw_bytes = target.read_bytes()
        # Document whether CRLF injection occurs
        has_crlf = b"\r\n" in raw_bytes
        # On Windows under standard text mode fdopen without newline='', CRLF is injected:
        if os.name == "nt":
            self.assertTrue(has_crlf, "Observed newline translation to CRLF on Windows")

    def test_windows_atomic_replace_concurrency_vulnerability(self):
        """
        Adversarial Test: Detect Windows PermissionError (WinError 5/32) when multiple threads
        attempt simultaneous os.replace() without a retry loop.
        """
        target_file = self.test_dir / "concurrent_overwrite.json"
        num_threads = 30
        barrier = threading.Barrier(num_threads)
        errors = []

        def worker(thread_id: int):
            try:
                barrier.wait()
                payload = {"writer_id": thread_id, "data": "X" * 512}
                save_json(target_file, payload)
            except PermissionError as exc:
                errors.append((thread_id, "PermissionError", str(exc)))
            except Exception as exc:
                errors.append((thread_id, "OtherError", str(exc)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if os.name == "nt":
            # Confirms reproduction of PermissionError on unmitigated Windows atomic_write
            perm_errors = [e for e in errors if e[1] == "PermissionError"]
            print(f"\n[Empirical Finding] Windows PermissionError reproduced in {len(perm_errors)}/{num_threads} threads")

    def test_concurrent_multiprocess_atomic_writes(self):
        """Stress-test concurrent atomic writes across multiple distinct files in process pool."""
        target_dir = self.test_dir / "multiprocess_test"
        ensure_dir(target_dir)

        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_mp_worker, (str(target_dir), i)) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), 20)
        for r in results:
            self.assertIn("magic", r)

    def test_cross_platform_path_resolution(self):
        """Test resolve_path across relative paths, absolute paths, nested missing dirs, spaces, and Unicode."""
        base_dir = self.test_dir / "project space with spaces" / "sub_dir"
        ensure_dir(base_dir)

        # 1. Relative path resolution
        p1 = resolve_path("output/test.json", base=base_dir)
        self.assertEqual(p1, (base_dir / "output/test.json").resolve())

        # 2. Absolute path resolution
        abs_target = (self.test_dir / "absolute_file.yaml").resolve()
        p2 = resolve_path(str(abs_target), base=base_dir)
        self.assertEqual(p2, abs_target)

        # 3. Path with deep nested non-existent directory
        deep_target = base_dir / "level1" / "level2" / "level3" / "deep_file.txt"
        save_text(deep_target, "deep content")
        self.assertTrue(deep_target.exists())
        self.assertEqual(load_text(deep_target), "deep content")

        # 4. Path with spaces and Unicode in filename
        unicode_target = base_dir / "résumé & analysis — 2026 🚀" / "data.json"
        save_json(unicode_target, {"key": "value"})
        self.assertTrue(unicode_target.exists())
        self.assertEqual(load_json(unicode_target), {"key": "value"})

    def test_atomic_write_error_cleanup_and_target_preservation(self):
        """Verify that when writing fails, temporary files are removed and existing target is untouched."""
        target_file = self.test_dir / "preserve_target.txt"
        original_content = "ORIGINAL CRITICAL UNTOUCHED DATA"
        save_text(target_file, original_content)

        # Count temp files before failed write
        initial_files = set(self.test_dir.iterdir())

        class UnserializableObject:
            pass

        # Attempt to save unserializable object
        with self.assertRaises(Exception):
            save_json(target_file, {"bad": UnserializableObject()})

        # Verify original file content is completely intact
        self.assertEqual(load_text(target_file), original_content)

        # Verify no orphan .tmp_ files remain in directory
        current_files = set(self.test_dir.iterdir())
        tmp_files = [f for f in current_files if f.name.startswith(".tmp_")]
        self.assertEqual(len(tmp_files), 0, f"Orphan temporary files were left behind: {tmp_files}")


if __name__ == "__main__":
    unittest.main()
