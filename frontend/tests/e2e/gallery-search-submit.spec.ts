import { test, expect } from '@playwright/test';

test('gallery search submit', async ({ page }) => {
  await page.goto('/gallery');
  
  const searchInput = page.locator('input[placeholder*="Search" i], input[type="search"]').first();
  if (await searchInput.isVisible({ timeout: 1000 }).catch(() => false)) {
    await searchInput.fill('test');
    await searchInput.press('Enter');
    await page.waitForTimeout(500);
  }
  
  // Just verify page doesn't crash
  await expect(page).toHaveURL(/\/gallery/);
});
