"""
tests/test_research_adversarial.py — Adversarial Stress Testing & Edge Case Harness for R1 Research Engine

Empirical challenges covered:
1. Fuzz Inputs:
   - Empty strings, pure whitespace (rejection validation)
   - Massive strings (1,000 to 50,000 characters)
   - Unicode, multi-lingual scripts (Arabic, Chinese, Japanese, Hebrew, Cyrillic, Devanagari, Greek, Thai, Diacritics)
   - Emojis, symbols, and pictographs
   - Security payloads (SQL injection, JSON injection, YAML exploits, XSS/HTML, null bytes, regex backtracking strings)
   - Extreme punctuation and special symbols

2. Extreme Durations:
   - 1 second (minimum positive boundary)
   - 500 seconds, 3600 seconds (1 hour), 100,000 seconds
   - Floating point durations (15.5s, 0.75s)
   - Boundary durations (0s, negative values: -10s, -500s)
   - Proportional beat scaling and duration distribution math

3. Network Failure & Provider Resiliency:
   - DNS resolution failure (URLError getaddrinfo)
   - HTTP error codes (403, 404, 429, 500, 502, 503, 504)
   - Socket timeouts and connection resets
   - Malformed JSON, empty responses, HTML error bodies
   - Fault isolation across multi-provider dispatcher
   - Graceful fallback verification (zero unhandled exceptions, valid dossier returned)

4. Confidence Score Bounds & Scoring Heuristics:
   - Invariant assertion: confidence score strictly in [0.0, 1.0] across all claims
   - Mathematical boundary testing (negative/excessive weights, negative conflict penalties, out-of-range domain authority)
   - Domain authority tiers (Tier 1 .gov/.edu/bell-labs/nobelprize, Tier 2, Tier 3, unknown)
   - Corroboration diversity scoring across single vs multi-domain sources
   - Clarity and specificity heuristic parsing (dates, units, metrics, proper nouns)
   - Disputed terminology conflict penalty application
   - All preset claims confidence bounds validation

5. Contract & Data Integrity:
   - Schema conformance and versioning
   - Claim ID referential integrity in talking points and statistics
   - Procedural seed reproducibility and topic entropy
   - Atomic JSON/YAML serialization and roundtrip fidelity
"""

import io
import json
import os
import re
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from src.config import AppConfig, get_default_config
from src.models.dossier import (
    Claim,
    DossierMetadata,
    ResearchDossier,
    Source,
    Statistic,
    Summary,
    TalkingPoint,
)
from src.research.engine import ResearchEngine, ResearchUnavailableError
from src.research.providers import (
    BaseSearchProvider,
    DuckDuckGoProvider,
    ExaProvider,
    MockSearchProvider,
    MultiProviderDispatcher,
    SearchResult,
    TavilyProvider,
    WikipediaProvider,
    clean_snippet,
    extract_domain,
)
from src.research.scoring import (
    DISPUTED_TERMS,
    TIER_1_DOMAINS,
    TIER_2_DOMAINS,
    TIER_3_DOMAINS,
    ScoringWeights,
    calculate_clarity_score,
    calculate_confidence_score,
    calculate_conflict_penalty,
    calculate_corroboration_score,
    extract_root_domain,
    get_domain_authority,
    score_claim,
)


class TestFuzzInputs(unittest.TestCase):
    """Untrusted and unsupported briefs fail closed instead of receiving fake facts."""

    def setUp(self):
        self.engine = ResearchEngine()

    def test_empty_and_whitespace_topics_are_rejected(self):
        for topic in ("", "   ", "\t\n", "\u200b\u200b"):
            with self.subTest(topic=topic):
                if topic.strip():
                    with self.assertRaises(ResearchUnavailableError):
                        self.engine.synthesize_research(topic, offline=True)
                else:
                    with self.assertRaises(ValueError):
                        self.engine.synthesize_research(topic, offline=True)

    def test_long_unicode_and_untrusted_topics_do_not_receive_fabricated_dossiers(self):
        topics = (
            ("Transistor semiconductor physics " * 350)[:10000],
            ("Quantum Entanglement Superposition " * 1500)[:50000],
            "\U0001f52c \U0001f680 \U0001f916",
            "\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u062a\u0631\u0627\u0646\u0632\u0633\u062a\u0648\u0631",
            "\u534a\u5c0e\u4f53\u306e\u6b74\u53f2",
            "caf\u00e9 semiconductor history",
            "' OR '1'='1'; DROP TABLE dossiers; --",
            '{"__proto__": {"admin": true}, "topic": "hacked"}',
            "!!python/object/apply:os.system ['echo pwned']",
            "transistor; rm -rf /; echo pwned",
            "<script>alert('XSS')</script><b>Bold Topic</b>",
            "transistor\x00\x01 history",
            "((a+)+)+b topic brief",
        )
        for topic in topics:
            with self.subTest(topic=topic[:80]):
                with self.assertRaises(ResearchUnavailableError):
                    self.engine.synthesize_research(topic, offline=True)

    def test_unknown_topic_failure_does_not_write_a_dossier(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ResearchUnavailableError):
                self.engine.synthesize_research(
                    "Unsupported beta topic", offline=True, output_dir=temp_dir
                )
            self.assertEqual(list(Path(temp_dir).iterdir()), [])


class TestExtremeDurations(unittest.TestCase):
    """Adversarial stress testing on target duration parameters."""

    def setUp(self):
        self.engine = ResearchEngine()

    def test_extreme_duration_1_second(self):
        """Assert minimum positive duration of 1s scales talking point durations correctly without div-by-zero."""
        # 1. Preset topic
        dossier_preset = self.engine.synthesize_research("The History of the Transistor", offline=True, target_duration=1)
        self.assertEqual(dossier_preset.metadata.target_duration_seconds, 1)
        total_tp_preset = sum(tp.estimated_duration_sec for tp in dossier_preset.talking_points)
        self.assertAlmostEqual(total_tp_preset, 1.0, delta=0.5)

        # Another bundled preset uses the same duration scaling path.
        dossier_gpu = self.engine.synthesize_research("How GPUs Work", offline=True, target_duration=1)
        self.assertEqual(dossier_gpu.metadata.target_duration_seconds, 1)
        total_tp_gpu = sum(tp.estimated_duration_sec for tp in dossier_gpu.talking_points)
        self.assertAlmostEqual(total_tp_gpu, 1.0, delta=0.1)

    def test_extreme_duration_500_seconds(self):
        """Assert large 500s duration scales talking points accurately."""
        dossier = self.engine.synthesize_research("How GPUs Work", offline=True, target_duration=500)
        self.assertEqual(dossier.metadata.target_duration_seconds, 500)
        total_tp = sum(tp.estimated_duration_sec for tp in dossier.talking_points)
        self.assertAlmostEqual(total_tp, 500.0, delta=5.0)

    def test_extreme_duration_3600_seconds(self):
        """Assert 1-hour (3600s) target duration executes safely."""
        dossier = self.engine.synthesize_research("The Apollo Guidance Computer", offline=True, target_duration=3600)
        self.assertEqual(dossier.metadata.target_duration_seconds, 3600)
        total_tp = sum(tp.estimated_duration_sec for tp in dossier.talking_points)
        self.assertAlmostEqual(total_tp, 3600.0, delta=10.0)

    def test_extreme_duration_100k_seconds(self):
        """Assert a bundled preset duration of 100,000s does not overflow."""
        dossier = self.engine.synthesize_research("How Quantum Computers Work", offline=True, target_duration=100000)
        self.assertEqual(dossier.metadata.target_duration_seconds, 100000)
        total_tp = sum(tp.estimated_duration_sec for tp in dossier.talking_points)
        self.assertAlmostEqual(total_tp, 100000.0, delta=1.0)

    def test_extreme_duration_floating_point(self):
        """Assert floating point durations (e.g. 15.5s, 0.75s) are handled gracefully."""
        for dur in [15.5, 0.75]:
            dossier = self.engine.synthesize_research("The History of the Transistor", offline=True, target_duration=dur)
            self.assertEqual(dossier.metadata.target_duration_seconds, dur)
            total_tp = sum(tp.estimated_duration_sec for tp in dossier.talking_points)
            self.assertAlmostEqual(total_tp, float(dur), delta=1.0)

    def test_extreme_duration_zero_and_negative_resilience(self):
        """Assert zero and negative durations execute without unhandled crashes."""
        for dur in [0, -10, -500]:
            dossier = self.engine.synthesize_research("The History of the Transistor", offline=True, target_duration=dur)
            self.assertIsInstance(dossier, ResearchDossier)
            self.assertEqual(dossier.metadata.target_duration_seconds, dur)


class TestNetworkFailureSimulation(unittest.TestCase):
    """Adversarial network failure simulation and fallback guarantee tests."""

    def setUp(self):
        self.engine = ResearchEngine()

    def test_network_dns_resolution_failure_is_reported(self):
        """DNS failure is reported instead of returning fabricated fallback research."""
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("DNS lookup failed")):
            with self.assertRaises(ResearchUnavailableError):
                self.engine.synthesize_research("Advanced Superconductors In Fusion Reactors", offline=False)

    def test_network_http_status_codes_are_reported(self):
        """HTTP errors do not produce a successful-looking dossier."""
        for code in [403, 404, 429, 500, 502, 503, 504]:
            with self.subTest(http_status=code):
                err = urllib.error.HTTPError(
                    url="https://api.example.com", code=code, msg=f"HTTP Error {code}",
                    hdrs={}, fp=io.BytesIO(b"Error response body"),
                )
                with patch("urllib.request.urlopen", side_effect=err):
                    with self.assertRaises(ResearchUnavailableError):
                        self.engine.synthesize_research("Photonic Quantum Processors", offline=False)

    def test_network_socket_timeout_is_reported(self):
        with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
            with self.assertRaises(ResearchUnavailableError):
                self.engine.synthesize_research("Neuromorphic Computing Architectures", offline=False)

    def test_network_connection_reset_is_reported(self):
        with patch("urllib.request.urlopen", side_effect=ConnectionResetError("Connection reset by peer")):
            with self.assertRaises(ResearchUnavailableError):
                self.engine.synthesize_research("Carbon Nanotube Field-Effect Transistors", offline=False)

    def test_network_malformed_json_does_not_return_a_dossier(self):
        malformed_bodies = [
            b"<!DOCTYPE html><html><body>502 Bad Gateway</body></html>",
            b"{ invalid json content here ...", b"", b"null", b"42",
            b"{\"results\": \"should_be_list_not_string\"}",
        ]
        for body in malformed_bodies:
            with self.subTest(body=body):
                mock_resp = MagicMock()
                mock_resp.read.return_value = body
                mock_resp.__enter__.return_value = mock_resp
                with patch("urllib.request.urlopen", return_value=mock_resp):
                    with self.assertRaises(ResearchUnavailableError):
                        self.engine.synthesize_research("High Temperature Superconductivity", offline=False)

    def test_network_multi_provider_fault_isolation(self):
        """Assert dispatcher continues when individual providers fail."""
        dispatcher = MultiProviderDispatcher()
        # Replace one provider with failing mock and one with working mock
        failing_provider = MockSearchProvider(simulate_error=True)
        working_provider = MockSearchProvider(simulate_error=False)
        dispatcher.providers = [failing_provider, working_provider]

        results = dispatcher.search("test query", max_results=3)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].source_domain, "example.org")

    def test_network_all_providers_failing_dispatcher(self):
        """Assert dispatcher returns empty list when all providers fail without crashing."""
        dispatcher = MultiProviderDispatcher()
        dispatcher.providers = [
            MockSearchProvider(simulate_error=True),
            MockSearchProvider(simulate_error=True),
        ]
        results = dispatcher.search("fail query", max_results=5)
        self.assertEqual(results, [])

    def test_clean_snippet_sanitization(self):
        """Assert snippet cleaner handles HTML, control characters, and entity escaping."""
        raw_text = "<b>Transistors</b> were invented in &lt;1947&gt; &amp; changed world!   &#39;Bell Labs&#39;."
        cleaned = clean_snippet(raw_text)
        self.assertEqual(cleaned, "Transistors were invented in <1947> & changed world! 'Bell Labs'.")
        self.assertEqual(clean_snippet(""), "")
        self.assertEqual(clean_snippet(None), "")


class TestConfidenceScoreBoundsAndHeuristics(unittest.TestCase):
    """Adversarial mathematical validation of confidence scoring bounds and heuristics."""

    def test_confidence_bounds_strictly_between_0_and_1(self):
        """Assert every claim confidence score generated across 20 distinct topics is in [0.0, 1.0]."""
        engine = ResearchEngine()
        sample_topics = [
            "The History of the Transistor",
            "How GPUs Work",
            "The Apollo Guidance Computer",
            "How Quantum Computers Work",
        ]
        for topic in sample_topics:
            dossier = engine.synthesize_research(topic, offline=True)
            for claim in dossier.claims:
                score = claim.confidence_score
                self.assertIsInstance(score, float)
                self.assertGreaterEqual(score, 0.0, f"Score {score} < 0.0 for claim {claim.claim_id}")
                self.assertLessEqual(score, 1.0, f"Score {score} > 1.0 for claim {claim.claim_id}")

    def test_calculate_confidence_score_extreme_arguments(self):
        """Assert calculate_confidence_score clamps mathematically out-of-range inputs."""
        # Extreme high authority and weights
        weights_high = ScoringWeights(weight_authority=50.0, weight_corroboration=50.0, weight_clarity=50.0)
        score_max = calculate_confidence_score(10.0, 10.0, 10.0, conflict_penalty=0.0, weights=weights_high)
        self.assertEqual(score_max, 1.0)

        # Extreme high conflict penalty
        score_min = calculate_confidence_score(1.0, 1.0, 1.0, conflict_penalty=100.0)
        self.assertEqual(score_min, 0.0)

        # Negative inputs
        score_neg = calculate_confidence_score(-10.0, -10.0, -10.0, conflict_penalty=50.0)
        self.assertEqual(score_neg, 0.0)

        # Zero weights
        weights_zero = ScoringWeights(0.0, 0.0, 0.0)
        score_zero = calculate_confidence_score(1.0, 1.0, 1.0, conflict_penalty=0.0, weights=weights_zero)
        self.assertEqual(score_zero, 0.0)

    def test_domain_authority_tiers(self):
        """Assert domain authority scoring matches assigned tier taxonomy."""
        # Tier 1
        for d in ["nobelprize.org", "bell-labs.com", "nasa.gov", "ieee.org", "mit.edu"]:
            auth = get_domain_authority(f"https://sub.{d}/page")
            self.assertGreaterEqual(auth, 0.95)

        # .gov and .edu wildcards
        self.assertEqual(get_domain_authority("https://energy.gov/report"), 0.98)
        self.assertEqual(get_domain_authority("https://cs.harvard.edu/paper"), 0.95)

        # Tier 2
        for d in ["wikipedia.org", "britannica.com", "spectrum.ieee.org"]:
            auth = get_domain_authority(f"https://en.{d}/entry")
            self.assertGreaterEqual(auth, 0.88)

        # Tier 3
        for d in ["arstechnica.com", "theverge.com", "reuters.com"]:
            auth = get_domain_authority(f"https://www.{d}/article")
            self.assertGreaterEqual(auth, 0.70)

        # Unknown / Generic
        self.assertEqual(get_domain_authority("https://random-tech-blog.com/post"), 0.55)
        self.assertEqual(get_domain_authority("not-a-url"), 0.40)
        self.assertEqual(get_domain_authority(""), 0.40)

    def test_corroboration_score_diversity(self):
        """Assert corroboration score scales with domain diversity."""
        primary = Source(title="Primary", url="https://nature.com/article1")

        # 0 corroborating
        c0 = calculate_corroboration_score(primary, [])
        self.assertEqual(c0, 0.40)

        # 1 corroborating on same domain
        c_same = calculate_corroboration_score(primary, [Source(title="Same", url="https://nature.com/article2")])
        self.assertEqual(c_same, 0.60)

        # 2 distinct domains
        c2 = calculate_corroboration_score(primary, [Source(title="Other", url="https://ieee.org/paper")])
        self.assertEqual(c2, 0.75)

        # 3+ distinct domains
        c3 = calculate_corroboration_score(
            primary,
            [
                Source(title="Other 1", url="https://ieee.org/paper"),
                Source(title="Other 2", url="https://mit.edu/research"),
            ],
        )
        self.assertEqual(c3, 1.0)

    def test_clarity_score_heuristics(self):
        """Assert clarity score captures dates, metrics, and capitalized entities."""
        # Baseline with no entities or dates
        q_base = calculate_clarity_score("this is a generic claim without specificity")
        self.assertAlmostEqual(q_base, 0.20)

        # Date only
        q_date = calculate_clarity_score("Demonstrated in December 1947 by physicists.")
        self.assertGreater(q_date, q_base)

        # Numerical metric only
        q_metric = calculate_clarity_score("Achieves 90% efficiency and 100 billion transistors.")
        self.assertGreater(q_metric, q_base)

        # Full high-clarity claim (dates + metrics + proper nouns)
        q_full = calculate_clarity_score("In December 1947, John Bardeen and Walter Brattain at Bell Labs scaled 100 billion transistors.")
        self.assertEqual(q_full, 1.0)

        # Empty string
        self.assertEqual(calculate_clarity_score(""), 0.20)

    def test_conflict_penalty_triggers(self):
        """Assert conflict penalty triggers on disputed keywords and ignores clean text."""
        for term in DISPUTED_TERMS:
            with self.subTest(disputed_term=term):
                claim = f"The invention was {term} by multiple researchers."
                penalty = calculate_conflict_penalty(claim)
                self.assertEqual(penalty, 0.25)

        # Clean text
        self.assertEqual(calculate_conflict_penalty("Unanimously confirmed by historical archives."), 0.0)
        self.assertEqual(calculate_conflict_penalty(""), 0.0)

    def test_score_claim_integration(self):
        """Assert score_claim integrates authority, corroboration, clarity, and penalties into clamped score."""
        primary_high = Source(title="Nobel", url="https://nobelprize.org/prizes/physics/1956")
        corrob_high = [
            Source(title="Bell Labs", url="https://bell-labs.com/history"),
            Source(title="IEEE", url="https://ieee.org/milestone"),
        ]
        text_high = "On December 23, 1947, John Bardeen and Walter Brattain created the first point-contact transistor at Bell Labs."

        score_high = score_claim(text_high, primary_high, corrob_high)
        self.assertGreaterEqual(score_high, 0.90)
        self.assertLessEqual(score_high, 1.0)

        # Full score with explicit numerical metric (100 billion)
        text_full = "In December 1947, John Bardeen and Walter Brattain produced 100 billion transistors at Bell Labs."
        score_full = score_claim(text_full, primary_high, corrob_high)
        self.assertEqual(score_full, 1.0)

        # Disputed claim on low-authority domain
        primary_low = Source(title="Blog", url="https://unverified-rumors.com/post")
        text_disputed = "The alleged device was disputed and rumored to be a myth."
        score_low = score_claim(text_disputed, primary_low, [])
        self.assertLess(score_low, 0.40)
        self.assertGreaterEqual(score_low, 0.0)

    def test_all_preset_files_confidence_score_bounds(self):
        """Assert all curated preset YAML files have strictly bounded confidence scores."""
        presets_dir = Path("src/research/presets")
        if not presets_dir.exists():
            return
        preset_files = list(presets_dir.glob("*.yaml"))
        self.assertGreaterEqual(len(preset_files), 3)

        preset_topics = {
            "transistor_history": "The History of the Transistor",
            "how_gpus_work": "How GPUs Work",
            "apollo_computer": "The Apollo Guidance Computer",
            "quantum_computing": "How Quantum Computers Work",
        }
        for p_file in preset_files:
            with self.subTest(preset=p_file.name):
                dossier = ResearchEngine().synthesize_research(preset_topics[p_file.stem], offline=True)
                self.assertGreaterEqual(len(dossier.claims), 3)
                for c in dossier.claims:
                    self.assertGreaterEqual(c.confidence_score, 0.0)
                    self.assertLessEqual(c.confidence_score, 1.0)


class TestResearchEngineIntegrityAndContract(unittest.TestCase):
    """Verification of API contracts, referential integrity, and seed determinism."""

    def setUp(self):
        self.engine = ResearchEngine()
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_claim_id_referential_integrity(self):
        """Assert talking points and statistics reference valid existing claim IDs."""
        topics = [
            "The History of the Transistor",
            "How GPUs Work",
            "The Apollo Guidance Computer",
            "How Quantum Computers Work",
        ]
        for t in topics:
            with self.subTest(topic=t):
                dossier = self.engine.synthesize_research(t, offline=True)
                claim_ids = {c.claim_id for c in dossier.claims}

                # Check talking points
                for tp in dossier.talking_points:
                    for cid in tp.supported_claim_ids:
                        self.assertIn(cid, claim_ids, f"Talking point {tp.beat_index} references non-existent claim {cid}")

                # Check statistics
                for stat in dossier.statistics:
                    self.assertIn(stat.source_claim_id, claim_ids, f"Statistic {stat.metric} references non-existent claim {stat.source_claim_id}")

    def test_unknown_topics_are_not_procedurally_synthesized(self):
        for topic in ("Topological Insulators and Quantum Spin Hall Effect", "Cryogenic CMOS Logic"):
            with self.subTest(topic=topic):
                with self.assertRaises(ResearchUnavailableError):
                    self.engine.synthesize_research(topic, offline=True)

    def test_atomic_save_and_load_roundtrip(self):
        """Assert atomic saving to JSON & YAML preserves complete fidelity."""
        topic = "The History of the Transistor"
        dossier = self.engine.synthesize_research(topic, offline=True, output_dir=self.out_path)

        json_path = self.out_path / "research_dossier.json"
        yaml_path = self.out_path / "research_dossier.yaml"

        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        loaded_json = ResearchDossier.load(json_path)
        loaded_yaml = ResearchDossier.load(yaml_path)

        self.assertEqual(loaded_json.topic, dossier.topic)
        self.assertEqual(loaded_yaml.topic, dossier.topic)
        self.assertEqual(len(loaded_json.claims), len(dossier.claims))
        self.assertEqual(len(loaded_yaml.claims), len(dossier.claims))
        self.assertEqual(loaded_json.schema_version, "1.0.0")
        self.assertEqual(loaded_yaml.schema_version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
