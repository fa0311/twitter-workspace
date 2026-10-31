---
name: feedback-design-preferences-2026-10
description: "fa0311's design calls - declarative typed definitions, no dead compatibility, POST where X uses it, recordings and guest runs on instruction only, no schema sharing across sites, enum policy, relay and clients ignorant of each other, simple GitHub Actions"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0650167e-5ffa-4364-b61a-870599f5819c
  modified: 2026-10-30T16:40:29.726Z
---

- **Declarative over procedural**: registries are typed literal definitions, not registration calls (twitter-snap's render definitions).
- **No needless backward compatibility**: when the live API dropped a field, drop the fallback after a live check ("無駄な後方互換性は利用者が混乱するだけ").
- **POST wherever X was seen using it**; the placeholder tool keeps POST when a recording used it.
- **Guest-token runs and recordings happen on instruction, not on a schedule**: no nightly guest job, `twitter-api-safe-dump` / `update-placeholder` are manual (workflow_dispatch) so a human checks before placeholder values change.
- **Schema sharing is a risk** ("共通化はそこそこリスクがある"): reuse a schema only for the same backend object under the same key; a look-alike site gets its own type; never widen a shared type for another site.
- **Enum policy** ("腕の見せ所"; "重要な部分は攻めて、内部のどうでもいい値はどうでもいい"): enum when the value decides shape or branching, or is user-facing and closed; plain string with known values in a comment for UI plumbing. twitter-snap is the reference consumer. Written in twitter-openapi `CONTRIBUTING.md`.
- **Relay and clients know nothing of each other**: the typed clients only document that the endpoint is configurable; the relay README carries the recipe.
- **GitHub Actions stay simple and readable**: one `jq` line over shell gymnastics; an action's own option over a hand-rolled check.
- **twitter-snap wraps text like a browser (UAX #14), no prettier**: phrase-level Japanese wrapping (BudouX / `word-break: auto-phrase`) was offered with sample images and declined ("不要", 2026-10-30). Images should break lines where X.com does.
- **TIAD**: avoid changes unless asked.
- **Feature ideas 2026-10-31**: the maintainer approved the idea list (twitter-snap poll / Community Notes rendering and thread mode, client pagination iterators and relay session helper, translation API after recording, MCP snap tool, relay rate-limit visibility, spec candidates from the relay catalog) and declined a catalog freshness check in CI (`recordedAt` age warning): not wanted. **X reference theme (approved 2026-10-31, "いいね！")**: a twitter-snap theme that reproduces the x.com tweet layout from measured values; it may share code with the existing themes and the existing themes' design may shift slightly as a result ("既存テーマと共通化してもいいよ、既存テーマのデザインが若干変わっても良い"). Translation, when it comes, takes the target language as an explicit argument (`--translate <lang>` style): X now renders in the viewer's translation language by default, so an implicit default would be ambiguous (2026-10-31).

**Why:** these settle recurring judgement calls so they are not re-asked.

**How to apply:** apply them silently; when a new judgement call appears, decide in their spirit and say so. Related: [[user-fa0311-preferences]], [[feedback-twitter-ecosystem-working-rules]].
