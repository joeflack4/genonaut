# Content Flagging System Documentation

## Overview

The Genonaut Content Flagging System automatically detects and flags content containing potentially problematic words. It provides an administrative interface for reviewing and managing flagged content with comprehensive risk metrics.

## Features

- **Automatic Detection**: Content is automatically scanned for problematic words during creation
- **Risk Scoring**: Sophisticated risk calculation based on word count, percentage, and diversity
- **Admin Management**: Full CRUD interface for reviewing, filtering, and managing flagged content
- **Manual Scanning**: Ability to manually scan existing content
- **Bulk Operations**: Delete multiple flagged items at once
- **Statistics**: Real-time statistics about flagged content
- **Flexible Configuration**: Configurable danger word list via text file

## Documentation overview

- **Quick Start**: [5-Minute Setup Guide](docs/flagging-quickstart.md) - Get started fast!
- **Full Guide**: [Content Flagging Documentation](docs/flagging.md) - Complete API reference and examples
- **Testing**: [Testing Guide](docs/flagging-testing.md) - Test suites and manual testing checklist
- **API Reference**: See `/api/v1/admin/flagged-content` endpoints in API docs (http://localhost:8001/docs)
- **Implementation Spec**: [Technical Details](notes/issues/by_priority/low/flagging.md) - Phase-by-phase implementation notes

## Quick Setup

1. Create your flag words configuration:
   ```bash
   cp docs/flag-words.txt.example flag-words.txt
   ```

2. Edit `flag-words.txt` to add words that should trigger flagging

3. Content is automatically flagged during creation - no additional setup needed!

## Configuration

### Flag Words File

Create a `flag-words.txt` file in the project root directory:

```bash
cp docs/flag-words.txt.example flag-words.txt
```

Edit the file to add words that should trigger flagging:

```
# Comment lines start with #
violence
weapon
hatred
explicit
# Add more words as needed
```

**Important**: The `flag-words.txt` file is in `.gitignore` for security. Never commit this file to version control. Use the example file at `docs/flag-words.txt.example` as a template.

### Environment Variables

No additional environment variables are required. The system will automatically detect the flag-words.txt file in the project root.

## How It Works

### Automatic Flagging

When content is created via the API, the system:

1. Extracts text to analyze (from `item_metadata.prompt` or title)
2. Tokenizes the text into words
3. Checks each word against the danger word list
4. Calculates risk metrics if problems are found
5. Creates a flagged content record linked to the original content

Content creation **never fails** due to flagging - the system gracefully handles all errors.

### Risk Score Calculation

The risk score (0-100) is calculated using a weighted formula:

- **40%**: Percentage of words that are problematic
- **30%**: Total count of problem words (normalized to max 10)
- **30%**: Diversity of unique problem words (normalized to max 5)

#### Example Calculations

**Low Risk (Score: 9.4)**
- Text: "Create a scene with one violence incident" (7 words)
- Problem words: 1 occurrence of "violence"
- Unique problems: 1
- Calculation: (1/7)×100×0.4 + (1/10)×100×0.3 + (1/5)×100×0.3 = 9.4

**High Risk (Score: 68.0)**
- Text: "violence hatred weapon combat destruction" (5 words)
- Problem words: 5 occurrences
- Unique problems: 5
- Calculation: (5/5)×100×0.4 + (5/10)×100×0.3 + (5/5)×100×0.3 = 68.0

### Risk Levels

- **0-25**: Low Risk (Green)
- **26-50**: Medium Risk (Yellow)
- **51-75**: High Risk (Orange)
- **76-100**: Critical Risk (Red)

## API Endpoints

All flagged content endpoints are under `/api/v1/admin/flagged-content`.

### Scan Content

Manually trigger scanning of existing content:

```http
POST /api/v1/admin/flagged-content/scan
Content-Type: application/json

{
  "content_types": ["regular", "auto"],
  "force_rescan": false
}
```

**Response:**
```json
{
  "items_scanned": 150,
  "items_flagged": 23,
  "processing_time_ms": 245.67
}
```

### List Flagged Content

Get paginated list with filters:

```http
GET /api/v1/admin/flagged-content/?page=1&page_size=10&sort_by=risk_score&sort_order=desc
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 10, max: 100)
- `creator_id` (UUID): Filter by creator
- `content_source` (string): Filter by source ("regular" or "auto")
- `min_risk_score` (float): Minimum risk score (0-100)
- `max_risk_score` (float): Maximum risk score (0-100)
- `reviewed` (boolean): Filter by review status
- `sort_by` (string): Sort field ("risk_score", "flagged_at", "problem_count")
- `sort_order` (string): Sort order ("asc" or "desc")

**Response:**
```json
{
  "items": [
    {
      "id": 123,
      "content_item_id": 456,
      "content_source": "regular",
      "flagged_text": "Create a scene with violence and weapons",
      "flagged_words": ["violence", "weapons"],
      "total_problem_words": 2,
      "total_words": 7,
      "problem_percentage": 28.57,
      "risk_score": 45.2,
      "creator_id": "uuid-here",
      "flagged_at": "2025-10-01T12:34:56Z",
      "reviewed": false,
      "reviewed_at": null,
      "reviewed_by": null,
      "notes": null
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 23,
    "has_next": true,
    "has_previous": false
  }
}
```

### Get Flagged Content Details

Get a single flagged content item:

```http
GET /api/v1/admin/flagged-content/{id}
```

### Review Flagged Content

Mark content as reviewed:

```http
PUT /api/v1/admin/flagged-content/{id}/review
Content-Type: application/json

{
  "reviewed": true,
  "reviewed_by": "reviewer-uuid",
  "notes": "Reviewed and approved for context"
}
```

### Delete Flagged Content

Delete both the flagged record and the original content:

```http
DELETE /api/v1/admin/flagged-content/{id}
```

**Note**: This deletes the original content item as well via cascade.

### Bulk Delete

Delete multiple flagged items:

```http
POST /api/v1/admin/flagged-content/bulk-delete
Content-Type: application/json

{
  "ids": [123, 124, 125]
}
```

**Response:**
```json
{
  "deleted_count": 2,
  "errors": [
    {
      "id": 125,
      "error": "FlaggedContent not found"
    }
  ]
}
```

### Get Statistics

Get statistics about flagged content:

```http
GET /api/v1/admin/flagged-content/statistics/summary
```

**Response:**
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

## Database Schema

### flagged_content Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| content_item_id | Integer | FK to content_items (nullable) |
| content_item_auto_id | Integer | FK to content_items_auto (nullable) |
| content_source | String(20) | 'regular' or 'auto' |
| flagged_text | Text | The text that was flagged |
| flagged_words | JSONB | Array of problem words found |
| total_problem_words | Integer | Count of problem word occurrences |
| total_words | Integer | Total word count |
| problem_percentage | Float | Percentage of problematic words |
| risk_score | Float | Calculated risk score (0-100) |
| creator_id | UUID | FK to users |
| flagged_at | DateTime | When content was flagged |
| reviewed | Boolean | Review status |
| reviewed_at | DateTime | When reviewed (nullable) |
| reviewed_by | UUID | FK to users (nullable) |
| notes | Text | Admin notes (nullable) |

### Indexes

The table includes optimized indexes for:
- Pagination by risk score, flagged date
- Filtering by creator, source, review status
- Unreviewed high-risk items (partial index)
- GIN index on flagged_words array

## Usage Examples

### Python Client

```python
import requests

base_url = "http://localhost:8000/api/v1/admin/flagged-content"

# Get high-risk unreviewed items
response = requests.get(
    f"{base_url}/",
    params={
        "reviewed": False,
        "min_risk_score": 75,
        "sort_by": "risk_score",
        "sort_order": "desc"
    }
)
high_risk_items = response.json()

# Review an item
requests.put(
    f"{base_url}/{item_id}/review",
    json={
        "reviewed": True,
        "reviewed_by": "admin-uuid",
        "notes": "Content is acceptable in context"
    }
)

# Delete inappropriate content
requests.delete(f"{base_url}/{item_id}")
```

### cURL Examples

```bash
# Scan existing content
curl -X POST http://localhost:8000/api/v1/admin/flagged-content/scan \
  -H "Content-Type: application/json" \
  -d '{"content_types": ["regular"], "force_rescan": false}'

# List flagged content
curl "http://localhost:8000/api/v1/admin/flagged-content/?page=1&page_size=10"

# Get statistics
curl http://localhost:8000/api/v1/admin/flagged-content/statistics/summary
```

## Testing

### Unit Tests

Run flagging engine unit tests:

```bash
pytest test/unit/test_flagging_engine.py -v
```

### Repository Tests

Run database repository tests:

```bash
pytest test/db/unit/test_flagged_content_repository.py -v
```

### API Integration Tests

Run full API integration tests:

```bash
pytest test/api/integration/test_flagged_content_api.py -v
```

**Note**: Integration tests require:
- API server running
- Test database configured
- Optional: flag-words.txt for full workflow tests

## Troubleshooting

### Flag Words File Not Found

**Error**: `ValidationError: Flag words file not found`

**Solution**:
1. Copy `docs/flag-words.txt.example` to `flag-words.txt` in project root
2. Ensure file is in project root
3. Verify file contains at least one word

### Content Not Being Flagged

**Possible causes**:
1. Flag words file not configured
2. Content doesn't contain any flag words
3. Text being analyzed is empty (check `item_metadata.prompt`)

**Debug**:
```python
from genonaut.utils.flagging import analyze_content, load_flag_words

# Load flag words
words = load_flag_words("flag-words.txt")
print(f"Loaded {len(words)} flag words")

# Test analysis
result = analyze_content("test text here", words)
print(result)
```

### High Memory Usage During Scan

Large content scans may use significant memory. Consider:
1. Scanning in batches
2. Setting `force_rescan=False` to skip already-flagged items
3. Scanning only specific content types

### Cascade Delete Not Working

The `DELETE` endpoint removes both the flagged record and original content via PostgreSQL cascade. If using SQLite for testing, cascade may not work properly - use PostgreSQL for production.

## Best Practices

1. **Regular Reviews**: Schedule regular reviews of flagged content
2. **Update Flag Words**: Periodically review and update your flag word list
3. **Context Matters**: Always review context before deleting content
4. **Monitor Statistics**: Use statistics endpoint to track trends
5. **Privacy**: Never commit flag-words.txt to version control
6. **Backup**: Backup flagged content data before bulk deletes
7. **Testing**: Use test/db/input/flag-words.txt for testing only

## Future Enhancements

Potential future improvements:
- Appeal/unflag mechanism for false positives
- Notification system for high-risk content
- Machine learning-based risk assessment
- Multi-language support
- Severity levels for different word categories
- User role-based access control for admin features
- Audit log for all flagging actions
- Export functionality for compliance reporting

## Support

For issues or questions:
1. Check this documentation
2. Review test files for usage examples
3. See `notes/flagging.md` for implementation details
4. Submit issues to the project repository
