"""Build an old->new time map from two forced alignments of the same script.

Usage: python3 remap_timeline.py <old_words.json> <new_words.json> <old_end> <out_remap.json>
Every word present in both alignments contributes anchors (start->start, end->end); times in
between are interpolated, so timeline.js literals written for the old edit land on the same words.
"""
import json, sys
from difflib import SequenceMatcher


def main(old, new, old_end, out):
    a = json.load(open(old))["tokens"]; b = json.load(open(new))["tokens"]
    key = lambda t: t["text"].lower().strip(".,?!")
    sm = SequenceMatcher(a=[key(t) for t in a], b=[key(t) for t in b], autojunk=False)
    pts = [(0.0, 0.0)]
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            ta, tb = a[blk.a + k], b[blk.b + k]
            pts += [(ta["s"], tb["s"]), (ta["e"], tb["e"])]
    old_end = float(old_end)
    pts.append((old_end, b[-1]["e"] + (old_end - a[-1]["e"])))
    pts = sorted(set(pts))
    mono = [pts[0]]
    for p in pts[1:]:
        if p[0] > mono[-1][0] and p[1] >= mono[-1][1]:
            mono.append(p)
    json.dump(mono, open(out, "w"))
    print(f"{len(mono)} anchors; matched {sum(x.size for x in sm.get_matching_blocks())}/{len(a)} old tokens; end {old_end} -> {mono[-1][1]:.2f}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
