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

## State (2026-10-31)

- twitter-snap #88 (`feat/poll-community-note` → master) is open and awaits an LGTM: poll cards render as bars (they were an empty link
  card) and a tweet's `birdwatch_pivot` renders as a Community Note box; the tweet body's line-breaking `<p>` became a shared `paragraph`
  widget and the three e2e tweets render byte-identical to master. Before / after PNGs: `screenshot/2026-10-31/` (screenshots always go to `screenshot/{date}/`, samples must be pleasant to look at).
- Feature backlog approved by the maintainer on 2026-10-31, in the order proposed: (1) poll / Community Notes in twitter-snap (#88);
  (2) pagination iterators in both clients, using the rate-limit headers to wait; (3) a relay session helper in the clients (no header
  building when the relay supplies the session); (4) thread mode in twitter-snap; (5) translation: needs a recording of the translate
  endpoint first, and the target language must be an explicit argument (X renders in the viewer's language by default); (6) a `snap_tweet`
  MCP tool; (7) rate-limit visibility in the relay dashboard / health; (8) spec candidates from the relay catalog, about 30 GraphQL
  operations the web app sends that the spec lacks (Viewer, GetUserClaims, ListMemberships, MutedAccounts, BlockedAccountsAll,
  ConversationControlsQuery, ModeratedTimeline, UserAccountLabel, AudienceAndTaggingQuery; reversible mutations PinTweet / UnpinTweet,
  PinTimeline / UnpinTimeline, MuteList / UnmuteList, ListSubscribe, UpdateList, ConversationControlChange) — an operation enters the
  spec only after it was recorded from the real client and replayed live, on instruction. Declined: a catalog freshness check in CI.
- Guest TweetResultByRestId returns both the poll card and `birdwatch_pivot`, so renderer work for these needs no cookie.

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
