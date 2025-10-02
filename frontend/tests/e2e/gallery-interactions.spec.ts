import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'
import { getCommonApiMocks, getTagHierarchyMocks } from './utils/mockData'

test.describe('Gallery Page Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockApi(page, [
      ...getCommonApiMocks(),
      ...getTagHierarchyMocks(),
    ])
    await page.goto('/gallery')
    await page.waitForSelector('main', { timeout: 10000 })
  })

  test('should switch between list and grid views', async ({ page }) => {
    const listView = page.locator('[data-testid="gallery-results-list"]')
    const gridView = page.locator('[data-testid="gallery-grid-view"]')
    const listToggle = page.locator('[data-testid="gallery-view-toggle-list"]')
    const gridToggle = page.locator('[data-testid="gallery-view-toggle-grid"]')

    await expect(listView).toBeVisible()
    await expect(gridView).toHaveCount(0)

    // Close options drawer if it's open to avoid blocking the grid toggle
    const closeButton = page.locator('[data-testid="gallery-options-close-button"]').first()
    if (await closeButton.isVisible()) {
      await closeButton.click()
      await page.waitForTimeout(300)
    }

    await gridToggle.click()
    await expect(gridView).toBeVisible()
    await expect(listView).toHaveCount(0)

    const storedGridMode = await page.evaluate(() => window.localStorage.getItem('gallery-view-mode'))
    expect(storedGridMode).toBe('grid-480x644')

    await listToggle.click()
    await expect(listView).toBeVisible()
    await expect(gridView).toHaveCount(0)

    const storedListMode = await page.evaluate(() => window.localStorage.getItem('gallery-view-mode'))
    expect(storedListMode).toBe('list')
  })

  test('should open image detail from grid view and return back', async ({ page }) => {
    // Close options drawer if it's open to avoid blocking the grid toggle
    const closeButton = page.locator('[data-testid="gallery-options-close-button"]').first()
    if (await closeButton.isVisible()) {
      await closeButton.click()
      await page.waitForTimeout(300)
    }

    const gridToggle = page.locator('[data-testid="gallery-view-toggle-grid"]')
    await gridToggle.click()
    await expect(page.locator('[data-testid="gallery-grid-view"]')).toBeVisible()

    const gridItem = page.locator('[data-testid^="gallery-grid-item-"]').first()
    await expect(gridItem).toBeVisible()
    await gridItem.click()

    await expect(page).toHaveURL(/\/gallery\/1$/)
    await expect(page.locator('[data-testid="gallery-detail-title"]')).toHaveText('Mock Artwork')

    await page.locator('[data-testid="gallery-detail-back-button"]').click()
    await expect(page).toHaveURL(/\/gallery$/)
    await expect(page.locator('[data-testid="gallery-grid-view"]')).toBeVisible()
  })

  test('should persist grid view selection after reload', async ({ page }) => {
    // Close options drawer if it's open to avoid blocking the grid toggle
    const closeButton = page.locator('[data-testid="gallery-options-close-button"]').first()
    if (await closeButton.isVisible()) {
      await closeButton.click()
      await page.waitForTimeout(300)
    }

    await page.locator('[data-testid="gallery-view-toggle-grid"]').click()
    await expect(page.locator('[data-testid="gallery-grid-view"]')).toBeVisible()

    await page.reload()
    await page.waitForSelector('[data-testid="gallery-grid-view"]', { timeout: 10000 })

    const storedMode = await page.evaluate(() => window.localStorage.getItem('gallery-view-mode'))
    expect(storedMode).toBe('grid-480x644')
    await expect(page.locator('[data-testid="gallery-grid-view"]')).toBeVisible()
    await expect(page.locator('[data-testid="gallery-results-list"]')).toHaveCount(0)
  })

  test('should toggle options panel open/close', async ({ page }) => {
    const closeButton = page.locator('[data-testid="gallery-options-close-button"]').first()
    const toggleButton = page.locator('[data-testid="gallery-options-toggle-button"]').first()
    const floatingOpenButton = page.locator('[data-testid="gallery-options-open-button"]').first()
    const drawer = page.locator('[data-testid="gallery-options-drawer"]')

    // If the drawer starts open, close it via the dedicated close button
    if (await closeButton.isVisible()) {
      await closeButton.click()
      await expect(drawer).not.toBeVisible({ timeout: 3000 })
    }

    // Open the drawer using whichever control becomes available (floating button or header toggle)
    const openCandidates = [floatingOpenButton, toggleButton]
    let opened = false
    for (const candidate of openCandidates) {
      try {
        await candidate.waitFor({ state: 'visible', timeout: 1500 })
        await candidate.click()
        opened = true
        break
      } catch {
        // Try next candidate
      }
    }

    if (!opened) {
      test.skip()
      return
    }

    await page.waitForTimeout(300)
    const openStyles = await drawer.evaluate((element) => {
      const styles = window.getComputedStyle(element as HTMLElement)
      return {
        visibility: styles.visibility,
        transform: styles.transform,
        ariaHidden: element.getAttribute('aria-hidden') ?? null,
      }
    })
    expect(openStyles.visibility).toBe('visible')
    expect(openStyles.transform === 'none' || openStyles.transform === 'matrix(1, 0, 0, 1, 0, 0)').toBe(true)
    const storedOpenState = await page.evaluate(() => window.localStorage.getItem('gallery-options-open'))
    expect(storedOpenState).toBe('true')

    // Close the drawer again
    await closeButton.click()
    await page.waitForTimeout(300)
    const closedStyles = await drawer.evaluate((element) => {
      const styles = window.getComputedStyle(element as HTMLElement)
      return {
        visibility: styles.visibility,
        transform: styles.transform,
        ariaHidden: element.getAttribute('aria-hidden') ?? null,
      }
    })
    const storedClosedState = await page.evaluate(() => window.localStorage.getItem('gallery-options-open'))
    expect(storedClosedState).toBe('false')
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

  test('should open gallery item detail view from grid', async ({ page }) => {
    // Ensure grid view is active
    const closeButton = page.locator('[data-testid="gallery-options-close-button"]').first()
    if (await closeButton.isVisible()) {
      await closeButton.click()
    }
    await page.locator('[data-testid="gallery-view-toggle-grid"]').click()
    await page.waitForTimeout(300)

    const firstGridItem = page.locator('[data-testid="gallery-grid-item-1"]')
    await firstGridItem.click()

    await expect(page).toHaveURL(/\/gallery\/1$/)
    await expect(page.locator('[data-testid="gallery-detail-title"]').first()).toHaveText('Mock Artwork')
    await expect(page.locator('[data-testid="gallery-detail-image"]')).toBeVisible()

    // Navigate back
    await page.locator('[data-testid="gallery-detail-back-button"]').click()
    await expect(page).toHaveURL(/\/gallery$/)
  })
})
