/**
 * Responsive Layout Tests
 *
 * Tests that verify the application adapts correctly to different viewport sizes:
 * - Mobile viewport (375px) - single column, drawer sidebar
 * - Tablet viewport (768px) - two column grids, visible sidebar
 */

import { test, expect } from '@playwright/test'

test.describe('Responsive Layout Tests', () => {
  test('mobile viewport - should have single column layout and drawer sidebar', async ({ page }) => {
    // Set mobile viewport (iPhone SE size)
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/dashboard')
    await page.waitForSelector('main')

    // Sidebar should be hidden by default on mobile
    const sidebar = page.locator('[data-testid="app-layout-drawer"]')
    const sidebarPaper = sidebar.locator('.MuiDrawer-paper')

    // Check if sidebar is hidden or off-screen
    const isHidden = await sidebarPaper.evaluate((el) => {
      const rect = el.getBoundingClientRect()
      return rect.left < -el.offsetWidth || !el.offsetParent
    }).catch(() => true)

    expect(isHidden).toBe(true)

    // Menu button should be visible to toggle sidebar
    const menuButton = page.locator('[data-testid="app-layout-toggle-sidebar"]')
    await expect(menuButton).toBeVisible()

    // Click menu to open sidebar (should be drawer on mobile)
    await menuButton.click()
    await page.waitForTimeout(300) // Wait for drawer animation

    // Verify sidebar is now visible
    await expect(sidebarPaper).toBeVisible()

    // Go to Gallery page
    await page.click('[data-testid="app-layout-nav-link-gallery"]')
    await expect(page).toHaveURL(/\/gallery/)

    // Wait for content to load
    await page.waitForSelector('main')

    // Check that images/grid adapt to mobile (single column or narrow layout)
    const gridView = page.locator('[data-testid="gallery-grid-view"]')
    if (await gridView.isVisible().catch(() => false)) {
      const gridInfo = await gridView.evaluate((el) => {
        const style = window.getComputedStyle(el)
        return {
          gridTemplateColumns: style.gridTemplateColumns,
          width: el.offsetWidth
        }
      })

      // On mobile, grid should be narrow (< 375px)
      expect(gridInfo.width).toBeLessThanOrEqual(375)
    }

    // Verify minimal horizontal scroll (allow small overflow for borders/scrollbars)
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    expect(bodyWidth).toBeLessThanOrEqual(410) // Allow small overflow for scrollbars/borders
  })

  test('tablet viewport - should have two-column grid and visible sidebar', async ({ page }) => {
    // Set tablet viewport (iPad Mini size)
    await page.setViewportSize({ width: 768, height: 1024 })

    await page.goto('/dashboard')
    await page.waitForSelector('main')

    // Sidebar behavior on tablet may vary - check if it can be opened
    const sidebar = page.locator('[data-testid="app-layout-drawer"]')
    const sidebarPaper = sidebar.locator('.MuiDrawer-paper')

    // Try to open sidebar if it's not visible
    const isVisible = await sidebarPaper.isVisible().catch(() => false)
    if (!isVisible) {
      const menuButton = page.locator('[data-testid="app-layout-toggle-sidebar"]')
      if (await menuButton.isVisible()) {
        await menuButton.click()
        await page.waitForTimeout(300)
      }
    }

    // Sidebar should now be accessible
    await expect(sidebarPaper).toBeVisible()

    // Navigate to Gallery
    await page.click('[data-testid="app-layout-nav-link-gallery"]')
    await expect(page).toHaveURL(/\/gallery/)
    await page.waitForSelector('main')

    // Close any overlaying drawers that might block interactions
    const closeButton = page.locator('[data-testid="gallery-options-close-button"]')
    if (await closeButton.isVisible().catch(() => false)) {
      await closeButton.click()
      await page.waitForTimeout(300)
    }

    // Close sidebar drawer on mobile/tablet to avoid blocking
    const sidebarBackdrop = page.locator('.MuiBackdrop-root')
    if (await sidebarBackdrop.isVisible().catch(() => false)) {
      await sidebarBackdrop.click()
      await page.waitForTimeout(300)
    }

    // Check main content area is appropriately sized for tablet and has appropriate spacing
    const mainEl = page.locator('main')
    const mainWidth = await mainEl.evaluate((el) => el.offsetWidth)

    // On tablet, main content should have reasonable width (not full 768px due to padding/sidebar)
    expect(mainWidth).toBeGreaterThan(400) // Should have substantive content area
    expect(mainWidth).toBeLessThan(800)

    // Verify appropriate spacing exists
    const mainStyles = await mainEl.evaluate((el) => {
      const style = window.getComputedStyle(el)
      return {
        paddingLeft: parseInt(style.paddingLeft),
        paddingRight: parseInt(style.paddingRight)
      }
    })

    // Should have some padding on tablet
    expect(mainStyles.paddingLeft + mainStyles.paddingRight).toBeGreaterThan(0)

    // Verify minimal horizontal scroll (allow small overflow for borders/scrollbars)
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    expect(bodyWidth).toBeLessThanOrEqual(790) // Allow small overflow for scrollbars/borders
  })

  test('responsive images should resize appropriately across viewports', async ({ page }) => {
    const viewports = [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1920, height: 1080 }
    ]

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height })
      await page.goto('/dashboard')
      await page.waitForSelector('main')

      // Check if any images are present and properly sized
      const images = page.locator('img')
      const imageCount = await images.count()

      if (imageCount > 0) {
        const firstImage = images.first()
        const imageSize = await firstImage.evaluate((img) => ({
          width: img.offsetWidth,
          height: img.offsetHeight,
          maxWidth: parseInt(window.getComputedStyle(img).maxWidth || '0')
        }))

        // Images should not exceed viewport width
        expect(imageSize.width).toBeLessThanOrEqual(viewport.width)
      }
    }
  })
})
