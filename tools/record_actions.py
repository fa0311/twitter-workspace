"""Drive the account in cookie.json through the mutations that page visits cannot reach and record the GraphQL requests.

    cd /root/workspace/twitter-openapi && uv run python /root/workspace/tools/record_actions.py            # -> /root/workspace/tools/out/actions_recorded.json
    uv run tools/update_placeholder.py --relay <(python3 /root/workspace/tools/to_ndjson.py /root/workspace/tools/out/actions_recorded.json)

Every tweet action is verified to target the test tweet posted by this run (URL + text), and every side effect is
reverted before the end: the tweet, the draft and the list are deleted, the like / bookmark / retweet are undone.
Selectors verified on 2026-10-15 (English UI). Needs a twitter-openapi checkout as cwd (tools/update_placeholder.py, cookie.json).
"""
import json, os, re, sys, time
sys.path.insert(0, "tools")
from urllib.parse import parse_qs, urlparse

import requests

GRAPHQL_PATH = re.compile(r"/graphql/(?P<query_id>[^/]+)/(?P<name>[^/?]+)")
HEADER_JSON = "https://raw.githubusercontent.com/fa0311/latest-user-agent/refs/heads/main/header.json"
USER = "elonmusk"


def parse_request(method, url, post_data):
    if method == "GET":
        params = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        return {k: json.loads(params[k]) for k in ["variables", "features", "fieldToggles"] if k in params}
    data = json.loads(post_data or "{}")
    return {k: data[k] for k in ["variables", "features", "fieldToggles"] if k in data}
from playwright.sync_api import sync_playwright

OUT = "/root/workspace/tools/out/"
TEXT = f"twitter-openapi placeholder check {int(time.time())}"
COMMUNITY = "1493446837214187523"
recorded, status, tweet = {}, {}, {}

def on_request(request):
    m = GRAPHQL_PATH.search(request.url)
    if m is None or m["name"] in recorded:
        return
    recorded[m["name"]] = {"@path": f"/i/api/graphql/{m['query_id']}/{m['name']}", "@method": request.method, "queryId": m["query_id"], **parse_request(request.method, request.url, request.post_data)}

DUMP = set(os.environ.get("DUMP", "").split(",")) - {""}  # operation names whose first 200 response is saved to out/responses/
dumped = {}

def on_response(response):
    m = GRAPHQL_PATH.search(response.url)
    if m and m["name"] == "CreateTweet" and response.status == 200:
        tweet["id"] = response.json()["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
    if m and m["name"] in DUMP and m["name"] not in dumped and response.status == 200:
        try:
            body = response.text(); json.loads(body)
        except Exception:
            return
        dumped[m["name"]] = True
        os.makedirs(OUT + "responses", exist_ok=True)
        open(f"{OUT}responses/{m['name']}.json", "w", encoding="utf-8").write(body)

def step(name, fn):
    before = set(recorded)
    try:
        fn(); page.wait_for_timeout(4000)
        status[name] = "ok: " + ", ".join(sorted(set(recorded) - before))
    except Exception as e:
        status[name] = f"FAIL {type(e).__name__}: {str(e).splitlines()[0][:160]}"
        page.screenshot(path=f"{OUT}{name}.png")
    print(name, "->", status[name], flush=True)

cookies = json.load(open("cookie.json", encoding="utf-8"))
same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict"}
cookies = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ".x.com"), "path": c.get("path", "/"), "secure": c.get("secure", True), "httpOnly": c.get("httpOnly", False), "sameSite": same_site.get(c.get("sameSite"), "None")} for c in cookies if c.get("domain", ".x.com").endswith("x.com")]
ua = requests.get(HEADER_JSON, timeout=60).json()["chrome"]["user-agent"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 900})
    context.add_cookies(cookies)
    page = context.new_page()
    page.set_default_navigation_timeout(120000); page.set_default_timeout(20000)
    page.on("request", on_request); page.on("response", on_response)
    page.goto("https://x.com/home")
    me = page.get_attribute('a[data-testid="AppTabBar_Profile_Link"]', "href", timeout=120000); me_name = me.strip("/")
    main = lambda: page.locator('article[data-testid="tweet"]').first
    lst = {}

    # --- home Following tab ---
    step("home_following_tab", lambda: page.get_by_role("tab", name=re.compile("^Following$")).click())

    # --- tweet lifecycle on the run's own tweet ---
    def expect_own_tweet_page():
        if not re.search(rf"x\.com/{re.escape(me_name)}/status/\d+", page.url):
            raise RuntimeError(f"not on the own tweet page: {page.url}")
        if TEXT not in main().inner_text():
            raise RuntimeError("main article is not the test tweet")
    def compose(text):
        page.goto("https://x.com/compose/post")
        dlg = page.locator('[role="dialog"]').first
        dlg.locator('[data-testid="tweetTextarea_0"]').first.fill(text)
        return dlg
    def create_tweet():
        compose(TEXT).locator('[data-testid="tweetButton"]').click(); page.wait_for_timeout(6000)
        if "id" not in tweet:
            raise RuntimeError("CreateTweet response not seen")
        tweet["url"] = f"https://x.com{me}/status/{tweet['id']}"; page.goto(tweet["url"]); expect_own_tweet_page()
    step("create_tweet", create_tweet)
    def own(fn):
        def inner():
            if page.url.split("?")[0] != tweet.get("url"):
                page.goto(tweet["url"])
            expect_own_tweet_page(); fn()
        return inner
    step("like", own(lambda: main().locator('[data-testid="like"]').click()))
    step("favoriters_page", own(lambda: (page.goto(tweet["url"] + "/likes"), page.wait_for_timeout(4000), page.goto(tweet["url"]))))
    step("bookmark", own(lambda: main().locator('[data-testid="bookmark"]').click()))
    step("retweet", own(lambda: (main().locator('[data-testid="retweet"]').click(), page.locator('[data-testid="retweetConfirm"]').click())))
    step("unretweet", own(lambda: (main().locator('[data-testid="unretweet"]').click(), page.locator('[data-testid="unretweetConfirm"]').click())))
    step("unbookmark", own(lambda: main().locator('[data-testid="removeBookmark"]').click()))
    step("unlike", own(lambda: main().locator('[data-testid="unlike"]').click()))
    def delete_tweet():
        main().locator('[data-testid="caret"]').click()
        item = page.get_by_role("menuitem", name=re.compile("^Delete"))
        if not item.count():
            raise RuntimeError("no Delete item in the menu")
        item.click(); page.locator('[data-testid="confirmationSheetConfirm"]').click(); page.wait_for_timeout(4000)
        page.goto(tweet["url"]); page.wait_for_timeout(4000)
        if TEXT in page.inner_text("body"):
            raise RuntimeError("test tweet still exists")
    step("delete_tweet", own(delete_tweet))

    # --- draft lifecycle ---
    def create_draft():
        compose(TEXT + " draft"); page.locator('[data-testid="app-bar-close"]').click()
        page.locator('[data-testid="confirmationSheetConfirm"]').click()  # Save
    step("create_draft", create_draft)
    def delete_draft():
        page.goto("https://x.com/compose/post")
        page.locator('[role="dialog"]').first.get_by_text(re.compile("^Drafts$")).click(); page.wait_for_timeout(3000)
        page.get_by_role("button", name=re.compile("^Edit$")).click(); page.wait_for_timeout(1500)
        page.get_by_role("checkbox").first.click(); page.wait_for_timeout(1000)
        page.get_by_role("button", name=re.compile("^Delete")).click(); page.wait_for_timeout(1500)
        page.locator('[data-testid="confirmationSheetConfirm"]').click(); page.wait_for_timeout(3000)
        if page.locator('[role="dialog"]').first.get_by_text("placeholder check").count():
            raise RuntimeError("draft still exists")
    step("delete_draft", delete_draft)

    # --- list lifecycle ---
    def create_list():
        page.goto("https://x.com/i/lists/create"); page.locator('input[name="name"]').fill("placeholder check")
        page.get_by_role("button", name=re.compile("^Next$")).click(); page.wait_for_timeout(4000)
        page.get_by_role("button", name=re.compile("^Done$")).click()
        page.wait_for_url(re.compile(r"/i/lists/\d+")); lst["url"] = page.url.split("?")[0]
    step("create_list", create_list)
    def search_member():
        page.goto(lst["url"]); page.get_by_role("link", name=re.compile("Edit List")).click(); page.wait_for_timeout(2000)
        page.get_by_text(re.compile("Manage members")).click(); page.wait_for_timeout(2000)
        page.get_by_role("tab", name=re.compile("Suggested")).click(); page.wait_for_timeout(1500)
        page.get_by_placeholder(re.compile("Search people")).fill(USER); page.wait_for_timeout(5000)
    step("search_member", search_member)
    step("list_add_member", lambda: page.get_by_role("button", name=re.compile("^Add$")).first.click())
    step("list_remove_member", lambda: page.get_by_role("button", name=re.compile("^Remove$")).first.click())
    def delete_list():
        page.goto(lst["url"]); page.get_by_role("link", name=re.compile("Edit List")).click(); page.wait_for_timeout(2000)
        page.get_by_text(re.compile("Delete List")).click(); page.locator('[data-testid="confirmationSheetConfirm"]').click(); page.wait_for_timeout(4000)
        page.goto(lst["url"]); page.wait_for_timeout(4000)
        if page.get_by_role("heading", name=re.compile("placeholder check")).count():
            raise RuntimeError("list still exists")
    step("delete_list", delete_list)

    # --- read-only dialogs and tabs ---
    def add_to_list_dialog():
        page.goto(f"https://x.com/{USER}"); page.locator('[data-testid="userActions"]').click()
        page.get_by_role("menuitem", name=re.compile("Add.remove")).click(); page.wait_for_timeout(4000); page.keyboard.press("Escape")
    step("add_to_list_dialog", add_to_list_dialog)
    def community_tabs():
        page.goto(f"https://x.com/i/communities/{COMMUNITY}"); page.wait_for_timeout(3000)
        for name in [t.inner_text() for t in page.get_by_role("tab").all()]:
            page.get_by_role("tab", name=name, exact=True).click(); page.wait_for_timeout(4000)
    step("community_tabs", community_tabs)
    browser.close()

os.makedirs(OUT, exist_ok=True)
json.dump(recorded, open(OUT + "actions_recorded.json", "w"), indent=1)
json.dump(status, open(OUT + "status.json", "w"), indent=1)
failed = [k for k, v in status.items() if v.startswith("FAIL")]
print("recorded", len(recorded), "| dumped:", sorted(dumped), "| failed steps:", failed or "none", "| CHECK THE ACCOUNT BY HAND if a delete/undo step failed")
