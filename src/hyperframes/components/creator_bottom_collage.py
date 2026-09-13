"""src.hyperframes.components.creator_bottom_collage — Creator Bottom Collage Component Block (Block 7).

Picture-in-picture lower third and bottom collage bar displaying creator avatar, handle,
brand verification badge, and supporting visual thumbnail.
"""

from typing import Any, Dict
from src.hyperframes.components.base import BaseComponent, ComponentSchema, ValidationResult


class CreatorBottomCollage(BaseComponent):
    """Component Block 7: Creator Bottom Collage."""

    schema = ComponentSchema(
        block_id="creator_bottom_collage",
        display_name="Creator Bottom Collage",
        description="Lower third picture-in-picture banner featuring creator identity, brand badge, handle, and supporting thumbnail",
        category="branding",
        supported_aspect_ratios=["16:9", "9:16"],
        required_props=["creator_name", "creator_handle"],
        default_props={
            "creator_name": "Harness 9 Studio",
            "creator_handle": "@Harness9AI",
            "avatar_path": "assets/images/asset_01.svg",
            "brand_badge": "VERIFIED PRODUCER",
            "headline": "Autonomous Video Intelligence OS",
            "thumbnail_path": "assets/images/asset_02.svg",
            "accent_color": "#00d2ff",
        },
        property_types={
            "creator_name": "str",
            "creator_handle": "str",
            "avatar_path": "str",
            "brand_badge": "str",
            "headline": "str",
            "thumbnail_path": "str",
            "accent_color": "str",
        },
    )

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Validate creator assets and parameters."""
        for key in ["avatar_path", "thumbnail_path"]:
            val = props.get(key, "")
            if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://")):
                result.add_error(f"Forbidden remote URL in {key}: '{val}'")

    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        name = self.escape(props.get("creator_name", "Creator Name"))
        handle = self.escape(props.get("creator_handle", "@creator"))
        avatar = self.escape(props.get("avatar_path", "assets/images/avatar.svg"))
        badge = self.escape(props.get("brand_badge", "VERIFIED PRODUCER"))
        headline = self.escape(props.get("headline", ""))
        thumb = self.escape(props.get("thumbnail_path", ""))

        thumb_html = ""
        if thumb:
            thumb_html = f"""        <div class="feature-thumb-wrap">
          <img class="feature-thumb" src="{thumb}" alt="Feature Thumbnail" />
        </div>"""

        headline_html = f"""<div class="creator-headline">{headline}</div>""" if headline else ""

        return f"""    <!-- Block: creator_bottom_collage [{scene_id}] -->
    <div class="hf-block creator-bottom-collage" id="{scene_id}-creator" data-block-id="creator_bottom_collage">
      <div class="creator-bar">
        <div class="creator-identity">
          <div class="creator-avatar-wrap">
            <img class="creator-avatar" src="{avatar}" alt="{name}" />
            <div class="creator-status-dot"></div>
          </div>
          <div class="creator-meta">
            <div class="creator-brand-badge">{badge}</div>
            <div class="creator-name">{name}</div>
            <div class="creator-handle">{handle}</div>
          </div>
        </div>
        <div class="creator-feature">
{thumb_html}
          {headline_html}
        </div>
      </div>
    </div>"""

    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        is_portrait = format_aspect == "9:16"
        accent = self.sanitize_color(props.get("accent_color"), "#00d2ff")
        bottom_pos = "580px" if is_portrait else "50px"

        return f"""/* HyperFrames Block: creator_bottom_collage [{scene_id}] */
#{scene_id}-creator {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: {bottom_pos};
  display: flex;
  justify-content: center;
  padding: {'0 24px' if is_portrait else '0 64px'};
  box-sizing: border-box;
  z-index: 8;
}}

#{scene_id}-creator .creator-bar {{
  width: 100%;
  max-width: {'100%' if is_portrait else '1200px'};
  background: rgba(15, 23, 42, 0.94);
  border: 1.5px solid rgba(0, 210, 255, 0.35);
  border-radius: 24px;
  padding: {'18px 22px' if is_portrait else '20px 32px'};
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(16px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}}

#{scene_id}-creator .creator-identity {{
  display: flex;
  align-items: center;
  gap: 16px;
}}

#{scene_id}-creator .creator-avatar-wrap {{
  position: relative;
  width: {'52px' if is_portrait else '64px'};
  height: {'52px' if is_portrait else '64px'};
  border-radius: 50%;
  border: 2px solid {accent};
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.4);
  flex-shrink: 0;
}}

#{scene_id}-creator .creator-avatar {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}}

#{scene_id}-creator .creator-status-dot {{
  position: absolute;
  bottom: 0;
  right: 0;
  width: 14px;
  height: 14px;
  background: #10b981;
  border: 2px solid #0f172a;
  border-radius: 50%;
}}

#{scene_id}-creator .creator-meta {{
  display: flex;
  flex-direction: column;
  gap: 2px;
}}

#{scene_id}-creator .creator-brand-badge {{
  align-self: flex-start;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: {accent};
}}

#{scene_id}-creator .creator-name {{
  font-size: {'18px' if is_portrait else '22px'};
  font-weight: 800;
  color: #ffffff;
}}

#{scene_id}-creator .creator-handle {{
  font-size: 13px;
  color: #94a3b8;
}}

#{scene_id}-creator .creator-feature {{
  display: flex;
  align-items: center;
  gap: 16px;
}}

#{scene_id}-creator .feature-thumb-wrap {{
  width: {'70px' if is_portrait else '100px'};
  height: {'45px' if is_portrait else '56px'};
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}}

#{scene_id}-creator .feature-thumb {{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}

#{scene_id}-creator .creator-headline {{
  font-size: {'14px' if is_portrait else '17px'};
  font-weight: 600;
  color: #cbd5e1;
  max-width: 320px;
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
        return f"""  // GSAP: creator_bottom_collage [{scene_id}] (t={start_time}s, dur={duration}s)
  tl.set("#{scene_id}-creator", {{ autoAlpha: 1 }}, {start_time});
  tl.from("#{scene_id}-creator .creator-bar", {{
    y: 70,
    opacity: 0,
    duration: 0.7,
    ease: "power3.out"
  }}, {start_time});
  tl.from("#{scene_id}-creator .creator-avatar-wrap", {{
    scale: 0,
    opacity: 0,
    duration: 0.5,
    ease: "back.out(2.0)"
  }}, {start_time + 0.15});
  tl.from("#{scene_id}-creator .creator-feature", {{
    x: 30,
    opacity: 0,
    duration: 0.6,
    ease: "power2.out"
  }}, {start_time + 0.25});"""
