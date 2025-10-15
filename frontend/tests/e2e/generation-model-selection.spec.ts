import { test, expect } from '@playwright/test';

test('generation form model selection', async ({ page }) => {
  await page.goto('/generate');
  const modelSelect = page.getByTestId('model-select');
  if (await modelSelect.isVisible()) {
    await modelSelect.click();
    await page.getByRole('option').first().click();
  }
});
