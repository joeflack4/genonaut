import { test, expect } from '@playwright/test';

test('generation cancel request', async ({ page }) => {
  await page.goto('/generate');
  const cancelButton = page.getByTestId('cancel-generation-button');
  if (await cancelButton.isVisible()) {
    await cancelButton.click();
  }
});
