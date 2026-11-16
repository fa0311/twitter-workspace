---
name: user-fa0311
description: "Who the user is (fa0311 / ふぁ, solo maintainer of the Twitter/X OSS family, Japanese) and their stated preferences that are not rules in CLAUDE.md"
metadata:
  node_type: memory
  type: user
  originSessionId: d250dea8-b7d2-47de-8276-a31f9ac33735
  modified: 2026-11-16T04:46:27.514Z
---

GitHub **fa0311** (ふぁ, git email yuki@yuki0311.com), Japanese, solo maintainer of twitter-openapi and its clients, twitter-snap and
its apps, twitter_api_safe_relay, TwitterInternalAPIDocument, x-client-transaction-id-pair-dict, twitter-secrets. Wants Claude as a
hands-on co-maintainer: investigate deeply, implement, open PRs, decide routine calls alone; once enough evidence is gathered, proceed
without re-asking. Read the old sandbox's `screenshot/{date}/` folders from VS Code; since 2026-11-16 works with the agent through
T3 Code on a Kasm desktop container.

- **Libraries over hand-written code** ("I like using libraries for everything"); adding or removing dependencies is fine.
- **Favourite projects:** x-client-transaction-id-pair-dict and twitter_api_safe_relay ("genius approach"). Review their external PRs
  thoroughly and keep changes conservative.
- **TwitterFrontendFlow** is dead; never depend on it. **TIAD**: avoid changes unless asked.
- **twitter-secrets being public is approved**; cookies / proxies rotate there (age key per consuming repo), not per repo.
- Says "LGTM" to approve, "任せる" to delegate; "だいたい良く出来てる" is not an approval.

**Why:** avoids re-asking and keeps the tone of a trusted co-maintainer.
**How to apply:** see [[feedback-working-rules]], [[feedback-design-preferences]], [[feedback-account-budget]], [[feedback-screenshots]].
