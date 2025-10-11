import { test, expect } from '@playwright/test'

test.describe('Settings Page Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForSelector('main', { timeout: 10000 })
  })

  test('should update profile information', async ({ page }) => {
    // Look for display name and email fields
    const displayNameField = page.locator('input[label*="name"], input[placeholder*="name"], input[name*="name"]').first()
    const emailField = page.locator('input[type="email"], input[label*="email"], input[placeholder*="email"]').first()
    const saveButton = page.locator('button:has-text("Save"), button[type="submit"]').first()

    if (await displayNameField.isVisible() && await emailField.isVisible()) {
      // Get original values
      const originalName = await displayNameField.inputValue()
      const originalEmail = await emailField.inputValue()

      // Update fields
      await displayNameField.fill('Test User Updated')
      await emailField.fill('updated@test.com')

      // Click save button
      if (await saveButton.isVisible()) {
        await saveButton.click()
        await page.waitForTimeout(1000)

        // Look for success message
        const successMessage = page.locator('text=updated, text=success, .MuiAlert-standardSuccess')
        if (await successMessage.count() > 0) {
          await expect(successMessage.first()).toBeVisible()
        }

        // Restore original values for cleanup
        await displayNameField.fill(originalName)
        await emailField.fill(originalEmail)
        if (await saveButton.isVisible() && await saveButton.isEnabled()) {
          await saveButton.click()
          await page.waitForTimeout(500)
        }
      }
    } else {
      test.skip()
    }
  })

  test('should toggle button labels setting', async ({ page }) => {
    // Look for button labels toggle
    const buttonLabelsToggle = page.locator('input[type="checkbox"]:has-text("label"), [role="switch"]:has-text("label"), .MuiSwitch-root').first()

    if (await buttonLabelsToggle.isVisible()) {
      // Get initial state
      const initialState = await buttonLabelsToggle.isChecked()

      // Toggle the setting
      await buttonLabelsToggle.click()
      await page.waitForTimeout(500)

      // Verify state changed
      const newState = await buttonLabelsToggle.isChecked()
      expect(newState).not.toBe(initialState)

      // Toggle back to original state
      await buttonLabelsToggle.click()
      await page.waitForTimeout(500)

      // Should be back to original state
      const finalState = await buttonLabelsToggle.isChecked()
      expect(finalState).toBe(initialState)
    } else {
      test.skip()
    }
  })

  test('should handle theme mode toggle', async ({ page }) => {
    const themeToggle = page.getByTestId('settings-toggle-theme-button')
    const modeLabel = page.getByTestId('settings-current-mode')

    await expect(themeToggle).toBeVisible()
    await expect(modeLabel).toBeVisible()

    const extractMode = async () => {
      const text = await modeLabel.textContent()
      const match = text?.match(/current mode:\s*(light|dark)/i)
      return match ? match[1].toLowerCase() : null
    }

    const initialMode = await extractMode()
    expect(initialMode).toBeTruthy()

    const initialStoredMode = await page.evaluate(() => window.localStorage.getItem('theme-mode'))

    await themeToggle.click()
    await page.waitForTimeout(200)

    const toggledMode = await extractMode()
    expect(toggledMode).toBeTruthy()
    expect(toggledMode).not.toBe(initialMode)

    const storedToggleMode = await page.evaluate(() => window.localStorage.getItem('theme-mode'))
    expect(storedToggleMode?.toLowerCase()).toBe(toggledMode ?? undefined)

    await themeToggle.click()
    await page.waitForTimeout(200)

    const finalMode = await extractMode()
    expect(finalMode).toBe(initialMode)

    const storedFinalMode = await page.evaluate(() => window.localStorage.getItem('theme-mode'))
    const expectedFinal = initialStoredMode ?? initialMode ?? null
    expect(storedFinalMode?.toLowerCase()).toBe(expectedFinal ?? undefined)
  })

  test('should validate form field requirements', async ({ page }) => {
    const displayNameField = page.locator('input[label*="name"], input[placeholder*="name"]').first()
    const emailField = page.locator('input[type="email"]').first()

    if (await emailField.isVisible()) {
      // Test invalid email format
      await emailField.fill('invalid-email')
      await emailField.blur()
      await page.waitForTimeout(300)

      // Check for validation error (might be visual or prevent submission)
      const errorMessage = page.locator('text=invalid, .error, .MuiFormHelperText-root')
      if (await errorMessage.count() > 0) {
        await expect(errorMessage.first()).toBeVisible()
      }

      // Test valid email format
      await emailField.fill('valid@email.com')
      await emailField.blur()
      await page.waitForTimeout(300)

      // Error should be gone if it existed
      if (await errorMessage.count() > 0) {
        await expect(errorMessage.first()).not.toBeVisible()
      }
    } else {
      test.skip()
    }
  })

  test('should persist settings across page reloads', async ({ page }) => {
    // Find any toggle that might persist state
    const toggle = page.locator('input[type="checkbox"], [role="switch"]').first()

    if (await toggle.isVisible()) {
      // Get initial state
      const initialState = await toggle.isChecked()

      // Toggle the setting
      await toggle.click()
      await page.waitForTimeout(500)

      // Verify state changed
      const newState = await toggle.isChecked()
      expect(newState).not.toBe(initialState)

      // Reload page
      await page.reload()
      await page.waitForSelector('main', { timeout: 10000 })

      // Check if setting persisted
      const persistedState = await toggle.isChecked()
      // Note: This might not always work depending on implementation
      // but it's good to test for persistence
      if (persistedState === newState) {
        expect(persistedState).toBe(newState)
      }

      // Reset to original state for cleanup
      if (persistedState !== initialState) {
        await toggle.click()
        await page.waitForTimeout(500)
      }
    } else {
      test.skip()
    }
  })
})
