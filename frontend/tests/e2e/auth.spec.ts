import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Auth pages', () => {
  test.skip('redirects logged-in user from login to dashboard', async ({ page }) => {
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
              title: 'Aurora Dreams',
              description: 'Generated skyline',
              image_url: null,
              quality_score: 0.88,
              created_at: '2024-01-09T12:00:00Z',
              updated_at: '2024-01-09T12:00:00Z',
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
              id: 101,
              title: 'Aurora Dreams',
              description: 'Generated skyline',
              image_url: null,
              quality_score: 0.88,
              created_at: '2024-01-09T12:00:00Z',
              updated_at: '2024-01-09T12:00:00Z',
              content_type: 'image',
              content_data: 'image_data',
              item_metadata: {},
              creator_id: 2,
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
    ])

    await page.goto('/login')
    await page.waitForURL('**/dashboard', { timeout: 20000 })

    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Community recent gens' })).toBeVisible()
    await expect(page.getByText('Aurora Dreams').first()).toBeVisible()
  })

  test.skip('keeps unauthenticated visitor on signup placeholder', async ({ page }) => {
    await setupMockApi(page, [
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
        status: 401,
        body: {
          detail: 'Not authenticated',
        },
      },
    ])

    await page.goto('/signup')

    await expect(page).toHaveURL(/\/signup$/)
    await expect(page.getByRole('heading', { name: /sign up/i })).toBeVisible()
    await expect(page.getByText(/placeholder screen/i)).toBeVisible()
    await expect(page.getByLabel('Name')).toBeDisabled()
    await expect(page.getByLabel('Email')).toBeDisabled()

    const history = await page.evaluate(() => window.__pwReadMockHistory())
    expect(history.filter((entry) => entry.method === 'GET').length).toBeGreaterThanOrEqual(1)
  })
})
