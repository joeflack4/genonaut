# Tag Ontology Frontend - Planning Document

## Overview

This document outlines the development of a frontend interface for displaying and exploring the tag ontology system in Genonaut. The feature will provide users with an interactive tree view to browse hierarchical tag relationships, enabling better content discovery and understanding of the tag classification system.

## Motivation

With the completed tag ontology backend system containing 129 parent-child relationships across 123 unique tags organized into hierarchical categories, users need an intuitive way to:

1. **Explore tag relationships** - Browse parent-child hierarchies visually
2. **Discover related content** - Navigate through semantic tag connections
3. **Understand tag structure** - See how tags are organized into categories
4. **Filter and search** - Find specific tags within the hierarchy
5. **Enhance content tagging** - Use the hierarchy to improve tag selection when creating content

## Technical Approach

### Frontend Architecture
- **Page**: New `/tags` route displaying the tag hierarchy
- **Component Library**: MUI X Tree View (aligns with existing MUI usage)
- **Data Format**: JSON representation of TSV hierarchy
- **API Integration**: New backend endpoint serving tree data
- **State Management**: React Query for caching and data fetching

### Data Flow
1. **Backend**: Convert TSV hierarchy to JSON format
2. **API**: Serve structured tree data via REST endpoint
3. **Frontend**: Fetch and render interactive tree view
4. **User Interaction**: Expand/collapse nodes, search, filter

## Library Selection: React-Accessible-Treeview ✅

Based on user decision and research of React tree view libraries for 2024, **react-accessible-treeview** is the chosen solution because:

### ✅ Advantages
- **Cost**: MIT licensed, completely free for commercial use
- **Accessibility**: WCAG 2.1 compliant, excellent screen reader support
- **Lightweight**: Smaller bundle size compared to MUI X
- **Customizable**: Can be styled with MUI theme system
- **Keyboard Navigation**: Full keyboard support built-in
- **Performance**: Good performance for moderate-sized trees

### 📊 Integration Strategy
- Use react-accessible-treeview for core functionality
- Style with MUI theme system for consistency
- Wrap in MUI containers and components
- Add MUI icons for expand/collapse

### 🎨 Styling Approach
- Apply MUI theme colors and typography
- Use MUI Paper/Card components as containers
- Integrate MUI icons (ExpandMore, ChevronRight)
- Maintain Material Design visual hierarchy

## Data Structure & API Design

### Current TSV Format
```tsv
parent	child
art_movements	abstract
art_movements	decorative
artistic_medium	digital_techniques
```

### Proposed JSON Format (Flat Array - Most Performant) ✅
For optimal performance with large datasets, using flat array with parent references:

```json
{
  "nodes": [
    { "id": "art_movements", "name": "Art Movements", "parent": null },
    { "id": "abstract", "name": "Abstract", "parent": "art_movements" },
    { "id": "decorative", "name": "Decorative", "parent": "art_movements" },
    { "id": "artistic_medium", "name": "Artistic Medium", "parent": null },
    { "id": "digital_techniques", "name": "Digital Techniques", "parent": "artistic_medium" }
  ],
  "metadata": {
    "totalNodes": 123,
    "totalRelationships": 129,
    "lastUpdated": "2024-09-27T01:39:00Z"
  }
}
```

**Performance Benefits:**
- Faster JSON parsing (no deep nesting)
- Lower memory usage
- Easier to search and filter
- Compatible with react-accessible-treeview format

### API Endpoint Design
```
GET /api/v1/tags/hierarchy
```

**Response:**
- **200**: JSON tree structure
- **304**: Not modified (with ETag caching)
- **500**: Server error

**Query Parameters:**
- `format=json` (default) | `tsv` | `flat`
- `depth=3` (limit tree depth)
- `expand_all=false` (return fully expanded tree)

## Directory Structure

### Backend Addition
```
genonaut/api/endpoints/
├── tags/
│   ├── __init__.py
│   ├── hierarchy.py          # New hierarchy endpoint
│   └── models.py            # Pydantic models for tree data

genonaut/ontologies/tags/
├── scripts/
│   └── generate_json.py     # New TSV-to-JSON converter
└── data/
    └── hierarchy.json       # Generated JSON file
```

### Frontend Addition
```
frontend/src/
├── pages/
│   └── tags/
│       ├── TagsPage.tsx           # Main page
│       ├── index.ts
│       └── __tests__/
│           └── TagsPage.test.tsx
├── components/
│   └── tags/
│       ├── TagTreeView.tsx        # Tree component
│       ├── TagSearchFilter.tsx    # Search/filter
│       ├── TagNodeActions.tsx     # Node interactions
│       ├── TagStats.tsx           # Statistics display
│       ├── index.ts
│       └── __tests__/
│           ├── TagTreeView.test.tsx
│           └── TagSearchFilter.test.tsx
├── services/
│   └── tag-hierarchy-service.ts   # API client
└── hooks/
    ├── useTagHierarchy.ts         # Data fetching hook
    └── useTagSearch.ts            # Search functionality hook
```

## User Experience Design

### Page Layout
```
┌─────────────────────────────────────────────────┐
│ Tag Hierarchy                                   │
├─────────────────────────────────────────────────┤
│ [Search Box] [Filter Options] [Stats: 123 tags]│
├─────────────────────────────────────────────────┤
│ ▶ Art Movements (4)                            │
│ ▼ Artistic Medium (8)                          │
│   ▶ Artistic Methods (5)                       │
│   ▶ Digital Techniques (2)                     │
│   ▶ Traditional Materials (1)                  │
│ ▶ Camera Angles (4)                            │
│ ▶ Cinematic Style (2)                          │
│ ▶ Color Properties (3)                         │
│ ...                                             │
└─────────────────────────────────────────────────┘
```

### Key Features
- **Expand/Collapse**: Click nodes to reveal children
- **Search**: Filter tree by tag names
- **Statistics**: Show tag counts per category
- **Breadcrumbs**: Show current selection path
- **Context Menu**: Right-click for tag actions

## Performance Considerations

### Optimization Strategies
- **Lazy Loading**: Load tree nodes on demand
- **Virtualization**: Render only visible nodes for large trees
- **Caching**: Cache tree data with React Query
- **Debounced Search**: Prevent excessive filtering
- **Memoization**: Optimize re-renders with React.memo

### Expected Performance
- **Initial Load**: < 1 second for full hierarchy
- **Search Response**: < 200ms for filter operations
- **Memory Usage**: < 10MB for tree state
- **Bundle Size**: +50KB for MUI X Tree View

## Questions & Decisions Required

### 1. MUI X Licensing 🔍
**Question**: Do we have MUI X Pro/Premium license for commercial use?
**Options**:
- A) Purchase MUI X license (~$15/dev/month)
- B) Use react-accessible-treeview (free, MIT)
- C) Build custom tree with MUI Core components
A: Let's start with B.

### 2. Data Format Preference 📊
**Question**: Preferred JSON structure for tree data?
**Options**:
- A) Nested children format (proposed above)
- B) Flat array with parent references
- C) Mixed approach with both formats
A: Whichever is the most performant. I will let you decide.

### 3. Integration with Existing Content 🔗
**Question**: Should tree nodes link to content search results?
**Scope**:
- A) Click tag node → search for content with that tag
- B) Show content count per tag in tree
- C) Enable multi-tag selection for search
A: Do option A! You should create a plan for this with its own set of checkboxes in this markdown document, as well as tests.

### 4. Real-time Updates 🔄
**Question**: How should hierarchy updates be handled?
**Options**:
- A) Static data (refresh on page reload)
- B) Polling for updates every N minutes
- C) WebSocket real-time updates
A: Option A.

### 5. Mobile Experience 📱
**Question**: Mobile-specific tree interaction patterns?
**Considerations**:
- Touch-friendly expand/collapse
- Horizontal scrolling for deep trees
- Simplified search interface
A: Create a plan for this, with its own section and set of checkboxes. But annotate that section with @skipped-until-TBD. Basically I don't want to do it now, but I would like to see some ideas.

## Content Search Integration Plan ✅

### User Experience Flow
1. User browses tag hierarchy on `/tags` page
2. User clicks on any tag node in the tree
3. Application navigates to gallery/search page with tag filter applied
4. Search results show all content items tagged with selected tag

### Technical Implementation

#### URL Structure
```
/gallery?tag=abstract
/gallery?tag=digital_techniques&search=portrait
```

#### API Integration
```typescript
// Update existing gallery service
const fetchGalleryItems = (params: {
  page?: number;
  search?: string;
  tag?: string; // New parameter
}) => {
  // Implementation
}
```

#### Component Updates
- `TagTreeView.tsx`: Add node click handlers
- `GalleryPage.tsx`: Accept and handle tag filters
- `SearchFilters.tsx`: Display active tag filter
