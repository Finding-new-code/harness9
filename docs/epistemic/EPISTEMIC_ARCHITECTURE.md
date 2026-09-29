# Epistemic Architecture Specification: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/epistemic/`, `src/models/`, `src/orchestrator/`, `src/h9_runtime/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/WORKFLOW_SPEC.md`, `docs/SECURITY_MODEL.md`, `docs/adrs/ADR-006-epistemic-verification.md`  

---

## 1. Executive Summary & Architectural Philosophy

The **Harness 9 Epistemic Verification Layer** is a formal, machine-readable verification subsystem designed to guarantee factual, historiographical, numerical, and visual ground truth across all AI-generated content productions. 

Historically, autonomous media creation systems have treated factual verification as an incidental byproduct of search retrieval or an unmonitored capability of large language model generation. In practice, this creates acute vulnerabilities: models hallucinate events, conflate popular myths with consensus scholarship, alter numerical quantities during narrative formatting, fabricate direct quotes, and render visual graphics that contradict spoken voiceover narration.

The Harness 9 Epistemic Architecture resolves these vulnerabilities by enforcing four foundational architectural principles:
1. **Decoupling of Epistemic Verification from Retrieval Confidence**: Search retrieval scores reflect query relevance and domain prestige, not empirical truth. Epistemic verification is an orthogonal, multi-strategy deductive process evaluated independently of search rankings.
2. **Graph-Grounded Evidence Lineage**: Claims are not isolated text strings; they are nodes in a directed acyclic **Evidence Graph** linking primary source records, verbatim passage excerpts, atomic assertions, script sentences, and rendered visual parameters.
3. **Historiographical Consensus Modeling**: For historical scholarship, binary true/false classifications are replaced by a formal **8-State Consensus Model**, distinguishing documented physical occurrences from causal interpretations and strictly prohibiting the arithmetic averaging of contradictory historical evidence.
4. **Deterministic Gate Enforcement & Publishing Lock**: Verification checks operate as non-bypassable checkpoints across the 17-state lifecycle machine. Publication is locked whenever a mandatory verification gate fails.

---

## 2. Decoupling Verification from Retrieval

### 2.1 The Retrieval-Verification Conflation Flaw
In existing retrieval pipelines, confidence is typically computed as a scalar function of domain top-level domains (`.gov`, `.edu`), regex query matching, and citation counts:
$$\text{Score}_{\text{retrieval}} = f(\text{DomainAuthority}, \text{KeywordMatchCount}, \text{DistinctDomainCount})$$

This formulation suffers from three fatal epistemic defects:
1. **The Popular Misconception Failure**: A widely repeated historical myth (e.g. *"Vikings wore horned helmets"*) appears on hundreds of distinct domains and across educational summaries, yielding $\text{Score}_{\text{retrieval}} > 0.95$, despite being contradicted by all primary archival records and scholarly consensus.
2. **The Authority Spoofing Failure**: Injected or unvetted blog text hosted under a `.org` or `.edu` personal home page receives high authority weighting regardless of textual substance.
3. **The Semantic Non-Entailment Failure**: A retrieval snippet may contain keywords associated with a claim while asserting the direct negation of that claim.

### 2.2 Mathematical Decoupling Formulation
Harness 9 establishes strict independence between retrieval ranking and epistemic verification:

$$\mathcal{E}(C) \perp \text{Score}_{\text{retrieval}}(C)$$

Where:
- $\text{Score}_{\text{retrieval}}(C) \in [0.0, 1.0]$: Measures query relevance, snippet readability, and initial candidate selection priority.
- $\mathcal{E}(C) = \langle S, T, K, \text{Score}_{\text{entailment}}, \text{Score}_{\text{corroboration}}, \text{Traces} \rangle$: Represents the multi-dimensional epistemic verification tuple.

Specifically:
- $S \in \text{EpistemicStatus}$: Discrete status (`verified`, `supported`, `partially_supported`, `contested`, `contradicted`, `unsupported`, `unverifiable`, `outdated`, `misleading`, `opinion`, `prediction`).
- $T \in \text{SourceTier}$: The highest authoritative tier backing the claim ($1$ to $13$).
- $K \in \text{ConsensusState}$: Scholarly consensus classification (`STRONG_CONSENSUS` through `INSUFFICIENT_LITERATURE`).
- $\text{Score}_{\text{entailment}} \in [0.0, 1.0]$: Natural language entailment score $P(\text{Passage} \models C)$.
- $\text{Score}_{\text{corroboration}} \in [0.0, 1.0]$: Independent, non-syndicated corroboration metric.

Under this architecture, a claim with $\text{Score}_{\text{retrieval}} = 0.99$ can be assigned $S = \text{CONTRADICTED}$ and blocked from publication.

---

## 3. Epistemic Architecture & Subsystem Interactions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL KNOWLEDGE SOURCES                           │
│  [Archival Sources]  [Academic Journals]  [Gov Datasets]  [Web Queries]    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Input Sanitization Boundary)
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UNTRUSTED CONTENT SANITIZER                              │
│  • Neutralizes prompt injection payloads                                    │
│  • Enforces structural tags: <untrusted_evidence id="..." sha256="...">     │
│  • Computes SHA-256 cryptographic digests of retrieved content              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    13-TIER SOURCE TAXONOMY CLASSIFIER                       │
│  • Resolves domain authority, DOIs, and publisher provenance                │
│  • Classifies sources: Tier 1 (Primary) down to Tier 13 (Unverified)        │
│  • Enforces claim-type source eligibility rules                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EVIDENCE GRAPH DAG ENGINE                             │
│  • Construct/reconstruct nodes: SourceNode, PassageNode, EvidenceUnitNode   │
│  • Links atomic assertions to ClaimNodes via ENTAILS / CONTRADICTS edges   │
│  • Maintains immutable provenance graph across entire project lifecycle     │
└───────────────────┬─────────────────────────────────────┬───────────────────┘
                    │                                     │
                    ▼                                     ▼
┌──────────────────────────────────────┐ ┌────────────────────────────────────┐
│  MULTI-STRATEGY VERIFICATION ENGINE  │ │  HISTORICAL SCHOLARSHIP POLICY     │
│  • SOURCE_ENTAILMENT (NLI / Semantics│ │  • Enforces 8 Consensus States     │
│  • CROSS_SOURCE_CORROBORATION (Graph)│ │  • Blocks single-source web facts  │
│  • CONTRADICTION_CHECK (Non-Averaging│ │  • Distinguishes Event vs Theory   │
│  • QUOTE_CHECK (Levenshtein / Paraph)│ │  • Calibrates narration framing    │
│  • NUMERICAL_CHECK (Units / Bounds)  │ └─────────────────┬──────────────────┘
│  • TEMPORAL_CHECK (Precedence / Anach)│                   │
└───────────────────┬──────────────────┘                   │
                    │                                      │
                    └───────────────────┬──────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               POST-SCRIPT CLAIM EXTRACTION & DRIFT AUDITOR                  │
│  • Deconstructs generated script sentences into atomic proposition claims   │
│  • Re-verifies script claims against Evidence Graph                         │
│  • Detects claim strengthening, omitted caveats, altered numbers, bad quotes│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│             VISUAL FACT-CHECKER & DETERMINISTIC DATASET PIPELINE            │
│  • Audits Production IR visual blocks (StatisticReveal, Timeline, Quote)    │
│  • Reconciles on-screen text/metrics against spoken voiceover narration     │
│  • Backs all rendered charts with immutable NumericalDataset instances     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│            LIFECYCLE STATE MACHINE VERIFICATION GATES (4 GATES)             │
│  [RESEARCH_VERIFICATION] ──► [SCRIPT_FACT_CHECK] ──► [VISUAL_FACT_CHECK]    │
│                                                            │                │
│                                                            ▼                │
│                                                [FINAL_EPISTEMIC_QA]         │
│                                                            │                │
│                       Deterministic Verdicts:              ▼                │
│             PASS  │  WARN  │  HUMAN_REVIEW  │  BLOCK ──► [PUBLISHING LOCK]  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NATIVE HERMES MODEL TOOLS LAYER                          │
│  h9.extract_claims, h9.verify_claim, h9.verify_script, h9.verify_quote,     │
│  h9.verify_numbers, h9.analyze_historical_consensus, h9.detect_contradic...│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Subsystem Specifications & Responsibilities

### 4.1 Untrusted Content Sanitizer (`src/epistemic/sanitizer.py`)
- **Input**: Raw text strings, HTML bodies, and metadata returned from search engines and external APIs.
- **Function**:
  - Encapsulates all external content in structured `<untrusted_evidence>` tags to neutralize indirect prompt injection attacks.
  - Strips null bytes (`\0`), control sequences, and fake model delimiters (e.g. `---`, ````system`, `<tool_call>`).
  - Computes an immutable SHA-256 digest (`content_sha256`) stored in `SourceRecord` to prevent citation tampering.

### 4.2 13-Tier Source Taxonomy (`src/epistemic/taxonomy.py`)
- **Input**: `SourceRecord` URL, publisher, author, DOI, and text content.
- **Function**:
  - Classifies source into `SourceTier` (from Tier 1 `PRIMARY_SOURCE` to Tier 13 `UNVERIFIED`).
  - Evaluates institutional provenance: validates DOIs against Crossref/PubMed registries and verifies domain authority against verified publisher lists.
  - Enforces minimum tier admissibility requirements based on claim category.

### 4.3 Evidence Graph DAG Engine (`src/epistemic/graph.py`)
- **Input**: Ingested sources, extracted passages, candidate claims, script scenes, and visual nodes.
- **Function**:
  - Constructs a directed acyclic grounding graph maintaining full cryptographic and textual provenance.
  - Links evidence units to claims via labeled edges (`ENTAILS`, `CONTRADICTS`, `HEDGES`).
  - Supports complete offline JSON-LD serialization and hermetic reconstruction without network access.

### 4.4 Multi-Strategy Verification Engine (`src/epistemic/engine.py`)
- **Input**: `ClaimRecord`, target `EvidenceGraph`, and `ClaimType`.
- **Function**:
  - Dispatches claims to specialized verification strategies based on claim typology.
  - Evaluates textual entailment, graph-based independence, contradiction presence, verbatim quotation fidelity, numerical dimensional consistency, and temporal validity.
  - Produces an immutable `VerificationResult` containing the claim's final `EpistemicStatus` and audit trace.

### 4.5 Historical Scholarship Policy Engine (`src/epistemic/historical.py`)
- **Input**: Historical claims, historiographical literature entries, and author attributions.
- **Function**:
  - Blocks single-source or popular web media from establishing historical facts or interpretations.
  - Classifies historical assertions into one of 8 `ConsensusState` classifications.
  - Differentiates documented empirical events from causal/scholarly interpretations.
  - Forbids arithmetic averaging of conflicting historical accounts; enforces calibrated script language framing.

### 4.6 Post-Script Claim Extractor & Auditor (`src/epistemic/script_verifier.py`)
- **Input**: Compiled `Script` (scenes, beats, voiceover narration) and backing `EvidenceGraph`.
- **Function**:
  - Deconstructs narration text into atomic claim assertions using natural language sentence decomposition.
  - Traverses the Evidence Graph to align script claims with research claims.
  - Detects semantic drift: flags strengthened claims (qualifiers dropped), altered numbers, omitted caveats, and fabricated quotes.

### 4.7 Visual Fact-Checker & Dataset Pipeline (`src/epistemic/visual_verifier.py`)
- **Input**: `ProductionIRDocument` visual blocks (`STATISTIC_REVEAL`, `TIMELINE_REVEAL`, `QUOTE_HIGHLIGHT`, `COMPARISON_PANEL`) and audio narration.
- **Function**:
  - Verifies that visual parameters (metrics, percentages, dates, quotes) strictly match spoken narration in the concurrent beat.
  - Enforces that all rendered data visualizations derive directly from immutable `NumericalDataset` instances with verifiable units and provenance.

### 4.8 Lifecycle State Machine Verification Gates (`src/orchestrator/state_machine.py`)
- **Input**: Production stage artifacts and verification summaries.
- **Function**:
  - Evaluates 4 verification gates (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`).
  - Outputs deterministic verdicts: `PASS`, `WARN`, `HUMAN_REVIEW`, or `BLOCK`.
  - Enforces the hard publishing lock: prevents transition to `COMPLETED` and blocks `h9.publish` whenever a mandatory gate has outcome `BLOCK` or `HUMAN_REVIEW`.

### 4.9 Hermes Native Model Tools (`tools/h9_content_tools.py`)
- **Function**:
  - Exposes 9 native verification tools to the Hermes agent runtime under toolset `h9_content` / `h9_epistemic`, service-gated by `check_h9_available`.
  - Enforces capability tokens and security boundaries before dispatching to host Python verification handlers.

---

## 5. Architectural Invariants & Guarantees

1. **Prompt Caching Invariant**: Verification tool calls do not alter past conversation history or dynamically recompile system prompts. The core agent conversation prefix remains byte-stable, preserving OpenAI/Anthropic prompt cache hits.
2. **Backward Compatibility Invariant**: All extensions to `SourceRecord`, `ClaimRecord`, `ScriptBeat`, `ScriptScene`, and `Script` use Pydantic v2 fields with default values, ensuring 100% pass rates across `tests/test_contracts.py` (12/12) and `tests/test_h9_acceptance.py` (44/44).
3. **Non-Averaging Invariant**: When historical sources or empirical datasets present contradictory numbers or conclusions, the system is mathematically prohibited from computing a synthetic average or mid-point. Contradictions must be preserved as opposing edges in the Evidence Graph and explicitly narrated as debated or contested.
4. **Publishing Lock Invariant**: The publishing interface (`h9.publish` and `bridge.publish()`) must verify that `FINAL_EPISTEMIC_QA` evaluated to `PASS` or `WARN`. A state of `BLOCK` or `HUMAN_REVIEW` halts execution and raises `EpistemicGateBlockError`.
5. **Least-Privilege Security Invariant**: All verification tools require a valid `CapabilityToken` signed via HMAC-SHA256. Child workers cannot execute tools outside the intersection of parent permissions, assigned role, and active lifecycle stage.
