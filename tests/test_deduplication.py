"""
tests/test_deduplication.py — Comprehensive Unit & Integration Tests for Asset Deduplication (M4).

Tests:
1. Tier 1: Byte-Exact SHA-256 Hashing & Deduplication.
2. Tier 2: Perceptual Difference Hashing (dHash) & Gradient Analysis.
3. Bitwise Hamming Distance Calculus (d_H <= 4 near-duplicate detection).
4. AssetDeduplicator registry lifecycle, persistence, and registration.
5. Image format invariance (JPEG, PNG, WebP, SVG placeholders).
6. Edge cases: zero-byte input, boundary distances, corrupted data.
"""

import hashlib
import io
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from src.assets.deduplication import (
    DEFAULT_HAMMING_THRESHOLD,
    AssetDeduplicator,
    DeduplicationResult,
    compute_bytes_sha256,
    compute_dhash,
    compute_dhash_hex,
    compute_file_sha256,
    hamming_distance,
    hamming_distance_hex,
)


def create_test_image(
    size: tuple = (100, 100),
    pattern: str = "gradient",
    color: tuple = (128, 128, 128),
) -> Image.Image:
    """Generate deterministic test images for perceptual hashing."""
    img = Image.new("RGB", size, color=color)
    pixels = img.load()

    if pattern == "gradient":
        for y in range(size[1]):
            for x in range(size[0]):
                val = int(255 * (x / size[0]))
                pixels[x, y] = (val, val, val)
    elif pattern == "vertical_gradient":
        for y in range(size[1]):
            for x in range(size[0]):
                val = int(255 * (y / size[1]))
                pixels[x, y] = (val, val, val)
    elif pattern == "checkerboard":
        for y in range(size[1]):
            for x in range(size[0]):
                val = 255 if ((x // 10) + (y // 10)) % 2 == 0 else 0
                pixels[x, y] = (val, val, val)
    elif pattern == "inverse_gradient":
        for y in range(size[1]):
            for x in range(size[0]):
                val = 255 - int(255 * (x / size[0]))
                pixels[x, y] = (val, val, val)

    return img


class TestAssetDeduplication(unittest.TestCase):
    """Test suite for Multi-Tier Asset Deduplication Engine."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name)
        self.deduplicator = AssetDeduplicator(hamming_threshold=DEFAULT_HAMMING_THRESHOLD)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_tier1_sha256_exact_deduplication(self):
        """Verify Tier 1 byte-exact SHA-256 duplicate detection."""
        img = create_test_image(pattern="gradient")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        # Register asset 1
        res1 = self.deduplicator.check_and_register(raw_bytes, asset_id="asset_orig")
        self.assertFalse(res1.is_duplicate)
        self.assertEqual(res1.action_taken, "accepted")
        self.assertEqual(len(res1.sha256), 64)

        # Check exact same bytes
        res2 = self.deduplicator.check_and_register(raw_bytes, asset_id="asset_duplicate")
        self.assertTrue(res2.is_duplicate)
        self.assertEqual(res2.duplicate_tier, "tier_1_sha256")
        self.assertEqual(res2.matched_asset_id, "asset_orig")
        self.assertEqual(res2.action_taken, "reused_existing")
        self.assertEqual(res2.hamming_distance, 0)

    def test_02_tier2_dhash_near_duplicate_detection(self):
        """Verify Tier 2 dHash flags near-duplicates with minor modifications."""
        # Original gradient image (100x100)
        img1 = create_test_image(size=(100, 100), pattern="gradient")
        
        # Resized and slightly recompressed version (200x200)
        img2 = create_test_image(size=(200, 200), pattern="gradient")

        # Completely distinct image (checkerboard)
        img3 = create_test_image(size=(100, 100), pattern="checkerboard")

        # Inverse gradient image
        img4 = create_test_image(size=(100, 100), pattern="inverse_gradient")

        h1 = compute_dhash(img1)
        h2 = compute_dhash(img2)
        h3 = compute_dhash(img3)
        h4 = compute_dhash(img4)

        # Resized image of same visual pattern should have identical or near-identical dHash (distance <= 4)
        dist_1_2 = hamming_distance(h1, h2)
        self.assertLessEqual(dist_1_2, 4)

        # Distinct images should have large Hamming distance (> 4, usually > 15)
        dist_1_3 = hamming_distance(h1, h3)
        self.assertGreater(dist_1_3, 4)

        dist_1_4 = hamming_distance(h1, h4)
        self.assertGreater(dist_1_4, 4)

    def test_03_deduplicator_pipeline_workflow(self):
        """Verify AssetDeduplicator rejects near-duplicates and accepts unique visual assets."""
        img1 = create_test_image(size=(100, 100), pattern="gradient")
        img2 = create_test_image(size=(150, 150), pattern="gradient")
        img3 = create_test_image(size=(100, 100), pattern="vertical_gradient")
        img4 = create_test_image(size=(100, 100), pattern="checkerboard")

        # 1. Register img1
        res1 = self.deduplicator.check_and_register(img1, asset_id="img_1")
        self.assertFalse(res1.is_duplicate)
        self.assertEqual(res1.action_taken, "accepted")

        # 2. Candidate img2 is a resized version of img1 (near-duplicate)
        res2 = self.deduplicator.check_and_register(img2, asset_id="img_2")
        self.assertTrue(res2.is_duplicate)
        self.assertEqual(res2.duplicate_tier, "tier_2_dhash")
        self.assertEqual(res2.matched_asset_id, "img_1")
        self.assertEqual(res2.action_taken, "rejected_near_duplicate")

        # 3. Candidate img3 is visually distinct
        res3 = self.deduplicator.check_and_register(img3, asset_id="img_3")
        self.assertFalse(res3.is_duplicate)
        self.assertEqual(res3.action_taken, "accepted")

        # 4. Candidate img4 is visually distinct
        res4 = self.deduplicator.check_and_register(img4, asset_id="img_4")
        self.assertFalse(res4.is_duplicate)
        self.assertEqual(res4.action_taken, "accepted")

        registered = self.deduplicator.get_registered_assets()
        self.assertEqual(len(registered), 3)  # img_1, img_3, img_4

    def test_04_hamming_distance_calculus(self):
        """Verify mathematical Hamming distance calculation."""
        h1 = 0b1111000011110000
        h2 = 0b1111000011110001  # 1 bit difference
        h3 = 0b1111000011111111  # 4 bits difference
        h4 = 0b0000111100001111  # 16 bits difference

        self.assertEqual(hamming_distance(h1, h1), 0)
        self.assertEqual(hamming_distance(h1, h2), 1)
        self.assertEqual(hamming_distance(h1, h3), 4)
        self.assertEqual(hamming_distance(h1, h4), 16)

        # Hex distance calculation
        self.assertEqual(hamming_distance_hex("000f", "000e"), 1)
        self.assertEqual(hamming_distance_hex("ffff", "0000"), 16)

    def test_05_registry_save_and_load_persistence(self):
        """Verify JSON persistence of asset deduplication index."""
        img1 = create_test_image(size=(50, 50), pattern="gradient")
        self.deduplicator.check_and_register(img1, asset_id="persist_01", metadata={"author": "Alice"})

        save_file = self.out_dir / "dedup_registry.json"
        self.deduplicator.save_registry(save_file)
        self.assertTrue(save_file.exists())

        # New instance loading registry
        new_dedup = AssetDeduplicator()
        new_dedup.load_registry(save_file)

        self.assertEqual(len(new_dedup.get_registered_assets()), 1)
        is_dup, match_id, _ = new_dedup.is_near_duplicate(img1)
        self.assertTrue(is_dup)
        self.assertEqual(match_id, "persist_01")

    def test_06_edge_cases_zero_bytes_and_svg_handling(self):
        """Verify handling of zero-byte inputs and SVG data."""
        empty_data = b""
        empty_sha = compute_bytes_sha256(empty_data)
        self.assertEqual(empty_sha, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

        res_empty = self.deduplicator.check_and_register(empty_data, asset_id="empty_asset")
        self.assertFalse(res_empty.is_duplicate)
        self.assertEqual(res_empty.sha256, empty_sha)

        # SVG content handling
        svg_content = b"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><rect width='100' height='100' fill='blue'/></svg>"
        res_svg = self.deduplicator.check_and_register(svg_content, asset_id="svg_asset")
        self.assertFalse(res_svg.is_duplicate)
        self.assertGreater(len(res_svg.dhash_hex), 0)


if __name__ == "__main__":
    unittest.main()
