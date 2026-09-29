# BRIEFING — 2026-09-14T01:16:00Z

## Mission
Investigate and design the hard Historical Scholarship Policy for Milestone 3 (R3) in src/epistemic/historical_policy.py.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: g:\Finding-new-code\harness9\.agents\explorer_2_m3
- Original parent: ba190775-5480-43b0-a934-7fd1b7ba9b5b
- Milestone: Milestone 3 (R3) - Epistemic Verification Layer: Historical Scholarship Policy

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly in src/
- Forbidden sole sources: no Tier 9-13 or single web summary can establish historical facts/interpretations
- Enforce 8 consensus states modeling
- Differentiate documented events from causal/scholarly interpretations
- Non-averaging contradiction invariant: forbid arithmetic averaging of contradictory historical figures/claims
- Calibrate script narration language and mandate balanced attribution
- Output analysis to g:\Finding-new-code\harness9\.agents\explorer_2_m3\analysis.md
- Send completion report via send_message to parent (ba190775-5480-43b0-a934-7fd1b7ba9b5b)

## Current Parent
- Conversation ID: ba190775-5480-43b0-a934-7fd1b7ba9b5b
- Updated: 2026-09-14T01:16:00Z

## Investigation State
- **Explored paths**:
  - g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md
  - g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\PROJECT.md
  - g:\Finding-new-code\harness9\docs\epistemic\HISTORICAL_SCHOLARSHIP_POLICY.md
  - g:\Finding-new-code\harness9\docs\epistemic\EPISTEMIC_ARCHITECTURE.md
  - g:\Finding-new-code\harness9\docs\epistemic\CLAIM_VERIFICATION.md
  - g:\Finding-new-code\harness9\docs\epistemic\FACT_CHECKING_SPEC.md
  - g:\Finding-new-code\harness9\docs\epistemic\FACTBENCH.md
  - g:\Finding-new-code\harness9\src\epistemic\graph.py
  - g:\Finding-new-code\harness9\src\models\contracts.py
  - g:\Finding-new-code\harness9\scripts\verify_epistemic_specs.py
- **Key findings**:
  - Historical scholarship cannot use standard binary verification or simple web retrieval scores.
  - Prohibition of sole web sources: Claims of type EVENT_FACT, CAUSAL_INTERPRETATION, or SCHOLARLY_INTERPRETATION backed solely by Tiers 9–13 are rejected with POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE and marked UNSUPPORTED.
  - Minimum evidentiary thresholds: Threshold A (Tier 1/6: Primary Source or Archival Document), Threshold B (Tier 3: Academic Press Book), or Threshold C (Two independent Tier 2: Peer-Reviewed Journals).
  - 8-State Consensus Model: STRONG_CONSENSUS, BROAD_CONSENSUS, MAJORITY_INTERPRETATION, MINORITY_INTERPRETATION, ACTIVE_DEBATE, CONTESTED, UNRESOLVED, INSUFFICIENT_LITERATURE.
  - Event vs. Interpretation: EVENT_FACT (empirical physical occurrence, date/location attested in primary records, affirmative narration) vs CAUSAL_INTERPRETATION / SCHOLARLY_INTERPRETATION (explanatory causal hypotheses, must be attributed to historical inquiry and calibrated to consensus state; never narrated as uncontested empirical fact).
  - Non-Averaging Contradiction Invariant: When sources contradict on numbers, dates, or sequences, arithmetic averaging is prohibited. Contradictions must be linked via CONTRADICTION edges, marked CONTESTED, and narrated with explicit range/dispute and balanced attribution.
  - Concrete class interface: HistoricalPolicyChecker (and alias HistoricalScholarshipPolicyEngine) with complete types, methods, and schemas.
- **Unexplored areas**: None. Ready for complete synthesis and analysis document authoring.

## Key Decisions Made
- Structure src/epistemic/historical_policy.py with HistoricalPolicyChecker class, comprehensive enums, data contracts, and algorithmic validation methods.
- Ensure strict alignment with src/epistemic/graph.py and src/models/contracts.py.

## Artifact Index
- g:\Finding-new-code\harness9\.agents\explorer_2_m3\analysis.md — Comprehensive findings & architecture report for Historical Policy
- g:\Finding-new-code\harness9\.agents\explorer_2_m3\handoff.md — 5-component handoff report
- g:\Finding-new-code\harness9\.agents\explorer_2_m3\progress.md — Liveness heartbeat
- g:\Finding-new-code\harness9\.agents\explorer_2_m3\BRIEFING.md — Situational awareness
- g:\Finding-new-code\harness9\.agents\explorer_2_m3\DISPATCH.md — Received user instructions
