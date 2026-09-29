# Milestone 4 Visual Fact-Checking & Numerical Pipeline Review & Adversarial Challenge Report

**Reviewer Agent**: `reviewer_2_m4_g10`  
**Roles**: `reviewer`, `critic`  
**Date**: 2026-09-14  
**Target Milestone**: Milestone 4 — Visual Fact-Checking & Numerical Pipeline  
**Target Codebase**: `src/epistemic/visual_verifier.py`, `src/epistemic/numerical_pipeline.py`  
**Test Suites**: `tests/test_visual_verifier.py`, `tests/test_numerical_pipeline.py`, `tests/test_m4_adversarial_challenger2.py`  
**Authoritative Contracts**: `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md`, `g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_10\PROJECT.md`, `docs/epistemic/VISUAL_FACT_CHECKING.md`  

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**  
**Overall Risk Assessment**: **HIGH**  
**Integrity Assessment**: **FINDINGS REQUIRING REMEDIATION** (Facade in comparison panel auditing, unverified quote text, brittle regex heuristics leading to false-positive blocks)

---

## 1. Observation

### 1.1 Test Suite Execution
- **Command**: `.venv\Scripts\pytest.exe tests/test_visual_verifier.py tests/test_numerical_pipeline.py tests/test_m4_adversarial_challenger2.py -v`
- **Result**: `60 passed in 26.91s` (100% test pass rate).
  - `tests/test_visual_verifier.py`: 27 passed.
  - `tests/test_numerical_pipeline.py`: 17 passed.
  - `tests/test_m4_adversarial_challenger2.py`: 16 passed.
- **Auxiliary regression command**: `.venv\Scripts\pytest.exe tests/test_script_verifier.py -v`
- **Result**: `24 passed in 14.82s` (100% pass rate).

### 1.2 Comparison Panel Verification Logic (`src/epistemic/visual_verifier.py`, lines 557–616)
```python
557:     def _audit_comparison_panel(
558:         self,
559:         scene_id: str,
560:         props: Dict[str, Any],
561:         beat_text: str,
562:         graph: Optional[EvidenceGraph],
563:         inconsistencies: List[VisualInconsistencyRecord],
564:     ) -> None:
565:         rows = props.get("comparison_rows", [])
566:         if not isinstance(rows, list):
567:             return
568: 
569:         lower_text = beat_text.lower()
570:         lower_synonyms = ["lower than", "less than", "smaller than", "below", "under", "worse than", "inferior to"]
571:         higher_synonyms = ["higher than", "greater than", "more than", "above", "better than", "superior to", "exceeded"]
572: 
573:         matched_lower = next((p for p in lower_synonyms if p in lower_text), None)
574:         matched_higher = next((p for p in higher_synonyms if p in lower_text), None)
575: 
576:         for r_idx, row in enumerate(rows):
577:             if isinstance(row, dict):
578:                 metric = row.get("metric", "")
579:                 val_a = row.get("val_a")
580:                 val_b = row.get("val_b")
581:                 num_a = val_a if isinstance(val_a, (int, float)) else self.parse_number_with_multiplier(str(val_a))
582:                 num_b = val_b if isinstance(val_b, (int, float)) else self.parse_number_with_multiplier(str(val_b))
583: 
584:                 if num_a is not None and num_b is not None:
585:                     # Case 1: val_a > val_b visually, but audio asserts lower relation
586:                     if num_a > num_b and matched_lower:
587:                         inconsistencies.append(...)
588:                     # Case 2: val_a < val_b visually, but audio asserts higher relation
589:                     elif num_a < num_b and matched_higher:
590:                         inconsistencies.append(...)
```

#### Empirical Counterexample 1: Multi-Predicate Narration
When executing:
```python
scene = {
    'scene_id': 'sc_multi_pred',
    'block_type': 'comparison_panel',
    'parameters': {
        'comparison_rows': [
            {'metric': 'Speed', 'val_a': 100, 'val_b': 50},
            {'metric': 'Cost', 'val_a': 20, 'val_b': 50},
        ]
    },
    'narration_text': 'Entity A operated higher than Entity B in speed, but was lower than Entity B in cost.'
}
report = verifier.verify_visuals([scene])
```
Observed output:
```
Passed: False
Verdicts/Inconsistencies count: 2
 - Comparison row 'Speed' shows Entity A higher than B (100 > 50), but audio asserts 'lower than'.
 - Comparison row 'Cost' shows Entity A lower than B (20 < 50), but audio asserts 'higher than'.
```
Both valid rows are rejected with fatal `VisualSeverity.BLOCK`.

#### Empirical Counterexample 2: Entity Subject Inversion
When executing:
```python
scene = {
    'scene_id': 'sc_entity_swap',
    'block_type': 'comparison_panel',
    'parameters': {
        'comparison_rows': [
            {'metric': 'Speed', 'val_a': 50, 'val_b': 100},
        ]
    },
    'narration_text': 'Entity B exceeded Entity A in speed.'
}
report = verifier.verify_visuals([scene])
```
Observed output:
```
Passed: False
 - Comparison row 'Speed' shows Entity A lower than B (50 < 100), but audio asserts 'exceeded'.
```
Valid visual rendering matching narration is blocked with `VisualSeverity.BLOCK`.

### 1.3 Quote Audit Logic (`src/epistemic/visual_verifier.py`, lines 700–731)
```python
700:     def _audit_quote(
701:         self,
702:         scene_id: str,
703:         props: Dict[str, Any],
704:         beat_text: str,
705:         graph: Optional[EvidenceGraph],
706:         inconsistencies: List[VisualInconsistencyRecord],
707:     ) -> None:
708:         vis_quote = str(props.get("quote_text", "")).strip()
709:         if not vis_quote:
710:             return
711: 
712:         author = str(props.get("author_name", "")).strip()
713:         if author and author.lower() not in beat_text.lower() and len(author) > 3:
714:             # Check if narration mentions a different author
715:             other_authors = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', beat_text)
716:             if other_authors and author not in other_authors:
717:                 inconsistencies.append(...)
```
#### Empirical Counterexample 3: Quote Attribution False Positive
When executing:
```python
scene = {
    'scene_id': 'sc_quote_false_pos',
    'block_type': 'quote_highlight',
    'parameters': {
        'quote_text': 'There is plenty of room at the bottom.',
        'author_name': 'Richard Feynman',
    },
    'narration_text': 'In December, the team celebrated the conceptual breakthrough.'
}
report = verifier.verify_visuals([scene])
```
Observed output:
```
Passed: False
 - VisualDiscrepancyType.QUOTE_ATTRIBUTION_MISMATCH : Quote attribution mismatch: Visual displays 'Richard Feynman', while voiceover names 'In December'.
```
Common time phrase `"In December"` is matched as a human author name and triggers fatal pipeline BLOCK.
Furthermore: `vis_quote` and `graph` are never referenced again in `_audit_quote`; on-screen quote text is completely unverified against the evidence graph.

### 1.4 Temporal Validity Bound Logic (`src/epistemic/visual_verifier.py`, lines 370–395)
```python
378:                         v_from = tc.get("valid_from") if isinstance(tc, dict) else getattr(tc, "valid_from", None)
379:                         v_until = tc.get("valid_until") if isinstance(tc, dict) else getattr(tc, "valid_until", None)
380:                         for py, m in parsed_years:
381:                             if v_from and py < int(v_from):
382:                                 inconsistencies.append(...)
```
`v_until` is extracted at line 379, but never evaluated. If `py > int(v_until)`, no discrepancy is appended.

### 1.5 Interface Class Export (`src/epistemic/numerical_pipeline.py`)
`PROJECT.md` line 99 specifies:
```
NumericalPipeline.verify_chart_data(dataset: NumericalDataset, chart_config: ChartConfig) -> NumericalVerificationResult
```
In `src/epistemic/numerical_pipeline.py`, the class is declared as `NumericalInvariantChecker`. There is no class or alias `NumericalPipeline`.

---

## 2. Findings

### [Critical] Finding 1: Comparison Panels Lack Multi-Predicate Support & Entity Reconciliation (Criterion 2 Failure)
- **Location**: `src/epistemic/visual_verifier.py:557-616` (`_audit_comparison_panel`)
- **Nature**: Heuristic shortcut / facade implementation failing Requirement 2.
- **Problem**:
  1. Compares global strings `matched_lower` and `matched_higher` extracted from the entire `beat_text` instead of metric-scoped or clause-segmented assertions.
  2. Any multi-row or multi-predicate comparison where narration contains both a "higher" and "lower" relation (e.g., "higher speed but lower cost") causes 100% of rows to be falsely rejected as `CHART_TREND_CONTRADICTION` with `VisualSeverity.BLOCK`.
  3. Direction is hardcoded to assume "Entity A" is always the subject and "Entity B" is the object. Statements such as "Entity B was higher than Entity A" or "Entity B exceeded Entity A" trigger false BLOCK errors.
  4. Omits support for canonical `VISUAL_FACT_CHECKING.md` Section 2.1 parameters (`left_val`, `right_val`, `delta_metric`, `dataset_binding_id`).
- **Remediation**:
  - Implement metric-scoped clause parsing or regex extraction that associates the comparative relation (higher/lower/better/worse) directly with the specific metric or entity.
  - Parse entity subjects (`entity_a`/`entity_b` or `left_label`/`right_label`) to correctly resolve directionality when Entity B is the grammatical subject.
  - Support `left_val` / `right_val` parameter aliases alongside `val_a` / `val_b`.

### [Major] Finding 2: Brittle Quote Attribution Regex Generates False-Positive Blocks & Quote Text is Unverified
- **Location**: `src/epistemic/visual_verifier.py:700-731` (`_audit_quote`)
- **Nature**: Algorithmic defect & dummy/unimplemented verification.
- **Problem**:
  1. The regex `r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'` matches capitalized words at sentence starts and proper nouns (e.g. "In December", "Bell Labs", "Silicon Valley"), falsely identifying them as conflicting authors and triggering fatal pipeline BLOCK.
  2. `vis_quote` is read but never verified against `graph` or primary source text. A completely fabricated quote with the correct author name passes visual fact-checking without error.
- **Remediation**:
  - Restrict voiceover author detection to explicit attribution patterns (e.g., `r'(?:stated by|according to|said|wrote|authored by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'`) or match against known entity nodes in `EvidenceGraph`.
  - Reconcile `vis_quote` against `EvidenceGraph` claim text or `ClaimType.DIRECT_QUOTE` nodes to detect visual quote fabrication.

### [Major] Finding 3: Missing Upper Bound Check on Temporal Context (`valid_until`)
- **Location**: `src/epistemic/visual_verifier.py:378-395` (`_audit_timeline`)
- **Nature**: Incomplete temporal validation.
- **Problem**:
  - Line 379 extracts `v_until`, but line 381 only checks `py < int(v_from)`. If a timeline milestone year exceeds `v_until`, it is silently ignored, allowing post-dated anachronisms to bypass the verifier.
- **Remediation**:
  - Add condition:
    ```python
    if v_until and py > int(v_until):
        inconsistencies.append(...)
    ```

### [Minor] Finding 4: Missing `NumericalPipeline` Export Alias
- **Location**: `src/epistemic/numerical_pipeline.py`
- **Nature**: Interface specification deviation from `PROJECT.md`.
- **Problem**:
  - `PROJECT.md` documents `NumericalPipeline.verify_chart_data`. The module exports `NumericalInvariantChecker` but does not alias `NumericalPipeline = NumericalInvariantChecker`.
- **Remediation**:
  - Add `NumericalPipeline = NumericalInvariantChecker` to `src/epistemic/numerical_pipeline.py` and `__all__`.

---

## 3. Logic Chain

1. **Premise 1**: Requirement 2 of the author request explicitly mandates:
   *"Comparison panels support multi-predicate checks and general entity reconciliation without hardcoded single-predicate limits."*
2. **Observation**: Code inspection of `src/epistemic/visual_verifier.py:569-590` shows:
   - `matched_lower` and `matched_higher` are evaluated once over the entire `beat_text`.
   - In any scene with both higher and lower comparative terms (multi-predicate), row evaluation checks `if num_a > num_b and matched_lower:` which triggers on the first branch regardless of metric relevance.
   - Any row where `num_a < num_b` hits `elif num_a < num_b and matched_higher:` and triggers a BLOCK.
3. **Empirical Proof**: Executing the verifier on a canonical 2-row multi-predicate scene ("Speed" 100 > 50, "Cost" 20 < 50, narration: "higher than in speed, but lower than in cost") fails with 2 false-positive BLOCK inconsistencies.
4. **Empirical Proof**: Executing the verifier on an inverted subject sentence ("Entity B exceeded Entity A in speed", visual: 50 vs 100) fails with a false-positive BLOCK inconsistency.
5. **Deduction**: The current implementation exhibits a single-predicate limit and hardcoded entity assumption that passes the 4 existing unit tests (which only tested single rows with single predicates) but fails on general multi-predicate inputs.
6. **Premise 2**: System instructions state:
   *"When reviewing work, actively check for integrity violations: Dummy or facade implementations that look correct but implement no real logic... If you detect ANY of these patterns, your verdict MUST be REQUEST_CHANGES."*
7. **Conclusion**: The implementation fails Requirement 2 and contains dummy/brittle checks in quote auditing and temporal checking. Changes must be requested before Milestone 4 gate approval.

---

## 4. Verified Claims & Strengths

Despite the findings above, significant portions of the implementation are well-engineered, robust, and verified:

1. **Numerical Pipeline Determinism**:
   - Ingestion handles messy tabular inputs, non-finite values (NaN, Inf), and verifies canonical SHA-256 hashes (`NumericalDatasetIngestion`).
   - `NumericalTransformer.calculate_percentage_shares` guarantees exact 100.00% sum across pathological splits (thirds, sevenths) using the Largest Remainder Method (Hare-Niemeyer).
   - `DeterministicChartRenderer` generates 100x bit-identical SVGs across BAR, LINE, and SCATTER charts.
   - Growth rate calculations correctly trap division-by-zero baselines.
2. **Timeline Monotonicity & Ancient Dates**:
   - BCE/BC, CE/AD, and negative integer astronomical years are parsed and ordered correctly.
   - Cross-scene timeline inversions are detected, respecting `flashback: True` exemptions.
3. **Bar Chart Zero-Baseline Anti-Distortion**:
   - Unjustified non-zero baselines in bar charts are rejected. Truncated baselines require explicit opt-in and rendered warning disclosures.
4. **Entity Count Heuristics**:
   - Distinguishes entity nouns (battalions, vessels, breakthroughs) from units/time (years, percent, dollars).
   - Scales severity appropriately (WARN for delta=1, BLOCK for delta>1).
5. **Trend Polarity Matching**:
   - Verbal sentiment analysis correctly correlates upward/downward vocabularies with chart coordinates.

---

## 5. Adversarial Challenge & Stress Test Results

| Challenge / Attack Scenario | Target Component | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| **Multi-predicate comparison narration** ("higher in X, but lower in Y") | `VisualVerifier._audit_comparison_panel` | Pass valid rows; evaluate each metric independently | Both rows falsely blocked with `CHART_TREND_CONTRADICTION` | **FAIL (Vulnerability)** |
| **Inverted subject entity comparison** ("Entity B exceeded Entity A") | `VisualVerifier._audit_comparison_panel` | Reconcile entity roles with `val_a`/`val_b` | Falsely blocked; assumes Entity A is always subject | **FAIL (Vulnerability)** |
| **Non-author capitalized phrase in narration** ("In December, ...") | `VisualVerifier._audit_quote` | Distinguish date/time phrase from author | Falsely blocked; treated "In December" as conflicting author | **FAIL (Vulnerability)** |
| **Milestone year past claim validity** (`py > valid_until`) | `VisualVerifier._audit_timeline` | Flag `TIMELINE_DATE_ANACHRONISM` | Silently passed without check | **FAIL (Vulnerability)** |
| **100x bit-identical SVG rendering** | `DeterministicChartRenderer` | Identical SHA-256 hash across 100 runs | Bit-identical across BAR, LINE, SCATTER | **PASS** |
| **NaN / Inf input injection** | `NumericalDataPoint`, `NumericalDatasetIngestion` | Raise `ValueError` on ingestion/instantiation | Strictly rejected with descriptive `ValueError` | **PASS** |
| **Hare-Niemeyer pathological splits** (thirds, sevenths, zero-values) | `NumericalTransformer.calculate_percentage_shares` | Exact 100.00% total sum | Exact 100.00% maintained | **PASS** |
| **BCE / negative year chronology inversion** | `VisualVerifier._audit_timeline` | Inversion detected (-44 before -500) | Inversion detected and blocked | **PASS** |
| **Bar chart non-zero baseline without disclosure** | `DeterministicChartRenderer`, `NumericalInvariantChecker` | Block with `CHART_BASELINE_TRUNCATION` | Correctly blocked | **PASS** |

---

## 6. Caveats

- The reviewer operated in review-only mode and did NOT modify implementation code files.
- The 60 existing tests in `tests/test_visual_verifier.py`, `tests/test_numerical_pipeline.py`, and `tests/test_m4_adversarial_challenger2.py` pass 100% because the existing tests only probed single-row, single-predicate comparison panels and did not include phrases like "In December" in quote test scenes.
- The adversarial counterexamples above were executed via isolated Python CLI executions against the runtime environment to prove reproducibility.

---

## 7. Conclusion

### Final Assessment
The numerical pipeline (`src/epistemic/numerical_pipeline.py`) is deterministic, mathematically rigorous, and adheres to data integrity principles. However, the visual verifier (`src/epistemic/visual_verifier.py`) contains critical flaws in comparison panel auditing (failing Requirement 2), brittle author extraction heuristics, and incomplete temporal/quote verification.

### Verdict
**REQUEST_CHANGES**

### Actionable Remediation Items
1. **Remediate `_audit_comparison_panel`**:
   - Scope comparative relations to individual metrics or clauses rather than matching globally across `beat_text`.
   - Implement entity subject resolution to allow statements like "Entity B exceeded Entity A".
   - Support `left_val` / `right_val` alongside `val_a` / `val_b`.
2. **Remediate `_audit_quote`**:
   - Restrict spoken author identification to contextual attribution patterns (`according to <Name>`, `said <Name>`) to avoid misidentifying capitalized temporal phrases like "In December" as authors.
   - Wire `vis_quote` verification to check against `graph` / `ClaimRecord` archival text.
3. **Remediate `_audit_timeline`**:
   - Enforce upper bound check `if v_until and py > int(v_until)` for temporal context anachronisms.
4. **Expose `NumericalPipeline`**:
   - Add `NumericalPipeline = NumericalInvariantChecker` in `src/epistemic/numerical_pipeline.py`.

---

## 8. Verification Method

To independently verify all findings and reproduction cases:

1. **Run Full Test Suite**:
   ```bash
   .venv\Scripts\pytest.exe tests/test_visual_verifier.py tests/test_numerical_pipeline.py tests/test_m4_adversarial_challenger2.py -v
   ```
2. **Reproduce Multi-Predicate Comparison Panel False-Positive Block**:
   ```bash
   .venv\Scripts\python.exe -c "from src.epistemic.visual_verifier import VisualVerifier; v = VisualVerifier(); sc = {'scene_id': 'sc1', 'block_type': 'comparison_panel', 'parameters': {'comparison_rows': [{'metric': 'Speed', 'val_a': 100, 'val_b': 50}, {'metric': 'Cost', 'val_a': 20, 'val_b': 50}]}, 'narration_text': 'Entity A was higher than Entity B in speed, but lower than Entity B in cost.'}; print(v.verify_visuals([sc]))"
   ```
   *Expectation*: `passed=False` with 2 false-positive BLOCK inconsistencies.
3. **Reproduce Entity Inversion False-Positive Block**:
   ```bash
   .venv\Scripts\python.exe -c "from src.epistemic.visual_verifier import VisualVerifier; v = VisualVerifier(); sc = {'scene_id': 'sc2', 'block_type': 'comparison_panel', 'parameters': {'comparison_rows': [{'metric': 'Speed', 'val_a': 50, 'val_b': 100}]}, 'narration_text': 'Entity B exceeded Entity A in speed.'}; print(v.verify_visuals([sc]))"
   ```
   *Expectation*: `passed=False` with false-positive BLOCK inconsistency.
4. **Reproduce Quote Attribution False-Positive Block**:
   ```bash
   .venv\Scripts\python.exe -c "from src.epistemic.visual_verifier import VisualVerifier; v = VisualVerifier(); sc = {'scene_id': 'sc3', 'block_type': 'quote_highlight', 'parameters': {'quote_text': 'Room at the bottom', 'author_name': 'Richard Feynman'}, 'narration_text': 'In December, the team celebrated.'}; print(v.verify_visuals([sc]))"
   ```
   *Expectation*: `passed=False` falsely asserting "In December" is the author.
