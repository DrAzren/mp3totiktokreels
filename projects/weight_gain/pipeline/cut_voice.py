"""Align the full TTS take, remove the '~' phrases, tighten pauses, speed up slightly.

Usage: python3 cut_voice.py <take.wav> <captions_full.txt> <out_dir> [tempo]
Writes out_dir/captions.txt (kept lines), out_dir/voice_edit.wav.
"""
import json, subprocess, sys, os
import numpy as np, soundfile as sf
sys.path.insert(0, "/home/user/mp3totiktokreels/pipeline")
import align_captions as ac

wav, full, out = sys.argv[1:4]
tempo = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
os.makedirs(out, exist_ok=True)
lines = open(full, encoding="utf-8").read().splitlines()
open(f"{out}/_align_full.txt", "w").write("\n".join(l.lstrip("~") for l in lines))
open(f"{out}/captions.txt", "w").write("\n".join(l for l in lines if not l.startswith("~")) + "\n")
# which phrase ids are cut
cut_ids, pid = set(), -1
for l in lines:
    s = l.strip()
    if not s or s.startswith("# ") or s.startswith("## "):
        continue
    pid += 1
    if s.startswith("~"):
        cut_ids.add(pid)
ac.main(wav, f"{out}/_align_full.txt", out)
tok = json.load(open(f"{out}/words.json"))["tokens"]
x, sr = sf.read(wav, dtype="float32")
if x.ndim > 1: x = x.mean(1)
# cut ranges: from end of previous kept word to end of last cut word
ranges = []
for i, t in enumerate(tok):
    if t["phrase"] in cut_ids:
        prev_end = tok[i - 1]["e"] + 0.02 if i else 0
        if ranges and ranges[-1][1] >= tok[i-1]["e"]:
            ranges[-1][1] = t["e"] + 0.02
        else:
            ranges.append([prev_end, t["e"] + 0.02])
print("cuts:", [(round(a, 2), round(b, 2)) for a, b in ranges])
keep = np.ones(len(x), bool)
for a, b in ranges:
    keep[int(a * sr):int(b * sr)] = False
# word mask for pause tightening (kept words only)
inword = np.zeros(len(x), bool)
for t in tok:
    if t["phrase"] not in cut_ids:
        inword[max(0, int((t["s"] - 0.03) * sr)):int((t["e"] + 0.03) * sr)] = True
# shorten every gap between kept words to a context target
kept_tok = [t for t in tok if t["phrase"] not in cut_ids]
for a, b in zip(kept_tok, kept_tok[1:]):
    gs, ge = a["e"] + 0.03, b["s"] - 0.03
    if ge - gs <= 0: continue
    end_char = a["text"][-1]
    newsec = a.get("section") != b.get("section")
    tgt = 0.30 if newsec else 0.20 if end_char in ".?!\"" else 0.12 if end_char == "," else 0.06
    if ge - gs > tgt:
        mid = (gs + ge) / 2
        keep[int((mid - (ge - gs - tgt) / 2) * sr):int((mid + (ge - gs - tgt) / 2) * sr)] = False
# leading/trailing silence
keep[:max(0, int((kept_tok[0]["s"] - 0.15) * sr))] = False
keep[int((kept_tok[-1]["e"] + 0.4) * sr):] = False
# apply with 5 ms crossfades at each splice
y, seg, i = [], None, 0
idx = np.flatnonzero(np.diff(np.concatenate([[0], keep.astype(np.int8), [0]])))
fade = int(0.005 * sr)
for s, e in zip(idx[::2], idx[1::2]):
    piece = x[s:e].copy()
    if len(piece) > 2 * fade:
        piece[:fade] *= np.linspace(0, 1, fade); piece[-fade:] *= np.linspace(1, 0, fade)
    y.append(piece)
y = np.concatenate(y)
sf.write(f"{out}/_voice_cut.wav", y, sr)
print(f"source {len(x)/sr:.1f}s -> cut {len(y)/sr:.1f}s -> tempo {tempo}: {len(y)/sr/tempo:.1f}s")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{out}/_voice_cut.wav", "-af", f"atempo={tempo}", "-ar", "48000", "-ac", "1", f"{out}/voice_edit.wav"], check=True)
