"""Asset provenance ledger schema and data models for R2."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from src.utils.filesystem import atomic_write, ensure_dir


@dataclass
class Dimensions:
    """Media asset visual dimensions."""
    width: int
    height: int
    aspect_ratio: str = "16:9"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": int(self.width),
            "height": int(self.height),
            "aspect_ratio": self.aspect_ratio,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dimensions":
        return cls(
            width=int(data.get("width", 1920)),
            height=int(data.get("height", 1080)),
            aspect_ratio=str(data.get("aspect_ratio", "16:9")),
        )


@dataclass
class CreatorInfo:
    """Creator or photographer attribution details."""
    name: str
    profile_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"name": self.name}
        if self.profile_url is not None:
            data["profile_url"] = self.profile_url
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CreatorInfo":
        return cls(
            name=str(data.get("name", "Unknown")),
            profile_url=data.get("profile_url"),
        )


@dataclass
class LicenseInfo:
    """Legal rights and licensing provenance."""
    license_type: str
    license_url: Optional[str] = None
    attribution_text: str = ""
    attribution_required: bool = False
    commercial_use_allowed: bool = True
    modification_allowed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "license_type": self.license_type,
            "attribution_text": self.attribution_text,
            "attribution_required": bool(self.attribution_required),
            "commercial_use_allowed": bool(self.commercial_use_allowed),
            "modification_allowed": bool(self.modification_allowed),
        }
        if self.license_url is not None:
            data["license_url"] = self.license_url
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LicenseInfo":
        return cls(
            license_type=str(data.get("license_type", "Public Domain")),
            license_url=data.get("license_url"),
            attribution_text=str(data.get("attribution_text", "")),
            attribution_required=bool(data.get("attribution_required", False)),
            commercial_use_allowed=bool(data.get("commercial_use_allowed", True)),
            modification_allowed=bool(data.get("modification_allowed", True)),
        )


@dataclass
class MediaAsset:
    """Individual media asset provenance and technical record."""
    asset_id: str
    local_path: str
    claim_id_refs: List[str] = field(default_factory=list)
    scene_target: str = ""
    media_type: str = "image/jpeg"
    absolute_path: Optional[str] = None
    file_size_bytes: int = 0
    file_sha256: str = ""
    dimensions: Optional[Dimensions] = None
    source_provider: str = "wikimedia_commons"
    source_url: str = ""
    page_url: Optional[str] = None
    creator: Optional[CreatorInfo] = None
    license: Optional[LicenseInfo] = None
    verification_status: str = "VERIFIED"
    downloaded_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "asset_id": self.asset_id,
            "claim_id_refs": list(self.claim_id_refs),
            "scene_target": self.scene_target,
            "media_type": self.media_type,
            "local_path": self.local_path,
            "file_size_bytes": int(self.file_size_bytes),
            "file_sha256": self.file_sha256,
            "source_provider": self.source_provider,
            "source_url": self.source_url,
            "verification_status": self.verification_status,
        }
        if self.absolute_path:
            data["absolute_path"] = self.absolute_path
        if self.dimensions:
            data["dimensions"] = self.dimensions.to_dict()
        if self.page_url:
            data["page_url"] = self.page_url
        if self.creator:
            data["creator"] = self.creator.to_dict()
        if self.license:
            data["license"] = self.license.to_dict()
        if self.downloaded_at:
            data["downloaded_at"] = self.downloaded_at
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MediaAsset":
        dim_data = data.get("dimensions")
        dimensions = Dimensions.from_dict(dim_data) if isinstance(dim_data, dict) else None

        creator_data = data.get("creator")
        creator = CreatorInfo.from_dict(creator_data) if isinstance(creator_data, dict) else None

        license_data = data.get("license")
        license_info = LicenseInfo.from_dict(license_data) if isinstance(license_data, dict) else None

        return cls(
            asset_id=str(data.get("asset_id", "")),
            local_path=str(data.get("local_path", "")),
            claim_id_refs=[str(c) for c in data.get("claim_id_refs", [])],
            scene_target=str(data.get("scene_target", "")),
            media_type=str(data.get("media_type", "image/jpeg")),
            absolute_path=data.get("absolute_path"),
            file_size_bytes=int(data.get("file_size_bytes", 0)),
            file_sha256=str(data.get("file_sha256", "")),
            dimensions=dimensions,
            source_provider=str(data.get("source_provider", "wikimedia_commons")),
            source_url=str(data.get("source_url", "")),
            page_url=data.get("page_url"),
            creator=creator,
            license=license_info,
            verification_status=str(data.get("verification_status", "VERIFIED")),
            downloaded_at=data.get("downloaded_at"),
        )


@dataclass
class AssetProvenanceLedger:
    """Complete provenance ledger for all project assets (Requirement R2)."""
    project_id: str
    total_assets: int
    license_summary: Dict[str, int] = field(default_factory=dict)
    assets: List[MediaAsset] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "generated_at": self.generated_at,
            "total_assets": int(self.total_assets),
            "license_summary": dict(self.license_summary),
            "assets": [a.to_dict() for a in self.assets],
        }

    def model_dump(self) -> Dict[str, Any]:
        return self.to_dict()

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetProvenanceLedger":
        raw_assets = data.get("assets") or []
        assets = [MediaAsset.from_dict(a) for a in raw_assets if isinstance(a, dict)]
        license_sum = {str(k): int(v) for k, v in (data.get("license_summary") or {}).items()}

        return cls(
            schema_version=str(data.get("schema_version", "1.0.0")),
            project_id=str(data.get("project_id", "")),
            total_assets=int(data.get("total_assets", len(assets))),
            license_summary=license_sum,
            assets=assets,
            generated_at=str(data.get("generated_at", datetime.now(timezone.utc).isoformat())),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "AssetProvenanceLedger":
        return cls.from_dict(json.loads(json_str))

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "AssetProvenanceLedger":
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a dictionary")
        return cls.from_dict(data)

    def save(
        self,
        output_dir: Union[str, Path],
        base_name: str = "asset_ledger",
    ) -> Tuple[Path, Path]:
        out_dir = ensure_dir(output_dir)
        json_path = out_dir / f"{base_name}.json"
        yaml_path = out_dir / f"{base_name}.yaml"

        atomic_write(json_path, self.to_json(indent=2), mode="w")
        atomic_write(yaml_path, self.to_yaml(), mode="w")

        return json_path, yaml_path

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "AssetProvenanceLedger":
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Ledger file not found: {p}")
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in [".yaml", ".yml"]:
            return cls.from_yaml(text)
        return cls.from_json(text)
