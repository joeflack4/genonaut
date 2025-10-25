/**
 * Test Data Helpers
 *
 * Utilities for handling missing test data in E2E tests.
 *
 * By default, tests fail when data is missing (to indicate a real problem).
 * Set E2E_SKIP_ON_MISSING_DATA=true to skip tests gracefully instead.
 */

/**
 * Check if tests should skip gracefully when data is missing.
 *
 * Default: false (tests should fail when data is missing)
 * Set E2E_SKIP_ON_MISSING_DATA=true to skip instead
 */
export function shouldSkipOnMissingData(): boolean {
  return process.env.E2E_SKIP_ON_MISSING_DATA === 'true'
}

/**
 * Handle missing test data by either skipping or failing the test.
 *
 * @param test - Playwright test object
 * @param testName - Name of the test for error messages
 * @param dataType - Type of data that's missing (e.g., "gallery data", "tags")
 * @param fixCommand - Optional command to fix the issue
 *
 * @example
 * if (!hasResults) {
 *   handleMissingData(
 *     test,
 *     'Gallery display test',
 *     'gallery data (content_items)',
 *     'make init-demo && python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target demo'
 *   )
 * }
 */
export function handleMissingData(
  test: any,
  testName: string,
  dataType: string,
  fixCommand?: string
): void {
  const message = `Test database missing ${dataType}`
  const fullMessage = fixCommand
    ? `${message}\n\nTo fix, run:\n${fixCommand}\n\nOr see: docs/testing.md#e2e-test-setup`
    : `${message}\n\nSee: docs/testing.md#e2e-test-setup`

  if (shouldSkipOnMissingData()) {
    test.skip(true, fullMessage)
  } else {
    throw new Error(fullMessage)
  }
}
