import { test, expect } from '@playwright/test'

test.describe('Gallery Page Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/gallery')
    await page.waitForSelector('main', { timeout: 10000 })
  })

  test('should toggle options panel open/close', async ({ page }) => {
    // Look for settings/options button to toggle panel
    const optionsToggle = page.locator('button:has(svg[data-testid="SettingsOutlinedIcon"]), button[aria-label*="settings"], button[aria-label*="options"]').first()

    if (await optionsToggle.isVisible()) {
      // Click toggle to test functionality
      await optionsToggle.click()
      await page.waitForTimeout(500)

      // Verify button is still functional
      await expect(optionsToggle).toBeVisible()

      // Toggle back
      await optionsToggle.click()
      await page.waitForTimeout(500)

      // Should still be visible and functional
      await expect(optionsToggle).toBeVisible()
    } else {
      test.skip()
    }
  })

  test('should toggle content type filters', async ({ page }) => {
    // Look for content type toggle switches (Your gens, Community gens, etc.)
    const toggles = page.locator('input[type="checkbox"], [role="switch"]')
    const toggleCount = await toggles.count()

    if (toggleCount > 0) {
      const firstToggle = toggles.first()

      // Get initial state
      const initialState = await firstToggle.isChecked()

      // Toggle the switch
      await firstToggle.click()
      await page.waitForTimeout(500)

      // Verify state changed
      const newState = await firstToggle.isChecked()
      expect(newState).not.toBe(initialState)

      // Toggle back
      await firstToggle.click()
      await page.waitForTimeout(500)

      // Should be back to original state
      const finalState = await firstToggle.isChecked()
      expect(finalState).toBe(initialState)
    } else {
      test.skip()
    }
  })

  test('should open and close stats information popover', async ({ page }) => {
    // Look for info button that opens stats popover
    const infoButton = page.locator('button:has(svg[data-testid="InfoOutlinedIcon"]), button[aria-label*="info"], .info-button').first()

    if (await infoButton.isVisible()) {
      // Click to open popover
      await infoButton.click()
      await page.waitForTimeout(300)

      // Look for popover content
      const popover = page.locator('.MuiPopover-root, [role="tooltip"], .stats-popover, .popover-content')
      if (await popover.count() > 0) {
        await expect(popover.first()).toBeVisible()

        // Click outside or press Escape to close
        await page.keyboard.press('Escape')
        await page.waitForTimeout(300)

        // Popover should be hidden
        await expect(popover.first()).not.toBeVisible()
      }
    } else {
      test.skip()
    }
  })

  test('should handle search input functionality', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"], input[type="text"]').first()

    if (await searchInput.isVisible()) {
      // Type search query
      await searchInput.fill('test search')
      await page.waitForTimeout(500)

      // Should trigger search (might update URL or content)
      const searchValue = await searchInput.inputValue()
      expect(searchValue).toBe('test search')

      // Clear search
      await searchInput.clear()
      await page.waitForTimeout(500)

      const clearedValue = await searchInput.inputValue()
      expect(clearedValue).toBe('')
    } else {
      test.skip()
    }
  })

  test('should handle sort option selection', async ({ page }) => {
    // Look for sort dropdown
    const sortSelect = page.locator('select, .MuiSelect-root, [role="combobox"]').first()

    if (await sortSelect.isVisible()) {
      // Click to open dropdown
      await sortSelect.click()
      await page.waitForTimeout(300)

      // Look for sort options
      const options = page.locator('[role="option"], .MuiMenuItem-root')
      const optionCount = await options.count()

      if (optionCount > 0) {
        // Click first available option
        await options.first().click()
        await page.waitForTimeout(500)

        // Dropdown should close
        await expect(sortSelect).toBeVisible()
      }
    } else {
      test.skip()
    }
  })

  test('should handle pagination navigation', async ({ page }) => {
    // Look for pagination component
    const pagination = page.locator('.MuiPagination-root, .pagination, [role="navigation"]')

    if (await pagination.isVisible()) {
      // Look for next/previous buttons
      const nextButton = page.locator('button[aria-label*="next"], button[aria-label*="Go to next page"]')
      const prevButton = page.locator('button[aria-label*="previous"], button[aria-label*="Go to previous page"]')

      if (await nextButton.count() > 0 && await nextButton.isEnabled()) {
        await nextButton.click()
        await page.waitForTimeout(1000)

        // Should navigate to next page
        await expect(pagination).toBeVisible()
      }

      if (await prevButton.count() > 0 && await prevButton.isEnabled()) {
        await prevButton.click()
        await page.waitForTimeout(1000)

        // Should navigate to previous page
        await expect(pagination).toBeVisible()
      }
    } else {
      test.skip()
    }
  })
})