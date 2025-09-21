import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Dashboard', () => {
  test('shows user stats and recent content', async ({ page }) => {
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
        pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1\\u002Fstats$',
        body: {
          total_recommendations: 12,
          served_recommendations: 5,
          generated_content: 7,
          last_active_at: '2024-01-12T10:00:00Z',
        },
      },
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent',
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
          total: 1,
          limit: 5,
          skip: 0,
        },
      },
    ])

    await page.goto('/dashboard')
    await page.waitForSelector('nav', { timeout: 20000 })

    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
    await expect(page.getByRole('heading', { name: '12' })).toBeVisible()
    await expect(page.getByText('Total Recommendations')).toBeVisible()
    await expect(page.getByText('Surreal Landscape')).toBeVisible()
  })
})
