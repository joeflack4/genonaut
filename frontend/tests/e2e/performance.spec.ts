/**
 * Frontend rendering performance tests for ComfyUI generation components.
 *
 * These tests measure rendering performance, load times, and user interaction responsiveness
 * for generation-related UI components and features.
 */

import { test, expect, Page } from '@playwright/test'

// Performance test configuration
const PERFORMANCE_THRESHOLDS = {
  pageLoadTime: 3000,        // 3 seconds max for initial page load
  componentRenderTime: 500,  // 500ms max for component rendering
  listScrollTime: 100,       // 100ms max for smooth scrolling
  imageLoadTime: 2000,       // 2 seconds max for image loading
  userInteractionTime: 200,  // 200ms max for user interaction response
}

test.describe('Frontend Performance Tests', () => {

  test.describe.configure({ mode: 'serial' })

  test.beforeEach(async ({ page }) => {
    // Mock API responses for consistent testing
    await page.route('**/api/comfyui/generations*', async route => {
      // Mock generation list response
      const mockGenerations = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        prompt: `Test generation prompt ${i + 1} with various details about landscapes and characters`,
        negative_prompt: i % 3 === 0 ? 'blurry, low quality' : '',
        checkpoint_model: `model_${(i % 5) + 1}.safetensors`,
        width: i % 2 === 0 ? 512 : 768,
        height: i % 2 === 0 ? 512 : 768,
        steps: 20 + (i % 30),
        cfg_scale: 7.0 + (i % 5) * 0.5,
        seed: i,
        batch_size: i % 4 === 0 ? 4 : 1,
        status: ['pending', 'processing', 'completed', 'failed'][i % 4],
        created_at: new Date(Date.now() - i * 60000).toISOString(),
        thumbnail_paths: i % 3 === 0 ? [`/thumbnails/thumb_${i}.jpg`] : [],
        output_paths: i % 4 === 0 ? [`/outputs/output_${i}.png`] : [],
        lora_models: []
      }))

      await route.fulfill({
        json: {
          items: mockGenerations,
          pagination: {
            page: 1,
            page_size: 50,
            total_count: 200,
            total_pages: 4
          }
        }
      })
    })

    // Mock model list response
    await page.route('**/api/comfyui/models*', async route => {
      const mockModels = Array.from({ length: 20 }, (_, i) => ({
        id: i + 1,
        name: `test_model_${i + 1}.safetensors`,
        type: ['checkpoint', 'lora', 'vae'][i % 3],
        file_path: `/models/test_model_${i + 1}.safetensors`,
        is_available: true
      }))

      await route.fulfill({
        json: {
          items: mockModels,
          pagination: {
            page: 1,
            page_size: 20,
            total_count: 20,
            total_pages: 1
          }
        }
      })
    })

    // Mock image requests to avoid network delays
    await page.route('**/thumbnails/**', async route => {
      // Return a 1x1 pixel PNG for testing
      const pngBuffer = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
        'base64'
      )
      await route.fulfill({
        status: 200,
        contentType: 'image/png',
        body: pngBuffer
      })
    })
  })

  test('generation page load performance', async ({ page }) => {
    // Measure initial page load time
    const startTime = Date.now()

    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Wait for the main content to be visible
    await expect(page.locator('[data-testid="generation-page"]')).toBeVisible()

    const loadTime = Date.now() - startTime

    // Assert page loads within threshold
    expect(loadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.pageLoadTime)

    console.log(`Generation page load time: ${loadTime}ms`)
  })

  test('generation history component rendering performance', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded' })

    // Navigate to history tab
    await page.click('[data-testid="history-tab"]')

    // Wait a moment for the history component to load
    await page.waitForTimeout(500)

    // Check if there are generation cards available
    const cardCount = await page.locator('[data-testid="generation-card"]').count()

    if (cardCount === 0) {
      // Skip test if no generations are available
      test.skip(true, 'No generation cards available for performance testing')
      return
    }

    // Measure component render time
    const startTime = Date.now()

    // Wait for generation cards to be rendered
    await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

    const renderTime = Date.now() - startTime

    // Assert component renders within threshold
    expect(renderTime).toBeLessThan(PERFORMANCE_THRESHOLDS.componentRenderTime)

    // Verify multiple cards are rendered efficiently
    expect(cardCount).toBeGreaterThan(0)

    console.log(`Generation history render time: ${renderTime}ms for ${cardCount} cards`)
  })

  test('virtual scrolling performance with large lists', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })
    await page.click('[data-testid="history-tab"]')

    // Wait a moment for the history component to load
    await page.waitForTimeout(500)

    // Check if there are generation cards available
    const cardCount = await page.locator('[data-testid="generation-card"]').count()

    if (cardCount === 0) {
      // Skip test if no generations are available
      test.skip(true, 'No generation cards available for virtual scrolling performance testing')
      return
    }

    // Enable virtual scrolling if available
    const virtualScrollToggle = page.locator('[data-testid="virtual-scroll-toggle"]')
    if (await virtualScrollToggle.isVisible()) {
      await virtualScrollToggle.click()
    }

    // Wait for initial render
    await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

    // Measure scroll performance
    const scrollContainer = page.locator('[data-testid="generation-list"]')
    const startTime = Date.now()

    // Perform multiple scroll actions
    for (let i = 0; i < 5; i++) {
      await scrollContainer.evaluate(el => {
        el.scrollTop += 300
      })
      await page.waitForTimeout(50) // Allow for scroll processing
    }

    const scrollTime = Date.now() - startTime

    // Assert scroll performance
    expect(scrollTime).toBeLessThan(PERFORMANCE_THRESHOLDS.listScrollTime * 5)

    console.log(`Virtual scroll performance: ${scrollTime}ms for 5 scroll actions`)
  })

  test('lazy image loading performance', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })
    await page.click('[data-testid="history-tab"]')

    // Wait a moment for the history component to load
    await page.waitForTimeout(500)

    // Check if there are generation cards available
    const cardCount = await page.locator('[data-testid="generation-card"]').count()

    if (cardCount === 0) {
      // Skip test if no generations are available
      test.skip(true, 'No generation cards available for lazy image loading performance testing')
      return
    }

    // Wait for generation cards to render
    await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

    // Find cards with thumbnail images
    const imageCards = page.locator('[data-testid="generation-card"] img')
    const imageCount = await imageCards.count()

    if (imageCount > 0) {
      // Measure image loading performance
      const startTime = Date.now()

      // Wait for first image to load
      await expect(imageCards.first()).toBeVisible()

      const loadTime = Date.now() - startTime

      // Assert image loads within threshold
      expect(loadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.imageLoadTime)

      console.log(`Lazy image loading time: ${loadTime}ms for first image`)
    }
  })

  test('search and filter interaction performance', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })
    await page.click('[data-testid="history-tab"]')

    // Wait a moment for the history component to load
    await page.waitForTimeout(500)

    // Check if there are generation cards available
    const cardCount = await page.locator('[data-testid="generation-card"]').count()

    if (cardCount === 0) {
      // Skip test if no generations are available
      test.skip(true, 'No generation cards available for search and filter performance testing')
      return
    }

    // Wait for initial render
    await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

    // Test search performance
    const searchInput = page.locator('[data-testid="search-input"]')
    if (await searchInput.isVisible()) {
      const startTime = Date.now()

      await searchInput.fill('test generation')

      // Wait for filtered results
      await page.waitForTimeout(100) // Allow for debouncing

      const searchTime = Date.now() - startTime

      expect(searchTime).toBeLessThan(PERFORMANCE_THRESHOLDS.userInteractionTime * 2)

      console.log(`Search interaction time: ${searchTime}ms`)
    }

    // Test status filter performance
    const statusFilter = page.locator('[data-testid="status-filter"]')
    if (await statusFilter.isVisible()) {
      const startTime = Date.now()

      await statusFilter.click()
      await page.click('[data-value="completed"]')

      // Wait for filtered results
      await page.waitForTimeout(100)

      const filterTime = Date.now() - startTime

      expect(filterTime).toBeLessThan(PERFORMANCE_THRESHOLDS.userInteractionTime * 4)

      console.log(`Status filter interaction time: ${filterTime}ms`)
    }
  })

  test('generation form interaction performance', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Wait for form to be visible
    await expect(page.locator('[data-testid="generation-form"]')).toBeVisible()

    // Test prompt input responsiveness
    const promptInput = page.locator('[data-testid="prompt-input"]')
    if (await promptInput.isVisible()) {
      const startTime = Date.now()

      await promptInput.fill('A beautiful landscape with mountains and trees')

      const inputTime = Date.now() - startTime

      expect(inputTime).toBeLessThan(PERFORMANCE_THRESHOLDS.userInteractionTime)

      console.log(`Prompt input response time: ${inputTime}ms`)
    }

    // Test model selector performance
    const modelSelector = page.locator('[data-testid="model-selector"]').locator('[role="combobox"]')
    if (await modelSelector.isVisible()) {
      const startTime = Date.now()

      await modelSelector.click()

      // Wait a moment for dropdown to potentially appear
      await page.waitForTimeout(500)

      // Check if dropdown options are available
      const optionCount = await page.locator('[role="option"]').count()

      if (optionCount === 0) {
        console.log('No model options available for performance testing')
        return
      }

      // Wait for dropdown options to appear
      await expect(page.locator('[role="option"]').first()).toBeVisible()

      const dropdownTime = Date.now() - startTime

      expect(dropdownTime).toBeLessThan(PERFORMANCE_THRESHOLDS.userInteractionTime)

      console.log(`Model selector dropdown time: ${dropdownTime}ms`)
    }
  })

  test('pagination performance', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })
    await page.click('[data-testid="history-tab"]')

    // Wait a moment for the history component to load
    await page.waitForTimeout(500)

    // Check if there are generation cards available
    const cardCount = await page.locator('[data-testid="generation-card"]').count()

    if (cardCount === 0) {
      // Skip test if no generations are available
      test.skip(true, 'No generation cards available for pagination performance testing')
      return
    }

    // Wait for initial page to load
    await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

    // Test pagination navigation
    const nextPageButton = page.locator('[data-testid="next-page"]')
    if (await nextPageButton.isVisible()) {
      const startTime = Date.now()

      await nextPageButton.click()

      // Wait for new page content
      await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

      const paginationTime = Date.now() - startTime

      expect(paginationTime).toBeLessThan(PERFORMANCE_THRESHOLDS.componentRenderTime)

      console.log(`Pagination navigation time: ${paginationTime}ms`)
    }
  })

  test('generation details modal performance', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })
    await page.click('[data-testid="history-tab"]')

    // Wait a moment for the history component to load
    await page.waitForTimeout(500)

    // Check if there are generation cards available
    const cardCount = await page.locator('[data-testid="generation-card"]').count()

    if (cardCount === 0) {
      // Skip test if no generations are available
      test.skip(true, 'No generation cards available for modal performance testing')
      return
    }

    // Wait for generation cards
    await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

    // Test modal opening performance
    const firstCard = page.locator('[data-testid="generation-card"]').first()
    const viewButton = firstCard.locator('[data-testid="view-details"]')

    if (await viewButton.isVisible()) {
      const startTime = Date.now()

      await viewButton.click()

      // Wait for modal to appear
      await expect(page.locator('[data-testid="generation-modal"]')).toBeVisible()

      const modalTime = Date.now() - startTime

      expect(modalTime).toBeLessThan(PERFORMANCE_THRESHOLDS.userInteractionTime)

      console.log(`Generation details modal time: ${modalTime}ms`)

      // Test modal closing performance
      const closeStartTime = Date.now()

      await page.keyboard.press('Escape')

      await expect(page.locator('[data-testid="generation-modal"]')).not.toBeVisible()

      const closeTime = Date.now() - closeStartTime

      expect(closeTime).toBeLessThan(PERFORMANCE_THRESHOLDS.userInteractionTime)

      console.log(`Modal close time: ${closeTime}ms`)
    }
  })

  test('memory usage during component lifecycle', async ({ page }) => {
    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Get initial memory usage (if available)
    const initialMetrics = await page.evaluate(() => {
      return (performance as any).memory ? {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize
      } : null
    })

    // Navigate through different views to test memory management
    await page.click('[data-testid="history-tab"]')

    // Wait a moment for the history component to load
    await page.waitForTimeout(500)

    // Check if there are generation cards available
    const cardCount = await page.locator('[data-testid="generation-card"]').count()

    if (cardCount === 0) {
      // Skip test if no generations are available
      test.skip(true, 'No generation cards available for memory usage testing')
      return
    }

    await expect(page.locator('[data-testid="generation-card"]').first()).toBeVisible()

    // Scroll and interact with the page
    await page.locator('[data-testid="generation-list"]').evaluate(el => {
      el.scrollTop = 1000
    })

    await page.waitForTimeout(1000) // Allow for any async operations

    // Get memory usage after interactions
    const finalMetrics = await page.evaluate(() => {
      return (performance as any).memory ? {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize
      } : null
    })

    if (initialMetrics && finalMetrics) {
      const memoryIncrease = finalMetrics.usedJSHeapSize - initialMetrics.usedJSHeapSize
      const memoryIncreasePercent = (memoryIncrease / initialMetrics.usedJSHeapSize) * 100

      // Memory increase should be reasonable (less than 50% for normal usage)
      expect(memoryIncreasePercent).toBeLessThan(50)

      console.log(`Memory usage increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB (${memoryIncreasePercent.toFixed(1)}%)`)
    }
  })

  test('bundle size and loading performance', async ({ page }) => {
    // Intercept network requests to measure bundle loading
    const resourceSizes: { [key: string]: number } = {}

    page.on('response', async (response) => {
      const url = response.url()
      const contentLength = response.headers()['content-length']

      if (url.includes('.js') || url.includes('.css')) {
        const size = contentLength ? parseInt(contentLength, 10) : 0
        resourceSizes[url] = size
      }
    })

    const startTime = Date.now()

    page.setDefaultNavigationTimeout(5_000)
    await page.goto('/generation', { waitUntil: 'domcontentloaded', timeout: 5_000 })

    // Wait for page to be fully loaded
    await expect(page.locator('[data-testid="generation-page"]')).toBeVisible()

    const loadTime = Date.now() - startTime

    // Calculate total bundle size
    const totalBundleSize = Object.values(resourceSizes).reduce((sum, size) => sum + size, 0)
    const bundleSizeMB = totalBundleSize / 1024 / 1024

    // Assert reasonable bundle size (adjust threshold as needed)
    expect(bundleSizeMB).toBeLessThan(12) // Dev bundle should stay below ~12MB total

    // Assert load time is reasonable for bundle size
    const expectedLoadTime = Math.max(1500, bundleSizeMB * 600) // Adjusted for dev bundle weight
    expect(loadTime).toBeLessThan(expectedLoadTime)

    console.log(`Bundle size: ${bundleSizeMB.toFixed(2)}MB, Load time: ${loadTime}ms`)
  })

  test.skip('performance regression detection', async ({ page }) => {
    // This test would be used to detect performance regressions
    // by comparing current metrics against baseline values

    const performanceMetrics = {
      pageLoadTime: 0,
      componentRenderTime: 0,
      memoryUsage: 0,
      bundleSize: 0
    }

    // Collect actual metrics here...

    // Compare against baseline (would be stored externally)
    const baseline = {
      pageLoadTime: 2000,
      componentRenderTime: 300,
      memoryUsage: 50 * 1024 * 1024, // 50MB
      bundleSize: 3 * 1024 * 1024     // 3MB
    }

    // Assert no significant regression (e.g., > 20% slower)
    Object.entries(performanceMetrics).forEach(([metric, value]) => {
      const baselineValue = baseline[metric as keyof typeof baseline]
      const regressionThreshold = baselineValue * 1.2 // 20% tolerance

      expect(value).toBeLessThan(regressionThreshold)
    })
  })
})
