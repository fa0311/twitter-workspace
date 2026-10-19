"""Broad strict sweep: call many timelines / searches / tweet details with the sandbox account, deserialize every
response with the strict generated client and collect every unknown enum value, unknown key and type mismatch.

    cd twitter-openapi-checkout && STRICT_MODE=True uv run python /root/workspace/tools/sweep_tweets.py <out_dir>
"""
import json, os, re, sys, time, collections, random
sys.path.insert(0, "test/python")
os.environ.setdefault("MULTI_THREAD", "false")
os.environ["STRICT_MODE"] = "True"
import requests
import test_serialize as ts  # noqa: E402
import openapi_client as pt  # noqa: E402
from pydantic import ValidationError  # noqa: E402

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
ts.placeholder = json.load(open("src/config/placeholder.json"))
cookies = json.load(open("cookie.json"))
if isinstance(cookies, list):
    cookies = {c["name"]: c["value"] for c in cookies}
header = requests.get("https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json", timeout=60).json()
BASE_HEADERS = {**ts.get_header(header, "chrome-fetch"), "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
                "x-twitter-auth-type": "OAuth2Session", "x-twitter-client-language": "en", "x-twitter-active-user": "yes", "x-csrf-token": cookies["ct0"],
                "cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()), "referer": "https://x.com/home"}
session = requests.Session()
calls = 0
failures = []  # dicts: op, tag, kind, where, detail
status_counter = collections.Counter()


rate = {}  # op -> (remaining, reset epoch) from X's x-rate-limit-* headers


def wait_for_budget(name):
    remaining, reset = rate.get(name, (None, 0))
    if remaining is not None and remaining < 3 and reset > time.time():
        wait = reset - time.time() + 5
        print(f"  rate limit budget of {name} used up; sleeping {wait:.0f}s until the window resets", flush=True)
        time.sleep(wait)


def call(name, override, tag):
    global calls
    entry = ts.placeholder[name]
    wait_for_budget(name)
    params = {"variables": json.dumps((entry.get("variables") or {}) | override)}
    for k in ("features", "fieldToggles"):
        if entry.get(k) is not None:
            params[k] = json.dumps(entry[k])
    headers = {**BASE_HEADERS, "x-client-transaction-id": ts.get_transaction_id(name)}
    for attempt in range(3):
        r = session.get("https://x.com" + entry["@path"], params=params, headers=headers, timeout=60)
        calls += 1
        status_counter[r.status_code] += 1
        try:
            rate[name] = (int(r.headers.get("x-rate-limit-remaining", "99")), int(r.headers.get("x-rate-limit-reset", "0")))
        except ValueError:
            pass
        if r.status_code == 429:
            reset = rate.get(name, (0, 0))[1]
            wait = max(reset - time.time(), 60) + 5
            print(f"  429 on {name} ({tag}); sleeping {wait:.0f}s until the window resets", flush=True); time.sleep(wait); continue
        break
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", tag)[:80]
    path = f"{OUT}/{name}__{safe}.json"
    open(path, "w", encoding="utf-8").write(r.text)
    if r.status_code != 200:
        failures.append({"op": name, "tag": tag, "kind": "http", "where": str(r.status_code), "detail": r.text[:200]})
        return None
    return r.text


def unknown_keys(raw, out, path, acc):
    if isinstance(raw, dict) and isinstance(out, dict):
        for k in raw.keys() - out.keys():
            acc.append((path + "." + k, json.dumps(raw[k], ensure_ascii=False)[:120]))
        for k in raw.keys() & out.keys():
            unknown_keys(raw[k], out[k], path + "." + k, acc)
    elif isinstance(raw, list) and isinstance(out, list):
        for a, b in zip(raw, out):
            unknown_keys(a, b, path + "[]", acc)


MODELS = json.load(open(os.environ.get("OP_MODELS", "/tmp/claude-0/-root-workspace/a32787d9-001f-49d1-ab30-d8c817e246f9/scratchpad/op_models.json")))


def model_for(name):
    m = MODELS.get(name) or name + "Response"
    return getattr(pt, m, None)


def check(name, tag, raw):
    model = model_for(name)
    if model is None:
        failures.append({"op": name, "tag": tag, "kind": "no-model", "where": name, "detail": ""}); return None
    try:
        obj = model.from_json(raw)
    except ValidationError as e:
        for err in e.errors()[:20]:
            failures.append({"op": name, "tag": tag, "kind": "validation", "where": f"{model.__name__}." + ".".join(str(x) for x in err["loc"]), "detail": f"{err['msg'][:140]} | input={json.dumps(err.get('input'), ensure_ascii=False, default=str)[:100]}"})
        return None
    except Exception as e:
        failures.append({"op": name, "tag": tag, "kind": "exception", "where": model.__name__, "detail": str(e)[:300]}); return None
    acc = []; unknown_keys(json.loads(raw), obj.to_dict(), "", acc)
    for p, v in acc[:30]:
        failures.append({"op": name, "tag": tag, "kind": "unknown-key", "where": re.sub(r"\[\]", "[]", p), "detail": v})
    return json.loads(raw)


def bottom_cursor(data):
    found = []
    def walk(o):
        if isinstance(o, dict):
            if o.get("__typename") == "TimelineTimelineCursor" and o.get("cursorType") == "Bottom" and o.get("value"):
                found.append(o["value"])
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(data)
    return found[0] if found else None


def tweet_ids(data):
    ids = set()
    def walk(o):
        if isinstance(o, dict):
            if o.get("__typename") == "Tweet" and o.get("rest_id"): ids.add(o["rest_id"])
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(data); return ids


def run(name, override, tag, pages=1, sleep=2.0):
    data_all = []; cursor = None
    for page in range(pages):
        ov = dict(override)
        if cursor: ov["cursor"] = cursor
        raw = call(name, ov, f"{tag}__p{page}")
        time.sleep(sleep)
        if raw is None: break
        data = check(name, f"{tag}__p{page}", raw)
        if data is None:
            try: data = json.loads(raw)
            except Exception: break
        data_all.append(data)
        cursor = bottom_cursor(data)
        if not cursor: break
    print(f"{name:28s} {tag[:40]:40s} pages={len(data_all)} calls={calls} failures={len(failures)}", flush=True)
    return data_all


collected = set()
# 1. searches
TERMS = os.environ["SWEEP_TERMS"].split("|") if os.environ.get("SWEEP_TERMS") else ["news", "lang:ja", "filter:videos", "filter:images", "filter:links", "filter:spaces", "card_name:poll", "min_faves:50000", "lang:ar", "filter:nativeretweets", "url:youtube.com", "card_name:audio"]
for term in TERMS:
    for product in ("Top", "Latest", "Media"):
        for d in run("SearchTimeline", {"rawQuery": term, "product": product}, f"search_{product}_{term}", pages=2, sleep=6):
            collected |= tweet_ids(d)
for term in ("news", "lang:ja"):
    run("SearchTimeline", {"rawQuery": term, "product": "People"}, f"search_People_{term}", pages=1, sleep=6)
# 2. user timelines
NAMES = os.environ["SWEEP_NAMES"].split(",") if os.environ.get("SWEEP_NAMES") else ["elonmusk", "X", "NASA", "nytimes", "BBCBreaking", "Support", "PlayStation", "NBA", "Pontifex", "Cristiano", "YouTube", "netflix", "OpenAI", "CommunityNotes", "nikkei", "livedoornews", "MLB", "XDevelopers", "github", "Google"]
ids = {}
for n in NAMES:
    raw = call("UserByScreenName", {"screen_name": n}, f"user_{n}"); time.sleep(2)
    if raw:
        d = check("UserByScreenName", f"user_{n}", raw) or json.loads(raw)
        try: ids[n] = d["data"]["user"]["result"]["rest_id"]
        except Exception: pass
print("resolved users:", len(ids), flush=True)
for n, uid in ids.items():
    for op in ("UserTweets", "UserTweetsAndReplies", "UserMedia", "UserHighlightsTweets"):
        for d in run(op, {"userId": uid}, f"{op}_{n}", pages=2, sleep=3):
            collected |= tweet_ids(d)
# 3. tweet details
random.seed(int(os.environ.get("SWEEP_SEED", "7")))
sample = sorted(collected); random.shuffle(sample)
for tid in ["2110391683418673555", "1349129669258448897"] + sample[:70]:
    run("TweetDetail", {"focalTweetId": tid}, f"detail_{tid}", pages=1, sleep=3)
# 4. home / explore / lists / communities / notifications
run("HomeTimeline", {}, "home", pages=3, sleep=3)
run("HomeLatestTimeline", {}, "home_latest", pages=3, sleep=3)
explore = run("ExplorePage", {}, "explore", pages=1, sleep=3)
try:
    tabs = [t["timeline"]["id"] for t in explore[0]["data"]["explore_page"]["body"]["timelines"] if t.get("timeline", {}).get("id")]
except Exception:
    tabs = []
for tid in tabs[:5]:
    run("GenericTimelineById", {"timelineId": tid}, f"explore_tab_{tid[-12:]}", pages=2, sleep=3)
lists = run("ListSearchTimeline", {"rawQuery": "news"}, "listsearch_news", pages=1, sleep=3)
list_ids = []
def walk_lists(o):
    if isinstance(o, dict):
        if o.get("__typename") == "TimelineTwitterList" and o.get("list", {}).get("id_str"): list_ids.append(o["list"]["id_str"])
        for v in o.values(): walk_lists(v)
    elif isinstance(o, list):
        for v in o: walk_lists(v)
for d in lists: walk_lists(d)
for lid in list_ids[:4]:
    run("ListLatestTweetsTimeline", {"listId": lid}, f"list_{lid}", pages=2, sleep=3)
comm = run("CommunitiesSearchQuery", {"query": "news"}, "communities_news", pages=1, sleep=3)
cids = []
try:
    cids = [x["result"]["rest_id"] for x in comm[0]["data"]["communities_search_slice"]["items_results"]]
except Exception:
    pass
for cid in cids[:4]:
    run("CommunityTweetsTimeline", {"communityId": cid}, f"community_{cid}", pages=2, sleep=3)
    run("CommunityMediaTimeline", {"communityId": cid}, f"community_media_{cid}", pages=1, sleep=3)
run("NotificationsTimeline", {}, "notifications", pages=2, sleep=3)
run("Bookmarks", {}, "bookmarks", pages=1, sleep=3)
run("BirdwatchFetchGlobalTimeline", {}, "birdwatch", pages=2, sleep=3)

json.dump(failures, open(f"{OUT}/failures.json", "w"), indent=1, ensure_ascii=False)
grouped = collections.defaultdict(list)
for f in failures:
    grouped[(f["kind"], f["where"])].append(f)
print(f"\n== calls: {calls} | statuses: {dict(status_counter)} | distinct tweets collected: {len(collected)} | failure records: {len(failures)} | groups: {len(grouped)}")
for (kind, where), items in sorted(grouped.items(), key=lambda kv: -len(kv[1]))[:60]:
    details = collections.Counter(i["detail"][:110] for i in items)
    print(f"{len(items):4d} {kind:12s} {where[:110]}")
    for dtl, n in details.most_common(3):
        print(f"       {n:3d}x {dtl}")
