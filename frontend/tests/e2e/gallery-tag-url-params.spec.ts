import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

/**
 * Gallery Tag URL Parameters Tests
 *
 * Tests the tags URL parameter (comma-delimited tag names) and its synchronization with UI:
 * - URL params should initialize tag selection correctly
 * - Tag selection changes should update URL params
 * - Browser back/forward should maintain tag selection state
 */

// Mock tag data
const mockTags = [
  {
    id: 'uuid-nature-123',
    name: 'nature',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    average_rating: 4.5,
    rating_count: 10,
  },
  {
    id: 'uuid-landscape-456',
    name: 'landscape',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    average_rating: 4.2,
    rating_count: 8,
  },
  {
    id: 'uuid-sunset-789',
    name: 'sunset',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    average_rating: 4.8,
    rating_count: 15,
  },
  {
    id: 'uuid-ocean-101',
    name: 'ocean',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    average_rating: 4.3,
    rating_count: 12,
  },
]

test.describe('Gallery Tag URL Parameters', () => {
  test.describe('tags parameter initialization', () => {
    test('initializes tag selection from URL with single tag name', async ({ page }) => {
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
          pattern: '\\u002Fapi\\u002Fv1\\u002Ftags',
          body: {
            items: mockTags,
            pagination: {
              page: 1,
              page_size: 100,
              total_count: mockTags.length,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
          },
        },
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\u002Funified',
          body: {
            items: Array.from({ length: 5 }, (_, i) => ({
              id: i + 1,
              title: `Nature Content ${i + 1}`,
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
              total_count: 5,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
            stats: {
              user_regular_count: 2,
              user_auto_count: 1,
              community_regular_count: 1,
              community_auto_count: 1,
            },
          },
        },
      ])

      // Navigate with tags URL param (single tag)
      await page.goto('/gallery?tags=nature')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const tagFilterSection = page.getByTestId('gallery-tag-filter-title')
      const isOptionsOpen = await tagFilterSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-tag-filter-title').waitFor({ state: 'visible' })
      }

      // Wait for tag filter to load
      await page.waitForTimeout(1000)

      // Check that the nature tag is selected (appears in selected tags section)
      const selectedTagsSection = page.getByTestId('tag-filter-selected')
      await expect(selectedTagsSection).toBeVisible()

      const selectedNatureTag = page.getByTestId('tag-filter-selected-uuid-nature-123')
      await expect(selectedNatureTag).toBeVisible()
      await expect(selectedNatureTag).toContainText('nature')
    })

    test('initializes tag selection from URL with multiple tag names', async ({ page }) => {
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
          pattern: '\\u002Fapi\\u002Fv1\\u002Ftags',
          body: {
            items: mockTags,
            pagination: {
              page: 1,
              page_size: 100,
              total_count: mockTags.length,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
          },
        },
        {
          pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\u002Funified',
          body: {
            items: Array.from({ length: 3 }, (_, i) => ({
              id: i + 1,
              title: `Landscape Sunset Content ${i + 1}`,
              description: `Description ${i + 1}`,
              image_url: null,
              quality_score: 0.9,
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z',
              creator_id: '1',
            })),
            pagination: {
              page: 1,
              page_size: 25,
              total_count: 3,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
            stats: {
              user_regular_count: 1,
              user_auto_count: 1,
              community_regular_count: 1,
              community_auto_count: 0,
            },
          },
        },
      ])

      // Navigate with tags URL param (multiple tags)
      await page.goto('/gallery?tags=landscape,sunset')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const tagFilterSection = page.getByTestId('gallery-tag-filter-title')
      const isOptionsOpen = await tagFilterSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-tag-filter-title').waitFor({ state: 'visible' })
      }

      // Wait for tag filter to load
      await page.waitForTimeout(1000)

      // Check that both tags are selected
      const selectedTagsSection = page.getByTestId('tag-filter-selected')
      await expect(selectedTagsSection).toBeVisible()

      const selectedLandscapeTag = page.getByTestId('tag-filter-selected-uuid-landscape-456')
      await expect(selectedLandscapeTag).toBeVisible()
      await expect(selectedLandscapeTag).toContainText('landscape')

      const selectedSunsetTag = page.getByTestId('tag-filter-selected-uuid-sunset-789')
      await expect(selectedSunsetTag).toBeVisible()
      await expect(selectedSunsetTag).toContainText('sunset')
    })

    test('shows no selected tags when tags parameter is absent', async ({ page }) => {
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
          pattern: '\\u002Fapi\\u002Fv1\\u002Ftags',
          body: {
            items: mockTags,
            pagination: {
              page: 1,
              page_size: 100,
              total_count: mockTags.length,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
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

      // Navigate without tags param
      await page.goto('/gallery')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const tagFilterSection = page.getByTestId('gallery-tag-filter-title')
      const isOptionsOpen = await tagFilterSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-tag-filter-title').waitFor({ state: 'visible' })
      }

      // Wait for tag filter to load
      await page.waitForTimeout(1000)

      // Verify no selected tags section is visible
      const selectedTagsSection = page.getByTestId('tag-filter-selected')
      await expect(selectedTagsSection).not.toBeVisible()

      // Verify URL has no tags param
      const url = page.url()
      expect(url).not.toContain('tags=')
    })
  })

  test.describe('URL parameter updates from tag selection', () => {
    test('updates URL when a tag is selected', async ({ page }) => {
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
          pattern: '\\u002Fapi\\u002Fv1\\u002Ftags',
          body: {
            items: mockTags,
            pagination: {
              page: 1,
              page_size: 100,
              total_count: mockTags.length,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
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
      const tagFilterSection = page.getByTestId('gallery-tag-filter-title')
      const isOptionsOpen = await tagFilterSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-tag-filter-title').waitFor({ state: 'visible' })
      }

      // Wait for tags to load
      await page.waitForTimeout(1000)

      // Select the "nature" tag
      const natureTagChip = page.getByTestId('tag-filter-chip-uuid-nature-123')
      await natureTagChip.click({ force: true })
      await page.waitForTimeout(500)

      // Verify URL now contains tags=nature
      const url = page.url()
      expect(url).toContain('tags=nature')
    })

    test('updates URL with multiple comma-delimited tag names', async ({ page }) => {
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
          pattern: '\\u002Fapi\\u002Fv1\\u002Ftags',
          body: {
            items: mockTags,
            pagination: {
              page: 1,
              page_size: 100,
              total_count: mockTags.length,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
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
      const tagFilterSection = page.getByTestId('gallery-tag-filter-title')
      const isOptionsOpen = await tagFilterSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-tag-filter-title').waitFor({ state: 'visible' })
      }

      // Wait for tags to load
      await page.waitForTimeout(1000)

      // Select multiple tags
      await page.getByTestId('tag-filter-chip-uuid-landscape-456').click({ force: true })
      await page.waitForTimeout(300)
      await page.getByTestId('tag-filter-chip-uuid-ocean-101').click({ force: true })
      await page.waitForTimeout(500)

      // Verify URL contains both tag names comma-delimited
      const url = page.url()
      expect(url).toContain('tags=')
      expect(url).toContain('landscape')
      expect(url).toContain('ocean')
    })

    test('removes tags param when all tags are deselected', async ({ page }) => {
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
          pattern: '\\u002Fapi\\u002Fv1\\u002Ftags',
          body: {
            items: mockTags,
            pagination: {
              page: 1,
              page_size: 100,
              total_count: mockTags.length,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
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

      // Start with a tag selected in URL
      await page.goto('/gallery?tags=nature')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Open options panel if not already open
      const tagFilterSection = page.getByTestId('gallery-tag-filter-title')
      const isOptionsOpen = await tagFilterSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-tag-filter-title').waitFor({ state: 'visible' })
      }

      // Wait for tags to load and verify nature tag is selected
      await page.waitForTimeout(1000)
      const selectedNatureTag = page.getByTestId('tag-filter-selected-uuid-nature-123')
      await expect(selectedNatureTag).toBeVisible()

      // Click the delete button on the selected tag to remove it
      const deleteButton = selectedNatureTag.getByTestId('tag-filter-selected-uuid-nature-123-delete')
      await deleteButton.click({ force: true })
      await page.waitForTimeout(500)

      // Verify URL no longer contains tags param
      const url = page.url()
      expect(url).not.toContain('tags=')
    })
  })

  test.describe('URL parameter persistence with navigation', () => {
    test('maintains tag URL params when using browser back button', async ({ page }) => {
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
          pattern: '\\u002Fapi\\u002Fv1\\u002Ftags',
          body: {
            items: mockTags,
            pagination: {
              page: 1,
              page_size: 100,
              total_count: mockTags.length,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
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

      // Navigate with tags URL param
      await page.goto('/gallery?tags=landscape,sunset')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Navigate to another page
      await page.goto('/dashboard')
      await page.waitForSelector('nav', { timeout: 20000 })

      // Go back
      await page.goBack()
      await page.waitForSelector('nav', { timeout: 20000 })

      // Verify URL still has the same params
      const url = page.url()
      expect(url).toContain('tags=landscape,sunset')

      // Open options panel if not already open
      const tagFilterSection = page.getByTestId('gallery-tag-filter-title')
      const isOptionsOpen = await tagFilterSection.isVisible().catch(() => false)

      if (!isOptionsOpen) {
        const optionsButton = page.getByTestId('gallery-options-toggle-button')
        await optionsButton.click({ force: true })
        await page.getByTestId('gallery-tag-filter-title').waitFor({ state: 'visible' })
      }

      await page.waitForTimeout(1000)

      // Verify tags still match - check selected tags
      const selectedLandscapeTag = page.getByTestId('tag-filter-selected-uuid-landscape-456')
      const selectedSunsetTag = page.getByTestId('tag-filter-selected-uuid-sunset-789')

      await expect(selectedLandscapeTag).toBeVisible()
      await expect(selectedSunsetTag).toBeVisible()
    })
  })
})
