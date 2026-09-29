# Milestone 3 (R3) Deep-Dive Analysis: The 7 Verification Strategies & Claim-Type Policy Dispatch

**Document Version:** 1.0.0  
**Status:** Canonical Engineering Specification & Implementation Recommendation  
**Author:** explorer_1_m3  
**Target Milestone:** Milestone 3 (R3) — Epistemic Verification Layer  
**Target Package:** `src/epistemic/` (`strategies/`, `engine.py`, `policy.py`, `historical.py`), `src/models/contracts.py`  
**Referenced Specifications:** `docs/epistemic/FACT_CHECKING_SPEC.md`, `docs/epistemic/CLAIM_VERIFICATION.md`, `docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md`, `docs/epistemic/EPISTEMIC_ARCHITECTURE.md`, `src/epistemic/graph.py`, `src/models/contracts.py`

---

## 1. Executive Summary & Problem Scope

Milestone 3 (Requirement R3) of the **Harness 9 Epistemic Verification Layer** constructs the core verification machinery: the **7 specialized verification strategies** and the **Claim-Type Policy Dispatch Engine**.

In autonomous multi-modal media production, verification cannot be treated as a single semantic similarity check or an unguided LLM completion. A quote attribution requires character-level string alignment; an economic metric requires dimensional and tolerance calculations; a historical causal argument requires historiographical consensus modeling; an astronomical or quantum mechanism requires peer-reviewed backing; and an emerging news report requires temporal anchoring.

This analysis provides the complete architectural and mathematical design for:
1. **Strategy 1: `SOURCE_ENTAILMENT`**: Natural language inference (NLI) scoring between atomic propositions and source passages, scaled by the 13-tier source hierarchy ($W_{\text{tier}}$), with assertion-strengthening detection.
2. **Strategy 2: `CROSS_SOURCE_CORROBORATION`**: Multi-source graph agreement with strict publisher, domain, and wire independence calculus, penalizing circular syndication and single-source vulnerabilities.
3. **Strategy 3: `CONTRADICTION_CHECK`**: High-sensitivity detection of polar negations, numerical variances, attribution rivalries, and chronological conflicts, enforcing the **Non-Averaging Contradiction Invariant** via explicit `ContradictionRecord` structures.
4. **Strategy 4: `QUOTE_CHECK`**: Character-level Levenshtein distance matching against primary transcripts, enforcing exact quote thresholds or mandating conversion to indirect discourse (the **Paraphrase Mandate**).
5. **Strategy 5: `NUMERICAL_CHECK`**: Dimensional extraction, SI unit normalization, mathematical tolerance boundaries ($\pm 0.1\%$ exact, $\pm 5\%$ approximate), magnitude mismatch traps ($10\times$ error traps), and compound arithmetic validation.
6. **Strategy 6: `TEMPORAL_CHECK`**: Temporal anchor extraction, causal chronology precedence ($Date(E_1) < Date(E_2)$), historical entity anachronism scanning, and temporal freshness validation.
7. **Strategy 7: `HISTORIOGRAPHICAL_CHECK`**: Enforcement of the **Historical Scholarship Policy**, blocking sole web sources (Tiers 9–13), enforcing minimum evidentiary thresholds, categorizing scholarly literature into the **8-State Consensus Model**, and separating empirical events from historiographical interpretations.
8. **Claim-Type Policy Dispatch**: Formal policy profiles for 6 canonical claim types (`SCIENTIFIC_LAW`, `NUMERICAL_METRIC`, `DIRECT_QUOTE`, `CURRENT_EVENT`, `TECHNICAL`, `HISTORICAL`), specifying mandatory strategy sets, pass/warn/block score thresholds, and deterministic failure behaviors.

---

## 2. Architectural Foundations & Existing Contracts

### 2.1 Upstream Contracts (`src/models/contracts.py`)
Milestone 2 established the core epistemic models in `src/models/contracts.py`:
- `EpistemicStatus` (11 states): `VERIFIED`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTESTED`, `CONTRADICTED`, `UNSUPPORTED`, `UNVERIFIABLE`, `OUTDATED`, `MISLEADING`, `OPINION`, `PREDICTION`.
- `SourceTier` (13 tiers): `PRIMARY_SOURCE` (1) through `UNVERIFIED` (13) with default weights $W_{\text{tier}} \in [1.00, 0.00]$.
- `ConsensusState` (8 states): `STRONG_CONSENSUS`, `BROAD_CONSENSUS`, `MAJORITY_INTERPRETATION`, `MINORITY_INTERPRETATION`, `ACTIVE_DEBATE`, `CONTESTED`, `UNRESOLVED`, `INSUFFICIENT_LITERATURE`.
- `ClaimType` (8 types): `EVENT_FACT`, `CAUSAL_INTERPRETATION`, `SCHOLARLY_INTERPRETATION`, `NUMERICAL_METRIC`, `DIRECT_QUOTE`, `SCIENTIFIC_LAW`, `CURRENT_EVENT`, `DEFINITIONAL`.
- `QuoteExactness`: `EXACT`, `ELLIPSES`, `PARAPHRASE`, `DISTORTED`, `NOT_APPLICABLE`.
- `ClaimRecord`: Stores `epistemic_status`, `consensus_state`, `source_tier`, `source_quality`, `corroboration_set`, `temporal_context`, `verifier_metadata`, `contradicting_sources`, and `evidence_links`.

### 2.2 Evidence Graph DAG (`src/epistemic/graph.py`)
`EvidenceGraph` provides the machine-readable DAG connecting:
$$\text{SourceNode} \xrightarrow{\text{DERIVES\_FROM}} \text{PassageNode} \xrightarrow{\text{DERIVES\_FROM}} \text{EvidenceUnitNode} \xrightarrow{\text{ENTAILMENT / CONTRADICTION}} \text{ClaimNode}$$
And downstream:
$$\text{ClaimNode} \xrightarrow{\text{ENTAILMENT}} \text{ScriptSentenceNode}, \quad \text{ClaimNode} \xrightarrow{\text{VISUAL\_DEPICTION}} \text{VisualElementNode}$$
Lineage is traversed backward via `trace_lineage(target_node_id) -> ProvenanceChain`, and forward via `topological_sort()`.

### 2.3 Verification Strategy Execution Model
When `VerificationEngine.verify_claim(claim, graph)` executes:
1. `claim.claim_type` is resolved to a `PolicyProfile`.
2. Mandatory and optional strategies are instantiated and executed in sequence.
3. Strategy outputs are collected into a composite `VerificationResult`.
4. The **Status Decision Function** computes the final `EpistemicStatus`.
5. A `VerificationTraceNode` is added to `EvidenceGraph` and linked to the `ClaimNode` via `DERIVES_FROM`.
6. Any contradictions detected are registered as `GraphEdge(..., relation=EdgeRelation.CONTRADICTION)` and recorded in `VerificationResult.contradictions`.

---

## 3. Deep Investigation of the 7 Verification Strategies

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                        VERIFICATION STRATEGY SUITE                                │
├───────────────────────────────────┬───────────────────────────────────────────────┤
│ 1. SOURCE_ENTAILMENT              │ 2. CROSS_SOURCE_CORROBORATION                 │
│    • S_entail = max[W_tier * P]   │    • S_corrob = 1 - prod(1 - W_tier * I_indep)│
│    • Modality strengthening check │    • Root domain & wire syndication filter    │
├───────────────────────────────────┼───────────────────────────────────────────────┤
│ 3. CONTRADICTION_CHECK            │ 4. QUOTE_CHECK                                │
│    • Non-averaging invariant      │    • Levenshtein D_norm <= 0.02 (EXACT)       │
│    • Preserves opposing edges     │    • Paraphrase mandate if D_norm > 0.02      │
├───────────────────────────────────┼───────────────────────────────────────────────┤
│ 5. NUMERICAL_CHECK                │ 6. TEMPORAL_CHECK                             │
│    • SI base unit normalization   │    • Chronological precedence (E1 < E2)       │
│    • Exact eps=0.1%, approx eps=5%│    • Anachronism scanner & freshness anchors  │
├───────────────────────────────────┴───────────────────────────────────────────────┤
│ 7. HISTORIOGRAPHICAL_CHECK                                                        │
│    • Forbid sole web sources (Tiers 9-13 blocked from establishing facts)         │
│    • 8 Consensus States modeling & Event vs Interpretation separation             │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 Strategy 1: `SOURCE_ENTAILMENT`

#### Objective & Mathematical Formulation
Calculates whether linked passage nodes $\{P_1, P_2, \dots, P_n\}$ logically entail claim $C$:
$$S_{\text{entail}}(C) = \max_{P_i \in \text{Passages}} \left[ W_{\text{tier}}(P_i) \times P(P_i \models C) \right]$$
Where:
- $P(P_i \models C) \in [0.0, 1.0]$ is the natural language inference entailment probability.
- $W_{\text{tier}}(P_i) \in [0.0, 1.0]$ is the source authority weight derived from `SourceTier`:
  $$W_{\text{tier}} = \begin{cases}
  1.00 & \text{Tier 1 (PRIMARY\_SOURCE)} \\
  0.98 & \text{Tier 2 (PEER\_REVIEWED\_JOURNAL)} \\
  0.95 & \text{Tier 3 (ACADEMIC\_BOOK / PRESS)} \\
  0.90 & \text{Tier 4 (SCHOLARLY\_CONFERENCE)} \\
  0.88 & \text{Tier 5 (INSTITUTIONAL\_REPORT)} \\
  0.92 & \text{Tier 6 (ARCHIVAL\_DOCUMENT)} \\
  0.80 & \text{Tier 7 (REFERENCE\_WORK)} \\
  0.75 & \text{Tier 8 (EXPERT\_ANALYSIS)} \\
  0.70 & \text{Tier 9 (REPUTABLE\_JOURNALISM)} \\
  0.55 & \text{Tier 10 (TRADE\_PUBLICATION)} \\
  0.35 & \text{Tier 11 (POPULAR\_MEDIA)} \\
  0.20 & \text{Tier 12 (SELF\_PUBLISHED)} \\
  0.00 & \text{Tier 13 (UNVERIFIED)}
  \end{cases}$$

#### Modality & Assertion Strengthening Detection
A common failure in generative research is unearned strengthening: a source notes that a drug *"may reduce symptoms in mice"*, but the generated claim asserts that the drug *"cures the disease"*.

The strategy establishes a 3-tier epistemic modality hierarchy:
- **Level 3 (Certain / Absolute)**: `always`, `proven`, `definitely`, `solely`, `undoubtedly`, `certainly`, `indisputable`, `conclusively`, `cure`, `guaranteed`.
- **Level 2 (Probable / Standard)**: `generally`, `typically`, `the primary`, `most`, `likely`, `usually`, `substantially`, `predominantly`.
- **Level 1 (Tentative / Hedged)**: `may`, `suggests`, `one factor`, `partially`, `possibly`, `could`, `preliminary`, `hypothesized`, `indicates potential`.

**Modality Invariant**:
Let $M(C)$ be the maximum modal level of claim $C$, and $M(P)$ be the modal level of passage $P$.
$$\text{If } M(C) > M(P) \implies \text{flag } \texttt{STRENGTHENED\_ASSERTION\_WARNING}$$
When assertion strengthening is detected without counter-evidence:
- Entailment score is capped at $0.75$.
- Recommended status is downgraded from `VERIFIED` to `PARTIALLY_SUPPORTED`.
- Script generation must inject hedges matching $M(P)$.

#### Hermetic Offline Scoring Implementation
In hermetic/offline execution (zero network egress), $P(P_i \models C)$ is computed deterministically:
1. **Lexical & Semantic Overlap**: Computes token-level precision and recall over non-stopword lemmatized content terms between $P_i$ and $C$.
2. **Polarity Check**: Scans for negative polarity markers (`not`, `never`, `failed`, `refuted`, `disproved`, `none`, `neither`). If polarity diverges (e.g. passage is negative while claim is affirmative), $P(P_i \models C)$ collapses to $0.0$, and $P(P_i \models \neg C)$ increases to $1.0$.
3. **Subject-Predicate Alignment**: Verifies that the primary named entities of $C$ appear in $P_i$ in non-negated grammatical contexts.

---

### 3.2 Strategy 2: `CROSS_SOURCE_CORROBORATION`

#### Objective & Mathematical Formulation
Multi-source agreement cannot simply count citations because syndication wire services (AP, Reuters) and blog aggregators replicate the exact same text across hundreds of URLs, creating the illusion of overwhelming consensus ("false consensus").

The Corroboration Index evaluates true independent sources:
$$S_{\text{corrob}}(C) = 1.0 - \prod_{k=1}^{m} \left( 1.0 - W_{\text{tier}}(S_k) \times I_{\text{indep}}(S_k, S_1) \right)$$
Where:
- $S_1$ is the primary establishing source.
- $\{S_2, \dots, S_{m+1}\}$ are candidate corroborating sources.
- $I_{\text{indep}}(S_k, S_1) \in [0.0, 1.0]$ is the independence coefficient.

#### Independence Calculus ($I_{\text{indep}}$)
The independence engine evaluates five orthogonality dimensions:
1. **Domain Disjointness**:
   $$\text{ExtractRootDomain}(S_k) == \text{ExtractRootDomain}(S_1) \implies I_{\text{indep}} = 0.0$$
   Subdomains (e.g., `news.example.com` and `blog.example.com`) collapse to the same root domain `example.com`.
2. **Wire Syndication Collapse**:
   If passage text or metadata contains news wire markers (`"AP"`, `"Associated Press"`, `"Reuters"`, `"Agence France-Presse"`, `"PR Newswire"`, `"Bloomberg Wire"`), candidate sources are marked as syndicated. Multiple articles carrying the same wire story collapse into a single source node with $I_{\text{indep}} = 0.0$ for all duplicates.
3. **Author Overlap**:
   If $S_k.\text{author} == S_1.\text{author}$ (and author is identified) $\implies I_{\text{indep}} = 0.0$.
4. **Publisher Conglomerate Overlap**:
   If publisher entities are identical (e.g. same academic press imprint or media conglomerate), $I_{\text{indep}}$ is discounted to $0.2$.
5. **Direct Citation Dependency**:
   If Source $S_k$ explicitly cites or links to $S_1$ as its sole authority for the proposition, $I_{\text{indep}} = 0.0$ (citation laundering detection).

#### Single-Source Vulnerability Detection
A claim is flagged with `SINGLE_SOURCE_VULNERABILITY` if:
$$\sum_{k=1}^m I_{\text{indep}}(S_k, S_1) == 0$$
- In historical scholarship and scientific law claims, a single-source vulnerability prevents the claim from ever achieving `VERIFIED` status, regardless of how prestigious the single source is.

---

### 3.3 Strategy 3: `CONTRADICTION_CHECK`

#### Objective & Mathematical Formulation
Evaluates whether any evidence in the graph refutes or directly conflicts with claim $C$:
$$P_{\text{contra}}(C) = \max_{P_j \in \text{Passages}} \left[ W_{\text{tier}}(P_j) \times P(P_j \models \neg C) \right]$$

#### The 4 Canonical Contradiction Classes
1. **Direct Polar Negation**:
   $C_1 \land C_2 \models \bot$. One passage asserts proposition $X$ occurred, while another asserts $X$ did not occur (e.g. *"The reactor core melted"* vs *"The core remained intact"*).
2. **Numerical Incompatibility**:
   Two sources report numerical quantities for the same entity and event that differ beyond the tolerance window $\epsilon$ (e.g. Source A: $20,000$ casualties; Source B: $100,000$ casualties).
3. **Attribution Rivalry**:
   Mutually exclusive actors credited with the exact same singular discovery or milestone (e.g. *"Shockley invented the junction transistor alone"* vs *"Bardeen, Brattain, and Shockley co-invented it"*).
4. **Chronological Conflict**:
   Incompatible dates or temporal orders for the same historical event (e.g. battle occurred on September 12 vs September 14).

#### The Non-Averaging Contradiction Invariant
$$\forall C_A, C_B \text{ such that } C_A.\text{value} \ne C_B.\text{value}, \quad \text{SynthesizeAverage}(C_A, C_B) \to \mathbf{STRICTLY\ PROHIBITED}$$
Generative models frequently resolve conflicts by taking an unprincipled arithmetic mean (e.g., averaging 20,000 and 100,000 into 60,000). This produces **epistemically fabricated content**: no historical document attests to 60,000.

**Invariant Enforcement Protocol**:
1. When a contradiction is detected, create a `ContradictionRecord`.
2. Insert an edge in `EvidenceGraph` with `EdgeRelation.CONTRADICTION`.
3. If both sources have comparable high tiers ($T \le 7$):
   - Set claim status to `CONTESTED`.
   - Set `ConsensusState` to `CONTESTED` or `ACTIVE_DEBATE`.
   - Mandate script generation report the dispute: *"Estimates range from 20,000 to over 100,000..."*
4. If the counter-source has decisively higher tier authority ($W_{\text{tier}}(P_{\text{contra}}) > W_{\text{tier}}(P_{\text{entail}}) + 0.20$):
   - Set claim status to `CONTRADICTED`.
   - Block the claim completely from script inclusion.

---

### 3.4 Strategy 4: `QUOTE_CHECK`

#### Objective & Verbatim Matching
Guarantees that direct speech or text attributed with quotation marks (`"..."`) corresponds verbatim to the primary historical or archival record.

#### Algorithmic Protocol
1. **Quote Extraction & Unicode Normalization**:
   - Extract text enclosed in quotation marks (`"`, `'`, `“`, `”`, `‘`, `’`, `«`, `»`).
   - Normalize smart quotes to standard ASCII `"`.
   - Collapse whitespace sequences (`\s+` $\to$ single space).
   - Strip leading/trailing punctuation and whitespace.
2. **Normalized Character-Level Levenshtein Distance**:
   $$D_{\text{norm}}(Q_{\text{asserted}}, Q_{\text{archive}}) = \frac{\text{Levenshtein}(Q_{\text{asserted}}, Q_{\text{archive}})}{\max(|Q_{\text{asserted}}|, |Q_{\text{archive}}|)}$$
3. **Threshold Classification Matrix**:
   - $D_{\text{norm}} \le 0.02$ ($0\%$ to $2\%$ edit distance, accounting for minor punctuation):
     $\implies \texttt{QuoteExactness.EXACT}$ (Verified exact quote).
   - $0.02 < D_{\norm} \le 0.15$ with standard ellipsis markers (`"..."`, `"[...]"`):
     $\implies \texttt{QuoteExactness.ELLIPSES}$ (Verified quote with editorial ellipses).
   - $D_{\text{norm}} > 0.02$ without valid ellipsis:
     $\implies \texttt{QuoteExactness.DISTORTED}$ (Fabricated, misquoted, or translated quote).

#### The Paraphrase Mandate
If $Q_{\text{asserted}}$ is classified as `DISTORTED`:
- The engine raises `QUOTE_FABRICATION_DETECTED`.
- **Quotation marks are strictly prohibited in the script.**
- The scriptwriter is mandated to rewrite the sentence into indirect discourse:
  - *Prohibited*: `"I have become death, the shatterer of worlds," Oppenheimer said.* (when Sanskrit translation diverges).
  - *Mandated*: *Oppenheimer recalled the Hindu scripture verse concerning becoming death.*
- In `ClaimRecord`, set `quote_exactness = QuoteExactness.PARAPHRASE`.

---

### 3.5 Strategy 5: `NUMERICAL_CHECK`

#### Objective & Quantitative Verification
Guarantees that counts, percentages, physical dimensions, financial numbers, and dates in claims are mathematically accurate, properly dimensioned, and within acceptable empirical tolerances.

#### Quantitative Parsing Pipeline
1. **Entity Extraction**:
   Extracts `(scalar, prefix_multiplier, unit_symbol, qualifier_string)`:
   - Numerical values: integers, decimals, fractions (`3/4`), scientific notation (`1.5e9`).
   - English multipliers: `k` / `thousand` ($10^3$), `M` / `million` ($10^6$), `B` / `billion` ($10^9$), `T` / `trillion` ($10^{12}$).
   - Approximation qualifiers: `approximately`, `around`, `nearly`, `roughly`, `estimated`, `over`, `more than`.
2. **SI Base Unit Normalization**:
   Converts non-standard units to SI base equivalents:
   - Length: nm, $\mu$m, mm, cm, m, km, in, ft, mi $\to$ meters ($m$).
   - Mass: mg, g, kg, ton, lb, oz $\to$ kilograms ($kg$).
   - Time: ms, s, min, hr, day, yr $\to$ seconds ($s$).
   - Digital storage: B, KB, MB, GB, TB $\to$ bytes ($B$) using decimal or binary prefixes.
   - Percentage: $X\% \to X / 100.0$.
3. **Tolerance Window Testing**:
   $$|V_{\text{claim}} - V_{\text{ground\_truth}}| \le \epsilon \times V_{\text{ground\_truth}}$$
   - **Exact Tolerance ($\epsilon = 0.001$, $0.1\%$)**: Applied by default to technical specifications, financial ledger statements, transistor counts, and physical constants.
   - **Approximation Tolerance ($\epsilon = 0.05$, $5.0\%$)**: Permitted only if the claim contains explicit approximation qualifiers (`approximately`, `nearly`, `around`).
   - **Historical Range Tolerance**: For historical claims with surviving archival variances (e.g. army sizes), checks whether $V_{\text{claim}} \in [V_{\min}, V_{\max}]$.
4. **Order-of-Magnitude Mismatch Trap**:
   $$\left| \log_{10}(|V_{\text{claim}}|) - \log_{10}(|V_{\text{ground\_truth}}|) \right| \ge 1.0$$
   Detects common hallucination bugs (e.g., reporting 80 million instead of 80 billion). Immediately raises `ORDER_OF_MAGNITUDE_MISMATCH` and triggers a mandatory `BLOCK`.
5. **Compound Arithmetic Consistency**:
   For assertions declaring derived mathematical relationships (e.g. *"Revenue grew from \$10M to \$30M, a 300% increase"*):
   - Computes expected $\Delta = \frac{30 - 10}{10} \times 100\% = 200\%$.
   - Flags mismatch ($300\% \ne 200\%$) as `MATHEMATICAL_CALCULATION_ERROR`.

---

### 3.6 Strategy 6: `TEMPORAL_CHECK`

#### Objective & Chronological Integrity
Ensures chronological causality, scans for historical anachronisms, and verifies time-sensitive freshness.

#### Mechanics
1. **Causal Chronology Precedence**:
   For any claim asserting a causal or sequential relationship ($E_1 \text{ caused } E_2$ or $E_1 \text{ occurred before } E_2$):
   $$\text{Date}(E_1) < \text{Date}(E_2)$$
   If $\text{Date}(E_1) \ge \text{Date}(E_2)$, flags `CHRONOLOGICAL_INCONSISTENCY` (impossible causal direction).
2. **Historical Anachronism Registry**:
   Maintains a curated temporal origin registry of key technologies, concepts, and institutions $[T_{\text{origin}}, T_{\text{end}}]$:
   - Printing Press: $1440$
   - Steam Engine: $1712$
   - Telegraph: $1837$
   - Transistor: $1947$
   - ARPANET: $1969$
   - World Wide Web: $1989$
   If a script claims Julius Caesar communicated via telegraph ($1837 > -44$), the claim is flagged as anachronistic.
3. **Temporal Freshness & Dynamic Claims**:
   Claims asserting dynamic records or superlatives (*"fastest supercomputer"*, *"most valuable company"*, *"current prime minister"*):
   - Must specify an explicit `as_of_date` or temporal anchor (*"as of 2024"*).
   - If the anchor is absent, or if verified records show the title has been superseded, status is set to `OUTDATED`.

---

### 3.7 Strategy 7: `HISTORIOGRAPHICAL_CHECK`

#### Objective & Historiographical Governance
Enforces the **Historical Scholarship Policy** (`docs/epistemic/HISTORICAL_SCHOLARSHIP_POLICY.md`), guarding against popular digital myths, single-source web summaries, and monocausal historical flattening.

#### Historiographical Rules
1. **The Forbidden Sole Source Rule**:
   - No historical claim (`EVENT_FACT`, `CAUSAL_INTERPRETATION`, `SCHOLARLY_INTERPRETATION`) may be established by a single web summary, blog, or crowdsourced wiki (Tiers 9–13).
   - Violation raises `POLICY_VIOLATION_UNQUALIFIED_HISTORICAL_SOURCE` and assigns status `UNSUPPORTED`.
2. **Minimum Evidentiary Thresholds**:
   Must satisfy at least one:
   - **Threshold A (Primary)**: $\ge 1$ verified Tier 1 (`PRIMARY_SOURCE`) or Tier 6 (`ARCHIVAL_DOCUMENT`).
   - **Threshold B (Academic Monograph)**: $\ge 1$ verified Tier 3 (`ACADEMIC_BOOK` / University Press).
   - **Threshold C (Peer-Reviewed)**: $\ge 2$ independent Tier 2 (`PEER_REVIEWED_JOURNAL`) sources.
3. **The 8-State Consensus Model**:
   Maps literature into:
   - `STRONG_CONSENSUS`: Unanimous baseline; zero modern scholarly dissent; primary archival backing.
   - `BROAD_CONSENSUS`: Overwhelming agreement (>90% of monographs); negligible fringe dissent.
   - `MAJORITY_INTERPRETATION`: Dominant paradigm, but recognized academic counter-hypotheses exist.
   - `MINORITY_INTERPRETATION`: Credible peer-reviewed thesis held by a qualified minority of historians.
   - `ACTIVE_DEBATE`: Substantial debate between multiple competing peer-reviewed interpretations.
   - `CONTESTED`: Mutually exclusive claims supported by contradictory primary accounts or physical evidence.
   - `UNRESOLVED`: Literature explicitly concludes surviving documentary evidence is inconclusive.
   - `INSUFFICIENT_LITERATURE`: $<2$ peer-reviewed citations in academic repositories.
4. **Documented Events vs Causal Interpretations**:
   - `EVENT_FACT`: Empirical occurrence (date, place, actors). Narrated definitively.
   - `CAUSAL_INTERPRETATION`: Historiographical model explaining *why* an event occurred. **Must NEVER be narrated as an uncontested empirical event.** Must be framed with scholarly attribution.
5. **Calibrated Narration Framing**:
   Voiceover scripts must match the rhetoric table (e.g. `ACTIVE_DEBATE` $\implies$ *"Historians remain divided over whether..."*).

---

## 4. Claim-Type Policy Dispatch

Different factual claims require fundamentally different verification standards. Rather than evaluating all claims with a one-size-fits-all formula, the **Policy Dispatch Engine** resolves each `ClaimRecord` to a specialized `PolicyProfile`.

```
                    ┌─────────────────────────┐
                    │      ClaimRecord        │
                    │  (claim_text, category) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ ClaimType Classifier /  │
                    │      claim.claim_type   │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ SCIENTIFIC_LAW   │    │ NUMERICAL_METRIC │    │  DIRECT_QUOTE    │
│ • SOURCE_ENTAIL  │    │ • NUMERICAL_CHECK│    │ • QUOTE_CHECK    │
│ • CROSS_CORROB   │    │ • SOURCE_ENTAIL  │    │ • SOURCE_ENTAIL  │
│ • CONTRADICTION  │    │ • CROSS_CORROB   │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  CURRENT_EVENT   │    │    TECHNICAL     │    │   HISTORICAL     │
│ • SOURCE_ENTAIL  │    │ • SOURCE_ENTAIL  │    │ • HISTORIOGRAPH  │
│ • TEMPORAL_CHECK │    │ • NUMERICAL_CHECK│    │ • SOURCE_ENTAIL  │
│ • CROSS_CORROB   │    │ • CONTRADICTION  │    │ • CONTRADICTION  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

### 4.1 Claim-Type Policy Profiles Matrix

| Policy Profile | Applicable `ClaimType` | Mandatory Strategies | Disallowed Source Tiers | Thresholds | Failure Behavior | Gate Impact |
|---|---|---|---|---|---|---|
| **`SCIENTIFIC`** | `SCIENTIFIC_LAW` | `SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK` | Tiers 11–13 (Blogs, forums, preprints without peer review) | $S_{\text{entail}} \ge 0.85$, $S_{\text{corrob}} \ge 0.80$, $P_{\text{contra}} < 0.20$ | Discard unverified mechanism; downgrade to theoretical hypothesis | `BLOCK` if unhedged |
| **`NUMERICAL`** | `NUMERICAL_METRIC` | `NUMERICAL_CHECK`, `SOURCE_ENTAILMENT`, `CROSS_SOURCE_CORROBORATION` | Tiers 11–13 (Secondary blogs without raw data) | Tolerance $\le 0.1\%$ (exact) or $\le 5\%$ (approx); Magnitude error $= 0$ | Flag order-of-magnitude mismatch; recalculate compound percentages | `BLOCK` on math/magnitude error |
| **`QUOTE`** | `DIRECT_QUOTE` | `QUOTE_CHECK`, `SOURCE_ENTAILMENT` | Tiers 10–13 (Secondary retellings without transcript provenance) | $D_{\text{norm}} \le 0.02$ (exact) or $\le 0.15$ (ellipses) | Strip quotation marks; convert to indirect discourse (Paraphrase Mandate) | `BLOCK` if quotation marks retained |
| **`CURRENT_EVENT`** | `CURRENT_EVENT` | `SOURCE_ENTAILMENT`, `TEMPORAL_CHECK`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK` | Tiers 12–13 (Social media rumors, unvetted forums) | $S_{\text{entail}} \ge 0.80$, Temporal anchor required, Freshness $\le 7$ days | Flag as outdated; mandate explicit temporal anchor ("as of [date]") | `WARN` / `BLOCK` if unanchored |
| **`TECHNICAL`** | `DEFINITIONAL`, Technical `NUMERICAL_METRIC` | `SOURCE_ENTAILMENT`, `NUMERICAL_CHECK`, `CONTRADICTION_CHECK` | Tiers 11–13 (Marketing fluff, unsourced wikis) | $S_{\text{entail}} \ge 0.85$, Spec compliance $\le 0.1\%$ | Flag vendor hype; enforce standard datasheet metrics | `BLOCK` if fabricated spec |
| **`HISTORICAL`** | `EVENT_FACT`, `CAUSAL_INTERPRETATION`, `SCHOLARLY_INTERPRETATION` | `HISTORIOGRAPHICAL_CHECK`, `SOURCE_ENTAILMENT`, `TEMPORAL_CHECK`, `CROSS_SOURCE_CORROBORATION`, `CONTRADICTION_CHECK` | Sole Tiers 9–13 strictly forbidden | Minimum Tier 1–4 threshold met; $P_{\text{contra}}$ preserved; Consensus classified | Reject sole web sources; forbid averaging; mandate consensus framing | `BLOCK` on sole web sources or averaged contradictions |

---

### 4.2 Status Decision Function
The composite verification status is determined by evaluating the strategy scores against the canonical decision matrix (`docs/epistemic/FACT_CHECKING_SPEC.md` Sec 4.4):

```python
def determine_epistemic_status(
    s_entail: float,
    s_corrob: float,
    p_contra: float,
    quote_exactness: Optional[QuoteExactness] = None,
    numerical_valid: Optional[bool] = None,
    temporal_valid: Optional[bool] = None,
    is_outdated: bool = False,
    is_opinion: bool = False,
    is_prediction: bool = False,
    violates_historical_policy: bool = False,
) -> EpistemicStatus:
    """Deterministic, unambiguous decision function for EpistemicStatus assignment."""
    if violates_historical_policy:
        return EpistemicStatus.UNSUPPORTED
    if is_opinion:
        return EpistemicStatus.OPINION
    if is_prediction:
        return EpistemicStatus.PREDICTION
    if is_outdated:
        return EpistemicStatus.OUTDATED
    if numerical_valid is False:
        return EpistemicStatus.CONTRADICTED
    if quote_exactness == QuoteExactness.DISTORTED:
        return EpistemicStatus.MISLEADING

    # Core Mathematical Matrix
    if p_contra >= 0.80 and p_contra > s_entail:
        return EpistemicStatus.CONTRADICTED
    elif p_contra >= 0.60 and s_entail >= 0.60:
        return EpistemicStatus.CONTESTED
    elif s_entail >= 0.90 and s_corrob >= 0.85 and p_contra < 0.20:
        return EpistemicStatus.VERIFIED
    elif s_entail >= 0.80 and p_contra < 0.30:
        return EpistemicStatus.SUPPORTED
    elif 0.60 <= s_entail < 0.80 and p_contra < 0.30:
        return EpistemicStatus.PARTIALLY_SUPPORTED
    else:
        return EpistemicStatus.UNSUPPORTED
```

---

## 5. Concrete Architecture & Implementation Recommendation for Worker M3

Worker M3 should structure `src/epistemic/` as a modular, maintainable subsystem with clear boundaries:

```
src/epistemic/
├── __init__.py               # Exports VerificationEngine, strategies, policy profiles
├── graph.py                  # EvidenceGraph DAG (completed in M2)
├── engine.py                 # VerificationEngine orchestrator & verify_claim / verify_dossier
├── policy.py                 # Claim-type policy definitions & dispatch registry
├── historical.py             # HistoricalScholarshipPolicyEngine / HistoricalPolicyChecker
└── strategies/
    ├── __init__.py           # Strategy registry & BaseVerificationStrategy
    ├── base.py               # Abstract Base Strategy interface & StrategyResult
    ├── entailment.py         # Strategy 1: SourceEntailmentStrategy
    ├── corroboration.py      # Strategy 2: CrossSourceCorroborationStrategy
    ├── contradiction.py      # Strategy 3: ContradictionCheckStrategy & ContradictionRecord
    ├── quote.py              # Strategy 4: QuoteCheckStrategy
    ├── numerical.py          # Strategy 5: NumericalCheckStrategy
    ├── temporal.py           # Strategy 6: TemporalCheckStrategy
    └── historiographical.py  # Strategy 7: HistoriographicalCheckStrategy
```

### 5.1 Base Strategy Interface (`src/epistemic/strategies/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.epistemic.graph import EvidenceGraph
from src.models.contracts import ClaimRecord, H9BaseModel

class StrategyResult(H9BaseModel):
    """Execution output from an individual verification strategy."""
    strategy_name: str
    passed: bool
    score: float = 0.0
    confidence: float = 1.0
    details: Dict[str, Any] = {}
    warnings: List[str] = []
    errors: List[str] = []

class BaseVerificationStrategy(ABC):
    """Abstract base class for all 7 epistemic verification strategies."""

    strategy_name: str

    @abstractmethod
    def evaluate(self, claim: ClaimRecord, graph: EvidenceGraph) -> StrategyResult:
        """Execute verification check against the claim and backing EvidenceGraph."""
        pass
```

### 5.2 Contradiction Record Contract (`src/epistemic/strategies/contradiction.py`)

```python
class ContradictionRecord(H9BaseModel):
    """Immutable record of an identified factual contradiction between sources."""
    contradiction_id: str
    claim_id: str
    contradiction_type: str  # "polar_negation", "numerical_incompatibility", "attribution_rivalry", "chronological_conflict"
    claim_assertion: str
    conflicting_assertion: str
    source_a_id: str
    source_b_id: str
    source_a_tier: int
    source_b_tier: int
    severity: float = 1.0
    mandated_framing: str = ""
    is_resolved_by_averaging: bool = False  # MUST ALWAYS BE FALSE (Non-averaging invariant)
```

### 5.3 Verification Result & Engine Contract (`src/epistemic/engine.py`)

```python
class VerificationResult(H9BaseModel):
    """Composite verification verdict for a single ClaimRecord."""
    claim_id: str
    status: EpistemicStatus
    claim_type: ClaimType
    confidence: float
    entailment_score: float
    corroboration_score: float
    contradiction_score: float
    highest_source_tier: SourceTier
    consensus_state: Optional[ConsensusState] = None
    quote_exactness: Optional[QuoteExactness] = None
    numerical_valid: Optional[bool] = None
    temporal_valid: Optional[bool] = None
    contradictions: List[ContradictionRecord] = []
    warnings: List[str] = []
    flags: List[str] = []
    trace_id: Optional[str] = None
    explanation: str

class DossierVerificationReport(H9BaseModel):
    """Aggregated verification report for an entire ResearchDossier."""
    run_id: str
    total_claims: int
    verified_count: int
    supported_count: int
    contested_count: int
    contradicted_count: int
    unsupported_count: int
    claims_results: Dict[str, VerificationResult]
    gate_recommendation: str  # "PASS", "WARN", "HUMAN_REVIEW", "BLOCK"
    summary_explanation: str
```

### 5.4 Verification Trace DAG Node Creation
Upon completion of `verify_claim(claim, graph)`:
1. `graph.add_verification_trace(target_node_id=claim.claim_id, ...)` creates a `VerificationTraceNode`.
2. The trace node records `entailment_score`, `contradiction_score`, `corroboration_score`, `status_assigned`, and `execution_duration_ms`.
3. `graph.link(claim.claim_id, trace_node_id, EdgeRelation.DERIVES_FROM)` inserts the trace into the DAG.
4. If contradictions exist, `graph.link(claim.claim_id, counter_node_id, EdgeRelation.CONTRADICTION)` is added.

---

## 6. Comprehensive Test Suite Design for Milestone 3

Worker M3 should implement two comprehensive test modules:

### 6.1 `tests/test_verification_engine.py`
1. **`test_source_entailment_scoring`**: Tests entailment scoring across Tiers 1 through 13. Asserts higher tiers yield higher $S_{\text{entail}}$.
2. **`test_assertion_strengthening_detection`**: Verifies that when a source has Level 1 modality ("suggests") and claim has Level 3 ("definitely"), `STRENGTHENED_ASSERTION_WARNING` is raised and status is capped at `PARTIALLY_SUPPORTED`.
3. **`test_cross_source_corroboration_domain_disjointness`**: Confirms that 5 URLs from the same root domain yield $S_{\text{corrob}} = 0.0$, while 3 distinct root domains produce high corroboration.
4. **`test_syndication_wire_collapse`**: Verifies that news articles with `"AP"` attribution collapse into a single source node.
5. **`test_contradiction_detection_non_averaging`**: Tests conflicting casualty numbers ($10,000$ vs $50,000$). Asserts both sources are preserved, status is `CONTESTED`, and no arithmetic average is generated.
6. **`test_quote_check_exact_and_ellipses`**: Verifies $D_{\text{norm}} \le 0.02$ yields `EXACT`, while $0.02 < D_{\text{norm}} \le 0.15$ with ellipses yields `ELLIPSES`.
7. **`test_quote_check_paraphrase_mandate`**: Verifies that distorted quotes trigger `paraphrase_mandated = True` and strip quotation marks.
8. **`test_numerical_check_dimensional_and_tolerances`**: Tests unit conversions ($nm \to m$, $GHz \to Hz$, percentages) and verifies exact vs approximate tolerances.
9. **`test_numerical_order_of_magnitude_trap`**: Confirms that a $10\times$ difference raises `ORDER_OF_MAGNITUDE_MISMATCH` and yields `BLOCK`.
10. **`test_temporal_check_chronology_and_anachronisms`**: Tests causal date precedence and verifies Caesar + telegraph triggers `ANACHRONISM_DETECTED`.
11. **`test_policy_dispatch_routing`**: Asserts that `SCIENTIFIC_LAW` dispatches `CROSS_CORROBORATION`, `NUMERICAL_METRIC` dispatches `NUMERICAL_CHECK`, and `DIRECT_QUOTE` dispatches `QUOTE_CHECK`.

### 6.2 `tests/test_historical_policy.py`
1. **`test_prohibition_of_sole_web_sources`**: Confirms that historical claims backed only by Wikipedia or blogs (Tiers 9–13) receive status `UNSUPPORTED`.
2. **`test_minimum_evidentiary_thresholds`**: Verifies Threshold A (Tier 1/6), Threshold B (Tier 3), and Threshold C (2x Tier 2).
3. **`test_consensus_state_classification`**: Verifies mapping into all 8 `ConsensusState` states.
4. **`test_event_vs_interpretation_separation`**: Asserts that causal hypotheses are not asserted as uncontested empirical facts.
5. **`test_calibrated_narration_framing`**: Verifies that `ACTIVE_DEBATE` mandates balanced dispute rhetoric in script generation.

---

## 7. Actionable Implementation Checklist for Worker M3

- [ ] Create `src/epistemic/strategies/` directory.
- [ ] Implement `src/epistemic/strategies/base.py` with `BaseVerificationStrategy` and `StrategyResult`.
- [ ] Implement `src/epistemic/strategies/entailment.py` with `SourceEntailmentStrategy` and modality strengthening detection.
- [ ] Implement `src/epistemic/strategies/corroboration.py` with `CrossSourceCorroborationStrategy`, root domain extraction, and wire syndication collapse.
- [ ] Implement `src/epistemic/strategies/contradiction.py` with `ContradictionCheckStrategy`, `ContradictionRecord`, and non-averaging preservation.
- [ ] Implement `src/epistemic/strategies/quote.py` with `QuoteCheckStrategy`, normalized Levenshtein calculation, and paraphrase mandate.
- [ ] Implement `src/epistemic/strategies/numerical.py` with `NumericalCheckStrategy`, unit normalizer, tolerance checks, and order-of-magnitude traps.
- [ ] Implement `src/epistemic/strategies/temporal.py` with `TemporalCheckStrategy`, chronology checker, and anachronism scanner.
- [ ] Implement `src/epistemic/strategies/historiographical.py` with `HistoriographicalCheckStrategy`.
- [ ] Implement `src/epistemic/historical.py` with `HistoricalScholarshipPolicyEngine` / `HistoricalPolicyChecker`.
- [ ] Implement `src/epistemic/policy.py` with `ClaimTypePolicyProfile` and `PolicyDispatchRegistry`.
- [ ] Implement `src/epistemic/engine.py` with `VerificationEngine`, `VerificationResult`, `verify_claim`, and `verify_dossier`.
- [ ] Update `src/epistemic/__init__.py` to export all new classes.
- [ ] Write and run `tests/test_verification_engine.py` and `tests/test_historical_policy.py`.
- [ ] Ensure 100% pass rate with zero regressions on existing test suites (`tests/test_contracts.py`, `tests/test_evidence_graph.py`, `tests/test_h9_acceptance.py`).
