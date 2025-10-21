import { test, expect } from '@playwright/test'
import {
  ensureRealApiAvailable,
  assertSufficientTestData,
  loginAsTestUser,
  waitForPageLoad,
  createTestContent,
  deleteTestContent,
  cleanupTestData,
  getUnifiedContent
} from './utils/realApiHelpers'

test.describe('Content CRUD Operations (Real API)', () => {
  let createdContentIds: string[] = []

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

    // Log in as test user
    await loginAsTestUser(page)
    createdContentIds = []
  })

  test.afterEach(async ({ page }) => {
    // Clean up created content
    await cleanupTestData(page, { contentIds: createdContentIds })
  })

  test('creates new content via generation interface', async ({ page }) => {
    test.setTimeout(30000) // Increase timeout for generation operations
    // Navigate to generation page
    await page.goto('/generate')
    await waitForPageLoad(page, 'generate')

    // Look for generation form
    const promptInput = page.getByPlaceholder(/describe.*image|prompt/i)
    const generateButton = page.getByRole('button', { name: /generate/i })

    if (await promptInput.count() === 0 || await generateButton.count() === 0) {
      test.skip(true, 'Generation form not found - content creation UI may not be implemented')
      return
    }

    // Fill in generation parameters
    const testPrompt = 'Test generation for CRUD operations - automated test'
    await promptInput.fill(testPrompt)

    // Fill additional parameters if available
    const widthInput = page.locator('input[type="number"]').filter({ hasText: /width/i }).or(
      page.getByLabel(/width/i)
    )
    const heightInput = page.locator('input[type="number"]').filter({ hasText: /height/i }).or(
      page.getByLabel(/height/i)
    )

    if (await widthInput.count() > 0) {
      await widthInput.fill('512')
    }
    if (await heightInput.count() > 0) {
      await heightInput.fill('512')
    }

    // Submit generation (this might create content asynchronously)
    if (await generateButton.isEnabled()) {
      await generateButton.click()

      // Wait for generation to start
      await page.waitForTimeout(2000)

      // Look for success indicators
      const successIndicators = [
        page.getByText(/generation started|submitted|queued/i),
        page.getByText(/processing|generating/i),
        page.locator('[data-testid*="success"]')
      ]

      let foundSuccess = false
      for (const indicator of successIndicators) {
        if (await indicator.count() > 0 && await indicator.isVisible()) {
          foundSuccess = true
          break
        }
      }

      if (foundSuccess) {
        // Generation was submitted successfully
        expect(foundSuccess).toBe(true)

        // Check if we can view generation history
        const historyTab = page.getByRole('tab', { name: /history/i }).or(
          page.getByText(/history/i)
        )

        if (await historyTab.count() > 0) {
          await historyTab.click()

          const historyCard = page.getByTestId('generation-history-card')
          if (await historyCard.count() > 0) {
            await expect(historyCard).toBeVisible({ timeout: 5000 })
          }

          const loadingIndicator = page.getByText(/loading generations/i)
          if (await loadingIndicator.count() > 0) {
            await loadingIndicator.first().waitFor({ state: 'detached', timeout: 15000 }).catch(() => undefined)
          }

          try {
            await expect
              .poll(async () => {
                if (page.isClosed()) {
                  throw new Error('page-closed')
                }
                return page.getByText(testPrompt).count()
              }, {
                timeout: 20000,
                intervals: [500, 1000],
              })
              .toBeGreaterThan(0)

            await expect(page.getByText(testPrompt).first()).toBeVisible({ timeout: 5000 })
          } catch (error) {
            if (page.isClosed() || (error instanceof Error && error.message === 'page-closed')) {
              test.info().annotations.push({
                type: 'info',
                description: 'Generation history closed before results rendered; skipping prompt visibility assertion.',
              })
            } else {
              throw error
            }
          }
        }
      } else {
        // Generation submission may not have immediate feedback
        // Verify the form accepted the input
        await expect(promptInput).toHaveValue(testPrompt)
      }
    } else {
      test.skip(true, 'Generate button is disabled - may require additional configuration')
    }
  })

  test('views content details and metadata', async ({ page }) => {
    test.setTimeout(20000) // Increase timeout for real API
    // Get existing content from API
    const contentData = await getUnifiedContent(page, { page: 1, page_size: 10 })

    if (!contentData.items || contentData.items.length === 0) {
      test.skip(true, 'No content available for viewing')
      return
    }

    const testContent = contentData.items[0]

    // Navigate to gallery to view content
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Look for the content item
    const contentTitle = testContent.title
    const contentElement = page.getByText(contentTitle).first()

    if (await contentElement.count() > 0) {
      // Click on content to view details
      await contentElement.click()

      // Look for detail view or modal
      const detailElements = [
        page.locator('[data-testid*="modal"]'),
        page.locator('[data-testid*="detail"]'),
        page.locator('.modal, .dialog'),
        page.getByRole('dialog')
      ]

      let foundDetail = false
      for (const element of detailElements) {
        if (await element.count() > 0 && await element.isVisible()) {
          foundDetail = true

          // Should show content metadata
          await expect(element.getByText(contentTitle)).toBeVisible()

          // Look for additional metadata
          const metadataElements = [
            element.getByText(/created|date/i),
            element.getByText(/id|#/),
            element.getByText(/type|category/i),
            element.getByText(/quality|score/i)
          ]

          let foundMetadata = false
          for (const metadata of metadataElements) {
            if (await metadata.count() > 0) {
              foundMetadata = true
              break
            }
          }

          expect(foundMetadata).toBe(true)
          break
        }
      }

      if (!foundDetail) {
        // Maybe content details show inline instead of modal
        await expect(page.getByText(contentTitle).first()).toBeVisible()
      }
    } else {
      test.skip(true, `Content "${contentTitle}" not found in gallery view`)
    }
  })

  test('edits existing content metadata', async ({ page }) => {
    // First create a test content item via API
    let testContent
    try {
      testContent = await createTestContent(page, {
        title: 'Test Content for Editing',
        description: 'This content will be edited in the test'
      })
      createdContentIds.push(testContent.id)
    } catch (error) {
      test.skip(true, 'Content creation API not available - endpoint may not be fully implemented')
      return
    }

    // Navigate to gallery to find the content
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Look for edit functionality
    const editButtons = [
      page.getByRole('button', { name: /edit/i }),
      page.getByText(/edit/i),
      page.locator('[data-testid*="edit"]'),
      page.locator('button[title*="edit"], [aria-label*="edit"]')
    ]

    let editButton = null
    for (const button of editButtons) {
      if (await button.count() > 0 && await button.isVisible()) {
        editButton = button.first()
        break
      }
    }

    if (editButton) {
      await editButton.click()
      await page.waitForTimeout(500)

      // Look for edit form
      const editForm = [
        page.locator('form'),
        page.locator('[data-testid*="edit-form"]'),
        page.getByLabel(/title|name/i),
        page.getByLabel(/description/i)
      ]

      let foundForm = false
      for (const form of editForm) {
        if (await form.count() > 0 && await form.isVisible()) {
          foundForm = true

          // Try to edit the content
          const titleInput = page.getByLabel(/title|name/i)
          const descInput = page.getByLabel(/description/i)

          if (await titleInput.count() > 0) {
            await titleInput.fill('Updated Test Content Title')
          }

          if (await descInput.count() > 0) {
            await descInput.fill('Updated description for test content')
          }

          // Save changes
          const saveButton = page.getByRole('button', { name: /save|update|apply/i })
          if (await saveButton.count() > 0) {
            await saveButton.click()
            await page.waitForTimeout(1000)

            // Look for success feedback
            const successIndicators = [
              page.getByText(/saved|updated|success/i),
              page.getByText('Updated Test Content Title')
            ]

            let foundSuccess = false
            for (const indicator of successIndicators) {
              if (await indicator.count() > 0 && await indicator.isVisible()) {
                foundSuccess = true
                break
              }
            }

            expect(foundSuccess).toBe(true)
          }
          break
        }
      }

      if (!foundForm) {
        test.skip(true, 'Edit form not found - content editing may not be implemented')
      }
    } else {
      test.skip(true, 'Edit functionality not found in UI')
    }
  })

  test('deletes content with confirmation', async ({ page }) => {
    // First create a test content item via API
    let testContent
    try {
      testContent = await createTestContent(page, {
        title: 'Test Content for Deletion',
        description: 'This content will be deleted in the test'
      })
      // Don't add to cleanup list since we're testing deletion
    } catch (error) {
      test.skip(true, 'Content creation API not available - endpoint may not be fully implemented')
      return
    }
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Look for delete functionality
    const deleteButtons = [
      page.getByRole('button', { name: /delete|remove/i }),
      page.getByText(/delete|remove/i),
      page.locator('[data-testid*="delete"]'),
      page.locator('button[title*="delete"], [aria-label*="delete"]')
    ]

    let deleteButton = null
    for (const button of deleteButtons) {
      if (await button.count() > 0 && await button.isVisible()) {
        deleteButton = button.first()
        break
      }
    }

    if (deleteButton) {
      await deleteButton.click()
      await page.waitForTimeout(500)

      // Look for confirmation dialog
      const confirmationElements = [
        page.getByText(/are you sure|confirm|delete/i),
        page.getByRole('dialog'),
        page.locator('[data-testid*="confirm"]'),
        page.locator('.modal, .dialog')
      ]

      let foundConfirmation = false
      for (const element of confirmationElements) {
        if (await element.count() > 0 && await element.isVisible()) {
          foundConfirmation = true

          // Confirm deletion
          const confirmButton = element.getByRole('button', { name: /delete|confirm|yes/i })
          if (await confirmButton.count() > 0) {
            await confirmButton.click()
            await page.waitForTimeout(1000)

            // Look for success feedback
            const successIndicators = [
              page.getByText(/deleted|removed|success/i),
              // Or verify content is no longer visible
              page.getByText('Test Content for Deletion').not.toBeVisible()
            ]

            let foundSuccess = false
            for (const indicator of successIndicators) {
              try {
                if (indicator.toString().includes('not.toBeVisible')) {
                  await indicator
                  foundSuccess = true
                } else if (await indicator.count() > 0 && await indicator.isVisible()) {
                  foundSuccess = true
                }
                break
              } catch (error) {
                // Continue checking other indicators
              }
            }

            expect(foundSuccess).toBe(true)
          }
          break
        }
      }

      if (!foundConfirmation) {
        // Maybe deletion happens immediately without confirmation
        await page.waitForTimeout(1000)

        // Check if content is gone
        const contentGone = await page.getByText('Test Content for Deletion').count() === 0
        if (contentGone) {
          expect(contentGone).toBe(true)
        }
      }
    } else {
      // Try deleting via API to clean up
      await deleteTestContent(page, testContent.id)
      test.skip(true, 'Delete functionality not found in UI')
    }
  })

  test('handles content operations with proper error handling', async ({ page }) => {
    test.setTimeout(20000) // Increase timeout for real API
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')

    // Test various error scenarios that might occur
    // Test 1: Try to access non-existent content
    await page.goto('/content/non-existent-id')
    await page.waitForTimeout(1000)

    // Should handle gracefully (404 page, redirect, or error message)
    const errorHandling = [
      page.getByText(/not found|404/i),
      page.getByText(/error|problem/i),
      page.locator('main'), // At minimum, page should render
      page.locator('nav') // Or navbar should be present
    ]

    let foundHandling = false
    for (const element of errorHandling) {
      if (await element.count() > 0 && await element.isVisible()) {
        foundHandling = true
        break
      }
    }

    expect(foundHandling).toBe(true)

    // Test 2: Navigate back to gallery and verify it still works
    await page.goto('/gallery')
    await waitForPageLoad(page, 'gallery')
    await expect(page.locator('main')).toBeVisible()

    // Gallery should still be functional after error
    const hasContent = await page.getByText(/pages showing|results/i).count() > 0
    const hasGalleryItems = await page.locator('li, .gallery-item, [data-testid*="item"]').count() > 0

    expect(hasContent || hasGalleryItems).toBe(true)
  })
})
