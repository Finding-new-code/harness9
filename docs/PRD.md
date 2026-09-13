# Product Requirements Document (PRD): Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Author:** Head of Engineering & Architecture Team  
**Target System:** Harness 9 Decoupled Autonomous Video Production Operating System  

---

## 1. Executive Summary & Vision

Harness 9 (H9) is a decoupled, autonomous, state-machine-driven content production operating system. It transforms high-level creative briefs and subject-matter topics into broadcast-quality, rendered MP4 video assets with full provenance, automated acoustic QA, creator brand DNA consistency, granular unit-cost ledgering, and mathematical capability security.

Unlike monolithic text-to-video generators or fragile script-scraping scripts, Harness 9 operates as an AI-native production studio. It incorporates:
1. **Deterministic 17-State Lifecycle State Machine**: Enforcing immutable contract handoffs from `CREATED` to `COMPLETED`.
2. **Editorial Intelligence Engine**: Generating multi-angle candidates across 5 archetypes and evaluating them via a 9-dimension editorial scorecard.
3. **HyperFrames Integration & Reusable Component Registry**: Decoupling visual rendering into parameterized blocks (HTML5/CSS3/GSAP) with strict composition linting.
4. **Voice Director & Automated Acoustic VoiceQA**: Multi-backend TTS routing (ElevenLabs, OpenAI, SAPI, Harmonic) paired with quantitative audio signal quality assurance (dead air, clipping, volume consistency, speech-beat alignment).
5. **Multi-Tier Asset Deduplication**: Combining SHA-256 byte-exact caching and perceptual gradient difference hashing (`dHash`).
6. **Creator DNA & Unit Economics Engine**: 6-component cognitive memory model paired with itemized resource ledgering (LLM, research, TTS, compute, storage).
7. **ContentBench Quality OS**: 4-layer evaluation benchmark scoring Research, Script, Video, and Cost dimensions on a normalized $[0.0, 1.0]$ scale.
8. **Capability Token Security Engine**: Enforcing least-privilege permission calculus $\mathcal{P}_{\text{child}} = \mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$ with HMAC-SHA256 signatures.

---

## 2. Target Personas & Stakeholders

| Persona | Description | Primary Use Case & Value Proposition |
|---|---|---|
| **Autonomous Hermes Agent** | Hermes AIAgent, TUI/CLI, and Messaging Gateways. | Invokes service-gated video tools (`generate_video_from_brief`) with byte-stable prompt caching and zero context pollution. |
| **Technical Content Creator** | Independent educational and deep-tech video creators. | Produces high-retention, brand-consistent explainers adhering to personal Brand Constitution without manual video editing. |
| **Media & DevRel Studios** | Enterprise developer relations and engineering media teams. | Rapidly converts technical documentation, RFCs, and release notes into animated video changelogs with audited factual claims. |
| **Quality & Security Auditor** | Forensic engineers and automated benchmark evaluators. | Audits capability token boundaries, verifies ContentBench quality metrics, and reviews itemized cost ledgers. |

---

## 3. Product Architecture & Subsystem Decomposition

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENT INTERFACES                                       │
│    Hermes CLI / TUI  │  Messaging Gateway (Discord/TG)  │  Desktop GUI  │  Python SDK     │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │ Service-Gated Invocation
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                           adapters/hermes/ (Hermes Compatibility)                         │
│   • HermesBridge (SDK API)    • HermesSessionSandbox (Isolation)   • Service-Gated Tools  │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │ Capability Token Passed
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                        HARNESS 9 CORE PRODUCTION OPERATING SYSTEM                         │
│                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    src/orchestrator/ (17-State State Machine)                       │  │
│  │  CREATED ──► RESEARCH ──► EDITORIAL ──► SCRIPT ──► AUDIO ──► ASSETS ──► RENDER ──►   │  │
│  └──────────────────────────────────────────┬──────────────────────────────────────────┘  │
│                                             │                                             │
│       ┌─────────────────────────────────────┼─────────────────────────────────────┐       │
│       ▼                                     ▼                                     ▼       │
│  ┌───────────────────────┐             ┌───────────────────────┐            ┌───────────┐ │
│  │   src/editorial/      │             │  src/scriptwriting/   │            │src/assets/│ │
│  │ • 5 Angle Archetypes  │             │ • VoiceDirector       │            │• SHA-256  │ │
│  │ • 9-Dimension Scorer  │             │ • Acoustic VoiceQA    │            │• dHash    │ │
│  │ • Narrative Planner   │             │ • Beat Aligner        │            │• Freezer  │ │
│  └───────────────────────┘             └───────────────────────┘            └───────────┘ │
│       │                                     │                                     │       │
│       └─────────────────────────────────────┼─────────────────────────────────────┘       │
│                                             ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    adapters/hyperframes/ & src/hyperframes/                         │  │
│  │ • 7+ Parameterized Blocks (Collage, SplitScreen, Quote, Timeline, Stat, Panel)      │  │
│  │ • HTML5/CSS3/GSAP Generator • Composition Linter • Headless Playwright Renderer     │  │
│  └──────────────────────────────────────────┬──────────────────────────────────────────┘  │
│                                             │                                             │
│       ┌─────────────────────────────────────┴─────────────────────────────────────┐       │
│       ▼                                                                           ▼       │
│  ┌───────────────────────────────────────┐               ┌──────────────────────────────┐ │
│  │   src/creator/ & src/evaluation/      │               │   src/security/              │ │
│  │ • Creator DNA (6-Component Cognitive) │               │ • Capability Token Engine    │ │
│  │ • Itemized Economics Cost Ledger      │               │ • P_child = P_p ∩ P_r ∩ P_w  │ │
│  │ • ContentBench (4-Layer Quality OS)   │               │ • Security Sandboxing Guard  │ │
│  └───────────────────────────────────────┘               └──────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Detailed Functional Requirements (R1 – R6)

### R1. State Machine, Production Contracts & Hermes Bridge
- **FR-1.1**: The lifecycle state machine must support exactly 17 canonical states (`CREATED` through `COMPLETED`) plus 3 control states (`PAUSED_FOR_HUMAN`, `FAILED`, `CANCELLED`).
- **FR-1.2**: All invalid state jumps (e.g. `CREATED` $\to$ `RENDER_COMPLETED`) must be rejected with `StateTransitionError`.
- **FR-1.3**: All inter-stage data exchanges must validate against strict Pydantic v2 schemas (`src/models/contracts.py`) without field truncation or type loss.
- **FR-1.4**: `adapters/hermes/` must provide service-gated tools (`check_fn: check_harness9_available`) that preserve Hermes prompt caching invariants and session directory confinement.

### R2. Editorial Intelligence & Multi-Angle Ideation
- **FR-2.1**: The ideation engine must generate candidate angles spanning 5 distinct archetypes: `contrarian`, `deep_dive`, `data_led`, `human_narrative`, and `future_impact`.
- **FR-2.2**: The 9-dimension editorial scorecard must evaluate candidates across: Audience Relevance, Novelty, Hook Potential, Narrative Potential, Creator Fit, Evidence Availability, Visual Potential, Platform Fit, and Saturation Risk (inverted penalty).
- **FR-2.3**: Top angle selection must automatically select the winning angle with auditable score breakdown and generate 3 hook variations feeding a 4-act `ContentOutline`.

### R3. HyperFrames Adapter & Reusable Component Registry
- **FR-3.1**: The `adapters/hyperframes/` layer must decouple composition assembly from core video rendering.
- **FR-3.2**: The component registry must implement 7+ parameterized blocks: `ReferenceCollageHook`, `SplitScreenIntro`, `QuoteHighlight`, `TimelineReveal`, `StatisticReveal`, `ComparisonPanel`, and `CreatorBottomCollage`.
- **FR-3.3**: Component renderers must output standards-compliant HTML5, CSS3, and deterministic GSAP animation timelines (`window.__timelines["root"]`).
- **FR-3.4**: The composition linter must reject infinite animation loops (`repeat: -1`), missing container elements (`data-composition-id="root"`), external `http://` asset references, and layout overflow.

### R4. Voice Director, VoiceQA & Asset Deduplication
- **FR-4.1**: `VoiceDirector` must orchestrate multi-backend speech synthesis (ElevenLabs, OpenAI TTS, Windows SAPI, Harmonic Synthesizer) with dynamic pacing ($130-160\text{ WPM}$) and emotional modulation.
- **FR-4.2**: `VoiceQA` must inspect synthesized audio waveforms and quantitatively enforce:
  - Dead air: No silence ($<-45\text{ dBFS}$) gap $>300\text{ms}$.
  - Clipping: Saturated samples ($|s| \ge 32767$) ratio $<0.01\%$.
  - Loudness variance: Scene-to-scene RMS energy delta $\le 2.5\text{ dBFS}$.
  - Speech-beat drift: Narration boundary alignment drift $\le 0.20\text{s}$.
- **FR-4.3**: Asset ingestion must enforce two-tier deduplication: Tier 1 SHA-256 byte-exact matching and Tier 2 `dHash` perceptual difference hashing with Hamming distance $d_H \le 4$ rejection.

### R5. Creator DNA, Creator Economics & ContentBench
- **FR-5.1**: `CreatorDNA` must store and enforce a 6-part cognitive profile: Brand Constitution (mission, tone, negative constraints), Preferences (cadence, colors, fonts), Skills (domain lexicon), Examples (exemplar hooks/outlines), Performance Memory (retention telemetry), and Negative Memory (past failure patterns).
- **FR-5.2**: `CreatorEconomics` must maintain an itemized ledger tracking LLM prompt/completion tokens, research queries, TTS characters, render compute, and storage footprint, calculating total cost and cost per video second.
- **FR-5.3**: `ContentBench` must evaluate completed productions across 4 objective layers:
  - Layer 1: Research Quality ($S_{\text{research}}$: fact density, source authority, corroboration).
  - Layer 2: Script Quality ($S_{\text{script}}$: hook strength, pacing cadence, readability, DNA compliance).
  - Layer 3: Video Quality ($S_{\text{video}}$: VoiceQA score, beat synchronization, visual relevance, lint compliance).
  - Layer 4: Cost Efficiency ($S_{\text{cost}}$: budget target compliance, token efficiency ratio).
  - Aggregate Composite Score: $S_{\text{composite}} = 0.25 S_{\text{research}} + 0.30 S_{\text{script}} + 0.30 S_{\text{video}} + 0.15 S_{\text{cost}} \in [0.0, 1.0]$.

### R6. Security Capability Tokens & Engineering Documentation Suite
- **FR-6.1**: Every worker and subagent execution must require an HMAC-SHA256 signed `CapabilityToken`.
- **FR-6.2**: Permissions must strictly enforce set intersection: $\mathcal{P}_{\text{child}} = \mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$.
- **FR-6.3**: `SecurityGuard` must enforce tool whitelisting, filesystem path confinement (preventing directory traversal `../` attacks), and network egress filtering.
- **FR-6.4**: The system must provide a complete engineering documentation suite (14 formal markdown specifications) and 5 Architecture Decision Records (ADR-001 through ADR-005).

---

## 5. Non-Functional Requirements (NFRs)

| ID | Category | Requirement Description | Acceptance SLA |
|---|---|---|---|
| **NFR-1** | **Deterministic Offline Mode** | Full pipeline must execute end-to-end without active internet connection using local mock research, harmonic audio, and procedural visual assets. | 100% pass in offline sandbox |
| **NFR-2** | **Prompt Cache Preservation** | Interaction with upstream Hermes Agent must never alter system prompts, inject synthetic user turns, or mutate past tool definitions mid-session. | 0 cache invalidations |
| **NFR-3** | **Execution Throughput** | Generating a standard 30-second explainer video in offline mode must complete in $<60\text{ seconds}$ total wall-clock time on standard developer hardware. | $<60\text{s}$ pipeline time |
| **NFR-4** | **Production Cost Efficiency** | Cloud production cost for a 30-second video must not exceed $\$0.25$ total ($\le \$0.0083 / \text{second}$). | $\le \$0.25$ / 30s video |
| **NFR-5** | **Cryptographic Security** | Tampered capability tokens, expired tokens, or unpermitted tool/path calls must be rejected immediately without execution leakage. | 0 unauthorized escapes |
| **NFR-6** | **Acoustic Quality Standard** | Audio narration must produce zero audible distortion or abrupt cuts, verified by automated waveform analysis. | Clipping $<0.01\%$, Drift $\le 0.2\text{s}$ |

---

## 6. Verification Gates & Acceptance Criteria

```
[ BRIEF.md ] ──► (State Machine Validation) ──► [ RESEARCH_COMPLETED ]
                       │
                       ▼ (Editorial Scoring >= 0.75)
             [ ANGLE_SELECTED ] ──► (VoiceQA Gate) ──► [ VOICE_QA_PASSED ]
                                                             │
                                                             ▼ (dHash Dedup + Linter)
                                                   [ COMPOSITION_GENERATED ]
                                                             │
                                                             ▼ (Playwright / FFmpeg)
                                                   [ RENDER_COMPLETED ]
                                                             │
                                                             ▼ (ContentBench >= 0.80)
                                                   [ FINAL PUBLISH PACKAGE ]
```

1. **State Machine Audit Gate**: 100% of state transitions logged in `TransitionRecord` audit log with zero illegal jumps.
2. **Design & Editorial Gate**: Winning angle selected with composite score $\ge 0.70$ and 4-act narrative outline approved.
3. **VoiceQA Gate**: Audio narration validates with zero clipping events, silence gaps $\le 300\text{ms}$, loudness delta $\le 2.5\text{ dBFS}$, and beat drift $\le 0.20\text{s}$.
4. **Composition Lint Gate**: Zero broken paths, finite animation loops, and valid GSAP registration.
5. **Quality OS Gate**: ContentBench composite score $\ge 0.80$ on standard test benchmarks.
6. **Security Gate**: Capability token engine verifies tool permissions and path sandboxes across all worker threads.
