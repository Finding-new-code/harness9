# Workflow & 17-State Lifecycle Specification: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/orchestrator/state_machine.py`  
**Cross-References:** `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/adrs/ADR-001.md`  

---

## 1. Lifecycle Overview & Deterministic State Model

The Harness 9 production workflow is governed by a deterministic, non-skipping state machine comprised of **17 canonical sequential states** and **3 control/exception states**. Every state boundary represents an immutable contract exchange.

```
 [CREATED]
    │
    ▼
 [RESEARCH_PLANNED] ──► [RESEARCH_IN_PROGRESS] ──► [RESEARCH_COMPLETED]
                                                          │
                                                          ▼
 [OUTLINE_APPROVED] ◄── [ANGLE_SELECTED] ◄── [EDITORIAL_ANALYSIS]
    │
    ▼
 [SCRIPTING_IN_PROGRESS] ──► [SCRIPT_COMPLETED]
                                    │
                                    ▼
 [VOICE_QA_PASSED] ◄── [VOICE_GENERATED]
    │
    ▼
 [ASSETS_DISCOVERED] ──► [ASSETS_FROZEN]
                                │
                                ▼
 [RENDER_IN_PROGRESS] ◄── [COMPOSITION_GENERATED]
    │
    ▼
 [RENDER_COMPLETED] ──► [COMPLETED]
```

---

## 2. State Transition Matrix

| # | Current State | Allowed Target States | Required Input Payload | Output Artifact Generated |
|---|---|---|---|---|
| 1 | `CREATED` | `RESEARCH_PLANNED`, `FAILED`, `CANCELLED` | `ContentBrief` | `brief.json`, `brief.yaml` |
| 2 | `RESEARCH_PLANNED` | `RESEARCH_IN_PROGRESS`, `FAILED`, `CANCELLED` | `ResearchPlan` | `research_plan.json` |
| 3 | `RESEARCH_IN_PROGRESS` | `RESEARCH_COMPLETED`, `FAILED`, `CANCELLED` | Intermediate query results | `raw_sources.json` |
| 4 | `RESEARCH_COMPLETED` | `EDITORIAL_ANALYSIS`, `FAILED`, `CANCELLED` | `ResearchDossier` | `research_dossier.json` |
| 5 | `EDITORIAL_ANALYSIS` | `ANGLE_SELECTED`, `FAILED`, `CANCELLED` | List of `EditorialAngle` | `candidate_angles.json` |
| 6 | `ANGLE_SELECTED` | `OUTLINE_APPROVED`, `PAUSED_FOR_HUMAN`, `FAILED`, `CANCELLED` | Winning `EditorialAngle` | `selected_angle.json` |
| 7 | `OUTLINE_APPROVED` | `SCRIPTING_IN_PROGRESS`, `FAILED`, `CANCELLED` | `ContentOutline` (4 Acts) | `content_outline.json` |
| 8 | `SCRIPTING_IN_PROGRESS` | `SCRIPT_COMPLETED`, `FAILED`, `CANCELLED` | Scene drafts & beats | `draft_scenes.json` |
| 9 | `SCRIPT_COMPLETED` | `VOICE_GENERATED`, `FAILED`, `CANCELLED` | `Script` | `script.json`, `SCRIPT.md` |
| 10 | `VOICE_GENERATED` | `VOICE_QA_PASSED`, `SCRIPTING_IN_PROGRESS`, `FAILED`, `CANCELLED` | `AudioNarration` | `narration.wav` |
| 11 | `VOICE_QA_PASSED` | `ASSETS_DISCOVERED`, `FAILED`, `CANCELLED` | `VoiceQAReport` | `voice_qa_report.json` |
| 12 | `ASSETS_DISCOVERED` | `ASSETS_FROZEN`, `FAILED`, `CANCELLED` | Candidate `AssetRecord` list | `discovered_assets.json` |
| 13 | `ASSETS_FROZEN` | `COMPOSITION_GENERATED`, `FAILED`, `CANCELLED` | `AssetLedger` (SHA-256 + dHash) | `asset_ledger.json` |
| 14 | `COMPOSITION_GENERATED` | `RENDER_IN_PROGRESS`, `FAILED`, `CANCELLED` | `HyperFramesProject` | `index.html`, `timeline.js` |
| 15 | `RENDER_IN_PROGRESS` | `RENDER_COMPLETED`, `FAILED`, `CANCELLED` | Frame capture stream | `raw_frames/` or video stream |
| 16 | `RENDER_COMPLETED` | `COMPLETED`, `FAILED`, `CANCELLED` | `RenderArtifact` | `renders/final.mp4` |
| 17 | `COMPLETED` | *(Terminal State)* | `PublishPackage`, `CostLedger`, `BenchmarkReport` | `publish_package.json`, `cost_ledger.json` |

### Control & Error State Transitions:
- `PAUSED_FOR_HUMAN`: Can transition to `OUTLINE_APPROVED` (approval given), `EDITORIAL_ANALYSIS` (rejected, redo angles), or `CANCELLED`.
- `FAILED`: Can transition to `CREATED` or `PAUSED_FOR_HUMAN` upon manual diagnostic intervention.
- `CANCELLED`: Terminal state.

---

## 3. Step-by-Step State Lifecycle Invariants

### State 1: `CREATED`
- **Trigger**: Ingestion of `ContentBrief`.
- **Invariants**: `topic` must not be empty; `target_duration_seconds` must be between $5$ and $600$; workspace directory initialized with root capability token.

### State 2: `RESEARCH_PLANNED`
- **Trigger**: Extraction of core queries and claim goals.
- **Invariants**: `target_claim_count >= 1`; `search_queries` must contain at least 1 search tuple; timeout set.

### State 3: `RESEARCH_IN_PROGRESS`
- **Trigger**: Dispatching worker agents with `researcher` capability token.
- **Invariants**: Sandboxed network queries; domain authority tracked for each queried URL.

### State 4: `RESEARCH_COMPLETED`
- **Trigger**: Consolidation of claims into `ResearchDossier`.
- **Invariants**: Must contain $\ge 3$ verifiable claims; each claim has a valid `primary_source`; zero unverified conflicting assertions.

### State 5: `EDITORIAL_ANALYSIS`
- **Trigger**: Multi-angle generator dispatched.
- **Invariants**: Exactly 5 candidate angles generated spanning 5 archetypes (`contrarian`, `deep_dive`, `data_led`, `human_narrative`, `future_impact`); all evaluated against 9-dimension scorecard.

### State 6: `ANGLE_SELECTED`
- **Trigger**: Top candidate selected by score.
- **Invariants**: Winning angle composite score $\ge 0.70$; selection rationale recorded.

### State 7: `OUTLINE_APPROVED`
- **Trigger**: Hook selection and 4-act narrative structure compiled.
- **Invariants**: Acts 1 through 4 cover $0.0$ to $1.0$ normalized time duration without gaps.

### State 8: `SCRIPTING_IN_PROGRESS`
- **Trigger**: Scriptwriter compiles scene dialogue and visual descriptions.
- **Invariants**: Words mapped to estimated seconds ($145\text{ WPM}$); Creator Brand Constitution negative constraints checked.

### State 9: `SCRIPT_COMPLETED`
- **Trigger**: Final script validation.
- **Invariants**: Total word count matches target duration $\pm 10\%$; scene IDs mapped to storyboard visual components.

### State 10: `VOICE_GENERATED`
- **Trigger**: `VoiceDirector` synthesizes audio track.
- **Invariants**: Valid 16-bit PCM WAV generated; non-empty audio stream.

### State 11: `VOICE_QA_PASSED`
- **Trigger**: `VoiceQA` waveform inspection.
- **Invariants**: Dead air $<300\text{ms}$; clipping $<0.01\%$; loudness variance $\le 2.5\text{ dBFS}$; speech-beat drift $\le 0.20\text{s}$. If failed, transitions back to `SCRIPTING_IN_PROGRESS` for pacing adjustment.

### State 12: `ASSETS_DISCOVERED`
- **Trigger**: Media discovery queries executed for all scene asset requirements.
- **Invariants**: Every scene has at least 1 candidate visual asset matching required aspect ratio.

### State 13: `ASSETS_FROZEN`
- **Trigger**: Ingestion and deduplication.
- **Invariants**: SHA-256 calculated and verified; `dHash` distance $d_H > 4$ between all selected scene images; local file existence confirmed.

### State 14: `COMPOSITION_GENERATED`
- **Trigger**: HyperFrames HTML5/CSS3/GSAP compilation.
- **Invariants**: Composition linter passes 100%; zero broken local paths; zero external `http://` URLs; finite GSAP repeats.

### State 15: `RENDER_IN_PROGRESS`
- **Trigger**: Headless Playwright capture and FFmpeg pipeline start.
- **Invariants**: Frame capture rate 30 FPS; audio and video muxed into H.264/AAC MP4.

### State 16: `RENDER_COMPLETED`
- **Trigger**: Video render finish.
- **Invariants**: Output file non-empty; valid MP4 headers; duration matches script $\pm 0.5\text{s}$.

### State 17: `COMPLETED`
- **Trigger**: Production packaging and ContentBench benchmark audit.
- **Invariants**: `PublishPackage`, `ProductionCostLedger`, and `EvaluationReport` atomically written to disk; final state locked.

---

## 4. Rollback, Pause & Error Recovery Policies

1. **Deterministic Retry**: If a stage fails due to transient compute or network error, the state machine permits up to 3 automatic retries before transitioning to `FAILED`.
2. **Human-in-the-Loop Gate**: If `auto_approve=False`, the state machine halts at `ANGLE_SELECTED` or `SCRIPT_COMPLETED` and enters `PAUSED_FOR_HUMAN`, generating an interactive inspection payload.
3. **Rollback Safety**: State regressions are only permitted along defined remediation paths (e.g. `VOICE_GENERATED` $\to$ `SCRIPTING_IN_PROGRESS` for audio pacing correction). Arbitrary backward jumps are forbidden.
