# Claim Verification Strategies & Algorithmic Engine: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/epistemic/`, `src/verification/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `docs/epistemic/FACT_CHECKING_SPEC.md`  

---

## 1. Executive Summary & Verification Engine Design

The **Harness 9 Claim Verification Engine** is a modular, multi-strategy verification system designed to evaluate diverse proposition types using specialized, explainable algorithms. 

Rather than treating verification as a uniform semantic similarity check, the engine dispatches claims to dedicated strategies:
1. **`SOURCE_ENTAILMENT`**: Natural language inference (NLI) testing whether passage text logically entails the claim and detecting unearned assertion strengthening.
2. **`CROSS_SOURCE_CORROBORATION`**: Graph-based independence analysis verifying corroboration across non-syndicated primary publishers.
3. **`CONTRADICTION_CHECK`**: Detection of mutually exclusive propositions, enforcing the strict non-averaging invariant.
4. **`QUOTE_CHECK`**: Character-level Levenshtein matching and attribution integrity, mandating conversion to paraphrase when verbatim match fails.
5. **`NUMERICAL_CHECK`**: Dimensional analysis, SI unit conversion, and mathematical tolerance verification against ground-truth datasets.
6. **`TEMPORAL_CHECK`**: Chronological precedence evaluation, historical anachronism scanning, and temporal validity intervals.
7. **`HISTORIOGRAPHICAL_CHECK`**: Consensus state classification and compliance with the Historical Scholarship Policy.

---

## 2. The 7 Verification Strategies in Rigorous Detail

### 2.1 Strategy 1: `SOURCE_ENTAILMENT`
- **Objective**: Determine whether an evidence passage $P$ logically entails proposition $C$, refutes $C$, or is neutral.
- **Mathematical Framework**:
  The NLI engine computes a three-class probability distribution over $\{\text{Entailment}, \text{Contradiction}, \text{Neutral}\}$:
  $$P(\text{Entailment}) + P(\text{Contradiction}) + P(\text{Neutral}) = 1.0$$
  - If $P(\text{Entailment}) \ge 0.85$: Status $\to$ `SUPPORTED`.
  - If $P(\text{Contradiction}) \ge 0.80$: Status $\to$ `CONTRADICTED`.
  - Otherwise: Status $\to$ `UNSUPPORTED`.

- **Assertion Strengthening & Hedging Detection**:
  The engine performs modality qualification comparison between passage $P$ and claim $C$:
  Let $M(P)$ and $M(C)$ denote the epistemic strength of modal qualifiers:
  $$\text{Strength} = \begin{cases}
  3 & \text{"always", "proven", "definitely", "solely", "undoubtedly"} \\
  2 & \text{"generally", "typically", "the primary", "most"} \\
  1 & \text{"may", "suggests", "one factor", "partially", "possibly"}
  \end{cases}$$
  **Invariant**: If $M(C) > M(P)$, the engine flags a `STRENGTHENED_ASSERTION_WARNING` and downgrades status to `PARTIALLY_SUPPORTED`, forcing the injection of appropriate hedges during scriptwriting.

---

### 2.2 Strategy 2: `CROSS_SOURCE_CORROBORATION`
- **Objective**: Verify that multiple independent sources confirm the proposition, discounting circular citations, republications, and wire syndication.
- **Independence Calculus**:
  For candidate sources $\{S_1, S_2, \dots, S_n\}$:
  1. **Domain Disjointness**: Root domains must be distinct ($\text{Root}(S_i) \ne \text{Root}(S_j)$).
  2. **Syndication Wire Check**: If text excerpts contain wire attribution markers (`"AP"`, `"Reuters"`, `"PR Newswire"`), they are collapsed into a single source node.
  3. **Author & Citation Trace**: Graph traversal verifies that Source $B$ does not cite Source $A$ as its sole authority.
- **Corroboration Metric**:
  $$S_{\text{corrob}} = 1.0 - \prod_{k=1}^{m} \left( 1.0 - W_{\text{tier}}(S_k) \times I_{\text{indep}}(S_k, S_1) \right)$$
  Where $I_{\text{indep}} \in \{0.0, 1.0\}$ represents boolean independence.

---

### 2.3 Strategy 3: `CONTRADICTION_CHECK`
- **Objective**: Detect conflicting claims within the Evidence Graph or between newly proposed claims and established knowledge.
- **Contradiction Types**:
  1. **Direct Polar Negation**: $C_1 \land C_2 \models \bot$ (e.g. *"Transistor invented at Bell Labs"* vs *"Transistor not invented at Bell Labs"*).
  2. **Numerical Incompatibility**: Values differ beyond tolerance (e.g. $N_1 = 50,000$, $N_2 = 12,000$, with $\pm 5\%$ tolerance).
  3. **Attribution Rivalry**: Mutually exclusive actors credited with the same singular breakthrough (e.g. *"Shockley invented the point-contact transistor alone"* vs *"Bardeen and Brattain created it"*).
- **The Non-Averaging Invariant**:
  When contradiction is detected, the engine **strictly forbids** resolving the conflict by averaging or selecting the most frequent occurrence. It marks the claim as `CONTESTED`, links both sources to an `OpposingAssertionRecord`, and alerts the editorial engine.

---

### 2.4 Strategy 4: `QUOTE_CHECK`
- **Objective**: Enforce verbatim accuracy for direct speech and document excerpts, mandating paraphrase when verbatim text cannot be confirmed.
- **Algorithmic Verification Protocol**:
  1. **Normalization**: Strips typographical quote marks, normalizes smart quotes (`"`, `"` $\to$ `"`), collapses whitespace, and standardizes capitalization.
  2. **Levenshtein Distance Calculation**:
     Computes normalized edit distance between asserted quote $Q_{\text{asserted}}$ and primary archival text $Q_{\text{archive}}$:
     $$D_{\text{norm}}(Q_{\text{asserted}}, Q_{\text{archive}}) = \frac{\text{Levenshtein}(Q_{\text{asserted}}, Q_{\text{archive}})}{\max(|Q_{\text{asserted}}|, |Q_{\text{archive}}|)}$$
  3. **Decision Boundaries**:
     - If $D_{\text{norm}} \le 0.02$: `QUOTE_VERIFIED_EXACT`.
     - If $0.02 < D_{\text{norm}} \le 0.15$ and differences are standard editorial omissions (marked with `...`): `QUOTE_VERIFIED_WITH_ELLIPSES`.
     - If $D_{\text{norm}} > 0.02$ without ellipses: **`QUOTE_FABRICATED_OR_DISTORTED`**.
- **The Paraphrase Mandate**:
  If verbatim match fails, the engine strips quotation marks and rewrites the script beat into an indirect paraphrase:
  *Prohibited*: `"I have become death, the shatterer of worlds," Oppenheimer said.* (if translation diverges)  
  *Mandated*: *Oppenheimer recalled thinking of the Hindu scripture line regarding becoming death.*

---

### 2.5 Strategy 5: `NUMERICAL_CHECK`
- **Objective**: Guarantee that all quantitative figures, metrics, percentages, and units are empirically accurate and mathematically consistent.
- **Dimensional Analysis Protocol**:
  1. **Entity & Unit Parsing**: Deconstructs number string into `(scalar, prefix, unit)`:
     - Examples: `"80 billion transistors"` $\to (80 \times 10^9, \text{unit: count})$; `"5 nm"` $\to (5 \times 10^{-9}, \text{unit: meters})$.
  2. **SI Base Normalization**: Converts non-standard units to SI base units for mathematical equivalence testing.
  3. **Tolerance Window Evaluation**:
     $$|V_{\text{claim}} - V_{\text{ground\_truth}}| \le \epsilon \times V_{\text{ground\_truth}}$$
     - Default $\epsilon = 0.001$ ($0.1\%$) for exact technical and financial metrics.
     - $\epsilon = 0.05$ ($5\%$) permitted only if claim contains explicit approximation qualifiers (*"approximately"*, *"around"*, *"nearly"*).
  4. **Mathematical Consistency**:
     For compound sentences asserting arithmetic relationships (e.g. *"Revenue grew from $10M to $30M, a 300% increase"*), the engine calculates:
     $$\Delta_{\text{expected}} = \frac{30 - 10}{10} \times 100\% = 200\%$$
     Flags calculation error ($300\% \ne 200\%$) and halts verification.

---

### 2.6 Strategy 6: `TEMPORAL_CHECK`
- **Objective**: Ensure chronological precedence, eliminate anachronisms, and verify time-sensitive freshness.
- **Verification Mechanics**:
  1. **Causal Chronology Precedence**: For claims asserting causal relationships ($E_1 \text{ caused } E_2$):
     $$\text{Date}(E_1) < \text{Date}(E_2)$$
     If $\text{Date}(E_1) \ge \text{Date}(E_2)$, the causal assertion is flagged as impossible.
  2. **Anachronism Scanner**: Evaluates named entities against historical existence intervals $[T_{\text{origin}}, T_{\text{end}}]$:
     - Example: A script claiming *"Caesar's engineers communicated via telegraph"* fails because $T_{\text{origin}}(\text{telegraph}) = 1837 > T(\text{Caesar})$.
  3. **Temporal Freshness Interval**: Claims with dynamic validity (*"the fastest supercomputer"*, *"the world's most valuable company"*) must specify an explicit temporal anchor (*"as of 2024"*). If missing, the status is flagged as `OUTDATED`.

---

### 2.7 Strategy 7: `HISTORIOGRAPHICAL_CHECK`
- **Objective**: Enforce the Historical Scholarship Policy, classify consensus states, and distinguish events from interpretations.
- **Execution Protocol**:
  1. **Forbidden Sole Source Verification**: Rejects any historical claim whose sole establishing reference is Tier 9–13.
  2. **Consensus State Classification**: Maps peer-reviewed literature into one of the 8 canonical consensus states.
  3. **Narration Calibrator**: Enforces mandated phrasing rules in generated script drafts.

---

## 3. Verification Strategy Dispatch Engine

The `VerificationEngine` inspects the `ClaimType` and domain metadata to dispatch claims to their mandatory strategy suites:

```python
class VerificationEngine:
    """Orchestrates strategy execution and computes composite EpistemicStatus."""

    STRATEGY_DISPATCH_MAP: Dict[ClaimType, List[str]] = {
        ClaimType.EVENT_FACT: [
            "SOURCE_ENTAILMENT",
            "CROSS_SOURCE_CORROBORATION",
            "TEMPORAL_CHECK",
            "HISTORIOGRAPHICAL_CHECK",
        ],
        ClaimType.CAUSAL_INTERPRETATION: [
            "HISTORIOGRAPHICAL_CHECK",
            "CONTRADICTION_CHECK",
            "CROSS_SOURCE_CORROBORATION",
        ],
        ClaimType.SCHOLARLY_INTERPRETATION: [
            "HISTORIOGRAPHICAL_CHECK",
            "CONTRADICTION_CHECK",
        ],
        ClaimType.NUMERICAL_METRIC: [
            "NUMERICAL_CHECK",
            "SOURCE_ENTAILMENT",
            "CROSS_SOURCE_CORROBORATION",
        ],
        ClaimType.DIRECT_QUOTE: [
            "QUOTE_CHECK",
            "SOURCE_ENTAILMENT",
        ],
        ClaimType.SCIENTIFIC_LAW: [
            "SOURCE_ENTAILMENT",
            "CROSS_SOURCE_CORROBORATION",
            "CONTRADICTION_CHECK",
        ],
        ClaimType.CURRENT_EVENT: [
            "SOURCE_ENTAILMENT",
            "TEMPORAL_CHECK",
            "CROSS_SOURCE_CORROBORATION",
            "CONTRADICTION_CHECK",
        ],
        ClaimType.DEFINITIONAL: [
            "SOURCE_ENTAILMENT",
        ],
    }
```

---

## 4. Verification Trace Audit Schema (`VerificationTrace`)

Every verification check produces an immutable audit record:

```python
class VerificationTrace(H9BaseModel):
    trace_id: str = Field(default_factory=lambda: f"vtr_{uuid.uuid4().hex[:12]}")
    claim_id: str
    strategies_executed: List[str]
    entailment_score: float
    corroboration_score: float
    contradiction_score: float
    numerical_deviation_pct: Optional[float] = None
    levenshtein_distance: Optional[float] = None
    status_assigned: EpistemicStatus
    consensus_state_assigned: Optional[ConsensusState] = None
    warnings: List[str] = Field(default_factory=list)
    verifier_agent: str = "H9EpistemicVerificationEngine"
    execution_duration_ms: float
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
```
