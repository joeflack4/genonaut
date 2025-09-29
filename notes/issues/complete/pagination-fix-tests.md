# Backend tests
All passing.

# Frontend tests
## Unit tests
All passing.

## Failing E2E playwright tests
### Test tracker
### UI Interaction and Viewport Issues
These tests fail due to timing, viewport, and element stability issues during complex user interactions, particularly with Material-UI components that may animate or change position during interaction.

#### Medium Effort
- [x] **content type toggles update pagination correctly** - Test fails when trying to uncheck the "Your auto-gens" switch because the element becomes "outside of the viewport" during the interaction. Despite adding `scrollIntoViewIfNeeded()` and `force: true` options, the Material-UI Switch component within the drawer sidebar isn't stable enough for reliable interaction. The drawer may be animating, the switch may be repositioning, or there may be timing issues with the options panel opening. Fix requires better wait strategies (wait for animations to complete), potentially using different selectors (clicking the FormControlLabel instead of the input), or adjusting the drawer's CSS to prevent layout shifts during interaction.

### Log
make frontend-test-e2e
Running frontend Playwright tests...
npm --prefix frontend run test:e2e

> frontend@0.0.0 test:e2e
> playwright test


Running 59 tests using 5 workers

  -   1 …tests/e2e/auth.spec.ts:5:8 › Auth pages › redirects logged-in user from login to dashboard
  -   2 …/e2e/auth.spec.ts:131:8 › Auth pages › keeps unauthenticated visitor on signup placeholder
  -   3 …um] › tests/e2e/dashboard.spec.ts:5:8 › Dashboard › shows gallery stats and recent content
  ✓   4 …c.ts:4:3 › Form UX Tests › should handle form field focus states on generation page (3.8s)
  -   5 …ium] › tests/e2e/gallery.spec.ts:5:8 › Gallery page › filters gallery items by search term
  ✘   6 …allery page › Gallery Pagffination › displays correct total count and page navigation (3.7s)
  ✓   7 …:3 › Frontend Error Handling › displays user-friendly error when API is unavailable (4.0s)
  -   8 …tests/e2e/generation.spec.ts:7:8 › ComfyUI Generation › should navigate to generation page
  -   9 …ts/e2e/generation.spec.ts:34:8 › ComfyUI Generation › should validate required form fields
  ✓  10 …tion.spec.ts:51:3 › ComfyUI Generation › should show generation parameters controls (4.0s)
  ✓  11 …pec.ts:7:3 › Accessibility Tests › should support comprehensive keyboard navigation (4.3s)
  ✓  12 …e/forms.spec.ts:33:3 › Form UX Tests › should validate form submission requirements (1.7s)
  -  13 ….spec.ts:73:3 › Frontend Error Handling › handles validation errors with specific guidance
     14 ….spec.ts:7:3 › Loading and Error State Tests › should not have console errors on page load
  -  15 …ing.spec.ts:129:3 › Frontend Error Handling › provides recovery options for network errors
  -  16 …s:165:3 › Frontend Error Handling › shows loading states and prevents multiple submissions
  -  17 …error-handling.spec.ts:203:3 › Frontend Error Handling › handles timeout errors gracefully
  -  18 …235:3 › Frontend Error Handling › displays generation failure errors with recovery options
  ✓  19 …lity.spec.ts:51:3 › Accessibility Tests › should support Enter/Space key activation (1.5s)
  -  20 …g.spec.ts:291:3 › Frontend Error Handling › provides rate limit feedback with clear timing
  -  21 …handling.spec.ts:345:3 › Frontend Error Handling › handles image loading errors in gallery
  -  22 …g.spec.ts:389:3 › Frontend Error Handling › shows offline mode when network is unavailable
  ✓  23 …andling.spec.ts:425:3 › Frontend Error Handling › preserves form data during errors (1.7s)
  ✘  24 …pec.ts:132:5 › Gallery page › Gallery Pagination › navigates to next page correctly (3.6s)
  ✓  25 …/e2e/forms.spec.ts:75:3 › Form UX Tests › should handle advanced settings accordion (1.4s)
  ✓  26 …ccessibility.spec.ts:76:3 › Accessibility Tests › should handle Escape key behavior (1.4s)
  ✓  27 …ndling.spec.ts:472:3 › Frontend Error Handling › provides accessible error messages (1.8s)
  ✓  28 …ests/e2e/forms.spec.ts:96:3 › Form UX Tests › should handle number input validation (1.7s)
  ✓  29 …ssibility.spec.ts:86:3 › Accessibility Tests › should have proper heading hierarchy (6.7s)
  -  30 …handling.spec.ts:515:3 › Frontend Error Handling › reports JavaScript errors appropriately
  -  31 …dling.spec.ts:551:3 › Frontend Error Handling › handles progressive enhancement gracefully
  ✓  32 …/navigation.spec.ts:7:3 › Navigation Tests › should navigate between all main pages (2.0s)
  ✓  33 …rmance.spec.ts:96:3 › Frontend Performance Tests › generation page load performance (1.5s)
  ✘  34 …allery page › Gallery Pagination › content type toggles update pagination correctly (3.9s)
Generation page load time: 1343ms
  -  35 …ts:113:3 › Frontend Performance Tests › generation history component rendering performance
  ✓  36 …3 › Navigation Tests › should verify all navigation items are visible and clickable (1.7s)
  ✓  37 …e2e/navigation.spec.ts:43:3 › Navigation Tests › should support keyboard navigation (1.6s)
Console errors found: [
  'Failed to load resource: the server responded with a status of 404 (Not Found)'
]
  ✓  14 …s:7:3 › Loading and Error State Tests › should not have console errors on page load (8.5s)
  ✓  38 …43:3 › Loading and Error State Tests › should show loading states during navigation (1.7s)
  -  39 …pec.ts:149:3 › Frontend Performance Tests › virtual scrolling performance with large lists
  ✓  40 …ion.spec.ts:67:3 › Navigation Tests › should handle direct URL access to all routes (6.0s)
  ✓  41 …essibility.spec.ts:110:3 › Accessibility Tests › should have accessible form labels (1.8s)
  ✓  42 …ts:79:3 › Loading and Error State Tests › should handle API error states gracefully (1.5s)
  -  43 …2e/performance.spec.ts:195:3 › Frontend Performance Tests › lazy image loading performance
  ✓  44 …s:126:3 › Loading and Error State Tests › should render pages without layout shifts (8.5s)
  ✓  45 …sibility.spec.ts:148:3 › Accessibility Tests › should have visible focus indicators (1.5s)
  ✓  46 …c.ts:301:5 › Gallery page › Gallery Pagination › dashboard and gallery totals match (3.1s)
  -  47 …nce.spec.ts:235:3 › Frontend Performance Tests › search and filter interaction performance
  -  48 …/e2e/recommendations.spec.ts:5:8 › Recommendations page › marks a recommendation as served
  -  49 …s/e2e/settings.spec.ts:5:8 › Settings page › persists profile updates and theme preference
  -  50 …e.spec.ts:4:3 › Theme and UI Settings Tests › should toggle theme and persist across pages
  ✘  51 …ts:362:5 › Gallery page › Gallery Pagination › large dataset pagination performance (3.5s)
  ✓  52 …pec.ts:291:3 › Frontend Performance Tests › generation form interaction performance (2.2s)
Theme toggle found but no theme change detected - skipping test
  ✓  53 …:75:3 › Theme and UI Settings Tests › should toggle UI settings and persist changes (3.0s)
Prompt input response time: 101ms
No model options available for performance testing
  -  54 … tests/e2e/performance.spec.ts:341:3 › Frontend Performance Tests › pagination performance
  -  55 …formance.spec.ts:379:3 › Frontend Performance Tests › generation details modal performance
  ✓  56 …ts:153:3 › Loading and Error State Tests › should handle network offline gracefully (1.5s)
  -  57 …mance.spec.ts:432:3 › Frontend Performance Tests › memory usage during component lifecycle
  ✓  58 …ce.spec.ts:487:3 › Frontend Performance Tests › bundle size and loading performance (1.7s)
Bundle size: 9.58MB, Load time: 1583ms
  -  59 …/performance.spec.ts:525:8 › Frontend Performance Tests › performance regression detection


  1) [chromium] › tests/e2e/gallery.spec.ts:71:5 › Gallery page › Gallery Pagination › displays correct total count and page navigation

    Error: expect.toBeVisible: Error: strict mode violation: getByRole('button', { name: '1' }) resolved to 2 elements:
        1) <button tabindex="0" type="button" aria-current="page" aria-label="page 1" class="MuiButtonBase-root MuiPaginationItem-root MuiPaginationItem-sizeMedium MuiPaginationItem-text MuiPaginationItem-rounded MuiPaginationItem-colorPrimary MuiPaginationItem-textPrimary Mui-selected MuiPaginationItem-page css-jqyqk4-MuiButtonBase-root-MuiPaginationItem-root">1</button> aka getByRole('button', { name: 'page 1', exact: true })
        2) <button tabindex="0" type="button" aria-label="Go to page 117500" class="MuiButtonBase-root MuiPaginationItem-root MuiPaginationItem-sizeMedium MuiPaginationItem-text MuiPaginationItem-rounded MuiPaginationItem-colorPrimary MuiPaginationItem-textPrimary MuiPaginationItem-page css-jqyqk4-MuiButtonBase-root-MuiPaginationItem-root">117500</button> aka getByRole('button', { name: 'Go to page 117500' })

    Call log:
      - Expect "toBeVisible" with timeout 2000ms
      - waiting for getByRole('button', { name: '1' })


      118 |
      119 |       // Check pagination component shows correct page numbers
    > 120 |       await expect(page.getByRole('button', { name: '1' })).toBeVisible()
          |                                                             ^
      121 |       await expect(page.getByRole('button', { name: '2' })).toBeVisible()
      122 |
      123 |       // Check next page button is enabled
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:120:61

    Error Context: test-results/gallery-Gallery-page-Galle-dad5e-l-count-and-page-navigation-chromium/error-context.md

  2) [chromium] › tests/e2e/gallery.spec.ts:132:5 › Gallery page › Gallery Pagination › navigates to next page correctly

    Error: expect(locator).toBeVisible() failed

    Locator:  getByText('Page 1 Item 1')
    Expected: visible
    Received: <element(s) not found>
    Timeout:  2000ms

    Call log:
      - Expect "toBeVisible" with timeout 2000ms
      - waiting for getByText('Page 1 Item 1')


      195 |
      196 |       // Verify we're on page 1
    > 197 |       await expect(page.getByText('Page 1 Item 1')).toBeVisible()
          |                                                     ^
      198 |
      199 |       // Click next page
      200 |       await page.getByRole('button', { name: '2' }).click()
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:197:53

    Error Context: test-results/gallery-Gallery-page-Galle-0e2ac-ates-to-next-page-correctly-chromium/error-context.md

  3) [chromium] › tests/e2e/gallery.spec.ts:207:5 › Gallery page › Gallery Pagination › content type toggles update pagination correctly

    TimeoutError: locator.uncheck: Timeout 2000ms exceeded.
    Call log:
      - waiting for getByLabel('Your auto-gens')
        - locator resolved to <input checked role="switch" type="checkbox" class="PrivateSwitchBase-input MuiSwitch-input css-12xagqm-MuiSwitchBase-root"/>
      - attempting click action
        2 × waiting for element to be visible, enabled and stable
          - element is not stable
        - retrying click action
        - waiting 20ms
        - waiting for element to be visible, enabled and stable
        - element is not stable
      2 × retrying click action
          - waiting 100ms
          - waiting for element to be visible, enabled and stable
          - element is not visible
      3 × retrying click action
          - waiting 500ms
          - waiting for element to be visible, enabled and stable
          - element is not visible
      - retrying click action
        - waiting 500ms


      291 |
      292 |       // Disable auto-gens
    > 293 |       await page.getByLabel('Your auto-gens').uncheck()
          |                                               ^
      294 |       await page.getByLabel('Community auto-gens').uncheck()
      295 |
      296 |       // Check that pagination updated
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:293:47

    Error Context: test-results/gallery-Gallery-page-Galle-5a546-update-pagination-correctly-chromium/error-context.md

  4) [chromium] › tests/e2e/gallery.spec.ts:362:5 › Gallery page › Gallery Pagination › large dataset pagination performance

    Error: expect(locator).toBeVisible() failed

    Locator:  getByText(/1,000,000 pages showing 10,000,000 results/)
    Expected: visible
    Received: <element(s) not found>
    Timeout:  2000ms

    Call log:
      - Expect "toBeVisible" with timeout 2000ms
      - waiting for getByText(/1,000,000 pages showing 10,000,000 results/)


      400 |
      401 |       // Verify it loads even at deep pages
    > 402 |       await expect(page.getByText(/1,000,000 pages showing 10,000,000 results/)).toBeVisible()
          |                                                                                  ^
      403 |       await expect(page.getByText('Content Item 1')).toBeVisible()
      404 |
      405 |       // Check that pagination controls work at deep pages
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:402:82

    Error Context: test-results/gallery-Gallery-page-Galle-4e360-aset-pagination-performance-chromium/error-context.md

  4 failed
    [chromium] › tests/e2e/gallery.spec.ts:71:5 › Gallery page › Gallery Pagination › displays correct total count and page navigation
    [chromium] › tests/e2e/gallery.spec.ts:132:5 › Gallery page › Gallery Pagination › navigates to next page correctly
    [chromium] › tests/e2e/gallery.spec.ts:207:5 › Gallery page › Gallery Pagination › content type toggles update pagination correctly
    [chromium] › tests/e2e/gallery.spec.ts:362:5 › Gallery page › Gallery Pagination › large dataset pagination performance
  27 skipped
  28 passed (35.0s)

To open last HTML report run:

  npx playwright show-report

make: *** [frontend-test-e2e] Error 1
make frontend-test-e2e
Running frontend Playwright tests...
npm --prefix frontend run test:e2e

> frontend@0.0.0 test:e2e
> playwright test


Running 59 tests using 5 workers

  -   1 …tests/e2e/auth.spec.ts:5:8 › Auth pages › redirects logged-in user from login to dashboard
  -   2 …/e2e/auth.spec.ts:131:8 › Auth pages › keeps unauthenticated visitor on signup placeholder
  -   3 …um] › tests/e2e/dashboard.spec.ts:5:8 › Dashboard › shows gallery stats and recent content
  ✓   4 …c.ts:4:3 › Form UX Tests › should handle form field focus states on generation page (3.5s)
  -   5 …tests/e2e/generation.spec.ts:7:8 › ComfyUI Generation › should navigate to generation page
  -   6 …ts/e2e/generation.spec.ts:34:8 › ComfyUI Generation › should validate required form fields
  ✓   7 …tion.spec.ts:51:3 › ComfyUI Generation › should show generation parameters controls (3.7s)
  ✓   8 …pec.ts:7:3 › Accessibility Tests › should support comprehensive keyboard navigation (4.2s)
  ✓   9 …:3 › Frontend Error Handling › displays user-friendly error when API is unavailable (3.7s)
  -  10 …ium] › tests/e2e/gallery.spec.ts:5:8 › Gallery page › filters gallery items by search term
  ✘  11 …allery page › Gallery Pagination › displays correct total count and page navigation (3.5s)
  ✓  12 …e/forms.spec.ts:33:3 › Form UX Tests › should validate form submission requirements (1.7s)
     13 ….spec.ts:7:3 › Loading and Error State Tests › should not have console errors on page load
  -  14 ….spec.ts:73:3 › Frontend Error Handling › handles validation errors with specific guidance
  -  15 …ing.spec.ts:129:3 › Frontend Error Handling › provides recovery options for network errors
  -  16 …s:165:3 › Frontend Error Handling › shows loading states and prevents multiple submissions
  -  17 …error-handling.spec.ts:203:3 › Frontend Error Handling › handles timeout errors gracefully
  -  18 …235:3 › Frontend Error Handling › displays generation failure errors with recovery options
  -  19 …g.spec.ts:291:3 › Frontend Error Handling › provides rate limit feedback with clear timing
  ✓  20 …lity.spec.ts:51:3 › Accessibility Tests › should support Enter/Space key activation (1.5s)
  -  21 …handling.spec.ts:345:3 › Frontend Error Handling › handles image loading errors in gallery
  -  22 …g.spec.ts:389:3 › Frontend Error Handling › shows offline mode when network is unavailable
  ✓  23 …andling.spec.ts:425:3 › Frontend Error Handling › preserves form data during errors (1.8s)
  ✘  24 …pec.ts:132:5 › Gallery page › Gallery Pagination › navigates to next page correctly (3.5s)
  ✓  25 …/e2e/forms.spec.ts:75:3 › Form UX Tests › should handle advanced settings accordion (1.5s)
  ✓  26 …ccessibility.spec.ts:76:3 › Accessibility Tests › should handle Escape key behavior (1.4s)
  ✓  27 …ndling.spec.ts:472:3 › Frontend Error Handling › provides accessible error messages (1.7s)
  ✓  28 …ests/e2e/forms.spec.ts:96:3 › Form UX Tests › should handle number input validation (1.7s)
  ✓  29 …ssibility.spec.ts:86:3 › Accessibility Tests › should have proper heading hierarchy (6.5s)
  -  30 …handling.spec.ts:515:3 › Frontend Error Handling › reports JavaScript errors appropriately
  -  31 …dling.spec.ts:551:3 › Frontend Error Handling › handles progressive enhancement gracefully
  ✓  32 …/navigation.spec.ts:7:3 › Navigation Tests › should navigate between all main pages (2.0s)
  ✓  33 …rmance.spec.ts:96:3 › Frontend Performance Tests › generation page load performance (1.5s)
  ✘  34 …allery page › Gallery Pagination › content type toggles update pagination correctly (3.8s)
Generation page load time: 1440ms
  -  35 …ts:113:3 › Frontend Performance Tests › generation history component rendering performance
  ✓  36 …3 › Navigation Tests › should verify all navigation items are visible and clickable (1.6s)
  ✓  37 …e2e/navigation.spec.ts:43:3 › Navigation Tests › should support keyboard navigation (1.6s)
Console errors found: [
  'Failed to load resource: the server responded with a status of 404 (Not Found)'
]
  ✓  13 …s:7:3 › Loading and Error State Tests › should not have console errors on page load (8.4s)
  ✓  38 …43:3 › Loading and Error State Tests › should show loading states during navigation (1.7s)
  -  39 …pec.ts:149:3 › Frontend Performance Tests › virtual scrolling performance with large lists
  ✓  40 …ion.spec.ts:67:3 › Navigation Tests › should handle direct URL access to all routes (5.3s)
  ✓  41 …essibility.spec.ts:110:3 › Accessibility Tests › should have accessible form labels (1.7s)
  ✓  42 …ts:79:3 › Loading and Error State Tests › should handle API error states gracefully (1.4s)
  -  43 …2e/performance.spec.ts:195:3 › Frontend Performance Tests › lazy image loading performance
  ✓  44 …c.ts:301:5 › Gallery page › Gallery Pagination › dashboard and gallery totals match (2.7s)
  ✓  45 …s:126:3 › Loading and Error State Tests › should render pages without layout shifts (7.9s)
  ✓  46 …sibility.spec.ts:148:3 › Accessibility Tests › should have visible focus indicators (1.4s)
  -  47 …nce.spec.ts:235:3 › Frontend Performance Tests › search and filter interaction performance
  -  48 …/e2e/recommendations.spec.ts:5:8 › Recommendations page › marks a recommendation as served
  -  49 …s/e2e/settings.spec.ts:5:8 › Settings page › persists profile updates and theme preference
  -  50 …e.spec.ts:4:3 › Theme and UI Settings Tests › should toggle theme and persist across pages
  ✘  51 …ts:362:5 › Gallery page › Gallery Pagination › large dataset pagination performance (3.6s)
  ✓  52 …pec.ts:291:3 › Frontend Performance Tests › generation form interaction performance (2.1s)
Theme toggle found but no theme change detected - skipping test
  ✓  53 …:75:3 › Theme and UI Settings Tests › should toggle UI settings and persist changes (2.9s)
Prompt input response time: 62ms
No model options available for performance testing
  -  54 … tests/e2e/performance.spec.ts:341:3 › Frontend Performance Tests › pagination performance
  ✓  55 …ts:153:3 › Loading and Error State Tests › should handle network offline gracefully (1.5s)
  -  56 …formance.spec.ts:379:3 › Frontend Performance Tests › generation details modal performance
  -  57 …mance.spec.ts:432:3 › Frontend Performance Tests › memory usage during component lifecycle
  ✓  58 …ce.spec.ts:487:3 › Frontend Performance Tests › bundle size and loading performance (1.3s)
Bundle size: 9.58MB, Load time: 1275ms
  -  59 …/performance.spec.ts:525:8 › Frontend Performance Tests › performance regression detection


  1) [chromium] › tests/e2e/gallery.spec.ts:71:5 › Gallery page › Gallery Pagination › displays correct total count and page navigation

    Error: expect.toBeVisible: Error: strict mode violation: getByRole('button', { name: '1' }) resolved to 2 elements:
        1) <button tabindex="0" type="button" aria-current="page" aria-label="page 1" class="MuiButtonBase-root MuiPaginationItem-root MuiPaginationItem-sizeMedium MuiPaginationItem-text MuiPaginationItem-rounded MuiPaginationItem-colorPrimary MuiPaginationItem-textPrimary Mui-selected MuiPaginationItem-page css-jqyqk4-MuiButtonBase-root-MuiPaginationItem-root">1</button> aka getByRole('button', { name: 'page 1', exact: true })
        2) <button tabindex="0" type="button" aria-label="Go to page 117500" class="MuiButtonBase-root MuiPaginationItem-root MuiPaginationItem-sizeMedium MuiPaginationItem-text MuiPaginationItem-rounded MuiPaginationItem-colorPrimary MuiPaginationItem-textPrimary MuiPaginationItem-page css-jqyqk4-MuiButtonBase-root-MuiPaginationItem-root">117500</button> aka getByRole('button', { name: 'Go to page 117500' })

    Call log:
      - Expect "toBeVisible" with timeout 2000ms
      - waiting for getByRole('button', { name: '1' })


      118 |
      119 |       // Check pagination component shows correct page numbers
    > 120 |       await expect(page.getByRole('button', { name: '1' })).toBeVisible()
          |                                                             ^
      121 |       await expect(page.getByRole('button', { name: '2' })).toBeVisible()
      122 |
      123 |       // Check next page button is enabled
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:120:61

    Error Context: test-results/gallery-Gallery-page-Galle-dad5e-l-count-and-page-navigation-chromium/error-context.md

  2) [chromium] › tests/e2e/gallery.spec.ts:132:5 › Gallery page › Gallery Pagination › navigates to next page correctly

    Error: expect(locator).toBeVisible() failed

    Locator:  getByText('Page 1 Item 1')
    Expected: visible
    Received: <element(s) not found>
    Timeout:  2000ms

    Call log:
      - Expect "toBeVisible" with timeout 2000ms
      - waiting for getByText('Page 1 Item 1')


      195 |
      196 |       // Verify we're on page 1
    > 197 |       await expect(page.getByText('Page 1 Item 1')).toBeVisible()
          |                                                     ^
      198 |
      199 |       // Click next page
      200 |       await page.getByRole('button', { name: '2' }).click()
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:197:53

    Error Context: test-results/gallery-Gallery-page-Galle-0e2ac-ates-to-next-page-correctly-chromium/error-context.md

  3) [chromium] › tests/e2e/gallery.spec.ts:207:5 › Gallery page › Gallery Pagination › content type toggles update pagination correctly

    TimeoutError: locator.uncheck: Timeout 2000ms exceeded.
    Call log:
      - waiting for getByLabel('Your auto-gens')
        - locator resolved to <input checked role="switch" type="checkbox" class="PrivateSwitchBase-input MuiSwitch-input css-12xagqm-MuiSwitchBase-root"/>
      - attempting click action
        2 × waiting for element to be visible, enabled and stable
          - element is not stable
        - retrying click action
        - waiting 20ms
        - waiting for element to be visible, enabled and stable
        - element is not stable
      2 × retrying click action
          - waiting 100ms
          - waiting for element to be visible, enabled and stable
          - element is not visible
      3 × retrying click action
          - waiting 500ms
          - waiting for element to be visible, enabled and stable
          - element is not visible
      - retrying click action
        - waiting 500ms


      291 |
      292 |       // Disable auto-gens
    > 293 |       await page.getByLabel('Your auto-gens').uncheck()
          |                                               ^
      294 |       await page.getByLabel('Community auto-gens').uncheck()
      295 |
      296 |       // Check that pagination updated
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:293:47

    Error Context: test-results/gallery-Gallery-page-Galle-5a546-update-pagination-correctly-chromium/error-context.md

  4) [chromium] › tests/e2e/gallery.spec.ts:362:5 › Gallery page › Gallery Pagination › large dataset pagination performance

    Error: expect(locator).toBeVisible() failed

    Locator:  getByText(/1,000,000 pages showing 10,000,000 results/)
    Expected: visible
    Received: <element(s) not found>
    Timeout:  2000ms

    Call log:
      - Expect "toBeVisible" with timeout 2000ms
      - waiting for getByText(/1,000,000 pages showing 10,000,000 results/)


      400 |
      401 |       // Verify it loads even at deep pages
    > 402 |       await expect(page.getByText(/1,000,000 pages showing 10,000,000 results/)).toBeVisible()
          |                                                                                  ^
      403 |       await expect(page.getByText('Content Item 1')).toBeVisible()
      404 |
      405 |       // Check that pagination controls work at deep pages
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery.spec.ts:402:82

    Error Context: test-results/gallery-Gallery-page-Galle-4e360-aset-pagination-performance-chromium/error-context.md

  4 failed
    [chromium] › tests/e2e/gallery.spec.ts:71:5 › Gallery page › Gallery Pagination › displays correct total count and page navigation
    [chromium] › tests/e2e/gallery.spec.ts:132:5 › Gallery page › Gallery Pagination › navigates to next page correctly
    [chromium] › tests/e2e/gallery.spec.ts:207:5 › Gallery page › Gallery Pagination › content type toggles update pagination correctly
    [chromium] › tests/e2e/gallery.spec.ts:362:5 › Gallery page › Gallery Pagination › large dataset pagination performance
  27 skipped
  28 passed (31.3s)