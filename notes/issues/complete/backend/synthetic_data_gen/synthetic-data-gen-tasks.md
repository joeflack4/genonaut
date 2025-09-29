# Synthetic Data Generator - Implementation Plan

## Library Landscape and Recommendations

### FK-aware / ORM Factories
**Recommendation: Direct SQLAlchemy model reflection**
- **Factory Boy**: Good for simple cases but can be complex for FK management across tables
- **Polyfactory**: Modern but adds dependency complexity
- **Direct SQLAlchemy reflection**: Lightweight, full control, leverage existing models
- **Trade-offs**: Direct approach requires more manual FK ordering but gives precise control over generation and batching

### Field Generators
**Recommendation: Faker + custom generators**
- **Faker**: Industry standard, extensive providers, good performance
- **mimesis**: Faster but smaller ecosystem
- **Trade-offs**: Faker has broader coverage for our diverse field requirements (usernames, emails, datetimes)

### Prompt Generation
**Recommendation: Jinja2 templates**
- **Jinja2**: Already likely in dependencies, flexible, readable templates
- **tracery**: Interesting for grammar-based generation but adds complexity
- **Trade-offs**: Jinja2 balances flexibility with simplicity for combinatorial prompt creation

### Bulk Loading
**Recommendation: SQLAlchemy bulk_insert_mappings with psycopg COPY fallback**
- **SQLAlchemy bulk_insert_mappings**: Good balance of ORM integration and performance
- **psycopg COPY**: Fastest for very large datasets but bypasses ORM validation
- **asyncpg**: Highest performance but requires async refactoring
- **Trade-offs**: Start with SQLAlchemy bulk, add COPY optimization if needed

### Concurrency
**Recommendation: concurrent.futures.ProcessPoolExecutor for prompt generation**
- **multiprocessing**: Good for CPU-bound prompt generation
- **ProcessPoolExecutor**: Cleaner interface than raw multiprocessing
- **Trade-offs**: Keep DB operations single-threaded to avoid deadlocks, parallelize data preparation

### Config & CLI
**Recommendation: argparse + Pydantic**
- **argparse**: Standard library, good for CLI parsing
- **typer**: Nicer but adds dependency
- **Pydantic**: Excellent for config validation and type safety
- **Trade-offs**: argparse + Pydantic gives validation without extra CLI dependencies

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Parser    │───▶│  Config Manager  │───▶│ Data Generator  │
│  (argparse)     │    │   (Pydantic)     │    │   (main logic)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                              ┌─────────────────────────┼─────────────────────────┐
                              │                         │                         │
                              ▼                         ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                    │  User Generator │    │Content Generator│    │  Job Generator  │
                    │   (FK: none)    │    │ (FK: users)     │    │(FK: content)    │
                    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │                         │
                              │         ┌─────────────────┐                      │
                              │         │ Prompt Engine   │                      │
                              │         │   (Jinja2 +     │                      │
                              │         │ ProcessPool)    │                      │
                              │         └─────────────────┘                      │
                              │                         │                         │
                              ▼                         ▼                         ▼
                    ┌─────────────────────────────────────────────────────────────────┐
                    │                  Bulk Inserter                                  │
                    │            (SQLAlchemy bulk_insert_mappings)                    │
                    │                 + Conflict Resolution                          │
                    └─────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │   PostgreSQL    │
                                        │    Database     │
                                        └─────────────────┘
```

### Data Flow
1. CLI parses arguments and loads config
2. Config manager validates and merges CLI overrides
3. Data generator determines FK dependency order: users → content_items/content_items_auto → generation_jobs
4. Each generator creates batches of data with parallel prompt generation
5. Bulk inserter handles conflicts and retries
6. Progress reporter tracks and logs completion

### Concurrency Model
- **Prompt Generation**: ProcessPoolExecutor for CPU-bound template rendering
- **Batch Preparation**: Parallel data structure creation
- **Database Operations**: Single-threaded to avoid FK constraint deadlocks
- **Progress Reporting**: Thread-safe logging throughout

## Implementation Plan

### Phase 1: Foundation (Tasks 1-3)
**Task 1: Project Structure Setup**
- [x] Create directory structure under `genonaut/db/demo/seed_data_gen/`
- [x] Set up `__main__.py` CLI entry point
- [x] Create core module files: `generator.py`, `config.py`, `prompt_engine.py`, `bulk_inserter.py`

**Acceptance Criteria:**
- [x] Directory structure matches specification
- [x] CLI responds to `python -m genonaut.db.demo.seed_data_gen --help`
- [x] Basic config loading works

**Task 2: Model Analysis & FK Mapping**
- [x] Inspect existing SQLAlchemy models
- [x] Create FK dependency graph
- [x] Validate generation order: users → content → jobs

**Acceptance Criteria:**
- [x] FK relationships documented
- [x] Generation order determined
- [x] Model field mappings identified

**Task 3: Config Management**
- [x] Implement Pydantic config schema
- [x] Add CLI argument parsing with config overrides
- [x] Validate admin UUID handling

**Acceptance Criteria:**
- [x] Config validates against schema
- [x] CLI overrides work for all specified options
- [x] Admin UUID error handling works as specified

### Phase 2: Core Generation (Tasks 4-6)
**Task 4: User Data Generation**
- [x] Implement user generator with Faker
- [x] Handle username uniqueness conflicts
- [x] Implement admin user insertion
- [x] Add datetime generation with ET/UTC conversion

**Acceptance Criteria:**
- [x] Users generated with all required fields
- [x] Username conflicts handled with warnings
- [x] Admin user properly identified
- [x] Date ranges respected (2025-05-01 to 2025-09-21)

**Task 5: Content Data Generation**
- [x] Implement content_items and content_items_auto generators
- [x] Add FK relationship to users
- [x] Implement tag selection from global pool
- [x] Handle admin user content requirements (exactly 50 each)

**Acceptance Criteria:**
- [x] Content items reference valid user IDs
- [x] Tag selection works (0-200 tags per item)
- [x] Admin gets exactly 50 items in each table
- [x] Image paths generated correctly

**Task 6: Prompt Generation Engine**
- [x] Implement Jinja2 template system
- [x] Add domain-specific prompt pools
- [x] Implement concurrent prompt generation
- [x] Add general phrase integration

**Acceptance Criteria:**
- [x] Prompts generated with 0-10 general + 4-30 domain phrases
- [x] Templates produce diverse output
- [x] Concurrent generation works efficiently
- [x] All 30 domains supported

### Phase 3: Advanced Features (Tasks 7-8)
**Task 7: Generation Jobs**
- [x] Implement job generator with FK to content
- [x] Handle status distribution requirements
- [x] Link every content item to completed job
- [x] Add additional jobs with varied statuses

**Acceptance Criteria:**
- [x] Every content item has corresponding completed job
- [x] Status distribution matches spec (98% completed, etc.)
- [x] Prompt titles match content item prompts

**Task 8: Bulk Insertion System**
- [x] Implement fast bulk insertion
- [x] Add conflict resolution for username uniqueness
- [x] Implement progress reporting
- [x] Add transaction management

**Acceptance Criteria:**
- [x] Bulk insertion significantly faster than individual inserts
- [x] Username conflicts resolved with logging
- [x] Progress shows per-batch completion percentages
- [x] Transactions handle partial failures

### Phase 4: Integration & Testing (Task 9)
**Task 9: System Integration & Validation**
- [x] Complete CLI implementation
- [x] Add comprehensive error handling
- [x] Implement timing and statistics reporting
- [x] Add required --database-url parameter
- [x] Add database name validation (_demo/_test only)
- [x] Create Makefile targets (seed-from-gen-demo, seed-from-gen-test)
- [x] Test full end-to-end workflow on demo database

**Acceptance Criteria:**
- [x] Complete CLI works with all options
- [x] Error scenarios handled gracefully
- [x] Performance timing reported
- [x] Database URL validation enforces safety (_demo/_test only)
- [x] Makefile targets implemented and functional
- [x] Data integrity validated on demo database
- [x] Admin user requirements verified (~50 items each table - working correctly)

## Test Strategy

### Unit Tests
- Config validation and CLI parsing
- Individual data generators
- Prompt template generation
- FK relationship validation

### Integration Tests
- Full pipeline with small datasets
- Username conflict resolution
- Admin user content distribution
- Status distribution validation

### Performance Tests
- Bulk insertion timing
- Concurrent prompt generation
- Memory usage with large batches
- Database connection handling

### Data Quality Tests
- FK constraint compliance
- Field value distributions
- Date range validation
- Tag selection accuracy

## Success Metrics

1. **Performance**: Generate 10,000 records per table in under 2 minutes
2. **Accuracy**: 100% FK compliance, exact admin user distribution
3. **Robustness**: Handle username conflicts gracefully
4. **Usability**: All config options overrideable via CLI
5. **Monitoring**: Clear progress reporting and final statistics