import { test, expect } from '@playwright/test'

test.describe('Navigation Tests', () => {
  test('should navigate between all main pages', async ({ page }) => {
    // Start at home (may redirect to dashboard)
    await page.goto('/')
    await page.waitForURL(/\/(dashboard)?$/)

    // Navigate to each main page
    await page.click('[href="/dashboard"]')
    await expect(page).toHaveURL('/dashboard')

    await page.click('[href="/gallery"]')
    await expect(page).toHaveURL('/gallery')

    await page.click('[href="/recommendations"]')
    await expect(page).toHaveURL('/recommendations')

    await page.click('[href="/settings"]')
    await expect(page).toHaveURL('/settings')

    await page.click('[href="/generate"]')
    await expect(page).toHaveURL('/generate')
  })

  test('should verify all navigation items are visible and clickable', async ({ page }) => {
    await page.goto('/')

    // Wait for navigation to load
    await page.waitForSelector('nav')

    // Check all main navigation items are visible
    await expect(page.locator('[href="/dashboard"]')).toBeVisible()
    await expect(page.locator('[href="/gallery"]')).toBeVisible()
    await expect(page.locator('[href="/recommendations"]')).toBeVisible()
    await expect(page.locator('[href="/settings"]')).toBeVisible()
    await expect(page.locator('[href="/generate"]')).toBeVisible()
  })

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/')

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
    const routes = ['/dashboard', '/gallery', '/recommendations', '/settings', '/generate']

    for (const route of routes) {
      await page.goto(route)
      await expect(page).toHaveURL(route)
      // Page should load without errors
      await expect(page.locator('body')).toBeVisible()
    }
  })
})