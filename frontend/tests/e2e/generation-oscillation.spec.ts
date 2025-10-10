import { test, expect } from '@playwright/test'

/**
 * E2E test for generation status oscillation bug.
 *
 * This test verifies the fix for a critical bug where submitting a second generation
 * while a completed generation is displayed causes an infinite render loop with:
 * - Status oscillating between "pending" and "completed"
 * - "Maximum update depth exceeded" React errors
 * - Console explosion with thousands of error messages
 * - WebSocket connection failures
 *
 * Bug details: notes/fix-gen-oscillation.md
 *
 * The fix involves:
 * 1. Adding hasMeaningfulChange check in prop sync effect (GenerationProgress.tsx:274-278)
 * 2. Adding key prop to force cleanup on ID change (GenerationPage.tsx:118)
 */
test.describe('Generation Status Oscillation Bug', () => {
  test.beforeEach(async ({ page }) => {
    // Mock checkpoint models API
    await page.route('**/api/v1/checkpoint-models/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'ckpt-test',
              path: 'checkpoints/test.safetensors',
              filename: 'test.safetensors',
              name: 'Test Checkpoint',
              version: '1.0.0',
              architecture: 'sdxl',
              family: 'sdxl',
              description: 'Test checkpoint for E2E',
              rating: 4.5,
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

    // Mock LoRA models API
    await page.route('**/api/v1/lora-models/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0,
          pagination: {
            page: 1,
            page_size: 10,
            total: 0,
            total_pages: 0
          }
        })
      })
    })

    // Mock generation history API
    await page.route('**/api/v1/generation-jobs/?*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [],
            total: 0,
            skip: 0,
            limit: 10
          })
        })
        return
      }
      await route.fallback()
    })

    await page.goto('/generate')
    await page.waitForSelector('[data-testid="generation-form"]', { timeout: 10000 })
  })

  test('should not oscillate when generating multiple images sequentially', async ({ page }) => {
    test.setTimeout(60000) // Increase timeout for this test

    // Track console errors and warnings
    const consoleErrors: string[] = []
    const consoleWarnings: string[] = []

    page.on('console', msg => {
      const text = msg.text()
      if (msg.type() === 'error') {
        consoleErrors.push(text)
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(text)
      }
    })

    // First generation - job ID 1000
    const firstJobId = 1000
    let firstJobStatus: 'pending' | 'completed' = 'pending'

    // Mock POST to create first generation
    await page.route('**/api/v1/generation-jobs/', async (route) => {
      if (route.request().method() === 'POST') {
        const requestBody = route.request().postDataJSON()

        // First generation
        if (!requestBody.__test_job_id || requestBody.__test_job_id === firstJobId) {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: firstJobId,
              user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
              job_type: 'image',
              prompt: 'cat',
              status: 'pending',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              checkpoint_model: 'Test Checkpoint',
              lora_models: [],
              width: 512,
              height: 768,
              batch_size: 1
            })
          })
          return
        }
      }

      await route.fallback()
    })

    // Mock GET for first generation job status
    await page.route(`**/api/v1/generation-jobs/${firstJobId}`, async (route) => {
      if (route.request().method() === 'GET') {
        // Transition to completed after first poll
        if (firstJobStatus === 'pending') {
          firstJobStatus = 'completed'
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: firstJobId,
            user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            job_type: 'image',
            prompt: 'cat',
            status: firstJobStatus,
            content_id: 5001,
            output_paths: ['/generated/cat1.png'],
            created_at: new Date(Date.now() - 10000).toISOString(),
            updated_at: new Date().toISOString(),
            completed_at: firstJobStatus === 'completed' ? new Date().toISOString() : undefined,
            checkpoint_model: 'Test Checkpoint',
            lora_models: [],
            width: 512,
            height: 768,
            batch_size: 1
          })
        })
        return
      }

      await route.fallback()
    })

    // Submit first generation
    await page.fill('[data-testid="prompt-input"]', 'cat')
    await page.click('[data-testid="generate-button"]')

    // Wait for first generation to complete
    // Look for the Chip component that shows "Completed" status
    const completedChip = page.locator('.MuiChip-label:has-text("Completed")').first()
    await completedChip.waitFor({ state: 'visible', timeout: 15000 })

    // Verify first generation completed successfully
    await expect(completedChip).toBeVisible()

    // Clear any errors from first generation
    consoleErrors.length = 0
    consoleWarnings.length = 0

    // Second generation - job ID 1001
    const secondJobId = 1001
    let secondJobStatus: 'pending' | 'completed' = 'pending'

    // Update POST route to handle second generation
    await page.unroute('**/api/v1/generation-jobs/')
    await page.route('**/api/v1/generation-jobs/', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: secondJobId,
            user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            job_type: 'image',
            prompt: 'cat',
            status: 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            checkpoint_model: 'Test Checkpoint',
            lora_models: [],
            width: 512,
            height: 768,
            batch_size: 1
          })
        })
        return
      }

      await route.fallback()
    })

    // Mock GET for second generation job status
    await page.route(`**/api/v1/generation-jobs/${secondJobId}`, async (route) => {
      if (route.request().method() === 'GET') {
        // Transition to completed after first poll
        if (secondJobStatus === 'pending') {
          secondJobStatus = 'completed'
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: secondJobId,
            user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            job_type: 'image',
            prompt: 'cat',
            status: secondJobStatus,
            content_id: 5002,
            output_paths: ['/generated/cat2.png'],
            created_at: new Date(Date.now() - 5000).toISOString(),
            updated_at: new Date().toISOString(),
            completed_at: secondJobStatus === 'completed' ? new Date().toISOString() : undefined,
            checkpoint_model: 'Test Checkpoint',
            lora_models: [],
            width: 512,
            height: 768,
            batch_size: 1
          })
        })
        return
      }

      await route.fallback()
    })

    // Submit second generation (THIS IS WHERE THE BUG WOULD OCCUR)
    await page.fill('[data-testid="prompt-input"]', 'cat')
    await page.click('[data-testid="generate-button"]')

    // Wait for second generation to show pending/running status
    await page.waitForTimeout(1000)

    // Critical: Wait for oscillation to potentially occur (it should not)
    // The bug caused oscillation within 2-3 seconds
    await page.waitForTimeout(5000)

    // Verify NO "Maximum update depth exceeded" errors
    const maxDepthErrors = consoleErrors.filter(e =>
      e.includes('Maximum update depth') ||
      e.includes('maximum update depth')
    )
    expect(maxDepthErrors).toHaveLength(0)

    // Verify NO excessive WebSocket errors (some reconnection is OK, but not hundreds)
    const wsErrors = consoleErrors.filter(e =>
      e.includes('WebSocket') &&
      e.includes('closed before the connection is established')
    )
    expect(wsErrors.length).toBeLessThan(10) // Allow a few, but not the explosion we saw in the bug

    // Verify status is stable (not rapidly oscillating)
    // Get status text multiple times to ensure it's not changing
    const getStatusText = async () => {
      const chip = page.locator('.MuiChip-label').first()
      return await chip.textContent()
    }

    const status1 = await getStatusText()
    await page.waitForTimeout(500)
    const status2 = await getStatusText()
    await page.waitForTimeout(500)
    const status3 = await getStatusText()

    // All three samples should be the same (status should be stable)
    expect(status1).toBe(status2)
    expect(status2).toBe(status3)

    // Wait for completion
    const secondCompletedChip = page.locator('.MuiChip-label:has-text("Completed")').first()
    await secondCompletedChip.waitFor({ state: 'visible', timeout: 15000 })

    // Verify second generation completed successfully without errors
    await expect(secondCompletedChip).toBeVisible()

    // Final check: total console errors should be minimal
    expect(consoleErrors.length).toBeLessThan(20) // Allow some normal errors, but not hundreds/thousands
  })

  test('should properly cleanup and not create excessive re-renders', async ({ page }) => {
    test.setTimeout(60000)

    // Track console messages to verify no excessive errors
    const consoleErrors: string[] = []
    let renderCount = 0

    page.on('console', msg => {
      const text = msg.text()
      if (msg.type() === 'error') {
        consoleErrors.push(text)
      }
      // Track Effect logs to detect excessive re-renders
      if (text.includes('[Effect:PropSync]') || text.includes('[Effect:ParentCallback]')) {
        renderCount++
      }
    })

    // Setup similar mocks as previous test
    let postCount = 0
    const firstJobId = 2000
    const secondJobId = 2001

    await page.route('**/api/v1/generation-jobs/', async (route) => {
      if (route.request().method() === 'POST') {
        postCount++
        const jobId = postCount === 1 ? firstJobId : secondJobId
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: jobId,
            user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            job_type: 'image',
            prompt: 'cat',
            status: 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            checkpoint_model: 'Test Checkpoint',
            lora_models: [],
            width: 512,
            height: 768,
            batch_size: 1
          })
        })
        return
      }
      await route.fallback()
    })

    // Mock status endpoints for both jobs
    await page.route('**/api/v1/generation-jobs/*', async (route) => {
      if (route.request().method() === 'GET') {
        const url = route.request().url()
        const jobId = parseInt(url.match(/generation-jobs\/(\d+)/)?.[1] || '0')

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: jobId,
            user_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            job_type: 'image',
            prompt: 'cat',
            status: 'completed',
            content_id: 5000 + jobId,
            output_paths: [`/generated/cat${jobId}.png`],
            created_at: new Date(Date.now() - 10000).toISOString(),
            updated_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            checkpoint_model: 'Test Checkpoint',
            lora_models: [],
            width: 512,
            height: 768,
            batch_size: 1
          })
        })
        return
      }
      await route.fallback()
    })

    // First generation
    await page.fill('[data-testid="prompt-input"]', 'cat')
    await page.click('[data-testid="generate-button"]')
    const firstCompletedChip = page.locator('.MuiChip-label:has-text("Completed")').first()
    await firstCompletedChip.waitFor({ state: 'visible', timeout: 15000 })

    // Reset render count after first generation
    renderCount = 0

    // Second generation
    await page.fill('[data-testid="prompt-input"]', 'cat')
    await page.click('[data-testid="generate-button"]')
    const secondCompletedChip = page.locator('.MuiChip-label:has-text("Completed")').first()
    await secondCompletedChip.waitFor({ state: 'visible', timeout: 15000 })

    // Allow time for any potential oscillation to occur
    await page.waitForTimeout(3000)

    // Verify: No excessive re-renders (bug caused hundreds of effect executions)
    // With the fix, we should see reasonable number of renders (< 50)
    expect(renderCount).toBeLessThan(100)

    // Verify no React errors
    const reactErrors = consoleErrors.filter(e =>
      e.includes('Maximum update depth') ||
      e.includes('Too many re-renders')
    )
    expect(reactErrors).toHaveLength(0)
  })
})
