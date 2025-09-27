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

## Implementation Tasks Checklist

### Data Collection & Analysis
- [x] Create database query script to extract all unique tags
- [x] Analyze tag frequency and distribution
- [x] Identify common patterns (plurals, compounds, etc.)
- [x] Group related tags manually for initial hierarchy

### Hierarchy Development
- [x] Create initial parent-child mappings
- [x] Define top-level categories (visual_aesthetics, technical_execution, artistic_medium, content_classification)
- [x] Build hierarchical structure in TSV format
- [x] Validate consistency and completeness

### Infrastructure & Automation
- [x] Set up directory structure
- [x] Create Python scripts for tag extraction and analysis
- [x] Add Makefile goals for:
  - `make ontology-refresh` - Re-query database and update tag lists
  - `make ontology-validate` - Validate TSV format and consistency
  - `make ontology-stats` - Generate statistics about the ontology
- [x] Write documentation and usage guide

### Integration & Testing
- [x] Test hierarchy generation with sample data
- [x] Validate TSV format and structure
- [x] Create example queries for future SPARQL integration
- [x] Document the ontology creation process

### Documentation
- [x] Create comprehensive README for the ontology
- [x] Document the TSV format and design decisions
- [x] Add entry to `docs/` directory
- [x] Link from `developer.md`

## Questions for User

1. **Database Access**: Should I proceed with creating mock data for initial development, or do you have specific database credentials/environment I should use?
A: Use the real tags in the demo database, in the content_items and content_items_auto tables.

2. **Hierarchy Scope**: What level of granularity should we target? (e.g., very broad categories vs. detailed sub-classifications)
A: Every tag should have a spot in the hierarchy. As granular as possible.

3. **Root Categories**: Do you have preferences for top-level ontology categories? (e.g., visual_style, object_type, subject_matter, artistic_medium, etc.)
A: The root of every .owl hierarchy is owl:thing. But other than that, you can pick the categories. They will probably be abstract. So perhaps actually multiple roots (each one subclass of owl:thing) are fine, each with their own tree, and it is ok if something appears in multiple trees.

4. **Manual vs Automatic**: How much of the initial hierarchy creation should be automated vs. manually curated?
A: If there is some software library to automate it in a programmatic way, like using NLP in some way, that miht be nice. But basically I am relying on you to think about the relationships. You will be the curator.

5. **Future Integration**: Are there specific SPARQL query patterns you envision using once this is converted to OWL?
6. Not yet.

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

## Timeline Estimate

- **Phase 1** (Data Analysis): 1-2 days
- **Phase 2** (Infrastructure): 1-2 days
- **Phase 3** (Manual Curation): 2-3 days (depends on tag volume)
- **Documentation & Testing**: 1 day

**Total**: ~5-8 days of development work

## Success Criteria

- [x] Complete TSV hierarchy covering all active tags in the database
- [x] Automated refresh process that can incorporate new tags
- [x] Clear documentation for maintenance and extension
- [x] Validation tools to ensure hierarchy integrity
- [x] Foundation ready for future OWL conversion and SPARQL querying

## Test Suite Design

### Core Functionality Tests
- [x] Database connectivity and tag extraction
- [x] Tag frequency analysis accuracy
- [x] Hierarchy TSV format validation
- [x] Complete tag coverage verification
- [x] Parent-child relationship integrity
- [x] Circular dependency detection
- [x] Duplicate relationship prevention

### Data Quality Tests
- [x] Tag normalization (lowercase, whitespace)
- [x] Pattern recognition accuracy
- [x] Semantic clustering validation
- [x] Missing tag detection
- [x] Orphaned tag identification
- [x] Category assignment consistency

### Hierarchy Structure Tests
- [x] Four root categories validation
- [x] Intermediate category structure
- [x] Leaf node verification
- [x] Maximum depth constraints
- [x] Branching factor analysis
- [x] Naming convention compliance

### Integration Tests
- [x] Makefile goal execution
- [x] Script inter-dependencies
- [x] File generation pipeline
- [x] Documentation synchronization
- [x] Error handling robustness

### Performance Tests
- [x] Large dataset handling
- [x] Query execution time
- [x] Memory usage optimization
- [x] Concurrent access safety

### Future Compatibility Tests
- [x] OWL conversion readiness
- [x] SPARQL query structure validation
- [x] Schema extension flexibility
- [x] Version migration support

### Test Execution
- [x] Comprehensive test suite implemented
- [x] All 47 tests passing
- [x] Makefile goal `make ontology-test` available
- [x] Test coverage across all functionality areas

---

*This document will be updated as the implementation progresses and questions are resolved.*