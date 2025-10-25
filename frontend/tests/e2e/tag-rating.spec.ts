/**
 * E2E tests for tag rating functionality
 * Tests the rating feature on tag detail pages
 */

import { test, expect } from '@playwright/test'
import { waitForPageLoad } from './utils/realApiHelpers'
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
    const sidebarToggle = page.getByTestId('gallery-sidebar-toggle')
    await sidebarToggle.click()
    await page.waitForTimeout(500)

    // Check if any tags are available in the sidebar
    const tagChips = page.locator('[data-testid^="gallery-tag-filter-chip-"]')
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

    // Click on the 4th star to rate
    const stars = yourRating.locator('[data-testid="star-rating-stars"]')
    const starLabels = stars.locator('label')
    await starLabels.nth(3).click()

    // Should show saving indicator
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 })

    // Wait for saving to complete
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 })

    // Verify the rating was applied (should show 4 stars filled)
    const filledStars = yourRating.locator('[data-testid="star-rating-filled"]')
    await expect(filledStars).toHaveCount(4)
  })

  test('should update existing rating', async ({ page }) => {
    // First, navigate to gallery to find available tags
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Open the sidebar to see available tags
    const sidebarToggle = page.getByTestId('gallery-sidebar-toggle')
    await sidebarToggle.click()
    await page.waitForTimeout(500)

    // Check if any tags are available in the sidebar
    const tagChips = page.locator('[data-testid^="gallery-tag-filter-chip-"]')
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

    // Find the "Your Rating" star widget
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]')
    const yourRating = ratingsSection.locator('[data-testid="star-rating"]').nth(1)

    // First set a rating of 3 stars
    const stars = yourRating.locator('[data-testid="star-rating-stars"]')
    const starLabels = stars.locator('label')
    await starLabels.nth(2).click() // 3rd star

    // Wait for save
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 })
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 })

    // Now update to 5 stars
    await starLabels.nth(4).click() // 5th star

    // Should show saving indicator again
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 })
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 })

    // Verify the rating was updated (should show 5 stars filled)
    const filledStars = yourRating.locator('[data-testid="star-rating-filled"]')
    await expect(filledStars).toHaveCount(5)
  })

  test('should persist rating across page refreshes', async ({ page }) => {
    // First, navigate to gallery to find available tags
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Open the sidebar to see available tags
    const sidebarToggle = page.getByTestId('gallery-sidebar-toggle')
    await sidebarToggle.click()
    await page.waitForTimeout(500)

    // Check if any tags are available in the sidebar
    const tagChips = page.locator('[data-testid^="gallery-tag-filter-chip-"]')
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

    // Find and rate the tag with 2 stars
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]')
    const yourRating = ratingsSection.locator('[data-testid="star-rating"]').nth(1)
    const stars = yourRating.locator('[data-testid="star-rating-stars"]')
    const starLabels = stars.locator('label')
    await starLabels.nth(1).click() // 2nd star

    // Wait for save
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 })
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 })

    // Verify initial rating
    let filledStars = yourRating.locator('[data-testid="star-rating-filled"]')
    await expect(filledStars).toHaveCount(2)

    // Refresh the page
    await page.reload()
    await waitForPageLoad(page, 'tagDetail')

    // Wait for ratings section to load again
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 })

    // Verify the rating persisted
    const ratingSectionAfter = page.locator('[data-testid="tag-detail-ratings-section"]')
    const yourRatingAfter = ratingSectionAfter.locator('[data-testid="star-rating"]').nth(1)
    filledStars = yourRatingAfter.locator('[data-testid="star-rating-filled"]')
    await expect(filledStars).toHaveCount(2)
  })
})