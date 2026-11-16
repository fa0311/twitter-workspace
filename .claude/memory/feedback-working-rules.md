---
name: feedback-working-rules
description: "How fa0311 wants PRs, merges, issues and releases handled beyond the rules in CLAUDE.md - stacked PR recovery, Dependabot delegation, issue reply voice, fewer releases, no overrides, no debatable helpers"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d250dea8-b7d2-47de-8276-a31f9ac33735
  modified: 2026-11-16T04:46:28.294Z
---

- **Stacked PRs** (2026-10-15): `gh pr merge --delete-branch` closes every open PR based on the deleted branch and a closed PR's base
  cannot be changed; recovery is `git push origin <sha>:refs/heads/<name>`, `gh pr reopen`, PATCH the base. Retarget children first
  (`gh api -X PATCH repos/<r>/pulls/<n> -f base=<new>`), merge bottom-up into main, never LGTM'd children into a parent still under
  review ("今回はいいけど次から気をつけて").
- **Dependabot is delegated** (2026-10-31 "dependabotのマージは任せる", 2026-11-12 restated): merge after CI, merge commits, no per-PR LGTM;
  a grouped PR that fails gets an own PR with the fix (same bumps, superseding it). Relay merges cost 3 live logins each.
- **No overrides for security alerts** (2026-11-05: "よっぽどのことがない限りオーバーライドはできるだけしたくない / 変なバグに当たる可能性があるし、
  実害ないから放置されている可能性がある"): fix inside the parents' ranges or by bumping the parent, otherwise leave the alert open and say
  why. Stated exception: a critical vulnerability upstream is not maintaining — bring it to the chat first.
- **Fewer releases** (2026-11-05 "リリース回数減らしたいので実施する順番気をつけてね"): order work along spec → clients → twitter-snap → apps so each
  package ships once; lockfile / docs PRs may still open early.
- **Issue replies** (2026-10-23, when asked to triage): one or two plain sentences in the maintainer's voice, no greetings, lists or mention
  of automation ("AIだとバレないように端的に対応して"); close with the right reason; open questions come back to the chat. The token cannot
  transfer issues: open a copy in the target repo and close the original with "Moved to …".
- **No helper whose semantics are debatable** (2026-10-31, pagination PRs closed: "議論の余地があるなら実装しないほうが良い"): cursor loops, limits,
  rate-limit waits are the caller's; prefer no API over one with arguable defaults.
- **No comments that restate the code** (2026-11-07 "こういうコメント要らない"); a comment carries only what the code cannot say (unit, external
  quirk, recorded fact); the why goes in the commit or PR body.
- **GitHub Actions stay simple**: one `jq` line over shell gymnastics; an action's own option over a hand-rolled check. Recordings and
  guest runs are manual (`workflow_dispatch`), never scheduled.
- Reviews and triage are read-only on GitHub; findings go to the chat with PR links (in CLAUDE.md, repeated here because it was said
  "every session").

**Why:** these settle recurring judgement calls so they are not re-asked.
**How to apply:** apply silently; when a new call appears, decide in their spirit and say so. Related: [[user-fa0311]], [[feedback-design-preferences]].
