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
  // Caption: "The Vacuum Tube" [0.0s - 1.015s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Vacuum Tube";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.8949999999999999);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 1.015);

  // Caption: "Bottleneck. Before the" [1.015s - 2.52s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Bottleneck. Before the";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 1.015);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 1.015);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.4);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.52);

  // Caption: "computer in your" [2.52s - 3.663s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "computer in your";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.52);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.52);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 3.5429999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 3.663);

  // Caption: "pocket, early computers" [3.663s - 5.204s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "pocket, early computers";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 3.663);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 3.663);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 5.084);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.204);

  // Caption: "filled entire rooms" [5.204s - 6.455s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "filled entire rooms";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.204);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.204);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.335);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.455);

  // Caption: "with burning hot," [6.455s - 7.416s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "with burning hot,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.455);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.455);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.296);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.416);

  // Caption: "glass vacuum tubes." [7.416s - 8.721s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "glass vacuum tubes.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.416);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.416);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.601);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.721);

  // Caption: "Early vacuum tubes" [8.721s - 10.027s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Early vacuum tubes";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.721);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.721);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.907);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.027);

  // Caption: "consumed large amounts" [10.027s - 11.477s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "consumed large amounts";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.027);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.027);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 11.357000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 11.477);

  // Caption: "of power and" [11.477s - 12.202s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "of power and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 11.477);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 11.477);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 12.082);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.202);

  // Caption: "generated high heat;" [12.202s - 13.544s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "generated high heat;";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.202);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.202);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.424000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.544);

  // Caption: "transistors slashed power" [13.544s - 15.013s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "transistors slashed power";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.544);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.544);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 14.893);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.013);

  // Caption: "consumption by over" [15.013s - 16.264s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "consumption by over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.013);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.013);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 16.144);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 16.264);

  // Caption: "99% and miniaturized" [16.264s - 17.606s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "99% and miniaturized";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 16.264);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 16.264);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 17.486);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.606);

  // Caption: "circuits." [17.606s - 18.349s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "circuits.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.606);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.606);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.229);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.349);

  // Caption: "The Miracle at" [18.349s - 19.259s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Miracle at";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.349);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.349);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.139);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 19.259);

  // Caption: "Bell Labs. On" [19.259s - 20.095s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Bell Labs. On";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 19.259);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 19.259);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.974999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.095);

  // Caption: "two cold days" [20.095s - 20.875s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "two cold days";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.095);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.095);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 20.755);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.875);

  // Caption: "in December 1947," [20.875s - 21.952s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "in December 1947,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.875);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.875);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 21.832);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 21.952);

  // Caption: "three physicists made" [21.952s - 23.308s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "three physicists made";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 21.952);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 21.952);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 23.188);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 23.308);

  // Caption: "history with a" [23.308s - 24.218s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "history with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 23.308);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 23.308);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 24.098);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 24.218);

  // Caption: "sliver of germanium," [24.218s - 25.592s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "sliver of germanium,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 24.218);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 24.218);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 25.471999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 25.592);

  // Caption: "gold foil, and" [25.592s - 26.465s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "gold foil, and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 25.592);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 25.592);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 26.345);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 26.465);

  // Caption: "a paper clip." [26.465s - 27.393s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a paper clip.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 26.465);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 26.465);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 27.273);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 27.393);

  // Caption: "The first working" [27.393s - 28.322s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The first working";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 27.393);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 27.393);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 28.201999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 28.322);

  // Caption: "point-contact transistor was" [28.322s - 29.993s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "point-contact transistor was";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 28.322);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 28.322);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 29.872999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 29.993);

  // Caption: "successfully demonstrated on" [29.993s - 31.795s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "successfully demonstrated on";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 29.993);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 29.993);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 31.675);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 31.795);

  // Caption: "December 23, 1947," [31.795s - 32.965s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "December 23, 1947,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 31.795);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 31.795);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 32.845000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 32.965);

  // Caption: "by John Bardeen" [32.965s - 33.912s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "by John Bardeen";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 32.965);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 32.965);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 33.792);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 33.912);

  // Caption: "and Walter Brattain" [33.912s - 35.101s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and Walter Brattain";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 33.912);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 33.912);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 34.981);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 35.101);

  // Caption: "at Bell Laboratories." [35.101s - 36.698s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "at Bell Laboratories.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 35.101);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 35.101);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 36.578);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 36.698);

  // Caption: "100 Billion Strong." [36.698s - 38.043s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 Billion Strong.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 36.698);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 36.698);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 37.923);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 38.043);

  // Caption: "Today, that single" [38.043s - 39.348s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Today, that single";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 38.043);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 38.043);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 39.228);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 39.348);

  // Caption: "rough prototype has" [39.348s - 40.733s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "rough prototype has";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 39.348);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 39.348);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 40.613);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 40.733);

  // Caption: "scaled to over" [40.733s - 41.717s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "scaled to over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 40.733);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 40.733);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 41.597);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 41.717);

  // Caption: "100 billion microscopic" [41.717s - 43.363s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 billion microscopic";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 41.717);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 41.717);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 43.243);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 43.363);

  // Caption: "switches powering every" [43.363s - 45.009s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "switches powering every";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 43.363);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 43.363);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 44.889);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 45.009);

  // Caption: "AI and phone" [45.009s - 45.912s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "AI and phone";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 45.009);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 45.009);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 45.792);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 45.912);

  // Caption: "on Earth. By" [45.912s - 46.876s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "on Earth. By";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 45.912);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 45.912);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 46.756);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 46.876);

  // Caption: "2026, leading-edge semiconductor" [46.876s - 49.205s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "2026, leading-edge semiconductor";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 46.876);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 46.876);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 49.085);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 49.205);

  // Caption: "chips pack over" [49.205s - 50.128s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "chips pack over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 49.205);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 49.205);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 50.008);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 50.128);

  // Caption: "100 billion transistors" [50.128s - 51.674s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 billion transistors";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 50.128);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 50.128);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 51.554);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 51.674);

  // Caption: "onto a silicon" [51.674s - 52.758s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "onto a silicon";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 51.674);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 51.674);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 52.638000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 52.758);

  // Caption: "die smaller than" [52.758s - 53.822s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "die smaller than";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 52.758);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 52.758);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 53.702000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 53.822);

  // Caption: "a postage stamp." [53.822s - 55.047s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a postage stamp.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 53.822);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 53.822);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 54.927);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 55.047);

  // Caption: "Looking forward, The" [55.047s - 57.775s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Looking forward, The";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 55.047);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 55.047);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 57.655);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 57.775);

  // Caption: "History of the" [57.775s - 59.713s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "History of the";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 57.775);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 57.775);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 59.593);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 59.713);

  // Caption: "Transistor continues to" [59.713s - 62.956s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Transistor continues to";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 59.713);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 59.713);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 62.836000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 62.956);

  // Caption: "accelerate innovations across" [62.956s - 67.464s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "accelerate innovations across";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 62.956);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 62.956);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 67.344);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 67.464);

  // Caption: "modern research and" [67.464s - 69.995s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "modern research and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 67.464);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 67.464);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 69.875);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 69.995);

  // Caption: "engineering domains." [69.995s - 73.396s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "engineering domains.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 69.995);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 69.995);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 73.276);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 73.396);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 30.0);
