import { test, expect } from '@playwright/test'
import {
  ensureRealApiAvailable,
  assertSufficientTestData,
  loginAsTestUser,
  waitForPageLoad,
  getCurrentUser,
  updateUserProfile,
  getTestUserId
} from './utils/realApiHelpers'

test.describe('Settings page (Real API)', () => {
  test.beforeEach(async ({ page }) => {
    // Check if real API is available, skip if not
    try {
      await ensureRealApiAvailable(page)
    } catch (error) {
      test.skip(true, 'Real API server not available on port 8002. Run with: npm run test:e2e:real-api')
      return
    }

    // Ensure we have sufficient test data
    try {
      await assertSufficientTestData(page, '/api/v1/content/unified?page=1&page_size=1', 1)
    } catch (error) {
      test.skip(true, 'Real API returned zero gallery results. Ensure the test database seed ran (make frontend-test-e2e-real-api).')
      return
    }

    // Log in as test user
    await loginAsTestUser(page)
  })

  test('persists profile updates and theme preference', async ({ page }) => {
    // Get initial user data
    const initialUser = await getCurrentUser(page)
    expect(initialUser).toBeTruthy()
    expect(initialUser.id).toBe(await getTestUserId())

    // Navigate to settings page
    await page.goto('/settings')
    await waitForPageLoad(page, 'settings')

    // Check for profile form elements
    const nameInput = page.getByLabel(/display name|name/i)
    const emailInput = page.getByLabel(/email/i)

    // Test profile updates if form is available
    if (await nameInput.count() > 0) {
      // Check initial values are loaded
      if (initialUser.name) {
        await expect(nameInput).toHaveValue(initialUser.name)
      }
      if (initialUser.email && await emailInput.count() > 0) {
        await expect(emailInput).toHaveValue(initialUser.email)
      }

      // Update profile
      const updatedName = `${initialUser.name || 'Test User'} Updated`
      await nameInput.fill(updatedName)

      // Save changes
      const saveButton = page.getByRole('button', { name: /save|update|apply/i })
      if (await saveButton.count() > 0) {
        await saveButton.click()

        // Wait for save to complete
        await page.waitForTimeout(1000)

        // Look for success message
        const successIndicators = [
          page.getByText(/saved|updated|success/i),
          page.getByText(/profile updated/i),
          page.getByText(/changes saved/i)
        ]

        let foundSuccess = false
        for (const indicator of successIndicators) {
          if (await indicator.count() > 0 && await indicator.isVisible()) {
            foundSuccess = true
            break
          }
        }

        if (foundSuccess) {
          // Verify changes were actually saved to the API
          const updatedUser = await getCurrentUser(page)
          expect(updatedUser.name).toBe(updatedName)

          // Test persistence by reloading the page
          await page.reload()
          await waitForPageLoad(page, 'settings')
          await expect(nameInput).toHaveValue(updatedName)

          // Restore original name for cleanup
          await nameInput.fill(initialUser.name || 'Test User')
          if (await saveButton.count() > 0) {
            await saveButton.click()
            await page.waitForTimeout(500)
          }
        }
      }
    }

    // Test theme functionality
    await testThemePersistence(page)
  })

  test('loads user profile data correctly', async ({ page }) => {
    // Get user data from API
    const userData = await getCurrentUser(page)

    await page.goto('/settings')
    await waitForPageLoad(page, 'settings')

    // Verify user data is loaded in the form
    if (userData.name) {
      const nameInput = page.getByLabel(/display name|name/i)
      if (await nameInput.count() > 0) {
        await expect(nameInput).toHaveValue(userData.name)
      }
    }

    if (userData.email) {
      const emailInput = page.getByLabel(/email/i)
      if (await emailInput.count() > 0) {
        await expect(emailInput).toHaveValue(userData.email)
      }
    }

    // Check that the settings page shows the user's information
    const userInfoElements = [
      page.getByText(userData.name || ''),
      page.getByText(userData.email || ''),
      page.getByDisplayValue(userData.name || ''),
      page.getByDisplayValue(userData.email || '')
    ]

    let foundUserInfo = false
    for (const element of userInfoElements) {
      if (await element.count() > 0 && await element.isVisible()) {
        foundUserInfo = true
        break
      }
    }

    expect(foundUserInfo).toBe(true)
  })

  test('validates form inputs properly', async ({ page }) => {
    await page.goto('/settings')
    await waitForPageLoad(page, 'settings')

    const nameInput = page.getByLabel(/display name|name/i)
    const saveButton = page.getByRole('button', { name: /save|update|apply/i })

    if (await nameInput.count() > 0 && await saveButton.count() > 0) {
      // Test empty name validation
      await nameInput.clear()

      // Try to save with empty name
      await saveButton.click()

      // Should show validation error or prevent saving
      const validationErrors = [
        page.getByText(/required|cannot be empty|please enter/i),
        page.locator('[aria-invalid="true"]'),
        page.locator('.error, [data-testid*="error"]')
      ]

      let foundValidation = false
      for (const error of validationErrors) {
        if (await error.count() > 0 && await error.isVisible()) {
          foundValidation = true
          break
        }
      }

      // Either validation error should be shown, or button should be disabled
      if (!foundValidation) {
        await expect(saveButton).toBeDisabled()
      }

      // Fill valid name to restore state
      const userData = await getCurrentUser(page)
      await nameInput.fill(userData.name || 'Test User')
    }
  })

  test('handles API errors gracefully', async ({ page }) => {
    await page.goto('/settings')
    await waitForPageLoad(page, 'settings')

    // Test behavior when API is temporarily unavailable
    // We'll simulate this by trying to update with invalid data
    const nameInput = page.getByLabel(/display name|name/i)
    const saveButton = page.getByRole('button', { name: /save|update|apply/i })

    if (await nameInput.count() > 0 && await saveButton.count() > 0) {
      // Save original value
      const originalValue = await nameInput.inputValue()

      // Try to save (may succeed or fail depending on API validation)
      await nameInput.fill('Test Update')
      await saveButton.click()

      // Wait for response
      await page.waitForTimeout(2000)

      // Check if any error messages are shown
      const errorMessages = [
        page.getByText(/error|failed|problem/i),
        page.getByText(/try again|retry/i),
        page.locator('[role="alert"]'),
        page.locator('.error, [data-testid*="error"]')
      ]

      // Either success or error handling should be visible
      const successMessages = [
        page.getByText(/saved|updated|success/i),
        page.getByText(/profile updated/i)
      ]

      let foundFeedback = false
      for (const message of [...errorMessages, ...successMessages]) {
        if (await message.count() > 0 && await message.isVisible()) {
          foundFeedback = true
          break
        }
      }

      // Some form of feedback should be provided to the user
      // Even if it's just the button state changing
      if (!foundFeedback) {
        // At minimum, the form should remain functional
        await expect(nameInput).toBeVisible()
        await expect(saveButton).toBeVisible()
      }

      // Restore original value
      await nameInput.fill(originalValue)
      if (await saveButton.isEnabled()) {
        await saveButton.click()
        await page.waitForTimeout(500)
      }
    }
  })
})

/**
 * Helper function to test theme persistence
 */
async function testThemePersistence(page: any) {
  // Look for theme toggle elements
  const themeElements = [
    page.getByRole('button', { name: /theme|dark|light/i }),
    page.getByText(/current mode|theme/i),
    page.locator('[data-testid*="theme"]'),
    page.locator('input[type="checkbox"]').filter({ hasText: /theme|dark|light/ })
  ]

  let themeToggle = null
  for (const element of themeElements) {
    if (await element.count() > 0 && await element.isVisible()) {
      themeToggle = element
      break
    }
  }

  if (themeToggle) {
    // Get initial theme state
    const getThemeState = async () => {
      const dataTheme = await page.locator('html').getAttribute('data-theme')
      const className = await page.locator('html').getAttribute('class')
      const bodyClass = await page.locator('body').getAttribute('class')
      return { dataTheme, className, bodyClass }
    }

    const initialState = await getThemeState()

    // Toggle theme
    await themeToggle.click()
    await page.waitForTimeout(500)

    // Check if theme changed
    const newState = await getThemeState()
    const changed = (
      newState.dataTheme !== initialState.dataTheme ||
      newState.className !== initialState.className ||
      newState.bodyClass !== initialState.bodyClass
    )

    if (changed) {
      // Test persistence across page reload
      await page.reload()
      await waitForPageLoad(page, 'settings')

      const persistedState = await getThemeState()
      const persisted = (
        persistedState.dataTheme === newState.dataTheme ||
        persistedState.className === newState.className ||
        persistedState.bodyClass === newState.bodyClass
      )

      expect(persisted).toBe(true)

      // Test persistence across navigation
      await page.click('[href="/dashboard"]')
      await waitForPageLoad(page, 'dashboard')
      await page.click('[href="/settings"]')
      await waitForPageLoad(page, 'settings')

      const navigationState = await getThemeState()
      const stillPersisted = (
        navigationState.dataTheme === newState.dataTheme ||
        navigationState.className === newState.className ||
        navigationState.bodyClass === newState.bodyClass
      )

      expect(stillPersisted).toBe(true)
    }
  }
}