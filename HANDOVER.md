# Handover: fa0311's X / Twitter OSS maintenance sandbox

Rules are in `CLAUDE.md`, non-derivable facts in `REFERENCE.md`, the maintainer's judgement calls in memory.
This file holds the environment, the routine and the current state. Past states: `git log -p -- HANDOVER.md`. Updated 2026-11-20.

## Environment

- The work runs in a Kasm desktop container (Ubuntu 26.04, user `kasm-user`, passwordless `sudo`, `TZ=Asia/Tokyo` while GitHub
  reports UTC) operated through T3 Code.
- Only git is durable. The image was rebuilt several times on 2026-11-16, and `/home/kasm-user` is the docker volume `agent_home`:
  it outlasts the container, but that day it was also replaced by an empty one, which took the clone, the venvs, the JRE, the
  browsers, every `node_modules` and Claude's session history with it. Chat scratch is under `/tmp/claude-1000/` and is wiped.
- The workspace is `/home/kasm-user/twitter-workspace`, a clone of fa0311/twitter-workspace: docs, `tools/` and `.claude/memory/` are
  tracked, the project repositories are submodules pinned at the commits in use (detached after a clone: switch to the default
  branch and pull before branching; TwitterInternalAPIDocument and x-client-transaction-id-pair-dict are moved by their own
  workflows, so their pins are always behind). Ignored and therefore only on this machine: `cookie.json`, `recordings/`,
  `tools/out/`, `screenshot/`, spec worktrees, `.pnpm-store/`.
- The image ships Node 26 with npm and pnpm 12 (pnpm switches to the version a repo pins in `packageManager`), uv with Python 3.14,
  `gh`, sops, age, jq, Ubuntu's ffmpeg 8.0.1 with `h264_nvenc` / `hevc_nvenc` on the host's NVIDIA RTX 3080 Ti, Google Chrome, Go
  and Rust. Not there: docker (images are checked by CI only), corepack, a second Node version.
- The home volume holds the rest: a Temurin 17 JRE in `~/.local/share/java` (`~/.local/bin` is first on `PATH`), the generator jar
  and the venv of `twitter-openapi/` with the strict generated client and Playwright (not a dependency of the repo), Playwright's
  Chromium in `~/.cache/ms-playwright`.
- `sh tools/bootstrap.sh` initialises missing submodules, restores memory into
  `~/.claude/projects/-home-kasm-user-twitter-workspace/memory/`, restores `cookie.json` from twitter-secrets, links it into
  `twitter-openapi/`, checks that it is @ptcpz3 and that signing works, and prints the install line for everything missing. On an
  empty home the printed lines, run top to bottom, bring all of the above back in a few minutes.
- Credentials: the maintainer's GPG key is mounted read-only behind `~/.gnupg`; `/usr/local/bin/git-gpg` (set as `gpg.program` in
  `/etc/gitconfig`) passes the passphrase from the environment, so git signs and sops decrypts twitter-secrets without anyone
  unlocking anything (REFERENCE, "Sandbox"). The CI age key is not on disk. `gh` runs on `GITHUB_TOKEN` with the scopes
  `public_repo` and read-only ones (no `workflow`); every repository of the family is public. If a GraphQL-backed command fails on
  token scopes, use `gh api` REST.
- The container has a desktop (KasmVNC, `DISPLAY=:1`) with Google Chrome, and the session offers browser tools (chrome-devtools,
  cua-driver, the T3 preview). None of them has been used against X; the recording scripts drive Playwright's own Chromium.

## Layout

- `twitter-openapi/` spec repo. Its venv holds the strict generated client (`uv pip install ./python_generated`) and Playwright.
  A second checkout for validating two branches at once is a worktree next to it (`twitter-openapi-browser-only/` and
  `twitter-openapi-sweep3/` are the ignored names) with its own venv, generator jar and cookie link; none exists at the moment.
- `twitter_openapi_python/`, `twitter-openapi-typescript/`: clients; the generated package is a subdirectory with the spec as a submodule.
- `twitter-snap*/`: the renderer (reference consumer of the TS client) and its apps; `twitter_api_safe_relay*/`: relay and its skill;
  `TwitterInternalAPIDocument/` (drift detector only); `twitter-secrets/`, `x-client-transaction-id-pair-dict/`, `private_bot/`.
- `tools/` local scripts (`tools/README.md`); `recordings/` raw X responses with `validate_args.json`, the offline set every spec
  change must pass at exactly 1.0 before a PR (absent here, see State); `screenshot/{date}/` renders for the maintainer.

## Routine

- twitter-openapi's nightly strict live test (`live-test.yaml`, cron 23:00 UTC; GitHub starts it between 11:00 and 13:30 JST) is the main drift signal. On a failure:
  reproduce it with a single GET, then diagnose as `CLAUDE.md` demands ("twitter-openapi is zero-tolerance": other samples of
  the operation with a positive control, the real web client when they cannot tell) and name the cause. Only a change of X is
  typed, from the raw responses: validate the recordings set, run strict once, PR. A sample that went bad or a cause that stays
  unknown is reported with what was checked, and the nightly stays red until the maintainer decides.
  A failure before the first `Try:` line with a proxy error is a proxy outage: `gh run rerun <id> --failed`.
- Recordings of X requests happen on the maintainer's instruction; placeholder values come only from them. Looking at what the
  real web client sends and gets for a page, without clicks, is not such a recording: it belongs to any diagnosis (REFERENCE,
  "Sandbox": the real Chrome).
- Release chains, each step after an LGTM unless delegated: spec merge → regenerate both clients (wrappers pin the spec hash) → the TS
  lockfile follow-up once npm has the generated package → twitter-snap release PR `update x.y.z` (version only; publish + Docker run on
  the merge) → twitter-snap-api lockfile bump (its Docker builds on push to main, no PR checks: `pnpm build` + `pnpm test` locally) →
  private_bot when the TS wrapper moved. twitter-snap-discord / -bookmarklet call the API over HTTP, nothing to bump.
- Dependabot: grouped in all seven repos (weekly version groups where they exist, one security group everywhere), ungrouped in
  TwitterInternalAPIDocument; merges are delegated everywhere (CI green or a local check, merge commit, relay at most once a day). Alerts GitHub cannot fix itself are handled by hand (REFERENCE, "GitHub and CI").
- Account use per day is in `CLAUDE.md`; a lock (`code 326`) is cleared only by the maintainer.

## Daily run

The maintainer asked for daily maintenance at 14:00 JST (2026-11-16), after the nightly. A T3 scheduled task, "Daily
maintenance", starts a fresh session in its own thread every day and works through this list with nobody present:

1. `sh tools/bootstrap.sh`, then the lines it prints.
2. The day's nightly; when GitHub has not started it by 14:00 JST, say so and go by the previous one. Failed: as in Routine;
   the fix is a PR only when the cause is established, otherwise the report carries the question.
3. Dependabot PRs in every repository: merged as delegated (Routine); a failing one is replaced by an own PR.
4. TwitterInternalAPIDocument's "Update Document" PR: `python3 ../tools/tiad_check.py` in its checkout. No anomaly: merged with
   a merge commit, `develop` stays. An anomaly: left open and reported.
5. New Dependabot alerts: a PR when the fix is inside the parents' ranges, otherwise the reason goes into State.
6. New issues and PRs from others: read and reported, nothing is written on GitHub.
7. What an earlier merge made due in a release chain: the next PR is opened.
8. State in this file, with the date of this run on its first line ("new" above means since that date), commit, push.
9. A short report in Japanese: what changed, a direct link to every PR that waits for review, each with what it rests on
   (observed on which samples), what was not verified and what the maintainer has to decide, and the new X features that
   the day's translation strings, operations and feature switches reveal (only the interesting ones).

Unattended, only Dependabot PRs and TwitterInternalAPIDocument's Update Document are merged. Every other PR, the run's own
included, waits for the maintainer's review and is merged in the session where the LGTM arrives. The account is spent only on
what a failed nightly needs (single GETs, the control samples of the diagnosis among them; one page view without clicks when
the samples cannot tell a changed X from a wrong request; one strict run) and on the local check of a Dependabot PR;
recordings, sweeps and suites are never started by this run.

T3 starts the run in a worktree of this repository (`~/.t3/worktrees/twitter-workspace/<id>`, a branch of its own at
`main`, submodules checked out at their pins) and tells the session to stay there. That checkout has no `cookie.json`, venv
or jar. What worked on 2026-11-17: `sh /home/kasm-user/twitter-workspace/tools/bootstrap.sh` for the check of the home volume;
`ln -s /home/kasm-user/twitter-workspace/cookie.json` into the worktree root and into its `twitter-openapi/`, the jar copied
from the workspace's `twitter-openapi/`, then the "strict client" line of bootstrap in the worktree's `twitter-openapi/` (three
minutes with the warm uv cache); project branches are made in the worktree's submodules. The State commit goes out with
`git push origin HEAD:main`, followed by `git -C /home/kasm-user/twitter-workspace pull --ff-only` and `submodule update` there,
so that the workspace and the next worktree start from it.

The task lives in T3's state inside the home volume. When `list_scheduled_tasks` no longer shows it, create it again with
`schedule_task`: `fixed_time` 14:00, `bindToCurrentThread: false`, `freshSession: true`, and this prompt:

> Daily maintenance of fa0311's X / Twitter repositories: follow HANDOVER.md, section "Daily run", in
> /home/kasm-user/twitter-workspace (CLAUDE.md rules apply). Nobody is present: merge only what CLAUDE.md delegates (Dependabot
> PRs, TwitterInternalAPIDocument's Update Document); every other PR, your own included, waits for the maintainer's review.
> Finish with a short report in Japanese that links every PR waiting for review and tells which new X features the day's
> documents reveal.

## State (2026-11-20)

- Last daily run: 2026-11-20, by the scheduled task. The nightly passed on d31ab31 (130 calls, each at 1.0). Merged as
  delegated: TwitterInternalAPIDocument #1150 (Update Document, no anomaly, `develop` stays). In the web client's documents
  (`docs/json`, same build as on 11-19) it changed the account's values of `x_sports_post_context_min_spacing` (25 → 5) and
  `x_sports_post_context_same_game_min_spacing` (25 → 10) and the metadata, nothing else. The X Pro documents
  (`docs/deck/json`) moved to another build: one switch neither tree had (`grok_xweb_bot_promotion_enabled`, default false,
  the account's value true), `ElectionsTimelineIdFeedQuery` with a new queryId where `electionsTimelineIdFeedQuery` was,
  queryIds of three `businessInsights*` and two elections operations that the web client's documents do not have, nine
  operations gone that the web client's documents still list, and otherwise what the web client's documents already had
  ('Clip video', `unifiedCardReminder*`, the video clipping, sports and international wires defaults). Until this run
  `tools/tiad_check.py` reported `docs/json` alone and the defaults alone; it now reports both trees and the account's
  values. No Dependabot PR was open and no alert is new: twitter-snap #234 (picomatch `<= 4.0.7`, GHSA-fc5q-39xc-vjpf) is
  still shown as open on an advisory GitHub withdrew on 11-18, with 4.0.7 the newest release on npm and nothing to bump;
  twitter-snap-api, private_bot and the relay lock picomatch 4.0.7 as well and have no alert, why only twitter-snap got one
  is unknown. The other alerts are the ones listed below (the newest satori 0.63.2, `@hono/vite-dev-server` 0.26.1 and
  webdav 5.11.0 still do not reach the fixes), no issue or outside PR has moved since 11-02, every workflow run since the
  run of 11-19 succeeded, and no release chain step is due. The run did not use the account.
- twitter-openapi #147 waits for the LGTM (`chore/placeholder-2026-11-20`, three commits on d31ab31, head b92c0ac, `build`
  passed). The daily run had found that TwitterInternalAPIDocument listed another queryId than the placeholder for 56 of
  the spec's 117 GraphQL operations, 38 of them since the day after the recording of 11-05, and the maintainer ordered a
  re-recording ("しようか、暇だから時間かけて丁寧にやっていいよ"). Recorded on 11-20 with the relay's dump in the desktop's Chrome, 53 pages in 14 minutes,
  logged from the network side as well (`tools/wire_tee.mjs`): every catalog line has an identical request on the wire.
  42 entries change (40 new queryIds; `post_ctas_fetch_enabled` true in 40; two more features in the two community
  timelines), 34 were sent and stay, 41 were sent by no page. Typed from the recorded answers: five fields that only the
  recorded query versions return, each compared on one target with both queryIds (commit 2), and shapes that do not
  depend on the queryId (commit 3: `AboutProfile` of other accounts, `ProfileBio.with_held_scope`,
  `Tweet.conversation_control_details` on the sandbox's own posts, four fields of the community page seen on 16
  communities). Checked: one strict run on the branch (130 calls at 1.0, before `is_identity_verified` was added; its
  answers are at 1.0 with the final client), 595 of the 596 recorded answers, 16 control GETs, the stored sets. Not
  checked: the mutations, a second account, the wrappers' suites. The PR text has the numbers.
- Asked of the maintainer with #147 (11-20), no answer yet: a `record_actions.py` session for the mutations and the list
  dialogs (eleven entries no page sent still carry `post_ctas_fetch_enabled: false`, `CreateTweet` among them, and 16
  entries still have another queryId than TwitterInternalAPIDocument: `BirdwatchFetchContributorNotesSlice`,
  `BroadcastQuery`, `CommunityHashtagsTimeline`, `CreateTweet`, `DelegatedAccountListQuery`, `DmAllSearchSlice`,
  `Favoriters`, `ListCreationRecommendedUsers`, `ListEditRecommendedUsers`, `ListOwnerships`, `PremiumContentQuery`,
  `UserMedia`, `UserTweets`, `UserTweetsAndReplies`, `affiliatesQuery`, `useSubscriptionProductDetailsQuery`);
  `membersSliceTimeline_Query` is sent without `features` while its entry keeps one, and `ProfileSpotlightsQuery` has
  `features: {}` (the tool never removes, and removing changes the generated signature); `mode` of
  `conversation_control_details` as a string (as proposed) or an enum of the two recorded values; the affiliate label
  with a mention on the community page (one answer, not typed, `recordings/placeholder_2026-11-20/open_args.json`).
- Due after the LGTM of #147: the chain of Routine from the merged hash (both clients, the TS lockfile follow-up).
  Whether twitter-snap then gets a release is open: the earlier decision waits for a user-facing change, and this
  placeholder moves `TweetDetail` and the features of `TweetResultByRestId`, which twitter-snap calls.
- Not done: the relay's catalog (`packages/server/requests.ndjson`) can be refreshed from the same recording. The
  session's latest requests carry ids of other people's posts and communities, so the variables need a pass before
  anything is published, or a run of the dump with its own page list; the PR belongs to a day without a suite.
- Spec main is d31ab31 (#146, merged 11-18 after the LGTM; before it #145, 37b4afd). The `AudioSpaceById` sample is a
  Binance space of 2025-10-09 that the real Chrome still shows (`1yNGabwXqXnJj`; the four spaces X's own accounts link no
  longer resolve, Elon Musk's accounts link none), `AudioSpaceMetadata.title` and `tweet_results` are optional (absent in 2
  and 1 of 24 spaces), `AudioSpace.metadata` / `participants` are required as before #145, `TimelineRichTextCashtag` is in
  `BirdwatchEntityRef.type` (a Community Note subtitle in `BirdwatchFetchGlobalTimeline`), `TweetSportsCompetitor.score` is
  optional instead of nullable (absent before the game; #140 had typed it from the log alone). Checked: one strict run on
  37b4afd (130 calls at 1.0); for #146 the saved space answers (the 25 with `metadata` at 1.0, the 10 without fail, as
  intended) and a live GET of the new sample at 1.0, no strict run of its own (it touches only the `AudioSpace*` schemas
  and the sample). The nightlies of 11-18 .. 11-20 ran on d31ab31 and passed.
- What happened around the space (11-17, 11-18): #145 made `metadata` / `participants` optional after one response and a
  guess of mine, and the maintainer approved it without that being visible; the rules that came out of it are in `CLAUDE.md`
  (Delivery rules, zero-tolerance) and in Routine. Examined afterwards: `metadata` is not gone. The old sample's id no longer
  resolves (it still answered in the nightly of 11-16), and the answer with only `is_subscribed` is the one for any id that
  resolves to no space; why a space stops resolving is unknown, and so is how long the new sample lasts. The maintainer
  chose required once it was looked up that the web client treats that answer as a failure (its error sheet is a branch on
  the space's error flag in `bundle.AudioSpacePeek`, no exception): a generated client failing on it is the same behaviour,
  and a sample that stops resolving turns the nightly red. Numbers and facts in REFERENCE, "X behaviour". Not sampled:
  scheduled or cancelled spaces, a second logged-in account.
- The answers are in `recordings/spaces_2026-11-17/` (35 files). `validate_args.json` lists the 25 with `metadata`, all at
  1.0 on d31ab31; the 10 that resolve to no space fail there as intended and are listed in `unresolved_args.json` next to
  them. The console recording of the two Chrome pages and its script are in `recordings/spaces_2026-11-18/`.
- Both clients are regenerated from d31ab31 and published (11-18, after the LGTM): twitter_openapi_python #88 (master
  afabd8a; PyPI generated 0.1.8 / wrapper 0.1.9, seen on PyPI) and twitter-openapi-typescript #181 (master 25f4312; npm
  generated 0.1.9 / wrapper 0.1.9, both seen on the registry; the wrapper appeared in the packument a few minutes after
  the publish run). The generated diff is three models (`AudioSpaceMetadata`, `BirdwatchEntityRef`, `TweetSportsCompetitor`) and the
  sample id; the wrappers changed version, dependency, spec hash and the id in the space test, which reads
  `metadata.title` and so fails when the sample dies. Checked before the merge: the space e2e test of each wrapper against
  X, the builds, linters as on master. Not checked: the Birdwatch e2e tests again (passed 11-17 on byte-identical model
  files), the rest of both suites.
- The rest of that chain was merged on 11-18 after the LGTM, none of it releasing a package: twitter-openapi-typescript
  #182 (master 2e29867: the wrapper's lockfile on generated 0.1.9; the publish run found both versions on npm and published
  nothing), twitter-snap #123 (master d2566ad: `package.json` and lockfile on both clients 0.1.9; the publish run found
  0.4.3 on npm, the Docker build passed) and private_bot #12 (master aac51dc: the same bump; the Docker build passed).
  twitter-snap's `tests` run on d2566ad failed in one of six jobs (ubuntu, lts/-1) on the pixiv test
  `single_illust_to_image` alone (no output file, `ENOENT`; the 19 Twitter tests of that job passed) and passed on the
  rerun of that job; why the first attempt produced no file is unknown.
- No twitter-snap release for clients 0.1.9: none of twitter-snap, twitter-snap-api and private_bot reads a field that
  changed (grep over their `src`), and the placeholder of d31ab31 differs from the one of 6c4914f only in the space sample
  id. Asked whether to release anyway, the maintainer left it to the sandbox (11-19, "either is fine"): decided against, the
  bumps go out with the next user-facing change, and until then twitter-snap-api has nothing to bump.
- Seen on the way, nothing done: the web client sends `post_ctas_fetch_enabled: true` with `AudioSpaceById` where the
  placeholder (features recorded 11-05) has `false`; query id, variables and the other 41 features are the same.
- The home volume was replaced after the previous push (15:37 JST) and set up again from this repository within the hour. Tried
  in the new home: every line bootstrap prints, the spec build, strict client generation and install, `tools/graphql_get.py
  UserByScreenName` (200, no errors: the account is not locked and X is reached directly), `tools/validate_dumps.py` on that response
  (1.0), a Playwright Chromium launch on a blank page, twitter-snap `pnpm install` + `pnpm build` and one guest render,
  twitter-snap-api `pnpm build` + `pnpm test` (it renders with the cookie session), nvenc encoding, decrypting both secrets,
  pushing this repository, opening and merging a PR, and on 11-17 a strict run from a fresh checkout, both client
  regenerations, single e2e tests of both wrappers and Playwright page views of x.com with the cookie session (no clicks), in
  the bundled Chromium and in the desktop's Google Chrome.
  On 11-20 the relay's `pnpm install` and its dump in the desktop's Chrome (in the daily run's worktree; the workspace's
  relay checkout has no `node_modules`).
  Not tried here yet: a Playwright script that acts on X, the relay itself
  (`tools/relay_local`), a whole e2e suite of a wrapper, a commit touching a workflow file (the token has no `workflow` scope).
- There is no `tools/out/` or `screenshot/` and no spec worktree; the maintainer left the earlier recordings behind on
  purpose (2026-11-16). `recordings/` holds the space answers of 11-17 and 11-18, `placeholder_2026-11-20/` (the dump's
  `requests.ndjson` and `responses/`, the tee's `wire.ndjson` and 680 `wire_responses/`, 16 `controls/`),
  `cache_raw_2026-11-17/` (the strict run of 11-17, on the previous queryIds) and `cache_raw_2026-11-20/` (the strict run
  on #147). `validate_args.json` lists 881 answers, all at 1.0 with the client of b92c0ac; the two that do not validate
  are listed next to their files (`unresolved_args.json`, `open_args.json`).
- Nightly green 2026-11-12 .. 11-16 on spec main e48c4bd (6c4914f plus lockfile / CI-only commits; the published clients pin
  6c4914f), failed 11-17 on two calls (#145), green 11-18 .. 11-20 on d31ab31.
  The "Review your email" half cover that broke 11-08 .. 11-11 is typed (#141); it may return until someone confirms the email on
  the account (x.com/settings/email).
- Published: PyPI generated 0.1.8 / wrapper 0.1.9; npm generated 0.1.9 / wrapper 0.1.9 (generated 0.1.7 on npm is a dud without `dist/`);
  twitter-snap 0.4.3 (npm + ghcr: resvg-js rasterizer, satori 0.63 with the border-box wrapper, Biome 2.6); twitter-snap-api main
  8b63e01 on twitter-snap 0.4.3 (Docker green; the maintainer pulls the image); private_bot master aac51dc on clients 0.1.9;
  relay 0.4.3 / dashboard 0.2.3 / mcp 0.4.2. twitter-snap master d2566ad is ahead of 0.4.3 by dependency bumps only (puppeteer
  25.17.0, hono, vite, both clients 0.1.9); no release needed until something user-facing lands.
- Open PRs in the maintained repos: twitter-openapi #147. Account use since 11-13:
  the nightlies, plus on 11-16 twelve single GETs (`UserByScreenName`, `TweetResultByRestId`) and one twitter-snap-api test run
  (three renders with the cookie session), on 11-17 two single GETs (`AudioSpaceById`, `BirdwatchFetchGlobalTimeline`), one
  strict run and four single e2e tests (the space and the Birdwatch timeline in each wrapper), then with the maintainer
  present nine `SearchTimeline` and 39 `AudioSpaceById` GETs and four page views of space pages (every answer 200, no lock),
  on 11-18 (JST, before the nightly) with the maintainer present two page views of space pages, one `AudioSpaceById` GET and
  the space e2e test of each wrapper (all answered); the daily runs of 11-18 .. 11-20 used nothing; on 11-20 after the
  daily run, on the maintainer's order, one recording session (53 page views with their tabs and no click that changes
  anything; what the web client writes by itself on such pages went out: notifications marked as seen, one
  `PutClientEducationFlag`, the push permission state of the new browser), 19 single GETs (`UserByScreenName` three times, the controls of #147) and one strict run (every answer 200
  except the session's seven 403 of `UsersByRestIds` and nine 429 at its end; `UserByScreenName` answered 200 without
  errors afterwards).
- Alerts that stay open because no release of the parent reaches the fix: fflate 0.7.3 pinned by satori (twitter-snap,
  twitter-snap-api); minimatch 9.0.9 and `@hono/node-server` 1.19 under the newest `@hono/vite-dev-server`, dev only (twitter-snap);
  minimatch 9.0.9 under the newest webdav (private_bot); soupsieve, see the next point. Open without any fixed release:
  picomatch 4.0.7 (twitter-snap #234, advisory withdrawn).
- Open for the maintainer: `npm deprecate twitter-openapi-typescript-generated@0.1.7`; `requires-python >= 3.11.5` in twitter-openapi and
  twitter_openapi_python (the soupsieve alert may stay open while the locks keep 2.10 for older Pythons); the leftover branch
  `fix/ffmpeg-timeout-seconds` in twitter-snap-api (closed #19, the sandbox cannot delete unmerged branches); twitter-snap-api's
  `Failed to get snapshot` hides twitter-snap's reason (deleted post, age restriction) — proposed to carry the error text into the
  API message, not done.
- Raised, no decision: the REST wrappers send no `x-client-transaction-id` although the frontend does; whether to answer and close
  twitter-openapi #131; the GET form of `HomeTimeline` still carries `seenTweetIds` (the frontend sends them only by POST); 18 placeholder
  operations the browser session did not send (listed in #139); an upstream FFmpeg report of the aac `nmr` hang.
- Waiting on the maintainer: a poll-with-image post URL to check twitter-snap's poll rendering.
- Backlog: `snap_tweet` MCP tool (home undecided), spec candidates from the relay catalog (recording only on instruction).
- The render compare kit is tracked in `tools/og_compare/` (`render.sh`, `compare.cjs`, `montage.cjs`, public sample URLs): render
  master and the branch into two directories and diff.
