# Celery Integration Questions

## Answered: Table merging questions

### Q1: job_type field for migrated ComfyUI records
**Context**: The `generation_jobs` table has a `job_type` field (text, image, video, audio), but 
`comfyui_generation_requests` does not. When migrating data from `comfyui_generation_requests` to `generation_jobs`, 
what value should we use for `job_type`?

A: Set to: "image"

### Q2: parameters field vs sampler_params field
**Context**: `generation_jobs` has a generic `parameters` JSONColumn, while `comfyui_generation_requests` has a specific
`sampler_params` JSONColumn. Should we:

A: Just 1 field. And make two changes:
- i. Rename it "params". 
- ii. Change the type to: JSONB

### Q3: result_content_id relationship
**Context**: `generation_jobs` has `result_content_id` linking to the generated content item. When images are generated
via ComfyUI, should we:

**Options**:
1. Create a ContentItem for each generated image and link via result_content_id
2. Store only the file paths in output_paths/thumbnail_paths without creating ContentItems
3. Create ContentItems but only link the first/primary image to result_content_id

**Recommendation**: Option 1 - create ContentItem for each image to maintain consistency with the existing data model.

A: If I understand correctly, I also agree with option 1. My assumption is that each generation job will create only 1 
image, and that we'll need to create thumbnails later. 
Let's go with 1 generation job always having 1 ContentItem. Let's also rename `result_content_id` to just `content_id`.
When we get to making thumbnails, either using ComfyUI or some other process, we will change the data model at that 
time. I may extend `generation_jobs` at that time to also include thumbnail generation jobs, or I might make another 
table. But these thumbnails will always point to the same `content_id`. 1 content ID will have 1 full size image and 
possibly several thumbnails. 

### Q4: Status value mapping
**Context**: During migration, ComfyUI requests may have status values like 'processing' that need to map to 
GenerationJob status values.

**Status Mapping**:
- 'pending' � 'pending' 
- 'processing' � 'running' (map to GenerationJob vocabulary)
- 'completed' � 'completed' 
- 'failed' � 'failed' 
- 'cancelled' � 'cancelled' 

**Recommendation**: Map 'processing' to 'running' during migration.

A: I agree.

### Q5: ComfyUI routes and old code cleanup
Moved to: notes/comfyui-questions-5.md

## Unanswered
### Q6: ComfyUI webhook support
#### Question
**Context**: Phase 8.5 asks to create a webhook endpoint `/webhooks/comfyui` for ComfyUI to call on job completion.

**Questions**:
1. Does ComfyUI support webhooks natively? I haven't found webhook functionality in ComfyUI documentation.
2. If not, should we:
   - **Option A**: Use polling in the Celery task (current implementation via `wait_for_outputs()`)
   - **Option B**: Set up a custom ComfyUI extension/plugin to call our webhook
   - **Option C**: Use ComfyUI's SSE (Server-Sent Events) if available
   - **Option D**: Monitor ComfyUI's output directory for file changes

**Current implementation**: We use polling via `comfy_client.wait_for_outputs()` which checks job status periodically. 
This works but is less efficient than webhooks.

**My recommendation**: Unless ComfyUI has built-in webhook support (which I haven't found), stick with the current 
polling approach. It's simple, reliable, and works. If you need webhooks, we'd need to modify ComfyUI itself or create 
a custom node.

#### Answer
You're right. sStick with the polling approach. ComfyUI only has webhooks with extensions, and for various reasons we 
are not going to use those.

### Q7: Frontend generation page - image display strategy
#### Question
**Context**: Phase 8.5 asks for the generation page to "display the completed image somewhere on the page" after generation succeeds.

**Current frontend state** (I need to verify this):
- Is there already a generation/create page in the React frontend?
- What's the current flow after a user submits a generation request?

**Options for displaying images**:
1. **WebSocket real-time** (ideal UX)
   - Frontend connects to WebSocket on job submission
   - Listens for "completed" status
   - Immediately displays image when received
   - **Requires**: Frontend WebSocket client code (not yet implemented)

2. **Polling** (simpler, works now)
   - Frontend submits job, gets job_id
   - Poll `/api/v1/generation-jobs/{job_id}` every 2-5 seconds
   - When status is "completed", fetch and display image
   - **Requires**: Minimal frontend changes

3. **Page refresh** (simplest, poor UX)
   - Submit job, redirect to "My Generations" page
   - User manually refreshes to see when complete

**Questions**:
1. What does the current frontend generation page look like? Does it exist?
2. What UX do you prefer - real-time WebSocket updates or polling?
3. Where should images be displayed - inline on the generation form, or redirect to a results page?

**My recommendation**: Start with Option 2 (polling) as a v1 implementation since it requires minimal frontend changes and works immediately. Then upgrade to Option 1 (WebSocket) for better UX once we've tested the WebSocket infrastructure.

**Current frontend implementation discovered**:
- `/frontend/src/pages/generation/GenerationPage.tsx` exists with Create and History tabs
- `/frontend/src/components/generation/GenerationProgress.tsx` component already polls for status
- Uses `useGenerationPolling` hook which polls `/api/v1/comfyui/...` endpoints (OLD API)
- Shows success message when completed: "Generation completed successfully! X image(s) generated."
- But does NOT actually display the generated images - just shows the count
- Frontend is currently using the OLD `/api/v1/comfyui/` endpoints, not the NEW `/api/v1/generation-jobs/` endpoints

**What needs to happen**:
1. Migrate frontend from old ComfyUI service to new GenerationJob service
2. Update GenerationProgress component to display actual images (not just count)
3. Either:
   - Keep using polling with new endpoints (simpler)
   - OR switch to WebSocket for real-time updates (better UX but more work)

#### Answer
In regards to these questions:
> **Current frontend state** (I need to verify this):
> i. Is there already a generation/create page in the React frontend?
> ii. What's the current flow after a user submits a generation request?

i. Yes! The title of the page is called: "Image Generation"
ii. You'll have to figure that out for yourself, sorry. Look at the page with that title "Image Generation", and look 
at what happens when the "Generate Images" button is clicked. It calls ComfyUI and generates an image--successfully. 
However, the output directory doesn't lie within our repo. It exists at: /Users/joeflack4/Documents/ComfyUI/output. If 
you have difficulty working with that directory due to permissions, let me know. We can try to set up a different dir, 
or I can set up a symlink (unless you can create one yoruself!). But other than the job being submitted, there is 
basically no follow-up. That is what you are here to do. Change it so that it submits through celery, and then we check 
up on ComfyUI to get the status, and otherwise check the outdir for the image if it doesn't tell us the outpath on 
success. If you need to see documentation about ComfyUI and its endpoints / request / response / params, etc, let me 
know.

RE: **Options for displaying images**:
We want to go the web socket route, if possible. Try to implement that.

**Questions**:
1. What does the current frontend generation page look like? Does it exist?
A: Answered above.

2. What UX do you prefer - real-time WebSocket updates or polling?
A: Answered above.

3. Where should images be displayed - inline on the generation form, or redirect to a results page?
A: Have it display on the same "Image Generation" page. I think there is sufficient space on the right, below 
 "Generation Status".

### Q8: Frontend service migration strategy
#### Question
**Context**: The frontend currently uses `/api/v1/comfyui/` endpoints (old table) via `comfyui-service.ts`. Should I:

**Option A**: Migrate frontend to use new `/api/v1/generation-jobs/` endpoints
- Create new `generation-job-service.ts` mirroring the old service but using new endpoints
- Update all frontend components to use new service
- Delete `comfyui-service.ts` and related types
- More work but cleaner architecture

**Option B**: Keep frontend as-is temporarily
- Old API endpoints still work (if we don't delete them)
- Gives time to test backend fully before frontend migration
- But maintains tech debt

**My recommendation**: Option A - migrate frontend to new API. The old ComfyUI endpoints should be deprecated.

#### Answer
Yes, Option A.

### Q9: Image display in GenerationProgress component
#### Question
**Context**: When a generation completes, where/how should images be displayed?

**Options**:
1. **Inline in GenerationProgress** - Show thumbnail grid right in the progress card
2. **Modal popup** - Click "View Images" button to open modal with image gallery
3. **Redirect to Gallery** - Redirect user to main gallery page showing their new images
4. **New "Results" panel** - Add a third column/section showing results

**Current state**: Component shows "X image(s) generated" text but no actual images.

**My recommendation**: Option 1 (inline) + Option 2 (modal for fullsize). Show thumbnail in the progress card, click to 
open modal with full image viewer.

#### Answer
Yes, option (1). More detail was answered in Q7, part 3:
> 3. Where should images be displayed - inline on the generation form, or redirect to a results page?
> A: Have it display on the same "Image Generation" page. I think there is sufficient space on the right, below 
 > "Generation Status".

However, I wouldn't open a modal, actually. For the full image viewer, let's instead use the very same page that we use 
when a user opens up an image by selecting it from a list or grid in either the "Dashboard" or "Gallery" pages. If you 
click one of those pages, it will direct you to a /N route, where N is an integer, I think representing the content item
(image) ID. It shows the prompt, tags, other metadata, and the image. So use that same page when a user opens up the 
full image from the generation page.
