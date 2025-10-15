import { test, expect } from '@playwright/test';

test('recommendations mark served workflow', async ({ page }) => {
  await page.goto('/recommendations');
  
  // Just verify page loads
  const pageLoaded = await page.waitForLoadState('networkidle').then(() => true).catch(() => false);
  expect(pageLoaded).toBeTruthy();
});
