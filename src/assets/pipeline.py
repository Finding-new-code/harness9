"""Asset pipeline orchestrator coordinating discovery, freezing, and ledger generation (F3, F4, F5)."""

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.assets.discovery import AssetDiscoveryEngine, CandidateAsset
from src.assets.freezer import AssetFreezer, sanitize_filename
from src.assets.ledger import AssetLedgerManager
from src.assets.procedural import ProceduralSVGGenerator
from src.config import AppConfig, get_default_config
from src.models.dossier import ResearchDossier
from src.models.ledger import (
    AssetProvenanceLedger,
    CreatorInfo,
    Dimensions,
    LicenseInfo,
    MediaAsset,
)
from src.utils.filesystem import ensure_dir

logger = logging.getLogger("harness9.assets.pipeline")


class AssetPipeline:
    """End-to-end asset pipeline transforming research dossiers into local frozen assets and rights ledgers."""

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        config: Optional[AppConfig] = None,
    ):
        self.output_dir = Path(output_dir) if output_dir else None
        self.config = config or get_default_config()
        self.discovery = AssetDiscoveryEngine(config=self.config)
        self.freezer = AssetFreezer(base_output_dir=self.output_dir)
        self.procedural = ProceduralSVGGenerator()

    def discover_and_freeze_assets(
        self,
        dossier: Union[ResearchDossier, Dict[str, Any]],
        output_dir: Optional[Union[str, Path]] = None,
        offline: bool = False,
        format_aspect: str = "16:9",
    ) -> AssetProvenanceLedger:
        """
        Execute Stage 2 asset discovery, local freezing, and provenance ledger generation.
        
        Args:
            dossier: ResearchDossier instance or parsed dict.
            output_dir: Target project directory for frozen assets and ledger files.
            offline: If True, forces zero-network procedural/mock asset generation.
            format_aspect: Aspect ratio ('16:9', '9:16', '1:1').
            
        Returns:
            AssetProvenanceLedger containing all frozen asset provenance records.
        """
        target_dir = Path(output_dir or self.output_dir or self.config.output_dir).resolve()
        images_dir = ensure_dir(target_dir / "assets" / "images")

        # Parse dossier properties
        if hasattr(dossier, "to_dict"):
            dossier_data = dossier.to_dict()
        elif hasattr(dossier, "model_dump"):
            dossier_data = dossier.model_dump()
        else:
            dossier_data = dict(dossier)

        topic = dossier_data.get("topic", "Technology Overview")
        claims = dossier_data.get("claims", [])
        talking_points = dossier_data.get("talking_points", [])
        visual_queries = dossier_data.get("suggested_visual_queries", [])

        # Fallback queries if list is empty
        if not visual_queries:
            for c in claims:
                cue = c.get("visual_cue_suggestion") if isinstance(c, dict) else getattr(c, "visual_cue_suggestion", "")
                if cue:
                    visual_queries.append(cue)
            if not visual_queries:
                visual_queries = [f"{topic} historical overview", f"{topic} technical schematic", f"{topic} modern impact"]

        width, height = (1920, 1080) if format_aspect == "16:9" else ((1080, 1920) if format_aspect == "9:16" else (1080, 1080))
        ledger_mgr = AssetLedgerManager(output_dir=target_dir, project_id=f"proj_{sanitize_filename(topic.lower())}")

        is_offline = offline or self.config.offline_mode

        for idx, query in enumerate(visual_queries):
            scene_target = f"scene_{idx + 1}"
            linked_claim_ids = []
            
            # Map claim IDs
            if idx < len(claims):
                c_item = claims[idx]
                cid = c_item.get("claim_id") if isinstance(c_item, dict) else getattr(c_item, "claim_id", f"claim_{idx+1:02d}")
                linked_claim_ids.append(cid)
            else:
                linked_claim_ids.append(f"claim_{idx+1:02d}")

            slug = f"asset_{idx + 1:02d}_{sanitize_filename(query.lower())[:24]}"
            asset_id = f"asset_{idx + 1:02d}"

            # Always generate a high quality procedural SVG as fallback or primary asset
            procedural_svg = self.procedural.generate_topic_svg(
                topic=topic,
                query=query,
                width=width,
                height=height,
                idx=idx + 1,
            )

            candidate: Optional[CandidateAsset] = None
            if not is_offline:
                candidates = self.discovery.search_assets(query, limit=1, offline=False)
                if candidates:
                    candidate = candidates[0]

            # If offline or no online candidate found, use procedural generator
            if is_offline or candidate is None:
                svg_bytes = procedural_svg.encode("utf-8")
                target_filename = f"{slug}.svg"
                local_rel_path = f"assets/images/{target_filename}"
                target_path = images_dir / target_filename
                
                frozen_path, sha256, size, mime = self.freezer.freeze_bytes(svg_bytes, target_path)

                ledger_mgr.record_frozen_asset(
                    asset_id=asset_id,
                    local_path=local_rel_path,
                    absolute_path=str(frozen_path),
                    file_size_bytes=size,
                    file_sha256=sha256,
                    media_type="image/svg+xml",
                    dimensions=Dimensions(width=width, height=height, aspect_ratio=format_aspect),
                    source_provider="procedural_generator",
                    source_url=f"procedural://vector/{slug}.svg",
                    page_url=None,
                    creator=CreatorInfo(name="Harness 9 Procedural Asset Engine", profile_url="https://github.com/nousresearch/hermes-agent"),
                    license_info=LicenseInfo(
                        license_type="CC0-1.0 (Public Domain)",
                        license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                        attribution_text="Procedural SVG Graphic by Harness 9 Engine (CC0)",
                        attribution_required=False,
                        commercial_use_allowed=True,
                        modification_allowed=True,
                    ),
                    scene_target=scene_target,
                    claim_id_refs=linked_claim_ids,
                    verification_status="FALLBACK_GENERATED" if is_offline else "VERIFIED",
                )
            else:
                # Online candidate found -> attempt download and freeze
                try:
                    frozen_path, sha256, size, mime, status = self.freezer.freeze_asset(
                        source=candidate.source_url,
                        output_dir=target_dir,
                        slug=slug,
                        procedural_fallback=procedural_svg,
                    )
                    local_rel_path = f"assets/images/{frozen_path.name}"

                    if status == "FALLBACK_GENERATED":
                        ledger_mgr.record_frozen_asset(
                            asset_id=asset_id,
                            local_path=local_rel_path,
                            absolute_path=str(frozen_path),
                            file_size_bytes=size,
                            file_sha256=sha256,
                            media_type=mime,
                            dimensions=Dimensions(width=width, height=height, aspect_ratio=format_aspect),
                            source_provider="procedural_generator",
                            source_url=f"procedural://vector/{slug}.svg",
                            creator=CreatorInfo(name="Harness 9 Procedural Asset Engine"),
                            license_info=LicenseInfo(
                                license_type="CC0-1.0 (Public Domain)",
                                attribution_text="Procedural SVG Graphic by Harness 9 Engine (CC0)",
                                attribution_required=False,
                                commercial_use_allowed=True,
                                modification_allowed=True,
                            ),
                            scene_target=scene_target,
                            claim_id_refs=linked_claim_ids,
                            verification_status="FALLBACK_GENERATED",
                        )
                    else:
                        ledger_mgr.record_frozen_asset(
                            asset_id=asset_id,
                            local_path=local_rel_path,
                            absolute_path=str(frozen_path),
                            file_size_bytes=size,
                            file_sha256=sha256,
                            media_type=mime,
                            dimensions=Dimensions(width=candidate.width, height=candidate.height, aspect_ratio=format_aspect),
                            source_provider=candidate.source_provider,
                            source_url=candidate.source_url,
                            page_url=candidate.page_url,
                            creator=CreatorInfo(name=candidate.creator_name, profile_url=candidate.creator_profile_url),
                            license_info=LicenseInfo(
                                license_type=candidate.license_type,
                                license_url=candidate.license_url,
                                attribution_text=candidate.attribution_text,
                                attribution_required=candidate.attribution_required,
                                commercial_use_allowed=candidate.commercial_use_allowed,
                                modification_allowed=candidate.modification_allowed,
                            ),
                            scene_target=scene_target,
                            claim_id_refs=linked_claim_ids,
                            verification_status=status,
                        )
                except Exception as e:
                    logger.warning(f"Freezing candidate asset failed for {query}, using procedural fallback: {e}")
                    svg_bytes = procedural_svg.encode("utf-8")
                    target_filename = f"{slug}.svg"
                    local_rel_path = f"assets/images/{target_filename}"
                    target_path = images_dir / target_filename
                    frozen_path, sha256, size, mime = self.freezer.freeze_bytes(svg_bytes, target_path)

                    ledger_mgr.record_frozen_asset(
                        asset_id=asset_id,
                        local_path=local_rel_path,
                        absolute_path=str(frozen_path),
                        file_size_bytes=size,
                        file_sha256=sha256,
                        media_type="image/svg+xml",
                        dimensions=Dimensions(width=width, height=height, aspect_ratio=format_aspect),
                        source_provider="procedural_generator",
                        source_url=f"procedural://vector/{slug}.svg",
                        creator=CreatorInfo(name="Harness 9 Procedural Asset Engine"),
                        license_info=LicenseInfo(
                            license_type="CC0-1.0 (Public Domain)",
                            attribution_text="Procedural SVG Graphic by Harness 9 Engine (CC0)",
                            attribution_required=False,
                            commercial_use_allowed=True,
                            modification_allowed=True,
                        ),
                        scene_target=scene_target,
                        claim_id_refs=linked_claim_ids,
                        verification_status="FALLBACK_GENERATED",
                    )

        # Save both asset_ledger.json and asset_ledger.yaml
        ledger_mgr.save(target_dir, base_name="asset_ledger")
        validation = ledger_mgr.validate_ledger(project_dir=target_dir)
        if not validation["valid"]:
            logger.warning(f"Ledger validation warnings/errors: {validation['errors']}")

        return ledger_mgr.ledger
