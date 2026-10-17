// Deterministic 1080x1920 canvas compositor. Everything is a pure function of time t,
// so any frame can be rendered independently (lets render.mjs split work across workers).
'use strict';
const W = 1080, H = 1920, FPS = 30;
const C = {
  navy: '#0B1B2E', navy2: '#13304D', ink: '#0A1626', paper: '#F4EFE6', paper2: '#E7DDCB',
  teal: '#2EC4B6', tealD: '#13867D', amber: '#F2A65A', coral: '#E76F51', yellow: '#FFD166',
  white: '#FFFFFF', red: '#D64545', mute: '#8FA3B8',
};
const F = {
  head: 'Anton', serif: 'DM Serif Display', ui: 'Plus Jakarta Sans', hand: 'Caveat', mono: 'JetBrains Mono',
};

// ---------- math / easing ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, t0, d) => clamp((t - t0) / d);
const E = {
  lin: t => t,
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  inOut: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  back: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  expo: t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  spring: t => (t >= 1 ? 1 : 1 - Math.exp(-6 * t) * Math.cos(10 * t)),
};
function rng(seed) {
  let a = seed >>> 0;
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
// in/out envelope: returns {i, o, a} where a = visible alpha
function env(t, t0, t1, din = 0.35, dout = 0.3) {
  const i = prog(t, t0, din), o = prog(t, t1 - dout, dout);
  return { i, o, a: Math.min(i, 1 - o) };
}

// ---------- canvas helpers ----------
function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function font(ctx, fam, size, weight = 400, style = 'normal') { ctx.font = `${style} ${weight} ${size}px '${fam}'`; }
function txt(ctx, s, x, y, o = {}) {
  font(ctx, o.font || F.ui, o.size || 48, o.weight || 700, o.style || 'normal');
  ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'middle';
  if ('letterSpacing' in ctx) ctx.letterSpacing = (o.track || 0) + 'px';
  if (o.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = o.strokeW || 10; ctx.strokeStyle = o.stroke; ctx.strokeText(s, x, y); }
  if (o.shadow) { ctx.shadowColor = o.shadow; ctx.shadowBlur = o.shadowBlur || 18; ctx.shadowOffsetY = o.shadowY || 4; }
  ctx.fillStyle = o.color || C.white; ctx.fillText(s, x, y);
  ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
}
function measure(ctx, s, o = {}) {
  font(ctx, o.font || F.ui, o.size || 48, o.weight || 700, o.style || 'normal');
  if ('letterSpacing' in ctx) ctx.letterSpacing = (o.track || 0) + 'px';
  const w = ctx.measureText(s).width;
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
  return w;
}
function rrect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function withT(ctx, x, y, rot, sc, fn) {
  ctx.save(); ctx.translate(x, y); if (rot) ctx.rotate(rot); if (sc !== undefined && sc !== 1) ctx.scale(sc, sc); fn(); ctx.restore();
}
// jittery polyline that looks hand drawn; returns points
function roughLine(pts, seed, amp = 3, steps = 12) {
  const r = rng(seed), out = [];
  for (let k = 0; k < pts.length - 1; k++) {
    const [x0, y0] = pts[k], [x1, y1] = pts[k + 1];
    for (let s = 0; s < steps; s++) { const u = s / steps; out.push([lerp(x0, x1, u) + (r() - .5) * amp, lerp(y0, y1, u) + (r() - .5) * amp]); }
  }
  out.push(pts[pts.length - 1]); return out;
}
// draws first fraction p of a polyline
function partialPath(ctx, pts, p) {
  if (p <= 0) return;
  let total = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); total += d; }
  let left = total * clamp(p); ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length && left > 0; i++) {
    const d = seg[i - 1], u = Math.min(1, left / d);
    ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)); left -= d;
  }
  ctx.stroke();
}

// ---------- procedural textures (built once) ----------
const TEX = {};
function buildTextures() {
  // paper grain
  const p = mk(540, 960), g = p.getContext('2d'), r = rng(7);
  g.fillStyle = C.paper; g.fillRect(0, 0, 540, 960);
  const id = g.getImageData(0, 0, 540, 960);
  for (let i = 0; i < id.data.length; i += 4) { const n = (r() - .5) * 18; id.data[i] += n; id.data[i + 1] += n; id.data[i + 2] += n - 2; }
  g.putImageData(id, 0, 0);
  for (let k = 0; k < 90; k++) { g.strokeStyle = `rgba(120,100,70,${0.03 + r() * 0.04})`; g.lineWidth = 1; g.beginPath();
    const x = r() * 540, y = r() * 960; g.moveTo(x, y); g.lineTo(x + (r() - .5) * 140, y + (r() - .5) * 30); g.stroke(); }
  TEX.paper = p;
  // film grain frames
  TEX.grain = [];
  for (let k = 0; k < 6; k++) {
    const c = mk(540, 960), cg = c.getContext('2d'), d = cg.createImageData(540, 960), rr = rng(100 + k);
    for (let i = 0; i < d.data.length; i += 4) { const v = 128 + (rr() - .5) * 120; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
    cg.putImageData(d, 0, 0); TEX.grain.push(c);
  }
  // vignette
  const v = mk(W, H), vg = v.getContext('2d'), rg = vg.createRadialGradient(W / 2, H * .46, H * .25, W / 2, H * .5, H * .75);
  rg.addColorStop(0, 'rgba(0,0,0,0)'); rg.addColorStop(1, 'rgba(3,10,20,0.62)'); vg.fillStyle = rg; vg.fillRect(0, 0, W, H);
  TEX.vignette = v;
  // stamp speckle mask
  const s = mk(600, 240), sg = s.getContext('2d'), sr = rng(42);
  for (let k = 0; k < 900; k++) { sg.fillStyle = `rgba(0,0,0,${0.3 + sr() * 0.7})`; sg.beginPath(); sg.arc(sr() * 600, sr() * 240, sr() * 2.4, 0, 7); sg.fill(); }
  TEX.speckle = s;
}

// paper sheet with torn edges + baked shadow, cached by key
const PAPER = new Map();
function paperSheet(w, h, o = {}) {
  const key = [w, h, o.color, o.torn, o.seed, o.kind].join('|');
  if (PAPER.has(key)) return PAPER.get(key);
  const pad = 40, c = mk(w + pad * 2, h + pad * 2), g = c.getContext('2d'), r = rng(o.seed || 1);
  const pts = [], tear = o.torn || 0;
  const edge = (x0, y0, x1, y1, n, torn) => { for (let i = 0; i < n; i++) { const u = i / n;
    const j = torn ? (r() - .5) * tear : (r() - .5) * 1.2; pts.push([lerp(x0, x1, u) + (y0 === y1 ? 0 : j), lerp(y0, y1, u) + (y0 === y1 ? j : 0)]); } };
  const T = o.tornSides || 'tb';
  edge(pad, pad, pad + w, pad, 40, T.includes('t')); edge(pad + w, pad, pad + w, pad + h, 60, T.includes('r'));
  edge(pad + w, pad + h, pad, pad + h, 40, T.includes('b')); edge(pad, pad + h, pad, pad, 60, T.includes('l'));
  const path = () => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); };
  g.save(); g.shadowColor = 'rgba(0,0,0,0.38)'; g.shadowBlur = 26; g.shadowOffsetY = 12; path(); g.fillStyle = o.color || C.paper; g.fill(); g.restore();
  g.save(); path(); g.clip();
  if (!o.flat) { g.globalAlpha = o.color && o.color !== C.paper ? 0.25 : 1; g.globalCompositeOperation = o.color && o.color !== C.paper ? 'multiply' : 'source-over';
    g.drawImage(TEX.paper, 0, 0, TEX.paper.width, TEX.paper.height, 0, 0, c.width, c.height); }
  g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  if (o.color && o.color !== C.paper && !o.flat) { g.globalCompositeOperation = 'color'; g.fillStyle = o.color; g.fillRect(0, 0, c.width, c.height); g.globalCompositeOperation = 'source-over'; }
  const lg = g.createLinearGradient(0, pad, 0, pad + h); lg.addColorStop(0, 'rgba(255,255,255,0.10)'); lg.addColorStop(1, 'rgba(0,0,0,0.07)');
  g.fillStyle = lg; g.fillRect(0, 0, c.width, c.height); g.restore();
  const res = { c, pad }; PAPER.set(key, res); return res;
}
function drawPaper(ctx, x, y, w, h, o = {}) { const p = paperSheet(w, h, o); ctx.drawImage(p.c, x - p.pad, y - p.pad); }
function tape(ctx, x, y, w, rot, alpha = 0.82) {
  withT(ctx, x, y, rot, 1, () => {
    ctx.globalAlpha *= alpha; ctx.fillStyle = '#EFE3C2'; ctx.beginPath(); const h = 46, r = rng(Math.round(x * 7 + y));
    ctx.moveTo(-w / 2, -h / 2); for (let i = 0; i <= 6; i++) ctx.lineTo(-w / 2 + (r() - .5) * 6, -h / 2 + i * h / 6);
    ctx.lineTo(w / 2, h / 2); for (let i = 6; i >= 0; i--) ctx.lineTo(w / 2 + (r() - .5) * 6, -h / 2 + i * h / 6);
    ctx.closePath(); ctx.fill(); ctx.globalAlpha /= alpha;
  });
}

// ---------- icons (100x100 design box, line style) ----------
const ICON = {
  syringe(g) { g.beginPath(); g.moveTo(20, 80); g.lineTo(62, 38); g.moveTo(30, 90); g.lineTo(72, 48); g.moveTo(20, 80); g.lineTo(30, 90);
    g.moveTo(62, 38); g.lineTo(72, 48); g.moveTo(67, 43); g.lineTo(84, 26); g.moveTo(76, 18); g.lineTo(92, 34); g.moveTo(25, 85); g.lineTo(10, 100);
    g.moveTo(36, 72); g.lineTo(42, 78); g.moveTo(46, 62); g.lineTo(52, 68); g.stroke(); },
  capsule(g) { g.save(); g.translate(50, 50); g.rotate(-0.7); rrect(g, -38, -16, 76, 32, 16); g.stroke(); g.beginPath(); g.moveTo(0, -16); g.lineTo(0, 16); g.stroke(); g.restore(); },
  tablet(g) { g.beginPath(); g.arc(50, 50, 32, 0, 7); g.stroke(); g.beginPath(); g.moveTo(28, 50); g.lineTo(72, 50); g.stroke(); },
  calendar(g) { rrect(g, 14, 22, 72, 64, 8); g.stroke(); g.beginPath(); g.moveTo(14, 40); g.lineTo(86, 40); g.moveTo(32, 14); g.lineTo(32, 28); g.moveTo(68, 14); g.lineTo(68, 28); g.stroke();
    [[32, 56], [50, 56], [68, 56], [32, 72], [50, 72]].forEach(([x, y]) => { g.beginPath(); g.arc(x, y, 3, 0, 7); g.fill(); }); },
  ear(g) { g.beginPath(); g.moveTo(40, 82); g.bezierCurveTo(30, 82, 26, 70, 34, 62); g.bezierCurveTo(44, 50, 30, 46, 30, 36); g.bezierCurveTo(30, 18, 60, 12, 66, 32);
    g.bezierCurveTo(70, 46, 56, 50, 54, 60); g.stroke(); g.beginPath(); g.arc(80, 40, 8, -1, 1); g.stroke(); g.beginPath(); g.arc(80, 40, 17, -1, 1); g.stroke(); },
  thought(g) { g.beginPath(); g.ellipse(52, 42, 34, 26, 0, 0, 7); g.stroke(); g.beginPath(); g.arc(26, 78, 6, 0, 7); g.stroke(); g.beginPath(); g.arc(14, 92, 3.5, 0, 7); g.stroke();
    g.beginPath(); g.moveTo(34, 42); g.bezierCurveTo(40, 26, 60, 60, 66, 40); g.bezierCurveTo(70, 30, 48, 30, 54, 48); g.stroke(); },
  eye(g) { g.beginPath(); g.moveTo(8, 50); g.quadraticCurveTo(50, 8, 92, 50); g.quadraticCurveTo(50, 92, 8, 50); g.stroke(); g.beginPath(); g.arc(50, 50, 14, 0, 7); g.stroke(); g.beginPath(); g.arc(50, 50, 5, 0, 7); g.fill(); },
  shield(g) { g.beginPath(); g.moveTo(50, 10); g.lineTo(84, 22); g.lineTo(80, 56); g.quadraticCurveTo(74, 80, 50, 92); g.quadraticCurveTo(26, 80, 20, 56); g.lineTo(16, 22); g.closePath(); g.stroke();
    g.beginPath(); g.moveTo(34, 50); g.lineTo(46, 62); g.lineTo(68, 38); g.stroke(); },
  check(g) { g.beginPath(); g.moveTo(16, 52); g.lineTo(40, 76); g.lineTo(86, 24); g.stroke(); },
  cross(g) { g.beginPath(); g.moveTo(20, 20); g.lineTo(80, 80); g.moveTo(80, 20); g.lineTo(20, 80); g.stroke(); },
  warn(g) { g.beginPath(); g.moveTo(50, 12); g.lineTo(90, 84); g.lineTo(10, 84); g.closePath(); g.stroke(); g.beginPath(); g.moveTo(50, 38); g.lineTo(50, 60); g.stroke(); g.beginPath(); g.arc(50, 72, 3.5, 0, 7); g.fill(); },
  comment(g) { rrect(g, 10, 14, 80, 56, 16); g.stroke(); g.beginPath(); g.moveTo(30, 70); g.lineTo(24, 90); g.lineTo(46, 70); g.stroke();
    [32, 50, 68].forEach(x => { g.beginPath(); g.arc(x, 42, 4, 0, 7); g.fill(); }); },
  arrowDown(g) { g.beginPath(); g.moveTo(50, 12); g.lineTo(50, 84); g.moveTo(24, 58); g.lineTo(50, 86); g.lineTo(76, 58); g.stroke(); },
  home(g) { g.beginPath(); g.moveTo(12, 50); g.lineTo(50, 16); g.lineTo(88, 50); g.moveTo(24, 40); g.lineTo(24, 86); g.lineTo(76, 86); g.lineTo(76, 40); g.moveTo(42, 86); g.lineTo(42, 62); g.lineTo(58, 62); g.lineTo(58, 86); g.stroke(); },
  clipboard(g) { rrect(g, 18, 16, 64, 78, 8); g.stroke(); rrect(g, 36, 8, 28, 16, 5); g.stroke(); g.beginPath(); [40, 56, 72].forEach(y => { g.moveTo(30, y); g.lineTo(70, y); }); g.stroke(); },
  brain(g) { g.beginPath(); g.moveTo(50, 18); g.bezierCurveTo(30, 6, 10, 24, 18, 42); g.bezierCurveTo(4, 54, 16, 80, 34, 76); g.bezierCurveTo(40, 92, 60, 92, 66, 78);
    g.bezierCurveTo(86, 82, 96, 56, 82, 44); g.bezierCurveTo(90, 24, 68, 6, 50, 18); g.stroke(); g.beginPath(); g.moveTo(50, 18); g.lineTo(50, 84);
    g.moveTo(30, 40); g.quadraticCurveTo(40, 48, 50, 42); g.moveTo(70, 40); g.quadraticCurveTo(60, 48, 50, 42); g.moveTo(28, 62); g.quadraticCurveTo(40, 56, 50, 64); g.moveTo(72, 62); g.quadraticCurveTo(60, 56, 50, 64); g.stroke(); },
  clock(g) { g.beginPath(); g.arc(50, 50, 38, 0, 7); g.stroke(); g.beginPath(); g.moveTo(50, 26); g.lineTo(50, 50); g.lineTo(66, 60); g.stroke(); },
  heart(g) { g.beginPath(); g.moveTo(50, 84); g.bezierCurveTo(10, 56, 8, 22, 32, 18); g.bezierCurveTo(42, 16, 48, 24, 50, 30); g.bezierCurveTo(52, 24, 58, 16, 68, 18); g.bezierCurveTo(92, 22, 90, 56, 50, 84); g.stroke(); },
};
function drawIcon(ctx, name, x, y, size, color, o = {}) {
  ctx.save(); ctx.translate(x - size / 2, y - size / 2); ctx.scale(size / 100, size / 100);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (o.sticker) { ctx.strokeStyle = o.sticker; ctx.fillStyle = o.sticker; ctx.lineWidth = (o.lw || 7) + 14; ICON[name](ctx); }
  ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = o.lw || 7; ICON[name](ctx); ctx.restore();
}

// ---------- word timing ----------
let WORDS = null, PH = [];
function setWords(data) {
  WORDS = data.tokens; PH = [];
  for (const t of WORDS) (PH[t.phrase] = PH[t.phrase] || []).push(t);
}
const P = i => PH[i][0].s;                 // phrase start
const PE = i => PH[i][PH[i].length - 1].e; // phrase end
const Wd = (i, j) => PH[i][j].s;           // word start

// ---------- sfx registry (read by the audio mixer) ----------
const SFX = [];
function sfx(type, t, gain = 1, extra = {}) { SFX.push(Object.assign({ type, t: +t.toFixed(3), gain }, extra)); }

// ---------- frame sources ----------
let CLIPS = {};
const IMG = new Map();
function frameSrc(clip, idx) { return `frames/${clip}/${String(idx + 1).padStart(5, '0')}.jpg`; }
function getImg(src) {
  if (IMG.has(src)) { const hit = IMG.get(src); IMG.delete(src); IMG.set(src, hit); return hit; }
  const p = new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('load ' + src)); i.src = src; });
  p.then(img => { p.img = img; }).catch(() => {});
  IMG.set(src, p);
  if (IMG.size > 260) { const k = IMG.keys().next().value; IMG.delete(k); }
  return p;
}
function clipIndex(shot, t, clip = shot.clip, inSec = shot.in) {
  const n = CLIPS[clip];
  const st = (inSec || 0) + (t - shot.t0) * (shot.speed || 1);
  return clamp(Math.floor(st * FPS), 0, n - 1);
}
function shotFrames(s, t) {
  if (s.split) return s.split.map(h => frameSrc(h.clip, clipIndex(s, t, h.clip, h.in)));
  return s.clip ? [frameSrc(s.clip, clipIndex(s, t))] : [];
}

// ---------- shots (backgrounds) ----------
const small = mk(135, 240), smallG = small.getContext('2d');
function drawBg(ctx, shot, t) {
  const lt = t - shot.t0, dur = shot.t1 - shot.t0, p = clamp(lt / dur);
  if (shot.split) {
    shot.split.forEach((h, k) => {
      const img = IMG.get(frameSrc(h.clip, clipIndex(shot, t, h.clip, h.in)))?.img, s = lerp(1.0, 1.08, E.inOut(p));
      ctx.save(); ctx.beginPath(); ctx.rect(0, k * 960, W, 960); ctx.clip();
      ctx.translate(W / 2, k * 960 + 480); ctx.scale(s, s);
      if (img) ctx.drawImage(img, 0, 480, 1080, 960, -W / 2, -480, W, 960); ctx.restore();
    });
    grade(ctx, 'neutral', 0.1);
    ctx.fillStyle = C.teal; ctx.fillRect(0, 956, W, 8);
    return;
  }
  if (shot.clip) {
    const img = IMG.get(frameSrc(shot.clip, clipIndex(shot, t)))?.img;
    const kb = shot.kb || {}, s = lerp(kb.s0 || 1.04, kb.s1 || 1.12, E.inOut(p));
    const ox = lerp(kb.x0 || 0, kb.x1 || 0, E.inOut(p)), oy = lerp(kb.y0 || 0, kb.y1 || 0, E.inOut(p));
    if (img) {
      if (shot.blur) {
        smallG.drawImage(img, 0, 0, 135, 240);
        ctx.save(); ctx.imageSmoothingQuality = 'high'; ctx.translate(W / 2 + ox, H / 2 + oy); ctx.scale(s * 1.05, s * 1.05); ctx.drawImage(small, -W / 2, -H / 2, W, H); ctx.restore();
      } else {
        ctx.save(); ctx.translate(W / 2 + ox, H / 2 + oy); ctx.scale(s, s); if (shot.flip) ctx.scale(-1, 1); ctx.drawImage(img, -W / 2, -H / 2, W, H); ctx.restore();
      }
    } else { ctx.fillStyle = C.navy; ctx.fillRect(0, 0, W, H); }
    grade(ctx, shot.grade || 'cool', shot.dim || 0);
  } else if (shot.bg === 'paper') {
    ctx.drawImage(TEX.paper, 0, 0, W, H);
    ctx.fillStyle = 'rgba(30,20,10,0.06)'; ctx.fillRect(0, 0, W, H);
    // faint grid like a notebook desk mat
    ctx.strokeStyle = 'rgba(11,27,46,0.06)'; ctx.lineWidth = 2;
    for (let x = 60; x < W; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = 40; y < H; y += 80) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  } else {
    const col = shot.bg === 'amber' ? ['#2A1A0C', '#3D2410'] : [C.navy, C.navy2];
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, col[1]); g.addColorStop(1, col[0]); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // slow drifting light orbs
    for (let k = 0; k < 5; k++) {
      const r = rng(k + 11), x = (r() * W + Math.sin(t * 0.15 + k) * 80), y = (r() * H + Math.cos(t * 0.12 + k * 2) * 120), rad = 260 + r() * 260;
      const rg = ctx.createRadialGradient(x, y, 0, x, y, rad);
      rg.addColorStop(0, shot.bg === 'amber' ? 'rgba(242,166,90,0.10)' : 'rgba(46,196,182,0.09)'); rg.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    }
  }
}
function grade(ctx, look, dim) {
  // legibility gradients for top brand line and caption band
  let g = ctx.createLinearGradient(0, 0, 0, 420); g.addColorStop(0, 'rgba(5,14,26,0.55)'); g.addColorStop(1, 'rgba(5,14,26,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, 420);
  g = ctx.createLinearGradient(0, 1080, 0, H); g.addColorStop(0, 'rgba(5,14,26,0)'); g.addColorStop(0.5, 'rgba(5,14,26,0.45)'); g.addColorStop(1, 'rgba(5,14,26,0.7)'); ctx.fillStyle = g; ctx.fillRect(0, 1080, W, H - 1080);
  ctx.save(); ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = look === 'warm' ? 'rgba(242,166,90,0.28)' : look === 'neutral' ? 'rgba(128,128,128,0.0)' : 'rgba(30,120,140,0.30)';
  ctx.fillRect(0, 0, W, H); ctx.restore();
  if (dim) { ctx.fillStyle = `rgba(6,16,30,${dim})`; ctx.fillRect(0, 0, W, H); }
}

// ---------- transitions ----------
const bufA = mk(W, H), bufB = mk(W, H), gA = bufA.getContext('2d'), gB = bufB.getContext('2d');
function transition(ctx, type, p, dir = 1) {
  const e = E.inOut(p);
  switch (type) {
    case 'fade': ctx.drawImage(bufA, 0, 0); ctx.globalAlpha = e; ctx.drawImage(bufB, 0, 0); ctx.globalAlpha = 1; break;
    case 'flash': ctx.drawImage(p < .5 ? bufA : bufB, 0, 0); ctx.fillStyle = `rgba(255,255,255,${1 - Math.abs(p - .5) * 2})`; ctx.fillRect(0, 0, W, H); break;
    case 'whip': {
      const off = e * W * dir, blurN = 6, amt = Math.sin(p * Math.PI) * 140;
      for (let k = 0; k < blurN; k++) { const d = (k / (blurN - 1) - .5) * amt; ctx.globalAlpha = 1 / (k + 1);
        ctx.drawImage(bufA, -off + d, 0); ctx.drawImage(bufB, W * dir - off + d, 0); }
      ctx.globalAlpha = 1; break;
    }
    case 'zoom': {
      ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(1 + e * 0.5, 1 + e * 0.5); ctx.drawImage(bufA, -W / 2, -H / 2); ctx.restore();
      ctx.save(); ctx.globalAlpha = E.out(p); ctx.translate(W / 2, H / 2); const s = 1.35 - 0.35 * E.out(p); ctx.scale(s, s); ctx.drawImage(bufB, -W / 2, -H / 2); ctx.restore();
      ctx.globalAlpha = 1; break;
    }
    case 'tear': {
      // torn paper edge sweeps upward revealing B underneath
      ctx.drawImage(bufB, 0, 0);
      const y = lerp(H + 80, -120, e), r = rng(5);
      const pts = []; for (let x = -20; x <= W + 20; x += 24) pts.push([x, y + (r() - .5) * 46 + Math.sin(x * 0.02) * 20]);
      ctx.save(); ctx.beginPath(); ctx.moveTo(-20, -20); ctx.lineTo(W + 20, -20); pts.slice().reverse().forEach(([x, yy]) => ctx.lineTo(x, yy)); ctx.closePath(); ctx.clip();
      ctx.drawImage(bufA, 0, -e * 60); ctx.restore();
      ctx.save(); ctx.beginPath(); pts.forEach(([x, yy], i) => (i ? ctx.lineTo(x, yy) : ctx.moveTo(x, yy)));
      pts.slice().reverse().forEach(([x, yy]) => ctx.lineTo(x, yy + 26 + (r() * 10))); ctx.closePath();
      ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 20; ctx.fillStyle = C.paper; ctx.fill(); ctx.restore(); break;
    }
    case 'iris': {
      ctx.drawImage(bufA, 0, 0); ctx.save(); ctx.beginPath(); ctx.arc(W / 2, H * .45, e * 1200, 0, 7); ctx.clip(); ctx.drawImage(bufB, 0, 0); ctx.restore(); break;
    }
    case 'push': {
      ctx.drawImage(bufA, 0, -e * H * 0.25); ctx.save(); ctx.translate(0, (1 - e) * H); ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 40; ctx.drawImage(bufB, 0, 0); ctx.restore(); break;
    }
    default: ctx.drawImage(bufB, 0, 0);
  }
}

// ---------- captions ----------
const CAP = { y: 1330, size: 60, maxW: 820, hl: C.teal };
function drawCaptions(ctx, t, opts) {
  if (opts.hidden) return;
  let cur = -1;
  for (let i = 0; i < PH.length; i++) {
    const s = P(i) - 0.06, nxt = i + 1 < PH.length ? P(i + 1) - 0.06 : 1e9, e = Math.min(PE(i) + 0.55, nxt);
    if (t >= s && t < e) { cur = i; break; }
  }
  if (cur < 0) return;
  const ws = PH[cur], s0 = P(cur) - 0.06, a = E.out(prog(t, s0, 0.12)), hl = opts.hl || CAP.hl;
  const size = CAP.size, o = { font: F.ui, size, weight: 800 };
  const space = measure(ctx, ' ', o) + 14, widths = ws.map(w => measure(ctx, w.text, o));
  // greedy wrap into max 2 lines
  const lines = [[]]; let lw = 0;
  ws.forEach((w, k) => { const add = widths[k] + (lines[lines.length - 1].length ? space : 0);
    if (lw + add > CAP.maxW && lines[lines.length - 1].length) { lines.push([]); lw = 0; } lines[lines.length - 1].push(k); lw += widths[k] + (lines[lines.length - 1].length > 1 ? space : 0); });
  const lh = size * 1.22, y0 = (opts.y || CAP.y) - (lines.length - 1) * lh / 2 + (1 - a) * 18;
  ctx.save(); ctx.globalAlpha = a;
  lines.forEach((ln, li) => {
    const tw = ln.reduce((s, k, j) => s + widths[k] + (j ? space : 0), 0); let x = 540 - tw / 2; const y = y0 + li * lh;
    ln.forEach(k => {
      const w = ws[k], active = t >= w.s - 0.03 && t < w.e + 0.08, said = t >= w.s - 0.03;
      const pop = active ? 1 + 0.10 * Math.sin(Math.PI * clamp((t - w.s) / 0.22)) : 1;
      const col = w.hl ? hl : (said ? C.white : 'rgba(255,255,255,0.92)');
      withT(ctx, x + widths[k] / 2, y, 0, pop, () => {
        if (active && w.hl) { ctx.fillStyle = 'rgba(11,27,46,0.55)'; rrect(ctx, -widths[k] / 2 - 12, -size * 0.62, widths[k] + 24, size * 1.2, 14); ctx.fill(); }
        txt(ctx, w.text, 0, 0, Object.assign({}, o, { color: col, stroke: 'rgba(8,18,32,0.92)', strokeW: 13 }));
      });
      x += widths[k] + space;
    });
  });
  ctx.restore();
}

// ---------- timeline + render loop ----------
let TL = null;
async function init() {
  buildTextures();
  const [words, clips] = await Promise.all([fetch('data/words.json').then(r => r.json()), fetch('data/clips.json').then(r => r.json())]);
  setWords(words); CLIPS = clips;
  await Promise.all(['Anton', 'DM Serif Display', 'Plus Jakarta Sans', 'Caveat', 'JetBrains Mono'].flatMap(f =>
    [400, 500, 600, 700, 800].map(w => document.fonts.load(`${w} 40px '${f}'`))));
  await document.fonts.ready;
  TL = buildTimeline();   // defined in timeline.js
  TL.shots.sort((a, b) => a.t0 - b.t0);
  TL.els.sort((a, b) => (a.z || 0) - (b.z || 0));
  window.SFX = SFX; window.DURATION = TL.duration;
  return { duration: TL.duration, sfx: SFX };
}
function activeShots(t) {
  const sh = TL.shots; let i = sh.findIndex(s => t >= s.t0 && t < s.t1);
  if (i < 0) i = t < sh[0].t0 ? 0 : sh.length - 1;
  const cur = sh[i], tr = cur.tr;
  if (tr && i > 0 && t < cur.t0 + tr.dur) return { cur, prev: sh[i - 1], p: (t - cur.t0) / tr.dur, tr };
  return { cur };
}
function needed(t) {
  const a = activeShots(t), list = [];
  for (const s of [a.cur, a.prev]) if (s) list.push(...shotFrames(s, t));
  return list;
}
async function renderFrame(t) {
  await Promise.all(needed(t).map(getImg));
  for (let k = 1; k <= 6; k++) needed(t + k / FPS).forEach(getImg); // prefetch
  const cv = document.getElementById('c'), ctx = cv.getContext('2d');
  const a = activeShots(t);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  if (a.prev) {
    gA.save(); drawBg(gA, a.prev, t); gA.restore(); gB.save(); drawBg(gB, a.cur, t); gB.restore();
    transition(ctx, a.tr.type, clamp(a.p), a.tr.dir || 1);
  } else { ctx.save(); drawBg(ctx, a.cur, t); ctx.restore(); }
  for (const el of TL.els) {
    if (t < el.t0 || t >= el.t1) continue;
    ctx.save(); el.draw(ctx, t); ctx.restore();
  }
  drawCaptions(ctx, t, TL.captionOpts(t));
  if (TL.top) { ctx.save(); TL.top(ctx, t); ctx.restore(); }
  // grain + vignette on everything
  ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.10;
  ctx.drawImage(TEX.grain[Math.floor(t * FPS) % TEX.grain.length], 0, 0, W, H); ctx.restore();
  ctx.drawImage(TEX.vignette, 0, 0);
  return cv.toDataURL('image/jpeg', 0.93);
}
window.init = init; window.renderFrame = renderFrame;
