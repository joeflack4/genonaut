# Generation Page - LoRA Table Enhancement - Tasks

## Overview
Enhance the LoRA selection modal with a paginated table view that shows compatibility and optimality indicators based on the currently selected checkpoint model.

## Tags
- later: Non-critical tasks deferred to after main functionality is complete (e.g., unit tests, E2E tests)

## Phase 1: API Enhancement

### 1.1 Update LoRA API endpoint
- [x] Add optional query parameters to GET `/api/v1/lora-models/`
  - `page`: Page number (default: 1)
  - `page_size`: Items per page (default: 10)
  - `checkpoint_id`: UUID of checkpoint to check compatibility against
- [x] Update `LoraModelRepository` to support pagination via `get_paginated()` method
- [x] Add compatibility and optimality checking methods in `LoraModelService`
- [x] Update `LoraModelListResponse` to include pagination metadata
- [x] Test API endpoint with curl - verified pagination and compatibility flags working

### 1.2 Update response models
- [x] Add `LoraModelPaginationMeta` model with page, page_size, total, total_pages
- [x] Add pagination metadata to `LoraModelListResponse`
- [x] Add `is_compatible` boolean field to `LoraModelResponse` (computed based on checkpoint)
- [x] Add `is_optimal` boolean field to `LoraModelResponse` (computed based on checkpoint)

## Phase 2: Frontend Service Layer

### 2.1 Update TypeScript types
- [x] Add pagination parameters to domain types
- [x] Update `LoraModel` type with `isCompatible` and `isOptimal` fields
- [x] Update API types to match backend changes
- [x] Add `PaginatedLoraModels` and `LoraModelPaginationMeta` types

### 2.2 Update LoRA service
- [x] Add `getPaginated()` method with `LoraModelQueryParams`
- [x] Add checkpoint filtering via `checkpointId` parameter
- [x] Update service to handle paginated responses
- [x] Transform API pagination metadata to domain types

### 2.3 Update hook
- [x] Update `useLoraModels` hook to accept `LoraModelQueryParams` and pagination
- [x] Auto-refetch when checkpoint changes via query key dependency

## Phase 3: Frontend UI Components

### 3.1 Create table component
- [x] Replace List component with MUI Table in LoRA dialog
- [x] Add table headers: Name, Description, Compatible, Optimal, Status
- [x] Use CheckCircle and Cancel icons for Compatible/Optimal columns
- [x] Keep "Added" chip in Status column
- [x] Make table clickable to add LoRA models

### 3.2 Add pagination controls
- [x] Add MUI TablePagination component
- [x] Handle page changes with `handleLoraPageChange`
- [x] Fixed at 10 rows per page

### 3.3 Update ModelSelector component
- [x] Pass currently selected checkpoint ID to LoRA query
- [x] Prefetch LoRA data when checkpoint changes (auto via useEffect)
- [x] Update dialog to use new table layout with sticky header
- [x] Reset page to 0 when checkpoint changes

## Phase 4: Testing & Verification

### 4.1 Manual testing
- [x] Test API pagination endpoint with curl
- [x] Test compatibility/optimality flags with checkpoint_id
- [ ] Test table displays correctly in browser with all columns
- [ ] Test pagination works in UI (next/previous page)
- [ ] Test compatibility indicators update when checkpoint changes
- [ ] Test optimality indicators show correctly
- [ ] Verify "Added" status persists across pages

### 4.2 Automated tests
- [ ] Add unit tests for compatibility/optimality logic @skipped-until-later
- [ ] Add E2E tests for table interaction @skipped-until-later
- [ ] Add E2E tests for pagination @skipped-until-later

## Progress Tracking
Current phase: Phase 4 (Testing)
Status: All implementation complete, ready for browser testing
