"""tests/test_historical_policy_adversarial.py — Adversarial Stress Suite for Historical Scholarship Policy.

Empirical verification suite challenging:
1. Sole Web Source Prohibition & Evidentiary Thresholds (Tiers 9-13, sybil attacks, metadata overrides, duplicate citations)
2. 8-Consensus State Classification under Adversarial Literature Distributions (fall-through edge cases, substring traps, unhandled opposing claims)
3. Non-Averaging Contradiction Invariants (casualty averaging, date averaging, string bypasses, range preservation)
4. Event vs. Interpretation Differentiation & Script Rhetoric (declarative causal claims, smuggled types, unhedged eligibility leakage)
"""

import math
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
)


class TestAdversarialSoleWebSourceProhibition(unittest.TestCase):
    """Adversarial stress-testing of sole web source prohibition and source tier enforcement."""

    def setUp(self):
        self.checker = HistoricalPolicyChecker(strict=True)

    def test_sybil_web_attack_50_blogs_rejected(self):
        """Sybil attack: 50 independent blogs and Wikipedia mirrors repeating a claim must be strictly blocked."""
        blog_sources = [
            SourceRecord(
                title=f"History Blog Mirror #{i}",
                url=f"https://fakenews-history-{i}.example.org/claim",
                tier=SourceTier.SELF_PUBLISHED,
                reliability_score=0.25,
            )
            for i in range(50)
        ]
        claim = ClaimRecord(
            claim_id="sybil_claim_1",
            claim_text="Nero played the fiddle while Rome burned.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=blog_sources[0],
            corroborating_sources=blog_sources[1:],
        )

        report = self.checker.evaluate_claim(claim)

        self.assertIn(HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE, report.violations)
        self.assertEqual(report.epistemic_status, EpistemicStatus.UNSUPPORTED)
        self.assertFalse(report.eligible_for_narration)

    def test_all_forbidden_tiers_individually_rejected(self):
        """Verify each of Tiers 9, 10, 11, 12, 13 is strictly rejected as sole source."""
        forbidden_tiers = [
            (SourceTier.REPUTABLE_JOURNALISM, 9),
            (SourceTier.TRADE_PUBLICATION, 10),
            (SourceTier.POPULAR_MEDIA, 11),
            (SourceTier.SELF_PUBLISHED, 12),
            (SourceTier.UNVERIFIED, 13),
        ]
        for tier, tier_num in forbidden_tiers:
            src = SourceRecord(
                title=f"Source of Tier {tier_num}",
                url=f"https://source-{tier_num}.org",
                tier=tier,
                reliability_score=0.5,
            )
            claim = ClaimRecord(
                claim_id=f"tier_claim_{tier_num}",
                claim_text="Historical event assertion.",
                claim_type=ClaimType.EVENT_FACT,
                primary_source=src,
            )
            report = self.checker.evaluate_claim(claim)
            self.assertIn(
                HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE,
                report.violations,
                f"Tier {tier} ({tier_num}) was not rejected as sole source!",
            )
            self.assertEqual(report.epistemic_status, EpistemicStatus.UNSUPPORTED)
            self.assertFalse(report.eligible_for_narration)

    def test_empty_sources_strictly_rejected(self):
        """A historical claim with no sources must be rejected with UNQUALIFIED_SOLE_SOURCE."""
        is_valid, msgs = self.checker.check_forbidden_sole_source([])
        self.assertFalse(is_valid)
        self.assertIn("No backing sources provided", msgs[0])

        is_valid_t, threshold, t_msgs = self.checker.verify_minimum_source_tiers([], ClaimType.EVENT_FACT)
        self.assertFalse(is_valid_t)
        self.assertIsNone(threshold)

    def test_metadata_strong_consensus_override_does_not_bypass_sole_web_source(self):
        """Malicious/hallucinated verifier_metadata specifying STRONG_CONSENSUS on blog source must NOT bypass rejection."""
        blog_src = SourceRecord(
            title="Conspiracy Blog",
            url="https://conspiracy.blog/pyramids",
            tier=SourceTier.SELF_PUBLISHED,
        )
        claim = ClaimRecord(
            claim_id="spoofed_meta_claim",
            claim_text="Extraterrestrials constructed the Great Pyramid of Giza.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=blog_src,
            verifier_metadata={"consensus_state": ConsensusState.STRONG_CONSENSUS},
        )
        report = self.checker.evaluate_claim(claim)
        self.assertIn(HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE, report.violations)
        self.assertEqual(report.epistemic_status, EpistemicStatus.UNSUPPORTED)
        self.assertFalse(report.eligible_for_narration)

    def test_single_peer_reviewed_source_alone_fails_threshold_c(self):
        """A single Tier 2 peer-reviewed journal cannot satisfy Threshold C without a second independent source."""
        journal = SourceRecord(
            title="Paper on Roman Currency",
            url="https://jstor.org/paper1",
            tier=SourceTier.PEER_REVIEWED_JOURNAL,
        )
        claim = ClaimRecord(
            claim_id="single_tier2_claim",
            claim_text="Silver content dropped 40% in 260 CE.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=journal,
        )
        report = self.checker.evaluate_claim(claim)
        self.assertIn(HistoriographicalViolationType.INSUFFICIENT_TIER_THRESHOLD, report.violations)
        self.assertIsNone(report.qualifying_threshold)
        self.assertFalse(report.eligible_for_narration)

    def test_duplicate_same_peer_reviewed_source_threshold_c_flaw(self):
        """CHALLENGE FINDING: Duplicate citation of the EXACT SAME journal article fools Threshold C."""
        same_journal = SourceRecord(
            title="Duplicate Paper",
            url="https://jstor.org/duplicate-paper",
            tier=SourceTier.PEER_REVIEWED_JOURNAL,
        )
        # Providing the exact same source twice
        claim = ClaimRecord(
            claim_id="duplicate_citation_claim",
            claim_text="Some historical assertion.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=same_journal,
            corroborating_sources=[same_journal],
        )
        report = self.checker.evaluate_claim(claim)
        # Empirical test: does verify_minimum_source_tiers check independence?
        # In current implementation, len(peer_sources) >= 2 passes Threshold C without deduplication.
        self.assertEqual(report.qualifying_threshold, "Threshold C")


class TestAdversarialConsensusClassification(unittest.TestCase):
    """Adversarial stress-testing of all 8 consensus states and distribution boundaries."""

    def setUp(self):
        self.checker = HistoricalPolicyChecker(strict=True)

    def test_state_1_strong_consensus_robustness(self):
        """STRONG_CONSENSUS requires zero dissent, at least 1 primary or academic book, and >=2 scholarly sources."""
        p = SourceRecord(title="Primary Treaty Archive", tier=SourceTier.PRIMARY_SOURCE, url="https://gov.arch/1")
        b = SourceRecord(title="Oxford University Monograph", tier=SourceTier.ACADEMIC_BOOK, url="https://oup.com/b")
        j = SourceRecord(title="Peer-Reviewed Journal", tier=SourceTier.PEER_REVIEWED_JOURNAL, url="https://jstor.org/j")

        claim = ClaimRecord(
            claim_id="strong_claim",
            claim_text="The Magna Carta was granted in 1215.",
            primary_source=p,
            corroborating_sources=[b, j],
            contradicting_sources=[],
        )
        cs = self.checker.classify_consensus_state(claim, [p, b, j])
        self.assertEqual(cs, ConsensusState.STRONG_CONSENSUS)

    def test_state_2_broad_consensus_boundary(self):
        """BROAD_CONSENSUS requires agreement ratio >= 0.90 with minor dissent."""
        p = SourceRecord(title="Primary Source", tier=SourceTier.PRIMARY_SOURCE, url="https://p.org")
        j_list = [
            SourceRecord(title=f"Scholarly Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://j{i}.org")
            for i in range(10)
        ]
        dissent = SourceRecord(title="Dissenting Source", tier=SourceTier.TRADE_PUBLICATION, url="https://d.org")

        claim = ClaimRecord(
            claim_id="broad_claim",
            claim_text="The Black Death originated in Asia and reached Europe in 1347.",
            primary_source=p,
            corroborating_sources=j_list,
            contradicting_sources=[dissent],  # 11 agree vs 1 dissent -> r_agree = 11/12 = 0.9167 >= 0.90
        )
        cs = self.checker.classify_consensus_state(claim, [p] + j_list)
        self.assertEqual(cs, ConsensusState.BROAD_CONSENSUS)

    def test_state_3_majority_interpretation_boundary(self):
        """MAJORITY_INTERPRETATION: 0.60 <= r_agree < 0.90."""
        p = SourceRecord(title="Primary Source", tier=SourceTier.PRIMARY_SOURCE, url="https://p.org")
        j_agree = [
            SourceRecord(title=f"Agree Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://ja{i}.org")
            for i in range(6)
        ]
        j_dissent = [
            SourceRecord(title=f"Dissent Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://jd{i}.org")
            for i in range(3)
        ]
        # Total agree: 7 (p + 6 j), Total dissent: 3 -> r_agree = 7 / 10 = 0.70
        claim = ClaimRecord(
            claim_id="majority_claim",
            claim_text="Agricultural exhaustion contributed significantly to Maya societal shifts.",
            primary_source=p,
            corroborating_sources=j_agree,
            contradicting_sources=j_dissent,
        )
        cs = self.checker.classify_consensus_state(claim, [p] + j_agree)
        self.assertEqual(cs, ConsensusState.MAJORITY_INTERPRETATION)

    def test_state_4_active_debate_boundary(self):
        """ACTIVE_DEBATE: 0.40 <= r_agree < 0.60."""
        j_agree = [
            SourceRecord(title=f"School A Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://a{i}.org")
            for i in range(5)
        ]
        j_dissent = [
            SourceRecord(title=f"School B Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://b{i}.org")
            for i in range(5)
        ]
        # 5 agree vs 5 dissent -> r_agree = 5 / 10 = 0.50
        claim = ClaimRecord(
            claim_id="debate_claim",
            claim_text="The standard of living during the early Industrial Revolution: optimist vs pessimist view.",
            primary_source=j_agree[0],
            corroborating_sources=j_agree[1:],
            contradicting_sources=j_dissent,
        )
        cs = self.checker.classify_consensus_state(claim, j_agree)
        self.assertEqual(cs, ConsensusState.ACTIVE_DEBATE)

    def test_state_5_minority_interpretation_boundary(self):
        """MINORITY_INTERPRETATION: 0.10 <= r_agree < 0.40."""
        j_agree = [
            SourceRecord(title=f"Minority Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://m{i}.org")
            for i in range(2)
        ]
        j_dissent = [
            SourceRecord(title=f"Orthodox Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://o{i}.org")
            for i in range(8)
        ]
        # 2 agree vs 8 dissent -> r_agree = 2 / 10 = 0.20
        claim = ClaimRecord(
            claim_id="minority_claim",
            claim_text="Heterodox thesis on medieval demographic transitions.",
            primary_source=j_agree[0],
            corroborating_sources=j_agree[1:],
            contradicting_sources=j_dissent,
        )
        cs = self.checker.classify_consensus_state(claim, j_agree)
        self.assertEqual(cs, ConsensusState.MINORITY_INTERPRETATION)

    def test_state_6_contested_primary_contradiction(self):
        """CONTESTED: when primary accounts (Tier 1 or Tier 6) directly conflict."""
        prim_a = SourceRecord(title="Roman Tribune Dispatch", tier=SourceTier.PRIMARY_SOURCE, url="https://a.arch")
        prim_b = SourceRecord(title="Carthaginian Chronicler", tier=SourceTier.PRIMARY_SOURCE, url="https://b.arch")

        claim = ClaimRecord(
            claim_id="contested_claim",
            claim_text="Hannibal deployed 50,000 infantry at Cannae.",
            primary_source=prim_a,
            corroborating_sources=[],
            contradicting_sources=[prim_b],
        )
        cs = self.checker.classify_consensus_state(claim, [prim_a])
        self.assertEqual(cs, ConsensusState.CONTESTED)

    def test_state_7_unresolved_explicit_markers(self):
        """UNRESOLVED: triggered by explicit ambiguity markers in notes or claim text."""
        p = SourceRecord(title="Bronze Age Archive", tier=SourceTier.PRIMARY_SOURCE, url="https://ba.arch")
        j = SourceRecord(title="Journal on Bronze Age Collapse", tier=SourceTier.PEER_REVIEWED_JOURNAL, url="https://jba.org")

        claim = ClaimRecord(
            claim_id="unresolved_claim",
            claim_text="The identity of the Sea Peoples remains an open mystery.",
            verification_notes="Surviving records are lost and inconclusive.",
            primary_source=p,
            corroborating_sources=[j],
        )
        cs = self.checker.classify_consensus_state(claim, [p, j])
        self.assertEqual(cs, ConsensusState.UNRESOLVED)

    def test_state_8_insufficient_literature(self):
        """INSUFFICIENT_LITERATURE: when <2 scholarly sources and <1 primary source are present."""
        pop_source = SourceRecord(title="Folklore Magazine", tier=SourceTier.POPULAR_MEDIA, url="https://mag.org")
        claim = ClaimRecord(
            claim_id="insuf_claim",
            claim_text="Local village legend regarding 14th-century ghost sightings.",
            primary_source=pop_source,
        )
        cs = self.checker.classify_consensus_state(claim, [pop_source])
        self.assertEqual(cs, ConsensusState.INSUFFICIENT_LITERATURE)

    def test_adversarial_fringe_below_10_percent_anomaly(self):
        """CHALLENGE FINDING: Claims with <10% support fall through to ACTIVE_DEBATE instead of MINORITY_INTERPRETATION."""
        # 1 agreeing source vs 25 dissenting sources -> r_agree = 1 / 26 = 0.0384 (< 0.10)
        j_agree = SourceRecord(title="Single Fringe Journal", tier=SourceTier.PEER_REVIEWED_JOURNAL, url="https://f.org")
        j_dissent = [
            SourceRecord(title=f"Consensus Journal {i}", tier=SourceTier.PEER_REVIEWED_JOURNAL, url=f"https://c{i}.org")
            for i in range(25)
        ]
        # In order to satisfy n_scholarly >= 2 so it doesn't trigger INSUFFICIENT_LITERATURE, provide 2 peer sources in agree list
        j_agree_list = [j_agree, SourceRecord(title="Fringe 2", tier=SourceTier.PEER_REVIEWED_JOURNAL, url="https://f2.org")]
        # 2 agree vs 25 dissent -> r_agree = 2 / 27 = 0.074 (< 0.10)
        claim = ClaimRecord(
            claim_id="fringe_claim",
            claim_text="Debunked revisionist theory with negligible support.",
            primary_source=j_agree_list[0],
            corroborating_sources=[j_agree_list[1]],
            contradicting_sources=j_dissent,
        )
        cs = self.checker.classify_consensus_state(claim, j_agree_list)
        # Because r_agree < 0.10, it fails all elif branches and hits `return ConsensusState.ACTIVE_DEBATE`!
        self.assertEqual(
            cs,
            ConsensusState.ACTIVE_DEBATE,
            "Documented flaw: r_agree < 0.10 wrongly falls through to ACTIVE_DEBATE instead of MINORITY_INTERPRETATION!",
        )

    def test_adversarial_substring_uncontested_false_positive(self):
        """CHALLENGE FINDING: Substring search 'contested' matches 'uncontested', wrongly classifying claims as CONTESTED."""
        p = SourceRecord(title="Primary Record", tier=SourceTier.PRIMARY_SOURCE, url="https://p.arch")
        j = SourceRecord(title="Journal", tier=SourceTier.PEER_REVIEWED_JOURNAL, url="https://j.org")

        claim = ClaimRecord(
            claim_id="uncontested_event_claim",
            claim_text="The coronation of King George VI was uncontested by Parliament.",
            primary_source=p,
            corroborating_sources=[j],
            contradicting_sources=[],
        )
        cs = self.checker.classify_consensus_state(claim, [p, j])
        # Because 'contested' in 'uncontested' is True, it returns CONTESTED!
        self.assertEqual(
            cs,
            ConsensusState.CONTESTED,
            "Documented flaw: raw substring check 'contested' matches 'uncontested'!",
        )

    def test_adversarial_opposing_claims_ignored_in_consensus(self):
        """CHALLENGE FINDING: opposing_claims parameter is ignored entirely during consensus classification."""
        p = SourceRecord(title="Primary Record", tier=SourceTier.PRIMARY_SOURCE, url="https://p.arch")
        b = SourceRecord(title="Academic Book", tier=SourceTier.ACADEMIC_BOOK, url="https://b.org")
        j = SourceRecord(title="Academic Journal", tier=SourceTier.PEER_REVIEWED_JOURNAL, url="https://j.org")

        main_claim = ClaimRecord(
            claim_id="main_claim",
            claim_text="Event X happened exactly as described.",
            primary_source=p,
            corroborating_sources=[b, j],
            contradicting_sources=[],
        )
        opposing = [
            ClaimRecord(
                claim_id=f"opp_{i}",
                claim_text=f"Event X did not happen, according to source {i}.",
                primary_source=p,
            )
            for i in range(10)
        ]
        # Pass opposing_claims to classify_consensus_state
        cs = self.checker.classify_consensus_state(main_claim, [p, b, j], opposing_claims=opposing)
        # Because opposing_claims is never inspected, it remains STRONG_CONSENSUS!
        self.assertEqual(cs, ConsensusState.STRONG_CONSENSUS)


class TestAdversarialNonAveragingInvariant(unittest.TestCase):
    """Adversarial stress-testing of non-averaging contradiction invariant."""

    def setUp(self):
        self.checker = HistoricalPolicyChecker(strict=True)

    def test_casualty_averaging_strictly_blocked(self):
        """Attempting to assert arithmetic mean of 30,000 and 90,000 (60,000) must be strictly blocked."""
        source_values = [30000.0, 90000.0]
        asserted_average = 60000.0

        is_valid, contra, msgs = self.checker.enforce_non_averaging(
            claim_id="battle_deaths",
            asserted_value=asserted_average,
            source_values=source_values,
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(contra)
        self.assertTrue(contra.is_resolved_by_averaging)
        self.assertIn("POLICY_VIOLATION_NUMERICAL_AVERAGING", msgs[0])

    def test_multi_source_averaging_three_estimates_blocked(self):
        """Averaging three conflicting estimates [10000, 20000, 60000] -> mean 30,000 must be blocked."""
        source_values = [10000.0, 20000.0, 60000.0]
        mean_val = 30000.0

        is_valid, contra, msgs = self.checker.enforce_non_averaging(
            claim_id="multi_est",
            asserted_value=mean_val,
            source_values=source_values,
        )
        self.assertFalse(is_valid)
        self.assertTrue(contra.is_resolved_by_averaging)

    def test_conflicting_historical_dates_averaging_blocked(self):
        """Averaging conflicting foundation years: 1200 CE and 1300 CE -> 1250 CE must be blocked."""
        source_values = [1200.0, 1300.0]
        asserted_date = 1250.0

        is_valid, contra, msgs = self.checker.enforce_non_averaging(
            claim_id="foundation_year",
            asserted_value=asserted_date,
            source_values=source_values,
        )
        self.assertFalse(is_valid)
        self.assertTrue(contra.is_resolved_by_averaging)

    def test_discrete_value_assertion_permitted_and_preserves_range(self):
        """Asserting one of the genuine source values directly (e.g. 30,000) is permitted and preserves the range."""
        source_values = [30000.0, 90000.0]
        is_valid, contra, msgs = self.checker.enforce_non_averaging(
            claim_id="valid_bound",
            asserted_value=30000.0,
            source_values=source_values,
        )
        self.assertTrue(is_valid)
        self.assertIsNotNone(contra)
        self.assertFalse(contra.is_resolved_by_averaging)
        self.assertEqual(contra.reported_range, (30000.0, 90000.0))

    def test_string_formatting_bypasses_averaging_detection(self):
        """CHALLENGE FINDING: Natural language phrases containing averaged figures bypass enforce_non_averaging."""
        source_values = [20000, 100000]  # mean is 60,000
        asserted_text = "approximately 60,000 casualties"

        is_valid, contra, msgs = self.checker.enforce_non_averaging(
            claim_id="nl_bypass_claim",
            asserted_value=asserted_text,
            source_values=source_values,
        )
        # Because float("approximately 60,000 casualties") raises ValueError, the check is silently bypassed!
        self.assertTrue(
            is_valid,
            "Documented flaw: string formatting bypasses numerical averaging detection!",
        )

    def test_evaluate_claim_averaging_blocks_publication(self):
        """evaluate_claim must set eligible_for_narration=False and status=CONTRADICTED when averaging is detected."""
        book = SourceRecord(title="Hist Monograph", tier=SourceTier.ACADEMIC_BOOK, url="https://b.org")
        claim = ClaimRecord(
            claim_id="eval_avg_claim",
            claim_text="The army had 50000 soldiers.",
            claim_type=ClaimType.EVENT_FACT,
            primary_source=book,
            verifier_metadata={
                "source_values": [20000.0, 80000.0],
                "asserted_value": 50000.0,
            },
        )
        report = self.checker.evaluate_claim(claim)
        self.assertIn(HistoriographicalViolationType.NUMERICAL_AVERAGING_DETECTED, report.violations)
        self.assertEqual(report.epistemic_status, EpistemicStatus.CONTRADICTED)
        self.assertFalse(report.eligible_for_narration)
        self.assertTrue(report.is_averaged)


class TestAdversarialEventVsInterpretation(unittest.TestCase):
    """Adversarial stress-testing of event vs interpretation distinction and rhetoric matrix."""

    def setUp(self):
        self.checker = HistoricalPolicyChecker(strict=True)

    def test_all_unhedged_causal_patterns_raise_violation(self):
        """Verify all 8 prohibited unhedged causal phrases trigger POLICY_VIOLATION_UNHEDGED_INTERPRETATION."""
        book = SourceRecord(title="Hist Monograph", tier=SourceTier.ACADEMIC_BOOK, url="https://b.org")
        patterns = [
            ("The alliance system definitely caused the war.", "definitely caused"),
            ("Economic greed was the sole cause of the conflict.", "sole cause"),
            ("Nationalism was the undisputed cause of the revolution.", "undisputed cause"),
            ("It is an established fact that climate shifts caused the migration.", "it is an established fact that"),
            ("It is proven beyond doubt that trade monopolies forced the crisis.", "proven beyond doubt that"),
            ("The crisis was caused solely by currency debasement.", "caused solely by"),
            ("The single reason was religious division.", "the single reason was"),
            ("The naval buildup indisputably caused tensions.", "indisputably caused"),
        ]
        for sentence, phrase in patterns:
            claim = ClaimRecord(
                claim_id="unhedged_pattern_test",
                claim_text=sentence,
                claim_type=ClaimType.CAUSAL_INTERPRETATION,
                primary_source=book,
            )
            is_valid, msgs = self.checker.validate_event_vs_interpretation(
                claim, ConsensusState.BROAD_CONSENSUS
            )
            self.assertFalse(is_valid, f"Pattern '{phrase}' failed to trigger violation!")
            self.assertTrue(any("POLICY_VIOLATION_UNHEDGED_INTERPRETATION" in m for m in msgs))

    def test_scholarly_hedging_passes_validation(self):
        """Properly attributed and hedged causal interpretations must pass validation."""
        book = SourceRecord(title="Hist Monograph", tier=SourceTier.ACADEMIC_BOOK, url="https://b.org")
        claim = ClaimRecord(
            claim_id="hedged_claim",
            claim_text="Historians argue that economic strain and administrative inertia combined to weaken frontiers.",
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
            primary_source=book,
        )
        is_valid, msgs = self.checker.validate_event_vs_interpretation(
            claim, ConsensusState.BROAD_CONSENSUS
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(msgs), 0)

    def test_smuggled_causal_claim_as_event_fact_bypasses_check(self):
        """CHALLENGE FINDING: A causal interpretation classified as EVENT_FACT bypasses validate_event_vs_interpretation."""
        book = SourceRecord(title="Hist Monograph", tier=SourceTier.ACADEMIC_BOOK, url="https://b.org")
        # Smuggling an unhedged causal hypothesis under EVENT_FACT
        claim = ClaimRecord(
            claim_id="smuggled_claim",
            claim_text="The alliance system definitely caused the outbreak of World War I.",
            claim_type=ClaimType.EVENT_FACT,  # Misclassified
            primary_source=book,
        )
        is_valid, msgs = self.checker.validate_event_vs_interpretation(
            claim, ConsensusState.BROAD_CONSENSUS
        )
        # Because claim_type is EVENT_FACT, is_interpretation is False, skipping all regex checks!
        self.assertTrue(
            is_valid,
            "Documented flaw: causal claims misclassified as EVENT_FACT bypass unhedged checks!",
        )

    def test_unhedged_interpretation_eligibility_leakage_in_evaluate_claim(self):
        """CHALLENGE FINDING: In evaluate_claim, UNHEDGED_INTERPRETATION does NOT set eligible_for_narration=False!"""
        book = SourceRecord(title="Hist Monograph", tier=SourceTier.ACADEMIC_BOOK, url="https://b.org")
        claim = ClaimRecord(
            claim_id="unhedged_leakage_claim",
            claim_text="The alliance system definitely caused World War I.",
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
            primary_source=book,
            corroborating_sources=[book],
        )
        report = self.checker.evaluate_claim(claim)
        # Violation is detected in report.violations:
        self.assertIn(HistoriographicalViolationType.UNHEDGED_INTERPRETATION, report.violations)
        # BUT look at eligible_for_narration and epistemic_status!
        # Lines 570-591 in evaluate_claim only check UNQUALIFIED_SOLE_SOURCE and NUMERICAL_AVERAGING!
        # Thus, a claim with UNHEDGED_INTERPRETATION is marked eligible_for_narration=True!
        self.assertTrue(
            report.eligible_for_narration,
            "Documented flaw: UNHEDGED_INTERPRETATION violation does not block eligible_for_narration!",
        )


class TestAdversarialNarrationFramingAndRhetoric(unittest.TestCase):
    """Adversarial stress-testing of narration framing rules and rhetorical constraints."""

    def setUp(self):
        self.checker = HistoricalPolicyChecker(strict=True)

    def test_strong_consensus_forbidden_speculation(self):
        """In STRONG_CONSENSUS, phrases like 'allegedly', 'it is claimed that', 'supposedly' are forbidden."""
        speculative_phrases = ["allegedly", "some believe", "it is claimed that", "supposedly"]
        for phrase in speculative_phrases:
            script = f"The Treaty of Versailles was {phrase} signed on June 28, 1919."
            is_ok, violations = self.checker.check_narration_framing(
                script_text=script,
                consensus_state=ConsensusState.STRONG_CONSENSUS,
                claim_type=ClaimType.EVENT_FACT,
            )
            self.assertFalse(is_ok, f"Speculative phrase '{phrase}' was not flagged!")

    def test_active_debate_mandates_debate_markers(self):
        """In ACTIVE_DEBATE, script must contain debate markers; dogmatic assertions are blocked."""
        dogmatic_script = "Monetarist policy was the settled fact behind the crisis."
        is_ok, violations = self.checker.check_narration_framing(
            script_text=dogmatic_script,
            consensus_state=ConsensusState.ACTIVE_DEBATE,
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
        )
        self.assertFalse(is_ok)

        # Properly hedged script
        balanced_script = "Historians remain divided: scholars debate whether policy X or Y triggered the crisis."
        is_ok_b, violations_b = self.checker.check_narration_framing(
            script_text=balanced_script,
            consensus_state=ConsensusState.ACTIVE_DEBATE,
            claim_type=ClaimType.CAUSAL_INTERPRETATION,
        )
        self.assertTrue(is_ok_b)

    def test_contested_state_forbids_spurious_precision(self):
        """In CONTESTED state, words like 'precisely' or 'exact count of' are forbidden."""
        script = "Surviving accounts conflict, but precisely 42,000 casualties occurred."
        is_ok, violations = self.checker.check_narration_framing(
            script_text=script,
            consensus_state=ConsensusState.CONTESTED,
            claim_type=ClaimType.EVENT_FACT,
        )
        self.assertFalse(is_ok)
        self.assertTrue(any("precisely" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
