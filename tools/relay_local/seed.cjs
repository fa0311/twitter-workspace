// Seed a persistent Chromium profile with the sandbox session so the relay's `launch` profile starts logged in.
const fs = require("node:fs");
const { chromium } = require("playwright");
const [userDataDir, cookieFile] = process.argv.slice(2);
(async () => {
  const list = JSON.parse(fs.readFileSync(cookieFile, "utf8"));
  // `expires` makes them persistent cookies: Chromium drops session cookies when the context closes, and the relay opens the profile anew.
  const year = Math.floor(Date.now() / 1000) + 365 * 86400;
  const cookies = list.map(({ name, value, domain, expirationDate }) => ({ name, value, domain, path: "/", secure: true, sameSite: "None", expires: Math.floor(expirationDate ?? year) }));
  const context = await chromium.launchPersistentContext(userDataDir, { headless: true });
  await context.addCookies(cookies);
  const page = context.pages()[0] ?? (await context.newPage());
  await page.goto("https://x.com/home", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);
  console.log("seeded", cookies.length, "cookies; url after load:", page.url());
  await context.close();
  const again = await chromium.launchPersistentContext(userDataDir, { headless: true });
  const p2 = again.pages()[0] ?? (await again.newPage());
  await p2.goto("https://x.com/home", { waitUntil: "domcontentloaded", timeout: 60000 });
  await p2.waitForTimeout(4000);
  console.log("reopened without addCookies: url", p2.url(), "| account switcher:", await p2.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count());
  await again.close();
})().catch((e) => { console.error(e); process.exit(1); });
