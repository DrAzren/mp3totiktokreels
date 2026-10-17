"""Procedural sound design + score, ducked under the voice, mastered for TikTok.

Usage: python3 audio_mix.py <voice_clean.wav> <sfx.json> <duration_s> <out.wav>
(reads shots.json from the same folder as sfx.json for transition sounds and scene ambience)
Everything here is synthesised (no third-party samples), so it is safe for social distribution.
"""
import json, os, sys
import numpy as np
import soundfile as sf
from scipy import signal

import sfx_synth as sx

SR = 48000
rs = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, fs=SR, output="sos"), x)


# ---------------- SFX ----------------
def place(L, R, x, t0, g, pan):
    i = int(t0 * SR); j = min(len(L), i + len(x))
    if i < 0 or i >= len(L):
        return
    L[i:j] += x[:j - i] * g * np.sqrt(0.5 - pan / 2) * 1.41
    R[i:j] += x[:j - i] * g * np.sqrt(0.5 + pan / 2) * 1.41


def build_sfx(cues, shots, n):
    """One-shot effects from the renderer's cue list, plus a transition sound on every cut."""
    L, R = np.zeros(n), np.zeros(n)
    cues = list(cues)
    for s in shots[1:]:
        kind = sx.TRANSITION.get(s["tr"] or "")
        if kind:   # land the peak of the transition sound on the cut
            lead = {"swipe": 0.12, "zoom": 0.32, "tear": 0.05, "swish": 0.1, "air": 0.3, "camera": 0.0, "whoosh": 0.2}[kind]
            cues.append({"type": kind, "t": max(0.0, s["t0"] - lead), "gain": 0.9})
    last = {}
    for k, c in enumerate(sorted(cues, key=lambda c: c["t"])):
        typ = c["type"]
        if typ not in sx.FX or c["gain"] <= 0:
            continue
        if c["t"] - last.get(typ, -9) < 0.06:   # de-clutter near-simultaneous duplicates
            continue
        last[typ] = c["t"]
        r = np.random.default_rng(1000 + k)       # every cue gets its own variant
        fn = sx.FX[typ]
        x = fn(r, c["dur"]) if typ in ("scribble", "type", "typewriter") and "dur" in c else fn(r)
        pan = r.uniform(-0.4, 0.4) if typ in ("pop", "bubble", "tap", "paper", "scribble", "check", "shimmer", "pill", "marker", "glass") else 0.0
        place(L, R, x, c["t"], c["gain"] * sx.GAIN.get(typ, 0.6), pan)
    return np.stack([L, R], 1)


def build_ambience(shots, n):
    """Scene beds matched to each B-roll clip, crossfaded at the cuts."""
    out = np.zeros((n, 2)); xf = 0.35
    for k, s in enumerate(shots):
        bed = sx.AMBIENCE.get(s.get("clip") or "")
        if not bed:
            continue
        fn, lvl = bed
        t0, t1 = max(0.0, s["t0"] - xf), min(n / SR, s["t1"] + xf)
        r = np.random.default_rng(500 + k)
        a, b = fn(r, t1 - t0), fn(np.random.default_rng(900 + k), t1 - t0)   # decorrelated L/R
        m = len(a); e = np.ones(m); f = int(xf * SR)
        e[:f] = np.linspace(0, 1, f); e[-f:] = np.linspace(1, 0, f)
        i = int(t0 * SR); j = min(n, i + m)
        out[i:j, 0] += a[:j - i] * e[:j - i] * lvl; out[i:j, 1] += b[:j - i] * e[:j - i] * lvl
    return out


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
            r = sx.swell(rs, max(0.5, s1 - s0)); add(m, r, s0, 0.35 * L["riser"])
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
    shots_path = os.path.join(os.path.dirname(os.path.abspath(sfx_json)), "shots.json")
    shots = json.load(open(shots_path)) if os.path.exists(shots_path) else []
    music = build_music(dur)
    fx = build_sfx(json.load(open(sfx_json)), shots, n)
    amb = build_ambience(shots, n)
    # duck music (~ -9 dB) and ambience (~ -6 dB) while he talks
    e = envelope(voice); e = np.clip(e / (np.percentile(e[e > 1e-4], 95) + 1e-9), 0, 1)
    music *= (1 - 0.65 * e)[:, None]; amb *= (1 - 0.5 * e)[:, None]
    rms = lambda x: np.sqrt(np.mean(x ** 2) + 1e-12)
    speech = np.abs(voice) > 1e-3
    vr, vpk = rms(voice[speech]), np.percentile(np.abs(voice[speech]), 99.9)
    music *= (vr * 10 ** (-15 / 20)) / rms(music)          # music bed ~15 dB under the voice
    amb *= (vr * 10 ** (-27 / 20)) / rms(amb[np.abs(amb).sum(1) > 1e-6])   # room tone, felt more than heard
    # SFX bus: loud transients (~5 dB under voice peaks), glued with a soft-knee limiter
    fx *= (vpk * 10 ** (-5 / 20)) / (np.percentile(np.abs(fx[np.abs(fx) > 1e-4]), 99.5) + 1e-9)
    fx = np.tanh(fx / (vpk * 1.1)) * vpk * 1.1
    mix = music + amb + fx + voice[:, None]
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    for name, stem in (("music", music), ("sfx", fx), ("amb", amb)):
        sf.write(out.replace(".wav", f"_{name}.wav"), stem.astype(np.float32), SR, subtype="FLOAT")
    print("mix written", out, f"{dur:.2f}s", f"{len(shots)} shots")


if __name__ == "__main__":
    main(*sys.argv[1:5])
