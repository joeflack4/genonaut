# Search Feature Documentation

## Overview
The Genonaut search feature provides comprehensive search capabilities across content items (both regular and auto-generated) with support for literal phrase matching and search history tracking.

## Search Algorithm

### Query Parsing
The search parser (`genonaut/api/services/search_parser.py`) extracts two types of patterns from user queries:

1. **Quoted Phrases**: Text within double quotes is treated as a literal phrase
   - Example: `"my cat"` matches only items containing the exact phrase "my cat"
   - Supports escaped quotes within phrases: `"phrase with \"nested\" quotes"`

2. **Individual Words**: Text outside of quotes is treated as individual words
   - Example: `my cat` matches items containing either "my" OR "cat"

### Search Execution
- **Fields Searched**: Both `title` and `prompt` fields
- **Matching Logic**: All phrases and words must match (AND logic)
  - Each phrase must appear in either title or prompt
  - Each word must appear in either title or prompt
- **Database Implementation**: Uses PostgreSQL ILIKE for case-insensitive substring matching
- **Performance**: Leverages existing indexes on title and prompt fields

### Search Examples

```
Query: cat dog
Matches: Items with "cat" AND "dog" anywhere in title or prompt

Query: "black cat" dog
Matches: Items with the exact phrase "black cat" AND the word "dog"

Query: "my cat" "my dog"
Matches: Items with both phrases "my cat" AND "my dog"
```

## Search History

### Storage
- **Table**: `user_search_history`
- **Fields**: id, user_id, search_query (max 500 chars), created_at
- **Indexes**:
  - Primary: user_id
  - Composite: (user_id, created_at DESC) for efficient recent search queries

### Features
- **Automatic Recording**: Every search is automatically saved to history
- **No Deduplication**: All searches are recorded, including duplicates
- **Retention**: No automatic cleanup (infinite retention)
- **Privacy**: Search history is per-user and not shared

### User Interface

#### Search History Dropdown
- **Location**: Appears below search input in Gallery sidebar and Navbar
- **Display**: Shows 3 most recent searches
- **Truncation**: Queries longer than 30 characters are truncated with "..."
- **Actions**:
  - Click search to execute it
  - Click X icon to delete from history

#### Search History Page
- **Location**: `/settings/search-history`
- **Access**: Via link in Account Settings
- **Features**:
  - Paginated list of all searches (20 per page)
  - Timestamp for each search
  - Execute button (magnifying glass icon) to run the search again
  - Delete button (trash icon) to remove individual items
  - "Clear All" button with confirmation dialog

## API Endpoints

### Add Search to History
```
POST /api/v1/users/{user_id}/search-history
Request Body: { "search_query": "my search" }
Response: SearchHistoryItem
```

### Get Recent Searches
```
GET /api/v1/users/{user_id}/search-history/recent?limit=3
Response: { "items": [SearchHistoryItem, ...] }
```

### Get Paginated History
```
GET /api/v1/users/{user_id}/search-history?page=1&page_size=20
Response: {
  "items": [SearchHistoryItem, ...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

### Delete History Item
```
DELETE /api/v1/users/{user_id}/search-history/{history_id}
Response: { "success": true, "message": "..." }
```

### Clear All History
```
DELETE /api/v1/users/{user_id}/search-history
Response: { "success": true, "deleted_count": 42, "message": "..." }
```

## Frontend Components

### Services
- **searchHistoryService** (`frontend/src/services/search-history-service.ts`): API client functions

### Hooks
- **useRecentSearches(userId, limit)**: Fetch recent searches for dropdown
- **useSearchHistory(userId, page, pageSize)**: Fetch paginated history for dedicated page
- **useAddSearchHistory(userId)**: Mutation to add search to history
- **useDeleteSearchHistory(userId)**: Mutation to delete single item
- **useClearSearchHistory(userId)**: Mutation to clear all history

### Components
- **SearchHistoryDropdown** (`frontend/src/components/search/SearchHistoryDropdown.tsx`): Dropdown UI
- **SearchHistoryPage** (`frontend/src/pages/settings/SearchHistoryPage.tsx`): Full history page

## Implementation Status

### Completed
- Database schema and migrations
- Search query parser with quote detection
- Enhanced search in ContentService (integrated into get_unified_content_paginated)
- Complete backend API (repository, service, routes)
- Frontend services and hooks
- Search history page with full CRUD operations
- Settings page integration

### Remaining
- Gallery page search integration (wire up SearchHistoryDropdown, add search execution)
- Navbar search integration (wire up SearchHistoryDropdown, handle navigation)
- Unit tests for parser, hooks, and components
- E2E tests for search flow
- Final integration testing

## Future Enhancements

### Potential Improvements
- **Full-Text Search**: Use PostgreSQL FTS (ts_query) for word matching instead of ILIKE
- **Search Suggestions**: Auto-complete based on search history
- **Search Analytics**: Track popular searches across all users
- **Advanced Syntax**: Support for NOT operator, wildcards, field-specific searches
- **History Cleanup**: Add background job to clean searches older than N months
- **Search Filters**: Save and reuse complex filter combinations
- **Export History**: Allow users to download their search history

### Performance Optimization
- Add FTS indexes if not already present
- Consider PostgreSQL trigram indexes for fuzzy matching
- Implement search result caching for common queries
- Add query timeout protection for complex searches

## Testing

### Backend Tests
- **Unit**: `test/unit/test_search_parser.py` (22 tests, all passing)
- **Database**: TODO - test search functionality across content tables
- **API**: TODO - test all search history endpoints

### Frontend Tests
- **Unit**: TODO - test hooks and components
- **E2E**: TODO - test complete search flow from input to results

### Manual Testing Checklist
- [ ] Search with simple words works
- [ ] Search with quoted phrases works
- [ ] Mixed quoted and unquoted works
- [ ] Search history dropdown appears on focus
- [ ] Clicking history item populates input
- [ ] Deleting history item works
- [ ] Search history page displays all items
- [ ] Pagination on history page works
- [ ] Executing search from history page works
- [ ] Clear all with confirmation works
- [ ] Search persists across page navigation

## Troubleshooting

### Common Issues

**Search returns no results**
- Check that search term has no typos
- Verify quoted phrases are exact matches
- Check that content exists in database with matching text

**Search history not saving**
- Verify user is authenticated
- Check browser console for API errors
- Verify database migration was applied

**Search history dropdown not appearing**
- Check that user has search history in database
- Verify API endpoint is returning data
- Check browser console for errors

**Performance issues with search**
- Verify indexes exist on title and prompt fields
- Check database query performance with EXPLAIN ANALYZE
- Consider query timeout if database is large
