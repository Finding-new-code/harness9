"""src/h9_runtime/skills.py

SkillRuntime protocol and DefaultSkillRuntime implementation.
Governs progressive disclosure skill discovery, YAML frontmatter parsing,
instruction retrieval, and byte-stable system prompt formatting.
"""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable
import yaml

from src.h9_runtime.types import SkillMetadata

logger = logging.getLogger(__name__)


@runtime_checkable
class SkillRuntime(Protocol):
    """Runtime interface for managing and loading agent skills."""

    def discover_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """Discover available skills matching category or platform."""
        ...

    def load_skill_instructions(self, skill_name: str) -> str:
        """Retrieve full Tier 2 instruction content (SKILL.md) for a skill."""
        ...

    def load_skill_resource(
        self,
        skill_name: str,
        relative_path: str,
    ) -> Union[str, bytes]:
        """Retrieve Tier 3 supporting reference, template, or script."""
        ...

    def build_system_prompt_index(self) -> str:
        """Render a byte-stable compact skills index table for system prompt injection."""
        ...


class DefaultSkillRuntime:
    """Concrete implementation of SkillRuntime adhering to the Hermes progressive disclosure model."""

    # Built-in canonical H9 skills definitions for deterministic fallback
    BUILTIN_SKILLS: Dict[str, Dict[str, Any]] = {
        "h9-research": {
            "name": "h9-research",
            "description": "Autonomous multi-source research synthesis, claim extraction, and verification for content production.",
            "version": "1.0.0",
            "author": "Harness 9, Hermes Agent",
            "platforms": ["linux", "macos", "windows"],
            "tags": ["Content", "Research", "FactChecking", "Verification", "H9"],
            "instructions": """# H9 Research & Fact Verification Skill

## Quick Reference
- Conducts multi-source intent query expansion across 5 categories.
- Extracts factual claims with confidence scores >= 0.7.
- Outputs validated `ResearchDossier` JSON/YAML.

## Workflow
1. Ingest topic and duration parameters.
2. Formulate 5 orthogonal queries (origin_history, technical_mechanism, quantitative_metric, modern_impact, visual_queries).
3. Search providers or execute offline procedural benchmark.
4. Score claims and emit `research_dossier.json`.
""",
        },
        "h9-content-planning": {
            "name": "h9-content-planning",
            "description": "Editorial intelligence, 5-archetype angle generation, 9-dimension scorecard evaluation, and 4-act narrative planning.",
            "version": "1.0.0",
            "author": "Harness 9, Hermes Agent",
            "platforms": ["linux", "macos", "windows"],
            "tags": ["Content", "Editorial", "Scriptwriting", "Planning", "H9"],
            "instructions": """# H9 Editorial Intelligence & Content Planning Skill

## Quick Reference
- Generates 5 angle archetypes (contrarian, deep_dive, data_led, human_centric, future_vision).
- Evaluates candidates against the 9-dimension scorecard.
- Synthesizes 4-act narrative outline.

## Workflow
1. Ingest `ResearchDossier`.
2. Generate candidate angles.
3. Compute 9-dimension scores (Audience, Novelty, Hook, Narrative, Creator, Evidence, Visual, Platform, Saturation).
4. Select top angle and construct 4-act outline.
""",
        },
        "h9-production": {
            "name": "h9-production",
            "description": "End-to-end studio production orchestrator: scriptwriting, voice direction, multi-tier asset deduplication, and voice QA.",
            "version": "1.0.0",
            "author": "Harness 9, Hermes Agent",
            "platforms": ["linux", "macos", "windows"],
            "tags": ["Production", "Audio", "TTS", "MediaAssets", "Pipeline", "H9"],
            "instructions": """# H9 Studio Production Skill

## Quick Reference
- Breaks script into timestamped scenes and beats.
- Multi-provider TTS voice synthesis with emotion tagging and WPM clamping (90-220).
- 4-gate Voice QA and SHA-256 / perceptual dHash asset deduplication.

## Workflow
1. Generate `Script`, `SCRIPT.md`, and `STORYBOARD.md`.
2. Synthesize `narration.wav` and audit via VoiceQA.
3. Discover and freeze assets into `assets/images/`.
""",
        },
        "h9-hyperframes": {
            "name": "h9-hyperframes",
            "description": "HyperFrames visual composition compilation, 7 canonical visual component blocks, static linting, and headless MP4 video rendering.",
            "version": "1.0.0",
            "author": "Harness 9, Hermes Agent",
            "platforms": ["linux", "macos", "windows"],
            "tags": ["Video", "HyperFrames", "GSAP", "Animation", "Rendering", "H9"],
            "instructions": """# H9 HyperFrames Video Composition & Rendering Skill

## Quick Reference
- Compiles scenes into 7 canonical visual blocks.
- Generates GSAP timelines synchronized to narration audio.
- Validates hermetic constraints and renders broadcast MP4.

## Workflow
1. Map scenes to component blocks.
2. Compile `index.html`, `styles.css`, `main.js`.
3. Validate composition (0 external URLs, finite repeats).
4. Render video to `renders/final.mp4`.
""",
        },
    }

    def __init__(self, skill_dirs: Optional[List[Path]] = None) -> None:
        self.skill_dirs = skill_dirs or [Path("skills"), Path(".hermes/skills")]

    def _parse_skill_file(self, skill_path: Path) -> Optional[SkillMetadata]:
        """Parse YAML frontmatter from a SKILL.md file."""
        if not skill_path.exists() or not skill_path.is_file():
            return None

        try:
            content = skill_path.read_text(encoding="utf-8")
            frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
            if not frontmatter_match:
                return None

            raw_yaml = frontmatter_match.group(1)
            parsed = yaml.safe_load(raw_yaml)
            if not isinstance(parsed, dict) or "name" not in parsed:
                return None

            metadata_tags = []
            if "metadata" in parsed and isinstance(parsed["metadata"], dict):
                hermes_meta = parsed["metadata"].get("hermes", {})
                if isinstance(hermes_meta, dict):
                    metadata_tags = hermes_meta.get("tags", [])

            return SkillMetadata(
                name=parsed.get("name", skill_path.parent.name),
                description=parsed.get("description", ""),
                version=str(parsed.get("version", "1.0.0")),
                author=parsed.get("author", "Harness 9"),
                platforms=parsed.get("platforms", ["linux", "macos", "windows"]),
                tags=metadata_tags or parsed.get("tags", []),
                skill_dir=skill_path.parent,
            )
        except Exception as exc:
            logger.warning(f"Failed to parse skill at {skill_path}: {exc}")
            return None

    def discover_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """Discover available skills from filesystem and built-ins."""
        discovered: Dict[str, SkillMetadata] = {}

        # 1. Scan filesystem skill directories
        for base_dir in self.skill_dirs:
            if not base_dir.exists() or not base_dir.is_dir():
                continue
            for skill_file in base_dir.glob("**/SKILL.md"):
                meta = self._parse_skill_file(skill_file)
                if meta:
                    discovered[meta.name] = meta

        # 2. Add canonical built-ins if not already present from filesystem
        for name, data in self.BUILTIN_SKILLS.items():
            if name not in discovered:
                discovered[name] = SkillMetadata(
                    name=data["name"],
                    description=data["description"],
                    version=data["version"],
                    author=data["author"],
                    platforms=data["platforms"],
                    tags=data["tags"],
                    skill_dir=Path(f"skills/{name}"),
                )

        results = list(discovered.values())
        if category:
            cat_lower = category.lower()
            results = [
                s for s in results
                if any(cat_lower in t.lower() for t in s.tags) or cat_lower in s.description.lower()
            ]

        # Sort for deterministic byte-stable ordering
        results.sort(key=lambda s: s.name)
        return results

    def load_skill_instructions(self, skill_name: str) -> str:
        """Retrieve full Tier 2 instruction content (SKILL.md) for a skill."""
        # 1. Try finding on disk
        for base_dir in self.skill_dirs:
            candidate = base_dir / skill_name / "SKILL.md"
            if candidate.exists():
                content = candidate.read_text(encoding="utf-8")
                # Return body after frontmatter if present
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    return parts[2].strip()
                return content.strip()

        # 2. Check built-ins
        if skill_name in self.BUILTIN_SKILLS:
            return self.BUILTIN_SKILLS[skill_name]["instructions"].strip()

        raise FileNotFoundError(f"Skill '{skill_name}' not found.")

    def load_skill_resource(
        self,
        skill_name: str,
        relative_path: str,
    ) -> Union[str, bytes]:
        """Retrieve Tier 3 supporting reference, template, or script with path confinement."""
        # Reject path traversal
        clean_rel = Path(relative_path).as_posix()
        if ".." in clean_rel or clean_rel.startswith("/"):
            raise ValueError(f"Path traversal detected in skill resource path: {relative_path}")

        for base_dir in self.skill_dirs:
            resource_file = base_dir / skill_name / relative_path
            if resource_file.exists() and resource_file.is_file():
                try:
                    return resource_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    return resource_file.read_bytes()

        # Fallback description if resource is simulated
        return f"# Reference Resource: {relative_path} for {skill_name}\nSimulated specification."

    def build_system_prompt_index(self) -> str:
        """Render a byte-stable compact skills index table for system prompt injection."""
        skills = self.discover_skills()
        lines = [
            "### Available Skills",
            "| Skill | Description | Platforms |",
            "|---|---|---|",
        ]
        for s in skills:
            platforms_str = ", ".join(s.platforms)
            lines.append(f"| `{s.name}` | {s.description} | {platforms_str} |")

        return "\n".join(lines)
