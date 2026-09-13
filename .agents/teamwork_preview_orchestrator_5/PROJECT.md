# Project: Harness 9 Refactoring & Hermes Agent Runtime Integration

## Architecture
Refactoring Harness 9 so that its content-production capabilities run directly through the full Hermes Agent runtime (agent loop, context engineering, skills, tools, MCP, provider/model routing, memory, subagents, permissions, sandbox, and cron) on branch `dev`, establishing a clean integration boundary (`src/h9_runtime/`) without duplicating or breaking either runtime.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Hermes Agent Core Runtime (Narrow Waist)                 │
│  AIAgent Loop │ Context / Caching │ MemoryManager │ Subagents │ Permissions │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Runtime Boundary (src/h9_runtime/)                     │
│  AgentRuntime │ SkillRuntime │ ToolRuntime │ ModelRuntime │ MemoryRuntime   │
│  ExecutionRuntime │ ContentRuntime │ CapabilityBridge (bridge.py)           │
└──────┬───────────────────────┬───────────────────────────────┬──────────────┘
       │                       │                               │
       ▼                       ▼                               ▼
┌──────────────┐      ┌─────────────────┐             ┌─────────────────┐
│ Native Tools │      │  Native Skills  │             │  Production IR  │
│  (Rung 3)    │      │ (skills/h9-*/)  │             │ (src/models/ir) │
│ h9.research  │      │ h9-research     │             │ SceneNode       │
│ h9.discover  │      │ h9-content-plan │             │ VisualBlockNode │
│ h9.gen_script│      │ h9-production   │             │ SpeechBeatNode  │
│ h9.render    │      │ h9-hyperframes  │             │ Temporal Sync   │
│ h9.publish   │      │                 │             │                 │
└──────────────┘      └─────────────────┘             └────────┬────────┘
                                                               │
                                                               ▼
                                                      ┌─────────────────┐
                                                      │   HyperFrames   │
                                                      │  Compiler & MP4 │
                                                      └─────────────────┘
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Architecture Audit & Call Graphs | In-depth audit in `docs/architecture/hermes-h9-runtime-coupling.md` with full capability comparison matrix and call graphs | M1 | Survey (R1) |
| 2 | Runtime Interface Abstractions | `src/h9_runtime/` defining AgentRuntime, SkillRuntime, ToolRuntime, ModelRuntime, MemoryRuntime, ExecutionRuntime, ContentRuntime | M1 | Survey (R1) |
| 3 | Backward Compatible Hermes Adapter | `adapters/hermes/` refactored as a lightweight delegation shim to `src/h9_runtime/` preventing test regressions | M1 | Survey (R1) |
| 4 | Capability Bridge | `src/h9_runtime/bridge.py` allowing H9 domain modules to request Hermes services without internal Hermes imports | M2 | Survey (R2) |
| 5 | Native H9 Model Tools | Expose `h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, `h9.publish` in `tools/registry.py` under named toolset `h9_content` | M2/M5 | Survey (R2/R5) |
| 6 | Service Check Gate | `check_h9_available()` in `tools/registry.py` ensuring zero core token overhead when H9 is not active | M2 | Survey (R2) |
| 7 | Native Hermes Skills | `skills/h9-research/`, `skills/h9-content-planning/`, `skills/h9-production/`, `skills/h9-hyperframes/` with valid `SKILL.md` | M3 | Survey (R3) |
| 8 | Typed Production IR Seam | `src/models/ir.py` AST interface connecting narrative planning to HyperFrames compiler with validation | M3 | Survey (R3) |
| 9 | Logical Capability Provider Routing | Route H9 model inference through Hermes provider system by roles (`fast_editorial`, `reasoning_research`, `creative_script`, `acoustic_eval`) | M4 | Survey (R4) |
| 10 | Unified Creator & Project Memory | Interface CreatorProfile, ContentProject, ProductionHistory with Hermes MemoryManager / SessionDB without competing persistence | M4 | Survey (R4) |
| 11 | Isolated Subagent Research Delegation | Delegate multi-source research to an isolated Hermes subagent via `delegate_task` returning structured ResearchDossier | M4 | Survey (R4) |
| 12 | Sandbox Execution Enforcement | Enforce `BaseEnvironment` (Docker/Modal/local) sandbox boundaries on subprocess rendering, asset downloads, and filesystem writes | M5 | Survey (R5) |
| 13 | Capability Token Permission Guard | Principle-of-least-privilege capability token enforcement restricting unauthorized scopes from calling critical tools | M5 | Survey (R5) |
| 14 | Hermes MCP Integration | Enable H9 operations to discover and call tools provided via Hermes MCP integration | M5 | Survey (R5) |
| 15 | 8-Dimension Acceptance Suite | Implement integration suite covering Dimensions A through H | M6 | Survey (R6) |
| 16 | Zero Regression Verification | Verify 100% pass across all baseline test suites and pipeline verifier | M6 | Survey (R6) |
| 17 | Final Integration Audit Report | Comprehensive audit report in `docs/architecture/hermes-h9-integration-audit.md` | M6 | Survey (R6) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Architecture Audit & Runtime Boundary | docs/architecture/hermes-h9-runtime-coupling.md, src/h9_runtime/ protocols & types, adapters/hermes/ delegation shim | none | DONE |
| M2 | Capability Bridge & Native Tools | src/h9_runtime/bridge.py, tools/h9_content_tools.py, tools/registry.py (h9.research, h9.discover_assets, h9.generate_script, h9.render) | M1 | DONE |
| M3 | Native Skills & Production IR Seam | skills/h9-*/SKILL.md, src/models/ir.py (ProductionIRDocument, IRSceneNode, IRVisualBlockNode, IRSpeechBeat) | M1, M2 | DONE |
| M4 | Provider, Memory & Subagent Integration | Role-based provider routing, H9CreatorMemoryProvider / SessionDB integration, research subagent delegation via delegate_task | M1, M2, M3 | DONE |
| M5 | Sandbox, Permission & MCP Integration | Subprocess execution via BaseEnvironment, capability token permission checks, MCP tool discovery & consumption | M1, M2, M3, M4 | DONE |
| M6 | Acceptance Verification Suite & Audit Report | tests/test_h9_acceptance.py, tests/test_h9_e2e_integration.py (Dims A-H), zero regressions, docs/architecture/hermes-h9-integration-audit.md | M1-M5 | IN_PROGRESS |

## Interface Contracts
### Domain Modules ↔ Runtime Boundary (src/h9_runtime/)
- `AgentRuntime`: `run_turn(messages, tools, context) -> TurnResult`
- `SkillRuntime`: `discover_skills() -> List[SkillMetadata]`, `load_skill(name) -> SkillInstruction`
- `ToolRuntime`: `register_tool(schema, handler)`, `invoke_tool(name, args) -> ToolResult`
- `ModelRuntime`: `execute_role(role, prompt, schema) -> ModelResult`
- `MemoryRuntime`: `get_creator_profile(creator_id) -> CreatorProfile`, `update_memory(entry)`
- `ExecutionRuntime`: `run_subprocess(command, env, timeout) -> ExecutionResult`
- `ContentRuntime`: `create_project(...)`, `get_production_state(...)`

### Capability Bridge ↔ Tools
- `h9.research(topic: str, depth: str, constraints: dict) -> ResearchDossier`
- `h9.discover_assets(requirements: list, scene_ids: list) -> List[AssetRecord]`
- `h9.generate_script(outline: dict, dossier: dict, creator: dict) -> Script`
- `h9.render(production_ir: dict, output_dir: str) -> RenderArtifact`
- `h9.publish(package: dict, platform: str) -> PublishResult`

### Sandbox Execution Boundary (Milestone 5 - DONE)
- HyperFrames rendering subprocesses, ffmpeg compilation, and asset fetches run through Hermes `BaseEnvironment` (LocalEnvironment / DockerEnvironment / ModalEnvironment).
- Strict execution bounds: process isolation, working directory confinement, resource/shm sizing (1G for renderers), command wrapping, and timeout guarantees (exit code 124 + stderr message).

### Permission & Capability Tokens (Milestone 5 - DONE)
- Principle-of-least-privilege: child permissions calculated via set-intersection ($P_{child} = P_{parent} \cap P_{role} \cap P_{workflow}$).
- Unauthorized or unentitled callers attempting to invoke privileged tools (`h9.render`, `h9.publish`) are strictly blocked by `TokenGuard`.
- Active `TokenRevocationRegistry` supporting instant revocation and cascading lineage invalidation.

### MCP Integration (Milestone 5 - DONE)
- Discover and expose MCP servers/tools seamlessly to H9 domain operations via Hermes MCP infrastructure.

## Code Layout
- `src/h9_runtime/`: Runtime boundary interfaces, capability bridge, types, provider/memory shims, execution runtime, token guards
- `src/security/`: CapabilityToken, TokenGuard, revocation registry, permission calculus
- `tools/h9_content_tools.py`: Native Hermes tool implementations and schemas (including h9.publish)
- `tools/registry.py`: Service-gated toolset registration (`h9_content`)
- `skills/h9-*/`: Native Hermes skills (`h9-research`, `h9-content-planning`, `h9-production`, `h9-hyperframes`)
- `src/models/ir.py`: Typed Production IR AST schemas
- `src/models/`: Pydantic production contracts
- `adapters/hermes/`: Backward-compatibility delegation shim
- `docs/architecture/`: Architecture audit documents and ADRs
- `tests/`: Baseline unit tests, `test_h9_runtime.py`, `test_h9_content_tools.py`, `test_h9_skills_and_ir.py`, `test_h9_provider_memory_subagent.py`, `test_h9_m5_sandbox_permission_mcp.py`, `test_challenger_m5_permissions.py`, `test_challenger_m5_sandbox_mcp.py`
