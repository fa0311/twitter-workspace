---
name: project-ci-pitfalls-pnpm12-ffmpeg
description: CI failure causes found 2026-10-15 in fa0311's Node repos - pnpm 12 ignored-builds error and lockfile packageManagerDependencies, johnvansickle static ffmpeg segfault on https input, biome CRLF failures on Windows runners
metadata:
  type: project
---

CI pitfalls met on 2026-10-15 while greening twitter-snap #68 and the pnpm-based repos:

- **pnpm 12 in CI (`CI=true`) turns "Ignored build scripts" into `ERR_PNPM_IGNORED_BUILDS`.** Every dependency with a build script must appear in `pnpm-workspace.yaml` `allowBuilds` (`true` or `false`). `sharp` (via `@vercel/og`) needs `sharp: false`; its binaries are optional deps.
- **pnpm 12.11 lockfiles have a leading `---` document with `packageManagerDependencies` (`@pnpm/exe.*`).** A lockfile written by an older 12.x makes `pnpm install --frozen-lockfile` fail with `ERR_PNPM_FROZEN_LOCKFILE_WITH_OUTDATED_LOCKFILE` ("Cannot update packageManagerDependencies"). Fix: `pnpm install --lockfile-only` with the pinned pnpm and commit. Check with `CI=true pnpm install --frozen-lockfile` locally; the snap-api / bookmarklet / discord PRs have no CI (docker build only on push).
- **`FedericoCarboni/setup-ffmpeg@v3` installs johnvansickle's static ffmpeg on Linux, which segfaults (exit 139) on any https input** (first ffmpeg call of twitter-snap's video path). BtbN builds (`AnimMouse/setup-ffmpeg@v1`, Linux + Windows) and apt ffmpeg 6.1 work; twitter-snap passes 49/49 with BtbN 9.0. twitter-snap master's `tests` workflow had been red for this reason.
- **biome `check` fails on Windows runners when git checks out CRLF.** `.gitattributes` with `* text=auto eol=lf` (and `*.cmd text eol=crlf` for `bin/dev.cmd`) fixes it.
- Sandbox shell: zsh has an alias `g`; parallel Bash calls share the cwd, so use absolute paths / `git -C`.

**Why:** these took most of a night to pin down; they recur in every pnpm/ffmpeg repo of the user.

**How to apply:** before pushing a pnpm change run `CI=true pnpm install --frozen-lockfile`; never add the johnvansickle action back; keep `.gitattributes` in repos with biome. Related: [[project-x-drift-2026-10]], [[project-twitter-ecosystem-standing-tasks]].
