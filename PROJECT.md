# Project: Harness 9 Studio OS

## Architecture
Harness 9 is a decoupled, deterministic, high-integrity autonomous content studio OS built with strict contracts, isolated adapters, multi-angle editorial intelligence, parameterized visual blocks, multi-provider acoustic synthesis & QA, creator cognitive memory & economics, least-privilege capability security tokens, and a 4-layer quality evaluation benchmark (ContentBench).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Harness 9 Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. State Machine & Orchestrator (17 Canonical States CREATED -> COMPLETED) │
│  2. Production Contracts (17 Strict Pydantic v2 Schemas + H9BaseModel)      │
│  3. Hermes Agent Adapter Layer (adapters/hermes/ Sandbox, Bridge & Tools)   │
│  4. Editorial Engine (5 Archetypes, 9-Dimension Scorecard, 4-Act Planner)   │
│  5. HyperFrames Adapter & Registry (adapters/hyperframes/ + 7 Blocks)       │
│  6. Audio & Media Pipeline (VoiceDirector, 4-Gate VoiceQA, SHA-256/dHash)   │
│  7. Creator Memory & Economics (6-Part DNA, Trapezoidal Retention, Ledger)  │
│  8. ContentBench Quality OS (4 Evaluation Layers: Research/Script/Video/Cost)│
│  9. Security Capability Token Engine (P_child = P_parent ∩ P_role ∩ P_flow)  │
│ 10. Engineering Documentation Suite (14 Markdown Specs + 5 ADRs)           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | 17-State Lifecycle State Machine | Deterministic lifecycle CREATED -> COMPLETED with transition validation & audit log | M1 | Survey (R1) |
| 2 | 17 Pydantic Production Schemas | Strict contracts inheriting H9BaseModel with dual JSON/YAML serialization | M1 | Survey (R1) |
| 3 | Hermes Adapter & Sandbox | Isolated adapters/hermes/ with prompt caching invariants & session sandboxing | M1 | Survey (R1) |
| 4 | Hermes Compatibility Spec | Complete integration architecture documentation in docs/HERMES_COMPATIBILITY.md | M1 | Survey (R1) |
| 5 | Multi-Angle Generation | 5 canonical archetypes (Contrarian, Deep Dive, Data-Led, Human, Future) | M2 | Survey (R2) |
| 6 | 9-Dimension Scorecard | Independent 9-dimension scoring with weighted composite and penalty logic | M2 | Survey (R2) |
| 7 | Deterministic Winning Selector | Multi-factor tie-breaker and selection audit rationale generator | M2 | Survey (R2) |
| 8 | Psychological Hook Generator | Multi-variation hook ideation across 5 cognitive psychological triggers | M2 | Survey (R2) |
| 9 | 4-Act Narrative Planner | Deterministic 4-act outline planning scaled across total duration | M2 | Survey (R2) |
| 10 | HyperFrames Adapter Interface | adapters/hyperframes/ compiler and renderer producing RenderArtifact | M3 | Survey (R3) |
| 11 | Component Registry | Dynamic discovery, schema introspection, and registration of visual blocks | M3 | Survey (R3) |
| 12 | 7 Canonical Visual Blocks | Parameterized blocks: reference collage, split-screen, quote, timeline, stat, comparison, creator banner | M3 | Survey (R3) |
| 13 | Master Composition Generator | Hermetic HTML/CSS/GSAP composition builder with finite loops & media decoupling | M3 | Survey (R3) |
| 14 | Composition Static Linter | Auditing root tags, local asset integrity, zero external URLs, and contrast | M3 | Survey (R3) |
| 15 | Multi-Provider VoiceDirector | 4 TTS providers (ElevenLabs, OpenAI, SAPI, Harmonic), 12 emotions, WPM clamping | M4 | Survey (R4) |
| 16 | Automated VoiceQA | 4 acoustic quality gates (dead air, clipping, loudness variance, beat drift) | M4 | Survey (R4) |
| 17 | Multi-Tier Deduplication | Tier 1 SHA-256 byte exact + Tier 2 dHash perceptual Hamming distance <= 4 | M4 | Survey (R4) |
| 18 | Creator DNA Data Model | 6-part cognitive identity (Constitution, Prefs, Skills, Examples, Memory) | M5 | Survey (R5) |
| 19 | Creator Memory & Constraints | Trapezoidal retention integration, drop-off detection, negative constraint engine | M5 | Survey (R5) |
| 20 | Creator Economics Ledger | 5-category cost accounting (LLM, Research, TTS, Render, Storage), margin & CPM | M5 | Survey (R5) |
| 21 | ContentBench Quality OS | 4-layer evaluation OS (S_research, S_script, S_video, S_cost) composite scoring | M5 | Survey (R5) |
| 22 | Capability Token Engine | Mathematical calculus P_child = P_parent ∩ P_role ∩ P_workflow + HMAC signing | M6 | Survey (R6) |
| 23 | Runtime Security Guard | Sandboxed execution whitelisting tools, filesystem paths, and network egress | M6 | Survey (R6) |
| 24 | Engineering Documentation Suite | 14 formal specifications in docs/ covering all subsystems | M6 | Survey (R6) |
| 25 | Architecture Decision Records | Formal ADR-001 through ADR-005 in docs/adrs/ | M6 | Survey (R6) |
| 26 | Acceptance Verification Pipeline | 6-checkpoint acceptance runner verify_pipeline.py | M_E2E | Survey (E2E) |
| 27 | 4-Tier Comprehensive E2E Suite | 22 Features, Boundaries, Pairwise, Scenarios S1-S10 in tests/ | M_E2E | Survey (E2E) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | State Machine, Contracts & Hermes Adapter | R1: state_machine.py, contracts.py, adapters/hermes/, HERMES_COMPATIBILITY.md | none | DONE |
| M2 | Editorial Intelligence & Decision Engine | R2: angle_generator.py, scorecard.py, selector.py, hook_generator.py, narrative_planner.py | M1 | DONE |
| M3 | HyperFrames Adapter & Component Registry | R3: adapters/hyperframes/, 7 component blocks, generator.py, validator.py, renderer.py | M1, M2 | DONE |
| M4 | Voice Director, Voice QA & Deduplication | R4: voice_director.py, voice_qa.py, deduplication.py, asset ledger | M1 | DONE |
| M5 | Creator DNA, Economics & ContentBench | R5: dna.py, memory.py, economics.py, contentbench.py | M1, M2, M4 | DONE |
| M6 | Security Tokens & Documentation Suite | R6: tokens.py, guard.py, 14 docs, ADR-001 through ADR-005 | M1 | DONE |
| M7 | Final E2E Integration & 100% Test Verification | 100% test pass across all unit, component, integration, and E2E suites | M1-M6 | DONE |

## Interface Contracts
### Orchestrator ↔ State Machine
- `ProductionStateMachine.transition_to(target_state: ProductionState, payload: BaseModel) -> TransitionRecord`
- Raises `StateTransitionError` on illegal transition jump.

### Editorial ↔ Models
- `AngleGenerator.generate_candidates(dossier: ResearchDossier, brief: ContentBrief, creator: Optional[CreatorProfile]) -> List[EditorialAngle]`
- `EditorialScorer.score_angle(...) -> EditorialScorecard`
- `AngleSelector.select_winning_angle(angles: List[EditorialAngle]) -> Tuple[EditorialAngle, EditorialScorecard]`
- `NarrativePlanner.build_outline(winner: EditorialAngle, hook: HookOption, dossier: ResearchDossier, brief: ContentBrief, target_duration: float) -> ContentOutline`

### Scriptwriting ↔ Audio & QA
- `VoiceDirector.synthesize_narration(script: Script, output_path: str, voice_profile: Optional[VoiceProfile]) -> AudioNarration`
- `VoiceQA.analyze_audio(audio_path: str, script: Optional[Script]) -> VoiceQAReport`
- `VoiceQAReport.to_evaluation_report() -> EvaluationReport`

### Assets ↔ Deduplication
- `AssetDeduplicator.register_asset(file_path: str, media_type: str, asset_id: Optional[str]) -> DeduplicationResult`
- `DeduplicationResult.is_duplicate: bool`, `dhash_hamming_distance: int`

### HyperFrames ↔ Render
- `HyperFramesAdapter.compile_composition(script: Script, assets: List[AssetRecord], output_dir: str, format: str) -> HyperFramesProject`
- `HyperFramesRenderer.render_project(project: HyperFramesProject, output_mp4: str) -> RenderArtifact`

### Security Guard ↔ Tools & Execution
- `calculate_capability_token(parent: CapabilityToken, role: RolePermissions, workflow: WorkflowPermissions) -> CapabilityToken`
- `SecurityGuard.enforce_tool_execution(tool_name: str)`, `enforce_filesystem_access(path: str, mode: str)`, `enforce_network_egress(host: str)`

## Code Layout
- `src/orchestrator/`: State machine, pipeline execution, CLI
- `src/models/`: Pydantic production contracts and backwards compatibility models
- `src/editorial/`: Multi-angle generator, 9-dimension scorecard, selector, hook ideator, narrative planner
- `src/hyperframes/`: 7 visual component blocks, generator, renderer, validator
- `src/scriptwriting/`: Multi-provider voice director, acoustic voice QA, alignment
- `src/assets/`: 2-tier deduplication, asset freezer, media discovery, procedural generator
- `src/creator/`: Creator DNA, cognitive performance & negative memory, economics cost ledger
- `src/evaluation/`: ContentBench 4-layer quality OS benchmark
- `src/security/`: Capability token engine, HMAC signing, runtime security guard
- `adapters/hermes/`: Hermes Agent sandbox, bridge, and service-gated tools
- `adapters/hyperframes/`: HyperFrames compiler, renderer adapter, and component registry
- `docs/`: 14 engineering specifications and `docs/adrs/` (ADR-001 to ADR-005)
- `tests/`: Full unit, integration, boundary, and 4-tier E2E test suites
