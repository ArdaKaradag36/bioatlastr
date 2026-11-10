import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

const MOBILE = [360, 390, 412];
const DESKTOP = [768, 1024, 1440];
const PAGES = [
  { name: "home", path: "/" },
  { name: "turler", path: "/turler" },
  { name: "tur", path: "/turler/acanthus-mollis" },
  { name: "agaclar", path: "/agaclar" },
  { name: "dizi-ara", path: "/dizi-ara" },
  { name: "en", path: "/en" },
  { name: "bosluk", path: "/veri-bosluklari" },
  { name: "oncelik", path: "/oncelik" },
  { name: "rehber", path: "/rehber" },
];

const shotDir = path.join(process.cwd(), "e2e", "screenshots");

test.describe.configure({ mode: "serial" });

test("mobile pages have no horizontal overflow", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium", "screenshots and overflow on chromium");
  fs.mkdirSync(shotDir, { recursive: true });
  for (const w of MOBILE) {
    for (const p of PAGES) {
      await page.setViewportSize({ width: w, height: 800 });
      await page.goto(p.path, { waitUntil: "networkidle" });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, `${p.path} @ ${w}`).toBeLessThanOrEqual(0);
      await page.screenshot({ path: path.join(shotDir, `after-${p.name}-${w}.png`), fullPage: true });
    }
  }
});

test("desktop screenshots at 768/1024/1440", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium", "desktop shots on chromium");
  fs.mkdirSync(shotDir, { recursive: true });
  for (const w of DESKTOP) {
    for (const p of PAGES) {
      await page.setViewportSize({ width: w, height: 900 });
      await page.goto(p.path, { waitUntil: "networkidle" });
      await page.screenshot({ path: path.join(shotDir, `desktop-${p.name}-${w}.png`), fullPage: true });
    }
  }
});

test("axe serious/critical violations are zero on main pages", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium");
  await page.setViewportSize({ width: 390, height: 800 });
  for (const p of PAGES) {
    await page.goto(p.path, { waitUntil: "networkidle" });
    const results = await new AxeBuilder({ page }).analyze();
    const bad = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(bad, `${p.path}: ${bad.map((v) => v.id).join(", ")}`).toEqual([]);
  }
});
