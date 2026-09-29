/**
 * HyperFrames Master GSAP Composition Controller
 * Compliant with HyperFrames deterministic seek & capture engine.
 */

// 1. Initialize Global Timelines Registry
window.__timelines = window.__timelines || {};

// 2. Synchronous Master Timeline Construction (must be paused: true)
const tl = gsap.timeline({
  paused: true,
  defaults: {
    ease: "power2.out",
    duration: 0.6
  }
});

// Register root composition timeline
window.__timelines["root"] = tl;

// 3. Scene Animations & Parameterized Component Blocks
  // Scene 1 container activation [s1]
  tl.set("#s1", { autoAlpha: 1 }, 0.0);
  // GSAP: reference_collage_hook [s1] (t=0.0s, dur=10.0s)
  tl.set("#s1-collage", { autoAlpha: 1 }, 0.0);
  tl.from("#s1-collage .collage-badge", {
    scale: 0.8,
    opacity: 0,
    duration: 0.5,
    ease: "back.out(1.7)"
  }, 0.0);
  tl.from("#s1-collage .collage-headline", {
    y: 40,
    opacity: 0,
    duration: 0.7,
    ease: "power3.out"
  }, 0.1);
  tl.from("#s1-collage .collage-item", {
    scale: 0.82,
    y: 30,
    opacity: 0,
    stagger: 0.15,
    duration: 0.75,
    ease: "power3.out"
  }, 0.25);
  tl.fromTo("#s1-collage .collage-card-glow", {
    opacity: 0.3
  }, {
    opacity: 0.8,
    duration: 1.2,
    repeat: Math.ceil(10.0 / 1.2) - 1,
    yoyo: true,
    ease: "sine.inOut"
  }, 0.5);
  tl.to("#s1", { opacity: 0, duration: 0.5, ease: "power2.in" }, 9.5);

// 4. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 10.0);
