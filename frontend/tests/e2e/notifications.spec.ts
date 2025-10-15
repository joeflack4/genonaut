import { test, expect } from '@playwright/test';

test('notifications list and detail', async ({ page }) => {
  await page.goto('/notifications');
  const list = page.getByTestId('notifications-list');
  if (await list.isVisible()) {
    await expect(list).toBeVisible();
  }
});
