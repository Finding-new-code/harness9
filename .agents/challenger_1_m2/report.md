# Adversarial Challenge Report: Milestone 2 Asset Pipeline (M2 - R2)

**Author:** Challenger 1 (`challenger_1_m2`)  
**Target:** Milestone 2 (Asset Discovery, Rights Ledger & Local Freezing - R2)  
**Date:** 2026-08-31  
**Verdict:** **REQUEST_CHANGES** (1 Critical Defect in Procedural SVG XML generation, 1 Minor Magic Byte Sniffing Observation)

---

## Challenge Summary

**Overall risk assessment:** **HIGH** (Downstream renderer / XML parser breakage under offline mode or fallback scenarios)

The Milestone 2 Asset Pipeline (`src/assets/`) implements a solid foundation across multi-provider discovery (`WikimediaProvider`, `PexelsProvider`, `NASAProvider`, `OfflineMockProvider`), streaming downloads with size caps and exponential backoff, SHA-256 tamper verification, and composition security auditing.

However, adversarial stress testing revealed a **critical XML well-formedness defect** in `ProceduralSVGGenerator.generate_topic_svg()` (`src/assets/procedural.py`). Because theme badge tags contain raw unescaped ampersands (`&`), **100% of procedural topic SVGs produced during offline runs or fallback downloads are invalid XML**. When consumed by downstream XML parsers, SVG renderers, or browser engines, they throw syntax parse errors (`xml.etree.ElementTree.ParseError: not well-formed (invalid token)`).

---

## Challenges

### [CRITICAL] Challenge 1: Unescaped XML Ampersand in `ProceduralSVGGenerator.generate_topic_svg()`

- **Assumption challenged:** "Procedural SVG generator creates valid, broadcast-grade vector assets ready for offline rendering."
- **Attack scenario / Root cause:**
  In `src/assets/procedural.py`, all 5 built-in theme presets in `THEMES` contain an ampersand (`&`) in their `tag` string:
  - `"circuits"`: `"tag": "SEMICONDUCTOR & SOLID-STATE"`
  - `"computing"`: `"tag": "PARALLEL COMPUTING & ARCHITECTURE"`
  - `"aerospace"`: `"tag": "AEROSPACE & TELEMETRY"`
  - `"science"`: `"tag": "QUANTUM PHYSICS & EXPLORATION"`
  - `"general"`: `"tag": "TECHNOLOGY & INNOVATION"`
  
  In `generate_topic_svg()`, line 106:
  ```python
  tag = palette["tag"]
  ```
  And in the SVG template (line 171):
  ```python
  <text x="{int(38 * scale)}" y="{int(42 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{tag_font_size}" font-weight="700" fill="{palette['primary']}" letter-spacing="1">{tag}</text>
  ```
  `tag` is interpolated directly into the SVG string **without XML entity escaping** (`html.escape(tag)`).
- **Blast radius:**
  1. Every call to `ProceduralSVGGenerator.generate_topic_svg()` across any theme produces malformed XML.
  2. In offline mode (`--offline`), all generated assets written to `assets/images/` are corrupt XML files.
  3. In online mode when a download fails (e.g. 404, DNS error, timeout), the fallback asset written to `assets/images/` is corrupt XML.
  4. Downstream consumers (e.g. M4 HyperFrames renderer, Playwright, Chromium, FFmpeg rasterizer, lxml, ElementTree) will fail or throw XML parse errors on these asset files.
- **Empirical Reproduction:**
  ```python
  import xml.etree.ElementTree as ET
  from src.assets.procedural import ProceduralSVGGenerator
  gen = ProceduralSVGGenerator()
  svg = gen.generate_topic_svg("The History of the Transistor", "1947")
  ET.fromstring(svg)
  # Raises: xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 43, column 155
  ```
- **Recommended Mitigation:**
  Pass `tag` through `html.escape(palette["tag"])` or escape ampersands as `&amp;` in all theme tags or in `generate_topic_svg()`.

---

### [LOW] Challenge 2: HTML Documents with `<svg>` Elements Sniffed as `image/svg+xml`

- **Assumption challenged:** "Magic byte sniffing accurately isolates SVG image vectors from HTML documents."
- **Attack scenario:**
  In `src/assets/freezer.py` lines 61-64:
  ```python
  # SVG / XML vector
  header_lower = header[:1024].lower()
  if b"<svg" in header_lower or (b"<?xml" in header_lower and b"<svg" in header_lower):
      return "image/svg+xml"
  ```
  If a web server returns an HTML error page or webpage containing an inline `<svg>` in the first 1024 bytes (e.g. `<!DOCTYPE html><html><body><svg width="10">...`), `sniff_magic_bytes` classifies the HTML document as `image/svg+xml` and saves it with `.svg` extension.
- **Blast radius:** Non-image HTML payload stored as an SVG asset if remote endpoint returns 200 with HTML instead of image.
- **Recommended Mitigation:** Ensure `header_lower.strip().startswith(b"<svg")` or `b"<?xml" in header_lower and not b"<!doctype html" in header_lower`.

---

## Stress Test Results

Executed test harness in `tests/test_adversarial_assets.py` (23 adversarial test cases):

| # | Test Scenario | Expected Behavior | Actual Behavior | Result |
|---|---------------|-------------------|-----------------|--------|
| 1 | Magic bytes: Fake extension mismatch (.png with JPG, .jpg with PNG, .svg with JPG, .mp4 with MP3) | Detect true binary MIME type | Identified true MIME correctly | **PASS** |
| 2 | Magic bytes: Micro & truncated headers (0 to 11 bytes) | Return octet-stream without IndexError | Returned octet-stream cleanly | **PASS** |
| 3 | Magic bytes: Executable & malware binary headers (PE MZ, Linux ELF, bash script, random noise) | Reject as octet-stream | Returned octet-stream | **PASS** |
| 4 | Magic bytes: Embedded SVG with XML declaration, leading whitespace, comments | Return image/svg+xml | Returned image/svg+xml | **PASS** |
| 5 | Freezing: Automatic extension resolution from sniffed MIME | Save with `.png` when ext is None | Resolved `.png` extension | **PASS** |
| 6 | Network: Socket connection timeout with retries | Retry 3 times with backoff, raise AssetDownloadError | Retried with 0.5s/1.0s backoff, raised AssetDownloadError | **PASS** |
| 7 | Network: DNS failure recovery | Catch gaierror, generate fallback procedural SVG | Created valid fallback asset on disk | **PASS** |
| 8 | Network: HTTP error matrix (400, 403, 404, 429, 500, 502, 503) | Raise without fallback, fallback when provided | Handled all HTTP codes cleanly | **PASS** |
| 9 | Network: Mid-stream connection drop | Catch ConnectionResetError, retry, raise AssetDownloadError | Retried and raised AssetDownloadError | **PASS** |
| 10 | Network: Offline mode zero-network guarantee | Zero network requests made when `offline=True` | Completed with 0 network calls | **PASS** |
| 11 | Composition Audit: Reject external `<img src="http://...">` & `https://` | Fail validation, raise ValueError in assert_zero_external_urls | Flagged external URLs, raised ValueError | **PASS** |
| 12 | Composition Audit: Reject external `<video>`, `<audio>`, `<source>` | Fail validation, flag external media streams | Flagged all 3 media tags | **PASS** |
| 13 | Composition Audit: Reject broken local paths & 0-byte files | Detect missing disk files and 0-byte corrupt files | Reported broken and empty files | **PASS** |
| 14 | Composition Audit: Allow CDN scripts with warning | Allow cdnjs GSAP / Google Fonts scripts | Allowed with warnings, zero errors | **PASS** |
| 15 | Procedural SVG: Card types XML validity (Quote, Metric, Hero) | Produce valid XML for all card types | All cards parsed cleanly with ElementTree | **PASS** |
| 16 | Procedural SVG: 5 Themes XML validity | Produce valid XML for all 5 themes | **FAILED: unescaped ampersand `&` in theme `tag`** | **FAIL** |
| 17 | Procedural SVG: Multi-resolution & aspect ratios (16:9, 9:16, 1:1, 4K, 21:9) | Produce valid XML across all aspect ratios | **FAILED: unescaped ampersand `&` in theme `tag`** | **FAIL** |
| 18 | Procedural SVG: XML injection & XSS safety (`<script>`, quotes, CDATA) | Sanitize/escape injection strings into valid XML | **FAILED: unescaped ampersand `&` in theme `tag`** | **FAIL** |
| 19 | Procedural SVG: Unicode & non-ASCII characters | Render unicode and math symbols cleanly | **FAILED: unescaped ampersand `&` in theme `tag`** | **FAIL** |
| 20 | Ledger Integrity: On-disk file tampering | Detect byte alteration via SHA-256 mismatch | Flagged SHA-256 mismatch | **PASS** |
| 21 | Ledger Integrity: Corrupt JSON / YAML loading | Raise FileNotFoundError and JSON/YAML decode errors | Raised appropriate exceptions | **PASS** |
| 22 | Ledger Integrity: Schema completeness check | Detect missing creator name or missing license | Reported schema validation errors | **PASS** |
| 23 | Security Boundary: Path traversal filename sanitization | Strip `../`, `..\`, absolute paths, Windows device names | Sanitized to safe local filenames | **PASS** |

---

## Unchallenged Areas

- **Heavy Remote Bandwidth / Network Throttling**: Live rate limiting of Wikimedia/NASA endpoints in production networks was tested via mocked socket/HTTP errors rather than live gigabit network stress.
- **GPU Texture Compression**: Procedural SVGs are vector XML representations; GPU raster caching is handled downstream in M4.

---

## Required Fix for Approval

To resolve this defect, apply `html.escape()` to `tag` in `ProceduralSVGGenerator.generate_topic_svg()` (`src/assets/procedural.py`):
```python
tag = html.escape(palette["tag"])
```
Once fixed, all 23 adversarial tests and acceptance checks will achieve a 100% pass rate.
