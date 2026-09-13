"""src.hyperframes.components.reference_collage_hook — Reference Collage Hook Component Block (Block 1).

High-density visual opening hook featuring an asymmetric multi-image collage / masonry grid,
glowing accent borders, kinetic badge tag, headline, and staggered GSAP entrance.
"""

from typing import Any, Dict, List
from src.hyperframes.components.base import BaseComponent, ComponentSchema, ValidationResult


class ReferenceCollageHook(BaseComponent):
    """Component Block 1: Reference Collage Hook."""

    schema = ComponentSchema(
        block_id="reference_collage_hook",
        display_name="Reference Collage Hook",
        description="High-density visual hook with staggered multi-image collage and glowing borders",
        category="hooks",
        supported_aspect_ratios=["16:9", "9:16"],
        required_props=["headline"],
        default_props={
            "headline": "The Accidental Breakthrough",
            "badge": "BREAKTHROUGH • HARNESS 9",
            "subtext": "",
            "image_paths": [
                "assets/images/asset_01.svg",
                "assets/images/asset_02.svg",
                "assets/images/asset_03.svg",
            ],
            "glow_color": "#00d2ff",
            "accent_color": "#00d2ff",
            "stagger_delay": 0.15,
        },
        property_types={
            "headline": "str",
            "badge": "str",
            "subtext": "str",
            "image_paths": "list[str]",
            "glow_color": "str",
            "accent_color": "str",
            "stagger_delay": "float",
        },
    )

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Validate collage images and parameters."""
        images = props.get("image_paths") or props.get("images", [])
        if not isinstance(images, list):
            result.add_error("Property 'image_paths' must be a list of image file paths")
        else:
            for img in images:
                if isinstance(img, str) and (img.startswith("http://") or img.startswith("https://")):
                    result.add_error(f"Forbidden remote URL in collage image: '{img}'")

        stagger = props.get("stagger_delay", 0.15)
        if not isinstance(stagger, (int, float)) or stagger < 0:
            result.add_error("Property 'stagger_delay' must be a non-negative number")

    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        headline = self.escape(props.get("headline", "The Accidental Breakthrough"))
        badge = self.escape(props.get("badge", "BREAKTHROUGH • HARNESS 9"))
        subtext = self.escape(props.get("subtext", ""))
        images = props.get("image_paths") or props.get("images", [])
        if not images:
            images = [f"assets/images/{scene_id}_img1.svg", f"assets/images/{scene_id}_img2.svg"]

        items_html = []
        for idx, img_path in enumerate(images):
            safe_path = self.escape(img_path)
            item_tag = f"""        <div class="collage-item collage-item-{idx+1}">
          <div class="collage-card">
            <img class="collage-img" src="{safe_path}" alt="Reference {idx+1}" />
            <div class="collage-card-glow"></div>
          </div>
        </div>"""
            items_html.append(item_tag)

        items_body = "\n".join(items_html)
        subtext_body = f"""<p class="collage-subtext">{subtext}</p>""" if subtext else ""

        return f"""    <!-- Block: reference_collage_hook [{scene_id}] -->
    <div class="hf-block reference-collage-hook" id="{scene_id}-collage" data-block-id="reference_collage_hook">
      <div class="collage-header">
        <div class="collage-badge">{badge}</div>
        <h1 class="collage-headline">{headline}</h1>
        {subtext_body}
      </div>
      <div class="collage-grid collage-count-{min(4, len(images))}">
{items_body}
      </div>
    </div>"""

    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        is_portrait = format_aspect == "9:16"
        glow_color = self.sanitize_color(props.get("glow_color") or props.get("accent_color"), "#00d2ff")
        headline_size = "48px" if is_portrait else "58px"
        padding_bottom = "620px" if is_portrait else "100px"
        grid_direction = "column" if is_portrait else "row"
        grid_gap = "16px" if is_portrait else "24px"

        return f"""/* HyperFrames Block: reference_collage_hook [{scene_id}] */
#{scene_id}-collage {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: {'40px 32px' if is_portrait else '64px'};
  padding-bottom: {padding_bottom};
  box-sizing: border-box;
  z-index: 5;
}}

#{scene_id}-collage .collage-header {{
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
  max-width: {'100%' if is_portrait else '1000px'};
}}

#{scene_id}-collage .collage-badge {{
  align-self: flex-start;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: {glow_color};
  background: rgba(0, 210, 255, 0.12);
  border: 1px solid {glow_color};
  padding: 6px 16px;
  border-radius: 999px;
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.25);
}}

#{scene_id}-collage .collage-headline {{
  font-size: {headline_size};
  font-weight: 800;
  line-height: 1.15;
  color: #ffffff;
  letter-spacing: -0.5px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
}}

#{scene_id}-collage .collage-subtext {{
  font-size: 20px;
  color: #a0aec0;
  line-height: 1.4;
}}

#{scene_id}-collage .collage-grid {{
  display: flex;
  flex-direction: {grid_direction};
  gap: {grid_gap};
  width: 100%;
  max-height: {'380px' if is_portrait else '460px'};
}}

#{scene_id}-collage .collage-item {{
  flex: 1;
  min-width: 0;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  background: rgba(15, 23, 42, 0.85);
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
}}

#{scene_id}-collage .collage-card {{
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}}

#{scene_id}-collage .collage-img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}

#{scene_id}-collage .collage-card-glow {{
  position: absolute;
  inset: 0;
  border-radius: 16px;
  pointer-events: none;
  box-shadow: inset 0 0 20px rgba(0, 210, 255, 0.2);
}}
"""

    def _render_gsap(
        self,
        scene_id: str,
        props: Dict[str, Any],
        start_time: float,
        duration: float,
        format_aspect: str,
    ) -> str:
        stagger = float(props.get("stagger_delay", 0.15))
        return f"""  // GSAP: reference_collage_hook [{scene_id}] (t={start_time}s, dur={duration}s)
  tl.set("#{scene_id}-collage", {{ autoAlpha: 1 }}, {start_time});
  tl.from("#{scene_id}-collage .collage-badge", {{
    scale: 0.8,
    opacity: 0,
    duration: 0.5,
    ease: "back.out(1.7)"
  }}, {start_time});
  tl.from("#{scene_id}-collage .collage-headline", {{
    y: 40,
    opacity: 0,
    duration: 0.7,
    ease: "power3.out"
  }}, {start_time + 0.1});
  tl.from("#{scene_id}-collage .collage-item", {{
    scale: 0.82,
    y: 30,
    opacity: 0,
    stagger: {stagger},
    duration: 0.75,
    ease: "power3.out"
  }}, {start_time + 0.25});
  tl.fromTo("#{scene_id}-collage .collage-card-glow", {{
    opacity: 0.3
  }}, {{
    opacity: 0.8,
    duration: 1.2,
    repeat: Math.ceil({duration} / 1.2) - 1,
    yoyo: true,
    ease: "sine.inOut"
  }}, {start_time + 0.5});"""
