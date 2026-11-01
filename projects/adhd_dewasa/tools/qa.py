"""QA for the delivered reel: specs, black frames, frozen frames, loudness/peaks, transition contact sheets.

Usage: python3 qa.py <final.mp4> <out_dir>
"""
import json, os, re, subprocess, sys


def run(*a):
    return subprocess.run(a, capture_output=True, text=True)


def main(mp4, out):
    os.makedirs(out, exist_ok=True)
    rep = {}
    pr = json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", mp4).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
    rep["video"] = dict(codec=v["codec_name"], profile=v.get("profile"), w=v["width"], h=v["height"], fps=v["r_frame_rate"],
                        pix_fmt=v["pix_fmt"], frames=v.get("nb_frames"), bitrate_kbps=int(v.get("bit_rate", 0)) // 1000)
    rep["audio"] = dict(codec=a["codec_name"], sr=a["sample_rate"], ch=a["channels"], bitrate_kbps=int(a.get("bit_rate", 0)) // 1000)
    rep["duration"] = float(pr["format"]["duration"]); rep["size_mb"] = round(int(pr["format"]["size"]) / 1e6, 1)
    # black frames (luma < ~10%), at least 0.1 s
    bd = run("ffmpeg", "-hide_banner", "-i", mp4, "-vf", "blackdetect=d=0.1:pix_th=0.10", "-an", "-f", "null", "-").stderr
    rep["black_segments"] = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)
    # frozen picture for >= 1.5 s
    fd = run("ffmpeg", "-hide_banner", "-i", mp4, "-vf", "freezedetect=n=0.002:d=1.5", "-an", "-f", "null", "-").stderr
    rep["frozen_segments"] = re.findall(r"freeze_start: ([\d.]+)", fd)
    # loudness + true peak + clipping
    ln = run("ffmpeg", "-hide_banner", "-i", mp4, "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-").stderr
    j = json.loads(ln[ln.rindex("{"):ln.rindex("}") + 1])
    vd = run("ffmpeg", "-hide_banner", "-i", mp4, "-vn", "-af", "volumedetect", "-f", "null", "-").stderr
    rep["loudness"] = dict(integrated_lufs=float(j["input_i"]), true_peak_dbtp=float(j["input_tp"]), lra=float(j["input_lra"]),
                           max_volume_db=float(re.search(r"max_volume: ([-\d.]+)", vd).group(1)))
    json.dump(rep, open(f"{out}/qa.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
