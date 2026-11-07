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

- Account budget: the nightly plus at most one strict run or one wrapper e2e suite per day, never two suites at once, and a push to a
  twitter_api_safe_relay PR counts as three logins (its CI runs a live browser session per Node version). The account was locked on
  2026-10-20, 10-26 and 11-04 after days heavier than that; `tools/graphql_get.py UserByScreenName` showing `code 326` means stop and
  tell the maintainer (they clear it at x.com/account/access).

- twitter-openapi runs a nightly strict live test (`live-test.yaml`, 23:00 UTC, often delayed); it is the main drift signal.
  A failure means: reproduce in a worktree, type the new field from the raw response, validate the recordings set, run strict, PR.
- Recordings of X requests happen on the maintainer's instruction; placeholder values come only from them.
- After a spec batch merges: regenerate both clients, then the TS lockfile follow-up, then bump twitter-snap.
- The sandbox account's rate limits differ a lot per operation (search is scarce); `tools/sweep_tweets.py` paces itself from the headers.
- Merge only on an explicit LGTM, with merge commits; retarget stacked children before deleting a merged branch.

## State (2026-11-07)

- Nightly: green 2026-10-30 .. 11-06 (11-06 was the first on the placeholder of #139); 11-07 failed on nulls in promoted
  trends and a sports score, fixed in twitter-openapi #140 (merged 11-07). Spec `main` 10a5fe8. Published: clients 0.1.7 on generated 0.1.6 (PyPI and npm, 2026-11-07), relay 0.4.2 /
  dashboard 0.2.3 / mcp 0.4.1 (npm and ghcr), twitter-snap 0.3.0 (npm); every image is on Node 26 with corepack installed from npm.
  x-client-transaction-id-pair-dict is not on npm.
- Unreleased: twitter-snap master 4b3d891 has #103 (even dimensions by `crop`, so a lossless WebP of a still matches the PNG pixel for
  pixel); it ships with the 0.3.1 of the round below.
- Round of 2026-11-05 ("すべてやって", fewest releases): the maintainer asked for the security alerts, the stale queryIds, issue #131,
  the transparent themes and the example directories in one go. Merge and release in this order, each step after an LGTM:
  1. Done: twitter-openapi #139 merged (main 45a5fb4): placeholder re-recorded 2026-11-05 (39 operations on the frontend's current
     query versions, `SmarttagTag.rest_id`) and `postTimelineFeedback` (#131; `live_pipeline/update_subscriptions` left out, see
     REFERENCE). twitter-openapi-typescript #170 (no `example/`), twitter-snap #104 (transparent themes) and #106 (fflate 0.7.5 in
     the lockfile) are merged too (twitter-snap master a58f303).
  2. Done 2026-11-07: twitter_openapi_python #81 and twitter-openapi-typescript #171 merged (regenerated from main 10a5fe8;
     generated 0.1.6, wrappers 0.1.7 with `post_timeline_feedback` / `postTimelineFeedback`), both publish workflows green,
     PyPI and npm carry them. Open, LGTM-gated: twitter-openapi-typescript #172 (lockfile resolves generated 0.1.6, lockfile only).
  3. Open, LGTM-gated: twitter-snap #107 (`update 0.3.1`: clients ^0.1.7 / ^0.1.6, ships #103, #104, #106, and the
     `--ffmpegTimeout` help now says seconds). Typecheck, lint, build and the 58 guest-render tests passed locally on Node 26.
     Merging publishes 0.3.1 to npm.
  4. twitter-snap-api (twitter-snap ^0.3.1; none of its alerts has a fix inside the ranges) and private_bot (new clients,
     body-parser and undici inside their ranges): one PR each, not started.
  twitter_api_safe_relay is independent: #45 is open and green (catalog of 2026-11-05, the dump `--responses` fix, body-parser /
  qs / fast-uri / glob in the lockfile, relay 0.4.3 / mcp 0.4.2), LGTM-gated.
- 2026-11-06: the maintainer's private_bot got `TypeError: fetch failed` (HeadersTimeoutError, exactly 300 s) from the self-hosted
  twitter-snap-api. The post from its log renders in 15 s locally on main e30904e (Node 26 and 22), so the trigger on that
  instance is unknown; what makes it permanent is known: twitter-snap-api passed `ffmpegTimeout: 30000`, which fluent-ffmpeg
  counts in seconds, and every route renders under one semaphore. twitter-snap-api #19 (240 seconds) is open, LGTM-gated.
  Still wanted from the maintainer: the twitter-snap-api container log around the failure, the image variant, `FFMPEG_OPTION`.
- Raised with the maintainer, no decision: the REST wrappers (follow / unfollow, the new feedback call) send no
  `x-client-transaction-id` although the frontend does; whether to answer and close #131.
- Left open on purpose: the satori, sharp, @hono/node-server and minimatch (`@oclif/core` asks for `^10`) alerts in twitter-snap / twitter-snap-api (their fixes are outside
  the ranges `@vercel/og` 0.11.1 and `@hono/vite-dev-server` ask for; the maintainer rejected overrides, #105 was closed); 18 placeholder
  operations the browser session did not send (listed in #139); the GET form of `HomeTimeline` still carries `seenTweetIds`, which
  the frontend only sends by POST (raised with the maintainer, no decision).
- Account use on 2026-11-05: nightly, one catalog recording session, one feedback click (undone), one strict run.
- Dependabot merges are delegated, but the sandbox's auto-mode classifier refuses a merge that has no approval in the current
  conversation, so get a go in the chat first. TwitterInternalAPIDocument's "Update Document" PRs are the maintainer's own.
- twitter_openapi_python no longer has an `example/` (its login went through the archived tweepy-authlib); the README Usage reads
  cookies from a file.
- Waiting on the maintainer: a poll-with-image post URL to check twitter-snap's poll rendering (they are looking too).
- Backlog: `snap_tweet` MCP tool (home undecided), spec candidates from the relay catalog (recording only on instruction).
- Decisions live in memory (design preferences, README policy, screenshots, sandbox account budget); the translation mechanics and
  the local relay recipe are memory files too. Nothing in the sandbox is running.
