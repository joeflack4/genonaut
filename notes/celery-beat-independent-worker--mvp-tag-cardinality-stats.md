# Tag Cardinality Statistics

## Overview

The `tag_cardinality_stats` table tracks the number of distinct content items per (tag_id, content_source) combination. This data is used by the adaptive tag query planner to select optimal query strategies for multi-tag filtering.

## Database Schema

```sql
CREATE TABLE tag_cardinality_stats (
    tag_id UUID PRIMARY KEY REFERENCES tags(id) ON DELETE CASCADE,
    content_source VARCHAR(10) PRIMARY KEY,
    cardinality INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tag_cardinality_stats_tag_src ON tag_cardinality_stats(tag_id, content_source);
```

## Manual Refresh

You can manually refresh the statistics using the Makefile command:

```bash
# Refresh for demo database (default)
make refresh-tag-stats

# Refresh for specific environment
make refresh-tag-stats-dev
make refresh-tag-stats-demo
make refresh-tag-stats-test
```

The script is located at `genonaut/db/refresh_tag_stats.py`.

## Automated Refresh with Celery Beat

### Setup Tasks

- [ ] 1. Create Celery task in `genonaut/tasks/scheduled_tasks.py`
- [ ] 2. Configure Celery Beat schedule in `genonaut/celery_config.py`
- [ ] 3. Add schedule configuration to `config/base.json`
- [ ] 4. Add Makefile commands to start Celery Beat
- [ ] 5. Update documentation in `docs/queuing.md`
- [ ] 6. Test Celery Beat scheduler locally

### Configuration

The scheduled refresh runs daily at midnight (12:00 AM). This can be configured in `config/base.json`:

```json
{
  "celery": {
    "beat-schedule": {
      "refresh-tag-stats": {
        "enabled": true,
        "schedule": {
          "hour": 0,
          "minute": 0
        }
      }
    }
  }
}
```

### Starting Celery Beat

```bash
# Start Celery Beat scheduler (demo environment)
make celery-beat-demo

# Start Celery Beat for other environments
make celery-beat-dev
make celery-beat-test
```

**Note:** Celery Beat should run as a separate process alongside your Celery worker.

### Monitoring

- Check Flower dashboard at http://localhost:5555 to see scheduled tasks
- View task history and execution times
- Monitor for failures and retry attempts

## Query Planner Usage

The tag query planner (`TagQueryPlanner`) uses these statistics to choose between:

1. **Self-join** (K <= 3 tags)
2. **Group/HAVING** (rarest tag <= 50K items)
3. **Two-phase single-seed** (rarest tag > 50K)
4. **Two-phase dual-seed** (rarest tag > 150K, K >= 7)

### Fallback Behavior

If statistics are missing for a tag, the planner uses a configurable default (1,000,000 items). This ensures queries still work but may not use the optimal strategy.

Configure the fallback in `config/base.json`:

```json
{
  "performance": {
    "query-planner-tag-prejoin": {
      "stats": {
        "fallback-default-count": 1000000
      }
    }
  }
}
```

## Implementation example
```py
from celery import shared_task
from genonaut.api.repositories.tag_repository import TagRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

@shared_task
def refresh_tag_cardinality_stats():
    """Refresh tag cardinality statistics for query planning."""
    db_url = f'postgresql://{os.getenv("DB_USER_ADMIN")}:{os.getenv("DB_PASSWORD_ADMIN"
)}@localhost/genonaut_demo'
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        repo = TagRepository(db)
        count = repo.refresh_tag_cardinality_stats()
        return f"Refreshed {count} stats"
    finally:
        db.close()
```

## Performance

- **Refresh time**: ~11 seconds for 207 tag-source combinations (demo database)
- **Table size**: Minimal (one row per tag-source pair)
- **Query impact**: Negligible (simple lookup by tag_id + content_source)

## Maintenance

### When to Refresh

- **After bulk content imports**: New content may significantly change tag distributions
- **After tag cleanup**: Removing unused tags or merging tags
- **Weekly**: For active development environments
- **Daily**: For production (automated via Celery Beat)

### Troubleshooting

**Issue:** Stats seem outdated
- Solution: Run `make refresh-tag-stats` manually
- Check: Celery Beat is running (`make celery-beat-demo`)
- Check: Celery worker is running (`make celery-demo`)

**Issue:** Refresh takes too long
- Cause: Large content_tags table (millions of rows)
- Solution: Consider running during off-peak hours
- Future: Implement incremental updates (track changed tags only)

**Issue:** Query planner not using stats
- Check: Stats table has data (`SELECT COUNT(*) FROM tag_cardinality_stats;`)
- Check: Configuration loaded properly (`performance.query-planner-tag-prejoin.stats.source = "table"`)
- Check: Telemetry logs show strategy selection with real cardinality values

## Related Files

- **Database schema**: `genonaut/db/schema.py` - TagCardinalityStats model
- **Refresh script**: `genonaut/db/refresh_tag_stats.py`
- **Repository**: `genonaut/api/repositories/tag_repository.py` - refresh_tag_cardinality_stats()
- **Query planner**: `genonaut/api/services/tag_query_planner.py`
- **Scheduled task**: `genonaut/tasks/scheduled_tasks.py` (TODO)
- **Configuration**: `config/base.json`
- **Makefile**: Targets for manual refresh and Celery Beat

## Future Enhancements

- Incremental updates (only refresh changed tags)
- Redis caching for frequently accessed stats
- Stats history tracking for trend analysis
- Automatic alerting for significant distribution changes
- Per-environment refresh schedules


## why we didn't end up doing this
went with a simpler approach. see copy/paste of claude code chat:



> we finished this phase now, i had to go back in your memory due to context. i want you
to tell me which you'd pick for scheduling and why: (a) simple, (b) complex. for complex,
 see: notes/tag-cardinality-stats.md

for simple, see:

  2. Add schedule to your Celery config (wherever you configure Celery):
  from celery.schedules import crontab

  app.conf.beat_schedule = {
      'refresh-tag-stats-nightly': {
          'task': 'genonaut.tasks.scheduled_tasks.refresh_tag_cardinality_stats',
          'schedule': crontab(hour=3, minute=0),  # 3 AM daily
      },
  }

⏺ I'd pick (a) simple - the Celery Beat configuration approach.

  Why:

  1. Direct integration: Celery Beat is already part of your infrastructure (you have
  make celery-dev, make flower-dev). This just adds a scheduled task to what you already
  have.
  2. Operational simplicity: One fewer moving part. No need to manage cron separately or
  deal with environment setup in cron jobs.
  3. Consistency: All async tasks in one place (Celery). Easier to monitor via Flower,
  easier to debug, unified logging.
  4. Environment-aware: Celery Beat tasks run in the same environment as your Celery
  workers, so DB credentials, config files, and virtual environment are already set up
  correctly.
  5. Development flexibility: Easy to trigger manually via Celery for testing: celery -A
  genonaut.celery call genonaut.tasks.scheduled_tasks.refresh_tag_cardinality_stats

  The complex approach (Makefile + cron) adds unnecessary indirection. You'd need to:
  - Manage cron separately
  - Ensure the cron environment has proper PATH, DB credentials, etc.
  - Debug cron failures (harder than Celery failures)
  - Run make from cron (works but feels awkward)

  Recommendation:
  - Use Celery Beat for the scheduled task
  - Keep a make refresh-tag-stats target for manual/ad-hoc refreshes during development
  - Document both in the code/notes

  This aligns with your existing infrastructure and follows the principle of using what
  you already have rather than introducing new complexity.

> ok but the complex setup is not asking to set up a crontab. it's saying to set up a 2nd
 worker. both option (a) and (b) appear to be related to beat, but it looks like (b)
appears to set up a second worker in a more complex way, whereas (a) just hooks beat into
 my current celery worker that i'm using for everything else. am i correct about this
distinction or?

⏺ You're absolutely correct - I misread the complex option. Let me clarify:

  Option (a) Simple: Single Celery worker that handles both:
  - Regular tasks (image generation, etc.)
  - Beat schedule (runs the scheduler in the same process via -B flag)

  Option (b) Complex: Two separate processes:
  - Worker 1: Regular Celery worker for tasks
  - Worker 2: Dedicated Beat scheduler (celery -A genonaut.celery beat)

  Both use Celery Beat, but differ in process architecture.

  I still recommend (a) Simple for your use case:

  Why:
  1. Fewer processes to manage: One make celery-dev command instead of two separate
  terminals/services
  2. Lower overhead: Beat is lightweight - just triggers tasks on schedule, doesn't
  execute them
  3. Development simplicity: Easier to start/stop everything together
  4. Sufficient for your scale: You have one scheduled task (stats refresh) running once
  daily

  When you'd want (b) Complex:
  - High-scale production with many scheduled tasks
  - Need Beat scheduler redundancy/failover
  - Beat scheduler needs different resources/config than workers
  - Running in orchestrated environments (Kubernetes) where separate processes are easier
   to manage

  For local dev and even moderate production, (a) is the right choice. The -B flag on
  your worker is exactly designed for this: "I have a few scheduled tasks and don't need
  a separate Beat process."

  So yes, your understanding is spot-on. Go with (a) - just add the beat schedule config
  and run your worker with the -B flag.
