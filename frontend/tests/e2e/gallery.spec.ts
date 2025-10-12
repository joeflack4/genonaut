import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Gallery page', () => {
  // Gallery search test moved to search-filtering-real-api.spec.ts

  test.describe('Gallery Pagination', () => {
    test('displays correct total count and page navigation', async ({ page }) => {
      await setupMockApi(page, [
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
          body: {
            id: 1,
            name: 'Admin',
            email: 'admin@example.com',
            is_active: true,
          },
        },
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\u002Funified',
          body: {
            items: Array.from({ length: 25 }, (_, i) => ({
              id: i + 1,
              title: `Content Item ${i + 1}`,
              description: `Description ${i + 1}`,
              image_url: null,
              quality_score: 0.8,
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z',
              creator_id: '1',
            })),
            pagination: {
              page: 1,
              page_size: 25,
              total_count: 1175000,
              total_pages: 47000,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 233,
              user_auto_count: 523,
              community_regular_count: 65000,
              community_auto_count: 1110000,
            },
          },
        },
      ])

      await page.goto('/gallery')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Check that large total count is displayed
      await expect(page.getByText(/47,000 pages showing 1,175,000 results/)).toBeVisible()

      // Check pagination component shows correct page numbers
      await expect(page.getByRole('button', { name: 'page 1' })).toBeVisible()
      await expect(page.getByRole('button', { name: 'Go to page 2' })).toBeVisible()

      // Check next page button is enabled
      const nextButton = page.getByRole('button', { name: 'Go to next page' })
      await expect(nextButton).toBeEnabled()

      // Check previous page button is disabled on first page
      const prevButton = page.getByRole('button', { name: 'Go to previous page' })
      await expect(prevButton).toBeDisabled()
    })

    // Gallery pagination test moved to gallery-real-api.spec.ts

    test('content type toggles update pagination correctly', async ({ page }) => {
      await setupMockApi(page, [
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
          body: {
            id: 1,
            name: 'Admin',
            email: 'admin@example.com',
            is_active: true,
          },
        },
        // All content types enabled (new API with content_source_types)
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\u002Funified\\?.*content_source_types=user-regular.*content_source_types=user-auto.*content_source_types=community-regular.*content_source_types=community-auto',
          body: {
            items: Array.from({ length: 25 }, (_, i) => ({
              id: i + 1,
              title: `All Content ${i + 1}`,
              description: `Description ${i + 1}`,
              image_url: null,
              quality_score: 0.8,
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z',
              creator_id: '1',
            })),
            pagination: {
              page: 1,
              page_size: 25,
              total_count: 1175000,
              total_pages: 47000,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 233,
              user_auto_count: 523,
              community_regular_count: 65000,
              community_auto_count: 1110000,
            },
          },
        },
        // Only regular content (user-regular + community-regular)
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\u002Funified\\?.*content_source_types=user-regular.*content_source_types=community-regular',
          body: {
            items: Array.from({ length: 25 }, (_, i) => ({
              id: i + 1,
              title: `Regular Content ${i + 1}`,
              description: `Description ${i + 1}`,
              image_url: null,
              quality_score: 0.8,
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z',
              creator_id: '1',
            })),
            pagination: {
              page: 1,
              page_size: 25,
              total_count: 65233,
              total_pages: 2610,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 233,
              user_auto_count: 0,
              community_regular_count: 65000,
              community_auto_count: 0,
            },
          },
        },
      ])

      await page.goto('/gallery')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Check initial state with all content
      await expect(page.getByText(/47,000 pages showing 1,175,000 results/)).toBeVisible()

      // Check if options panel is already open (default behavior) or needs to be opened
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        // Options panel is closed, need to open it
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      // Wait for switches to be fully rendered and stable
      await page.waitForTimeout(1000)

      const yourAutoGenSwitch = page.getByTestId('gallery-toggle-your-autogens-label')
      const communityAutoGenSwitch = page.getByTestId('gallery-toggle-community-autogens-label')

      const yourAutoGenInput = yourAutoGenSwitch.locator('input[role="switch"]')
      const communityAutoGenInput = communityAutoGenSwitch.locator('input[role="switch"]')

      await expect(yourAutoGenInput).toBeVisible()
      await expect(communityAutoGenInput).toBeVisible()

      // Verify switches are checked before clicking (they should be checked initially)
      await expect(yourAutoGenInput).toBeChecked()
      await expect(communityAutoGenInput).toBeChecked()

      // Click to uncheck them via the label (material UI wraps the input)
      await yourAutoGenSwitch.click({ force: true })
      await communityAutoGenSwitch.click({ force: true })

      // Verify they are now unchecked
      await expect(yourAutoGenInput).not.toBeChecked()
      await expect(communityAutoGenInput).not.toBeChecked()

      // Check that pagination updated
      await expect(page.getByText(/2,610 pages showing 65,233 results/)).toBeVisible()
      await expect(page.getByText('Regular Content 1', { exact: true })).toBeVisible()
    })

    test('dashboard and gallery totals match', async ({ page }) => {
      await setupMockApi(page, [
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
          body: {
            id: 1,
            name: 'Admin',
            email: 'admin@example.com',
            is_active: true,
          },
        },
        // Unified stats API for dashboard
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\u002Fstats\\u002Funified',
          body: {
            user_regular_count: 233,
            user_auto_count: 523,
            community_regular_count: 65000,
            community_auto_count: 1110000,
          },
        },
        // Gallery unified API
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\u002Funified',
          body: {
            items: [],
            pagination: {
              page: 1,
              page_size: 25,
              total_count: 1175000,
              total_pages: 47000,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 233,
              user_auto_count: 523,
              community_regular_count: 65000,
              community_auto_count: 1110000,
            },
          },
        },
      ])

      // Check dashboard
      await page.goto('/dashboard')
      await page.waitForSelector('nav', { timeout: 20000 })

      await expect(page.getByText('233')).toBeVisible() // Your gens
      await expect(page.getByText('523')).toBeVisible() // Your auto-gens
      await expect(page.getByText('65,000')).toBeVisible() // Community gens
      await expect(page.getByText('1,110,000')).toBeVisible() // Community auto-gens

      // Check gallery
      await page.goto('/gallery')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Verify total count matches what the API returns
      await expect(page.getByText(/47,000 pages showing 1,175,000 results/)).toBeVisible()
    })

    // Large dataset pagination test moved to gallery-real-api-improved.spec.ts
  })
})
