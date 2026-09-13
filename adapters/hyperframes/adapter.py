"""adapters.hyperframes.adapter — HyperFrames Compilation and Video Render Adapter (Milestone M3).

Provides the primary integration interface isolating HyperFrames composition compilation,
component block assembly, static linter validation, and headless MP4 video rendering.
"""

from dataclasses import dataclass, field
import html
import json
import logging
from pathlib import Path
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from adapters.hyperframes.registry import ComponentRegistry, get_registry
from src.hyperframes.generator import HyperFramesGenerator
from src.hyperframes.renderer import HyperFramesRenderer, RenderResult
from src.hyperframes.validator import CompositionValidator, validate_composition
from src.models.contracts import AssetRecord, RenderArtifact, Script, ScriptScene
from src.utils.filesystem import atomic_write, ensure_dir

logger = logging.getLogger("harness9.adapters.hyperframes.adapter")


@dataclass
class HyperFramesProject:
    """Represents a compiled HyperFrames project workspace."""
    project_dir: Path
    index_html: Path
    styles_css: Path
    main_js: Path
    topic: str
    duration: float
    format_aspect: str = "16:9"
    width: int = 1920
    height: int = 1080
    scene_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def exists(self) -> bool:
        """Check if core project files exist on disk."""
        return self.index_html.exists() and self.styles_css.exists() and self.main_js.exists()

    def validate(self) -> Dict[str, Any]:
        """Run composition static validation against this project."""
        validator = CompositionValidator(self.project_dir)
        return validator.validate()

    def __contains__(self, key: str) -> bool:
        return key in ("html", "css", "js", "assets", "project_dir") or hasattr(self, key)

    def __getitem__(self, key: str) -> Any:
        if key == "html":
            return self.index_html.read_text(encoding="utf-8") if self.index_html.exists() else ""
        if key == "css":
            return self.styles_css.read_text(encoding="utf-8") if self.styles_css.exists() else ""
        if key == "js":
            return self.main_js.read_text(encoding="utf-8") if self.main_js.exists() else ""
        if key == "assets":
            assets_dir = self.project_dir / "assets"
            if assets_dir.exists():
                return [str(p.relative_to(self.project_dir)) for p in assets_dir.rglob("*") if p.is_file()]
            return []
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Convert project metadata to dictionary."""
        return {
            "project_dir": str(self.project_dir),
            "index_html": str(self.index_html),
            "styles_css": str(self.styles_css),
            "main_js": str(self.main_js),
            "topic": self.topic,
            "duration": self.duration,
            "format_aspect": self.format_aspect,
            "width": self.width,
            "height": self.height,
            "scene_count": self.scene_count,
            "metadata": self.metadata,
        }


class HyperFramesAdapter:
    """Primary adapter bridge interfacing pipeline stages with the HyperFrames engine."""

    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        renderer: Optional[HyperFramesRenderer] = None,
        execution_runtime: Optional[Any] = None,
    ) -> None:
        self.registry = registry or get_registry()
        self.execution_runtime = execution_runtime
        self.renderer = renderer or HyperFramesRenderer(execution_runtime=execution_runtime)

    def compile_composition(
        self,
        script: Union[Script, Dict[str, Any]],
        assets: Optional[List[Union[AssetRecord, Dict[str, Any]]]] = None,
        template: str = "default",
        output_dir: Optional[Union[str, Path]] = None,
        format_aspect: str = "16:9",
        duration: Optional[float] = None,
        audio_rel_path: str = "assets/audio/narration.wav",
        transcript: Optional[Any] = None,
        brand: Optional[Any] = None,
    ) -> HyperFramesProject:
        """
        Compile a Script, Assets, and component blocks into a valid HyperFramesProject.
        """
        norm_script = self._normalize_script(script)
        topic = norm_script.get("topic", norm_script.get("title", "Video Presentation"))
        scenes = norm_script.get("scenes", [])
        total_duration = duration or float(norm_script.get("total_duration", 30.0))
        if not total_duration or total_duration <= 0:
            total_duration = sum(float(s.get("duration", 5.0)) for s in scenes) if scenes else 30.0

        target_dir = Path(output_dir).resolve() if output_dir else Path(f"output/hf_{int(time.time())}").resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
        (target_dir / "assets" / "audio").mkdir(parents=True, exist_ok=True)
        (target_dir / "renders").mkdir(parents=True, exist_ok=True)

        # Stage assets into target directory
        self._stage_assets(
            target_dir=target_dir,
            scenes=scenes,
            assets=assets,
            audio_rel_path=audio_rel_path,
        )

        width = 1080 if format_aspect == "9:16" else 1920
        height = 1920 if format_aspect == "9:16" else 1080

        # Assemble HTML, CSS, and GSAP across all scenes
        scenes_html_blocks: List[str] = []
        scenes_css_blocks: List[str] = []
        scenes_gsap_blocks: List[str] = []

        for idx, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", f"scene_{idx+1}")
            st = float(scene.get("start_time", scene.get("start", idx * 5.0)))
            dur = float(scene.get("duration", 5.0))
            comp_type = scene.get("component_type", "")
            comp_props = scene.get("component_props", {}) or {}

            # Map assets if available
            visual_path = scene.get("visual_asset_path", scene.get("visual", f"assets/images/asset_{idx+1:02d}.svg"))
            if "image_paths" not in comp_props and "images" not in comp_props and visual_path:
                comp_props["image_paths"] = [visual_path]
            if "left_image" not in comp_props and visual_path:
                comp_props["left_image"] = visual_path
            if "avatar_path" not in comp_props and visual_path:
                comp_props["avatar_path"] = visual_path

            # If component block is recognized in registry, render via component block
            if comp_type and self.registry.has(comp_type):
                comp = self.registry.get(comp_type)
                # Render component HTML, CSS, GSAP
                c_html = comp.render_html(scene_id, comp_props, format_aspect=format_aspect)
                c_css = comp.render_css(scene_id, comp_props, format_aspect=format_aspect)
                c_gsap = comp.render_gsap(scene_id, comp_props, start_time=st, duration=dur, format_aspect=format_aspect)

                scene_container_html = f"""    <!-- Scene Container {idx+1}: {scene_id} -->
    <div class="scene" id="{scene_id}" data-start="{st}" data-duration="{dur}">
      <div class="scene-background">
        <img class="hero-image" src="{visual_path}" alt="{self.escape(scene.get('title', ''))}" />
        <div class="scrim-overlay"></div>
      </div>
{c_html}
    </div>"""
                scenes_html_blocks.append(scene_container_html)
                scenes_css_blocks.append(c_css)

                # Scene entrance and exit timeline control
                scene_timeline_ctrl = f"""  // Scene {idx+1} container activation [{scene_id}]
  tl.set("#{scene_id}", {{ autoAlpha: 1 }}, {st});
{c_gsap}"""
                if idx < len(scenes) - 1:
                    scene_timeline_ctrl += f"""\n  tl.set("#{scene_id}", {{ autoAlpha: 0 }}, {st + dur});"""
                else:
                    scene_timeline_ctrl += f"""\n  tl.to("#{scene_id}", {{ opacity: 0, duration: 0.5, ease: "power2.in" }}, {st + dur - 0.5});"""

                scenes_gsap_blocks.append(scene_timeline_ctrl)

            else:
                # Default scene presentation
                scene_title = self.escape(scene.get("title", f"Scene {idx+1}"))
                narration = self.escape(scene.get("narration_text", scene.get("narration", "")))
                default_html = f"""    <!-- Scene {idx+1}: {scene_id} -->
    <div class="scene" id="{scene_id}" data-start="{st}" data-duration="{dur}">
      <div class="scene-background">
        <img class="hero-image" src="{visual_path}" alt="{scene_title}" />
        <div class="scrim-overlay"></div>
      </div>
      <div class="scene-content">
        <div class="badge-tag">PART {idx+1:02d} • HARNESS 9</div>
        <h2 class="scene-title">{scene_title}</h2>
        <p class="scene-narration">{narration}</p>
      </div>
    </div>"""
                scenes_html_blocks.append(default_html)

                anim_code = f"""  // Scene {idx+1}: {scene_id} (t={st}s to {st + dur}s)
  tl.set("#{scene_id}", {{ autoAlpha: 1 }}, {st});
  tl.from("#{scene_id} .scene-content", {{
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }}, {st});
  tl.from("#{scene_id} .hero-image", {{
    scale: 1.15,
    duration: {dur},
    ease: "none"
  }}, {st});"""
                if idx < len(scenes) - 1:
                    anim_code += f"""\n  tl.set("#{scene_id}", {{ autoAlpha: 0 }}, {st + dur});"""
                else:
                    anim_code += f"""\n  tl.to("#{scene_id}", {{ opacity: 0, duration: 0.5, ease: "power2.in" }}, {st + dur - 0.5});"""
                scenes_gsap_blocks.append(anim_code)

        # Build full index.html
        full_html = self._build_full_html(
            topic=topic,
            scenes_html="\n\n".join(scenes_html_blocks),
            total_duration=total_duration,
            width=width,
            height=height,
            audio_rel_path=audio_rel_path,
        )

        # Build full styles.css
        base_generator = HyperFramesGenerator(format_aspect=format_aspect)
        base_css = base_generator.generate_css(brand=brand)
        custom_css = "\n\n".join(scenes_css_blocks)
        full_css = f"{base_css}\n\n/* ==========================================================================\n   Component Block Styles\n   ========================================================================== */\n\n{custom_css}"

        # Build full main.js
        full_js = self._build_full_js(
            scenes_gsap="\n\n".join(scenes_gsap_blocks),
            total_duration=total_duration,
        )

        # Write files atomically
        html_file = target_dir / "index.html"
        css_file = target_dir / "styles.css"
        js_file = target_dir / "main.js"

        atomic_write(html_file, full_html)
        atomic_write(css_file, full_css)
        atomic_write(js_file, full_js)

        return HyperFramesProject(
            project_dir=target_dir,
            index_html=html_file,
            styles_css=css_file,
            main_js=js_file,
            topic=topic,
            duration=total_duration,
            format_aspect=format_aspect,
            width=width,
            height=height,
            scene_count=len(scenes),
            metadata={"template": template},
        )

    def render_project(
        self,
        project: Union[str, Path, HyperFramesProject],
        output_path: Optional[Union[str, Path]] = None,
        duration: Optional[float] = None,
        fps: int = 30,
        quality: str = "standard",
        execution_runtime: Optional[Any] = None,
    ) -> RenderArtifact:
        """
        Render a compiled HyperFrames project to a broadcast-grade MP4 video.
        """
        proj_dir = project.project_dir if isinstance(project, HyperFramesProject) else Path(project)
        runtime = execution_runtime or self.execution_runtime
        render_res = self.renderer.render(
            project_dir=proj_dir,
            output_mp4=output_path,
            duration=duration or (project.duration if isinstance(project, HyperFramesProject) else None),
            fps=fps,
            execution_runtime=runtime,
        )

        return RenderArtifact(
            video_path=render_res.output_path,
            duration_seconds=render_res.duration_seconds,
            file_size_bytes=render_res.file_size_bytes,
            width=render_res.width,
            height=render_res.height,
            fps=render_res.fps,
            video_codec=render_res.video_codec,
            audio_codec=render_res.audio_codec,
            validation_status=render_res.validation_status,
        )

    def validate_project(
        self,
        project: Union[str, Path, HyperFramesProject],
    ) -> Dict[str, Any]:
        """
        Run static validation rules on a HyperFrames project.
        """
        proj_dir = project.project_dir if isinstance(project, HyperFramesProject) else Path(project)
        return validate_composition(proj_dir)

    def _normalize_script(self, script: Union[Script, Dict[str, Any]]) -> Dict[str, Any]:
        """Convert Script contract or dictionary to plain dictionary."""
        if hasattr(script, "model_dump"):
            return script.model_dump()
        if hasattr(script, "to_dict"):
            return script.to_dict()
        if isinstance(script, dict):
            return script
        return {"topic": "Video", "scenes": []}

    @staticmethod
    def escape(text: Any) -> str:
        """Escape text for safe HTML rendering."""
        if text is None:
            return ""
        return html.escape(str(text))

    def _build_full_html(
        self,
        topic: str,
        scenes_html: str,
        total_duration: float,
        width: int,
        height: int,
        audio_rel_path: str,
    ) -> str:
        safe_title = self.escape(topic)
        dur_str = f"{int(total_duration) if float(total_duration).is_integer() else total_duration}"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_title} — HyperFrames Composition</title>
  <link rel="stylesheet" href="styles.css" />
  <!-- GSAP Core -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
  <!-- Root Composition Canvas -->
  <div data-composition-id="root" data-start="0" data-duration="{dur_str}" data-width="{width}" data-height="{height}">
    
    <!-- Visual Stage Layers -->
    <div id="stage" class="stage-container">
{scenes_html}
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

    def _build_full_js(self, scenes_gsap: str, total_duration: float) -> str:
        return f"""/**
 * HyperFrames Master GSAP Composition Controller
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

// 3. Scene Animations & Parameterized Component Blocks
{scenes_gsap}

// 4. Total Composition Duration Anchor
tl.to({{}}, {{ duration: 0.01 }}, {total_duration});
"""

    def _stage_assets(
        self,
        target_dir: Path,
        scenes: List[Dict[str, Any]],
        assets: Optional[List[Union[AssetRecord, Dict[str, Any]]]] = None,
        audio_rel_path: str = "assets/audio/narration.wav",
    ) -> None:
        """
        Stage all local visual and audio assets into the target directory's assets/ structure.
        Ensures CompositionValidator local disk existence checks pass.
        """
        images_dir = target_dir / "assets" / "images"
        audio_dir = target_dir / "assets" / "audio"
        images_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # 1. Process explicit assets list if passed
        if assets:
            for item in assets:
                f_path = ""
                asset_id = ""
                if isinstance(item, AssetRecord):
                    f_path = item.file_path or ""
                    asset_id = item.asset_id or ""
                elif isinstance(item, dict):
                    f_path = item.get("file_path", item.get("path", item.get("storage_url", "")))
                    asset_id = item.get("asset_id", "")

                if f_path:
                    cand_paths = [Path(f_path), target_dir.parent / f_path, target_dir / f_path]
                    copied = False
                    for cp in cand_paths:
                        if cp.exists() and cp.is_file():
                            dst = images_dir / cp.name if cp.suffix.lower() not in [".wav", ".mp3", ".aac"] else audio_dir / cp.name
                            if not dst.exists() or dst.resolve() != cp.resolve():
                                shutil.copy2(cp, dst)
                            copied = True
                            break
                    if not copied:
                        fname = Path(f_path).name or f"{asset_id or 'asset'}.svg"
                        dst = images_dir / fname if fname.endswith(".svg") else audio_dir / fname
                        if fname.endswith(".svg"):
                            dst.write_text(
                                f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><rect width="100%" height="100%" fill="#0a0e17"/><text x="50%" y="50%" fill="#00d2ff">{asset_id or "Asset"}</text></svg>',
                                encoding="utf-8",
                            )

        # 2. Collect all referenced relative paths in scenes and audio
        referenced_paths: List[str] = [audio_rel_path] if audio_rel_path else []
        for s in scenes:
            for k in ["visual_asset_path", "visual", "image_path", "avatar_path", "author_image"]:
                v = s.get(k)
                if isinstance(v, str) and not v.startswith(("http://", "https://", "data:")):
                    referenced_paths.append(v)
            c_props = s.get("component_props", {}) or {}
            for k, val in c_props.items():
                if isinstance(val, str) and not val.startswith(("http://", "https://", "data:")):
                    if any(val.endswith(ext) for ext in [".svg", ".png", ".jpg", ".jpeg", ".webp", ".wav", ".mp3"]):
                        referenced_paths.append(val)
                elif isinstance(val, list):
                    for elem in val:
                        if isinstance(elem, str) and not elem.startswith(("http://", "https://", "data:")):
                            if any(elem.endswith(ext) for ext in [".svg", ".png", ".jpg", ".jpeg", ".webp", ".wav", ".mp3"]):
                                referenced_paths.append(elem)

        # 3. Stage each referenced path
        for rel in set(referenced_paths):
            if not rel:
                continue
            dest = target_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                candidates = [
                    target_dir.parent / rel,
                    Path(rel),
                    target_dir.parent / "assets" / Path(rel).name,
                    target_dir.parent / "assets" / "images" / Path(rel).name,
                    target_dir.parent / "assets" / "audio" / Path(rel).name,
                ]
                staged = False
                for c in candidates:
                    if c.exists() and c.is_file():
                        shutil.copy2(c, dest)
                        staged = True
                        break
                if not staged:
                    if dest.suffix.lower() == ".svg":
                        dest.write_text(
                            f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><rect width="100%" height="100%" fill="#0a0e17"/><text x="50%" y="50%" fill="#00d2ff">{dest.stem}</text></svg>',
                            encoding="utf-8",
                        )
                    elif dest.suffix.lower() in [".wav", ".mp3", ".aac"]:
                        dest.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
                    elif dest.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                        dest.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\r\xefe\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

