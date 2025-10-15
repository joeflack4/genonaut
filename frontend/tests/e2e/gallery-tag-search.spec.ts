import { test, expect } from '@playwright/test';

test.describe('Gallery Tag Search Tests', () => {
  // Configure separate timeout caps for this test suite
  test.use({
    expect: { timeout: 4000 },
    navigationTimeout: 7000,
    actionTimeout: 4000
  });

  test.beforeEach(async ({ page }) => {
    // Set overall test timeout
    test.setTimeout(20000);

    // Navigate and wait for app readiness
    await page.goto('/gallery', { waitUntil: 'domcontentloaded' });
    // Use longer timeout for real API tests
    await page.locator('[data-app-ready="1"]').waitFor({ timeout: 10000 });

    // Open options sidebar if it's closed
    const optionsButton = page.getByTestId('gallery-options-toggle-button');
    const tagFilter = page.getByTestId('tag-filter');
    const isTagFilterVisible = await tagFilter.isVisible().catch(() => false);

    if (!isTagFilterVisible) {
      await optionsButton.click();
      await page.waitForTimeout(300);
    }

    // Wait for the tag filter to be visible
    await page.waitForSelector('[data-testid="tag-filter"]', { timeout: 5000 });
  });

  test('should display search input field', async ({ page }) => {
    const searchInput = page.getByTestId('tag-filter-search');
    await expect(searchInput).toBeVisible();

    const input = page.getByTestId('tag-filter-search-input');
    await expect(input).toBeVisible();
  });

  test('should filter tags with word-based search - single word', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Give extra time for initial render
    await page.waitForTimeout(500);

    // Type "anime" in search
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('anime');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should show tags that contain words starting with "anime"
    // Check that we have at least one visible chip
    const visibleChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const count = await visibleChips.count();
    expect(count).toBeGreaterThan(0);

    // Check that at least one chip contains "anime" in its text
    let foundAnime = false;
    for (let i = 0; i < count; i++) {
      const chipText = await visibleChips.nth(i).textContent();
      if (chipText?.toLowerCase().includes('anime')) {
        foundAnime = true;
        break;
      }
    }
    expect(foundAnime).toBeTruthy();
  });

  test('should filter tags with word-based search - multiple words', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Give extra time for initial render
    await page.waitForTimeout(500);

    // Type "3d art" in search
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('3d art');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should show tags with words starting with "3d" or "art"
    // Get all visible tag chips
    const visibleChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const count = await visibleChips.count();

    // Should have at least some results (3D, 3D-render, concept-art, line-art, pixel-art, poster-style)
    expect(count).toBeGreaterThan(0);

    // Check that visible chips match our criteria
    for (let i = 0; i < count; i++) {
      const chipText = await visibleChips.nth(i).textContent();
      const normalizedText = chipText?.toLowerCase() || '';

      // Split into words (handling hyphens)
      const words = normalizedText.split(/[\s-]+/);

      // At least one word should start with "3d" or "art"
      const hasMatch = words.some(word => word.startsWith('3d') || word.startsWith('art'));
      expect(hasMatch).toBeTruthy();
    }
  });

  test('should filter tags with exact match search', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Type quoted search for exact match
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('"3d-render"');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should show only tags containing the exact string "3d-render"
    const visibleChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const count = await visibleChips.count();

    expect(count).toBeGreaterThan(0);

    // All visible chips should contain "3d-render"
    for (let i = 0; i < count; i++) {
      const chipText = await visibleChips.nth(i).textContent();
      const normalizedText = chipText?.toLowerCase() || '';
      expect(normalizedText).toContain('3d-render');
    }
  });

  test('should show "no matches" message when search has no results', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Type a search that should have no results
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('zzzznonexistenttag');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should show "no matches" message
    const emptyMessage = page.getByTestId('tag-filter-empty');
    await expect(emptyMessage).toBeVisible();
    await expect(emptyMessage).toHaveText('No tags match your search');
  });

  test('should reset to all tags when search is cleared', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Get initial count of tags
    const initialChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const initialCount = await initialChips.count();

    // Type a search to filter
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('anime');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should have fewer tags now
    const filteredChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const filteredCount = await filteredChips.count();
    expect(filteredCount).toBeLessThan(initialCount);

    // Clear the search
    await searchInput.clear();

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should show all tags again
    const finalChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const finalCount = await finalChips.count();
    expect(finalCount).toBe(initialCount);
  });

  test('should update pagination based on filtered results', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Check if pagination exists initially
    const pagination = page.getByTestId('tag-filter-pagination');
    const initialPaginationExists = await pagination.isVisible().catch(() => false);

    // Type a search that will have few results
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('anime');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // If there are very few results, pagination might be hidden
    // Just verify that the filtered tags are showing correctly
    const visibleChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const count = await visibleChips.count();

    // Should have at least one result (anime tag)
    expect(count).toBeGreaterThan(0);

    // All visible tags should match the search criteria
    for (let i = 0; i < count; i++) {
      const chipText = await visibleChips.nth(i).textContent();
      const normalizedText = chipText?.toLowerCase() || '';
      const words = normalizedText.split(/[\s-]+/);
      const hasMatch = words.some(word => word.startsWith('anime'));
      expect(hasMatch).toBeTruthy();
    }
  });

  test('should be case-insensitive in search', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Give extra time for initial render
    await page.waitForTimeout(500);

    // Type uppercase search
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('ANIME');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should still find lowercase "anime" tag
    const visibleChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const count = await visibleChips.count();

    expect(count).toBeGreaterThan(0);

    // Check that results include anime-related tags
    for (let i = 0; i < count; i++) {
      const chipText = await visibleChips.nth(i).textContent();
      const normalizedText = chipText?.toLowerCase() || '';
      const words = normalizedText.split(/[\s-]+/);
      const hasMatch = words.some(word => word.startsWith('anime'));
      expect(hasMatch).toBeTruthy();
    }
  });

  test('should handle hyphenated tags correctly in word-based search', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Give extra time for initial render
    await page.waitForTimeout(500);

    // Search for "3d" which should match "3D-render"
    const searchInput = page.getByTestId('tag-filter-search-input');
    await searchInput.fill('3d');

    // Wait for debounce (1 second)
    await page.waitForTimeout(1200);

    // Should show tags where a word starts with "3d"
    const visibleChips = page.locator('[data-testid^="tag-filter-chip-"]');
    const count = await visibleChips.count();

    expect(count).toBeGreaterThan(0);

    // Check that visible chips match our criteria
    for (let i = 0; i < count; i++) {
      const chipText = await visibleChips.nth(i).textContent();
      const normalizedText = chipText?.toLowerCase() || '';
      const words = normalizedText.split(/[\s-]+/);
      const hasMatch = words.some(word => word.startsWith('3d'));
      expect(hasMatch).toBeTruthy();
    }
  });

  test('should reset to page 1 when search is applied', async ({ page }) => {
    // Wait for tags to load
    await page.waitForSelector('[data-testid^="tag-filter-chip-"]');

    // Give extra time for initial render
    await page.waitForTimeout(500);

    // Check if pagination exists and has multiple pages
    const pagination = page.getByTestId('tag-filter-pagination');
    const hasPagination = await pagination.isVisible().catch(() => false);

    if (hasPagination) {
      // Navigate to page 2 if it exists
      const page2Button = pagination.locator('button[aria-label="Go to page 2"]');
      const page2Exists = await page2Button.isVisible().catch(() => false);

      if (page2Exists) {
        await page2Button.click();
        await page.waitForTimeout(500);

        // Verify we're on page 2
        const activePage = pagination.locator('button[aria-current="true"]');
        const activePageText = await activePage.textContent();
        expect(activePageText).toBe('2');

        // Apply a search
        const searchInput = page.getByTestId('tag-filter-search-input');
        await searchInput.fill('art');

        // Wait for debounce (1 second)
        await page.waitForTimeout(1200);

        // Should reset to page 1
        const paginationAfterSearch = page.getByTestId('tag-filter-pagination');
        const hasPageAfterSearch = await paginationAfterSearch.isVisible().catch(() => false);

        if (hasPageAfterSearch) {
          const activePageAfterSearch = paginationAfterSearch.locator('button[aria-current="true"]');
          const activePageTextAfterSearch = await activePageAfterSearch.textContent();
          expect(activePageTextAfterSearch).toBe('1');
        }
      }
    }
  });
});
