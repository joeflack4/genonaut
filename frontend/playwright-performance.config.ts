import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000, // Higher timeout for performance tests
  expect: {
    timeout: 5_000,
  },
  use: {
    actionTimeout: 5_000,
    navigationTimeout: 15_000,
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:4173',
    headless: true,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    // Disable tracing, video, and screenshots for accurate performance measurements
    trace: 'off',
    video: 'off',
    screenshot: 'off',
  },
  reporter: [['list'], ['html', { outputFolder: 'tests/e2e/output/playwright-report', open: 'never' }]],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173',
    port: 4173,
    reuseExistingServer: true,
    timeout: process.env.CI ? 120_000 : 30_000,
    env: { VITE_API_BASE_URL: 'http://127.0.0.1:8001' },
  }
})
