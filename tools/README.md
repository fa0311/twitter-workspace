# Tools of the workspace (tracked here, not in any project repository)

Run them from a twitter-openapi checkout (`cd /root/workspace/twitter-openapi && uv run python /root/workspace/tools/<script>`); they import `tools/update_placeholder.py` and read `cookie.json` there. Never run two account-mutating scripts at once.

| script | purpose |
|---|---|
| `record_actions.py` | drives the account through the mutations (tweet / draft / list lifecycle, like, bookmark, retweet, list members, add-to-list dialog, community tabs), records the GraphQL requests to `out/actions_recorded.json` and reverts every side effect; `DUMP=Op1,Op2` also saves those responses to `out/responses/` |
| `record_pages.py` | visits pages (`PAGES=/a,/b,/{me}/lists`; `{me}` = own profile path; default list inside), clicks every tab, records requests and dumps the responses named in `DUMP=` |
| `to_ndjson.py` | converts a recorded JSON into the NDJSON that `tools/update_placeholder.py --relay` reads |
| `graphql_get.py <Op> ['{json variables}']` | replays one GET operation exactly like the strict harness (cookie + transaction id + placeholder params) and prints status / `errors`; `DUMP_TO=file` saves the raw body; `CLIENT_LANGUAGE=ja` sets `x-twitter-client-language` (default `en`) |
| `rest_call.py <path> ['{json body}']` | replays one REST endpoint under `/i/api` the same way (GET, or POST with a JSON body), streamed line by line; `CLIENT_LANGUAGE`, `DUMP_TO` as above |
| `record_translate.py <tweet_url> <outdir>` | opens one post with the account, clicks the buttons named in `CLICKS` (regexes separated by `\|`, e.g. `^Show translation$`; `POST_TEXT` picks the post of a thread) and records every request each click causes, twice: Playwright network events and a `fetch()` tee injected into the page (streamed bodies); also the page-load request list, its GraphQL bodies and the translation feature switches; stops on a 326 lock |
| `record_feedback.py <outdir>` | opens the home timeline, clicks "Not interested in this post" on the first organic post of another account and then "Undo", and records the requests of both clicks plus the live pipeline requests of the page load; exits non-zero when the undo did not go through |
| `validate_dumps.py <dump>=<ResponseModel> ...` | strict-validates dumped responses against the generated Python models with the harness's own comparison (for mutations, which the harness never executes) |
| `delete_tweet.py <tweet_id>` | deletes one own tweet by id after checking the URL belongs to the account (cleanup after a failed run) |
| `sweep_tweets.py <outdir>` | broad strict sweep (searches, user timelines, tweet details, lists, communities, notifications), rate-limit aware; `SWEEP_TERMS` / `SWEEP_NAMES` / `SWEEP_SEED` vary the sample; writes raws + `failures.json` (see `recordings/README.md`) |
| `json_to_schema.py <response.json> <Op>` | drafts twitter-openapi style schemas from one recording (required = present in every sample); check its shared-type guesses |
| `sweep_leftovers.py` | lists (`CLEAN=1` removes) leftovers of the recording scripts on the account: "placeholder check" lists, drafts, tweets |
| `x_dom_styles.py <outdir> <name>=<url> ...` | opens tweet pages with the account, screenshots the main `<article>` and dumps the computed styles of its DOM (light + dark JSON) as the layout reference for twitter-snap: sizes, colors, spacing, icon paths |
| `bootstrap.sh` | after a container recreate: restores Claude's memory from `.claude/memory/`, creates `/root/.gnupg-rw`, reports missing tools and the gpg / gh / cookie state |

`out/` holds older recordings (`actions_recorded.json`, `pages_recorded*.json`, `responses/*.json`, part of the validation set) and screenshots.

## Offline validation set

`/root/workspace/recordings/validate_args.json` lists every stored response as `<file>=<ResponseModel>`; run them all through `validate_dumps.py` from a worktree whose venv has the current generated client (command in `recordings/README.md`). To add a strict run's cache:

```sh
python3 - <<'EOF'
import json, glob, os
src, dst = "/root/workspace/twitter-openapi-browser-only/cache", "/root/workspace/recordings/cache_rawN"   # pick the next N
os.makedirs(dst, exist_ok=True); args = json.load(open("/root/workspace/recordings/validate_args.json"))
for f in glob.glob(src + "/*.json"):
    d = json.load(open(f)); out = f"{dst}/{os.path.basename(f)}"
    open(out, "w").write(d["raw"]); open(out + ".type", "w").write(d["type"]); args.append(f"{out}={d['type']}")
json.dump(args, open("/root/workspace/recordings/validate_args.json", "w"), indent=0)
EOF
```

## relay_local/ — run twitter_api_safe_relay with the sandbox session

`seed.cjs` seeds a persistent headless Chromium profile from `cookie.json` (persistent cookies, verified by a reopen); `settings.json`
is a one-profile relay config on 127.0.0.1:3777 with the dashboard. Run from the built relay checkout so `playwright` resolves:

```sh
cd /root/workspace/twitter_api_safe_relay && pnpm install && pnpm build
cd packages/server && NODE_PATH=$PWD/node_modules node /root/workspace/tools/relay_local/seed.cjs /tmp/relay-profile/sandbox /root/workspace/cookie.json
node dist/server.js /root/workspace/tools/relay_local/settings.json   # dashboard http://localhost:3777/, JSON /health
```
