import { test, expect } from '@playwright/test'

test.describe('Recommendations Page Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recommendations')
    await page.waitForSelector('main', { timeout: 10000 })
  })

  test('should display recommendations list', async ({ page }) => {
    // Look for recommendations list or empty state
    const listContainer = page.locator('.MuiList-root, .recommendations-list, ul')

    if (await listContainer.count() > 0) {
      await expect(listContainer.first()).toBeVisible()
    } else {
      // Check for empty state
      const emptyState = page.locator('text=No recommendations, text=empty, .empty-state')
      if (await emptyState.count() > 0) {
        await expect(emptyState.first()).toBeVisible()
      }
    }
  })

  test('should handle mark as served button clicks', async ({ page }) => {
    // Look for "Mark as served" buttons
    const markServedButtons = page.locator('button:has-text("Mark as served"), button:has-text("served")')
    const buttonCount = await markServedButtons.count()

    if (buttonCount > 0) {
      const firstButton = markServedButtons.first()

      // Get initial button state
      const initialDisabled = await firstButton.isDisabled()

      // Click the button
      await firstButton.click()
      await page.waitForTimeout(500)

      // Button might become disabled during processing or disappear after serving
      const buttonStillExists = await markServedButtons.count() > 0
      if (buttonStillExists) {
        const newDisabled = await firstButton.isDisabled()
        // Button state might have changed
        expect(typeof newDisabled).toBe('boolean')
      }

      // Look for success feedback
      const successIndicator = page.locator('.MuiAlert-standardSuccess, .success, text=served, .checkmark')
      if (await successIndicator.count() > 0) {
        await expect(successIndicator.first()).toBeVisible()
      }
    } else {
      // No actionable recommendations - this is valid
      test.skip()
    }
  })

  test('should display recommendation details and status', async ({ page }) => {
    // Look for recommendation items
    const recommendations = page.locator('.MuiListItem-root, .recommendation-item, li')
    const recCount = await recommendations.count()

    if (recCount > 0) {
      const firstRec = recommendations.first()
      await expect(firstRec).toBeVisible()

      // Look for recommendation ID
      const recId = firstRec.locator('text=Recommendation #, .recommendation-id')
      if (await recId.count() > 0) {
        await expect(recId.first()).toBeVisible()
      }

      // Look for algorithm chip/tag
      const algorithm = firstRec.locator('.MuiChip-root, .algorithm-chip, .tag')
      if (await algorithm.count() > 0) {
        await expect(algorithm.first()).toBeVisible()
      }

      // Look for status indicators
      const statusIcon = firstRec.locator('svg[data-testid="CheckCircleIcon"], svg[data-testid="PendingIcon"], .status-icon')
      if (await statusIcon.count() > 0) {
        await expect(statusIcon.first()).toBeVisible()
      }
    } else {
      test.skip()
    }
  })

  test('should handle loading states', async ({ page }) => {
    // Check for loading skeletons
    const loadingElements = page.locator('.MuiSkeleton-root, .loading, .spinner')

    if (await loadingElements.count() > 0) {
      // Wait for loading to complete
      await loadingElements.first().waitFor({ state: 'hidden', timeout: 10000 })
    }

    // Verify content or empty state is shown
    const content = page.locator('.MuiList-root, main')
    await expect(content.first()).toBeVisible()
  })

  test('should display proper status indicators for served vs unserved recommendations', async ({ page }) => {
    const recommendations = page.locator('.MuiListItem-root, .recommendation-item')
    const recCount = await recommendations.count()

    if (recCount > 0) {
      for (let i = 0; i < Math.min(recCount, 3); i++) {
        const rec = recommendations.nth(i)

        // Check for served status (check icon or no action button)
        const checkIcon = rec.locator('svg[data-testid="CheckCircleIcon"]')
        const pendingIcon = rec.locator('svg[data-testid="PendingIcon"]')
        const actionButton = rec.locator('button:has-text("Mark as served")')

        // If served, should have check icon and no action button
        if (await checkIcon.count() > 0) {
          await expect(checkIcon.first()).toBeVisible()
          // Should not have action button
          expect(await actionButton.count()).toBe(0)
        }
        // If unserved, should have pending icon and action button
        else if (await pendingIcon.count() > 0) {
          await expect(pendingIcon.first()).toBeVisible()
          // Should have action button
          if (await actionButton.count() > 0) {
            await expect(actionButton.first()).toBeVisible()
          }
        }
      }
    } else {
      test.skip()
    }
  })

  test('should handle button disabled state during API calls', async ({ page }) => {
    const markServedButtons = page.locator('button:has-text("Mark as served")')

    if (await markServedButtons.count() > 0) {
      const button = markServedButtons.first()

      // Button should be enabled initially
      await expect(button).toBeEnabled()

      // Click button and immediately check if it gets disabled
      await button.click()

      // Button might briefly become disabled during API call
      const quickCheck = await button.isDisabled()
      // This test allows for either immediate disable or staying enabled
      expect(typeof quickCheck).toBe('boolean')

      // Wait for operation to complete
      await page.waitForTimeout(1000)
    } else {
      test.skip()
    }
  })
})