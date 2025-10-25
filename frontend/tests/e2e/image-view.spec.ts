import { test, expect } from '@playwright/test';
import { handleMissingData } from './utils/testDataHelpers';

test.describe('Image View Page', () => {
  test('displays image details and metadata', async ({ page }) => {
    // Navigate to gallery to find an image
    await page.goto('/gallery');
    await expect(page).toHaveURL(/\/gallery/);

    // Wait for network to settle and page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Wait for gallery results to load (or empty state)
    const galleryResults = page.getByTestId('gallery-results-list');
    const emptyState = page.getByTestId('gallery-results-empty');

    // Check if we have results or empty state
    const hasResults = await galleryResults.isVisible().catch(() => false);
    const isEmpty = await emptyState.isVisible().catch(() => false);

    if (isEmpty || !hasResults) {
      handleMissingData(
        test,
        'Image view test',
        'gallery data (content_items)',
        'make init-test && python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      );
      return;
    }

    await expect(galleryResults).toBeVisible({ timeout: 5000 });

    // Find first image card and click it
    const firstImage = page.locator('[data-testid^="gallery-result-item-"]').first();
    await expect(firstImage).toBeVisible({ timeout: 5000 });
    await firstImage.click();

    // Verify we're on the view page
    await expect(page).toHaveURL(/\/view\/\d+/);

    // Verify page elements are present
    await expect(page.getByTestId('image-view-page')).toBeVisible();
    await expect(page.getByTestId('image-view-title')).toBeVisible();
    await expect(page.getByTestId('image-view-tags')).toBeVisible();
  });

  test('navigates to tag detail page when tag chip is clicked', async ({ page }) => {
    // Navigate to gallery
    await page.goto('/gallery');
    await expect(page).toHaveURL(/\/gallery/);

    // Wait for network to settle and page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Wait for gallery results to load (or empty state)
    const galleryResults = page.getByTestId('gallery-results-list');
    const emptyState = page.getByTestId('gallery-results-empty');

    // Check if we have results or empty state
    const hasResults = await galleryResults.isVisible().catch(() => false);
    const isEmpty = await emptyState.isVisible().catch(() => false);

    if (isEmpty || !hasResults) {
      handleMissingData(
        test,
        'Image view test',
        'gallery data (content_items)',
        'make init-test && python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      );
      return;
    }

    await expect(galleryResults).toBeVisible({ timeout: 5000 });

    // Find first image card and click it
    const firstImage = page.locator('[data-testid^="gallery-result-item-"]').first();
    await expect(firstImage).toBeVisible({ timeout: 5000 });
    await firstImage.click();

    // Verify we're on the view page
    await expect(page).toHaveURL(/\/view\/\d+/);

    // Find and click a tag chip (if tags exist)
    const tagsSection = page.getByTestId('image-view-tags');
    await expect(tagsSection).toBeVisible();

    // Check if there are tag chips
    const tagChip = page.locator('[data-testid^="image-view-tag-"]').first();

    // If tags exist, click and verify navigation
    if (await tagChip.count() > 0) {
      const tagText = await tagChip.textContent();
      await tagChip.click();

      // Verify we navigated to the tag detail page
      await expect(page).toHaveURL(/\/tags\/.+/);
      await expect(page.getByTestId('tag-detail-page')).toBeVisible();

      // Verify tag detail page shows the correct tag
      const tagTitle = page.getByTestId('tag-detail-title');
      await expect(tagTitle).toBeVisible();
      if (tagText) {
        await expect(tagTitle).toContainText(tagText);
      }
    }
  });

  test('back button returns to previous page', async ({ page }) => {
    // Navigate to gallery
    await page.goto('/gallery');
    await expect(page).toHaveURL(/\/gallery/);

    // Wait for network to settle and page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Wait for gallery results to load (or empty state)
    const galleryResults = page.getByTestId('gallery-results-list');
    const emptyState = page.getByTestId('gallery-results-empty');

    // Check if we have results or empty state
    const hasResults = await galleryResults.isVisible().catch(() => false);
    const isEmpty = await emptyState.isVisible().catch(() => false);

    if (isEmpty || !hasResults) {
      handleMissingData(
        test,
        'Image view test',
        'gallery data (content_items)',
        'make init-test && python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test'
      );
      return;
    }

    await expect(galleryResults).toBeVisible({ timeout: 5000 });

    // Find first image card and click it
    const firstImage = page.locator('[data-testid^="gallery-result-item-"]').first();
    await expect(firstImage).toBeVisible({ timeout: 5000 });
    await firstImage.click();

    // Verify we're on the view page
    await expect(page).toHaveURL(/\/view\/\d+/);

    // Click back button
    const backButton = page.getByTestId('image-view-back-button');
    await expect(backButton).toBeVisible();
    await backButton.click();

    // Verify we're back on the gallery page
    await expect(page).toHaveURL(/\/gallery/);
    await expect(galleryResults).toBeVisible();
  });
});
