#!/usr/bin/env python3
"""Analyze tag patterns and linguistic features for better hierarchy building.

This script identifies patterns like plurals, compounds, variations, and
semantic relationships in the tag data to improve the ontology structure.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from collections import defaultdict, Counter

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def analyze_linguistic_patterns(tags: List[str]) -> Dict[str, List[str]]:
    """Analyze linguistic patterns in the tags."""

    patterns = {
        'compound_terms': [],       # hyphenated terms
        'dimensional_terms': [],    # 2d, 3d, etc.
        'quality_terms': [],        # 4k, 8k, hdr
        'technique_suffixes': [],   # -art, -painting, -style
        'material_terms': [],       # acrylic, oil, chalk
        'perspective_terms': [],    # bird's-eye, top-down, close-up
        'style_adjectives': [],     # modern, vintage, gothic
        'color_mood_terms': [],     # bright, dark, vibrant
        'genre_terms': [],          # fantasy, sci-fi, horror
        'single_words': [],         # simple single terms
    }

    # Regex patterns for categorization
    dimension_pattern = r'^[0-9]+d$|^3d-render$'
    quality_pattern = r'^[0-9]+k$|^hdr$|^high-detail$'
    technique_suffix_pattern = r'-(art|painting|style|shaded|light|framing)$'
    material_pattern = r'^(acrylic|oil-painting|chalk|charcoal|crayon|marker|inked)$'
    perspective_pattern = r'(eye|view|up|down|shot|angle|perspective)'

    for tag in tags:
        if '-' in tag:
            patterns['compound_terms'].append(tag)

            # Check specific compound patterns
            if re.search(technique_suffix_pattern, tag):
                patterns['technique_suffixes'].append(tag)
            elif 'eye' in tag or any(word in tag for word in ['top-down', 'bird\'s-eye', 'close-up']):
                patterns['perspective_terms'].append(tag)
        elif re.search(dimension_pattern, tag):
            patterns['dimensional_terms'].append(tag)
        elif re.search(quality_pattern, tag):
            patterns['quality_terms'].append(tag)
        elif re.search(material_pattern, tag):
            patterns['material_terms'].append(tag)
        elif tag in ['modern', 'vintage', 'gothic', 'elegant', 'futuristic', 'ornate', 'minimalism']:
            patterns['style_adjectives'].append(tag)
        elif tag in ['bright', 'dark', 'vibrant', 'colorful', 'monochrome', 'pastel', 'cool', 'warm']:
            patterns['color_mood_terms'].append(tag)
        elif tag in ['fantasy', 'sci-fi', 'horror', 'action', 'anime']:
            patterns['genre_terms'].append(tag)
        else:
            patterns['single_words'].append(tag)

    return {k: v for k, v in patterns.items() if v}


def identify_semantic_clusters(tags: List[str]) -> Dict[str, List[str]]:
    """Group tags into semantic clusters based on meaning and usage."""

    clusters = {
        # Visual characteristics
        'colors_brightness': ['bright', 'dark', 'vibrant', 'colorful', 'monochrome', 'pastel', 'cool', 'warm', 'neon'],
        'lighting_atmosphere': ['atmospheric', 'glitch', 'hard-light', 'soft-light', 'hdr', 'moody', 'dreamy', 'ethereal'],
        'visual_qualities': ['glossy', 'matte', 'textured', 'ornate', 'minimalism', 'elegant', 'gritty'],

        # Technical aspects
        'resolution_detail': ['4k', '8k', 'high-detail', 'low-poly'],
        'rendering_styles': ['photorealistic', 'stylized', 'cel-shaded', 'painterly', 'hand-drawn'],
        'composition_views': ['close-up', 'panoramic', 'bird\'s-eye', 'overhead', 'top-down', 'fisheye', 'macro', 'tilt-shift', 'isometric'],
        'symmetry_balance': ['symmetrical', 'asymmetrical'],

        # Artistic mediums and techniques
        'traditional_media': ['acrylic', 'oil-painting', 'chalk', 'charcoal', 'crayon', 'marker', 'inked'],
        'digital_techniques': ['digital-painting', 'pixel-art', 'vector', 'raster', '3d-render'],
        'art_techniques': ['collage', 'mixed-media', 'line-art', 'concept-art', 'illustration', 'photobash'],

        # Dimensional and format
        'dimensions': ['2d', '3d', 'flat', 'voxel'],
        'content_formats': ['poster-style', 'magazine-cover', 'logo-ready', 'thumbnail', 'editorial'],

        # Artistic movements and styles
        'art_movements': ['abstract', 'realistic', 'surreal', 'experimental', 'decorative'],
        'style_periods': ['modern', 'vintage', 'futuristic', 'gothic'],
        'mood_styles': ['mystical', 'surreal', 'dreamy', 'gritty'],

        # Content genres
        'fiction_genres': ['fantasy', 'sci-fi', 'horror', 'action'],
        'art_forms': ['anime', 'sculpture', 'still-life', 'installation'],

        # Workflow and trending
        'production_quality': ['trending', 'dynamic', 'expressive'],
    }

    # Verify tags exist in our dataset
    verified_clusters = {}
    all_tags_set = set(tags)

    for cluster_name, cluster_tags in clusters.items():
        verified_tags = [tag for tag in cluster_tags if tag in all_tags_set]
        if verified_tags:
            verified_clusters[cluster_name] = verified_tags

    return verified_clusters


def suggest_hierarchy_improvements(current_hierarchy: List[Tuple[str, str]],
                                 semantic_clusters: Dict[str, List[str]]) -> List[str]:
    """Suggest improvements to the current hierarchy based on analysis."""

    suggestions = []

    # Check for missing relationships
    current_relationships = set(current_hierarchy)

    # Suggest intermediate categories for large clusters
    for cluster_name, cluster_tags in semantic_clusters.items():
        if len(cluster_tags) > 5:
            suggestions.append(f"Consider creating intermediate category '{cluster_name}' for: {', '.join(cluster_tags[:3])}...")

    # Check for consistency in naming
    parents = {parent for parent, child in current_hierarchy}
    children = {child for parent, child in current_hierarchy}

    # Find categories that could be grouped
    style_related = [p for p in parents if 'style' in p.lower()]
    if len(style_related) > 1:
        suggestions.append(f"Consider consolidating style-related categories: {style_related}")

    return suggestions


def main():
    """Analyze tag patterns and provide insights for hierarchy building."""

    # Read tags from analysis file
    data_dir = Path(__file__).parent.parent / "data"
    analysis_file = data_dir / "tags_analysis.txt"

    if not analysis_file.exists():
        print(f"Error: Analysis file not found at {analysis_file}")
        return 1

    # Extract tags
    tags = []
    tag_frequencies = {}

    with open(analysis_file, 'r') as f:
        lines = f.readlines()

        # Parse both sections
        in_tags_section = False
        in_frequency_section = False

        for line in lines:
            if "ALL UNIQUE TAGS" in line:
                in_tags_section = True
                in_frequency_section = False
                continue
            elif "TAG FREQUENCY ANALYSIS" in line:
                in_tags_section = False
                in_frequency_section = True
                continue
            elif in_tags_section and line.strip() and not line.startswith('='):
                tags.append(line.strip())
            elif in_frequency_section and ':' in line:
                parts = line.strip().split(': ')
                if len(parts) == 2:
                    tag_frequencies[parts[0]] = int(parts[1])

    print(f"Analyzing {len(tags)} tags for linguistic and semantic patterns...\n")

    # Analyze linguistic patterns
    linguistic_patterns = analyze_linguistic_patterns(tags)

    print("=== LINGUISTIC PATTERNS ===")
    for pattern_type, pattern_tags in linguistic_patterns.items():
        print(f"{pattern_type}: {len(pattern_tags)} tags")
        print(f"  Examples: {', '.join(pattern_tags[:5])}{'...' if len(pattern_tags) > 5 else ''}")

    # Analyze semantic clusters
    semantic_clusters = identify_semantic_clusters(tags)

    print(f"\n=== SEMANTIC CLUSTERS ===")
    for cluster_name, cluster_tags in semantic_clusters.items():
        avg_frequency = sum(tag_frequencies.get(tag, 0) for tag in cluster_tags) / len(cluster_tags)
        print(f"{cluster_name}: {len(cluster_tags)} tags (avg freq: {avg_frequency:.0f})")
        print(f"  Tags: {', '.join(cluster_tags)}")

    # Read current hierarchy for analysis
    hierarchy_file = data_dir / "hierarchy.tsv"
    current_hierarchy = []

    if hierarchy_file.exists():
        with open(hierarchy_file, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    current_hierarchy.append((parts[0], parts[1]))

    # Generate suggestions
    suggestions = suggest_hierarchy_improvements(current_hierarchy, semantic_clusters)

    print(f"\n=== HIERARCHY ANALYSIS ===")
    print(f"Current hierarchy has {len(current_hierarchy)} relationships")

    if suggestions:
        print("\nSuggestions for improvement:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")
    else:
        print("Current hierarchy structure looks well-organized!")

    # Write detailed analysis to file
    analysis_output = data_dir / "pattern_analysis.txt"
    with open(analysis_output, 'w') as f:
        f.write("=== TAG PATTERN ANALYSIS ===\n\n")

        f.write("LINGUISTIC PATTERNS:\n")
        for pattern_type, pattern_tags in linguistic_patterns.items():
            f.write(f"\n{pattern_type.upper()}:\n")
            for tag in sorted(pattern_tags):
                freq = tag_frequencies.get(tag, 0)
                f.write(f"  {tag} (freq: {freq})\n")

        f.write(f"\n\nSEMANTIC CLUSTERS:\n")
        for cluster_name, cluster_tags in semantic_clusters.items():
            f.write(f"\n{cluster_name.upper()}:\n")
            for tag in sorted(cluster_tags):
                freq = tag_frequencies.get(tag, 0)
                f.write(f"  {tag} (freq: {freq})\n")

    print(f"\nDetailed analysis written to: {analysis_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())