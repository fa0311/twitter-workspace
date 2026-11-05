---
name: feedback-sandbox-account-only
description: Every live call, recording and test uses the sandbox account @ptcpz3 in cookie.json; verify the account before touching X and never print cookie values
metadata:
  type: feedback
---

`/root/workspace/cookie.json` holds the session of the sandbox account **@ptcpz3**, the only account this workspace may drive. Before recording, testing or rotating secrets, confirm the session is that account (for example `UserByScreenName` for the viewer, or the `twid` cookie), and keep every copy (worktrees, wrapper test dirs, the sops secret) in step with it. Never print cookie values.

Lock symptom (seen 2026-10-20): GraphQL answers 200 with data plus `errors[].code 326` and `bounce_location: https://twitter.com/account/access`; web pages redirect to `/account/access` behind a Cloudflare challenge, so HTML scrapers (TwitterInternalAPIDocument's generator) find no scripts. Only the maintainer can clear it (challenge / phone check in a browser); then export a fresh cookie, update `cookie.json`, the sops secret in twitter-secrets and every local copy. Heavy automated use of the account (sweeps, relay suites, nightlies) is the likely trigger: space them out.

**Why:** the generated clients and the relay are tested against this account by many sessions; a wrong session would mix another account's data into recordings and placeholders.

**How to apply:** check the account once at session start, treat any other session as wrong and stop. Related: [[feedback-twitter-ecosystem-working-rules]].

**Third lock, 2026-11-04:** the day held the nightly (130 calls), four cookie renders, one python e2e suite (85 calls) and then two pushes to a twitter_api_safe_relay PR, whose CI opens a live browser session with the account on three Node versions each (6 logins from the CI proxies within an hour). Count relay PR pushes as live use (3 sessions per push) and keep them off days that already had a suite; the lock shows up in that CI as `runs graphQLFullResponse through a persistent X profile` timing out after 120 s.

**Recording clicks (2026-11-05):** for twitter-openapi #131 the maintainer said "これはMCPとかで出来るでしょ？サンドボックス環境だよここ": a UI action that only affects the sandbox account's own state (a "Not interested" click on a timeline post, then Undo) may be driven with Playwright when a recording needs it; still undo it in the same run and say what was clicked.
