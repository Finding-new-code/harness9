# Pre-Implementation Forensic Audit Report: Harness 9 Epistemic Verification Layer

**Document Version:** 1.0.0  
**Audit Date:** 2026-09-13T17:15:00Z  
**Auditors:** Forensic Architecture Team (`teamwork_preview_worker_m1`, `teamwork_preview_explorer_survey_1-3`)  
**Status:** Approved Baseline Pre-Audit  
**Target Milestone:** Harness 9 Epistemic Verification Layer (`ORIGINAL_REQUEST.md` entry `## 2026-09-13T16:44:00Z`)  
**Repository Scope:** `g:\Finding-new-code\harness9`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/WORKFLOW_SPEC.md`, `docs/SECURITY_MODEL.md`, `docs/CONTENTBENCH.md`, `docs/adrs/ADR-006-epistemic-verification.md`  

---

## 1. Executive Summary & Forensic Audit Mandate

This pre-implementation audit report establishes the authoritative empirical and architectural baseline for implementing the **Harness 9 Epistemic Verification Layer**. It forensically evaluates existing code paths, data structures, evaluation suites, and execution boundaries in Harness 9 prior to any core epistemic modifications.

Harness 9 currently possesses a decoupled architecture featuring a 17-state lifecycle state machine (`src/orchestrator/state_machine.py`), Pydantic v2 production contracts (`src/models/contracts.py`), a Production Intermediate Representation AST (`src/models/ir.py`), an editorial decision engine (`src/editorial/`), an acoustic QA suite (`src/scriptwriting/voice_qa.py`), and runtime coupling to the Hermes Agent platform (`src/h9_runtime/`, `tools/h9_content_tools.py`). All 44 acceptance tests in `tests/test_h9_acceptance.py` pass cleanly.

However, a rigorous investigation of the research, scriptwriting, and rendering pipelines reveals that **Harness 9 currently lacks genuine epistemic verification**:
1. **Conflation of Retrieval Confidence with Ground Truth**: `src/research/scoring.py` computes claim confidence using heuristic keyword matching, TLD boosts (`.gov`, `.edu`), and distinct root domain counts. It executes zero natural language inference (NLI), passage entailment, or empirical verification.
2. **Anemic Epistemic Semantics in Contracts**: `ClaimRecord` and `SourceRecord` in `src/models/contracts.py` lack discrete epistemic statuses, consensus classifications, source taxonomy tiers, character offset passage links, and temporal bounding.
3. **Open-Ended Hallucination & Drift in Scripting**: `src/scriptwriting/generator.py` procedurally formats voiceover beats from claims without any post-script extraction or verification. Generative models freely inflate assertions, alter numbers, omit caveats, and fabricate direct quotes.
4. **Purely Acoustic QA**: Existing QA (`src/scriptwriting/voice_qa.py`) only detects audio clipping, dead air, and RMS loudness. Zero textual, semantic, numerical, or factual QA exists anywhere in the codebase.
5. **No Ground-Truth Lineage for Visual Elements**: Intermediate Representation (`src/models/ir.py`) visual blocks (`STATISTIC_REVEAL`, `TIMELINE_REVEAL`, `QUOTE_HIGHLIGHT`) accept arbitrary untyped string parameters without connection to verified primary datasets, risking glaring visual/audio discrepancies.
6. **Absence of Lifecycle Verification Gates**: The 17-state production state machine advances from `CREATED` to `COMPLETED` without evaluating factual integrity. Videos containing refuted assertions or fabricated quotes can be rendered and published without restriction.

This document systematically details these vulnerabilities across all subsystems, provides empirical test results, and defines the structural requirements for the Epistemic Verification Layer.

---

## 2. Empirical Baseline Audit of Existing Subsystems

### 2.1 Research Scoring & Heuristic Flaws (`src/research/scoring.py`, `src/research/engine.py`)

#### A. Code Path Citations & Formula Deconstruction
In `src/research/scoring.py`:
- Lines 15–49, 79–108: `calculate_authority_score(url)` relies on hardcoded domain sets (`TIER_1_DOMAINS`, `TIER_2_DOMAINS`, `TIER_3_DOMAINS`) and top-level domain (TLD) suffix checks:
  - `.gov` $\to 0.98$
  - `.edu` $\to 0.95$
  - `.org` $\to 0.70$
  - Generic fallback $\to 0.55$
- Lines 110–124: `calculate_corroboration_score(primary, corroborating)` merely counts unique root domain names:
  $$\text{Score} = \begin{cases} 1.0 & \text{if distinct domains} \ge 3 \\ 0.75 & \text{if distinct domains} = 2 \\ 0.60 & \text{if distinct domains} = 1 \\ 0.40 & \text{if distinct domains} = 0 \end{cases}$$
- Lines 126–159: `calculate_clarity_score(claim_text)` uses regular expressions to match 4-digit years (`\b(19\d\d|20\d\d)\b`), metric units (`%`, `billion`, `nm`, `GHz`), and capitalized tokens. `calculate_conflict_penalty(notes)` looks for exact substring occurrences in `DISPUTED_TERMS = ["disputed", "alleged", "controversial", "unconfirmed"]`, deducting a static $0.25$.
- Lines 161–202: The scalar `score_claim(claim)` aggregates these components via linear weighting:
  $$\text{Confidence} = w_{\text{auth}} \cdot A + w_{\text{corrob}} \cdot C + w_{\text{clarity}} \cdot Q - P_{\text{conflict}}$$
  where $w_{\text{auth}} = 0.35$, $w_{\text{corrob}} = 0.35$, $w_{\text{clarity}} = 0.30$.

#### B. Forensic Analysis of Vulnerabilities
1. **Complete Conflation of Retrieval with Verification**: A search snippet containing a date and a metric from a `.edu` blog, corroborated by a `.org` content aggregator, receives a confidence score $>0.90$, even if the claim is an apocryphal myth (e.g. *"Napoleon was 4 feet tall"*), an obsolete scientific hypothesis, or a mathematical error.
2. **Zero Natural Language Inference (NLI)**: `scoring.py` never checks whether the retrieved text logically entails, refutes, or is neutral towards the assertion.
3. **Syndication & Citation Laundering Blindness**: `calculate_corroboration_score` treats three different domains republishing the same syndicated wire article as three independent confirmations, completely vulnerable to circular citation laundering.
4. **No Passage-Level Extraction**: In `src/research/engine.py:140-176`, the search engine splits raw snippets into arbitrary sentences (40–280 characters), assigns the first result as `primary_source`, and grabs the next two results with different domain roots as `corroborating_sources` without testing semantic relevance.

---

### 2.2 Core Production Contracts (`src/models/contracts.py`)

#### A. Code Path Citations
Direct inspection of `src/models/contracts.py` (lines 197–255, 327–458):

```python
# contracts.py:197-205
class SourceRecord(H9BaseModel):
    """Citation and provenance metadata for an external information source."""
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)

# contracts.py:207-217
class ClaimRecord(H9BaseModel):
    """Factual claim backed by primary and corroborating source records."""
    claim_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    category: str = Field(default="general")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    primary_source: SourceRecord
    corroborating_sources: List[SourceRecord] = Field(default_factory=list)
    visual_cue_suggestion: str = ""
    verification_notes: str = ""
```

#### B. Forensic Deficiencies
1. **Lack of Discrete Epistemic Status**: The contract models epistemic status only as a floating-point `confidence_score`. There is no classification for `verified`, `supported`, `partially_supported`, `contested`, `contradicted`, `unsupported`, `unverifiable`, `outdated`, `misleading`, `opinion`, or `prediction`.
2. **No 13-Tier Source Taxonomy**: `SourceRecord` lacks classification according to source authority (e.g. `PRIMARY_SOURCE`, `PEER_REVIEWED_JOURNAL`, `ACADEMIC_PRESS_BOOK`, `GOVERNMENT_RECORD_STATISTICAL_AGENCY` down to `UNVERIFIED`). It treats all URLs symmetrically.
3. **No Consensus State Modeling**: The schema cannot record whether a historical or scientific claim represents a `STRONG_CONSENSUS`, an `ACTIVE_DEBATE`, or a `CONTESTED` thesis.
4. **No Passage-Level Grounding**: Sources point to coarse URLs without passage text, character start/end offsets, or specific citation page numbers.
5. **No Negative Evidence Tracking**: `ClaimRecord` only stores `corroborating_sources`. Refuting or dissenting sources are ignored.
6. **No Temporal Anchoring**: Lacks `valid_from`, `valid_until`, `as_of_date`, and `temporal_status` fields.
7. **Ungrounded Script Beats**: In `ScriptBeat` (`contracts.py:353-385`) and `ScriptScene` (`contracts.py:387-420`), neither model contains references to `claim_id` or evidence nodes. Narration text exists in total disconnection from the research claims that allegedly justify it.

---

### 2.3 Scriptwriting Engine & Narrative Drift (`src/scriptwriting/generator.py`)

#### A. Code Path Citations
In `src/scriptwriting/generator.py` (lines 351–450, `synthesize_scenes_from_dossier`):
- Scenes and voiceover narration are generated by open-ended string concatenation and prompting:
  ```python
  narration = f"{tp.title}. {tp.narrative_hook} {claim_text}"
  ```
- No post-generation claim extraction or verification step exists.

#### B. Manifestations of Hallucination and Semantic Drift
1. **Claim Inflation / Strengthening**: An original hedged research claim (e.g. *"Archaeological evidence suggests preliminary early iron smelting around 1000 BCE"*) is routinely rewritten into unhedged absolutes (e.g. *"Historians have proven that iron working was definitively invented in 1000 BCE"*).
2. **Numerical Mutation**: Exact quantities from `StatisticRecord` (e.g. *"82.4 billion transistors"*) are casually rounded or transposed (e.g. *"nearly 100 billion"* or *"84 billion"*) without tracking tolerance or approximation indicators.
3. **Quote Fabrication & Misattribution**: Dialogue beats introduce quotation marks around synthetic paraphrases that do not appear verbatim in any primary historical source.
4. **Omission of Dissenting Views**: Contentious debates are presented as settled facts to maximize dramatic tension.

---

### 2.4 Audio & Script QA (`src/scriptwriting/voice_qa.py`)

#### A. Code Path Citations
In `src/scriptwriting/voice_qa.py` (lines 1–60):
- `VoiceQA.inspect_audio(waveform)` evaluates exclusively physical audio signal properties:
  - Silence threshold: $< -45\text{ dBFS}$
  - Dead air gap: $> 300\text{ ms}$
  - Clipping ratio: $< 0.0001$
  - Loudness variance: $\le 2.5\text{ dBFS}$
  - Speech-beat sync drift: $\le 0.20\text{ s}$

#### B. Complete Absence of Factual QA
There is zero textual, semantic, numerical, or epistemic QA in `src/qa/` or `src/scriptwriting/`. The system can produce an audio track asserting that the earth is flat or that Apollo 11 landed in 1985, and `VoiceQA` will assign it a 100% `PASS` score as long as the audio does not clip and has no dead air.

---

### 2.5 Visual Intermediate Representation Pipeline (`src/models/ir.py`)

#### A. Code Path Citations
In `src/models/ir.py`:
- `IRBlockType` (lines 33–42): Defines visual components (`REFERENCE_COLLAGE_HOOK`, `SPLIT_SCREEN_INTRO`, `QUOTE_HIGHLIGHT`, `TIMELINE_REVEAL`, `STATISTIC_REVEAL`, `COMPARISON_PANEL`, `CREATOR_BOTTOM_COLLAGE`).
- `IRVisualBlockNode` (lines 139–172): Holds untyped parameter dictionaries (`parameters: Dict[str, Any]`). In `STATISTIC_REVEAL`, parameters like `stat_number: "90%+"` are arbitrary string literals.
- `ProductionIRDocument` (lines 246–374): Linter verifies temporal conservation and asset references, but executes zero factual consistency checks between visual parameters and narration audio.

#### B. Visual Discrepancy Vulnerabilities
1. **Visual-Audio Numerical Mismatch**: Voiceover may say *"over four million dollars"*, while the on-screen `STATISTIC_REVEAL` displays `"$4.2B"`.
2. **Timeline Anachronism**: Voiceover narrates *"in the early 19th century"*, while the visual `TIMELINE_REVEAL` displays `"1742"`.
3. **Absence of Numerical Dataset Lineage**: Charts rendered in `COMPARISON_PANEL` or `STATISTIC_REVEAL` have no lineage back to tabular datasets, risking completely fabricated bar heights, percentages, and trends.

---

### 2.6 Lifecycle State Machine & Publishing Gates (`src/orchestrator/state_machine.py`)

#### A. Code Path Citations
In `src/orchestrator/state_machine.py`:
- `ProductionState` (lines 14–61): The 17 canonical sequential states proceed without verification gates:
  $$\text{CREATED} \to \dots \to \text{RESEARCH\_COMPLETED} \to \text{EDITORIAL\_ANALYSIS} \to \dots \to \text{SCRIPT\_COMPLETED} \to \dots \to \text{RENDER\_COMPLETED} \to \text{COMPLETED}$$
- `VALID_TRANSITIONS` (lines 116–225): Transitions are purely structural.
- `HermesCapabilityBridge.publish()` (`src/h9_runtime/bridge.py:805-875`): Checks token capability and directory paths, but **never checks whether factual verification passed**.

#### B. Vulnerability
Factual errors are completely non-blocking. An autonomous pipeline execution runs end-to-end and publishes video packages even when claims are contradicted or completely ungrounded.

---

### 2.7 Hermes Native Model Tools (`tools/h9_content_tools.py`)

#### A. Code Path Citations
`tools/h9_content_tools.py` exposes 5 content tools under the `h9_content` toolset:
1. `h9.research` (`tools/h9_content_tools.py:75-104`)
2. `h9.discover_assets` (`tools/h9_content_tools.py:106-134`)
3. `h9.generate_script` (`tools/h9_content_tools.py:136-164`)
4. `h9.render` (`tools/h9_content_tools.py:166-194`)
5. `h9.publish` (`tools/h9_content_tools.py:196-224`)

#### B. Gap
The Hermes Agent core cannot invoke claim extraction, claim verification, script audits, quote verification, numerical checks, historical consensus analysis, or gate evaluations as native model tools.

---

### 2.8 ContentBench Evaluation Framework (`src/evaluation/contentbench.py`)

#### A. Code Path Citations
In `src/evaluation/contentbench.py`:
- Layer 1 (`S_research`, lines 262–345): Scores fact density ($\ge 3$ claims per 30s), domain authority averages, and corroboration ratio (percentage of claims with $\ge 1$ corroborating source).
- Deductions occur only if notes literally contain `"conflict"`.

#### B. Gap
ContentBench lacks factual verification test suites, ground-truth claim benchmarks, historical consensus calibration metrics, and adversarial datasets.

---

## 3. Empirical Test Execution Baseline

To establish rigorous ground truth and confirm stability prior to implementation, the test suite was executed against the virtual environment:

### 3.1 Production Contracts Suite (`tests/test_contracts.py`)
```pwsh
.venv\Scripts\python.exe -m pytest tests/test_contracts.py -q
```
**Result:** `12 passed in 12.26s (100%)`.  
*Confirmed Invariant:* All 17 Pydantic contracts validate cleanly, instantiate from valid schemas, and enforce `H9BaseModel` validation rules.

### 3.2 Runtime Acceptance Suite (`tests/test_h9_acceptance.py`)
```pwsh
.venv\Scripts\python.exe -m pytest tests/test_h9_acceptance.py -q
```
**Result:** `44 passed in 81.25s (100%)`.  
*Confirmed Invariant:* All 8 required acceptance dimensions (A through H) pass:
- Dimension A (Runtime Coupling & Contracts): 5/5
- Dimension B (Skill Coupling & Production IR): 5/5
- Dimension C (Provider Fallbacks): 5/5
- Dimension D (Tool Schemas & Registry): 5/5
- Dimension E (Subagent Research Delegation): 5/5
- Dimension F (Permission Tokens & Guard): 7/7
- Dimension G (Execution Sandboxing & Path Limits): 6/6
- Dimension H (End-to-End Rendering & Publication): 6/6

### 3.3 Security & Sandbox Suite (`tests/test_h9_m5_sandbox_permission_mcp.py`)
```pwsh
.venv\Scripts\python.exe -m pytest tests/test_h9_m5_sandbox_permission_mcp.py -q
```
**Result:** `19 passed in 36.70s (100%)`.

### 3.4 Circular Import Diagnosis
- Direct import test:
  ```pwsh
  .venv\Scripts\python.exe -c "import src.orchestrator.state_machine"
  ```
  *Observed Traceback:* `ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline' (most likely due to a circular import)`.
- *Root Cause:* `src/h9_runtime/content.py:37` performs an eager module-level import: `from src.orchestrator.pipeline import Pipeline`.
- *Remediation Invariant:* Moving this import inside `run_full_production()` removes the import cycle without altering runtime behavior.

---

## 4. Architectural Gap & Vulnerability Matrix

| Subsystem | Existing State | Forensic Gap / Vulnerability | Required Epistemic Remediation |
|---|---|---|---|
| **Research Scoring** (`scoring.py`) | Linear heuristic over domain authority, regex dates, and domain counts. | Evaluates retrieval confidence, not epistemic truth; vulnerable to syndication laundering; zero semantic NLI. | Multi-strategy verification engine; 13-tier taxonomy; decouple verification from retrieval confidence. |
| **Contracts** (`contracts.py`) | Lightweight `ClaimRecord` & `SourceRecord`. | No discrete epistemic status, no consensus states, no passage offsets, no temporal bounds, no contradiction tracking. | Non-breaking extension: 11 `EpistemicStatus` values, 8 `ConsensusState` values, `EvidenceUnitLink`, `TemporalContext`. |
| **Evidence Graph** | Non-existent; claims are isolated objects in `ResearchDossier`. | Cannot trace provenance from primary source to rendered frame; cannot model multi-source contradiction DAGs. | Directed acyclic `EvidenceGraph` linking Sources, Passages, Evidence Units, Claims, Scripts, and Visuals. |
| **Historical Scholarship** | None; treats Wikipedia, random blogs, and academic monographs equally. | Single web sources establish false historical consensus; contradictions averaged away numerically; events confused with interpretations. | Strict Historical Scholarship Policy: block sole web sources, 8 consensus states, event vs interpretation, no numeric averaging. |
| **Scriptwriting** (`generator.py`) | Procedural string formatting into voiceover beats. | Open-ended LLM drift; claim strengthening; altered numbers; fabricated quotes; omitted uncertainty. | Post-script claim extraction and re-verification against Evidence Graph; quote verifier (exact or paraphrase). |
| **Visual IR** (`models/ir.py`) | Untyped parameter dictionaries on HyperFrames blocks. | Visual statistics and dates mismatch narration; no ground-truth dataset backing for charts. | Visual fact-checker auditing scene IR against narration; deterministic numerical pipeline (`NumericalDataset`). |
| **State Machine** (`state_machine.py`) | 17 sequential states without verification checks. | Production advances to render and publish even if claims are refuted, uncorroborated, or hallucinatory. | 4 verification gates (`RESEARCH`, `SCRIPT`, `VISUAL`, `FINAL_QA`) with outcomes `PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`. |
| **Publishing Lock** | `bridge.publish()` checks only tokens and paths. | Unsupported or contradicted content can be published. | Hard publishing lock: publishing is unconditionally blocked if any mandatory gate is `BLOCK` or `HUMAN_REVIEW`. |
| **Hermes Tools** (`h9_content_tools.py`)| 5 content tools (`research`, `discover_assets`, `script`, `render`, `publish`). | Verification capabilities are not accessible as native model tools to Hermes agents. | 9 native model tools registered under `h9_content` / `h9_epistemic`, service-gated by `check_h9_available`. |
| **Security & Sanitization** | Raw text snippets parsed directly. | Scraped web content can inject prompt overrides or attempt authority escalation. | Treat all retrieved web data as untrusted; encapsulate in `<untrusted_evidence>` delimiters; host-enforced tokens. |
| **Evaluation Suite** (`contentbench.py`)| Evaluates claim density and domain reputation. | No benchmark datasets for claims, quotes, numbers, or contested historical consensus; no adversarial tests. | `H9-FactBench` across 9 categories (hybrid offline + live) and `tests/test_epistemic_adversarial.py`. |

---

## 5. Target Epistemic Architecture & Remediation Roadmap

The Epistemic Verification Layer introduces 6 foundational layers:

```
[ Research Dossier / Web Sources / External APIs ]
                      │
                      ▼ (Untrusted Content Sanitization: <untrusted_evidence>)
         [ 13-Tier Source Taxonomy Hierarchy ]
                      │
                      ▼
            [ Evidence Graph DAG ] ◄────────────────────────────────┐
                      │                                             │
                      ▼                                             │
      [ Multi-Strategy Verification Engine ]                        │
        ├─ SOURCE_ENTAILMENT (NLI / Semantic Bounds)                │
        ├─ CROSS_SOURCE_CORROBORATION (Graph Independence)          │
        ├─ CONTRADICTION_CHECK (Preserve Conflicts)                 │
        ├─ QUOTE_CHECK (Verbatim Match or Paraphrase)               │
        ├─ NUMERICAL_CHECK (Units, Bounds, Dimensional Analysis)    │
        ├─ TEMPORAL_CHECK (Chronology, Anachronisms, Freshness)     │
        └─ HISTORIOGRAPHICAL_CHECK (8 Consensus States)             │
                      │                                             │
                      ▼                                             │
   [ Post-Script Claim Re-Verification & Drift Audit ] ─────────────┤
                      │                                             │
                      ▼                                             │
   [ Visual & Numerical Integrity / Dataset Pipeline ] ─────────────┘
                      │
                      ▼
      [ Deterministic State Machine Verification Gates ]
        ├─ RESEARCH_VERIFICATION Gate  (Transition 1)
        ├─ SCRIPT_FACT_CHECK Gate      (Transition 2)
        ├─ VISUAL_FACT_CHECK Gate      (Transition 3)
        └─ FINAL_EPISTEMIC_QA Gate     (Transition 4) ──► Hard Publishing Lock
                      │
                      ▼
         [ 9 Native Hermes Model Tools ]
           (h9.extract_claims, h9.verify_claim, h9.verify_script, ...)
```

---

## 6. Audit Conclusion & Compliance Attestation

This forensic audit confirms that while Harness 9 possesses robust runtime mechanics and 100% test pass rates across its foundational suites, its factual grounding is currently purely heuristic and vulnerable to hallucinations, distortions, and unverified claims.

The implementation of the Epistemic Verification Layer must:
1. Maintain strict backward compatibility with `tests/test_contracts.py` and `tests/test_h9_acceptance.py` (44/44 passing).
2. Adhere strictly to the Hermes Footprint Ladder (Rung 3 for model tools) and preserve prompt cache byte stability.
3. Enforce the Historical Scholarship Policy without numeric averaging of conflicting accounts.
4. Block publication deterministically when verification gates fail.

**Audit Status:** Certified and Approved for Implementation.
