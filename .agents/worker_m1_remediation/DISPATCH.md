## 2026-09-04T09:52:33Z

You are worker_m1_remediation, a teamwork_preview_worker subagent.
Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m1_remediation

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP:
Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md (under ## 2026-09-04T08:55:45Z) and challenger_2_m1_dev handoff:
`g:\Finding-new-code\harness9\.agents\challenger_2_m1_dev\handoff.md`

TASK:
Remediate the critical defect uncovered by challenger_2_m1_dev in `src/h9_runtime/memory.py`:

DEFECT DETAILS:
`src/models/contracts.py` lines 520-530 defines `LearningCandidate` with fields:
`lesson_id: str`
`creator_id: str`
`rule_type: str`
`observation: str`
`recommended_action: str`
`confidence: float`
`created_at: datetime`

In `src/h9_runtime/memory.py` lines 129-137, `DefaultMemoryRuntime.recall_context()` attempts to dereference:
`lc.hypothesis`, `lc.category`, `lc.proposed_action`, `lc.candidate_id`.
These attributes do not exist on `LearningCandidate`, causing:
`AttributeError: 'LearningCandidate' object has no attribute 'hypothesis'` when `recall_context()` is invoked with learning candidates.

FIX REQUIREMENT:
Update `src/h9_runtime/memory.py`:
Properly dereference `lc.observation`, `lc.rule_type`, `lc.recommended_action`, and `lc.lesson_id` (supporting backwards-compatible fallback getattr if dictionary or object).
Ensure `DefaultMemoryRuntime.recall_context()` correctly scores and returns `MemoryRecallItem` for both negative rules and learning candidates without error.

VERIFICATION MANDATE:
Execute the full test suite using:
`.venv\Scripts\python.exe -m unittest tests\test_challenger_2_integration_stress.py tests\test_h9_runtime.py tests\test_hermes_adapter.py tests\test_state_machine.py tests\test_contracts.py`
Verify that all 52+ tests pass with OK and zero failures.

Write your handoff report to:
`g:\Finding-new-code\harness9\.agents\worker_m1_remediation\handoff.md`
and message the parent with your results.
