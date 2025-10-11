# Frontend E2E Tests - Skipped Stability Tests

These are core UX tests that should work but are currently skipped due to test implementation issues, not missing features. They are worth fixing.

**Status:** All 4 tests are currently skipped in `frontend/tests/e2e/error-handling.spec.ts`

**Goal:** Fix these tests to validate important user experience features

---

## Test 1: "handles validation errors with specific guidance"

### Location
`frontend/tests/e2e/error-handling.spec.ts` line 146

### What it tests
When a user submits invalid form values (width=0, steps=0), the backend returns 422 validation errors and the UI should:
- Show field-specific error messages below each invalid field
- Highlight invalid fields with error styling (`.error` class)
- NOT highlight valid fields (prompt should not have error class)

### Current behavior
**Failing because:**
- Backend validation messages don't match test expectations
- Test expects: "between 64 and 2048" and "between 1 and 150"
- Backend actually returns: "Input should be greater than or equal to 64" and similar messages
- Steps error may not be appearing because steps input is in a collapsed accordion

### How to fix
1. **Update test expectations** to match actual backend error format:
   ```typescript
   // Change from:
   await expect(page.getByTestId('width-error')).toHaveText(/between 64 and 2048/i)
   await expect(page.getByTestId('steps-error')).toHaveText(/between 1 and 150/i)

   // To:
   await expect(page.getByTestId('width-error')).toContainText(/64/i)
   await expect(page.getByTestId('steps-error')).toContainText(/1/i)
   ```

2. **Ensure advanced settings accordion is expanded** before checking steps error:
   ```typescript
   // Before filling steps, ensure accordion is open
   const accordion = page.locator('[data-testid="advanced-settings-accordion"]')
   if (!(await accordion.isVisible())) {
     await page.click('[data-testid="advanced-settings-header"]')
   }
   ```

3. **Verify error display timing** - may need to wait for validation to complete after submit

### Test value
**HIGH** - Form validation is a core UX feature. Users need clear feedback on what's wrong with their input.

---

## Test 2: "shows loading states and prevents multiple submissions"

### Location
`frontend/tests/e2e/error-handling.spec.ts` line 203

### What it tests
When a user clicks the Generate button:
- Button should show "Generating..." text with a loading spinner
- Button should be disabled during generation
- Clicking the button again during generation should NOT send another request
- Should only send exactly 1 POST request

### Current behavior
**Failing because:**
- `createCalls` counter stays at 0, meaning the mock route never fires
- The POST request isn't being intercepted by the mock
- Could be a route pattern matching issue or timing issue

### How to fix
1. **Debug route pattern** - verify the pattern actually matches:
   ```typescript
   await page.route('**/api/v1/generation-jobs/**', async (route) => {
     console.log('Route matched:', route.request().url())
     // ... rest of mock
   })
   ```

2. **Use page.waitForRequest** to confirm POST is actually sent:
   ```typescript
   const [request] = await Promise.all([
     page.waitForRequest(req =>
       req.url().includes('/generation-jobs') && req.method() === 'POST'
     ),
     generateButton.click(),
   ])
   expect(request).toBeTruthy()
   ```

3. **Alternative: Track via page.on('request')** instead of route handler counter:
   ```typescript
   let postCount = 0
   page.on('request', req => {
     if (req.url().includes('/generation-jobs') && req.method() === 'POST') {
       postCount++
     }
   })
   ```

4. **Check button actually submits form** - the generate button might use `onClick` instead of form submission

### Test value
**HIGH** - Preventing duplicate submissions is important to avoid wasting resources and confusing users.

---

## Test 3: "preserves form data during errors"

### Location
`frontend/tests/e2e/error-handling.spec.ts` line 328

### What it tests
When a generation request fails (500 error), all form fields should retain their values:
- prompt, negativePrompt, width, height, steps, cfgScale, seed
- Users can immediately retry without re-entering everything

### Current behavior
**Failing because:**
- The error isn't actually showing up (error-alert not visible)
- Same root cause as Test 1 - the 503 mock response isn't triggering the error display
- Once error shows, the form persistence should work automatically (uses `usePersistedState`)

### How to fix
1. **First fix error display** - ensure 500 response triggers error state:
   ```typescript
   // Verify the mock is firing
   let mockFired = false
   await page.route('**/api/v1/generation-jobs*', async (route) => {
     if (request.method() === 'POST') {
       mockFired = true
       console.log('500 error mock fired')
       // ... fulfill with 500
     }
   })

   await generateButton.click()
   expect(mockFired).toBe(true) // Verify mock actually ran
   ```

2. **Wait for error with proper timeout**:
   ```typescript
   await expect(page.getByTestId('error-alert')).toBeVisible({ timeout: 10000 })
   ```

3. **If error displays but values don't persist**, check localStorage:
   ```typescript
   const storedPrompt = await page.evaluate(() =>
     localStorage.getItem('generation-form-prompt')
   )
   expect(storedPrompt).toBe(formData.prompt)
   ```

### Test value
**MEDIUM-HIGH** - Important UX feature. Losing form data on error is frustrating, especially for long prompts.

---

## Test 4: "provides accessible error messages"

### Location
`frontend/tests/e2e/error-handling.spec.ts` line 476

### What it tests
Error messages follow accessibility standards:
- Error alert has `role="alert"` attribute
- Error alert has `aria-live="assertive"` attribute
- Retry button is keyboard accessible (Tab key focuses it after error appears)

### Current behavior
**Failing because:**
- Same as tests 1 and 3 - the error-alert isn't showing up
- Once error displays, the accessibility attributes should already be there (they're in the UI code)

### How to fix
1. **Fix error display first** (same as Test 3)

2. **Verify ARIA attributes** are present in the GenerationForm component:
   ```typescript
   // Check frontend/src/components/generation/GenerationForm.tsx line 544-548
   // Should have:
   <Alert
     severity="error"
     role="alert"
     aria-live="assertive"
     data-testid="error-alert"
   >
   ```

3. **Test keyboard focus** after error appears:
   ```typescript
   await page.getByTestId('generate-button').click()
   await expect(page.getByTestId('error-alert')).toBeVisible()

   // Focus should naturally move to first interactive element
   await page.keyboard.press('Tab')
   const retryButton = page.getByTestId('retry-button')
   await expect(retryButton).toBeFocused()
   ```

4. **If focus doesn't move automatically**, add focus management to error display:
   ```typescript
   // In GenerationForm component, when error state changes:
   useEffect(() => {
     if (errorState.type !== 'none') {
       // Focus the retry button
       document.querySelector('[data-testid="retry-button"]')?.focus()
     }
   }, [errorState])
   ```

### Test value
**MEDIUM** - Accessibility is important, but this is a polish feature. Fix after other tests work.

---

## Summary

### Fix order (recommended)
1. **Test 2** (loading states) - Easiest to fix, just need to debug route matching
2. **Test 1** (validation) - Update expectations to match backend format
3. **Test 3** (form preservation) - Depends on error display working
4. **Test 4** (accessibility) - Depends on error display working

### Common issues across tests
- **Error display not triggering**: Several tests mock error responses but the UI error state isn't showing
- **Route mocks not firing**: Need to verify route patterns match actual request URLs
- **Timing issues**: May need longer waits for async state updates

### Testing approach
1. Start by adding debug logging to confirm mocks fire
2. Use browser DevTools to inspect actual requests/responses during test
3. Check that UI components actually have the expected test IDs
4. Verify state updates happen before making assertions
