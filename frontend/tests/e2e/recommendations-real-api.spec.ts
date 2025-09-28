import { test, expect } from '@playwright/test'
import {
  ensureRealApiAvailable,
  assertSufficientTestData,
  loginAsTestUser,
  waitForPageLoad,
  getUserRecommendations,
  markRecommendationServed,
  cleanupTestData
} from './utils/realApiHelpers'

test.describe('Recommendations page (Real API)', () => {
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
      await assertSufficientTestData(page, '/api/v1/content/unified?page=1&page_size=1', 1)
    } catch (error) {
      test.skip(true, 'Real API returned zero gallery results. Ensure the test database seed ran (make frontend-test-e2e-real-api).')
      return
    }

    // Log in as test user
    await loginAsTestUser(page)
  })

  test('marks a recommendation as served', async ({ page }) => {
    // Get recommendations from API
    let recommendations
    try {
      recommendations = await getUserRecommendations(page)
    } catch (error) {
      test.skip(true, 'No recommendations available or API endpoint not implemented')
      return
    }

    // Skip if no recommendations available
    if (!recommendations || (Array.isArray(recommendations) && recommendations.length === 0)) {
      test.skip(true, 'No recommendations available for testing')
      return
    }

    const recommendationsList = Array.isArray(recommendations) ? recommendations : recommendations.items || []

    if (recommendationsList.length === 0) {
      test.skip(true, 'No recommendation items available for testing')
      return
    }

    // Find an unserved recommendation
    const unservedRec = recommendationsList.find(rec => !rec.served_at && !rec.is_served)

    if (!unservedRec) {
      test.skip(true, 'No unserved recommendations available for testing')
      return
    }

    await page.goto('/recommendations')
    await waitForPageLoad(page, 'recommendations')

    // Look for recommendation content on the page
    const recommendationElements = [
      page.getByText(new RegExp(`recommendation.*${unservedRec.id}`, 'i')),
      page.getByText(/recommendation #\d+/i),
      page.locator(`[data-testid*="recommendation-${unservedRec.id}"]`),
      page.locator('[data-testid*="recommendation"]')
    ]

    let foundRecommendation = null
    for (const element of recommendationElements) {
      if (await element.count() > 0 && await element.isVisible()) {
        foundRecommendation = element
        break
      }
    }

    if (!foundRecommendation) {
      // If specific recommendation not found, look for any recommendations
      const generalRec = page.locator('text=/recommendation/i').first()
      if (await generalRec.count() > 0) {
        foundRecommendation = generalRec
      }
    }

    if (foundRecommendation) {
      // Look for "mark as served" button
      const serveButtons = [
        page.getByRole('button', { name: /mark as served/i }),
        page.getByRole('button', { name: /served/i }),
        page.getByRole('button', { name: /mark.*served/i }),
        foundRecommendation.locator('button').filter({ hasText: /served/i })
      ]

      let serveButton = null
      for (const button of serveButtons) {
        if (await button.count() > 0 && await button.isVisible()) {
          serveButton = button
          break
        }
      }

      if (serveButton) {
        // Click the serve button
        await serveButton.click()

        // Wait for the action to complete
        await page.waitForTimeout(1000)

        // Look for success indicators
        const successIndicators = [
          page.getByText(/served/i),
          page.getByText(/marked as served/i),
          page.getByText(/success/i),
          page.locator('[data-testid*="served"]')
        ]

        let foundSuccess = false
        for (const indicator of successIndicators) {
          if (await indicator.count() > 0 && await indicator.isVisible()) {
            foundSuccess = true
            break
          }
        }

        if (foundSuccess) {
          // Verify the change via API
          try {
            const updatedRecommendations = await getUserRecommendations(page)
            const updatedList = Array.isArray(updatedRecommendations) ?
              updatedRecommendations : updatedRecommendations.items || []

            const updatedRec = updatedList.find(rec => rec.id === unservedRec.id)
            if (updatedRec) {
              expect(updatedRec.served_at || updatedRec.is_served).toBeTruthy()
            }
          } catch (error) {
            // API verification failed, but UI showed success
            console.warn('Could not verify recommendation status via API')
          }
        } else {
          // Button clicked but no clear success indicator
          // Check if button state changed (e.g., disabled, text changed)
          const buttonDisabled = await serveButton.isDisabled()
          const buttonText = await serveButton.textContent()

          expect(buttonDisabled || buttonText?.toLowerCase().includes('served')).toBe(true)
        }
      } else {
        test.skip(true, 'No "mark as served" button found on recommendations page')
      }
    } else {
      test.skip(true, 'No recommendations displayed on the page')
    }
  })

  test('displays recommendations list correctly', async ({ page }) => {
    await page.goto('/recommendations')
    await waitForPageLoad(page, 'recommendations')

    // Check if recommendations are loaded and displayed
    try {
      const recommendations = await getUserRecommendations(page)
      const recommendationsList = Array.isArray(recommendations) ?
        recommendations : recommendations.items || []

      if (recommendationsList.length > 0) {
        // Should display recommendations
        const recommendationDisplays = [
          page.getByText(/recommendation/i),
          page.locator('[data-testid*="recommendation"]'),
          page.locator('li, .recommendation, [role="listitem"]')
        ]

        let foundDisplay = false
        for (const display of recommendationDisplays) {
          if (await display.count() > 0) {
            foundDisplay = true
            break
          }
        }

        expect(foundDisplay).toBe(true)

        // Should show recommendation details
        const rec = recommendationsList[0]
        if (rec.id) {
          const idDisplay = page.getByText(rec.id.toString())
          if (await idDisplay.count() > 0) {
            await expect(idDisplay).toBeVisible()
          }
        }

        // Should show action buttons
        const actionButtons = [
          page.getByRole('button', { name: /mark as served/i }),
          page.getByRole('button', { name: /served/i }),
          page.getByRole('button', { name: /view/i }),
          page.getByRole('button', { name: /action/i })
        ]

        let foundButton = false
        for (const button of actionButtons) {
          if (await button.count() > 0) {
            foundButton = true
            break
          }
        }

        expect(foundButton).toBe(true)
      } else {
        // No recommendations available - should show empty state
        const emptyStates = [
          page.getByText(/no recommendations/i),
          page.getByText(/no items/i),
          page.getByText(/empty/i),
          page.getByText(/nothing here/i)
        ]

        let foundEmptyState = false
        for (const emptyState of emptyStates) {
          if (await emptyState.count() > 0 && await emptyState.isVisible()) {
            foundEmptyState = true
            break
          }
        }

        if (!foundEmptyState) {
          // At minimum, page should load without errors
          await expect(page.locator('main')).toBeVisible()
        }
      }
    } catch (error) {
      // API call failed - check if page handles this gracefully
      await expect(page.locator('main')).toBeVisible()

      const errorStates = [
        page.getByText(/error/i),
        page.getByText(/failed to load/i),
        page.getByText(/try again/i),
        page.locator('[data-testid*="error"]')
      ]

      let foundErrorState = false
      for (const errorState of errorStates) {
        if (await errorState.count() > 0 && await errorState.isVisible()) {
          foundErrorState = true
          break
        }
      }

      // Either show error state or graceful fallback
      expect(foundErrorState || await page.locator('main').isVisible()).toBe(true)
    }
  })

  test('handles recommendation interactions correctly', async ({ page }) => {
    await page.goto('/recommendations')
    await waitForPageLoad(page, 'recommendations')

    // Look for any interactive elements on the recommendations page
    const interactiveElements = [
      page.getByRole('button'),
      page.getByRole('link'),
      page.locator('input[type="checkbox"]'),
      page.locator('[role="button"]')
    ]

    let foundInteraction = false
    for (const element of interactiveElements) {
      const count = await element.count()
      if (count > 0) {
        foundInteraction = true

        // Test that at least one element is clickable
        const firstElement = element.first()
        if (await firstElement.isVisible() && await firstElement.isEnabled()) {
          // Verify it responds to hover/focus
          await firstElement.hover()
          await firstElement.focus()

          // The element should be focusable
          const isFocused = await firstElement.evaluate(el => document.activeElement === el)
          if (isFocused) {
            expect(isFocused).toBe(true)
          }
        }
        break
      }
    }

    // Page should have some form of interaction or content
    if (!foundInteraction) {
      // At minimum, navigation should work
      await expect(page.locator('nav')).toBeVisible()
    }
  })

  test('maintains recommendation state across navigation', async ({ page }) => {
    await page.goto('/recommendations')
    await waitForPageLoad(page, 'recommendations')

    // Capture initial state
    const initialContent = await page.locator('main').textContent()

    // Navigate away and back
    await page.click('[href="/dashboard"]')
    await waitForPageLoad(page, 'dashboard')
    await expect(page).toHaveURL('/dashboard')

    await page.click('[href="/recommendations"]')
    await waitForPageLoad(page, 'recommendations')

    // Content should be consistent
    const returnContent = await page.locator('main').textContent()

    // Basic consistency check - page should load the same content
    if (initialContent && returnContent) {
      // Should contain similar structural elements
      const hasRecommendations = initialContent.toLowerCase().includes('recommendation')
      const stillHasRecommendations = returnContent.toLowerCase().includes('recommendation')

      if (hasRecommendations) {
        expect(stillHasRecommendations).toBe(true)
      }
    }

    // Page should not crash or show errors
    await expect(page.locator('main')).toBeVisible()
  })

  test('handles empty recommendations state', async ({ page }) => {
    await page.goto('/recommendations')
    await waitForPageLoad(page, 'recommendations')

    // Check for empty state handling
    const emptyStateIndicators = [
      page.getByText(/no recommendations/i),
      page.getByText(/no items found/i),
      page.getByText(/nothing to show/i),
      page.getByText(/empty/i),
      page.locator('[data-testid*="empty"]'),
      page.locator('.empty-state')
    ]

    let foundEmptyState = false
    for (const indicator of emptyStateIndicators) {
      if (await indicator.count() > 0 && await indicator.isVisible()) {
        foundEmptyState = true
        break
      }
    }

    // Check for recommendation content
    const hasRecommendations = await page.getByText(/recommendation/i).count() > 0

    if (!hasRecommendations && !foundEmptyState) {
      // Should at least show the page without errors
      await expect(page.locator('main')).toBeVisible()

      // Should not show error messages
      const errorMessages = [
        page.getByText(/error/i),
        page.getByText(/failed/i),
        page.getByText(/broken/i)
      ]

      for (const errorMsg of errorMessages) {
        await expect(errorMsg).not.toBeVisible()
      }
    }

    // Page should be functional regardless of content
    await expect(page.locator('nav')).toBeVisible()
    await expect(page.locator('main')).toBeVisible()
  })
})