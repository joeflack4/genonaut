"""Cursor-based pagination utilities for efficient database queries.

This module provides cursor encoding/decoding for keyset pagination, which eliminates
the OFFSET overhead of traditional pagination and provides consistent performance
across all pages.
"""

import base64
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from uuid import UUID


class CursorError(Exception):
    """Raised when cursor encoding/decoding fails."""
    pass


def encode_cursor(
    created_at: datetime,
    id: int,
    source_type: str
) -> str:
    """
    Encode pagination cursor from timestamp, ID, and source type.

    Args:
        created_at: Timestamp of the item (for ordering)
        id: Item ID (for stable ordering when timestamps match)
        source_type: Source type ('items' or 'auto')

    Returns:
        Base64-encoded cursor string

    Raises:
        CursorError: If encoding fails
    """
    try:
        cursor_data = {
            "ts": created_at.isoformat(),
            "id": id,
            "src": source_type
        }
        cursor_json = json.dumps(cursor_data, sort_keys=True)
        cursor_b64 = base64.urlsafe_b64encode(cursor_json.encode('utf-8')).decode('utf-8')
        return cursor_b64
    except Exception as e:
        raise CursorError(f"Failed to encode cursor: {e}")


def decode_cursor(cursor: str) -> Tuple[datetime, int, str]:
    """
    Decode pagination cursor to extract timestamp, ID, and source type.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (created_at, id, source_type)

    Raises:
        CursorError: If decoding fails or cursor format is invalid
    """
    if not cursor or cursor.strip() == "":
        raise CursorError("Cursor cannot be empty")

    try:
        cursor_json = base64.urlsafe_b64decode(cursor.encode('utf-8')).decode('utf-8')
        cursor_data = json.loads(cursor_json)

        # Validate required fields
        if "ts" not in cursor_data or "id" not in cursor_data or "src" not in cursor_data:
            raise CursorError("Cursor missing required fields (ts, id, src)")

        # Parse timestamp
        created_at = datetime.fromisoformat(cursor_data["ts"])

        # Validate ID is an integer
        id = int(cursor_data["id"])

        # Validate source type
        source_type = cursor_data["src"]
        if source_type not in ("items", "auto"):
            raise CursorError(f"Invalid source_type in cursor: {source_type}")

        return (created_at, id, source_type)

    except json.JSONDecodeError as e:
        raise CursorError(f"Invalid JSON in cursor: {e}")
    except ValueError as e:
        raise CursorError(f"Invalid cursor data: {e}")
    except Exception as e:
        raise CursorError(f"Failed to decode cursor: {e}")


def validate_cursor(cursor: Optional[str]) -> bool:
    """
    Validate cursor format without raising exceptions.

    Args:
        cursor: Cursor string to validate

    Returns:
        True if cursor is valid, False otherwise
    """
    if cursor is None or cursor.strip() == "":
        return True  # Empty cursor is valid (means first page)

    try:
        decode_cursor(cursor)
        return True
    except CursorError:
        return False


def create_next_cursor(
    items: list,
    created_at_field: str = "created_at",
    id_field: str = "id",
    source_type_field: str = "source_type"
) -> Optional[str]:
    """
    Create next page cursor from last item in results.

    Args:
        items: List of items from current page
        created_at_field: Name of timestamp field in items
        id_field: Name of ID field in items
        source_type_field: Name of source type field in items

    Returns:
        Cursor string for next page, or None if no more pages
    """
    if not items:
        return None

    last_item = items[-1]

    # Handle both dict and object access patterns
    if isinstance(last_item, dict):
        created_at = last_item.get(created_at_field)
        id = last_item.get(id_field)
        source_type = last_item.get(source_type_field)
    else:
        created_at = getattr(last_item, created_at_field, None)
        id = getattr(last_item, id_field, None)
        source_type = getattr(last_item, source_type_field, None)

    if created_at is None or id is None or source_type is None:
        return None

    # Convert string timestamp to datetime if needed
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

    return encode_cursor(created_at, id, source_type)


def create_prev_cursor(
    items: list,
    created_at_field: str = "created_at",
    id_field: str = "id",
    source_type_field: str = "source_type"
) -> Optional[str]:
    """
    Create previous page cursor from first item in results.

    Args:
        items: List of items from current page
        created_at_field: Name of timestamp field in items
        id_field: Name of ID field in items
        source_type_field: Name of source type field in items

    Returns:
        Cursor string for previous page, or None if on first page
    """
    if not items:
        return None

    first_item = items[0]

    # Handle both dict and object access patterns
    if isinstance(first_item, dict):
        created_at = first_item.get(created_at_field)
        id = first_item.get(id_field)
        source_type = first_item.get(source_type_field)
    else:
        created_at = getattr(first_item, created_at_field, None)
        id = getattr(first_item, id_field, None)
        source_type = getattr(first_item, source_type_field, None)

    if created_at is None or id is None or source_type is None:
        return None

    # Convert string timestamp to datetime if needed
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

    return encode_cursor(created_at, id, source_type)
