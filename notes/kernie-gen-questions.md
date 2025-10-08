# KernieGen Integration - Questions

## Configuration Questions
1. **Output directory**: The mock server outputs to `test/_infra/mock_services/comfyui/output/` by default. Do you want to:
   - Keep this as-is (separate from real ComfyUI output)?
   - Point `comfyui-output-dir` in `local-demo.json` to this directory?
   - Use a different directory?

Answer:

2. **Input images**: The mock server uses test images from `test/_infra/mock_services/comfyui/input/kernie_512x768.jpg`. 
Is this the image you want generated outputs to be based on, or do you want to add other test images?

Answer:


## Workflow Questions
1. **Development workflow**: Going forward, when switching between real ComfyUI and the mock server, what's your preferred workflow?
   - Option A: Maintain separate config files (e.g., `local-demo-real.json` and `local-demo-mock.json`)
   - Option B: Toggle a single config value and restart services
   - Option C: Add an environment variable or CLI flag to choose at runtime

Answer:

2. **Service management**: Would you like a single command to restart all affected services when config changes? For example:
   - `make restart-demo` - restarts API server, Celery worker, and any other services
   - Individual commands as they are now

Answer:

## Testing Questions
1. **Mock server features**: The current mock server (test/_infra/mock_services/comfyui/server.py) supports:
   - Workflow submission
   - Status tracking
   - Mock file generation (copies a static image)
   - Model/LoRA enumeration

   Are there additional ComfyUI features you need the mock to support?

Answer:

2. **E2E testing**: Do you plan to use the mock server for automated E2E tests, or primarily for manual testing/development?

Answer:

## Process Questions
1. **Celery worker status**: Before I found this issue, was the Celery worker running? You can check with:
   ```bash
   ps aux | grep celery
   ```

Answer:

2. **Error visibility**: Did you see any errors in the API logs or UI when clicking "generate"? Understanding where
errors surfaced (or didn't) can help improve error messaging.

Answer:
