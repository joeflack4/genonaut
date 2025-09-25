import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Recommendations page', () => {
  test.skip('marks a recommendation as served', async ({ page }) => {
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
        pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1\\u002Frecommendations$',
        body: [
          {
            id: 7,
            user_id: 1,
            content_id: 42,
            algorithm: 'collaborative',
            score: 0.82,
            served_at: null,
            created_at: '2024-01-10T00:00:00Z',
          },
        ],
      },
    ])

    await page.route('**/api/v1/recommendations/served', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 7,
          user_id: 1,
          content_id: 42,
          algorithm: 'collaborative',
          score: 0.82,
          served_at: '2024-01-11T12:00:00Z',
          created_at: '2024-01-10T00:00:00Z',
        }),
      })

      await page.evaluate(() => {
        window.__pwUpdateMock(
          '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1\\u002Frecommendations$',
          'GET',
          [
            {
              id: 7,
              user_id: 1,
              content_id: 42,
              algorithm: 'collaborative',
              score: 0.82,
              served_at: '2024-01-11T12:00:00Z',
              created_at: '2024-01-10T00:00:00Z',
            },
          ],
          200
        )
      })
    })

    await page.goto('/recommendations')
    await page.waitForSelector('nav', { timeout: 20000 })

    await expect(page.getByText(/Recommendation #7/)).toBeVisible()
    await page.getByRole('button', { name: /mark as served/i }).click()
    await expect(page.getByText(/Served/)).toBeVisible()
  })
})
