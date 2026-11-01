# Handover: fa0311's X / Twitter OSS maintenance sandbox

Rules are in `CLAUDE.md`, non-derivable facts in `REFERENCE.md`, judgement calls in memory.
This file holds what those cannot: the environment and the state of the work. Updated 2026-10-19.

## Environment

- This directory is itself a git repository: the docs, `tools/`, `.claude/memory/` and `docker-compose.yml` are tracked, the project
  repositories are submodules pinned at the commits in use. To rebuild elsewhere: `git clone --recursive <workspace remote> /root/workspace`,
  then add `cookie.json` and `.sops/` from the maintainer. `recordings/`, `tools/out/`, the two spec worktrees and `.pnpm-store/` are
  ignored (large or derived); the recordings can be regenerated with `tools/sweep_tweets.py` and strict runs.
- `/root/workspace` is a bind mount; `/root/.claude` (memory, sessions), `/root/.cache` and `/root/.local` are named volumes since
  2026-10-19, so they survive a recreate as long as the volumes are kept. Memory is still mirrored in `.claude/memory/` and
  `sh tools/bootstrap.sh` restores it when needed, writes the gpg-agent config, recreates the writable GPG home sops needs and reports
  missing tools. Chat scratch space (`/tmp`) is wiped; keep anything valuable under this directory.
- Credentials: `cookie.json` is the sandbox account @ptcpz3, the only account to drive (verify before use, never print values);
  `.sops/age-key.txt` decrypts `twitter-secrets/secrets.enc.yaml`; GPG key material and `gh` config are mounted read-only.
  If signing fails the gpg-agent is locked and the maintainer unlocks it from a VS Code terminal.
- The `gh` token has no GraphQL scopes: merging, retargeting and editing PR bodies go through `gh api` REST calls.

## Layout

- `twitter-openapi/` is the spec repo on `main`; `twitter-openapi-browser-only/` and `twitter-openapi-sweep3/` are worktrees of it,
  each with its own venv, generator jar and cookie, so two branches can be validated at once. Leave them detached at `origin/main`.
- `twitter_openapi_python/`, `twitter-openapi-typescript/`: clients; the generated package is a subdirectory with the spec as a submodule.
- `twitter-snap*/`: the renderer (reference consumer of the TS client) and its apps. `twitter_api_safe_relay*/`: relay and its skill.
- `TwitterInternalAPIDocument/`: scraper of X's bundle, useful only as a drift detector. `twitter-secrets/`, `x-client-transaction-id-pair-dict/`, `private_bot/`.
- `tools/`: local scripts (index in `tools/README.md`). `recordings/`: 1,300+ raw X responses with `validate_args.json`, the offline
  validation set every spec change must pass at exactly 1.0 before a PR (`recordings/README.md`).

## Routine

- twitter-openapi runs a nightly strict live test (`live-test.yaml`, 23:00 UTC, often delayed); it is the main drift signal.
  A failure means: reproduce in a worktree, type the new field from the raw response, validate the recordings set, run strict, PR.
- Recordings of X requests happen on the maintainer's instruction; placeholder values come only from them.
- After a spec batch merges: regenerate both clients, then the TS lockfile follow-up, then bump twitter-snap.
- The sandbox account's rate limits differ a lot per operation (search is scarce); `tools/sweep_tweets.py` paces itself from the headers.
- Merge only on an explicit LGTM, with merge commits; retarget stacked children before deleting a merged branch.

## State (2026-11-01)

- Merged 2026-10-31 night on the maintainer's LGTM, with merge commits, head branches deleted: twitter-snap #99 (README trim),
  #92 `--thread` (the author's self-reply chain through a tweet in one image / video; honors `displayTextRange`; composes several
  video frames one after another) and #93 `--translate <lang>` (sets `x-twitter-client-language` on the session and shows the
  post as x.com shows a translated post, see below). master is 9c5324d; not released yet (last release 0.2.1), the release is
  the maintainer's call. #92 and #93 both touched the README example block and `tweetRender`, so each later one got master
  merged in (a merge commit, not a rebase: the branches had two commits whose intermediate state conflicted) and CI ran again
  before the merge; the resolved tree was verified by rendering a thread and a translation from it.
- Merged 2026-11-01 on the maintainer's LGTM ("1 2 3 は LGTM", then "#42 LGTM"), merge commits, head branches deleted:
  twitter-openapi-typescript #165 `getClientFromEndpoint(basePath, headers)` (1e83cdb) and twitter_openapi_python #75
  `get_client_from_endpoint(host, headers)` (1ad5b71), both 0.1.5 and published by the push-to-master workflows (npm run
  41265700136, PyPI run 41265703296, both registries checked before the next step); then twitter_api_safe_relay #41 README
  recipe on the factories (69353ec, merged only after the registries showed 0.1.5) and #42 Tests section without the CI
  plumbing (3deb5f7). Local checkouts of the two client repos are on master.
- Merged 2026-11-01 ("LGTM" after the page change): twitter_api_safe_relay #40 rate-limit visibility (X's `x-rate-limit-*`
  headers passed through on relay responses, latest per profile x endpoint in `/health` and a dashboard page; relay 0.4.1,
  dashboard 0.2.2), merge commit 3c5a695, head branch deleted, local checkout back on main. Push-to-main runs: publish
  41268901924 and docker 41268901930 both succeeded (npm shows twitter-api-safe-relay 0.4.1 and twitter-api-safe-relay-dashboard 0.2.2), test 41268901919. No PR of ours is open anywhere.
  Review history: it first stopped at the README ("READMEの問題が残っている", then "Rate limitsの節いる？"): the "Rate limits"
  section went away entirely (7011bcd, 7074457; the PR body carries the explanation).
  For the review the relay from `feat/rate-limit` is running in the sandbox ("手元で見たいからサーバー建てて"): port 3777,
  `twitter_api_safe_relay` checked out on `feat/rate-limit` with `pnpm build` done, started with
  `node packages/server/dist/server.js <settings>` (settings and the profile seeder are kept in `tools/relay_local/`, the
  running instance uses the session scratchpad copy; log `scratchpad/relay40/relay.log`). The maintainer reaches it through a
  VS Code port forward of 3777: `http://localhost:3777/` is the dashboard (the rate-limit panel is at the bottom of the sidebar
  and works without debug mode), `/health` the JSON. One `UserByScreenName` was sent through it so the panel has a row;
  `screenshot/2026-11-01/relay40-dashboard.png` shows it. The process dies with the container; restart with the tools recipe. It kept running after the merge (its dist is the branch build, same content as main); `kill $(pgrep -f dist/server.js)` ends it.
  Review feedback so far and what was done: "Rate Limitは無限に増えていくだろうから、別のページに作ったほうが良いのでは？" →
  c64da1f moves the table out of the request sidebar onto its own page (header switch Requests / Rate limits, hash
  `#rate-limits`, full-height table with a text filter, `/health` polled only while open; `RateLimitPanel.tsx` deleted,
  `RateLimitPage.tsx` added, sidebar back to main's version; PR body updated). The running relay serves the new build from
  the dashboard's `dist` without a restart (`screenshot/2026-11-01/relay40-rate-limits-page.png`, `-requests-page.png`).
  "v1.1 系のAPIが叩け無い、404になる" (2026-11-01, asked again "v1.1は再現できなかった？"): reproduced and fixed in
  twitter_api_safe_relay #43 (merged 2026-11-01 on "LGTM", merge commit 74213d9, head branch deleted, local checkout on main; publish run 41332967464 and docker run 41332967444 both succeeded: npm has twitter-api-safe-relay 0.4.2 (depends on dashboard 0.2.3), twitter-api-safe-relay-dashboard 0.2.3, twitter-api-safe-mcp 0.4.1; ghcr `latest-relay*` = 0.4.2-*, `latest-mcp*` = 0.4.1-* as of 17:47 UTC, so `docker compose pull` on the maintainer's side gets the fixed dashboard). Cause: relay 0.4.0 (2026-10-17)
  moved REST from `/1.1/*`, `/2/*` to `/i/api/1.1/*`, `/i/api/2/*`, but the dashboard's JavaScript tab still generated
  `fetch("/1.1/...")` for REST entries (GraphQL snippets had `/i/api`), so Execute got the relay's own 404. Fix: one `relayPath`
  for both, Vite dev proxy `/i/api`, versions dashboard 0.2.3 / relay 0.4.2 / mcp 0.4.1 (the docker workflow pushes an image
  only when `<version>-<suffix>` is new, so the bumps are what refresh `latest-relay*` / `latest-mcp*`). Measured on the
  running relay with Playwright (`screenshot/2026-11-01/relay-dashboard-v11-execute-{before,after}.png`): before
  `GET /1.1/users/show.json -> 404`, after `GET /i/api/1.1/users/show.json -> 200`. Other paths checked and fine: the skill
  (`$B/i/api<path>`), the MCP (dispatches directly), curl per the README. Direct relay facts from the probes: `/1.1/...`
  without `/i/api` and non GET/POST methods are Hono 404s; an endpoint X does not serve (statuses/show) is X's
  `ApiError HTTP-404 codes:[1003]`, relayed as 500; a form-encoded POST body is a 500 (`c.req.json()`).
  "docker系にデプロイしてるやつもアップデートしよう": the maintainer's own relay runs from `docker/docker-compose.yml`
  (kasmweb + `latest-relay-slim`, relay at localhost:6900 as in the skills README); nothing in the sandbox to update (no
  docker here). ghcr got `0.4.1-*` / `latest-*` for relay, relay-slim, relay-firefox, relay-webkit at 03:23–03:25 today;
  the dashboard fix reaches the images once its PR is merged (new tags 0.4.2-*, 0.4.1-mcp*). `docker compose pull` on
  their side then picks them up. twitter-snap-api (docker) depends on twitter-snap ^0.2.1, nothing newer released.
  The typed TS wrapper has no v1.1 helpers (`getV11GetApi().api` is the generated class, which wants every placeholder
  parameter), so a v1.1 call from the typed clients is the generated API with the endpoint as base path.
  Pitfalls met: cookies added with `addCookies` without `expires` are session cookies and vanish when the seeding context
  closes, so the relay's `launch` profile opened x.com logged out and every `/i/api/*` request hung forever (`waitStartup`
  has no timeout; `/health` still answered). Seed with `expires`. Do not `pkill -f` a pattern that also matches the shell
  running the relay command.
- README policy settled 2026-10-31 ("READMEいじる意味ある？"): twitter-snap's README is a list of one-line examples plus the oclif
  usage block; features get `# comment` + command in the example block and nothing else. No explanatory paragraphs (PR description)
  and no per-feature sample images in `docs/img` (samples: issue #47, or `screenshot/` for the maintainer). #92 and #93 were trimmed
  to that shape and twitter-snap #99 does the same to the merged x.com reference section (drops its paragraph and four images,
  1 MB). The three PRs touch the same example block, so whichever merges later is rebased.
  Review material for the maintainer (the earlier renders had disappeared from `screenshot/2026-10-31/`, the folder is
  gitignored): `screenshot/2026-10-31/readme/` holds every README version rendered with GitHub's own markdown API
  (`gh api /markdown`) + github-markdown-css in Playwright (`<version>.png` full page, `<version>-examples.png` the example block;
  `all-merged` is a local composition of the three PRs); `thread/` and `translate/` hold fresh renders from the PR heads
  (SpaceX EVA thread 1786759044948189202, Tesla Japan 2113567187046993971 with `--translate en`, four themes each, cookie
  session, 13 account calls, no 326). Pitfall met on the way: with a cookie session a status URL renders the whole
  conversation up to `--limit` (default 20), so a fixed `-o name.png` ends up holding the last entry (a related post), not the
  tweet of the URL; use `--limit 1` or keep `{id}` in the output name.
- Translation UI (2026-10-31 evening, "TwitterのtranslateのUIにもっとよせて"): x.com's translated post was measured with
  `tools/x_dom_styles.py` (`tools/out/translate_ui/`, screenshots copied to `screenshot/2026-10-31/translate/x.com-{light,dark}.png`):
  the translation replaces the text; above it a 13/16 line "[Grok] Translated from Japanese  Show original [gear]" (4px above,
  24px to the text), below it "Rate this translation: [thumbs]" (14/16, 24px buttons with 16px icons, 12px above), then the media.
  twitter-snap (#93, merged) does the same: every theme swaps the text for the translation under a Grok-marked line; the X reference
  theme adds Show original, the gear and the rating row; the plain themes keep only the line (page controls stay out of them).
  The original text is no longer in the image, as on x.com.
- Dependabot in twitter-snap 2026-10-31 evening: #94 (@oclif/plugin-plugins), #97 (puppeteer 25.16.0), #98 (@oclif/core 5.1.10),
  #95 (@oclif/plugin-warn-if-update-available) and #96 (@oclif/plugin-help) merged with merge commits, branches deleted (master
  c4d8af0). #95 / #96 conflicted on the lockfile after the first merge; dependabot rebased them by itself within ~15 min and CI
  went green again, so lockfile conflicts in a dependabot batch only need waiting, not a manual rebase.
- Translation (recorded 2026-10-31, `recordings/translate/`, tools `record_translate.py` / `rest_call.py`): x.com no longer calls
  a translation endpoint for posts. TweetDetail / TweetResultByRestId carry `grok_translated_post_with_availability` (already
  typed) and the destination language follows the request header `x-twitter-client-language`; replies are often
  `is_available: false` until someone clicks. On-demand translation is a Grok streaming POST (`/2/grok/translation.json`, NDJSON
  without content-type) that the generated clients cannot consume, and the old strato `translateTweet` is only a code fallback the
  web client no longer sends. So: no spec change; twitter-snap sets the header itself and renders the embedded translation.
- twitter-snap #88 (polls + Community Notes) and #89 (RenderXReference theme) were merged 2026-10-31 with merge commits (master
  a9eb14c), head branches deleted. Released as twitter-snap 0.2.0 the same day (#90 `release/0.2.0`, merge 3e39f38, publish run
  41186046218, npm shows 0.2.0; the README usage block was refreshed with `node replace.js` after a build). 0.2.0 has a defect:
  one or two rows of the marker color stay under a video whose frame is an odd pixel tall; fixed and released as 0.2.1 the same day
  (#91, merge 9797ebd, publish run 41188325568, npm 0.2.1). #91 also put the README samples on the current renderer (JST) and added
  the x.com reference samples: Elon Musk and official accounts only, never private individuals (also scrubbed from the #88 / #89
  descriptions). `test.yml` runs only for PRs against master and a
  retarget does not trigger it (`gh workflow run test.yml --ref <branch>` does). pngjs's `PNG.sync.read` breaks on Node 25; the
  stream parser is used.
- Merged 2026-10-31 evening: twitter-snap-api #15 (twitter-snap ^0.2.1, LGTM'd) and the dependabot batch the maintainer delegated
  (twitter-openapi #137 / #138, twitter-openapi-typescript #162, TwitterInternalAPIDocument #1135–#1137), all with merge commits,
  branches deleted. Dependabot merges are delegated from now on (CI first where a repo has it, merge commits).
- `paginate()` (twitter-openapi-typescript #164, twitter_openapi_python #74) was closed unmerged: limit / waiting / cancellation are the
  caller's business, and a helper with debatable semantics is worse than none.
- Backlog after this batch: `snap_tweet` MCP tool (where it lives is undecided), spec candidates from the relay catalog (recording
  only on instruction). Waiting on the maintainer: twitter-openapi #131 feedback.json recording, TIAD queryId drift recordings,
  whether to delete `screenshot/2026-10-31/`.
- Design decisions of 2026-10-31 (also in memory): plain themes do not depend on when the snap was taken (no views, running polls show
  choices + end date, no controls); RenderXReference copies the page including views / counts / time left / controls; media is
  stacked at full width (x.com's carousel is not copied: media would fall out of the picture); videos play one after another in one
  frame found by its marker color; quoted dates always carry the year; width defaults stay 650 / 600 (both give x.com's 566px column).
  A thread is the author's own reply chain through the tweet (never other people's tweets); ancestors and continuation are compact
  with the avatar line, the tweet itself in full, as x.com's conversation page.
- Guest TweetResultByRestId returns both the poll card and `birdwatch_pivot`, so renderer work for these needs no cookie.
- The relay's `dispatch` resolves to X's parsed body only; response headers come from Playwright's `page.on("response")`.

## State (2026-10-30, evening)

- Shipped 2026-10-30: spec #136 / #135, clients 0.1.4 (twitter_openapi_python #72, twitter-openapi-typescript #159 with the TypeScript 7
  build fix) on PyPI and npm, dependabot bumps in python / typescript / TIAD.
- Follow-ups merged the same day: twitter-openapi-typescript #163 (wrapper lockfile) and twitter-snap #85 (^0.1.4). Nothing open from
  this side; TwitterInternalAPIDocument #1133 (develop → master) is the maintainer's own scheduled PR. twitter-snap on ^0.1.4; relay 0.4.0.
- twitter-snap 0.1.2 released 2026-10-30 (#87; publish.yml publishes on master when the version is new on npm, registry lagged ~1 min
  behind the green run). It carries #85 (^0.1.4) and #86: text wrapping comes from `linebreak` (UAX #14) instead of one flex item
  per non-Latin character, so Japanese no longer breaks before 。、ー / small kana and newlines after non-Latin characters are kept.
  Verified with guest renders (build `dist` first: `bin/dev.js` runs the stale dist). Phrase-level wrapping (BudouX) was offered and
  declined: wrapping stays browser-equivalent.
- Spec `main` (24b82ab) is ahead of the 0.1.4 clients by #136 only; not worth a release on its own.
- Publish workflows: a run can fail on a transient sigstore / registry step while a later run on the same version succeeds (seen for
  python 0.1.4); check the registry version before treating a red publish run as a problem.
- Issues triaged 2026-10-23 (30 closed). Left open on purpose: twitter-openapi #33 (missing-API checklist, maintained by the maintainer),
  twitter-openapi #131 (feed-algorithm endpoints, moved from TIAD; recording `/2/timeline/feedback.json` needs a real "not interested"
  click on the sandbox, which leaves a side effect, so wait for instruction), pair-dict #6 (maintainer's own investigation). Replies on
  GitHub are terse and never mention automation; questions for the maintainer go to the chat.
- Drift hotspots: notifications and ads. Each nightly fix so far came from `NotificationsTimeline` or a promoted / pre-roll item in
  `HomeTimeline`; a nightly that fails before its first `Try:` line with a proxy connection error is infrastructure, rerun it first.
- The sandbox account has been locked twice (2026-10-20 and 2026-10-26, both after a few hundred live calls within a few hours; the
  maintainer clears it at x.com/account/access). Symptom: every GraphQL response carries `errors[].code == 326` with a bounce to
  `/account/access`, partial data still comes back. Budget: the nightly plus at most one strict run or one wrapper e2e suite per day,
  never two suites concurrently; sweeps only on instruction. When the probe (`tools/graphql_get.py UserByScreenName`) shows 326, stop
  every live call and tell the maintainer.
- Drift seen but not acted on: TIAD shows newer queryIds for DelegatedAccountListQuery, affiliatesQuery, PremiumContentQuery,
  useSubscriptionProductDetailsQuery, AboutAccountQuery. X still accepts the old ids; a recording is the only valid fix.
- Only one untyped spec site remains (`TweetInterstitialRevealText`). Sports-related HAR operations were skipped on purpose.
