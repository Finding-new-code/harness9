"""
src.scriptwriting.generator — Structured Script, Storyboard, Design Gate & Brief Generator.

Generates:
1. BRIEF.md — Topic, audience, target duration, aspect ratio format (16:9 or 9:16), narrative arc.
2. DESIGN.md — HARD GATE: Brand name, 3-5 explicit colors with functional roles, typography, motion mood, and anti-patterns.
3. SCRIPT.md — Scene breakdown with timestamped voiceover beats, duration estimates, and visual cues.
4. STORYBOARD.md — Hero frame descriptions, GSAP entrance animations (gsap.from()), and transitions.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.models.dossier import Claim, ResearchDossier, TalkingPoint
from src.models.ledger import AssetProvenanceLedger, MediaAsset
from src.models.script import Beat, Scene, Script, Storyboard
from src.utils.filesystem import atomic_write, ensure_dir


@dataclass
class ColorRole:
    """Explicit color definition with functional role."""
    name: str
    hex_code: str
    role: str
    rgb: Optional[Tuple[int, int, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hex_code": self.hex_code,
            "role": self.role,
        }


@dataclass
class TypographyStyle:
    """Typography specification for display and body text."""
    family: str
    weight: int
    fallback: str = "sans-serif"
    letter_spacing: str = "normal"
    line_height: float = 1.2

    @property
    def css_font(self) -> str:
        return f"{self.weight} {self.family}, {self.fallback}"


@dataclass
class MotionRules:
    """Motion design system and standard easings."""
    mood: str = "Cinematic & Fluid"
    default_duration_sec: float = 0.6
    standard_easing: str = "power2.out"
    emphasis_easing: str = "elastic.out(1, 0.75)"
    transition_easing: str = "power3.inOut"


@dataclass
class BrandGuidelines:
    """Brand identity specification satisfying the DESIGN.md hard gate."""
    brand_name: str = "Harness9 TechChronicles"
    tagline: str = "Illuminating Breakthrough Science & Computing"
    tone: str = "Authoritative, Cinematic, Modern, Engaging"
    colors: List[ColorRole] = field(default_factory=lambda: [
        ColorRole(name="Background", hex_code="#0a0e17", role="Canvas background & dark surfaces"),
        ColorRole(name="Primary Accent", hex_code="#00d2ff", role="High-contrast hero highlights, borders & kinetic markers"),
        ColorRole(name="Secondary Text", hex_code="#8fa3bf", role="Subtitles, metadata badges & secondary annotations"),
        ColorRole(name="Base Text", hex_code="#ffffff", role="Primary readable narration & headline typography"),
        ColorRole(name="Warning/Alert", hex_code="#ff5252", role="Contrast highlights & focal visual cues"),
    ])
    display_typography: TypographyStyle = field(
        default_factory=lambda: TypographyStyle(family="'Inter Tight'", weight=700, fallback="sans-serif", letter_spacing="-0.02em", line_height=1.1)
    )
    body_typography: TypographyStyle = field(
        default_factory=lambda: TypographyStyle(family="'Inter'", weight=400, fallback="sans-serif", letter_spacing="normal", line_height=1.5)
    )
    motion: MotionRules = field(default_factory=MotionRules)
    anti_patterns: List[str] = field(default_factory=lambda: [
        "Never use unbranded neon greens or harsh saturation mismatches.",
        "Never use pure black #000000 as background without deep-blue or slate tinting (#0a0e17).",
        "Never hardcode exit fades (gsap.to opacity: 0) on intermediate scenes (the scene transition acts as the exit).",
        "Never use infinite loops (repeat: -1); always calculate finite repeats: Math.ceil(duration / cycleDuration) - 1.",
        "Never use unbranded generic drop shadows; prefer crisp borders or ambient glow."
    ])


class DesignTheme:
    """Pre-configured design theme presets."""

    @staticmethod
    def tech_dark() -> BrandGuidelines:
        return BrandGuidelines(
            brand_name="TechChronicles",
            tagline="Deep Tech Engineering & Architecture",
            tone="Authoritative, Cinematic, Modern",
            colors=[
                ColorRole(name="Background", hex_code="#0a0e17", role="Deep navy-slate canvas"),
                ColorRole(name="Primary Accent", hex_code="#00d2ff", role="Electric cyan for hero elements"),
                ColorRole(name="Secondary Text", hex_code="#8fa3bf", role="Muted blue-grey for captions"),
                ColorRole(name="Base Text", hex_code="#ffffff", role="Pure white headline and body text"),
                ColorRole(name="Warning/Alert", hex_code="#ff5252", role="Vibrant coral for callouts"),
            ],
            display_typography=TypographyStyle(family="'Inter Tight'", weight=700),
            body_typography=TypographyStyle(family="'Inter'", weight=400),
            motion=MotionRules(mood="Cinematic & Fluid", standard_easing="power2.out"),
        )

    @staticmethod
    def cyberpunk_neon() -> BrandGuidelines:
        return BrandGuidelines(
            brand_name="NeonPulse",
            tagline="Frontier Technology & Cybernetics",
            tone="High-Energy, Futuristic, Bold",
            colors=[
                ColorRole(name="Background", hex_code="#070913", role="Abyssal obsidian base"),
                ColorRole(name="Primary Accent", hex_code="#ff007f", role="Neon magenta focal pulse"),
                ColorRole(name="Secondary Text", hex_code="#00f0ff", role="Fluorescent cyan secondary lines"),
                ColorRole(name="Base Text", hex_code="#f8f9fa", role="Crisp off-white typography"),
                ColorRole(name="Warning/Alert", hex_code="#ffe600", role="Electric yellow warning badge"),
            ],
            display_typography=TypographyStyle(family="'Space Grotesk'", weight=700),
            body_typography=TypographyStyle(family="'JetBrains Mono'", weight=400),
            motion=MotionRules(mood="Explosive & Kinetic", standard_easing="expo.out"),
        )

    @staticmethod
    def editorial_gold() -> BrandGuidelines:
        return BrandGuidelines(
            brand_name="Chronicle & Insight",
            tagline="Historical Analysis & Discovery",
            tone="Prestigious, Scholarly, Refined",
            colors=[
                ColorRole(name="Background", hex_code="#0d1117", role="Dark editorial parchment slate"),
                ColorRole(name="Primary Accent", hex_code="#f0a500", role="Warm gold accents and highlights"),
                ColorRole(name="Secondary Text", hex_code="#a0a8b4", role="Subdued slate commentary"),
                ColorRole(name="Base Text", hex_code="#ffffff", role="Stark white headings"),
                ColorRole(name="Warning/Alert", hex_code="#e63946", role="Imperial crimson emphasis"),
            ],
            display_typography=TypographyStyle(family="'Cinzel'", weight=700),
            body_typography=TypographyStyle(family="'Inter'", weight=400),
            motion=MotionRules(mood="Graceful & Paced", standard_easing="power1.out"),
        )

    @staticmethod
    def get_preset(name: str) -> BrandGuidelines:
        name_lower = name.lower().replace("-", "_").strip()
        if "cyber" in name_lower or "neon" in name_lower:
            return DesignTheme.cyberpunk_neon()
        if "gold" in name_lower or "editorial" in name_lower or "history" in name_lower:
            return DesignTheme.editorial_gold()
        return DesignTheme.tech_dark()


def generate_brief(
    topic: str,
    target_duration: float = 30.0,
    aspect_ratio: str = "16:9",
    audience: str = "General Tech Enthusiasts, Developers & Innovators",
    narrative_arc: Optional[str] = None,
    objectives: Optional[List[str]] = None,
) -> str:
    """
    Generate BRIEF.md content following HyperFrames specifications.
    """
    if not narrative_arc:
        narrative_arc = (
            f"Explore the breakthrough discovery, technical architecture, and "
            f"monumental modern impact of {topic}, taking the audience on a concise "
            f"chronological and technical journey."
        )

    if not objectives:
        objectives = [
            f"Hook the viewer with the core significance of {topic}.",
            "Deconstruct the fundamental working mechanism with clear visual cues.",
            "Demonstrate real-world modern scale and future implications.",
        ]

    obj_md = "\n".join([f"- {obj}" for obj in objectives])

    return f"""# BRIEF: {topic}

**Format**: {aspect_ratio}
**Target Duration**: {target_duration:.1f}s
**Audience**: {audience}

## Narrative Arc
{narrative_arc}

## Key Objectives
{obj_md}

## Composition Directives
- Resolution: {'1920x1080 (Landscape)' if aspect_ratio == '16:9' else '1080x1920 (Vertical Portrait)'}
- Framerate: 30 fps
- Pacing: Dynamic short-form visual storytelling with continuous motion and synchronized voiceover.
"""


def generate_design(
    topic: str,
    guidelines: Optional[BrandGuidelines] = None,
    theme_name: str = "tech_dark",
) -> str:
    """
    Generate DESIGN.md content strictly satisfying the Hard Gate.
    Must include:
    - ## Brand
    - ## Colors (3-5 explicit hex codes with functional roles)
    - ## Typography (Display and Body)
    - ## Motion (Mood and standard easings)
    - ## What NOT to Do (Anti-patterns)
    """
    if guidelines is None:
        guidelines = DesignTheme.get_preset(theme_name)

    colors_md = "\n".join([
        f"- **{c.name}**: `{c.hex_code}` — {c.role}"
        for c in guidelines.colors
    ])

    anti_md = "\n".join([
        f"- {anti}"
        for anti in guidelines.anti_patterns
    ])

    return f"""# DESIGN: {topic}

## Brand
- **Name**: {guidelines.brand_name}
- **Tagline**: {guidelines.tagline}
- **Tone**: {guidelines.tone}

## Colors
{colors_md}

## Typography
- **Display**: {guidelines.display_typography.family}, {guidelines.display_typography.fallback} ({guidelines.display_typography.weight}) — Letter spacing: {guidelines.display_typography.letter_spacing}, Line height: {guidelines.display_typography.line_height}
- **Body**: {guidelines.body_typography.family}, {guidelines.body_typography.fallback} ({guidelines.body_typography.weight}) — Letter spacing: {guidelines.body_typography.letter_spacing}, Line height: {guidelines.body_typography.line_height}

## Motion
- **Mood**: {guidelines.motion.mood}
- **Default Tween Duration**: {guidelines.motion.default_duration_sec}s
- **Standard Easing**: `{guidelines.motion.standard_easing}`
- **Emphasis Easing**: `{guidelines.motion.emphasis_easing}`
- **Transition Easing**: `{guidelines.motion.transition_easing}`

## What NOT to Do
{anti_md}
"""


def generate_script(
    topic: str,
    scenes: List[Scene],
    total_duration: float,
) -> Tuple[Script, str]:
    """
    Generate structured Script model and SCRIPT.md markdown.
    """
    full_transcript_parts = []
    total_words = 0

    script_md_lines = [
        f"# SCRIPT: {topic}\n",
        f"**Total Duration**: {total_duration:.1f}s | **Scenes**: {len(scenes)}\n",
    ]

    for s in scenes:
        end_time = s.start_time + s.duration
        full_transcript_parts.append(s.narration_text)
        words = len(s.narration_text.split())
        total_words += words

        script_md_lines.append(f"## Scene {s.scene_id} [{s.start_time:.1f}s - {end_time:.1f}s]")
        script_md_lines.append(f"**Title**: {s.title}")
        script_md_lines.append(f"**Voiceover**: \"{s.narration_text}\"")
        script_md_lines.append(f"**Visual Cue**: {s.hero_frame_description or s.visual_asset_path}")

        if s.beats:
            script_md_lines.append("**Beats**:")
            for b in s.beats:
                script_md_lines.append(f"  - [{b.start_time:.1f}s - {b.end_time:.1f}s] \"{b.text}\" ({b.visual_cue})")
        
        script_md_lines.append("")

    full_transcript = " ".join(full_transcript_parts)

    storyboard = Storyboard(
        project_id=f"proj_{topic.lower().replace(' ', '_')}",
        target_duration=total_duration,
        scenes=scenes,
    )

    script_model = Script(
        topic=topic,
        title=f"{topic}: The Definitive Breakdown",
        total_duration=total_duration,
        storyboard=storyboard,
        full_transcript=full_transcript,
        word_count=total_words,
    )

    return script_model, "\n".join(script_md_lines)


def generate_storyboard(
    topic: str,
    scenes: List[Scene],
    aspect_ratio: str = "16:9",
) -> str:
    """
    Generate STORYBOARD.md content documenting hero frames, GSAP entrance animations, and transitions.
    """
    sb_lines = [
        f"# STORYBOARD: {topic}\n",
        f"**Aspect Ratio**: {aspect_ratio} | **Total Scenes**: {len(scenes)}\n",
    ]

    for s in scenes:
        end_time = s.start_time + s.duration
        sb_lines.append(f"## {s.scene_id.upper()}: {s.title}")
        sb_lines.append(f"- **Time Window**: {s.start_time:.1f}s - {end_time:.1f}s ({s.duration:.1f}s duration)")
        sb_lines.append(f"- **Visual Asset**: `{s.visual_asset_path}`")
        sb_lines.append(f"- **Hero Frame Description**: {s.hero_frame_description or 'Central visual card framed with ambient glow and typography'}")
        sb_lines.append(f"- **Entrance Animation**: `{s.entrance_animation}`")
        sb_lines.append(f"- **Transition Out**: `{s.transition_out}`")
        sb_lines.append(f"- **Narration Beat**: \"{s.narration_text}\"")
        sb_lines.append("")

    return "\n".join(sb_lines)


class ScriptGenerator:
    """
    High-level orchestrator for synthesizing all scriptwriting documents
    from ResearchDossier and AssetProvenanceLedger.
    """

    def __init__(
        self,
        theme_name: str = "tech_dark",
        brand_guidelines: Optional[BrandGuidelines] = None,
    ):
        self.theme_name = theme_name
        self.brand_guidelines = brand_guidelines or DesignTheme.get_preset(theme_name)

    def synthesize_scenes_from_dossier(
        self,
        dossier: ResearchDossier,
        ledger: Optional[AssetProvenanceLedger] = None,
        target_duration: float = 30.0,
    ) -> List[Scene]:
        """
        Derive scenes from talking points and claims, mapping available assets.
        """
        talking_points = dossier.talking_points or []
        claims = dossier.claims or []
        assets = ledger.assets if ledger else []

        # If no talking points, synthesize default beats
        if not talking_points:
            num_scenes = max(3, len(assets)) if assets else 3
            dur_per_scene = target_duration / float(num_scenes)
            scenes = []
            for i in range(num_scenes):
                asset_path = assets[i].local_path if (assets and i < len(assets)) else f"assets/images/asset_{i+1:02d}.svg"
                scenes.append(Scene(
                    scene_id=f"scene_{i+1}",
                    title=f"Breakthrough Chapter {i+1}",
                    start_time=round(i * dur_per_scene, 2),
                    duration=round(dur_per_scene, 2),
                    narration_text=f"Exploring key discovery {i+1} regarding {dossier.topic}, detailing solid-state physics and exponential technology growth.",
                    visual_asset_path=asset_path,
                    hero_frame_description=f"High-impact graphic demonstrating {dossier.topic} fundamentals.",
                    entrance_animation=f"gsap.from('.scene_{i+1} .scene-content', {{ opacity: 0, y: 30, duration: 0.8, ease: 'power2.out' }})",
                    transition_out="Seamless push-slide transition to next scene",
                ))
            return scenes

        num_scenes = max(len(talking_points), len(assets)) if assets else len(talking_points)
        dur_per_scene = target_duration / float(num_scenes)

        scenes = []
        current_time = 0.0

        for i in range(num_scenes):
            scene_dur = round(dur_per_scene, 2)

            if i < len(talking_points):
                tp = talking_points[i]
                # Map matching claim texts or narrative hook
                supported_claims = [c for c in claims if c.claim_id in tp.supported_claim_ids]
                claim_text = supported_claims[0].claim_text if supported_claims else tp.narrative_hook
                title = tp.title
                narration = f"{tp.title}. {tp.narrative_hook} {claim_text}" if tp.narrative_hook != claim_text else f"{tp.title}. {tp.narrative_hook}"
                visual_cue = supported_claims[0].visual_cue_suggestion if supported_claims and supported_claims[0].visual_cue_suggestion else f"Visual card highlighting {tp.title}"
            else:
                extra_idx = i - len(talking_points) + 1
                title = f"Future Horizons & Scale {extra_idx}"
                narration = f"Looking forward, {dossier.topic} continues to accelerate innovations across modern research and engineering domains."
                visual_cue = f"Visual roadmap and scaling analysis for {dossier.topic}"

            # Map asset
            asset_path = ""
            if assets:
                # Find asset targeting this scene or claim
                matching_asset = next(
                    (a for a in assets if a.scene_target == f"scene_{i+1}" or (i < len(talking_points) and any(cid in talking_points[i].supported_claim_ids for cid in a.claim_id_refs))),
                    None
                )
                if matching_asset:
                    asset_path = matching_asset.local_path
                elif i < len(assets):
                    asset_path = assets[i].local_path
                else:
                    asset_path = assets[-1].local_path
            else:
                asset_path = f"assets/images/asset_{i+1:02d}.svg"

            # Entrance animation
            entrance_anim = f"gsap.from('.scene_{i+1} .scene-content', {{ opacity: 0, y: 30, duration: 0.8, ease: 'power2.out' }})"

            # Transition out
            trans_out = "Final fade out" if i == num_scenes - 1 else "Seamless push-slide transition to next scene"

            # Generate beats
            beat1 = Beat(
                beat_id=f"beat_{i+1}_1",
                start_time=round(current_time, 2),
                end_time=round(current_time + scene_dur * 0.5, 2),
                duration=round(scene_dur * 0.5, 2),
                text=title,
                visual_cue=f"Header entrance for {title}",
            )
            beat2 = Beat(
                beat_id=f"beat_{i+1}_2",
                start_time=round(current_time + scene_dur * 0.5, 2),
                end_time=round(current_time + scene_dur, 2),
                duration=round(scene_dur * 0.5, 2),
                text=narration,
                visual_cue=visual_cue,
            )

            scenes.append(Scene(
                scene_id=f"scene_{i+1}",
                title=title,
                start_time=round(current_time, 2),
                duration=scene_dur,
                narration_text=narration,
                visual_asset_path=asset_path,
                hero_frame_description=f"Hero frame showcasing {tp.title} with backing asset {asset_path} and kinetic typography.",
                entrance_animation=entrance_anim,
                transition_out=trans_out,
                beats=[beat1, beat2],
            ))

            current_time += scene_dur

        return scenes

    def generate_all_documents(
        self,
        topic: str,
        dossier: ResearchDossier,
        ledger: Optional[AssetProvenanceLedger] = None,
        target_duration: float = 30.0,
        aspect_ratio: str = "16:9",
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize BRIEF.md, DESIGN.md, SCRIPT.md, STORYBOARD.md, script.json, and script.yaml.
        """
        scenes = self.synthesize_scenes_from_dossier(
            dossier=dossier,
            ledger=ledger,
            target_duration=target_duration,
        )

        brief_md = generate_brief(
            topic=topic,
            target_duration=target_duration,
            aspect_ratio=aspect_ratio,
        )

        design_md = generate_design(
            topic=topic,
            guidelines=self.brand_guidelines,
            theme_name=self.theme_name,
        )

        script_model, script_md = generate_script(
            topic=topic,
            scenes=scenes,
            total_duration=target_duration,
        )

        storyboard_md = generate_storyboard(
            topic=topic,
            scenes=scenes,
            aspect_ratio=aspect_ratio,
        )

        result: Dict[str, Any] = {
            "topic": topic,
            "brief_md": brief_md,
            "design_md": design_md,
            "script_md": script_md,
            "storyboard_md": storyboard_md,
            "script_model": script_model,
            "scenes": scenes,
        }

        if output_dir:
            out_p = ensure_dir(output_dir)
            atomic_write(out_p / "BRIEF.md", brief_md)
            atomic_write(out_p / "DESIGN.md", design_md)
            atomic_write(out_p / "SCRIPT.md", script_md)
            atomic_write(out_p / "STORYBOARD.md", storyboard_md)
            script_model.save(out_p, base_name="script")
            result["output_dir"] = str(out_p)

        return result
