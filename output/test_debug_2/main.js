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
  // Scene 1: scene_1 (t=0.0s to 0.22s)
  tl.set("#scene_1", { autoAlpha: 1 }, 0.0);
  tl.from("#scene_1 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 0.0);
  tl.from("#scene_1 .hero-image", {
    scale: 1.15,
    duration: 0.22,
    ease: "none"
  }, 0.0);
  tl.set("#scene_1", { autoAlpha: 0 }, 0.22);

  // Scene 2: scene_2 (t=0.22s to 0.66s)
  tl.set("#scene_2", { autoAlpha: 1 }, 0.22);
  tl.from("#scene_2 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 0.22);
  tl.from("#scene_2 .hero-image", {
    scale: 1.15,
    duration: 0.44,
    ease: "none"
  }, 0.22);
  tl.set("#scene_2", { autoAlpha: 0 }, 0.66);

  // Scene 3: scene_3 (t=0.66s to 0.99s)
  tl.set("#scene_3", { autoAlpha: 1 }, 0.66);
  tl.from("#scene_3 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 0.66);
  tl.from("#scene_3 .hero-image", {
    scale: 1.15,
    duration: 0.33,
    ease: "none"
  }, 0.66);
  tl.to("#scene_3", { opacity: 0, duration: 0.5, ease: "power2.in" }, 0.49);

// 4. Kinetic Captions Alignment (with Hard Kill Guarantee)
  // Caption: "The Vacuum Tube" [0.0s - 0.8s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Vacuum Tube";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.68);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 0.8);

  // Caption: "Bottleneck. Before the" [0.8s - 1.986s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Bottleneck. Before the";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.8);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.8);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 1.866);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 1.986);

  // Caption: "computer in your" [1.986s - 2.886s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "computer in your";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 1.986);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 1.986);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.766);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.886);

  // Caption: "pocket, early computers" [2.886s - 4.101s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "pocket, early computers";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.886);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.886);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 3.981);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.101);

  // Caption: "filled entire rooms" [4.101s - 5.087s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "filled entire rooms";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.101);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.101);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.967);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.087);

  // Caption: "with burning hot," [5.087s - 5.844s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "with burning hot,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.087);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.087);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 5.724);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.844);

  // Caption: "glass vacuum tubes." [5.844s - 6.872s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "glass vacuum tubes.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.844);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.844);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.752);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.872);

  // Caption: "Early vacuum tubes" [6.872s - 7.901s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Early vacuum tubes";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.872);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.872);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.781);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.901);

  // Caption: "consumed large amounts" [7.901s - 9.044s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "consumed large amounts";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.901);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.901);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.924000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.044);

  // Caption: "of power and" [9.044s - 9.616s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "of power and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.044);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.044);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.496);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.616);

  // Caption: "generated high heat;" [9.616s - 10.673s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "generated high heat;";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.616);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.616);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.553);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.673);

  // Caption: "transistors slashed power" [10.673s - 11.83s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "transistors slashed power";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.673);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.673);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 11.71);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 11.83);

  // Caption: "consumption by over" [11.83s - 12.816s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "consumption by over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 11.83);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 11.83);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 12.696000000000002);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.816);

  // Caption: "99% and miniaturized" [12.816s - 13.874s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "99% and miniaturized";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.816);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.816);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.754000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.874);

  // Caption: "circuits." [13.874s - 14.459s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "circuits.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.874);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.874);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 14.339);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 14.459);

  // Caption: "The Miracle at" [14.459s - 15.894s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Miracle at";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 14.459);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 14.459);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 15.774000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.894);

  // Caption: "Bell Labs. On" [15.894s - 17.211s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Bell Labs. On";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.894);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.894);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 17.090999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.211);

  // Caption: "two cold days" [17.211s - 18.44s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "two cold days";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.211);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.211);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.32);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.44);

  // Caption: "in December 1947," [18.44s - 20.138s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "in December 1947,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.44);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.44);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 20.018);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.138);

  // Caption: "three physicists made" [20.138s - 22.274s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "three physicists made";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.138);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.138);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 22.154);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 22.274);

  // Caption: "history with a" [22.274s - 23.709s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "history with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 22.274);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 22.274);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 23.589);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 23.709);

  // Caption: "sliver of germanium," [23.709s - 25.875s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "sliver of germanium,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 23.709);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 23.709);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 25.755);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 25.875);

  // Caption: "gold foil, and" [25.875s - 27.25s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "gold foil, and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 25.875);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 25.875);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 27.13);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 27.25);

  // Caption: "a paper clip." [27.25s - 28.714s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a paper clip.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 27.25);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 27.25);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 28.593999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 28.714);

  // Caption: "The first working" [28.714s - 30.177s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The first working";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 28.714);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 28.714);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 30.057);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 30.177);

  // Caption: "point-contact transistor was" [30.177s - 32.812s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "point-contact transistor was";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 30.177);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 30.177);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 32.692);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 32.812);

  // Caption: "successfully demonstrated on" [32.812s - 35.651s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "successfully demonstrated on";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 32.812);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 32.812);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 35.531000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 35.651);

  // Caption: "December 23, 1947," [35.651s - 37.495s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "December 23, 1947,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 35.651);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 35.651);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 37.375);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 37.495);

  // Caption: "by John Bardeen" [37.495s - 38.988s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "by John Bardeen";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 37.495);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 37.495);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 38.868);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 38.988);

  // Caption: "and Walter Brattain" [38.988s - 40.861s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and Walter Brattain";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 38.988);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 38.988);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 40.741);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 40.861);

  // Caption: "at Bell Laboratories." [40.861s - 43.378s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "at Bell Laboratories.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 40.861);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 40.861);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 43.258);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 43.378);

  // Caption: "100 Billion Strong." [43.378s - 44.968s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 Billion Strong.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 43.378);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 43.378);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 44.848000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 44.968);

  // Caption: "Today, that single" [44.968s - 46.511s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Today, that single";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 44.968);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 44.968);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 46.391000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 46.511);

  // Caption: "rough prototype has" [46.511s - 48.148s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "rough prototype has";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 46.511);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 46.511);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 48.028000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 48.148);

  // Caption: "scaled to over" [48.148s - 49.311s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "scaled to over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 48.148);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 48.148);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 49.191);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 49.311);

  // Caption: "100 billion microscopic" [49.311s - 51.256s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 billion microscopic";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 49.311);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 49.311);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 51.136);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 51.256);

  // Caption: "switches powering every" [51.256s - 53.202s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "switches powering every";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 51.256);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 51.256);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 53.082);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 53.202);

  // Caption: "AI and phone" [53.202s - 54.27s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "AI and phone";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 53.202);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 53.202);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 54.150000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 54.27);

  // Caption: "on Earth. By" [54.27s - 55.409s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "on Earth. By";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 54.27);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 54.27);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 55.289);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 55.409);

  // Caption: "2026, leading-edge semiconductor" [55.409s - 58.162s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "2026, leading-edge semiconductor";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 55.409);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 55.409);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 58.042);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 58.162);

  // Caption: "chips pack over" [58.162s - 59.253s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "chips pack over";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 58.162);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 58.162);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 59.133);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 59.253);

  // Caption: "100 billion transistors" [59.253s - 61.081s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "100 billion transistors";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 59.253);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 59.253);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 60.961000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 61.081);

  // Caption: "onto a silicon" [61.081s - 62.362s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "onto a silicon";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 61.081);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 61.081);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 62.242000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 62.362);

  // Caption: "die smaller than" [62.362s - 63.62s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "die smaller than";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 62.362);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 62.362);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 63.5);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 63.62);

  // Caption: "a postage stamp." [63.62s - 65.067s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a postage stamp.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 63.62);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 63.62);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 64.94699999999999);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 65.067);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 1.0);
