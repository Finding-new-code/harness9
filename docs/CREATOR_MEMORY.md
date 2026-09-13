# Creator Memory & Brand Constitution Specification: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/creator/`  
**Cross-References:** `docs/DATA_MODEL.md`, `docs/EVOLUTION_SPEC.md`, `docs/adrs/ADR-004.md`  

---

## 1. Architectural Role & Cognitive Model

The **Creator DNA & Memory Architecture** captures the unique voice, aesthetic taste, pedagogical standards, and learned experiences of a content creator. It ensures that videos produced by Harness 9 possess a distinct, authentic creative identity rather than generic AI output.

```
                              ┌─────────────────────────────┐
                              │         CREATOR DNA         │
                              └──────────────┬──────────────┘
                                             │
      ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
      ▼                  ▼                   ▼                   ▼                  ▼
┌───────────┐      ┌───────────┐       ┌───────────┐       ┌───────────┐      ┌───────────┐
│   Brand   │      │  Creator  │       │  Creator  │       │  Creator  │      │Performance│
│Constitution│     │Preferences│       │  Skills   │       │ Examples  │      │  Memory   │
└───────────┘      └───────────┘       └───────────┘       └───────────┘      └───────────┘
                                             │
                                             ▼
                                     ┌───────────────┐
                                     │   Negative    │
                                     │    Memory     │
                                     └───────────────┘
```

---

## 2. The 6 Components of Creator DNA

### 2.1 Component 1: Brand Constitution
The foundational editorial philosophy and ethical guardrails of the channel:
- **Mission Statement**: Core pedagogical objective (e.g. *"Demystify deep hardware engineering through rigorous historical context and animated schematic breakdowns"*).
- **Tone of Voice Parameters**: 3–5 tone descriptors (e.g. `authoritative`, `curious`, `accessible`, `unpretentious`).
- **Non-Negotiable Anti-Patterns**: Prohibited words (e.g. `game-changer`, `revolutionize`, `mind-blowing`, `in this video we will`), forbidden tropes, and copyright rules.
- **Target Audience Level**: Target comprehension level (e.g. `Intermediate Hardware Engineer / General Tech Learner`).

### 2.2 Component 2: Creator Preferences
Aesthetic, pacing, and formatting defaults:
- **Pacing Profile**: Target speaking rate ($145\text{ WPM}$), scene transition tempo ($4.5\text{s}$ average scene duration), asset density ($2.0\text{ visuals per 10s}$).
- **Brand Palette & Style Tokens**:
  - Primary Accent: `#00d2ff` (Electric Cyan)
  - Background: `#0a0e17` (Deep Obsidian)
  - Text: `#ffffff` (Pure White)
  - Contrast Accent: `#ff5252` (Coral Flame)
- **Typography Tokens**: Header font (`Inter Tight`, 700 weight), body font (`Inter`, 400 weight), monospace accent (`JetBrains Mono`).
- **GSAP Transition Preferences**: Default easing (`power2.out`), duration ($0.8\text{s}$).

### 2.3 Component 3: Creator Skills & Domain Lexicon
Specialized subject-matter knowledge:
- **Domain Specializations**: e.g. `Semiconductor Physics`, `Computer Architecture`, `Distributed Systems`.
- **Specialized Vocabulary**: Pronunciation guides and domain-specific terms (e.g. `FinFET`, `EUV Photolithography`, `Von Neumann Bottleneck`).
- **Preferred Visual Archetypes**: e.g. `Interactive Block Diagrams`, `Timeline Callouts`, `Animated Silicon Wafers`.

### 2.4 Component 4: Creator Examples (Few-Shot Bank)
Curated high-performing exemplar pairs:
- **Hook Exemplars**: Examples of high-retention openings with labeled curiosity gap formulas.
- **Scene Breakdown Exemplars**: Pairings of concise voiceover scripts with rich visual descriptions.

### 2.5 Component 5: Performance Memory
Historical audience analytics and correlation patterns:
- **AVD & Retention Telemetry**: Top 10% highest-retention video structures.
- **Learned Success Formulas**: Observed positive correlation between opening contrarian statements and 30-second completion rates.

### 2.6 Component 6: Negative Memory
Explicit failure repository and constraint generator:
- **Historical Failure Log**: Record of rejected angles, confusing analogies, and viewer drop-off incidents.
- **Dynamic Constraint Engine**: Compiles active negative constraints injected into LLM prompt headers to prevent repeating past mistakes.

---

## 3. Storage, Indexing & Persistence

```
~/.hermes/creators/<creator_id>/
├── constitution.yaml            # Brand Constitution & Anti-Patterns
├── preferences.yaml             # Pacing, Colors, Typography, GSAP Easing
├── skills.yaml                  # Domain Lexicon & Visual Archetypes
├── exemplars/                   # Few-Shot Hook & Script Examples
│   ├── hooks.json
│   └── storyboards.json
└── memory/                      # Performance & Negative Memories
    ├── performance_history.json
    └── negative_rules.json
```

---

## 4. Prompt Synthesis & Conditioning Flow

When generating a script or outline, the `CreatorDNAStore` compiles the active context into structured prompt headers:

```markdown
## CREATOR IDENTITY: Quantum Frontier
- Tone: Authoritative, Curious, Accessible
- Target Cadence: 145 WPM (approx. 72 words for 30s)

## BRAND CONSTITUTION GUARDRAILS
- PROHIBITED WORDS: "game-changer", "revolutionary", "in this video"
- MANDATORY: Open with an immediate cognitive curiosity gap.

## NEGATIVE CONSTRAINTS (LEARNED FROM PRIOR RUNS)
- Avoid passive voice in opening sentence.
- Do not introduce more than 2 technical acronyms without immediate visual labeling.
```
