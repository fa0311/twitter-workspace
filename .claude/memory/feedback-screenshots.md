---
name: feedback-screenshots
description: Where to put screenshots / sample renders for the maintainer (./screenshot/{date}/ in the workspace) and that sample tweets must be pleasant to look at
metadata:
  type: feedback
---

Screenshots and before / after renders the maintainer should look at go to `/root/workspace/screenshot/{YYYY-MM-DD}/` (asked 2026-10-31: "screenshotは./screenshot/{date}/ とかに置いて欲しい"), not under `tools/out/` or the scratchpad. Sample tweets chosen for renders must be pleasant to look at ("食事中でも見れる画像にして", after a Community Note sample showed a cockroach): no insects, gore, food-safety horror or other unappetising imagery; prefer neutral or pleasant subjects (space, animals people like, tech, sports).

**Why:** the maintainer opens the images from VS Code at any time, including over meals, and a fixed dated folder is easy to find.

Layout since 2026-10-31 (after "わかりにくい" about a flat folder of 38 files): `screenshot/{date}/<theme>/<sample>.png` with subfolders such as `x-reference/`, `default/`, `x.com/` (the real page), the same sample names in each, and mp4 samples next to their `-frame.png`.

README sample images of twitter-snap use Elon Musk's posts and official / brand accounts such as SpaceX only, no private individuals (2026-10-31: "elon系以外のツイートは載せないで" → "公式のやつは良い"), and no Community Note sample; the set is the 🍊 post 1770222178279252062, the poll 1604617643973124097, the photo post 1349129669258448897 and SpaceX's quote 2112637394654822514, rendered with `TZ=Asia/Tokyo` like the originals.

**Never involve private individuals** (2026-10-31: "とにかく、一般人は巻き込まない"): no private person's post in anything public — README images, PR descriptions, issue replies, test URLs, docs. Only the maintainer-approved set: Elon Musk and official / brand accounts (SpaceX, NASA, publications). Private posts may be used for local checks in the sandbox only, and are not named in public text.

**How to apply:** render samples into `screenshot/{date}/`, name them `<feature>-before.png` / `<feature>-after.png` (`-dark` for the dark theme), check the media of a candidate tweet before using it, and point to the folder in the chat. Related: [[feedback-design-preferences-2026-10]], [[project-twitter-snap-dev-facts]].
