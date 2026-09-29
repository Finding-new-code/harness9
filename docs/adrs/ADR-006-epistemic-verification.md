# ADR-006: Epistemic Verification Layer Architecture

**Status:** ACCEPTED  
**Date:** 2026-09-13  
**Deciders:** Head of Engineering, Architecture Team, Epistemic Verification Team  
**Scope:** Core Verification, Models (`src/models/`), Epistemic (`src/epistemic/`), Orchestrator (`src/orchestrator/`), Hermes Runtime (`src/h9_runtime/`, `tools/`)  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/WORKFLOW_SPEC.md`, `docs/SECURITY_MODEL.md`, `docs/CONTENTBENCH.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/adrs/ADR-001.md` through `ADR-005.md`  

---

## 1. Context & Problem Statement

Harness 9 produces autonomous video content through a 17-state lifecycle machine, Pydantic v2 production contracts, an editorial decision engine, and native Hermes Agent runtime coupling. Prior to this decision, factual grounding in Harness 9 relied on heuristic retrieval confidence scoring (`src/research/scoring.py`), which derived claim confidence from static domain authority (`.gov`, `.edu`), regex date detection, and distinct root domain counts.

Empirical investigation across the codebase revealed critical vulnerabilities:
1. **Conflation of Retrieval with Truth**: A claim repeated across multiple blogs or crowdsourced sites achieved $>0.90$ confidence even if it was an apocryphal myth, an obsolete scientific theory, or a mathematical error. Zero natural language entailment (NLI) or primary archival verification was performed.
2. **Generative Drift & Hallucination in Scripting**: In `src/scriptwriting/generator.py`, scripts were synthesized from claims without post-script extraction or audit. Generative models freely inflated assertions (dropping epistemic qualifiers like "preliminary"), altered numbers, omitted caveats, and fabricated direct quotes.
3. **Audio-Visual Discrepancy & Hallucinated Charts**: Intermediate Representation (`src/models/ir.py`) visual blocks (`STATISTIC_REVEAL`, `TIMELINE_REVEAL`, `QUOTE_HIGHLIGHT`) accepted untyped parameter strings without connection to verified primary datasets, risking glaring discrepancies between on-screen graphics and spoken audio.
4. **Historical Illiteracy & False Consensus**: Content from commercial blogs and crowdsourced wikis was permitted to act as sole authority; conflicting historical numbers were vulnerable to synthetic arithmetic averaging; and events were confused with scholarly interpretations.
5. **Absence of Lifecycle Verification Gates**: The state machine advanced from `CREATED` to `COMPLETED` without factual checkpoints. Videos containing refuted assertions could be rendered and published without restriction.

Harness 9 required a rigorous, mathematically sound, machine-readable **Epistemic Verification Layer** to guarantee factual, historiographical, numerical, and visual ground truth while maintaining 100% backward compatibility with existing contracts and acceptance test suites.

---

## 2. Decision & Architecture

We decided to implement the **Harness 9 Epistemic Verification Layer** structured across six foundational pillars:

### 2.1 Decoupling Verification from Retrieval Confidence
We strictly decouple epistemic verification from search retrieval confidence:
$$\mathcal{E}(C) \perp \text{Score}_{\text{retrieval}}(C)$$
Retrieval ranking evaluates query relevance and snippet priority. Epistemic status is evaluated by an orthogonal multi-strategy deductive engine that assigns discrete machine-readable statuses (`verified`, `supported`, `partially_supported`, `contested`, `contradicted`, `unsupported`, `unverifiable`, `outdated`, `misleading`, `opinion`, `prediction`).

### 2.2 Reconstructable Directed Acyclic Evidence Graph
We introduce a machine-readable DAG (`EvidenceGraph`) connecting `SourceNode` (Tier 1–13), `PassageNode` (character start/end offsets), `EvidenceUnitNode` (atomic propositions), `ClaimNode` (claims), `ScriptSentenceNode` (voiceover sentences), and `VisualElementNode` (HyperFrames parameters). The graph maintains immutable SHA-256 cryptographic digests and serializes to self-contained JSON-LD/YAML documents reconstructable offline.

### 2.3 13-Tier Source Taxonomy & Historical Scholarship Policy
We establish an authoritative 13-tier source hierarchy (from Tier 1 `PRIMARY_SOURCE` to Tier 13 `UNVERIFIED`) and enforce the strict Historical Scholarship Policy:
- **Prohibition of Sole Web Sources**: Single web summaries, commercial blogs, and crowdsourced wikis are strictly barred from establishing historical facts or interpretations.
- **The 8-State Consensus Model**: Historical claims are classified into one of 8 consensus states (`STRONG_CONSENSUS`, `BROAD_CONSENSUS`, `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `INSUFFICIENT_LITERATURE`).
- **Event vs. Interpretation Boundary**: Documented empirical events are separated from scholarly causal hypotheses.
- **The Non-Averaging Invariant**: Arithmetic averaging of contradictory historical casualty figures, dates, or economic metrics is strictly prohibited; contradictions must be preserved and narrated as disputed.

### 2.4 Multi-Strategy Verification Engine
We implement 7 composable verification strategies orchestrated via claim-type policy dispatch:
1. `SOURCE_ENTAILMENT`: Evaluates $P(\text{Passage} \models C)$ and flags unearned assertion strengthening.
2. `CROSS_SOURCE_CORROBORATION`: Evaluates non-syndicated graph independence across publishers.
3. `CONTRADICTION_CHECK`: Detects mutually exclusive assertions and enforces conflict preservation.
4. `QUOTE_CHECK`: Enforces normalized Levenshtein distance $\le 0.02$ or mandates transformation into attributed paraphrase.
5. `NUMERICAL_CHECK`: Performs dimensional analysis, SI base unit conversion, and mathematical consistency checks against ground-truth datasets.
6. `TEMPORAL_CHECK`: Enforces chronological precedence, temporal validity bounds, and anachronism elimination.
7. `HISTORIOGRAPHICAL_CHECK`: Enforces the Historical Scholarship Policy and rhetoric calibration.

### 2.5 Visual Fact-Checking & Deterministic Numerical Pipeline
- Compiled `ProductionIRDocument` visual blocks are audited against concurrent voiceover audio to eliminate number, date, and quote discrepancies.
- All rendered charts, curves, and statistical graphics must bind directly to immutable, typed `NumericalDataset` instances, guaranteeing mathematical identity between raw data and rendered visuals.

### 2.6 Deterministic Lifecycle Gates & Hard Publishing Lock
We integrate 4 verification gates into the state machine transition checkpoints:
1. `RESEARCH_VERIFICATION`: Evaluated at `RESEARCH_IN_PROGRESS` $\to$ `RESEARCH_COMPLETED`.
2. `SCRIPT_FACT_CHECK`: Evaluated at `SCRIPTING_IN_PROGRESS` $\to$ `SCRIPT_COMPLETED`.
3. `VISUAL_FACT_CHECK`: Evaluated at `COMPOSITION_GENERATED` $\to$ `RENDER_IN_PROGRESS`.
4. `FINAL_EPISTEMIC_QA`: Evaluated at `RENDER_COMPLETED` $\to$ `COMPLETED`.

Gates yield deterministic outcomes (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`). **The Publishing Lock Invariant** unconditionally halts publication (`h9.publish` and `bridge.publish()`) if `FINAL_EPISTEMIC_QA` outcome is not `PASS` or `WARN`.

### 2.7 Hermes Native Model Tools & Security Boundaries
We expose 9 native verification tools (`h9.extract_claims`, `h9.verify_claim`, `h9.verify_script`, `h9.verify_quote`, `h9.verify_numbers`, `h9.analyze_historical_consensus`, `h9.detect_contradictions`, `h9.verify_visual_claims`, `h9.epistemic_gate`) in the `h9_content` toolset, service-gated by `check_h9_available` (Footprint Ladder Rung 3). All retrieved web content is sanitized within `<untrusted_evidence>` boundaries to neutralize prompt injections.

---

## 3. Consequences & Trade-Offs

### Positive Consequences
- **Uncompromised Epistemic Integrity**: No video can be rendered or published containing refuted facts, fabricated quotes, altered statistics, or uncalibrated historical claims.
- **Explainable Provenance**: Every spoken word and visual graphic traces backward through the Evidence Graph to an immutable source passage.
- **Adversarial Resilience**: Defends against false consensus attacks, citation laundering, lookalike academic domains, and prompt injection via scraped text.
- **100% Backward Compatibility**: Contract extensions use Pydantic v2 default fields, ensuring all 44 existing acceptance tests in `tests/test_h9_acceptance.py` and 12 contract tests in `tests/test_contracts.py` pass unconditionally.
- **Prompt Cache Byte Stability**: Conforms strictly to Hermes core invariants; verification operations execute as isolated tool calls without mutating the main conversation prefix.

### Negative Consequences & Mitigations
- **Computational Latency**: Deep semantic NLI and historiographical evaluation add compute time during pipeline execution.
  - *Mitigation*: Tiered evaluation. Fast deterministic rule engines (exact quote Levenshtein, regex dimensional analysis, domain taxonomy, temporal bounds) run first in microseconds. Deep NLI runs only on unverified or high-stakes claims, with results cached by claim SHA-256 digest.
- **External Scholarly API Dependencies**: Querying live academic databases (OpenAlex, Europe PMC) risks rate limits and network drops.
  - *Mitigation*: The evaluation suite (`H9-FactBench`) features a hybrid architecture with hermetic offline test fixtures for CI/CD runs, isolating live scholarly APIs to scheduled integration benchmarks.

---

## 4. Compliance & Verification

Compliance with ADR-006 is verified empirically via:
1. **Contract Schema Conformance**:
   ```pwsh
   .venv\Scripts\python.exe -m pytest tests/test_contracts.py -v
   ```
   *Requirement*: 100% passing (12/12).
2. **Acceptance Regression Verification**:
   ```pwsh
   .venv\Scripts\python.exe -m pytest tests/test_h9_acceptance.py -v
   ```
   *Requirement*: 100% passing across all 8 dimensions (44/44).
3. **Epistemic Benchmark & Adversarial Verification**:
   ```pwsh
   .venv\Scripts\python.exe -m pytest tests/test_epistemic_adversarial.py -v
   ```
   *Requirement*: Zero vulnerabilities permitted across false consensus, citation laundering, authority spoofing, prompt injection, and gate bypass vectors.
4. **Publishing Lock Invariant**:
   Assert that `bridge.publish()` raises `EpistemicGateBlockError` when `FINAL_EPISTEMIC_QA` is simulated as `BLOCK`.
