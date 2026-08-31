# Harness 9 — Provenance & Rights Ledger Protocol

## 1. Provenance Philosophy

Content created for commercial distribution, social platforms, and broadcast requires strict copyright compliance. Harness 9 enforces an automated **Rights & Provenance Ledger** across every media file ingested, downloaded, or procedurally generated.

Unverified media is never permitted into the final composition.

---

## 2. Asset Discovery & Acquisition Hierarchy

Media assets are acquired according to the following strict hierarchy:

```
1. Creator / Brand Owned Local Assets
2. Explicitly Licensed Open Media (Wikimedia Commons with verified license)
3. Pexels API (with API attribution metadata)
4. Procedural High-Fidelity SVG Vector Assets (Zero-network / 100% safe)
5. AI Generated Imagery (fal / model providers with provenance metadata)
```

Arbitrary web scrapers or unauthorized media sources are strictly disallowed.

---

## 3. Asset Ledger Schema

Every production outputs `asset_ledger.json` and `asset_ledger.yaml` conforming to the typed schema:

```json
{
  "project_id": "transistor_history_001",
  "generated_at": "2026-08-31T10:15:00Z",
  "total_assets": 4,
  "assets": [
    {
      "asset_id": "asset_001",
      "filename": "asset_001.png",
      "local_path": "assets/images/asset_001.png",
      "provider": "wikimedia_commons",
      "source_url": "https://commons.wikimedia.org/wiki/File:Point_contact_transistor.jpg",
      "author": "Bell Labs / Public Domain",
      "license": "CC0-1.0",
      "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
      "allowed_commercial_use": true,
      "requires_attribution": false,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "mime_type": "image/png",
      "byte_size": 248912,
      "used_in_scenes": ["scene_01", "scene_02"]
    },
    {
      "asset_id": "asset_002",
      "filename": "asset_002.svg",
      "local_path": "assets/images/asset_002.svg",
      "provider": "procedural_generator",
      "source_url": "internal://procedural/svg",
      "author": "Harness 9 Engine",
      "license": "MIT",
      "license_url": "https://opensource.org/licenses/MIT",
      "allowed_commercial_use": true,
      "requires_attribution": false,
      "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
      "mime_type": "image/svg+xml",
      "byte_size": 4096,
      "used_in_scenes": ["scene_03"]
    }
  ],
  "credits_summary": "1. Point contact transistor — Bell Labs (Public Domain, CC0)\n2. Vector graphics generated via Harness 9 Engine (MIT)"
}
```

---

## 4. Local Freezing & Integrity Validation

To avoid dependency on live network URLs during rendering:

1. **Streaming Download**: Files are fetched via `httpx` with timeout limits and response size guards.
2. **Magic-Byte Sniffing**: Header bytes are verified (`PNG: \x89PNG`, `JPEG: \xFF\xD8\xFF`, `GIF: GIF8`, `SVG: <svg`) to prevent malformed or spoofed payload injection.
3. **SHA-256 Checksums**: A cryptographic digest is computed and recorded upon download.
4. **Local Freezing**: Assets are saved directly to `assets/images/` and referenced exclusively by relative local paths.
5. **Credit Package**: A formatted credit package is automatically synthesized for video descriptions or end-card credits.
