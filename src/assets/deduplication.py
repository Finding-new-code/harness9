"""
src.assets.deduplication — Multi-Tier Asset Deduplication Engine (Milestone M4).

Combines two-tier visual and binary deduplication:
1. Tier 1: Byte-Exact Cryptographic SHA-256 Hashing.
   - Prevents duplicate downloads and binary collisions.
2. Tier 2: Perceptual Gradient Difference Hashing (dHash).
   - Generates 64-bit gradient hashes invariant to resolution, format, and minor compression.
   - Calculates bitwise Hamming distance (threshold <= 4 flags near-duplicates).
"""

from datetime import datetime, timezone
import hashlib
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image
from pydantic import Field

from src.models.contracts import H9BaseModel

logger = logging.getLogger("harness9.assets.deduplication")

DEFAULT_HAMMING_THRESHOLD = 4  # Hamming distance <= 4 indicates near-duplicate


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class DeduplicationResult(H9BaseModel):
    """Result of asset deduplication inspection."""
    is_duplicate: bool = False
    duplicate_tier: Optional[str] = None  # "tier_1_sha256", "tier_2_dhash", or None
    matched_asset_id: Optional[str] = None
    sha256: str = ""
    dhash: int = 0
    dhash_hex: str = ""
    hamming_distance: Optional[int] = None
    action_taken: str = "accepted"  # "accepted", "reused_existing", "rejected_near_duplicate"
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Hashing & Distance Functions
# ---------------------------------------------------------------------------

def compute_bytes_sha256(data: bytes) -> str:
    """Compute hexadecimal SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Compute hexadecimal SHA-256 digest of a local file."""
    p = Path(file_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found for SHA-256 calculation: {p}")
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def hamming_distance(h1: int, h2: int) -> int:
    """
    Calculate bitwise Hamming distance between two 64-bit perceptual integer hashes.
    d_H(H1, H2) = popcount(H1 ^ H2)
    """
    xor_val = h1 ^ h2
    if hasattr(xor_val, "bit_count"):
        return xor_val.bit_count()
    return bin(xor_val).count("1")


def hamming_distance_hex(hex1: str, hex2: str) -> int:
    """Calculate Hamming distance between two hexadecimal hash strings."""
    val1 = int(hex1, 16) if hex1 else 0
    val2 = int(hex2, 16) if hex2 else 0
    return hamming_distance(val1, val2)


def _load_image_object(image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
    """Load and return PIL Image instance from file path, raw bytes, or existing Image."""
    if isinstance(image_input, Image.Image):
        return image_input.copy()
    if isinstance(image_input, (str, Path)):
        p = Path(image_input).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Image file not found: {p}")
        return Image.open(p)
    if isinstance(image_input, bytes):
        if len(image_input) == 0:
            # Return a blank 1x1 image for zero-byte input
            return Image.new("RGB", (1, 1), color="black")
        # Check if SVG
        header = image_input[:1024].lower()
        if b"<svg" in header or b"<?xml" in header:
            # Generate deterministic procedural placeholder image for SVG vector
            seed = int(hashlib.md5(image_input).hexdigest()[:8], 16)
            img = Image.new("RGB", (64, 64))
            pixels = img.load()
            for y in range(64):
                for x in range(64):
                    r = (seed + x * 7) % 256
                    g = (seed // 2 + y * 7) % 256
                    b = (seed // 3 + (x + y) * 3) % 256
                    pixels[x, y] = (r, g, b)
            return img
        return Image.open(io.BytesIO(image_input))
    raise TypeError(f"Unsupported image input type: {type(image_input)}")


def compute_dhash(image_input: Union[str, Path, bytes, Image.Image], hash_size: int = 8) -> int:
    """
    Compute 64-bit Difference Hash (dHash) for visual perceptual deduplication.
    Combines 32-bit horizontal gradient analysis and 32-bit vertical gradient analysis
    for robust 2D multi-axis perceptual hashing.
    """
    try:
        img = _load_image_object(image_input)
    except Exception as e:
        logger.warning(f"Failed to load image for dHash: {e}. Falling back to byte hash derivation.")
        if isinstance(image_input, bytes):
            raw_b = image_input
        elif isinstance(image_input, (str, Path)) and Path(image_input).exists():
            raw_b = Path(image_input).read_bytes()
        else:
            raw_b = b""
        return int(hashlib.sha256(raw_b).hexdigest()[:16], 16)

    # 1. Convert to grayscale
    gray = img.convert("L")

    # 2. Resize to calculate dual-axis 32-bit horizontal + 32-bit vertical gradient
    resample_filter = getattr(Image, "Resampling", Image).LANCZOS if hasattr(Image, "Resampling") else getattr(Image, "LANCZOS", 1)

    # Horizontal 32-bit gradient (8 cols x 4 rows)
    h_resized = gray.resize((hash_size + 1, 4), resample_filter)
    h_pixels = list(h_resized.get_flattened_data()) if hasattr(h_resized, "get_flattened_data") else list(h_resized.getdata())
    h_width = hash_size + 1
    h_hash = 0
    for row in range(4):
        row_offset = row * h_width
        for col in range(hash_size):
            left = h_pixels[row_offset + col]
            right = h_pixels[row_offset + col + 1]
            bit = 1 if left > right else 0
            h_hash = (h_hash << 1) | bit

    # Vertical 32-bit gradient (4 cols x 8 rows)
    v_resized = gray.resize((4, hash_size + 1), resample_filter)
    v_pixels = list(v_resized.get_flattened_data()) if hasattr(v_resized, "get_flattened_data") else list(v_resized.getdata())
    v_width = 4
    v_hash = 0
    for row in range(hash_size):
        row_top = row * v_width
        row_bottom = (row + 1) * v_width
        for col in range(4):
            top = v_pixels[row_top + col]
            bottom = v_pixels[row_bottom + col]
            bit = 1 if top < bottom else 0
            v_hash = (v_hash << 1) | bit

    decimal_hash = (h_hash << 32) | v_hash
    return decimal_hash


def compute_dhash_hex(image_input: Union[str, Path, bytes, Image.Image], hash_size: int = 8) -> str:
    """Compute 16-character hexadecimal dHash string."""
    val = compute_dhash(image_input, hash_size=hash_size)
    return f"{val:016x}"


# ---------------------------------------------------------------------------
# Multi-Tier Asset Deduplicator Engine
# ---------------------------------------------------------------------------

class AssetDeduplicator:
    """
    Two-Tier Asset Deduplication Engine managing SHA-256 byte-exact cache
    and dHash perceptual visual similarity index.
    """

    def __init__(self, hamming_threshold: int = DEFAULT_HAMMING_THRESHOLD):
        self.hamming_threshold = hamming_threshold
        # Tier 1 Index: sha256 -> asset_record
        self.sha_index: Dict[str, Dict[str, Any]] = {}
        # Tier 2 Index: dhash -> asset_record
        self.dhash_index: Dict[int, Dict[str, Any]] = {}
        # All registered assets: asset_id -> record
        self.registry: Dict[str, Dict[str, Any]] = {}

    def check_and_register(
        self,
        asset_input: Union[str, Path, bytes, Image.Image],
        asset_id: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeduplicationResult:
        """
        Evaluate candidate asset against Tier 1 (SHA-256) and Tier 2 (dHash).
        If unique, registers the asset into indices.
        """
        # Determine raw bytes and file path
        if isinstance(asset_input, (str, Path)):
            p = Path(asset_input).resolve()
            if p.exists():
                raw_bytes = p.read_bytes()
                f_path = str(p)
            else:
                raw_bytes = str(asset_input).encode("utf-8")
                f_path = str(asset_input)
        elif isinstance(asset_input, bytes):
            raw_bytes = asset_input
            f_path = file_path or ""
        elif isinstance(asset_input, Image.Image):
            buf = io.BytesIO()
            asset_input.save(buf, format="PNG")
            raw_bytes = buf.getvalue()
            f_path = file_path or ""
        else:
            raw_bytes = b""
            f_path = file_path or ""

        # Compute Hashes
        sha = compute_bytes_sha256(raw_bytes)
        dhash_val = compute_dhash(asset_input)
        dhash_hex_str = f"{dhash_val:016x}"
        target_id = asset_id or f"asset_{sha[:12]}"

        # --------------------------------------------------------------------
        # Tier 1 Check: Byte-Exact SHA-256 Matching
        # --------------------------------------------------------------------
        if sha in self.sha_index:
            matched = self.sha_index[sha]
            logger.info(f"Tier 1 Duplicate detected: SHA-256 match with '{matched['asset_id']}'")
            return DeduplicationResult(
                is_duplicate=True,
                duplicate_tier="tier_1_sha256",
                matched_asset_id=matched["asset_id"],
                sha256=sha,
                dhash=dhash_val,
                dhash_hex=dhash_hex_str,
                hamming_distance=0,
                action_taken="reused_existing",
            )

        # --------------------------------------------------------------------
        # Tier 2 Check: Perceptual dHash Hamming Distance Matching
        # --------------------------------------------------------------------
        min_distance = 65
        closest_match_id = None

        for existing_dhash, existing_rec in self.dhash_index.items():
            dist = hamming_distance(dhash_val, existing_dhash)
            if dist < min_distance:
                min_distance = dist
                closest_match_id = existing_rec["asset_id"]

        if min_distance <= self.hamming_threshold and closest_match_id is not None:
            logger.info(
                f"Tier 2 Perceptual Duplicate detected: Hamming distance {min_distance} <= {self.hamming_threshold} with '{closest_match_id}'"
            )
            return DeduplicationResult(
                is_duplicate=True,
                duplicate_tier="tier_2_dhash",
                matched_asset_id=closest_match_id,
                sha256=sha,
                dhash=dhash_val,
                dhash_hex=dhash_hex_str,
                hamming_distance=min_distance,
                action_taken="rejected_near_duplicate",
            )

        # --------------------------------------------------------------------
        # Unique Asset: Register into Indices
        # --------------------------------------------------------------------
        record = {
            "asset_id": target_id,
            "sha256": sha,
            "dhash": dhash_val,
            "dhash_hex": dhash_hex_str,
            "file_path": f_path,
            "metadata": metadata or {},
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self.sha_index[sha] = record
        self.dhash_index[dhash_val] = record
        self.registry[target_id] = record

        return DeduplicationResult(
            is_duplicate=False,
            duplicate_tier=None,
            matched_asset_id=None,
            sha256=sha,
            dhash=dhash_val,
            dhash_hex=dhash_hex_str,
            hamming_distance=min_distance if min_distance <= 64 else None,
            action_taken="accepted",
        )

    def is_near_duplicate(
        self,
        candidate_input: Union[str, Path, bytes, Image.Image],
        threshold: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if candidate image is a perceptual near-duplicate of any registered asset.
        Returns: (is_duplicate: bool, matched_asset_id: Optional[str], distance: Optional[int])
        """
        eff_threshold = threshold if threshold is not None else self.hamming_threshold
        cand_dhash = compute_dhash(candidate_input)

        min_dist = 65
        closest_id = None

        for existing_dhash, existing_rec in self.dhash_index.items():
            dist = hamming_distance(cand_dhash, existing_dhash)
            if dist < min_dist:
                min_dist = dist
                closest_id = existing_rec["asset_id"]

        if min_dist <= eff_threshold and closest_id is not None:
            return True, closest_id, min_dist
        return False, None, min_dist if min_dist <= 64 else None

    def register_asset(
        self,
        asset_id: str,
        sha256: str,
        dhash: int,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Manually register an asset into the deduplication indices."""
        record = {
            "asset_id": asset_id,
            "sha256": sha256,
            "dhash": dhash,
            "dhash_hex": f"{dhash:016x}",
            "file_path": file_path or "",
            "metadata": metadata or {},
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self.sha_index[sha256] = record
        self.dhash_index[dhash] = record
        self.registry[asset_id] = record

    def get_registered_assets(self) -> List[Dict[str, Any]]:
        """Return all registered asset records."""
        return list(self.registry.values())

    def clear(self) -> None:
        """Clear all deduplication indices."""
        self.sha_index.clear()
        self.dhash_index.clear()
        self.registry.clear()

    def save_registry(self, file_path: Union[str, Path]) -> None:
        """Save registry to a JSON file."""
        p = Path(file_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.registry, indent=2), encoding="utf-8")

    def load_registry(self, file_path: Union[str, Path]) -> None:
        """Load registry from a JSON file."""
        p = Path(file_path).resolve()
        if not p.exists():
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        for asset_id, rec in data.items():
            sha = rec.get("sha256", "")
            dhash = rec.get("dhash", 0)
            self.register_asset(
                asset_id=asset_id,
                sha256=sha,
                dhash=dhash,
                file_path=rec.get("file_path"),
                metadata=rec.get("metadata"),
            )
