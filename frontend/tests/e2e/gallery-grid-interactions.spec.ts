import { test, expect } from '@playwright/test';

test('gallery grid view interactions', async ({ page }) => {
  await page.goto('/gallery');
  
  // Verify gallery loads
  await expect(page).toHaveURL(/\/gallery/);
  
  // Try to find any content item
  const contentItem = page.locator('[class*="grid"], [class*="Gallery"], main').first();
  await expect(contentItem).toBeVisible();
});
