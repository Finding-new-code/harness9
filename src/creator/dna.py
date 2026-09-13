"""Harness 9 Creator DNA & Brand Memory Engine (Milestone M5).

Implements the 6-Component Creator DNA cognitive system:
1. Brand Constitution (Mission, tone, guardrails, non-negotiable rules)
2. Creator Preferences (Pacing WPM, colors, typography, aspect ratios)
3. Creator Skills (Domain strengths, technical lexicon, visual archetypes)
4. Creator Examples (Few-shot exemplars across hooks, transitions, storyboards)
5. Performance Memory (Retention curves, drop-off analytics, learned patterns)
6. Negative Memory (Failure logs, prohibited buzzwords, negative prompt constraints)

Provides CreatorDNAStore for persistent storage, memory updates, and LLM prompt conditioning.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import Field, field_validator

from src.creator.memory import (
    LearnedPattern,
    NegativeConstraint,
    NegativeMemory,
    NegativeMistakeRecord,
    PerformanceMemory,
    RetentionCurve,
    RetentionCurvePoint,
)
from src.models.contracts import CreatorProfile, H9BaseModel, LearningCandidate


# ===========================================================================
# 1. Brand Constitution
# ===========================================================================
class BrandConstitution(H9BaseModel):
    """Core editorial philosophy, voice parameters, and non-negotiable guardrails."""
    mission: str = Field(
        default="Demystifying complex technology and science through rigorous historical accuracy and cinematic pacing.",
        min_length=1,
    )
    tone_of_voice: List[str] = Field(
        default_factory=lambda: ["authoritative", "curious", "engaging", "accessible"]
    )
    prohibited_words: List[str] = Field(
        default_factory=lambda: [
            "game-changer",
            "revolutionize",
            "miracle",
            "in this video we will explore",
            "buckle up",
            "mind-blowing",
            "paradigm shift",
        ]
    )
    prohibited_themes: List[str] = Field(
        default_factory=lambda: [
            "Unverified hype statistics",
            "Clickbait sensationalism",
            "Uncited speculation presented as fact",
        ]
    )
    target_audience_level: str = Field(default="intermediate")  # beginner, intermediate, expert
    audience_archetypes: List[str] = Field(
        default_factory=lambda: [
            "Curious Engineers & Developers",
            "Tech Enthusiasts & Lifelong Learners",
            "Decision Makers & Founders",
        ]
    )
    non_negotiable_guardrails: List[str] = Field(
        default_factory=lambda: [
            "Every core technical claim must cite a primary source.",
            "Visual assets must be accurate diagrams or historical imagery, never generic clip art.",
            "Never use hyperbolic buzzwords in hooks or narration.",
        ]
    )


# ===========================================================================
# 2. Creator Preferences
# ===========================================================================
class CreatorPreferences(H9BaseModel):
    """Stylistic, visual, and rhythmic preferences."""
    preferred_wpm: int = Field(default=145, ge=80, le=240, description="Target speaking cadence in words per minute")
    target_scene_duration_sec: float = Field(default=4.5, ge=1.0, le=30.0)
    visual_density_per_min: int = Field(default=12, ge=1, le=60)
    primary_color: str = Field(default="#00d2ff", pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    background_color: str = Field(default="#0a0e17", pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    text_color: str = Field(default="#ffffff", pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    accent_color: str = Field(default="#ff5252", pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    font_heading: str = Field(default="Inter, sans-serif")
    font_body: str = Field(default="Inter, sans-serif")
    font_mono: str = Field(default="JetBrains Mono, monospace")
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")
    easing_function: str = Field(default="power2.out")


# ===========================================================================
# 3. Creator Skills
# ===========================================================================
class CreatorSkills(H9BaseModel):
    """Subject matter competencies, technical lexicon, and visual archetypes."""
    domain_specializations: List[str] = Field(
        default_factory=lambda: [
            "Semiconductor Physics & Microelectronics",
            "Distributed Computing & Cloud Architecture",
            "Aerospace Systems & Orbital Mechanics",
            "Applied AI & Deep Learning Systems",
        ]
    )
    technical_lexicon: Dict[str, str] = Field(
        default_factory=lambda: {
            "MOSFET": "Metal-Oxide-Semiconductor Field-Effect Transistor",
            "EUV": "Extreme Ultraviolet Lithography (13.5nm wavelength)",
            "HBM": "High Bandwidth Memory (3D stacked DRAM)",
            "CUDA": "Compute Unified Device Architecture",
        }
    )
    visual_representation_archetypes: List[str] = Field(
        default_factory=lambda: [
            "interactive_block_diagram",
            "timeline_reveal",
            "stat_counter_card",
            "comparison_split_panel",
            "quote_highlight_box",
        ]
    )
    editorial_archetype_preferences: List[str] = Field(
        default_factory=lambda: ["deep_dive", "data_led", "contrarian"]
    )


# ===========================================================================
# 4. Creator Examples (Few-Shot Exemplars)
# ===========================================================================
class CreatorExample(H9BaseModel):
    """Curated exemplar snippet for few-shot conditioning."""
    example_id: str = Field(..., min_length=1)
    category: str = Field(default="hook")  # hook, intro, transition, explanation, outro
    text: str = Field(..., min_length=1)
    notes: str = ""
    performance_rating: float = Field(default=1.0, ge=0.0, le=1.0)


class CreatorExamples(H9BaseModel):
    """Repository of few-shot exemplars."""
    exemplars: List[CreatorExample] = Field(
        default_factory=lambda: [
            CreatorExample(
                example_id="ex_hook_01",
                category="hook",
                text="In 1947, three physicists at Bell Labs built a fragile sliver of germanium that changed civilization forever.",
                notes="High curiosity gap with specific historical anchor and stakes.",
                performance_rating=0.96,
            ),
            CreatorExample(
                example_id="ex_hook_02",
                category="hook",
                text="Every modern smartphone packs 15 billion transistors into a chip the size of a fingernail. Here is how they do it.",
                notes="Quantitative scale juxtaposition with direct payoff promise.",
                performance_rating=0.94,
            ),
            CreatorExample(
                example_id="ex_trans_01",
                category="transition",
                text="To understand why silicon conquered the world, we first have to look at the vacuum tubes it replaced.",
                notes="Smooth cause-and-effect narrative bridge.",
                performance_rating=0.92,
            ),
        ]
    )

    def get_examples_by_category(self, category: str) -> List[CreatorExample]:
        return [ex for ex in self.exemplars if ex.category == category]

    def get_few_shot_prompt(self, category: str, limit: int = 3) -> str:
        matches = self.get_examples_by_category(category)[:limit]
        if not matches:
            return ""
        lines = [f"### Exemplary {category.capitalize()} Examples (Emulate this style):"]
        for idx, ex in enumerate(matches, 1):
            lines.append(f"{idx}. \"{ex.text}\" ({ex.notes})")
        return "\n".join(lines)


# ===========================================================================
# 5. Master Creator DNA Model
# ===========================================================================
class CreatorDNA(H9BaseModel):
    """Comprehensive Creator DNA cognitive identity."""
    creator_id: str = Field(default="harness9_creator", min_length=1)
    display_name: str = Field(default="Harness 9 Creator", min_length=1)
    brand_constitution: BrandConstitution = Field(default_factory=BrandConstitution)
    preferences: CreatorPreferences = Field(default_factory=CreatorPreferences)
    skills: CreatorSkills = Field(default_factory=CreatorSkills)
    examples: CreatorExamples = Field(default_factory=CreatorExamples)
    performance_memory: PerformanceMemory = Field(default_factory=PerformanceMemory)
    negative_memory: NegativeMemory = Field(default_factory=NegativeMemory)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_creator_profile(self) -> CreatorProfile:
        """Convert CreatorDNA to production contract CreatorProfile."""
        # Combine negative rules
        negative_rules = list(self.brand_constitution.non_negotiable_guardrails)
        negative_rules.extend(self.negative_memory.forbidden_themes)
        for w in self.brand_constitution.prohibited_words:
            negative_rules.append(f"Never use buzzword '{w}'")

        return CreatorProfile(
            creator_id=self.creator_id,
            display_name=self.display_name,
            tone_of_voice=self.brand_constitution.tone_of_voice,
            target_audiences=self.brand_constitution.audience_archetypes,
            brand_colors={
                "primary": self.preferences.primary_color,
                "background": self.preferences.background_color,
                "text": self.preferences.text_color,
                "accent": self.preferences.accent_color,
            },
            default_format=self.preferences.aspect_ratio,
            negative_rules=negative_rules,
            voice_preference="default",
            metadata={
                "preferred_wpm": self.preferences.preferred_wpm,
                "font_heading": self.preferences.font_heading,
                "font_body": self.preferences.font_body,
                "font_mono": self.preferences.font_mono,
                "domain_specializations": self.skills.domain_specializations,
            },
        )

    @classmethod
    def from_creator_profile(cls, profile: CreatorProfile) -> "CreatorDNA":
        """Instantiate CreatorDNA from a CreatorProfile contract."""
        brand = BrandConstitution(
            mission=profile.metadata.get("mission", "Rigorous educational content"),
            tone_of_voice=profile.tone_of_voice,
            audience_archetypes=profile.target_audiences,
        )
        prefs = CreatorPreferences(
            primary_color=profile.brand_colors.get("primary", "#00d2ff"),
            background_color=profile.brand_colors.get("background", "#0a0e17"),
            text_color=profile.brand_colors.get("text", "#ffffff"),
            accent_color=profile.brand_colors.get("accent", "#ff5252"),
            aspect_ratio=profile.default_format,
            preferred_wpm=profile.metadata.get("preferred_wpm", 145),
        )
        neg_mem = NegativeMemory()
        for rule in profile.negative_rules:
            if "buzzword" in rule.lower() or "never use" in rule.lower():
                # Extract quoted buzzwords
                matches = re.findall(r"['\"]([^'\"]+)['\"]", rule)
                for m in matches:
                    neg_mem.add_forbidden_word(m)
            neg_mem.add_forbidden_theme(rule)

        return cls(
            creator_id=profile.creator_id,
            display_name=profile.display_name,
            brand_constitution=brand,
            preferences=prefs,
            negative_memory=neg_mem,
        )

    def build_system_prompt_context(self, stage_name: str = "scriptwriting") -> str:
        """Produce structured system prompt context for LLM guidance."""
        sections = []

        # 1. Mission & Tone
        sections.append(f"## CREATOR BRAND DNA: {self.display_name.upper()}")
        sections.append(f"**Editorial Mission**: {self.brand_constitution.mission}")
        sections.append(f"**Tone of Voice**: {', '.join(self.brand_constitution.tone_of_voice)}")
        sections.append(f"**Audience Level**: {self.brand_constitution.target_audience_level.capitalize()} ({', '.join(self.brand_constitution.audience_archetypes)})")

        # 2. Pacing & Format
        sections.append(f"**Target Cadence**: {self.preferences.preferred_wpm} WPM (approx. {self.preferences.target_scene_duration_sec}s per scene)")

        # 3. Domain Specializations
        if self.skills.domain_specializations:
            sections.append(f"**Domain Focus**: {', '.join(self.skills.domain_specializations)}")

        # 4. Negative Directives
        neg_directives = self.negative_memory.generate_negative_prompt_directives()
        if neg_directives:
            sections.append("### STRICT NEGATIVE CONSTRAINTS (DO NOT VIOLATE):")
            for d in neg_directives:
                sections.append(f"- {d}")

        # 5. Exemplars
        if stage_name in ("scriptwriting", "editorial"):
            hook_examples = self.examples.get_few_shot_prompt("hook", limit=2)
            if hook_examples:
                sections.append(hook_examples)

        return "\n".join(sections)

    def validate_content(self, text: str) -> Dict[str, Any]:
        """Verify text against Brand Constitution and Negative Memory."""
        violations = []
        warnings = []

        # Check negative memory violations
        violations.extend(self.negative_memory.check_violations(text))

        # Check brand constitution prohibited words
        text_lower = text.lower()
        for word in self.brand_constitution.prohibited_words:
            pattern = rf"\b{re.escape(word.lower())}\b"
            if re.search(pattern, text_lower):
                if not any(v.get("pattern") == word for v in violations):
                    violations.append({
                        "type": "brand_prohibited_word",
                        "pattern": word,
                        "severity": "high",
                        "message": f"Brand constitution prohibits buzzword: '{word}'",
                    })

        # Calculate word count and approximate speaking time
        words = len(text.split())
        approx_seconds = (words / self.preferences.preferred_wpm) * 60.0 if self.preferences.preferred_wpm > 0 else 0.0

        is_valid = len([v for v in violations if v.get("severity") in ("critical", "high")]) == 0

        return {
            "valid": is_valid,
            "violations_count": len(violations),
            "violations": violations,
            "warnings": warnings,
            "word_count": words,
            "estimated_spoken_duration_seconds": round(approx_seconds, 2),
        }

    def get_style_tokens(self) -> Dict[str, str]:
        """Return CSS/design token mapping."""
        return {
            "primary": self.preferences.primary_color,
            "background": self.preferences.background_color,
            "text": self.preferences.text_color,
            "accent": self.preferences.accent_color,
            "fontHeading": self.preferences.font_heading,
            "fontBody": self.preferences.font_body,
            "fontMono": self.preferences.font_mono,
            "aspectRatio": self.preferences.aspect_ratio,
            "easing": self.preferences.easing_function,
        }


# ===========================================================================
# 6. Creator DNA Storage & Memory Manager
# ===========================================================================
class CreatorDNAStore:
    """Store for managing, retrieving, and updating Creator DNA instances."""

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None):
        self.storage_dir = Path(storage_dir).resolve() if storage_dir else None
        self._cache: Dict[str, CreatorDNA] = {}
        # Preload default creator
        default_dna = self.register_default_creator()
        self._cache[default_dna.creator_id] = default_dna

    def register_default_creator(self) -> CreatorDNA:
        """Create and register the default standard creator DNA."""
        dna = CreatorDNA(
            creator_id="harness9_creator",
            display_name="Harness 9 Official Creator",
        )
        self._cache[dna.creator_id] = dna
        return dna

    def get_creator_dna(self, creator_id: str) -> CreatorDNA:
        """Fetch CreatorDNA by ID from cache or disk, falling back to default."""
        creator_id = str(creator_id).strip() or "harness9_creator"
        if creator_id in self._cache:
            return self._cache[creator_id]

        # Attempt to load from storage_dir
        if self.storage_dir and self.storage_dir.exists():
            for ext in [".json", ".yaml", ".yml"]:
                file_path = self.storage_dir / f"{creator_id}{ext}"
                if file_path.exists():
                    try:
                        dna = CreatorDNA.load(file_path)
                        self._cache[creator_id] = dna
                        return dna
                    except Exception:
                        pass

        # If not found, return a default customized for this ID
        dna = CreatorDNA(creator_id=creator_id, display_name=f"Creator {creator_id}")
        self._cache[creator_id] = dna
        return dna

    def save_creator_dna(self, dna: CreatorDNA) -> Optional[Tuple[Path, Path]]:
        """Save CreatorDNA to cache and disk if storage_dir is configured."""
        self._cache[dna.creator_id] = dna
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            return dna.save(self.storage_dir, base_name=dna.creator_id)
        return None

    def update_memory(self, creator_id: str, feedback: Dict[str, Any]) -> CreatorDNA:
        """Apply production feedback, retention telemetry, or failure logs to Creator DNA."""
        dna = self.get_creator_dna(creator_id)

        # 1. Retention curve feedback
        if "retention_points" in feedback:
            points_data = feedback["retention_points"]
            points = [
                RetentionCurvePoint(
                    timestamp_sec=p.get("timestamp_sec", 0.0),
                    retention_pct=p.get("retention_pct", 100.0),
                )
                for p in points_data
            ]
            curve = RetentionCurve(
                project_id=feedback.get("project_id", "prod_run"),
                duration_seconds=float(feedback.get("duration_seconds", 30.0)),
                points=points,
            )
            dna.performance_memory.add_retention_curve(curve)

        # 2. Learned pattern feedback
        if "learned_pattern" in feedback:
            pat_data = feedback["learned_pattern"]
            pattern = LearnedPattern(
                pattern_id=pat_data.get("pattern_id", f"pat_{int(datetime.now().timestamp())}"),
                category=pat_data.get("category", "hook_structure"),
                description=pat_data.get("description", "Observation"),
                positive_correlation=pat_data.get("positive_correlation", "Positive boost"),
                confidence_score=float(pat_data.get("confidence_score", 0.85)),
            )
            dna.performance_memory.add_pattern(pattern)

        # 3. Mistake / Negative memory feedback
        if "mistake" in feedback:
            m_data = feedback["mistake"]
            mistake = NegativeMistakeRecord(
                mistake_id=m_data.get("mistake_id", f"mistake_{int(datetime.now().timestamp())}"),
                project_id=feedback.get("project_id", "prod_run"),
                category=m_data.get("category", "editorial"),
                pattern_or_phrase=m_data.get("pattern_or_phrase", "Bad pattern"),
                failure_reason=m_data.get("failure_reason", "Negative audience response"),
                severity=m_data.get("severity", "high"),
            )
            dna.negative_memory.record_mistake(mistake)

        # 4. Prohibited words feedback
        if "forbidden_word" in feedback:
            dna.negative_memory.add_forbidden_word(feedback["forbidden_word"])

        # Save updated DNA
        self.save_creator_dna(dna)
        return dna

    def list_creators(self) -> List[str]:
        """List all creator IDs available in cache and storage."""
        creators = set(self._cache.keys())
        if self.storage_dir and self.storage_dir.exists():
            for p in self.storage_dir.glob("*.json"):
                creators.add(p.stem)
        return sorted(list(creators))

    def delete_creator(self, creator_id: str) -> bool:
        """Remove a creator from cache and disk."""
        removed = False
        if creator_id in self._cache:
            del self._cache[creator_id]
            removed = True
        if self.storage_dir:
            for ext in [".json", ".yaml", ".yml"]:
                p = self.storage_dir / f"{creator_id}{ext}"
                if p.exists():
                    p.unlink()
                    removed = True
        return removed
