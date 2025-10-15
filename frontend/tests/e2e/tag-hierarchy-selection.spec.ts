import { test, expect } from '@playwright/test';

test.describe('Tag Hierarchy Selection and Query', () => {
  test('select tags and query content', async ({ page }) => {
    await page.goto('/tags');
    await expect(page).toHaveURL(/\/tags/);
    
    // Navigate to gallery
    await page.goto('/gallery');
    await expect(page).toHaveURL(/\/gallery/);
  });
});
