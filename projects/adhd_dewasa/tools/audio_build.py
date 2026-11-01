"""Audio for the ADHD Dewasa reel: narration (untouched words, gentle polish), original score, SFX + ambience stems,
and a -14 LUFS master.

Usage: python3 audio_build.py <narration.mp3> <sfx_cues.json> <project_dir> <build_dir>
Writes project assets/audio/{narration,music,sfx}.wav (the stems the HyperFrames project plays, levels baked in)
and build/mix_master.wav (sum of the stems, loudness-normalised) used for the delivery mux.

Music is composed procedurally here (pipeline/audio_mix.py instruments), so it is original and royalty-free.
Sound effects: HyperFrames' bundled offline SFX library ("hf:*") plus synthesised variants (pipeline/sfx_synth.py).
"""
import json, os, subprocess, sys, glob
import numpy as np
import soundfile as sf

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import audio_mix as am      # noqa: E402  (score instruments, envelope follower)
import sfx_synth as sx      # noqa: E402

SR = 48000
END = 241.5
HF_SFX = sorted(glob.glob("/root/.npm/_npx/*/node_modules/hyperframes/dist/skills/media-use/audio/assets/sfx"))

# emotional arc -> score sections (start, end, chords, layers)
am.SECTIONS = [
    (0.0, 9.0, ["Dm"], {"drone": 1.0, "heart": 0.9}),                                  # hook: unease
    (9.0, 16.5, ["Dm"], {"drone": 0.8, "heart": 0.7, "riser": 0.8}),                   # build to the ADHD reveal
    (16.5, 30.0, ["Dm", "Bb", "F", "C"], {"pad": 0.9, "keys": 0.6}),                   # it is not just children
    (30.0, 35.5, ["Bb", "C"], {"pad": 0.9, "arp": 0.5, "riser": 0.5}),                 # "10 tanda"
    (35.5, 79.3, ["Dm", "Bb", "F", "C"], {"pad": 0.8, "arp": 0.8, "kick": 0.45}),      # signs 1-4: steady pulse
    (79.3, 116.4, ["Dm", "Bb", "F", "C"], {"pad": 0.85, "arp": 0.9, "kick": 0.55, "sub": 0.55}),  # signs 5-7
    (116.4, 141.5, ["Gm", "Bb", "F", "C"], {"pad": 0.85, "arp": 0.8, "keys": 0.4, "kick": 0.45}),  # signs 8-9
    (141.5, 166.4, ["Bb", "C", "Dm", "C"], {"pad": 0.9, "arp": 0.55}),                 # hyperfocus: floating, no drums
    (166.4, 200.9, ["Dm", "Gm", "Dm", "A"], {"pad": 0.85, "keys": 0.45, "drone": 0.3}),  # how diagnosis works: serious
    (200.9, 219.3, ["F", "C", "Dm", "Bb"], {"pad": 0.95, "keys": 0.6}),                # help is available: warm
    (219.3, 224.2, ["Csus"], {"pad": 0.9, "riser": 0.5}),                              # lift
    (224.2, 236.5, ["F", "C", "Dm", "Bb"], {"pad": 1.05, "arp": 0.9, "keys": 0.7, "kick": 0.5, "sub": 0.6}),  # hope
    (236.5, 999, ["Fmaj7"], {"pad": 1.0, "keys": 0.6}),                                # end card
]

AMB = {  # scene -> (bed, level); everything else gets a faint room tone
    "s01": (sx.amb_room, 0.6), "s02": (sx.amb_crickets, 0.5), "s03": (sx.amb_room, 0.5), "s04": (sx.amb_crickets, 0.6),
    "s05": (sx.amb_room, 0.9), "s06": (sx.amb_drone, 0.6), "s07": (sx.amb_birds, 0.7), "s08": (sx.amb_room, 0.6),
    "s10": (sx.amb_street, 0.8), "s12": (sx.amb_room, 0.8), "s13": (sx.amb_room, 0.8), "s16": (sx.amb_crickets, 0.7),
    "s22": (sx.amb_street, 0.7), "s30": (sx.amb_crowd, 1.0), "s38": (sx.amb_drone, 0.5), "s40": (sx.amb_drone, 0.5),
    "s44": (sx.amb_birds, 0.9), "s46": (sx.amb_crickets, 0.7), "s49": (sx.amb_room, 0.6), "s51": (sx.amb_street, 0.8),
    "s52": (sx.amb_birds, 0.6),
}
GAIN = dict(sx.GAIN, glitchs=0.5, typing=0.5, ping=0.5)
_cache = {}


def load_hf(name):
    if name in _cache:
        return _cache[name]
    p = os.path.join(HF_SFX[0], name + ".mp3")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    x /= np.abs(x).max() + 1e-9
    _cache[name] = x
    return x


def render_cue(c, k):
    r = np.random.default_rng(2000 + k)
    t = c["type"]
    if t.startswith("hf:"):
        x = load_hf(t[3:])
        if "src_from" in c:
            x = x[int(c["src_from"] * SR):]
        g = {"impact-bass-1": 0.9, "impact-bass-2": 1.0, "riser": 0.7, "notification": 0.55, "typing": 0.45,
             "glitch-1": 0.45, "glitch-3": 0.5, "whoosh": 0.8, "whoosh-short": 0.8, "pop": 0.6, "click-soft": 0.5}.get(t[3:], 0.6)
        return x.copy(), g
    if t in ("glitchs",):
        return load_hf("glitch-3").copy(), 0.4
    if t not in sx.FX:
        return None, 0
    fn = sx.FX[t]
    x = fn(r, c["dur"]) if t in ("scribble", "type", "typewriter") and "dur" in c else fn(r)
    return x, GAIN.get(t, 0.6)


def place(buf, x, t0, g, pan=0.0):
    i = int(t0 * SR); j = min(len(buf), i + len(x))
    if i < 0:
        x, i = x[-i:], 0
    if i >= len(buf) or j <= i:
        return
    buf[i:j, 0] += x[:j - i] * g * np.sqrt(0.5 - pan / 2) * 1.41
    buf[i:j, 1] += x[:j - i] * g * np.sqrt(0.5 + pan / 2) * 1.41


def lufs(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    j = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
    return j


def main(mp3, cues_json, proj, build):
    n = int(END * SR)
    os.makedirs(f"{proj}/assets/audio", exist_ok=True); os.makedirs(build, exist_ok=True)
    # 1. narration: the original MP3, every word kept; only HPF, gentle presence EQ, 2:1 compression, peak limit
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-af",
                    "highpass=f=60,equalizer=f=220:t=q:w=1.0:g=-1.5,equalizer=f=3200:t=q:w=1.4:g=1.2,"
                    "acompressor=threshold=-20dB:ratio=2:attack=10:release=160:makeup=1.5,alimiter=limit=0.84:level=false",
                    "-ar", str(SR), "-ac", "1", f"{build}/voice_polish.wav"], check=True)
    v, sr = sf.read(f"{build}/voice_polish.wav", dtype="float64"); assert sr == SR
    # undo the limiter's look-ahead latency so the voice sits exactly where the captions were aligned
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    o = np.frombuffer(raw, np.float32).astype(np.float64)
    a = o[SR * 60:SR * 62]
    lag = max(range(0, 600), key=lambda L: np.dot(a, v[SR * 60 + L:SR * 62 + L]))
    v = v[lag:]
    print(f"voice latency compensated: {lag} samples ({lag / SR * 1000:.1f} ms)")
    voice = np.zeros(n); voice[:min(n, len(v))] = v[:n]

    data = json.load(open(cues_json))
    cuts, cues = data["cuts"], data["cues"]
    # 2. score
    music = am.build_music(END)
    # 3. sfx bus
    fx = np.zeros((n, 2)); last = {}
    for k, c in enumerate(sorted(cues, key=lambda c: c["t"])):
        if c["t"] - last.get(c["type"], -9) < 0.07:
            continue
        last[c["type"]] = c["t"]
        x, g = render_cue(c, k)
        if x is None:
            print("  unknown sfx", c["type"]); continue
        pan = np.random.default_rng(k).uniform(-0.35, 0.35) if c["type"] in ("pop", "tap", "tick", "check", "marker", "paper") else 0.0
        place(fx, x, c["t"], g * c["gain"], pan)
    # 4. ambience beds per scene, crossfaded
    amb = np.zeros((n, 2)); xf = 0.4
    for k, c in enumerate(cuts):
        fn, lvl = AMB.get(c["id"], (sx.amb_room, 0.35))
        t0, t1 = max(0.0, c["t0"] - xf), min(END, c["t1"] + xf)
        a = fn(np.random.default_rng(500 + k), t1 - t0); b = fn(np.random.default_rng(900 + k), t1 - t0)
        m = len(a); e = np.ones(m); f = int(xf * SR)
        e[:f] = np.linspace(0, 1, f); e[-f:] = np.linspace(1, 0, f)
        i = int(t0 * SR); j = min(n, i + m)
        amb[i:j, 0] += a[:j - i] * e[:j - i] * lvl; amb[i:j, 1] += b[:j - i] * e[:j - i] * lvl

    # 5. levels: music ~17 dB under the voice and ducked a further ~8 dB while he speaks; ambience ~30 dB under
    env = am.envelope(voice); env = np.clip(env / (np.percentile(env[env > 1e-4], 95) + 1e-9), 0, 1)
    rms = lambda x: np.sqrt(np.mean(x ** 2) + 1e-12)
    speech = np.abs(voice) > 1e-3
    vr, vpk = rms(voice[speech]), np.percentile(np.abs(voice[speech]), 99.9)
    music *= (vr * 10 ** (-17 / 20)) / rms(music)
    music *= (1 - 0.6 * env)[:, None]
    amb *= (vr * 10 ** (-30 / 20)) / rms(amb[np.abs(amb).sum(1) > 1e-6])
    amb *= (1 - 0.4 * env)[:, None]
    fx *= (vpk * 10 ** (-7 / 20)) / (np.percentile(np.abs(fx[np.abs(fx) > 1e-4]), 99.5) + 1e-9)
    fx *= (1 - 0.35 * env)[:, None]                       # effects step aside for words
    fx = np.tanh(fx / (vpk * 1.1)) * vpk * 1.1
    sfxbus = fx + amb

    sf.write(f"{proj}/assets/audio/narration.wav", np.stack([voice, voice], 1).astype(np.float32), SR, subtype="PCM_24")
    sf.write(f"{proj}/assets/audio/music.wav", music.astype(np.float32), SR, subtype="PCM_24")
    sf.write(f"{proj}/assets/audio/sfx.wav", sfxbus.astype(np.float32), SR, subtype="PCM_24")
    for name in ("narration", "music", "sfx"):   # compact copies the HyperFrames project plays (WAVs stay out of git)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{proj}/assets/audio/{name}.wav", "-c:a", "aac", "-b:a", "256k",
                        f"{proj}/assets/audio/{name}.m4a"], check=True)
    mix = voice[:, None] + music + sfxbus
    print("raw mix peak dBFS", 20 * np.log10(np.abs(mix).max()))
    sf.write(f"{build}/mix_raw.wav", mix.astype(np.float32), SR, subtype="FLOAT")
    m = lufs(f"{build}/mix_raw.wav")
    lin = (f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
           f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{build}/mix_raw.wav", "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11:{lin},aresample={SR}",
                    "-c:a", "pcm_s24le", f"{build}/mix_master.wav"], check=True)
    f = lufs(f"{build}/mix_master.wav")
    print(f"master: {f['input_i']} LUFS, true peak {f['input_tp']} dBTP, LRA {f['input_lra']}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
