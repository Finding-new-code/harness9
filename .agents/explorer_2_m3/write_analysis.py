from pathlib import Path

content = """# Historical Scholarship Policy & Historiographical Governance Investigation

**Milestone:** Milestone 3 (R3) - Epistemic Verification Layer  
**Component:** `src/epistemic/historical_policy.py` (`HistoricalPolicyChecker`)  
**Investigator:** `explorer_2_m3`  
**Date:** 2026-09-14  
**Status:** Investigation Complete & Canonically Specified  

---

## 1. Executive Summary & Problem Scope

Historical scholarship possesses fundamentally distinct epistemic characteristics from physical laboratory sciences or contemporary news reporting:
- Empirical science deals with reproducible experimental observations and mathematical laws.
- Contemporary journalism deals with living witnesses, official announcements, and real-time sensor/video records.
- Historical scholarship deals with incomplete, surviving primary documentary records, material archaeology, and historiographical debates reconstructed across centuries.

Autonomous AI media generation pipelines suffer from catastrophic historical failures when relying on generic search retrieval or unconstrained LLM synthesis:
1. **Popular Myth Propagation (The False Consensus Defect)**: LLMs routinely cite popular web summaries, commercial blogs, or crowdsourced wikis that repeat apocryphal legends (e.g. "Vikings wore horned helmets", "Nero fiddled while Rome burned", "Galileo dropped balls from the Leaning Tower of Pisa") because they appear on millions of websites, confusing web repetition with scholarly consensus.
2. **Historiographical Flattening**: Complex, multi-causal historical transformations (such as the fall of the Western Roman Empire or the origins of the First World War) are flattened into dogmatic, monocausal soundbites, presenting one historian's speculative hypothesis as an indisputable empirical fact.
3. **Synthetic Numerical Averaging**: When divergent primary accounts or rival archival studies report contradictory casualty counts, troop sizes, or dates (e.g. 20,000 vs 100,000 casualties), LLMs synthesize a mathematical average (e.g. 60,000), fabricating an ungrounded number that no contemporary recorded and no scholarly monograph supports.
4. **Dogmatic False Certainty**: Narrations use unearned absolute phrasing ("it is undisputed that", "definitely caused by") for issues that remain subject to vigorous scholarly dispute.

To resolve these defects in Harness 9 productions, **Milestone 3 (R3)** mandates a dedicated, hard Historical Scholarship Policy implemented in `src/epistemic/historical_policy.py` via `HistoricalPolicyChecker` (and alias `HistoricalScholarshipPolicyEngine`). This specification provides the complete analytical foundation and algorithmic blueprints.

---

## 2. Forbidden Sole Sources & Minimum Evidentiary Tiers

### 2.1 The Prohibition of Sole Web Sources
Under the 13-tier source taxonomy established in `src/models/contracts.py`:
- **Tier 1**: `PRIMARY_SOURCE` (1.00) — Archival records, treaties, official gazettes, contemporary lab logs, inscriptions.
- **Tier 2**: `PEER_REVIEWED_JOURNAL` (0.98) — Refereed historical journals (*American Historical Review*, *Past & Present*, *Journal of Modern History*).
- **Tier 3**: `ACADEMIC_BOOK` / `ACADEMIC_PRESS_BOOK` (0.95) — University press monographs (Oxford, Cambridge, Harvard, Princeton, Chicago, MIT Press).
- **Tier 4**: `SCHOLARLY_CONFERENCE` / `HISTORICAL_DOCUMENT_CRITICAL_EDITION` (0.90 / 0.92) — Critical scholarly editions, published archaeological proceedings.
- **Tier 5**: `INSTITUTIONAL_REPORT` / `GOVERNMENT_RECORD_STATISTICAL_AGENCY` (0.88) — Official census, parliamentary acts, judicial registries.
- **Tier 6**: `ARCHIVAL_DOCUMENT` (0.92) — Preserved historical collections, diplomatic cables, estate records, wills.
- **Tier 7**: `REFERENCE_WORK` / `SPECIALIZED_SCHOLARLY_DATABASE` (0.80) — Authoritative academic encyclopedias, Oxford Classical Dictionary, Pauly-Wissowa.
- **Tier 8**: `EXPERT_ANALYSIS` (0.75) — Published essays by credentialed historians in recognized cultural/academic reviews.
- **Tier 9**: `REPUTABLE_JOURNALISM` (0.70) — Investigative reporting by major international news agencies (BBC, Reuters, NYT, AP).
- **Tier 10**: `TRADE_PUBLICATION` (0.55) — Trade or industry magazines, commercial monographs.
- **Tier 11**: `POPULAR_MEDIA` (0.35) — Commercial popular science magazines, commercial history magazines, video essays, podcasts.
- **Tier 12**: `SELF_PUBLISHED` / `BLOG_OPINION_COMMENTARY` (0.20) — Substack newsletters, personal blogs, Medium posts, hobbyist forums.
- **Tier 13**: `UNVERIFIED` / `SOCIAL_MEDIA_FORUM` (0.00) — Reddit, Wikipedia/crowdsourced wikis, anonymous forums, tweet threads.

#### The Hard Inviolable Rule
**Strict Prohibition**: Content from general web encyclopedias (Tier 9/10, including Wikipedia), commercial blogs (Tier 11/12), popular media videos, or social forums (Tier 12/13) is **strictly forbidden from serving as the sole establishing source** for any historical fact (`ClaimType.EVENT_FACT`) or interpretation (`ClaimType.CAUSAL_INTERPRETATION` or `ClaimType.SCHOLARLY_INTERPRETATION`).

#### Permitted Role of Web Summaries
General encyclopedic sources (such as Wikipedia or general web overviews) may be utilized **exclusively for initial discovery**:
- Identifying key entities, dates, and historical figures.
- Extracting scholarly bibliography and citations.
- Expanding search query vectors.
Under no circumstances may a claim enter `SUPPORTED` or `VERIFIED` status if its provenance terminates solely at a Tier 9–13 node.

#### Violation Handling & Engine Action
If an evaluated historical claim is backed exclusively by Tier 9–13 sources:
1. The engine records violation: `HistoriographicalViolationType.UNQUALIFIED_SOLE_SOURCE` (`"POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE"`).
2. The claim is downgraded to `EpistemicStatus.UNSUPPORTED`.
3. For `ClaimType.EVENT_FACT`, the pipeline verdict is a hard `BLOCK`.
4. For `ClaimType.CAUSAL_INTERPRETATION`, the verdict is `HUMAN_REVIEW` or `BLOCK`.

### 2.2 Minimum Evidentiary Thresholds
To be certified as `SUPPORTED` or `VERIFIED`, any historical claim must satisfy at least one of the three following non-negotiable threshold sets:

| Threshold Set | Category | Minimum Required Source Quality | Operational Rule |
|---|---|---|---|
| **Threshold A** | Primary / Archival Backing | >= 1 verified Tier 1 (`PRIMARY_SOURCE`) or Tier 6 (`ARCHIVAL_DOCUMENT`) | Primary treaty text, state paper, archival decree, archaeological excavation report. |
| **Threshold B** | Academic Monograph Backing | >= 1 verified Tier 3 (`ACADEMIC_PRESS_BOOK`) | Monograph published by a recognized university press with rigorous peer review. |
| **Threshold C** | Peer-Reviewed Historiography | >= 2 independent Tier 2 (`PEER_REVIEWED_JOURNAL`) | Two distinct, non-syndicated articles published in recognized peer-reviewed history journals. |

If none of Thresholds A, B, or C is satisfied:
- If only Tier 7–8 sources exist: Maximum allowable status is `PARTIALLY_SUPPORTED`, triggering a warning that primary or academic press confirmation is missing.
- If only Tier 9–13 sources exist: Status is forced to `UNSUPPORTED`.

---

## 3. Consensus States Modeling (8 States)

Historical scholarship cannot be represented as a binary boolean (`True` / `False`). Historians operate through evidential baselines, dominant paradigms, revisionist critiques, open debates, and acknowledged evidential lacunae. 

Harness 9 defines the **8 Canonical Consensus States** (`ConsensusState` in `src/models/contracts.py`):
1. `STRONG_CONSENSUS`
2. `BROAD_CONSENSUS`
3. `MAJORITY_INTERPRETATION`
4. `MINORITY_INTERPRETATION`
5. `ACTIVE_DEBATE`
6. `CONTESTED`
7. `UNRESOLVED`
8. `INSUFFICIENT_LITERATURE`

### 3.1 Formal Definitions & Rhetoric Matrix

| Consensus State | Operational Definition | Evidentiary Requirement | Permitted Script Tone |
|---|---|---|---|
| **`STRONG_CONSENSUS`** | Unanimous agreement across all modern scholarly literature; established historical baseline. | Zero peer-reviewed dissent in the last 50 years; substantiated by multiple independent primary records. | Direct, declarative assertion. (e.g. "On December 23, 1947, Bell Labs demonstrated...") |
| **`BROAD_CONSENSUS`** | Overwhelming consensus among specialists; negligible fringe dissent. | > 90% of academic monographs agree; dissenting arguments lack mainstream peer-reviewed support. | Calibrated consensus attribution. (e.g. "Historians broadly agree...", "Scholarly consensus indicates...") |
| **`MAJORITY_INTERPRETATION`** | Dominant academic paradigm, but recognized alternative scholarly schools exist. | Supported by leading university presses, but recognized peer-reviewed counter-hypotheses exist (50% < R <= 90%). | Paradigmatic framing. (e.g. "The leading historical view holds...", "While debated, evidence points to...") |
| **`MINORITY_INTERPRETATION`** | Credible, peer-reviewed academic thesis held by a qualified minority of historians. | Published in peer-reviewed academic journals or university press monographs; challenges majority paradigm (10% <= R <= 50%). | Explicit counter-perspective attribution. (e.g. "A significant school of historians argues...", "Alternatively, scholars propose...") |
| **`ACTIVE_DEBATE`** | Substantial, unresolved debate with mutually incompatible theories supported by prominent scholars. | Multiple competing peer-reviewed interpretations with neither holding decisive majority agreement. | Balanced dual-attribution. (e.g. "Historians remain divided over whether X or Y...", "Debate centers on...") |
| **`CONTESTED`** | Mutually exclusive claims supported by contradictory primary accounts or contested physical evidence. | Surviving primary sources or archival records directly conflict (e.g. casualty counts, rival invention claims). | Explicit conflict narration. (e.g. "Surviving accounts directly conflict...", "Contemporary records dispute...") |
| **`UNRESOLVED`** | Insufficient surviving documentary evidence to determine factual truth; open historical mystery. | Scholarly literature explicitly concludes that available evidence cannot prove either thesis. | Humble mystery framing. (e.g. "Surviving records leave the question open...", "The ultimate cause remains unknown.") |
| **`INSUFFICIENT_LITERATURE`** | The specific topic or question has not received adequate academic study in peer-reviewed historiography. | < 2 peer-reviewed citations exist in scholarly databases (JSTOR, Historical Abstracts, Google Scholar). | Sparse record disclosure. (e.g. "Historical documentation is sparse...", "With scarce primary records...") |

### 3.2 Mathematical & Logical Classification Criteria

Let a candidate historical claim C be evaluated against scholarly corpus S = S_scholarly union S_primary, where:
- N_primary: Count of independent Tier 1 and Tier 6 primary sources.
- N_peer: Count of peer-reviewed journal articles (Tier 2).
- N_book: Count of university press monographs (Tier 3).
- N_scholarly = N_peer + N_book: Total academic secondary literature.
- N_agree: Academic sources affirming proposition C.
- N_dissent: Academic sources advocating alternative or opposing hypotheses.
- R_agree = N_agree / (N_agree + N_dissent): Scholarly agreement ratio.
- P_contra: Primary contradiction flag (whether surviving primary documents assert contradictory facts).
- M_unresolved: Scholarly consensus flag indicating evidential insolubility.

#### Classification Algorithm:
```
IF N_scholarly < 2 AND N_primary < 1:
    RETURN INSUFFICIENT_LITERATURE

IF P_contra IS TRUE (contradictory primary accounts exist):
    RETURN CONTESTED

IF M_unresolved IS TRUE (scholars agree evidence is lost or permanently inconclusive):
    RETURN UNRESOLVED

IF N_dissent == 0 AND N_primary >= 1 AND N_scholarly >= 2:
    RETURN STRONG_CONSENSUS

IF R_agree >= 0.90:
    RETURN BROAD_CONSENSUS

IF 0.50 < R_agree < 0.90:
    RETURN MAJORITY_INTERPRETATION

IF 0.10 <= R_agree <= 0.50:
    IF is_evaluating_minority_thesis:
        RETURN MINORITY_INTERPRETATION
    ELSE:
        RETURN ACTIVE_DEBATE

IF 0.40 <= R_agree <= 0.60 (or multiple incompatible scholarly schools exist):
    RETURN ACTIVE_DEBATE

RETURN INSUFFICIENT_LITERATURE
```

This decision logic maps every historical claim deterministically to exactly one of the 8 states without heuristic ambiguity.

---

## 4. Event vs. Interpretation Differentiation

A primary failure mode of automated historical storytelling is treating historical causality or motivation with the same epistemic certainty as a documented occurrence. Harness 9 establishes a strict ontological separation between two claim categories.

### 4.1 Physically Documented Occurrences (`ClaimType.EVENT_FACT`)
- **Ontological Nature**: An empirical, spatiotemporally located occurrence attested by contemporary primary documentary records, material culture, or archaeological excavation.
  - *Examples*: 
    - "The Treaty of Versailles was signed in the Hall of Mirrors on June 28, 1919."
    - "John Bardeen and Walter Brattain demonstrated the point-contact transistor on December 23, 1947."
    - "The eruption of Mount Vesuvius destroyed Pompeii in 79 CE."
- **Verification Criteria**:
  - Requires primary documentary source provenance (Tier 1 or Tier 6).
  - Must pass `TEMPORAL_CHECK` (chronological precedence, calendar validation, absence of anachronisms).
- **Narration Rules**:
  - If `ConsensusState` is `STRONG_CONSENSUS`, the event may be stated affirmatively as an objective historical fact.
  - No hedging or epistemological qualification is required.

### 4.2 Scholarly & Causal Interpretations (`ClaimType.CAUSAL_INTERPRETATION` & `ClaimType.SCHOLARLY_INTERPRETATION`)
- **Ontological Nature**: An explanatory hypothesis, causal model, or historiographical narrative explaining why an event occurred, the psychological motives of historical actors, or long-term societal consequences.
  - *Examples*:
    - "The primary cause of the Great Depression was the Federal Reserve's contractionary monetary policy."
    - "The fall of the Roman Republic was driven by agrarian inequality and the rise of private client armies."
    - "The Industrial Revolution began in Britain due to cheap coal and high wages."
- **Verification Criteria**:
  - Must be backed by university press monographs (Tier 3) or peer-reviewed historiography (Tier 2).
  - Must be mapped to an explicit `ConsensusState`.
  - Must catalog competing historiographical schools (e.g. Marxist, Revisionist, Neoclassical, Annales school).
- **The Inviolable Narration Invariant**:
  - **A causal or scholarly interpretation must NEVER be narrated as an uncontested empirical event.**
  - Script generation models are strictly forbidden from writing:
    *Prohibited*: "Rome fell because debasement of the denarius destroyed its currency."
    *Mandated*: "Historians emphasize several interlocking factors, with economic historians pointing to the severe debasement of the denarius."
  - If a script draft narrates an interpretation as an objective fact, the policy engine raises `HistoriographicalViolationType.UNHEDGED_INTERPRETATION` (`"POLICY_VIOLATION_UNHEDGED_INTERPRETATION"`) and blocks script approval until hedged and attributed.

---

## 5. Preserving Contradictions & Calibrating Consensus Language

### 5.1 The Non-Averaging Contradiction Invariant
When historical sources present contradictory quantitative data (casualty counts, troop strengths, population sizes, financial figures) or conflicting event sequences, generative systems frequently calculate an arithmetic mean to create a smooth narrative. 

#### Mathematical Invalidation of Averaging
Let Source A report casualty count N_A = 20,000, and Source B report N_B = 100,000.
A synthetic average:
N_avg = (N_A + N_B) / 2 = 60,000
is **epistemically false**:
- No primary observer recorded 60,000 casualties.
- No peer-reviewed archival study justifies that number.
- It conceals the genuine historiographical debate between official contemporary claims (N_A) and modern revisionist demographic modeling (N_B).

#### The Invariant Formulation
For all claims C_A, C_B where C_A.value != C_B.value:
SynthesizeAverage(C_A, C_B) -> PROHIBITED.

#### Operational Requirements:
1. Both conflicting propositions must be preserved as discrete nodes in the Evidence Graph.
2. They must be linked via a directed `EdgeRelation.CONTRADICTION` edge.
3. The claim's status must be assigned `EpistemicStatus.CONTESTED`, and the consensus state set to `ConsensusState.CONTESTED`.
4. The script generator must be forced to narrate the range and context:
   *"Casualty figures remain heavily contested: while official state records claimed 20,000 fallen, subsequent archival reconstructions estimate losses exceeded 100,000."*

### 5.2 Calibrated Narration Rhetoric Matrix
The policy engine enforces a strict mapping between consensus state and allowed/forbidden rhetorical framing in generated voiceover scripts:

| Consensus State | Mandated Phrasing Patterns | Strictly Forbidden Phrasing |
|---|---|---|
| **`STRONG_CONSENSUS`** | Declarative affirmative statements ("In 1947, Bell Labs demonstrated...", "The treaty was signed on...") | Speculative doubt ("allegedly", "it is claimed that", "some believe") |
| **`BROAD_CONSENSUS`** | "Historical evidence demonstrates...", "Scholarly consensus indicates...", "Extensive archival research shows..." | Absolute dogmatic assertion without context; dismissive phrasing toward established context |
| **`MAJORITY_INTERPRETATION`** | "The dominant historical view holds...", "Most evidence points to...", "A leading explanation among historians is..." | Presenting the majority view as the sole indisputable fact ("it is an established fact that...") |
| **`MINORITY_INTERPRETATION`** | "An important scholarly counter-thesis argues...", "Historians such as X emphasize...", "Alternatively, revisionist scholars propose..." | Presenting minority scholarship as mainstream consensus OR dismissing it as ungrounded conspiracy |
| **`ACTIVE_DEBATE`** | "Historians remain divided over whether X or Y...", "Scholarly debate centers on two competing perspectives..." | Picking one side and presenting it as accepted truth; erasing opposing academic viewpoints |
| **`CONTESTED`** | "Surviving accounts directly conflict...", "Estimates range widely from X to Y...", "Contemporary records dispute..." | Averaging divergent numbers; declaring a single primary account correct without qualification |
| **`UNRESOLVED`** | "Surviving records leave this question unanswered...", "Historical evidence remains inconclusive...", "The ultimate cause remains unknown." | Fabricating neat resolutions; pretending lost evidence is known |
| **`INSUFFICIENT_LITERATURE`** | "Due to limited surviving documentation...", "With scarce primary records surviving..." | Presenting modern speculation or internet rumors as historical authority |

### 5.3 Balanced Attribution Rules
For claims classified under `ACTIVE_DEBATE`, `CONTESTED`, or `MINORITY_INTERPRETATION`, the policy mandates **Balanced Attribution**:
- The narration must name or cite the representative scholarly perspectives.
- Phrasing pattern:
  "Historians such as [Scholar/School A] argue [Perspective A], whereas [Scholar/School B] contends [Perspective B]."
- If a script beat covers a contested topic but cites only one school of thought, the policy engine raises `HistoriographicalViolationType.UNBALANCED_ATTRIBUTION` and halts script approval.

---

## 6. Concrete Architecture and Signatures for `src/epistemic/historical_policy.py`

Below is the complete, production-grade architectural specification for `HistoricalPolicyChecker` (and its canonical alias `HistoricalScholarshipPolicyEngine`).

### 6.1 Data Models & Schemas
```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    H9BaseModel,
    SourceRecord,
    SourceTier,
)


class HistoriographicalViolationType(str, Enum):
    \"\"\"Categories of historiographical scholarship policy violations.\"\"\"
    UNQUALIFIED_SOLE_SOURCE = "POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE"
    INSUFFICIENT_TIER_THRESHOLD = "POLICY_VIOLATION_INSUFFICIENT_TIER_THRESHOLD"
    UNHEDGED_INTERPRETATION = "POLICY_VIOLATION_UNHEDGED_INTERPRETATION"
    NUMERICAL_AVERAGING_DETECTED = "POLICY_VIOLATION_NUMERICAL_AVERAGING"
    UNBALANCED_ATTRIBUTION = "POLICY_VIOLATION_UNBALANCED_ATTRIBUTION"
    SPECULATIVE_CERTAINTY = "POLICY_VIOLATION_SPECULATIVE_CERTAINTY"
    ANACHRONISM_DETECTED = "POLICY_VIOLATION_ANACHRONISM"


class HistoricalFraming(H9BaseModel):
    \"\"\"Prescribed rhetorical rules for voiceover script generation.\"\"\"
    consensus_state: ConsensusState
    mandated_phrases: List[str] = field(default_factory=list)
    forbidden_phrases: List[str] = field(default_factory=list)
    attribution_template: Optional[str] = None
    tone_directive: str = "neutral_scholarly"
    requires_hedging: bool = False
    requires_balanced_perspectives: bool = False


class HistoriographicalEvaluationReport(H9BaseModel):
    \"\"\"Comprehensive audit report for a historical claim.\"\"\"
    claim_id: str
    claim_type: ClaimType
    consensus_state: ConsensusState
    epistemic_status: EpistemicStatus
    eligible_for_narration: bool
    violations: List[HistoriographicalViolationType] = field(default_factory=list)
    violation_details: List[str] = field(default_factory=list)
    highest_source_tier: SourceTier
    qualifying_threshold: Optional[str] = None  # "Threshold A", "Threshold B", or "Threshold C"
    mandated_framing: HistoricalFraming
    is_averaged: bool = False
    divergent_values_preserved: List[Union[str, float, int]] = field(default_factory=list)
    evaluated_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ContradictionRecord(H9BaseModel):
    \"\"\"Preserves un-averaged contradictory accounts.\"\"\"
    claim_id: str
    parameter_name: str
    conflicting_assertions: List[Dict[str, Any]] = field(default_factory=list)
    reported_range: Optional[Tuple[float, float]] = None
    is_numeric: bool = False
    narrative_recommendation: str = ""
```

### 6.2 The `HistoricalPolicyChecker` Class Interface
```python
class HistoricalPolicyChecker:
    \"\"\"Evaluates historical claims and enforces historiographical scholarship rules.\"\"\"

    FORBIDDEN_SOLE_SOURCE_TIERS: Set[SourceTier] = {
        SourceTier.REPUTABLE_JOURNALISM,      # Tier 9 (when used as sole establishing source)
        SourceTier.TRADE_PUBLICATION,         # Tier 10
        SourceTier.POPULAR_MEDIA,             # Tier 11
        SourceTier.SELF_PUBLISHED,            # Tier 12
        SourceTier.UNVERIFIED,                # Tier 13
    }

    PRIMARY_TIERS: Set[SourceTier] = {
        SourceTier.PRIMARY_SOURCE,            # Tier 1
        SourceTier.ARCHIVAL_DOCUMENT,         # Tier 6
    }

    ACADEMIC_BOOK_TIERS: Set[SourceTier] = {
        SourceTier.ACADEMIC_BOOK,             # Tier 3
    }

    PEER_REVIEWED_TIERS: Set[SourceTier] = {
        SourceTier.PEER_REVIEWED_JOURNAL,     # Tier 2
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def evaluate_claim(
        self,
        claim: ClaimRecord,
        sources: Optional[List[SourceRecord]] = None,
        opposing_claims: Optional[List[ClaimRecord]] = None,
    ) -> HistoriographicalEvaluationReport:
        \"\"\"Executes end-to-end historical policy verification on a candidate claim.\"\"\"
        ...

    def check_forbidden_sole_source(
        self,
        sources: List[SourceRecord],
    ) -> Tuple[bool, List[str]]:
        \"\"\"Returns (is_valid, violation_messages). Rejects if all sources are Tiers 9-13.\"\"\"
        ...

    def verify_minimum_source_tiers(
        self,
        sources: List[SourceRecord],
        claim_type: ClaimType,
    ) -> Tuple[bool, Optional[str], List[str]]:
        \"\"\"Verifies satisfaction of Threshold A, B, or C. Returns (is_valid, threshold_name, messages).\"\"\"
        ...

    def classify_consensus_state(
        self,
        claim: ClaimRecord,
        sources: List[SourceRecord],
        opposing_claims: Optional[List[ClaimRecord]] = None,
    ) -> ConsensusState:
        \"\"\"Classifies claim into one of the 8 ConsensusState categories from literature distribution.\"\"\"
        ...

    def validate_event_vs_interpretation(
        self,
        claim: ClaimRecord,
        consensus_state: ConsensusState,
    ) -> Tuple[bool, List[str]]:
        \"\"\"Ensures causal interpretations are never framed as uncontested empirical events.\"\"\"
        ...

    def enforce_non_averaging(
        self,
        claim_id: str,
        asserted_value: Union[float, int, str],
        source_values: List[Union[float, int, str]],
    ) -> Tuple[bool, Optional[ContradictionRecord], List[str]]:
        \"\"\"Detects and prohibits arithmetic averaging of divergent numbers or accounts.\"\"\"
        ...

    def check_narration_framing(
        self,
        script_text: str,
        consensus_state: ConsensusState,
        claim_type: ClaimType,
    ) -> Tuple[bool, List[str]]:
        \"\"\"Audits generated voiceover text against the mandated phrasing and forbidden rhetoric matrix.\"\"\"
        ...

    def format_balanced_attribution(
        self,
        perspectives: List[Dict[str, str]],
    ) -> str:
        \"\"\"Generates a balanced attribution string conforming to policy templates.\"\"\"
        ...

    def get_mandated_framing(
        self,
        consensus_state: ConsensusState,
        claim_type: Optional[ClaimType] = None,
    ) -> HistoricalFraming:
        \"\"\"Returns the prescribed HistoricalFraming rules for a given consensus state.\"\"\"
        ...


# Canonical alias for compatibility with docs and specifications
HistoricalScholarshipPolicyEngine = HistoricalPolicyChecker
```

---

## 7. Integration Blueprint & Verification Plan

### 7.1 Integration with `src/epistemic/graph.py`
1. `EvidenceGraph.add_claim()` and `from_dossier()`:
   - When a claim is added, `HistoricalPolicyChecker.classify_consensus_state()` assigns `consensus_state`.
   - If conflicting accounts are detected, the graph creates `EdgeRelation.CONTRADICTION` between the conflicting evidence units and sets `ClaimNode.consensus_state = ConsensusState.CONTESTED`.
2. Lineage checks:
   - `graph.trace_lineage(claim_id)` verifies that ancestor `SourceNode` objects meet Thresholds A, B, or C.

### 7.2 Integration with `src/epistemic/engine.py`
1. Strategy Dispatch:
   - `ClaimType.EVENT_FACT` dispatches to `HISTORIOGRAPHICAL_CHECK` alongside `SOURCE_ENTAILMENT` and `TEMPORAL_CHECK`.
   - `ClaimType.CAUSAL_INTERPRETATION` and `ClaimType.SCHOLARLY_INTERPRETATION` prioritize `HISTORIOGRAPHICAL_CHECK` and `CONTRADICTION_CHECK`.
2. Engine Trace Node:
   - The engine logs `VerificationTraceNode` with `strategy_used="HISTORIOGRAPHICAL_CHECK"`, `consensus_state_assigned`, and any `HistoriographicalViolationType` recorded in `warnings`.

### 7.3 Integration with Lifecycle State Machine (`src/orchestrator/state_machine.py`)
1. `RESEARCH_VERIFICATION` Gate:
   - Evaluates `HistoricalPolicyChecker.evaluate_claim()` on all research claims.
   - If any claim has `UNQUALIFIED_SOLE_SOURCE` or fails minimum tiers, the gate evaluates to `BLOCK`.
2. `SCRIPT_FACT_CHECK` Gate:
   - Evaluates `HistoricalPolicyChecker.check_narration_framing()`.
   - If an unhedged interpretation or averaged contradiction is detected, returns `BLOCK` (forcing script regeneration) or `HUMAN_REVIEW`.

### 7.4 Verification & Unit Test Suite (`tests/test_historical_policy.py`)
The implementation will be verified against a comprehensive pytest suite covering:
1. `test_sole_web_source_rejection`: Claims backed only by Wikipedia / blog are assigned `UNSUPPORTED`.
2. `test_minimum_tier_thresholds`: Verification of Thresholds A (Primary), B (Monograph), and C (2 Peer-Reviewed).
3. `test_8_consensus_states_classification`: Test cases covering all 8 consensus states.
4. `test_event_vs_interpretation_differentiation`: Ensuring event claims permit declarative assertions while causal interpretations require hedging.
5. `test_non_averaging_invariant`: Feeding casualty claims of 20,000 and 100,000, asserting that 60,000 average is rejected and both values are preserved with `CONTESTED` status.
6. `test_narration_framing_calibration`: Auditing script strings for forbidden and mandated phrases.
7. `test_balanced_attribution_formatting`: Validating template generation for multi-perspective debates.
"""

Path('g:/Finding-new-code/harness9/.agents/explorer_2_m3/analysis.md').write_text(content, encoding='utf-8')
print('analysis.md written successfully!')
