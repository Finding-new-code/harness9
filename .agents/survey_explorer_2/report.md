# Harness 9 to Hermes Native Integration: Architectural Survey & Design Report

**Subagent:** `survey_explorer_2` (teamwork_preview_explorer)  
**Date:** 2026-09-04  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\survey_explorer_2`  
**Status:** Canonical Engineering Design Report  
**Target Scope:** Requirements R2 (Native Tools & Bridge), R3 (Native Skills & Production IR Seam), R4 (Providers, Memory & Subagent Delegation)

---

## Executive Summary

This investigation surveys the Harness 9 autonomous content production codebase and defines the comprehensive architecture for refactoring its capabilities to execute directly through the Hermes Agent runtime. Rather than operating as an isolated external pipeline wrapped by a thin adapter, Harness 9's domain engines (Research, Editorial, Scriptwriting, Asset Discovery, and HyperFrames) are refactored into:

1. **Four Native Hermes Model Tools** (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`), registered within a named Hermes toolset (`h9_content`), conforming strictly to the Hermes Footprint Ladder, prompt caching invariants, and OpenAI function calling standards.
2. **A Capability Bridge** (`src/h9_runtime/bridge.py`) providing clean, bidirectional abstraction so H9 domain engines can request Hermes services (model inference, memory access, subagent delegation, sandboxed execution) without tight coupling to internal Hermes implementations.
3. **Four Native Hermes Skills** (`skills/h9-research/`, `skills/h9-content-planning/`, `skills/h9-production/`, `skills/h9-hyperframes/`), packaging domain workflows with standard YAML frontmatter, operational procedures, and helper scripts.
4. **A Strongly Typed Production Intermediate Representation (IR) Seam**, serving as an explicit Abstract Syntax Tree (AST) between high-level narrative planning/scriptwriting and low-level HyperFrames HTML/CSS/GSAP compilation, enforcing temporal conservation, asset binding integrity, and acoustic synchronization.
5. **A Role-Based Provider, Memory, and Subagent Architecture**, routing model calls by logical roles (`researcher`, `writer`, `critic`, `planner`), unifying creator and project memory with Hermes `USER.md` and `SessionDB`, and isolating high-token research synthesis inside a dedicated Hermes subagent.

---

## 1. Mapping Current H9 Execution Paths

An in-depth audit of the existing Harness 9 codebase reveals four foundational execution paths. Each path has been analyzed down to file paths, class definitions, and control flow.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Harness 9 Production Flow                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 1. RESEARCH & FACT VERIFICATION                                                 │
│    src/research/engine.py: ResearchEngine.synthesize_research()                 │
│    ├── Keyword / Preset Matching (presets/*.yaml)                               │
│    ├── 5 Intent Query Expansion (_generate_queries)                             │
│    ├── MultiProviderDispatcher (Tavily, Exa, procedural fallback)               │
│    └── Claim Extraction & Scoring (scoring.py: score_claim) -> ResearchDossier   │
│                                                                                 │
│ 2. ASSET DISCOVERY & DEDUPLICATION                                              │
│    src/assets/pipeline.py: AssetPipeline.discover_and_freeze_assets()           │
│    ├── MediaDiscoveryAdapter (Wikimedia, NASA, Pexels, procedural SVG)          │
│    ├── AssetFreezer (Local staging)                                             │
│    └── AssetDeduplicator (Tier 1 SHA-256 + Tier 2 64-bit dHash Hamming <= 4)   │
│                                                                                 │
│ 3. SCRIPT GENERATION & VOICE DIRECTION                                          │
│    src/editorial/ & src/scriptwriting/                                          │
│    ├── EditorialEngine: 5 Archetype Angles -> 9-Dimension Scorecard -> Winner   │
│    ├── NarrativePlanner: 4-Act ContentOutline                                   │
│    ├── ScriptGenerator: Script with ScriptScenes, ScriptBeats & Markdown docs   │
│    ├── VoiceDirector: Multi-provider TTS (ElevenLabs, OpenAI, SAPI, Harmonic)   │
│    │   + Emotion Tags + WPM Clamping (90-220 WPM) -> narration.wav             │
│    └── VoiceQA: 4 Gates (Dead Air, Clipping, Volume, Beat Alignment)            │
│                                                                                 │
│ 4. HYPERFRAMES COMPOSITION & RENDERING                                          │
│    src/hyperframes/ & adapters/hyperframes/                                     │
│    ├── ComponentRegistry: 7 Parameterized Visual Blocks                         │
│    ├── HyperFramesGenerator: index.html, styles.css, main.js (GSAP 3.12.5)      │
│    ├── CompositionValidator: Zero remote URLs, finite loops, asset integrity    │
│    └── HyperFramesRenderer: Playwright / Chromium headless + FFmpeg pipe       │
│        -> final.mp4 RenderArtifact                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Research & Fact Verification Path
- **Primary Modules**: `src/research/engine.py`, `src/research/providers.py`, `src/research/scoring.py`, `src/models/contracts.py` (`ResearchDossier`, `ClaimRecord`, `SourceRecord`).
- **Entry Method**: `ResearchEngine.synthesize_research(topic: str, offline: bool, target_duration: int) -> ResearchDossier`.
- **Execution Flow**:
  1. **Topic Normalization & Preset Matching**: Examines `presets_dir` (`src/research/presets/*.yaml`) against keywords (`transistor_history.yaml`, `how_gpus_work.yaml`, `apollo_computer.yaml`, `quantum_computing.yaml`). If matched, loads YAML, generates a fresh `run_id`, updates timestamps, and scales talking points proportionally to `target_duration`.
  2. **Intent Query Expansion**: `_generate_queries(topic)` outputs 5 orthogonal query categories:
     - `origin_history`: Historical genesis and early discoveries.
     - `technical_mechanism`: Physical and engineering principles.
     - `quantitative_metric`: Concrete metrics, benchmarks, and data.
     - `modern_impact`: Societal, commercial, and future relevance.
     - `visual_queries`: Visual cues and photographic descriptors.
  3. **Multi-Provider Search**: When `offline=False`, `MultiProviderDispatcher.search()` queries Tavily and Exa APIs. If `offline=True` or API calls fail, falls back to `_synthesize_procedural()`.
  4. **Claim Extraction & Reliability Scoring**: `score_claim(claim, source)` evaluates source domain TLD, author attribution, citation count, and specificity, assigning a confidence score (0.0 to 1.0). Claims below threshold (0.6) are rejected.
  5. **Dossier Serialization**: Emits `ResearchDossier` containing headline, executive summary, 5–8 verified `ClaimRecord`s, 4–6 `TalkingPointRecord`s, `StatisticRecord`s, and suggested visual search queries. Atomically writes to `research_dossier.json` and `research_dossier.yaml`.

### 1.2 Asset Discovery & Deduplication Path
- **Primary Modules**: `src/assets/pipeline.py`, `src/assets/discovery.py`, `src/assets/freezer.py`, `src/assets/deduplication.py`, `src/assets/procedural.py`, `src/models/ledger.py`.
- **Entry Method**: `AssetPipeline.discover_and_freeze_assets(dossier, output_dir, offline, format_aspect) -> AssetProvenanceLedger`.
- **Execution Flow**:
  1. **Query Formulation**: Derives visual asset requirements from `dossier.suggested_visual_queries` and individual `ClaimRecord.visual_cue_suggestion`.
  2. **Candidate Search**: `MediaDiscoveryAdapter` searches Wikimedia Commons API, NASA Image Library, and Pexels API, extracting media URLs, dimensions, creator information, and license metadata (`CC0`, `CC-BY`, `Public Domain`).
  3. **Offline Procedural Synthesis**: In offline mode or when queries yield insufficient candidates, `ProceduralAssetGenerator` creates deterministic SVGs (flowcharts, architecture blocks, waveform plots, comparison graphs) rendered to disk.
  4. **Two-Tier Deduplication**: `AssetDeduplicator.register_asset(file_path)`:
     - **Tier 1 (Byte-Exact SHA-256)**: Hashes byte stream (`compute_file_sha256`). If SHA-256 matches an existing asset, the file download is discarded and the existing record is reused.
     - **Tier 2 (Perceptual 64-bit dHash)**: Computes difference gradient hash by resizing images to 9x8 grayscale, comparing adjacent pixels:
       $$\text{bit}_{x,y} = 1 \text{ if } P(x, y) > P(x+1, y) \text{ else } 0$$
       Calculates bitwise Hamming distance:
       $$d_H(H_1, H_2) = \text{popcount}(H_1 \oplus H_2)$$
       If $d_H \le 4$ (`DEFAULT_HAMMING_THRESHOLD`), the image is flagged as a perceptual near-duplicate and deduplicated.
  5. **Ledger Freezing**: Approved assets are moved to `assets/images/`, cataloged in `AssetProvenanceLedger` (`asset_ledger.json` / `asset_ledger.yaml`), complete with license terms, attribution requirements, and scene targets.

### 1.3 Script Generation, Voice Direction & Voice QA Path
- **Primary Modules**: `src/editorial/`, `src/scriptwriting/`, `src/models/contracts.py`.
- **Entry Methods**: `EditorialEngine.process_editorial()`, `ScriptwritingPipeline.run()`, `VoiceDirector.synthesize_narration()`, `VoiceQA.analyze_audio()`.
- **Execution Flow**:
  1. **Multi-Angle Generation**: `AngleGenerator` produces 5 candidate angles across archetypes: `contrarian`, `deep_dive`, `data_led`, `human_centric`, and `future_vision`.
  2. **9-Dimension Scorecard Evaluation**: `EditorialScorer` scores each candidate across:
     - Audience Relevance (0.15), Novelty (0.15), Hook Potential (0.15)
     - Narrative Potential (0.10), Creator Fit (0.10), Evidence Availability (0.10)
     - Visual Potential (0.10), Platform Fit (0.10), Saturation Risk (0.05)
  3. **Deterministic Selection & Hook Ideation**: `AngleSelector` picks the winning angle using composite scoring and tie-breaking. `HookGenerator` crafts psychological hooks across cognitive triggers.
  4. **4-Act Narrative Planning**: `NarrativePlanner` designs `ContentOutline` spanning Act 1 (Hook/Setup), Act 2 (Mechanism/Context), Act 3 (Climax/Impact), and Act 4 (Takeaway/Resolution).
  5. **Script & Beat Breakdown**: `ScriptGenerator` generates `BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`, and structured `Script` with timestamped `ScriptScene`s and `ScriptBeat`s.
  6. **Voice Direction & Acoustic Synthesis**:
     - `VoiceDirector` routes synthesis through ElevenLabs v2, OpenAI Audio (`tts-1`), Windows SAPI (`System.Speech`), or pure-Python `HarmonicWAVSynthesizer`.
     - Parses emotional tags (`[tense]`, `[authoritative]`, `[curious]`, `[triumphant]`), adjusting pitch multiplier, rate multiplier, and volume.
     - Clamps delivery speed via `clamp_wpm(wpm, min_wpm=90, max_wpm=220, default=145)`.
     - Emits `assets/audio/narration.wav`.
  7. **Voice QA Validation**: `VoiceQA.analyze_audio()` runs 4 acoustic quality gates:
     - Dead air duration (< 1.5s max threshold)
     - Clipping detection (samples exceeding digital ceiling)
     - Loudness consistency (RMS variance)
     - Speech-to-beat synchronization (drift < 250ms)
     Outputs `VoiceQAReport` converting to `EvaluationReport`.

### 1.4 HyperFrames Composition & MP4 Rendering Path
- **Primary Modules**: `src/hyperframes/`, `adapters/hyperframes/`, `src/hyperframes/components/`.
- **Entry Methods**: `HyperFramesAdapter.compile_composition()`, `HyperFramesRenderer.render()`.
- **Execution Flow**:
  1. **Component Registry Mapping**: Inspects `ScriptScene.component_type` against the 7 canonical visual blocks:
     - `reference_collage_hook`: Dynamic multi-image collage with entrance staggering.
     - `split_screen_intro`: Dual-pane comparative or presenter/subject split.
     - `quote_highlight`: Callout quote with animated author badge and typography.
     - `timeline_reveal`: Sequential historical milestone progression.
     - `statistic_reveal`: Key metric counter with contextual footnote.
     - `comparison_panel`: Side-by-side contrast metrics with winner badge.
     - `creator_bottom_collage`: Lower-third branding and creator attribution panel.
  2. **Master Composition Generation**: `HyperFramesGenerator` synthesizes `index.html`, `styles.css`, and `main.js`:
     - Instantiates GSAP 3.12.5 timelines.
     - Synchronizes master timeline to `<audio src="assets/audio/narration.wav">`.
     - Pauses timelines by default for exact deterministic frame scrubbing.
  3. **Static Composition Linter**: `CompositionValidator.validate()` checks:
     - Root element `#hyperframes-stage` existence and correct CSS dimensions.
     - Local asset existence (all images reside in `assets/images/`).
     - Absolute zero external remote URLs (`http://`, `https://`).
     - Finite GSAP loops (disallows `repeat: -1`).
  4. **Headless MP4 Rendering**: `HyperFramesRenderer.render()` launches headless Chromium via Playwright, sets viewport to 1920x1080 (16:9) or 1080x1920 (9:16), seeks GSAP timeline frame-by-frame at 30 FPS (`timeline.time(frame / 30.0)`), and streams raw frames into an FFmpeg subprocess:
     ```bash
     ffmpeg -y -f image2pipe -vcodec png -r 30 -i - -i assets/audio/narration.wav \
            -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest renders/final.mp4
     ```
  5. **Artifact Verification**: Validates non-empty file size, playability, duration, and returns `RenderArtifact`.

---

## 2. Native Tool Conversion Architecture (Requirement R2)

### 2.1 Hermes Tool Registry Strategy & Footprint Ladder Compliance

In compliance with the Hermes Development Guide (`AGENTS.md`), adding capabilities to the core model schema must follow the Footprint Ladder:
- **Core Schema Protection**: H9 capabilities must **never** be added to `_HERMES_CORE_TOOLS` in `toolsets.py`. Adding specialized tools to the core list inflates token count on every API call across all unrelated conversations and breaks prompt caching.
- **Service-Gated Named Toolset**: H9 tools are registered under the named toolset `"h9_content"` in `tools/registry.py`. They are enabled exclusively when:
  1. The user's active Hermes profile or task requests the `h9_content` toolset.
  2. The service gate check function `check_h9_available()` returns `True`.
- **Prompt Cache Stability**: Schemas are 100% static, deterministic, and free of dynamic runtime mutations. Tool handlers strictly return valid JSON strings without mutating system prompts or inserting synthetic turns.
- **Naming & Alias Convention**: Registered as canonical names `h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, with snake_case aliases `h9_research`, `h9_discover_assets`, `h9_generate_script`, `h9_render` registered in `tools/registry.py` to support LLM backends with strict identifier constraints (`^[a-zA-Z0-9_-]+$`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Hermes Tool Registry                            │
├────────────────────────────────────────────────────────────────────────┤
│ _HERMES_CORE_TOOLS: [web_search, read_file, write_file, terminal, ...] │
│                                                                        │
│ Toolset: "h9_content" (Gated via check_h9_available())                 │
│ ├── h9.research        (alias: h9_research)        -> ResearchDossier   │
│ ├── h9.discover_assets (alias: h9_discover_assets) -> AssetRecord list │
│ ├── h9.generate_script (alias: h9_generate_script) -> Script           │
│ └── h9.render          (alias: h9_render)          -> RenderArtifact   │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Tool Specification 1: `h9.research`

- **Canonical Name**: `h9.research`
- **Alias**: `h9_research`
- **Toolset**: `h9_content`
- **Description**: "Execute deep multi-source factual research, claim extraction, and confidence scoring for a content production topic. Returns a verified, structured ResearchDossier."
- **Parameter Schema**:
  ```json
  {
    "type": "object",
    "properties": {
      "topic": {
        "type": "string",
        "description": "The topic, technology, or historical event to research."
      },
      "target_duration": {
        "type": "integer",
        "default": 30,
        "description": "Target video duration in seconds (scales the number of talking points and depth)."
      },
      "offline": {
        "type": "boolean",
        "default": true,
        "description": "Whether to use hermetic offline benchmarks and procedural fallback."
      },
      "intent_categories": {
        "type": "array",
        "items": { "type": "string" },
        "default": ["origin_history", "technical_mechanism", "quantitative_metric", "modern_impact"],
        "description": "Specific intent query categories to investigate."
      },
      "max_claims": {
        "type": "integer",
        "default": 8,
        "description": "Maximum number of verified factual claims to extract."
      }
    },
    "required": ["topic"]
  }
  ```
- **Return Schema**: Serialized `ResearchDossier` dictionary:
  ```json
  {
    "topic": "The History of the Transistor",
    "schema_version": "2.0.0",
    "run_id": "run_9a8b7c6d",
    "generated_at": "2026-09-04T09:00:00Z",
    "headline": "How Three Physicists at Bell Labs Changed the World",
    "executive_summary": "In December 1947, John Bardeen, Walter Brattain, and William Shockley invented the point-contact transistor...",
    "key_takeaways": ["Replaced fragile vacuum tubes", "Enabled microelectronics revolution"],
    "claims": [
      {
        "claim_id": "claim_01",
        "claim_text": "The point-contact transistor was first demonstrated on December 23, 1947.",
        "category": "origin_history",
        "confidence_score": 0.98,
        "primary_source": {
          "title": "Bell Laboratories Historical Archives",
          "url": "https://www.bell-labs.com/about/history/",
          "publisher": "Bell Labs",
          "reliability_score": 0.95
        },
        "corroborating_sources": [],
        "visual_cue_suggestion": "Close-up macro of point-contact germanium transistor replica"
      }
    ],
    "talking_points": [
      {
        "beat_index": 1,
        "title": "The Vacuum Tube Bottleneck",
        "narrative_hook": "Before 1947, computing was held back by glowing glass tubes that burned out daily.",
        "supported_claim_ids": ["claim_01"],
        "estimated_duration_sec": 7.5
      }
    ],
    "statistics": [
      {
        "metric": "Power Reduction",
        "value": "1000x",
        "context": "Compared to contemporary vacuum tubes",
        "source_claim_id": "claim_01"
      }
    ],
    "suggested_visual_queries": [
      "1947 point contact transistor bell labs",
      "john bardeen walter brattain laboratory"
    ]
  }
  ```
- **Invocation Flow**:
  1. Hermes Agent calls `h9.research(topic="...", target_duration=30, offline=True)`.
  2. Handler retrieves active session sandbox via `HermesSessionSandbox(session_id)`.
  3. Dispatches execution to `ResearchEngine` or delegates to subagent if `offline=False`.
  4. Saves output atomically to `workspace/research_dossier.json` and `workspace/research_dossier.yaml`.
  5. Returns structured JSON dictionary to LLM context.

### 2.3 Tool Specification 2: `h9.discover_assets`

- **Canonical Name**: `h9.discover_assets`
- **Alias**: `h9_discover_assets`
- **Toolset**: `h9_content`
- **Description**: "Discover, download, verify licenses, freeze, and deduplicate media assets for a topic or research dossier. Emits verified AssetRecords."
- **Parameter Schema**:
  ```json
  {
    "type": "object",
    "properties": {
      "dossier": {
        "type": "object",
        "description": "The ResearchDossier object containing claims and visual queries."
      },
      "queries": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Explicit list of visual search queries if dossier is omitted."
      },
      "format_aspect": {
        "type": "string",
        "enum": ["16:9", "9:16", "1:1"],
        "default": "16:9",
        "description": "Target video aspect ratio."
      },
      "offline": {
        "type": "boolean",
        "default": true,
        "description": "Whether to use procedural generation rather than live web scraping."
      },
      "max_assets": {
        "type": "integer",
        "default": 6,
        "description": "Maximum number of unique media assets to collect."
      }
    },
    "required": []
  }
  ```
- **Return Schema**: Dictionary containing asset list and ledger summary:
  ```json
  {
    "total_assets": 4,
    "assets": [
      {
        "asset_id": "asset_img_01",
        "local_path": "assets/images/transistor_point_contact.png",
        "file_size_bytes": 142850,
        "file_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "perceptual_hash": "a8c4f2e1d09b33a7",
        "media_type": "image/png",
        "dimensions": { "width": 1920, "height": 1080, "aspect_ratio": "16:9" },
        "source_provider": "wikimedia_commons",
        "source_url": "https://upload.wikimedia.org/example.jpg",
        "license": {
          "license_type": "CC0-1.0 (Public Domain)",
          "attribution_required": false,
          "commercial_use_allowed": true
        },
        "verification_status": "VERIFIED",
        "scene_target": "scene_01"
      }
    ],
    "deduplication_stats": {
      "sha256_duplicates_prevented": 1,
      "perceptual_near_duplicates_filtered": 0
    }
  }
  ```
- **Invocation Flow**:
  1. Agent passes `dossier` or list of `queries`.
  2. Handler queries `MediaDiscoveryAdapter` or `ProceduralAssetGenerator`.
  3. Computes SHA-256 and 64-bit dHash; rejects/reuses duplicates.
  4. Writes validated files into session `assets/images/`.
  5. Updates `asset_ledger.json` and returns asset records.

### 2.4 Tool Specification 3: `h9.generate_script`

- **Canonical Name**: `h9.generate_script`
- **Alias**: `h9_generate_script`
- **Toolset**: `h9_content`
- **Description**: "Generate a broadcast script, 4-act narrative outline, visual storyboard, and acoustic voiceover narration from a ResearchDossier."
- **Parameter Schema**:
  ```json
  {
    "type": "object",
    "properties": {
      "dossier": {
        "type": "object",
        "description": "The ResearchDossier containing claims, talking points, and statistics."
      },
      "angle_archetype": {
        "type": "string",
        "enum": ["contrarian", "deep_dive", "data_led", "human_centric", "future_vision", "auto"],
        "default": "auto",
        "description": "Editorial angle archetype, or 'auto' for 9-dimension scorecard selection."
      },
      "target_duration": {
        "type": "number",
        "default": 30.0,
        "description": "Target script duration in seconds."
      },
      "voice": {
        "type": "string",
        "default": "default",
        "description": "Voice profile or persona for voice direction."
      },
      "format_aspect": {
        "type": "string",
        "enum": ["16:9", "9:16"],
        "default": "16:9",
        "description": "Target aspect ratio."
      },
      "creator_id": {
        "type": "string",
        "description": "Optional Creator DNA identifier to apply brand rules and negative constraints."
      }
    },
    "required": ["dossier"]
  }
  ```
- **Return Schema**: Serialized `Script` contract:
  ```json
  {
    "topic": "The History of the Transistor",
    "title": "The Spark That Built Modern Computing",
    "angle_id": "angle_deep_dive_01",
    "total_duration": 30.0,
    "full_transcript": "Before 1947, all electronics ran on glowing vacuum tubes...",
    "word_count": 72,
    "scenes": [
      {
        "scene_id": "scene_01",
        "title": "The Glass Tube Problem",
        "duration": 7.5,
        "narration_text": "Before 1947, all electronics ran on glowing vacuum tubes.",
        "visual_asset_path": "assets/images/vacuum_tube.png",
        "hero_frame_description": "Hero macro of fragile glowing tube",
        "component_type": "reference_collage_hook",
        "component_props": { "headline": "Fragile Power", "accent_color": "#00d2ff" },
        "entrance_animation": "fade",
        "transition_out": "fade",
        "beats": [
          {
            "beat_id": "beat_01",
            "start_time": 0.0,
            "end_time": 3.8,
            "duration": 3.8,
            "text": "Before 1947, all electronics ran on glowing vacuum tubes.",
            "visual_cue": "Show glowing filaments"
          }
        ]
      }
    ],
    "audio_path": "assets/audio/narration.wav",
    "transcript_path": "assets/transcript.json",
    "artifacts": ["BRIEF.md", "DESIGN.md", "SCRIPT.md", "STORYBOARD.md"]
  }
  ```
- **Invocation Flow**:
  1. Runs `EditorialEngine` to score angles, select winner, and plan 4-act outline.
  2. Generates Markdown documents (`BRIEF.md`, `DESIGN.md`, `SCRIPT.md`, `STORYBOARD.md`).
  3. Synthesizes narration via `VoiceDirector` and validates with `VoiceQA`.
  4. Returns `Script` contract.

### 2.5 Tool Specification 4: `h9.render`

- **Canonical Name**: `h9.render`
- **Alias**: `h9_render`
- **Toolset**: `h9_content`
- **Description**: "Compile visual HyperFrames components, assemble GSAP master composition, run static linting, and render broadcast MP4 video."
- **Parameter Schema**:
  ```json
  {
    "type": "object",
    "properties": {
      "script": {
        "type": "object",
        "description": "The Script contract containing scene descriptions, component types, and props."
      },
      "assets": {
        "type": "array",
        "items": { "type": "object" },
        "description": "List of AssetRecord objects providing media paths and metadata."
      },
      "format_aspect": {
        "type": "string",
        "enum": ["16:9", "9:16"],
        "default": "16:9",
        "description": "Render resolution aspect ratio."
      },
      "fps": {
        "type": "integer",
        "default": 30,
        "description": "Target video frame rate."
      },
      "quality": {
        "type": "string",
        "enum": ["draft", "standard", "broadcast"],
        "default": "standard",
        "description": "Render quality profile."
      }
    },
    "required": ["script"]
  }
  ```
- **Return Schema**: Serialized `RenderArtifact` contract:
  ```json
  {
    "video_path": "renders/final.mp4",
    "duration_seconds": 30.0,
    "file_size_bytes": 12845920,
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "video_codec": "h264",
    "audio_codec": "aac",
    "rendered_at": "2026-09-04T09:02:15Z",
    "validation_status": "VERIFIED"
  }
  ```
- **Invocation Flow**:
  1. Calls `HyperFramesAdapter.compile_composition()` to build HTML/CSS/JS.
  2. Runs `CompositionValidator` to ensure hermetic compliance.
  3. Executes `HyperFramesRenderer` with Playwright and FFmpeg.
  4. Returns validated `RenderArtifact`.

### 2.6 Capability Bridge Architecture (`src/h9_runtime/bridge.py`)

To ensure H9 domain modules never directly import internal, private Hermes Agent classes (`AIAgent`, `HermesCLI`, `SessionDB`), the runtime boundary is encapsulated in `src/h9_runtime/bridge.py`:

```python
"""src/h9_runtime/bridge.py — Hermes Capability Bridge for Harness 9.

Decouples H9 domain modules from internal Hermes agent implementations,
providing standard interfaces for Model Inference, Memory, Subagent Delegation,
and Sandboxed Subprocess Execution.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

class HermesCapabilityBridge:
    """Central gateway for H9 domain services requesting Hermes runtime capabilities."""

    def __init__(self, session_id: str, workspace_root: Optional[Path] = None):
        self.session_id = session_id
        self.workspace_root = workspace_root or Path(f"output/sessions/{session_id}")
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    # 1. Model Inference Gateway (Role-based routing)
    def request_model_completion(
        self,
        role: str,  # "researcher" | "writer" | "critic" | "planner"
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        response_schema: Optional[type[BaseModel]] = None,
    ) -> str:
        """Route model completion through Hermes provider system by capability role."""
        ...

    # 2. Memory Integration Gateway
    def query_creator_memory(self, creator_id: str) -> Dict[str, Any]:
        """Fetch creator brand DNA, preferences, and negative memory from Hermes USER.md."""
        ...

    def record_learning_candidate(self, candidate: Dict[str, Any]) -> None:
        """Persist distilled negative rule or learning into Hermes memory store."""
        ...

    # 3. Subagent Delegation Gateway
    def delegate_subagent_task(
        self,
        goal: str,
        context: Dict[str, Any],
        toolsets: List[str],
        timeout_sec: float = 120.0,
    ) -> Dict[str, Any]:
        """Spawn an isolated Hermes child agent with restricted toolsets and fresh context."""
        ...

    # 4. Sandboxed Execution Gateway
    def run_sandboxed_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        timeout_sec: float = 60.0,
    ) -> Tuple[int, str, str]:
        """Execute subprocess (e.g. FFmpeg) within Hermes sandbox boundaries."""
        ...
```

---

## 3. Native Hermes Skills Architecture (Requirement R3)

### 3.1 Hermes Skill Conventions & Directory Structure

In Hermes Agent, skills live in `skills/<category>/<skill-name>/` or `skills/<skill-name>/`. Each skill directory contains:
- `SKILL.md`: Mandatory entrypoint featuring standard YAML frontmatter, triggering conditions ("When to use"), setup dependencies, procedural operational workflows, and output schema specifications.
- `scripts/`: Python helper scripts invoked either directly by the agent or by human operators.
- `references/`: Detailed specifications, rulebooks, and templates.

We package H9 capabilities into four native skills:
```
skills/
├── h9-research/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── run_research.py
│   └── references/
│       ├── intent_categories.md
│       └── claim_scoring_guide.md
├── h9-content-planning/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── plan_content.py
│   └── references/
│       ├── angle_archetypes.md
│       ├── scorecard_weights.md
│       └── 4_act_narrative_structure.md
├── h9-production/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── run_production_pipeline.py
│   └── references/
│       ├── production_lifecycle.md
│       ├── voice_direction_guide.md
│       └── asset_deduplication_spec.md
└── h9-hyperframes/
    ├── SKILL.md
    ├── scripts/
    │   ├── compile_composition.py
    │   └── validate_composition.py
    └── references/
        ├── component_blocks_catalog.md
        ├── gsap_timing_rules.md
        └── static_linter_rules.md
```

### 3.2 Skill: `skills/h9-research/SKILL.md`

```yaml
---
name: h9-research
description: "Autonomous multi-source research synthesis, claim extraction, and verification for content production."
version: 1.0.0
author: Harness 9, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Content, Research, FactChecking, Verification, H9]
    related_skills: [h9-content-planning, research]
---

# H9 Research & Fact Verification Skill

## When to use
Use when the user requests factual investigation, background research, claim verification, or technical dossier preparation for a video or multimedia topic. Transforms raw concepts into structured, verified `ResearchDossier`s.

## Prerequisites & Dependencies
- Python 3.10+
- `pip install pydantic pyyaml`
- Optional: `TAVILY_API_KEY`, `EXA_API_KEY` for live web queries. Defaults to deterministic offline benchmarks.

## Procedural Workflow
1. **Analyze Topic & Scope**: Extract key entities, target duration, and required depth.
2. **Intent Expansion**: Formulate 5 orthogonal queries (`origin_history`, `technical_mechanism`, `quantitative_metric`, `modern_impact`, `visual_queries`).
3. **Execute Search or Subagent Delegation**:
   - For complex online queries, invoke `delegate_task` with `toolsets=["research", "web"]` to protect parent context.
   - For hermetic offline queries, call native tool `h9.research(topic=..., offline=True)`.
4. **Evaluate Claim Grounding**: Verify each extracted claim has an identified primary source and confidence score >= 0.7.
5. **Output**: Deliver `research_dossier.json` and `research_dossier.yaml`.
```

### 3.3 Skill: `skills/h9-content-planning/SKILL.md`

```yaml
---
name: h9-content-planning
description: "Editorial intelligence, 5-archetype angle generation, 9-dimension scorecard evaluation, and 4-act narrative outline planning."
version: 1.0.0
author: Harness 9, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Content, Editorial, Scriptwriting, Planning, H9]
    related_skills: [h9-research, h9-production]
---

# H9 Editorial Intelligence & Content Planning Skill

## When to use
Use when transitioning from a research dossier into creative framing, angle selection, hook ideation, or narrative structuring.

## Procedural Workflow
1. **Load Research Dossier**: Ingest `ResearchDossier` from `h9.research` or disk.
2. **Generate 5 Angle Archetypes**: Formulate candidate perspectives across:
   - `contrarian`: Subverts popular wisdom or misconceptions.
   - `deep_dive`: Rigorous first-principles technical exploration.
   - `data_led`: Quantitative, empirical metric-driven progression.
   - `human_centric`: Biographical struggle, founder story, human drama.
   - `future_vision`: Extrapolation to future frontiers and societal shift.
3. **Score via 9-Dimension Scorecard**:
   - Compute independent scores (0.0 to 1.0) for: Audience Relevance, Novelty, Hook Potential, Narrative Potential, Creator Fit, Evidence Availability, Visual Potential, Platform Fit, Saturation Risk.
   - Apply weighted composite formula.
4. **Select Winning Angle**: Pick highest composite score, recording selection rationale.
5. **Generate Cognitive Hooks**: Formulate 3+ hook options (curiosity gap, paradox, stakes-first).
6. **Construct 4-Act Outline**: Map acts to target duration percentages (Act 1: 0-25%, Act 2: 25-60%, Act 3: 60-85%, Act 4: 85-100%).
```

### 3.4 Skill: `skills/h9-production/SKILL.md`

```yaml
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
---

# H9 Studio Production Skill

## When to use
Use to execute the complete audiovisual production pipeline from approved outline to speech synthesis, asset freezing, and voice QA.

## Procedural Workflow
1. **Generate Script & Storyboard**: Invoke `h9.generate_script(dossier=..., angle_archetype=...)`.
2. **Discover & Deduplicate Assets**: Invoke `h9.discover_assets(dossier=...)` to freeze unique media into `assets/images/` using SHA-256 and perceptual dHash.
3. **Voice Direction & Acoustic Synthesis**:
   - Map script emotional tags (`[tense]`, `[authoritative]`, `[curious]`) to acoustic parameters.
   - Enforce WPM rate clamping (130-160 WPM).
   - Synthesize `assets/audio/narration.wav`.
4. **Acoustic Voice QA**: Audit generated WAV across the 4 gates (dead air < 1.5s, 0 clipping, volume stability, beat drift < 250ms).
```

### 3.5 Skill: `skills/h9-hyperframes/SKILL.md`

```yaml
---
name: h9-hyperframes
description: "HyperFrames visual composition compilation, 7 canonical visual component blocks, static linting, and headless MP4 video rendering."
version: 1.0.0
author: Harness 9, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Video, HyperFrames, GSAP, Animation, Rendering, H9]
    related_skills: [h9-production]
---

# H9 HyperFrames Video Composition & Rendering Skill

## When to use
Use when compiling a storyboard and frozen assets into a deterministic WebCodecs/GSAP visual composition and rendering an MP4 video.

## Procedural Workflow
1. **Component Assignment**: Assign each scene to one of the 7 canonical visual blocks (`reference_collage_hook`, `split_screen_intro`, `quote_highlight`, `timeline_reveal`, `statistic_reveal`, `comparison_panel`, `creator_bottom_collage`).
2. **Compile Composition**: Assemble `index.html`, `styles.css`, `main.js` with paused GSAP timelines.
3. **Run Static Linter**: Verify 0 remote URLs, finite repeats, and valid DOM elements.
4. **Execute Headless Render**: Call `h9.render(script=..., assets=...)` to generate `renders/final.mp4`.
```

---

## 4. The Typed Production IR Seam (Requirement R3)

### 4.1 Architectural Rationale & Decoupling Boundary

In the legacy implementation, scriptwriting generates raw Markdown files and loosely typed dictionaries passed into `HyperFramesGenerator`. This creates tight coupling between narrative text formatting and DOM construction, making schema evolution fragile.

The **Production Intermediate Representation (IR)** introduces a typed, hermetic Abstract Syntax Tree (AST) boundary. It separates:
- **Upstream Creative Intent**: Editorial angles, narrative acts, speech beats, and voice direction.
- **Downstream Mechanical Execution**: Layout calculation, CSS viewport math, asset resolution, GSAP timeline tracks, and headless frame capture.

```
┌────────────────────────────────────────────────────────┐
│   Narrative Planning & Scriptwriting (Creative Layer)  │
│   (EditorialEngine, ScriptGenerator, VoiceDirector)    │
└───────────────────────────┬────────────────────────────┘
                            │
              Emits Production IR Document
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             TYPED PRODUCTION IR SEAM (AST)             │
│  • IRDocument (Metadata, AudioTrack, Manifest, Timeline│
│  • IRSceneNode (ActRef, NarrationBlock, VisualBlock)   │
│  • IRVisualBlockNode (ComponentType, Props, Bindings)  │
│  • IRSpeechBeat (Start/End, Words, VisualTriggers)     │
└───────────────────────────┬────────────────────────────┘
                            │
          Compiles Composition & Renders Video
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│       HyperFrames Compiler & Headless Renderer         │
│       (ComponentRegistry, Validator, Playwright/FFmpeg)│
└────────────────────────────────────────────────────────┘
```

### 4.2 Complete AST Node Hierarchy & Schema Definitions

The Production IR is formally defined as strict Pydantic v2 schemas:

```python
"""src/models/ir.py — Harness 9 Production Intermediate Representation (IR) Contracts."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator


class IRBlockType(str, Enum):
    """The 7 canonical visual component blocks in the H9 registry."""
    REFERENCE_COLLAGE_HOOK = "reference_collage_hook"
    SPLIT_SCREEN_INTRO = "split_screen_intro"
    QUOTE_HIGHLIGHT = "quote_highlight"
    TIMELINE_REVEAL = "timeline_reveal"
    STATISTIC_REVEAL = "statistic_reveal"
    COMPARISON_PANEL = "comparison_panel"
    CREATOR_BOTTOM_COLLAGE = "creator_bottom_collage"


class IRAssetReference(BaseModel):
    """Cryptographically pinned media asset reference."""
    asset_id: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1, description="Relative path from workspace root")
    file_sha256: str = Field(..., min_length=64, max_length=64)
    media_type: str = Field(default="image/png")
    width: int = Field(default=1920, gt=0)
    height: int = Field(default=1080, gt=0)
    aspect_ratio: str = Field(default="16:9")
    license_type: str = Field(default="Public Domain")
    verified: bool = Field(default=True)


class IRSpeechBeat(BaseModel):
    """Individual vocal cadence beat aligned to acoustic timestamps."""
    beat_id: str = Field(..., min_length=1)
    start_time_sec: float = Field(..., ge=0.0)
    end_time_sec: float = Field(..., ge=0.0)
    text: str = Field(..., min_length=1)
    emphasis_words: List[str] = Field(default_factory=list)
    visual_trigger: Optional[str] = Field(
        default=None,
        description="Named visual animation trigger to fire at this beat start"
    )

    @property
    def duration_sec(self) -> float:
        return max(0.0, self.end_time_sec - self.start_time_sec)


class IRNarrationBlock(BaseModel):
    """Scene-level speech delivery and alignment specification."""
    full_text: str = Field(..., min_length=1)
    voice_profile: str = Field(default="default")
    target_wpm: int = Field(default=145, ge=90, le=220)
    speech_beats: List[IRSpeechBeat] = Field(default_factory=list)


class IRAnimationTrack(BaseModel):
    """Parametric GSAP animation keyframe track."""
    target_selector: str = Field(..., min_length=1)
    property_name: str = Field(..., min_length=1)  # "opacity", "transform", "scale"
    from_value: Union[str, float]
    to_value: Union[str, float]
    start_offset_sec: float = Field(default=0.0, ge=0.0)
    duration_sec: float = Field(default=0.5, gt=0.0)
    easing: str = Field(default="power2.out")


class IRVisualBlockNode(BaseModel):
    """Visual component AST block parameterized for compilation."""
    block_type: IRBlockType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    asset_bindings: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps visual slot parameter name to asset_id in manifest"
    )
    animation_tracks: List[IRAnimationTrack] = Field(default_factory=list)


class IRTransitionSpec(BaseModel):
    """Scene entrance and exit transition dynamics."""
    entrance_type: str = Field(default="fade")
    exit_type: str = Field(default="fade")
    transition_duration_sec: float = Field(default=0.4, ge=0.0, le=2.0)


class IRSceneNode(BaseModel):
    """Independent temporal video scene node."""
    scene_id: str = Field(..., min_length=1)
    scene_index: int = Field(..., ge=1)
    act_index: int = Field(default=1, ge=1, le=4)
    start_time_sec: float = Field(..., ge=0.0)
    duration_sec: float = Field(..., gt=0.0)
    narration: IRNarrationBlock
    visual_block: IRVisualBlockNode
    transitions: IRTransitionSpec = Field(default_factory=IRTransitionSpec)

    @property
    def end_time_sec(self) -> float:
        return self.start_time_sec + self.duration_sec


class IRAudioTrack(BaseModel):
    """Global acoustic master track."""
    audio_rel_path: str = Field(default="assets/audio/narration.wav")
    total_duration_sec: float = Field(..., gt=0.0)
    sample_rate: int = Field(default=44100)
    channels: int = Field(default=2)


class IRMetadata(BaseModel):
    """Global composition configuration."""
    project_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")
    fps: int = Field(default=30, ge=15, le=60)
    width: int = 1920
    height: int = 1080
    brand_primary_color: str = "#00d2ff"
    brand_background_color: str = "#0a0e17"


class ProductionIRDocument(BaseModel):
    """The master root AST document interfacing narrative and visual compilation."""
    ir_version: str = "1.0.0"
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: IRMetadata
    audio_track: IRAudioTrack
    asset_manifest: Dict[str, IRAssetReference] = Field(default_factory=dict)
    scenes: List[IRSceneNode] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_production_invariants(self) -> "ProductionIRDocument":
        """Validate temporal conservation, asset integrity, and speech bounds."""
        if not self.scenes:
            raise ValueError("ProductionIRDocument must contain at least one IRSceneNode")

        # Invariant 1: Temporal Conservation & Contiguity
        expected_start = 0.0
        for i, scene in enumerate(self.scenes):
            if abs(scene.start_time_sec - expected_start) > 0.05:
                raise ValueError(
                    f"Temporal Discontinuity: Scene {scene.scene_id} start ({scene.start_time_sec}s) "
                    f"does not match expected contiguous start ({expected_start}s)."
                )
            expected_start += scene.duration_sec

        # Invariant 2: Audio Track Match
        total_scene_duration = expected_start
        if abs(total_scene_duration - self.audio_track.total_duration_sec) > 0.5:
            raise ValueError(
                f"Audio Drift: Total scene duration ({total_scene_duration}s) diverges from "
                f"audio narration length ({self.audio_track.total_duration_sec}s)."
            )

        # Invariant 3: Asset Binding Integrity
        for scene in self.scenes:
            for slot, asset_id in scene.visual_block.asset_bindings.items():
                if asset_id not in self.asset_manifest:
                    raise ValueError(
                        f"Dangling Asset Reference: Scene {scene.scene_id} binds slot '{slot}' "
                        f"to '{asset_id}', which is missing from asset_manifest."
                    )

        # Invariant 4: Speech Beat Clamping
        for scene in self.scenes:
            for beat in scene.narration.speech_beats:
                if beat.start_time_sec < scene.start_time_sec or beat.end_time_sec > (scene.end_time_sec + 0.1):
                    raise ValueError(
                        f"Speech Beat Out of Bounds: Beat {beat.beat_id} [{beat.start_time_sec}-{beat.end_time_sec}s] "
                        f"escapes Scene {scene.scene_id} [{scene.start_time_sec}-{scene.end_time_sec}s]."
                    )

        return self
```

---

## 5. Provider, Memory & Subagent Integration (Requirement R4)

### 5.1 Role-Based Model Routing via Hermes Providers

In Hermes Agent, model calls route through `providers/` and `plugins/model-providers/`, allowing flexible backend selection (Anthropic, OpenAI, OpenRouter, DeepSeek, local GGUF/llama.cpp) driven by `config.yaml`.

H9 eliminates hardcoded LLM client instantiations by introducing **Logical Capability Roles**:

| Logical Role | Purpose | Model Class / Requirements | Typical Provider Mapping |
|---|---|---|---|
| `researcher` | Broad factual recall, query expansion, claim extraction | Large context window, strong web/factual ground truth | `openrouter` (`anthropic/claude-3.7-sonnet`) or `anthropic` |
| `writer` | Script dialogue, emotional tone modulation, pacing | High stylistic expressiveness, adherence to tone rules | `anthropic` (`claude-3-7-sonnet`) or `openai` (`gpt-4o`) |
| `critic` | 9-dimension scorecard evaluation, QA verification | Analytical reasoning, objective calibration, zero sycophancy | `openrouter` (`openai/o3-mini`) or `anthropic` |
| `planner` | 4-act outline timing, beat math, scene duration scaling | Strict JSON schema conformance, temporal arithmetic | `openai` (`gpt-4o`) or `anthropic` |

#### Configuration in `config.yaml`:
```yaml
h9:
  model_roles:
    researcher:
      provider: "openrouter"
      model: "anthropic/claude-3.7-sonnet"
      temperature: 0.2
    writer:
      provider: "anthropic"
      model: "claude-3-7-sonnet-20250219"
      temperature: 0.7
    critic:
      provider: "openrouter"
      model: "openai/o3-mini"
    planner:
      provider: "openai"
      model: "gpt-4o"
      temperature: 0.1
```

Through `src/h9_runtime/bridge.py`, H9 components call `HermesCapabilityBridge.request_model_completion(role="writer", prompt=...)`. The bridge looks up the configured provider profile, initializes the provider client dynamically, and preserves prompt caching by reusing fixed system prompt prefixes.

### 5.2 Unified Memory Interface (Creator DNA & Project Persistence)

Hermes maintains two core persistence layers:
1. **Curated Markdown Memory (`~/.hermes/memories/USER.md` and `MEMORY.md`)**: Injected into session context at startup as a frozen prefix.
2. **SessionDB (`hermes_state.py`)**: SQLite database with FTS5 full-text search, tracking sessions, messages, and artifacts.

H9 interfaces with Hermes memory without running a competing persistence database:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Hermes Memory Integration                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. CREATOR DNA -> ~/.hermes/memories/USER.md                           │
│    • Brand Constitution (Mission, tone, non-negotiables)              │
│    • Creator Preferences (Pacing WPM, color palette, aspect ratio)     │
│    • Negative Memory (Prohibited buzzwords: "game-changer", etc.)     │
│    • Stored under § section markers; injected into prompt cache prefix │
│                                                                        │
│ 2. CONTENT PROJECTS & PRODUCTION HISTORY -> Hermes SessionDB           │
│    • Session metadata & State Machine audit records                    │
│    • ContentBrief, ResearchDossier, Script, RenderArtifact             │
│    • Searchable via Hermes `session_search` (FTS5 SQLite index)        │
│                                                                        │
│ 3. POST-PUBLISH LEARNING DISTILLATION -> LearningCandidate            │
│    • Evaluated retention drops emit new NegativeConstraints           │
│    • Written directly to USER.md via native `memory` tool              │
└────────────────────────────────────────────────────────────────────────┘
```

- **CreatorProfile Mapping**: Serialized into a structured section in `USER.md`:
  ```markdown
  ## Creator DNA: tech_explorer
  - Tone: Authoritative, engaging, accessible
  - Pacing: 145 WPM
  - Non-negotiables: Every technical claim must cite a primary source.
  - Prohibited words: "game-changer", "revolutionize", "miracle", "paradigm shift".
  §
  ```
- **Project & State Machine Persistence**: Every transition in `ProductionStateMachine` and every production artifact is written to the session's workspace and indexed into `SessionDB`.

### 5.3 Subagent Research Delegation Architecture

When performing extensive research, web searches produce thousands of words of unstructured HTML, boilerplate, and search results. Ingesting this raw content into the parent agent's conversation multiplies token overhead and invalidates the prompt cache.

H9 solves this by delegating the research phase to an **isolated Hermes subagent**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  Parent Hermes Agent (Orchestrator)                     │
│  Conversation History remains clean & cache-stable                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
           Calls `delegate_task` (Goal, Topic, Research Parameters)
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                Isolated Child AIAgent (Subagent Worker)                 │
│  • Fresh conversation history (zero parent pollution)                  │
│  • Task-specific toolset: ["web_search", "web_extract", "h9.research"] │
│  • Blocked tools: ["delegate_task", "clarify", "memory", "cronjob"]    │
│  • Executes multi-source web queries, scraping, and claim verification │
│  • Assembles and validates Pydantic ResearchDossier                     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         Returns Pydantic ResearchDossier JSON + Writes to Disk
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Parent Agent Resumes Loop                          │
│  Parent receives structured ResearchDossier without raw search bloat    │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Delegation Flow Details:
1. **Parent Invocation**:
   ```python
   delegate_task(
       goal="Perform comprehensive factual research on 'The History of the Transistor' and return a verified ResearchDossier.",
       context={
           "topic": "The History of the Transistor",
           "target_duration": 30,
           "offline": False,
           "intent_categories": ["origin_history", "technical_mechanism", "quantitative_metric"],
           "output_file": "workspace/research_dossier.json"
       },
       toolsets=["research", "web"]
   )
   ```
2. **Child Isolation**:
   - The subagent runs inside a worker thread with an isolated `task_id`.
   - Blocked tools (`DELEGATE_BLOCKED_TOOLS`) prevent recursive delegation or unauthorized writes to parent memory.
   - Non-interactive approval callback (`_subagent_auto_deny`) guarantees no hanging prompts.
3. **Execution & Synthesis**:
   - The subagent executes search queries, reads articles via `web_extract`, extracts verifiable claims, and scores confidence.
   - Writes `research_dossier.json` to the session workspace.
4. **Clean Handoff**:
   - The subagent returns the clean, validated `ResearchDossier` JSON string.
   - The parent's context history receives only the structured dossier summary, keeping token consumption minimal and prompt caching 100% intact.

---

## 6. Five-Component Handoff Protocol

### 6.1 Observation
- **State Machine**: 17 canonical states declared in `src/orchestrator/state_machine.py:14-61`. Valid transitions strictly enforced; jumps raise `StateTransitionError`.
- **Contracts**: 17 Pydantic schemas declared in `src/models/contracts.py:43-531`, inheriting `H9BaseModel` with JSON and YAML persistence.
- **Editorial Engine**: Multi-angle generator (`src/editorial/angle_generator.py:40`), 9-dimension scorecard (`src/editorial/scorecard.py:20`), and 4-act outline planner (`src/editorial/narrative_planner.py:15`).
- **Acoustics & QA**: `VoiceDirector` in `src/scriptwriting/voice_director.py:34` supports 4 backends (ElevenLabs, OpenAI, Windows SAPI, Harmonic WAV) with WPM clamping (90-220 WPM). `VoiceQA` (`src/scriptwriting/voice_qa.py:40`) audits 4 acoustic gates.
- **Deduplication**: `AssetDeduplicator` (`src/assets/deduplication.py:34`) applies SHA-256 byte hashing and 64-bit perceptual dHash with Hamming distance threshold $\le 4$.
- **HyperFrames**: 7 canonical visual blocks registered in `adapters/hyperframes/registry.py:30`. Playwright headless browser capture streamed into FFmpeg in `src/hyperframes/renderer.py:50`.
- **Existing Adapter**: `adapters/hermes/bridge.py:32` implements external monolithic pipeline execution rather than native Hermes tool/skill integration.
- **Hermes Runtime Invariants**: Defined in `AGENTS.md` and `tools/registry.py`: prompt caching is sacred (stable prefix), narrow core waist (`_HERMES_CORE_TOOLS` kept minimal), session-scoped surface gates.

### 6.2 Logic Chain
1. *Observation*: The existing `adapters/hermes/bridge.py` executes the entire pipeline as a black box (`pipeline.run()`), preventing Hermes agents from intervening between research, scripting, and rendering.
2. *Deduction*: Decomposing H9 capabilities into 4 granular native model tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) allows the Hermes Agent loop to inspect, iterate, and branch at each production phase.
3. *Observation*: Adding tools directly to `_HERMES_CORE_TOOLS` sends schemas on every API call, violating the Footprint Ladder and wasting prompt tokens.
4. *Deduction*: Registering H9 tools under a dedicated named toolset (`h9_content`) with a service gate (`check_h9_available`) restricts tool visibility to content production sessions while keeping standard conversations lean.
5. *Observation*: Narrative planning outputs text Markdown while HyperFrames consumes DOM/GSAP timelines, creating an implicit structural gap.
6. *Deduction*: A strongly typed Production IR Seam (`ProductionIRDocument`, `IRSceneNode`, `IRVisualBlockNode`) creates an explicit AST contract that guarantees temporal conservation, asset binding integrity, and hermetic rendering.
7. *Observation*: Raw web research generates extensive conversational bloat, degrading prompt caching.
8. *Deduction*: Delegating the research phase to an isolated Hermes subagent via `delegate_task` produces a clean, structured `ResearchDossier` without polluting the parent's context window.

### 6.3 Caveats & Assumptions
- **No Source Code Edits Made**: In accordance with READ-ONLY mode, no production or test files have been modified. All findings are purely observational and design-focused.
- **Audio Rendering Dependencies**: Headless Chromium (Playwright) and FFmpeg must be present in the execution environment for broadcast MP4 rendering; in constrained environments, H9 falls back to pure-Python procedural rendering.
- **Subagent Permissions**: Subagent execution relies on `delegation.subagent_auto_approve` configuration to avoid deadlock in non-interactive CLI environments.

### 6.4 Conclusion
The refactoring of Harness 9 into a native Hermes system is architecturally coherent and directly realizable:
1. Converting H9 capabilities to 4 native model tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) registered in the `h9_content` toolset.
2. Building `src/h9_runtime/bridge.py` as a decoupled capability bridge.
3. Authoring 4 native Hermes skills (`skills/h9-research/`, `skills/h9-content-planning/`, `skills/h9-production/`, `skills/h9-hyperframes/`).
4. Establishing the typed Production IR AST seam in `src/models/ir.py`.
5. Routing model calls through logical roles (`researcher`, `writer`, `critic`, `planner`), unifying creator memory with `USER.md`/`SessionDB`, and isolating research inside a dedicated subagent.

### 6.5 Verification Method
To independently verify this design during implementation:
1. **Unit & Contract Verification**:
   ```bash
   pytest tests/test_production_contracts.py tests/test_state_machine.py -v
   ```
2. **Native Tool Registry Verification**:
   ```python
   from tools.registry import registry
   assert "h9.research" in registry._tools or "h9_research" in registry._tools
   assert "h9_content" in registry.get_registered_toolset_names()
   ```
3. **Hermes Skill Linting & Discovery**:
   ```bash
   python -c "from tools.skill_linter import lint_skill; assert lint_skill('skills/h9-research')"
   ```
4. **End-to-End Pipeline Verification**:
   ```bash
   python verify_pipeline.py --test-mode --output-dir output/test_verification_run
   ```
5. **Acceptance Dimension Suite (A through H)**: Execute the complete integration test suite verifying runtime decoupling, subagent isolation, and MP4 artifact generation.
