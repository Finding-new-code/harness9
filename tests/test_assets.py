"""Comprehensive Unit & Boundary Tests for R2 Asset Discovery, Rights Ledger & Local Freezing.

Covers:
- Tier 1: Feature Coverage (F3 Discovery, F4 Freezing & Ledger, F5 Procedural SVGs, Pipeline Integration)
- Tier 2: Boundary & Edge Cases (Corrupt files, zero network, missing metadata, scaling, deduplication, large files, special characters, XML sanitization, empty queries, SHA tamper detection, size limits, composition auditing)
"""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import yaml

from src.assets.discovery import (
    AssetDiscoveryEngine,
    CandidateAsset,
    NASAProvider,
    OfflineMockProvider,
    PexelsProvider,
    WikimediaProvider,
    _strip_html,
)
from src.assets.freezer import (
    AssetChecksumMismatchError,
    AssetDownloadError,
    AssetFreezer,
    AssetSizeExceededError,
    assert_zero_external_urls,
    audit_composition_paths,
    compute_file_sha256,
    compute_sha256,
    download_stream,
    mime_to_extension,
    sanitize_filename,
    sniff_magic_bytes,
    verify_sha256,
)
from src.assets.ledger import AssetLedgerManager, LedgerManager
from src.assets.pipeline import AssetPipeline
from src.assets.procedural import ProceduralSVGGenerator
from src.config import AppConfig
from src.models.dossier import Claim, DossierMetadata, ResearchDossier, Source, Summary, TalkingPoint
from src.models.ledger import (
    AssetProvenanceLedger,
    CreatorInfo,
    Dimensions,
    LicenseInfo,
    MediaAsset,
)


class TestAssetDiscovery(unittest.TestCase):
    """F3: Media Discovery across Wikimedia, Pexels, NASA, and Offline Fallback."""

    def test_strip_html_utility(self):
        """Test HTML entity and tag stripping."""
        raw = '<a href="https://example.com"><b>John Doe</b></a> &amp; Co.'
        self.assertEqual(_strip_html(raw), "John Doe & Co.")
        self.assertEqual(_strip_html(""), "")
        self.assertEqual(_strip_html(None), "")

    def test_candidate_asset_to_media_asset_conversion(self):
        """Test conversion from candidate asset to MediaAsset dataclass."""
        cand = CandidateAsset(
            title="Point Contact Transistor",
            source_provider="wikimedia_commons",
            source_url="https://commons.wikimedia.org/wiki/File:Transistor.jpg",
            page_url="https://commons.wikimedia.org/wiki/File:Transistor.jpg",
            media_type="image/jpeg",
            width=1920,
            height=1080,
            creator_name="Bell Labs",
            creator_profile_url="https://bell-labs.com",
            license_type="Public Domain",
            attribution_text="Bell Labs, Public Domain",
            attribution_required=False,
            commercial_use_allowed=True,
            modification_allowed=True,
            query_matched="transistor 1947",
        )
        media_asset = cand.to_media_asset(
            asset_id="asset_01",
            local_path="assets/images/transistor.jpg",
            file_size_bytes=1024,
            file_sha256="abc12345" * 8,
            scene_target="scene_1",
            claim_id_refs=["claim_01"],
            verification_status="FROZEN_LOCAL",
        )
        self.assertEqual(media_asset.asset_id, "asset_01")
        self.assertEqual(media_asset.local_path, "assets/images/transistor.jpg")
        self.assertEqual(media_asset.dimensions.width, 1920)
        self.assertEqual(media_asset.dimensions.height, 1080)
        self.assertEqual(media_asset.dimensions.aspect_ratio, "16:9")
        self.assertEqual(media_asset.creator.name, "Bell Labs")
        self.assertEqual(media_asset.license.license_type, "Public Domain")
        self.assertEqual(media_asset.claim_id_refs, ["claim_01"])

    def test_offline_mock_provider_benchmark_catalog(self):
        """Test OfflineMockProvider returns accurate domain-matched candidates."""
        provider = OfflineMockProvider()

        # Transistor query
        results = provider.search("The History of the Transistor Bell Labs", limit=3)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].source_provider, "offline_mock")
        self.assertIn("transistor", results[0].title.lower())

        # GPU query
        gpu_results = provider.search("GPU parallel compute microarchitecture", limit=2)
        self.assertGreaterEqual(len(gpu_results), 1)
        self.assertIn("gpu", gpu_results[0].title.lower())

        # Apollo query
        apollo_results = provider.search("Apollo 11 guidance computer DSKY", limit=1)
        self.assertEqual(len(apollo_results), 1)
        self.assertIn("apollo", apollo_results[0].title.lower())

        # Procedural fallback query
        generic_results = provider.search("Quantum Supercomputing Entanglement Qubits", limit=2)
        self.assertGreaterEqual(len(generic_results), 1)
        self.assertIsNotNone(generic_results[0].license_type)

    def test_wikimedia_provider_parsing(self):
        """Test WikimediaProvider JSON response parsing and ExtMetadata handling."""
        mock_payload = {
            "query": {
                "pages": {
                    "12345": {
                        "pageid": 12345,
                        "title": "File:First_Transistor.jpg",
                        "fullurl": "https://commons.wikimedia.org/wiki/File:First_Transistor.jpg",
                        "imageinfo": [
                            {
                                "thumburl": "https://upload.wikimedia.org/thumb/First_Transistor.jpg",
                                "thumbwidth": 1920,
                                "thumbheight": 1080,
                                "mime": "image/jpeg",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
                                    "Artist": {"value": "<span>Walter Brattain</span>"},
                                    "Credit": {"value": "Bell Labs Archives"},
                                },
                            }
                        ],
                    }
                }
            }
        }

        provider = WikimediaProvider()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            candidates = provider.search("transistor", limit=2)
            self.assertEqual(len(candidates), 1)
            c = candidates[0]
            self.assertEqual(c.creator_name, "Walter Brattain")
            self.assertEqual(c.license_type, "CC BY-SA 4.0")
            self.assertTrue(c.attribution_required)
            self.assertTrue(c.commercial_use_allowed)
            self.assertEqual(c.source_url, "https://upload.wikimedia.org/thumb/First_Transistor.jpg")

    def test_pexels_provider_parsing(self):
        """Test PexelsProvider REST response and licensing extraction."""
        mock_payload = {
            "photos": [
                {
                    "id": 998877,
                    "width": 1920,
                    "height": 1080,
                    "url": "https://www.pexels.com/photo/microchip-998877/",
                    "photographer": "Tech Photographer",
                    "photographer_url": "https://www.pexels.com/@techphoto",
                    "src": {
                        "large2x": "https://images.pexels.com/photos/998877/pexels-photo-998877.jpeg",
                    },
                }
            ]
        }

        provider = PexelsProvider(api_key="test_pexels_key")
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            candidates = provider.search("microchip", limit=1)
            self.assertEqual(len(candidates), 1)
            c = candidates[0]
            self.assertEqual(c.creator_name, "Tech Photographer")
            self.assertEqual(c.license_type, "Pexels License")
            self.assertFalse(c.attribution_required)
            self.assertTrue(c.commercial_use_allowed)

    def test_nasa_provider_parsing(self):
        """Test NASA Image & Video Library provider parsing."""
        mock_payload = {
            "collection": {
                "items": [
                    {
                        "data": [
                            {
                                "title": "Apollo Guidance Computer DSKY",
                                "nasa_id": "AS11-40-5874",
                                "center": "JSC",
                                "photographer": "NASA JSC",
                                "description": "Apollo guidance computer display unit",
                            }
                        ],
                        "links": [
                            {"href": "https://images-assets.nasa.gov/image/AS11-40-5874/AS11-40-5874~thumb.jpg"}
                        ],
                    }
                ]
            }
        }

        provider = NASAProvider()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            candidates = provider.search("apollo guidance computer", limit=1)
            self.assertEqual(len(candidates), 1)
            c = candidates[0]
            self.assertEqual(c.creator_name, "NASA JSC")
            self.assertEqual(c.license_type, "NASA Public Domain")
            self.assertTrue(c.commercial_use_allowed)

    def test_asset_discovery_engine_orchestration(self):
        """Test AssetDiscoveryEngine routing and offline mode."""
        config = AppConfig(offline_mode=True)
        engine = AssetDiscoveryEngine(config=config)
        results = engine.search_assets("point contact transistor", limit=2)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].source_provider, "offline_mock")


class TestAssetFreezerAndHashing(unittest.TestCase):
    """F4: Media Freezing, Magic Byte Sniffing, Checksums, and Relative Path Auditing."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_magic_byte_sniffing_all_formats(self):
        """Verify binary signature sniffing for JPEG, PNG, WebP, SVG, MP4, WAV, and MP3."""
        self.assertEqual(sniff_magic_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF"), "image/jpeg")
        self.assertEqual(sniff_magic_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"), "image/png")
        self.assertEqual(sniff_magic_bytes(b"RIFF\x24\x00\x00\x00WEBPVP8 "), "image/webp")
        self.assertEqual(sniff_magic_bytes(b"<svg xmlns='http://www.w3.org/2000/svg'>"), "image/svg+xml")
        self.assertEqual(sniff_magic_bytes(b"<?xml version='1.0'?><svg>"), "image/svg+xml")
        self.assertEqual(sniff_magic_bytes(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00"), "video/mp4")
        self.assertEqual(sniff_magic_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt "), "audio/wav")
        self.assertEqual(sniff_magic_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x21"), "audio/mp3")
        self.assertEqual(sniff_magic_bytes(b"\xff\xfb\x90\x44"), "audio/mp3")
        self.assertEqual(sniff_magic_bytes(b"RANDOM_BYTES"), "application/octet-stream")
        self.assertEqual(sniff_magic_bytes(b""), "application/octet-stream")

    def test_mime_to_extension_mapping(self):
        """Test MIME type mapping to file extensions."""
        self.assertEqual(mime_to_extension("image/jpeg"), "jpg")
        self.assertEqual(mime_to_extension("image/png"), "png")
        self.assertEqual(mime_to_extension("image/webp"), "webp")
        self.assertEqual(mime_to_extension("image/svg+xml"), "svg")
        self.assertEqual(mime_to_extension("video/mp4"), "mp4")
        self.assertEqual(mime_to_extension("audio/wav"), "wav")
        self.assertEqual(mime_to_extension("audio/mp3"), "mp3")
        self.assertEqual(mime_to_extension("unknown"), "bin")

    def test_sha256_computation_and_verification(self):
        """Test deterministic SHA-256 calculation and file validation."""
        sample_bytes = b"Harness 9 Deterministic Asset Verification Payload 2026"
        expected_sha = hashlib.sha256(sample_bytes).hexdigest()

        self.assertEqual(compute_sha256(sample_bytes), expected_sha)

        file_path = self.out_path / "test_sha.bin"
        file_path.write_bytes(sample_bytes)

        self.assertEqual(compute_file_sha256(file_path), expected_sha)
        self.assertTrue(verify_sha256(file_path, expected_sha))
        self.assertFalse(verify_sha256(file_path, "0" * 64))

    def test_freeze_bytes_and_tamper_detection(self):
        """Test freezing raw bytes to disk and tamper detection."""
        freezer = AssetFreezer()
        sample_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        target = self.out_path / "assets" / "images" / "test_freeze.png"

        frozen_path, sha256, size, mime = freezer.freeze_bytes(sample_png, target)
        self.assertTrue(frozen_path.exists())
        self.assertEqual(mime, "image/png")
        self.assertEqual(size, len(sample_png))
        self.assertEqual(sha256, hashlib.sha256(sample_png).hexdigest())

        # Check tamper rejection
        wrong_sha = "f" * 64
        with self.assertRaises(AssetChecksumMismatchError):
            freezer.freeze_bytes(sample_png, self.out_path / "tamper.png", expected_sha=wrong_sha)

    def test_streaming_download_size_limit(self):
        """Test streaming download enforcement of 25MB safety limit."""
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Length": str(30 * 1024 * 1024)}  # 30MB
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with self.assertRaises(AssetSizeExceededError):
                download_stream("https://example.com/oversized.jpg", max_size_bytes=25 * 1024 * 1024)

    def test_freeze_asset_with_procedural_fallback(self):
        """Test freeze_asset handles network failure with procedural fallback."""
        freezer = AssetFreezer()
        procedural_svg = "<svg xmlns='http://www.w3.org/2000/svg'><circle cx='10' cy='10' r='5'/></svg>"

        # Simulate failed download
        with patch("urllib.request.urlopen", side_effect=Exception("Connection Refused")):
            frozen_path, sha256, size, mime, status = freezer.freeze_asset(
                source="https://example.com/broken.jpg",
                output_dir=self.out_path,
                slug="broken_fallback_test",
                procedural_fallback=procedural_svg,
            )
            self.assertTrue(frozen_path.exists())
            self.assertEqual(status, "FALLBACK_GENERATED")
            self.assertEqual(mime, "image/svg+xml")

    def test_composition_path_auditor(self):
        """Test audit_composition_paths detects remote URLs and broken local files."""
        # Create a valid local asset
        images_dir = self.out_path / "assets" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        (images_dir / "hero.svg").write_text("<svg></svg>", encoding="utf-8")

        # HTML with valid local asset
        valid_html = """
        <!DOCTYPE html>
        <html>
        <head><link rel="stylesheet" href="styles.css"></head>
        <body>
          <img src="assets/images/hero.svg" />
          <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
        </body>
        </html>
        """
        # Create dummy styles.css
        (self.out_path / "styles.css").write_text("body {}", encoding="utf-8")

        audit_res = audit_composition_paths(valid_html, self.out_path)
        self.assertTrue(audit_res["valid"])
        self.assertIn("assets/images/hero.svg", audit_res["verified_paths"])

        # HTML with illegal external image URL
        invalid_html = """
        <html>
        <body>
          <img src="https://external.com/photo.jpg" />
          <img src="assets/images/missing_file.png" />
        </body>
        </html>
        """
        audit_invalid = audit_composition_paths(invalid_html, self.out_path)
        self.assertFalse(audit_invalid["valid"])
        self.assertGreaterEqual(len(audit_invalid["errors"]), 2)
        self.assertIn("https://external.com/photo.jpg", audit_invalid["external_urls"])

        # Test assert_zero_external_urls
        with self.assertRaises(ValueError):
            assert_zero_external_urls(invalid_html)
        self.assertTrue(assert_zero_external_urls(valid_html))


class TestAssetLedgerManager(unittest.TestCase):
    """F4: Asset Provenance Ledger Creation, Validation, and Dual JSON/YAML Serialization."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_ledger_creation_and_mutation(self):
        """Test AssetLedgerManager adds, retrieves, lists, and removes assets."""
        mgr = AssetLedgerManager(output_dir=self.out_path, project_id="proj_test_100")
        self.assertEqual(mgr.ledger.project_id, "proj_test_100")

        asset = MediaAsset(
            asset_id="asset_01",
            local_path="assets/images/asset_01.svg",
            claim_id_refs=["claim_01"],
            scene_target="scene_1",
            media_type="image/svg+xml",
            file_size_bytes=2048,
            file_sha256="abc12345" * 8,
            dimensions=Dimensions(width=1920, height=1080),
            source_provider="wikimedia_commons",
            source_url="https://commons.wikimedia.org/wiki/File:Transistor.svg",
            creator=CreatorInfo(name="Test Creator"),
            license=LicenseInfo(license_type="CC-BY-4.0", attribution_required=True),
            verification_status="FROZEN_LOCAL",
        )

        mgr.add_asset(asset)
        self.assertEqual(mgr.ledger.total_assets, 1)
        self.assertEqual(mgr.ledger.license_summary.get("CC-BY-4.0"), 1)
        self.assertIsNotNone(mgr.get_asset("asset_01"))

        # Remove asset
        removed = mgr.remove_asset("asset_01")
        self.assertTrue(removed)
        self.assertEqual(mgr.ledger.total_assets, 0)

    def test_dual_json_and_yaml_serialization(self):
        """Test saving and loading AssetProvenanceLedger to/from JSON and YAML."""
        mgr = AssetLedgerManager(output_dir=self.out_path, project_id="proj_serialization_test")
        mgr.record_frozen_asset(
            asset_id="asset_01",
            local_path="assets/images/sample.jpg",
            file_size_bytes=4096,
            file_sha256="12345678" * 8,
            media_type="image/jpeg",
            dimensions=Dimensions(width=1920, height=1080),
            source_provider="wikimedia_commons",
            source_url="https://commons.wikimedia.org/wiki/sample.jpg",
            creator=CreatorInfo(name="John Doe"),
            license_info=LicenseInfo(license_type="Public Domain"),
            scene_target="scene_1",
            claim_id_refs=["claim_01"],
        )

        json_path, yaml_path = mgr.save(self.out_path, base_name="asset_ledger")
        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        # Load JSON
        loaded_json = AssetProvenanceLedger.load(json_path)
        self.assertEqual(loaded_json.project_id, "proj_serialization_test")
        self.assertEqual(loaded_json.total_assets, 1)
        self.assertEqual(loaded_json.assets[0].asset_id, "asset_01")

        # Load YAML
        loaded_yaml = AssetProvenanceLedger.load(yaml_path)
        self.assertEqual(loaded_yaml.project_id, "proj_serialization_test")
        self.assertEqual(loaded_yaml.total_assets, 1)
        self.assertEqual(loaded_yaml.assets[0].creator.name, "John Doe")

    def test_ledger_validation_against_disk(self):
        """Test validate_ledger verifies on-disk files and SHA-256 match."""
        mgr = AssetLedgerManager(output_dir=self.out_path, project_id="proj_disk_val")
        target_file = self.out_path / "assets" / "images" / "test_val.svg"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        content = b"<svg>Test Content</svg>"
        target_file.write_bytes(content)
        correct_sha = hashlib.sha256(content).hexdigest()

        mgr.record_frozen_asset(
            asset_id="asset_val_01",
            local_path="assets/images/test_val.svg",
            file_size_bytes=len(content),
            file_sha256=correct_sha,
            source_provider="procedural_generator",
            source_url="procedural://test",
            creator=CreatorInfo(name="Procedural Engine"),
            license_info=LicenseInfo(license_type="CC0-1.0"),
        )

        # Validation passes
        res_ok = mgr.validate_ledger(project_dir=self.out_path)
        self.assertTrue(res_ok["valid"])
        self.assertEqual(len(res_ok["errors"]), 0)

        # Tamper with file
        target_file.write_bytes(b"<svg>TAMPERED</svg>")
        res_tampered = mgr.validate_ledger(project_dir=self.out_path)
        self.assertFalse(res_tampered["valid"])
        self.assertTrue(any("SHA-256 mismatch" in err for err in res_tampered["errors"]))


class TestProceduralSVGGenerator(unittest.TestCase):
    """F5: Procedural SVG Graphics, Aspect Ratios, Typographic & Metric Cards."""

    def setUp(self):
        self.generator = ProceduralSVGGenerator()

    def test_theme_classification(self):
        """Test topic text classification into visual themes."""
        self.assertEqual(self.generator.classify_theme("The History of the Transistor"), "circuits")
        self.assertEqual(self.generator.classify_theme("Silicon wafer fabrication semiconductors"), "circuits")
        self.assertEqual(self.generator.classify_theme("How GPUs Work: Parallel Computing"), "computing")
        self.assertEqual(self.generator.classify_theme("Apollo 11 Guidance Computer DSKY NASA"), "aerospace")
        self.assertEqual(self.generator.classify_theme("Quantum Computing Superposition Qubits"), "science")
        self.assertEqual(self.generator.classify_theme("The Architecture of Modern Skyscrapers"), "general")

    def test_generate_topic_svg_16_9_and_9_16(self):
        """Test generation of 1920x1080 (16:9) and 1080x1920 (9:16) SVGs."""
        svg_16_9 = self.generator.generate_topic_svg(
            topic="The History of the Transistor",
            query="1947 Bell Labs point contact",
            width=1920,
            height=1080,
        )
        self.assertTrue(svg_16_9.startswith("<svg"))
        self.assertTrue(svg_16_9.endswith("</svg>"))
        self.assertIn('viewBox="0 0 1920 1080"', svg_16_9)
        self.assertIn("The History of the Transistor", svg_16_9)

        svg_9_16 = self.generator.generate_topic_svg(
            topic="GPU Compute Units",
            query="Parallel Streaming Multiprocessors",
            width=1080,
            height=1920,
        )
        self.assertTrue(svg_9_16.startswith("<svg"))
        self.assertTrue(svg_9_16.endswith("</svg>"))
        self.assertIn('viewBox="0 0 1080 1920"', svg_9_16)

    def test_generate_quote_card(self):
        """Test typographic quote card SVG generation."""
        quote_svg = self.generator.generate_quote_card(
            quote="The transistor was probably the most important invention of the 20th century.",
            author="Walter Brattain",
            context="Nobel Laureate in Physics, 1956",
        )
        self.assertIn("<svg", quote_svg)
        self.assertIn("Walter Brattain", quote_svg)
        self.assertIn("Nobel Laureate in Physics, 1956", quote_svg)

    def test_generate_metric_card(self):
        """Test data metric callout badge SVG generation."""
        metric_svg = self.generator.generate_metric_card(
            metric="Modern Transistor Count",
            value="100,000,000,000+",
            context="Packed per leading-edge microchip die",
        )
        self.assertIn("<svg", metric_svg)
        self.assertIn("100,000,000,000+", metric_svg)
        self.assertIn("Modern Transistor Count", metric_svg)

    def test_generate_hero_card(self):
        """Test hero visual card generation."""
        hero_svg = self.generator.generate_hero_card(
            headline="THE SILICON REVOLUTION",
            subheadline="How three physicists at Bell Labs ignited the digital age.",
            topic="The Transistor",
        )
        self.assertIn("<svg", hero_svg)
        self.assertIn("THE SILICON REVOLUTION", hero_svg)
        self.assertIn("THE TRANSISTOR", hero_svg)

    def test_xml_sanitization_and_special_characters(self):
        """Test special character escaping in SVG typography."""
        svg = self.generator.generate_topic_svg(
            topic="Shockley & Bardeen's <Invention>",
            query="Transistor \"1947\" & Microchips",
        )
        self.assertIn("Shockley &amp; Bardeen&#x27;s &lt;Invention&gt;", svg)
        self.assertIn("Transistor &quot;1947&quot; &amp; Microchips", svg)


class TestAssetPipelineIntegration(unittest.TestCase):
    """End-to-end integration tests for AssetPipeline (Stage 2)."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_discover_and_freeze_assets_offline(self):
        """Test complete Stage 2 flow with ResearchDossier input in offline mode."""
        dossier = ResearchDossier(
            topic="The History of the Transistor",
            metadata=DossierMetadata(run_id="run_test_01", mode="offline_fallback"),
            summary=Summary(
                headline="The Miracle at Bell Labs",
                executive_summary="Overview of transistor history",
                key_takeaways=["Point contact invented 1947", "Nobel Prize 1956"],
            ),
            claims=[
                Claim(
                    claim_id="claim_01",
                    claim_text="The point-contact transistor was demonstrated on Dec 23, 1947.",
                    category="origin_history",
                    confidence_score=0.98,
                    primary_source=Source(title="Bell Labs Archive", url="https://bell-labs.com/transistor"),
                    visual_cue_suggestion="Bell Labs 1947 prototype replica",
                ),
                Claim(
                    claim_id="claim_02",
                    claim_text="Bardeen, Brattain, and Shockley won the 1956 Nobel Prize.",
                    category="key_figure",
                    confidence_score=1.0,
                    primary_source=Source(title="Nobel Prize", url="https://nobelprize.org/physics/1956"),
                    visual_cue_suggestion="Bardeen Brattain Shockley workbench photo",
                ),
                Claim(
                    claim_id="claim_03",
                    claim_text="Modern microprocessors pack over 100 billion transistors.",
                    category="quantitative_metric",
                    confidence_score=0.95,
                    primary_source=Source(title="IEEE Spectrum", url="https://spectrum.ieee.org"),
                    visual_cue_suggestion="Silicon wafer microchip die circuitry",
                ),
            ],
            talking_points=[
                TalkingPoint(beat_index=1, title="Dawn", narrative_hook="Hook 1", supported_claim_ids=["claim_01"]),
                TalkingPoint(beat_index=2, title="Nobel", narrative_hook="Hook 2", supported_claim_ids=["claim_02"]),
                TalkingPoint(beat_index=3, title="Scaling", narrative_hook="Hook 3", supported_claim_ids=["claim_03"]),
            ],
            suggested_visual_queries=[
                "Point contact transistor replica",
                "Bardeen Brattain Shockley Bell Labs",
                "Silicon wafer modern microchip die",
            ],
        )

        pipeline = AssetPipeline(output_dir=self.out_path)
        ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=self.out_path, offline=True)

        self.assertIsInstance(ledger, AssetProvenanceLedger)
        self.assertEqual(ledger.total_assets, 3)
        self.assertEqual(len(ledger.assets), 3)

        # Verify that all 3 files exist on disk in assets/images/
        for asset in ledger.assets:
            disk_file = self.out_path / asset.local_path
            self.assertTrue(disk_file.exists(), f"Missing file: {disk_file}")
            self.assertGreater(disk_file.stat().st_size, 0)
            self.assertEqual(compute_file_sha256(disk_file), asset.file_sha256)
            self.assertEqual(asset.dimensions.width, 1920)
            self.assertEqual(asset.dimensions.height, 1080)
            self.assertTrue(len(asset.claim_id_refs) > 0)
            self.assertTrue(asset.scene_target.startswith("scene_"))

        # Verify ledger JSON and YAML exist on disk
        json_path = self.out_path / "asset_ledger.json"
        yaml_path = self.out_path / "asset_ledger.yaml"
        self.assertTrue(json_path.exists())
        self.assertTrue(yaml_path.exists())

        # Verify ledger contents
        loaded_json = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded_json["total_assets"], 3)
        loaded_yaml = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded_yaml["total_assets"], 3)


class TestAssetBoundaryAndEdgeCases(unittest.TestCase):
    """Tier 2 Boundary, Fault Tolerance & Edge Cases."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_sanitize_filename_edge_cases(self):
        """Test sanitize_filename cleans paths, quotes, and dangerous characters."""
        self.assertEqual(sanitize_filename("asset_01_Bell's Transistor & Shockley (1947).svg"), "asset_01_Bell_s_Transistor_Shockley_1947.svg")
        self.assertEqual(sanitize_filename("../../etc/passwd"), "etc_passwd")
        self.assertEqual(sanitize_filename("   "), "asset")

    def test_empty_search_query_handling(self):
        """Test pipeline behavior when visual queries are empty."""
        dossier_empty = {
            "topic": "Quantum Computing",
            "claims": [{"claim_id": "claim_01", "claim_text": "Qubits exist in superposition."}],
            "talking_points": [],
            "suggested_visual_queries": [],
        }
        pipeline = AssetPipeline(output_dir=self.out_path)
        ledger = pipeline.discover_and_freeze_assets(dossier_empty, output_dir=self.out_path, offline=True)
        self.assertGreaterEqual(ledger.total_assets, 1)

    def test_deduplication_of_assets(self):
        """Test deduplication logic does not duplicate identical asset records."""
        mgr = AssetLedgerManager(output_dir=self.out_path)
        asset1 = MediaAsset(
            asset_id="asset_01",
            local_path="assets/images/dup.jpg",
            file_size_bytes=100,
            file_sha256="abc",
            source_url="https://example.com/dup.jpg",
        )
        asset1_updated = MediaAsset(
            asset_id="asset_01",
            local_path="assets/images/dup_updated.jpg",
            file_size_bytes=200,
            file_sha256="def",
            source_url="https://example.com/dup.jpg",
        )
        mgr.add_asset(asset1)
        self.assertEqual(mgr.ledger.total_assets, 1)
        mgr.add_asset(asset1_updated)
        self.assertEqual(mgr.ledger.total_assets, 1)
        self.assertEqual(mgr.get_asset("asset_01").file_size_bytes, 200)

    def test_large_streaming_hash_integrity(self):
        """Test chunked SHA-256 calculation on 2MB binary payload."""
        large_path = self.out_path / "large_test.bin"
        payload = b"\xaa\xbb\xcc\xdd" * (512 * 1024)  # 2MB
        large_path.write_bytes(payload)

        computed = compute_file_sha256(large_path)
        expected = hashlib.sha256(payload).hexdigest()
        self.assertEqual(computed, expected)


if __name__ == "__main__":
    unittest.main()
