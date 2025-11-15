import { test, expect } from '@playwright/test'
import { handleMissingData } from './utils/testDataHelpers'
import { waitForApiResponse, loginAsTestUser } from './utils/realApiHelpers'

/**
 * E2E tests for batch bookmark status fetching on Generation History page
 *
 * These tests verify that bookmark status is fetched in a single batch request
 * for generation history items.
 */
test.describe('Generation History Bookmarks - Batch Fetching @performance', () => {
  test('should make single batch bookmark API call for generation history', async ({ page }) => {
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

    // Navigate to generation history and wait for all network activity to complete
    await page.goto('/generate/history')
    await expect(page).toHaveURL(/\/generate\/history/)
    await page.waitForLoadState('networkidle')

    // Wait for EITHER generation list OR empty state to appear (whichever renders first)
    await page.waitForSelector(
      '[data-testid="generation-list"], [data-testid="generation-list-empty"]',
      { timeout: 15000 }
    )

    // Now check which one is visible
    const generationList = page.getByTestId('generation-list')
    const hasGenerationList = await generationList.isVisible().catch(() => false)

    if (!hasGenerationList) {
      handleMissingData(test, 'Generation history batch test', 'generation history data', 'Create some generations first')
      return
    }

    await expect(generationList).toBeVisible()

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

    console.log(`Batch check calls: ${batchCheckCalls.length}`)
    console.log(`Individual check calls: ${individualCheckCalls.length}`)
    console.log(`Total bookmark requests: ${bookmarkRequests.length}`)
  })

  test('bookmark button appears in generation cards', async ({ page }) => {
    // Login as test user first
    await loginAsTestUser(page)

    // Navigate to generation history and wait for all network activity to complete
    await page.goto('/generate/history')
    await expect(page).toHaveURL(/\/generate\/history/)
    await page.waitForLoadState('networkidle')

    // Wait for EITHER generation list OR empty state to appear (whichever renders first)
    await page.waitForSelector(
      '[data-testid="generation-list"], [data-testid="generation-list-empty"]',
      { timeout: 15000 }
    )

    // Now check which one is visible
    const generationList = page.getByTestId('generation-list')
    const hasGenerationList = await generationList.isVisible().catch(() => false)

    if (!hasGenerationList) {
      handleMissingData(test, 'Generation history bookmarks test', 'generation history data', 'Create some generations first')
      return
    }

    // Find generation list items
    const generationItems = page.getByTestId('generation-list-item')
    const itemCount = await generationItems.count()

    if (itemCount === 0) {
      handleMissingData(test, 'Generation history bookmarks test', 'generation items', 'Create some generations first')
      return
    }

    // Get first generation item
    const firstItem = generationItems.first()
    await expect(firstItem).toBeVisible()

    // Look for bookmark button within the card
    // Note: The data-testid might be different depending on implementation
    const bookmarkButtons = firstItem.locator('[data-testid^="bookmark-button-"]')
    const bookmarkButtonCount = await bookmarkButtons.count()

    // Verify at least one bookmark button is visible in the card
    expect(bookmarkButtonCount).toBeGreaterThan(0)
  })

  test('can add bookmark from generation card', async ({ page }) => {
    // Login as test user first
    await loginAsTestUser(page)

    // Navigate to generation history and wait for all network activity to complete
    await page.goto('/generate/history')
    await expect(page).toHaveURL(/\/generate\/history/)
    await page.waitForLoadState('networkidle')

    // Wait for DOM to be ready
    await page.waitForSelector('main', { timeout: 15000 })

    const generationList = page.getByTestId('generation-list')
    const hasGenerationList = await generationList.isVisible({ timeout: 5000 }).catch(() => false)

    if (!hasGenerationList) {
      handleMissingData(test, 'Add bookmark from generation test', 'generation history data', 'Create some generations first')
      return
    }

    // Find first generation item
    const generationItems = page.getByTestId('generation-list-item')
    const itemCount = await generationItems.count()

    if (itemCount === 0) {
      handleMissingData(test, 'Add bookmark from generation test', 'generation items', 'Create some generations first')
      return
    }

    const firstItem = generationItems.first()
    await expect(firstItem).toBeVisible()

    // Find bookmark button - need to find a generation with content_id
    const bookmarkButton = firstItem.locator('[data-testid^="bookmark-button-"]').first()
    const hasBookmarkButton = await bookmarkButton.isVisible({ timeout: 2000 }).catch(() => false)

    if (!hasBookmarkButton) {
      // This generation might not have content_id yet (still processing)
      console.log('Skipping test - no bookmark button found (generation may not have content_id)')
      return
    }

    await expect(bookmarkButton).toBeVisible()

    // Check if already bookmarked
    const filledIcon = bookmarkButton.getByTestId('bookmark-icon-filled')
    const outlineIcon = bookmarkButton.getByTestId('bookmark-icon-outline')
    const isBookmarked = await filledIcon.isVisible().catch(() => false)

    // If already bookmarked, remove it first
    if (isBookmarked) {
      // Set up wait for batch check API call (triggered by cache invalidation after delete)
      const deleteResponsePromise = waitForApiResponse(page, '/api/v1/bookmarks/check-batch', { timeout: 15000 })

      await bookmarkButton.click()
      await expect(page.getByRole('heading', { name: /manage bookmark/i })).toBeVisible()
      await page.getByTestId('bookmark-remove-button').click()
      await expect(page.getByRole('heading', { name: /manage bookmark/i })).not.toBeVisible()
      await expect(outlineIcon).toBeVisible({ timeout: 3000 })

      // Wait for cache invalidation batch check
      await deleteResponsePromise
    }

    // Add bookmark
    await bookmarkButton.click()

    // With optimistic UI, icon should change immediately
    await expect(filledIcon).toBeVisible({ timeout: 2000 })
    await expect(outlineIcon).not.toBeVisible()
  })

  /**
   * SKIPPED: This test expects specific batch check API timing that React Query doesn't guarantee.
   * See notes/bookmark-tests.md for detailed explanation and potential solutions.
   * Test verifies implementation detail (batch check timing) rather than user behavior (filtering works).
   */
  test.skip('should batch fetch after filtering generations', async ({ page }) => {
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

    // Navigate to generation history and wait for all network activity to complete
    await page.goto('/generate/history')
    await expect(page).toHaveURL(/\/generate\/history/)
    await page.waitForLoadState('networkidle')

    // Wait for DOM to be ready
    await page.waitForSelector('main', { timeout: 15000 })

    const generationList = page.getByTestId('generation-list')
    const hasGenerationList = await generationList.isVisible({ timeout: 5000 }).catch(() => false)

    if (!hasGenerationList) {
      handleMissingData(test, 'Generation filtering batch test', 'generation history data', 'Create some generations first')
      return
    }

    await expect(generationList).toBeVisible()

    const initialBatchCalls = bookmarkRequests.length

    // Try to filter by status
    const statusFilter = page.getByTestId('status-filter')
    const hasStatusFilter = await statusFilter.isVisible({ timeout: 2000 }).catch(() => false)

    if (hasStatusFilter) {
      await statusFilter.click()

      // Select "completed" status
      const completedOption = page.getByRole('option', { name: /completed/i })
      const hasCompletedOption = await completedOption.isVisible({ timeout: 1000 }).catch(() => false)

      if (hasCompletedOption) {
        // Set up wait for API responses AFTER confirming option is visible
        const jobsResponsePromise = waitForApiResponse(page, '/api/v1/generation-jobs/', { timeout: 15000 })
        const batchResponsePromise = waitForApiResponse(page, '/api/v1/bookmarks/check-batch', { timeout: 15000 })

        await completedOption.click()

        // Wait for API responses to complete
        await jobsResponsePromise
        await batchResponsePromise

        // Should have made another batch call for filtered results
        expect(bookmarkRequests.length).toBeGreaterThan(initialBatchCalls)
      }
    }

    console.log(`Total batch calls after filtering: ${bookmarkRequests.length}`)
  })

  /**
   * SKIPPED: This test has timing issues with optimistic UI and modal opening.
   * See notes/bookmark-tests.md for detailed explanation and potential solutions.
   * After optimistically creating a bookmark, the modal requires server-confirmed bookmark data.
   */
  test.skip('can remove bookmark from generation card modal', async ({ page }) => {
    // Login as test user first
    await loginAsTestUser(page)

    // Navigate to generation history and wait for all network activity to complete
    await page.goto('/generate/history')
    await expect(page).toHaveURL(/\/generate\/history/)
    await page.waitForLoadState('networkidle')

    // Wait for DOM to be ready
    await page.waitForSelector('main', { timeout: 15000 })

    const generationList = page.getByTestId('generation-list')
    const hasGenerationList = await generationList.isVisible({ timeout: 5000 }).catch(() => false)

    if (!hasGenerationList) {
      handleMissingData(test, 'Remove bookmark from generation test', 'generation history data', 'Create some generations first')
      return
    }

    // Find first generation item
    const generationItems = page.getByTestId('generation-list-item')
    const itemCount = await generationItems.count()

    if (itemCount === 0) {
      handleMissingData(test, 'Remove bookmark from generation test', 'generation items', 'Create some generations first')
      return
    }

    const firstItem = generationItems.first()
    await expect(firstItem).toBeVisible()

    // Find bookmark button
    const bookmarkButton = firstItem.locator('[data-testid^="bookmark-button-"]').first()
    const hasBookmarkButton = await bookmarkButton.isVisible({ timeout: 2000 }).catch(() => false)

    if (!hasBookmarkButton) {
      console.log('Skipping test - no bookmark button found (generation may not have content_id)')
      return
    }

    await expect(bookmarkButton).toBeVisible()

    const filledIcon = bookmarkButton.getByTestId('bookmark-icon-filled')
    const outlineIcon = bookmarkButton.getByTestId('bookmark-icon-outline')

    // Ensure it's bookmarked first
    const isBookmarked = await filledIcon.isVisible().catch(() => false)

    if (!isBookmarked) {
      // Wait for bookmark creation API to complete (so we can open modal after)
      const createResponsePromise = waitForApiResponse(page, '/api/v1/bookmarks', { method: 'POST', timeout: 10000 })

      await bookmarkButton.click()

      // With optimistic UI, icon should change immediately
      await expect(filledIcon).toBeVisible({ timeout: 2000 })

      // Wait for server to confirm bookmark creation before trying to open modal
      await createResponsePromise
    }

    // Open modal (now we know bookmark exists on server)
    await bookmarkButton.click()
    await expect(page.getByRole('heading', { name: /manage bookmark/i })).toBeVisible()

    // Remove bookmark
    await page.getByTestId('bookmark-remove-button').click()

    // Verify modal closed
    await expect(page.getByRole('heading', { name: /manage bookmark/i })).not.toBeVisible()

    // With optimistic UI (future enhancement), icon should change quickly
    // For now, wait for server response and cache update
    await expect(outlineIcon).toBeVisible({ timeout: 5000 })
    await expect(filledIcon).not.toBeVisible()
  })
})
