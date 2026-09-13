## 2026-09-04T18:09:12Z

You are worker_m2_remediation_orch3, a teamwork_preview_worker implementing Milestone 2 Remediation (Iteration 2).

Your working directory is: g:\Finding-new-code\harness9\.agents\worker_m2_remediation_orch3\
Create and maintain your own BRIEFING.md, progress.md, and handoff.md in your working directory.
Communicate updates and completion via send_message to your parent (Recipient: d832f8a0-ed17-43c0-91e0-f1ecca7ae126).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INPUTS — READ THESE FIRST:
1. g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md
2. g:\Finding-new-code\harness9\.agents\challenger_1_m2_orch3\handoff.md (Detailed failure analysis of the 3 crash vulnerabilities)
3. Repro test suite: g:\Finding-new-code\harness9\tests\test_challenger_m2_stress.py
4. Files to remediate:
   - g:\Finding-new-code\harness9\tools\h9_content_tools.py
   - g:\Finding-new-code\harness9\src\h9_runtime\bridge.py

SPECIFIC BUGS TO FIX:
1. `tools/h9_content_tools.py:272`:
   `handle_h9_generate_script` performs unprotected `float(args.get("target_duration", 30.0))` outside the `try:` block.
   When `target_duration` is a non-numeric string or `None`, it raises uncaught `ValueError` or `TypeError`.
   Fix: Robustly parse `target_duration` inside the `try:` block, catching `(ValueError, TypeError)` and returning `tool_error("Parameter 'target_duration' must be a valid number of seconds.")` if invalid.
2. `src/h9_runtime/bridge.py:746`:
   `discover_assets` crashes with `TypeError: 'NoneType' object is not iterable` when `dossier` contains `suggested_visual_queries: None`.
   Fix: Use `queries = list(dossier.get("suggested_visual_queries") or [])`.
3. `src/h9_runtime/bridge.py:458`:
   `generate_script` crashes with `TypeError: 'NoneType' object is not iterable` when `dossier` contains `claims: None`.
   Fix: Use `claims = dossier.get("claims") or []` before iterating.

TEST & VERIFICATION INSTRUCTIONS:
Run the tests using `.venv\Scripts\python.exe`:
1. `.venv\Scripts\python.exe -m pytest tests/test_challenger_m2_stress.py -v` (MUST PASS 26/26!)
2. `.venv\Scripts\python.exe -m pytest tests/test_h9_content_tools.py -v` (MUST PASS 34/34!)
3. `.venv\Scripts\python.exe -m pytest tests/test_adversarial_m2_tools.py -v` (MUST PASS 22/22!)
4. `.venv\Scripts\python.exe -m pytest tests/test_h9_runtime.py -v` (MUST PASS 10/10!)
5. `.venv\Scripts\python.exe -m pytest tests/tools/test_registry.py -v` (MUST PASS 39/39!)

Author a detailed `handoff.md` with verification commands and output, then notify parent via `send_message`.
