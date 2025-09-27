#!/usr/bin/env python3
"""Analyze semantic relationships between tags using NLP techniques.

This script uses word similarity and semantic analysis to suggest hierarchical
relationships between tags for the ontology.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from collections import defaultdict

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def categorize_tags_by_semantic_domains(tags: List[str]) -> Dict[str, List[str]]:
    """Categorize tags into semantic domains based on patterns and meaning.

    This is a rule-based approach that groups tags by their semantic categories.
    """
    categories = {
        # Visual characteristics
        'color_properties': [],
        'lighting_effects': [],
        'visual_style': [],
        'mood_atmosphere': [],

        # Technical aspects
        'rendering_technique': [],
        'resolution_quality': [],
        'composition_viewpoint': [],
        'medium_material': [],

        # Art styles and genres
        'art_movement': [],
        'content_genre': [],
        'artistic_technique': [],
        'dimensional_properties': []
    }

    # Define keyword patterns for each category
    patterns = {
        'color_properties': ['colorful', 'monochrome', 'pastel', 'vibrant', 'bright', 'dark', 'cool', 'warm', 'neon'],
        'lighting_effects': ['hard-light', 'soft-light', 'hdr', 'atmospheric', 'glitch'],
        'visual_style': ['minimalism', 'ornate', 'elegant', 'gothic', 'modern', 'vintage', 'futuristic'],
        'mood_atmosphere': ['moody', 'dreamy', 'ethereal', 'mystical', 'gritty', 'surreal'],

        'rendering_technique': ['photorealistic', 'stylized', 'cel-shaded', 'painterly', 'hand-drawn', 'digital-painting'],
        'resolution_quality': ['4k', '8k', 'high-detail', 'low-poly'],
        'composition_viewpoint': ['close-up', 'panoramic', 'bird\'s-eye', 'overhead', 'top-down', 'fisheye', 'macro', 'tilt-shift', 'isometric'],
        'medium_material': ['acrylic', 'oil-painting', 'chalk', 'charcoal', 'crayon', 'marker', 'inked'],

        'art_movement': ['abstract', 'realistic', 'experimental', 'decorative'],
        'content_genre': ['fantasy', 'sci-fi', 'horror', 'action', 'anime'],
        'artistic_technique': ['collage', 'mixed-media', 'line-art', 'pixel-art', 'vector', 'raster', 'concept-art'],
        'dimensional_properties': ['2d', '3d', '3d-render', 'flat', 'voxel']
    }

    # First pass: categorize by exact matches
    uncategorized = []
    for tag in tags:
        categorized = False
        for category, keywords in patterns.items():
            if tag in keywords:
                categories[category].append(tag)
                categorized = True
                break
        if not categorized:
            uncategorized.append(tag)

    # Second pass: categorize by partial matches and patterns
    for tag in uncategorized:
        categorized = False

        # Check for compound terms
        if '-' in tag:
            parts = tag.split('-')
            for category, keywords in patterns.items():
                if any(part in keywords for part in parts):
                    categories[category].append(tag)
                    categorized = True
                    break

        # Pattern-based categorization
        if not categorized:
            if tag.endswith('-art') or tag.endswith('-painting'):
                categories['artistic_technique'].append(tag)
            elif tag.endswith('-style') or tag.endswith('-framing'):
                categories['visual_style'].append(tag)
            elif 'symmetrical' in tag or 'asymmetrical' in tag:
                categories['composition_viewpoint'].append(tag)
            elif any(word in tag for word in ['magazine', 'poster', 'editorial', 'logo', 'thumbnail']):
                categories['content_genre'].append(tag)
            elif any(word in tag for word in ['glossy', 'matte', 'textured']):
                categories['visual_style'].append(tag)
            else:
                # Default fallback categories
                if tag in ['trending', 'dynamic', 'expressive', 'installation']:
                    categories['visual_style'].append(tag)
                elif tag in ['sculpture', 'still-life']:
                    categories['content_genre'].append(tag)
                elif tag in ['illustration', 'photobash']:
                    categories['artistic_technique'].append(tag)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def create_hierarchical_mappings(categorized_tags: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    """Create parent-child mappings from categorized tags.

    Returns list of (parent, child) tuples for the TSV file.
    """
    mappings = []

    # Define high-level root categories
    root_mappings = {
        'visual_properties': ['color_properties', 'lighting_effects', 'visual_style', 'mood_atmosphere'],
        'technical_aspects': ['rendering_technique', 'resolution_quality', 'composition_viewpoint'],
        'artistic_medium': ['medium_material', 'artistic_technique'],
        'content_classification': ['art_movement', 'content_genre', 'dimensional_properties']
    }

    # Create root category mappings
    for root, subcategories in root_mappings.items():
        for subcategory in subcategories:
            if subcategory in categorized_tags:
                mappings.append((root, subcategory))

    # Create leaf mappings (subcategory -> individual tags)
    for category, tags in categorized_tags.items():
        for tag in tags:
            mappings.append((category, tag))

    # Add some specific sub-hierarchies based on semantic relationships
    specific_hierarchies = [
        # Resolution quality hierarchy
        ('resolution_quality', 'high_resolution'),
        ('high_resolution', '4k'),
        ('high_resolution', '8k'),

        # 3D rendering hierarchy
        ('3d', '3d-render'),
        ('3d', 'voxel'),
        ('3d', 'low-poly'),

        # Lighting effects
        ('lighting_effects', 'directional_lighting'),
        ('directional_lighting', 'hard-light'),
        ('directional_lighting', 'soft-light'),

        # Symmetry
        ('composition_viewpoint', 'symmetry'),
        ('symmetry', 'symmetrical'),
        ('symmetry', 'asymmetrical'),

        # Editorial styles
        ('content_genre', 'editorial_design'),
        ('editorial_design', 'magazine-cover'),
        ('editorial_design', 'poster-style'),
        ('editorial_design', 'editorial'),
        ('editorial_design', 'editorial-style'),

        # Art techniques
        ('artistic_technique', 'traditional_media'),
        ('traditional_media', 'oil-painting'),
        ('traditional_media', 'acrylic'),
        ('traditional_media', 'chalk'),
        ('traditional_media', 'charcoal'),
        ('traditional_media', 'crayon'),
        ('traditional_media', 'marker'),
        ('traditional_media', 'inked'),

        # Digital techniques
        ('artistic_technique', 'digital_media'),
        ('digital_media', 'digital-painting'),
        ('digital_media', 'pixel-art'),
        ('digital_media', 'vector'),
        ('digital_media', 'raster'),

        # Surreal styles
        ('art_movement', 'surrealism'),
        ('surrealism', 'surreal'),
        ('surrealism', 'surreal-collage'),

        # Typography
        ('visual_style', 'typography'),
        ('typography', 'minimalist-typography'),

        # Cinematic
        ('visual_style', 'cinematic_style'),
        ('cinematic_style', 'cinematic'),
        ('cinematic_style', 'cinematic-framing')
    ]

    # Only add specific hierarchies if both parent and child exist in our data
    all_tags = {tag for tags_list in categorized_tags.values() for tag in tags_list}
    for parent, child in specific_hierarchies:
        if child in all_tags:
            mappings.append((parent, child))

    return mappings


def main():
    """Analyze semantic relationships and create enhanced hierarchy."""

    # Read tags from analysis file
    data_dir = Path(__file__).parent.parent / "data"
    analysis_file = data_dir / "tags_analysis.txt"

    if not analysis_file.exists():
        print(f"Error: Analysis file not found at {analysis_file}")
        return 1

    # Extract tags
    tags = []
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
                tags.append(line.strip())

    print(f"Analyzing {len(tags)} tags for semantic relationships...")

    # Categorize tags
    categorized = categorize_tags_by_semantic_domains(tags)

    print("\nSemantic categories found:")
    for category, tag_list in categorized.items():
        print(f"  {category}: {len(tag_list)} tags")
        print(f"    {', '.join(tag_list[:5])}{'...' if len(tag_list) > 5 else ''}")

    # Create hierarchical mappings
    mappings = create_hierarchical_mappings(categorized)

    # Write to TSV file
    hierarchy_file = data_dir / "hierarchy.tsv"
    with open(hierarchy_file, 'w') as f:
        f.write("parent\tchild\n")
        for parent, child in sorted(mappings):
            f.write(f"{parent}\t{child}\n")

    print(f"\nSemantic hierarchy created with {len(mappings)} relationships")
    print(f"Written to: {hierarchy_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())