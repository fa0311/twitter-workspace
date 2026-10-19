---
name: project-x-frontend-bundle-facts
description: Logged-out x.com is static HTML (guest GraphQL still works); the frontend bundle defines operations in two styles and TwitterInternalAPIDocument parses only one, so TIAD cannot prove an operation is gone
metadata:
  type: project
---

- Logged-out x.com pages are server-rendered HTML with no scripts, so nothing "guest" can be recorded from a browser; guest-token GraphQL (`getGuestClient()`) still works and the wrappers keep guest mode.
- The logged-in bundle (`abs.twimg.com/responsive-web/client-web/*.js`, chunk map in the `/home` HTML) defines operations as `queryId/operationName` literals and as Relay `params:{id,name,...}` objects; TIAD parses only the former. Scan the bundle (or record) before calling an operation dead.
- Typing-triggered operations are reachable via URLs (`/i/lists/search?q=`, `/i/communities/suggested?q=`); bookmarks search needs its own button. Setting an X Chat passcode (needed for DM search) is forbidden.

**Why:** a TIAD-based "35 operations are gone" claim was wrong for 28 of them.

**How to apply:** treat TIAD as a detector of change, verify liveness by recording. Related: [[project-x-drift-2026-10]].
