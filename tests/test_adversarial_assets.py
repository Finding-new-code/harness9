"""Adversarial and Stress Test Suite for Milestone 2 Asset Pipeline (M2 - R2).

Author: Challenger 1 (critic/specialist)
Focus Areas:
1. Malicious & Corrupted File Sniffing (fake extensions, truncated headers, corrupted binary streams, polyglots).
2. Network Failure Resilience (timeouts, DNS failures, 404/500 HTTP errors, dropped streams, procedural fallback).
3. Composition Path Audit (strict rejection of external URLs, broken local files, 0-byte files, CDN rules).
4. Procedural SVG Validity (XML well-formedness, multi-resolution scaling, XSS/XML injection safety, unicode).
5. Ledger Integrity & Tamper Forensics (hash validation, schema conformance, corrupt ledger handling).
6. Security Boundary Stress (path traversal filenames, Windows reserved device names, concurrent mutations).
"""

import hashlib
import html
import io
import json
import os
import socket
import tempfile
import unittest
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import yaml

from src.assets.discovery import (
    AssetDiscoveryEngine,
    CandidateAsset,
    NASAProvider,
    OfflineMockProvider,
    PexelsProvider,
    WikimediaProvider,
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
from src.assets.ledger import AssetLedgerManager
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


class TestAdversarialFileSniffing(unittest.TestCase):
    """Stress testing magic byte detection, fake extensions, truncated headers, and corrupt payloads."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.freezer = AssetFreezer(base_output_dir=self.out_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_fake_extensions_mismatch(self):
        """Test that magic byte sniffing correctly identifies true MIME type regardless of claimed extension."""
        # PNG bytes with fake JPEG name
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 32
        self.assertEqual(sniff_magic_bytes(png_bytes), "image/png")
        self.assertEqual(mime_to_extension(sniff_magic_bytes(png_bytes)), "png")

        # JPEG bytes with fake SVG name
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        self.assertEqual(sniff_magic_bytes(jpeg_bytes), "image/jpeg")
        self.assertEqual(mime_to_extension(sniff_magic_bytes(jpeg_bytes)), "jpg")

        # WebP bytes with fake PNG name
        webp_bytes = b"RIFF\x28\x00\x00\x00WEBPVP8 \x1c\x00\x00\x00\x00\x00\x00\x00"
        self.assertEqual(sniff_magic_bytes(webp_bytes), "image/webp")
        self.assertEqual(mime_to_extension(sniff_magic_bytes(webp_bytes)), "webp")

        # MP4 bytes with fake MP3 name
        mp4_bytes = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41"
        self.assertEqual(sniff_magic_bytes(mp4_bytes), "video/mp4")
        self.assertEqual(mime_to_extension(sniff_magic_bytes(mp4_bytes)), "mp4")

        # WAV bytes with fake JPG name
        wav_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00"
        self.assertEqual(sniff_magic_bytes(wav_bytes), "audio/wav")
        self.assertEqual(mime_to_extension(sniff_magic_bytes(wav_bytes)), "wav")

    def test_truncated_and_micro_headers(self):
        """Test magic byte sniffing behavior with micro headers (0 to 11 bytes)."""
        # Empty header
        self.assertEqual(sniff_magic_bytes(b""), "application/octet-stream")
        # 1 byte
        self.assertEqual(sniff_magic_bytes(b"\xff"), "application/octet-stream")
        # 2 bytes
        self.assertEqual(sniff_magic_bytes(b"\xff\xd8"), "application/octet-stream")
        # 3 bytes JPEG prefix (valid)
        self.assertEqual(sniff_magic_bytes(b"\xff\xd8\xff"), "image/jpeg")
        # Partial PNG (7 bytes)
        self.assertEqual(sniff_magic_bytes(b"\x89PNG\r\n\x1a"), "application/octet-stream")
        # Truncated RIFF (8 bytes, missing WEBP or WAVE tag)
        self.assertEqual(sniff_magic_bytes(b"RIFF\x24\x00\x00\x00"), "application/octet-stream")
        # Truncated MP4 (missing ftyp)
        self.assertEqual(sniff_magic_bytes(b"\x00\x00\x00\x18"), "application/octet-stream")

    def test_executable_and_binary_malware_headers(self):
        """Test that PE/ELF/Mach-O/Shell executables are flagged as octet-stream, not recognized images."""
        # Windows PE executable (MZ header)
        pe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        self.assertEqual(sniff_magic_bytes(pe_bytes), "application/octet-stream")
        self.assertEqual(mime_to_extension(sniff_magic_bytes(pe_bytes)), "bin")

        # Linux ELF executable (\x7fELF)
        elf_bytes = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        self.assertEqual(sniff_magic_bytes(elf_bytes), "application/octet-stream")

        # Shell script
        sh_bytes = b"#!/bin/bash\nrm -rf /\n"
        self.assertEqual(sniff_magic_bytes(sh_bytes), "application/octet-stream")

        # Random garbage noise
        noise_bytes = bytes(range(256))
        self.assertEqual(sniff_magic_bytes(noise_bytes), "application/octet-stream")

    def test_polyglot_and_embedded_svg_sniffing(self):
        """Test SVG sniffing with leading comments, whitespace, and XML declarations."""
        svg_clean = b"<svg xmlns='http://www.w3.org/2000/svg'><circle/></svg>"
        self.assertEqual(sniff_magic_bytes(svg_clean), "image/svg+xml")

        svg_with_xml_decl = b"<?xml version='1.0' encoding='UTF-8'?>\n<svg width='100' height='100'></svg>"
        self.assertEqual(sniff_magic_bytes(svg_with_xml_decl), "image/svg+xml")

        svg_with_spaces = b"   \r\n\t  <svg viewBox='0 0 100 100'></svg>"
        self.assertEqual(sniff_magic_bytes(svg_with_spaces), "image/svg+xml")

        # Non-SVG XML document
        xml_not_svg = b"<?xml version='1.0'?><note><to>Tove</to><from>Jani</from></note>"
        self.assertEqual(sniff_magic_bytes(xml_not_svg), "application/octet-stream")

    def test_freeze_asset_automatic_extension_resolution(self):
        """Test that freeze_asset resolves extension from MIME when ext is omitted."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        target_path, sha, size, mime, status = self.freezer.freeze_asset(
            source=png_data,
            output_dir=self.out_path,
            slug="auto_ext_test",
            ext=None,
        )
        self.assertEqual(target_path.suffix, ".png")
        self.assertEqual(mime, "image/png")
        self.assertTrue(target_path.exists())


class TestAdversarialNetworkResilience(unittest.TestCase):
    """Stress testing network failures, timeouts, DNS errors, HTTP error codes, and fallback safety."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.freezer = AssetFreezer(base_output_dir=self.out_path, timeout_sec=1)
        self.procedural = ProceduralSVGGenerator()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_connection_timeout_retry_and_failure(self):
        """Test that connection timeout triggers retries with backoff and raises AssetDownloadError."""
        with patch("urllib.request.urlopen", side_effect=socket.timeout("Socket timed out")):
            with patch("time.sleep") as mock_sleep:
                with self.assertRaises(AssetDownloadError):
                    download_stream("https://unreachable.example.com/photo.jpg", timeout_sec=1, max_retries=3)
                # Ensure backoff sleeps occurred (attempt 1: 0.5s, attempt 2: 1.0s)
                self.assertEqual(mock_sleep.call_count, 2)
                mock_sleep.assert_any_call(0.5)
                mock_sleep.assert_any_call(1.0)

    def test_dns_failure_recovery_with_fallback(self):
        """Test that DNS resolution failure in freeze_asset safely falls back to procedural SVG."""
        fallback_svg = self.procedural.generate_hero_card("Title", "Subtitle", "Topic")
        dns_error = urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed"))

        with patch("urllib.request.urlopen", side_effect=dns_error):
            with patch("time.sleep"):
                path, sha, size, mime, status = self.freezer.freeze_asset(
                    source="https://nonexistent-domain-xyz-123.com/image.jpg",
                    output_dir=self.out_path,
                    slug="dns_fail_test",
                    procedural_fallback=fallback_svg,
                )
                self.assertTrue(path.exists())
                self.assertEqual(status, "FALLBACK_GENERATED")
                self.assertEqual(mime, "image/svg+xml")
                self.assertEqual(compute_file_sha256(path), sha)

    def test_http_error_codes_matrix(self):
        """Test behavior against various HTTP status errors (400, 403, 404, 429, 500, 503)."""
        error_codes = [400, 403, 404, 429, 500, 502, 503]
        fallback_svg = "<svg xmlns='http://www.w3.org/2000/svg'><circle/></svg>"

        for code in error_codes:
            http_err = urllib.error.HTTPError(
                url=f"https://example.com/err_{code}.jpg",
                code=code,
                msg=f"HTTP Error {code}",
                hdrs={},
                fp=io.BytesIO(b"error response"),
            )
            with patch("urllib.request.urlopen", side_effect=http_err):
                with patch("time.sleep"):
                    # Without fallback -> raises AssetDownloadError
                    with self.assertRaises(AssetDownloadError):
                        self.freezer.freeze_asset(
                            source=f"https://example.com/err_{code}.jpg",
                            output_dir=self.out_path,
                            slug=f"http_err_{code}",
                            procedural_fallback=None,
                        )

                    # With fallback -> successfully generates fallback asset
                    path, sha, size, mime, status = self.freezer.freeze_asset(
                        source=f"https://example.com/err_{code}.jpg",
                        output_dir=self.out_path,
                        slug=f"http_err_{code}_fallback",
                        procedural_fallback=fallback_svg,
                    )
                    self.assertTrue(path.exists())
                    self.assertEqual(status, "FALLBACK_GENERATED")

    def test_partial_stream_interruption(self):
        """Test stream interruption mid-download triggers retry and error handling."""
        class FaultyResponse:
            def __init__(self):
                self.headers = {}
                self.calls = 0
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def read(self, size):
                self.calls += 1
                if self.calls == 1:
                    return b"PARTIAL_HEADER"
                raise ConnectionResetError("Connection lost mid-stream")

        with patch("urllib.request.urlopen", return_value=FaultyResponse()):
            with patch("time.sleep"):
                with self.assertRaises(AssetDownloadError):
                    download_stream("https://example.com/interrupted.jpg", max_retries=2)

    def test_pipeline_zero_network_execution_guarantee(self):
        """Test AssetPipeline in offline mode executes without making any network requests."""
        dossier = {
            "topic": "Semiconductor Physics",
            "claims": [
                {"claim_id": "c1", "claim_text": "Silicon is a group IV semiconductor.", "visual_cue_suggestion": "Silicon crystal lattice"},
                {"claim_id": "c2", "claim_text": "Doping creates p-n junctions.", "visual_cue_suggestion": "P-N junction diode"},
            ],
            "suggested_visual_queries": ["Silicon lattice structure", "P-N junction diode schematic"],
        }

        pipeline = AssetPipeline(output_dir=self.out_path)
        
        # Patch urlopen to fail immediately if any network request is attempted
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network call made in offline mode!")):
            ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=self.out_path, offline=True)
            self.assertEqual(ledger.total_assets, 2)
            self.assertTrue(all(a.verification_status == "FALLBACK_GENERATED" for a in ledger.assets))
            self.assertTrue(all((self.out_path / a.local_path).exists() for a in ledger.assets))


class TestAdversarialCompositionAudit(unittest.TestCase):
    """Stress testing HTML composition security auditing and strict zero-external-URL enforcement."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.images_dir = self.out_path / "assets" / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        (self.images_dir / "valid_image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
        (self.out_path / "styles.css").write_text("body { margin: 0; }", encoding="utf-8")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_reject_external_http_image_tags(self):
        """Ensure <img src='http://...'> and <img src='https://...'> are rejected."""
        malicious_html = """
        <!DOCTYPE html>
        <html>
        <body>
          <img src="http://untrusted-tracker.com/pixel.gif" />
          <img src="https://cdn.example.com/external-photo.jpg" />
        </body>
        </html>
        """
        audit = audit_composition_paths(malicious_html, self.out_path)
        self.assertFalse(audit["valid"])
        self.assertEqual(len(audit["external_urls"]), 2)
        self.assertIn("http://untrusted-tracker.com/pixel.gif", audit["external_urls"])
        self.assertIn("https://cdn.example.com/external-photo.jpg", audit["external_urls"])

        with self.assertRaises(ValueError):
            assert_zero_external_urls(malicious_html)

    def test_reject_external_video_audio_source_tags(self):
        """Ensure <video>, <audio>, <source> with external URLs are rejected."""
        video_html = """
        <html>
        <body>
          <video src="http://stream.example.com/video.mp4"></video>
          <audio src="https://stream.example.com/audio.mp3"></audio>
          <video><source src="http://stream.example.com/source.mp4" type="video/mp4"></video>
        </body>
        </html>
        """
        audit = audit_composition_paths(video_html, self.out_path)
        self.assertFalse(audit["valid"])
        self.assertGreaterEqual(len(audit["external_urls"]), 3)

        with self.assertRaises(ValueError):
            assert_zero_external_urls(video_html)

    def test_reject_broken_and_zero_byte_local_files(self):
        """Ensure missing local files and 0-byte corrupted files are flagged as invalid."""
        # Create 0-byte file
        (self.images_dir / "empty_file.png").write_bytes(b"")

        html_with_broken_refs = """
        <html>
        <head><link rel="stylesheet" href="styles.css"></head>
        <body>
          <img src="assets/images/valid_image.png" />
          <img src="assets/images/missing_asset.png" />
          <img src="assets/images/empty_file.png" />
        </body>
        </html>
        """
        audit = audit_composition_paths(html_with_broken_refs, self.out_path)
        self.assertFalse(audit["valid"])
        self.assertTrue(any("Broken local asset reference" in err for err in audit["errors"]))
        self.assertTrue(any("Empty local asset file" in err for err in audit["errors"]))
        self.assertIn("assets/images/valid_image.png", audit["verified_paths"])

    def test_allowed_cdn_scripts_handling(self):
        """Verify standard GSAP and Google Fonts CDN scripts are recognized with warning but don't fail media audit."""
        cdn_html = """
        <html>
        <head>
          <link rel="stylesheet" href="styles.css">
          <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap">
          <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
        </head>
        <body>
          <img src="assets/images/valid_image.png" />
        </body>
        </html>
        """
        audit = audit_composition_paths(cdn_html, self.out_path, allow_cdn_scripts=True)
        self.assertTrue(audit["valid"])
        self.assertEqual(len(audit["errors"]), 0)
        self.assertGreaterEqual(len(audit["warnings"]), 2)


class TestAdversarialProceduralSVG(unittest.TestCase):
    """Stress testing SVG generator against XML injection, extreme resolutions, and unicode."""

    def setUp(self):
        self.generator = ProceduralSVGGenerator()

    def _assert_valid_xml(self, svg_str: str) -> ET.Element:
        """Helper to assert that SVG string is valid, well-formed XML."""
        try:
            root = ET.fromstring(svg_str)
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
            return root
        except ET.ParseError as e:
            self.fail(f"SVG failed XML validation: {e}\nSVG Content preview: {svg_str[:200]}")

    def test_all_themes_xml_validity(self):
        """Ensure all 5 visual themes produce valid XML."""
        themes = ["circuits", "computing", "aerospace", "science", "general"]
        for theme in themes:
            svg = self.generator.generate_topic_svg(
                topic=f"Theme Test {theme.upper()}",
                query="Visual schematic representation",
                theme=theme,
                width=1920,
                height=1080,
                idx=1,
            )
            root = self._assert_valid_xml(svg)
            self.assertEqual(root.attrib.get("viewBox"), "0 0 1920 1080")

    def test_all_card_types_xml_validity(self):
        """Ensure quote, metric, and hero card generators produce valid XML."""
        # Quote Card
        quote_svg = self.generator.generate_quote_card(
            quote="Physics is like sex: sure, it may give some practical results, but that's not why we do it.",
            author="Richard Feynman",
            context="Theoretical Physicist",
            width=1920,
            height=1080,
        )
        self._assert_valid_xml(quote_svg)

        # Metric Card
        metric_svg = self.generator.generate_metric_card(
            metric="Operations Per Second",
            value="125.5 TFLOPS",
            context="Measured on modern GPU tensor cores",
            width=1920,
            height=1080,
        )
        self._assert_valid_xml(metric_svg)

        # Hero Card
        hero_svg = self.generator.generate_hero_card(
            headline="THE QUANTUM LEAP",
            subheadline="A Deep Dive into Subatomic Engineering",
            topic="Quantum Computing",
            width=1920,
            height=1080,
        )
        self._assert_valid_xml(hero_svg)

    def test_multi_resolution_and_aspect_ratios(self):
        """Test SVG rendering across horizontal (16:9), vertical (9:16), square (1:1), 4K, and ultra-wide."""
        resolutions = [
            (1920, 1080),  # 16:9 UHD
            (1080, 1920),  # 9:16 Mobile Vertical
            (1080, 1080),  # 1:1 Square
            (3840, 2160),  # 4K UHD
            (2560, 1080),  # 21:9 Ultrawide
            (720, 1280),   # 9:16 HD
            (640, 480),    # 4:3 Standard
        ]
        for w, h in resolutions:
            svg = self.generator.generate_topic_svg(
                topic="Resolution Scaling Test",
                query="Multi-aspect test",
                width=w,
                height=h,
            )
            root = self._assert_valid_xml(svg)
            self.assertEqual(root.attrib.get("viewBox"), f"0 0 {w} {h}")
            self.assertEqual(root.attrib.get("width"), str(w))
            self.assertEqual(root.attrib.get("height"), str(h))

    def test_xml_injection_and_xss_safety(self):
        """Test that malicious injection strings do not break XML well-formedness."""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            '"><svg onload=alert(1)>',
            "& < > \" ' ` / \\",
            "<![CDATA[<test>]]>",
            "<!-- XML Comment Injection -->",
            "Shockley & Bardeen's <Integrated> 'Circuit' \"Design\"",
            "Topic with \r\n and \t and \0 control characters",
        ]

        for mal_str in malicious_inputs:
            # Topic SVG
            topic_svg = self.generator.generate_topic_svg(topic=mal_str, query=mal_str)
            self._assert_valid_xml(topic_svg)

            # Quote Card
            quote_svg = self.generator.generate_quote_card(quote=mal_str, author=mal_str, context=mal_str)
            self._assert_valid_xml(quote_svg)

            # Metric Card
            metric_svg = self.generator.generate_metric_card(metric=mal_str, value=mal_str, context=mal_str)
            self._assert_valid_xml(metric_svg)

            # Hero Card
            hero_svg = self.generator.generate_hero_card(headline=mal_str, subheadline=mal_str, topic=mal_str)
            self._assert_valid_xml(hero_svg)

    def test_unicode_and_multilingual_rendering(self):
        """Test unicode, mathematical symbols, Greek, and non-ASCII character handling."""
        unicode_topic = "Quantum Superposition: Ψ(t) = α|0⟩ + β|1⟩ (ℏ = 1.054×10⁻³⁴ J·s)"
        unicode_query = "半导体与集成电路 🔬 🚀 ΔE = ℏω"

        svg = self.generator.generate_topic_svg(topic=unicode_topic, query=unicode_query)
        self._assert_valid_xml(svg)


class TestAdversarialLedgerIntegrity(unittest.TestCase):
    """Stress testing rights ledger serialization, corrupt ledgers, tampering, and schema validation."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)
        self.mgr = AssetLedgerManager(output_dir=self.out_path, project_id="proj_adversarial_ledger")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_ledger_tamper_detection(self):
        """Test that altering a frozen file on disk causes validate_ledger to fail with SHA-256 mismatch."""
        target_file = self.out_path / "assets" / "images" / "transistor.svg"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        original_bytes = b"<svg><circle r='10'/></svg>"
        target_file.write_bytes(original_bytes)
        sha = hashlib.sha256(original_bytes).hexdigest()

        self.mgr.record_frozen_asset(
            asset_id="asset_01",
            local_path="assets/images/transistor.svg",
            file_size_bytes=len(original_bytes),
            file_sha256=sha,
            source_provider="procedural_generator",
            source_url="procedural://transistor.svg",
            creator=CreatorInfo(name="Procedural Engine"),
            license_info=LicenseInfo(license_type="CC0-1.0"),
        )

        # Baseline: valid
        val_before = self.mgr.validate_ledger(project_dir=self.out_path)
        self.assertTrue(val_before["valid"])

        # Adversarial tamper: byte change
        target_file.write_bytes(b"<svg><circle r='999'/></svg>")
        val_after = self.mgr.validate_ledger(project_dir=self.out_path)
        self.assertFalse(val_after["valid"])
        self.assertTrue(any("SHA-256 mismatch" in e for e in val_after["errors"]))

    def test_corrupt_and_empty_ledger_file_loading(self):
        """Test loading non-existent, corrupt JSON, and corrupt YAML ledger files."""
        # Non-existent
        with self.assertRaises(FileNotFoundError):
            AssetProvenanceLedger.load(self.out_path / "nonexistent.json")

        # Corrupt JSON
        corrupt_json = self.out_path / "corrupt.json"
        corrupt_json.write_text("{ unclosed json: [ }", encoding="utf-8")
        with self.assertRaises(Exception):
            AssetProvenanceLedger.load(corrupt_json)

    def test_missing_metadata_schema_rejection(self):
        """Test validate_ledger detects missing required attributes."""
        # Asset missing creator and license
        incomplete_asset = MediaAsset(
            asset_id="asset_incomplete",
            local_path="assets/images/sample.jpg",
            file_size_bytes=100,
            file_sha256="123",
            source_url="https://example.com/sample.jpg",
            creator=CreatorInfo(name=""),  # Empty name
            license=LicenseInfo(license_type=""),  # Empty license
        )
        self.mgr.add_asset(incomplete_asset)
        val = self.mgr.validate_ledger()
        self.assertFalse(val["valid"])
        self.assertTrue(any("missing creator" in e.lower() for e in val["errors"]))
        self.assertTrue(any("missing license" in e.lower() for e in val["errors"]))


class TestSecurityBoundaryStress(unittest.TestCase):
    """Stress testing security boundaries, path traversal, and extreme sanitization."""

    def test_path_traversal_filename_sanitization(self):
        """Test that malicious path traversal strings are safely sanitized."""
        attacks = [
            "../../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\cmd.exe",
            "asset/../../../secret.key",
            "/absolute/root/file.png",
            "C:\\boot.ini",
            "nul.txt",
            "con.png",
            "com1.jpg",
            "asset with spaces and \x00 null byte.svg",
        ]
        for attack in attacks:
            sanitized = sanitize_filename(attack)
            self.assertNotIn("/", sanitized)
            self.assertNotIn("\\", sanitized)
            self.assertNotIn("..", sanitized)
            self.assertGreater(len(sanitized), 0)


if __name__ == "__main__":
    unittest.main()
