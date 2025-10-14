You compelted tasks in view-pages-fixes.md. Thanks! But there are some issues

## 1. white screen of death
But now, when I click on an item from either the dashboard or gallery page, I get a "white screen of death".

Please fix. Here's the log.

```
ImageViewPage.tsx:132 React has detected a change in the order of Hooks called by ImageViewPage. This will lead to bugs and errors if not fixed. For more information, read the Rules of Hooks: https://react.dev/link/rules-of-hooks

   Previous render            Next render
   ------------------------------------------------------
1. useContext                 useContext
2. useContext                 useContext
3. useContext                 useContext
4. useContext                 useContext
5. useContext                 useContext
6. useContext                 useContext
7. useContext                 useContext
8. useContext                 useContext
9. useRef                     useRef
10. useContext                useContext
11. useLayoutEffect           useLayoutEffect
12. useCallback               useCallback
13. useContext                useContext
14. useContext                useContext
15. useMemo                   useMemo
16. useContext                useContext
17. useContext                useContext
18. useContext                useContext
19. useEffect                 useEffect
20. useState                  useState
21. useCallback               useCallback
22. useSyncExternalStore      useSyncExternalStore
23. useEffect                 useEffect
24. undefined                 useMemo
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

overrideMethod @ hook.js:608
updateHookTypesDev @ react-dom_client.js?v=6e96e4bf:4144
useMemo @ react-dom_client.js?v=6e96e4bf:16757
exports.useMemo @ chunk-X4QARNC5.js?v=6e96e4bf:944
ImageViewPage @ ImageViewPage.tsx:132
react_stack_bottom_frame @ react-dom_client.js?v=6e96e4bf:17422
renderWithHooks @ react-dom_client.js?v=6e96e4bf:4204
updateFunctionComponent @ react-dom_client.js?v=6e96e4bf:6617
beginWork @ react-dom_client.js?v=6e96e4bf:7652
runWithFiberInDEV @ react-dom_client.js?v=6e96e4bf:1483
performUnitOfWork @ react-dom_client.js?v=6e96e4bf:10866
workLoopSync @ react-dom_client.js?v=6e96e4bf:10726
renderRootSync @ react-dom_client.js?v=6e96e4bf:10709
performWorkOnRoot @ react-dom_client.js?v=6e96e4bf:10328
performSyncWorkOnRoot @ react-dom_client.js?v=6e96e4bf:11633
flushSyncWorkAcrossRoots_impl @ react-dom_client.js?v=6e96e4bf:11534
processRootScheduleInMicrotask @ react-dom_client.js?v=6e96e4bf:11556
(anonymous) @ react-dom_client.js?v=6e96e4bf:11647
react-dom_client.js?v=6e96e4bf:4342 Uncaught Error: Rendered more hooks than during the previous render.
    at updateWorkInProgressHook (react-dom_client.js?v=6e96e4bf:4342:19)
    at updateMemo (react-dom_client.js?v=6e96e4bf:5063:20)
    at Object.useMemo (react-dom_client.js?v=6e96e4bf:16761:20)
    at exports.useMemo (chunk-X4QARNC5.js?v=6e96e4bf:944:36)
    at ImageViewPage (ImageViewPage.tsx:132:23)
    at Object.react_stack_bottom_frame (react-dom_client.js?v=6e96e4bf:17422:20)
    at renderWithHooks (react-dom_client.js?v=6e96e4bf:4204:24)
    at updateFunctionComponent (react-dom_client.js?v=6e96e4bf:6617:21)
    at beginWork (react-dom_client.js?v=6e96e4bf:7652:20)
    at runWithFiberInDEV (react-dom_client.js?v=6e96e4bf:1483:72)
updateWorkInProgressHook @ react-dom_client.js?v=6e96e4bf:4342
updateMemo @ react-dom_client.js?v=6e96e4bf:5063
useMemo @ react-dom_client.js?v=6e96e4bf:16761
exports.useMemo @ chunk-X4QARNC5.js?v=6e96e4bf:944
ImageViewPage @ ImageViewPage.tsx:132
react_stack_bottom_frame @ react-dom_client.js?v=6e96e4bf:17422
renderWithHooks @ react-dom_client.js?v=6e96e4bf:4204
updateFunctionComponent @ react-dom_client.js?v=6e96e4bf:6617
beginWork @ react-dom_client.js?v=6e96e4bf:7652
runWithFiberInDEV @ react-dom_client.js?v=6e96e4bf:1483
performUnitOfWork @ react-dom_client.js?v=6e96e4bf:10866
workLoopSync @ react-dom_client.js?v=6e96e4bf:10726
renderRootSync @ react-dom_client.js?v=6e96e4bf:10709
performWorkOnRoot @ react-dom_client.js?v=6e96e4bf:10357
performSyncWorkOnRoot @ react-dom_client.js?v=6e96e4bf:11633
flushSyncWorkAcrossRoots_impl @ react-dom_client.js?v=6e96e4bf:11534
processRootScheduleInMicrotask @ react-dom_client.js?v=6e96e4bf:11556
(anonymous) @ react-dom_client.js?v=6e96e4bf:11647
hook.js:608 An error occurred in the <ImageViewPage> component.

Consider adding an error boundary to your tree to customize error handling behavior.
Visit https://react.dev/link/error-boundaries to learn more about error boundaries.

overrideMethod @ hook.js:608
defaultOnUncaughtError @ react-dom_client.js?v=6e96e4bf:6227
logUncaughtError @ react-dom_client.js?v=6e96e4bf:6281
runWithFiberInDEV @ react-dom_client.js?v=6e96e4bf:1483
lane.callback @ react-dom_client.js?v=6e96e4bf:6309
callCallback @ react-dom_client.js?v=6e96e4bf:4095
commitCallbacks @ react-dom_client.js?v=6e96e4bf:4107
runWithFiberInDEV @ react-dom_client.js?v=6e96e4bf:1485
commitLayoutEffectOnFiber @ react-dom_client.js?v=6e96e4bf:9027
flushLayoutEffects @ react-dom_client.js?v=6e96e4bf:11172
commitRoot @ react-dom_client.js?v=6e96e4bf:11078
commitRootWhenReady @ react-dom_client.js?v=6e96e4bf:10510
performWorkOnRoot @ react-dom_client.js?v=6e96e4bf:10455
performSyncWorkOnRoot @ react-dom_client.js?v=6e96e4bf:11633
flushSyncWorkAcrossRoots_impl @ react-dom_client.js?v=6e96e4bf:11534
processRootScheduleInMicrotask @ react-dom_client.js?v=6e96e4bf:11556
(anonymous) @ react-dom_client.js?v=6e96e4bf:11647

```

## 2. failing tests
the following playwright tests are failing. please fix:

```


  1) [chromium] › tests/e2e/dashboard-interactions.spec.ts:177:3 › Dashboard Page Interactions › should open dashboard detail view from grid

    Error: expect(page).toHaveURL(expected) failed

    Expected pattern: /\/dashboard\/1$/
    Received string:  "http://127.0.0.1:4173/view/1"
    Timeout: 3000ms

    Call log:
      - Expect "toHaveURL" with timeout 3000ms
        7 × unexpected value "http://127.0.0.1:4173/view/1"


      184 |     await gridItem.click()
      185 |
    > 186 |     await expect(page).toHaveURL(/\/dashboard\/1$/)
          |                        ^
      187 |     await expect(page.locator('[data-testid="dashboard-detail-title"]').first()).toHaveText('Mock Artwork')
      188 |
      189 |     await page.locator('[data-testid="dashboard-detail-back-button"]').click()
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/dashboard-interactions.spec.ts:186:24

  2) [chromium] › tests/e2e/error-handling.spec.ts:27:3 › Frontend Error Handling › displays user-friendly error when API is unavailable

    TimeoutError: page.goto: Timeout 5000ms exceeded.
    Call log:
      - navigating to "http://127.0.0.1:4173/generation", waiting until "load"


      44 |     })
      45 |
    > 46 |     await page.goto('/generation')
         |                ^
      47 |
      48 |     // Try to submit a generation request
      49 |     await page.fill('[data-testid="prompt-input"]', 'Test prompt')
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/error-handling.spec.ts:46:16

    Error Context: test-results/error-handling-Frontend-Er-98481-ror-when-API-is-unavailable-chromium/error-context.md

  3) [chromium] › tests/e2e/gallery-interactions.spec.ts:46:3 › Gallery Page Interactions › should open image detail from grid view and return back

    Error: expect(page).toHaveURL(expected) failed

    Expected pattern: /\/gallery\/1$/
    Received string:  "http://127.0.0.1:4173/view/1"
    Timeout: 3000ms

    Call log:
      - Expect "toHaveURL" with timeout 3000ms
        6 × unexpected value "http://127.0.0.1:4173/view/1"


      60 |     await gridItem.click()
      61 |
    > 62 |     await expect(page).toHaveURL(/\/gallery\/1$/)
         |                        ^
      63 |     await expect(page.locator('[data-testid="gallery-detail-title"]')).toHaveText('Mock Artwork')
      64 |
      65 |     await page.locator('[data-testid="gallery-detail-back-button"]').click()
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery-interactions.spec.ts:62:24

  4) [chromium] › tests/e2e/gallery-interactions.spec.ts:285:3 › Gallery Page Interactions › should open gallery item detail view from grid

    Error: expect(page).toHaveURL(expected) failed

    Expected pattern: /\/gallery\/1$/
    Received string:  "http://127.0.0.1:4173/view/1"
    Timeout: 3000ms

    Call log:
      - Expect "toHaveURL" with timeout 3000ms
        7 × unexpected value "http://127.0.0.1:4173/view/1"


      295 |     await firstGridItem.click()
      296 |
    > 297 |     await expect(page).toHaveURL(/\/gallery\/1$/)
          |                        ^
      298 |     await expect(page.locator('[data-testid="gallery-detail-title"]').first()).toHaveText('Mock Artwork')
      299 |     await expect(page.locator('[data-testid="gallery-detail-image"]')).toBeVisible()
      300 |
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery-interactions.spec.ts:297:24

  5) [chromium] › tests/e2e/generation-failure-feedback.spec.ts:184:3 › Generation failure feedback › keeps failure message visible after validation error

    TimeoutError: locator.focus: Timeout 3000ms exceeded.
    Call log:
      - waiting for locator('[role="slider"]').first()


      190 |
      191 |     const modelSlider = page.locator('[role="slider"]').first()
    > 192 |     await modelSlider.focus()
          |                       ^
      193 |     await page.keyboard.press('Home') // Jump to minimum (0)
      194 |
      195 |     const sliderValueAttr = await modelSlider.getAttribute('aria-valuenow')
        at /Users/joeflack4/projects/genonaut/frontend/tests/e2e/generation-failure-feedback.spec.ts:192:23

    Error Context: test-results/generation-failure-feedbac-a3f5a-ible-after-validation-error-chromium/error-context.md

  5 failed
    [chromium] › tests/e2e/dashboard-interactions.spec.ts:177:3 › Dashboard Page Interactions › should open dashboard detail view from grid
    [chromium] › tests/e2e/error-handling.spec.ts:27:3 › Frontend Error Handling › displays user-friendly error when API is unavailable
    [chromium] › tests/e2e/gallery-interactions.spec.ts:46:3 › Gallery Page Interactions › should open image detail from grid view and return back
    [chromium] › tests/e2e/gallery-interactions.spec.ts:285:3 › Gallery Page Interactions › should open gallery item detail view from grid
    [chromium] › tests/e2e/generation-failure-feedback.spec.ts:184:3 › Generation failure feedback › keeps failure message visible after validation error
  65 skipped
  88 passed (1.3m)

To open last HTML report run:

  npx playwright show-report tests/e2e/output/playwright-report

make: *** [frontend-test-e2e] Error 1
```