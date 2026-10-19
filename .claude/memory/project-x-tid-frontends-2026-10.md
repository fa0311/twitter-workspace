---
name: project-x-tid-frontends-2026-10
description: As of 2026-10-19 logged-out x.com/home serves the new x-web app, /i/jf/ still serves the responsive-web shell; X does not enforce x-client-transaction-id on UserByScreenName; Lqm1/x-client-transaction-id 0.3.2 verified e2e against the real frontend
metadata:
  type: project
---

Observed 2026-10-19 while verifying Lqm1/x-client-transaction-id (jsr @lami/x-client-transaction-id, npm 0.3.2):

- Logged-out `x.com/home` in a browser lands on `/i/jf/onboarding/web` served by the new **x-web** app (`abs.twimg.com/x-web/x-web/entry-client-logged-out-*.js`, Rolldown build, no `webpackChunk_twitter_responsive_web`, no `loading-x-anim` SVGs in the DOM). It still hashes `METHOD!path!time` + `obfiowerehiring` + animationKey, so the pair-dict digest hook keeps working (`PAIR_MAX=2 pnpm start` produced pairs that day).
- `https://x.com/i/jf/` (what Lqm1's `fetchXDocument` reads) and the logged-in `/home` are still the **responsive-web** shell: ~305 KB HTML with the inline webpack runtime, `twitter-site-verification` meta, 4 `loading-x-anim` frames.
- `x-client-transaction-id-extract-browser` 0.0.3: `initKeyConverter` (digest hook) works on both shells; `initIdConverter` / `createSessionOverride` fail (`webpackChunk...find(...)` has no `ondemand.s` entry on the current pages). pair-dict only uses the hook, so it is unaffected.
- The real frontend hashes the URL pathname as is: `/i/api/graphql/<id>/<Op>` on x.com, `/1.1/...` on api.x.com, `/onboarding/web` for `x.com/i/jfapi/onboarding/web`.
- X did **not** reject missing / garbage / wrong-key transaction ids on `UserByScreenName` (guest on api.x.com and logged-in on x.com/i/api) from the sandbox IP, so an "API accepted it" test proves nothing; compare against the frontend's own headers instead.
- Lqm1 0.3.2 result: identical payloads to `x-client-transaction-id-generater` for 2,400 (pair.json × method × path × time) cases, same key + animationKey as the frontend on 12 pages, identical payload to 52 headers the page itself sent. Scripts were in the session scratchpad (`t1_encode.mjs`, `t2_oracle.mjs`, `t3_*.mjs`, `t4_loggedin_oracle.mjs`).

**Why:** the maintainer asked for an e2e verdict on a third-party implementation; these facts about X's two frontends and the non-enforcement decide which oracle is valid. Related: [[project-x-frontend-bundle-facts]], [[project-x-drift-2026-10]].
