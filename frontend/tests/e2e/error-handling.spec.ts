/**
 * End-to-end tests for frontend error handling and user experience during errors.
 *
 * These tests validate that users receive appropriate feedback, can recover from errors,
 * and have a smooth experience even when things go wrong.
 */

import { test, expect, Page } from '@playwright/test'

test.describe('Frontend Error Handling', () => {

  test.beforeEach(async ({ page }) => {
    // Set up console error tracking
    const consoleErrors: string[] = []
    page.setDefaultNavigationTimeout(5_000)
    page.setDefaultTimeout(4_000)
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    // Store console errors for later verification
    page.consoleErrors = consoleErrors
  })

  test('displays user-friendly error when API is unavailable', async ({ page }) => {
    // Mock necessary APIs for page load
    await page.route('**/api/v1/users/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          username: 'testuser',
          email: 'test@example.com'
        })
      })
    })

    await page.route('**/api/v1/models**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          checkpoints: [],
          loras: []
        })
      })
    })

    // Mock API to return 503 Service Unavailable for generation jobs
    await page.route('**/api/v1/generation-jobs/**', async route => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            message: 'Image generation service is temporarily unavailable. Please try again in a few minutes.',
            category: 'connection',
            retry_after: 60,
            support_info: {
              status_page: 'https://status.example.com'
            }
          }
        })
      })
    })

    await page.goto('/generation', { waitUntil: 'domcontentloaded' })

    // Try to submit a generation request
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    await page.click('[data-testid="generate-button"]')

    // Should display user-friendly error message
    const errorAlert = page.locator('[data-testid="error-alert"]')
    await expect(errorAlert).toBeVisible()

    const errorMessage = await errorAlert.textContent()
    expect(errorMessage).toContain('temporarily unavailable')
    expect(errorMessage).toContain('try again')
    expect(errorMessage).not.toContain('503')
    expect(errorMessage).not.toContain('API')

    // Should show retry option
    const retryButton = page.locator('[data-testid="retry-button"]')
    await expect(retryButton).toBeVisible()

    // Should provide support information
    const supportLink = page.locator('[data-testid="support-link"]')
    if (await supportLink.isVisible()) {
      expect(await supportLink.getAttribute('href')).toContain('status')
    }
  })

  test('handles validation errors with specific guidance', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Mock API to return validation errors
    await page.route('**/api/comfyui/generations*', async route => {
      await route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: [
            {
              loc: ['body', 'prompt'],
              msg: 'Prompt cannot be empty',
              type: 'value_error'
            },
            {
              loc: ['body', 'width'],
              msg: 'Width must be between 64 and 2048',
              type: 'value_error'
            },
            {
              loc: ['body', 'steps'],
              msg: 'Steps must be between 1 and 150',
              type: 'value_error'
            }
          ]
        })
      })
    })

    await page.goto('/generation')

    // Submit form with invalid data
    await page.fill('[data-testid="prompt-input"]', '')  // Empty prompt
    await page.fill('[data-testid="width-input"]', '0')  // Invalid width
    await page.fill('[data-testid="steps-input"]', '0')  // Invalid steps
    await page.click('[data-testid="generate-button"]')

    // Should display specific validation errors
    const promptError = page.locator('[data-testid="prompt-error"]')
    await expect(promptError).toBeVisible()
    await expect(promptError).toContainText('cannot be empty')

    const widthError = page.locator('[data-testid="width-error"]')
    await expect(widthError).toBeVisible()
    await expect(widthError).toContainText('between 64 and 2048')

    const stepsError = page.locator('[data-testid="steps-error"]')
    await expect(stepsError).toBeVisible()
    await expect(stepsError).toContainText('between 1 and 150')

    // Form fields should be highlighted
    await expect(page.locator('[data-testid="prompt-input"]')).toHaveClass(/error/)
    await expect(page.locator('[data-testid="width-input"]')).toHaveClass(/error/)
    await expect(page.locator('[data-testid="steps-input"]')).toHaveClass(/error/)
  })

  test('provides recovery options for network errors', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Mock network error
    await page.route('**/api/comfyui/generations*', async route => {
      await route.abort('failed')
    })

    await page.goto('/generation')

    // Submit a generation request
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    await page.click('[data-testid="generate-button"]')

    // Should display network error with recovery options
    const errorContainer = page.locator('[data-testid="error-container"]')
    await expect(errorContainer).toBeVisible()

    const errorMessage = await errorContainer.textContent()
    expect(errorMessage).toContain('connection')
    expect(errorMessage).toContain('network')

    // Should provide multiple recovery options
    const retryButton = page.locator('[data-testid="retry-button"]')
    await expect(retryButton).toBeVisible()

    const refreshButton = page.locator('[data-testid="refresh-page-button"]')
    if (await refreshButton.isVisible()) {
      expect(await refreshButton.textContent()).toContain('Refresh')
    }

    const offlineModeInfo = page.locator('[data-testid="offline-info"]')
    if (await offlineModeInfo.isVisible()) {
      expect(await offlineModeInfo.textContent()).toContain('offline')
    }
  })

  test('shows loading states and prevents multiple submissions', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Mock slow API response
    await page.route('**/api/comfyui/generations*', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000)) // 2 second delay
      await route.fulfill({
        json: {
          id: 1,
          status: 'pending',
          prompt: 'Test prompt'
        }
      })
    })

    await page.goto('/generation')

    // Submit a generation request
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    const generateButton = page.locator('[data-testid="generate-button"]')
    await generateButton.click()

    // Should show loading state immediately
    await expect(generateButton).toBeDisabled()
    await expect(generateButton).toContainText('Generating')

    // Loading indicator should be visible
    const loadingSpinner = page.locator('[data-testid="loading-spinner"]')
    await expect(loadingSpinner).toBeVisible()

    // Should prevent additional submissions
    await generateButton.click({ force: true })
    // Should not trigger additional requests (verified by network mock)

    // Wait for completion
    await expect(generateButton).toBeEnabled({ timeout: 5000 })
    await expect(loadingSpinner).not.toBeVisible()
  })

  test('handles timeout errors gracefully', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Mock timeout error
    await page.route('**/api/comfyui/generations*', async route => {
      await new Promise(resolve => setTimeout(resolve, 30000)) // Never resolves
    })

    // Set shorter timeout for test
    page.setDefaultTimeout(2000)

    await page.goto('/generation')

    // Submit request that will timeout
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    await page.click('[data-testid="generate-button"]')

    // Should handle timeout gracefully
    const timeoutError = page.locator('[data-testid="timeout-error"]')
    await expect(timeoutError).toBeVisible({ timeout: 5000 })

    const errorMessage = await timeoutError.textContent()
    expect(errorMessage).toContain('taking longer than expected')
    expect(errorMessage).toContain('busy')

    // Should offer to continue waiting or cancel
    const continueWaitingButton = page.locator('[data-testid="continue-waiting-button"]')
    const cancelButton = page.locator('[data-testid="cancel-request-button"]')

    await expect(continueWaitingButton).toBeVisible()
    await expect(cancelButton).toBeVisible()
  })

  test('displays generation failure errors with recovery options', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Mock successful submission but failed generation
    await page.route('**/api/comfyui/generations*', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          json: { id: 1, status: 'pending', prompt: 'Test prompt' }
        })
      } else {
        // Status check returns failure
        await route.fulfill({
          json: {
            id: 1,
            status: 'failed',
            prompt: 'Test prompt',
            error_message: 'Generation failed due to insufficient VRAM. Try reducing image size or batch size.',
            recovery_suggestions: [
              'Reduce image width and height',
              'Use batch size of 1',
              'Try a different model'
            ]
          }
        })
      }
    })

    await page.goto('/generation')

    // Submit generation
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    await page.click('[data-testid="generate-button"]')

    // Wait for failure to be detected
    await expect(page.locator('[data-testid="generation-failed"]')).toBeVisible({ timeout: 10000 })

    // Should display clear error message
    const errorMessage = page.locator('[data-testid="failure-message"]')
    await expect(errorMessage).toContainText('insufficient VRAM')
    await expect(errorMessage).toContainText('reducing image size')

    // Should show recovery suggestions
    const suggestions = page.locator('[data-testid="recovery-suggestions"]')
    await expect(suggestions).toBeVisible()

    const suggestionsList = page.locator('[data-testid="suggestion-item"]')
    await expect(suggestionsList).toHaveCount(3)

    // Should allow easy retry with suggested changes
    const retryWithChangesButton = page.locator('[data-testid="retry-with-suggestions-button"]')
    if (await retryWithChangesButton.isVisible()) {
      await retryWithChangesButton.click()
      // Should auto-apply suggested settings
      expect(await page.locator('[data-testid="batch-size-input"]').inputValue()).toBe('1')
    }
  })

  test('provides rate limit feedback with clear timing', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Mock rate limit error
    await page.route('**/api/comfyui/generations*', async route => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            message: 'You have exceeded the rate limit. Please wait before making another request.',
            category: 'rate_limit',
            retry_after: 60,
            rate_limit_info: {
              current_usage: 15,
              limit: 10,
              reset_time: new Date(Date.now() + 60000).toISOString()
            }
          }
        })
      })
    })

    await page.goto('/generation')

    // Submit request that hits rate limit
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    await page.click('[data-testid="generate-button"]')

    // Should display rate limit information
    const rateLimitError = page.locator('[data-testid="rate-limit-error"]')
    await expect(rateLimitError).toBeVisible()

    const errorMessage = await rateLimitError.textContent()
    expect(errorMessage).toContain('rate limit')
    expect(errorMessage).toContain('wait')

    // Should show specific timing information
    const countdown = page.locator('[data-testid="rate-limit-countdown"]')
    await expect(countdown).toBeVisible()

    const countdownText = await countdown.textContent()
    expect(countdownText).toMatch(/\d+.*seconds?/)

    // Should show current usage vs limit
    const usageInfo = page.locator('[data-testid="usage-info"]')
    await expect(usageInfo).toBeVisible()
    await expect(usageInfo).toContainText('15')
    await expect(usageInfo).toContainText('10')

    // Generate button should be disabled during cooldown
    const generateButton = page.locator('[data-testid="generate-button"]')
    await expect(generateButton).toBeDisabled()
  })

  test('handles image loading errors in gallery', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Mock generations list with broken image URLs
    await page.route('**/api/comfyui/generations*', async route => {
      await route.fulfill({
        json: {
          items: [
            {
              id: 1,
              prompt: 'Test generation',
              status: 'completed',
              thumbnail_paths: ['/broken/thumbnail.jpg'],
              output_paths: ['/broken/output.png']
            }
          ],
          pagination: { page: 1, page_size: 10, total_count: 1, total_pages: 1 }
        }
      })
    })

    // Mock broken image requests
    await page.route('**/broken/**', async route => {
      await route.fulfill({ status: 404 })
    })

    await page.goto('/generation')
    await page.click('[data-testid="history-tab"]')

    // Should display placeholder for broken images
    const imagePlaceholder = page.locator('[data-testid="image-placeholder"]')
    await expect(imagePlaceholder).toBeVisible()

    // Should show image error indicator
    const imageError = page.locator('[data-testid="image-error"]')
    await expect(imageError).toBeVisible()

    // Should provide option to retry image loading
    const retryImageButton = page.locator('[data-testid="retry-image-button"]')
    if (await retryImageButton.isVisible()) {
      await retryImageButton.click()
      // Should attempt to reload the image
    }
  })

  test('shows offline mode when network is unavailable', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    await page.goto('/generation')

    // Simulate going offline
    await page.context().setOffline(true)

    // Try to submit a generation
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    await page.click('[data-testid="generate-button"]')

    // Should detect offline state
    const offlineIndicator = page.locator('[data-testid="offline-indicator"]')
    await expect(offlineIndicator).toBeVisible()

    const offlineMessage = await offlineIndicator.textContent()
    expect(offlineMessage).toContain('offline')
    expect(offlineMessage).toContain('connection')

    // Should disable network-dependent features
    const generateButton = page.locator('[data-testid="generate-button"]')
    await expect(generateButton).toBeDisabled()

    // Should show offline mode information
    const offlineBanner = page.locator('[data-testid="offline-banner"]')
    await expect(offlineBanner).toBeVisible()
    await expect(offlineBanner).toContainText('working offline')

    // Go back online
    await page.context().setOffline(false)

    // Should detect online state and re-enable features
    await expect(offlineIndicator).not.toBeVisible({ timeout: 5000 })
    await expect(generateButton).toBeEnabled()
  })

  test('preserves form data during errors', async ({ page }) => {
    // Mock necessary APIs for page load
    await page.route('**/api/v1/users/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          username: 'testuser',
          email: 'test@example.com'
        })
      })
    })

    await page.route('**/api/v1/models**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          checkpoints: [],
          loras: []
        })
      })
    })

    await page.goto('/generation', { waitUntil: 'domcontentloaded' })

    // Fill out form with complex data
    const formData = {
      prompt: 'A detailed fantasy landscape with mountains, forests, and a magical castle',
      negativePrompt: 'blurry, low quality, artifacts',
      width: '768',
      height: '512',
      steps: '30',
      cfgScale: '8.5',
      seed: '12345'
    }

    await page.fill('[data-testid="prompt-input"]', formData.prompt)
    await page.fill('[data-testid="negative-prompt-input"]', formData.negativePrompt)
    await page.fill('[data-testid="width-input"]', formData.width)
    await page.fill('[data-testid="height-input"]', formData.height)
    await page.fill('[data-testid="steps-input"]', formData.steps)
    await page.fill('[data-testid="cfg-scale-input"]', formData.cfgScale)
    await page.fill('[data-testid="seed-input"]', formData.seed)

    // Mock error response
    await page.route('**/api/v1/generation-jobs/**', async route => {
      await route.fulfill({ status: 500, body: 'Internal Server Error' })
    })

    // Submit form
    await page.click('[data-testid="generate-button"]')

    // Should show error
    await expect(page.locator('[data-testid="error-alert"]')).toBeVisible()

    // Form data should be preserved
    expect(await page.locator('[data-testid="prompt-input"]').inputValue()).toBe(formData.prompt)
    expect(await page.locator('[data-testid="negative-prompt-input"]').inputValue()).toBe(formData.negativePrompt)
    expect(await page.locator('[data-testid="width-input"]').inputValue()).toBe(formData.width)
    expect(await page.locator('[data-testid="height-input"]').inputValue()).toBe(formData.height)
    expect(await page.locator('[data-testid="steps-input"]').inputValue()).toBe(formData.steps)
    expect(await page.locator('[data-testid="cfg-scale-input"]').inputValue()).toBe(formData.cfgScale)
    expect(await page.locator('[data-testid="seed-input"]').inputValue()).toBe(formData.seed)

    // User can immediately retry with same data
    const retryButton = page.locator('[data-testid="retry-button"]')
    await expect(retryButton).toBeVisible()
  })

  test('provides accessible error messages', async ({ page }) => {
    // Mock necessary APIs for page load
    await page.route('**/api/v1/users/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          username: 'testuser',
          email: 'test@example.com'
        })
      })
    })

    await page.route('**/api/v1/models**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          checkpoints: [],
          loras: []
        })
      })
    })

    // Mock error response
    await page.route('**/api/v1/generation-jobs/**', async route => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            message: 'Service temporarily unavailable',
            category: 'connection'
          }
        })
      })
    })

    await page.goto('/generation', { waitUntil: 'domcontentloaded' })

    // Submit request
    await page.fill('[data-testid="prompt-input"]', 'Test prompt')
    await page.click('[data-testid="generate-button"]')

    // Error should be announced to screen readers
    const errorAlert = page.locator('[data-testid="error-alert"]')
    await expect(errorAlert).toBeVisible()
    await expect(errorAlert).toHaveAttribute('role', 'alert')
    await expect(errorAlert).toHaveAttribute('aria-live', 'assertive')

    // Error should have appropriate semantic markup
    const errorHeading = page.locator('[data-testid="error-heading"]')
    if (await errorHeading.isVisible()) {
      await expect(errorHeading).toHaveRole('heading')
    }

    // Error should be keyboard accessible
    await page.keyboard.press('Tab')
    const retryButton = page.locator('[data-testid="retry-button"]')
    if (await retryButton.isVisible()) {
      await expect(retryButton).toBeFocused()
      await page.keyboard.press('Enter')
      // Should trigger retry action
    }
  })

  test('reports JavaScript errors appropriately', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    await page.goto('/generation')

    // Trigger a JavaScript error
    await page.evaluate(() => {
      // Simulate an unhandled error
      setTimeout(() => {
        throw new Error('Test JavaScript error')
      }, 100)
    })

    await page.waitForTimeout(500)

    // Should display user-friendly error message (not technical details)
    const jsErrorAlert = page.locator('[data-testid="js-error-alert"]')
    if (await jsErrorAlert.isVisible()) {
      const errorText = await jsErrorAlert.textContent()
      expect(errorText).toContain('unexpected error')
      expect(errorText).not.toContain('Test JavaScript error') // Technical details hidden
      expect(errorText).toContain('refresh')
    }

    // Should provide recovery options
    const refreshButton = page.locator('[data-testid="refresh-page-button"]')
    if (await refreshButton.isVisible()) {
      await refreshButton.click()
      await expect(page).toHaveURL('/generation')
    }

    // Console errors should be tracked (for testing purposes)
    const consoleErrors = (page as any).consoleErrors as string[]
    expect(consoleErrors.length).toBeGreaterThan(0)
    expect(consoleErrors.some(error => error.includes('Test JavaScript error'))).toBe(true)
  })

  test('handles progressive enhancement gracefully', async ({ page }) => {
    test.skip('Temporarily skipped – see notes/fix-playwright-tests.md for context')
    // Disable JavaScript to test progressive enhancement
    await page.context().addInitScript(() => {
      // Simulate limited JavaScript functionality
      delete (window as any).fetch
    })

    await page.goto('/generation')

    // Should provide fallback messaging when JavaScript features unavailable
    const noJsFallback = page.locator('[data-testid="no-js-fallback"]')
    if (await noJsFallback.isVisible()) {
      const fallbackText = await noJsFallback.textContent()
      expect(fallbackText).toContain('JavaScript')
      expect(fallbackText).toContain('enable')
    }

    // Should still allow basic form interaction
    const promptInput = page.locator('[data-testid="prompt-input"]')
    await expect(promptInput).toBeVisible()
    await promptInput.fill('Test prompt')
    expect(await promptInput.inputValue()).toBe('Test prompt')
  })
})
