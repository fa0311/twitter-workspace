---
name: feedback-stacked-pr-merging
description: How to merge fa0311's stacked PRs without closing the children - retarget child PRs before deleting the merged head branch; user merges with merge commits
metadata:
  type: feedback
  originSessionId: a32787d9-001f-49d1-ab30-d8c817e246f9
  modified: 2026-10-15T17:30:00.000Z
---

Learned 2026-10-15 while merging twitter-openapi #108 → #107 → #106 bottom-up on request.

- `gh pr merge --merge --delete-branch` on a stacked PR **closes every open PR whose base was the deleted head branch** (GitHub did not retarget #109; it was closed with base `feat/user-timelines`). A closed PR's base cannot be changed, so recovery means recreating the branch at its old tip (`git push origin <sha>:refs/heads/<name>`), `gh pr reopen`, PATCH the base, then delete the branch again.
- Correct order: `gh api -X PATCH repos/<r>/pulls/<child> -f base=<new base>` for every child first, then merge the parent, then delete the head branch.
- fa0311 merges with **merge commits** (twitter-openapi #102, safe_relay #30/#32 all have 2 parents); match that, not squash.
- The user says "マージしていいよ" only for PRs they explicitly LGTM'd; "だいたい良く出来てる" is not an LGTM.
- **Do not merge LGTM'd children into a parent that is still under review.** Doing so (#108 → #107 → #106 on 2026-10-15) only made #106's diff harder to read; the user let it pass once ("今回はいいけど次から気をつけて"). Wait for the bottom PR's LGTM, then merge bottom-up into main.

**Why:** avoids losing PRs and keeps the review history the user expects.

**How to apply:** before any `--delete-branch`, list open PRs with that base (`gh pr list --base <branch>`) and retarget them. Related: [[feedback-twitter-ecosystem-working-rules]], [[project-x-drift-2026-10]].
