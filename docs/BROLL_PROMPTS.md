# B-roll generation sheet (Higgsfield)

Workflow per shot: **keyframe** with `kling_omni_image` (2k, 9:16; character shots pass the two reference images) → manual review for hands, faces, text and cultural accuracy → **animate** with `kling3_0` mode `pro`, `sound: off`, 9:16, start_image = keyframe.
Cost for this reel: about 0.5 credit per keyframe and 8.75 credits per 5 s clip (17.5 for 10 s), roughly 225 credits total.

Shared style suffix (keyframes): *Photorealistic cinematic film still, ARRI Alexa, shallow depth of field, realistic skin texture and hands, subtle film grain, documentary realism, muted teal-and-amber grade. No text, no logos.*

## Recurring characters (references)

| Ref | Prompt | Job |
|---|---|---|
| P1 patient | Malaysian Malay man, early 30s, short neat black hair, light stubble, warm brown skin, kind tired eyes, plain heather-grey t-shirt, terrace-house living room, louvred windows, morning light | `19f087ee-d2ca-4ff4-9ad3-fb51dfb216a6` |
| M1 mother | Malaysian Malay mother, late 50s, dusty-rose bawal tudung, simple floral baju kurung, reading glasses on a cord, terrace-house kitchen, warm tungsten light | `a4c17075-0555-4be5-b2d8-09f52aa505ee` |

## Shots

| Clip | Used at | Keyframe prompt (+ refs) | Motion prompt |
|---|---|---|---|
| v21 | 0.0 hook | Dark navy still life: one syringe with pale yellow liquid in teal light beside a towering pile of tablet blister strips and spilled pills | Slow dramatic push-in/orbit to the syringe; a few pills roll toward it |
| v01 | 3.0 | M1 alone at a kitchen table at night sorting tablets into a 7-day pill organizer, single pendant lamp (M1) | Push-in; she drops tablets in, pauses, sighs |
| v02 | 5.1, 148 split | Macro: older woman's hands (floral sleeve) pressing a white tablet from a blister into her palm, pill box, glass of water | Thumb presses tablet out, it drops into palm |
| v03 | 9.6, 148 split | Malaysian Indian staff nurse in a government clinic drawing pale-yellow oily liquid from a glass ampoule into a syringe, steel tray, yellow sharps bin | Draws liquid, holds up, taps for bubbles |
| v04 | 15.4 | P1 on sofa looking at a pill organizer; M1 rests a hand on his shoulder; louvred windows, afternoon (P1+M1) | M1 squeezes shoulder, he looks up, receptive |
| v07 | 20.1, 35.6 | P1 in navy work polo with lanyard hurrying out of a small apartment kitchen; zip-lock pharmacy pouch and white medicine box left on the counter (P1) | Checks watch, grabs keys, leaves; rack focus to the meds |
| v05 | 22.4, 141 | Late-afternoon Negeri Sembilan shophouse row with a small clinic (blank signboard); P1 and M1 walking from a Perodua (P1+M1) | Crane-down; people walk to entrance, palms sway |
| v06 | 25.0 | Over-the-shoulder from behind a doctor (face never shown) at a desk; P1 and M1 listening in a bright consultation room (P1+M1) | Push-in; doctor writes, P1 nods, M1 smiles with relief |
| v22 | 41.4, 60.0 | Macro: three unlabeled glass ampoules of golden oily liquid on a dark navy reflective surface | Slow slide; glints travel across the oil |
| v09 | 45.1, 48, 81.3 | Macro: glowing amber oil droplet suspended in water, luminous particles slowly diffusing outward, navy background (10 s) | Droplet steady, particles release continuously, slow orbit |
| v10 | 64.3 | Malaysian Chinese hospital pharmacist reviewing a medication chart at a dispensing counter | Dolly-in; reads, turns page, nods |
| v23 | 69.0 | P1 on a bench by an open louvred window with a cup of tea, contemplative, early morning (P1) | Sips tea, gazes out, steam rises |
| v24 | 72.3 | Close-up: nurse writing the next appointment date on a card; patient's hand waiting; desk calendar blurred | Finishes writing, slides card, patient takes it |
| v11 | 89.1 | Malaysian Chinese woman, mid-20s, light-blue blouse, crowded KL MRT carriage, commuters motion-blurred, quietly overwhelmed | Carriage sways; she closes her eyes, slow breath |
| v12 | 94.3 | Same woman (ref v11 keyframe) calm by an MRT window, golden light, KL skyline | Expression softens, shoulders relax, small smile |
| v25 | 99.2 | Macro: blue-gloved hand holding a syringe of golden oil against navy-teal, droplet at needle tip | Slow rotation; light glides along the oil |
| v13 | 102.8 | P1 working calmly in a small Malaysian printing shop arranging prints (P1) | Sorts, checks a sheet, small nod |
| v14 | 122.3 | P1 on an exam couch; doctor (face out of frame) flexing his elbow to check muscle tone (P1) | Elbow bent/straightened a few times |
| v15 | 127.2 | Close-up: P1 holding a glass mug of teh tarik at a mamak table (P1); top of frame cropped in the edit to hide signage | Slight fine tremor; tea ripples; steadies with both hands |
| v16 | 130.1, 134 | P1 restless on plastic chairs in a clinic waiting area (P1) | Knee bounces, shifts, half-stands (first 3.5 s used) |
| v17 | 145.1 | Malay staff nurse in white tudung taking P1's blood pressure, both smiling (P1) | Reads monitor, encourages; he smiles back |
| v18 | 152.4 | Family breakfast: P1, M1, younger sister in pastel tudung, small boy; nasi lemak and teh; morning sun (P1+M1) | Laughing; mother passes a plate |
| v19 | 154.5 | P1 jogging at Taman Tasik Titiwangsa at golden hour, KL Tower across the lake (P1) | Tracking shot alongside him |
| v20 | 157.0 | P1 and M1 on terrace-house porch steps at sunset, bougainvillea — *"one single photograph, not a collage"* (the first attempt came back tiled 3×) (P1+M1) | She takes his hand, quiet laugh, push-in |

Higgsfield job IDs for every keyframe and clip are in `deliverables/broll_jobs.json`.
