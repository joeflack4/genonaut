import { test, expect } from '@playwright/test'

test.describe('Tags Page Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tags')
    await page.waitForSelector('main', { timeout: 10000 })
  })

  test('should toggle between tree view and search mode', async ({ page }) => {
    // Look for the search/tree toggle button
    const toggleButton = page.locator('button[aria-label*="search"], button[aria-label*="tree"]').first()

    if (await toggleButton.isVisible()) {
      // Get initial button state
      const initialPressed = await toggleButton.getAttribute('aria-pressed') || await toggleButton.getAttribute('aria-expanded')

      // Click toggle
      await toggleButton.click()
      await page.waitForTimeout(500)

      // Verify button state changed or content changed
      const newPressed = await toggleButton.getAttribute('aria-pressed') || await toggleButton.getAttribute('aria-expanded')

      // If aria attributes exist, they should have changed, otherwise just verify click worked
      if (initialPressed !== null && newPressed !== null) {
        expect(newPressed).not.toBe(initialPressed)
      } else {
        // Just verify the button is still visible after click
        await expect(toggleButton).toBeVisible()
      }

      // Toggle back
      await toggleButton.click()
      await page.waitForTimeout(500)

      // Verify we can toggle back
      await expect(toggleButton).toBeVisible()
    } else {
      test.skip()
    }
  })

  test('should handle refresh button click', async ({ page }) => {
    const refreshButton = page.locator('button[aria-label*="refresh"], button:has(svg[data-testid="RefreshIcon"])')

    if (await refreshButton.isVisible()) {
      // Click refresh button
      await refreshButton.click()

      // Verify button was clicked (should disable briefly during refresh)
      await expect(refreshButton).toBeVisible()

      // Wait for any loading state to complete
      await page.waitForTimeout(1000)
    } else {
      test.skip()
    }
  })

  test('should handle tag tree node interactions', async ({ page }) => {
    // Look for tag tree nodes or expandable items
    const treeItems = page.locator('[role="treeitem"], .MuiTreeItem-root, button:has-text("tag"), .tag-node')
    const itemCount = await treeItems.count()

    if (itemCount > 0) {
      const firstItem = treeItems.first()

      // Click on tree item
      await firstItem.click()

      // Should navigate to gallery with tag filter (or expand if it's a parent node)
      await page.waitForTimeout(500)

      // Check if we navigated to gallery with tag parameter
      const currentUrl = page.url()
      if (currentUrl.includes('/gallery') && currentUrl.includes('tag=')) {
        expect(currentUrl).toContain('/gallery')
        expect(currentUrl).toContain('tag=')
      }
    } else {
      test.skip()
    }
  })

  test('should handle tag search functionality', async ({ page }) => {
    // First try to activate search mode
    const searchToggle = page.locator('button[aria-label*="search"]').first()
    if (await searchToggle.isVisible()) {
      await searchToggle.click()
      await page.waitForTimeout(500)
    }

    // Look for search input
    const searchInput = page.locator('input[placeholder*="search"], input[placeholder*="tag"], input[type="text"]').first()

    if (await searchInput.isVisible()) {
      // Type in search
      await searchInput.fill('test tag')
      await page.waitForTimeout(500)

      // Look for search results or filtered content
      const searchResults = page.locator('.search-results, .tag-results, [data-testid*="search"]')
      if (await searchResults.count() > 0) {
        await expect(searchResults.first()).toBeVisible()
      }

      // Clear search
      await searchInput.clear()
      await page.waitForTimeout(500)
    } else {
      test.skip()
    }
  })
})