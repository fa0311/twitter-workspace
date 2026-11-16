---
name: feedback-design-preferences
description: "fa0311's design calls for the spec, clients and twitter-snap - typing policy, schema sharing, enum policy, what a snapshot is, README policy, ffmpeg is the user's, translation UI"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d250dea8-b7d2-47de-8276-a31f9ac33735
  modified: 2026-11-16T04:46:29.934Z
---

Spec and clients
- **Declarative over procedural**: registries are typed literal definitions, not registration calls.
- **No needless backward compatibility**: when the live API dropped a field, drop the fallback after a live check ("無駄な後方互換性は利用者が混乱するだけ").
- **POST wherever X was seen using it**; the placeholder tool keeps POST when a recording used it.
- **Schema sharing is a risk** ("共通化はそこそこリスクがある"): reuse a schema only for the same backend object under the same key; never widen a
  shared type for a look-alike site.
- **Enum policy** ("重要な部分は攻めて、内部のどうでもいい値はどうでもいい"): enum when the value decides shape or branching or is user-facing and
  closed; plain string with known values in a comment for UI plumbing. twitter-snap is the reference consumer. Written in `CONTRIBUTING.md`.
- **Relay and clients know nothing of each other**: the clients only document that the endpoint is configurable; the relay README has the recipe.
- A list that grows without bound (per-endpoint rate limits) gets its own page with a filter, not a sidebar panel (relay dashboard).

twitter-snap
- **A snapshot is not the web page** ("全く同じUIにすることは出来ない。してしまうとあとから見返した時に見づらくなる"): the X reference theme copies
  x.com's type, colors and spacing; anything that only works on an interactive page (carousels, relative times, controls) is adapted or
  dropped. Plain themes must not depend on when the snap was taken (no views, a running poll shows choices + end date); the X reference
  theme may (views, counts, time left). Both keep media complete: photos stacked at full width at their own proportions, videos one
  after another; no carousel ("致命的" because media falls out of the picture). Dates always carry the year.
- Text wraps like a browser (UAX #14); phrase-level Japanese wrapping (BudouX) was declined ("不要").
- Translation looks like x.com's translated post: the translation replaces the text with the Grok-marked "Translated from <language>" line;
  the X reference theme also copies "Show original" / gear / "Rate this translation". `--translate <lang>` is explicit, never implicit.
- **ffmpeg is the user's** ("エンジニアが使う前提でいいし、ffmpeg とかユーザーに責務を押し付けたい"): no codec / container / quality tables; ffmpeg
  picks the encoder from the container, `--ffmpegAdditonalOption` carries the rest, even "does this container hold audio" is asked from
  ffmpeg. Pick the default with the smallest implementation ("規定にするのは実装軽い方にして").
- **README stays a list of one-line examples** ("READMEいじる意味ある？"): a feature gets `# comment` + command; no paragraphs, no per-feature
  images in `docs/img`, no version notes ("それはgitから確認できるでしょうに"), no sections for transparent behaviour (`/health`, passed-through
  headers). The PR description explains.
- Existing themes may shift slightly when code is shared with a new theme ("既存テーマのデザインが若干変わっても良い").

**Why:** these are the maintainer's taste, not derivable from the code.
**How to apply:** apply silently and decide new cases in their spirit. Related: [[feedback-working-rules]], [[feedback-screenshots]].
