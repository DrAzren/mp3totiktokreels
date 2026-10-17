"""Procedural sound design + score, ducked under the voice, mastered for TikTok.

Usage: python3 audio_mix.py <voice_clean.wav> <sfx.json> <duration_s> <out.wav>
Everything here is synthesised (no third-party samples), so it is safe for social distribution.
"""
import json, sys
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
rs = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env_ar(n, a, r, curve=3.0):
    """attack/release envelope over n samples (a, r in seconds)."""
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) * curve / max(r, 1e-4))
    return e


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def noise(d):
    return rs.standard_normal(int(d * SR))


def sweep_noise(d, f0, f1, q=0.6):
    """noise through a band-pass whose centre glides f0 -> f1 (block-wise)."""
    x, out, blk = noise(d), np.zeros(int(d * SR)), 1024
    for i in range(0, len(x), blk):
        u = i / len(x)
        fc = f0 * (f1 / f0) ** u
        out[i:i + blk] = bp(x[i:i + blk + 2048], fc * (1 - q / 2), min(fc * (1 + q / 2), SR / 2 - 100))[:len(x[i:i + blk])]
    return out


# ---------------- SFX ----------------
def whoosh(d=0.5):
    n = int(d * SR); x = sweep_noise(d, 300, 4000, 1.0)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2.2
    return x * e * 0.5


def rewind(d=0.7):
    x = whoosh(d)[::-1] * 0.8
    t = t_(d); return x * (1 + 0.4 * np.sin(2 * np.pi * 9 * t))


def hit(d=0.9, f0=90, f1=42):
    t = t_(d); f = f1 + (f0 - f1) * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    click = hp(noise(d), 2000) * np.exp(-t * 60) * 0.3
    return (body + click) * 0.9


def boom():
    t = t_(2.2); f = 38 + 50 * np.exp(-t * 10)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    air = lp(noise(2.2), 900) * np.exp(-t * 3) * 0.25
    return (body + air) * 1.0


def tick():
    t = t_(0.05); return (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 140) + bp(noise(0.05), 3000, 7000) * np.exp(-t * 200) * 0.4) * 0.35


def click():
    t = t_(0.04); return bp(noise(0.04), 1500, 5000) * np.exp(-t * 180) * 0.6


def pop():
    t = t_(0.12); f = 380 + 700 * np.exp(-t * 45)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32) * 0.55


def paper(d=0.38):
    n = int(d * SR); x = bp(noise(d), 900, 7000)
    am = np.abs(lp(rs.standard_normal(n), 40)); am /= am.max() + 1e-9
    return x * am * np.sin(np.pi * np.linspace(0, 1, n)) * 0.55


def tear(d=0.55):
    n = int(d * SR); imp = (rs.random(n) < 0.012) * rs.standard_normal(n) * 4
    x = bp(imp + noise(d) * 0.15, 700, 6000) * np.sin(np.pi * np.linspace(0, 1, n) ** 0.7)
    return x * 0.6


def scribble(d=0.45):
    t = t_(d); x = bp(noise(d), 2500, 9000)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 11 * t + 3 * np.sin(2 * np.pi * 2.3 * t))
    return x * am * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05) * 0.35


def stamp():
    t = t_(0.35); f = 60 + 110 * np.exp(-t * 40)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    slap = bp(noise(0.35), 400, 3500) * np.exp(-t * 35) * 0.6
    return (thump + slap) * 0.9


def check():
    a, b = scribble(0.1), scribble(0.18); out = np.zeros(int(0.32 * SR)); out[:len(a)] += a; out[int(0.12 * SR):int(0.12 * SR) + len(b)] += b
    return out * 1.3


def typewriter(d=1.0, cps=28):
    out = np.zeros(int((d + 0.1) * SR))
    for k in range(int(d * cps)):
        c = click() * (0.6 + 0.4 * rs.random()); i = int((k / cps + rs.random() * 0.01) * SR); out[i:i + len(c)] += c
    return out * 0.7


def swell(d=1.3):
    n = int(d * SR); t = t_(d); x = noise(d)
    out = np.zeros(n); blk = 2048
    for i in range(0, n, blk):
        u = i / n; out[i:i + blk] = lp(x[i:i + blk + 2048], 300 + 6000 * u ** 2)[:len(x[i:i + blk])]
    return out * (t / d) ** 2.5 * 0.35


def chime():
    t = t_(2.5); out = np.zeros_like(t)
    for m, a in [(1, 1), (2.76, 0.4), (5.4, 0.2), (8.93, 0.1)]:
        out += a * np.sin(2 * np.pi * 880 * m * t) * np.exp(-t * (1.2 + m * 0.8))
    return out * 0.18


SFX_FN = {"whoosh": whoosh, "rewind": rewind, "hit": hit, "boom": boom, "tick": tick, "click": click, "pop": pop,
          "paper": paper, "tear": tear, "scribble": scribble, "stamp": stamp, "check": check, "type": typewriter,
          "swell": swell, "chime": chime}
SFX_GAIN = {"tick": 0.35, "pop": 0.55, "paper": 0.6, "scribble": 0.55, "whoosh": 0.7, "hit": 0.85, "boom": 1.0,
            "stamp": 0.8, "tear": 0.7, "check": 0.6, "type": 0.45, "swell": 0.6, "chime": 0.6, "click": 0.5, "rewind": 0.7}


def build_sfx(cues, n):
    L, R = np.zeros(n), np.zeros(n)
    last = {}
    for c in sorted(cues, key=lambda c: c["t"]):
        k = c["type"]
        if k not in SFX_FN or c["gain"] <= 0:
            continue
        if c["t"] - last.get(k, -9) < 0.07:   # de-clutter near-simultaneous duplicates
            continue
        last[k] = c["t"]
        fn = SFX_FN[k]
        x = fn(c["dur"]) if "dur" in c and k in ("scribble", "type") else fn()
        x = x * c["gain"] * SFX_GAIN[k]
        pan = rs.uniform(-0.35, 0.35) if k in ("pop", "tick", "paper", "scribble", "check") else 0
        i = int(c["t"] * SR); j = min(n, i + len(x))
        if i >= n:
            continue
        L[i:j] += x[:j - i] * np.sqrt(0.5 - pan / 2) * 1.41
        R[i:j] += x[:j - i] * np.sqrt(0.5 + pan / 2) * 1.41
    return np.stack([L, R], 1)


# ---------------- music ----------------
NOTE = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def hz(name, octv):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octv + 1) - 69) / 12)


CHORDS = {  # root, triad tones (pitch classes), colour tone
    "Dm": ("D", ["D", "F", "A"], "E"), "Bb": ("Bb", ["Bb", "D", "F"], "C"), "F": ("F", ["F", "A", "C"], "G"),
    "C": ("C", ["C", "E", "G"], "D"), "Gm": ("G", ["G", "Bb", "D"], "A"), "A": ("A", ["A", "C#", "E"], "B"),
    "Csus": ("C", ["C", "F", "G"], "D"), "Fmaj7": ("F", ["F", "A", "C", "E"], "G"),
}
BPM = 84
BEAT = 60 / BPM
# (start, end, chord progression (each chord = 2 bars), layers)
SECTIONS = [
    (0.0, 7.65, ["Dm"], {"drone": 1, "heart": 1, "riser": 1}),
    (7.7, 15.4, ["Dm", "Bb"], {"pad": 0.8, "arp": 0.5}),
    (15.4, 29.4, ["F", "C", "Dm", "Bb"], {"pad": 1, "keys": 0.8}),
    (29.4, 41.4, ["Dm", "Bb", "F", "C"], {"pad": 0.8, "arp": 0.8, "kick": 0.5}),
    (41.4, 55.0, ["Dm", "Bb", "F", "C"], {"pad": 0.9, "arp": 0.9, "kick": 0.6, "sub": 0.6}),
    (55.0, 117.5, ["Dm", "Bb", "F", "C"], {"pad": 0.85, "arp": 1, "kick": 0.7, "sub": 0.7}),
    (117.5, 137.9, ["Dm", "Gm", "Dm", "A"], {"pad": 0.9, "keys": 0.5, "drone": 0.4}),
    (137.9, 148.0, ["Bb", "C", "Dm", "C"], {"pad": 0.9, "arp": 0.8, "kick": 0.5}),
    (148.0, 152.4, ["Csus"], {"pad": 0.8, "riser": 0.6}),
    (152.4, 159.5, ["F", "C", "Dm", "Bb"], {"pad": 1.1, "arp": 1, "keys": 0.8, "kick": 0.6, "sub": 0.7}),
    (159.5, 999, ["Fmaj7"], {"pad": 1.0, "keys": 0.7}),
]


def pad_voice(f, d, bright=1.0):
    t = t_(d); out = np.zeros_like(t)
    for det in (-0.12, 0, 0.11):
        ff = f * 2 ** (det / 12)
        for h in range(1, 7):
            out += np.sin(2 * np.pi * ff * h * t + rs.random() * 6) / h ** (1.6 / bright)
    e = np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 1.0)
    return out * np.clip(e, 0, 1)


def pluck(f, d=1.6, bright=1.0):
    t = t_(d); out = np.zeros_like(t)
    for h in range(1, 8):
        out += np.sin(2 * np.pi * f * h * (1 + 0.0004 * h * h) * t) * np.exp(-t * (2.2 + h * 1.4 / bright)) / h ** 1.3
    return out * np.minimum(1, t / 0.004)


def kick():
    t = t_(0.35); f = 45 + 70 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def add(buf, x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR); j = min(len(buf), i + len(x))
    if i >= len(buf) or j <= i:
        return
    buf[i:j, 0] += x[:j - i] * g * np.sqrt(0.5 - pan / 2) * 1.41
    buf[i:j, 1] += x[:j - i] * g * np.sqrt(0.5 + pan / 2) * 1.41


def build_music(dur):
    n = int(dur * SR); m = np.zeros((n, 2))
    for s0, s1, prog_, L in SECTIONS:
        s1 = min(s1, dur)
        seg = 8 * BEAT  # two bars per chord
        k, t = 0, s0
        while t < s1 - 0.05:
            name = prog_[k % len(prog_)]; root, tones, colour = CHORDS[name]
            d = min(seg, s1 - t) + 1.0
            if "pad" in L:
                for i, pc in enumerate(tones):
                    add(m, pad_voice(hz(pc, 3 if NOTE[pc] >= NOTE["F"] else 4), d), t, 0.022 * L["pad"], pan=(i - 1) * 0.5)
                add(m, pad_voice(hz(root, 2), d, 0.7), t, 0.03 * L["pad"])
            if "drone" in L:
                add(m, pad_voice(hz("D", 2), d, 0.5) + pad_voice(hz("A", 2), d, 0.5), t, 0.03 * L["drone"])
            if "sub" in L:
                tt = t_(d); add(m, np.sin(2 * np.pi * hz(root, 1) * tt) * np.minimum(1, tt / 0.5) * np.minimum(1, (d - tt) / 0.5), t, 0.08 * L["sub"])
            if "keys" in L:  # soft chord stabs on beat 1 and the 'and' of 3
                for off in (0, 2.5 * BEAT, 4 * BEAT, 6.5 * BEAT):
                    if t + off < s1:
                        for i, pc in enumerate(tones):
                            add(m, pluck(hz(pc, 4), 2.2, 0.8), t + off + i * 0.012, 0.035 * L["keys"], pan=(i - 1) * 0.3)
            if "arp" in L:  # 8th-note arpeggio
                pat = [0, 1, 2, 1, 3, 2, 1, 2]
                pool = [hz(p, 4) for p in tones] + [hz(colour, 5)]
                for b in range(16):
                    tb = t + b * BEAT / 2
                    if tb >= s1:
                        break
                    f = pool[pat[b % 8] % len(pool)] * (2 if (k % 4 == 3 and b >= 8) else 1)
                    add(m, pluck(f, 1.2, 1.2), tb, 0.03 * L["arp"] * (1.0 if b % 2 == 0 else 0.7), pan=0.35 * np.sin(b))
            if "kick" in L:  # beats 1 and 3 of each bar
                for b in (0, 2, 4, 6):
                    if t + b * BEAT < s1:
                        add(m, kick(), t + b * BEAT, 0.16 * L["kick"])
            t += seg; k += 1
        if "heart" in L:  # soft lub-dub at ~72 bpm
            b = s0 + 0.3
            while b < s1 - 0.3:
                add(m, kick() * 0.9, b, 0.22 * L["heart"]); add(m, kick() * 0.6, b + 0.28, 0.18 * L["heart"]); b += 60 / 72
        if "riser" in L:
            r = swell(max(0.5, s1 - s0)); add(m, r, s0, 0.35 * L["riser"])
    # simple stereo reverb: exponentially decaying noise IR
    ir_len = int(2.4 * SR); tt = np.arange(ir_len) / SR
    irL = rs.standard_normal(ir_len) * np.exp(-tt * 2.6); irR = rs.standard_normal(ir_len) * np.exp(-tt * 2.6)
    irL[:int(0.012 * SR)] = 0; irR[:int(0.017 * SR)] = 0
    irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
    wet = np.stack([signal.fftconvolve(m[:, 0], irL)[:n], signal.fftconvolve(m[:, 1], irR)[:n]], 1)
    m = m * 0.7 + wet * 0.55
    m = lp(m.T, 9000).T
    fade = np.ones(n); fo = int(2.5 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
    return m * fade[:, None]


def envelope(x, att=0.03, rel=0.35):
    a = np.abs(x); out = np.zeros_like(a); v = 0.0
    # one-pole follower on a 10x decimated signal for speed
    dec = 10; ad = a[: len(a) // dec * dec].reshape(-1, dec).max(1); od = np.zeros_like(ad)
    ga, gr = np.exp(-1 / (att * SR / dec)), np.exp(-1 / (rel * SR / dec))
    for i, s in enumerate(ad):
        v = ga * v + (1 - ga) * s if s > v else gr * v + (1 - gr) * s; od[i] = v
    out[: len(od) * dec] = np.repeat(od, dec)
    return out


def main(voice_wav, sfx_json, dur, out):
    dur = float(dur); n = int(dur * SR)
    v, sr = sf.read(voice_wav, dtype="float64"); assert sr == SR
    if v.ndim > 1:
        v = v.mean(1)
    voice = np.zeros(n); voice[:min(n, len(v))] = v[:n]
    music = build_music(dur)
    fx = build_sfx(json.load(open(sfx_json)), n)
    # duck music under speech (~ -9 dB while talking)
    e = envelope(voice); e = e / (np.percentile(e[e > 1e-4], 95) + 1e-9)
    duck = 1 - 0.65 * np.clip(e, 0, 1)
    music *= duck[:, None]
    rms = lambda x: np.sqrt(np.mean(x ** 2) + 1e-12)
    vr = rms(voice[np.abs(voice) > 1e-3])
    music *= (vr * 10 ** (-15 / 20)) / rms(music)      # music bed sits ~15 dB under the voice
    fx *= (vr * 10 ** (-9 / 20)) / (np.percentile(np.abs(fx[np.abs(fx) > 1e-4]), 99) + 1e-9) * 1.1
    mix = music + fx + voice[:, None]
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    sf.write(out.replace(".wav", "_music.wav"), music.astype(np.float32), SR, subtype="FLOAT")
    sf.write(out.replace(".wav", "_sfx.wav"), fx.astype(np.float32), SR, subtype="FLOAT")
    print("mix written", out, f"{dur:.2f}s")


if __name__ == "__main__":
    main(*sys.argv[1:5])
