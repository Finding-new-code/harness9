"""Unit & Integration Tests for Creator DNA & Memory Engine (Milestone M5).

Tests:
1. BrandConstitution, CreatorPreferences, CreatorSkills, CreatorExamples.
2. RetentionCurve, RetentionCurvePoint, AVD calculation, and drop-off analysis.
3. NegativeMemory, mistake logging, negative prompt directives, and violation detection.
4. CreatorDNA data model, profile conversions, system prompt builder, and content validation.
5. CreatorDNAStore disk persistence, in-memory caching, and memory update lifecycle.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.creator.dna import (
    BrandConstitution,
    CreatorDNA,
    CreatorDNAStore,
    CreatorExample,
    CreatorExamples,
    CreatorPreferences,
    CreatorSkills,
)
from src.creator.memory import (
    LearnedPattern,
    NegativeConstraint,
    NegativeMemory,
    NegativeMistakeRecord,
    PerformanceMemory,
    RetentionCurve,
    RetentionCurvePoint,
)
from src.models.contracts import CreatorProfile, LearningCandidate


class TestCreatorDNAAndMemory(unittest.TestCase):
    """Test suite verifying Creator DNA, Performance Retention, and Negative Memory."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 1. Brand Constitution & Preferences Tests
    # -----------------------------------------------------------------------
    def test_brand_constitution_defaults_and_validation(self):
        brand = BrandConstitution()
        self.assertIn("authoritative", brand.tone_of_voice)
        self.assertIn("game-changer", brand.prohibited_words)
        self.assertIn("revolutionize", brand.prohibited_words)
        self.assertGreater(len(brand.non_negotiable_guardrails), 0)
        self.assertEqual(brand.target_audience_level, "intermediate")

    def test_creator_preferences_defaults_and_style_tokens(self):
        prefs = CreatorPreferences(
            preferred_wpm=150,
            primary_color="#00ffcc",
            aspect_ratio="9:16",
        )
        self.assertEqual(prefs.preferred_wpm, 150)
        self.assertEqual(prefs.primary_color, "#00ffcc")
        self.assertEqual(prefs.aspect_ratio, "9:16")
        self.assertEqual(prefs.easing_function, "power2.out")

    def test_creator_skills_and_examples(self):
        skills = CreatorSkills(
            domain_specializations=["Quantum Computing", "Superconductors"],
            technical_lexicon={"Qubit": "Quantum Bit"},
        )
        self.assertEqual(len(skills.domain_specializations), 2)
        self.assertEqual(skills.technical_lexicon["Qubit"], "Quantum Bit")

        examples = CreatorExamples()
        hooks = examples.get_examples_by_category("hook")
        self.assertGreaterEqual(len(hooks), 2)
        prompt_snippet = examples.get_few_shot_prompt("hook", limit=2)
        self.assertIn("Exemplary Hook Examples", prompt_snippet)
        self.assertIn("Bell Labs", prompt_snippet)

    # -----------------------------------------------------------------------
    # 2. Performance Retention Curve Tests
    # -----------------------------------------------------------------------
    def test_retention_curve_metrics_calculation(self):
        points = [
            RetentionCurvePoint(timestamp_sec=0.0, retention_pct=100.0),
            RetentionCurvePoint(timestamp_sec=5.0, retention_pct=85.0),
            RetentionCurvePoint(timestamp_sec=15.0, retention_pct=70.0),
            RetentionCurvePoint(timestamp_sec=30.0, retention_pct=60.0),
        ]
        curve = RetentionCurve(
            project_id="test_proj_01",
            duration_seconds=30.0,
            points=points,
        )

        self.assertEqual(curve.initial_5s_retention_pct, 85.0)
        self.assertEqual(curve.completion_rate_pct, 60.0)
        self.assertGreater(curve.average_view_duration_sec, 20.0)
        self.assertLessEqual(curve.average_view_duration_sec, 30.0)

        # Test linear interpolation
        ret_at_10 = curve.retention_at(10.0)
        self.assertAlmostEqual(ret_at_10, 77.5, places=1)
        self.assertEqual(curve.retention_at(0.0), 100.0)
        self.assertEqual(curve.retention_at(30.0), 60.0)
        self.assertEqual(curve.retention_at(50.0), 60.0)

    def test_retention_curve_drop_off_detection(self):
        points = [
            RetentionCurvePoint(timestamp_sec=0.0, retention_pct=100.0),
            RetentionCurvePoint(timestamp_sec=5.0, retention_pct=95.0),
            RetentionCurvePoint(timestamp_sec=10.0, retention_pct=65.0),  # 30% drop
            RetentionCurvePoint(timestamp_sec=30.0, retention_pct=60.0),
        ]
        curve = RetentionCurve(
            project_id="test_drop",
            duration_seconds=30.0,
            points=points,
        )
        drops = curve.find_drop_off_points(threshold_pct_drop=15.0)
        self.assertEqual(len(drops), 1)
        self.assertEqual(drops[0]["start_time_sec"], 5.0)
        self.assertEqual(drops[0]["end_time_sec"], 10.0)
        self.assertEqual(drops[0]["drop_pct"], 30.0)
        self.assertEqual(drops[0]["severity"], "critical" if drops[0]["drop_pct"] >= 20.0 else "medium")

    def test_performance_memory_aggregation(self):
        mem = PerformanceMemory()
        c1 = RetentionCurve(
            project_id="p1",
            duration_seconds=30.0,
            points=[
                RetentionCurvePoint(timestamp_sec=0.0, retention_pct=100.0),
                RetentionCurvePoint(timestamp_sec=30.0, retention_pct=80.0),
            ],
        )
        c2 = RetentionCurve(
            project_id="p2",
            duration_seconds=30.0,
            points=[
                RetentionCurvePoint(timestamp_sec=0.0, retention_pct=100.0),
                RetentionCurvePoint(timestamp_sec=30.0, retention_pct=60.0),
            ],
        )
        mem.add_retention_curve(c1)
        mem.add_retention_curve(c2)

        self.assertEqual(len(mem.retention_curves), 2)
        self.assertEqual(mem.average_retention_overall, 70.0)

        pat = LearnedPattern(
            pattern_id="pat_01",
            category="hook_structure",
            description="Opening with historical year increases 5s retention",
            positive_correlation="+18% watch rate",
            confidence_score=0.92,
        )
        mem.add_pattern(pat)
        learnings = mem.get_top_learnings(min_confidence=0.8)
        self.assertEqual(len(learnings), 1)
        self.assertIn("HOOK_STRUCTURE", learnings[0])

    # -----------------------------------------------------------------------
    # 3. Negative Memory & Constraint Enforcement Tests
    # -----------------------------------------------------------------------
    def test_negative_memory_violations_detection(self):
        neg = NegativeMemory()
        script_text = "This game-changer discovery will revolutionize modern computing."
        violations = neg.check_violations(script_text)

        self.assertEqual(len(violations), 2)
        patterns = [v["pattern"] for v in violations]
        self.assertIn("game-changer", patterns)
        self.assertIn("revolutionize", patterns)

    def test_negative_memory_mistake_recording_and_directives(self):
        neg = NegativeMemory()
        mistake = NegativeMistakeRecord(
            mistake_id="mistake_101",
            project_id="run_05",
            category="script",
            pattern_or_phrase="overly abstract mathematical derivations without visual analogies",
            failure_reason="Audience retention collapsed in Act 2",
            severity="critical",
        )
        neg.record_mistake(mistake)

        self.assertEqual(len(neg.mistake_log), 1)
        self.assertEqual(len(neg.active_constraints), 1)

        directives = neg.generate_negative_prompt_directives()
        self.assertGreaterEqual(len(directives), 3)
        found_mistake_directive = any("overly abstract mathematical derivations" in d for d in directives)
        self.assertTrue(found_mistake_directive)

        candidates = neg.extract_learning_candidates(creator_id="test_creator")
        self.assertEqual(len(candidates), 1)
        self.assertIsInstance(candidates[0], LearningCandidate)
        self.assertEqual(candidates[0].creator_id, "test_creator")
        self.assertGreaterEqual(candidates[0].confidence, 0.8)

    # -----------------------------------------------------------------------
    # 4. Creator DNA Master Model Tests
    # -----------------------------------------------------------------------
    def test_creator_dna_full_model_and_validation(self):
        dna = CreatorDNA(
            creator_id="deep_tech_creator",
            display_name="Deep Tech Explained",
        )
        dna.brand_constitution.prohibited_words.append("mind-boggling")

        # Clean text
        clean_text = "In 1958, Jack Kilby constructed the first integrated circuit using germanium."
        res_clean = dna.validate_content(clean_text)
        self.assertTrue(res_clean["valid"])
        self.assertEqual(res_clean["violations_count"], 0)
        self.assertGreater(res_clean["word_count"], 5)

        # Violating text
        bad_text = "This mind-boggling game-changer will revolutionize everything."
        res_bad = dna.validate_content(bad_text)
        self.assertFalse(res_bad["valid"])
        self.assertGreaterEqual(res_bad["violations_count"], 3)

    def test_creator_dna_to_and_from_profile_contract(self):
        dna = CreatorDNA(
            creator_id="creator_abc",
            display_name="ABC Science",
        )
        profile = dna.to_creator_profile()
        self.assertIsInstance(profile, CreatorProfile)
        self.assertEqual(profile.creator_id, "creator_abc")
        self.assertEqual(profile.display_name, "ABC Science")
        self.assertIn("primary", profile.brand_colors)

        # Convert back
        dna_reconstructed = CreatorDNA.from_creator_profile(profile)
        self.assertEqual(dna_reconstructed.creator_id, "creator_abc")
        self.assertEqual(dna_reconstructed.display_name, "ABC Science")

    def test_system_prompt_builder(self):
        dna = CreatorDNA(
            creator_id="host_01",
            display_name="Tech Frontier",
        )
        prompt_context = dna.build_system_prompt_context(stage_name="scriptwriting")
        self.assertIn("CREATOR BRAND DNA: TECH FRONTIER", prompt_context)
        self.assertIn("STRICT NEGATIVE CONSTRAINTS", prompt_context)
        self.assertIn("Target Cadence", prompt_context)

    # -----------------------------------------------------------------------
    # 5. CreatorDNAStore Persistence & Memory Lifecycle Tests
    # -----------------------------------------------------------------------
    def test_creator_dna_store_lifecycle(self):
        store = CreatorDNAStore(storage_dir=self.temp_dir)
        default_dna = store.get_creator_dna("harness9_creator")
        self.assertIsNotNone(default_dna)
        self.assertEqual(default_dna.creator_id, "harness9_creator")

        # Create new creator DNA and save
        new_dna = CreatorDNA(
            creator_id="quantum_host",
            display_name="Quantum Host",
        )
        new_dna.preferences.preferred_wpm = 160
        paths = store.save_creator_dna(new_dna)
        self.assertIsNotNone(paths)
        json_path, yaml_path = paths
        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        # List creators
        creators = store.list_creators()
        self.assertIn("quantum_host", creators)
        self.assertIn("harness9_creator", creators)

        # Reload from fresh store instance
        store2 = CreatorDNAStore(storage_dir=self.temp_dir)
        loaded_dna = store2.get_creator_dna("quantum_host")
        self.assertEqual(loaded_dna.preferences.preferred_wpm, 160)

        # Apply memory feedback update
        store2.update_memory(
            creator_id="quantum_host",
            feedback={
                "project_id": "proj_99",
                "duration_seconds": 30.0,
                "retention_points": [
                    {"timestamp_sec": 0.0, "retention_pct": 100.0},
                    {"timestamp_sec": 30.0, "retention_pct": 75.0},
                ],
                "forbidden_word": "miraculous",
            },
        )
        updated = store2.get_creator_dna("quantum_host")
        self.assertEqual(len(updated.performance_memory.retention_curves), 1)
        self.assertIn("miraculous", updated.negative_memory.forbidden_words)

        # Delete creator
        deleted = store2.delete_creator("quantum_host")
        self.assertTrue(deleted)
        self.assertNotIn("quantum_host", store2.list_creators())

    # -----------------------------------------------------------------------
    # 6. Boundary & Edge Case Tests
    # -----------------------------------------------------------------------
    def test_large_retention_curve_trapezoidal_integration(self):
        """Verify trapezoidal integration over 100 dense time points."""
        points = [
            RetentionCurvePoint(timestamp_sec=float(t), retention_pct=max(10.0, 100.0 - 0.8 * t))
            for t in range(101)
        ]
        curve = RetentionCurve(project_id="dense_curve", duration_seconds=100.0, points=points)
        self.assertGreater(curve.average_view_duration_sec, 50.0)
        self.assertLessEqual(curve.average_view_duration_sec, 100.0)
        self.assertEqual(curve.retention_at(50.0), 60.0)

    def test_negative_memory_punctuation_and_casing_variations(self):
        """Verify regex boundary matches across diverse punctuation styles."""
        neg = NegativeMemory()
        neg.add_forbidden_word("game-changer")
        neg.add_forbidden_word("revolutionize")

        sample_texts = [
            "This is a true Game-Changer!",
            "Will it REVOLUTIONIZE the sector?",
            "It is a (game-changer) for all.",
        ]
        for t in sample_texts:
            violations = neg.check_violations(t)
            self.assertGreaterEqual(len(violations), 1)

    def test_creator_dna_store_corrupt_file_recovery(self):
        """Verify store gracefully handles invalid file on disk."""
        store = CreatorDNAStore(storage_dir=self.temp_dir)
        corrupt_file = Path(self.temp_dir) / "broken_creator.json"
        corrupt_file.write_text("{invalid_json: true", encoding="utf-8")

        # Loading corrupt file falls back gracefully
        dna = store.get_creator_dna("broken_creator")
        self.assertEqual(dna.creator_id, "broken_creator")


if __name__ == "__main__":
    unittest.main()
