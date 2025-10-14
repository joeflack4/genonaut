# Fix Tag Hierarchy Page - Action Plan

## Problem Summary

The Tag Hierarchy page is crashing when rendering. The root cause is:

1. **Empty `tag_parents` table**: Currently 0 rows in the `tag_parents` junction table
2. **No parent-child relationships**: All 106 tags in the database have `parent: null`
3. **Missing hierarchy data**: The page expects a hierarchical tree structure but receives a flat list
4. **No error boundary**: The page crashes instead of gracefully handling the empty state

## Current State Analysis

### Database State
- `tags` table: 106 tags exist
- `tag_parents` table: 0 relationships
- Result: All tags appear as root nodes with no hierarchy

### API Response
```json
{
  "nodes": [...106 tags with parent: null...],
  "metadata": {
    "totalNodes": 106,
    "totalRelationships": 0,
    "rootCategories": 106,
    "lastUpdated": "2025-10-14T04:07:44.756461Z",
    "format": "flat_array",
    "version": "2.0"
  }
}
```

### Static Hierarchy File
- Location: `genonaut/ontologies/tags/data/hierarchy.json` - old. not using anymore.
- Status: **Not being used** - system now reads from database.

### Frontend Components
- `TagsPage.tsx`: Main page component
- `TagTreeView`: Component that renders the tree
- `useTagHierarchy`: Hook that fetches hierarchy from API
- `tag-hierarchy-service.ts`: Service with `convertToTree()` function

## Root Cause Analysis

The system was migrated from a static JSON file to database-backed tags, but:

1. **Migration incomplete**: Tag parent relationships from `hierarchy.json` were not imported into `tag_parents` table
2. **No data pipeline**: No mechanism to sync hierarchy data from JSON to database
3. **No graceful degradation**: Frontend crashes when hierarchy is empty instead of showing a helpful message

## Investigation Questions (answered)

Before implementation, investigate:

1. **Q1**: Why was `tag_parents` table not populated during migration?
   - Check git history for when tags were migrated from JSON to DB
   - Look for existing migration scripts that may have failed
   - Check if there was a previous import attempt

Answer: because we're going to redo it and we haven't yet

2. **Q2**: What is the expected source of truth for hierarchy?
   - Should `hierarchy.json` be authoritative?
   - Or should database be authoritative?
   - How do we keep them in sync?

Answer: read [tags-db-and-gallery-and-view.md](../../../../tags-db-and-gallery-and-view.md). database is the new authority. no more json

3. **Q3**: Are there any scripts/tools that modify tag hierarchy?
   - Check `genonaut/ontologies/tags/` directory
   - Look for CLI tools or admin functions
   - Understand the intended workflow for hierarchy updates

Answer: No. if there are, they are defunct. this will be done in the future. your goal is not to fix the hierarchy or make one. it's to ensure the page loads now, when there is no hierarchy.

4. **Q4**: What causes the page to crash specifically?
   - Examine browser console errors
   - Check if `TagTreeView.convertToTree()` fails with empty hierarchy
   - Identify exact line/component where crash occurs

Answer: that is really for you to figure out if this isn't sufficient, but i forgot to give you a log earlier. here it is: [fix-tag-hierarchy-log.txt](fix-tag-hierarchy-log.txt). this is what happens when you open the page.

## Related Files

### Frontend
- `frontend/src/pages/tags/TagsPage.tsx` - Main page component
- `frontend/src/components/tags/TagTreeView.tsx` - Tree rendering component
- `frontend/src/hooks/useTagHierarchy.ts` - Data fetching hook
- `frontend/src/services/tag-hierarchy-service.ts` - Service layer
- `frontend/tests/e2e/tag-hierarchy.spec.ts` - E2E tests

### Backend
- `genonaut/api/routes/tags.py` - API endpoint for hierarchy
- `genonaut/api/services/tag_service.py` - Service with get_full_hierarchy()
- `genonaut/db/schema.py` - TagParent model definition

### Data
- `genonaut/ontologies/tags/data/hierarchy.json` - Source of truth for hierarchy
- `genonaut/ontologies/tags/data/hierarchy.tsv` - TSV version of hierarchy

### Database
- `tag_parents` table - Junction table for parent-child relationships
- `tags` table - Tag definitions

## Notes

- The hierarchy.json file contains 153 nodes with 132 relationships and 4 root categories
- The database currently has 106 tags with 0 relationships and 106 root categories
- This suggests either:
  1. Not all tags from JSON were imported into database, OR
  2. Database has different tags than JSON file
- Need to reconcile which tags should exist and which relationships to preserve
