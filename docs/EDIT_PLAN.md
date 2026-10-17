# Depot Injection — TikTok reel edit plan

**Source:** `Depot Injection.MP3` (Google Drive, 3:05, 192 kbps)
**Output:** 1080×1920 · 30 fps · H.264 · AAC 48 kHz · 2:33 (voice 2:30 + 3.5 s end card) · −14 LUFS / −1.5 dBTP
**Look:** Netflix-documentary × premium TikTok: photoreal Malaysian B-roll (Higgsfield: Kling O1 keyframes → Kling 3.0 Pro image-to-video), editorial paper-cut cards, kinetic Anton/DM Serif typography, word-synced Malay captions, navy / off-white / teal palette with amber for the side-effects chapter.

## 1. Audio edit (voice is untouched except for cuts and cleanup)

| Source time | Removed | Why |
|---|---|---|
| 0.00–3.50 | leading silence | |
| 18.95–20.32 | "Iklan," | spoken edit cue before the clinic invitation |
| 26.28–27.98 | "boleh da-yang. Boleh." | stutter; kept take is "…makan ubat, boleh datang buat saringan…" |
| 35.42–43.40 | "Ok, balik kepada soalan tadi. Bukan semua pesakit teruk." | abandoned take; restarted at 43.5 |
| 127.00–128.07 | "apa ni" | filler between "boleh bagi" and "kesan ubat" |
| 153.80–160.60 | "Serta ada kesan-kesan sampingan juga bergantung kepada ubat." | first take; second take (same words + "lain … dan pesakit") kept |
| 184.40– | tail | |
| 6.52–6.64 | "dia" | filler: "pesakit skizofrenia ni ~~dia~~ ada ubat" |
| 11.39–11.57 | "Ok," | filler before "jawapannya ya" |
| 43.99–44.22 | "Ok," | filler before "balik kepada soalan tadi" |
| 74.61–75.11 | "adalah" | repeated: "pernah dengar ~~adalah~~, yang pertama adalah" |
| 104.79–105.18 | "dia, dia" | repeated filler: "Secara umum ~~dia, dia~~ kurangkan" |
| 126.00–126.12 | "dia" | filler: "satu injection ni ~~dia~~ boleh" |
| 133.06–133.52 | "lah" | particle after "doktor dah setkan" |
| 165.64–165.79 | "dia" | filler: "depot injection ni ~~dia~~ bukanlah" |

**Pause tightening** (`pipeline/tighten_voice.py`, second pass): every silence, and every breath sitting between two silences (detected by spectral flatness, outside any aligned word), is shortened to a context target: 0.07 s inside a phrase, 0.12 s between phrases, 0.16 s after a comma, 0.24 s after a sentence, 0.32 s between sections. Only silent or breath samples are removed, never word audio; silences inside a word (stop consonants) are skipped. Short voiced sounds between words were kept, because they may be the first syllable of a word. Result: speech 2:37 → 2:30, longest remaining pause 0.39 s.

Every cut edge is checked to sit in silence or an inter-word dip (`pipeline/edit_voice.py` prints the level at each edge). Chain: high-pass 75 Hz → light FFT denoise (source SNR ≈ 36 dB, so only 10 dB reduction) → gentle EQ → de-ess → 2.5:1 compression. No AI voice, no added words.

## 2. Transcript decisions to confirm

| Heard | Subtitled as | Note |
|---|---|---|
| "di klinik saya dinilai" | **"di klinik saya di Nilai"** | Sounds identical. Shown on the CTA card as "Klinik · Nilai". If wrong, set `CTA_LOCATION = ''` in `pipeline/render/timeline.js` and fix line 24 of `pipeline/captions.txt`. |
| "patut balik ke apa" | "pastu balik ke apa" | colloquial *lepas tu* — "inject, then just go home" |
| "pinggan" | "sampingan" | (kesan sampingan) |
| "dilusi", "akertisia", "dudiam" | delusi, akatisia, duduk diam | |
| "pengguna jangka panjang" | penggunaan jangka panjang | |
| "Zuclofentisol / Fluventisol / Flufenazine Dekanuid" | zuclopenthixol / flupentixol / fluphenazine decanoate | standard INN spelling |
| "Clopixol Acufase", "Fluanzol", "Modicate" | Clopixol Acuphase, Fluanxol, Modecate | brand spelling |
| "keselamatan mental" | kesihatan mental | |
| "Secara umum dia, dia kurangkan" | "Secara umum, kurangkan" | repeated "dia, dia" cut from the audio too |

## 3. Time-coded EDL

Times below are on the first cut (2:43). The renderer maps them onto the tightened edit through word anchors (`T()` in `timeline.js`), so every shot and graphic still lands on the same word, about 0–10 s earlier in the final 2:33 cut. Caption phrase timings are in `deliverables/captions.srt` (forced-aligned with MMS-FA; spot-checked against the waveform to ±10 ms).

| Time | Narration (summary) | Picture | Graphics / motion | Transition · SFX |
|---|---|---|---|---|
| 0.0–3.0 | "Doktor, betul ke pesakit skizofrenia…" | **v21** one syringe vs a tower of blister packs, push-in | HOOK headline *SEKALI CUCUK, / TAK PAYAH MAKAN / UBAT HARI-HARI?* on frame 1; chip SKIZOFRENIA | cinematic boom + hit on frame 1 |
| 3.0–5.05 | "…kena cucuk sekali…" | **v01** mother sorting a weekly pill box at night | syringe sticker + handwritten "sekali?" | zoom-punch · whoosh |
| 5.05–7.7 | "…makan ubat tablet setiap hari?" | **v02** tablet pushed into palm (macro) | 7-pill row ticks in; *SETIAP HARI?* | whip pan · ticks |
| 7.7–9.6 | "Ok, jawapannya ya, memang ada." | navy | JAWAPANNYA → stamp **YA!** → MEMANG ADA. | white flash · stamp |
| 9.6–15.4 | "depot injection / long-acting injectable antipsikotik" | **v03** nurse preparing an oily IM injection | taped paper card DEPOT INJECTION + typewriter "long-acting injectable antipsikotik" | paper tear · typewriter |
| 15.4–20.1 | "Kalau anda atau ahli keluarga… skizofrenia / gangguan psikosis" | **v04** mother's hand on her son's shoulder | chips Skizofrenia, Gangguan psikosis | dissolve |
| 20.1–22.4 | "susah nak konsisten makan ubat" | **v07** man rushes out, meds left on counter | yellow scribble circle + arrow on the untouched pouch | whip · pencil |
| 22.4–29.4 | "boleh datang buat saringan… bersama saya, Dr Azren…" | **v05** clinic shophouse → **v06** consultation (doctor's face never shown) | CTA card: SARINGAN & KONSULTASI KESIHATAN MENTAL · bersama Dr Azren · Klinik · Nilai; ✓ on "sesuai" | dissolve / zoom |
| 29.4–35.6 | "Ok, balik kepada soalan tadi. Kenapa… Bukan sebab pesakit tu teruk ke?" | paper desk | newspaper clippings + hand-drawn "?" | tear · rewind |
| 35.6–41.4 | "Tapi… susah nak ingat makan ubat tablet hari-hari" | v07 blurred | 28-day calendar fills with pills; red X on missed days; "susah nak ingat!" | push · ticks / pencil |
| 41.4–45.1 | "Dengan ubat depot injection ni…" | **v22** three golden oil ampoules | chip DEPOT INJECTION | dissolve |
| 45.1–48.0 | "dilepas secara perlahan-lahan… beberapa minggu" | **v09** glowing oil droplet slowly releasing particles | *perlahan-lahan*, BEBERAPA MINGGU | dissolve |
| 48.0–54.9 | "paras ubat lebih konsisten… tidak perlu bergantung kepada ubat pil setiap hari" | v09 blurred | concept graph "Paras ubat dalam badan" (dashed daily-pill line with missed-dose dips vs steady depot line; labelled *Ilustrasi konsep*); pill row struck through | swell |
| 54.9–60.0 | "Antara ubat depot generasi lama…" | navy | UBAT DEPOT / GENERASI LAMA + index cards 01 02 03 | tear |
| 60.0–64.3 | "Clopixol Depot / zuclopenthixol decanoate" | v22 dimmed | drug card 01; chapter chip 01/03 | whip |
| 64.3–72.3 | "antipsikotik… maintenance treatment… skizofrenia / psychotic disorder" | **v10** hospital pharmacist → **v23** patient by the window | chips | dissolves |
| 72.3–77.0 | "diberikan secara berkala mengikut dos dan keadaan pesakit" | **v24** appointment card handed over | strip SECARA BERKALA (no interval stated, as in the audio) + "ikut dos & keadaan pesakit" | whip · pops |
| 77.0–81.3 | "jangan confused dengan Clopixol Acuphase… dua benda berbeza" | paper | JANGAN CONFUSED! Depot ≠ Acuphase | tear · stamp |
| 81.3–86.0 | "Fluanxol Depot / flupentixol decanoate" | v09 dimmed | drug card 02; chip 02/03 | whip |
| 86.0–89.1 | "antipsikotik punya depot. Fungsi dia sama." | navy | 01 = 02, FUNGSI SAMA | |
| 89.1–94.3 | "kurangkan halusinasi, delusi… paranoid" | **v11** woman overwhelmed on a crowded KL MRT (non-stigmatising) | KURANGKAN + chips with ear / thought / eye icons | |
| 94.3–99.2 | "mencegah simptom psikotik daripada relapse" | **v12** same woman calm by the window, Petronas skyline | shield sticker, MENCEGAH RELAPSE | warm dissolve |
| 99.2–102.8 | "Modecate, fluphenazine decanoate" | **v25** golden syringe macro | drug card 03; chip 03/03 | whip |
| 102.8–109.0 | "generasi pertama… maintenance… skizofrenia" | **v13** patient working steadily in a printing shop | chips | |
| 109.0–117.6 | "Konsep dia sama je… kesan ubat yang berpanjangan… rejim yang doktor dah setkan" | paper | KONSEP SAMA; cards; 1 suntikan → long bar; stamp IKUT REJIM DOKTOR | tear · swell · stamp |
| 117.6–122.3 | "kesan-kesan sampingan… first generation" | amber | caution tape, warning sticker, KESAN SAMPINGAN, chip *Antipsikotik generasi pertama* | captions switch to amber |
| 122.3–127.2 | "kena monitor… otot menjadi kaku" | **v14** doctor checking elbow tone | PERLU MONITOR, OTOT KAKU | whip |
| 127.2–130.1 | "tangan jadi menggeletar" | **v15** fine tremor holding teh tarik | TANGAN MENGGELETAR | |
| 130.1–134.0 | "gelisah, tak boleh duduk diam… akatisia" | **v16** restless in a clinic waiting area | GELISAH / TAK BOLEH DUDUK DIAM / = AKATISIA | whip |
| 134.0–137.9 | "pergerakan jadi abnormal kalau penggunaan jangka panjang" | v16 blurred | clipboard checklist recaps all four | pencil checks |
| 137.9–141.3 | "bergantung kepada ubat dan pesakit" | paper | UBAT + PESAKIT venn | tear |
| 141.3–145.1 | "bukanlah kita bagi cucuk, pastu balik ke apa" | v05 blurred | syringe → home, struck out in red | pencil |
| 145.1–148.0 | "kena follow up patient-patient juga" | **v17** nurse checking BP, both smiling | stamp FOLLOW-UP + calendar sticker | whip · stamp |
| 148.0–152.4 | "Tablet ke, injection ke… mana yang lagi power" | split screen v02 / v03 | TABLET / INJECTION chips; MANA LAGI POWER? struck out | push |
| 152.4–157.0 | "mana yang lagi sesuai, selamat dan praktikal…" | **v18** family breakfast → **v19** jog at Titiwangsa with KL Tower | SESUAI. SELAMAT. PRAKTIKAL. (marker swipes) | warm dissolves · hits |
| 157.0–159.5 | "Kalau ada apa-apa soalan, boleh tanya di dalam komen. Take care." | **v20** mother and son on the porch at sunset | comment sticker + "Tanya di komen", handwritten "Take care!" (his own invitation) | |
| 159.5–163.0 | — | end card | Dr Azren · SPREAD POSITIVITY · Psikiatri & Pendidikan Kesihatan Mental · small education disclaimer | swell · chime |

## 4. Sound

- **Score** (original, synthesised in `pipeline/audio_mix.py`, 84 BPM, D minor → F major): heartbeat drone and riser for the hook; documentary pulse and arpeggio for the explanation and drug list; darker Dm–Gm–Dm–A pads with no kick for side effects; build-up for follow-up; suspended chord under "mana lagi power"; warm F–C–Dm–B♭ resolution for the takeaway; Fmaj7 ring-out on the end card.
- **Ducking:** music follows the voice envelope (about −9 dB while he speaks) and sits about 15 dB under the voice overall.
- **SFX** (`pipeline/sfx_synth.py`): 209 cues exported by the renderer, plus an automatic sound on each of the 38 cuts (whip → swipe, zoom → riser and thud, paper tear → rip, push → swish, dissolve → air, flash → camera shutter). There are 34 effect types, each generated as a new random variant per cue, so no two pops, whooshes or taps sound the same. They include woodblock and tap text reveals, marker squeaks on highlight swipes, sparkle shimmers on stickers, pill rattles, glass tinks on the ampoule shots, a heartbeat in the hook, a cinematic braam for KESAN SAMPINGAN, dings on checklist ticks, stamps with thuds, typewriter, risers and a logo hit. The SFX bus sits about 5 dB under the voice peaks, glued with a soft limiter.
- **Scene ambience** matched to every B-roll clip: crickets for night and evening, birds for mornings, the park and breakfast, clinic air-con hum and murmur, MRT rumble with track clacks, mamak chatter with cutlery, printing-shop machine hum, street traffic, and a low drone for the macro shots. It is crossfaded at cuts, ducked under speech, and sits about 27 dB under the voice.
- **Master:** two-pass loudnorm to −14 LUFS integrated, −1.5 dBTP.

## 5. Ethics / accuracy guardrails applied

- No claims beyond the narration. Dosing interval is shown only as "berkala — ikut dos & keadaan pesakit". The graph is labelled *Ilustrasi konsep*. Acuphase is only marked "≠ / dua benda berbeza", as said.
- Symptoms shown with dignity: no violence, horror or crying; the patient character is shown recovering, working and with family.
- The on-screen doctor's face is never shown, so no actor is presented as Dr Azren.
- No real product packaging or brand imagery (unlabelled ampoules/syringes); brand names appear only as typography.
- The only CTA is the narrator's own (clinic invitation and "tanya di komen").
