import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  timeout: 60_000,
  webServer: {
    command: "npm run start -- --port 3210",
    port: 3210,
    reuseExistingServer: false,
    timeout: 120_000,
  },
  use: { baseURL: "http://127.0.0.1:3210", trace: "off" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
