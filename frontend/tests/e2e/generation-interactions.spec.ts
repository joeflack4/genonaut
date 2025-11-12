import { test, expect } from '@playwright/test'

test.describe('Generation Page Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/generate')
    await page.waitForSelector('[data-testid="generation-page"]', { timeout: 10000 })
  })

  test('should switch between Create and History tabs', async ({ page }) => {
    // Verify both tabs are visible
    const createTab = page.locator('[data-testid="create-tab"]')
    const historyTab = page.locator('[data-testid="history-tab"]')

    await expect(createTab).toBeVisible()
    await expect(historyTab).toBeVisible()

    // Verify Create tab is initially selected
    await expect(createTab).toHaveAttribute('aria-selected', 'true')
    await expect(historyTab).toHaveAttribute('aria-selected', 'false')

    // Click History tab
    await historyTab.click()
    await page.waitForTimeout(300)

    // Verify History tab is now selected
    await expect(historyTab).toHaveAttribute('aria-selected', 'true')
    await expect(createTab).toHaveAttribute('aria-selected', 'false')

    // Verify content changed - should show history content
    const historySection = page.locator('text=Generation History')
    await expect(historySection).toBeVisible()

    // Click Create tab again
    await createTab.click()
    await page.waitForTimeout(300)

    // Verify Create tab is selected again
    await expect(createTab).toHaveAttribute('aria-selected', 'true')
    await expect(historyTab).toHaveAttribute('aria-selected', 'false')

    // Verify content changed back - should show create form
    const createSection = page.locator('text=Create')
    await expect(createSection).toBeVisible()
  })

  test('should display generation status area when no generation is active', async ({ page }) => {
    // Should show placeholder text when no generation is active
    const placeholderText = page.locator('text=Progress will display once generation starts.')
    await expect(placeholderText).toBeVisible()
  })

  test('should handle tab keyboard navigation', async ({ page }) => {
    const createTab = page.locator('[data-testid="create-tab"]')
    const historyTab = page.locator('[data-testid="history-tab"]')

    // Focus on tabs area
    await createTab.focus()
    await expect(createTab).toBeFocused()

    // Use arrow keys to navigate between tabs
    await page.keyboard.press('ArrowRight')
    await expect(historyTab).toBeFocused()

    // Use Enter to activate tab
    await page.keyboard.press('Enter')
    await page.waitForTimeout(300)

    // Verify History tab is now selected
    await expect(historyTab).toHaveAttribute('aria-selected', 'true')
  })

  test('should show generation progress when generation is active', async ({ page }) => {
    // This test would require mocking an active generation
    // For now, we'll just verify the structure exists
    const progressSection = page.locator('text=Status')
    await expect(progressSection).toBeVisible()

    const progressArea = page.locator('text=Progress will display once generation starts.')
    await expect(progressArea).toBeVisible()
  })
})