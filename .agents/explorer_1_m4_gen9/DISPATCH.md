## 2026-09-14T00:03:09Z
You are explorer_1_m4_gen9, a teamwork_preview_spec_miner subagent.
Working directory: g:\Finding-new-code\harness9\.agents\explorer_1_m4_gen9

MANDATORY INSTRUCTION: You MUST read the authoritative request at g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work. Do NOT skip this.

Scope Document: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_9\PROJECT.md

OBJECTIVE:
Investigate and specify the post-script claim extraction and re-verification engine (src/epistemic/script_verifier.py) for Milestone 4 (R4).

KEY SOURCES TO INVESTIGATE:
1. docs/epistemic/CLAIM_VERIFICATION.md
2. docs/epistemic/FACT_CHECKING_SPEC.md
3. docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md
4. docs/epistemic/EVIDENCE_GRAPH.md
5. src/models/contracts.py (inspect existing Script, ScriptScene, ClaimRecord, EpistemicStatus, EvidenceGraph integration)
6. src/scriptwriting/ (how scripts are generated and structured)
7. src/epistemic/ (inspect graph.py, engine.py, strategies.py)

YOU MUST SPECIFY:
1. Claim extraction from script dialogue/narration (sentence segmentation, regex/heuristic patterns, temporal anchor mapping).
2. Comparison of extracted script claims against EvidenceGraph DAG nodes to detect:
   - Strengthened claims: confidence escalated beyond evidence support (e.g., source says "suggests" or confidence 0.6, but script says "definitively proves" or confidence 1.0).
   - Altered numbers: numerical values differing from source evidence (e.g., 50,000 in evidence vs 500,000 in script).
   - Omitted uncertainty: epistemic hedging removed in narration for claims marked UNVERIFIED, CONTESTED, PLAUSIBLE, or DISPUTED.
   - Fabricated quotes: strict quote matching against primary source texts; paraphrase mandate when quotation marks are used without exact primary source passage.
3. Return contract: ScriptVerificationReport, ScriptClaimDriftRecord, DriftType enum (STRENGTHENED, ALTERED_NUMBER, OMITTED_UNCERTAINTY, FABRICATED_QUOTE), severity, recommended edits.
4. Integration with VerificationEngine and EvidenceGraph.

SCOPE BOUNDARIES:
- Read-only exploration. DO NOT write or edit source code files.
- Maintain progress.md in your working directory with 'Last visited: [timestamp]' for liveness.

DELIVERABLE:
Write a complete 5-part handoff report to g:\Finding-new-code\harness9\.agents\explorer_1_m4_gen9\handoff.md (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
When done, notify parent using send_message with your handoff summary.
