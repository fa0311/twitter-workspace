"""Open the home timeline with the account in /root/workspace/cookie.json, pick the first organic post of another account, click
"Not interested in this post" in its menu and then "Undo", and record every API request each step causes (method, URL, headers with
cookie / csrf masked, body, response). The live pipeline requests of the page load (events stream, update_subscriptions) are kept too.

    uv run python /root/workspace/tools/record_feedback.py <outdir>   # from a twitter-openapi checkout

Writes <outdir>/pageload_requests.json, <outdir>/pageload_HomeTimeline.json, <outdir>/live_pipeline.json, <outdir>/dontlike_requests.json,
<outdir>/undo_requests.json and screenshots. The feedback is always undone before the browser closes; the run fails loudly when it cannot.
Stops before any click when the account is locked (errors[].code == 326 or a bounce to /account/access).
"""
import datetime, json, os, re, sys
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright

HEADER_JSON = "https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json"
MASK = {"cookie", "x-csrf-token"}
STATIC = re.compile(r"\.(js|css|png|jpg|gif|svg|woff2?|mp4|m3u8|ts|ico)(\?|$)")
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
log, entries = [], {}


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def mask(headers):
    return {k: ("<masked>" if k.lower() in MASK else v) for k, v in (headers or {}).items()}


def on_request(request):
    if request.resource_type in ("image", "font", "script", "stylesheet", "media") or STATIC.search(urlparse(request.url).path):
        return
    entry = {"at": now(), "method": request.method, "url": request.url, "resourceType": request.resource_type, "headers": mask(request.headers),
             "postData": request.post_data, "response": {"status": None, "headers": None, "body": None}}
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


def locked():
    for hit in log:
        try:
            errors = json.loads(hit["response"]["body"] or "{}").get("errors") or []
        except Exception:
            continue
        if any(e.get("code") == 326 for e in errors if isinstance(e, dict)):
            return True
    return "/account/access" in page.url


def step(name, since):
    caused = log[since:]
    json.dump(caused, open(f"{out}/{name}_requests.json", "w"), indent=1, ensure_ascii=False)
    for hit in caused:
        print("  ", hit["method"], hit["url"][:160], "->", hit["response"]["status"], "| body:", (hit["postData"] or "")[:120])
    page.screenshot(path=f"{out}/{name}.png")
    return [hit for hit in caused if "/timeline/feedback.json" in hit["url"]]


same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", "unspecified": "None", None: "None"}
cookies = json.load(open("/root/workspace/cookie.json", encoding="utf-8"))
cookies = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ".x.com"), "path": c.get("path", "/"), "secure": c.get("secure", True),
            "httpOnly": c.get("httpOnly", False), "sameSite": same_site.get(c.get("sameSite"), "None"),
            **({"expires": c["expirationDate"]} if c.get("expirationDate") else {})} for c in cookies]
ua = requests.get(HEADER_JSON, timeout=60).json()["chrome"]["user-agent"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 1600})
    context.add_cookies(cookies)
    page = context.new_page()
    page.set_default_navigation_timeout(120000); page.set_default_timeout(20000)
    page.on("request", on_request); page.on("response", on_response); page.on("requestfinished", on_finished)
    page.goto("https://x.com/home", wait_until="domcontentloaded")
    page.wait_for_selector('article[data-testid="tweet"]'); page.wait_for_timeout(8000)
    if locked():
        print("LOCKED 326: no click"); browser.close(); sys.exit(1)
    me = page.get_attribute('a[data-testid="AppTabBar_Profile_Link"]', "href")
    print("page url", page.url, "| viewer", me)
    json.dump([{"method": h["method"], "url": h["url"], "status": h["response"]["status"]} for h in log], open(f"{out}/pageload_requests.json", "w"), indent=1)
    for hit in log:
        if "/HomeTimeline" in hit["url"] and hit["response"]["body"]:
            open(f"{out}/pageload_HomeTimeline.json", "w", encoding="utf-8").write(hit["response"]["body"])
    json.dump([h for h in log if "live_pipeline" in h["url"]], open(f"{out}/live_pipeline.json", "w"), indent=1, ensure_ascii=False)

    target = None
    for article in page.locator('article[data-testid="tweet"]').all():
        links = [a.get_attribute("href") for a in article.locator('a[href*="/status/"]').all()]
        status = next((h for h in links if re.fullmatch(r"/[^/]+/status/\d+", h or "")), None)
        if status is None or status.startswith(f"{me}/") or article.locator('text=/^Ad$/').count() > 0:
            continue  # promoted posts and own posts have no "not interested" entry
        target = article; break
    if target is None:
        print("no organic post of another account on the page"); page.screenshot(path=f"{out}/no_target.png"); browser.close(); sys.exit(1)
    print("target post", status, "|", repr(target.locator('[data-testid="tweetText"]').first.inner_text(timeout=5000)[:80]) if target.locator('[data-testid="tweetText"]').count() else "(no text)")

    target.locator('[data-testid="caret"]').first.click(); page.wait_for_selector('[role="menu"]'); page.wait_for_timeout(1500)
    items = [i.inner_text() for i in page.locator('[role="menu"] [role="menuitem"]').all()]
    print("menu:", items)
    entry = page.locator('[role="menu"] [role="menuitem"]').filter(has_text=re.compile(r"^Not interested in this post$"))
    if entry.count() == 0:
        print("no 'Not interested in this post' entry"); page.screenshot(path=f"{out}/no_entry.png"); page.keyboard.press("Escape"); browser.close(); sys.exit(1)
    since = len(log)
    entry.first.click(); page.wait_for_timeout(6000)
    print("click 'Not interested in this post':")
    sent = step("dontlike", since)
    if not sent:
        print("no feedback request was sent: nothing to undo"); browser.close(); sys.exit(1)

    undo = page.locator('[role="button"]').filter(has_text=re.compile(r"^Undo$"))
    print("undo buttons:", undo.count())
    since = len(log)
    undo.first.click(); page.wait_for_timeout(6000)
    print("click 'Undo':")
    undone = step("undo", since)
    ok = any("undo=true" in (h["postData"] or "") + h["url"] and h["response"]["status"] == 200 for h in undone)
    print("UNDONE" if ok else "NOT UNDONE: the feedback on " + status + " is still in place")
    browser.close()
    sys.exit(0 if ok else 2)
