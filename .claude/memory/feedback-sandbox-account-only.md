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
