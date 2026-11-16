#!/bin/sh
# Session bootstrap. The home directory is a docker volume and survives the container being recreated; everything outside it
# (apt packages, /tmp) does not, so tools are installed under ~/.local. A fresh clone on another machine has neither.
# Idempotent: initialises missing submodules, restores Claude's memory from the workspace mirror and the sandbox cookie from
# twitter-secrets, and prints an install line for every missing tool.
set -u
WS=$(cd "$(dirname "$0")/.." && pwd)
KEY=EAB5AF5AA7ED7A16C4027B5283A8A5E74872A8AA
SANDBOX_TWID=u%3D1787148517779406848   # @ptcpz3
# git signs through the wrapper in gpg.program (passphrase from the container's environment); plain gpg would wait on a pinentry
GPG=$(git config --get gpg.program || echo gpg)

for m in $(git -C "$WS" submodule status | awk '/^-/{print $2}'); do git -C "$WS" submodule update --init --recursive -- "$m"; done

MEM=$HOME/.claude/projects/$(printf %s "$WS" | tr -c 'A-Za-z0-9' '-')/memory
if [ ! -f "$MEM/MEMORY.md" ] && [ -f "$WS/.claude/memory/MEMORY.md" ]; then
  mkdir -p "$MEM" && cp "$WS"/.claude/memory/*.md "$MEM"/ && echo "memory restored from .claude/memory"
fi

# ~/.npm turned up owned by root in this volume, which makes every npm install fail with EACCES
[ ! -e "$HOME/.npm" ] || [ -O "$HOME/.npm" ] || sudo chown -R "$(id -un):" "$HOME/.npm"

need() { command -v "$1" >/dev/null 2>&1 && printf '%-6s ok  %s\n' "$1" "$(command -v "$1")" || printf '%-6s MISSING -> %s\n' "$1" "$2"; }
need java   "mkdir -p ~/.local/share/java ~/.local/bin && curl -fsSL https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jre/hotspot/normal/eclipse | tar -xz -C ~/.local/share/java && ln -sfn ~/.local/share/java/jdk-17*-jre/bin/java ~/.local/bin/java"
need uv     "curl -LsSf https://astral.sh/uv/install.sh | sh"
need node   "image tool (v26); other versions: unpack the nodejs.org tarball under ~/.local/node-versions/"
need pnpm   "npm i -g --prefix ~/.local pnpm@12"
need gh     "image tool; GITHUB_TOKEN is in the environment"
need sops   "gh release download -R getsops/sops -p 'sops-*.linux.amd64' -O ~/.local/bin/sops && chmod +x ~/.local/bin/sops"
need age    "sudo apt-get update && sudo apt-get install -y age   (gone again with the next image)"
need jq     "sudo apt-get update && sudo apt-get install -y jq   (gone again with the next image)"
need ffmpeg "sudo apt-get update && sudo apt-get install -y ffmpeg   (gone again with the next image)"
[ -f "$WS/twitter-openapi/openapi-generator-cli.jar" ] && echo "generator jar ok" || echo "generator jar MISSING -> curl -fsSL -o $WS/twitter-openapi/openapi-generator-cli.jar https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.26.0/openapi-generator-cli-7.26.0.jar"
[ -d "$HOME/.cache/ms-playwright" ] && echo "playwright browsers ok" || echo "playwright browsers MISSING -> (cd $WS/twitter-openapi && uv pip install playwright && uv run --no-sync playwright install chromium)"

echo t | timeout 20 "$GPG" --batch -bsau $KEY >/dev/null 2>&1 && echo "gpg signing ok ($GPG)" || echo "gpg signing FAILED -> tell the maintainer (GPG_PASSPHRASE or the key mount is missing from the container)"
gh auth status >/dev/null 2>&1 && echo "gh auth ok" || echo "gh auth MISSING"

# twitter-secrets is encrypted to the maintainer's PGP key as well as the CI age key, so the same wrapper decrypts it
if [ ! -s "$WS/cookie.json" ]; then
  (umask 077; SOPS_GPG_EXEC=$GPG sops decrypt --extract '["cookie_json"]' "$WS/twitter-secrets/secrets.enc.yaml" > "$WS/cookie.json") && echo "cookie.json restored from twitter-secrets"
fi
[ -e "$WS/twitter-openapi/cookie.json" ] || ln -s ../cookie.json "$WS/twitter-openapi/cookie.json"
[ "$(jq -r '.[] | select(.name == "twid") | .value' "$WS/cookie.json" 2>/dev/null)" = "$SANDBOX_TWID" ] && echo "cookie.json is the sandbox account @ptcpz3" || echo "cookie.json is MISSING or NOT @ptcpz3 -> do not use it"
