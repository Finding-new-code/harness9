# Plan — auditor_m4

## Objective
Forensic integrity audit for Milestone 4: Provider, Memory & Subagent Integration (R4).

## Scope
Perform systematic forensic checks:
1. Check 1: Authenticity of Provider Routing (verify absence of hardcoded LLM backends, verify dynamic role mapping and fallback).
2. Check 2: Authenticity of Unified Memory & SessionDB Integration (verify tables created in state.db, verify genuine micro-transactions, absence of competing databases or file lockup).
3. Check 3: Authenticity of Subagent Research Delegation (verify tool scoping, output schema validation, prompt caching preservation).
4. Check 4: Anti-Facade / Anti-Cheating Analysis (check for hardcoded test returns, mock bypasses, pre-populated artifacts).
5. Check 5: Runtime Test Verification (independently execute pytest suites and verify passing assertions).

## Deliverable
Write forensic audit report to `.agents/auditor_m4/handoff.md` with binary verdict: `CLEAN` or `INTEGRITY VIOLATION`.
