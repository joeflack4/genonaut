import { test, expect } from '@playwright/test';

test.describe('Tag Hierarchy Tests', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000);
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

  test('should expand and collapse tree nodes', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Find a root category with children and click to expand
    const artisticMediumNode = page.locator('text=Artistic Medium').first();
    await expect(artisticMediumNode).toBeVisible();

    // Click to expand (look for the expand button next to the node)
    await artisticMediumNode.click();

    // Wait a moment for expansion
    await page.waitForTimeout(500);

    // Should now see child categories under Artistic Medium
    // Based on the API data, these should include:
    await expect(page.locator('text=Artistic Methods')).toBeVisible();
    await expect(page.locator('text=Digital Techniques')).toBeVisible();
    await expect(page.locator('text=Traditional Materials')).toBeVisible();
  });

  test('should handle node selection and navigation', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Wait for tree to load
    await page.waitForSelector('[aria-label="Tag hierarchy tree"]');

    // Expand a category to see children
    const artisticMediumNode = page.locator('text=Artistic Medium').first();
    await artisticMediumNode.click();
    await page.waitForTimeout(500);

    // Click on a child node - this should navigate to gallery with tag filter
    const digitalTechniquesNode = page.locator('text=Digital Techniques').first();
    await digitalTechniquesNode.click();

    // Should navigate to gallery page with tag filter
    await expect(page).toHaveURL(/\/gallery\?tag=digital_techniques/);
  });

  test('should toggle between tree view and search mode', async ({ page }) => {
    await page.goto('/tags', { waitUntil: 'domcontentloaded' });

    // Should start in tree view mode
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible();
    await expect(page.locator('text=Browse Categories')).toBeVisible();

    // Click search toggle button
    const searchToggle = page.locator('button[aria-label*="search"], button:has-text("search"), [title*="search"]').first();
    await searchToggle.click();

    // Should now be in search mode
    await expect(page.locator('text=Search Tags')).toBeVisible();
    await expect(page.locator('input[placeholder*="Search for tags"]')).toBeVisible();

    // Tree view should be hidden
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).not.toBeVisible();

    // Toggle back to tree view
    const treeToggle = page.locator('button[aria-label*="tree"], button:has-text("tree"), [title*="tree"]').first();
    await treeToggle.click();

    // Should be back to tree view
    await expect(page.locator('[aria-label="Tag hierarchy tree"]')).toBeVisible();
    await expect(page.locator('text=Browse Categories')).toBeVisible();
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
});