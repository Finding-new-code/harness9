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
  // Scene 1: scene_1 (t=0.0s to 2.5s)
  tl.set("#scene_1", { autoAlpha: 1 }, 0.0);
  tl.from("#scene_1 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 0.0);
  tl.from("#scene_1 .hero-image", {
    scale: 1.15,
    duration: 2.5,
    ease: "none"
  }, 0.0);
  tl.set("#scene_1", { autoAlpha: 0 }, 2.5);

  // Scene 2: scene_2 (t=2.5s to 5.0s)
  tl.set("#scene_2", { autoAlpha: 1 }, 2.5);
  tl.from("#scene_2 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 2.5);
  tl.from("#scene_2 .hero-image", {
    scale: 1.15,
    duration: 2.5,
    ease: "none"
  }, 2.5);
  tl.set("#scene_2", { autoAlpha: 0 }, 5.0);

  // Scene 3: scene_3 (t=5.0s to 7.5s)
  tl.set("#scene_3", { autoAlpha: 1 }, 5.0);
  tl.from("#scene_3 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 5.0);
  tl.from("#scene_3 .hero-image", {
    scale: 1.15,
    duration: 2.5,
    ease: "none"
  }, 5.0);
  tl.set("#scene_3", { autoAlpha: 0 }, 7.5);

  // Scene 4: scene_4 (t=7.5s to 10.0s)
  tl.set("#scene_4", { autoAlpha: 1 }, 7.5);
  tl.from("#scene_4 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 7.5);
  tl.from("#scene_4 .hero-image", {
    scale: 1.15,
    duration: 2.5,
    ease: "none"
  }, 7.5);
  tl.to("#scene_4", { opacity: 0, duration: 0.5, ease: "power2.in" }, 9.5);

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

  // Caption: "CRISPR-Cas9 Precision Molecular" [0.769s - 2.434s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "CRISPR-Cas9 Precision Molecular";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.769);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.769);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.314);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.434);

  // Caption: "Scissors. Every great" [2.434s - 3.705s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Scissors. Every great";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.434);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.434);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 3.585);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 3.705);

  // Caption: "technological revolution starts" [3.705s - 5.479s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "technological revolution starts";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 3.705);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 3.705);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 5.359);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.479);

  // Caption: "with a challenge." [5.479s - 6.468s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "with a challenge.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.479);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.479);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.348);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.468);

  // Caption: "For CRISPR-Cas9 Precision" [6.468s - 7.709s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "For CRISPR-Cas9 Precision";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.468);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.468);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.5889999999999995);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.709);

  // Caption: "Molecular Scissors, it" [7.709s - 8.933s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Molecular Scissors, it";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.709);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.709);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.813);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.933);

  // Caption: "began with a" [8.933s - 9.561s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "began with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.933);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.933);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.441);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.561);

  // Caption: "daring new approach." [9.561s - 10.723s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "daring new approach.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.561);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.561);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.603000000000002);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.723);

  // Caption: "The foundational principles" [10.723s - 12.293s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The foundational principles";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.723);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.723);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 12.173);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.293);

  // Caption: "of CRISPR-Cas9 Precision" [12.293s - 13.502s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "of CRISPR-Cas9 Precision";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.293);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.293);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.382000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.502);

  // Caption: "Molecular Scissors were" [13.502s - 14.79s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Molecular Scissors were";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.502);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.502);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 14.67);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 14.79);

  // Caption: "established through seminal" [14.79s - 16.281s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "established through seminal";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 14.79);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 14.79);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 16.160999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 16.281);

  // Caption: "experimental breakthroughs and" [16.281s - 17.945s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "experimental breakthroughs and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 16.281);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 16.281);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 17.825);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.945);

  // Caption: "early theoretical formulations." [17.945s - 20.002s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "early theoretical formulations.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.945);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.945);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.881999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.002);

  // Caption: "The Architecture of" [20.002s - 21.185s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Architecture of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.002);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.002);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 21.064999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 21.185);

  // Caption: "CRISPR-Cas9 Precision Molecular" [21.185s - 23.001s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "CRISPR-Cas9 Precision Molecular";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 21.185);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 21.185);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 22.881);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 23.001);

  // Caption: "Scissors. Behind its" [23.001s - 24.184s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Scissors. Behind its";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 23.001);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 23.001);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 24.064);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 24.184);

  // Caption: "outward simplicity lies" [24.184s - 25.675s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "outward simplicity lies";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 24.184);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 24.184);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 25.555);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 25.675);

  // Caption: "an intricate system" [25.675s - 26.858s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "an intricate system";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 25.675);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 25.675);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 26.738);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 26.858);

  // Caption: "designed for precision," [26.858s - 28.315s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "designed for precision,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 26.858);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 26.858);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 28.195);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 28.315);

  // Caption: "speed, and continuous" [28.315s - 29.703s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "speed, and continuous";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 28.315);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 28.315);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 29.583);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 29.703);

  // Caption: "scaling. At its" [29.703s - 30.629s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "scaling. At its";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 29.703);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 29.703);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 30.509);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 30.629);

  // Caption: "functional core, CRISPR-Cas9" [30.629s - 32.223s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "functional core, CRISPR-Cas9";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 30.629);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 30.629);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 32.103);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 32.223);

  // Caption: "Precision Molecular Scissors" [32.223s - 33.971s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Precision Molecular Scissors";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 32.223);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 32.223);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 33.851);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 33.971);

  // Caption: "operates by transforming" [33.971s - 35.411s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "operates by transforming";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 33.971);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 33.971);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 35.291000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 35.411);

  // Caption: "input energy or" [35.411s - 36.37s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "input energy or";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 35.411);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 35.411);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 36.25);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 36.37);

  // Caption: "signals through structured" [36.37s - 37.793s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "signals through structured";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 36.37);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 36.37);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 37.673);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 37.793);

  // Caption: "physical and algorithmic" [37.793s - 39.233s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "physical and algorithmic";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 37.793);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 37.793);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 39.113);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 39.233);

  // Caption: "mechanisms." [39.233s - 40.004s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "mechanisms.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 39.233);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 39.233);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 39.884);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 40.004);

  // Caption: "Transforming the Modern" [40.004s - 41.25s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Transforming the Modern";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 40.004);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 40.004);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 41.13);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 41.25);

  // Caption: "World. Today, CRISPR-Cas9" [41.25s - 42.721s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "World. Today, CRISPR-Cas9";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 41.25);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 41.25);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 42.601);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 42.721);

  // Caption: "Precision Molecular Scissors" [42.721s - 44.486s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Precision Molecular Scissors";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 42.721);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 42.721);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 44.366);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 44.486);

  // Caption: "quietly powers the" [44.486s - 45.645s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "quietly powers the";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 44.486);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 44.486);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 45.525000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 45.645);

  // Caption: "systems we rely" [45.645s - 46.527s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "systems we rely";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 45.645);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 45.645);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 46.407000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 46.527);

  // Caption: "on daily, laying" [46.527s - 47.669s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "on daily, laying";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 46.527);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 46.527);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 47.549);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 47.669);

  // Caption: "the groundwork for" [47.669s - 48.655s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "the groundwork for";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 47.669);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 47.669);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 48.535000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 48.655);

  // Caption: "tomorrow's breakthroughs. Today," [48.655s - 50.715s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "tomorrow's breakthroughs. Today,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 48.655);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 48.655);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 50.595000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 50.715);

  // Caption: "CRISPR-Cas9 Precision Molecular" [50.715s - 52.549s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "CRISPR-Cas9 Precision Molecular";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 50.715);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 50.715);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 52.429);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 52.549);

  // Caption: "Scissors serves as" [52.549s - 53.535s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Scissors serves as";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 52.549);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 52.549);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 53.415);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 53.535);

  // Caption: "a critical technological" [53.535s - 55.075s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "a critical technological";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 53.535);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 53.535);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 54.955000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 55.075);

  // Caption: "pillar across modern" [55.075s - 56.217s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "pillar across modern";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 55.075);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 55.075);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 56.097);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 56.217);

  // Caption: "computing, manufacturing, and" [56.217s - 58.034s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "computing, manufacturing, and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 56.217);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 56.217);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 57.914);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 58.034);

  // Caption: "global digital infrastructure." [58.034s - 60.006s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "global digital infrastructure.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 58.034);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 58.034);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 59.886);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 60.006);

  // Caption: "Looking forward, CRISPR-Cas9" [60.006s - 63.519s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Looking forward, CRISPR-Cas9";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 60.006);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 60.006);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 63.399);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 63.519);

  // Caption: "Precision Molecular Scissors" [63.519s - 67.592s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Precision Molecular Scissors";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 63.519);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 63.519);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 67.472);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 67.592);

  // Caption: "continues to accelerate" [67.592s - 71.265s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "continues to accelerate";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 67.592);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 67.592);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 71.145);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 71.265);

  // Caption: "innovations across modern" [71.265s - 74.898s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "innovations across modern";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 71.265);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 71.265);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 74.77799999999999);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 74.898);

  // Caption: "research and engineering" [74.898s - 78.451s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "research and engineering";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 74.898);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 74.898);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 78.33099999999999);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 78.451);

  // Caption: "domains." [78.451s - 80.008s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "domains.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 78.451);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 78.451);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 79.88799999999999);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 80.008);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 10.0);
