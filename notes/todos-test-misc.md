# Misc test todo's
## Currently failing tests

### Mock API and Data Display Issues
These tests are failing because mock API patterns aren't matching correctly, resulting in expected content not being displayed on the page. The unified gallery API integration uses complex URL patterns with query parameters, and the mock setup needs precise pattern matching to return the correct data for different pagination states.

#### Medium Effort
No tests currently in this category.

#### Medium-High Effort
- [ ] **navigates to next page correctly** - **PARTIALLY FIXED** - Test was failing when trying to verify "Page 1 Item 1" content is visible on the first page due to mock API pattern mismatches. **Major Progress Made**: Successfully resolved the "No gallery items found" issue by fixing mock API patterns to match actual `useUnifiedGallery` requests. The actual API calls include complex query parameters like `/api/v1/content/unified?page=1&page_size=10&content_types=regular,auto&creator_filter=all&user_id=121e194b-4caa-4b81-ad4f-86ca3919d5b9&sort_field=created_at&sort_order=desc`. Fixed mock data structure to include proper `source_type` and `stats` fields matching the API contract. **Remaining Issue**: Page 2 navigation doesn't work - clicking "Go to page 2" doesn't update content or set `aria-current="true"` on the button. This indicates the page=2 API call pattern isn't matching correctly, possibly due to React Query caching behavior or the specific URL pattern not being caught by the mock. **Next Steps**: Need to debug exact URL patterns for page=2 requests, potentially inspect network requests in browser dev tools during test execution, consider React Query cache invalidation, and ensure mock patterns handle all query parameter combinations precisely. May also need to investigate component state management for pagination updates.

- [ ] **large dataset pagination performance** - Test fails when trying to verify pagination text "/1,000,000 pages showing 10,000,000 results/" is visible on a deep page (page 50000). The mock data provides the correct pagination structure (10M total_count, 1M total_pages), but the component isn't displaying the formatted text. This could be due to the options panel not opening by default, the unified API call not matching the mock pattern, or the toLocaleString() formatting not working as expected. Fix requires ensuring the mock API call matches correctly for deep pages and verifying the pagination text display logic in the component.

## Currently skipped tests

### Error Recovery Integration Tests
These tests require complex database schema fixes and ComfyUI integration improvements:

- [ ] **test_connection_recovery_after_downtime** - Tests system recovery after ComfyUI downtime with connection retry logic. Currently failing due to database binding issues where the `submit_to_comfyui` method attempts to store a dict object (`{'prompt_id': 'recovery-123'}`) directly in the `comfyui_prompt_id` column, but SQLite expects a string. Requires database schema fixes for proper prompt_id storage and mock response handling.
- [ ] **test_partial_service_degradation_handling** - Tests handling when some ComfyUI features are unavailable but core functionality works. Currently failing due to complex service interactions and mock setup issues with ComfyUI status checking methods. Requires refined service architecture and better separation between ComfyUI submission and status checking.
- [ ] **test_graceful_degradation_during_high_error_rate** - Tests system behavior under high error rates (80% failure simulation). Currently failing due to complex database transaction issues and mock coordination problems when testing multiple concurrent requests. Requires improved error handling infrastructure and transaction management for high-load scenarios.
