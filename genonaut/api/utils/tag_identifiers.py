"""Helpers for working with tag identifiers across legacy and database forms."""

from __future__ import annotations

import json
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple


TAG_UUID_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')


def _hierarchy_path() -> Path:
    """Return the filesystem path to the tag hierarchy JSON file."""

    return Path(__file__).resolve().parents[2] / 'ontologies' / 'tags' / 'data' / 'hierarchy.json'


@lru_cache(maxsize=1)
def _load_tag_mappings() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Load mappings between UUID identifiers and legacy slug identifiers.

    Returns a tuple of two dictionaries:
        (uuid_to_slug, slug_to_uuid)
    """

    uuid_to_slug: Dict[str, str] = {}
    slug_to_uuid: Dict[str, str] = {}

    path = _hierarchy_path()
    if not path.exists():
        return uuid_to_slug, slug_to_uuid

    try:
        with path.open('r', encoding='utf-8') as handle:
            hierarchy = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return uuid_to_slug, slug_to_uuid

    for node in hierarchy.get('nodes', []):
        slug = node.get('id')
        if not slug:
            continue

        generated_uuid = str(uuid.uuid5(TAG_UUID_NAMESPACE, slug))
        uuid_to_slug[generated_uuid] = slug
        slug_to_uuid[slug] = generated_uuid

    return uuid_to_slug, slug_to_uuid


def get_slug_for_identifier(identifier: str) -> Optional[str]:
    """Return the legacy slug for a given tag identifier if known."""

    uuid_to_slug, _ = _load_tag_mappings()
    return uuid_to_slug.get(str(identifier))


def get_uuid_for_slug(slug: str) -> Optional[str]:
    """Return the UUID string for a given legacy slug if known."""

    _, slug_to_uuid = _load_tag_mappings()
    return slug_to_uuid.get(slug)


def expand_tag_identifiers(tags: List[str]) -> List[str]:
    """Augment tag identifiers with their slug/UUID counterparts.

    Ensures filtering works regardless of whether the content records store legacy
    slugs (e.g., "artistic_medium") or the new UUID identifiers.
    """

    if not tags:
        return []

    uuid_to_slug, slug_to_uuid = _load_tag_mappings()

    expanded: List[str] = []
    seen: set[str] = set()

    for value in tags:
        if not value:
            continue

        identifier = str(value)
        if identifier not in seen:
            expanded.append(identifier)
            seen.add(identifier)

        # If identifier looks like a UUID and we know the corresponding slug, include it
        try:
            uuid.UUID(identifier)
        except ValueError:
            continue

        slug = uuid_to_slug.get(identifier)
        if slug and slug not in seen:
            expanded.append(slug)
            seen.add(slug)

    return expanded
