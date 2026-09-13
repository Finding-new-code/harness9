# HyperFrames Integration & Registry Specification: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `adapters/hyperframes/`, `src/hyperframes/`  
**Cross-References:** `docs/ARCHITECTURE.md`, `docs/SYSTEM_DESIGN.md`, `docs/adrs/ADR-004.md`  

---

## 1. Executive Summary & Interface Scope

The Harness 9 **HyperFrames Integration** provides a clean, decoupled bridge between the high-level narrative scriptwriter and the low-level visual rendering engine. It compiles abstract scene descriptions and frozen media assets into standards-compliant HTML5/CSS3/GSAP compositions, validates them through a composition linter, and renders them to broadcast MP4 video files.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Script & Storyboard Scene Requirements                   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HyperFrames Component Registry                        │
│                                                                             │
│ ┌───────────────────────┐ ┌───────────────────────┐ ┌────────────────────┐  │
│ │ ReferenceCollageHook  │ │   SplitScreenIntro    │ │   QuoteHighlight   │  │
│ └───────────────────────┘ └───────────────────────┘ └────────────────────┘  │
│ ┌───────────────────────┐ ┌───────────────────────┐ ┌────────────────────┐  │
│ │    TimelineReveal     │ │    StatisticReveal    │ │  ComparisonPanel   │  │
│ └───────────────────────┘ └───────────────────────┘ └────────────────────┘  │
│ ┌─────────────────────────────────────────────────┐                         │
│ │              CreatorBottomCollage               │                         │
│ └─────────────────────────────────────────────────┘                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTML5 + CSS3 + GSAP Timeline Code
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Composition Linter & AST Validator                       │
│     (Safe Zones, No Remote URLs, Zero Infinite Loops, Master Timeline)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Validated index.html
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               Headless Playwright Frame Grabber + FFmpeg Muxer              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Master GSAP Protocol & DOM Schema

Every HyperFrames composition must strictly adhere to the following DOM and JavaScript contract:

### 2.1 DOM Root Container
- The root document must contain a top-level container element with attribute `data-composition-id="root"`:
  ```html
  <div id="root" data-composition-id="root" class="composition-root">
    <!-- Scene blocks injected here -->
  </div>
  ```
- **Viewport Dimensioning**:
  - Horizontal ($16:9$): `width: 1920px; height: 1080px;`
  - Vertical ($9:16$): `width: 1080px; height: 1920px;`

### 2.2 Global Timeline Registration
- All GSAP animations must be compiled into a single master timeline registered on the global `window` object:
  ```javascript
  window.__timelines = window.__timelines || {};
  const masterTimeline = gsap.timeline({ paused: true });
  
  // Scene animations added via labels and relative offsets
  masterTimeline.addLabel("scene_1", 0.0);
  masterTimeline.to("#block-1", { duration: 1.2, opacity: 1, y: 0, ease: "power2.out" }, "scene_1");
  
  window.__timelines["root"] = masterTimeline;
  ```
- **Seeking Contract**: The headless renderer advances time deterministically using `window.__timelines["root"].seek(currentTimeInSeconds)`.

---

## 3. The 7 Canonical Reusable Component Blocks

### 3.1 `ReferenceCollageHook`
- **Purpose**: High-energy opening visual showing 3 staggered reference image cards rotating into view.
- **Parameters**: `title: str`, `badge_text: str`, `image_cards: List[str]`, `accent_color: str`.
- **GSAP Sequence**: Staggered $y$-axis slide-in with subtle $-3^\circ$ and $+4^\circ$ card rotations.

### 3.2 `SplitScreenIntro`
- **Purpose**: Direct contrast between two competing concepts or historical eras.
- **Parameters**: `left_label: str`, `left_image: str`, `right_label: str`, `right_image: str`, `divider_color: str`.
- **GSAP Sequence**: Expanding vertical divider bar with opposing horizontal panel slide-ins.

### 3.3 `QuoteHighlight`
- **Purpose**: High-authority citation callout emphasizing primary research quotes.
- **Parameters**: `quote_text: str`, `author_name: str`, `author_title: str`, `avatar_url: str`.
- **GSAP Sequence**: Scaling quotation mark glyph, kinetic text fade-in, author badge slide-up.

### 3.4 `TimelineReveal`
- **Purpose**: Sequential chronological breakdown of historical milestones or technological evolution.
- **Parameters**: `milestones: List[Dict[str, str]]`, `active_index: int`, `glow_color: str`.
- **GSAP Sequence**: Glowing vertical track animation illuminating milestone nodes sequentially.

### 3.5 `StatisticReveal`
- **Purpose**: Punchy quantitative metric presentation with dynamic counter.
- **Parameters**: `number_value: str`, `unit_label: str`, `context_description: str`, `accent_glow: str`.
- **GSAP Sequence**: Kinetic number scale-up ($0.8 \to 1.0$), radial ring sweep, text fade-in.

### 3.6 `ComparisonPanel`
- **Purpose**: Structured tabular comparison highlighting strengths and trade-offs.
- **Parameters**: `rows: List[Dict[str, Any]]`, `header_a: str`, `header_b: str`.
- **GSAP Sequence**: Staggered row reveals with animated green checkmarks and red crosses.

### 3.7 `CreatorBottomCollage`
- **Purpose**: Persistent branded lower-third creator card displaying avatar and channel identity.
- **Parameters**: `creator_name: str`, `handle: str`, `brand_color: str`.
- **GSAP Sequence**: Smooth slide-in from bottom screen boundary, holding through scene duration.

---

## 4. Composition Linter & AST Validator Rules

Before sending any generated composition to the rendering engine, the `CompositionValidator` enforces the following rules:

1. **`RULE_NO_REMOTE_URLS`**: Rejects any `http://` or `https://` string in `src`, `href`, or CSS `url()` rules. All assets must point to frozen local files (`assets/...`).
2. **`RULE_NO_INFINITE_LOOPS`**: Rejects any GSAP animation containing `repeat: -1` or `repeat: Infinity`, which prevents headless renderers from determining stream completion.
3. **`RULE_ROOT_TIMELINE_EXISTS`**: Verifies that `window.__timelines["root"]` is assigned a valid GSAP timeline instance.
4. **`RULE_SAFE_ZONE_COMPLIANCE`**: Ensures all critical typography and cards maintain minimum $64\text{px}$ margin from screen boundaries ($120\text{px}$ for 9:16 vertical safe zones).
5. **`RULE_ASPECT_RATIO_MATCH`**: Verifies that root CSS dimensions exactly match target project aspect ratio ($1920\times 1080$ vs $1080\times 1920$).
