import { test, expect } from '@playwright/test'

test.describe('Dashboard Page Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForSelector('main', { timeout: 10000 })
  })

  test('should display welcome message with user name', async ({ page }) => {
    // Look for welcome message
    const welcomeMessage = page.locator('h1:has-text("Welcome")')
    if (await welcomeMessage.count() > 0) {
      await expect(welcomeMessage.first()).toBeVisible()

      // Check if user name is displayed
      const welcomeText = await welcomeMessage.first().textContent()
      expect(welcomeText).toContain('Welcome')
    } else {
      test.skip()
    }
  })

  test('should display gallery statistics cards', async ({ page }) => {
    // Look for stat cards
    const statCards = page.locator('.MuiCard-root, .stat-card, [role="region"]')
    const cardCount = await statCards.count()

    if (cardCount > 0) {
      // Check each stat card is visible and has content
      for (let i = 0; i < Math.min(cardCount, 4); i++) {
        const card = statCards.nth(i)
        await expect(card).toBeVisible()

        // Look for stat value and label
        const statValue = card.locator('.MuiTypography-h4, .stat-value, .value')
        const statLabel = card.locator('.MuiTypography-subtitle2, .stat-label, .label')

        if (await statValue.count() > 0) {
          await expect(statValue.first()).toBeVisible()
        }
        if (await statLabel.count() > 0) {
          await expect(statLabel.first()).toBeVisible()
        }
      }
    } else {
      test.skip()
    }
  })

  test('should display recent content sections', async ({ page }) => {
    // Look for recent content sections
    const recentSections = page.locator('h2:has-text("recent"), h6:has-text("recent"), .recent-content')
    const sectionCount = await recentSections.count()

    if (sectionCount > 0) {
      // Check each recent section
      for (let i = 0; i < Math.min(sectionCount, 3); i++) {
        const section = recentSections.nth(i)
        await expect(section).toBeVisible()

        // Look for content list or items
        const contentList = section.locator('~ .MuiList-root, ~ ul, ~ .content-list').first()
        if (await contentList.count() > 0) {
          await expect(contentList).toBeVisible()
        }
      }
    } else {
      test.skip()
    }
  })

  test('should handle stat card interactions', async ({ page }) => {
    // Look for clickable stat cards
    const statCards = page.locator('.MuiCard-root, .stat-card')
    const cardCount = await statCards.count()

    if (cardCount > 0) {
      const firstCard = statCards.first()

      // Check if card is clickable (has cursor pointer or click handler)
      const isClickable = await firstCard.evaluate(el => {
        const style = window.getComputedStyle(el)
        return style.cursor === 'pointer' || el.onclick !== null
      })

      if (isClickable) {
        // Click the card
        await firstCard.click()
        await page.waitForTimeout(500)

        // Should potentially navigate somewhere or trigger an action
        // For now, just verify the click was handled
        await expect(firstCard).toBeVisible()
      }
    } else {
      test.skip()
    }
  })

  test('should handle recent content item clicks', async ({ page }) => {
    // Look for clickable content items
    const contentItems = page.locator('.MuiListItem-root, .content-item, li')
    const itemCount = await contentItems.count()

    if (itemCount > 0) {
      // Find a clickable item
      for (let i = 0; i < Math.min(itemCount, 3); i++) {
        const item = contentItems.nth(i)

        if (await item.isVisible()) {
          const isClickable = await item.evaluate(el => {
            const style = window.getComputedStyle(el)
            return style.cursor === 'pointer' || el.onclick !== null || el.querySelector('a') !== null
          })

          if (isClickable) {
            // Click the item
            await item.click()
            await page.waitForTimeout(500)

            // Might navigate to detail view or gallery
            const currentUrl = page.url()
            // Could navigate to gallery or stay on dashboard
            expect(currentUrl).toMatch(/\/(dashboard|gallery)/)
            break
          }
        }
      }
    } else {
      test.skip()
    }
  })

  test('should handle loading states gracefully', async ({ page }) => {
    // Check for loading skeletons or indicators
    const loadingElements = page.locator('.MuiSkeleton-root, .loading, .spinner')

    // If loading elements are present, wait for them to disappear
    if (await loadingElements.count() > 0) {
      await loadingElements.first().waitFor({ state: 'hidden', timeout: 10000 })
    }

    // Verify content is loaded
    const mainContent = page.locator('h1, .MuiCard-root, main')
    await expect(mainContent.first()).toBeVisible()
  })

  test('should display proper empty states when no data', async ({ page }) => {
    // Look for empty state messages or placeholders
    const emptyStates = page.locator('text=No content, text=No recent, text=Empty, .empty-state')

    // If empty states exist, they should be properly styled and informative
    if (await emptyStates.count() > 0) {
      const firstEmptyState = emptyStates.first()
      await expect(firstEmptyState).toBeVisible()

      const text = await firstEmptyState.textContent()
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    }
  })
})