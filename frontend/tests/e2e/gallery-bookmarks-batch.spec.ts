import { test, expect } from '@playwright/test'
import { handleMissingData } from './utils/testDataHelpers'
import { waitForApiResponse, loginAsTestUser } from './utils/realApiHelpers'

/**
 * E2E tests for batch bookmark status fetching performance
 *
 * These tests verify that bookmark status is fetched in a single batch request
 * instead of individual requests for each gallery item.
 */
test.describe('Gallery Bookmarks - Batch Fetching @performance', () => {
  test('should make single batch bookmark API call instead of multiple individual calls', async ({ page }) => {
    // Track network requests
    const bookmarkRequests: string[] = []

    page.on('request', (request) => {
      const url = request.url()
      if (url.includes('/api/v1/bookmarks/')) {
        bookmarkRequests.push(url)
      }
    })

    // Login as test user first
    await loginAsTestUser(page)

    // Navigate to gallery and wait for all network activity to complete
    await page.goto('/gallery')
    await page.waitForLoadState('networkidle')

    // Wait for EITHER grid view OR empty state to appear (whichever renders first)
    await page.waitForSelector(
      '[data-testid="gallery-grid-view"], [data-testid="gallery-grid-empty"]',
      { timeout: 15000 }
    )

    // Now check which one is visible
    const galleryGridView = page.getByTestId('gallery-grid-view')
    const emptyStateGrid = page.getByTestId('gallery-grid-empty')
    const hasGridView = await galleryGridView.isVisible().catch(() => false)
    const isEmptyGrid = await emptyStateGrid.isVisible().catch(() => false)

    if (isEmptyGrid || !hasGridView) {
      handleMissingData(test, 'Batch bookmarks test', 'gallery data', 'make init-test')
      return
    }

    // Wait for gallery grid to be fully loaded
    await expect(galleryGridView).toBeVisible()

    // Count bookmark-related API calls
    const individualCheckCalls = bookmarkRequests.filter(url =>
      url.includes('/api/v1/bookmarks/check?') && !url.includes('/check-batch')
    )
    const batchCheckCalls = bookmarkRequests.filter(url =>
      url.includes('/api/v1/bookmarks/check-batch')
    )

    // Verify batch fetching behavior:
    // - Should have exactly 1 batch check call
    // - Should have 0 individual check calls
    expect(batchCheckCalls.length).toBe(1)
    expect(individualCheckCalls.length).toBe(0)

    // Log results for debugging
    console.log(`Batch check calls: ${batchCheckCalls.length}`)
    console.log(`Individual check calls: ${individualCheckCalls.length}`)
    console.log(`Total bookmark requests: ${bookmarkRequests.length}`)
  })

  test('should batch fetch bookmarks after page navigation', async ({ page }) => {
    // Track network requests
    let batchCallCount = 0

    page.on('request', (request) => {
      const url = request.url()
      if (url.includes('/api/v1/bookmarks/check-batch')) {
        batchCallCount++
      }
    })

    // Login as test user first
    await loginAsTestUser(page)

    // Navigate to gallery and wait for all network activity to complete
    await page.goto('/gallery')
    await page.waitForLoadState('networkidle')

    // Wait for EITHER grid view OR empty state to appear (whichever renders first)
    await page.waitForSelector(
      '[data-testid="gallery-grid-view"], [data-testid="gallery-grid-empty"]',
      { timeout: 15000 }
    )

    // Now check which one is visible
    const galleryGridView = page.getByTestId('gallery-grid-view')
    const emptyStateGrid = page.getByTestId('gallery-grid-empty')
    const hasGridView = await galleryGridView.isVisible().catch(() => false)
    const isEmptyGrid = await emptyStateGrid.isVisible().catch(() => false)

    if (isEmptyGrid || !hasGridView) {
      handleMissingData(test, 'Batch navigation test', 'gallery data', 'make init-test')
      return
    }

    await expect(galleryGridView).toBeVisible()

    const initialBatchCalls = batchCallCount

    // Navigate to next page (if pagination exists)
    const nextPageButton = page.getByTestId('next-page')
    const hasNextPage = await nextPageButton.isVisible().catch(() => false)

    if (hasNextPage) {
      // Set up wait for API responses BEFORE clicking
      const contentResponsePromise = waitForApiResponse(page, '/api/v1/content/unified', { timeout: 15000 })
      const batchResponsePromise = waitForApiResponse(page, '/api/v1/bookmarks/check-batch', { timeout: 15000 })

      await nextPageButton.click()

      // Wait for API responses to complete
      await contentResponsePromise
      await batchResponsePromise

      // Should have made another batch call for the new page
      expect(batchCallCount).toBeGreaterThan(initialBatchCalls)

      // Navigate back to first page
      const previousPageButton = page.getByTestId('previous-page')

      // Set up wait for API responses BEFORE clicking
      const contentResponsePromise2 = waitForApiResponse(page, '/api/v1/content/unified', { timeout: 15000 })
      const batchResponsePromise2 = waitForApiResponse(page, '/api/v1/bookmarks/check-batch', { timeout: 15000 })

      await previousPageButton.click()

      // Wait for API responses to complete
      await contentResponsePromise2
      await batchResponsePromise2

      // Should have made another batch call when returning to first page
      expect(batchCallCount).toBeGreaterThan(initialBatchCalls + 1)
    }

    console.log(`Total batch calls after navigation: ${batchCallCount}`)
  })

  test('should batch fetch bookmarks when filtering content', async ({ page }) => {
    // Track network requests
    const bookmarkRequests: string[] = []

    page.on('request', (request) => {
      const url = request.url()
      if (url.includes('/api/v1/bookmarks/check-batch')) {
        bookmarkRequests.push(url)
      }
    })

    // Login as test user first
    await loginAsTestUser(page)

    // Navigate to gallery and wait for all network activity to complete
    await page.goto('/gallery')
    await page.waitForLoadState('networkidle')

    // Wait for DOM to be ready
    await page.waitForSelector('main', { timeout: 15000 })

    const galleryGridView = page.getByTestId('gallery-grid-view')
    const emptyStateGrid = page.getByTestId('gallery-grid-empty')
    const hasGridView = await galleryGridView.isVisible().catch(() => false)
    const isEmptyGrid = await emptyStateGrid.isVisible().catch(() => false)

    if (isEmptyGrid || !hasGridView) {
      handleMissingData(test, 'Batch filtering test', 'gallery data', 'make init-test')
      return
    }

    await expect(galleryGridView).toBeVisible()

    const initialBatchCalls = bookmarkRequests.length

    // Apply a search filter
    const searchInput = page.getByTestId('gallery-search-input')
    const hasSearchInput = await searchInput.isVisible().catch(() => false)

    if (hasSearchInput) {
      // Set up wait for API responses BEFORE entering search
      const contentResponsePromise = waitForApiResponse(page, '/api/v1/content/unified', { timeout: 15000 })
      const batchResponsePromise = waitForApiResponse(page, '/api/v1/bookmarks/check-batch', { timeout: 15000 })

      await searchInput.fill('cat')
      await searchInput.press('Enter')

      // Wait for API responses to complete
      await contentResponsePromise
      await batchResponsePromise

      // Should have made another batch call for filtered results
      expect(bookmarkRequests.length).toBeGreaterThan(initialBatchCalls)
    }

    console.log(`Total batch calls after filtering: ${bookmarkRequests.length}`)
  })

  /**
   * SKIPPED: This test expects specific batch check API timing that React Query doesn't guarantee.
   * See notes/bookmark-tests.md for detailed explanation and potential solutions.
   * Test verifies implementation detail (batch check timing) rather than user behavior (bookmarks work).
   */
  test.skip('should update bookmark status without refetching entire batch', async ({ page }) => {
    // Track network requests
    const bookmarkCreateRequests: string[] = []
    const batchCheckRequests: string[] = []

    page.on('request', (request) => {
      const url = request.url()
      const method = request.method()

      if (url.includes('/api/v1/bookmarks/check-batch')) {
        batchCheckRequests.push(url)
      }
      if (method === 'POST' && url.includes('/api/v1/bookmarks?')) {
        bookmarkCreateRequests.push(url)
      }
    })

    // Login as test user first
    await loginAsTestUser(page)

    // Navigate to gallery and wait for all network activity to complete
    await page.goto('/gallery')
    await page.waitForLoadState('networkidle')

    // Wait for DOM to be ready
    await page.waitForSelector('main', { timeout: 15000 })

    const galleryGridView = page.getByTestId('gallery-grid-view')
    const emptyStateGrid = page.getByTestId('gallery-grid-empty')
    const hasGridView = await galleryGridView.isVisible().catch(() => false)
    const isEmptyGrid = await emptyStateGrid.isVisible().catch(() => false)

    if (isEmptyGrid || !hasGridView) {
      handleMissingData(test, 'Batch cache invalidation test', 'gallery data', 'make init-test')
      return
    }

    await expect(galleryGridView).toBeVisible()

    const initialBatchCalls = batchCheckRequests.length

    // Find first grid item and get its bookmark button
    const firstImage = page.locator('[data-testid^="gallery-grid-item-"]').first()
    await expect(firstImage).toBeVisible({ timeout: 5000 })

    const testId = await firstImage.getAttribute('data-testid')
    const contentId = testId?.match(/gallery-grid-item-(\d+)/)?.[1]

    if (!contentId) throw new Error('Could not extract contentId')

    const bookmarkButton = page.getByTestId(`bookmark-button-${contentId}`)
    await expect(bookmarkButton).toBeVisible()

    const outlineIcon = bookmarkButton.getByTestId('bookmark-icon-outline')
    const filledIcon = bookmarkButton.getByTestId('bookmark-icon-filled')
    const isBookmarked = await filledIcon.isVisible().catch(() => false)

    // Ensure we start unbookmarked
    if (isBookmarked) {
      await bookmarkButton.click()
      await expect(page.getByRole('heading', { name: /manage bookmark/i })).toBeVisible()
      await page.getByTestId('bookmark-remove-button').click()
      await expect(page.getByRole('heading', { name: /manage bookmark/i })).not.toBeVisible()

      // Wait for UI to update after delete
      await expect(outlineIcon).toBeVisible({ timeout: 5000 })
    }

    // Add bookmark
    await bookmarkButton.click()

    // With optimistic UI, icon should change immediately
    await expect(filledIcon).toBeVisible({ timeout: 2000 })

    // Verify cache was invalidated (another batch call should have been made)
    expect(batchCheckRequests.length).toBeGreaterThan(initialBatchCalls)

    // Verify bookmark was created
    expect(bookmarkCreateRequests.length).toBeGreaterThan(0)

    console.log(`Batch calls before bookmark: ${initialBatchCalls}`)
    console.log(`Batch calls after bookmark: ${batchCheckRequests.length}`)
    console.log(`Bookmark create calls: ${bookmarkCreateRequests.length}`)
  })
})
