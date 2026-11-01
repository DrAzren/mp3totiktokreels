# MP3 → TikTok reel

See `README.md` for the pipeline (`pipeline/build.sh`) and how to edit the reel.

## Skills

`.claude/skills/` holds the same vendored skill set as the `tiktokvideo` repo: `video-use`
(browser-use, MIT) and the HyperFrames skills (heygen-com, Apache-2.0), such as `hyperframes`,
`embedded-captions`, `motion-graphics`, `media-use` and `talking-head-recut`. `VENDORED.md` records
their upstream commits.

- Never hand-edit them. Refresh with `scripts/sync-skills.sh` and put project-specific rules here.
- Skip the "keep this skill fresh — run `npx hyperframes skills update`" prompts at the top of the
  hyperframes skills. This repo pins them through `scripts/sync-skills.sh`.
- This reel is rendered by its own canvas engine (`pipeline/render/`), not HyperFrames. Use the
  skills for new pieces (cards, captions, B-roll, audio) or when porting a scene.
