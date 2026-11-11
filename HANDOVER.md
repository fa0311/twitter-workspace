# Handover: fa0311's X / Twitter OSS maintenance sandbox

Rules are in `CLAUDE.md`, non-derivable facts in `REFERENCE.md`, judgement calls in memory.
This file holds what those cannot: the environment and the state of the work. Updated 2026-11-11.

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
- After the 2026-11-07 recreate the named volume `/root/.local` had lost uv's Python 3.13, so every `.venv` (main checkout and both
  worktrees) pointed at a missing interpreter. `uv python install 3.13` repairs the worktree venvs in place; the main checkout's venv
  was recreated (`uv venv -p 3.13 && uv sync && uv pip install ./python_generated`). `tools/graphql_get.py` and friends need the
  generated client installed in the venv they run from.
- The GPU: since 2026-11-07 the compose reserves the host's NVIDIA GPU (RTX 3080 Ti, driver 615.71.09) and the Ubuntu ffmpeg 6.1.1
  here has `h264_nvenc` / `hevc_nvenc` / `av1_nvenc`. The maintainer renamed the container to `0000-twitter-workspace` on the host
  (`docker-compose.yml`).
- The clock: the host's NTP is broken (2026-11-07: ~30 s behind the HTTP `Date` of api.github.com) and the maintainer will fix it
  eventually. The clock is the host's and the container has no CAP_SYS_TIME, so `date -s` and `adjtimex` fail with EPERM from inside;
  it can only be set on the host (or after `cap_add: [SYS_TIME]` in `docker-compose.yml`, which the maintainer decides).

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

## State (2026-11-11)

- Nightly: red 2026-11-08 .. 11-11 on main 10a5fe8, all the same cause: the sandbox account is shown a "Review your email" half
  cover on `HomeLatestTimeline` (`TimelineShowCover`), whose `TimelineHalfCover` has no `dismissible`, a new `secondaryCoverCta`,
  and a `TimelineCoverBehaviorNavigate` url object that revealed the spec's `url_type` should be `urlType`. Fixed in
  twitter-openapi #141 (`fix/nightly-2026-11-11`; recording `recordings/night_2026-11-11/HomeLatestTimeline.json`, full set 1,453 at
  1.0, strict run of 2026-11-11 green on the branch); merged on an LGTM (spec main 6c4914f). Regeneration PRs open, waiting for
  LGTMs: twitter_openapi_python #84 (generated 0.1.7 / wrapper 0.1.8) and twitter-openapi-typescript #176 (generated 0.1.7 /
  wrapper 0.1.8); neither repo has PR CI (publish runs on push to master). After #176 merges: the lockfile follow-up PR once npm
  has generated 0.1.7, then twitter-snap bumps the clients (0.4.1). The cover stays until someone confirms the email on the
  account (x.com/settings/email); tonight's nightly on 6c4914f is the live check.
- Account use 2026-11-11: one UserByScreenName check, one HomeLatestTimeline dump, one strict run (the day's allowance is used).
- Dependabot PRs open (merge delegated, need a go in the chat): twitter-openapi-typescript #173 (biome 2.6.5), #174 (tsc-alias 1.9.10),
  #175 (vitest 5.1.0); twitter_openapi_python #82 (pydantic 2.14.3), #83 (ruff 0.17.4). twitter-snap-api #19 still open (close recommended).

## State (2026-11-07, evening)

- Session of 2026-11-07 (maintenance pass): nightly of 11-07 was the only red run (fixed by #140, see below); the next one runs
  tonight on main 10a5fe8. The full recordings set validates at 1.0 on 10a5fe8 (1,449 entries). No new issues anywhere; the only
  open PRs are twitter-snap-api #19 (see below), TwitterInternalAPIDocument #1143 (the maintainer's own) and the new twitter-snap #108.
  Account: one UserByScreenName check and one cookie render (the nvenc repro) today, no lock.
- SOLVED 2026-11-07 (evening): the stall is not nvenc. The maintainer posted a second occurrence (same post, same final ffmpeg
  line); downloading the same BtbN `ffmpeg-master-latest` build (`build.sh`) reproduced it here: the final encode stays at
  `frame=0`, ignores SIGTERM; bisected to the aac encoder (`-i <video> -map 0:a -c:a aac` hangs; the default `nmr` coder; `twoloop`,
  `fast`, `-ar 44100` fine; a 2 s float WAV reproduces: `tools/out/nvenc_repro/hang_2s_f32_u.wav`). n8.1 / n9.0 release builds and
  Ubuntu 6.1.1 finish in 33 s. twitter-snap-api #22 (`fix/ffmpeg-release-build`) pins `build.sh` to the n9.0 line; merged on an LGTM
  the same evening (main 1ad73a4, Docker build of all four images green, branch deleted); the maintainer pulls the new nvenc image. Upstream report (FFmpeg trac) not filed; proposed.
  twitter-snap-api #19 (ffmpegTimeout) is still open; with the real cause fixed it is only damage control.
- GPU repro of the afternoon (before the cause was known): post 2111792834483556435 rendered here with the cookie at `--width 1440 --scale 2 --theme
  RenderOceanBlueColor --limit 1 --ffmpegAdditonalOption "-c:v hevc_nvenc -rc constqp -qp 20 -b_ref_mode middle -preset p5"` in 35 s
  (hevc 1440x2720, 41 s, 33 MB; `tools/out/nvenc_repro/`), and a synthetic 1440x2720 hevc_nvenc encode with the same options works
  too. So the maintainer's hang is not reproducible with Ubuntu's ffmpeg 6.1.1 on driver 615.71.09 / RTX 3080 Ti; their nvenc image
  copies a self-built ffmpeg from `.temp/ffmpeg` (`Dockerfile.nvenc`, CUDA 12.4.1 runtime, Node 22). Next: ask for `ffmpeg -version`
  and the GPU of that host, and the rerun of the logged ffmpeg line inside the container.
- twitter-snap #108 and the release PR #109 (`update 0.4.0`, 0.4.0 because the library API changed) merged 2026-11-07 on LGTMs;
  master 6e08141, twitter-snap 0.4.0 is on npm and ghcr (publish + docker green). twitter-snap's open alerts are now minimatch,
  @hono/node-server and fflate (medium each). twitter-snap-api #21 (`chore/twitter-snap-0.4.0`) merged the same day on an LGTM
  (main c69d698, Docker build green, branch deleted): its open alerts are now fflate + minimatch (medium). The maintainer's
  self-hosted twitter-snap-api picks 0.4.0 up when they pull the new image. `engines` is still `>=20.0.0` while sharp
  0.35 wants >= 20.9 (raised, no decision).
- twitter-snap #108 (history): `@vercel/og` replaced by `satori` ^0.33.5 + `sharp` ^0.35.5, which closes
  the three sharp and the satori alerts of twitter-snap (and, once twitter-snap-api follows, its three) without overrides; the
  font flow was reworked on the maintainer's ask ("コードのきれいさ優先", external libraries allowed): `loadFonts(dir)` in
  `src/utils/font.ts` replaces the per-app callback and `FontUtils`, `FontOptions` became `Font[]` (`getFonts`, run param `fonts`,
  required), the satori asset fallback (twemoji via `@twemoji/parser`, Noto subsets from Google Fonts) sits in `render.ts`, and
  the pixiv app renders with the Segoe UI / Meiryo set (it used `@vercel/og`'s bundled Geist before, so its look changes: bold works, no tofu). Trade-off stated in the
  PR: satori >= 0.33.5 pins `fflate` 0.7.3, so the medium fflate alert returns and is not fixable in range. satori 0.6x changes layout
  (poll bars overflow), hence the 0.33 pin. Verified: lint / typecheck / build, 58 tests, 12 guest renders equal to the published
  0.3.1 within 0.34% of pixels (`tools/out/og_compare/`). If merged: release twitter-snap 0.3.2, then twitter-snap-api follows.
  The branch `deps/vercel-og-1` (WIP commit 4b06817, `@vercel/og` 1.0.1) is a dead experiment, local only; delete it when convenient.

- Nightly: green 2026-10-30 .. 11-06 (11-06 was the first on the placeholder of #139); 11-07 failed on nulls in promoted
  trends and a sports score, fixed in twitter-openapi #140 (merged 11-07). Spec `main` 10a5fe8. Published: clients 0.1.7 on generated 0.1.6 (PyPI and npm, 2026-11-07), relay 0.4.3 /
  dashboard 0.2.3 / mcp 0.4.2 (npm and ghcr, 2026-11-07), twitter-snap 0.3.1 (npm and ghcr, 2026-11-07); every image is on Node 26 with corepack installed from npm.
  x-client-transaction-id-pair-dict is not on npm.
- Round of 2026-11-05 ("すべてやって", fewest releases): the maintainer asked for the security alerts, the stale queryIds, issue #131,
  the transparent themes and the example directories in one go. Merge and release in this order, each step after an LGTM:
  1. Done: twitter-openapi #139 merged (main 45a5fb4): placeholder re-recorded 2026-11-05 (39 operations on the frontend's current
     query versions, `SmarttagTag.rest_id`) and `postTimelineFeedback` (#131; `live_pipeline/update_subscriptions` left out, see
     REFERENCE). twitter-openapi-typescript #170 (no `example/`), twitter-snap #104 (transparent themes) and #106 (fflate 0.7.5 in
     the lockfile) are merged too (twitter-snap master a58f303).
  2. Done 2026-11-07: twitter_openapi_python #81 and twitter-openapi-typescript #171 merged (regenerated from main 10a5fe8;
     generated 0.1.6, wrappers 0.1.7 with `post_timeline_feedback` / `postTimelineFeedback`), both publish workflows green,
     PyPI and npm carry them; twitter-openapi-typescript #172 (lockfile resolves generated 0.1.6) merged the same day.
  3. Done 2026-11-07: twitter-snap #107 (`update 0.3.1`: clients ^0.1.7 / ^0.1.6, ships #103, #104, #106, and the
     `--ffmpegTimeout` help now says seconds) merged; CI on ubuntu + windows x three Node versions and the 58 guest renders
     locally were green; 0.3.1 is on npm and ghcr.
  4. Done 2026-11-07: private_bot #8 (clients 0.1.7 / 0.1.6; undici 6.29.1 / 7.30.2 and body-parser 2.4.0 inside the ranges
     discord.js, cheerio and express ask for, closes its 14 alerts; no overrides) and twitter-snap-api #20 (twitter-snap ^0.3.1,
     lockfile moves only twitter-snap and the clients; its sharp / satori / minimatch alerts stay, no fix inside the ranges) merged;
     both image builds on the merge commits (a81e01e, 010e02b) succeeded. The round is complete: every package was released once.
     The maintainer's self-hosted twitter-snap-api picks 0.3.1 up when they pull the new image.
  twitter_api_safe_relay #45 (catalog of 2026-11-05, the dump `--responses` fix, body-parser / qs / fast-uri / glob in the
  lockfile, relay 0.4.3 / mcp 0.4.2) merged 2026-11-07 after the maintainer asked for a code comment to go ("こういうコメント
  要らない"; the no-restating-comments rule is in memory). Publish, docker and test on the merge commit 461259d succeeded: relay 0.4.3 / mcp 0.4.2 on npm and ghcr.
- twitter-snap-api #19 (`ffmpegTimeout` 240 s) is open but the maintainer doubts it is the real fix ("本質的な修正じゃなさそう");
  my assessment in the chat: private_bot's plain `fetch` (undici's 300 s headers timeout) is where the error happened and sets no
  wait of its own; twitter-snap-api's `createMutex(1)` turns one stuck render into a timeout for every later request (async-mutex
  `withTimeout` would fail queued requests fast); the hang's trigger is unknown (twitter-snap hands the CDN URL to ffmpeg, a stalled
  read has no timeout). Proposed: close #19; one PR for private_bot's wait (minutes to be chosen), one for the queue bound.
  Waiting for the maintainer's choice and the container log.
- 2026-11-06: the maintainer's private_bot got `TypeError: fetch failed` (HeadersTimeoutError, exactly 300 s) from the self-hosted
  twitter-snap-api. The post from its log renders in 15 s locally on main e30904e (Node 26 and 22), so the trigger on that
  instance is unknown; what makes it permanent is known: twitter-snap-api passed `ffmpegTimeout: 30000`, which fluent-ffmpeg
  counts in seconds, and every route renders under one semaphore. twitter-snap-api #19 (240 seconds) is open; see the assessment below.
  Container log received 2026-11-07 (nvenc image, `-c:v hevc_nvenc -rc constqp -qp 20 -b_ref_mode middle -preset p5`): the stall is
  the final ffmpeg of post 2111792834483556435 (a 41 s portrait video; the download, ffprobe and the sound probe had finished), frame
  1440x2720; a landscape video (140 s, frame ~1440x1200) had rendered in 34 s just before, `/health/encoder` (h264_nvenc, one frame)
  kept answering, six later renders queued behind it. The same post renders here in software: libx264 at the default size 26 s,
  libx265 at `--width 1440 --scale 2` 134 s (1440x2720), so the filter graph and the input are fine and the hang is inside the nvenc
  session (not reproducible without a GPU). Guest access cannot read that post; the cookie can. Asked the maintainer to rerun the
  logged ffmpeg line inside the container (`.temp/hlHyGbrMjBAMkCbi/` should still hold the inputs) and to try h264_nvenc / without
  `-b_ref_mode middle`. The compose of the sandbox now reserves the NVIDIA GPU (2026-11-07, for this repro): after the
  restart check `nvidia-smi` and `ffmpeg -encoders | grep nvenc`, then render post 2111792834483556435 with the cookie at
  `--width 1440 --scale 2 --theme RenderOceanBlueColor --limit 1` and the maintainer's option string (above) to see whether
  hevc_nvenc hangs here too; Intel (`/dev/dri`) was not passed in, the incident is nvenc only.
- Raised with the maintainer, no decision: the REST wrappers (follow / unfollow, the new feedback call) send no
  `x-client-transaction-id` although the frontend does; whether to answer and close #131.
- Left open on purpose: private_bot's minimatch alert of 2026-11-07 (9.0.9 via webdav 5.11.0, the newest webdav, which asks for `^9.0.9`;
  the fix is 11.0.1); the @hono/node-server and minimatch (`@oclif/core` asks for `^10`) alerts in twitter-snap / twitter-snap-api (their fixes are outside
  the ranges `@hono/vite-dev-server` and `@oclif/core` ask for; the maintainer rejected overrides, #105 was closed; the satori and sharp
  alerts are addressed by twitter-snap #108); 18 placeholder
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
