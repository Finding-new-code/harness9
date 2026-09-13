# Data Model & Schema Catalog: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/models/`, `src/security/`, `src/creator/`  
**Cross-References:** `docs/API_CONTRACTS.md`, `docs/WORKFLOW_SPEC.md`, `docs/adrs/ADR-002.md`  

---

## 1. Schema Design Philosophy

Harness 9 uses **Pydantic v2** as the single source of truth for all data models. The data architecture satisfies:
1. **Zero Data Loss**: Strict validation preserves exact types and precision across disk and network boundaries.
2. **Dual Serialization**: Every contract natively serializes to both formatted JSON (`.json`) and human-readable YAML (`.yaml`).
3. **Immutability & Integrity**: Stage artifacts are immutable once frozen; any modification requires a new transition record.
4. **Field-Level Validation**: Regular expression format checks, numeric range constraints, and checksum length guarantees are enforced at instantiation.

---

## 2. Production Contracts Catalog (17 Schemas)

### 2.1 `CreatorProfile`
Defines creator identity, brand rules, color palette, and negative constraints.
```yaml
creator_id: "tech_explainer_01"
display_name: "Quantum Frontier"
tone_of_voice: ["authoritative", "curious", "rigorous"]
target_audiences: ["developers", "hardware engineers"]
brand_colors:
  primary: "#00d2ff"
  background: "#0a0e17"
  text: "#ffffff"
  accent: "#ff5252"
default_format: "16:9"
negative_rules:
  - "Never use buzzwords like 'game-changer' or 'revolutionize'"
  - "Avoid unverified hype claims"
voice_preference: "elevenlabs_adam"
metadata: {}
```

### 2.2 `ContentBrief`
Defines the creative goal and production constraints for a video project.
```yaml
project_id: "proj_transistor_001"
topic: "The History of the Transistor: How Bell Labs Changed the World"
target_duration_seconds: 30
aspect_ratio: "16:9"
goal: "Educational Overview"
audience: "Tech Enthusiasts"
offline_mode: true
custom_instructions: "Emphasize Shockley, Bardeen, and Brattain's 1947 breakthrough."
creator_id: "tech_explainer_01"
metadata: {}
```

### 2.3 `ResearchPlan`
Structured search plan with target claim count and category queries.
```yaml
topic: "The History of the Transistor"
target_claim_count: 5
search_queries:
  - ["origin_history", "Bell Labs point contact transistor 1947"]
  - ["technical_mechanism", "Germanium vs Silicon semiconductor amplification"]
  - ["quantitative_metric", "Modern GPU transistor count 80 billion"]
intent_categories: ["origin_history", "technical_mechanism", "quantitative_metric"]
timeout_seconds: 15.0
```

### 2.4 `SourceRecord` & `ClaimRecord`
Provenance tracking for verified factual claims.
```yaml
# SourceRecord
title: "The Invention of the Transistor"
url: "https://www.bell-labs.com/about/history/innovation-stories/transistor/"
publisher: "Nokia Bell Labs"
author: "Bell Labs Historical Archives"
published_date: "1947-12-23"
domain_authority: 0.95
retrieved_at: "2026-08-31T12:00:00Z"
content_snippet: "John Bardeen and Walter Brattain created the point-contact transistor."

# ClaimRecord
claim_id: "claim_001"
claim_text: "In December 1947, Bell Labs physicists created the first working point-contact transistor using germanium."
confidence_score: 0.98
verification_status: "VERIFIED"
primary_source: { ... } # SourceRecord
corroborating_sources: []
tags: ["history", "breakthrough", "1947"]
```

### 2.5 `ResearchDossier`
Consolidated research findings, claims, and statistical facts.
```yaml
topic: "The History of the Transistor"
executive_summary: "The transition from fragile vacuum tubes to solid-state semiconductors."
claims: [ { ... } ]
sources: [ { ... } ]
statistics: [ { "metric": "Transistors in modern chip", "value": "100 Billion" } ]
entity_mentions: ["John Bardeen", "Walter Brattain", "William Shockley"]
generated_at: "2026-08-31T12:05:00Z"
```

### 2.6 `EditorialAngle` & `EditorialScorecard`
Evaluated narrative angles and scorecard metrics.
```yaml
angle_id: "angle_contrarian_01"
title: "The Accidental Revolution: Why Silicon Valley Almost Didn't Happen"
narrative_style: "Contrarian Revelation"
archetype: "contrarian"
core_thesis: "The transistor was nearly abandoned because germanium was too brittle."
key_hooks:
  - "What if the greatest invention of the 20th century was almost thrown in the trash?"
scorecard:
  audience_relevance: 0.92
  novelty: 0.88
  hook_potential: 0.95
  narrative_potential: 0.90
  creator_fit: 0.95
  evidence_availability: 0.90
  visual_potential: 0.85
  platform_fit: 0.90
  saturation_risk: 0.15
  composite_score: 0.9125
selected: true
selection_rationale: "Highest composite score with strong hook potential."
```

### 2.7 `ContentOutline`
4-act narrative structure mapping time percentages and visual directions.
```yaml
topic: "The History of the Transistor"
selected_angle_id: "angle_contrarian_01"
primary_hook: "What if the greatest invention of the 20th century was almost thrown in the trash?"
acts:
  - act_index: 1
    act_name: "The Hook"
    target_start_pct: 0.0
    target_end_pct: 0.15
    narrative_focus: "The failure-prone vacuum tube bottleneck."
  - act_index: 2
    act_name: "The Barrier"
    target_start_pct: 0.15
    target_end_pct: 0.45
  - act_index: 3
    act_name: "The Breakthrough"
    target_start_pct: 0.45
    target_end_pct: 0.75
  - act_index: 4
    act_name: "The Ripple Effect"
    target_start_pct: 0.75
    target_end_pct: 1.0
total_estimated_duration: 30.0
```

### 2.8 `Script` & `ScriptBeat`
Scene-by-scene script with timing, narration text, and visual requirements.
```yaml
script_id: "script_001"
topic: "The History of the Transistor"
word_count: 72
estimated_duration_seconds: 30.0
scenes:
  - scene_id: "scene_1"
    act_index: 1
    start_time_seconds: 0.0
    end_time_seconds: 4.5
    narration_text: "In 1947, computing was trapped inside glowing glass vacuum tubes that constantly burned out."
    visual_description: "Glowing vacuum tubes flickering and failing."
    component_type: "reference_collage_hook"
    required_assets: ["asset_req_01"]
```

### 2.9 `AssetRecord` & `AssetLedger`
Cryptographically verified media assets with SHA-256 and dHash.
```yaml
asset_id: "asset_transistor_svg"
local_path: "assets/images/transistor.svg"
file_size_bytes: 14250
file_sha256: "a3f5e1b8c2d9...64_chars"
perceptual_hash: "dhash_ffff0000aaaa5555"
media_type: "image/svg+xml"
dimensions:
  width: 1920
  height: 1080
  aspect_ratio: "16:9"
source_provider: "procedural_generator"
license:
  license_type: "CC0-1.0 (Public Domain)"
  attribution_required: false
verification_status: "VERIFIED"
```

### 2.10 `EvaluationReport` (ContentBench)
Quality audit report generated across 4 evaluation layers.
```yaml
run_id: "run_prod_001"
layer: "layer_2_script"
scores:
  hook_strength: 0.95
  pacing_cadence: 0.90
  readability_flesch: 0.88
  dna_adherence: 1.0
composite_score: 0.9325
passed: true
feedback:
  - "Strong hook opening curiosity gap."
  - "Pacing matches target 145 WPM cadence."
```

### 2.11 `RenderArtifact` & `PublishPackage`
Final production delivery bundle with video metadata.
```yaml
# RenderArtifact
video_path: "renders/final.mp4"
duration_seconds: 30.0
file_size_bytes: 5242880
width: 1920
height: 1080
fps: 30
video_codec: "h264"
audio_codec: "aac"
validation_status: "VERIFIED"

# PublishPackage
project_id: "proj_transistor_001"
title: "The Accidental Invention of the Transistor"
description: "How Bell Labs physicists revolutionized computing in 1947."
tags: ["tech", "history", "computing", "semiconductor"]
video_path: "renders/final.mp4"
thumbnail_path: "renders/thumb.png"
captions_vtt_path: "assets/captions.vtt"
total_cost_usd: 0.165
```

---

## 3. Audio & VoiceQA Schemas

```yaml
# VoiceProfile
voice_id: "adam_neural"
provider: "elevenlabs"
display_name: "Adam (Authoritative)"
speaking_rate_wpm: 145
stability: 0.5
similarity_boost: 0.75

# VoiceQAReport
passed: true
total_duration_sec: 29.85
clipping_events_count: 0
clipping_ratio: 0.0
dead_air_instances_count: 0
max_dead_air_duration_sec: 0.18
average_gap_duration_sec: 0.14
loudness_variance_db: 1.2
speech_beat_max_drift_sec: 0.08
metrics:
  rms_loudness_dbfs: -18.4
  peak_dbfs: -1.2
```

---

## 4. Creator Economics & Security Schemas

```yaml
# CostItem
category: "llm"
item_name: "gpt-4o-completion-tokens"
units_consumed: 3800.0
unit_type: "tokens"
unit_rate_usd: 0.000010
total_cost_usd: 0.0380

# ProductionCostLedger
run_id: "run_prod_001"
project_id: "proj_transistor_001"
items: [ { ... } ]
total_cost_usd: 0.1666
cost_per_video_second: 0.00555
estimated_margin_percent: 78.5

# CapabilityToken
token_id: "cap_7a9f82d1c0e3"
subject_id: "worker_researcher_01"
role: "researcher"
workflow_id: "proj_transistor_001"
workflow_stage: "RESEARCH_IN_PROGRESS"
allowed_tools: ["search_web", "fetch_url"]
allowed_write_paths: ["output/proj_transistor_001/research"]
allowed_network_hosts: ["commons.wikimedia.org"]
expires_at_utc: 1788200000.0
delegation_depth: 1
signature: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```
