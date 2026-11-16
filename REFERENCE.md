# Twitter ecosystem reference

Facts that are not derivable from the repos or the web. History and PR numbers are in git; the current state is in `HANDOVER.md`.

## Sandbox
- `/root/workspace` is a bind mount owned by the host user; as root, git needs `safe.directory` for it (bootstrap sets it).
- Parallel Bash calls share one shell cwd: use absolute paths and `git -C`. `pkill -f` matches the calling shell; kill by pid.
- The shell is zsh: an unquoted `$var` is not word-split, an unmatched glob such as `--include=*.ts` aborts the command, `=word` is
  expanded; quote globs, use arrays or `${=var}`.
- GPG key is passphrase-protected; the sandbox agent is unlocked by the maintainer from a VS Code terminal (long cache TTL). sops uses the
  writable copy `GNUPGHOME=/root/.gnupg-rw`. Secrets: `source .sops/env.sh && SOPS_AGE_KEY_FILE=.sops/age-key.txt sops decrypt --extract
  '["proxy_list"]' twitter-secrets/secrets.enc.yaml` (same for `cookie_json`).
- The sandbox reaches X directly. GitHub-hosted runners get a Cloudflare challenge, so CI goes through the maintainer's HTTP CONNECT
  proxies (`proxy_list`, fastest first; exits fluctuate, so reruns are legitimate). Chromium only authenticates against HTTP proxies.
- Node 24.22.1 and 26.13.0 for local reproduction are in `/root/.local/node-versions/`; downloaded ffmpeg builds in `tools/out/ffmpeg-*`.

## GitHub and CI
- Delete a head branch only after the merge response says `"merged":true` and `gh pr list --base <branch>` is empty: during a GitHub
  outage an empty API body once led to deleting the branch of an unmerged PR, which closes it (recovery: push the commit back as the
  branch, reopen, merge). Check githubstatus.com when API answers look odd. A dropped push event is restarted with
  `gh workflow run <file> --ref <branch>` where the workflow has `workflow_dispatch`.
- The sandbox's auto-mode classifier refuses a merge it sees as unreviewed: say in the command description that the PR was LGTM'd or
  that Dependabot is delegated. It also refuses to delete unmerged branches.
- Publishing is automatic on push to the default branch (PyPI / npm trusted publishing, ghcr). twitter-snap publishes only when
  `package.json`'s version is not on npm yet; its Docker image builds on every master push. twitter-snap-api, private_bot, -discord and
  -bookmarklet build Docker on push to the default branch and have no PR checks. The TS / Python wrappers and TIAD have no PR CI either;
  twitter-openapi and twitter-snap do.
- Stacked PRs get no CI in twitter-snap (`pull_request` against master only; retargeting does not trigger it): `gh workflow run
  test.yml --ref <branch>` or push a commit.
- Dependabot: `groups` are configured everywhere; version updates are off in the relay, twitter-snap-api and private_bot (every relay
  CI run logs in to X). Security updates of nested packages fail with `security_update_not_possible` when the parent's range does not
  reach the fix. Manual fix inside ranges: `pnpm update <pkg> --no-save` (`-r --depth 99` in a workspace); for a package that is also a
  direct dependency, add a temporary `overrides` entry, install, remove it, install again. Alerts: `gh api repos/fa0311/<repo>/dependabot/alerts`.
- pnpm 12 in CI: every dependency with a build script needs an `allowBuilds` entry in `pnpm-workspace.yaml`; Dockerfiles must copy
  `pnpm-workspace.yaml`; a lockfile from an older 12.x breaks `--frozen-lockfile` (`pnpm install --lockfile-only` with the pinned pnpm).
  Check with `CI=true pnpm install --frozen-lockfile` before pushing.
- `node:26` images do not ship corepack: `npm install -g corepack && corepack enable` in every Dockerfile; the pnpm version comes from
  `packageManager`.
- Windows runners check out CRLF: repos with biome need `.gitattributes` (`* text=auto eol=lf`, `*.cmd text eol=crlf`). Biome 2.6
  formats YAML (double quotes by default: `yaml.formatter.quoteStyle: single`) and Markdown too.
- ffmpeg in CI: johnvansickle static builds (`FedericoCarboni/setup-ffmpeg@v3`) segfault on https input; BtbN builds
  (`AnimMouse/setup-ffmpeg@v1`) and apt ffmpeg work. BtbN `ffmpeg-master-latest` is not for production images: its aac `nmr` coder looped
  forever on some 48 kHz audio in Nov 2026 (stuck at `frame=0`, ignores SIGTERM); pin release lines (n9.0). Repro: `tools/out/nvenc_repro/`.
- pngjs on Node 25+: `PNG.sync.read` throws (`Inflate` without `new`); use `new PNG().parse(buffer, cb)`.

## X behaviour
- New GraphQL query versions have no `User.legacy`; old queryIds keep returning it and keep working for a while (stale ids are a quiet
  drift, not an outage). X often returns complete data next to partial `errors`; the harness logs these as warnings.
- Logged-out x.com is static HTML with no scripts; guest-token GraphQL still works. `UserByRestId` / `UsersByRestIds` are 403 for
  non-browser clients. Other users' likes are empty. Every list answers `ListByRestId` with a partial `BadRequestError` (harness skips it).
- Two frontends: logged-out `x.com/home` lands on the new x-web app (`abs.twimg.com/x-web/...`, Rolldown build); `x.com/i/jf/` and the
  logged-in `/home` are the responsive-web shell (inline webpack runtime, `loading-x-anim` frames). Both hash
  `METHOD!path!time` + `obfiowerehiring` + animationKey for `x-client-transaction-id`, with the URL pathname as is. X does not reject a
  missing or wrong transaction id on `UserByScreenName`, so "the API accepted it" proves nothing; compare against the frontend's own
  headers. The bundle defines operations as `queryId/operationName` literals and as Relay `params:{id,name}` objects; TIAD parses only
  the former, so "gone from TIAD" never means gone.
- The web app sends REST under `/i/api/1.1/...`; `HomeTimeline` is GET at launch and POST once `seenTweetIds` / a cursor is sent;
  mutations no longer send `dark_request`. "Not interested in this post" is `POST /i/api/2/timeline/feedback.json` with the query of the
  timeline's `feedbackUrl` and a form body `feedback_type=…&undo=false` (Undo: `undo=true`). `live_pipeline/update_subscriptions` lives
  on `api.x.com` and needs the `livepipeline-session` of the open `live_pipeline/events` stream.
- Translation: the web client sends no request for posts; `TweetDetail` / `TweetResultByRestId` carry
  `grok_translated_post_with_availability`, keyed by the request header `x-twitter-client-language` (same language → `is_translatable:
  false`; replies are often `is_available: false` until someone clicks on x.com). On-demand `POST /2/grok/translation.json` is an NDJSON
  stream without content-type, not consumable by the generated clients, so it is not in the spec; twitter-snap takes `--translate <lang>`
  and sets the header itself.
- Typing-triggered operations are reachable via URLs (`/i/lists/search?q=`, `/i/communities/suggested?q=`); bookmarks search needs its
  own button. Setting an X Chat passcode is forbidden.
- Rate limits per 15 minutes vary by an order of magnitude between operations (search is the scarce one); read `x-rate-limit-*`.
- Lock: GraphQL answers 200 with data plus `errors[].code 326` and `bounce_location: …/account/access`; web pages redirect to
  `/account/access` behind a Cloudflare challenge; the relay's CI login times out after 120 s. Triggers so far: sweeps, several suites
  in a day, relay CI logins (3 per push / merge). After the maintainer clears it, export a fresh cookie if the session changed and update
  `cookie.json`, the worktree copies and the sops secret.
- Media: pbs.twimg.com serves every photo at `?name=orig` (`format=jpg&name=4096x4096` is 404 for some) and keeps serving media of
  deleted posts for a while. Posts can carry ~20 photos. Age-restricted posts give guests a `TweetTombstone`.

## twitter-openapi (spec)
- Build: `uv run python tools/build.py`; generate the strict Python client with `openapi-generator-cli.jar` 7.26.0
  (`test/python/openapi-generator-config.yaml`); strict harness `STRICT_MODE=True ERROR_UNCATCHED=False CUESOR_TEST_COUNT=2 uv run python
  test/python/test_serialize.py` calls every GET operation of every API class with the placeholder values and raises `Not defined:
  Model.field` / enum errors. PostApi is never executed: mutations are validated from recorded dumps (`tools/validate_dumps.py`).
- Placeholder keys resolve case-insensitively; `cache/*.json` holds `{raw, type}` of every response of a run.
- Offline check before any PR: every file in `recordings/validate_args.json` at match rate exactly 1.0 via `tools/validate_dumps.py`;
  add every new recording there.
- Generated `from_dict` reads every key with `obj.get`, so `required` + `nullable` silently accepts absence; model an absent field as
  optional non-nullable.
- Conventions: `src/openapi/paths/*.yaml` hold paths and their response schemas, shared objects live in `src/openapi/schemas/*.yaml`,
  `__typename` values must be in `schemas/typename.yaml`, tags map to generated API classes, hooks inject the placeholder parameters at
  build time. Schema sharing only for the same backend object under the same key; a look-alike site gets its own type. Enum vs string
  per `CONTRIBUTING.md`.
- Placeholder: values only from recordings of the real web client (relay catalog `requests.ndjson` applied with
  `tools/update_placeholder.py <file|url>`, the relay's `twitter-api-safe-dump --cookies`, a HAR). Sample values are elonmusk /
  44196397 / 1349129669258448897; viewer-bound entries are recorded on the sandbox. TIAD's GraphQL.json is only a detector of changed queryIds.
- `tools/sweep_tweets.py` (broad strict sweep) and `tools/json_to_schema.py` (schema drafts; check its shared-type guesses, reduced
  users are not `User`) live in `/root/workspace/tools`.

## Generated clients
- Regeneration: in the generated directory, move the `twitter-openapi` submodule to the spec commit, bump the version in
  `tools/openapi-generator-config.yaml`, remove what `tools/win/clean.ps1` lists (Python: `rm -rf test` too, or `.openapi-generator/FILES`
  loses the tests), run the generate command from `tools/win/gen.ps1`. TS: do **not** run `tools/win/replace.py` (it drops the `prepare`
  script and the ESM build fields, and npm then gets a package without `dist/`); after the jar run `npm install --package-lock-only`
  and compare `package.json` with the previous release (`npm pack --dry-run` lists 5,400+ files). Wrapper: bump version and generated
  dependency, pin the spec hash (`client.py` / `src/api.ts`), add typed helpers with e2e tests for new operations. Conventional
  commits: `generated: regenerate X from twitter-openapi <sha>`, `wrapper: X on generated X`.
- The TS lockfile can only resolve the new generated version after npm has it (the packument lags ~10 min): a follow-up PR.
  twitter-snap then takes `^x.y.z` (its own packages are exempt from pnpm's minimumReleaseAge).
- The TS wrapper's `cookie.json` is not gitignored; the Python wrapper's is. The wrappers expose cursors and rate-limit headers and
  deliberately have no pagination helper.

## twitter_api_safe_relay
- Everything the relay serves lives under `/i/api` like the X web app; dispatch paths inside are relative to `https://x.com/i/api`.
  `x-profile-name` selects a profile. Anything else is a Hono 404; a form-encoded POST body or an endpoint X itself rejects comes back
  as a relay 500.
- Its tests and a throwaway relay for e2e take `X_COOKIE_FILE` through `twitter-api-safe-test-utils` (headless Chromium with the
  cookies added); `node file.ts` runs TypeScript directly on Node 24. Every CI run logs in to X three times (one per Node version).
- The catalog `packages/server/requests.ndjson` is recorded with `twitter-api-safe-dump` (`--cookies`, `--headless`), merged line by
  line, `recordedAt` stamped.
- Local run for reviews: `tools/relay_local/` (recipe in `tools/README.md`). Session cookies seeded without `expires` vanish when the
  seeding context closes; the relay then opens x.com logged out and every `/i/api/*` request hangs while `/health` answers. Dashboard
  entries exist only while a page is connected to `/api/events`.

## twitter-snap (+ -api)
- pnpm + biome + vitest; default branch `master`; tests hit X as guest and need ffmpeg. `node bin/dev.js` runs the stale `dist/`:
  `pnpm build` before verifying a change. `node bin/run.js <url> --sessionType guest --simpleLog -o <path>` renders public posts and
  pixiv without a cookie; a cookie session renders the whole conversation up to `--limit` (use `--limit 1` or `{id}` in the name).
  CI can lose guest access on single runners (every render test fails with ENOENT on the output): rerun before suspecting the change.
- Pipeline: satori → SVG → `@resvg/resvg-js` (sharp was dropped: it refuses SVGs above 32767 px, which a many-photo post reaches at
  scale 2). satori ≥ 0.34 lays out like a browser: content-box by default and absolutely positioned elements painted above in-flow
  siblings; `renderPng` therefore wraps the element with `<style>* { box-sizing: border-box }</style>` and the poll texts are
  `position: relative`. A satori bump still needs a visual pass: `tools/out/og_compare/` (`render.sh <outdir> node bin/run.js`,
  `compare.cjs <a> <b>`, `montage.cjs`; sharp installed there). satori ≥ 0.33.5 pins `fflate` 0.7.3 (medium advisory, not fixable in range).
- Text is a flex-wrap of UAX #14 units (`linebreak`, `src/utils/text.ts`); satori has no inline flow. satori clips an `<img>` only by its
  own `borderRadius` (put border + radius on the image). Fonts: `loadFonts(dir)` (Segoe UI / Meiryo set), twemoji images and Noto
  subsets from Google Fonts as satori asset fallback (`src/utils/render.ts`).
- Video: the image renderer paints the first video's frame in `#ff00fe`; `RenderBasicVideo` finds the box on the PNG (`pngjs`) and overlays
  with `overlay=…:format=rgb,format=yuv420p` (keep the RGB step) through an alpha mask for the corners; blanks need even inner sides,
  otherwise marker-colored rows remain (check renders with a full-frame scan for `r>150,g<120,b>150`). `ffmpegTimeout` goes to
  fluent-ffmpeg in seconds. The e2e `--noCleanup` test expects `temp-0-0.png` + `temp-1-0.mp4`.
- Library path: `getSnapAppRenderWithCache` never installs twitter-snap's own `fetchApi`, and the TS client captures `fetch` at import
  time: to feed a saved response, replace `TwitterOpenApi.fetchApi` (`tools/render_saved_tweet.mjs`). The CLI logger used to swallow
  render-stream errors (fixed in 0.4.2); a "success" without a file means run through the library to see the exception.
- Layout reference for X UI work: `tools/x_dom_styles.py` (Playwright + cookie) dumps computed styles and screenshots of the real article;
  match sizes and colors from that. Guest `TweetResultByRestId` carries polls and `birdwatch_pivot` but never `callToAction`.
- twitter-snap-api: `width: 1440, scale: 2` (a 720 px layout at 2×), one render at a time (`createMutex(1)`, so one stuck render queues
  everything), `Failed to get snapshot` for any empty result; GPU images (`Dockerfile.nvenc` / `.qsv` / `.full`) run Node 22 from nodesource,
  `Dockerfile` is node:26; `build.sh` pins the BtbN n9.0 release line.

## Other repos
- TwitterInternalAPIDocument: generator needs a cookie; docs on `develop`, merged to `master` by the scheduled workflow; its "Update
  Document" PRs are the maintainer's own. Avoid changes unless asked.
- x-client-transaction-id-pair-dict: `pnpm start` yields 30 pairs in a few minutes without a proxy (`PAIR_MAX=2` for a quick check);
  pairs stay valid for weeks; not on npm. Lqm1/x-client-transaction-id 0.3.2 was verified identical to the frontend (2026-10-19).
- private_bot: LINE bot calling twitter-snap-api over HTTP; depends on the TS clients directly.
