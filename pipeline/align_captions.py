"""Force-align captions.txt to the edited voice track (torchaudio MMS_FA).

Usage: python3 align_captions.py <voice_edit.wav> <captions.txt> <out_dir>
Writes words.json (display tokens with times + phrase/section ids) and captions.srt.
"""
import json, re, sys
import soundfile as sf
import torch, torchaudio
from torchaudio.pipelines import MMS_FA as bundle


def parse(path):
    tokens, sections, sec, phrase = [], [], None, -1
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("# "):
            continue
        if line.startswith("## "):
            sec = line[3:].strip()
            sections.append(sec)
            continue
        phrase += 1
        for tok in line.split():
            hl = tok.startswith("*")
            tok = tok.lstrip("*")
            disp, _, al = tok.partition("=")
            al = (al or disp).lower().replace("_", " ").replace("-", " ")
            al = re.sub(r"[^a-z ]", "", al).split()
            tokens.append({"text": disp, "align": al, "hl": hl, "phrase": phrase, "section": sec})
    return tokens, sections


def main(wav, cap, out):
    tokens, sections = parse(cap)
    data, sr = sf.read(wav, dtype="float32", always_2d=True)
    wave = torch.from_numpy(data.mean(1)).unsqueeze(0)
    wave = torchaudio.functional.resample(wave, sr, bundle.sample_rate)
    model = bundle.get_model(with_star=False)
    labels = bundle.get_labels(star=None)
    dictionary = {c: i for i, c in enumerate(labels)}
    words = [w for t in tokens for w in t["align"]]
    with torch.inference_mode():
        emission, _ = model(wave)
    targets = torch.tensor([[dictionary[c] for w in words for c in w]], dtype=torch.int32)
    ali, scores = torchaudio.functional.forced_align(emission, targets, blank=0)
    spans = torchaudio.functional.merge_tokens(ali[0], scores[0].exp())
    ratio = wave.size(1) / emission.size(1) / bundle.sample_rate
    # group character spans back into words
    i, wt = 0, []
    for w in words:
        s = spans[i:i + len(w)]
        i += len(w)
        wt.append((s[0].start * ratio, s[-1].end * ratio, sum(x.score for x in s) / len(s)))
    k = 0
    for t in tokens:
        n = len(t["align"])
        t["s"], t["e"] = round(wt[k][0], 3), round(wt[k + n - 1][1], 3)
        t["conf"] = round(min(x[2] for x in wt[k:k + n]), 3)
        k += n
        del t["align"]
    json.dump({"sections": sections, "tokens": tokens}, open(f"{out}/words.json", "w"), ensure_ascii=False, indent=0)

    def ts(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")

    with open(f"{out}/captions.srt", "w", encoding="utf-8") as f:
        phrases = {}
        for t in tokens:
            phrases.setdefault(t["phrase"], []).append(t)
        for n, (pid, ws) in enumerate(sorted(phrases.items()), 1):
            nxt = phrases.get(pid + 1)
            end = min(ws[-1]["e"] + 0.6, nxt[0]["s"]) if nxt else ws[-1]["e"] + 0.8
            f.write(f"{n}\n{ts(ws[0]['s'])} --> {ts(end)}\n{' '.join(w['text'] for w in ws)}\n\n")
    low = [t for t in tokens if t["conf"] < 0.2]
    print(f"{len(tokens)} tokens aligned, {len(low)} low-confidence:", [(t["text"], t["s"]) for t in low][:30])


if __name__ == "__main__":
    main(*sys.argv[1:4])
