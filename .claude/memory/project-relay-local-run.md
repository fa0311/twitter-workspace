---
name: project-relay-local-run
description: How to run twitter_api_safe_relay in the sandbox with the @ptcpz3 session for reviews (tools/relay_local, port 3777) and the two ways it silently hangs
metadata:
  type: project
---

Recipe (2026-11-01, written for "手元で見たいからサーバー建てて"): `tools/relay_local/seed.cjs` seeds a persistent headless Chromium profile
from `cookie.json`, `tools/relay_local/settings.json` runs one `launch` profile named `sandbox` on 127.0.0.1:3777 with the dashboard;
start `node packages/server/dist/server.js <settings>` from the built checkout (`pnpm build` first). The maintainer opens it through a
VS Code port forward (`http://localhost:3777/`, `/health`). Full commands in `tools/README.md`.

Pitfalls: (1) `context.addCookies` without `expires` creates session cookies that are gone once the seeding context closes, so the relay
opens x.com logged out and every `/i/api/*` request hangs forever (`waitStartup` has no timeout) while `/health` keeps answering; seed
with `expires`, and verify by reopening the profile. (2) `pkill -f 'dist/server.js'` matches the shell that is about to start the relay.
(3) The first request launches the browser, so it takes a few seconds; later ones ~2 s.

**Why:** reproducing a logged-in relay in the sandbox cost an hour the first time; the hang looks like a relay bug but is the profile.

**How to apply:** reuse the tools files; when relay requests hang but `/health` works, check the profile's login state first. Related: [[project-twitter-ecosystem-standing-tasks]], [[feedback-sandbox-account-only]].
