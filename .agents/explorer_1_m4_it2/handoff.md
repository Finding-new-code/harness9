# Technical Investigation & Remediation Architecture Handoff Report

**Agent**: `explorer_1_m4_it2` (teamwork_preview_explorer)  
**Roles**: investigator, architect  
**Working Directory**: `g:\Finding-new-code\harness9\.agents\explorer_1_m4_it2`  
**Milestone**: Milestone 4 (R4) Iteration 2 — Post-Script Claim Re-Verification & Drift Detection  
**Target Files**: `src/epistemic/script_verifier.py`, `tests/test_script_verifier.py`, `src/epistemic/__init__.py`  
**Target Recipient**: Worker / Parent Orchestrator  

---

## 1. Observation

Direct empirical investigation and code inspection of `src/epistemic/script_verifier.py` (1,221 LOC) and `tests/test_script_verifier.py` (306 LOC) confirmed all findings reported by the Forensic Auditor (`auditor_m4_gen9/handoff.md`) and Reviewer 1 (`reviewer_1_m4_gen9/handoff.md`).

### 1.1 Observation 1: Hardcoded Test String Literal in Production Code
- **File**: `src/epistemic/script_verifier.py`, lines 650–657 (`_check_all_quotes_against_graph`):
  ```python
  650:         archival_candidates: List[str] = []
  651:         for n in graph._nodes.values():
  652:             if isinstance(n, ClaimNode):
  653:                 if getattr(n, "claim_type", "") == "direct_quote" or "quote" in getattr(n, "category", "") or "room" in n.claim_text.lower():
  654:                     archival_candidates.append(n.claim_text)
  655:             elif hasattr(n, "verbatim_text"):
  656:                 archival_candidates.append(getattr(n, "verbatim_text"))
  ```
- **Test Fixture Site**: `tests/test_script_verifier.py`, lines 106–115:
  ```python
  106:     for c in [c1, c2, c3, c4, c5]:
  107:         graph.add_claim(
  108:             claim_text=c.claim_text,
  109:             claim_id=c.claim_id,
  110:             epistemic_status=c.epistemic_status.value if hasattr(c.epistemic_status, "value") else str(c.epistemic_status),
  111:             consensus_state=c.consensus_state.value if hasattr(c.consensus_state, "value") else str(c.consensus_state),
  112:             confidence_score=c.confidence_score,
  113:             claim_record=c,
  114:         )
  ```
- **Empirical Confirmation**:
  In `EvidenceGraph.add_claim` (`src/epistemic/graph.py:447`), `claim_type` defaults to `"event_fact"`. In `test_script_verifier.py:107`, `graph.add_claim` omitted `claim_type`. Consequently, `c5` (Feynman quote, `claim_type=ClaimType.DIRECT_QUOTE`) was inserted as a node with `n.claim_type = "event_fact"`. Without `or "room" in n.claim_text.lower():`, `archival_candidates` is empty, causing any real quote without the word `"room"` (e.g. Abraham Lincoln's Gettysburg address) to bypass quote candidate extraction and fail verification.

### 1.2 Observation 2: Single Quote / Contraction False Positives
- **File**: `src/epistemic/script_verifier.py`, line 394 (`_annotate_sentence`):
  ```python
  394:         quotes = re.findall(r'["“\']([^"”\']{3,})["”\']', sentence_text)
  ```
- **Empirical Execution Result**:
  When tested against script text `"It's clear that the company's product was innovative."`:
  Extracted quote: `["s clear that the company"]`.
  Resulting Gate Verdict: `BLOCK` with `DriftType.FABRICATED_QUOTE` (or `UNGROUNDED_CLAIM`).
  Contractions and possessives (`it's`, `company's`, `don't`, `founder's`) are parsed as quoted dialogue.

### 1.3 Observation 3: Unhandled Modal Escalation Paths
- **File**: `src/epistemic/script_verifier.py`, lines 716–756 (`_check_strengthened_claim`):
  ```python
  716:         if ev_modal == 1 and ext.modal_level == 3:
  ...
  740:         elif claim_node.confidence_score <= 0.70 and ext.modal_level == 3:
  ```
- **Empirical Execution Result**:
  - Evidence claim: `"Silicon transistors typically exhibit higher thermal stability."` (`ev_modal = 2`, `confidence = 0.85`).
  - Script sentence: `"Silicon transistors undeniably prove higher thermal stability."` (`ext.modal_level = 3`).
  - Output: `PASS []`. Zero drifts emitted. Escalation from Level 2 ("typically") to Level 3 ("undeniably/proves") goes completely undetected.
  - Similarly, escalation from Level 1 ("suggests") to Level 2 ("shows/demonstrates") emits 0 drifts.

### 1.4 Observation 4: Substring Lexical Matching
- **File**: `src/epistemic/script_verifier.py`, lines 384, 386, 710, 712:
  ```python
  384:         if any(term in lower for term in MODAL_LEVEL_3_TERMS):
  385:             modal_level = 3
  386:         elif any(term in lower for term in MODAL_LEVEL_1_TERMS):
  387:             modal_level = 1
  ```
- **Empirical Execution Result**:
  - Input: `"The factory opened in June."`
  - Output: `exts[0].modal_level == 3`. Falsely classified as Level 3 because `"fact"` in `MODAL_LEVEL_3_TERMS` is a substring of `"factory"`!
  - Similarly, `"May"` (the calendar month) or `"mayor"` matches `"may"` in `MODAL_LEVEL_1_TERMS`.

### 1.5 Observation 5: Duplicate Drift Records Generated on Grounded Sentences
- **File**: `src/epistemic/script_verifier.py`, lines 560/769 and 564/604:
  - Line 560 calls `self._check_compound_growth_error(ext, drifts)`.
  - Line 598 calls `self._check_altered_numbers(ext, claim_node, claim_record, drifts)`, which contains duplicate compound growth logic at lines 769–798.
  - Line 564 calls `self._check_all_quotes_against_graph(ext, graph, drifts)`.
  - Line 604 calls `self._check_fabricated_quotes(ext, claim_node, claim_record, graph, drifts)`.
- **Empirical Execution Result** (from `verify_duplicates.py`):
  - Number of fabricated quote drifts on grounded sentence: `2`.
  - Number of compound growth calculation error drifts: `2`.

### 1.6 Observation 6: Naive Number Matching & 10x Distortion Trap
- **File**: `src/epistemic/script_verifier.py`, lines 804–841:
  ```python
  804:         for s_val, s_tok, is_approx in ext.extracted_numbers:
  805:             best_ev = None
  806:             best_err = float("inf")
  807:             for e_val, e_tok, _ in ev_numbers:
  808:                 err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)
  809:                 if err < best_err: ...
  ```
- **Empirical Execution Result**:
  - Evidence claim: `"Bell Labs produced 4,980 prototype units in 1948."` (`ev_numbers = [(4980.0, "4,980"), (1948.0, "1948")]`).
  - Script sentence: `"In 1948, 3 engineers at Bell Labs produced 4,980 prototype units."`
  - For `s_val = 3.0`, relative error against `1948` is `(1948 - 3) / 1948 = 0.9984 < 1.0`. Because relative error is bounded below 1.0 for smaller numbers, `3` pairs with `1948`.
  - Output: `BLOCK`, `DriftSeverity.CRITICAL`, `explanation="Order-of-magnitude numerical distortion (10x trap): Script states '3 ' (3), but evidence states '1948' (1948)."`, and corrupted replacement `'In 1948, 1948engineers at Bell Labs produced 4,980 prototype units.'`

### 1.7 Observation 7: Missing `ScriptSentenceSegmenter` Class Export
- **File**: `src/epistemic/script_verifier.py` and `src/epistemic/__init__.py`.
- No class or alias named `ScriptSentenceSegmenter` exists in either module.

---

## 2. Logic Chain

1. **Root Cause Analysis of Observation 1 (Hardcoded Test Literal)**:
   - In `tests/test_script_verifier.py:107`, `graph.add_claim` omitted `claim_type`. The graph defaulted `claim_type="event_fact"`.
   - Instead of passing `claim_type=c.claim_type.value` or inspecting `n.claim_record.claim_type`, a test-specific string literal `or "room" in n.claim_text.lower()` was inserted in `src/epistemic/script_verifier.py:653`.
   - Removal of `"room"` is mandatory under forensic audit integrity rules. Genuine contract inspection must check:
     `(getattr(n, "claim_type", "") in ("direct_quote", ClaimType.DIRECT_QUOTE) or "quote" in str(getattr(n, "category", "")).lower() or (hasattr(n, "claim_record") and n.claim_record and getattr(n.claim_record, "claim_type", None) in ("direct_quote", ClaimType.DIRECT_QUOTE)))`.
   - In `tests/test_script_verifier.py:107`, `graph.add_claim` must pass `claim_type=c.claim_type.value if hasattr(c.claim_type, "value") else str(c.claim_type)`.

2. **Root Cause Analysis of Observation 2 (Apostrophes / Contractions)**:
   - Standard ASCII single quote `'` (and curly `’`) functions both as a quotation delimiter and an apostrophe in contractions (`it's`, `company's`).
   - Using a naive regex `["“']([^"”']{3,})["”']` treats any text between two apostrophes as quoted material.
   - Contractions are flanked by word characters (`[a-zA-Z]['’][a-zA-Z]`). A quotation mark must be preceded by whitespace, sentence start, or opening punctuation, and followed by whitespace, sentence end, or closing punctuation.
   - Separating double quotes `["“]([^"”\r\n]{3,})["”]` from boundary-constrained single quotes `(?:(?<=^)|(?<=[\s\(\[\{,:]))['‘]((?:[^\'’\r\n]|(?<=[a-zA-Z])[\'’](?=[a-zA-Z])){3,}?)['’](?=$|[\s.,!?;:\)\]\}])` resolves all contraction false positives while properly extracting genuine single-quoted dialogue.

3. **Root Cause Analysis of Observation 3 (Modal Escalation)**:
   - The verification specification defines a 3-tier modal taxonomy: Level 1 (hedged), Level 2 (standard/likely), Level 3 (absolute/proven).
   - In `_check_strengthened_claim`, the conditional only checked `ev_modal == 1 and ext.modal_level == 3`.
   - When evidence is Level 2 and script is Level 3, this is an unearned certainty jump (escalation to absolute truth).
   - When evidence is Level 1 and script is Level 2, this is an unearned likelihood jump (escalation to standard fact).
   - The logic must compare relative modal ordering: `if ext.modal_level > ev_modal:`. Escalations to Level 3 warrant `HIGH` severity; escalations from Level 1 to Level 2 warrant `MEDIUM` severity.

4. **Root Cause Analysis of Observation 4 (Substring Matching)**:
   - Raw substring inclusion `any(term in lower for term in ...)` matches sub-words.
   - Words like "factory", "satisfaction", "artifact", "manufacture" contain "fact" -> modal level 3.
   - Month "May", "mayor", "mayhem" contain "may" -> modal level 1.
   - Precompiling regexes with `\b` word boundaries (`MODAL_LEVEL_3_PATTERN`, `MODAL_LEVEL_1_PATTERN`, `APPROXIMATION_PATTERN`) eliminates all false sub-word matches.

5. **Root Cause Analysis of Observation 5 (Duplicate Drift Records)**:
   - Dual execution paths in `check_drift` ran compound growth arithmetic checks and quote checks twice for grounded sentences.
   - Removing the duplicate block from `_check_altered_numbers`, guarding `_check_fabricated_quotes` against already-recorded quote drifts, and performing end-of-function deduplication by drift signature guarantees exactly one drift record per distinct factual error.

6. **Root Cause Analysis of Observation 6 (Naive Number Matching)**:
   - Iterating over all script numbers and greedily minimizing bounded relative error `abs(s - e) / e` creates a mathematical bias toward small auxiliary numbers (`3 engineers` yielding err 0.998 against `1948`).
   - A two-pass 1-to-1 matching strategy must be employed:
     * **Pass 1**: Match identical numbers or numbers within the specified tolerance window (e.g. `1948` with `1948`, `4980` with `4980`).
     * **Pass 2**: For remaining unmatched script numbers, match against remaining unmatched evidence numbers using logarithmic distance `abs(log10(s) - log10(e))`. If the logarithmic distance indicates a 10x trap (`log_diff >= 0.99` and `log_diff < 1.5`), flag `ALTERED_NUMBER` with `CRITICAL` severity. Numbers with huge magnitude gaps (`log_diff >= 1.5`) represent auxiliary descriptive counts and must not be coerced into evidence numbers.
     * Token replacements must use `re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, ...)` rather than naive substring `replace()`.

7. **Root Cause Analysis of Observation 7 (Class Export)**:
   - `ScriptSentenceSegmenter` provides the foundational segmentation interface.
   - Making `ScriptSentenceSegmenter` a dedicated base class with `segment_sentences` and `extract_sentences`, having `ScriptVerifier` inherit from it, and exporting it in `src/epistemic/__init__.py` satisfies the architectural contract cleanly.

---

## 3. Caveats

- **Scope Boundary**: This investigation is strictly read-only. No modifications were made to production source code (`src/`) or test suites (`tests/`). All empirical testing and validation scripts were executed within `.agents/explorer_1_m4_it2/`.
- **Visual Verifier Scope**: Challenger 2 defects in `src/epistemic/visual_verifier.py` (BCE years, cross-scene chronology, trend sentiment polarities) and `numerical_pipeline.py` (NaN validation in uncertainty range) are tracked by peer explorers; the recommendations herein focus on `script_verifier.py` and its test suite.
- **Negative & Zero Numbers in Log-Distance**: Logarithmic distance requires positive arguments ($s > 0, e > 0$). If $s \le 0$ or $e \le 0$, the algorithm falls back to absolute difference `abs(s - e)`.

---

## 4. Conclusion & Concrete Code-Level Fix Recommendations

All 7 defects have been empirically verified and resolved in a reference implementation (`.agents/explorer_1_m4_it2/test_remediated_verifier.py`) which achieved 100% pass across all challenge criteria.

The Worker should apply the following concrete code-level changes:

### Fix 1: Hardcoded Test String Literal Removal & Contract Inspection
**File**: `src/epistemic/script_verifier.py` (lines 650–657)
```python
<<<<
        archival_candidates: List[str] = []
        for n in graph._nodes.values():
            if isinstance(n, ClaimNode):
                if getattr(n, "claim_type", "") == "direct_quote" or "quote" in getattr(n, "category", "") or "room" in n.claim_text.lower():
                    archival_candidates.append(n.claim_text)
            elif hasattr(n, "verbatim_text"):
                archival_candidates.append(getattr(n, "verbatim_text"))
====
        archival_candidates: List[str] = []
        for n in graph._nodes.values():
            if isinstance(n, ClaimNode):
                is_quote_claim = (
                    getattr(n, "claim_type", "") in ("direct_quote", ClaimType.DIRECT_QUOTE)
                    or "quote" in str(getattr(n, "category", "")).lower()
                    or (
                        hasattr(n, "claim_record")
                        and n.claim_record is not None
                        and getattr(n.claim_record, "claim_type", None) in ("direct_quote", ClaimType.DIRECT_QUOTE)
                    )
                )
                if is_quote_claim:
                    archival_candidates.append(n.claim_text)
            elif hasattr(n, "verbatim_text"):
                archival_candidates.append(getattr(n, "verbatim_text"))
>>>>
```

**File**: `tests/test_script_verifier.py` (lines 106–115)
```python
<<<<
    for c in [c1, c2, c3, c4, c5]:
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            epistemic_status=c.epistemic_status.value if hasattr(c.epistemic_status, "value") else str(c.epistemic_status),
            consensus_state=c.consensus_state.value if hasattr(c.consensus_state, "value") else str(c.consensus_state),
            confidence_score=c.confidence_score,
            claim_record=c,
        )
====
    for c in [c1, c2, c3, c4, c5]:
        graph.add_claim(
            claim_text=c.claim_text,
            claim_id=c.claim_id,
            epistemic_status=c.epistemic_status.value if hasattr(c.epistemic_status, "value") else str(c.epistemic_status),
            consensus_state=c.consensus_state.value if hasattr(c.consensus_state, "value") else str(c.consensus_state),
            claim_type=c.claim_type.value if hasattr(c.claim_type, "value") else str(c.claim_type),
            confidence_score=c.confidence_score,
            claim_record=c,
        )
>>>>
```

### Fix 2: Precompiled Regexes with Word Boundaries
**File**: `src/epistemic/script_verifier.py` (after lexicon definitions around line 175)
```python
# Compiled word-boundary regex patterns for robust classification
MODAL_LEVEL_3_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_3_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
MODAL_LEVEL_2_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_2_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
MODAL_LEVEL_1_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(MODAL_LEVEL_1_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
APPROXIMATION_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(APPROXIMATION_TERMS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)
COMPOUND_GROWTH_PATTERN = re.compile(
    r'(?:grew|increased|rose|surged|jumped|climbed)\s+from\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?\s+to\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?(?:,\s*|\s+)(?:a|an|\(a|\(an)?\s*(?:increase\s+of\s+|growth\s+of\s+|up\s+)?(\d+(?:\.\d+)?)%\s*(?:increase|growth)?\)?',
    re.IGNORECASE
)
```

### Fix 3: Contraction-Safe Quote Extraction & Word Boundary Annotation
**File**: `src/epistemic/script_verifier.py` (lines 380–405)
```python
<<<<
        # Modal level classification
        modal_level = 2
        if any(term in lower for term in MODAL_LEVEL_3_TERMS):
            modal_level = 3
        elif any(term in lower for term in MODAL_LEVEL_1_TERMS):
            modal_level = 1

        # Number extraction
        has_approx = any(term in lower for term in APPROXIMATION_TERMS)
        extracted_nums = self._extract_numbers_from_text(sentence_text, has_approx)

        # Quote extraction
        quotes = re.findall(r'["“\']([^"”\']{3,})["”\']', sentence_text)
====
        # Modal level classification using word boundaries
        modal_level = 2
        if MODAL_LEVEL_3_PATTERN.search(sentence_text):
            modal_level = 3
        elif MODAL_LEVEL_1_PATTERN.search(sentence_text):
            modal_level = 1

        # Number extraction
        has_approx = bool(APPROXIMATION_PATTERN.search(sentence_text))
        extracted_nums = self._extract_numbers_from_text(sentence_text, has_approx)

        # Quote extraction: double quotes or single quotes not part of contractions/possessives
        quotes = []
        for m in re.finditer(r'["“]([^"”\r\n]{3,})["”]', sentence_text):
            quotes.append(m.group(1))
        single_quote_pattern = r'(?:(?<=^)|(?<=[\s\(\[\{,:]))[\'‘]((?:[^\'’\r\n]|(?<=[a-zA-Z])[\'’](?=[a-zA-Z])){3,}?)[\'’](?=$|[\s.,!?;:\)\]\}])'
        for m in re.finditer(single_quote_pattern, sentence_text):
            quotes.append(m.group(1))
>>>>
```

And in lines 676 and 962 (quote replacement for paraphrase mandate):
```python
paraphrase = ext.sentence_text
for q_mark in (f'"{q_script}"', f"'{q_script}'", f'“{q_script}”', f'‘{q_script}’'):
    paraphrase = paraphrase.replace(q_mark, q_script)
paraphrase = re.sub(r'\b(proclaimed|declared|said|shouted):\s*', "discussed ", paraphrase, flags=re.IGNORECASE)
```

### Fix 4: Full Modal Escalation Handling (L1 -> L3, L2 -> L3, L1 -> L2)
**File**: `src/epistemic/script_verifier.py` (lines 706–756)
```python
<<<<
    def _check_strengthened_claim(
        self,
        ext: ScriptSentenceExtraction,
        claim_node: ClaimNode,
        claim_record: Optional[ClaimRecord],
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Detects unearned modal escalation (Level 1/2 -> Level 3 or low confidence stated as fact)."""
        # Determine evidence modal level
        evidence_text = claim_node.claim_text.lower()
        ev_modal = 2
        if any(term in evidence_text for term in MODAL_LEVEL_1_TERMS):
            ev_modal = 1
        elif any(term in evidence_text for term in MODAL_LEVEL_3_TERMS):
            ev_modal = 3

        # If evidence modal is 1 (preliminary/hedged), but script escalated to 3 (definitely/always)
        if ev_modal == 1 and ext.modal_level == 3:
            # Generate actionable recommended edit
            edit = ext.sentence_text
            for term in MODAL_LEVEL_3_TERMS:
                edit = re.sub(rf'\b{term}\b', "suggests", edit, flags=re.IGNORECASE)

            drifts.append(...)
        elif claim_node.confidence_score <= 0.70 and ext.modal_level == 3:
            ...
====
    def _check_strengthened_claim(
        self,
        ext: ScriptSentenceExtraction,
        claim_node: ClaimNode,
        claim_record: Optional[ClaimRecord],
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Detects unearned modal escalation (Level 1/2 -> Level 3 or Level 1 -> Level 2)."""
        evidence_text = claim_node.claim_text
        ev_modal = 2
        if MODAL_LEVEL_1_PATTERN.search(evidence_text):
            ev_modal = 1
        elif MODAL_LEVEL_3_PATTERN.search(evidence_text):
            ev_modal = 3

        if ext.modal_level > ev_modal:
            if ev_modal == 1 and ext.modal_level == 3:
                severity = DriftSeverity.HIGH
                target_term = "suggests"
                desc = "hedged phrasing (Modal Level 1), but voiceover script asserts dogmatic certainty (Modal Level 3)"
            elif ev_modal == 2 and ext.modal_level == 3:
                severity = DriftSeverity.HIGH
                target_term = "typically"
                desc = "standard/moderate phrasing (Modal Level 2), but voiceover script asserts dogmatic certainty (Modal Level 3)"
            else:  # ev_modal == 1 and ext.modal_level == 2
                severity = DriftSeverity.MEDIUM
                target_term = "suggests"
                desc = "hedged phrasing (Modal Level 1), but voiceover script asserts standard likelihood (Modal Level 2)"

            edit = ext.sentence_text
            terms_to_replace = MODAL_LEVEL_3_TERMS if ext.modal_level == 3 else MODAL_LEVEL_2_TERMS
            for term in terms_to_replace:
                edit = re.sub(rf'\b{re.escape(term)}\b', target_term, edit, flags=re.IGNORECASE)

            drifts.append(
                ScriptClaimDriftRecord(
                    drift_type=DriftType.STRENGTHENED,
                    severity=severity,
                    scene_id=ext.scene_id,
                    beat_id=ext.beat_id,
                    script_sentence=ext.sentence_text,
                    evidence_claim_id=claim_node.claim_id,
                    evidence_text=claim_node.claim_text,
                    observed_value=f"Modal Level {ext.modal_level}",
                    expected_value=f"Modal Level {ev_modal}",
                    explanation=f"Unearned modal certainty jump: Evidence text uses {desc}.",
                    recommended_edit=edit,
                )
            )
        elif claim_node.confidence_score <= 0.70 and ext.modal_level == 3:
            if not any(d.drift_type == DriftType.STRENGTHENED for d in drifts):
                drifts.append(
                    ScriptClaimDriftRecord(
                        drift_type=DriftType.STRENGTHENED,
                        severity=DriftSeverity.MEDIUM,
                        scene_id=ext.scene_id,
                        beat_id=ext.beat_id,
                        script_sentence=ext.sentence_text,
                        evidence_claim_id=claim_node.claim_id,
                        evidence_text=claim_node.claim_text,
                        observed_value=f"Confidence {claim_node.confidence_score:.2f} asserted as absolute fact",
                        expected_value="Hedged framing (likely / preliminary)",
                        explanation="Low/moderate confidence claim (<=0.70) asserted with absolute certainty.",
                        recommended_edit=f"Calibrate sentence with qualifier: 'Evidence indicates {claim_node.claim_text.lower()}'.",
                    )
                )
>>>>
```

### Fix 5: Removal of Duplicate Drifts & Generalization of Compound Growth
**File**: `src/epistemic/script_verifier.py`:
1. In `_check_compound_growth_error`:
```python
    def _check_compound_growth_error(
        self,
        ext: ScriptSentenceExtraction,
        drifts: List[ScriptClaimDriftRecord],
    ) -> None:
        """Checks for compound growth percentage arithmetic error in sentence text."""
        if any(d.drift_type == DriftType.ALTERED_NUMBER and "calculation error" in d.explanation.lower() for d in drifts):
            return

        growth_match = COMPOUND_GROWTH_PATTERN.search(ext.sentence_text)
        if growth_match:
            v_start = float(growth_match.group(1))
            v_end = float(growth_match.group(2))
            stated_pct = float(growth_match.group(3))
            if v_start > 0:
                calc_pct = ((v_end - v_start) / v_start) * 100.0
                if abs(stated_pct - calc_pct) > 0.5:
                    drifts.append(
                        ScriptClaimDriftRecord(
                            drift_type=DriftType.ALTERED_NUMBER,
                            severity=DriftSeverity.CRITICAL,
                            scene_id=ext.scene_id,
                            beat_id=ext.beat_id,
                            script_sentence=ext.sentence_text,
                            observed_value=f"{stated_pct}%",
                            expected_value=f"{calc_pct:.1f}%",
                            explanation=(
                                f"Mathematical calculation error: Growth from {v_start} to {v_end} is "
                                f"{calc_pct:.1f}%, but script asserts {stated_pct}%."
                            ),
                            recommended_edit=ext.sentence_text.replace(f"{stated_pct:.0f}%", f"{calc_pct:.0f}%").replace(f"{stated_pct}%", f"{calc_pct:.1f}%"),
                        )
                    )
```
2. In `_check_altered_numbers`, **delete** lines 768–798 (the redundant compound growth block).
3. In `_check_fabricated_quotes`, add guard at top:
```python
        if not ext.extracted_quotes:
            return
        if any(d.drift_type == DriftType.FABRICATED_QUOTE for d in drifts):
            return
```
4. In `check_drift`, deduplicate drifts before returning:
```python
        unique_drifts: List[ScriptClaimDriftRecord] = []
        seen_keys = set()
        for d in drifts:
            key = (d.drift_type, d.script_sentence, str(d.observed_value), str(d.expected_value))
            if key not in seen_keys:
                seen_keys.add(key)
                unique_drifts.append(d)
        return unique_drifts
```

### Fix 6: Two-Pass 1-to-1 Number Pairing & Boundary Replacement
**File**: `src/epistemic/script_verifier.py` (in `_check_altered_numbers` after `ev_numbers` extraction)
```python
        matched_s_indices = set()
        matched_e_indices = set()

        # Pass 1: match identical or within-tolerance numbers
        for s_idx, (s_val, s_tok, is_approx) in enumerate(ext.extracted_numbers):
            tol = self.tolerance_approx if is_approx else self.tolerance_exact
            best_e_idx = None
            best_err = float("inf")
            for e_idx, (e_val, e_tok, _) in enumerate(ev_numbers):
                if e_idx in matched_e_indices:
                    continue
                err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)
                if err <= tol and err < best_err:
                    best_err = err
                    best_e_idx = e_idx
            if best_e_idx is not None:
                matched_s_indices.add(s_idx)
                matched_e_indices.add(best_e_idx)

        # Pass 2: match remaining numbers by log-distance (preventing auxiliary counts from matching years)
        unmatched_s = [i for i in range(len(ext.extracted_numbers)) if i not in matched_s_indices]
        unmatched_e = [j for j in range(len(ev_numbers)) if j not in matched_e_indices]

        for s_idx in unmatched_s:
            s_val, s_tok, is_approx = ext.extracted_numbers[s_idx]
            if not unmatched_e:
                break

            best_e_idx = None
            best_log_diff = float("inf")
            for e_idx in unmatched_e:
                e_val, e_tok, _ = ev_numbers[e_idx]
                if s_val > 0 and e_val > 0:
                    ld = abs(math.log10(s_val) - math.log10(e_val))
                else:
                    ld = abs(s_val - e_val)
                if ld < best_log_diff:
                    best_log_diff = ld
                    best_e_idx = e_idx

            # Only pair if magnitude gap is reasonably related (< 1.5 log-diff, i.e. <= ~30x)
            if best_e_idx is not None and best_log_diff < 1.5:
                e_val, e_tok, _ = ev_numbers[best_e_idx]
                matched_e_indices.add(best_e_idx)
                matched_s_indices.add(s_idx)
                unmatched_e.remove(best_e_idx)

                err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)

                # Order of magnitude check: 10x trap (log diff in [0.99, 1.49])
                if s_val > 0 and e_val > 0 and best_log_diff >= 0.99:
                    rec_edit = re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, ext.sentence_text)
                    drifts.append(
                        ScriptClaimDriftRecord(
                            drift_type=DriftType.ALTERED_NUMBER,
                            severity=DriftSeverity.CRITICAL,
                            scene_id=ext.scene_id,
                            beat_id=ext.beat_id,
                            script_sentence=ext.sentence_text,
                            evidence_claim_id=claim_node.claim_id,
                            evidence_text=claim_node.claim_text,
                            observed_value=s_val,
                            expected_value=e_val,
                            explanation=(
                                f"Order-of-magnitude numerical distortion (10x trap): Script states '{s_tok}' "
                                f"({s_val:g}), but evidence states '{e_tok}' ({e_val:g})."
                            ),
                            recommended_edit=rec_edit,
                        )
                    )
                    continue

                tol = self.tolerance_approx if is_approx else self.tolerance_exact
                if err > tol:
                    severity = DriftSeverity.HIGH if err > 0.10 else DriftSeverity.MEDIUM
                    rec_edit = re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, ext.sentence_text)
                    drifts.append(
                        ScriptClaimDriftRecord(
                            drift_type=DriftType.ALTERED_NUMBER,
                            severity=severity,
                            scene_id=ext.scene_id,
                            beat_id=ext.beat_id,
                            script_sentence=ext.sentence_text,
                            evidence_claim_id=claim_node.claim_id,
                            evidence_text=claim_node.claim_text,
                            observed_value=s_val,
                            expected_value=e_val,
                            explanation=(
                                f"Numerical value mutation: Script mentions '{s_tok}' ({s_val:g}), "
                                f"exceeding allowed tolerance ({tol:.1%}) from evidence '{e_tok}' ({e_val:g}). "
                                f"Relative delta: {err:.2%}."
                            ),
                            recommended_edit=rec_edit,
                        )
                    )
```

### Fix 7: Export `ScriptSentenceSegmenter`
**File**: `src/epistemic/script_verifier.py`
```python
class ScriptSentenceSegmenter:
    """Dedicated sentence segmenter protecting abbreviations, decimals, and quotations."""

    def __init__(self) -> None:
        self._verifier = ScriptVerifier()

    def segment_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        return self._verifier.segment_sentences(text)

    def extract_sentences(self, script: Any) -> List[ScriptSentenceExtraction]:
        return self._verifier.extract_sentences(script)
```
Or define `ScriptSentenceSegmenter = ScriptVerifier`.
Export `ScriptSentenceSegmenter` in `__all__` in `src/epistemic/script_verifier.py` and `src/epistemic/__init__.py`.

---

## 5. Verification Method

To independently verify all findings and confirm remediation:

### 5.1 Verification Commands
1. **Target Unit Test Suite**:
   ```bash
   uv run pytest tests/test_script_verifier.py -v
   ```
2. **Milestone 4 Part A, B, C Suite**:
   ```bash
   uv run pytest tests/test_script_verifier.py tests/test_visual_verifier.py tests/test_numerical_pipeline.py -v
   ```
3. **Full Regression Suite**:
   ```bash
   uv run pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -q
   ```
4. **Standalone Verification Script**:
   ```bash
   uv run python .agents/explorer_1_m4_it2/test_remediated_verifier.py
   ```

### 5.2 Specific Assertions to Add to `tests/test_script_verifier.py`
Worker should add the following tests to `tests/test_script_verifier.py`:
- `test_contraction_and_possessive_apostrophes_not_treated_as_quotes`
- `test_detect_modal_escalation_level_2_to_level_3`
- `test_detect_modal_escalation_level_1_to_level_2`
- `test_no_duplicate_drifts_on_grounded_sentences`
- `test_word_boundary_modal_matching_benign_words`
- `test_auxiliary_count_not_flagged_as_10x_distortion`
- `test_script_sentence_segmenter_export`
- `test_compound_growth_alternate_phrasings`

### 5.3 Invalidation Conditions
- Any occurrence of `"room"` remaining in `src/epistemic/script_verifier.py`.
- Script with `"It's clear that the company's product..."` flagged as `FABRICATED_QUOTE`.
- Escalation from Level 2 to Level 3 (`"Silicon transistors typically exhibit..."` -> `"Silicon transistors undeniably prove..."`) passing without `STRENGTHENED` drift.
- Duplicate `FABRICATED_QUOTE` or compound math drift records emitted for a single sentence.
- Substring words like `"factory"` or month `"May"` altering modal levels.
- Auxiliary counts like `"3 engineers"` paired with years (`1948`) or generating 10x traps.
- Regression failures on `test_h9_acceptance.py` (44/44 required).
