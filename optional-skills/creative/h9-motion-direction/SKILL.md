---
name: h9-motion-direction
description: Shape factual H9 explainers with purposeful motion design.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [H9, Motion Design, Storyboard, Video]
    category: creative
    related_skills: [hyperframes, creative-ideation, grounded-citations]
---

# H9 Motion Direction Skill

Use this skill to give a source-backed H9 explainer a clear visual idea and a distinct motion rhythm. It shapes the storyboard and review; it does not invent facts or certify subjective visual quality.

## When to Use

- Planning or revising an H9 storyboard, scene sequence, or visual direction.
- Reviewing a rendered explainer for repetitive layouts, unreadable titles, or motion that does not support the narration.
- Choosing concise entrance and transition directions for H9 scenes.

Do not use it for claim research, TTS configuration, or publishing; use `h9-research` or `h9-production` for those tasks.

## Prerequisites

- A research dossier with source-linked claims and licensed or generated assets recorded in the asset ledger.
- A configured H9 renderer. The motion presets use the existing GSAP and FFmpeg render path; they add no provider or API key.

## How to Run

For a complete local run, invoke `terminal(command="python run_harness9.py --topic \"<topic>\" --output-dir output/<run-name> --duration 30 --format 16:9", timeout=...)`. Add `--online --model-script` only when live research and model-written narration are intended. Review `DESIGN.md` and `STORYBOARD.md` before sharing the MP4.

For a tool-driven session, use `h9.research` followed by `h9.generate_script` to inspect source-backed material and scene ideas. `h9.render` exports a render that already passed the session checks; it does not rebuild a composition from edited script JSON.

## Quick Reference

| Scene intent | Entrance preset |
| --- | --- |
| Land an opening idea | `rise` |
| Set two sides against each other | `slide_left` |
| Isolate a verified value or detail | `zoom` |
| Uncover a timeline or mechanism | `reveal` |
| Let a new visual carry the beat | `cut` |

Scene exits use `cut` by default. The final scene holds its resolved frame; an authored `fade` is available when the ending needs to disappear.

## Procedure

1. **Choose the film's visual thesis.** Write one sentence describing what the viewer should see happen. Base it on a verified claim or a clearly illustrative metaphor.
2. **Give every scene a job.** Record the viewer takeaway, one focal subject, the visual action, and how the shot leads into the next beat. Drop scenes that only repeat narration.
3. **Choose motion by meaning.** Use `slide_left` for comparisons, `reveal` for ordered change, and `zoom` for a sourced detail. Reserve `rise` for a deliberate entrance. Prefer `cut` when the next image itself supplies the change.
4. **Build one visual system.** Reuse a coherent light, texture, type, and color logic. Vary composition with the subject; do not rotate layouts mechanically.
5. **Keep screen text purposeful.** Do not add default scene numbers, brand badges, counters, or a static narration card. Keep timed captions readable and preserve source context for displayed numbers.
6. **Review the render.** Inspect the opening, one proof scene, the ending, and the contact sheet with `vision_analyze`. Check both 16:9 and 9:16 when both formats are required.
7. **Separate evidence from taste.** Quote the render and media-gate measurements. Describe legibility, pacing, and visual interest as human observations, not verified metrics.

## Pitfalls

- Motion labels are data and resolve to a fixed allowlist. Unknown values fall back to `rise`; never put JavaScript in `entrance_animation`.
- A passing render or media gate checks technical media properties, not whether the film feels original or emotionally clear.
- Use a generated metaphor only as illustration. Do not let imagery imply a specific event, measurement, or source attribution that the dossier does not support.
- Keep the reference project's code and measured precedent library separate; this skill adapts its design workflow to H9 rather than bundling its scripts or data.

## Verification

- The composition validator reports no errors and no decorative scene badge or duplicated narration-card hints.
- The render has the requested dimensions, duration, audio, and passing media gate.
- A human can follow each visual beat without reading invented facts, and all displayed factual text remains traceable to the dossier.
- Record any unresolved crop, contrast, timing, or pronunciation issue in the run notes.

This workflow was inspired by the motion-design review approach in [motionmaxxing](https://github.com/Finding-new-code/motionmaxxing); H9-specific wording and implementation remain in this repository.
