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
  // Scene 1: scene_1 (t=0.0s to 3.75s)
  tl.set("#scene_1", { autoAlpha: 1 }, 0.0);
  tl.from("#scene_1 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 0.0);
  tl.from("#scene_1 .hero-image", {
    scale: 1.15,
    duration: 3.75,
    ease: "none"
  }, 0.0);
  tl.set("#scene_1", { autoAlpha: 0 }, 3.75);

  // Scene 2: scene_2 (t=3.75s to 7.5s)
  tl.set("#scene_2", { autoAlpha: 1 }, 3.75);
  tl.from("#scene_2 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 3.75);
  tl.from("#scene_2 .hero-image", {
    scale: 1.15,
    duration: 3.75,
    ease: "none"
  }, 3.75);
  tl.set("#scene_2", { autoAlpha: 0 }, 7.5);

  // Scene 3: scene_3 (t=7.5s to 11.25s)
  tl.set("#scene_3", { autoAlpha: 1 }, 7.5);
  tl.from("#scene_3 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 7.5);
  tl.from("#scene_3 .hero-image", {
    scale: 1.15,
    duration: 3.75,
    ease: "none"
  }, 7.5);
  tl.set("#scene_3", { autoAlpha: 0 }, 11.25);

  // Scene 4: scene_4 (t=11.25s to 15.0s)
  tl.set("#scene_4", { autoAlpha: 1 }, 11.25);
  tl.from("#scene_4 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 11.25);
  tl.from("#scene_4 .hero-image", {
    scale: 1.15,
    duration: 3.75,
    ease: "none"
  }, 11.25);
  tl.to("#scene_4", { opacity: 0, duration: 0.5, ease: "power2.in" }, 14.5);

// 4. Kinetic Captions Alignment (with Hard Kill Guarantee)
  // Caption: "The Genesis of" [0.0s - 0.769s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Genesis of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.649);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 0.769);

  // Caption: "The Quantum Hall" [0.769s - 1.601s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Quantum Hall";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.769);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.769);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 1.4809999999999999);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 1.601);

  // Caption: "Effect. Every great" [1.601s - 2.809s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Effect. Every great";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 1.601);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 1.601);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.689);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.809);

  // Caption: "technological revolution starts" [2.809s - 4.583s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "technological revolution starts";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.809);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.809);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.463);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.583);

  // Caption: "with a challenge." [4.583s - 5.571s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "with a challenge.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.583);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.583);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 5.451);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.571);

  // Caption: "For The Quantum" [5.571s - 6.372s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "For The Quantum";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.571);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.571);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.252);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.372);

  // Caption: "Hall Effect, it" [6.372s - 7.141s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Hall Effect, it";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.372);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.372);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.021);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.141);

  // Caption: "began with a" [7.141s - 7.768s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "began with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.141);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.141);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.648);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.768);

  // Caption: "daring new approach." [7.768s - 8.93s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "daring new approach.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.768);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.768);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.81);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.93);

  // Caption: "The foundational principles" [8.93s - 10.499s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The foundational principles";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.93);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.93);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.379000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.499);

  // Caption: "of The Quantum" [10.499s - 11.268s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "of The Quantum";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.499);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.499);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 11.148000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 11.268);

  // Caption: "Hall Effect were" [11.268s - 12.1s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Hall Effect were";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 11.268);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 11.268);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 11.98);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.1);

  // Caption: "established through seminal" [12.1s - 13.591s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "established through seminal";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.1);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.1);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.471);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.591);

  // Caption: "experimental breakthroughs and" [13.591s - 15.254s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "experimental breakthroughs and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.591);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.591);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 15.134);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.254);

  // Caption: "early theoretical formulations." [15.254s - 17.31s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "early theoretical formulations.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.254);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.254);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 17.189999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.31);

  // Caption: "The Architecture of" [17.31s - 18.444s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Architecture of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.31);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.31);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.323999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.444);

  // Caption: "The Quantum Hall" [18.444s - 19.316s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Quantum Hall";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.444);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.444);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.195999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 19.316);

  // Caption: "Effect. Behind its" [19.316s - 20.384s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Effect. Behind its";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 19.316);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 19.316);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 20.264);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.384);

  // Caption: "outward simplicity lies" [20.384s - 21.814s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "outward simplicity lies";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.384);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.384);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 21.694);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 21.814);

  // Caption: "an intricate system" [21.814s - 22.949s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "an intricate system";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 21.814);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 21.814);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 22.829);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 22.949);

  // Caption: "designed for precision," [22.949s - 24.346s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "designed for precision,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 22.949);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 22.949);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 24.226);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 24.346);

  // Caption: "speed, and continuous" [24.346s - 25.678s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "speed, and continuous";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 24.346);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 24.346);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 25.558);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 25.678);

  // Caption: "scaling. At its" [25.678s - 26.565s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "scaling. At its";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 25.678);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 25.678);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 26.445);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 26.565);

  // Caption: "functional core, The" [26.565s - 27.782s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "functional core, The";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 26.565);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 26.565);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 27.662);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 27.782);

  // Caption: "Quantum Hall Effect" [27.782s - 28.834s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Quantum Hall Effect";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 27.782);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 27.782);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 28.714);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 28.834);

  // Caption: "operates by transforming" [28.834s - 30.215s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "operates by transforming";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 28.834);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 28.834);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 30.095);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 30.215);

  // Caption: "input energy or" [30.215s - 31.135s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "input energy or";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 30.215);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 30.215);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 31.015);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 31.135);

  // Caption: "signals through structured" [31.135s - 32.5s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "signals through structured";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 31.135);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 31.135);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 32.38);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 32.5);

  // Caption: "physical and algorithmic" [32.5s - 33.881s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "physical and algorithmic";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 32.5);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 32.5);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 33.761);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 33.881);

  // Caption: "mechanisms." [33.881s - 34.62s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "mechanisms.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 33.881);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 33.881);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 34.5);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 34.62);

  // Caption: "Transforming the Modern" [34.62s - 35.817s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Transforming the Modern";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 34.62);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 34.62);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 35.697);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 35.817);

  // Caption: "World. Today, The" [35.817s - 36.913s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "World. Today, The";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 35.817);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 35.817);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 36.793);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 36.913);

  // Caption: "Quantum Hall Effect" [36.913s - 37.976s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Quantum Hall Effect";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 36.913);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 36.913);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 37.856);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 37.976);

  // Caption: "quietly powers the" [37.976s - 39.089s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "quietly powers the";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 37.976);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 37.976);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 38.969);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 39.089);

  // Caption: "systems we rely" [39.089s - 39.936s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "systems we rely";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 39.089);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 39.089);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 39.816);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 39.936);

  // Caption: "on daily, laying" [39.936s - 41.033s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "on daily, laying";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 39.936);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 39.936);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 40.913000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 41.033);

  // Caption: "the groundwork for" [41.033s - 41.98s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "the groundwork for";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 41.033);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 41.033);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 41.86);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 41.98);

  // Caption: "tomorrow's breakthroughs. Today," [41.98s - 43.957s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "tomorrow's breakthroughs. Today,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 41.98);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 41.98);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 43.837);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 43.957);

  // Caption: "The Quantum Hall" [43.957s - 44.837s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Quantum Hall";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 43.957);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 43.957);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 44.717000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 44.837);

  // Caption: "Effect serves as" [44.837s - 45.718s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Effect serves as";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 44.837);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 44.837);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 45.598000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 45.718);

  // Caption: "a critical technological" [45.718s - 47.196s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a critical technological";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 45.718);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 45.718);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 47.076);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 47.196);

  // Caption: "pillar across modern" [47.196s - 48.292s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "pillar across modern";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 47.196);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 47.196);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 48.172000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 48.292);

  // Caption: "computing, manufacturing, and" [48.292s - 50.037s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "computing, manufacturing, and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 48.292);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 48.292);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 49.917);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 50.037);

  // Caption: "global digital infrastructure." [50.037s - 51.931s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "global digital infrastructure.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 50.037);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 50.037);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 51.811);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 51.931);

  // Caption: "Looking forward, The" [51.931s - 54.621s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Looking forward, The";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 51.931);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 51.931);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 54.501000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 54.621);

  // Caption: "Quantum Hall Effect" [54.621s - 57.116s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Quantum Hall Effect";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 54.621);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 54.621);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 56.996);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 57.116);

  // Caption: "continues to accelerate" [57.116s - 60.703s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "continues to accelerate";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 57.116);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 57.116);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 60.583000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 60.703);

  // Caption: "innovations across modern" [60.703s - 64.25s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "innovations across modern";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 60.703);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 60.703);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 64.13);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 64.25);

  // Caption: "research and engineering" [64.25s - 67.72s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "research and engineering";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 64.25);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 64.25);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 67.6);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 67.72);

  // Caption: "domains." [67.72s - 69.241s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "domains.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 67.72);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 67.72);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 69.121);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 69.241);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 15.0);
