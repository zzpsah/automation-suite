import { chromium } from "playwright-core";

async function main(): Promise<void> {
  const endpoint = process.env.CDP_ENDPOINT ?? "http://127.0.0.1:9222";
  const browser = await chromium.connectOverCDP(endpoint);
  try {
    const context = browser.contexts()[0] ?? await browser.newContext();
    const page = context.pages()[0] ?? await context.newPage();
    await page.goto("https://example.com", { waitUntil: "domcontentloaded", timeout: 30_000 });
    const title = await page.title();
    const heading = await page.locator("h1").innerText({ timeout: 10_000 });
    if (title !== "Example Domain") throw new Error(`Unexpected title: ${title}`);
    if (heading !== "Example Domain") throw new Error(`Unexpected heading: ${heading}`);
    const href = await page.locator("a").first().getAttribute("href");
    if (!href) throw new Error("Expected example.com link was not observed.");
    console.log(JSON.stringify({ endpoint, url: page.url(), title, heading, link: href, status: "PASS" }));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
