"""Media discovery adapters for Wikimedia Commons, Pexels, NASA, and Offline Mock (F3)."""

import html
import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.config import AppConfig, get_default_config
from src.models.ledger import CreatorInfo, Dimensions, LicenseInfo, MediaAsset

logger = logging.getLogger("harness9.assets.discovery")


@dataclass
class CandidateAsset:
    """Discovered media candidate before local freezing."""
    title: str
    source_provider: str
    source_url: str
    page_url: Optional[str] = None
    media_type: str = "image/jpeg"
    width: int = 1920
    height: int = 1080
    creator_name: str = "Unknown"
    creator_profile_url: Optional[str] = None
    license_type: str = "Public Domain"
    license_url: Optional[str] = None
    attribution_text: str = ""
    attribution_required: bool = False
    commercial_use_allowed: bool = True
    modification_allowed: bool = True
    query_matched: str = ""
    confidence_score: float = 1.0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "source_provider": self.source_provider,
            "source_url": self.source_url,
            "page_url": self.page_url,
            "media_type": self.media_type,
            "width": self.width,
            "height": self.height,
            "creator_name": self.creator_name,
            "creator_profile_url": self.creator_profile_url,
            "license_type": self.license_type,
            "license_url": self.license_url,
            "attribution_text": self.attribution_text,
            "attribution_required": self.attribution_required,
            "commercial_use_allowed": self.commercial_use_allowed,
            "modification_allowed": self.modification_allowed,
            "query_matched": self.query_matched,
            "confidence_score": self.confidence_score,
        }

    def to_media_asset(
        self,
        asset_id: str,
        local_path: str,
        file_size_bytes: int,
        file_sha256: str,
        scene_target: str = "",
        claim_id_refs: Optional[List[str]] = None,
        verification_status: str = "VERIFIED",
    ) -> MediaAsset:
        """Convert CandidateAsset to validated MediaAsset model."""
        aspect_ratio = "16:9"
        if self.height > 0:
            ratio_val = self.width / self.height
            if abs(ratio_val - 16 / 9) < 0.1:
                aspect_ratio = "16:9"
            elif abs(ratio_val - 9 / 16) < 0.1:
                aspect_ratio = "9:16"
            elif abs(ratio_val - 1.0) < 0.1:
                aspect_ratio = "1:1"
            else:
                aspect_ratio = f"{self.width}:{self.height}"

        return MediaAsset(
            asset_id=asset_id,
            local_path=local_path,
            claim_id_refs=claim_id_refs or [],
            scene_target=scene_target,
            media_type=self.media_type,
            file_size_bytes=file_size_bytes,
            file_sha256=file_sha256,
            dimensions=Dimensions(
                width=self.width,
                height=self.height,
                aspect_ratio=aspect_ratio,
            ),
            source_provider=self.source_provider,
            source_url=self.source_url,
            page_url=self.page_url,
            creator=CreatorInfo(
                name=self.creator_name,
                profile_url=self.creator_profile_url,
            ),
            license=LicenseInfo(
                license_type=self.license_type,
                license_url=self.license_url,
                attribution_text=self.attribution_text or f"Asset by {self.creator_name} ({self.license_type})",
                attribution_required=self.attribution_required,
                commercial_use_allowed=self.commercial_use_allowed,
                modification_allowed=self.modification_allowed,
            ),
            verification_status=verification_status,
        )


def _strip_html(text: str) -> str:
    """Strip HTML markup and unescape HTML entities."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    return html.unescape(clean).strip()


class WikimediaProvider:
    """Wikimedia Commons MediaWiki Action API adapter with ExtMetadata extraction."""

    BASE_URL = "https://commons.wikimedia.org/w/api.php"
    USER_AGENT = "Harness9-VideoPOC/1.0 (https://github.com/nousresearch/hermes-agent; research@nousresearch.com)"

    def __init__(self, timeout_sec: int = 10):
        self.timeout_sec = timeout_sec

    def search(self, query: str, limit: int = 5) -> List[CandidateAsset]:
        """Query Wikimedia Commons search API and extract metadata."""
        if not query.strip():
            return []

        search_term = f"{query.strip()} filetype:bitmap"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": search_term,
            "gsrnamespace": "6",  # File namespace
            "gsrlimit": str(min(limit, 10)),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata|dimensions",
            "iiurlwidth": "1920",
        }

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status != 200:
                    logger.warning(f"Wikimedia API returned status {resp.status}")
                    return []
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Wikimedia API query failed for '{query}': {e}")
            return []

        query_data = payload.get("query", {})
        pages = query_data.get("pages", {})
        results: List[CandidateAsset] = []

        for page_id, page_info in pages.items():
            image_infos = page_info.get("imageinfo", [])
            if not image_infos:
                continue

            info = image_infos[0]
            file_url = info.get("thumburl") or info.get("url")
            desc_url = info.get("descriptionurl") or page_info.get("fullurl")
            mime = info.get("mime", "image/jpeg")

            # Only accept supported image and video MIME types
            if not (mime.startswith("image/") or mime.startswith("video/")):
                continue

            width = int(info.get("thumbwidth") or info.get("width") or 1920)
            height = int(info.get("thumbheight") or info.get("height") or 1080)

            ext_meta = info.get("extmetadata", {})
            raw_license = ext_meta.get("LicenseShortName", {}).get("value") or ext_meta.get("License", {}).get("value") or "Public domain"
            license_url = ext_meta.get("LicenseUrl", {}).get("value")
            
            raw_artist = ext_meta.get("Artist", {}).get("value") or ext_meta.get("Credit", {}).get("value") or "Wikimedia Contributor"
            clean_artist = _strip_html(raw_artist) or "Wikimedia Contributor"
            
            clean_license = _strip_html(raw_license)
            is_pd = "public domain" in clean_license.lower() or "cc0" in clean_license.lower() or "no copyright" in clean_license.lower()
            attr_req = not is_pd
            comm_ok = "nc" not in clean_license.lower() and "noncommercial" not in clean_license.lower()
            mod_ok = "nd" not in clean_license.lower() and "noderivatives" not in clean_license.lower()

            attr_text = f"Photo by {clean_artist} via Wikimedia Commons ({clean_license})"

            results.append(
                CandidateAsset(
                    title=page_info.get("title", f"File:{query}"),
                    source_provider="wikimedia_commons",
                    source_url=file_url,
                    page_url=desc_url,
                    media_type=mime,
                    width=width,
                    height=height,
                    creator_name=clean_artist,
                    creator_profile_url="https://commons.wikimedia.org",
                    license_type=clean_license,
                    license_url=license_url,
                    attribution_text=attr_text,
                    attribution_required=attr_req,
                    commercial_use_allowed=comm_ok,
                    modification_allowed=mod_ok,
                    query_matched=query,
                    confidence_score=0.95,
                    raw_metadata=ext_meta,
                )
            )

        return results


class PexelsProvider:
    """Pexels REST API adapter with authentication and Pexels License mapping."""

    BASE_URL = "https://api.pexels.com/v1/search"

    def __init__(self, api_key: Optional[str] = None, timeout_sec: int = 10):
        self.api_key = api_key
        self.timeout_sec = timeout_sec

    def search(self, query: str, limit: int = 5) -> List[CandidateAsset]:
        """Search Pexels for photos matching query."""
        if not self.api_key or not query.strip():
            return []

        params = {
            "query": query.strip(),
            "per_page": str(min(limit, 10)),
            "orientation": "landscape",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": self.api_key,
                "User-Agent": "Harness9-VideoPOC/1.0",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status != 200:
                    logger.warning(f"Pexels API status: {resp.status}")
                    return []
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Pexels search failed for '{query}': {e}")
            return []

        photos = payload.get("photos", [])
        results: List[CandidateAsset] = []

        for photo in photos:
            src_map = photo.get("src", {})
            img_url = src_map.get("large2x") or src_map.get("large") or src_map.get("original")
            if not img_url:
                continue

            photographer = photo.get("photographer", "Pexels Creator")
            photographer_url = photo.get("photographer_url")
            page_url = photo.get("url")
            width = int(photo.get("width", 1920))
            height = int(photo.get("height", 1080))

            results.append(
                CandidateAsset(
                    title=f"Pexels Photo {photo.get('id', '')} - {query}",
                    source_provider="pexels",
                    source_url=img_url,
                    page_url=page_url,
                    media_type="image/jpeg",
                    width=width,
                    height=height,
                    creator_name=photographer,
                    creator_profile_url=photographer_url,
                    license_type="Pexels License",
                    license_url="https://www.pexels.com/license/",
                    attribution_text=f"Photo by {photographer} on Pexels",
                    attribution_required=False,
                    commercial_use_allowed=True,
                    modification_allowed=True,
                    query_matched=query,
                    confidence_score=0.90,
                    raw_metadata=photo,
                )
            )

        return results


class NASAProvider:
    """NASA Image & Video Library API adapter."""

    BASE_URL = "https://images-api.nasa.gov/search"

    def __init__(self, timeout_sec: int = 10):
        self.timeout_sec = timeout_sec

    def search(self, query: str, limit: int = 5) -> List[CandidateAsset]:
        """Search NASA media library for space & aerospace assets."""
        if not query.strip():
            return []

        params = {
            "q": query.strip(),
            "media_type": "image",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Harness9-VideoPOC/1.0",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status != 200:
                    return []
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"NASA API query failed for '{query}': {e}")
            return []

        collection = payload.get("collection", {})
        items = collection.get("items", [])[:limit]
        results: List[CandidateAsset] = []

        for item in items:
            data_list = item.get("data", [])
            links = item.get("links", [])
            if not data_list or not links:
                continue

            data_info = data_list[0]
            img_url = links[0].get("href")
            if not img_url:
                continue

            title = data_info.get("title", f"NASA - {query}")
            center = data_info.get("center", "NASA")
            photographer = data_info.get("photographer") or f"NASA / {center}"
            desc = data_info.get("description", "")

            results.append(
                CandidateAsset(
                    title=title,
                    source_provider="nasa_gov",
                    source_url=img_url,
                    page_url=f"https://images.nasa.gov/details-{data_info.get('nasa_id', '')}",
                    media_type="image/jpeg",
                    width=1920,
                    height=1080,
                    creator_name=photographer,
                    creator_profile_url="https://images.nasa.gov",
                    license_type="NASA Public Domain",
                    license_url="https://www.nasa.gov/multimedia/guidelines/index.html",
                    attribution_text=f"Image courtesy of NASA / {center}",
                    attribution_required=False,
                    commercial_use_allowed=True,
                    modification_allowed=True,
                    query_matched=query,
                    confidence_score=0.92,
                    raw_metadata=data_info,
                )
            )

        return results


class OfflineMockProvider:
    """Deterministic offline mock discovery engine for benchmark and procedural topics."""

    MOCK_CATALOG = {
        "transistor": [
            {
                "title": "Replica of Point-Contact Transistor (1947)",
                "source_url": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Replica-of-first-transistor.jpg",
                "page_url": "https://commons.wikimedia.org/wiki/File:Replica-of-first-transistor.jpg",
                "media_type": "image/jpeg",
                "creator_name": "Bell Laboratories / Nokia",
                "license_type": "Public Domain",
                "attribution_text": "Replica of first transistor by Bell Labs, Public Domain via Wikimedia Commons",
            },
            {
                "title": "Bardeen, Brattain, and Shockley at Bell Labs (1948)",
                "source_url": "https://upload.wikimedia.org/wikipedia/commons/b/b2/Bardeen_Brattain_Shockley_1948.jpg",
                "page_url": "https://commons.wikimedia.org/wiki/File:Bardeen_Brattain_Shockley_1948.jpg",
                "media_type": "image/jpeg",
                "creator_name": "AT&T Technologies",
                "license_type": "CC-BY-SA 3.0",
                "attribution_text": "Photo of Bardeen, Brattain, Shockley (1948) by AT&T under CC-BY-SA 3.0",
            },
            {
                "title": "Microscopic Silicon Wafer Die Circuitry",
                "source_url": "https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg",
                "page_url": "https://www.pexels.com/photo/close-up-of-microchip-2582937/",
                "media_type": "image/jpeg",
                "creator_name": "Alexandre Debiève",
                "license_type": "Pexels License",
                "attribution_text": "Photo by Alexandre Debiève on Pexels",
            },
        ],
        "gpu": [
            {
                "title": "GPU Die Microarchitecture and Compute Units",
                "source_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/GPU_die.jpg/1920px-GPU_die.jpg",
                "page_url": "https://commons.wikimedia.org/wiki/File:GPU_die.jpg",
                "media_type": "image/jpeg",
                "creator_name": "Hardware Anatomy Archive",
                "license_type": "CC-BY-SA 4.0",
                "attribution_text": "GPU Die Architecture under CC-BY-SA 4.0",
            },
            {
                "title": "Parallel Processor Silicon Wafer Array",
                "source_url": "https://images.pexels.com/photos/373543/pexels-photo-373543.jpeg",
                "page_url": "https://www.pexels.com/photo/computer-chip-373543/",
                "media_type": "image/jpeg",
                "creator_name": "Pixabay / Pexels",
                "license_type": "Pexels License",
                "attribution_text": "Photo by Pixabay on Pexels",
            },
        ],
        "apollo": [
            {
                "title": "Apollo Guidance Computer (AGC) Display and Keyboard (DSKY)",
                "source_url": "https://images-assets.nasa.gov/image/S69-38827/S69-38827~orig.jpg",
                "page_url": "https://images.nasa.gov/details-S69-38827",
                "media_type": "image/jpeg",
                "creator_name": "NASA Johnson Space Center",
                "license_type": "NASA Public Domain",
                "attribution_text": "NASA Apollo 11 Guidance Computer DSKY, NASA Public Domain",
            }
        ],
    }

    def __init__(self):
        pass

    def search(self, query: str, limit: int = 5) -> List[CandidateAsset]:
        """Return cataloged offline mock candidate assets."""
        q_lower = query.lower()
        matched_category = None
        for key in self.MOCK_CATALOG:
            if key in q_lower:
                matched_category = key
                break

        results: List[CandidateAsset] = []
        if matched_category:
            entries = self.MOCK_CATALOG[matched_category]
            for entry in entries[:limit]:
                results.append(
                    CandidateAsset(
                        title=entry["title"],
                        source_provider="offline_mock",
                        source_url=entry["source_url"],
                        page_url=entry["page_url"],
                        media_type=entry["media_type"],
                        width=1920,
                        height=1080,
                        creator_name=entry["creator_name"],
                        creator_profile_url="https://commons.wikimedia.org",
                        license_type=entry["license_type"],
                        license_url="https://creativecommons.org/licenses/",
                        attribution_text=entry["attribution_text"],
                        attribution_required="CC" in entry["license_type"],
                        commercial_use_allowed=True,
                        modification_allowed=True,
                        query_matched=query,
                        confidence_score=1.0,
                    )
                )

        # If no specific catalog match, generate procedural asset candidate
        if not results:
            safe_slug = re.sub(r"[^a-z0-9_]+", "_", query.lower()).strip("_") or "overview"
            results.append(
                CandidateAsset(
                    title=f"Procedural Vector Graphic: {query}",
                    source_provider="procedural_generator",
                    source_url=f"procedural://vector/{safe_slug}.svg",
                    page_url=None,
                    media_type="image/svg+xml",
                    width=1920,
                    height=1080,
                    creator_name="Harness 9 Procedural Engine",
                    creator_profile_url="https://github.com/nousresearch/hermes-agent",
                    license_type="CC0-1.0 (Public Domain)",
                    license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                    attribution_text="Procedural SVG Graphic by Harness 9 Engine (CC0)",
                    attribution_required=False,
                    commercial_use_allowed=True,
                    modification_allowed=True,
                    query_matched=query,
                    confidence_score=1.0,
                )
            )

        return results


class AssetDiscoveryEngine:
    """Unified asset discovery orchestrator across Wikimedia, Pexels, NASA, and Offline fallback."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_default_config()
        self.wikimedia = WikimediaProvider(timeout_sec=self.config.search_timeout_sec)
        self.pexels = PexelsProvider(api_key=self.config.pexels_api_key, timeout_sec=self.config.search_timeout_sec)
        self.nasa = NASAProvider(timeout_sec=self.config.search_timeout_sec)
        self.offline_mock = OfflineMockProvider()

    def search_assets(
        self,
        query: str,
        limit: int = 5,
        providers: Optional[List[str]] = None,
        offline: bool = False,
    ) -> List[CandidateAsset]:
        """Search across providers and return deduplicated candidate assets."""
        if offline or self.config.offline_mode:
            return self.offline_mock.search(query, limit=limit)

        provider_order = providers or ["wikimedia", "pexels", "nasa"]
        accumulated: List[CandidateAsset] = []
        seen_urls = set()

        for prov_name in provider_order:
            if len(accumulated) >= limit:
                break

            prov_results: List[CandidateAsset] = []
            if prov_name == "wikimedia":
                prov_results = self.wikimedia.search(query, limit=limit - len(accumulated))
            elif prov_name == "pexels" and self.config.pexels_api_key:
                prov_results = self.pexels.search(query, limit=limit - len(accumulated))
            elif prov_name == "nasa":
                prov_results = self.nasa.search(query, limit=limit - len(accumulated))

            for r in prov_results:
                if r.source_url not in seen_urls:
                    seen_urls.add(r.source_url)
                    accumulated.append(r)

        # Fall back to offline mock if online search yielded no results
        if not accumulated:
            accumulated = self.offline_mock.search(query, limit=limit)

        return accumulated[:limit]


# Backward compatibility aliases
WikimediaProvider = WikimediaProvider
PexelsProvider = PexelsProvider
NASAProvider = NASAProvider
AssetDiscoveryEngine = AssetDiscoveryEngine
CandidateAsset = CandidateAsset
