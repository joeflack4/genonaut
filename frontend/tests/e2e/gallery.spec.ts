import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Gallery page', () => {
  test('filters gallery items by search term', async ({ page }) => {
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
        pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent[^?]*\\?[^#]*search=Portrait',
        body: {
          items: [
            {
              id: 99,
              title: 'Portrait Muse',
              description: 'New filtered item',
              image_url: null,
              quality_score: 0.95,
              created_at: '2024-01-11T00:00:00Z',
              updated_at: '2024-01-11T00:00:00Z',
            },
          ],
          total: 1,
          limit: 10,
          skip: 0,
        },
      },
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent',
        body: {
          items: [
            {
              id: 1,
              title: 'Neon Cityscape',
              description: 'Futuristic skyline',
              image_url: null,
              quality_score: 0.87,
              created_at: '2024-01-05T00:00:00Z',
              updated_at: '2024-01-05T00:00:00Z',
            },
          ],
          total: 1,
          limit: 10,
          skip: 0,
        },
      },
    ])

    await page.goto('/gallery')
    await page.waitForSelector('nav', { timeout: 20000 })

    await expect(page.getByText('Neon Cityscape')).toBeVisible()

    const searchInput = page.getByLabel('Search gallery')
    await searchInput.fill('Portrait')
    await page.locator('form[aria-label="gallery filters"]').evaluate((form) =>
      (form as HTMLFormElement).requestSubmit()
    )

    await expect(page.getByText('Portrait Muse')).toBeVisible()
  })
})
