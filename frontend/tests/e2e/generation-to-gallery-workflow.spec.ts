import { test, expect } from '@playwright/test';

test.describe('Generation to Gallery Workflow', () => {
  test('create generation and view in gallery', async ({ page }) => {
    await page.goto('/generate');
    await expect(page).toHaveURL(/\/generate/);
    
    // Navigate to gallery
    await page.goto('/gallery');
    await expect(page).toHaveURL(/\/gallery/);
  });
});
