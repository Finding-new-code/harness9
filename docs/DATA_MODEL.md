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

---

## 5. Epistemic Verification Layer Schemas (Extended Contracts)

**Package:** `src/models/contracts.py`, `src/epistemic/`  
**Cross-References:** `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/epistemic/EVIDENCE_GRAPH.md`, `docs/epistemic/FACT_CHECKING_SPEC.md`

### 5.1 Epistemic Enumerations

```python
class EpistemicStatus(str, Enum):
    """11 discrete machine-readable verification statuses."""
    VERIFIED = "verified"                    # Confirmed by >=2 independent high-tier sources
    SUPPORTED = "supported"                  # Entailed by >=1 reliable source without contradiction
    PARTIALLY_SUPPORTED = "partially_supported" # Core fact supported, but details/numbers diverge
    CONTESTED = "contested"                  # Legitimate scholarly or empirical dispute exists
    CONTRADICTED = "contradicted"            # Refuted by authoritative counter-evidence
    UNSUPPORTED = "unsupported"              # No cited evidence entails the assertion
    UNVERIFIABLE = "unverifiable"            # Cannot be empirically or textually tested
    OUTDATED = "outdated"                    # Was historically true, but superseded by newer data
    MISLEADING = "misleading"                # True in isolation, but contextually deceptive
    OPINION = "opinion"                      # Subjective or evaluative judgment
    PREDICTION = "prediction"                # Forward-looking forecast

class ClaimType(str, Enum):
    """Typology of factual claims dictating verification policy."""
    EVENT_FACT = "event_fact"                # Empirical historical or physical event
    CAUSAL_INTERPRETATION = "causal_interpretation" # Explanatory theory for why an event occurred
    SCHOLARLY_INTERPRETATION = "scholarly_interpretation" # Historiographical paradigm
    NUMERICAL_METRIC = "numerical_metric"    # Quantitative measurement, count, dimension
    DIRECT_QUOTE = "direct_quote"            # Exact speech or written statement
    SCIENTIFIC_LAW = "scientific_law"        # Empirically validated physical or biological rule
    CURRENT_EVENT = "current_event"          # Contemporary news occurrence
    DEFINITIONAL = "definitional"            # Terminology or semantic definition

class ConsensusState(str, Enum):
    """8-state historiographical and scientific consensus classifications."""
    STRONG_CONSENSUS = "STRONG_CONSENSUS"    # Overwhelming agreement across modern scholarship
    BROAD_CONSENSUS = "BROAD_CONSENSUS"      # General specialist agreement; negligible dissent
    MAJORITY_INTERPRETATION = "MAJORITY_INTERPRETATION" # Dominant academic view; recognized alternatives
    MINORITY_INTERPRETATION = "MINORITY_INTERPRETATION" # Credible academic counter-thesis
    ACTIVE_DEBATE = "ACTIVE_DEBATE"          # Substantial, ongoing academic debate
    CONTESTED = "CONTESTED"                  # Direct dispute between primary records
    UNRESOLVED = "UNRESOLVED"                # Insufficient surviving evidence to decide
    INSUFFICIENT_LITERATURE = "INSUFFICIENT_LITERATURE" # Topic lacks adequate peer-reviewed study

class SourceTier(int, Enum):
    """13-tier hierarchical source taxonomy ranking epistemic authority."""
    PRIMARY_SOURCE = 1                       # Archival records, treaties, raw datasets
    PEER_REVIEWED_JOURNAL = 2                # Refereed academic journals (Nature, Science)
    ACADEMIC_PRESS_BOOK = 3                  # University press monographs (Oxford, Cambridge)
    HISTORICAL_DOCUMENT_CRITICAL_EDITION = 4 # Scholarly edited historical editions
    GOVERNMENT_RECORD_STATISTICAL_AGENCY = 5 # Census, BLS, NIST, NASA technical reports
    PREPRINT_SCHOLARLY = 6                   # arXiv, bioRxiv preprints (must be hedged)
    SPECIALIZED_SCHOLARLY_DATABASE = 7       # PDB, UniProt, ChEMBL, curated repositories
    REPUTABLE_NEWS_INVESTIGATIVE = 8         # Reuters, AP, BBC, NYT investigative desks
    GENERAL_ENCYCLOPEDIC = 9                 # Britannica, Stanford Enc Phil, Wikipedia (non-sole)
    CORPORATE_WHITE_PAPER = 10               # Vendor specifications, technical manuals
    BLOG_OPINION_COMMENTARY = 11             # Expert blogs, Substack (opinions only)
    SOCIAL_MEDIA_FORUM = 12                  # Twitter, Reddit, forums (untrusted)
    UNVERIFIED = 13                          # Anonymous aggregators, hallucinations (rejected)
```

### 5.2 Extended Production Contracts

```yaml
# Extended SourceRecord
source_id: "src_bell_labs_1947"
title: "The Point-Contact Transistor"
url: "https://www.bell-labs.com/about/history/transistor/"
publisher: "Nokia Bell Labs"
author: "Bell Labs Historical Archives"
published_date: "1947-12-23"
reliability_score: 1.0
tier: 1                                      # SourceTier.PRIMARY_SOURCE
domain_authority: 0.98
doi: null
peer_reviewed: false
archived_url: "https://web.archive.org/web/..."
content_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
retrieved_at: "2026-09-13T12:00:00Z"
is_sanitized: true
metadata: {}

# Extended ClaimRecord
claim_id: "claim_001"
claim_text: "In December 1947, Bell Labs physicists John Bardeen and Walter Brattain created the first working point-contact transistor."
category: "history"
confidence_score: 0.98                       # Retrieval confidence
epistemic_status: "verified"                 # EpistemicStatus.VERIFIED
claim_type: "event_fact"                     # ClaimType.EVENT_FACT
consensus_state: "STRONG_CONSENSUS"          # ConsensusState.STRONG_CONSENSUS
primary_source: { ... }                      # Extended SourceRecord
corroborating_sources: [ { ... } ]
contradicting_sources: []
evidence_links:
  - evidence_unit_id: "eu_001"
    source_id: "src_bell_labs_1947"
    verbatim_excerpt: "On December 23, 1947, John Bardeen and Walter Brattain demonstrated the point-contact transistor."
    char_offset_start: 1024
    char_offset_end: 1145
    entailment_relation: "SUPPORTS"
    confidence: 1.0
temporal_context:
  valid_from: "1947-12-23"
  valid_until: null
  as_of_date: "2026-09-13"
  is_time_sensitive: false
  temporal_status: "historical"
verifier_metadata:
  strategy_used: "SOURCE_ENTAILMENT"
  verifier_name: "H9EpistemicVerificationEngine"
  verified_at: "2026-09-13T17:20:00Z"
  verification_trace_id: "vtr_7a9f82d1"
  entailment_score: 0.99
  contradiction_score: 0.0
```

### 5.3 Evidence Graph DAG Schema

```yaml
# EvidenceGraphDocument
graph_id: "eg_proj_transistor_001"
project_id: "proj_transistor_001"
nodes:
  sources: [ { "node_id": "src_001", "tier": 1, "sha256": "..." } ]
  passages: [ { "node_id": "pas_001", "source_id": "src_001", "char_start": 100, "char_end": 250 } ]
  evidence_units: [ { "node_id": "eu_001", "passage_id": "pas_001", "statement": "...", "modality": "CERTAIN" } ]
  claims: [ { "node_id": "claim_001", "epistemic_status": "verified", "consensus": "STRONG_CONSENSUS" } ]
  script_sentences: [ { "node_id": "sent_001", "scene_id": "scene_1", "text": "..." } ]
  visual_elements: [ { "node_id": "vis_001", "block_type": "STATISTIC_REVEAL", "parameter_key": "stat_number" } ]
  verification_traces: [ { "node_id": "vtr_001", "strategy": "SOURCE_ENTAILMENT", "entailment_score": 0.99 } ]
edges:
  - { source: "src_001", target: "pas_001", relation: "PROVIDES" }
  - { source: "pas_001", target: "eu_001", relation: "EXTRACTS_FROM" }
  - { source: "eu_001", target: "claim_001", relation: "ENTAILS", weight: 1.0 }
  - { source: "claim_001", target: "sent_001", relation: "GROUNDS" }
  - { source: "claim_001", target: "vis_001", relation: "BINDS_TO" }
```

### 5.4 Numerical Data Contracts (Deterministic Lineage)

```yaml
# NumericalDataPoint
x_value: 1947
y_value: 1.0
label: "First Point-Contact Transistor"
uncertainty_range: null

# NumericalDataset
dataset_id: "ds_transistor_scaling_01"
title: "Transistor Count Scaling in Semiconductor Computing (1947-2024)"
x_label: "Year"
y_label: "Transistor Count"
x_unit: "year"
y_unit: "count"
data_points:
  - { x_value: 1947, y_value: 1.0, label: "Bell Labs Point-Contact" }
  - { x_value: 1971, y_value: 2300.0, label: "Intel 4004" }
  - { x_value: 2024, y_value: 208000000000.0, label: "Modern AI Accelerator" }
source_record: { ... }                       # SourceRecord
dataset_sha256: "b4c2...64_chars"
```

