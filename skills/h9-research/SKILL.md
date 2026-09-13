---
name: h9-research
description: "Autonomous multi-source research synthesis, claim extraction, and verification for content production."
version: 1.0.0
author: Harness 9, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Content, Research, FactChecking, Verification, H9]
    related_skills: [h9-content-planning, h9-production]
prerequisites:
  commands: [python]
---

# H9 Research & Fact Verification Skill

Autonomous research specialist for the Harness 9 multimedia production pipeline.
Conducts multi-source investigation, extracts verifiable factual claims with quantitative
confidence scoring, tracks primary source provenance, and packages findings into a
validated `ResearchDossier`.

---

## When to Use

- Conducting initial background research for a new video production project.
- Verifying factual claims, statistics, or historical timelines before scriptwriting.
- Expanding broad topic prompts into orthogonal multi-source search vectors.
- Generating candidate visual asset queries and primary reference source records.

## When NOT to Use

- Narrative angle selection or outline drafting (use `h9-content-planning`).
- Audio synthesis, voiceover direction, or asset freezing (use `h9-production`).
- GSAP timeline animation or video compilation (use `h9-hyperframes`).

---

## Quick Reference

- **Invocation Tool**: `h9.research(topic: str, depth: str = "standard", constraints: dict = None)`
- **Depth Parameters**:
  - `overview`: Rapid 15-second scan for high-level concepts and key headlines.
  - `standard`: Balanced 30-second multi-source investigation across 5 query axes.
  - `deep`: Exhaustive 60-second+ deep synthesis delegating to isolated subagents.
- **Output Artifact**: Validated `ResearchDossier` JSON/YAML contract.
- **Verification Threshold**: Factual claims require confidence score $\ge 0.70$ and primary source provenance.

---

## Investigation Methodology

### 1. Orthogonal Query Expansion
To avoid single-source bias, expand the user topic into 5 orthogonal query axes:
1. **Origin & History**: Genesis, pioneering breakthroughs, evolutionary inflection points.
2. **Technical Mechanisms**: Architectural principles, operational mechanics, system design.
3. **Quantitative Metrics**: Benchmarks, empirical measurements, market size, performance data.
4. **Modern Impact**: Contemporary adoption, ecosystem effects, case studies.
5. **Visual Metaphors**: Concrete imagery, diagrams, physical hardware, and reference charts.

### 2. Claim Extraction & Scoring
For every fact retrieved:
- Extract atomic statements into `ClaimRecord` nodes.
- Assign confidence score (0.0 to 1.0) based on source authority and multi-source corroboration.
- Attribute primary source URL, publication title, and author/institution.
- Discard claims scoring $< 0.70$ or flag conflicting data for editorial review.

### 3. Subagent Delegation for Deep Research
When `depth="deep"` is specified:
- Delegate sub-tasks to isolated Hermes subagents via `delegate_subagent`.
- Provide isolated context and restricted toolsets (web search, scraping, calculator).
- Merge subagent findings into the master `ResearchDossier`.

---

## Output Schema: `ResearchDossier`

```json
{
  "dossier_id": "dossier_ai_chips_01",
  "topic": "Semiconductor Lithography Evolution",
  "headline": "Extreme Ultraviolet Lithography at Sub-2nm Scales",
  "executive_summary": "Comprehensive overview of optical versus extreme ultraviolet patterning...",
  "key_takeaways": [
    "ASML High-NA EUV tools achieve 0.55 numerical aperture.",
    "Cost per leading-edge scanner exceeds $350M USD.",
    "Pattern distortion mitigation relies on multi-layer reflective mirrors."
  ],
  "claims": [
    {
      "claim_id": "claim_01",
      "claim_text": "High-NA EUV lithography achieves 0.55 numerical aperture resolution.",
      "confidence_score": 0.98,
      "primary_source": {
        "title": "ASML High-NA Technical Briefing",
        "url": "https://asml.com/technology/high-na",
        "reliability_score": 0.99
      }
    }
  ],
  "suggested_visual_queries": [
    "EUV light source laser produced plasma chamber",
    "Silicon wafer reflective photomask patterning cross section"
  ],
  "confidence_score": 0.96
}
```
