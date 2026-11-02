"""Generate the HyperFrames project (index.html + one sub-composition per scene + captions + HUD)
from scenes.py and the forced-aligned words.json.

Usage: python3 build_project.py <words.json> <project_dir>
Also writes <project_dir>/../build/sfx_cues.json (for audio_build.py), storyboard.md and transcript.srt.
Every graphic is keyed to the time of the word it illustrates, so a re-alignment keeps everything in sync.
"""
import json, os, re, sys, random, html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import scenes as S  # noqa: E402

W, H, FPS = 1080, 1920, 30
END = 241.5                      # 237.8 s narration + end card hold
NAVY, DEEP, CYAN, WHITE, WARM, RED = "#0B1A33", "#061024", "#6FE3EE", "#F5F7FA", "#FFD25A", "#FF5A5F"
OV = {"cold": 0, "flash": 0.0, "glitch": 0.05, "light": 0.6, "whip": 0.15, "push": 0.25, "zoom": 0.25,
      "dissolve": 0.5, "match": 0.25, "split": 0.5}
CLIPS = {}  # sid -> media seconds (filled in main)


def esc(s):
    return html.escape(s, quote=True)


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


# ------------------------------------------------------------------ context per scene
class Ctx:
    def __init__(self, sc, t0, t1, host0, words, cues):
        self.sc, self.sid, self.t0, self.t1, self.h0 = sc, sc["id"], t0, t1, host0
        self.words, self.cues = words, cues
        self.html, self.css, self.js = [], [], []
        self.n = 0

    def id(self, k):
        self.n += 1
        return f"{self.sid}-{k}{self.n}"

    def L(self, t):                       # absolute -> local (host) time
        return round(t - self.h0, 3)

    def w(self, word, nth=0, after=None):
        """absolute start of the nth token starting with `word` inside this scene (falls back to scene start)."""
        a = self.t0 - 0.3 if after is None else after
        k = 0
        for t in self.words:
            if t["s"] >= a and t["s"] < self.t1 + 0.2 and norm(t["text"]).startswith(norm(word)):
                if k == nth:
                    return t["s"]
                k += 1
        print(f"  ! {self.sid}: word '{word}' not found, using scene start", file=sys.stderr)
        return self.t0 + 0.3

    def we(self, word, nth=0):
        s = self.w(word, nth)
        return next(t["e"] for t in self.words if t["s"] == s)

    def cue(self, typ, t, gain=1.0, **kw):
        self.cues.append(dict(type=typ, t=round(t, 3), gain=gain, scene=self.sid, **kw))


# ------------------------------------------------------------------ shared CSS
BASE_CSS = f"""
#root{{position:absolute;inset:0;overflow:hidden;background:{DEEP};font-family:'Montserrat',sans-serif;color:{WHITE}}}
.sc{{position:absolute;inset:0;overflow:hidden}}
.cam,.punch{{position:absolute;inset:0}}
.plate{{position:absolute;left:-27px;top:-48px;width:1134px;height:2016px;object-fit:cover}}
.vid{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
.shade-t{{position:absolute;left:0;top:0;width:1080px;height:560px;background:linear-gradient(180deg,rgba(6,16,36,.62),rgba(6,16,36,0))}}
.shade-b{{position:absolute;left:0;top:980px;width:1080px;height:940px;background:linear-gradient(180deg,rgba(6,16,36,0),rgba(6,16,36,.55) 35%,rgba(6,16,36,.82))}}
.mote{{position:absolute;border-radius:50%;background:radial-gradient(circle,rgba(255,236,200,.85),rgba(255,236,200,0) 70%)}}
.g{{position:absolute;left:90px;width:900px}}
.kt{{font-family:'League Gothic','Oswald',sans-serif;text-transform:uppercase;line-height:.92;letter-spacing:.01em;color:{WHITE};text-shadow:0 6px 30px rgba(0,0,0,.55)}}
.kick{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:34px;letter-spacing:.32em;text-transform:uppercase;color:{CYAN}}}
.serif{{font-family:'Playfair Display',serif;font-style:italic}}
.chip{{display:inline-block;padding:14px 26px;border-radius:999px;background:rgba(11,26,51,.78);border:2px solid rgba(111,227,238,.7);font-weight:800;font-size:34px;letter-spacing:.06em;color:{WHITE};box-shadow:0 10px 30px rgba(0,0,0,.35)}}
.card{{background:rgba(8,20,42,.82);border:1.5px solid rgba(111,227,238,.45);border-radius:28px;box-shadow:0 24px 60px rgba(0,0,0,.45)}}
.ln{{display:inline-block;overflow:hidden;vertical-align:bottom}}
.ln>span{{display:inline-block}}
.fx{{position:absolute;inset:0;pointer-events:none}}
.warm{{color:{WARM}}} .cyan{{color:{CYAN}}}
"""


# ------------------------------------------------------------------ building blocks
def letters(text, cls="ch"):
    return "".join(f'<span class="{cls}">{esc(c) if c != " " else "&nbsp;"}</span>' for c in text)


def reveal_words(ctx, sel, t, stagger=0.06, dur=0.5, y=110):
    ctx.js.append(f'tl.fromTo("{sel}",{{yPercent:{y},opacity:0}},{{yPercent:0,opacity:1,duration:{dur},ease:"power4.out",stagger:{stagger}}},{ctx.L(t)});')


def punch(ctx, t, amt=0.035):
    ctx.js.append(f'tl.fromTo("#{ctx.sid}-punch",{{scale:1}},{{scale:{1+amt},duration:0.12,ease:"power2.out",immediateRender:false,overwrite:"auto"}},{ctx.L(t)});'
                  f'tl.to("#{ctx.sid}-punch",{{scale:1,duration:0.9,ease:"power3.out",overwrite:"auto"}},{ctx.L(t)+0.12});')


def kt_line(ctx, text, top, size, cls="", align="center", t=None, color=None, key="kl"):
    i = ctx.id(key)
    words = "".join(f'<span class="ln"><span>{esc(wd)}</span></span> ' for wd in text.split())
    st = f"top:{top}px;font-size:{size}px;text-align:{align};" + (f"color:{color};" if color else "")
    ctx.html.append(f'<div id="{i}" class="g kt {cls}" style="{st}">{words}</div>')
    if t is not None:
        reveal_words(ctx, f"#{i} .ln>span", t)
    return i


def fade_out(ctx, sel, t, d=0.2):
    ctx.js.append(f'tl.to("{sel}",{{opacity:0,duration:{d},ease:"power2.in"}},{ctx.L(t)});')


# ------------------------------------------------------------------ graphics library
def g_hook(ctx, g):
    a, b, c = g["words"]
    t1, t2, t3 = ctx.w("satu"), ctx.w("tiba"), ctx.w("benda")
    i1 = kt_line(ctx, a, 300, 120, t=t1 - 0.05)
    i2 = kt_line(ctx, b, 420, 210, cls="cyan", t=t2 - 0.03)
    i3 = kt_line(ctx, c, 640, 120, t=t3 - 0.05)
    ctx.js.append(f'tl.fromTo("#{i3}",{{x:0}},{{keyframes:[{{x:-18,duration:.04}},{{x:14,duration:.04}},{{x:-6,duration:.04}},{{x:0,duration:.04}}]}},{ctx.L(t3+0.35)});')
    fade_out(ctx, f"#{i1},#{i2},#{i3}", ctx.t1 - 0.25, 0.2)
    punch(ctx, t2, 0.05)
    ctx.cue("hf:impact-bass-1", 0.02, 0.8); ctx.cue("tap", t1, 0.7); ctx.cue("hf:whoosh-short", t2 - 0.08, 0.7); ctx.cue("thock", t3, 0.6)


def g_taghop(ctx, g):
    pos = [(110, 330), (560, 520), (220, 760)]
    if ctx.sid == "s03":
        trig = [ctx.w("belum"), ctx.w("pergi"), ctx.w("kerja")]
    else:
        trig = [ctx.t0 + 0.25, ctx.w("benda")]
    ids = []
    for k, item in enumerate(g["items"]):
        x, y = pos[k]
        i = ctx.id("tag")
        ids.append(i)
        ctx.html.append(f'<div id="{i}" class="chip" style="position:absolute;left:{x}px;top:{y}px">{esc(item)}</div>')
        ctx.js.append(f'tl.fromTo("#{i}",{{scale:0.4,opacity:0}},{{scale:1,opacity:1,duration:0.45,ease:"back.out(2.2)"}},{ctx.L(trig[k])});')
        ctx.cue("pop", trig[k], 0.6)
        if k:
            px, py = pos[k - 1]
            j = ctx.id("hop")
            x0, y0, x1, y1 = px + 150, py + 80, x + 60, y
            mx, my = (x0 + x1) / 2, min(y0, y1) - 120
            ctx.html.append(f'<svg id="{j}" class="fx" viewBox="0 0 1080 1920"><path d="M{x0} {y0} Q{mx} {my} {x1} {y1}" pathLength="1" fill="none" stroke="{CYAN}" stroke-width="5" stroke-linecap="round" stroke-dasharray="1 1.2" stroke-dashoffset="1.1"/></svg>')
            ctx.js.append(f'tl.fromTo("#{j} path",{{strokeDashoffset:1.1}},{{strokeDashoffset:0,duration:0.35,ease:"power2.inOut"}},{ctx.L(trig[k]-0.3)});')
            # previous task greys out = abandoned
            ctx.js.append(f'tl.to("#{ids[k-1]}",{{opacity:0.38,duration:0.3,overwrite:"auto"}},{ctx.L(trig[k]+0.12)});')


def g_checklist(ctx, g):
    i = ctx.id("ck")
    rows = "".join(f'<div class="row"><span class="box"></span><span class="tx">{esc(it)}</span><span class="x">✕</span></div>' for it in g["items"])
    ctx.css.append(f"#{i}{{top:300px;left:200px;width:680px;padding:36px 44px}} #{i} .hd{{font-weight:900;font-size:30px;letter-spacing:.24em;color:{CYAN};margin-bottom:18px}}"
                   f"#{i} .row{{display:flex;align-items:center;gap:22px;font-size:38px;font-weight:700;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.12)}}"
                   f"#{i} .box{{width:36px;height:36px;border:3px solid rgba(255,255,255,.7);border-radius:8px}} #{i} .tx{{flex:1}}"
                   f"#{i} .x{{color:{RED};font-weight:900;font-size:40px;opacity:0}} #{i} .ft{{margin-top:22px;font-family:'League Gothic';font-size:96px;color:{WARM};opacity:0}}")
    ctx.html.append(f'<div id="{i}" class="g card"><div class="hd">SENARAI KERJA</div>{rows}<div class="ft">{esc(g["label"])}</div></div>')
    t0 = ctx.t0 + 0.15
    ctx.js.append(f'tl.fromTo("#{i}",{{y:60,opacity:0,rotationX:-25}},{{y:0,opacity:1,rotationX:0,duration:0.6,ease:"power3.out"}},{ctx.L(t0)});')
    ctx.js.append(f'tl.fromTo("#{i} .row",{{x:-30,opacity:0}},{{x:0,opacity:1,duration:0.3,stagger:0.08,ease:"power2.out"}},{ctx.L(t0+0.2)});')
    tx = ctx.w("tak")
    ctx.js.append(f'tl.fromTo("#{i} .x",{{scale:2.2,opacity:0}},{{scale:1,opacity:1,duration:0.18,stagger:0.07,ease:"power3.out"}},{ctx.L(tx)});')
    ctx.js.append(f'tl.fromTo("#{i} .ft",{{y:30,opacity:0}},{{y:0,opacity:1,duration:0.4,ease:"power3.out"}},{ctx.L(tx+0.3)});')
    for k in range(5):
        ctx.cue("tick", tx + 0.07 * k, 0.5)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_stamp(ctx, g):
    i = ctx.id("st")
    t = ctx.w("pemalas")
    ctx.css.append(f"#{i}{{top:430px;text-align:center}} #{i} .w{{display:inline-block;font-family:'League Gothic';font-size:230px;color:{WHITE};padding:0 36px;border:10px solid {WHITE};border-radius:18px;text-shadow:none;background:rgba(6,16,36,.35)}}"
                   f"#{i} .strike{{position:absolute;left:120px;top:540px;width:840px;height:22px;background:{CYAN};border-radius:12px;transform-origin:left center}}")
    ctx.html.append(f'<div id="{i}" class="g"><span class="w">{esc(g["word"])}</span></div><div id="{i}s" class="strike" style="position:absolute;left:150px;top:545px;width:780px;height:22px;background:{CYAN};border-radius:12px"></div>')
    ctx.js.append(f'tl.fromTo("#{i} .w",{{scale:2.4,rotation:-14,opacity:0}},{{scale:1,rotation:-6,opacity:1,duration:0.22,ease:"power4.in"}},{ctx.L(t-0.1)});')
    ctx.js.append(f'tl.fromTo("#{i}s",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"power3.inOut"}},{ctx.L(ctx.t1-0.55)});')
    punch(ctx, t + 0.12, 0.05)
    ctx.cue("stamp", t + 0.1, 1.0); ctx.cue("marker", ctx.t1 - 0.55, 0.6)


def g_title3d(ctx, g):
    i = ctx.id("t3")
    t = ctx.w("adhd")
    k1 = kt_line(ctx, "ADA KEMUNGKINAN…", 330, 76, t=ctx.w("ada"), color=CYAN)
    ctx.css.append(f"#{i}{{top:470px;text-align:center;perspective:900px}} #{i} .ch{{display:inline-block;font-family:'League Gothic';font-size:380px;line-height:1;color:{WHITE};text-shadow:0 0 40px rgba(111,227,238,.65),0 0 120px rgba(111,227,238,.35)}}"
                   f"#{i} .sub{{font-family:'Montserrat';font-weight:600;font-size:30px;letter-spacing:.08em;color:{CYAN};margin-top:10px}}")
    ctx.html.append(f'<div id="{i}" class="g"><div>{letters(g["word"])}</div><div class="sub">{esc(g["sub"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .ch",{{rotationX:-95,opacity:0,z:-300}},{{rotationX:0,opacity:1,z:0,duration:0.7,ease:"expo.out",stagger:0.07}},{ctx.L(t-0.12)});')
    ctx.js.append(f'tl.fromTo("#{i} .sub",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.5}},{ctx.L(t+0.4)});')
    ctx.js.append(f'tl.to("#{k1}",{{opacity:0.0,duration:0.3}},{ctx.L(t-0.2)});')
    punch(ctx, t, 0.06)
    ctx.cue("hf:riser", t - 3.2, 0.55, src_from=6.8); ctx.cue("hf:impact-bass-2", t - 0.02, 1.0); ctx.cue("shimmer", t + 0.1, 0.5)


def g_kicker(ctx, g):
    top_t = ctx.t0 + 0.15
    key = {"s07": "kanak", "s08": "dewasa", "s47": "penilaian"}.get(ctx.sid, None)
    big_t = ctx.w(key) if key else ctx.t0 + 0.6
    a = kt_line(ctx, g["top"], 330, 80, t=top_t, color=CYAN)
    b = kt_line(ctx, g["big"], 420, 168, t=big_t)
    ctx.cue("swish", top_t, 0.5); ctx.cue("thock", big_t, 0.6)
    fade_out(ctx, f"#{a},#{b}", ctx.t1 - 0.25, 0.2)


def g_counter(ctx, g):
    i = ctx.id("cn")
    t30, t40 = ctx.w("30"), ctx.w("40")
    ctx.css.append(f"#{i}{{top:300px;text-align:center}} #{i} .lb{{font-weight:800;font-size:34px;letter-spacing:.24em;color:{CYAN}}}"
                   f"#{i} .nums{{font-family:'League Gothic';font-size:300px;line-height:1;margin-top:10px}} #{i} .dot{{color:{CYAN};padding:0 26px}} #{i} .u{{font-family:'League Gothic';font-size:110px;letter-spacing:.1em}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="lb">{esc(g["label"])}</div><div class="nums"><span class="n1">0</span><span class="dot">·</span><span class="n2 warm">0</span></div><div class="u">{esc(g["unit"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .lb",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.4}},{ctx.L(ctx.w("diagnosis"))});')
    for cls, tt, val in ((".n1", t30, 30), (".n2", t40, 40)):
        ctx.js.append(f'(function(){{const o={{v:0}},el=document.querySelector("#{i} {cls}");tl.fromTo(o,{{v:0}},{{v:{val},immediateRender:false,duration:0.55,ease:"power3.out",onUpdate:()=>{{el.textContent=Math.round(o.v)}}}},{ctx.L(tt-0.15)});}})();')
        ctx.js.append(f'tl.fromTo("#{i} {cls}",{{opacity:0.25}},{{opacity:1,duration:0.2}},{ctx.L(tt-0.15)});')
        ctx.cue("tick", tt, 0.6)
    ctx.js.append(f'tl.fromTo("#{i} .nums,#{i} .u",{{opacity:0}},{{opacity:1,duration:0.3}},{ctx.L(t30-0.3)});')
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_bigtitle(ctx, g):
    i = ctx.id("bt")
    t = ctx.w("10")
    ctx.css.append(f"#{i}{{top:250px;text-align:center;perspective:1100px}} #{i} .num{{display:inline-block;font-family:'League Gothic';font-size:560px;line-height:.9;color:{WHITE};"
                   f"-webkit-text-stroke:0;text-shadow:0 0 60px rgba(111,227,238,.55),0 30px 60px rgba(0,0,0,.6)}}"
                   f"#{i} .l1{{font-family:'League Gothic';font-size:150px;line-height:.95;color:{CYAN}}} #{i} .l2{{font-weight:800;font-size:36px;letter-spacing:.16em;margin-top:14px}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="num">{g["num"]}</div><div class="l1">{esc(g["line1"])}</div><div class="l2">{esc(g["line2"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .num",{{rotationY:-80,scale:0.6,opacity:0}},{{rotationY:0,scale:1,opacity:1,duration:0.9,ease:"expo.out"}},{ctx.L(t-0.1)});')
    ctx.js.append(f'tl.fromTo("#{i} .num",{{rotationY:0}},{{rotationY:8,duration:2.5,ease:"sine.inOut",immediateRender:false}},{ctx.L(t+0.8)});')
    ctx.js.append(f'tl.fromTo("#{i} .l1",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.5,ease:"power3.out"}},{ctx.L(ctx.w("tanda"))});')
    ctx.js.append(f'tl.fromTo("#{i} .l2",{{y:20,opacity:0,scale:1.08}},{{y:0,opacity:1,scale:1,duration:0.8,ease:"power3.out"}},{ctx.L(ctx.w("dalam"))});')
    punch(ctx, t, 0.06)
    ctx.cue("hf:riser", t - 2.0, 0.45, src_from=8.0); ctx.cue("boom", t, 1.0); ctx.cue("swish", ctx.w("tanda"), 0.5)


CH_TIMES = {}


def g_chapter(ctx, g):
    i = ctx.id("ch")
    n = int(g["n"])
    t = ctx.t0 + 0.05
    tt = ctx.w({1: "susah", 2: "mudah", 3: "selalu", 4: "susah", 5: "suka", 6: "susah", 7: "impulsif", 8: "susah",
                9: "susah", 10: "hyperfocus"}[n])
    dots = "".join(f'<span class="d{" on" if k + 1 == n else (" done" if k + 1 < n else "")}"></span>' for k in range(10))
    title = g["title"]
    size = 150 if len(title) <= 16 else (124 if len(title) <= 20 else 104)
    ctx.css.append(f"#{i}{{top:250px;perspective:1000px}} #{i} .tg{{font-weight:800;font-size:32px;letter-spacing:.36em;color:{CYAN}}}"
                   f"#{i} .num{{font-family:'League Gothic';font-size:400px;line-height:.86;color:transparent;-webkit-text-stroke:4px {WHITE};position:relative;display:inline-block}}"
                   f"#{i} .fill{{position:absolute;left:0;top:0;color:{WHITE};-webkit-text-stroke:0;clip-path:inset(100% 0 0 0)}}"
                   f"#{i} .tt{{font-family:'League Gothic';font-size:{size}px;line-height:.95;margin-top:6px;text-transform:uppercase}}"
                   f"#{i} .bar{{height:8px;width:180px;background:{WARM};border-radius:6px;margin:22px 0 18px;transform-origin:left center}}"
                   f"#{i} .dots{{display:flex;gap:12px}} #{i} .dots span{{width:44px;height:8px;border-radius:5px;background:rgba(255,255,255,.25)}}"
                   f"#{i} .dots .done{{background:rgba(111,227,238,.6)}} #{i} .dots .on{{background:{WARM}}}")
    words = "".join(f'<span class="ln"><span>{esc(wd)}</span></span> ' for wd in title.split())
    ctx.html.append(f'<div id="{i}" class="g"><div class="tg">TANDA</div><div class="num">{g["n"]}<span class="fill">{g["n"]}</span></div>'
                    f'<div class="bar"></div><div class="tt">{words}</div><div class="dots">{dots}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .tg",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.5,ease:"power3.out"}},{ctx.L(t)});')
    ctx.js.append(f'tl.fromTo("#{i} .num",{{rotationY:70,opacity:0,x:-80}},{{rotationY:0,opacity:1,x:0,duration:0.7,ease:"expo.out"}},{ctx.L(t+0.05)});')
    ctx.js.append(f'tl.fromTo("#{i} .fill",{{clipPath:"inset(100% 0 0 0)"}},{{clipPath:"inset(0% 0 0 0)",duration:0.8,ease:"power2.inOut"}},{ctx.L(t+0.45)});')
    ctx.js.append(f'tl.fromTo("#{i} .bar",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{ctx.L(t+0.3)});')
    reveal_words(ctx, f"#{i} .tt .ln>span", tt - 0.08, 0.07)
    ctx.js.append(f'tl.fromTo("#{i} .dots span",{{scaleX:0}},{{scaleX:1,duration:0.25,stagger:0.03,ease:"power2.out"}},{ctx.L(t+0.4)});')
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)
    punch(ctx, tt, 0.04)
    ctx.cue("hf:impact-bass-1" if n % 2 else "hit", t + 0.03, 0.75); ctx.cue("thock", tt, 0.5)


def g_drift(ctx, g):
    i = ctx.id("dr")
    t = ctx.w("melayang")
    ctx.html.append(f'<svg id="{i}p" class="fx" viewBox="0 0 1080 1920"><path d="M300 860 C 420 600, 640 760, 760 420 S 980 260, 1020 180" pathLength="1" fill="none" stroke="{CYAN}" stroke-width="4" stroke-dasharray="0.012 0.018" stroke-linecap="round" opacity=".9"/></svg>')
    ctx.html.append(f'<div id="{i}" class="serif" style="position:absolute;left:150px;top:820px;font-size:78px;color:{WHITE};text-shadow:0 4px 24px rgba(0,0,0,.6)">{esc(g["text"])}</div>')
    ctx.css.append(f"#{i}p path{{clip-path:inset(0 100% 0 0)}}")
    ctx.js.append(f'tl.fromTo("#{i}p path",{{clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 0% 0 0)",duration:1.6,ease:"power1.inOut"}},{ctx.L(t-0.4)});')
    ctx.js.append(f'tl.fromTo("#{i}",{{x:0,y:0,opacity:0,rotation:0}},{{keyframes:[{{opacity:1,duration:0.4}},{{x:420,y:-520,rotation:-8,opacity:0,duration:2.0,ease:"sine.in"}}]}},{ctx.L(t-0.3)});')
    ctx.cue("air", t - 0.3, 0.6); ctx.cue("shimmer", t, 0.3)


def g_wave(ctx, g):
    i = ctx.id("wv")
    td, tg = ctx.w("dengar"), ctx.w("tangkap")
    bars = "".join(f'<span style="height:{20 + int(60 * abs((k * 37) % 11 - 5) / 5)}px"></span>' for k in range(26))
    ctx.css.append(f"#{i}{{top:360px;text-align:center}} #{i} .bars{{display:flex;gap:9px;justify-content:center;align-items:center;height:200px}}"
                   f"#{i} .bars span{{width:14px;border-radius:8px;background:{CYAN};display:block}}"
                   f"#{i} .r{{display:flex;justify-content:center;gap:40px;margin-top:30px}} #{i} .r div{{font-family:'League Gothic';font-size:110px}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="bars">{bars}</div><div class="r"><div class="a">DENGAR <span class="cyan">✓</span></div><div class="b">FAHAM <span style="color:{RED}">✕</span></div></div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .bars span",{{scaleY:0.2}},{{scaleY:1,duration:0.3,stagger:{{each:0.02,from:"center"}},ease:"power2.out"}},{ctx.L(ctx.t0+0.3)});')
    ctx.js.append(f'tl.to("#{i} .bars span",{{scaleY:(k)=>0.3+((k*53)%10)/9,duration:0.25,ease:"sine.inOut",stagger:0.01,repeat:9,yoyo:true}},{ctx.L(ctx.t0+0.7)});')
    ctx.js.append(f'tl.fromTo("#{i} .a",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{ctx.L(td)});')
    ctx.js.append(f'tl.fromTo("#{i} .b",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{ctx.L(tg)});')
    ctx.js.append(f'tl.to("#{i} .bars span",{{y:(k)=>((k*29)%7-3)*14,opacity:0.35,background:"{RED}",duration:0.3,stagger:0.01}},{ctx.L(tg)});')
    ctx.cue("pop", td, 0.5); ctx.cue("hf:glitch-3", tg, 0.35)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_notif(ctx, g):
    i = ctx.id("nt")
    times = [ctx.w("telefon"), ctx.w("terus"), ctx.w("buka")]
    cards = "".join(f'<div class="n"><span class="ic"></span><div><div class="ap">MESEJ · sekarang</div><div class="tx">{esc(it)}</div></div></div>' for it in g["items"])
    ctx.css.append(f"#{i}{{top:280px;left:130px;width:820px}} #{i} .n{{display:flex;gap:22px;align-items:center;background:rgba(245,247,250,.92);color:#0B1A33;border-radius:30px;padding:24px 30px;margin-bottom:18px;box-shadow:0 18px 40px rgba(0,0,0,.4)}}"
                   f"#{i} .ic{{width:70px;height:70px;border-radius:18px;background:linear-gradient(135deg,{CYAN},#2B7FFF);flex:none}} #{i} .ap{{font-size:28px;font-weight:700;opacity:.6}} #{i} .tx{{font-size:36px;font-weight:800}}")
    ctx.html.append(f'<div id="{i}" class="g">{cards}</div>')
    for k, t in enumerate(times):
        ctx.js.append(f'tl.fromTo("#{i} .n:nth-child({k+1})",{{y:-90,opacity:0,scale:0.9}},{{y:0,opacity:1,scale:1,duration:0.45,ease:"back.out(1.8)"}},{ctx.L(t)});')
        ctx.cue("hf:notification" if k == 0 else "pop", t, 0.5 if k == 0 else 0.55)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_clock(ctx, g):
    i = ctx.id("ck")
    t0, tk = ctx.t0 + 0.3, ctx.w("setengah")
    ctx.css.append(f"#{i}{{top:300px;text-align:center}} #{i} .tm{{font-family:'League Gothic';font-size:300px;line-height:1;font-variant-numeric:tabular-nums}} #{i} .lb{{font-family:'League Gothic';font-size:120px;color:{WARM}}}"
                   f"#{i} .ring{{position:absolute;left:300px;top:-10px;width:300px;height:300px}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="tm">00:01</div><div class="lb">{esc(g["label"])}</div></div>')
    dur = max(1.0, tk - t0 + 0.4)
    ctx.js.append(f'tl.fromTo("#{i} .tm",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4}},{ctx.L(t0)});')
    ctx.js.append(f'(function(){{const o={{v:1}},el=document.querySelector("#{i} .tm");tl.fromTo(o,{{v:1}},{{v:1800,duration:{dur:.2f},ease:"power2.in",onUpdate:()=>{{const s=Math.round(o.v);el.textContent=String(Math.floor(s/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0")}}}},{ctx.L(t0)});}})();')
    ctx.js.append(f'tl.fromTo("#{i} .lb",{{opacity:0,scale:1.4}},{{opacity:1,scale:1,duration:0.35,ease:"power3.out"}},{ctx.L(tk)});')
    ctx.js.append(f'tl.to("#{i} .tm",{{color:"{WARM}",duration:0.2}},{ctx.L(tk)});')
    ctx.cue("hf:typing", t0, 0.25); ctx.cue("thock", tk, 0.6)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_strikelist(ctx, g):
    i = ctx.id("sl")
    times = [ctx.w("appointment"), ctx.w("bayar"), ctx.w("letak")]
    rows = "".join(f'<div class="r"><span class="t">{esc(it)}<i class="s"></i></span></div>' for it in g["items"])
    ctx.css.append(f"#{i}{{top:330px;left:150px;width:780px}} #{i} .r{{position:relative;font-family:'League Gothic';font-size:136px;line-height:1.08;text-transform:uppercase}}"
                   f"#{i} .s{{position:absolute;left:-12px;right:-12px;top:50%;height:14px;background:{WARM};border-radius:8px;transform-origin:left center}}"
                   f"#{i} .r .t{{display:inline-block;position:relative}}")
    ctx.html.append(f'<div id="{i}" class="g">{rows}</div>')
    for k, t in enumerate(times):
        ctx.js.append(f'tl.fromTo("#{i} .r:nth-child({k+1}) .t",{{x:-60,opacity:0}},{{x:0,opacity:1,duration:0.35,ease:"power3.out"}},{ctx.L(t-0.25)});')
        ctx.js.append(f'tl.fromTo("#{i} .r:nth-child({k+1}) .s",{{scaleX:0}},{{scaleX:1,duration:0.3,ease:"power2.inOut"}},{ctx.L(t+0.35)});')
        ctx.js.append(f'tl.to("#{i} .r:nth-child({k+1}) .t",{{opacity:0.55,duration:0.3}},{ctx.L(t+0.5)});')
        ctx.cue("marker", t + 0.35, 0.55)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_qmark(ctx, g):
    i = ctx.id("qm")
    t = ctx.w("lupa")
    ctx.html.append(f'<svg id="{i}" class="fx" viewBox="0 0 1080 1920"><path d="M440 420 C440 300 640 290 650 410 C660 520 540 530 540 640 L540 700" pathLength="1" fill="none" stroke="{WARM}" stroke-width="34" stroke-linecap="round" stroke-dasharray="1 1.2" stroke-dashoffset="1.1"/><circle cx="540" cy="800" r="26" fill="{WARM}"/></svg>')
    ctx.js.append(f'tl.fromTo("#{i} path",{{strokeDashoffset:1.1}},{{strokeDashoffset:0,duration:0.7,ease:"power2.inOut"}},{ctx.L(t-0.4)});')
    ctx.js.append(f'tl.fromTo("#{i} circle",{{scale:0,transformOrigin:"540px 800px"}},{{scale:1,duration:0.35,ease:"back.out(3)"}},{ctx.L(t+0.25)});')
    ctx.js.append(f'tl.fromTo("#{i}",{{rotation:0,transformOrigin:"540px 600px"}},{{rotation:6,duration:1.2,ease:"sine.inOut",yoyo:true,repeat:1}},{ctx.L(t+0.3)});')
    ctx.cue("scribble", t - 0.4, 0.5, dur=0.6); ctx.cue("pop", t + 0.25, 0.5)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_timer(ctx, g):
    i = ctx.id("tb")
    ta, tb = ctx.w("10"), ctx.w("sejam")
    ctx.css.append(f"#{i}{{top:360px}} #{i} .lbl{{display:flex;justify-content:space-between;font-family:'League Gothic';font-size:110px}}"
                   f"#{i} .track{{position:relative;height:56px;border-radius:30px;background:rgba(255,255,255,.14);margin-top:20px;overflow:hidden}}"
                   f"#{i} .a{{position:absolute;left:0;top:0;bottom:0;width:100%;background:{CYAN};transform-origin:left center;border-radius:30px}}"
                   f"#{i} .b{{position:absolute;left:0;top:0;bottom:0;width:100%;background:linear-gradient(90deg,{CYAN},{WARM} 40%,{RED});transform-origin:left center;border-radius:30px}}"
                   f"#{i} .ft{{font-weight:800;font-size:34px;letter-spacing:.2em;margin-top:22px;color:{CYAN}}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="lbl"><span class="la">{esc(g["a"])}</span><span class="lb2 warm">{esc(g["b"])}</span></div>'
                    f'<div class="track"><div class="b"></div><div class="a"></div></div><div class="ft">JANGKAAN VS REALITI</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .la,#{i} .track,#{i} .ft",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.4,stagger:0.08}},{ctx.L(ta-0.3)});')
    ctx.js.append(f'tl.fromTo("#{i} .a",{{scaleX:0}},{{scaleX:0.17,duration:0.6,ease:"power3.out"}},{ctx.L(ta)});')
    ctx.js.append(f'tl.fromTo("#{i} .b",{{scaleX:0}},{{scaleX:1,duration:1.0,ease:"power2.inOut"}},{ctx.L(tb-0.5)});')
    ctx.js.append(f'tl.fromTo("#{i} .lb2",{{opacity:0,scale:1.5}},{{opacity:1,scale:1,duration:0.35,ease:"power3.out"}},{ctx.L(tb)});')
    ctx.cue("tick", ta, 0.5); ctx.cue("swish", tb - 0.5, 0.5); ctx.cue("thock", tb, 0.6)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_shake(ctx, g):
    ta, tb = ctx.w("lambat"), ctx.w("kelam")
    a = kt_line(ctx, g["words"][0], 330, 230, t=ta - 0.05, color=WARM)
    b = kt_line(ctx, g["words"][1], 560, 150, t=tb - 0.05)
    jit = ",".join(f'{{x:{dx},y:{dy},duration:.05}}' for dx, dy in ((-14, 6), (12, -8), (-8, 10), (10, -4), (-4, 4), (0, 0)))
    ctx.js.append(f'tl.fromTo("#{b}",{{x:0,y:0}},{{keyframes:[{jit}]}},{ctx.L(tb+0.25)});')
    punch(ctx, ta, 0.04)
    ctx.cue("thud", ta, 0.7); ctx.cue("hf:glitch-3", tb + 0.2, 0.3)


def g_countdown(ctx, g):
    i = ctx.id("cd")
    t0, td = ctx.w("kerja"), ctx.w("deadline")
    ctx.css.append(f"#{i}{{top:300px;text-align:center}} #{i} .lb{{font-weight:900;font-size:40px;letter-spacing:.4em;color:{RED}}}"
                   f"#{i} .big{{font-family:'League Gothic';font-size:250px;line-height:1;font-variant-numeric:tabular-nums}} #{i} .cal{{display:flex;justify-content:center;gap:10px;margin-top:12px}}"
                   f"#{i} .cal span{{width:80px;height:80px;border-radius:14px;background:rgba(255,255,255,.12);font-weight:800;font-size:30px;line-height:80px}}")
    days = "".join(f'<span>{d}</span>' for d in ("I", "S", "R", "K", "J", "S", "A"))
    ctx.html.append(f'<div id="{i}" class="g"><div class="lb">{esc(g["label"])}</div><div class="big">{esc(g["a"])}</div><div class="cal">{days}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .lb,#{i} .big",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.4,stagger:0.08}},{ctx.L(t0)});')
    ctx.js.append(f'tl.fromTo("#{i} .cal span",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.25,stagger:0.07}},{ctx.L(t0+0.2)});')
    ctx.js.append(f'tl.to("#{i} .cal span",{{background:"rgba(255,90,95,.75)",duration:0.12,stagger:0.12}},{ctx.L(td-0.9)});')
    ctx.js.append(f'(function(){{const o={{v:10800}},el=document.querySelector("#{i} .big");tl.fromTo(o,{{v:10800}},{{v:10790,duration:{max(0.5, ctx.t1-td-0.4):.2f},ease:"none",onUpdate:()=>{{const s=Math.round(o.v);el.textContent="0"+Math.floor(s/3600)+":"+String(Math.floor(s%3600/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0")}}}},{ctx.L(td)});}})();')
    ctx.js.append(f'tl.to("#{i} .big",{{color:"{RED}",duration:0.2}},{ctx.L(td)});')
    punch(ctx, td, 0.04)
    ctx.cue("hf:typing", ctx.t0 + 0.4, 0.35); ctx.cue("hit", td, 0.6)
    for k in range(7):
        ctx.cue("tick", td - 0.9 + 0.12 * k, 0.35)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_notmalas(ctx, g):
    i = ctx.id("nm")
    tm, tk = ctx.w("malas"), ctx.w("kesukaran")
    ctx.css.append(f"#{i}{{top:340px;text-align:center}} #{i} .bk{{font-weight:800;font-size:38px;letter-spacing:.3em;color:{CYAN}}}"
                   f"#{i} .m{{position:relative;display:inline-block;font-family:'League Gothic';font-size:250px;line-height:1}} #{i} .m i{{position:absolute;left:-20px;right:-20px;top:50%;height:18px;background:{RED};border-radius:10px;transform-origin:left center}}"
                   f"#{i} .k{{font-family:'Playfair Display';font-style:italic;font-size:92px;color:{WARM};margin-top:10px}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="bk">BUKAN SEMESTINYA</div><div class="m">{esc(g["a"])}<i></i></div><div class="k">{esc(g["b"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .bk",{{opacity:0}},{{opacity:1,duration:0.4}},{ctx.L(ctx.t0+0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .m",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,duration:0.3,ease:"power3.out"}},{ctx.L(tm-0.1)});')
    ctx.js.append(f'tl.fromTo("#{i} .m i",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"power2.inOut"}},{ctx.L(tm+0.4)});')
    ctx.js.append(f'tl.to("#{i} .m",{{opacity:0.45,duration:0.3}},{ctx.L(tm+0.8)});')
    ctx.js.append(f'tl.fromTo("#{i} .k",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{ctx.L(tk)});')
    ctx.cue("marker", tm + 0.4, 0.6); ctx.cue("shimmer", tk, 0.35)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_ripple(ctx, g):
    i = ctx.id("rp")
    tk, tj = ctx.w("kaki"), ctx.w("mengetuk")
    rings = "".join(f'<span class="r" style="left:{x}px;top:{y}px"></span>' for x, y in ((520, 980), (520, 980), (520, 980)))
    ctx.css.append(f"#{i} .r{{position:absolute;width:160px;height:160px;margin:-80px 0 0 -80px;border-radius:50%;border:5px solid {CYAN}}}"
                   f"#{i} .tx{{position:absolute;left:90px;width:900px;text-align:center;font-family:'League Gothic';font-size:120px;line-height:1}}")
    ctx.html.append(f'<div id="{i}" class="fx">{rings}<div class="tx a" style="top:330px">KAKI BERGERAK</div><div class="tx b warm" style="top:460px">JARI MENGETUK</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .r",{{scale:0.2,opacity:0.9}},{{scale:2.6,opacity:0,duration:0.55,ease:"power2.out",stagger:{{each:0.18,repeat:4}}}},{ctx.L(tj-0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .a",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{ctx.L(tk)});')
    ctx.js.append(f'tl.fromTo("#{i} .b",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{ctx.L(tj)});')
    for k in range(6):
        ctx.cue("tap", tj - 0.2 + 0.18 * k, 0.5)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_pulse(ctx, g):
    i = ctx.id("pl")
    t = ctx.w("gelisah")
    pts = []
    for k in range(0, 1081, 20):
        amp = 0 if k < 200 or k > 880 else (70 if k % 120 == 0 else (-40 if k % 60 == 0 else 8))
        pts.append(f"{k} {300 + amp}")
    ctx.html.append(f'<svg id="{i}" class="fx" viewBox="0 0 1080 1920"><polyline points="{" ".join(pts)}" pathLength="1" fill="none" stroke="{CYAN}" stroke-width="5" stroke-dasharray="1 1.2" stroke-dashoffset="1.1" stroke-linejoin="round"/></svg>')
    k = kt_line(ctx, g["text"], 420, 150, t=t - 0.05)
    ctx.js.append(f'tl.fromTo("#{i} polyline",{{strokeDashoffset:1.1}},{{strokeDashoffset:0,duration:1.2,ease:"none"}},{ctx.L(ctx.t0+0.2)});')
    jit = ",".join(f'{{x:{dx},duration:.04}}' for dx in (-6, 5, -4, 3, -2, 0))
    ctx.js.append(f'tl.fromTo("#{k}",{{x:0}},{{keyframes:[{jit}]}},{ctx.L(t+0.5)});')
    ctx.cue("heartbeat", ctx.t0 + 0.1, 0.55)
    fade_out(ctx, f"#{i},#{k}", ctx.t1 - 0.12)


def g_bubbles(ctx, g):
    i = ctx.id("bb")
    ta, tb, tg = ctx.w("bercakap"), ctx.w("sebelum"), ctx.w("giliran")
    ctx.css.append(f"#{i} .b{{position:absolute;padding:30px 44px;border-radius:44px;font-weight:800;font-size:46px}}"
                   f"#{i} .b1{{left:120px;top:330px;background:rgba(245,247,250,.92);color:{NAVY};border-bottom-left-radius:8px}}"
                   f"#{i} .b2{{left:380px;top:420px;background:{WARM};color:{NAVY};border-bottom-right-radius:8px}}"
                   f"#{i} .lb{{position:absolute;left:90px;width:900px;top:640px;text-align:center;font-family:'League Gothic';font-size:120px}}")
    ctx.html.append(f'<div id="{i}" class="fx"><div class="b b1">Saya rasa kita patut…</div><div class="b b2">Haa, betul! Lepas tu—</div><div class="lb">TUNGGU GILIRAN?</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .b1",{{scale:0.5,opacity:0,transformOrigin:"0% 100%"}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(2)"}},{ctx.L(ta)});')
    ctx.js.append(f'tl.fromTo("#{i} .b2",{{scale:0.5,opacity:0,x:120,transformOrigin:"100% 100%"}},{{scale:1,opacity:1,x:0,duration:0.35,ease:"back.out(2.5)"}},{ctx.L(tb)});')
    ctx.js.append(f'tl.to("#{i} .b1",{{x:-40,opacity:0.5,duration:0.3}},{ctx.L(tb+0.05)});')
    ctx.js.append(f'tl.fromTo("#{i} .lb",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{ctx.L(tg)});')
    ctx.cue("pop", ta, 0.5); ctx.cue("hf:pop", tb, 0.6); ctx.cue("thock", tg, 0.5)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_arrow(ctx, g):
    i = ctx.id("ar")
    if ctx.sid == "s31":
        ta, tb = ctx.w("keputusan"), ctx.w("akibatnya")
    else:
        ta, tb = ctx.w("membosankan"), ctx.w("beralih")
    ctx.css.append(f"#{i}{{top:330px;text-align:center}} #{i} .a{{font-family:'League Gothic';font-size:130px;line-height:1}} #{i} .b{{font-family:'League Gothic';font-size:170px;line-height:1;color:{WARM}}}"
                   f"#{i} svg{{display:block;margin:10px auto;width:120px;height:170px}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="a">{esc(g["a"])}</div><svg viewBox="0 0 120 170"><path d="M60 5 L60 150 M20 110 L60 155 L100 110" pathLength="1" fill="none" stroke="{CYAN}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 1.2" stroke-dashoffset="1.1"/></svg><div class="b">{esc(g["b"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .a",{{opacity:0,y:-30}},{{opacity:1,y:0,duration:0.35,ease:"power3.out"}},{ctx.L(ta-0.1)});')
    ctx.js.append(f'tl.fromTo("#{i} path",{{strokeDashoffset:1.1}},{{strokeDashoffset:0,duration:0.25,ease:"power4.in"}},{ctx.L(ta+0.35)});')
    ctx.js.append(f'tl.fromTo("#{i} .b",{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:0.3,ease:"power4.out"}},{ctx.L(tb-0.05)});')
    ctx.cue("hf:whoosh-short", ta + 0.3, 0.55); ctx.cue("thock", tb, 0.6)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_progress(ctx, g):
    i = ctx.id("pg")
    t, ts = ctx.w("dimulakan"), ctx.w("sedikit")
    rows = "".join(f'<div class="r"><div class="lb"><span>{esc(n)}</span><span class="pc">0%</span></div><div class="tr"><div class="f" data-v="{v}"></div></div></div>' for n, v in g["items"])
    ctx.css.append(f"#{i}{{top:320px;left:150px;width:780px;padding:40px}} #{i} .r{{margin-bottom:26px}} #{i} .lb{{display:flex;justify-content:space-between;font-weight:800;font-size:38px;margin-bottom:12px}}"
                   f"#{i} .tr{{height:26px;border-radius:14px;background:rgba(255,255,255,.14);overflow:hidden}} #{i} .f{{height:100%;width:100%;background:{CYAN};border-radius:14px;transform-origin:left center}}"
                   f"#{i} .pc{{color:{WARM}}} #{i} .st{{font-family:'League Gothic';font-size:96px;text-align:center;color:{WARM}}}")
    ctx.html.append(f'<div id="{i}" class="g card">{rows}<div class="st">TERHENTI DI TENGAH JALAN</div></div>')
    ctx.js.append(f'tl.fromTo("#{i}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{ctx.L(ctx.t0+0.2)});')
    for k, (_, v) in enumerate(g["items"]):
        ctx.js.append(f'tl.fromTo("#{i} .r:nth-child({k+1}) .f",{{scaleX:0}},{{scaleX:{v/100},duration:0.9,ease:"power2.out"}},{ctx.L(t+0.15*k)});')
        ctx.js.append(f'(function(){{const o={{v:0}},el=document.querySelector("#{i} .r:nth-child({k+1}) .pc");tl.fromTo(o,{{v:0}},{{v:{v},immediateRender:false,duration:0.9,ease:"power2.out",onUpdate:()=>{{el.textContent=Math.round(o.v)+"%"}}}},{ctx.L(t+0.15*k)});}})();')
    ctx.js.append(f'tl.fromTo("#{i} .st",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,duration:0.35,ease:"power3.out"}},{ctx.L(ts)});')
    ctx.cue("tick", t, 0.5); ctx.cue("tick", t + 0.15, 0.45); ctx.cue("tick", t + 0.3, 0.45); ctx.cue("thud", ts, 0.5)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_search(ctx, g):
    i = ctx.id("se")
    t, th = ctx.w("dokumen"), ctx.w("hilang")
    ctx.html.append(f'<svg id="{i}m" class="fx" viewBox="0 0 1080 1920"><g><circle cx="0" cy="0" r="110" fill="rgba(111,227,238,.08)" stroke="{CYAN}" stroke-width="10"/><line x1="78" y1="78" x2="170" y2="170" stroke="{CYAN}" stroke-width="22" stroke-linecap="round"/></g></svg>')
    k = kt_line(ctx, g["text"], 330, 130, t=t)
    ctx.js.append(f'tl.fromTo("#{i}m g",{{x:300,y:1000,opacity:0}},{{keyframes:[{{opacity:1,duration:0.2}},{{x:700,y:880,duration:0.7,ease:"sine.inOut"}},{{x:380,y:760,duration:0.7,ease:"sine.inOut"}},{{x:640,y:960,duration:0.7,ease:"sine.inOut"}}]}},{ctx.L(t-0.2)});')
    ctx.js.append(f'tl.to("#{k}",{{color:"{RED}",duration:0.2}},{ctx.L(th)});')
    ctx.cue("paper", ctx.t0 + 0.2, 0.6); ctx.cue("hf:click-soft", th, 0.5)
    fade_out(ctx, f"#{i}m,#{k}", ctx.t1 - 0.12)


def g_tags(ctx, g):
    i = ctx.id("tg")
    t, tm = ctx.w("banyak"), ctx.w("mula")
    rnd = random.Random(9)
    items = ["Emel", "Bil", "Laporan", "Mesyuarat", "Cuci kereta", "Tempah klinik", "Slide", "Bayar kad", "Jawab mesej", "Hantar dokumen", "Beli barang"]
    tags = "".join(f'<span class="t" style="left:{rnd.randint(70, 760)}px;top:{rnd.randint(260, 900)}px;rotate:{rnd.randint(-12, 12)}deg">{esc(x)}</span>' for x in items)
    ctx.css.append(f"#{i} .t{{position:absolute;padding:12px 22px;border-radius:12px;background:rgba(255,210,90,.92);color:{NAVY};font-weight:800;font-size:30px;box-shadow:0 8px 20px rgba(0,0,0,.35)}}"
                   f"#{i} .q{{position:absolute;left:90px;width:900px;top:560px;text-align:center;font-family:'Playfair Display';font-style:italic;font-size:110px;text-shadow:0 6px 30px rgba(0,0,0,.8)}}")
    ctx.html.append(f'<div id="{i}" class="fx">{tags}<div class="q">{esc(g["text"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .t",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2.5)",stagger:0.11}},{ctx.L(t)});')
    ctx.js.append(f'tl.to("#{i} .t",{{opacity:0.25,duration:0.3}},{ctx.L(tm-0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .q",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ctx.L(tm-0.1)});')
    for k in range(0, 11, 2):
        ctx.cue("pop", t + 0.11 * k, 0.35)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_meter(ctx, g):
    i = ctx.id("mt")
    tk = ctx.w("kesukaran")
    ctx.html.append(f'<svg id="{i}" class="fx" viewBox="0 0 1080 1920"><path d="M290 700 A250 250 0 0 1 790 700" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="34" stroke-linecap="round"/>'
                    f'<path d="M290 700 A250 250 0 0 1 790 700" pathLength="1" fill="none" stroke="{CYAN}" stroke-width="34" stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="0.15" class="arc"/>'
                    f'<g class="nd"><line x1="540" y1="700" x2="540" y2="490" stroke="{WARM}" stroke-width="14" stroke-linecap="round"/><circle cx="540" cy="700" r="22" fill="{WARM}"/></g>'
                    f'<text x="540" y="800" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="40" letter-spacing="10" fill="{WHITE}">{esc(g["label"])}</text></svg>')
    ctx.js.append(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.4}},{ctx.L(ctx.t0+0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .nd",{{rotation:50,svgOrigin:"540 700"}},{{rotation:-62,duration:1.0,ease:"power2.inOut"}},{ctx.L(tk)});')
    ctx.js.append(f'tl.fromTo("#{i} .arc",{{strokeDashoffset:0.15}},{{strokeDashoffset:0.82,duration:1.0,ease:"power2.inOut"}},{ctx.L(tk)});')
    ctx.js.append(f'tl.to("#{i} .nd",{{rotation:-55,duration:0.25,yoyo:true,repeat:3,ease:"sine.inOut"}},{ctx.L(tk+1.0)});')
    ctx.cue("swish", tk, 0.45)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_tunnel(ctx, g):
    i = ctx.id("tu")
    t = ctx.w("terlalu")
    ctx.css.append(f"#{i}{{background:radial-gradient(ellipse 34% 26% at 50% 36%,rgba(0,0,0,0) 0%,rgba(0,0,0,0) 55%,rgba(2,6,16,.92) 100%)}}")
    ctx.html.append(f'<div id="{i}" class="fx"></div>')
    k = kt_line(ctx, g["text"], 1000, 150, t=t)
    ctx.js.append(f'tl.fromTo("#{i}",{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:2.2,ease:"power2.inOut"}},{ctx.L(ctx.t0+0.4)});')
    ctx.cue("hf:riser", t - 2.5, 0.3, src_from=7.5)


def g_icons(ctx, g):
    i = ctx.id("ic")
    times = [ctx.w("game"), ctx.w("kreatif"), ctx.w("hobi")]
    tf = ctx.w("terlupa")
    svgs = [
        f'<svg viewBox="0 0 64 64"><rect x="6" y="20" width="52" height="28" rx="14" fill="none" stroke="{CYAN}" stroke-width="5"/><path d="M20 28v12M14 34h12" stroke="{CYAN}" stroke-width="5" stroke-linecap="round"/><circle cx="44" cy="31" r="3.5" fill="{CYAN}"/><circle cx="50" cy="38" r="3.5" fill="{CYAN}"/></svg>',
        f'<svg viewBox="0 0 64 64"><path d="M32 8C16 8 6 20 6 32s10 24 22 24c4 0 6-3 4-7s0-7 5-7h8c8 0 13-5 13-12C58 18 46 8 32 8z" fill="none" stroke="{CYAN}" stroke-width="5"/><circle cx="20" cy="30" r="4" fill="{WARM}"/><circle cx="30" cy="20" r="4" fill="{CYAN}"/><circle cx="43" cy="22" r="4" fill="{RED}"/></svg>',
        f'<svg viewBox="0 0 64 64"><path d="M10 54C10 30 26 12 54 10c-2 28-20 44-44 44z" fill="none" stroke="{CYAN}" stroke-width="5"/><path d="M10 54L36 28" stroke="{CYAN}" stroke-width="5" stroke-linecap="round"/></svg>']
    chips = "".join(f'<div class="c">{s}<span>{esc(n)}</span></div>' for s, n in zip(svgs, g["items"]))
    ctx.css.append(f"#{i}{{top:300px}} #{i} .c{{display:flex;align-items:center;gap:26px;padding:22px 34px;margin:0 auto 22px;width:640px;border-radius:26px;background:rgba(8,20,42,.8);border:1.5px solid rgba(111,227,238,.5);font-weight:800;font-size:44px}}"
                   f"#{i} .c svg{{width:70px;height:70px;flex:none}} #{i} .f{{text-align:center;font-family:'Playfair Display';font-style:italic;font-size:80px;color:{WARM};margin-top:20px}}")
    ctx.html.append(f'<div id="{i}" class="g">{chips}<div class="f">{esc(g["foot"])}</div></div>')
    for k, t in enumerate(times):
        ctx.js.append(f'tl.fromTo("#{i} .c:nth-child({k+1})",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.4,ease:"power3.out"}},{ctx.L(t-0.1)});')
        ctx.cue("pop", t, 0.5)
    ctx.js.append(f'tl.fromTo("#{i} .f",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ctx.L(tf)});')
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_note(ctx, g):
    i = ctx.id("no")
    t = ctx.w("bukan")
    ctx.css.append(f"#{i}{{top:420px;left:130px;width:820px;padding:46px 50px}} #{i} .h{{display:inline-block;font-weight:900;font-size:30px;letter-spacing:.3em;color:{NAVY};background:{WARM};padding:8px 18px;border-radius:8px}}"
                   f"#{i} .t{{font-family:'Playfair Display';font-size:66px;line-height:1.18;margin-top:22px}} #{i} .t b{{color:{CYAN};font-style:italic}}")
    txt = esc(g["text"]).replace("bukan simptom diagnostik khusus", "<b>bukan simptom diagnostik khusus</b>")
    ctx.html.append(f'<div id="{i}" class="g card"><span class="h">{esc(g["head"])}</span><div class="t">{txt}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i}",{{opacity:0,y:50,rotationX:-20}},{{opacity:1,y:0,rotationX:0,duration:0.6,ease:"power3.out"}},{ctx.L(ctx.t0+0.25)});')
    ctx.js.append(f'tl.fromTo("#{i} b",{{color:"{WHITE}"}},{{color:"{CYAN}",duration:0.4}},{ctx.L(t)});')
    ctx.cue("paper", ctx.t0 + 0.25, 0.55)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_neq(ctx, g):
    i = ctx.id("nq")
    ta, tb = ctx.w("satu", after=ctx.t0 + 1.5), ctx.w("bermaksud")
    ctx.css.append(f"#{i}{{top:320px;text-align:center}} #{i} .a{{font-family:'League Gothic';font-size:170px;line-height:1}} #{i} .eq{{font-family:'League Gothic';font-size:200px;line-height:1;color:{WARM}}} #{i} .b{{font-family:'League Gothic';font-size:200px;line-height:1;color:{CYAN}}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="a">{esc(g["a"])}</div><div class="eq">≠</div><div class="b">{esc(g["b"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .a",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{ctx.L(ta)});')
    ctx.js.append(f'tl.fromTo("#{i} .eq",{{opacity:0,scale:2,rotation:-30}},{{opacity:1,scale:1,rotation:0,duration:0.4,ease:"back.out(2)"}},{ctx.L(tb)});')
    ctx.js.append(f'tl.fromTo("#{i} .b",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:"power3.out"}},{ctx.L(tb+0.35)});')
    ctx.cue("pop", ta, 0.45); ctx.cue("thud", tb, 0.7)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_timeline(ctx, g):
    i = ctx.id("tl")
    tk, t12 = ctx.w("kanak"), ctx.w("12")
    ctx.css.append(f"#{i}{{top:360px}} #{i} .lb{{font-weight:800;font-size:36px;letter-spacing:.24em;color:{CYAN};text-align:center}}"
                   f"#{i} .ax{{position:relative;height:200px;margin-top:40px}} #{i} .ln{{position:absolute;left:40px;right:40px;top:90px;height:8px;background:rgba(255,255,255,.25);border-radius:4px}}"
                   f"#{i} .fl{{position:absolute;left:40px;right:40px;top:90px;height:8px;background:{WARM};border-radius:4px;transform-origin:left center}}"
                   f"#{i} .p{{position:absolute;top:120px;font-family:'League Gothic';font-size:100px}} #{i} .p0{{left:20px}} #{i} .p1{{right:0}}"
                   f"#{i} .dt{{position:absolute;top:78px;left:28px;width:32px;height:32px;border-radius:50%;background:{WARM}}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="lb">{esc(g["label"])}</div><div class="ax"><div class="ln"></div><div class="fl"></div><div class="dt"></div><div class="p p0">{esc(g["a"])}</div><div class="p p1 warm">{esc(g["b"])}</div></div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .lb,#{i} .ln,#{i} .p0",{{opacity:0}},{{opacity:1,duration:0.4,stagger:0.1}},{ctx.L(tk-0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .fl",{{scaleX:0}},{{scaleX:1,duration:1.6,ease:"power1.inOut"}},{ctx.L(tk+0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .dt",{{x:0}},{{x:780,duration:1.6,ease:"power1.inOut"}},{ctx.L(tk+0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .p1",{{opacity:0,scale:1.4}},{{opacity:1,scale:1,duration:0.35,ease:"power3.out"}},{ctx.L(t12)});')
    ctx.cue("swish", tk + 0.2, 0.45); ctx.cue("pop", t12, 0.55)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_split(ctx, g):
    tl_, tr, tt, tg = ctx.w("lebih"), ctx.w("rumah"), ctx.w("tempat"), ctx.w("gangguan")
    i = ctx.id("sp")
    ctx.css.append(f"#{i}{{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:hidden;clip-path:inset(100% 0 0 0)}}"
                   f"#{i} img{{position:absolute;left:-27px;top:-48px;width:1134px;height:2016px;object-fit:cover}}"
                   f"#{i}d{{position:absolute;left:0;top:958px;width:1080px;height:6px;background:{CYAN};transform-origin:left center}}"
                   f".{ctx.sid}-lab{{position:absolute;left:60px;padding:10px 22px;border-radius:10px;background:rgba(6,16,36,.75);font-family:'League Gothic';font-size:84px;letter-spacing:.04em}}")
    ctx.html.append(f'<div id="{i}"><img src="assets/img/{g["img2"]}.jpg" alt=""></div><div id="{i}d"></div>'
                    f'<div class="{ctx.sid}-lab" id="{i}a" style="top:240px">{esc(g["a"])}</div><div class="{ctx.sid}-lab" id="{i}b" style="top:1000px;color:{WARM}">{esc(g["b"])}</div>')
    k = kt_line(ctx, "LEBIH DARIPADA SATU SITUASI", 300, 120, t=tl_)
    ctx.js.append(f'tl.to("#{k}",{{opacity:0,duration:0.25}},{ctx.L(tr-0.3)});')
    ctx.js.append(f'tl.fromTo("#{i}",{{clipPath:"inset(100% 0 0 0)"}},{{clipPath:"inset(50% 0 0 0)",duration:0.6,ease:"power3.inOut"}},{ctx.L(tr)});')
    ctx.js.append(f'tl.fromTo("#{ctx.sid}-cam",{{yPercent:0}},{{yPercent:-22,duration:0.6,ease:"power3.inOut",immediateRender:false}},{ctx.L(tr)});')
    ctx.js.append(f'tl.fromTo("#{i} img",{{yPercent:0}},{{yPercent:18,duration:0.6,ease:"power3.inOut"}},{ctx.L(tr)});')
    ctx.js.append(f'tl.fromTo("#{i}d",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{ctx.L(tr+0.2)});')
    ctx.js.append(f'tl.fromTo("#{i}a",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.35}},{ctx.L(tr)});')
    ctx.js.append(f'tl.fromTo("#{i}b",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.35}},{ctx.L(tt)});')
    k2 = kt_line(ctx, "GANGGUAN FUNGSI", 830, 120, t=tg, color=WARM)
    ctx.cue("hf:whoosh-short", tr, 0.6); ctx.cue("pop", tt, 0.5); ctx.cue("thud", tg, 0.55)


def g_venn(ctx, g):
    i = ctx.id("vn")
    times = [ctx.w("tidur"), ctx.w("anxiety"), ctx.w("depression")]
    th = ctx.w("hampir")
    pos = [(400, 520), (680, 520), (540, 760)]
    circles = "".join(f'<g class="c{k}"><circle cx="{x}" cy="{y}" r="200" fill="rgba(111,227,238,.16)" stroke="{CYAN}" stroke-width="5"/><text x="{x + (-60 if k == 0 else (60 if k == 1 else 0))}" y="{y + (-40 if k < 2 else 90)}" text-anchor="middle" font-family="League Gothic" font-size="70" fill="{WHITE}">{esc(n)}</text></g>' for k, ((x, y), n) in enumerate(zip(pos, g["items"])))
    ctx.html.append(f'<svg id="{i}" class="fx" viewBox="0 0 1080 1920">{circles}<g class="ctr"><circle cx="540" cy="600" r="72" fill="{WARM}"/><text x="540" y="622" text-anchor="middle" font-family="League Gothic" font-size="62" fill="{NAVY}">{esc(g["center"])}</text></g></svg>')
    for k, t in enumerate(times):
        x, y = pos[k]
        ctx.js.append(f'tl.fromTo("#{i} .c{k}",{{scale:0,opacity:0,svgOrigin:"{x} {y}"}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.7)"}},{ctx.L(t-0.1)});')
        ctx.cue("pop", t, 0.45)
    ctx.js.append(f'tl.fromTo("#{i} .ctr",{{scale:0,svgOrigin:"540 600"}},{{scale:1,duration:0.45,ease:"back.out(2.5)"}},{ctx.L(th)});')
    ctx.cue("thock", th, 0.6)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_lower(ctx, g):
    i = ctx.id("lt")
    tp, tn, tl2 = ctx.w("penilaian"), ctx.w("dr"), ctx.w("nilai", after=ctx.w("klinik"))
    ctx.css.append(f"#{i}{{top:760px;left:90px;width:840px;padding:36px 44px}} #{i} .k{{font-weight:800;font-size:28px;letter-spacing:.28em;color:{CYAN}}}"
                   f"#{i} .n{{font-family:'League Gothic';font-size:150px;line-height:1;margin-top:6px}} #{i} .u{{height:6px;width:220px;background:{WARM};border-radius:4px;transform-origin:left center;margin:10px 0 16px}}"
                   f"#{i} .p{{font-weight:700;font-size:40px}} #{i} .p span{{color:{WARM}}}")
    ctx.html.append(f'<div id="{i}" class="g card"><div class="k">{esc(g["role"]).upper()}</div><div class="n">{esc(g["name"])}</div><div class="u"></div><div class="p">Klinik · <span>Nilai</span></div></div>')
    ctx.js.append(f'tl.fromTo("#{i}",{{opacity:0,x:-80}},{{opacity:1,x:0,duration:0.55,ease:"power3.out"}},{ctx.L(tp-0.1)});')
    ctx.js.append(f'tl.fromTo("#{i} .n",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{ctx.L(tn-0.05)});')
    ctx.js.append(f'tl.fromTo("#{i} .u",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{ctx.L(tn+0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .p",{{opacity:0}},{{opacity:1,duration:0.4}},{ctx.L(tl2-0.4)});')
    ctx.cue("swish", tp - 0.1, 0.5); ctx.cue("logo", tn, 0.45)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_book(ctx, g):
    i = ctx.id("bk")
    tb, tt, tp = ctx.w("buku"), ctx.w("doktor"), ctx.w("terbitan")
    ctx.css.append(f"#{i}{{top:300px;text-align:center}} #{i} .k{{font-weight:800;font-size:30px;letter-spacing:.36em;color:{CYAN}}}"
                   f"#{i} .t{{font-family:'Playfair Display';font-style:italic;font-weight:700;font-size:100px;line-height:1.08;margin-top:16px;text-shadow:0 8px 40px rgba(0,0,0,.7)}}"
                   f"#{i} .u{{height:5px;width:160px;background:{WARM};margin:28px auto 18px;border-radius:3px;transform-origin:center}} #{i} .p{{font-weight:600;font-size:36px;letter-spacing:.06em}}")
    tw = "".join(f'<span class="ln"><span>{esc(x)}</span></span> ' for x in ("“" + g["title"] + "”").split())
    ctx.html.append(f'<div id="{i}" class="g"><div class="k">BUKU OLEH DR AZREN</div><div class="t">{tw}</div><div class="u"></div><div class="p">{esc(g["sub"])}</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .k",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{ctx.L(tb)});')
    reveal_words(ctx, f"#{i} .t .ln>span", tt - 0.1, 0.12, 0.6)
    ctx.js.append(f'tl.fromTo("#{i} .u",{{scaleX:0}},{{scaleX:1,duration:0.5}},{ctx.L(tp-0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .p",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.45}},{ctx.L(tp)});')
    ctx.cue("paper", tb, 0.5); ctx.cue("shimmer", tt, 0.35)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


def g_book3d(ctx, g):
    """Dr Azren's real book as a 3D object built from the print artwork (front, spine, back, page edges)."""
    i = ctx.id("b3")
    tm, tb, tt, tp = ctx.w("menulis"), ctx.w("buku"), ctx.w("dr", after=ctx.w("bertajuk")), ctx.w("terbitan")
    BW, BH, T = 500, 711, 51           # 125 x 177 mm cover, 13 mm spine, same proportions as the print file
    hw, hh, ht = BW / 2, BH / 2, T / 2
    ctx.css.append(
        f"#{i}k{{position:absolute;left:0;right:0;top:206px;text-align:center;font-weight:800;font-size:30px;letter-spacing:.36em;color:{CYAN}}}"
        f"#{i}s{{position:absolute;left:0;width:1080px;top:270px;height:900px;perspective:1700px;perspective-origin:50% 40%}}"
        f"#{i}sh{{position:absolute;left:250px;top:800px;width:580px;height:90px;border-radius:50%;"
        f"background:radial-gradient(ellipse at center,rgba(0,0,0,.62),rgba(0,0,0,.25) 45%,rgba(0,0,0,0) 72%)}}"
        f"#{i}{{position:absolute;left:{540-hw}px;top:40px;width:{BW}px;height:{BH}px;transform-style:preserve-3d}}"
        f"#{i} .f{{position:absolute;backface-visibility:hidden;overflow:hidden}}"
        f"#{i} .fr{{left:0;top:0;width:{BW}px;height:{BH}px;background:url('assets/book/front.jpg') center/100% 100% no-repeat;transform:translateZ({ht}px);border-radius:0 4px 4px 0}}"
        f"#{i} .bk{{left:0;top:0;width:{BW}px;height:{BH}px;background:url('assets/book/back.jpg') center/100% 100% no-repeat;transform:rotateY(180deg) translateZ({ht}px)}}"
        f"#{i} .sp{{left:{hw-ht}px;top:0;width:{T}px;height:{BH}px;background:url('assets/book/spine.jpg') center/100% 100% no-repeat;transform:rotateY(-90deg) translateZ({hw}px)}}"
        f"#{i} .pr{{left:{hw-ht+2}px;top:3px;width:{T-4}px;height:{BH-6}px;background:repeating-linear-gradient(90deg,#f5f0e6 0 2px,#d9d1c0 2px 3px);transform:rotateY(90deg) translateZ({hw-3}px)}}"
        f"#{i} .pt{{left:3px;top:{hh-ht+2}px;width:{BW-6}px;height:{T-4}px;background:repeating-linear-gradient(0deg,#f5f0e6 0 2px,#d9d1c0 2px 3px);transform:rotateX(90deg) translateZ({hh-2}px)}}"
        f"#{i} .pb{{left:3px;top:{hh-ht+2}px;width:{BW-6}px;height:{T-4}px;background:repeating-linear-gradient(0deg,#efe9dc 0 2px,#cfc6b4 2px 3px);transform:rotateX(-90deg) translateZ({hh-2}px)}}"
        f"#{i} .sd{{position:absolute;inset:0;background:linear-gradient(100deg,rgba(255,255,255,.10),rgba(255,255,255,0) 35%,rgba(0,0,0,.10) 80%,rgba(0,0,0,.22))}}"
        f"#{i} .hinge{{position:absolute;left:0;top:0;bottom:0;width:22px;background:linear-gradient(90deg,rgba(0,0,0,.28),rgba(255,255,255,.08) 55%,rgba(0,0,0,0))}}"
        f"#{i} .spd{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.30),rgba(0,0,0,.05) 50%,rgba(0,0,0,.25))}}"
        f"#{i} .gl{{position:absolute;top:-20%;left:0;width:180px;height:140%;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.55),rgba(255,255,255,0));opacity:.9}}"
        f"#{i}p{{position:absolute;left:0;right:0;top:1062px;text-align:center;font-weight:700;font-size:34px;letter-spacing:.08em;color:{WHITE};text-shadow:0 4px 18px rgba(0,0,0,.8)}}"
        f"#{i}p b{{color:{WARM};font-weight:800}}")
    ctx.html.append(
        f'<div id="{i}k">BUKU OLEH DR AZREN</div>'
        f'<div id="{i}s"><div id="{i}sh"></div><div id="{i}">'
        f'<div class="f bk"><div class="sd"></div></div>'
        f'<div class="f pr"></div><div class="f pt"></div><div class="f pb"></div>'
        f'<div class="f sp"><div class="spd"></div></div>'
        f'<div class="f fr"><div class="sd"></div><div class="hinge"></div><div class="gl"></div></div>'
        f'</div></div>'
        f'<div id="{i}p">terbitan <b>{esc(g["publisher"])}</b></div>')
    J = ctx.js.append
    # enter: rises out of depth, pages edge toward camera
    J(f'tl.fromTo("#{i}",{{y:620,z:-420,rotationY:-62,rotationX:18,rotationZ:-4,opacity:0}},{{y:0,z:0,rotationY:-30,rotationX:7,rotationZ:-1.5,opacity:1,duration:1.15,ease:"expo.out"}},{ctx.L(tm-0.15)});')
    J(f'tl.fromTo("#{i}sh",{{opacity:0,scaleX:0.4}},{{opacity:1,scaleX:1,duration:1.0,ease:"power3.out"}},{ctx.L(tm)});')
    J(f'tl.fromTo("#{i}k",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{ctx.L(tb)});')
    # turn to face the viewer while the title is spoken, light sweeps across the cover
    J(f'tl.to("#{i}",{{rotationY:-9,rotationX:4,rotationZ:0,duration:1.3,ease:"power2.inOut"}},{ctx.L(tt-0.35)});')
    J(f'tl.fromTo("#{i} .gl",{{x:-260}},{{x:{BW+120},duration:1.1,ease:"power2.inOut"}},{ctx.L(tt+0.2)});')
    J(f'tl.fromTo("#{i}p",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ctx.L(tp)});')
    # slow hero turn that reveals the spine, gentle float
    turn = max(1.0, ctx.t1 - 0.7 - (tp + 0.3))
    J(f'tl.to("#{i}",{{rotationY:28,rotationX:5,duration:{turn:.2f},ease:"sine.inOut"}},{ctx.L(tp+0.3)});')
    J(f'tl.fromTo("#{i}s",{{y:0}},{{y:-14,duration:1.6,ease:"sine.inOut",yoyo:true,repeat:{max(1, int((ctx.t1 - tm) / 1.6))}}},{ctx.L(tm+0.8)});')
    J(f'tl.fromTo("#{i} .gl",{{x:{BW+120}}},{{x:-260,duration:1.4,ease:"power2.inOut",immediateRender:false}},{ctx.L(tp+1.6)});')
    ctx.cue("hf:whoosh-cinematic", tm - 0.55, 0.45, src_from=1.6); ctx.cue("thud", tm + 0.55, 0.35)
    ctx.cue("paper", tb, 0.45); ctx.cue("shimmer", tt + 0.25, 0.4); ctx.cue("swish", tp + 0.4, 0.35)
    fade_out(ctx, f"#{i}k,#{i}p", ctx.t1 - 0.12)


def g_twoline(ctx, g):
    tb, tp = ctx.w("bodoh"), ctx.w("pemalas")
    a = kt_line(ctx, g["a"], 330, 190, t=tb - 0.08)
    b = kt_line(ctx, g["b"], 520, 190, t=tp - 0.08, color=WARM)
    punch(ctx, tb, 0.04); punch(ctx, tp, 0.04)
    ctx.cue("hit", tb, 0.7); ctx.cue("hf:impact-bass-1", tp, 0.75)
    fade_out(ctx, f"#{a},#{b}", ctx.t1 - 0.12)


def g_checks(ctx, g):
    i = ctx.id("cx")
    times = [ctx.w("diagnosis"), ctx.w("rawatan"), ctx.w("strategi")]
    tf = ctx.w("berfungsi")
    rows = "".join(f'<div class="r"><svg viewBox="0 0 60 60"><circle cx="30" cy="30" r="26" fill="none" stroke="{CYAN}" stroke-width="4"/><path d="M17 31 L27 41 L44 21" pathLength="1" fill="none" stroke="{WARM}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 1.2" stroke-dashoffset="1.1"/></svg><span>{esc(it)}</span></div>' for it in g["items"])
    ctx.css.append(f"#{i}{{top:290px;left:140px;width:800px;padding:40px 46px}} #{i} .r{{display:flex;align-items:center;gap:26px;font-weight:800;font-size:46px;margin-bottom:22px}} #{i} .r svg{{width:74px;height:74px;flex:none}}"
                   f"#{i} .f{{font-family:'League Gothic';font-size:104px;line-height:1;color:{CYAN};margin-top:12px}}")
    ctx.html.append(f'<div id="{i}" class="g card">{rows}<div class="f">BERFUNGSI DENGAN LEBIH BAIK</div></div>')
    ctx.js.append(f'tl.fromTo("#{i}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ctx.L(times[0]-0.4)});')
    ctx.js.append(f'tl.fromTo("#{i} .r",{{opacity:0.25}},{{opacity:0.25,duration:0.01}},{ctx.L(times[0]-0.4)});')
    for k, t in enumerate(times):
        ctx.js.append(f'tl.to("#{i} .r:nth-child({k+1})",{{opacity:1,duration:0.25}},{ctx.L(t)});')
        ctx.js.append(f'tl.fromTo("#{i} .r:nth-child({k+1}) path",{{strokeDashoffset:1.1}},{{strokeDashoffset:0,duration:0.35,ease:"power2.out"}},{ctx.L(t+0.05)});')
        ctx.cue("check", t + 0.05, 0.6)
    ctx.js.append(f'tl.fromTo("#{i} .f",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ctx.L(tf)});')
    ctx.cue("shimmer", tf, 0.45)
    fade_out(ctx, f"#{i}", ctx.t1 - 0.12)


SIGN_TITLES = ["Susah nak fokus", "Mudah terganggu", "Selalu terlupa", "Susah urus masa", "Suka bertangguh",
               "Susah duduk diam", "Impulsif", "Susah siapkan kerja", "Susah urus barang", "Hyperfocus"]


def g_recap(ctx, g):
    i = ctx.id("rc")
    t10, tm, tk = ctx.w("10"), ctx.w("mana"), ctx.w("komen")
    cells = "".join(f'<div class="c"><b>{k+1:02d}</b>{esc(n)}</div>' for k, n in enumerate(SIGN_TITLES))
    ctx.css.append(f"#{i}{{top:230px;left:70px;width:940px}} #{i} .h{{font-family:'League Gothic';font-size:96px;text-align:center;line-height:1;margin-bottom:22px}}"
                   f"#{i} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} #{i} .c{{display:flex;gap:16px;align-items:center;padding:18px 20px;border-radius:18px;background:rgba(8,20,42,.82);border:1.5px solid rgba(111,227,238,.4);font-weight:700;font-size:30px}}"
                   f"#{i} .c b{{font-family:'League Gothic';font-weight:400;font-size:52px;color:{WARM}}}"
                   f"#{i} .cm{{display:flex;align-items:center;justify-content:center;gap:20px;margin-top:26px;font-weight:800;font-size:40px;color:{WHITE}}}"
                   f"#{i} .cm svg{{width:70px;height:70px}}")
    ctx.html.append(f'<div id="{i}" class="g"><div class="h">MANA SATU <span class="warm">PALING KERAP?</span></div><div class="grid">{cells}</div>'
                    f'<div class="cm"><svg viewBox="0 0 64 64"><path d="M8 12h48v32H26l-12 10V44H8z" fill="{CYAN}"/><circle cx="22" cy="28" r="3.5" fill="{NAVY}"/><circle cx="32" cy="28" r="3.5" fill="{NAVY}"/><circle cx="42" cy="28" r="3.5" fill="{NAVY}"/></svg>Kongsi di ruangan komen</div></div>')
    ctx.js.append(f'tl.fromTo("#{i} .h",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ctx.L(t10-0.2)});')
    ctx.js.append(f'tl.fromTo("#{i} .c",{{opacity:0,scale:0.7}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)",stagger:0.08}},{ctx.L(t10+0.1)});')
    ctx.js.append(f'tl.to("#{i} .c",{{borderColor:"rgba(255,210,90,.9)",duration:0.15,stagger:{{each:0.09,yoyo:true,repeat:1}}}},{ctx.L(tm)});')
    ctx.js.append(f'tl.fromTo("#{i} .cm",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.45,ease:"back.out(2)"}},{ctx.L(tk-0.6)});')
    ctx.js.append(f'tl.to("#{i}",{{opacity:0,y:-40,duration:0.4,ease:"power2.in"}},{ctx.L(tk+0.1)});')
    for k in range(0, 10, 2):
        ctx.cue("pop", t10 + 0.1 + 0.08 * k, 0.35)
    ctx.cue("hf:pop", tk - 0.6, 0.55)
    # end card
    e = ctx.id("end")
    te = tk + 0.15
    ctx.css.append(f"#{e}{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%,rgba(11,26,51,.78),rgba(6,16,36,.96));text-align:center}}"
                   f"#{e} .n{{position:absolute;left:0;right:0;top:640px;font-family:'League Gothic';font-size:190px;line-height:1;letter-spacing:.02em}}"
                   f"#{e} .bar{{position:absolute;left:390px;top:850px;width:300px;height:6px;background:{CYAN};border-radius:3px;transform-origin:center}}"
                   f"#{e} .s{{position:absolute;left:0;right:0;top:885px;font-family:'Playfair Display';font-style:italic;font-size:72px;color:{WARM}}}"
                   f"#{e} .pp{{position:absolute;left:0;right:0;top:1010px;font-weight:700;font-size:30px;letter-spacing:.42em;color:{CYAN}}}")
    ctx.html.append(f'<div id="{e}"><div class="n">DR AZREN</div><div class="bar"></div><div class="s">Spread Positivity</div><div class="pp">DR AZREN | SPREAD POSITIVITY</div></div>')
    ctx.js.append(f'tl.fromTo("#{e}",{{opacity:0}},{{opacity:1,duration:0.6,ease:"power2.out"}},{ctx.L(te)});')
    ctx.js.append(f'tl.fromTo("#{e} .n",{{opacity:0,y:40,scale:1.12}},{{opacity:1,y:0,scale:1,duration:1.0,ease:"expo.out"}},{ctx.L(te+0.2)});')
    ctx.js.append(f'tl.fromTo("#{e} .bar",{{scaleX:0}},{{scaleX:1,duration:0.6,ease:"power3.out"}},{ctx.L(te+0.6)});')
    ctx.js.append(f'tl.fromTo("#{e} .s",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.6}},{ctx.L(te+0.8)});')
    ctx.js.append(f'tl.fromTo("#{e} .pp",{{opacity:0}},{{opacity:1,duration:0.6}},{ctx.L(te+1.1)});')
    ctx.cue("logo", te + 0.25, 0.8); ctx.cue("shimmer", te + 0.8, 0.4)


GFX = {k[2:]: v for k, v in globals().items() if k.startswith("g_")}


# ------------------------------------------------------------------ transitions
def transition(ctx, kind, k):
    sid, sc = ctx.sid, f"#{ctx.sid}-sc"
    J = ctx.js.append
    if kind in ("dissolve", "split"):
        J(f'tl.fromTo("{sc}",{{opacity:0}},{{opacity:1,duration:0.5,ease:"sine.inOut"}},0);'); ctx.cue("air", ctx.t0 - 0.4, 0.35)
    elif kind == "match":
        J(f'tl.fromTo("{sc}",{{opacity:0}},{{opacity:1,duration:0.25,ease:"none"}},0);')
    elif kind == "whip":
        ctx.html.append(f'<div id="{sid}-streak" class="fx" style="background:linear-gradient(90deg,rgba(255,255,255,0),rgba(220,250,255,.55),rgba(255,255,255,0));width:500px;left:-500px"></div>')
        J(f'tl.fromTo("{sc}",{{x:760,skewX:-10}},{{x:0,skewX:0,duration:0.38,ease:"power4.out"}},0);')
        J(f'tl.fromTo("#{sid}-streak",{{x:0,opacity:1}},{{x:2100,opacity:0,duration:0.38,ease:"power2.out"}},0);')
        ctx.cue("swipe" if k % 2 else "hf:whoosh", ctx.t0 - 0.12, 0.75)
    elif kind == "push":
        J(f'tl.fromTo("{sc}",{{yPercent:22,opacity:0}},{{yPercent:0,opacity:1,duration:0.5,ease:"power3.out"}},0);'); ctx.cue("swish", ctx.t0 - 0.2, 0.55)
    elif kind == "zoom":
        J(f'tl.fromTo("{sc}",{{scale:1.45,opacity:0}},{{scale:1,opacity:1,duration:0.55,ease:"expo.out"}},0);'); ctx.cue("zoom", ctx.t0 - 0.3, 0.7)
    elif kind == "flash":
        ctx.html.append(f'<div id="{sid}-flash" class="fx" style="background:#EFFFFF"></div>')
        J(f'tl.fromTo("#{sid}-flash",{{opacity:0.95}},{{opacity:0,duration:0.45,ease:"power2.out"}},0);'); ctx.cue("camera", ctx.t0, 0.45)
    elif kind == "glitch":
        rnd = random.Random(k)
        bars = "".join(f'<span style="position:absolute;left:0;width:1080px;top:{rnd.randint(150, 1700)}px;height:{rnd.randint(14, 70)}px;background:{rnd.choice([CYAN, "#FF3DA8", WHITE])};mix-blend-mode:screen;opacity:.8"></span>' for _ in range(7))
        ctx.html.append(f'<div id="{sid}-gl" class="fx">{bars}</div>')
        J(f'tl.fromTo("{sc}",{{x:0}},{{keyframes:[{{x:-36,duration:.04}},{{x:28,duration:.04}},{{x:-12,duration:.04}},{{x:0,duration:.04}}]}},0);')
        J(f'tl.fromTo("#{sid}-gl span",{{x:(i)=>((i*97)%5-2)*90,opacity:0.85}},{{x:0,opacity:0,duration:0.3,ease:"steps(5)",stagger:0.01}},0);')
        ctx.cue("hf:glitch-3" if k % 2 else "hf:glitch-1", ctx.t0, 0.28)
    elif kind == "light":
        ctx.html.append(f'<div id="{sid}-leak" class="fx" style="background:radial-gradient(ellipse 60% 45% at 50% 50%,rgba(255,200,120,.85),rgba(255,140,60,.35) 45%,rgba(255,140,60,0) 72%);mix-blend-mode:screen"></div>')
        J(f'tl.fromTo("{sc}",{{opacity:0}},{{opacity:1,duration:0.7,ease:"sine.inOut"}},0);')
        J(f'tl.fromTo("#{sid}-leak",{{xPercent:-70,opacity:0}},{{keyframes:[{{xPercent:-10,opacity:1,duration:0.5,ease:"sine.out"}},{{xPercent:60,opacity:0,duration:0.8,ease:"sine.in"}}]}},0);')
        ctx.cue("air", ctx.t0 - 0.5, 0.45); ctx.cue("shimmer", ctx.t0 - 0.1, 0.25)


def camera(ctx, move, dur):
    c = f"#{ctx.sid}-cam"
    m = {"pushin": ("{scale:1.0}", "{scale:1.09}"), "pullout": ("{scale:1.1}", "{scale:1.01}"),
         "panl": ("{scale:1.06,x:26}", "{scale:1.06,x:-26}"), "panr": ("{scale:1.06,x:-26}", "{scale:1.06,x:26}"),
         "rise": ("{scale:1.05,y:40}", "{scale:1.07,y:-40}"), "drift": ("{scale:1.03,x:-12,y:10}", "{scale:1.07,x:12,y:-10}"),
         "none": ("{scale:1.0}", "{scale:1.04}")}[move]
    ctx.js.append(f'tl.fromTo("{c}",{m[0]},{{...{m[1]},duration:{dur:.3f},ease:"sine.inOut"}},0);')


def motes(ctx, dur, n=12, warm=True):
    rnd = random.Random(hash(ctx.sid) % 1000)
    out = []
    for k in range(n):
        s = rnd.randint(6, 18); x = rnd.randint(0, 1060); y = rnd.randint(150, 1800)
        out.append(f'<span class="mote" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;opacity:{rnd.uniform(.15, .5):.2f}"></span>')
    ctx.html.append(f'<div id="{ctx.sid}-motes" class="fx">{"".join(out)}</div>')
    ctx.js.append(f'tl.fromTo("#{ctx.sid}-motes",{{y:20,x:0}},{{y:-90,x:24,duration:{dur:.3f},ease:"none"}},0);')


# ------------------------------------------------------------------ scene file
def scene_file(ctx, host_dur):
    sc, sid = ctx.sc, ctx.sid
    if sc["kind"] == "vid" or (sc["kind"] == "reuse"):
        src = sc.get("src", sid)
        media = CLIPS[src]
        # slow the clip just enough that it covers the whole slot (speed ramp), never below 0.6x
        rate = 1.0 if sc["kind"] == "reuse" else min(1.0, max(0.6, (media - 0.05) / host_dur))
        vdur = min(host_dur, (media - 0.05) / rate)
        if sc["kind"] == "reuse":
            plate = f'<img class="plate" src="assets/img/{src}_last.jpg" alt="">'
        else:
            plate = (f'<img class="plate" src="assets/img/{sid}_last.jpg" alt="">'
                     f'<video id="{sid}-v" class="vid clip" src="assets/vid/{sid}.mp4" muted playsinline data-start="0" data-duration="{vdur:.3f}" '
                     f'data-playback-rate="{rate:.3f}" data-track-index="1"></video>')
    else:
        plate = f'<img class="plate" src="assets/img/{sc.get("plate", sid)}.jpg" alt="">'
    camera(ctx, sc["cam"], host_dur)
    motes(ctx, host_dur)
    gx = sc.get("gfx")
    a = len(ctx.html)
    if gx:
        GFX[gx["t"]](ctx, gx)
    b = len(ctx.html)
    if sc.get("tr") and sc["tr"] != "cold":
        transition(ctx, sc["tr"], int(re.sub(r"\D", "", sid) or 0))
    pre, gfx_html, trans_html = ctx.html[:a], ctx.html[a:b], ctx.html[b:]
    body = (f'<div id="{sid}-sc" class="sc"><div id="{sid}-punch" class="punch"><div id="{sid}-cam" class="cam">{plate}</div></div>'
            f'{"".join(pre)}<div class="shade-t"></div><div class="shade-b"></div>{"".join(gfx_html)}</div>{"".join(trans_html)}')
    css = BASE_CSS + "\n".join(ctx.css)
    js = "\n".join(ctx.js)
    return f"""<template>
<style>{css}</style>
<div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}" data-layout-allow-overflow data-layout-allow-overlap>
{body}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines["{sid}"] = tl;
</script>
</template>
"""


# ------------------------------------------------------------------ captions + hud
def caption_file(words, phrases):
    groups, css, js = [], [], []
    keys = sorted(phrases)
    for n, pid in enumerate(keys):
        ws = phrases[pid]
        s0 = ws[0]["s"] - 0.06
        nxt = phrases[keys[n + 1]][0]["s"] - 0.06 if n + 1 < len(keys) else END
        e0 = min(nxt, ws[-1]["e"] + 0.7)
        dur = round(e0 - s0, 3)
        chars = sum(len(w["text"]) + 1 for w in ws)
        fs = 66 if chars <= 22 else (62 if chars <= 30 else 56)
        spans = "".join(f'<span class="w{" hl" if w["hl"] else ""}" id="cw{pid}_{k}">{esc(w["text"])}</span> ' for k, w in enumerate(ws))
        gid = f"cg{pid}"
        groups.append(f'<div id="{gid}" class="cg clip" data-start="{s0:.3f}" data-duration="{dur:.3f}" data-track-index="9"><div class="in" style="font-size:{fs}px">{spans}</div></div>')
        js.append(f'tl.fromTo("#{gid} .in",{{y:26,opacity:0}},{{y:0,opacity:1,duration:0.16,ease:"power3.out"}},{s0:.3f});')
        for k, w in enumerate(ws):
            js.append(f'tl.fromTo("#cw{pid}_{k}",{{opacity:0.55,y:0}},{{opacity:1,y:-7,duration:0.08,ease:"power2.out"}},{w["s"]:.3f});'
                      f'tl.to("#cw{pid}_{k}",{{y:0,duration:0.22,ease:"power2.out"}},{w["s"]+0.08:.3f});')
            if w["hl"]:
                js.append(f'tl.fromTo("#cw{pid}_{k}",{{color:"{WHITE}"}},{{color:"{WARM}",duration:0.1}},{w["s"]:.3f});')
        js.append(f'tl.to("#{gid} .in",{{opacity:0,duration:0.1,ease:"power2.in"}},{e0-0.1:.3f});')
    style = f"""#root{{position:absolute;inset:0}}
.cg{{position:absolute;left:110px;width:860px;top:1080px;height:250px;display:flex;align-items:flex-end;justify-content:center}}
.cg .in{{width:860px;text-align:center;font-family:'Montserrat',sans-serif;font-weight:800;line-height:1.16;color:{WHITE};text-wrap:balance;
 text-shadow:0 3px 0 rgba(0,0,0,.55),0 6px 22px rgba(0,0,0,.75),0 0 2px rgba(0,0,0,.9)}}
.cg .w{{display:inline-block;margin:0 .05em}}
.cg .hl{{color:{WHITE}}}"""
    return f"""<template>
<style>{style}</style>
<div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}" data-layout-allow-overlap>
{chr(10).join(groups)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["captions"] = tl;
</script>
</template>
"""


def hud_file(spans):
    els, js = [], []
    for n, (a, b) in enumerate(spans, 1):
        els.append(f'<div id="hud{n}" class="hud clip" data-start="{a:.3f}" data-duration="{b-a:.3f}" data-track-index="8"><div class="in"><b>{n:02d}</b><span>/10</span><i>{esc(SIGN_TITLES[n-1])}</i></div></div>')
        js.append(f'tl.fromTo("#hud{n} .in",{{x:-40,opacity:0}},{{x:0,opacity:1,duration:0.4,ease:"power3.out"}},{a+0.05:.3f});')
        js.append(f'tl.to("#hud{n} .in",{{opacity:0,duration:0.2}},{b-0.22:.3f});')
    style = f"""#root{{position:absolute;inset:0}}
.hud{{position:absolute;left:60px;top:186px;width:700px;height:70px}}
.hud .in{{display:inline-flex;align-items:center;gap:10px;padding:10px 22px 10px 18px;border-radius:999px;background:rgba(6,16,36,.62);border:1.5px solid rgba(111,227,238,.55);font-family:'Montserrat';font-weight:800;font-size:28px;color:{WHITE}}}
.hud b{{font-family:'League Gothic';font-weight:400;font-size:44px;color:{WARM};line-height:1}} .hud span{{opacity:.7}} .hud i{{font-style:normal;margin-left:8px;letter-spacing:.04em;text-transform:uppercase;font-size:28px;color:{CYAN}}}"""
    return f"""<template>
<style>{style}</style>
<div id="root" data-composition-id="hud" data-width="{W}" data-height="{H}">
{chr(10).join(els)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["hud"] = tl;
</script>
</template>
"""


# ------------------------------------------------------------------ main
def main(words_json, proj):
    import subprocess
    d = json.load(open(words_json))
    words = d["tokens"]
    phrases = {}
    for t in words:
        phrases.setdefault(t["phrase"], []).append(t)
    pstart = {k: v[0]["s"] for k, v in phrases.items()}
    for f in os.listdir(f"{proj}/assets/vid"):
        CLIPS[f[:-4]] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                              f"{proj}/assets/vid/{f}"], capture_output=True, text=True).stdout)
    seq = [s for s in S.SCENES if s.get("p") is not None]
    cuts = [0.0 if s["p"] == 0 else round(pstart[s["p"]] - 0.12, 3) for s in seq] + [END]
    os.makedirs(f"{proj}/compositions", exist_ok=True)
    cues, hosts, board = [], [], []
    for k, sc in enumerate(seq):
        t0, t1 = cuts[k], cuts[k + 1]
        ov = OV.get(sc.get("tr") or "cold", 0)
        h0 = max(0.0, t0 - ov)
        nxt_ov = OV.get(seq[k + 1].get("tr") or "cold", 0) if k + 1 < len(seq) else 0
        h1 = min(END, t1 + 0.55)          # stay under the next scene through its entrance
        ctx = Ctx(sc, t0, t1, h0, words, cues)
        open(f"{proj}/compositions/{sc['id']}.html", "w").write(scene_file(ctx, h1 - h0))
        hosts.append(f'<div id="{sc["id"]}" data-composition-id="{sc["id"]}" data-composition-src="compositions/{sc["id"]}.html" '
                     f'data-start="{h0:.3f}" data-duration="{h1-h0:.3f}" data-track-index="{1 + k % 2}" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}" style="position:absolute;inset:0;z-index:{10 + k}"></div>')
        said = " ".join(w["text"] for w in words if t0 - 0.05 <= w["s"] < t1 - 0.05)
        board.append(dict(id=sc["id"], t0=t0, t1=t1, said=said, sc=sc))
    # sign spans for the HUD: chapter scene start -> next chapter (or caveat)
    ch = [b for b in board if (b["sc"].get("gfx") or {}).get("t") == "chapter"]
    cav = next(b["t0"] for b in board if b["id"] == "s43")
    spans = [(c["t0"] + 1.6, (ch[n + 1]["t0"] if n + 1 < len(ch) else cav) - 0.1) for n, c in enumerate(ch)]
    open(f"{proj}/compositions/captions.html", "w").write(caption_file(words, phrases))
    open(f"{proj}/compositions/hud.html", "w").write(hud_file(spans))
    root = f"""<!doctype html>
<html lang="ms">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{ --ground: {DEEP}; --ink: {WHITE}; --navy: {NAVY}; --cyan: {CYAN}; --warm: {WARM}; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: var(--ground); }}
      #main {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; }}
      #bg {{ position: absolute; inset: 0; background: var(--ground); }}
      #grain {{ position: absolute; inset: 0; pointer-events: none; z-index: 800; background-image: url("assets/fx/grain.png"); background-size: 384px 384px; opacity: 0.075; }}
      #hf-vignette {{ position: absolute; inset: 0; pointer-events: none; z-index: 790;
        background: radial-gradient(ellipse at center, transparent 52%, rgba(0, 0, 0, 0.5) 100%); }}
    </style>
  </head>
  <body>
    <div id="main" data-composition-id="main" data-start="0" data-duration="{END}" data-width="{W}" data-height="{H}" data-fps="{FPS}">
      <div id="bg"></div>
      {chr(10).join("      " + h for h in hosts).strip()}
      <div id="hud" data-composition-id="hud" data-composition-src="compositions/hud.html" data-start="0" data-duration="{END}" data-track-index="7" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="position:absolute;inset:0;z-index:700"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{END}" data-track-index="8" data-track-kind="captions" data-width="{W}" data-height="{H}" style="position:absolute;inset:0;z-index:750"></div>
      <div id="hf-vignette" data-layout-ignore></div>
      <div id="grain" data-layout-ignore></div>
      <audio id="narration" class="clip" src="assets/audio/narration.m4a" data-start="0" data-duration="{END}" data-track-index="10" data-volume="1"></audio>
      <audio id="music" class="clip" src="assets/audio/music.m4a" data-start="0" data-duration="{END}" data-track-index="11" data-volume="1"></audio>
      <audio id="sfx" class="clip" src="assets/audio/sfx.m4a" data-start="0" data-duration="{END}" data-track-index="12" data-volume="1"></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      // film grain: a deterministic stepped walk of the noise tile, 12 changes per second
      tl.fromTo("#grain", {{ backgroundPosition: "0px 0px" }}, {{ backgroundPosition: "{137*12*int(END)}px {211*12*int(END)}px", duration: {END}, ease: "steps({12*int(END)})" }}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    open(f"{proj}/index.html", "w").write(root)
    os.makedirs(f"{proj}/../build", exist_ok=True)
    json.dump(dict(cuts=[dict(id=b["id"], t0=b["t0"], t1=b["t1"], tr=b["sc"].get("tr")) for b in board], cues=cues),
              open(f"{proj}/../build/sfx_cues.json", "w"), indent=0)
    json.dump(board and [dict(id=b["id"], t0=b["t0"], t1=b["t1"], said=b["said"]) for b in board], open(f"{proj}/../build/board.json", "w"), ensure_ascii=False, indent=0)
    print(f"{len(seq)} scenes, {len(cues)} sfx cues, {len(phrases)} caption groups, end {END}s")


if __name__ == "__main__":
    main(*sys.argv[1:3])
