import { test, expect } from "@playwright/test";

const PAGES = ["/", "/turler", "/turler/acanthus-mollis", "/agaclar", "/dizi-ara", "/en"];

test("main routes return 200", async ({ page }) => {
  for (const path of PAGES) {
    const res = await page.goto(path, { waitUntil: "domcontentloaded" });
    expect(res?.ok(), path).toBeTruthy();
    await expect(page.locator("main#icerik")).toBeVisible();
  }
});

test("unknown species slug is 404", async ({ page }) => {
  const res = await page.goto("/turler/this-slug-does-not-exist-xyz", { waitUntil: "domcontentloaded" });
  expect(res?.status()).toBe(404);
  await expect(page.getByRole("heading", { name: /bulunamadı/i })).toBeVisible();
});
