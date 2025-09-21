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
        pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\?creator_id=1&limit=1',
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
            },
          ],
          total: 1,
          limit: 1,
          skip: 0,
        },
      },
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\?limit=1',
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
            },
          ],
          total: 3,
          limit: 1,
          skip: 0,
        },
      },
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent\\?limit=5&sort=recent',
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
    await expect(page.getByText('User Content')).toBeVisible()
    await expect(page.getByText('Community Content')).toBeVisible()
    await expect(page.getByText('Surreal Landscape')).toBeVisible()
  })
})
