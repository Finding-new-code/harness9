# Milestone 3 Review & Adversarial Critic Report: Historical Scholarship Policy

**Agent:** `reviewer_1_m3`  
**Roles:** `reviewer`, `critic`  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\reviewer_1_m3`  
**Target Files:** `src/epistemic/historical_policy.py`, `tests/test_historical_policy.py`  
**Parent Agent:** `ba190775-5480-43b0-a934-7fd1b7ba9b5b`  
**Date:** 2026-09-13T20:12:00Z  
**Verdict:** `REQUEST_CHANGES`  

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**

The Historical Scholarship Policy engine in `src/epistemic/historical_policy.py` demonstrates solid architectural structure, clean Pydantic modeling, zero integrity cheating (no hardcoded test cheats or facade implementations), and 100% pass rate on current unit tests (15/15) and regression suites (144/144). 

However, adversarial stress testing and line-by-line inspection revealed **3 Major logic defects** and **3 Minor gaps** that directly compromise policy compliance and production execution:
1. **Substring matching false positive**: `"contested" in lower_text` matches `"uncontested"`, erroneously classifying undisputed historical facts (e.g., George Washington's uncontested 1789 election) as `ConsensusState.CONTESTED`.
2. **Threshold B Monograph vs. Literature Sufficiency Contradiction**: A claim backed solely by a university press monograph (Tier 3) satisfies Threshold B, yet `classify_consensus_state()` classifies it as `ConsensusState.INSUFFICIENT_LITERATURE` (`n_scholarly < 2 and n_primary < 1`), which causes `evaluate_claim()` to mark it `EpistemicStatus.UNSUPPORTED` and `eligible_for_narration = False`. This blocks valid academic monographs from narration.
3. **Data loss in Non-Averaging Contradiction Invariant**: `evaluate_claim()` reads `c_rec.conflicting_assertions` to populate `divergent_values_preserved`, but `enforce_non_averaging()` only populates the singular field `conflicting_assertion: str`, leaving `conflicting_assertions: List[Dict[str, Any]]` empty. Consequently, `report.divergent_values_preserved` is always empty `[]`.

---

## Findings

### [Major] Finding 1: Substring Matching False Positive in Consensus Classification
- **What**: The string check `"contested" in lower_text` matches any word containing `"contested"`, including `"uncontested"`.
- **Where**: `src/epistemic/historical_policy.py`, Line 226:
  ```python
  if primary_dissent or "contested" in lower_text:
      return ConsensusState.CONTESTED
  ```
- **Why**: Historical claims containing affirmative statements like *"George Washington won the uncontested election of 1789"* or *"The treaty ceded uncontested control"* are classified as `ConsensusState.CONTESTED`, incorrectly triggering conflict-transparency framing and demanding divergent ranges for uncontested facts.
- **Empirical Proof**:
  ```python
  c = ClaimRecord(claim_id="t1", claim_text="George Washington won the uncontested election of 1789.", primary_source=p)
  checker.classify_consensus_state(c, [p]) # Returns: ConsensusState.CONTESTED
  ```
- **Suggestion**: Use word boundary regex:
  ```python
  if primary_dissent or re.search(r"\bcontested\b", lower_text) and not re.search(r"\buncontested\b", lower_text):
  ```

---

### [Major] Finding 2: Threshold B Monograph vs. Literature Sufficiency Contradiction
- **Where**: `src/epistemic/historical_policy.py`, Lines 231–238 & Lines 588–590:
  ```python
  n_scholarly = n_peer + n_book
  if n_scholarly < 2 and n_primary < 1:
      return ConsensusState.INSUFFICIENT_LITERATURE
  ```
- **Why**: According to `HISTORICAL_SCHOLARSHIP_POLICY.md` Section 2 (lines 33–36), **Threshold B** explicitly allows a claim to achieve status `SUPPORTED` or `VERIFIED` with *"at least one verified Tier 3 source (ACADEMIC_PRESS_BOOK)"*. While `verify_minimum_source_tiers()` passes this as `"Threshold B"`, `classify_consensus_state()` requires `n_scholarly >= 2 and n_primary < 1`. When a claim has 1 Tier 3 monograph (`n_book = 1, n_peer = 0, n_primary = 0`), it is classified as `INSUFFICIENT_LITERATURE`. In `evaluate_claim()`, `INSUFFICIENT_LITERATURE` forces `final_status = EpistemicStatus.UNSUPPORTED` and `eligible_for_narration = False`.
- **Empirical Proof**:
  ```python
  # c is backed by 1 Oxford University Press book:
  report = checker.evaluate_claim(c)
  # report.qualifying_threshold == "Threshold B"
  # report.consensus_state == ConsensusState.INSUFFICIENT_LITERATURE
  # report.epistemic_status == EpistemicStatus.UNSUPPORTED
  # report.eligible_for_narration == False
  ```
- **Suggestion**: In `classify_consensus_state()`, allow a verified Tier 3 monograph to satisfy literature sufficiency:
  ```python
  if n_scholarly < 2 and n_primary < 1 and n_book < 1:
      return ConsensusState.INSUFFICIENT_LITERATURE
  ```
  And in consensus classification when `n_book >= 1` and `n_dissent == 0`: classify as `MAJORITY_INTERPRETATION` or `BROAD_CONSENSUS`.

---

### [Major] Finding 3: Dropped Divergent Values in Non-Averaging Invariant
- **Where**: `src/epistemic/historical_policy.py`, Lines 347–356 & Lines 559–560:
  ```python
  # In enforce_non_averaging():
  contra = ContradictionRecord(
      ...
      conflicting_assertion=f"Sources: {source_values}",
      # conflicting_assertions is NOT populated!
  )
  # In evaluate_claim():
  if c_rec and c_rec.conflicting_assertions:
      divergent_preserved = [c.get("value", "") for c in c_rec.conflicting_assertions]
  ```
- **Why**: `c_rec.conflicting_assertions` is always `[]`. Thus `divergent_preserved` is never populated, and `report.divergent_values_preserved` in `HistoriographicalEvaluationReport` is always empty `[]` even when divergent values were present in `source_values`.
- **Empirical Proof**:
  ```python
  c = ClaimRecord(claim_id="t4", claim_text="Casualties", primary_source=p, verifier_metadata={"source_values": [20000, 100000], "asserted_value": 20000})
  report = checker.evaluate_claim(c)
  # report.divergent_values_preserved == []  (Expected [20000, 100000])
  ```
- **Suggestion**: Populate `conflicting_assertions` in `enforce_non_averaging()`:
  ```python
  conflicting_assertions=[{"source_id": f"src_{i}", "value": v} for i, v in enumerate(source_values)],
  ```
  Or in `evaluate_claim()`, fallback to `source_values`:
  ```python
  divergent_preserved = list(s_vals)
  ```

---

### [Minor] Finding 4: Extreme Dissent (<10% agreement) Fall-through to `ACTIVE_DEBATE`
- **Where**: `src/epistemic/historical_policy.py`, Lines 251–256:
  ```python
  elif 0.40 <= r_agree < 0.60:
      return ConsensusState.ACTIVE_DEBATE
  elif 0.10 <= r_agree < 0.40:
      return ConsensusState.MINORITY_INTERPRETATION
  return ConsensusState.ACTIVE_DEBATE
  ```
- **Why**: If `r_agree < 0.10` (e.g. 1 supporter vs 20 peer-reviewed dissenters), the condition fails all `if/elif` branches and falls through to line 256 (`return ConsensusState.ACTIVE_DEBATE`). This classifies an extreme fringe hypothesis as an active scholarly debate rather than `MINORITY_INTERPRETATION` or `CONTESTED`.
- **Suggestion**:
  ```python
  elif r_agree < 0.40:
      return ConsensusState.MINORITY_INTERPRETATION
  ```

---

### [Minor] Finding 5: `mandated_phrases` and Hedging Gaps in `check_narration_framing()`
- **Where**: `src/epistemic/historical_policy.py`, Lines 459–479.
- **Why**: 
  1. `HistoricalFraming.mandated_phrases` is defined for every consensus state, but `check_narration_framing()` never checks whether any mandated phrase is present in the script.
  2. `framing.requires_hedging` is `True` for `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, and `INSUFFICIENT_LITERATURE`, but the hedge marker check is hardcoded only for `ACTIVE_DEBATE`, `CONTESTED`, and `UNRESOLVED`.
- **Suggestion**: Expand hedge checks to all states where `framing.requires_hedging` is True, and issue warnings when none of the `mandated_phrases` are used.

---

### [Minor] Finding 6: Duplicate Source Counting for Threshold C
- **Where**: `src/epistemic/historical_policy.py`, Line 180:
  ```python
  peer_sources = [s for s, t in coerced if t in self.PEER_REVIEWED_TIERS]
  if len(peer_sources) >= 2:
      return True, "Threshold C", []
  ```
- **Why**: It does not deduplicate sources by URL, title, or ID. If the caller passes the same Tier 2 source twice in `sources` or corroborated list, it qualifies for Threshold C despite representing only one study.
- **Suggestion**: Deduplicate `peer_sources` by `(s.url, s.title, s.source_id)`.

---

## Adversarial Challenge Summary

**Overall risk assessment**: **MEDIUM**

### Challenge 1: Substring word contamination
- **Assumption challenged**: Simple substring check `"contested" in lower_text` is sufficient.
- **Attack scenario**: Claims like *"George Washington's uncontested 1789 election"* or *"Uncontested territory"*.
- **Blast radius**: Undisputed consensus facts are forced into conflict framing and range requirements.
- **Mitigation**: Word boundary regex (`\bcontested\b`).

### Challenge 2: Single-monograph deadlock
- **Assumption challenged**: Historiographical consensus requires at least 2 scholarly works (`n_scholarly >= 2`) or primary source (`n_primary >= 1`).
- **Attack scenario**: A historical interpretation based on an authoritative Oxford University Press monograph (Tier 3).
- **Blast radius**: The claim passes Threshold B, but is marked `INSUFFICIENT_LITERATURE` and `UNSUPPORTED`, preventing publication.
- **Mitigation**: Recognize Tier 3 monographs as sufficient literature in `classify_consensus_state()`.

### Challenge 3: Invariant audit data loss
- **Assumption challenged**: Non-averaging contradiction records correctly preserve divergent figures in audit reports.
- **Attack scenario**: Pipeline audits divergent casualty counts (e.g., 20,000 vs 100,000).
- **Blast radius**: `report.divergent_values_preserved` is empty `[]`.
- **Mitigation**: Align `conflicting_assertions` in `ContradictionRecord` or pass `source_values` directly.

---

## 5-Component Handoff Protocol

### 1. Observation
- `src/epistemic/historical_policy.py`: 612 lines implementing `HistoriographicalViolationType`, `HistoricalFraming`, `ContradictionRecord`, `HistoriographicalEvaluationReport`, and `HistoricalPolicyChecker`.
- `tests/test_historical_policy.py`: 15 test cases, all passing (`15 passed in 10.80s`).
- Full regression suite: `144 passed in 60.85s` across `test_historical_policy.py`, `test_verification_engine.py`, `test_evidence_graph.py`, `test_contracts.py`, `test_state_machine.py`, `test_h9_acceptance.py`.
- No integrity violations, facades, or test cheats detected.
- Line 226: `"contested" in lower_text` matches `"uncontested"`.
- Line 237: `if n_scholarly < 2 and n_primary < 1:` classifies 1 Tier 3 monograph as `INSUFFICIENT_LITERATURE`.
- Lines 559–560: `c_rec.conflicting_assertions` is unpopulated, causing `report.divergent_values_preserved == []`.

### 2. Logic Chain
1. In `classify_consensus_state()`, checking `"contested" in lower_text` evaluates to `True` on `"uncontested"`, causing incorrect consensus classification for undisputed historical facts.
2. In `HISTORICAL_SCHOLARSHIP_POLICY.md` Section 2, Threshold B establishes that a single Tier 3 university press monograph is sufficient to achieve `SUPPORTED` or `VERIFIED` status. In `historical_policy.py`, `verify_minimum_source_tiers()` passes Threshold B, but `classify_consensus_state()` requires `n_scholarly >= 2`, downgrading the claim to `INSUFFICIENT_LITERATURE`, which in turn forces `evaluate_claim()` to set `epistemic_status = UNSUPPORTED` and `eligible_for_narration = False`.
3. In `evaluate_claim()`, the code expects `c_rec.conflicting_assertions` to be a list of dictionaries with `"value"` keys. Because `enforce_non_averaging()` only populates `conflicting_assertion: str`, `divergent_values_preserved` remains empty, violating the data preservation requirement.

### 3. Caveats
- Current unit tests pass because they do not include claims containing the word "uncontested", do not check `report.epistemic_status` or `report.eligible_for_narration` on single-monograph claims (only checking `report.qualifying_threshold == "Threshold B"`), and do not assert the contents of `report.divergent_values_preserved`.
- No source code in `src/` was modified during this review (review-only mandate respected).

### 4. Conclusion
The implementation of the Historical Scholarship Policy is well-architected and contains no integrity violations. However, because of the 3 Major defects identified (uncontested classification false-positive, single-monograph Threshold B deadlock, and non-averaging divergent values data loss), the verdict is **REQUEST_CHANGES**. Remediating these 3 issues will ensure robust, error-free historical claim governance.

### 5. Verification Method
To independently reproduce:
```bash
# 1. Run standard unit tests
uv run pytest tests/test_historical_policy.py -v

# 2. Run adversarial reproduction script
uv run python -c "
from src.epistemic.historical_policy import HistoricalPolicyChecker, ConsensusState
from src.models.contracts import ClaimRecord, ClaimType, SourceRecord, SourceTier

checker = HistoricalPolicyChecker()

# Bug 1: uncontested matched as contested
c1 = ClaimRecord(claim_id='t1', claim_text='George Washington won the uncontested election of 1789.', primary_source=SourceRecord(title='P', url='http://a', tier=SourceTier.PRIMARY_SOURCE))
print('Bug 1 (uncontested -> CONTESTED):', checker.classify_consensus_state(c1, [c1.primary_source]))

# Bug 2: Threshold B monograph marked UNSUPPORTED
book = SourceRecord(title='Book', url='http://b', tier=SourceTier.ACADEMIC_BOOK)
c2 = ClaimRecord(claim_id='t2', claim_text='Interpretation', primary_source=book, claim_type=ClaimType.SCHOLARLY_INTERPRETATION)
rep2 = checker.evaluate_claim(c2)
print('Bug 2 (Threshold B eligible):', rep2.eligible_for_narration, 'status:', rep2.epistemic_status)

# Bug 3: Divergent values lost
c4 = ClaimRecord(claim_id='t4', claim_text='Casualties', primary_source=SourceRecord(title='P', url='http://p', tier=SourceTier.PRIMARY_SOURCE), verifier_metadata={'source_values': [20000, 100000], 'asserted_value': 20000})
rep4 = checker.evaluate_claim(c4)
print('Bug 3 (divergent_preserved empty):', rep4.divergent_values_preserved)
"
```
