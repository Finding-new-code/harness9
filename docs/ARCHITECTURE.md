# System Architecture Specification: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/`, `adapters/`  
**Cross-References:** `docs/PRD.md`, `docs/SYSTEM_DESIGN.md`, `docs/DATA_MODEL.md`, `docs/adrs/ADR-001.md` through `ADR-005.md`  

---

## 1. Architectural Philosophy & Design Principles

Harness 9 is architected around four non-negotiable architectural tenets:

1. **Decoupled State-Machine Orchestration**: Pipeline execution is not an opaque sequential Python script; it is a deterministic, event-driven state machine advancing through 17 explicit canonical states. Every transition validates the incoming payload against strict contracts, records an immutable audit log, and permits pausing, inspection, or failure recovery.
2. **Strict Contract Boundaries (Pydantic v2)**: Subsystems never pass untyped dictionaries or mutable global state across domain boundaries. All inputs and outputs are validated Pydantic v2 schemas supporting bi-directional JSON/YAML serialization and atomic filesystem persistence.
3. **Narrow Core Waist & Adapter Isolation**: Upstream agent systems (Hermes Agent) and downstream rendering engines (HyperFrames) interact strictly through isolated adapters (`adapters/hermes/`, `adapters/hyperframes/`). This prevents prompt cache invalidation in Hermes and shields the core OS from browser/FFmpeg internals.
4. **Mathematical Principle of Least Privilege**: Subagents, child workers, and background tools operate inside sandboxed execution envelopes enforced by HMAC-SHA256 signed capability tokens where child permissions are strictly bounded by set intersection ($\mathcal{P}_{\text{child}} = \mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$).

---

## 2. Layered Subsystem Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                             LAYER 1: ADAPTERS & INTERFACES                               │
│  ┌────────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────────┐  │
│  │   adapters/hermes/     │  │  adapters/hyperframes/  │  │      CLI Orchestrator     │  │
│  │  • HermesBridge API    │  │  • Composition Compiler │  │  • Pipeline Runner        │  │
│  │  • Session Sandbox     │  │  • Renderer Bridge      │  │  • Inspect & Benchmark    │  │
│  │  • Service-Gated Tools │  │  • Linter Bridge        │  │  • Dry-Run & Offline Mode │  │
│  └────────────────────────┘  └─────────────────────────┘  └───────────────────────────┘  │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ Validated Request + Capability Token
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 2: STATE MACHINE & ORCHESTRATION                           │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    src/orchestrator/state_machine.py                               │  │
│  │   • 17 Canonical Lifecycle States (CREATED ──► COMPLETED)                          │  │
│  │   • Deterministic State Transition Guards & Illegal Jump Rejection                 │  │
│  │   • TransitionRecord Audit Trail & Rollback Management                             │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
┌───────────────────────────────────────────┐ ┌────────────────────────────────────────────┐
│      LAYER 3: COGNITIVE & EDITORIAL       │ │     LAYER 4: MEDIA SYNTHESIS & ASSETS      │
│  ┌─────────────────────────────────────┐  │ │  ┌──────────────────────────────────────┐   │
│  │          src/editorial/             │  │ │  │          src/scriptwriting/          │   │
│  │ • 5 Angle Archetypes Generator      │  │ │  │ • Multi-Backend VoiceDirector        │   │
│  │ • 9-Dimension Editorial Scorecard   │  │ │  │ • Acoustic Automated VoiceQA Engine  │   │
│  │ • Top Angle Selector & Rationale    │  │ │  │ • 4-Act Script Generator & Aligner   │   │
│  │ • Hook Ideation & Narrative Planner │  │ │  └──────────────────────────────────────┘   │
│  └─────────────────────────────────────┘  │ │  ┌──────────────────────────────────────┐   │
│  ┌─────────────────────────────────────┐  │ │  │             src/assets/              │   │
│  │            src/creator/             │  │ │  │ • Tier 1 SHA-256 Byte Deduplication  │   │
│  │ • Creator DNA Model (6 Components)  │  │ │  │ • Tier 2 dHash Perceptual Hashing    │   │
│  │ • Performance & Negative Memory     │  │ │  │ • Asset Freezer & Provenance Ledger  │   │
│  └─────────────────────────────────────┘  │ │  └──────────────────────────────────────┘   │
└───────────────────────────────────────────┘ └────────────────────────────────────────────┘
                     │                                               │
                     └───────────────────────┬───────────────────────┘
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                       LAYER 5: QUALITY OS, ECONOMICS & SECURITY                          │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │     src/evaluation/     │  │      src/creator/       │  │      src/security/       │  │
│  │ • ContentBench Framework│  │ • Creator Economics     │  │ • CapabilityToken Engine │  │
│  │ • 4-Layer Quality OS    │  │ • Itemized Cost Ledger  │  │ • Calculus: P_p ∩ P_r ∩ P│  │
│  │   (Research/Script/     │  │   (LLM/TTS/GPU/Storage) │  │ • Sandboxed Guard Jail   │  │
│  │    Video/Economics)     │  │ • Unit Margin Analytics │  │ • HMAC-SHA256 Signatures │  │
│  └─────────────────────────┘  └─────────────────────────┘  └──────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Breakdown & Contracts

### 3.1 Orchestration & State Machine (`src/orchestrator/`)
- **Deterministic Transition Graph**: Enforces the canonical state sequence:
  $$\text{CREATED} \to \text{RESEARCH\_PLANNED} \to \dots \to \text{RENDER\_COMPLETED} \to \text{COMPLETED}$$
- **State Guards**: Validates prerequisite state outputs before advancing. Any attempt to skip states (e.g. `CREATED` to `SCRIPT_COMPLETED`) raises `StateTransitionError`.
- **Audit Persistence**: Every transition appends a `TransitionRecord` with millisecond timing, payload digest, and actor metadata to `transition_history.json`.

### 3.2 Production Contracts (`src/models/`)
- Built on `pydantic.BaseModel` (Pydantic v2).
- Exports 17 core contracts: `CreatorProfile`, `ContentBrief`, `ResearchPlan`, `ResearchDossier`, `SourceRecord`, `ClaimRecord`, `EditorialAngle`, `ContentOutline`, `Script`, `ScriptBeat`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`.
- All models provide atomic dual serialization: `.save(output_dir, base_name)` outputs both formatted `.json` and clean `.yaml`.

### 3.3 Editorial Intelligence Engine (`src/editorial/`)
- **Multi-Angle Ideation**: Generates 5 competing editorial angles (`contrarian`, `deep_dive`, `data_led`, `human_narrative`, `future_impact`) for the topic dossier.
- **9-Dimension Scorecard**: Evaluates candidate angles across 9 criteria with weights summing to $1.0$:
  $$S_{\text{angle}} = 0.15 A_{\text{relevance}} + 0.15 N_{\text{novelty}} + 0.15 H_{\text{hook}} + 0.10 P_{\text{narrative}} + 0.10 C_{\text{creator}} + 0.10 E_{\text{evidence}} + 0.10 V_{\text{visual}} + 0.10 P_{\text{platform}} + 0.05 (1 - R_{\text{saturation}})$$
- **Hook & Outline Generation**: Synthesizes 3 hook variations and generates a 4-act narrative structure (`The Hook`, `The Barrier`, `The Breakthrough`, `The Ripple Effect`).

### 3.4 Media Synthesis, Audio & Assets (`src/scriptwriting/`, `src/assets/`)
- **VoiceDirector**: Multi-provider audio router dynamically switching between ElevenLabs API, OpenAI Audio, Windows SAPI, and deterministic Harmonic WAV synthesis based on availability and cost profiles.
- **VoiceQA Engine**: Analyzes generated 16-bit PCM audio waveforms for dead air ($<-45\text{ dBFS}$, $>300\text{ms}$), clipping ($|s| \ge 32767$, ratio $<0.01\%$), loudness consistency ($\Delta \text{RMS} \le 2.5\text{ dBFS}$), and speech-beat sync drift ($\le 0.20\text{s}$).
- **Two-Tier Deduplication**: Tier 1 SHA-256 exact matching prevents duplicate downloads; Tier 2 `dHash` (64-bit difference hash) prevents visual near-duplicates ($d_H \le 4$).

### 3.5 HyperFrames Integration (`adapters/hyperframes/`, `src/hyperframes/`)
- **H9 Component Registry**: Parameterized reusable visual blocks (`ReferenceCollageHook`, `SplitScreenIntro`, `QuoteHighlight`, `TimelineReveal`, `StatisticReveal`, `ComparisonPanel`, `CreatorBottomCollage`).
- **Deterministic GSAP Protocol**: Generates structured HTML5/CSS3 and registers timelines on `window.__timelines["root"]`.
- **Composition Linter**: Verifies zero remote URL dependencies, finite loop bounds, and responsive safe zones before triggering headless Chromium capture.

### 3.6 Security Capability Token Model (`src/security/`)
- **Token Engine**: Issues HMAC-SHA256 signed capability tokens binding:
  - Subject ID and Role
  - Allowed Tool Whitelist
  - Allowed Filesystem Write/Read Path Sandboxes
  - Allowed Network Egress Whitelist
  - UTC Expiration Timestamp & Max Delegation Depth
- **Calculus**: Child permissions are strictly computed as set intersections:
  $$\mathcal{P}_{\text{child}} = \mathcal{P}_{\text{parent}} \cap \mathcal{P}_{\text{role}} \cap \mathcal{P}_{\text{workflow}}$$
- **Security Guard**: Intercepts tool execution, file I/O, and network requests, enforcing sandbox jails and raising `PermissionDeniedError` or `PathTraversalError` upon violation.

---

## 4. End-to-End Execution Flow

```
1. Client / Hermes Agent ──► Issue Root Capability Token (src/security/)
2. Client ──► ContentBrief ──► Orchestrator (CREATED)
3. Orchestrator ──► Derive Child Token (Researcher) ──► Query Sources & Extract Claims
4. State Machine ──► RESEARCH_COMPLETED (ResearchDossier)
5. Orchestrator ──► Derive Child Token (Editorial) ──► Generate 5 Angles & 9-Dim Scoring
6. State Machine ──► ANGLE_SELECTED (Winning Angle + ContentOutline)
7. Orchestrator ──► Scriptwriter ──► SCRIPT_COMPLETED (Script + Beats)
8. Orchestrator ──► VoiceDirector ──► Synthesize Narration WAV
9. VoiceQA Engine ──► Inspect Waveform ──► VOICE_QA_PASSED
10. Asset Freezer ──► SHA-256 + dHash Dedup ──► ASSETS_FROZEN (AssetLedger)
11. HyperFrames ──► Render HTML/GSAP ──► Lint Check ──► COMPOSITION_GENERATED
12. Playwright / FFmpeg ──► Render MP4 ──► RENDER_COMPLETED (RenderArtifact)
13. ContentBench ──► 4-Layer Scoring ──► COMPLETED (PublishPackage + CostLedger)
```

---

## 5. Security & Isolation Architecture

```
                       ┌───────────────────────────────┐
                       │     Master Security Guard     │
                       │  (HMAC Secret + Egress Rules) │
                       └───────────────┬───────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│ Researcher Jail │           │ Script/TTS Jail │           │  Renderer Jail  │
│ Tools: [search] │           │ Tools: [tts]    │           │ Tools: [render] │
│ Path: /research │           │ Path: /audio    │           │ Path: /renders  │
│ Net: [wikimedia]│           │ Net: [elevenlab]│           │ Net: [OFFLINE]  │
└─────────────────┘           └─────────────────┘           └─────────────────┘
```

1. **Jail Isolation**: Each stage runs within a restricted directory prefix (`output/{project_id}/{stage}/`). Path resolution validates that normalized targets do not escape via `../` relative traversals.
2. **Network Egress Boundaries**: Rendering and assembly stages run with `OFFLINE_ONLY` egress policy, strictly blocking socket creation to prevent telemetry or data exfiltration.
3. **Secret Isolation**: API credentials for cloud providers (ElevenLabs, OpenAI) are accessed exclusively via runtime environment variables and never logged or serialized into JSON contracts.
