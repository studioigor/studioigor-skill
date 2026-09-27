#!/usr/bin/env node
// Web game frame capture for studioigor: this is how the agent sees the game without a human.
//
// Copy into the project as tools/capture.mjs. Playwright is taken from the project:
//   npm i -D playwright && npx playwright install chromium
// (inside the project specifically: the package version and browser revision must match).
//
// Run (from the project root):
//   node tools/capture.mjs --dir dist --out .studioigor/captures/main --duration 8 --every 1
//   node tools/capture.mjs --serve "npx vite --port 5199 --strictPort" --url http://localhost:5199/?scene=drift \
//       --out .studioigor/captures/drift --duration 8 --every 1 --inputs tools/inputs/drift.json
//   node tools/capture.mjs --url http://localhost:5173/ --out .studioigor/captures/x
//
// Options:
//   --url U            game address (with --dir defaults to the root of the built-in server)
//   --dir D            serve folder D with the built-in static server (dist/ build, no dependencies)
//   --isolate          the built-in server sends COOP/COEP (only for multithreaded builds)
//   --serve "CMD"      start your own server (vite/preview); waits until --url responds
//   --out O            where to write frames (default .studioigor/captures/capture)
//   --duration S       session length, s (8)      --every S   frame step, s (1)
//   --start S          first frame S s after the page is ready (0.25)
//   --width W --height H  viewport (1280x720)           --scale N   deviceScaleFactor (1)
//   --inputs F         JSON input schedule (see below)
//   --wait-for "JS"    wait until the expression is truthy, e.g. "window.__GAME__?.ready"
//   --seed N           append ?capture=1&seed=N to the URL (the game reads the seed itself)
//   --selector CSS     capture an element (e.g. canvas) instead of the whole page
//   --cols N --tile PX contact sheet (4 columns of 480 px)
//   --headed           show the browser window (headless by default: on macOS WebGL runs on the GPU)
//   --allow-errors     do not fail on console/page errors (they still go into metrics.json)
//   --ignore "regex"   ignore console errors matching the regex (favicon.ico is always ignored)
//   --require-completed  fail if window.__metrics.completed !== true
//   --timeout S        overall timeout, s (120)
//
// Input schedule (t — seconds since the page was ready):
//   [{"t": 0.5, "key": "ArrowUp", "hold": 3.0},     hold and release after 3 s
//    {"t": 1.0, "key": "Space"},                    tap (hold defaults to 0.1)
//    {"t": 2.0, "keydown": "KeyW"}, {"t": 4.0, "keyup": "KeyW"},
//    {"t": 5.0, "click": [640, 360]},              click at viewport coordinates
//    {"t": 6.0, "eval": "window.__GAME__.spawnWave()"}]
//
// Writes to --out: frame_000.png …, sheet.png (contact sheet), metrics.json.
// Game metrics: whatever the game puts in window.__metrics goes into the "game" field.
// Exit: 0 — ok; 1 — failure (did not load, console/page errors, no frames,
// completed !== true with --require-completed); 2 — invalid run (no playwright, arguments).
//
// Browser: if the chromium revision does not match the package ("Executable doesn't exist"),
// run `npx playwright install chromium` INSIDE the project. Fallback — the
// PW_CHROMIUM=/path/to/chrome variable or headless_shell (executablePath).

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';

// ------------------------------------------------------------------ arguments
const argv = process.argv.slice(2);
const opts = {};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (!a.startsWith('--')) { usage(`unexpected argument ${a}`); }
  const [k, inline] = a.slice(2).split(/=(.*)/s);
  if (inline !== undefined) opts[k] = inline;
  else if (i + 1 < argv.length && !argv[i + 1].startsWith('--')) opts[k] = argv[++i];
  else opts[k] = true;
}
const KNOWN = ['url', 'dir', 'serve', 'out', 'duration', 'every', 'start', 'width', 'height', 'scale',
  'inputs', 'wait-for', 'seed', 'selector', 'cols', 'tile', 'headed', 'allow-errors', 'ignore',
  'require-completed', 'timeout', 'isolate'];
for (const k of Object.keys(opts)) if (!KNOWN.includes(k)) usage(`unknown argument --${k}`);

const OUT = path.resolve(opts.out ?? '.studioigor/captures/capture');
const DURATION = num('duration', 8);
const EVERY = Math.max(0.05, num('every', 1));
const START = num('start', 0.25);
const VIEWPORT = { width: num('width', 1280), height: num('height', 720) };
const SCALE = num('scale', 1);
const COLS = Math.max(1, num('cols', 4));
const TILE = Math.max(64, num('tile', 480));
const TIMEOUT = num('timeout', 120) * 1000;
const IGNORE = opts.ignore ? new RegExp(opts.ignore) : null;
if (!opts.url && !opts.dir) usage('--url or --dir is required');
if (opts.serve && !opts.url) usage('with --serve, give the --url the server answers on');

function num(k, d) {
  if (opts[k] === undefined) return d;
  const v = Number(opts[k]);
  if (!Number.isFinite(v)) usage(`--${k} must be a number`);
  return v;
}
function usage(msg) {
  console.error(`capture.mjs: ${msg}. Help: the comment at the top of the file.`);
  process.exit(2);
}

// ------------------------------------------------------------------ playwright from the project
let chromium;
for (const mod of ['playwright', '@playwright/test', 'playwright-core']) {
  try { ({ chromium } = await import(mod)); if (chromium) break; } catch { /* next */ }
}
if (!chromium) {
  console.error('capture.mjs: playwright not found in the project. Install: ' +
    'npm i -D playwright && npx playwright install chromium');
  process.exit(2);
}

// ------------------------------------------------------------------ input schedule
const events = [];
if (opts.inputs) {
  let raw;
  try { raw = JSON.parse(fs.readFileSync(opts.inputs, 'utf8')); } catch (e) { usage(`cannot read ${opts.inputs}: ${e.message}`); }
  if (!Array.isArray(raw)) usage(`${opts.inputs}: a JSON array is required`);
  for (const e of raw) {
    if (typeof e.t !== 'number') usage(`event without t: ${JSON.stringify(e)}`);
    if (e.key) {
      const hold = e.hold ?? 0.1;
      events.push({ t: e.t, do: 'down', key: e.key }, { t: e.t + hold, do: 'up', key: e.key });
    } else if (e.keydown) events.push({ t: e.t, do: 'down', key: e.keydown });
    else if (e.keyup) events.push({ t: e.t, do: 'up', key: e.keyup });
    else if (e.click) events.push({ t: e.t, do: 'click', x: e.click[0], y: e.click[1] });
    else if (e.eval) events.push({ t: e.t, do: 'eval', js: e.eval });
    else usage(`an event needs key, keydown, keyup, click or eval: ${JSON.stringify(e)}`);
  }
  events.sort((a, b) => a.t - b.t);
}

// ------------------------------------------------------------------ server
let server = null;       // built-in static server
let child = null;        // external --serve
let baseUrl = opts.url;

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.wasm': 'application/wasm', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml',
  '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.ogg': 'audio/ogg', '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav', '.ttf': 'font/ttf', '.woff2': 'font/woff2', '.pck': 'application/octet-stream' };

if (opts.dir) {
  const root = path.resolve(opts.dir);
  if (!fs.existsSync(path.join(root, 'index.html'))) usage(`no index.html in ${root} (run BUILD)`);
  server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let f = path.join(root, p);
    if (!f.startsWith(root)) { res.writeHead(403).end(); return; }
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
    if (!fs.existsSync(f)) { res.writeHead(404).end('not found'); return; }
    const headers = { 'Content-Type': MIME[path.extname(f).toLowerCase()] ?? 'application/octet-stream' };
    if (opts.isolate) {
      // COOP/COEP are needed only by multithreaded builds (Godot threads, SharedArrayBuffer)
      headers['Cross-Origin-Opener-Policy'] = 'same-origin';
      headers['Cross-Origin-Embedder-Policy'] = 'require-corp';
    }
    res.writeHead(200, headers);
    fs.createReadStream(f).pipe(res);
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  baseUrl = opts.url ? new URL(opts.url, `http://127.0.0.1:${port}/`).href : `http://127.0.0.1:${port}/`;
}

if (opts.serve) {
  child = spawn(opts.serve, { shell: true, stdio: 'ignore', detached: true });
  const until = Date.now() + 30000;
  let up = false;
  while (Date.now() < until && !up) {
    try { const r = await fetch(baseUrl); up = r.status < 500; } catch { /* not up yet */ }
    if (!up) await sleep(300);
  }
  if (!up) await done(1, [`server "${opts.serve}" did not respond at ${baseUrl} within 30 s`]);
}

if (opts.seed !== undefined) {
  const u = new URL(baseUrl);
  u.searchParams.set('capture', '1');
  u.searchParams.set('seed', String(opts.seed));
  baseUrl = u.href;
}

// ------------------------------------------------------------------ browser
fs.mkdirSync(OUT, { recursive: true });
for (const f of fs.readdirSync(OUT)) {
  if (/^frame_\d+\.png$/.test(f) || f === 'sheet.png' || f === 'metrics.json') fs.rmSync(path.join(OUT, f));
}

const launchOpts = { headless: !opts.headed };
if (process.env.PW_CHROMIUM) launchOpts.executablePath = process.env.PW_CHROMIUM;
let browser;
try {
  browser = await chromium.launch(launchOpts);
} catch (e) {
  const first = String(e.message).split('\n')[0];
  await done(2, [`chromium failed to launch: ${first}. Run in the project: npx playwright install chromium ` +
    `(or set PW_CHROMIUM=/path/to/chrome)`]);
}
const watchdog = setTimeout(() => done(1, [`timeout ${TIMEOUT / 1000} s`]), TIMEOUT);

const errors = [];
const warnings = [];
const page = await browser.newPage({ viewport: VIEWPORT, deviceScaleFactor: SCALE });
page.on('pageerror', e => errors.push(`pageerror: ${e.message}`));
page.on('console', m => {
  const loc = m.location()?.url ?? '';
  const text = `${m.text()}${loc ? ` (${loc.split('/').pop()})` : ''}`;
  if (m.type() === 'error') {
    if (/favicon\.ico/.test(loc) || /favicon\.ico/.test(m.text()) || (IGNORE && IGNORE.test(text))) return;
    errors.push(`console: ${text}`);
  } else if (m.type() === 'warning' && !/GL Driver Message/.test(text)) warnings.push(text);  // noise from screenshots
});
page.on('crash', () => errors.push('the page crashed (crash)'));

// fps from the harness side: count requestAnimationFrame, nothing needed from the game
await page.addInitScript(() => {
  window.__fps = [];
  let n = 0;
  const tick = () => { n++; requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  setInterval(() => { window.__fps.push(n); n = 0; }, 1000);
});

try {
  await page.goto(baseUrl, { waitUntil: 'load', timeout: 30000 });
  if (opts['wait-for']) {
    await page.waitForFunction(opts['wait-for'], null, { timeout: 30000, polling: 100 });
  }
} catch (e) {
  await done(1, [`the page did not load or --wait-for timed out: ${String(e.message).split('\n')[0]}`]);
}

// ------------------------------------------------------------------ session
const shots = [];
const target = opts.selector ? page.locator(opts.selector).first() : page;
const t0 = Date.now();
let nextShot = START;
const due = [...events];
while (true) {
  const t = (Date.now() - t0) / 1000;
  while (due.length && due[0].t <= t) {
    const e = due.shift();
    try {
      if (e.do === 'down') await page.keyboard.down(e.key);
      else if (e.do === 'up') await page.keyboard.up(e.key);
      else if (e.do === 'click') await page.mouse.click(e.x, e.y);
      else if (e.do === 'eval') await page.evaluate(e.js);
    } catch (err) {
      errors.push(`input ${JSON.stringify(e)}: ${String(err.message).split('\n')[0]}`);
    }
  }
  if (t >= nextShot && nextShot <= DURATION + 1e-6) {
    const file = path.join(OUT, `frame_${String(shots.length).padStart(3, '0')}.png`);
    await target.screenshot({ path: file });
    shots.push(file);
    nextShot += EVERY;
  }
  if (t >= DURATION) break;
  await sleep(15);
}

// ------------------------------------------------------------------ metrics
const game = await page.evaluate(() => window.__metrics ?? null).catch(() => null);
const fpsAll = await page.evaluate(() => window.__fps ?? []).catch(() => []);
const fps = fpsAll.length > 1 ? fpsAll.slice(1) : fpsAll;
const sheet = shots.length ? await makeSheet(shots) : '';

const fails = [];
if (!shots.length) fails.push('no frames captured');
if (errors.length && !opts['allow-errors']) fails.push(`page/console errors: ${errors.length} (first: ${errors[0]})`);
if (opts['require-completed'] && game?.completed !== true) fails.push('window.__metrics.completed !== true');

const metrics = {
  ok: fails.length === 0,
  url: baseUrl,
  viewport: [VIEWPORT.width, VIEWPORT.height],
  seed: opts.seed ?? null,
  duration: DURATION,
  fps_mean: fps.length ? +(fps.reduce((a, b) => a + b, 0) / fps.length).toFixed(1) : 0,
  fps_min: fps.length ? Math.min(...fps) : 0,
  frames: shots.map(f => path.basename(f)),
  sheet: sheet ? path.basename(sheet) : '',
  error_count: errors.length,
  errors: errors.slice(0, 20),
  warning_count: warnings.length,
  warnings: warnings.slice(0, 20),
  game,
  fail_reasons: fails,
};
fs.writeFileSync(path.join(OUT, 'metrics.json'), JSON.stringify(metrics, null, 2) + '\n');
clearTimeout(watchdog);
if (fails.length) await done(1, fails);
console.log(`capture ok: ${shots.length} frames, ${metrics.sheet}, metrics.json -> ${OUT}`);
await done(0, []);

// ------------------------------------------------------------------ helpers
async function makeSheet(files) {
  const p = await browser.newPage();
  await p.setContent('<canvas id=c></canvas>');
  const data = await p.evaluate(async ({ srcs, cols, tile }) => {
    const imgs = await Promise.all(srcs.map(s => new Promise((res, rej) => {
      const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = s;
    })));
    const th = Math.round(tile * imgs[0].height / imgs[0].width);
    const c = Math.min(cols, imgs.length);
    const cv = document.getElementById('c');
    cv.width = c * tile; cv.height = Math.ceil(imgs.length / c) * th;
    const ctx = cv.getContext('2d');
    ctx.fillStyle = '#101012'; ctx.fillRect(0, 0, cv.width, cv.height);
    imgs.forEach((im, i) => ctx.drawImage(im, (i % c) * tile, Math.floor(i / c) * th, tile, th));
    return cv.toDataURL('image/png');
  }, {
    srcs: files.map(f => `data:image/png;base64,${fs.readFileSync(f).toString('base64')}`),
    cols: COLS, tile: TILE,
  });
  await p.close();
  const out = path.join(OUT, 'sheet.png');
  fs.writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
  return out;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function done(code, reasons) {
  for (const r of reasons) console.error(`CAPTURE FAILED: ${r}`);
  try { if (browser) await browser.close(); } catch { /* already closed */ }
  if (server) server.close();
  if (child) { try { process.kill(-child.pid); } catch { /* already exited */ } }
  process.exit(code);
}
