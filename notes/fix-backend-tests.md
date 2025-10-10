# Backend Test Failures - Fix Summary

## Overview
- **Total Failures**: 16 (1 test failure + 15 fixture errors)
- **Root Causes**: 2 distinct issues

## Issues

### Issue 1: Missing `api_client` Fixture (15 errors)
**File**: `test/api/integration/test_content_source_types.py`

**Problem**: All 15 tests are failing because they use `api_client` fixture, but only `api_server` fixture exists in conftest.

**Available fixtures** (from error message):
- `api_server` (probably what we need)
- `db_session`
- `faker`
- Other pytest built-ins

**Failed Tests** (all in `TestContentSourceTypesParameter`) - Should be fixed now:
- [ ] test_parameter_validation_accepts_valid_types (needs verification)
- [ ] test_parameter_validation_rejects_invalid_types (needs verification)
- [ ] test_single_source_type_user_regular (needs verification)
- [ ] test_single_source_type_user_auto (needs verification)
- [ ] test_single_source_type_community_regular (needs verification)
- [ ] test_single_source_type_community_auto (needs verification)
- [ ] test_empty_content_source_types_returns_zero_results (needs verification)
- [ ] test_multiple_source_types_combination (needs verification)
- [ ] test_backward_compatibility_with_legacy_params (needs verification)
- [ ] test_content_source_types_takes_precedence_over_legacy (needs verification)
- [ ] test_pagination_works_with_content_source_types (needs verification)
- [ ] test_all_four_types_together (needs verification)
- [ ] test_three_types_combination (needs verification)
- [ ] test_works_with_search_term (needs verification)
- [ ] test_works_with_sorting (needs verification)

**Solution**:
1. Check conftest.py to see how API client fixture is defined
2. Either rename fixture usage to match what exists, or create `api_client` fixture if needed

### Issue 2: UnboundLocalError in content_service.py (1 failure)
**File**: `genonaut/api/services/content_service.py:660`
**Test**: `test/api/db/test_services.py::TestContentService::test_path_thumbs_alt_res_included_in_unified_content`

**Problem**: Indentation error in LEGACY APPROACH section. The code tries to use `auto_query` variable outside the `if "auto" in content_types:` block.

**Error**:
```
UnboundLocalError: cannot access local variable 'auto_query' where it is not associated with a value
```

**Current (broken) code structure**:
```python
# Auto content query
if "auto" in content_types:
    auto_query = session.query(...).join(User, ContentItemAuto.creator)

    # Apply filters
    if creator_filter == "user" and user_id:
        auto_query = auto_query.filter(ContentItemAuto.creator_id == user_id)
    elif creator_filter == "community" and user_id:
        auto_query = auto_query.filter(ContentItemAuto.creator_id != user_id)

# BUG: These are OUTSIDE the if block, but use auto_query!
if search_term:
    auto_query = auto_query.filter(ContentItemAuto.title.ilike(f"%{search_term}%"))

if tags:
    auto_query = auto_query.filter(
        func.jsonb_exists_any(ContentItemAuto.tags, text(':tags'))
    ).params(tags=tags)

queries.append(auto_query)  # BUG: Also outside, will fail if auto not in content_types
```

**Solution**: Move the `search_term`, `tags`, and `queries.append(auto_query)` lines INSIDE the `if "auto" in content_types:` block by indenting them properly.

## Other Observations (not failures)
- 90 deprecation warnings (mostly Pydantic v1 -> v2 migration)
- 552 tests passing
- 111 tests skipped

## Fix Priority
1. **CRITICAL**: Fix UnboundLocalError in content_service.py (breaks existing functionality) - FIXED
2. **HIGH**: Fix api_client fixture issue (prevents new tests from running) - FIXED

## Fixes Applied

### 1. Fixed UnboundLocalError in content_service.py
**Location**: `genonaut/api/services/content_service.py:650-660`

**Problem**: The `search_term` and `tags` filter blocks were incorrectly indented outside the `if "auto" in content_types:` block, causing `auto_query` to be undefined when the condition was false.

**Solution**: Indented lines 650-660 to be inside the `if "auto" in content_types:` block.

### 2. Fixed Missing api_client Fixture
**Location**: `test/api/integration/conftest.py`

**Problem**: The `api_client` fixture was only defined in `test_api_endpoints.py`, making it unavailable to other integration tests.

**Solution**: Moved `APITestClient` class and `api_client` fixture to `conftest.py` so all integration tests can use it.

### 3. Fixed Validation Error Returns 500 Instead of 400
**Location**: `genonaut/api/routes/content.py:71-141`

**Problem**: The route had a try/except that wrapped validation logic, causing HTTPException(400) to be caught and converted to 500.

**Solution**: Moved validation logic OUTSIDE the try/except block so validation errors return proper 400 status codes.

### 4. Fixed Empty Array Handling (HTTP Protocol Issue)
**Locations**:
- `genonaut/api/routes/content.py:73-85`
- `frontend/src/services/unified-gallery-service.ts:47-54`
- `test/api/integration/test_content_source_types.py:89-105, 135-155`

**Problem**: HTTP doesn't transmit empty arrays in query parameters (they're omitted). When tests/frontend sent `content_source_types=[]`, the backend received `None` and used legacy defaults, returning all content instead of zero.

**Root Cause**: The `requests` library (and standard HTTP clients) don't include empty arrays in URLs.

**Solution**:
1. Introduced sentinel value `[""]` (array with one empty string) to explicitly signal "no content types selected"
2. Route detects `[""]` and converts it to empty array for service layer
3. Frontend sends `content_source_types=` (empty string) when array is empty
4. Tests updated to use `[""]` instead of `[]`

This allows users to explicitly select "zero content types" which returns zero results, distinguishing it from "no parameter sent" which uses legacy defaults.
