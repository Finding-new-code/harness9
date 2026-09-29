# Technical Survey & Epistemic Architecture Report: Harness 9 Epistemic Verification Layer

**Date:** 2026-09-13  
**Author:** Survey Explorer 1 (`teamwork_preview_explorer_survey_1`)  
**Mission:** Survey existing data models, contracts, and research/editorial subsystems in Harness 9 to prepare for the Epistemic Verification Layer (`ORIGINAL_REQUEST.md` entry `## 2026-09-13T16:44:00Z`).  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_survey_1`  
**Target File:** `handoff.md`  

---

## Executive Summary

This survey report provides the forensic architectural baseline for implementing the **Harness 9 Epistemic Verification Layer** across the research, claim, production contract, editorial, scriptwriting, visual rendering, and lifecycle state machine systems. 

Harness 9 currently represents factual claims using lightweight Pydantic v2 schemas (`ClaimRecord`, `SourceRecord` in `src/models/contracts.py`) and computes confidence scores through heuristic keyword/domain-authority formulas (`src/research/scoring.py`). However, existing claims lack machine-readable epistemic semantics, passage-level grounding, consensus modeling, quote validation, and cross-stage verification traces. In downstream scriptwriting (`src/scriptwriting/generator.py`) and visual compilation (`src/models/ir.py`), claims are freely paraphrased, concatenated, and converted into visual cards without post-generation fact-checking or numerical dataset lineage.

To address these foundational vulnerabilities while preserving 100% backward compatibility with all 44 existing acceptance tests in `tests/test_h9_acceptance.py` and 12 unit tests in `tests/test_contracts.py`, this report specifies:
1. **Executable Epistemic Semantics for Core Contracts**: Non-breaking extension of `ClaimRecord` and `SourceRecord` with 11 granular epistemic statuses, 8 consensus states, structured evidence links, temporal anchors, and verifier metadata.
2. **Dedicated Evidence Graph Abstraction**: A reconstructable directed acyclic grounding DAG spanning Sources, Passages, Evidence Units, Claims, Verification Traces, Script Sentences, Scenes, and Visual Elements.
3. **13-Tier Source Taxonomy & Policy Dispatch**: An authoritative information hierarchy (from `PRIMARY_SOURCE` to `UNVERIFIED`) with claim-type-specific dispatch rules.
4. **Historical Scholarship Policy**: Strict enforcement of historiographical standards (forbidding single-source popular summaries, distinguishing documented events from causal interpretations, preserving contradictions without numeric averaging).
5. **Multi-Stage Verification Pipeline & Hard State Machine Gates**: Deterministic gates (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`) supporting `PASS`, `WARN`, `HUMAN_REVIEW`, and `BLOCK`.
6. **Hermes Native Model Tools**: Exposing 9 specialized epistemic tools via the Hermes runtime bridge conforming to Rung 3 of the Footprint Ladder.

---

## 1. Observation

### 1.1 Direct Codebase & Contract Inspection

#### A. `src/models/contracts.py` (Core Production Contracts)
Direct inspection of `src/models/contracts.py` (lines 197–255, 327–458) reveals how claims, sources, and scripts are currently represented:

- **`SourceRecord` (`contracts.py:197-205`)**:
  ```python
  class SourceRecord(H9BaseModel):
      """Citation and provenance metadata for an external information source."""
      title: str = Field(..., min_length=1)
      url: str = Field(..., min_length=1)
      publisher: Optional[str] = None
      author: Optional[str] = None
      published_date: Optional[str] = None
      reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
  ```
  *Observed Capabilities*: Basic URL string, publication title, author, and bounded float reliability score.  
  *Observed Deficiencies*: No unique source identifier (`source_id`), no source tier classification (`tier`), no domain authority rating, no DOI, no peer-review flag, no archival/Wayback URL, no content hash for tamper resistance, no raw text snippet, and no untrusted input sanitization metadata.

- **`ClaimRecord` (`contracts.py:207-217`)**:
  ```python
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
  *Observed Capabilities*: Unique ID, natural language claim string, category tag, float confidence score, nested primary `SourceRecord`, and list of corroborating `SourceRecord`s.  
  *Observed Deficiencies*: 
  1. No discrete epistemic status (`verified`, `supported`, `contested`, `contradicted`, `unsupported`, `unverifiable`, etc.); it relies solely on continuous float `confidence_score`.
  2. No distinction between claim types (event fact, causal hypothesis, numerical measurement, verbatim quote, scientific law).
  3. No consensus classification (`STRONG_CONSENSUS`, `ACTIVE_DEBATE`, `CONTESTED`, etc.).
  4. No passage-level grounding; sources are pointed to as whole web pages without passage text, character offsets, or entailment relationships.
  5. Contradictions are not modeled; `corroborating_sources` only captures positive reinforcement, ignoring dissenting or refuting evidence.
  6. No temporal bounding (`valid_from`, `valid_until`, `as_of_date`).
  7. No verifier provenance (strategy used, verifier name, execution timestamp, trace ID).

- **`ResearchDossier` (`contracts.py:240-255`)**:
  Contains `claims: List[ClaimRecord]`, `talking_points: List[TalkingPointRecord]`, `statistics: List[StatisticRecord]`. It aggregates claims but provides no machine-readable evidence graph or normalized source repository.

- **`ScriptBeat` (`contracts.py:353-385`), `ScriptScene` (`contracts.py:387-420`), `Script` (`contracts.py:422-458`)**:
  `ScriptBeat` contains `beat_id`, `start_time`, `end_time`, `duration`, `text`, `visual_cue`, `emphasis_words`. Neither `ScriptBeat` nor `ScriptScene` possesses any foreign key reference to `claim_id` or evidence units. There is zero linkage between speech beats and the factual claims that purportedly ground them.

#### B. `src/models/ir.py` (Production Intermediate Representation AST)
- `IRBlockType` (`ir.py:33-42`): Defines the 7 canonical visual blocks (`REFERENCE_COLLAGE_HOOK`, `SPLIT_SCREEN_INTRO`, `QUOTE_HIGHLIGHT`, `TIMELINE_REVEAL`, `STATISTIC_REVEAL`, `COMPARISON_PANEL`, `CREATOR_BOTTOM_COLLAGE`).
- `IRVisualBlockNode` (`ir.py:139-172`): Contains `parameters` and `asset_bindings`. In components like `STATISTIC_REVEAL` and `TIMELINE_REVEAL`, parameters contain raw strings (e.g. `stat_number: "90%+"`, `year: "1947"`), but have zero pointers to backing dataset claims or verified evidence units.
- `ProductionIRDocument` (`ir.py:246-374`): Enforces temporal conservation and asset manifest integrity, but performs zero semantic or numerical validation between narration text and visual parameters.

#### C. `src/research/engine.py` & `src/research/scoring.py` (Research Pipeline)
- `ResearchEngine._synthesize_live()` (`engine.py:106-273`): Splits search snippets into sentences (between 40 and 280 characters), creates `Source` objects, and assigns corroborating sources based on domain dissimilarity.
- `score_claim()` (`scoring.py:161-203`):
  $$\text{Confidence} = w_{\text{auth}} \cdot A + w_{\text{corrob}} \cdot C + w_{\text{clarity}} \cdot Q - P_{\text{conflict}}$$
  Where:
  - $A$ (Authority): Static domain lookup (`TIER_1_DOMAINS`, `TIER_2_DOMAINS`, `TIER_3_DOMAINS`, `.gov`/`.edu`).
  - $C$ (Corroboration): Count of distinct domain roots.
  - $Q$ (Clarity): Regex matching 4-digit years, metric suffixes, and capitalized words.
  - $P_{\text{conflict}}$: Fixed 0.25 penalty if keyword matching finds terms like "disputed", "alleged", "controversial".
  *Direct Finding*: The confidence score is a shallow retrieval heuristic. It does NOT evaluate whether the text of the source logically entails the claim, whether historical consensus exists, or whether numbers are empirically verified.

#### D. `src/editorial/angle_generator.py` & `src/editorial/scorecard.py` (Editorial Engine)
- `AngleGenerator.generate_candidates()` (`angle_generator.py:47-93`): Concatenates all claim strings into a single unstructured string: `claims_text = " ".join([c.claim_text for c in dossier.claims])`.
- `EditorialScorer._eval_evidence_availability()` (`scorecard.py:271-300`):
  Computes score purely from `len(claims)` ($+0.06$ per claim), average confidence score ($+0.15 \cdot \text{avg}$), and `len(stats)` ($+0.02$ per stat).
  *Direct Finding*: It checks quantity and heuristic confidence, not topical entailment. An angle proposing a completely contradicted or debunked thesis receives a high evidence availability score simply because the dossier contains numerous claims.

#### E. `src/scriptwriting/generator.py` (Scriptwriting Engine)
- `synthesize_scenes_from_dossier()` (`generator.py:351-450`):
  Constructs scene voiceover by string formatting:
  `narration = f"{tp.title}. {tp.narrative_hook} {claim_text}"`.
  *Direct Finding*: The narration is generated in an open-ended manner. Once generated, there is no post-script verification step to extract claims, verify that numbers were not altered, ensure quotes were not fabricated, or check that hedged claims were not converted into unhedged absolutes.

#### F. `src/orchestrator/state_machine.py` (Lifecycle State Machine)
- `ProductionState` (`state_machine.py:14-61`): Contains 17 canonical states:
  `CREATED` $\to$ `RESEARCH_PLANNED` $\to$ `RESEARCH_IN_PROGRESS` $\to$ `RESEARCH_COMPLETED` $\to$ `EDITORIAL_ANALYSIS` $\to$ `ANGLE_SELECTED` $\to$ `OUTLINE_APPROVED` $\to$ `SCRIPTING_IN_PROGRESS` $\to$ `SCRIPT_COMPLETED` $\to$ `VOICE_GENERATED` $\to$ `VOICE_QA_PASSED` $\to$ `ASSETS_DISCOVERED` $\to$ `ASSETS_FROZEN` $\to$ `COMPOSITION_GENERATED` $\to$ `RENDER_IN_PROGRESS` $\to$ `RENDER_COMPLETED` $\to$ `COMPLETED`.
  *Direct Finding*: There are currently no explicit verification gate states for research verification, script fact-checking, visual fact-checking, or final epistemic QA.

#### G. `src/h9_runtime/bridge.py` & `tools/h9_content_tools.py` (Runtime & Tools)
- `HermesCapabilityBridge` implements unified facade protocols (`AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`).
- `delegate_research()` (`bridge.py:608-640`): Fallback creates minimal `ClaimRecord` and `SourceRecord`.
- `tools/h9_content_tools.py`: Exposes 5 content tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, `h9.publish`) gated by `check_h9_available()`. Lacks epistemic verification tools.

---

### 1.2 Baseline Verification Execution

To establish empirical ground truth regarding current test pass rates and backward compatibility, the existing test suites were executed via `uv run pytest`:

1. **Production Contracts Suite (`tests/test_contracts.py`)**:
   ```powershell
   uv run pytest tests/test_contracts.py -q
   ```
   **Output:** `12 passed in 12.26s` (100% pass rate).
   Verified: `CreatorProfile`, `ContentBrief`, `ResearchPlan`, `SourceRecord`, `ClaimRecord`, `ResearchDossier`, `EditorialScorecard`, `ContentOutline`, `Script`, `AssetRequirement`, `AssetRecord`, `EvaluationReport`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`.

2. **Accepted Hermes × H9 Runtime Coupling Suite (`tests/test_h9_acceptance.py`)**:
   ```powershell
   uv run pytest tests/test_h9_acceptance.py -q
   ```
   **Output:** `44 passed in 69.63s` (100% pass rate).
   Verified all 8 required acceptance dimensions:
   - Dimension A (Runtime Coupling & Typed Contracts): 5/5 passed.
   - Dimension B (Skill Coupling & Production IR): 5/5 passed.
   - Dimension C (Provider Coupling & Fallbacks): 5/5 passed.
   - Dimension D (Tool Coupling & Registry): 5/5 passed.
   - Dimension E (Subagent Research Delegation): 5/5 passed.
   - Dimension F (Permission Tokens & Guard): 7/7 passed.
   - Dimension G (Sandbox & Execution Isolation): 6/6 passed.
   - Dimension H (End-to-End Artifact Generation): 6/6 passed.

---

## 2. Logic Chain

From the direct observations above, the logical progression to the required Epistemic Verification Layer architecture follows five deductive steps:

1. **Premise 1: Research Confidence $\ne$ Epistemic Verification**
   - *Observation*: `scoring.py` derives `confidence_score` purely from domain name matching (`.edu`, `.gov`, `.org`), regex date detection, and keyword counts.
   - *Deduction*: A claim can have high confidence in `scoring.py` while being completely contradicted by primary scholarship or containing inaccurate numbers. Epistemic verification must evaluate logical entailment, source tier, consensus state, and empirical data, strictly decoupled from research retrieval confidence.

2. **Premise 2: Script Synthesis Introduces Hallucinations & Distortions**
   - *Observation*: `generator.py` concatenates claim text with creative hooks and titles into narrative voiceover beats.
   - *Deduction*: Creative language generation inherently tends to strengthen claims (removing uncertainty qualifiers), round/transpose numbers, paraphrase quotes, or introduce unverified narrative flourishes. Independent post-script claim extraction and re-verification against the evidence graph is mathematically necessary to catch script-level drift.

3. **Premise 3: Visual Components Present Factual Assertions Independent of Narration**
   - *Observation*: `ProductionIRDocument` in `ir.py` compiles `STATISTIC_REVEAL`, `TIMELINE_REVEAL`, and `QUOTE_HIGHLIGHT` visual blocks using props passed from creative stages.
   - *Deduction*: Even if a voiceover is factual, an on-screen graphic displaying "100 Billion Transistors" or "December 1948" can be factually wrong or inconsistent with narration. Visual elements must be explicitly bound to claims and verified via a dedicated visual fact-checker.

4. **Premise 4: Historical Claims Require Consensus Modeling, Not Semantic Averaging**
   - *Observation*: Current `ClaimRecord` only holds `primary_source` and `corroborating_sources`.
   - *Deduction*: When historical sources disagree (e.g. regarding causal factors or specific dates), averaging their claims or picking the most frequent web result produces historical inaccuracy. Contradictions must be preserved as explicit opposing edges in an Evidence Graph, and classified into explicit consensus states (`STRONG_CONSENSUS`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`).

5. **Premise 5: Non-Breaking Contract Extension Via Pydantic v2 Invariants**
   - *Observation*: `H9BaseModel` specifies `ConfigDict(extra="allow", validate_assignment=True)`. Existing tests instantiate `SourceRecord(title=..., url=...)` and `ClaimRecord(claim_id=..., claim_text=..., primary_source=...)`.
   - *Deduction*: Extending `SourceRecord` and `ClaimRecord` with new fields that have default values or `Optional` types will maintain 100% backward compatibility with all existing tests, while granting new epistemic subsystems access to rich structured evidence.

---

## 3. Key Findings

| Subsystem | Existing Implementation State | Observed Epistemic Vulnerability / Gap | Architectural Requirement |
|---|---|---|---|
| **Contracts (`contracts.py`)** | Lightweight Pydantic v2 models (`ClaimRecord`, `SourceRecord`). | No discrete epistemic statuses, no evidence passage links, no temporal bounds, no consensus states. | Extend with discrete `EpistemicStatus`, `ClaimType`, `ConsensusState`, `EvidenceUnitLink`, `TemporalContext`, `VerifierMetadata`. |
| **Research (`research/`)** | Web query expansion, snippet sentence extraction, heuristic confidence scoring (`scoring.py`). | Decoupled from textual entailment; no passage offsets; no multi-tier academic source filtering. | Multi-strategy verification engine; 13-tier source taxonomy; passage extraction; strict decoupling of verification from confidence. |
| **Editorial (`editorial/`)** | 5-archetype angle generator; 9-dimension scorecard (`evidence_availability`). | Scores evidence availability purely on claim count and average confidence, ignoring angle thesis truth. | Angle thesis verification gate; checking whether candidate angle premises conflict with established consensus. |
| **Scriptwriting (`scriptwriting/`)** | Procedural/LLM narrative generation combining hooks, titles, and claims. | Script prose strengthens claims, fabricates quotes, alters numbers, or drops hedges without audit. | Post-script claim extraction (`h9.extract_claims`) and re-verification against evidence graph. |
| **Visual IR (`models/ir.py`)** | 7 canonical HyperFrames component blocks parameterizing animations and assets. | Component props (numbers, dates, quotes) have no ground-truth lineage back to source evidence. | Visual fact-checking linking on-screen text/metrics to verified claim records and deterministic datasets. |
| **Lifecycle (`state_machine.py`)** | 17 sequential states (`CREATED` to `COMPLETED`) with deterministic transitions. | No factual quality gates; production can proceed to render and publish even if claims are contested. | 4 verification gates (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`). |
| **Hermes Tools (`tools/`)** | 5 content tools (`h9.research`, `h9.discover_assets`, `h9.generate_script`, `h9.render`, `h9.publish`). | No native tools for verifying claims, quotes, numbers, or running epistemic gates. | Register 9 native epistemic tools in toolset `h9_content` gated by `check_h9_available()`. |

---

## 4. Recommended Contract Additions & Evidence Graph Architecture

### 4.1 Recommended Contract Extensions (`src/models/contracts.py`)

All contract additions are designed with strict defaults to guarantee 100% backward compatibility:

#### A. Core Epistemic Enums
```python
class EpistemicStatus(str, Enum):
    """Granular machine-readable epistemic verification statuses."""
    VERIFIED = "verified"                    # Supported by multiple high-tier independent sources
    SUPPORTED = "supported"                  # Entailed by at least one reliable source without contradiction
    PARTIALLY_SUPPORTED = "partially_supported" # Core fact supported, but details/numbers differ
    CONTESTED = "contested"                  # Legitimate scholarly or factual dispute exists
    CONTRADICTED = "contradicted"            # Refuted by authoritative counter-evidence
    UNSUPPORTED = "unsupported"              # No cited evidence entails the assertion
    UNVERIFIABLE = "unverifiable"            # Cannot be empirically or textually confirmed
    OUTDATED = "outdated"                    # Was true historically, but superseded by newer data
    MISLEADING = "misleading"                # Technically true in isolation, but contextually deceptive
    OPINION = "opinion"                      # Subjective or aesthetic judgment, not a verifiable fact
    PREDICTION = "prediction"                # Forward-looking forecast, not yet factual


class ClaimType(str, Enum):
    """Structural typology of factual claims dictating verification policy."""
    EVENT_FACT = "event_fact"                # Historical or physical occurrence with date/place
    CAUSAL_INTERPRETATION = "causal_interpretation" # Explanatory theory for why an event occurred
    SCHOLARLY_INTERPRETATION = "scholarly_interpretation" # Historiographical consensus or hypothesis
    NUMERICAL_METRIC = "numerical_metric"    # Quantitative measurement, count, percentage, speed
    DIRECT_QUOTE = "direct_quote"            # Exact speech or written statement attributed to an entity
    SCIENTIFIC_LAW = "scientific_law"        # Empirically validated physical or algorithmic principle
    CURRENT_EVENT = "current_event"          # Recent news occurrence
    DEFINITIONAL = "definitional"            # Terminology or semantic definition


class ConsensusState(str, Enum):
    """Consensus classifications mandated by the Historical Scholarship Policy."""
    STRONG_CONSENSUS = "STRONG_CONSENSUS"    # Overwhelming agreement across primary & scholarly literature
    BROAD_CONSENSUS = "BROAD_CONSENSUS"      # Majority academic agreement with negligible dissent
    MAJORITY_INTERPRETATION = "MAJORITY_INTERPRETATION" # Dominant school of thought, but noted alternatives
    MINORITY_INTERPRETATION = "MINORITY_INTERPRETATION" # Credible academic dissent held by a minority
    ACTIVE_DEBATE = "ACTIVE_DEBATE"          # Substantial ongoing historiographical or scientific debate
    CONTESTED = "CONTESTED"                  # Open dispute between mutually exclusive primary accounts
    UNRESOLVED = "UNRESOLVED"                # Insufficient evidence to determine factual truth
    INSUFFICIENT_LITERATURE = "INSUFFICIENT_LITERATURE" # Not enough scholarly work exists to establish consensus
```

#### B. 13-Tier Source Taxonomy Enum
```python
class SourceTier(int, Enum):
    """13-tier hierarchical source taxonomy ranking epistemic authority."""
    PRIMARY_SOURCE = 1                       # Archival records, contemporaneous documents, raw datasets
    PEER_REVIEWED_JOURNAL = 2                # Nature, Science, IEEE, peer-reviewed academic articles
    ACADEMIC_PRESS_BOOK = 3                  # University press monographs (Oxford, Cambridge, MIT)
    HISTORICAL_DOCUMENT_CRITICAL_EDITION = 4 # Scholarly edited and annotated historical source editions
    GOVERNMENT_RECORD_STATISTICAL_AGENCY = 5 # US Census, BLS, NIST, NASA technical reports
    PREPRINT_SCHOLARLY = 6                   # arXiv, bioRxiv preprints
    SPECIALIZED_SCHOLARLY_DATABASE = 7       # PDB, UniProt, ChEMBL, curated scientific repositories
    REPUTABLE_NEWS_INVESTIGATIVE = 8         # Reuters, AP, BBC, NYT investigative reports
    GENERAL_ENCYCLOPEDIC = 9                 # Britannica, Stanford Enc. Philosophy, curated Wikipedia
    CORPORATE_WHITE_PAPER = 10               # Industry technical reports, vendor architecture manuals
    BLOG_OPINION_COMMENTARY = 11             # Expert blogs, Substack, op-eds (opinions only)
    SOCIAL_MEDIA_FORUM = 12                  # Twitter, Reddit, forums (cannot establish facts)
    UNVERIFIED = 13                          # Anonymous aggregators, ungrounded LLM outputs, content farms
```

#### C. Extended Structured Records
```python
class EvidenceUnitLink(H9BaseModel):
    """Direct ground-truth excerpt link within an external source."""
    evidence_unit_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    verbatim_excerpt: str = Field(..., min_length=1)
    page_or_section: Optional[str] = None
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None
    entailment_relation: str = "SUPPORTS"    # "SUPPORTS", "REFUTES", "HEDGES"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TemporalContext(H9BaseModel):
    """Temporal validity anchoring for a factual claim."""
    valid_from: Optional[str] = None         # ISO-8601 or partial date (e.g. "1947-12-23")
    valid_until: Optional[str] = None
    as_of_date: Optional[str] = None
    is_time_sensitive: bool = False
    temporal_status: str = "historical"      # "current", "historical", "obsolete"


class VerifierMetadata(H9BaseModel):
    """Execution audit trail for claim verification."""
    strategy_used: str = "SOURCE_ENTAILMENT" # Strategy identifier
    verifier_name: str = "EpistemicVerificationEngine"
    verified_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    verification_trace_id: str = ""
    verification_method: str = "deterministic_offline"
    entailment_score: float = Field(default=1.0, ge=0.0, le=1.0)
    contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SourceRecord(H9BaseModel):
    """Extended source citation with 13-tier taxonomy and integrity checksums."""
    source_id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:8]}")
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    tier: SourceTier = SourceTier.REPUTABLE_NEWS_INVESTIGATIVE
    domain_authority: float = Field(default=0.8, ge=0.0, le=1.0)
    doi: Optional[str] = None
    peer_reviewed: bool = False
    archived_url: Optional[str] = None
    content_sha256: Optional[str] = None
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_sanitized: bool = True                # Neutralizes prompt injection in scraped content
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClaimRecord(H9BaseModel):
    """Factual claim backed by executable epistemic semantics and evidence links."""
    claim_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    category: str = Field(default="general")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0) # Retrieval confidence
    primary_source: SourceRecord
    corroborating_sources: List[SourceRecord] = Field(default_factory=list)
    visual_cue_suggestion: str = ""
    verification_notes: str = ""
    
    # Executable Epistemic Semantics
    epistemic_status: EpistemicStatus = EpistemicStatus.SUPPORTED
    claim_type: ClaimType = ClaimType.EVENT_FACT
    consensus_state: ConsensusState = ConsensusState.BROAD_CONSENSUS
    evidence_links: List[EvidenceUnitLink] = Field(default_factory=list)
    contradicting_sources: List[SourceRecord] = Field(default_factory=list)
    temporal_context: Optional[TemporalContext] = None
    verifier_metadata: Optional[VerifierMetadata] = None
    numeric_data_lineage: Optional[Dict[str, Any]] = None
    quote_metadata: Optional[Dict[str, Any]] = None
```

#### D. Script & Visual IR Grounding Additions
- In `ScriptBeat`: Add `grounded_claim_ids: List[str] = Field(default_factory=list)`, `evidence_unit_ids: List[str] = Field(default_factory=list)`, `is_factual_assertion: bool = True`, and `verification_status: str = "UNCHECKED"`.
- In `ScriptScene`: Add `grounded_claim_ids: List[str] = Field(default_factory=list)` and `visual_claim_bindings: Dict[str, str] = Field(default_factory=dict)` (mapping component slot to `claim_id`).
- In `Script`: Add `epistemic_verification_report: Optional[Dict[str, Any]] = None`.
- In `IRVisualBlockNode`: Add `claim_bindings: Dict[str, str] = Field(default_factory=dict)` (e.g. `{"stat_number": "claim_03"}`).

---

### 4.2 Evidence Graph Abstraction Architecture

The Evidence Graph is a machine-readable, directed acyclic grounding graph connecting sources to rendered pixels and audio beats:

```
[SourceRecord (Tier 1-13)] 
         │ (provides)
         ▼
  [PassageNode] (raw text & offsets)
         │ (yields)
         ▼
[EvidenceUnitNode] (atomic assertion, modality)
    │           │
    │ (entails) │ (refutes / contradicts)
    ▼           ▼
 [ClaimRecord] ◄──────► [ClaimRecord] (corroborates / contests)
    │
    ├──────────────────────────┐
    │ (grounds)                │ (binds to)
    ▼                          ▼
[ScriptSentenceNode]     [VisualElementNode] (StatisticReveal, Timeline, Quote)
    │                          │
    ▼                          ▼
[ScriptBeatNode] ────────► [IRSceneNode]
```

#### Graph Entity Invariants:
1. **No Orphan Verified Claims**: A claim cannot hold `EpistemicStatus.VERIFIED` or `EpistemicStatus.SUPPORTED` without at least one incoming `SUPPORTS` edge from an `EvidenceUnitNode`.
2. **Preservation of Contradiction**: When sources conflict, opposing evidence units are linked via `CONTESTS` or `CONTRADICTS` edges. The claim's `consensus_state` transitions to `ACTIVE_DEBATE` or `CONTESTED`. Numerical or semantic averaging is explicitly rejected.
3. **Reconstructability & Hermetic Portability**: The entire graph serializes to an `EvidenceGraphDocument` (JSON-LD / Pydantic v2 format). It can be reconstructed offline from `ResearchDossier` or audit fixtures without network access.
4. **Visual & Acoustic Traceability**: Every rendered metric in `IRVisualBlockNode` and every factual sentence in `ScriptBeat` contains a verifiable path traversing backward to an `EvidenceUnitNode` and a `SourceRecord`.

---

## 5. The 13-Tier Source Taxonomy & Policy Dispatch

### 5.1 Authoritative Source Taxonomy Hierarchy

| Tier | Category Name | Authority Baseline | Admissible Scope | Disallowed Uses |
|---|---|---|---|---|
| **Tier 1** | `PRIMARY_SOURCE` | 1.00 | Archival records, treaties, patents, lab notebooks, raw datasets. | Modern scholarly interpretations. |
| **Tier 2** | `PEER_REVIEWED_JOURNAL` | 0.98 | Scientific laws, empirical findings, peer-reviewed historiography. | Unvetted breaking news. |
| **Tier 3** | `ACADEMIC_PRESS_BOOK` | 0.95 | Comprehensive historiographical consensus, scholarly monographs. | Rapid real-time metrics. |
| **Tier 4** | `HISTORICAL_DOCUMENT_CRITICAL_EDITION` | 0.94 | Authoritative verbatim correspondence, speeches, critical texts. | Unannotated popular reprints. |
| **Tier 5** | `GOVERNMENT_RECORD_STATISTICAL_AGENCY` | 0.92 | Official census, economic indicators, NIST/NASA engineering standards. | Unofficial political claims. |
| **Tier 6** | `PREPRINT_SCHOLARLY` | 0.82 | Emerging scientific discoveries (must hedge as preliminary). | Establishing historical consensus. |
| **Tier 7** | `SPECIALIZED_SCHOLARLY_DATABASE` | 0.90 | Curated scientific identifiers (PDB, UniProt, ChEMBL). | Qualitative narrative arcs. |
| **Tier 8** | `REPUTABLE_NEWS_INVESTIGATIVE` | 0.80 | Contemporary current events, investigative journalism. | Sole source for historical facts. |
| **Tier 9** | `GENERAL_ENCYCLOPEDIC` | 0.75 | Topic framing, initial query expansion. | Sole source for facts/interpretations. |
| **Tier 10** | `CORPORATE_WHITE_PAPER` | 0.70 | Vendor specifications, architectural documentation. | Objective competitive comparisons. |
| **Tier 11** | `BLOG_OPINION_COMMENTARY` | 0.40 | Creator perspective, subjective commentary. | Establishing factual claims. |
| **Tier 12** | `SOCIAL_MEDIA_FORUM` | 0.20 | Gauging cultural sentiment, informal discussion. | Any factual evidence ground truth. |
| **Tier 13** | `UNVERIFIED` | 0.05 | None (rejected as untrusted input). | Any factual assertion. |

### 5.2 Claim-Type Verification Policy Dispatch Matrix

```
                      ┌────────────────────────────────────────┐
                      │ Incoming Claim / Script Assertion      │
                      └──────────────────┬─────────────────────┘
                                         │
                         [Inspect ClaimType & Domain]
                                         │
         ┌───────────────────┬───────────┴─────────┬───────────────────┐
         ▼                   ▼                     ▼                   ▼
 [Historical Event]  [Scholarly Interp]    [Numerical Metric]    [Direct Quote]
         │                   │                     │                   │
   Requires ≥1         Requires Consensus    Requires Dataset    Requires Exact
   Tier 1 or Tier 3/4  State Modeling        Lineage (Tier 1/5)  Verbatim Match
   (Single Tier 9      (No Contradiction     (Tolerance & Unit   (Tier 1 or 4)
    Blocked)            Averaging)            Match)              (Or Paraphrase)
```

1. **Historical Facts (`ClaimType.EVENT_FACT`)**:
   - **Policy**: Must be backed by at least one Tier 1 (`PRIMARY_SOURCE`) or Tier 3/4 (`ACADEMIC_PRESS_BOOK` / `HISTORICAL_DOCUMENT_CRITICAL_EDITION`), or corroborated by at least two independent Tier 2/3 sources.
   - **Hard Prohibition**: Popular web summaries (Tier 9 `GENERAL_ENCYCLOPEDIC`, Tier 10 `CORPORATE_WHITE_PAPER`, or Tier 11 `BLOG_OPINION`) are strictly blocked from acting as the sole establishing source.
2. **Scholarly & Causal Interpretations (`ClaimType.SCHOLARLY_INTERPRETATION`)**:
   - **Policy**: Must explicitly identify the `ConsensusState`. If `ACTIVE_DEBATE` or `CONTESTED`, script generation must calibrate its language (e.g. *"While historians widely agree that X occurred, debate remains whether Y or Z was the primary driver"*).
   - **Hard Prohibition**: Contradictions must never be resolved by numerical averaging or by arbitrarily picking one side without qualification.
3. **Numerical Metrics (`ClaimType.NUMERICAL_METRIC`)**:
   - **Policy**: Requires exact matching against Tier 5 (`GOVERNMENT_RECORD_STATISTICAL_AGENCY`) or Tier 1/2 datasets. The verification engine checks metric name, numerical value, units, baseline year, and tolerance window ($\pm \epsilon$).
   - **Hard Prohibition**: Unrounded script numbers that diverge from source data by $>0.1\%$ without explicit approximation words ("approximately", "roughly") fail verification.
4. **Direct Quotes (`ClaimType.DIRECT_QUOTE`)**:
   - **Policy**: Must match verbatim text from a primary historical edition (Tier 1 or 4) with normalized whitespace/punctuation.
   - **Hard Prohibition**: Fabricated quotes or quotes attributed to the wrong historical figure trigger an immediate `BLOCK` gate. Quotations with minor omissions must include standard ellipses or be converted into a paraphrase.

---

## 6. Lifecycle State Machine Integration & Hard Gates

To enforce epistemic rigor across video production, 4 verification gates are integrated into `src/orchestrator/state_machine.py`:

```
[RESEARCH_COMPLETED]
         │
         ▼
[RESEARCH_VERIFICATION]  ──(BLOCK)──► [FAILED]
         │ (PASS / WARN)
         ▼
[EDITORIAL_ANALYSIS]
         │
        ...
         ▼
[SCRIPT_COMPLETED]
         │
         ▼
  [SCRIPT_FACT_CHECK]    ──(BLOCK / HUMAN_REVIEW)──► [PAUSED_FOR_HUMAN] / [FAILED]
         │ (PASS / WARN)
         ▼
[VOICE_GENERATED]
         │
        ...
         ▼
[COMPOSITION_GENERATED]
         │
         ▼
  [VISUAL_FACT_CHECK]    ──(BLOCK)──► [FAILED]
         │ (PASS / WARN)
         ▼
[RENDER_IN_PROGRESS]
         │
         ▼
 [RENDER_COMPLETED]
         │
         ▼
 [FINAL_EPISTEMIC_QA]    ──(BLOCK)──► [FAILED] (Publish Blocked)
         │ (PASS)
         ▼
    [COMPLETED]
```

### Deterministic Gate Outcomes:
1. `PASS`: All mandatory verification policies satisfied. Pipeline proceeds automatically.
2. `WARN`: Minor discrepancies (e.g. non-critical numerical rounding, lack of secondary corroboration on low-stakes background fact). Transition proceeds, but warnings are appended to `PublishPackage.metadata["epistemic_warnings"]`.
3. `HUMAN_REVIEW`: Contentious historical debate or ambiguous quote detected. State machine transitions to `PAUSED_FOR_HUMAN`, generating an audit report for creator approval.
4. `BLOCK`: Hard failure (hallucinated quote, contradicted historical fact, ungrounded statistic, prompt injection attempt). State transitions to `FAILED` or aborts publish. Production cannot publish while a mandatory gate is in `BLOCK`.

---

## 7. Hermes Runtime Tools & Security Enforcement

### 7.1 Native Hermes Model Tools Catalog
Conforming to Rung 3 of the Footprint Ladder, verification capabilities are registered as native Hermes tools under the named toolset `h9_content` gated by `check_h9_available()`:

1. `h9.extract_claims`: Deconstructs script narration or research text into atomic `ClaimRecord` propositions.
2. `h9.verify_claim`: Runs multi-strategy verification (`SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`) against the evidence graph.
3. `h9.verify_script`: Full audit comparing generated script beats against research dossier claims.
4. `h9.verify_quote`: Verifies verbatim quotation accuracy and attribution against primary sources.
5. `h9.verify_numbers`: Deterministic verification of numerical metrics, units, and dates against dataset baselines.
6. `h9.analyze_historical_consensus`: Evaluates historiographical literature to classify `ConsensusState`.
7. `h9.detect_contradictions`: Graph traversal identifying mutually exclusive assertions between sources.
8. `h9.verify_visual_claims`: Verifies that HyperFrames visual component parameters (`stat_number`, `year`) match narration.
9. `h9.epistemic_gate`: Evaluates all stage verification traces and returns deterministic `PASS`, `WARN`, `HUMAN_REVIEW`, or `BLOCK`.

### 7.2 Untrusted Content Sanitization & Security Boundary
Scraped web documents and third-party texts are untrusted inputs. Under `src/security/`:
- Raw scraped content is quarantined before ingestion.
- System prompt delimiters (`---`, ````system`, `Ignore previous instructions`) and authority-escalation triggers are sanitized.
- Evidence graph nodes preserve immutable SHA-256 digests (`content_sha256`) of raw fetched data to prevent citation tampering or cache manipulation.

---

## 8. Backward Compatibility & Verification Recommendations

### 8.1 Backward Compatibility Impact Analysis

1. **Pydantic v2 `extra="allow"` Compatibility**:
   `H9BaseModel` specifies `ConfigDict(extra="allow", validate_assignment=True)`. All proposed new fields on `SourceRecord`, `ClaimRecord`, `ScriptBeat`, `ScriptScene`, `Script`, and `ResearchDossier` have safe default values (e.g. `epistemic_status: EpistemicStatus = EpistemicStatus.SUPPORTED`, `tier: SourceTier = SourceTier.REPUTABLE_NEWS_INVESTIGATIVE`).
   *Proof*: Existing tests instantiate `SourceRecord(title="...", url="...")` and `ClaimRecord(claim_id="...", claim_text="...", primary_source=...)`. These will continue to initialize and validate with zero errors.

2. **Acceptance Suite Invariants (`tests/test_h9_acceptance.py`)**:
   - `test_e03_research_subagent_returns_verified_dossier` checks:
     `isinstance(dossier, ResearchDossier)`, `isinstance(dossier.claims[0], ClaimRecord)`, `isinstance(dossier.claims[0].primary_source, SourceRecord)`. Because `ClaimRecord` and `SourceRecord` remain the exact same Pydantic classes with added optional fields, `test_e03` and all other Dimension E tests pass unconditionally.
   - `test_b01-b05` checks Production IR AST validation. Adding optional `claim_bindings` to `IRVisualBlockNode` preserves existing AST invariants (temporal contiguity, audio track length, asset binding integrity).
   - `test_d01-d05` checks tool registration. Adding new model tools to the existing `h9_content` toolset preserves existing tool aliases and registration tests.

3. **Subsystem Migration Path**:
   - `src/research/engine.py`: Wrap existing output in `ResearchDossier` with newly populated `evidence_links` and `epistemic_status`.
   - `src/editorial/scorecard.py`: Enhance `_eval_evidence_availability()` to penalize `EpistemicStatus.CONTRADICTED` and reward `EpistemicStatus.VERIFIED`.
   - `src/scriptwriting/generator.py`: Maintain `synthesize_scenes_from_dossier()`, while annotating each generated `ScriptBeat` with `grounded_claim_ids`.

---

## 9. Caveats & Risks

1. **Hermetic vs. Live Scholarly Connectors**:
   - *Observation*: Live scholarly search APIs (Crossref, Semantic Scholar, Tavily, Exa) require active API keys and network connectivity.
   - *Mitigation*: The benchmark evaluation suite (`H9-FactBench`) and regression test suites must provide hermetic offline test fixtures (curated JSON/YAML evidence graphs in `tests/fixtures/epistemic/`) ensuring tests run 100% reliably in CI/CD without external network dependencies.
2. **LLM Entailment Latency & Determinism**:
   - *Observation*: Running deep LLM-based textual entailment verification on dozens of extracted claims could increase pipeline execution latency.
   - *Mitigation*: Implement hybrid verification: fast deterministic regex/rule checks for numbers, dates, and domain authority, combined with batched subagent entailment checks only for high-stakes or contested claims.
3. **Historical Nuance & Subjectivity**:
   - *Observation*: Historical interpretations rarely boil down to binary true/false.
   - *Mitigation*: The 8-state `ConsensusState` taxonomy avoids artificial binary flattening by explicitly representing `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, and `ACTIVE_DEBATE`, calibrating script language rather than suppressing legitimate historical schools of thought.

---

## 10. Conclusion

The existing Harness 9 architecture provides a solid, highly modular foundation with strict Pydantic v2 contracts, a deterministic 17-state lifecycle machine, and clean Hermes runtime coupling. However, its factual grounding layer currently relies on shallow domain heuristics, leaving scriptwriting and visual rendering vulnerable to hallucinations, strengthened assertions, altered numbers, and distorted quotations.

By introducing:
1. Extended `ClaimRecord` and `SourceRecord` schemas with executable epistemic semantics,
2. A machine-readable, reconstructable `EvidenceGraph` abstraction,
3. A 13-tier source taxonomy enforcing the Historical Scholarship Policy,
4. Post-script claim extraction and visual fact-checking,
5. Hard state machine verification gates (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`), and
6. 9 native Hermes model tools,

the Harness 9 Epistemic Verification Layer will ensure that every published video is rigorously grounded in verifiable evidence, historical scholarship, and empirical data, while maintaining 100% backward compatibility with all existing acceptance suites.

---

## 11. Verification Method

To independently verify the observations, contract validity, and backward compatibility reported herein:

1. **Verify Contract Schemas**:
   ```powershell
   uv run pytest tests/test_contracts.py -v
   ```
   *Expected Result*: All 12 tests pass cleanly (100%).

2. **Verify Hermes × H9 Runtime Acceptance Suite**:
   ```powershell
   uv run pytest tests/test_h9_acceptance.py -v
   ```
   *Expected Result*: All 44 tests across Dimensions A through H pass cleanly with 0 failures and 0 errors.

3. **Verify File Paths & Line Locations**:
   - `src/models/contracts.py:197-217` (`SourceRecord`, `ClaimRecord`)
   - `src/models/ir.py:33-42, 139-172` (`IRBlockType`, `IRVisualBlockNode`)
   - `src/research/engine.py:106-273` (`_synthesize_live`)
   - `src/research/scoring.py:161-203` (`score_claim`)
   - `src/editorial/scorecard.py:271-300` (`_eval_evidence_availability`)
   - `src/scriptwriting/generator.py:351-450` (`synthesize_scenes_from_dossier`)
   - `src/orchestrator/state_machine.py:14-61, 116-225` (`ProductionState`, `VALID_TRANSITIONS`)
   - `tools/h9_content_tools.py:1-120` (`h9_content` toolset)

4. **Invalidation Conditions**:
   - Any failure in `tests/test_contracts.py` or `tests/test_h9_acceptance.py` invalidates the backward compatibility claims.
   - Any removal of Pydantic `extra="allow"` from `H9BaseModel` invalidates the safe non-breaking contract extension design.
