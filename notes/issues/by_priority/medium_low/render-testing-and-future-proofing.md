# Image Rendering Fixes - Action Plan

## Current Issue
Image endpoint works when accessed directly in browser (http://localhost:8001/api/v1/images/65015) but fails to render in frontend with broken image placeholder.

HTML from frontend:
```html
<img class="MuiCardMedia-root MuiCardMedia-media MuiCardMedia-img css-zwexhw-MuiCardMedia-root" alt="cat" src="/api/v1/images/65015">
```

## Solution Summary

**Root Cause**: Frontend running on port 5173, backend on port 8001. Image src used relative URL `/api/v1/images/65015` which resolved to `http://localhost:5173/api/v1/images/65015` instead of `http://localhost:8001/api/v1/images/65015`.

**Fix Applied**:
1. Created `frontend/src/utils/image-url.ts` with `getImageUrl()` helper function
2. Updated `GenerationProgress.tsx` to use `getImageUrl(content_id)` instead of template literal
3. Updated `ImageViewer.tsx` similarly
4. Function reads `VITE_API_BASE_URL` env var or defaults to `http://localhost:8001`

**Files Changed**:
- `frontend/src/utils/image-url.ts` (new file)
- `frontend/src/components/generation/GenerationProgress.tsx`
- `frontend/src/components/generation/ImageViewer.tsx`

## Investigation Steps

### Phase 1: URL and Proxy Configuration
- [X] Check if frontend is running on different port than backend - CONFIRMED: Frontend on 5173, backend on 8001
- [X] Verify frontend proxy configuration (vite.config.ts / package.json) - NO PROXY CONFIGURED
- [X] Check if image src needs absolute URL vs relative path - ROOT CAUSE: Relative URLs don't work across ports
- [X] Test with hardcoded absolute URL in frontend code - FIXED: Created getImageUrl() utility
- [ ] Check browser console for network errors
- [ ] Check browser Network tab for the failed image request

### Phase 2: CORS and Headers
- [ ] Check CORS configuration in backend (FastAPI middleware)
- [ ] Verify CORS allows image requests from frontend origin
- [ ] Check response headers when image is loaded from frontend vs browser
- [ ] Test with CORS disabled temporarily to rule out CORS issue
- [ ] Check Content-Security-Policy headers

### Phase 3: Frontend Component Investigation
- [ ] Find the React component rendering the image
- [ ] Check if image URL is being constructed correctly
- [ ] Verify state/props are passing correct content_id
- [ ] Check if there's any URL transformation happening
- [ ] Look for any image loading error handlers in the component
- [ ] Add console.log to see what URL is actually being used

### Phase 4: Authentication and Session
- [ ] Check if API requires authentication headers
- [ ] Verify cookies are being sent with image requests
- [ ] Check if session is valid when image is requested
- [ ] Test with authentication disabled temporarily

### Phase 5: Cache and Timing Issues
- [ ] Check if browser is caching a failed request
- [ ] Try hard refresh (Cmd+Shift+R) in browser
- [ ] Check if image becomes available after delay
- [ ] Verify content_id exists in database before render
- [ ] Check for race conditions in frontend

## Proposed Tests

### Low Effort Tests
- [X] Direct API endpoint test (curl/httpie) - ALREADY DONE
- [X] Check frontend proxy configuration files - DONE: No proxy configured
- [X] Unit test for image URL utility function - DONE: 9 tests passing
- [ ] Browser DevTools network inspection
- [ ] Simple manual test: replace src with absolute URL in browser inspector
- [ ] Check browser console for JavaScript errors
- [ ] Manual verification: Test image rendering in actual frontend

### Medium Effort Tests
- [ ] Basic Playwright test: navigate to generation page and check image element
- [ ] API integration test: verify image endpoint returns correct content-type and content-length
- [ ] Frontend unit test: mock image component and verify src prop
- [ ] Test CORS headers with curl from different origins
- [ ] Network request interception test to verify URL being requested

### High Effort Tests
- [ ] Full e2e test: submit generation, wait for completion, verify image renders
- [ ] Screenshot comparison test: verify actual image content matches expected
- [ ] Load testing: multiple concurrent image requests
- [ ] Integration test with mock ComfyUI: full workflow from generation to display
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Responsive design test: image rendering at different viewport sizes
- [ ] Error recovery test: handle missing images, network failures

## Additional Debugging Ideas
- [ ] Add detailed logging to serve_image endpoint
- [ ] Add React error boundary around image component
- [ ] Check if MUI CardMedia has special requirements
- [ ] Verify image file actually exists at the path in database
- [ ] Check file permissions on image files
- [ ] Test with a simple <img> tag instead of MUI CardMedia

## Notes
- API endpoint returns 200 OK with correct content-type: image/png
- Content-length: 97179 bytes
- Image path in DB: /Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/output/generations/121e194b-4caa-4b81-ad4f-86ca3919d5b9/2025/10/09/gen_1193924_gen_job_1193924_00014_.png
- Backend running on port 8001
- Frontend running on port 5173 (confirmed)

## Next Steps

1. **Test the fix manually**:
   - Ensure frontend dev server is running
   - Generate a new image
   - Verify it displays correctly in the browser
   - Check browser console for any errors

2. **Consider adding a Vite proxy** (optional):
   - Could configure Vite to proxy /api requests to port 8001
   - Would allow using relative URLs throughout frontend
   - Trade-off: More configuration vs explicit base URLs

3. **Update other components** (if needed):
   - Search for other places using `/api/v1/images/` pattern
   - Consider if gallery components need similar updates

4. **Production considerations**:
   - Ensure VITE_API_BASE_URL is set correctly in production builds
   - Test with production build to verify image loading works

### Next Steps for Production
1. Set `VITE_API_BASE_URL` environment variable in production builds
2. Consider adding Vite proxy configuration as an alternative approach
3. Monitor for any other components that might need the `getImageUrl()` utility
4. Test with production build to ensure images load correctly in deployed environment
