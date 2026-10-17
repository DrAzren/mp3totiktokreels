#!/bin/bash
# End-to-end build for the Depot Injection reel.
# Requires: ffmpeg, python3 (numpy scipy soundfile faster-whisper torch torchaudio), node + playwright (Chromium).
#   WORK=/path/to/workdir ./build.sh            # expects $WORK/src/depot.mp3 and $WORK/broll/clips/vNN.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:?set WORK to a scratch directory}"
cd "$WORK"; mkdir -p build broll/frames

# 1. decode + transcribe (Whisper large-v3, used for the cut list) -------------------------
ffmpeg -v error -y -i src/depot.mp3 -ac 1 -ar 48000 src/voice48.wav
[ -f transcript_v3.json ] || { ffmpeg -v error -y -i src/depot.mp3 -ac 1 -ar 16000 -f f32le src/depot16k.f32
  python3 "$HERE/transcribe.py" src/depot16k.f32 large-v3 transcript_v3.json; }

# 2. cut retakes + filler words, align, then shorten pauses and breaths ---------------------
python3 "$HERE/edit_voice.py" src/voice48.wav transcript_v3.json build
python3 "$HERE/align_captions.py" build/voice_edit.wav "$HERE/captions.txt" build && cp build/words.json build/words_pre.json
python3 "$HERE/tighten_voice.py" build/voice_edit.wav build/words_pre.json build
ffmpeg -v error -y -i build/voice_tight.wav -af "highpass=f=75,afftdn=nr=10:nf=-52:tn=1,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.5:g=1.5,deesser=i=0.3,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=140:makeup=1.5,alimiter=limit=0.89" build/voice_clean.wav

# 3. force-align the caption script to the final voice -> words.json + captions.srt ---------
python3 "$HERE/align_captions.py" build/voice_tight.wav "$HERE/captions.txt" build
# timeline.js literals were authored against render/words_v1.json; map them onto this edit
python3 "$HERE/remap_timeline.py" "$HERE/render/words_v1.json" build/words.json 163.0 build/remap.json

# 4. B-roll clips -> 30 fps cover-cropped JPEG frames -----------------------------------------
for c in broll/clips/*.mp4; do n=$(basename "$c" .mp4); [ -d "broll/frames/$n" ] && continue; mkdir -p "broll/frames/$n"
  ffmpeg -v error -y -i "$c" -vf "scale=1084:1924:flags=lanczos,crop=1080:1920,framerate=fps=30:interp_start=0:interp_end=255:scene=100" -q:v 3 "broll/frames/$n/%05d.jpg"; done

# 5. render picture (headless Chromium, 4 workers) -----------------------------------------
mkdir -p build/site/data build/video
for f in index.html engine.js components.js timeline.js fonts; do ln -sfn "$HERE/render/$f" "build/site/$f"; done
ln -sfn "$WORK/broll/frames" build/site/frames; cp build/words.json build/remap.json build/site/data/
python3 -c "import os,json;d='broll/frames';json.dump({k:len(os.listdir(os.path.join(d,k))) for k in sorted(os.listdir(d))},open('build/site/data/clips.json','w'))"
node "$HERE/render/render.mjs" --site build/site --out build/video/video_noaudio.mp4 --sfx build/sfx.json --workers 4

# 6. score + SFX + ambience (uses build/shots.json from the renderer), master -14 LUFS, mux ---
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 build/video/video_noaudio.mp4)
python3 "$HERE/audio_mix.py" build/voice_clean.wav build/sfx.json "$DUR" build/mix_raw.wav
M=$(ffmpeg -hide_banner -i build/mix_raw.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p' |
  python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -v error -y -i build/mix_raw.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:$M:linear=true,aresample=48000" -c:a pcm_s16le build/mix_master.wav
ffmpeg -v error -y -i build/video/video_noaudio.mp4 -i build/mix_master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart build/DepotInjection_DrAzren_TikTok.mp4
echo "done: $WORK/build/DepotInjection_DrAzren_TikTok.mp4"
