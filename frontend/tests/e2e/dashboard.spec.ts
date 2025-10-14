import { test, expect } from '@playwright/test'
import { setupMockApi } from './utils/mockApi'

const ADMIN_USER_ID = '121e194b-4caa-4b81-ad4f-86ca3919d5b9'

test.describe('Dashboard', () => {
  test('shows gallery stats and recent content', async ({ page }) => {
    const now = new Date().toISOString()

    const userContent = {
      id: 101,
      title: 'User Content Item',
      description: 'Content created by user',
      image_url: null,
      path_thumb: null,
      content_type: 'image',
      content_data: '/static/user-item.png',
      item_metadata: {},
      creator_id: ADMIN_USER_ID,
      creator_username: 'admin',
      tags: ['featured'],
      is_public: true,
      is_private: false,
      quality_score: 0.92,
      created_at: now,
      updated_at: now,
      prompt: 'User generated prompt',
    }

    const communityContent = {
      id: 202,
      title: 'Surreal Landscape',
      description: 'AI art piece',
      image_url: null,
      path_thumb: null,
      content_type: 'image',
      content_data: '/static/community-item.png',
      item_metadata: {},
      creator_id: 'community-user',
      creator_username: 'community-member',
      tags: ['community'],
      is_public: true,
      is_private: false,
      quality_score: 0.88,
      created_at: now,
      updated_at: now,
      prompt: 'Community prompt',
    }

    const communityAutoContent = {
      ...communityContent,
      id: 303,
      title: 'Community Auto Piece',
      content_type: 'image',
      content_data: '/static/community-auto.png',
    }

    await setupMockApi(page, [
      {
        pattern: String.raw`/api/v1/users/${ADMIN_USER_ID}$`,
        method: 'GET',
        body: {
          id: ADMIN_USER_ID,
          name: 'Admin',
          email: 'admin@example.com',
          is_active: true,
          created_at: now,
          updated_at: now,
        },
      },
      {
        pattern: String.raw`/api/v1/content/stats/unified.*`,
        method: 'GET',
        body: {
          user_regular_count: 1,
          user_auto_count: 1,
          community_regular_count: 3,
          community_auto_count: 2,
        },
      },
      {
        pattern: String.raw`/api/v1/content\?limit=5.*sort=recent.*creator_id=${ADMIN_USER_ID}`,
        method: 'GET',
        body: {
          items: [userContent],
          total: 1,
          limit: 5,
          skip: 0,
        },
      },
      {
        pattern: String.raw`/api/v1/content\?limit=20.*sort=recent(?!.*creator_id)` ,
        method: 'GET',
        body: {
          items: [communityContent],
          total: 3,
          limit: 20,
          skip: 0,
        },
      },
      {
        pattern: String.raw`/api/v1/content-auto\?limit=5.*sort=recent.*creator_id=${ADMIN_USER_ID}`,
        method: 'GET',
        body: {
          items: [
            {
              ...userContent,
              id: 111,
              title: 'User Auto Item',
              content_type: 'image',
              content_data: '/static/user-auto.png',
            },
          ],
          total: 1,
          limit: 5,
          skip: 0,
        },
      },
      {
        pattern: String.raw`/api/v1/content-auto\?limit=20.*sort=recent(?!.*creator_id)` ,
        method: 'GET',
        body: {
          items: [communityAutoContent],
          total: 2,
          limit: 20,
          skip: 0,
        },
      },
    ])

    await page.goto('/dashboard')
    await page.waitForSelector('[data-testid="dashboard-page-root"]', { timeout: 15000 })

    await expect(page.getByTestId('dashboard-header-title')).toContainText('Welcome back')

    await expect(page.getByTestId('dashboard-stat-card-userGalleryCount-value')).toHaveText('1')
    await expect(page.getByTestId('dashboard-stat-card-userAutoGalleryCount-value')).toHaveText('1')
    await expect(page.getByTestId('dashboard-stat-card-totalGalleryCount-value')).toHaveText('3')
    await expect(page.getByTestId('dashboard-stat-card-totalAutoGalleryCount-value')).toHaveText('2')

    await expect(page.getByTestId('dashboard-user-recent-title')).toBeVisible()
    await expect(page.getByTestId('dashboard-user-autogens-title')).toBeVisible()
    await expect(page.getByTestId('dashboard-community-recent-title')).toBeVisible()
    await expect(page.getByTestId('dashboard-community-autogens-title')).toBeVisible()

    // Default view is grid, so check grid views instead of list views
    await expect(page.getByTestId('dashboard-user-recent-grid')).toBeVisible()
    await expect(page.getByTestId('dashboard-user-autogens-grid')).toBeVisible()
    await expect(page.getByTestId('dashboard-community-recent-grid')).toBeVisible()
    await expect(page.getByTestId('dashboard-community-autogens-grid')).toBeVisible()
  })
})
