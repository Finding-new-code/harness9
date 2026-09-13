---
name: h9-content-planning
description: "Editorial intelligence, 5-archetype angle generation, 9-dimension scorecard evaluation, and 4-act narrative planning."
version: 1.0.0
author: Harness 9, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Content, Editorial, Scriptwriting, Planning, H9]
    related_skills: [h9-research, h9-production]
prerequisites:
  commands: [python]
---

# H9 Editorial Intelligence & Content Planning Skill

Editorial intelligence engine for the Harness 9 content creation system.
Transforms verified research dossiers into compelling narrative storylines through
multi-angle ideation, objective 9-dimension scorecard evaluation, hook selection,
and 4-act narrative architecture planning.

---

## When to Use

- Ingesting a `ResearchDossier` to brainstorm narrative approaches.
- Scoring competing story angles using the standardized 9-dimension editorial scorecard.
- Selecting high-retention opening hooks tailored to creator brand DNA.
- Structuring a comprehensive 4-act `ContentOutline` and `Script` with scene timings.

## When NOT to Use

- Raw fact gathering and claim verification (use `h9-research`).
- TTS voice synthesis or media asset downloading (use `h9-production`).
- HTML/CSS composition assembly and video rendering (use `h9-hyperframes`).

---

## Quick Reference

- **Invocation Tool**: `h9.generate_script(outline: dict, dossier: dict, creator: dict = None, format_aspect: str = "16:9", duration: float = 30.0)`
- **Core Archetypes**:
  1. `contrarian`: Inverts accepted wisdom; challenges consensus assumptions.
  2. `deep_dive`: Focuses on technical intricacies and architectural mechanics.
  3. `data_led`: Quantitative narrative anchored by metrics, charts, and inflections.
  4. `human_centric`: Centers on engineers, founders, end users, and cultural impact.
  5. `future_vision`: Extrapolates forward trajectory, scenarios, and second-order effects.
- **Output Artifacts**: `EditorialAngle`, `EditorialScorecard`, `ContentOutline`, `Script`.

---

## Editorial Workflow

### 1. 5-Archetype Candidate Generation
From the input dossier, formulate at least 3 to 5 candidate editorial angles, ensuring each represents a distinct narrative archetype with a clear premise, core thesis, and proposed hook.

### 2. The 9-Dimension Editorial Scorecard
Evaluate each candidate angle across 9 orthogonal dimensions (scored 1 to 10):
1. **Audience Relevance**: Resonates with target viewers' active interests and curiosity.
2. **Novelty**: Delivers fresh insights rather than recycled summaries.
3. **Hook Potential**: Provides an irresistible opening promise within the first 3 seconds.
4. **Narrative Potential**: Sustains dramatic tension, conflict, and logical resolution.
5. **Creator Fit**: Harmonizes with the creator's brand voice, expertise, and style DNA.
6. **Evidence Availability**: Grounded in verified claims from the research dossier.
7. **Visual Potential**: Translates naturally into striking HyperFrames visual components.
8. **Platform Fit**: Matches target aspect ratio (16:9 vs 9:16) and pacing expectations.
9. **Saturation Risk (Inverted)**: Rewards under-explored perspectives; penalizes overdone tropes.

Compute the weighted composite score and rank candidates deterministically to select the winning angle.

### 3. 4-Act Narrative Structuring
Construct a 4-act outline where each act serves a dedicated narrative function:
- **Act 1: Hook & Inciting Question (0% - 25% duration)**
  - Disrupt the viewer's scroll with an unexpected visual collage or paradoxical claim.
  - Component suggestion: `reference_collage_hook` or `split_screen_intro`.
- **Act 2: Context & Evolutionary Progression (25% - 50% duration)**
  - Establish historical baseline and reveal the breakthrough mechanism.
  - Component suggestion: `timeline_reveal` or `quote_highlight`.
- **Act 3: Core Mechanical Demonstration (50% - 75% duration)**
  - Unpack quantitative benchmarks and comparative trade-offs.
  - Component suggestion: `statistic_reveal` or `comparison_panel`.
- **Act 4: Future Trajectory & Climax (75% - 100% duration)**
  - Deliver the decisive synthesis, future outlook, and host wrap-up.
  - Component suggestion: `creator_bottom_collage`.

---

## Output Schema: `Script`

```json
{
  "topic": "Semiconductor Lithography Evolution",
  "title": "The $350M Machine That Powers AI",
  "angle_id": "angle_contrarian_01",
  "total_duration": 30.0,
  "full_transcript": "Every modern AI chip depends on a machine the size of a bus...",
  "scenes": [
    {
      "scene_id": "scene_01",
      "title": "Act 1: The Monopolistic Miracle",
      "start_time": 0.0,
      "duration": 7.5,
      "narration_text": "Every modern AI chip depends on a machine the size of a bus...",
      "component_type": "reference_collage_hook",
      "beats": [
        {
          "beat_id": "beat_01_01",
          "start_time": 0.0,
          "end_time": 3.75,
          "duration": 3.75,
          "text": "Every modern AI chip depends on a machine the size of a bus...",
          "visual_cue": "Stagger image cards into collage"
        }
      ]
    }
  ]
}
```
