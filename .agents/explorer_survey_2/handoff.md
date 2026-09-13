# Handoff Report: Requirements R1, R2, and R3 Investigation

**Author:** explorer_survey_2  
**Date:** 2026-08-31  
**Target:** Parent Orchestrator / Implementers  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\explorer_survey_2`  
**Artifact Reference:** `g:\Finding-new-code\harness9\.agents\explorer_survey_2\analysis.md`  

---

## 1. Observation

Direct observations from examining the Harness 9 codebase:

1. **Current Pipeline Execution Model**:
   - `src/orchestrator/pipeline.py:55-256`: `Pipeline.run()` executes 5 stages in a sequential procedural loop (`research` at line 77, `assets` at line 111, `script_voiceover` at line 145, `hyperframes_render` at line 191, and `summary` at line 247).
   - There is no discrete state machine, no state enum, no transition graph, and no validation preventing out-of-order execution or invalid state jumps.

2. **Current Schema & Contract Implementation**:
   - `src/models/dossier.py:13-270`, `src/models/ledger.py:13-150`, `src/models/script.py:13-150`, `src/models/summary.py:13-108`: Data models are implemented as standard Python `@dataclass` classes with manual `.to_dict()` and `.from_dict()` serialization.
   - None of the models use Pydantic v2 `BaseModel`, and 13+ production contracts specified in the requirements are absent from `src/models/` (`CreatorProfile`, `ContentBrief`, `ResearchPlan`, `SourceRecord`, `ClaimRecord`, `EditorialAngle`, `ContentOutline`, `ScriptBeat`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`).

3. **Absence of Hermes Adapter**:
   - `find_by_name` for `*adapters*` and `grep_search` for `HERMES_COMPATIBILITY.md` confirmed that no `adapters/hermes/` directory or `docs/HERMES_COMPATIBILITY.md` file currently exists in the repository.

4. **Absence of Editorial Intelligence Engine**:
   - `src/scriptwriting/generator.py:1-527`: Script generation proceeds directly from research claims to hardcoded scene cards without multi-angle candidate generation, without 9-dimension scoring, and without a narrative planning step.
   - No `src/editorial/` or `packages/editorial/` package exists in the repository.

5. **Current HyperFrames Composition Engine**:
   - `src/hyperframes/generator.py:102-168`: The HTML composition generator emits a single hardcoded scene card structure (`<div class="scene">` containing `<div class="scene-background">` and `<div class="scene-content">`).
   - No `adapters/hyperframes/` adapter layer exists, and no reusable modular component blocks (such as `reference_collage_hook`, `split_screen_intro`, `quote_highlight`, `timeline_reveal`, `statistic_reveal`, `comparison_panel`, `creator_bottom_collage`) exist.

---

## 2. Logic Chain

1. **R1 State Machine & Contracts**:
   - *From Observation 1*: Because `src/orchestrator/pipeline.py` relies on an unverified procedural script, stages can fail silently or proceed with incomplete context if called directly.
   - *Therefore*: A formal 17-state deterministic lifecycle state machine (`ProductionStateMachine` with states `CREATED` through `COMPLETED`) must be implemented in `src/orchestrator/state_machine.py` to enforce deterministic stage transitions and reject invalid jumps.
   - *From Observation 2*: Because existing models in `src/models/` are untyped dataclasses missing 13+ contracts, schema guarantees cannot be enforced across pipeline boundaries.
   - *Therefore*: All 17 production contracts must be implemented in `src/models/contracts.py` as strict Pydantic v2 `BaseModel` classes, with backward-compatibility exports maintained in `src/models/__init__.py`.
   - *From Observation 3*: Because Hermes Agent requires sacred prompt caching, service-gated toolsets, and session isolation (as defined in `AGENTS.md`), Harness 9 must not mutate environment variables or leak state into the host process.
   - *Therefore*: An isolated `adapters/hermes/` compatibility package and `docs/HERMES_COMPATIBILITY.md` must be created.

2. **R2 Editorial Intelligence**:
   - *From Observation 4*: Without multi-angle ideation and objective scoring, scripts default to uniform narrative structures without optimizing for audience engagement or creator voice.
   - *Therefore*: `src/editorial/` must be introduced with `AngleGenerator` (5 distinct archetypes), `EditorialScorer` (evaluating 9 dimensions: audience relevance, novelty, hook potential, narrative potential, creator fit, evidence availability, visual potential, platform fit, and saturation risk), `HookGenerator` (3 hook variations), and `NarrativePlanner` (4-Act `ContentOutline`).

3. **R3 HyperFrames Adapter & Component Registry**:
   - *From Observation 5*: A single monolithic scene layout produces repetitive video compositions and lacks the visual dynamism required for broadcast-grade content.
   - *Therefore*: `adapters/hyperframes/` and `src/hyperframes/components/` must be implemented with 7+ parameterized blocks (`reference_collage_hook`, `split_screen_intro`, `quote_highlight`, `timeline_reveal`, `statistic_reveal`, `comparison_panel`, `creator_bottom_collage`), each implementing `render_html()`, `render_css()`, and deterministic GSAP `render_gsap()`.

---

## 3. Caveats

- **Scope Boundary**: This investigation focused exclusively on Requirements R1, R2, and R3. Requirements R4 (Voice Director & Asset Deduplication), R5 (Creator DNA, Economics & ContentBench), and R6 (Capability Tokens & Documentation Suite) are covered by peer survey agents.
- **Backward Compatibility**: Existing tests in `tests/test_research.py`, `tests/test_assets.py`, `tests/test_scriptwriting.py`, and `verify_pipeline.py` depend on the current signatures of `ResearchDossier`, `MediaAsset`, `Script`, and `PipelineSummary`. The Pydantic refactoring must maintain duck-typing/attribute compatibility (`.claims`, `.talking_points`, `.to_dict()`, `.save()`, `.load()`) to prevent regressions.

---

## 4. Conclusion

Requirements R1, R2, and R3 require the following concrete modules to be added to the codebase:
1. `src/orchestrator/state_machine.py`: 17-state deterministic lifecycle machine with transition enforcement.
2. `src/models/contracts.py`: 17 Pydantic v2 production contract models (`CreatorProfile`, `ContentBrief`, `ResearchPlan`, `ResearchDossier`, `SourceRecord`, `ClaimRecord`, `EditorialAngle`, `ContentOutline`, `Script`, `ScriptBeat`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`).
3. `adapters/hermes/`: Clean Hermes Agent integration bridge, session sandbox, and tool schema definitions + `docs/HERMES_COMPATIBILITY.md`.
4. `src/editorial/`: Multi-angle generator (5 archetypes), 9-dimension scorecard engine, winning angle selector, hook generator, and 4-act narrative planner.
5. `adapters/hyperframes/` & `src/hyperframes/components/`: HyperFrames adapter and 7+ parameterized reusable component blocks.

Full specifications, code snippets, schemas, and mathematical scoring models have been documented in `g:\Finding-new-code\harness9\.agents\explorer_survey_2\analysis.md`.

---

## 5. Verification Method

To independently verify the findings and subsequent implementations:

1. **State Machine Unit Tests**:
   ```bash
   pytest tests/test_state_machine.py -v
   ```
   - Assert all 17 valid transitions succeed in sequence.
   - Assert invalid transitions (e.g. `CREATED` -> `RENDER_COMPLETED`) raise `ValueError`.

2. **Editorial Engine Unit Tests**:
   ```bash
   pytest tests/test_editorial.py -v
   ```
   - Assert $\ge 3$ candidate angles are generated.
   - Assert all 9 scorecard dimensions are computed in $[0.0, 1.0]$.
   - Assert top angle selection correctly flags `selected=True` on the highest-scoring candidate.

3. **HyperFrames Components & Linter**:
   ```bash
   pytest tests/test_hyperframes_components.py -v
   ```
   - Assert all 7 component blocks render valid HTML, CSS, and GSAP timeline code.
   - Assert `validate_composition()` passes with zero errors in both 16:9 and 9:16 aspect ratios.

4. **Full Pipeline Acceptance Suite**:
   ```bash
   python verify_pipeline.py --test-mode
   pytest tests/test_e2e_pipeline.py -v
   ```
