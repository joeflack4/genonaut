### Q5: ComfyUI routes and old code cleanup
#### Question
**Context**: Phase 9.3 asks to "Remove references to `comfyui_generation_requests` table". The note says "the only ref 
is the `ComfyUIGenerationRequest` class, and it has no other refs." However, I found extensive references:

**Files using the old ComfyUIGenerationRequest model**:
1. `/genonaut/api/routes/comfyui.py` - Full API router with `/api/v1/comfyui/generate` endpoint
2. `/genonaut/api/services/comfyui_generation_service.py` - Service layer
3. `/genonaut/api/repositories/comfyui_generation_repository.py` - Repository layer
4. Multiple test files using this service/repository

**Current state**:
- These routes are ACTIVE (registered in main.py)
- Users can still POST to `/api/v1/comfyui/generate`
- This creates records in the old `comfyui_generation_requests` table
- The new system uses `/api/v1/generation-jobs` endpoint with the merged `generation_jobs` table

**Question**: Should I:

**Option A**: Delete everything (recommended for clean architecture)
- Remove `ComfyUIGenerationRequest` class from schema.py
- Delete `/api/routes/comfyui.py`
- Delete `/api/services/comfyui_generation_service.py`
- Delete `/api/repositories/comfyui_generation_repository.py`
- Delete or mark skip on all related test files
- Create migration to drop `comfyui_generation_requests` table
- Unregister comfyui router from main.py

**Option B**: Keep for backwards compatibility
- Keep old routes/service/repository
- Leave table in database
- Maintain dual API until deprecation period

**Option C**: Soft deprecation
- Keep routes but mark as deprecated in OpenAPI docs
- Add warnings in responses
- Document migration path in README

**My recommendation**: Option A - clean break since we've already migrated the data. The new `/api/v1/generation-jobs` endpoint has all the same ComfyUI capabilities.

#### Answer
I think that the descriptions of this task in the spec document were not clear. We do not want to remove all of this 
functionality. This is simply a follow-up on previous work thta was done to merge the generation_jobs and the 
comfyui_generation_requests table. Right now, the only "generation job" that we are focusing on are ComfyUI image 
generation jobs. The only table for this should be the generation_jobs table. Now that we have merged/migrated over all 
of the useful fields from `comfyui_generation_requests` into this table, we have no need for the table anymore. And 
therefore, I believe that the class that it is based on, `ComfyUIGenerationRequest`, will likely also need to be deleted.

It seems like, based on what you are saying, that the previous work that was done did not consider the fact that there 
is a lot of the codebase that is connected to `ComfyUIGenerationRequest`. If that is the case, then we need to wire 
everything to use the `GenerationJob` table. It seems like you will need to ensure that `GenerationJob` has all of the 
methods, all of the functionality in it that `ComfyUIGenerationRequest` had.

The basic flow should be something like this:

1. User interacts with "Image Generation" page, to generate new images, etc.
2. The frontend calls to the backend routes to handle this.
3. Eventually, DB interaction will need to happen. This should utilize the `GenerationJob` model and the 
`generation_jobs` table.

You might want to read about what was done in `nots/celery.md` to get caught back up to speed. For example, you can look
at this subsection:  

```
### Table Merge (COMPLETED)
The `comfyui_generation_requests` and `generation_jobs` tables have been merged into `generation_jobs`. 
```
