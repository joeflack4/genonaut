import { test, expect } from '@playwright/test';

test('settings appearance theme toggle', async ({ page }) => {
  await page.goto('/settings');
  const themeToggle = page.getByTestId('theme-toggle');
  if (await themeToggle.isVisible()) {
    await themeToggle.click();
  }
});
