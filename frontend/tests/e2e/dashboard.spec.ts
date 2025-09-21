import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Dashboard', () => {
  test('shows content stats and recent content', async ({ page }) => {
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
        pattern: '\\/api\\/v1\\/content\\?limit=1&creator_id=1',
        body: {
          items: [
            {
              id: 1,
              title: 'User Content Item',
              description: 'Content created by user',
              image_url: null,
              quality_score: 0.9,
              created_at: '2024-01-10T00:00:00Z',
              updated_at: '2024-01-10T00:00:00Z',
              content_type: 'text',
              content_data: 'Sample content',
              item_metadata: {},
              creator_id: 1,
              tags: [],
              is_public: true,
              is_private: false,
            },
          ],
          total: 1,
          limit: 1,
          skip: 0,
        },
      },
      {
        pattern: '\\/api\\/v1\\/content\\?limit=1$',
        body: {
          items: [
            {
              id: 42,
              title: 'Surreal Landscape',
              description: 'AI art piece',
              image_url: null,
              quality_score: 0.9,
              created_at: '2024-01-10T00:00:00Z',
              updated_at: '2024-01-10T00:00:00Z',
              content_type: 'image',
              content_data: 'image_data',
              item_metadata: {},
              creator_id: 2,
              tags: [],
              is_public: true,
              is_private: false,
            },
          ],
          total: 3,
          limit: 1,
          skip: 0,
        },
      },
      {
        pattern: '/api/v1/content.*limit=5.*sort=recent.*creator_id=1',
        body: {
          items: [
            {
              id: 1,
              title: 'User Content Item',
              description: 'Content created by user',
              image_url: null,
              quality_score: 0.9,
              created_at: '2024-01-10T00:00:00Z',
              updated_at: '2024-01-10T00:00:00Z',
              content_type: 'text',
              content_data: 'Sample content',
              item_metadata: {},
              creator_id: 1,
              tags: [],
              is_public: true,
              is_private: false,
            },
          ],
          total: 1,
          limit: 5,
          skip: 0,
        },
      },
      {
        pattern: '/api/v1/content.*limit=5.*sort=recent(?!.*creator_id)',
        body: {
          items: [
            {
              id: 42,
              title: 'Surreal Landscape',
              description: 'AI art piece',
              image_url: null,
              quality_score: 0.9,
              created_at: '2024-01-10T00:00:00Z',
              updated_at: '2024-01-10T00:00:00Z',
              content_type: 'image',
              content_data: 'image_data',
              item_metadata: {},
              creator_id: 2,
              tags: [],
              is_public: true,
              is_private: false,
            },
          ],
          total: 3,
          limit: 5,
          skip: 0,
        },
      },
    ])

    await page.goto('/dashboard')
    await page.waitForSelector('nav', { timeout: 20000 })

    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
    await expect(page.getByRole('heading', { name: '1' })).toBeVisible() // User content count
    await expect(page.getByRole('heading', { name: '3' })).toBeVisible() // Total content count
    await expect(page.getByText('Your works').first()).toBeVisible()
    await expect(page.getByText('Community works').first()).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Your recent works' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Your recent auto-gens' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Community recent works' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Community recent auto-gens' })).toBeVisible()

    await expect(page.getByRole('heading', { level: 2 })).toHaveText([
      'Your recent works',
      'Your recent auto-gens',
      'Community recent works',
      'Community recent auto-gens',
    ])
    await expect(page.getByText('User Content Item').first()).toBeVisible() // User's recent content
    await expect(page.getByText('Surreal Landscape').first()).toBeVisible() // Community recent content
  })
})
