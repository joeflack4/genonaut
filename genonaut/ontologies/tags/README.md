# Tag Ontology

This directory contains the tag ontology for Genonaut, which provides a hierarchical classification of all tags used in the system.

## Overview

The tag ontology organizes content tags into a hierarchical structure using `rdfs:subClassOf` relationships. This enables:

- **Semantic search**: Find content through hierarchical tag relationships
- **Content organization**: Group related content automatically
- **Recommendation enhancement**: Suggest content based on tag relationships
- **SPARQL queries**: Query the ontology using standard semantic web tools

## Directory Structure

```
genonaut/ontologies/tags/
├── scripts/
│   ├── query_tags.py           # Extract tags from database
│   ├── generate_hierarchy.py   # Create hierarchical relationships
│   └── validate_ontology.py    # Validate consistency
├── data/
│   ├── tags_analysis.txt       # Raw tag analysis from database
│   ├── hierarchy.tsv           # Main hierarchy file (parent-child relationships)
│   └── raw_tags.txt           # List of all unique tags
├── queries/
│   └── examples.sparql        # Example SPARQL queries for future OWL version
└── README.md                  # This file
```

## Files

### `data/hierarchy.tsv`

The main ontology file containing parent-child relationships in TSV format:

```
parent	child
software_category	api
software_category	test
test	integration
```

**Format Rules:**
- Tab-separated values
- First column: parent tag
- Second column: child tag
- Root categories have no parent (top-level entries)
- Each child should have exactly one parent (monohierarchy)

### `scripts/query_tags.py`

Extracts all unique tags from the database and generates usage statistics.

**Usage:**
```bash
cd genonaut/ontologies/tags/scripts
set -a && source ../../../../env/.env && python query_tags.py
```

### `scripts/generate_hierarchy.py`

Analyzes tags and generates the hierarchical structure automatically, with provisions for manual curation.

**Usage:**
```bash
cd genonaut/ontologies/tags/scripts
python generate_hierarchy.py
```

## Current Ontology

Based on the current database content, the ontology includes:

### Software Category
- **api**: Application Programming Interface related content
- **test**: Testing-related content

### Test Types
- **integration**: Integration testing (subclass of test)

## Maintenance

### Adding New Tags

1. **Automatic**: New tags are detected when running `query_tags.py`
2. **Manual curation**: Edit `data/hierarchy.tsv` to add new relationships
3. **Validation**: Run validation scripts to ensure consistency

### Refreshing from Database

```bash
# From project root
make ontology-refresh
```

### Validation

```bash
# From project root
make ontology-validate
```

## Future Development

### OWL Conversion

The TSV hierarchy will be converted to OWL format for full semantic web compatibility:

```turtle
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix genonaut: <http://genonaut.ai/ontology/tags#> .

genonaut:api rdfs:subClassOf genonaut:software_category .
genonaut:test rdfs:subClassOf genonaut:software_category .
genonaut:integration rdfs:subClassOf genonaut:test .
```

### SPARQL Queries

Once converted to OWL, queries like these will be possible:

```sparql
# Find all subtypes of 'test'
SELECT ?subtest WHERE {
  ?subtest rdfs:subClassOf* genonaut:test .
}

# Find all content tagged with testing-related tags
SELECT ?content WHERE {
  ?content genonaut:hasTag ?tag .
  ?tag rdfs:subClassOf* genonaut:test .
}
```

## Design Principles

1. **Monohierarchy**: Each tag has exactly one parent
2. **Clarity**: Relationships should be intuitive and logically sound
3. **Stability**: Changes should be backward-compatible when possible
4. **Completeness**: All active tags should be included in the hierarchy
5. **Maintainability**: Structure should be easy to update and extend

## Contributing

When adding new tag relationships:

1. Consider the logical relationship (is-a vs. related-to)
2. Maintain monohierarchy (one parent per child)
3. Use consistent naming conventions
4. Test with validation scripts
5. Document significant changes

## Technical Notes

- Tags are stored in lowercase for consistency
- Special characters in tags are preserved
- Compound tags (e.g., "black_cat") are treated as single entities
- Frequency data is maintained for prioritization decisions

## Integration

This ontology integrates with:

- **Database schema**: `ContentItem.tags` and `ContentItemAuto.tags` columns
- **Search system**: Hierarchical tag queries
- **Recommendation engine**: Tag relationship scoring
- **Content management**: Automatic tag suggestions

For more information, see the main project documentation in `docs/`.