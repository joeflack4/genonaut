# Image Generation Output Path Routing Issue

## Executive Summary

**Status**: Root cause identified, solution designed, ready for implementation

**Problem**: After fixing URL routing for backend selection, KernieGen (mock) jobs fail because the system looks for generated images in the wrong output directory (`~/Documents/ComfyUI/output` instead of `test/_infra/mock_services/comfyui/output`).

**Root Cause**: The `comfyui_output_dir` setting is hardcoded in the client and not backend-aware. Same issue exists for `comfyui_models_dir`.

**Solution**: Add `comfyui-mock-output-dir` and `comfyui-mock-models-dir` config settings, pass them as parameters to the client (mirroring the existing `backend_url` pattern), and select the correct directories in worker tasks based on backend choice.

**Impact**:
- Low risk - backward compatible (parameters are optional)
- Mirrors existing backend_url pattern
- Fixes both output dir and models dir issues
- No breaking changes to existing code

**Effort**: ~5 file changes, estimated 30-60 minutes

---

## Problem Statement

After fixing the URL routing for backend selection (KernieGen vs ComfyUI), a new issue has emerged: the system is reading from the wrong output directory when KernieGen (mock) is selected.

**Error Log**:
```
[2025-11-08 15:50:28,209: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194217: processing (subscribers: 0)
[2025-11-08 15:50:30,225: WARNING/ForkPoolWorker-9] Source file not found: ~/Documents/ComfyUI/output/gen_job_1194217_00020_.png
[2025-11-08 15:50:30,226: ERROR/ForkPoolWorker-9] Job 1194217 failed: Unable to determine primary image path for job 1194217
```

**Expected Behavior**:
- When `backend='kerniegen'` (mock) is selected -> should use `test/_infra/mock_services/comfyui/output`
- When `backend='comfyui'` (real) is selected -> should use `~/Documents/ComfyUI/output`

**Actual Behavior**:
- System is looking in `~/Documents/ComfyUI/output/` even when KernieGen is selected

## Initial Observations

1. **This was working before** - suggests a recent change broke it
2. **URL routing is now correct** - backend selection successfully routes to correct URLs (8189 for mock, 8000 for real)
3. **Output path is hardcoded or not dynamic** - the output directory isn't being selected based on backend choice
4. **Potential brittleness** - the system may have multiple hardcoded assumptions about paths that aren't backend-aware

## Questions to Answer

### 1. How does the system determine output paths?
- [ ] Where is `comfyui-output-dir` configured? (config/base.json)
- [ ] Is there a separate config for mock output dir?
- [ ] How does the worker/client know which output dir to use?
- [ ] Is output dir passed as a parameter or read from settings?

### 2. Where does output path selection happen?
- [ ] In ComfyUIWorkerClient initialization?
- [ ] In the worker task (tasks.py)?
- [ ] In the file storage service?
- [ ] When parsing ComfyUI response?

### 3. What other backend-specific configuration might exist?
- [ ] Model directories
- [ ] Checkpoint paths
- [ ] API endpoints beyond the base URL
- [ ] Authentication/credentials
- [ ] Workflow templates

### 4. How does the mock service work?
- [ ] Does it return actual file paths or mock paths?
- [ ] Where does it store generated images?
- [ ] Does it follow the same path structure as real ComfyUI?

## Investigation Plan

### Phase 1: Understand Current Architecture (Read-only) [COMPLETE]
- [x] Read `genonaut/api/services/comfyui_client.py` - understand how client initializes and uses output dir
- [x] Read `genonaut/worker/comfyui_client.py` - understand worker client implementation
- [x] Read `genonaut/worker/tasks.py` (full file) - understand complete job processing flow
- [x] Read `test/_infra/mock_services/comfyui/server.py` - understand what mock returns
- [x] Check config files for all output-dir related settings
- [x] Trace the complete flow: job creation -> submission -> response -> file retrieval

**Key Findings**:
- Client accepts `backend_url` parameter but NOT `output_dir` parameter
- Output dir is always read from `self.settings.comfyui_output_dir` (line 312)
- Mock service is hardcoded to use `test/_infra/mock_services/comfyui/output` (server.py:212)
- Worker tasks.py selects backend URL correctly but doesn't select output dir
- No file storage service involved in path resolution - happens in client

### Phase 2: Identify All Backend-Specific Settings [COMPLETE]
- [x] List all settings that should vary by backend (URL, output dir, model dir, etc.)
- [x] Check if these settings exist in config files
- [x] Determine which settings are backend-aware vs hardcoded
- [x] Map out the configuration load order for each setting

**Backend-Specific Settings Identified**:

| Setting | Real ComfyUI | KernieGen (Mock) | Backend-Aware? | Config Key |
|---------|-------------|------------------|----------------|------------|
| URL | http://localhost:8000 | http://localhost:8189 | YES (fixed!) | comfyui-url, comfyui-mock-url |
| Output Dir | ~/Documents/ComfyUI/output | test/_infra/mock_services/comfyui/output | NO (BUG) | comfyui-output-dir only |
| Models Dir | ~/Documents/ComfyUI/models | (not configured) | NO (BUG) | comfyui-models-dir only |
| Port | 8000 | 8189 | Sort of | comfyui-mock-port exists but unused |

**Other Settings (Not Backend-Specific)**:
- comfyui-timeout, comfyui-poll-interval, comfyui-max-wait-time
- comfyui-default-checkpoint, comfyui-default-width/height/batch-size
- These are application defaults, not backend-specific

### Phase 3: Design Solution [COMPLETE]
- [x] Decide on approach: **Option A** (mirrors existing URL pattern)
- [x] Identify all code locations that need changes
- [x] Plan backward compatibility considerations
- [x] Design validation/testing strategy

**Selected Approach: Option A**

Add separate config settings and pass as parameters (mirrors backend_url pattern):
1. Add `comfyui-mock-output-dir` and `comfyui-mock-models-dir` to base.json
2. Modify `ComfyUIClient.__init__()` to accept optional `output_dir` and `models_dir` parameters
3. Modify worker `tasks.py` to select and pass correct dirs based on backend choice
4. Client uses provided dirs instead of always using settings.comfyui_output_dir

**Code Locations Requiring Changes**:
1. `config/base.json` - Add new config keys
2. `genonaut/api/services/comfyui_client.py`:
   - `__init__()` - Add parameters (lines 33-48)
   - `get_output_files()` - Use dynamic output_dir (line 312)
   - `read_output_file()` - Use dynamic output_dir (line 334)
3. `genonaut/worker/comfyui_client.py`:
   - `__init__()` - Accept and pass parameters (lines 24-32)
4. `genonaut/worker/tasks.py`:
   - `process_comfy_job()` - Select and pass correct dirs (lines 90-105)

**Backward Compatibility**:
- Parameters are optional - if not provided, defaults to settings values (current behavior)
- No breaking changes to existing code that doesn't use backend selection
- Tests that don't specify backend will continue to work

### Phase 4: Implementation [COMPLETE]

#### Step 1: Update Configuration [COMPLETE]
- [x] Add `comfyui-mock-output-dir` to config/base.json
  - Value: `test/_infra/mock_services/comfyui/output`
- [x] Add `comfyui-mock-models-dir` to config/base.json
  - Value: `test/_infra/mock_services/comfyui/models`
- [x] Added fields to Settings class in genonaut/api/config.py

#### Step 2: Update ComfyUIClient [COMPLETE]
- [x] Modified `genonaut/api/services/comfyui_client.py`:
  - [x] Added `output_dir` parameter to `__init__()` (optional)
  - [x] Added `models_dir` parameter to `__init__()` (optional)
  - [x] Store as instance variables (self.output_dir, self.models_dir)
  - [x] Default to settings values if not provided
  - [x] Updated `get_output_files()` to use self.output_dir (line 328-330)
  - [x] Updated `read_output_file()` to use self.output_dir (line 350)
  - [x] Updated docstrings to document new parameters

#### Step 3: Update ComfyUIWorkerClient [COMPLETE]
- [x] Modified `genonaut/worker/comfyui_client.py`:
  - [x] Added `output_dir` parameter to `__init__()` (optional)
  - [x] Added `models_dir` parameter to `__init__()` (optional)
  - [x] Pass to parent `__init__()` via super()
  - [x] Updated docstrings

#### Step 4: Update Worker Task [COMPLETE]
- [x] Modified `genonaut/worker/tasks.py`:
  - [x] In `process_comfy_job()` added backend-aware directory selection (lines 90-111):
    - [x] Added output_dir selection logic
    - [x] Added models_dir selection logic
    - [x] If backend='comfyui' -> uses settings.comfyui_output_dir and settings.comfyui_models_dir
    - [x] If backend='kerniegen' -> uses settings.comfyui_mock_output_dir and settings.comfyui_mock_models_dir
  - [x] Pass output_dir and models_dir to ComfyUIWorkerClient() constructor (lines 113-118)
  - [x] Added logging to show which dirs are being used (lines 105, 111)

#### Step 5: Restart Services [COMPLETE]
- [x] Restarted Celery worker to load new configuration
- [x] Worker started successfully and loaded new settings

### Phase 5: Testing & Verification [IN PROGRESS]
- [x] Test KernieGen backend end-to-end - Found path joining issue
- [ ] Test ComfyUI backend end-to-end
- [x] Verify logs show correct paths - Identified double slash issue
- [ ] Verify files are found and processed correctly
- [ ] Test switching between backends

### Phase 6: Fix File Organization Issue [COMPLETE]

**Problem Discovered**: After implementing Phase 4, testing revealed a second issue:
- Mock service correctly returned files from `test/_infra/mock_services/comfyui/output/`
- But FileStorageService was **moving** those files to `~/Documents/ComfyUI/output/generations/...`
- This caused the frontend to show broken image links

**Root Cause**:
1. Mock service was copying `test/_infra/mock_services/comfyui/input/kernie_512x768.jpg` to output dir
2. FileStorageService then moved that file to the hardcoded destination directory
3. The destination was always `~/Documents/ComfyUI/output/` regardless of backend

**Solution Implemented** (Option B - user preference):
- Modified mock service to return direct reference to input file (no copying)
- Modified worker task to skip file organization for KernieGen backend
- For KernieGen: Files stay at `test/_infra/mock_services/comfyui/input/kernie_512x768.jpg`
- For ComfyUI: Files still get organized into user/date directory structure

**Changes Made**:

1. **Mock Service** (`test/_infra/mock_services/comfyui/server.py`):
   - Removed file copying logic (lines 94-105)
   - Now returns absolute path to input file directly: `str(input_file)`
   - Simplified `process_job()` method

2. **Worker Task** (`genonaut/worker/tasks.py`):
   - Made `backend_choice` available throughout function (line 94)
   - Added conditional file organization (lines 202-212):
     - If `backend_choice == 'kerniegen'`: Use output_paths directly (no organization)
     - If `backend_choice == 'comfyui'`: Call file_service.organize_generation_files()
   - Added logging for KernieGen path usage

**Rationale**:
- KernieGen is for testing - no need to copy files or organize them
- Keeps test infrastructure simple and predictable
- Matches user preference for "option b" (reference file directly)
- Real ComfyUI still gets proper file organization

**Services Restarted**:
- Mock ComfyUI service (port 8189) - running
- Celery worker - running
- Redis - running

### Phase 7: Fix Path Joining Issue [COMPLETE]

**Problem Discovered**: Testing revealed a path joining issue where absolute paths were being concatenated:

```
test/_infra/mock_services/comfyui/output//Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/input/kernie_512x768.jpg
```

**Root Cause**:
- Mock service was returning **absolute path** in `filename` field: `str(input_file)`
- Client code in `get_output_files()` was joining `output_dir` with `filename`
- Result: `output_dir + "/" + absolute_path` created invalid double-slash path

**Solution Implemented**:
- Modified mock service to return **relative path** from output directory
- Changed from `str(input_file)` (absolute) to `"../input/{filename}"` (relative)
- Client now correctly joins: `test/_infra/mock_services/comfyui/output/../input/kernie_512x768.jpg`
- Which resolves to: `test/_infra/mock_services/comfyui/input/kernie_512x768.jpg`

**Changes Made**:

1. **Mock Service** (`test/_infra/mock_services/comfyui/server.py:104`):
   ```python
   # Before: "filename": str(input_file)  # Absolute path
   # After:  "filename": "../input/{input_file.name}"  # Relative path
   ```

**Services Restarted**:
- Mock ComfyUI service (port 8189) - restarted to apply changes

### Phase 8: Content ID Collision Issue [CRITICAL ARCHITECTURAL PROBLEM]

**Status**: Root cause identified - requires architectural decision

**Problem Discovered**: Images not rendering in frontend even though generation succeeds and path is correct.

**Error from API**:
```
INFO: 127.0.0.1:57661 - "GET /api/v1/images/65252 HTTP/1.1" 404 Not Found
```

**Root Cause Analysis**:

#### 1. Database Schema - Partitioned Tables with ID Collision

The system uses PostgreSQL table partitioning with a parent table `content_items_all` and two child partitions:
- `content_items` (source_type = 'items') - User-generated content
- `content_items_auto` (source_type = 'auto') - Auto-generated content

**CRITICAL ISSUE**: Both tables use independent INTEGER IDENTITY sequences, resulting in ID collisions:

```sql
-- Query shows TWO different records with id=65252
SELECT id, source_type, content_data FROM content_items_all WHERE id = 65252;

id    | source_type | content_data
------+-------------+----------------------------------------------------------
65252 | auto        | io/storage/images/6dcd03a7-cafb-4df4-a271-a29db068296d.png
65252 | items       | test/_infra/mock_services/comfyui/output/../input/kernie_512x768.jpg
```

**Primary Key Structure**:
- Individual tables: `PRIMARY KEY (id)` - single column
- Parent table: Partitioned by `source_type`
- Result: IDs are NOT unique across the partition hierarchy

#### 2. Image Serving Endpoint - Missing source_type Parameter

File: `genonaut/api/routes/images.py`

Current implementation (lines 43-50):
```python
# Check if file_path is a content_id (numeric)
use_db_lookup = file_path.isdigit()
if use_db_lookup:
    content_id = int(file_path)

    # Try to find content in both tables
    content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not content:
        content = db.query(ContentItemAuto).filter(ContentItemAuto.id == content_id).first()
```

**Problem**: The endpoint tries `ContentItem` first, then falls back to `ContentItemAuto`.
- When ID exists in both tables, it ALWAYS returns the first match (from `content_items`)
- No way to specify which partition to query
- The lookup is non-deterministic when IDs collide

#### 3. Frontend Request - No source_type Information

File: `frontend/src/utils/image-url.ts`

Current implementation (line 20-23):
```typescript
export function getImageUrl(contentId: number, thumbnail?: 'small' | 'medium' | 'large'): string {
  const baseUrl = getApiBaseUrl()
  const path = `/api/v1/images/${contentId}`
  // ...
}
```

**Request format**: `GET /api/v1/images/{content_id}`
- No source_type parameter
- No way to disambiguate which partition to query
- Assumes content_id is globally unique (it's not)

#### 4. Content Creation - Source Type Determined by Service Class

File: `genonaut/api/services/content_service.py`

The `ContentService` class is instantiated with a specific model:
```python
def __init__(self, db: Session, *, model: Type[ContentItem] = ContentItem):
    self.model: Type[ContentItem] = model
    self.repository = ContentRepository(db, model=model)
```

Worker task creates content in `ContentItem` table (lines 240-248 in tasks.py):
```python
content_item = content_service.create_content(
    title=content_title,
    content_type='image',
    content_data=primary_image,
    prompt=job.prompt,
    creator_id=job.user_id,
    item_metadata=metadata,
)
```

**Result**: Generated images go into `content_items` (source_type='items'), not `content_items_auto`

## Architectural Problem Summary

**The Fundamental Issue**: The system has a **composite key** in practice `(id, source_type)` but treats `id` as if it's a **global unique identifier**.

### Current State:
- Database: Uses partitioning where `(id, source_type)` forms the logical key
- API: Expects `id` alone to be sufficient for lookups
- Frontend: Only knows about `content_id`, not `source_type`
- Result: **Ambiguous lookups when IDs collide**

### Why This Happens:
1. Each partition has its own IDENTITY sequence
2. Sequences start from 1 and increment independently
3. IDs collide as soon as both partitions have records
4. System was designed for partitioning but not for the consequences

### Impact:
- **Data Corruption Risk**: Wrong content returned for lookup
- **Unpredictable Behavior**: Which record is returned depends on query order
- **Frontend Breaks**: Cannot reliably fetch the correct image
- **API Limitation**: No way to specify partition in current API design

## Proposed Solutions

### Option A: Shared Sequence Across Partitions [RECOMMENDED]

**Description**: Use a single shared sequence for both partitions to ensure globally unique IDs.

**Implementation**:
1. Create a shared sequence: `CREATE SEQUENCE content_items_id_seq;`
2. Modify both tables to use this sequence: `id INTEGER DEFAULT nextval('content_items_id_seq')`
3. No API changes required
4. No frontend changes required

**Pros**:
- Simplest solution - no API or frontend changes
- Maintains backward compatibility
- IDs are truly unique across all content
- Minimal migration effort
- Aligns with how system currently assumes IDs work

**Cons**:
- Loses some benefits of partitioning (independent sequences per partition)
- Migration required to reconcile existing ID collisions
- Non-contiguous ID ranges per partition (gaps in sequences)

**Migration Strategy**:
1. Find all colliding IDs: `SELECT id FROM content_items_all GROUP BY id HAVING COUNT(*) > 1`
2. Reassign IDs in one partition to avoid collisions
3. Create shared sequence starting from `MAX(id) + 1`
4. Update both table definitions to use shared sequence
5. Test thoroughly

**Estimated Effort**: 2-4 hours (1 hour for migration script, 1-2 hours for testing, 1 hour buffer)

---

### Option B: Add source_type to API Requests

**Description**: Pass `source_type` alongside `content_id` in API requests.

**Implementation**:
1. Update API endpoint to accept query parameter: `GET /api/v1/images/{id}?source_type=items`
2. Update frontend to include source_type in requests
3. Update all content response models to include source_type
4. Frontend tracks both id and source_type for each content item

**Pros**:
- Preserves partition independence
- Makes partition structure explicit in API
- No database migration required
- Allows for future partition-specific optimizations

**Cons**:
- Breaking API change (requires version bump or deprecation period)
- Frontend changes across many components
- More complex - requires tracking two values instead of one
- Increases API request complexity
- Every content reference needs both id + source_type

**Required Changes**:
- API routes: `/images.py`, `/content.py`
- Frontend utilities: `image-url.ts`, all content-related hooks
- Response models: Add `source_type` field to all content responses
- Database queries: Add source_type filters everywhere

**Estimated Effort**: 1-2 weeks (significant refactoring required)

---

### Option C: Composite Key with URL Encoding

**Description**: Encode both id and source_type into a single URL-safe identifier.

**Implementation**:
1. Create compound ID format: `{source_type}-{id}` (e.g., `items-65252`, `auto-65252`)
2. Update API to parse compound IDs
3. Update frontend to use compound IDs
4. Add helper functions for encoding/decoding

**Pros**:
- Single identifier in API (simpler than Option B)
- No database migration
- Makes partition explicit without query parameters
- Relatively clean API design

**Cons**:
- Changes ID format throughout system
- Requires careful parsing and validation
- Could break existing integrations
- String manipulation overhead
- Less intuitive than pure integers

**Required Changes**:
- API: Parser for compound IDs in image/content endpoints
- Frontend: Encode IDs before requests, update all usages
- Database queries: Extract id and source_type from compound key
- Validation: Ensure proper format, handle edge cases

**Estimated Effort**: 1 week (less than Option B, more than Option A)

---

### Option D: Use UUIDs as Primary Key

**Description**: Replace integer IDs with UUIDs for globally unique identifiers.

**Implementation**:
1. Add UUID column to both tables
2. Migrate existing data to have UUIDs
3. Switch primary key to UUID
4. Update all foreign key references
5. Update API and frontend to use UUIDs

**Pros**:
- Globally unique by design
- No collision possible
- Industry standard for distributed systems
- Better for future scaling (e.g., multi-region)

**Cons**:
- MAJOR breaking change - affects entire system
- Large database migration (all foreign keys)
- Performance impact (UUIDs are larger, slower to index)
- User-facing ID changes (less friendly than integers)
- Months of work for complete migration

**Estimated Effort**: 2-4 weeks minimum (very large refactor)

---

### Option E: Query parent table instead of child tables

**Description**: Query `content_items_all` and let PostgreSQL route to correct partition.

**Implementation**:
1. Change SQLAlchemy models to query parent table
2. Ensure source_type is always included in WHERE clause for partition pruning
3. Update image endpoint to query parent table

**Pros**:
- Leverages PostgreSQL partitioning correctly
- Minimal code changes
- No API changes if we still accept colliding IDs (just query differently)

**Cons**:
- Doesn't solve ID collision problem, just masks it
- Still need source_type to disambiguate (back to Option B)
- Could return wrong content if source_type not specified
- Performance may be worse without partition pruning

**Estimated Effort**: 1-2 days (not recommended - doesn't solve root cause)

---

## Recommendation: Option A (Shared Sequence)

**Rationale**:
1. **Minimal disruption**: No API or frontend changes
2. **Quick implementation**: 2-4 hours vs weeks for other options
3. **Fixes root cause**: Eliminates ID collision permanently
4. **Aligns with current architecture**: System already assumes IDs are unique
5. **Low risk**: Well-understood PostgreSQL pattern

**Trade-off accepted**: Lose independent sequences per partition, but gain data integrity and system correctness.

**Next Steps if Option A approved**:
1. Write migration script to identify and fix existing collisions
2. Create shared sequence
3. Update Alembic migration files
4. Test with demo database
5. Apply to all environments
6. Verify image serving works correctly

## Implementation Summary

**Status**: Path routing COMPLETE, but blocked by ID collision issue

**Changes Made**:

1. **Configuration** (`config/base.json`):
   - Added `comfyui-mock-output-dir`: `test/_infra/mock_services/comfyui/output`
   - Added `comfyui-mock-models-dir`: `test/_infra/mock_services/comfyui/models`

2. **Settings Schema** (`genonaut/api/config.py`):
   - Added `comfyui_mock_output_dir` field (line 81)
   - Added `comfyui_mock_models_dir` field (line 82)

3. **ComfyUI Client** (`genonaut/api/services/comfyui_client.py`):
   - Added `output_dir` and `models_dir` optional parameters to `__init__()`
   - Store as instance variables with fallback to settings
   - Updated `get_output_files()` to use `self.output_dir`
   - Updated `read_output_file()` to use `self.output_dir`
   - Updated docstrings

4. **Worker Client** (`genonaut/worker/comfyui_client.py`):
   - Added `output_dir` and `models_dir` parameters
   - Pass through to parent class

5. **Worker Task** (`genonaut/worker/tasks.py`):
   - Extended backend selection logic to include directories
   - Select `output_dir` and `models_dir` based on backend choice
   - Pass directories to client constructor
   - Added logging for directory selection

**Files Modified**: 5 files
**Lines Changed**: ~50 lines

**Backward Compatibility**: ✓
- All new parameters are optional
- Defaults to existing behavior if not provided
- No breaking changes

**Ready for Testing**: The implementation is complete and Celery worker has been restarted with the new configuration. Ready to test KernieGen backend end-to-end.

## Key Files to Examine

### Configuration
- `config/base.json` - check all comfyui-related settings
- `env/.env` - check for any output dir overrides

### Backend Client Code
- `genonaut/api/services/comfyui_client.py` - API client
- `genonaut/worker/comfyui_client.py` - Worker client
- `genonaut/worker/tasks.py` - Task processing

### Mock Service
- `test/_infra/mock_services/comfyui/server.py` - Mock implementation

### File Storage
- Search for files related to file storage, image organization
- Look for code that resolves/validates image paths

## Root Cause Analysis

**FOUND THE BUG!**

The output directory path is hardcoded to use `self.settings.comfyui_output_dir` regardless of which backend is selected.

### Evidence Trail:

1. **Mock service returns** (server.py:108-111):
   ```python
   job["output_files"].append({
       "filename": output_filename,  # Just filename, no full path
       "subfolder": "",
       "type": "output"
   })
   ```

2. **Client constructs full path** (comfyui_client.py:312-315):
   ```python
   file_path = f"{self.settings.comfyui_output_dir}/{subfolder}/{filename}"
   # ALWAYS uses comfyui_output_dir, even when backend is mock!
   ```

3. **Current config** (base.json:15):
   ```json
   "comfyui-output-dir": "~/Documents/ComfyUI/output"
   ```
   No separate `comfyui-mock-output-dir` exists

4. **What should happen**:
   - When backend='kerniegen' (mock) -> use `test/_infra/mock_services/comfyui/output`
   - When backend='comfyui' (real) -> use `~/Documents/ComfyUI/output`

### The Same Problem Exists for Models Dir

Looking at config, there's also:
- `comfyui-models-dir`: `~/Documents/ComfyUI/models` (line 16)
- No separate mock models dir

This will likely cause issues when fetching available models from different backends.

### Solution Design

**Option A: Add separate mock config settings** (RECOMMENDED)
- Add `comfyui-mock-output-dir` to base.json
- Add `comfyui-mock-models-dir` to base.json
- Pass `output_dir` parameter to client init (like `backend_url`)
- Client uses provided `output_dir` instead of `self.settings.comfyui_output_dir`

**Option B: Auto-detect from URL**
- Map URL to corresponding output/models directories
- More brittle, couples URL to filesystem assumptions

**Option C: Backend-specific configuration objects**
- Create structured backend configs in JSON
- More complex but most flexible for future backends

## Notes

- **Root cause confirmed**: The `comfyui_output_dir` setting is being used for both backends
- **Brittleness confirmed**: Models dir has same issue; likely other settings too
- **Configuration philosophy**: Should follow the same pattern as URL selection - dynamic based on backend choice
- **Mock service path**: `test/_infra/mock_services/comfyui/output` (from server.py:212)
