import { test, expect } from '@playwright/test';

test('gallery stats popover', async ({ page }) => {
  await page.goto('/gallery');
  const statsIcon = page.getByTestId('stats-info-icon');
  if (await statsIcon.isVisible()) {
    await statsIcon.hover();
  }
});
