import { test, expect } from '@playwright/test';
import { setupMockApi } from './utils/mockApi';
import { getCommonApiMocks, getTagHierarchyMocks } from './utils/mockData';

/**
 * E2E tests for Tag Detail Page
 *
 * Tests navigation, tag hierarchy display, ratings, and content browsing
 */
test.describe('Tag Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000);
    await setupMockApi(page, [
      ...getCommonApiMocks(),
      ...getTagHierarchyMocks(),
    ]);
  });

  test.skip('should load tag detail page correctly', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    // Navigate to a tag detail page
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // Should display tag name
    await expect(page.locator('[data-testid="tag-detail-title"]')).toBeVisible();

    // Should display back button
    await expect(page.locator('[data-testid="tag-detail-back-button"]')).toBeVisible();

    // Should display tag info card
    await expect(page.locator('[data-testid="tag-detail-info-card"]')).toBeVisible();
  });

  test.skip('should navigate through parent/child links', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    await page.goto('/tags/some-child-tag-id', { waitUntil: 'domcontentloaded' });

    // Wait for parent section
    await page.waitForSelector('[data-testid="tag-detail-parents-section"]');

    // Click on a parent tag
    const parentChip = page.locator('[data-testid^="tag-detail-parent-"]').first();
    const parentId = await parentChip.getAttribute('data-testid');

    if (parentId) {
      await parentChip.click();

      // Should navigate to parent tag detail page
      await expect(page).toHaveURL(/\/tags\/.+/);
      await expect(page.locator('[data-testid="tag-detail-title"]')).toBeVisible();
    }
  });

  test.skip('should display and toggle content browser', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // Content browser should be hidden initially
    await expect(page.locator('[data-testid="tag-detail-content-section"]')).not.toBeVisible();

    // Click browse button
    await page.locator('[data-testid="tag-detail-browse-button"]').click();

    // Content browser should be visible
    await expect(page.locator('[data-testid="tag-detail-content-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="tag-content-browser"]')).toBeVisible();

    // Click browse button again to hide
    await page.locator('[data-testid="tag-detail-browse-button"]').click();

    // Content browser should be hidden
    await expect(page.locator('[data-testid="tag-detail-content-section"]')).not.toBeVisible();
  });

  test.skip('should handle back button navigation', async ({ page }) => {
    // Note: This test is skipped until backend API endpoints are available
    await page.goto('/tags/some-tag-id', { waitUntil: 'domcontentloaded' });

    // Click back button
    await page.locator('[data-testid="tag-detail-back-button"]').click();

    // Should navigate back to tags page
    await expect(page).toHaveURL('/tags');
  });
});
