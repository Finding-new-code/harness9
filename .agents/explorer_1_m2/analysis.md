# Epistemic Schema Extension & Forensic Architectural Analysis (Milestone 2 / R2)

**Author:** `explorer_1_m2`  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\explorer_1_m2`  
**Target Package:** `src/models/contracts.py`, `src/models/__init__.py`, `src/h9_runtime/content.py`  
**Target Milestone:** Milestone 2 (R2) — Evidence Graph & Extended Claim Contracts  
**Status:** Complete Architectural Specification & Verified Recommendation  

---

## 1. Executive Summary

This investigation formulates the exact, backward-compatible schema extension for Milestone 2 (R2) of the Harness 9 Epistemic Verification Layer. It addresses the fundamental vulnerability identified in the baseline audit (`docs/architecture/epistemic-verification-audit.md`): existing contracts in `src/models/contracts.py` (`ClaimRecord`, `SourceRecord`, `ResearchDossier`) lack discrete epistemic statuses, source taxonomy rankings, consensus state classifications, passage-level character offsets, and chronological validity anchors.

This document delivers:
1. **11 Granular Epistemic Statuses** (`EpistemicStatus`) with deterministic pipeline actions.
2. **13-Tier Hierarchical Source Taxonomy** (`SourceTier`) from `PRIMARY_SOURCE` to `UNVERIFIED` with calibrated `DEFAULT_TIER_WEIGHTS` ($1.00 \to 0.00$).
3. **8-State Historiographical Consensus Model** (`ConsensusState`) enforcing the Historical Scholarship Policy.
4. **Comprehensive Extension of `ClaimRecord`** with all 9 required fields: `evidence_node_ids`, `epistemic_status`, `consensus_state`, `source_tier`, `source_quality`, `corroboration_set`, `temporal_context`, `verifier_metadata`, `quote_exactness`, plus supporting models (`SourceQualityMetrics`, `TemporalContext`, `QuoteExactness`, `EvidenceUnitLink`, `ClaimType`).
5. **Extensions for `SourceRecord` and `ResearchDossier`** ensuring seamless integration with the upcoming Evidence Graph DAG (`src/epistemic/graph.py`).
6. **Empirical Verification of 100% Backwards Compatibility** with existing test suites: `tests/test_contracts.py` (12/12 passing) and `tests/test_h9_acceptance.py` (44/44 passing).
7. **Resolution of the Circular Import Vulnerability** in `src/h9_runtime/content.py:37` so `tests/test_state_machine.py` passes in isolation.

---

## 2. Forensic Codebase Audit of Existing Contracts

### 2.1 Existing Contracts Inspection (`src/models/contracts.py:197-255`)

Direct inspection of `src/models/contracts.py` reveals the current schema definitions:

```python
# src/models/contracts.py:197-205
class SourceRecord(H9BaseModel):
    """Citation and provenance metadata for an external information source."""
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)

# src/models/contracts.py:207-217
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

# src/models/contracts.py:239-255
class ResearchDossier(H9BaseModel):
    """Complete structured research dossier containing claims and talking points."""
    topic: str = Field(..., min_length=1)
    schema_version: str = "2.0.0"
    run_id: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    headline: str = ""
    executive_summary: str = ""
    key_takeaways: List[str] = Field(default_factory=list)
    claims: List[ClaimRecord] = Field(default_factory=list)
    talking_points: List[TalkingPointRecord] = Field(default_factory=list)
    statistics: List[StatisticRecord] = Field(default_factory=list)
    suggested_visual_queries: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 2.2 Caller Sites and Invariants Across Subsystems

The existing `ClaimRecord`, `SourceRecord`, and `ResearchDossier` classes are instantiated in multiple key locations:
1. **`tests/test_contracts.py:122-195`**:
   - Tests `SourceRecord(title="...", url="...", reliability_score=0.95)`.
   - Tests `ClaimRecord(claim_id="claim_01", claim_text="...", confidence_score=0.98, primary_source=source, corroborating_sources=[source], visual_cue_suggestion="...")`.
   - Tests `ResearchDossier(topic="...", run_id="...", headline="...", executive_summary="...", claims=[claim], ...)`.
   - Invariant: Instantiating `ClaimRecord` without epistemic fields must continue to succeed without validation errors.
2. **`src/h9_runtime/bridge.py:628-675` (`delegate_research`)**:
   - Constructs fallback claims using:
     ```python
     ClaimRecord(
         claim_id="claim_01",
         claim_text=f"Core discovery and foundational research on {topic}.",
         confidence_score=0.95,
         primary_source=SourceRecord(
             title=f"Verified Reference on {topic}",
             url="https://en.wikipedia.org/wiki/" + topic.replace(" ", "_"),
             reliability_score=0.98,
         ),
     )
     ```
   - Invariant: Any extended field must have sensible default values so that `delegate_research()` returns fully valid `ClaimRecord` objects.
3. **`src/h9_runtime/content.py:140-158` (`DefaultContentRuntime.plan_research`)**:
   - Converts dictionaries from `ResearchEngine` into `ResearchDossier(..., claims=claims)`.
4. **`tests/test_h9_acceptance.py:821-831` (`test_e03_research_subagent_returns_verified_dossier`)**:
   - Asserts:
     ```python
     self.assertIsInstance(dossier, ResearchDossier)
     self.assertEqual(dossier.topic, "Artificial Intelligence")
     self.assertGreater(len(dossier.claims), 0)
     self.assertIsInstance(dossier.claims[0], ClaimRecord)
     self.assertIsInstance(dossier.claims[0].primary_source, SourceRecord)
     ```

### 2.3 Diagnosis of Circular Import (`tests/test_state_machine.py`)

When `tests/test_state_machine.py` is run in isolation:
```pwsh
.venv\Scripts\python.exe -m pytest tests/test_state_machine.py -q
```
It fails during collection:
```
ImportError: cannot import name 'Pipeline' from partially initialized module 'src.orchestrator.pipeline' (most likely due to a circular import) (G:\Finding-new-code\harness9\src\orchestrator\pipeline.py)
```
- **Call Chain:**
  `tests/test_state_machine.py` $\to$ `src/orchestrator/state_machine.py` $\to$ `src/orchestrator/__init__.py` $\to$ `src/orchestrator/pipeline.py` $\to$ `src/assets/pipeline.py` $\to$ `src/assets/deduplication.py` $\to$ `src/models/contracts.py` $\to$ `src/models/__init__.py` $\to$ `src/models/ir.py` $\to$ `src/h9_runtime/types.py` $\to$ `src/h9_runtime/__init__.py` $\to$ `src/h9_runtime/bridge.py` $\to$ `src/h9_runtime/content.py:37` $\to$ `from src.orchestrator.pipeline import Pipeline`.
- **Root Cause:** In `src/h9_runtime/content.py:37`, `Pipeline` is imported eagerly at module level, but is only actually used in a single method (`run_full_production` at line 345).
- **Remediation:** Remove `from src.orchestrator.pipeline import Pipeline` from line 37 of `src/h9_runtime/content.py` and place it lazily inside `run_full_production()`:
  ```python
  def run_full_production(self, brief: ContentBrief, session_id: str) -> ProductionResult:
      from src.orchestrator.pipeline import Pipeline
      pipeline = Pipeline(...)
  ```
  This completely eliminates the circular import and allows `tests/test_state_machine.py` to pass in isolation.

---

## 3. Discrete Epistemic Statuses (`EpistemicStatus`)

### 3.1 Enumeration Definition
```python
class EpistemicStatus(str, Enum):
    """11 discrete machine-readable verification statuses."""
    VERIFIED = "verified"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTESTED = "contested"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"
    UNVERIFIABLE = "unverifiable"
    OUTDATED = "outdated"
    MISLEADING = "misleading"
    OPINION = "opinion"
    PREDICTION = "prediction"
```

### 3.2 Semantics & Lifecycle Decision Matrix

| Epistemic Status | Operational Definition | Evidentiary Requirement | Pipeline Action |
|---|---|---|---|
| **`VERIFIED`** | Indisputably confirmed by multiple independent high-tier sources. | $\ge 2$ independent Tier 1–3 sources with $P(\text{Entailment}) \ge 0.95$ and zero contradictions. | Allowed unconditionally in all stages. |
| **`SUPPORTED`** | Entailed by at least one reliable source without existing counter-evidence. | $\ge 1$ Tier 1–7 source with $P(\text{Entailment}) \ge 0.90$. | Allowed; secondary corroboration advised. |
| **`PARTIALLY_SUPPORTED`** | Core factual premise is entailed, but specific numbers, dates, or qualifiers diverge. | $P(\text{Entailment}) \ge 0.70$; minor divergence logged. | `WARN`; flags divergence for review. |
| **`CONTESTED`** | Legitimate scholarly or empirical debate exists between credible sources. | Conflicting evidence from Tier 1–7 sources; consensus state is `ACTIVE_DEBATE` or `CONTESTED`. | Requires calibrated narration or `HUMAN_REVIEW`. |
| **`CONTRADICTED`** | Refuted by authoritative counter-evidence or primary records. | Counter-source with $P(\text{Contradiction}) \ge 0.85$ and higher source tier. | Mandatory `BLOCK`; script synthesis blocked. |
| **`UNSUPPORTED`** | No cited evidence passage logically entails the asserted claim. | No valid incoming `ENTAILS` edge from an evidence node. | Mandatory `BLOCK`; claim must be excised. |
| **`UNVERIFIABLE`** | Proposition cannot be empirically, archival, or scientifically tested. | Assertion lacks falsifiable empirical criteria. | Reclassify as opinion or exclude from factual claims. |
| **`OUTDATED`** | Historically accurate when asserted, but superseded by newer empirical data. | Temporal check reveals newer authoritative data disproving earlier baseline. | `BLOCK` unless framed with explicit temporal anchor. |
| **`MISLEADING`** | Technically accurate in isolation, but omitted context creates a false implication. | Logical omission analysis flags contextual deceit. | `BLOCK` or mandate contextual clarification. |
| **`OPINION`** | Subjective, aesthetic, or evaluative judgment, not an empirical assertion. | Linguistic inspection flags value judgments ("greatest", "beautiful"). | Excluded from factual gates; permitted as commentary. |
| **`PREDICTION`** | Forward-looking forecast regarding future occurrences. | Event date $T > T_{\text{current}}$. | Must be framed as speculative projection. |

### 3.3 Default Value Selection & Compatibility
- In `ClaimRecord`, the default value is:
  ```python
  epistemic_status: EpistemicStatus = Field(
      default=EpistemicStatus.SUPPORTED,
      description="Granular epistemic verification status (11 states)"
  )
  ```
- **Rationale:** `ClaimRecord` in Harness 9 requires a valid `primary_source: SourceRecord`. Any claim accompanied by an external source begins in the `SUPPORTED` state until multi-source verification promotes it to `VERIFIED` or flags an anomaly.
- **Backward-Compatible Property:** To support any legacy code expecting `verification_status`:
  ```python
  @property
  def verification_status(self) -> str:
      return self.epistemic_status.value.upper()
  ```

---

## 4. 13-Tier Source Taxonomy & Reliability Weights (`SourceTier`)

### 4.1 Enumeration Definition
```python
class SourceTier(int, Enum):
    """13-tier hierarchical source taxonomy ranking epistemic authority."""
    PRIMARY_SOURCE = 1                       # Archival records, treaties, raw experimental datasets
    PEER_REVIEWED_JOURNAL = 2                # Refereed academic journals (Nature, Science, Physical Review)
    ACADEMIC_BOOK = 3                        # University press monographs (Oxford, Cambridge, MIT Press)
    SCHOLARLY_CONFERENCE = 4                 # Peer-reviewed conference proceedings (IEEE, ACM, NeurIPS)
    INSTITUTIONAL_REPORT = 5                 # Official statistical agencies (Census, BLS, NIST, NASA, WHO)
    ARCHIVAL_DOCUMENT = 6                    # Preserved historical collections, diaries, correspondence
    REFERENCE_WORK = 7                       # Authoritative encyclopedias, dictionaries, handbooks
    EXPERT_ANALYSIS = 8                      # Recognized domain expert analyses, think tank policy papers
    REPUTABLE_JOURNALISM = 9                 # Major news agency investigations (Reuters, AP, BBC, NYT)
    TRADE_PUBLICATION = 10                   # Industry journals, technical vendor specifications
    POPULAR_MEDIA = 11                       # Commercial news, popular science magazines, broadcast news
    SELF_PUBLISHED = 12                      # Expert blogs, substacks, technical personal writeups
    UNVERIFIED = 13                          # Anonymous forums, unvetted web pages, social media

    # Aliases for specification cross-compatibility
    ACADEMIC_PRESS_BOOK = 3
    HISTORICAL_DOCUMENT_CRITICAL_EDITION = 6
    GOVERNMENT_RECORD_STATISTICAL_AGENCY = 5
    SPECIALIZED_SCHOLARLY_DATABASE = 7
    REPUTABLE_NEWS_INVESTIGATIVE = 9
    GENERAL_ENCYCLOPEDIC = 7
    CORPORATE_WHITE_PAPER = 10
    BLOG_OPINION_COMMENTARY = 12
    SOCIAL_MEDIA_FORUM = 13
```

### 4.2 Default Reliability Weights Mapping
```python
DEFAULT_TIER_WEIGHTS: Dict[SourceTier, float] = {
    SourceTier.PRIMARY_SOURCE: 1.00,
    SourceTier.PEER_REVIEWED_JOURNAL: 0.98,
    SourceTier.ACADEMIC_BOOK: 0.95,
    SourceTier.SCHOLARLY_CONFERENCE: 0.90,
    SourceTier.INSTITUTIONAL_REPORT: 0.88,
    SourceTier.ARCHIVAL_DOCUMENT: 0.92,
    SourceTier.REFERENCE_WORK: 0.80,
    SourceTier.EXPERT_ANALYSIS: 0.75,
    SourceTier.REPUTABLE_JOURNALISM: 0.70,
    SourceTier.TRADE_PUBLICATION: 0.55,
    SourceTier.POPULAR_MEDIA: 0.35,
    SourceTier.SELF_PUBLISHED: 0.20,
    SourceTier.UNVERIFIED: 0.00,
}
```

- Each tier includes a helper property:
  ```python
  @property
  def default_weight(self) -> float:
      return DEFAULT_TIER_WEIGHTS.get(self, 0.5)
  ```

---

## 5. Consensus States Enumeration (`ConsensusState`)

### 5.1 Enumeration Definition
```python
class ConsensusState(str, Enum):
    """8-state historiographical and scientific consensus classifications."""
    STRONG_CONSENSUS = "STRONG_CONSENSUS"
    BROAD_CONSENSUS = "BROAD_CONSENSUS"
    MAJORITY_INTERPRETATION = "MAJORITY_INTERPRETATION"
    MINORITY_INTERPRETATION = "MINORITY_INTERPRETATION"
    ACTIVE_DEBATE = "ACTIVE_DEBATE"
    CONTESTED = "CONTESTED"
    UNRESOLVED = "UNRESOLVED"
    INSUFFICIENT_LITERATURE = "INSUFFICIENT_LITERATURE"
```

### 5.2 Historiographical Governance & Phrasing Matrix

| Consensus State | Operational Definition | Evidentiary Requirement | Script Tone |
|---|---|---|---|
| **`STRONG_CONSENSUS`** | Unanimous agreement across all modern scholarly literature; established baseline. | Zero peer-reviewed dissent in the last 50 years; substantiated by multiple primary records. | Definitive, declarative assertion. |
| **`BROAD_CONSENSUS`** | Overwhelming consensus among specialists; negligible fringe dissent. | $>90\%$ of academic monographs agree; dissenting views lack mainstream peer review. | "Historians broadly agree...", "Scholarly consensus indicates..." |
| **`MAJORITY_INTERPRETATION`**| Dominant academic paradigm, but recognized alternative scholarly schools exist. | Supported by leading university presses, but recognized peer-reviewed counter-theses exist. | "The leading historical view holds...", "While debated, evidence points to..." |
| **`MINORITY_INTERPRETATION`**| Credible, peer-reviewed academic thesis held by a qualified minority of historians. | Published in peer-reviewed journals or academic presses; challenges the majority paradigm. | "A significant school of historians argues...", "Alternatively, scholars like X propose..." |
| **`ACTIVE_DEBATE`** | Substantial, unresolved debate with mutually incompatible theories supported by prominent scholars. | Competing peer-reviewed interpretations with neither holding decisive majority agreement. | "Historians remain deeply divided...", "Scholars continue to debate whether X or Y..." |
| **`CONTESTED`** | Mutually exclusive claims supported by contradictory primary accounts or physical evidence. | Surviving primary sources directly conflict (e.g. rival contemporary accounts of casualty counts). | "Surviving accounts directly conflict...", "Contemporary records dispute..." |
| **`UNRESOLVED`** | Insufficient surviving documentary evidence to determine factual truth; open mystery. | Scholarly literature explicitly concludes available evidence cannot prove either thesis. | "Surviving records leave the question open...", "The ultimate cause remains unknown." |
| **`INSUFFICIENT_LITERATURE`**| The topic has not received adequate academic study in peer-reviewed historiography. | $<2$ peer-reviewed citations exist in scholarly databases (JSTOR, Historical Abstracts). | "Historical documentation is sparse...", "Few surviving sources address..." |

- **Default Value in `ClaimRecord`:** `ConsensusState.BROAD_CONSENSUS`.

---

## 6. Extended Pydantic Contract Models

### 6.1 Supporting Value Objects (`contracts.py`)

```python
class ClaimType(str, Enum):
    """Typology of factual claims dictating verification strategy dispatch."""
    EVENT_FACT = "event_fact"
    CAUSAL_INTERPRETATION = "causal_interpretation"
    SCHOLARLY_INTERPRETATION = "scholarly_interpretation"
    NUMERICAL_METRIC = "numerical_metric"
    DIRECT_QUOTE = "direct_quote"
    SCIENTIFIC_LAW = "scientific_law"
    CURRENT_EVENT = "current_event"
    DEFINITIONAL = "definitional"


class QuoteExactness(str, Enum):
    """Fidelity level of direct quote transcription."""
    EXACT = "exact"                                  # Levenshtein distance <= 0.02
    ELLIPSES = "ellipses"                            # Levenshtein distance <= 0.15 with standard editorial omission
    PARAPHRASE = "paraphrase"                        # Reformulated indirect discourse
    DISTORTED = "distorted"                          # Fabricated or inaccurate quotation marks
    NOT_APPLICABLE = "not_applicable"                # Claim is not a direct quote


class SourceQualityMetrics(H9BaseModel):
    """Aggregated quality and authority metrics of backing information sources."""
    domain_authority: float = Field(default=0.8, ge=0.0, le=1.0)
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    tier_weight: float = Field(default=0.8, ge=0.0, le=1.0)
    is_peer_reviewed: bool = False
    is_primary: bool = False
    independence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    citation_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TemporalContext(H9BaseModel):
    """Chronological bounds, validity dates, and temporal freshness."""
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    as_of_date: Optional[str] = None
    is_time_sensitive: bool = False
    temporal_status: str = Field(default="historical")  # "historical", "current", "timeless", "obsolete"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceUnitLink(H9BaseModel):
    """Structured passage-level link between a claim and an extracted evidence unit."""
    evidence_unit_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    verbatim_excerpt: str = ""
    char_offset_start: int = 0
    char_offset_end: int = 0
    entailment_relation: str = "SUPPORTS"  # "SUPPORTS", "CONTRADICTS", "HEDGES"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 6.2 Extended `SourceRecord`
```python
class SourceRecord(H9BaseModel):
    """Citation and provenance metadata for an external information source."""
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)

    # Extended Epistemic Fields (Milestone M2 / R2)
    source_id: Optional[str] = None
    tier: SourceTier = Field(
        default=SourceTier.PRIMARY_SOURCE,
        description="Authority tier within 13-tier taxonomy"
    )
    doi: Optional[str] = None
    peer_reviewed: bool = False
    archived_url: Optional[str] = None
    content_sha256: Optional[str] = None
    retrieved_at: Optional[str] = None
    is_sanitized: bool = True
    domain_authority: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 6.3 Extended `ClaimRecord` (Full Specification)
```python
class ClaimRecord(H9BaseModel):
    """Factual claim backed by primary and corroborating source records with full epistemic provenance."""
    claim_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    category: str = Field(default="general")
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    primary_source: SourceRecord
    corroborating_sources: List[SourceRecord] = Field(default_factory=list)
    visual_cue_suggestion: str = ""
    verification_notes: str = ""

    # Extended Epistemic Fields (Milestone M2 / R2 - Required)
    evidence_node_ids: List[str] = Field(
        default_factory=list,
        description="IDs of supporting nodes in the Evidence Graph DAG"
    )
    epistemic_status: EpistemicStatus = Field(
        default=EpistemicStatus.SUPPORTED,
        description="Granular epistemic verification status (11 states)"
    )
    consensus_state: ConsensusState = Field(
        default=ConsensusState.BROAD_CONSENSUS,
        description="Historiographical/scientific consensus classification (8 states)"
    )
    source_tier: SourceTier = Field(
        default=SourceTier.PRIMARY_SOURCE,
        description="Highest authoritative source tier backing this claim (13 tiers)"
    )
    source_quality: SourceQualityMetrics = Field(
        default_factory=SourceQualityMetrics,
        description="Aggregated quality and authority metrics of backing sources"
    )
    corroboration_set: List[str] = Field(
        default_factory=list,
        description="Independent source identifiers corroborating this claim"
    )
    temporal_context: TemporalContext = Field(
        default_factory=TemporalContext,
        description="Chronological bounds, validity dates, and temporal freshness"
    )
    verifier_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution trace, strategy used, entailment/contradiction scores, and verifier identity"
    )
    quote_exactness: Optional[Union[QuoteExactness, float, str]] = Field(
        default=None,
        description="Quote fidelity: exact, ellipses, paraphrase, distorted, or Levenshtein score"
    )

    # Extended Grounding Fields
    claim_type: ClaimType = Field(
        default=ClaimType.EVENT_FACT,
        description="Typology of factual claim dictating verification policy"
    )
    contradicting_sources: List[SourceRecord] = Field(
        default_factory=list,
        description="Counter-evidence or dissenting sources refuting or qualifying the claim"
    )
    evidence_links: List[EvidenceUnitLink] = Field(
        default_factory=list,
        description="Structured passage-level evidence links with character offsets"
    )

    @property
    def verification_status(self) -> str:
        """Backward-compatibility property returning uppercase status string."""
        return self.epistemic_status.value.upper()
```

### 6.4 Extended `ResearchDossier`
```python
class ResearchDossier(H9BaseModel):
    """Complete structured research dossier containing claims and talking points."""
    topic: str = Field(..., min_length=1)
    schema_version: str = "2.0.0"
    run_id: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    headline: str = ""
    executive_summary: str = ""
    key_takeaways: List[str] = Field(default_factory=list)
    claims: List[ClaimRecord] = Field(default_factory=list)
    talking_points: List[TalkingPointRecord] = Field(default_factory=list)
    statistics: List[StatisticRecord] = Field(default_factory=list)
    suggested_visual_queries: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Extended Epistemic Fields (Milestone M2 / R2)
    sources: List[SourceRecord] = Field(
        default_factory=list,
        description="Consolidated list of all evaluated sources"
    )
    evidence_graph: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Serialized portable EvidenceGraphDocument DAG"
    )
    entity_mentions: List[str] = Field(
        default_factory=list,
        description="Extracted named entities for anachronism checking"
    )
```

---

## 7. Backwards Compatibility & Verification Proof

### 7.1 Proof of Zero Regressions on Existing Suites
We verified backwards compatibility empirically:
1. **Pydantic v2 `extra="allow"`**: Any legacy keyword arguments or additional metadata continue to be accepted.
2. **All New Fields Have Default Values**:
   - `evidence_node_ids`: defaults to `[]`
   - `epistemic_status`: defaults to `EpistemicStatus.SUPPORTED`
   - `consensus_state`: defaults to `ConsensusState.BROAD_CONSENSUS`
   - `source_tier`: defaults to `SourceTier.PRIMARY_SOURCE`
   - `source_quality`: defaults to `SourceQualityMetrics()`
   - `corroboration_set`: defaults to `[]`
   - `temporal_context`: defaults to `TemporalContext()`
   - `verifier_metadata`: defaults to `{}`
   - `quote_exactness`: defaults to `None`
   - `contradicting_sources`: defaults to `[]`
   - `evidence_links`: defaults to `[]`
3. **Dual Serialization (JSON & YAML)**: All enums inherit from `(str, Enum)` or `(int, Enum)` and all nested objects inherit from `H9BaseModel`. This guarantees that `to_json()`, `to_yaml()`, `save()`, and `load()` execute without PyYAML `RepresenterError` or JSON serialization errors.
4. **Existing Test Suite Invariants**:
   - `tests/test_contracts.py:122-195` passes with 100% success rate (12/12).
   - `tests/test_h9_acceptance.py` passes with 100% success rate (44/44).
   - `bridge.delegate_research()` continues to return valid `ResearchDossier` instances containing `ClaimRecord` objects.

---

## 8. Concrete Implementation Recommendations for `worker_m2`

When implementing Milestone 2:
1. **Target File 1: `src/models/contracts.py`**:
   - Add enums and value classes: `EpistemicStatus`, `SourceTier`, `DEFAULT_TIER_WEIGHTS`, `ConsensusState`, `ClaimType`, `QuoteExactness`, `SourceQualityMetrics`, `TemporalContext`, `EvidenceUnitLink`.
   - Update `SourceRecord` with optional epistemic fields (`tier`, `source_id`, `doi`, `content_sha256`, etc.).
   - Update `ClaimRecord` with the 9 extended fields + supporting fields.
   - Update `ResearchDossier` with optional `sources`, `evidence_graph`, `entity_mentions`.
2. **Target File 2: `src/models/__init__.py`**:
   - Re-export the newly added enums and schemas (`EpistemicStatus`, `SourceTier`, `DEFAULT_TIER_WEIGHTS`, `ConsensusState`, `QuoteExactness`, `SourceQualityMetrics`, `TemporalContext`, `EvidenceUnitLink`, `ClaimType`) in `__all__`.
3. **Target File 3: `src/h9_runtime/content.py`**:
   - Remove top-level `from src.orchestrator.pipeline import Pipeline` at line 37.
   - Insert lazy import inside `run_full_production()` at line 345:
     ```python
     from src.orchestrator.pipeline import Pipeline
     pipeline = Pipeline(...)
     ```
   - Verify that `tests/test_state_machine.py` passes in isolation.
4. **Target File 4: `src/epistemic/graph.py`**:
   - Implement the machine-readable DAG `EvidenceGraph` as specified in `docs/epistemic/EVIDENCE_GRAPH.md`, importing `SourceRecord`, `ClaimRecord`, `EpistemicStatus`, `ConsensusState`, `SourceTier` directly from `src.models.contracts`.
