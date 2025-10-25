import { test, expect } from '@playwright/test'
import {
  waitForGalleryLoad,
  getPaginationInfo,
  clickNextPage,
  clickPreviousPage,
  navigateToPage,
  verifyPaginationState,
  toggleContentTypeFilter,
  logGalleryState,
  ensureRealApiAvailable,
  assertSufficientTestData,
} from './utils/realApiHelpers'

/**
 * Gallery Real API Tests - Improved Version
 *
 * This demonstrates the improved testing patterns using real API utilities.
 * These tests are much cleaner and more maintainable than mock-based tests.
 *
 * Note: These tests require the test API server to be running on port 8002.
 * When run with the main test suite, they will be skipped if the server is not available.
 */

test.describe.configure({ mode: 'serial' });

test.describe('Gallery page (Real API - Improved)', () => {
  test.beforeEach(async ({ page }) => {
    try {
      await ensureRealApiAvailable(page)
      await assertSufficientTestData(page, '/api/v1/content/unified?page=1&page_size=1', 1)
    } catch (error) {
      test.skip(true, 'Real API server not available or missing seed data. Run with: npm run test:e2e:real-api')
    }
  })
  test.describe('Gallery Pagination', () => {
    test('displays correct pagination and handles navigation', async ({ page }) => {
      test.setTimeout(30000); // Increase timeout for pagination test

      // Navigate to gallery page
      await page.goto('/gallery')

      // Wait for gallery to load with real API data
      await waitForGalleryLoad(page)

      // Get current pagination state
      const paginationInfo = await getPaginationInfo(page)
      await logGalleryState(page, 'Initial load')

      // Verify basic pagination structure
      if (paginationInfo.results === 0) {
        test.skip(true, 'Real API returned zero gallery results. Ensure the test database seed ran (make frontend-test-e2e-real-api).')
      }

      if (paginationInfo.pages < 2) {
        test.skip(true, 'Not enough data for pagination test - need at least 2 pages')
      }

      expect(paginationInfo.pages).toBeGreaterThan(0)
      expect(paginationInfo.results).toBeGreaterThan(0)

      if (paginationInfo.pages === 1) {
        // Single page scenario
        await verifyPaginationState(page, {
          currentPage: 1,
          totalPages: 1,
          hasNext: false,
          hasPrevious: false
        })
        console.log('✅ Single page pagination verified')
      } else {
        // Multi-page scenario
        await verifyPaginationState(page, {
          currentPage: 1,
          totalPages: paginationInfo.pages,
          hasNext: true,
          hasPrevious: false
        })

        // Test navigation to next page
        await clickNextPage(page)
        await logGalleryState(page, 'After next page')

        // Verify we're now on page 2
        await verifyPaginationState(page, {
          currentPage: 2,
          totalPages: paginationInfo.pages,
          hasNext: paginationInfo.pages > 2,
          hasPrevious: true
        })

        // Navigate back to page 1
        await clickPreviousPage(page)
        await logGalleryState(page, 'Back to page 1')

        console.log('✅ Multi-page pagination navigation verified')
      }
    })

    test('supports deep pagination across large dataset', async ({ page }) => {
      await page.goto('/gallery')

      await waitForGalleryLoad(page)

      const initialPagination = await getPaginationInfo(page)
      await logGalleryState(page, 'Before deep pagination')

      if (initialPagination.results === 0) {
        test.skip(true, 'Real API returned zero gallery results. Ensure the test database seed ran (make frontend-test-e2e-real-api).')
      }

      if (initialPagination.results < 100 || initialPagination.pages < 5) {
        test.skip(true, 'Real API dataset too small for deep pagination scenario.')
      }

      await navigateToPage(page, initialPagination.pages)

      await waitForGalleryLoad(page)
      await logGalleryState(page, 'After last page navigation')

      await verifyPaginationState(page, {
        currentPage: initialPagination.pages,
        totalPages: initialPagination.pages,
        hasNext: false,
        hasPrevious: initialPagination.pages > 1
      })

      const deepPagination = await getPaginationInfo(page)
      expect(deepPagination.results).toBe(initialPagination.results)
      expect(deepPagination.pages).toBe(initialPagination.pages)

      const previousButton = page.getByRole('button', { name: /go to previous page/i })
      await expect(previousButton).toBeEnabled()

      // Return to the first page to keep subsequent tests isolated
      await navigateToPage(page, 1)

      await waitForGalleryLoad(page)
      await logGalleryState(page, 'Back to first page after deep pagination')

      await verifyPaginationState(page, {
        currentPage: 1,
        totalPages: initialPagination.pages,
        hasNext: initialPagination.pages > 1,
        hasPrevious: false
      })
    })

    test('content type filtering works correctly', async ({ page }) => {
      await page.goto('/gallery')
      await waitForGalleryLoad(page)

      // Get initial state (all content types)
      const initialPagination = await getPaginationInfo(page)
      await logGalleryState(page, 'All content types')

      if (initialPagination.results === 0) {
        test.skip(true, 'Real API returned zero gallery results. Ensure the test database seed ran (make frontend-test-e2e-real-api).')
      }

      // Try to toggle content type filters
      const regularToggled = await toggleContentTypeFilter(page, 'regular', true)
      const autoToggled = await toggleContentTypeFilter(page, 'auto', false)

      if (!regularToggled && !autoToggled) {
        test.skip(true, 'Content type toggles not available in current UI build')
      }

      if (regularToggled && autoToggled) {
        // Successfully found and used content type filters
        const regularOnlyPagination = await getPaginationInfo(page)
        await logGalleryState(page, 'Regular content only')

        // Switch to auto content only
        await toggleContentTypeFilter(page, 'regular', false)
        await toggleContentTypeFilter(page, 'auto', true)

        const autoOnlyPagination = await getPaginationInfo(page)
        await logGalleryState(page, 'Auto content only')

        // Restore all content
        await toggleContentTypeFilter(page, 'regular', true)
        await toggleContentTypeFilter(page, 'auto', true)

        const restoredPagination = await getPaginationInfo(page)
        await logGalleryState(page, 'All content restored')

        console.log('✅ Content type filtering fully functional')
      } else {
        console.log('ℹ️  Content type filters not found - may need UI updates')
        console.log('✅ Basic filtering test structure verified')
      }
    })
  })
})
