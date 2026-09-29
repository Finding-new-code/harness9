# Epistemic Post-Script Claim Verification Engine Specification: Milestone 4 (R4)
**Author:** explorer_1_m4_gen9 (Teamwork Preview Spec Miner)  
**Target Module:** `src/epistemic/script_verifier.py`  
**Related Test Suite:** `tests/unit/test_script_verifier.py`, `tests/epistemic/test_script_fact_check.py`  
**Date:** 2026-09-14  

---

## 1. Observation

Direct inspection of the Harness 9 codebase and canonical specifications reveals the existing state, architectural requirements, and design contracts:

1. **`ORIGINAL_REQUEST.md` (lines 230–232, 256):**
   - *"R4. Multi-Stage Pipeline & Visual/Numerical Integrity: Implement post-script claim extraction and re-verification comparing script claims against the evidence graph to detect strengthened claims, altered numbers, omitted uncertainty, or fabricated quotes (enforcing strict quote verification and paraphrase rules)."*
   - *"Acceptance Criteria: Script claims independently re-extracted and audited against the evidence graph."*

2. **`PROJECT.md` (lines 54, 92–96, 117):**
   - Feature 10: Post-Script Claim Re-Verification in `src/epistemic/script_verifier.py` for Milestone 4 (R4).
   - Interface Contract: `ScriptVerifier.verify_script(script: ScriptDraft, graph: EvidenceGraph) -> ScriptVerificationReport`.
   - Required checks:
     - Detect strengthened claims (confidence escalated beyond evidence support).
     - Detect altered numbers (numerical values differing from source evidence).
     - Detect omitted uncertainty (epistemic hedging removed in narration).
     - Detect fabricated quotes (strict quote matching or paraphrase mandate).

3. **`docs/epistemic/FACT_CHECKING_SPEC.md` (lines 151–184):**
   - Pipeline 2: Post-Script Narration Claim Re-Extraction & Auditing:
     1. Sentence Decomposition: Parses generated voiceover text into discrete sentences.
     2. Script Claim Extraction: Deconstructs each sentence into one or more candidate assertions ($C_{\text{script}}$).
     3. Bipartite Graph Alignment: Computes cosine similarity / token overlap between $C_{\text{script}}$ and $C_{\text{dossier}}$ nodes in Evidence Graph.
     4. Drift Detection:
        - Strengthening: Flagged if $C_{\text{dossier}}$ has epistemic qualifier ("preliminary", "suggests") but $C_{\text{script}}$ uses absolute phrasing ("proven", "definitely").
        - Numerical Mutation: Flagged if $|V_{\text{script}} - V_{\text{dossier}}| / V_{\text{dossier}} > \text{Tolerance}$.
        - Quote Fabrication: Flagged if quotation marks enclose text with normalized Levenshtein distance $> 0.02$ from primary text.

4. **`docs/epistemic/CLAIM_VERIFICATION.md` (lines 36–46, 72–87, 90–105):**
   - Modality Qualification Comparison:
     $$\text{Strength} = \begin{cases}
     3 & \text{"always", "proven", "definitely", "solely", "undoubtedly", "certainly", "indisputable", "conclusively"} \\
     2 & \text{"generally", "typically", "the primary", "most", "likely"} \\
     1 & \text{"may", "suggests", "one factor", "partially", "possibly", "could", "preliminary", "hypothesized"}
     \end{cases}$$
     Invariant: If $M(C_{\text{script}}) > M(C_{\text{evidence}})$, flag `STRENGTHENED_ASSERTION_WARNING`.
   - Quote Check Normalized Levenshtein distance:
     $$D_{\text{norm}}(Q_{\text{asserted}}, Q_{\text{archive}}) = \frac{\text{Levenshtein}(Q_{\text{asserted}}, Q_{\text{archive}})}{\max(|Q_{\text{asserted}}|, |Q_{\text{archive}}|)}$$
     - $D_{\text{norm}} \le 0.02$: `EXACT`.
     - $0.02 < D_{\text{norm}} \le 0.15$ with ellipses: `ELLIPSES`.
     - $D_{\text{norm}} > 0.02$ without ellipses: `DISTORTED` / `FABRICATED` $\to$ Paraphrase Mandate (quotation marks must be stripped).
   - Numerical Check:
     - Dual tolerance: $\epsilon = 0.001$ ($0.1\%$) for exact values; $\epsilon = 0.05$ ($5.0\%$) for approximate values.
     - Order of magnitude mismatch trap: $|\log_{10}(V_{\text{script}}) - \log_{10}(V_{\text{evidence}})| \ge 1.0$.

5. **`docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md` (lines 112–147):**
   - Non-averaging invariant: Prohibits arithmetic synthesis of conflicting counts or dates.
   - Consensus State Framing rules:
     - `ACTIVE_DEBATE`: Mandates phrasing: *"Historians remain divided over whether X or Y..."*.
     - `CONTESTED`: Mandates phrasing: *"Contemporary sources directly contradict each other...", "Estimates range from X to Y..."*. Forbids picking one side.
     - `MINORITY_INTERPRETATION`: Mandates phrasing: *"An important scholarly counter-thesis argues..."*.
     - `UNRESOLVED`: Mandates phrasing: *"Surviving records leave this question unanswered..."*.

6. **`src/models/contracts.py` (lines 568–676):**
   - `ScriptBeat`: `beat_id`, `beat_index`, `start_time` / `start_second`, `end_time` / `end_second`, `duration`, `text`, `visual_cue`.
   - `ScriptScene`: `scene_id`, `scene_index`, `title`, `start_time`, `duration`, `narration_text` / `narration`, `beats: List[ScriptBeat]`.
   - `Script`: `topic`, `title`, `total_duration`, `full_transcript`, `scenes: List[ScriptScene]`.
   - `ClaimRecord`: `claim_id`, `claim_text`, `epistemic_status: EpistemicStatus`, `consensus_state: ConsensusState`, `confidence_score: float`, `claim_type: ClaimType`, `primary_source: SourceRecord`, `evidence_node_ids: List[str]`, `verifier_metadata: Dict[str, Any]`.

7. **`src/epistemic/graph.py` (lines 198–223, 534–565):**
   - `SceneNode`: `scene_id`, `scene_index`, `title`, `start_time_seconds`, `duration_seconds`, `narration_text`.
   - `ScriptSentenceNode`: `node_id`, `scene_id`, `beat_id`, `sentence_text`, `start_time_seconds`, `end_time_seconds`, `grounded_claim_ids`, `hedging_applied`, `paraphrase_mandated`.
   - Method `graph.add_script_sentence(scene_id, beat_id, sentence_text, start_time_seconds, end_time_seconds, grounded_claim_ids, hedging_applied, paraphrase_mandated)`.
   - Graph Edge Relations: `EdgeRelation.ENTAILMENT` (grounds claim to sentence), `EdgeRelation.DERIVES_FROM`, `EdgeRelation.CONTRADICTION`.

8. **`src/epistemic/engine.py` (lines 157–167, 200–284, 462–563):**
   - `VerificationEngine` with registered strategies: `SourceEntailmentStrategy`, `CrossSourceCorroborationStrategy`, `ContradictionCheckStrategy`, `QuoteCheckStrategy`, `NumericalCheckStrategy`, `TemporalCheckStrategy`, `HistoriographicalCheckStrategy`.
   - Gate outcome taxonomy: `PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`.

---

## 2. Logic Chain

From the observations above, we establish the following deductive chain for the design and implementation of `src/epistemic/script_verifier.py`:

1. **Input Polysemy Resolution:**
   - In Harness 9, scripts may be passed as `src.models.contracts.Script`, `src.models.script.Script`, dictionary dumps, or raw string transcripts.
   - Therefore, `ScriptVerifier` must accept `Union[Script, Dict[str, Any], str]`, normalizing any input into a canonical scene and beat structure.

2. **Hierarchical Sentence Segmentation & Temporal Anchor Mapping:**
   - A video script's voiceover narration is delivered in beats (`ScriptBeat`) within scenes (`ScriptScene`).
   - Simple string splitting on `.` introduces catastrophic bugs on abbreviations ("Dr.", "U.S.", "e.g."), decimal numbers ("3.14", "$4.2M"), ellipses ("..."), and quotes with terminal periods (`"No."`).
   - Therefore, `ScriptVerifier` must implement a robust abbreviation-protected, quote-aware sentence segmenter (`_segment_sentences`), tracking exact timestamp intervals:
     $$\text{start\_time} = \text{beat.start\_time} + \left( \frac{\text{sentence\_start\_char}}{\text{total\_beat\_chars}} \times \text{beat.duration} \right)$$
     $$\text{end\_time} = \text{beat.start\_time} + \left( \frac{\text{sentence\_end\_char}}{\text{total\_beat\_chars}} \times \text{beat.duration} \right)$$

3. **Bipartite Alignment against EvidenceGraph:**
   - Once atomic sentences $S_i$ are extracted, they must be matched to corresponding `ClaimNode` or `EvidenceUnitNode` in the `EvidenceGraph`.
   - If the script was generated from a `ResearchDossier` or has `grounded_claim_ids`, direct metadata mapping takes precedence.
   - For unlinked sentences, semantic similarity is computed over lemmatized content words, numbers, and entities.
   - Sentences failing to match any evidence node with similarity $\ge 0.35$ are classified as `UNGROUNDED_CLAIM`.

4. **Forensic Drift Detection Engine:**
   - For each aligned pair $(S_i, C_j)$, the engine executes four orthogonal drift audits:
     - **Strengthening**: Checks if $M(S_i) > M(C_j)$ or if $C_j$ confidence $\le 0.70$ is stated without epistemic qualification as certain fact.
     - **Altered Number**: Extracts numbers $V_S$ and compares to $V_E$. Computes relative delta $\Delta = |V_S - V_E| / |V_E|$. Checks dual tolerance ($\epsilon_{\text{exact}} = 0.001$, $\epsilon_{\text{approx}} = 0.05$) and order-of-magnitude ratio ($|\log_{10}(V_S) - \log_{10}(V_E)| \ge 1.0$).
     - **Omitted Uncertainty**: If $C_j$ has status in `UNVERIFIED`, `CONTESTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `UNVERIFIABLE` or consensus in `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, checks whether $S_i$ contains mandatory hedging phrases. If missing, flags omitted uncertainty.
     - **Fabricated Quote**: If $S_i$ contains quotation marks, extracts quote substring $Q_S$ and compares via normalized Levenshtein distance against archival quote $Q_A$ in EvidenceGraph. If $D_{\text{norm}} > 0.02$ without ellipses, flags quote fabrication and triggers the Paraphrase Mandate.

5. **Actionable Remediation & DAG Mutation:**
   - Drift detection without actionable feedback causes pipelines to halt indefinitely. Every `ScriptClaimDriftRecord` must provide a concrete, syntactically valid `recommended_edit`.
   - When verified against an `EvidenceGraph`, the verifier must mutatively insert `ScriptSentenceNode` instances and link them with `ENTAILS` edges to `ClaimNode`, setting flags `hedging_applied` and `paraphrase_mandated`.
   - It records a `VerificationTraceNode` targeting each `ScriptSentenceNode`, ensuring complete audit closure.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Ingestion | `ScriptNormalizer` | Accepts `contracts.Script`, `models.script.Script`, `dict`, or raw text; normalizes into structured scene/beat stream | `Union[Script, Dict[str, Any], str]` | `List[NormalizedScene]` with timestamped beats | Raises `ValueError` on empty or completely unparseable input | `src/models/contracts.py`, `src/models/script.py` |
| 2 | Extraction | `SentenceSegmenter` | Abbreviation-protected, quote-aware sentence splitter avoiding splits on decimals, abbreviations, and ellipses | Raw voiceover string | `List[str]` of discrete grammatical sentences | Preserves intact text on regex corner cases | `docs/epistemic/FACT_CHECKING_SPEC.md` |
| 3 | Extraction | `TemporalAnchorMapper` | Computes fractional sentence timestamp bounds and extracts explicit historical years/dates/eras | Spoken beat, beat time window, sentence text | `Tuple[float, float]` (start, end) & `List[str]` temporal anchors | Clamps to beat `[start_time, end_time]` on overflow | `docs/epistemic/CLAIM_VERIFICATION.md`, `src/epistemic/graph.py` |
| 4 | Extraction | `CandidateAssertionExtractor` | Extracts candidate factual propositions ($C_{\text{script}}$), filters rhetorical filler, detects modal level (1–3), numbers, and quotes | `ScriptSentenceExtraction` | `ExtractedAssertion` with feature flags | Returns empty list if sentence is purely rhetorical commentary | `docs/epistemic/CLAIM_VERIFICATION.md` |
| 5 | Alignment | `BipartiteEvidenceAligner` | Aligns script sentences to `EvidenceGraph` `ClaimNode` using metadata IDs, entity matching, and token overlap | Extracted sentences, `EvidenceGraph` | `List[ScriptClaimMapping]` with alignment scores | Unaligned sentences marked `is_grounded=False` (`UNGROUNDED_CLAIM`) | `docs/epistemic/FACT_CHECKING_SPEC.md` |
| 6 | Drift Detection | `StrengthenedClaimDetector` | Compares modal certainty ($M(S) \text{ vs } M(E)$) and confidence scores; flags unearned dogmatic certainty | Aligned script claim, evidence node | `Optional[ScriptClaimDriftRecord]` (STRENGTHENED) | Emits HIGH severity if modal 1 escalated to 3 | `docs/epistemic/CLAIM_VERIFICATION.md` §2.1 |
| 7 | Drift Detection | `AlteredNumberDetector` | Normalizes SI units and multipliers; verifies dual tolerance (0.1% / 5.0%) and order-of-magnitude traps | Script numbers, evidence numbers, qualifier context | `Optional[ScriptClaimDriftRecord]` (ALTERED_NUMBER) | Emits CRITICAL severity on order-of-magnitude errors | `docs/epistemic/CLAIM_VERIFICATION.md` §2.5 |
| 8 | Drift Detection | `OmittedUncertaintyDetector` | Verifies epistemic hedging presence for UNVERIFIED, CONTESTED, ACTIVE_DEBATE, or DISPUTED claims | Script sentence, evidence status, consensus state | `Optional[ScriptClaimDriftRecord]` (OMITTED_UNCERTAINTY) | Emits CRITICAL if contradicted/contested claim asserted as fact | `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md` §6 |
| 9 | Drift Detection | `FabricatedQuoteDetector` | Normalizes quote punctuation; computes character Levenshtein distance; enforces Paraphrase Mandate | Script quote, archival primary quote | `Optional[ScriptClaimDriftRecord]` (FABRICATED_QUOTE) | Emits CRITICAL if $D_{\text{norm}} > 0.02$ without ellipses | `docs/epistemic/CLAIM_VERIFICATION.md` §2.4 |
| 10 | Contract | `ScriptVerificationReport` | Comprehensive report schema including drift records, severity counts, gate recommendation, and revision | Script, EvidenceGraph | `ScriptVerificationReport` | Deterministic validation via Pydantic v2 | `PROJECT.md` Interface Contracts |
| 11 | Remediation | `ScriptAutoRemediator` | Produces revised `Script` by stripping fabricated quotes into paraphrases, adding hedges, and correcting numbers | `Script`, `ScriptVerificationReport` | Revised `Script` ready for re-check | Preserves original beat timings and visual cues | `docs/epistemic/FACT_CHECKING_SPEC.md` §7 |
| 12 | Integration | `EvidenceGraphSynchronizer` | Mutatively inserts `ScriptSentenceNode` and `VerificationTraceNode` into EvidenceGraph DAG | `ScriptVerificationReport`, `EvidenceGraph` | Mutated `EvidenceGraph` with full provenance | Rejects edge additions that introduce cycles (`CycleDetectedError`) | `src/epistemic/graph.py` |
| 13 | Integration | `VerificationEngineBridge` | Exposes `verify_script()` as an engine method and supports dispatch of individual assertions to engine strategies | `VerificationEngine`, `Script` | `ScriptVerificationReport` | Safe fallback if EvidenceGraph is empty | `src/epistemic/engine.py` |

---

## 4. Edge Cases & Observed Behaviors

| # | Feature | Input | Observed / Prescribed Behavior |
|---|---------|-------|--------------------------------|
| 1 | Sentence Segmentation | Voiceover: `"Dr. Shockley developed the junction transistor at Bell Labs in the U.S. for $3.5M."` | Correctly segments into **1 sentence**, not splitting at `"Dr."`, `"U.S."`, or `"$3.5M."`. |
| 2 | Sentence Segmentation | Voiceover: `"He shouted 'Stop!' and ran."` | Correctly identifies quotation punctuation boundary and does not split mid-quote. |
| 3 | Number Normalization | Evidence: `50,000` casualties; Script: `"Over 500,000 soldiers perished."` | Flags `DriftType.ALTERED_NUMBER`, severity `CRITICAL` due to 10x order-of-magnitude mismatch ($|\log_{10}(500000) - \log_{10}(50000)| = 1.0$). Recommends: `"Over 50,000 soldiers perished."` |
| 4 | Number Approximation | Evidence: `4,980`; Script: `"Approximately 5,000 units were produced."` | Relative delta $\Delta = |5000 - 4980| / 4980 = 0.004$ ($0.4\%$). Since script contains `"Approximately"`, tolerance is $5.0\%$; check **passes** with zero drift. |
| 5 | Number Strictness | Evidence: `4,980`; Script: `"Exactly 5,000 units were produced."` | Relative delta $\Delta = 0.4\% > 0.1\%$ exact tolerance window. Flags `DriftType.ALTERED_NUMBER`, severity `MEDIUM`. Recommends `"Exactly 4,980 units"`. |
| 6 | Strengthened Claim | Evidence: `"Recent findings suggest a potential link between diet and longevity."` (Modal Level 1); Script: `"Scientists have definitively proven that diet cures aging."` (Modal Level 3) | Flags `DriftType.STRENGTHENED`, severity `HIGH`. Recommends demoting to: `"Recent findings suggest that diet influences aging."` |
| 7 | Omitted Uncertainty | Evidence claim has `ConsensusState.ACTIVE_DEBATE` (e.g. causes of Bronze Age collapse); Script: `"The collapse of Bronze Age civilizations was solely caused by the Sea Peoples."` | Flags `DriftType.OMITTED_UNCERTAINTY`, severity `HIGH`. Recommends calibrated framing: `"While the Sea Peoples played a role, historians remain divided over the multi-causal collapse."` |
| 8 | Fabricated Quote | Archival text: `"There is plenty of room at the bottom."`; Script: `"Feynman famously proclaimed: 'We can easily shrink machines to the atomic scale!'"` | $D_{\text{norm}} \approx 0.85 > 0.02$. Flags `DriftType.FABRICATED_QUOTE`, severity `CRITICAL`. Mandates paraphrase: strips quotes to `"Feynman famously discussed shrinking machines to the atomic scale."` |
| 9 | Quote with Ellipses | Archival text: `"In the beginning was the Word, and the Word was with God."`; Script: `"'In the beginning... the Word was with God.'" ` | Normalized distance with standard omission is $\le 0.15$ and all sub-phrases exist in archive. Classified as `QuoteExactness.ELLIPSES`, passes without drift. |
| 10 | Ungrounded Claim | Script: `"Bell Labs was secretly funded by alien technology."` (No matching node in EvidenceGraph) | Aligner finds no candidate above 0.35 similarity. Flags `DriftType.UNGROUNDED_CLAIM`, severity `HIGH`. Gate outcome evaluates to `BLOCK` or `HUMAN_REVIEW`. |
| 11 | Empty / Silent Beats | Script contains an instrumental pause beat with text `""` or `"[Music]"` | Sentence extractor safely filters non-vocal audio cues without raising segmentation errors. |
| 12 | Graph Cycle Defense | Script sentence aligned to Claim $A$ references Beat $B$, which is linked to Scene $C$ | Aligner tests `graph.would_create_cycle(c_id, sent_id)` before adding `ENTAILS` edge, preventing `CycleDetectedError`. |

---

## 5. Specification Architecture for `src/epistemic/script_verifier.py`

### 5.1 Enums & Data Contracts

```python
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import Field
from src.models.contracts import (
    ClaimRecord,
    ClaimType,
    ConsensusState,
    EpistemicStatus,
    H9BaseModel,
    QuoteExactness,
    ResearchDossier,
    Script,
    ScriptBeat,
    ScriptScene,
    SourceRecord,
    SourceTier,
)

class DriftType(str, Enum):
    """Categorical taxonomy of factual semantic drift in generated scripts."""
    STRENGTHENED = "strengthened"
    ALTERED_NUMBER = "altered_number"
    OMITTED_UNCERTAINTY = "omitted_uncertainty"
    FABRICATED_QUOTE = "fabricated_quote"
    UNGROUNDED_CLAIM = "ungrounded_claim"
    ANACHRONISM = "anachronism"

class DriftSeverity(str, Enum):
    """Impact level of a detected drift on publication gating."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ScriptClaimDriftRecord(H9BaseModel):
    """Detailed forensic record of an identified factual drift in a script beat."""
    drift_id: str = Field(default_factory=lambda: f"drift_{uuid.uuid4().hex[:8]}")
    drift_type: DriftType
    severity: DriftSeverity
    scene_id: str
    beat_id: Optional[str] = None
    script_sentence: str
    evidence_claim_id: Optional[str] = None
    evidence_text: Optional[str] = None
    observed_value: Any = None
    expected_value: Any = None
    explanation: str
    recommended_edit: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScriptClaimMapping(H9BaseModel):
    """Provenance mapping connecting a script sentence to an EvidenceGraph node."""
    mapping_id: str = Field(default_factory=lambda: f"map_{uuid.uuid4().hex[:8]}")
    scene_id: str
    beat_id: Optional[str] = None
    sentence_text: str
    start_time: float = 0.0
    end_time: float = 0.0
    aligned_claim_id: Optional[str] = None
    alignment_score: float = 0.0
    is_grounded: bool = False
    has_drift: bool = False
    drifts: List[ScriptClaimDriftRecord] = Field(default_factory=list)

class ScriptVerificationReport(H9BaseModel):
    """Canonical verification verdict emitted by ScriptVerifier."""
    report_id: str = Field(default_factory=lambda: f"svr_{uuid.uuid4().hex[:8]}")
    project_id: Optional[str] = None
    topic: str = ""
    total_scenes: int = 0
    total_beats: int = 0
    total_sentences: int = 0
    grounded_sentences_count: int = 0
    ungrounded_sentences_count: int = 0
    drifts: List[ScriptClaimDriftRecord] = Field(default_factory=list)
    drift_counts_by_type: Dict[str, int] = Field(default_factory=dict)
    drift_counts_by_severity: Dict[str, int] = Field(default_factory=dict)
    mappings: List[ScriptClaimMapping] = Field(default_factory=list)
    passed: bool = True
    gate_recommendation: str = "PASS"  # PASS | WARN | HUMAN_REVIEW | BLOCK
    summary: str = ""
    revised_script: Optional[Script] = None
    graph_id: str = ""
    duration_ms: float = 0.0
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

### 5.2 Algorithmic Subsystems

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SCRIPT VERIFIER ARCHITECTURE                          │
│                                                                             │
│   [ Script: scenes, beats, voiceover text ]                                 │
│                     │                                                       │
│                     ▼                                                       │
│   ┌──────────────────────────────────────────────────┐                      │
│   │ 1. Script Normalizer & Sentence Segmenter        │                      │
│   │    - Protected abbreviations, decimals, quotes   │                      │
│   │    - Temporal window bounds calculation          │                      │
│   └─────────────────┬────────────────────────────────┘                      │
│                     │                                                       │
│                     ▼                                                       │
│   ┌──────────────────────────────────────────────────┐                      │
│   │ 2. Bipartite Evidence Graph Aligner              │                      │
│   │    - Metadata linking (grounded_claim_ids)       │ ◄─── [ EvidenceGraph ]
│   │    - Lexical, entity, and numerical alignment    │                      │
│   └─────────────────┬────────────────────────────────┘                      │
│                     │                                                       │
│                     ▼                                                       │
│   ┌──────────────────────────────────────────────────┐                      │
│   │ 3. 4-Fold Drift Detection Engine                 │                      │
│   │    ├─ Strengthened Claim Detector (Modal L1-L3)  │                      │
│   │    ├─ Altered Number Detector (Dual Tolerance)   │                      │
│   │    ├─ Omitted Uncertainty Detector (Consensus)   │                      │
│   │    └─ Fabricated Quote Detector (Levenshtein)    │                      │
│   └─────────────────┬────────────────────────────────┘                      │
│                     │                                                       │
│                     ▼                                                       │
│   ┌──────────────────────────────────────────────────┐                      │
│   │ 4. Remediation & EvidenceGraph Mutation          │                      │
│   │    - Auto-remediation (paraphrase mandate)       │                      │
│   │    - Inserts ScriptSentenceNode & TraceNode      │ ───► [ Mutated Graph]
│   │    - Evaluates gate: PASS/WARN/REVIEW/BLOCK      │                      │
│   └─────────────────┬────────────────────────────────┘                      │
│                     │                                                       │
│                     ▼                                                       │
│   [ ScriptVerificationReport & Gating Verdict ]                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Implementation Method Signatures for `ScriptVerifier`

```python
class ScriptVerifier:
    """Post-script claim extraction and re-verification engine."""

    def __init__(
        self,
        engine: Optional[VerificationEngine] = None,
        graph: Optional[EvidenceGraph] = None,
        strict: bool = True,
        tolerance_exact: float = 0.001,
        tolerance_approx: float = 0.05,
    ): ...

    def extract_sentences(
        self,
        script: Union[Script, Dict[str, Any], str],
    ) -> List[ScriptSentenceExtraction]:
        """Segments script voiceover narration into discrete timestamped sentence objects."""

    def align_sentences_to_graph(
        self,
        extractions: List[ScriptSentenceExtraction],
        graph: EvidenceGraph,
    ) -> List[ScriptClaimMapping]:
        """Aligns extracted script sentences against EvidenceGraph ClaimNodes and EvidenceUnitNodes."""

    def check_drift(
        self,
        mapping: ScriptClaimMapping,
        graph: EvidenceGraph,
    ) -> List[ScriptClaimDriftRecord]:
        """Audits an aligned mapping for strengthened claims, altered numbers, omitted uncertainty, and fabricated quotes."""

    def verify_script(
        self,
        script: Union[Script, Dict[str, Any], str],
        graph: Optional[EvidenceGraph] = None,
        dossier: Optional[ResearchDossier] = None,
        auto_remediate: bool = True,
    ) -> ScriptVerificationReport:
        """End-to-end verification of script, producing ScriptVerificationReport and updating EvidenceGraph."""

    def remediate_script(
        self,
        script: Script,
        drifts: List[ScriptClaimDriftRecord],
    ) -> Script:
        """Generates a corrected Script by applying recommended edits (hedging, number fixes, quote paraphrasing)."""

    def sync_to_evidence_graph(
        self,
        report: ScriptVerificationReport,
        graph: EvidenceGraph,
    ) -> None:
        """Mutatively records ScriptSentenceNode and VerificationTraceNode instances in the EvidenceGraph."""
```

---

## 6. Caveats

1. **No Out-of-Scope Code Edits:**
   - In accordance with the Spec Miner mandate, no production files under `src/` were edited or created during this exploration turn. All findings and contracts are formally specified in this handoff.
2. **LLM Inference vs Heuristic Engine:**
   - The specification provides deterministic algorithmic heuristics (regex, character Levenshtein, modal dictionaries, and dual mathematical tolerance) that execute with 100% determinism in hermetic offline CI environments without requiring live LLM API keys. When live Hermes model providers are active, sentence decomposition and paraphrase generation can be further augmented by LLM prompting, but the heuristic boundaries remain authoritative.
3. **Data Model Compatibility:**
   - `Script` in `src/models/contracts.py` uses Pydantic v2, whereas `Script` in `src/models/script.py` is a dataclass. `ScriptVerifier` must support both by duck-typing attributes (`scenes`, `beats`, `narration_text`).

---

## 7. Conclusion

The specification for `src/epistemic/script_verifier.py` is completely and rigorously defined. It bridges the critical seam between scriptwriting generation and epistemic verification by:
1. Extracting timestamped sentences from script scenes and beats using abbreviation-protected segmentation.
2. Aligning script sentences with the `EvidenceGraph` DAG.
3. Detecting all 4 canonical drift classes:
   - **Strengthened claims** via modal qualification comparison (Level 1/2 vs Level 3) and confidence jumps.
   - **Altered numbers** via SI unit normalization, dual tolerances (0.1% / 5.0%), compound growth verification, and order-of-magnitude mismatch traps.
   - **Omitted uncertainty** via Historical Scholarship Policy consensus state matching (`ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `UNVERIFIED`).
   - **Fabricated quotes** via normalized character Levenshtein distance ($D_{\text{norm}} \le 0.02$) and the strict Paraphrase Mandate.
4. Emitting `ScriptVerificationReport` with typed `ScriptClaimDriftRecord` entries and concrete `recommended_edit` rewrites.
5. Mutating the `EvidenceGraph` with `ScriptSentenceNode` and `VerificationTraceNode` without violating acyclicity, enabling deterministic gating in the 17-state lifecycle machine.

---

## 8. Verification Method

To independently verify the implementation once coded:

1. **Inspect Contract Definitions:**
   - Confirm `ScriptVerificationReport`, `ScriptClaimDriftRecord`, `DriftType`, and `DriftSeverity` are cleanly importable from `src.epistemic.script_verifier`.
2. **Run Unit Tests:**
   ```bash
   pytest tests/unit/test_script_verifier.py -v
   ```
   Must test:
   - Sentence segmentation with abbreviations, numbers, and quotes.
   - Strengthened claim detection (modal level 1 vs 3).
   - Altered number detection (50,000 vs 500,000 order-of-magnitude mismatch).
   - Omitted uncertainty detection on `ACTIVE_DEBATE` and `CONTESTED` consensus claims.
   - Fabricated quote detection and paraphrase mandate rewrite.
   - EvidenceGraph synchronization and acyclicity preservation.
3. **Run Epistemic & Runtime Acceptance Tests:**
   ```bash
   pytest tests/test_evidence_graph.py tests/test_verification_engine.py tests/test_h9_acceptance.py -v
   ```
   Must achieve 100% pass rate with zero regressions.
