# 10 Ubat Psikiatri & Kenaikan Berat Badan (Dr Azren | Spread Positivity)

Malay reel, 1080×1920, 2:58. Voice: Dr Azren's ElevenLabs voice clone (model eleven_v4) (script in `SCRIPT.md`, the exact TTS input with phonetic drug names in `tts_input.txt`).

| File | What |
|---|---|
| `SCRIPT.md` | Approved script |
| `captions_full.txt` | Caption script for the whole TTS take; lines starting with `~` are cut from the audio to fit 3:00 |
| `captions.txt`, `captions.srt`, `words.json` | Final captions, forced-aligned to the edited voice |
| `pipeline/cut_voice.py` | Align the TTS take, remove `~` lines, tighten pauses, speed ×1.06 |
| `music_sections.json` | Score map for `pipeline/audio_mix.py` (`MUSIC_SECTIONS=...`) |
| `../../pipeline/render/timeline_weightgain.js` | Shots, motion graphics, 3D book (load via `index_weightgain.html`) |
| `broll_jobs.json` | Higgsfield job IDs (8 new Seedance 2.0 Mini clips + reused Depot clips) |
| `post_caption.md` | TikTok / Facebook / YouTube caption |
| `Thumbnail_WeightGain_*.jpg`, `thumbnail/thumb.html` | Cover (uses `pipeline/thumbnail/` assets) |

Build (scratch dir `$WORK` with `src/v4.wav`, `broll/frames/*`, `book.jpg` = book cover from Google Drive):

```
python3 pipeline/cut_voice.py $WORK/src/v4.wav captions_full.txt $WORK/build 1.06
python3 ../../pipeline/align_captions.py $WORK/build/voice_edit.wav captions.txt $WORK/build
node ../../pipeline/render/render.mjs --site $WORK/build/site --out $WORK/build/video/video_noaudio.mp4 --sfx $WORK/build/sfx.json --workers 4
MUSIC_SECTIONS=music_sections.json python3 ../../pipeline/audio_mix.py $WORK/build/voice_clean.wav $WORK/build/sfx.json 178.329 $WORK/build/mix_raw.wav
```
