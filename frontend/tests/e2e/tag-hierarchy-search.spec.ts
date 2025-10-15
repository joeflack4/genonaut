import { test, expect } from '@playwright/test';

test('tag hierarchy search mode', async ({ page }) => {
  await page.goto('/tags');
  const searchToggle = page.getByTestId('search-mode-toggle');
  if (await searchToggle.isVisible()) {
    await searchToggle.click();
  }
});
