## 2026-09-04T18:18:45Z
You are worker_m3_orch3, a teamwork_preview_worker implementing Milestone 3 of the Hermes x Harness 9 Runtime Coupling (Native Hermes Skills & Production IR Seam).

Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m3_orch3\
Create and maintain your own BRIEFING.md, progress.md, and handoff.md in your working directory.
Communicate updates and completion via send_message to your parent (Recipient: d832f8a0-ed17-43c0-91e0-f1ecca7ae126).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INPUTS — READ THESE FIRST:
1. g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (sections ## 2026-09-04T17:41:55Z and ## 2026-09-04T08:55:45Z, Requirement R3)
2. g:\Finding-new-code\harness9\.agents\survey_explorer_2\report.md (Section 4: "The Typed Production IR Seam" lines 748-960)
3. g:\Finding-new-code\harness9\.agents\survey_spec_miner_1\report.md (Section 2.2: "Hermes Skills Standard & Progressive Disclosure" lines 135-165)
4. Existing implementations:
   - g:\Finding-new-code\harness9\src\h9_runtime\skills.py (DefaultSkillRuntime)
   - g:\Finding-new-code\harness9\src\h9_runtime\bridge.py
   - g:\Finding-new-code\harness9\src\h9_runtime\content.py
   - g:\Finding-new-code\harness9\src\models\contracts.py
   - g:\Finding-new-code\harness9\adapters\hyperframes\
5. g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_3\PROJECT.md
6. g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_3\plan.md

YOUR EXCLUSIVE WRITE OWNERSHIP:
- g:\Finding-new-code\harness9\skills\h9-research\SKILL.md
- g:\Finding-new-code\harness9\skills\h9-content-planning\SKILL.md
- g:\Finding-new-code\harness9\skills\h9-production\SKILL.md
- g:\Finding-new-code\harness9\skills\h9-hyperframes\SKILL.md
- g:\Finding-new-code\harness9\src\models\ir.py
- g:\Finding-new-code\harness9\src\models\__init__.py (if exporting IR schemas)
- g:\Finding-new-code\harness9\src\h9_runtime\bridge.py (wire compile_production_ir to return ProductionIRDocument)
- g:\Finding-new-code\harness9\src\h9_runtime\content.py (wire compile_production_ir to return ProductionIRDocument)
- g:\Finding-new-code\harness9\tests\test_h9_skills_and_ir.py

DELIVERABLES & TASKS:
1. Implement `src/models/ir.py`:
   - Define strict Pydantic v2 AST schemas:
     - `IRBlockType` (enum with the 7 canonical visual blocks: reference_collage_hook, split_screen_intro, quote_highlight, timeline_reveal, statistic_reveal, comparison_panel, creator_bottom_collage).
     - `IRAssetReference` (asset_id, file_path, file_sha256, media_type, width, height, aspect_ratio, license_type, verified).
     - `IRSpeechBeat` (beat_id, start_time_sec, end_time_sec, text, emphasis_words, visual_trigger, duration_sec property).
     - `IRNarrationBlock` (full_text, voice_profile, target_wpm, speech_beats).
     - `IRAnimationTrack` (target_selector, property_name, from_value, to_value, start_offset_sec, duration_sec, easing).
     - `IRVisualBlockNode` (block_type, parameters, asset_bindings, animation_tracks).
     - `IRTransitionSpec` (entrance_type, exit_type, transition_duration_sec).
     - `IRSceneNode` (scene_id, scene_index, act_index, start_time_sec, duration_sec, narration, visual_block, transitions, end_time_sec property).
     - `IRAudioTrack` (audio_rel_path, total_duration_sec, sample_rate, channels).
     - `IRMetadata` (project_id, topic, title, aspect_ratio, fps, width, height, brand_primary_color, brand_background_color).
     - `ProductionIRDocument` (ir_version, generated_at, metadata, audio_track, asset_manifest, scenes).
   - Enforce AST invariants via `@model_validator(mode="after")`:
     - Temporal contiguity & conservation: `abs(scene.start_time_sec - expected_start) <= 0.05` across all scenes.
     - Audio duration matching: total scene duration matches `audio_track.total_duration_sec` within 0.5s.
     - Asset binding integrity: every `asset_id` referenced in `asset_bindings` must exist in `asset_manifest`.
     - Non-empty scenes validation.
   - Implement `compile_script_to_ir(script: Script, assets: List[AssetRecord], metadata: Optional[IRMetadata], audio_narration: Optional[AudioNarration]) -> ProductionIRDocument`.
   - Ensure `HyperFramesCompiler` / `HyperFramesAdapter` can consume `ProductionIRDocument`.
2. Implement 4 native Hermes skills under `skills/`:
   - `skills/h9-research/SKILL.md`: YAML frontmatter + structured instructions for autonomous multi-source research, claim verification, depth parameters, and output structuring into `ResearchDossier`.
   - `skills/h9-content-planning/SKILL.md`: YAML frontmatter + structured instructions for multi-angle ideation, 9-dimension editorial scorecard evaluation, hook selection, and 4-act narrative planning into `ContentOutline` and `Script`.
   - `skills/h9-production/SKILL.md`: YAML frontmatter + structured instructions for end-to-end studio OS execution, asset discovery, voice direction, acoustic QA, timeline compilation, and execution.
   - `skills/h9-hyperframes/SKILL.md`: YAML frontmatter + structured instructions for visual block selection, parameterization, Production IR compilation, and MP4 rendering.
   - Verify skill discovery: ensure `DefaultSkillRuntime` in `src/h9_runtime/skills.py` discovers all 4 skills.
3. Update `src/h9_runtime/bridge.py` and `src/h9_runtime/content.py`:
   - Wire `compile_production_ir` to construct and return a valid `ProductionIRDocument`.
4. Implement comprehensive test suite in `tests/test_h9_skills_and_ir.py`:
   - Skill discovery & loading: all 4 skills discoverable, valid YAML frontmatter, correct tags and metadata.
   - Production IR AST validation: valid documents pass; invalid documents (temporal gaps, audio drift, dangling asset references) raise validation errors.
   - Script to Production IR compilation: verifies genuine mapping from `Script` + `AssetRecord`s to `ProductionIRDocument`.
   - Production IR to HyperFrames compilation & rendering: verified end-to-end compilation into renderable format.
5. Run test verification with `.venv\Scripts\python.exe`:
   - `tests/test_h9_skills_and_ir.py`
   - `tests/test_h9_content_tools.py`
   - `tests/test_challenger_m2_stress.py`
   - `tests/test_h9_runtime.py`
   - `tests/tools/test_registry.py`
   Ensure 100% pass and zero regressions.
6. Write a detailed `handoff.md` and report completion via `send_message`.
