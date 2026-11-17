# Handover: fa0311's X / Twitter OSS maintenance sandbox

Rules are in `CLAUDE.md`, non-derivable facts in `REFERENCE.md`, the maintainer's judgement calls in memory.
This file holds the environment, the routine and the current state. Past states: `git log -p -- HANDOVER.md`. Updated 2026-11-17.

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

## State (2026-11-17)

- Last daily run: 2026-11-17, the first one by the scheduled task. The nightly failed on two calls and twitter-openapi #145
  answered it (merged the same day after the LGTM, next two points). Merged as delegated: twitter_openapi_python #87 (ruff 0.17.5, dev only; local check: `uv sync --frozen`,
  ruff findings identical to master, import) and TwitterInternalAPIDocument #1147 (Update Document, no anomaly). The alerts
  are the ones listed below, no issue or outside PR has moved since 11-02, every other workflow run since 11-16 succeeded, and
  no release chain step is due.
- Spec main is 37b4afd (#145): `AudioSpace.metadata` / `participants` optional, `TimelineRichTextCashtag` in `BirdwatchEntityRef.type` (a Community
  Note subtitle in `BirdwatchFetchGlobalTimeline`), `TweetSportsCompetitor.score` optional instead of nullable (absent before
  the game; #140 had typed it from the log alone). Checked with the two raw responses at 1.0 and one strict run (130 calls at
  1.0); the nightly of 11-18 is the first one on it.
- The space change of #145 rested on one response and a guess of mine, and the maintainer approved it without that being
  visible; the rules that came out of it are in `CLAUDE.md` (Delivery rules, zero-tolerance) and in Routine. Examined
  afterwards (11-17): `metadata` is not gone. The sample's id no longer resolves (it still answered in the nightly of 11-16),
  and the answer with only `is_subscribed` is the one for any id that resolves to no space. Numbers in the next point, facts
  in REFERENCE, "X behaviour".
- Waiting for review: twitter-openapi #146 (branch `fix/audio-space-sample-and-title`, 3bb13cd), opened after the maintainer
  said that everything in the sandbox is permitted and to do what is necessary. It replaces the sample by a Binance space of
  2025-10-09 that the real Chrome still shows (`1yNGabwXqXnJj`; the four spaces X's own accounts link no longer resolve, Elon
  Musk's accounts link none) and makes `AudioSpaceMetadata.title` and `tweet_results` optional. It rests on 34 real space ids
  fetched with the placeholder's request: 24 answer with `metadata` (7 running, 17 ended; `title` absent in 2, `tweet_results`
  in 1), 10 do not resolve; all 22 of the last 31 days answer, of the 12 others only two. Checked: the 41 saved answers and
  a live GET of the new sample validate at 1.0 with the regenerated strict client. Not checked: a full strict run on the
  branch (the day's run was spent), why spaces stop resolving and so how long the sample lasts, scheduled or cancelled
  spaces, a second logged-in account.
- The maintainer decides (asked in the chat 11-17, no answer yet): whether `metadata` / `participants` stay optional, as
  `UserResponseData.user` and `TweetResultByRestIdData.tweetResult` are for their not-found answers, or go back to required.
  Optional means a client gets an object for an unknown id and the nightly keeps passing when the sample dies; required means
  the nightly turns red on a dead sample and a client raises. #146 leaves them optional.
- The answers are in `recordings/spaces_2026-11-17/` (35 files, listed in `validate_args.json`): on main 37b4afd three of them
  fail (`title` twice, `tweet_results` once), on the branch of #146 all validate at 1.0.
- twitter_openapi_python #88 (generated 0.1.8 / wrapper 0.1.9) and twitter-openapi-typescript #181 (generated 0.1.9 / wrapper
  0.1.9) are open, regenerated from 37b4afd, and held by the maintainer (11-17): not to be merged as they are. The spec moves
  again (#146); after that merge both are regenerated onto the new commit, so that each package is released once, and the
  space tests of both wrappers go back to reading `metadata.title` with the new id: the change that made them tolerate a
  missing `metadata` hid the dead sample, and a test that fails when the sample dies is the signal. The suites were not run.
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
  Not tried here yet: a Playwright script that acts on X, the relay
  (`tools/relay_local`), a whole e2e suite of a wrapper, a commit touching a workflow file (the token has no `workflow` scope).
- There is no `tools/out/` or `screenshot/` and no spec worktree, and `recordings/` holds nothing but the 35 space answers of
  11-17: the maintainer left the rest behind on purpose (2026-11-16). Beyond those a spec change is checked by the strict run
  alone unless a set is collected again (`tools/README.md`, "Offline validation set").
- Nightly green 2026-11-12 .. 11-16 on spec main e48c4bd (6c4914f plus lockfile / CI-only commits; the published clients pin
  6c4914f), failed 11-17 on two calls (#145).
  The "Review your email" half cover that broke 11-08 .. 11-11 is typed (#141); it may return until someone confirms the email on
  the account (x.com/settings/email).
- Published: PyPI generated 0.1.7 / wrapper 0.1.8; npm generated 0.1.8 / wrapper 0.1.8 (0.1.7 on npm is a dud without `dist/`);
  twitter-snap 0.4.3 (npm + ghcr: resvg-js rasterizer, satori 0.63 with the border-box wrapper, Biome 2.6); twitter-snap-api main
  8b63e01 on twitter-snap 0.4.3 (Docker green; the maintainer pulls the image); private_bot master 0ebbb0a on clients 0.1.8;
  relay 0.4.3 / dashboard 0.2.3 / mcp 0.4.2. twitter-snap master f5e6d4f is ahead of 0.4.3 by Dependabot bumps only (puppeteer
  25.17.0, hono, vite); no release needed until something user-facing lands.
- Open PRs in the maintained repos: twitter-openapi #146, twitter_openapi_python #88 and twitter-openapi-typescript #181. Account use since 11-13:
  the nightlies, plus on 11-16 twelve single GETs (`UserByScreenName`, `TweetResultByRestId`) and one twitter-snap-api test run
  (three renders with the cookie session), on 11-17 two single GETs (`AudioSpaceById`, `BirdwatchFetchGlobalTimeline`), one
  strict run and four single e2e tests (the space and the Birdwatch timeline in each wrapper), then with the maintainer
  present nine `SearchTimeline` and 39 `AudioSpaceById` GETs and four page views of space pages (every answer 200, no lock).
- Alerts that stay open because no release of the parent reaches the fix: fflate 0.7.3 pinned by satori (twitter-snap,
  twitter-snap-api); minimatch 9.0.9 and `@hono/node-server` 1.19 under the newest `@hono/vite-dev-server`, dev only (twitter-snap);
  minimatch 9.0.9 under the newest webdav (private_bot); soupsieve, see the next point.
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
