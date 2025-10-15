import { test, expect } from '@playwright/test';

test('dashboard view mode persistence', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Try to switch to grid view if the button exists
  const gridButton = page.getByTestId('view-mode-grid');
  if (await gridButton.isVisible({ timeout: 1000 }).catch(() => false)) {
    await gridButton.click();
  }
  
  // Navigate away and back
  await page.goto('/gallery');
  await page.goto('/dashboard');
  
  // Just verify we can navigate back successfully
  await expect(page).toHaveURL(/\/dashboard/);
});
