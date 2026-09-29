## 2026-09-13T19:02:16Z
You are explorer_3_m2. Your working directory is g:\Finding-new-code\harness9\.agents\explorer_3_m2.
Update your progress.md regularly.

MANDATORY FIRST STEP: Read g:\Finding-new-code\harness9\.agents\ORIGINAL_REQUEST.md before starting work.
Also read:
- g:\Finding-new-code\harness9\.agents\teamwork_preview_orchestrator_8\PROJECT.md
- g:\Finding-new-code\harness9\docs\epistemic\EVIDENCE_GRAPH.md
- g:\Finding-new-code\harness9\docs\epistemic\EPISTEMIC_ARCHITECTURE.md
- g:\Finding-new-code\harness9\src\models\contracts.py

OBJECTIVE:
Design the dedicated machine-readable Evidence Graph abstraction in src/epistemic/graph.py.
1. Nodes: Sources, Passages, Evidence Units, Claims, Verification Traces, Script Sentences, Scenes, Visual Elements.
2. Edges / Relations: Entailment, Contradiction, Corroboration, Mentions, DerivesFrom, VisualDepiction.
3. DAG algorithms and operations: cycle prevention/detection, topological sort, serialization to/from dict/JSON, querying claims by status, reconstructing evidence chains, calculating chain confidence.
4. Define clean class interfaces, methods, and Pydantic/dataclass models for EvidenceGraph, GraphNode, GraphEdge.
5. Provide detailed specifications and test case designs for tests/test_evidence_graph.py.

Do NOT modify or write source code directly (read-only exploration).
Write your findings and implementation recommendation to g:\Finding-new-code\harness9\.agents\explorer_3_m2\analysis.md and send your completion report via send_message.
