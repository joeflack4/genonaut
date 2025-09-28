import { test, expect } from '@playwright/test'
import {
  ensureRealApiAvailable,
  assertSufficientTestData,
  loginAsTestUser,
  waitForPageLoad,
  getDashboardStats,
  getUnifiedContent,
  getPaginationInfo,
  waitForGalleryLoad
} from './utils/realApiHelpers'

test.describe('Statistics and Counting (Real API)', () => {
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

  test('dashboard and gallery totals match exactly', async ({ page }) => {
    // Get statistics from API
    const dashboardStats = await getDashboardStats(page)
    const galleryData = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      content_types: 'regular,auto',
      creator_filter: 'all'
    })

    // Navigate to dashboard first
    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Extract dashboard numbers
    const dashboardNumbers = {
      userRegular: dashboardStats.user_regular_count,
      userAuto: dashboardStats.user_auto_count,
      communityRegular: dashboardStats.community_regular_count,
      communityAuto: dashboardStats.community_auto_count
    }

    // Verify dashboard displays these numbers correctly
    for (const [key, value] of Object.entries(dashboardNumbers)) {
      if (value > 0) {
        const formattedValue = value.toLocaleString()
        const dashboardDisplay = page.getByText(formattedValue)

        if (await dashboardDisplay.count() > 0) {
          await expect(dashboardDisplay).toBeVisible()
        } else {
          // Try without formatting for smaller numbers
          const unformattedDisplay = page.getByText(value.toString())
          if (await unformattedDisplay.count() > 0) {
            await expect(unformattedDisplay).toBeVisible()
          }
        }
      }
    }

    // Navigate to gallery
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Get gallery pagination info
    const galleryPagination = await getPaginationInfo(page)

    // Verify gallery total matches API data
    expect(galleryPagination.results).toBe(galleryData.pagination.total_count)

    // Calculate expected total from dashboard stats
    const expectedTotal = dashboardNumbers.userRegular +
                         dashboardNumbers.userAuto +
                         dashboardNumbers.communityRegular +
                         dashboardNumbers.communityAuto

    // Gallery total should match sum of dashboard components
    expect(galleryPagination.results).toBe(expectedTotal)

    // Verify gallery displays the same total
    const galleryTotalDisplay = page.getByText(galleryPagination.results.toLocaleString())
    await expect(galleryTotalDisplay).toBeVisible()
  })

  test('content type breakdown statistics are accurate', async ({ page }) => {
    // Get content breakdowns from API
    const allContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      content_types: 'regular,auto'
    })

    const regularOnlyContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      content_types: 'regular'
    })

    const autoOnlyContent = await getUnifiedContent(page, {
      page: 1,
      page_size: 10,
      content_types: 'auto'
    })

    // Verify the sum matches
    expect(allContent.pagination.total_count).toBe(
      regularOnlyContent.pagination.total_count + autoOnlyContent.pagination.total_count
    )

    // Navigate to gallery and test filtering
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Initial state should show all content
    const initialPagination = await getPaginationInfo(page)
    expect(initialPagination.results).toBe(allContent.pagination.total_count)

    // Get statistics from the gallery stats (if displayed)
    const stats = allContent.stats || {}

    if (stats.user_regular_count !== undefined) {
      expect(stats.user_regular_count + stats.community_regular_count).toBe(
        regularOnlyContent.pagination.total_count
      )
    }

    if (stats.user_auto_count !== undefined) {
      expect(stats.user_auto_count + stats.community_auto_count).toBe(
        autoOnlyContent.pagination.total_count
      )
    }

    // Look for filter panel to test content type filtering
    const filterButton = page.getByRole('button', { name: /filter|options/i })
    if (await filterButton.count() > 0) {
      await filterButton.click()
      await page.waitForTimeout(500)
    }

    // Test regular content filter
    const regularToggle = page.locator('input[type="checkbox"]').filter({ hasText: /regular/i })
    const autoToggle = page.locator('input[type="checkbox"]').filter({ hasText: /auto/i })

    if (await autoToggle.count() > 0 && await autoToggle.isChecked()) {
      await autoToggle.click()
      await page.waitForLoadState('networkidle')

      const regularFilteredPagination = await getPaginationInfo(page)
      expect(regularFilteredPagination.results).toBe(regularOnlyContent.pagination.total_count)

      // Re-enable auto content
      await autoToggle.click()
      await page.waitForLoadState('networkidle')
    }

    // Test auto content filter
    if (await regularToggle.count() > 0 && await regularToggle.isChecked()) {
      await regularToggle.click()
      await page.waitForLoadState('networkidle')

      const autoFilteredPagination = await getPaginationInfo(page)
      expect(autoFilteredPagination.results).toBe(autoOnlyContent.pagination.total_count)

      // Re-enable regular content
      await regularToggle.click()
      await page.waitForLoadState('networkidle')
    }

    // Final state should return to all content
    const finalPagination = await getPaginationInfo(page)
    expect(finalPagination.results).toBe(allContent.pagination.total_count)
  })

  test('user vs community content statistics are correct', async ({ page }) => {
    // Get creator-based breakdowns from API
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

    // Verify the sum matches
    expect(allCreatorContent.pagination.total_count).toBe(
      userContent.pagination.total_count + communityContent.pagination.total_count
    )

    // Check dashboard statistics
    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    const dashboardStats = await getDashboardStats(page)

    // User total should match
    const expectedUserTotal = dashboardStats.user_regular_count + dashboardStats.user_auto_count
    expect(userContent.pagination.total_count).toBe(expectedUserTotal)

    // Community total should match
    const expectedCommunityTotal = dashboardStats.community_regular_count + dashboardStats.community_auto_count
    expect(communityContent.pagination.total_count).toBe(expectedCommunityTotal)

    // Verify dashboard displays these correctly
    if (dashboardStats.user_regular_count > 0) {
      const userRegularDisplay = page.getByText(dashboardStats.user_regular_count.toString())
      if (await userRegularDisplay.count() > 0) {
        await expect(userRegularDisplay).toBeVisible()
      }
    }

    if (dashboardStats.community_regular_count > 999) {
      const formattedCommunityRegular = dashboardStats.community_regular_count.toLocaleString()
      const communityDisplay = page.getByText(formattedCommunityRegular)
      if (await communityDisplay.count() > 0) {
        await expect(communityDisplay).toBeVisible()
      }
    }

    // Test creator filtering in gallery
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Open filter panel if available
    const filterButton = page.getByRole('button', { name: /filter|options/i })
    if (await filterButton.count() > 0) {
      await filterButton.click()
      await page.waitForTimeout(500)
    }

    // Test user filter
    const userFilterOption = page.getByText(/^user$|your content/i).or(
      page.locator('input[value="user"]')
    )

    if (await userFilterOption.count() > 0) {
      await userFilterOption.click()
      await page.waitForLoadState('networkidle')

      const userFilteredPagination = await getPaginationInfo(page)
      expect(userFilteredPagination.results).toBe(userContent.pagination.total_count)

      // Return to all
      const allFilterOption = page.getByText(/^all$|everyone/i).or(
        page.locator('input[value="all"]')
      )
      if (await allFilterOption.count() > 0) {
        await allFilterOption.click()
        await page.waitForLoadState('networkidle')
      }
    }

    // Test community filter
    const communityFilterOption = page.getByText(/^community$/i).or(
      page.locator('input[value="community"]')
    )

    if (await communityFilterOption.count() > 0) {
      await communityFilterOption.click()
      await page.waitForLoadState('networkidle')

      const communityFilteredPagination = await getPaginationInfo(page)
      expect(communityFilteredPagination.results).toBe(communityContent.pagination.total_count)
    }
  })

  test('pagination calculations are mathematically correct', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    const paginationInfo = await getPaginationInfo(page)
    const pageSize = 10 // Default page size

    // Calculate expected pages
    const expectedPages = Math.ceil(paginationInfo.results / pageSize)
    expect(paginationInfo.pages).toBe(expectedPages)

    // Verify pagination math
    expect(paginationInfo.results).toBeGreaterThan(0)
    expect(paginationInfo.pages).toBeGreaterThan(0)

    // If there are multiple pages, test page navigation
    if (paginationInfo.pages > 1) {
      // Navigate to second page
      const page2Button = page.getByRole('button', { name: /page 2|go to page 2/i })
      if (await page2Button.count() > 0) {
        await page2Button.click()
        await page.waitForLoadState('networkidle')

        // Pagination info should remain consistent
        const page2Pagination = await getPaginationInfo(page)
        expect(page2Pagination.results).toBe(paginationInfo.results)
        expect(page2Pagination.pages).toBe(paginationInfo.pages)

        // Navigate to last page if it exists
        if (paginationInfo.pages > 2) {
          const lastPageButton = page.getByRole('button', { name: new RegExp(`page ${paginationInfo.pages}`, 'i') })
          if (await lastPageButton.count() > 0) {
            await lastPageButton.click()
            await page.waitForLoadState('networkidle')

            const lastPagePagination = await getPaginationInfo(page)
            expect(lastPagePagination.results).toBe(paginationInfo.results)
            expect(lastPagePagination.pages).toBe(paginationInfo.pages)
          }
        }

        // Return to first page
        const page1Button = page.getByRole('button', { name: /page 1|go to page 1/i })
        if (await page1Button.count() > 0) {
          await page1Button.click()
          await page.waitForLoadState('networkidle')
        }
      }
    }
  })

  test('real-time statistics updates correctly', async ({ page }) => {
    // Get initial statistics
    const initialStats = await getDashboardStats(page)
    const initialGalleryData = await getUnifiedContent(page, { page: 1, page_size: 1 })

    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Capture initial displayed values
    const initialDisplayedValues = []
    for (const statValue of Object.values(initialStats)) {
      if (typeof statValue === 'number' && statValue > 0) {
        const display = page.getByText(statValue.toLocaleString())
        if (await display.count() > 0) {
          initialDisplayedValues.push(statValue)
        }
      }
    }

    // Refresh the page
    await page.reload()
    await waitForPageLoad(page, 'dashboard')

    // Statistics should remain consistent after refresh
    const refreshedStats = await getDashboardStats(page)
    expect(refreshedStats.user_regular_count).toBe(initialStats.user_regular_count)
    expect(refreshedStats.user_auto_count).toBe(initialStats.user_auto_count)
    expect(refreshedStats.community_regular_count).toBe(initialStats.community_regular_count)
    expect(refreshedStats.community_auto_count).toBe(initialStats.community_auto_count)

    // Navigate to gallery and check consistency
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    const refreshedGalleryData = await getUnifiedContent(page, { page: 1, page_size: 1 })
    expect(refreshedGalleryData.pagination.total_count).toBe(initialGalleryData.pagination.total_count)

    // Display should still show the same values
    const refreshedPagination = await getPaginationInfo(page)
    expect(refreshedPagination.results).toBe(initialGalleryData.pagination.total_count)
  })

  test('statistics handle edge cases correctly', async ({ page }) => {
    // Test with various filter combinations to ensure statistics remain consistent

    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Test empty search results
    const searchInput = page.getByLabel(/search/i).or(page.getByPlaceholder(/search/i))
    if (await searchInput.count() > 0) {
      await searchInput.fill('nonexistentsearchterm12345')
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')

      // Should show 0 results gracefully
      const emptyPagination = await getPaginationInfo(page).catch(() => null)
      if (emptyPagination) {
        expect(emptyPagination.results).toBe(0)
        expect(emptyPagination.pages).toBe(0)
      } else {
        // Should show "no results" message
        const noResults = page.getByText(/no results|0 results/i)
        await expect(noResults).toBeVisible()
      }

      // Clear search
      await searchInput.clear()
      await searchInput.press('Enter')
      await page.waitForLoadState('networkidle')
    }

    // Test with all filters disabled (if possible)
    const filterButton = page.getByRole('button', { name: /filter|options/i })
    if (await filterButton.count() > 0) {
      await filterButton.click()
      await page.waitForTimeout(500)

      // Try to disable all content type filters
      const toggles = page.locator('input[type="checkbox"]')
      const toggleCount = await toggles.count()

      for (let i = 0; i < toggleCount; i++) {
        const toggle = toggles.nth(i)
        if (await toggle.isChecked()) {
          await toggle.click()
          await page.waitForTimeout(200)
        }
      }

      await page.waitForLoadState('networkidle')

      // Should either show 0 results or prevent disabling all filters
      const finalPagination = await getPaginationInfo(page).catch(() => null)
      if (finalPagination) {
        expect(finalPagination.results).toBeGreaterThanOrEqual(0)
      }

      // Re-enable filters
      for (let i = 0; i < toggleCount; i++) {
        const toggle = toggles.nth(i)
        if (!await toggle.isChecked()) {
          await toggle.click()
          await page.waitForTimeout(200)
        }
      }

      await page.waitForLoadState('networkidle')
    }

    // Final verification that statistics are still coherent
    const finalPagination = await getPaginationInfo(page)
    expect(finalPagination.results).toBeGreaterThan(0)
    expect(finalPagination.pages).toBeGreaterThan(0)
  })

  test('large number formatting is consistent', async ({ page }) => {
    const stats = await getDashboardStats(page)

    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Test large number formatting (community content likely has large numbers)
    const largeNumbers = [
      stats.community_regular_count,
      stats.community_auto_count
    ].filter(num => num > 999)

    for (const num of largeNumbers) {
      const formatted = num.toLocaleString()
      const display = page.getByText(formatted)

      if (await display.count() > 0) {
        await expect(display).toBeVisible()

        // Verify the number contains commas for thousands
        expect(formatted).toMatch(/\d{1,3}(,\d{3})*/)
      }
    }

    // Navigate to gallery and check large number formatting there
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    const pagination = await getPaginationInfo(page)
    if (pagination.results > 999) {
      const formattedResults = pagination.results.toLocaleString()
      const galleryDisplay = page.getByText(formattedResults)
      await expect(galleryDisplay).toBeVisible()
    }

    if (pagination.pages > 999) {
      const formattedPages = pagination.pages.toLocaleString()
      const pageDisplay = page.getByText(formattedPages)
      await expect(pageDisplay).toBeVisible()
    }
  })
})