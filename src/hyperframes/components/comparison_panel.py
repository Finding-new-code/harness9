"""src.hyperframes.components.comparison_panel — Comparison Panel Component Block (Block 6).

Side-by-side spec comparison table or Before/After breakdown with metric rows,
values for Entity A vs Entity B, and winner highlighting.
"""

from typing import Any, Dict, List
from src.hyperframes.components.base import BaseComponent, ComponentSchema, ValidationResult


class ComparisonPanel(BaseComponent):
    """Component Block 6: Comparison Panel."""

    schema = ComponentSchema(
        block_id="comparison_panel",
        display_name="Comparison Panel",
        description="Side-by-side comparison table contrasting two entities across multiple performance or technical metrics",
        category="data_tables",
        supported_aspect_ratios=["16:9", "9:16"],
        required_props=["entity_a_name", "entity_b_name"],
        default_props={
            "title": "Architectural Showdown",
            "badge": "HEAD-TO-HEAD • HARNESS 9",
            "entity_a_name": "Vacuum Tubes (1940s)",
            "entity_b_name": "Silicon Transistors (1950s+)",
            "accent_color": "#00d2ff",
            "comparison_rows": [
                {
                    "metric": "Power Consumption",
                    "val_a": "50W per gate",
                    "val_b": "< 0.001W per gate",
                    "winner": "b",
                },
                {
                    "metric": "Switching Speed",
                    "val_a": "100 kHz",
                    "val_b": "100+ MHz",
                    "winner": "b",
                },
                {
                    "metric": "Physical Footprint",
                    "val_a": "Bulky Glass Tube",
                    "val_b": "Sub-millimeter Crystal",
                    "winner": "b",
                },
                {
                    "metric": "Reliability (MTBF)",
                    "val_a": "Hours / Days",
                    "val_b": "Decades",
                    "winner": "b",
                },
            ],
        },
        property_types={
            "title": "str",
            "badge": "str",
            "entity_a_name": "str",
            "entity_b_name": "str",
            "accent_color": "str",
            "comparison_rows": "list[dict]",
        },
    )

    def _validate_props(
        self,
        props: Dict[str, Any],
        format_aspect: str,
        result: ValidationResult,
    ) -> None:
        """Validate comparison rows structure."""
        rows = props.get("comparison_rows", [])
        if not isinstance(rows, list):
            result.add_error("Property 'comparison_rows' must be a list of row dictionaries")
            return

        if len(rows) < 1:
            result.add_error("Property 'comparison_rows' must contain at least 1 comparison row")

        for idx, r in enumerate(rows):
            if not isinstance(r, dict):
                result.add_error(f"Comparison row at index {idx} must be a dictionary")
            elif "metric" not in r:
                result.add_error(f"Comparison row at index {idx} missing 'metric' property")

    def _render_html(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        title = self.escape(props.get("title", "Architectural Showdown"))
        badge = self.escape(props.get("badge", "HEAD-TO-HEAD • HARNESS 9"))
        name_a = self.escape(props.get("entity_a_name", "Entity A"))
        name_b = self.escape(props.get("entity_b_name", "Entity B"))
        rows = props.get("comparison_rows", [])

        rows_html = []
        for idx, r in enumerate(rows):
            metric = self.escape(r.get("metric", f"Metric {idx+1}"))
            val_a = self.escape(r.get("val_a", r.get("value_a", "-")))
            val_b = self.escape(r.get("val_b", r.get("value_b", "-")))
            winner = str(r.get("winner", "")).lower()

            win_a_cls = "is-winner" if winner in ["a", "left"] else ""
            win_b_cls = "is-winner" if winner in ["b", "right"] else ""

            row_tag = f"""          <div class="table-row table-row-{idx+1}">
            <div class="col-metric">{metric}</div>
            <div class="col-val col-val-a {win_a_cls}">{val_a}</div>
            <div class="col-val col-val-b {win_b_cls}">{val_b}</div>
          </div>"""
            rows_html.append(row_tag)

        rows_body = "\n".join(rows_html)

        return f"""    <!-- Block: comparison_panel [{scene_id}] -->
    <div class="hf-block comparison-panel" id="{scene_id}-comparison" data-block-id="comparison_panel">
      <div class="comparison-card">
        <div class="comparison-header">
          <div class="comparison-badge">{badge}</div>
          <h2 class="comparison-title">{title}</h2>
        </div>
        <div class="comparison-table">
          <div class="table-header-row">
            <div class="col-metric">KEY METRICS</div>
            <div class="col-entity col-entity-a">{name_a}</div>
            <div class="col-entity col-entity-b">{name_b}</div>
          </div>
          <div class="table-rows">
{rows_body}
          </div>
        </div>
      </div>
    </div>"""

    def _render_css(self, scene_id: str, props: Dict[str, Any], format_aspect: str) -> str:
        is_portrait = format_aspect == "9:16"
        accent = self.sanitize_color(props.get("accent_color"), "#00d2ff")
        title_size = "32px" if is_portrait else "44px"
        padding_bottom = "600px" if is_portrait else "80px"

        return f"""/* HyperFrames Block: comparison_panel [{scene_id}] */
#{scene_id}-comparison {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: {'32px 20px' if is_portrait else '64px'};
  padding-bottom: {padding_bottom};
  box-sizing: border-box;
  z-index: 5;
}}

#{scene_id}-comparison .comparison-card {{
  width: 100%;
  max-width: {'100%' if is_portrait else '1150px'};
  background: rgba(15, 23, 42, 0.92);
  border: 1.5px solid rgba(0, 210, 255, 0.35);
  border-radius: 28px;
  padding: {'32px 24px' if is_portrait else '48px 56px'};
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  gap: 24px;
}}

#{scene_id}-comparison .comparison-header {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}

#{scene_id}-comparison .comparison-badge {{
  align-self: flex-start;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: {accent};
  background: rgba(0, 210, 255, 0.12);
  border: 1px solid {accent};
  padding: 6px 14px;
  border-radius: 999px;
}}

#{scene_id}-comparison .comparison-title {{
  font-size: {title_size};
  font-weight: 800;
  color: #ffffff;
}}

#{scene_id}-comparison .comparison-table {{
  display: flex;
  flex-direction: column;
  width: 100%;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}}

#{scene_id}-comparison .table-header-row {{
  display: flex;
  background: rgba(30, 41, 59, 0.85);
  padding: 14px 20px;
  font-size: {'13px' if is_portrait else '15px'};
  font-weight: 800;
  letter-spacing: 1px;
  border-bottom: 1.5px solid rgba(255, 255, 255, 0.15);
}}

#{scene_id}-comparison .col-metric {{
  flex: {'1.2' if is_portrait else '1.5'};
  color: #94a3b8;
  font-weight: 700;
}}

#{scene_id}-comparison .col-entity-a {{
  flex: 1;
  color: #ff9800;
  text-align: right;
}}

#{scene_id}-comparison .col-entity-b {{
  flex: 1;
  color: {accent};
  text-align: right;
}}

#{scene_id}-comparison .table-row {{
  display: flex;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.6);
  font-size: {'13px' if is_portrait else '16px'};
  align-items: center;
}}

#{scene_id}-comparison .table-row:nth-child(even) {{
  background: rgba(30, 41, 59, 0.4);
}}

#{scene_id}-comparison .col-val {{
  flex: 1;
  text-align: right;
  color: #cbd5e1;
}}

#{scene_id}-comparison .col-val-a {{
  color: #e2e8f0;
}}

#{scene_id}-comparison .col-val-b {{
  color: #e2e8f0;
}}

#{scene_id}-comparison .col-val.is-winner {{
  color: #10b981;
  font-weight: 800;
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
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
        return f"""  // GSAP: comparison_panel [{scene_id}] (t={start_time}s, dur={duration}s)
  tl.set("#{scene_id}-comparison", {{ autoAlpha: 1 }}, {start_time});
  tl.from("#{scene_id}-comparison .comparison-card", {{
    scale: 0.94,
    opacity: 0,
    duration: 0.7,
    ease: "power3.out"
  }}, {start_time});
  tl.from("#{scene_id}-comparison .table-header-row", {{
    y: -15,
    opacity: 0,
    duration: 0.5,
    ease: "power2.out"
  }}, {start_time + 0.15});
  tl.from("#{scene_id}-comparison .table-row", {{
    x: -25,
    opacity: 0,
    stagger: 0.12,
    duration: 0.55,
    ease: "power2.out"
  }}, {start_time + 0.25});"""
