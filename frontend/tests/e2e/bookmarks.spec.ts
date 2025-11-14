import { test, expect } from '@playwright/test'

// Test user from bookmarks test data (aandersen)
const TEST_USER_ID = 'a04237b8-f14e-4fed-9427-576c780d6e2a'

test.describe('Bookmarks Feature - Real API', () => {
  test.beforeEach(async ({ page }) => {
    // Set up authentication for test user (aandersen) who has bookmark test data
    await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 10_000 })

    // Set user_id in localStorage and cookie for auth
    await page.context().addCookies([{
      name: 'user_id',
      value: TEST_USER_ID,
      domain: 'localhost',
      path: '/'
    }])

    await page.evaluate((userId) => {
      window.localStorage.setItem('user_id', userId)
      window.localStorage.setItem('authenticated', 'true')
    }, TEST_USER_ID)

    // Wait for app to be ready (critical data loaded)
    await page.locator('[data-app-ready="1"]').waitFor({ timeout: 15000 })
  })

  test.describe('Navigation & Basic Flow', () => {
    test('should navigate to bookmarks page via sidebar', async ({ page }) => {
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded', timeout: 10_000 })

      // Click Bookmarks link (top-level nav item)
      await page.click('[data-testid="app-layout-nav-link-bookmarks"]')

      // Verify on bookmarks page
      await expect(page).toHaveURL('/bookmarks')
      await expect(page.locator('[data-testid="bookmarks-page-root"]')).toBeVisible({ timeout: 10000 })
      await expect(page.locator('[data-testid="bookmarks-page-title"]')).toHaveText('Bookmarks')
    })

    test('should display categories and bookmarks in grid layout', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for page to load
      await page.waitForSelector('[data-testid="bookmarks-page-root"]')

      // Check for category sections (at least 1 should exist with test data)
      const categorySections = page.locator('[data-testid^="bookmarks-page-category-"]')
      await expect(categorySections.first()).toBeVisible({ timeout: 10000 })

      // Verify category section has required elements
      const firstCategory = categorySections.first()
      await expect(firstCategory.locator('[data-testid$="-name"]')).toBeVisible()
      await expect(firstCategory.locator('[data-testid$="-edit-button"]')).toBeVisible()
      await expect(firstCategory.locator('[data-testid$="-public-toggle"]')).toBeVisible()
    })
  })

  test.describe('Category Management', () => {
    test('should toggle category public status with debounce', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for categories to load
      await page.waitForSelector('[data-testid^="bookmarks-page-category-"]', { timeout: 10000 })

      // Get the first category's public toggle
      const firstToggle = page.locator('[data-testid$="-public-toggle"]').first()
      await firstToggle.waitFor({ state: 'visible' })

      // Get initial state (check aria-label or icon)
      const initialState = await firstToggle.getAttribute('aria-label')

      // Click toggle
      await firstToggle.click()

      // Wait for debounce (500ms)
      await page.waitForTimeout(600)

      // Verify state changed
      const newState = await firstToggle.getAttribute('aria-label')
      expect(newState).not.toBe(initialState)
    })

    test('should open category edit modal', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for categories
      await page.waitForSelector('[data-testid^="bookmarks-page-category-"]', { timeout: 10000 })

      // Click edit button on first category
      const editButton = page.locator('[data-testid$="-edit-button"]').first()
      await editButton.click()

      // Verify modal opens
      const modal = page.locator('[data-testid="bookmarks-page-category-modal-root"]')
      await expect(modal).toBeVisible()

      // Verify form fields exist
      await expect(page.locator('[data-testid="bookmarks-page-category-modal-name-input"]')).toBeVisible()
      await expect(page.locator('[data-testid="bookmarks-page-category-modal-description-input"]')).toBeVisible()

      // Close modal
      const cancelButton = page.locator('[data-testid="bookmarks-page-category-modal-cancel-button"]')
      await cancelButton.click()

      // Verify modal closed
      await expect(modal).not.toBeVisible()
    })
  })

  test.describe('Sorting & Filtering', () => {
    test('should change category sort order', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for page to load
      await page.waitForSelector('[data-testid="bookmarks-page-category-sort-select"]', { timeout: 10000 })

      // Change to alphabetical sort
      const sortSelect = page.locator('[data-testid="bookmarks-page-category-sort-select"]')
      await sortSelect.click()

      // Select 'name' option from dropdown
      const nameOption = page.locator('li[data-value="name"]')
      await nameOption.click()

      // Wait for re-render
      await page.waitForTimeout(300)

      // Verify localStorage updated
      const categorySortOrder = await page.evaluate(() => {
        return localStorage.getItem('bookmarks-category-sort-field')
      })
      expect(categorySortOrder).toBe('name')
    })

    test('should change items sort order', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for items sort select
      await page.waitForSelector('[data-testid="bookmarks-page-items-sort-select"]', { timeout: 10000 })

      // Change to quality_score sort
      const sortSelect = page.locator('[data-testid="bookmarks-page-items-sort-select"]')
      await sortSelect.click()

      const qualityOption = page.locator('li[data-value="quality_score"]')
      await qualityOption.click()

      // Wait for re-render
      await page.waitForTimeout(300)

      // Verify localStorage updated
      const itemsSortField = await page.evaluate(() => {
        return localStorage.getItem('bookmarks-items-sort-field')
      })
      expect(itemsSortField).toBe('quality_score')
    })

    test('should adjust items per page', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for items per page select
      await page.waitForSelector('[data-testid="bookmarks-page-items-per-page-select"]', { timeout: 10000 })

      // Change to 25 items per page
      const perPageSelect = page.locator('[data-testid="bookmarks-page-items-per-page-select"]')
      await perPageSelect.click()

      const option25 = page.locator('li[data-value="25"]')
      await option25.click()

      // Verify localStorage updated
      const itemsPerPage = await page.evaluate(() => {
        return JSON.parse(localStorage.getItem('bookmarks-items-per-page') || '15')
      })
      expect(itemsPerPage).toBe(25)
    })
  })

  test.describe('Navigation to Category Page', () => {
    test('should navigate to category page via More cell', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for categories to load
      await page.waitForSelector('[data-testid^="bookmarks-page-category-"]', { timeout: 10000 })

      // Find a More cell (only visible if category has >N items)
      const moreCell = page.locator('[data-testid$="-more-cell"]').first()

      if (await moreCell.isVisible()) {
        await moreCell.click()

        // Verify on category page
        await expect(page).toHaveURL(/\/bookmarks\/[a-f0-9-]+/)
        await expect(page.locator('[data-testid="bookmarks-category-page-root"]')).toBeVisible()
      } else {
        // Skip test if no categories have enough items for More cell
        test.skip()
      }
    })
  })

  test.describe('Single Category Page', () => {
    test('should access category page directly and display content', async ({ page }) => {
      // Use test data category ID from bookmark_categories.tsv - "Favorites"
      const categoryId = 'b3f5e8d2-4c5a-4d3e-9f2b-1a8c7e6d5f4a'

      await page.goto(`/bookmarks/${categoryId}`, { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Verify page loaded
      await expect(page.locator('[data-testid="bookmarks-category-page-root"]')).toBeVisible({ timeout: 10000 })

      // Verify breadcrumbs
      await expect(page.locator('[data-testid="bookmarks-category-page-breadcrumb-bookmarks"]')).toBeVisible()
      await expect(page.locator('[data-testid="bookmarks-category-page-breadcrumb-category"]')).toBeVisible()

      // Verify controls exist
      await expect(page.locator('[data-testid="bookmarks-category-page-resolution-dropdown"]')).toBeVisible()
      await expect(page.locator('[data-testid="bookmarks-category-page-items-per-page-select"]')).toBeVisible()
    })

    test('should navigate back via breadcrumbs', async ({ page }) => {
      const categoryId = 'b3f5e8d2-4c5a-4d3e-9f2b-1a8c7e6d5f4a'
      await page.goto(`/bookmarks/${categoryId}`, { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for page to load
      await page.waitForSelector('[data-testid="bookmarks-category-page-root"]', { timeout: 10000 })

      // Click Bookmarks breadcrumb
      await page.click('[data-testid="bookmarks-category-page-breadcrumb-bookmarks"]')

      // Verify back on main page
      await expect(page).toHaveURL('/bookmarks')
      await expect(page.locator('[data-testid="bookmarks-page-root"]')).toBeVisible()
    })

    test('should change grid resolution', async ({ page }) => {
      const categoryId = 'b3f5e8d2-4c5a-4d3e-9f2b-1a8c7e6d5f4a'
      await page.goto(`/bookmarks/${categoryId}`, { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for page
      await page.waitForSelector('[data-testid="bookmarks-category-page-root"]', { timeout: 10000 })

      // Open resolution dropdown
      const resolutionDropdown = page.locator('[data-testid="bookmarks-category-page-resolution-dropdown"]')
      await resolutionDropdown.click()

      // Select larger size (512x768)
      const option512 = page.getByRole('menuitem', { name: '512x768' })
      if (await option512.isVisible()) {
        await option512.click()

        // Verify localStorage updated
        const resolution = await page.evaluate(() => {
          return JSON.parse(localStorage.getItem('bookmarks-category-page-resolution') || '"184x272"')
        })
        expect(resolution).toBe('512x768')
      }
    })
  })

  test.describe('Persistence', () => {
    test('should persist sort preferences after reload', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for page
      await page.waitForSelector('[data-testid="bookmarks-page-category-sort-select"]', { timeout: 10000 })

      // Change category sort to 'name'
      const categorySortSelect = page.locator('[data-testid="bookmarks-page-category-sort-select"]')
      await categorySortSelect.click()
      await page.locator('li[data-value="name"]').click()
      await page.waitForTimeout(200)

      // Change items per page to 20
      const itemsPerPageSelect = page.locator('[data-testid="bookmarks-page-items-per-page-select"]')
      await itemsPerPageSelect.click()
      await page.locator('li[data-value="20"]').click()
      await page.waitForTimeout(200)

      // Reload page
      await page.reload({ waitUntil: 'domcontentloaded' })

      // Wait for page to load
      await page.waitForSelector('[data-testid="bookmarks-page-root"]', { timeout: 10000 })

      // Verify preferences restored from localStorage
      const categorySortField = await page.evaluate(() => {
        return localStorage.getItem('bookmarks-category-sort-field')
      })
      const itemsPerPage = await page.evaluate(() => {
        return localStorage.getItem('bookmarks-items-per-page')
      })

      expect(categorySortField).toBe('name')
      expect(itemsPerPage).toBe('20')
    })
  })

  test.describe('Error States', () => {
    test('should show 404 for missing category', async ({ page }) => {
      const invalidId = '00000000-0000-0000-0000-000000000000'
      await page.goto(`/bookmarks/${invalidId}`, { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Verify 404 or error state
      const notFoundMsg = page.locator('[data-testid="bookmarks-category-page-not-found"]')
      const errorMsg = page.getByText(/Category not found|not found|404/i)

      // At least one should be visible
      await expect(notFoundMsg.or(errorMsg)).toBeVisible({ timeout: 10000 })
    })
  })
})
