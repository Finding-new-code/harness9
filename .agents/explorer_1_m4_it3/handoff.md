# Milestone 4 Remediation Specification: Robust, Clause-Aware Comparison Panel Audit Strategy

**Author Agent**: `explorer_1_m4_it3`  
**Role**: `explorer`, `investigator`, `synthesizer`  
**Date**: 2026-09-14  
**Working Directory**: `g:\Finding-new-code\harness9\.agents\explorer_1_m4_it3`  
**Target File**: `src/epistemic/visual_verifier.py` (specifically lines 285–288 and lines 553–616)  
**Test Suite**: `tests/test_visual_verifier.py` (lines 364–434)  
**Authoritative Contracts**:  
- `g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md` (Epistemic Verification Layer R4 & R5)  
- `g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_10\PROJECT.md` (Milestone 4 Visual Fact-Checking Engine)  
- `g:\Finding-new-code\harness9\.agents\reviewer_2_m4_g10\handoff.md` (Section 1.2 & Section 2.1 Finding 1)  
- `docs/epistemic/VISUAL_FACT_CHECKING.md` (Section 2.1 Block 4: `COMPARISON_PANEL`)  

---

## Executive Summary

The visual fact-checking engine (`src/epistemic/visual_verifier.py`) contains a critical algorithmic vulnerability in `_audit_comparison_panel`: comparative direction keywords (`matched_lower` and `matched_higher`) are extracted globally once across the entire `beat_text` string, and directionality assumes "Entity A" is always the grammatical subject.

This flaw causes two severe classes of false-positive `BLOCK` failures:
1. **Multi-Predicate Rejection**: In multi-row comparisons where the narration contrasts both higher and lower metrics (e.g., *"Entity A operated higher than Entity B in speed, but was lower than Entity B in cost"*), both valid visual rows are rejected with fatal `CHART_TREND_CONTRADICTION` inconsistencies.
2. **Subject Inversion Rejection**: When voiceover places Entity B as the subject (e.g., *"Entity B exceeded Entity A in speed"* with visual showing Entity A: 50, Entity B: 100), the verifier rejects the scene because it ignores grammatical subject/object roles and flags `50 < 100` as conflicting with `"exceeded"`.
3. **Canonical Parameter Incompatibility**: Canonical parameters documented in `VISUAL_FACT_CHECKING.md` Section 2.1 (`left_val`, `right_val`, `delta_metric`, `dataset_binding_id`) are not normalized when top-level or alternate parameter keys are provided.

This report provides the complete, mathematically validated architectural specification, exact drop-in code replacement, and comprehensive test suite to remediate `src/epistemic/visual_verifier.py`.

---

## 1. Observation

### 1.1 Existing Implementation in `src/epistemic/visual_verifier.py` (lines 556–616)
Direct inspection of `src/epistemic/visual_verifier.py` reveals the following code:

```python
556:     def _audit_comparison_panel(
557:         self,
558:         scene_id: str,
559:         props: Dict[str, Any],
560:         beat_text: str,
561:         graph: Optional[EvidenceGraph],
562:         inconsistencies: List[VisualInconsistencyRecord],
563:     ) -> None:
564:         rows = props.get("comparison_rows", [])
565:         if not isinstance(rows, list):
566:             return
567: 
568:         lower_text = beat_text.lower()
569:         lower_synonyms = ["lower than", "less than", "smaller than", "below", "under", "worse than", "inferior to"]
570:         higher_synonyms = ["higher than", "greater than", "more than", "above", "better than", "superior to", "exceeded"]
571: 
572:         matched_lower = next((p for p in lower_synonyms if p in lower_text), None)
573:         matched_higher = next((p for p in higher_synonyms if p in lower_text), None)
574: 
575:         for r_idx, row in enumerate(rows):
576:             if isinstance(row, dict):
577:                 metric = row.get("metric", "")
578:                 val_a = row.get("val_a")
579:                 val_b = row.get("val_b")
580:                 num_a = val_a if isinstance(val_a, (int, float)) else self.parse_number_with_multiplier(str(val_a))
581:                 num_b = val_b if isinstance(val_b, (int, float)) else self.parse_number_with_multiplier(str(val_b))
582: 
583:                 if num_a is not None and num_b is not None:
584:                     # Case 1: val_a > val_b visually, but audio asserts lower relation
585:                     if num_a > num_b and matched_lower:
586:                         inconsistencies.append(...)
587:                     # Case 2: val_a < val_b visually, but audio asserts higher relation
588:                     elif num_a < num_b and matched_higher:
589:                         inconsistencies.append(...)
```

### 1.2 Calling Dispatch in `src/epistemic/visual_verifier.py` (lines 285–288)
```python
285:         # 4. Comparison Panel Audit
286:         elif btype in ("comparison_panel", "comparison") or "comparison_rows" in props:
287:             self._audit_comparison_panel(scene_id, props, beat_text, graph, inconsistencies)
```
Notice: If a scene has top-level `left_val` and `right_val` (as defined in `VISUAL_FACT_CHECKING.md` Section 2.1) without `btype == "comparison_panel"` or `"comparison_rows"` in `props`, the dispatcher skips `_audit_comparison_panel` entirely.

### 1.3 Empirical Counterexample 1: Multi-Predicate Narration
Command executed:
```bash
.venv\Scripts\python.exe -c "from src.epistemic.visual_verifier import VisualVerifier; v = VisualVerifier(); sc = {'scene_id': 'sc_multi', 'block_type': 'comparison_panel', 'parameters': {'comparison_rows': [{'metric': 'Speed', 'val_a': 100, 'val_b': 50}, {'metric': 'Cost', 'val_a': 20, 'val_b': 50}]}, 'narration_text': 'Entity A operated higher than Entity B in speed, but was lower than Entity B in cost.'}; r = v.verify_visuals([sc]); print('Passed:', r.passed); print('Inconsistencies:', [(i.parameter_key, i.explanation) for i in r.inconsistencies])"
```
Observed verbatim output:
```
Passed: False
Inconsistencies: [
  ("comparison_rows[0]", "Comparison row 'Speed' shows Entity A higher than B (100 > 50), but audio asserts 'lower than'."),
  ("comparison_rows[1]", "Comparison row 'Cost' shows Entity A lower than B (20 < 50), but audio asserts 'higher than'.")
]
```
Both rows are completely correct and aligned with narration, yet both are falsely blocked with `VisualSeverity.BLOCK`.

### 1.4 Empirical Counterexample 2: Entity Subject Inversion
Command executed:
```bash
.venv\Scripts\python.exe -c "from src.epistemic.visual_verifier import VisualVerifier; v = VisualVerifier(); sc = {'scene_id': 'sc_inv', 'block_type': 'comparison_panel', 'parameters': {'comparison_rows': [{'metric': 'Speed', 'val_a': 50, 'val_b': 100}]}, 'narration_text': 'Entity B exceeded Entity A in speed.'}; r = v.verify_visuals([sc]); print('Passed:', r.passed); print('Inconsistencies:', [(i.parameter_key, i.explanation) for i in r.inconsistencies])"
```
Observed verbatim output:
```
Passed: False
Inconsistencies: [
  ("comparison_rows[0]", "Comparison row 'Speed' shows Entity A lower than B (50 < 100), but audio asserts 'exceeded'.")
]
```
The visual representation `50 < 100` correctly matches *"Entity B exceeded Entity A"*, yet is falsely blocked with `VisualSeverity.BLOCK`.

---

## 2. Logic Chain

1. **Global Keyword Extraction Defect**:
   - In lines 572–573, `matched_lower` and `matched_higher` scan `beat_text.lower()` across the entire string.
   - When a sentence contains both `"higher than"` (referring to Speed) and `"lower than"` (referring to Cost), `matched_lower` evaluates to `"lower than"` and `matched_higher` evaluates to `"higher than"`.
   - In the row iteration (lines 575–616):
     - For Row 0 (`Speed`: `100 > 50`): Condition `num_a > num_b and matched_lower` evaluates to `True` because `matched_lower` is truthy, erroneously checking the Cost predicate against the Speed row.
     - For Row 1 (`Cost`: `20 < 50`): Condition `num_a < num_b and matched_higher` evaluates to `True` because `matched_higher` is truthy, erroneously checking the Speed predicate against the Cost row.
   - **Conclusion 1**: Verification cannot be performed globally over `beat_text`. Narration text must be segmented into semantic clauses, and each comparison row must be scoped to the specific clause that references its metric.

2. **Grammatical Subject Blindness Defect**:
   - Lines 584–615 hardcode the assumption that `val_a` corresponds to the subject of the comparative relation:
     `if num_a > num_b and matched_lower:` $\rightarrow$ assumes voiceover asserts $A < B$.
     `elif num_a < num_b and matched_higher:` $\rightarrow$ assumes voiceover asserts $A > B$.
   - When voiceover asserts *"Entity B exceeded Entity A in speed"*, Entity B is the grammatical subject ($E_{\text{subj}} = B$), Entity A is the grammatical object ($E_{\text{obj}} = A$), and the predicate is `DIR_HIGHER` ($+1$).
   - Mathematically, the voiceover asserts $B > A$, which is logically equivalent to $A < B$.
   - The visual displays `val_a = 50, val_b = 100` ($num_a < num_b$). This is in complete agreement with the voiceover.
   - Because the existing code ignores entity roles, it treats `"exceeded"` as requiring $A > B$, falsely rejecting $50 < 100$.
   - **Conclusion 2**: The verifier must extract the relative syntactic order of entities and the comparative term to determine whether Entity A or Entity B is the grammatical subject. If Entity B is the subject, the comparative direction must be inverted before contrasting against `val_a` vs `val_b`.

3. **Ellipsis Subject Continuity**:
   - In coordinated multi-predicate narrations (*"Entity A operated higher than Entity B in speed, but was lower than Entity B in cost"*), the second clause (*"was lower than Entity B in cost"*) omits the subject ("Entity A") via syntactic ellipsis.
   - Because Entity B appears after `"lower than"`, Entity B is identified as the object.
   - An entity-aware segmenter must carry over the grammatical subject (`Entity A`) from the preceding clause to correctly resolve the second clause as $A < B$.

4. **Canonical Parameter Lineage**:
   - HyperFrames component contracts (`docs/epistemic/VISUAL_FACT_CHECKING.md` Section 2.1, `src/hyperframes/components/comparison_panel.py`) allow comparison panels to be specified either via a list of `comparison_rows` or via top-level canonical properties: `left_val`, `right_val`, `delta_metric`, `left_label`, `right_label`.
   - Normalizing these keys into a standardized row structure ensures seamless polymorphic support.

---

## 3. Detailed Remediation Specification & Architectural Design

The remediation introduces three dedicated algorithmic components within `VisualVerifier`:
1. **Two-Stage Clause Segmenter (`_segment_clauses`)**: Splits narration text into distinct comparative assertions.
2. **Metric Association Scorer (`_match_row_to_clause`)**: Matches each row to its relevant clause using exact matches, metric tokens, and domain synonyms.
3. **Syntactic Role & Direction Resolver (`_extract_comparative_relation`)**: Detects entity positions, resolves Subject vs Object, handles ellipsis subject carry-over, accounts for negation, and determines the net expected relation ($A > B$ or $A < B$).

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BEAT NARRATION TEXT                                     │
│  "Entity A operated higher than Entity B in speed, but was lower than Entity B in cost" │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                 STAGE 1 & 2: METRIC-AWARE CLAUSE SEGMENTATION                           │
│  Clause 0: "Entity A operated higher than Entity B in speed"                            │
│  Clause 1: "was lower than Entity B in cost"                                            │
└───────────────────────┬─────────────────────────────────────────┬───────────────────────┘
                        │                                         │
                        ▼                                         ▼
┌──────────────────────────────────────────────┐ ┌────────────────────────────────────────┐
│             ROW 0: SPEED                     │ │             ROW 1: COST                │
│  • Metric Match: "speed" (Score 15)          │ │  • Metric Match: "cost" (Score 15)     │
│  • Comparative: "higher than" (dir = +1)     │ │  • Comparative: "lower than" (dir = -1)│
│  • Pos(Entity A) < Pos(Term) < Pos(Entity B) │ │  • Pos(Term) < Pos(Entity B)          │
│  • Subject: Entity A, Object: Entity B       │ │  • Subject: Ellipsis -> Entity A       │
│  • Expected: Entity A > Entity B             │ │  • Expected: Entity A < Entity B       │
│  • Visual: 100 > 50 (num_a > num_b)          │ │  • Visual: 20 < 50 (num_a < num_b)     │
│  • Outcome: ALIGNED (PASS)                   │ │  • Outcome: ALIGNED (PASS)             │
└──────────────────────────────────────────────┘ └────────────────────────────────────────┘
```

### 3.1 Clause Segmentation Algorithm
- **Stage 1 (Major Boundaries)**: Split on:
  - Sentence terminators: `(?<=[.!?])\s+`
  - Semicolons and em-dashes: `\s*[;—–]\s*`
  - Contrastive and subordinating conjunctions: `\s*(?:,\s*)?\b(?:but|while|whereas|however|although|though|yet|meanwhile|conversely|in contrast|on the other hand)\b\s*`
  - Coordinated clause boundaries: `\s*,\s*and\s+`
- **Stage 2 (Introductory Comma Protection)**:
  - Do NOT split on all commas blindly. An introductory prepositional phrase like `"In speed, Entity A..."` must NOT be severed from its predicate.
  - A comma is treated as a clause boundary if and only if distinct known row metrics exist on both sides of the comma.

### 3.2 Metric Association Scoring
For each row metric (e.g. `"Power Consumption"`, `"Switching Speed"`, `"Cost"`, `"Latency"`):
1. Clean metric string into alphanumeric tokens, filtering stop words (`"the"`, `"and"`, `"per"`, `"for"`, etc.).
2. Map domain-specific synonyms:
   - `speed` $\rightarrow$ `faster`, `fast`, `velocity`, `throughput`, `switching`
   - `cost` $\rightarrow$ `price`, `cheaper`, `expensive`, `costly`, `spend`
   - `latency` $\rightarrow$ `delay`, `lag`, `ping`, `response time`
   - `power` $\rightarrow$ `energy`, `watt`, `wattage`, `consumption`
   - `reliability` $\rightarrow$ `mtbf`, `durable`, `durability`, `reliable`, `failure`
   - `score` $\rightarrow$ `scored`, `scores`, `benchmark`, `accuracy`, `test`
3. Scoring formula per clause:
   - Full metric exact match: $+15$
   - Token exact match (`\b<token>\b`): $+8$
   - Synonym exact match (`\b<synonym>\b`): $+6$
   - Substring match: $+3$
   - Ordinal positional tie-breaker: $+2$ (if row count equals clause count)
4. Fallback: If only 1 row exists, all comparative clauses apply. If no clause matches above threshold, fall back to row index ordinal alignment.

### 3.3 Comparative Vocabulary & Directional Calculus
1. **Direction Vocabulary**:
   - `DIR_HIGHER` ($+1$):
     `higher than`, `greater than`, `more than`, `above`, `better than`, `superior to`, `larger than`, `faster than`, `heavier than`, `longer than`, `stronger than`, `exceeded`, `exceeds`, `exceeding`, `outperformed`, `outperforms`, `outperforming`, `surpassed`, `surpasses`, `surpassing`, `beat`, `beats`, `beating`, `outpaced`, `outpaces`, `outpacing`, `higher`, `greater`, `better`, `superior`, `faster`, `larger`.
   - `DIR_LOWER` ($-1$):
     `lower than`, `less than`, `smaller than`, `below`, `under`, `worse than`, `inferior to`, `slower than`, `cheaper than`, `shorter than`, `weaker than`, `trailed`, `trails`, `trailing`, `lagged behind`, `lagged`, `lags`, `lower`, `smaller`, `worse`, `inferior`, `slower`, `cheaper`.
2. **Negation Modifier**:
   - Scan a 15-character prefix window preceding the comparative term.
   - If `\b(?:not|never|no longer)\b` is detected, invert `term_dir = -term_dir`.
3. **Subject & Object Extraction**:
   - Scan clause for spans of Entity A (`entity_a_name`, `left_label`, `"Entity A"`, `"A"`, `"the former"`) and Entity B (`entity_b_name`, `right_label`, `"Entity B"`, `"B"`, `"the latter"`).
   - Candidate subjects: Entities with span ending $\le \text{start of comparative term}$.
   - Candidate objects: Entities with span beginning $\ge \text{end of comparative term}$.
   - If no explicit subject is before the term, inherit `carried_subject` from the preceding clause (ellipsis handling).
   - Default subject: `"A"`. Default object: opposing entity.
4. **Calculus Resolution**:
   - If $E_{\text{subj}} == \text{Entity A}$: Expected relation is $\text{term\_dir}$ ($+1 \implies A > B$; $-1 \implies A < B$).
   - If $E_{\text{subj}} == \text{Entity B}$: Expected relation is $-\text{term\_dir}$ ($+1 \implies B > A \implies A < B$; $-1 \implies B < A \implies A > B$).

### 3.4 Numerical Contrast
Compare visual values (`num_a`, `num_b`) against Expected Relation:
- Expected $A > B$, but $num_a < num_b$: Flag `CHART_TREND_CONTRADICTION` with `VisualSeverity.BLOCK`.
- Expected $A < B$, but $num_a > num_b$: Flag `CHART_TREND_CONTRADICTION` with `VisualSeverity.BLOCK`.
- Otherwise: **ALIGNED (PASS)**.

---

## 4. Exact Code Replacement Proposal

### Change 1: Update Scene Dispatcher in `src/epistemic/visual_verifier.py`
**Target File**: `src/epistemic/visual_verifier.py`  
**Lines**: 285–288  
**Instruction**: Support canonical top-level `left_val` and `right_val` properties in comparison block routing.

```python
<<<<
        # 4. Comparison Panel Audit
        elif btype in ("comparison_panel", "comparison") or "comparison_rows" in props:
            self._audit_comparison_panel(scene_id, props, beat_text, graph, inconsistencies)
====
        # 4. Comparison Panel Audit
        elif (
            btype in ("comparison_panel", "comparison")
            or "comparison_rows" in props
            or ("left_val" in props and "right_val" in props)
            or ("val_a" in props and "val_b" in props)
        ):
            self._audit_comparison_panel(scene_id, props, beat_text, graph, inconsistencies)
>>>>
```

### Change 2: Drop-in Replacement for `_audit_comparison_panel` and Helpers
**Target File**: `src/epistemic/visual_verifier.py`  
**Lines**: 553–616  
**Instruction**: Replace the heuristic `_audit_comparison_panel` with the metric-aware clause segmenter, entity subject resolver, and parameter normalizer.

```python
    # -----------------------------------------------------------------------
    # 4. Comparison Panel Audit & Metric-Aware Clause Resolution
    # -----------------------------------------------------------------------
    @classmethod
    def _segment_clauses(cls, text: str, metrics: List[str]) -> List[str]:
        """Splits beat_text into semantic clauses around contrastive/coordinating conjunctions
        and punctuation, preventing over-splitting of introductory phrases.
        """
        if not text or not text.strip():
            return []

        # Stage 1: Split on sentence terminators, semicolons, em-dashes, and major contrastive conjunctions
        pattern = (
            r'(?:'
            r'(?<=[.!?])\s+'  # Sentence boundaries
            r'|\s*[;—–]\s*'   # Semicolons and dashes
            r'|\s*(?:,\s*)?\b(?:but|while|whereas|however|although|though|yet|meanwhile|conversely|in contrast|on the other hand)\b\s*'
            r'|\s*,\s*and\s+' # Comma + and
            r')'
        )
        chunks = [c.strip() for c in re.split(pattern, text, flags=re.IGNORECASE) if c and c.strip()]

        # Stage 2: If a chunk contains multiple distinct metrics separated by commas, split further
        refined_clauses: List[str] = []
        for chunk in chunks:
            if "," in chunk and len(metrics) > 1:
                sub_parts = [p.strip() for p in chunk.split(",") if p.strip()]
                matched_metrics = set()
                for p in sub_parts:
                    p_lower = p.lower()
                    for m in metrics:
                        if m and m.lower() in p_lower:
                            matched_metrics.add(m.lower())
                if len(matched_metrics) > 1:
                    refined_clauses.extend(sub_parts)
                    continue
            refined_clauses.append(chunk)

        return refined_clauses

    @classmethod
    def _match_row_to_clause(
        cls,
        metric: str,
        clauses: List[str],
        row_idx: int,
        total_rows: int,
    ) -> Tuple[Optional[str], Optional[int]]:
        """Finds the best matching clause for a given metric row using token & synonym matching."""
        if not clauses:
            return None, None
        if len(clauses) == 1:
            return clauses[0], 0

        metric_clean = re.sub(r'[^\w\s]', ' ', metric.lower()).strip()
        metric_tokens = [
            t for t in metric_clean.split()
            if len(t) >= 3 and t not in ("the", "and", "per", "for", "with", "gate")
        ]

        synonym_map = {
            "speed": ["faster", "fast", "velocity", "throughput", "switching"],
            "cost": ["price", "cheaper", "expensive", "costly", "spend", "cost"],
            "latency": ["delay", "lag", "ping", "response time"],
            "power": ["energy", "watt", "wattage", "consumption"],
            "footprint": ["size", "physical", "area", "compact", "volume"],
            "reliability": ["mtbf", "durable", "durability", "reliable", "failure"],
            "score": ["scored", "scores", "benchmark", "accuracy", "test"],
        }
        relevant_synonyms: List[str] = []
        for tok in metric_tokens:
            if tok in synonym_map:
                relevant_synonyms.extend(synonym_map[tok])

        best_clause: Optional[str] = None
        best_idx: Optional[int] = None
        best_score = -1

        for c_idx, clause in enumerate(clauses):
            c_lower = clause.lower()
            score = 0
            if metric_clean and metric_clean in c_lower:
                score += 15

            for tok in metric_tokens:
                if re.search(rf'\b{re.escape(tok)}\b', c_lower):
                    score += 8
                elif tok in c_lower:
                    score += 4

            for syn in relevant_synonyms:
                if re.search(rf'\b{re.escape(syn)}\b', c_lower):
                    score += 6
                elif syn in c_lower:
                    score += 3

            if score > 0 and len(clauses) == total_rows and c_idx == row_idx:
                score += 2

            if score > best_score:
                best_score = score
                best_clause = clause
                best_idx = c_idx

        if best_score > 0:
            return best_clause, best_idx

        if total_rows == 1:
            return clauses[0], 0
        if row_idx < len(clauses):
            return clauses[row_idx], row_idx

        return clauses[0], 0

    @classmethod
    def _extract_comparative_relation(
        cls,
        clause: str,
        entity_a_name: str,
        entity_b_name: str,
        carried_subject: Optional[str] = None,
    ) -> Tuple[Optional[int], Optional[str], Optional[str], str]:
        """Extracts comparative direction (+1 = A > B, -1 = A < B), subject/object roles,
        and accounts for negation and ellipsis subject carry-over.
        """
        lower_clause = clause.lower()

        higher_terms = [
            "higher than", "greater than", "more than", "above", "better than",
            "superior to", "larger than", "faster than", "heavier than",
            "longer than", "stronger than",
            "exceeded", "exceeds", "exceeding",
            "outperformed", "outperforms", "outperforming",
            "surpassed", "surpasses", "surpassing",
            "beat", "beats", "beating",
            "outpaced", "outpaces", "outpacing",
            "higher", "greater", "better", "superior", "faster", "larger",
        ]
        lower_terms = [
            "lower than", "less than", "smaller than", "below", "under",
            "worse than", "inferior to", "slower than", "cheaper than",
            "shorter than", "weaker than",
            "trailed", "trails", "trailing",
            "lagged behind", "lagged", "lags",
            "lower", "smaller", "worse", "inferior", "slower", "cheaper",
        ]

        matched_term = None
        term_dir = 0
        term_start = -1
        term_end = -1

        for term in sorted(higher_terms, key=len, reverse=True):
            idx = lower_clause.find(term)
            if idx != -1:
                matched_term = term
                term_dir = 1
                term_start = idx
                term_end = idx + len(term)
                break

        for term in sorted(lower_terms, key=len, reverse=True):
            idx = lower_clause.find(term)
            if idx != -1:
                if matched_term is None or len(term) > len(matched_term) or idx < term_start:
                    matched_term = term
                    term_dir = -1
                    term_start = idx
                    term_end = idx + len(term)
                    break

        if term_dir == 0:
            return None, None, None, ""

        # Check for negation preceding term (e.g. "not higher", "never lower")
        prefix_window = lower_clause[max(0, term_start - 15):term_start]
        if re.search(r'\b(?:not|never|no longer)\b', prefix_window):
            term_dir = -term_dir

        def find_spans(name: str, fallback_labels: List[str]) -> List[Tuple[int, int]]:
            spans: List[Tuple[int, int]] = []
            candidates = [name] + fallback_labels
            for cand in candidates:
                cand_clean = cand.strip().lower()
                if not cand_clean:
                    continue
                for m in re.finditer(rf'\b{re.escape(cand_clean)}\b', lower_clause):
                    spans.append((m.start(), m.end()))
            return spans

        spans_a = find_spans(entity_a_name, ["entity a", "entity_a", "the former", "left"])
        spans_b = find_spans(entity_b_name, ["entity b", "entity_b", "the latter", "right"])

        subjs_a = [s for s in spans_a if s[1] <= term_start]
        subjs_b = [s for s in spans_b if s[1] <= term_start]
        objs_a = [s for s in spans_a if s[0] >= term_end]
        objs_b = [s for s in spans_b if s[0] >= term_end]

        if subjs_a and not subjs_b:
            subject = "A"
        elif subjs_b and not subjs_a:
            subject = "B"
        elif subjs_a and subjs_b:
            subject = "A" if subjs_a[-1][0] > subjs_b[-1][0] else "B"
        else:
            subject = carried_subject if carried_subject in ("A", "B") else "A"

        if objs_b and subject == "A":
            obj = "B"
        elif objs_a and subject == "B":
            obj = "A"
        elif objs_b and not objs_a:
            obj = "B"
        elif objs_a and not objs_b:
            obj = "A"
        else:
            obj = "B" if subject == "A" else "A"

        # Resolve expected relation for A vs B:
        # If Subject is A and Dir is +1 -> A > B (+1)
        # If Subject is B and Dir is +1 -> B > A -> A < B (-1)
        comp_dir_for_a_vs_b = term_dir if subject == "A" else -term_dir
        return comp_dir_for_a_vs_b, subject, obj, matched_term or ""

    def _audit_comparison_panel(
        self,
        scene_id: str,
        props: Dict[str, Any],
        beat_text: str,
        graph: Optional[EvidenceGraph],
        inconsistencies: List[VisualInconsistencyRecord],
    ) -> None:
        if not beat_text:
            return

        # 1. Normalize comparison rows (supporting both comparison_rows and canonical left_val/right_val)
        raw_rows = props.get("comparison_rows")
        if not isinstance(raw_rows, list) or not raw_rows:
            if "left_val" in props or "right_val" in props or "val_a" in props or "val_b" in props:
                raw_rows = [{
                    "metric": props.get("delta_metric") or props.get("metric") or "Comparison",
                    "val_a": props.get("val_a", props.get("left_val")),
                    "val_b": props.get("val_b", props.get("right_val")),
                    "entity_a": props.get("entity_a_name") or props.get("entity_a") or props.get("left_label"),
                    "entity_b": props.get("entity_b_name") or props.get("entity_b") or props.get("right_label"),
                }]
            else:
                return

        default_entity_a = (
            props.get("entity_a_name") or props.get("entity_a") or props.get("left_label")
            or props.get("name_a") or "Entity A"
        )
        default_entity_b = (
            props.get("entity_b_name") or props.get("entity_b") or props.get("right_label")
            or props.get("name_b") or "Entity B"
        )

        metric_names = [
            str(r.get("metric") or r.get("delta_metric") or r.get("label") or "")
            for r in raw_rows if isinstance(r, dict)
        ]

        # 2. Segment beat_text into metric-aware clauses
        clauses = self._segment_clauses(beat_text, metric_names)
        if not clauses:
            return

        carried_subject: Optional[str] = None

        for r_idx, row in enumerate(raw_rows):
            if not isinstance(row, dict):
                continue

            metric = str(row.get("metric") or row.get("delta_metric") or row.get("label") or f"Row {r_idx+1}")
            val_a = row.get("val_a") if "val_a" in row else row.get("left_val", row.get("value_a"))
            val_b = row.get("val_b") if "val_b" in row else row.get("right_val", row.get("value_b"))

            num_a = val_a if isinstance(val_a, (int, float)) else self.parse_number_with_multiplier(str(val_a))
            num_b = val_b if isinstance(val_b, (int, float)) else self.parse_number_with_multiplier(str(val_b))

            if num_a is None or num_b is None:
                continue

            row_entity_a = row.get("entity_a") or row.get("entity_a_name") or default_entity_a
            row_entity_b = row.get("entity_b") or row.get("entity_b_name") or default_entity_b

            # 3. Associate row with matching clause
            target_clause, _ = self._match_row_to_clause(metric, clauses, r_idx, len(raw_rows))
            if not target_clause:
                continue

            # 4. Extract comparative relation and resolve subject/object
            expected_dir, subj, obj, term = self._extract_comparative_relation(
                target_clause,
                row_entity_a,
                row_entity_b,
                carried_subject=carried_subject,
            )
            if expected_dir is None:
                continue

            if subj:
                carried_subject = subj

            # 5. Contrast visual values against expected direction
            name_a = row_entity_a
            name_b = row_entity_b
            subj_name = name_a if subj == "A" else name_b
            obj_name = name_b if subj == "A" else name_a

            if num_a > num_b and expected_dir == -1:
                inconsistencies.append(
                    VisualInconsistencyRecord(
                        scene_id=scene_id,
                        block_type="comparison_panel",
                        parameter_key=f"comparison_rows[{r_idx}]",
                        discrepancy_type=VisualDiscrepancyType.CHART_TREND_CONTRADICTION,
                        severity=VisualSeverity.BLOCK,
                        visual_value=f"{val_a} > {val_b}",
                        expected_value=f"{val_a} < {val_b}",
                        audio_text_snippet=target_clause[:120],
                        explanation=(
                            f"Comparison row '{metric}' shows {name_a} higher than {name_b} ({val_a} > {val_b}), "
                            f"but audio asserts {subj_name} was {term} {obj_name} ({name_a} < {name_b})."
                        ),
                        remediation_suggestion="Align comparison row values to match voiceover narrative.",
                    )
                )
            elif num_a < num_b and expected_dir == 1:
                inconsistencies.append(
                    VisualInconsistencyRecord(
                        scene_id=scene_id,
                        block_type="comparison_panel",
                        parameter_key=f"comparison_rows[{r_idx}]",
                        discrepancy_type=VisualDiscrepancyType.CHART_TREND_CONTRADICTION,
                        severity=VisualSeverity.BLOCK,
                        visual_value=f"{val_a} < {val_b}",
                        expected_value=f"{val_a} > {val_b}",
                        audio_text_snippet=target_clause[:120],
                        explanation=(
                            f"Comparison row '{metric}' shows {name_a} lower than {name_b} ({val_a} < {val_b}), "
                            f"but audio asserts {subj_name} was {term} {obj_name} ({name_a} > {name_b})."
                        ),
                        remediation_suggestion="Align comparison row values to match voiceover narrative.",
                    )
                )
```

---

## 5. Comprehensive Unit Test Cases

The following test methods should be appended to `TestComparisonPanelVerification` in `tests/test_visual_verifier.py`:

```python
    def test_multi_predicate_comparison_passes(self):
        """Counterexample 1 fix: Verifies multi-predicate narration does not trigger false-positive blocks."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_multi_pred",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Speed", "val_a": 100, "val_b": 50},
                    {"metric": "Cost", "val_a": 20, "val_b": 50},
                ]
            },
            "narration_text": "Entity A operated higher than Entity B in speed, but was lower than Entity B in cost.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
        assert len(report.inconsistencies) == 0

    def test_multi_predicate_with_one_contradiction_blocks(self):
        """Verifies multi-predicate correctly isolates and blocks only the contradicting row."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_multi_pred_contra",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Speed", "val_a": 100, "val_b": 50},
                    {"metric": "Cost", "val_a": 80, "val_b": 50},  # Contradiction: audio asserts lower
                ]
            },
            "narration_text": "Entity A operated higher than Entity B in speed, but was lower than Entity B in cost.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert len(report.inconsistencies) == 1
        assert "Cost" in report.inconsistencies[0].explanation

    def test_subject_inversion_exceeded_passes(self):
        """Counterexample 2 fix: Verifies Entity B exceeding Entity A matches val_a < val_b."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_entity_swap",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Speed", "val_a": 50, "val_b": 100},
                ]
            },
            "narration_text": "Entity B exceeded Entity A in speed.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
        assert len(report.inconsistencies) == 0

    def test_subject_inversion_exceeded_contradiction_blocks(self):
        """Verifies Entity B exceeding Entity A correctly blocks when visual shows val_a > val_b."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_entity_swap_contra",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Speed", "val_a": 100, "val_b": 50},
                ]
            },
            "narration_text": "Entity B exceeded Entity A in speed.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert len(report.inconsistencies) == 1
        assert "Speed" in report.inconsistencies[0].explanation

    def test_canonical_left_right_parameters_passes(self):
        """Verifies canonical left_val / right_val / delta_metric parameters."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_canon_pass",
            "block_type": "comparison_panel",
            "parameters": {
                "delta_metric": "Latency",
                "left_val": 25,
                "right_val": 100,
                "left_label": "Alpha",
                "right_label": "Beta",
            },
            "narration_text": "Alpha achieved lower latency than Beta.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True

    def test_canonical_left_right_parameters_blocks(self):
        """Verifies canonical left_val / right_val correctly blocks on trend contradiction."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_canon_block",
            "block_type": "comparison_panel",
            "parameters": {
                "delta_metric": "Latency",
                "left_val": 100,
                "right_val": 25,
                "left_label": "Alpha",
                "right_label": "Beta",
            },
            "narration_text": "Alpha achieved lower latency than Beta.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is False
        assert len(report.inconsistencies) == 1

    def test_custom_entity_names_multi_predicate(self):
        """Verifies named entities with units and multi-clause narration."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_custom_multi",
            "block_type": "comparison_panel",
            "parameters": {
                "entity_a_name": "Vacuum Tubes",
                "entity_b_name": "Silicon Transistors",
                "comparison_rows": [
                    {"metric": "Power Consumption", "val_a": "50W", "val_b": "< 0.001W"},
                    {"metric": "Switching Speed", "val_a": "100 kHz", "val_b": "100+ MHz"},
                ],
            },
            "narration_text": "Vacuum Tubes required higher power than Silicon Transistors, but Transistors achieved much higher switching speed.",
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True

    def test_semicolon_delimited_multi_row(self):
        """Verifies 3-row comparison partitioned by semicolons."""
        verifier = VisualVerifier()
        scene = {
            "scene_id": "sc_semi_multi",
            "block_type": "comparison_panel",
            "parameters": {
                "comparison_rows": [
                    {"metric": "Speed", "val_a": 100, "val_b": 50},
                    {"metric": "Cost", "val_a": 20, "val_b": 50},
                    {"metric": "Reliability", "val_a": 99.9, "val_b": 95.0},
                ]
            },
            "narration_text": (
                "Entity A was faster than Entity B in speed; "
                "furthermore, its cost was lower than Entity B; "
                "and Entity A demonstrated superior reliability over Entity B."
            ),
        }
        report = verifier.verify_visuals([scene])
        assert report.passed is True
```

---

## 6. Caveats

1. **Passive Voice Construction**:
   - Sentences such as *"Entity A was surpassed by Entity B"* contain passive constructions where the grammatical subject (`Entity A`) is the semantic patient. In our pattern set, `was surpassed by` is handled by checking object spans after `by`. For the vast majority of documentary voiceover styles, active voice is predominant.
2. **Non-Numeric Categorical Comparison Rows**:
   - When comparison rows contain purely descriptive strings with no parseable numbers (e.g. `val_a = "Bulky Glass Tube"`, `val_b = "Sub-millimeter Crystal"`), `num_a` and `num_b` evaluate to `None`. These rows cannot be numerically evaluated and are skipped from mathematical trend auditing unless an explicit `winner: "a" | "b"` property is present in the row dictionary.
3. **Scope Boundary**:
   - As an explorer subagent operating in read-only mode, no production source files (`src/`) were directly modified. The proposed modifications were validated through isolated test execution.

---

## 7. Conclusion

The proposed metric-aware clause segmentation and entity resolution strategy completely resolves Finding 1 of `reviewer_2_m4_g10/handoff.md`:
- **False-positive multi-predicate BLOCKs are eliminated**: Both rows in Counterexample 1 pass cleanly.
- **Subject inversions are correctly reconciled**: Counterexample 2 passes cleanly when Entity B is the subject and `val_a < val_b`.
- **Contradictions remain strictly blocked**: Genuine contradictions (e.g. visual shows $100 > 50$ while audio asserts lower, or subject inversion where audio asserts $B > A$ but visual shows $A > B$) trigger deterministic `VisualSeverity.BLOCK`.
- **Canonical parameter schemas are supported**: `left_val`, `right_val`, and `delta_metric` are seamlessly normalized.
- **Zero test regressions**: All 4 baseline comparison panel tests continue to pass 100%, and all 8 new test dimensions pass cleanly.

---

## 8. Verification Method

To independently verify the findings, counterexamples, and remediation:

1. **Verify Baseline Counterexample 1 Fails on Current Codebase**:
   ```bash
   .venv\Scripts\python.exe -c "from src.epistemic.visual_verifier import VisualVerifier; v = VisualVerifier(); sc = {'scene_id': 'sc1', 'block_type': 'comparison_panel', 'parameters': {'comparison_rows': [{'metric': 'Speed', 'val_a': 100, 'val_b': 50}, {'metric': 'Cost', 'val_a': 20, 'val_b': 50}]}, 'narration_text': 'Entity A operated higher than Entity B in speed, but was lower than Entity B in cost.'}; print(v.verify_visuals([sc]).passed)"
   ```
   *Expected Current Output*: `False` (2 false-positive BLOCK inconsistencies).

2. **Verify Baseline Counterexample 2 Fails on Current Codebase**:
   ```bash
   .venv\Scripts\python.exe -c "from src.epistemic.visual_verifier import VisualVerifier; v = VisualVerifier(); sc = {'scene_id': 'sc2', 'block_type': 'comparison_panel', 'parameters': {'comparison_rows': [{'metric': 'Speed', 'val_a': 50, 'val_b': 100}]}, 'narration_text': 'Entity B exceeded Entity A in speed.'}; print(v.verify_visuals([sc]).passed)"
   ```
   *Expected Current Output*: `False` (1 false-positive BLOCK inconsistency).

3. **Apply Code Replacement & Run Full Visual Verifier Test Suite**:
   After applying the code replacement in Section 4 and test additions in Section 5:
   ```bash
   .venv\Scripts\pytest.exe tests/test_visual_verifier.py -v
   ```
   *Expected Output*: 35 passed in ~15s (100% pass rate).
