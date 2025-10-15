import { test, expect } from '@playwright/test'

test.describe('Navigation Tests', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
  })
  test('should navigate between all main pages', async ({ page }) => {
    // Start at home (may redirect to dashboard)
    await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 5_000 })
    await page.waitForURL(/\/(dashboard)?$/)

    // Navigate to each main page using data-testid
    await page.click('[data-testid="app-layout-nav-link-dashboard"]')
    await expect(page).toHaveURL('/dashboard')

    // Gallery uses custom navigation (button, not link) to preserve query params
    await page.click('[data-testid="app-layout-nav-link-gallery"]')
    await expect(page).toHaveURL('/gallery')

    await page.click('[data-testid="app-layout-nav-link-settings"]')
    await expect(page).toHaveURL('/settings')

    await page.click('[data-testid="app-layout-nav-link-generate"]')
    await expect(page).toHaveURL('/generate')
  })

  test('should verify all navigation items are visible and clickable', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Wait for navigation to load
    await page.waitForSelector('nav')

    // Check visible navigation items (by default: dashboard, gallery, generate, tag-hierarchy, settings)
    // Note: recommendations and flagged-content are hidden by default
    await expect(page.locator('[data-testid="app-layout-nav-link-dashboard"]')).toBeVisible()
    await expect(page.locator('[data-testid="app-layout-nav-link-gallery"]')).toBeVisible()
    await expect(page.locator('[data-testid="app-layout-nav-link-generate"]')).toBeVisible()
    await expect(page.locator('[data-testid="app-layout-nav-link-tag-hierarchy"]')).toBeVisible()
    await expect(page.locator('[data-testid="app-layout-nav-link-settings"]')).toBeVisible()
  })

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Wait for navigation to load
    await page.waitForSelector('nav')

    // Test Tab navigation through navigation elements
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Test Enter key activation on focused element
    const focusedElement = await page.locator(':focus')
    await expect(focusedElement).toBeVisible()

    // Press Enter to activate
    await page.keyboard.press('Enter')

    // Should have navigated somewhere
    await page.waitForTimeout(100)
    const url = page.url()
    expect(url).toMatch(/\/(dashboard|gallery|recommendations|settings|generate)/)
  })

  test('should handle direct URL access to all routes', async ({ page }) => {
    test.setTimeout(15_000)
    const routes = ['/dashboard', '/gallery', '/recommendations', '/settings', '/generate']

    for (const route of routes) {
      await page.goto(route, { waitUntil: 'domcontentloaded', timeout: 5_000 })
      await expect(page).toHaveURL(route)
      // Page should load without errors
      await expect(page.locator('body')).toBeVisible()
    }
  })
})
