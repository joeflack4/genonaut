import { test, expect } from '@playwright/test';
import { setupMockApi } from './utils/mockApi';
import { getCommonApiMocks } from './utils/mockData';

/**
 * E2E tests for Tag Rating functionality (Real API)
 *
 * Tests rating submission, updates, and display using the real backend API
 */
test.describe('Tag Rating (Real API)', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000);
  });

  test('should allow user to rate a tag', async ({ page }) => {
    // Go to tags page with tree view
    await page.goto('/tags');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Wait for tree view to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]', { timeout: 10000 });

    // Find any clickable tag in the tree (look for TreeItem with button role)
    const treeItems = page.locator('[aria-label="Tag hierarchy tree"] [role="treeitem"]');
    const firstTag = treeItems.first();

    // Check if any tags exist
    if (await treeItems.count() === 0) {
      test.skip(true, 'No tags available in test database');
      return;
    }

    await firstTag.click();

    // Should navigate to tag detail page (now uses tag names instead of UUIDs)
    await page.waitForURL(/\/tags\/.+/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');

    // Wait for ratings section
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 });

    // Find the "Your Rating" star widget (not the average rating)
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]');
    const starWidgets = ratingsSection.locator('[data-testid="star-rating"]');

    // The second one should be "Your Rating"
    const yourRating = starWidgets.nth(1);
    await expect(yourRating).toBeVisible();

    // Click on the 4th star to rate
    const stars = yourRating.locator('[data-testid="star-rating-stars"]');
    const starLabels = stars.locator('label');
    await starLabels.nth(3).click();

    // Should show saving indicator
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 });

    // Wait for save to complete
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 });

    // Verify rating persists - the value should show "4.0"
    const ratingValue = yourRating.locator('[data-testid="star-rating-value"]');
    await expect(ratingValue).toContainText('4.0');
  });

  test('should update existing rating', async ({ page }) => {
    // Go to tags page with tree view
    await page.goto('/tags');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Wait for tree view to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]', { timeout: 10000 });

    // Find any clickable tag in the tree
    const treeItems = page.locator('[aria-label="Tag hierarchy tree"] [role="treeitem"]');
    const firstTag = treeItems.first();

    // Check if any tags exist
    if (await treeItems.count() === 0) {
      test.skip(true, 'No tags available in test database');
      return;
    }

    await firstTag.click();

    // Should navigate to tag detail page (now uses tag names instead of UUIDs)
    await page.waitForURL(/\/tags\/.+/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');

    // Wait for ratings section
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 });

    // Find "Your Rating" widget
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]');
    const yourRating = ratingsSection.locator('[data-testid="star-rating"]').nth(1);

    // Change rating to 5 stars
    const stars = yourRating.locator('[data-testid="star-rating-stars"]');
    const starLabels = stars.locator('label');
    await starLabels.nth(4).click();

    // Should show saving indicator
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 });

    // Verify rating updated to 5.0
    const ratingValue = yourRating.locator('[data-testid="star-rating-value"]');
    await expect(ratingValue).toContainText('5.0');
  });

  test('should persist rating across page refreshes', async ({ page }) => {
    // Go to tags page with tree view
    await page.goto('/tags');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Wait for tree view to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]', { timeout: 10000 });

    // Find any clickable tag in the tree
    const treeItems = page.locator('[aria-label="Tag hierarchy tree"] [role="treeitem"]');
    const firstTag = treeItems.first();

    // Check if any tags exist
    if (await treeItems.count() === 0) {
      test.skip(true, 'No tags available in test database');
      return;
    }

    await firstTag.click();

    // Navigate to tag detail page (now uses tag names instead of UUIDs)
    await page.waitForURL(/\/tags\/.+/, { timeout: 10000 });
    const tagUrl = page.url();

    // Wait for page load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 });

    // Rate the tag with 3 stars
    const ratingsSection = page.locator('[data-testid="tag-detail-ratings-section"]');
    const yourRating = ratingsSection.locator('[data-testid="star-rating"]').nth(1);
    const stars = yourRating.locator('[data-testid="star-rating-stars"]');
    await stars.locator('label').nth(2).click();

    // Wait for save
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=Saving...')).not.toBeVisible({ timeout: 5000 });

    // Verify rating shows 3.0
    let ratingValue = yourRating.locator('[data-testid="star-rating-value"]');
    await expect(ratingValue).toContainText('3.0');

    // Refresh the page
    await page.reload();
    await page.waitForLoadState('domcontentloaded');
    await page.waitForSelector('[data-testid="tag-detail-ratings-section"]', { timeout: 10000 });

    // Verify rating still shows 3.0 after refresh
    const yourRatingAfterRefresh = page.locator('[data-testid="tag-detail-ratings-section"]')
      .locator('[data-testid="star-rating"]').nth(1);
    ratingValue = yourRatingAfterRefresh.locator('[data-testid="star-rating-value"]');
    await expect(ratingValue).toContainText('3.0');
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
