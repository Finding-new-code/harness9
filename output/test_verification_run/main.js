// HyperFrames GSAP Composition Controller
window.__timelines = window.__timelines || {};

// Initialize root timeline with paused state for frame capture engine
const tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
window.__timelines["root"] = tl;

// Synchronous Scene Choreography

// scene_1 [start: 0.0s, dur: 10.0s]
tl.set(".scene_1", { opacity: 1, visibility: "visible" }, 0.0);
tl.from(".scene_1 .scene-content", { y: 40, opacity: 0, duration: 0.8 }, 0.0);
tl.from(".scene_1 .scene-img", { scale: 1.08, duration: 10.0, ease: "none" }, 0.0);
tl.set(".scene_1", { opacity: 0, visibility: "hidden" }, 10.0);


// scene_2 [start: 10.0s, dur: 10.0s]
tl.set(".scene_2", { opacity: 1, visibility: "visible" }, 10.0);
tl.from(".scene_2 .scene-content", { y: 40, opacity: 0, duration: 0.8 }, 10.0);
tl.from(".scene_2 .scene-img", { scale: 1.08, duration: 10.0, ease: "none" }, 10.0);
tl.set(".scene_2", { opacity: 0, visibility: "hidden" }, 20.0);


// scene_3 [start: 20.0s, dur: 10.0s]
tl.set(".scene_3", { opacity: 1, visibility: "visible" }, 20.0);
tl.from(".scene_3 .scene-content", { y: 40, opacity: 0, duration: 0.8 }, 20.0);
tl.from(".scene_3 .scene-img", { scale: 1.08, duration: 10.0, ease: "none" }, 20.0);
tl.set(".scene_3", { opacity: 0, visibility: "hidden" }, 30.0);


// Finite repeat math calculation (bounded cycle duration)
const cycleDuration = 2.0;
const repeatCount = Math.ceil(30 / cycleDuration) - 1;

// Global hook for capture engine
window.seekComposition = function(seconds) {
  tl.seek(seconds);
};
