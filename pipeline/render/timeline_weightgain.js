// Edit decision list for "10 Ubat Psikiatri & Kenaikan Berat Badan" (Dr Azren, ElevenLabs voice clone).
// P(i) = start of caption phrase i, Wd(i, j) = start of word j in phrase i (projects/weight_gain/captions.srt).
// Load this file instead of timeline.js (index_weightgain.html).
'use strict';

const CTA_LOCATION = 'Nilai';
const BOOK = new Image(), BOOK3D = new Image();
const loadImg = (img, src) => new Promise(res => { img.onload = res; img.onerror = res; img.src = src; });
window.PRELOAD = () => Promise.all([loadImg(BOOK, 'book.jpg'), loadImg(BOOK3D, 'book3d.jpg')]);

const CLS = {
  ap: { label: 'ANTIPSIKOTIK', col: C.teal },
  ad: { label: 'ANTIDEPRESAN', col: C.amber },
  ms: { label: 'PENSTABIL MOOD', col: C.coral },
};

function scrim(at, t1, alpha = 0.5) {
  return { t0: at, t1: t1 + 0.3, z: 1, draw(ctx, t) { const a = Math.min(prog(t, at, 0.35), 1 - prog(t, t1, 0.3)) * alpha;
    ctx.fillStyle = `rgba(6,16,30,${a})`; ctx.fillRect(0, 0, W, H); } };
}

// drug title card: big index, generic name, class tag, optional brand line
function drugIntro(n, name, cls, at, t1, o = {}) {
  sfx('whoosh', at - 0.15, 0.7);
  const c = CLS[cls];
  return card({ at, t1, x: 90, y: o.y || 420, w: 900, h: 560, rot: o.rot ?? -0.02, from: o.from || 'right', seed: 140 + n, exit: 'left', content(ctx, t, w, h) {
    ctx.fillStyle = C.navy; ctx.fillRect(0, 0, 250, h);
    txt(ctx, String(n).padStart(2, '0'), 125, 210, { font: F.head, size: 190, color: c.col });
    txt(ctx, '/ 10', 125, 360, { font: F.mono, size: 40, weight: 700, color: C.paper, track: 4 });
    const p1 = E.out(prog(t, at + 0.15, 0.4)), p2 = E.out(prog(t, at + 0.5, 0.4));
    ctx.globalAlpha = p2; ctx.fillStyle = c.col; const tw = measure(ctx, c.label, { font: F.mono, size: 30, weight: 700, track: 3 });
    rrect(ctx, 300, 92, tw + 48, 60, 30); ctx.fill();
    txt(ctx, c.label, 324, 123, { font: F.mono, size: 30, weight: 700, color: C.navy, align: 'left', track: 3 });
    ctx.globalAlpha = p1;
    const nw = measure(ctx, name, { font: F.serif, size: 100 }), size = nw > 560 ? Math.floor(100 * 560 / nw) : 100;
    txt(ctx, name, 300 + (1 - p1) * 40, 270, { font: F.serif, size, color: C.navy, align: 'left' });
    if (o.sub) { ctx.globalAlpha = p2; txt(ctx, o.sub, 302, 380, { font: F.ui, size: 40, weight: 700, color: C.mute, align: 'left' }); }
    if (o.brand) { const p3 = E.out(prog(t, o.brandAt ?? at + 0.9, 0.4)); ctx.globalAlpha = p3;
      txt(ctx, o.brand, 302, 460, { font: F.hand, size: 70, weight: 700, color: C.tealD, align: 'left' }); }
    ctx.globalAlpha = 1;
  } });
}

// labelled stack of chips (e.g. INDIKASI) with a small header tab
function chipStack(head, items, t1, o = {}) {
  const y0 = o.y || 430, gap = o.gap || 120, els = [];
  const hAt = items[0].at - 0.15;
  sfx('click', hAt, 0.5);
  els.push({ t0: hAt, t1: t1 + 0.3, z: 6, draw(ctx, t) {
    const p = E.out(prog(t, hAt, 0.3)), out = prog(t, t1, 0.25); ctx.globalAlpha = p * (1 - out);
    const w = measure(ctx, head, { font: F.mono, size: 30, weight: 700, track: 4 }) + 50;
    ctx.fillStyle = o.headBg || C.navy; rrect(ctx, 540 - w / 2, y0 - 120, w, 58, 10); ctx.fill();
    txt(ctx, head, 540, y0 - 90, { font: F.mono, size: 30, weight: 700, color: o.headFg || C.teal, track: 4 });
  } });
  items.forEach((it, k) => els.push(chip(it.text, it.at, t1, { y: y0 + k * gap, x: 540 + (k % 2 ? 40 : -40), rot: (k % 2 ? 0.025 : -0.025),
    bg: it.bg || C.paper, fg: it.fg || C.navy, icon: it.icon, size: it.size || 46 })));
  return els;
}

// cause -> effect strip: icon disc, arrow, result text (mechanism of weight gain)
function mechRow(items, t1, o = {}) {
  const y0 = o.y || 460, gap = o.gap || 190;
  items.forEach(it => { sfx('pop', it.at, 0.7); if (it.res) sfx('ding', it.at + 0.35, 0.4); });
  return { t0: items[0].at - 0.1, t1: t1 + 0.3, z: 7, draw(ctx, t) {
    const out = prog(t, t1, 0.3); ctx.globalAlpha = 1 - out;
    if (o.title) { const q = E.out(prog(t, items[0].at - 0.3, 0.3)); ctx.save(); ctx.globalAlpha *= q;
      txt(ctx, o.title, 540, y0 - 140, { font: F.head, size: 66, color: C.white, track: 2, shadow: 'rgba(0,0,0,0.5)' }); ctx.restore(); }
    items.forEach((it, k) => {
      const y = y0 + k * gap, p = E.back(prog(t, it.at, 0.35)); if (p <= 0) return;
      withT(ctx, 0, y, 0, 1, () => {
        ctx.save(); ctx.globalAlpha *= E.out(prog(t, it.at, 0.3));
        ctx.fillStyle = 'rgba(244,239,230,0.96)'; ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 20; ctx.shadowOffsetY = 6;
        rrect(ctx, 90 + (1 - p) * -60, -70, 900, 140, 70); ctx.fill(); ctx.shadowColor = 'transparent';
        ctx.fillStyle = it.col || C.teal; ctx.beginPath(); ctx.arc(160, 0, 54, 0, 7); ctx.fill();
        drawIcon(ctx, it.icon || 'brain', 160, 0, 66, C.navy, { lw: 9 });
        txt(ctx, it.text, 240, it.sub ? -16 : 2, { font: F.ui, size: 44, weight: 800, color: C.navy, align: 'left' });
        if (it.sub) txt(ctx, it.sub, 242, 34, { font: F.ui, size: 32, weight: 700, color: '#4E6378', align: 'left' });
        if (it.res) { const q = E.back(prog(t, it.at + 0.35, 0.3)); if (q > 0) withT(ctx, 900, 0, 0, q, () => {
          ctx.fillStyle = it.resCol || C.coral; rrect(ctx, -80, -38, 160, 76, 38); ctx.fill();
          txt(ctx, it.res, 0, 2, { font: F.ui, size: 40, weight: 800, color: C.white }); }); }
        ctx.restore();
      });
    });
  } };
}

// risk gauge (only where the narration states a level)
function riskGauge(label, level, at, t1, o = {}) {
  sfx('riser', at - 0.2, 0.4); sfx('hit', at + 0.6, 0.6);
  return { t0: at, t1: t1 + 0.3, z: 7, draw(ctx, t) {
    const p = E.out(prog(t, at, 0.35)), out = prog(t, t1, 0.3), fill = E.out(prog(t, at + 0.15, 0.8)) * level;
    ctx.globalAlpha = p * (1 - out); const y = o.y || 1050, x0 = 140, w = 800;
    txt(ctx, 'RISIKO NAIK BERAT BADAN', 540, y - 70, { font: F.mono, size: 30, weight: 700, color: C.white, track: 4, shadow: 'rgba(0,0,0,0.6)' });
    ctx.fillStyle = 'rgba(11,27,46,0.75)'; rrect(ctx, x0, y - 26, w, 52, 26); ctx.fill();
    const g = ctx.createLinearGradient(x0, 0, x0 + w, 0); g.addColorStop(0, C.teal); g.addColorStop(0.5, C.yellow); g.addColorStop(1, C.red);
    ctx.save(); rrect(ctx, x0 + 6, y - 20, (w - 12) * fill, 40, 20); ctx.clip(); ctx.fillStyle = g; ctx.fillRect(x0, y - 30, w, 60); ctx.restore();
    const q = E.back(prog(t, at + 0.6, 0.3)); if (q > 0) withT(ctx, x0 + (w - 12) * level, y + 72, 0, q, () => {
      ctx.fillStyle = level > 0.7 ? C.red : C.yellow; rrect(ctx, -110, -34, 220, 68, 34); ctx.fill();
      txt(ctx, label, 0, 2, { font: F.ui, size: 36, weight: 800, color: level > 0.7 ? C.white : C.navy }); });
  } };
}

// receptor block diagram: brain, two receptors, blocker capsule docks; "kenyang" signal fades
function receptorDiagram(at, hAt, sAt, t1) {
  sfx('paper', at, 0.6); sfx('bubble', hAt, 0.7); sfx('bubble', sAt, 0.7);
  return { t0: at, t1: t1 + 0.3, z: 6, draw(ctx, t) {
    const out = prog(t, t1, 0.3), p = E.back(prog(t, at, 0.4)); ctx.globalAlpha = 1 - out;
    withT(ctx, 540, 560, 0, p, () => {
      ctx.fillStyle = 'rgba(11,27,46,0.72)'; rrect(ctx, -440, -230, 880, 460, 40); ctx.fill();
      drawIcon(ctx, 'brain', -270, -20, 230, C.paper, { lw: 5 });
      [['HISTAMIN', hAt, -95, C.teal], ['SEROTONIN', sAt, 95, C.amber]].forEach(([lab, tt, y, col]) => {
        const q = E.back(prog(t, tt, 0.35)); if (q <= 0) return;
        withT(ctx, 130, y, 0, q, () => {
          ctx.strokeStyle = col; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(-110, 0, 40, -1.1, 1.1); ctx.stroke(); // receptor cup
          const d = E.out(prog(t, tt + 0.3, 0.5)); // blocker docks
          withT(ctx, lerp(-20, -88, d), 0, 0, 1, () => { ctx.fillStyle = C.coral; rrect(ctx, -34, -18, 68, 36, 18); ctx.fill(); });
          txt(ctx, lab, 0, 0, { font: F.mono, size: 34, weight: 700, color: C.white, align: 'left', track: 2 });
          if (d >= 1) drawIcon(ctx, 'cross', -150, -48, 40, C.red, { lw: 14 });
        });
      });
    });
  } };
}

// AI-generated photoreal 3D mockup of the book (Higgsfield), with a slow camera push, parallax drift and a light sweep
function bookStill(at, t1, o = {}) {
  sfx('riser', at - 0.6, 0.6); sfx('whoosh', at, 0.8); sfx('shimmer', at + 0.5, 0.6); sfx('logo', at + 0.4, 0.7);
  return { t0: at - 0.05, t1: t1 + 0.4, z: 2, draw(ctx, t) {
    if (!BOOK3D.width) return;
    const p = E.out(prog(t, at, 0.7)), out = E.in(prog(t, t1, 0.35)), u = E.inOut(prog(t, at, t1 - at));
    const s = lerp(0.9, 0.78, E.out(prog(t, at, 1.4))) + u * 0.04, dx = Math.sin((t - at) * 0.6) * 10, dy = lerp(30, -10, u);
    ctx.save(); ctx.globalAlpha = p * (1 - out);
    if (!BOOK3D.feather) { // soft-edged copy so the mockup blends into the navy background
      const c = mk(BOOK3D.width, BOOK3D.height), g = c.getContext('2d'); g.drawImage(BOOK3D, 0, 0);
      g.globalCompositeOperation = 'destination-in'; const cw = c.width, chh = c.height;
      const rg = g.createRadialGradient(cw / 2, chh * 0.4, cw * 0.3, cw / 2, chh * 0.45, chh * 0.62);
      rg.addColorStop(0, 'rgba(0,0,0,1)'); rg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = rg; g.fillRect(0, 0, cw, chh);
      BOOK3D.feather = c; }
    const iw = BOOK3D.width, ih = BOOK3D.height, k = Math.max(W / iw, H / ih) * s;
    ctx.drawImage(BOOK3D.feather, W / 2 - iw * k / 2 + dx, 860 - ih * k / 2 + dy, iw * k, ih * k);
    const sw = prog(t, at + 1.0, 1.4); if (sw > 0 && sw < 1) { ctx.globalCompositeOperation = 'screen';
      const x = lerp(-300, W + 300, sw), g = ctx.createLinearGradient(x - 160, 0, x + 160, 0);
      g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, 'rgba(255,255,255,0.16)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
    ctx.restore();
  } };
}

// 3D book: box rendered with per-column perspective (cover = the real cover image)
function book3d(at, t1, o = {}) {
  sfx('riser', at - 0.6, 0.6); sfx('whoosh', at, 0.8); sfx('shimmer', at + 0.5, 0.6); sfx('logo', at + 0.4, 0.7);
  return { t0: at, t1: t1 + 0.4, z: 8, draw(ctx, t) {
    const p = E.out(prog(t, at, 0.9)), out = E.in(prog(t, t1, 0.35));
    const cx = o.x ?? 540, cy = (o.y ?? 760) + (1 - p) * 700 + out * 900, bh = o.h ?? 760, bw = bh * BOOK.width / BOOK.height, bd = bh * 0.12;
    const ang = lerp(-1.3, -0.55, E.inOut(prog(t, at, 1.6))) + Math.sin((t - at) * 0.9) * 0.14, D = 2200;
    const ca = Math.cos(ang), sa = Math.sin(ang);
    const proj = (x, y, z) => { const X = x * ca + z * sa, Z = -x * sa + z * ca, s = D / (D + Z); return [cx + X * s, cy + y * s, s]; };
    ctx.save(); ctx.globalAlpha = 1 - out;
    // floor shadow
    const sh = ctx.createRadialGradient(cx, cy + bh / 2 + 30, 10, cx, cy + bh / 2 + 30, bw * 0.9);
    sh.addColorStop(0, 'rgba(0,0,0,0.55)'); sh.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = sh;
    ctx.save(); ctx.translate(cx, cy + bh / 2 + 30); ctx.scale(1, 0.16); ctx.beginPath(); ctx.arc(0, 0, bw * 0.9, 0, 7); ctx.restore(); ctx.fill();
    const face = (x0, z0, x1, z1, draw) => { // vertical strips between (x0,z0) and (x1,z1)
      const N = 90;
      for (let i = 0; i < N; i++) {
        const u0 = i / N, u1 = (i + 1) / N;
        const a = proj(lerp(x0, x1, u0), -bh / 2, lerp(z0, z1, u0)), b = proj(lerp(x0, x1, u1), -bh / 2, lerp(z0, z1, u1));
        const a2 = proj(lerp(x0, x1, u0), bh / 2, lerp(z0, z1, u0));
        const wpx = b[0] - a[0]; if (wpx <= 0) continue;
        draw(u0, u1, a[0], a[1], wpx + 0.8, a2[1] - a[1], (b[1] - a[1]));
      }
    };
    // spine (left side, visible when rotated toward the viewer's left)
    if (sa < 0) face(-bw / 2, bd / 2, -bw / 2, -bd / 2, (u0, u1, x, y, w, h) => {
      ctx.fillStyle = '#E8C800'; ctx.fillRect(x, y, w, h); ctx.fillStyle = `rgba(0,0,0,${0.38 + 0.12 * u0})`; ctx.fillRect(x, y, w, h); });
    // page block (right side)
    if (sa > 0) face(bw / 2, -bd / 2, bw / 2, bd / 2, (u0, u1, x, y, w, h) => { ctx.fillStyle = '#F3EFE6'; ctx.fillRect(x, y, w, h); });
    // front cover
    face(-bw / 2, -bd / 2, bw / 2, -bd / 2, (u0, u1, x, y, w, h, dy) => {
      if (BOOK.width) ctx.drawImage(BOOK, u0 * BOOK.width, 0, (u1 - u0) * BOOK.width + 0.5, BOOK.height, x, y, w, h);
    });
    // sheen sweep
    const sw = prog(t, at + 1.0, 1.2); if (sw > 0 && sw < 1) { ctx.save(); ctx.globalCompositeOperation = 'screen';
      face(-bw / 2, -bd / 2, bw / 2, -bd / 2, (u0, u1, x, y, w, h) => { const d = Math.abs(u0 - lerp(-0.2, 1.2, sw)); if (d < 0.12) { ctx.fillStyle = `rgba(255,255,255,${0.35 * (1 - d / 0.12)})`; ctx.fillRect(x, y, w, h); } });
      ctx.restore(); }
    ctx.restore();
  } };
}

function buildTimeline() {
  const shots = [], els = [];
  const A = (...e) => e.flat().forEach(x => els.push(x));
  // shot helper: slows a clip down if the shot is longer than the clip
  const S = (o) => { if (o.clip && CLIPS[o.clip]) { const len = CLIPS[o.clip] / FPS - (o.in || 0) - 0.05;
    o.speed = Math.min(o.speed || 1, len / (o.t1 - o.t0)); } shots.push(o); };
  const END = PE(141) + 0.25, DUR = END + 3.6;
  const sec = i => P(i) - 0.12;   // cut point just before a phrase
  const caps = [];                 // caption colour per section

  // ===== HOOK =====
  S({ clip: 'n01', t0: 0, t1: sec(3), kb: { s0: 1.0, s1: 1.14, y1: -40 }, grade: 'cool' });
  sfx('boom', 0.0, 1.0); sfx('heartbeat', 0.6, 0.6);
  A(headline([
    { text: 'UBAT PSIKIATRI', at: -0.6, y: 520, size: 118, mark: C.teal, color: C.navy, noShadow: true, sfx: 'none' },
    { text: 'BUAT BERAT', at: -0.6, y: 680, size: 150, color: C.white, sfx: 'none' },
    { text: 'BADAN NAIK?', at: -0.6, y: 840, size: 150, color: C.yellow, sfx: 'none' },
  ], sec(3) - 0.1));
  S({ clip: 'm01', t0: sec(3), t1: sec(5), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'whip', dur: 0.3 }, grade: 'warm' });
  A(chip('Soalan biasa di klinik', Wd(3, 1), sec(5), { y: 560, bg: C.paper, fg: C.navy, icon: 'comment' }));
  S({ bg: 'navy', t0: sec(5), t1: sec(6), tr: { type: 'flash', dur: 0.2 } });
  A(stamp('YA!', Wd(5, 1), sec(6) - 0.05, { y: 760, size: 200, color: C.teal }));
  S({ clip: 'm02', t0: sec(6), t1: sec(9), kb: { s0: 1.05, s1: 1.15 }, tr: { type: 'zoom', dur: 0.3 }, grade: 'warm' });
  A(chip('Ubat psikiatri', Wd(6, 1), sec(9), { y: 520, x: 420, bg: C.teal, icon: 'capsule', rot: -0.03 }));
  A(chip('Berat badan ↑', Wd(8, 2), sec(9), { y: 660, x: 640, bg: C.coral, fg: C.white, rot: 0.03 }));
  S({ bg: 'paper', t0: sec(9), t1: sec(15), tr: { type: 'tear', dur: 0.45 } });
  A(headline([{ text: '10', at: Wd(10, 0), y: 560, size: 380, color: C.navy, noShadow: true, sfx: 'hit' },
              { text: 'UBAT', at: Wd(10, 1), y: 820, size: 150, color: C.tealD, noShadow: true }], sec(15) - 0.1));
  A(chip('Fungsi', Wd(12, 1), sec(15), { y: 1040, x: 330, bg: C.navy, fg: C.paper, icon: 'check' }));
  A(chip('Kenapa berat naik', Wd(13, 1), sec(15), { y: 1040, x: 700, bg: C.coral, fg: C.white }));
  A(hand('jom tengok!', Wd(9, 0), sec(12), { x: 540, y: 330, size: 80, color: C.coral, shadow: false, rot: -0.04 }));

  // ===== MECHANISM =====
  S({ clip: 'n03', t0: sec(15), t1: sec(22), kb: { s0: 1.02, s1: 1.18 }, tr: { type: 'zoom', dur: 0.35 }, grade: 'cool' });
  A(receptorDiagram(Wd(16, 0), Wd(17, 0), Wd(17, 2), sec(20) - 0.1));
  A(headline([{ text: 'CEPAT LAPAR,', at: Wd(20, 2), y: 560, size: 130, color: C.yellow },
              { text: 'LAMBAT KENYANG', at: Wd(21, 0), y: 720, size: 118, color: C.white, mark: C.coral }], sec(22) - 0.1));

  // ===== 01 CLOZAPINE =====
  const ch = (n, a, b) => A(chapter(String(n).padStart(2, '0'), '/ 10 UBAT', a, b));
  S({ bg: 'navy', t0: sec(22), t1: sec(24), tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(1, 'Clozapine', 'ap', P(22) + 0.05, sec(24) + 0.2));
  ch(1, P(22), sec(35));
  S({ clip: 'm03', t0: sec(24), t1: sec(27), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  A(chipStack('INDIKASI', [{ text: 'Skizofrenia', at: Wd(24, 3), icon: 'brain' }, { text: 'Tak respon ubat lain', at: Wd(25, 2) }], sec(27) - 0.1));
  S({ clip: 'm04', t0: sec(27), t1: sec(30), kb: { s0: 1.05, s1: 1.15 }, tr: { type: 'whip', dur: 0.3 }, grade: 'cool', dim: 0.25 });
  A(hand('sangat berkesan', Wd(27, 1), sec(28), { x: 540, y: 600, size: 96, color: C.teal }));
  A(riskGauge('TINGGI', 0.92, Wd(28, 3), sec(30) - 0.1, { y: 760 }));
  S({ clip: 'm05', t0: sec(30), t1: sec(35), kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'zoom', dur: 0.3 }, grade: 'cool', dim: 0.15 });
  A(mechRow([{ text: 'Selera makan', at: P(30), icon: 'heart', res: '↑' },
             { text: 'Sensitiviti insulin', at: Wd(31, 3), icon: 'warn', res: '↓', resCol: C.tealD },
             { text: 'Gula & kolesterol', at: P(33), icon: 'tablet', res: '↑' }], sec(35) - 0.1, { title: 'KENAPA BERAT NAIK?', y: 470 }));

  // ===== 02 OLANZAPINE =====
  S({ bg: 'navy', t0: sec(35), t1: sec(36) + 0.2, tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(2, 'Olanzapine', 'ap', P(35) + 0.1, sec(36) + 0.4));
  ch(2, P(35), sec(41));
  S({ clip: 'm06', t0: sec(36) + 0.2, t1: sec(38), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'cool' });
  A(chipStack('INDIKASI', [{ text: 'Skizofrenia', at: Wd(36, 2), icon: 'brain' }, { text: 'Bipolar', at: Wd(37, 1) }], sec(38) - 0.1));
  S({ clip: 'm07', t0: sec(38), t1: sec(41), kb: { s0: 1.1, s1: 1.22 }, tr: { type: 'zoom', dur: 0.3 }, grade: 'cool', dim: 0.2 });
  A(mechRow([{ text: 'Sekat histamin', sub: '& serotonin (kuat)', at: Wd(38, 2), icon: 'brain', res: '✕', resCol: C.red },
             { text: 'Rasa lapar', at: Wd(40, 2), icon: 'heart', res: '↑' }], sec(41) - 0.1, { title: 'KENAPA BERAT NAIK?', y: 560 }));

  // ===== 03 QUETIAPINE =====
  S({ bg: 'navy', t0: sec(41), t1: sec(42) + 0.2, tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(3, 'Quetiapine', 'ap', P(41) + 0.1, sec(42) + 0.4));
  ch(3, P(41), sec(47));
  S({ clip: 'm08', t0: sec(42) + 0.2, t1: sec(46), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'cool' });
  A(chipStack('INDIKASI', [{ text: 'Skizofrenia', at: Wd(42, 1), icon: 'brain' }, { text: 'Bipolar', at: Wd(42, 2) },
                           { text: 'Tambahan: kemurungan', at: Wd(44, 1) }], sec(46) - 0.1, { gap: 115 }));
  S({ clip: 'n07', t0: sec(46), t1: sec(47), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'whip', dur: 0.3 }, grade: 'warm' });
  A(chip('Mengantuk', Wd(46, 2), sec(47) - 0.1, { y: 520, x: 400, bg: C.paper, fg: C.navy, icon: 'clock', rot: -0.03 }));
  A(chip('Lapar ↑', Wd(46, 4), sec(47) - 0.1, { y: 650, x: 650, bg: C.coral, fg: C.white, rot: 0.03 }));

  // ===== 04 RISPERIDONE =====
  S({ bg: 'navy', t0: sec(47), t1: sec(48) + 0.2, tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(4, 'Risperidone', 'ap', P(47) + 0.1, sec(48) + 0.4));
  ch(4, P(47), sec(55));
  S({ clip: 'm09', t0: sec(48) + 0.2, t1: sec(52), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  A(chipStack('INDIKASI', [{ text: 'Skizofrenia', at: Wd(48, 2), icon: 'brain' }, { text: 'Bipolar', at: Wd(49, 0) },
                           { text: 'Autisme: mudah marah', at: Wd(50, 1) }, { text: '& agresif', at: Wd(50, 4) }], sec(52) - 0.1, { gap: 110, y: 420 }));
  S({ clip: 'm10', t0: sec(52), t1: sec(55), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  A(riskGauge('SEDERHANA', 0.55, Wd(52, 0), sec(55) - 0.1, { y: 520 }));
  A(chip('Kanak-kanak & remaja: lebih mudah terkesan', Wd(53, 1), sec(55) - 0.1, { y: 760, bg: C.yellow, fg: C.navy, size: 34 }));

  // ===== 05 CHLORPROMAZINE =====
  S({ bg: 'navy', t0: sec(55), t1: sec(56) + 0.2, tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(5, 'Chlorpromazine', 'ap', P(55) + 0.1, sec(56) + 0.6, { sub: 'Generasi lama' }));
  ch(5, P(55), sec(62));
  S({ clip: 'm11', t0: sec(56) + 0.2, t1: sec(59), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'cool' });
  A(chipStack('INDIKASI', [{ text: 'Psikosis', at: Wd(57, 1), icon: 'brain' }, { text: 'Gelisah yang teruk', at: Wd(58, 0) }], sec(59) - 0.1));
  S({ clip: 'm12', t0: sec(59), t1: sec(62), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  A(mechRow([{ text: 'Sangat menenangkan', at: Wd(59, 2), icon: 'heart' },
             { text: 'Mengantuk', at: Wd(60, 1), icon: 'clock' },
             { text: 'Selera makan', at: Wd(61, 1), icon: 'tablet', res: '↑' }], sec(62) - 0.1, { y: 460, gap: 175 }));

  // ===== 06 MIRTAZAPINE =====
  S({ bg: 'amber', t0: sec(62), t1: sec(63) + 0.2, tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(6, 'Mirtazapine', 'ad', P(62) + 0.1, sec(63) + 0.5));
  ch(6, P(62), sec(72));
  S({ clip: 'm13', t0: sec(63) + 0.2, t1: sec(68), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'cool' });
  A(chipStack('SELALU DIPILIH UNTUK', [{ text: 'Kemurungan', at: Wd(65, 1), icon: 'heart' }, { text: 'Susah tidur', at: Wd(66, 1) },
                                       { text: 'Hilang selera makan', at: Wd(67, 1) }], sec(68) - 0.1, { gap: 115, headFg: C.amber }));
  S({ clip: 'n02', t0: sec(68), t1: sec(72), kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'zoom', dur: 0.3 }, grade: 'cool' });
  A(chip('Cepat lapar', Wd(69, 0), sec(72) - 0.1, { y: 470, x: 400, bg: C.coral, fg: C.white, rot: -0.03 }));
  A(hand('teringin manis...', Wd(70, 1), sec(72) - 0.1, { x: 600, y: 620, size: 92, color: C.yellow, rot: -0.04 }));

  // ===== 07 AMITRIPTYLINE =====
  S({ bg: 'amber', t0: sec(72), t1: sec(73) + 0.2, tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(7, 'Amitriptyline', 'ad', P(72) + 0.1, sec(73) + 0.6, { sub: 'Generasi lama' }));
  ch(7, P(72), sec(80));
  S({ clip: 'm14', t0: sec(73) + 0.2, t1: sec(77), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  A(chipStack('KINI LEBIH BANYAK UNTUK', [{ text: 'Sakit saraf', at: Wd(75, 1), icon: 'warn' }, { text: 'Cegah migrain', at: Wd(76, 1), icon: 'brain' }],
    sec(77) - 0.1, { headFg: C.amber }));
  S({ bg: 'amber', t0: sec(77), t1: sec(80), tr: { type: 'push', dur: 0.35 } });
  A(mechRow([{ text: 'Sekat histamin', at: Wd(77, 2), icon: 'brain', res: '✕', resCol: C.red },
             { text: 'Mengantuk', at: Wd(78, 2), icon: 'clock' },
             { text: 'Teringin makanan manis', at: Wd(79, 1), icon: 'heart', res: '↑' }], sec(80) - 0.1, { title: 'KENAPA BERAT NAIK?', y: 520 }));

  // ===== 08 PAROXETINE =====
  S({ bg: 'amber', t0: sec(80), t1: sec(81) + 0.2, tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(8, 'Paroxetine', 'ad', P(80) + 0.1, sec(81) + 0.5, { sub: 'Kumpulan SSRI' }));
  ch(8, P(80), sec(89));
  S({ clip: 'm15', t0: sec(81) + 0.2, t1: sec(85), kb: { s0: 1.08, s1: 1.16 }, tr: { type: 'fade', dur: 0.3 }, grade: 'cool' });
  A(chipStack('INDIKASI', [{ text: 'Kemurungan', at: Wd(82, 1), icon: 'heart' }, { text: 'Keresahan (anxiety)', at: Wd(83, 2) },
                           { text: 'Panik', at: Wd(84, 1) }, { text: 'OCD', at: Wd(84, 3) }], sec(85) - 0.1, { gap: 108, y: 420, headFg: C.amber }));
  S({ clip: 'm16', t0: sec(85), t1: sec(89), kb: { s0: 1.06, s1: 1.16 }, tr: { type: 'zoom', dur: 0.3 }, grade: 'cool', dim: 0.15 });
  A(headline([{ text: 'DALAM KUMPULAN SSRI:', at: Wd(85, 0), y: 470, size: 64, color: C.white, font: F.ui, weight: 800 },
              { text: 'PALING KERAP', at: Wd(86, 3), y: 600, size: 130, color: C.yellow },
              { text: 'DIKAITKAN', at: Wd(86, 4), y: 740, size: 110, color: C.white }], sec(89) - 0.1));
  A(chip('Bila diambil jangka panjang', Wd(88, 1), sec(89) - 0.1, { y: 900, bg: C.paper, fg: C.navy, icon: 'calendar', size: 38 }));

  // ===== 09 LITHIUM =====
  S({ bg: 'navy', t0: sec(89), t1: sec(91), tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(9, 'Lithium', 'ms', P(89) + 0.1, sec(91) - 0.1, { sub: 'Untuk bipolar', brand: '' }));
  ch(9, P(89), sec(100));
  A(chip('Bipolar', Wd(90, 3), sec(91) - 0.1, { y: 1100, bg: C.coral, fg: C.white, icon: 'heart' }));
  S({ clip: 'n06', t0: sec(91), t1: sec(96), kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'zoom', dur: 0.3 }, grade: 'warm' });
  A(chip('Cepat dahaga', Wd(92, 1), sec(96) - 0.1, { y: 440, x: 420, bg: C.paper, fg: C.navy, rot: -0.03 }));
  A(chip('+ air manis', Wd(94, 1), sec(96) - 0.1, { y: 570, x: 640, bg: C.coral, fg: C.white, rot: 0.03 }));
  A(stamp('KALORI ↑', Wd(95, 0), sec(96) - 0.1, { y: 760, size: 100, color: C.red }));
  S({ bg: 'paper', t0: sec(96), t1: sec(100), tr: { type: 'tear', dur: 0.45 } });
  A(checklist({ at: sec(96) + 0.05, t1: sec(100) - 0.1, title: 'KENAPA BERAT NAIK?', y: 300, h: 820, gap: 190, items: [
    { text: 'Dahaga → air manis', sub: 'kalori bertambah', at: Wd(96, 1) },
    { text: 'Air tertahan', sub: 'dalam badan', at: Wd(97, 1) },
    { text: 'Fungsi tiroid terjejas', sub: 'metabolisme jadi perlahan', at: Wd(98, 3) }] }));

  // ===== 10 VALPROATE =====
  S({ bg: 'navy', t0: sec(100), t1: sec(102), tr: { type: 'whip', dur: 0.3 } });
  A(drugIntro(10, 'Sodium valproate', 'ms', P(100) + 0.1, sec(102) - 0.1, { brand: 'Epilim', brandAt: Wd(101, 1) }));
  ch(10, P(100), sec(107));
  S({ clip: 'm17', t0: sec(102), t1: sec(104), kb: { s0: 1.06, s1: 1.14 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  A(chipStack('INDIKASI', [{ text: 'Epilepsi', at: Wd(102, 2), icon: 'brain' }, { text: 'Bipolar', at: Wd(103, 0) },
                           { text: 'Cegah migrain', at: Wd(103, 3) }], sec(104) - 0.1, { gap: 115, headFg: C.coral }));
  S({ clip: 'm18', t0: sec(104), t1: sec(107), kb: { s0: 1.1, s1: 1.18 }, tr: { type: 'zoom', dur: 0.3 }, grade: 'cool', dim: 0.3 });
  A(mechRow([{ text: 'Selera makan', at: Wd(104, 3), icon: 'heart', res: '↑' },
             { text: 'Paras insulin', at: Wd(105, 2), icon: 'warn', res: '↑' },
             { text: 'Lemak mudah disimpan', at: Wd(106, 1), icon: 'tablet' }], sec(107) - 0.1, { title: 'KENAPA BERAT NAIK?', y: 470 }));

  // ===== WARNING =====
  S({ clip: 'm19', t0: sec(107), t1: sec(111), kb: { s0: 1.05, s1: 1.15 }, tr: { type: 'flash', dur: 0.25 }, grade: 'cool', dim: 0.35 });
  A(hand('tapi ingat...', P(107), sec(108) + 0.3, { x: 540, y: 420, size: 90, color: C.yellow }));
  A(headline([{ text: 'BUKAN SEMUA', at: Wd(108, 0), y: 560, size: 140, color: C.white, mark: C.tealD },
              { text: 'ORANG', at: Wd(108, 2), y: 720, size: 140, color: C.white },
              { text: 'akan naik berat badan', at: Wd(110, 0), y: 860, size: 60, color: C.teal, font: F.ui, weight: 800 }], sec(111) - 0.1));
  S({ bg: 'navy', t0: sec(111), t1: sec(115), tr: { type: 'push', dur: 0.35 } });
  A(headline([{ text: 'JANGAN', at: Wd(111, 1), y: 520, size: 170, color: C.red },
              { text: 'BERHENTI UBAT', at: Wd(112, 0), y: 690, size: 120, color: C.white },
              { text: 'SENDIRI', at: Wd(112, 2), y: 830, size: 120, color: C.white, mark: C.red }], sec(115) - 0.1));
  A(chip('Simptom boleh datang balik', Wd(113, 1), sec(115) - 0.1, { y: 1010, bg: C.yellow, fg: C.navy, icon: 'warn', size: 40 }));
  caps.push([sec(107), sec(115), C.yellow]);

  // ===== WHAT TO DO =====
  S({ clip: 'm20', t0: sec(115), t1: sec(117) + 0.3, kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'whip', dur: 0.3 }, grade: 'warm' });
  A(headline([{ text: 'APA BOLEH BUAT?', at: Wd(115, 1), y: 560, size: 120, color: C.white, mark: C.tealD }], Wd(116, 0) - 0.3));
  S({ clip: 'n04', t0: sec(117) + 0.3, t1: sec(118), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'whip', dur: 0.3 }, grade: 'warm' });
  S({ clip: 'm21', t0: sec(118), t1: sec(121), kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'whip', dur: 0.3 }, grade: 'cool' });
  S({ clip: 'n08', t0: sec(121), t1: sec(123), kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  S({ clip: 'm22', t0: sec(123), t1: sec(124), kb: { s0: 1.02, s1: 1.1 }, tr: { type: 'whip', dur: 0.3 }, grade: 'warm' });
  S({ clip: 'm23', t0: sec(124), t1: sec(129), kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  const todo = [['Timbang berat badan', Wd(116, 0)], ['Ukur lilit pinggang', Wd(117, 1)], ['Periksa gula & kolesterol', Wd(119, 0)],
                ['Pilih air kosong', Wd(121, 0)], ['Jaga pemakanan', Wd(122, 0)], ['Kekal aktif', Wd(123, 1)]];
  todo.forEach(([s, at], k) => A(chip(s, at, sec(124) - 0.1, { y: 380 + k * 112, x: 540 + (k % 2 ? 30 : -30), bg: k < 3 ? C.paper : C.teal, fg: C.navy, icon: 'check', size: 40 })));
  A(chipStack('BINCANG DENGAN DOKTOR', [{ text: 'Dos boleh diubah', at: Wd(126, 1), icon: 'check' },
                                        { text: 'Pilihan ubat lain yang lebih sesuai', at: Wd(127, 2), icon: 'check', size: 36 }],
    sec(129) - 0.1, { y: 560, gap: 130 }));

  // ===== CTA CLINIC =====
  S({ clip: 'm24', t0: sec(129), t1: sec(132), kb: { s0: 1.0, s1: 1.1, y1: 30 }, tr: { type: 'zoom', dur: 0.35 }, grade: 'warm' });
  S({ clip: 'm25', t0: sec(132), t1: sec(135), kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'fade', dur: 0.35 }, grade: 'warm' });
  A(card({ at: P(129) + 0.1, t1: sec(135) - 0.1, x: 90, y: 330, w: 900, h: 660, rot: 0.015, from: 'bottom', seed: 14, content(ctx, t, w, h) {
    ctx.fillStyle = C.navy; ctx.fillRect(0, 0, w, 14);
    txt(ctx, 'RISAU KESAN', 60, 100, { font: F.head, size: 84, color: C.navy, align: 'left' });
    txt(ctx, 'SAMPINGAN UBAT?', 60, 200, { font: F.head, size: 84, color: C.coral, align: 'left' });
    const a = E.out(prog(t, Wd(132, 3), 0.3)); ctx.globalAlpha = a;
    txt(ctx, 'KONSULTASI', 60, 310, { font: F.head, size: 84, color: C.tealD, align: 'left' }); ctx.globalAlpha = 1;
    const b = E.out(prog(t, Wd(133, 0), 0.35)); ctx.globalAlpha = b;
    txt(ctx, 'bersama', 60, 420, { font: F.serif, style: 'italic', size: 48, color: C.mute, align: 'left' }); ctx.globalAlpha = 1;
    const c = E.back(prog(t, Wd(133, 3), 0.4)); if (c > 0) withT(ctx, 240, 520, 0, c, () => txt(ctx, 'Dr Azren', 0, 0, { font: F.serif, size: 104, color: C.navy }));
    if (CTA_LOCATION) { const d = E.out(prog(t, Wd(134, 4), 0.3)); ctx.globalAlpha = d;
      ctx.fillStyle = C.teal; rrect(ctx, 520, 490, 330, 64, 32); ctx.fill();
      txt(ctx, `Klinik · ${CTA_LOCATION}`, 685, 523, { font: F.ui, size: 32, weight: 800, color: C.navy }); ctx.globalAlpha = 1; }
  } }));

  // ===== BOOK (3D) =====
  S({ bg: 'navy', t0: sec(135), t1: sec(140), tr: { type: 'iris', dur: 0.45 } });
  A(hand('baca lebih lanjut...', P(135) + 0.6, sec(137), { x: 540, y: 1190, size: 80, color: C.teal }));
  A(bookStill(P(135) + 0.1, sec(140) - 0.05));
  A(chip('DAPATKAN BUKU SAYA', Wd(137, 0), sec(140) - 0.1, { y: 1250, bg: C.yellow, fg: C.navy, icon: 'heart', size: 44 }));

  // ===== OUTRO =====
  S({ clip: 'm26', t0: sec(140), t1: END + 0.6, kb: { s0: 1.05, s1: 1.15 }, tr: { type: 'fade', dur: 0.45 }, grade: 'warm' });
  A(sticker('comment', Wd(140, 2), END, { x: 790, y: 600, size: 170, disc: C.white, color: C.navy }));
  A(chip('Tanya di komen', Wd(140, 2), END, { y: 790, bg: C.teal }));
  A(hand('Take care!', Wd(141, 0), END, { x: 540, y: 980, size: 110 }));
  A(brandBug(0.3, END));

  const top = endCard(END, DUR - END);
  return {
    shots, els, duration: DUR, top,
    captionOpts(t) {
      if (t >= END) return { hidden: true };
      if (t >= sec(135) && t < sec(140)) return { y: 1500 };
      for (const [a, b, col] of caps) if (t >= a && t < b) return { hl: col };
      return {};
    },
  };
}
