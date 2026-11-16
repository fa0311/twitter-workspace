# Handover: fa0311's X / Twitter OSS maintenance sandbox

Rules are in `CLAUDE.md`, non-derivable facts in `REFERENCE.md`, the maintainer's judgement calls in memory.
This file holds the environment, the routine and the current state. Past states: `git log -p -- HANDOVER.md`. Updated 2026-11-16.

## Environment

- Since 2026-11-16 the work runs in a Kasm desktop container (Ubuntu 26.04, user `kasm-user`, passwordless `sudo`) operated through
  T3 Code. Until then it ran as root in a container with the workspace bind-mounted at `/root/workspace`; its `docker-compose.yml`
  left the repository with the move.
- The workspace is `/home/kasm-user/twitter-workspace`, a clone of fa0311/twitter-workspace: docs, `tools/` and `.claude/memory/` are
  tracked, the project repositories are submodules pinned at the commits in use (detached after a clone: switch to the default
  branch and pull before branching). Ignored and therefore only on this machine: `cookie.json`, `recordings/`, `tools/out/`,
  `screenshot/`, spec worktrees, `.pnpm-store/`.
- `/home/kasm-user` is one docker volume (workspace, `~/.claude`, `~/.cache`, `~/.local`); the image around it was rebuilt several
  times on the first day while the volume carried over. Whatever is installed with apt is gone after a recreate, so tools go into
  `~/.local` (`~/.local/bin` is first on `PATH`). Chat scratch is under `/tmp/claude-1000/` and is wiped.
- `sh tools/bootstrap.sh` initialises missing submodules, restores memory into
  `~/.claude/projects/-home-kasm-user-twitter-workspace/memory/`, restores `cookie.json` from twitter-secrets, links it into
  `twitter-openapi/`, checks that it is @ptcpz3 and that signing works, and prints the install line for every missing tool.
- Credentials: the maintainer's GPG key is mounted read-only behind `~/.gnupg`; `/usr/local/bin/git-gpg` (set as `gpg.program` in
  `/etc/gitconfig`) passes the passphrase from the environment, so git signs and sops decrypts twitter-secrets without anyone
  unlocking anything (REFERENCE, "Sandbox"). The CI age key is not on disk. `gh` runs on `GITHUB_TOKEN` with the scopes
  `public_repo` and read-only ones (no `workflow`); every repository of the family is public. If a GraphQL-backed command fails on
  token scopes, use `gh api` REST.
- Installed and tried on 2026-11-16: Node 26 with pnpm 12 (pnpm fetches the version a repo pins), uv with Python 3.14, a Temurin 17
  JRE in `~/.local/share/java`, the generator jar in `twitter-openapi/`, Playwright with its Chromium in the `twitter-openapi` venv
  (`uv pip install playwright`; not a dependency of the repo), sops, age, jq, Ubuntu's ffmpeg 8.0.1 with `h264_nvenc` / `hevc_nvenc`
  on the host's NVIDIA RTX 3080 Ti. Not here: docker (images are checked by CI only), corepack, a second Node version.
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

- twitter-openapi's nightly strict live test (`live-test.yaml`, 23:00 UTC, often delayed) is the main drift signal. On a failure:
  reproduce in a worktree, type the new field from the raw response, validate the recordings set, run strict once, PR.
  A failure before the first `Try:` line with a proxy error is a proxy outage: `gh run rerun <id> --failed`.
- Recordings of X requests happen on the maintainer's instruction; placeholder values come only from them.
- Release chains, each step after an LGTM unless delegated: spec merge → regenerate both clients (wrappers pin the spec hash) → the TS
  lockfile follow-up once npm has the generated package → twitter-snap release PR `update x.y.z` (version only; publish + Docker run on
  the merge) → twitter-snap-api lockfile bump (its Docker builds on push to main, no PR checks: `pnpm build` + `pnpm test` locally) →
  private_bot when the TS wrapper moved. twitter-snap-discord / -bookmarklet call the API over HTTP, nothing to bump.
- Dependabot: grouped in all seven repos (weekly version groups where they exist, one security group everywhere), ungrouped in
  TwitterInternalAPIDocument; merges are delegated everywhere (CI green or a local check, merge commit, relay at most once a day). Alerts GitHub cannot fix itself are handled by hand (REFERENCE, "GitHub and CI").
- Account use per day is in `CLAUDE.md`; a lock (`code 326`) is cleared only by the maintainer.

## State (2026-11-16)

- Moved to the new environment today. Tried here: spec build, strict client generation and install, `tools/graphql_get.py
  UserByScreenName` (200, no errors: the account is not locked and X is reached directly), `tools/validate_dumps.py` on that response
  (1.0), a Playwright Chromium launch on a blank page, twitter-snap `pnpm install` + `pnpm build` and one guest render, nvenc
  encoding, decrypting both secrets, pushing this repository and merging PRs with this token. Not tried here yet: a strict run, any
  Playwright script against X, the relay (`tools/relay_local`), the wrappers' e2e suites, opening a PR, a commit touching a workflow
  file (the token has no `workflow` scope).
- `recordings/` was not brought along, on purpose (maintainer, 2026-11-16), and neither were `tools/out/`, `screenshot/` and the two
  spec worktrees. There is no offline validation set here: a spec change is checked by the strict run alone unless a set is
  collected again (`tools/README.md`, "Offline validation set").
- Nightly green 2026-11-12 .. 11-16 on spec main e48c4bd (6c4914f plus lockfile / CI-only commits; the clients pin 6c4914f).
  The "Review your email" half cover that broke 11-08 .. 11-11 is typed (#141); it may return until someone confirms the email on
  the account (x.com/settings/email).
- Published: PyPI generated 0.1.7 / wrapper 0.1.8; npm generated 0.1.8 / wrapper 0.1.8 (0.1.7 on npm is a dud without `dist/`);
  twitter-snap 0.4.3 (npm + ghcr: resvg-js rasterizer, satori 0.63 with the border-box wrapper, Biome 2.6); twitter-snap-api main
  ddc85cd on twitter-snap 0.4.3 (Docker green; the maintainer pulls the image); private_bot master 0ebbb0a on clients 0.1.8;
  relay 0.4.3 / dashboard 0.2.3 / mcp 0.4.2. twitter-snap master f5e6d4f is ahead of 0.4.3 by Dependabot bumps only (puppeteer
  25.17.0, hono, vite); no release needed until something user-facing lands.
- No open PRs in the maintained repos; TwitterInternalAPIDocument's #1144 (Update Document) is the maintainer's own. Its Dependabot
  #1145 / #1146 (pandas 3.1.1, ruff 0.17.4) were merged on 11-16 after the local check in REFERENCE, "Other repos". Account use
  since 11-13: the nightlies, plus eleven single GETs on 11-16 (`UserByScreenName`, `TweetResultByRestId`).
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
- The render compare kit is tracked in `tools/og_compare/` (`render.sh`, `compare.cjs`, `montage.cjs`, public sample URLs): render
  master and the branch into two directories and diff.
