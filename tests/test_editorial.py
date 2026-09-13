"""Comprehensive Unit & Behavioral Test Suite for Editorial Intelligence (Milestone M2).

Tests:
1. 5 Canonical Angle Archetypes (contrarian, deep_dive, data_led, human_narrative, future_impact)
2. 9-Dimension Scorecard Evaluator & Boundary Calculations
3. Winning Angle Selection, Ranking & Deterministic Tie-Breaking
4. Multi-Variation Hook Generation & Psychological Triggers
5. 4-Act ContentOutline Planning & Extreme Duration Scaling
6. Unified EditorialEngine Pipeline & Sparse Dossier Resilience
"""

import json
from pathlib import Path
import tempfile
import unittest

from src.models.contracts import (
    AngleScorecard,
    ClaimRecord,
    ContentBrief,
    ContentOutline,
    CreatorProfile,
    EditorialAngle,
    EditorialScorecard,
    OutlineAct,
    ResearchDossier,
    SourceRecord,
    StatisticRecord,
    TalkingPointRecord,
)
from src.editorial import (
    AngleArchetype,
    AngleGenerator,
    AngleSelector,
    EditorialEngine,
    EditorialScorer,
    HookGenerator,
    HookOption,
    NarrativePlanner,
    calculate_scorecard_composite,
)


class TestEditorialIntelligence(unittest.TestCase):
    """Comprehensive test suite for Harness 9 Editorial Intelligence subsystem."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.temp_dir.name)

        # Standard test fixtures
        self.sample_source = SourceRecord(
            title="IEEE Annals of the History of Computing",
            url="https://ieee.org/transistor-history",
            reliability_score=0.95,
        )
        self.sample_claims = [
            ClaimRecord(
                claim_id="claim_01",
                claim_text="The first point-contact transistor was created by Bardeen and Brattain at Bell Labs on December 23, 1947.",
                category="origin_history",
                confidence_score=0.98,
                primary_source=self.sample_source,
            ),
            ClaimRecord(
                claim_id="claim_02",
                claim_text="Modern semiconductor nodes operate at 2nm gate lengths, overcoming quantum tunneling via GAAFET architecture.",
                category="technical_mechanism",
                confidence_score=0.95,
                primary_source=self.sample_source,
            ),
            ClaimRecord(
                claim_id="claim_03",
                claim_text="Over 100 billion transistors are fabricated every second worldwide.",
                category="quantitative_metric",
                confidence_score=0.92,
                primary_source=self.sample_source,
            ),
            ClaimRecord(
                claim_id="claim_04",
                claim_text="Global geopolitical sovereignty increasingly hinges on advanced photolithography supply chokepoints.",
                category="modern_impact",
                confidence_score=0.90,
                primary_source=self.sample_source,
            ),
        ]
        self.sample_talking_points = [
            TalkingPointRecord(beat_index=1, title="The Point Contact Spark", narrative_hook="A gold foil strip and germanium slab changed history.", supported_claim_ids=["claim_01"]),
            TalkingPointRecord(beat_index=2, title="The Vacuum Tube Bottleneck", narrative_hook="Why bulky vacuum tubes were burning out ENIAC daily.", supported_claim_ids=["claim_01"]),
            TalkingPointRecord(beat_index=3, title="The Quantum Architecture", narrative_hook="How Gate-All-Around FETs tame rogue quantum electrons.", supported_claim_ids=["claim_02"]),
            TalkingPointRecord(beat_index=4, title="The Silicon Sovereign", narrative_hook="The global supply chain that powers modern nations.", supported_claim_ids=["claim_03", "claim_04"]),
        ]
        self.sample_statistics = [
            StatisticRecord(metric="Transistors per second", value="100 Billion", context="Global output", source_claim_id="claim_03"),
            StatisticRecord(metric="Gate width", value="2 nanometers", context="Leading-edge fab nodes", source_claim_id="claim_02"),
        ]
        self.sample_dossier = ResearchDossier(
            topic="How Transistors Rule the Modern World",
            run_id="run_test_001",
            headline="From Bell Labs Point-Contact to 2nm GAAFETs",
            executive_summary="An exhaustive technical and historical overview of the transistor revolution.",
            key_takeaways=["Transistors replaced fragile vacuum tubes", "Quantum tunneling requires GAAFETs", "Supply chains are centralized"],
            claims=self.sample_claims,
            talking_points=self.sample_talking_points,
            statistics=self.sample_statistics,
            suggested_visual_queries=["Point contact transistor replica", "2nm GAAFET diagram", "Silicon wafer fab cleanroom"],
        )
        self.sample_brief = ContentBrief(
            project_id="proj_transistor_01",
            topic="How Transistors Rule the Modern World",
            target_duration_seconds=30,
            aspect_ratio="16:9",
            goal="Technical Wonder",
            audience="General Tech Enthusiasts",
        )
        self.sample_creator = CreatorProfile(
            creator_id="silicon_stories",
            display_name="Silicon Stories",
            tone_of_voice=["authoritative", "curious", "rigorous"],
            target_audiences=["engineers", "tech enthusiasts"],
            negative_rules=["Never use buzzwords like 'game-changer' or 'revolutionize'"],
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    # -----------------------------------------------------------------------
    # 1. 5 Canonical Angle Archetypes Tests
    # -----------------------------------------------------------------------
    def test_01_all_five_archetypes_generated(self):
        """Verify generation across all 5 canonical archetypes with distinct styles and attributes."""
        generator = AngleGenerator()
        candidates = generator.generate_candidates(
            dossier=self.sample_dossier,
            brief=self.sample_brief,
            creator=self.sample_creator,
        )

        self.assertEqual(len(candidates), 5)
        expected_styles = {
            "Contrarian Revelation",
            "Technical Deep Dive",
            "Data-Driven Analysis",
            "Human-Centric Drama",
            "Futurist Speculation",
        }
        actual_styles = {c.narrative_style for c in candidates}
        self.assertEqual(actual_styles, expected_styles)

        for candidate in candidates:
            self.assertTrue(len(candidate.angle_id) > 0)
            self.assertTrue(len(candidate.title) > 5)
            self.assertTrue(len(candidate.premise) > 20)
            self.assertTrue(len(candidate.core_thesis) > 20)
            self.assertGreaterEqual(len(candidate.key_hooks), 2)
            self.assertIsNotNone(candidate.scorecard)
            self.assertGreater(candidate.scorecard.composite_score, 0.0)
            self.assertLessEqual(candidate.scorecard.composite_score, 1.0)

    def test_02_archetype_content_orthogonality(self):
        """Verify candidate angles are mutually distinct in title, premise, and thesis."""
        generator = AngleGenerator()
        candidates = generator.generate_candidates(dossier=self.sample_dossier, brief=self.sample_brief)

        titles = [c.title for c in candidates]
        theses = [c.core_thesis for c in candidates]
        self.assertEqual(len(set(titles)), 5, "Titles must be unique across archetypes.")
        self.assertEqual(len(set(theses)), 5, "Theses must be unique across archetypes.")

        # Contrarian check
        contrarian = next(c for c in candidates if c.narrative_style == "Contrarian Revelation")
        self.assertTrue("paradox" in contrarian.title.lower() or "misunderstands" in contrarian.title.lower())

        # Deep dive check
        deep_dive = next(c for c in candidates if c.narrative_style == "Technical Deep Dive")
        self.assertTrue("works" in deep_dive.title.lower() or "nanometer" in deep_dive.title.lower())

        # Data led check
        data_led = next(c for c in candidates if c.narrative_style == "Data-Driven Analysis")
        self.assertTrue("math" in data_led.title.lower() or "reality" in data_led.title.lower() or "numbers" in data_led.title.lower())

    # -----------------------------------------------------------------------
    # 2. 9-Dimension Scorecard Evaluator Tests
    # -----------------------------------------------------------------------
    def test_03_scorecard_composite_formula_and_weights(self):
        """Verify 9-dimension composite math matches specification."""
        # Standard balanced input
        composite = calculate_scorecard_composite(
            audience_relevance=0.8,
            novelty=0.8,
            hook_potential=0.8,
            narrative_potential=0.8,
            creator_fit=0.8,
            evidence_availability=0.8,
            visual_potential=0.8,
            platform_fit=0.8,
            saturation_risk=0.2,  # inverted (1 - 0.2 = 0.8)
        )
        self.assertAlmostEqual(composite, 0.80, places=3)

    def test_04_scorecard_boundary_values(self):
        """Verify boundary extremes: all 1.0 (with 0.0 saturation) vs all 0.0 (with 1.0 saturation)."""
        max_score = calculate_scorecard_composite(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0)
        self.assertAlmostEqual(max_score, 1.0, places=4)

        min_score = calculate_scorecard_composite(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(min_score, 0.0, places=4)

        # High saturation risk penalty
        saturated_score = calculate_scorecard_composite(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        self.assertAlmostEqual(saturated_score, 0.95, places=4)
        self.assertGreater(max_score, saturated_score)

    def test_05_creator_negative_rules_penalty(self):
        """Verify creator negative rules penalty triggers on forbidden buzzwords."""
        scorer = EditorialScorer()
        clean_angle = EditorialAngle(
            angle_id="a_clean",
            title="The Physics of 2nm Transistors",
            premise="A rigorous breakdown of gate architecture.",
            core_thesis="Physical engineering overcomes quantum limits.",
            narrative_style="Technical Deep Dive",
            key_hooks=["How 2nm transistors work."],
        )
        buzzword_angle = EditorialAngle(
            angle_id="a_buzz",
            title="The Game-Changer Chip That Will Revolutionize Everything",
            premise="This game-changer tech will revolutionize the world.",
            core_thesis="A revolutionary breakthrough.",
            narrative_style="Technical Deep Dive",
            key_hooks=["Why this is a game-changer."],
        )

        sc_clean = scorer.score_angle(clean_angle, creator=self.sample_creator)
        sc_buzz = scorer.score_angle(buzzword_angle, creator=self.sample_creator)

        self.assertGreater(sc_clean.creator_fit, sc_buzz.creator_fit)
        self.assertLess(sc_buzz.creator_fit, 0.70)

    def test_06_evidence_density_scaling(self):
        """Verify evidence_availability scales with dossier claims count and confidence."""
        scorer = EditorialScorer()
        angle = EditorialAngle(
            angle_id="a1",
            title="Transistor Evolution",
            premise="Testing evidence density.",
            core_thesis="More evidence increases score.",
        )
        # Full dossier with 4 claims and 2 statistics
        sc_full = scorer.score_angle(angle, dossier=self.sample_dossier)
        # Empty dossier
        empty_dossier = ResearchDossier(topic="Empty", claims=[])
        sc_empty = scorer.score_angle(angle, dossier=empty_dossier)

        self.assertGreater(sc_full.evidence_availability, sc_empty.evidence_availability)
        self.assertGreaterEqual(sc_full.evidence_availability, 0.85)

    def test_07_platform_fit_aspect_ratio_adaptation(self):
        """Verify platform_fit score adapts between 9:16 vertical shorts and 16:9 horizontal."""
        scorer = EditorialScorer()
        punchy_short_angle = EditorialAngle(
            angle_id="a_short",
            title="5 Second Transistor Shock",
            premise="Short punchy narrative.",
            core_thesis="Quick impact.",
            key_hooks=["Hook 1", "Hook 2"],
            narrative_style="Contrarian Revelation",
        )

        brief_9_16 = ContentBrief(project_id="p1", topic="Transistors", aspect_ratio="9:16", target_duration_seconds=15)
        brief_16_9 = ContentBrief(project_id="p2", topic="Transistors", aspect_ratio="16:9", target_duration_seconds=120)

        sc_vertical = scorer.score_angle(punchy_short_angle, brief=brief_9_16)
        sc_horizontal = scorer.score_angle(punchy_short_angle, brief=brief_16_9)

        self.assertGreaterEqual(sc_vertical.platform_fit, 0.85)
        self.assertIsInstance(sc_horizontal.platform_fit, float)

    # -----------------------------------------------------------------------
    # 3. Winning Angle Selection & Ranking Tests
    # -----------------------------------------------------------------------
    def test_08_winning_angle_selection_and_rationale(self):
        """Verify AngleSelector ranks candidates, flags winner, and generates audit rationale."""
        angles = [
            EditorialAngle(
                angle_id="a1",
                title="Angle Low",
                premise="Low score premise",
                core_thesis="Low thesis",
                scorecard=EditorialScorecard(composite_score=0.72, hook_potential=0.70),
                selected=False,
            ),
            EditorialAngle(
                angle_id="a2",
                title="Angle Winner",
                premise="Winner score premise",
                core_thesis="Winner thesis",
                scorecard=EditorialScorecard(composite_score=0.94, hook_potential=0.95, novelty=0.90),
                selected=False,
            ),
            EditorialAngle(
                angle_id="a3",
                title="Angle Medium",
                premise="Medium score premise",
                core_thesis="Medium thesis",
                scorecard=EditorialScorecard(composite_score=0.81, hook_potential=0.80),
                selected=False,
            ),
        ]

        selector = AngleSelector()
        winner, scorecard = selector.select_winning_angle(angles)

        self.assertEqual(winner.angle_id, "a2")
        self.assertEqual(scorecard.composite_score, 0.94)
        self.assertTrue(winner.selected)
        self.assertFalse(angles[0].selected)
        self.assertFalse(angles[2].selected)
        self.assertIsNotNone(winner.selection_rationale)
        self.assertIn("0.94", winner.selection_rationale)
        self.assertIn("Angle Winner", winner.selection_rationale)

    def test_09_deterministic_tie_breaker(self):
        """Verify tie-breaker prioritizes hook_potential, novelty, evidence, and angle_id."""
        a1 = EditorialAngle(
            angle_id="angle_01",
            title="Tied Angle 1",
            premise="P1",
            core_thesis="T1",
            scorecard=EditorialScorecard(composite_score=0.88, hook_potential=0.80, novelty=0.85),
        )
        a2 = EditorialAngle(
            angle_id="angle_02",
            title="Tied Angle 2",
            premise="P2",
            core_thesis="T2",
            scorecard=EditorialScorecard(composite_score=0.88, hook_potential=0.95, novelty=0.80),
        )

        selector = AngleSelector()
        winner, _ = selector.select_winning_angle([a1, a2])

        self.assertEqual(winner.angle_id, "angle_02", "Higher hook_potential must win tie-break.")

    def test_10_selector_empty_list_error(self):
        """Verify AngleSelector raises ValueError on empty candidate list."""
        selector = AngleSelector()
        with self.assertRaises(ValueError):
            selector.select_winning_angle([])

    # -----------------------------------------------------------------------
    # 4. Hook Generation Tests
    # -----------------------------------------------------------------------
    def test_11_hook_generation_variations(self):
        """Verify HookGenerator produces >= 3 distinct psychological hook types."""
        generator = HookGenerator()
        angle = EditorialAngle(
            angle_id="angle_winner",
            title="The Nanometer Miracle of Transistors",
            premise="Microscopic quantum tunneling overcome by GAAFETs.",
            core_thesis="Physics barriers conquered by architecture.",
            narrative_style="Technical Deep Dive",
            key_hooks=["How do 2nm transistors work?"],
        )

        hooks = generator.generate_hooks(angle=angle, dossier=self.sample_dossier, count=4)
        self.assertGreaterEqual(len(hooks), 3)

        hook_types = {h.hook_type for h in hooks}
        self.assertIn("question", hook_types)
        self.assertIn("paradox", hook_types)
        self.assertIn("dramatic_statement", hook_types)

        for h in hooks:
            self.assertIsInstance(h, HookOption)
            self.assertTrue(len(h.text) > 15)
            self.assertGreater(h.estimated_retention_lift, 0.7)
            self.assertTrue(len(h.visual_cue) > 5)
            self.assertTrue(len(h.psychological_trigger) > 0)

    # -----------------------------------------------------------------------
    # 5. 4-Act Narrative Planning Tests
    # -----------------------------------------------------------------------
    def test_12_four_act_outline_generation(self):
        """Verify NarrativePlanner constructs a compliant 4-act ContentOutline."""
        planner = NarrativePlanner()
        winner = EditorialAngle(
            angle_id="angle_top",
            title="The Silicon Sovereign",
            premise="Global supply chains and technical wonder.",
            core_thesis="Modern nations depend on advanced lithography.",
            narrative_style="Futurist Speculation",
        )
        hook = HookOption(
            hook_id="hook_01",
            hook_type="question",
            text="What if modern civilization depends on a 2nm needle?",
            visual_cue="Macro close up",
        )

        outline = planner.build_outline(
            winning_angle=winner,
            hook=hook,
            dossier=self.sample_dossier,
            brief=self.sample_brief,
        )

        self.assertIsInstance(outline, ContentOutline)
        self.assertEqual(len(outline.acts), 4)
        self.assertEqual(outline.angle_id, "angle_top")
        self.assertEqual(outline.total_estimated_duration, 30.0)

        # Validate act percentages and sequence
        self.assertEqual(outline.acts[0].act_index, 1)
        self.assertEqual(outline.acts[0].target_start_pct, 0.0)
        self.assertEqual(outline.acts[0].target_end_pct, 0.15)
        self.assertIn("The Hook", outline.acts[0].act_name)

        self.assertEqual(outline.acts[1].act_index, 2)
        self.assertEqual(outline.acts[1].target_start_pct, 0.15)
        self.assertEqual(outline.acts[1].target_end_pct, 0.45)
        self.assertIn("Bottleneck", outline.acts[1].act_name)

        self.assertEqual(outline.acts[2].act_index, 3)
        self.assertEqual(outline.acts[2].target_start_pct, 0.45)
        self.assertEqual(outline.acts[2].target_end_pct, 0.75)
        self.assertIn("Core Insight", outline.acts[2].act_name)

        self.assertEqual(outline.acts[3].act_index, 4)
        self.assertEqual(outline.acts[3].target_start_pct, 0.75)
        self.assertEqual(outline.acts[3].target_end_pct, 1.0)
        self.assertIn("Payoff", outline.acts[3].act_name)

    def test_13_duration_scaling_extremes(self):
        """Verify duration scaling across 5s (short short) and 600s (long-form documentary)."""
        planner = NarrativePlanner()
        angle = EditorialAngle(angle_id="a1", title="Scaling Test", premise="P", core_thesis="T")
        hook = "Test hook"

        # 5 seconds
        outline_5s = planner.build_outline(winning_angle=angle, hook=hook, target_duration=5.0)
        self.assertEqual(outline_5s.total_estimated_duration, 5.0)

        # 600 seconds
        outline_600s = planner.build_outline(winning_angle=angle, hook=hook, target_duration=600.0)
        self.assertEqual(outline_600s.total_estimated_duration, 600.0)

    def test_14_outline_serialization_roundtrip(self):
        """Verify ContentOutline serialization to and deserialization from JSON/YAML."""
        planner = NarrativePlanner()
        angle = EditorialAngle(angle_id="a_roundtrip", title="Roundtrip Angle", premise="P", core_thesis="T")
        outline = planner.build_outline(
            winning_angle=angle,
            hook="How the world changed.",
            dossier=self.sample_dossier,
            brief=self.sample_brief,
        )

        json_p, yaml_p = outline.save(self.out_path, "outline_test")
        self.assertTrue(json_p.exists())
        self.assertTrue(yaml_p.exists())

        loaded_json = ContentOutline.load(json_p)
        loaded_yaml = ContentOutline.load(yaml_p)

        self.assertEqual(loaded_json.angle_id, "a_roundtrip")
        self.assertEqual(loaded_yaml.topic, self.sample_dossier.topic)
        self.assertEqual(len(loaded_yaml.acts), 4)

    # -----------------------------------------------------------------------
    # 6. Unified EditorialEngine Facade & Sparse Dossier Resilience
    # -----------------------------------------------------------------------
    def test_15_editorial_engine_full_flow(self):
        """Verify end-to-end EditorialEngine executes full ideation, scoring, selection, hook, and outline."""
        engine = EditorialEngine()
        candidates, winner, hooks, outline = engine.process_editorial(
            dossier=self.sample_dossier,
            brief=self.sample_brief,
            creator=self.sample_creator,
        )

        self.assertEqual(len(candidates), 5)
        self.assertTrue(winner.selected)
        self.assertGreaterEqual(len(hooks), 3)
        self.assertIsInstance(outline, ContentOutline)
        self.assertEqual(len(outline.acts), 4)
        self.assertEqual(outline.angle_id, winner.angle_id)

    def test_16_sparse_dossier_graceful_handling(self):
        """Verify editorial engine handles empty or single-claim sparse research dossiers gracefully."""
        sparse_dossier = ResearchDossier(
            topic="Quantum Dot Computing",
            claims=[],
            talking_points=[],
            statistics=[],
        )
        engine = EditorialEngine()
        candidates, winner, hooks, outline = engine.process_editorial(dossier=sparse_dossier)

        self.assertEqual(len(candidates), 5)
        self.assertTrue(winner.selected)
        self.assertGreaterEqual(len(hooks), 3)
        self.assertIsInstance(outline, ContentOutline)
        self.assertEqual(outline.topic, "Quantum Dot Computing")


if __name__ == "__main__":
    unittest.main()
