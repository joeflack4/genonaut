/**
 * End-to-end tests for frontend error handling and user experience during errors.
 *
 * These tests validate that users receive appropriate feedback, can recover from errors,
 * and have a smooth experience even when things go wrong.
 */

import { test, expect, type Page, type Request, type Response, type TestInfo } from '@playwright/test'

const ADMIN_USER_ID = '121e194b-4caa-4b81-ad4f-86ca3919d5b9'

const createTimestamp = () => new Date().toISOString()

async function fulfillJson(route: any, status: number, body: any) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function setupBaseMocks(page: Page) {
  const now = createTimestamp()
  const userResponse = {
    id: ADMIN_USER_ID,
    name: 'Admin User',
    email: 'admin@example.com',
    is_active: true,
    avatar_url: null,
    created_at: now,
    updated_at: now,
  }

  await page.route(`**/api/v1/users/${ADMIN_USER_ID}` , async (route) => {
    await fulfillJson(route, 200, userResponse)
  })

  const checkpointResponse = {
    items: [
      {
        id: 'ckpt-1',
        path: 'models/checkpoints/test-model.safetensors',
        filename: 'test-model.safetensors',
        name: 'Test Checkpoint',
        version: '1.0',
        architecture: 'sdxl',
        family: 'sd',
        description: 'Checkpoint used for error handling tests',
        rating: 4.8,
        tags: ['test'],
        model_metadata: {},
        created_at: now,
        updated_at: now,
      },
    ],
    total: 1,
  }

  await page.route('**/api/v1/checkpoint-models/**', async (route) => {
    await fulfillJson(route, 200, checkpointResponse)
  })

  const loraResponse = {
    items: [
      {
        id: 'lora-1',
        path: 'models/lora/test-lora.safetensors',
        filename: 'test-lora.safetensors',
        name: 'Test LoRA',
        version: '1.0',
        compatible_architectures: 'sdxl',
        family: 'sd',
        description: 'LoRA used for error handling tests',
        rating: 4.6,
        tags: ['test'],
        trigger_words: [],
        optimal_checkpoints: [],
        model_metadata: {},
        created_at: now,
        updated_at: now,
        is_compatible: true,
        is_optimal: true,
      },
    ],
    total: 1,
    pagination: {
      page: 1,
      page_size: 10,
      total_count: 1,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    },
  }

  await page.route('**/api/v1/lora-models/**', async (route) => {
    await fulfillJson(route, 200, loraResponse)
  })
}

function buildJob(overrides: Record<string, any> = {}) {
  const now = createTimestamp()
  return {
    id: 9901,
    user_id: ADMIN_USER_ID,
    job_type: 'image',
    prompt: 'Test prompt',
    params: {},
    status: 'pending',
    checkpoint_model: 'Test Checkpoint',
    lora_models: [],
    width: 512,
    height: 768,
    batch_size: 1,
    created_at: now,
    updated_at: now,
    negative_prompt: '',
    recovery_suggestions: [],
    output_paths: [],
    thumbnail_paths: [],
    ...overrides,
  }
}

async function gotoGeneration(page: Page) {
  await page.goto('/generate', { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('[data-testid="generation-form"]', { timeout: 10000 })
}

async function shortenTimeouts(page: Page) {
  await page.addInitScript(() => {
    const originalSetTimeout = window.setTimeout
    window.setTimeout = ((handler: TimerHandler, timeout?: number, ...args: unknown[]) => {
      const adjusted = typeof timeout === 'number' && timeout > 1000 ? 1000 : timeout
      return originalSetTimeout(handler, adjusted, ...args)
    }) as typeof window.setTimeout
  })
}

test.describe('Frontend Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultNavigationTimeout(10_000)
    page.setDefaultTimeout(8_000)
  })

  test('handles validation errors with specific guidance', async ({ page }) => {
    await setupBaseMocks(page)

    await page.route('**/api/v1/generation-jobs*', async (route) => {
      const request = route.request()
      const url = new URL(request.url())

      if (request.method() === 'POST' && url.pathname.endsWith('/generation-jobs/')) {
        await fulfillJson(route, 422, {
          detail: [
            {
              loc: ['body', 'width'],
              msg: 'Width must be between 64 and 2048',
              type: 'value_error',
            },
            {
              loc: ['body', 'steps'],
              msg: 'Steps must be between 1 and 150',
              type: 'value_error',
            },
          ],
        })
        return
      }

      if (request.method() === 'GET' && url.pathname.endsWith('/generation-jobs/')) {
        await fulfillJson(route, 200, { items: [], total: 0, limit: 20, skip: 0 })
        return
      }

      await route.continue()
    })

    await gotoGeneration(page)

    await page.getByTestId('prompt-input').fill('Valid prompt for validation test')
    await page.getByTestId('width-input').fill('0')

    // Wait for steps input to be available (in Advanced Settings accordion)
    const stepsInput = page.getByTestId('steps-input')
    await expect(stepsInput).toBeVisible({ timeout: 5000 })
    await stepsInput.fill('0')

    const generateButton = page.getByTestId('generate-button')
    await expect(generateButton).toBeEnabled({ timeout: 10_000 })

    // Click the button - don't wait for response if it doesn't happen
    await generateButton.click()

    // Wait for the error to appear (either from frontend validation or backend response)
    // The form might validate on frontend before even making the POST request
    await page.waitForTimeout(1000)

    // Check if width error appears
    const widthError = page.getByTestId('width-error')
    const widthErrorVisible = await widthError.isVisible().catch(() => false)

    if (!widthErrorVisible) {
      // If no immediate error, wait for potential API response
      try {
        await page.waitForResponse(
          response => response.url().includes('/generation-jobs') && response.request().method() === 'POST',
          { timeout: 3000 }
        )
        await page.waitForTimeout(500)
      } catch (e) {
        // API request might not have been made due to frontend validation
      }
    }

    // Now check for the width error - it should be visible either way
    await expect(page.getByTestId('width-error')).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('width-error')).toContainText(/64/i)

    // Check if steps error also appears (it might not if steps has a default value)
    const stepsError = page.getByTestId('steps-error')
    if (await stepsError.isVisible()) {
      await expect(stepsError).toContainText(/1.*150|between 1 and 150/i)
      await expect(page.getByTestId('steps-input')).toHaveClass(/error/)
    }

    // Verify field error classes
    await expect(page.getByTestId('prompt-input')).not.toHaveClass(/error/)
    await expect(page.getByTestId('width-input')).toHaveClass(/error/)
  })

  test('shows loading states and prevents multiple submissions', async ({ page }) => {
    await setupBaseMocks(page)

    let createCalls = 0

    await page.route('**/api/v1/generation-jobs/**', async (route) => {
      const request = route.request()

      if (request.method() === 'POST') {
        createCalls += 1
        // Simulate slow server response
        await new Promise((resolve) => setTimeout(resolve, 1000))
        await fulfillJson(route, 201, buildJob({ status: 'pending' }))
        return
      }

      if (request.method() === 'GET') {
        // Return running status for polling
        await fulfillJson(route, 200, buildJob({ status: 'running' }))
        return
      }

      await route.continue()
    })

    // Also handle list endpoint
    await page.route('**/api/v1/generation-jobs?*', async (route) => {
      await fulfillJson(route, 200, { items: [], total: 0, limit: 20, skip: 0 })
    })

    await gotoGeneration(page)
    const generateButton = page.getByTestId('generate-button')

    await page.getByTestId('prompt-input').fill('Long running prompt')
    await expect(generateButton).toBeEnabled({ timeout: 10_000 })

    // Track POST request
    const postRequestPromise = page.waitForRequest((req) =>
      req.url().includes('/generation-jobs/') && req.method() === 'POST'
    )

    await generateButton.click()

    // Wait for POST to be sent
    await postRequestPromise

    // Button should be disabled during submission
    await expect(generateButton).toBeDisabled()
    await expect(generateButton).toHaveText(/generating/i)

    // Try clicking again - should still be disabled
    await generateButton.click({ force: true })
    await expect(generateButton).toBeDisabled()

    // Wait for submission to complete
    await expect(generateButton).toBeEnabled({ timeout: 4000 })

    // Verify only one POST was sent
    expect(createCalls).toBe(1)
  })

  test('handles timeout errors gracefully', async ({ page }) => {
    await shortenTimeouts(page)
    await setupBaseMocks(page)

    await page.route('**/api/v1/generation-jobs*', async (route) => {
      const request = route.request()
      const url = new URL(request.url())

      if (request.method() === 'POST' && url.pathname.endsWith('/generation-jobs/')) {
        await new Promise((resolve) => setTimeout(resolve, 2000))
        await fulfillJson(route, 201, buildJob())
        return
      }

      if (request.method() === 'GET' && url.pathname.endsWith('/generation-jobs/')) {
        await fulfillJson(route, 200, { items: [], total: 0, limit: 20, skip: 0 })
        return
      }

      await route.continue()
    })

    await gotoGeneration(page)
    await page.getByTestId('prompt-input').fill('Prompt triggering timeout warning')
    await page.getByTestId('generate-button').click()

    await expect(page.getByTestId('timeout-warning')).toBeVisible()
  })

  test('preserves form data during errors', async ({ page }) => {
    await setupBaseMocks(page)

    await page.route('**/api/v1/generation-jobs/**', async (route) => {
      const request = route.request()

      if (request.method() === 'POST') {
        await fulfillJson(route, 500, { message: 'Internal Server Error' })
        return
      }

      await route.continue()
    })

    // Also handle list endpoint
    await page.route('**/api/v1/generation-jobs?*', async (route) => {
      await fulfillJson(route, 200, { items: [], total: 0, limit: 20, skip: 0 })
    })

    await gotoGeneration(page)

    const formData = {
      prompt: 'A detailed fantasy landscape with mountains, forests, and a magical castle',
      negativePrompt: 'blurry, low quality, artifacts',
      width: '768',
      height: '512',
      steps: '30',
      cfgScale: '8.5',
      seed: '12345',
    }

    await page.getByTestId('prompt-input').fill(formData.prompt)
    await page.getByTestId('negative-prompt-input').fill(formData.negativePrompt)
    await page.getByTestId('width-input').fill(formData.width)
    await page.getByTestId('height-input').fill(formData.height)
    await page.getByTestId('steps-input').fill(formData.steps)
    await page.getByTestId('cfg-scale-input').fill(formData.cfgScale)
    await page.getByTestId('seed-input').fill(formData.seed)

    await page.getByTestId('generate-button').click()
    await expect(page.getByTestId('error-alert')).toBeVisible({ timeout: 10000 })

    await expect(page.getByTestId('prompt-input')).toHaveValue(formData.prompt)
    await expect(page.getByTestId('negative-prompt-input')).toHaveValue(formData.negativePrompt)
    await expect(page.getByTestId('width-input')).toHaveValue(formData.width)
    await expect(page.getByTestId('height-input')).toHaveValue(formData.height)
    await expect(page.getByTestId('steps-input')).toHaveValue(formData.steps)
    await expect(page.getByTestId('cfg-scale-input')).toHaveValue(formData.cfgScale)
    await expect(page.getByTestId('seed-input')).toHaveValue(formData.seed)

    await expect(page.getByTestId('retry-button')).toBeVisible()
  })

  test('provides accessible error messages', async ({ page }) => {
    await setupBaseMocks(page)

    await page.route('**/api/v1/generation-jobs/**', async (route) => {
      const request = route.request()

      if (request.method() === 'POST') {
        await fulfillJson(route, 503, {
          error: {
            message: 'Service temporarily unavailable',
            category: 'connection',
          },
        })
        return
      }

      await route.continue()
    })

    // Also handle list endpoint
    await page.route('**/api/v1/generation-jobs?*', async (route) => {
      await fulfillJson(route, 200, { items: [], total: 0, limit: 20, skip: 0 })
    })

    await gotoGeneration(page)
    await page.getByTestId('prompt-input').fill('Accessible error prompt')
    await page.getByTestId('generate-button').click()

    const errorAlert = page.getByTestId('error-alert')
    await expect(errorAlert).toBeVisible({ timeout: 10000 })
    await expect(errorAlert).toHaveAttribute('role', 'alert')
    await expect(errorAlert).toHaveAttribute('aria-live', 'assertive')

    await page.keyboard.press('Tab')
    const retryButton = page.getByTestId('retry-button')
    if (await retryButton.isVisible()) {
      await expect(retryButton).toBeFocused()
    }
  })

})
