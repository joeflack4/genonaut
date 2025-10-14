# "Image Generation" page: Successful generation fix - image not being displayed
## Problem description
We've fixed a lot of problems preventing image generation from occurring successfully, both for ComfyUI and also for 
the mock. I'm actually currently set up using the mock for now as my main development backend for image generation.

But I've noticed that even when a successful generation occurs, and even when the frontend displays a "Completed" 
message (also says "Generation completed successfully!"), there are a few things that are broken. Right now I wanna focus on the image not being displayed.

## Initial investigation
I'm troubleshooting this live. You can look at this screenshot: [/Users/joeflack4/Desktop/gen.png](/Users/joeflack4/Desktop/gen.png).

When I inspect in the browser, I see this HTML for where the image should be:

`<img class="MuiCardMedia-root MuiCardMedia-media MuiCardMedia-img css-zwexhw-MuiCardMedia-root" alt="cat" src="/api/v1/images/65013">`

So, I am investigating, and I open up the URL in the api for 'src' and I see this:
I enter this manually in my browser: http://localhost:8001/api/v1/images/65013

Result:
```
{
"detail": "Image not found"
}
```

I investigate further:

I can see that the latest row for generation_jobs shows the image I just made. And I see the match for its content_id (65013) in the content_itemst able.

See:
- notes/gen_result_latest.csv
- notes/content_items__by_id__65013.csv

I see that content_items shows the outpath is:
- /Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/output/generations/121e194b-4caa-4b81-ad4f-86ca3919d5b9/2025/10/09/gen_1193924_gen_job_1193924_00014_.png

I checked and the image is really there.

I also see the celery worker correctly shows that path:

```
:03:20,858: INFO/ForkPoolWorker-8] Generated thumbnails for generation 1193923: gen_1193923_gen_job_1193923_00013_.png
[2025-10-09 16:03:20,890: INFO/ForkPoolWorker-8] Job 1193923 completed successfully
[2025-10-09 16:03:20,893: INFO/ForkPoolWorker-8] Published update to genonaut_demo:job:1193923: completed (subscribers: 1)
[2025-10-09 16:03:20,895: INFO/ForkPoolWorker-8] Task genonaut.worker.tasks.run_comfy_job[7946e54f-ba81-4c04-837e-afa3c75101d4] succeeded in 2.9519621250219643s: {'job_id': 1193923, 'status': 'completed', 'content_id': 65012, 'output_paths': ['/Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/output/generations/121e194b-4caa-4b81-ad4f-86ca3919d5b9/2025/10/09/gen_1193923_gen_job_1193923_00013_.png'], 'prompt_id': '841b5b19-a10a-411a-8c64-b2b6a66927a9'}
[2025-10-09 16:03:38,667: INFO/MainProcess] Task genonaut.worker.tasks.run_comfy_job[3cc9ad6a-3e8d-4f11-b2d9-65890bba9eb2] received
[2025-10-09 16:03:38,668: INFO/ForkPoolWorker-8] Starting ComfyUI job 1193924
[2025-10-09 16:03:38,673: INFO/ForkPoolWorker-8] Job 1193924 status updated to 'running'
[2025-10-09 16:03:38,677: INFO/ForkPoolWorker-8] Published update to genonaut_demo:job:1193924: started (subscribers: 0)
[2025-10-09 16:03:38,686: INFO/ForkPoolWorker-8] Job 1193924 submitted to ComfyUI (prompt_id=ab32561e-0a97-40c7-9f99-b99eb4fea75f)
[2025-10-09 16:03:38,688: INFO/ForkPoolWorker-8] Published update to genonaut_demo:job:1193924: processing (subscribers: 0)
[2025-10-09 16:03:40,711: INFO/ForkPoolWorker-8] Organized file: /Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/output/gen_job_1193924_00014_.png -> /Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/output/generations/121e194b-4caa-4b81-ad4f-86ca3919d5b9/2025/10/09/gen_1193924_gen_job_1193924_00014_.png
[2025-10-09 16:03:41,399: INFO/ForkPoolWorker-8] Generated thumbnails for generation 1193924: gen_1193924_gen_job_1193924_00014_.png
[2025-10-09 16:03:41,410: INFO/ForkPoolWorker-8] Job 1193924 completed successfully
[2025-10-09 16:03:41,414: INFO/ForkPoolWorker-8] Published update to genonaut_demo:job:1193924: completed (subscribers: 1)
[2025-10-09 16:03:41,416: INFO/ForkPoolWorker-8] Task genonaut.worker.tasks.run_comfy_job[3cc9ad6a-3e8d-4f11-b2d9-65890bba9eb2] succeeded in 2.7483858338091522s: {'job_id': 1193924, 'status': 'completed', 'content_id': 65013, 'output_paths': ['/Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/output/generations/121e194b-4caa-4b81-ad4f-86ca3919d5b9/2025/10/09/gen_1193924_gen_job_1193924_00014_.png'], 'prompt_id': 'ab32561e-0a97-40c7-9f99-b99eb4fea75f'}
```

## Ideation: Possible root cause & solution
I think that the fixation on us relying on a configured ComfyUI output dir (`comfyui-output-dir` in the JSON configs,
and called `COMFYUI_OUTPUT_DIR` in the .env files) is problematic. Let's update our API server logic to do this:

When the DB is queried, and the `content_data` field in `content_items` or `content_items_auto` shows a full path, e.g. `/Users/joeflack4/projects/genonaut/test/_infra/mock_services/comfyui/output/generations/121e194b-4caa-4b81-ad4f-86ca3919d5b9/2025/10/09/gen_1193924_gen_job_1193924_00014_.png`,
then we should ignore the configured `comfyui-output-dir` and just use the path as-is. However, if `content_data` just
shows a filename and no path, then let's create a path, using `comfyui-output-dir`.

See if this fixes the problem. If not, see if you can figure out what the problem is.

## Final Report

### Problem Summary
Images were not displaying in the frontend after successful generation, despite the backend showing completion and the image files existing on disk.

### Root Causes Identified

**Issue 1: Backend API endpoint not handling content_id lookups**
- The `/api/v1/images/{file_path}` endpoint expected file paths, not content IDs
- Frontend was passing content_id (e.g., `65013`) but backend couldn't resolve it to an actual file path
- Database contained absolute paths in `content_data` field, but endpoint only used `comfyui-output-dir` config

**Issue 2: Frontend using relative URLs across different ports**
- Frontend runs on port 5173 (Vite dev server)
- Backend API runs on port 8001
- Frontend was using relative URL `/api/v1/images/65013`
- Browser tried to fetch from `http://localhost:5173/api/v1/images/65013` instead of `http://localhost:8001/api/v1/images/65013`

### Solutions Implemented

**Backend Fix (genonaut/api/routes/images.py)**:

1. Updated `serve_image()` endpoint to detect numeric content_id:
   - Check if `file_path` parameter is numeric using `isdigit()`
   - Query database (`ContentItem` or `ContentItemAuto`) to get image path from `content_data` field
   - Handle both absolute paths (use as-is) and relative paths (prepend `comfyui-output-dir`)
   - Skip security checks for database-sourced paths (already trusted)

2. Applied same logic to `get_image_info()` and `delete_thumbnails()` endpoints for consistency

3. Added imports for `ContentItem` and `ContentItemAuto` schema classes

**Frontend Fix (frontend/src/)**:

1. Created utility module `utils/image-url.ts`:
   - `getImageUrl(contentId, thumbnail?)` - Constructs absolute URLs with API base
   - `getImageUrlFromPath(path)` - Handles absolute/relative path conversion
   - Reads `VITE_API_BASE_URL` environment variable or defaults to `http://localhost:8001`

2. Updated components to use utility:
   - `components/generation/GenerationProgress.tsx` - Changed from template literal to `getImageUrl(content_id)`
   - `components/generation/ImageViewer.tsx` - Same fix

3. Created comprehensive unit tests (`utils/__tests__/image-url.test.ts`):
   - 9 tests covering all scenarios
   - Tests for default behavior, environment variables, and thumbnail parameters
   - All tests passing

### Verification

**Backend testing**:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/images/65013
# Result: 200 OK

curl -s -I -X GET http://localhost:8001/api/v1/images/65013
# Result: Content-Type: image/png, Content-Length: 97179
```

**Frontend testing**:
```bash
npm run test-unit -- src/utils/__tests__/image-url.test.ts
# Result: 9 passed (9)
```

### Files Modified

**Backend**:
- `genonaut/api/routes/images.py` - Updated 3 endpoints with content_id lookup logic

**Frontend**:
- `frontend/src/utils/image-url.ts` - New utility module
- `frontend/src/utils/__tests__/image-url.test.ts` - New test file
- `frontend/src/components/generation/GenerationProgress.tsx` - Updated image URL construction
- `frontend/src/components/generation/ImageViewer.tsx` - Updated image URL construction

**Documentation**:
- `notes/render-fixes.md` - Created detailed action plan and investigation notes

### Key Learnings

1. **Multi-layer debugging required**: The issue had both backend and frontend components that needed fixing separately
2. **Port awareness**: Development environments with frontend/backend on different ports require absolute URLs
3. **Database-driven paths**: When paths are stored in the database, API endpoints should be flexible enough to handle both absolute and relative paths
4. **Environment configuration**: Using environment variables (`VITE_API_BASE_URL`) makes the solution work across dev/staging/production
5. **Comprehensive testing**: Both unit tests (frontend utility) and manual API tests (backend) were crucial for verification
