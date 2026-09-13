## 2026-09-04T08:59:24Z

You are survey_test_explorer_3, a teamwork_preview_explorer subagent.
Your working directory is: g:\Finding-new-code\harness9\.agents\survey_test_explorer_3
You are in READ-ONLY mode. Do NOT edit any source code or test files. Only write your metadata, progress, and final report into your working directory.

TASK:
Investigate existing test suites, test infrastructure, regression verification baselines, and design the acceptance and regression verification suite for the Harness 9 refactoring.

READ FIRST:
1. g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (specifically under ## 2026-09-04T08:55:45Z).
2. g:\Finding-new-code\harness9\PROJECT.md
3. Existing test suite in tests/ (list and inspect all test files, test_e2e_pipeline.py, test_hermes_adapter.py, etc.).
4. verify_pipeline.py and how tests are executed.

INVESTIGATION OBJECTIVES (Requirements R1, R6):
1. Audit the 8 required acceptance dimensions (A through H):
   - Dimension A: Runtime Coupling (H9 content services request Hermes capabilities strictly via src/h9_runtime/ interfaces without internal Hermes private imports)
   - Dimension B: Skill Coupling (Hermes-native skills in skills/h9-* discoverable, valid SKILL.md, executable)
   - Dimension C: Provider Coupling (H9 requests logical capability execution through Hermes provider system, no hardcoded LLM clients)
   - Dimension D: Tool Coupling (Native Hermes tools h9.research, h9.discover_assets, h9.generate_script, h9.render registered in registry and callable)
   - Dimension E: Subagent Coupling (Delegation of multi-source research synthesis to isolated Hermes subagent returning ResearchDossier)
   - Dimension F: Permission Coupling (Capability tokens and permission checks prevent restricted scopes from calling unauthorized tools)
   - Dimension G: Sandbox Coupling (Subprocess rendering, filesystem, and network operations respect Hermes sandbox policies)
   - Dimension H: End-to-End Video Artifact Generation (Full pipeline from user creation request to valid MP4 video artifact)
2. Map baseline regression tests:
   - What existing tests exist in tests/?
   - Are there any existing tests that might break during the refactoring?
   - How can we run tests fast and reliably (e.g. pytest, python -m unittest, uv run)?
3. Documentation Requirements:
   - Audit requirements for docs/architecture/hermes-h9-runtime-coupling.md (capability comparison table, call graphs).
   - Audit requirements for docs/architecture/hermes-h9-integration-audit.md (final audit report).
4. Concrete test architecture and test case catalog plan across all 8 dimensions.

OUTPUT:
Write your comprehensive report to g:\Finding-new-code\harness9\.agents\survey_test_explorer_3\report.md.
Update your progress.md and send a message back with your executive summary when complete.

## 2026-09-04T09:08:59Z

Sender: dba72588-b963-4d76-af7f-a4dfb2b69d51
**Context**: Phase 0 Survey on Verification & Regression Baseline.
**Content**: Both survey_spec_miner_1 and survey_explorer_2 have completed their survey reports. Please report your current status, progress on auditing the 8 acceptance dimensions (A through H) and baseline test discovery.
**Action**: Update your progress.md and report your current status or blockers.
