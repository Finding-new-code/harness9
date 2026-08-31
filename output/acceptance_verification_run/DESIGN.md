# DESIGN: The History of the Transistor

## Brand
- **Name**: TechChronicles
- **Tagline**: Deep Tech Engineering & Architecture
- **Tone**: Authoritative, Cinematic, Modern

## Colors
- **Background**: `#0a0e17` — Deep navy-slate canvas
- **Primary Accent**: `#00d2ff` — Electric cyan for hero elements
- **Secondary Text**: `#8fa3bf` — Muted blue-grey for captions
- **Base Text**: `#ffffff` — Pure white headline and body text
- **Warning/Alert**: `#ff5252` — Vibrant coral for callouts

## Typography
- **Display**: 'Inter Tight', sans-serif (700) — Letter spacing: normal, Line height: 1.2
- **Body**: 'Inter', sans-serif (400) — Letter spacing: normal, Line height: 1.2

## Motion
- **Mood**: Cinematic & Fluid
- **Default Tween Duration**: 0.6s
- **Standard Easing**: `power2.out`
- **Emphasis Easing**: `elastic.out(1, 0.75)`
- **Transition Easing**: `power3.inOut`

## What NOT to Do
- Never use unbranded neon greens or harsh saturation mismatches.
- Never use pure black #000000 as background without deep-blue or slate tinting (#0a0e17).
- Never hardcode exit fades (gsap.to opacity: 0) on intermediate scenes (the scene transition acts as the exit).
- Never use infinite loops (repeat: -1); always calculate finite repeats: Math.ceil(duration / cycleDuration) - 1.
- Never use unbranded generic drop shadows; prefer crisp borders or ambient glow.
