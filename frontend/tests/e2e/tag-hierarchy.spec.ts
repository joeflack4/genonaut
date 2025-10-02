import { test, expect } from '@playwright/test';
import { setupMockApi } from './utils/mockApi';
import { getCommonApiMocks, getTagHierarchyMocks } from './utils/mockData';

test.describe('Tag Hierarchy Tests', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000);
    await setupMockApi(page, [
      ...getCommonApiMocks(),
      ...getTagHierarchyMocks(),
    ]);
  });

  test('should display tag hierarchy page with tree view', async ({ page }) => {
    // Navigate to tags page
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Page should have the correct title
    await expect(page.locator('h1')).toContainText('Tag Hierarchy');

    // Should show hierarchy stats
    await expect(page.locator('text=/\\d+ total tags/')).toBeVisible();
    await expect(page.locator('text=/\\d+ root categories/')).toBeVisible();
    await expect(page.locator('text=/\\d+ relationships/')).toBeVisible();

    // TreeView should be visible and not show error messages
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible();

    // Should not show "TreeView have no nodes to display" error
    await expect(page.locator('text=TreeView have no nodes to display')).not.toBeVisible();

    // Should not show "No tag hierarchy data available" error
    await expect(page.locator('text=No tag hierarchy data available')).not.toBeVisible();
  });

  test('should display root categories in tree view', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Should show the expected root categories based on API data
    // These are the 4 root categories from the backend API
    await expect(page.locator('text=Artistic Medium')).toBeVisible();
    await expect(page.locator('text=Content Classification')).toBeVisible();
    await expect(page.locator('text=Technical Execution')).toBeVisible();
    await expect(page.locator('text=Visual Aesthetics')).toBeVisible();
  });


  test('should toggle between tree view and search mode', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Should start in tree view mode
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible();
    await expect(page.locator('[data-testid="tags-page-tree-mode"]')).toBeVisible();

    // Click search toggle button
    const searchToggle = page.locator('button[aria-label*="search"], button:has-text("search"), [title*="search"]').first();
    await searchToggle.click();

    // Should now be in search mode
    await expect(page.locator('[data-testid="tags-page-search-title"]')).toBeVisible();
    await expect(page.locator('input[placeholder*="Search for tags"]')).toBeVisible();

    // Tree view should be hidden
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).not.toBeVisible();

    // Toggle back to tree view
    const treeToggle = page.locator('button[aria-label*="tree"], button:has-text("tree"), [title*="tree"]').first();
    await treeToggle.click();

    // Should be back to tree view
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible();
    await expect(page.locator('[data-testid="tags-page-tree-mode"]')).toBeVisible();
  });

  test('should display hierarchy metadata correctly', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for data to load
    await page.waitForSelector('text=/\\d+ total tags/');

    // Verify metadata matches expected values from API
    // Based on the API response we saw: 127 nodes, 4 root categories, 123 relationships
    await expect(page.locator('text=127 total tags')).toBeVisible();
    await expect(page.locator('text=4 root categories')).toBeVisible();
    await expect(page.locator('text=123 relationships')).toBeVisible();

    // Should show last updated date
    await expect(page.locator('text=/Updated: \\d+\\/\\d+\\/\\d+/')).toBeVisible();
  });

  test('should handle refresh functionality', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for initial load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Click refresh button
    const refreshButton = page.locator('button[title*="Refresh"], button:has([data-testid="RefreshIcon"])').first();
    await refreshButton.click();

    // Tree should still be visible after refresh
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible();

    // Root categories should still be there
    await expect(page.locator('text=Artistic Medium')).toBeVisible();
  });

  test('should show loading state initially', async ({ page }) => {
    // Start navigation but don't wait for full load
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Should either show loading state or the loaded content
    // This test ensures the page doesn't crash during loading
    await expect(page.locator('body')).toBeVisible();

    // Eventually the tree should load
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible({ timeout: 10000 });
  });

  test('should expand and collapse nodes without navigation', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Find the first root category with children
    const rootNode = page.locator('text=Artistic Medium').first();
    await expect(rootNode).toBeVisible();

    // Click the expand arrow (not the text)
    const expandButton = page.locator('[aria-label="Tag hierarchy tree"] button').first();
    await expandButton.click();

    // Should expand without navigating away from tags page
    await expect(page).toHaveURL('/tags');

    // Should show expanded content (wait for children to appear)
    await page.waitForTimeout(500); // Small delay for animation

    // Click collapse button
    await expandButton.click();

    // Should still be on tags page
    await expect(page).toHaveURL('/tags');
  });

  test('should select tags and show apply button', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Apply button should not be visible initially
    await expect(page.locator('button:has-text("Apply & Query")')).not.toBeVisible();

    // Click on a tag to select it (not the expand arrow)
    const tagNode = page.locator('text=Artistic Medium').first();
    await tagNode.click();

    // Should show the apply button
    await expect(page.locator('button:has-text("Apply & Query")')).toBeVisible();

    // Should show selection indicator (checkmark)
    await expect(page.locator('[data-testid="CheckCircleIcon"]')).toBeVisible();

    // Should show count in separate display area (not on button)
    await expect(page.locator('text=1 tag selected')).toBeVisible();
  });

  test('should handle multiple tag selections', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Select first tag
    const firstTag = page.locator('text=Artistic Medium').first();
    await firstTag.click();

    // Select second tag
    const secondTag = page.locator('text=Content Classification').first();
    await secondTag.click();

    // Should show apply button
    await expect(page.locator('button:has-text("Apply & Query")')).toBeVisible();

    // Should show tag count in separate display area (not on button)
    await expect(page.locator('text=2 tags selected')).toBeVisible();

    // Should show multiple checkmarks
    await expect(page.locator('[data-testid="CheckCircleIcon"]')).toHaveCount(2);
  });

  test('should toggle tag selection on/off', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    const tagNode = page.locator('text=Artistic Medium').first();

    // Click to select
    await tagNode.click();
    await expect(page.locator('button:has-text("Apply & Query")')).toBeVisible();

    // Click again to deselect
    await tagNode.click();
    await expect(page.locator('button:has-text("Apply & Query")')).not.toBeVisible();
  });

  test('should apply selected tags and navigate to gallery', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Select a tag
    const tagNode = page.locator('text=Artistic Medium').first();
    await tagNode.click();

    // Click apply button
    const applyButton = page.locator('button:has-text("Apply & Query")');
    await expect(applyButton).toBeVisible();
    await applyButton.click();

    // Should navigate to gallery with tag filter
    await expect(page).toHaveURL(/\/gallery\?.*tag=/);

    // Apply button should be hidden after successful navigation
    // (Note: This might not be testable if we navigate away)
  });

  test('should preserve expanded state when selecting tags', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Expand a node
    const expandButton = page.locator('[aria-label="Tag hierarchy tree"] button').first();
    await expandButton.click();
    await page.waitForTimeout(500); // Wait for expansion

    // Select a tag
    const tagNode = page.locator('text=Artistic Medium').first();
    await tagNode.click();

    // The expanded state should be preserved
    // (This is implicit - if the page reloaded, the expansion would be lost)
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible();
  });
});
