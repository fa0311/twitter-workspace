---
name: feedback-sandbox-account-only
description: Only the sandbox account @ptcpz3 may be used for recording, tests and CI; the twitter-snap production account must never appear in cookies, placeholders or catalogs
metadata:
  type: feedback
---

On 2026-10-16 the session in `cookie.json` (and every copy: worktrees, wrapper test dirs, the sops `cookie_json` secret) turned out to be the user's **production twitter-snap account** (user id 1788224200639160320, @0y1kOJxopr65402). The user replaced it with the **development sandbox account @ptcpz3**, which the strict harness already expects (`UserByScreenName == "ptcpz3"`).

**Why:** recordings put the logged-in account's id / screen name into placeholder.json, the relay catalog and generated docs (ListOwnerships, UsersVerifiedAvatars, GenericTimelineById's base64 timelineId, Likes, ProfileSpotlightsQuery, ...), and tests mutate the account.

**How to apply:** before any recording, test or sops rotation, check the `twid` cookie of the file in use is not the production id; never print cookie values; scrub the production identifiers from anything public (placeholder, catalog, docs) and re-record on the sandbox account. Copies of cookie.json live in twitter-openapi, twitter-openapi-browser-only, TwitterInternalAPIDocument, twitter-snap-api, twitter_openapi_python/twitter_openapi_python, twitter-openapi-typescript/twitter-openapi-typescript (cookies.json). See [[user-fa0311-preferences]].
