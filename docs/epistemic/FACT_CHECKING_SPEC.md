# Fact-Checking Specification & Verification Pipelines: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/epistemic/`, `src/models/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md`  

---

## 1. Executive Summary & Purpose

The **Harness 9 Fact-Checking Specification** defines the taxonomy of factual claims, the 11 discrete epistemic verification states, the mathematical formulations for verification scoring, and the execution pipelines across pre-script research, post-script narration auditing, and visual fact-checking.

In media production workflows, factual claims vary drastically in structure and verification requirements. An astronomical measurement requires mathematical dimensional analysis; a direct quote requires character-level Levenshtein matching against primary transcripts; a historical causal claim requires historiographical consensus analysis; and a scientific mechanism requires peer-reviewed corroboration. 

This specification establishes deterministic, explainable verification rules tailored to each claim type, replacing vague confidence heuristics with rigorous mathematical criteria.

---

## 2. Typology of Factual Claims (`ClaimType`)

Every proposition extracted from research notes, scripts, or on-screen graphics is typed into one of 8 structural categories:

```python
class ClaimType(str, Enum):
    EVENT_FACT = "event_fact"                            # Empirical historical or physical event with date/location
    CAUSAL_INTERPRETATION = "causal_interpretation"      # Explanatory theory for why an event occurred
    SCHOLARLY_INTERPRETATION = "scholarly_interpretation"# Historiographical paradigm or academic hypothesis
    NUMERICAL_METRIC = "numerical_metric"                # Quantitative measurement, count, percentage, dimension
    DIRECT_QUOTE = "direct_quote"                        # Verbatim statement attributed to a specific entity
    SCIENTIFIC_LAW = "scientific_law"                    # Validated physical, biological, or mathematical rule
    CURRENT_EVENT = "current_event"                      # Contemporary news occurrence
    DEFINITIONAL = "definitional"                        # Semantic definition or terminology explanation
```

### Claim Type Verification Profile Matrix

| `ClaimType` | Primary Evidentiary Anchor | Mandatory Strategy | Disallowed Sources | Failure Verdict |
|---|---|---|---|---|
| `EVENT_FACT` | Primary archive / Official Gazette | `SOURCE_ENTAILMENT`, `TEMPORAL_CHECK` | Unverified web, forum posts | `BLOCK` |
| `CAUSAL_INTERPRETATION` | Scholarly monographs, peer-reviewed journals | `HISTORIOGRAPHICAL_CHECK` | Commercial blogs, pop summaries | `HUMAN_REVIEW` / Calibrate |
| `SCHOLARLY_INTERPRETATION`| Academic historiography | `HISTORIOGRAPHICAL_CHECK`, `CONTRADICTION_CHECK`| Popular media, crowdsourced wikis | `HUMAN_REVIEW` / Calibrate |
| `NUMERICAL_METRIC` | Official statistical dataset | `NUMERICAL_CHECK`, `SOURCE_ENTAILMENT` | Secondary blogs without raw data | `BLOCK` |
| `DIRECT_QUOTE` | Primary document edition / Recording | `QUOTE_CHECK` | Secondary popular retellings | `BLOCK` (force paraphrase) |
| `SCIENTIFIC_LAW` | Peer-reviewed journal / Standard text | `SOURCE_ENTAILMENT`, `CROSS_CORROBORATION` | Preprints, sensational science news | `BLOCK` |
| `CURRENT_EVENT` | Reputable investigative news agencies | `SOURCE_ENTAILMENT`, `TEMPORAL_CHECK` | Social media rumors, unvetted blogs | `WARN` / `BLOCK` |
| `DEFINITIONAL` | Standard encyclopedia, authoritative lexicon | `SOURCE_ENTAILMENT` | Urban/slang forums (unless linguistic) | `WARN` |

---

## 3. The 11 Granular Epistemic Statuses (`EpistemicStatus`)

A continuous float score cannot distinguish between an assertion supported by a single source, an assertion subject to active academic debate, an assertion that is factually refuted, and a subjective opinion. Harness 9 defines 11 mutually exclusive epistemic states:

```python
class EpistemicStatus(str, Enum):
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

### Status Definitions and Lifecycle Semantics

| Epistemic Status | Operational Definition | Evidentiary Requirement | Pipeline Action |
|---|---|---|---|
| **`VERIFIED`** | Indisputably confirmed by multiple independent, authoritative high-tier sources. | $\ge 2$ independent Tier 1–3 sources with $P(\text{Entailment}) \ge 0.95$ and zero contradictions. | Allowed unconditionally in all stages. |
| **`SUPPORTED`** | Entailed by at least one reliable source without existing counter-evidence. | $\ge 1$ Tier 1–7 source with $P(\text{Entailment}) \ge 0.90$. | Allowed; secondary corroboration advised. |
| **`PARTIALLY_SUPPORTED`** | Core factual premise is entailed, but specific numbers, dates, or details diverge. | $P(\text{Entailment}) \ge 0.70$; minor discrepancy logged. | `WARN`; flags divergence for creator review. |
| **`CONTESTED`** | Legitimate scholarly, factual, or empirical debate exists between credible sources. | Conflicting evidence from Tier 1–7 sources; consensus state is `ACTIVE_DEBATE` or `CONTESTED`. | Requires calibrated narration or `HUMAN_REVIEW`. |
| **`CONTRADICTED`** | Refuted by authoritative counter-evidence or primary records. | Counter-source with $P(\text{Contradiction}) \ge 0.85$ and higher source tier. | Mandatory `BLOCK`; script synthesis blocked. |
| **`UNSUPPORTED`** | No cited evidence passage logically entails the asserted claim. | No valid incoming `SUPPORTS` edge from an evidence node. | Mandatory `BLOCK`; claim must be excised. |
| **`UNVERIFIABLE`** | Proposition cannot be empirically, archival, or scientifically tested. | Assertion lacks falsifiable empirical criteria. | Reject as factual claim; reclassify as opinion. |
| **`OUTDATED`** | Historically accurate when asserted, but superseded by newer empirical data or discoveries. | Temporal check reveals newer authoritative data disproving earlier baseline. | `BLOCK` unless framed with explicit temporal anchor. |
| **`MISLEADING`** | Technically accurate in isolation, but omitted context creates a false implication. | Logical omission analysis flags contextual deceit. | `BLOCK` or mandate contextual clarification. |
| **`OPINION`** | Subjective, aesthetic, or evaluative judgment, not an empirical assertion. | Linguistic inspection flags value judgments ("greatest", "beautiful"). | Excluded from factual gates; permitted as commentary. |
| **`PREDICTION`** | Forward-looking forecast regarding future occurrences. | Event date $T > T_{\text{current}}$. | Must be framed as speculative projection. |

---

## 4. Mathematical Formulation of Epistemic Scoring

The epistemic evaluation of a claim $C$ against an evidence graph $G = (V, E)$ is governed by three deterministic metrics: Entailment Score, Corroboration Index, and Contradiction Penalty.

### 4.1 Entailment Score ($S_{\text{entail}}$)
Given a set of retrieved passage nodes $\{P_1, P_2, \dots, P_n\}$ linked to $C$:

$$S_{\text{entail}}(C) = \max_{P_i \in \text{Passages}} \left[ W_{\text{tier}}(P_i) \times P(P_i \models C) \right]$$

Where:
- $P(P_i \models C) \in [0.0, 1.0]$: Probability of textual entailment computed by the NLI engine.
- $W_{\text{tier}}(P_i) \in [0.0, 1.0]$: Source tier authority weight derived from the 13-Tier Taxonomy:
  $$W_{\text{tier}} = \begin{cases} 
  1.00 & \text{Tier 1 (PRIMARY\_SOURCE)} \\
  0.98 & \text{Tier 2 (PEER\_REVIEWED\_JOURNAL)} \\
  0.95 & \text{Tier 3 (ACADEMIC\_PRESS\_BOOK)} \\
  0.92 & \text{Tier 5 (GOVERNMENT\_RECORD)} \\
  0.80 & \text{Tier 8 (REPUTABLE\_NEWS)} \\
  0.20 & \text{Tier 12 (SOCIAL\_MEDIA)} \\
  0.00 & \text{Tier 13 (UNVERIFIED)}
  \end{cases}$$

### 4.2 Corroboration Index ($S_{\text{corrob}}$)
Corroboration evaluates independent source nodes that entail $C$, discounting syndicated or circular citations:

$$S_{\text{corrob}}(C) = 1.0 - \prod_{k=1}^{m} \left( 1.0 - W_{\text{tier}}(S_k) \times I_{\text{indep}}(S_k, S_{\text{primary}}) \right)$$

Where:
- $I_{\text{indep}}(S_k, S_{\text{primary}}) \in [0.0, 1.0]$: Independence coefficient between source $S_k$ and the primary source. If $S_k$ is syndicated from $S_{\text{primary}}$ (e.g. shared wire feed, identical author, identical publisher), $I_{\text{indep}} = 0.0$.

### 4.3 Contradiction Penalty ($P_{\text{contra}}$)
Evaluates whether any authoritative passage $P_j$ refutes $C$:

$$P_{\text{contra}}(C) = \max_{P_j \in \text{Passages}} \left[ W_{\text{tier}}(P_j) \times P(P_j \models \neg C) \right]$$

### 4.4 Status Decision Function
$$\text{Status}(C) = \begin{cases}
\text{CONTRADICTED} & \text{if } P_{\text{contra}}(C) \ge 0.80 \land P_{\text{contra}}(C) > S_{\text{entail}}(C) \\
\text{CONTESTED} & \text{if } P_{\text{contra}}(C) \ge 0.60 \land S_{\text{entail}}(C) \ge 0.60 \\
\text{VERIFIED} & \text{if } S_{\text{entail}}(C) \ge 0.90 \land S_{\text{corrob}}(C) \ge 0.85 \land P_{\text{contra}}(C) < 0.20 \\
\text{SUPPORTED} & \text{if } S_{\text{entail}}(C) \ge 0.80 \land P_{\text{contra}}(C) < 0.30 \\
\text{PARTIALLY\_SUPPORTED} & \text{if } 0.60 \le S_{\text{entail}}(C) < 0.80 \land P_{\text{contra}}(C) < 0.30 \\
\text{UNSUPPORTED} & \text{otherwise}
\end{cases}$$

---

## 5. End-to-End Verification Pipelines

```
[ Research Sources ]
         │
         ▼
[ Pipeline 1: Pre-Script Research Verification ]
  • Extracts atomic propositions from research dossier
  • Builds initial Evidence Graph DAG
  • Filters by 13-Tier Source Taxonomy
  • Evaluates initial EpistemicStatus
         │
         ▼
[ Editorial & Script Synthesis Engine ]
         │
         ▼
[ Pipeline 2: Post-Script Narration Claim Re-Extraction & Verification ]
  • Extracts script claims C_script from narration text
  • Performs bipartite alignment C_script ↔ C_dossier
  • Detects strengthening, number changes, quote falsification
         │
         ▼
[ Pipeline 3: Visual & On-Screen Fact-Checking ]
  • Inspects Production IR visual blocks (StatisticReveal, Timeline, Quote)
  • Reconciles on-screen parameters against voiceover narration
  • Validates chart parameters against NumericalDataset
         │
         ▼
[ Pipeline 4: Cross-Source Contradiction Resolution ]
  • Graph traversal for mutually exclusive assertions
  • Preserves conflicting edges; forbids arithmetic averaging
  • Classifies ConsensusState (STRONG_CONSENSUS ... UNRESOLVED)
```

### 5.1 Pipeline 1: Pre-Script Research Claim Verification
1. **Proposition Extraction**: Ingests raw research notes, splitting text into atomic propositions containing exactly one subject-predicate assertion.
2. **Taxonomy Gating**: Sources in Tier 11–13 are marked ineligible for establishing historical or scientific claims.
3. **Graph Ingestion**: Inserts `SourceNode`, `PassageNode`, and `EvidenceUnitNode` into the `EvidenceGraph`.
4. **NLI Verification**: Runs `SOURCE_ENTAILMENT` to establish baseline `EpistemicStatus`.

### 5.2 Pipeline 2: Post-Script Narration Claim Re-Extraction & Auditing
1. **Sentence Decomposition**: Parses generated voiceover text into discrete sentences.
2. **Script Claim Extraction**: Deconstructs each sentence into one or more candidate assertions ($C_{\text{script}}$).
3. **Bipartite Graph Alignment**: Computes cosine similarity between $C_{\text{script}}$ and all $C_{\text{dossier}}$ nodes in the Evidence Graph:
   $$\text{Sim}(C_{\text{script}}, C_{\text{dossier}}) = \cos(\mathbf{e}_{\text{script}}, \mathbf{e}_{\text{dossier}})$$
4. **Drift Detection**:
   - **Strengthening**: Flagged if $C_{\text{dossier}}$ has epistemic qualifier ("preliminary", "suggests") but $C_{\text{script}}$ uses absolute phrasing ("proven", "definitely").
   - **Numerical Mutation**: Flagged if $|V_{\text{script}} - V_{\text{dossier}}| / V_{\text{dossier}} > \text{Tolerance}$.
   - **Quote Fabrication**: Flagged if quotation marks enclose text with normalized Levenshtein distance $> 0.02$ from primary text.

### 5.3 Pipeline 3: Visual & On-Screen Fact-Checking
1. **Block Property Extraction**: Inspects compiled `IRVisualBlockNode` parameters:
   - `STATISTIC_REVEAL`: extracts `stat_number`, `stat_label`, `unit`.
   - `TIMELINE_REVEAL`: extracts `year`, `date`, `event_label`.
   - `QUOTE_HIGHLIGHT`: extracts `quote_text`, `speaker`, `source`.
2. **Audio-Visual Cross-Check**: Compares extracted parameters against the concurrent `ScriptBeat.text`. If the spoken beat narrates a different number, date, or author, a `VISUAL_AUDIO_MISMATCH` is raised.
3. **Dataset Lineage Validation**: Verifies that any visual chart binds to a validated `NumericalDataset`.

### 5.4 Pipeline 4: Cross-Source Contradiction Resolution
1. **Conflict Search**: Searches for pairs $(C_A, C_B)$ where $C_A \land C_B \models \bot$.
2. **Non-Averaging Enforcement**: If $C_A$ asserts 10,000 casualties and $C_B$ asserts 50,000 casualties, the pipeline binds both to an `OpposingAssertionRecord`. It sets `ConsensusState = CONTESTED` and mandates that narration report the range or dispute.

---

## 6. Verification Result Schema (`VerificationResult`)

```python
class VerificationResult(H9BaseModel):
    """Execution output from the Epistemic Verification Engine."""
    claim_id: str
    status: EpistemicStatus
    claim_type: ClaimType
    confidence: float = Field(ge=0.0, le=1.0)
    entailment_score: float = Field(ge=0.0, le=1.0)
    corroboration_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    highest_source_tier: SourceTier
    consensus_state: Optional[ConsensusState] = None
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    explanation: str
    verified_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
```

---

## 7. Failure Handling & Gate Remediations

| Failure Condition | Detected By | Default Action | Automated Remediation |
|---|---|---|---|
| Contradicted claim in research | Pipeline 1 | `BLOCK` | Discard claim from dossier; re-query research engine for counter-evidence. |
| Single web source establishing historical fact | Pipeline 1 | `BLOCK` | Flag as unqualified source; dispatch query to academic press/primary archive APIs. |
| Strengthened assertion in script | Pipeline 2 | `WARN` / `BLOCK` | Inject hedging prompt into scriptwriter to restore original epistemic qualifiers. |
| Fabricated direct quote in script | Pipeline 2 | `BLOCK` | Strip quotation marks; convert to attributed paraphrase. |
| Visual-narration number mismatch | Pipeline 3 | `BLOCK` | Synchronize visual block parameters to match spoken beat text and dataset record. |
| Visual chart lacks dataset lineage | Pipeline 3 | `BLOCK` | Synthesize or bind verified `NumericalDataset` before visual rendering. |
| Contradiction averaged away | Pipeline 4 | `BLOCK` | Replace synthetic average with explicit contested range narration. |
