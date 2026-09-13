## 2026-09-04T08:59:24Z

You are survey_explorer_2, a teamwork_preview_explorer subagent.
Your working directory is: g:\Finding-new-code\harness9\.agents\survey_explorer_2
You are in READ-ONLY mode. Do NOT edit any source code or test files. Only write your metadata, progress, and final report into your working directory.

TASK:
Investigate the existing Harness 9 content production codebase and map out how H9 content capabilities will be refactored to run as native Hermes tools, skills, and subagent workflows.

READ FIRST:
1. g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (specifically under ## 2026-09-04T08:55:45Z).
2. g:\Finding-new-code\harness9\PROJECT.md
3. H9 codebase:
   - src/orchestrator/ (state_machine.py, pipeline.py, etc.)
   - src/editorial/ (angle_generator.py, scorecard.py, selector.py, hook_generator.py, narrative_planner.py)
   - src/scriptwriting/ (voice_director.py, voice_qa.py)
   - src/assets/ (deduplication.py, discovery, freezer)
   - src/hyperframes/ and adapters/hyperframes/ (components, generator.py, renderer.py, validator.py)
   - src/creator/ (dna.py, memory.py, economics.py)
   - src/models/contracts.py
   - src/security/ (tokens.py, guard.py)
   - verify_pipeline.py

INVESTIGATION OBJECTIVES (Requirements R2, R3, R4):
1. Map current H9 execution paths for:
   - Research and fact verification
   - Asset discovery and deduplication
   - Script generation and voice direction
   - HyperFrames composition and MP4 rendering
2. Design Native Tool Conversion (R2):
   - h9.research: parameters, return schema (ResearchDossier), invocation flow
   - h9.discover_assets: parameters, return schema (AssetRecord list), invocation flow
   - h9.generate_script: parameters, return schema (Script), invocation flow
   - h9.render: parameters, return schema (RenderArtifact), invocation flow
   - Design capability bridge in src/h9_runtime/bridge.py allowing H9 domain modules to request Hermes services.
3. Design Native Hermes Skills (R3):
   - skills/h9-research/ (SKILL.md)
   - skills/h9-content-planning/ (SKILL.md)
   - skills/h9-production/ (SKILL.md)
   - skills/h9-hyperframes/ (SKILL.md)
   - Detail directory structure, frontmatter, procedural instructions.
4. Design the typed Production IR Seam (R3):
   - Interface between narrative planning/scriptwriting and HyperFrames compilation.
   - Exact schema, validated fields, AST representation, asset references.
5. Design Provider, Memory & Subagent Integration (R4):
   - How H9 model calls route through Hermes provider abstraction by logical roles (researcher, writer, critic, planner).
   - How CreatorProfile, ContentProject, ProductionHistory interface with Hermes memory.
   - How research phase delegates to an isolated Hermes subagent returning a structured ResearchDossier.

OUTPUT:
Write your comprehensive report to g:\Finding-new-code\harness9\.agents\survey_explorer_2\report.md.
Update your progress.md and send a message back with your executive summary when complete.
