# Original User Request

## Initial Request — 2026-08-31T10:15:35+05:30

Build an automated Proof of Concept (POC) pipeline for Harness 9 that takes a creator topic or brief, conducts web research, downloads and verifies visual assets from open web sources with license tracking, synthesizes voice narration, and generates a short-form video composition rendered via HyperFrames.

Working directory: g:\Finding-new-code\harness9
Integrity mode: development

## Requirements

### R1. Research & Fact Synthesis Engine
Given a topic brief, query the web to extract key facts, statistics, and narrative claims. Output a structured research dossier that includes cited sources, claim confidence, and key talking points for scriptwriting.

### R2. Asset Discovery, Rights Ledger & Local Freezing
Search and download relevant media assets (e.g. from Wikimedia Commons, Pexels, or open web sources). Record license provenance (license type, source URL, author/attribution) in an asset ledger. Ensure all asset dependencies are downloaded and frozen locally before composition rendering.

### R3. Script & Voiceover Generation
Generate a structured video script with timestamped beats, voiceover transcript, and visual cues. Synthesize audio narration using ElevenLabs or a deterministic synthetic TTS fallback if API credentials are not provided.

### R4. HyperFrames Composition & Video Rendering Pipeline
Generate a valid HyperFrames composition (HTML/CSS/GSAP structure following HyperFrames conventions: `BRIEF.md`, `STORYBOARD.md`, `SCRIPT.md`, and composition files). Run validation checks on the composition and render a playable MP4 video file.

### R5. End-to-End Orchestrator & CLI Runner
Provide a unified script or command-line runner that executes the entire pipeline end-to-end from a single topic input to a rendered MP4 output, producing structured artifact files and a summary report of the run.

## Acceptance Criteria

### Automated Pipeline Execution
- [ ] Running the orchestrator command with a sample topic (e.g., "The History of the Transistor" or "How GPUs Work") completes the full flow without unhandled exceptions.
- [ ] Outputs a structured research dossier JSON/YAML containing at least 3 verifiable claims with sources.
- [ ] Outputs an asset provenance ledger JSON/YAML containing downloaded image/media metadata and licensing info.
- [ ] Generates an audio narration file (.mp3 or .wav) synchronized with script beats.

### HyperFrames & Render Validation
- [ ] Generates valid HyperFrames project files (BRIEF.md, STORYBOARD.md, SCRIPT.md, and composition assets).
- [ ] Composition passes HyperFrames validation without broken local assets or missing media paths.
- [ ] Produces a valid, non-empty .mp4 video file in the output directory.

### Verification Suite
- [ ] An automated test/verification script runs the end-to-end pipeline in a test mode and asserts that all stage artifacts (dossier, asset ledger, audio, storyboard, rendered video) are generated and non-empty.
