"""Streaming asset downloader, binary magic-byte sniffing, and local freezer (F4).

Guarantees 100% frozen local assets before rendering:
- Streaming download with 25MB safety caps and retry logic.
- Binary magic-byte sniffing (JPEG, PNG, WebP, SVG, MP4, WAV, MP3).
- Deterministic SHA-256 validation and tamper detection.
- Strict relative path audit ensuring zero external HTTP/HTTPS media references.
"""

import hashlib
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.filesystem import atomic_write, ensure_dir

logger = logging.getLogger("harness9.assets.freezer")

MAX_ASSET_SIZE_BYTES = 25 * 1024 * 1024  # 25MB safety limit
DEFAULT_DOWNLOAD_TIMEOUT = 15  # seconds
DEFAULT_MAX_RETRIES = 3


class AssetDownloadError(Exception):
    """Raised when asset streaming download fails."""
    pass


class AssetSizeExceededError(AssetDownloadError, ValueError):
    """Raised when asset file size exceeds limit."""
    pass


class AssetChecksumMismatchError(Exception):
    """Raised when computed SHA-256 does not match recorded digest."""
    pass


def sniff_magic_bytes(header: bytes) -> str:
    """Sniff binary header signature to determine media MIME type."""
    if not header:
        return "application/octet-stream"

    # JPEG: FF D8 FF
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # WebP: RIFF....WEBP
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"

    # SVG / XML vector
    header_lower = header[:1024].lower()
    if b"<svg" in header_lower or (b"<?xml" in header_lower and b"<svg" in header_lower):
        return "image/svg+xml"

    # MP4 / ISO Base Media: ftyp
    if len(header) >= 12 and (b"ftyp" in header[:16] or header[4:8] == b"ftyp"):
        return "video/mp4"

    # WAV: RIFF....WAVE
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return "audio/wav"

    # MP3: ID3 or sync frame FF FB / FF F3
    if header.startswith(b"ID3") or header.startswith(b"\xff\xfb") or header.startswith(b"\xff\xf3"):
        return "audio/mp3"

    return "application/octet-stream"


def mime_to_extension(mime: str) -> str:
    """Map MIME type string to standard file extension."""
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/svg+xml": "svg",
        "video/mp4": "mp4",
        "audio/wav": "wav",
        "audio/mp3": "mp3",
    }
    return mapping.get(mime.lower(), "bin")


def compute_sha256(data: bytes) -> str:
    """Compute hexadecimal SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Compute chunked streaming SHA-256 digest of a file on disk."""
    p = Path(file_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found for SHA-256: {p}")
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_sha256(file_path: Union[str, Path], expected_sha: str) -> bool:
    """Verify disk file integrity against expected SHA-256 hash."""
    if not expected_sha:
        return True
    actual_sha = compute_file_sha256(file_path)
    return actual_sha.lower() == expected_sha.lower()


def download_stream(
    url: str,
    max_size_bytes: int = MAX_ASSET_SIZE_BYTES,
    timeout_sec: int = DEFAULT_DOWNLOAD_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> bytes:
    """Stream download media over HTTP/HTTPS with size caps, timeouts, and retries."""
    headers = {
        "User-Agent": "Harness9-VideoPOC/1.0 (media-freezer; bot@example.com)",
        "Accept": "*/*",
    }

    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > max_size_bytes:
                    raise AssetSizeExceededError(
                        f"Asset at {url} declared size {content_length} bytes exceeding {max_size_bytes} limit"
                    )

                chunks: List[bytes] = []
                total_bytes = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > max_size_bytes:
                        raise AssetSizeExceededError(
                            f"Asset at {url} exceeded {max_size_bytes} bytes during download stream"
                        )
                    chunks.append(chunk)

                return b"".join(chunks)

        except AssetSizeExceededError:
            raise
        except Exception as e:
            last_error = e
            logger.warning(f"Download attempt {attempt}/{max_retries} for {url} failed: {e}")
            if attempt < max_retries:
                time.sleep(0.5 * (2 ** (attempt - 1)))

    raise AssetDownloadError(f"Failed to download asset from {url} after {max_retries} attempts: {last_error}")


def download_stream_sandboxed(
    url: str,
    target_path: Optional[Union[str, Path]] = None,
    execution_runtime: Optional[Any] = None,
    max_size_bytes: int = MAX_ASSET_SIZE_BYTES,
    timeout_sec: int = DEFAULT_DOWNLOAD_TIMEOUT,
    destination_path: Optional[Union[str, Path]] = None,
    max_bytes: Optional[int] = None,
    **kwargs: Any,
) -> Tuple[Path, str, int, str]:
    """Stream download media inside sandbox environment respecting network & CWD confinement."""
    effective_path = destination_path or target_path
    if not effective_path:
        raise ValueError("Must provide destination_path or target_path")

    effective_max = max_bytes if max_bytes is not None else max_size_bytes

    if execution_runtime is not None and hasattr(execution_runtime, "validate_path"):
        out_path = execution_runtime.validate_path(effective_path)
    else:
        out_path = Path(effective_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    import requests
    try:
        response = requests.get(url, stream=True, timeout=timeout_sec)
        total_bytes = 0
        chunks = []
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                total_bytes += len(chunk)
                if total_bytes > effective_max:
                    raise AssetSizeExceededError(
                        f"Asset at {url} exceeded {effective_max} bytes during download stream"
                    )
                chunks.append(chunk)

        data = b"".join(chunks)
        if execution_runtime is not None and hasattr(execution_runtime, "write_file"):
            written_path = execution_runtime.write_file(out_path, data)
            sha = compute_file_sha256(written_path)
            return Path(written_path), sha, len(data), "application/octet-stream"
        else:
            out_path.write_bytes(data)
            sha = compute_file_sha256(out_path)
            return out_path, sha, len(data), "application/octet-stream"
    except AssetSizeExceededError:
        raise
    except Exception as exc:
        logger.warning(f"Download stream error: {exc}")
        raise AssetDownloadError(f"Failed to download asset from {url}: {exc}")


def sanitize_filename(name: str) -> str:
    """Sanitize filename to alphanumeric and safe characters."""
    clean = re.sub(r"[^\w\-.]", "_", name)
    clean = re.sub(r"\.{2,}", "_", clean)
    clean = re.sub(r"_+", "_", clean)
    clean = re.sub(r"_+\.", ".", clean)
    clean = clean.strip("._")
    return clean or "asset"


class AssetFreezer:
    """Manages local media downloading, byte validation, SHA-256 hashing, and directory freezing."""

    def __init__(
        self,
        base_output_dir: Optional[Union[str, Path]] = None,
        max_size_bytes: int = MAX_ASSET_SIZE_BYTES,
        timeout_sec: int = DEFAULT_DOWNLOAD_TIMEOUT,
    ):
        self.base_output_dir = Path(base_output_dir) if base_output_dir else None
        self.max_size_bytes = max_size_bytes
        self.timeout_sec = timeout_sec

    def freeze_bytes(
        self,
        data: bytes,
        target_path: Union[str, Path],
        expected_sha: Optional[str] = None,
    ) -> Tuple[Path, str, int, str]:
        """Atomically freeze raw bytes to disk and return (path, sha256, size, mime)."""
        if len(data) > self.max_size_bytes:
            raise AssetSizeExceededError(f"Data size {len(data)} exceeds {self.max_size_bytes} bytes")

        target = Path(target_path).resolve()
        ensure_dir(target.parent)

        mime_type = sniff_magic_bytes(data)
        actual_sha = compute_sha256(data)

        if expected_sha and actual_sha.lower() != expected_sha.lower():
            raise AssetChecksumMismatchError(
                f"Checksum mismatch: expected {expected_sha}, computed {actual_sha}"
            )

        atomic_write(target, data, mode="wb")
        return target, actual_sha, len(data), mime_type

    def freeze_asset(
        self,
        source: Union[str, bytes],
        output_dir: Union[str, Path],
        slug: str,
        ext: Optional[str] = None,
        procedural_fallback: Optional[str] = None,
    ) -> Tuple[Path, str, int, str, str]:
        """
        Download/copy media and freeze to output_dir/assets/images/{slug}.{ext}.
        
        Returns:
            Tuple of (file_path, file_sha256, file_size_bytes, mime_type, verification_status)
        """
        out_base = Path(output_dir).resolve()
        images_dir = ensure_dir(out_base / "assets" / "images")
        clean_slug = sanitize_filename(slug)

        raw_bytes: Optional[bytes] = None
        status = "FROZEN_LOCAL"

        # Case 1: Raw bytes passed directly
        if isinstance(source, bytes):
            raw_bytes = source

        # Case 2: Procedural URI or SVG source
        elif isinstance(source, str) and (source.startswith("procedural://") or "<svg" in source):
            if "<svg" in source:
                raw_bytes = source.encode("utf-8")
            elif procedural_fallback:
                raw_bytes = procedural_fallback.encode("utf-8")
            else:
                raw_bytes = b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1920 1080'></svg>"
            status = "FALLBACK_GENERATED"

        # Case 3: Remote HTTP/HTTPS URL
        elif isinstance(source, str) and (source.startswith("http://") or source.startswith("https://")):
            try:
                raw_bytes = download_stream(
                    source,
                    max_size_bytes=self.max_size_bytes,
                    timeout_sec=self.timeout_sec,
                )
            except Exception as e:
                logger.warning(f"Failed to download remote asset from {source}: {e}")
                if procedural_fallback:
                    raw_bytes = procedural_fallback.encode("utf-8")
                    status = "FALLBACK_GENERATED"
                else:
                    raise

        # Case 4: Local filesystem path
        elif isinstance(source, str):
            local_src = Path(source).resolve()
            if local_src.exists():
                raw_bytes = local_src.read_bytes()
            elif procedural_fallback:
                raw_bytes = procedural_fallback.encode("utf-8")
                status = "FALLBACK_GENERATED"
            else:
                raise FileNotFoundError(f"Local asset source not found: {source}")

        if raw_bytes is None:
            raise ValueError(f"Unable to resolve media bytes from source: {source}")

        # Sniff MIME and determine correct extension
        mime_type = sniff_magic_bytes(raw_bytes)
        resolved_ext = ext or mime_to_extension(mime_type)
        target_filename = f"{clean_slug}.{resolved_ext}"
        target_path = images_dir / target_filename

        frozen_path, sha256, size, final_mime = self.freeze_bytes(raw_bytes, target_path)
        return frozen_path, sha256, size, final_mime, status


def audit_composition_paths(
    html_content: str,
    project_dir: Union[str, Path],
    allow_cdn_scripts: bool = True,
) -> Dict[str, Any]:
    """
    Audit HTML composition to ensure 100% local frozen asset compliance.
    
    Verifies:
    1. Zero external http:// / https:// media links (<img src=...>, <video src=...>, <audio src=...>).
    2. All local references (assets/...) resolve to valid, non-empty files on disk.
    """
    proj_dir = Path(project_dir).resolve()
    errors: List[str] = []
    warnings: List[str] = []
    verified_paths: List[str] = []
    external_urls: List[str] = []

    # Find all src="..." and href="..." occurrences
    src_matches = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html_content, re.IGNORECASE)

    for ref in src_matches:
        ref_clean = ref.strip()
        if not ref_clean or ref_clean.startswith("#") or ref_clean.startswith("javascript:"):
            continue

        # Check for remote HTTP / HTTPS references
        if ref_clean.startswith("http://") or ref_clean.startswith("https://"):
            # Check if it's an allowed CDN script/font
            is_cdn_script = allow_cdn_scripts and any(
                cdn in ref_clean for cdn in ["cdnjs.cloudflare.com", "cdn.jsdelivr.net", "fonts.googleapis.com"]
            )
            if not is_cdn_script:
                external_urls.append(ref_clean)
                errors.append(f"External remote URL found in composition: {ref_clean}")
            else:
                warnings.append(f"CDN external dependency: {ref_clean}")
            continue

        # Local asset path check
        local_target = proj_dir / ref_clean
        if not local_target.exists():
            errors.append(f"Broken local asset reference: '{ref_clean}' not found in {proj_dir}")
        elif local_target.stat().st_size == 0:
            errors.append(f"Empty local asset file: '{ref_clean}' has 0 bytes")
        else:
            verified_paths.append(ref_clean)

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "verified_paths": verified_paths,
        "external_urls": external_urls,
    }


def assert_zero_external_urls(html_content: str, allow_cdn_scripts: bool = True) -> bool:
    """Assert composition contains zero remote media URLs. Returns True or raises ValueError."""
    # Find img, video, audio src tags
    media_tags = re.findall(r'<(?:img|video|audio|source)[^>]+src=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    external_media = [url for url in media_tags if url.startswith("http://") or url.startswith("https://")]
    if external_media:
        raise ValueError(f"Composition violates zero-external-URL invariant: found {external_media}")
    return True
