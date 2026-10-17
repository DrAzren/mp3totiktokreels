# MP3 → cinematic TikTok reel

Turns a voice recording into a 1080×1920 documentary-style reel with photoreal AI B-roll, motion graphics, word-synced captions, sound design and an original score, without altering or replacing the narrator's voice.

First production: **Depot Injection** (Dr Azren | Spread Positivity), Malay, 2:43.

| Path | What |
|---|---|
| `docs/EDIT_PLAN.md` | Time-coded EDL, audio cut list, transcript decisions to confirm, sound plan, accuracy guardrails |
| `docs/BROLL_PROMPTS.md` | Keyframe and motion prompts for all 23 Higgsfield clips |
| `deliverables/captions.srt` | Malay subtitles (forced-aligned) for upload as a separate caption track |
| `deliverables/transcript_ms.txt` | Clean transcript of the edited voice track |
| `deliverables/broll_jobs.json` | Higgsfield job IDs (keyframes + clips) |
| `pipeline/` | Reproducible build: `edit_voice.py` → `align_captions.py` → `render/` (canvas engine, components, `timeline.js` = the editable project) → `audio_mix.py`; `build.sh` runs it end to end |

The rendered MP4 (~230 MB) is not committed. Run `pipeline/build.sh` to reproduce it.

## Editing the reel

- **Wording on screen**: `pipeline/captions.txt` (one caption per line; `*word` highlights, `Display=spoken` fixes alignment spelling), then re-run alignment.
- **Shots, graphics, timing**: `pipeline/render/timeline.js`. Everything is keyed to word times (`P(i)`, `Wd(i, j)`), so it stays in sync after caption edits.
- **Preview frames**: `node pipeline/render/render.mjs --site <site> --stills 12.5,60 --outdir previews/`
