# Review Handoff Report — Milestone 4 Part A: Post-Script Claim Re-Verification

**Reviewer**: reviewer_1_m4_gen9  
**Target**: Milestone 4 Part A (`src/epistemic/script_verifier.py`, `tests/test_script_verifier.py`)  
**Worker**: worker_m4_gen9  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1 Test Suite & Regression Execution
Independent test execution was performed directly via `uv run pytest`:
1. **Target Unit Test Suite (`tests/test_script_verifier.py`)**:
   - Command: `uv run pytest tests/test_script_verifier.py -v`
   - Result: 14 passed in 7.15s. Zero failures, zero errors.
2. **Baseline Regression Suite**:
   - Command: `uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -v`
   - Result: 144 passed in 61.74s. Zero regressions across state machine, evidence graph, contracts, runtime bridge, and 8-dimension acceptance suite.

### 1.2 Integrity Violation Audit
- Hardcoded test strings/results: None detected. Sentence segmentation, Levenshtein calculation, modal classification, graph alignment, and DAG synchronization are implemented with genuine algorithmic logic.
- Dummy/Facade implementations: None detected. Real implementations exist for all requested features.
- Verdict on integrity: **PASS** (No integrity violation detected).

### 1.3 Forensic Code Inspection Findings

#### Finding 1: [Critical] Single Quote / Apostrophe Regex Misinterprets Contractions and Possessives as Fabricated Quotes, Falsely Triggering Publication `BLOCK`
- **Location**: `src/epistemic/script_verifier.py`, line 394:
  ```python
  quotes = re.findall(r'["“\']([^"”\']{3,})["”\']', sentence_text)
  ```
- **Observed Behavior**:
  The quote extraction regex includes the single quote/apostrophe character (`'`). In English script narration, contractions and possessives frequently appear (e.g., `"It's clear that the company's product was innovative."`). The regex treats `'s clear that the company'` as a direct quotation.
  When checked against archival evidence in `EvidenceGraph`, the Levenshtein distance exceeds 0.02, triggering a `CRITICAL` severity `FABRICATED_QUOTE` drift, setting `report.passed = False` and `report.gate_recommendation = "BLOCK"`.
- **Reproduction**:
  ```python
  from src.epistemic.script_verifier import ScriptVerifier
  from src.epistemic.graph import EvidenceGraph

  v = ScriptVerifier()
  g = EvidenceGraph(graph_id="g")
  g.add_claim("The company product was innovative in every way.", "c1", claim_type="direct_quote")
  rep = v.verify_script("It's clear that the company's product was innovative.", g)
  assert rep.passed is False
  assert rep.gate_recommendation == "BLOCK"
  assert any(d.drift_type.value == "fabricated_quote" for d in rep.drifts)
  ```
- **Why this is a problem**: Ordinary English scripts with standard punctuation (`it's`, `don't`, `founder's`) are erroneously blocked from publication as fabricated quotes.
- **Suggestion**: Use word-boundary-aware quotation extraction (e.g. require matching double quotes `r'["“]([^"”]{3,})["”]'` or require whitespace/punctuation boundaries for single quotes `r'(?<=\s|^)\'([^\']{3,})\'(?=\s|[.,!?;]|$)'`).

---

#### Finding 2: [Critical] Omitted Modal Escalation Paths (Level 2 -> Level 3 and Level 1 -> Level 2)
- **Location**: `src/epistemic/script_verifier.py`, lines 716–756 (`_check_strengthened_claim`):
  ```python
  if ev_modal == 1 and ext.modal_level == 3:
      ...
  elif claim_node.confidence_score <= 0.70 and ext.modal_level == 3:
      ...
  ```
- **Observed Behavior**:
  The verification specification and checklist mandate modal drift detection across all 3 modal tiers:
  `Level 1 (may/suggests) -> Level 2 (shows/demonstrates) -> Level 3 (proves/undeniably)`.
  However, `_check_strengthened_claim` ONLY detects:
  1. `ev_modal == 1` and `ext.modal_level == 3`, or
  2. `claim_node.confidence_score <= 0.70` and `ext.modal_level == 3`.
  
  It completely ignores:
  - **Level 2 to Level 3 Escalation**: When evidence is Level 2 (e.g., `"Silicon transistors typically exhibit higher thermal stability"`, confidence 0.85) and the script escalates to Level 3 (e.g., `"Silicon transistors undeniably prove higher thermal stability"`), zero drifts are flagged and `report.passed = True`.
  - **Level 1 to Level 2 Escalation**: When evidence is Level 1 (e.g., `"Recent findings suggest a potential link..."`) and the script escalates to Level 2 (e.g., `"Recent findings show the primary link..."`), zero drifts are flagged and `report.passed = True`.
- **Reproduction**:
  ```python
  from src.epistemic.script_verifier import ScriptVerifier
  from src.epistemic.graph import EvidenceGraph
  from src.models.contracts import ClaimRecord, SourceRecord, SourceTier

  g = EvidenceGraph(graph_id="g")
  src = SourceRecord(source_id="s1", title="t", url="u", tier=SourceTier.PRIMARY_SOURCE)
  c = ClaimRecord(claim_id="c1", claim_text="Silicon transistors typically exhibit higher thermal stability.", confidence_score=0.85, primary_source=src)
  g.add_claim(claim_text=c.claim_text, claim_id=c.claim_id, confidence_score=c.confidence_score, claim_record=c)

  v = ScriptVerifier()
  report = v.verify_script("Silicon transistors undeniably prove higher thermal stability.", g)
  assert len(report.drifts) == 0  # Bug: Escalation from Level 2 to Level 3 goes completely undetected!
  assert report.passed is True
  ```
- **Why this is a problem**: Unearned certainty jumps from moderate consensus to absolute proof pass through the epistemic gate undetected.
- **Suggestion**: Update modal comparison to evaluate relative modal order: `if ext.modal_level > ev_modal:`. If escalating to Level 3 from Level 2, raise `STRENGTHENED` with HIGH severity; if escalating to Level 2 from Level 1, raise `STRENGTHENED` with MEDIUM severity.

---

#### Finding 3: [Major] Duplicate Drift Records Generated for Grounded Sentences
- **Location**: `src/epistemic/script_verifier.py`:
  - Lines 560 and 769 (`_check_compound_growth_error` executed at line 560 AND duplicated inside `_check_altered_numbers` at line 769).
  - Lines 564 and 604 (`_check_all_quotes_against_graph` at line 564 AND `_check_fabricated_quotes` at line 604).
- **Observed Behavior**:
  When an extracted sentence is grounded to an evidence claim and contains a compound growth arithmetic error or a fabricated quote, `check_drift()` appends duplicate drift records to `drifts`.
  This doubles the reported drift count in `report.drift_counts_by_type` and `report.drift_counts_by_severity`, and inserts redundant warnings in the `EvidenceGraph` verification traces.
- **Reproduction**:
  ```python
  v = ScriptVerifier()
  q = chr(34)
  script = f"Feynman said: {q}There is barely any room at the bottom.{q}"
  report = v.verify_script(script, sample_graph)
  assert len([d for d in report.drifts if d.drift_type.value == "fabricated_quote"]) == 2  # Duplicate drift!
  ```
- **Why this is a problem**: Distorts telemetry metrics, gate decision counts, and audit logs.
- **Suggestion**: Ensure each check is run exactly once per sentence, or guard `_check_fabricated_quotes` with `if not any(d.drift_type == DriftType.FABRICATED_QUOTE for d in drifts):` and remove the duplicate compound growth block from `_check_altered_numbers`.

---

#### Finding 4: [Major] Substring Lexical Matching Causes False-Positive Modal Classification
- **Location**: `src/epistemic/script_verifier.py`, lines 384, 386, 710, 712:
  ```python
  if any(term in lower for term in MODAL_LEVEL_3_TERMS):
      modal_level = 3
  elif any(term in lower for term in MODAL_LEVEL_1_TERMS):
      modal_level = 1
  ```
- **Observed Behavior**:
  Because terms are checked as raw substrings (`term in lower`) rather than word tokens:
  - `"fact"` is in `MODAL_LEVEL_3_TERMS`. Sentences containing `"factory"`, `"artifact"`, `"manufacture"`, `"satisfaction"`, or `"factor"` are classified as `modal_level = 3`.
  - `"may"` is in `MODAL_LEVEL_1_TERMS`. Sentences containing the month `"May"`, `"mayor"`, `"mayhem"`, or `"dismay"` are classified as `modal_level = 1`.
  - In `HISTORICAL_UNCERTAINTY_HEDGES`, `"debate"` as a substring allows sentences mentioning `"debate"` (e.g. `"The debate on TV showed that..."`) to falsely pass uncertainty hedging checks on `ACTIVE_DEBATE` claims.
- **Reproduction**:
  ```python
  v = ScriptVerifier()
  exts = v.extract_sentences("The factory produced new goods in May 1945.")
  assert exts[0].modal_level == 3  # "factory" matched "fact", falsely forcing Level 3
  ```
- **Why this is a problem**: Falsely elevates or degrades modal levels on benign vocabulary, triggering spurious `STRENGTHENED` drifts and publication blocks.
- **Suggestion**: Use word boundaries `\b` for term matching: `any(re.search(rf"\b{re.escape(term)}\b", lower) for term in TERMS)`.

---

#### Finding 5: [Major] Naive Number Matching Forces Any Additional Count into a 10x Order-of-Magnitude Distortion
- **Location**: `src/epistemic/script_verifier.py`, lines 804–841 (`_check_altered_numbers`):
  ```python
  for s_val, s_tok, is_approx in ext.extracted_numbers:
      best_ev = None
      best_err = float("inf")
      for e_val, e_tok, _ in ev_numbers:
          err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)
          if err < best_err: ...
  ```
- **Observed Behavior**:
  The algorithm iterates over *every* extracted number in the script sentence and pairs it with the closest evidence number. If a script sentence mentions an auxiliary count (e.g. `"In 1948, 3 engineers at Bell Labs produced 4,980 prototype units"`), the number `3` is paired with the year `1948`, flagged as an order-of-magnitude 10x trap (critical severity), and rewritten to replace `"3 "` with `"1948"`, producing corrupted narration: `"In 1948, 1948engineers at Bell Labs produced 4,980 prototype units."` and BLOCKING the script.
- **Why this is a problem**: Scripts with descriptive context (e.g. "3 scientists", "chapter 2", "5 hours") cannot be verified without triggering false numerical distortion errors.
- **Suggestion**: Match numbers contextually or only pair numbers of similar order/units; do not flag unmatched auxiliary counts as 10x mutations unless they represent the primary quantity asserted by the claim. Also ensure token replacement matches exact word boundaries (`\b`) to avoid merging numbers with adjacent words.

---

#### Finding 6: [Minor] Missing `ScriptSentenceSegmenter` Class Abstraction
- **Location**: `src/epistemic/script_verifier.py`, `src/epistemic/__init__.py`.
- **Observed Behavior**:
  Both the worker handoff report and the dispatch checklist specify `ScriptSentenceSegmenter`. In the codebase, segmentation is implemented as private/instance methods on `ScriptVerifier` (`segment_sentences`, `extract_sentences`). There is no class or alias named `ScriptSentenceSegmenter`.
- **Suggestion**: Expose `ScriptSentenceSegmenter = ScriptVerifier` or extract a dedicated segmenter class to satisfy interface expectations and re-export it in `src/epistemic/__init__.py`.

---

#### Finding 7: [Minor] Inflexible Regex Phrasing for Compound Growth Calculations
- **Location**: `src/epistemic/script_verifier.py`, line 614:
  ```python
  growth_match = re.search(
      r'grew\s+from\s+(\d+(?:\.\d+)?)\s*(?:million|billion|k|m|b)?\s+to\s+(\d+(?:\.\d+)?)\s*(?:million|billion|k|m|b)?,\s*a\s+(\d+(?:\.\d+)?)%\s*(?:increase|growth)',
      ext.sentence_text,
      re.IGNORECASE
  )
  ```
- **Observed Behavior**:
  The regex is brittle: it requires `, a X% increase`. Phrasings such as `"increased from 10 to 30, an increase of 300%"` or `"rose from 10 to 30 (a 300% increase)"` are not matched, allowing compound calculation errors to escape check.
- **Suggestion**: Generalize the regex to accept `"an increase of"`, `"up X%"`, and alternate verbs (`increased`, `rose`, `surged`).

---

## 2. Logic Chain

1. **Test Conformance Verification**:
   - The test suite `tests/test_script_verifier.py` (14 tests) and baseline regression suite (144 tests) were executed and passed cleanly.
   - However, the tests in `test_script_verifier.py` used loose assertions (e.g., `assert any(...)`, `assert len(quote_drifts) >= 1`), masking underlying defects like duplicate drift creation.

2. **Adversarial Analysis of Quote Detection**:
   - Examining line 394: `re.findall(r'["“\']([^"”\']{3,})["”\']', sentence_text)`.
   - The inclusion of `'` means any two apostrophes in a sentence (e.g., `"It's ... company's"`) are parsed as a quoted span.
   - Because this non-quote text is checked against evidence quotes, Levenshtein distance is high, generating a CRITICAL fabricated quote drift and a BLOCK gate recommendation. This makes the verifier unusable on normal prose.

3. **Adversarial Analysis of Modal Escalation**:
   - The specification requires detecting: Level 1 -> Level 2 -> Level 3 escalation.
   - Inspecting line 716 reveals that only `ev_modal == 1 and ext.modal_level == 3` is checked.
   - Escalations from Level 2 to Level 3 (and Level 1 to Level 2) are completely omitted when confidence > 0.70, directly violating the review checklist.

4. **Adversarial Analysis of Lexical Markers**:
   - `term in lower` checks substrings without `\b`.
   - Common words ("factory", "artifact", "May") pollute modal classification, causing false-positive drifts.

5. **Adversarial Analysis of Numerical Checking**:
   - Forcing every number in a sentence to match the nearest evidence number causes auxiliary counts ("3 engineers") to be flagged as 10x distortions against years ("1948"), corrupting script remediation ("1948engineers").

6. **Synthesis**:
   - Although the structural architecture and baseline tests are sound, the presence of two Critical findings (Finding 1 breaking on contractions/possessives; Finding 2 missing Level 2 -> Level 3 modal escalation) and three Major findings (duplicate drifts, false-positive substring matching, naive number pairing) impairs the reliability and robustness of the epistemic verification gate.
   - Therefore, changes are required before approval.

---

## 3. Caveats

- The worker implemented a large volume of code across M4 Part A, Part B, and Part C. Part B (`visual_verifier.py`) and Part C (`numerical_pipeline.py`) were not within the scope of this review (which was dedicated to Part A and its test suite), but baseline regression tests across the entire repository remained green.
- The 14 existing unit tests in `tests/test_script_verifier.py` pass cleanly; the defects identified above were revealed through adversarial stress-testing and boundary probing.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

Milestone 4 Part A demonstrates high architectural alignment with the project specifications, clean DAG synchronization, and zero baseline regressions. However, adversarial review revealed critical functional flaws:
1. **Critical**: Single quotes in contractions/possessives (`it's`, `company's`) trigger false-positive `FABRICATED_QUOTE` drifts and inappropriately BLOCK publication.
2. **Critical**: Modal escalation from Level 2 to Level 3 and Level 1 to Level 2 is unhandled and passes through the verifier undetected.
3. **Major**: Duplicate drift records are generated on grounded sentences containing math errors or quotes.
4. **Major**: Substring checking without word boundaries causes false modal level classifications on everyday words (`factory`, `May`).
5. **Major**: Naive number matching forces auxiliary descriptive numbers into false 10x order-of-magnitude violations.

These issues must be remediated to ensure robust post-script claim re-verification.

---

## 5. Verification Method

To verify these findings:
1. Run the test suite:
   ```bash
   uv run pytest tests/test_script_verifier.py -v
   ```
2. Run the adversarial reproduction script:
   ```bash
   uv run python -c "
   from src.epistemic.script_verifier import ScriptVerifier
   from src.epistemic.graph import EvidenceGraph
   from src.models.contracts import ClaimRecord, SourceRecord, SourceTier

   v = ScriptVerifier()
   g = EvidenceGraph(graph_id='g')
   src = SourceRecord(source_id='s1', title='t', url='u', tier=SourceTier.PRIMARY_SOURCE)
   c = ClaimRecord(claim_id='c1', claim_text='Silicon transistors typically exhibit higher thermal stability.', confidence_score=0.85, primary_source=src)
   g.add_claim(claim_text=c.claim_text, claim_id=c.claim_id, confidence_score=c.confidence_score, claim_record=c)

   # Test 1: Contraction false-positive quote block
   r1 = v.verify_script(\"It's clear that the company's product was innovative.\", g)
   print('Test 1 (Contractions):', r1.gate_recommendation, [d.drift_type for d in r1.drifts])

   # Test 2: Level 2 -> Level 3 missed escalation
   r2 = v.verify_script('Silicon transistors undeniably prove higher thermal stability.', g)
   print('Test 2 (Modal Escalation):', r2.gate_recommendation, [d.drift_type for d in r2.drifts])

   # Test 3: Substring 'factory' -> 'fact' false Level 3
   exts = v.extract_sentences('The factory opened in June.')
   print('Test 3 (Modal Level of factory):', exts[0].modal_level)
   "
   ```
   **Expected Output Demonstrating Defects**:
   - Test 1 outputs `BLOCK` with `fabricated_quote`.
   - Test 2 outputs `PASS` with `[]` drifts (undetected escalation).
   - Test 3 outputs `3` instead of `2`.
