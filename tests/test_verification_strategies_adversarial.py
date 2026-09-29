"""tests/test_verification_strategies_adversarial.py — Adversarial Stress Suite for Epistemic Verification Strategies.

Empirical verification suite challenging:
1. Quote Verification: exact matching, smart quotes, single curly quotes, whitespace normalization,
   unicode ellipses, reordered/fabricated ellipsis injections, missing archive fallback vulnerability, paraphrase mandate.
2. Numerical Verification: order-of-magnitude traps (10x, 100x, 1000x, zero handling), dual tolerance boundaries
   (0.1% vs 5.0%), year-prefix collision extraction flaw, negative numbers, unit conversion absence.
3. Temporal Verification: historical anachronism registry, explicit year bypass flaw, metaphor false positives,
   chronological precedence inversion, hardcoded freshness expiration date flaw.
4. Contradiction Verification: polar negations, non-averaging invariant, numerical averaging detection & string bypass,
   hardcoded cross-claim contradiction limitations.
5. Entailment & Corroboration: modal strengthening penalties, wire syndication collapse, root domain deduplication.
"""

import math
import unittest

from src.epistemic.engine import (
    DossierVerificationReport,
    VerificationEngine,
    VerificationResult,
)
from src.epistemic.graph import (
    EdgeRelation,
    EvidenceGraph,
)
from src.epistemic.historical_policy import (
    ContradictionRecord,
    HistoricalPolicyChecker,
    HistoriographicalViolationType,
)
from src.epistemic.strategies import (
    ContradictionCheckStrategy,
    CrossSourceCorroborationStrategy,
    HistoriographicalCheckStrategy,
    NumericalCheckStrategy,
    QuoteCheckStrategy,
    SourceEntailmentStrategy,
    StrategyExecutionResult,
    TemporalCheckStrategy,
)
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    EvidenceUnitLink,
    QuoteExactness,
    ResearchDossier,
    SourceRecord,
    SourceTier,
    TemporalContext,
)


class TestAdversarialQuoteVerification(unittest.TestCase):
    """Adversarial challenge tests for QuoteCheckStrategy and quote verification policies."""

    def setUp(self):
        self.strategy = QuoteCheckStrategy()
        self.graph = EvidenceGraph(graph_id="test_quote_graph")
        self.engine = VerificationEngine()

    def test_quote_exact_match_ascii_and_smart_double_quotes(self):
        """Tests that standard ASCII and typographical smart double quotes match exact archive text."""
        archive = "The only thing we have to fear is fear itself."

        # ASCII double quotes
        c_ascii = ClaimRecord(
            claim_id="q_ascii",
            claim_text='Roosevelt asserted "The only thing we have to fear is fear itself."',
            claim_type=ClaimType.DIRECT_QUOTE,
            primary_source=SourceRecord(title="Inaugural", url="https://archives.gov", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"archive_quote": archive},
        )
        res_ascii = self.strategy.evaluate(c_ascii, self.graph)
        self.assertTrue(res_ascii.passed)
        self.assertEqual(res_ascii.quote_exactness, QuoteExactness.EXACT)

        # Smart/curly double quotes
        c_smart = ClaimRecord(
            claim_id="q_smart",
            claim_text='Roosevelt asserted “The only thing we have to fear is fear itself.”',
            claim_type=ClaimType.DIRECT_QUOTE,
            primary_source=SourceRecord(title="Inaugural", url="https://archives.gov", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"archive_quote": archive},
        )
        res_smart = self.strategy.evaluate(c_smart, self.graph)
        self.assertTrue(res_smart.passed)
        self.assertEqual(res_smart.quote_exactness, QuoteExactness.EXACT)

    def test_quote_single_smart_curly_quotes_extraction_blindspot(self):
        """Demonstrates that single smart curly quotes (‘...’) are NOT extracted by _extract_quoted_substring.

        Because the regex patterns only include ASCII single quote '([^']+)' and double quotes,
        single curly quotes are not captured, causing the full claim text to be treated as the quote.
        """
        archive = "I think, therefore I am."
        c_single_curly = ClaimRecord(
            claim_id="q_single_curly",
            claim_text="Descartes wrote ‘I think, therefore I am.’ in his treatise.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=SourceRecord(title="Discourse", url="https://arch.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"archive_quote": archive},
        )
        # In _extract_quoted_substring: ‘...’ is not in patterns, returns None
        extracted = self.strategy._extract_quoted_substring(c_single_curly.claim_text)
        self.assertIsNone(
            extracted,
            "Vulnerability: _extract_quoted_substring fails to extract single smart quotes (\u2018...\u2019)",
        )
        # Because claim_type is EVENT_FACT and extracted is None, QuoteCheck returns NOT_APPLICABLE
        res = self.strategy.evaluate(c_single_curly, self.graph)
        self.assertEqual(res.quote_exactness, QuoteExactness.NOT_APPLICABLE)

    def test_quote_whitespace_normalization(self):
        """Verifies that multiple spaces, tabs, and newlines are collapsed during normalization."""
        archive = "Knowledge is power."
        c_whitespace = ClaimRecord(
            claim_id="q_ws",
            claim_text='Bacon noted "Knowledge   is \t \n power."',
            claim_type=ClaimType.DIRECT_QUOTE,
            primary_source=SourceRecord(title="Meditationes", url="https://arch.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"archive_quote": archive},
        )
        res = self.strategy.evaluate(c_whitespace, self.graph)
        self.assertTrue(res.passed)
        self.assertEqual(res.quote_exactness, QuoteExactness.EXACT)

    def test_quote_unicode_ellipsis_insertion_fails_exactness(self):
        """Demonstrates that typographical unicode ellipsis character ('…', U+2026) is not recognized as an ellipsis.

        QuoteCheckStrategy checks: '"..." in asserted_quote or "[...]" in asserted_quote'.
        It does not check or normalize '…'. Consequently, a quote using '…' is evaluated as a normal string,
        and because words were omitted, D_norm > 0.02, triggering a false QUOTE_FABRICATION_DETECTED warning.
        """
        archive = "Government of the people, by the people, for the people, shall not perish from the earth."
        # Using unicode ellipsis '…'
        c_unicode_ellipses = ClaimRecord(
            claim_id="q_u_ellipses",
            claim_text='Lincoln stated "Government of the people … shall not perish from the earth."',
            claim_type=ClaimType.DIRECT_QUOTE,
            primary_source=SourceRecord(title="Gettysburg Address", url="https://archives.gov", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"archive_quote": archive},
        )
        res = self.strategy.evaluate(c_unicode_ellipses, self.graph)
        # Empirically proves the bug: exactness becomes DISTORTED rather than ELLIPSES
        self.assertEqual(res.quote_exactness, QuoteExactness.DISTORTED)
        self.assertFalse(res.passed)
        self.assertIn("QUOTE_FABRICATION_DETECTED", res.flags)

    def test_quote_ellipsis_fabricated_text_pass_vulnerability(self):
        """Demonstrates vulnerability where fabricated text passes if '...' is present and D_norm <= 0.35.

        In QuoteCheckStrategy: 'if all_parts_match or d_norm <= 0.35: exactness = QuoteExactness.ELLIPSES; passed = True'
        If a user fabricates words into a quote and adds '...', as long as edit distance <= 35%, it incorrectly passes!
        """
        archive = "Ask not what your country can do for you, ask what you can do for your country."
        # Fabricate: replace 'country' with 'government and society' (altered text) plus '...'
        c_altered = ClaimRecord(
            claim_id="q_altered_ellipses",
            claim_text='Kennedy said "Ask not what your government can do for you ... ask what you can do for your country."',
            claim_type=ClaimType.DIRECT_QUOTE,
            primary_source=SourceRecord(title="Inaugural", url="https://jfklibrary.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"archive_quote": archive},
        )
        # 'government' was NOT in archive, so all_parts_match is False. But D_norm is ~0.10 <= 0.35!
        res = self.strategy.evaluate(c_altered, self.graph)
        # It passes as ELLIPSES despite fabricated words inside the quote!
        self.assertTrue(
            res.passed,
            "Vulnerability confirmed: quote with fabricated substitution passed as ELLIPSES due to 'or d_norm <= 0.35' bypass.",
        )
        self.assertEqual(res.quote_exactness, QuoteExactness.ELLIPSES)

    def test_quote_missing_archive_quote_fallback_vulnerability(self):
        """Demonstrates critical vulnerability: if no archive_quote is provided in metadata,

        the strategy defaults archive_quote = asserted_quote, validating 100% fabricated quotes as EXACT!
        """
        c_pure_fiction = ClaimRecord(
            claim_id="q_fiction",
            claim_text='Albert Einstein famously declared "Always believe quotes you read on the internet, for they are true."',
            claim_type=ClaimType.DIRECT_QUOTE,
            primary_source=SourceRecord(title="Shady Website", url="https://fake.example.com", tier=SourceTier.UNVERIFIED),
            # Notice: verifier_metadata does NOT contain archive_quote
            verifier_metadata={},
        )
        res = self.strategy.evaluate(c_pure_fiction, self.graph)
        # Because of: if not archive_quote: archive_quote = asserted_quote
        self.assertTrue(res.passed, "Vulnerability: fabricated quote verified as passed due to missing archive fallback.")
        self.assertEqual(res.quote_exactness, QuoteExactness.EXACT)

    def test_quote_paraphrase_mandate_enforced_when_distorted(self):
        """Tests that when an actual archive quote is provided, distorted quotes are marked DISTORTED,

        flagged as QUOTE_FABRICATION_DETECTED, assigned MISLEADING status by engine, and trigger BLOCK gate.
        """
        c_distorted = ClaimRecord(
            claim_id="q_distorted",
            claim_text='Galileo boldly declared "The Earth revolves around the Sun with absolute mathematical perfection."',
            claim_type=ClaimType.DIRECT_QUOTE,
            primary_source=SourceRecord(title="Dialogue", url="https://arch.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"archive_quote": "And yet it moves."},
        )
        res = self.strategy.evaluate(c_distorted, self.graph)
        self.assertFalse(res.passed)
        self.assertEqual(res.quote_exactness, QuoteExactness.DISTORTED)
        self.assertIn("QUOTE_FABRICATION_DETECTED", res.flags)
        self.assertIn("Paraphrase Mandate", res.warnings[0])

        # Test through engine: must yield MISLEADING status
        engine_res = self.engine.verify_claim(c_distorted, self.graph)
        self.assertEqual(engine_res.status, EpistemicStatus.MISLEADING)
        self.assertEqual(engine_res.quote_exactness, QuoteExactness.DISTORTED)

        # In dossier: must trigger BLOCK
        dossier = ResearchDossier(topic="Astronomy", run_id="r_quote", claims=[c_distorted])
        report = self.engine.verify_dossier(dossier, self.graph)
        self.assertEqual(report.gate_recommendation, "BLOCK")
        self.assertIn("q_distorted", report.contradicted_claim_ids)


class TestAdversarialNumericalVerification(unittest.TestCase):
    """Adversarial challenge tests for NumericalCheckStrategy and numeric integrity."""

    def setUp(self):
        self.strategy = NumericalCheckStrategy()
        self.graph = EvidenceGraph(graph_id="test_num_graph")
        self.engine = VerificationEngine()

    def test_numerical_order_of_magnitude_trap_various_multiples(self):
        """Tests order-of-magnitude mismatch trap across 10x, 100x, and 1000x errors."""
        # 10x mismatch: 80 million vs 800 million (log10 diff = 1.0)
        c_10x = ClaimRecord(
            claim_id="num_10x",
            claim_text="The bridge project cost 80 million dollars.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Audit", url="https://audit.gov", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": 800.0e6},
        )
        res_10x = self.strategy.evaluate(c_10x, self.graph)
        self.assertFalse(res_10x.passed)
        self.assertIn("ORDER_OF_MAGNITUDE_MISMATCH", res_10x.flags)

        # 1000x mismatch: 50 thousand vs 50 million
        c_1000x = ClaimRecord(
            claim_id="num_1000x",
            claim_text="The company employs 50 thousand people.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="10-K", url="https://sec.gov", tier=SourceTier.INSTITUTIONAL_REPORT),
            verifier_metadata={"ground_truth_num": 50.0e6},
        )
        res_1000x = self.strategy.evaluate(c_1000x, self.graph)
        self.assertFalse(res_1000x.passed)
        self.assertIn("ORDER_OF_MAGNITUDE_MISMATCH", res_1000x.flags)

        # Verify engine assigns CONTRADICTED
        eng_res = self.engine.verify_claim(c_1000x, self.graph)
        self.assertEqual(eng_res.status, EpistemicStatus.CONTRADICTED)

    def test_numerical_zero_handling_bypasses_order_of_magnitude_trap(self):
        """Demonstrates that asserting 0 when ground truth is 10,000,000 does NOT trigger ORDER_OF_MAGNITUDE_MISMATCH.

        The check uses 'if claim_num > 0 and ground_truth > 0:'.
        When claim_num == 0, log10 is skipped, so the order of magnitude trap flag is omitted.
        """
        c_zero = ClaimRecord(
            claim_id="num_zero",
            claim_text="The disease caused 0 deaths worldwide.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="WHO", url="https://who.int", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": 10000000.0},
        )
        res = self.strategy.evaluate(c_zero, self.graph)
        self.assertFalse(res.passed)
        # Flag is NUMERICAL_MISMATCH, NOT ORDER_OF_MAGNITUDE_MISMATCH
        self.assertNotIn(
            "ORDER_OF_MAGNITUDE_MISMATCH",
            res.flags,
            "Trap blindspot: zero asserted value bypasses log10 order-of-magnitude trap.",
        )
        self.assertIn("NUMERICAL_MISMATCH", res.flags)

    def test_numerical_boundary_tolerances_exact_0_1_percent(self):
        """Tests exact 0.1% (0.001) boundary condition strictly."""
        gt = 10000.0

        # Exact: 0.09% deviation (below 0.1% threshold) -> PASS
        c_pass = ClaimRecord(
            claim_id="num_tol_pass",
            claim_text="The measurement yielded 10009 units.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Lab", url="https://lab.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": gt},
        )
        res_pass = self.strategy.evaluate(c_pass, self.graph)
        self.assertTrue(res_pass.passed)

        # Exact: 0.10% deviation (10010 vs 10000 = 0.001000) -> PASS (delta <= tolerance)
        c_boundary = ClaimRecord(
            claim_id="num_tol_bound",
            claim_text="The measurement yielded 10010 units.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Lab", url="https://lab.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": gt},
        )
        res_bound = self.strategy.evaluate(c_boundary, self.graph)
        self.assertTrue(res_bound.passed)

        # Exact: 0.12% deviation (10012 vs 10000 = 0.0012) -> FAIL
        c_fail = ClaimRecord(
            claim_id="num_tol_fail",
            claim_text="The measurement yielded 10012 units.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Lab", url="https://lab.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": gt},
        )
        res_fail = self.strategy.evaluate(c_fail, self.graph)
        self.assertFalse(res_fail.passed)
        self.assertIn("NUMERICAL_MISMATCH", res_fail.flags)

    def test_numerical_boundary_tolerances_approximate_5_0_percent(self):
        """Tests approximate 5.0% (0.05) boundary condition with qualifiers."""
        gt = 10000.0

        # Approximate: 4.9% deviation -> PASS
        c_pass = ClaimRecord(
            claim_id="num_app_pass",
            claim_text="The measurement yielded approximately 10490 units.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Lab", url="https://lab.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": gt},
        )
        self.assertTrue(self.strategy.evaluate(c_pass, self.graph).passed)

        # Approximate: exactly 5.0% deviation (10500 vs 10000) -> PASS
        c_bound = ClaimRecord(
            claim_id="num_app_bound",
            claim_text="The measurement yielded roughly 10500 units.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Lab", url="https://lab.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": gt},
        )
        self.assertTrue(self.strategy.evaluate(c_bound, self.graph).passed)

        # Approximate: 5.1% deviation (10510 vs 10000) -> FAIL
        c_fail = ClaimRecord(
            claim_id="num_app_fail",
            claim_text="The measurement yielded about 10510 units.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Lab", url="https://lab.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": gt},
        )
        res_fail = self.strategy.evaluate(c_fail, self.graph)
        self.assertFalse(res_fail.passed)
        self.assertIn("NUMERICAL_MISMATCH", res_fail.flags)

    def test_numerical_year_prefix_collision_extraction_bug(self):
        """Demonstrates catastrophic extraction bug: when a year precedes a metric in claim text,

        _extract_number_and_multiplier takes matches[0], parsing the YEAR as the metric!
        For example: 'In 2023, company revenue was 80 billion.'
        matches[0] is ('2023', ''). Extracted number is 2023 instead of 80e9.
        This triggers a massive false ORDER_OF_MAGNITUDE_MISMATCH!
        """
        c_year_prefix = ClaimRecord(
            claim_id="num_year_collision",
            claim_text="In 2023, the organization generated 80 billion in total revenue.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Annual Report", url="https://sec.gov", tier=SourceTier.INSTITUTIONAL_REPORT),
            verifier_metadata={"ground_truth_num": 80.0e9},
        )
        res = self.strategy.evaluate(c_year_prefix, self.graph)
        # Because matches[0] = ('2023', ''), extracted claim_num = 2023.0
        # log10(2023) = 3.30 vs log10(80e9) = 10.90 -> diff = 7.60 >= 1.0!
        self.assertEqual(res.details["claim_num"], 2023.0)
        self.assertFalse(res.passed)
        self.assertIn(
            "ORDER_OF_MAGNITUDE_MISMATCH",
            res.flags,
            "Critical bug demonstrated: regex extracts preceding year as metric value!",
        )

    def test_numerical_negative_numbers_parsing_flaw(self):
        """Demonstrates that negative numbers (e.g. -5%) lose their negative sign in regex extraction."""
        text = "Operating margin declined to -5% in Q4."
        extracted = self.strategy._extract_number_and_multiplier(text)
        self.assertIsNotNone(extracted)
        val, is_approx = extracted
        # \b\d+ matches 5, ignoring the minus sign!
        self.assertEqual(
            val,
            5.0,
            "Extraction flaw: negative number -5% extracted as positive scalar 5.0",
        )

    def test_numerical_unit_conversion_absence(self):
        """Demonstrates that unit conversion is completely absent; different units (e.g. 62 miles vs 100 km) fail."""
        c_units = ClaimRecord(
            claim_id="num_units",
            claim_text="The spacecraft traveled 62 miles above the surface.",
            claim_type=ClaimType.NUMERICAL_METRIC,
            primary_source=SourceRecord(title="Flight Log", url="https://space.org", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={"ground_truth_num": 100.0},  # Ground truth in kilometers (100 km = 62.137 miles)
        )
        res = self.strategy.evaluate(c_units, self.graph)
        # Without unit conversion, 62 vs 100 gives 38% deviation, failing numerical verification
        self.assertFalse(res.passed)
        self.assertIn("NUMERICAL_MISMATCH", res.flags)


class TestAdversarialTemporalVerification(unittest.TestCase):
    """Adversarial challenge tests for TemporalCheckStrategy and temporal validity."""

    def setUp(self):
        self.strategy = TemporalCheckStrategy()
        self.graph = EvidenceGraph(graph_id="test_temp_graph")

    def test_temporal_anachronism_registry_positive_detection(self):
        """Tests that historical figures/eras paired with later technologies trigger ANACHRONISM_DETECTED."""
        # Julius Caesar (-44) with radar (1935)
        c1 = ClaimRecord(
            claim_id="t_caesar_radar",
            claim_text="Julius Caesar deployed radar stations along the Rhine frontier.",
            primary_source=SourceRecord(title="History Blog", url="https://blog.org", tier=SourceTier.POPULAR_MEDIA),
        )
        res1 = self.strategy.evaluate(c1, self.graph)
        self.assertFalse(res1.passed)
        self.assertIn("ANACHRONISM_DETECTED", res1.flags)
        self.assertEqual(res1.temporal_status, "anachronistic")

        # Napoleon (1815) with smartphone (2007)
        c2 = ClaimRecord(
            claim_id="t_napoleon_phone",
            claim_text="Napoleon checked his smartphone before the battle of Waterloo.",
            primary_source=SourceRecord(title="Satire", url="https://satire.org", tier=SourceTier.POPULAR_MEDIA),
        )
        res2 = self.strategy.evaluate(c2, self.graph)
        self.assertFalse(res2.passed)
        self.assertIn("ANACHRONISM_DETECTED", res2.flags)

    def test_temporal_anachronism_metaphor_false_positive(self):
        """Demonstrates false positive: comparative or metaphorical mentions of historical eras fail anachronism scan.

        If a sentence compares the modern world to Ancient Rome, matching both 'ancient rome' and 'personal computer',
        it is falsely flagged as an anachronism.
        """
        c_metaphor = ClaimRecord(
            claim_id="t_metaphor",
            claim_text="Unlike ancient rome, modern citizens communicate daily through the personal computer.",
            primary_source=SourceRecord(title="Sociology Essay", url="https://soc.org", tier=SourceTier.EXPERT_ANALYSIS),
        )
        res = self.strategy.evaluate(c_metaphor, self.graph)
        # Falsely flags ANACHRONISM_DETECTED!
        self.assertFalse(res.passed)
        self.assertIn(
            "ANACHRONISM_DETECTED",
            res.flags,
            "False positive demonstrated: comparative statement triggers anachronism flag!",
        )

    def test_temporal_anachronism_explicit_year_bypass_bug(self):
        """Demonstrates flaw: explicit historical years (e.g. 1750) are extracted into claim_year

        but are NEVER compared against ANACHRONISM_REGISTRY!
        Thus, 'In 1750, doctors used the airplane' is completely missed because '1750' is not in era_markers.
        """
        c_year_anachronism = ClaimRecord(
            claim_id="t_year_bypass",
            claim_text="In 1750, explorers traveled across the Atlantic using an airplane.",
            primary_source=SourceRecord(title="Fiction", url="https://fict.org", tier=SourceTier.POPULAR_MEDIA),
        )
        res = self.strategy.evaluate(c_year_bypass, self.graph)
        # The strategy passes this anachronism because claim_year (1750) is never compared to tech_start (1903)!
        self.assertTrue(
            res.passed,
            "Blindspot demonstrated: explicit year anachronism bypassed without era marker!",
        )
        self.assertNotIn("ANACHRONISM_DETECTED", res.flags)

    def test_temporal_chronological_precedence_inversion(self):
        """Tests that inverted cause-and-effect dates trigger CHRONOLOGICAL_INCONSISTENCY."""
        c_inv = ClaimRecord(
            claim_id="t_inversion",
            claim_text="The 1945 atomic bombing caused the 1939 outbreak of World War II.",
            primary_source=SourceRecord(title="Analysis", url="https://hist.org", tier=SourceTier.POPULAR_MEDIA),
            verifier_metadata={"chronology_precedence": ("1945-08-06", "1939-09-01")},
        )
        res = self.strategy.evaluate(c_inv, self.graph)
        self.assertFalse(res.passed)
        self.assertIn("CHRONOLOGICAL_INCONSISTENCY", res.flags)
        self.assertEqual(res.temporal_status, "inverted")

    def test_temporal_freshness_expiration_hardcoded_date_flaw(self):
        """Demonstrates hardcoded date flaw in freshness check.

        In TemporalCheckStrategy: 'if vu < "2026-01-01": flags.append("OUTDATED_CLAIM")'.
        If a claim expired on 2026-06-01 (before current date 2026-09-14),
        it is NOT flagged as outdated because "2026-06-01" < "2026-01-01" is False!
        """
        # Claim that expired on June 1, 2026
        c_expired = ClaimRecord(
            claim_id="t_expired_2026",
            claim_text="He is the current prime minister of the nation.",
            primary_source=SourceRecord(title="Gov Site", url="https://gov.org", tier=SourceTier.PRIMARY_SOURCE),
            temporal_context=TemporalContext(valid_until="2026-06-01", is_time_sensitive=True),
        )
        res = self.strategy.evaluate(c_expired, self.graph)
        # Because of hardcoded 2026-01-01, this claim passes as valid and not outdated!
        self.assertTrue(res.passed)
        self.assertNotIn(
            "OUTDATED_CLAIM",
            res.flags,
            "Flaw confirmed: expired 2026 claim passes due to hardcoded 2026-01-01 cutoff date.",
        )


class TestAdversarialContradictionVerification(unittest.TestCase):
    """Adversarial challenge tests for ContradictionCheckStrategy and non-averaging invariant."""

    def setUp(self):
        self.strategy = ContradictionCheckStrategy()
        self.graph = EvidenceGraph(graph_id="test_contra_graph")
        self.engine = VerificationEngine()

    def test_contradiction_polar_negation_via_counter_source(self):
        """Verifies high-sensitivity contradiction detection and record creation with non-averaging invariant."""
        p_src = SourceRecord(title="Company Founding Charter", url="https://corp.com", tier=SourceTier.PRIMARY_SOURCE)
        c_src = SourceRecord(title="Supreme Court Annulment", url="https://court.gov", tier=SourceTier.PRIMARY_SOURCE, reliability_score=1.0)

        claim = ClaimRecord(
            claim_id="contra_polar",
            claim_text="The corporation was legally chartered in 1920.",
            primary_source=p_src,
            contradicting_sources=[c_src],
        )

        res = self.strategy.evaluate(claim, self.graph)
        self.assertFalse(res.passed)
        self.assertGreaterEqual(res.contradiction_score, 0.90)
        self.assertIn("CONTRADICTION_DETECTED", res.flags)
        self.assertEqual(len(res.contradictions), 1)
        self.assertFalse(res.contradictions[0].is_resolved_by_averaging)

    def test_contradiction_opposing_graph_edges(self):
        """Verifies contradiction detected from graph incoming EdgeRelation.CONTRADICTION."""
        claim = ClaimRecord(
            claim_id="contra_graph_edge",
            claim_text="The treaty was ratified by all member states.",
            primary_source=SourceRecord(title="Treaty Text", url="https://un.org", tier=SourceTier.PRIMARY_SOURCE),
        )
        self.graph.add_claim(claim.claim_id, claim.claim_text, "event_fact")
        self.graph.add_evidence_unit("eu_dissent", "source_dissent", "State X rejected ratification.")
        self.graph.link("eu_dissent", claim.claim_id, EdgeRelation.CONTRADICTION, weight=0.95)

        res = self.strategy.evaluate(claim, self.graph)
        self.assertFalse(res.passed)
        self.assertGreaterEqual(res.contradiction_score, 0.90)
        self.assertIn("eu_dissent", res.contradicting_evidence_ids)

    def test_contradiction_numerical_averaging_violation_caught(self):
        """Verifies that synthetic arithmetic averaging across divergent historical accounts is strictly blocked."""
        # Source A says 20,000 casualties; Source B says 100,000 casualties.
        # Synthetically asserting 60,000 (arithmetic mean) is a policy violation.
        claim = ClaimRecord(
            claim_id="hist_avg_1",
            claim_text="Casualties at the battle totaled 60,000.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=SourceRecord(title="General A Memoirs", url="https://arch.org/a", tier=SourceTier.PRIMARY_SOURCE),
            verifier_metadata={
                "source_values": [20000, 100000],
                "asserted_value": 60000.0,
            },
        )
        # Evaluate via HistoriographicalCheckStrategy
        strat = HistoriographicalCheckStrategy(strict=True)
        res = strat.evaluate(claim, self.graph)
        self.assertFalse(res.passed)
        self.assertIn(HistoriographicalViolationType.NUMERICAL_AVERAGING_DETECTED.value, res.flags)

        # In engine, must yield CONTRADICTED
        eng_res = self.engine.verify_claim(claim, self.graph)
        self.assertEqual(eng_res.status, EpistemicStatus.CONTRADICTED)

    def test_contradiction_numerical_averaging_string_bypass_flaw(self):
        """Demonstrates flaw: when asserted_value is not in metadata, it defaults to claim_text.

        In enforce_non_averaging: float(asserted_value) throws ValueError and gets caught silently!
        Therefore, an averaged figure embedded in natural text ('Casualties were 60,000.') completely bypasses the check!
        """
        checker = HistoricalPolicyChecker(strict=True)
        claim_with_text = ClaimRecord(
            claim_id="hist_avg_text_bypass",
            claim_text="Casualties at the battle totaled approximately 60,000 soldiers.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=SourceRecord(title="General A Memoirs", url="https://arch.org/a", tier=SourceTier.PRIMARY_SOURCE),
            # Notice: source_values provided, but asserted_value omitted from metadata
            verifier_metadata={"source_values": [20000, 100000]},
        )
        report = checker.evaluate_claim(claim_with_text)
        # Because float("Casualties at...") raises ValueError and is swallowed by pass,
        # NUMERICAL_AVERAGING_DETECTED is NOT flagged!
        self.assertNotIn(
            HistoriographicalViolationType.NUMERICAL_AVERAGING_DETECTED,
            report.violations,
            "Bypass flaw demonstrated: averaging in natural text strings is swallowed silently by ValueError catch!",
        )

    def test_contradiction_cross_claim_hardcoded_limitation(self):
        """Demonstrates severe limitation in engine.verify_dossier:

        Cross-claim contradiction is HARDCODED to only detect 'invented in' and 'founded in',
        and only when category != 'general'. Contradicting casualty counts or dates on other verbs are ignored!
        """
        c1 = ClaimRecord(
            claim_id="cc_lim_1",
            claim_text="The treaty was signed in 1918.",
            category="treaty_history",
            primary_source=SourceRecord(title="A", url="https://a.org", tier=SourceTier.PRIMARY_SOURCE),
        )
        c2 = ClaimRecord(
            claim_id="cc_lim_2",
            claim_text="The treaty was signed in 1919.",
            category="treaty_history",
            primary_source=SourceRecord(title="B", url="https://b.org", tier=SourceTier.PRIMARY_SOURCE),
        )
        dossier = ResearchDossier(topic="Treaty", run_id="r_cc", claims=[c1, c2])
        report = self.engine.verify_dossier(dossier, self.graph)
        # Neither claim is flagged as contested because the verb was 'signed in' rather than 'invented in' / 'founded in'!
        self.assertNotIn("cc_lim_1", report.contested_claim_ids)
        self.assertNotIn("cc_lim_2", report.contested_claim_ids)


class TestAdversarialEntailmentAndCorroboration(unittest.TestCase):
    """Adversarial challenge tests for SourceEntailmentStrategy and CrossSourceCorroborationStrategy."""

    def setUp(self):
        self.graph = EvidenceGraph(graph_id="test_entail_corrob_graph")

    def test_entailment_modal_strengthening_penalty(self):
        """Verifies that modal certainty escalation (Level 1 'suggests' -> Level 3 'definitely proven')

        triggers STRENGTHENED_ASSERTION_WARNING and caps score at 0.70.
        """
        strat = SourceEntailmentStrategy()
        claim = ClaimRecord(
            claim_id="entail_modal",
            claim_text="The therapy is definitely proven to cure chronic arthritis completely.",
            primary_source=SourceRecord(
                title="Preliminary evidence suggests therapy may possibly reduce minor symptoms.",
                url="https://nih.gov/paper",
                tier=SourceTier.PEER_REVIEWED_JOURNAL,
            ),
        )
        res = strat.evaluate(claim, self.graph)
        self.assertIn("STRENGTHENED_ASSERTION_WARNING", res.flags)
        self.assertLessEqual(res.entailment_score, 0.70)

    def test_entailment_polar_negation_in_passage_zeroes_score(self):
        """Verifies that opposite polarity between claim and passage (e.g. 'failed' vs affirmative)

        collapses semantic support to 0.0.
        """
        strat = SourceEntailmentStrategy()
        support, is_neg = strat._compute_semantic_support(
            claim_text="The experiment replicated the quantum entanglement effect.",
            passage_text="The experiment failed and never replicated the quantum entanglement effect.",
        )
        self.assertTrue(is_neg)
        self.assertEqual(support, 0.0)

    def test_corroboration_wire_syndication_complete_collapse(self):
        """Verifies that syndication wire tags (AP, Reuters, Bloomberg Wire) collapse corroboration to 0.0."""
        strat = CrossSourceCorroborationStrategy()
        p_src = SourceRecord(title="Global Economic Summit (Reuters)", url="https://site1.com/a", tier=SourceTier.REPUTABLE_JOURNALISM)
        c1 = SourceRecord(title="Market Reacts to Summit (Reuters)", url="https://site2.org/b", tier=SourceTier.REPUTABLE_JOURNALISM)
        c2 = SourceRecord(title="Financial Wrap (Reuters)", url="https://site3.net/c", tier=SourceTier.REPUTABLE_JOURNALISM)

        claim = ClaimRecord(
            claim_id="wire_collapse",
            claim_text="Finance ministers agreed to coordinate fiscal liquidity.",
            primary_source=p_src,
            corroborating_sources=[c1, c2],
        )
        res = strat.evaluate(claim, self.graph)
        self.assertEqual(res.corroboration_score, 0.0)
        self.assertIn("SINGLE_SOURCE_VULNERABILITY", res.flags)

    def test_corroboration_root_domain_collapse(self):
        """Verifies that subdomains belonging to the same root domain collapse independence."""
        strat = CrossSourceCorroborationStrategy()
        p_src = SourceRecord(title="Study", url="https://news.bbc.co.uk/story1", tier=SourceTier.REPUTABLE_JOURNALISM)
        c1 = SourceRecord(title="Followup", url="https://sport.bbc.co.uk/story2", tier=SourceTier.REPUTABLE_JOURNALISM)

        claim = ClaimRecord(
            claim_id="domain_collapse",
            claim_text="Major tournament concluded in London.",
            primary_source=p_src,
            corroborating_sources=[c1],
        )
        res = strat.evaluate(claim, self.graph)
        self.assertEqual(res.corroboration_score, 0.0)
        self.assertIn("SINGLE_SOURCE_VULNERABILITY", res.flags)


if __name__ == "__main__":
    unittest.main()
