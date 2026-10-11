"""Fail-closed regression checks for Harness 9 research inputs."""

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from src.models.dossier import Claim, Source
from src.research.engine import (
    InsufficientEvidenceError,
    ResearchEngine,
    ResearchUnavailableError,
)
from src.research.providers import SearchResult


class TestResearchIntegrity(unittest.TestCase):
    def test_unknown_offline_topic_fails_with_available_presets(self):
        engine = ResearchEngine()

        with self.assertRaises(ResearchUnavailableError) as raised:
            engine.synthesize_research("A new topic without a preset", offline=True)

        self.assertIn("The History of the Transistor", str(raised.exception))
        self.assertIn("Use online research", str(raised.exception))

    def test_live_search_with_one_claim_does_not_pad_the_dossier(self):
        engine = ResearchEngine()
        result = SearchResult(
            title="Example source",
            url="https://example.org/research",
            snippet=(
                "This single source contains one sufficiently long sentence about a topic, "
                "but does not provide enough independent claims for a research dossier."
            ),
            source_domain="example.org",
        )

        with patch.object(engine.dispatcher, "search", return_value=[result]):
            with self.assertRaises(InsufficientEvidenceError):
                engine.synthesize_research("A new topic", offline=False)

    def test_live_claim_filter_rejects_related_but_different_computer_systems(self):
        engine = ResearchEngine()
        self.assertFalse(
            engine._claim_matches_topic(
                "AP-101 computers were used in the Space Shuttle.",
                "Apollo Guidance Computer",
            )
        )
        self.assertTrue(
            engine._claim_matches_topic(
                "The Apollo Guidance Computer (AGC) was installed in Apollo spacecraft.",
                "Apollo Guidance Computer",
            )
        )

    def test_curated_preset_has_source_urls_and_reviewed_claims_are_marked_verified(self):
        dossier = ResearchEngine().synthesize_research(
            "The History of the Transistor", offline=True
        )

        self.assertEqual(dossier.metadata.mode, "curated_preset")
        self.assertTrue(dossier.claims)
        for claim in dossier.claims:
            self.assertTrue(claim.primary_source.url.startswith("https://"))
            self.assertGreaterEqual(claim.confidence_score, 0.0)
            self.assertLessEqual(claim.confidence_score, 1.0)
            self.assertEqual(claim.verification_status, "VERIFIED")

    def test_unreviewed_claim_defaults_to_unverified(self):
        claim = Claim(
            claim_id="claim_01",
            claim_text="An unreviewed claim.",
            category="technical_mechanism",
            confidence_score=0.0,
            primary_source=Source(title="Test source", url="https://example.org"),
        )
        self.assertEqual(claim.verification_status, "UNVERIFIED")

    def test_research_code_does_not_set_confidence_to_a_numeric_literal(self):
        research_dir = Path(__file__).parents[1] / "src" / "research"

        for path in research_dir.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                for keyword in node.keywords:
                    if keyword.arg == "confidence_score":
                        self.assertFalse(
                            isinstance(keyword.value, ast.Constant)
                            and isinstance(keyword.value.value, (int, float)),
                            f"{path} assigns a fixed confidence_score",
                        )


if __name__ == "__main__":
    unittest.main()
