# E2E Test Infra: Harness 9 Studio OS

## Test Philosophy
- Opaque-box, requirement-driven, deterministic, and 100% hermetic offline capability.
- Multi-tier testing methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinatorial + Real-World Workload Scenarios S1–S10.

## Feature Inventory
| # | Feature | Source (Requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|----------------------|:------:|:------:|:------:|
| 1 | 17-State Lifecycle State Machine | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 2 | 17 Pydantic Production Schemas | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 3 | Hermes Adapter Sandbox & Bridge | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 4 | Hermes Compatibility Documentation | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 5 | Multi-Angle Generation (5 Archetypes) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 6 | 9-Dimension Editorial Scorecard | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 7 | Deterministic Winning Angle Selector | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 8 | Psychological Hook Ideator | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 9 | 4-Act Narrative Planner | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 10 | HyperFrames Adapter Interface | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 11 | HyperFrames Component Registry | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 12 | 7 Canonical Parameterized Blocks | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 13 | Master Composition Generator | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 14 | Composition Static Linter | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 15 | Multi-Provider VoiceDirector | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |
| 16 | 4-Gate Automated VoiceQA | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |
| 17 | Two-Tier Asset Deduplication | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |
| 18 | Creator DNA 6-Component Model | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ |
| 19 | Creator Memory & Constraints | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ |
| 20 | Creator Economics Cost Ledger | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ |
| 21 | ContentBench 4-Layer Quality OS | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ |
| 22 | Capability Token Security Engine | ORIGINAL_REQUEST §R6 | 5 | 5 | ✓ |

## Test Architecture
- **Acceptance Verification Runner**: `verify_pipeline.py` executing 6 acceptance checkpoints (`CP_DOSSIER_VALID`, `CP_LEDGER_VALID`, `CP_AUDIO_VALID`, `CP_PROJECT_FILES`, `CP_COMP_VALID`, `CP_VIDEO_VALID`).
- **Unit & Integration Suites**: `tests/test_state_machine.py`, `tests/test_contracts.py`, `tests/test_hermes_adapter.py`, `tests/test_editorial.py`, `tests/test_hyperframes.py`, `tests/test_hyperframes_components.py`, `tests/test_voice_director.py`, `tests/test_voice_qa.py`, `tests/test_deduplication.py`, `tests/test_creator_dna.py`, `tests/test_economics.py`, `tests/test_contentbench.py`, `tests/test_security_tokens.py`.
- **Comprehensive 4-Tier E2E Suite**: `tests/test_e2e_comprehensive.py` and `tests/test_e2e_pipeline.py`.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| S1 | Deep Dive Tech Explainer (16:9 Landscape, 180s) | M1, M2, M3, M4, M5, M6 | High |
| S2 | High-Urgency Contrarian Short (9:16 Portrait, 45s) | M1, M2, M3, M4, M5, M6 | High |
| S3 | Data-Led Industry Research Breakdown (16:9, 120s) | M1, M2, M3, M4, M5, M6 | High |
| S4 | Human Narrative Historical Profile (16:9, 240s) | M1, M2, M3, M4, M5, M6 | High |
| S5 | Future Impact Trend Forecast (9:16 Portrait, 60s) | M1, M2, M3, M4, M5, M6 | High |
| S6 | Budget-Constrained Autonomous Fast Render (16:9, 30s) | M1, M2, M3, M4, M5, M6 | High |
| S7 | Strict Brand Constitution Enforcement & Guardrail Test | M1, M2, M5, M6 | Medium |
| S8 | Multi-Asset Deduplication & High Reuse Pipeline Run | M1, M3, M4, M5 | High |
| S9 | Degraded Acoustic Repair & VoiceQA Reject/Pass Run | M1, M4, M5 | Medium |
| S10 | Sandboxed Least-Privilege Subagent Execution Run | M1, M6 | High |

## Coverage Thresholds
- Tier 1: >= 5 tests per feature
- Tier 2: >= 5 boundary / error tests per feature
- Tier 3: Pairwise combinations across major feature boundaries
- Tier 4: 10 full end-to-end real-world scenarios S1–S10
