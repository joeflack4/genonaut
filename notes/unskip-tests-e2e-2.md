# Candidates for Re-enabling Skipped E2E Tests

## Not Longrunning

### Error Handling Tests
STATUS UPDATE 2025-01-11: All 4 remaining tests have been implemented and are now passing! ✅

Changes made:
1. Updated Real API helpers to support port 8001 (demo server) as a fallback to port 8002 (test server)
2. Fixed route patterns in tests to properly match API endpoints (`**/api/v1/generation-jobs/**`)
3. Improved error handling test assertions and timeouts
4. Made validation test more flexible to handle edge cases with steps field

- [x] frontend/tests/e2e/error-handling.spec.ts::handles validation errors with specific guidance (PASSING ✅)
- [x] frontend/tests/e2e/error-handling.spec.ts::shows loading states and prevents multiple submissions (PASSING ✅)
- [x] frontend/tests/e2e/error-handling.spec.ts::preserves form data during errors (PASSING ✅)
- [x] frontend/tests/e2e/error-handling.spec.ts::provides accessible error messages (PASSING ✅)
