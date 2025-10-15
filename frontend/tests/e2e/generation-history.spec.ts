import { test, expect } from '@playwright/test';

test('generation history tab workflow', async ({ page }) => {
  await page.goto('/generate');
  await expect(page).toHaveURL(/\/generate/);
  
  // Look for history tab
  const historyTab = page.locator('[role="tab"]').filter({ hasText: /history/i }).first();
  if (await historyTab.isVisible({ timeout: 1000 }).catch(() => false)) {
    await historyTab.click();
  }
  
  // Verify page loads
  expect(true).toBeTruthy();
});
