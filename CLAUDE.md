# fa0311 X (Twitter) ecosystem workspace

Workspace of fa0311 (ふぁ), maintainer of twitter-openapi, twitter-openapi-typescript, twitter_openapi_python, TwitterInternalAPIDocument, twitter-snap (+ -api/-discord/-bookmarklet), twitter_api_safe_relay (+_skills), x-client-transaction-id-pair-dict, twitter-secrets. Reply in Japanese. Non-derivable facts about the sandbox, X and the repos live in `REFERENCE.md`.

Start every session with `HANDOVER.md` (environment, routine, state of the work) and `sh tools/bootstrap.sh`. Only `/root/workspace` survives the container being recreated: Claude's memory is backed up in `.claude/memory/` (bootstrap restores it), recordings live in `recordings/`, local scripts in `tools/`.

## Delivery rules
- Deliver as GitHub PRs, always targeting `main`/`master` (stacked PRs are fine). Never post comments or reviews on GitHub; review results go to the chat, as direct PR links.
- Merge only PRs the user explicitly LGTM'd ("だいたい良く出来てる" is not an LGTM), with merge commits. Never merge stacked children into a parent that is still under review. Before deleting a merged head branch, retarget every PR based on it (`gh pr list --base <branch>`), otherwise GitHub closes them.
- Every commit GPG-signed with EAB5AF5AA7ED7A16C4027B5283A8A5E74872A8AA; run git with `env -u GNUPGHOME` (the writable copy `/root/.gnupg-rw` is only for sops). Check `echo t | gpg --batch -bsau EAB5AF5AA7ED7A16C4027B5283A8A5E74872A8AA` emits a signature first; if not, the user unlocks it from a VS Code terminal.
- Match the existing style, minimal error handling, prefer libraries over hand-written parsing (`new URL` / `urlparse`, never a custom `host:port:user:pass` parser). Unneeded features may be deleted. No complex unit tests; e2e is preferred.
- READMEs carry no CI-only notes (cookie/proxy/secrets plumbing belongs in workflows and in fa0311/twitter-secrets).
- Full sandbox autonomy: install anything, use the account in `cookie.json` freely (mind rate limits), spend as much effort as needed. Only `/root/workspace` survives a restart.

## twitter-openapi is zero-tolerance
A wrong spec or placeholder harms the accounts of everyone using the generated clients. Only values recorded from the real frontend go into `placeholder.json` (`tools/update_placeholder.py --browser` / `--relay`); nothing is guessed, and TwitterInternalAPIDocument is not a source. Verify with the strict live test before proposing, and state plainly what was and was not verified.

## Account actions
When driving the account with Playwright, every mutation must be verified to target the test tweet/list created in the same run (URL + text check), and every side effect must be reverted before the run ends (unlike, unbookmark, delete tweet, delete list, delete draft). Never type into a search box blindly: the bookmarks search box is the global one.

## Secrets
`/root/workspace/cookie.json` (never print values), `/root/workspace/.sops/age-key.txt` (CI age key). Shared secrets live encrypted in fa0311/twitter-secrets (`proxy_list`: one `http://user:pass@host:1080` URL per line, fastest first; consumed as `PROXY_LIST`). Mask proxies and cookies in any log you show.

## Branches that must never be deleted
TwitterInternalAPIDocument: `develop`, `legacy-twitter`, `for/kaonasi-biwa/Twitter-UI-Customizer`, `twitter-login`, `twitter-blue`.
