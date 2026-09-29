# Historical Scholarship Policy & Historiographical Governance: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/epistemic/`, `src/scriptwriting/`, `src/editorial/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/epistemic/FACT_CHECKING_SPEC.md`  

---

## 1. Executive Summary & Historiographical Philosophy

The **Harness 9 Historical Scholarship Policy** establishes mandatory rules governing how historical events, causal arguments, timelines, and scholarly debates are researched, validated, and narrated in Harness 9 video productions.

Historical inquiry differs fundamentally from empirical laboratory sciences or contemporary news reporting. Historical facts are rarely observed directly; they are reconstructed from surviving primary documentary records, material artifacts, and critical historiographical consensus. Popular digital media (blogs, YouTube video scripts, crowdsourced wikis) frequently propagate apocryphal legends, flatten complex multi-causal debates into monocausal caricatures, and average divergent archival estimates into meaningless numbers.

To prevent Harness 9 productions from publishing misleading, ungrounded, or historically illiterate content, this policy enforces six inviolable rules:
1. **The Forbidden Sole Source Rule**: No historical fact or interpretation may be established by a single web summary, blog, or crowdsourced encyclopedia.
2. **Mandatory Minimum Evidentiary Thresholds**: Historical claims must be anchored in primary archival editions or peer-reviewed academic press scholarship.
3. **The 8-State Consensus Model**: All historical claims must be classified into one of eight formal consensus states.
4. **The Event vs. Interpretation Distinction**: The system must rigorously separate documented physical occurrences from historiographical causal hypotheses.
5. **The Non-Averaging Contradiction Invariant**: Divergent casualty counts, economic estimates, and dates must never be averaged away; contradictions must be preserved and narrated as disputed.
6. **Calibrated Narration Framing**: Voiceover scripts must calibrate their rhetorical stance to the verified consensus state, avoiding unearned dogmatic certainty.

---

## 2. Inviolable Historiographical Rules

### Rule 1: Prohibition of Sole Web Sources
- **Strict Prohibition**: Content from general web encyclopedias (Tier 9/10, including Wikipedia), commercial blogs (Tier 11), popular media videos, or social forums (Tier 12/13) is **strictly forbidden from serving as the sole establishing source** for any historical fact or interpretation.
- **Permitted Role of Web Summaries**: General encyclopedic sources may be used solely for initial query expansion, entity discovery, and index lookup. They must be cross-referenced against primary documents or peer-reviewed secondary literature before a claim can be verified.
- **Enforcement Mechanism**: If a historical claim (`ClaimType.EVENT_FACT` or `ClaimType.SCHOLARLY_INTERPRETATION`) has only Tier 9–13 sources, the verification engine raises `POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE` and assigns status `UNSUPPORTED`.

### Rule 2: Minimum Evidentiary Thresholds
To achieve status `SUPPORTED` or `VERIFIED`, historical claims must satisfy one of the following minimum thresholds:
1. **Threshold A (Primary Backing)**: At least one verified Tier 1 (`PRIMARY_SOURCE`: archival state papers, treaties, contemporary lab journals, archaeological reports) or Tier 4 (`HISTORICAL_DOCUMENT_CRITICAL_EDITION`).
2. **Threshold B (Academic Monograph Backing)**: At least one verified Tier 3 source (`ACADEMIC_PRESS_BOOK`: Oxford University Press, Cambridge University Press, Harvard University Press, MIT Press, etc.).
3. **Threshold C (Peer-Reviewed Historiography)**: At least two independent Tier 2 sources (`PEER_REVIEWED_JOURNAL`: *The American Historical Review*, *Past & Present*, *Journal of Modern History*, etc.).

---

## 3. The 8-State Consensus Model (`ConsensusState`)

Historical assertions must not be reduced to binary truth values. Instead, the engine classifies every historical claim into one of eight distinct consensus states:

```python
class ConsensusState(str, Enum):
    STRONG_CONSENSUS = "STRONG_CONSENSUS"
    BROAD_CONSENSUS = "BROAD_CONSENSUS"
    MAJORITY_INTERPRETATION = "MAJORITY_INTERPRETATION"
    MINORITY_INTERPRETATION = "MINORITY_INTERPRETATION"
    ACTIVE_DEBATE = "ACTIVE_DEBATE"
    CONTESTED = "CONTESTED"
    UNRESOLVED = "UNRESOLVED"
    INSUFFICIENT_LITERATURE = "INSUFFICIENT_LITERATURE"
```

### Consensus State Definitions and Classification Criteria

```
                              SCHOLARLY LITERATURE
                                       │
                      [Are primary/secondary sources unanimous?]
                                       │
                    ┌──────────────────┴──────────────────┐
                   YES                                    NO
                    │                                     │
        [Is dissent negligible?]              [Is there an established majority?]
            ┌───────┴───────┐                     ┌───────┴───────┐
           YES              NO                   YES              NO
            │               │                     │               │
     STRONG_CONSENSUS  BROAD_CONSENSUS     MAJORITY_INTERP   [Is there active debate?]
                                                  │               ┌───────┴───────┐
                                           MINORITY_INTERP       YES              NO
                                                                  │               │
                                                            ACTIVE_DEBATE    [Is evidence contradictory?]
                                                                                  ┌───────┴───────┐
                                                                                 YES              NO
                                                                                  │               │
                                                                              CONTESTED      UNRESOLVED /
                                                                                            INSUFFICIENT
```

| Consensus State | Operational Definition | Evidentiary Requirement | Script Tone |
|---|---|---|---|
| **`STRONG_CONSENSUS`** | Unanimous agreement across all modern scholarly literature; established historical baseline. | Zero peer-reviewed dissent in the last 50 years; substantiated by multiple independent primary records. | Definitive, declarative assertion. |
| **`BROAD_CONSENSUS`** | Overwhelming consensus among specialists; negligible fringe dissent. | $>90\%$ of academic monographs agree; minor dissenting arguments lack mainstream peer-reviewed support. | "Historians broadly agree...", "Scholarly consensus indicates..." |
| **`MAJORITY_INTERPRETATION`**| Dominant academic paradigm, but recognized alternative scholarly schools exist. | Supported by leading university presses, but recognized peer-reviewed counter-hypotheses exist. | "The leading historical view holds...", "While debated, evidence points to..." |
| **`MINORITY_INTERPRETATION`**| Credible, peer-reviewed academic thesis held by a qualified minority of historians. | Published in peer-reviewed academic journals or university press monographs; challenges the majority paradigm. | "A significant school of historians argues...", "Alternatively, scholars like X propose..." |
| **`ACTIVE_DEBATE`** | Substantial, unresolved debate with mutually incompatible theories supported by prominent scholars. | Multiple competing peer-reviewed interpretations with neither holding decisive majority agreement. | "Historians remain deeply divided...", "Scholars continue to debate whether X or Y..." |
| **`CONTESTED`** | Mutually exclusive claims supported by contradictory primary accounts or contested physical evidence. | Surviving primary sources directly conflict (e.g. rival contemporary accounts of troop counts or battle sequence). | "Surviving accounts directly conflict...", "Contemporary records dispute..." |
| **`UNRESOLVED`** | Insufficient surviving documentary evidence to determine factual truth; open historical mystery. | Scholarly literature explicitly concludes that available evidence cannot prove either thesis. | "Surviving records leave the question open...", "The ultimate cause remains unknown." |
| **`INSUFFICIENT_LITERATURE`**| The specific topic or question has not received adequate academic study in peer-reviewed historiography. | $<2$ peer-reviewed citations exist in scholarly databases (JSTOR, Historical Abstracts, Google Scholar). | "Historical documentation is sparse...", "Few surviving sources address..." |

---

## 4. Event vs. Interpretation Distinction

Harness 9 enforces a fundamental architectural boundary between **Documented Events** and **Scholarly Interpretations**:

### 4.1 Documented Events (`ClaimType.EVENT_FACT`)
- **Definition**: An empirical occurrence in time and space attested by primary documentary records or physical archaeology (e.g. *"The Declaration of Independence was adopted by the Continental Congress on July 4, 1776"*).
- **Verification Criterion**: Requires primary source provenance and temporal consistency.
- **Narration Rule**: Stated affirmatively as an objective fact.

### 4.2 Scholarly & Causal Interpretations (`ClaimType.CAUSAL_INTERPRETATION`)
- **Definition**: An explanatory hypothesis or historiographical model explaining *why* an event occurred, the psychological motivations of actors, or long-term societal consequences (e.g. *"The collapse of the Roman economy in the 3rd century was precipitated by debasement of the denarius"*).
- **Verification Criterion**: Must be mapped to an explicit `ConsensusState` and attributed to historical scholarship.
- **Narration Rule**: **Must never be narrated as an uncontested empirical event.** Must be framed with appropriate epistemic humility and attribution to historical inquiry.

---

## 5. The Non-Averaging Contradiction Invariant

When historical sources provide contradictory quantitative data (e.g. troop strengths, plague mortality, economic inflation rates) or conflicting timelines, generative models frequently perform an "arithmetic average" or fabricate a smooth synthetic estimate.

### Mathematical Invalidation of Averaging
Let Source $A$ report casualty count $N_A = 20,000$, and Source $B$ report $N_B = 100,000$.
A synthetic average:
$$\overline{N} = \frac{N_A + N_B}{2} = 60,000$$
is **epistemically false**: no contemporary observer recorded 60,000 casualties, and no scholarly monograph justifies that number.

### Invariant Rule
$$\forall C_A, C_B \text{ such that } C_A.\text{value} \ne C_B.\text{value}, \quad \text{SynthesizeAverage}(C_A, C_B) \to \mathbf{PROHIBITED}$$

The verification engine must:
1. Preserve both records in the Evidence Graph connected by an opposing `CONTRADICTS` edge.
2. Set the claim's status to `CONTESTED`.
3. Force the script generator to narrate the discrepancy:
   *"Casualty figures remain heavily contested, ranging from 20,000 according to official communiqués to over 100,000 according to modern archival revisions."*

---

## 6. Calibrated Script Language Generation Rules

Scriptwriting models must strictly adhere to the rhetoric matrix corresponding to the verified consensus state:

| Consensus State | Mandated Narration Phrasing | Strictly Forbidden Phrasing |
|---|---|---|
| **`STRONG_CONSENSUS`** | Direct, affirmative assertions ("In December 1947, Bell Labs created..."). | Speculative doubt ("allegedly", "it is claimed that", "some believe"). |
| **`BROAD_CONSENSUS`** | "Historical evidence demonstrates...", "Scholarly consensus indicates..." | Absolute dogma without context; ignoring prominent context. |
| **`MAJORITY_INTERPRETATION`**| "The dominant historical view holds...", "Most evidence points to..." | Stating the majority interpretation as the *sole indisputable fact*. |
| **`MINORITY_INTERPRETATION`**| "An important scholarly counter-thesis argues...", "Some historians emphasize..." | Presenting minority scholarship as mainstream consensus or fringe myth. |
| **`ACTIVE_DEBATE`** | "Historians remain divided over whether X or Y...", "Debate centers on..." | Picking one side and presenting it as established truth. |
| **`CONTESTED`** | "Contemporary sources directly contradict each other...", "Estimates range from X to Y..." | Averaging numbers; selecting one primary account without acknowledging others. |
| **`UNRESOLVED`** | "The surviving records leave this question unanswered...", "Historical evidence is inconclusive." | Fabricating neat conclusions or synthetic certainty. |
| **`INSUFFICIENT_LITERATURE`**| "Due to limited surviving documentation...", "With scarce primary records..." | Citing popular blogs or speculation as authoritative history. |

---

## 7. Adversarial Defense Against Historical Myths

Popular historical myths frequently pass simple web-search verification because they are repeated across hundreds of websites (the "false consensus" attack).

### Myth Neutralization Protocol
1. **Taxonomy Demotion**: The system discounts blog, wiki, and content farm repetitions to weight zero.
2. **Historiographical Disconfirmation Check**: The engine cross-references claims against specialized historiographical myth registries (e.g. debunked historical claims catalog).
3. **Primary Anachronism Scanner**: Rejects claims asserting technologies, concepts, or terms that did not exist during the target era.

---

## 8. Implementation Interface (`HistoricalScholarshipPolicyEngine`)

```python
class HistoricalScholarshipPolicyEngine:
    """Evaluates historical claims and enforces historiographical scholarship rules."""

    def evaluate_claim(
        self,
        claim: ClaimRecord,
        sources: List[SourceRecord],
    ) -> HistoriographicalEvaluationReport:
        """Enforces the 6 historical scholarship rules on a candidate claim."""
        # 1. Enforce prohibition of sole web sources
        self._check_unqualified_sources(sources)

        # 2. Check minimum tier thresholds
        self._verify_source_tiers(sources, claim.claim_type)

        # 3. Classify consensus state
        consensus_state = self._classify_consensus_state(claim, sources)

        # 4. Check event vs interpretation
        self._validate_interpretation_framing(claim, consensus_state)

        # 5. Enforce non-averaging on conflicting metrics
        self._enforce_non_averaging(claim, sources)

        return HistoriographicalEvaluationReport(
            claim_id=claim.claim_id,
            consensus_state=consensus_state,
            eligible_for_narration=True,
            mandated_framing=self._get_mandated_framing(consensus_state),
        )
```
