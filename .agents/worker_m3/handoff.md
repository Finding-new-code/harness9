# Milestone 3 Handoff Report: Verification Strategies, Historical Policy & Verification Engine

**Agent:** `worker_m3`  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\worker_m3`  
**Parent Agent:** `ba190775-5480-43b0-a934-7fd1b7ba9b5b`  
**Handoff Type:** Hard (Task Complete)  
**Date:** 2026-09-13T20:07:00Z  

---

## 1. Observation

1. **Requirements & Scope**:
   - `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md` (lines 227–229) specifies Requirement R3:
     > "Implement modular, explainable verification strategies (`SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK`, `QUOTE_CHECK`, `NUMERICAL_CHECK`, `TEMPORAL_CHECK`, `HISTORIOGRAPHICAL_CHECK`). Enforce claim-type-specific policy dispatch (scientific, numerical, quote, current-event, technical, historical). Implement the hard Historical Scholarship Policy: forbid single-source or popular web summaries from establishing historical facts or interpretations; explicitly model consensus states (`STRONG_CONSENSUS`, `BROAD_CONSENSUS`, `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `INSUFFICIENT_LITERATURE`); differentiate documented events from scholarly/causal interpretations; and calibrate consensus language in script generation without ever averaging contradictions away."
   - Upstream explorer reports:
     - `g:\Finding-new-code\harness9\.agents\explorer_1_m3\analysis.md`: Mathematical specifications for all 7 strategies, assertion strengthening detection, normalized Levenshtein quote bounds, dual tolerances for numbers, and claim-type policy profiles.
     - `g:\Finding-new-code\harness9\.agents\explorer_2_m3\analysis.md`: Complete specification of `HistoricalPolicyChecker`, forbidden sole web sources (Tiers 9–13), Thresholds A/B/C, 8-consensus-state classification algorithm, event vs interpretation differentiation, and non-averaging contradiction invariant.
     - `g:\Finding-new-code\harness9\.agents\explorer_3_m3\analysis.md`: Design of `VerificationEngine`, policy dispatch registry, priority decision ladder for 11 `EpistemicStatus` values, `VerificationTraceNode` DAG insertion, and `verify_dossier`.

2. **Implemented Source Files**:
   - `src/epistemic/historical_policy.py`:
     - `HistoriographicalViolationType` enum (7 violation categories).
     - `HistoricalFraming` model with mandated/forbidden phrases and tone directives.
     - `ContradictionRecord` with `is_resolved_by_averaging = False` invariant.
     - `HistoriographicalEvaluationReport` contract.
     - `HistoricalPolicyChecker` (and alias `HistoricalScholarshipPolicyEngine`) implementing `check_forbidden_sole_source()`, `verify_minimum_source_tiers()`, `classify_consensus_state()`, `validate_event_vs_interpretation()`, `enforce_non_averaging()`, `check_narration_framing()`, `format_balanced_attribution()`, and `evaluate_claim()`.
   - `src/epistemic/strategies.py`:
     - Base `VerificationStrategy` protocol / class and `StrategyExecutionResult`.
     - `SourceEntailmentStrategy`: Entailment probability scaled by 13-tier weights, modal qualifier analysis (Levels 1, 2, 3), flagging `STRENGTHENED_ASSERTION_WARNING` and capping score at 0.70.
     - `CrossSourceCorroborationStrategy`: Multi-source independence calculation $I_{\text{indep}}$, root domain extraction (`ExtractRootDomain`), syndication wire collapse (AP, Reuters, etc.), single-source vulnerability detection (`SINGLE_SOURCE_VULNERABILITY`).
     - `ContradictionCheckStrategy`: Polar negation and numerical variance detection, non-averaging preservation, linking `EdgeRelation.CONTRADICTION`.
     - `QuoteCheckStrategy`: Normalized character Levenshtein distance, exact ($\le 0.02$), ellipses ($\le 0.35$ with ellipsis markers), and distorted ($> 0.02$) with paraphrase mandate and quote fabrication flag.
     - `NumericalCheckStrategy`: Quantity and multiplier parsing, dual tolerance ($\le 0.1\%$ exact, $\le 5.0\%$ approx), order-of-magnitude mismatch trap ($|\Delta \log_{10}| \ge 1.0$) triggering `ORDER_OF_MAGNITUDE_MISMATCH`, and compound growth calculation error detection.
     - `TemporalCheckStrategy`: Causal chronology precedence ($Date(E_1) < Date(E_2)$), historical anachronism scanning (Caesar + telegraph), temporal freshness validation.
     - `HistoriographicalCheckStrategy`: Integrates `HistoricalPolicyChecker`.
   - `src/epistemic/engine.py`:
     - `VerificationResult` and `DossierVerificationReport` models.
     - `STRATEGY_DISPATCH_MAP` mapping 8 `ClaimType`s to required strategies.
     - `VerificationEngine` with strategy registry, dynamic facet augmentation (quotes, numbers, historical context), priority decision ladder across all 11 `EpistemicStatus` values.
     - `verify_claim()`: Executes strategies, creates `VerificationTraceNode` linked via `EdgeRelation.DERIVES_FROM`, links supporting and contradicting evidence, synchronously updates `ClaimRecord` and `ClaimNode`.
     - `verify_dossier()`: Verifies all claims, runs cross-claim contradiction checks, evaluates gate outcomes (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`), and embeds serialized graph into `dossier.evidence_graph`.
   - `src/epistemic/__init__.py`:
     - Re-exported all new public symbols alongside existing graph abstractions.

3. **Test Suites & Verification Results**:
   - `tests/test_historical_policy.py`: 15 comprehensive test cases covering sole web sources, thresholds A/B/C, 8 consensus states, event vs interpretation, non-averaging, calibrated rhetoric, and balanced attribution formatting.
   - `tests/test_verification_engine.py`: 21 comprehensive test cases covering engine initialization, policy dispatch, dynamic facets, all 7 individual strategies, 11-status decision ladder, DAG mutation/acyclicity, and `verify_dossier` gate recommendations.
   - Full test run result:
     `uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -v`
     ```
     ======================= 144 passed in 62.24s (0:01:02) ========================
     ```
   - Spec verification:
     `uv run python scripts/verify_epistemic_specs.py`
     ```
     === Suite 1: Taxonomies Completeness & Mutual Consistency ===
       all_checks_passed: True
     === Suite 2: Decision Function Partition & Boundary Analysis ===
       all_checks_passed: True
     === Suite 3: Mathematical Formulas Boundedness & Limits ===
       all_checks_passed: True
     === Suite 4: Evidence Graph DAG & Edge Directionality ===
       all_checks_passed: True
     === Suite 5: ADR-006 Cross-Document Conformance ===
       all_checks_passed: True
     ```

---

## 2. Logic Chain

1. **Historical Scholarship Invariant**:
   - In automated media generation, web frequency cannot establish historical truth because digital repetition propagates apocryphal myths (e.g. horned Viking helmets, Galileo Leaning Tower).
   - Enforcing the prohibition on sole Tier 9–13 sources ensures all historical claims are anchored in primary archival editions (Tier 1/6) or peer-reviewed scholarly monographs (Tier 3/2).
   - Causal models cannot be narrated as indisputable empirical events; segregating `EVENT_FACT` from `CAUSAL_INTERPRETATION` and requiring hedging prevents dogmatic oversimplification.
   - Conflicting casualty counts or dates (e.g. 20,000 vs 100,000) are mathematically and epistemically invalid to average ($60,000$). The non-averaging invariant preserves discrete accounts as opposing edges in `EvidenceGraph` with `CONTESTED` status and mandates range narration.

2. **Modular Strategy Dispatch**:
   - Rather than relying on generic text embeddings, verification requires specialized structural analysis.
   - Quotations require character-level Levenshtein alignment; numbers require unit normalization and dual tolerance; historical events require historiographical consensus modeling; emerging events require temporal freshness.
   - The dispatch engine routes claims by `ClaimType` and dynamically augments required checks when text contains quotes, metrics, or historical dates.

3. **Deterministic Status Priority Ladder**:
   - Mapping claims across 11 discrete statuses requires a clear, non-overlapping priority hierarchy: Unverifiable $\to$ Opinion $\to$ Prediction $\to$ Historical Policy Violation $\to$ Quote Distortion $\to$ Numerical Incompatibility $\to$ Temporal Obsolete $\to$ Contradicted $\to$ Contested $\to$ Partially Supported (strengthened/hedged) $\to$ Verified $\to$ Supported $\to$ Unsupported.
   - This ensures unambiguous status assignment and reliable lifecycle gating (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`).

4. **DAG Trace Node Invariant & Cycle Safety**:
   - Every verification execution instantiates a `VerificationTraceNode` and establishes a directed edge `claim -> trace` with `EdgeRelation.DERIVES_FROM`.
   - Because trace nodes are terminal sink nodes with no outgoing edges, adding them can never introduce a cycle into `EvidenceGraph`, preserving the strict DAG acyclicity invariant.

---

## 3. Caveats

- **Hermetic / Offline Determinism**: All verification strategies operate in fully deterministic, hermetic offline mode without requiring live external network egress or API keys. In production, `SOURCE_ENTAILMENT` can optionally hook into live LLM embeddings or local transformer NLI models via the Hermes capability bridge (`src/h9_runtime/bridge.py`).
- **Downstream Milestones**: Post-script claim re-extraction (`src/epistemic/script_verifier.py`) and visual fact-checking (`src/epistemic/visual_verifier.py`) belong to Milestone 4, and production lifecycle state machine gate handlers belong to Milestone 5. The engine and strategies implemented here provide the foundational API (`verify_claim`, `verify_dossier`, `HistoricalPolicyChecker`) that those downstream components will consume.

---

## 4. Conclusion

Milestone 3 is complete. The 7 modular verification strategies, the Historical Scholarship Policy engine, the Claim-Type Policy Dispatcher, and the top-level `VerificationEngine` have been fully implemented, integrated, and verified with 100% test pass rate (144/144 tests across all affected test suites, 0 failures, 0 errors, zero regressions).

---

## 5. Verification Method

To independently reproduce and verify this work:

1. **Run Historical Policy & Verification Engine Test Suites**:
   ```bash
   uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py -v
   ```
   *Expected result: 36 passed in ~16s.*

2. **Run Full Regression Suite**:
   ```bash
   uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -v
   ```
   *Expected result: 144 passed in ~62s (0 failures, 0 errors).*

3. **Run Epistemic Specification Checker**:
   ```bash
   uv run python scripts/verify_epistemic_specs.py
   ```
   *Expected result: All 5 suites pass with True.*

4. **Invalidation Conditions**:
   - Any strategy producing scores outside $[0.0, 1.0]$.
   - Any arithmetic averaging of conflicting numbers or dates.
   - Any acceptance of sole Tier 9–13 sources for historical facts or interpretations.
   - Any failure to enforce the paraphrase mandate on distorted quotes.
   - Any cycle created in `EvidenceGraph` by verification trace nodes.
