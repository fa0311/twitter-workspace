# Tools of the workspace (tracked here, not in any project repository)

Run them from a twitter-openapi checkout (`cd twitter-openapi && uv run python ../tools/<script>`): they import the checkout's `test/python/test_serialize.py` or `tools/update_placeholder.py` and read `cookie.json` there, a link to the workspace's that bootstrap creates. The venv needs the strict generated client and, for the scripts that open a browser, Playwright with its Chromium; bootstrap prints the line for whichever is missing. Never run two account-mutating scripts at once.

| script | purpose |
|---|---|
| `record_actions.py` | drives the account through the mutations (tweet / draft / list lifecycle, like, bookmark, retweet, list members, add-to-list dialog, community tabs), records the GraphQL requests to `out/actions_recorded.json` and reverts every side effect; `DUMP=Op1,Op2` also saves those responses to `out/responses/` |
| `record_pages.py` | visits pages (`PAGES=/a,/b,/{me}/lists`; `{me}` = own profile path; default list inside), clicks every tab, records requests and dumps the responses named in `DUMP=` |
| `to_ndjson.py` | converts a recorded JSON into the NDJSON catalog that `tools/update_placeholder.py` reads |
| `graphql_get.py <Op> ['{json variables}']` | replays one GET operation exactly like the strict harness (cookie + transaction id + placeholder params) and prints status / `errors`; `DUMP_TO=file` saves the raw body; `CLIENT_LANGUAGE=ja` sets `x-twitter-client-language` (default `en`) |
| `rest_call.py <path> ['{json body}']` | replays one REST endpoint under `/i/api` the same way (GET, or POST with a JSON body), streamed line by line; `CLIENT_LANGUAGE`, `DUMP_TO` as above |
| `record_translate.py <tweet_url> <outdir>` | opens one post with the account, clicks the buttons named in `CLICKS` (regexes separated by `\|`, e.g. `^Show translation$`; `POST_TEXT` picks the post of a thread) and records every request each click causes, twice: Playwright network events and a `fetch()` tee injected into the page (streamed bodies); also the page-load request list, its GraphQL bodies and the translation feature switches; stops on a 326 lock |
| `record_feedback.py <outdir>` | opens the home timeline, clicks "Not interested in this post" on the first organic post of another account and then "Undo", and records the requests of both clicks plus the live pipeline requests of the page load; exits non-zero when the undo did not go through |
| `validate_dumps.py <dump>=<ResponseModel> ...` | strict-validates dumped responses against the generated Python models with the harness's own comparison (for mutations, which the harness never executes) |
| `delete_tweet.py <tweet_id>` | deletes one own tweet by id after checking the URL belongs to the account (cleanup after a failed run) |
| `sweep_tweets.py <outdir>` | broad strict sweep (searches, user timelines, tweet details, lists, communities, notifications), rate-limit aware; `SWEEP_TERMS` / `SWEEP_NAMES` / `SWEEP_SEED` vary the sample; takes each operation's response model from the built spec (`dist/`, so run `tools/build.py` first); writes raws + `failures.json` |
| `json_to_schema.py <response.json> <Op>` | drafts twitter-openapi style schemas from one recording (required = present in every sample); check its shared-type guesses |
| `sweep_leftovers.py` | lists (`CLEAN=1` removes) leftovers of the recording scripts on the account: "placeholder check" lists, drafts, tweets |
| `x_dom_styles.py <outdir> <name>=<url> ...` | opens tweet pages with the account, screenshots the main `<article>` and dumps the computed styles of its DOM (light + dark JSON) as the layout reference for twitter-snap: sizes, colors, spacing, icon paths |
| `render_saved_tweet.mjs <post url> <saved TweetResultByRestId.json> <out.png> [scale] [width]` | renders a post from a saved raw response through twitter-snap's guest pipeline (run after `pnpm build` in `twitter-snap/`, which it imports by relative path); the way to re-render a deleted post while pbs.twimg.com still serves its media |
| `og_compare/` | render-compare kit for twitter-snap changes: `sh og_compare/render.sh <outdir> node bin/run.js` renders the sample posts of `og_compare/urls.txt` (official accounts only; add private posts locally, never commit them) in both themes, `node og_compare/compare.cjs <a> <b>` diffs the PNGs pixel-wise (needs `sharp` installed next to it: `npm i sharp`), `montage.cjs` puts them side by side |
| `tiad_check.py [<old> <new>]` | run from the TwitterInternalAPIDocument checkout before merging its "Update Document" PR: exits 1 on an anomaly (a change outside `docs/`, a deleted file, invalid JSON, a file that lost more than 10 %, a value of the sandbox cookie in the documents, a user entity other than the sandbox account) and lists, for the web client (`docs/json`) and for X Pro (`docs/deck/json`), the GraphQL operations, feature switches (defaults and the account's values) and translation strings that were added, removed or changed; two commits as arguments look at an earlier range |
| `bootstrap.sh` | at the start of a session: initialises missing submodules, restores Claude's memory from `.claude/memory/` and `cookie.json` from twitter-secrets (linked into `twitter-openapi/`, checked to be @ptcpz3), reports missing tools, the strict client and Playwright with their install lines (in the order to run them) and the signing / gh state |

`out/` (ignored) receives what the recording scripts write: `actions_recorded.json`, `pages_recorded*.json`, `responses/*.json`, screenshots.

## Offline validation set

`recordings/validate_args.json` lists every stored response as `<file>=<ResponseModel>`. Run the whole list through `validate_dumps.py` from a checkout whose venv has the current generated client; every line must print `match 1.0`:

```sh
cd twitter-openapi && uv run python ../tools/validate_dumps.py $(jq -r '.[]' ../recordings/validate_args.json)
```

To add a strict run's cache (`cache/*.json` holds `{raw, type}` of every response), from the workspace root:

```sh
python3 - <<'EOF'
import json, glob, os
src, dst = "twitter-openapi/cache", "recordings/cache_rawN"   # pick the next N
os.makedirs(dst, exist_ok=True); listing = "recordings/validate_args.json"
args = json.load(open(listing)) if os.path.exists(listing) else []
for f in glob.glob(src + "/*.json"):
    d = json.load(open(f)); out = f"{dst}/{os.path.basename(f)}"
    open(out, "w").write(d["raw"]); open(out + ".type", "w").write(d["type"]); args.append(f"../{out}={d['type']}")
json.dump(args, open(listing, "w"), indent=0)
EOF
```

The paths in the list are relative to a twitter-openapi checkout (`../recordings/...`), so the set works from the main checkout and from a worktree next to it, wherever the workspace lives.

## relay_local/ — run twitter_api_safe_relay with the sandbox session

`seed.cjs` seeds a persistent headless Chromium profile from `cookie.json` (persistent cookies, verified by a reopen); `settings.json`
is a one-profile relay config on 127.0.0.1:3777 with the dashboard. Run from the built relay checkout so `playwright` resolves (starting it logs the account in once; not run in this environment yet):

```sh
WS=~/twitter-workspace
cd $WS/twitter_api_safe_relay && pnpm install && pnpm build
cd packages/server && NODE_PATH=$PWD/node_modules node $WS/tools/relay_local/seed.cjs /tmp/relay-profile/sandbox $WS/cookie.json
node dist/server.js $WS/tools/relay_local/settings.json   # dashboard http://localhost:3777/, JSON /health
```

Pitfalls: the first request launches the browser (a few seconds); `pkill -f 'dist/server.js'` matches the shell about to start the relay; a profile seeded without cookie `expires` is logged out after the seeding context closes and every `/i/api/*` request then hangs while `/health` answers; dashboard entries exist only while a page is connected to `/api/events`; the dashboard is served from `packages/dashboard/dist`, so a rebuild shows up on reload.
