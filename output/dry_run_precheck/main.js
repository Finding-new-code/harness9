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
  // Caption: "The Genesis of" [0.0s - 0.742s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Genesis of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.0);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.0);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 0.622);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 0.742);

  // Caption: "Artificial Intelligence. Every" [0.742s - 2.696s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Artificial Intelligence. Every";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 0.742);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 0.742);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 2.576);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 2.696);

  // Caption: "great technological revolution" [2.696s - 4.452s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "great technological revolution";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 2.696);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 2.696);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.332);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 4.452);

  // Caption: "starts with a" [4.452s - 5.012s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "starts with a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 4.452);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 4.452);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 4.8919999999999995);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 5.012);

  // Caption: "challenge. For Artificial" [5.012s - 6.512s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "challenge. For Artificial";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 5.012);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 5.012);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 6.3919999999999995);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 6.512);

  // Caption: "Intelligence, it began" [6.512s - 7.769s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Intelligence, it began";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 6.512);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 6.512);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 7.649);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 7.769);

  // Caption: "with a daring" [7.769s - 8.405s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "with a daring";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 7.769);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 7.769);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 8.285);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 8.405);

  // Caption: "new approach. The" [8.405s - 9.359s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "new approach. The";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 8.405);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 8.405);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 9.239);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 9.359);

  // Caption: "foundational principles of" [9.359s - 10.843s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "foundational principles of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 9.359);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 9.359);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 10.723);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 10.843);

  // Caption: "Artificial Intelligence were" [10.843s - 12.539s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Artificial Intelligence were";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 10.843);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 10.843);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 12.419);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 12.539);

  // Caption: "established through seminal" [12.539s - 13.977s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "established through seminal";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 12.539);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 12.539);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 13.857000000000001);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 13.977);

  // Caption: "experimental breakthroughs and" [13.977s - 15.582s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "experimental breakthroughs and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 13.977);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 13.977);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 15.462000000000002);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 15.582);

  // Caption: "early theoretical formulations." [15.582s - 17.566s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "early theoretical formulations.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 15.582);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 15.582);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 17.445999999999998);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 17.566);

  // Caption: "The Architecture of" [17.566s - 18.677s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "The Architecture of";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 17.566);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 17.566);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 18.557);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 18.677);

  // Caption: "Artificial Intelligence. Behind" [18.677s - 20.706s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Artificial Intelligence. Behind";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 18.677);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 18.677);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 20.586);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 20.706);

  // Caption: "its outward simplicity" [20.706s - 21.994s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "its outward simplicity";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 20.706);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 20.706);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 21.874);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 21.994);

  // Caption: "lies an intricate" [21.994s - 23.041s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "lies an intricate";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 21.994);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 21.994);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 22.921);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 23.041);

  // Caption: "system designed for" [23.041s - 24.071s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "system designed for";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 23.041);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 23.041);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 23.951);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 24.071);

  // Caption: "precision, speed, and" [24.071s - 25.343s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "precision, speed, and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 24.071);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 24.071);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 25.223);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 25.343);

  // Caption: "continuous scaling. At" [25.343s - 26.76s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "continuous scaling. At";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 25.343);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 25.343);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 26.64);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 26.76);

  // Caption: "its functional core," [26.76s - 27.951s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "its functional core,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 26.76);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 26.76);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 27.831);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 27.951);

  // Caption: "Artificial Intelligence operates" [27.951s - 30.045s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Artificial Intelligence operates";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 27.951);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 27.951);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 29.925);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 30.045);

  // Caption: "by transforming input" [30.045s - 31.139s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "by transforming input";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 30.045);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 30.045);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 31.019);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 31.139);

  // Caption: "energy or signals" [31.139s - 32.105s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "energy or signals";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 31.139);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 31.139);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 31.984999999999996);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 32.105);

  // Caption: "through structured physical" [32.105s - 33.555s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "through structured physical";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 32.105);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 32.105);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 33.435);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 33.555);

  // Caption: "and algorithmic mechanisms." [33.555s - 35.132s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "and algorithmic mechanisms.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 33.555);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 33.555);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 35.012);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 35.132);

  // Caption: "Transforming the Modern" [35.132s - 36.304s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Transforming the Modern";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 35.132);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 35.132);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 36.184000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 36.304);

  // Caption: "World. Today, Artificial" [36.304s - 37.93s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "World. Today, Artificial";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 36.304);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 36.304);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 37.81);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 37.93);

  // Caption: "Intelligence quietly powers" [37.93s - 39.638s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Intelligence quietly powers";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 37.93);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 37.93);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 39.518);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 39.638);

  // Caption: "the systems we" [39.638s - 40.354s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "the systems we";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 39.638);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 39.638);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 40.234);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 40.354);

  // Caption: "rely on daily," [40.354s - 41.281s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "rely on daily,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 40.354);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 40.354);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 41.161);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 41.281);

  // Caption: "laying the groundwork" [41.281s - 42.468s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "laying the groundwork";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 41.281);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 41.281);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 42.348000000000006);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 42.468);

  // Caption: "for tomorrow's breakthroughs." [42.468s - 44.094s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "for tomorrow's breakthroughs.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 42.468);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 42.468);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 43.974000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 44.094);

  // Caption: "Today, Artificial Intelligence" [44.094s - 46.111s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Today, Artificial Intelligence";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 44.094);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 44.094);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 45.991);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 46.111);

  // Caption: "serves as a" [46.111s - 46.729s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "serves as a";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 46.111);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 46.111);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 46.609);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 46.729);

  // Caption: "critical technological pillar" [46.729s - 48.421s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "critical technological pillar";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 46.729);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 46.729);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 48.301);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 48.421);

  // Caption: "across modern computing," [48.421s - 49.755s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "across modern computing,";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 48.421);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 48.421);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 49.635000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 49.755);

  // Caption: "manufacturing, and global" [49.755s - 51.202s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "manufacturing, and global";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 49.755);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 49.755);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 51.082);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 51.202);

  // Caption: "digital infrastructure." [51.202s - 52.699s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "digital infrastructure.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 51.202);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 51.202);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 52.579);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 52.699);

  // Caption: "Looking forward, Artificial" [52.699s - 56.606s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Looking forward, Artificial";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 52.699);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 52.699);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 56.486000000000004);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 56.606);

  // Caption: "Intelligence continues to" [56.606s - 60.249s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "Intelligence continues to";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 56.606);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 56.606);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 60.129000000000005);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 60.249);

  // Caption: "accelerate innovations across" [60.249s - 64.574s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "accelerate innovations across";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 60.249);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 60.249);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 64.454);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 64.574);

  // Caption: "modern research and" [64.574s - 67.002s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "modern research and";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 64.574);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 64.574);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 66.88199999999999);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 67.002);

  // Caption: "engineering domains." [67.002s - 70.265s]
  tl.call(() => {
    const box = document.getElementById("caption-box");
    if (box) {
      box.textContent = "engineering domains.";
      box.style.visibility = "visible";
      box.style.opacity = "1";
    }
  }, [], 67.002);
  tl.fromTo("#caption-box", { scale: 0.95, opacity: 0 }, { scale: 1.0, opacity: 1, duration: 0.15, ease: "power2.out" }, 67.002);
  tl.to("#caption-box", { opacity: 0, duration: 0.12, ease: "power2.in" }, 70.145);
  // Hard kill guarantee
  tl.set("#caption-box", { opacity: 0, visibility: "hidden" }, 70.265);

// 5. Total Composition Duration Anchor
tl.to({}, { duration: 0.01 }, 5.0);
