# Handoff Report: survey_explorer_2

**Agent**: `survey_explorer_2` (teamwork_preview_explorer)  
**Parent Agent ID**: `dba72588-b963-4d76-af7f-a4dfb2b69d51`  
**Working Directory**: `g:\Finding-new-code\harness9\.agents\survey_explorer_2`  
**Report Path**: `g:\Finding-new-code\harness9\.agents\survey_explorer_2\report.md`  
**Type**: Hard Handoff (Investigation & Architecture Design Complete)

---

## 1. Observation
- **Research Path**: `ResearchEngine.synthesize_research` in `src/research/engine.py:34` matches keyword presets (`src/research/presets/*.yaml`) or expands 5 intent queries (`origin_history`, `technical_mechanism`, `quantitative_metric`, `modern_impact`, `visual_queries`) via `MultiProviderDispatcher` (`src/research/providers.py:27`), scoring claims with `score_claim` (`src/research/scoring.py:28`) and returning `ResearchDossier` (`src/models/contracts.py:239`).
- **Asset Path**: `AssetPipeline.discover_and_freeze_assets` in `src/assets/pipeline.py` executes multi-provider candidate discovery (`src/assets/discovery.py:18`), downloads/freezes local assets (`src/assets/freezer.py`), runs 2-tier deduplication (`src/assets/deduplication.py:34` - Tier 1 SHA-256 and Tier 2 64-bit perceptual dHash Hamming distance $\le 4$), generating `AssetProvenanceLedger` (`src/models/ledger.py:12`).
- **Script & Voice Path**: `EditorialEngine` in `src/editorial/__init__.py:35` evaluates 5 archetypes with the 9-dimension scorecard (`src/editorial/scorecard.py:20`) and 4-act narrative planner (`src/editorial/narrative_planner.py:25`). `ScriptwritingPipeline` in `src/scriptwriting/pipeline.py:36` and `VoiceDirector` in `src/scriptwriting/voice_director.py:45` support 4 TTS providers (ElevenLabs, OpenAI, SAPI, Harmonic WAV), emotional modulation, WPM rate clamping (90-220 WPM), followed by 4-gate `VoiceQA` (`src/scriptwriting/voice_qa.py:51`).
- **HyperFrames & Render Path**: `ComponentRegistry` (`adapters/hyperframes/registry.py:30`) manages 7 visual blocks (`src/hyperframes/components/`). `HyperFramesGenerator` (`src/hyperframes/generator.py:20`) builds HTML/CSS/GSAP compositions validated by `CompositionValidator` (`src/hyperframes/validator.py:19`) for zero external URLs. `HyperFramesRenderer` (`src/hyperframes/renderer.py:20`) drives headless Playwright into FFmpeg piping.
- **Hermes Runtime Invariants**: Defined in `AGENTS.md` and `tools/registry.py:763`: per-conversation prompt caching is sacred; core is a narrow waist (`_HERMES_CORE_TOOLS` protected); new tools live on the Footprint Ladder as service-gated named toolsets (`check_fn`); subagent delegation via `tools/delegate_tool.py:1` isolates context; memory persists via `USER.md`, `MEMORY.md`, and `SessionDB`.

---

## 2. Logic Chain
1. Current H9 operates as a monolithic pipeline in `adapters/hermes/bridge.py` running `Pipeline.run()`. This acts as an opaque black box, preventing Hermes agents from inspecting, iterating, or branching across stages.
2. Converting H9 capabilities into four granular native Hermes tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`) unlocks full interactive agent control while preserving prompt caching through static JSON schemas.
3. Placing these tools in a dedicated named toolset (`h9_content`) gated by `check_h9_available()` ensures zero token bloat in standard conversations, complying with the Hermes Footprint Ladder.
4. The semantic gap between creative narrative scripting (Markdown, beats) and low-level DOM/GSAP timelines is solved by introducing the typed Production IR Seam (`ProductionIRDocument`, `IRSceneNode`, `IRVisualBlockNode`), which acts as a validated AST enforcing temporal contiguity, asset binding integrity, and speech synchronization.
5. Delegating the research phase to an isolated Hermes subagent via `delegate_task` keeps massive raw search dumps out of the parent conversation, preserving the parent's prompt cache and token budget.
6. Abstracting LLM calls into 4 logical roles (`researcher`, `writer`, `critic`, `planner`) routed via Hermes's provider layer (`providers/`) eliminates hardcoded LLM backends and enables flexible model selection via `config.yaml`.

---

## 3. Caveats
- **Read-Only Scope**: In strict compliance with explorer instructions, no code or test files in `src/`, `adapters/`, `skills/`, or `tests/` were altered.
- **Renderer Dependencies**: Headless Chromium and system FFmpeg are required for broadcast MP4 output; procedural fallback mode is provided for environments lacking graphical or media binaries.
- **Subagent Auto-Approval**: Subagent execution requires `delegation.subagent_auto_approve: true` or non-interactive safe auto-denial to prevent CLI terminal deadlocks.

---

## 4. Conclusion
The architectural blueprint for refactoring Harness 9 into native Hermes tools, skills, production IR seam, and subagent delegation workflows is fully specified in `report.md`. The design fulfills Requirements R2, R3, and R4 with zero disruption to Hermes core prompt caching or the narrow waist.

---

## 5. Verification Method
- Inspect the complete architectural design report:
  `g:\Finding-new-code\harness9\.agents\survey_explorer_2\report.md`
- Run existing contract and state machine verification:
  `python -m pytest tests/test_production_contracts.py tests/test_state_machine.py -v`
- Verify pipeline end-to-end baseline:
  `python verify_pipeline.py --test-mode --output-dir output/test_verification_run`
