"""src.hyperframes.components.split_screen_intro — Split-Screen Intro Component Block (Block 2).

Contrasts two eras, rival technologies, or concepts with opposing wipes and central divider.
"""

from typing import Any, Dict
from src.hyperframes.components.base import BaseComponent, ComponentSchema, ValidationResult


class SplitScreenIntro(BaseComponent):
    """Component Block 2: Split-Screen Intro."""

    schema = ComponentSchema(
        block_id="split_screen_intro",
        display_name="Split-Screen Intro",
        description="Dual-concept contrast panel with opposing wipes, image backgrounds, and central divider",
        category="intros",
        supported_aspect_ratios=["16:9", "9:16"],
        required_props=["left_title", "right_title"],
        default_props={
            "badge": "THE PARADIGM SHIFT",
            "left_title": "Vacuum Tubes (1904)",
            "left_subtitle": "Bulky, fragile, and power-hungry",
            "left_image": "assets/images/asset_01.svg",
            "left_tag": "LEGACY ERA",
            "right_title": "Solid State (1947)",
            "right_subtitle": "Microscopic, durable, and instant",
            "right_image": "assets/images/asset_02.svg",
            "right_tag": "NEW ERA",
            "divider_color": "#00d2ff",
        },
        property_types={
            "badge": "str",
            "left_title": "str",
            "left_subtitle": "str",
            "left_image": "str",
            "left_tag": "str",
            "right_title": "str",
            "right_subtitle": "str",
            "right_image": "str",
            "right_tag": "str",
            "divider_color": "str",
        },
    )

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Validate left and right assets and text parameters."""
        for side in ["left", "right"]:
            img = props.get(f"{side}_image", "")
            if isinstance(img, str) and (img.startswith("http://") or img.startswith("https://")):
                result.add_error(f"Forbidden remote URL in {side}_image: '{img}'")

    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        badge = self.escape(props.get("badge", "THE PARADIGM SHIFT"))
        l_title = self.escape(props.get("left_title", "Left Concept"))
        l_sub = self.escape(props.get("left_subtitle", ""))
        l_img = self.escape(props.get("left_image", "assets/images/left.svg"))
        l_tag = self.escape(props.get("left_tag", "SIDE A"))

        r_title = self.escape(props.get("right_title", "Right Concept"))
        r_sub = self.escape(props.get("right_subtitle", ""))
        r_img = self.escape(props.get("right_image", "assets/images/right.svg"))
        r_tag = self.escape(props.get("right_tag", "SIDE B"))

        return f"""    <!-- Block: split_screen_intro [{scene_id}] -->
    <div class="hf-block split-screen-intro" id="{scene_id}-splitscreen" data-block-id="split_screen_intro">
      <div class="split-badge-container">
        <div class="split-badge">{badge}</div>
      </div>
      <div class="split-stage">
        <div class="split-half split-left">
          <div class="split-bg-wrap">
            <img class="split-bg" src="{l_img}" alt="{l_title}" />
            <div class="split-scrim"></div>
          </div>
          <div class="split-content">
            <span class="split-tag split-tag-left">{l_tag}</span>
            <h2 class="split-title">{l_title}</h2>
            <p class="split-subtitle">{l_sub}</p>
          </div>
        </div>

        <div class="split-divider">
          <div class="divider-line"></div>
          <div class="divider-node">VS</div>
        </div>

        <div class="split-half split-right">
          <div class="split-bg-wrap">
            <img class="split-bg" src="{r_img}" alt="{r_title}" />
            <div class="split-scrim"></div>
          </div>
          <div class="split-content">
            <span class="split-tag split-tag-right">{r_tag}</span>
            <h2 class="split-title">{r_title}</h2>
            <p class="split-subtitle">{r_sub}</p>
          </div>
        </div>
      </div>
    </div>"""

    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        is_portrait = format_aspect == "9:16"
        div_color = self.sanitize_color(props.get("divider_color"), "#00d2ff")
        split_direction = "column" if is_portrait else "row"
        title_size = "34px" if is_portrait else "44px"
        padding_bottom = "580px" if is_portrait else "60px"

        return f"""/* HyperFrames Block: split_screen_intro [{scene_id}] */
#{scene_id}-splitscreen {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  z-index: 5;
}}

#{scene_id}-splitscreen .split-badge-container {{
  position: absolute;
  top: {'40px' if is_portrait else '48px'};
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  z-index: 10;
}}

#{scene_id}-splitscreen .split-badge {{
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: #ffffff;
  background: rgba(15, 23, 42, 0.9);
  border: 1.5px solid {div_color};
  padding: 8px 24px;
  border-radius: 999px;
  box-shadow: 0 0 25px rgba(0, 210, 255, 0.3);
  backdrop-filter: blur(12px);
}}

#{scene_id}-splitscreen .split-stage {{
  display: flex;
  flex-direction: {split_direction};
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  padding-bottom: {padding_bottom if is_portrait else '0'};
}}

#{scene_id}-splitscreen .split-half {{
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: {'36px' if is_portrait else '56px'};
  overflow: hidden;
}}

#{scene_id}-splitscreen .split-bg-wrap {{
  position: absolute;
  inset: 0;
  z-index: 1;
}}

#{scene_id}-splitscreen .split-bg {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.05);
}}

#{scene_id}-splitscreen .split-scrim {{
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(10, 14, 23, 0.3) 0%, rgba(10, 14, 23, 0.92) 85%);
}}

#{scene_id}-splitscreen .split-content {{
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 12px;
}}

#{scene_id}-splitscreen .split-tag {{
  align-self: flex-start;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 4px 12px;
  border-radius: 6px;
  text-transform: uppercase;
}}

#{scene_id}-splitscreen .split-tag-left {{
  color: #ff9800;
  background: rgba(255, 152, 0, 0.15);
  border: 1px solid rgba(255, 152, 0, 0.4);
}}

#{scene_id}-splitscreen .split-tag-right {{
  color: {div_color};
  background: rgba(0, 210, 255, 0.15);
  border: 1px solid rgba(0, 210, 255, 0.4);
}}

#{scene_id}-splitscreen .split-title {{
  font-size: {title_size};
  font-weight: 800;
  color: #ffffff;
  line-height: 1.2;
}}

#{scene_id}-splitscreen .split-subtitle {{
  font-size: {'18px' if is_portrait else '20px'};
  color: #cbd5e1;
  line-height: 1.4;
}}

#{scene_id}-splitscreen .split-divider {{
  position: absolute;
  {'top: 50%; left: 0; width: 100%; height: 2px;' if is_portrait else 'top: 0; left: 50%; width: 2px; height: 100%;'}
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 8;
  transform: {'translateY(-50%)' if is_portrait else 'translateX(-50%)'};
}}

#{scene_id}-splitscreen .divider-line {{
  position: absolute;
  inset: 0;
  background: {div_color};
  box-shadow: 0 0 15px {div_color};
}}

#{scene_id}-splitscreen .divider-node {{
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #0a0e17;
  border: 2px solid {div_color};
  color: {div_color};
  font-size: 14px;
  font-weight: 900;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 0 20px rgba(0, 210, 255, 0.5);
  z-index: 9;
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
        is_portrait = format_aspect == "9:16"
        x_left = 0 if is_portrait else -80
        y_left = -60 if is_portrait else 0
        x_right = 0 if is_portrait else 80
        y_right = 60 if is_portrait else 0

        return f"""  // GSAP: split_screen_intro [{scene_id}] (t={start_time}s, dur={duration}s)
  tl.set("#{scene_id}-splitscreen", {{ autoAlpha: 1 }}, {start_time});
  tl.from("#{scene_id}-splitscreen .split-badge", {{
    y: -30,
    opacity: 0,
    duration: 0.6,
    ease: "back.out(1.7)"
  }}, {start_time});
  tl.from("#{scene_id}-splitscreen .split-left", {{
    x: {x_left},
    y: {y_left},
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }}, {start_time + 0.1});
  tl.from("#{scene_id}-splitscreen .split-right", {{
    x: {x_right},
    y: {y_right},
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }}, {start_time + 0.15});
  tl.from("#{scene_id}-splitscreen .divider-node", {{
    scale: 0,
    opacity: 0,
    duration: 0.5,
    ease: "back.out(2.0)"
  }}, {start_time + 0.3});"""
