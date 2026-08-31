"""Adversarial stress-test harness by Challenger 2 for Milestone 2 (Asset Discovery, Rights Ledger & Local Freezing - R2).

Empirically tests:
1. SHA-256 Byte-Level Exactness & Tamper Detection:
   - 100% exact match between on-disk frozen assets and ledger `file_sha256` and `file_size_bytes`.
   - Verification across chunk boundaries (0B, 1B, 65535B, 65536B, 65537B, 131072B, 1MB).
   - Tamper detection on flipped bytes, truncations, file substitutions, and missing files.
2. License Metadata & Provenance Completeness:
   - Asserts non-empty `license_type`, `attribution_text`, `source_url`, and `creator.name` on 100% of assets.
   - Tests fallback procedural licensing contracts and online provider license mapping.
   - Tests `validate_ledger()` sensitivity to missing or malformed license fields.
3. Dual JSON/YAML Ledger Serialization & Roundtripping Parity:
   - Bit-accurate and schema-accurate roundtripping between Python objects, JSON strings, YAML strings, and disk files.
   - Cross-format parity (JSON vs YAML).
   - Type preservation (integers, booleans, nested dataclasses, lists, dicts).
   - Unicode, special characters, and multiline attribution stability.
4. Adversarial Edge Cases & Stress Scenarios:
   - High-load query scaling (50+ assets).
   - Malicious topic strings with path traversal injections and special characters.
   - Duplicate asset ID replacement and ledger license summary recalculation.
"""

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List
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


class TestSHA256ByteExactnessAndIntegrity(unittest.TestCase):
    """Empirical challenges for SHA-256 byte-level exactness and integrity."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_frozen_assets_sha256_exactness_100_percent(self):
        """Assert 100% of frozen assets on disk match ledger file_sha256 and byte size."""
        topics = [
            "The History of the Transistor",
            "How GPUs Work: Parallel Microarchitectures",
            "Apollo 11 Lunar Guidance Computer",
        ]

        for topic in topics:
            sub_dir = self.out_path / sanitize_filename(topic)
            dossier = ResearchDossier(
                topic=topic,
                metadata=DossierMetadata(run_id="run_sha_test", mode="offline_fallback"),
                summary=Summary(headline=f"Headline for {topic}", executive_summary="Summary", key_takeaways=["Point 1"]),
                claims=[
                    Claim(
                        claim_id=f"claim_{i+1:02d}",
                        claim_text=f"Verifiable historical claim {i+1} for {topic}.",
                        category="technical",
                        confidence_score=0.95,
                        primary_source=Source(title="Archive", url="https://example.com"),
                        visual_cue_suggestion=f"Visual asset {i+1} for {topic}",
                    )
                    for i in range(4)
                ],
                talking_points=[
                    TalkingPoint(beat_index=i+1, title=f"Beat {i+1}", narrative_hook=f"Hook {i+1}", supported_claim_ids=[f"claim_{i+1:02d}"])
                    for i in range(4)
                ],
                suggested_visual_queries=[
                    f"{topic} key diagram {i+1}" for i in range(4)
                ],
            )

            pipeline = AssetPipeline(output_dir=sub_dir)
            ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=sub_dir, offline=True)

            self.assertEqual(len(ledger.assets), 4)
            self.assertEqual(ledger.total_assets, 4)

            # Check every asset on disk
            for asset in ledger.assets:
                disk_file = sub_dir / asset.local_path
                self.assertTrue(disk_file.exists(), f"File {disk_file} does not exist on disk.")
                disk_bytes = disk_file.read_bytes()
                
                # Check SHA-256
                actual_sha = hashlib.sha256(disk_bytes).hexdigest()
                self.assertEqual(
                    actual_sha.lower(),
                    asset.file_sha256.lower(),
                    f"SHA-256 mismatch on {asset.asset_id}: disk={actual_sha} vs ledger={asset.file_sha256}",
                )
                
                # Check exact byte size
                actual_size = len(disk_bytes)
                self.assertEqual(
                    actual_size,
                    asset.file_size_bytes,
                    f"Size mismatch on {asset.asset_id}: disk={actual_size} vs ledger={asset.file_size_bytes}",
                )
                self.assertGreater(actual_size, 0, f"Asset {asset.asset_id} is 0 bytes.")

    def test_chunk_boundary_hashing_exactness(self):
        """Test SHA-256 hashing across various file sizes and buffer chunk boundaries."""
        # Test sizes around 65536 chunk boundary: 0, 1, 65535, 65536, 65537, 131072, 1000000
        test_sizes = [0, 1, 100, 65535, 65536, 65537, 131072, 1048576]
        
        for size in test_sizes:
            test_file = self.out_path / f"chunk_test_{size}.bin"
            data = os.urandom(size) if size > 0 else b""
            test_file.write_bytes(data)
            
            expected_sha = hashlib.sha256(data).hexdigest()
            computed_sha = compute_file_sha256(test_file)
            
            self.assertEqual(
                computed_sha,
                expected_sha,
                f"Chunk hashing failed for size {size}: expected {expected_sha}, got {computed_sha}",
            )
            self.assertTrue(verify_sha256(test_file, expected_sha))
            self.assertFalse(verify_sha256(test_file, "a" * 64))

    def test_tamper_detection_scenarios(self):
        """Stress-test tamper detection when on-disk files are subtly modified or corrupted."""
        mgr = AssetLedgerManager(output_dir=self.out_path, project_id="proj_tamper_test")
        images_dir = self.out_path / "assets" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        original_data = b"<svg xmlns='http://www.w3.org/2000/svg'><rect width='100' height='100' fill='blue'/></svg>"
        asset_file = images_dir / "asset_tamper.svg"
        asset_file.write_bytes(original_data)
        correct_sha = hashlib.sha256(original_data).hexdigest()
        
        mgr.record_frozen_asset(
            asset_id="asset_tamper_01",
            local_path="assets/images/asset_tamper.svg",
            file_size_bytes=len(original_data),
            file_sha256=correct_sha,
            source_provider="procedural_generator",
            source_url="procedural://vector/asset_tamper.svg",
            creator=CreatorInfo(name="Harness 9 Engine"),
            license_info=LicenseInfo(license_type="CC0-1.0 (Public Domain)", attribution_text="CC0"),
        )
        
        # 1. Untampered passes
        val = mgr.validate_ledger(project_dir=self.out_path)
        self.assertTrue(val["valid"])
        self.assertEqual(len(val["errors"]), 0)
        
        # 2. Single byte flip
        tampered_data = bytearray(original_data)
        tampered_data[10] = ord(b"Z") if tampered_data[10] != ord(b"Z") else ord(b"A")
        asset_file.write_bytes(bytes(tampered_data))
        val_flipped = mgr.validate_ledger(project_dir=self.out_path)
        self.assertFalse(val_flipped["valid"])
        self.assertTrue(any("SHA-256 mismatch" in e for e in val_flipped["errors"]))
        
        # 3. Truncated by 1 byte
        asset_file.write_bytes(original_data[:-1])
        val_truncated = mgr.validate_ledger(project_dir=self.out_path)
        self.assertFalse(val_truncated["valid"])
        self.assertTrue(any("SHA-256 mismatch" in e for e in val_truncated["errors"]))
        
        # 4. Appended newline / trailing byte
        asset_file.write_bytes(original_data + b"\n")
        val_appended = mgr.validate_ledger(project_dir=self.out_path)
        self.assertFalse(val_appended["valid"])
        self.assertTrue(any("SHA-256 mismatch" in e for e in val_appended["errors"]))
        
        # 5. Missing file
        asset_file.unlink()
        val_missing = mgr.validate_ledger(project_dir=self.out_path)
        self.assertFalse(val_missing["valid"])
        self.assertTrue(any("missing on disk" in e for e in val_missing["errors"]))


class TestLicenseMetadataCompleteness(unittest.TestCase):
    """Empirical challenges for license metadata completeness and provenance."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_all_assets_have_complete_license_metadata(self):
        """Assert every generated asset has non-empty license_type, attribution_text, source_url, creator."""
        dossier = ResearchDossier(
            topic="GPU Computing Architecture",
            metadata=DossierMetadata(run_id="run_license_test", mode="offline_fallback"),
            summary=Summary(headline="GPU Acceleration", executive_summary="Summary", key_takeaways=["CUDA", "SIMD"]),
            claims=[
                Claim(
                    claim_id=f"claim_{i+1:02d}",
                    claim_text=f"Claim text {i+1}",
                    category="tech",
                    confidence_score=0.99,
                    primary_source=Source(title="NVIDIA", url="https://nvidia.com"),
                    visual_cue_suggestion=f"GPU Visual {i+1}",
                )
                for i in range(5)
            ],
            talking_points=[
                TalkingPoint(beat_index=i+1, title=f"Beat {i+1}", narrative_hook="Hook", supported_claim_ids=[f"claim_{i+1:02d}"])
                for i in range(5)
            ],
            suggested_visual_queries=[
                f"GPU streaming multiprocessor {i+1}" for i in range(5)
            ],
        )

        pipeline = AssetPipeline(output_dir=self.out_path)
        ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=self.out_path, offline=True)

        for asset in ledger.assets:
            # 1. license_type must be non-empty string
            self.assertIsNotNone(asset.license, f"Asset {asset.asset_id} missing license object.")
            self.assertTrue(
                isinstance(asset.license.license_type, str) and len(asset.license.license_type.strip()) > 0,
                f"Asset {asset.asset_id} has empty license_type: {asset.license.license_type}",
            )

            # 2. attribution_text must be non-empty string
            self.assertTrue(
                isinstance(asset.license.attribution_text, str) and len(asset.license.attribution_text.strip()) > 0,
                f"Asset {asset.asset_id} has empty attribution_text: {asset.license.attribution_text}",
            )

            # 3. source_url must be non-empty string
            self.assertTrue(
                isinstance(asset.source_url, str) and len(asset.source_url.strip()) > 0,
                f"Asset {asset.asset_id} has empty source_url: {asset.source_url}",
            )

            # 4. creator must be non-empty with a valid name
            self.assertIsNotNone(asset.creator, f"Asset {asset.asset_id} missing creator object.")
            self.assertTrue(
                isinstance(asset.creator.name, str) and len(asset.creator.name.strip()) > 0,
                f"Asset {asset.asset_id} has empty creator.name: {asset.creator.name}",
            )

            # 5. Boolean flags should be valid booleans
            self.assertIsInstance(asset.license.attribution_required, bool)
            self.assertIsInstance(asset.license.commercial_use_allowed, bool)
            self.assertIsInstance(asset.license.modification_allowed, bool)

    def test_online_candidate_and_fallback_license_completeness(self):
        """Test licensing completeness when switching between online candidate and fallback."""
        pipeline = AssetPipeline(output_dir=self.out_path)

        # Mock online candidate discovery
        mock_candidate = CandidateAsset(
            title="Transistor Bell Labs Photo",
            source_provider="wikimedia_commons",
            source_url="https://commons.wikimedia.org/wiki/File:Transistor.jpg",
            page_url="https://commons.wikimedia.org/wiki/File:Transistor.jpg",
            media_type="image/jpeg",
            width=1920,
            height=1080,
            creator_name="Walter Brattain",
            creator_profile_url="https://example.com/brattain",
            license_type="CC BY-SA 4.0",
            attribution_text="Walter Brattain, CC BY-SA 4.0 via Wikimedia Commons",
            attribution_required=True,
            commercial_use_allowed=True,
            modification_allowed=True,
            query_matched="transistor",
        )

        dummy_jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00" + b"\x00" * 32

        # 1. Success case: download succeeds
        with patch.object(pipeline.discovery, "search_assets", return_value=[mock_candidate]):
            with patch("urllib.request.urlopen") as mock_url:
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_resp.headers = {"Content-Length": str(len(dummy_jpeg_bytes))}
                mock_resp.read.side_effect = [dummy_jpeg_bytes, b""]
                mock_resp.__enter__.return_value = mock_resp
                mock_url.return_value = mock_resp

                dossier = {
                    "topic": "Transistor History",
                    "claims": [{"claim_id": "c1", "claim_text": "text"}],
                    "suggested_visual_queries": ["transistor"],
                }
                ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=self.out_path, offline=False)

                self.assertEqual(len(ledger.assets), 1)
                asset = ledger.assets[0]
                self.assertEqual(asset.creator.name, "Walter Brattain")
                self.assertEqual(asset.license.license_type, "CC BY-SA 4.0")
                self.assertTrue(asset.license.attribution_required)
                self.assertTrue(len(asset.license.attribution_text) > 0)
                self.assertTrue(len(asset.source_url) > 0)

        # 2. Test candidate failure when freeze_asset raises vs when fallback is generated
        sub_dir2 = self.out_path / "fallback_run"
        with patch.object(pipeline.discovery, "search_assets", return_value=[mock_candidate]):
            with patch("urllib.request.urlopen", side_effect=Exception("Network Timeout")):
                ledger_fb = pipeline.discover_and_freeze_assets(dossier, output_dir=sub_dir2, offline=False)
                self.assertEqual(len(ledger_fb.assets), 1)
                asset_fb = ledger_fb.assets[0]
                self.assertEqual(asset_fb.media_type, "image/svg+xml")
                # Document current behavior: status is FALLBACK_GENERATED
                self.assertEqual(asset_fb.verification_status, "FALLBACK_GENERATED")
                # Assert license completeness regardless of provider
                self.assertTrue(len(asset_fb.license.license_type) > 0)
                self.assertTrue(len(asset_fb.license.attribution_text) > 0)
                self.assertTrue(len(asset_fb.source_url) > 0)
                self.assertTrue(len(asset_fb.creator.name) > 0)

    def test_validate_ledger_detects_incomplete_metadata(self):
        """Test validate_ledger rejects assets with missing required metadata fields."""
        mgr = AssetLedgerManager(output_dir=self.out_path, project_id="proj_metadata_check")
        
        # Valid asset
        mgr.record_frozen_asset(
            asset_id="asset_valid",
            local_path="assets/images/valid.svg",
            file_size_bytes=100,
            file_sha256="abc",
            source_url="https://example.com/valid.svg",
            creator=CreatorInfo(name="Creator A"),
            license_info=LicenseInfo(license_type="CC0", attribution_text="CC0"),
        )
        
        # Incomplete asset missing creator name
        asset_no_creator = MediaAsset(
            asset_id="asset_no_creator",
            local_path="assets/images/bad1.svg",
            source_url="https://example.com/bad1.svg",
            creator=CreatorInfo(name=""),
            license=LicenseInfo(license_type="CC0", attribution_text="CC0"),
        )
        mgr.add_asset(asset_no_creator)
        
        # Incomplete asset missing license_type
        asset_no_license = MediaAsset(
            asset_id="asset_no_license",
            local_path="assets/images/bad2.svg",
            source_url="https://example.com/bad2.svg",
            creator=CreatorInfo(name="Creator B"),
            license=LicenseInfo(license_type="", attribution_text=""),
        )
        mgr.add_asset(asset_no_license)

        # Incomplete asset missing source_url
        asset_no_url = MediaAsset(
            asset_id="asset_no_url",
            local_path="assets/images/bad3.svg",
            source_url="",
            creator=CreatorInfo(name="Creator C"),
            license=LicenseInfo(license_type="CC0", attribution_text="CC0"),
        )
        mgr.add_asset(asset_no_url)

        val = mgr.validate_ledger()
        self.assertFalse(val["valid"])
        self.assertTrue(any("missing creator" in e for e in val["errors"]))
        self.assertTrue(any("missing license" in e for e in val["errors"]))
        self.assertTrue(any("missing source_url" in e for e in val["errors"]))


class TestLedgerSerializationRoundtripping(unittest.TestCase):
    """Empirical challenges for dual JSON & YAML serialization and roundtripping parity."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def _build_complex_sample_ledger(self) -> AssetProvenanceLedger:
        """Create a richly populated AssetProvenanceLedger with edge strings and unicode."""
        assets = [
            MediaAsset(
                asset_id="asset_01",
                local_path="assets/images/asset_01_bell_labs.svg",
                absolute_path="g:/Finding-new-code/harness9/assets/images/asset_01_bell_labs.svg",
                claim_id_refs=["claim_01", "claim_02"],
                scene_target="scene_1",
                media_type="image/svg+xml",
                file_size_bytes=1048576,
                file_sha256="a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
                dimensions=Dimensions(width=1920, height=1080, aspect_ratio="16:9"),
                source_provider="procedural_generator",
                source_url="procedural://vector/asset_01_bell_labs.svg",
                page_url=None,
                creator=CreatorInfo(
                    name="Harness 9 Procedural Engine (Walter Brattain & John Bardeen's Workshop)",
                    profile_url="https://github.com/nousresearch/hermes-agent",
                ),
                license=LicenseInfo(
                    license_type="CC0-1.0 (Public Domain)",
                    license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                    attribution_text='Procedural SVG Graphic; "Zero Rights Reserved" © 2026.',
                    attribution_required=False,
                    commercial_use_allowed=True,
                    modification_allowed=True,
                ),
                verification_status="FALLBACK_GENERATED",
                downloaded_at="2026-08-31T05:00:00+00:00",
            ),
            MediaAsset(
                asset_id="asset_02",
                local_path="assets/images/asset_02_gpu_arch.jpg",
                claim_id_refs=["claim_03"],
                scene_target="scene_2",
                media_type="image/jpeg",
                file_size_bytes=524288,
                file_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                dimensions=Dimensions(width=3840, height=2160, aspect_ratio="16:9"),
                source_provider="wikimedia_commons",
                source_url="https://upload.wikimedia.org/wikipedia/commons/gpu_arch_2026.jpg",
                page_url="https://commons.wikimedia.org/wiki/File:gpu_arch_2026.jpg",
                creator=CreatorInfo(
                    name="Prof. Müller-Schumacher & 计算机研究所 (Beijing Institute)",
                    profile_url="https://example.com/mueller",
                ),
                license=LicenseInfo(
                    license_type="CC BY-SA 4.0",
                    license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                    attribution_text="Müller-Schumacher / CC BY-SA 4.0: Modern Streaming Multiprocessors",
                    attribution_required=True,
                    commercial_use_allowed=True,
                    modification_allowed=True,
                ),
                verification_status="VERIFIED",
                downloaded_at="2026-08-31T05:01:00+00:00",
            ),
        ]

        license_summary = {"CC0-1.0 (Public Domain)": 1, "CC BY-SA 4.0": 1}
        return AssetProvenanceLedger(
            schema_version="1.0.0",
            project_id="proj_complex_roundtrip_test",
            total_assets=2,
            license_summary=license_summary,
            assets=assets,
            generated_at="2026-08-31T05:00:00+00:00",
        )

    def test_json_roundtrip_parity(self):
        """Assert JSON serialization and deserialization produces identical data structures."""
        original = self._build_complex_sample_ledger()
        
        json_str = original.to_json(indent=2)
        reloaded = AssetProvenanceLedger.from_json(json_str)
        
        self.assertEqual(original.to_dict(), reloaded.to_dict())
        self.assertEqual(original.project_id, reloaded.project_id)
        self.assertEqual(original.total_assets, reloaded.total_assets)
        self.assertEqual(original.license_summary, reloaded.license_summary)
        self.assertEqual(len(original.assets), len(reloaded.assets))

        for orig_a, relo_a in zip(original.assets, reloaded.assets):
            self.assertEqual(orig_a.to_dict(), relo_a.to_dict())
            self.assertEqual(orig_a.file_sha256, relo_a.file_sha256)
            self.assertEqual(orig_a.file_size_bytes, relo_a.file_size_bytes)
            self.assertEqual(orig_a.creator.name, relo_a.creator.name)
            self.assertEqual(orig_a.license.attribution_text, relo_a.license.attribution_text)

    def test_yaml_roundtrip_parity(self):
        """Assert YAML serialization and deserialization produces identical data structures."""
        original = self._build_complex_sample_ledger()
        
        yaml_str = original.to_yaml()
        reloaded = AssetProvenanceLedger.from_yaml(yaml_str)
        
        self.assertEqual(original.to_dict(), reloaded.to_dict())
        self.assertEqual(original.project_id, reloaded.project_id)
        self.assertEqual(original.total_assets, reloaded.total_assets)
        self.assertEqual(original.license_summary, reloaded.license_summary)
        self.assertEqual(len(original.assets), len(reloaded.assets))

        for orig_a, relo_a in zip(original.assets, reloaded.assets):
            self.assertEqual(orig_a.to_dict(), relo_a.to_dict())
            self.assertEqual(orig_a.file_sha256, relo_a.file_sha256)
            self.assertEqual(orig_a.file_size_bytes, relo_a.file_size_bytes)
            self.assertEqual(orig_a.creator.name, relo_a.creator.name)
            self.assertEqual(orig_a.license.attribution_text, relo_a.license.attribution_text)

    def test_cross_format_json_yaml_parity(self):
        """Assert JSON and YAML representations deserialize into 100% equivalent models."""
        original = self._build_complex_sample_ledger()
        
        json_path, yaml_path = original.save(self.out_path, base_name="test_cross")
        
        from_json_model = AssetProvenanceLedger.load(json_path)
        from_yaml_model = AssetProvenanceLedger.load(yaml_path)
        
        self.assertEqual(from_json_model.to_dict(), from_yaml_model.to_dict())
        self.assertEqual(from_json_model.model_dump(), from_yaml_model.model_dump())

    def test_dict_interface_parity(self):
        """Assert ledger supports dict-like access: __getitem__, get, __contains__, model_dump."""
        original = self._build_complex_sample_ledger()
        
        self.assertEqual(original["project_id"], "proj_complex_roundtrip_test")
        self.assertEqual(original["total_assets"], 2)
        self.assertEqual(original.get("schema_version"), "1.0.0")
        self.assertEqual(original.get("nonexistent_key", "fallback"), "fallback")
        self.assertIn("assets", original)
        self.assertIn("license_summary", original)
        self.assertNotIn("unknown_field", original)
        
        dumped = original.model_dump()
        self.assertIsInstance(dumped, dict)
        self.assertEqual(dumped["total_assets"], 2)


class TestAdversarialAndEdgeScenarios(unittest.TestCase):
    """Stress tests for extreme inputs, path sanitization, and edge behaviors."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_high_volume_assets_stress_test(self):
        """Test pipeline handling 50 visual queries with ledger integrity and hashing."""
        num_queries = 50
        dossier = ResearchDossier(
            topic="High Volume Scaling Test",
            metadata=DossierMetadata(run_id="run_scale_test", mode="offline_fallback"),
            summary=Summary(headline="Scale", executive_summary="Scale", key_takeaways=["Fast"]),
            claims=[
                Claim(
                    claim_id=f"claim_{i+1:03d}",
                    claim_text=f"Claim statement #{i+1}",
                    category="scaling",
                    confidence_score=0.9,
                    primary_source=Source(title="Src", url="https://example.com"),
                    visual_cue_suggestion=f"Visual #{i+1}",
                )
                for i in range(num_queries)
            ],
            talking_points=[],
            suggested_visual_queries=[f"Query scale item #{i+1}" for i in range(num_queries)],
        )

        pipeline = AssetPipeline(output_dir=self.out_path)
        ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=self.out_path, offline=True)

        self.assertEqual(ledger.total_assets, num_queries)
        self.assertEqual(len(ledger.assets), num_queries)
        self.assertEqual(ledger.license_summary.get("CC0-1.0 (Public Domain)"), num_queries)

        # Validate all 50 files on disk
        val = AssetLedgerManager().validate_ledger(ledger=ledger, project_dir=self.out_path)
        self.assertTrue(val["valid"], f"Validation failed with errors: {val['errors']}")

    def test_path_traversal_and_malicious_topic_sanitization(self):
        """Assert malicious topics and queries with path traversal are safely sanitized."""
        malicious_topic = "../../../etc/passwd && rm -rf / \\'\"` ; --"
        sanitized = sanitize_filename(malicious_topic)
        self.assertNotIn("..", sanitized)
        self.assertNotIn("/", sanitized)
        self.assertNotIn("\\", sanitized)
        self.assertNotIn(";", sanitized)

        dossier = {
            "topic": malicious_topic,
            "claims": [{"claim_id": "c1", "claim_text": "Safe text"}],
            "suggested_visual_queries": [
                "../../Windows/System32/calc.exe",
                "assets/images/../../../secret.key",
            ],
        }

        pipeline = AssetPipeline(output_dir=self.out_path)
        ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=self.out_path, offline=True)

        for asset in ledger.assets:
            # Must remain safely inside assets/images/
            self.assertTrue(asset.local_path.startswith("assets/images/"))
            self.assertNotIn("..", asset.local_path)
            disk_path = self.out_path / asset.local_path
            self.assertTrue(disk_path.exists())
            # Ensure resolved path is child of output directory
            self.assertTrue(str(disk_path.resolve()).startswith(str(self.out_path.resolve())))

    def test_duplicate_asset_id_replacement_and_summary_recount(self):
        """Test ledger manager handles replacement of duplicate asset IDs and updates summary."""
        mgr = AssetLedgerManager(output_dir=self.out_path, project_id="proj_dup_test")
        
        asset_cc0 = MediaAsset(
            asset_id="asset_01",
            local_path="assets/images/01.svg",
            file_size_bytes=100,
            file_sha256="sha_cc0",
            source_url="https://example.com/1",
            creator=CreatorInfo(name="A"),
            license=LicenseInfo(license_type="CC0-1.0"),
        )
        mgr.add_asset(asset_cc0)
        self.assertEqual(mgr.ledger.total_assets, 1)
        self.assertEqual(mgr.ledger.license_summary, {"CC0-1.0": 1})

        # Overwrite asset_01 with CC-BY license
        asset_cc_by = MediaAsset(
            asset_id="asset_01",
            local_path="assets/images/01_updated.svg",
            file_size_bytes=200,
            file_sha256="sha_by",
            source_url="https://example.com/1_updated",
            creator=CreatorInfo(name="A"),
            license=LicenseInfo(license_type="CC-BY-4.0"),
        )
        mgr.add_asset(asset_cc_by)
        self.assertEqual(mgr.ledger.total_assets, 1)
        self.assertEqual(mgr.ledger.license_summary, {"CC-BY-4.0": 1})
        self.assertEqual(mgr.get_asset("asset_01").file_size_bytes, 200)

    def test_corrupt_json_and_yaml_load_errors(self):
        """Test AssetProvenanceLedger raises expected errors on corrupted JSON/YAML files."""
        corrupt_json_file = self.out_path / "corrupt.json"
        corrupt_json_file.write_text("{ unquoted_key: missing_bracket", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            AssetProvenanceLedger.load(corrupt_json_file)

        corrupt_yaml_file = self.out_path / "corrupt.yaml"
        corrupt_yaml_file.write_text("- item1\n- item2\n- not_a_dict", encoding="utf-8")
        with self.assertRaises(ValueError):
            AssetProvenanceLedger.load(corrupt_yaml_file)

        missing_file = self.out_path / "does_not_exist.json"
        with self.assertRaises(FileNotFoundError):
            AssetProvenanceLedger.load(missing_file)

    def test_network_fallback_provenance_recording_audit(self):
        """
        Adversarial Challenge: Verify provenance attribution when online candidate download fails.
        Demonstrates that when candidate download fails, freezer.freeze_asset returns FALLBACK_GENERATED,
        and ledger records verification_status=FALLBACK_GENERATED while preserving schema completeness.
        """
        pipeline = AssetPipeline(output_dir=self.out_path)
        mock_cand = CandidateAsset(
            title="NASA Apollo Photo",
            source_provider="nasa_images",
            source_url="https://images.nasa.gov/apollo.jpg",
            page_url="https://images.nasa.gov/details/apollo",
            media_type="image/jpeg",
            width=1920,
            height=1080,
            creator_name="NASA JSC",
            creator_profile_url="https://nasa.gov",
            license_type="NASA Public Domain",
            attribution_text="NASA JSC, Public Domain",
            attribution_required=False,
            commercial_use_allowed=True,
            modification_allowed=True,
            query_matched="apollo computer",
        )

        with patch.object(pipeline.discovery, "search_assets", return_value=[mock_cand]):
            with patch("urllib.request.urlopen", side_effect=Exception("HTTP 503 Service Unavailable")):
                dossier = {
                    "topic": "Apollo Computer",
                    "claims": [{"claim_id": "c1", "claim_text": "Apollo Guidance"}],
                    "suggested_visual_queries": ["apollo computer"],
                }
                sub_dir = self.out_path / "apollo_fallback"
                ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=sub_dir, offline=False)

                self.assertEqual(len(ledger.assets), 1)
                asset = ledger.assets[0]
                
                # Check that on-disk file is an SVG and checksum is valid
                disk_file = sub_dir / asset.local_path
                self.assertTrue(disk_file.exists())
                self.assertEqual(asset.media_type, "image/svg+xml")
                self.assertEqual(compute_file_sha256(disk_file), asset.file_sha256)
                self.assertEqual(asset.verification_status, "FALLBACK_GENERATED")


if __name__ == "__main__":
    unittest.main()
