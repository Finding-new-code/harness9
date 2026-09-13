# Detailed Subsystem Design: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/`  
**Cross-References:** `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/API_CONTRACTS.md`, `docs/WORKFLOW_SPEC.md`  

---

## 1. Subsystem Decomposition Overview

This document specifies the internal class architectures, algorithms, mathematical formulations, and execution flows for the 8 core subsystems of Harness 9.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                HARNESS 9 CORE                                   │
│                                                                                 │
│   1. Orchestration & State Machine  ───►  5. HyperFrames Component Registry     │
│   2. Editorial Intelligence Engine  ───►  6. Creator DNA & Economics Engine     │
│   3. Voice Director & Acoustic QA   ───►  7. ContentBench Evaluation Framework  │
│   4. Two-Tier Asset Deduplication   ───►  8. Security Capability Token Engine   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Subsystem 1: Orchestration & State Machine Engine (`src/orchestrator/`)

### 2.1 State Machine Class Architecture
- **Class**: `ProductionStateMachine`
- **Internal State**:
  - `current_state: ProductionState`: Current active state in the 17-state lifecycle.
  - `history: List[TransitionRecord]`: Append-only transition audit log.
  - `context: Dict[str, Any]`: Execution payload storage keyed by contract type.
  - `run_id: str`: Unique execution identifier.
  - `lock: threading.Lock`: Thread-safe state transition synchronization.

### 2.2 Transition Validation Algorithm
1. On `transition_to(target_state, payload, metadata)`:
   - Check if `target_state` exists in `VALID_TRANSITIONS[self.current_state]`.
   - If not valid, raise `StateTransitionError(f"Illegal state jump: {current_state} -> {target_state}")`.
   - Validate that `payload` conforms to the required Pydantic contract for `target_state`.
   - Compute transition duration $\Delta t = t_{\text{now}} - t_{\text{prev}}$.
   - Record `TransitionRecord(from_state, to_state, timestamp, payload_summary, duration_ms)`.
   - Set `self.current_state = target_state`.
   - Atomically persist `transition_history.json` and `transition_history.yaml`.

---

## 3. Subsystem 2: Editorial Intelligence Engine (`src/editorial/`)

### 3.1 Multi-Angle Generation (`AngleGenerator`)
- Accepts `ResearchDossier` and `ContentBrief`.
- Generates 5 distinct candidates mapped to predefined archetypes:
  1. `contrarian`: Subverts common assumptions (e.g. "Why Silicon Valley Didn't Invent the Modern Chip").
  2. `deep_dive`: Focuses on underlying mechanics (e.g. "How Quantum Tunneling Governs FinFETs").
  3. `data_led`: Centers on empirical curves and metrics (e.g. "The Exponential Scaling Law That Broke Computing").
  4. `human_narrative`: Highlights biographical struggle and collaboration (e.g. "The 3 Renegades Who Built the First Transistor").
  5. `future_impact`: Projects technological trajectories (e.g. "The Post-Silicon Architecture of 2035").

### 3.2 9-Dimension Scoring Matrix (`EditorialScorer`)
- Evaluates each candidate $a_k$ across 9 dimensions normalized to $[0.0, 1.0]$:
  - $d_1$: Audience Relevance ($w_1 = 0.15$)
  - $d_2$: Novelty ($w_2 = 0.15$)
  - $d_3$: Hook Potential ($w_3 = 0.15$)
  - $d_4$: Narrative Potential ($w_4 = 0.10$)
  - $d_5$: Creator Fit ($w_5 = 0.10$)
  - $d_6$: Evidence Availability ($w_6 = 0.10$)
  - $d_7$: Visual Potential ($w_7 = 0.10$)
  - $d_8$: Platform Fit ($w_8 = 0.10$)
  - $d_9$: Saturation Risk ($w_9 = 0.05$, inverted: $1.0 - d_9$)
- **Composite Score Formula**:
  $$S(a_k) = \sum_{i=1}^{8} w_i d_i + w_9 (1.0 - d_9)$$
- **Selection**: `AngleSelector` selects $a^* = \arg\max_{a_k} S(a_k)$ and attaches the full score breakdown into `EditorialAngle.scorecard`.

### 3.3 Hook Ideation & Narrative Planner (`NarrativePlanner`)
- Generates 3 hook variations (Question, Contrarian Statement, Shocking Metric).
- Builds `ContentOutline` consisting of 4 distinct acts:
  - Act 1: `The Hook` ($0\% - 15\%$ duration)
  - Act 2: `The Barrier` ($15\% - 45\%$ duration)
  - Act 3: `The Breakthrough` ($45\% - 75\%$ duration)
  - Act 4: `The Ripple Effect` ($75\% - 100\%$ duration)

---

## 4. Subsystem 3: Voice Director & Acoustic VoiceQA (`src/scriptwriting/`)

### 4.1 Multi-Backend VoiceDirector (`VoiceDirector`)
- Implements 4-tier provider hierarchy:
  1. `ElevenLabsTTSProvider`: High-fidelity neural voice with SSML and stability control.
  2. `OpenAITTSProvider`: Fast cloud TTS fallback (`tts-1-hd`).
  3. `WindowsSAPITTSProvider`: Offline OS-native speech synthesis via PowerShell.
  4. `HarmonicWAVSynthesizer`: 100% deterministic pure-Python formant synthesizer ($F_0=130\text{Hz}, F_1=500\text{Hz}, F_2=1500\text{Hz}$).
- Pacing calculator enforces target words per minute ($145\text{ WPM}$) to ensure audio fits scene duration limits without unnatural time-stretching.

### 4.2 Automated Acoustic VoiceQA Engine (`VoiceQA`)
- Reads raw 16-bit PCM WAV audio samples $s[n] \in [-32768, 32767]$ at sample rate $f_s = 44100\text{Hz}$ or $22050\text{Hz}$.
- **Metrics Evaluated**:
  1. **Dead Air Analysis**:
     - Computes frame-by-frame RMS power: $P_{\text{frame}} = 20 \log_{10}(\text{RMS} / 32767)$.
     - Flags contiguous silent frames ($<-45\text{ dBFS}$) exceeding $300\text{ms}$.
  2. **Clipping & Saturation**:
     - Counts samples where $|s[n]| \ge 32767$.
     - Rejects audio if $\text{ClippingRatio} = N_{\text{clipped}} / N_{\text{total}} \ge 0.0001$ ($0.01\%$).
  3. **Loudness Consistency**:
     - Calculates RMS loudness per scene segment.
     - Enforces maximum inter-scene volume delta: $\Delta L = \max(L_k) - \min(L_k) \le 2.5\text{ dBFS}$.
  4. **Speech-Beat Alignment Drift**:
     - Compares narration end timestamps $T_{\text{audio}, j}$ with storyboard scene boundary $T_{\text{scene}, j}$.
     - Enforces $\max_j |T_{\text{audio}, j} - T_{\text{scene}, j}| \le 0.20\text{s}$.
- Outputs `VoiceQAReport` with boolean `passed` flag and itemized DSP metrics.

---

## 5. Subsystem 4: Two-Tier Asset Deduplication Engine (`src/assets/`)

```
               Incoming Candidate Asset (Image / SVG / Video)
                                     │
                                     ▼
                   ┌───────────────────────────────────┐
                   │    Tier 1: Byte-Exact SHA-256     │
                   │    Hash = SHA256(RawBytes)        │
                   └─────────────────┬─────────────────┘
                                     │
                    Match in Asset Ledger?
                    ├── YES ──► Reference Existing Asset (0 Byte Download)
                    └── NO  ──► Proceed to Tier 2
                                     │
                                     ▼
                   ┌───────────────────────────────────┐
                   │ Tier 2: Perceptual dHash (64-bit) │
                   │ Grayscale 9x8 Gradient Comparison │
                   └─────────────────┬─────────────────┘
                                     │
                    Hamming Distance d_H <= 4 against selected assets?
                    ├── YES ──► Near-Duplicate (Reject Candidate)
                    └── NO  ──► Distinct Visual (Freeze into Asset Ledger)
```

### 5.1 Algorithm: Difference Hash (`dHash`)
1. Convert image to 8-bit grayscale ($L$).
2. Resize to $9 \times 8$ pixels using Lanczos resampling.
3. Compute row-wise gradient: for $y \in [0, 7]$ and $x \in [0, 7]$, compare $P(x, y)$ with $P(x+1, y)$.
4. Set bit $b = 1$ if $P(x, y) > P(x+1, y)$, else $0$.
5. Pack 64 bits into 64-bit integer $H_{\text{dhash}}$.
6. Calculate Hamming distance against all frozen scene assets:
   $$d_H(H_1, H_2) = \text{popcount}(H_1 \oplus H_2)$$
7. Reject candidate if $d_H \le 4$.

---

## 6. Subsystem 5: HyperFrames Integration & Component Registry (`src/hyperframes/`)

### 6.1 Component Registry Architecture
- **Base Class**: `BaseComponent`
  - `render_html(params: Dict[str, Any]) -> str`
  - `render_css(params: Dict[str, Any]) -> str`
  - `render_gsap(params: Dict[str, Any], timeline_var: str) -> str`
  - `validate_parameters(params: Dict[str, Any]) -> bool`

### 6.2 The 7 Canonical Reusable Blocks
1. `ReferenceCollageHook`: 3-card dynamic visual stack with staggered entrance animations.
2. `SplitScreenIntro`: 50/50 comparison layout with contrasting typography and animated center divider.
3. `QuoteHighlight`: Prominent citation callout with animated quotation glyph and source attribution badge.
4. `TimelineReveal`: Vertical/horizontal milestone progression with synchronized glowing nodes.
5. `StatisticReveal`: Large-format animated number counter with contextual label and radial progress accent.
6. `ComparisonPanel`: Side-by-side feature matrix with green/red checkmark transition badges.
7. `CreatorBottomCollage`: Persistent bottom third creator identity card with social handle and badge.

### 6.3 Composition Linter (`CompositionValidator`)
- Enforces non-negotiable DOM and animation constraints:
  - Container must include `<div data-composition-id="root">`.
  - Zero external `http://` or `https://` URLs (all assets must resolve to frozen local paths).
  - GSAP timeline must register on `window.__timelines["root"]`.
  - Zero infinite animations (`repeat: -1`).
  - Viewport dimension check ($1920\times 1080$ for 16:9, $1080\times 1920$ for 9:16).

---

## 7. Subsystem 6: Creator DNA & Economics Engine (`src/creator/`)

### 7.1 Creator DNA Structure
- **BrandConstitution**: Non-negotiable editorial guardrails, forbidden words (`game-changer`, `revolutionize`), audience comprehension level.
- **CreatorPreferences**: Speaking rate ($145\text{ WPM}$), scene transition tempo ($4.5\text{s}$), brand color palette (HEX), typography hierarchy.
- **CreatorSkills**: Domain-specific terminology and preferred visual diagramming styles.
- **CreatorExamples**: Curated few-shot exemplar hooks and storyboards.
- **PerformanceMemory**: Historical engagement analytics and high-retention patterns.
- **NegativeMemory**: Past failure log and dynamic negative prompt constraints.

### 7.2 Creator Economics Ledger (`ProductionCostLedger`)
- Granular tracking across 5 resource categories:
  1. `LLM Tokens`: Prompt tokens, completion tokens, cached tokens across all model calls.
  2. `Research APIs`: Query count against search and knowledge endpoints.
  3. `TTS Audio`: Character count and compute tier.
  4. `Video Rendering`: Headless Chromium execution time and FFmpeg muxing compute.
  5. `Storage Footprint`: Media bytes stored in project workspace.
- Computes `total_cost_usd` and `cost_per_video_second`.

---

## 8. Subsystem 7: ContentBench 4-Layer Quality OS (`src/evaluation/`)

```
                                CONTENTBENCH
                                      │
       ┌──────────────────┬───────────┴───────────┬──────────────────┐
       ▼                  ▼                       ▼                  ▼
┌──────────────┐   ┌──────────────┐        ┌──────────────┐   ┌──────────────┐
│   Layer 1    │   │   Layer 2    │        │   Layer 3    │   │   Layer 4    │
│   Research   │   │    Script    │        │ Video & Comp │   │  Economics   │
│ (Density,    │   │ (Hook, WPM,  │        │ (VoiceQA,    │   │ (Cost/Min,   │
│  Authority,  │   │  Readability,│        │  Beat Sync,  │   │  Token Eff,  │
│  Corroborat.)│   │  DNA Rules)  │        │  Lint Check) │   │  GPU Speed)  │
└──────┬───────┘   └──────┬───────┘        └──────┬───────┘   └──────┬───────┘
       │                  │                       │                  │
       └──────────────────┼───────────────────────┼──────────────────┘
                          ▼
             [ Composite Quality Score ]
          S = 0.25 S_1 + 0.30 S_2 + 0.30 S_3 + 0.15 S_4
```

- Generates `EvaluationReport` for each stage.
- Pass threshold: $S_{\text{composite}} \ge 0.80$.

---

## 9. Subsystem 8: Security Capability Token Engine (`src/security/`)

### 9.1 Capability Token Lifecycle & Calculus
- Every actor executes with a signed `CapabilityToken`.
- **Permission Calculus**:
  $$\mathcal{P}_{\text{child}} = \mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$$
- **Cryptographic Signature**:
  $$\text{Signature} = \text{HMAC-SHA256}(K_{\text{master}}, \text{CanonicalJSON}(\text{Payload}))$$
- **Lineage**: Lineage array tracks complete chain of delegator token IDs from root down to leaf.
- **Security Guard**: Enforces tool execution whitelist, filesystem path confinement (preventing path traversal `..`), and network egress controls.
