// Overlay element factories. Each returns {t0, t1, z, draw(ctx, t)} and registers its own SFX.
'use strict';

// Big stacked kinetic headline. lines: [{text, at, size, color, font, mark, y, x, align, rot}]
function headline(lines, t1, o = {}) {
  const t0 = Math.min(...lines.map(l => l.at)) - 0.05;
  lines.forEach(l => { sfx(l.sfx || (l.size >= 120 ? 'thock' : 'tap'), l.at, l.gain || 0.8); if (l.mark) sfx('marker', l.at + 0.12, 0.8); });
  return { t0, t1: t1 + 0.35, z: o.z || 5, draw(ctx, t) {
    const out = E.in(prog(t, t1, 0.3));
    lines.forEach(l => {
      const p = prog(t, l.at, l.dur || 0.42); if (p <= 0) return;
      const f = l.font || F.head, size = l.size || 120, x = l.x ?? 540, y = l.y;
      const w = measure(ctx, l.text, { font: f, size, weight: l.weight || 400, track: l.track || 0 });
      ctx.save(); ctx.globalAlpha = 1 - out;
      ctx.translate(x, y - out * 40); ctx.rotate(l.rot || 0);
      const s = lerp(l.from || 1.35, 1, E.back(p)); ctx.scale(s, s);
      if (l.mark) { // marker swipe behind the line, sized from the real glyph box
        font(ctx, f, size, l.weight || 400); ctx.textBaseline = 'middle';
        const m = ctx.measureText(l.text), asc = m.actualBoundingBoxAscent, desc = m.actualBoundingBoxDescent;
        const mp = E.out(prog(t, l.at + 0.12, 0.35)), al = l.align === 'left' ? 0 : -w / 2;
        ctx.fillStyle = l.mark; ctx.beginPath(); const r = rng(Math.round(l.at * 100));
        const top = size * 0.04 - asc - 16, bot = size * 0.04 + desc + 16, mx = al - 22, mw = (w + 44) * mp;
        ctx.moveTo(mx, top + r() * 6); ctx.lineTo(mx + mw, top + r() * 8); ctx.lineTo(mx + mw - 6, bot - r() * 6); ctx.lineTo(mx + 4, bot); ctx.closePath(); ctx.fill();
      }
      ctx.globalAlpha *= E.out(p);
      txt(ctx, l.text, 0, size * 0.04, { font: f, size, weight: l.weight || 400, color: l.color || C.white, align: l.align || 'center',
        track: l.track || 0, stroke: l.stroke, strokeW: l.strokeW, shadow: l.noShadow ? null : 'rgba(0,0,0,0.45)', shadowBlur: 24 });
      ctx.restore();
    });
  } };
}

// rubber stamp that slams in
function stamp(text, at, t1, o = {}) {
  sfx('stamp', at, o.gain || 1); sfx('thud', at + 0.02, 0.7);
  const size = o.size || 110, col = o.color || C.coral;
  return { t0: at, t1: t1 + 0.3, z: o.z || 8, draw(ctx, t) {
    const p = prog(t, at, 0.28), out = prog(t, t1, 0.3);
    const w = measure(ctx, text, { font: F.head, size, track: 4 }) + 70, h = size * 1.3;
    withT(ctx, o.x ?? 540, o.y ?? 860, (o.rot ?? -0.12), lerp(2.2, 1, E.out(p)) * (1 + 0.04 * Math.sin(Math.PI * clamp((t - at - 0.28) / 0.2))), () => {
      ctx.globalAlpha = Math.min(E.out(p * 1.6), 1 - out);
      ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = 12; rrect(ctx, -w / 2, -h / 2, w, h, 16); ctx.stroke();
      ctx.lineWidth = 4; rrect(ctx, -w / 2 + 14, -h / 2 + 14, w - 28, h - 28, 10); ctx.stroke();
      txt(ctx, text, 0, 6, { font: F.head, size, color: col, track: 4 });
      ctx.globalCompositeOperation = 'destination-out'; ctx.drawImage(TEX.speckle, -w / 2, -h / 2, w, h); ctx.restore();
    });
  } };
}

// paper card with arbitrary content; content(ctx, t, w, h) draws in card-local coords (0,0 top-left)
function card(o) {
  const at = o.at, t1 = o.t1, w = o.w, h = o.h, x = o.x ?? (540 - w / 2), y = o.y;
  if (o.sfx !== 'none') sfx(o.sfx || 'paper', at, o.gain || 0.8);
  if (o.from !== 'pop') sfx('swish', at - 0.05, 0.6);
  const from = o.from || 'bottom';
  return { t0: at, t1: t1 + 0.4, z: o.z || 4, draw(ctx, t) {
    const p = E.back(prog(t, at, o.din || 0.5)), out = E.in(prog(t, t1, 0.35));
    let dx = 0, dy = 0; const far = 1400;
    if (from === 'bottom') dy = (1 - p) * far; else if (from === 'top') dy = -(1 - p) * far;
    else if (from === 'left') dx = -(1 - p) * far; else if (from === 'right') dx = (1 - p) * far;
    else if (from === 'pop') { /* scale handled below */ }
    const exitDx = (o.exit === 'left' ? -1 : o.exit === 'right' ? 1 : 0) * out * 1300, exitDy = (o.exit ? 0 : 1) * out * 1500;
    const rot = (o.rot || 0) + (1 - p) * (o.spin ?? 0.25) * (from === 'left' ? -1 : 1);
    const sc = from === 'pop' ? lerp(0.3, 1, p) : 1, bob = Math.sin((t - at) * 1.3) * 3;
    withT(ctx, x + w / 2 + dx + exitDx, y + h / 2 + dy + exitDy + bob, rot, sc, () => {
      ctx.translate(-w / 2, -h / 2);
      drawPaper(ctx, 0, 0, w, h, { color: o.color, torn: o.torn ?? 10, tornSides: o.tornSides || 'tb', seed: o.seed || Math.round(at * 10), flat: o.flat });
      if (o.tape !== false) { tape(ctx, w / 2 - 10, -8, 170, -0.05); }
      if (o.content) { ctx.save(); o.content(ctx, t, w, h); ctx.restore(); }
    });
  } };
}

// rounded label chip
function chip(text, at, t1, o = {}) {
  sfx(o.icon ? 'bubble' : 'pop', at, o.gain || 0.75);
  const size = o.size || 42;
  return { t0: at, t1: t1 + 0.3, z: o.z || 6, draw(ctx, t) {
    const p = E.back(prog(t, at, 0.32)), out = prog(t, t1, 0.25);
    const tw = measure(ctx, text, { font: F.ui, size, weight: 800 }), isz = size * 1.1, iw = o.icon ? isz + 16 : 0, w = tw + 60 + iw, h = size * 1.75;
    withT(ctx, o.x ?? 540, o.y, o.rot || 0, p * (1 - out * 0.3), () => {
      ctx.globalAlpha = 1 - out;
      ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6;
      ctx.fillStyle = o.bg || C.teal; rrect(ctx, -w / 2, -h / 2, w, h, h / 2); ctx.fill(); ctx.shadowColor = 'transparent';
      if (o.icon) drawIcon(ctx, o.icon, -w / 2 + 30 + isz / 2, 0, isz, o.fg || C.navy, { lw: 9 });
      txt(ctx, text, -w / 2 + 30 + iw, 2, { font: F.ui, size, weight: 800, color: o.fg || C.navy, align: 'left' });
    });
  } };
}

// sticker icon with white outline
function sticker(name, at, t1, o = {}) {
  sfx('pop', at, o.gain || 0.7); sfx('shimmer', at + 0.06, 0.6);
  return { t0: at, t1: t1 + 0.3, z: o.z || 7, draw(ctx, t) {
    const p = E.back(prog(t, at, 0.36)), out = prog(t, t1, 0.25), wob = Math.sin((t - at) * 3) * 0.05;
    withT(ctx, o.x, o.y + Math.sin((t - at) * 2) * 6, (o.rot || 0) + wob, p * (1 - out), () => {
      ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 6;
      if (o.disc) { ctx.fillStyle = o.disc; ctx.beginPath(); ctx.arc(0, 0, o.size * 0.62, 0, 7); ctx.fill(); ctx.shadowColor = 'transparent'; }
      drawIcon(ctx, name, 0, 0, o.size || 120, o.color || C.navy, { sticker: o.disc ? null : C.white, lw: o.lw || 8 });
    });
  } };
}

// hand-drawn ellipse / underline / arrow / cross-out
function scribble(kind, at, t1, o = {}) {
  sfx('scribble', at, o.gain || 0.6, { dur: o.dur || 0.45 });
  let pts;
  if (kind === 'circle') { pts = []; const r = rng(Math.round(at * 77));
    for (let k = 0; k <= 46; k++) { const a = -0.6 + (k / 40) * Math.PI * 2; const j = 1 + (r() - .5) * 0.06;
      pts.push([o.x + Math.cos(a) * o.rx * j, o.y + Math.sin(a) * o.ry * j]); } }
  else if (kind === 'underline') pts = roughLine([[o.x, o.y], [o.x + o.w * 0.5, o.y + 6], [o.x + o.w, o.y - 4]], Math.round(at * 33), 4, 10);
  else if (kind === 'strike') pts = roughLine([[o.x, o.y + 8], [o.x + o.w, o.y - 8]], Math.round(at * 13), 3, 10);
  else if (kind === 'arrow') { const [x1, y1, x2, y2] = o.pts; const a = Math.atan2(y2 - y1, x2 - x1), hl = 34;
    pts = roughLine([[x1, y1], [(x1 + x2) / 2 + (o.bend || 0), (y1 + y2) / 2 - (o.bend || 0)], [x2, y2]], Math.round(at * 9), 3, 10)
      .concat([[x2 - hl * Math.cos(a - 0.5), y2 - hl * Math.sin(a - 0.5)], [x2, y2], [x2 - hl * Math.cos(a + 0.5), y2 - hl * Math.sin(a + 0.5)]]); }
  else if (kind === 'question') { pts = []; for (let k = 0; k <= 30; k++) { const a = Math.PI * 1.1 - (k / 30) * Math.PI * 1.55; pts.push([o.x + Math.cos(a) * 70, o.y - 80 + Math.sin(a) * 70]); }
    pts.push([o.x + 4, o.y + 20]); pts.push([o.x + 2, o.y + 60]); }
  return { t0: at, t1: t1 + 0.25, z: o.z || 9, draw(ctx, t) {
    const p = E.out(prog(t, at, o.dur || 0.45)), out = prog(t, t1, 0.25);
    ctx.globalAlpha = 1 - out; ctx.strokeStyle = o.color || C.coral; ctx.lineWidth = o.lw || 10; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    partialPath(ctx, pts, p);
    if (kind === 'question' && p >= 1) { ctx.fillStyle = o.color || C.coral; ctx.beginPath(); ctx.arc(o.x + 2, o.y + 105, 10, 0, 7); ctx.fill(); }
  } };
}

// typewriter line
function typewriter(text, at, t1, o = {}) {
  const cps = o.cps || 28; sfx('type', at, o.gain || 0.5, { dur: text.length / cps });
  return { t0: at, t1: t1 + 0.25, z: o.z || 6, draw(ctx, t) {
    const n = Math.floor((t - at) * cps), out = prog(t, t1, 0.25); if (n <= 0) return;
    ctx.globalAlpha = 1 - out; const s = text.slice(0, n);
    txt(ctx, s, o.x, o.y, { font: o.font || F.mono, size: o.size || 40, weight: o.weight || 700, color: o.color || C.navy, align: o.align || 'left' });
    if (n < text.length && Math.floor(t * 4) % 2 === 0) { const w = measure(ctx, s, { font: o.font || F.mono, size: o.size || 40, weight: o.weight || 700 });
      ctx.fillStyle = o.color || C.navy; ctx.fillRect((o.align === 'center' ? o.x + w / 2 : o.x + w) + 4, o.y - (o.size || 40) * .45, 4, (o.size || 40) * .9); }
  } };
}

// handwritten note that wipes on left->right
function hand(text, at, t1, o = {}) {
  sfx('scribble', at, (o.gain || 0.4), { dur: 0.5 });
  return { t0: at, t1: t1 + 0.25, z: o.z || 9, draw(ctx, t) {
    const p = E.out(prog(t, at, o.dur || 0.6)), out = prog(t, t1, 0.25), size = o.size || 72;
    const w = measure(ctx, text, { font: F.hand, size, weight: 700 }), x0 = (o.align === 'left' ? o.x : o.x - w / 2);
    withT(ctx, 0, 0, 0, 1, () => { ctx.translate(o.x, o.y); ctx.rotate(o.rot || 0); ctx.translate(-o.x, -o.y);
      ctx.beginPath(); ctx.rect(x0 - 20, o.y - size, (w + 40) * p, size * 2); ctx.clip(); ctx.globalAlpha = 1 - out;
      txt(ctx, text, o.x, o.y, { font: F.hand, size, weight: 700, color: o.color || C.yellow, align: o.align || 'center', shadow: o.shadow === false ? null : 'rgba(0,0,0,0.5)', shadowBlur: 10 }); });
  } };
}

// persistent brand lockup (top-left, inside TikTok safe area)
function brandBug(t0, t1) {
  return { t0, t1, z: 20, draw(ctx, t) {
    const a = Math.min(prog(t, t0, 0.6), 1 - prog(t, t1 - 0.4, 0.4)) * 0.92; if (a <= 0) return; ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(11,27,46,0.55)'; rrect(ctx, 62, 140, 480, 56, 28); ctx.fill();
    ctx.fillStyle = C.teal; ctx.beginPath(); ctx.arc(86, 168, 9, 0, 7); ctx.fill();
    txt(ctx, 'DR AZREN', 108, 168, { font: F.ui, size: 30, weight: 800, align: 'left', color: C.white, track: 3, shadow: 'rgba(0,0,0,0.5)', shadowBlur: 8 });
    txt(ctx, 'Spread Positivity', 290, 169, { font: F.serif, size: 28, style: 'italic', weight: 400, align: 'left', color: 'rgba(255,255,255,0.85)', shadow: 'rgba(0,0,0,0.5)', shadowBlur: 8 });
  } };
}
// chapter chip top-right e.g. "01/03"
function chapter(label, sub, t0, t1) {
  sfx('click', t0, 0.5);
  return { t0, t1, z: 19, draw(ctx, t) {
    const p = E.out(prog(t, t0, 0.4)), out = prog(t, t1 - 0.3, 0.3); ctx.globalAlpha = Math.min(p, 1 - out);
    const w = measure(ctx, sub, { font: F.mono, size: 24, weight: 700 }) + 120;
    withT(ctx, 1000 - w / 2 + (1 - p) * 60, 168, 0, 1, () => {
      ctx.fillStyle = 'rgba(11,27,46,0.78)'; rrect(ctx, -w / 2, -26, w, 52, 26); ctx.fill();
      ctx.fillStyle = C.teal; rrect(ctx, -w / 2, -26, 82, 52, 26); ctx.fill();
      txt(ctx, label, -w / 2 + 41, 1, { font: F.mono, size: 26, weight: 700, color: C.navy });
      txt(ctx, sub, -w / 2 + 96, 1, { font: F.mono, size: 24, weight: 700, color: C.white, align: 'left' });
    });
  } };
}

// ---------- infographics ----------

// month calendar where daily pills appear, some days missed (X)
function calendarGrid(o) {
  const at = o.at, t1 = o.t1, missed = new Set(o.missed || []);
  sfx('paper', at, 0.8);
  for (let d = 0; d < 28; d++) { const tt = o.fillAt + d * o.step; if (missed.has(d)) sfx('scribble', tt, 0.35, { dur: 0.2 }); else if (d % 2 === 0) sfx('pill', tt, 0.35); }
  return card({ at, t1, x: 90, y: o.y || 330, w: 900, h: 940, rot: -0.02, from: 'bottom', seed: 3, sfx: 'none', content(ctx, t, w, h) {
    txt(ctx, o.title || 'UBAT HARI-HARI', w / 2, 82, { font: F.head, size: 64, color: C.navy, track: 2 });
    const days = ['I', 'S', 'R', 'K', 'J', 'S', 'A'], cw = 112, x0 = (w - cw * 7) / 2 + cw / 2, y0 = 170;
    days.forEach((d, i) => txt(ctx, d, x0 + i * cw, y0, { font: F.mono, size: 28, weight: 700, color: C.mute }));
    for (let d = 0; d < 28; d++) {
      const cx = x0 + (d % 7) * cw, cy = y0 + 70 + Math.floor(d / 7) * 150, tt = o.fillAt + d * o.step, p = prog(t, tt, 0.25);
      ctx.strokeStyle = 'rgba(11,27,46,0.15)'; ctx.lineWidth = 2; rrect(ctx, cx - 50, cy - 10, 100, 130, 12); ctx.stroke();
      txt(ctx, String(d + 1), cx - 30, cy + 12, { font: F.mono, size: 22, weight: 500, color: C.mute });
      if (p > 0) {
        if (missed.has(d)) { ctx.strokeStyle = C.red; ctx.lineWidth = 9; ctx.lineCap = 'round'; const e = E.out(p);
          ctx.beginPath(); ctx.moveTo(cx - 28, cy + 30); ctx.lineTo(cx - 28 + 56 * e, cy + 30 + 66 * e); ctx.stroke();
          if (e > .5) { const e2 = (e - .5) * 2; ctx.beginPath(); ctx.moveTo(cx + 28, cy + 30); ctx.lineTo(cx + 28 - 56 * e2, cy + 30 + 66 * e2); ctx.stroke(); } }
        else withT(ctx, cx, cy + 64, 0, E.back(p), () => drawIcon(ctx, 'capsule', 0, 0, 74, C.tealD, { lw: 10 }));
      }
    }
    if (o.note) { const q = E.out(prog(t, o.noteAt ?? at, 0.4)); ctx.globalAlpha = q; withT(ctx, w / 2, h - 48, -0.03, lerp(1.3, 1, q), () =>
      txt(ctx, o.note, 0, 0, { font: F.hand, size: 66, weight: 700, color: C.red })); ctx.globalAlpha = 1; }
  } });
}

// plasma level concept graph
function plasmaGraph(o) {
  const at = o.at, t1 = o.t1, gx = 110, gy = 250, gw = 690, gh = 430;
  sfx('paper', at, 0.8); sfx('scribble', o.oralAt, 0.4, { dur: 1.2 }); sfx('riser', o.depotAt, 0.6); sfx('ding', o.consistAt || o.depotAt + 1, 0.5);
  // oral: daily peaks with two missed doses (troughs); depot: smooth gentle wave
  const oral = u => { const day = u * 14, k = Math.floor(day), f = day - k, miss = k === 5 || k === 6 || k === 10;
    let base = 0.55; if (k >= 6 && k <= 7) base = 0.32; if (k === 7) base = 0.22; if (k === 11) base = 0.38;
    return miss ? base * (1 - f * 0.25) : base + 0.32 * Math.exp(-f * 3.2) * (1 - Math.exp(-f * 25)); };
  const depot = u => 0.52 + 0.06 * Math.sin(u * Math.PI * 2 * 1.1 - 1.2);
  return card({ at, t1, x: 90, y: o.y || 300, w: 900, h: 900, rot: 0.015, from: 'right', seed: 9, sfx: 'none', content(ctx, t, w, h) {
    txt(ctx, 'PARAS UBAT DALAM BADAN', w / 2, 92, { font: F.head, size: 58, color: C.navy, track: 2 });
    txt(ctx, 'Ilustrasi konsep', w / 2, 150, { font: F.serif, style: 'italic', size: 34, color: C.mute });
    ctx.strokeStyle = C.navy; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + gh); ctx.lineTo(gx + gw, gy + gh); ctx.stroke();
    txt(ctx, 'masa (minggu)', gx + gw, gy + gh + 40, { font: F.mono, size: 24, weight: 500, color: C.mute, align: 'right' });
    // band of "steady" range
    ctx.fillStyle = 'rgba(46,196,182,0.12)'; ctx.fillRect(gx + 4, gy + gh * 0.36, gw - 4, gh * 0.18);
    const plot = (fn, p, col, lw, dash) => { ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.setLineDash(dash || []); ctx.lineJoin = 'round'; ctx.beginPath();
      const N = 280; for (let i = 0; i <= N * p; i++) { const u = i / N, X = gx + 6 + u * (gw - 10), Y = gy + gh - fn(u) * gh; i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); } ctx.stroke(); ctx.restore(); };
    const po = E.inOut(prog(t, o.oralAt, 1.6)), pd = E.inOut(prog(t, o.depotAt, 1.4));
    plot(oral, po, C.coral, 6, [14, 10]); plot(depot, pd, C.tealD, 10);
    const lp = prog(t, o.oralAt + 0.6, 0.4), lq = prog(t, o.depotAt + 0.6, 0.4);
    ctx.globalAlpha = lp; drawIcon(ctx, 'capsule', 150, gy + gh + 110, 52, C.coral, { lw: 10 });
    txt(ctx, 'Pil harian (bila terlupa dos)', 190, gy + gh + 112, { font: F.ui, size: 32, weight: 700, color: C.coral, align: 'left' });
    ctx.globalAlpha = lq; drawIcon(ctx, 'syringe', 150, gy + gh + 180, 54, C.tealD, { lw: 9 });
    txt(ctx, 'Depot injection', 190, gy + gh + 182, { font: F.ui, size: 32, weight: 800, color: C.tealD, align: 'left' });
    ctx.globalAlpha = 1;
    if (o.consistAt && t > o.consistAt) { const p = E.back(prog(t, o.consistAt, 0.35));
      withT(ctx, gx + gw - 120, gy + gh * 0.28, -0.08, p, () => { ctx.fillStyle = C.teal; rrect(ctx, -150, -36, 300, 72, 36); ctx.fill();
        txt(ctx, 'LEBIH KONSISTEN', 0, 2, { font: F.ui, size: 30, weight: 800, color: C.navy }); }); }
  } });
}

// periodic injection strip (no fixed interval stated: "berkala")
function injectionStrip(o) {
  const at = o.at, t1 = o.t1;
  [0, 1, 2, 3].forEach(k => sfx('bubble', o.markAt + k * 0.32, 0.6));
  return card({ at, t1, x: 90, y: o.y || 420, w: 900, h: 560, rot: -0.015, from: 'left', seed: 21, content(ctx, t, w, h) {
    txt(ctx, 'SECARA BERKALA', w / 2, 90, { font: F.head, size: 74, color: C.navy, track: 2 });
    const x0 = 80, x1 = w - 80, y = 270, p = E.inOut(prog(t, at + 0.3, 1.2));
    ctx.strokeStyle = C.navy; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(lerp(x0, x1, p), y); ctx.stroke();
    for (let i = 0; i <= 12; i++) { const X = lerp(x0, x1, i / 12); if (X > lerp(x0, x1, p)) break; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(X, y - 12); ctx.lineTo(X, y + 12); ctx.stroke(); }
    [0, 1, 2, 3].forEach(k => { const X = lerp(x0 + 40, x1 - 40, k / 3), q = E.back(prog(t, o.markAt + k * 0.32, 0.35));
      if (q > 0) withT(ctx, X, y - 70, 0, q, () => { ctx.fillStyle = C.teal; ctx.beginPath(); ctx.arc(0, 0, 46, 0, 7); ctx.fill(); drawIcon(ctx, 'syringe', 0, 0, 58, C.navy, { lw: 10 }); }); });
    const q = prog(t, o.noteAt, 0.4);
    if (q > 0) { ctx.globalAlpha = q; txt(ctx, 'ikut dos & keadaan pesakit', w / 2, 420, { font: F.hand, size: 64, weight: 700, color: C.tealD }); ctx.globalAlpha = 1; }
  } });
}

// clipboard checklist; items: [{text, sub, at}]
function checklist(o) {
  o.items.forEach(it => { sfx('check', it.at, 0.8); sfx('ding', it.at + 0.12, 0.45); });
  return card({ at: o.at, t1: o.t1, x: 80, y: o.y || 300, w: 920, h: o.h || 900, rot: -0.01, from: 'bottom', seed: 33, tape: false, content(ctx, t, w, h) {
    ctx.fillStyle = '#9C7A54'; rrect(ctx, w / 2 - 120, -28, 240, 64, 14); ctx.fill(); ctx.fillStyle = '#C9C9C9'; rrect(ctx, w / 2 - 80, -40, 160, 36, 10); ctx.fill();
    txt(ctx, o.title || 'PERLU DIPANTAU', w / 2, 100, { font: F.head, size: 66, color: C.navy, track: 2 });
    o.items.forEach((it, k) => {
      const y = 220 + k * (o.gap || 160), p = prog(t, it.at, 0.35);
      ctx.strokeStyle = C.navy; ctx.lineWidth = 5; rrect(ctx, 70, y - 34, 68, 68, 10); ctx.stroke();
      if (p > 0) { ctx.save(); ctx.strokeStyle = C.coral; ctx.lineWidth = 11; ctx.lineCap = 'round'; partialPath(ctx, [[82, y], [102, y + 22], [150, y - 40]], E.out(p)); ctx.restore();
        ctx.globalAlpha = E.out(p);
        txt(ctx, it.text, 175, y - (it.sub ? 14 : 0), { font: F.ui, size: 46, weight: 800, color: C.navy, align: 'left' });
        if (it.sub) txt(ctx, it.sub, 177, y + 36, { font: F.ui, size: 36, weight: 700, color: '#4E6378', align: 'left' });
        ctx.globalAlpha = 1; }
    });
  } });
}

// drug index card: big number, brand name, generic name
function drugCard(n, brand, generic, at, t1, o = {}) {
  sfx('whoosh', at - 0.15, 0.7);
  return card({ at, t1, x: 90, y: o.y || 360, w: 900, h: 640, rot: o.rot ?? -0.025, from: o.from || 'right', seed: 40 + n, exit: o.exit || 'left', content(ctx, t, w, h) {
    ctx.fillStyle = C.navy; rrect(ctx, 0, 0, 230, h, 0); ctx.fill();
    txt(ctx, String(n).padStart(2, '0'), 115, 150, { font: F.head, size: 170, color: C.teal });
    txt(ctx, 'DEPOT', 115, 290, { font: F.mono, size: 30, weight: 700, color: C.paper, track: 6 });
    drawIcon(ctx, 'syringe', 115, 440, 120, C.paper, { lw: 7 });
    const p1 = E.out(prog(t, o.brandAt ?? at + 0.2, 0.4)), p2 = E.out(prog(t, o.genAt ?? at + 0.8, 0.4));
    ctx.globalAlpha = p1; txt(ctx, 'GENERASI PERTAMA', 280, 120, { font: F.mono, size: 26, weight: 700, color: C.tealD, align: 'left', track: 3 });
    const bsize = measure(ctx, brand, { font: F.serif, size: 92 }) > 560 ? 78 : 92;
    txt(ctx, brand, 280 + (1 - p1) * 40, 230, { font: F.serif, size: bsize, color: C.navy, align: 'left' });
    ctx.globalAlpha = p2; ctx.fillStyle = 'rgba(11,27,46,0.12)'; ctx.fillRect(280, 320, 560, 3);
    txt(ctx, generic[0], 280 + (1 - p2) * 40, 400, { font: F.mono, size: 40, weight: 700, color: C.navy, align: 'left' });
    txt(ctx, generic[1], 280 + (1 - p2) * 40, 456, { font: F.mono, size: 40, weight: 500, color: C.mute, align: 'left' });
    ctx.globalAlpha = 1;
  } });
}

// "A ≠ B" comparison card
function vsCard(o) {
  sfx('paper', o.at, 0.8); sfx('stamp', o.neqAt, 0.9);
  return card({ at: o.at, t1: o.t1, x: 90, y: 330, w: 900, h: 860, rot: 0.01, from: 'bottom', seed: 51, content(ctx, t, w, h) {
    txt(ctx, 'JANGAN CONFUSED!', w / 2, 96, { font: F.head, size: 76, color: C.coral, track: 2 });
    const box = (y, a, b, col) => { ctx.fillStyle = col; rrect(ctx, 80, y, w - 160, 190, 22); ctx.fill();
      txt(ctx, a, w / 2, y + 78, { font: F.serif, size: 70, color: C.paper }); txt(ctx, b, w / 2, y + 146, { font: F.mono, size: 30, weight: 700, color: 'rgba(244,239,230,0.8)', track: 4 }); };
    box(190, 'Clopixol', 'DEPOT', C.navy);
    const pb = E.out(prog(t, o.bAt, 0.4)); ctx.globalAlpha = pb; box(560, 'Clopixol', 'ACUPHASE', C.tealD); ctx.globalAlpha = 1;
    const q = E.back(prog(t, o.neqAt, 0.3));
    if (q > 0) withT(ctx, w / 2, 470, 0, q, () => { ctx.fillStyle = C.coral; ctx.beginPath(); ctx.arc(0, 0, 70, 0, 7); ctx.fill(); txt(ctx, '≠', 0, 4, { font: F.ui, size: 110, weight: 800, color: C.white }); });
    const r = prog(t, o.noteAt, 0.4); if (r > 0) { ctx.globalAlpha = r; txt(ctx, 'dua benda yang berbeza', w / 2, 800, { font: F.hand, size: 58, weight: 700, color: C.coral }); }
  } });
}

// end card overlay (drawn above captions)
function endCard(at, dur) {
  sfx('riser', at - 0.9, 0.7); sfx('logo', at + 0.2, 0.9); sfx('chime', at + 0.6, 0.6); sfx('shimmer', at + 0.95, 0.5);
  return function (ctx, t) {
    const p = prog(t, at, 0.6); if (p <= 0) return;
    ctx.globalAlpha = E.out(p); const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, C.navy2); g.addColorStop(1, C.navy); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    for (let k = 0; k < 4; k++) { const r = rng(k + 3), x = r() * W, y = r() * H, rad = 320 + r() * 200; const rg = ctx.createRadialGradient(x, y, 0, x, y, rad);
      rg.addColorStop(0, 'rgba(46,196,182,0.12)'); rg.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H); }
    const a = E.back(prog(t, at + 0.2, 0.6)), b = E.out(prog(t, at + 0.55, 0.5)), c = E.out(prog(t, at + 0.9, 0.5));
    withT(ctx, 540, 760, 0, a, () => { ctx.strokeStyle = C.teal; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(0, 0, 92, 0, 7); ctx.stroke();
      drawIcon(ctx, 'heart', 0, 6, 104, C.teal, { lw: 8 }); });
    ctx.globalAlpha = b; txt(ctx, 'Dr Azren', 540, 960, { font: F.serif, size: 112, color: C.paper });
    txt(ctx, 'SPREAD POSITIVITY', 540, 1050, { font: F.mono, size: 34, weight: 700, color: C.teal, track: 10 });
    ctx.globalAlpha = c; ctx.fillStyle = 'rgba(244,239,230,0.25)'; ctx.fillRect(390, 1110, 300, 2);
    txt(ctx, 'Psikiatri & Pendidikan Kesihatan Mental', 540, 1170, { font: F.ui, size: 36, weight: 600, color: 'rgba(244,239,230,0.85)' });
    txt(ctx, 'Kandungan ini untuk pendidikan. Rawatan perlu', 540, 1330, { font: F.ui, size: 30, weight: 500, color: 'rgba(244,239,230,0.6)' });
    txt(ctx, 'disesuaikan oleh doktor anda.', 540, 1374, { font: F.ui, size: 30, weight: 500, color: 'rgba(244,239,230,0.6)' });
    ctx.globalAlpha = 1;
  };
}
