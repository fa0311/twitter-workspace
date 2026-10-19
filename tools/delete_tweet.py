"""Delete one tweet of the account in cookie.json by id, verifying it is the account's own tweet first.  usage: delete_tweet.py <tweet_id>"""
import json, re, sys
sys.path.insert(0, "tools")
import update_placeholder as up
from playwright.sync_api import sync_playwright
tid = sys.argv[1]
cookies = json.load(open("cookie.json", encoding="utf-8"))
same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict"}
cookies = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ".x.com"), "path": c.get("path", "/"), "secure": c.get("secure", True), "httpOnly": c.get("httpOnly", False), "sameSite": same_site.get(c.get("sameSite"), "None")} for c in cookies if c.get("domain", ".x.com").endswith("x.com")]
ua = up.requests.get(up.HEADER_JSON, timeout=60).json()["chrome"]["user-agent"]
with sync_playwright() as p:
    browser = p.chromium.launch(); context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 900}); context.add_cookies(cookies)
    page = context.new_page(); page.set_default_navigation_timeout(120000); page.set_default_timeout(20000)
    page.goto("https://x.com/home"); me = page.get_attribute('a[data-testid="AppTabBar_Profile_Link"]', "href", timeout=120000)
    page.goto(f"https://x.com{me}/status/{tid}"); page.wait_for_timeout(5000)
    if not re.search(rf"x\.com{re.escape(me)}/status/{tid}", page.url):
        raise SystemExit(f"not an own tweet url: {page.url}")
    art = page.locator('article[data-testid="tweet"]').first
    print("tweet text:", art.inner_text()[:100].replace("\n", " "))
    art.locator('[data-testid="caret"]').click()
    item = page.get_by_role("menuitem", name=re.compile("^Delete"))
    if not item.count():
        raise SystemExit("no Delete item (not own tweet?)")
    item.click(); page.locator('[data-testid="confirmationSheetConfirm"]').click(); page.wait_for_timeout(4000)
    page.goto(f"https://x.com{me}/status/{tid}"); page.wait_for_timeout(5000)
    print("still exists:", page.locator('article[data-testid="tweet"]').count() > 0 and tid in page.url and "placeholder check" in page.inner_text("body"))
    browser.close()
