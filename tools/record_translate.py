"""Open one post with the account in /root/workspace/cookie.json, click the given buttons of the post one after another ("Show translation",
"Show original", ...) and record every API request each click causes (REST and GraphQL alike, streamed bodies included: method, URL,
request headers, body, response status / headers / body).

    CLICKS='^Show translation$' POST_TEXT='フォトフレーム' uv run python /root/workspace/tools/record_translate.py <tweet_url> <outdir>   # from a twitter-openapi checkout

CLICKS is a list of button-text regexes separated by |; UI_LANG overrides the lang cookie in the browser only (it does not change the UI language, which follows the account setting); POST_TEXT restricts the clicks to the post containing that text (the focal post of a
thread). Requests are captured twice: by Playwright's network events and by a fetch() tee injected into the page (the Grok translation is a
streamed fetch that the network events can miss). Writes <outdir>/pageload_requests.json (method + URL of everything the page load sent),
<outdir>/pageload_<Op>__<i>.json (GraphQL bodies of the load), <outdir>/click<n>_requests.json and <outdir>/click<n>_fetch.json per click
(cookie / csrf masked), one <outdir>/click<n>_<name>__<i>.json per response body and <outdir>/click<n>.png. Stops before the first click
when the account is locked (errors[].code == 326 or a bounce to /account/access).
"""
import datetime, json, os, re, sys
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright

HEADER_JSON = "https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json"
MASK = {"cookie", "x-csrf-token"}
STATIC = re.compile(r"\.(js|css|png|jpg|gif|svg|woff2?|mp4|m3u8|ts|ico)(\?|$)")
CAPTURE_JS = """
(() => {
  window.__captured = [];
  const orig = window.fetch;
  window.fetch = async function(input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || String(input);
    const entry = {at: new Date().toISOString(), url, method: (init && init.method) || (input && input.method) || 'GET', requestHeaders: null, requestBody: null, status: null, responseHeaders: null, text: null, error: null};
    try {
      const h = (init && init.headers) || (input && input.headers);
      if (h) entry.requestHeaders = h instanceof Headers ? Object.fromEntries(h.entries()) : Array.isArray(h) ? Object.fromEntries(h) : {...h};
      if (init && typeof init.body === 'string') entry.requestBody = init.body;
    } catch (e) {}
    window.__captured.push(entry);
    const res = await orig.call(this, input, init);
    try {
      entry.status = res.status; entry.responseHeaders = Object.fromEntries(res.headers.entries());
      res.clone().text().then(t => { entry.text = t; }, e => { entry.error = String(e); });
    } catch (e) { entry.error = String(e); }
    return res;
  };
})();
"""
url, out = sys.argv[1], sys.argv[2]
clicks = [c for c in os.environ.get("CLICKS", "Show translation").split("|") if c]
os.makedirs(out, exist_ok=True)
log, entries = [], {}


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def name_of(u):
    m = re.search(r"/graphql/[^/]+/([^/?]+)", u)
    return m[1] if m else urlparse(u).path.rstrip("/").rsplit("/", 1)[-1]


def mask(headers):
    return {k: ("<masked>" if k.lower() in MASK else v) for k, v in (headers or {}).items()}


def wanted(request):
    return request.resource_type not in ("image", "font", "script", "stylesheet", "media") and not STATIC.search(urlparse(request.url).path)


def on_request(request):
    if not wanted(request):
        return
    entry = {"at": now(), "method": request.method, "url": request.url, "resourceType": request.resource_type, "headers": mask(request.headers), "postData": request.post_data,
             "response": {"status": None, "headers": None, "body": None}}
    entries[request] = entry; log.append(entry)


def on_response(response):
    entry = entries.get(response.request)
    if entry:
        entry["response"]["status"] = response.status; entry["response"]["headers"] = response.headers


def on_finished(request):
    entry = entries.get(request)
    if not entry:
        return
    try:
        entry["headers"] = mask(request.all_headers())
    except Exception as e:
        entry["headersError"] = str(e).splitlines()[0][:120]
    try:
        entry["response"]["body"] = request.response().text()
    except Exception as e:
        entry["response"]["bodyError"] = str(e).splitlines()[0][:120]


def on_failed(request):
    entry = entries.get(request)
    if entry:
        entry["failure"] = request.failure


def locked():
    for hit in log:
        try:
            errors = json.loads(hit["response"]["body"] or "{}").get("errors") or []
        except Exception:
            continue
        if any(e.get("code") == 326 for e in errors if isinstance(e, dict)):
            return True
    return "/account/access" in page.url


def fetch_log():
    rows = page.evaluate("window.__captured")
    for row in rows:
        row["requestHeaders"] = mask(row.get("requestHeaders"))
    return [r for r in rows if not STATIC.search(urlparse(r["url"]).path)]


same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", "unspecified": "None", None: "None"}
cookies = json.load(open("/root/workspace/cookie.json", encoding="utf-8"))
cookies = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ".x.com"), "path": c.get("path", "/"), "secure": c.get("secure", True), "httpOnly": c.get("httpOnly", False), "sameSite": same_site.get(c.get("sameSite"), "None")} for c in cookies if c.get("domain", ".x.com").endswith("x.com")]
if os.environ.get("UI_LANG"):  # the web client's UI language (x-twitter-client-language) follows the lang cookie; browser-side only, the account is not changed
    cookies = [c for c in cookies if c["name"] != "lang"] + [{"name": "lang", "value": os.environ["UI_LANG"], "domain": ".x.com", "path": "/", "secure": True, "httpOnly": False, "sameSite": "None"}]
ua = requests.get(HEADER_JSON, timeout=60).json()["chrome"]["user-agent"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 1600})
    context.add_cookies(cookies)
    context.add_init_script(CAPTURE_JS)
    page = context.new_page()
    page.set_default_navigation_timeout(120000); page.set_default_timeout(20000)
    page.on("request", on_request); page.on("response", on_response); page.on("requestfinished", on_finished); page.on("requestfailed", on_failed)
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector('article[data-testid="tweet"]'); page.wait_for_timeout(6000)
    print("page url", page.url, "| html lang", page.evaluate("document.documentElement.lang"), "| navigator.language", page.evaluate("navigator.language"))
    if locked():
        print("LOCKED 326: no click"); browser.close(); sys.exit(1)
    json.dump([{"method": h["method"], "url": h["url"], "status": h["response"]["status"], "x-twitter-client-language": h["headers"].get("x-twitter-client-language")} for h in log],
              open(f"{out}/pageload_requests.json", "w"), indent=1)
    for hit in log:  # the translation feature switches from the app shell's inline window.__INITIAL_STATE__ (deleted after boot)
        if hit["resourceType"] == "document" and hit["response"]["body"]:
            m = re.search(r"window.__INITIAL_STATE__=(\{.*?\});window.__META_DATA__", hit["response"]["body"], re.S)
            if m:
                config = json.loads(m[1]).get("featureSwitch", {}).get("user", {}).get("config", {})
                switches = {k: v.get("value") for k, v in config.items() if re.search(r"translat", k, re.I)}
                print("translation feature switches:", json.dumps(switches)); json.dump(switches, open(f"{out}/feature_switches_translation.json", "w"), indent=1)
    for i, hit in enumerate(log):  # the GraphQL bodies of the page load (TweetDetail etc.) as evidence of what the post carried
        if "/graphql/" in hit["url"] and hit["response"]["body"]:
            open(f"{out}/pageload_{name_of(hit['url'])}__{i}.json", "w", encoding="utf-8").write(hit["response"]["body"])
    articles = page.locator('article[data-testid="tweet"]')
    if os.environ.get("POST_TEXT"):  # only the post containing this text (e.g. the focal post of a thread)
        articles = articles.filter(has_text=os.environ["POST_TEXT"])
    print("posts on the page:", articles.count())
    for n, text in enumerate(clicks):
        inner = page.locator('[role="button"]').filter(has_text=re.compile(text))
        article = articles.filter(has=inner).first
        if article.count() == 0:
            print(f"click{n}: no post with a button {text!r}; buttons on the page:", sorted({b.inner_text()[:40] for b in page.locator('article [role="button"]').all() if b.inner_text().strip() and not b.inner_text().strip().isdigit()}))
            page.screenshot(path=f"{out}/click{n}_missing.png"); break
        button = article.locator('[role="button"]').filter(has_text=re.compile(text)).first
        before, fetched_before = len(log), len(page.evaluate("window.__captured"))
        button.click(); page.wait_for_timeout(15000)
        caused, fetched = log[before:], fetch_log()[fetched_before:]
        print(f"click{n} {text!r}: {len(caused)} requests (network events), {len(fetched)} fetch() calls")
        for i, hit in enumerate(caused):
            print("  ", hit["method"], hit["url"][:200], "->", hit["response"]["status"], "| x-twitter-client-language:", hit["headers"].get("x-twitter-client-language"), "| accept-language:", hit["headers"].get("accept-language"))
            if hit["response"]["body"]:
                open(f"{out}/click{n}_{name_of(hit['url'])}__{i}.json", "w", encoding="utf-8").write(hit["response"]["body"])
        for i, hit in enumerate(fetched):
            print("   fetch", hit["method"], hit["url"][:200], "->", hit["status"], "| body:", (hit["requestBody"] or "")[:200], "| text:", (hit["text"] or "")[:200].replace("\n", " | "))
        json.dump(caused, open(f"{out}/click{n}_requests.json", "w"), indent=1, ensure_ascii=False)
        json.dump(fetched, open(f"{out}/click{n}_fetch.json", "w"), indent=1, ensure_ascii=False)
        page.screenshot(path=f"{out}/click{n}.png")
        try:  # diagnostics only
            print("   post text now:", repr(article.locator('[data-testid="tweetText"]').first.inner_text(timeout=5000)[:300]))
            print("   buttons in that post now:", [b.inner_text()[:40] for b in article.locator('[role="button"]').all() if b.inner_text().strip() and not b.inner_text().strip().isdigit()])
        except Exception as e:
            print("   diagnostics failed:", str(e).splitlines()[0][:120])
    browser.close()
