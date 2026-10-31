---
name: project-twitter-snap-dev-facts
description: "twitter-snap sandbox facts — default branch master, bin/dev.js loads dist (build first), guest session renders need no cookie, text layout is flex-wrap of UAX#14 units"
metadata:
  node_type: memory
  type: project
  originSessionId: 0650167e-5ffa-4364-b61a-870599f5819c
  modified: 2026-10-30T16:17:08.747Z
---

twitter-snap (fa0311/twitter-snap) facts learned 2026-10-30:

- Default branch is `master` (PRs target master), unlike the spec/client repos.
- `node bin/dev.js` (oclif development mode) does **not** load `src/`: the oclif target is `./dist/commands/index.js` and tsconfig has no rootDir/outDir mapping, so it silently runs the stale `dist/`. Always `pnpm build` before rendering to verify a change (a byte-identical output image is the tell).
- `node bin/run.js <url> --sessionType="guest" --simpleLog -o=<path>` renders public tweets and pixiv artworks without any cookie, so renderer verification costs no sandbox-account calls. `--theme RenderMakeItAQuote` for the quote card.
- Tweet text is laid out as a flex-wrap `<p>` of `<span display:flex>` units (satori has no inline flow); since PR fix/line-break the units come from `linebreak` (UAX #14, same lib satori uses) via `src/utils/text.ts`. A `height: 1em` spacer is applied only to blank-line units.
- Old CI tests (`test/commands/*.test.ts`) run live with guest session; CI `test.yml` runs build/lint/typecheck/test on pull_request.
- Guest `TweetResultByRestId` carries poll cards and `birdwatch_pivot` but never `callToAction` (rating row); a cookie session (`--sessionType=file --cookiesFile=/root/workspace/cookie.json`) renders the whole TweetDetail conversation, so a fixed `-o` name needs `--limit=1`.
- x.com layout facts measured 2026-10-31 (desktop post page, 598px article + 1px column borders, 16px side padding): text 17/24, names 15/20, sub text 13-15; media radius 16 with a 1px #cfd9de|#2f3336 border; 2+ photos are a carousel (fit to width when ≥240px tall, else height 0.68W, each ≤0.8W, cropped, 8px radius, 1px #eff3f4|#2f3336 frames, 4px gaps); quote box radius 16, padding 12, 24px avatar, media flush; action bar 48px + 1px top border #eff3f4|#2f3336, icons 23px, counts 13/16 (repost count = retweet + quote; numbers truncated: 12K, 366.6M); Community Note box radius 16 with a header band. Guests get no `callToAction`; a bare link gives a `card` with only `restId` (no legacy); broadcast card thumbnails are webp (request `format=jpg`); `@vercel/og` cannot decode webp.
- Layout reference for X UI work: `tools/x_dom_styles.py` (Playwright + account cookie) dumps computed styles and screenshots of the real article; match sizes/colors from that, not from memory (2026-10-31: note box 16px radius, header band, 14px bold title, 13px footer outside the box).

**Why:** the dev entry point fooled a first verification; guest rendering keeps the account-lock budget untouched.
**How to apply:** build, then render with bin/run.js; compare before/after PNGs with `cmp`. See [[project-twitter-ecosystem-standing-tasks]].
