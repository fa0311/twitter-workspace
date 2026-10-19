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

## State (2026-10-19)

- Nothing open. Spec `main` clean on the nightly; clients 0.1.3 (lag `main` by one small nightly fix, next regeneration is 0.1.4 when
  a batch justifies it); twitter-snap on ^0.1.3; relay 0.4.0 (everything under `/i/api`); spec, clients and relay cross-link in their docs.
- Drift seen but not acted on: TIAD shows newer queryIds for DelegatedAccountListQuery, affiliatesQuery, PremiumContentQuery,
  useSubscriptionProductDetailsQuery, AboutAccountQuery. X still accepts the old ids; a recording is the only valid fix.
- Only one untyped spec site remains (`TweetInterstitialRevealText`). Sports-related HAR operations were skipped on purpose.
