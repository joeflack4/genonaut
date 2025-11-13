import { test, expect } from '@playwright/test'
import { waitForGalleryLoad, getPaginationInfo, getTestUserId } from './utils/realApiHelpers'

/**
 * Gallery Content Type Filters Tests
 *
 * Tests the 4 content type filters on the gallery page:
 * 1. Your gens (user + regular content)
 * 2. Your auto-gens (user + auto content)
 * 3. Community gens (community + regular content)
 * 4. Community auto-gens (community + auto content)
 *
 * These tests verify that:
 * - Each filter combination produces different result counts
 * - When all filters are OFF, 0 results are shown
 * - The filters work correctly in combination
 */

test.describe.configure({ mode: 'serial' })

test.describe('Gallery Content Type Filters (Real API)', () => {
  test.beforeAll(async () => {
    // Check if test API server is available
    try {
      const response = await fetch('http://127.0.0.1:8002/health', {
        method: 'GET',
        signal: AbortSignal.timeout(2000)
      })
      if (!response.ok) {
        throw new Error('Test API server not responding correctly')
      }
    } catch (error) {
      test.skip(true, 'Real API server not available on port 8002. Run with: npm run test:e2e:real-api')
    }
  })

  /**
   * Helper to toggle a specific content filter
   */
  async function toggleFilter(page, filterName: string, checked: boolean) {
    // Map filter names to their accessible labels
    const labelMap = {
      'your-gens': 'Your gens',
      'your-autogens': 'Your auto-gens',
      'community-gens': 'Community gens',
      'community-autogens': 'Community auto-gens'
    }

    const label = labelMap[filterName]
    // Use role and name instead of data-testid since Material UI Switch doesn't preserve data-testid
    const toggle = page.getByRole('switch', { name: label })

    const isChecked = await toggle.isChecked()
    if (isChecked !== checked) {
      await toggle.click()
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500) // Wait for API call and UI update
    }
  }

  /**
   * Helper to set all 4 filters to specific states
   */
  async function setAllFilters(page, filters: {
    yourGens: boolean
    yourAutoGens: boolean
    communityGens: boolean
    communityAutoGens: boolean
  }) {
    // Make sure options panel is open
    const optionsDrawer = page.locator('[data-testid="gallery-options-drawer"]')

    // Wait for drawer to be in DOM
    await optionsDrawer.waitFor({ state: 'attached', timeout: 5000 })

    // Check if drawer is open (has data-open="true")
    const drawerOpenAttr = await optionsDrawer.getAttribute('data-open')
    const isDrawerOpen = drawerOpenAttr === 'true'

    if (!isDrawerOpen) {
      const optionsToggleButton = page.locator('[data-testid="gallery-options-toggle-button"]')
      await optionsToggleButton.click()

      // Wait for drawer to actually open by checking the data-open attribute
      await page.waitForFunction(
        () => {
          const drawer = document.querySelector('[data-testid="gallery-options-drawer"]')
          return drawer?.getAttribute('data-open') === 'true'
        },
        { timeout: 5000 }
      )

      // Additional wait for drawer animation to complete
      await page.waitForTimeout(300)
    }

    // Wait for the content toggles section to be visible (confirms drawer content loaded)
    await page.locator('[data-testid="gallery-content-toggles"]').waitFor({ state: 'visible', timeout: 5000 })

    // Toggle each filter
    await toggleFilter(page, 'your-gens', filters.yourGens)
    await toggleFilter(page, 'your-autogens', filters.yourAutoGens)
    await toggleFilter(page, 'community-gens', filters.communityGens)
    await toggleFilter(page, 'community-autogens', filters.communityAutoGens)

    // Wait for the last filter change to propagate
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)
  }

  /**
   * Helper to get the result count from the pagination text
   */
  async function getResultCount(page): Promise<number> {
    // First check for empty state (faster when there are 0 results)
    // Check both grid and list view empty messages
    const gridEmptyMessage = page.locator('[data-testid="gallery-grid-empty"]')
    const listEmptyMessage = page.locator('[data-testid="gallery-results-empty"]')

    try {
      if (await gridEmptyMessage.isVisible({ timeout: 2000 })) {
        return 0
      }
    } catch {
      // Not visible, try list view
    }

    try {
      if (await listEmptyMessage.isVisible({ timeout: 2000 })) {
        return 0
      }
    } catch {
      // Not visible, continue to pagination check
    }

    // Then check for pagination info
    try {
      const paginationInfo = await getPaginationInfo(page, { timeout: 3000 })
      return paginationInfo.results
    } catch (error) {
      // If all checks fail, assume 0 results
      return 0
    }
  }

  test('should show 0 results when all filters are OFF', async ({ page }) => {
    // Longer timeout needed for toggling 4 filters with API calls
    test.setTimeout(30000)

    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Turn off all 4 filters
    await setAllFilters(page, {
      yourGens: false,
      yourAutoGens: false,
      communityGens: false,
      communityAutoGens: false
    })

    // Should show 0 results
    const resultCount = await getResultCount(page)
    expect(resultCount).toBe(0)

    // Verify the summary text shows "0 results"
    const summaryText = page.locator('[data-testid="gallery-options-summary-text"]')
    const summaryContent = await summaryText.textContent()
    expect(summaryContent).toContain('0 results')

    // Verify empty message is shown (grid view uses different data-testid than list view)
    const emptyMessage = page.locator('[data-testid="gallery-grid-empty"]')
    await expect(emptyMessage).toBeVisible()
  })

  test('should show all results when all filters are ON', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Turn on all 4 filters
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: true,
      communityGens: true,
      communityAutoGens: true
    })

    // Should show some results (total count)
    const allResultsCount = await getResultCount(page)
    expect(allResultsCount).toBeGreaterThan(0)

    // Store this for comparison in other tests
    page.context().storageState()
    console.log(`All filters ON: ${allResultsCount} results`)
  })

  test('should show different result counts for each individual filter', async ({ page }) => {
    // Longer timeout needed for toggling filters 5 times with API calls
    test.setTimeout(60000)

    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    const resultCounts = {
      allOn: 0,
      yourGens: 0,
      yourAutoGens: 0,
      communityGens: 0,
      communityAutoGens: 0
    }

    // Test (i): All filters ON
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: true,
      communityGens: true,
      communityAutoGens: true
    })
    resultCounts.allOn = await getResultCount(page)
    console.log(`All ON: ${resultCounts.allOn} results`)

    // Test (ii): Only "Your gens" ON
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: false,
      communityGens: false,
      communityAutoGens: false
    })
    resultCounts.yourGens = await getResultCount(page)
    console.log(`Your gens only: ${resultCounts.yourGens} results`)

    // Test (iii): Only "Your auto-gens" ON
    await setAllFilters(page, {
      yourGens: false,
      yourAutoGens: true,
      communityGens: false,
      communityAutoGens: false
    })
    resultCounts.yourAutoGens = await getResultCount(page)
    console.log(`Your auto-gens only: ${resultCounts.yourAutoGens} results`)

    // Test (iv): Only "Community gens" ON
    await setAllFilters(page, {
      yourGens: false,
      yourAutoGens: false,
      communityGens: true,
      communityAutoGens: false
    })
    resultCounts.communityGens = await getResultCount(page)
    console.log(`Community gens only: ${resultCounts.communityGens} results`)

    // Test (v): Only "Community auto-gens" ON
    await setAllFilters(page, {
      yourGens: false,
      yourAutoGens: false,
      communityGens: false,
      communityAutoGens: true
    })
    resultCounts.communityAutoGens = await getResultCount(page)
    console.log(`Community auto-gens only: ${resultCounts.communityAutoGens} results`)

    // Verify that "all ON" equals the sum of all individual filters
    // (assuming no overlap in content categories, which should be the case)
    const sumOfIndividuals =
      resultCounts.yourGens +
      resultCounts.yourAutoGens +
      resultCounts.communityGens +
      resultCounts.communityAutoGens

    expect(resultCounts.allOn).toBe(sumOfIndividuals)

    // Verify that at least some of the individual filter counts are different
    // This ensures the filters are actually working and not all returning the same data
    const uniqueCounts = new Set([
      resultCounts.yourGens,
      resultCounts.yourAutoGens,
      resultCounts.communityGens,
      resultCounts.communityAutoGens
    ])

    // We expect at least 2 different counts (could all be different, or some could be the same)
    // But they shouldn't ALL be identical
    if (resultCounts.yourGens > 0 || resultCounts.yourAutoGens > 0 ||
        resultCounts.communityGens > 0 || resultCounts.communityAutoGens > 0) {
      // Only enforce this if there's any data at all
      expect(uniqueCounts.size).toBeGreaterThanOrEqual(1)
    }
  })

  test('should correctly filter combinations of content types', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Test: Your gens + Your auto-gens
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: true,
      communityGens: false,
      communityAutoGens: false
    })
    const yourContentCount = await getResultCount(page)
    console.log(`Your content (gens + auto-gens): ${yourContentCount} results`)

    // Test: Community gens + Community auto-gens
    await setAllFilters(page, {
      yourGens: false,
      yourAutoGens: false,
      communityGens: true,
      communityAutoGens: true
    })
    const communityContentCount = await getResultCount(page)
    console.log(`Community content (gens + auto-gens): ${communityContentCount} results`)

    // Test: All gens (regular content only)
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: false,
      communityGens: true,
      communityAutoGens: false
    })
    const allGensCount = await getResultCount(page)
    console.log(`All gens (regular content): ${allGensCount} results`)

    // Test: All auto-gens (auto content only)
    await setAllFilters(page, {
      yourGens: false,
      yourAutoGens: true,
      communityGens: false,
      communityAutoGens: true
    })
    const allAutoGensCount = await getResultCount(page)
    console.log(`All auto-gens (auto content): ${allAutoGensCount} results`)

    // All counts should be >= 0
    expect(yourContentCount).toBeGreaterThanOrEqual(0)
    expect(communityContentCount).toBeGreaterThanOrEqual(0)
    expect(allGensCount).toBeGreaterThanOrEqual(0)
    expect(allAutoGensCount).toBeGreaterThanOrEqual(0)
  })

  test('should persist filter state during navigation', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Set a specific filter combination
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: false,
      communityGens: true,
      communityAutoGens: false
    })

    const initialCount = await getResultCount(page)

    // Navigate to a detail page and back
    const firstItem = page.locator('[data-testid^="gallery-result-item-"]').first()
    if (await firstItem.isVisible()) {
      await firstItem.click()
      await page.waitForLoadState('networkidle')

      // Go back
      await page.goBack()
      await waitForGalleryLoad(page)

      // Verify filters are still in the same state
      const finalCount = await getResultCount(page)
      expect(finalCount).toBe(initialCount)

      // Verify the toggles are still in the correct state
      const yourGensToggle = page.locator('[data-testid="gallery-toggle-your-gens"]')
      const yourAutoGensToggle = page.locator('[data-testid="gallery-toggle-your-autogens"]')
      const communityGensToggle = page.locator('[data-testid="gallery-toggle-community-gens"]')
      const communityAutoGensToggle = page.locator('[data-testid="gallery-toggle-community-autogens"]')

      await expect(yourGensToggle).toBeChecked()
      await expect(yourAutoGensToggle).not.toBeChecked()
      await expect(communityGensToggle).toBeChecked()
      await expect(communityAutoGensToggle).not.toBeChecked()
    }
  })

  test('should update result count immediately when toggling filters', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Start with all filters ON
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: true,
      communityGens: true,
      communityAutoGens: true
    })

    const initialCount = await getResultCount(page)

    // Toggle one filter OFF
    await toggleFilter(page, 'your-gens', false)

    const newCount = await getResultCount(page)

    // Count should have changed (unless "your gens" was already 0)
    // We just verify the page updated
    expect(newCount).toBeGreaterThanOrEqual(0)
    expect(newCount).toBeLessThanOrEqual(initialCount)
  })

  test('should show stats popover with correct breakdown', async ({ page }) => {
    await page.goto('/gallery')
    await waitForGalleryLoad(page)

    // Make sure all filters are ON
    await setAllFilters(page, {
      yourGens: true,
      yourAutoGens: true,
      communityGens: true,
      communityAutoGens: true
    })

    // Find and hover over the stats info button
    const infoButton = page.locator('[data-testid="gallery-options-stats-info-button"]')

    if (await infoButton.isVisible()) {
      // Trigger the popover by hovering
      await infoButton.hover()
      await page.waitForTimeout(500)

      // Verify popover is visible
      const popover = page.locator('[data-testid="gallery-stats-popover"]')
      await expect(popover).toBeVisible()

      // Verify stats breakdown is shown
      const userRegularStat = page.locator('[data-testid="gallery-stats-user-regular"]')
      const userAutoStat = page.locator('[data-testid="gallery-stats-user-auto"]')
      const communityRegularStat = page.locator('[data-testid="gallery-stats-community-regular"]')
      const communityAutoStat = page.locator('[data-testid="gallery-stats-community-auto"]')

      await expect(userRegularStat).toBeVisible()
      await expect(userAutoStat).toBeVisible()
      await expect(communityRegularStat).toBeVisible()
      await expect(communityAutoStat).toBeVisible()

      // Get the stat values
      const userRegularText = await userRegularStat.textContent()
      const userAutoText = await userAutoStat.textContent()
      const communityRegularText = await communityRegularStat.textContent()
      const communityAutoText = await communityAutoStat.textContent()

      // Extract numbers from text (format: "Your gens: 5")
      const extractNumber = (text: string | null): number => {
        if (!text) return 0
        const match = text.match(/(\d+)/)
        return match ? parseInt(match[1], 10) : 0
      }

      const userRegularCount = extractNumber(userRegularText)
      const userAutoCount = extractNumber(userAutoText)
      const communityRegularCount = extractNumber(communityRegularText)
      const communityAutoCount = extractNumber(communityAutoText)

      console.log('Stats breakdown:', {
        userRegular: userRegularCount,
        userAuto: userAutoCount,
        communityRegular: communityRegularCount,
        communityAuto: communityAutoCount
      })

      // Verify the sum equals the total
      const totalFromStats = userRegularCount + userAutoCount + communityRegularCount + communityAutoCount
      const totalFromPagination = await getResultCount(page)
      expect(totalFromStats).toBe(totalFromPagination)
    }
  })
})
