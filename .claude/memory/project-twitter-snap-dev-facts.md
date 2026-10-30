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

**Why:** the dev entry point fooled a first verification; guest rendering keeps the account-lock budget untouched.
**How to apply:** build, then render with bin/run.js; compare before/after PNGs with `cmp`. See [[project-twitter-ecosystem-standing-tasks]].
