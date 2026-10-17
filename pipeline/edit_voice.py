"""Cut retakes / false starts, tighten long pauses, and write a source->output time map.

Usage: python3 edit_voice.py <voice48.wav> <transcript.json> <out_dir>
"""
import json, sys
import numpy as np
import soundfile as sf

SR = 48000
# Source-time regions removed on purpose (seconds). Each is a retake, an
# editing cue, or a false start; the kept take carries the same words.
CUTS = [
    (0.00, 3.50),     # leading silence
    (18.95, 20.32),   # spoken edit cue "Iklan," (true onset of "kalau" is 20.44)
    (26.28, 27.98),   # stutter "boleh da-yang. Boleh." -> keeps "ubat, boleh datang"
    (35.42, 43.40),   # abandoned take "Ok, balik kepada soalan tadi. Bukan semua pesakit teruk."
    (127.00, 128.07), # filler "apa ni" between "boleh bagi" and "kesan ubat"
    (153.80, 160.60), # retake of "Serta kesan-kesan sampingan..." (second take kept)
    (184.40, 999.0),  # tail ("care" ends 184.16)
]
MAX_GAP = 0.55    # pauses longer than this get shortened...
KEEP_GAP = 0.32   # ...down to this (split around the quietest part)
XFADE = 0.012

def main(wav, tjson, out):
    x, sr = sf.read(wav, dtype="float32")
    assert sr == SR
    words = [w for s in json.load(open(tjson)) for w in s["words"]]
    # frame RMS (10 ms) for finding true silence inside gaps
    hop = SR // 100
    rms = np.sqrt(np.convolve(x**2, np.ones(hop) / hop, "same"))[::hop]

    cuts = list(CUTS)
    for a, b in zip(words, words[1:]):
        g0, g1 = a["e"], b["s"]
        if g1 - g0 <= MAX_GAP or any(c0 <= g0 <= c1 or c0 <= g1 <= c1 for c0, c1 in CUTS):
            continue
        # whisper word edges are loose: only remove the quiet core of the gap
        f0, f1 = int(g0 * 100), int(g1 * 100)
        seg = rms[f0:f1]
        thr = max(seg.min() * 4, 10 ** (-38 / 20))
        quiet = np.where(seg < thr)[0]
        if len(quiet) < 10:
            continue
        q0, q1 = (f0 + quiet[0]) / 100, (f0 + quiet[-1]) / 100
        remove = (q1 - q0) - KEEP_GAP
        if remove > 0.1:
            mid = (q0 + q1) / 2
            cuts.append((mid - remove / 2, mid + remove / 2))

    cuts.sort()
    keeps, t = [], 0.0
    for c0, c1 in cuts:
        if c0 > t:
            keeps.append((t, c0))
        t = max(t, c1)
    keeps.append((t, len(x) / SR)) if t < len(x) / SR else None

    xf = int(XFADE * SR)
    ramp = np.linspace(0, 1, xf, dtype="float32")
    parts, tmap, out_t = [], [], 0.0
    for s0, s1 in keeps:
        seg = x[int(s0 * SR):int(s1 * SR)].copy()
        if len(seg) < 2 * xf:
            continue
        seg[:xf] *= ramp
        seg[-xf:] *= ramp[::-1]
        tmap.append([round(s0, 4), round(s1, 4), round(out_t, 4)])
        parts.append(seg)
        out_t += len(seg) / SR
    y = np.concatenate(parts)
    sf.write(f"{out}/voice_edit.wav", y, SR)
    json.dump(tmap, open(f"{out}/timemap.json", "w"), indent=0)
    for c0, c1 in CUTS:
        for edge in (c0, c1):
            if 0 < edge < len(x) / SR:
                db = 20 * np.log10(rms[int(edge * 100) - 3:int(edge * 100) + 4].max() + 1e-9)
                print(f"cut edge {edge:7.2f}s  peak {db:6.1f} dB{'  <-- NOT SILENT' if db > -40 else ''}")
    print(f"kept {len(tmap)} pieces, {len(x)/SR:.2f}s -> {len(y)/SR:.2f}s")

if __name__ == "__main__":
    main(*sys.argv[1:4])
