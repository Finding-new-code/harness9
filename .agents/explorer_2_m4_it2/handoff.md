# Milestone 4 Remediation Technical Investigation & Architecture Design Report

**Agent**: `explorer_2_m4_it2` (teamwork_preview_explorer)  
**Scope**: Technical Investigation & Remediation Architecture for `src/epistemic/visual_verifier.py` and `tests/test_visual_verifier.py`  
**Working Directory**: `g:\Finding-new-code\harness9\.agents\explorer_2_m4_it2`  
**Date**: 2026-09-14  

---

## 1. Observation

### 1.1 Baseline Test Environment & Current State
The existing test suites were executed independently in `g:\Finding-new-code\harness9` using Python 3.11:
- `pytest tests/test_visual_verifier.py`:
  * Output: **14 passed in 13.64s** (Exit code 0).
- `pytest tests/test_m4_adversarial_challenger2.py`:
  * Output: **9 passed, 7 xfailed in 6.24s** (Exit code 0).
  * 7 active `xfail` markers directly isolate the vulnerabilities identified by Challenger 2 and Forensic Auditor.

### 1.2 Direct Observations of the 7 Defect Sites

#### Defect 1: Over-Specialized Entity Count Regex (Forensic Auditor Finding 2)
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 733–742
- **Verbatim Code**:
  ```python
  pattern = r'\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:key\s+|distinct\s+|major\s+)?(phases|breakthroughs|steps|pillars|innovations|models|categories|types|panels|components|factors)'
  ```
- **Observed Failure**:
  The regex is constrained to a hardcoded list of exactly 11 nouns (`phases`, `breakthroughs`, `steps`, `pillars`, `innovations`, `models`, `categories`, `types`, `panels`, `components`, `factors`).
  * Direct Execution:
    - `VisualVerifier.extract_stated_entity_count("three battalions")` -> `None`
    - `VisualVerifier.extract_stated_entity_count("5 vessels")` -> `None`
    - `VisualVerifier.extract_stated_entity_count("Three distinct breakthroughs")` -> `3`
  Any general noun phrase describing quantities outside these 11 nouns returns `None`, bypassing count verification entirely.

#### Defect 2: Comparison Panel Validator Single-Predicate Restriction (Forensic Auditor Finding 3)
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 532–547
- **Verbatim Code**:
  ```python
  if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
      if val_a > val_b and "lower than" in beat_text.lower() and str(val_a) in beat_text:
          inconsistencies.append(...)
  ```
- **Observed Failure**:
  * Only checks `val_a > val_b` when the exact substring `"lower than"` is present.
  * Completely misses the inverse relation (`val_a < val_b` where audio states `"higher than"`).
  * Ignores standard comparative synonyms: `"less than"`, `"smaller than"`, `"below"`, `"under"`, `"worse than"`, `"greater than"`, `"more than"`, `"above"`, `"better than"`.
  * The requirement `and str(val_a) in beat_text` breaks when floating-point numbers are formatted differently in audio (e.g. `50.0` vs `"50"`) or when audio compares entities by name rather than repeating raw numbers.

#### Defect 3: Timeline Year Extraction Ignores BCE/BC & Negative Years (Challenger 2 GAP-1 & Reviewer 2 Finding 4)
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 283, 310, 605
- **Verbatim Code**:
  ```python
  raw_year = m.get("year", m.get("date", ""))
  y_match = re.search(r"\b(1\d{3}|20\d{2})\b", str(raw_year))
  if y_match:
      parsed_years.append((int(y_match.group(1)), m))
  ```
- **Observed Failure**:
  * The regex `r"\b(1\d{3}|20\d{2})\b"` matches only 4-digit years in [1000, 2099] CE.
  * Ancient timeline strings (`"44 BCE"`, `"500 BCE"`, `"300 BC"`) and negative astronomical integers (`-44`, `-500`) return `None`.
  * When `parsed_years` has fewer than 2 elements, `_audit_timeline` silently returns without checking chronology.
  * In `test_timeline_chronology_bce_string_inversion`, `[{"year": "44 BCE"}, {"year": "500 BCE"}]` (inversion: -44 placed before -500) passes undetected.

#### Defect 4: Single-Scene Scope Omits Cross-Scene Timeline Inversions (Challenger 2 GAP-2)
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 184–197 (`verify_visuals`)
- **Verbatim Code**:
  ```python
  for sc in scenes:
      sc_inconsistencies, elem_count = self.verify_scene(sc, graph, datasets)
      total_elements += elem_count
      all_inconsistencies.extend(sc_inconsistencies)
      ...
  ```
- **Observed Failure**:
  * `verify_visuals` audits each scene in isolation with no inter-scene temporal state.
  * If Scene 1 covers 1990–1995 and Scene 2 jumps back to 1970–1975 without an explicit non-linear narrative tag (`flashback` or `non_linear`), 0 discrepancies are emitted.
  * Reproducible in `test_cross_scene_out_of_order_chronology`.

#### Defect 5: Polarity Lexicon Omission of Critical Downturn Verbs (Challenger 2 GAP-3)
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 716–724
- **Verbatim Code**:
  ```python
  up_words = ["increase", "increased", "growing", "grew", "surged", "rose", "rising", "jumped", "upward", "doubled", "tripled"]
  down_words = ["decrease", "decreased", "fell", "falling", "dropped", "drop", "plummeted", "declined", "downturn", "loss", "lower"]
  ```
- **Observed Failure**:
  * Missing core market/economic downturn terms: `"crashed"`, `"crash"`, `"collapsed"`, `"collapse"`, `"tanked"`, `"plunged"`, `"slumped"`, `"nosedived"`.
  * In `test_trend_inversion_crashed_sentiment_detection`, an upward chart `[10, 50, 100]` with audio `"The market crashed to historic lows amidst the panic."` yields `down_score=0`, `up_score=0`, `extract_trend_polarity` returns 0, and no `CHART_TREND_CONTRADICTION` is emitted.

#### Defect 6: Missing "Dozens" Quantifier & Singular Noun Rejection in Entity Counts (Challenger 2 GAP-5)
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 727–743
- **Observed Failure**:
  1. Lexicon lacks `"dozens"` / `"dozen"` and regex lacks `(?:of\s+)`. Audio `"Dozens of breakthroughs..."` yields `extract_stated_entity_count -> None`, skipping visual count checks against 5 images (`test_voiceover_dozens_vs_visual_five`).
  2. The regex noun list strictly required plural suffixes (`breakthroughs`, `innovations`, `steps`). Singular phrases like `"One breakthrough..."` return `None`, skipping visual count checks against 5 images (`test_singular_noun_count_boundary`).

#### Defect 7: Missing Fallback to Referenced NumericalDataset (Reviewer 2 Finding 2)
- **File**: `src/epistemic/visual_verifier.py`
- **Lines**: 431–454
- **Verbatim Code**:
  ```python
  points = props.get("data_points") or props.get("chart_data") or []
  if isinstance(points, list) and len(points) >= 2:
  ```
- **Observed Failure**:
  When a scene declares `dataset_id="ds_rev"` bound to a verified `NumericalDataset` in `datasets`, but omits redundant raw `data_points` inside `props`, `points` defaults to `[]`. Consequently, `len(points) >= 2` evaluates to `False`, silently bypassing trend polarity and zero-baseline audits.

---

## 2. Logic Chain

1. **Premise & Policy Foundation**:
   - Harness 9 enforces strict multi-modal factual consistency and historical scholarship (ADR-006, `PROJECT.md`).
   - The Visual Fact-Checking Engine (`src/epistemic/visual_verifier.py`) must guarantee that rendered visuals (timelines, charts, comparison panels, entity collages) truthfully represent narration and ground-truth evidence.

2. **Entity Count Generalization (Items 1 & 6)**:
   - Limiting entity count nouns to 11 hardcoded words is an artificial constraint that failed forensic inspection.
   - Natural spoken narration references arbitrary entities (`battalions`, `vessels`, `prototypes`, `cards`).
   - Group quantifiers like `"dozens"` represent numbers well exceeding single-digit panels (e.g. 24 vs 5 panels).
   - Singular entities (`"one breakthrough"`) represent a count of 1.
   - By matching general noun tokens preceded by numbers/quantifiers and filtering out excluded time units (`years`, `months`, `days`), currencies (`dollars`, `euros`), and percentage terms, the verifier handles both general entity nouns and boundary quantifiers without false positives.

3. **Comparison Panel Invariant (Item 2)**:
   - A comparison panel visually expresses order relations ($A > B$ or $A < B$).
   - A factual contradiction occurs whenever the verbal assertion contradicts the visual relation.
   - Supporting both directions ($A > B$ with lower-synonyms, $A < B$ with higher-synonyms) creates a symmetrical, complete invariant check.

4. **Chronology & Ancient History (Items 3 & 4)**:
   - Historical timelines precede 1000 CE and include BCE dates.
   - In BCE notation, $500\text{ BCE}$ happened before $44\text{ BCE}$; mathematically, $-500 < -44$. Mapping BCE dates to negative integers allows standard monotonic progression logic (`y_curr <= y_next`) to catch inversions across both ancient and modern eras.
   - Narratives span multiple scenes. An unannounced temporal jump backwards across scene boundaries (e.g. 1995 $\to$ 1970) is an inversion unless explicitly declared as a flashback.

5. **Cross-Modal Trend Sentiment (Item 5)**:
   - Narrators frequently describe market or trend movements with high-impact verbs (`crashed`, `tanked`, `collapsed`, `plunged`).
   - Expanding `down_words` and `up_words` with word-boundary set intersection ensures reliable polarity detection while preventing partial-token false positives (e.g. `gain` in `against`).

6. **Dataset Referencing (Item 7)**:
   - In Production IR, scenes reference datasets by ID (`dataset_id`) to avoid redundant inline data payload duplication.
   - When `data_points` is omitted from scene parameters, extracting `x_value` and `y_value` from the referenced `NumericalDataset.data_points` ensures that trend and baseline checks execute on the verified dataset.

---

## 3. Caveats

1. **Flashbacks and Non-Linear Storytelling**:
   Cross-scene chronology checks must allow intentional non-linear narratives. Scenes tagged with `flashback: True`, `non_linear: True`, or `is_retrospective: True` in parameters must be exempted from cross-scene inversion errors.
2. **Colloquial Quantifiers**:
   `"dozens"` denotes an approximate multitude. Mapping `"dozens"` to 24 (or 12) serves as an effective deterministic count that correctly detects divergences against small panel counts (such as 3 or 5 images) without requiring non-deterministic probabilistic modeling.
3. **Truncated Baseline in Numerical Pipeline (Reviewer 2 Finding 1 / Challenger 2 GAP-4)**:
   While this investigation focuses on `src/epistemic/visual_verifier.py` and `tests/test_visual_verifier.py`, Worker should also be advised of the 1-line check in `NumericalDataPoint.validate_uncertainty` in `src/epistemic/numerical_pipeline.py` (`math.isnan / math.isinf`) to turn all 7 Challenger 2 adversarial tests green.

---

## 4. Conclusion & Actionable Fix Recommendations for Worker

### 4.1 Recommended Code Changes for `src/epistemic/visual_verifier.py`

#### Fix 1: Helper Functions for Year Parsing & Audio Year Extraction
Add the following helper methods to `VisualVerifier`:

```python
    @staticmethod
    def parse_year_value(val: Any) -> Optional[int]:
        """Parses BCE/BC, CE/AD, signed integers, and standard years into signed integers.
        BCE/BC years are mapped to negative integers (e.g., '44 BCE' -> -44, '500 BCE' -> -500).
        """
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return int(val)
        s = str(val).strip()
        if not s:
            return None

        # 1. Negative integer string, e.g. "-44", "-500"
        if re.match(r'^-\d+$', s):
            return int(s)

        # 2. Year with BCE or BC suffix (e.g., "44 BCE", "500 BC", "44 B.C.E.")
        bce_match = re.search(r'\b(\d+)\s*(?:bce|bc|b\.c\.e\.|b\.c\.)\b', s, re.IGNORECASE)
        if bce_match:
            return -int(bce_match.group(1))

        # 3. Year with CE or AD prefix/suffix (e.g., "476 AD", "1995 CE")
        ce_match = re.search(r'\b(\d+)\s*(?:ce|ad|c\.e\.|a\.d\.)\b', s, re.IGNORECASE)
        if ce_match:
            return int(ce_match.group(1))

        # 4. Pure integer digits string
        if s.isdigit():
            return int(s)

        # 5. Embedded 4-digit year in date string (e.g. "1947-06-15", "October 1954")
        m4 = re.search(r'\b(1\d{3}|20\d{2})\b', s)
        if m4:
            return int(m4.group(1))

        return None

    @staticmethod
    def extract_audio_years(text: str) -> List[int]:
        """Extracts spoken years including BCE/BC and CE into signed integers."""
        years: List[int] = []
        # 1. Look for BCE/BC years
        for m in re.finditer(r'\b(\d+)\s*(?:bce|bc|b\.c\.e\.|b\.c\.)\b', text, re.IGNORECASE):
            years.append(-int(m.group(1)))
        # 2. Look for CE/AD years
        for m in re.finditer(r'\b(\d+)\s*(?:ce|ad|c\.e\.|a\.d\.)\b', text, re.IGNORECASE):
            years.append(int(m.group(1)))
        # 3. Look for 4-digit years (not part of BCE/BC/CE/AD)
        for m in re.finditer(r'\b(1\d{3}|20\d{2})\b', text):
            val = int(m.group(1))
            if val not in years and -val not in years:
                years.append(val)
        return years
```

#### Fix 2: Update `_audit_timeline` in `src/epistemic/visual_verifier.py`
Replace lines 279–329 with:

```python
        parsed_years: List[Tuple[int, Dict[str, Any]]] = []
        for idx, m in enumerate(milestones):
            if isinstance(m, dict):
                raw_year = m.get("year", m.get("date", ""))
                y_val = self.parse_year_value(raw_year)
                if y_val is not None:
                    parsed_years.append((y_val, m))

        # A. Chronology Inversion Check
        for i in range(len(parsed_years) - 1):
            y_curr, m_curr = parsed_years[i]
            y_next, m_next = parsed_years[i + 1]
            if y_curr > y_next:
                inconsistencies.append(
                    VisualInconsistencyRecord(
                        scene_id=scene_id,
                        block_type="timeline_reveal",
                        parameter_key="milestones",
                        discrepancy_type=VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION,
                        severity=VisualSeverity.BLOCK,
                        visual_value=f"{y_curr} preceding {y_next}",
                        expected_value=f"{y_next} after {y_curr}",
                        explanation=(
                            f"Chronological inversion in scene '{scene_id}': Milestone '{m_curr.get('title')}' "
                            f"({y_curr}) is placed before '{m_next.get('title')}' ({y_next})."
                        ),
                        remediation_suggestion=f"Reorder timeline milestones so {y_curr} appears after {y_next}.",
                    )
                )

        # B. Spoken Audio Date Mismatch Check
        spoken_years = self.extract_audio_years(beat_text)
        if spoken_years and parsed_years:
            vis_year_set = {py[0] for py in parsed_years}
            for sy in spoken_years:
                if sy not in vis_year_set and not any(abs(sy - vy) <= 1 for vy in vis_year_set):
                    inconsistencies.append(
                        VisualInconsistencyRecord(
                            scene_id=scene_id,
                            block_type="timeline_reveal",
                            parameter_key="year",
                            discrepancy_type=VisualDiscrepancyType.VISUAL_AUDIO_TEMPORAL_MISMATCH,
                            severity=VisualSeverity.BLOCK,
                            visual_value=list(vis_year_set),
                            expected_value=sy,
                            audio_text_snippet=beat_text[:120],
                            explanation=f"Audio speaks of year {sy}, but timeline milestones only display {list(vis_year_set)}.",
                            remediation_suggestion=f"Align visual timeline milestones to cover year {sy}.",
                        )
                    )
```

#### Fix 3: Cross-Scene Timeline Sequence Audit in `verify_visuals`
In `verify_visuals`, track timeline state across scenes:

```python
    def verify_visuals(
        self,
        storyboard: Union[Script, Any, Dict[str, Any]],
        graph: Optional[EvidenceGraph] = None,
        script: Optional[Any] = None,
        datasets: Optional[Dict[str, NumericalDataset]] = None,
    ) -> VisualVerificationReport:
        """Executes full visual fact-checking audit across all scenes."""
        scenes = self._normalize_scenes(storyboard, script)
        all_inconsistencies: List[VisualInconsistencyRecord] = []
        scene_reports: List[SceneVisualReport] = []
        total_elements = 0

        last_timeline_scene_id: Optional[str] = None
        last_timeline_max_year: Optional[int] = None

        for sc in scenes:
            sc_inconsistencies, elem_count = self.verify_scene(sc, graph, datasets)
            total_elements += elem_count

            # Cross-scene timeline sequence audit
            sc_props = sc.get("parameters", {})
            sc_btype = sc.get("block_type", "")
            if sc_btype in ("timeline_reveal", "timeline") or "milestones" in sc_props:
                milestones = sc_props.get("milestones", [])
                if isinstance(milestones, list) and milestones:
                    sc_years = []
                    for m in milestones:
                        if isinstance(m, dict):
                            y_val = self.parse_year_value(m.get("year", m.get("date", "")))
                            if y_val is not None:
                                sc_years.append(y_val)
                    if sc_years:
                        sc_min_yr = min(sc_years)
                        sc_max_yr = max(sc_years)
                        is_flashback = bool(sc_props.get("flashback", False) or sc_props.get("non_linear", False))
                        if last_timeline_max_year is not None and sc_min_yr < last_timeline_max_year and not is_flashback:
                            cross_inversion = VisualInconsistencyRecord(
                                scene_id=sc["scene_id"],
                                block_type=sc_btype or "timeline_reveal",
                                parameter_key="milestones",
                                discrepancy_type=VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION,
                                severity=VisualSeverity.BLOCK,
                                visual_value=f"Scene '{last_timeline_scene_id}' ({last_timeline_max_year}) preceding Scene '{sc['scene_id']}' ({sc_min_yr})",
                                expected_value=f"Chronological continuity across scenes (year >= {last_timeline_max_year})",
                                explanation=(
                                    f"Cross-scene chronological inversion: Scene '{sc['scene_id']}' displays year {sc_min_yr}, "
                                    f"which is earlier than previous scene '{last_timeline_scene_id}' year {last_timeline_max_year}."
                                ),
                                remediation_suggestion="Reorder scenes or set 'flashback: True' to denote non-linear chronology.",
                            )
                            sc_inconsistencies.append(cross_inversion)
                        last_timeline_scene_id = sc["scene_id"]
                        last_timeline_max_year = sc_max_yr

            all_inconsistencies.extend(sc_inconsistencies)
            scene_reports.append(
                SceneVisualReport(
                    scene_id=sc["scene_id"],
                    scene_index=sc["scene_index"],
                    block_type=sc["block_type"],
                    passed=not any(i.severity == VisualSeverity.BLOCK for i in sc_inconsistencies),
                    inconsistencies=sc_inconsistencies,
                )
            )
```

#### Fix 4: Symmetrical Comparison Panel Validator (`_audit_comparison_panel`)
Replace lines 526–547 with:

```python
        lower_text = beat_text.lower()
        lower_synonyms = ["lower than", "less than", "smaller than", "below", "under", "worse than", "inferior to"]
        higher_synonyms = ["higher than", "greater than", "more than", "above", "better than", "superior to", "exceeded"]

        matched_lower = next((p for p in lower_synonyms if p in lower_text), None)
        matched_higher = next((p for p in higher_synonyms if p in lower_text), None)

        for r_idx, row in enumerate(rows):
            if isinstance(row, dict):
                metric = row.get("metric", "")
                val_a = row.get("val_a")
                val_b = row.get("val_b")
                num_a = val_a if isinstance(val_a, (int, float)) else self.parse_number_with_multiplier(str(val_a))
                num_b = val_b if isinstance(val_b, (int, float)) else self.parse_number_with_multiplier(str(val_b))

                if num_a is not None and num_b is not None:
                    # Case 1: val_a > val_b visually, but audio asserts lower relation
                    if num_a > num_b and matched_lower:
                        inconsistencies.append(
                            VisualInconsistencyRecord(
                                scene_id=scene_id,
                                block_type="comparison_panel",
                                parameter_key=f"comparison_rows[{r_idx}]",
                                discrepancy_type=VisualDiscrepancyType.CHART_TREND_CONTRADICTION,
                                severity=VisualSeverity.BLOCK,
                                visual_value=f"{val_a} > {val_b}",
                                expected_value=f"{val_a} < {val_b}",
                                audio_text_snippet=beat_text[:120],
                                explanation=f"Comparison row '{metric}' shows Entity A higher than B ({val_a} > {val_b}), but audio asserts '{matched_lower}'.",
                                remediation_suggestion="Align comparison row values to match voiceover narrative.",
                            )
                        )
                    # Case 2: val_a < val_b visually, but audio asserts higher relation
                    elif num_a < num_b and matched_higher:
                        inconsistencies.append(
                            VisualInconsistencyRecord(
                                scene_id=scene_id,
                                block_type="comparison_panel",
                                parameter_key=f"comparison_rows[{r_idx}]",
                                discrepancy_type=VisualDiscrepancyType.CHART_TREND_CONTRADICTION,
                                severity=VisualSeverity.BLOCK,
                                visual_value=f"{val_a} < {val_b}",
                                expected_value=f"{val_a} > {val_b}",
                                audio_text_snippet=beat_text[:120],
                                explanation=f"Comparison row '{metric}' shows Entity A lower than B ({val_a} < {val_b}), but audio asserts '{matched_higher}'.",
                                remediation_suggestion="Align comparison row values to match voiceover narrative.",
                            )
                        )
```

#### Fix 5: Dataset ID Fallback in Chart Audit (`_audit_chart`)
In `_audit_chart`, after line 452:

```python
        points = props.get("data_points") or props.get("chart_data") or []
        # Fallback to extracting data_points from referenced verified NumericalDataset
        if not points and ds is not None and hasattr(ds, "data_points") and ds.data_points:
            points = [{"x": p.x_value, "y": p.y_value, "label": p.label} for p in ds.data_points]
```

#### Fix 6: Expanded Polarity Lexicon with Token Boundary Matching (`extract_trend_polarity`)
Replace lines 713–725 with:

```python
    @staticmethod
    def extract_trend_polarity(text: str) -> int:
        """Determines verbal trend direction (+1=rising, -1=falling, 0=neutral/none)."""
        lower = text.lower()
        words_in_text = set(re.findall(r'\b[a-z]+\b', lower))

        up_words = {
            "increase", "increased", "increasing",
            "growing", "grew", "grow", "growth",
            "surged", "surging", "surge",
            "rose", "rising", "rise",
            "jumped", "jumping", "jump",
            "upward", "doubled", "tripled",
            "skyrocketed", "skyrocketing", "skyrocket",
            "exploded", "exploding",
            "boomed", "booming", "boom",
            "rallied", "rallying", "rally",
            "gained", "gaining", "gain", "gains",
        }
        down_words = {
            "decrease", "decreased", "decreasing",
            "fell", "falling", "fall",
            "dropped", "dropping", "drop",
            "plummeted", "plummeting", "plummet",
            "declined", "declining", "decline",
            "downturn", "loss", "losses", "lost", "lower",
            "crashed", "crashing", "crash",
            "collapsed", "collapsing", "collapse",
            "tanked", "tanking",
            "plunged", "plunging", "plunge",
            "slumped", "slumping", "slump",
            "nosedived", "nosediving", "nosedive",
        }

        up_score = len(up_words.intersection(words_in_text))
        down_score = len(down_words.intersection(words_in_text))
        if up_score > down_score:
            return 1
        elif down_score > up_score:
            return -1
        return 0
```

#### Fix 7: General Entity Count Regex Supporting "Dozens" & Singular Nouns (`extract_stated_entity_count`)
Replace lines 727–743 with:

```python
    @staticmethod
    def extract_stated_entity_count(text: str) -> Optional[int]:
        """Extracts spoken count assertions like 'three breakthroughs', 'three battalions',
        '5 vessels', 'one breakthrough', or 'dozens of breakthroughs'.
        """
        word_to_int = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "dozen": 12, "dozens": 24,
        }
        excluded_nouns = {
            "year", "years", "decade", "decades", "century", "centuries",
            "month", "months", "week", "weeks", "day", "days", "hour", "hours",
            "minute", "minutes", "second", "seconds", "percent", "percentage",
            "dollar", "dollars", "cent", "cents", "euro", "euros",
            "bce", "bc", "ce", "ad", "million", "billion", "trillion", "thousand",
            "times", "fold", "points", "point",
        }

        pattern = re.compile(
            r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|dozens|\d{1,3})\s+(?:of\s+)?(?:[a-zA-Z]{3,}\s+)?([a-zA-Z]{3,})\b',
            re.IGNORECASE
        )

        for m in pattern.finditer(text):
            raw_cnt = m.group(1).lower()
            noun = m.group(2).lower()
            if noun in excluded_nouns:
                continue
            if raw_cnt in word_to_int:
                return word_to_int[raw_cnt]
            if raw_cnt.isdigit():
                return int(raw_cnt)

        return None
```

---

### 4.2 Recommended New Test Classes for `tests/test_visual_verifier.py`

Worker should append the following test classes and methods to `tests/test_visual_verifier.py`:

```python
class TestComparisonPanelVerification:
    """Tests comparison panel order relations and synonym consistency."""

    def test_comparison_panel_lower_than_conflict_blocks(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_1",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Cost", "val_a": 100, "val_b": 50},
                ]
            },
            "narration_text": "Entity A cost significantly lower than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
            and i.severity == VisualSeverity.BLOCK
            for i in report.inconsistencies
        )

    def test_comparison_panel_higher_than_inverse_conflict_blocks(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_2",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Latency", "val_a": 10, "val_b": 50},
                ]
            },
            "narration_text": "Entity A latency was higher than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(
            i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION
            and i.severity == VisualSeverity.BLOCK
            for i in report.inconsistencies
        )

    def test_comparison_panel_synonyms_detected(self):
        verifier = VisualVerifier()
        # "worse than"
        scene = {
            "scene_id": "sc_comp_syn",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [{"metric": "Score", "val_a": 95, "val_b": 70}]
            },
            "narration_text": "Entity A scored worse than Entity B across tests.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False

    def test_comparison_panel_consistent_passes(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_comp_ok",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [{"metric": "Speed", "val_a": 100, "val_b": 50}]
            },
            "narration_text": "Entity A operated faster and higher than Entity B.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True


class TestAncientTimelineAndCrossSceneVerification:
    """Tests BCE timeline parsing and cross-scene sequence continuity."""

    def test_detect_bce_timeline_inversion(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_bce",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": "44 BCE", "title": "Caesar"},
                    {"year": "500 BCE", "title": "Republic"},
                ]
            },
            "narration_text": "From 500 BCE to 44 BCE, Rome evolved.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)

    def test_detect_negative_integer_timeline_inversion(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_neg",
            "block_type": "timeline_reveal",
            "parameters": {
                "milestones": [
                    {"year": -44, "title": "Later"},
                    {"year": -500, "title": "Earlier"},
                ]
            },
            "narration_text": "Ancient timeline.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)

    def test_detect_cross_scene_timeline_inversion(self):
        verifier = VisualVerifier()
        scenes = [
            {
                "scene_id": "sc_1",
                "scene_index": 1,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [{"year": "1990", "title": "A"}, {"year": "1995", "title": "B"}]
                },
                "narration_text": "1990 to 1995.",
            },
            {
                "scene_id": "sc_2",
                "scene_index": 2,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [{"year": "1970", "title": "C"}, {"year": "1975", "title": "D"}]
                },
                "narration_text": "1970 to 1975.",
            },
        ]
        report = verifier.verify_visuals(scenes)
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)

    def test_cross_scene_flashback_allowed(self):
        verifier = VisualVerifier()
        scenes = [
            {
                "scene_id": "sc_1",
                "scene_index": 1,
                "block_type": "timeline_reveal",
                "parameters": {
                    "milestones": [{"year": "1990", "title": "A"}, {"year": "1995", "title": "B"}]
                },
                "narration_text": "1990 to 1995.",
            },
            {
                "scene_id": "sc_2",
                "scene_index": 2,
                "block_type": "timeline_reveal",
                "parameters": {
                    "flashback": True,
                    "milestones": [{"year": "1970", "title": "C"}, {"year": "1975", "title": "D"}]
                },
                "narration_text": "Flashback to 1970.",
            },
        ]
        report = verifier.verify_visuals(scenes)
        assert not any(i.discrepancy_type == VisualDiscrepancyType.TIMELINE_CHRONOLOGY_INVERSION for i in report.inconsistencies)


class TestEntityCountGeneralizationAndBoundaries:
    """Tests general entity nouns, 'dozens', and singular noun counts."""

    def test_general_entity_nouns_battalions_and_vessels(self):
        verifier = VisualVerifier()
        # Voiceover says "three battalions" vs 5 images -> discrepancy
        scene_discrepancy = {
            "scene_id": "sc_bat_bad",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "Three battalions defended the mountain pass.",
        }
        report = verifier.verify_visuals([scene_discrepancy])
        assert any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report.inconsistencies)

        # Voiceover says "5 vessels" vs 5 images -> passes
        scene_ok = {
            "scene_id": "sc_ves_ok",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "5 vessels sailed across the Atlantic.",
        }
        report_ok = verifier.verify_visuals([scene_ok])
        assert not any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report_ok.inconsistencies)

    def test_dozens_quantifier_boundary(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_dozens",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "Dozens of breakthroughs transformed the entire scientific world.",
        }
        report = verifier.verify_visuals([scene])
        assert any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report.inconsistencies)

    def test_singular_noun_boundary(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_sing",
            "block_type": "reference_collage_hook",
            "parameters": {"image_paths": ["1.png", "2.png", "3.png", "4.png", "5.png"]},
            "narration_text": "One breakthrough transformed the field of solid state physics.",
        }
        report = verifier.verify_visuals([scene])
        assert any(i.discrepancy_type == VisualDiscrepancyType.VISUAL_COUNT_DISCREPANCY for i in report.inconsistencies)


class TestChartTrendVocabularyAndDatasetFallback:
    """Tests 'crashed' sentiment detection and dataset_id fallback."""

    def test_trend_inversion_crashed_detected(self):
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_crash",
            "block_type": "chart",
            "parameters": {
                "chart_data": [{"x": 1, "y": 10}, {"x": 2, "y": 50}, {"x": 3, "y": 100}],
            },
            "narration_text": "The market crashed to historic lows amidst the panic.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION for i in report.inconsistencies)

    def test_dataset_id_fallback_when_data_points_omitted(self, sample_source):
        verifier = VisualVerifier()
        ds = NumericalDataset(
            dataset_id="ds_sales_trend",
            title="Sales",
            data_points=[
                NumericalDataPoint(x_value=1, y_value=10.0),
                NumericalDataPoint(x_value=2, y_value=50.0),
                NumericalDataPoint(x_value=3, y_value=100.0),
            ],
            source_record=sample_source,
        )
        scene = {
            "scene_id": "sc_ds_fallback",
            "block_type": "chart",
            "parameters": {
                "dataset_id": "ds_sales_trend",
                # Note: data_points omitted
            },
            "narration_text": "Revenues fell precipitously and dropped sharply over the year.",
        }
        report = verifier.verify_visuals([scene], datasets={"ds_sales_trend": ds})
        assert report.passed is False
        assert any(i.discrepancy_type == VisualDiscrepancyType.CHART_TREND_CONTRADICTION for i in report.inconsistencies)
```

---

## 5. Verification Method

To independently verify this investigation and validate the remediation once implemented by Worker:

1. **Verify Existing Tests Pass**:
   ```bash
   .venv\Scripts\pytest.exe tests/test_visual_verifier.py -v
   ```
   *Expected Current*: 14 passed.
   *Expected Post-Remediation*: 24+ passed (with new test classes).

2. **Verify Adversarial Challenge Suite**:
   ```bash
   .venv\Scripts\pytest.exe tests/test_m4_adversarial_challenger2.py -v
   ```
   *Expected Current*: 9 passed, 7 xfailed.
   *Expected Post-Remediation*: 15 passed, 1 xfailed (or 16 passed if `NumericalDataPoint.validate_uncertainty` NaN check is applied, removing xfail marks).

3. **Verify Baseline Regression Suite**:
   ```bash
   .venv\Scripts\pytest.exe tests/test_historical_policy.py tests/test_verification_engine.py tests/test_evidence_graph.py tests/test_contracts.py tests/test_state_machine.py tests/test_h9_acceptance.py -q
   ```
   *Expected*: 144 passed, 0 regressions.

4. **Invalidation Conditions**:
   - `extract_stated_entity_count("three battalions")` returning `None`.
   - `extract_stated_entity_count("5 vessels")` returning `None`.
   - `extract_stated_entity_count("One breakthrough")` returning `None`.
   - `extract_stated_entity_count("Dozens of breakthroughs")` returning `None`.
   - Comparison row with `val_a = 50 < val_b = 100` and voiceover `"higher than"` failing to flag `CHART_TREND_CONTRADICTION`.
   - Upward chart with audio `"the market crashed"` failing to flag `CHART_TREND_CONTRADICTION`.
   - Timeline with milestones `[{"year": "44 BCE"}, {"year": "500 BCE"}]` failing to flag `TIMELINE_CHRONOLOGY_INVERSION`.
   - Multi-scene storyboard with Scene 1 in 1995 and Scene 2 in 1970 failing to flag `TIMELINE_CHRONOLOGY_INVERSION`.
   - Scene referencing `dataset_id` without inline `data_points` skipping chart trend/baseline checks.
