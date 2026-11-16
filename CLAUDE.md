# fa0311 X (Twitter) ecosystem workspace

Workspace of fa0311 (ふぁ), maintainer of twitter-openapi, twitter-openapi-typescript, twitter_openapi_python, TwitterInternalAPIDocument, twitter-snap (+ -api/-discord/-bookmarklet), twitter_api_safe_relay (+_skills), x-client-transaction-id-pair-dict, twitter-secrets. Reply in Japanese. Non-derivable facts about the sandbox, X and the repos live in `REFERENCE.md`; local scripts are indexed in `tools/README.md`.

Start every session with `HANDOVER.md` (environment, routine, current state) and `sh tools/bootstrap.sh`. The workspace is `/home/kasm-user/twitter-workspace`. The home directory survives the container being recreated; the system around it (apt packages, `/tmp`) does not, so tools are installed under `~/.local`. Only git survives a move to another machine: Claude's memory is mirrored in `.claude/memory/` (bootstrap restores it; copy the memory directory back there after changing it), local scripts are in `tools/`; `recordings/` and `cookie.json` are untracked. Commit and push the workspace repo (signed) after changing docs or memory; the history of `HANDOVER.md` is its git log.

## Delivery rules
- Deliver as GitHub PRs, always targeting `main`/`master` (stacked PRs are fine). Never post comments or reviews on GitHub; review results go to the chat, as direct PR links.
- Merge only PRs the user explicitly LGTM'd ("だいたい良く出来てる" is not an LGTM), with merge commits. Exception: Dependabot PRs are delegated — merge them once CI is green (repos without PR checks: build + test locally first); a failing one gets an own PR with the fix. Never merge stacked children into a parent that is still under review. Before deleting a merged head branch, retarget every PR based on it (`gh pr list --base <branch>`), otherwise GitHub closes them.
- Every commit GPG-signed with EAB5AF5AA7ED7A16C4027B5283A8A5E74872A8AA. git signs by itself through `/usr/local/bin/git-gpg` (`gpg.program`; the passphrase comes from the container's environment), so nothing has to be unlocked. Never sign or decrypt with plain `gpg`: it hangs waiting for the passphrase. Bootstrap checks that signing works; if it does not, stop and tell the maintainer.
- Match the existing style, minimal error handling, prefer libraries over hand-written parsing (`new URL` / `urlparse`, never a custom `host:port:user:pass` parser). Unneeded features may be deleted. No complex unit tests; e2e is preferred. No comments that restate the code.
- Security alerts are fixed only inside the ranges the parents allow or by bumping the parent; no lasting `overrides` / `resolutions`. When neither works, leave the alert open and say why.
- READMEs carry no CI-only notes, version numbers or explanations of transparent behaviour (cookie/proxy/secrets plumbing belongs in workflows and in fa0311/twitter-secrets).
- Order multi-package work along the dependency chain (spec → clients → twitter-snap → apps) so every package is released once.
- Full sandbox autonomy: install anything, use the account in `cookie.json` freely within the budget below, spend as much effort as needed.

## Account budget
`cookie.json` is the sandbox account @ptcpz3, the only account to drive; bootstrap restores it from twitter-secrets and checks whose it is. Per day: the nightly plus at most one strict run or one wrapper e2e suite, never two suites at once. A push to or merge of a twitter_api_safe_relay PR runs its live `test` (three logins): at most one relay merge per day, none on a day with a suite. `tools/graphql_get.py UserByScreenName` answering `code 326` means the account is locked: stop and tell the maintainer (they clear it at x.com/account/access).

## twitter-openapi is zero-tolerance
A wrong spec or placeholder harms the accounts of everyone using the generated clients. Only values recorded from the real frontend go into `placeholder.json` (`tools/update_placeholder.py <catalog file|url>`); nothing is guessed, and TwitterInternalAPIDocument is not a source. New operations enter only after a recording from the real web client, on the maintainer's instruction. Verify with the strict live test before proposing, and state plainly what was and was not verified.

## Account actions
When driving the account with Playwright, every mutation must be verified to target the test tweet/list created in the same run (URL + text check), and every side effect must be reverted before the run ends (unlike, unbookmark, delete tweet, delete list, delete draft, undo feedback). Never type into a search box blindly: the bookmarks search box is the global one.

## Public text
Never involve private individuals in anything public (README images, PR descriptions, issue replies, test URLs, sample lists in tracked files; this workspace repository is public too): only Elon Musk and the accounts of his companies (X, SpaceX, Tesla, xAI, ...) may appear. Other accounts are for local checks only. Renders for the maintainer go to `screenshot/{YYYY-MM-DD}/`, the ones that matter are shown inline in the reply (Markdown image with the absolute path), and they must be pleasant to look at.

## Secrets
`cookie.json` in the workspace root (untracked, linked into `twitter-openapi/`; never print values); `GPG_PASSPHRASE` and `GITHUB_TOKEN` in the environment (never print the environment). Shared secrets live encrypted in fa0311/twitter-secrets (`cookie_json`; `proxy_list`: one `http://user:pass@host:1080` URL per line, fastest first; consumed as `PROXY_LIST`) and decrypt here with the maintainer's PGP key: `SOPS_GPG_EXEC=/usr/local/bin/git-gpg sops decrypt --extract '["proxy_list"]' twitter-secrets/secrets.enc.yaml`. Mask proxies and cookies in any log you show.

## Branches that must never be deleted
TwitterInternalAPIDocument: `develop`, `legacy-twitter`, `for/kaonasi-biwa/Twitter-UI-Customizer`, `twitter-login`, `twitter-blue`.
