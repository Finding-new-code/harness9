# Adversarial Challenge & Verification Report: Milestone 1 Runtime Boundary & Hermes Adapter

**Document Version:** 1.0.0  
**Agent:** challenger_2_m1_dev (Teamwork Preview Challenger)  
**Target:** Milestone 1 Architecture Audit & Runtime Boundary Interface (`adapters/hermes/` and `src/h9_runtime/`)  
**Working Directory:** `g:\Finding-new-code\harness9\.agents\challenger_2_m1_dev`  
**Verdict:** **REJECT**

---

## 1. Observation

1. **Baseline Test Suite Execution:**
   - Command executed:
     ```powershell
     .venv\Scripts\python.exe -m unittest tests\test_hermes_adapter.py tests\test_state_machine.py tests\test_contracts.py tests\test_h9_runtime.py
     ```
   - Output: `Ran 38 tests in 74.474s - OK`.

2. **Discovery of Critical Defect in MemoryRuntime (`src/h9_runtime/memory.py`):**
   - In `src/models/contracts.py` (lines 520–530), `LearningCandidate` is formally defined as:
     ```python
     class LearningCandidate(H9BaseModel):
         lesson_id: str = Field(..., min_length=1)
         creator_id: str = Field(..., min_length=1)
         rule_type: str = "negative_constraint"
         observation: str = Field(..., min_length=1)
         recommended_action: str = Field(..., min_length=1)
         confidence: float = Field(default=0.8, ge=0.0, le=1.0)
         created_at: str = Field(
             default_factory=lambda: datetime.now(timezone.utc).isoformat()
         )
     ```
   - In `src/h9_runtime/memory.py` (lines 128–137), `DefaultMemoryRuntime.recall_context()` attempts to access non-existent properties:
     ```python
     # 2. Search learning candidates
     for lc in self._learning_candidates:
         if q_lower in lc.observation.lower() or q_lower in lc.hypothesis.lower():
             results.append(MemoryRecallItem(
                 source="learning_candidates",
                 category=lc.category,
                 content=f"Observation: {lc.observation} -> Rule: {lc.proposed_action}",
                 score=0.9,
                 metadata={"candidate_id": lc.candidate_id},
             ))
     ```
   - Notice the mismatched attributes accessed on `lc`:
     * `lc.hypothesis` — does NOT exist on `LearningCandidate`.
     * `lc.category` — does NOT exist on `LearningCandidate` (the contract defines `rule_type`).
     * `lc.proposed_action` — does NOT exist on `LearningCandidate` (the contract defines `recommended_action`).
     * `lc.candidate_id` — does NOT exist on `LearningCandidate` (the contract defines `lesson_id`).

3. **Empirical Reproduction Command & Stack Trace:**
   - Reproduction command:
     ```powershell
     .venv\Scripts\python.exe -c "from src.models.contracts import LearningCandidate; from src.h9_runtime.memory import DefaultMemoryRuntime; cand = LearningCandidate(lesson_id='lc_01', creator_id='c1', observation='drops off', recommended_action='cut'); rt = DefaultMemoryRuntime(); rt.record_production_telemetry('p1', {}, [cand]); rt.recall_context('drops', creator_id='c1')"
     ```
   - Verbatim error output:
     ```text
     Traceback (most recent call last):
       File "<string>", line 1, in <module>
       File "G:\Finding-new-code\harness9\src\h9_runtime\memory.py", line 130, in recall_context
         if q_lower in lc.observation.lower() or q_lower in lc.hypothesis.lower():
                                                            ^^^^^^^^^^^^^
       File "G:\Finding-new-code\harness9\src\models\contracts.py", line 112, in __getitem__
         return getattr(self, key)
                ^^^^^^^^^^^^^^^^^^^
       File "G:\Finding-new-code\harness9\.venv\Lib\site-packages\pydantic\main.py", line 957, in __getattr__
         raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
     AttributeError: 'LearningCandidate' object has no attribute 'hypothesis'
     ```

4. **Worker Test Suite Gap:**
   - In `tests/test_h9_runtime.py`, `LearningCandidate` was only imported at line 45 and never instantiated or passed into `record_production_telemetry` or `recall_context`. Consequently, the worker's test suite gave a false green signal for requirement R4/Focus Item 1c ("Verify that CreatorProfile and memory updates through DefaultMemoryRuntime persist and recall accurately").

---

## 2. Logic Chain

1. **Mandate Requirement:**
   - Challenge Focus 1c explicitly states: *"Verify that CreatorProfile and memory updates through DefaultMemoryRuntime persist and recall accurately."*
2. **Observation:**
   - `DefaultMemoryRuntime` is designed to ingest `LearningCandidate` instances via `record_production_telemetry()` and retrieve them via `recall_context()`.
   - The production contract `src.models.contracts.LearningCandidate` defines `lesson_id`, `creator_id`, `rule_type`, `observation`, `recommended_action`.
   - `DefaultMemoryRuntime.recall_context()` dereferences `lc.hypothesis`, `lc.category`, `lc.proposed_action`, and `lc.candidate_id`.
3. **Inference:**
   - Any execution path that records a valid `LearningCandidate` into `DefaultMemoryRuntime` results in an unhandled `AttributeError` when `recall_context()` is invoked with any query.
4. **Deduction:**
   - Memory updates involving learning candidates fail to recall accurately and cause runtime crashes. Milestone 1 cannot be approved until this contract mismatch is resolved.

---

## 3. Caveats

- **HermesBridge & StateMachine Soundness:** The implementation in `adapters/hermes/bridge.py` and `src/h9_runtime/content.py` successfully passed all backward-compatibility, parameter fuzzing, sandbox isolation, and 17-state sequential execution tests. The rejection is strictly localized to the contract defect in `src/h9_runtime/memory.py`.
- **Review-Only Constraint:** In accordance with the role boundary ("Review-only — do NOT modify implementation code"), I have not patched `src/h9_runtime/memory.py` directly; a remediation agent must apply the one-block fix detailed below.

---

## 4. Conclusion

**Verdict: REJECT**

The Milestone 1 work product cannot be approved due to an empirical crash in `src/h9_runtime/memory.py` violating the core requirement for memory persistence and recall.

### Required Remediation
In `src/h9_runtime/memory.py` (lines 129–137), update the `_learning_candidates` loop to conform to the `LearningCandidate` schema:
```python
        # 2. Search learning candidates
        for lc in self._learning_candidates:
            # Check observation or recommended_action matching query
            action = getattr(lc, "recommended_action", getattr(lc, "proposed_action", ""))
            obs = getattr(lc, "observation", "")
            rule_type = getattr(lc, "rule_type", getattr(lc, "category", "learning"))
            lesson_id = getattr(lc, "lesson_id", getattr(lc, "candidate_id", "lc_unknown"))

            if q_lower in obs.lower() or q_lower in action.lower():
                results.append(MemoryRecallItem(
                    source="learning_candidates",
                    category=rule_type,
                    content=f"Observation: {obs} -> Rule: {action}",
                    score=0.9,
                    metadata={"candidate_id": lesson_id},
                ))
```

---

## 5. Verification Method

To reproduce the failure before remediation:
```powershell
.venv\Scripts\python.exe -c "from src.models.contracts import LearningCandidate; from src.h9_runtime.memory import DefaultMemoryRuntime; cand = LearningCandidate(lesson_id='lc_01', creator_id='c1', observation='drops off', recommended_action='cut'); rt = DefaultMemoryRuntime(); rt.record_production_telemetry('p1', {}, [cand]); rt.recall_context('drops', creator_id='c1')"
```
*Expected Failure:* `AttributeError: 'LearningCandidate' object has no attribute 'hypothesis'` with exit code 1.

To verify after remediation:
```powershell
.venv\Scripts\python.exe -m unittest tests.test_challenger_2_integration_stress.TestCreatorProfileAndMemoryRuntimeStress.test_12_context_recall_scoring_and_learning_candidates
```
*Expected Pass:* `Ran 1 test in ~0.01s - OK`.
