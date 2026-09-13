/**
 * HyperFrames GSAP Composition Controller
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

// 3. Scene Hierarchy & Entrance Choreography
  // Scene 1: scene_1 (t=0.0s to 7.5s)
  tl.set("#scene_1", { autoAlpha: 1 }, 0.0);
  tl.from("#scene_1 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 0.0);
  tl.from("#scene_1 .hero-image", {
    scale: 1.15,
    duration: 7.5,
    ease: "none"
  }, 0.0);
  tl.set("#scene_1", { autoAlpha: 0 }, 7.5);

  // Scene 2: scene_2 (t=7.5s to 15.0s)
  tl.set("#scene_2", { autoAlpha: 1 }, 7.5);
  tl.from("#scene_2 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 7.5);
  tl.from("#scene_2 .hero-image", {
    scale: 1.15,
    duration: 7.5,
    ease: "none"
  }, 7.5);
  tl.set("#scene_2", { autoAlpha: 0 }, 15.0);

  // Scene 3: scene_3 (t=15.0s to 22.5s)
  tl.set("#scene_3", { autoAlpha: 1 }, 15.0);
  tl.from("#scene_3 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 15.0);
  tl.from("#scene_3 .hero-image", {
    scale: 1.15,
    duration: 7.5,
    ease: "none"
  }, 15.0);
  tl.set("#scene_3", { autoAlpha: 0 }, 22.5);

  // Scene 4: scene_4 (t=22.5s to 30.0s)
  tl.set("#scene_4", { autoAlpha: 1 }, 22.5);
  tl.from("#scene_4 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 22.5);
  tl.from("#scene_4 .hero-image", {
    scale: 1.15,
    duration: 7.5,
    ease: "none"
  }, 22.5);
  tl.to("#scene_4", { opacity: 0, duration: 0.5, ease: "power2.in" }, 29.5);

// 4. Kinetic Captions Alignment (with Hard Kill Guarantee)
  // Caption: "The Vacuum Tube" [0.0s - 0.415s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Vacuum Tube";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.295);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 0.415);

  // Caption: "Bottleneck. Before the" [0.415s - 1.03s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Bottleneck. Before the";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.415);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.415);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.91);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 1.03);

  // Caption: "computer in your" [1.03s - 1.497s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "computer in your";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 1.03);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 1.03);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 1.3770000000000002);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 1.497);

  // Caption: "pocket, early computers" [1.497s - 2.127s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "pocket, early computers";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 1.497);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 1.497);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.0069999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.127);

  // Caption: "filled entire rooms" [2.127s - 2.638s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "filled entire rooms";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.127);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.127);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.518);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.638);

  // Caption: "with burning hot," [2.638s - 3.031s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "with burning hot,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.638);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.638);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.911);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 3.031);

  // Caption: "glass vacuum tubes." [3.031s - 3.565s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "glass vacuum tubes.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 3.031);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 3.031);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 3.445);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 3.565);

  // Caption: "Early vacuum tubes" [3.565s - 4.098s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Early vacuum tubes";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 3.565);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 3.565);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 3.9779999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.098);

  // Caption: "consumed large amounts" [4.098s - 4.691s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "consumed large amounts";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.098);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.098);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.571);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.691);

  // Caption: "of power and" [4.691s - 4.988s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "of power and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.691);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.691);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.868);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.988);

  // Caption: "generated high heat;" [4.988s - 5.536s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "generated high heat;";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.988);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.988);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 5.4159999999999995);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.536);

  // Caption: "transistors slashed power" [5.536s - 6.136s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "transistors slashed power";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.536);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.536);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.016);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.136);

  // Caption: "consumption by over" [6.136s - 6.648s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "consumption by over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.136);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.136);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.528);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.648);

  // Caption: "99% and miniaturized" [6.648s - 7.196s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "99% and miniaturized";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.648);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.648);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.076);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.196);

  // Caption: "circuits." [7.196s - 7.5s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "circuits.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.196);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.196);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.38);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.5);

  // Caption: "The Miracle at" [7.5s - 7.872s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Miracle at";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.5);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.5);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.752);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.872);

  // Caption: "Bell Labs. On" [7.872s - 8.214s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Bell Labs. On";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.872);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.872);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.094000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.214);

  // Caption: "two cold days" [8.214s - 8.532s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "two cold days";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.214);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.214);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.412);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.532);

  // Caption: "in December 1947," [8.532s - 8.973s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "in December 1947,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.532);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.532);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.853000000000002);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.973);

  // Caption: "three physicists made" [8.973s - 9.527s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "three physicists made";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.973);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.973);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.407);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.527);

  // Caption: "history with a" [9.527s - 9.899s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "history with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.527);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.527);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.779);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.899);

  // Caption: "sliver of germanium," [9.899s - 10.461s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "sliver of germanium,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.899);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.899);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.341000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.461);

  // Caption: "gold foil, and" [10.461s - 10.817s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "gold foil, and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.461);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.461);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.697000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.817);

  // Caption: "a paper clip." [10.817s - 11.197s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a paper clip.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.817);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.817);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 11.077);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 11.197);

  // Caption: "The first working" [11.197s - 11.576s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The first working";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 11.197);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 11.197);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 11.456000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 11.576);

  // Caption: "point-contact transistor was" [11.576s - 12.26s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "point-contact transistor was";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 11.576);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 11.576);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 12.14);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.26);

  // Caption: "successfully demonstrated on" [12.26s - 12.996s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "successfully demonstrated on";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.26);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.26);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 12.876000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.996);

  // Caption: "December 23, 1947," [12.996s - 13.474s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "December 23, 1947,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.996);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.996);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.354000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.474);

  // Caption: "by John Bardeen" [13.474s - 13.861s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "by John Bardeen";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.474);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.474);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.741000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.861);

  // Caption: "and Walter Brattain" [13.861s - 14.347s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and Walter Brattain";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.861);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.861);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 14.227);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 14.347);

  // Caption: "at Bell Laboratories." [14.347s - 15.0s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "at Bell Laboratories.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 14.347);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 14.347);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 14.88);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.0);

  // Caption: "100 Billion Strong." [15.0s - 15.55s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 Billion Strong.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 15.430000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.55);

  // Caption: "Today, that single" [15.55s - 16.083s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Today, that single";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.55);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.55);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 15.963);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 16.083);

  // Caption: "rough prototype has" [16.083s - 16.649s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "rough prototype has";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 16.083);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 16.083);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 16.529);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 16.649);

  // Caption: "scaled to over" [16.649s - 17.051s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "scaled to over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 16.649);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 16.649);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 16.930999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.051);

  // Caption: "100 billion microscopic" [17.051s - 17.724s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 billion microscopic";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.051);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.051);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 17.604);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.724);

  // Caption: "switches powering every" [17.724s - 18.397s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "switches powering every";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.724);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.724);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.276999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.397);

  // Caption: "AI and phone" [18.397s - 18.766s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "AI and phone";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.397);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.397);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.645999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.766);

  // Caption: "on Earth. By" [18.766s - 19.16s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "on Earth. By";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.766);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.766);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.04);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 19.16);

  // Caption: "2026, leading-edge semiconductor" [19.16s - 20.112s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "2026, leading-edge semiconductor";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 19.16);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 19.16);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.991999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.112);

  // Caption: "chips pack over" [20.112s - 20.49s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "chips pack over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.112);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.112);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 20.369999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.49);

  // Caption: "100 billion transistors" [20.49s - 21.121s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 billion transistors";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.49);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.49);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 21.000999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 21.121);

  // Caption: "onto a silicon" [21.121s - 21.565s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "onto a silicon";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 21.121);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 21.121);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 21.445);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 21.565);

  // Caption: "die smaller than" [21.565s - 21.999s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "die smaller than";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 21.565);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 21.565);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 21.878999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 21.999);

  // Caption: "a postage stamp." [21.999s - 22.5s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a postage stamp.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 21.999);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 21.999);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 22.38);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 22.5);

  // Caption: "Looking forward, The" [22.5s - 23.615s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Looking forward, The";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 22.5);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 22.5);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 23.494999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 23.615);

  // Caption: "History of the" [23.615s - 24.407s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "History of the";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 23.615);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 23.615);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 24.287);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 24.407);

  // Caption: "Transistor continues to" [24.407s - 25.733s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Transistor continues to";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 24.407);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 24.407);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 25.613);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 25.733);

  // Caption: "accelerate innovations across" [25.733s - 27.575s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "accelerate innovations across";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 25.733);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 25.733);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 27.455);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 27.575);

  // Caption: "modern research and" [27.575s - 28.61s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "modern research and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 27.575);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 27.575);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 28.49);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 28.61);

  // Caption: "engineering domains." [28.61s - 30.0s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "engineering domains.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 28.61);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 28.61);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 29.88);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 30.0);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 30.0);
