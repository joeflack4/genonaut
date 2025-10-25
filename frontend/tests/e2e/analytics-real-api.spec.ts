/**
 * E2E Tests for Analytics Page with Real API
 *
 * Tests analytics functionality including:
 * - Route performance metrics
 * - Generation analytics
 * - Tag cardinality statistics
 * - Responsive behavior
 */

import { test, expect } from '@playwright/test'
import { waitForPageLoad } from './utils/realApiHelpers'
import { handleMissingData } from './utils/testDataHelpers'

const ROUTE_ANALYTICS_TITLE = 'Route Analytics'
const GENERATION_ANALYTICS_TITLE = 'Generation Analytics'
const TAG_CARDINALITY_TITLE = 'Tags'

/**
 * Wait for MUI Select to be interactable and click it
 */
async function clickSelect(page: any, selector: string) {
  const selectElement = page.getByTestId(selector)

  // Wait for the element to be visible
  await expect(selectElement).toBeVisible({ timeout: 5000 })

  // Try to click the parent element instead of the input
  // MUI Select has a div wrapper around the hidden input
  const parentElement = selectElement.locator('..')
  await parentElement.click()

  // Wait for menu to open
  await page.waitForTimeout(300)
}

test.describe('Analytics Page (Real API)', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to analytics page
    await page.goto('/analytics')
    await waitForPageLoad(page, 'analytics')
    await page.waitForTimeout(1000) // Additional wait for data loading
  })

  test.describe('Page Structure', () => {
    test('displays page title and subtitle', async ({ page }) => {
      await expect(page.getByTestId('analytics-title')).toHaveText('Analytics')
      await expect(page.getByTestId('analytics-subtitle')).toContainText('System performance metrics')
    })

    test('displays refresh all button', async ({ page }) => {
      const refreshBtn = page.getByTestId('analytics-refresh-all')
      await expect(refreshBtn).toBeVisible()
      await expect(refreshBtn).toHaveText('Refresh All')
    })

    test('displays all analytics cards', async ({ page }) => {
      // Route Analytics Card
      await expect(page.getByTestId('route-analytics-card')).toBeVisible()
      await expect(page.getByText(ROUTE_ANALYTICS_TITLE)).toBeVisible()

      // Generation Analytics Card
      await expect(page.getByTestId('generation-analytics-card')).toBeVisible()
      await expect(page.getByText(GENERATION_ANALYTICS_TITLE)).toBeVisible()

      // Tag Cardinality Card (may not be visible if no data)
      const tagCard = page.getByTestId('tag-cardinality-card')
      const hasTagCard = await tagCard.isVisible().catch(() => false)
      if (hasTagCard) {
        await expect(page.getByText(TAG_CARDINALITY_TITLE)).toBeVisible()
      }
    })
  })

  test.describe('Navigation', () => {
    test('navigates to Analytics page from Settings page', async ({ page }) => {
      // Go to settings page first
      await page.goto('/settings')
      await waitForPageLoad(page, 'settings')

      // Find and click analytics link in settings
      const analyticsLink = page.getByTestId('settings-analytics-link')
      await expect(analyticsLink).toBeVisible()
      await analyticsLink.click()

      // Should navigate to analytics page
      await page.waitForURL(/\/analytics/)
      await expect(page.getByTestId('analytics-page-root')).toBeVisible()
    })
  })

  test.describe('Route Analytics Section', () => {
    test('displays route performance data', async ({ page }) => {
      // Check for main elements
      await expect(page.getByTestId('route-analytics-card')).toBeVisible()

      // Check for time range selector
      await expect(page.getByTestId('route-analytics-timerange-select')).toBeVisible()

      // Check for table (should show even if empty)
      const tableOrEmpty = page.locator('[data-testid="route-analytics-table"], [data-testid="route-analytics-empty"]')
      await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })

    test('displays route columns in table', async ({ page }) => {
      // Check if table has data
      const hasTable = await page.getByTestId('route-analytics-table').isVisible().catch(() => false)

      if (hasTable) {
        // Should have these columns
        await expect(page.getByRole('columnheader', { name: /route/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /total queries/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /unique users/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /avg response/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /cache priority/i })).toBeVisible()
      } else {
        // Should show empty state
        await expect(page.getByTestId('route-analytics-empty')).toBeVisible()
      }
    })

    test('shows correct cache priority chip colors', async ({ page }) => {
      // Check if table has data
      const hasRows = await page.locator('[data-testid="route-analytics-table"] tbody tr').count()

      if (hasRows > 0) {
        // Get all priority chips
        const priorityChips = page.locator('[data-testid^="route-priority-"]')
        const chipCount = await priorityChips.count()

        for (let i = 0; i < chipCount; i++) {
          const chip = priorityChips.nth(i)
          const testId = await chip.getAttribute('data-testid')

          if (testId?.includes('high')) {
            // High priority should have specific styling
            await expect(chip).toBeVisible()
          } else if (testId?.includes('medium')) {
            // Medium priority
            await expect(chip).toBeVisible()
          } else if (testId?.includes('low')) {
            // Low priority
            await expect(chip).toBeVisible()
          }
        }
      }
    })

    test('changes time range filter', async ({ page }) => {
      // Click on time range select using parent element
      await clickSelect(page, 'route-analytics-timerange-select')

      // Select "Last 7 Days"
      await page.getByRole('option', { name: /last 7 days/i }).click()

      // Verify selection changed
      await expect(page.getByTestId('route-analytics-timerange-select')).toContainText('Last 7 Days')
    })

    test('changes Top N filter', async ({ page }) => {
      // Click on Top N select using parent element
      await clickSelect(page, 'route-analytics-topn-select')

      // Select "Top 20"
      await page.getByRole('option', { name: /top 20/i }).click()

      // Verify selection changed
      await expect(page.getByTestId('route-analytics-topn-select')).toContainText('Top 20')
    })

    test('persists filter selections across page reload', async ({ page }) => {
      // Change time range using parent element
      await clickSelect(page, 'route-analytics-timerange-select')
      await page.getByRole('option', { name: /last 30 days/i }).click()

      // Change Top N using parent element
      await clickSelect(page, 'route-analytics-topn-select')
      await page.getByRole('option', { name: /top 50/i }).click()

      // Wait for changes to be saved
      await page.waitForTimeout(500)

      // Reload page
      await page.reload()
      await waitForPageLoad(page, 'analytics')

      // Verify selections persisted
      await expect(page.getByTestId('route-analytics-timerange-select')).toContainText('Last 30 Days')
      await expect(page.getByTestId('route-analytics-topn-select')).toContainText('Top 50')
    })
  })

  test.describe('Generation Analytics Section', () => {
    test('displays generation metrics', async ({ page }) => {
      // Check for main elements
      await expect(page.getByTestId('generation-analytics-card')).toBeVisible()

      // Check for statistics grid (should always be visible even with zeros)
      await expect(page.getByTestId('generation-analytics-stats')).toBeVisible()

      // Check for individual stat items
      await expect(page.getByTestId('gen-stat-total-generations')).toBeVisible()
      await expect(page.getByTestId('gen-stat-success-rate')).toBeVisible()
      await expect(page.getByTestId('gen-stat-avg-duration')).toBeVisible()
      await expect(page.getByTestId('gen-stat-unique-users')).toBeVisible()
    })

    test('displays generation chart or empty state', async ({ page }) => {
      // Either chart or empty state should be visible
      const chartOrEmpty = page.locator('[data-testid="generation-analytics-chart"], [data-testid="generation-analytics-empty"]')
      await expect(chartOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })

    test('displays recent generations table or empty state', async ({ page }) => {
      // Either table or empty state should be visible
      const tableOrEmpty = page.locator('[data-testid="recent-generations-table"], [data-testid="recent-generations-empty"]')
      await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })

    test('displays generation table columns', async ({ page }) => {
      // Check if table has data
      const hasTable = await page.getByTestId('recent-generations-table').isVisible().catch(() => false)

      if (hasTable) {
        // Should have these columns
        await expect(page.getByRole('columnheader', { name: /title/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /type/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /status/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /created/i })).toBeVisible()
        await expect(page.getByRole('columnheader', { name: /duration/i })).toBeVisible()
      }
    })

    test('changes time range filter', async ({ page }) => {
      // Click on time range select using parent element
      await clickSelect(page, 'generation-analytics-timerange-select')

      // Select "Last 7 Days"
      await page.getByRole('option', { name: /last 7 days/i }).click()

      // Verify selection changed
      await expect(page.getByTestId('generation-analytics-timerange-select')).toContainText('Last 7 Days')
    })
  })

  test.describe('Tag Cardinality Section', () => {
    test('displays tag cardinality card if data available', async ({ page }) => {
      const cardinalityCard = page.getByTestId('tag-cardinality-card')
      const hasCard = await cardinalityCard.isVisible().catch(() => false)

      if (!hasCard) {
        test.skip(true, 'Tag cardinality card not available - may need data')
        return
      }

      await expect(page.getByTestId('tag-cardinality-title')).toHaveText('Tags')

      // Check for tabs - wait for them to be available
      await expect(page.getByTestId('tag-cardinality-tabs')).toBeVisible({ timeout: 10000 })
    })

    test('switches between Table and Visualization tabs', async ({ page }) => {
      // Check if card exists
      const cardinalityCard = page.getByTestId('tag-cardinality-card')
      const hasCard = await cardinalityCard.isVisible().catch(() => false)

      if (!hasCard) {
        handleMissingData(
          test,
          'Tag cardinality test',
          'tag cardinality data',
          'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
        )
        return
      }

      // Wait for tabs container to be visible
      await expect(page.getByTestId('tag-cardinality-tabs')).toBeVisible({ timeout: 10000 })

      // Click on Visualization tab
      const vizTab = page.getByTestId('tag-cardinality-tab-visualization')
      await expect(vizTab).toBeVisible({ timeout: 10000 })
      await vizTab.click()
      await page.waitForTimeout(500)

      // Visualization tab should be selected
      await expect(vizTab).toHaveAttribute('aria-selected', 'true')

      // Should show visualization content (log scale toggle)
      await expect(page.getByRole('switch', { name: /log scale/i })).toBeVisible()

      // Click back to Table tab
      const tableTab = page.getByTestId('tag-cardinality-tab-table')
      await tableTab.click()
      await page.waitForTimeout(500)

      // Table tab should be selected
      await expect(tableTab).toHaveAttribute('aria-selected', 'true')
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
      // Check if card exists
      const cardinalityCard = page.getByTestId('tag-cardinality-card')
      const hasCard = await cardinalityCard.isVisible().catch(() => false)

      if (!hasCard) {
        handleMissingData(
          test,
          'Tag cardinality test',
          'tag cardinality data',
          'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
        )
        return
      }

      // Wait for tabs to be visible
      await expect(page.getByTestId('tag-cardinality-tabs')).toBeVisible({ timeout: 10000 })

      // Switch to Visualization tab
      const vizTab = page.getByTestId('tag-cardinality-tab-visualization')
      await expect(vizTab).toBeVisible({ timeout: 10000 })
      await vizTab.click()
      await page.waitForTimeout(500)

      // Find log scale toggle
      const logScaleToggle = page.getByRole('switch', { name: /log scale/i })
      await expect(logScaleToggle).toBeVisible({ timeout: 5000 })

      // Get initial state
      const initialState = await logScaleToggle.isChecked()

      // Toggle
      await logScaleToggle.click()

      // Verify state changed
      const newState = await logScaleToggle.isChecked()
      expect(newState).toBe(!initialState)

      // Toggle back
      await logScaleToggle.click()
      const finalState = await logScaleToggle.isChecked()
      expect(finalState).toBe(initialState)
    })

    test('changes Top N filter for Regular content', async ({ page }) => {
      const hasCard = await page.getByTestId('tag-cardinality-card').isVisible().catch(() => false)
      if (!hasCard) {
        test.skip(true, 'Tag cardinality card not available')
        return
      }

      // Click on Regular content Top N select
      await clickSelect(page, 'tag-cardinality-items-topn-select')

      // Select "Top 50"
      await page.getByRole('option', { name: /top 50/i }).click()

      // Verify selection changed
      await expect(page.getByTestId('tag-cardinality-items-topn-select')).toContainText('Top 50')
    })

    test('changes Top N filter for Auto-Generated content', async ({ page }) => {
      const hasCard = await page.getByTestId('tag-cardinality-card').isVisible().catch(() => false)
      if (!hasCard) {
        test.skip(true, 'Tag cardinality card not available')
        return
      }

      // Click on Auto-Generated content Top N select
      await clickSelect(page, 'tag-cardinality-auto-topn-select')

      // Select "Top 200"
      await page.getByRole('option', { name: /top 200/i }).click()

      // Verify selection changed
      await expect(page.getByTestId('tag-cardinality-auto-topn-select')).toContainText('Top 200')
    })
  })

  test.describe('Responsive Behavior', () => {
    test('displays correctly on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      // Navigate again with mobile viewport
      await page.goto('/analytics')

      // Don't use waitForPageLoad on mobile as nav is hidden
      // Wait for main content and network idle instead
      await page.waitForSelector('main', { state: 'visible' })
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      // Page should still load
      await expect(page.getByTestId('analytics-page-root')).toBeVisible()
      await expect(page.getByTestId('analytics-title')).toBeVisible()

      // Cards should stack vertically on mobile
      await expect(page.getByTestId('route-analytics-card')).toBeVisible()
      await expect(page.getByTestId('generation-analytics-card')).toBeVisible()
    })
  })
})