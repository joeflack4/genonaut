import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

test.describe('Settings page', () => {
  test.skip('persists profile updates and theme preference', async ({ page }) => {
    const initialUser = {
      id: 1,
      name: 'Admin',
      email: 'admin@example.com',
      is_active: true,
    }

    const updatedUser = {
      ...initialUser,
      name: 'Updated Admin',
    }

    await setupMockApi(page, [
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
        body: initialUser,
      },
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
        method: 'PUT',
        body: updatedUser,
      },
    ])

    await page.goto('/settings')
    await page.waitForSelector('nav', { timeout: 20000 })

    const nameInput = page.getByLabel('Display name')
    await expect(nameInput).toHaveValue('Admin')

    await nameInput.fill(updatedUser.name)
    await page.getByRole('button', { name: /save changes/i }).click()
    await expect(page.getByText(/profile updated/i)).toBeVisible()

    const history = await page.evaluate(() => window.__pwReadMockHistory())
    expect(history.some((entry) => /api\/v1\/users\/1$/.test(entry.url) && entry.method === 'PUT')).toBe(true)

    await page.evaluate(
      ({ pattern, body }) => {
        window.__pwUpdateMock(pattern, 'GET', body, 200)
      },
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
        body: updatedUser,
      }
    )

    const modeLocator = page.getByText(/current mode:/i)
    const initialModeText = (await modeLocator.textContent()) ?? 'Current mode: dark'
    const initialMode = initialModeText.toLowerCase().includes('light') ? 'light' : 'dark'
    const nextMode = initialMode === 'light' ? 'dark' : 'light'

    await expect(modeLocator).toHaveText(new RegExp(`Current mode: ${initialMode}`, 'i'))
    await page.getByRole('button', { name: /toggle theme/i }).click()
    await expect(modeLocator).toHaveText(new RegExp(`Current mode: ${nextMode}`, 'i'))

    await expect
      .poll(async () => await page.evaluate(() => window.localStorage.getItem('theme-mode')))
      .toBe(nextMode)

    const secondPage = await page.context().newPage()
    await setupMockApi(secondPage, [
      {
        pattern: '\\u002Fapi\\u002Fv1\\u002Fusers\\u002F1$',
        body: updatedUser,
      },
    ])

    await secondPage.goto('/settings')
    await secondPage.waitForSelector('nav', { timeout: 20000 })

    await expect(secondPage.getByLabel('Display name')).toHaveValue(updatedUser.name)
    await expect(secondPage.getByText(new RegExp(`Current mode: ${nextMode}`, 'i'))).toBeVisible()

    await secondPage.close()
  })
})
