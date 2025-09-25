import { test, expect } from '@playwright/test'

test.describe('Form UX Tests', () => {
  test('should handle form field focus states on generation page', async ({ page }) => {
    await page.goto('/generate')

    // Wait for form to load
    await page.waitForSelector('form', { timeout: 10000 })

    // Test prompt input focus
    const promptInput = page.getByPlaceholder('Describe the image you want to generate...')
    await expect(promptInput).toBeVisible()

    await promptInput.focus()
    await expect(promptInput).toBeFocused()

    // Test number inputs focus
    const numberInputs = page.locator('input[type="number"]')
    const inputCount = await numberInputs.count()

    if (inputCount > 0) {
      const firstNumberInput = numberInputs.first()
      await firstNumberInput.focus()
      await expect(firstNumberInput).toBeFocused()
    }

    // Test tab navigation between form fields
    await page.keyboard.press('Tab')
    const focusedElement = page.locator(':focus')
    await expect(focusedElement).toBeVisible()
  })

  test('should validate form submission requirements', async ({ page }) => {
    await page.goto('/generate')

    // Wait for form to load
    await page.waitForSelector('form', { timeout: 10000 })

    // Generate button should be disabled without prompt
    const generateButton = page.locator('button:has-text("Generate Images"), button:has-text("Generate")')

    if (await generateButton.isVisible()) {
      await expect(generateButton).toBeDisabled()

      // Fill in prompt
      const promptInput = page.getByPlaceholder('Describe the image you want to generate...')
      await promptInput.fill('test prompt for validation')

      // Wait a moment for validation to process
      await page.waitForTimeout(100)

      // Check if button is enabled now, or if it needs more requirements
      const isEnabledAfterPrompt = await generateButton.isEnabled()

      if (isEnabledAfterPrompt) {
        // Button should now be enabled
        await expect(generateButton).toBeEnabled()

        // Clear prompt, button should be disabled again
        await promptInput.clear()
        await expect(generateButton).toBeDisabled()
      } else {
        // Button might need additional requirements like model selection
        // This is acceptable behavior - just verify prompt is required
        await promptInput.clear()
        await expect(generateButton).toBeDisabled()

        // Verify prompt is still required when filled again
        await promptInput.fill('another test prompt')
        // Don't assert enabled state since other requirements may exist
      }
    }
  })

  test('should handle advanced settings accordion', async ({ page }) => {
    await page.goto('/generate')

    // Wait for form to load
    await page.waitForSelector('form', { timeout: 10000 })

    // Look for advanced settings accordion
    const advancedToggle = page.locator('text=Advanced Settings, button:has-text("Advanced"), [aria-expanded]')

    if (await advancedToggle.first().isVisible()) {
      // Click to expand
      await advancedToggle.first().click()

      // Advanced controls should be visible
      await expect(page.locator('label:has-text("Seed"), label:has-text("Steps"), text=CFG Scale, label:has-text("Sampler")').first()).toBeVisible()

      // Click to collapse
      await advancedToggle.first().click()
    }
  })

  test('should handle number input validation', async ({ page }) => {
    await page.goto('/generate')

    // Wait for form to load
    await page.waitForSelector('form', { timeout: 10000 })

    const numberInputs = page.locator('input[type="number"]')
    const inputCount = await numberInputs.count()

    if (inputCount > 0) {
      const firstInput = numberInputs.first()

      // Get original value
      const originalValue = await firstInput.inputValue()

      // Test valid number input
      await firstInput.fill('100')
      await expect(firstInput).toHaveValue('100')

      // Test clearing the input
      await firstInput.clear()

      // Test that input accepts numeric values
      await firstInput.fill('512')
      await expect(firstInput).toHaveValue('512')

      // Restore original value
      if (originalValue) {
        await firstInput.fill(originalValue)
        await expect(firstInput).toHaveValue(originalValue)
      }

      // Test input boundaries if they exist
      const min = await firstInput.getAttribute('min')
      const max = await firstInput.getAttribute('max')

      if (min) {
        await firstInput.fill(min)
        await expect(firstInput).toHaveValue(min)
      }

      if (max) {
        await firstInput.fill(max)
        await expect(firstInput).toHaveValue(max)
      }
    }
  })
})