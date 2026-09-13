"""src.hyperframes.components.statistic_reveal — Statistic Reveal Component Block (Block 5).

Dramatizes a massive numerical breakthrough with a monumental hero counter,
prefix/suffix, metric badge, context subtext, and expanding pulse ring.
"""

from typing import Any, Dict
from src.hyperframes.components.base import BaseComponent, ComponentSchema, ValidationResult


class StatisticReveal(BaseComponent):
    """Component Block 5: Statistic Reveal."""

    schema = ComponentSchema(
        block_id="statistic_reveal",
        display_name="Statistic Reveal",
        description="High-impact numerical callout with large animated counter, unit labels, context subtext, and pulse rings",
        category="metrics",
        supported_aspect_ratios=["16:9", "9:16"],
        required_props=["target_number", "metric_label"],
        default_props={
            "badge": "BY THE NUMBERS",
            "target_number": "100 Billion",
            "prefix": "",
            "suffix": "+",
            "metric_label": "Transistors Per Modern Chip",
            "context_subtext": "A 10,000,000x increase in density since the Intel 4004 in 1971.",
            "accent_color": "#00d2ff",
            "pulse_color": "#00d2ff",
        },
        property_types={
            "badge": "str",
            "target_number": "str",
            "prefix": "str",
            "suffix": "str",
            "metric_label": "str",
            "context_subtext": "str",
            "accent_color": "str",
            "pulse_color": "str",
        },
    )

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Validate target number and labels."""
        num = props.get("target_number")
        if num is None or str(num).strip() == "":
            result.add_error("Property 'target_number' cannot be empty")
        lbl = props.get("metric_label")
        if lbl is None or str(lbl).strip() == "":
            result.add_error("Property 'metric_label' cannot be empty")

    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        badge = self.escape(props.get("badge", "BY THE NUMBERS"))
        num = self.escape(props.get("target_number", "100 Billion"))
        prefix = self.escape(props.get("prefix", ""))
        suffix = self.escape(props.get("suffix", "+"))
        label = self.escape(props.get("metric_label", "Key Metric"))
        context = self.escape(props.get("context_subtext", ""))

        context_html = f"""<p class="stat-context">{context}</p>""" if context else ""

        return f"""    <!-- Block: statistic_reveal [{scene_id}] -->
    <div class="hf-block statistic-reveal" id="{scene_id}-stat" data-block-id="statistic_reveal">
      <div class="stat-container">
        <div class="stat-badge">{badge}</div>
        <div class="stat-counter-box">
          <div class="pulse-ring"></div>
          <div class="stat-number-display">
            <span class="stat-prefix">{prefix}</span>
            <span class="stat-number">{num}</span>
            <span class="stat-suffix">{suffix}</span>
          </div>
        </div>
        <h2 class="stat-label">{label}</h2>
        {context_html}
      </div>
    </div>"""

    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        is_portrait = format_aspect == "9:16"
        accent = self.sanitize_color(props.get("accent_color"), "#00d2ff")
        num_size = "76px" if is_portrait else "112px"
        label_size = "28px" if is_portrait else "36px"
        padding_bottom = "620px" if is_portrait else "80px"

        return f"""/* HyperFrames Block: statistic_reveal [{scene_id}] */
#{scene_id}-stat {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: {'36px 24px' if is_portrait else '64px'};
  padding-bottom: {padding_bottom};
  box-sizing: border-box;
  z-index: 5;
}}

#{scene_id}-stat .stat-container {{
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: rgba(15, 23, 42, 0.92);
  border: 1.5px solid rgba(0, 210, 255, 0.4);
  border-radius: 32px;
  padding: {'48px 28px' if is_portrait else '64px 80px'};
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(20px);
  max-width: {'100%' if is_portrait else '1050px'};
  width: 100%;
  overflow: hidden;
}}

#{scene_id}-stat .stat-badge {{
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: {accent};
  background: rgba(0, 210, 255, 0.12);
  border: 1px solid {accent};
  padding: 6px 18px;
  border-radius: 999px;
  margin-bottom: 24px;
}}

#{scene_id}-stat .stat-counter-box {{
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 12px 0 20px 0;
}}

#{scene_id}-stat .pulse-ring {{
  position: absolute;
  width: {'220px' if is_portrait else '320px'};
  height: {'220px' if is_portrait else '320px'};
  border-radius: 50%;
  border: 2px solid {accent};
  box-shadow: 0 0 30px rgba(0, 210, 255, 0.5);
  pointer-events: none;
}}

#{scene_id}-stat .stat-number-display {{
  position: relative;
  z-index: 2;
  font-size: {num_size};
  font-weight: 900;
  line-height: 1;
  color: #ffffff;
  letter-spacing: -1.5px;
  text-shadow: 0 0 40px rgba(0, 210, 255, 0.6);
}}

#{scene_id}-stat .stat-prefix,
#{scene_id}-stat .stat-suffix {{
  color: {accent};
}}

#{scene_id}-stat .stat-label {{
  font-size: {label_size};
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 12px;
  line-height: 1.25;
}}

#{scene_id}-stat .stat-context {{
  font-size: {'16px' if is_portrait else '20px'};
  color: #94a3b8;
  max-width: 750px;
  line-height: 1.45;
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
        return f"""  // GSAP: statistic_reveal [{scene_id}] (t={start_time}s, dur={duration}s)
  tl.set("#{scene_id}-stat", {{ autoAlpha: 1 }}, {start_time});
  tl.from("#{scene_id}-stat .stat-badge", {{
    scale: 0.7,
    opacity: 0,
    duration: 0.5,
    ease: "back.out(1.8)"
  }}, {start_time});
  tl.from("#{scene_id}-stat .stat-number-display", {{
    scale: 0.5,
    opacity: 0,
    duration: 0.85,
    ease: "elastic.out(1, 0.75)"
  }}, {start_time + 0.15});
  tl.from("#{scene_id}-stat .stat-label", {{
    y: 25,
    opacity: 0,
    duration: 0.6,
    ease: "power2.out"
  }}, {start_time + 0.3});
  tl.from("#{scene_id}-stat .stat-context", {{
    y: 20,
    opacity: 0,
    duration: 0.6,
    ease: "power2.out"
  }}, {start_time + 0.4});
  tl.fromTo("#{scene_id}-stat .pulse-ring", {{
    scale: 0.8,
    opacity: 0.8
  }}, {{
    scale: 1.45,
    opacity: 0,
    duration: 1.6,
    repeat: Math.ceil({duration} / 1.6) - 1,
    ease: "power1.out"
  }}, {start_time + 0.25});"""
