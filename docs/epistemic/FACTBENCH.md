# H9-FactBench Evaluation Suite & Benchmark Specification: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/evaluation/factbench/`, `tests/epistemic/`  
**Cross-References:** `docs/CONTENTBENCH.md`, `docs/DATA_MODEL.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`  

---

## 1. Executive Summary & Benchmark Philosophy

**H9-FactBench** is a standardized, multidimensional evaluation benchmark designed to rigorously assess the factual verification, historiographical rigor, numerical integrity, and visual-narrative consistency of the Harness 9 Epistemic Verification Layer.

While traditional language model benchmarks (e.g. MMLU, GSM8K, FactScore) evaluate isolated question answering or text generation, **H9-FactBench is designed for autonomous multi-modal production pipelines**. It evaluates:
1. Retrieval grounding and 13-tier source taxonomy adherence.
2. Natural language entailment and unearned assertion-strengthening detection.
3. Strict verbatim quote verification and paraphrase enforcement.
4. Historiographical consensus state modeling and non-averaging contradiction resolution.
5. Numerical dataset integrity and dimensional analysis.
6. Audio-visual consistency between spoken voiceover and rendered motion graphics.
7. Robustness against adversarial attacks (false consensus, citation laundering, authority spoofing, prompt injection).

---

## 2. The 9 Benchmark Categories

`H9-FactBench` comprises test suites distributed across 9 specialized categories:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       H9-FACTBENCH EVALUATION SUITE                         │
├──────────────────────────┬──────────────────────────┬───────────────────────┤
│ 1. general_factual       │ 2. numerical_integrity   │ 3. quote_veracity     │
│    • Encyclopedic ground │    • Dimensional checks  │    • Levenshtein test │
│    • Geography & biology │    • Unit conversions    │    • Paraphrase rules │
├──────────────────────────┼──────────────────────────┼───────────────────────┤
│ 4. scientific_mechanisms │ 5. current_events_temp   │ 6. historical_facts   │
│    • Peer-reviewed NLI   │    • Temporal freshness  │    • Primary archives │
│    • Causal mechanisms   │    • Anachronism checks  │    • Documented event │
├──────────────────────────┼──────────────────────────┼───────────────────────┤
│ 7. contested_hist_interp │ 8. contradictory_sources │ 9. visual_script_sync │
│    • 8 Consensus States  │    • Preserved conflict  │    • Render vs Voice  │
│    • Event vs Theory     │    • Non-averaging rule  │    • Dataset lineage  │
└──────────────────────────┴──────────────────────────┴───────────────────────┘
```

### Category Definitions & Benchmark Invariants

1. **`general_factual`**:
   - **Scope**: Established encyclopedic, astronomical, and geographical facts.
   - **Target**: Evaluates baseline NLI entailment and 13-tier taxonomy filtering.
2. **`numerical_integrity`**:
   - **Scope**: Complex quantitative claims, percentage changes, orders of magnitude, and unit conversions.
   - **Target**: Evaluates dimensional analysis, compound math consistency, and $\pm \epsilon$ tolerance boundaries.
3. **`quote_veracity`**:
   - **Scope**: Historical quotes, public speeches, legal testimony, and famous apocryphal quotations.
   - **Target**: Evaluates normalized Levenshtein distance, speaker attribution, and conversion to paraphrase upon verbatim divergence.
4. **`scientific_mechanisms`**:
   - **Scope**: Peer-reviewed biology, chemistry, computer architecture, and quantum mechanics.
   - **Target**: Evaluates whether claims assert unverified causal hypotheses as established physical laws.
5. **`current_events_temporal`**:
   - **Scope**: Rapidly evolving contemporary events, leadership appointments, and records.
   - **Target**: Evaluates temporal validity anchors (`as_of_date`) and flags outdated claims.
6. **`historical_facts`**:
   - **Scope**: Documented primary archival occurrences, dates, treaties, and technological breakthroughs.
   - **Target**: Enforces prohibition of sole web sources and verifies Tier 1–4 primary grounding.
7. **`contested_historical_interpretations`**:
   - **Scope**: Competing historical paradigms, causality of revolutions, and economic crises.
   - **Target**: Assesses accurate classification into the 8 `ConsensusState` categories and calibrated script rhetoric.
8. **`contradictory_sources`**:
   - **Scope**: Conflicting casualty figures, rival invention attributions, and contested economic indicators.
   - **Target**: Assesses enforcement of the Non-Averaging Contradiction Invariant.
9. **`visual_script_consistency`**:
   - **Scope**: Storyboard `ProductionIRDocument` scene parameters vs concurrent `ScriptBeat` voiceover audio.
   - **Target**: Detects visual/spoken numerical discrepancies, timeline date mismatches, and ungrounded chart parameters.

---

## 3. Hybrid Execution Architecture: Offline Fixtures & Live Connectors

To guarantee both **100% hermetic determinism in CI/CD** and **real-world evaluation capability**, `H9-FactBench` uses a dual-engine architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FACTBENCH RUNNER                                  │
└──────────────────────┬──────────────────────────────┬───────────────────────┘
                       │                              │
       [CI/CD Hermetic Mode]                  [Live Scholarly Mode]
                       │                              │
                       ▼                              ▼
┌──────────────────────────────┐       ┌──────────────────────────────┐
│   HERMETIC OFFLINE FIXTURES  │       │   LIVE SCHOLARLY CONNECTORS  │
│  • Local JSON/YAML datasets  │       │  • OpenAlex / Crossref API   │
│  • Curated Evidence Graphs   │       │  • Europe PMC / PubMed API   │
│  • Zero network egress       │       │  • arXiv API                 │
│  • 100% deterministic runs   │       │  • Semantic Scholar API      │
└──────────────────────────────┘       └──────────────────────────────┘
```

1. **Hermetic Offline Mode (`--mode=offline`)**:
   - Runs against curated, verified fixtures located in `tests/fixtures/factbench/`.
   - Requires zero network connectivity, zero API keys, and executes in $< 30$ seconds.
   - Standard mode for GitHub Actions, pre-commit hooks, and regression verification.
2. **Live Scholarly Mode (`--mode=live`)**:
   - Connects to authoritative open-access academic APIs (OpenAlex, Europe PMC, Crossref, arXiv) via rate-limited, exponential-backoff clients.
   - Periodically audits live research queries against newly published scholarly literature.

---

## 4. Mathematical Metric Formulations

`H9-FactBench` computes quantitative evaluation metrics across 5 core dimensions:

### 4.1 Precision of Verification ($P_{\text{verif}}$)
Measures the proportion of verified claims that are genuinely true according to benchmark ground truth:
$$P_{\text{verif}} = \frac{\text{True Positives (Accurately Verified)}}{\text{True Positives} + \text{False Positives (Hallucinations Verified)}}$$

### 4.2 Recall of Contradictions ($R_{\text{contra}}$)
Measures the ability of the engine to detect and flag genuine contradictions and apocryphal myths:
$$R_{\text{contra}} = \frac{\text{Detected Contradictions}}{\text{Total Actual Contradictions in Benchmark}}$$

### 4.3 Historiographical Calibration ($S_{\text{hist}}$)
Evaluates agreement between the predicted consensus state and the ground-truth scholarly consensus:
$$S_{\text{hist}} = \frac{1}{N} \sum_{i=1}^{N} \mathbf{1}(\text{PredictedState}_i == \text{GroundTruthState}_i)$$

### 4.4 Visual-Narrative Alignment ($S_{\text{vis}}$)
Percentage of visual scene parameters perfectly aligned with spoken narration and primary datasets:
$$S_{\text{vis}} = \frac{\text{Aligned Visual Scene Blocks}}{\text{Total Evaluated Visual Blocks}}$$

### 4.5 Numerical Accuracy Index ($S_{\text{num}}$)
Evaluates mathematical calculation accuracy and tolerance compliance:
$$S_{\text{num}} = \frac{\text{Valid Numerical Assertions}}{\text{Total Numerical Claims Evaluated}}$$

### 4.6 Epistemic Composite Quality Score ($S_{\text{factbench}}$)
The overall FactBench composite quality metric combines all dimensions:

$$\boxed{S_{\text{factbench}} = 0.25 \cdot P_{\text{verif}} + 0.20 \cdot R_{\text{contra}} + 0.20 \cdot S_{\text{hist}} + 0.20 \cdot S_{\text{vis}} + 0.15 \cdot S_{\text{num}}}$$

---

## 5. Benchmark Fixture Contract Schema (`FactBenchTestCase`)

```python
class FactBenchTestCase(H9BaseModel):
    """Schema for individual H9-FactBench test cases."""
    test_case_id: str = Field(..., min_length=1)
    category: str                                # One of the 9 benchmark categories
    assertion_text: str = Field(..., min_length=1)
    expected_status: EpistemicStatus
    expected_consensus_state: Optional[ConsensusState] = None
    expected_claim_type: ClaimType
    ground_truth_dataset: Optional[Dict[str, Any]] = None
    primary_source: SourceRecord
    corroborating_sources: List[SourceRecord] = Field(default_factory=list)
    conflicting_sources: List[SourceRecord] = Field(default_factory=list)
    forbidden_sole_sources: List[str] = Field(default_factory=list)
    adversarial_mutations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

---

## 6. Integration with ContentBench Quality OS

`H9-FactBench` integrates directly into **ContentBench** (`src/evaluation/contentbench.py`), replacing the heuristic Layer 1 ($S_{\text{research}}$) and upgrading Layer 3 ($S_{\text{video}}$):

$$\begin{aligned}
S_{\text{research}}^{\text{new}} &= 0.60 \times S_{\text{factbench}}^{\text{epistemic}} + 0.40 \times S_{\text{research}}^{\text{density}} \\
S_{\text{video}}^{\text{new}} &= 0.50 \times S_{\text{video}}^{\text{acoustic}} + 0.50 \times S_{\text{vis}}^{\text{alignment}}
\end{aligned}$$

This ensures that ContentBench cannot award an "A+ Exemplar" or "A Broadcast" grade to any production that fails epistemic grounding.
