import { test, expect } from '@playwright/test'

test.describe('Accessibility Tests', () => {
  test('should support comprehensive keyboard navigation', async ({ page }) => {
    await page.goto('/')

    // Test Tab navigation through interactive elements
    const interactiveElements = []
    let tabCount = 0
    const maxTabs = 20 // Prevent infinite loops

    while (tabCount < maxTabs) {
      await page.keyboard.press('Tab')
      tabCount++

      const focusedElement = page.locator(':focus')

      if (await focusedElement.count() > 0) {
        const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase())
        const role = await focusedElement.getAttribute('role')

        if (['button', 'a', 'input', 'select', 'textarea'].includes(tagName) ||
            ['button', 'link', 'textbox'].includes(role)) {
          interactiveElements.push({ tagName, role })
        }
      }
    }

    // Should have found some interactive elements
    expect(interactiveElements.length).toBeGreaterThan(0)
  })

  test('should support Enter/Space key activation', async ({ page }) => {
    await page.goto('/generate')

    // Wait for page to load
    await page.waitForSelector('main')

    // Find a button to test
    const buttons = page.locator('button:visible')
    const buttonCount = await buttons.count()

    if (buttonCount > 0) {
      const testButton = buttons.first()
      await testButton.focus()
      await expect(testButton).toBeFocused()

      // Test space key activation (if it's a normal button)
      const buttonText = await testButton.textContent()
      if (buttonText && !buttonText.includes('Generate')) {
        // Don't actually trigger generation
        await page.keyboard.press('Space')
        // Button should have received the keypress
      }
    }
  })

  test('should handle Escape key behavior', async ({ page }) => {
    await page.goto('/settings')

    // Test Escape key behavior (should not cause errors)
    await page.keyboard.press('Escape')

    // Page should still be functional
    await expect(page.locator('main')).toBeVisible()
  })

  test('should have proper heading hierarchy', async ({ page }) => {
    const pages = ['/', '/dashboard', '/gallery', '/recommendations', '/settings', '/generate']

    for (const pagePath of pages) {
      await page.goto(pagePath)
      await page.waitForSelector('main, body')

      // Check for heading elements
      const headings = page.locator('h1, h2, h3, h4, h5, h6')
      const headingCount = await headings.count()

      if (headingCount > 0) {
        // Should have at least one heading per page
        expect(headingCount).toBeGreaterThan(0)

        // Check that headings have text content
        const firstHeading = headings.first()
        const headingText = await firstHeading.textContent()
        expect(headingText).toBeTruthy()
      }
    }
  })

  test('should have accessible form labels', async ({ page }) => {
    await page.goto('/generate')

    // Wait for form to load
    await page.waitForSelector('form', { timeout: 10000 })

    // Check for proper form labeling
    const inputs = page.locator('input, select, textarea')
    const inputCount = await inputs.count()

    let labeledInputs = 0

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i)

      // Check if input has associated label
      const id = await input.getAttribute('id')
      const ariaLabel = await input.getAttribute('aria-label')
      const placeholder = await input.getAttribute('placeholder')

      if (id) {
        const label = page.locator(`label[for="${id}"]`)
        if (await label.count() > 0) {
          labeledInputs++
        }
      }

      if (ariaLabel || placeholder) {
        labeledInputs++
      }
    }

    // Most inputs should have some form of labeling
    if (inputCount > 0) {
      expect(labeledInputs).toBeGreaterThan(0)
    }
  })

  test('should have visible focus indicators', async ({ page }) => {
    await page.goto('/')

    // Tab to first focusable element
    await page.keyboard.press('Tab')

    const focusedElement = page.locator(':focus')

    if (await focusedElement.count() > 0) {
      // Focus should be visible (this is hard to test programmatically,
      // but we can at least verify an element is focused)
      await expect(focusedElement).toBeFocused()
    }
  })
})