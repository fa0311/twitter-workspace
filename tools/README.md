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
| `wire_tee.mjs` | Node preload for the relay's `twitter-api-safe-dump` (`node --import ../tools/wire_tee.mjs ... packages/dump/src/dump.ts`, `WIRE_TEE_OUT=<dir>`): logs what the browser puts on the wire next to what the dump records, `<dir>/wire.ndjson` (every API request and answer, no headers) and `<dir>/wire_responses/<Operation>.<n>.json` (every GraphQL 200 body) |
| `catalog_check.py <recording dir>` | before a recorded catalog goes into the placeholder: every line of the dump's `requests.ndjson` must have an identical request in `wire.ndjson`; lists operations that used two queryIds or feature sets in the session and, per placeholder entry, what the session changes next to TwitterInternalAPIDocument's queryId |
| `validate_recorded.py <dir> [<Op> ...]` | strict-validates every stored response of a recording, a strict run's `cache/` or a directory of `graphql_get.py` dumps (`<Operation>.<tag>.json`) and lists every field the generated client does not define, without stopping at the first one and including those the harness lets through (`false`, `[]`, `{}`, `null`); exits 1 when anything is listed |
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

The paths in the list are relative to a twitter-openapi checkout (`../recordings/...`), so the set works from the main checkout and from a worktree next to it, wherever the workspace lives. A stored response that is known not to validate is listed next to its files instead (`unresolved_args.json`: a space that no longer resolves; `open_args.json`: a shape that is not typed yet).

## Re-recording the placeholder

On the maintainer's instruction. One browsing session of the relay's dump in the desktop's Google Chrome (53 pages took 14 minutes on 2026-11-20), logged from the network side as well:

```sh
WS=~/twitter-workspace; REC=$WS/recordings/placeholder_$(date +%F); mkdir -p $REC
jq '[.[] | select(.domain | endswith("x.com"))]' $WS/cookie.json > /tmp/x_cookies.json   # the dump adds every cookie of the file
cd $WS/twitter_api_safe_relay && CI=true pnpm install --frozen-lockfile
DISPLAY=:1 WIRE_TEE_OUT=$REC node --import ../tools/wire_tee.mjs --conditions=development packages/dump/src/dump.ts \
  --user-data-dir /tmp/dump-profile --cookies /tmp/x_cookies.json --channel chrome --out $REC/requests.ndjson --responses $REC/responses \
  --page '{me}/communities' --page /i/communities/1493446837214187523/members --page /i/communitynotes/download-data \
  --page /elonmusk/about --page /i/premium_sign_up --page /i/spaces/<the placeholder's space>
cd $WS/twitter-openapi
uv run python ../tools/catalog_check.py $REC             # catalog = wire, and what will change
uv run tools/update_placeholder.py $REC/requests.ndjson
uv run python tools/build.py && java -jar openapi-generator-cli.jar generate -c test/python/openapi-generator-config.yaml -g python && uv pip install ./python_generated
uv run python ../tools/validate_recorded.py $REC         # what the recorded query versions return and the spec lacks
```

A field the validation lists is compared on one target with both queryIds before it is typed: a directory with the previous `src/config/placeholder.json` and links to the checkout's `test/` and `cookie.json`, `DUMP_TO=$REC/controls/<Operation>.old.<tag>.json <checkout>/.venv/bin/python $WS/tools/graphql_get.py <Operation> '<variables>'` there and the same in the checkout (`.new.`), then `validate_recorded.py $REC/controls`. The dump writes its catalog only at the end; if it aborts, `wire.ndjson` still has every request. Wait 15 minutes between the session and a strict run (`ViewerBadgeCounts` and `CreatorStudioTabBarItemQuery` are sent on every page load and ran into 429). The mutations and the list dialogs are `record_actions.py`, a session of its own.

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
