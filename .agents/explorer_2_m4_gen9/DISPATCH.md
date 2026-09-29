## 2026-09-14T00:03:09Z
You are explorer_2_m4_gen9, a teamwork_preview_explorer subagent.
Working directory: g:\Finding-new-code\harness9\.agents\explorer_2_m4_gen9

MANDATORY INSTRUCTION: You MUST read the authoritative request at g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work. Do NOT skip this.

Scope Document: g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_9\PROJECT.md

OBJECTIVE:
Investigate and specify the visual fact-checking engine (src/epistemic/visual_verifier.py) for Milestone 4 (R4).

KEY SOURCES TO INVESTIGATE:
1. docs/epistemic/VISUAL_FACT_CHECKING.md
2. docs/epistemic/FACT_CHECKING_SPEC.md
3. src/models/contracts.py (inspect Storyboard, StoryboardScene, VisualAsset, ChartData, TimelineEvent, etc.)
4. src/epistemic/graph.py (how visual nodes connect to claims and sources in EvidenceGraph)
5. Existing storyboard/rendering code in src/

YOU MUST SPECIFY:
1. Extraction and verification of rendered visual elements:
   - Timelines: event sequencing, date consistency against script narration and evidence graph.
   - Charts: data points, trends, axis labels, baseline zeros against numerical evidence.
   - Counts / Quantities: on-screen entity counts matching script statements.
   - Maps / Geospatial: geographic boundaries, territory labels.
2. Return contract: VisualVerificationReport, VisualInconsistencyRecord, VisualDiscrepancyType enum, severity (BLOCK, WARN).
3. Cross-modal consistency checks: verifying that visuals do not contradict narration (e.g. voiceover says "revenue fell by 10%" while chart shows upward trend).
4. Concrete interface contracts and verification functions.

SCOPE BOUNDARIES:
- Read-only exploration. DO NOT write or edit source code files.
- Maintain progress.md in your working directory with 'Last visited: [timestamp]' for liveness.

DELIVERABLE:
Write a complete 5-part handoff report to g:\Finding-new-code\harness9\.agents\explorer_2_m4_gen9\handoff.md (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
When done, notify parent using send_message with your handoff summary.
