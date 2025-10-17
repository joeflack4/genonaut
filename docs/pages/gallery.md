# Gallery Page URL Query Parameters

The Gallery page supports URL query parameters that allow users to construct custom URLs for filtering and searching content. These parameters are reflected in the browser's address bar and can be shared or bookmarked.

## Available Query Parameters

### 1. Search Query (`search`)

Filter gallery items by text search across title and prompt fields.

**Parameter**: `search`
**Type**: String
**Example**: `http://localhost:5173/gallery?search=landscape`

**Description**: Searches through content item titles and generation prompts. Supports both word matching and literal phrase matching when enclosed in quotation marks.

**Examples**:
```
http://localhost:5173/gallery?search=sunset
http://localhost:5173/gallery?search=cyberpunk%20city
http://localhost:5173/gallery?search="exact%20phrase%20match"
```

### 2. Tag Filtering (`tags`)

Filter gallery items by specific tags. Multiple tags can be specified using comma-delimited tag names.

**Parameter**: `tags`
**Type**: Comma-delimited string of tag names
**Example**: `http://localhost:5173/gallery?tags=nature,landscape`

**Description**: Filters content to show only items that have all specified tags. Tags are specified by their names (not IDs) in a comma-delimited format.

**Examples**:
```
# Single tag
http://localhost:5173/gallery?tags=nature

# Multiple tags (AND logic - items must have all tags)
http://localhost:5173/gallery?tags=nature,landscape,sunset

# Combined with search
http://localhost:5173/gallery?search=forest&tags=nature,trees
```

### 3. Generation Source Filtering (`notGenSource`)

Exclude specific generation source types from the gallery view. By default, all source types are included (all toggles are ON). This parameter only specifies which toggles should be turned OFF.

**Parameter**: `notGenSource`
**Type**: Comma-delimited string
**Options**:
- `your-g` - Your gens (user-regular content)
- `your-ag` - Your auto-gens (user-auto content)
- `comm-g` - Community gens (community-regular content)
- `comm-ag` - Community auto-gens (community-auto content)

**Default Behavior**: If the parameter is absent or empty, all content source types are included (all toggles ON).

**Examples**:

```
# Exclude "Your gens" (show only auto-gens and community content)
http://localhost:5173/gallery?notGenSource=your-g

# Exclude multiple sources (show only community auto-gens)
http://localhost:5173/gallery?notGenSource=your-g,your-ag,comm-g

# Exclude all user content (show only community content)
http://localhost:5173/gallery?notGenSource=your-g,your-ag

# Combined with other filters
http://localhost:5173/gallery?search=landscape&tag=nature&notGenSource=your-g,comm-ag
```

**UI Representation**:
- When a source type ID appears in `notGenSource`, its corresponding toggle in the sidebar will be OFF
- When a source type ID is NOT in `notGenSource`, its toggle will be ON
- If the URL has no `notGenSource` parameter, all toggles are ON

## Complete Examples

### Example 1: Search with tag filtering
```
http://localhost:5173/gallery?search=mountain&tags=landscape,photography
```
Shows items with "mountain" in the title/prompt that have both the "landscape" and "photography" tags.

### Example 2: Exclude your personal content
```
http://localhost:5173/gallery?notGenSource=your-g,your-ag
```
Shows only community-generated content (both regular and auto-generated).

### Example 3: Search with source filtering
```
http://localhost:5173/gallery?search=cyberpunk&notGenSource=your-ag,comm-ag
```
Shows items containing "cyberpunk" but excludes all auto-generated content.

### Example 4: Combined filtering
```
http://localhost:5173/gallery?search=sunset&tags=nature,ocean&notGenSource=your-g,your-ag,comm-g
```
Shows only community auto-generated content with "sunset" in the title/prompt and tagged with both "nature" and "ocean".

## URL Parameter Synchronization

The Gallery page maintains bidirectional synchronization between:
1. **URL query parameters** - What appears in the browser address bar
2. **UI controls** - Search input, tag chips, and generation source toggles
3. **API requests** - The actual data fetched from the backend

### User Interactions:

**Toggling filters in the UI**:
- Turns a toggle OFF -> Adds its ID to `notGenSource` in the URL
- Turns a toggle ON -> Removes its ID from `notGenSource` in the URL
- If all toggles are ON -> `notGenSource` parameter is removed from URL

**Entering a URL directly**:
- URL with `notGenSource=your-g,comm-ag` -> "Your gens" and "Community auto-gens" toggles are OFF
- URL without `notGenSource` -> All toggles are ON
- Page loads with UI state matching the URL parameters

**Search and tags**:
- Submitting search -> Updates `search` parameter in URL
- Selecting/deselecting tags -> Updates `tags` parameter in URL with comma-delimited tag names
- Clearing search -> Removes `search` parameter from URL
- Clearing all tags -> Removes `tags` parameter from URL

## Technical Notes

### Parameter Encoding
- Spaces in search terms should be URL-encoded as `%20` or `+`
- Special characters in search terms should be properly URL-encoded
- Tag names with spaces or special characters should be URL-encoded in the `tags` parameter
- The `tags` and `notGenSource` parameters use comma (`,`) as a delimiter
- Example with spaces: `tags=mountain%20landscape,forest%20path` represents tags "mountain landscape" and "forest path"

### State Persistence
- URL parameters are the source of truth for filter state
- Browser back/forward navigation updates filters based on URL history
- Search history is saved separately in the database (not in URL)
- View mode (grid/list) and thumbnail resolution are saved to localStorage (not in URL)

### API Integration
The frontend transforms URL parameters into API request parameters:
- `notGenSource` values are converted to `contentSourceTypes` for the API
  - Example: `notGenSource=your-g` means exclude `user-regular` from `contentSourceTypes` array
  - The API receives only the enabled source types, not the disabled ones
- `tags` parameter (tag names) is converted to tag IDs for the API
  - The frontend maintains a mapping between tag names and tag IDs
  - Tag names from the URL are looked up to find their corresponding IDs
  - The API receives an array of tag IDs to filter by
