"""Visit pages / click things with the account in cookie.json, record every GraphQL request, and dump the responses of selected operations.

    uv run python /root/workspace/tools/record_pages.py            # -> /root/workspace/tools/out/pages_recorded.json, out/responses/<Op>.json
Edit PAGES / ACTIONS below; run from a twitter-openapi checkout.
"""
import json, os, re, sys
from urllib.parse import parse_qs, urlparse

import requests
from playwright.sync_api import sync_playwright

GRAPHQL_PATH = re.compile(r"/graphql/(?P<query_id>[^/]+)/(?P<name>[^/?]+)")
HEADER_JSON = "https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json"
USER = "elonmusk"  # public profile used by the default page list


def parse_request(method, url, post_data):
    """variables / features / fieldToggles of a GraphQL request, parsed like update_placeholder.read_catalog does."""
    if method == "GET":
        params = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        return {k: json.loads(params[k]) for k in ["variables", "features", "fieldToggles"] if k in params}
    data = json.loads(post_data or "{}")
    return {k: data[k] for k in ["variables", "features", "fieldToggles"] if k in data}

OUT = "/root/workspace/tools/out/"; os.makedirs(OUT + "responses", exist_ok=True)
DUMP = set(os.environ.get("DUMP", "").split(",")) - {""}  # operation names whose first 200 response is saved
USER, COMMUNITY = USER, "1493446837214187523"
recorded, dumped, status = {}, {}, {}

def on_request(request):
    m = GRAPHQL_PATH.search(request.url)
    if m is None or m["name"] in recorded:
        return
    recorded[m["name"]] = {"@path": f"/i/api/graphql/{m['query_id']}/{m['name']}", "@method": request.method, "queryId": m["query_id"], **parse_request(request.method, request.url, request.post_data)}

def on_response(response):
    m = GRAPHQL_PATH.search(response.url)
    if m and (not DUMP or m["name"] in DUMP) and m["name"] not in dumped and response.status == 200:
        try:
            body = response.text(); json.loads(body)
        except Exception:
            return
        dumped[m["name"]] = True
        open(f"{OUT}responses/{m['name']}.json", "w", encoding="utf-8").write(body)

def step(name, fn):
    before = set(recorded)
    try:
        fn(); page.wait_for_timeout(5000)
        for tab in page.locator('[role="tab"]').all():
            try:
                tab.click(timeout=3000); page.wait_for_timeout(3000)
            except Exception:
                pass
        status[name] = "ok: " + ", ".join(sorted(set(recorded) - before))
    except Exception as e:
        status[name] = f"FAIL {type(e).__name__}: {str(e).splitlines()[0][:160]}"
        page.screenshot(path=f"{OUT}{re.sub(r'[^A-Za-z0-9]+', '_', name)}.png")
    print(name, "->", status[name][:300], flush=True)

cookies = json.load(open("cookie.json", encoding="utf-8"))
same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict"}
cookies = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ".x.com"), "path": c.get("path", "/"), "secure": c.get("secure", True), "httpOnly": c.get("httpOnly", False), "sameSite": same_site.get(c.get("sameSite"), "None")} for c in cookies if c.get("domain", ".x.com").endswith("x.com")]
ua = requests.get(HEADER_JSON, timeout=60).json()["chrome"]["user-agent"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 900})
    context.add_cookies(cookies)
    page = context.new_page()
    page.set_default_navigation_timeout(120000); page.set_default_timeout(15000)
    page.on("request", on_request); page.on("response", on_response)
    page.goto("https://x.com/home")
    me = page.get_attribute('a[data-testid="AppTabBar_Profile_Link"]', "href", timeout=120000)

    PAGES = os.environ["PAGES"].split(",") if os.environ.get("PAGES") else [me, f"{me}/with_replies", f"{me}/media", f"{me}/highlights", f"{me}/articles", f"/{USER}/articles", f"/{USER}/affiliates",
             "/i/communitynotes", "/i/communitynotes/notes", "/i/communitynotes/download-data", "/i/communitynotes/t/1349129669258448897",
             f"/i/communities/{COMMUNITY}/hashtags", f"/i/communities/{COMMUNITY}/members", f"/i/communities/{COMMUNITY}/moderators",
             "/messages", "/i/chat", "/settings/account", "/settings/privacy_and_safety", "/settings/accessibility_display_and_languages", "/settings/notifications",
             "/i/premium_sign_up", "/i/verified-orgs-signup", "/i/spaces/start", "/i/topics/picker/home", "/explore/tabs/for-you", "/explore/tabs/news", "/i/trends"]
    for path in PAGES:
        step("page " + path, lambda path=path: page.goto(f"https://x.com{path.replace('{me}', me)}"))

    if os.environ.get("PAGES"):
        browser.close(); json.dump(recorded, open(OUT + "pages_recorded.json", "w"), indent=1); print("recorded", len(recorded), "| dumped responses:", sorted(dumped)); sys.exit(0)
    def communities_search():
        page.goto("https://x.com/i/communities/suggested"); page.wait_for_timeout(3000)
        box = page.locator('[data-testid="SearchBox_Search_Input"]').first; box.fill("twitter"); box.press("Enter")
    step("communities search box", communities_search)
    def dm_search():
        page.goto("https://x.com/messages"); page.wait_for_timeout(3000)
        box = page.locator('[data-testid="searchPeople"], [data-testid="SearchBox_Search_Input"]').first; box.fill("a")
    step("dm search box", dm_search)
    def bookmark_search():
        page.goto("https://x.com/i/bookmarks"); page.wait_for_timeout(3000)
        print("bookmark inputs:", [i.get_attribute("placeholder") for i in page.locator("input").all()], flush=True)
    step("bookmarks inputs", bookmark_search)
    browser.close()

json.dump(recorded, open(OUT + "pages_recorded.json", "w"), indent=1)
json.dump(status, open(OUT + "pages_status.json", "w"), indent=1)
print("recorded", len(recorded), "| dumped responses:", sorted(dumped))
