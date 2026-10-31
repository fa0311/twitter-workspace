"""Open tweet pages with the account in /root/workspace/cookie.json, screenshot the main <article> and dump the computed styles of
every element in it (light and dark), as the reference for twitter-snap layout work.

    uv run --project /root/workspace/twitter-openapi python -I tools/x_dom_styles.py <outdir> <name>=<url> ...

ARTICLES=all takes the whole conversation column instead (every <article> of the thread view, screenshot and styles).
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

out = sys.argv[1]
same_site = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", "unspecified": "None", None: "None"}
cookies = json.load(open("/root/workspace/cookie.json", encoding="utf-8"))
cookies = [{"name": c["name"], "value": c["value"], "domain": c.get("domain", ".x.com"), "path": c.get("path", "/"), "secure": c.get("secure", True), "httpOnly": c.get("httpOnly", False), "sameSite": same_site.get(c.get("sameSite"), "None")} for c in cookies if c.get("domain", ".x.com").endswith("x.com")]
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
urls = dict(arg.split("=", 1) for arg in sys.argv[2:])
JS = """
(root) => {
  const props = ['display','fontSize','fontWeight','lineHeight','color','backgroundColor','borderTopWidth','borderTopColor','borderTopStyle','borderRadius','paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginBottom','marginLeft','marginRight','gap','alignItems','justifyContent','flexDirection','opacity','minWidth','fill'];
  const rows = [];
  const walk = (el, depth) => {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).filter(Boolean).join(' ').slice(0, 80);
    const o = {depth, tag: el.tagName.toLowerCase(), testid: el.getAttribute('data-testid'), role: el.getAttribute('role'), href: el.getAttribute('href'), text: own, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]};
    for (const p of props) o[p] = cs[p];
    if (el.tagName.toLowerCase() === 'path') o.d = el.getAttribute('d');
    if (el.tagName.toLowerCase() === 'svg') o.viewBox = el.getAttribute('viewBox');
    if (el.style && el.style.width) o.inlineWidth = el.style.width;
    rows.push(o);
    for (const c of el.children) walk(c, depth + 1);
  };
  walk(root, 0);
  return rows;
}
"""
with sync_playwright() as p:
    browser = p.chromium.launch()
    for theme in ("light", "dark"):
        context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 1600}, color_scheme=theme, device_scale_factor=2)
        context.add_cookies(cookies)
        page = context.new_page()
        for name, url in urls.items():
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector('article[data-testid="tweet"]', timeout=60000)
            time.sleep(4)
            if "/account/access" in page.url:
                print("LOCKED 326"); sys.exit(1)
            if os.environ.get("ARTICLES") == "all":
                article = page.locator('[aria-label="Timeline: Conversation"]').first
            else:
                article = page.locator('article[data-testid="tweet"]').first
            article.screenshot(path=f"{out}/{name}-{theme}.png")
            rows = article.evaluate(JS)
            json.dump(rows, open(f"{out}/{name}-{theme}.json", "w"), ensure_ascii=False, indent=0)
            print(name, theme, "rows", len(rows), "url", page.url)
        context.close()
    browser.close()
