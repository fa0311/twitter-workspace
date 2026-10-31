"""Call one REST endpoint under https://x.com/i/api exactly as the strict harness would (cookie + transaction id + the web client's
headers) and print status, content-type and body (streamed line by line).

    uv run python /root/workspace/tools/rest_call.py '/1.1/strato/column/None/tweetId=1,.../translation/service/translateTweet'      # GET, from a twitter-openapi checkout
    uv run python /root/workspace/tools/rest_call.py /2/grok/translation.json '{"content_type":"POST","id":"1","dst_lang":"en"}'  # POST with a JSON body
    CLIENT_LANGUAGE=ja DUMP_TO=file ...                                                                                           # x-twitter-client-language (default en), save the raw body
"""
import json, os, sys
sys.path.insert(0, "test/python")
os.environ.setdefault("MULTI_THREAD", "false")
import requests
import test_serialize as ts  # noqa: E402  (only functions; main is guarded)
path = sys.argv[1]; body = sys.argv[2] if len(sys.argv) > 2 else None
method = "POST" if body is not None else "GET"
cookies = json.load(open("cookie.json"))
if isinstance(cookies, list):
    cookies = {c["name"]: c["value"] for c in cookies}
header = requests.get("https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json", timeout=60).json()
headers = {**ts.get_header(header, "chrome-fetch"), "accept-encoding": "identity",  # requests cannot decode br / zstd
           "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
           "x-twitter-auth-type": "OAuth2Session", "x-twitter-client-language": os.environ.get("CLIENT_LANGUAGE", "en"), "x-twitter-active-user": "yes", "x-csrf-token": cookies["ct0"],
           "x-client-transaction-id": ts.get_transaction_base().generate_transaction_id(method=method, path="/i/api" + path),
           "cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()), "referer": "https://x.com/home"}
if body is not None:
    headers["content-type"] = "application/json"
r = requests.request(method, "https://x.com/i/api" + path, headers=headers, data=body, timeout=60, stream=True)
print("status", r.status_code, "| content-type", r.headers.get("content-type"), "| transfer-encoding", r.headers.get("transfer-encoding"), "| rate", r.headers.get("x-rate-limit-remaining"), "/", r.headers.get("x-rate-limit-limit"))
r.encoding = r.encoding or "utf-8"  # the Grok stream carries no content-type
lines = []
for line in r.iter_lines(decode_unicode=True):
    lines.append(line); print("line:", line[:300])
if os.environ.get("DUMP_TO"):
    open(os.environ["DUMP_TO"], "w", encoding="utf-8").write("\n".join(lines) + "\n"); print("dumped to", os.environ["DUMP_TO"])
