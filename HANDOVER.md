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

## State (2026-10-30)

- Open, LGTM-gated: twitter-openapi #136 (nightlies 10-27 / 10-29: ad `clickTrackingInfo.urlOverride`, `UserLabelMentionUser` without
  `core`; strict 130/130), the verified 0.1.4 clients twitter_openapi_python #72 and twitter-openapi-typescript #159 (the
  latter also fixes the TypeScript 7 build), and dependabot bumps twitter-openapi #135, python #71 #73, typescript #160 #161, TIAD #1132.
  All CI-clean. TwitterInternalAPIDocument #1133 (develop → master) is the maintainer's own scheduled PR.
- After #72 / #159 merge: the TS lockfile follow-up PR, then twitter-snap to ^0.1.4 (lockfile), as for 0.1.3. twitter-snap on ^0.1.3; relay 0.4.0.
- Spec `main` (8535fd9) will lag the 0.1.4 clients by #136 once it lands; a 0.1.5 is not worth a release on its own.
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
