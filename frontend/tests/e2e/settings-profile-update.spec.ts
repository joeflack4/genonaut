import { test, expect } from '@playwright/test';

test('settings profile update', async ({ page }) => {
  await page.goto('/settings');
  const displayName = page.getByTestId('display-name-input');
  if (await displayName.isVisible()) {
    await displayName.fill('New Name');
    const saveButton = page.getByTestId('save-button');
    await saveButton.click();
  }
});
