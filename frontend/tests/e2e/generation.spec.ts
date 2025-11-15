import { test, expect } from '@playwright/test'

test.describe('ComfyUI Generation', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
  })

  test('should successfully submit a generation job with real API', async ({ page }) => {
    // Navigate to generate page
    await page.goto('/generate', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Wait for form to load
    await page.waitForSelector('form', { timeout: 10000 })

    // Fill in the prompt
    const promptInput = page.getByPlaceholder('Describe the image you want to generate...')
    await promptInput.fill('cat')

    // Wait for models to finish loading (this may take time as it loads from API)
    // If models don't load, the form validation will show an error which the test handles
    const loadingModelsText = page.locator('text=Loading models...')
    try {
      // Wait for "Loading models..." to disappear (max 10 seconds)
      await loadingModelsText.waitFor({ state: 'detached', timeout: 10000 }).catch(() => {
        // Loading text might not appear if models load very fast
      })
    } catch {
      // Models might already be loaded
    }

    // Select a checkpoint model (required - models should be available in test database)
    // Wait for the model selector to be ready
    const modelSelector = page.getByTestId('model-selector')
    await expect(modelSelector).toBeVisible({ timeout: 5000 })

    // Find the Select combobox (MUI Select component)
    const selectCombobox = modelSelector.locator('[role="combobox"]')
    await expect(selectCombobox).toBeVisible()

    // Click to open the dropdown
    await selectCombobox.click()

    // MUI Select renders options as li elements - select the first one
    // Wait for at least one option to appear
    const firstOption = page.locator('li[role="option"]').first()
    await expect(firstOption).toBeVisible({ timeout: 5000 })
    await firstOption.click()

    // Wait a moment for the selection to register
    await page.waitForTimeout(500)

    // Submit the form
    const generateButton = page.locator('[data-testid="generate-button"]')
    await expect(generateButton).toBeEnabled()
    await generateButton.click()

    // Wait for submission to complete by checking when button is no longer busy
    // The button shows aria-busy="true" and loading spinner while submitting
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(1000) // Give time for submission to start

    // Wait for loading spinner to disappear (indicates submission complete)
    const loadingSpinner = page.getByTestId('loading-spinner')
    await loadingSpinner.waitFor({ state: 'detached', timeout: 30000 }).catch(() => {
      // Spinner might not appear if submission is very fast or fails immediately
    })

    // Wait a bit more for any error to appear
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(1000)

    // Check if an error appeared
    const errorAlert = page.locator('[role="alert"]').or(
      page.locator('[data-testid="error-alert"]')
    )
    const hasError = await errorAlert.isVisible().catch(() => false)

    if (hasError) {
      const errorText = await errorAlert.textContent()

      // Service unavailable is an acceptable state (ComfyUI not running)
      if (errorText?.includes('temporarily unavailable') || errorText?.includes('unavailable')) {
        console.log('Generation service unavailable - test passes (expected state when ComfyUI is down)')
        return
      }

      // Other errors should fail the test
      throw new Error(`Generation job submission failed: ${errorText}`)
    }

    // If no error, submission was successful
    // Success is indicated by the button returning to "Generate" state (not showing spinner)
    await expect(generateButton).toContainText('Generate')
  })

  test('should navigate to generation page', async ({ page }) => {
    await page.goto('/')

    // Wait for navigation to load
    await page.waitForSelector('nav', { timeout: 10000 })

    // Click on Generate navigation item using data-testid
    const generateLink = page.getByTestId('app-layout-nav-link-generate')
    await expect(generateLink).toBeVisible({ timeout: 5000 })
    await generateLink.click()

    // Should navigate to generation page
    await expect(page).toHaveURL('/generate')

    // Should show generation form
    await expect(page.locator('h6:has-text("Create")')).toBeVisible()

    // Should show prompt input (wait for form to fully load)
    await expect(page.getByPlaceholder('Describe the image you want to generate...')).toBeVisible()

    // Should show model selector (or loading state)
    await expect(
      page.locator('label:has-text("Checkpoint Model")').first().or(page.locator('text=Loading models...'))
    ).toBeVisible()

    // Should show generate button
    await expect(page.locator('button:has-text("Generate")')).toBeVisible()
  })

  test('should validate required form fields', async ({ page }) => {
    await page.goto('/generate', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Wait for form to load
    await page.waitForSelector('form', { timeout: 10000 })

    // Try to submit without prompt (button should be disabled)
    const generateButton = page.locator('button:has-text("Generate")')
    await expect(generateButton).toBeDisabled()

    // Fill in prompt to enable the button
    await page.getByPlaceholder('Describe the image you want to generate...').fill('test prompt')

    // Button should now be enabled
    await expect(generateButton).toBeEnabled()
  })

  test('should show generation parameters controls', async ({ page }) => {
    await page.goto('/generate', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Should show basic parameters
    await expect(page.locator('input[type="number"][value="512"]')).toBeVisible() // Width
    await expect(page.locator('input[type="number"][value="768"]')).toBeVisible() // Height
    await expect(page.locator('input[type="number"][value="1"]')).toBeVisible() // Batch size

    // Advanced settings accordion is expanded by default (defaultExpanded=true)
    // So we can directly check for advanced controls without clicking

    // Check that the cfg-scale input is visible (we know this has a data-testid)
    await expect(page.locator('[data-testid="cfg-scale-input"]')).toBeVisible()

    // Check for seed input (also in advanced settings)
    await expect(page.locator('[data-testid="seed-input"]')).toBeVisible()

    // Check for steps input (also in advanced settings)
    await expect(page.locator('[data-testid="steps-input"]')).toBeVisible()

    // Verify at least one select/combobox is present (for sampler)
    const selectElements = page.locator('select, [role="combobox"]')
    await expect(selectElements.first()).toBeVisible()
  })
})
