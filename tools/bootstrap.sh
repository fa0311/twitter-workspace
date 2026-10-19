#!/bin/sh
# Session bootstrap for a fresh container (only /root/workspace survives `docker compose up` recreating it).
# Idempotent: restores Claude's memory from the workspace backup, prepares GNUPGHOME for sops, and reports
# which tools are missing with the install line that worked before.
set -u
# the bind mount is owned by the host user; git refuses to touch it as root without this
git config --global --get-all safe.directory 2>/dev/null | grep -qx /root/workspace || git config --global --add safe.directory /root/workspace
MEM=/root/.claude/projects/-root-workspace/memory
if [ ! -f "$MEM/MEMORY.md" ] && [ -f /root/workspace/.claude/memory/MEMORY.md ]; then
  mkdir -p "$MEM" && cp /root/workspace/.claude/memory/*.md "$MEM"/ && echo "memory restored from /root/workspace/.claude/memory"
fi
# sops needs a writable GNUPGHOME; the mounted /root/.gnupg files are read-only (see .sops/env.sh)
if [ ! -d /root/.gnupg-rw ]; then
  mkdir -m700 /root/.gnupg-rw && cp -r /root/.gnupg/private-keys-v1.d /root/.gnupg/pubring.kbx /root/.gnupg/trustdb.gpg /root/.gnupg-rw/ && echo "/root/.gnupg-rw created"
fi
need() { command -v "$1" >/dev/null 2>&1 && printf '%-6s ok  %s\n' "$1" "$(command -v "$1")" || printf '%-6s MISSING -> %s\n' "$1" "$2"; }
need java  "apt-get install -y openjdk-17-jre-headless   (openapi-generator-cli.jar 7.26.0 sits in each twitter-openapi worktree)"
need uv    "curl -LsSf https://astral.sh/uv/install.sh | sh"
need node  "apt-get install -y nodejs (v24) ; npm i -g pnpm@12"
need pnpm  "npm i -g pnpm@12"
need gh    "download the linux_amd64 tarball from https://github.com/cli/cli/releases/latest and install gh to /usr/local/bin (GITHUB_TOKEN is in the env; ~/.config/gh is mounted)"
need sops  "curl -LO https://github.com/getsops/sops/releases/latest/download/sops-v3.x.linux.amd64 ; install -m755 ... /usr/local/bin/sops"
need age   "apt-get install -y age  (or the GitHub release)"
need jq    "apt-get install -y jq"
[ -d /root/.cache/ms-playwright ] && echo "playwright browsers ok" || echo "playwright browsers MISSING -> (cd /root/workspace/twitter_api_safe_relay && pnpm exec playwright install chromium)"
echo t | gpg --batch -bsau EAB5AF5AA7ED7A16C4027B5283A8A5E74872A8AA >/dev/null 2>&1 && echo "gpg signing ok" || echo "gpg LOCKED -> ask the user to unlock it from a VS Code terminal (echo t | gpg --clearsign -u EAB5AF5AA7ED7A16C4027B5283A8A5E74872A8AA)"
gh auth status >/dev/null 2>&1 && echo "gh auth ok" || echo "gh auth MISSING"
[ -f /root/workspace/cookie.json ] && echo "cookie.json present (must be the sandbox account @ptcpz3)" || echo "cookie.json MISSING"
