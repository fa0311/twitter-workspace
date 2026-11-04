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

## State (2026-11-04)

- Nightly green since 2026-10-31. Spec `main` 24b82ab; clients 0.1.5 (endpoint factories `getClientFromEndpoint` /
  `get_client_from_endpoint`) on npm and PyPI; relay 0.4.2 / dashboard 0.2.3 / mcp 0.4.1 published and on ghcr;
  twitter-snap 0.2.1 released (RenderXReference theme, polls, Community Notes), master also has `--thread` and `--translate`
  unreleased: the release is the maintainer's call.
- twitter-snap #101 (webp / gif / webm outputs by ffmpeg's container defaults) and #100 (README gallery with two animated WebPs made
  by twitter-snap) merged 2026-11-04 (master d5ffe8f), unreleased.
- Release round in progress ("全パッケージ、リリースいれよう", 2026-11-04), in dependency order, each step LGTM-gated and waiting for the
  registry before the next: (1) done: twitter_openapi_python 0.1.6 / generated 0.1.5 on PyPI, twitter-openapi-typescript 0.1.6 / generated 0.1.5 on npm; the
  wrapper lockfile follow-up #169 is open; (2) twitter-snap #102 `release/0.3.0` open (deps ^0.1.6, Node 26 image with corepack,
  publish on Node 26, guest tests 57/57); (3) twitter-snap-api ^0.3.0 + Node 26 image, private_bot
  clients ^0.1.6 + Node 26 image. Done on the side: Node 26 images for twitter-snap-discord / -bookmarklet (merged, then their builds
  failed on the missing corepack: fix PRs #14 / #7 open, LGTM-gated) and twitter_api_safe_relay #44 (merged with the corepack fix,
  images and npm publish green). Relay packages have nothing else unreleased; x-client-transaction-pair-dict is not on npm.
- Side finding: dependabot's security-update jobs in twitter_api_safe_relay have failed since 2026-11-01 (minimatch, qs, glob,
  body-parser, fast-uri); the updater uses pnpm 12 against the repo's pnpm 11 lockfile. Not part of the release; raised with the maintainer.
- Open: dependabot bumps twitter_openapi_python #76 #77 #78 and twitter-openapi-typescript #166 #167 (all clean, no CI in those
  repos). Dependabot merges are delegated, but the sandbox's auto-mode classifier refuses a merge that has no approval in the
  current conversation, so get a go from the maintainer in the chat first. TwitterInternalAPIDocument #1140 is the maintainer's
  own scheduled PR.
- Waiting on the maintainer: twitter-openapi #131 (feed-algorithm endpoints need a real "not interested" click to record), TIAD
  queryId drift recordings, whether to delete `screenshot/2026-10-31/` and `screenshot/2026-11-01/` (gitignored review renders).
- Backlog: an animated WebP sample in the README once #101 ships (the maintainer has not decided; candidates in
  `screenshot/2026-11-04/video/`), `RenderTransparentShadow` fails on `background: none` (pre-existing, also in 0.2.1), `snap_tweet`
  MCP tool (home undecided), spec candidates from the relay catalog (recording only on instruction).
- Decisions of 2026-10-31 / 11-01 live in memory (design preferences, README policy, screenshots, sandbox account budget); the
  translation mechanics and the local relay recipe are memory files too. Nothing in the sandbox is running.
