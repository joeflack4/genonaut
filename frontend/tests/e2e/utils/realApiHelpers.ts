/**
 * Real API Test Helpers
 *
 * Utility functions for Playwright tests that use the real API server
 * instead of mocks. These helpers make it easier to write maintainable
 * tests that work with actual API responses.
 */

import { Page, expect } from '@playwright/test'

/**
 * Wait for the gallery page to fully load with real API data
 */
export async function waitForGalleryLoad(page: Page, timeout = 10000) {
  // Wait for navigation to complete
  await page.waitForSelector('nav', { timeout })

  // Wait for any API calls to settle
  await page.waitForLoadState('networkidle')

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
export async function getPaginationInfo(page: Page): Promise<{
  text: string
  pages: number
  results: number
}> {
  const paginationText = await page.locator('text=/\\d+ pages showing [\\d,]+ results/').textContent()
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
  await nextButton.click()
  await page.waitForLoadState('networkidle')
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
export async function checkRealApiHealth(page: Page, port = 8002): Promise<boolean> {
  try {
    const response = await page.request.get(`http://localhost:${port}/api/v1/health`, {
      timeout: 3000
    })
    return response.ok()
  } catch (error) {
    return false
  }
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
export async function ensureRealApiAvailable(page: Page, port = 8002): Promise<void> {
  const isAvailable = await checkRealApiHealth(page, port)
  if (!isAvailable) {
    throw new Error(`Real API server not available on port ${port}. Run with: npm run test:e2e:real-api`)
  }
}

/**
 * Check if the API returns sufficient data for testing
 */
export async function checkApiDataAvailable(page: Page, endpoint: string, minCount = 1): Promise<boolean> {
  try {
    const response = await page.request.get(`http://localhost:8002${endpoint}`)
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
    const response = await page.request.get('http://localhost:8002/api/v1/users/me')
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
  const userId = await getTestUserId()
  const response = await page.request.get(`http://localhost:8002/api/v1/users/${userId}`)
  if (!response.ok()) {
    throw new Error(`Failed to get user: ${response.status()}`)
  }
  return response.json()
}

/**
 * Update user profile
 */
export async function updateUserProfile(page: Page, updates: any): Promise<any> {
  const userId = await getTestUserId()
  const response = await page.request.put(`http://localhost:8002/api/v1/users/${userId}`, {
    data: updates
  })
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
  const response = await page.request.post('http://localhost:8002/api/v1/content', {
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
  const response = await page.request.delete(`http://localhost:8002/api/v1/content/${contentId}`)
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

  const response = await page.request.get(`http://localhost:8002/api/v1/content/unified?${queryParams}`)
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
  const userId = await getTestUserId()
  const response = await page.request.get(`http://localhost:8002/api/v1/users/${userId}/recommendations`)
  if (!response.ok()) {
    throw new Error(`Failed to get recommendations: ${response.status()}`)
  }
  return response.json()
}

/**
 * Mark a recommendation as served
 */
export async function markRecommendationServed(page: Page, recommendationId: string): Promise<any> {
  const response = await page.request.post('http://localhost:8002/api/v1/recommendations/served', {
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
  const response = await page.request.get('http://localhost:8002/api/v1/content/stats/unified')
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
  const queryParams = new URLSearchParams({
    limit: String(params.limit || 5),
    sort: params.sort || 'recent',
    ...(params.creator_id && { creator_id: params.creator_id })
  })

  const response = await page.request.get(`http://localhost:8002/api/v1/content?${queryParams}`)
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
    for (const id of createdIds.recommendationIds) {
      try {
        await page.request.delete(`http://localhost:8002/api/v1/recommendations/${id}`)
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
