---
name: h9-production
description: "End-to-end studio production orchestrator: scriptwriting, voice direction, multi-tier asset deduplication, and voice QA."
version: 1.0.0
author: Harness 9, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Production, Audio, TTS, MediaAssets, Pipeline, H9]
    related_skills: [h9-content-planning, h9-hyperframes]
prerequisites:
  commands: [python, ffmpeg]
---

# H9 Studio Production Orchestrator Skill

Master production controller for the Harness 9 studio pipeline.
Drives the 17-state autonomous production lifecycle, handles multi-provider TTS
voice synthesis with acoustic QA verification, executes multi-tier visual asset
discovery and deduplication, and freezes verified assets into the project workspace.

---

## When to Use

- Orchestrating the end-to-end production lifecycle from script to voice and media.
- Discovering, generating, and cryptographically freezing visual media assets.
- Directing speech synthesis across voice profiles and auditing acoustic quality via Voice QA.
- Assembling master audio tracks and aligning vocal cadence beats to visual scenes.

## When NOT to Use

- Research investigation and claim verification (use `h9-research`).
- Story angle brainstorming and scorecard evaluation (use `h9-content-planning`).
- Compiling HTML/CSS compositions and executing headless render (use `h9-hyperframes`).

---

## Quick Reference

- **Invocation Tools**:
  - `h9.discover_assets(requirements: list, scene_ids: list = None, format_aspect: str = "16:9", offline: bool = True)`
  - Direct pipeline execution via `HermesCapabilityBridge.run_full_production(brief)`
- **Acoustic Bounds**:
  - Target speech cadence: 140–160 WPM (clamped strictly between 90 and 220 WPM).
  - Voice QA ceilings: Max silence gap $\le 1.2\text{s}$, True Peak $\le -1.0\text{ dBFS}$.
- **Asset Deduplication Tiers**:
  - Tier 1: Exact byte match via SHA-256 digest.
  - Tier 2: Perceptual visual match via difference hash (`dHash`).
  - Tier 3: Semantic topic and claim tag matching.

---

## Studio Production Workflow

### 1. 17-State Lifecycle Machine
The production orchestrator executes deterministically across 17 formal states:
`CREATED` $\to$ `RESEARCH_PLANNED` $\to$ `RESEARCH_IN_PROGRESS` $\to$ `RESEARCH_COMPLETED` $\to$
`EDITORIAL_ANALYSIS` $\to$ `ANGLE_SELECTED` $\to$ `OUTLINE_APPROVED` $\to$ `SCRIPTING_IN_PROGRESS` $\to$
`SCRIPT_COMPLETED` $\to$ `VOICE_GENERATED` $\to$ `VOICE_QA_PASSED` $\to$ `ASSETS_DISCOVERED` $\to$
`ASSETS_FROZEN` $\to$ `COMPOSITION_GENERATED` $\to$ `RENDER_IN_PROGRESS` $\to$ `RENDER_COMPLETED` $\to$
`COMPLETED` (or `FAILED`).

### 2. Multi-Tier Media Asset Discovery & Freezing
1. Parse visual requirements from script scenes (`scene.visual_asset_path`, `hero_frame_description`).
2. Search asset repositories or invoke the offline procedural vector generator (`ProceduralSVGGenerator`).
3. Compute cryptographic SHA-256 checksum and 64-bit perceptual `dHash` for every asset.
4. Filter duplicates using the deduplication ledger to ensure zero redundant files.
5. Save verified assets into `assets/images/` and record provenance in `AssetRecord` schemas.

### 3. Voice Direction & Automated 4-Gate Voice QA
1. Synthesize narration audio for each scene using configured voice profiles and cadence controls.
2. Concatenate into `assets/audio/narration.wav`.
3. Run the automated 4-Gate Voice QA audit:
   - **Gate 1: Silence & Dead Air**: Scan for unscripted pauses exceeding 1.2s.
   - **Gate 2: Amplitude Normalization & Clipping**: Ensure audio does not exceed -1.0 dBFS true peak.
   - **Gate 3: RMS Consistency**: Verify volume delta between adjacent scenes remains within $\pm 2.5\text{ dB}$.
   - **Gate 4: Speech Beat Alignment**: Verify speech beat timestamps match actual audio acoustic energy.
4. Record metrics in `EvaluationReport` and proceed only when QA passes.

---

## Output Schemas: `AssetRecord`

```json
{
  "asset_id": "asset_scene_01",
  "local_path": "assets/images/asset_scene_01.svg",
  "file_size_bytes": 14280,
  "file_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "perceptual_hash": "d4e8b2a1c7f0e932",
  "media_type": "image/svg+xml",
  "dimensions": {
    "width": 1920,
    "height": 1080,
    "aspect_ratio": "16:9"
  },
  "source_provider": "procedural_vector_generator",
  "license": {
    "license_type": "CC0-1.0 (Public Domain)",
    "commercial_use_allowed": true
  },
  "verification_status": "VERIFIED",
  "scene_target": "scene_01"
}
```
