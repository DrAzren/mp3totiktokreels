// Renders the reel with headless Chromium.
//   node render.mjs --site <dir> --out video.mp4 [--workers 4] [--from 0 --to 163]
//   node render.mjs --site <dir> --stills 0.5,8.7,30 --outdir previews/
// <dir> must contain index.html + js, fonts/, data/{words,clips}.json and frames/.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || '/opt/node22/lib/node_modules/playwright');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? a.concat([[v.slice(2), arr[i + 1]]]) : a), []));
const SITE = path.resolve(args.site), FPS = 30;
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.png': 'image/png' };

function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(SITE, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(p, (err, buf) => {
        if (err) { rsp.writeHead(404); rsp.end(); return; }
        rsp.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'max-age=3600' }); rsp.end(buf);
      });
    }).listen(0, () => res(srv));
  });
}

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  const info = await page.evaluate(() => window.init());
  return { page, info };
}

function encoder(file) {
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg ' + c)))));
  return { ff, done };
}

async function renderRange(browser, port, f0, f1, file, label) {
  const { page } = await openPage(browser, port);
  const { ff, done } = encoder(file);
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const url = await page.evaluate(t => window.renderFrame(t), f / FPS);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 150 === 0) console.log(`[${label}] frame ${f - f0}/${f1 - f0}  ${((f - f0) / ((Date.now() - t0) / 1000 + 1e-3)).toFixed(1)} fps`);
  }
  ff.stdin.end(); await done; await page.close();
}

const srv = await serve();
const port = srv.address().port;
const browser = await chromium.launch({ args: ['--disable-web-security', '--font-render-hinting=none'] });
try {
  if (args.stills) {
    const { page, info } = await openPage(browser, port);
    fs.mkdirSync(args.outdir, { recursive: true });
    for (const s of args.stills.split(',').map(Number)) {
      const url = await page.evaluate(t => window.renderFrame(t), s);
      fs.writeFileSync(path.join(args.outdir, `still_${s.toFixed(2)}.jpg`), Buffer.from(url.split(',')[1], 'base64'));
    }
    console.log('stills done; duration', info.duration);
  } else {
    const { page, info } = await openPage(browser, port);
    fs.writeFileSync(args.sfx || 'sfx.json', JSON.stringify(info.sfx, null, 0));
    fs.writeFileSync((args.sfx || 'sfx.json').replace(/sfx\.json$/, 'shots.json'), JSON.stringify(info.shots, null, 0));
    await page.close();
    const from = +(args.from || 0), to = +(args.to || info.duration), N = +(args.workers || 4);
    const F0 = Math.round(from * FPS), F1 = Math.round(to * FPS), per = Math.ceil((F1 - F0) / N), parts = [];
    const tmp = path.dirname(path.resolve(args.out));
    await Promise.all(Array.from({ length: N }, (_, k) => {
      const a = F0 + k * per, b = Math.min(F1, a + per); if (a >= b) return null;
      const file = path.join(tmp, `part_${k}.mp4`); parts[k] = file;
      return renderRange(browser, port, a, b, file, 'w' + k);
    }));
    const list = path.join(tmp, 'parts.txt'); fs.writeFileSync(list, parts.filter(Boolean).map(p => `file '${p}'`).join('\n'));
    await new Promise((res, rej) => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', args.out], { stdio: 'inherit' })
      .on('close', c => (c === 0 ? res() : rej(new Error('concat ' + c)))));
    console.log('video written', args.out, 'sfx events', info.sfx.length);
  }
} finally { await browser.close(); srv.close(); }
