# Tag Ontology Feature - Planning Document

## Overview

This document outlines the development of a tag ontology system for Genonaut that will create a hierarchical classification of all tags currently associated with images in the database.

## Motivation

Currently, tags in the Genonaut system are stored as flat JSON arrays in the database without any hierarchical structure or semantic relationships. Creating an ontology will:

1. **Improve search and discovery** - Users can find content through hierarchical browsing
2. **Enable semantic queries** - SPARQL queries can leverage parent/child relationships
3. **Support recommendation systems** - Content can be recommended based on tag relationships
4. **Facilitate content organization** - Related tags can be grouped logically
5. **Enable automatic tag suggestions** - When tagging content, suggest related/parent tags

## Technical Approach

### Phase 1: Data Analysis & TSV Generation
1. **Query existing tags** from both `content_items` and `content_items_auto` tables
2. **Analyze tag patterns** and identify potential hierarchical relationships
3. **Create initial TSV** with parent-child relationships (monohierarchy: each tag has only one parent)
4. **Manual curation** of the initial hierarchy

### Phase 2: Infrastructure Setup
1. **Directory structure**: `genonaut/ontologies/tags/`
2. **Scripts for querying** and updating the tag ontology
3. **Makefile goals** for automation
4. **Documentation** and developer guides

### Phase 3: OWL Generation (Future)
1. **Convert TSV to OWL** format using `rdfs:subClassOf` relationships
2. **SPARQL query support** using the `robot` tool
3. **Integration with existing system**

## Database Schema Analysis

From `genonaut/db/schema.py`, tags are stored as:
- **ContentItem.tags**: `Column(JSONColumn, default=list)` (line 106)
- **ContentItemAuto.tags**: `Column(JSONColumn, default=list)` (line 106 in ContentItemColumns)

Both tables use the same column structure, storing tags as JSON arrays.

## Proposed Directory Structure

```
genonaut/ontologies/tags/
├── scripts/
│   ├── query_tags.py           # Extract all tags from database
│   ├── analyze_hierarchy.py    # Analyze and suggest parent-child relationships
│   └── generate_tsv.py         # Generate the parent-child TSV file
├── data/
│   ├── raw_tags.txt           # All unique tags from database
│   ├── tag_frequencies.txt    # Tag usage statistics
│   └── hierarchy.tsv          # Parent-child relationships (main output)
├── queries/
│   └── example_sparql.rq      # Example SPARQL queries (for future OWL)
└── README.md                  # Documentation for this ontology
```

## TSV Format Specification

The main output will be a TSV file: `hierarchy.tsv`

Format:
```
parent	child
animal	cat
animal	dog
vehicle	car
vehicle	bicycle
cat	persian_cat
cat	siamese_cat
```

Rules:
- **Monohierarchy**: Each child has exactly one parent
- **Root concepts**: Top-level categories have no parent (empty parent field or special ROOT marker)
- **Case normalization**: All tags stored in lowercase for consistency
- **Manual curation**: Initial automatic suggestions will be manually reviewed and refined



## Technical Considerations

### Database Connection
- Using `genonaut.db.utils.utils.get_database_session()` for database access
- Environment configuration via `env/.env` file
- Support for multiple environments (dev, demo, test)

### Tag Normalization
- Convert to lowercase for consistency
- Handle plurals and variations (e.g., "cat" vs "cats")
- Address compound tags (e.g., "black_cat" vs "black cat")
- Deal with special characters and spaces

### Validation
- Ensure no circular dependencies in hierarchy
- Validate that all children have valid parents
- Check for orphaned tags (no relationships)
- Maintain referential integrity

### Performance
- Consider tag frequency when building hierarchy (more common tags might be higher level)
- Optimize for common query patterns
- Plan for scalability as tag collection grows
