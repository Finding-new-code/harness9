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
  // Caption: "The Chef vs." [0.0s - 0.83s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Chef vs.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.71);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 0.83);

  // Caption: "The Assembly Line." [0.83s - 2.181s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Assembly Line.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.83);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.83);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.061);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.181);

  // Caption: "If a CPU" [2.181s - 2.702s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "If a CPU";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.181);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.181);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.582);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.702);

  // Caption: "is a master" [2.702s - 3.435s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "is a master";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.702);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.702);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 3.315);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 3.435);

  // Caption: "chef preparing one" [3.435s - 4.632s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "chef preparing one";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 3.435);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 3.435);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.512);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.632);

  // Caption: "complex dish at" [4.632s - 5.519s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "complex dish at";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.632);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.632);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 5.399);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.519);

  // Caption: "lighting speed, a" [5.519s - 6.639s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "lighting speed, a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.519);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.519);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.519);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.639);

  // Caption: "GPU is a" [6.639s - 7.16s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "GPU is a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.639);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.639);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.04);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.16);

  // Caption: "factory of ten" [7.16s - 8.105s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "factory of ten";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.16);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.16);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.985);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.105);

  // Caption: "thousand cooks chopping" [8.105s - 9.591s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "thousand cooks chopping";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.105);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.105);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.471);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.591);

  // Caption: "vegetables at once." [9.591s - 11.077s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "vegetables at once.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.591);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.591);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.957);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 11.077);

  // Caption: "A central processing" [11.077s - 12.351s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "A central processing";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 11.077);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 11.077);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 12.231000000000002);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.351);

  // Caption: "unit (CPU) typically" [12.351s - 13.644s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "unit (CPU) typically";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.351);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.351);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.524000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.644);

  // Caption: "possesses between 8" [13.644s - 14.975s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "possesses between 8";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.644);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.644);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 14.855);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 14.975);

  // Caption: "and 64 high-speed" [14.975s - 15.998s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and 64 high-speed";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 14.975);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 14.975);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 15.878);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.998);

  // Caption: "cores designed for" [15.998s - 17.195s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "cores designed for";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.998);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.998);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 17.075);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.195);

  // Caption: "complex branching logic" [17.195s - 18.584s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "complex branching logic";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.195);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.195);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.464);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.584);

  // Caption: "and low latency." [18.584s - 19.761s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and low latency.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.584);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.584);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.641);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 19.761);

  // Caption: "The Power of" [19.761s - 20.521s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Power of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 19.761);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 19.761);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 20.401);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.521);

  // Caption: "SIMD Parallelism. Originally" [20.521s - 22.611s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "SIMD Parallelism. Originally";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.521);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.521);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 22.491);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 22.611);

  // Caption: "designed to render" [22.611s - 23.789s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "designed to render";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 22.611);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 22.611);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 23.669);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 23.789);

  // Caption: "3D video game" [23.789s - 24.777s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "3D video game";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 23.789);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 23.789);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 24.657);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 24.777);

  // Caption: "polygons, GPUs process" [24.777s - 26.165s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "polygons, GPUs process";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 24.777);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 24.777);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 26.044999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 26.165);

  // Caption: "massive arrays of" [26.165s - 27.4s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "massive arrays of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 26.165);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 26.165);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 27.279999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 27.4);

  // Caption: "pixels with a" [27.4s - 28.198s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "pixels with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 27.4);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 27.4);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 28.078);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 28.198);

  // Caption: "single broadcast instruction." [28.198s - 30.231s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "single broadcast instruction.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 28.198);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 28.198);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 30.111);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 30.231);

  // Caption: "Modern flagship GPUs" [30.231s - 31.39s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Modern flagship GPUs";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 30.231);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 30.231);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 31.27);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 31.39);

  // Caption: "feature over 16,000" [31.39s - 32.663s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "feature over 16,000";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 31.39);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 31.39);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 32.543);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 32.663);

  // Caption: "arithmetic logic units" [32.663s - 34.183s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "arithmetic logic units";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 32.663);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 32.663);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 34.063);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 34.183);

  // Caption: "(ALUs) executing parallel" [34.183s - 35.836s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "(ALUs) executing parallel";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 34.183);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 34.183);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 35.716);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 35.836);

  // Caption: "mathematical operations across" [35.836s - 38.04s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "mathematical operations across";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 35.836);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 35.836);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 37.92);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 38.04);

  // Caption: "high-bandwidth memory." [38.04s - 39.522s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "high-bandwidth memory.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 38.04);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 38.04);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 39.402);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 39.522);

  // Caption: "Fueling the AI" [39.522s - 40.45s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Fueling the AI";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 39.522);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 39.522);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 40.330000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 40.45);

  // Caption: "Revolution. Because artificial" [40.45s - 42.753s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Revolution. Because artificial";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 40.45);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 40.45);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 42.633);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 42.753);

  // Caption: "intelligence calculations are" [42.753s - 44.712s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "intelligence calculations are";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 42.753);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 42.753);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 44.592000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 44.712);

  // Caption: "essentially giant matrix" [44.712s - 46.241s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "essentially giant matrix";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 44.712);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 44.712);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 46.121);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 46.241);

  // Caption: "multiplications, GPUs became" [46.241s - 48.045s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "multiplications, GPUs became";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 46.241);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 46.241);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 47.925000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 48.045);

  // Caption: "the turbo-engine of" [48.045s - 49.197s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "the turbo-engine of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 48.045);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 48.045);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 49.077000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 49.197);

  // Caption: "modern deep learning." [49.197s - 50.589s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "modern deep learning.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 49.197);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 49.197);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 50.469);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 50.589);

  // Caption: "Matrix multiplication in" [50.589s - 52.118s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Matrix multiplication in";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 50.589);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 50.589);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 51.998000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 52.118);

  // Caption: "neural networks maps" [52.118s - 53.252s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "neural networks maps";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 52.118);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 52.118);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 53.132000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 53.252);

  // Caption: "directly to GPU" [53.252s - 54.128s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "directly to GPU";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 53.252);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 53.252);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 54.008);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 54.128);

  // Caption: "tensor architectures, enabling" [54.128s - 56.001s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "tensor architectures, enabling";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 54.128);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 54.128);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 55.881);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 56.001);

  // Caption: "trillion-parameter AI models" [56.001s - 57.806s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "trillion-parameter AI models";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 56.001);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 56.001);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 57.686);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 57.806);

  // Caption: "to train efficiently." [57.806s - 59.284s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "to train efficiently.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 57.806);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 57.806);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 59.164);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 59.284);

  // Caption: "Looking forward, How" [59.284s - 62.154s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Looking forward, How";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 59.284);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 59.284);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 62.034000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 62.154);

  // Caption: "GPUs Work: Parallel" [62.154s - 64.733s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "GPUs Work: Parallel";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 62.154);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 62.154);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 64.613);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 64.733);

  // Caption: "Computing continues to" [64.733s - 68.062s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Computing continues to";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 64.733);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 64.733);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 67.942);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 68.062);

  // Caption: "accelerate innovations across" [68.062s - 72.804s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "accelerate innovations across";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 68.062);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 68.062);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 72.684);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 72.804);

  // Caption: "modern research and" [72.804s - 75.467s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "modern research and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 72.804);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 72.804);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 75.347);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 75.467);

  // Caption: "engineering domains." [75.467s - 79.045s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "engineering domains.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 75.467);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 75.467);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 78.925);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 79.045);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 10.0);
