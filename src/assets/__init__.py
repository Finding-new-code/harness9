"""src.assets — Milestone 2: Asset Discovery, Rights Ledger & Local Freezing (R2)."""

from src.assets.deduplication import (
    AssetDeduplicator,
    DeduplicationResult,
    compute_bytes_sha256,
    compute_dhash,
    compute_dhash_hex,
    hamming_distance,
    hamming_distance_hex,
)
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
    sniff_magic_bytes,
    verify_sha256,
)
from src.assets.ledger import AssetLedgerManager, LedgerManager
from src.assets.pipeline import AssetPipeline
from src.assets.procedural import ProceduralSVGGenerator
from src.models.ledger import (
    AssetProvenanceLedger,
    CreatorInfo,
    Dimensions,
    LicenseInfo,
    MediaAsset,
)

__all__ = [
    "AssetPipeline",
    "AssetDiscoveryEngine",
    "CandidateAsset",
    "WikimediaProvider",
    "PexelsProvider",
    "NASAProvider",
    "OfflineMockProvider",
    "AssetFreezer",
    "AssetDownloadError",
    "AssetSizeExceededError",
    "AssetChecksumMismatchError",
    "sniff_magic_bytes",
    "compute_sha256",
    "compute_file_sha256",
    "verify_sha256",
    "audit_composition_paths",
    "assert_zero_external_urls",
    "AssetLedgerManager",
    "LedgerManager",
    "ProceduralSVGGenerator",
    "AssetProvenanceLedger",
    "MediaAsset",
    "Dimensions",
    "CreatorInfo",
    "LicenseInfo",
    "AssetDeduplicator",
    "DeduplicationResult",
    "compute_bytes_sha256",
    "compute_dhash",
    "compute_dhash_hex",
    "hamming_distance",
    "hamming_distance_hex",
]

