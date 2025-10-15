import { test, expect } from '@playwright/test';

test('dashboard grid cell interactions', async ({ page }) => {
  await page.goto('/dashboard');
  const cell = page.locator('[data-testid^="grid-cell-"]').first();
  if (await cell.isVisible()) {
    await cell.click();
  }
});
