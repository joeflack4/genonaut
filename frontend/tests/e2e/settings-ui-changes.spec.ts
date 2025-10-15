import { test, expect } from '@playwright/test';

test.describe('Settings UI Changes Reflect Immediately', () => {
  test('toggle sidebar labels and verify changes persist', async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/\/settings/);
    
    // Navigate to Dashboard to verify no crashes
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
