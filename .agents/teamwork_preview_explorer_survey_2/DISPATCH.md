## 2026-09-13T16:47:00Z

Received user dispatch:
Scope & Mission:
Investigate the production lifecycle state machine, runtime bridge, Hermes tools, and security boundaries in Harness 9:
1. Inspect `src/orchestrator/state_machine.py`: How does the 17-state machine work? What states, transitions, validators, and gates exist? Where should verification gates (`RESEARCH_VERIFICATION`, `SCRIPT_FACT_CHECK`, `VISUAL_FACT_CHECK`, `FINAL_EPISTEMIC_QA`) be integrated? How can deterministic outcomes (`PASS`, `WARN`, `HUMAN_REVIEW`, `BLOCK`) be enforced such that publishing is blocked when mandatory gates fail?
2. Inspect `src/h9_runtime/` and `tools/h9_content_tools.py`: How are Hermes native model tools currently declared and registered? What is the pattern for adding new native Hermes tools (`h9.extract_claims`, `h9.verify_claim`, `h9.verify_script`, `h9.verify_quote`, `h9.verify_numbers`, `h9.analyze_historical_consensus`, `h9.detect_contradictions`, `h9.verify_visual_claims`, `h9.epistemic_gate`)?
3. Inspect `src/security/tokens.py`, capability permissions, and sandbox execution: How are tool calls guarded? How should retrieved web content be sanitized as untrusted data to prevent prompt injection or authority escalation?
4. Check how `tests/test_state_machine.py`, `tests/test_h9_acceptance.py`, and `tests/test_h9_m5_sandbox_permission_mcp.py` test these systems.
