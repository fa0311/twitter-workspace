# Twitter ecosystem reference

Facts that are not derivable from the repos or the web. History and PR numbers are in git; the current state is in `HANDOVER.md`.

## Sandbox
- Everything runs as `kasm-user`, who owns the workspace; `sudo` needs no password. What survives a container recreate is in
  `HANDOVER.md`.
- A `cd` in one Bash call moves the working directory of the following ones: use absolute paths and `git -C`. `pkill -f` matches
  the calling shell; kill by pid.
- The shell is zsh: an unquoted `$var` is not word-split, an unmatched glob such as `--include=*.ts` aborts the command, `=word` is
  expanded; quote globs, use arrays or `${=var}`.
- The GPG key is passphrase-protected and the agent never has it cached: plain `gpg` hangs waiting for the passphrase, with
  `--batch` too. `/usr/local/bin/git-gpg` is `gpg --batch --pinentry-mode loopback` with the passphrase from
  `GPG_PASSPHRASE`; git calls it by itself, and it takes any other gpg arguments (`git-gpg -bsau <key>`, `git-gpg -d <file>`).
- twitter-secrets is encrypted to that PGP key and to the CI age key, so no age key is needed here: `SOPS_GPG_EXEC=/usr/local/bin/git-gpg
  sops decrypt --extract '["proxy_list"]' twitter-secrets/secrets.enc.yaml` (same for `cookie_json`). The CI age key, for a repository
  that needs `SOPS_AGE_KEY`, is `git-gpg -d twitter-secrets/keys-ci-age.txt.gpg`.
- The sandbox reaches X directly. GitHub-hosted runners get a Cloudflare challenge, so CI goes through the maintainer's HTTP CONNECT
  proxies (`proxy_list`, fastest first; exits fluctuate, so reruns are legitimate). Chromium only authenticates against HTTP proxies.
- Only the image's Node 26 is installed; another version for local reproduction is the nodejs.org tarball unpacked under
  `~/.local/node-versions/`. Playwright's Chromium download works on Ubuntu 26.04 without `--with-deps`. `EACCES` from npm means
  `~/.npm` is owned by root again (bootstrap hands it back). apt needs `sudo apt-get update` first: the image ships no package lists.

## GitHub and CI
- Delete a head branch only after the merge response says `"merged":true` and `gh pr list --base <branch>` is empty: during a GitHub
  outage an empty API body once led to deleting the branch of an unmerged PR, which closes it (recovery: push the commit back as the
  branch, reopen, merge). Check githubstatus.com when API answers look odd. A dropped push event is restarted with
  `gh workflow run <file> --ref <branch>` where the workflow has `workflow_dispatch`.
- `gh pr merge --delete-branch` closes every open PR based on the deleted branch, and the base of a closed PR cannot be changed.
  Retarget the children first (`gh api -X PATCH repos/<r>/pulls/<n> -f base=<new>`) and merge bottom-up into the default branch;
  recovery is `git push origin <sha>:refs/heads/<name>`, `gh pr reopen`, then the PATCH. A grouped Dependabot PR that fails is
  superseded by an own PR with the same bumps.
- The token cannot transfer issues: open a copy in the target repo and close the original with "Moved to …". Workflows that record
  from X or run as guest are `workflow_dispatch` only.
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
  forever on some 48 kHz audio in Nov 2026 (stuck at `frame=0`, ignores SIGTERM); pin release lines (n9.0).
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
  in a day, relay CI logins (3 per push / merge; six logins within an hour and about twelve in a morning were each enough). After the maintainer clears it and the session changed, the fresh export goes into
  the sops secret (`cookie_json`, recipe in twitter-secrets' README); delete the workspace's `cookie.json` and rerun bootstrap.
- Media: pbs.twimg.com serves every photo at `?name=orig` (`format=jpg&name=4096x4096` is 404 for some) and keeps serving media of
  deleted posts for a while. Posts can carry ~20 photos. Age-restricted posts give guests a `TweetTombstone`.

## twitter-openapi (spec)
- Build: `uv run python tools/build.py`; generate the strict Python client with `openapi-generator-cli.jar` 7.26.0
  (`java -jar openapi-generator-cli.jar generate -c test/python/openapi-generator-config.yaml -g python`, then `uv pip install
  ./python_generated`; the jar and the output are ignored, `uv run` keeps the installed client); strict harness `STRICT_MODE=True ERROR_UNCATCHED=False CUESOR_TEST_COUNT=2 uv run python
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
  per `CONTRIBUTING.md`. An operation is POST wherever the frontend was recorded sending POST.
- Placeholder: values only from recordings of the real web client (relay catalog `requests.ndjson` applied with
  `tools/update_placeholder.py <file|url>`, the relay's `twitter-api-safe-dump --cookies`, a HAR). Sample values are elonmusk /
  44196397 / 1349129669258448897; viewer-bound entries are recorded on the sandbox. TIAD's GraphQL.json is only a detector of changed queryIds.
- `tools/sweep_tweets.py` (broad strict sweep) and `tools/json_to_schema.py` (schema drafts; check its shared-type guesses, reduced
  users are not `User`) live in the workspace's `tools/`.

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
- The relay and the clients do not reference each other: the clients only document that the endpoint is configurable, the recipe
  for pointing one at the other is in the relay's README.
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
  `position: relative`. A satori bump still needs a visual pass: `tools/og_compare/` (`render.sh <outdir> node bin/run.js`,
  `compare.cjs <a> <b>`, `montage.cjs`; they need `sharp` installed next to them). satori ≥ 0.33.5 pins `fflate` 0.7.3 (medium advisory, not fixable in range).
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
- Decided with the maintainer: media is never folded into a carousel (photos stacked at full width in their own proportions, videos
  one after another); plain themes show nothing that depends on when the snap was taken (no views, a running poll as choices +
  end date), the X reference theme may; dates carry the year; phrase-level Japanese wrapping (BudouX) was declined; a translation
  replaces the text under the "Translated from <language>" line and `--translate <lang>` is never implied; no codec / container /
  quality tables in front of ffmpeg (`--ffmpegAdditonalOption` carries the rest).
- README: one `# comment` + command per feature, no per-feature images or sections. Its samples are the 🍊 post
  1770222178279252062, the poll 1604617643973124097, the photo 1349129669258448897 and the SpaceX quote 2112637394654822514,
  rendered with `TZ=Asia/Tokyo`; no Community Note sample.
- Renders for the maintainer: `screenshot/{date}/<theme>/<sample>.png` (`x-reference/`, `default/`, `x.com/` for the real page;
  `-before` / `-after`, `-dark`; an mp4 next to its `-frame.png`).
- twitter-snap-api: `width: 1440, scale: 2` (a 720 px layout at 2×), one render at a time (`createMutex(1)`, so one stuck render queues
  everything), `Failed to get snapshot` for any empty result; GPU images (`Dockerfile.nvenc` / `.qsv` / `.full`) run Node 22 from nodesource,
  `Dockerfile` is node:26; `build.sh` pins the BtbN n9.0 release line.

## Other repos
- TwitterInternalAPIDocument: generator needs a cookie; docs on `develop`, merged to `master` by the scheduled workflow; its "Update
  Document" PRs are the maintainer's own. Avoid changes unless asked; Dependabot is delegated there too. No PR checks, and code runs
  from `master`: the local check is `uv sync --frozen` on the merged lock, `lib.md.gen_md_graphql` over `docs/json/GraphQL.json`
  compared with the committed `docs/markdown/GraphQL.md` (pandas only feeds `to_markdown`), and `ruff check` against master's findings.
- x-client-transaction-id-pair-dict: `pnpm start` yields 30 pairs in a few minutes without a proxy (`PAIR_MAX=2` for a quick check);
  pairs stay valid for weeks; not on npm. Lqm1/x-client-transaction-id 0.3.2 was verified identical to the frontend (2026-10-19).
- private_bot: LINE bot calling twitter-snap-api over HTTP; depends on the TS clients directly.
