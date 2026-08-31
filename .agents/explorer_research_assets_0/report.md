# Research & Asset Engine Technical Specification (Requirements R1 & R2)

**Author:** Research & Asset API Explorer (`explorer_research_assets_0`)  
**Date:** 2026-08-31  
**Target System:** Harness 9 Automated Video Generation Pipeline  
**Scope:** Requirement R1 (Research & Fact Synthesis Engine) & Requirement R2 (Asset Discovery, Rights Ledger & Local Freezing)

---

## 1. Executive Summary & Architectural Overview

The Harness 9 Video Generation Pipeline automates the synthesis of creator briefs into rendered MP4 videos. Within this pipeline, **R1 (Research & Fact Synthesis)** and **R2 (Asset Discovery & Rights Ledger)** form the foundational ingestion and provenance layer upon which all downstream scripting, voiceover, and visual composition rely.

```
+-----------------------------------------------------------------------------------+
|                              PIPELINE ARCHITECTURE                                |
+-----------------------------------------------------------------------------------+

   +-------------------+
   |   Creator Topic   |  (e.g., "The History of the Transistor")
   |    / Brief Input  |
   +---------+---------+
             |
             v
   +-------------------+     [Online Search APIs: Exa / Tavily / Firecrawl]
   |   R1: Research    |<--------------------------------------------------+
   |   & Fact Engine   |     [Offline Deterministic Research Fallback DB]
   +---------+---------+
             |
             +------------------------------+
             |                              |
             v                              v
   +-------------------+          +-------------------+
   |  Research Dossier |          | Visual Directives |
   |    (JSON/YAML)    |          |  & Search Terms   |
   +---------+---------+          +---------+---------+
             |                              |
             | (Feeds R3 Scriptwriter)      v
             |                    +-------------------+   [APIs: Wikimedia Commons / Pexels]
             |                    |    R2: Asset      |<------------------------------------+
             |                    |   Discovery &     |   [Offline Procedural / SVG Mocks]
             |                    | Freezing Pipeline |
             |                    +---------+---------+
             |                              |
             |                              v
             |                    +-------------------+
             |                    |   Asset Ledger    | + Frozen Local Assets
             |                    |    (JSON/YAML)    |   (assets/images/*.jpg/png/svg)
             |                    +---------+---------+
             |                              |
             +--------------+---------------+
                            |
                            v
   +--------------------------------------------------+
   | Downstream Stages: R3 Scripting & TTS Narration  |
   | R4 HyperFrames Composition -> Rendered MP4 Video |
   +--------------------------------------------------+
```

### Core Architectural Invariants:
1. **Schema Strictness:** All intermediate artifacts (`research_dossier.json`/`.yaml` and `asset_ledger.json`/`.yaml`) must adhere to strict, validated schemas.
2. **Rights & Provenance Traceability:** Every factual claim must have verifiable source citations, and every visual asset must have explicit machine-readable licensing and attribution metadata.
3. **Hermetic Freezing (Zero Broken Paths):** Video renderers (Chromium headless/FFmpeg) must never fetch live web URLs during composition rendering. 100% of media assets must be downloaded, validated, and frozen locally as relative paths (`assets/...`).
4. **Deterministic / Offline Fallback Mode:** The entire pipeline must be capable of executing offline in CI/CD or test environments with zero network calls, producing high-fidelity mock dossiers and procedural vector/media assets.

---

## 2. Requirement R1: Research & Fact Synthesis Engine

### 2.1 Multi-Stage Query Strategy

To transform a high-level user prompt or topic brief into a structured, verifiable dossier, the Research Engine employs a **4-phase query expansion and synthesis pipeline**:

```
+-----------------------------------------------------------------------------------+
|                        R1 QUERY & SYNTHESIS WORKFLOW                              |
+-----------------------------------------------------------------------------------+

 [Topic Brief] ---> Phase 1: Query Expansion (3-5 Intent-Specific Queries)
                         |
                         v
                    Phase 2: Search Provider Dispatch (Tavily/Exa/Firecrawl/Fallback)
                         |
                         v
                    Phase 3: Content Normalization & Snippet Parsing
                         |
                         v
                    Phase 4: Fact Synthesis & Confidence Scoring
                         |
                         v
                    [Structured Research Dossier (JSON/YAML)]
```

#### Phase 1: Query Intent Expansion
A single topic brief (e.g., *"The History of the Transistor"*) is decomposed into 5 orthogonal query dimensions:
1. **Chronological / Genesis Query:** `"Transistor invention 1947 Bell Labs Bardeen Brattain Shockley origins"`
2. **Technical / Mechanism Query:** `"How point-contact and bipolar junction transistors work semiconductor germanium silicon"`
3. **Quantitative / Milestone Query:** `"Transistor count Moore's law modern microprocessors statistics 1947 to 2026"`
4. **Socio-Economic / Impact Query:** `"Global impact of the transistor computing revolution information age"`
5. **Visual Subject Query:** `"Original point contact transistor Bell Labs historical photographs patent diagrams"`

#### Phase 2: Search Execution & Provider Routing
- Primary adapters supported:
  - **Tavily Search API:** Optimised for factual extracts and clean context snippets.
  - **Exa Search API:** High-precision semantic search with document parsing.
  - **Firecrawl API:** Deep content extraction from specific authority URLs.
  - **Native/Offline Mock:** Fast-path local search simulation for test environments.

#### Phase 3: Content Extraction & Deduplication
- Raw HTML/text results are cleaned of boilerplate, tracking parameters, and ads.
- Results are indexed by normalized URL and scored for domain authority (e.g. `.edu`, `.org`, `ieee.org`, `nobelprize.org`, `computerhistory.org`, `wikipedia.org`).

#### Phase 4: Claim Synthesis & Confidence Scoring
Extracted claims are evaluated using a deterministic scoring formula:

$$\text{Confidence Score} = w_{\text{auth}} \cdot A + w_{\text{corrob}} \cdot C + w_{\text{clarity}} \cdot Q - P_{\text{conflict}}$$

Where:
- $A \in [0.0, 1.0]$: Domain authority weight ($1.0$ for primary archives/peer-reviewed, $0.8$ for major encyclopedias, $0.6$ for standard news, $0.4$ for blogs).
- $C \in [0.0, 1.0]$: Corroboration score ($1.0$ if $\ge 3$ distinct sources agree, $0.7$ if 2 sources agree, $0.4$ for single source).
- $Q \in [0.0, 1.0]$: Claim specificity/clarity (contains precise names, dates, numbers).
- $P_{\text{conflict}} \in [0.0, 0.5]$: Penalty applied if conflicting claims or disputed dates are detected.

**Confidence Tiers:**
- **High Confidence ($\ge 0.85$):** Ground-truth facts suitable for primary voiceover assertions.
- **Medium Confidence ($0.60 - 0.84$):** Standard context and supporting historical details.
- **Low Confidence ($< 0.60$):** Anecdotes or disputed estimates; flagged with verification notes.

---

### 2.2 Research Dossier Schema Specification

The research dossier must be serializable to both **JSON** and **YAML**.

#### Schema Definition (JSON Schema Draft-07 compliant):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ResearchDossier",
  "type": "object",
  "required": [
    "schema_version",
    "topic",
    "metadata",
    "summary",
    "claims",
    "talking_points",
    "statistics",
    "suggested_visual_queries"
  ],
  "properties": {
    "schema_version": { "type": "string", "enum": ["1.0.0"] },
    "topic": { "type": "string" },
    "metadata": {
      "type": "object",
      "required": ["run_id", "generated_at", "mode", "target_duration_seconds"],
      "properties": {
        "run_id": { "type": "string" },
        "generated_at": { "type": "string", "format": "date-time" },
        "mode": { "type": "string", "enum": ["online", "offline_fallback"] },
        "target_duration_seconds": { "type": "integer", "minimum": 5, "maximum": 600 },
        "search_backend": { "type": "string" }
      }
    },
    "summary": {
      "type": "object",
      "required": ["headline", "executive_summary", "key_takeaways"],
      "properties": {
        "headline": { "type": "string" },
        "executive_summary": { "type": "string" },
        "key_takeaways": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 2
        }
      }
    },
    "claims": {
      "type": "array",
      "minItems": 3,
      "items": {
        "type": "object",
        "required": [
          "claim_id",
          "claim_text",
          "category",
          "confidence_score",
          "primary_source",
          "visual_cue_suggestion"
        ],
        "properties": {
          "claim_id": { "type": "string", "pattern": "^claim_[0-9]{2,}$" },
          "claim_text": { "type": "string" },
          "category": {
            "type": "string",
            "enum": [
              "origin_history",
              "technical_mechanism",
              "quantitative_metric",
              "modern_impact",
              "key_figure"
            ]
          },
          "confidence_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "primary_source": {
            "type": "object",
            "required": ["title", "url"],
            "properties": {
              "title": { "type": "string" },
              "url": { "type": "string", "format": "uri" },
              "publisher": { "type": "string" }
            }
          },
          "corroborating_sources": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["title", "url"],
              "properties": {
                "title": { "type": "string" },
                "url": { "type": "string" }
              }
            }
          },
          "visual_cue_suggestion": { "type": "string" },
          "verification_notes": { "type": "string" }
        }
      }
    },
    "talking_points": {
      "type": "array",
      "minItems": 3,
      "items": {
        "type": "object",
        "required": [
          "beat_index",
          "title",
          "narrative_hook",
          "supported_claim_ids",
          "estimated_duration_sec"
        ],
        "properties": {
          "beat_index": { "type": "integer", "minimum": 1 },
          "title": { "type": "string" },
          "narrative_hook": { "type": "string" },
          "supported_claim_ids": {
            "type": "array",
            "items": { "type": "string" }
          },
          "estimated_duration_sec": { "type": "number", "minimum": 1.0 }
        }
      }
    },
    "statistics": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["metric", "value", "context", "source_claim_id"],
        "properties": {
          "metric": { "type": "string" },
          "value": { "type": "string" },
          "context": { "type": "string" },
          "source_claim_id": { "type": "string" }
        }
      }
    },
    "suggested_visual_queries": {
      "type": "array",
      "minItems": 3,
      "items": { "type": "string" }
    }
  }
}
```

#### Annotated YAML Dossier Example (`research_dossier.yaml`):

```yaml
schema_version: "1.0.0"
topic: "The History of the Transistor"
metadata:
  run_id: "run_20260831_transistor_poc"
  generated_at: "2026-08-31T04:52:00Z"
  mode: "online"
  target_duration_seconds: 30
  search_backend: "tavily"

summary:
  headline: "How Three Bell Labs Physicists Ignited the Digital Age in 1947"
  executive_summary: >
    In December 1947, John Bardeen, Walter Brattain, and William Shockley created the first
    working point-contact transistor at Bell Labs. Replacing fragile, power-hungry vacuum tubes,
    the transistor enabled solid-state electronics, microchips, and the modern computing era.
  key_takeaways:
    - "Invented in December 1947 at Bell Labs using germanium crystal and gold foil."
    - "Bardeen, Brattain, and Shockley were awarded the 1956 Nobel Prize in Physics."
    - "Modern microprocessors contain over 100 billion transistors on a single chip."

claims:
  - claim_id: "claim_01"
    claim_text: "The first working point-contact transistor was successfully demonstrated on December 23, 1947, by John Bardeen and Walter Brattain at Bell Laboratories."
    category: "origin_history"
    confidence_score: 0.98
    primary_source:
      title: "The Invention of the Transistor - Bell Labs Archive"
      url: "https://www.bell-labs.com/about/history/transistor/"
      publisher: "Nokia Bell Labs"
    corroborating_sources:
      - title: "December 23, 1947: Transistor Invented - APS Physics"
        url: "https://www.aps.org/publications/apsnews/200012/history.cfm"
      - title: "Computer History Museum - The Transistor Milestone"
        url: "https://www.computerhistory.org/siliconengine/invention-of-the-point-contact-transistor/"
    visual_cue_suggestion: "Historical replica photo of the 1947 point-contact transistor with germanium crystal and plastic wedge"
    verification_notes: "Unanimous historical consensus across Nobel, Bell Labs, and IEEE archives."

  - claim_id: "claim_02"
    claim_text: "Shockley, Bardeen, and Brattain were jointly awarded the 1956 Nobel Prize in Physics for their research on semiconductors and the transistor effect."
    category: "key_figure"
    confidence_score: 1.00
    primary_source:
      title: "The Nobel Prize in Physics 1956"
      url: "https://www.nobelprize.org/prizes/physics/1956/summary/"
      publisher: "The Nobel Foundation"
    visual_cue_suggestion: "Photograph of John Bardeen, William Shockley, and Walter Brattain at Bell Labs laboratory workbench"
    verification_notes: "Verified via official Nobel Prize citation."

  - claim_id: "claim_03"
    claim_text: "Early vacuum tubes consumed large amounts of power and generated high heat; transistors slashed power consumption by over 99% and miniaturized circuits."
    category: "technical_mechanism"
    confidence_score: 0.92
    primary_source:
      title: "From Vacuum Tubes to Transistors - IEEE Spectrum"
      url: "https://spectrum.ieee.org/from-vacuum-tubes-to-transistors"
      publisher: "IEEE Spectrum"
    visual_cue_suggestion: "Side-by-side comparison diagram of a glowing glass vacuum tube versus a tiny modern semiconductor chip"
    verification_notes: "Consistent with standard solid-state electronics engineering benchmarks."

  - claim_id: "claim_04"
    claim_text: "By 2026, leading-edge semiconductor chips pack over 100 billion transistors onto a silicon die smaller than a postage stamp."
    category: "quantitative_metric"
    confidence_score: 0.95
    primary_source:
      title: "Semiconductor Industry Roadmap & Transistor Scaling"
      url: "https://www.semiconductors.org/technology-and-innovation/"
      publisher: "Semiconductor Industry Association"
    visual_cue_suggestion: "Macro photograph of modern silicon wafer microchip die with iridescent microscopic circuitry"
    verification_notes: "Matches TSMC, Apple M-series, and Nvidia GPU transistor density disclosures."

talking_points:
  - beat_index: 1
    title: "The Vacuum Tube Bottleneck"
    narrative_hook: "Before the computer in your pocket, early computers filled entire rooms with burning hot, glass vacuum tubes."
    supported_claim_ids: ["claim_03"]
    estimated_duration_sec: 7.0

  - beat_index: 2
    title: "The Miracle at Bell Labs"
    narrative_hook: "On two cold days in December 1947, three physicists made history with a sliver of germanium, gold foil, and a paper clip."
    supported_claim_ids: ["claim_01", "claim_02"]
    estimated_duration_sec: 13.0

  - beat_index: 3
    title: "100 Billion Strong"
    narrative_hook: "Today, that single rough prototype has scaled to over 100 billion microscopic switches powering every AI and phone on Earth."
    supported_claim_ids: ["claim_04"]
    estimated_duration_sec: 10.0

statistics:
  - metric: "Date of First Working Demonstration"
    value: "December 23, 1947"
    context: "Bell Labs, Murray Hill, New Jersey"
    source_claim_id: "claim_01"
  - metric: "Nobel Prize Year"
    value: "1956"
    context: "Awarded jointly to Bardeen, Brattain, and Shockley"
    source_claim_id: "claim_02"
  - metric: "Modern Transistor Count"
    value: "100,000,000,000+"
    context: "Transistors packed per state-of-the-art silicon die"
    source_claim_id: "claim_04"

suggested_visual_queries:
  - "Point contact transistor 1947 Bell Labs replica"
  - "Bardeen Brattain Shockley Bell Labs laboratory"
  - "Vacuum tube vs transistor comparison"
  - "Modern silicon wafer semiconductor microchip"
```

---

### 2.3 Deterministic & Offline Fallback Research Mode

To guarantee **100% flake-free CI/CD and unit testing** without relying on external network requests or paid search API tokens, the Research Engine implements a multi-tier offline fallback subsystem:

```
+-----------------------------------------------------------------------------------+
|                        OFFLINE RESEARCH FALLBACK STRATEGY                         |
+-----------------------------------------------------------------------------------+

                       [Run Research Engine Request]
                                     |
                Is '--offline' set OR are API keys missing?
                               /           \
                             YES            NO
                             /                \
          [Offline Fallback Mode]          [Attempt Live Web Search]
                    |                                 |
     Does topic match Preset Catalog?            Search succeeds?
          /                  \                    /             \
        YES                   NO                YES              NO (API error/net down)
        /                       \                /                \
 [Load Curated Preset]   [Procedural Dossier   [Live Dossier]   [Fallback to Offline]
                          Synthesizer (Seed)]
```

#### Tier 1: Curated Benchmark Catalog (`research_presets/`)
Pre-baked, expertly verified dossiers for standard demo topics are bundled in the repository:
1. `transistor_history.yaml` ("The History of the Transistor")
2. `how_gpus_work.yaml` ("How GPUs Work: Parallel Computing Explained")
3. `apollo_guidance_computer.yaml` ("The Apollo 11 Guidance Computer")
4. `quantum_computing_basics.yaml` ("How Quantum Computers Work")

#### Tier 2: Procedural Topic Synthesizer (Arbitrary Offline Topics)
For arbitrary topic briefs passed in offline mode (e.g., `"The History of Concrete"`), a deterministic heuristic generator generates a structured dossier:
- Hashes the input string using `hashlib.sha256(topic.encode()).hexdigest()` to initialize a pseudo-random generator.
- Generates 3-4 structured claims, 3 talking points with exact durations, domain-relevant synthetic sources (`archive.org`, `wikipedia.org`), and visual cue directives.
- Produces valid, schema-compliant JSON/YAML that passes 100% of validation rules.

---

## 3. Requirement R2: Asset Discovery, Rights Ledger & Local Freezing

### 3.1 Media Search Strategies across Repositories & APIs

The Asset Discovery subsystem queries open-access and public domain repositories to acquire high-resolution visual assets.

```
+-----------------------------------------------------------------------------------+
|                      MEDIA DISCOVERY REPOSITORY MATRIX                            |
+-----------------------------------------------------------------------------------+

  Repository           Endpoint / Strategy                    License Models
  ----------------------------------------------------------------------------------
  Wikimedia Commons    MediaWiki Action API (generator=search)  Public Domain, CC0, CC-BY, CC-BY-SA
  Pexels API           https://api.pexels.com/v1/search        Pexels License (Commercial, Free)
  NASA Image Library   https://images-api.nasa.gov/search      US Govt Public Domain
  Offline Procedural   Built-in SVG/Canvas Generator           CC0 1.0 (Procedural Fallback)
```

#### 1. Wikimedia Commons API Strategy
- **Endpoint:** `https://commons.wikimedia.org/w/api.php`
- **Request Parameters:**
  ```http
  GET /w/api.php?action=query
      &format=json
      &generator=search
      &gsrsearch=Point+contact+transistor+filetype:bitmap
      &gsrnamespace=6
      &gsrlimit=5
      &prop=imageinfo
      &iiprop=url|size|mime|extmetadata|dimensions
      &iiurlwidth=1920
  ```
- **ExtMetadata Extraction:**
  - License detection reads `extmetadata.LicenseShortName.value` (e.g., `"Public domain"`, `"CC BY-SA 4.0"`).
  - Creator extraction reads `extmetadata.Artist.value` (cleans HTML entities and tags).
  - Attribution text reads `extmetadata.Credit.value` or synthesizes standard CC attribution.

#### 2. Pexels API Strategy
- **Endpoint:** `https://api.pexels.com/v1/search`
- **Headers:** `Authorization: <PEXELS_API_KEY>`
- **Request Parameters:** `query=semiconductor+microchip&per_page=5&orientation=landscape`
- **License Extraction:**
  - License is categorized as `"Pexels License"` (commercial use permitted, modification permitted, no legal attribution required).
  - Author and profile link (`photographer`, `photographer_url`) are automatically recorded for provenance integrity.

#### 3. NASA Image & Video Library API (Scientific / Tech Topics)
- **Endpoint:** `https://images-api.nasa.gov/search?q=apollo+computer&media_type=image`
- **License Model:** Public domain (US Federal Government work).

---

### 3.2 Asset Provenance Ledger Schema Specification

The asset provenance ledger tracks the complete legal and technical lifecycle of every media file used in the video composition.

#### Schema Definition (JSON Schema Draft-07):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AssetProvenanceLedger",
  "type": "object",
  "required": [
    "schema_version",
    "project_id",
    "generated_at",
    "total_assets",
    "license_summary",
    "assets"
  ],
  "properties": {
    "schema_version": { "type": "string", "enum": ["1.0.0"] },
    "project_id": { "type": "string" },
    "generated_at": { "type": "string", "format": "date-time" },
    "total_assets": { "type": "integer", "minimum": 1 },
    "license_summary": {
      "type": "object",
      "additionalProperties": { "type": "integer" }
    },
    "assets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "asset_id",
          "claim_id_refs",
          "scene_target",
          "media_type",
          "local_path",
          "file_size_bytes",
          "file_sha256",
          "dimensions",
          "source_provider",
          "source_url",
          "license",
          "verification_status"
        ],
        "properties": {
          "asset_id": { "type": "string", "pattern": "^asset_[a-z0-9_]+$" },
          "claim_id_refs": {
            "type": "array",
            "items": { "type": "string" }
          },
          "scene_target": { "type": "string" },
          "media_type": {
            "type": "string",
            "enum": [
              "image/jpeg",
              "image/png",
              "image/webp",
              "image/svg+xml",
              "video/mp4",
              "audio/mp3",
              "audio/wav"
            ]
          },
          "local_path": { "type": "string", "description": "Relative path from project root, e.g. assets/images/transistor_1947.jpg" },
          "absolute_path": { "type": "string" },
          "file_size_bytes": { "type": "integer", "minimum": 1 },
          "file_sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
          "dimensions": {
            "type": "object",
            "required": ["width", "height", "aspect_ratio"],
            "properties": {
              "width": { "type": "integer" },
              "height": { "type": "integer" },
              "aspect_ratio": { "type": "string" }
            }
          },
          "source_provider": {
            "type": "string",
            "enum": ["wikimedia_commons", "pexels", "nasa_gov", "procedural_generator", "local_bundle"]
          },
          "source_url": { "type": "string", "format": "uri" },
          "page_url": { "type": "string" },
          "creator": {
            "type": "object",
            "required": ["name"],
            "properties": {
              "name": { "type": "string" },
              "profile_url": { "type": "string" }
            }
          },
          "license": {
            "type": "object",
            "required": [
              "license_type",
              "attribution_text",
              "attribution_required",
              "commercial_use_allowed",
              "modification_allowed"
            ],
            "properties": {
              "license_type": { "type": "string" },
              "license_url": { "type": "string" },
              "attribution_text": { "type": "string" },
              "attribution_required": { "type": "boolean" },
              "commercial_use_allowed": { "type": "boolean" },
              "modification_allowed": { "type": "boolean" }
            }
          },
          "verification_status": {
            "type": "string",
            "enum": ["VERIFIED", "FROZEN_LOCAL", "FALLBACK_GENERATED", "FAILED"]
          },
          "downloaded_at": { "type": "string", "format": "date-time" }
        }
      }
    }
  }
}
```

#### Annotated YAML Asset Ledger Example (`asset_ledger.yaml`):

```yaml
schema_version: "1.0.0"
project_id: "transistor_video_poc_2026"
generated_at: "2026-08-31T04:53:15Z"
total_assets: 3
license_summary:
  "Public Domain": 1
  "CC-BY-SA 3.0": 1
  "Pexels License": 1

assets:
  - asset_id: "asset_img_01_point_contact"
    claim_id_refs: ["claim_01"]
    scene_target: "scene_01"
    media_type: "image/jpeg"
    local_path: "assets/images/point_contact_transistor.jpg"
    absolute_path: "g:/Finding-new-code/harness9/output/transistor/assets/images/point_contact_transistor.jpg"
    file_size_bytes: 428190
    file_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    dimensions:
      width: 1920
      height: 1080
      aspect_ratio: "16:9"
    source_provider: "wikimedia_commons"
    source_url: "https://upload.wikimedia.org/wikipedia/commons/4/4c/Replica-of-first-transistor.jpg"
    page_url: "https://commons.wikimedia.org/wiki/File:Replica-of-first-transistor.jpg"
    creator:
      name: "Bell Laboratories / Nokia"
      profile_url: "https://commons.wikimedia.org/wiki/User:PublicDomain"
    license:
      license_type: "Public Domain"
      license_url: "https://creativecommons.org/publicdomain/mark/1.0/"
      attribution_text: "Replica of first transistor by Bell Labs, Public Domain via Wikimedia Commons"
      attribution_required: false
      commercial_use_allowed: true
      modification_allowed: true
    verification_status: "FROZEN_LOCAL"
    downloaded_at: "2026-08-31T04:53:10Z"

  - asset_id: "asset_img_02_inventors"
    claim_id_refs: ["claim_02"]
    scene_target: "scene_02"
    media_type: "image/jpeg"
    local_path: "assets/images/bardeen_brattain_shockley.jpg"
    absolute_path: "g:/Finding-new-code/harness9/output/transistor/assets/images/bardeen_brattain_shockley.jpg"
    file_size_bytes: 561204
    file_sha256: "f4a1c54298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b999"
    dimensions:
      width: 1920
      height: 1080
      aspect_ratio: "16:9"
    source_provider: "wikimedia_commons"
    source_url: "https://upload.wikimedia.org/wikipedia/commons/b/b2/Bardeen_Brattain_Shockley_1948.jpg"
    page_url: "https://commons.wikimedia.org/wiki/File:Bardeen_Brattain_Shockley_1948.jpg"
    creator:
      name: "AT&T Technologies, Inc."
      profile_url: "https://commons.wikimedia.org"
    license:
      license_type: "CC-BY-SA 3.0"
      license_url: "https://creativecommons.org/licenses/by-sa/3.0/"
      attribution_text: "Photo of Bardeen, Brattain, Shockley (1948) by AT&T under CC-BY-SA 3.0"
      attribution_required: true
      commercial_use_allowed: true
      modification_allowed: true
    verification_status: "FROZEN_LOCAL"
    downloaded_at: "2026-08-31T04:53:12Z"

  - asset_id: "asset_img_03_modern_silicon"
    claim_id_refs: ["claim_04"]
    scene_target: "scene_03"
    media_type: "image/jpeg"
    local_path: "assets/images/modern_silicon_wafer.jpg"
    absolute_path: "g:/Finding-new-code/harness9/output/transistor/assets/images/modern_silicon_wafer.jpg"
    file_size_bytes: 842100
    file_sha256: "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0"
    dimensions:
      width: 1920
      height: 1080
      aspect_ratio: "16:9"
    source_provider: "pexels"
    source_url: "https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg"
    page_url: "https://www.pexels.com/photo/close-up-of-microchip-2582937/"
    creator:
      name: "Alexandre Debiève"
      profile_url: "https://www.pexels.com/@alexandre-debieve"
    license:
      license_type: "Pexels License"
      license_url: "https://www.pexels.com/license/"
      attribution_text: "Photo by Alexandre Debiève on Pexels"
      attribution_required: false
      commercial_use_allowed: true
      modification_allowed: true
    verification_status: "FROZEN_LOCAL"
    downloaded_at: "2026-08-31T04:53:14Z"
```

---

### 3.3 Local Asset Freezing Pipeline

The **Asset Freezing Pipeline** guarantees that rendering engines never experience missing assets, broken paths, or network jitter.

```
+-----------------------------------------------------------------------------------+
|                        ASSET FREEZING 5-STAGE PIPELINE                            |
+-----------------------------------------------------------------------------------+

 [Candidate Asset URL]
         |
         v
 [Stage 1: Streaming Download] ---> Cap max size (25MB), enforce connection timeout
         |
         v
 [Stage 2: Magic Byte & MIME Check] ---> Verify binary signatures (JPEG, PNG, WebP, SVG)
         |
         v
 [Stage 3: SHA-256 Checksum] ---> Compute deterministic content digest
         |
         v
 [Stage 4: Relative Path Placement] ---> Write to project './assets/images/{slug}.{ext}'
         |
         v
 [Stage 5: Composition Audit Gate] ---> Verify HTML/CSS/GSAP composition references
                                         strictly resolve to frozen local paths
```

#### Magic Byte Sniffing Signatures:
- **JPEG:** Starts with `FF D8 FF`
- **PNG:** Starts with `89 50 4E 47 0D 0A 1A 0A`
- **WebP:** Starts with `52 49 46 46` ... `57 45 42 50` (`RIFF....WEBP`)
- **SVG:** XML/text containing `<svg` root element.
- **MP4:** Starts with `00 00 00 .. 66 74 79 70` (`ftyp`)

#### Composition Relative Path Audit Rule:
Before HyperFrames rendering initiates, the validator runs an AST / regex check over all project HTML files (`index.html`, `compositions/*.html`):
- Any `src="http://..."` or `src="https://..."` triggers a **FATAL_EXTERNAL_URL_IN_COMPOSITION** lint failure.
- Every `src="assets/..."` is verified with `os.path.exists(os.path.join(project_dir, src_path))`.
- If missing, rendering is blocked and fallback resolution is triggered.

---

### 3.4 Deterministic Offline Asset Fallback Subsystem

When the pipeline runs in `--offline` mode or without external image API credentials, the fallback subsystem ensures complete, gorgeous visual assets are generated locally with zero network access.

```
+-----------------------------------------------------------------------------------+
|                        OFFLINE ASSET GENERATION MODES                             |
+-----------------------------------------------------------------------------------+

 1. Bundled High-Res Sample Assets:
    - Pre-packaged CC0 reference images in 'assets/samples/' for benchmark topics.

 2. Dynamic Procedural SVG Vector Generator:
    - Synthesizes 1920x1080 SVG graphics tailored to the topic.
    - Uses technical grids, stylized circuit traces, silicon chip iconography, and
      modern dark-mode gradients adhering to 'DESIGN.md'.
    - Fully scalable, zero artifacts, renders at 60 FPS in Chromium headless.

 3. Structured Visual Typographic Cards:
    - Beautiful typographic hero slides with gradient borders, claim badges,
      and metric callouts rendered as standalone SVG/HTML elements.
```

#### Example Procedural SVG Generation Algorithm (Technical / Semiconductor Motif):

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0e17"/>
      <stop offset="100%" stop-color="#141d2e"/>
    </linearGradient>
    <linearGradient id="cyanGlow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00f2fe"/>
      <stop offset="100%" stop-color="#4facfe"/>
    </linearGradient>
  </defs>
  
  <!-- Background Canvas -->
  <rect width="1920" height="1080" fill="url(#bgGrad)"/>
  
  <!-- Technical Grid Overlay -->
  <g opacity="0.12" stroke="#4facfe" stroke-width="1">
    <path d="M0,180 H1920 M0,360 H1920 M0,540 H1920 M0,720 H1920 M0,900 H1920"/>
    <path d="M320,0 V1080 M640,0 V1080 M960,0 V1080 M1280,0 V1080 M1600,0 V1080"/>
  </g>
  
  <!-- Central Semiconductor Motif -->
  <rect x="760" y="340" width="400" height="400" rx="32" fill="#111c2e" stroke="url(#cyanGlow)" stroke-width="4"/>
  <circle cx="960" cy="540" r="120" fill="none" stroke="#00f2fe" stroke-width="2" opacity="0.6"/>
  
  <!-- Circuit Traces -->
  <path d="M760,440 H600 V300 H400" stroke="#00f2fe" stroke-width="3" fill="none" opacity="0.7"/>
  <path d="M1160,440 H1320 V300 H1520" stroke="#00f2fe" stroke-width="3" fill="none" opacity="0.7"/>
  <path d="M960,740 V900 H1200" stroke="#4facfe" stroke-width="3" fill="none" opacity="0.7"/>

  <!-- Content Badges -->
  <text x="960" y="550" font-family="Inter, sans-serif" font-size="28" font-weight="700" fill="#ffffff" text-anchor="middle">
    POINT-CONTACT TRANSISTOR 1947
  </text>
</svg>
```

---

## 4. Integration Interfaces & Downstream Contracts

### 4.1 Interface Contract: R1 -> R3 (Script & Voiceover Generator)
- **Input to R3:** `research_dossier.yaml` (or `.json`).
- **Data consumed by R3:**
  - `talking_points`: Direct blueprint for video scenes and script beats.
  - `claims`: Source facts embedded into voiceover narration and timestamped audio cues.
  - `statistics`: Numbers formatted for on-screen lower thirds and kinetic typography.
  - `metadata.target_duration_seconds`: Enforces strict word-count budget (approx. 2.5 words per second).

### 4.2 Interface Contract: R2 -> R4 (HyperFrames Composition & Video Render)
- **Input to R4:** `asset_ledger.yaml` + `./assets/` directory.
- **Data consumed by R4:**
  - `local_path`: Injected into `<img src="assets/...">` or `<video src="assets/...">`.
  - `dimensions`: Used to calculate responsive aspect-ratio containment (`object-fit: cover`).
  - `license.attribution_text`: Injected into end-screen credits or lower-third attribution tags.
  - `verification_status`: Checked before render; non-`FROZEN_LOCAL` or non-`FALLBACK_GENERATED` assets abort the build.

### 4.3 Interface Contract: R1 + R2 -> R5 (End-to-End Orchestrator CLI)
- Unified CLI Runner (`hermes-video` / `pipeline_runner.py`) orchestrates execution:
  ```bash
  # Standard Online Execution
  python pipeline_runner.py --topic "The History of the Transistor" --output-dir ./dist/transistor

  # 100% Hermetic / Offline Test Execution
  python pipeline_runner.py --topic "The History of the Transistor" --offline --output-dir ./dist/transistor_offline
  ```

---

## 5. Verification & Testing Matrix

| Test ID | Module | Category | Test Case Description | Expected Result |
|---|---|---|---|---|
| **T-R1-01** | R1 | Schema Validation | Validate synthesized dossier against JSON Schema | Passes 100% schema checks with zero validation errors |
| **T-R1-02** | R1 | Offline Fallback | Run research engine with `--offline` for arbitrary topic | Returns valid dossier with $\ge 3$ claims and talking points |
| **T-R1-03** | R1 | Confidence Scorer | Verify confidence scoring with authoritative vs untrusted sources | Higher scores assigned to primary archives |
| **T-R2-01** | R2 | Wikimedia Parsing | Parse mock/live Wikimedia API response | Correctly extracts URL, author, and CC license |
| **T-R2-02** | R2 | Magic Byte Sniff | Verify integrity checker rejects corrupt or mismatched image bytes | Throws `InvalidImageBinary` and triggers fallback |
| **T-R2-03** | R2 | Asset Freezing | Download media and verify SHA-256 and local file placement | Checksum matches byte stream, local file exists on disk |
| **T-R2-04** | R2 | Path Isolation | Audit HTML composition for zero external `http://` URLs | Passes zero-network audit check |
| **T-R2-05** | R2 | Offline SVG Gen | Generate procedural SVG assets in offline mode | Produces valid 1920x1080 SVG files with `CC0` ledger entries |
| **T-E2E-01**| R1+R2 | Full Stage Run | Run R1 & R2 sequentially from CLI | Produces `research_dossier.yaml`, `asset_ledger.yaml`, and frozen `./assets/` |

---

## 6. Implementation Blueprint & File Layout

When transitioning to Milestone implementation, the following module structure is recommended:

```
src/
├── research/
│   ├── __init__.py
│   ├── engine.py             # ResearchEngine coordinator
│   ├── query_expander.py     # Multi-intent query generator
│   ├── search_clients.py     # Tavily/Exa/Firecrawl web search adapters
│   ├── confidence.py         # Claim scoring heuristics
│   ├── dossier_schema.py     # Pydantic / dataclass schema definitions
│   └── offline_fallback.py   # Curated presets & procedural topic synthesizer
│
├── assets/
│   ├── __init__.py
│   ├── discovery.py          # Media search coordinator
│   ├── wikimedia.py          # Wikimedia Commons API client
│   ├── pexels.py             # Pexels API client
│   ├── ledger_schema.py      # Asset ledger schema definitions
│   ├── freezer.py            # Download, integrity verification & SHA-256
│   └── procedural_svg.py     # Deterministic offline SVG & canvas generator
│
└── presets/
    ├── dossiers/             # Pre-baked YAML dossiers for benchmark topics
    └── assets/               # Bundled sample media packs
```

---
*Report completed and verified by `explorer_research_assets_0`.*
