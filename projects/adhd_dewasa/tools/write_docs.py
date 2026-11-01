"""Write storyboard.md and higgsfield_credit_report.md from scenes.py, build/board.json, build/sfx_cues.json and jobs.json.

Usage: python3 write_docs.py <jobs.json> <out_dir>
"""
import json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import scenes as S  # noqa: E402

GFX_DESC = {
    "hook": "Kinetic stacked title SATU KERJA → TIBA-TIBA… (cyan, 210 px) → BENDA LAIN with glitch-shake; camera punch-in on “tiba-tiba”",
    "taghop": "Task chips pop in; a cyan arc draws from one task to the next and the abandoned task greys out",
    "checklist": "3D-tilting checklist card; red ✕ stamps on every item at “tak siap”; 0 / 5 SIAP",
    "stamp": "PEMALAS? rubber-stamp slam with punch-in, then a cyan strike-through rejects the label",
    "title3d": "“ADA KEMUNGKINAN…” kicker, then ADHD in 380 px 3D letters flipping up with cyan glow + full term subtitle",
    "kicker": "Two-tier kinetic type: cyan kicker + 168 px headline revealed word-by-word through masks",
    "counter": "Rolling counters 30 · 40 TAHUN under “DIAGNOSIS SELEPAS UMUR”",
    "bigtitle": "Giant 3D “10” swinging in on Y axis, TANDA ADHD + DALAM KALANGAN ORANG DEWASA",
    "chapter": "Chapter card: outlined number fills bottom-up, 3D swing-in, warm rule, masked title, 10-dot progress bar",
    "drift": "Serif ‘fikiran melayang…’ drifts away along a dotted path toward the window",
    "wave": "Voice waveform bars; DENGAR ✓ then FAHAM ✕ as the bars scatter and turn red",
    "notif": "Three phone notification cards drop in on “berbunyi”, “terus”, “buka”",
    "clock": "Timer races 00:01 → 30:00, SETENGAH JAM lands warm",
    "strikelist": "APPOINTMENT / BAYAR BIL / KUNCI KERETA written in and struck through on each “lupa”",
    "qmark": "Hand-drawn warm question mark draws itself, dot pops",
    "timer": "Expectation-vs-reality bar: 10 MINIT fills 17 %, then overruns to SEJAM (cyan→warm→red)",
    "shake": "LAMBAT slams in warm, KELAM KABUT jitters",
    "countdown": "DEADLINE: week-day tiles turn red one by one, clock ticks 03:00:00 down in red",
    "notmalas": "BUKAN SEMESTINYA · MALAS struck in red · ‘kesukaran memulakan’ in warm serif",
    "ripple": "Concentric tap ripples in rhythm; KAKI BERGERAK / JARI MENGETUK",
    "pulse": "Jittery ECG line draws across; GELISAH DARI DALAM trembles",
    "bubbles": "Second speech bubble cuts over the first; TUNGGU GILIRAN?",
    "arrow": "Fast arrow from cause to consequence (KEPUTUSAN → AKIBAT? / BOSAN·RUMIT → BERALIH)",
    "progress": "Three project bars stall at 20/45/60 % with live counters; TERHENTI DI TENGAH JALAN",
    "search": "Magnifier sweeps the desk; DOKUMEN PENTING? turns red on “hilang”",
    "tags": "Eleven task sticky-tags scatter-pop, dim, and ‘mula dari mana?’ resolves",
    "meter": "Attention gauge needle drops on “kesukaran”",
    "tunnel": "Tunnel-vision vignette closes in; TERLALU FOKUS",
    "icons": "Icon chips GAME / PROJEK KREATIF / HOBI, then ‘sampai terlupa makan’",
    "note": "NOTA card: Hyperfocus bukan simptom diagnostik khusus ADHD (key phrase cyan)",
    "neq": "1–2 TANDA ≠ ADHD with the ≠ spinning in",
    "timeline": "Age line 0 → 12 TAHUN with travelling marker; SEJAK KANAK-KANAK",
    "split": "LEBIH DARIPADA SATU SITUASI → screen splits RUMAH / TEMPAT KERJA (second AI still) → GANGGUAN FUNGSI",
    "venn": "Venn circles TIDUR / ANXIETY / DEPRESSION overlap onto ADHD?",
    "lower": "Lower-third card: PENILAIAN KESIHATAN MENTAL · Dr Azren · Klinik · Nilai",
    "book": "Typographic book card: “Doktor, Saya Boleh Sembuh Ke?” · terbitan White Coat",
    "twoline": "BUKAN BODOH. / BUKAN PEMALAS. with double punch-in",
    "checks": "Checklist ticks Diagnosis yang tepat ✓ Rawatan ✓ Strategi yang sesuai ✓ → BERFUNGSI DENGAN LEBIH BAIK",
    "recap": "10-sign recap grid, comment prompt, then end card DR AZREN | Spread Positivity",
}
TR_DESC = {"cold": "cold open (frame 0 is the hook)", "whip": "whip-pan with light streak", "match": "quick match-cut dissolve",
           "dissolve": "soft dissolve", "flash": "white light flash", "push": "vertical push", "zoom": "zoom-through",
           "glitch": "RGB glitch slice (chapter signature)", "light": "warm light-leak dissolve", "split": "dissolve into split-screen"}


def ts(x):
    m, s = divmod(x, 60)
    return f"{int(m)}:{s:05.2f}"


def main(jobs_json, out):
    board = {b["id"]: b for b in json.load(open(f"{ROOT}/build/board.json"))}
    cues = json.load(open(f"{ROOT}/build/sfx_cues.json"))["cues"]
    jobs = json.load(open(jobs_json))
    byscene = defaultdict(list)
    for c in cues:
        byscene[c["scene"]].append(c["type"].replace("hf:", ""))
    L = ["# ADHD Dewasa: storyboard", "",
         "**Reel:** “10 tanda ADHD dalam kalangan orang dewasa” (Dr Azren | Spread Positivity) · Bahasa Melayu narration (ElevenLabs voice clone, untouched)",
         "**Format:** 1080×1920 · 30 fps · 241.5 s (237.8 s narration + 3.7 s end card) · 53 scenes, average 4.5 s",
         "**Look:** photoreal Malaysian documentary B-roll, navy/cyan shadows with warm tungsten highlights; League Gothic kinetic type, Montserrat captions, Playfair Display italic accents; navy #0B1A33 · cyan #6FE3EE · white · warm #FFD25A",
         "**B-roll:** every scene has its own AI-generated plate. 6 scenes are Seedance 2.0 Mini image-to-video clips (marked 🎬); the rest are Z Image stills animated locally (camera move, parallax light motes, punch-ins) — disclosed per the brief.",
         "", "Times are the cut points on the master timeline. Every graphic is keyed to the aligned time of the word it illustrates.", ""]
    sec = None
    names = {"s01": "HOOK", "s07": "INTRO", "s11": "TANDA 1", "s14": "TANDA 2", "s17": "TANDA 3", "s20": "TANDA 4", "s23": "TANDA 5",
             "s26": "TANDA 6", "s29": "TANDA 7", "s32": "TANDA 8", "s35": "TANDA 9", "s38": "TANDA 10", "s43": "BUKAN DIAGNOSIS SENDIRI",
             "s48": "PENILAIAN & CTA", "s51": "PENUTUP"}
    for sc in S.SCENES:
        if sc["p"] is None:
            continue
        sid = sc["id"]
        if sid in names:
            L += ["", f"## {names[sid]}", ""]
        b = board[sid]
        kind = "🎬 Seedance 2.0 Mini " + sc.get("res", "480p") + " clip" if sc["kind"] == "vid" else ("re-used s52 plate" if sc["kind"] == "reuse" else "Z Image still → local camera move")
        gx = sc.get("gfx")
        L.append(f"### {sid.upper()} · {ts(b['t0'])}–{ts(b['t1'])} ({b['t1']-b['t0']:.1f} s)")
        L.append(f"- **Narration:** “{b['said']}”")
        L.append(f"- **Visual:** {sc['prompt']}" + (f"  \n  *Motion prompt:* {sc['motion']}" if sc.get("motion") else ""))
        if sid == "s45":
            L.append(f"  *Second plate (split screen):* {next(x for x in S.SCENES if x['id']=='s45b')['prompt']}")
        L.append(f"- **Source:** {kind} · camera: {sc['cam']}")
        L.append(f"- **Motion graphics:** {GFX_DESC.get(gx['t'], gx['t']) if gx else 'none (breathing room for the voice)'}")
        L.append(f"- **Transition in:** {TR_DESC.get(sc.get('tr') or 'cold')}")
        L.append(f"- **Sound:** {', '.join(dict.fromkeys(byscene[sid])) or 'ambience only'}")
        L.append("")
    L += ["## Persistent layers", "",
          "- Word-by-word Malay captions (Montserrat 800, 56–66 px, keywords warm yellow), bottom of the TikTok safe band (y ≤ 1330 px), never over faces' eye-lines.",
          "- Sign counter chip (e.g. `03 /10 SELALU TERLUPA`) during the ten signs, top-left under the status bar.",
          "- Film grain (stepped deterministic noise, 7.5 %) and a soft vignette over everything.",
          "- Score: original procedural instrumental (D minor → F major arc), ducked under the voice; scene ambiences; ~200 placed SFX."]
    open(f"{out}/storyboard.md", "w").write("\n".join(L) + "\n")

    # ---------------- credit report
    rows = [  # chronological, from Higgsfield transactions
        ("test", "s01 keyframe (also the hook's start frame)", "Z Image", "1152×2048 still", "-", 0.15),
        ("test", "s01 look test (discarded: composition came out rotated)", "Soul Cinematic 1.5k", "960×1696 still", "-", 0.12),
    ]
    order = [s["id"] for s in S.SCENES if s["id"] not in ("s01", "s52", "s53")]
    rows.append(("keyframes", "s02–s13 keyframes (batch 1, 12 stills)", "Z Image", "1152×2048", "-", 12 * 0.15))
    rows.append(("video", "s01 hook clip", "Seedance 2.0 Mini (i2v)", "720p", "4 s", 4))
    rows.append(("keyframes", "s14–s25 keyframes (batch 2, 12 stills)", "Z Image", "1152×2048", "-", 12 * 0.15))
    rows.append(("keyframes", "s26–s37 keyframes (batch 3, 12 stills)", "Z Image", "1152×2048", "-", 12 * 0.15))
    rows.append(("keyframes", "s38–s48 + s45b keyframes (batch 4, 12 stills)", "Z Image", "1152×2048", "-", 12 * 0.15))
    rows.append(("keyframes", "s49–s51 keyframes (batch 5, 3 stills)", "Z Image", "1152×2048", "-", 3 * 0.15))
    rows += [("video", "s16 doom-scrolling clip", "Seedance 2.0 Mini (i2v)", "480p", "4 s", 2),
             ("video", "s27 finger-drumming clip", "Seedance 2.0 Mini (i2v)", "480p", "4 s", 2),
             ("video", "s22 rushing-out clip", "Seedance 2.0 Mini (i2v)", "480p", "4 s", 2),
             ("video", "s40 hyperfocus dolly clip", "Seedance 2.0 Mini (i2v)", "480p", "4 s", 2),
             ("keyframes", "s52 payoff keyframe (same man as the hook, reference image)", "Kling O1 Image", "768×1360", "-", 0.5),
             ("video", "s52 payoff clip", "Seedance 2.0 Mini (i2v)", "480p", "6 s", 3)]
    C = ["# Higgsfield credit report", "",
         "**Cap:** 30 credits · **Spent:** 23.42 credits · **Unused reserve:** 6.58 credits · **Regenerations:** 0 · **Upscales on Higgsfield:** 0", "",
         "Every price was preflighted with `get_cost` before submitting, and every charge below was confirmed against the account's Higgsfield transaction log "
         "(`transactions`), which lists 52 × Z Image (0.15), 1 × Soul Cinematic (0.12), 1 × Kling O1 Image (0.5) and Seedance 2.0 Mini charges of 4 + 2 + 2 + 2 + 2 + 3 for this session.", "",
         "## Prices checked (actual, 1 Nov 2026)", "",
         "| Model | Setting | Quoted cost |", "|---|---|---|",
         "| Seedance 1.5 Pro | 480p · 4 s | 2.4 |", "| Seedance 1.5 Pro | 720p · 4 s | 4.8 |",
         "| **Seedance 2.0 Mini** | **480p · 4 s / 6 s** | **2 / 3** (0.5 per second) |", "| **Seedance 2.0 Mini** | **720p · 4 s** | **4** (1 per second) |",
         "| Wan 3.0 / Grok Video 1.5 Lite | 480p | 5 |", "| Hailuo (MiniMax) default | – | 6 |", "| Kling 2.6 | default | 10 |", "| Veo 3.1 Lite | default | 12 |",
         "| **Z Image** | 9:16 still | **0.15** |", "| Soul Cinematic | 1.5k still | 0.12 (displayed as 1) |", "| Kling O1 Image | 1k still + reference | 0.5 |",
         "| Nano Banana / Seedream 4.5 / FLUX.2 | still | 1 |", "",
         "Seedance 2.0 Mini was cheaper per second than the Seedance 1.5 the brief listed first, and is the newer model, so it was used for all video. "
         "The brief's example prices (1 credit at 480p, 3 at 720p) were lower than the real prices, so the plan was rebuilt around them.", "",
         "## Ledger (chronological)", "",
         "| # | Item | Model | Resolution | Duration | Credits | Cumulative | Remaining of 30 |", "|---|---|---|---|---|---|---|---|"]
    cum = 0.0
    for k, (_, item, model, res, dur, c) in enumerate(rows, 1):
        cum += c
        C.append(f"| {k} | {item} | {model} | {res} | {dur} | {c:.2f} | {cum:.2f} | {30-cum:.2f} |")
    C += ["", f"**Total: {cum:.2f} credits.** Before each submission the rule `cumulative + next cost ≤ 30` was checked; it was never close to binding.", "",
          "## Strategy", "",
          "- 3:58 of narration needed ~53 visual beats. At 0.5 credits per video-second, generating video for every scene would have cost about 120 credits, so the hybrid route was used:",
          "  - every scene gets its own photoreal AI keyframe (Z Image, 0.15 each, 1152×2048, above delivery resolution);",
          "  - 6 key beats are real AI video, image-to-video from those keyframes, so the style matches: the hook (720p), doom-scrolling, rushing out late, fidgeting, hyperfocus, and the hopeful payoff (same man as the hook, kept consistent with a Kling O1 reference image);",
          "  - the other 47 plates are animated locally (camera moves, parallax motes, punch-ins, transitions) in HyperFrames: the disclosed last-resort substitution.",
          "- Two video submissions were bounced by Higgsfield with a preset recommendation; nothing was charged, and they were resubmitted once with the preset declined.",
          "- No subtitles, SFX, music, transitions or graphics were generated on Higgsfield.", "",
          "## Job IDs", "", "| Asset | Model | Job ID |", "|---|---|---|"]
    for k in sorted(jobs):
        C.append(f"| {k} | {jobs[k]['model']} | `{jobs[k]['job_id']}` |")
    C.append("| (discarded) Soul Cinematic look test | soul_cinematic | `d6a4b880-65a9-407b-ae2b-2549113419db` |")
    open(f"{out}/higgsfield_credit_report.md", "w").write("\n".join(C) + "\n")
    print("docs written", cum)


if __name__ == "__main__":
    main(*sys.argv[1:3])
