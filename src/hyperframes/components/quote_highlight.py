"""src.hyperframes.components.quote_highlight — Quote Highlight Component Block (Block 3).

Highlights an authoritative quote or key historical claim with stylized quotation marks,
author credentials, avatar, and ambient glowing glassmorphism backdrop.
"""

from typing import Any, Dict
from src.hyperframes.components.base import BaseComponent, ComponentSchema, ValidationResult


class QuoteHighlight(BaseComponent):
    """Component Block 3: Quote Highlight."""

    schema = ComponentSchema(
        block_id="quote_highlight",
        display_name="Quote Highlight",
        description="Authoritative citation card with quotation mark styling, author avatar, and glowing kinetic backdrop",
        category="citations",
        supported_aspect_ratios=["16:9", "9:16"],
        required_props=["quote_text", "author_name"],
        default_props={
            "quote_text": "We knew the world would not be the same.",
            "author_name": "J. Robert Oppenheimer",
            "author_title": "Director, Los Alamos Laboratory",
            "author_image": "assets/images/asset_01.svg",
            "accent_color": "#00d2ff",
            "publication": "Trinity Test Witness",
            "date": "1945",
        },
        property_types={
            "quote_text": "str",
            "author_name": "str",
            "author_title": "str",
            "author_image": "str",
            "accent_color": "str",
            "publication": "str",
            "date": "str",
        },
    )

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Validate quote text and author info."""
        img = props.get("author_image", "")
        if isinstance(img, str) and (img.startswith("http://") or img.startswith("https://")):
            result.add_error(f"Forbidden remote URL in author_image: '{img}'")

    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        quote = self.escape(props.get("quote_text", ""))
        name = self.escape(props.get("author_name", "Author"))
        title = self.escape(props.get("author_title", ""))
        image = self.escape(props.get("author_image", ""))
        publication = self.escape(props.get("publication", ""))
        date_str = self.escape(props.get("date", ""))

        avatar_html = ""
        if image:
            avatar_html = f"""          <div class="quote-avatar-wrap">
            <img class="quote-avatar" src="{image}" alt="{name}" />
          </div>"""

        pub_meta = []
        if publication:
            pub_meta.append(publication)
        if date_str:
            pub_meta.append(date_str)
        pub_text = self.escape(" • ".join(pub_meta))
        pub_html = f"""<div class="quote-pub">{pub_text}</div>""" if pub_text else ""

        return f"""    <!-- Block: quote_highlight [{scene_id}] -->
    <div class="hf-block quote-highlight" id="{scene_id}-quote" data-block-id="quote_highlight">
      <div class="quote-card">
        <div class="quote-mark">“</div>
        <blockquote class="quote-body">
          {quote}
        </blockquote>
        <div class="quote-author-row">
{avatar_html}
          <div class="quote-author-info">
            <div class="quote-author-name">{name}</div>
            <div class="quote-author-title">{title}</div>
            {pub_html}
          </div>
        </div>
        <div class="quote-card-ambient"></div>
      </div>
    </div>"""

    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        is_portrait = format_aspect == "9:16"
        accent = self.sanitize_color(props.get("accent_color"), "#00d2ff")
        quote_size = "32px" if is_portrait else "42px"
        padding_bottom = "620px" if is_portrait else "80px"

        return f"""/* HyperFrames Block: quote_highlight [{scene_id}] */
#{scene_id}-quote {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: {'36px 28px' if is_portrait else '64px'};
  padding-bottom: {padding_bottom};
  box-sizing: border-box;
  z-index: 5;
}}

#{scene_id}-quote .quote-card {{
  position: relative;
  width: 100%;
  max-width: {'100%' if is_portrait else '1100px'};
  background: rgba(15, 23, 42, 0.9);
  border: 1.5px solid rgba(0, 210, 255, 0.35);
  border-radius: 28px;
  padding: {'40px 32px' if is_portrait else '56px 64px'};
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(20px);
  overflow: hidden;
}}

#{scene_id}-quote .quote-mark {{
  font-family: Georgia, serif;
  font-size: {'80px' if is_portrait else '110px'};
  line-height: 0.7;
  color: {accent};
  opacity: 0.6;
  margin-bottom: 8px;
}}

#{scene_id}-quote .quote-body {{
  font-size: {quote_size};
  font-weight: 600;
  line-height: 1.35;
  color: #ffffff;
  font-style: italic;
  letter-spacing: -0.3px;
  margin-bottom: 32px;
  position: relative;
  z-index: 2;
}}

#{scene_id}-quote .quote-author-row {{
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 2;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 24px;
}}

#{scene_id}-quote .quote-avatar-wrap {{
  width: {'60px' if is_portrait else '72px'};
  height: {'60px' if is_portrait else '72px'};
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid {accent};
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.4);
  flex-shrink: 0;
}}

#{scene_id}-quote .quote-avatar {{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}

#{scene_id}-quote .quote-author-info {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}

#{scene_id}-quote .quote-author-name {{
  font-size: {'22px' if is_portrait else '26px'};
  font-weight: 800;
  color: #ffffff;
}}

#{scene_id}-quote .quote-author-title {{
  font-size: {'16px' if is_portrait else '18px'};
  color: {accent};
  font-weight: 500;
}}

#{scene_id}-quote .quote-pub {{
  font-size: 14px;
  color: #94a3b8;
}}

#{scene_id}-quote .quote-card-ambient {{
  position: absolute;
  top: -20%;
  right: -20%;
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(0, 210, 255, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 1;
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
        return f"""  // GSAP: quote_highlight [{scene_id}] (t={start_time}s, dur={duration}s)
  tl.set("#{scene_id}-quote", {{ autoAlpha: 1 }}, {start_time});
  tl.from("#{scene_id}-quote .quote-card", {{
    scale: 0.92,
    opacity: 0,
    duration: 0.75,
    ease: "power3.out"
  }}, {start_time});
  tl.from("#{scene_id}-quote .quote-mark", {{
    scale: 0.6,
    opacity: 0,
    duration: 0.5,
    ease: "back.out(1.8)"
  }}, {start_time + 0.1});
  tl.from("#{scene_id}-quote .quote-body", {{
    y: 30,
    opacity: 0,
    duration: 0.65,
    ease: "power2.out"
  }}, {start_time + 0.2});
  tl.from("#{scene_id}-quote .quote-author-row", {{
    x: -25,
    opacity: 0,
    duration: 0.55,
    ease: "power2.out"
  }}, {start_time + 0.35});
  tl.fromTo("#{scene_id}-quote .quote-card-ambient", {{
    scale: 0.8,
    opacity: 0.2
  }}, {{
    scale: 1.2,
    opacity: 0.6,
    duration: 2.0,
    repeat: Math.ceil({duration} / 2.0) - 1,
    yoyo: true,
    ease: "sine.inOut"
  }}, {start_time + 0.4});"""
