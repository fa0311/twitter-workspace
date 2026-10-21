"""Call one GET GraphQL operation exactly as the strict harness does (placeholder entry + cookie + transaction id) and print the raw response.

    uv run python /root/workspace/tools/graphql_get.py ListByRestId            # from a twitter-openapi checkout with cookie.json
    uv run python /root/workspace/tools/graphql_get.py ListByRestId '{"listId": "123"}'   # override variables
"""
import json, sys, os
sys.path.insert(0, "test/python")
os.environ.setdefault("MULTI_THREAD", "false")
import requests
import test_serialize as ts  # noqa: E402  (only functions; main is guarded)
name = sys.argv[1]; override = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
ts.placeholder = json.load(open("src/config/placeholder.json"))
entry = ts.placeholder[name]
cookies = json.load(open("cookie.json"))
if isinstance(cookies, list):
    cookies = {c["name"]: c["value"] for c in cookies}
header = requests.get("https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json", timeout=60).json()
headers = {**ts.get_header(header, "chrome-fetch"), "accept-encoding": "identity",  # requests cannot decode br / zstd
           "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
           "x-twitter-auth-type": "OAuth2Session", "x-twitter-client-language": "en", "x-twitter-active-user": "yes", "x-csrf-token": cookies["ct0"],
           "x-client-transaction-id": ts.get_transaction_id(name), "cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()), "referer": "https://x.com/home"}
params = {"variables": json.dumps(entry["variables"] | override)}
for k, pk in [("features", "features"), ("fieldToggles", "fieldToggles")]:
    if entry.get(k) is not None:
        params[pk] = json.dumps(entry[k])
r = requests.get("https://x.com" + entry["@path"], params=params, headers=headers, timeout=60)
print("status", r.status_code, "| bytes", len(r.content))
body = r.json()
print("errors:", json.dumps(body.get("errors"), ensure_ascii=False)[:1500])
print("data keys:", list(body.get("data", {}))[:10])
if os.environ.get("DUMP_TO"):
    open(os.environ["DUMP_TO"], "w", encoding="utf-8").write(r.text); print("dumped to", os.environ["DUMP_TO"])
