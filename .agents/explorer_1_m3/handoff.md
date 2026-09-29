# Handoff Report — Explorer 1 (Milestone 3: Verification Strategies & Policy Dispatch)

## 1. Observation
- Inspected `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md` (lines 227–229) establishing Requirement R3:
  > "Implement modular, explainable verification strategies (`SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK`, `QUOTE_CHECK`, `NUMERICAL_CHECK`, `TEMPORAL_CHECK`, `HISTORIOGRAPHICAL_CHECK`). Enforce claim-type-specific policy dispatch (scientific, numerical, quote, current-event, technical, historical). Implement the hard Historical Scholarship Policy: forbid single-source or popular web summaries from establishing historical facts or interpretations; explicitly model consensus states (`STRONG_CONSENSUS`, `BROAD_CONSENSUS`, `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `INSUFFICIENT_LITERATURE`); differentiate documented events from scholarly/causal interpretations; and calibrate consensus language in script generation without ever averaging contradictions away."
- Inspected `src/models/contracts.py` (lines 197–284, 353–420):
  - `EpistemicStatus` enum defines 11 statuses (`verified`, `supported`, `partially_supported`, `contested`, `contradicted`, `unsupported`, `unverifiable`, `outdated`, `misleading`, `opinion`, `prediction`).
  - `SourceTier` enum defines 13 tiers with `DEFAULT_TIER_WEIGHTS` ranging from $1.00$ (`PRIMARY_SOURCE`) to $0.00$ (`UNVERIFIED`).
  - `ConsensusState` enum defines 8 states from `STRONG_CONSENSUS` to `INSUFFICIENT_LITERATURE`.
  - `ClaimType` enum defines 8 claim typologies.
  - `ClaimRecord` model contains fields `epistemic_status`, `consensus_state`, `source_tier`, `source_quality`, `corroboration_set`, `temporal_context`, `verifier_metadata`, `contradicting_sources`, and `evidence_links`.
- Inspected `src/epistemic/graph.py` (lines 1–1179):
  - `EvidenceGraph` DAG implements typed node models (`SourceNode`, `PassageNode`, `EvidenceUnitNode`, `ClaimNode`, `VerificationTraceNode`, `SceneNode`, `ScriptSentenceNode`, `VisualElementNode`) and edge relations (`ENTAILMENT`, `CONTRADICTION`, `CORROBORATION`, `DERIVES_FROM`, `VISUAL_DEPICTION`).
  - Provenance lineage traversal via `trace_lineage()`, acyclicity checking via `would_create_cycle()`, deterministic topological sort via Kahn's algorithm, and multi-path corroboration confidence calculation via `calculate_chain_confidence()`.
- Inspected `docs/epistemic/FACT_CHECKING_SPEC.md` and `docs/epistemic/CLAIM_VERIFICATION.md`:
  - Defined mathematical formulations for $S_{\text{entail}}$, $S_{\text{corrob}}$, $P_{\text{contra}}$, normalized Levenshtein distance for quotes, numerical tolerance intervals, temporal chronology checks, and the status decision function.
- Inspected `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md`:
  - Detailed the prohibition of sole web sources (Tiers 9–13), minimum evidentiary thresholds (Thresholds A, B, C), event vs interpretation boundary, and the Non-Averaging Contradiction Invariant.
- Inspected `scripts/verify_epistemic_specs.py` (lines 76–220):
  - Validated mathematical boundedness of formulas in $[0.0, 1.0]$, Monte Carlo stress test with 100,000 iterations, and deterministic if-elif decision tree.

## 2. Logic Chain
1. **Mathematical & Epistemic Decoupling**: Observation of `FACT_CHECKING_SPEC.md` and `EPISTEMIC_ARCHITECTURE.md` proves that retrieval confidence is fundamentally orthogonal to epistemic truth. High search frequency or domain authority cannot override empirical non-entailment or historical contradiction.
2. **Strategy Modularization**: Each of the 7 strategies targets an independent factual property:
   - `SOURCE_ENTAILMENT`: Evaluates textual support probability scaled by $W_{\text{tier}}$, detecting unearned assertion strengthening ($M(C) > M(P)$).
   - `CROSS_SOURCE_CORROBORATION`: Prevents false consensus by requiring independent root domains and collapsing syndicated news wire feeds.
   - `CONTRADICTION_CHECK`: Detects direct polar negations, numerical variances, and attribution rivalries, preserving conflicting claims as opposing DAG edges without arithmetic averaging.
   - `QUOTE_CHECK`: Enforces normalized Levenshtein distance $\le 0.02$ for exact quotes, mandating paraphrase when verbatim matching fails.
   - `NUMERICAL_CHECK`: Converts quantities to SI base units and tests tolerances ($\le 0.1\%$ exact, $\le 5\%$ approx), flagging order-of-magnitude hallucinations.
   - `TEMPORAL_CHECK`: Validates causal chronology ($Date(E_1) < Date(E_2)$), scans for anachronisms via technology existence intervals, and flags outdated dynamic claims missing temporal anchors.
   - `HISTORIOGRAPHICAL_CHECK`: Blocks historical assertions backed solely by Tiers 9–13, verifies minimum thresholds, classifies literature into 8 consensus states, and distinguishes documented events from causal interpretations.
3. **Claim-Type Policy Dispatch**: Observation of the claim typology matrix indicates that evaluating all claims with identical rules leads to false negatives (e.g. demanding Levenshtein quote matching on a numerical statistic) or false positives (e.g. accepting a single news article for a historical consensus claim). Dispatching claims by `ClaimType` to tailored `PolicyProfile` instances guarantees appropriate rigor.
4. **DAG Trace Invariant**: Every verification run must produce an immutable `VerificationTraceNode` linked to `ClaimNode` via `DERIVES_FROM`, ensuring full auditability.

## 3. Caveats
- **Offline / Hermetic vs Live LLM Mode**: In offline CI/CD mode, NLI semantic entailment is evaluated using deterministic token containment, lexical overlap, polarity heuristics, and modality analysis. When running in live mode with an active Hermes model, the strategies can delegate complex semantic inference to native Hermes model tools or local NLI models while retaining the exact same mathematical scoring framework.
- **External Scholarly APIs**: While scholarly API connectors (Crossref, OpenAlex) exist for live research expansion, all verification tests in CI must execute hermetically against local test fixtures without network calls.

## 4. Conclusion
The 7 verification strategies and the Claim-Type Policy Dispatch Engine have a complete, mathematically grounded, and contract-aligned architecture ready for implementation in Milestone 3 by Worker M3.
The recommended implementation structure divides `src/epistemic/` into modular strategy classes under `src/epistemic/strategies/`, a policy dispatch registry in `src/epistemic/policy.py`, a historical policy checker in `src/epistemic/historical.py`, and the top-level `VerificationEngine` in `src/epistemic/engine.py`. Full implementation blueprints, data contracts, and test case designs are published in `analysis.md`.

## 5. Verification Method
Worker M3's implementation can be independently verified via:
1. **Unit Test Execution**:
   ```bash
   .venv/Scripts/python.exe -m unittest tests/test_verification_engine.py
   .venv/Scripts/python.exe -m unittest tests/test_historical_policy.py
   ```
2. **Regression Verification**:
   ```bash
   .venv/Scripts/python.exe -m unittest tests/test_contracts.py tests/test_evidence_graph.py tests/test_h9_acceptance.py
   ```
3. **Spec Consistency Execution**:
   ```bash
   .venv/Scripts/python.exe scripts/verify_epistemic_specs.py
   ```
4. **Inspection Points**:
   - Confirm `analysis.md` at `g:\Finding-new-code\harness9\.agents\explorer_1_m3\analysis.md`.
   - Invalidation conditions: Any strategy producing scores outside $[0.0, 1.0]$, any arithmetic averaging of contradictory claims, any acceptance of sole Tier 9–13 sources for historical facts, or any failure to enforce the paraphrase mandate on distorted quotes.
