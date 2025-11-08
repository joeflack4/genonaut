## Original dump
### Background
Was considering doing this as an alterantive to another solution at the time. I didn't think it would be the biggest change, but it looks like I was wrong.

### Claude Code wrote:
Why Option D (UUID) Takes 2-4 Weeks

1. Database Schema Changes (1-2 days)

- Add UUID column to content_items and content_items_auto
- Add UUID column to ALL 8 referencing tables
- Populate UUIDs for 1.17 million existing content items
- Populate UUIDs for 1.2 million generation_jobs
- Create indexes on new UUID columns
- Test foreign key constraints

2. Data Migration Script (2-3 days)

-- Example of what needs to happen:
ALTER TABLE content_items ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();
ALTER TABLE content_items_auto ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();

-- For EACH of the 8 referencing tables:
ALTER TABLE generation_jobs ADD COLUMN content_uuid UUID;
UPDATE generation_jobs SET content_uuid = (
    SELECT uuid_id FROM content_items WHERE id = generation_jobs.content_id
);
-- This UPDATE alone touches 1.2 million rows!

-- Then drop old integer FKs, rename UUID columns, add new FK constraints

3. Code Changes Across Entire Codebase (3-5 days)

Every place that uses content_id needs updating:

Backend (Python):
- SQLAlchemy models: Change Integer → UUID for PKs and FKs
- All queries that filter by ID
- All API request/response models (Pydantic)
- All service layer methods
- All repository methods
- URL route parameters (FastAPI)
- Celery task parameters

Frontend (TypeScript):
- Type definitions: number → string for all content IDs
- All API calls
- All hooks (useQuery, useMutation)
- URL generation
- Local state management
- Component props

4. API Breaking Changes (2-3 days)

// BEFORE
GET /api/v1/images/65252
{ "content_id": 65252 }

// AFTER
GET /api/v1/images/a3bb189e-8bf9-3888-9fa5-a3bb189e8bf9
{ "content_id": "a3bb189e-8bf9-3888-9fa5-a3bb189e8bf9" }

Every API endpoint that accepts/returns content IDs changes:
- Version API or deprecation period needed
- API client updates
- Mobile app updates (if any)
- Third-party integrations

5. Testing (3-4 days)

- Unit tests: Update all fixtures with UUIDs
- Integration tests: Update all test data
- E2E tests: Update all assertions
- Migration testing: Ensure data integrity
- Performance testing: UUID indexes vs integer
- Regression testing: Ensure nothing breaks

6. Performance Considerations

- UUIDs are 128 bits vs 32 bits for integers
- Indexes are 4x larger
- B-tree performance degradation (UUIDs are random, not sequential)
- Join performance impact
- Possible need for UUID v7 (time-ordered) instead of v4

Why I Said 2-4 Weeks Minimum

- Schema changes: 1-2 days
- Migration script: 2-3 days
- Backend code: 2-3 days
- Frontend code: 2-3 days
- Testing: 3-4 days
- Buffer for issues: 2-3 days

Total: 12-18 business days = 2.5-3.5 weeks

And that's assuming:
- No major blockers
- Single developer working full-time
- No production deployment issues
- No rollback needed

---
Why Shared Sequence (Option A) is Better

By comparison, Option A:

-- Create shared sequence
CREATE SEQUENCE content_items_id_seq START WITH 1200000;  -- Start above max

-- Update content_items to use it
ALTER TABLE content_items
    ALTER COLUMN id SET DEFAULT nextval('content_items_id_seq');

-- Update content_items_auto to use it
ALTER TABLE content_items_auto
    ALTER COLUMN id SET DEFAULT nextval('content_items_id_seq');

- No FK changes needed
- No code changes needed
- IDs stay as integers
- API unchanged
- 2-4 hours of work, not weeks

The only downside is you lose independent sequences per partition, but you gain data
integrity without the massive refactor.

My verdict: Unless you're planning to go UUID for other architectural reasons
(distributed systems, multi-region, etc.), Option A is vastly superior for solving this
 specific problem.

Does that help clarify why UUID is such a big lift?