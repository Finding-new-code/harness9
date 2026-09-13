# System Evolution & Learning Loop Specification: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/creator/memory.py`, `src/models/contracts.py`  
**Cross-References:** `docs/CREATOR_MEMORY.md`, `docs/CONTENTBENCH.md`, `docs/DATA_MODEL.md`  

---

## 1. Architectural Role & Evolution Philosophy

A static content production system degrades over time as audience preferences shift and recurring creative flaws persist. Harness 9 implements an **Autonomous Evolution & Continuous Learning Loop** that transforms post-publication performance telemetry and reviewer feedback into durable cognitive constraints and few-shot exemplars.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Autonomous Production Lifecycle                       │
│       (Brief ──► Research ──► Editorial ──► Script ──► Render ──► Dist)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Publish & Telemetry Ingestion)
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Analytics & Audience Feedback                      │
│        • Retention Curves  • Drop-Off Timestamps  • CTR  • Comments         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Cognitive Distillation)
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Learning Candidate Extractor                        │
│    • Identifies High-Retention Hooks     • Detects Pacing Drop-Off Points   │
│    • Flags Ineffective Visual Blocks     • Isolates Negative Memory Rules   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Consolidation & Verification)
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Creator DNA Memory Consolidation                     │
│    • Updates Brand Constitution          • Appends Negative Memory Rules    │
│    • Enriches Few-Shot Exemplar Bank     • Self-Tunes System Prompts        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ingestion of Performance Telemetry (`AnalyticsSnapshot`)

Upon publication across distribution channels, telemetry is captured in structured `AnalyticsSnapshot` payloads:
- `views: int`: Total impression and view count.
- `average_watch_percentage: float`: Percentage of video completed by viewers.
- `retention_curve: List[float]`: Second-by-second viewer retention percentage.
- `ctr: float`: Click-through rate on thumbnail and title.
- `engagement_rate: float`: Likes, shares, and comments divided by views.

### 2.1 Retention Anomaly Detection Algorithm
1. **Hook Efficacy (Seconds $0 - 5$)**:
   - If $\text{Retention}(5\text{s}) \ge 80\%$, the opening hook structure is marked as a **Positive Exemplar**.
   - If $\text{Retention}(5\text{s}) < 60\%$, a **Negative Learning Rule** is triggered: *"Opening curiosity gap failed to establish emotional stakes within 5 seconds"*.
2. **Mid-Video Drop-Off Detection**:
   - Computes first derivative of retention: $\Delta R(t) = R(t) - R(t-1)$.
   - If $\Delta R(t) < -5.0\%$ in a 2-second window, the corresponding `ScriptBeat` and visual block are flagged for pacing analysis.

---

## 3. Learning Candidate Distillation (`LearningCandidate`)

Identified learnings are formulated as immutable `LearningCandidate` contracts before consolidation:

```yaml
lesson_id: "lesson_20260831_001"
creator_id: "tech_explainer_01"
rule_type: "negative_constraint"
observation: "Act 2 technical jargon density caused 7.2% viewer drop-off at second 12."
recommended_action: "Limit technical terminology to maximum 1 new term per 10 seconds without visual diagram."
confidence: 0.92
created_at: "2026-08-31T14:30:00Z"
```

### Rule Types
1. `negative_constraint`: Explicit prohibition appended to Creator Brand Constitution (e.g. *"Do NOT use split-screen intro when comparing more than 2 parameters"*).
2. `positive_exemplar`: High-performing hook or transition added to Few-Shot Exemplar bank.
3. `pacing_calibration`: Adjusts target speaking rate (WPM) or scene duration parameters.

---

## 4. Consolidation into Creator DNA & Memory

Learned rules are merged into the creator's persistent storage:

```
                      LearningCandidate (Confidence >= 0.80)
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │     Memory Consolidator       │
                     └───────────────┬───────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│     Negative Memory Bank      │               │     Few-Shot Exemplar Bank    │
│ "Avoid pattern X in topic Y"  │               │ "Use hook structure Z"        │
└───────────────┬───────────────┘               └───────────────┬───────────────┘
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        ▼
                         [ Dynamic Prompt Injection ]
```

### 4.1 Dynamic Prompt Injection Contract
When generating future outlines and scripts, the prompt builder injects negative rules dynamically:
```
## CREATOR BRAND GUARDRAILS & LEARNED NEGATIVE RULES
- Never use buzzwords like 'game-changer' or 'revolutionize'
- [LEARNED]: Limit technical terminology to max 1 new term per 10s without visual diagram (Confidence: 0.92)
- [LEARNED]: Avoid passive voice in Act 1 opening sentence (Confidence: 0.88)
```

---

## 5. Regression Avoidance & Safety Verification

To prevent degenerate feedback loops where negative rules excessively constrain creative diversity:
1. **Rule Confidence Threshold**: Only candidates with $\text{Confidence} \ge 0.80$ are automatically promoted.
2. **Rule Pruning & Decay**: Negative constraints undergo periodic evaluation; rules with zero violations over 50 productions are archived.
3. **Contradiction Checking**: New candidate rules are checked against core Brand Constitution tenets before consolidation.
