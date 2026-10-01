#!/usr/bin/env node
/**
 * Harness 9 — deterministic HyperFrames frame capture.
 *
 * Loads a HyperFrames composition (index.html + a paused GSAP timeline registered on
 * window.__timelines) in headless Chromium, seeks every timeline to t = frame / fps and
 * writes one image per frame. Encoding + audio muxing happen afterwards in Python/ffmpeg.
 *
 * Guarantees
 *   - Deterministic: frames come from absolute timeline seeks, never from wall-clock playback.
 *   - Hermetic: the page can only read file:// and data: URLs. GSAP requests (CDN links) are
 *     answered from the pinned local copy; every other network request is blocked and reported.
 *   - Loud: a missing browser, GSAP, timeline registry or a frame that fails to capture is an
 *     error (non-zero exit). There is no "placeholder frame" fallback.
 *
 * Protocol: one JSON object per stdout line: {event:"start"|"progress"|"done"|"error", ...}.
 * Exit codes: 0 ok · 2 capture failed · 3 no browser available.
 *
 * Usage:
 *   node capture_frames.mjs --project DIR --out FRAMES_DIR --width 1920 --height 1080 \
 *        --fps 30 --duration 30 [--format jpeg|png] [--quality 95] [--chrome PATH] [--no-sandbox]
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));

const emit = (obj) => process.stdout.write(JSON.stringify(obj) + '\n');
const log = (msg) => process.stderr.write(`[h9-capture] ${msg}\n`);

class BrowserUnavailable extends Error {}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) out[key] = true;
    else {
      out[key] = next;
      i++;
    }
  }
  return out;
}

const BASE_ARGS = [
  '--hide-scrollbars',
  '--mute-audio',
  '--disable-gpu',
  '--disable-dev-shm-usage',
  '--force-color-profile=srgb',
  '--font-render-hinting=none',
  '--disable-lcd-text',
  '--allow-file-access-from-files',
  '--disable-background-timer-throttling',
  '--disable-renderer-backgrounding',
  '--disable-backgrounding-occluded-windows',
];

function locateGsapDist(explicit) {
  const candidates = [
    explicit,
    path.join(HERE, 'node_modules', 'gsap', 'dist'),
  ].filter(Boolean);
  try {
    candidates.push(path.join(path.dirname(require.resolve('gsap/package.json')), 'dist'));
  } catch {
    /* gsap exports map may hide package.json; the path above is authoritative */
  }
  return candidates.find((dir) => fs.existsSync(path.join(dir, 'gsap.min.js'))) || null;
}

async function resolveBrowser(chromeArg) {
  if (chromeArg && chromeArg !== true) {
    if (!fs.existsSync(chromeArg)) throw new BrowserUnavailable(`Chrome executable not found: ${chromeArg}`);
    return { executablePath: chromeArg, headless: true, args: [], label: chromeArg };
  }
  try {
    // Optional: Linux-only self-contained Chromium (install with `npm i @sparticuz/chromium`).
    const mod = await import('@sparticuz/chromium');
    const chromium = mod.default;
    const executablePath = await chromium.executablePath();
    return { executablePath, headless: 'shell', args: [...chromium.args], label: `@sparticuz/chromium (${executablePath})` };
  } catch {
    throw new BrowserUnavailable(
      'No Chrome/Chromium executable was provided (--chrome) and the optional @sparticuz/chromium package is not installed.'
    );
  }
}

async function main() {
  const a = parseArgs(process.argv.slice(2));
  for (const key of ['project', 'out', 'width', 'height', 'fps', 'duration']) {
    if (a[key] === undefined || a[key] === true) throw new Error(`missing required argument --${key}`);
  }
  const width = parseInt(a.width, 10);
  const height = parseInt(a.height, 10);
  const fps = parseFloat(a.fps);
  const duration = parseFloat(a.duration);
  if (!(width > 0 && height > 0 && fps > 0 && duration > 0)) throw new Error('width/height/fps/duration must be positive numbers');

  const total = Math.max(1, Math.round(duration * fps));
  const format = String(a.format || 'jpeg').toLowerCase() === 'png' ? 'png' : 'jpeg';
  const ext = format === 'png' ? 'png' : 'jpg';
  const quality = Math.min(100, Math.max(1, parseInt(a.quality || '95', 10)));

  const projectDir = path.resolve(String(a.project));
  const entry = path.join(projectDir, String(a.entry || 'index.html'));
  if (!fs.existsSync(entry)) throw new Error(`composition entry not found: ${entry}`);
  const outDir = path.resolve(String(a.out));
  fs.mkdirSync(outDir, { recursive: true });

  const gsapDist = locateGsapDist(a.gsapDir && a.gsapDir !== true ? String(a.gsapDir) : null);
  if (!gsapDist) throw new Error('local GSAP not found — run the toolchain setup (npm install in the capture directory).');
  const gsapCore = fs.readFileSync(path.join(gsapDist, 'gsap.min.js'), 'utf8');

  const browserInfo = await resolveBrowser(a.chrome);
  const launchArgs = [...browserInfo.args, ...BASE_ARGS];
  if (a.noSandbox) launchArgs.push('--no-sandbox', '--disable-setuid-sandbox');

  emit({ event: 'start', total, width, height, fps, format, browser: browserInfo.label });

  const blocked = new Set();
  const pageErrors = [];
  const browser = await puppeteer.launch({
    executablePath: browserInfo.executablePath,
    headless: browserInfo.headless,
    args: launchArgs,
    defaultViewport: { width, height, deviceScaleFactor: 1 },
    protocolTimeout: 120000,
  });

  try {
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', (req) => {
      const url = req.url();
      const settle = (fn) => {
        try {
          fn();
        } catch {
          /* request already settled */
        }
      };
      if (url.startsWith('file://') || url.startsWith('data:') || url.startsWith('blob:') || url === 'about:blank') {
        return settle(() => req.continue());
      }
      let pathname = '';
      try {
        pathname = new URL(url).pathname;
      } catch {
        /* ignore */
      }
      // GSAP core / plugins referenced through a CDN <script src> → serve the pinned local copy.
      if (/\/gsap\b/i.test(pathname) || /\/gsap(\.min)?\.js$/i.test(pathname)) {
        const name = path.basename(pathname);
        const local = path.join(gsapDist, name);
        if (name.endsWith('.js') && fs.existsSync(local)) {
          return settle(() =>
            req.respond({ status: 200, contentType: 'application/javascript; charset=utf-8', body: fs.readFileSync(local, 'utf8') })
          );
        }
      }
      blocked.add(url);
      return settle(() => req.abort('blockedbyclient'));
    });
    page.on('pageerror', (err) => pageErrors.push(String(err && err.message ? err.message : err)));

    await page.goto(pathToFileURL(entry).href, { waitUntil: 'load', timeout: 60000 });

    const ready = await page.evaluate(async () => {
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      const imgs = Array.from(document.images);
      await Promise.all(imgs.map((img) => (img.decode ? img.decode().catch(() => null) : null)));
      const broken = imgs
        .filter((img) => !img.complete || (img.naturalWidth === 0 && !/\.svg(\?|#|$)/i.test(img.currentSrc || img.src)))
        .map((img) => img.getAttribute('src'));
      return {
        hasGsap: typeof window.gsap !== 'undefined',
        timelines: Object.keys(window.__timelines || {}),
        brokenImages: broken,
      };
    });

    if (!ready.hasGsap) {
      throw new Error('GSAP did not load in the page (window.gsap is undefined). Check the <script> tag in index.html.');
    }
    if (ready.timelines.length === 0) {
      throw new Error(
        'No timelines are registered on window.__timelines. A HyperFrames composition must register its paused ' +
          'GSAP timeline (e.g. window.__timelines["root"] = tl). Without it every frame would be identical.' +
          (pageErrors.length ? ` Page errors: ${pageErrors.slice(0, 3).join(' | ')}` : '')
      );
    }

    const started = Date.now();
    const step = Math.max(1, Math.floor(total / 10));
    for (let i = 0; i < total; i++) {
      const t = i / fps;
      await page.evaluate((time) => {
        for (const tl of Object.values(window.__timelines)) {
          if (tl && typeof tl.pause === 'function') {
            tl.pause();
            tl.time(time, false);
          }
        }
        return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      }, t);

      const file = path.join(outDir, `frame_${String(i).padStart(6, '0')}.${ext}`);
      const shot = { path: file, type: format, optimizeForSpeed: true, captureBeyondViewport: false };
      if (format === 'jpeg') shot.quality = quality;
      await page.screenshot(shot);
      if (!fs.existsSync(file) || fs.statSync(file).size === 0) {
        throw new Error(`frame ${i} was not written: ${file}`);
      }
      if (i % step === 0 || i === total - 1) {
        emit({ event: 'progress', frame: i + 1, total, elapsed: (Date.now() - started) / 1000 });
      }
    }

    emit({
      event: 'done',
      frames: total,
      format,
      ext,
      timelines: ready.timelines,
      blocked_requests: Array.from(blocked),
      broken_images: ready.brokenImages,
      page_errors: pageErrors.slice(0, 20),
      browser: browserInfo.label,
      seconds: (Date.now() - started) / 1000,
    });
  } finally {
    await browser.close().catch(() => undefined);
  }
}

main().then(
  () => process.exit(0),
  (err) => {
    const code = err instanceof BrowserUnavailable ? 3 : 2;
    emit({ event: 'error', code, message: String(err && err.message ? err.message : err) });
    log(String(err && err.stack ? err.stack : err));
    process.exit(code);
  }
);
