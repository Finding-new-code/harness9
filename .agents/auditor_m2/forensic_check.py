"""Forensic Integrity Auditor Execution Trace & Empirical Verification Suite for Milestone 2 (src/assets)."""

import hashlib
import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(r"g:\Finding-new-code\harness9").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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

results = []

def record(name: str, passed: bool, details: str):
    status = "PASS" if passed else "FAIL"
    results.append({"check": name, "status": status, "details": details})
    print(f"[{status}] {name}: {details}")

print("================================================================================")
print("FORENSIC INTEGRITY AUDIT: Milestone 2 (Asset Discovery, Rights Ledger, Freezer)")
print("================================================================================")

# ------------------------------------------------------------------------------
# Check 1: Magic-Byte Sniffing Verification
# ------------------------------------------------------------------------------
print("\n--- Check 1: Magic-Byte Sniffing ---")
try:
    test_cases = [
        (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01", "image/jpeg"),
        (b"\xff\xd8\xff\xdb\x00C\x00", "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "image/png"),
        (b"RIFF\x24\x00\x00\x00WEBPVP8 ", "image/webp"),
        (b"<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>", "image/svg+xml"),
        (b"<?xml version=\"1.0\" encoding=\"UTF-8\"?><svg width=\"100\"></svg>", "image/svg+xml"),
        (b"\x00\x00\x00 ftypisom\x00\x00\x02\x00mp41mp42isom", "video/mp4"),
        (b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00", "audio/wav"),
        (b"ID3\x03\x00\x00\x00\x00\x00#TIT2", "audio/mp3"),
        (b"\xff\xfb\x90d\x00\x00\x00\x00", "audio/mp3"),
        (b"\xff\xf3\x40\xc4", "audio/mp3"),
        (b"SOME RANDOM OCTET STREAM DATA", "application/octet-stream"),
        (b"", "application/octet-stream"),
    ]
    all_match = True
    mismatches = []
    for raw, expected in test_cases:
        actual = sniff_magic_bytes(raw)
        if actual != expected:
            all_match = False
            mismatches.append(f"Expected {expected}, got {actual} for raw={raw[:16]}")
    
    record(
        "Magic-Byte Sniffing Signatures",
        all_match,
        f"Verified {len(test_cases)} MIME signatures across JPEG, PNG, WebP, SVG, MP4, WAV, MP3. Mismatches: {mismatches}"
    )
except Exception as e:
    record("Magic-Byte Sniffing Signatures", False, f"Exception: {e}")

# ------------------------------------------------------------------------------
# Check 2: NIST Standard SHA-256 Vectors & Tamper Detection
# ------------------------------------------------------------------------------
print("\n--- Check 2: SHA-256 Computation & Tamper Detection ---")
try:
    nist_vectors = [
        (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
        (b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"),
    ]
    nist_pass = True
    for data, expected in nist_vectors:
        computed = compute_sha256(data)
        if computed != expected:
            nist_pass = False
            print(f"SHA mismatch: computed {computed} != expected {expected}")
            break

    # Test file sha256 with 3MB binary payload
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "large_sha_test.bin"
        payload = os.urandom(3 * 1024 * 1024)
        tmp_file.write_bytes(payload)
        expected_file_sha = hashlib.sha256(payload).hexdigest()
        computed_file_sha = compute_file_sha256(tmp_file)
        file_sha_pass = (computed_file_sha == expected_file_sha)

        # Test tamper detection
        verify_true = verify_sha256(tmp_file, expected_file_sha)
        verify_false = verify_sha256(tmp_file, "a" * 64)
        tamper_pass = verify_true and not verify_false

    record(
        "NIST SHA-256 Test Vectors & Chunked Hashing",
        nist_pass and file_sha_pass and tamper_pass,
        f"NIST vectors match={nist_pass}, 3MB chunked hash match={file_sha_pass}, Tamper detection={tamper_pass}"
    )
except Exception as e:
    record("NIST SHA-256 Test Vectors & Chunked Hashing", False, f"Exception: {e}")

# ------------------------------------------------------------------------------
# Check 3: Procedural SVG Structure & Generator Verification
# ------------------------------------------------------------------------------
print("\n--- Check 3: Procedural SVG Vector Rendering & Structure Analysis ---")
try:
    gen = ProceduralSVGGenerator()
    themes = ["circuits", "computing", "aerospace", "science", "general"]
    theme_details = []
    has_geometric_elements = True

    for th in themes:
        svg_code = gen.generate_topic_svg(
            topic=f"Forensic Test Topic for {th.upper()}",
            query=f"Technical Query for {th}",
            width=1920,
            height=1080,
            theme=th,
        )
        # Check basic SVG structural contract
        has_svg_tag = svg_code.startswith("<svg") and svg_code.strip().endswith("</svg>")
        has_viewbox = 'viewBox="0 0 1920 1080"' in svg_code
        has_defs = "<defs>" in svg_code and "<linearGradient" in svg_code
        has_motif = "<rect" in svg_code and ("<circle" in svg_code or "<line" in svg_code or "<ellipse" in svg_code)

        if not (has_svg_tag and has_viewbox and has_defs and has_motif):
            has_geometric_elements = False
        theme_details.append(f"{th}: len={len(svg_code)} chars, valid_structure={has_svg_tag and has_viewbox}")

    # Test quote, metric, and hero cards
    quote_svg = gen.generate_quote_card("Test quote", "Author", "Context")
    metric_svg = gen.generate_metric_card("Metric", "100K", "Context")
    hero_svg = gen.generate_hero_card("Headline", "Subhead", "Topic")

    cards_ok = ("<svg" in quote_svg and "<svg" in metric_svg and "<svg" in hero_svg)

    # Check XML entity note
    raw_tag_ampersand = any("&" in gen.THEMES[t]["tag"] for t in gen.THEMES)

    record(
        "Procedural SVG Generator Execution",
        has_geometric_elements and cards_ok,
        f"All 5 themes and 3 card types generate genuine procedural vectors. Structural validity={has_geometric_elements}. Note: Theme tags contain raw '&' which requires html.escape() for strict XML parser compliance: {raw_tag_ampersand}"
    )
except Exception as e:
    record("Procedural SVG Generator Execution", False, f"Exception: {e}")

# ------------------------------------------------------------------------------
# Check 4: Rights Ledger & Provenance Serialization
# ------------------------------------------------------------------------------
print("\n--- Check 4: Rights Ledger & Provenance Serialization ---")
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mgr = AssetLedgerManager(output_dir=tmp_path, project_id="forensic_proj_1")
        
        # Add 3 assets with different licenses
        mgr.record_frozen_asset(
            asset_id="asset_01",
            local_path="assets/images/asset_01.svg",
            file_size_bytes=1000,
            file_sha256="11" * 32,
            source_provider="procedural_generator",
            source_url="procedural://test1.svg",
            license_info=LicenseInfo(license_type="CC0-1.0 (Public Domain)", commercial_use_allowed=True),
        )
        mgr.record_frozen_asset(
            asset_id="asset_02",
            local_path="assets/images/asset_02.jpg",
            file_size_bytes=2000,
            file_sha256="22" * 32,
            source_provider="wikimedia_commons",
            source_url="https://commons.wikimedia.org/test2.jpg",
            license_info=LicenseInfo(license_type="CC-BY-SA 4.0", attribution_required=True),
        )
        mgr.record_frozen_asset(
            asset_id="asset_03",
            local_path="assets/images/asset_03.jpg",
            file_size_bytes=3000,
            file_sha256="33" * 32,
            source_provider="pexels",
            source_url="https://pexels.com/test3.jpg",
            license_info=LicenseInfo(license_type="Pexels License", attribution_required=False),
        )

        json_file, yaml_file = mgr.save(tmp_path)
        
        # Verify JSON
        loaded_json = AssetProvenanceLedger.load(json_file)
        json_ok = (loaded_json.total_assets == 3 and len(loaded_json.assets) == 3 and loaded_json.license_summary.get("CC-BY-SA 4.0") == 1)

        # Verify YAML
        loaded_yaml = AssetProvenanceLedger.load(yaml_file)
        yaml_ok = (loaded_yaml.total_assets == 3 and len(loaded_yaml.assets) == 3 and loaded_yaml.license_summary.get("Pexels License") == 1)

    record(
        "Rights Ledger Serialization (JSON & YAML)",
        json_ok and yaml_ok,
        f"JSON loaded={json_ok}, YAML loaded={yaml_ok}, License summary correctly calculated: {mgr.ledger.license_summary}"
    )
except Exception as e:
    record("Rights Ledger Serialization (JSON & YAML)", False, f"Exception: {e}")

# ------------------------------------------------------------------------------
# Check 5: Asset Freezer Atomic Operations & Composition Auditing
# ------------------------------------------------------------------------------
print("\n--- Check 5: Asset Freezer & Zero-External URL Auditing ---")
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        freezer = AssetFreezer(base_output_dir=tmp_path)
        
        # Test freeze_bytes
        test_raw = b"<svg xmlns=\"http://www.w3.org/2000/svg\"><circle cx=\"50\" cy=\"50\" r=\"40\"/></svg>"
        frozen_file, sha, size, mime = freezer.freeze_bytes(test_raw, tmp_path / "assets" / "images" / "test.svg")
        freeze_ok = frozen_file.exists() and size == len(test_raw) and mime == "image/svg+xml"

        # Test composition auditing
        html_clean = f"""<!DOCTYPE html><html><body><img src="assets/images/test.svg"/></body></html>"""
        html_dirty = f"""<!DOCTYPE html><html><body><img src="https://example.com/external.jpg"/></body></html>"""

        clean_audit = audit_composition_paths(html_clean, tmp_path)
        dirty_audit = audit_composition_paths(html_dirty, tmp_path)

        audit_ok = clean_audit["valid"] and not dirty_audit["valid"] and len(dirty_audit["external_urls"]) == 1

    record(
        "Asset Freezer & Zero-External-URL Linter",
        freeze_ok and audit_ok,
        f"freeze_bytes disk write={freeze_ok}, clean HTML audit valid={clean_audit['valid']}, dirty HTML detected={not dirty_audit['valid']}"
    )
except Exception as e:
    record("Asset Freezer & Zero-External-URL Linter", False, f"Exception: {e}")

# ------------------------------------------------------------------------------
# Check 6: Full Asset Pipeline Integration with Real Dossier
# ------------------------------------------------------------------------------
print("\n--- Check 6: End-to-End Asset Pipeline Offline Execution ---")
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        dossier = ResearchDossier(
            topic="How GPUs Work: Parallel Microarchitectures",
            metadata=DossierMetadata(run_id="audit_run_gpu", mode="offline_fallback"),
            summary=Summary(
                headline="Parallel Compute Revolution",
                executive_summary="GPUs process thousands of threads concurrently.",
                key_takeaways=["SIMD/SIMT architectures", "High memory bandwidth"],
            ),
            claims=[
                Claim(
                    claim_id="claim_01",
                    claim_text="GPUs contain thousands of smaller stream processor cores.",
                    category="technical_architecture",
                    confidence_score=0.99,
                    primary_source=Source(title="NVIDIA Whitepaper", url="https://nvidia.com/gpu-arch"),
                    visual_cue_suggestion="GPU die parallel streaming cores layout",
                ),
                Claim(
                    claim_id="claim_02",
                    claim_text="Memory bandwidth in modern GPUs exceeds 1 TB/s.",
                    category="performance_metric",
                    confidence_score=0.97,
                    primary_source=Source(title="AnandTech", url="https://anandtech.com/hbm"),
                    visual_cue_suggestion="High bandwidth memory stacked silicon interconnect",
                ),
            ],
            talking_points=[
                TalkingPoint(beat_index=1, title="Compute Array", narrative_hook="Stream processors", supported_claim_ids=["claim_01"]),
                TalkingPoint(beat_index=2, title="Memory Wall", narrative_hook="VRAM bandwidth", supported_claim_ids=["claim_02"]),
            ],
            suggested_visual_queries=[
                "GPU die parallel streaming cores layout",
                "High bandwidth memory stacked silicon interconnect",
            ],
        )

        pipeline = AssetPipeline(output_dir=tmp_path)
        ledger = pipeline.discover_and_freeze_assets(dossier, output_dir=tmp_path, offline=True, format_aspect="16:9")

        # Verify output files
        files_created = list((tmp_path / "assets" / "images").glob("*.*"))
        has_ledger_json = (tmp_path / "asset_ledger.json").exists()
        has_ledger_yaml = (tmp_path / "asset_ledger.yaml").exists()

        all_files_valid = True
        for f in files_created:
            f_size = f.stat().st_size
            if f_size == 0:
                all_files_valid = False

        pipeline_ok = (len(files_created) == 2 and has_ledger_json and has_ledger_yaml and all_files_valid)

    record(
        "End-to-End Asset Pipeline Execution",
        pipeline_ok,
        f"Files created={len(files_created)}, JSON ledger={has_ledger_json}, YAML ledger={has_ledger_yaml}, All files non-empty={all_files_valid}"
    )
except Exception as e:
    record("End-to-End Asset Pipeline Execution", False, f"Exception: {e}")

# ------------------------------------------------------------------------------
# Check 7: Static Integrity Audit (Hardcoded/Dummy/Facade search)
# ------------------------------------------------------------------------------
print("\n--- Check 7: Static Analysis for Cheats & Facades ---")
try:
    assets_dir = PROJECT_ROOT / "src" / "assets"
    source_files = list(assets_dir.glob("*.py"))
    
    facade_flags = []
    for sf in source_files:
        content = sf.read_text(encoding="utf-8")
        if "TODO" in content or "NotImplementedError" in content:
            facade_flags.append(f"{sf.name}: Contains unimplemented markers")
        # Check for dummy hashes like 00000000 or fake constants
        if "0000000000000000" in content:
            facade_flags.append(f"{sf.name}: Contains dummy zero hashes")
    
    no_cheats = (len(facade_flags) == 0)
    record(
        "Static Facade & Dummy Code Audit",
        no_cheats,
        f"Scanned {len(source_files)} source files. Flags: {facade_flags}"
    )
except Exception as e:
    record("Static Facade & Dummy Code Audit", False, f"Exception: {e}")

print("\n================================================================================")
print("AUDIT EXECUTION SUMMARY")
print("================================================================================")
total_checks = len(results)
passed_checks = sum(1 for r in results if r["status"] == "PASS")
failed_checks = total_checks - passed_checks

print(f"Total Checks: {total_checks}")
print(f"Passed: {passed_checks}")
print(f"Failed: {failed_checks}")
if failed_checks == 0:
    print("\nFINAL FORENSIC VERDICT: CLEAN")
else:
    print("\nFINAL FORENSIC VERDICT: INTEGRITY VIOLATION")
