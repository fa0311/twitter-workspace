---
name: feedback-design-preferences-2026-10
description: fa0311's design calls - declarative typed definitions, no dead compatibility, POST where X uses it, recordings and guest runs on instruction only, no schema sharing across sites, enum policy, relay and clients ignorant of each other, simple GitHub Actions
metadata:
  type: feedback
---

- **Declarative over procedural**: registries are typed literal definitions, not registration calls (twitter-snap's render definitions).
- **No needless backward compatibility**: when the live API dropped a field, drop the fallback after a live check ("無駄な後方互換性は利用者が混乱するだけ").
- **POST wherever X was seen using it**; the placeholder tool keeps POST when a recording used it.
- **Guest-token runs and recordings happen on instruction, not on a schedule**: no nightly guest job, `twitter-api-safe-dump` / `update-placeholder` are manual (workflow_dispatch) so a human checks before placeholder values change.
- **Schema sharing is a risk** ("共通化はそこそこリスクがある"): reuse a schema only for the same backend object under the same key; a look-alike site gets its own type; never widen a shared type for another site.
- **Enum policy** ("腕の見せ所"; "重要な部分は攻めて、内部のどうでもいい値はどうでもいい"): enum when the value decides shape or branching, or is user-facing and closed; plain string with known values in a comment for UI plumbing. twitter-snap is the reference consumer. Written in twitter-openapi `CONTRIBUTING.md`.
- **Relay and clients know nothing of each other**: the typed clients only document that the endpoint is configurable; the relay README carries the recipe.
- **GitHub Actions stay simple and readable**: one `jq` line over shell gymnastics; an action's own option over a hand-rolled check.
- **TIAD**: avoid changes unless asked.

**Why:** these settle recurring judgement calls so they are not re-asked.

**How to apply:** apply them silently; when a new judgement call appears, decide in their spirit and say so. Related: [[user-fa0311-preferences]], [[feedback-twitter-ecosystem-working-rules]].
