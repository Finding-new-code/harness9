# Milestone 4 Empirical Challenge & Stress-Test Handoff Report

**Agent**: `challenger_2_m4_gen9` (teamwork_preview_challenger)  
**Roles**: critic, specialist  
**Working Directory**: `g:\Finding-new-code\harness9\.agents\challenger_2_m4_gen9`  
**Target Modules**: `src/epistemic/visual_verifier.py`, `src/epistemic/numerical_pipeline.py`  
**Target Test Suites**: `tests/test_visual_verifier.py`, `tests/test_numerical_pipeline.py`, `tests/test_m4_adversarial_challenger2.py`  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1 Baseline Verification
The worker's implementations and baseline test suites were inspected and executed empirically:
- `uv run pytest tests/test_visual_verifier.py tests/test_numerical_pipeline.py -v`:
  Output: `============================= 31 passed in 10.82s =============================`
- Full baseline regression suite (`pytest tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py`):
  Output: `======================= 144 passed in 60.06s (0:01:00) ========================`

The baseline demonstrates solid foundational implementations for 100x bit-identical SVG chart rendering, zero-baseline anti-distortion on bar charts, Hare-Niemeyer Largest Remainder Method, and standard 4-digit CE chronological ordering.

### 1.2 Adversarial Challenge Empirical Execution
To stress-test the implementation against the 4 mandated challenge scenarios, a dedicated adversarial test suite was authored at `tests/test_m4_adversarial_challenger2.py`.
Execution command:
```bash
uv run pytest tests/test_m4_adversarial_challenger2.py -v
```
Verbatim test output:
```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collected 16 items

tests/test_m4_adversarial_challenger2.py::TestTimelineAndChronologyStress::test_timeline_chronology_inversion_positive_ce_detected PASSED [  6%]
tests/test_m4_adversarial_challenger2.py::TestTimelineAndChronologyStress::test_timeline_chronology_bce_string_inversion XFAIL [ 12%]
tests/test_m4_adversarial_challenger2.py::TestTimelineAndChronologyStress::test_timeline_negative_integer_year_inversion XFAIL [ 18%]
tests/test_m4_adversarial_challenger2.py::TestTimelineAndChronologyStress::test_cross_scene_out_of_order_chronology XFAIL [ 25%]
tests/test_m4_adversarial_challenger2.py::TestTimelineAndChronologyStress::test_conflicting_voiceover_vs_visual_dates PASSED [ 31%]
tests/test_m4_adversarial_challenger2.py::TestVisualChartTrendInversionStress::test_trend_inversion_plummeted_detected PASSED [ 37%]
tests/test_m4_adversarial_challenger2.py::TestVisualChartTrendInversionStress::test_trend_inversion_crashed_sentiment_detection XFAIL [ 43%]
tests/test_m4_adversarial_challenger2.py::TestVisualChartTrendInversionStress::test_bar_chart_non_zero_baseline_lacking_disclosure_blocked PASSED [ 50%]
tests/test_m4_adversarial_challenger2.py::TestVisualChartTrendInversionStress::test_numerical_invariant_checker_non_zero_baseline_violation PASSED [ 56%]
tests/test_m4_adversarial_challenger2.py::TestNumericalPipelinePrecisionAndDeterminism::test_100x_bit_identical_svg_rendering_stress PASSED [ 62%]
tests/test_m4_adversarial_challenger2.py::TestNumericalPipelinePrecisionAndDeterminism::test_nan_and_inf_input_injection_rejection PASSED [ 68%]
tests/test_m4_adversarial_challenger2.py::TestNumericalPipelinePrecisionAndDeterminism::test_nan_injection_in_uncertainty_range XFAIL [ 75%]
tests/test_m4_adversarial_challenger2.py::TestNumericalPipelinePrecisionAndDeterminism::test_hare_niemeyer_pathological_splits PASSED [ 81%]
tests/test_m4_adversarial_challenger2.py::TestEntityCountMismatchBoundaries::test_voiceover_dozens_vs_visual_five XFAIL [ 87%]
tests/test_m4_adversarial_challenger2.py::TestEntityCountMismatchBoundaries::test_singular_noun_count_boundary XFAIL [ 93%]
tests/test_m4_adversarial_challenger2.py::TestEntityCountMismatchBoundaries::test_exact_singular_plural_delta_one_severity PASSED [100%]

======================== 9 passed, 7 xfailed in 11.57s ========================
```

### 1.3 Forensic Code Inspections & Exact Failure Sites

#### Observation 1: BCE / Negative Year Regex Omission
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 283, 310, 605
- **Verbatim Code**:
  ```python
  raw_year = m.get("year", m.get("date", ""))
  y_match = re.search(r"\b(1\d{3}|20\d{2})\b", str(raw_year))
  if y_match:
      parsed_years.append((int(y_match.group(1)), m))
  ```
- **Observed Behavior**:
  The regex `r"\b(1\d{3}|20\d{2})\b"` matches strictly 4-digit years between 1000 and 2099 CE.
  - "44 BCE", "500 BCE", "300 BC", "-44", "-500" return `None`.
  - In an inverted BCE timeline (`[{"year": "44 BCE"}, {"year": "500 BCE"}]`), `len(parsed_years)` is 0 (< 2), so `_audit_timeline` silently skips the chronology check, allowing inverted historical timelines to publish unchecked.
  - If 4-digit BCE years are passed as positive numbers (e.g. 1200 BCE followed by 1500 BCE), the parser treats them as positive integers, falsely reporting correct chronological flow (1500 BCE -> 1200 BCE) as an inverted error.

#### Observation 2: Single-Scene Scope Omits Cross-Scene Chronological Validation
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 184–196 (`verify_visuals`)
- **Verbatim Code**:
  ```python
  for sc in scenes:
      sc_inconsistencies, elem_count = self.verify_scene(sc, graph, datasets)
      total_elements += elem_count
      all_inconsistencies.extend(sc_inconsistencies)
  ```
- **Observed Behavior**:
  `verify_visuals` audits scenes independently without maintaining narrative chronological state. If Scene 1 depicts 1995 and Scene 2 depicts 1970, `VisualVerifier` emits 0 discrepancies.

#### Observation 3: Sentiment Dictionary Omission for Negative Slopes ("crashed")
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 716–724
- **Verbatim Code**:
  ```python
  up_words = ["increase", "increased", "growing", "grew", "surged", "rose", "rising", "jumped", "upward", "doubled", "tripled"]
  down_words = ["decrease", "decreased", "fell", "falling", "dropped", "drop", "plummeted", "declined", "downturn", "loss", "lower"]
  ```
- **Observed Behavior**:
  "plummeted" is present in `down_words`, but "crashed", "crash", "collapsed", "collapse", "tanked", "slumped", "nosedived" are absent. When a visual chart depicts an upward trend ([10, 50, 100]) and the voiceover narrates "The market crashed to historic lows", `extract_trend_polarity` returns 0. The trend contradiction is silently ignored.

#### Observation 4: NaN Permitted in `uncertainty_range` of `NumericalDataPoint`
- **File**: `src/epistemic/numerical_pipeline.py`
- **Lines**: 60–68
- **Verbatim Code**:
  ```python
  @field_validator("uncertainty_range")
  @classmethod
  def validate_uncertainty(cls, v: Optional[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
      if v is not None:
          if len(v) != 2:
              raise ValueError("uncertainty_range must be a (min, max) tuple")
          if v[0] > v[1]:
              raise ValueError("uncertainty_range min must be <= max")
      return v
  ```
- **Observed Behavior**:
  Because in IEEE-754 semantics `float("nan") > 12.0` evaluates to `False`, `uncertainty_range=(float("nan"), 12.0)` bypasses validation. It serializes into `calculate_canonical_hash()` as `"nan:12.00000000"`, corrupting cryptographic dataset integrity.

#### Observation 5: "Dozens" and Singular Nouns Omitted from Entity Count Extraction
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 727–744
- **Verbatim Code**:
  ```python
  pattern = r'\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:key\s+|distinct\s+|major\s+)?(phases|breakthroughs|steps|pillars|innovations|models|categories|types|panels|components|factors)'
  ```
- **Observed Behavior**:
  1. The regex ignores colloquial/group quantifiers like "dozens", "scores", "hundreds". When voiceover narrates "Dozens of breakthroughs...", `extract_stated_entity_count` returns `None` and line 560 `if stated_cnt is None: return` skips visual count comparison against 5 visual panels.
  2. All entity nouns in the regex pattern are strictly plural (`breakthroughs`, `innovations`, `steps`). A spoken singular noun such as "one breakthrough" or "1 factor" fails to match, returning `None` and bypassing visual count discrepancy checks.

---

## 2. Logic Chain

1. **Premise 1 (Chronology & Ancient History)**:
   - Harness 9 enforces strict historical scholarship guidelines (ADR-006, Historical Scholarship Policy).
   - Historical timelines routinely feature BCE/BC dates and ancient dates prior to 1000 CE (Observation 1).
   - By constraining the year extraction regex to `r"\b(1\d{3}|20\d{2})\b"`, ancient dates and negative years are parsed as `None`.
   - Therefore, chronological inversions across BCE years and negative astronomical years bypass the verifier completely.
   - Furthermore, video productions contain multi-scene storyboards (Observation 2). Auditing scenes in isolation allows chronological jumps (1995 -> 1970) without cross-scene consistency checking.

2. **Premise 2 (Visual Chart Integrity & Vocabulary Coverage)**:
   - Chart-to-audio reconciliation requires detecting when narrator sentiment directly contradicts the data visual (Observation 3).
   - The test demonstrated that "plummeted" is caught, but "crashed" (the prompt's exact scenario) is missed because `down_words` lacks common financial/economic downturn terms.
   - Therefore, videos containing statements like "crypto crashed" or "the market crashed" accompanied by rising charts will pass visual QA without error.

3. **Premise 3 (Numerical Integrity & IEEE-754 Edge Cases)**:
   - `NumericalDataset` promises cryptographic tamper resistance and finite number guarantees (Observation 4).
   - While `y_value` finite validation is correctly implemented, `uncertainty_range` relied on `v[0] > v[1]`.
   - In Python, comparisons with `float("nan")` return `False`.
   - Therefore, NaN bounds successfully instantiate, contaminating `dataset_sha256`.

4. **Premise 4 (Entity Count Boundaries)**:
   - The dispatch specifically requested testing entity count boundaries: voiceover stating "dozens" vs visual containing 5, and singular vs plural counts (Observation 5).
   - The current regex in `extract_stated_entity_count` lacks "dozens" and requires plural suffixes on all nouns.
   - Consequently, both "dozens of breakthroughs" vs 5 images and "one breakthrough" vs 5 images bypass entity count auditing.

---

## 3. Caveats

1. **Raster vs Metadata Analysis**:
   - `VisualVerifier` operates on structured scene and component props (`parameters`, `milestones`, `data_points`, `image_paths`). It does not run OCR or YOLO object detection over raw MP4 pixel streams. This is the intended architecture at this layer (storyboard IR and parameter validation before expensive rendering).
2. **Non-Linear Narrative Intent**:
   - In cross-scene storytelling, flashbacks and non-linear narrative devices occur legitimately. Cross-scene chronology enforcement should distinguish intentional flashbacks (e.g. marked with flashback/retrospective beat tags) from accidental chronological inversions.
3. **Colloquial Quantifiers**:
   - "Dozens" represents an imprecise numerical range (typically 24+). While it clearly contradicts a small panel count like 3 or 5, an exact integer mapping (e.g. 12, 24, 36) requires either a fuzzy count validator or setting an expected lower bound (e.g. `>= 12`).

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

Milestone 4 is solidly structured and passes all its initial tests (189 passing across baseline + worker tests). However, adversarial stress-testing against the specific challenge scenarios revealed 5 concrete, reproducible functional gaps:

### Required Remediations for Worker:

1. **Remediation 1 (BCE & Ancient Timeline Parsing in `_audit_timeline`)**:
   - Update date extraction in `src/epistemic/visual_verifier.py` to parse BCE/BC years and negative numbers (e.g., `-?\d+\s*(?:BCE|BC|CE|AD)?` or helper converting BCE to negative integers).
   - Invert chronological order logic when comparing BCE years (where larger BCE year precedes smaller BCE year).
2. **Remediation 2 (Cross-Scene Chronological Continuity in `verify_visuals`)**:
   - Track `last_scene_max_year` across consecutive scenes in `verify_visuals`. If scene $N+1$ displays years strictly earlier than scene $N$ without an explicit `flashback` or `non_linear` property, emit a `TIMELINE_CHRONOLOGY_INVERSION` (or `WARN` severity).
3. **Remediation 3 (Expand Sentiment Polarities in `extract_trend_polarity`)**:
   - Add "crashed", "crash", "collapsed", "collapse", "tanked", "slumped", "nosedived", "plunged" to `down_words`.
   - Add "skyrocketed", "exploded", "boomed" to `up_words`.
4. **Remediation 4 (Finite Number Enforcement for `uncertainty_range`)**:
   - In `NumericalDataPoint.validate_uncertainty` in `src/epistemic/numerical_pipeline.py`, add explicit checks:
     ```python
     if math.isnan(v[0]) or math.isnan(v[1]) or math.isinf(v[0]) or math.isinf(v[1]):
         raise ValueError("uncertainty_range values must be finite numbers, not NaN or Inf")
     ```
5. **Remediation 5 (Quantifier & Singular Noun Support in `extract_stated_entity_count`)**:
   - Support "dozens" (mapping to expected count >= 12 or detecting conflict with visual counts < 12).
   - Make the noun list in `extract_stated_entity_count` support both singular and plural forms (e.g. `breakthrough|breakthroughs`, `innovation|innovations`, `step|steps`, `panel|panels`, `component|components`).

---

## 5. Verification Method

To independently verify these findings and confirm remediation:

### 5.1 Run Adversarial Challenge Suite
```bash
uv run pytest tests/test_m4_adversarial_challenger2.py -v
```
**Current Result**: `9 passed, 7 xfailed in 11.57s`  
(The 7 `xfailed` tests precisely reproduce the 5 gaps documented above).

### 5.2 Verification Post-Remediation
Upon implementing Remediations 1–5:
1. Remove `@pytest.mark.xfail` decorators from `tests/test_m4_adversarial_challenger2.py`.
2. Run:
   ```bash
   uv run pytest tests/test_m4_adversarial_challenger2.py -v
   ```
   **Target Outcome**: All 16 tests pass cleanly (`16 passed, 0 failed`).
3. Run full regression suite:
   ```bash
   uv run pytest tests/test_script_verifier.py tests/test_visual_verifier.py tests/test_numerical_pipeline.py tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py tests/test_m4_adversarial_challenger2.py
   ```
   **Target Outcome**: 205+ tests passing with 0 regressions.

### 5.3 Invalidation Conditions
- Any test failure in the baseline regression suite (144 tests).
- Inability to parse `44 BCE` or `-500` in visual timeline milestones.
- Missing `CHART_TREND_CONTRADICTION` when audio says "the market crashed" against an upward chart.
- Permitting `(float('nan'), 12.0)` in `NumericalDataPoint.uncertainty_range`.
- Permitting voiceover "dozens" vs visual count 5 without discrepancy notification.
