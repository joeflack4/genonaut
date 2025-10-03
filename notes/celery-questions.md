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

## Unanswered
