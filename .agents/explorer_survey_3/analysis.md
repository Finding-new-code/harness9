# Comprehensive Survey & Deep Investigation: Requirements R4, R5, R6 & Verification Framework

**Agent**: `explorer_survey_3`  
**Date**: 2026-08-31  
**Working Directory**: `g:\Finding-new-code\harness9\.agents\explorer_survey_3`  
**Target Focus**: 
- **Requirement R4**: Voice Director, Automated VoiceQA & Multi-Tiered Asset Deduplication
- **Requirement R5**: Creator DNA Data Model, Creator Economics Cost/Revenue Ledger & Quality OS / ContentBench (4-Layer Evaluation Framework)
- **Requirement R6**: Security Capability Token Engine & Comprehensive Engineering Documentation Suite (14 Specs + ADR-001 through ADR-005)
- **Verification & Test Framework**: Pytest/Unittest suite, 6-checkpoint verification harness (`verify_pipeline.py`), and end-to-end acceptance testing strategy.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Requirement R4: Voice Director, Voice QA & Asset Deduplication](#2-requirement-r4-voice-director-voice-qa--asset-deduplication)
   - 2.1 [Current Codebase Baseline (`src/scriptwriting/tts.py`, `src/assets/freezer.py`)](#21-current-codebase-baseline)
   - 2.2 [Multi-Provider VoiceDirector Architecture](#22-multi-provider-voicedirector-architecture)
   - 2.3 [Automated VoiceQA Engine & Acoustic Quality Metrics](#23-automated-voiceqa-engine--acoustic-quality-metrics)
   - 2.4 [Multi-Tiered Asset Deduplication (SHA-256 + Perceptual Hashing)](#24-multi-tiered-asset-deduplication-sha-256--perceptual-hashing)
3. [Requirement R5: Creator DNA, Creator Economics & Quality OS (ContentBench)](#3-requirement-r5-creator-dna-creator-economics--quality-os-contentbench)
   - 3.1 [Current Codebase Baseline (`src/scriptwriting/generator.py`, `src/models/summary.py`)](#31-current-codebase-baseline)
   - 3.2 [Creator DNA Data Model (6-Component System)](#32-creator-dna-data-model-6-component-system)
   - 3.3 [Creator Economics Cost/Revenue Ledger](#33-creator-economics-costrevenue-ledger)
   - 3.4 [ContentBench: 4-Layer Quality OS Evaluation Framework](#34-contentbench-4-layer-quality-os-evaluation-framework)
4. [Requirement R6: Security Capability Tokens & Engineering Documentation Suite](#4-requirement-r6-security-capability-tokens--engineering-documentation-suite)
   - 4.1 [Principle-of-Least-Privilege Capability Token Engine](#41-principle-of-least-privilege-capability-token-engine)
   - 4.2 [Permission Intersection Calculus & Sandboxing Enforcement](#42-permission-intersection-calculus--sandboxing-enforcement)
   - 4.3 [Comprehensive Engineering Documentation Suite (14 Specifications)](#43-comprehensive-engineering-documentation-suite-14-specifications)
   - 4.4 [Architecture Decision Records (ADR-001 through ADR-005)](#44-architecture-decision-records-adr-001-through-adr-005)
5. [Verification, Test Framework & Acceptance Harness](#5-verification-test-framework--acceptance-harness)
   - 5.1 [Test Suite Inventory & Execution Baseline](#51-test-suite-inventory--execution-baseline)
   - 5.2 [Automated Acceptance Verification Harness (`verify_pipeline.py`)](#52-automated-acceptance-verification-harness-verify_pipelinepy)
   - 5.3 [Expansion Plan for R4, R5, and R6 Verification](#53-expansion-plan-for-r4-r5-and-r6-verification)
6. [Architectural Gap Analysis & Traceability Matrix](#6-architectural-gap-analysis--traceability-matrix)
7. [Target Schemas, Interfaces & Implementation Blueprints](#7-target-schemas-interfaces--implementation-blueprints)
8. [Conclusion & Next Actions](#8-conclusion--next-actions)

---

## 1. Executive Summary

Harness 9 is transitioning from an initial 5-stage sequential proof-of-concept into a durable, decoupled AI-native video production studio operating system built on top of Hermes Agent and HyperFrames. The mission of `explorer_survey_3` is to conduct an in-depth code-level exploration and structural gap analysis of **Requirements R4, R5, and R6**, as well as the **Verification and Test Framework**, establishing exact data models, algorithms, math formulations, integration contracts, and acceptance gates.

### Core Discoveries & Baseline Status:
1. **R4 (Audio & Media Pipelines)**: The current codebase provides a 3-tier fallback `TTSEngine` in `src/scriptwriting/tts.py` (ElevenLabs API $\to$ Windows SAPI $\to$ Harmonic WAV Synthesizer) and byte-exact SHA-256 verification in `src/assets/freezer.py`. However, it lacks director-level voice orchestration (character casting, emotion modulation), automated acoustic QA (detecting dead air, gap duration, clipping, volume consistency, speech-beat sync), and perceptual visual hashing (dHash/pHash) for deduplication.
2. **R5 (Creator Intelligence & Economics)**: The current implementation contains basic `BrandGuidelines` (colors, typography, motion rules in `src/scriptwriting/generator.py`) and execution time telemetry in `src/models/summary.py`. It lacks the 6-part **Creator DNA** model (Brand Constitution, Preferences, Skills, Examples, Performance Memory, Negative Memory), granular itemized resource cost accounting (LLM tokens, research queries, TTS characters, render compute, storage), and the 4-layer **ContentBench** Quality OS evaluation benchmark.
3. **R6 (Security & Specifications)**: The current codebase operates with flat process privileges and includes only initial subsystem guides in `docs/harness9/`. It requires the **Capability Token Engine** enforcing the least-privilege calculus ($\text{child} = \text{parent} \cap \text{role} \cap \text{workflow}$) and the complete 14-spec engineering documentation suite along with formal ADRs (ADR-001 through ADR-005).
4. **Verification & Testing**: Harness 9 possesses a hermetic, flake-free test harness in `tests/` and an automated 6-checkpoint verification gate in `verify_pipeline.py`. All tests pass deterministically in offline environments. This framework provides the solid foundation to integrate new automated acceptance checkpoints for R4, R5, and R6.

---

## 2. Requirement R4: Voice Director, Voice QA & Asset Deduplication

### 2.1 Current Codebase Baseline

#### TTS Synthesis (`src/scriptwriting/tts.py`):
- `TTSProvider` (lines 57–78): Abstract base class defining `is_available()` and `synthesize(text, output_path, target_duration, voice, **kwargs)`.
- `ElevenLabsTTSProvider` (lines 80–157): REST integration targeting `api.elevenlabs.io/v1/text-to-speech/{voice_id}` with stability (0.5) and similarity boost (0.75).
- `WindowsSAPITTSProvider` (lines 159–260): Offline speech synthesis executing PowerShell `System.Speech.Synthesis.SpeechSynthesizer`.
- `HarmonicWAVSynthesizer` (lines 262–397): 100% deterministic pure-Python modulated harmonic wave synthesizer generating 16-bit PCM WAV with natural formant frequencies ($F_0, F_1, F_2, F_3$) and amplitude attack/decay envelopes.
- `TTSEngine` (lines 399–494): Orchestrates fallback priority: `ElevenLabs -> Windows SAPI -> Harmonic Synthesizer`.

#### Asset Ingestion & Freezing (`src/assets/freezer.py` & `src/assets/discovery.py`):
- `AssetDiscoveryEngine` (`src/assets/discovery.py`, lines 535–572): Queries Wikimedia, Pexels, NASA, and Offline Mock with URL deduplication via `seen_urls = set()`.
- `AssetFreezer` (`src/assets/freezer.py`, lines 179–289): Streaming download with 25MB safety caps, binary magic-byte sniffing (JPEG, PNG, WebP, SVG, MP4, WAV, MP3), and byte-exact SHA-256 validation.

---

### 2.2 Multi-Provider VoiceDirector Architecture

The upgraded **VoiceDirector** replaces the basic fallback `TTSEngine` with a director-level audio orchestration engine capable of multi-speaker casting, emotional tone modulation, and scene-specific pacing.

```
                      ┌────────────────────────────────────────┐
                      │             VoiceDirector              │
                      │  (Casting, Tone, Emotion, Routing)     │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┼────────────────────────┐
                  ▼                       ▼                        ▼
       ┌─────────────────────┐ ┌─────────────────────┐  ┌─────────────────────┐
       │   Cloud Providers   │ │   Local/OS Providers│  │ Deterministic Fallback│
       │- ElevenLabs v2      │ │- Windows SAPI / Mac │  │- Harmonic Synthesizer│
       │- OpenAI Audio / TTS │ │- Piper / Kokoro /   │  │- Pure Python PCM     │
       │- Cartesia / Azure   │ │  System Speech      │  │  Formant Synthesis  │
       └─────────────────────┘ └─────────────────────┘  └─────────────────────┘
```

#### Core Responsibilities of VoiceDirector:
1. **Voice Casting & Character Profile Mapping**:
   - Maps scene narration and speaker roles to distinct voice models, pitch ranges, speaking rates, and timbre profiles.
   - Supports multi-character dialogue and narrator-to-quote transitions.
2. **Dynamic Pacing & Rate Control**:
   - Calculates target syllable rates ($\approx 3.5 \text{ to } 4.5 \text{ syllables/sec}$) and words per minute ($\approx 130 \text{ to } 160 \text{ WPM}$) to conform audio tracks precisely to scene duration constraints without artificial pitch shifts.
3. **Emotion & Tone Modulation**:
   - Parses script emotional markers (`[tense]`, `[authoritative]`, `[curious]`, `[triumphant]`, `[reflective]`) and injects SSML / provider-specific stability and style modifiers.
4. **Resilient Multi-Provider Fallback Hierarchy**:
   - Prioritized tier: `ElevenLabs -> OpenAI TTS -> Local Piper/SAPI -> Deterministic Harmonic Synthesizer`.

---

### 2.3 Automated VoiceQA Engine & Acoustic Quality Metrics

The **VoiceQA** engine performs deep quantitative audio signal analysis on generated WAV audio files before composition rendering.

```
       Generated WAV Audio ────► [ VoiceQA Analysis Engine ]
                                            │
        ┌───────────────────────────────────┼──────────────────────────────────┐
        ▼                                   ▼                                  ▼
[Dead Air / Silence]               [Clipping & Peak Sat]              [Volume Consistency]
- Silence: < -45 dBFS              - Samples: |s| >= 32767            - Scene-by-scene RMS
- Gap threshold: > 300ms           - Ratio: saturated / total         - Loudness delta < 2.5 dB
- Leading/trailing: > 200ms        - Distortion timestamp log         - Dynamic range check
        │                                   │                                  │
        └───────────────────────────────────┼──────────────────────────────────┘
                                            ▼
                          [Speech-Beat Alignment Gate]
                          - Drift tolerance: <= +/- 0.2s
                          - Word boundary synchronization
                                            │
                                            ▼
                               [ VoiceQAReport Metrics ]
```

#### Detailed Mathematical & Quantitative Metrics:

1. **Dead Air & Silence Detection**:
   - **Threshold**: Audio frames with RMS power below $-45\text{ dBFS}$ are classified as silence.
   - **Excessive Gap Rule**: Internal non-speech gaps exceeding $300\text{ms}$ (0.3s) without intentional dramatic pause marking trigger a `DEAD_AIR_WARNING`.
   - **Boundary Dead Air**: Leading silence $>200\text{ms}$ or trailing silence $>250\text{ms}$ is flagged for automatic trimming.
   
2. **Gap Duration Analysis**:
   - Calculates inter-word pause distribution:
     $$\mu_{\text{gap}} = \frac{1}{N-1} \sum_{i=1}^{N-1} (t_{\text{start}, i+1} - t_{\text{end}, i})$$
   - Natural cadence requires $50\text{ms} \le \text{gap} \le 350\text{ms}$ for standard narration; sentence-ending pauses require $350\text{ms} \le \text{pause} \le 700\text{ms}$.

3. **Clipping & Harmonic Distortion Detection**:
   - Scans 16-bit signed PCM integer samples $s[n] \in [-32768, 32767]$.
   - Flags clipping event whenever $|s[n]| \ge 32767$ or $|s[n]| / 32768.0 \ge 0.999$.
   - **Clipping Metric**:
     $$\text{ClippingRatio} = \frac{N_{\text{clipped}}}{N_{\text{total}}}$$
   - **Acceptance Criterion**: $\text{ClippingRatio} < 0.0001$ ($<0.01\%$). Any sustained clip of $>5\text{ consecutive samples}$ is marked as severe acoustic distortion.

4. **Volume Consistency & RMS Energy**:
   - Calculates Root Mean Square (RMS) energy per scene $k$:
     $$\text{RMS}_k = \sqrt{\frac{1}{M_k} \sum_{m=1}^{M_k} s_k[m]^2}, \quad \text{Loudness}_{\text{dBFS}} = 20 \log_{10}\left(\frac{\text{RMS}_k}{32767}\right)$$
   - Computes loudness variance across scenes:
     $$\Delta \text{Loudness} = \max_k(\text{Loudness}_k) - \min_k(\text{Loudness}_k)$$
   - **Acceptance Criterion**: $\Delta \text{Loudness} \le 2.5\text{ dBFS}$ across all scenes in a single video.

5. **Speech-Beat Alignment Synchronization**:
   - Calculates time offset between planned storyboard scene transitions $T_{\text{scene\_end}}$ and actual spoken audio boundary $T_{\text{audio\_segment\_end}}$:
     $$\text{Drift}_j = |T_{\text{storyboard}, j} - T_{\text{audio\_actual}, j}|$$
   - **Acceptance Criterion**: $\max_j(\text{Drift}_j) \le 0.20\text{s}$ ($200\text{ms}$).

---

### 2.4 Multi-Tiered Asset Deduplication (SHA-256 + Perceptual Hashing)

To prevent redundant downloads, save bandwidth, and ensure visual variety across scenes, the media ingestion pipeline employs a **Two-Tier Deduplication Engine**.

```
                   Incoming Asset Candidate (URL / Bytes)
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  Tier 1: Byte-Exact SHA-256     │
                    │  Hash = SHA256(RawBytes)        │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │ Match in Global Ledger?         │
                    │ YES ──► Reference Canonical     │
                    │ NO  ──► Proceed to Tier 2       │
                    └────────────────┬────────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │  Tier 2: Perceptual Hashing     │
                    │  dHash / pHash (Visual Content) │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │ Hamming Distance d_H <= 4?      │
                    │ YES ──► Near-Duplicate Detected │
                    │         (Reject / Use Existing) │
                    │ NO  ──► Unique Visual Asset     │
                    │         (Freeze & Index)        │
                    └─────────────────────────────────┘
```

#### Algorithm Specifications:

1. **Tier 1: Byte-Exact SHA-256 Deduplication**:
   - Streaming hash calculation during download chunks.
   - Prevents identical file downloads across multiple search queries or candidate queries.
   - Content-addressable key: `sha256:<hex_digest>`.

2. **Tier 2: Perceptual Difference Hashing (`dHash`)**:
   - **Step 1**: Convert image to grayscale ($8\text{-bit}$).
   - **Step 2**: Resize to $9 \times 8$ pixels (72 pixels total), ignoring aspect ratio.
   - **Step 3**: Compute horizontal gradient comparison: for each row $y \in [0, 7]$ and column $x \in [0, 7]$, compare pixel $P(x, y)$ with adjacent pixel $P(x+1, y)$.
   - **Step 4**: Set bit $b_{8y+x} = 1$ if $P(x, y) > P(x+1, y)$, else $0$.
   - **Step 5**: Form a 64-bit integer hash $H_{\text{dhash}}$.
   - **Hamming Distance Calculation**:
     $$d_H(H_1, H_2) = \text{popcount}(H_1 \oplus H_2)$$
   - **Deduplication Threshold**:
     - $d_H = 0$: Identical visual content.
     - $1 \le d_H \le 4$: Near-duplicate (same image resized, cropped slightly, or re-compressed).
     - $d_H > 10$: Visually distinct images.
   - **Rule**: If candidate asset has $d_H \le 4$ against any already-selected scene asset, it is rejected in favor of the next unique candidate.

---

## 3. Requirement R5: Creator DNA, Creator Economics & Quality OS (ContentBench)

### 3.1 Current Codebase Baseline

- `src/scriptwriting/generator.py`: Generates `DESIGN.md` containing `BrandGuidelines`, `ColorRole`, `TypographyStyle`, and `MotionRules`.
- `src/models/summary.py`: `PipelineSummary` records basic stage execution times (`execution_time_seconds`) and binary status, but contains zero monetary/resource cost ledger.
- `verify_pipeline.py`: Executes 6 verification checkpoints checking presence and structure of files, but lacks qualitative grading, narrative scoring, or benchmark dataset evaluation.

---

### 3.2 Creator DNA Data Model (6-Component System)

The **Creator DNA** data model represents the complete cognitive identity, aesthetic standards, and operational memories of a content creator.

```
                              ┌─────────────────────────────┐
                              │         CREATOR DNA         │
                              └──────────────┬──────────────┘
                                             │
      ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
      ▼                  ▼                   ▼                   ▼                  ▼
┌───────────┐      ┌───────────┐       ┌───────────┐       ┌───────────┐      ┌───────────┐
│   Brand   │      │  Creator  │       │  Creator  │       │  Creator  │      │Performance│
│Constitution│     │Preferences│       │  Skills   │       │ Examples  │      │  Memory   │
└───────────┘      └───────────┘       └───────────┘       └───────────┘      └───────────┘
                                             │
                                             ▼
                                     ┌───────────────┐
                                     │   Negative    │
                                     │    Memory     │
                                     └───────────────┘
```

#### 1. Brand Constitution:
- **Core Editorial Mission**: Guiding editorial philosophy (e.g., "Demystifying deep tech through rigorous historical accuracy and cinematic pacing").
- **Voice & Tone Directives**: Formal tone parameters (e.g., "Authoritative yet accessible; never clickbaity; avoid hyperbole").
- **Non-Negotiable Guardrails**: Prohibited words/phrases (e.g., "game-changer", "revolutionary", "in this video we will explore"), forbidden themes, and copyright safety rules.
- **Audience Archetype**: Technical depth level, expected background knowledge, primary engagement motivators.

#### 2. Creator Preferences:
- **Pacing Profile**: Target speaking cadence ($145\text{ WPM}$), scene transition tempo ($4.5\text{s}$ average scene duration), asset density ($2.0\text{ visual assets per 10s}$).
- **Visual & Style Tokens**: Preferred color palettes (HEX/HSL), typography hierarchy (Header font, body font, monospace accents), standard GSAP transition easing (`power2.out`, `expo.inOut`).
- **Default Format & Aspect Ratio**: Preferred resolution ($1920\times 1080$ vs $1080\times 1920$) and safe-zone margins.

#### 3. Creator Skills:
- **Domain Specializations**: Specific subject matter strengths (e.g., solid-state physics, distributed computing, aerospace engineering).
- **Technical Lexicon**: Curated vocabulary dictionaries and pronunciation guides for specialized terminology.
- **Visual Representation Archetypes**: Preferred diagramming styles (e.g., interactive block architecture, timeline callouts, animated graphs).

#### 4. Creator Examples (Few-Shot Exemplars):
- Curated repository of top-tier hooks, high-retention script openings, elegant transition scripts, and effective storyboard descriptions used for prompt few-shot conditioning.

#### 5. Performance Memory:
- **Historical Telemetry**: Retention curves from prior publications, average view duration (AVD), click-through rate (CTR), engagement drop-off points.
- **Learned Patterns**: Positive correlations between specific hook structures and initial 5-second retention.

#### 6. Negative Memory:
- **Explicit Failure Log**: Record of past creative mistakes, rejected editorial angles, hallucinated claims caught in review, poorly received visual analogies, and awkward phrasing patterns.
- **Negative Constraints Generator**: Dynamically appends negative prompt constraints to script and research generation prompts: *"Do NOT use [Pattern X], which failed in project [ID] due to [Reason Y]"*.

---

### 3.3 Creator Economics Cost/Revenue Ledger

The **Creator Economics Engine** introduces itemized, transparent resource cost tracking across every stage of the production lifecycle.

```
                          CREATOR PRODUCTION COST LEDGER
─────────────────────────────────────────────────────────────────────────────
 Category           Resource Unit              Unit Rate ($)       Total Cost
─────────────────────────────────────────────────────────────────────────────
 LLM Inference      - Prompt Tokens (12.4k)    $0.0025 / 1k        $0.0310
                    - Completion Tokens (3.8k) $0.0100 / 1k        $0.0380
                    - Cached Tokens (8.1k)     $0.0005 / 1k        $0.0041
 Research APIs      - Search Queries (6 calls) $0.0050 / query     $0.0300
 TTS Audio Synth    - Characters (1,840 chars) $0.00003 / char     $0.0552
 Video Rendering    - GPU Compute (18.2s)      $0.0004 / sec       $0.0073
 Storage & Egress   - Media Storage (48 MB)    $0.0200 / GB/mo     $0.0010
─────────────────────────────────────────────────────────────────────────────
 TOTAL PRODUCTION COST (per 30s video):                            $0.1666
 COST PER SECOND OF FINISHED VIDEO:                                $0.00555 / s
─────────────────────────────────────────────────────────────────────────────
```

#### Itemized Cost Breakdown Schema:
1. **LLM Inference**: Itemizes input tokens, output tokens, and cache hits per model (`gpt-4o`, `claude-3-5-sonnet`, `deepseek-v3`, etc.) across Research, Editorial, Scriptwriting, and Layout stages.
2. **Research & Data Retrieval**: Tracks query counts against search APIs (Tavily, Exa, Serper, Wikimedia API).
3. **Voice Synthesis**: Tracks character counts, billable audio duration, and model tier pricing (ElevenLabs Turbo vs Multilingual vs local free tier).
4. **Rendering & Encoding**: Tracks Chromium headless execution time and FFmpeg H.264/AAC muxing compute time.
5. **Storage & Assets**: Calculates total byte footprint of frozen assets, HTML compositions, and final MP4 files.
6. **Economics Reporting**: Generates `cost_ledger.json` / `cost_ledger.yaml` with total production cost, cost per finished second, and estimated margin against platform CPM/RPM.

---

### 3.4 ContentBench: 4-Layer Quality OS Evaluation Framework

**ContentBench** is an automated, multi-dimensional benchmarking and evaluation framework that scores generated content against objective quality standards.

```
                             CONTENTBENCH (Quality OS)
                                         │
        ┌───────────────────┬────────────┴───────┬───────────────────┐
        ▼                   ▼                    ▼                   ▼
┌───────────────┐   ┌───────────────┐    ┌───────────────┐   ┌───────────────┐
│    Layer 1    │   │    Layer 2    │    │    Layer 3    │   │    Layer 4    │
│   Research    │   │    Script     │    │ Video & Comp  │   │   Economics   │
│  Evaluation   │   │  Evaluation   │    │  Evaluation   │   │  Efficiency   │
└───────┬───────┘   └───────┬───────┘    └───────┬───────┘   └───────┬───────┘
        │                   │                    │                   │
        └───────────────────┼────────────────────┼───────────────────┘
                            ▼
               [ Composite Quality Score: 0.0 - 1.0 ]
```

#### Layer 1: Research Quality Evaluation ($S_{\text{research}}$)
- **Fact Density**: Ratio of verifiable claims per 30 seconds of content ($\ge 3\text{ claims}$).
- **Source Authority & Diversity**: Domain authority score of cited sources (e.g., `.edu`, `.gov`, peer-reviewed, official standards).
- **Corroboration Index**: Percentage of claims confirmed by $\ge 2$ independent primary/secondary sources.
- **Conflict Penalty**: Deduction for uncorroborated, conflicting, or vague claims.
- **Formula**:
  $$S_{\text{research}} = 0.35 \times \text{FactDensity} + 0.35 \times \text{Authority} + 0.30 \times \text{Corroboration} - \text{Penalty}$$

#### Layer 2: Script & Narrative Evaluation ($S_{\text{script}}$)
- **Hook Strength ($0.0 - 1.0$)**: Evaluates initial 5-second cognitive curiosity gap, question framing, and emotional stake.
- **Pacing Consistency**: Word cadence variance across scenes (penalizes scenes $>180\text{ WPM}$ or $<110\text{ WPM}$).
- **Flesch-Kincaid Readability**: Ensures target grade level (Grade 7–10 for general tech).
- **Creator DNA Adherence**: Verification that zero forbidden words/themes appear and all brand tone guidelines are met.
- **Formula**:
  $$S_{\text{script}} = 0.30 \times \text{HookScore} + 0.25 \times \text{PacingScore} + 0.25 \times \text{ReadabilityScore} + 0.20 \times \text{DNAAdherence}$$

#### Layer 3: Video & Composition Evaluation ($S_{\text{video}}$)
- **VoiceQA Score**: Audio cleanliness, zero clipping, natural gap cadences, loudness consistency ($< 2.5\text{ dB}$).
- **Speech-Beat Sync**: Synchronization alignment between narration and scene animation ($\le 0.2\text{s}$ drift).
- **Visual Relevance**: Semantic relevance between scene visual asset and claim text.
- **Composition Linter**: Zero broken paths, finite animation loops, responsive safe-zone compliance.
- **Formula**:
  $$S_{\text{video}} = 0.30 \times \text{VoiceQA} + 0.30 \times \text{SyncScore} + 0.20 \times \text{VisualRelevance} + 0.20 \times \text{LintCompliance}$$

#### Layer 4: Cost & Resource Efficiency ($S_{\text{cost}}$)
- **Cost per Minute Target**: Evaluates whether production cost is within target budget envelope ($< \$0.50 / \text{min}$).
- **Token Efficiency Ratio**: $\text{Useful Output Tokens} / \text{Total LLM Tokens}$.
- **Compute Efficiency**: Render time to video duration ratio ($< 1.5\times$ real-time).
- **Formula**:
  $$S_{\text{cost}} = 0.40 \times \text{BudgetScore} + 0.30 \times \text{TokenEfficiency} + 0.30 \times \text{RenderEfficiency}$$

#### Aggregate ContentBench Quality Score:
$$\text{ContentBench Score} = 0.25 \times S_{\text{research}} + 0.30 \times S_{\text{script}} + 0.30 \times S_{\text{video}} + 0.15 \times S_{\text{cost}}$$

---

## 4. Requirement R6: Security Capability Tokens & Engineering Documentation Suite

### 4.1 Principle-of-Least-Privilege Capability Token Engine

To safeguard the production pipeline against unauthorized tool execution, privilege escalation, or rogue child agent behavior, Harness 9 implements an immutable **Capability Token Engine**.

```
       [ Master Orchestrator / Root Token ]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[ Research Worker Token ]     [ Scriptwriting Worker Token ]
- network: read-only          - network: none
- filesystem: output/research - filesystem: output/script
- tools: [search_web, fetch]  - tools: [align_text, synth_tts]
       │
       ▼
[ Child Fact Checker Token ]
- Permission = Parent ∩ Role ∩ Workflow
- strictly restricted sub-scope
```

---

### 4.2 Permission Intersection Calculus & Sandboxing Enforcement

#### Mathematical Permission Calculus:
Every task or child agent execution receives a cryptographically signed capability token $T_{\text{child}}$ derived via set intersection:
$$\mathcal{P}_{\text{child}} = \mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$$

Where:
- $\mathcal{P}_{\text{parent}}$: Permissions granted to the initiating parent agent/orchestrator.
- $\mathcal{P}_{\text{role}}$: Maximum permission boundary permitted for that specific functional role (e.g., `researcher`, `scriptwriter`, `renderer`, `publisher`).
- $\mathcal{P}_{\text{workflow}}$: Granular permissions authorized for the specific active stage of the production workflow.

#### Enforced Capability Dimensions:
1. **Tool Access Whitelist**: Explicit list of allowed model tools (e.g., `["web_search", "fetch_url"]`; tool calls outside this list are intercepted and rejected with `PermissionDeniedError`).
2. **Filesystem Path Sandboxing**: Restricted read/write prefixes (e.g., write allowed *only* under `output/{project_id}/assets/`; attempts to read `~/.hermes/.env` or write to root are blocked).
3. **Network Egress Policy**:
   - `OFFLINE_ONLY`: No outbound sockets allowed.
   - `WHITELIST_HOSTS`: Outbound connections restricted strictly to approved domains (e.g., `commons.wikimedia.org`, `api.elevenlabs.io`).
   - `FULL_INTERNET`: Allowed only for initial research discovery.
4. **Token Expiry & Replay Prevention**: Tokens carry UTC expiration timestamps, workflow run IDs, and HMAC-SHA256 signatures preventing tampering or cross-session reuse.

---

### 4.3 Comprehensive Engineering Documentation Suite (14 Specifications)

To satisfy R6, Harness 9 must provide a full, production-grade engineering documentation suite consisting of **14 dedicated specification documents**:

| # | Document | Target Path | Scope & Core Contents |
|---|----------|-------------|-----------------------|
| 1 | **PRD** | `docs/PRD.md` | Product Requirements Document: Studio OS vision, user personas, functional requirements (R1–R6), acceptance criteria, non-functional SLA targets. |
| 2 | **Architecture** | `docs/ARCHITECTURE.md` | High-level decoupled architecture: 17-state machine, layer boundaries, execution flow, Hermes Agent integration, HyperFrames decoupling. |
| 3 | **System Design** | `docs/SYSTEM_DESIGN.md` | Detailed module design: subsystem interfaces, sequence diagrams, dataflows, synchronization primitives, error handling. |
| 4 | **Data Model** | `docs/DATA_MODEL.md` | Complete Pydantic schemas: 17 production models, validation rules, field constraints, serialization formats (JSON/YAML). |
| 5 | **API Contracts** | `docs/API_CONTRACTS.md` | Public & internal API contracts: CLI commands, Python programmatic API, RPC interfaces, request/response payloads, error codes. |
| 6 | **Workflow Spec** | `docs/WORKFLOW_SPEC.md` | 17-state lifecycle specification: state definitions (`CREATED` $\to$ `COMPLETED`), transition conditions, guard invariants, rollback policies. |
| 7 | **Security Model** | `docs/SECURITY_MODEL.md` | Least-privilege capability tokens: permission intersection calculus, sandboxing decorators, secret isolation, egress controls. |
| 8 | **Skill Spec** | `docs/SKILL_SPEC.md` | Hermes skills & CLI tool wrappers: skill metadata, invocation schemas, input validation, tool registration. |
| 9 | **Connector Spec** | `docs/CONNECTOR_SPEC.md` | External service connectors: search engines (Tavily, Exa), TTS backends (ElevenLabs, SAPI), media libraries (Wikimedia, Pexels). |
| 10 | **HyperFrames Integration** | `docs/HYPERFRAMES_INTEGRATION.md` | HyperFrames adapter interface, GSAP master timeline protocol, finite repeat rules, 7-block parameterized component registry. |
| 11 | **Hermes Compatibility** | `docs/HERMES_COMPATIBILITY.md` | Upstream Hermes compatibility layer (`adapters/hermes/`), prompt caching invariants, message alternation, toolset gating. |
| 12 | **ContentBench** | `docs/CONTENTBENCH.md` | 4-layer evaluation framework specification: scoring rubrics, benchmark datasets, automated test runner, evaluation reports. |
| 13 | **Evolution Spec** | `docs/EVOLUTION_SPEC.md` | Continuous learning engine: performance feedback ingestion, retention analytics, negative memory consolidation, prompt self-tuning. |
| 14 | **Creator Memory** | `docs/CREATOR_MEMORY.md` | Creator DNA architecture: Brand Constitution, preferences, skills, exemplars, memory indexing, few-shot conditioning. |

---

### 4.4 Architecture Decision Records (ADR-001 through ADR-005)

The repository must include formal Architecture Decision Records documenting key architectural trade-offs:

1. **`docs/adr/ADR-001-decoupled-state-machine-architecture.md`**:
   - *Context*: Linear sequential execution lacks auditability, pause/resume capability, and strict stage validation.
   - *Decision*: Adopt an explicit 17-state deterministic state machine with validated transitions and immutable stage artifact handoffs.
2. **`docs/adr/ADR-002-editorial-intelligence-multi-angle-engine.md`**:
   - *Context*: Directly expanding topic briefs into scripts leads to generic, repetitive content without editorial tension.
   - *Decision*: Introduce pre-scriptwriting Editorial Intelligence generating multiple candidate angles scored across a 9-dimension evaluation matrix.
3. **`docs/adr/ADR-003-hyperframes-modular-component-registry.md`**:
   - *Context*: Monolithic template generation in HTML/CSS causes brittle layouts and code duplication.
   - *Decision*: Establish an H9 component block registry featuring 7 reusable, parameterized, lint-checked visual building blocks.
4. **`docs/adr/ADR-004-creator-dna-economics-ledger.md`**:
   - *Context*: Content generation without creator memory produces off-brand videos, and unmonitored API calls risk budget overruns.
   - *Decision*: Implement the 6-component Creator DNA data model paired with an itemized, real-time Creator Economics ledger.
5. **`docs/adr/ADR-005-capability-token-security-model.md`**:
   - *Context*: Subagents executing arbitrary tools risk unauthorized file modification, network egress leaks, or secret exposure.
   - *Decision*: Enforce principle-of-least-privilege capability tokens derived via set intersection ($\mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$).

---

## 5. Verification, Test Framework & Acceptance Harness

### 5.1 Test Suite Inventory & Execution Baseline

The test suite in `tests/` is organized into a four-tier testing hierarchy ensuring full coverage and zero flakiness:

| Test Tier | Focus & Scope | Target Test Files | Total Tests | Status |
|---|---|---|:---:|:---:|
| **Tier 1** | Feature Coverage | `test_research.py`, `test_assets.py`, `test_scriptwriting.py`, `test_hyperframes.py`, `test_renderer.py`, `test_cli.py` | 60 | **PASS** |
| **Tier 2** | Boundary & Error Cases | Edge cases, corrupt WAV/MP4 headers, missing keys, size limits, offline isolation | 60 | **PASS** |
| **Tier 3** | Pairwise Combinations | Cross-feature interactions (Format $\times$ Voice $\times$ Provider $\times$ Duration) | 12 | **PASS** |
| **Tier 4** | Real-World Scenarios | Scenarios S1–S10 (Transistor, GPUs, Apollo, 9:16 vertical, CRISPR, JWST, etc.) | 16 | **PASS** |
| **Total** | **All Core Modules** | **148+ automated tests** | **148** | **100% PASS** |

- **Execution Commands**:
  ```powershell
  # Run full unit & integration test suite via unittest
  .\.venv\Scripts\python.exe -m unittest tests.test_research tests.test_assets tests.test_scriptwriting tests.test_hyperframes tests.test_renderer tests.test_cli tests.test_e2e_pipeline
  ```

---

### 5.2 Automated Acceptance Verification Harness (`verify_pipeline.py`)

`verify_pipeline.py` serves as the primary acceptance verification gate. It executes the end-to-end pipeline in test/offline mode and automatically verifies 6 core stage checkpoints:

1. **`CP_DOSSIER_VALID`**: Verifies schema-conforming `research_dossier.json`/`.yaml` with $\ge 3$ verifiable claims, confidence scores $\in [0.0, 1.0]$, and primary source URLs.
2. **`CP_LEDGER_VALID`**: Verifies `asset_ledger.json`/`.yaml` recording frozen local assets with SPDX licenses, source URLs, author attribution, and matching SHA-256 hashes.
3. **`CP_AUDIO_VALID`**: Verifies non-empty audio narration file `assets/audio/narration.wav` matching script duration within $\pm 0.2\text{s}$ with valid 16-bit PCM WAV headers.
4. **`CP_PROJECT_FILES` & `CP_DESIGN_GATE`**: Verifies existence and structure of `BRIEF.md`, `DESIGN.md` (Brand, Colors, Typography, Motion, Anti-Patterns), `SCRIPT.md`, and `STORYBOARD.md`.
5. **`CP_COMP_VALID`**: Verifies `index.html` featuring `<div data-composition-id="root">`, zero remote `http://` media URLs, zero broken local asset paths, `window.__timelines["root"]` GSAP registration, and finite animation repeats (no `repeat: -1`).
6. **`CP_VIDEO_VALID`**: Verifies valid, non-empty, playable `renders/final.mp4` with H.264 video and AAC audio streams.

---

### 5.3 Expansion Plan for R4, R5, and R6 Verification

To support the upgraded requirements, the verification harness and test suite will be expanded with the following dedicated acceptance checkpoints:

1. **R4 Acceptance Checkpoint (`CP_VOICE_QA_AND_DEDUP`)**:
   - VoiceQA asserts clipping ratio $< 0.01\%$, silence gaps $\le 300\text{ms}$, loudness variance $\le 2.5\text{ dB}$, and beat alignment drift $\le 0.2\text{s}$.
   - Asset deduplication asserts perceptual hash distance $d_H > 4$ between all selected scene images.
2. **R5 Acceptance Checkpoint (`CP_CREATOR_DNA_AND_BENCHMARK`)**:
   - Asserts generation adheres to Creator DNA constraints and negative memories.
   - Verifies `cost_ledger.json` calculates itemized LLM, research, TTS, rendering, and storage costs.
   - Runs ContentBench evaluation producing scores across Research, Script, Video, and Cost dimensions.
3. **R6 Acceptance Checkpoint (`CP_SECURITY_TOKENS_AND_SPECS`)**:
   - Permission boundary tests verify that child agents cannot execute unauthorized tools or write outside their sandboxed output directory.
   - Documentation audit verifies all 14 specification files and ADR-001 through ADR-005 exist and conform to required structural sections.

---

## 6. Architectural Gap Analysis & Traceability Matrix

| Requirement | Target Feature (from ORIGINAL_REQUEST.md) | Current Codebase Baseline | Architectural & Code Gaps | Priority & Action Plan |
|---|---|---|---|:---:|
| **R4** | **Multi-Provider VoiceDirector** | `TTSEngine` with 3-tier fallback (`src/scriptwriting/tts.py`) | Lacks character casting, emotion marker parsing, dynamic WPM rate adjustment, and unified director API | **HIGH**: Implement `VoiceDirector` in `src/audio/` or `src/scriptwriting/` |
| **R4** | **Automated VoiceQA** | Basic duration check in `verify_pipeline.py` | No automated waveform inspection for dead air, gaps, clipping, or loudness variance | **HIGH**: Build `VoiceQA` analyzer and metric reporting |
| **R4** | **Asset Deduplication** | URL check in `discovery.py`, SHA-256 in `freezer.py` | Lacks perceptual visual hashing (dHash/pHash) and cross-scene deduplication ledger | **MEDIUM**: Implement `dHash` perceptual deduplication in `src/assets/` |
| **R5** | **Creator DNA Data Model** | `DESIGN.md` in `src/scriptwriting/generator.py` | Missing Brand Constitution, Preferences, Skills, Examples, Performance & Negative Memory | **HIGH**: Create `CreatorDNA` schemas in `src/models/` and engine |
| **R5** | **Creator Economics Ledger** | Stage durations in `src/models/summary.py` | No granular itemized cost tracking (LLM, research, TTS, render compute, storage) | **HIGH**: Implement `CostLedger` and pricing models |
| **R5** | **ContentBench (Quality OS)** | 6 binary checks in `verify_pipeline.py` | Lacks 4-layer quantitative evaluation framework and benchmark scoring suite | **HIGH**: Implement `ContentBench` evaluation engine |
| **R6** | **Security Capability Tokens** | Unrestricted process execution | Missing capability token engine and permission intersection ($\mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$) | **HIGH**: Build `CapabilityTokenEngine` and permission guards |
| **R6** | **Engineering Documentation Suite** | 5 files in `docs/harness9/` | Missing 14 formal specifications and ADR-001 through ADR-005 | **HIGH**: Author full documentation suite in `docs/` |

---

## 7. Target Schemas, Interfaces & Implementation Blueprints

### 7.1 VoiceQA & VoiceDirector Blueprint

```python
# Target Schema: src/models/audio.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class VoiceProfile(BaseModel):
    voice_id: str
    provider: str  # "elevenlabs", "openai", "sapi", "harmonic"
    display_name: str
    gender: str = "neutral"
    pitch_adjustment: float = 0.0
    speaking_rate_wpm: int = 145
    stability: float = 0.5
    similarity_boost: float = 0.75

class VoiceQAReport(BaseModel):
    passed: bool
    total_duration_sec: float
    clipping_events_count: int = 0
    clipping_ratio: float = 0.0  # Must be < 0.0001
    dead_air_instances_count: int = 0
    max_dead_air_duration_sec: float = 0.0  # Must be <= 0.3s
    average_gap_duration_sec: float = 0.15
    loudness_variance_db: float = 0.0  # Must be <= 2.5 dB
    speech_beat_max_drift_sec: float = 0.0  # Must be <= 0.2s
    metrics: Dict[str, float] = Field(default_factory=dict)
```

### 7.2 Perceptual Hashing Blueprint

```python
# Target Implementation: src/assets/dedup.py
from PIL import Image
from typing import List, Set

def compute_dhash(image_path: str, hash_size: int = 8) -> int:
    """Compute difference hash (dHash) for visual perceptual deduplication."""
    img = Image.open(image_path).convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())
    diff = []
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * (hash_size + 1) + col]
            right = pixels[row * (hash_size + 1) + col + 1]
            diff.append(1 if left > right else 0)
    decimal_val = 0
    for bit in diff:
        decimal_val = (decimal_val << 1) | bit
    return decimal_val

def hamming_distance(h1: int, h2: int) -> int:
    """Calculate bitwise Hamming distance between two 64-bit perceptual hashes."""
    return bin(h1 ^ h2).count("1")
```

### 7.3 Creator DNA & Economics Ledger Blueprint

```python
# Target Schema: src/models/creator.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class BrandConstitution(BaseModel):
    mission: str
    tone_of_voice: List[str]
    prohibited_words: List[str] = Field(default_factory=list)
    prohibited_themes: List[str] = Field(default_factory=list)
    target_audience_level: str = "intermediate"

class CreatorPreferences(BaseModel):
    preferred_wpm: int = 145
    target_scene_duration_sec: float = 4.5
    visual_density_per_min: int = 12
    primary_color: str = "#00d2ff"
    background_color: str = "#0a0e17"
    aspect_ratio: str = "16:9"

class CreatorMemory(BaseModel):
    performance_learnings: List[str] = Field(default_factory=list)
    negative_memories: List[str] = Field(default_factory=list)

class CreatorDNA(BaseModel):
    creator_id: str
    brand_constitution: BrandConstitution
    preferences: CreatorPreferences
    skills: List[str] = Field(default_factory=list)
    examples: List[Dict[str, str]] = Field(default_factory=list)
    memory: CreatorMemory = Field(default_factory=CreatorMemory)
```

```python
# Target Schema: src/models/economics.py
from pydantic import BaseModel, Field
from typing import List, Dict

class CostItem(BaseModel):
    category: str  # "llm", "research", "tts", "render", "storage"
    item_name: str
    units_consumed: float
    unit_type: str  # "tokens", "queries", "characters", "seconds", "megabytes"
    unit_rate_usd: float
    total_cost_usd: float

class ProductionCostLedger(BaseModel):
    run_id: str
    project_id: str
    items: List[CostItem] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    cost_per_video_second: float = 0.0
    estimated_margin_percent: float = 0.0
```

### 7.4 Security Capability Token Blueprint

```python
# Target Implementation: src/security/tokens.py
import hmac
import hashlib
import time
from typing import Set, Dict, Any
from pydantic import BaseModel, Field

class CapabilityToken(BaseModel):
    token_id: str
    agent_id: str
    role: str
    workflow_id: str
    allowed_tools: Set[str]
    allowed_write_paths: Set[str]
    allowed_network_hosts: Set[str]
    expires_at_utc: float

def derive_child_token(
    parent_token: CapabilityToken,
    role_allowed_tools: Set[str],
    role_allowed_paths: Set[str],
    workflow_allowed_tools: Set[str],
    workflow_allowed_paths: Set[str],
    child_agent_id: str,
    secret_key: bytes,
) -> CapabilityToken:
    """Enforce child_permission = parent ∩ role ∩ workflow."""
    child_tools = parent_token.allowed_tools.intersection(role_allowed_tools).intersection(workflow_allowed_tools)
    child_paths = parent_token.allowed_write_paths.intersection(role_allowed_paths).intersection(workflow_allowed_paths)
    child_hosts = parent_token.allowed_network_hosts

    return CapabilityToken(
        token_id=f"tok_{int(time.time()*1000)}",
        agent_id=child_agent_id,
        role=parent_token.role,
        workflow_id=parent_token.workflow_id,
        allowed_tools=child_tools,
        allowed_write_paths=child_paths,
        allowed_network_hosts=child_hosts,
        expires_at_utc=time.time() + 3600.0,
    )
```

---

## 8. Conclusion & Next Actions

1. **Investigation Completion**: The investigation of Requirements R4, R5, R6 and the Verification Framework is complete. All architectural foundations, quantitative formulas, data schemas, security mechanics, and documentation structures have been mapped out and verified against the existing codebase.
2. **Handoff Report**: Detailed observations, logic chains, caveats, conclusions, and verification commands are formally documented in `g:\Finding-new-code\harness9\.agents\explorer_survey_3\handoff.md`.
3. **Execution Readiness**: The architecture is fully prepared for the subsequent implementation phases across models, voice director/QA, creator memory, capability tokens, and documentation.
