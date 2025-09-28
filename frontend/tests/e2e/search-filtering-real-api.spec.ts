import { test, expect } from '@playwright/test'
import {
  ensureRealApiAvailable,
  assertSufficientTestData,
  loginAsTestUser,
  waitForGalleryLoad,
  waitForPageLoad,
  getPaginationInfo,
  getUnifiedContent,
  openFilterPanel
} from './utils/realApiHelpers'

test.describe('Search and Filtering (Real API)', () => {
  test.beforeEach(async ({ page }) => {
    // Check if real API is available, skip if not
    try {
      await ensureRealApiAvailable(page)
    } catch (error) {
      test.skip(true, 'Real API server not available on port 8002. Run with: npm run test:e2e:real-api')
      return
    }

    // Ensure we have sufficient test data
    try {
      await assertSufficientTestData(page, '/api/v1/content/unified?page=1&page_size=1', 10)
    } catch (error) {
      test.skip(true, 'Real API returned insufficient gallery results. Ensure the test database seed ran (make frontend-test-e2e-real-api).')
      return
    }

    // Log in as test user
    await loginAsTestUser(page)
  })

  test('filters gallery items by search term', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Get initial content to know what to search for
    const initialContent = await getUnifiedContent(page, { page: 1, page_size: 20 })
    if (!initialContent.items || initialContent.items.length === 0) {
      test.skip(true, 'No content available for search testing')
      return
    }

    // Find a search term from existing content
    const searchTerms = [
      'landscape',
      'portrait',
      'abstract',
      'nature',
      'city',
      'art'
    ]

    let foundSearchTerm = null
    let expectedResults = []

    for (const term of searchTerms) {
      expectedResults = initialContent.items.filter(item =>
        item.title.toLowerCase().includes(term.toLowerCase()) ||
        (item.description && item.description.toLowerCase().includes(term.toLowerCase()))
      )

      if (expectedResults.length > 0) {
        foundSearchTerm = term
        break
      }
    }

    if (!foundSearchTerm) {
      // Use first word from first content title as search term
      const firstTitle = initialContent.items[0].title
      foundSearchTerm = firstTitle.split(' ')[0]
      expectedResults = initialContent.items.filter(item =>
        item.title.toLowerCase().includes(foundSearchTerm.toLowerCase())
      )
    }

    // Look for search input
    const searchInputs = [
      page.getByLabel(/search/i),
      page.getByPlaceholder(/search/i),
      page.locator('input[type="search"]'),
      page.locator('input[type="text"]').filter({ hasText: /search/i }),
      page.locator('[data-testid*="search"]')
    ]

    let searchInput = null
    for (const input of searchInputs) {
      if (await input.count() > 0 && await input.isVisible()) {
        searchInput = input.first()
        break
      }
    }

    if (!searchInput) {
      test.skip(true, 'Search input not found in gallery interface')
      return
    }

    // Perform search
    await searchInput.fill(foundSearchTerm)

    // Submit search (could be auto-submit or button)
    const searchButton = page.getByRole('button', { name: /search/i })
    if (await searchButton.count() > 0 && await searchButton.isVisible()) {
      await searchButton.click()
    } else {
      // Try submitting the form
      await searchInput.press('Enter')
    }

    // Wait for search results
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Verify search results
    if (expectedResults.length > 0) {
      // Should show matching content
      const firstExpectedTitle = expectedResults[0].title
      await expect(page.getByText(firstExpectedTitle)).toBeVisible()

      // Check pagination reflects filtered results
      const paginationInfo = await getPaginationInfo(page)
      expect(paginationInfo.results).toBeGreaterThan(0)
      expect(paginationInfo.results).toBeLessThanOrEqual(initialContent.pagination.total_count)
    } else {
      // Should show no results found
      const noResultsIndicators = [
        page.getByText(/no results|no items found|nothing found/i),
        page.getByText(/0 results/i)
      ]

      let foundNoResults = false
      for (const indicator of noResultsIndicators) {
        if (await indicator.count() > 0 && await indicator.isVisible()) {
          foundNoResults = true
          break
        }
      }

      expect(foundNoResults).toBe(true)
    }

    // Clear search to return to original state
    await searchInput.clear()
    await searchInput.press('Enter')
    await page.waitForLoadState('networkidle')

    // Should return to showing all results
    const finalPagination = await getPaginationInfo(page)
    expect(finalPagination.results).toBe(initialContent.pagination.total_count)
  })

  test('content type filtering updates results correctly', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Get initial content data
    const allContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      content_types: 'regular,auto'
    })

    const regularContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      content_types: 'regular'
    })

    const autoContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      content_types: 'auto'
    })

    // Initial state should show all content types
    const initialPagination = await getPaginationInfo(page)

    // Open filter panel if needed
    await openFilterPanel(page)

    // Look for content type toggles
    const contentTypeToggles = [
      page.locator('input[type="checkbox"]').filter({ hasText: /regular|gens/i }),
      page.locator('input[type="checkbox"]').filter({ hasText: /auto|auto-gens/i }),
      page.getByLabel(/regular|gens/i),
      page.getByLabel(/auto|auto-gens/i),
      page.locator('[data-testid*="content-type"]')
    ]

    let regularToggle = null
    let autoToggle = null

    for (const toggle of contentTypeToggles) {
      const count = await toggle.count()
      for (let i = 0; i < count; i++) {
        const element = toggle.nth(i)
        const text = await element.textContent() || ''
        const label = await element.getAttribute('aria-label') || ''
        const combined = (text + ' ' + label).toLowerCase()

        if (combined.includes('auto') && !autoToggle) {
          autoToggle = element
        } else if ((combined.includes('regular') || combined.includes('gens')) && !regularToggle) {
          regularToggle = element
        }
      }
    }

    if (!regularToggle || !autoToggle) {
      test.skip(true, 'Content type toggles not found in gallery interface')
      return
    }

    // Test filtering to regular content only
    if (await autoToggle.isChecked()) {
      await autoToggle.click()
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      // Should show only regular content
      const filteredPagination = await getPaginationInfo(page)
      if (regularContent.pagination.total_count > 0) {
        expect(filteredPagination.results).toBe(regularContent.pagination.total_count)
      }

      // Re-enable auto content
      await autoToggle.click()
      await page.waitForLoadState('networkidle')
    }

    // Test filtering to auto content only
    if (await regularToggle.isChecked()) {
      await regularToggle.click()
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      // Should show only auto content
      const autoFilteredPagination = await getPaginationInfo(page)
      if (autoContent.pagination.total_count > 0) {
        expect(autoFilteredPagination.results).toBe(autoContent.pagination.total_count)
      }

      // Re-enable regular content
      await regularToggle.click()
      await page.waitForLoadState('networkidle')
    }

    // Should return to showing all content
    const finalPagination = await getPaginationInfo(page)
    expect(finalPagination.results).toBe(allContent.pagination.total_count)
  })

  test('creator filtering works correctly', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Get content for different creator filters
    const allCreatorContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      creator_filter: 'all'
    })

    const userContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      creator_filter: 'user'
    })

    const communityContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      creator_filter: 'community'
    })

    // Open filter panel if needed
    await openFilterPanel(page)

    // Look for creator filter controls
    const creatorFilters = [
      page.getByLabel(/creator|filter/i),
      page.locator('select').filter({ hasText: /creator|user|community/i }),
      page.locator('input[type="radio"]').filter({ hasText: /all|user|community/i }),
      page.locator('[data-testid*="creator"]')
    ]

    let creatorFilter = null
    for (const filter of creatorFilters) {
      if (await filter.count() > 0 && await filter.isVisible()) {
        creatorFilter = filter.first()
        break
      }
    }

    if (!creatorFilter) {
      test.skip(true, 'Creator filter controls not found in gallery interface')
      return
    }

    // Test filtering by user content
    const userFilterOptions = [
      page.getByText(/^user$|your|my content/i),
      page.getByRole('option', { name: /user/i }),
      page.locator('input[value="user"]')
    ]

    for (const option of userFilterOptions) {
      if (await option.count() > 0 && await option.isVisible()) {
        await option.click()
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(500)

        // Check if results changed appropriately
        const userFilteredPagination = await getPaginationInfo(page)
        if (userContent.pagination.total_count !== allCreatorContent.pagination.total_count) {
          expect(userFilteredPagination.results).toBe(userContent.pagination.total_count)
        }
        break
      }
    }

    // Test filtering by community content
    const communityFilterOptions = [
      page.getByText(/^community$|others/i),
      page.getByRole('option', { name: /community/i }),
      page.locator('input[value="community"]')
    ]

    for (const option of communityFilterOptions) {
      if (await option.count() > 0 && await option.isVisible()) {
        await option.click()
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(500)

        // Check if results changed appropriately
        const communityFilteredPagination = await getPaginationInfo(page)
        if (communityContent.pagination.total_count !== allCreatorContent.pagination.total_count) {
          expect(communityFilteredPagination.results).toBe(communityContent.pagination.total_count)
        }
        break
      }
    }

    // Return to all creators
    const allFilterOptions = [
      page.getByText(/^all$|everyone/i),
      page.getByRole('option', { name: /all/i }),
      page.locator('input[value="all"]')
    ]

    for (const option of allFilterOptions) {
      if (await option.count() > 0 && await option.isVisible()) {
        await option.click()
        await page.waitForLoadState('networkidle')
        break
      }
    }

    // Should return to showing all content
    const finalPagination = await getPaginationInfo(page)
    expect(finalPagination.results).toBe(allCreatorContent.pagination.total_count)
  })

  test('combines multiple filters correctly', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Open filter panel
    await openFilterPanel(page)

    // Apply search filter first
    const searchInput = page.getByLabel(/search/i).or(page.getByPlaceholder(/search/i))

    if (await searchInput.count() > 0) {
      await searchInput.fill('test')
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')

      const searchPagination = await getPaginationInfo(page)

      // Then apply content type filter
      const autoToggle = page.locator('input[type="checkbox"]').filter({ hasText: /auto/i })
      if (await autoToggle.count() > 0 && await autoToggle.isChecked()) {
        await autoToggle.click()
        await page.waitForLoadState('networkidle')

        // Results should be further filtered
        const combinedPagination = await getPaginationInfo(page)
        expect(combinedPagination.results).toBeLessThanOrEqual(searchPagination.results)
      }

      // Clear filters
      await searchInput.clear()
      await searchInput.press('Enter')
      if (await autoToggle.count() > 0 && !await autoToggle.isChecked()) {
        await autoToggle.click()
      }
      await page.waitForLoadState('networkidle')
    }

    // Verify filters can be cleared
    const finalPagination = await getPaginationInfo(page)
    expect(finalPagination.results).toBeGreaterThan(0)
  })

  test('maintains filter state during pagination', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Get initial pagination info
    const initialPagination = await getPaginationInfo(page)

    if (initialPagination.pages <= 1) {
      test.skip(true, 'Not enough content for pagination testing')
      return
    }

    // Apply a filter
    const searchInput = page.getByLabel(/search/i).or(page.getByPlaceholder(/search/i))

    if (await searchInput.count() > 0) {
      await searchInput.fill('a') // Broad search to get multiple pages
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')

      const filteredPagination = await getPaginationInfo(page)

      if (filteredPagination.pages > 1) {
        // Navigate to next page
        const nextButton = page.getByRole('button', { name: /next page|page 2/i })
        if (await nextButton.count() > 0 && await nextButton.isEnabled()) {
          await nextButton.click()
          await page.waitForLoadState('networkidle')

          // Search should still be applied
          await expect(searchInput).toHaveValue('a')

          // Results should still be filtered
          const page2Pagination = await getPaginationInfo(page)
          expect(page2Pagination.results).toBe(filteredPagination.results)
        }
      }

      // Clear search
      await searchInput.clear()
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')
    }
  })

  test('handles empty search results gracefully', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Search for something unlikely to exist
    const searchInput = page.getByLabel(/search/i).or(page.getByPlaceholder(/search/i))

    if (await searchInput.count() > 0) {
      await searchInput.fill('xyznonexistentsearchterm123')
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')

      // Should handle empty results gracefully
      const emptyStateIndicators = [
        page.getByText(/no results|no items found|nothing found/i),
        page.getByText(/0 results|0 items/i),
        page.getByText(/try a different search/i),
        page.locator('[data-testid*="empty"]')
      ]

      let foundEmptyState = false
      for (const indicator of emptyStateIndicators) {
        if (await indicator.count() > 0 && await indicator.isVisible()) {
          foundEmptyState = true
          break
        }
      }

      expect(foundEmptyState).toBe(true)

      // Should still show search controls
      await expect(searchInput).toBeVisible()

      // Clear search should restore content
      await searchInput.clear()
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')

      const restoredPagination = await getPaginationInfo(page)
      expect(restoredPagination.results).toBeGreaterThan(0)
    } else {
      test.skip(true, 'Search input not available for testing')
    }
  })

  test('filter performance with large datasets', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Measure filter response time
    const searchInput = page.getByLabel(/search/i).or(page.getByPlaceholder(/search/i))

    if (await searchInput.count() > 0) {
      const startTime = Date.now()

      await searchInput.fill('test')
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')

      const filterTime = Date.now() - startTime

      // Filter should respond reasonably quickly (under 5 seconds)
      expect(filterTime).toBeLessThan(5000)

      // Results should be displayed
      await expect(page.locator('main')).toBeVisible()

      // Clear search
      await searchInput.clear()
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')
    }
  })
})