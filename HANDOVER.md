# Handover: fa0311's X / Twitter OSS maintenance sandbox

Rules are in `CLAUDE.md`, non-derivable facts in `REFERENCE.md`, the maintainer's judgement calls in memory.
This file holds the environment, the routine and the current state. Past states: `git log -p -- HANDOVER.md`. Updated 2026-11-16.

## Environment

- This directory is a git repository: docs, `tools/`, `.claude/memory/` and `docker-compose.yml` are tracked, the project repositories
  are submodules pinned at the commits in use. Rebuild elsewhere with `git clone --recursive <workspace remote> /root/workspace` plus
  `cookie.json` and `.sops/` from the maintainer. Ignored: `recordings/` (212 MB, regenerable with `tools/sweep_tweets.py` and strict
  runs), `tools/out/` (1.8 GB of compare sets and ffmpeg builds), the two spec worktrees, `.pnpm-store/`, `screenshot/`.
- `/root/workspace` is a bind mount; `/root/.claude`, `/root/.cache` and `/root/.local` are named volumes that survive a recreate as
  long as they are kept. `/tmp` (chat scratch) is wiped. `sh tools/bootstrap.sh` restores memory, writes the gpg-agent config,
  recreates the writable GPG home sops needs and reports missing tools. If a recreate loses uv's Python, `uv python install 3.13`
  repairs the venvs (`tools/graphql_get.py` and friends need the generated client installed in the venv they run from).
- Credentials: `cookie.json` (sandbox account @ptcpz3), `.sops/age-key.txt` (decrypts `twitter-secrets/secrets.enc.yaml`); GPG key
  material and `gh` config are mounted read-only. `gh pr create/checks/merge/close` and `gh run` work; if a GraphQL-backed command
  fails on token scopes, use `gh api` REST.
- Hardware: the compose reserves the host's NVIDIA RTX 3080 Ti (Ubuntu ffmpeg 6.1.1 with `h264_nvenc` / `hevc_nvenc`). The container
  is `0000-twitter-workspace` on the host. The host clock runs a few seconds behind GitHub's; it cannot be set from inside.

## Layout

- `twitter-openapi/` spec repo on `main`; `twitter-openapi-browser-only/` and `twitter-openapi-sweep3/` are worktrees of it with their own
  venv, generator jar and cookie (two branches can be validated at once; leave them detached at `origin/main`).
- `twitter_openapi_python/`, `twitter-openapi-typescript/`: clients; the generated package is a subdirectory with the spec as a submodule.
- `twitter-snap*/`: the renderer (reference consumer of the TS client) and its apps; `twitter_api_safe_relay*/`: relay and its skill;
  `TwitterInternalAPIDocument/` (drift detector only); `twitter-secrets/`, `x-client-transaction-id-pair-dict/`, `private_bot/`.
- `tools/` local scripts (`tools/README.md`); `recordings/` 1,450+ raw X responses with `validate_args.json`, the offline set every spec
  change must pass at exactly 1.0 before a PR (`recordings/README.md`); `screenshot/{date}/` renders for the maintainer.

## Routine

- twitter-openapi's nightly strict live test (`live-test.yaml`, 23:00 UTC, often delayed) is the main drift signal. On a failure:
  reproduce in a worktree, type the new field from the raw response, validate the recordings set, run strict once, PR.
  A failure before the first `Try:` line with a proxy error is a proxy outage: `gh run rerun <id> --failed`.
- Recordings of X requests happen on the maintainer's instruction; placeholder values come only from them.
- Release chains, each step after an LGTM unless delegated: spec merge → regenerate both clients (wrappers pin the spec hash) → the TS
  lockfile follow-up once npm has the generated package → twitter-snap release PR `update x.y.z` (version only; publish + Docker run on
  the merge) → twitter-snap-api lockfile bump (its Docker builds on push to main, no PR checks: `pnpm build` + `pnpm test` locally) →
  private_bot when the TS wrapper moved. twitter-snap-discord / -bookmarklet call the API over HTTP, nothing to bump.
- Dependabot: grouped in all seven repos (weekly version groups where they exist, one security group everywhere); merges are delegated
  (CI green, merge commit, relay at most once a day). Alerts GitHub cannot fix itself are handled by hand (REFERENCE, "GitHub and CI").
- Account use per day is in `CLAUDE.md`; a lock (`code 326`) is cleared only by the maintainer.

## State (2026-11-16)

- Nightly green 2026-11-12 .. 11-16 on spec main e48c4bd (6c4914f plus lockfile / CI-only commits; the clients pin 6c4914f).
  The "Review your email" half cover that broke 11-08 .. 11-11 is typed (#141); it may return until someone confirms the email on
  the account (x.com/settings/email).
- Published: PyPI generated 0.1.7 / wrapper 0.1.8; npm generated 0.1.8 / wrapper 0.1.8 (0.1.7 on npm is a dud without `dist/`);
  twitter-snap 0.4.3 (npm + ghcr: resvg-js rasterizer, satori 0.63 with the border-box wrapper, Biome 2.6); twitter-snap-api main
  ddc85cd on twitter-snap 0.4.3 (Docker green; the maintainer pulls the image); private_bot master 0ebbb0a on clients 0.1.8;
  relay 0.4.3 / dashboard 0.2.3 / mcp 0.4.2. twitter-snap master f5e6d4f is ahead of 0.4.3 by Dependabot bumps only (puppeteer
  25.17.0, hono, vite); no release needed until something user-facing lands.
- No open PRs in any repo. Account use since 11-13: the nightlies only.
- Open for the maintainer: `npm deprecate twitter-openapi-typescript-generated@0.1.7`; `requires-python >= 3.11.5` in twitter-openapi and
  twitter_openapi_python (the soupsieve alert may stay open while the locks keep 2.10 for older Pythons); the leftover branch
  `fix/ffmpeg-timeout-seconds` in twitter-snap-api (closed #19, the sandbox cannot delete unmerged branches); private_bot's `minimatch`
  alert (9.0.9 via the newest webdav, fix 11.0.1: only an override or upstream could close it); twitter-snap-api's `Failed to get snapshot`
  hides twitter-snap's reason (deleted post, age restriction) — proposed to carry the error text into the API message, not done.
- Raised, no decision: the REST wrappers send no `x-client-transaction-id` although the frontend does; whether to answer and close
  twitter-openapi #131; the GET form of `HomeTimeline` still carries `seenTweetIds` (the frontend sends them only by POST); 18 placeholder
  operations the browser session did not send (listed in #139); an upstream FFmpeg report of the aac `nmr` hang.
- Waiting on the maintainer: a poll-with-image post URL to check twitter-snap's poll rendering.
- Backlog: `snap_tweet` MCP tool (home undecided), spec candidates from the relay catalog (recording only on instruction).
- Scratch kept on purpose: `screenshot/2026-11-13/` (the deleted 19-photo post rendered at scale 1 and at the API's width 1440 / scale 2
  from its saved response), `tools/out/og_compare/` (render compare sets: `master042`, `satori063`, `satori063fix`, `resvg`, `baseline`).
