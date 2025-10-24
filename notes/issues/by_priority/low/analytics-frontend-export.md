# Analytics Data Export - Future Enhancement

## Overview
Add data export functionality to the Analytics page, allowing users to download analytics data in CSV and JSON formats for external analysis, reporting, or archival purposes.

## User Story
As a system administrator or developer, I want to export analytics data (route performance, generation stats, tag cardinality) in machine-readable formats, so that I can analyze the data in external tools, create custom reports, or archive historical data.

## Current State
The Analytics page displays data in tables and charts but does not provide any download or export functionality. Users can only view data in the browser.

## Proposed Enhancement

### Export Options

**Three export scopes:**
1. **Section Export** - Export data from a single section (Route Analytics, Generation Analytics, or Tag Cardinality)
2. **Page Export** - Export all data from the entire Analytics page
3. **Filtered Export** - Export respects current filters (time range, system type, etc.)

**Two export formats:**
1. **CSV** - For spreadsheet applications (Excel, Google Sheets)
2. **JSON** - For programmatic analysis (Python, R, custom scripts)

### UI Design

**Section-Level Export Buttons:**
- Each analytics card (Route Analytics, Generation Analytics, Tag Cardinality) gets an export button
- Button location: Top-right corner of card, next to refresh button
- Icon: DownloadIcon from Material UI
- Dropdown menu on click:
  - "Export as CSV"
  - "Export as JSON"
- Visual feedback: Downloading spinner while preparing file

**Page-Level Export Button:**
- Located in page header, next to global refresh button
- Text: "Export All Data"
- Opens dialog with options:
  - Format: CSV or JSON
  - Sections: Checkboxes for each section
  - Filename preview
  - "Download" button

**Export Progress Indicator:**
- Show toast notification: "Preparing export..."
- On completion: "Downloaded [filename]"
- On error: "Export failed - [error message]"

### Export Specifications

#### Route Analytics Export

**CSV Format:**
```csv
Rank,Method,Route,Query Params,Avg Req/Hr,P95 Latency (ms),P99 Latency (ms),Unique Users,Priority Score,Success Rate,Total Requests
1,GET,/api/v1/content/unified,"{""page_size"": ""10""}",2450,189,245,45,24559.4,98.5%,411600
2,GET,/api/v1/tags/hierarchy,{},890,156,198,32,9076.2,99.1%,149520
...
```

**JSON Format:**
```json
{
  "export_type": "route_analytics",
  "exported_at": "2025-10-23T14:30:00Z",
  "filters": {
    "system": "absolute",
    "lookback_days": 7,
    "top_n": 10
  },
  "data": [
    {
      "rank": 1,
      "method": "GET",
      "route": "/api/v1/content/unified",
      "query_params_normalized": {"page_size": "10"},
      "avg_hourly_requests": 2450.0,
      "avg_p95_latency_ms": 189.0,
      "avg_p99_latency_ms": 245.0,
      "avg_unique_users": 45.0,
      "cache_priority_score": 24559.4,
      "success_rate": 0.985,
      "total_requests": 411600
    }
    // ... more routes
  ]
}
```

#### Generation Analytics Export

**CSV Format:**
```csv
Metric,Value
Total Generations,15234
Successful Generations,14123
Failed Generations,1089
Cancelled Generations,22
Success Rate,92.7%
Avg Duration (s),42.5
P95 Duration (s),55.0
P99 Duration (s),62.0
Active Users (24h),127
Avg Queue Length,4.5
```

**Time-Series Data (separate CSV):**
```csv
Timestamp,Total Generations,Successful,Failed,Cancelled,Avg Duration (s)
2025-10-23 00:00,145,132,10,3,42.5
2025-10-23 01:00,98,89,8,1,41.2
...
```

**JSON Format:**
```json
{
  "export_type": "generation_analytics",
  "exported_at": "2025-10-23T14:30:00Z",
  "filters": {
    "time_range_days": 7
  },
  "summary": {
    "total_generations": 15234,
    "successful_generations": 14123,
    "failed_generations": 1089,
    "cancelled_generations": 22,
    "success_rate": 0.927,
    "avg_duration_seconds": 42.5,
    "p95_duration_seconds": 55.0,
    "p99_duration_seconds": 62.0,
    "active_users_24h": 127,
    "avg_queue_length": 4.5
  },
  "time_series": [
    {
      "timestamp": "2025-10-23T00:00:00Z",
      "total_generations": 145,
      "successful": 132,
      "failed": 10,
      "cancelled": 3,
      "avg_duration_seconds": 42.5
    }
    // ... hourly data
  ]
}
```

#### Tag Cardinality Export

**CSV Format:**
```csv
Rank,Tag ID,Tag Name,Cardinality,Percentage,Content Source
1,uuid-1,character,1247,12.3%,all
2,uuid-2,landscape,892,8.8%,all
3,uuid-3,portrait,654,6.5%,all
...
```

**Histogram Data (separate CSV):**
```csv
Bucket,Min,Max,Tag Count
1,1,1,1523
2-5,2,5,742
6-10,6,10,345
11-25,11,25,198
26-50,26,50,87
51-100,51,100,42
101-250,101,250,18
251-500,251,500,7
501-1000,501,1000,3
1000+,1001,9999,1
```

**JSON Format:**
```json
{
  "export_type": "tag_cardinality",
  "exported_at": "2025-10-23T14:30:00Z",
  "filters": {
    "content_source": "all",
    "min_cardinality": 1
  },
  "statistics": {
    "total_tags": 2966,
    "tags_with_content": 2966,
    "most_popular_tag": {
      "id": "uuid-1",
      "name": "character",
      "cardinality": 1247
    },
    "median_cardinality": 8,
    "p90_cardinality": 67
  },
  "popular_tags": [
    {
      "rank": 1,
      "id": "uuid-1",
      "name": "character",
      "cardinality": 1247,
      "percentage": 12.3,
      "content_source": "all"
    }
    // ... top tags
  ],
  "histogram": [
    {
      "bucket": "1",
      "min_cardinality": 1,
      "max_cardinality": 1,
      "tag_count": 1523
    }
    // ... other buckets
  ]
}
```

### Technical Implementation

**Frontend Implementation:**

```typescript
// Utility function to convert data to CSV
function convertToCSV(data: any[], headers: string[]): string {
  const csvRows = [];
  csvRows.push(headers.join(','));

  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header];
      // Escape quotes and commas
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    });
    csvRows.push(values.join(','));
  }

  return csvRows.join('\n');
}

// Utility function to trigger download
function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// Export hook
function useExportData() {
  const exportAsCSV = (data: any[], headers: string[], filename: string) => {
    const csv = convertToCSV(data, headers);
    downloadFile(csv, filename, 'text/csv;charset=utf-8;');
  };

  const exportAsJSON = (data: any, filename: string) => {
    const json = JSON.stringify(data, null, 2);
    downloadFile(json, filename, 'application/json;charset=utf-8;');
  };

  return { exportAsCSV, exportAsJSON };
}
```

**Component Structure:**
- `ExportButton` - Reusable button with dropdown menu
- `ExportDialog` - Dialog for page-level export with options
- `useExportData` - Hook for export functionality
- Toast notifications for status updates

**Filename Convention:**
- Pattern: `genonaut-[section]-[date]-[time].[ext]`
- Examples:
  - `genonaut-route-analytics-2025-10-23-1430.csv`
  - `genonaut-generation-analytics-2025-10-23-1430.json`
  - `genonaut-tag-cardinality-2025-10-23-1430.csv`
  - `genonaut-all-analytics-2025-10-23-1430.json`

### Data Preparation

**Client-Side Processing:**
- Format numbers (commas for thousands, 2 decimals for percentages)
- Convert timestamps to ISO 8601 format
- Flatten nested objects for CSV
- Include metadata (export timestamp, filters applied)

**Performance Considerations:**
- For large datasets (1000+ rows), show progress indicator
- Consider using Web Workers for CSV conversion (if slow)
- Limit JSON exports to reasonable size (10MB max)
- For very large exports, consider backend generation

### Accessibility
- Export button has clear ARIA label: "Export data"
- Keyboard accessible (Tab, Enter)
- Toast notifications are announced to screen readers
- Dialog has proper ARIA roles and labels

### Testing Requirements
- Unit test: CSV conversion produces correct format
- Unit test: JSON export includes all expected fields
- Unit test: Filename generation follows convention
- Unit test: Download trigger works
- Integration test: Export respects current filters
- E2E test: Click export button -> file downloads
- Test with empty data (should handle gracefully)
- Test with special characters (quotes, commas in data)

### Error Handling
- If no data to export, show message: "No data to export"
- If export fails, show error toast with retry option
- If data is too large, warn user and suggest filtering
- Validate data before export (check for required fields)

### User Preferences
Store in localStorage:
- Preferred export format (CSV or JSON)
- Default filename pattern
- Auto-include filters in export metadata

### Backend Support (Optional)

For very large exports, consider backend endpoint:
```
GET /api/v1/analytics/export?section=routes&format=csv&lookback_days=30
```

**Benefits:**
- Can handle larger datasets
- Can schedule/automate exports
- Can email export link
- Server can optimize query performance

**Implementation:**
- Generate file on server
- Return download URL or stream file
- Clean up file after 1 hour
- Rate limit to prevent abuse

### Dependencies
- File-saver library (optional, can use native browser APIs)
- Papa Parse library (optional, for robust CSV generation)
- Existing analytics data fetching hooks

### Success Metrics
- Export completes within 2 seconds for typical datasets
- CSV files open correctly in Excel and Google Sheets
- JSON files are valid and parse correctly
- Zero data loss or corruption in exports
- Works in all major browsers
- Mobile-friendly (downloads work on iOS/Android)

### Future Enhancements (beyond this task)
- Export charts as images (PNG, SVG)
- Schedule recurring exports (daily, weekly)
- Email export to user
- Export to cloud storage (Google Drive, Dropbox)
- Custom column selection for CSV exports
- Export templates (saved filter combinations)
- Bulk export (all historical data)

### Estimated Effort
- Frontend export utilities: 3-4 hours
- Section-level export buttons: 2-3 hours
- Page-level export dialog: 3-4 hours
- Data formatting and validation: 2-3 hours
- Testing (unit + E2E): 2-3 hours
- Polish and error handling: 1-2 hours
- **Total: 13-19 hours**

### Priority
**Medium** - Useful feature for power users and administrators but not critical for initial Analytics page launch. Can be added in a subsequent iteration.
