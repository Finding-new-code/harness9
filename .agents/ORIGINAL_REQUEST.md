# Original User Request

## 2026-08-31T15:04:20Z

Complete all remaining and incomplete implementation, integration, and verification tasks for the Harness 9 codebase according to the Head of Engineering's architecture and engineering plan: verify and finalize the decoupled architecture, 17-state machine, editorial intelligence (multi-angle generation and 9-dimension evaluation), HyperFrames adapter & component registry, multi-backend voice director & QA, creator memory & economics engine, capability permission tokens, ContentBench evaluation suite, and comprehensive engineering specifications and ADRs.

Working directory: g:\Finding-new-code\harness9
Integrity mode: development

## Requirements

### R1. State Machine, Production Contracts & Hermes Adapter
Implement and verify the 17-state production lifecycle state machine (CREATED through COMPLETED), comprehensive Pydantic production schemas (incorporating CreatorProfile, ContentBrief, ResearchPlan, ResearchDossier, SourceRecord, ClaimRecord, EditorialAngle, ContentOutline, Script, ScriptBeat, AssetRequirement, AssetRecord, EvaluationReport, RenderArtifact, PublishPackage, AnalyticsSnapshot, LearningCandidate), and the isolated adapters/hermes/ compatibility layer with docs/HERMES_COMPATIBILITY.md.

### R2. Editorial Intelligence & Multi-Angle Decision Engine
Build and verify the editorial engine (src/editorial/ or packages/editorial/) featuring multi-angle generation (generating candidate angles, independent 9-dimension scoring across audience relevance, novelty, hook potential, narrative potential, creator fit, evidence availability, visual potential, platform fit, and saturation risk; selecting the top candidate), hook generation, and narrative planning before scriptwriting.

### R3. HyperFrames Adapter, Extension Pack & Reusable Component Registry
Build and verify the formal adapters/hyperframes/ integration interface and the H9 HyperFrames component registry (including reusable parameterized blocks for reference collage hook, split-screen intro, quote highlight, timeline reveal, statistic reveal, comparison panel, and creator bottom collage).

### R4. Voice Director, Voice QA & Asset Deduplication
Enhance and verify audio and media pipelines with a multi-provider VoiceDirector and automated VoiceQA (detecting dead air, gap duration, clipping, volume consistency, and speech-beat alignment) alongside multi-tiered asset deduplication (SHA-256 and perceptual hashing).

### R5. Creator DNA, Creator Economics & Quality OS (ContentBench)
Implement and verify the Creator DNA data model (Brand Constitution, Creator Preferences, Creator Skills, Creator Examples, Performance Memory, Negative Memory), the Creator Economics cost/revenue ledger, and the 4-layer evaluation framework (ContentBench) for objective quality scoring across research, script, video, and cost dimensions.

### R6. Security Capability Tokens & Engineering Documentation Suite
Enforce principle-of-least-privilege capability tokens (child_permission = parent ∩ role ∩ workflow) across pipeline execution and provide the full engineering documentation suite (PRD.md, ARCHITECTURE.md, SYSTEM_DESIGN.md, DATA_MODEL.md, API_CONTRACTS.md, WORKFLOW_SPEC.md, SECURITY_MODEL.md, SKILL_SPEC.md, CONNECTOR_SPEC.md, HYPERFRAMES_INTEGRATION.md, HERMES_COMPATIBILITY.md, CONTENTBENCH.md, EVOLUTION_SPEC.md, CREATOR_MEMORY.md, and Architecture Decision Records ADR-001 through ADR-005).

## Acceptance Criteria

### Architecture & Production Lifecycle
- [ ] The 17-state lifecycle state machine transitions deterministically across all stages and rejects invalid state jumps.
- [ ] All production contracts validate against strict Pydantic schemas without data loss.
- [ ] adapters/hermes/ isolates upstream Hermes interaction and includes docs/HERMES_COMPATIBILITY.md.

### Editorial Intelligence & HyperFrames Registry
- [ ] Editorial stage generates multiple candidate angles, evaluates them against the 9-dimension scorecard, and outputs the winning angle into the narrative outline.
- [ ] HyperFrames adapter (adapters/hyperframes/) and H9 component registry provide parameterized, lint-checked components.

### Voice QA & Asset Deduplication
- [ ] VoiceQA validates audio for clipping, dead air, and beat alignment, reporting quantitative metrics in the production summary.
- [ ] Asset deduplication prevents duplicate downloads using SHA-256 and content hashing.

### Creator DNA, Economics & ContentBench
- [ ] Creator DNA stores and applies creator rules, preferences, and negative memories.
- [ ] Production cost reports calculate granular itemized costs (LLM, research, TTS, rendering, storage).
- [ ] ContentBench evaluation framework runs test cases and produces multi-dimensional quality reports.

### Security & Verification
- [ ] Capability token engine prevents child agents or restricted steps from executing unauthorized tools (tested via permission boundary tests).
- [ ] All unit, integration, and E2E tests pass 100% across the test suite (pytest and verify_pipeline.py).
- [ ] Complete engineering documentation suite and ADRs (ADR-001 through ADR-005) are present and fully detailed.

## 2026-09-04T08:55:45Z

Refactor Harness 9 so that its content-production capabilities run directly through the full Hermes Agent runtime (agent loop, context engineering, skills, tools, MCP, provider/model routing, memory, subagents, permissions, sandbox, and cron) on branch dev, establishing a clean integration boundary (src/h9_runtime/) without duplicating or breaking either runtime.

Working directory: g:\Finding-new-code\harness9
Integrity mode: development

## Requirements

### R1. Architecture Audit & Runtime Boundary Interface
Perform an in-depth audit of current Hermes vs. H9 execution paths documented in docs/architecture/hermes-h9-runtime-coupling.md, including a full capability comparison matrix. Define clean runtime interface abstractions in src/h9_runtime/ (AgentRuntime, SkillRuntime, ToolRuntime, ModelRuntime, MemoryRuntime, ExecutionRuntime, ContentRuntime).

### R2. Hermes Capability Bridge & Native Tool Conversion
Implement the capability bridge in src/h9_runtime/bridge.py allowing H9 domain modules to request Hermes services. Expose H9 content capabilities (h9.research, h9.discover_assets, h9.generate_script, h9.render) as native Hermes model tools registered into the Hermes tool registry.

### R3. Native Hermes Skills & Production IR Seam
Package H9 domain workflows into native Hermes skills (skills/h9-research/, skills/h9-content-planning/, skills/h9-production/, skills/h9-hyperframes/) using existing Hermes skill conventions (SKILL.md). Introduce the typed Production IR seam between narrative planning and HyperFrames compilation.

### R4. Provider, Memory & Subagent Integration
Route H9 model execution requests through Hermes' provider abstraction by logical capability roles without hardcoded LLM backends. Interface creator and project memory (CreatorProfile, ContentProject, ProductionHistory) with Hermes memory infrastructure without competing persistence. Demonstrate delegation of multi-source research synthesis to an isolated Hermes subagent returning a structured ResearchDossier.

### R5. Sandbox, Permission & MCP Integration
Enforce Hermes permission and sandbox execution boundaries on all H9 operations (web research, asset downloading, rendering subprocess, filesystem writes). Enable H9 to consume Hermes MCP capabilities via the native Hermes tool/runtime layer.

### R6. Acceptance & Regression Verification Suite
Implement an integration test suite covering the 8 required acceptance dimensions (runtime coupling, skill coupling, provider coupling, tool coupling, subagent coupling, permission coupling, sandbox coupling, and end-to-end video artifact generation). Ensure zero regressions across existing Hermes and H9 test suites. Author final audit report in docs/architecture/hermes-h9-integration-audit.md.

## Acceptance Criteria

### Architecture Audit & Boundary
- [ ] Architecture audit document docs/architecture/hermes-h9-runtime-coupling.md exists with full capability comparison table and call graph diagrams.
- [ ] Runtime interface definitions in src/h9_runtime/ allow H9 content services to request Hermes capabilities without importing internal implementation details everywhere.

### Tools & Skills
- [ ] H9 content tools (h9.research, h9.discover_assets, h9.generate_script, h9.render) are registered in Hermes tool registry and invokable by Hermes Agent.
- [ ] Hermes-native skills (skills/h9-research/, skills/h9-content-planning/, skills/h9-production/, skills/h9-hyperframes/) are discoverable and loadable by Hermes.
- [ ] Typed Production IR interface connects script/storyboard planning to the HyperFrames compiler.

### Providers, Memory & Subagents
- [ ] Model inference in H9 requests logical capability execution through the Hermes provider system rather than direct client initialization.
- [ ] H9 creator and project memory stores and retrieves state using Hermes memory infrastructure.
- [ ] Research phase delegates to an isolated Hermes subagent and receives a structured ResearchDossier.

### Permissions, Sandbox & MCP
- [ ] Permission tests verify that restricted agents or execution scopes cannot call unauthorized H9 tools (e.g., render or publish).
- [ ] Subprocess execution for HyperFrames rendering respects Hermes sandbox policies.
- [ ] H9 operations can discover and call tools provided via Hermes MCP integration.

### Verification & Regression
- [ ] End-to-end integration test passes: a content creation request submitted through the Hermes Agent runtime executes through H9 skills, tools, and subagents to render a valid MP4 video.
- [ ] Tests covering all 8 acceptance dimensions (A through H) pass.
- [ ] Full regression suite passes without regression.
- [ ] Final integration audit report is published at docs/architecture/hermes-h9-integration-audit.md.

## 2026-09-04T17:41:55Z

Complete the remaining and undone tasks for the Hermes x Harness 9 Runtime Coupling on branch dev in g:\Finding-new-code\harness9: build upon completed Milestone 1 (src/h9_runtime/ and docs/architecture/hermes-h9-runtime-coupling.md) to deliver the Hermes Capability Bridge (src/h9_runtime/bridge.py), native Hermes model tools (tools/h9_content_tools.py), native skills (skills/h9-*/), Production IR seam, provider/memory/subagent integration, permission & sandbox enforcement, 8-dimension acceptance test suite (A through H), regression verification, and the final audit report (docs/architecture/hermes-h9-integration-audit.md).

Working directory: g:\Finding-new-code\harness9
Integrity mode: development

## Requirements

### R1. Architecture Audit & Runtime Boundary Interface (COMPLETED)
- [x] In-depth audit in docs/architecture/hermes-h9-runtime-coupling.md with capability comparison matrix.
- [x] Protocol abstractions implemented in src/h9_runtime/ (AgentRuntime, SkillRuntime, ToolRuntime, ModelRuntime, MemoryRuntime, ExecutionRuntime, ContentRuntime).
- [x] Unit test suite in tests/test_h9_runtime.py passing.

### R2. Hermes Capability Bridge & Native Tool Conversion (ACTIVE)
Implement the capability bridge in src/h9_runtime/bridge.py allowing H9 domain modules to request Hermes services. Expose H9 content capabilities (h9.research, h9.discover_assets, h9.generate_script, h9.render) as native Hermes model tools registered into the Hermes tool registry (tools/h9_content_tools.py).

### R3. Native Hermes Skills & Production IR Seam
Package H9 domain workflows into native Hermes skills (skills/h9-research/, skills/h9-content-planning/, skills/h9-production/, skills/h9-hyperframes/) using existing Hermes skill conventions (SKILL.md). Introduce the typed Production IR seam between narrative planning and HyperFrames compilation.

### R4. Provider, Memory & Subagent Integration
Route H9 model execution requests through Hermes' provider abstraction by logical capability roles without hardcoded LLM backends. Interface creator and project memory (CreatorProfile, ContentProject, ProductionHistory) with Hermes memory infrastructure without competing persistence. Demonstrate delegation of multi-source research synthesis to an isolated Hermes subagent returning a structured ResearchDossier.

### R5. Sandbox, Permission & MCP Integration
Enforce Hermes permission and sandbox execution boundaries on all H9 operations (web research, asset downloading, rendering subprocess, filesystem writes). Enable H9 to consume Hermes MCP capabilities via the native Hermes tool/runtime layer.

### R6. Acceptance & Regression Verification Suite
Implement an integration test suite covering the 8 required acceptance dimensions (runtime coupling, skill coupling, provider coupling, tool coupling, subagent coupling, permission coupling, sandbox coupling, and end-to-end video artifact generation). Ensure zero regressions across existing Hermes and H9 test suites. Author final audit report in docs/architecture/hermes-h9-integration-audit.md.

## Acceptance Criteria

### Tools & Skills
- [ ] H9 content tools (h9.research, h9.discover_assets, h9.generate_script, h9.render) are registered in Hermes tool registry and invokable by Hermes Agent.
- [ ] Hermes-native skills (skills/h9-research/, skills/h9-content-planning/, skills/h9-production/, skills/h9-hyperframes/) are discoverable and loadable by Hermes.
- [ ] Typed Production IR interface connects script/storyboard planning to the HyperFrames compiler.

### Providers, Memory & Subagents
- [ ] Model inference in H9 requests logical capability execution through the Hermes provider system rather than direct client initialization.
- [ ] H9 creator and project memory stores and retrieves state using Hermes memory infrastructure.
- [ ] Research phase delegates to an isolated Hermes subagent and receives a structured ResearchDossier.

### Permissions, Sandbox & MCP
- [ ] Permission tests verify that restricted agents or execution scopes cannot call unauthorized H9 tools (e.g., render or publish).
- [ ] Subprocess execution for HyperFrames rendering respects Hermes sandbox policies.
- [ ] H9 operations can discover and call tools provided via Hermes MCP integration.

### Verification & Regression
- [ ] End-to-end integration test passes: a content creation request submitted through the Hermes Agent runtime executes through H9 skills, tools, and subagents to render a valid MP4 video.
- [ ] Tests covering all 8 acceptance dimensions (A through H) pass.
- [ ] Full regression suite passes without regression.
- [ ] Final integration audit report is published at docs/architecture/hermes-h9-integration-audit.md.

## 2026-09-10T13:36:42Z

Complete the remaining and undone tasks for the Hermes × Harness 9 Runtime Coupling on branch `dev` in `g:\Finding-new-code\harness9`: resolve all 26 failing tests and 4 errors in the 8-dimension acceptance suite `tests/test_h9_acceptance.py`, ensure zero regressions across existing test suites, and author the comprehensive final integration audit report at `docs/architecture/hermes-h9-integration-audit.md`.

Working directory: g:\Finding-new-code\harness9
Integrity mode: development

## Requirements

### R1. Acceptance Suite Defect Remediation across Dimensions A–H
Resolve all failing tests and errors in `tests/test_h9_acceptance.py` to achieve 44/44 passing tests across all 8 acceptance dimensions:
- **Dimension A (Runtime Coupling & Typed Contracts):** Fix unified facade protocol implementations and contract serialization invariants in `src/h9_runtime/bridge.py` and `src/models/contracts.py`.
- **Dimension B (Skill Coupling & Production IR Seam):** Fix Production IR AST schema validation, script/asset-to-IR AST compilation, and HyperFrames compiler bundle generation in `src/models/ir.py`.
- **Dimension C (Provider Coupling & Fallback Chains):** Align structured Pydantic schema enforcement across logical roles and verify provider fallback resilience.
- **Dimension D (Tool Coupling):** Fix OpenAI function schemas in `tools/h9_content_tools.py`, verify genuine handler execution, and ensure robust error handling and parameter sanitization.
- **Dimension E (Subagent Coupling):** Fix subagent spawning, context isolation, tool scoping, prompt cache stability, and verified `ResearchDossier` returns via `bridge.delegate_research()`.
- **Dimension F (Permission Coupling):** Align `create_root_token()` and token derivation parameters (`subject` / `subject_id` compatibility), HMAC-SHA256 verification, expiration detection, privileged tool gating, and active cascading revocation in `src/security/tokens.py`.
- **Dimension G (Sandbox Coupling):** Fix `download_stream_sandboxed()` parameter alignment (`destination_path`), process group isolation, and sandboxed subprocess routing for HyperFrames rendering.
- **Dimension H (End-to-End Artifact Generation):** Fix end-to-end video artifact generation (`bridge.delegate_research`, `bridge.publish` manifest return schema with `success`), and multi-dimensional governance coordination.

### R2. Regression Verification
Run the entire Hermes × H9 test suite (`tests/test_h9_runtime.py`, `tests/test_h9_content_tools.py`, `tests/test_h9_skills_and_ir.py`, `tests/test_h9_provider_memory_subagent.py`, `tests/test_h9_m5_sandbox_permission_mcp.py`, `tests/test_state_machine.py`, `tests/test_contracts.py`, `tests/test_editorial.py`, `tests/test_deduplication.py`, `tests/test_economics.py`, `tests/test_security_tokens.py`, etc.) ensuring 100% pass rate with zero regressions.

### R3. Final Integration Audit Report
Author the comprehensive final integration audit report at `docs/architecture/hermes-h9-integration-audit.md` providing forensic documentation of:
- Full capability matrix comparing standalone H9 vs. Hermes runtime coupled H9.
- Boundary interface architecture (`src/h9_runtime/`).
- Native model tools and skill catalog (`tools/h9_content_tools.py`, `skills/h9-*/`).
- Production IR specification and HyperFrames compilation seam.
- Provider, memory, subagent, permission, and sandbox governance.
- Empirical acceptance test results across all 8 dimensions (A through H) with zero-regression confirmation.

## Acceptance Criteria

### Acceptance Suite (tests/test_h9_acceptance.py)
- [ ] All 44 tests in `tests/test_h9_acceptance.py` pass cleanly (0 failures, 0 errors).
- [ ] Dimension A: Protocol conformance and contract serialization verified.
- [ ] Dimension B: Production IR compilation and bundle generation verified.
- [ ] Dimension C: Logical provider roles and fallback resilience verified.
- [ ] Dimension D: Model tool schemas and handlers verified.
- [ ] Dimension E: Isolated subagent research delegation verified.
- [ ] Dimension F: Capability token calculus, least-privilege, and cascading revocation verified.
- [ ] Dimension G: Sandboxed execution, streaming byte limits, and subprocess isolation verified.
- [ ] Dimension H: Autonomous end-to-end MP4 rendering and publication manifest generation verified.

### Regression Suite
- [ ] Full regression suite passes with 0 regressions.

### Documentation & Audit Report
- [ ] `docs/architecture/hermes-h9-integration-audit.md` is authored, comprehensive, and accurate.
