#!/usr/bin/env python3
"""Create the final curated hierarchy based on pattern analysis and semantic understanding.

This script combines the automated semantic analysis with manual curation
to create the definitive tag ontology hierarchy.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def create_curated_hierarchy() -> List[Tuple[str, str]]:
    """Create the manually curated hierarchy based on semantic analysis.

    This represents the final, production-ready hierarchy that incorporates
    insights from pattern analysis and follows OWL Thing structure.
    """

    # Root level: Everything ultimately derives from owl:Thing
    # But we create 4 main branches as immediate children
    hierarchy = []

    # =================================================================
    # LEVEL 1: Main Categories (direct children of owl:Thing)
    # =================================================================

    main_categories = [
        'visual_aesthetics',      # How things look and feel
        'technical_execution',    # How things are made/composed
        'artistic_medium',        # What tools/materials/techniques
        'content_classification'  # What type of content it is
    ]

    # =================================================================
    # LEVEL 2: Sub-categories
    # =================================================================

    # Visual Aesthetics subcategories
    hierarchy.extend([
        ('visual_aesthetics', 'color_properties'),
        ('visual_aesthetics', 'lighting_effects'),
        ('visual_aesthetics', 'mood_atmosphere'),
        ('visual_aesthetics', 'visual_style'),
        ('visual_aesthetics', 'surface_qualities'),
    ])

    # Technical Execution subcategories
    hierarchy.extend([
        ('technical_execution', 'composition_viewpoint'),
        ('technical_execution', 'rendering_technique'),
        ('technical_execution', 'resolution_quality'),
        ('technical_execution', 'dimensional_properties'),
    ])

    # Artistic Medium subcategories
    hierarchy.extend([
        ('artistic_medium', 'traditional_materials'),
        ('artistic_medium', 'digital_techniques'),
        ('artistic_medium', 'artistic_methods'),
    ])

    # Content Classification subcategories
    hierarchy.extend([
        ('content_classification', 'art_movements'),
        ('content_classification', 'content_genres'),
        ('content_classification', 'format_types'),
        ('content_classification', 'production_context'),
    ])

    # =================================================================
    # LEVEL 3: Specific groupings and leaf nodes
    # =================================================================

    # Color Properties
    color_tags = ['bright', 'dark', 'vibrant', 'colorful', 'monochrome', 'pastel', 'cool', 'warm', 'neon']
    hierarchy.extend([('color_properties', tag) for tag in color_tags])

    # Lighting Effects
    lighting_tags = ['atmospheric', 'glitch', 'hard-light', 'soft-light', 'hdr']
    hierarchy.extend([('lighting_effects', tag) for tag in lighting_tags])

    # Mood & Atmosphere
    mood_tags = ['moody', 'dreamy', 'ethereal', 'mystical', 'gritty', 'surreal']
    hierarchy.extend([('mood_atmosphere', tag) for tag in mood_tags])

    # Visual Style
    style_tags = ['elegant', 'futuristic', 'gothic', 'minimalism', 'modern', 'ornate', 'vintage',
                  'dynamic', 'expressive', 'trending']
    hierarchy.extend([('visual_style', tag) for tag in style_tags])

    # Surface Qualities
    surface_tags = ['glossy', 'matte', 'textured']
    hierarchy.extend([('surface_qualities', tag) for tag in surface_tags])

    # Composition & Viewpoint - with intermediate groupings
    hierarchy.extend([
        ('composition_viewpoint', 'camera_angles'),
        ('composition_viewpoint', 'distance_framing'),
        ('composition_viewpoint', 'spatial_organization'),
    ])

    # Camera angles
    angle_tags = ['bird\'s-eye', 'overhead', 'top-down', 'worm\'s-eye']
    hierarchy.extend([('camera_angles', tag) for tag in angle_tags])

    # Distance framing
    distance_tags = ['close-up', 'macro', 'panoramic']
    hierarchy.extend([('distance_framing', tag) for tag in distance_tags])

    # Spatial organization
    spatial_tags = ['isometric', 'fisheye', 'tilt-shift', 'symmetrical', 'asymmetrical']
    hierarchy.extend([('spatial_organization', tag) for tag in spatial_tags])

    # Rendering Technique
    rendering_tags = ['photorealistic', 'stylized', 'cel-shaded', 'painterly', 'hand-drawn']
    hierarchy.extend([('rendering_technique', tag) for tag in rendering_tags])

    # Resolution & Quality
    quality_tags = ['4k', '8k', 'high-detail', 'low-poly']
    hierarchy.extend([('resolution_quality', tag) for tag in quality_tags])

    # Dimensional Properties
    dimension_tags = ['2d', '3d', 'flat', 'voxel', '3d-render']
    hierarchy.extend([('dimensional_properties', tag) for tag in dimension_tags])

    # Traditional Materials
    traditional_tags = ['acrylic', 'oil-painting', 'chalk', 'charcoal', 'crayon', 'marker', 'inked']
    hierarchy.extend([('traditional_materials', tag) for tag in traditional_tags])

    # Digital Techniques
    digital_tags = ['digital-painting', 'pixel-art', 'vector', 'raster', 'photobash']
    hierarchy.extend([('digital_techniques', tag) for tag in digital_tags])

    # Artistic Methods
    method_tags = ['collage', 'mixed-media', 'line-art', 'concept-art', 'illustration']
    hierarchy.extend([('artistic_methods', tag) for tag in method_tags])

    # Art Movements
    movement_tags = ['abstract', 'realistic', 'experimental', 'decorative']
    hierarchy.extend([('art_movements', tag) for tag in movement_tags])

    # Content Genres
    genre_tags = ['fantasy', 'sci-fi', 'horror', 'action', 'anime', 'sculpture', 'still-life', 'installation']
    hierarchy.extend([('content_genres', tag) for tag in genre_tags])

    # Format Types
    format_tags = ['poster-style', 'magazine-cover', 'logo-ready', 'thumbnail', 'editorial', 'editorial-style']
    hierarchy.extend([('format_types', tag) for tag in format_tags])

    # Production Context
    production_tags = ['cinematic', 'cinematic-framing']
    hierarchy.extend([('production_context', tag) for tag in production_tags])

    # =================================================================
    # LEVEL 4: Additional specific relationships for compound terms
    # =================================================================

    # Handle some specific sub-relationships
    hierarchy.extend([
        # Surreal art subcategory
        ('mood_atmosphere', 'surreal_art'),
        ('surreal_art', 'surreal'),
        ('surreal_art', 'surreal-collage'),

        # Editorial design subcategory
        ('format_types', 'editorial_design'),
        ('editorial_design', 'editorial'),
        ('editorial_design', 'editorial-style'),
        ('editorial_design', 'magazine-cover'),

        # Cinematic style subcategory
        ('production_context', 'cinematic_style'),
        ('cinematic_style', 'cinematic'),
        ('cinematic_style', 'cinematic-framing'),
    ])

    return hierarchy


def validate_hierarchy_completeness(hierarchy: List[Tuple[str, str]], all_tags: List[str]) -> Dict:
    """Validate that all tags are included in the hierarchy."""

    # Get all children (leaf tags) from hierarchy
    children_in_hierarchy = {child for parent, child in hierarchy}

    # Get all tags from the original data
    all_tags_set = set(all_tags)

    # Find missing tags
    missing_tags = all_tags_set - children_in_hierarchy

    # Find extra tags in hierarchy not in original data
    extra_tags = children_in_hierarchy - all_tags_set

    # Count hierarchy stats
    total_relationships = len(hierarchy)
    unique_children = len(children_in_hierarchy)
    unique_parents = len({parent for parent, child in hierarchy})

    return {
        'missing_tags': missing_tags,
        'extra_tags': extra_tags,
        'total_relationships': total_relationships,
        'unique_children': unique_children,
        'unique_parents': unique_parents,
        'coverage_percent': (len(all_tags_set & children_in_hierarchy) / len(all_tags_set)) * 100
    }


def main():
    """Create the final curated hierarchy."""

    # Read original tags from analysis
    data_dir = Path(__file__).parent.parent / "data"
    analysis_file = data_dir / "tags_analysis.txt"

    if not analysis_file.exists():
        print(f"Error: Analysis file not found at {analysis_file}")
        return 1

    # Extract original tags
    original_tags = []
    with open(analysis_file, 'r') as f:
        lines = f.readlines()
        in_tags_section = False
        for line in lines:
            if "ALL UNIQUE TAGS" in line:
                in_tags_section = True
                continue
            elif "TAG FREQUENCY ANALYSIS" in line:
                break
            elif in_tags_section and line.strip() and not line.startswith('='):
                original_tags.append(line.strip())

    print(f"Creating curated hierarchy for {len(original_tags)} original tags...")

    # Create the curated hierarchy
    hierarchy = create_curated_hierarchy()

    # Validate completeness
    validation = validate_hierarchy_completeness(hierarchy, original_tags)

    print(f"\n=== HIERARCHY VALIDATION ===")
    print(f"Total relationships: {validation['total_relationships']}")
    print(f"Unique children: {validation['unique_children']}")
    print(f"Unique parents: {validation['unique_parents']}")
    print(f"Coverage: {validation['coverage_percent']:.1f}%")

    if validation['missing_tags']:
        print(f"\nMissing tags ({len(validation['missing_tags'])}): {', '.join(sorted(validation['missing_tags']))}")

    if validation['extra_tags']:
        print(f"\nExtra hierarchy tags ({len(validation['extra_tags'])}): {', '.join(sorted(validation['extra_tags']))}")

    # Write the final hierarchy
    hierarchy_file = data_dir / "hierarchy.tsv"
    with open(hierarchy_file, 'w') as f:
        f.write("parent\tchild\n")
        for parent, child in sorted(hierarchy):
            f.write(f"{parent}\t{child}\n")

    print(f"\n✅ Final curated hierarchy written to: {hierarchy_file}")

    # Create a human-readable summary
    summary_file = data_dir / "hierarchy_summary.md"
    with open(summary_file, 'w') as f:
        f.write("# Tag Ontology Hierarchy Summary\n\n")
        f.write(f"Generated from {len(original_tags)} tags with {validation['total_relationships']} relationships.\n\n")

        # Group by top-level categories
        hierarchy_dict = defaultdict(list)
        for parent, child in hierarchy:
            hierarchy_dict[parent].append(child)

        main_cats = ['visual_aesthetics', 'technical_execution', 'artistic_medium', 'content_classification']

        for main_cat in main_cats:
            if main_cat in hierarchy_dict:
                f.write(f"## {main_cat.replace('_', ' ').title()}\n\n")
                for subcat in sorted(hierarchy_dict[main_cat]):
                    f.write(f"### {subcat.replace('_', ' ').title()}\n")
                    if subcat in hierarchy_dict:
                        subcats = sorted(hierarchy_dict[subcat])
                        for item in subcats:
                            if item in hierarchy_dict:
                                # This is an intermediate category
                                f.write(f"- **{item.replace('_', ' ').title()}**: ")
                                leaves = sorted(hierarchy_dict[item])
                                f.write(', '.join(leaves))
                                f.write("\n")
                            else:
                                # This is a leaf tag
                                f.write(f"- {item}\n")
                    f.write("\n")
                f.write("\n")

    print(f"📄 Human-readable summary written to: {summary_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())