"""Asset provenance ledger manager and serialization engine (F4).

Tracks the complete legal and technical lifecycle of media assets:
- Rights and license attribution (CC, Public Domain, Pexels)
- SHA-256 file hashes and byte counts
- Schema validation and verification status tracking
- Dual JSON and YAML serialization (asset_ledger.json / asset_ledger.yaml)
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.models.ledger import (
    AssetProvenanceLedger,
    CreatorInfo,
    Dimensions,
    LicenseInfo,
    MediaAsset,
)
from src.utils.filesystem import atomic_write, ensure_dir

logger = logging.getLogger("harness9.assets.ledger")


class AssetLedgerManager:
    """Manages the creation, mutation, validation, and serialization of AssetProvenanceLedger."""

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        project_id: Optional[str] = None,
    ):
        self.output_dir = Path(output_dir) if output_dir else None
        self.project_id = project_id or f"proj_{int(datetime.now(timezone.utc).timestamp())}"
        self.ledger = AssetProvenanceLedger(
            project_id=self.project_id,
            total_assets=0,
            license_summary={},
            assets=[],
        )

    def create_empty_ledger(self, project_id: str) -> AssetProvenanceLedger:
        """Initialize a fresh empty ledger instance."""
        self.project_id = project_id
        self.ledger = AssetProvenanceLedger(
            project_id=project_id,
            total_assets=0,
            license_summary={},
            assets=[],
        )
        return self.ledger

    def add_asset(self, asset: MediaAsset) -> None:
        """Add or update an individual MediaAsset in the ledger."""
        # Replace if existing asset_id matches, else append
        existing_idx = next(
            (i for i, a in enumerate(self.ledger.assets) if a.asset_id == asset.asset_id),
            None,
        )
        if existing_idx is not None:
            self.ledger.assets[existing_idx] = asset
        else:
            self.ledger.assets.append(asset)

        self.update_license_summary()

    def get_asset(self, asset_id: str) -> Optional[MediaAsset]:
        """Retrieve MediaAsset record by asset_id."""
        for a in self.ledger.assets:
            if a.asset_id == asset_id:
                return a
        return None

    def list_assets(self) -> List[MediaAsset]:
        """Return list of all registered media assets."""
        return list(self.ledger.assets)

    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset from the ledger by asset_id."""
        orig_len = len(self.ledger.assets)
        self.ledger.assets = [a for a in self.ledger.assets if a.asset_id != asset_id]
        if len(self.ledger.assets) != orig_len:
            self.update_license_summary()
            return True
        return False

    def update_license_summary(self) -> Dict[str, int]:
        """Recalculate summary counts of all asset licenses."""
        summary: Dict[str, int] = {}
        for a in self.ledger.assets:
            lic_type = a.license.license_type if a.license else "Unknown"
            summary[lic_type] = summary.get(lic_type, 0) + 1

        self.ledger.total_assets = len(self.ledger.assets)
        self.ledger.license_summary = summary
        return summary

    def record_frozen_asset(
        self,
        asset_id: str,
        local_path: str,
        file_size_bytes: int,
        file_sha256: str,
        media_type: str = "image/jpeg",
        dimensions: Optional[Dimensions] = None,
        source_provider: str = "wikimedia_commons",
        source_url: str = "",
        page_url: Optional[str] = None,
        creator: Optional[CreatorInfo] = None,
        license_info: Optional[LicenseInfo] = None,
        scene_target: str = "",
        claim_id_refs: Optional[List[str]] = None,
        verification_status: str = "FROZEN_LOCAL",
        absolute_path: Optional[str] = None,
    ) -> MediaAsset:
        """Helper to build, register, and return a MediaAsset record."""
        asset = MediaAsset(
            asset_id=asset_id,
            local_path=local_path,
            absolute_path=absolute_path,
            claim_id_refs=claim_id_refs or [],
            scene_target=scene_target,
            media_type=media_type,
            file_size_bytes=file_size_bytes,
            file_sha256=file_sha256,
            dimensions=dimensions or Dimensions(width=1920, height=1080, aspect_ratio="16:9"),
            source_provider=source_provider,
            source_url=source_url,
            page_url=page_url,
            creator=creator or CreatorInfo(name="Unknown"),
            license=license_info or LicenseInfo(license_type="Public Domain"),
            verification_status=verification_status,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )
        self.add_asset(asset)
        return asset

    def save(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        base_name: str = "asset_ledger",
    ) -> Tuple[Path, Path]:
        """Save the ledger atomically to both JSON and YAML."""
        target_dir = ensure_dir(output_dir or self.output_dir or Path.cwd())
        self.update_license_summary()
        return self.ledger.save(target_dir, base_name=base_name)

    def load(self, file_path: Union[str, Path]) -> AssetProvenanceLedger:
        """Load ledger from JSON or YAML file."""
        self.ledger = AssetProvenanceLedger.load(file_path)
        self.project_id = self.ledger.project_id
        return self.ledger

    def validate_ledger(
        self,
        ledger: Optional[AssetProvenanceLedger] = None,
        project_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """
        Validate ledger completeness, schema adherence, and on-disk file checksums.
        """
        target_ledger = ledger or self.ledger
        base_dir = Path(project_dir or self.output_dir or Path.cwd()).resolve()

        errors: List[str] = []
        warnings: List[str] = []

        if not target_ledger.project_id:
            errors.append("Ledger missing project_id")

        if len(target_ledger.assets) == 0:
            warnings.append("Ledger contains 0 assets")

        if target_ledger.total_assets != len(target_ledger.assets):
            errors.append(
                f"total_assets count ({target_ledger.total_assets}) does not match assets list length ({len(target_ledger.assets)})"
            )

        for i, a in enumerate(target_ledger.assets):
            if not a.asset_id:
                errors.append(f"Asset #{i} missing asset_id")
            if not a.local_path:
                errors.append(f"Asset '{a.asset_id}' missing local_path")
            if not a.source_url:
                errors.append(f"Asset '{a.asset_id}' missing source_url")
            if not a.creator or not a.creator.name:
                errors.append(f"Asset '{a.asset_id}' missing creator information")
            if not a.license or not a.license.license_type:
                errors.append(f"Asset '{a.asset_id}' missing license information")

            # Check file presence and checksum on disk if project_dir or output_dir is available
            if a.local_path and (project_dir or self.output_dir):
                disk_path = base_dir / a.local_path
                if not disk_path.exists():
                    errors.append(f"Asset '{a.asset_id}' local file missing on disk: {disk_path}")
                elif a.file_sha256:
                    actual_sha = hashlib.sha256(disk_path.read_bytes()).hexdigest()
                    if actual_sha.lower() != a.file_sha256.lower():
                        errors.append(
                            f"Asset '{a.asset_id}' SHA-256 mismatch (expected {a.file_sha256[:8]}, actual {actual_sha[:8]})"
                        )

        is_valid = len(errors) == 0
        return {
            "valid": is_valid,
            "asset_count": len(target_ledger.assets),
            "errors": errors,
            "warnings": warnings,
            "license_summary": target_ledger.license_summary,
        }


# Alias for backward compatibility
LedgerManager = AssetLedgerManager
