import { test, expect } from '@playwright/test';
import { setupMockApi } from './utils/mockApi';
import { getCommonApiMocks } from './utils/mockData';

/**
 * E2E tests for Tag Rating functionality
 *
 * Tests rating submission, updates, deletion, and favorites
 */
test.describe('Tag Rating', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000);
    await setupMockApi(page, getCommonApiMocks());
  });

  test.skip('should allow user to rate a tag', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // Wait for ratings section
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]');

    // Should show star rating widget
    await expect(page.locator('[data-testid="star-rating-your-rating"]')).toBeVisible();

    // Click on a star to rate (e.g., 4th star)
    const stars = page.locator('[data-testid="star-rating-stars"] label');
    await stars.nth(3).click();

    // Should show saving indicator
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 2000 });

    // Wait for save to complete
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 });
  });

  test.skip('should update existing rating', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // User already has a rating
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]');

    // Change rating to different value
    const stars = page.locator('[data-testid="star-rating-stars"] label');
    await stars.nth(4).click();

    // Should update the rating
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 2000 });
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 });
  });

  test.skip('should display average rating from all users', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // Should show average rating with count
    await expect(page.locator('[data-testid="star-rating-average-rating"]')).toBeVisible();
    await expect(page.locator('text=/\\d+\\.\\d+ \\(\\d+ ratings?\\)/')).toBeVisible();
  });

  test.skip('should show half-star ratings', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]');

    // Average rating should support half stars (e.g., 4.5)
    const avgRating = page.locator('[data-testid="star-rating-average-rating"]');
    await expect(avgRating).toBeVisible();

    // The rating value should be displayed
    await expect(avgRating).toContainText(/\d+\.\d/);
  });
});

/**
 * E2E tests for Tag Favorites functionality
 *
 * Tests adding and removing favorite tags
 */
test.describe('Tag Favorites', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000);
    await setupMockApi(page, getCommonApiMocks());
  });

  test.skip('should add tag to favorites', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    // This feature may be implemented in a future phase
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // Click favorite button
    const favoriteButton = page.locator('[data-testid="tag-detail-favorite-button"]');
    await favoriteButton.click();

    // Should show as favorited
    await expect(favoriteButton).toHaveAttribute('aria-pressed', 'true');
  });

  test.skip('should remove tag from favorites', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    // This feature may be implemented in a future phase
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // Tag is already favorited
    const favoriteButton = page.locator('[data-testid="tag-detail-favorite-button"]');
    await expect(favoriteButton).toHaveAttribute('aria-pressed', 'true');

    // Click to unfavorite
    await favoriteButton.click();

    // Should no longer be favorited
    await expect(favoriteButton).toHaveAttribute('aria-pressed', 'false');
  });
});
