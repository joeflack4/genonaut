import { test, expect } from '@playwright/test'
import {
  ensureRealApiAvailable,
  assertSufficientTestData,
  loginAsTestUser,
  waitForPageLoad,
  getDashboardStats,
  getRecentContent,
  getTestUserId
} from './utils/realApiHelpers'

test.describe('Dashboard (Real API)', () => {
  test.beforeEach(async ({ page }) => {
    // Check if real API is available, skip if not
    try {
      await ensureRealApiAvailable(page)
    } catch (error) {
      test.skip(true, 'Real API server not available on port 8002. Run with: npm run test:e2e:real-api')
      return
    }

    // Ensure we have sufficient test data
    try {
      await assertSufficientTestData(page, '/api/v1/content/unified?page=1&page_size=1', 1)
    } catch (error) {
      test.skip(true, 'Real API returned zero gallery results. Ensure the test database seed ran (make frontend-test-e2e-real-api).')
      return
    }

    // Log in as test user for dashboard access
    await loginAsTestUser(page)
  })

  test('shows gallery stats and recent content', async ({ page }) => {
    // Get expected data from API
    const stats = await getDashboardStats(page)
    expect(stats).toBeTruthy()

    const userId = await getTestUserId()
    const userRecentContent = await getRecentContent(page, { limit: 5, creator_id: userId })
    const communityRecentContent = await getRecentContent(page, { limit: 5 })

    // Navigate to dashboard
    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Should show welcome message
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()

    // Should show gallery statistics
    // The dashboard should display user and community content counts
    const expectedStats = [
      stats.user_regular_count?.toString(),
      stats.user_auto_count?.toString(),
      stats.community_regular_count?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','), // Add commas
      stats.community_auto_count?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    ].filter(Boolean)

    // Look for these numbers in the dashboard
    let statsFound = 0
    for (const statValue of expectedStats) {
      if (statValue && await page.getByText(statValue).count() > 0) {
        statsFound++
      }
    }

    // Should find at least some of the expected statistics
    expect(statsFound).toBeGreaterThan(0)

    // Should show content type labels
    const contentLabels = [
      page.getByText(/your gens/i),
      page.getByText(/your auto-gens/i),
      page.getByText(/community gens/i),
      page.getByText(/community auto-gens/i)
    ]

    let labelsFound = 0
    for (const label of contentLabels) {
      if (await label.count() > 0) {
        labelsFound++
      }
    }

    expect(labelsFound).toBeGreaterThan(0)

    // Should show recent content sections
    const recentSections = [
      page.getByRole('heading', { name: /your recent gens/i }),
      page.getByRole('heading', { name: /your recent auto-gens/i }),
      page.getByRole('heading', { name: /community recent gens/i }),
      page.getByRole('heading', { name: /community recent auto-gens/i })
    ]

    let sectionsFound = 0
    for (const section of recentSections) {
      if (await section.count() > 0) {
        sectionsFound++
      }
    }

    expect(sectionsFound).toBeGreaterThan(0)

    // Should show actual content items if available
    if (userRecentContent.items?.length > 0) {
      // Look for user's content
      const userContentTitle = userRecentContent.items[0].title
      if (userContentTitle) {
        await expect(page.getByText(userContentTitle).first()).toBeVisible()
      }
    }

    if (communityRecentContent.items?.length > 0) {
      // Look for community content
      const communityContentTitle = communityRecentContent.items[0].title
      if (communityContentTitle) {
        // Community content might be displayed
        const communityContent = page.getByText(communityContentTitle)
        if (await communityContent.count() > 0) {
          await expect(communityContent.first()).toBeVisible()
        }
      }
    }
  })

  test('displays correct user vs community statistics', async ({ page }) => {
    // Get stats from API
    const stats = await getDashboardStats(page)

    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Verify user content counts are displayed correctly
    if (stats.user_regular_count > 0) {
      const userRegularDisplay = page.getByText(stats.user_regular_count.toString())
      await expect(userRegularDisplay).toBeVisible()
    }

    if (stats.user_auto_count > 0) {
      const userAutoDisplay = page.getByText(stats.user_auto_count.toString())
      await expect(userAutoDisplay).toBeVisible()
    }

    // Verify community content counts (likely large numbers with commas)
    if (stats.community_regular_count > 999) {
      const formattedCommunityRegular = stats.community_regular_count.toLocaleString()
      const communityRegularDisplay = page.getByText(formattedCommunityRegular)
      if (await communityRegularDisplay.count() > 0) {
        await expect(communityRegularDisplay).toBeVisible()
      }
    }

    if (stats.community_auto_count > 999) {
      const formattedCommunityAuto = stats.community_auto_count.toLocaleString()
      const communityAutoDisplay = page.getByText(formattedCommunityAuto)
      if (await communityAutoDisplay.count() > 0) {
        await expect(communityAutoDisplay).toBeVisible()
      }
    }

    // Verify the distinction between user and community content is clear
    await expect(page.getByText(/your/i)).toHaveCount({ min: 1 })
    await expect(page.getByText(/community/i)).toHaveCount({ min: 1 })
  })

  test('recent content sections load correctly', async ({ page }) => {
    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // All recent content sections should have headers
    const expectedSections = [
      'Your recent gens',
      'Your recent auto-gens',
      'Community recent gens',
      'Community recent auto-gens'
    ]

    let foundSections = 0
    for (const sectionName of expectedSections) {
      const section = page.getByRole('heading', { name: new RegExp(sectionName, 'i') })
      if (await section.count() > 0) {
        foundSections++
      }
    }

    // Should have at least 2 sections visible (may depend on data available)
    expect(foundSections).toBeGreaterThanOrEqual(2)

    // If there's content available, some sections should show actual items
    const userId = await getTestUserId()
    const userContent = await getRecentContent(page, { limit: 1, creator_id: userId })

    if (userContent.items?.length > 0) {
      // User should have some content displayed
      const contentTitle = userContent.items[0].title
      if (contentTitle) {
        await expect(page.getByText(contentTitle).first()).toBeVisible()
      }
    }

    // Test that sections are properly organized
    const headings = await page.getByRole('heading', { level: 2 }).allTextContents()
    const validHeadings = headings.filter(heading =>
      expectedSections.some(section =>
        section.toLowerCase().includes(heading.toLowerCase()) ||
        heading.toLowerCase().includes(section.toLowerCase())
      )
    )

    expect(validHeadings.length).toBeGreaterThan(0)
  })

  test('dashboard navigation and responsiveness', async ({ page }) => {
    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Dashboard should be responsive and functional
    await expect(page.locator('main')).toBeVisible()

    // Should be able to navigate from dashboard to other sections
    const navigationLinks = [
      { href: '/gallery', label: 'Gallery' },
      { href: '/settings', label: 'Settings' },
      { href: '/recommendations', label: 'Recommendations' }
    ]

    for (const { href, label } of navigationLinks) {
      const link = page.locator(`[href="${href}"]`)
      if (await link.count() > 0) {
        await expect(link).toBeVisible()
        await expect(link).toBeEnabled()
      }
    }

    // Test clicking on one navigation item
    await page.click('[href="/gallery"]')
    await expect(page).toHaveURL('/gallery')

    // Navigate back to dashboard
    await page.click('[href="/dashboard"]')
    await expect(page).toHaveURL('/dashboard')
    await waitForPageLoad(page, 'dashboard')
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
  })

  test('handles real-time data updates gracefully', async ({ page }) => {
    await page.goto('/dashboard')
    await waitForPageLoad(page, 'dashboard')

    // Capture initial state
    const initialStats = await getDashboardStats(page)

    // Refresh the page and verify data consistency
    await page.reload()
    await waitForPageLoad(page, 'dashboard')

    // Dashboard should still show the same data after refresh
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()

    // Check that the same statistics are still displayed
    if (initialStats.user_regular_count > 0) {
      await expect(page.getByText(initialStats.user_regular_count.toString())).toBeVisible()
    }

    // Verify that the page handles data loading gracefully
    // (no broken images, missing content, or error states)
    const errorElements = [
      page.getByText(/error/i),
      page.getByText(/failed/i),
      page.getByText(/not found/i),
      page.locator('[alt*="error"], [alt*="broken"]')
    ]

    for (const errorElement of errorElements) {
      await expect(errorElement).not.toBeVisible()
    }
  })
})