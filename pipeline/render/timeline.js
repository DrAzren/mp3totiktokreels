// Edit decision list for "Depot Injection". Times come from the forced-aligned words:
// P(i) = start of caption phrase i, Wd(i, j) = start of word j in phrase i (see build/captions.srt).
'use strict';

// Spoken as "di klinik saya di Nilai" — the town name is unverified (could be "dinilai").
// Set to '' to drop the location line from the CTA card.
const CTA_LOCATION = 'Nilai';

function scrim(at, t1, alpha = 0.5) {
  return { t0: at, t1: t1 + 0.3, z: 1, draw(ctx, t) { const a = Math.min(prog(t, at, 0.35), 1 - prog(t, t1, 0.3)) * alpha;
    ctx.fillStyle = `rgba(6,16,30,${a})`; ctx.fillRect(0, 0, W, H); } };
}

// a row of daily pills that gets struck through, then one syringe takes over
function pillRow(at, strikeAt, t1) {
  for (let k = 0; k < 7; k++) sfx('tick', at + k * 0.07, 0.3);
  if (strikeAt) sfx('scribble', strikeAt, 0.6, { dur: 0.35 });
  return { t0: at, t1: t1 + 0.3, z: 7, draw(ctx, t) {
    const out = prog(t, t1, 0.3); ctx.globalAlpha = 1 - out;
    for (let k = 0; k < 7; k++) { const p = E.back(prog(t, at + k * 0.07, 0.3));
      if (p > 0) withT(ctx, 150 + k * 130, 1215, 0, p, () => { ctx.fillStyle = C.paper; ctx.beginPath(); ctx.arc(0, 0, 50, 0, 7); ctx.fill(); drawIcon(ctx, 'capsule', 0, 0, 62, C.coral, { lw: 10 }); }); }
    const s = strikeAt ? E.out(prog(t, strikeAt, 0.35)) : 0;
    if (s > 0) { ctx.strokeStyle = C.red; ctx.lineWidth = 14; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(90, 1240); ctx.lineTo(90 + 900 * s, 1190); ctx.stroke(); }
  } };
}

// three small index cards labelled 01..03
function miniCards(ats, t1, labels, y = 940) {
  return ats.map((at, k) => card({ at, t1, x: 115 + k * 300, y, w: 250, h: 300, rot: (k - 1) * 0.06, from: 'pop', seed: 70 + k, tape: k === 1, sfx: 'pop', content(ctx, t, w, h) {
    txt(ctx, `0${k + 1}`, w / 2, 110, { font: F.head, size: 120, color: C.tealD });
    txt(ctx, labels[k], w / 2, 230, { font: F.mono, size: 26, weight: 700, color: C.navy });
  } }));
}

// two drug cards with an "=" between (same function)
function equalCards(at, eqAt, t1) {
  sfx('stamp', eqAt, 0.7);
  const els = [
    card({ at, t1, x: 80, y: 430, w: 380, h: 420, rot: -0.05, from: 'left', seed: 81, content(ctx, t, w, h) {
      txt(ctx, '01', w / 2, 110, { font: F.head, size: 120, color: C.tealD }); txt(ctx, 'Clopixol', w / 2, 250, { font: F.serif, size: 62, color: C.navy });
      txt(ctx, 'DEPOT', w / 2, 320, { font: F.mono, size: 30, weight: 700, color: C.mute, track: 4 }); } }),
    card({ at: at + 0.25, t1, x: 620, y: 430, w: 380, h: 420, rot: 0.05, from: 'right', seed: 82, content(ctx, t, w, h) {
      txt(ctx, '02', w / 2, 110, { font: F.head, size: 120, color: C.tealD }); txt(ctx, 'Fluanxol', w / 2, 250, { font: F.serif, size: 62, color: C.navy });
      txt(ctx, 'DEPOT', w / 2, 320, { font: F.mono, size: 30, weight: 700, color: C.mute, track: 4 }); } }),
    { t0: eqAt, t1: t1 + 0.3, z: 8, draw(ctx, t) { const p = E.back(prog(t, eqAt, 0.3)), out = prog(t, t1, 0.3);
      withT(ctx, 540, 640, 0, p * (1 - out), () => { ctx.fillStyle = C.teal; ctx.beginPath(); ctx.arc(0, 0, 74, 0, 7); ctx.fill(); txt(ctx, '=', 0, 2, { font: F.ui, size: 120, weight: 800, color: C.navy }); }); } },
  ];
  return els;
}

// overlapping discs: UBAT + PESAKIT
function venn(aAt, bAt, t1) {
  sfx('pop', aAt, 0.7); sfx('pop', bAt, 0.7);
  return { t0: aAt, t1: t1 + 0.3, z: 6, draw(ctx, t) {
    const out = prog(t, t1, 0.3), pa = E.back(prog(t, aAt, 0.4)), pb = E.back(prog(t, bAt, 0.4));
    ctx.globalAlpha = 1 - out;
    if (pa > 0) withT(ctx, 380, 760, 0, pa, () => { ctx.fillStyle = 'rgba(46,196,182,0.88)'; ctx.beginPath(); ctx.arc(0, 0, 230, 0, 7); ctx.fill();
      drawIcon(ctx, 'capsule', -40, -70, 120, C.navy, { lw: 9 }); txt(ctx, 'UBAT', -40, 60, { font: F.head, size: 96, color: C.navy }); });
    if (pb > 0) withT(ctx, 700, 760, 0, pb, () => { ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = 'rgba(242,166,90,0.92)'; ctx.beginPath(); ctx.arc(0, 0, 230, 0, 7); ctx.fill();
      ctx.globalCompositeOperation = 'source-over'; drawIcon(ctx, 'heart', 50, -70, 110, C.navy, { lw: 9 }); txt(ctx, 'PESAKIT', 50, 60, { font: F.head, size: 92, color: C.navy }); });
  } };
}

// one syringe -> long bar of lasting effect
function lastingBar(at, barAt, barEnd, t1) {
  sfx('swell', barAt, 0.5);
  return { t0: at, t1: t1 + 0.3, z: 6, draw(ctx, t) {
    const out = prog(t, t1, 0.3); ctx.globalAlpha = 1 - out;
    const p = E.back(prog(t, at, 0.4));
    if (p > 0) withT(ctx, 200, 720, 0, p, () => { ctx.fillStyle = C.teal; ctx.beginPath(); ctx.arc(0, 0, 105, 0, 7); ctx.fill(); drawIcon(ctx, 'syringe', 0, 0, 130, C.navy, { lw: 9 }); });
    if (p > 0) { ctx.globalAlpha = (1 - out) * E.out(p); txt(ctx, '1 suntikan', 200, 880, { font: F.hand, size: 62, weight: 700, color: C.navy }); ctx.globalAlpha = 1 - out; }
    const b = E.inOut(prog(t, barAt, barEnd - barAt + 0.4));
    if (b > 0) { const x0 = 330, x1 = 980, y = 720, xe = lerp(x0, x1, b);
      const g = ctx.createLinearGradient(x0, 0, x1, 0); g.addColorStop(0, C.teal); g.addColorStop(1, 'rgba(46,196,182,0.25)');
      ctx.fillStyle = g; rrect(ctx, x0, y - 34, xe - x0, 68, 34); ctx.fill();
      for (let k = 1; k <= 4; k++) { const X = lerp(x0, x1, k / 5); if (X < xe) { ctx.fillStyle = 'rgba(11,27,46,0.35)'; ctx.fillRect(X - 2, y - 20, 4, 40); } }
      ctx.globalAlpha = (1 - out) * prog(t, barAt + 0.3, 0.4);
      txt(ctx, 'kesan ubat berpanjangan', 655, 820, { font: F.ui, size: 40, weight: 800, color: C.navy }); }
  } };
}

// diagonal caution tapes sweeping in (side-effects chapter)
function cautionTape(at, t1) {
  sfx('whoosh', at, 0.8);
  return { t0: at, t1: t1 + 0.3, z: 2, draw(ctx, t) {
    const out = prog(t, t1, 0.3);
    [[300, -0.32, 0], [1560, 0.28, 0.12]].forEach(([y, rot, d], k) => {
      const p = E.out(prog(t, at + d, 0.5)), x = lerp(k ? 1700 : -700, 540, p) + (k ? 1 : -1) * out * 1600;
      withT(ctx, x, y, rot, 1, () => { ctx.fillStyle = C.amber; ctx.fillRect(-900, -46, 1800, 92);
        ctx.save(); ctx.beginPath(); ctx.rect(-900, -46, 1800, 92); ctx.clip(); ctx.fillStyle = C.ink;
        for (let s = -900; s < 900; s += 90) { ctx.beginPath(); ctx.moveTo(s, 46); ctx.lineTo(s + 46, -46); ctx.lineTo(s + 80, -46); ctx.lineTo(s + 34, 46); ctx.fill(); }
        ctx.restore(); });
    });
  } };
}

// newspaper clipping card
function clipping(at, t1, kicker, head, o = {}) {
  return card({ at, t1, x: o.x ?? 110, y: o.y, w: o.w || 860, h: o.h || 380, rot: o.rot || 0, from: o.from || 'right', seed: o.seed || 90, tornSides: 'tblr', torn: 14, tape: true, content(ctx, t, w, h) {
    txt(ctx, kicker, 50, 64, { font: F.mono, size: 26, weight: 700, color: C.coral, align: 'left', track: 4 });
    ctx.fillStyle = C.navy; ctx.fillRect(50, 92, w - 100, 4);
    const lines = head.split('\n'); lines.forEach((l, k) => txt(ctx, l, 50, 160 + k * 84, { font: F.serif, size: 76, color: C.navy, align: 'left' }));
    ctx.fillStyle = 'rgba(11,27,46,0.18)'; for (let k = 0; k < 3; k++) ctx.fillRect(50, h - 90 + k * 22, (w - 100) * (k === 2 ? 0.6 : 1), 8);
  } });
}

function buildTimeline() {
  const shots = [], els = [];
  const S = (o) => shots.push(o), A = (...e) => e.flat().forEach(x => els.push(x));
  const END = 159.45, DUR = 163.0;

  // ===== S01 HOOK =====
  S({ clip: 'v21', t0: 0, t1: 3.0, kb: { s0: 1.02, s1: 1.2, y1: -50 }, grade: 'cool' });
  S({ clip: 'v01', t0: 3.0, t1: 5.05, kb: { s0: 1.0, s1: 1.12 }, tr: { type: 'zoom', dur: 0.32 } });
  S({ clip: 'v02', t0: 5.05, t1: 7.7, kb: { s0: 1.05, s1: 1.14, x1: 20 }, tr: { type: 'whip', dur: 0.3, dir: 1 }, grade: 'warm' });
  sfx('boom', 0.0, 1.0); sfx('whoosh', 2.84, 0.7); sfx('whoosh', 4.92, 0.8);
  A(headline([
    { text: 'SEKALI CUCUK,', at: -0.6, y: 560, size: 150, mark: C.teal, color: C.navy, noShadow: true, sfx: 'none' },
    { text: 'TAK PAYAH MAKAN', at: 0.3, y: 720, size: 96 },
    { text: 'UBAT HARI-HARI?', at: 0.62, y: 840, size: 118, color: C.yellow, sfx: 'hit' },
  ], 2.85));
  A(chip('SKIZOFRENIA', Wd(1, 1), 2.85, { y: 990, bg: C.paper, fg: C.navy, rot: -0.03, size: 44 }));
  A(sticker('syringe', Wd(3, 1), 4.95, { x: 790, y: 640, size: 150, disc: C.teal, color: C.navy, rot: -0.2 }));
  A(hand('sekali?', Wd(3, 2), 4.95, { x: 790, y: 800, size: 84 }));
  A(pillRow(Wd(5, 0), null, 7.6));
  A(headline([{ text: 'SETIAP HARI?', at: Wd(6, 0), y: 560, size: 150, color: C.yellow, sfx: 'hit' }], 7.6));

  // ===== S02 ANSWER =====
  S({ bg: 'navy', t0: 7.7, t1: 9.62, tr: { type: 'flash', dur: 0.24 } });
  A(headline([{ text: 'JAWAPANNYA', at: Wd(7, 1), y: 640, size: 64, font: F.mono, weight: 700, track: 10, color: C.teal, from: 1 }], 9.55));
  A(stamp('YA!', Wd(7, 2), 9.55, { y: 860, size: 200, color: C.teal, rot: -0.08 }));
  A(headline([{ text: 'MEMANG ADA.', at: Wd(8, 1), y: 1070, size: 110, sfx: 'hit' }], 9.55));
  S({ clip: 'v03', t0: 9.62, t1: 15.4, speed: 0.87, kb: { s0: 1.06, s1: 1.18, x1: -30 }, tr: { type: 'tear', dur: 0.5 } });
  sfx('tear', 9.6, 0.9);
  A(card({ at: Wd(10, 0) - 0.1, t1: 15.25, x: 90, y: 360, w: 900, h: 560, rot: -0.02, from: 'left', seed: 12, content(ctx, t, w, h) {
    txt(ctx, 'NAMA RAWATAN', 60, 70, { font: F.mono, size: 28, weight: 700, color: C.tealD, align: 'left', track: 6 });
    txt(ctx, 'DEPOT', 60, 190, { font: F.head, size: 170, color: C.navy, align: 'left' });
    const q = E.out(prog(t, Wd(10, 1), 0.3)); ctx.globalAlpha = q;
    txt(ctx, 'INJECTION', 60 + (1 - q) * 30, 320, { font: F.head, size: 118, color: C.tealD, align: 'left' }); ctx.globalAlpha = 1;
    const r = prog(t, Wd(11, 0), 0.3); if (r > 0) { ctx.globalAlpha = r; txt(ctx, 'ataupun', 60, 420, { font: F.hand, size: 56, weight: 700, color: C.coral, align: 'left' }); ctx.globalAlpha = 1; }
  } }));
  A(typewriter('long-acting injectable', Wd(11, 1), 15.25, { x: 345, y: 782, size: 38 }));
  A(typewriter('antipsikotik', Wd(12, 1), 15.25, { x: 345, y: 840, size: 38, color: C.tealD }));

  // ===== S03 CTA (narrator's own invitation) =====
  S({ clip: 'v04', t0: 15.4, t1: 20.1, kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'fade', dur: 0.45 }, grade: 'warm' });
  A(chip('Skizofrenia', Wd(15, 1), 20.0, { x: 380, y: 520, bg: C.paper, fg: C.navy, rot: -0.04 }));
  A(chip('Gangguan psikosis', Wd(16, 1), 20.0, { x: 620, y: 640, bg: C.paper, fg: C.navy, rot: 0.03 }));
  S({ clip: 'v07', t0: 20.1, t1: 22.4, kb: { s0: 1.02, s1: 1.1 }, tr: { type: 'whip', dur: 0.3, dir: 1 } });
  sfx('whoosh', 19.98, 0.7);
  A(scribble('circle', Wd(17, 2), 22.3, { x: 240, y: 1560, rx: 150, ry: 130, color: C.yellow, lw: 11 }));
  A(scribble('arrow', Wd(17, 2) + 0.3, 22.3, { pts: [560, 1180, 380, 1420], bend: 40, color: C.yellow, lw: 10 }));
  S({ clip: 'v05', t0: 22.4, t1: 24.95, kb: { s0: 1.0, s1: 1.1, y1: 30 }, tr: { type: 'fade', dur: 0.35 }, grade: 'warm' });
  S({ clip: 'v06', t0: 24.95, t1: 29.4, kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'zoom', dur: 0.35 }, grade: 'warm' });
  A(card({ at: P(20) - 0.05, t1: 27.95, x: 90, y: 330, w: 900, h: 640, rot: 0.015, from: 'bottom', seed: 14, content(ctx, t, w, h) {
    ctx.fillStyle = C.navy; ctx.fillRect(0, 0, w, 14);
    txt(ctx, 'SARINGAN &', 60, 100, { font: F.head, size: 84, color: C.navy, align: 'left' });
    const a = E.out(prog(t, Wd(21, 0), 0.3)); ctx.globalAlpha = a;
    txt(ctx, 'KONSULTASI', 60, 200, { font: F.head, size: 84, color: C.navy, align: 'left' });
    txt(ctx, 'KESIHATAN MENTAL', 60, 300, { font: F.head, size: 84, color: C.tealD, align: 'left' }); ctx.globalAlpha = 1;
    const b = E.out(prog(t, Wd(22, 0), 0.35)); ctx.globalAlpha = b;
    txt(ctx, 'bersama', 60, 410, { font: F.serif, style: 'italic', size: 48, color: C.mute, align: 'left' }); ctx.globalAlpha = 1;
    const c = E.back(prog(t, Wd(23, 0), 0.4)); if (c > 0) withT(ctx, 240, 500, 0, c, () => txt(ctx, 'Dr Azren', 0, 0, { font: F.serif, size: 104, color: C.navy }));
    if (CTA_LOCATION) { const d = E.out(prog(t, Wd(24, 4), 0.3)); ctx.globalAlpha = d;
      ctx.fillStyle = C.teal; rrect(ctx, 520, 470, 330, 64, 32); ctx.fill();
      txt(ctx, `Klinik · ${CTA_LOCATION}`, 685, 503, { font: F.ui, size: 32, weight: 800, color: C.navy }); ctx.globalAlpha = 1; }
  } }));
  A(sticker('check', Wd(26, 3), 29.3, { x: 820, y: 700, size: 140, disc: C.teal, color: C.navy }));

  // ===== S04 WHY AN INJECTION? =====
  S({ bg: 'paper', t0: 29.4, t1: 35.55, tr: { type: 'tear', dur: 0.5 } });
  sfx('rewind', 29.25, 0.8);
  A(hand('balik kepada soalan tadi...', Wd(27, 1), 35.4, { x: 540, y: 360, size: 66, color: C.navy, shadow: false }));
  A(clipping(P(29) - 0.05, 35.4, 'SOALAN', 'Kenapa ada ubat\nyang kena cucuk?', { y: 480, rot: -0.025, seed: 91 }));
  A(clipping(P(31) - 0.05, 35.4, 'SALAH FAHAM?', 'Sebab pesakit\ntu teruk ke?', { y: 900, rot: 0.03, from: 'left', seed: 92 }));
  A(scribble('question', Wd(32, 1), 35.4, { x: 870, y: 980, color: C.coral, lw: 12 }));
  S({ clip: 'v07', t0: 35.55, t1: 41.38, blur: true, dim: 0.35, kb: { s0: 1.1, s1: 1.15 }, tr: { type: 'push', dur: 0.45 } });
  sfx('whoosh', 35.5, 0.6);
  A(hand('Tapi...', Wd(33, 0), 36.3, { x: 540, y: 520, size: 110 }));
  A(calendarGrid({ at: 36.15, t1: 41.25, fillAt: 36.5, step: 0.12, missed: [4, 9, 10, 16, 22, 23], title: 'MAKAN UBAT HARI-HARI', note: 'susah nak ingat!', noteAt: Wd(34, 2), y: 290 }));

  // ===== S05 HOW A DEPOT WORKS =====
  S({ clip: 'v22', t0: 41.38, t1: 45.1, kb: { s0: 1.0, s1: 1.16 }, tr: { type: 'fade', dur: 0.4 } });
  A(chip('DEPOT INJECTION', Wd(37, 2), 45.0, { y: 430, icon: 'syringe' }));
  S({ clip: 'v09', t0: 45.1, t1: 48.05, kb: { s0: 1.0, s1: 1.1 }, tr: { type: 'fade', dur: 0.5 } });
  A(headline([
    { text: 'perlahan-lahan', at: Wd(39, 1), y: 470, size: 120, font: F.serif, style: 'italic', color: C.paper, from: 1.1, dur: 0.8 },
    { text: 'BEBERAPA MINGGU', at: Wd(41, 1), y: 1090, size: 104, color: C.teal, sfx: 'hit' },
  ], 47.95));
  S({ clip: 'v09', t0: 48.05, t1: 54.9, in: 2.95, blur: true, dim: 0.45, tr: { type: 'fade', dur: 0.3 } });
  A(plasmaGraph({ at: P(42) - 0.05, t1: 52.8, oralAt: 48.5, depotAt: 49.2, consistAt: Wd(43, 1), y: 270 }));
  A(headline([{ text: 'TAK BERGANTUNG', at: Wd(45, 0), y: 700, size: 110 }, { text: 'PADA PIL HARIAN', at: Wd(46, 0), y: 830, size: 96, color: C.coral }], 54.8));
  A(pillRow(Wd(46, 0), Wd(46, 2), 54.8));

  // ===== S06 LIST INTRO =====
  S({ bg: 'navy', t0: 54.9, t1: 60.0, tr: { type: 'tear', dur: 0.45 } });
  sfx('tear', 54.85, 0.8);
  A(headline([
    { text: 'UBAT DEPOT', at: Wd(47, 1), y: 520, size: 130 },
    { text: 'GENERASI LAMA', at: Wd(48, 0), y: 680, size: 140, color: C.navy, mark: C.teal, noShadow: true, sfx: 'hit' },
  ], 59.95));
  A(miniCards([Wd(49, 0), Wd(49, 1), Wd(49, 2)], 59.95, ['CLOPIXOL', 'FLUANXOL', 'MODECATE']));

  // ===== S07 CLOPIXOL DEPOT =====
  A(chapter('01/03', 'CLOPIXOL DEPOT', 60.0, 81.25));
  S({ clip: 'v22', t0: 60.0, t1: 64.3, in: 1.5, dim: 0.4, kb: { s0: 1.15, s1: 1.25 }, tr: { type: 'whip', dur: 0.3, dir: 1 } });
  A(drugCard(1, 'Clopixol Depot', ['zuclopenthixol', 'decanoate'], 60.1, 64.2, { brandAt: Wd(52, 0), genAt: Wd(53, 1) }));
  S({ clip: 'v10', t0: 64.3, t1: 68.95, kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'fade', dur: 0.35 } });
  A(chip('Antipsikotik', Wd(54, 2), 68.85, { x: 400, y: 470, rot: -0.03, icon: 'capsule' }));
  A(chip('Maintenance treatment', Wd(56, 1), 68.85, { x: 580, y: 590, rot: 0.02, bg: C.paper, fg: C.navy }));
  S({ clip: 'v23', t0: 68.95, t1: 72.3, kb: { s0: 1.02, s1: 1.12 }, tr: { type: 'fade', dur: 0.4 } });
  A(chip('Skizofrenia', Wd(58, 0), 72.2, { x: 380, y: 480, rot: -0.03, bg: C.paper, fg: C.navy }));
  A(chip('Psychotic disorder', Wd(59, 0), 72.2, { x: 600, y: 600, rot: 0.03, bg: C.paper, fg: C.navy }));
  S({ clip: 'v24', t0: 72.3, t1: 77.0, kb: { s0: 1.04, s1: 1.16 }, tr: { type: 'whip', dur: 0.3, dir: -1 } });
  sfx('whoosh', 72.2, 0.6);
  A(scrim(73.95, 76.9, 0.5));
  A(injectionStrip({ at: 74.0, t1: 76.9, markAt: 74.35, noteAt: Wd(62, 1), y: 400 }));
  S({ bg: 'paper', t0: 77.0, t1: 81.3, tr: { type: 'tear', dur: 0.45 } });
  sfx('tear', 76.95, 0.8);
  A(vsCard({ at: 77.05, t1: 81.2, bAt: Wd(65, 0), neqAt: Wd(66, 2), noteAt: Wd(67, 1) }));

  // ===== S08 FLUANXOL DEPOT =====
  A(chapter('02/03', 'FLUANXOL DEPOT', 81.3, 99.15));
  S({ clip: 'v09', t0: 81.3, t1: 86.0, in: 5.0, dim: 0.4, kb: { s0: 1.1, s1: 1.2 }, tr: { type: 'whip', dur: 0.3, dir: -1 } });
  A(drugCard(2, 'Fluanxol Depot', ['flupentixol', 'decanoate'], 81.38, 85.92, { brandAt: Wd(69, 0), genAt: Wd(70, 1), from: 'left', exit: 'right', rot: 0.02 }));
  S({ bg: 'navy', t0: 86.0, t1: 89.1, tr: { type: 'fade', dur: 0.3 } });
  A(equalCards(86.05, Wd(73, 2), 89.05));
  A(headline([{ text: 'FUNGSI SAMA', at: Wd(73, 2) + 0.05, y: 1010, size: 120, color: C.teal }], 89.05));
  S({ clip: 'v11', t0: 89.1, t1: 94.3, speed: 0.97, kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'fade', dur: 0.35 } });
  A(headline([{ text: 'KURANGKAN', at: Wd(75, 0), y: 330, size: 92, color: C.yellow }], 94.2));
  A(chip('Halusinasi', Wd(75, 1), 94.2, { x: 330, y: 470, icon: 'ear', rot: -0.03 }));
  A(chip('Delusi', Wd(76, 0), 94.2, { x: 680, y: 600, icon: 'thought', rot: 0.03 }));
  A(chip('Paranoid', Wd(77, 1), 94.2, { x: 380, y: 730, icon: 'eye', rot: -0.02 }));
  S({ clip: 'v12', t0: 94.3, t1: 99.2, kb: { s0: 1.02, s1: 1.12 }, tr: { type: 'fade', dur: 0.5 }, grade: 'warm' });
  A(sticker('shield', Wd(78, 3), 99.1, { x: 540, y: 520, size: 190, disc: C.teal, color: C.navy }));
  A(headline([{ text: 'MENCEGAH', at: Wd(78, 3) + 0.1, y: 740, size: 110 }, { text: 'RELAPSE', at: Wd(80, 1), y: 870, size: 140, color: C.navy, mark: C.teal, noShadow: true, sfx: 'hit' }], 99.1));

  // ===== S09 MODECATE =====
  A(chapter('03/03', 'MODECATE', 99.2, 117.45));
  S({ clip: 'v25', t0: 99.2, t1: 102.8, dim: 0.35, kb: { s0: 1.08, s1: 1.18 }, tr: { type: 'whip', dur: 0.3, dir: 1 } });
  A(drugCard(3, 'Modecate', ['fluphenazine', 'decanoate'], 99.28, 102.72, { brandAt: Wd(82, 0), genAt: Wd(83, 0) }));
  S({ clip: 'v13', t0: 102.8, t1: 108.95, speed: 0.82, kb: { s0: 1.02, s1: 1.12 }, tr: { type: 'fade', dur: 0.35 } });
  A(chip('Generasi pertama', Wd(86, 0), 108.85, { x: 420, y: 480, rot: -0.03 }));
  A(chip('Maintenance · skizofrenia', Wd(88, 0), 108.85, { x: 560, y: 600, rot: 0.02, bg: C.paper, fg: C.navy }));
  S({ bg: 'paper', t0: 108.95, t1: 117.55, tr: { type: 'tear', dur: 0.45 } });
  sfx('tear', 108.9, 0.8);
  A(headline([{ text: 'KONSEP SAMA', at: Wd(90, 0), y: 420, size: 130, color: C.navy, noShadow: true }], 117.45));
  A(miniCards([Wd(90, 1), Wd(90, 2), Wd(90, 3)], 110.2, ['CLOPIXOL', 'FLUANXOL', 'MODECATE'], 520));
  A(lastingBar(Wd(91, 1), Wd(92, 2), Wd(93, 1), 117.45));
  A(stamp('IKUT REJIM DOKTOR', Wd(95, 0), 117.45, { y: 1070, size: 86, color: C.tealD, rot: -0.05 }));

  // ===== S10 SIDE EFFECTS (first-generation antipsychotics) =====
  S({ bg: 'amber', t0: 117.55, t1: 122.25, tr: { type: 'fade', dur: 0.3 } });
  A(cautionTape(117.6, 122.15));
  A(sticker('warn', 117.75, 122.15, { x: 540, y: 430, size: 150, disc: C.amber, color: C.ink }));
  A(headline([{ text: 'KESAN', at: Wd(98, 0), y: 640, size: 180, color: C.amber, sfx: 'hit' }, { text: 'SAMPINGAN', at: Wd(98, 1), y: 820, size: 150 }], 122.15));
  A(chip('Antipsikotik generasi pertama', Wd(102, 0), 122.15, { y: 1000, bg: C.amber, fg: C.ink, size: 38 }));
  S({ clip: 'v14', t0: 122.25, t1: 127.2, kb: { s0: 1.04, s1: 1.14 }, tr: { type: 'whip', dur: 0.3, dir: 1 } });
  sfx('whoosh', 122.15, 0.7);
  A(chip('PERLU MONITOR', Wd(103, 3), 127.1, { y: 430, icon: 'clipboard', bg: C.amber, fg: C.ink }));
  A(headline([{ text: 'OTOT KAKU', at: Wd(105, 2), y: 600, size: 130 }], 127.1));
  S({ clip: 'v15', t0: 127.2, t1: 130.1, kb: { s0: 1.28, s1: 1.36, y0: -260, y1: -280 }, tr: { type: 'fade', dur: 0.3 } });
  A(headline([{ text: 'TANGAN', at: Wd(108, 0), y: 470, size: 120 }, { text: 'MENGGELETAR', at: Wd(108, 2), y: 600, size: 120, color: C.amber }], 130.0));
  S({ clip: 'v16', t0: 130.1, t1: 133.95, kb: { s0: 1.04, s1: 1.1 }, tr: { type: 'whip', dur: 0.3, dir: -1 } });
  sfx('whoosh', 130.0, 0.6);
  A(headline([{ text: 'GELISAH', at: Wd(109, 1), y: 440, size: 130 }, { text: 'TAK BOLEH DUDUK DIAM', at: Wd(110, 3), y: 590, size: 76, color: C.amber }], 133.85));
  A(chip('= AKATISIA', Wd(112, 0), 133.85, { y: 730, bg: C.amber, fg: C.ink, size: 54 }));
  S({ clip: 'v16', t0: 133.95, t1: 137.9, blur: true, dim: 0.45, tr: { type: 'fade', dur: 0.3 } });
  A(checklist({ at: 133.98, t1: 137.8, y: 300, h: 900, items: [
    { text: 'Otot / badan kaku', at: 134.2 }, { text: 'Tangan menggeletar', at: 134.4 },
    { text: 'Akatisia', sub: 'gelisah, tak boleh duduk diam', at: 134.6 },
    { text: 'Pergerakan abnormal', sub: 'penggunaan jangka panjang', at: Wd(113, 2) }] }));

  // ===== S11 FOLLOW-UP =====
  S({ bg: 'paper', t0: 137.9, t1: 141.25, tr: { type: 'tear', dur: 0.45 } });
  sfx('tear', 137.85, 0.8);
  A(headline([{ text: 'BERGANTUNG KEPADA', at: Wd(116, 1), y: 420, size: 84, color: C.navy, noShadow: true }], 141.15));
  A(venn(Wd(117, 0), Wd(117, 2), 141.15));
  S({ clip: 'v05', t0: 141.25, t1: 145.05, in: 1.0, blur: true, dim: 0.4, tr: { type: 'fade', dur: 0.3 } });
  A(sticker('syringe', Wd(120, 3), 145.0, { x: 270, y: 640, size: 170, disc: C.teal, color: C.navy }));
  A(scribble('arrow', Wd(121, 0), 145.0, { pts: [400, 640, 680, 640], bend: 30, color: C.white, lw: 10, dur: 0.3 }));
  A(sticker('home', Wd(121, 1), 145.0, { x: 810, y: 640, size: 170, disc: C.paper, color: C.navy }));
  A(hand('cucuk, pastu balik?', Wd(120, 3), 145.0, { x: 540, y: 860, size: 80 }));
  A(scribble('strike', Wd(121, 3), 145.0, { x: 200, y: 650, w: 700, color: C.red, lw: 16, dur: 0.3 }));
  S({ clip: 'v17', t0: 145.05, t1: 147.7, kb: { s0: 1.04, s1: 1.12 }, tr: { type: 'whip', dur: 0.3, dir: 1 }, grade: 'warm' });
  A(sticker('calendar', Wd(122, 2), 147.6, { x: 820, y: 820, size: 140, disc: C.paper, color: C.navy, rot: 0.1 }));
  A(stamp('FOLLOW-UP', Wd(123, 0), 147.6, { y: 560, size: 130, color: C.teal, rot: -0.09 }));

  // ===== S12 TAKEAWAY =====
  S({ split: [{ clip: 'v02', in: 1.0 }, { clip: 'v03', in: 2.5 }], t0: 147.7, t1: 152.4, tr: { type: 'push', dur: 0.4 } });
  sfx('whoosh', 147.65, 0.6);
  A(chip('TABLET', Wd(125, 0), 152.3, { y: 800, icon: 'capsule', bg: C.paper, fg: C.navy }));
  A(chip('INJECTION', Wd(126, 0), 152.3, { y: 1130, icon: 'syringe' }));
  A({ t0: Wd(128, 0) - 0.1, t1: 152.6, z: 4, draw(ctx, t) { const p = E.out(prog(t, Wd(128, 0) - 0.1, 0.3)), o = prog(t, 152.3, 0.3);
    ctx.globalAlpha = 1 - o; ctx.fillStyle = 'rgba(11,27,46,0.92)'; ctx.fillRect(0, 965 - 80 * p, W, 160 * p); } });
  A(headline([{ text: 'MANA LAGI POWER?', at: Wd(128, 0), y: 965, size: 96, from: 1.15 }], 152.3));
  A(scribble('strike', Wd(128, 3) + 0.05, 152.3, { x: 160, y: 965, w: 760, color: C.red, lw: 18, dur: 0.3 }));
  S({ clip: 'v18', t0: 152.4, t1: 154.45, kb: { s0: 1.02, s1: 1.1 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  S({ clip: 'v19', t0: 154.45, t1: 156.95, kb: { s0: 1.02, s1: 1.1 }, tr: { type: 'fade', dur: 0.3 }, grade: 'warm' });
  A(headline([
    { text: 'SESUAI.', at: Wd(130, 3), y: 540, size: 160, color: C.navy, mark: C.teal, noShadow: true, sfx: 'hit' },
    { text: 'SELAMAT.', at: Wd(131, 0), y: 720, size: 160, color: C.navy, mark: C.amber, noShadow: true, sfx: 'hit' },
    { text: 'PRAKTIKAL.', at: Wd(131, 2), y: 900, size: 160, color: C.navy, mark: C.paper, noShadow: true, sfx: 'hit' },
  ], 156.85));

  // ===== S13 OUTRO =====
  S({ clip: 'v20', t0: 156.95, t1: END + 0.6, kb: { s0: 1.05, s1: 1.15 }, tr: { type: 'fade', dur: 0.5 }, grade: 'warm' });
  A(sticker('comment', Wd(134, 4), END, { x: 790, y: 600, size: 170, disc: C.white, color: C.navy }));
  A(chip('Tanya di komen', Wd(134, 4), END, { y: 790, bg: C.teal }));
  A(hand('Take care!', Wd(135, 0), END, { x: 540, y: 980, size: 110 }));
  A(brandBug(0.3, END));

  const top = endCard(END, DUR - END);
  return {
    shots, els, duration: DUR, top,
    captionOpts(t) {
      if (t >= END) return { hidden: true };
      if (t >= 117.5 && t < 137.95) return { hl: C.amber };
      return {};
    },
  };
}
