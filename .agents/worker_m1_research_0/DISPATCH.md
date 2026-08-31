## 2026-08-31T05:11:07Z
You are the Worker for Milestone 1: Research & Fact Synthesis Engine (R1).
Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m1_research_0
Project root: g:\Finding-new-code\harness9
Original request: g:\Finding-new-code\harness9\ORIGINAL_REQUEST.md
Project architecture & specs: g:\Finding-new-code\harness9\PROJECT.md
Research Explorer report & schemas: g:\Finding-new-code\harness9\.agents\explorer_research_assets_0\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your exclusive write ownership: `src/config.py`, `src/utils/`, `src/models/`, `src/research/`

Your tasks:
1. Implement `src/config.py` and `src/utils/filesystem.py` for atomic file writes, path handling, and config defaults.
2. Implement schema models in `src/models/`:
   - `src/models/dossier.py` (ResearchDossier, Claim, Source, TalkingPoint, Statistic, Metadata)
   - `src/models/ledger.py` (AssetProvenanceLedger, MediaAsset, LicenseInfo, CreatorInfo)
   - `src/models/script.py` (Script, Scene, Storyboard, Beat)
   - `src/models/summary.py` (PipelineSummary, StageResult)
   Ensure models support serialization/deserialization to both JSON and YAML.
3. Implement M1 Research Engine in `src/research/`:
   - `src/research/providers.py`: Live search adapters (Tavily/Exa/DuckDuckGo/Wikipedia/urllib APIs) with clean snippet parsing and error recovery.
   - `src/research/scoring.py`: Claim confidence scoring formula ($w_{auth} \cdot A + w_{corrob} \cdot C + w_{clarity} \cdot Q - P_{conflict}$).
   - `src/research/presets/`: Curated benchmark dossiers in YAML format:
     - `transistor_history.yaml`
     - `how_gpus_work.yaml`
     - `apollo_computer.yaml`
     - `quantum_computing.yaml`
   - `src/research/engine.py`: ResearchEngine class with `synthesize_research(topic: str, offline: bool = False, target_duration: int = 30) -> ResearchDossier`.
     - Supports live multi-intent query expansion.
     - If offline mode or network fails, checks curated presets first; if topic not in presets, procedurally synthesizes a deterministic, schema-compliant dossier using seeded hashing.
     - Saves `research_dossier.json` and `research_dossier.yaml`.
4. Run tests for M1 (e.g. `python -m unittest tests/test_research.py` or write an ad-hoc runner) to verify 100% passing.

Write report to: `g:\Finding-new-code\harness9\.agents\worker_m1_research_0\report.md`
And handoff to: `g:\Finding-new-code\harness9\.agents\worker_m1_research_0\handoff.md`

Send a message to parent when finished.
