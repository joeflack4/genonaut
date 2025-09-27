# Tag Hierarchy Frontend Documentation

This document covers the frontend implementation of the tag hierarchy feature in Genonaut.

## Overview

The tag hierarchy frontend provides an interactive tree view for exploring tag relationships and filtering content. Users can browse the hierarchical tag structure, search for specific tags, and click tags to filter gallery content.

## Components Architecture

### Core Components

#### `TagsPage.tsx`
Main page component located at `/tags` route.

**Features:**
- Displays hierarchy statistics (total tags, root categories, relationships)
- Toggle between tree view and search modes
- Refresh hierarchy data
- Help cards and hierarchy overview

**Props:** None (route-based component)

#### `TagTreeView.tsx`
Interactive tree view component using `react-accessible-treeview`.

**Features:**
- Hierarchical display with expand/collapse
- Click to navigate to gallery with tag filter
- Keyboard navigation support
- Loading and error states

**Props:**
```typescript
interface TagTreeViewProps {
  onNodeClick?: (nodeId: string, nodeName: string) => void;
  selectedNodeId?: string;
  showNodeCounts?: boolean;
  maxHeight?: number | string;
  className?: string;
}
```

#### `TagSearchFilter.tsx`
Search and filter component for finding tags.

**Features:**
- Real-time search with highlighting
- Breadcrumb display for tag context
- Result limiting and pagination
- Tag selection with callbacks

**Props:**
```typescript
interface TagSearchFilterProps {
  onTagSelect?: (nodeId: string, nodeName: string) => void;
  selectedTags?: string[];
  placeholder?: string;
  showBreadcrumbs?: boolean;
  maxResults?: number;
}
```

### Data Management

#### `useTagHierarchy.ts`
React Query-based hooks for data fetching and state management.

**Available Hooks:**
- `useTagHierarchy()` - Fetch complete hierarchy
- `useTagHierarchyTree()` - Get tree structure
- `useTagSearch(query)` - Search functionality
- `useTagBreadcrumbs(nodeId)` - Get node path
- `useRefreshHierarchy()` - Cache invalidation

#### `tag-hierarchy-service.ts`
Service layer for API communication and data transformation.

**Key Methods:**
- `getHierarchy()` - Fetch hierarchy data
- `convertToTree()` - Transform flat data to tree
- `searchNodes()` - Filter nodes by query
- `getBreadcrumbs()` - Get parent path

## Integration with Gallery

### Tag Filtering Flow

1. User clicks tag in tree view
2. Navigate to `/gallery?tag={tagId}`
3. Gallery page reads tag parameter
4. Filter content by selected tag
5. Display filter chip with clear option

### URL Structure
```
/gallery?tag=abstract
/gallery?tag=digital_techniques&search=portrait
```

### Gallery Integration Code
```typescript
// GalleryPage.tsx updates
const [searchParams] = useSearchParams();
const tagFilter = searchParams.get('tag');

// API call includes tag filter
const { data } = useGalleryList({
  ...otherParams,
  tag: tagFilter
});
```

## Styling and Theming

### MUI Integration
- Uses Material-UI components for consistent design
- Integrates with existing theme system
- Responsive design with breakpoints

### Tree Styling
```typescript
// Custom styling for react-accessible-treeview
const TreeView = styled('ul')(({ theme }) => ({
  '& .tree-node': {
    padding: theme.spacing(1),
    borderRadius: theme.shape.borderRadius,
    '&:hover': {
      backgroundColor: theme.palette.action.hover,
    },
  },
}));
```

## Performance Considerations

### Optimization Strategies
- React Query caching with 5-minute stale time
- Flat array data structure for fast processing
- Virtual scrolling for large hierarchies (if needed)
- Debounced search to reduce API calls

### Bundle Impact
- `react-accessible-treeview`: ~15KB gzipped
- Additional tree components: ~10KB
- Total feature impact: ~25KB

## Testing Strategy

### Unit Tests
- Component rendering and interactions
- Hook behavior and state management
- Service layer data transformations
- Search and filtering logic

### Integration Tests
- API data fetching and caching
- Navigation and URL parameter handling
- Gallery integration workflow

### E2E Tests
- Complete user journey from tag selection to content filtering
- Accessibility testing with screen readers
- Cross-browser compatibility

## Accessibility Features

### WCAG 2.1 Compliance
- Screen reader support via `react-accessible-treeview`
- Keyboard navigation (Tab, Arrow keys, Enter, Space)
- Focus management and visual indicators
- High contrast mode support

### Keyboard Shortcuts
- **Tab/Shift+Tab**: Navigate between interactive elements
- **Arrow Keys**: Move through tree nodes
- **Enter/Space**: Expand/collapse or select nodes
- **Escape**: Close search results

## API Endpoints

### Primary Endpoint
```
GET /api/v1/tags/hierarchy
```

**Response:**
```json
{
  "nodes": [
    { "id": "art_movements", "name": "Art Movements", "parent": null },
    { "id": "abstract", "name": "Abstract", "parent": "art_movements" }
  ],
  "metadata": {
    "totalNodes": 127,
    "totalRelationships": 123,
    "rootCategories": 4,
    "lastUpdated": "2024-09-27T07:13:30.633Z",
    "format": "flat_array",
    "version": "1.0"
  }
}
```

### Additional Endpoints
- `GET /api/v1/tags/hierarchy/nodes/{nodeId}` - Get specific node
- `GET /api/v1/tags/hierarchy/children/{parentId}` - Get direct children
- `GET /api/v1/tags/hierarchy/roots` - Get root nodes only
- `POST /api/v1/tags/hierarchy/refresh` - Refresh cache

## Error Handling

### Common Error States
- **Network errors**: Show retry button with error message
- **Empty hierarchy**: Display helpful message about data loading
- **Search no results**: Show "No tags found" with search term
- **Loading failures**: Fallback to cached data if available

### Error Boundaries
```typescript
<ErrorBoundary fallback={<TagHierarchyErrorFallback />}>
  <TagTreeView />
</ErrorBoundary>
```

## Development Guidelines

### Adding New Features
1. Update TypeScript interfaces in service layer
2. Add corresponding React Query hooks
3. Create/update UI components
4. Add comprehensive tests
5. Update documentation

### Code Style
- Use TypeScript with strict mode
- Follow existing MUI patterns
- Implement proper error boundaries
- Add accessibility attributes
- Write descriptive test names

## Troubleshooting

### Common Issues

**Tree not loading:**
- Check network tab for API errors
- Verify hierarchy.json file exists
- Check React Query devtools for cache state

**Search not working:**
- Ensure search query is properly debounced
- Check filter logic in service layer
- Verify search results rendering

**Navigation issues:**
- Check React Router configuration
- Verify URL parameter handling
- Test with browser navigation

### Debug Commands
```bash
# Regenerate hierarchy data
make ontology-json

# Run frontend tests
npm test -- --run src/components/tags/

# Check TypeScript errors
npm run type-check
```

## Future Enhancements

### Planned Features
- [ ] Advanced search with filters
- [ ] Tag usage statistics
- [ ] Bulk tag operations
- [ ] Real-time collaboration features
- [ ] Mobile gesture support

### Performance Improvements
- [ ] Virtual scrolling for very large trees
- [ ] Progressive loading of tree branches
- [ ] Background cache warming
- [ ] Service worker caching

---

For backend tag ontology documentation, see [tag_ontology.md](../tag_ontology.md).