---
name: project-twitter-ecosystem-standing-tasks
description: Standing tasks for fa0311's Twitter-ecosystem sandbox and the environment facts that are not in CLAUDE.md or HANDOVER.md
metadata:
  type: project
---

Standing tasks (since 2026-10-15, recurring): follow X API drift (nightly strict test, sweeps, TIAD as detector); keep the generated clients and twitter-snap current after spec batches; dependency bumps; twitter-snap type-safety; keep Python projects on uv.

Environment: repos under `/root/workspace/<repo>`, each its own git repo; two spec worktrees carry the venv / generator jar / sandbox cookie. `GITHUB_TOKEN` drives `gh` and pushes but lacks GraphQL scopes (merge, retarget, body edits go through `gh api` REST). Only `/root/workspace` survives a container recreate; memory is mirrored in `/root/workspace/.claude/memory/` and restored by `tools/bootstrap.sh`. Publishing is automatic on push to the default branch (PyPI / npm trusted publishing, ghcr for the relay).

**Why:** saves the rediscovery cost each session.

**How to apply:** start with `/root/workspace/HANDOVER.md` and `sh tools/bootstrap.sh`; non-derivable facts are in `/root/workspace/REFERENCE.md`. Related: [[feedback-twitter-ecosystem-working-rules]], [[project-x-drift-2026-10]].
