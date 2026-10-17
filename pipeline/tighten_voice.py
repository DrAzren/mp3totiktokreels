"""Second edit pass: shorten the pauses between words.

Usage: python3 tighten_voice.py <voice_edit.wav> <words.json> <out_dir>
Writes voice_tight.wav and tight_map.json ([[edit_time, tight_time], ...] breakpoints).

Pauses are found on the waveform (10 ms RMS below QUIET_DB), and breaths sitting between two
silences (noise-like spectrum, soft, outside any aligned word) are folded into the pause. Only
those samples are ever removed, so word onsets and tails cannot be clipped. The aligned words are used to skip silences inside a word (stop
closures) and to choose how much pause to keep for the context.
"""
import json, sys
import numpy as np
import soundfile as sf

TARGET = {"word": 0.07, "phrase": 0.12, "comma": 0.16, "sentence": 0.24, "section": 0.32}
QUIET_DB = -42
BREATH_MAX_DB = -14   # louder than this is speech, not a breath
BREATH_FLATNESS = 0.3  # spectral flatness; voiced sounds (possible syllables) score well below this
XFADE = 0.012


def runs(mask):
    """[(start, end)] frame index runs where mask is True."""
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def main(wav, words_json, out):
    x, sr = sf.read(wav, dtype="float32")
    toks = json.load(open(words_json))["tokens"]
    hop = sr // 100
    db = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop] + 1e-9)
    quiet = db < QUIET_DB
    covered = np.zeros(len(db), bool)
    for t in toks:
        covered[int(t["s"] * 100):int(t["e"] * 100)] = True

    def flatness(a, b):
        seg = x[a * hop:b * hop]
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))[20:len(seg) // 4] + 1e-9
        return float(np.exp(np.mean(np.log(spec))) / np.mean(spec))

    # fold breaths into the surrounding pause: soft, noise-like, outside words, silence on both sides
    for a, b in runs(~quiet):
        if 5 <= b - a <= 60 and db[a:b].max() < BREATH_MAX_DB and covered[a:b].mean() < 0.15 \
                and quiet[max(0, a - 4):a].all() and quiet[b:b + 4].all() and flatness(a, b) >= BREATH_FLATNESS:
            quiet[a:b] = True
    cuts = []
    for a, b in runs(quiet):
        s0, s1 = a / 100, b / 100
        if s1 - s0 < 0.1 or s0 < 0.05:
            continue
        mid = (s0 + s1) / 2
        if any(t["s"] + 0.02 < mid < t["e"] - 0.02 for t in toks):
            continue                                   # stop closure inside a word
        nxt = next((i for i, t in enumerate(toks) if t["s"] >= mid - 0.02), None)
        if nxt is None or nxt == 0:
            continue                                   # leading/trailing silence: leave for the edit
        pa, pb = toks[nxt - 1], toks[nxt]
        kind = ("section" if pa["section"] != pb["section"] else "sentence" if pa["text"][-1] in ".?!" else
                "comma" if pa["text"][-1] == "," else "phrase" if pa["phrase"] != pb["phrase"] else "word")
        keep = TARGET[kind]
        if s1 - s0 > keep + 0.03:
            cuts.append((s0 + keep * 0.55, s1 - keep * 0.45, kind))

    xf = int(XFADE * sr); ramp = np.linspace(0, 1, xf, dtype="float32")
    parts, bp, t, removed = [], [[0.0, 0.0]], 0.0, 0.0
    for c0, c1, _ in cuts:
        seg = x[int(t * sr):int(c0 * sr)].copy()
        if parts:
            seg[:xf] *= ramp
        seg[-xf:] *= ramp[::-1]
        parts.append(seg)
        bp.append([c0, c0 - removed]); removed += c1 - c0; bp.append([c1, c1 - removed]); t = c1
    seg = x[int(t * sr):].copy(); seg[:xf] *= ramp; parts.append(seg)
    y = np.concatenate(parts)
    bp.append([len(x) / sr, len(y) / sr])
    sf.write(f"{out}/voice_tight.wav", y, sr)
    json.dump([[round(a, 4), round(b, 4)] for a, b in bp], open(f"{out}/tight_map.json", "w"))
    by = {}
    for c0, c1, k in cuts:
        by[k] = round(by.get(k, 0) + (c1 - c0), 1)
    print(f"{len(cuts)} pauses shortened, {removed:.1f}s removed  {len(x)/sr:.2f}s -> {len(y)/sr:.2f}s", by)


if __name__ == "__main__":
    main(*sys.argv[1:4])
