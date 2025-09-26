# ComfyUI Integration Specification

## Overview
This specification outlines the integration of ComfyUI for AI image generation within the Genonaut application. Users will be able to generate custom images using ComfyUI's workflow system with configurable parameters including prompts, models, and generation settings.

## Core Workflow Pattern
Based on the reference workflow in `test/integrations/comfy_ui/input/1.json`, our integration follows this node chain:
1. **CheckpointLoaderSimple** - Load base model
2. **LoraLoader** (0-n instances) - Apply LoRA models for style/character modifications
3. **CLIPTextEncode** (2 instances) - Encode positive and negative prompts
4. **EmptyLatentImage** - Define image dimensions and batch size
5. **KSampler** - Perform generation with sampling parameters
6. **VAEDecode** - Decode latent to image
7. **SaveImage** - Save generated image

## Backend Requirements

### Database Schema Updates
- **GenerationRequest** table
  - id (Primary Key)
  - user_id (Foreign Key)
  - prompt (Text)
  - negative_prompt (Text, nullable)
  - checkpoint_model (String)
  - lora_models (JSON array of {name, strength_model, strength_clip})
  - width, height, batch_size (Integers)
  - sampler_params (JSON: seed, steps, cfg, sampler_name, scheduler, denoise)
  - status (Enum: pending, processing, completed, failed)
  - comfyui_prompt_id (String, nullable)
  - output_paths (JSON array of file paths)
  - thumbnail_paths (JSON array of file paths)
  - created_at, updated_at (Timestamps)

- **AvailableModel** table
  - id (Primary Key)
  - name (String)
  - type (Enum: checkpoint, lora)
  - file_path (String)
  - description (Text, nullable)
  - is_active (Boolean)

### API Endpoints
- `POST /api/generation/request` - Submit generation request
- `GET /api/generation/{id}` - Get generation status and results
- `GET /api/generation/list` - List user's generation requests
- `DELETE /api/generation/{id}` - Cancel/delete generation request
- `GET /api/generation/models` - Get available checkpoint and LoRA models

### ComfyUI Integration Module
- **ComfyUIClient** class
  - Connection management to ComfyUI API
  - Workflow submission and monitoring
  - Result retrieval and status polling
- **WorkflowBuilder** class
  - Dynamic workflow JSON generation from user parameters
  - Model validation and path resolution
- **GenerationService** class
  - Orchestrates generation requests
  - Handles async processing and status updates

### Storage
- Generated images stored in configurable directory (@dev: determine ComfyUI output directory)
- Thumbnail generation either via ComfyUI workflow extension or post-processing
- Future: AWS S3 integration for cloud storage

### Worker Queue Integration
Integration with worker system (Ray/Celery/Kafka) for:
- Async generation request processing
- Status polling and result retrieval
- Error handling and retry logic

## Frontend Requirements

### Generation Page (`/generate`)
- **Model Selection**
  - Dropdown for checkpoint model selection
  - Multi-select for LoRA models with strength sliders
- **Prompt Interface**
  - Text area for positive prompt
  - Text area for negative prompt (optional)
- **Image Parameters**
  - Width/height inputs or preset selection
  - Batch size selector
- **Advanced Settings** (collapsible)
  - KSampler parameters (seed, steps, cfg, sampler_name, scheduler, denoise)
- **Generation Controls**
  - Submit button
  - Progress indicator
  - Cancel button

### Generation History/Gallery
- Grid view of generated images with thumbnails
- Click to view full size
- Generation parameters display
- Re-generate with same parameters option
- Delete generated images

### Components
- `GenerationForm` - Main generation interface
- `ModelSelector` - Checkpoint and LoRA selection
- `ParameterControls` - Image and sampling parameter inputs
- `GenerationProgress` - Real-time status and progress
- `GenerationHistory` - List/grid of past generations
- `ImageViewer` - Full-size image display with metadata

## Technical Decisions Needed (@dev)

1. **ComfyUI Output Directory**: Where does ComfyUI save generated images? Need to configure proper paths.

2. **Model Management**:
   - How to discover available models dynamically?
   - Manual model registration vs auto-discovery?
   - Model validation and error handling?

3. **Thumbnail Generation**:
   - Use ComfyUI workflow nodes for thumbnails?
   - Post-process with PIL/Pillow?
   - What sizes/formats?

4. **Worker Queue Choice**: Ray, Celery, or Kafka for async processing?

5. **ComfyUI Instance Management**:
   - Single shared instance or per-user instances?
   - Load balancing multiple ComfyUI instances?
   - Docker containerization strategy?

6. **Rate Limiting**:
   - Per-user generation limits?
   - Queue management and priority?

7. **Storage Strategy**:
   - Local disk structure and cleanup policies?
   - When to migrate to cloud storage?
   - Image compression and format standards?

8. **Error Handling**:
   - ComfyUI connection failures?
   - Invalid model references?
   - Generation timeouts and retries?

## Security Considerations
- Input validation for all parameters
- File path sanitization
- User isolation for generated content
- Model file access restrictions
- Rate limiting to prevent abuse

## Performance Considerations
- Async processing for all generation requests
- Efficient thumbnail generation
- Database indexing for user queries
- Caching of model metadata
- Cleanup of old generated images

## Testing Strategy
- Unit tests for workflow generation logic
- Integration tests with mock ComfyUI API
- End-to-end tests for generation flow
- Load testing for concurrent generations
- Model validation testing

## Misc
ComfyUI is running on localhost:8000 right now. If it is ever not running, please prompt the user / dev to start it for 
you. Feel free to make whatever queries you want on it, including POST queries that create images.
