---
name: project-x-translation-2026-10
description: How x.com translates posts as of 2026-10-31 (embedded Grok translation keyed by x-twitter-client-language; no typeable endpoint) and what twitter-snap does with it
metadata:
  node_type: memory
  type: project
  originSessionId: d434b7bb-ffad-4bc5-9c3e-becfecbc4c6f
  modified: 2026-10-31T14:17:48.363Z
---

Recorded 2026-10-31 on the sandbox (`/root/workspace/recordings/translate/`, tools `record_translate.py`, `rest_call.py`):
- The x.com web client sends no translation request for posts. `TweetDetail` / `TweetResultByRestId` already carry
  `grok_translated_post_with_availability` (typed in twitter-openapi `tweet.yaml`); "Show original / Show translation" is client-side.
- The destination language is the request header `x-twitter-client-language` (en/de/fi/cs/hu verified; same language → `is_translatable: false`).
  Top-level posts translate on the fly; replies are often `is_available: false` until someone clicks on x.com.
- On-demand translation is `POST /2/grok/translation.json` (`{content_type:"POST", id, dst_lang}`), NDJSON stream without content-type:
  not consumable by the generated clients, so it is not in the spec. The strato `translateTweet` (Google) still answers but the web
  client no longer sends it (feature switches: grok translation on, x_translation / papago off) → not in the spec either (zero tolerance).
- Consequence: no spec or client change for translation; twitter-snap takes `--translate <lang>` and sets the header itself, rendering the
  embedded translation under the original text.

**Why:** avoids re-recording and re-deciding; explains why there is no translate operation in the spec.

**How to apply:** when translation comes up, point at the embedded field and the header; re-record only if x.com's client changes. Related: [[feedback-design-preferences-2026-10]], [[project-x-drift-2026-10]].
