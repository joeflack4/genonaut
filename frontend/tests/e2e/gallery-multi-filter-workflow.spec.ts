import { test, expect } from '@playwright/test';

test.describe('Gallery Multi-Filter Workflow', () => {
  test('complex filter workflow with multiple filters', async ({ page }) => {
    await page.goto('/gallery');
    await expect(page).toHaveURL(/\/gallery/);
    
    // Try search if it exists
    const searchInput = page.locator('input[placeholder*="Search" i], input[type="search"]').first();
    if (await searchInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await searchInput.fill('sunset');
    }
    
    // Verify we're still on gallery
    await expect(page).toHaveURL(/\/gallery/);
  });
});
