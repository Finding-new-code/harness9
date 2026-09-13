"""src.hyperframes.components.timeline_reveal — Timeline Reveal Component Block (Block 4).

Displays chronological progression across 3-4 historical milestones with animated connecting path/line
and progressive node pop-in.
"""

from typing import Any, Dict, List
from src.hyperframes.components.base import BaseComponent, ComponentSchema, ValidationResult


class TimelineReveal(BaseComponent):
    """Component Block 4: Timeline Reveal."""

    schema = ComponentSchema(
        block_id="timeline_reveal",
        display_name="Timeline Reveal",
        description="Chronological milestone timeline with animated connecting track line and progressive node reveals",
        category="chronology",
        supported_aspect_ratios=["16:9", "9:16"],
        required_props=["milestones"],
        default_props={
            "title": "Evolutionary Milestones",
            "badge": "CHRONOLOGY • HARNESS 9",
            "line_color": "#00d2ff",
            "accent_color": "#00d2ff",
            "milestones": [
                {
                    "year": "1947",
                    "title": "Point Contact",
                    "description": "Bardeen & Brattain invent first transistor.",
                },
                {
                    "year": "1954",
                    "title": "Silicon Transition",
                    "description": "Texas Instruments produces first commercial silicon transistor.",
                },
                {
                    "year": "1958",
                    "title": "Integrated Circuit",
                    "description": "Kilby & Noyce integrate components on one substrate.",
                },
                {
                    "year": "1971",
                    "title": "Microprocessor",
                    "description": "Intel 4004 puts complete CPU on single chip.",
                },
            ],
        },
        property_types={
            "title": "str",
            "badge": "str",
            "line_color": "str",
            "accent_color": "str",
            "milestones": "list[dict]",
        },
    )

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Validate milestones list format and structure."""
        milestones = props.get("milestones", [])
        if not isinstance(milestones, list):
            result.add_error("Property 'milestones' must be a list of milestone dictionaries")
            return

        if len(milestones) < 2:
            result.add_error("Property 'milestones' must contain at least 2 milestone entries")

        for idx, m in enumerate(milestones):
            if not isinstance(m, dict):
                result.add_error(f"Milestone at index {idx} must be a dictionary object")
            elif "year" not in m and "date" not in m:
                result.add_error(f"Milestone at index {idx} missing 'year' or 'date' property")

    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        title = self.escape(props.get("title", "Evolutionary Milestones"))
        badge = self.escape(props.get("badge", "CHRONOLOGY • HARNESS 9"))
        milestones = props.get("milestones", [])

        nodes_html = []
        for idx, m in enumerate(milestones):
            year_val = self.escape(m.get("year", m.get("date", f"Step {idx+1}")))
            m_title = self.escape(m.get("title", f"Milestone {idx+1}"))
            m_desc = self.escape(m.get("description", ""))

            node_tag = f"""        <div class="timeline-step timeline-step-{idx+1}">
          <div class="timeline-node">
            <div class="node-dot"></div>
          </div>
          <div class="timeline-card">
            <div class="milestone-year">{year_val}</div>
            <h3 class="milestone-title">{m_title}</h3>
            <p class="milestone-desc">{m_desc}</p>
          </div>
        </div>"""
            nodes_html.append(node_tag)

        nodes_body = "\n".join(nodes_html)

        return f"""    <!-- Block: timeline_reveal [{scene_id}] -->
    <div class="hf-block timeline-reveal" id="{scene_id}-timeline" data-block-id="timeline_reveal">
      <div class="timeline-header">
        <div class="timeline-badge">{badge}</div>
        <h2 class="timeline-title">{title}</h2>
      </div>
      <div class="timeline-container">
        <div class="timeline-track"></div>
        <div class="timeline-steps">
{nodes_body}
        </div>
      </div>
    </div>"""

    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        is_portrait = format_aspect == "9:16"
        line_color = self.sanitize_color(props.get("line_color") or props.get("accent_color"), "#00d2ff")
        padding_bottom = "600px" if is_portrait else "80px"
        title_size = "36px" if is_portrait else "48px"

        return f"""/* HyperFrames Block: timeline_reveal [{scene_id}] */
#{scene_id}-timeline {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: {'36px 28px' if is_portrait else '64px'};
  padding-bottom: {padding_bottom};
  box-sizing: border-box;
  z-index: 5;
}}

#{scene_id}-timeline .timeline-header {{
  margin-bottom: {'24px' if is_portrait else '40px'};
  display: flex;
  flex-direction: column;
  gap: 10px;
}}

#{scene_id}-timeline .timeline-badge {{
  align-self: flex-start;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: {line_color};
  background: rgba(0, 210, 255, 0.12);
  border: 1px solid {line_color};
  padding: 6px 14px;
  border-radius: 999px;
}}

#{scene_id}-timeline .timeline-title {{
  font-size: {title_size};
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
}}

#{scene_id}-timeline .timeline-container {{
  position: relative;
  width: 100%;
}}

#{scene_id}-timeline .timeline-track {{
  position: absolute;
  background: {line_color};
  box-shadow: 0 0 16px {line_color};
  z-index: 1;
  {'top: 0; bottom: 0; left: 15px; width: 3px;' if is_portrait else 'top: 15px; left: 0; right: 0; height: 3px;'}
}}

#{scene_id}-timeline .timeline-steps {{
  display: flex;
  flex-direction: {'column' if is_portrait else 'row'};
  gap: {'20px' if is_portrait else '24px'};
  position: relative;
  z-index: 2;
}}

#{scene_id}-timeline .timeline-step {{
  flex: 1;
  display: flex;
  flex-direction: {'row' if is_portrait else 'column'};
  align-items: {'flex-start' if is_portrait else 'center'};
  gap: {'20px' if is_portrait else '16px'};
}}

#{scene_id}-timeline .timeline-node {{
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #0a0e17;
  border: 2.5px solid {line_color};
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 0 16px rgba(0, 210, 255, 0.6);
  flex-shrink: 0;
}}

#{scene_id}-timeline .node-dot {{
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: {line_color};
}}

#{scene_id}-timeline .timeline-card {{
  background: rgba(15, 23, 42, 0.9);
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: {'18px 22px' if is_portrait else '24px 20px'};
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  width: 100%;
}}

#{scene_id}-timeline .milestone-year {{
  font-size: 13px;
  font-weight: 800;
  color: {line_color};
  letter-spacing: 1.5px;
  margin-bottom: 6px;
}}

#{scene_id}-timeline .milestone-title {{
  font-size: {'18px' if is_portrait else '20px'};
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 6px;
}}

#{scene_id}-timeline .milestone-desc {{
  font-size: {'14px' if is_portrait else '15px'};
  color: #94a3b8;
  line-height: 1.4;
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
        scale_prop = "scaleY" if is_portrait else "scaleX"
        origin = "top center" if is_portrait else "left center"

        return f"""  // GSAP: timeline_reveal [{scene_id}] (t={start_time}s, dur={duration}s)
  tl.set("#{scene_id}-timeline", {{ autoAlpha: 1 }}, {start_time});
  tl.from("#{scene_id}-timeline .timeline-header", {{
    y: -30,
    opacity: 0,
    duration: 0.6,
    ease: "power3.out"
  }}, {start_time});
  tl.from("#{scene_id}-timeline .timeline-track", {{
    {scale_prop}: 0,
    transformOrigin: "{origin}",
    duration: 0.8,
    ease: "power2.inOut"
  }}, {start_time + 0.15});
  tl.from("#{scene_id}-timeline .timeline-node", {{
    scale: 0,
    opacity: 0,
    stagger: 0.18,
    duration: 0.5,
    ease: "back.out(2.0)"
  }}, {start_time + 0.25});
  tl.from("#{scene_id}-timeline .timeline-card", {{
    y: 30,
    opacity: 0,
    stagger: 0.18,
    duration: 0.6,
    ease: "power3.out"
  }}, {start_time + 0.35});"""
