# Higgsfield credit report

**Cap:** 30 credits · **Spent:** 23.42 credits · **Unused reserve:** 6.58 credits · **Regenerations:** 0 · **Upscales on Higgsfield:** 0

Every price was preflighted with `get_cost` before submitting, and every charge below was confirmed against the account's Higgsfield transaction log (`transactions`), which lists 52 × Z Image (0.15), 1 × Soul Cinematic (0.12), 1 × Kling O1 Image (0.5) and Seedance 2.0 Mini charges of 4 + 2 + 2 + 2 + 2 + 3 for this session.

## Prices checked (actual, 1 Nov 2026)

| Model | Setting | Quoted cost |
|---|---|---|
| Seedance 1.5 Pro | 480p · 4 s | 2.4 |
| Seedance 1.5 Pro | 720p · 4 s | 4.8 |
| **Seedance 2.0 Mini** | **480p · 4 s / 6 s** | **2 / 3** (0.5 per second) |
| **Seedance 2.0 Mini** | **720p · 4 s** | **4** (1 per second) |
| Wan 3.0 / Grok Video 1.5 Lite | 480p | 5 |
| Hailuo (MiniMax) default | – | 6 |
| Kling 2.6 | default | 10 |
| Veo 3.1 Lite | default | 12 |
| **Z Image** | 9:16 still | **0.15** |
| Soul Cinematic | 1.5k still | 0.12 (displayed as 1) |
| Kling O1 Image | 1k still + reference | 0.5 |
| Nano Banana / Seedream 4.5 / FLUX.2 | still | 1 |

Seedance 2.0 Mini was cheaper per second than the Seedance 1.5 the brief listed first, and is the newer model, so it was used for all video. The brief's example prices (1 credit at 480p, 3 at 720p) were lower than the real prices, so the plan was rebuilt around them.

## Ledger (chronological)

| # | Item | Model | Resolution | Duration | Credits | Cumulative | Remaining of 30 |
|---|---|---|---|---|---|---|---|
| 1 | s01 keyframe (also the hook's start frame) | Z Image | 1152×2048 still | - | 0.15 | 0.15 | 29.85 |
| 2 | s01 look test (discarded: composition came out rotated) | Soul Cinematic 1.5k | 960×1696 still | - | 0.12 | 0.27 | 29.73 |
| 3 | s02–s13 keyframes (batch 1, 12 stills) | Z Image | 1152×2048 | - | 1.80 | 2.07 | 27.93 |
| 4 | s01 hook clip | Seedance 2.0 Mini (i2v) | 720p | 4 s | 4.00 | 6.07 | 23.93 |
| 5 | s14–s25 keyframes (batch 2, 12 stills) | Z Image | 1152×2048 | - | 1.80 | 7.87 | 22.13 |
| 6 | s26–s37 keyframes (batch 3, 12 stills) | Z Image | 1152×2048 | - | 1.80 | 9.67 | 20.33 |
| 7 | s38–s48 + s45b keyframes (batch 4, 12 stills) | Z Image | 1152×2048 | - | 1.80 | 11.47 | 18.53 |
| 8 | s49–s51 keyframes (batch 5, 3 stills) | Z Image | 1152×2048 | - | 0.45 | 11.92 | 18.08 |
| 9 | s16 doom-scrolling clip | Seedance 2.0 Mini (i2v) | 480p | 4 s | 2.00 | 13.92 | 16.08 |
| 10 | s27 finger-drumming clip | Seedance 2.0 Mini (i2v) | 480p | 4 s | 2.00 | 15.92 | 14.08 |
| 11 | s22 rushing-out clip | Seedance 2.0 Mini (i2v) | 480p | 4 s | 2.00 | 17.92 | 12.08 |
| 12 | s40 hyperfocus dolly clip | Seedance 2.0 Mini (i2v) | 480p | 4 s | 2.00 | 19.92 | 10.08 |
| 13 | s52 payoff keyframe (same man as the hook, reference image) | Kling O1 Image | 768×1360 | - | 0.50 | 20.42 | 9.58 |
| 14 | s52 payoff clip | Seedance 2.0 Mini (i2v) | 480p | 6 s | 3.00 | 23.42 | 6.58 |

**Total: 23.42 credits.** Before each submission the rule `cumulative + next cost ≤ 30` was checked; it was never close to binding.

## Strategy

- 3:58 of narration needed ~53 visual beats. At 0.5 credits per video-second, generating video for every scene would have cost about 120 credits, so the hybrid route was used:
  - every scene gets its own photoreal AI keyframe (Z Image, 0.15 each, 1152×2048, above delivery resolution);
  - 6 key beats are real AI video, image-to-video from those keyframes, so the style matches: the hook (720p), doom-scrolling, rushing out late, fidgeting, hyperfocus, and the hopeful payoff (same man as the hook, kept consistent with a Kling O1 reference image);
  - the other 47 plates are animated locally (camera moves, parallax motes, punch-ins, transitions) in HyperFrames: the disclosed last-resort substitution.
- Two video submissions were bounced by Higgsfield with a preset recommendation; nothing was charged, and they were resubmitted once with the preset declined.
- No subtitles, SFX, music, transitions or graphics were generated on Higgsfield.

## Job IDs

| Asset | Model | Job ID |
|---|---|---|
| img:s01 | z_image | `6b9b57b1-1ab7-4e73-99ec-9117bc0af423` |
| img:s02 | z_image | `f4937bee-e4bd-44e4-bb9e-dabd4b5154cf` |
| img:s03 | z_image | `04fabc11-0909-48da-a7b9-2cf7a23e782c` |
| img:s04 | z_image | `577fa329-3444-43f1-ae8f-fa4b820184bb` |
| img:s05 | z_image | `e9c09060-fd14-4ba1-a111-b06036676f73` |
| img:s06 | z_image | `c298b698-e646-4eb6-ad11-3d340b5e0432` |
| img:s07 | z_image | `9d4fc073-7bdb-45fd-b110-361f5472d954` |
| img:s08 | z_image | `3ee3c7b2-2af4-470a-abc7-c4229b0d10bf` |
| img:s09 | z_image | `58ffa774-19c4-4dc9-baf0-f01cdae3d9b3` |
| img:s10 | z_image | `41b29b95-fefd-4a66-8a1e-0f89291beb27` |
| img:s11 | z_image | `df5bc54f-1bdb-4e54-a008-728f28aeb9df` |
| img:s12 | z_image | `f84782ad-f1be-4c94-995e-1c0dcb3b7a14` |
| img:s13 | z_image | `5f17703c-c0f6-4cfc-8dd5-e0dc6d045083` |
| img:s14 | z_image | `fb8a908a-c6b6-4b1e-b451-4451c901238b` |
| img:s15 | z_image | `8523d8ad-08d3-494f-bab6-7124780b8add` |
| img:s16 | z_image | `94102845-055c-4f7e-82f9-a8b4d3ca2887` |
| img:s17 | z_image | `e5e1b3a0-725e-4b19-9c07-9e2f74b8ddd4` |
| img:s18 | z_image | `bf9653ab-0b27-420c-8411-808806ef80d8` |
| img:s19 | z_image | `135a040d-688b-46d2-b762-4be645b0f422` |
| img:s20 | z_image | `a9768207-5aa3-4b85-b40c-ddb69f93a570` |
| img:s21 | z_image | `a6c64408-cb13-494a-bddc-064b75a2a959` |
| img:s22 | z_image | `af2408a2-1d5a-4792-abe7-61e3ede4bfc8` |
| img:s23 | z_image | `e24a7cae-23b9-49d9-8291-537cd05f5a45` |
| img:s24 | z_image | `72516b2f-6475-42d1-9aac-7651c0b71f14` |
| img:s25 | z_image | `226ea22e-7e5b-486d-8016-91193c161e8d` |
| img:s26 | z_image | `60d80aa7-ba1c-46ee-8734-4bb66fdabf82` |
| img:s27 | z_image | `9b4a23cf-d008-4378-8842-9f180ff7e2d6` |
| img:s28 | z_image | `56248302-ee37-4df6-9d0c-5fe90d69f145` |
| img:s29 | z_image | `948da0bb-4cc3-477a-aa18-cea824b55927` |
| img:s30 | z_image | `607e2430-eeed-4e2d-9f9b-c774afee32ad` |
| img:s31 | z_image | `2ed89729-e199-4f25-8789-9271adbed752` |
| img:s32 | z_image | `3428e4a5-a4f8-425c-b6b7-7897150e3ccc` |
| img:s33 | z_image | `004a35bf-13a8-40af-bd8a-bacb3f989a93` |
| img:s34 | z_image | `f713d3db-3baa-4081-b7c1-d2798505e2b2` |
| img:s35 | z_image | `9dd485ba-17e5-4a01-bab6-e8ae8e8e4ee6` |
| img:s36 | z_image | `f0b52a9d-445a-47e6-adad-c87d2b64a3aa` |
| img:s37 | z_image | `fc8957b7-7d62-4245-b973-5c5b3dd965e9` |
| img:s38 | z_image | `19b2f705-ff60-4e31-843a-82657bfa3cb7` |
| img:s39 | z_image | `a7bd9b98-40d9-4b7d-b4f9-c6ed80847abf` |
| img:s40 | z_image | `5291d7fb-bf53-4597-ab12-bd4610d44e20` |
| img:s41 | z_image | `4390f041-808f-4a26-aca6-83d77aadca1b` |
| img:s42 | z_image | `1cbc0766-c93f-429b-9ac6-1e6c36cebb65` |
| img:s43 | z_image | `1f112585-73ef-4c68-81e6-79bb1b1b7c58` |
| img:s44 | z_image | `3e01cd61-19e6-4dbe-a7b8-06226631869c` |
| img:s45 | z_image | `5a3da0ec-10a8-4d96-9403-795b803e1718` |
| img:s45b | z_image | `8d18495a-07cd-4aaf-bef2-2486f5c09774` |
| img:s46 | z_image | `92cc0972-c8d7-4df2-8b8d-5301a451a750` |
| img:s47 | z_image | `62014c2a-c648-4ed8-96c6-c39bd62f8683` |
| img:s48 | z_image | `7044eb10-4e56-4f61-ab0b-5af3651f846b` |
| img:s49 | z_image | `2ec2852f-ed46-477c-8c31-a398a44bad35` |
| img:s50 | z_image | `0a634151-9572-456e-b85c-6bfe4c9392e5` |
| img:s51 | z_image | `6c0fa00c-559f-4ed6-9c4d-379b85516ddf` |
| img:s52 | kling_omni_image | `3deeaeba-8432-4e05-956a-ca431368c218` |
| vid:s01 | seedance_2_0_mini | `93dd99f4-6e8c-4d90-a371-dc2e01924e72` |
| vid:s16 | seedance_2_0_mini | `6e9e2ae6-aea1-48ad-9b87-bc3b8c26d9b1` |
| vid:s22 | seedance_2_0_mini | `fde459f1-2b51-48e1-8463-2fa4414b08ff` |
| vid:s27 | seedance_2_0_mini | `06c46e81-7a90-453f-85ea-dafdde29805b` |
| vid:s40 | seedance_2_0_mini | `9a026557-7b18-44c8-98e3-64780e1b003e` |
| vid:s52 | seedance_2_0_mini | `17195f8b-b4e0-4626-839e-c8947ea0b308` |
| (discarded) Soul Cinematic look test | soul_cinematic | `d6a4b880-65a9-407b-ae2b-2549113419db` |
