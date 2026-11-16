---
name: feedback-account-budget
description: "The sandbox account @ptcpz3 is the only account to drive; what locked it (four times, Oct-Nov 2026) and what the maintainer allows on it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d250dea8-b7d2-47de-8276-a31f9ac33735
  modified: 2026-11-16T04:46:29.123Z
---

`cookie.json` is **@ptcpz3**; confirm the session is that account before recording or testing (`UserByScreenName` for the viewer or the
`twid` cookie, `u%3D1787148517779406848`), never print values. Since 2026-11-16 the file is restored from the sops secret by
`tools/bootstrap.sh` and linked, not copied, into the checkouts that need it.

Locks (code 326) so far: 2026-10-20 (sweeps), 10-26, 11-04 (nightly + four cookie renders + a python e2e suite + two relay PR pushes
= 6 CI logins in an hour), 11-13 (two relay Dependabot merges in one morning = ~12 CI logins). Hence the budget in CLAUDE.md: nightly
plus one suite per day, one relay merge per day, relay pushes count as 3 logins. Only the maintainer clears a lock.

Allowed on the account (2026-11-05, "これはMCPとかで出来るでしょ？サンドボックス環境だよここ"): UI actions that only touch the sandbox account's own
state (a "Not interested" click, a test tweet, a list) may be driven with Playwright when a recording needs them, undone in the same run,
and reported.

**Why:** the clients and the relay are tested against this account by many sessions; a lock stops the nightly and every suite.
**How to apply:** count logins before starting anything live; when the relay's CI login times out after 120 s, it is the lock, not the code.
Related: [[feedback-working-rules]].
