# ContentBench: 4-Layer Quality OS Evaluation Specification

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/evaluation/contentbench.py`  
**Cross-References:** `docs/PRD.md`, `docs/SYSTEM_DESIGN.md`, `docs/DATA_MODEL.md`  

---

## 1. Executive Summary & Benchmark Philosophy

**ContentBench** is an automated, multi-dimensional benchmarking and evaluation framework designed to objectively score AI-generated video productions across four distinct quality layers:
1. **Research Quality ($S_{\text{research}}$)**: Factual integrity, citation authority, claim density, and corroboration.
2. **Script & Narrative Quality ($S_{\text{script}}$)**: Cognitive hook strength, pacing tempo, readability, and brand guardrail compliance.
3. **Video & Composition Quality ($S_{\text{video}}$)**: Acoustic cleanliness, speech-beat alignment, visual relevance, and linter conformance.
4. **Cost & Resource Efficiency ($S_{\text{cost}}$)**: Unit economics, token efficiency, and compute rendering speed.

```
                             CONTENTBENCH (Quality OS)
                                         │
        ┌───────────────────┬────────────┴───────┬───────────────────┐
        ▼                   ▼                    ▼                   ▼
┌───────────────┐   ┌───────────────┐    ┌───────────────┐   ┌───────────────┐
│    Layer 1    │   │    Layer 2    │    │    Layer 3    │   │    Layer 4    │
│   Research    │   │    Script     │    │ Video & Comp  │   │   Economics   │
│  Evaluation   │   │  Evaluation   │    │  Evaluation   │   │  Efficiency   │
└───────┬───────┘   └───────┬───────┘    └───────┬───────┘   └───────┬───────┘
        │                   │                    │                   │
        └───────────────────┼────────────────────┼───────────────────┘
                            ▼
               [ Composite Quality Score: 0.0 - 1.0 ]
```

---

## 2. Layer 1: Research Quality Evaluation ($S_{\text{research}}$)

Evaluates the factual rigor and evidentiary backing in the `ResearchDossier`.

### 2.1 Evaluated Dimensions
1. **Fact Density**: Ratio of verifiable claims per 30 seconds of content ($\ge 3.0\text{ claims}$ for maximum score).
2. **Source Authority & Diversity**: Domain authority weighting based on source provenance (peer-reviewed / `.gov` / `.edu` = $1.0$; primary archives = $0.9$; mainstream tech journalism = $0.75$).
3. **Corroboration Index**: Percentage of core claims confirmed by $\ge 2$ independent sources.
4. **Conflict & Hallucination Penalty**: Deductions for uncorroborated assertions or internal contradictions.

### 2.2 Mathematical Formulation
$$S_{\text{research}} = 0.35 \times \min\left(1.0, \frac{\text{Claims}}{3.0}\right) + 0.35 \times \overline{\text{Authority}} + 0.30 \times \text{CorroborationRatio} - \text{Penalty}$$

---

## 3. Layer 2: Script & Narrative Evaluation ($S_{\text{script}}$)

Evaluates the pedagogical clarity, engagement dynamics, and structural flow of `Script`.

### 3.1 Evaluated Dimensions
1. **Hook Strength ($0.0 - 1.0$)**: Presence of cognitive curiosity gaps, contrarian reframing, or high-stakes questions in the opening 5 seconds.
2. **Pacing Cadence Consistency**: Evaluates words per minute across scenes against target $145\text{ WPM}$ (penalizes deviations outside $115 - 175\text{ WPM}$).
3. **Flesch-Kincaid Readability**: Ensures comprehension grade level matches target audience (Grade 7–10 for general tech education).
4. **Brand & DNA Guardrail Adherence**: 100% deduction if any prohibited buzzword (`game-changer`, `revolutionize`, `in this video`) or forbidden theme appears.

### 3.2 Mathematical Formulation
$$S_{\text{script}} = 0.30 \times \text{HookScore} + 0.25 \times \text{PacingScore} + 0.25 \times \text{ReadabilityScore} + 0.20 \times \text{DNAAdherence}$$

---

## 4. Layer 3: Video & Composition Evaluation ($S_{\text{video}}$)

Evaluates the acoustic signal, visual composition, and animation synchronization.

### 4.1 Evaluated Dimensions
1. **VoiceQA Acoustic Score**: Waveform inspection verifying zero clipping events ($<0.01\%$), zero dead air gaps ($>300\text{ms}$), and loudness consistency ($\Delta \text{RMS} \le 2.5\text{ dBFS}$).
2. **Speech-Beat Synchronization**: Drift offset between narration audio segment and storyboard visual transition ($\le 0.20\text{s}$).
3. **Visual Relevance & Quality**: Semantic match between scene description and frozen image/vector asset.
4. **Composition Linter Compliance**: Binary verification of zero broken local paths, zero remote `http://` URLs, and finite GSAP animation timelines.

### 4.2 Mathematical Formulation
$$S_{\text{video}} = 0.30 \times S_{\text{voice\_qa}} + 0.30 \times S_{\text{sync}} + 0.20 \times S_{\text{visual}} + 0.20 \times S_{\text{lint}}$$

---

## 5. Layer 4: Cost & Resource Efficiency ($S_{\text{cost}}$)

Evaluates unit economics and compute resource utilization from `ProductionCostLedger`.

### 5.1 Evaluated Dimensions
1. **Budget Target Compliance**: Score against target ceiling ($\le \$0.25$ per 30-second finished video).
2. **Token Efficiency Ratio**: Useful script output tokens vs total LLM prompt tokens consumed:
   $$\text{TokenEfficiency} = \frac{\text{ScriptTokens}}{\text{TotalTokens}} \times 10.0$$
3. **Rendering Compute Speed**: Total render duration relative to video runtime ($< 1.5\times$ real-time).

### 5.2 Mathematical Formulation
$$S_{\text{cost}} = 0.40 \times \text{BudgetScore} + 0.30 \times \text{TokenEfficiency} + 0.30 \times \text{RenderEfficiency}$$

---

## 6. Composite Benchmark Quality Score

The overall ContentBench quality score combines all 4 layers into a single normalized index $S_{\text{composite}} \in [0.0, 1.0]$:

$$\boxed{S_{\text{composite}} = 0.25 \times S_{\text{research}} + 0.30 \times S_{\text{script}} + 0.30 \times S_{\text{video}} + 0.15 \times S_{\text{cost}}}$$

### Quality Thresholds & Production Grades
| Composite Score | Grade | Status | Action |
|---|:---:|:---:|---|
| **$0.90 - 1.00$** | **A+ (Exemplar)** | **PASSED** | Ready for automated multi-platform distribution. |
| **$0.80 - 0.89$** | **A (Broadcast Standard)** | **PASSED** | Meets all broadcast quality and factual standards. |
| **$0.70 - 0.79$** | **B (Acceptable)** | **REVIEW** | Flagged for optional human review. |
| **$< 0.70$** | **F (Reject)** | **FAILED** | Automated rollback to scripting or audio stage. |

---

## 7. Standard Benchmark Corpora (Scenarios S1 – S5)

ContentBench includes 5 standardized evaluation scenarios executed during regression testing:
1. **`CB-S1: Transistor History`**: Dense technological history requiring 3 key historical claims and contrasting vacuum tube visuals.
2. **`CB-S2: GPU Parallelism`**: High-density quantitative explainer requiring animated matrix statistics and architectural blocks.
3. **`CB-S3: Apollo Guidance Computer`**: Creator-brand monologue enforcing strict Brand Constitution negative constraints.
4. **`CB-S4: CRISPR-Cas9 Mechanisms`**: Molecular biology breakdown requiring strict source authority citations.
5. **`CB-S5: James Webb Space Telescope`**: 9:16 vertical short-form format with safe-zone margin checks.
