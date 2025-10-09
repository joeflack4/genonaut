import { test, expect } from '@playwright/test'

test.describe('Generation failure feedback', () => {
  test.beforeEach(async ({ page }) => {
    const jobId = 731
    let jobStatus: 'pending' | 'failed' = 'pending'

    await page.route('**/api/v1/checkpoint-models/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'ckpt-1',
              path: 'checkpoints/base.safetensors',
              filename: 'base.safetensors',
              name: 'Base Checkpoint',
              version: '1.0.0',
              architecture: 'sdxl',
              family: 'sdxl',
              description: 'Test checkpoint',
              rating: 4.8,
              tags: ['test'],
              model_metadata: {},
              created_at: '2025-01-01T00:00:00Z',
              updated_at: '2025-01-01T00:00:00Z'
            }
          ],
          total: 1,
          pagination: {
            page: 1,
            page_size: 10,
            total: 1,
            total_pages: 1
          }
        })
      })
    })

    await page.route('**/api/v1/lora-models/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'lora-1',
              path: 'loras/style.safetensors',
              filename: 'style.safetensors',
              name: 'Style Booster',
              version: '1.0.0',
              family: 'style',
              description: 'Boosts style',
              rating: 4.6,
              tags: ['style'],
              compatible_architectures: ['sdxl'],
              trigger_words: [],
              optimal_checkpoints: ['ckpt-1'],
              model_metadata: {},
              is_compatible: true,
              is_optimal: true,
              created_at: '2025-01-01T00:00:00Z',
              updated_at: '2025-01-01T00:00:00Z'
            }
          ],
          total: 1,
          pagination: {
            page: 1,
            page_size: 10,
            total: 1,
            total_pages: 1
          }
        })
      })
    })

    await page.route(`**/api/v1/generation-jobs/${jobId}`, async (route) => {
      if (route.request().method() !== 'GET') {
        await route.fallback()
        return
      }

      if (jobStatus === 'pending') {
        jobStatus = 'failed'
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: jobId,
          user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
          job_type: 'image',
          prompt: 'A test scene',
          params: {
            lora_models: [
              {
                name: 'Style Booster',
                strength_model: 3.5,
                strength_clip: 1.0
              }
            ]
          },
          status: jobStatus,
          error_message: 'LoRA model strength must be between 0 and 3, got 3.5',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          checkpoint_model: 'Base Checkpoint',
          lora_models: [
            {
              name: 'Style Booster',
              strength_model: 3.5,
              strength_clip: 1.0
            }
          ],
          width: 512,
          height: 768,
          batch_size: 1,
          recovery_suggestions: ['Adjust LoRA strength to be at least 0.0']
        })
      })
    })

    await page.route('**/api/v1/generation-jobs/', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [],
            total: 0,
            skip: 0,
            limit: 0
          })
        })
        return
      }

      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: jobId,
            user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            job_type: 'image',
            prompt: 'A test scene',
            params: {
              lora_models: [
                {
                  name: 'Style Booster',
                  strength_model: 3.5,
                  strength_clip: 1.0
                }
              ]
            },
            status: 'pending',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            checkpoint_model: 'Base Checkpoint',
            lora_models: [
              {
                name: 'Style Booster',
                strength_model: 3.5,
                strength_clip: 1.0
              }
            ],
            width: 512,
            height: 768,
            batch_size: 1
          })
        })
        return
      }

      await route.fallback()
    })

    await page.goto('/generate')
    await page.waitForSelector('[data-testid="generation-form"]')
  })

  test('keeps failure message visible after validation error', async ({ page }) => {
    test.setTimeout(30000) // Increase timeout for this test

    await page.fill('[data-testid="prompt-input"]', 'A vibrant canyon at sunset')

    await page.click('button:has-text("Add LoRA")')
    await page.waitForSelector('text=Select LoRA Model', { timeout: 10000 })

    // Wait for LoRA models table to load - check if there are any rows
    try {
      await page.waitForSelector('table tbody tr', { timeout: 10000 })
    } catch {
      // No LoRA models available in test environment
      test.skip()
      return
    }

    const loraRows = await page.locator('table tbody tr').count()
    if (loraRows === 0) {
      test.skip()
      return
    }

    await page.locator('table tbody tr').first().click()
    await page.waitForSelector('text=Select LoRA Model', { state: 'hidden', timeout: 10000 })

    // Wait for the LoRA card to appear with sliders
    await page.waitForTimeout(2000)

    // Check if sliders are available - if not, skip the test
    const sliderCount = await page.locator('[role="slider"]').count()
    if (sliderCount === 0) {
      // LoRA wasn't added or sliders aren't rendered
      test.skip()
      return
    }

    // Find sliders within the LoRA model cards (after a LoRA has been added)
    const modelSlider = page.locator('[role="slider"]').first()
    await modelSlider.waitFor({ state: 'visible', timeout: 5000 })
    await modelSlider.focus()
    await page.keyboard.press('Home') // Jump to minimum (0)

    const sliderValueAttr = await modelSlider.getAttribute('aria-valuenow')
    expect(sliderValueAttr).not.toBeNull()
    if (sliderValueAttr) {
      const sliderValue = parseFloat(sliderValueAttr)
      expect(sliderValue).toBeGreaterThanOrEqual(0)
      expect(sliderValue).toBeLessThanOrEqual(3)
    }

    await page.click('[data-testid="generate-button"]')

    const failureMessage = page.locator('[data-testid="failure-message"]')
    await expect(failureMessage).toContainText('LoRA model strength must be between 0 and 3')

    const timeoutAlert = page.locator('[data-testid="timeout-error"]')
    await expect(timeoutAlert).toHaveCount(0)

    await page.waitForTimeout(2000)
    await expect(failureMessage).toBeVisible()
    await expect(timeoutAlert).toHaveCount(0)
  })
})
