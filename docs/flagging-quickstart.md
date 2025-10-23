# Content Flagging System - Quick Start Guide

Get the content flagging system up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Project already set up with `make init`

## 1. Configure Flag Words (2 minutes)

Create your flag words list:

```bash
# Copy example file
cp docs/flag-words.txt.example flag-words.txt

# Edit to add your words
nano flag-words.txt
```

**Example flag-words.txt:**
```
# Violence & Weapons
violence
weapon
gun
combat

# Hate Speech
hatred
racist
slur

# Explicit Content
explicit
nude
sexual
```

**Important:** The `flag-words.txt` file is in `.gitignore` - never commit it!

## 2. Start Backend (1 minute)

```bash
# Start API server (development database)
make api-dev

# Or use test database
make api-test
```

**Verify it's running:**
```bash
curl http://localhost:8001/api/v1/health
# Should return: {"status":"healthy"}
```

## 3. Start Frontend (1 minute)

```bash
cd frontend
npm install  # First time only
npm run dev
```

**Access the UI:**
- Frontend: http://localhost:5173
- Admin Page: http://localhost:5173/admin/flagged-content

## 4. Test It Out (1 minute)

### Create Flagged Content via API

```bash
curl -X POST http://localhost:8001/api/v1/content \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Content",
    "content_type": "regular",
    "item_metadata": {
      "prompt": "A scene with violence and weapons"
    },
    "creator_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9"
  }'
```

### View Flagged Content

**Via API:**
```bash
curl http://localhost:8001/api/v1/admin/flagged-content/ | jq
```

**Via UI:**
1. Navigate to http://localhost:5173/admin/flagged-content
2. See your flagged content in the table!
3. Click the eye icon to view details
4. Try filtering, reviewing, or deleting

## 5. Key Features to Try

### Risk Scoring

Content is automatically scored 0-100:
- **0-25**: Low Risk (Green)
- **26-50**: Medium Risk (Yellow)
- **51-75**: High Risk (Orange)
- **76-100**: Critical Risk (Red)

### Filtering

Use the filter panel to find specific content:
- **Content Source**: Regular vs Auto-generated
- **Unreviewed Only**: Show only items needing review
- **Risk Score Range**: Filter by risk level
- **Sort Options**: Risk, date, or problem count

### Review Workflow

1. Click the checkmark icon on any item
2. Add review notes
3. Mark as reviewed
4. Item gets timestamped and marked complete

### Bulk Operations

1. Select multiple items with checkboxes
2. Click "Delete Selected"
3. Confirm bulk delete
4. All selected items removed at once

## Common Tasks

### Scan Existing Content

If you have existing content, scan it:

```bash
curl -X POST http://localhost:8001/api/v1/admin/flagged-content/scan \
  -H "Content-Type: application/json" \
  -d '{
    "content_types": ["regular", "auto"],
    "force_rescan": false
  }'
```

### Get Statistics

```bash
curl http://localhost:8001/api/v1/admin/flagged-content/statistics/summary | jq
```

Output:
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

### Filter High-Risk Items

```bash
# API
curl "http://localhost:8001/api/v1/admin/flagged-content/?min_risk_score=75" | jq

# UI
# 1. Open admin page
# 2. Set risk slider to 75-100
# 3. See only critical items
```

## Understanding Risk Scores

The risk score is calculated using:
- **40%**: Percentage of problematic words
- **30%**: Total count of problem words (capped at 10)
- **30%**: Diversity of unique problem words (capped at 5)

**Example:**
```
Text: "A violent scene with weapons and combat"
Problem words: ["violent", "weapons", "combat"]
Total words: 7
Calculation:
  - Percentage: (3/7) × 100 × 0.4 = 17.14
  - Count: (3/10) × 100 × 0.3 = 9.0
  - Diversity: (3/5) × 100 × 0.3 = 18.0
  - Total: 44.14 (Medium Risk)
```

## Automatic Flagging

Content is **automatically flagged** when created:

```python
# In your application code
response = requests.post('/api/v1/content', json={
    'title': 'My Content',
    'item_metadata': {'prompt': 'Some text here'},
    # ... other fields
})

# Flagging happens in background
# No need to call flagging API separately!
```

**Key Points:**
- ✅ Automatic - no extra code needed
- ✅ Non-blocking - content creation always succeeds
- ✅ Graceful - works even if flag-words.txt missing
- ✅ Fast - minimal performance impact

## Next Steps

### For Admins

1. **Configure Your Word List**
   - Add words specific to your use case
   - Update regularly based on content trends
   - Keep the list in a secure location

2. **Set Up Review Process**
   - Decide on review cadence (daily/weekly)
   - Assign reviewers
   - Document review criteria
   - Track review metrics

3. **Monitor Statistics**
   - Check dashboard regularly
   - Watch for trends in flagged content
   - Adjust word list as needed
   - Set thresholds for alerts

### For Developers

1. **API Integration**
   - See [API Documentation](./flagging.md#api-endpoints)
   - All endpoints documented with examples
   - OpenAPI/Swagger docs at http://localhost:8001/docs

2. **Testing**
   - See [Testing Guide](./flagging-testing.md)
   - Run unit tests: `pytest test/unit/test_flagging_engine.py`
   - Manual testing checklist provided

3. **Customization**
   - Risk calculation in `genonaut/utils/flagging.py`
   - Repository queries in `genonaut/api/repositories/flagged_content_repository.py`
   - Frontend components in `frontend/src/components/admin/`

## Troubleshooting

### "Flag words file not found"

```bash
# Ensure file exists in project root
ls flag-words.txt

# If not, create it
cp docs/flag-words.txt.example flag-words.txt
```

### "Content not being flagged"

1. Check flag-words.txt has content
2. Ensure words are lowercase
3. Verify content has matching words
4. Check logs for errors

### "Frontend not loading"

```bash
# Check backend is running
curl http://localhost:8001/api/v1/health

# Check frontend is running
curl http://localhost:5173

# Restart if needed
cd frontend && npm run dev
```

### "Database errors"

```bash
# Reinitialize database
make init-test

# Or for dev database
make init-dev
```

## Resources

- **Full Documentation**: [docs/flagging.md](./flagging.md)
- **API Reference**: http://localhost:8001/docs (when server running)
- **Testing Guide**: [docs/flagging-testing.md](./flagging-testing.md)
- **Implementation Spec**: [notes/flagging.md](../notes/issues/by_priority/low/flagging.md)

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `flag-words.txt` | Your word list (project root, not committed) |
| `docs/flag-words.txt.example` | Example template |
| `test/db/input/flag-words.txt` | Test fixture |

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/flagged-content/` | GET | List flagged items |
| `/admin/flagged-content/scan` | POST | Manual scan |
| `/admin/flagged-content/{id}` | GET | Get details |
| `/admin/flagged-content/{id}/review` | PUT | Review item |
| `/admin/flagged-content/{id}` | DELETE | Delete item |
| `/admin/flagged-content/bulk-delete` | POST | Bulk delete |
| `/admin/flagged-content/statistics/summary` | GET | Statistics |

### Key Commands

```bash
# Backend
make api-dev              # Start dev server
pytest test/unit -v       # Run unit tests
pytest test/db -v         # Run DB tests

# Frontend
cd frontend && npm run dev    # Start dev server
npm run type-check            # Check TypeScript
npm run lint                  # Check linting
npm run build                 # Build for production
```

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review [Testing Guide](./flagging-testing.md) for debugging steps
3. Check logs for error messages
4. Verify all prerequisites are met

---

**Ready to dive deeper?** Check out the [Full Documentation](./flagging.md) for:
- Detailed API documentation
- Risk calculation examples
- Advanced filtering options
- Production deployment guidance
- Best practices and recommendations
