## 2026-09-13T16:47:00Z
You are Survey Explorer 3 for the Harness 9 Epistemic Verification Layer project.
Your working directory is: g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_survey_3

MANDATORY FIRST STEP: Read the authoritative request file before starting any work:
g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (specifically entry ## 2026-09-13T16:44:00Z)

Scope & Mission:
Investigate verification strategies, historical scholarship policy, visual/numerical pipelines, and evaluation benchmarks:
1. Inspect existing verification or QA logic across `src/` (e.g. `src/research/`, `src/editorial/`, `src/qa/`, `ContentBench`).
2. Requirements for the Multi-Strategy Verification Engine: analyze how to structure `SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK`, `QUOTE_CHECK`, `NUMERICAL_CHECK`, `TEMPORAL_CHECK`, `HISTORIOGRAPHICAL_CHECK` with policy dispatch.
3. Requirements for Historical Scholarship Policy: forbidding sole/popular web sources, modeling consensus states (`STRONG_CONSENSUS` down to `INSUFFICIENT_LITERATURE`), event vs. interpretation distinction, no averaging contradictions.
4. Requirements for Visual/Numerical integrity: post-script claim extraction and re-verification, visual fact-checking (rendered elements/charts/counts vs narration), deterministic numerical data pipeline from dataset to chart.
5. Requirements for `H9-FactBench` across 9 categories (general, numerical, quotes, scientific, current-event, historical facts, contested historical interpretations, contradictory sources, visual consistency) with offline fixtures + live scholarly API connectors.
6. Inspect `tests/test_h9_acceptance.py` and analyze what `tests/test_epistemic_adversarial.py` needs to test (false consensus, citation laundering, authority spoofing, prompt injection).

Output Requirements:
Write a comprehensive, structured technical handoff report to:
`g:\Finding-new-code\harness9\.agents\teamwork_preview_explorer_survey_3\handoff.md`
Include: Observation, Logic Chain, Engine & Policy Design, FactBench & Adversarial Test Design, Caveats/Risks, and Verification Recommendations.
When finished, message your parent with a concise completion notice and reference to the file.
