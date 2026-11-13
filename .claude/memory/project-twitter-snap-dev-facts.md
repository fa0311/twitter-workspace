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
- Video overlay (since the X reference PR): the image renderer paints the first video's frame in `#ff00fe`; `RenderBasicVideo` finds that box on the PNG (`pngjs`) and overlays there with `overlay=x:y:format=rgb,format=yuv420p`. Overlaying in 4:2:0 leaves 1-2 magenta-tinted rows around the video (chroma of the marker survives), so keep the RGB step. The e2e `--noCleanup` test expects `temp-0-0.png` + `temp-1-0.mp4`, unchanged.
- x.com shows mixed media (photos + videos) and several videos in one carousel of 453x385 frames with duration pills ("1:14", remaining time while playing) and a 24px mute circle; our image output shows the full duration.
- satori clips an `<img>` only by its own `borderRadius`; a rounded parent with `overflow: hidden` does not clip children at the corners (square corners poke out) and child borders are not clipped either. Put border + radius on the image itself. The video overlay gets the same corners through an alpha mask (`alphaextract` + `alphamerge=shortest=1`) rendered with `ImageResponse` at the radius read off the marker's shape.
- Video blank must have even inner sides (the video is scaled to even sides for yuv420p); an odd blank leaves marker-colored rows under the video (0.2.0 defect, fixed in 0.2.1). Check video renders with a full-frame scan for `r>150,g<120,b>150` pixels, not only the corners.
- Layout reference for X UI work: `tools/x_dom_styles.py` (Playwright + account cookie) dumps computed styles and screenshots of the real article; match sizes/colors from that, not from memory (2026-10-31: note box 16px radius, header band, 14px bold title, 13px footer outside the box).

- A status URL with a cookie session renders the conversation (TweetDetail) up to `--limit` (default 20), not just the tweet of the URL; a fixed `-o name.png` is overwritten by each entry and ends with a related post. For one tweet use `--limit 1` or keep `{id}` in the output name (2026-10-31).

- satori versions (2026-11-07): twitter-snap's layouts were tuned on satori 0.25.0 (bundled by `@vercel/og` 0.11.1). satori 0.33.5 renders the sample set pixel-equal within 0.3% (subpixel text only); satori 0.63.x changes text measurement and flex sizing (poll bars overflow, labels disappear, different line wraps), so a satori bump needs a visual pass. `@vercel/og` 1.x does not load on Node ("Dynamic require of fs"), and every satori >= 0.33.5 pins `fflate` 0.7.3 (a medium advisory, unzipSync only). Compare sets: `tools/out/og_compare/` (`render.sh`, `compare.cjs`, `montage.cjs`).

**Why:** the dev entry point fooled a first verification; guest rendering keeps the account-lock budget untouched.
**How to apply:** build, then render with bin/run.js; compare before/after PNGs with `cmp`. See [[project-twitter-ecosystem-standing-tasks]].

- 2026-11-13: sharp refuses SVGs taller than 32767px (`pipeline.cc`, no density/resize workaround); a 19-photo post at scale 2 hits it because media stacks at full width. twitter-snap #111 switched `renderPng` to `@resvg/resvg-js` (renders 100000px tall; same renderer family as the old @vercel/og), pixel diffs vs sharp are glyph-edge AA only (0.4–3.9 %). Posts can carry up to ~20 photos now.
- The CLI's Logger dropped errors from the render stream and under `--simpleLog` (fixed in #111); when a render "succeeds" with no file, run through the library API to see the exception.
- Compare tooling: `tools/out/og_compare/` (`render.sh <outdir> node bin/run.js`, `compare.cjs <a> <b>`; sharp installed locally there). `branch033full` = satori 0.33.5 + sharp (0.4.0/0.4.1 output), `baseline` = @vercel/og, `resvg` = #111.

