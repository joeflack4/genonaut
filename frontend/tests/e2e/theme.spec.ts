import { test, expect } from '@playwright/test'

test.describe('Theme and UI Settings Tests', () => {
  test('should toggle theme and persist across pages', async ({ page }) => {
    await page.goto('/settings')
    await page.waitForSelector('[data-testid="settings-page-root"]')

    const getToggle = () => page.getByTestId('settings-toggle-theme-button')
    const getModeLabel = () => page.getByTestId('settings-current-mode')

    const extractMode = async () => {
      const text = await getModeLabel().textContent()
      const match = text?.match(/current mode:\s*(light|dark)/i)
      return match ? match[1].toLowerCase() : null
    }

    await expect(getToggle()).toBeVisible()
    await expect(getModeLabel()).toBeVisible()

    const initialMode = await extractMode()
    expect(initialMode).toBeTruthy()

    const initialStored = await page.evaluate(() => window.localStorage.getItem('theme-mode'))

    await getToggle().click()
    await page.waitForTimeout(200)

    const toggledMode = await extractMode()
    expect(toggledMode).toBeTruthy()
    expect(toggledMode).not.toBe(initialMode)

    const storedAfterToggle = await page.evaluate(() => window.localStorage.getItem('theme-mode'))
    expect(storedAfterToggle?.toLowerCase()).toBe(toggledMode ?? undefined)

    const dashboardLink = page.locator('[href="/dashboard"]').first()
    await expect(dashboardLink).toBeVisible()
    await dashboardLink.click()
    await page.waitForURL('**/dashboard')
    await page.waitForSelector('[data-testid="dashboard-page-root"]')

    const persistedMode = await page.evaluate(() => window.localStorage.getItem('theme-mode'))
    expect(persistedMode?.toLowerCase()).toBe(toggledMode ?? undefined)

    const settingsLink = page.locator('[href="/settings"]').first()
    await expect(settingsLink).toBeVisible()
    await settingsLink.click()
    await page.waitForURL('**/settings')
    await page.waitForSelector('[data-testid="settings-page-root"]')

    await getToggle().click()
    await page.waitForTimeout(200)

    const finalMode = await extractMode()
    expect(finalMode).toBe(initialMode)

    const storedFinal = await page.evaluate(() => window.localStorage.getItem('theme-mode'))
    const expectedFinal = initialStored ?? initialMode ?? null
    expect(storedFinal?.toLowerCase()).toBe(expectedFinal ?? undefined)
  })

  test('should toggle UI settings and persist changes', async ({ page }) => {
    await page.goto('/settings')

    // Wait for settings page to load
    await page.waitForSelector('main')

    // Look for UI settings toggles (button labels, etc.)
    const uiToggles = page.locator('input[type="checkbox"], [role="switch"], button:has-text("Label"), button:has-text("Show"), button:has-text("Hide")')
    const toggleCount = await uiToggles.count()

    if (toggleCount > 0) {
      const firstToggle = uiToggles.first()

      // Get initial state
      const initialState = await firstToggle.isChecked().catch(() =>
        firstToggle.getAttribute('aria-checked').then(val => val === 'true')
      )

      // Toggle the setting
      await firstToggle.click()

      // Wait for change to apply
      await page.waitForTimeout(100)

      // Verify state changed
      const newState = await firstToggle.isChecked().catch(() =>
        firstToggle.getAttribute('aria-checked').then(val => val === 'true')
      )

      expect(newState).not.toBe(initialState)

      // Refresh page to test persistence
      await page.reload()
      await page.waitForSelector('main')

      // Verify setting persisted
      const persistedState = await firstToggle.isChecked().catch(() =>
        firstToggle.getAttribute('aria-checked').then(val => val === 'true')
      )

      expect(persistedState).toBe(newState)
    } else {
      // Skip if no UI toggles found
      test.skip()
    }
  })
})
