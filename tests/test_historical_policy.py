"""tests/test_historical_policy.py — Comprehensive Test Suite for Historical Scholarship Policy.

Verifies:
1. Prohibition on forbidden sole web sources (Tiers 9-13).
2. Minimum evidentiary tier thresholds (Threshold A: Tier 1/6, Threshold B: Tier 3, Threshold C: 2x Tier 2).
3. Deterministic 8-consensus-state classification.
4. Event vs interpretation distinction (unhedged causal hypotheses blocked).
5. Non-averaging contradiction invariant (arithmetic synthesis prohibited, discrete nodes preserved).
6. Calibrated script language framing & balanced attribution formatting.
"""

import unittest

from src.epistemic.historical_policy import (
    ContradictionRecord,
    HistoricalFraming,
    HistoricalPolicyChecker,
    HistoricalScholarshipPolicyEngine,
    HistoriographicalEvaluationReport,
    HistoriographicalViolationType,
)
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    SourceRecord,
    SourceTier,
    TemporalContext,
)


class TestHistoricalScholarshipPolicy(unittest.TestCase):
    """Exhaustive test suite for HistoricalPolicyChecker and scholarship invariants."""

    def setUp(self):
        self.checker = HistoricalPolicyChecker(strict=True)

    # -----------------------------------------------------------------------
    # Rule 1: Prohibition of Sole Web Sources (Tiers 9–13)
    # -----------------------------------------------------------------------
    def test_sole_source_wikipedia_rejected(self):
        """Historical claims backed only by Wikipedia/General Encyclopedias (Tier 9/13) must be UNSUPPORTED."""
        wiki_source = SourceRecord(
            title="Wikipedia: Treaty of Versailles",
            url="https://en.wikipedia.org/wiki/Treaty_of_Versailles",
            tier=SourceTier.UNVERIFIED,
            reliability_score=0.4,
        )
        claim = ClaimRecord(
            claim_id="hist_c1",
            claim_text="The Treaty of Versailles was signed on June 28, 1919.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=wiki_source,
            corroborating_sources=[],
        )

        report = self.checker.evaluate_claim(claim)

        self.assertIn(HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE, report.violations)
        self.assertEqual(report.epistemic_status, EpistemicStatus.UNSUPPORTED)
        self.assertFalse(report.eligible_for_narration)

    def test_sole_source_blog_rejected(self):
        """Historical claims backed only by commercial blogs/popular media must be UNSUPPORTED."""
        blog_source = SourceRecord(
            title="History Blog: Why Rome Fell",
            url="https://someblog.example.com/rome-fall",
            tier=SourceTier.SELF_PUBLISHED,
            reliability_score=0.3,
        )
        claim = ClaimRecord(
            claim_id="hist_c2",
            claim_text="The Roman Republic collapsed due to economic inequality.",
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
            primary_source=blog_source,
            corroborating_sources=[],
        )

        report = self.checker.evaluate_claim(claim)

        self.assertIn(HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE, report.violations)
        self.assertEqual(report.epistemic_status, EpistemicStatus.UNSUPPORTED)
        self.assertFalse(report.eligible_for_narration)

    def test_web_source_corroborated_by_primary_archive_allowed(self):
        """A web source corroborated by a Tier 1 or Tier 3 source is permitted."""
        web_source = SourceRecord(
            title="Web Summary: Treaty of Versailles",
            url="https://en.wikipedia.org/wiki/Treaty_of_Versailles",
            tier=SourceTier.REPUTABLE_JOURNALISM,
            reliability_score=0.7,
        )
        archive_source = SourceRecord(
            title="Treaty of Peace between the Allied and Associated Powers and Germany",
            url="https://archives.gov/milestone-documents/treaty-of-versailles",
            tier=SourceTier.PRIMARY_SOURCE,
            reliability_score=1.0,
            is_primary=True,
        )
        claim = ClaimRecord(
            claim_id="hist_c3",
            claim_text="The Treaty of Versailles was signed on June 28, 1919.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=archive_source,
            corroborating_sources=[web_source],
        )

        report = self.checker.evaluate_claim(claim)

        self.assertNotIn(HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE, report.violations)
        self.assertTrue(report.eligible_for_narration)
        self.assertEqual(report.qualifying_threshold, "Threshold A")

    # -----------------------------------------------------------------------
    # Rule 2: Minimum Evidentiary Thresholds (Thresholds A, B, C)
    # -----------------------------------------------------------------------
    def test_threshold_a_primary_source_pass(self):
        """Threshold A is satisfied by >= 1 verified Tier 1 or Tier 6 archival record."""
        primary_src = SourceRecord(
            title="Bell Labs Demonstration Log 1947",
            url="https://bell-labs.com/archives/1947-log",
            tier=SourceTier.PRIMARY_SOURCE,
            reliability_score=1.0,
        )
        claim = ClaimRecord(
            claim_id="hist_c4",
            claim_text="Bardeen and Brattain demonstrated the transistor on December 23, 1947.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=primary_src,
        )

        report = self.checker.evaluate_claim(claim)

        self.assertEqual(report.qualifying_threshold, "Threshold A")
        self.assertNotIn(HistoriographicalViolationType.INSUFFICIENT_TIER_THRESHOLD, report.violations)

    def test_threshold_b_academic_press_pass(self):
        """Threshold B is satisfied by >= 1 verified Tier 3 university press monograph."""
        oxford_book = SourceRecord(
            title="The Roman Revolution",
            author="Ronald Syme",
            publisher="Oxford University Press",
            url="https://academic.oup.com/book/syme-roman-revolution",
            tier=SourceTier.ACADEMIC_BOOK,
            reliability_score=0.95,
        )
        claim = ClaimRecord(
            claim_id="hist_c5",
            claim_text="The rise of private armies destabilized the Roman senatorial oligarchy.",
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
            primary_source=oxford_book,
        )

        report = self.checker.evaluate_claim(claim)

        self.assertEqual(report.qualifying_threshold, "Threshold B")
        self.assertNotIn(HistoriographicalViolationType.INSUFFICIENT_TIER_THRESHOLD, report.violations)

    def test_threshold_c_two_peer_reviewed_journals_pass(self):
        """Threshold C is satisfied by >= 2 independent Tier 2 peer-reviewed journal articles."""
        journal1 = SourceRecord(
            title="Economic Factors in Late Antiquity",
            publisher="Past & Present",
            url="https://academic.oup.com/past/article/1",
            tier=SourceTier.PEER_REVIEWED_JOURNAL,
            reliability_score=0.98,
        )
        journal2 = SourceRecord(
            title="Monetary Debasement in Third Century Rome",
            publisher="Journal of Roman Studies",
            url="https://cambridge.org/jrs/article/2",
            tier=SourceTier.PEER_REVIEWED_JOURNAL,
            reliability_score=0.98,
        )
        claim = ClaimRecord(
            claim_id="hist_c6",
            claim_text="Currency debasement accelerated inflationary pressure in third-century Rome.",
            claim_type=ClaimType.SCHOLARLY_INTERPRETATION,
            primary_source=journal1,
            corroborating_sources=[journal2],
        )

        report = self.checker.evaluate_claim(claim)

        self.assertEqual(report.qualifying_threshold, "Threshold C")
        self.assertNotIn(HistoriographicalViolationType.INSUFFICIENT_TIER_THRESHOLD, report.violations)

    def test_single_peer_reviewed_journal_insufficient_for_threshold_c(self):
        """A single Tier 2 journal article alone fails Threshold C without primary backing."""
        journal1 = SourceRecord(
            title="Speculative Trade Routes in Bronze Age",
            url="https://jstor.org/stable/12345",
            tier=SourceTier.PEER_REVIEWED_JOURNAL,
            reliability_score=0.95,
        )
        claim = ClaimRecord(
            claim_id="hist_c7",
            claim_text="Tin trade routes extended to Cornwall in the second millennium BCE.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=journal1,
            corroborating_sources=[],
        )

        report = self.checker.evaluate_claim(claim)

        self.assertIsNone(report.qualifying_threshold)
        self.assertIn(HistoriographicalViolationType.INSUFFICIENT_TIER_THRESHOLD, report.violations)

    # -----------------------------------------------------------------------
    # Rule 3: 8-State Consensus Model Classification
    # -----------------------------------------------------------------------
    def test_8_consensus_states_classification(self):
        """Verifies mapping of scholarly literature into all 8 ConsensusState categories."""
        # 1. STRONG_CONSENSUS
        p1 = SourceRecord(title="Primary Treaty", url="https://a.gov/t", tier=SourceTier.PRIMARY_SOURCE)
        j1 = SourceRecord(title="Journal 1", url="https://b.org/j1", tier=SourceTier.PEER_REVIEWED_JOURNAL)
        j2 = SourceRecord(title="Journal 2", url="https://c.org/j2", tier=SourceTier.PEER_REVIEWED_JOURNAL)
        c_strong = ClaimRecord(
            claim_id="cs1",
            claim_text="The Treaty of Versailles was concluded in 1919.",
            primary_source=p1,
            corroborating_sources=[j1, j2],
        )
        self.assertEqual(self.checker.classify_consensus_state(c_strong, [p1, j1, j2]), ConsensusState.STRONG_CONSENSUS)

        # 2. BROAD_CONSENSUS (>90% agreement, minor dissent)
        dissent_src = SourceRecord(title="Minority blog", url="https://d.org/d", tier=SourceTier.TRADE_PUBLICATION)
        c_broad = ClaimRecord(
            claim_id="cs2",
            claim_text="The Industrial Revolution began in Great Britain.",
            primary_source=p1,
            corroborating_sources=[j1, j2] * 5,
            contradicting_sources=[dissent_src],
        )
        self.assertEqual(self.checker.classify_consensus_state(c_broad, [p1] + [j1, j2] * 5), ConsensusState.BROAD_CONSENSUS)

        # 3. MAJORITY_INTERPRETATION (60-90% agreement)
        dissent_list = [dissent_src, dissent_src, dissent_src]
        c_maj = ClaimRecord(
            claim_id="cs3",
            claim_text="Economic factors were the primary cause.",
            primary_source=p1,
            corroborating_sources=[j1, j2, j1, j2, j1],
            contradicting_sources=dissent_list,
        )
        self.assertEqual(self.checker.classify_consensus_state(c_maj, [p1, j1, j2, j1, j2, j1]), ConsensusState.MAJORITY_INTERPRETATION)

        # 4. ACTIVE_DEBATE (40-60% split between competing schools)
        c_active = ClaimRecord(
            claim_id="cs4",
            claim_text="Debate between monetarist and Keynesian explanations of the Great Depression.",
            primary_source=p1,
            corroborating_sources=[j1, j2],
            contradicting_sources=[j1, j2, j1],
        )
        self.assertEqual(self.checker.classify_consensus_state(c_active, [p1, j1, j2]), ConsensusState.ACTIVE_DEBATE)

        # 5. CONTESTED (primary accounts conflict)
        c_contested = ClaimRecord(
            claim_id="cs5",
            claim_text="Contested casualty counts in the Battle of Borodino.",
            primary_source=p1,
            corroborating_sources=[j1],
            contradicting_sources=[p1],
        )
        self.assertEqual(self.checker.classify_consensus_state(c_contested, [p1, j1]), ConsensusState.CONTESTED)

        # 6. UNRESOLVED (records are lost / open mystery)
        c_unres = ClaimRecord(
            claim_id="cs6",
            claim_text="The exact location of Genghis Khan's tomb remains an open mystery.",
            verification_notes="Historical evidence remains inconclusive; archival records are lost.",
            primary_source=p1,
            corroborating_sources=[j1],
        )
        self.assertEqual(self.checker.classify_consensus_state(c_unres, [p1, j1]), ConsensusState.UNRESOLVED)

        # 7. INSUFFICIENT_LITERATURE (<2 scholarly sources, 0 primary)
        trade_src = SourceRecord(title="Pop Mag", url="https://pop.org", tier=SourceTier.POPULAR_MEDIA)
        c_insuf = ClaimRecord(
            claim_id="cs7",
            claim_text="Fringe legend regarding medieval folklore.",
            primary_source=trade_src,
            corroborating_sources=[],
        )
        self.assertEqual(self.checker.classify_consensus_state(c_insuf, [trade_src]), ConsensusState.INSUFFICIENT_LITERATURE)

        # 8. MINORITY_INTERPRETATION
        c_min = ClaimRecord(
            claim_id="cs8",
            claim_text="Revisionist thesis on Roman agrarian reforms.",
            primary_source=j1,
            corroborating_sources=[j2],
            contradicting_sources=[j1] * 7,
        )
        self.assertEqual(self.checker.classify_consensus_state(c_min, [j1, j2]), ConsensusState.MINORITY_INTERPRETATION)

    # -----------------------------------------------------------------------
    # Rule 4: Event vs. Interpretation Differentiation
    # -----------------------------------------------------------------------
    def test_unhedged_causal_interpretation_rejected(self):
        """A causal interpretation phrased with unhedged declarative certainty must be rejected."""
        oxford_book = SourceRecord(
            title="The Origins of World War I",
            publisher="Cambridge University Press",
            url="https://cambridge.org/ww1",
            tier=SourceTier.ACADEMIC_BOOK,
        )
        claim = ClaimRecord(
            claim_id="hist_c8",
            claim_text="The alliance system was the sole cause of World War I, proven beyond doubt that no other factor mattered.",
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
            primary_source=oxford_book,
        )

        report = self.checker.evaluate_claim(claim)

        self.assertIn(HistoriographicalViolationType.UNHEDGED_INTERPRETATION, report.violations)

    def test_hedged_causal_interpretation_permitted(self):
        """A causal interpretation properly framed with scholarly attribution is permitted."""
        oxford_book = SourceRecord(
            title="The Origins of World War I",
            publisher="Cambridge University Press",
            url="https://cambridge.org/ww1",
            tier=SourceTier.ACADEMIC_BOOK,
        )
        claim = ClaimRecord(
            claim_id="hist_c9",
            claim_text="Historians emphasize that rigid alliance mobilization schedules were a major contributing factor in 1914.",
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
            primary_source=oxford_book,
        )

        report = self.checker.evaluate_claim(claim)

        self.assertNotIn(HistoriographicalViolationType.UNHEDGED_INTERPRETATION, report.violations)

    # -----------------------------------------------------------------------
    # Rule 5: Non-Averaging Contradiction Invariant
    # -----------------------------------------------------------------------
    def test_non_averaging_invariant_enforced(self):
        """Detects and strictly blocks arithmetic averaging of divergent historical casualty counts."""
        # Divergent source values: 20,000 vs 100,000
        source_values = [20000.0, 100000.0]
        # Average is 60,000
        synthetic_average = 60000.0

        is_valid, contra_rec, msgs = self.checker.enforce_non_averaging(
            claim_id="claim_battle",
            asserted_value=synthetic_average,
            source_values=source_values,
        )

        self.assertFalse(is_valid)
        self.assertIsNotNone(contra_rec)
        self.assertTrue(contra_rec.is_resolved_by_averaging)
        self.assertIn("POLICY_VIOLATION_NUMERICAL_AVERAGING", msgs[0])

    def test_non_averaging_preserves_discrete_range(self):
        """Preserves discrete divergent figures without taking an average."""
        source_values = [20000.0, 100000.0]
        # Asserting one of the historical claims directly: 20,000
        is_valid, contra_rec, msgs = self.checker.enforce_non_averaging(
            claim_id="claim_battle_valid",
            asserted_value=20000.0,
            source_values=source_values,
        )

        self.assertTrue(is_valid)
        self.assertIsNotNone(contra_rec)
        self.assertFalse(contra_rec.is_resolved_by_averaging)
        self.assertEqual(contra_rec.reported_range, (20000.0, 100000.0))

    # -----------------------------------------------------------------------
    # Rule 6: Calibrated Rhetoric Matrix & Balanced Attribution
    # -----------------------------------------------------------------------
    def test_narration_framing_strong_consensus(self):
        """In STRONG_CONSENSUS, speculative phrases like 'allegedly' are forbidden."""
        script_with_speculation = "The treaty allegedly concluded on June 28, 1919."
        is_ok, violations = self.checker.check_narration_framing(
            script_text=script_with_speculation,
            consensus_state=ConsensusState.STRONG_CONSENSUS,
            claim_type=ClaimType.EVENT_FACT,
        )
        self.assertFalse(is_ok)
        self.assertTrue(any("allegedly" in v for v in violations))

    def test_narration_framing_active_debate(self):
        """In ACTIVE_DEBATE, dogmatic phrases like 'settled fact' are forbidden, and debate markers are required."""
        script_dogmatic = "It is a settled fact that monetarist policy alone caused the downturn."
        is_ok, violations = self.checker.check_narration_framing(
            script_text=script_dogmatic,
            consensus_state=ConsensusState.ACTIVE_DEBATE,
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
        )
        self.assertFalse(is_ok)
        self.assertTrue(any("settled fact" in v for v in violations))

        # Balanced debate narration
        script_balanced = "Historians remain divided: whereas monetarists argue X, Keynesians contend Y."
        is_ok_b, violations_b = self.checker.check_narration_framing(
            script_text=script_balanced,
            consensus_state=ConsensusState.ACTIVE_DEBATE,
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
        )
        self.assertTrue(is_ok_b)
        self.assertEqual(len(violations_b), 0)

    def test_format_balanced_attribution(self):
        """Validates templated balanced attribution formatting."""
        perspectives = [
            {"scholar": "A.J.P. Taylor", "argument": "the war resulted from diplomatic blunders"},
            {"scholar": "Fritz Fischer", "argument": "imperial German expansionism drove the conflict"},
        ]
        result = self.checker.format_balanced_attribution(perspectives)
        self.assertIn("Historians such as A.J.P. Taylor argue that the war resulted from diplomatic blunders", result)
        self.assertIn("whereas Fritz Fischer contends that imperial German expansionism drove the conflict", result)


if __name__ == "__main__":
    unittest.main()
