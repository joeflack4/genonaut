import { test, expect } from '@playwright/test'

// Admin user ID (frontend always authenticates as admin)
const TEST_USER_ID = '121e194b-4caa-4b81-ad4f-86ca3919d5b9'

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
  })

  test.describe('Navigation & Basic Flow', () => {
    test('should navigate to bookmarks page via sidebar', async ({ page }) => {
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded', timeout: 10_000 })

      // Expand Gallery menu and click Bookmarks link (submenu item under Gallery)
      await page.click('[data-testid="app-layout-nav-link-gallery"]')
      await page.click('[data-testid="app-layout-nav-link-bookmarks"]')

      // Verify on bookmarks page
      await expect(page).toHaveURL('/bookmarks')
      await expect(page.locator('[data-testid="bookmarks-page-root"]')).toBeVisible({ timeout: 10000 })
      await expect(page.locator('[data-testid="bookmarks-page-title"]')).toHaveText('Bookmarks')
    })

    test('should display categories and bookmarks in grid layout', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'networkidle', timeout: 10_000 })

      // Wait for page root
      await expect(page.locator('[data-testid="bookmarks-page-root"]')).toBeVisible()

      // Wait for categories container and at least one category section within it
      // Use the categories container to scope our selector and avoid matching control elements
      const categoriesContainer = page.locator('[data-testid="bookmarks-page-categories"]')
      await expect(categoriesContainer).toBeVisible()

      // Get first non-Uncategorized category (Uncategorized hides edit button by design)
      // Find a category that has an edit button
      const categoryWithEditButton = categoriesContainer.locator('[data-testid$="-edit-button"]').first()
      await expect(categoryWithEditButton).toBeVisible()

      // Get the category ID from the edit button's data-testid
      const editButtonId = await categoryWithEditButton.getAttribute('data-testid')
      const categoryIdMatch = editButtonId?.match(/bookmarks-page-category-(.+)-edit-button/)
      const categoryId = categoryIdMatch?.[1]

      if (categoryId) {
        await expect(page.locator(`[data-testid="bookmarks-page-category-${categoryId}"]`)).toBeVisible()
        await expect(page.locator(`[data-testid="bookmarks-page-category-${categoryId}-name"]`)).toBeVisible()
        await expect(page.locator(`[data-testid="bookmarks-page-category-${categoryId}-public-toggle"]`)).toBeVisible()
      }
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
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
      await page.waitForTimeout(600)

      // Verify state changed
      const newState = await firstToggle.getAttribute('aria-label')
      expect(newState).not.toBe(initialState)
    })

    test('should open category edit modal', async ({ page }) => {
      await page.goto('/bookmarks', { waitUntil: 'networkidle', timeout: 10_000 })

      // Wait for categories container first
      const categoriesContainer = page.locator('[data-testid="bookmarks-page-categories"]')
      await expect(categoriesContainer).toBeVisible()

      // Find first category's edit button within categories (not from controls)
      const editButton = categoriesContainer.locator('[data-testid$="-edit-button"]').first()
      await expect(editButton).toBeVisible()
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
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
      await page.waitForTimeout(300)

      // Verify localStorage updated
      const categorySortData = await page.evaluate(() => {
        const stored = localStorage.getItem('bookmarks-category-sort')
        return stored ? JSON.parse(stored) : null
      })
      expect(categorySortData?.field).toBe('name')
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
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
      await page.waitForTimeout(300)

      // Verify localStorage updated
      const itemsSortData = await page.evaluate(() => {
        const stored = localStorage.getItem('bookmarks-items-sort')
        return stored ? JSON.parse(stored) : null
      })
      expect(itemsSortData?.field).toBe('quality_score')
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
      // Use admin user's "Favorites" category ID from bookmark_categories.tsv
      const categoryId = 'c864d743-990a-4ef3-90a9-3f8613ac749b'

      await page.goto(`/bookmarks/${categoryId}`, { waitUntil: 'networkidle', timeout: 10_000 })

      // Wait for page root and key elements (auto-waiting)
      await expect(page.locator('[data-testid="bookmarks-category-page-root"]')).toBeVisible()

      // Verify breadcrumbs (wait for them to appear)
      await expect(page.locator('[data-testid="bookmarks-category-page-breadcrumb-bookmarks"]')).toBeVisible()
      await expect(page.locator('[data-testid="bookmarks-category-page-breadcrumb-category"]')).toBeVisible()

      // Verify controls exist (auto-waiting)
      await expect(page.locator('[data-testid="bookmarks-category-page-resolution-dropdown"]')).toBeVisible()
      await expect(page.locator('[data-testid="bookmarks-category-page-items-per-page-select"]')).toBeVisible()
    })

    test('should navigate back via breadcrumbs', async ({ page }) => {
      const categoryId = 'c864d743-990a-4ef3-90a9-3f8613ac749b'
      await page.goto(`/bookmarks/${categoryId}`, { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Wait for page to load
      await page.waitForSelector('[data-testid="bookmarks-category-page-root"]', { timeout: 10000 })

      // Click Bookmarks breadcrumb
      await page.click('[data-testid="bookmarks-category-page-breadcrumb-bookmarks"]')

      // Verify back on main page
      await expect(page).toHaveURL('/bookmarks')
      await expect(page.locator('[data-testid="bookmarks-page-root"]')).toBeVisible()
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
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
      await page.waitForTimeout(200)

      // Change items per page to 20
      const itemsPerPageSelect = page.locator('[data-testid="bookmarks-page-items-per-page-select"]')
      await itemsPerPageSelect.click()
      await page.locator('li[data-value="20"]').click()
    // TODO: If this test fails, consider refactoring to use the Batched API Wait Pattern
    // instead of arbitrary waitForTimeout(). See docs/testing/e2e-network-wait-pattern.md
    // for details on waiting for actual API responses rather than guessing with fixed delays.
      await page.waitForTimeout(200)

      // Reload page
      await page.reload({ waitUntil: 'domcontentloaded' })

      // Wait for page to load
      await page.waitForSelector('[data-testid="bookmarks-page-root"]', { timeout: 10000 })

      // Verify preferences restored from localStorage
      const categorySortData = await page.evaluate(() => {
        const stored = localStorage.getItem('bookmarks-category-sort')
        return stored ? JSON.parse(stored) : null
      })
      const itemsPerPage = await page.evaluate(() => {
        const stored = localStorage.getItem('bookmarks-items-per-page')
        return stored ? JSON.parse(stored) : null
      })

      expect(categorySortData?.field).toBe('name')
      expect(itemsPerPage).toBe(20)
    })
  })

  test.describe('Error States', () => {
    test('should show 404 for missing category', async ({ page }) => {
      const invalidId = '00000000-0000-0000-0000-000000000000'
      await page.goto(`/bookmarks/${invalidId}`, { waitUntil: 'domcontentloaded', timeout: 5_000 })

      // Verify 404 or error state (use specific data-testid to avoid strict mode violations)
      const notFoundMsg = page.locator('[data-testid="bookmarks-category-page-not-found"]')

      await expect(notFoundMsg).toBeVisible({ timeout: 10000 })
    })
  })
})
