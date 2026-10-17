"""Synthesised sound-effects library and scene ambiences (no third-party samples).

Every effect takes a numpy Generator so each cue gets its own variant (pitch, length, colour):
the same "pop" never sounds identical twice.
"""
import numpy as np
from scipy import signal

SR = 48000


def t_(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, min(hi, SR / 2 - 200)], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def sweep(x, f0, f1, q=0.8, blk=1024):
    """band-pass x with a centre frequency gliding f0 -> f1."""
    out = np.zeros_like(x)
    for i in range(0, len(x), blk):
        fc = f0 * (f1 / f0) ** (i / len(x))
        out[i:i + blk] = bp(x[i:i + blk + 2048], fc * (1 - q / 2), fc * (1 + q / 2))[:len(x[i:i + blk])]
    return out


def chirp(f, d):
    """sine with an arbitrary frequency curve f (array) or constant."""
    f = np.broadcast_to(f, (int(d * SR),))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def mix_in(out, x, i):
    """add x into out starting at sample i, clipped to out's bounds."""
    j = min(len(out), i + len(x))
    if 0 <= i < j:
        out[i:j] += x[:j - i]


def norm(x, peak=1.0):
    return x / (np.abs(x).max() + 1e-9) * peak


# ---------------- transitions / movement ----------------
def whoosh(r, d=None):
    d = d or r.uniform(0.38, 0.6); n = int(d * SR)
    x = sweep(r.standard_normal(n), r.uniform(200, 400), r.uniform(2500, 6000), r.uniform(0.7, 1.2))
    return norm(x * np.sin(np.pi * np.linspace(0, 1, n)) ** r.uniform(1.6, 2.8), 0.8)


def swipe(r):   # fast whip-pan
    d = r.uniform(0.22, 0.3); n = int(d * SR); u = np.linspace(0, 1, n)
    x = sweep(r.standard_normal(n), 600, r.uniform(7000, 9000), 0.9) * np.exp(-((u - 0.45) ** 2) / 0.03)
    return norm(x, 1.0)


def swish(r):   # soft slide for cards
    d = r.uniform(0.25, 0.4); n = int(d * SR)
    x = sweep(r.standard_normal(n), r.uniform(800, 1500), r.uniform(3000, 5000), 1.0)
    return norm(x * np.sin(np.pi * np.linspace(0, 1, n)) ** 2, 0.55)


def zoom(r):    # reverse swell into a thud
    a = riser(r, r.uniform(0.28, 0.36)); b = thud(r)
    return np.concatenate([a * 0.8, b])


def rewind(r):
    x = whoosh(r, 0.7)[::-1]
    return x * (1 + 0.45 * np.sin(2 * np.pi * r.uniform(8, 12) * t_(0.7)[:len(x)]))


def air(r):     # gentle breath for dissolves
    d = r.uniform(0.7, 1.0); n = int(d * SR)
    return norm(lp(r.standard_normal(n), r.uniform(1500, 2500)) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2, 0.35)


def riser(r, d=None):
    d = d or r.uniform(1.0, 1.4); n = int(d * SR); u = np.linspace(0, 1, n)
    x = sweep(r.standard_normal(n), 300, r.uniform(5000, 8000), 0.6) * u ** 2.2
    tone = chirp(200 * 2 ** (u * r.uniform(1.5, 2.5)), d) * u ** 3 * 0.25
    return norm(x + tone, 0.8)


def tear(r):
    d = r.uniform(0.45, 0.65); n = int(d * SR)
    imp = (r.random(n) < r.uniform(0.008, 0.016)) * r.standard_normal(n) * 4
    x = bp(imp + r.standard_normal(n) * 0.2, r.uniform(500, 900), r.uniform(5000, 8000))
    return norm(x * np.sin(np.pi * np.linspace(0, 1, n) ** 0.6), 0.85)


def camera(r):
    out = np.zeros(int(0.25 * SR))
    for off in (0.0, r.uniform(0.07, 0.1)):
        mix_in(out, bp(r.standard_normal(int(0.03 * SR)), 1500, 7000) * np.exp(-t_(0.03) * 150), int(off * SR))
    return norm(out, 0.8)


# ---------------- impacts ----------------
def hit(r):
    d = 0.9; t = t_(d); f0, f1 = r.uniform(80, 120), r.uniform(38, 50)
    body = chirp(f1 + (f0 - f1) * np.exp(-t * 18), d) * np.exp(-t * r.uniform(4, 6))
    click = hp(r.standard_normal(len(t)), 2500) * np.exp(-t * 70) * 0.35
    return norm(body + click, 1.0)


def boom(r):
    d = 2.4; t = t_(d)
    body = chirp(36 + 55 * np.exp(-t * 9), d) * np.exp(-t * 1.5)
    air_ = lp(r.standard_normal(len(t)), 900) * np.exp(-t * 3) * 0.3
    return norm(body + air_, 1.0)


def thud(r):
    d = 0.3; t = t_(d)
    return norm(chirp(r.uniform(55, 75) + 80 * np.exp(-t * 40), d) * np.exp(-t * 16), 0.9)


def braam(r):   # low cinematic brass swell (side-effects chapter)
    d = 2.6; t = t_(d); out = np.zeros_like(t)
    for f, a in [(55, 1), (82.4, 0.7), (110, 0.5), (164.8, 0.3)]:
        saw = 2 * ((f * t + r.random()) % 1) - 1
        out += a * saw
    out = lp(out, 900) * np.minimum(1, t / 0.12) * np.exp(-t * 0.9)
    mix_in(out, hit(r) * 0.4, 0)
    return norm(out, 1.0)


def stamp(r):
    d = 0.35; t = t_(d)
    thump = chirp(r.uniform(55, 70) + 110 * np.exp(-t * 40), d) * np.exp(-t * 14)
    slap = bp(r.standard_normal(len(t)), 400, 3500) * np.exp(-t * 35) * 0.7
    return norm(thump + slap, 1.0)


def logo(r):
    h, s = hit(r) * 0.7, shimmer(r) * 0.5
    out = np.zeros(max(len(h), len(s))); mix_in(out, h, 0); mix_in(out, s, 0)
    return norm(out, 0.9)


# ---------------- UI / text ----------------
def tap(r):     # light text reveal
    d = 0.06; t = t_(d); f = r.uniform(1400, 2400)
    return norm(chirp(f, d) * np.exp(-t * 120) + bp(r.standard_normal(len(t)), 3000, 8000) * np.exp(-t * 200) * 0.5, 0.5)


def thock(r):   # woodblock for big words
    d = 0.12; t = t_(d); f = r.uniform(500, 800)
    x = chirp(f, d) * np.exp(-t * 45) + chirp(f * 2.7, d) * np.exp(-t * 80) * 0.4 + bp(r.standard_normal(len(t)), 1000, 4000) * np.exp(-t * 150) * 0.3
    return norm(x, 0.85)


def tick(r):
    return tap(r) * 0.7


def click(r):
    d = 0.04; t = t_(d)
    return norm(bp(r.standard_normal(len(t)), 1500, 5000) * np.exp(-t * 180), 0.6)


def pop(r):
    d = 0.12; t = t_(d); f0 = r.uniform(300, 520); sweep_ = r.uniform(500, 900)
    return norm(chirp(f0 + sweep_ * np.exp(-t * 45), d) * np.exp(-t * 30), 0.8)


def bubble(r):  # brighter rising pop for chips with icons
    d = 0.1; t = t_(d); f0 = r.uniform(500, 800)
    return norm(chirp(f0 * (1 + 1.2 * (1 - np.exp(-t * 40))), d) * np.exp(-t * 35), 0.7)


def shimmer(r): # sparkle arpeggio
    d = 0.8; t = t_(d); out = np.zeros_like(t)
    base = r.choice([1760, 1976, 2093, 2349])
    for k, m in enumerate(r.permutation([1, 1.25, 1.5, 2, 2.5])[:4]):
        i = int(k * r.uniform(0.04, 0.07) * SR); n = len(t) - i
        mix_in(out, np.sin(2 * np.pi * base * m * t[:n]) * np.exp(-t[:n] * 9) / (k + 1), i)
    return norm(out, 0.45)


def ding(r):
    d = 1.2; t = t_(d); f = r.choice([1318, 1568, 1760]); out = np.zeros_like(t)
    for m, a in [(1, 1), (2.0, 0.3), (3.01, 0.15)]:
        out += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * (4 + m))
    return norm(out, 0.5)


def chime(r):
    d = 2.5; t = t_(d); out = np.zeros_like(t)
    for m, a in [(1, 1), (2.76, 0.4), (5.4, 0.2), (8.93, 0.1)]:
        out += a * np.sin(2 * np.pi * 880 * m * t) * np.exp(-t * (1.2 + m * 0.8))
    return norm(out, 0.5)


def glass(r):   # ampoule tink
    d = 1.0; t = t_(d); f = r.uniform(2600, 3600); out = np.zeros_like(t)
    for m, a in [(1, 1), (2.32, 0.5), (4.25, 0.25)]:
        out += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * (7 + 4 * m))
    return norm(out, 0.6)


# ---------------- paper / pencil ----------------
def paper(r):
    d = r.uniform(0.3, 0.45); n = int(d * SR)
    am = np.abs(lp(r.standard_normal(n), r.uniform(25, 60))); am /= am.max() + 1e-9
    x = bp(r.standard_normal(n), r.uniform(700, 1200), r.uniform(5000, 8000)) * am
    return norm(x * np.sin(np.pi * np.linspace(0, 1, n)), 0.75)


def scribble(r, d=0.45):
    t = t_(d); x = bp(r.standard_normal(len(t)), 2500, 9000)
    f = r.uniform(8, 14)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * r.uniform(1.5, 3) * t))
    return norm(x * am * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05), 0.55)


def marker(r):  # felt-tip highlighter squeak
    d = r.uniform(0.28, 0.4); t = t_(d)
    x = sweep(r.standard_normal(len(t)), r.uniform(1800, 2500), r.uniform(3200, 4200), 0.25)
    return norm(x * np.sin(np.pi * np.linspace(0, 1, len(t))) ** 0.8, 0.6)


def check(r):
    a, b = scribble(r, 0.1), scribble(r, 0.18); out = np.zeros(int(0.32 * SR))
    mix_in(out, a, 0); mix_in(out, b, int(0.12 * SR))
    return norm(out, 0.7)


def typewriter(r, d=1.0, cps=28):
    out = np.zeros(int((d + 0.15) * SR))
    for k in range(int(d * cps)):
        mix_in(out, click(r) * (0.6 + 0.4 * r.random()), int((k / cps + r.random() * 0.012) * SR))
    bell = ding(r)[:int(0.4 * SR)] * 0.3; mix_in(out, bell, max(0, len(out) - len(bell)))
    return norm(out, 0.6)


def pill(r):    # plastic pills rattling
    d = 0.35; out = np.zeros(int(d * SR))
    for _ in range(r.integers(6, 11)):
        f = r.uniform(3000, 6500); n = int(0.03 * SR); tt = np.arange(n) / SR
        c = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 260) + bp(r.standard_normal(n), 3000, 9000) * np.exp(-tt * 300) * 0.4
        mix_in(out, c * r.uniform(0.4, 1), int(r.uniform(0, d - 0.03) * SR))
    return norm(out, 0.6)


def heartbeat(r):
    out = np.zeros(int(2.6 * SR))
    for k in range(3):
        for off, g in ((0, 1.0), (0.28, 0.65)):
            mix_in(out, thud(r) * g, int((k * 0.85 + off) * SR))
    return norm(lp(out, 300), 0.9)


def swell(r, d=1.3):
    n = int(d * SR); t = t_(d); x = r.standard_normal(n); out = np.zeros(n)
    for i in range(0, n, 2048):
        out[i:i + 2048] = lp(x[i:i + 4096], 300 + 6000 * (i / n) ** 2)[:len(x[i:i + 2048])]
    return out * (t / d) ** 2.5 * 0.35


FX = {k: v for k, v in globals().items() if callable(v) and k in (
    "whoosh swipe swish zoom rewind air riser tear camera hit boom thud braam stamp logo tap thock tick click pop "
    "bubble shimmer ding chime glass paper scribble marker check typewriter pill heartbeat swell").split()}
FX["type"] = FX["typewriter"]
# relative loudness of each family on the SFX bus
GAIN = {"tap": 0.55, "tick": 0.4, "thock": 0.75, "pop": 0.7, "bubble": 0.65, "shimmer": 0.5, "paper": 0.7, "swish": 0.55,
        "scribble": 0.6, "marker": 0.55, "check": 0.7, "ding": 0.45, "whoosh": 0.85, "swipe": 0.9, "zoom": 0.85, "air": 0.5,
        "riser": 0.6, "hit": 1.0, "boom": 1.0, "thud": 0.8, "braam": 0.95, "stamp": 0.95, "tear": 0.85, "camera": 0.7,
        "logo": 0.9, "chime": 0.6, "glass": 0.6, "type": 0.55, "typewriter": 0.55, "pill": 0.6, "heartbeat": 0.8,
        "rewind": 0.8, "click": 0.55, "swell": 0.6}
TRANSITION = {"whip": "swipe", "zoom": "zoom", "tear": "tear", "push": "swish", "fade": "air", "flash": "camera", "iris": "whoosh"}


# ---------------- ambiences (looped beds per clip) ----------------
def amb_crickets(r, d):
    t = t_(d); out = np.zeros_like(t)
    for _ in range(3):
        f = r.uniform(4200, 5200); rate = r.uniform(14, 20); ph = r.random() * 6
        gate = (np.sin(2 * np.pi * rate * t + ph) > 0.6) * (np.sin(2 * np.pi * r.uniform(0.4, 0.8) * t + ph) > -0.2)
        out += np.sin(2 * np.pi * f * t) * lp(gate.astype(float), 200) * r.uniform(0.3, 0.6)
    return out + lp(r.standard_normal(len(t)), 300) * 0.08


def amb_birds(r, d):
    t = t_(d); out = lp(r.standard_normal(len(t)), 1200) * 0.05
    k = 0.3
    while k < d - 0.5:
        n = int(r.uniform(0.08, 0.25) * SR); tt = np.arange(n) / SR; f0 = r.uniform(2500, 4500)
        c = np.sin(2 * np.pi * np.cumsum(f0 + 900 * np.sin(2 * np.pi * r.uniform(15, 30) * tt)) / SR) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
        mix_in(out, c * r.uniform(0.15, 0.45), int(k * SR)); k += r.uniform(0.25, 1.4)
    return out


def amb_room(r, d):    # air-con hum + distant murmur
    t = t_(d); hum = lp(r.standard_normal(len(t)), 250) * 0.5 + np.sin(2 * np.pi * 100 * t) * 0.03
    mur = bp(r.standard_normal(len(t)), 300, 1400) * (0.5 + 0.5 * lp(np.abs(r.standard_normal(len(t))), 2)) * 0.25
    return hum + mur


def amb_crowd(r, d):   # mamak: chatter + cutlery
    out = amb_room(r, d) * 1.6; k = 0.2
    while k < d - 0.2:
        mix_in(out, glass(r)[:int(0.3 * SR)] * r.uniform(0.05, 0.15), int(k * SR)); k += r.uniform(0.4, 1.5)
    return out


def amb_train(r, d):
    t = t_(d); out = lp(r.standard_normal(len(t)), 180) * 1.2 + bp(r.standard_normal(len(t)), 400, 1200) * 0.1
    k = 0.4
    while k < d - 0.2:
        for off in (0, 0.12):
            mix_in(out, thud(r)[:int(0.15 * SR)] * 0.25, int((k + off) * SR))
        k += r.uniform(0.9, 1.1)
    return out


def amb_street(r, d):
    t = t_(d); out = lp(r.standard_normal(len(t)), 220) * 0.8 + amb_birds(r, d) * 0.5
    k = r.uniform(0.3, 1.0)
    while k < d - 1.2:
        mix_in(out, lp(whoosh(r, 1.6), 1200) * 0.35, int(k * SR)); k += r.uniform(2, 4)
    return out


def amb_machine(r, d):
    t = t_(d); return lp(r.standard_normal(len(t)), 300) * 0.6 + bp(r.standard_normal(len(t)), 800, 2500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 3.2 * t))) * 0.08


def amb_drone(r, d):   # abstract macro shots
    t = t_(d); return (np.sin(2 * np.pi * 55 * t) * 0.3 + np.sin(2 * np.pi * 82.5 * t + 1) * 0.2) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * t)) + lp(r.standard_normal(len(t)), 600) * 0.1


AMBIENCE = {  # clip -> (bed, level)
    "v01": (amb_crickets, 0.8), "v02": (amb_crickets, 0.7), "v20": (amb_crickets, 0.9),
    "v04": (amb_birds, 0.8), "v07": (amb_birds, 0.6), "v18": (amb_birds, 0.9), "v19": (amb_birds, 1.0), "v23": (amb_birds, 0.8),
    "v03": (amb_room, 0.7), "v06": (amb_room, 0.7), "v10": (amb_room, 0.8), "v14": (amb_room, 0.7), "v16": (amb_room, 0.9),
    "v17": (amb_room, 0.7), "v24": (amb_room, 0.7), "v05": (amb_street, 0.9), "v15": (amb_crowd, 1.0),
    "v11": (amb_train, 1.0), "v12": (amb_train, 0.7), "v13": (amb_machine, 0.8),
    "v09": (amb_drone, 0.7), "v21": (amb_drone, 0.8), "v22": (amb_drone, 0.6), "v25": (amb_drone, 0.6),
}
