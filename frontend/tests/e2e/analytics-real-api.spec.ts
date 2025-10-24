import { test, expect } from '@playwright/test'
import {
  ensureRealApiAvailable,
  loginAsTestUser,
  waitForPageLoad,
} from './utils/realApiHelpers'

test.describe('Analytics Page (Real API)', () => {
  test.beforeEach(async ({ page }) => {
    // Check if real API is available, skip if not
    try {
      await ensureRealApiAvailable(page)
    } catch (error) {
      test.skip(true, 'Real API server not available on port 8002. Run with: npm run test:e2e:real-api')
      return
    }

    // Log in as test user
    await loginAsTestUser(page)
  })

  test.describe('Navigation', () => {
    test('navigates to Analytics page from Settings page', async ({ page }) => {
      // Go to Settings page first
      await page.goto('/settings')
      await waitForPageLoad(page, 'settings')

      // Look for Analytics card/link
      const analyticsLink = page.getByRole('link', { name: /analytics/i }).or(
        page.getByText(/analytics/i).locator('..')
      )

      await analyticsLink.click()
      await waitForPageLoad(page, 'analytics')

      // Verify we're on the Analytics page
      await expect(page).toHaveURL(/\/settings\/analytics/)
      await expect(page.getByTestId('analytics-page-root')).toBeVisible()
      await expect(page.getByTestId('analytics-title')).toHaveText('Analytics')
    })

    test('shows Analytics page header and sections', async ({ page }) => {
      await page.goto('/settings/analytics')
      await waitForPageLoad(page, 'analytics')

      // Check page header
      await expect(page.getByTestId('analytics-title')).toHaveText('Analytics')
      await expect(page.getByTestId('analytics-subtitle')).toBeVisible()

      // Check refresh all button
      await expect(page.getByTestId('analytics-refresh-all')).toBeVisible()

      // Check last updated timestamp
      await expect(page.getByTestId('analytics-last-updated')).toBeVisible()

      // Check all three card sections are present
      await expect(page.getByTestId('route-analytics-card')).toBeVisible()
      await expect(page.getByTestId('generation-analytics-card')).toBeVisible()
      await expect(page.getByTestId('tag-cardinality-card')).toBeVisible()
    })
  })

  test.describe('Route Analytics Section', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/settings/analytics')
      await waitForPageLoad(page, 'analytics')
    })

    test('shows route analytics with filters', async ({ page }) => {
      // Check section title
      await expect(page.getByTestId('route-analytics-title')).toHaveText('Route Analytics')

      // Check filters are present
      await expect(page.getByTestId('route-analytics-filters')).toBeVisible()
      await expect(page.getByTestId('route-analytics-system-select')).toBeVisible()
      await expect(page.getByTestId('route-analytics-days-select')).toBeVisible()
      await expect(page.getByTestId('route-analytics-topn-select')).toBeVisible()

      // Check refresh button
      await expect(page.getByTestId('route-analytics-refresh')).toBeVisible()
    })

    test('loads and displays route data', async ({ page }) => {
      // Wait for data to load (either table or empty state)
      await page.waitForTimeout(2000)

      // Check if we have data or empty state
      const hasTable = await page.getByTestId('route-analytics-table').count() > 0
      const hasEmpty = await page.getByTestId('route-analytics-empty').count() > 0

      expect(hasTable || hasEmpty).toBe(true)

      // If we have data, verify table structure
      if (hasTable) {
        const table = page.getByTestId('route-analytics-table')
        await expect(table).toBeVisible()

        // Check for table headers
        await expect(table.getByText(/method/i)).toBeVisible()
        await expect(table.getByText(/route/i)).toBeVisible()
        await expect(table.getByText(/req\/hr/i)).toBeVisible()
        await expect(table.getByText(/latency/i)).toBeVisible()
      }
    })

    test('changes time range filter', async ({ page }) => {
      const daysSelect = page.getByTestId('route-analytics-days-select')

      // Get initial value
      const initialValue = await daysSelect.inputValue()

      // Open select dropdown
      await daysSelect.click()

      // Select a different option (14 days if not already selected, otherwise 30 days)
      const targetOption = initialValue === '14' ? '30' : '14'
      await page.getByRole('option', { name: targetOption === '14' ? /14 days/i : /30 days/i }).click()

      // Wait for data to reload
      await page.waitForTimeout(1000)

      // Verify selection changed
      await expect(daysSelect).toHaveValue(targetOption)
    })

    test('changes Top N filter', async ({ page }) => {
      const topNSelect = page.getByTestId('route-analytics-topn-select')

      // Get initial value
      const initialValue = await topNSelect.inputValue()

      // Open select dropdown
      await topNSelect.click()

      // Select a different option
      const targetOption = initialValue === '10' ? '20' : '10'
      await page.getByRole('option', { name: targetOption === '10' ? /top 10/i : /top 20/i }).click()

      // Wait for data to reload
      await page.waitForTimeout(1000)

      // Verify selection changed
      await expect(topNSelect).toHaveValue(targetOption)
    })

    test('persists filter selections across page reload', async ({ page }) => {
      // Change filters
      const daysSelect = page.getByTestId('route-analytics-days-select')
      await daysSelect.click()
      await page.getByRole('option', { name: /14 days/i }).click()
      await page.waitForTimeout(500)

      const topNSelect = page.getByTestId('route-analytics-topn-select')
      await topNSelect.click()
      await page.getByRole('option', { name: /top 20/i }).click()
      await page.waitForTimeout(500)

      // Reload page
      await page.reload()
      await waitForPageLoad(page, 'analytics')

      // Verify filters are still set
      await expect(daysSelect).toHaveValue('14')
      await expect(topNSelect).toHaveValue('20')
    })

    test('refreshes data when refresh button clicked', async ({ page }) => {
      const refreshButton = page.getByTestId('route-analytics-refresh')

      // Click refresh
      await refreshButton.click()

      // Wait for refresh to complete
      await page.waitForTimeout(1000)

      // Button should still be visible after refresh
      await expect(refreshButton).toBeVisible()
    })
  })

  test.describe('Generation Analytics Section', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/settings/analytics')
      await waitForPageLoad(page, 'analytics')
    })

    test('shows generation analytics with filters', async ({ page }) => {
      // Check section title
      await expect(page.getByTestId('generation-analytics-title')).toHaveText('Generation Analytics')

      // Check filters are present
      await expect(page.getByTestId('generation-analytics-filters')).toBeVisible()
      await expect(page.getByTestId('generation-analytics-days-select')).toBeVisible()

      // Check refresh button
      await expect(page.getByTestId('generation-analytics-refresh')).toBeVisible()
    })

    test('loads and displays generation metrics', async ({ page }) => {
      // Wait for data to load
      await page.waitForTimeout(2000)

      // Check if we have data or empty state
      const hasMetrics = await page.getByTestId('generation-analytics-metrics').count() > 0
      const hasEmpty = await page.getByTestId('generation-analytics-empty').count() > 0

      expect(hasMetrics || hasEmpty).toBe(true)

      // If we have data, verify metrics are displayed
      if (hasMetrics) {
        const metrics = page.getByTestId('generation-analytics-metrics')
        await expect(metrics).toBeVisible()

        // Should show metric cards
        await expect(metrics.getByText(/total generations/i)).toBeVisible()
        await expect(metrics.getByText(/success rate/i)).toBeVisible()
        await expect(metrics.getByText(/avg duration/i)).toBeVisible()
        await expect(metrics.getByText(/unique users/i)).toBeVisible()
      }
    })

    test('changes time range filter', async ({ page }) => {
      const daysSelect = page.getByTestId('generation-analytics-days-select')

      // Get initial value
      const initialValue = await daysSelect.inputValue()

      // Open select dropdown
      await daysSelect.click()

      // Select a different option
      const targetOption = initialValue === '7' ? '30' : '7'
      await page.getByRole('option', { name: targetOption === '7' ? /7 days/i : /30 days/i }).click()

      // Wait for data to reload
      await page.waitForTimeout(1000)

      // Verify selection changed
      await expect(daysSelect).toHaveValue(targetOption)
    })

    test('refreshes data when refresh button clicked', async ({ page }) => {
      const refreshButton = page.getByTestId('generation-analytics-refresh')

      // Click refresh
      await refreshButton.click()

      // Wait for refresh to complete
      await page.waitForTimeout(1000)

      // Button should still be visible after refresh
      await expect(refreshButton).toBeVisible()
    })
  })

  test.describe('Tag Cardinality Section', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/settings/analytics')
      await waitForPageLoad(page, 'analytics')
    })

    test('shows tag cardinality with tabs', async ({ page }) => {
      // Check section title
      await expect(page.getByTestId('tag-cardinality-title')).toHaveText('Tags')

      // Check tabs are present
      await expect(page.getByTestId('tag-cardinality-tabs')).toBeVisible()
      await expect(page.getByTestId('tag-cardinality-tab-table')).toBeVisible()
      await expect(page.getByTestId('tag-cardinality-tab-visualization')).toBeVisible()

      // Table tab should be selected by default
      await expect(page.getByTestId('tag-cardinality-tab-table')).toHaveAttribute('aria-selected', 'true')
    })

    test('switches between Table and Visualization tabs', async ({ page }) => {
      // Click on Visualization tab
      await page.getByTestId('tag-cardinality-tab-visualization').click()
      await page.waitForTimeout(500)

      // Visualization tab should be selected
      await expect(page.getByTestId('tag-cardinality-tab-visualization')).toHaveAttribute('aria-selected', 'true')

      // Should show visualization content (log scale toggle)
      await expect(page.getByRole('switch', { name: /log scale/i })).toBeVisible()

      // Click back to Table tab
      await page.getByTestId('tag-cardinality-tab-table').click()
      await page.waitForTimeout(500)

      // Table tab should be selected
      await expect(page.getByTestId('tag-cardinality-tab-table')).toHaveAttribute('aria-selected', 'true')
    })

    test('shows Regular and Auto-Generated sections in Table tab', async ({ page }) => {
      // Should be on Table tab by default
      await expect(page.getByText(/regular content/i).first()).toBeVisible()
      await expect(page.getByText(/auto-generated content/i).first()).toBeVisible()

      // Both sections should have Show selectors
      await expect(page.getByTestId('tag-cardinality-items-topn-select')).toBeVisible()
      await expect(page.getByTestId('tag-cardinality-auto-topn-select')).toBeVisible()
    })

    test('toggles log scale in Visualization tab', async ({ page }) => {
      // Go to Visualization tab
      await page.getByTestId('tag-cardinality-tab-visualization').click()
      await page.waitForTimeout(500)

      const logScaleToggle = page.getByRole('switch', { name: /log scale/i })

      // Get initial state
      const initialState = await logScaleToggle.isChecked()

      // Toggle
      await logScaleToggle.click()
      await page.waitForTimeout(500)

      // Verify state changed
      const newState = await logScaleToggle.isChecked()
      expect(newState).not.toBe(initialState)

      // Toggle back
      await logScaleToggle.click()
      await page.waitForTimeout(500)

      // Verify state changed back
      const finalState = await logScaleToggle.isChecked()
      expect(finalState).toBe(initialState)
    })

    test('persists tab selection across page reload', async ({ page }) => {
      // Switch to Visualization tab
      await page.getByTestId('tag-cardinality-tab-visualization').click()
      await page.waitForTimeout(500)

      // Reload page
      await page.reload()
      await waitForPageLoad(page, 'analytics')

      // Visualization tab should still be selected
      await expect(page.getByTestId('tag-cardinality-tab-visualization')).toHaveAttribute('aria-selected', 'true')
    })
  })

  test.describe('Global Functionality', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/settings/analytics')
      await waitForPageLoad(page, 'analytics')
    })

    test('refreshes all sections when Refresh All button clicked', async ({ page }) => {
      const refreshAllButton = page.getByTestId('analytics-refresh-all')

      // Get initial timestamp
      const initialTimestamp = await page.getByTestId('analytics-last-updated').textContent()

      // Wait a moment to ensure timestamp will change
      await page.waitForTimeout(1000)

      // Click refresh all
      await refreshAllButton.click()

      // Wait for refresh to complete
      await page.waitForTimeout(1000)

      // Timestamp should have updated
      const newTimestamp = await page.getByTestId('analytics-last-updated').textContent()
      expect(newTimestamp).not.toBe(initialTimestamp)
    })

    test('shows total unique tags count', async ({ page }) => {
      // Wait for data to load
      await page.waitForTimeout(2000)

      // Check if total tag count is displayed
      const totalCount = page.getByTestId('tag-cardinality-total')
      if (await totalCount.count() > 0) {
        await expect(totalCount).toBeVisible()
        await expect(totalCount).toContainText(/total tags:/i)
      }
    })
  })

  test.describe('Responsive Behavior', () => {
    test('displays correctly on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await page.goto('/settings/analytics')
      await waitForPageLoad(page, 'analytics')

      // Page should still be accessible
      await expect(page.getByTestId('analytics-page-root')).toBeVisible()
      await expect(page.getByTestId('analytics-title')).toBeVisible()

      // All three sections should be visible (stacked vertically)
      await expect(page.getByTestId('route-analytics-card')).toBeVisible()
      await expect(page.getByTestId('generation-analytics-card')).toBeVisible()
      await expect(page.getByTestId('tag-cardinality-card')).toBeVisible()

      // Filters should be visible
      await expect(page.getByTestId('route-analytics-filters')).toBeVisible()
      await expect(page.getByTestId('generation-analytics-filters')).toBeVisible()
    })
  })

  test.describe('Error Handling', () => {
    test('handles data loading states', async ({ page }) => {
      await page.goto('/settings/analytics')

      // Page should eventually show either data or empty states
      await page.waitForTimeout(3000)

      // Each section should have either:
      // 1. Data displayed (table, metrics, etc.)
      // 2. Loading skeleton
      // 3. Error message
      // 4. Empty state

      const routeSection = page.getByTestId('route-analytics-card')
      await expect(routeSection).toBeVisible()

      const generationSection = page.getByTestId('generation-analytics-card')
      await expect(generationSection).toBeVisible()

      const tagSection = page.getByTestId('tag-cardinality-card')
      await expect(tagSection).toBeVisible()
    })
  })
})
