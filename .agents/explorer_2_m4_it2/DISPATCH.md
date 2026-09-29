## 2026-09-14T00:49:42Z

You are explorer_2_m4_it2, a teamwork_preview_explorer subagent.
Working directory: g:\Finding-new-code\harness9\.agents\explorer_2_m4_it2

MANDATORY INSTRUCTION: You MUST read the authoritative request at g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work. Do NOT skip this.

Scope Document: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_9\PROJECT.md

CONTEXT:
Milestone 4 (R4) Iteration 1 FAILED due to a Forensic Auditor INTEGRITY VIOLATION, Reviewer 1 REQUEST_CHANGES, and Challenger 2 REQUEST_CHANGES.
You are tasked with technical investigation and architecture design for the remediation of src/epistemic/visual_verifier.py and tests/test_visual_verifier.py.

FULL AUDIT & REVIEWER/CHALLENGER EVIDENCE TO ADDRESS:
1. Forensic Auditor Finding 2 (src/epistemic/visual_verifier.py:733):
   Entity count regex is over-specialized to 11 hardcoded nouns from test_visual_verifier.py, failing on general entity nouns (e.g. "three battalions", "5 vessels"). Generalize regex to support general quantity phrases.
2. Forensic Auditor Finding 3 (src/epistemic/visual_verifier.py:540):
   Comparison panel validator only checks for the exact phrase "lower than" where val_a > val_b. Expand to support inverse relations (val_a < val_b and "higher than") and synonyms ("greater than", "less than", "smaller than", "below", "under", "worse than", "better than").
3. Challenger 2 GAP-1 & Reviewer 2 Finding 4:
   Timeline year extraction regex `r"\b(1\d{3}|20\d{2})\b"` ignores BCE/BC strings ("44 BCE", "500 BCE") and negative years (-44, -500), skipping ancient timeline inverted chronology checks. Must parse BCE/BC years into negative numbers for monotonic chronology checks.
4. Challenger 2 GAP-2:
   verify_visuals audits scenes in isolation; out-of-order scenes across scene boundaries (e.g. Scene 1 in 1995, Scene 2 in 1970) are not checked globally. Add a global cross-scene timeline sequence audit.
5. Challenger 2 GAP-3:
   Polarity lexicon in extract_trend_polarity lacks "crashed", "collapsed", "tanked", "plunged", causing upward charts with voiceover "the market crashed" to pass without flagging CHART_TREND_CONTRADICTION.
6. Challenger 2 GAP-5:
   extract_stated_entity_count misses "dozens" (skipping count checks against 5 visual panels) and requires plural noun suffixes (skipping singular counts like "one breakthrough" vs 5 images).
7. Reviewer 2 Finding 2:
   Dataset ID Fallback: When a scene specifies dataset_id referencing a verified NumericalDataset in datasets but omits redundant raw data_points in scene parameters, points defaults to empty. Fallback to extracting data_points from the referenced dataset.

SCOPE BOUNDARIES:
- Read-only exploration. DO NOT write or edit source code files.
- Maintain progress.md in your working directory with 'Last visited: [timestamp]' for liveness.

DELIVERABLE:
Write a complete 5-part handoff report to g:\Finding-new-code\harness9\.agents\explorer_2_m4_it2\handoff.md with concrete, code-level fix recommendations for Worker.
Notify parent via send_message when done.
