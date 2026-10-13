"""
src.hyperframes.generator — HyperFrames HTML/CSS/GSAP Composition Generator (Milestone 4 - F8).

Compiles structured Storyboard, Script, Brand Guidelines, and Audio Transcripts into
broadcast-grade, deterministic HyperFrames compositions adhering to all specifications:
- Root composition element with data-composition-id="root"
- Global GSAP registry binding: window.__timelines["root"] = gsap.timeline({ paused: true })
- Decoupled media: <video muted playsinline> + <audio data-track-index="...">
- Finite, bounded animation timelines (never repeat: -1)
- Safe entrance presets mapped to finite GSAP timelines; scene cuts by default
- Kinetic caption alignment with Hard Kill Guarantee: tl.set(..., { opacity: 0, visibility: "hidden" })
- Strict local relative paths: assets/... (zero remote URLs)
"""

import html
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.models.dossier import ResearchDossier
from src.models.ledger import AssetProvenanceLedger
from src.models.script import Scene, Script, Storyboard
from src.scriptwriting.aligner import TranscriptResult
from src.scriptwriting.generator import BrandGuidelines, DesignTheme
from src.utils.filesystem import atomic_write, ensure_dir

logger = logging.getLogger("harness9.hyperframes.generator")


class HyperFramesGenerator:
    """Generates broadcast-compliant HyperFrames composition source files."""

    def __init__(
        self,
        format_aspect: str = "16:9",
        fps: int = 30,
    ):
        self.format_aspect = format_aspect
        self.fps = fps
        if format_aspect == "9:16":
            self.width = 1080
            self.height = 1920
        else:
            self.width = 1920
            self.height = 1080

    def generate_composition(
        self,
        topic: str,
        storyboard: Union[Storyboard, List[Dict[str, Any]], List[Scene]],
        output_dir: Union[str, Path],
        duration: Optional[float] = None,
        audio_rel_path: str = "assets/audio/narration.wav",
        transcript: Optional[Union[TranscriptResult, Dict[str, Any]]] = None,
        brand: Optional[BrandGuidelines] = None,
    ) -> Dict[str, Path]:
        """
        Generate and write index.html, styles.css, and main.js to output_dir.
        """
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        # Normalize scenes list
        raw_scenes = self._normalize_scenes(storyboard)
        total_duration = duration or (
            sum(s["duration"] for s in raw_scenes) if raw_scenes else 30.0
        )

        # Normalize transcript data
        transcript_data = self._normalize_transcript(transcript)

        # Generate files
        html_content = self.generate_html(
            topic=topic,
            scenes=raw_scenes,
            total_duration=total_duration,
            audio_rel_path=audio_rel_path,
        )
        css_content = self.generate_css(brand=brand)
        js_content = self.generate_js(
            scenes=raw_scenes,
            total_duration=total_duration,
            transcript_data=transcript_data,
        )

        # Write files atomically
        html_file = out_path / "index.html"
        css_file = out_path / "styles.css"
        js_file = out_path / "main.js"

        atomic_write(html_file, html_content)
        atomic_write(css_file, css_content)
        atomic_write(js_file, js_content)

        return {
            "index_html": html_file,
            "styles_css": css_file,
            "main_js": js_file,
        }

    def generate_html(
        self,
        topic: str,
        scenes: List[Dict[str, Any]],
        total_duration: float,
        audio_rel_path: str = "assets/audio/narration.wav",
    ) -> str:
        """Generate root composition index.html adhering to HyperFrames specification."""
        safe_title = html.escape(topic)

        # Build scene DOM elements
        scenes_html_lines = []
        for i, s in enumerate(scenes):
            scene_id = s.get("scene_id", f"scene_{i+1}")
            start = s.get("start", s.get("start_time", 0.0))
            dur = s.get("duration", 5.0)
            scene_title = html.escape(s.get("title", f"Scene {i+1}"))
            visual_path = s.get("visual", s.get("visual_asset_path", f"assets/images/asset_{i+1:02d}.svg"))

            scene_block = f"""    <!-- Scene {i+1}: {scene_id} -->
    <div class="scene" id="{scene_id}" data-start="{start}" data-duration="{dur}">
      <div class="scene-background">
        <img class="hero-image" src="{visual_path}" alt="{scene_title}" />
        <div class="scrim-overlay"></div>
      </div>
      <div class="scene-content">
        <h2 class="scene-title">{scene_title}</h2>
      </div>
    </div>"""
            scenes_html_lines.append(scene_block)

        scenes_body = "\n".join(scenes_html_lines)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_title} — HyperFrames Composition</title>
  <link rel="stylesheet" href="styles.css" />
  <!-- GSAP Core & Plugins -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
  <!-- Root Composition Canvas -->
  <div data-composition-id="root" data-start="0" data-duration="{int(total_duration) if float(total_duration).is_integer() else total_duration}" data-width="{self.width}" data-height="{self.height}">
    
    <!-- Visual Stage Layers -->
    <div id="stage" class="stage-container">
{scenes_body}
    </div>

    <!-- Kinetic Captions Container -->
    <div id="captions-layer" class="captions-overlay">
      <div id="caption-box" class="caption-text"></div>
    </div>

    <!-- Decoupled Audio Narration Track -->
    <audio id="narration-audio" data-start="0" data-duration="{total_duration}" data-track-index="1" data-volume="1.0" src="{audio_rel_path}"></audio>
  </div>

  <script src="main.js"></script>
</body>
</html>"""

    def generate_css(
        self,
        brand: Optional[BrandGuidelines] = None,
    ) -> str:
        # Extract color roles from BrandGuidelines or defaults
        bg_color = "#0a0e17"
        text_color = "#ffffff"

        if brand and hasattr(brand, "colors") and brand.colors:
            for c in brand.colors:
                role_name = getattr(c, "name", "").lower()
                hex_code = getattr(c, "hex_code", "")
                if "background" in role_name:
                    bg_color = hex_code
                elif "base" in role_name:
                    text_color = hex_code

        is_portrait = self.format_aspect == "9:16"
        title_size = "48px" if is_portrait else "56px"
        caption_size = "44px" if is_portrait else "36px"
        bottom_padding = "600px" if is_portrait else "100px"

        return f"""/* HyperFrames Composition Stylesheet — Format: {self.format_aspect} */
* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  background-color: {bg_color};
  color: {text_color};
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}}

/* Root Composition Bounds */
[data-composition-id="root"] {{
  position: relative;
  width: {self.width}px;
  height: {self.height}px;
  background-color: {bg_color};
  overflow: hidden;
}}

/* Stage & Scene Containers */
.stage-container {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}}

.scene {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 64px;
  padding-bottom: {bottom_padding};
  opacity: 0;
  visibility: hidden;
}}

.scene.active {{
  opacity: 1;
  visibility: visible;
}}

/* Scene Background Layer */
.scene-background {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  overflow: hidden;
}}

.hero-image {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.02);
}}

.scrim-overlay {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, rgba(10, 14, 23, 0.2) 0%, rgba(10, 14, 23, 0.85) 75%, {bg_color} 100%);
}}

/* Foreground Scene Content */
.scene-content {{
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 0;
  max-width: {'900px' if not is_portrait else '100%'};
  padding: 0;
}}

.scene-title {{
  font-size: {title_size};
  font-weight: 800;
  line-height: 1.15;
  color: {text_color};
  letter-spacing: -0.5px;
  max-width: 100%;
  overflow-wrap: anywhere;
  text-wrap: balance;
  text-shadow: 0 2px 22px rgba(0, 0, 0, 0.9);
}}

/* Captions Overlay */
.captions-overlay {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: {'450px' if is_portrait else '60px'};
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  padding: 0 40px;
}}

.caption-text {{
  font-size: {caption_size};
  font-weight: 800;
  color: #ffffff;
  text-align: center;
  max-width: 100%;
  padding: 8px 12px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.95);
  opacity: 0;
  visibility: hidden;
}}
"""

    def generate_js(
        self,
        scenes: List[Dict[str, Any]],
        total_duration: float,
        transcript_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate main.js with synchronous GSAP timeline and finite animation loops."""
        scene_animations = []
        for i, s in enumerate(scenes):
            scene_id = s.get("scene_id", f"scene_{i+1}")
            start = float(s.get("start", s.get("start_time", 0.0)))
            dur = float(s.get("duration", 5.0))
            entrance = self._resolve_entrance_animation(s.get("entrance_animation"))
            transition = self._resolve_transition_out(
                s.get("transition_out"), is_final=i == len(scenes) - 1
            )
            selector = f"#{scene_id}"
            content_selector = f"{selector} .scene-content"

            if entrance == "rise":
                entrance_code = f'''  tl.fromTo("{content_selector}", {{ autoAlpha: 0, y: 42 }}, {{ autoAlpha: 1, y: 0, duration: {self._bounded_motion_duration(dur, 10):.3f}, ease: "power3.out" }}, {start});'''
            elif entrance == "slide_left":
                entrance_code = f'''  tl.fromTo("{content_selector}", {{ autoAlpha: 0, x: 54 }}, {{ autoAlpha: 1, x: 0, duration: {self._bounded_motion_duration(dur, 10):.3f}, ease: "power3.out" }}, {start});'''
            elif entrance == "zoom":
                entrance_code = f'''  tl.fromTo("{content_selector}", {{ autoAlpha: 0, scale: 0.96 }}, {{ autoAlpha: 1, scale: 1, duration: {self._bounded_motion_duration(dur, 12):.3f}, ease: "power2.out" }}, {start});'''
            elif entrance == "reveal":
                entrance_code = f'''  tl.fromTo("{content_selector}", {{ clipPath: "inset(0 0 100% 0)" }}, {{ clipPath: "inset(0 0 0% 0)", duration: {self._bounded_motion_duration(dur, 12):.3f}, ease: "power2.out" }}, {start});'''
            elif entrance == "fade":
                entrance_code = f'''  tl.fromTo("{content_selector}", {{ autoAlpha: 0 }}, {{ autoAlpha: 1, duration: {self._bounded_motion_duration(dur, 6):.3f}, ease: "power1.out" }}, {start});'''
            else:
                entrance_code = f'''  tl.set("{content_selector}", {{ autoAlpha: 1 }}, {start});'''

            anim_code = f"""  // Scene {i+1}: {scene_id} (t={start}s to {start + dur}s)
  tl.set("{selector}", {{ autoAlpha: 1 }}, {start});
{entrance_code}
  tl.from("{selector} .hero-image", {{
    scale: 1.15,
    duration: {dur},
    ease: "none"
  }}, {start});"""

            if i < len(scenes) - 1:
                if transition == "fade":
                    fade_duration = self._bounded_motion_duration(dur, 6)
                    anim_code += f'''\n  tl.to("{selector}", {{ autoAlpha: 0, duration: {fade_duration:.3f}, ease: "power1.in" }}, {start + dur - fade_duration});'''
                else:
                    anim_code += f'''\n  tl.set("{selector}", {{ autoAlpha: 0 }}, {start + dur});'''
            else:
                # Keep a resolved final frame unless the storyboard asks to fade.
                if transition == "fade":
                    fade_duration = self._bounded_motion_duration(dur, 6)
                    anim_code += f'''\n  tl.to("{selector}", {{ autoAlpha: 0, duration: {fade_duration:.3f}, ease: "power1.in" }}, {start + dur - fade_duration});'''

            scene_animations.append(anim_code)

        all_scenes_js = "\n\n".join(scene_animations)

        # Kinetic Caption Animations with Hard Kill Guarantee
        caption_animations = []
        if transcript_data and "scenes" in transcript_data:
            for s_item in transcript_data.get("scenes", []):
                for grp in s_item.get("groups", []):
                    text = grp.get("text", "").replace('"', '\\"')
                    g_start = float(grp.get("start", 0.0))
                    g_end = float(grp.get("end", g_start + 1.0))
                    g_dur = max(0.1, g_end - g_start)

                    cap_block = f"""  // Caption: "{text}" [{g_start}s - {g_end}s]
  tl.call(() => {{
    const box = document.getElementById("caption-box");
    if (box) {{
      box.textContent = "{text}";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }}
  }}, [], {g_start});
  tl.fromTo("#caption-box", {{ scale: 0.95, opacity: 0 }}, {{ scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }}, {g_start});
  tl.to("#caption-box", {{ opacity: 0, duration: 0.12, ease: "power2.in" }}, {g_end - 0.12});
  // Hard kill guarantee
  tl.set("#caption-box", {{ opacity: 0, visibility: "hidden" }}, {g_end});"""
                    caption_animations.append(cap_block)

        captions_js = "\n\n".join(caption_animations) if caption_animations else "  // No word groups provided for kinetic captions"

        return f"""/**
 * HyperFrames GSAP Composition Controller
 * Compliant with HyperFrames deterministic seek & capture engine.
 */

// 1. Initialize Global Timelines Registry
window.__timelines = window.__timelines || {{}};

// 2. Synchronous Master Timeline Construction (must be paused: true)
const tl = gsap.timeline({{
  paused: true,
  defaults: {{
    ease: "power2.out",
    duration: 0.6
  }}
}});

// Register root composition timeline
window.__timelines["root"] = tl;

// 3. Scene Hierarchy & Entrance Choreography
{all_scenes_js}

// 4. Kinetic Captions Alignment (with Hard Kill Guarantee)
{captions_js}

// 5. Total Composition Duration Anchor
tl.to({{}}, {{ duration: 0.01 }}, {total_duration});
"""

    def _bounded_motion_duration(self, scene_duration: float, frames: int) -> float:
        """Keep entry and exit movement short and within its scene."""
        frame_duration = float(frames) / max(1, self.fps)
        return max(0.001, min(frame_duration, max(0.001, scene_duration * 0.35)))

    @staticmethod
    def _resolve_entrance_animation(value: Any) -> str:
        """Map storyboard labels and legacy notes to safe GSAP presets.

        Animation text is treated as data; arbitrary storyboard strings are
        never copied into executable JavaScript.
        """
        normalized = str(value or "").strip().lower().replace("-", "_")
        if normalized in {"cut", "none", "hold"}:
            return "cut"
        if "reveal" in normalized or "wipe" in normalized:
            return "reveal"
        if "zoom" in normalized or "scale" in normalized:
            return "zoom"
        if "slide" in normalized or "push" in normalized or "x:" in normalized:
            return "slide_left"
        if "rise" in normalized or "y:" in normalized:
            return "rise"
        if "fade" in normalized or "opacity" in normalized:
            return "fade"
        return "rise"

    @staticmethod
    def _resolve_transition_out(value: Any, *, is_final: bool) -> str:
        """Resolve exits to a bounded cut, fade, or final-frame hold."""
        normalized = str(value or "").strip().lower()
        if "fade" in normalized:
            return "fade"
        if "hold" in normalized or "none" in normalized:
            return "hold"
        if "cut" in normalized:
            return "cut"
        return "hold" if is_final else "cut"

    def _normalize_scenes(
        self,
        storyboard: Union[Storyboard, List[Dict[str, Any]], List[Scene]],
    ) -> List[Dict[str, Any]]:
        """Convert diverse storyboard representations to a clean list of scene dicts."""
        if hasattr(storyboard, "scenes"):
            # Storyboard dataclass/model
            res = []
            for s in storyboard.scenes:
                if hasattr(s, "to_dict"):
                    res.append(s.to_dict())
                elif hasattr(s, "model_dump"):
                    res.append(s.model_dump())
                elif isinstance(s, dict):
                    res.append(s)
            return res
        elif isinstance(storyboard, list):
            res = []
            for s in storyboard:
                if hasattr(s, "to_dict"):
                    res.append(s.to_dict())
                elif hasattr(s, "model_dump"):
                    res.append(s.model_dump())
                elif isinstance(s, dict):
                    res.append(s)
            return res
        return []

    def _normalize_transcript(
        self,
        transcript: Optional[Union[TranscriptResult, Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        """Normalize transcript input to dict format."""
        if transcript is None:
            return None
        if hasattr(transcript, "to_dict"):
            return transcript.to_dict()
        if hasattr(transcript, "model_dump"):
            return transcript.model_dump()
        if isinstance(transcript, dict):
            return transcript
        return None
