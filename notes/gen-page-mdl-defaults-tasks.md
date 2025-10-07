# Generation Page - Model Defaults - Tasks

## Overview
Implementing checkpoint and LoRA model defaults for the generation page by creating database tables, seed data, API routes, and frontend integration.

## Tags
- infrastructure: Database/infrastructure setup tasks that may require manual intervention
- blocked: Waiting for user input or clarification
- seed-data: Related to creating or loading seed data
- later: Non-critical tasks deferred to after main functionality is complete (e.g., unit tests for static data loader)

## Phase 1: Database Schema & Models

### 1.1 Create seed data CSV files
- [x] Create directory: `genonaut/db/demo/seed_data_static/`
- [x] Create `models_checkpoints.csv` with sample data
- [x] Create `models_loras.csv` with sample data

### 1.2 Create SQLAlchemy models
- [x] Add `CheckpointModel` class to `genonaut/db/schema.py`
  - UUID id field
  - String path field (unique, not nullable)
  - String filename field (unique, nullable, auto-populated from path)
  - String name field (unique, nullable, auto-populated from filename)
  - String version field
  - String architecture field
  - String family field
  - String description field
  - Float rating field (0-1)
  - Array tags field
  - Array compatible_architectures field
  - JSONB metadata field
  - DateTime created_at field
  - DateTime updated_at field
  - Add standard indexes for: name, path, rating, architecture, family
  - Add GIN indexes for: tags, compatible_architectures, metadata
  - Add GiST index for: description
- [x] Add `LoraModel` class to `genonaut/db/schema.py`
  - UUID id field
  - String path field (unique, not nullable)
  - String filename field (unique, nullable, auto-populated from path)
  - String name field (unique, nullable, auto-populated from filename)
  - String version field
  - String architecture field
  - String family field
  - String description field
  - Float rating field (0-1)
  - Array tags field
  - Array trigger_words field
  - Array optimal_checkpoints field
  - JSONB metadata field
  - DateTime created_at field
  - DateTime updated_at field
  - Add standard indexes for: name, path, rating, architecture, family
  - Add GIN indexes for: tags, trigger_words, optimal_checkpoints, metadata
  - Add GiST index for: description
- [x] Add Python-level logic to auto-populate filename from path if missing
- [x] Add Python-level logic to auto-populate name from filename if missing

### 1.3 Database migration
- [x] Run `make migrate-prep` to generate migration
- [x] Run `make migrate-demo` to apply migration to demo database
- [x] Verify tables created successfully

## Phase 2: Database Seeding

### 2.1 Create static seed data loader
- [x] Create function `seed_static_data()` in demo seeding script
- [x] Implement CSV/TSV file discovery in `seed_data_static/`
- [x] Implement table name matching logic
- [x] Implement row insertion logic with proper field population
- [ ] Add unit tests for seed data loader @skipped-until-later

### 2.2 Integrate with main seeding script
- [x] Add `seed_static_data()` call near beginning of main seed script
- [x] Ensure it runs before synthetic data generation

### 2.3 CLI command for static data only
- [x] Add CLI argument for `seed-static` subcommand
- [x] Add Makefile commands `seed-static-demo` and `seed-static-test`
- [x] Test the command and verify data in database

## Phase 3: API Layer

### 3.1 Create API models (Pydantic)
- [x] Add `CheckpointModelResponse` to `genonaut/api/models/responses.py`
- [x] Add `LoraModelResponse` to `genonaut/api/models/responses.py`
- [x] Add `CheckpointModelListResponse` to `genonaut/api/models/responses.py`
- [x] Add `LoraModelListResponse` to `genonaut/api/models/responses.py`

### 3.2 Create repositories
- [x] Create `genonaut/api/repositories/checkpoint_model_repository.py`
  - `get_all()` method
  - `get_by_id()` method
  - Proper sorting by rating descending
- [x] Create `genonaut/api/repositories/lora_model_repository.py`
  - `get_all()` method
  - `get_by_id()` method
  - Proper sorting by rating descending
- [ ] Add unit tests for repositories @skipped-until-later

### 3.3 Create services
- [x] Create `genonaut/api/services/checkpoint_model_service.py`
  - `get_all()` method
  - `get_by_id()` method
- [x] Create `genonaut/api/services/lora_model_service.py`
  - `get_all()` method
  - `get_by_id()` method
- [ ] Add unit tests for services @skipped-until-later

### 3.4 Create API routes
- [x] Create `genonaut/api/routes/checkpoint_models.py`
  - GET `/api/v1/checkpoint-models/` endpoint
  - GET `/api/v1/checkpoint-models/{id}` endpoint
- [x] Create `genonaut/api/routes/lora_models.py`
  - GET `/api/v1/lora-models/` endpoint
  - GET `/api/v1/lora-models/{id}` endpoint
- [x] Register routes in main API app
- [ ] Add API integration tests @skipped-until-later

## Phase 4: Frontend Integration

### 4.1 Create API hooks
- [x] Create `frontend/src/hooks/useCheckpointModels.ts`
- [x] Create `frontend/src/hooks/useLoraModels.ts`
- [ ] Add unit tests for hooks @skipped-until-later

### 4.2 Create TypeScript types
- [x] Add `CheckpointModel` type to `frontend/src/types/domain.ts`
- [x] Add `LoraModel` type to `frontend/src/types/domain.ts`
- [x] Add API types to `frontend/src/types/api.ts`

### 4.3 Update Generation page
- [x] Create checkpoint and LoRA model services
- [x] Update `frontend/src/components/generation/ModelSelector.tsx`
  - Query for checkpoint models using useCheckpointModels hook
  - Query for LoRA models using useLoraModels hook
  - Display checkpoint models in dropdown (sorted by rating desc by API)
  - Display LoRA models in dropdown (sorted by rating desc by API)
  - Handle selection and state management
- [x] Verified API endpoints working via browser network logs
- [ ] Add unit tests for GenerationForm changes

### 4.4 E2E tests
- [ ] Create Playwright test to verify at least 1 checkpoint displayed
- [ ] Create Playwright test to verify at least 1 LoRA displayed
- [ ] Verify models are sorted by rating descending

## Phase 5: Documentation & Cleanup

### 5.1 Update README
See 

- [ ] Document new database tables: docs/db.md
- [ ] Document new API endpoints: docs/api.md
- [ ] Update docs for seed data process (the new 'static' seed data; particularly, want the user to know that they can 
  edit the CSV or TSV files in that folder): within docs/db.md

### 5.2 Verify all tests passing
- [ ] Run unit tests: `make test-unit`
- [ ] Run database tests: `make test-db`
- [ ] Run API tests: `make test-api`
- [ ] Run frontend tests: `npm run test-unit`
- [ ] Run E2E tests: `npm run test:e2e`

## Progress Tracking
Current phase: Not started
Next action: Begin Phase 1.1
