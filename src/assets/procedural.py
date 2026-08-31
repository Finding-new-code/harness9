"""Procedural SVG vector and typography card generator for Harness 9 (F5).

Generates high-fidelity, scalable 1920x1080 (and custom aspect ratio) SVG graphics
for offline mode and synthetic topic visualizations:
- Semiconductor & circuit traces
- Computing, parallel architectures & AI nodes
- Aerospace, orbital mechanics & telemetry
- Quantum physics, wave functions & atomic shells
- Typographic quote cards & data metric callouts
"""

import html
import math
import re
from typing import Dict, List, Optional, Tuple


class ProceduralSVGGenerator:
    """Dynamic procedural SVG generator creating broadcast-grade vector assets."""

    THEMES = {
        "circuits": {
            "bg_top": "#070b14",
            "bg_bot": "#0d1527",
            "primary": "#00f2fe",
            "secondary": "#4facfe",
            "accent": "#00c6ff",
            "line_stroke": "rgba(79, 172, 254, 0.25)",
            "glow": "#00f2fe",
            "tag": "SEMICONDUCTOR & SOLID-STATE",
        },
        "computing": {
            "bg_top": "#090a1a",
            "bg_bot": "#131433",
            "primary": "#8a2be2",
            "secondary": "#4a00e0",
            "accent": "#00d2ff",
            "line_stroke": "rgba(138, 43, 226, 0.25)",
            "glow": "#9d4edd",
            "tag": "PARALLEL COMPUTING & ARCHITECTURE",
        },
        "aerospace": {
            "bg_top": "#050711",
            "bg_bot": "#0f1b2b",
            "primary": "#f59e0b",
            "secondary": "#d97706",
            "accent": "#38bdf8",
            "line_stroke": "rgba(245, 158, 11, 0.25)",
            "glow": "#fbbf24",
            "tag": "AEROSPACE & TELEMETRY",
        },
        "science": {
            "bg_top": "#041417",
            "bg_bot": "#09252a",
            "primary": "#10b981",
            "secondary": "#059669",
            "accent": "#06b6d4",
            "line_stroke": "rgba(16, 185, 129, 0.25)",
            "glow": "#34d399",
            "tag": "QUANTUM PHYSICS & EXPLORATION",
        },
        "general": {
            "bg_top": "#0a0e17",
            "bg_bot": "#162035",
            "primary": "#00d2ff",
            "secondary": "#3a7bd5",
            "accent": "#00f2fe",
            "line_stroke": "rgba(0, 210, 255, 0.20)",
            "glow": "#00d2ff",
            "tag": "TECHNOLOGY & INNOVATION",
        },
    }

    def __init__(self):
        pass

    @classmethod
    def classify_theme(cls, topic: str, query: str = "") -> str:
        """Classify topic string into one of the specialized visual theme styles."""
        combined = f"{topic} {query}".lower()
        if re.search(r"quantum|qubit|superposition|entanglement|atom|laser|optics|particle|physics", combined):
            return "science"
        if re.search(r"apollo|space|orbit|nasa|guidance|rocket|satellite|moon|lunar|telemetry|astronomy|telescope", combined):
            return "aerospace"
        if re.search(r"transistor|semiconductor|silicon|chip|wafer|circuit|integrated|microchip|vacuum tube|gate|p-n junction", combined):
            return "circuits"
        if re.search(r"gpu|computing|parallel|cuda|shader|processor|ai|neural|deep learning|memory|database|algorithm|software", combined):
            return "computing"
        return "general"

    @staticmethod
    def _clean_text(text: Optional[str], default: str = "") -> str:
        """Strip null bytes and non-XML-1.0 control characters and escape HTML entities."""
        val = text if text is not None else default
        val_str = str(val)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]", "", val_str)
        return html.escape(cleaned)

    def generate_topic_svg(
        self,
        topic: str,
        query: str = "",
        width: int = 1920,
        height: int = 1080,
        theme: Optional[str] = None,
        idx: int = 1,
    ) -> str:
        """Generate a complete standalone, scalable 1920x1080 SVG graphic tailored to topic."""
        selected_theme_key = theme if theme in self.THEMES else self.classify_theme(topic, query)
        palette = self.THEMES[selected_theme_key]

        safe_topic = self._clean_text(topic, "Technology Overview")
        safe_query = self._clean_text(query or topic, "Overview")
        tag = self._clean_text(palette["tag"])

        center_x = width // 2
        center_y = height // 2
        scale = min(width / 1920.0, height / 1080.0)

        # Generate theme-specific inner motif
        if selected_theme_key == "circuits":
            motif_svg = self._generate_circuit_motif(center_x, center_y, scale, palette)
        elif selected_theme_key == "computing":
            motif_svg = self._generate_computing_motif(center_x, center_y, scale, palette)
        elif selected_theme_key == "aerospace":
            motif_svg = self._generate_aerospace_motif(center_x, center_y, scale, palette)
        elif selected_theme_key == "science":
            motif_svg = self._generate_science_motif(center_x, center_y, scale, palette)
        else:
            motif_svg = self._generate_general_motif(center_x, center_y, scale, palette)

        grid_svg = self._generate_tech_grid(width, height, palette["line_stroke"])

        # Typography Card coordinates
        card_w = min(int(700 * scale), width - 60)
        card_h = min(int(280 * scale), height - 60)
        card_x = center_x - card_w // 2
        card_y = height - card_h - int(50 * scale)

        title_font_size = max(18, int(32 * scale))
        sub_font_size = max(14, int(20 * scale))
        tag_font_size = max(11, int(14 * scale))
        meta_font_size = max(10, int(13 * scale))

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bgGrad_{idx}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{palette['bg_top']}"/>
      <stop offset="100%" stop-color="{palette['bg_bot']}"/>
    </linearGradient>
    <linearGradient id="glowGrad_{idx}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{palette['primary']}"/>
      <stop offset="100%" stop-color="{palette['secondary']}"/>
    </linearGradient>
    <filter id="neonGlow_{idx}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Background Base -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad_{idx})"/>

  <!-- Technical Coordinate Grid -->
  {grid_svg}

  <!-- Theme Geometric Motif -->
  {motif_svg}

  <!-- Bottom Information Hero Card -->
  <g transform="translate({card_x}, {card_y})">
    <rect width="{card_w}" height="{card_h}" rx="{int(16 * scale)}" fill="rgba(10, 15, 26, 0.85)" stroke="{palette['primary']}" stroke-width="1.5" stroke-opacity="0.6"/>
    
    <!-- Header Pill Badge -->
    <rect x="{int(28 * scale)}" y="{int(24 * scale)}" width="{int(max(180, len(tag) * 9) * scale)}" height="{int(26 * scale)}" rx="{int(13 * scale)}" fill="rgba(255, 255, 255, 0.06)" stroke="{palette['primary']}" stroke-width="1"/>
    <text x="{int(38 * scale)}" y="{int(42 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{tag_font_size}" font-weight="700" fill="{palette['primary']}" letter-spacing="1">{tag}</text>

    <!-- Main Subject Title -->
    <text x="{int(28 * scale)}" y="{int(95 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{title_font_size}" font-weight="800" fill="#ffffff">{safe_topic}</text>
    
    <!-- Visual Subtitle / Query -->
    <text x="{int(28 * scale)}" y="{int(140 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{sub_font_size}" font-weight="500" fill="{palette['accent']}">{safe_query}</text>

    <!-- Provenance & Rights Stamp -->
    <line x1="{int(28 * scale)}" y1="{int(175 * scale)}" x2="{card_w - int(28 * scale)}" y2="{int(175 * scale)}" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
    <text x="{int(28 * scale)}" y="{int(208 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{meta_font_size}" fill="#8fa3bf">Harness 9 Verified Procedural Asset • Rights: CC0-1.0 Public Domain</text>
    <text x="{card_w - int(28 * scale)}" y="{int(208 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{meta_font_size}" font-weight="600" fill="{palette['secondary']}" text-anchor="end">{width}x{height} UHD</text>
  </g>
</svg>"""

    def generate_quote_card(
        self,
        quote: str,
        author: str,
        context: str = "",
        width: int = 1920,
        height: int = 1080,
    ) -> str:
        """Generate a sleek typographic quote card SVG."""
        safe_quote = self._clean_text(quote)
        safe_author = self._clean_text(author)
        safe_context = self._clean_text(context)
        scale = min(width / 1920.0, height / 1080.0)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="quoteBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0f1d"/>
      <stop offset="100%" stop-color="#050811"/>
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00d2ff"/>
      <stop offset="100%" stop-color="#3a7bd5"/>
    </linearGradient>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#quoteBg)"/>

  <!-- Quotation Mark Vector Glyph -->
  <text x="{int(160 * scale)}" y="{int(280 * scale)}" font-family="Georgia, serif" font-size="{int(220 * scale)}" fill="#00d2ff" opacity="0.18">“</text>

  <!-- Central Glass Card -->
  <rect x="{int(140 * scale)}" y="{int(180 * scale)}" width="{width - int(280 * scale)}" height="{height - int(360 * scale)}" rx="{int(24 * scale)}" fill="rgba(15, 23, 42, 0.7)" stroke="#00d2ff" stroke-width="1.5" stroke-opacity="0.4"/>

  <!-- Quote Text -->
  <text x="{width // 2}" y="{int(440 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(20, int(38 * scale))}" font-weight="600" fill="#ffffff" text-anchor="middle" letter-spacing="-0.5">
    "{safe_quote}"
  </text>

  <!-- Author Badge -->
  <text x="{width // 2}" y="{int(560 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(16, int(26 * scale))}" font-weight="700" fill="#00d2ff" text-anchor="middle">
    — {safe_author}
  </text>
  
  <!-- Context Details -->
  <text x="{width // 2}" y="{int(610 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(12, int(18 * scale))}" font-weight="400" fill="#94a3b8" text-anchor="middle">
    {safe_context}
  </text>
</svg>"""

    def generate_metric_card(
        self,
        metric: str,
        value: str,
        context: str = "",
        width: int = 1920,
        height: int = 1080,
    ) -> str:
        """Generate a high-contrast data metric callout SVG."""
        safe_metric = self._clean_text(metric)
        safe_value = self._clean_text(value)
        safe_context = self._clean_text(context)
        scale = min(width / 1920.0, height / 1080.0)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="metricBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b1329"/>
      <stop offset="100%" stop-color="#050914"/>
    </linearGradient>
    <linearGradient id="glowMetric" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#06b6d4"/>
    </linearGradient>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#metricBg)"/>

  <!-- Radial Progress Ring Decorator -->
  <circle cx="{width // 2}" cy="{height // 2 - int(40 * scale)}" r="{int(260 * scale)}" fill="none" stroke="rgba(16, 185, 129, 0.12)" stroke-width="{int(16 * scale)}"/>
  <circle cx="{width // 2}" cy="{height // 2 - int(40 * scale)}" r="{int(260 * scale)}" fill="none" stroke="url(#glowMetric)" stroke-width="{int(16 * scale)}" stroke-dasharray="{int(1200 * scale)}" stroke-dashoffset="{int(400 * scale)}" stroke-linecap="round"/>

  <!-- Main Value Number -->
  <text x="{width // 2}" y="{height // 2 - int(20 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(28, int(84 * scale))}" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="-1">{safe_value}</text>

  <!-- Metric Label -->
  <text x="{width // 2}" y="{height // 2 + int(60 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(16, int(30 * scale))}" font-weight="700" fill="#10b981" text-anchor="middle">{safe_metric}</text>

  <!-- Context -->
  <text x="{width // 2}" y="{height // 2 + int(110 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(12, int(20 * scale))}" fill="#94a3b8" text-anchor="middle">{safe_context}</text>
</svg>"""

    def generate_hero_card(
        self,
        headline: str,
        subheadline: str,
        topic: str = "",
        width: int = 1920,
        height: int = 1080,
    ) -> str:
        """Generate a bold hero visual for introduction scenes."""
        safe_head = self._clean_text(headline)
        safe_sub = self._clean_text(subheadline)
        safe_topic = self._clean_text((topic or "Documentary Showcase").upper())
        scale = min(width / 1920.0, height / 1080.0)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="heroBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#080c16"/>
      <stop offset="100%" stop-color="#111a2e"/>
    </linearGradient>
    <linearGradient id="heroAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00f2fe"/>
      <stop offset="100%" stop-color="#4facfe"/>
    </linearGradient>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#heroBg)"/>

  <!-- Centered Hero Iconography -->
  <g transform="translate({width // 2}, {height // 2 - int(100 * scale)})">
    <circle cx="0" cy="0" r="{int(140 * scale)}" fill="rgba(0, 242, 254, 0.06)" stroke="url(#heroAccent)" stroke-width="2"/>
    <circle cx="0" cy="0" r="{int(90 * scale)}" fill="rgba(79, 172, 254, 0.12)" stroke="#00f2fe" stroke-width="3" stroke-dasharray="10 6"/>
    <polygon points="0,{-int(40 * scale)} {int(35 * scale)},{int(25 * scale)} {-int(35 * scale)},{int(25 * scale)}" fill="url(#heroAccent)"/>
  </g>

  <!-- Topic Badge -->
  <text x="{width // 2}" y="{height // 2 + int(100 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(12, int(18 * scale))}" font-weight="700" fill="#00f2fe" letter-spacing="3" text-anchor="middle">{safe_topic}</text>

  <!-- Headline -->
  <text x="{width // 2}" y="{height // 2 + int(160 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(20, int(46 * scale))}" font-weight="900" fill="#ffffff" text-anchor="middle">{safe_head}</text>

  <!-- Subheadline -->
  <text x="{width // 2}" y="{height // 2 + int(210 * scale)}" font-family="'Inter', -apple-system, sans-serif" font-size="{max(14, int(22 * scale))}" fill="#8fa3bf" text-anchor="middle">{safe_sub}</text>
</svg>"""

    # ------------------------------------------------------------------------
    # Private Visual Helpers
    # ------------------------------------------------------------------------

    def _generate_tech_grid(self, width: int, height: int, stroke: str) -> str:
        """Generate subtle background technical grid lines."""
        lines = []
        step_x = max(80, width // 12)
        step_y = max(80, height // 8)

        for x in range(0, width + 1, step_x):
            lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="{stroke}" stroke-width="1"/>')
        for y in range(0, height + 1, step_y):
            lines.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="{stroke}" stroke-width="1"/>')

        return f'<g opacity="0.45">{"".join(lines)}</g>'

    def _generate_circuit_motif(self, cx: int, cy: int, s: float, p: Dict[str, str]) -> str:
        """Generate semiconductor die and circuit traces."""
        die_size = int(320 * s)
        half_die = die_size // 2
        chip_x = cx - half_die
        chip_y = cy - half_die - int(100 * s)

        traces = []
        # Draw decorative circuit lines and terminal pins
        for i in range(-4, 5):
            offset = int(i * 30 * s)
            traces.append(f'<line x1="{cx + offset}" y1="{chip_y - int(80 * s)}" x2="{cx + offset}" y2="{chip_y}" stroke="{p["secondary"]}" stroke-width="2.5"/>')
            traces.append(f'<circle cx="{cx + offset}" cy="{chip_y - int(80 * s)}" r="4" fill="{p["primary"]}"/>')
            traces.append(f'<line x1="{chip_x - int(80 * s)}" y1="{chip_y + half_die + offset}" x2="{chip_x}" y2="{chip_y + half_die + offset}" stroke="{p["secondary"]}" stroke-width="2.5"/>')
            traces.append(f'<circle cx="{chip_x - int(80 * s)}" cy="{chip_y + half_die + offset}" r="4" fill="{p["primary"]}"/>')

        return f"""<g>
    <!-- Circuit Traces -->
    {''.join(traces)}
    <!-- Main Silicon Chip Die -->
    <rect x="{chip_x}" y="{chip_y}" width="{die_size}" height="{die_size}" rx="{int(20 * s)}" fill="#0c1628" stroke="{p['primary']}" stroke-width="3" filter="url(#neonGlow_1)"/>
    <!-- Core Die Center Ring -->
    <circle cx="{cx}" cy="{chip_y + half_die}" r="{int(75 * s)}" fill="none" stroke="{p['accent']}" stroke-width="2" stroke-dasharray="8 6"/>
    <circle cx="{cx}" cy="{chip_y + half_die}" r="{int(35 * s)}" fill="{p['primary']}" opacity="0.8"/>
  </g>"""

    def _generate_computing_motif(self, cx: int, cy: int, s: float, p: Dict[str, str]) -> str:
        """Generate parallel GPU / computing node matrix."""
        cy_adj = cy - int(100 * s)
        nodes = []
        rows, cols = 4, 6
        spacing = int(70 * s)
        start_x = cx - int((cols - 1) * spacing / 2)
        start_y = cy_adj - int((rows - 1) * spacing / 2)

        for r in range(rows):
            for c in range(cols):
                nx = start_x + c * spacing
                ny = start_y + r * spacing
                if c < cols - 1:
                    nodes.append(f'<line x1="{nx}" y1="{ny}" x2="{nx + spacing}" y2="{ny}" stroke="{p["line_stroke"]}" stroke-width="2"/>')
                if r < rows - 1:
                    nodes.append(f'<line x1="{nx}" y1="{ny}" x2="{nx}" y2="{ny + spacing}" stroke="{p["line_stroke"]}" stroke-width="2"/>')
                nodes.append(f'<circle cx="{nx}" cy="{ny}" r="{int(10 * s)}" fill="{p["primary"]}" stroke="{p["accent"]}" stroke-width="2"/>')

        return f"""<g>
    <rect x="{cx - int(240 * s)}" y="{cy_adj - int(160 * s)}" width="{int(480 * s)}" height="{int(320 * s)}" rx="{int(24 * s)}" fill="rgba(19, 20, 51, 0.6)" stroke="{p['primary']}" stroke-width="2"/>
    {''.join(nodes)}
  </g>"""

    def _generate_aerospace_motif(self, cx: int, cy: int, s: float, p: Dict[str, str]) -> str:
        """Generate orbital paths and aerospace HUD."""
        cy_adj = cy - int(100 * s)
        return f"""<g>
    <!-- Planetary Body -->
    <circle cx="{cx}" cy="{cy_adj}" r="{int(100 * s)}" fill="#142338" stroke="{p['primary']}" stroke-width="3"/>
    <!-- Orbital Ellipses -->
    <ellipse cx="{cx}" cy="{cy_adj}" rx="{int(240 * s)}" ry="{int(80 * s)}" fill="none" stroke="{p['secondary']}" stroke-width="2" transform="rotate(-25 {cx} {cy_adj})"/>
    <ellipse cx="{cx}" cy="{cy_adj}" rx="{int(280 * s)}" ry="{int(110 * s)}" fill="none" stroke="{p['accent']}" stroke-width="1.5" stroke-dasharray="10 8" transform="rotate(35 {cx} {cy_adj})"/>
    <!-- Satellite Marker -->
    <circle cx="{cx + int(180 * s)}" cy="{cy_adj - int(70 * s)}" r="{int(8 * s)}" fill="{p['primary']}"/>
  </g>"""

    def _generate_science_motif(self, cx: int, cy: int, s: float, p: Dict[str, str]) -> str:
        """Generate atomic orbital rings and quantum wave."""
        cy_adj = cy - int(100 * s)
        return f"""<g>
    <!-- Atomic Nucleus -->
    <circle cx="{cx}" cy="{cy_adj}" r="{int(30 * s)}" fill="{p['primary']}"/>
    <!-- Quantum Electron Shells -->
    <ellipse cx="{cx}" cy="{cy_adj}" rx="{int(220 * s)}" ry="{int(75 * s)}" fill="none" stroke="{p['secondary']}" stroke-width="2" transform="rotate(0 {cx} {cy_adj})"/>
    <ellipse cx="{cx}" cy="{cy_adj}" rx="{int(220 * s)}" ry="{int(75 * s)}" fill="none" stroke="{p['secondary']}" stroke-width="2" transform="rotate(60 {cx} {cy_adj})"/>
    <ellipse cx="{cx}" cy="{cy_adj}" rx="{int(220 * s)}" ry="{int(75 * s)}" fill="none" stroke="{p['secondary']}" stroke-width="2" transform="rotate(120 {cx} {cy_adj})"/>
  </g>"""

    def _generate_general_motif(self, cx: int, cy: int, s: float, p: Dict[str, str]) -> str:
        """Generate geometric tech nexus."""
        cy_adj = cy - int(100 * s)
        return f"""<g>
    <circle cx="{cx}" cy="{cy_adj}" r="{int(180 * s)}" fill="none" stroke="{p['primary']}" stroke-width="3" stroke-dasharray="16 10"/>
    <circle cx="{cx}" cy="{cy_adj}" r="{int(110 * s)}" fill="none" stroke="{p['secondary']}" stroke-width="2"/>
    <rect x="{cx - int(60 * s)}" y="{cy_adj - int(60 * s)}" width="{int(120 * s)}" height="{int(120 * s)}" rx="{int(16 * s)}" fill="#121e33" stroke="{p['accent']}" stroke-width="2.5"/>
  </g>"""
