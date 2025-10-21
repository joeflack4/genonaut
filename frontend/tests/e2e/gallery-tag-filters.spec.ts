import { test, expect } from '@playwright/test';
import { setupMockApi } from './utils/mockApi';
import { getCommonApiMocks, getTagHierarchyMocks } from './utils/mockData';

test.describe('Gallery Tag Filters Tests', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000);
    await setupMockApi(page, [
      ...getCommonApiMocks(),
      ...getTagHierarchyMocks(),
    ]);
  });

  test('should display single tag filter in gallery', async ({ page }) => {
    // Navigate directly to gallery with a single tag
    await page.goto('/gallery?tags=Artistic Medium', { waitUntil: 'domcontentloaded' });

    // Should show the selected tag chip within the tag filter
    await expect(page.getByTestId('tag-filter-selected-artistic_medium')).toBeVisible();

    // Should show the clear all tags button
    await expect(page.getByTestId('tag-filter-clear-all-button')).toBeVisible();
  });

  test('should display multiple tag filters in gallery', async ({ page }) => {
    // Navigate directly to gallery with multiple tags (using actual tag names)
    await page.goto('/gallery?tags=Artistic Medium,Content Classification', { waitUntil: 'domcontentloaded' });

    // Should show both tags
    await expect(page.getByTestId('tag-filter-selected-artistic_medium')).toBeVisible();
    await expect(page.getByTestId('tag-filter-selected-content_classification')).toBeVisible();

    // Should show the clear all tags button
    await expect(page.getByTestId('tag-filter-clear-all-button')).toBeVisible();
  });

  test('should allow removing individual tags from gallery', async ({ page }) => {
    // Navigate directly to gallery with multiple tags
    await page.goto('/gallery?tags=Artistic Medium,Content Classification', { waitUntil: 'domcontentloaded' });

    // Should show both tags initially
    await expect(page.getByTestId('tag-filter-selected-artistic_medium')).toBeVisible();
    await expect(page.getByTestId('tag-filter-selected-content_classification')).toBeVisible();

    // Remove one tag by clicking its delete button
    const firstTagDelete = page.getByTestId('tag-filter-selected-artistic_medium-delete');
    await firstTagDelete.click();

    // Should still show the remaining tag chip
    await expect(page.getByTestId('tag-filter-selected-content_classification')).toBeVisible();

    // The removed tag should not be visible
    await expect(page.locator('[data-testid="tag-filter-selected-artistic_medium"]')).toHaveCount(0);

    // URL should be updated (using tag names, not IDs)
    await expect(page).toHaveURL('/gallery?tags=Content+Classification');
  });

  test('should clear all tags when clear all button is clicked', async ({ page }) => {
    // Navigate directly to gallery with multiple tags
    await page.goto('/gallery?tags=Artistic Medium,Content Classification', { waitUntil: 'domcontentloaded' });

    // Should show tag chips
    await expect(page.getByTestId('tag-filter-selected-artistic_medium')).toBeVisible();

    // Click clear all tags button
    await page.getByTestId('tag-filter-clear-all-button').click();

    // Tag filter display should disappear
    await expect(page.locator('[data-testid^="tag-filter-selected-"]')).toHaveCount(0);
    await expect(page.getByTestId('tag-filter-clear-all-button')).not.toBeVisible();

    // URL should be updated to remove tag parameters
    await expect(page).toHaveURL('/gallery');
  });

  test('should navigate from tag hierarchy to gallery with multiple tags', async ({ page }) => {
    // Start on tag hierarchy page
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Select multiple tags
    const firstTag = page.locator('text=Artistic Medium').first();
    await firstTag.click();

    const secondTag = page.locator('text=Content Classification').first();
    await secondTag.click();

    // Should show the apply button
    await expect(page.locator('button:has-text("Apply & Query")')).toBeVisible();

    // Click apply and query
    await page.locator('button:has-text("Apply & Query")').click();

    // Should navigate to gallery
    await expect(page).toHaveURL(/\/gallery\?.*tags=/);

    // Should show the selected tag chips and clear all button in gallery
    await expect(page.getByTestId('tag-filter-selected-artistic_medium')).toBeVisible();
    await expect(page.getByTestId('tag-filter-selected-content_classification')).toBeVisible();
    await expect(page.getByTestId('tag-filter-clear-all-button')).toBeVisible();
  });

  test('should maintain tag filters when navigating within gallery', async ({ page }) => {
    // Navigate to gallery with tags
    await page.goto('/gallery?tags=Artistic Medium,Content Classification', { waitUntil: 'domcontentloaded' });

    // Verify tag chips are shown
    await expect(page.getByTestId('tag-filter-selected-artistic_medium')).toBeVisible();
    await expect(page.getByTestId('tag-filter-selected-content_classification')).toBeVisible();

    // Navigate to a different page and back
    await page.goto('/tags');
    await page.goto('/gallery?tags=Artistic Medium,Content Classification');

    // Tag chips should still be shown
    await expect(page.getByTestId('tag-filter-selected-artistic_medium')).toBeVisible();
    await expect(page.getByTestId('tag-filter-selected-content_classification')).toBeVisible();
  });

  test('should show clear all tags button in tag hierarchy when tags are selected', async ({ page }) => {
    // Navigate to tag hierarchy page
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Clear all tags button should not be visible initially
    await expect(page.locator('button:has-text("Clear All Tags")')).not.toBeVisible();

    // Select a tag
    const tagNode = page.locator('text=Artistic Medium').first();
    await tagNode.click();

    // Clear all tags button should now be visible
    await expect(page.locator('button:has-text("Clear All Tags")')).toBeVisible();

    // Click clear all tags
    await page.locator('button:has-text("Clear All Tags")').click();

    // Apply buttons should disappear (since no tags are selected)
    await expect(page.locator('button:has-text("Apply & Query")')).not.toBeVisible();
    await expect(page.locator('button:has-text("Clear All Tags")')).not.toBeVisible();
  });
});
