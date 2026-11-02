# Final video report: ADHD Dewasa

**File:** `deliverables/final_tiktok_reel.mp4` (280.3 MB; not committed to git, which caps files at 100 MB, so it is delivered alongside this report)
**Status:** rendered and verified (all measurements below come from the delivered file)

## Specs (measured with ffprobe)

| | Requested | Delivered |
|---|---|---|
| Resolution | 1080×1920 (9:16) | 1080×1920 |
| Frame rate | 30 fps | 30/1, 7,245 frames |
| Video codec | H.264 | H.264 High, yuv420p, CRF 20 capped at 9 Mbps (avg 9.0 Mbps), 2 s GOP, faststart |
| Audio codec | AAC | AAC-LC 48 kHz stereo, 257 kbps |
| Duration | full narration | 241.5 s = 237.8 s narration (complete) + 3.7 s end card |

## Checks

| Check | Result |
|---|---|
| Missing media | none: every scene has its plate; 53/53 scene transitions inspected frame by frame on the master render |
| Black frames (`blackdetect`, ≥ 0.1 s, luma < 10 %) | **none** |
| Frozen picture (`freezedetect`, ≥ 1.5 s) | **none** |
| Narration preserved | the complete ElevenLabs MP3 is used, nothing cut, re-timed or re-voiced; every 1 s window of the delivered narration stem correlates with the original (median 0.885 after gentle EQ/compression) |
| Narration sync | delivered audio vs original MP3: offset **0.1 ms** at 0:20, 2:00 and 3:40 (limiter look-ahead of 4.9 ms was measured and compensated) |
| Subtitle sync | captions forced-aligned to the narration with torchaudio MMS (534 words); highlight and graphic timings are keyed to those word times |
| Loudness | **−14.0 LUFS** integrated, true peak **−1.4 dBTP**, max sample −1.4 dBFS: no clipping |
| Music vs voice | score sits ~17 dB under the voice and ducks a further ~8 dB while words are spoken; SFX ~7 dB under voice peaks and step back during words |
| Safe zones | nothing in the top 168 px (sign chip starts at y = 186); captions end at y ≤ 1330; graphics live in y 230–1150; no text under the right action rail |
| HyperFrames `check` | `ok: true`: 0 lint, runtime, layout, motion or contrast errors (warnings left: the caption track is one large file by design) |
| Watermarks | none: Higgsfield outputs carry no watermark; no stock footage or third-party logos |

## Pipeline

1. **Audio analysis:** 237.79 s mono MP3, Malay (Whisper large-v3, p = 0.9995). Full transcript corrected by isolated re-decoding and forced-alignment scoring (see Transcript decisions).
2. **Storyboard:** 53 scenes (average 4.5 s) anchored to caption phrases; every scene has its own visual concept (`storyboard.md`).
3. **Higgsfield (23.42 credits):** 52 Z Image stills (51 keyframes + 1 kept test), 1 Kling O1 reference keyframe, 6 Seedance 2.0 Mini image-to-video clips. Details: `higgsfield_credit_report.md`.
4. **Grade/conform:** unified navy/cyan/warm grade baked into every plate; the 480p clips are denoised (hqdn3d), Lanczos-scaled, lightly sharpened and frame-blended to 30 fps. Upscaling adds no real detail; the 480p shots are close-ups and moody low-key scenes where that holds up.
5. **HyperFrames composition:** generated `index.html` + 53 scene sub-compositions + captions + sign-counter HUD, GSAP timelines; registry vignette; deterministic film grain; rendered locally by HyperFrames 0.8.229 (Chrome, software GPU, 18.5 min).
6. **Sound:** narration polish (HPF 60 Hz, ±1.5 dB EQ, 2:1 compression, peak limit); original procedural score that follows the story (D-minor unease → steady pulse through the ten signs → floating hyperfocus section → serious caveat → warm F-major hope); 21 scene ambiences; 196 placed SFX from HyperFrames' bundled library plus synthesised variants, so repeated sounds never repeat exactly; master normalised to −14 LUFS.
7. **Delivery:** the HyperFrames render (CRF 19, 14 Mbps) is re-encoded once to a TikTok-friendly 9 Mbps file and muxed with the loudness-normalised master of the same stems.

## Transcript decisions (please confirm)

| Whisper heard | Subtitled as | Why |
|---|---|---|
| “selalu tersenyum” | **selalu terlupa** | Re-decoding the clip alone gives “terlupa”; forced alignment also scores it better, and the examples that follow are all about forgetting |
| “Dr. Azrin” | **Dr Azren** | creator's name |
| “di klinik saya dinilai” | **di klinik saya di Nilai** | sounds identical; read as the town of Nilai (same as the Depot Injection reel); shown as “Klinik · Nilai” on the lower third |
| “terbitan white code” | **terbitan Whitecoat** | confirmed from the book's own cover (WHITECOAT NON-FICTION logo, www.whitecoat.com.my) |
| “Doktor, Saya Boleh Sembuh Ke?” | **“Dr, Saya Boleh Sembuh Ke?”** | spoken “Doktor”; subtitle uses the book's real title as printed on the cover |
| meeting, appointment, scroll TikTok, deadline, game, hyperfocus, anxiety, depression, share | kept in English as spoken | code-switching preserved verbatim |

## Book scene (s50, 3:30–3:39)

Dr Azren's book is shown as a real 3D object, built in HyperFrames (CSS 3D) from the print-ready cover PDF in Google Drive (“Front and Back Cover Dr Saya Boleh Sembuh Ke?.pdf”, rasterised at 300 dpi and cut along its trim marks): front cover, 13 mm spine and back cover at their true 125 × 177 mm proportions, with paper page edges. It rises in, faces the camera as the title is spoken (light sweep across the cover), then turns to reveal the spine. The cover artwork is used as-is, not AI-regenerated, so every word on it stays exact. It cost no Higgsfield credits.

## Limitations and disclosures

- **AI video vs animated stills:** with real prices of 0.5 credits per video-second (480p), video for all 53 beats would have cost about 120 credits. 6 scenes are true AI video; the other 47 use their own AI-generated photoreal stills animated locally (camera moves, parallax light motes, punch-ins, transitions), the last-resort substitution the brief allowed.
- **Same character:** only the hook and the payoff show the same man (kept consistent with a Kling O1 reference image). Other scenes show different Malaysian adults on purpose: ADHD affects many kinds of people. Dr Azren's face is never generated; the clinic scenes show only hands and empty rooms.
- **Music** is an original instrumental composed procedurally for this video (no licence needed). No HeyGen sign-in was available in this cloud session, so the HyperFrames music catalog wasn't used, and Higgsfield's music model is restricted to its game pipeline.
- **Loudness, not listening:** audio levels, peaks and sync were measured; nobody listened to the mix in this session. Give it a listen on a phone before posting.
- **Duration:** 4:01 is fine for TikTok/Reels (both allow longer), but YouTube Shorts allows up to 3:00. For Shorts you would need a cut, e.g. signs 1–10 only.
- **Medical accuracy:** on-screen text paraphrases only what the narration says (e.g. hyperfocus is not a diagnostic criterion; symptoms before age 12, in more than one setting, with significant impairment; sleep problems, anxiety and depression can mimic ADHD). No claims were added.
- The full-quality master render (`source_project/renders/video_hf.mp4`, 410 MB) is not committed; rebuild it with the commands in `../README.md`.
