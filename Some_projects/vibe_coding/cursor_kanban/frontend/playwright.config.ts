import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  retries: process.env.CI ? 2 : 0,
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:3001",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run dev -- -p 3001",
    url: "http://127.0.0.1:3001",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});

