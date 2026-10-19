---
name: feedback-twitter-ecosystem-working-rules
description: "Standing working rules from fa0311 for Twitter-ecosystem maintenance sessions - open PRs (stacked OK), review/triage read-only and report in chat, GPG-signed commits, match existing style with minimal error handling, full sandbox autonomy"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a32787d9-001f-49d1-ab30-d8c817e246f9
  modified: 2026-10-15T10:08:56.421Z
---

Rules the user gave (2026-10-15) and said will be repeated every session:

- **Deliver as PRs.** Go all the way to opening PRs on GitHub. Multiple PRs and stacked PRs are fine.
- **Review & triage are read-only.** Review open PRs and triage issues, but never post comments/labels on GitHub. Report findings to the user in chat.
- **GPG signing is mandatory** on every commit (`commit.gpgsign=true` is set; verify with `git log --show-signature`).
- **Match the existing code style.** Keep error handling minimal, as the codebases already do. Do not add defensive layers.
- **Twitter/X changes constantly.** Part of every session is checking for API/schema drift and following it.
- **Sandbox, full delegation.** Install any tools/MCP freely. The environment is wiped on sandbox restart, so anything that must persist goes into the repos or `/root/workspace` (mounted volume).
- **Unlimited effort budget.** Investigate thoroughly. Deleting unnecessary features is allowed. Once enough evidence is gathered, assume the conclusion holds and proceed without re-asking.

**Why:** The user is a solo maintainer of many repos and wants Claude to behave like a trusted co-maintainer, not an assistant that stops to ask.

**How to apply:** Start sessions with `/root/workspace/HANDOVER.md` and `sh tools/bootstrap.sh`, then work through [[project-twitter-ecosystem-standing-tasks]]. Related: [[user-fa0311-twitter-oss-maintainer]].
