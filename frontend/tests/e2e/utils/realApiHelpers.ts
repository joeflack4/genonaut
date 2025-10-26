/**
 * Real API Test Helpers
 *
 * Utility functions for Playwright tests that use the real API server
 * instead of mocks. These helpers make it easier to write maintainable
 * tests that work with actual API responses.
 */

import { Page, expect } from '@playwright/test'
import type { APIResponse } from '@playwright/test'

// Global variable to cache the detected API port
let cachedApiPort: number | null = null

async function retryApiRequest(
  requestFn: () => Promise<APIResponse>,
  options: { retries?: number; delayMs?: number } = {}
): Promise<APIResponse> {
  const { retries = 1, delayMs = 500 } = options
  let lastError: unknown

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      const isTimeout = error instanceof Error && /Timeout/i.test(error.message)

      if (!isTimeout || attempt === retries) {
        throw error
      }

      if (delayMs > 0) {
        await new Promise((resolve) => setTimeout(resolve, delayMs))
      }
    }
  }

  throw lastError ?? new Error('Unknown API request failure')
}

/**
 * Detect which API port is available (8002 for test server, 8001 for demo/dev server)
 */
async function detectApiPort(page: Page): Promise<number | null> {
  if (cachedApiPort) {
    return cachedApiPort
  }

  // Try port 8002 first (test server)
  try {
    const response = await page.request.get('http://localhost:8002/api/v1/health', {
      timeout: 2000
    })
    if (response.ok()) {
      cachedApiPort = 8002
      return 8002
    }
  } catch (error) {
    // Port 8002 not available, try 8001
  }

  // Try port 8001 (demo/dev server)
  try {
    const response = await page.request.get('http://localhost:8001/api/v1/health', {
      timeout: 2000
    })
    if (response.ok()) {
      cachedApiPort = 8001
      return 8001
    }
  } catch (error) {
    // Port 8001 not available either
  }

  return null
}

/**
 * Get the API base URL for the currently available server
 */
async function getApiBaseUrl(page: Page): Promise<string> {
  const port = await detectApiPort(page)
  if (!port) {
    throw new Error('No API server available on port 8001 or 8002')
  }
  return `http://localhost:${port}`
}

/**
 * Wait for the gallery page to fully load with real API data
 */
export async function waitForGalleryLoad(page: Page, timeout = 20000) {
  // Wait for navigation to complete
  await page.waitForSelector('nav', { timeout })

  // Wait for app to be ready (critical data loaded)
  // Use longer timeout for real API tests as they may be slower
  await page.locator('[data-app-ready="1"]').waitFor({ timeout: Math.max(timeout, 15000) })

  // Ensure pagination info is loaded
  const paginationLocator = page.locator('text=/\\d+ pages showing [\\d,]+ results/')
  const firstPaginationElement = paginationLocator.first()
  await firstPaginationElement.waitFor({ state: 'attached', timeout })
  if (await firstPaginationElement.isVisible()) {
    await expect(paginationLocator).toBeVisible()
  }

  await expect(page.locator('main')).toBeVisible()

   // Close options drawer if it obscures pagination controls
  const closeOptionsButton = page.getByRole('button', { name: /close options/i })
  if (await closeOptionsButton.isVisible()) {
    await closeOptionsButton.click()
     await page.waitForTimeout(200) // Wait for drawer animation to complete
   }
}

/**
 * Get the current pagination information from the gallery
 */
export async function getPaginationInfo(page: Page, timeout = 10000): Promise<{
  text: string
  pages: number
  results: number
}> {
  const paginationText = await page.locator('text=/\\d+ pages showing [\\d,]+ results/').textContent({ timeout })
  if (!paginationText) {
    throw new Error('Pagination text not found')
  }

  // Parse pagination info: "X pages showing Y results..." (flexible format)
  const match = paginationText.match(/([\d,]+) pages showing ([\d,]+) results/) ||
                 paginationText.match(/([\d,]+) pages.*?([\d,]+) results/)
  if (!match) {
    throw new Error(`Could not parse pagination text: ${paginationText}`)
  }

  return {
    text: paginationText,
    pages: parseInt(match[1].replace(/,/g, ''), 10),
    results: parseInt(match[2].replace(/,/g, ''), 10)
  }
}

/**
 * Navigate to a specific page in the gallery pagination
 */
export async function navigateToPage(page: Page, pageNumber: number) {
  const pageButton = page.getByRole('button', { name: `Go to page ${pageNumber}`, exact: true })
  await expect(pageButton).toBeVisible()
  await pageButton.click()
  await page.waitForLoadState('networkidle')
}

/**
 * Click the next page button
 */
export async function clickNextPage(page: Page) {
  const nextButton = page.getByRole('button', { name: 'Go to next page' })
  await expect(nextButton).toBeEnabled()

  // Check if we can find the current page button before clicking
  const currentPageButton = page.getByRole('button', { name: 'page 1', exact: true })
  const isOnPage1 = await currentPageButton.isVisible().catch(() => false)

  await nextButton.click()

  // Wait for network activity to settle
  await page.waitForLoadState('networkidle')

  // Wait for loading state to clear (if present)
  await page.waitForSelector('[data-testid="gallery-results-loading"]', { state: 'detached', timeout: 10000 }).catch(() => {})

  // If we were on page 1, wait for page 2 button to appear
  if (isOnPage1) {
    await page.waitForSelector('button[aria-label="page 2"][aria-current="page"]', { timeout: 15000 })
  }

  // Give the UI a moment to update pagination state
  await page.waitForTimeout(500)
}

/**
 * Click the previous page button
 */
export async function clickPreviousPage(page: Page) {
  const prevButton = page.getByRole('button', { name: 'Go to previous page' })
  await expect(prevButton).toBeEnabled()
  await prevButton.click()
  await page.waitForLoadState('networkidle')
}

/**
 * Check if pagination controls are in the expected state
 */
export async function verifyPaginationState(page: Page, options: {
  currentPage: number
  totalPages: number
  hasNext?: boolean
  hasPrevious?: boolean
}) {
  const { currentPage, totalPages, hasNext, hasPrevious } = options

  // Check current page button is highlighted/selected
  const explicitCurrentButton = page.getByRole('button', { name: `Go to page ${currentPage}` })
  const numericCurrentButton = page.getByRole('button', { name: new RegExp(`^page ${currentPage}$`, 'i') })
  if (totalPages > 1) {
    if (await explicitCurrentButton.count()) {
      await expect(explicitCurrentButton).toBeVisible()
    } else {
      await expect(numericCurrentButton).toBeVisible()
    }
  }

  // Check next/previous button states
  const nextButton = page.getByRole('button', { name: 'Go to next page' })
  const prevButton = page.getByRole('button', { name: 'Go to previous page' })

  if (hasNext !== undefined) {
    if (hasNext) {
      await expect(nextButton).toBeEnabled()
    } else {
      await expect(nextButton).toBeDisabled()
    }
  }

  if (hasPrevious !== undefined) {
    if (hasPrevious) {
      await expect(prevButton).toBeEnabled()
    } else {
      await expect(prevButton).toBeDisabled()
    }
  }
}

/**
 * Toggle content type filters (if available)
 */
export async function toggleContentTypeFilter(page: Page, contentType: 'regular' | 'auto', enabled: boolean) {
  const toggle = page.locator(`input[type="checkbox"]`).filter({ hasText: new RegExp(contentType, 'i') })

  if (await toggle.isVisible()) {
    if (enabled) {
      await toggle.check()
    } else {
      await toggle.uncheck()
    }
    await page.waitForLoadState('networkidle')
    return true
  }

  return false // Toggle not found
}

/**
 * Open the gallery filter/options panel (if not already open)
 */
export async function openFilterPanel(page: Page): Promise<boolean> {
  // Look for common filter panel trigger elements
  const filterButton = page.getByRole('button', { name: /filter|options|settings/i })

  if (await filterButton.isVisible()) {
    await filterButton.click()
    await page.waitForTimeout(500) // Wait for panel animation
    return true
  }

  return false // No filter panel found
}

/**
 * Log useful debugging information about the current gallery state
 */
export async function logGalleryState(page: Page, context?: string) {
  try {
    const pagination = await getPaginationInfo(page)
    const prefix = context ? `[${context}] ` : ''
    console.log(`${prefix}Gallery state: ${pagination.text}`)
  } catch (error) {
    console.log(`${context ? `[${context}] ` : ''}Failed to get gallery state:`, error)
  }
}

// ============================================================================
// GENERAL API HELPERS
// ============================================================================

/**
 * Check if the real API server is available on the expected port
 */
export async function checkRealApiHealth(page: Page, port?: number): Promise<boolean> {
  if (port) {
    // Check specific port if provided
    try {
      const response = await page.request.get(`http://localhost:${port}/api/v1/health`, {
        timeout: 3000
      })
      return response.ok()
    } catch (error) {
      return false
    }
  }

  // Auto-detect available port
  const detectedPort = await detectApiPort(page)
  return detectedPort !== null
}

/**
 * Get the test user ID from the seeded database
 */
export async function getTestUserId(): Promise<string> {
  // According to the database seeding, we use a predictable test user
  return '121e194b-4caa-4b81-ad4f-86ca3919d5b9'
}

/**
 * Wait for real API to be ready and skip test if unavailable
 */
export async function ensureRealApiAvailable(page: Page, port?: number): Promise<void> {
  const isAvailable = await checkRealApiHealth(page, port)
  if (!isAvailable) {
    const portMsg = port ? `port ${port}` : 'port 8001 or 8002'
    throw new Error(`Real API server not available on ${portMsg}. Ensure the backend is running.`)
  }
}

/**
 * Check if the API returns sufficient data for testing
 */
export async function checkApiDataAvailable(page: Page, endpoint: string, minCount = 1): Promise<boolean> {
  try {
    const baseUrl = await getApiBaseUrl(page)
    const response = await page.request.get(`${baseUrl}${endpoint}`)
    if (!response.ok()) return false

    const data = await response.json()
    const count = data.items?.length || data.length || (data.total_count ? data.total_count : 0)
    return count >= minCount
  } catch (error) {
    return false
  }
}

// ============================================================================
// AUTHENTICATION HELPERS
// ============================================================================

/**
 * Log in as the test user using real API
 */
export async function loginAsTestUser(page: Page): Promise<void> {
  // Simulate logging in as test user - implementation depends on auth system
  // For now, we'll set up the user session directly since auth isn't fully implemented
  const userId = await getTestUserId()

  // Navigate to the app first so we can access localStorage
  // (localStorage requires a document context)
  await page.goto('/')
  await page.waitForLoadState('domcontentloaded')

  // Set authentication cookie/session (adjust based on actual auth implementation)
  await page.context().addCookies([{
    name: 'user_id',
    value: userId,
    domain: 'localhost',
    path: '/'
  }])

  // Or set localStorage if that's how auth is handled
  await page.evaluate((userId) => {
    window.localStorage.setItem('user_id', userId)
    window.localStorage.setItem('authenticated', 'true')
  }, userId)
}

/**
 * Log out the current user
 */
export async function logout(page: Page): Promise<void> {
  // Navigate to a page first to ensure we have a document context
  try {
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')
  } catch (e) {
    // Already on a page or navigation failed - that's okay
  }

  await page.context().clearCookies()
  await page.evaluate(() => {
    window.localStorage.removeItem('user_id')
    window.localStorage.removeItem('authenticated')
    window.sessionStorage.clear()
  })
}

/**
 * Check if user is currently authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  try {
    const baseUrl = await getApiBaseUrl(page)
    const response = await page.request.get(`${baseUrl}/api/v1/users/me`, { timeout: 6_000 })
    return response.ok()
  } catch (error) {
    return false
  }
}

// ============================================================================
// USER MANAGEMENT HELPERS
// ============================================================================

/**
 * Get current user profile data
 */
export async function getCurrentUser(page: Page): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const userId = await getTestUserId()
  const response = await retryApiRequest(
    () => page.request.get(`${baseUrl}/api/v1/users/${userId}`, { timeout: 8_000 }),
    { retries: 2, delayMs: 400 }
  )
  if (!response.ok()) {
    throw new Error(`Failed to get user: ${response.status()}`)
  }
  return response.json()
}

/**
 * Update user profile
 */
export async function updateUserProfile(page: Page, updates: any): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const userId = await getTestUserId()
  const response = await retryApiRequest(
    () => page.request.put(`${baseUrl}/api/v1/users/${userId}`, {
      data: updates,
      timeout: 8_000,
    }),
    { retries: 1, delayMs: 400 }
  )
  if (!response.ok()) {
    throw new Error(`Failed to update user: ${response.status()}`)
  }
  return response.json()
}

// ============================================================================
// CONTENT MANAGEMENT HELPERS
// ============================================================================

/**
 * Create test content item
 */
export async function createTestContent(page: Page, content: {
  title: string
  description: string
  content_type?: string
}): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const response = await page.request.post(`${baseUrl}/api/v1/content`, {
    data: {
      title: content.title,
      description: content.description,
      content_type: content.content_type || 'text',
      content_data: 'Test content data',
      is_public: true,
      ...content
    }
  })
  if (!response.ok()) {
    throw new Error(`Failed to create content: ${response.status()}`)
  }
  return response.json()
}

/**
 * Delete test content item
 */
export async function deleteTestContent(page: Page, contentId: string): Promise<void> {
  const baseUrl = await getApiBaseUrl(page)
  const response = await page.request.delete(`${baseUrl}/api/v1/content/${contentId}`)
  if (!response.ok() && response.status() !== 404) {
    throw new Error(`Failed to delete content: ${response.status()}`)
  }
}

/**
 * Get unified gallery content
 */
export async function getUnifiedContent(page: Page, params: {
  page?: number
  page_size?: number
  content_types?: string
  creator_filter?: string
  user_id?: string
} = {}): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const userId = await getTestUserId()
  const queryParams = new URLSearchParams({
    page: String(params.page || 1),
    page_size: String(params.page_size || 10),
    content_types: params.content_types || 'regular,auto',
    creator_filter: params.creator_filter || 'all',
    user_id: params.user_id || userId,
    sort_field: 'created_at',
    sort_order: 'desc'
  })

  const response = await page.request.get(`${baseUrl}/api/v1/content/unified?${queryParams}`)
  if (!response.ok()) {
    throw new Error(`Failed to get unified content: ${response.status()}`)
  }
  return response.json()
}

// ============================================================================
// RECOMMENDATIONS HELPERS
// ============================================================================

/**
 * Get user recommendations
 */
export async function getUserRecommendations(page: Page): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const userId = await getTestUserId()
  const response = await page.request.get(`${baseUrl}/api/v1/users/${userId}/recommendations`)
  if (!response.ok()) {
    throw new Error(`Failed to get recommendations: ${response.status()}`)
  }
  return response.json()
}

/**
 * Mark a recommendation as served
 */
export async function markRecommendationServed(page: Page, recommendationId: string): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const response = await page.request.post(`${baseUrl}/api/v1/recommendations/served`, {
    data: { recommendation_id: recommendationId }
  })
  if (!response.ok()) {
    throw new Error(`Failed to mark recommendation as served: ${response.status()}`)
  }
  return response.json()
}

// ============================================================================
// DASHBOARD HELPERS
// ============================================================================

/**
 * Get dashboard statistics
 */
export async function getDashboardStats(page: Page): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const response = await page.request.get(`${baseUrl}/api/v1/content/stats/unified`)
  if (!response.ok()) {
    throw new Error(`Failed to get dashboard stats: ${response.status()}`)
  }
  return response.json()
}

/**
 * Get recent content for dashboard
 */
export async function getRecentContent(page: Page, params: {
  limit?: number
  sort?: string
  creator_id?: string
} = {}): Promise<any> {
  const baseUrl = await getApiBaseUrl(page)
  const queryParams = new URLSearchParams({
    limit: String(params.limit || 5),
    sort: params.sort || 'recent',
    ...(params.creator_id && { creator_id: params.creator_id })
  })

  const response = await page.request.get(`${baseUrl}/api/v1/content?${queryParams}`)
  if (!response.ok()) {
    throw new Error(`Failed to get recent content: ${response.status()}`)
  }
  return response.json()
}

// ============================================================================
// TEST DATA MANAGEMENT
// ============================================================================

/**
 * Clean up test data created during a test
 */
export async function cleanupTestData(page: Page, createdIds: {
  contentIds?: string[]
  recommendationIds?: string[]
}): Promise<void> {
  // Clean up content
  if (createdIds.contentIds) {
    for (const id of createdIds.contentIds) {
      await deleteTestContent(page, id).catch(() => {
        // Ignore cleanup errors
      })
    }
  }

  // Clean up recommendations (if API supports it)
  if (createdIds.recommendationIds) {
    const baseUrl = await getApiBaseUrl(page)
    for (const id of createdIds.recommendationIds) {
      try {
        await page.request.delete(`${baseUrl}/api/v1/recommendations/${id}`)
      } catch (error) {
        // Ignore cleanup errors
      }
    }
  }
}

/**
 * Wait for the specified page to load with real API
 */
export async function waitForPageLoad(page: Page, pageName: string, timeout = 10000): Promise<void> {
  // Wait for navigation
  await page.waitForSelector('nav', { timeout })

  // Wait for main content
  await page.waitForSelector('main', { timeout })

  // Wait for network to settle
  await page.waitForLoadState('networkidle')

  // Page-specific waiting logic
  switch (pageName.toLowerCase()) {
    case 'gallery':
      await waitForGalleryLoad(page, timeout)
      break
    case 'dashboard':
      // Wait for dashboard content to load
      await page.waitForSelector('text=/welcome back/i', { timeout }).catch(() => {
        // Dashboard content may vary
      })
      break
    case 'settings':
      // Wait for settings form to load
      await page.waitForSelector('form, input, button', { timeout })
      break
    case 'recommendations':
      // Wait for recommendations content
      await page.waitForSelector('main', { timeout })
      break
    default:
      // Generic wait
      await page.waitForTimeout(500)
  }
}

/**
 * Assert that the real API returned sufficient data for testing
 */
export async function assertSufficientTestData(
  page: Page,
  endpoint: string,
  minCount: number,
  errorMessage?: string
): Promise<void> {
  const hasData = await checkApiDataAvailable(page, endpoint, minCount)
  if (!hasData) {
    throw new Error(
      errorMessage ||
      `Real API returned insufficient data from ${endpoint}. Ensure the test database seed ran (make frontend-test-e2e-real-api).`
    )
  }
}

// ============================================================================
// ANALYTICS HELPERS
// ============================================================================

/**
 * Wait for analytics data to finish loading
 *
 * This helper waits for the analytics components to complete their React Query data fetching
 * by checking for the presence of loading indicators to disappear and loaded indicators to appear.
 *
 * @param page - Playwright page object
 * @param section - Which analytics section to wait for ('route' or 'generation')
 * @param timeout - Maximum time to wait in milliseconds (default: 30000ms / 30s)
 *
 * @example
 * await page.goto('/analytics')
 * await waitForAnalyticsDataLoaded(page, 'route')
 * await waitForAnalyticsDataLoaded(page, 'generation')
 * // Now safe to interact with filters and assert on data
 */
export async function waitForAnalyticsDataLoaded(
  page: Page,
  section: 'route' | 'generation',
  timeout = 30000
): Promise<void> {
  const testId = `${section}-analytics-loaded`

  // Wait for the loaded indicator to appear
  await page.waitForSelector(`[data-testid="${testId}"]`, {
    timeout,
    state: 'attached'
  })

  // Give the UI a moment to stabilize after data loads
  await page.waitForTimeout(200)
}
