---
name: user-fa0311-preferences
description: "fa0311's stated preferences - loves using libraries over hand-rolled edge-case code, favorite projects are x-client-transaction-id-pair-dict and twitter_api_safe_relay, TwitterFrontendFlow is dead, protected archive branches in TwitterInternalAPIDocument"
metadata:
  node_type: memory
  type: user
  originSessionId: a32787d9-001f-49d1-ab30-d8c817e246f9
  modified: 2026-10-15T16:50:00.000Z
---

Stated by the user on 2026-10-15:

- **Libraries over hand-written code.** "I like using libraries for everything" because researching standards (IEEE etc.) and writing edge-case code is tedious. Adding or removing dependencies is fine.
- **Favorite projects:** x-client-transaction-id-pair-dict and twitter_api_safe_relay ("genius approach, one of a kind"). Treat them with extra care; review their external PRs thoroughly.
- **TwitterFrontendFlow** is an old, unmaintained project. Do not depend on it (removed from TwitterInternalAPIDocument in favor of native cookie loading).
- **Branches that must never be deleted** in TwitterInternalAPIDocument: `develop` (generator output branch), `legacy-twitter`, `for/kaonasi-biwa/Twitter-UI-Customizer` (in use), `twitter-login`, `twitter-blue` (archives). Other repos' merged `dev`/`develop` branches were deleted on 2026-10-15 with permission; PRs now always target master/main.
- **Credentials:** cookies/proxies live in the shared sops repo fa0311/twitter-secrets (age key per consuming repo as `SOPS_AGE_KEY`, maintainer PGP as second recipient). Rotate there, not per repo.
- **GPG:** the signing key is passphrase-protected; the sandbox gpg-agent needs a one-time unlock from a VS Code terminal (TTL set to 400 days in /root/.gnupg/gpg-agent.conf). Check `echo t | gpg --batch -bsau <key>` emits a signature before committing.

- **twitter-openapi has zero tolerance for mistakes** (stated 2026-10-15): a wrong spec/placeholder harms the accounts of the many users of the generated clients. Be conservative there: only apply values recorded from the real frontend, never guess, verify live before proposing, and say plainly what is and is not verified.
- **placeholder.json values come only from recordings of the real web client** (the relay's request catalog / dump, HAR), applied with `tools/update_placeholder.py`, on the maintainer's instruction. TIAD is speed-first and may be wrong; twitter-openapi must not depend on it.
- **READMEs should not carry CI-only notes.** Cookie/proxy/secrets plumbing belongs in the workflow files and the twitter-secrets repo, not in a project README ("ドキュメントとして残す価値がない", 2026-10-15).
- **twitter-secrets being public is approved.**

**Why:** avoids re-asking and prevents accidental deletion of in-use branches.

**How to apply:** prefer well-maintained libraries, keep pair-dict/safe_relay changes conservative, verify GPG works at session start. Related: [[feedback-twitter-ecosystem-working-rules]], [[project-twitter-ecosystem-standing-tasks]].
