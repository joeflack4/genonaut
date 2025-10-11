import { test, expect } from '@playwright/test'

test.describe('ComfyUI Generation', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
  })
  test('should navigate to generation page', async ({ page }) => {
    await page.goto('/')

    // Wait for navigation to load
    await page.waitForSelector('nav')

    // Click on Generate navigation item
    await page.click('[href="/generate"]')

    // Should navigate to generation page
    await expect(page).toHaveURL('/generate')

    // Should show generation form
    await expect(page.locator('h6:has-text("Create New Generation")')).toBeVisible()

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
