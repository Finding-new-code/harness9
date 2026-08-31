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
  // Scene 1: scene_1 (t=0.0s to 1.25s)
  tl.set("#scene_1", { autoAlpha: 1 }, 0.0);
  tl.from("#scene_1 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 0.0);
  tl.from("#scene_1 .hero-image", {
    scale: 1.15,
    duration: 1.25,
    ease: "none"
  }, 0.0);
  tl.set("#scene_1", { autoAlpha: 0 }, 1.25);

  // Scene 2: scene_2 (t=1.25s to 2.5s)
  tl.set("#scene_2", { autoAlpha: 1 }, 1.25);
  tl.from("#scene_2 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 1.25);
  tl.from("#scene_2 .hero-image", {
    scale: 1.15,
    duration: 1.25,
    ease: "none"
  }, 1.25);
  tl.set("#scene_2", { autoAlpha: 0 }, 2.5);

  // Scene 3: scene_3 (t=2.5s to 3.75s)
  tl.set("#scene_3", { autoAlpha: 1 }, 2.5);
  tl.from("#scene_3 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 2.5);
  tl.from("#scene_3 .hero-image", {
    scale: 1.15,
    duration: 1.25,
    ease: "none"
  }, 2.5);
  tl.set("#scene_3", { autoAlpha: 0 }, 3.75);

  // Scene 4: scene_4 (t=3.75s to 5.0s)
  tl.set("#scene_4", { autoAlpha: 1 }, 3.75);
  tl.from("#scene_4 .scene-content", {
    y: 60,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  }, 3.75);
  tl.from("#scene_4 .hero-image", {
    scale: 1.15,
    duration: 1.25,
    ease: "none"
  }, 3.75);
  tl.to("#scene_4", { opacity: 0, duration: 0.5, ease: "power2.in" }, 4.5);

// 4. Kinetic Captions Alignment (with Hard Kill Guarantee)
  // Caption: "The Chef vs." [0.0s - 0.813s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Chef vs.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.693);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 0.813);

  // Caption: "The Assembly Line." [0.813s - 2.136s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Assembly Line.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.813);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.813);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.016);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.136);

  // Caption: "If a CPU" [2.136s - 2.646s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "If a CPU";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.136);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.136);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.526);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.646);

  // Caption: "is a master" [2.646s - 3.364s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "is a master";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.646);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.646);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 3.2439999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 3.364);

  // Caption: "chef preparing one" [3.364s - 4.536s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "chef preparing one";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 3.364);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 3.364);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.4159999999999995);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.536);

  // Caption: "complex dish at" [4.536s - 5.406s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "complex dish at";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.536);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.536);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 5.286);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.406);

  // Caption: "lighting speed, a" [5.406s - 6.502s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "lighting speed, a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.406);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.406);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.382);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.502);

  // Caption: "GPU is a" [6.502s - 7.012s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "GPU is a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.502);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.502);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.8919999999999995);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.012);

  // Caption: "factory of ten" [7.012s - 7.939s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "factory of ten";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.012);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.012);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.819);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.939);

  // Caption: "thousand cooks chopping" [7.939s - 9.394s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "thousand cooks chopping";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.939);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.939);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.274000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.394);

  // Caption: "vegetables at once." [9.394s - 10.849s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "vegetables at once.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.394);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.394);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.729000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.849);

  // Caption: "A central processing" [10.849s - 12.097s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "A central processing";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.849);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.849);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 11.977);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.097);

  // Caption: "unit (CPU) typically" [12.097s - 13.363s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "unit (CPU) typically";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.097);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.097);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.243);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.363);

  // Caption: "possesses between 8" [13.363s - 14.667s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "possesses between 8";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.363);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.363);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 14.547);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 14.667);

  // Caption: "and 64 high-speed" [14.667s - 15.669s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and 64 high-speed";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 14.667);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 14.667);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 15.549000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.669);

  // Caption: "cores designed for" [15.669s - 16.841s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "cores designed for";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.669);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.669);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 16.721);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 16.841);

  // Caption: "complex branching logic" [16.841s - 18.202s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "complex branching logic";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 16.841);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 16.841);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.082);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.202);

  // Caption: "and low latency." [18.202s - 19.355s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and low latency.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.202);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.202);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.235);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 19.355);

  // Caption: "The Power of" [19.355s - 20.099s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Power of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 19.355);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 19.355);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 19.979);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.099);

  // Caption: "SIMD Parallelism. Originally" [20.099s - 22.147s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "SIMD Parallelism. Originally";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.099);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.099);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 22.026999999999997);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 22.147);

  // Caption: "designed to render" [22.147s - 23.3s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "designed to render";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 22.147);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 22.147);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 23.18);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 23.3);

  // Caption: "3D video game" [23.3s - 24.268s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "3D video game";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 23.3);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 23.3);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 24.148);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 24.268);

  // Caption: "polygons, GPUs process" [24.268s - 25.627s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "polygons, GPUs process";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 24.268);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 24.268);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 25.506999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 25.627);

  // Caption: "massive arrays of" [25.627s - 26.836s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "massive arrays of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 25.627);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 25.627);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 26.715999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 26.836);

  // Caption: "pixels with a" [26.836s - 27.618s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "pixels with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 26.836);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 26.836);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 27.497999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 27.618);

  // Caption: "single broadcast instruction." [27.618s - 29.609s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "single broadcast instruction.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 27.618);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 27.618);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 29.489);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 29.609);

  // Caption: "Modern flagship GPUs" [29.609s - 30.745s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Modern flagship GPUs";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 29.609);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 29.609);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 30.625);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 30.745);

  // Caption: "feature over 16,000" [30.745s - 31.992s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "feature over 16,000";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 30.745);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 30.745);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 31.872);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 31.992);

  // Caption: "arithmetic logic units" [31.992s - 33.48s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "arithmetic logic units";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 31.992);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 31.992);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 33.36);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 33.48);

  // Caption: "(ALUs) executing parallel" [33.48s - 35.099s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "(ALUs) executing parallel";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 33.48);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 33.48);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 34.979);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 35.099);

  // Caption: "mathematical operations across" [35.099s - 37.258s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "mathematical operations across";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 35.099);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 35.099);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 37.138000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 37.258);

  // Caption: "high-bandwidth memory." [37.258s - 38.71s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "high-bandwidth memory.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 37.258);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 37.258);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 38.59);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 38.71);

  // Caption: "Fueling the AI" [38.71s - 39.619s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Fueling the AI";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 38.71);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 38.71);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 39.499);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 39.619);

  // Caption: "Revolution. Because artificial" [39.619s - 41.874s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Revolution. Because artificial";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 39.619);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 39.619);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 41.754000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 41.874);

  // Caption: "intelligence calculations are" [41.874s - 43.793s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "intelligence calculations are";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 41.874);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 41.874);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 43.673);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 43.793);

  // Caption: "essentially giant matrix" [43.793s - 45.291s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "essentially giant matrix";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 43.793);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 43.793);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 45.171);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 45.291);

  // Caption: "multiplications, GPUs became" [45.291s - 47.058s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "multiplications, GPUs became";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 45.291);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 45.291);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 46.938);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 47.058);

  // Caption: "the turbo-engine of" [47.058s - 48.185s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "the turbo-engine of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 47.058);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 47.058);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 48.065000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 48.185);

  // Caption: "modern deep learning." [48.185s - 49.549s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "modern deep learning.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 48.185);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 48.185);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 49.429);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 49.549);

  // Caption: "Matrix multiplication in" [49.549s - 51.047s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Matrix multiplication in";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 49.549);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 49.549);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 50.927);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 51.047);

  // Caption: "neural networks maps" [51.047s - 52.157s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "neural networks maps";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 51.047);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 51.047);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 52.037);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 52.157);

  // Caption: "directly to GPU" [52.157s - 53.016s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "directly to GPU";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 52.157);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 52.157);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 52.896);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 53.016);

  // Caption: "tensor architectures, enabling" [53.016s - 54.85s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "tensor architectures, enabling";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 53.016);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 53.016);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 54.730000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 54.85);

  // Caption: "trillion-parameter AI models" [54.85s - 56.617s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "trillion-parameter AI models";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 54.85);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 54.85);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 56.497);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 56.617);

  // Caption: "to train efficiently." [56.617s - 58.065s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "to train efficiently.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 56.617);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 56.617);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 57.945);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 58.065);

  // Caption: "Looking forward, How" [58.065s - 61.354s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Looking forward, How";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 58.065);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 58.065);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 61.234);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 61.354);

  // Caption: "GPUs Work continues" [61.354s - 64.405s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "GPUs Work continues";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 61.354);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 61.354);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 64.285);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 64.405);

  // Caption: "to accelerate innovations" [64.405s - 69.22s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "to accelerate innovations";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 64.405);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 64.405);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 69.1);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 69.22);

  // Caption: "across modern research" [69.22s - 72.796s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "across modern research";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 69.22);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 69.22);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 72.676);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 72.796);

  // Caption: "and engineering domains." [72.796s - 77.42s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and engineering domains.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 72.796);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 72.796);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 77.3);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 77.42);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 5.0);
