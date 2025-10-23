import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: /.*-real-api.*\.spec\.ts$/,
  timeout: 10_000, // Longer timeout for real API tests
  expect: {
    timeout: 3_000,
  },
  use: {
    actionTimeout: 3_000,
    navigationTimeout: 10_000,
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:4173',
    headless: true,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    trace: 'on-first-retry',
  },
  reporter: [['list'], ['html', { outputFolder: 'tests/e2e/output/playwright-report/real-api', open: 'never' }]],
  projects: [
    {
      name: 'chromium-real-api',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      // Test API server with PostgreSQL test database (ENV_TARGET='local-test')
      // Note: Database credentials loaded from env/.env.shared and env/.env.local-test
      // Requires: make init-test (to initialize genonaut_test database)
      command: 'npm run test:api-server',
      port: 8002, // Different port to avoid conflicts
      reuseExistingServer: false,
      timeout: process.env.CI ? 180_000 : 60_000,
      env: {
        APP_ENV: 'test'
      },
    },
    {
      // Frontend server
      command: 'npm run dev -- --host 127.0.0.1 --port 4173',
      port: 4173,
      reuseExistingServer: false,
      timeout: process.env.CI ? 120_000 : 30_000,
      env: { VITE_API_BASE_URL: 'http://127.0.0.1:8002' },
    }
  ]
})
