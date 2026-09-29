# Empirical Challenge Plan — Script Re-Verification (M4)

## Objective
Adversarially challenge and stress test `src/epistemic/script_verifier.py` across quote verification edge cases, epistemic drift / confidence escalation, and numerical distortions.

## Target Dimensions & Test Cases

### 1. Quote Verification Edge Cases
- **Test Q1 (Multi-sentence quote segmentation flaw)**: Script contains `"Sentence one. Sentence two."`. Check if sentence segmenter breaks across the period inside the quote, leaving sentence 1 with unmatched opening quote and sentence 2 with unmatched closing quote, causing `extracted_quotes` to be empty and completely bypassing quote verification.
- **Test Q2 (Long quote Levenshtein threshold evasion)**: Test 100+ character quotes where 1-2 words are substituted (e.g. 2 chars in 120 chars -> Levenshtein distance 0.0167 <= 0.02). Does this evade `FABRICATED_QUOTE` detection?
- **Test Q3 (Contraction handling in single-quote contexts)**: Test sentences containing contractions like `don't`, `it's`, `couldn't` within and outside single-quoted citations.
- **Test Q4 (Punctuation and trailing punctuation sensitivity)**: Check exactness when trailing comma or period differs between archival and script quote.
- **Test Q5 (Dialogue verb rewrite in paraphrase mandate)**: Test if non-standard dialogue verbs (e.g. "shouted", "screamed", "insisted") or dialogue without colons get correctly paraphrased.

### 2. Epistemic Drift & Confidence Escalation
- **Test E1 (Epistemic status CONTESTED/UNRESOLVED vs unhedged narration)**: Evidence claim has status `CONTESTED` or `UNRESOLVED`. Verify whether unhedged narration is flagged as `OMITTED_UNCERTAINTY`.
- **Test E2 (Subtle escalation verbs - 'verified', 'confirmed', 'established')**: Narrator uses "has verified" or "confirmed". Does `MODAL_LEVEL_3_TERMS` cover these, or are they categorized as Level 2?
- **Test E3 (CONTRADICTED / UNSUPPORTED claim narration)**: Evidence claim has status `CONTRADICTED` or `UNSUPPORTED`. Does the verifier block or flag script asserting it as fact (at modal level 2)?
- **Test E4 (Low confidence claim at standard modal level 2)**: Evidence claim confidence is 0.30. Script asserts it at modal level 2 ("Event X occurred in 1950"). Is it flagged as strengthened or allowed?

### 3. Numerical Integrity & Alteration Boundaries
- **Test N1 (Negative numbers & sign flips)**: Evidence contains `-15%` or `-20 degrees`. Script asserts `+15%` or `20 degrees`. Does `_extract_numbers_from_text` preserve negative signs or strip them?
- **Test N2 (Extreme magnitude gap > 1.5 log-diff / > 31.6x)**: Evidence has 100. Script says 10,000 (100x alteration, log diff = 2.0). Does the `best_log_diff < 1.5` filter prevent pairing and drop the number from drift detection?
- **Test N3 (Zero handling & growth calculations)**: Growth from 0 to 10M, or 10M to 0. Does compound growth calculate correctly without crashing or skipping?
- **Test N4 (Multi-number sentences with auxiliary counts)**: Sentences with years, casualty counts, and percentages. Does pairing correctly isolate the changed number?
