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

## State (2026-11-05)

- Nightly green since 2026-10-30. Spec `main` 9751966. Published: clients 0.1.6 on generated 0.1.5 (PyPI and npm), relay 0.4.2 /
  dashboard 0.2.3 / mcp 0.4.1 (npm and ghcr), twitter-snap 0.3.0 (npm); every image is on Node 26 with corepack installed from npm.
  x-client-transaction-id-pair-dict is not on npm.
- Unreleased: twitter-snap master 4b3d891 has #103 (even dimensions by `crop`, so a lossless WebP of a still matches the PNG pixel for
  pixel); a 0.3.1 is the maintainer's call. Nothing else is unreleased.
- No PR open from this side. Dependabot merges are delegated, but the sandbox's auto-mode classifier refuses a merge that has no
  approval in the current conversation, so get a go in the chat first. TwitterInternalAPIDocument's "Update Document" PRs are the
  maintainer's own.
- twitter_openapi_python no longer has an `example/` (its login went through the archived tweepy-authlib); the README Usage reads
  cookies from a file. twitter-openapi-typescript keeps a similar `example/`; the maintainer has not said whether it goes too.
- Open dependabot alerts, all in `pnpm-lock.yaml`: twitter_api_safe_relay 7, twitter-snap 6, twitter-snap-api 4, private_bot 14
  (`gh api repos/fa0311/<repo>/dependabot/alerts` works with the sandbox token). Dependabot's security-update jobs fail in the pnpm
  repositories ("VulnerabilityAuditor: missing lockfile", with pnpm 11 and pnpm 12 pins alike; cause not established) while its
  version-update PRs still arrive, so these need hand-made bumps. Proposed to the maintainer, no decision yet.
- Waiting on the maintainer: twitter-openapi #131 (feed-algorithm endpoints need a real "not interested" click to record), TIAD
  queryId drift recordings, a poll-with-image post URL to check twitter-snap's poll rendering, whether to delete
  `screenshot/2026-10-31/` and `screenshot/2026-11-01/` (gitignored review renders).
- Backlog: `RenderTransparentShadow` fails on `background: none` (pre-existing), `snap_tweet` MCP tool (home undecided), spec
  candidates from the relay catalog (recording only on instruction).
- Decisions live in memory (design preferences, README policy, screenshots, sandbox account budget); the translation mechanics and
  the local relay recipe are memory files too. Nothing in the sandbox is running.
