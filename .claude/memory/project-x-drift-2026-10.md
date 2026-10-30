---
name: project-x-drift-2026-10
description: Durable facts about X's API drift in Oct 2026 and where the ecosystem stands (spec, clients, relay versions); the PR-level history is in git
metadata:
  type: project
---

X facts that still shape the work (verified Oct 2026):
- New GraphQL query versions drop `User.legacy`; its replacements are typed in the spec. Old queryIds keep answering for a while, so stale ids are a quiet drift, not an outage.
- Logged-out x.com is static HTML with no scripts; guest-token GraphQL still works. Transaction ids come from x-client-transaction-id-pair-dict.
- `UserByRestId` / `UsersByRestIds` answer 403 to every non-browser client; other users' likes are empty. The web app calls REST under `/i/api/1.1/...` too.
- Enum values X keeps extending (Community Notes icons, feedback kinds, conversation sections) show up in every sweep; the enum policy in twitter-openapi `CONTRIBUTING.md` decides enum vs string.
- The X bundle defines operations in two styles; TwitterInternalAPIDocument parses only one, so "gone from TIAD" never means gone. TIAD is a drift detector, never a source of placeholder values.

Where things stand (2026-10-30): clients 0.1.4 shipped from spec 8535fd9 (PyPI + npm); spec main 24b82ab adds #136 (ad click tracker override, mention user without core); follow-ups twitter-openapi-typescript #163 and twitter-snap #85 await LGTM; nightly fixes so far all came from notifications or ads;

**Why:** the next session should start from the state, not rediscover it; the history is in the repos.

**How to apply:** read `/root/workspace/HANDOVER.md` §4 for the current state and update it (and this file) when it changes. Related: [[project-twitter-ecosystem-standing-tasks]], [[feedback-design-preferences-2026-10]].
