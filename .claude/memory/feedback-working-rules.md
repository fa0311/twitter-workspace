---
name: feedback-working-rules
description: "How fa0311 wants delivery handled: what is delegated and what waits for approval, how work is ordered, how public replies sound, when not to build something"
metadata:
  type: feedback
---

- **Approval is explicit, delegation is by category.** A favourable remark approves nothing. Routine mechanical updates are delegated
  as a class, in every repository: verify, merge, report, and replace a failing one with a fix of my own.
- **No operation may destroy or pre-empt work that is still under review.** Order merges and clean-ups so that open work keeps its
  base and approved work never rides into unapproved work.
- **A known, harmless problem beats a workaround that can bring new bugs.** Fix at the source or leave it open and say why;
  anything further comes to the chat first.
- **Each package ships once.** Order work along the dependency chain; preparation may open early, releases wait for it.
- **When the semantics are debatable, do not build it.** No API beats an API with arguable defaults; such choices stay with the caller.
- **Say only what the artefact cannot say itself.** Code shows the what, git and the PR carry the why; comments, READMEs and CI
  steps hold no restatement, no history and no cleverness, and a tool's own option beats hand-rolled logic.
- **The public voice is the maintainer's.** Short and plain, without ceremony or any trace of automation; judgement, findings and
  open questions go to the chat, never to GitHub.
- **What spends the live account runs when someone starts it**, not on a schedule of my making.

**Why:** these settle recurring judgement calls so they are not re-asked.
**How to apply:** apply silently; decide a new case in their spirit and say which one decided it. The recipes and incidents behind
them are in `REFERENCE.md`. Related: [[user-fa0311]], [[feedback-design-preferences]], [[feedback-memory-style]].
