"""Grade + conform the Higgsfield assets into the HyperFrames project.

Usage: python3 prep_assets.py <gen_dir> <project_dir>
 stills  -> assets/img/<id>.jpg  1134x2016 (5% camera headroom), unified look baked in
 clips   -> assets/vid/<id>.mp4  1080x1920 30 fps H.264, light denoise + sharpen, same look, silent
            assets/img/<id>_last.jpg  last frame (hold plate under the clip)
The look: slightly lifted blacks, navy/cyan shadows, warm highlights, -8% saturation.
"""
import os, subprocess, sys, glob, json

GRADE = ("eq=contrast=1.05:saturation=0.92:gamma=0.98,"
         "colorbalance=rs=-0.03:gs=0.00:bs=0.05:rm=-0.01:bm=0.02:rh=0.05:gh=0.02:bh=-0.03,"
         "curves=master='0/0.025 0.25/0.22 0.5/0.49 0.85/0.86 1/0.97'")


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def main(gen, proj):
    os.makedirs(f"{proj}/assets/img", exist_ok=True); os.makedirs(f"{proj}/assets/vid", exist_ok=True)
    for p in sorted(glob.glob(f"{gen}/img/s*.png")):
        sid = os.path.basename(p)[:-4]
        out = f"{proj}/assets/img/{sid}.jpg"
        if os.path.exists(out): continue
        run("-i", p, "-vf", f"scale=1134:2016:force_original_aspect_ratio=increase:flags=lanczos,crop=1134:2016,{GRADE}",
            "-q:v", "3", out)
        print("img", sid)
    for p in sorted(glob.glob(f"{gen}/vid/s*.mp4")):
        sid = os.path.basename(p)[:-4]
        out = f"{proj}/assets/vid/{sid}.mp4"
        if os.path.exists(out): continue
        run("-i", p, "-vf",
            "hqdn3d=1.5:1.5:3:3,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,"
            f"unsharp=5:5:0.45:5:5:0.0,{GRADE},framerate=fps=30",
            "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out)
        run("-sseof", "-0.1", "-i", out, "-frames:v", "1", "-q:v", "3", f"{proj}/assets/img/{sid}_last.jpg")
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                           capture_output=True, text=True).stdout.strip()
        print("vid", sid, d)


if __name__ == "__main__":
    main(*sys.argv[1:3])
