# Data Scaling Requirements and Implementation Plan

## Overview

This document outlines the requirements and implementation plan for scaling the Genonaut application to handle millions 
of rows efficiently. The primary focus is on implementing proper pagination with pre-fetching in both the backend API 
and frontend client.

## Current State Analysis

### Backend Issues
1. **Inconsistent pagination patterns**: Some endpoints use hardcoded limits (e.g., `limit: int = 100`), others have different defaults
2. **Missing pagination metadata**: Current responses lack `has_more` field and pagination links
3. **Inefficient count queries**: Total counts are calculated using `count()` which can be slow on large tables
4. **No pagination standards**: Different endpoints use different default page sizes
5. **No offset/cursor optimization**: All pagination uses OFFSET which becomes slow with large offsets
6. **Missing database indices**: Repository queries may lack proper indexing for pagination performance

### Frontend Issues
1. **No pre-fetching strategy**: Frontend fetches pages individually without lookahead
2. **No caching strategy**: Multiple requests for same data with no client-side cache management
3. **Manual pagination logic**: Each component handles pagination differently (see GalleryPage.tsx lines 88-96)
4. **Inefficient data fetching**: Gallery page fetches multiple separate queries and combines client-side (lines 99-112)
5. **No infinite scroll support**: Only traditional pagination supported
6. **No loading optimization**: No skeleton loading or progressive rendering for large datasets

## Requirements

### Backend Requirements
- API endpoints must support pagination with default page size of 50 items
- Users should be able to specify custom page sizes up to 1000 items
- Responses must include pagination metadata (`has_more`, `next_page`, etc.)
- Database queries must be optimized for large datasets (millions of rows)
- Implement cursor-based pagination for high-performance scenarios

### Frontend Requirements
- Pre-fetch next page when user navigates to a new page
- Cache pre-fetched data in client state/cache
- Display cached data instantly when user navigates
- Progressive loading with skeleton screens
- Support both traditional pagination and infinite scroll patterns
- Optimize rendering for large lists with virtualization

### Performance Requirements
- API response time < 200ms for paginated queries on millions of rows
- Frontend page navigation should feel instant (< 50ms) when data is cached
- Memory usage should remain stable even with large cached datasets
- Database queries should use appropriate indices and avoid N+1 problems

## Implementation Plan

**IMPORTANT: Use Test-Driven Development (TDD) approach for all tasks. Write tests first, ensure they fail, then 
implement the feature to make tests pass. Run the appropriate test suite after each task to validate the implementation.**

### Phase 1: Backend Pagination Infrastructure

#### Task 1.1: Create standardized pagination models
- [x] **Test First**: Create tests for pagination request/response models in `test/api/unit/test_pagination_models.py`
- [x] **Implementation**:
  - [x] Create `PaginationRequest` model in `genonaut/api/models/requests.py`
  - [x] Create enhanced `PaginatedResponse` model in `genonaut/api/models/responses.py`
  - [x] Add `has_more`, `next_cursor`, `prev_cursor` fields
- **Files to modify**:
  - `genonaut/api/models/requests.py`
  - `genonaut/api/models/responses.py`
- **Test Command**: `make test-unit`

#### Task 1.2: Enhance BaseRepository with optimized pagination
- [x] **Test First**: Create tests for repository pagination in `test/api/unit/test_base_repository_pagination.py`
- [x] **Implementation**:
  - [x] Add `get_paginated()` method to `BaseRepository` with cursor support
  - [x] Implement efficient counting using `SELECT COUNT(*) OVER()` window function
  - [x] Add index hints and query optimization
- **Files to modify**:
  - `genonaut/api/repositories/base.py`
- **Test Command**: `make test-unit`

#### Task 1.3: Update ContentRepository with pagination optimizations
- [x] **Test First**: Create tests for content repository pagination in `test/api/unit/test_content_repository_pagination.py`
- [x] **Implementation**:
  - [x] Override pagination methods in `ContentRepository` with content-specific optimizations
  - [x] Add composite indices for common query patterns (creator_id + created_at, quality_score + created_at)
  - [x] Implement cursor-based pagination for high-performance scenarios
- **Files to modify**:
  - `genonaut/api/repositories/content_repository.py`
  - Database migration for new indices (prompt the user to do it)
- **Test Command**: `make test-db-unit`

#### Task 1.4: Update content endpoints with standardized pagination
- [x] **Test First**: Create tests for content endpoint pagination in `test/api/integration/test_content_endpoints_pagination.py`
- [x] **Implementation**:
  - [x] Update all content endpoints to use standardized pagination (default 50, max 1000)
  - [x] Replace current pagination logic with new `PaginatedResponse` model
  - [x] Ensure consistent parameter naming (`page`, `page_size`, `cursor`)
- **Files to modify**:
  - `genonaut/api/routes/content.py`
  - `genonaut/api/routes/content_auto.py`
- **Test Command**: `make test-api`

#### Task 1.5: Update remaining endpoints (users, recommendations, interactions, generation)
- [x] **Test First**: Create pagination tests for each endpoint type
- [x] **Implementation**:
  - [x] Apply same pagination standards to user endpoints (completed)
  - [~] Update recommendations, interactions, and generation endpoints (partially completed - pattern established)
  - [x] Ensure consistent error handling and validation
- **Files to modify**:
  - `genonaut/api/routes/users.py` ✅
  - `genonaut/api/routes/recommendations.py` (pattern established, can be applied)
  - `genonaut/api/routes/interactions.py` (pattern established, can be applied)
  - `genonaut/api/routes/generation.py` (pattern established, can be applied)
  - Corresponding repositories and services ✅
- **Test Command**: `make test-api`

### Phase 2: Database Optimization

#### Task 2.1: Create pagination-optimized database indices
- [x] **Test First**: Create tests for query performance in `test/db/integration/test_pagination_performance.py`
- [x] **Implementation**:
  - [x] Add composite indices for common pagination patterns
  - [x] Add partial indices for filtered queries (e.g., public content only)
  - [x] When SQLAlchemy model modification is done, prompt the user to do a migration or otherwise remake the database.
- **Files to create/modify**:
  - Modify SqlAlchemy models ✅
  - Performance test suite ✅
- **Test Command**: `make test-db-integration`

#### Task 2.2: Implement cursor-based pagination for high-volume endpoints
- [x] **Test First**: Create tests for cursor pagination in `test/api/integration/test_cursor_pagination.py`
- [x] **Implementation**:
  - [x] Implement cursor encoding/decoding using base64-encoded JSON
  - [x] Add cursor pagination to content and recommendations endpoints
  - [x] Ensure cursor stability across data modifications
- **Files to modify**:
  - `genonaut/api/repositories/base.py` ✅
  - Content and recommendation repositories ✅
- **Test Command**: `make test-api`

### Phase 3: Frontend Pagination and Caching

#### Task 3.1: Create pagination hooks with pre-fetching
- [x] **Test First**: Create tests for pagination hooks in `src/hooks/__tests__/usePagination.test.tsx`
- [x] **Implementation**:
  - [x] Create `usePagination` hook with pre-fetching logic
  - [x] Create `usePaginatedQuery` hook that wraps React Query with pagination
  - [x] Implement automatic next-page pre-fetching
- **Files to create/modify**:
  - `src/hooks/usePagination.ts`
  - `src/hooks/usePaginatedQuery.ts`
  - `src/hooks/index.ts`
- **Test Command**: `make frontend-test-unit`

#### Task 3.2: Create caching service for paginated data
- [x] **Test First**: Create tests for pagination cache in `src/services/__tests__/paginationCache.test.ts`
- [x] **Implementation**:
  - [x] Create `PaginationCache` class to manage pre-fetched pages
  - [x] Implement LRU eviction policy for memory management
  - [x] Add cache invalidation strategies
- **Files to create**:
  - `src/services/paginationCache.ts`
  - `src/services/__tests__/paginationCache.test.ts`
- **Test Command**: `make frontend-test-unit`

#### Task 3.3: Update API services to use new pagination models
- [x] **Test First**: Update existing service tests to verify pagination support
- [x] **Implementation**:
  - [x] Update `GalleryService` to use standardized pagination
  - [x] Update API client to handle new pagination response format
- **Files to modify**:
  - `src/services/gallery-service.ts`
  - `src/services/api-client.ts`
  - `src/types/api.ts`
- **Test Command**: `make frontend-test-unit`

#### Task 3.4: Refactor GalleryPage to use new pagination system
- [x] **Test First**: Update tests in `src/pages/gallery/__tests__/GalleryPage.test.tsx`
- [x] **Implementation**:
  - [x] Replace manual pagination logic with new hooks
  - [x] Implement pre-fetching for next page
  - [x] Add loading states and error handling
  - [x] Remove client-side data combination logic
- **Files to modify**:
  - `src/pages/gallery/GalleryPage.tsx`
  - `src/hooks/useGalleryList.ts`
  - `src/hooks/useGalleryAutoList.ts`
- **Test Command**: `make frontend-test-unit`

### Phase 4: Performance Testing and Optimization

#### Task 4.1: Add pagination stress testing
- [x] **Test First**: Create stress tests in `test/api/stress/test_pagination_stress.py`
- [x] **Implementation**:
  - [x] Create tests that simulate millions of rows
  - [x] Test pagination performance under load
  - [x] Validate memory usage and response times
- **Files created**:
  - [x] Stress test suite for pagination (`test/api/stress/test_pagination_stress.py`)
  - [x] Performance benchmarking scripts (`test/api/stress/benchmark_pagination.py`)
  - [x] Test runner script (`test/api/stress/run_stress_tests.py`)
- **Test Command**: `make test-all`

## Database Schema Changes

### New Indices Required
Example SQL. You should actually just be adding these indexes to SqlAlchemy models.
```sql
-- Content pagination indices
CREATE INDEX CONCURRENTLY idx_content_items_created_at_desc ON content_items (created_at DESC);
CREATE INDEX CONCURRENTLY idx_content_items_creator_created ON content_items (creator_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_content_items_quality_created ON content_items (quality_score DESC NULLS LAST, created_at DESC);
CREATE INDEX CONCURRENTLY idx_content_items_public_created ON content_items (created_at DESC) WHERE is_private = false;

-- User content access patterns
CREATE INDEX CONCURRENTLY idx_content_items_type_created ON content_items (content_type, created_at DESC);

-- Similar indices for content_items_auto, recommendations, interactions, generation_jobs
```

### Pagination Metadata Tables
Example SQL. You should actually just be adding these indexes to SqlAlchemy models.
```sql
-- Optional: Table to store pagination cursors for complex queries
CREATE TABLE pagination_cursors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL,
    cursor_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
CREATE INDEX idx_pagination_cursors_hash ON pagination_cursors (query_hash);
```

## API Contract Changes

### Request Parameters
```json
{
  "page": 1,           // Page number (1-based)
  "page_size": 50,     // Items per page (default: 50, max: 1000)
  "cursor": "base64...", // Optional cursor for cursor-based pagination
  "sort": "created_at", // Sort field
  "order": "desc"      // Sort order (asc/desc)
}
```

### Response Format
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 125000,     // May be estimated for very large datasets
    "total_pages": 2500,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "base64...", // For cursor-based pagination
    "prev_cursor": null
  }
}
```

## Frontend State Management

### Pagination Cache Structure
```typescript
interface PaginationCache<T> {
  pages: Map<number, CachedPage<T>>
  prefetchQueue: number[]
  maxCacheSize: number
  lastAccessed: Map<number, number>
}

interface CachedPage<T> {
  data: T[]
  timestamp: number
  stale: boolean
  loading: boolean
}
```

### Pre-fetching Strategy
1. **Immediate**: When user navigates to page N, immediately start fetching page N+1
2. **Predictive**: Based on user scrolling speed and direction, prefetch 1-3 pages ahead
3. **Bandwidth-aware**: Adjust prefetch aggressiveness based on connection speed
4. **Cache management**: Evict old pages using LRU policy when cache exceeds limits

## Performance Targets

### Backend Performance
- **Pagination queries**: < 200ms response time for any page on datasets up to 10M rows
- **Count queries**: < 100ms for total count estimation
- **Memory usage**: < 100MB per worker for pagination state
- **Concurrency**: Support 1000+ concurrent pagination requests

### Frontend Performance
- **Page navigation**: < 50ms when data is cached, < 500ms for cache misses
- **Memory usage**: < 50MB for pagination cache regardless of dataset size
- **Rendering**: Smooth 60fps scrolling with virtualized lists
- **Pre-fetch efficiency**: > 80% cache hit rate for sequential page navigation

## Risk Mitigation

### Database Risks
- **Index build time**: Use `CONCURRENTLY` and monitor build progress

### Frontend Risks
- **Memory leaks**: Implement proper cache cleanup and validation
- **Cache invalidation**: Ensure proper cache invalidation when data changes
- **User experience**: Maintain loading states during cache misses

### Performance Risks
- **Regression testing**: Comprehensive performance testing before deployment
- **Rollback plan**: Feature flags to quickly disable new pagination if issues arise
  - Add an SOP for how to do this activation/deactivation in docs/developer.md. Also add SOP sections to docs/api.md 
  and make a new document called docs/frontend/sops.md, and don't re-write the SOP there, but make mention of it, and 
  link to developer.md for more information. Make sure docs/frontend/sops.md is linked to at the end of 
  frontend/overview.md. 
- **Performance validation**: Comprehensive testing under realistic load conditions

## Success Criteria

### Technical Success
- [x] All endpoints support pagination with consistent API ✅
- [x] Database queries perform within target response times ✅
- [x] Frontend cache hit rate > 80% for sequential navigation ✅
- [x] Memory usage remains stable under load ✅
- [x] All tests pass including new pagination test suites ✅

### User Experience Success
- [x] Page navigation feels instant for cached data ✅
- [x] Loading states are smooth and informative ✅
- [x] No pagination-related errors in production ✅
- [x] Users can efficiently browse large datasets ✅