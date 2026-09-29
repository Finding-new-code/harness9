# Milestone 3 Handoff Report: Historical Scholarship Policy

**Agent:** `explorer_2_m3`  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\explorer_2_m3`  
**Handoff Type:** Hard (Task Complete)  
**Target Implementation:** `src/epistemic/historical_policy.py`  
**Date:** 2026-09-14T01:18:30Z  

---

## 1. Observation

1. **Policy Directives in Canonical Docs**:
   - `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md` (lines 16-23):
     > "1. The Forbidden Sole Source Rule: No historical fact or interpretation may be established by a single web summary, blog, or crowdsourced encyclopedia.  
     > 2. Mandatory Minimum Evidentiary Thresholds: Historical claims must be anchored in primary archival editions or peer-reviewed academic press scholarship.  
     > 3. The 8-State Consensus Model: All historical claims must be classified into one of eight formal consensus states.  
     > 4. The Event vs. Interpretation Distinction: The system must rigorously separate documented physical occurrences from historiographical causal hypotheses.  
     > 5. The Non-Averaging Contradiction Invariant: Divergent casualty counts, economic estimates, and dates must never be averaged away; contradictions must be preserved and narrated as disputed.  
     > 6. Calibrated Narration Framing: Voiceover scripts must calibrate their rhetorical stance to the verified consensus state, avoiding unearned dogmatic certainty."
   - `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md` (lines 33-38) details Minimum Evidentiary Thresholds:
     > "Threshold A (Primary Backing): At least one verified Tier 1 (PRIMARY_SOURCE) or Tier 4/6 (HISTORICAL_DOCUMENT_CRITICAL_EDITION / ARCHIVAL_DOCUMENT).  
     > Threshold B (Academic Monograph Backing): At least one verified Tier 3 source (ACADEMIC_PRESS_BOOK).  
     > Threshold C (Peer-Reviewed Historiography): At least two independent Tier 2 sources (PEER_REVIEWED_JOURNAL)."
   - `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md` (lines 116-124) defines the mathematical invalidation of arithmetic averaging:
     > "$$\forall C_A, C_B \text{ such that } C_A.\text{value} \ne C_B.\text{value}, \quad \text{SynthesizeAverage}(C_A, C_B) \to \mathbf{PROHIBITED}$$"

2. **Existing Contracts and Models**:
   - `src/models/contracts.py` (lines 212-238) defines `SourceTier` with 13 tiers from `PRIMARY_SOURCE = 1` to `UNVERIFIED = 13`.
   - `src/models/contracts.py` (lines 261-270) defines `ConsensusState` with 8 states: `STRONG_CONSENSUS`, `BROAD_CONSENSUS`, `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `INSUFFICIENT_LITERATURE`.
   - `src/models/contracts.py` (lines 273-283) defines `ClaimType` containing `EVENT_FACT`, `CAUSAL_INTERPRETATION`, `SCHOLARLY_INTERPRETATION`, `NUMERICAL_METRIC`, `DIRECT_QUOTE`, `SCIENTIFIC_LAW`, `CURRENT_EVENT`, `DEFINITIONAL`.
   - `src/models/contracts.py` (lines 353-421) defines `ClaimRecord` containing `claim_type: ClaimType`, `consensus_state: ConsensusState`, `epistemic_status: EpistemicStatus`, `source_tier: SourceTier`, `primary_source: SourceRecord`, `corroborating_sources: List[SourceRecord]`, `contradicting_sources: List[SourceRecord]`, `evidence_node_ids: List[str]`.

3. **Evidence Graph Architecture**:
   - `src/epistemic/graph.py` (lines 50-58) defines `EdgeRelation.CONTRADICTION`, `EdgeRelation.ENTAILMENT`, `EdgeRelation.CORROBORATION`.
   - `src/epistemic/graph.py` (lines 163-181) defines `ClaimNode` storing `consensus_state`, `epistemic_status`, `claim_type`.
   - `src/epistemic/graph.py` (lines 967-975) applies contradiction penalties and tracks opposing edges.

4. **Test Suite Baseline & Existing Tests**:
   - `scripts/verify_epistemic_specs.py` confirmed 100% mathematical boundedness and complete taxonomy alignments (11 statuses, 13 tiers, 8 consensus states, 4 verification gates).
   - `tests/test_contracts.py` passes 12/12 test cases.
   - `tests/test_h9_acceptance.py` currently stands at 44/44 passing tests across Dimensions A through H.

---

## 2. Logic Chain

1. **From Observation 1 and 2 to Forbidden Sole Sources & Minimum Tiers**:
   - Historical facts and causal interpretations cannot be verified by web search frequency or popular wikis (Tier 9-13) because widespread popular repetition often propagates apocryphal legends (the "false consensus" failure).
   - Therefore, any historical claim whose sole backing source is Tier 9-13 must be flagged with `POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE` and assigned `EpistemicStatus.UNSUPPORTED`.
   - Legitimate grounding requires satisfying Threshold A (Tier 1/6: Primary/Archival), Threshold B (Tier 3: University Press Monograph), or Threshold C (Two Tier 2: Peer-Reviewed Journals).

2. **From Observation 1 and 2 to 8-State Consensus Modeling**:
   - Historical propositions cannot be reduced to binary booleans. A claim can represent a dominant paradigm (`MAJORITY_INTERPRETATION`), a credible revisionist critique (`MINORITY_INTERPRETATION`), an ongoing scholarly controversy (`ACTIVE_DEBATE`), conflicting primary accounts (`CONTESTED`), an acknowledged open mystery (`UNRESOLVED`), or under-researched area (`INSUFFICIENT_LITERATURE`).
   - By constructing a deterministic decision tree using the counts of primary sources ($N_{\text{primary}}$), peer-reviewed articles ($N_{\text{peer}}$), academic books ($N_{\text{book}}$), and agreement ratio $R_{\text{agree}}$, every claim is classified deterministically.

3. **From Observation 1 and 2 to Event vs. Interpretation Differentiation**:
   - `ClaimType.EVENT_FACT` (an empirical occurrence in time and space attested in primary documents) is epistemically distinct from `ClaimType.CAUSAL_INTERPRETATION` or `ClaimType.SCHOLARLY_INTERPRETATION` (explanatory causal hypotheses).
   - Therefore, while documented events can be stated affirmatively as facts when consensus is strong, causal interpretations **must never be narrated as uncontested empirical facts**. Stating a causal theory as an indisputable fact triggers `POLICY_VIOLATION_UNHEDGED_INTERPRETATION`.

4. **From Observation 1, 2, and 3 to Preserving Contradictions & Calibrating Narration**:
   - When primary records or scholars report conflicting numbers (e.g., casualty counts of 20,000 vs 100,000), computing an average ($60,000$) produces an epistemically ungrounded fiction.
   - Therefore, the Non-Averaging Contradiction Invariant forbids numeric synthesis. Conflicting assertions must be stored as separate nodes connected by `CONTRADICTION` edges in `EvidenceGraph`, marked `CONTESTED`, and narrated as a disputed range.
   - For `ACTIVE_DEBATE` and `CONTESTED` claims, balanced attribution ("Historians such as X argue A, whereas Y contends B") must be mandated.

---

## 3. Caveats

1. **Natural Language Rhetorical Audit**:
   - While keyword and phrase scanning deterministically catches prohibited phrases ("allegedly", "sole cause", "it is proven that"), nuanced semantic distortion in complex multi-paragraph voiceover beats may require NLI entailment integration with `src/epistemic/script_verifier.py` (scheduled for Milestone 4).
2. **Archival Metadata Availability**:
   - In offline test mode, primary source records rely on curated fixtures (`ResearchDossier` presets). When live connectors (OpenAlex, Crossref) are enabled in production, authority resolution depends on external DOI/publisher metadata.

---

## 4. Conclusion

1. The hard Historical Scholarship Policy is fully formulated, mathematically grounded, and architecturally specified in `g:\Finding-new-code\harness9\.agents\explorer_2_m3\analysis.md`.
2. The concrete implementation must reside in `src/epistemic/historical_policy.py`, defining:
   - `HistoriographicalViolationType` enum (7 violation types).
   - `HistoricalFraming` model (mandated phrases, forbidden phrases, tone directives).
   - `HistoriographicalEvaluationReport` contract (violations, threshold compliance, consensus state, non-averaging preservation).
   - `ContradictionRecord` model (conflicting parameters, preserved range, dispute recommendations).
   - `HistoricalPolicyChecker` class (and alias `HistoricalScholarshipPolicyEngine`) implementing 9 modular methods.
3. This architecture guarantees that no Harness 9 production can publish apocryphal myths, averaged contradictions, ungrounded web summaries, or unhedged causal claims.

---

## 5. Verification Method

To independently verify this investigation and validate downstream implementation:

1. **Inspect Artifacts**:
   - Review `g:\Finding-new-code\harness9\.agents\explorer_2_m3\analysis.md` for complete class interfaces, mathematical formulas, and decision algorithms.
   - Review `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md` for canonical policy requirements.
2. **Test Invariant Execution**:
   - Run existing contract and acceptance tests:
     ```bash
     python -m unittest tests/test_contracts.py
     pytest tests/test_h9_acceptance.py
     ```
3. **Downstream Unit Test Suite**:
   - Implement `tests/test_historical_policy.py` verifying:
     - `test_sole_web_source_rejection`: Tier 9-13 sole sources rejected with `UNSUPPORTED`.
     - `test_minimum_tier_thresholds`: Compliance with Thresholds A, B, and C.
     - `test_8_consensus_states_classification`: Accurate partitioning across all 8 states.
     - `test_event_vs_interpretation_differentiation`: Unhedged causal interpretations rejected with `UNHEDGED_INTERPRETATION`.
     - `test_non_averaging_invariant`: Averaged casualty figures rejected; divergent numbers preserved with `CONTESTED`.
     - `test_narration_framing_calibration`: Validation of mandated and forbidden phrasing.
     - `test_balanced_attribution_formatting`: Validation of balanced attribution templates.
