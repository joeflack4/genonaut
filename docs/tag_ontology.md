# Tag Ontology Documentation

This document provides comprehensive information about Genonaut's tag ontology system, which organizes content tags into a hierarchical structure for improved search, discovery, and content organization.

## Overview

The tag ontology creates semantic relationships between tags used throughout the Genonaut system. Tags are organized in a monohierarchy using `rdfs:subClassOf` relationships, enabling:

- **Hierarchical browsing** - Navigate content through tag categories
- **Semantic search** - Find content using parent/child tag relationships
- **Enhanced recommendations** - Suggest content based on tag hierarchy
- **SPARQL queries** - Query the ontology using semantic web standards
- **Automatic tag suggestions** - Propose related tags during content creation

## Architecture

### Data Flow

```
Database (tags) → query_tags.py → Analysis → generate_hierarchy.py → TSV → JSON → Frontend
                                     ↓                                    ↓
                              Makefile Goals ← Manual Curation          API Server
```

### File Structure

```
genonaut/ontologies/tags/
├── scripts/           # Automation scripts
│   ├── generate_json.py      # TSV to JSON conversion
│   └── query_tags.py         # Database extraction
├── data/             # Generated data files
│   ├── hierarchy.tsv         # Source hierarchy data
│   └── hierarchy.json        # Frontend-ready JSON
├── queries/          # Example SPARQL queries
└── README.md         # Implementation documentation
```

### Database Integration

Tags are stored as JSON arrays in:
- `ContentItem.tags` - Manual content tags
- `ContentItemAuto.tags` - Automatically generated content tags

## Usage

### Basic Operations

```bash
# Extract latest tags from database
make ontology-refresh

# Generate hierarchy from analysis
make ontology-generate

# Validate hierarchy consistency
make ontology-validate

# Show ontology statistics
make ontology-stats
```

### Manual Curation

Edit `genonaut/ontologies/tags/data/hierarchy.tsv` directly:

```tsv
parent	child
software_category	api
software_category	test
test	integration
```

**Rules:**
- Tab-separated format
- Each child has exactly one parent (monohierarchy)
- Root categories have no parent entry
- Use lowercase, consistent naming

### Validation

The validation system checks for:
- **Format consistency** - Proper TSV structure
- **Duplicate relationships** - No repeated parent-child pairs
- **Potential cycles** - Warns if tags are both parents and children
- **Orphaned tags** - Tags without relationships

## Current Ontology

Based on 101 diverse visual/artistic tags from the demo database, the ontology includes 4 major root categories under `owl:Thing`:

### Visual Properties
Characteristics of visual appearance and aesthetics:
- **Color Properties**: bright, colorful, cool, dark, monochrome, neon, pastel, vibrant, warm
- **Lighting Effects**: atmospheric, glitch, hard-light, hdr, soft-light
- **Mood & Atmosphere**: dreamy, ethereal, gritty, moody, mystical, surreal
- **Visual Style**: elegant, futuristic, gothic, minimalism, modern, ornate, vintage

### Technical Aspects
Technical and compositional elements:
- **Composition & Viewpoint**: bird's-eye, close-up, fisheye, isometric, macro, panoramic
- **Rendering Technique**: cel-shaded, digital-painting, hand-drawn, painterly, photorealistic
- **Resolution & Quality**: 4k, 8k, high-detail, low-poly

### Artistic Medium
Materials and techniques used:
- **Medium & Material**: acrylic, chalk, charcoal, crayon, oil-painting, marker
- **Artistic Technique**: collage, concept-art, line-art, mixed-media, pixel-art, vector

### Content Classification
Content types and artistic movements:
- **Art Movement**: abstract, decorative, experimental, realistic
- **Content Genre**: action, anime, fantasy, horror, sci-fi, sculpture, still-life
- **Dimensional Properties**: 2d, 3d, flat, voxel

The hierarchy contains 134 parent-child relationships covering all 101 tags with no orphaned terms.

## Development Workflow

### Adding New Tags

1. **Automatic detection**: New tags appear when running `ontology-refresh`
2. **Manual classification**: Edit `hierarchy.tsv` to add relationships
3. **Validation**: Run `ontology-validate` to check consistency
4. **Documentation**: Update this file for significant changes

### Refreshing from Database

```bash
# Complete refresh workflow
make ontology-refresh    # Extract from database
make ontology-generate   # Regenerate hierarchy
make ontology-validate   # Check consistency
make ontology-stats      # Review results
```

### Quality Assurance

- **Regular validation** - Run validation after any manual changes
- **Frequency analysis** - Consider tag usage when creating hierarchies
- **Logical consistency** - Ensure parent-child relationships make semantic sense
- **Documentation** - Keep examples and guides current

## Future Development

### OWL Conversion

The TSV format will be converted to OWL for full semantic web support, with all categories ultimately deriving from `owl:Thing`:

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix genonaut: <http://genonaut.ai/ontology/tags#> .

# Root categories under owl:Thing
genonaut:visual_properties rdfs:subClassOf owl:Thing .
genonaut:technical_aspects rdfs:subClassOf owl:Thing .
genonaut:artistic_medium rdfs:subClassOf owl:Thing .
genonaut:content_classification rdfs:subClassOf owl:Thing .

# Intermediate categories
genonaut:color_properties rdfs:subClassOf genonaut:visual_properties .
genonaut:artistic_technique rdfs:subClassOf genonaut:artistic_medium .

# Leaf tags
genonaut:vibrant rdfs:subClassOf genonaut:color_properties .
genonaut:pixel-art rdfs:subClassOf genonaut:artistic_technique .
```

### SPARQL Integration

Example queries for the OWL version:

```sparql
# Find all subtypes of a category
SELECT ?subtype WHERE {
  ?subtype rdfs:subClassOf* genonaut:test .
}

# Find content with hierarchically related tags
SELECT ?content WHERE {
  ?content genonaut:hasTag ?tag .
  ?tag rdfs:subClassOf* genonaut:software_category .
}
```

### System Integration

- **Search enhancement** - Use hierarchy for query expansion
- **Recommendation engine** - Score content based on tag relationships
- **Content management** - Suggest related tags during creation
- **Analytics** - Generate reports based on tag categories

## Best Practices

### Hierarchy Design

1. **Logical relationships** - Use true is-a relationships (not just related-to)
2. **Appropriate depth** - Balance specificity with usability (typically 2-4 levels)
3. **Consistent granularity** - Similar level of detail within each branch
4. **Stable foundations** - Avoid frequent changes to root categories

### Tag Normalization

- **Lowercase** - Store all tags in lowercase for consistency
- **Underscore separation** - Use underscores for compound terms (e.g., `black_cat`)
- **Singular forms** - Prefer singular over plural (e.g., `cat` not `cats`)
- **No special characters** - Avoid punctuation except underscores

### Maintenance

- **Regular reviews** - Periodically audit the hierarchy for completeness
- **Usage monitoring** - Track which tags/categories are most used
- **Performance testing** - Ensure queries remain efficient as hierarchy grows
- **Backup procedures** - Version control changes to hierarchy files

## Integration Points

### Database Schema

The ontology integrates with these database columns:
- `content_items.tags` (JSONB array)
- `content_items_auto.tags` (JSONB array)
- `content_items.item_metadata` (for future tag metadata)

### API Endpoints

Future API integration will support:
- Tag hierarchy browsing
- Hierarchical tag search
- Tag suggestion based on hierarchy
- Ontology statistics and reporting

### Frontend Integration

The hierarchy will enable:
- Hierarchical tag browser components
- Auto-complete with related tag suggestions
- Category-based content filtering
- Visual ontology exploration tools

## Troubleshooting

### Common Issues

**Tags not appearing after refresh:**
- Verify database connection in `env/.env`
- Check that content items have non-empty tags arrays
- Ensure proper environment variables are loaded

**Validation errors:**
- Fix TSV format issues (ensure tab separation)
- Remove duplicate relationships
- Check for circular dependencies

**Performance issues:**
- Consider tag frequency when designing hierarchy
- Limit hierarchy depth for large tag sets
- Use appropriate indexes for tag queries

### Debug Commands

```bash
# Check current database tags
cd genonaut/ontologies/tags/scripts
set -a && source ../../../../env/.env && python query_tags.py

# Manual validation
cd genonaut/ontologies/tags/scripts
python generate_hierarchy.py

# Check file formats
head -5 ../data/hierarchy.tsv
wc -l ../data/hierarchy.tsv
```

## Frontend Integration

The tag hierarchy is now accessible through an interactive web interface that allows users to browse, search, and filter content by tags.

### Features

- **Interactive Tree View**: Browse hierarchical tag relationships with expand/collapse
- **Real-time Search**: Find tags quickly with search highlighting and filtering
- **Content Integration**: Click tags to filter gallery content automatically
- **Statistics Display**: View hierarchy metadata (total tags, relationships, categories)
- **Responsive Design**: Works on desktop and mobile devices
- **Accessibility**: Full keyboard navigation and screen reader support

### Access Points

- **Main Interface**: Navigate to `/tags` in the web application
- **Gallery Integration**: Tags can be selected from hierarchy to filter content
- **URL Direct Access**: Direct links like `/gallery?tag=abstract` work from bookmarks

### Technical Implementation

- **Frontend Framework**: React with Material-UI components
- **Tree Library**: react-accessible-treeview for WCAG compliance
- **Data Format**: JSON conversion from TSV for optimal performance
- **API Endpoints**: RESTful hierarchy endpoints with caching
- **State Management**: React Query for efficient data fetching

### API Endpoints

```bash
# Get complete hierarchy
GET /api/v1/tags/hierarchy

# Refresh hierarchy cache
POST /api/v1/tags/hierarchy/refresh

# Get specific nodes
GET /api/v1/tags/hierarchy/nodes/{nodeId}
```

For detailed frontend documentation, see [Tag Hierarchy UI Documentation](./frontend/tag_hierarchy_ui.md).

## Support

For questions or issues with the tag ontology:

1. **Check this documentation** for usage patterns and troubleshooting
2. **Review the planning document** at `notes/tag-ontology.md` for design rationale
3. **Examine the implementation** in `genonaut/ontologies/tags/README.md`
4. **Test with validation tools** to identify specific issues
5. **Consult database documentation** for underlying data structure questions

## Related Documentation

- [Database Documentation](./db.md) - Understanding tag storage and indexing
- [API Documentation](./api.md) - Current and future API integration
- [Testing Documentation](./testing.md) - Testing strategies for ontology features
- [Planning Document](../notes/tag-ontology.md) - Original design and specifications