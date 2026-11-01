# ADHD Dewasa: 10 tanda ADHD dalam kalangan orang dewasa

Second production: Dr Azren's ElevenLabs narration (Malay, 3:58) turned into a 1080×1920 documentary reel built in **HyperFrames**, with **Higgsfield** AI B-roll on every scene (23.42 of the 30-credit cap spent).

| Path | What |
|---|---|
| `deliverables/storyboard.md` | Scene-by-scene storyboard: timings, narration, AI prompts, graphics, transitions, sound |
| `deliverables/transcript.srt` | Verbatim Malay subtitles (forced-aligned, 174 cues) |
| `deliverables/higgsfield_credit_report.md` | Price checks, chronological credit ledger, job IDs |
| `deliverables/final_video_report.md` | Render specs, QA checks, audio measurements, limitations |
| `deliverables/final_tiktok_reel.mp4` | The finished reel (not committed: too large for git; see the report) |
| `source_project/` | The editable HyperFrames project: `index.html` + 53 scene compositions + captions + HUD, graded stills, clips, audio stems |
| `captions.txt` | Verbatim caption script (`*word` = highlight, `Display=spoken` = aligner spelling) |
| `scenes.py` | The scene plan: phrase anchor, AI prompt, camera move, graphic, transition per scene |
| `tools/` | `prep_assets.py` (grade + conform), `build_project.py` (generates the HyperFrames project), `audio_build.py` (narration polish, score, SFX, master), `write_docs.py` |
| `build/` | `words.json` (word timings), `sfx_cues.json`, `board.json`, `higgsfield_jobs.json` |

## Rebuild

```bash
# 1. word timings (torchaudio MMS forced alignment of captions.txt to the narration)
python3 ../../pipeline/align_captions.py narration_48k.wav captions.txt build
# 2. HyperFrames project (scenes + captions + HUD + SFX cue list)
python3 tools/build_project.py build/words.json source_project
# 3. audio stems + -14 LUFS master
python3 tools/audio_build.py narration.mp3 build/sfx_cues.json source_project build
# 4. check, preview, render
cd source_project && npx hyperframes check && npx hyperframes preview
npx hyperframes render --quality delivery --crf 19 -o renders/video_hf.mp4
# 5. delivery mux: the rendered picture + the loudness-normalised master of the same stems
ffmpeg -i renders/video_hf.mp4 -i ../build/mix_master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart final_tiktok_reel.mp4
```

Edit wording in `captions.txt`, then re-align and rebuild: every graphic is keyed to the time of its word, so it stays in sync. Edit a shot's look or graphic in `scenes.py` / `tools/build_project.py`, or open `source_project/` in HyperFrames Studio and edit the compositions directly.
