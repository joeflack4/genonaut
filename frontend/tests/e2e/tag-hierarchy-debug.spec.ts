import { test, expect } from '@playwright/test';

test.describe('Tag Hierarchy Debug', () => {
  test('should debug tags page loading with network monitoring', async ({ page }) => {
    // Track network requests
    const requests: any[] = [];
    const responses: any[] = [];

    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method(),
        headers: request.headers()
      });
      console.log('REQUEST:', request.method(), request.url());
    });

    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText()
      });
      console.log('RESPONSE:', response.status(), response.url());
    });

    // Log console messages
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

    console.log('Navigating to /tags...');
    await page.goto('/tags', { waitUntil: 'networkidle' });

    console.log('Current URL:', page.url());

    // Wait a bit for React to render and API calls
    await page.waitForTimeout(5000);

    // Check API requests
    const apiRequests = requests.filter(req => req.url.includes('/api/v1/tags/hierarchy'));
    console.log('API requests made:', apiRequests.length);

    for (const req of apiRequests) {
      console.log('API Request:', req.method, req.url);
    }

    const apiResponses = responses.filter(res => res.url.includes('/api/v1/tags/hierarchy'));
    console.log('API responses received:', apiResponses.length);

    for (const res of apiResponses) {
      console.log('API Response:', res.status, res.statusText, res.url);
    }

    // Check what's actually on the page
    const bodyContent = await page.locator('body').innerHTML();
    console.log('Body content length:', bodyContent.length);

    // Look for specific elements
    const hierarchyTitle = await page.locator('h1:has-text("Tag Hierarchy")').count();
    console.log('Tag Hierarchy title found:', hierarchyTitle);

    const treeElement = await page.locator('[aria-label="Tag hierarchy tree"]').count();
    console.log('Tree element found:', treeElement);

    const virtualRoot = await page.locator('text=Tag Categories').count();
    console.log('Virtual root "Tag Categories" found:', virtualRoot);

    const artisticMedium = await page.locator('text=Artistic Medium').count();
    console.log('Artistic Medium found:', artisticMedium);

    // Check for loading states
    const loadingElements = await page.locator('*:has-text("loading"), *:has-text("Loading")').all();
    console.log('Loading elements found:', loadingElements.length);

    // Check for any React Query error states
    const reactQueryStates = await page.locator('*').evaluateAll(elements => {
      return elements.map(el => el.textContent).filter(text =>
        text && (text.includes('failed') || text.includes('error') || text.includes('retry'))
      );
    });
    // console.log('React Query error indicators:', reactQueryStates);  // very verbose

    // Get the debug panel content to see the exact data structure (if it exists)
    try {
      const debugPanel = await page.locator('*:has-text("🐛 DEBUG TreeView:")').first();
      const debugText = await debugPanel.textContent({ timeout: 1000 });
      console.log('DEBUG PANEL CONTENT:', debugText);
    } catch (error) {
      console.log('No debug panel found (this is expected in production)');
    }

    // Basic assertion that the page loads something
    await expect(page.locator('body')).not.toBeEmpty();
  });
});