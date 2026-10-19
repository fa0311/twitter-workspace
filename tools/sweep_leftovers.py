"""Report (and with CLEAN=1 remove) leftovers of the recording scripts on the account: 'placeholder check' lists, drafts, and own tweets containing 'placeholder check'."""
import json, os, re, sys
sys.path.insert(0, "tools")
import update_placeholder as up
from playwright.sync_api import sync_playwright
cookies = json.load(open("cookie.json", encoding="utf-8"))
same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict"}
cookies = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ".x.com"), "path": c.get("path", "/"), "secure": c.get("secure", True), "httpOnly": c.get("httpOnly", False), "sameSite": same_site.get(c.get("sameSite"), "None")} for c in cookies if c.get("domain", ".x.com").endswith("x.com")]
ua = up.requests.get(up.HEADER_JSON, timeout=60).json()["chrome"]["user-agent"]
with sync_playwright() as p:
    browser = p.chromium.launch(); context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 900}); context.add_cookies(cookies)
    page = context.new_page(); page.set_default_navigation_timeout(120000); page.set_default_timeout(20000)
    page.goto("https://x.com/home"); me = page.get_attribute('a[data-testid="AppTabBar_Profile_Link"]', "href", timeout=120000)
    page.goto(f"https://x.com{me}/lists"); page.wait_for_timeout(6000)
    lists = page.get_by_text(re.compile("placeholder check")).count(); print("own lists named 'placeholder check':", lists)
    page.goto("https://x.com/compose/post"); page.locator('[role="dialog"]').first.get_by_text(re.compile("^Drafts$")).click(); page.wait_for_timeout(4000)
    drafts = page.locator('[role="dialog"]').first.get_by_text(re.compile("placeholder|draft sample")).count(); print("drafts from the scripts:", drafts)
    page.goto(f"https://x.com{me}"); page.wait_for_timeout(6000)
    tweets = page.locator('article[data-testid="tweet"]', has_text=re.compile("placeholder check")).count(); print("own tweets containing 'placeholder check' (first page):", tweets)
    page.goto(f"https://x.com{me}/likes"); page.wait_for_timeout(5000)
    likes = page.locator('article[data-testid="tweet"]').count(); print("likes page articles:", likes)
    page.goto("https://x.com/i/bookmarks"); page.wait_for_timeout(5000)
    print("bookmarks articles:", page.locator('article[data-testid="tweet"]').count())
    browser.close()
