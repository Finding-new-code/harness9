## 2026-08-31T05:20:49Z
You are the Worker for Milestone 2: Asset Discovery, Rights Ledger & Local Freezing (R2).
Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m2_assets_0
Project root: g:\Finding-new-code\harness9
Original request: g:\Finding-new-code\harness9\ORIGINAL_REQUEST.md
Project architecture & specs: g:\Finding-new-code\harness9\PROJECT.md
Explorer Research & Asset Report: g:\Finding-new-code\harness9\.agents\explorer_research_assets_0\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your exclusive write ownership: `src/assets/`, `tests/test_assets.py`

Your tasks:
1. Implement `src/assets/discovery.py`:
   - Wikimedia Commons MediaWiki Action API adapter with `ExtMetadata` extraction (LicenseShortName, Artist, Credit, URL).
   - Pexels API adapter (with API key header support, photographer attribution, and Pexels License mapping).
   - NASA Image & Video Library adapter.
   - Robust offline mock discovery that generates domain-matched assets for benchmark and procedural topics.
2. Implement `src/assets/freezer.py`:
   - Streaming downloader with size limits (max 25MB), connection timeouts, and retry logic.
   - Binary magic-byte sniffing (JPEG `FF D8 FF`, PNG `89 50 4E 47`, WebP `RIFF...WEBP`, SVG `<svg`, MP4 `ftyp`).
   - SHA-256 checksum calculation and validation.
   - Local directory freezing (`assets/images/{slug}.{ext}`).
   - Relative path composition auditor (asserts zero `http://` / `https://` URLs in HTML compositions, verifies local file presence).
3. Implement `src/assets/ledger.py`:
   - `AssetLedgerManager`: builds, updates, and serializes `AssetProvenanceLedger` to `asset_ledger.json` and `asset_ledger.yaml`.
   - Tracks `asset_id`, `claim_id_refs`, `scene_target`, `media_type`, `local_path`, `file_size_bytes`, `file_sha256`, `dimensions`, `source_provider`, `source_url`, `creator`, `license` (license_type, attribution_text, commercial_use_allowed), `verification_status`.
4. Implement `src/assets/procedural.py`:
   - Dynamic procedural SVG generator creating beautiful, scalable 1920x1080 SVG graphics tailored to topics (circuits/semiconductors, computing, aerospace, science, general abstract tech).
   - Generates typographic quote cards, data metric badges, and hero visuals for offline mode.
5. Implement `src/assets/pipeline.py`:
   - Main `AssetPipeline` class with `discover_and_freeze_assets(dossier: ResearchDossier, output_dir: Path, offline: bool = False) -> AssetProvenanceLedger`.
6. Implement comprehensive tests in `tests/test_assets.py` and run them (`python -m unittest tests/test_assets.py -v`) to verify 100% passing.

Write report to: g:\Finding-new-code\harness9\.agents\worker_m2_assets_0\report.md
And handoff to: g:\Finding-new-code\harness9\.agents\worker_m2_assets_0\handoff.md

Send message to parent when finished.
