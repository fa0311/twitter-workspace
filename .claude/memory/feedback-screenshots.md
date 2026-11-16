---
name: feedback-screenshots
description: "Where renders for the maintainer go (screenshot/{date}/<theme>/<sample>.png), which posts may appear in public material, and that samples must be pleasant to look at"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d250dea8-b7d2-47de-8276-a31f9ac33735
  modified: 2026-11-16T04:46:30.777Z
---

- Renders the maintainer should look at go to `/root/workspace/screenshot/{YYYY-MM-DD}/`, grouped as `<theme>/<sample>.png`
  (`x-reference/`, `default/`, `x.com/` for the real page; `-before` / `-after`, `-dark`; mp4 next to its `-frame.png`). Point to the
  folder in the chat. ("screenshotは./screenshot/{date}/ とかに置いて欲しい"; a flat folder of 38 files was "わかりにくい").
- Samples must be pleasant ("食事中でも見れる画像にして", after a cockroach in a Community Note sample): space, animals, tech, sports; check a
  candidate's media first.
- Public material (README images, PR descriptions, issue replies, test URLs) uses only Elon Musk and official / brand accounts
  ("とにかく、一般人は巻き込まない"). README set: 🍊 post 1770222178279252062, poll 1604617643973124097, photo 1349129669258448897, SpaceX quote
  2112637394654822514, rendered with `TZ=Asia/Tokyo`; no Community Note sample. Private posts only for local checks, never named in public text.

**Why:** the maintainer opens images at any time, including over meals, and private people must not end up in the project's material.
Related: [[feedback-design-preferences]].
