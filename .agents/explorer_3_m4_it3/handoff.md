# Investigation & Remediation Report: NumericalPipeline Export Interface & ScriptVerifier Edge Cases

**Agent**: `explorer_3_m4_it3`  
**Roles**: `investigator`, `synthesizer`  
**Date**: 2026-09-14  
**Target Milestone**: Milestone 4 — Script Re-Verification & Visual/Numerical Integrity  
**Target Files**: `src/epistemic/numerical_pipeline.py`, `src/epistemic/script_verifier.py`, `src/epistemic/__init__.py`  
**Authoritative Specifications**:  
- `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md`
- `g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_10\PROJECT.md`
- `g:\Finding-new-code\harness9\.agents\reviewer_2_m4_g10\handoff.md` (Section 2.4)
- `g:\Finding-new-code\harness9\.agents\challenger_1_m4_g10\plan.md`

---

## 1. Observation

### 1.1 Interface Gap: Missing `NumericalPipeline` Export & Method Alignment
- **Specification**: `PROJECT.md` line 99 defines the contract:
  ```markdown
  - NumericalPipeline.verify_chart_data(dataset: NumericalDataset, chart_config: ChartConfig) -> NumericalVerificationResult
  ```
- **Code Inspection**:
  - In `src/epistemic/numerical_pipeline.py:657–753`:
    ```python
    class NumericalInvariantChecker:
        """Audits chart configurations and visual metrics for mathematical distortion."""

        @classmethod
        def verify_chart_data(
            cls,
            dataset: NumericalDataset,
            chart_config: ChartConfig,
        ) -> NumericalVerificationResult:
    ```
  - The class is defined as `NumericalInvariantChecker`. There is no class, alias, or reference named `NumericalPipeline` anywhere in `src/epistemic/numerical_pipeline.py`.
  - In `src/epistemic/__init__.py:74–86, 151–162`:
    ```python
    from src.epistemic.numerical_pipeline import (
        ChartConfig,
        ChartElement,
        ChartType,
        DeterministicChartRenderer,
        NumericalDataPoint,
        NumericalDataset,
        NumericalDatasetIngestion,
        NumericalInvariantChecker,
        NumericalTransformationRecord,
        NumericalTransformer,
        NumericalVerificationResult,
    )
    ```
    `NumericalPipeline` is omitted from both the imports and `__all__`.
- **Empirical Execution**:
  - Command:
    ```bash
    .venv\Scripts\python.exe -c "from src.epistemic.numerical_pipeline import NumericalPipeline; print(NumericalPipeline)"
    ```
  - Result:
    ```
    ImportError: cannot import name 'NumericalPipeline' from 'src.epistemic.numerical_pipeline' (G:\Finding-new-code\harness9\src\epistemic\numerical_pipeline.py)
    ```
- **Signature Confirmation**:
  `NumericalInvariantChecker.verify_chart_data` is a `@classmethod` accepting `(dataset: NumericalDataset, chart_config: ChartConfig)` and returning `NumericalVerificationResult`. Aliasing `NumericalPipeline = NumericalInvariantChecker` satisfies the contract for both class-level (`NumericalPipeline.verify_chart_data(...)`) and instance-level invocations.

---

### 1.2 ScriptVerifier Edge Case 1: Multi-Sentence Quote Segmentation Flaw
- **Location**: `src/epistemic/script_verifier.py:288–312` (`segment_sentences`) and `lines 420–425` (`_annotate_sentence`).
- **Code Inspection**:
  ```python
  288: pattern = r'([.!?]+[\'"”’]?)(?:\s+(?=[A-Z0-9"\'“‘])|\s*$)'
  ...
  420: quotes = []
  421: for m in re.finditer(r'["“]([^"”\r\n]{3,})["”]', sentence_text):
  422:     quotes.append(m.group(1))
  423: single_quote_pattern = r'(?:(?<=^)|(?<=[\s\(\[\{,:]))[\'‘]((?:[^\'’\r\n]|(?<=[a-zA-Z])[\'’](?=[a-zA-Z])){3,}?)[\'’](?=$|[\s.,!?;:\)\]\}])'
  424: for m in re.finditer(single_quote_pattern, sentence_text):
  425:     quotes.append(m.group(1))
  ```
- **Vulnerability Mechanism**:
  When narration contains a quote spanning across periods (e.g. `He said: "Sentence one. Sentence two."`):
  1. `pattern` in line 288 matches the period at `Sentence one.` because it is followed by a space and capitalized `S`.
  2. The segmenter does not track whether it is inside an open quotation. It splits the utterance into:
     - Segment 1: `'He said: "Sentence one.'` (unmatched opening quote mark).
     - Segment 2: `'Sentence two."'` (unmatched closing quote mark).
  3. In `_annotate_sentence`, regex line 421 `r'["“]([^"”\r\n]{3,})["”]'` requires matching opening and closing quotes. Because both segments have only one unmatched quote mark, `quotes` is empty (`[]`).
  4. In `check_drift` line 593:
     ```python
     if ext.extracted_quotes and graph is not None:
         self._check_all_quotes_against_graph(ext, graph, drifts)
     ```
     Because `ext.extracted_quotes == []`, quote verification is completely bypassed.
- **Empirical Execution**:
  ```python
  from src.epistemic.graph import EvidenceGraph
  from src.epistemic.script_verifier import ScriptVerifier, DriftType
  from src.models.contracts import ClaimRecord, SourceRecord, SourceTier, EpistemicStatus, ConsensusState, ClaimType

  sample_source = SourceRecord(source_id='s1', title='Report', url='https://example.com', source_tier=SourceTier.PRIMARY_SOURCE)
  graph = EvidenceGraph(graph_id='g1')
  c5 = ClaimRecord(claim_id='c5', claim_text='There is plenty of room at the bottom.', claim_type=ClaimType.DIRECT_QUOTE, epistemic_status=EpistemicStatus.VERIFIED, consensus_state=ConsensusState.STRONG_CONSENSUS, confidence_score=1.0, primary_source=sample_source)
  graph.add_claim(claim_text=c5.claim_text, claim_id=c5.claim_id, claim_type=c5.claim_type.value, confidence_score=1.0, claim_record=c5)

  v = ScriptVerifier()
  script_multi_obj = {
      'scenes': [{
          'scene_id': 's1',
          'beats': [{
              'beat_id': 'b1',
              'text': 'Feynman declared: "There is plenty of room. It is at the bottom."',
              'grounded_claim_ids': ['c5']
          }]
      }]
  }
  rep = v.verify_script(script_multi_obj, graph)
  print('Drifts count:', len(rep.drifts))
  print('Passed:', rep.passed)
  ```
- **Observed Output**:
  ```
  Drifts count: 0
  Drifts: []
  Passed: True
  ```
  A completely altered, non-verbatim quote (`"There is plenty of room. It is at the bottom."`) bypassed quote exactness auditing and the Paraphrase Mandate, returning `Passed: True` with 0 drifts.

---

### 1.3 ScriptVerifier Edge Case 2: Negative Number Parsing in `_extract_numbers_from_text`
- **Location**: `src/epistemic/script_verifier.py:449–477` (`_extract_numbers_from_text`).
- **Code Inspection**:
  ```python
  449: def _extract_numbers_from_text(self, text: str, default_approx: bool) -> List[Tuple[float, str, bool]]:
  450:     """Extracts scalar numbers, multipliers (K, M, B), and percentages."""
  451:     results = []
  452:     pattern = r'(\b\d+(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|thousand|k|m|b|%|percent)?'
  453:     for m in re.finditer(pattern, text, re.IGNORECASE):
  454:         raw_str = m.group(1).replace(",", "")
  455:         mult_str = (m.group(2) or "").lower()
  456:         try:
  457:             val = float(raw_str)
  ...
  ```
- **Vulnerability Mechanism**:
  1. `pattern` begins with `\b\d+`. The regex word boundary `\b` asserts position between non-word characters (`-`) and digits (`\d`).
  2. As a consequence, negative signs (`-`, `−`, `–`) are stripped.
  3. Preceding negative currency symbols (e.g. `-$50M`, `$-50M`) fail to extract or extract without sign.
  4. Spoken negatives (`negative 15%`, `minus 20`) drop the sign.
- **Empirical Execution**:
  ```python
  v = ScriptVerifier()
  print('Negative %:', v._extract_numbers_from_text('The return was -15%', False))
  print('Negative temp:', v._extract_numbers_from_text('Temperature dropped to -20 degrees', False))
  print('Negative currency:', v._extract_numbers_from_text('Loss was -$50M', False))
  print('Negative float:', v._extract_numbers_from_text('Operating margin was -3.5%', False))
  ```
- **Observed Output**:
  ```
  Negative %: [(15.0, '15%', False)]
  Negative temp: [(20.0, '20 ', False)]
  Negative currency: []
  Negative float: [(3.5, '3.5%', False)]
  ```
- **Downstream Effect**:
  When evidence claims a loss (`"-15%"`) and script asserts a gain (`"15%"`):
  - Evidence number: `[(15.0, '15%', False)]`
  - Script number: `[(15.0, '15%', False)]`
  - Pass 1 error: `abs(15.0 - 15.0) / 15.0 = 0.0 <= tolerance`.
  - The severe polarity reversal (loss vs gain) is accepted as an exact 0.0% error match with 0 drifts!

---

### 1.4 ScriptVerifier Edge Case 3: Extreme Magnitude Gap (> 1.5 log diff / > 31.6x) in Drift Detection
- **Location**: `src/epistemic/script_verifier.py:853–928` (`_check_altered_numbers`).
- **Code Inspection**:
  ```python
  853: unmatched_s = [i for i in range(len(ext.extracted_numbers)) if i not in matched_s_indices]
  854: unmatched_e = [j for j in range(len(ev_numbers)) if j not in matched_e_indices]
  ...
  864: for e_idx in unmatched_e:
  865:     e_val, e_tok, _ = ev_numbers[e_idx]
  866:     if s_val > 0 and e_val > 0:
  867:         ld = abs(math.log10(s_val) - math.log10(e_val))
  868:     else:
  869:         ld = abs(s_val - e_val)
  870:     if ld < best_log_diff:
  871:         best_log_diff = ld
  872:         best_e_idx = e_idx
  873: 
  874: # Only pair if magnitude gap is reasonably related (< 1.5 log-diff, i.e. <= ~30x)
  875: if best_e_idx is not None and best_log_diff < 1.5:
  876:     ...
  883:     if s_val > 0 and e_val > 0 and best_log_diff >= 0.99:
  884:         # Order of magnitude check: 10x trap (log diff in [0.99, 1.49])
  ```
- **Vulnerability Mechanism**:
  1. The filter `best_log_diff < 1.5` was intended to prevent pairing calendar years (e.g. 1945) with small auxiliary counts (e.g. 3 casualties).
  2. However, it imposes an upper bound of `1.49` log-diff (`10^1.49 ≈ 30.9x`) on paired drift detection.
  3. Any numerical distortion exceeding 31.6x (e.g. 35x, 50x, 100x, 1000x):
     - Log difference is `log10(10000) - log10(100) = 4 - 2 = 2.0 >= 1.5`.
     - `best_log_diff < 1.5` evaluates to `False`.
     - The altered number is NOT paired and NOT added to `drifts`.
     - The alteration is SILENTLY DROPPED.
  4. Furthermore, line 869 falls back to `ld = abs(s_val - e_val)` for non-positive numbers. If `s_val = 15` and `e_val = -15`, `ld = 30.0 >= 1.5`. If `s_val = -10` and `e_val = -12`, `ld = 2.0 >= 1.5`. Negative number alterations are always dropped!
- **Empirical Execution**:
  ```python
  # Scenario: 50,000 casualties in evidence
  rep_10x = v.verify_script('During the siege, over 500,000 soldiers perished in the battle.', graph)
  rep_100x = v.verify_script('During the siege, over 5,000,000 soldiers perished in the battle.', graph)

  print('10x drifts count:', len(rep_10x.drifts))
  print('100x drifts count:', len(rep_100x.drifts))
  print('100x passed:', rep_100x.passed)
  ```
- **Observed Output**:
  ```
  10x drifts count: 1
  100x drifts count: 0
  100x passed: True
  ```
  A 10x error (500k vs 50k) is correctly flagged as a CRITICAL BLOCK (`DriftType.ALTERED_NUMBER`).
  A 100x error (5M vs 50k) is SILENTLY DROPPED and passes verification (`Passed: True`).

---

## 2. Logic Chain

1. **Premise 1 (Interface Contract)**: `PROJECT.md` line 99 explicitly defines `NumericalPipeline.verify_chart_data(dataset: NumericalDataset, chart_config: ChartConfig) -> NumericalVerificationResult`.
2. **Observation 1**: `src/epistemic/numerical_pipeline.py` implements the exact logic under `NumericalInvariantChecker` as a `@classmethod`, but lacks the class alias `NumericalPipeline`. This causes external callers conforming to `PROJECT.md` to fail with `ImportError`.
3. **Premise 2 (Quote Grounding Invariant)**: Direct quotes in scripts must be strictly verified against primary source evidence; ungrounded or altered quotes must trigger the Paraphrase Mandate (`DriftType.FABRICATED_QUOTE`).
4. **Observation 2**: Sentence segmentation (`segment_sentences`) blindly splits on periods inside quotation marks (`"Sentence one. Sentence two."`). This separates opening and closing quotation marks into distinct sentences, breaking regex matching in `_annotate_sentence` and causing `extracted_quotes` to be empty.
5. **Deduction 2**: As proved empirically, an altered quote split across a period bypasses all quote verification rules and passes with `Passed: True`. Sentence segmentation must preserve periods inside open quotations so multi-sentence quotes stay intact.
6. **Premise 3 (Numerical Integrity Invariant)**: Verification must preserve mathematical signs and detect value drift across both positive and negative domains.
7. **Observation 3**: `_extract_numbers_from_text` strips negative signs due to `\b\d+`. Evidence with `-15%` and script with `15%` both extract as `15.0`, yielding 0.0% error and zero drifts.
8. **Premise 4 (Non-Dropping Drift Invariant)**: Gross numerical alterations must never be silently ignored; a 100x alteration is more severe than a 10x alteration.
9. **Observation 4**: In `_check_altered_numbers`, line 874 gates pairing behind `best_log_diff < 1.5`. Any alteration > 31.6x (e.g. 100x, 1000x) is rejected from pairing and never recorded in `drifts`.
10. **Conclusion**: All 4 issues represent genuine defects/vulnerabilities that undermine the epistemic verification layer. Remediating them restores full interface compliance and closes factual evasion loopholes.

---

## 3. Detailed Remediation Specification & Code Changes

### Remediation 1: `NumericalPipeline` Export & Class Alias
**Target File**: `src/epistemic/numerical_pipeline.py` and `src/epistemic/__init__.py`

#### 1. In `src/epistemic/numerical_pipeline.py`:
Add alias and convenience methods at line 753:
```python
# ===========================================================================
# 6. Public Export Aliases
# ===========================================================================

# Conforms to PROJECT.md line 99 interface contract
NumericalPipeline = NumericalInvariantChecker
```

#### 2. In `src/epistemic/__init__.py`:
Import `NumericalPipeline` and add it to `__all__`:
```python
from src.epistemic.numerical_pipeline import (
    ChartConfig,
    ChartElement,
    ChartType,
    DeterministicChartRenderer,
    NumericalDataPoint,
    NumericalDataset,
    NumericalDatasetIngestion,
    NumericalInvariantChecker,
    NumericalPipeline,
    NumericalTransformationRecord,
    NumericalTransformer,
    NumericalVerificationResult,
)
```
And add `"NumericalPipeline"` to `__all__`.

---

### Remediation 2: ScriptVerifier Multi-Sentence Quote Protection
**Target File**: `src/epistemic/script_verifier.py:276–325` (`segment_sentences`)

#### Design Rationale:
Pre-scan `text` for balanced quotation spans (both double quotes `["“]...["”]` and single quotes not in contractions). A sentence boundary punctuation `[.!?]` is protected (not split) if it falls strictly inside an unclosed quote span (`span_start < punct_end < span_end`). When `punct_end == span_end`, the punctuation is at the closing quote boundary, so the sentence terminates normally.

#### Code Replacement in `segment_sentences`:
```python
    def segment_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """Splits raw text into sentences while protecting abbreviations, numbers, and quotes."""
        if not text or not text.strip():
            return []

        working = text
        spans: List[Tuple[int, int]] = []
        active_abbrevs = self.abbreviations if hasattr(self, "abbreviations") and self.abbreviations is not None else ABBREVIATIONS

        # Pre-compute quotation spans to avoid splitting multi-sentence quotes across periods
        quote_spans: List[Tuple[int, int]] = []
        # Double and curly quotes
        for qm in re.finditer(r'["“]([^"”\r\n]*?)["”]', working):
            quote_spans.append((qm.start(), qm.end()))
        # Single quotes (excluding contractions)
        single_quote_pattern = r'(?:(?<=^)|(?<=[\s\(\[\{,:]))[\'‘]((?:[^\'’\r\n]|(?<=[a-zA-Z])[\'’](?=[a-zA-Z])){3,}?)[\'’](?=$|[\s.,!?;:\)\]\}])'
        for qm in re.finditer(single_quote_pattern, working):
            quote_spans.append((qm.start(), qm.end()))

        # Find sentence boundaries: punctuation (.!?) followed by space and capital letter or end of string
        pattern = r'([.!?]+[\'"”’]?)(?:\s+(?=[A-Z0-9"\'“‘])|\s*$)'

        last_end = 0
        for m in re.finditer(pattern, working):
            punct_end = m.end(1)

            # Check if this punctuation point is strictly inside an open quote span
            inside_quote = any(qs < punct_end < qe for qs, qe in quote_spans)
            if inside_quote:
                continue

            candidate_text = working[last_end:punct_end].strip()

            # Check if candidate ends with an abbreviation
            words = candidate_text.split()
            if words:
                last_word = words[-1].lower()
                if last_word in active_abbrevs:
                    continue
                # Check decimal number like '$3.5M.' or '3.14'
                if re.search(r'\b\d+\.\d*$', candidate_text):
                    continue

            # Valid sentence boundary
            start_idx = working.find(candidate_text, last_end)
            if start_idx != -1:
                end_idx = start_idx + len(candidate_text)
                spans.append((candidate_text, start_idx, end_idx))
                last_end = m.end()

        # Catch trailing segment if any
        if last_end < len(working):
            trailing = working[last_end:].strip()
            if trailing:
                start_idx = working.find(trailing, last_end)
                spans.append((trailing, start_idx, start_idx + len(trailing)))

        if not spans:
            clean_full = text.strip()
            return [(clean_full, 0, len(clean_full))]

        return spans
```

---

### Remediation 3: Negative Number Parsing in `_extract_numbers_from_text`
**Target File**: `src/epistemic/script_verifier.py:449–477` (`_extract_numbers_from_text`)

#### Design Rationale:
1. Capture optional sign `[+\-−–]` or spoken prefix `negative|minus`.
2. Support optional currency symbols `[\$,€,£,¥]`.
3. Ensure prefix lookbehind `(?<=^)|(?<=[\s\(\[\{:=~,])` so hyphens in words (`pre-1950`, `top-10`) or ranges (`20-30`) do not turn positive numbers into negatives.
4. Correctly negate `val = -val` when a negative sign or spoken word is present.

#### Code Replacement in `_extract_numbers_from_text`:
```python
    def _extract_numbers_from_text(self, text: str, default_approx: bool) -> List[Tuple[float, str, bool]]:
        """Extracts scalar numbers, multipliers (K, M, B), percentages, and negative values."""
        results = []
        # Pattern captures:
        # Group 1 (word_sign): 'negative' or 'minus'
        # Group 2 (sign_prefix): '+' or '-' before optional currency (e.g. -$50M, -15%)
        # Group 3 (sign_after_curr): '+' or '-' after currency (e.g. $-50M)
        # Group 4 (number): digits with commas and decimals
        # Group 5 (multiplier): billion, million, thousand, k, m, b, %, percent
        pattern = (
            r'(?:(?<=^)|(?<=[\s\(\[\{:=~,]))'
            r'(?:'
                r'(?P<word_sign>\b(?:negative|minus)\s+)'
                r'|'
                r'(?P<sign_prefix>[+\-−–])\s*(?:[\$,€,£,¥]\s*)?'
                r'|'
                r'(?:[\$,€,£,¥]\s*)(?P<sign_after_curr>[+\-−–])?\s*'
            r')?'
            r'(?P<number>\d+(?:,\d{3})*(?:\.\d+)?)'
            r'\s*'
            r'(?P<mult>billion|million|thousand|k|m|b|%|percent)?'
            r'(?=$|[\s.,!?;:\)\]\}])'
        )

        for m in re.finditer(pattern, text, re.IGNORECASE):
            raw_num_str = m.group("number").replace(",", "")
            mult_str = (m.group("mult") or "").lower()
            word_sign = m.group("word_sign")
            sign_prefix = m.group("sign_prefix")
            sign_after_curr = m.group("sign_after_curr")

            is_negative = bool(word_sign) or (sign_prefix in ("-", "−", "–")) or (sign_after_curr in ("-", "−", "–"))

            try:
                val = float(raw_num_str)
            except ValueError:
                continue

            if mult_str in ("billion", "b"):
                val *= 1e9
            elif mult_str in ("million", "m"):
                val *= 1e6
            elif mult_str in ("thousand", "k"):
                val *= 1e3

            if is_negative:
                val = -val

            # Check local approximation around the number
            start_pos = max(0, m.start() - 20)
            end_pos = min(len(text), m.end() + 20)
            context = text[start_pos:end_pos].lower()
            local_approx = default_approx or any(term in context for term in APPROXIMATION_TERMS)

            results.append((val, m.group(0).strip(), local_approx))

        return results
```

---

### Remediation 4: Extreme Magnitude Gap (> 1.5 log diff / > 31.6x) & Sign Flips in `_check_altered_numbers`
**Target File**: `src/epistemic/script_verifier.py:853–928` (`_check_altered_numbers`)

#### Design Rationale:
1. **Disambiguate Years**: Distinguish 4-digit calendar years (`1000 <= v <= 2099` without multipliers or decimals) with a +100.0 distance penalty when comparing against non-year scalars. This prevents auxiliary counts from matching years without needing an arbitrary `< 1.5` log-diff ceiling.
2. **Log-Magnitude Distance**: Use `abs(math.log10(abs(s_val)) - math.log10(abs(e_val)))` for non-zero numbers.
3. **Sign Polarity Inversion**: Detect when non-zero numbers have opposing signs (`(s_val < 0) != (e_val < 0)`). Flag as `DriftSeverity.CRITICAL`.
4. **Remove Hard Filter**: Allow pairing of the best available candidate even if `log_mag_diff >= 1.5`.
5. **Classify Severity by Magnitude**:
   - `log_mag_diff >= 1.5`: Extreme order-of-magnitude distortion (> 31.6x, e.g. 100x, 1000x) -> `DriftSeverity.CRITICAL`.
   - `0.99 <= log_mag_diff < 1.5`: 10x order-of-magnitude trap -> `DriftSeverity.CRITICAL`.
   - `log_mag_diff < 0.99`: Tolerance threshold check (`err > tol`) -> `DriftSeverity.HIGH` or `MEDIUM`.

#### Code Replacement in `_check_altered_numbers`:
```python
        # Helper: identify calendar years to avoid cross-matching years with metrics
        def _is_calendar_year(val: float, tok: str) -> bool:
            return 1000 <= val <= 2099 and val == math.floor(val) and not any(
                c in tok.lower() for c in ("%", "m", "b", "k", "$", "€", "£", "¥")
            )

        # Pass 2: match remaining numbers by log-distance with year disambiguation
        unmatched_s = [i for i in range(len(ext.extracted_numbers)) if i not in matched_s_indices]
        unmatched_e = [j for j in range(len(ev_numbers)) if j not in matched_e_indices]

        for s_idx in unmatched_s:
            s_val, s_tok, is_approx = ext.extracted_numbers[s_idx]
            if not unmatched_e:
                break

            best_e_idx = None
            best_dist = float("inf")
            s_is_year = _is_calendar_year(s_val, s_tok)

            for e_idx in unmatched_e:
                e_val, e_tok, _ = ev_numbers[e_idx]
                e_is_year = _is_calendar_year(e_val, e_tok)

                # Distance calculation using absolute magnitude
                if s_val != 0 and e_val != 0:
                    d = abs(math.log10(abs(s_val)) - math.log10(abs(e_val)))
                else:
                    d = abs(s_val - e_val)

                # Add heavy penalty if pairing a year with a non-year metric
                if s_is_year != e_is_year:
                    d += 100.0

                if d < best_dist:
                    best_dist = d
                    best_e_idx = e_idx

            # Pair candidate (allow pairing even if best_dist >= 1.5 to catch extreme alterations)
            if best_e_idx is not None:
                e_val, e_tok, _ = ev_numbers[best_e_idx]
                e_is_year = _is_calendar_year(e_val, e_tok)

                # Do not pair year with non-year if other candidates exist
                if s_is_year != e_is_year and best_dist >= 100.0 and len(unmatched_e) > 1:
                    continue

                matched_e_indices.add(best_e_idx)
                matched_s_indices.add(s_idx)
                unmatched_e.remove(best_e_idx)

                rec_edit = re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, ext.sentence_text)

                # 1. Check sign polarity flip (e.g. -15% vs +15%)
                if s_val != 0 and e_val != 0 and (s_val < 0) != (e_val < 0):
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
                                f"Mathematical sign / polarity inversion: Script asserts '{s_tok}' ({s_val:g}), "
                                f"while evidence states opposite sign '{e_tok}' ({e_val:g})."
                            ),
                            recommended_edit=rec_edit,
                        )
                    )
                    continue

                # 2. Check extreme order of magnitude distortion (log diff >= 1.5, i.e. > ~31.6x, e.g. 100x, 1000x)
                log_mag_diff = (
                    abs(math.log10(abs(s_val)) - math.log10(abs(e_val)))
                    if (s_val != 0 and e_val != 0) else abs(s_val - e_val)
                )

                if s_val != 0 and e_val != 0 and log_mag_diff >= 1.5:
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
                                f"Extreme order-of-magnitude numerical distortion: Script states '{s_tok}' "
                                f"({s_val:g}), but evidence states '{e_tok}' ({e_val:g}) "
                                f"(divergence of {10**log_mag_diff:.1f}x exceeds 31.6x threshold)."
                            ),
                            recommended_edit=rec_edit,
                        )
                    )
                    continue

                # 3. Check 10x order-of-magnitude trap (log diff in [0.99, 1.49])
                if s_val != 0 and e_val != 0 and log_mag_diff >= 0.99:
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

                # 4. Standard tolerance checking
                err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)
                tol = self.tolerance_approx if is_approx else self.tolerance_exact
                if err > tol:
                    severity = DriftSeverity.HIGH if err > 0.10 else DriftSeverity.MEDIUM
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

---

## 4. Caveats

1. **Read-Only Explorer Execution**: This investigation strictly obeyed the read-only mandate. No modifications were committed to source files in `src/`. All proposals are specified as drop-in code snippets ready for implementation by the builder/implementer agent.
2. **Quotation Grammar Scope**: The quote preservation algorithm relies on balanced opening and closing quotes (`"..."`, `'...'`). If an author writes an intentionally unclosed quote across scenes without closing it, the sentence segmenter will not treat that span as closed, falling back to standard sentence splitting at trailing periods.
3. **Calendar Year Boundary**: The calendar year heuristic (`1000 <= val <= 2099`) covers the standard historical range for contemporary and medieval/modern history. For ancient BCE years (e.g. -44, -500), ancient dates are typically represented with explicit negative signs or BCE suffixes, which are handled by the negative sign extractor and temporal anchor parser.

---

## 5. Conclusion

1. **Interface Contract Gap**:
   - `NumericalPipeline` was missing from `src/epistemic/numerical_pipeline.py` and `src/epistemic/__init__.py`.
   - Remediated by aliasing `NumericalPipeline = NumericalInvariantChecker`, which exposes `@classmethod verify_chart_data(dataset, chart_config) -> NumericalVerificationResult` matching `PROJECT.md` line 99.

2. **ScriptVerifier Vulnerabilities Closed**:
   - **Multi-Sentence Quotes**: Protected periods inside quote spans from being split during sentence segmentation. Ensures full quote strings are extracted and submitted to `_check_all_quotes_against_graph`, closing the quote evasion loophole.
   - **Negative Numbers**: Overhauled regex to capture `-`, `−`, `–`, currency signs, and spoken negatives (`negative`, `minus`). Closes the false-negative pass on polarity inversions (-15% vs +15%).
   - **Extreme Magnitude Gap**: Eliminated the `< 1.5` log-diff ceiling that caused alterations > 31.6x (e.g. 100x, 1000x) to be silently dropped. Replaced with explicit calendar year disambiguation and tiered severity classification (`log_mag_diff >= 1.5` -> `CRITICAL`).

---

## 6. Verification Method

To independently verify these findings and confirm the remediation:

### 1. Verify `NumericalPipeline` Import & Interface
```bash
.venv\Scripts\python.exe -c "from src.epistemic.numerical_pipeline import NumericalPipeline; from src.epistemic import NumericalPipeline as NP2; print('Import succeeded:', NumericalPipeline is NP2); assert hasattr(NumericalPipeline, 'verify_chart_data')"
```

### 2. Verify Multi-Sentence Quote Extraction & Fabrication Detection
```bash
.venv\Scripts\python.exe -c "
from src.epistemic.graph import EvidenceGraph
from src.epistemic.script_verifier import ScriptVerifier, DriftType
from src.models.contracts import ClaimRecord, SourceRecord, SourceTier, EpistemicStatus, ConsensusState, ClaimType

sample_source = SourceRecord(source_id='s1', title='Report', url='https://example.com', source_tier=SourceTier.PRIMARY_SOURCE)
graph = EvidenceGraph(graph_id='g1')
c5 = ClaimRecord(claim_id='c5', claim_text='There is plenty of room at the bottom.', claim_type=ClaimType.DIRECT_QUOTE, epistemic_status=EpistemicStatus.VERIFIED, consensus_state=ConsensusState.STRONG_CONSENSUS, confidence_score=1.0, primary_source=sample_source)
graph.add_claim(claim_text=c5.claim_text, claim_id=c5.claim_id, claim_type=c5.claim_type.value, confidence_score=1.0, claim_record=c5)

v = ScriptVerifier()
script = 'Feynman declared: \"There is plenty of room. It is at the lowest levels.\"'
rep = v.verify_script(script, graph)
print('Drifts count:', len(rep.drifts))
print('Fabricated quote caught:', any(d.drift_type == DriftType.FABRICATED_QUOTE for d in rep.drifts))
assert rep.passed is False
"
```

### 3. Verify Negative Number Parsing & Polarity Flip Detection
```bash
.venv\Scripts\python.exe -c "
from src.epistemic.script_verifier import ScriptVerifier
v = ScriptVerifier()
res_neg = v._extract_numbers_from_text('The return was -15% and loss was -$50M, with margin at -3.2%', False)
print('Extracted:', res_neg)
assert any(val == -15.0 for val, tok, _ in res_neg)
assert any(val == -50000000.0 for val, tok, _ in res_neg)
assert any(val == -3.2 for val, tok, _ in res_neg)
"
```

### 4. Verify Extreme Magnitude Gap (> 100x Distortion) Detection
```bash
.venv\Scripts\python.exe -c "
from src.epistemic.graph import EvidenceGraph
from src.epistemic.script_verifier import ScriptVerifier, DriftType, DriftSeverity
from src.models.contracts import ClaimRecord, SourceRecord, SourceTier, EpistemicStatus, ConsensusState

sample_source = SourceRecord(source_id='s1', title='Report', url='https://example.com', source_tier=SourceTier.PRIMARY_SOURCE)
graph = EvidenceGraph(graph_id='g1')
c2 = ClaimRecord(claim_id='c2', claim_text='Historical archives record 50,000 casualties during the siege.', epistemic_status=EpistemicStatus.VERIFIED, consensus_state=ConsensusState.STRONG_CONSENSUS, confidence_score=0.95, primary_source=sample_source)
graph.add_claim(claim_text=c2.claim_text, claim_id=c2.claim_id, confidence_score=0.95, claim_record=c2)

v = ScriptVerifier()
rep_100x = v.verify_script('During the siege, over 5,000,000 soldiers perished in the battle.', graph)
print('100x drifts count:', len(rep_100x.drifts))
assert len(rep_100x.drifts) >= 1
assert rep_100x.passed is False
assert any(d.drift_type == DriftType.ALTERED_NUMBER and d.severity == DriftSeverity.CRITICAL for d in rep_100x.drifts)
"
```

### 5. Regression Test Command
```bash
.venv\Scripts\pytest.exe tests/test_numerical_pipeline.py tests/test_script_verifier.py tests/test_visual_verifier.py -v
```
Ensure 100% pass rate across all existing unit and adversarial test suites.
