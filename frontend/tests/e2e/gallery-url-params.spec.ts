import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

/**
 * Gallery URL Query Parameters Tests
 *
 * Tests the notGenSource URL parameter and its synchronization with UI toggles:
 * - URL params should initialize toggle states correctly
 * - Toggle changes should update URL params
 * - Browser back/forward should maintain toggle state
 */

test.describe('Gallery URL Query Parameters', () => {
  test.describe('notGenSource parameter initialization', () => {
    test('initializes toggles from URL with multiple disabled sources', async ({ page }) => {
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
            items: Array.from({ length: 10 }, (_, i) => ({
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
              total_count: 100,
              total_pages: 4,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 25,
              user_auto_count: 25,
              community_regular_count: 25,
              community_auto_count: 25,
            },
          },
        },
      ])

      // Navigate with notGenSource URL param
      await page.goto('/gallery?notGenSource=your-g,your-ag,comm-g')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      // Wait for switches to be fully rendered and stable
      await page.waitForTimeout(1000)

      // Get the switch labels, then find inputs inside them
      const yourGensLabel = page.getByTestId('gallery-toggle-your-gens-label')
      const yourAutoGensLabel = page.getByTestId('gallery-toggle-your-autogens-label')
      const communityGensLabel = page.getByTestId('gallery-toggle-community-gens-label')
      const communityAutoGensLabel = page.getByTestId('gallery-toggle-community-autogens-label')

      const yourGensToggle = yourGensLabel.locator('input[role="switch"]')
      const yourAutoGensToggle = yourAutoGensLabel.locator('input[role="switch"]')
      const communityGensToggle = communityGensLabel.locator('input[role="switch"]')
      const communityAutoGensToggle = communityAutoGensLabel.locator('input[role="switch"]')

      // Wait for toggles to be visible
      await expect(yourGensToggle).toBeVisible()
      await expect(yourAutoGensToggle).toBeVisible()
      await expect(communityGensToggle).toBeVisible()
      await expect(communityAutoGensToggle).toBeVisible()

      // These three should be OFF (disabled in URL)
      await expect(yourGensToggle).not.toBeChecked()
      await expect(yourAutoGensToggle).not.toBeChecked()
      await expect(communityGensToggle).not.toBeChecked()

      // This one should be ON (not in URL)
      await expect(communityAutoGensToggle).toBeChecked()
    })

    test('initializes all toggles ON when notGenSource is absent', async ({ page }) => {
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
            items: Array.from({ length: 10 }, (_, i) => ({
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
              total_count: 100,
              total_pages: 4,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 25,
              user_auto_count: 25,
              community_regular_count: 25,
              community_auto_count: 25,
            },
          },
        },
      ])

      // Navigate without notGenSource param
      await page.goto('/gallery')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      // Wait for switches to be fully rendered and stable
      await page.waitForTimeout(1000)

      // Get the switch labels, then find inputs inside them
      const yourGensLabel = page.getByTestId('gallery-toggle-your-gens-label')
      const yourAutoGensLabel = page.getByTestId('gallery-toggle-your-autogens-label')
      const communityGensLabel = page.getByTestId('gallery-toggle-community-gens-label')
      const communityAutoGensLabel = page.getByTestId('gallery-toggle-community-autogens-label')

      const yourGensToggle = yourGensLabel.locator('input[role="switch"]')
      const yourAutoGensToggle = yourAutoGensLabel.locator('input[role="switch"]')
      const communityGensToggle = communityGensLabel.locator('input[role="switch"]')
      const communityAutoGensToggle = communityAutoGensLabel.locator('input[role="switch"]')

      await expect(yourGensToggle).toBeVisible()
      await expect(yourGensToggle).toBeChecked()
      await expect(yourAutoGensToggle).toBeChecked()
      await expect(communityGensToggle).toBeChecked()
      await expect(communityAutoGensToggle).toBeChecked()

      // Verify URL has no notGenSource param
      const url = page.url()
      expect(url).not.toContain('notGenSource')
    })

    test('initializes single toggle OFF from URL', async ({ page }) => {
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
            items: Array.from({ length: 10 }, (_, i) => ({
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
              total_count: 75,
              total_pages: 3,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 0,
              user_auto_count: 25,
              community_regular_count: 25,
              community_auto_count: 25,
            },
          },
        },
      ])

      // Navigate with single disabled source
      await page.goto('/gallery?notGenSource=your-g')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      // Wait for switches to be fully rendered and stable
      await page.waitForTimeout(1000)

      // Get the switch labels, then find inputs inside them
      const yourGensLabel = page.getByTestId('gallery-toggle-your-gens-label')
      const yourAutoGensLabel = page.getByTestId('gallery-toggle-your-autogens-label')
      const communityGensLabel = page.getByTestId('gallery-toggle-community-gens-label')
      const communityAutoGensLabel = page.getByTestId('gallery-toggle-community-autogens-label')

      const yourGensToggle = yourGensLabel.locator('input[role="switch"]')
      const yourAutoGensToggle = yourAutoGensLabel.locator('input[role="switch"]')
      const communityGensToggle = communityGensLabel.locator('input[role="switch"]')
      const communityAutoGensToggle = communityAutoGensLabel.locator('input[role="switch"]')

      await expect(yourGensToggle).toBeVisible()
      await expect(yourGensToggle).not.toBeChecked()
      await expect(yourAutoGensToggle).toBeChecked()
      await expect(communityGensToggle).toBeChecked()
      await expect(communityAutoGensToggle).toBeChecked()
    })
  })

  test.describe('URL parameter updates from toggle changes', () => {
    test('updates URL when toggle is turned OFF', async ({ page }) => {
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
            items: Array.from({ length: 10 }, (_, i) => ({
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
              total_count: 100,
              total_pages: 4,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 25,
              user_auto_count: 25,
              community_regular_count: 25,
              community_auto_count: 25,
            },
          },
        },
      ])

      // Start with no URL params
      await page.goto('/gallery')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      // Wait for toggles to be stable
      await page.waitForTimeout(500)

      // Turn OFF "Your gens" toggle
      const yourGensToggleLabel = page.getByTestId('gallery-toggle-your-gens-label')
      await yourGensToggleLabel.click({ force: true })
      await page.waitForTimeout(500)

      // Verify URL now contains notGenSource=your-g
      const url = page.url()
      expect(url).toContain('notGenSource=your-g')
    })

    test('removes URL param when last disabled toggle is turned ON', async ({ page }) => {
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
            items: Array.from({ length: 10 }, (_, i) => ({
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
              total_count: 100,
              total_pages: 4,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 25,
              user_auto_count: 25,
              community_regular_count: 25,
              community_auto_count: 25,
            },
          },
        },
      ])

      // Start with URL param
      await page.goto('/gallery?notGenSource=your-g')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      // Wait for switches to be fully rendered and stable
      await page.waitForTimeout(1000)

      // Get the switch label, then find input inside it
      const yourGensLabel = page.getByTestId('gallery-toggle-your-gens-label')
      const yourGensToggle = yourGensLabel.locator('input[role="switch"]')

      await expect(yourGensToggle).toBeVisible()
      await expect(yourGensToggle).not.toBeChecked()

      // Turn it back ON
      const yourGensToggleLabel = page.getByTestId('gallery-toggle-your-gens-label')
      await yourGensToggleLabel.click({ force: true })
      await page.waitForTimeout(500)

      // Verify URL no longer contains notGenSource
      const url = page.url()
      expect(url).not.toContain('notGenSource')
    })

    test('updates URL with multiple disabled sources', async ({ page }) => {
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
            items: Array.from({ length: 10 }, (_, i) => ({
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
              total_count: 100,
              total_pages: 4,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 25,
              user_auto_count: 25,
              community_regular_count: 25,
              community_auto_count: 25,
            },
          },
        },
      ])

      // Start with no URL params
      await page.goto('/gallery')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      // Wait for toggles to be stable
      await page.waitForTimeout(500)

      // Turn OFF multiple toggles
      await page.getByTestId('gallery-toggle-your-gens-label').click({ force: true })
      await page.waitForTimeout(300)
      await page.getByTestId('gallery-toggle-your-autogens-label').click({ force: true })
      await page.waitForTimeout(300)
      await page.getByTestId('gallery-toggle-community-gens-label').click({ force: true })
      await page.waitForTimeout(500)

      // Verify URL contains all three disabled sources
      const url = page.url()
      expect(url).toContain('notGenSource=')
      expect(url).toContain('your-g')
      expect(url).toContain('your-ag')
      expect(url).toContain('comm-g')
    })
  })

  test.describe('URL parameter persistence with navigation', () => {
    test('maintains URL params when using browser back button', async ({ page }) => {
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
            items: Array.from({ length: 10 }, (_, i) => ({
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
              total_count: 100,
              total_pages: 4,
              has_next: true,
              has_previous: false,
            },
            stats: {
              user_regular_count: 25,
              user_auto_count: 25,
              community_regular_count: 25,
              community_auto_count: 25,
            },
          },
        },
      ])

      // Navigate with URL params
      await page.goto('/gallery?notGenSource=your-g,comm-ag')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Navigate to another page
      await page.goto('/dashboard')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Go back
      await page.goBack()
      await page.waitForSelector('nav', { timeout: 20000 })

      // Verify URL still has the same params
      const url = page.url()
      expect(url).toContain('notGenSource=your-g,comm-ag')

      // Open options panel if not already open
      const contentTypesSection = page.getByTestId('gallery-content-toggles-title')
      const isOptionsOpen = await contentTypesSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-content-toggles-title').waitFor({ state: 'visible' })
      }

      await page.waitForTimeout(1000)

      // Verify toggles still match - get labels then find inputs inside
      const yourGensLabel = page.getByTestId('gallery-toggle-your-gens-label')
      const communityAutoGensLabel = page.getByTestId('gallery-toggle-community-autogens-label')

      const yourGensToggle = yourGensLabel.locator('input[role="switch"]')
      const communityAutoGensToggle = communityAutoGensLabel.locator('input[role="switch"]')

      await expect(yourGensToggle).toBeVisible()
      await expect(yourGensToggle).not.toBeChecked()
      await expect(communityAutoGensToggle).not.toBeChecked()
    })
  })
})
