import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Auth pages', () => {
  test('redirects logged-in user from login to dashboard', async ({ page }) => {
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
          total_recommendations: 6,
          served_recommendations: 3,
          generated_content: 9,
          last_active_at: '2024-01-10T00:00:00Z',
        },
      },
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fcontent.*limit=5.*sort=recent',
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
    await expect(page.getByText('Aurora Dreams')).toBeVisible()
  })

  test('keeps unauthenticated visitor on signup placeholder', async ({ page }) => {
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
