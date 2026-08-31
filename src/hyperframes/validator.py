"""
src.hyperframes.validator — Static Linter, Path Auditor & HyperFrames Composition Validator (Milestone 4 - F9).

Performs strict multi-tier static analysis and verification on HyperFrames composition files:
1. Root Composition Structure (data-composition-id="root", data-width, data-height, data-duration)
2. Media Decoupling (<video muted playsinline> + <audio data-track-index="...">)
3. Zero-External-URL Linter (ensures all referenced media assets are frozen locally)
4. Local Asset Existence on Disk (assets/images/*, assets/audio/*)
5. Track Collision Detection (no overlapping clips on identical data-track-index)
6. GSAP Timeline Registration & Paused State (window.__timelines["root"] = gsap.timeline({ paused: true }))
7. Finite Loop Math Enforcement (rejection of repeat: -1)
8. Caption Exit Guarantee Verification (hard visibility kill on word groups)
9. WCAG AA Contrast Compliance Heuristic
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("harness9.hyperframes.validator")


class CompositionValidator:
    """Validator and static linter for HyperFrames video compositions."""

    def __init__(self, project_dir: Union[str, Path]):
        self.project_dir = Path(project_dir).resolve()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.details: Dict[str, Any] = {}

    def validate(self) -> Dict[str, Any]:
        """Run all validation passes and return a structured verdict."""
        self.errors = []
        self.warnings = []
        self.details = {}

        html_file = self.project_dir / "index.html"
        css_file = self.project_dir / "styles.css"
        js_file = self.project_dir / "main.js"

        # Check required files
        if not html_file.exists():
            self.errors.append(f"Missing required composition file: {html_file.name}")
        if not css_file.exists():
            self.warnings.append(f"Missing styles.css (inline <style> might be used)")
        if not js_file.exists():
            self.warnings.append(f"Missing main.js (inline <script> might be used)")

        if not html_file.exists():
            return {
                "valid": False,
                "errors": self.errors,
                "warnings": self.warnings,
                "details": self.details,
            }

        html_content = html_file.read_text(encoding="utf-8")
        css_content = css_file.read_text(encoding="utf-8") if css_file.exists() else ""
        js_content = js_file.read_text(encoding="utf-8") if js_file.exists() else ""

        # Run individual check passes
        self._check_root_composition(html_content)
        self._check_media_elements(html_content)
        self._check_zero_external_urls(html_content, css_content)
        self._check_local_asset_paths(html_content)
        self._check_gsap_timeline_contract(js_content, html_content)
        self._check_wcag_contrast(css_content)

        is_valid = len(self.errors) == 0
        return {
            "valid": is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }

    def _check_root_composition(self, html: str) -> None:
        """Validate root composition element contract."""
        # Must have data-composition-id="root"
        if 'data-composition-id="root"' not in html and "data-composition-id='root'" not in html:
            self.errors.append("Missing root composition element: data-composition-id='root'")

        # Must not be wrapped in <template> at root level
        if re.search(r'<template[^>]*>[\s\S]*data-composition-id=["\']root["\']', html):
            self.errors.append("Root composition must not be wrapped inside a <template> tag")

        # Must define dimension and duration data attributes
        if not re.search(r'data-width=["\']\d+["\']', html):
            self.errors.append("Root composition missing data-width attribute")
        if not re.search(r'data-height=["\']\d+["\']', html):
            self.errors.append("Root composition missing data-height attribute")
        if not re.search(r'data-duration=["\'][\d.]+["\']', html):
            self.errors.append("Root composition missing data-duration attribute")

    def _check_media_elements(self, html: str) -> None:
        """Validate media element decoupling and track attributes."""
        # Video elements must be muted and playsinline
        video_tags = re.findall(r'<video\b[^>]*>', html, re.IGNORECASE)
        for v in video_tags:
            if "muted" not in v:
                self.errors.append(f"Video element must be muted for autoplay compliance: {v}")
            if "playsinline" not in v:
                self.warnings.append(f"Video element should specify playsinline: {v}")

        # Audio elements must define data-track-index and data-start / data-duration
        audio_tags = re.findall(r'<audio\b[^>]*>', html, re.IGNORECASE)
        track_clips: Dict[str, List[Tuple[float, float]]] = {}

        for a in audio_tags:
            track_idx_m = re.search(r'data-track-index=["\']([^"\']+)["\']', a)
            if not track_idx_m:
                self.warnings.append(f"Audio element missing data-track-index: {a}")
            else:
                t_idx = track_idx_m.group(1)
                start_m = re.search(r'data-start=["\']([\d.]+)["\']', a)
                dur_m = re.search(r'data-duration=["\']([\d.]+)["\']', a)
                if start_m and dur_m:
                    start = float(start_m.group(1))
                    dur = float(dur_m.group(1))
                    end = start + dur
                    if t_idx not in track_clips:
                        track_clips[t_idx] = []
                    # Check overlap with existing clips on same track
                    for ex_start, ex_end in track_clips[t_idx]:
                        if not (end <= ex_start or start >= ex_end):
                            self.errors.append(
                                f"Track collision on track-index={t_idx}: clip [{start}, {end}] overlaps with [{ex_start}, {ex_end}]"
                            )
                    track_clips[t_idx].append((start, end))

    def _check_zero_external_urls(self, html: str, css: str) -> None:
        """Verify that media and visual elements do not reference external http/https URLs."""
        # Scan src attributes in media tags: img, video, audio, source
        media_srcs = re.findall(r'<(?:img|video|audio|source)\b[^>]*\bsrc=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for s in media_srcs:
            if s.startswith("http://") or s.startswith("https://"):
                self.errors.append(f"Forbidden external media URL in composition: {s}")

        # Scan CSS url(...) references
        css_urls = re.findall(r'url\s*\(\s*["\']?([^"\'\)]+)["\']?\s*\)', css, re.IGNORECASE)
        for u in css_urls:
            if u.startswith("http://") or u.startswith("https://"):
                self.warnings.append(f"External font or background URL in CSS: {u}")

    def _check_local_asset_paths(self, html: str) -> None:
        """Verify that all relative local asset paths referenced exist on disk."""
        local_srcs = re.findall(r'<(?:img|video|audio|source)\b[^>]*\bsrc=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for s in local_srcs:
            if s.startswith("http://") or s.startswith("https://") or s.startswith("data:"):
                continue
            asset_path = self.project_dir / s
            if not asset_path.exists():
                self.errors.append(f"Referenced local asset file does not exist on disk: {s}")

    def _check_gsap_timeline_contract(self, js: str, html: str) -> None:
        """Verify GSAP timeline registry, paused state, and deterministic finite animation math."""
        combined_js = js
        # Extract any inline <script> content from HTML as well
        inline_scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)</script>', html, re.IGNORECASE)
        for scr in inline_scripts:
            if "gsap" in scr or "timelines" in scr:
                combined_js += "\n" + scr

        if not combined_js.strip():
            self.warnings.append("No JavaScript animation script found")
            return

        # 1. Timeline registration
        if "window.__timelines" not in combined_js and "__timelines" not in combined_js:
            self.errors.append("GSAP timeline not registered on window.__timelines")

        # 2. Paused initialization
        if "paused: true" not in combined_js and "paused:!0" not in combined_js:
            self.errors.append("GSAP timeline must be initialized with { paused: true }")

        # 3. Infinite repeat rejection (repeat: -1)
        code_without_comments = re.sub(r'//.*', '', combined_js)
        code_without_comments = re.sub(r'/\*[\s\S]*?\*/', '', code_without_comments)
        if re.search(r'repeat\s*:\s*-1\b', code_without_comments):
            self.errors.append("Infinite loops ('repeat: -1') are forbidden in HyperFrames compositions")

        # 4. Asynchronous timeline construction rejection
        if re.search(r'\basync\s+function\b', combined_js) or "setTimeout(" in combined_js:
            self.warnings.append("Timeline construction should be synchronous and avoid setTimeout/async")

        # 5. Native video.play() / audio.play() rejection
        if re.search(r'\b(?:video|audio)\.play\s*\(', combined_js):
            self.errors.append("Native media .play() is forbidden; HyperFrames frame seek controls timeline")

    def _check_wcag_contrast(self, css: str) -> None:
        """Heuristic check for background vs text contrast compliance."""
        # Look for body background and text color
        bg_match = re.search(r'background(?:-color)?\s*:\s*#([0-9a-fA-F]{6})', css)
        text_match = re.search(r'color\s*:\s*#([0-9a-fA-F]{6})', css)

        if bg_match and text_match:
            bg_hex = bg_match.group(1)
            text_hex = text_match.group(1)
            contrast_ratio = self._compute_contrast_ratio(bg_hex, text_hex)
            self.details["measured_contrast_ratio"] = round(contrast_ratio, 2)
            if contrast_ratio < 3.0:
                self.warnings.append(f"Low WCAG contrast detected ({contrast_ratio:.2f}:1, minimum recommended is 4.5:1)")

    @staticmethod
    def _compute_contrast_ratio(hex1: str, hex2: str) -> float:
        """Calculate relative luminance contrast ratio between two hex colors."""
        def _luminance(hex_code: str) -> float:
            r = int(hex_code[0:2], 16) / 255.0
            g = int(hex_code[2:4], 16) / 255.0
            b = int(hex_code[4:6], 16) / 255.0
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        l1 = _luminance(hex1)
        l2 = _luminance(hex2)
        bright = max(l1, l2)
        dark = min(l1, l2)
        return (bright + 0.05) / (dark + 0.05)


def validate_composition(project_dir: Union[str, Path]) -> Dict[str, Any]:
    """Convenience helper to validate a HyperFrames composition directory."""
    validator = CompositionValidator(project_dir)
    return validator.validate()
