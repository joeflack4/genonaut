import { test, expect } from '@playwright/test'
import { handleMissingData } from './utils/testDataHelpers'
import { waitForPageLoad } from './utils/realApiHelpers'

test.describe('Gallery Bookmarks', () => {
  test('bookmark button appears in gallery grid cells', async ({ page }) => {
    // Navigate to gallery
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Wait for gallery results to load
    const galleryGridView = page.getByTestId('gallery-grid-view')
    const emptyStateGrid = page.getByTestId('gallery-grid-empty')
    const hasGridView = await galleryGridView.isVisible().catch(() => false)
    const isEmptyGrid = await emptyStateGrid.isVisible().catch(() => false)

    if (isEmptyGrid || !hasGridView) {
      handleMissingData(test, 'Gallery bookmarks test', 'gallery data', 'make init-test')
      return
    }

    await expect(galleryGridView).toBeVisible()

    // Find first grid item
    const firstImage = page.locator('[data-testid^="gallery-grid-item-"]').first()
    await expect(firstImage).toBeVisible({ timeout: 5000 })

    // Extract content ID from data-testid
    const testId = await firstImage.getAttribute('data-testid')
    const contentId = testId?.match(/gallery-grid-item-(\d+)/)?.[1]

    if (!contentId) {
      throw new Error('Could not extract contentId from grid item')
    }

    // Check that bookmark button is present in the grid cell
    const bookmarkButton = page.getByTestId(`bookmark-button-${contentId}`)
    await expect(bookmarkButton).toBeVisible()
  })

  test('bookmark button does NOT appear in dashboard grid cells', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Wait for dashboard to load
    const dashboardPage = page.getByTestId('dashboard-page')
    await expect(dashboardPage).toBeVisible({ timeout: 5000 })

    // Find any grid items on dashboard (there are multiple grids)
    const gridItems = page.locator('[data-testid^="gallery-grid-item-"]')
    const gridItemCount = await gridItems.count()

    if (gridItemCount > 0) {
      // Check first grid item for bookmark button
      const firstItem = gridItems.first()
      const testId = await firstItem.getAttribute('data-testid')
      const contentId = testId?.match(/gallery-grid-item-(\d+)/)?.[1]

      if (contentId) {
        // Verify bookmark button is NOT present
        const bookmarkButton = page.getByTestId(`bookmark-button-${contentId}`)
        await expect(bookmarkButton).not.toBeVisible()
      }
    }
  })

  test('can add bookmark from gallery grid cell', async ({ page }) => {
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    const galleryGridView = page.getByTestId('gallery-grid-view')
    const emptyStateGrid = page.getByTestId('gallery-grid-empty')
    const hasGridView = await galleryGridView.isVisible().catch(() => false)
    const isEmptyGrid = await emptyStateGrid.isVisible().catch(() => false)

    if (isEmptyGrid || !hasGridView) {
      handleMissingData(test, 'Add bookmark from grid test', 'gallery data', 'make init-test')
      return
    }

    // Find first grid item
    const firstImage = page.locator('[data-testid^="gallery-grid-item-"]').first()
    await expect(firstImage).toBeVisible({ timeout: 5000 })

    const testId = await firstImage.getAttribute('data-testid')
    const contentId = testId?.match(/gallery-grid-item-(\d+)/)?.[1]

    if (!contentId) throw new Error('Could not extract contentId')

    const bookmarkButton = page.getByTestId(`bookmark-button-${contentId}`)
    await expect(bookmarkButton).toBeVisible()

    // Check if already bookmarked
    const filledIcon = bookmarkButton.getByTestId('bookmark-icon-filled')
    const outlineIcon = bookmarkButton.getByTestId('bookmark-icon-outline')
    const isBookmarked = await filledIcon.isVisible().catch(() => false)

    // If already bookmarked, remove it first
    if (isBookmarked) {
      await bookmarkButton.click()
      await expect(page.getByRole('heading', { name: /manage bookmark/i })).toBeVisible()
      await page.getByTestId('bookmark-remove-button').click()
      await expect(page.getByRole('heading', { name: /manage bookmark/i })).not.toBeVisible()
      await expect(outlineIcon).toBeVisible({ timeout: 3000 })
    }

    // Now add bookmark
    await bookmarkButton.click()

    // Wait for icon to change to filled
    await expect(filledIcon).toBeVisible({ timeout: 3000 })
    await expect(outlineIcon).not.toBeVisible()

    // Verify tooltip changed
    await expect(bookmarkButton).toHaveAttribute('aria-label', 'Manage bookmark')
  })

  test('can remove bookmark from grid cell modal', async ({ page }) => {
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    const galleryGridView = page.getByTestId('gallery-grid-view')
    const emptyStateGrid = page.getByTestId('gallery-grid-empty')
    const hasGridView = await galleryGridView.isVisible().catch(() => false)
    const isEmptyGrid = await emptyStateGrid.isVisible().catch(() => false)

    if (isEmptyGrid || !hasGridView) {
      handleMissingData(test, 'Remove bookmark from grid test', 'gallery data', 'make init-test')
      return
    }

    // Find first grid item
    const firstImage = page.locator('[data-testid^="gallery-grid-item-"]').first()
    await expect(firstImage).toBeVisible({ timeout: 5000 })

    const testId = await firstImage.getAttribute('data-testid')
    const contentId = testId?.match(/gallery-grid-item-(\d+)/)?.[1]

    if (!contentId) throw new Error('Could not extract contentId')

    const bookmarkButton = page.getByTestId(`bookmark-button-${contentId}`)
    await expect(bookmarkButton).toBeVisible()

    const filledIcon = bookmarkButton.getByTestId('bookmark-icon-filled')
    const outlineIcon = bookmarkButton.getByTestId('bookmark-icon-outline')

    // Ensure it's bookmarked
    const isBookmarked = await filledIcon.isVisible().catch(() => false)

    if (!isBookmarked) {
      await bookmarkButton.click()
      await expect(filledIcon).toBeVisible({ timeout: 3000 })
    }

    // Open modal
    await bookmarkButton.click()
    await expect(page.getByRole('heading', { name: /manage bookmark/i })).toBeVisible()

    // Remove bookmark
    await page.getByTestId('bookmark-remove-button').click()

    // Verify modal closed
    await expect(page.getByRole('heading', { name: /manage bookmark/i })).not.toBeVisible()

    // Verify bookmark removed (outline icon visible)
    await expect(outlineIcon).toBeVisible({ timeout: 3000 })
    await expect(filledIcon).not.toBeVisible()
  })
})
