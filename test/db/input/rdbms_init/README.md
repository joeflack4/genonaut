# Test Database Seed Data

This directory contains TSV files used for seeding test databases.

## File Sizes

### Current (Active) Files
- `content_items.tsv` - 100 rows
- `content_item_autos.tsv` - 100 rows
- `generation_jobs.tsv` - 100 rows
- `users.tsv` - 57 rows
- `user_interactions.tsv` - minimal data
- `recommendations.tsv` - minimal data

### Full Dataset (Archived)
- `content_items_full.tsv` - 1000 rows (original)
- `content_item_autos_full.tsv` - 1000 rows (original)
- `generation_jobs_full.tsv` - 1000 rows (original)

## Performance Optimization (2025-10-13)

The test dataset was reduced from 1000 rows to 100 rows per table to improve test performance:

- **Before**: Database seeding tests took ~463 seconds (7m 43s)
- **After**: Database seeding tests take ~38 seconds
- **Speedup**: 12x faster (66x for individual test)

### Why It Was Slow

Each content item had ~100 tags. With 1000 items × 100 tags = 100,000 tag relationships to process and insert into the `content_tags` junction table. The tag syncing code was creating/checking each tag individually.

### Solution

Reduced test data to 1/10th the size (100 rows instead of 1000). This provides:
- Sufficient test coverage
- Much faster test execution
- Same variety of test cases (just fewer of each)

## Restoring Full Dataset

If you need the full dataset for performance testing or other purposes:

```bash
cd test/db/input/rdbms_init
mv content_items.tsv content_items_small.tsv
mv content_item_autos.tsv content_item_autos_small.tsv
mv generation_jobs.tsv generation_jobs_small.tsv
mv content_items_full.tsv content_items.tsv
mv content_item_autos_full.tsv content_item_autos.tsv
mv generation_jobs_full.tsv generation_jobs.tsv
```
