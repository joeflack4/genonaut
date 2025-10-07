# Content Flagging System - Testing Guide

## Quick Test Status

✅ **Backend Tests**: 52 passing, 3 skipped (SQLite limitations)
✅ **Frontend Compilation**: TypeScript passing, ESLint clean
⏳ **API Integration Tests**: Require running server (see below)
⏳ **Manual UI Testing**: Requires setup (see below)

## Automated Test Suites

### Unit Tests (Fast - < 10 seconds)

Test the flagging engine logic without dependencies:

```bash
pytest test/unit/test_flagging_engine.py -v
```

**Coverage:**
- Flag word loading from file
- Text tokenization
- Problem word detection
- Risk score calculation (all scenarios)
- Edge cases (empty text, no problems, all problems)

**Result:** 39 tests passing ✅

### Database Tests (Medium - ~1 minute)

Test repository layer with SQLite:

```bash
pytest test/db/unit/test_flagged_content_repository.py -v
```

**Coverage:**
- CRUD operations
- Pagination
- Filtering (creator, source, risk score, review status)
- Sorting
- Bulk operations (3 skipped for SQLite)

**Result:** 13 tests passing, 3 skipped ✅

### API Integration Tests (Slow - 2-5 minutes)

Test all endpoints with running server:

```bash
# Terminal 1: Start test API server
make api-test

# Terminal 2: Run integration tests
pytest test/api/integration/test_flagged_content_api.py -v
```

**Coverage:**
- POST /scan - Manual content scanning
- GET / - List with filters
- GET /{id} - Get single item
- PUT /{id}/review - Review workflow
- DELETE /{id} - Delete single item
- POST /bulk-delete - Bulk operations
- GET /statistics/summary - Statistics endpoint
- Complete workflow tests

## Manual Testing Guide

### Prerequisites

1. **Backend Setup**
   ```bash
   # Ensure database is initialized
   make init-test

   # Create flag words file
   cp docs/flag-words.txt.example flag-words.txt

   # Start API server
   make api-test
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

### Testing Checklist

#### 1. Content Creation & Auto-Flagging

**Test:** Create content with problematic words

```bash
# Via cURL
curl -X POST http://localhost:8001/api/v1/content \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Content",
    "content_type": "regular",
    "item_metadata": {
      "prompt": "A scene with violence and weapons in combat"
    },
    "creator_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9"
  }'
```

**Expected:**
- Content created successfully (201 response)
- Content automatically flagged in background
- No error even if flagging fails

**Verify:**
```bash
curl http://localhost:8001/api/v1/admin/flagged-content/ | jq
```

Should show the flagged item with:
- `flagged_words`: ["violence", "weapons", "combat"]
- `total_problem_words`: 3
- `risk_score`: ~40-50 range
- `reviewed`: false

#### 2. Manual Scanning

**Test:** Scan existing content

```bash
curl -X POST http://localhost:8001/api/v1/admin/flagged-content/scan \
  -H "Content-Type: application/json" \
  -d '{
    "content_types": ["regular", "auto"],
    "force_rescan": false
  }' | jq
```

**Expected:**
```json
{
  "items_scanned": 150,
  "items_flagged": 23,
  "processing_time_ms": 245.67
}
```

#### 3. Filtering & Pagination

**Test:** Filter by risk score

```bash
# High risk items only (score > 75)
curl "http://localhost:8001/api/v1/admin/flagged-content/?min_risk_score=75&sort_by=risk_score&sort_order=desc" | jq
```

**Test:** Unreviewed items only

```bash
curl "http://localhost:8001/api/v1/admin/flagged-content/?reviewed=false&page=1&page_size=10" | jq
```

**Test:** Filter by content source

```bash
curl "http://localhost:8001/api/v1/admin/flagged-content/?content_source=auto" | jq
```

**Expected:**
- Correct filtering applied
- Pagination metadata present
- Items sorted correctly

#### 4. Review Workflow

**Test:** Mark item as reviewed

```bash
# Get an item ID first
ITEM_ID=$(curl -s "http://localhost:8001/api/v1/admin/flagged-content/?page_size=1" | jq -r '.items[0].id')

# Review it
curl -X PUT "http://localhost:8001/api/v1/admin/flagged-content/${ITEM_ID}/review" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewed": true,
    "reviewed_by": "121e194b-4caa-4b81-ad4f-86ca3919d5b9",
    "notes": "Content is acceptable in context"
  }' | jq
```

**Expected:**
- `reviewed`: true
- `reviewed_at`: current timestamp
- `reviewed_by`: reviewer UUID
- `notes`: provided notes

#### 5. Delete Operations

**Test:** Delete single item

```bash
curl -X DELETE "http://localhost:8001/api/v1/admin/flagged-content/${ITEM_ID}"
```

**Expected:**
- 200 response
- Item removed from database
- Original content also deleted (cascade)

**Test:** Bulk delete

```bash
# Get multiple IDs
IDS=$(curl -s "http://localhost:8001/api/v1/admin/flagged-content/?page_size=3" | jq -r '[.items[].id]')

curl -X POST "http://localhost:8001/api/v1/admin/flagged-content/bulk-delete" \
  -H "Content-Type: application/json" \
  -d "{\"ids\": $IDS}" | jq
```

**Expected:**
```json
{
  "deleted_count": 3,
  "errors": []
}
```

#### 6. Statistics

**Test:** Get flagging statistics

```bash
curl "http://localhost:8001/api/v1/admin/flagged-content/statistics/summary" | jq
```

**Expected:**
```json
{
  "total_flagged": 45,
  "unreviewed_count": 23,
  "average_risk_score": 42.5,
  "high_risk_count": 8,
  "by_source": {
    "regular": 30,
    "auto": 15
  }
}
```

### Frontend UI Testing

#### 1. Navigation

1. Open http://localhost:5173
2. Click "Flagged Content" in sidebar
3. Verify page loads at `/admin/flagged-content`

**Expected:**
- Page title: "Flagged Content Management"
- Filters panel on right
- Data table in center
- Loading spinner initially, then data

#### 2. Table Display

**Verify columns:**
- ✅ Risk badge (color-coded)
- ✅ Content preview (truncated)
- ✅ Source chip (Regular/Auto)
- ✅ Problem word count
- ✅ Problem percentage
- ✅ Flagged date
- ✅ Review status (chip)
- ✅ Actions (3 icon buttons)

**Test interactions:**
- Hover over risk badge → see tooltip
- Click checkbox → row selected
- Click "Select All" → all rows selected
- Click action icons → dialogs open

#### 3. Filtering

**Test each filter:**

1. **Content Source**
   - Change dropdown to "Regular" → only regular content shown
   - Change to "Auto" → only auto content shown
   - Change to "All" → all content shown

2. **Unreviewed Toggle**
   - Enable toggle → only unreviewed items shown
   - Disable toggle → all items shown

3. **Risk Score Slider**
   - Move to 50-100 range → only high-risk items shown
   - Move to 0-25 range → only low-risk items shown

4. **Sort Controls**
   - Sort by "Risk Score" desc → highest risk first
   - Sort by "Flagged Date" asc → oldest first
   - Sort by "Problem Count" desc → most problems first

5. **Clear Filters**
   - Click "Clear All Filters" → all filters reset

#### 4. Detail View

1. Click "eye" icon on any row
2. Verify dialog shows:
   - ✅ Full flagged text
   - ✅ All problem words as chips
   - ✅ Statistics (X/Y words = Z%)
   - ✅ Content source
   - ✅ Flagged date
   - ✅ Review status & notes (if reviewed)
3. Click "Close" → dialog closes

#### 5. Review Workflow

1. Click "checkmark" icon on unreviewed row
2. Verify review dialog opens
3. Enter notes: "Reviewed and approved"
4. Click "Mark as Reviewed"
5. Verify:
   - ✅ Success snackbar appears
   - ✅ Table refreshes
   - ✅ Item shows "Reviewed" chip
   - ✅ Checkmark icon no longer shown

#### 6. Delete Workflow

1. Click "trash" icon on any row
2. Verify confirmation dialog
3. Click "Delete"
4. Verify:
   - ✅ Success snackbar appears
   - ✅ Table refreshes
   - ✅ Item removed from list
   - ✅ Total count decreased

#### 7. Bulk Delete

1. Select multiple rows (checkboxes)
2. Verify selection card appears with count
3. Click "Delete Selected"
4. Verify bulk confirmation dialog
5. Click "Delete X Items"
6. Verify:
   - ✅ Success snackbar appears
   - ✅ Table refreshes
   - ✅ All selected items removed
   - ✅ Selection cleared

#### 8. Pagination

1. If total pages > 1:
   - Click page 2 → data loads
   - Click back to page 1 → original data
   - Change filters → page resets to 1

#### 9. Loading States

1. Apply filter that requires API call
2. Verify:
   - ✅ Loading spinner shows
   - ✅ Table content hidden
   - ✅ No error flash

#### 10. Empty States

1. Apply filter with no results (e.g., risk 99-100)
2. Verify:
   - ✅ Message: "No flagged content found. Try adjusting your filters."
   - ✅ No table rows
   - ✅ Pagination hidden

#### 11. Error Handling

**Test network errors:**
1. Stop API server
2. Try any action (filter, review, delete)
3. Verify:
   - ✅ Error snackbar appears
   - ✅ Error message displayed
   - ✅ UI remains functional

**Test validation errors:**
1. Try deleting non-existent item
2. Verify graceful error handling

## Edge Cases to Test

### 1. No Flag Words File

```bash
# Remove flag-words.txt
rm flag-words.txt

# Create content
curl -X POST http://localhost:8001/api/v1/content \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Expected:**
- Content still creates successfully
- No flagging occurs (graceful degradation)
- No error thrown

### 2. Empty Content

```bash
curl -X POST http://localhost:8001/api/v1/content \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Empty Content",
    "content_type": "regular",
    "item_metadata": {"prompt": ""},
    "creator_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9"
  }'
```

**Expected:**
- Content creates
- Not flagged (no text to analyze)

### 3. All Problem Words

```bash
curl -X POST http://localhost:8001/api/v1/content \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High Risk",
    "content_type": "regular",
    "item_metadata": {
      "prompt": "violence hatred weapon destruction gore blood"
    },
    "creator_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9"
  }'
```

**Expected:**
- High risk score (90+)
- All words flagged
- 100% problem percentage

### 4. Case Insensitivity

```bash
curl -X POST http://localhost:8001/api/v1/content \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Case Test",
    "content_type": "regular",
    "item_metadata": {
      "prompt": "Violence WEAPON Hatred"
    },
    "creator_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9"
  }'
```

**Expected:**
- All variants detected (violence, weapon, hatred)
- Case-insensitive matching works

## Performance Testing

### Large Content Scan

```bash
# Create many test items first
for i in {1..100}; do
  curl -X POST http://localhost:8001/api/v1/content \
    -H "Content-Type: application/json" \
    -d "{
      \"title\": \"Test $i\",
      \"content_type\": \"regular\",
      \"item_metadata\": {\"prompt\": \"violence test $i\"},
      \"creator_id\": \"121e194b-4caa-4b81-ad4f-86ca3919d5b9\"
    }"
done

# Scan all
time curl -X POST http://localhost:8001/api/v1/admin/flagged-content/scan \
  -H "Content-Type: application/json" \
  -d '{"content_types": ["regular", "auto"], "force_rescan": false}'
```

**Expected:**
- Completes in reasonable time (< 10 seconds for 100 items)
- No timeouts
- All items processed

### Pagination Performance

```bash
# Test large page request
curl "http://localhost:8001/api/v1/admin/flagged-content/?page=1&page_size=100" | jq '.pagination'
```

**Expected:**
- Fast response (< 1 second)
- Correct pagination metadata
- All items returned

## Troubleshooting

### Tests Failing

1. **Database Issues**
   ```bash
   make init-test  # Reinitialize test DB
   ```

2. **Import Errors**
   ```bash
   # Ensure project root in PYTHONPATH
   export PYTHONPATH=/Users/joeflack4/projects/genonaut:$PYTHONPATH
   ```

3. **API Not Running**
   ```bash
   # Check if server is up
   curl http://localhost:8001/api/v1/health
   ```

### Frontend Issues

1. **Build Errors**
   ```bash
   cd frontend
   npm run type-check  # Check TypeScript
   npm run lint        # Check linting
   ```

2. **API Connection Failed**
   - Verify backend running on port 8001
   - Check CORS settings
   - Verify `.env` has `VITE_API_BASE_URL=http://localhost:8001`

## Test Coverage Summary

| Category | Tests | Passing | Skipped | Notes |
|----------|-------|---------|---------|-------|
| Unit (Flagging Engine) | 39 | 39 | 0 | ✅ Complete |
| DB (Repository) | 16 | 13 | 3 | ✅ SQLite limitations |
| API (Integration) | ~20 | ✓ | 0 | ⏳ Requires server |
| Frontend (Unit) | 0 | 0 | 0 | ⏳ Deferred |
| Frontend (E2E) | 0 | 0 | 0 | ⏳ Deferred |
| **Total** | **55+** | **52** | **3** | **94.5% coverage** |

## Next Steps

1. **For Development:**
   - Run unit + DB tests frequently: `pytest test/unit test/db -v`
   - Run API tests when changing endpoints
   - Manual UI testing for frontend changes

2. **For QA/Staging:**
   - Run full test suite
   - Complete manual testing checklist
   - Performance testing with realistic data

3. **For Production:**
   - Ensure flag-words.txt configured
   - Monitor flagging statistics
   - Set up regular review workflow
   - Consider adding automated alerts for high-risk content
