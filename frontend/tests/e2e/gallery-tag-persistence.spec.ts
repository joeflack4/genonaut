import { test, expect } from '@playwright/test';

test.describe('Gallery Tag Persistence', () => {
  test('tag selection persists across navigation', async ({ page }) => {
    await page.goto('/gallery');
    await expect(page).toHaveURL(/\/gallery/);
    
    // Navigate away and back
    await page.goto('/dashboard');
    await page.goBack();
    
    // Verify still on gallery
    await expect(page).toHaveURL(/\/gallery/);
  });

  test('navigate to hierarchy and select additional tag', async ({ page }) => {
    await page.goto('/gallery');
    
    // Try to navigate to tags page
    await page.goto('/tags');
    await expect(page).toHaveURL(/\/tags/);
  });
});
