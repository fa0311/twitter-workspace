# Twitter ecosystem reference

Facts that are not derivable from the repos or the web. History and PR numbers are in git; the current state is in `/root/workspace/HANDOVER.md`.

## Sandbox
- `/root/workspace` is a bind mount owned by the host user; as root, git needs `safe.directory` for it (bootstrap sets it). The workspace is a git repo with the project repositories as submodules.
- Parallel Bash calls share one shell cwd: use absolute paths and `git -C`. `pkill -f` matches the calling shell; kill by pid.
- GPG key is passphrase-protected; the sandbox agent is unlocked by the maintainer from a VS Code terminal (long cache TTL). sops uses the writable copy `GNUPGHOME=/root/.gnupg-rw`.
- `gh` works for `pr create`, `pr checks`, `run list/view`; GraphQL-backed commands fail (token scopes). Merge / retarget / body edits / branch deletion go through `gh api` REST, and a branch is deleted only after `pulls?state=open&base=<branch>` is empty.
- Secrets: `source .sops/env.sh && SOPS_AGE_KEY_FILE=.sops/age-key.txt sops decrypt --extract '["proxy_list"]' twitter-secrets/secrets.enc.yaml` (same for `cookie_json`).
- A nightly that fails before its first `Try:` line with a proxy connection error is a proxy outage, not drift: `gh run rerun <id> --failed` first.
- The sandbox reaches X directly. GitHub-hosted runners get a Cloudflare challenge, so CI goes through the maintainer's HTTP CONNECT proxies (`proxy_list` in twitter-secrets, one `http://user:pass@host:port` per line, fastest first; exits fluctuate, so reruns are legitimate). Chromium only authenticates against HTTP proxies.

## X behaviour
- New GraphQL query versions have no `User.legacy`; old queryIds keep returning it and keep working for a while.
- Logged-out x.com is static HTML; guest-token GraphQL still works. `UserByRestId` / `UsersByRestIds` are 403 for non-browser clients. Other users' likes are empty. Every list answers `ListByRestId` with a partial `BadRequestError`, so the harness skips it.
- X frequently returns complete data next to partial `errors`; the harness logs these as warnings, not failures.
- The web app sends REST under `/i/api/1.1/...`; `HomeTimeline` is GET; mutations no longer send `dark_request`.
- Rate limits per 15 minutes vary by an order of magnitude between operations (search is the scarce one); read `x-rate-limit-*`.

## twitter-openapi (spec)
- Build: `uv run python tools/build.py`; generate the strict Python client with `openapi-generator-cli.jar` 7.26.0 (`test/python/openapi-generator-config.yaml`); strict harness `STRICT_MODE=True ERROR_UNCATCHED=False CUESOR_TEST_COUNT=2 uv run python test/python/test_serialize.py` calls every GET operation of every API class with the placeholder values and raises `Not defined: Model.field` / enum errors. PostApi is never executed: mutations are validated from recorded dumps.
- Harness details: placeholder keys resolve case-insensitively (operations named in lowerCamel exist); `cache/*.json` holds `{raw, type}` of every response of a run.
- Offline check before any PR: every file in `recordings/validate_args.json` at match rate exactly 1.0 via `tools/validate_dumps.py`; add every new recording there.
- Generated `from_dict` reads every key with `obj.get`, so `required` + `nullable` silently accepts absence; model an absent field as optional non-nullable.
- Conventions: `src/openapi/paths/*.yaml` hold paths and their response schemas, shared objects live in `src/openapi/schemas/*.yaml`, `__typename` values must be in `schemas/typename.yaml`, tags map to generated API classes, hooks inject the placeholder parameters at build time. Schema sharing only for the same backend object under the same key; a look-alike site gets its own type. Enum vs string per `CONTRIBUTING.md`.
- Placeholder: values only from recordings of the real web client (relay catalog `requests.ndjson` applied with `tools/update_placeholder.py <file|url>`, the relay's `twitter-api-safe-dump --cookies`, a HAR). Sample values are elonmusk / 44196397 / 1349129669258448897; viewer-bound entries are recorded on the sandbox. TIAD's GraphQL.json is only a detector of changed queryIds.
- `tools/sweep_tweets.py` (broad strict sweep) and `tools/json_to_schema.py` (schema drafts; check its shared-type guesses, reduced users are not `User`) live in `/root/workspace/tools`.

## Generated clients
- Regeneration: in the generated directory, move the `twitter-openapi` submodule to the spec commit, bump the version in `tools/openapi-generator-config.yaml`, remove what `tools/win/clean.ps1` lists, run the generate command from `tools/win/gen.ps1`. TS additionally runs `tools/win/replace.py`, then restore the committed `package.json` (it carries hand-made ESM build fields) and bump only its version. Wrapper: bump version and generated dependency, pin the spec hash (`client.py` / `src/api.ts`), add typed helpers with e2e tests for new operations. Conventional commits: `generated: regenerate X from twitter-openapi <sha>`, `wrapper: X on generated X`, `wrapper: ...`.
- Publishing happens on push to the default branch. The TS lockfile can only resolve the new generated version after npm has it: a follow-up PR. twitter-snap then takes `^x.y.z` (its own packages are exempt from pnpm's minimumReleaseAge).
- The TS wrapper's `cookie.json` is not gitignored; the Python wrapper's is.

## twitter_api_safe_relay
- Everything the relay serves lives under `/i/api` like the X web app; dispatch paths inside are relative to `https://x.com/i/api`. `x-profile-name` selects a profile.
- Its tests and a throwaway relay for e2e take `X_COOKIE_FILE` through `twitter-api-safe-test-utils` (headless Chromium with the cookies added); `node file.ts` runs TypeScript directly on Node 24.
- The catalog `packages/server/requests.ndjson` is recorded with `twitter-api-safe-dump` (`--cookies`, `--headless`), merged line by line, `recordedAt` stamped.

## Other repos
- TwitterInternalAPIDocument: generator needs a cookie; docs on `develop`, merged to `master` by the scheduled workflow; branches `develop`, `legacy-twitter`, `for/kaonasi-biwa/Twitter-UI-Customizer`, `twitter-login`, `twitter-blue` must never be deleted.
- x-client-transaction-id-pair-dict: `pnpm start` yields 30 pairs in a few minutes without a proxy; pairs stay valid for weeks.
- twitter-snap: pnpm + biome + vitest; tests hit X as guest and need ffmpeg (BtbN builds; the johnvansickle static build segfaults on https input); `@vercel/og` stays 0.x; some media only serve `?name=orig`.
- pnpm 12 in CI: every dependency with a build script needs an `allowBuilds` entry; Dockerfiles must copy `pnpm-workspace.yaml`; a lockfile from an older 12.x breaks `--frozen-lockfile`.
