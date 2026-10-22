import { defineConfig, devices } from "@playwright/test";

// E2E against the production build served by `vite preview` (build first: npm run build). PLUMES_FIXTURES=1 makes
// the preview serve the contract fixtures at /data/ and a config.json pointing there (scripts/vite-fixture-data.ts). OpenFreeMap is stubbed unreachable in
// e2e/fixtures.ts, so the interactive map uses its bundled coastline and runs offline.
const PORT = Number(process.env.E2E_PORT ?? 4327);

export default defineConfig({
  testDir: "e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  workers: 2,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: "retain-on-failure",
    launchOptions: { args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] },
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 } }, testIgnore: /devices\.spec/ },
    // Rule 6b device matrix: only the map decision runs here (devices.spec.ts).
    { name: "devices", testMatch: /devices\.spec/, use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: `npx vite preview --port ${PORT} --strictPort --host 127.0.0.1`,
    url: `http://127.0.0.1:${PORT}/`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: { PLUMES_FIXTURES: "1" },
  },
});
