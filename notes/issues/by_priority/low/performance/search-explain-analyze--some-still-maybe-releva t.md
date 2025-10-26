# Search Query EXPLAIN ANALYZE Results

## Context
Analysis of SQL query execution for search term "grumpy cat" from the gallery page.

**Frontend URL:** `http://localhost:5173/gallery?search=%22grumpy+cat%22`

**Request Parameters:**
- `page=1`
- `page_size=10`
- `content_types=regular,auto`
- `creator_filter=all`
- `user_id=121e194b-4caa-4b81-ad4f-86ca3919d5b9`
- `sort_field=created_at`
- `sort_order=desc`
- `search_term="grumpy cat"`

## Generated SQL Query

The search parser detects quoted phrases and generates an ILIKE search for exact substring matching.

### Simplified Query (for EXPLAIN ANALYZE)

```sql
SELECT anon_1.*
FROM (
  SELECT content_items.id, content_items.title, content_items.content_type,
         content_items.created_at, 'regular' AS source_type, users.username AS creator_username
  FROM content_items
  JOIN users ON users.id = content_items.creator_id
  WHERE content_items.title ILIKE '%grumpy cat%' OR content_items.prompt ILIKE '%grumpy cat%'

  UNION ALL

  SELECT content_items_auto.id, content_items_auto.title, content_items_auto.content_type,
         content_items_auto.created_at, 'auto' AS source_type, users.username AS creator_username
  FROM content_items_auto
  JOIN users ON users.id = content_items_auto.creator_id
  WHERE content_items_auto.title ILIKE '%grumpy cat%' OR content_items_auto.prompt ILIKE '%grumpy cat%'
) AS anon_1
ORDER BY anon_1.created_at DESC
LIMIT 10;
```

## EXPLAIN ANALYZE Output

```
Limit  (cost=15.00..15.00 rows=2 width=796) (actual time=0.213..0.216 rows=0 loops=1)
  Output: content_items.id, content_items.title, content_items.content_type, content_items.created_at, ('regular'::text), users.username
  Buffers: shared hit=4 read=2
  ->  Sort  (cost=15.00..15.00 rows=2 width=796) (actual time=0.213..0.216 rows=0 loops=1)
        Output: content_items.id, content_items.title, content_items.content_type, content_items.created_at, ('regular'::text), users.username
        Sort Key: content_items.created_at DESC
        Sort Method: quicksort  Memory: 25kB
        Buffers: shared hit=4 read=2
        ->  Append  (cost=1.16..14.99 rows=2 width=796) (actual time=0.199..0.202 rows=0 loops=1)
              Buffers: shared hit=1 read=2
              ->  Hash Join  (cost=1.16..2.76 rows=1 width=796) (actual time=0.193..0.193 rows=0 loops=1)
                    Output: content_items.id, content_items.title, content_items.content_type, content_items.created_at, 'regular'::text, users.username
                    Hash Cond: (users.id = content_items.creator_id)
                    Buffers: shared read=2
                    ->  Seq Scan on public.users  (cost=0.00..1.43 rows=43 width=122) (actual time=0.030..0.030 rows=1 loops=1)
                          Output: users.id, users.username, users.email, users.created_at, users.updated_at, users.preferences, users.is_active
                          Buffers: shared read=1
                    ->  Hash  (cost=1.15..1.15 rows=1 width=650) (actual time=0.158..0.158 rows=0 loops=1)
                          Output: content_items.id, content_items.title, content_items.content_type, content_items.created_at, content_items.creator_id
                          Buckets: 1024  Batches: 1  Memory Usage: 8kB
                          Buffers: shared read=1
                          ->  Seq Scan on public.content_items  (cost=0.00..1.15 rows=1 width=650) (actual time=0.158..0.158 rows=0 loops=1)
                                Output: content_items.id, content_items.title, content_items.content_type, content_items.created_at, content_items.creator_id
                                Filter: (((content_items.title)::text ~~* '%grumpy cat%'::text) OR ((content_items.prompt)::text ~~* '%grumpy cat%'::text))
                                Rows Removed by Filter: 10
                                Buffers: shared read=1
              ->  Hash Join  (cost=10.61..12.21 rows=1 width=796) (actual time=0.006..0.008 rows=0 loops=1)
                    Output: content_items_auto.id, content_items_auto.title, content_items_auto.content_type, content_items_auto.created_at, 'auto'::text, users_1.username
                    Hash Cond: (users_1.id = content_items_auto.creator_id)
                    Buffers: shared hit=1
                    ->  Seq Scan on public.users users_1  (cost=0.00..1.43 rows=43 width=122) (actual time=0.001..0.001 rows=1 loops=1)
                          Output: users_1.id, users_1.username, users_1.email, users_1.created_at, users_1.updated_at, users_1.preferences, users_1.is_active
                          Buffers: shared hit=1
                    ->  Hash  (cost=10.60..10.60 rows=1 width=650) (actual time=0.001..0.003 rows=0 loops=1)
                          Output: content_items_auto.id, content_items_auto.title, content_items_auto.content_type, content_items_auto.created_at, content_items_auto.creator_id
                          Buckets: 1024  Batches: 1  Memory Usage: 8kB
                          ->  Seq Scan on public.content_items_auto  (cost=0.00..10.60 rows=1 width=650) (actual time=0.001..0.001 rows=0 loops=1)
                                Output: content_items_auto.id, content_items_auto.title, content_items_auto.content_type, content_items_auto.created_at, content_items_auto.creator_id
                                Filter: (((content_items_auto.title)::text ~~* '%grumpy cat%'::text) OR ((content_items_auto.prompt)::text ~~* '%grumpy cat%'::text))

Planning:
  Buffers: shared hit=634 read=59
Planning Time: 11.518 ms
Execution Time: 0.247 ms
```

## Key Observations

### Performance Metrics
- **Total Execution Time:** 0.247 ms (very fast!)
- **Planning Time:** 11.518 ms
- **Total Time:** ~16 ms

### Query Execution Plan Analysis

1. **Strategy:** PostgreSQL uses a UNION ALL with Append node to combine results from both tables
2. **Scan Type:** Sequential scans (Seq Scan) on both `content_items` and `content_items_auto`
3. **Join Type:** Hash joins with the `users` table to get creator username
4. **Sorting:** Quicksort on `created_at DESC` with minimal memory (25kB)

### Buffer Usage
- **Shared Buffers Hit:** 5 (data already in memory)
- **Shared Buffers Read:** 2 (data read from disk)
- **Total Buffer Accesses:** 7 (very low, indicating small dataset)

### Filter Performance

For `content_items` table:
```
Filter: (((content_items.title)::text ~~* '%grumpy cat%'::text) OR ((content_items.prompt)::text ~~* '%grumpy cat%'::text))
Rows Removed by Filter: 10
```
- Scanned 10 rows in `content_items`, found 0 matches
- ILIKE pattern matching with wildcards on both sides (`%...%`)

For `content_items_auto` table:
- Similar filter applied
- No rows matched

### Observations

1. **Sequential Scans:** The database is doing full table scans (Seq Scan) rather than using indexes. This is reasonable because:
   - The tables are small (10 rows in content_items, likely similar in content_items_auto)
   - ILIKE with leading wildcards (`%grumpy cat%`) cannot use B-tree indexes effectively
   - PostgreSQL correctly determined sequential scan is faster for small datasets

2. **ILIKE Pattern Matching:**
   - The search uses `ILIKE '%grumpy cat%'` which is case-insensitive
   - Leading wildcard prevents index usage
   - For larger datasets, this could become a performance bottleneck

3. **Performance is Excellent (for this dataset):**
   - 0.247ms execution time is very fast
   - Small number of buffer accesses indicates minimal I/O

## Search Implementation Details

From the code analysis (`content_service.py:151-198`), the search uses:

1. **Parse Search Query:** `parse_search_query()` detects quoted phrases vs individual words
2. **Phrase Matching:** Quoted strings like `"grumpy cat"` become exact substring searches
3. **Word Matching:** Unquoted words are searched individually (all must match - AND logic)
4. **Fields Searched:** Both `title` and `prompt` fields
5. **Logic:** Phrases/words combined with AND, but within each phrase/word the title OR prompt must match

## Potential Optimizations (for larger datasets)

If the tables grow significantly larger (100K+ rows), consider:

1. **Full-Text Search (FTS):**
   - Use PostgreSQL's built-in full-text search with `tsvector` and GIN indexes
   - Would allow indexed phrase searches
   - Example: `ALTER TABLE content_items ADD COLUMN search_vector tsvector;`

me: we have this for gen jobs prompt and content items title fields

2. **Trigram Indexes (pg_trgm):**
   - Enable the `pg_trgm` extension
   - Create GIN or GiST indexes on title and prompt
   - Supports ILIKE with wildcards
   - Example: `CREATE INDEX idx_content_title_trgm ON content_items USING gin(title gin_trgm_ops);`

me: we have this

3. **Specialized Search Columns:**
   - Create a computed/materialized column combining title + prompt
   - Index this combined column
   - Reduces OR conditions in WHERE clause

4. **Query Rewriting:**
   - Consider separating the UNION ALL into independent queries
   - Use UNION instead of UNION ALL if deduplication is needed
   - Could parallelize execution of independent subqueries

## Full Query Details

The actual production query includes many more columns and additional filtering logic:

### Main Data Query (4 queries executed)

**Query 1:** Count query for pagination
```sql
SELECT count(*) AS count_1
FROM (SELECT anon_2.id AS id, anon_2.title AS title, ... FROM (...) AS anon_2) AS anon_1
```

**Query 2-3:** Title-only counts for each table
```sql
SELECT count(content_items.id) AS count_1
FROM content_items
WHERE content_items.title ILIKE '%"grumpy cat"%'
```

**Query 4:** Main data retrieval (shown above in EXPLAIN ANALYZE)

**Query 5-8:** Stats queries for user and community counts

### Parameters Used
- `param_1`: 'regular' (source_type literal)
- `param_2`: 'auto' (source_type literal)
- `title_1/title_2`: '%grumpy cat%' (search pattern)
- `prompt_1/prompt_2`: '%grumpy cat%' (search pattern)
- `param_3`: 10 (LIMIT)
- `param_4`: 0 (OFFSET)

## Conclusion

The current search implementation performs well for small to medium datasets:
- Sub-millisecond execution time
- Minimal memory usage
- Reasonable query plan

For production with larger datasets, full-text search or trigram indexes would be recommended to maintain performance as data scales.
