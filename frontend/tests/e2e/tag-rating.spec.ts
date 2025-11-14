/**
 * E2E tests for tag rating functionality
 * Tests the rating feature on tag detail pages
 */

import { test, expect } from '@playwright/test'
import {
  waitForPageLoad,
  waitForApiResponse,
  performActionAndWaitForApi
} from './utils/realApiHelpers'
import { handleMissingData } from './utils/testDataHelpers'

test.describe('Tag Rating (Real API)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await waitForPageLoad(page, 'home')
  })

  test('should allow user to rate a tag', async ({ page }) => {
    // First, navigate to gallery to find available tags
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Open the sidebar to see available tags
    const sidebarToggle = page.getByTestId('app-layout-toggle-sidebar')
    await sidebarToggle.click()
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(500)

    // Check if any tags are available in the sidebar
    const tagChips = page.locator('[data-testid^="tag-filter-chip-"]')
    const tagCount = await tagChips.count()

    if (tagCount === 0) {
      handleMissingData(
        test,
        'Tag rating test',
        'tags in database',
        'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      )
      return
    }

    // Get the first available tag's name
    const firstTag = tagChips.first()
    const tagName = await firstTag.textContent()

    if (!tagName) {
      handleMissingData(
        test,
        'Tag rating test',
        'tag name not found',
        'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      )
      return
    }

    // Navigate directly to the tag detail page using the tag name
    await page.goto(`/tags/${encodeURIComponent(tagName.trim())}`)
    await waitForPageLoad(page, 'tagDetail')

    // Wait for ratings section
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 })

    // Find the "Your Rating" star widget (not the average rating)
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]')
    const starWidgets = ratingsSection.locator('[data-testid="star-rating"]')

    // The second one should be "Your Rating"
    const yourRating = starWidgets.nth(1)
    await expect(yourRating).toBeVisible()

    // Click on the 4th star to rate (index 7 for 4.0 stars with 0.5 precision)
    const stars = yourRating.locator('[data-testid="star-rating-stars"]')
    const starLabels = stars.locator('label')
    await starLabels.nth(7).click({ force: true })

    // Wait for the mutation to complete (API may be too fast to show "Saving...")
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(1000)

    // Verify the rating was applied by checking the displayed value
    const ratingValue = yourRating.locator('[data-testid="star-rating-value"]')
    await expect(ratingValue).toContainText('4.0')
  })

  test('should update existing rating', async ({ page }) => {
    // First, navigate to gallery to find available tags
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Open the sidebar to see available tags
    const sidebarToggle = page.getByTestId('app-layout-toggle-sidebar')
    await sidebarToggle.click()
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(500)

    // Check if any tags are available in the sidebar
    const tagChips = page.locator('[data-testid^="tag-filter-chip-"]')
    const tagCount = await tagChips.count()

    if (tagCount === 0) {
      handleMissingData(
        test,
        'Tag rating test',
        'tags in database',
        'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      )
      return
    }

    // Get the first available tag's name
    const firstTag = tagChips.first()
    const tagName = await firstTag.textContent()

    if (!tagName) {
      handleMissingData(
        test,
        'Tag rating test',
        'tag name not found',
        'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      )
      return
    }

    // Navigate directly to the tag detail page using the tag name
    await page.goto(`/tags/${encodeURIComponent(tagName.trim())}`)
    await waitForPageLoad(page, 'tagDetail')

    // Wait for ratings section
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 })

    // Scroll the ratings section into view first
    await page.locator('[data-testid="tag-detail-ratings-section"]').scrollIntoViewIfNeeded()

    // Find the "Your Rating" star widget
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]')
    const yourRating = ratingsSection.locator('[data-testid="star-rating"]').nth(1)

    // First set a rating of 3 stars (index 5 for 3.0 stars with 0.5 precision)
    const stars = yourRating.locator('[data-testid="star-rating-stars"]')
    const starLabels = stars.locator('label')
    await starLabels.nth(5).click({ force: true })

    // Wait for mutation to complete
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(1000)

    // Now update to 5 stars (index 9 for 5.0 stars with 0.5 precision)
    await starLabels.nth(9).click({ force: true })

    // Wait for mutation to complete
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(1000)

    // Verify the rating was updated by checking the displayed value
    const ratingValue = yourRating.locator('[data-testid="star-rating-value"]')
    await expect(ratingValue).toContainText('5.0')
  })

  test('should persist rating across page refreshes', async ({ page }) => {
    // First, navigate to gallery to find available tags
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Open the sidebar to see available tags
    const sidebarToggle = page.getByTestId('app-layout-toggle-sidebar')
    await sidebarToggle.click()
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(500)

    // Check if any tags are available in the sidebar
    const tagChips = page.locator('[data-testid^="tag-filter-chip-"]')
    const tagCount = await tagChips.count()

    if (tagCount === 0) {
      handleMissingData(
        test,
        'Tag rating test',
        'tags in database',
        'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      )
      return
    }

    // Get the first available tag's name
    const firstTag = tagChips.first()
    const tagName = await firstTag.textContent()

    if (!tagName) {
      handleMissingData(
        test,
        'Tag rating test',
        'tag name not found',
        'python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      )
      return
    }

    // Navigate directly to the tag detail page using the tag name
    const tagUrl = `/tags/${encodeURIComponent(tagName.trim())}`
    await page.goto(tagUrl)
    await waitForPageLoad(page, 'tagDetail')

    // Wait for page load
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 })

    // Find and rate the tag with 2 stars (index 3 for 2.0 stars with 0.5 precision)
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]')
    const yourRating = ratingsSection.locator('[data-testid="star-rating"]').nth(1)
    const stars = yourRating.locator('[data-testid="star-rating-stars"]')
    const starLabels = stars.locator('label')
    await starLabels.nth(3).click({ force: true })

    // Wait for mutation to complete
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
    await page.waitForTimeout(1000)

    // Verify initial rating by checking the displayed value
    let ratingValue = yourRating.locator('[data-testid="star-rating-value"]')
    await expect(ratingValue).toContainText('2.0')

    // Refresh the page
    await page.reload()
    await waitForPageLoad(page, 'tagDetail')

    // Wait for ratings section to load again
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 })

    // Verify the rating persisted by checking the displayed value
    const ratingSectionAfter = page.locator('[data-testid="tag-detail-ratings-section"]')
    const yourRatingAfter = ratingSectionAfter.locator('[data-testid="star-rating"]').nth(1)
    ratingValue = yourRatingAfter.locator('[data-testid="star-rating-value"]')
    await expect(ratingValue).toContainText('2.0')
  })
})
