"""Unit & Integration Tests for Creator Economics Engine (Milestone M5).

Tests:
1. RateTable pricing defaults, per-model overrides, and custom rates.
2. UsageEvent and CostItem data structures across all 5 cost categories.
3. ProductionCostLedger calculation, cost-per-second, margin analysis, and zero-division protection.
4. CreatorEconomicsEngine multi-stage usage recording and ledger generation.
5. Budget compliance evaluation and serialization.
"""

import math
import shutil
import tempfile
import unittest

from src.creator.economics import (
    CostCategory,
    CostItem,
    CreatorEconomicsEngine,
    ProductionCostLedger,
    RateTable,
    UnitType,
    UsageEvent,
)


class TestCreatorEconomics(unittest.TestCase):
    """Test suite verifying Creator Economics ledger and unit cost calculation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = CreatorEconomicsEngine()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 1. RateTable Tests
    # -----------------------------------------------------------------------
    def test_rate_table_defaults_and_model_overrides(self):
        rates = RateTable()
        # Default rates
        self.assertAlmostEqual(rates.llm_prompt_rate_per_1k, 0.0025)
        self.assertAlmostEqual(rates.llm_completion_rate_per_1k, 0.0100)
        self.assertAlmostEqual(rates.research_query_rate_usd, 0.0050)
        self.assertAlmostEqual(rates.tts_char_rate_usd, 0.00003)

        # Per-token rates
        prompt_rate = rates.get_llm_rate("gpt-4o", "prompt")
        self.assertAlmostEqual(prompt_rate, 0.0025 / 1000.0)

        claude_comp_rate = rates.get_llm_rate("claude-3-5-sonnet", "completion")
        self.assertAlmostEqual(claude_comp_rate, 0.0150 / 1000.0)

        # Free tier TTS
        sapi_rate = rates.get_tts_rate("sapi")
        self.assertEqual(sapi_rate, 0.0)
        harmonic_rate = rates.get_tts_rate("harmonic")
        self.assertEqual(harmonic_rate, 0.0)

        # ElevenLabs TTS
        eleven_rate = rates.get_tts_rate("elevenlabs")
        self.assertEqual(eleven_rate, 0.00003)

    # -----------------------------------------------------------------------
    # 2. ProductionCostLedger Itemized Calculation Tests
    # -----------------------------------------------------------------------
    def test_production_cost_ledger_aggregation(self):
        items = [
            CostItem(
                category=CostCategory.LLM.value,
                item_name="LLM Prompt Tokens",
                units_consumed=12400,
                unit_type=UnitType.TOKENS.value,
                unit_rate_usd=0.0025 / 1000.0,
                total_cost_usd=0.0310,
            ),
            CostItem(
                category=CostCategory.LLM.value,
                item_name="LLM Completion Tokens",
                units_consumed=3800,
                unit_type=UnitType.TOKENS.value,
                unit_rate_usd=0.0100 / 1000.0,
                total_cost_usd=0.0380,
            ),
            CostItem(
                category=CostCategory.RESEARCH.value,
                item_name="Search Queries",
                units_consumed=6,
                unit_type=UnitType.QUERIES.value,
                unit_rate_usd=0.0050,
                total_cost_usd=0.0300,
            ),
            CostItem(
                category=CostCategory.TTS.value,
                item_name="TTS Audio Synthesis",
                units_consumed=1840,
                unit_type=UnitType.CHARACTERS.value,
                unit_rate_usd=0.00003,
                total_cost_usd=0.0552,
            ),
            CostItem(
                category=CostCategory.RENDER.value,
                item_name="Render GPU Compute",
                units_consumed=18.25,
                unit_type=UnitType.SECONDS.value,
                unit_rate_usd=0.0004,
                total_cost_usd=0.0073,
            ),
            CostItem(
                category=CostCategory.STORAGE.value,
                item_name="Asset Media Storage",
                units_consumed=48.0,
                unit_type=UnitType.MEGABYTES.value,
                unit_rate_usd=0.0200 / 1024.0,
                total_cost_usd=0.000938,
            ),
        ]

        ledger = ProductionCostLedger(
            run_id="run_test_01",
            project_id="proj_harness9",
            items=items,
            video_duration_seconds=30.0,
            target_cpm_usd=5.0,
            projected_views=1000,
        )

        self.assertAlmostEqual(ledger.total_cost_usd, 0.162438, places=4)
        self.assertAlmostEqual(ledger.cost_per_video_second, 0.162438 / 30.0, places=4)
        self.assertEqual(ledger.estimated_revenue_usd, 5.0)
        self.assertGreater(ledger.estimated_margin_percent, 90.0)

        # Summary by category
        cat_summary = ledger.summary_by_category()
        self.assertEqual(len(cat_summary), 5)
        self.assertAlmostEqual(cat_summary[CostCategory.LLM.value], 0.069, places=3)
        self.assertAlmostEqual(cat_summary[CostCategory.TTS.value], 0.0552, places=4)

    def test_zero_duration_and_zero_revenue_protection(self):
        """Verify boundary condition for zero duration or zero views."""
        ledger = ProductionCostLedger(
            run_id="run_zero",
            items=[
                CostItem(
                    category=CostCategory.LLM.value,
                    item_name="LLM Test",
                    units_consumed=1000,
                    unit_type=UnitType.TOKENS.value,
                    unit_rate_usd=0.001,
                    total_cost_usd=1.0,
                )
            ],
            video_duration_seconds=0.0,
            projected_views=0,
        )

        self.assertEqual(ledger.cost_per_video_second, 0.0)
        self.assertFalse(math.isinf(ledger.cost_per_video_second))
        self.assertEqual(ledger.estimated_margin_percent, 0.0)
        self.assertFalse(math.isnan(ledger.estimated_margin_percent))

    # -----------------------------------------------------------------------
    # 3. CreatorEconomicsEngine End-to-End Tests
    # -----------------------------------------------------------------------
    def test_engine_record_usage_and_calculate_ledger(self):
        engine = CreatorEconomicsEngine()

        # Record pipeline stages
        engine.record_llm_usage(prompt_tokens=10000, completion_tokens=2500, cached_tokens=5000, model="gpt-4o")
        engine.record_research_usage(queries_count=4, provider="tavily")
        engine.record_tts_usage(character_count=1200, provider="elevenlabs")
        engine.record_render_usage(render_duration_sec=15.0, gpu_accelerated=True)
        engine.record_storage_usage(storage_mb=35.0)

        ledger = engine.calculate_production_cost(
            session_id="sess_econ_01",
            video_duration_seconds=30.0,
            target_cpm=6.0,
            projected_views=2000,
        )

        self.assertGreater(ledger.total_cost_usd, 0.0)
        self.assertLess(ledger.total_cost_usd, 0.50)
        self.assertEqual(len(ledger.items), 7)  # prompt, comp, cache, query, tts, render, storage
        self.assertEqual(ledger.estimated_revenue_usd, 12.0)
        self.assertGreater(ledger.estimated_margin_percent, 90.0)

        # Verify markdown export
        md = ledger.to_markdown_table()
        self.assertIn("Production Cost Ledger", md)
        self.assertIn("TOTAL", md)
        self.assertIn("LLM Prompt Tokens", md)

    def test_budget_compliance_estimation(self):
        engine = CreatorEconomicsEngine()
        engine.record_llm_usage(prompt_tokens=5000, completion_tokens=1000)
        engine.record_tts_usage(character_count=800)

        ledger = engine.calculate_production_cost(session_id="sess_budg", video_duration_seconds=30.0)
        comp = engine.estimate_budget_compliance(ledger, max_budget_usd=0.50)

        self.assertTrue(comp["compliant"])
        self.assertGreater(comp["headroom_usd"], 0.40)
        self.assertLess(comp["percent_budget_used"], 20.0)

    def test_ledger_json_and_yaml_serialization(self):
        engine = CreatorEconomicsEngine()
        engine.record_llm_usage(prompt_tokens=1000, completion_tokens=500)
        ledger = engine.calculate_production_cost(session_id="sess_ser")

        json_path, yaml_path = ledger.save(self.temp_dir, base_name="cost_ledger")
        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        loaded_json = ProductionCostLedger.load(json_path)
        self.assertEqual(loaded_json.run_id, "sess_ser")
        self.assertAlmostEqual(loaded_json.total_cost_usd, ledger.total_cost_usd)

        loaded_yaml = ProductionCostLedger.load(yaml_path)
        self.assertEqual(loaded_yaml.run_id, "sess_ser")
        self.assertAlmostEqual(loaded_yaml.total_cost_usd, ledger.total_cost_usd)

    # -----------------------------------------------------------------------
    # 4. Boundary & Edge Case Tests
    # -----------------------------------------------------------------------
    def test_negative_margin_calculation(self):
        """Verify negative margins when production costs exceed revenue."""
        ledger = ProductionCostLedger(
            run_id="run_negative_margin",
            items=[
                CostItem(
                    category=CostCategory.LLM.value,
                    item_name="Heavy Compute",
                    units_consumed=1,
                    unit_type="job",
                    unit_rate_usd=25.0,
                    total_cost_usd=25.0,
                )
            ],
            video_duration_seconds=60.0,
            target_cpm_usd=10.0,
            projected_views=1000,  # $10 revenue
        )
        # Cost $25, Revenue $10 -> Margin = ((10 - 25) / 10) * 100 = -150%
        self.assertEqual(ledger.estimated_revenue_usd, 10.0)
        self.assertEqual(ledger.total_cost_usd, 25.0)
        self.assertEqual(ledger.estimated_margin_percent, -150.0)

    def test_extreme_token_counts(self):
        """Verify large-scale token volume pricing."""
        engine = CreatorEconomicsEngine()
        engine.record_llm_usage(
            prompt_tokens=2_500_000,
            completion_tokens=500_000,
            cached_tokens=1_000_000,
            model="gpt-4o",
        )
        ledger = engine.calculate_production_cost(session_id="sess_large", video_duration_seconds=600.0)
        # Expected:
        # Prompt: 2,500 * $0.0025 = $6.25
        # Comp: 500 * $0.0100 = $5.00
        # Cache: 1,000 * $0.00125 = $1.25
        # Total = $12.50
        self.assertAlmostEqual(ledger.total_cost_usd, 12.50, places=2)
        self.assertAlmostEqual(ledger.cost_per_video_second, 12.50 / 600.0, places=4)

    def test_empty_events_list_ledger(self):
        """Verify empty events produce clean zero ledger."""
        engine = CreatorEconomicsEngine()
        ledger = engine.calculate_production_cost(session_id="sess_empty", events=[])
        self.assertEqual(ledger.total_cost_usd, 0.0)
        self.assertEqual(ledger.cost_per_video_second, 0.0)
        self.assertEqual(len(ledger.items), 0)


if __name__ == "__main__":
    unittest.main()
